# 模型主动激发模块
# 1、后台线程根据群聊最近聊天记录，获取群聊列表，主动发起聊天
# 2、如果长时间没有聊天，主动发起聊天
# 3、根据时事热点，主动发起聊天
import datetime
import traceback
import uuid

from sqlalchemy import and_
from typing import List
import json

from flask import Flask, current_app
from flask.ctx import AppContext

from controllers.service_api.app import create_or_update_end_user_for_user_id
from core.completion import Completion
from extensions.ext_database import db
from models.model import Conversation, App, AppModelConfig
from mylogger import logger


import threading
import time
import random
import requests


from core.judge_llm_active import judge_llm_active
from services.completion_service import CompletionService
from controllers.app_api.app.utils import *
from controllers.app_api.app.search_event import get_topic
from extensions.ext_redis import redis_client


def model_chat(conversation_id: str, outer_memory: List, is_force=False, query="", user_name=''):
    # time.sleep(10000)
    # 对当前conversation上锁
    if redis_client.get(conversation_id) is None:
        redis_client.setex(conversation_id, 40, 1)
    else:
        logger.info(f"conversation {conversation_id} is locked")
        return None
    conversation_filter = [
        Conversation.id == conversation_id
    ]

    conversation = db.session.query(Conversation).filter(and_(*conversation_filter)).first()
    if not conversation:
        logger.info(f"{conversation_id} not exist")
        return None
    app_id = conversation.app_id
    app_model = db.session.query(App).filter(App.id == app_id).first()
    args = {
        'conversation_id': conversation_id, "inputs": {}, "query": query
    }
    logger.info(f"{app_model.name} {conversation_id}")
    histories = ""
    for message in outer_memory:
        histories += f"{message['role']}:{message['message']}\n"
    if is_force:
        judge_result = True
    else:
        judge_result = judge_llm_active("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", histories,
                                        app_model.name, is_random_true=False)
    if judge_result:
        end_user = create_or_update_end_user_for_user_id(app_model, '')
        logger.info(f"主动发起聊天：{app_model.name} {conversation_id}")
        # logger.info(f"{outer_memory[:-min(2, len(outer_memory))]}")
        response = CompletionService.completion(
            app_model=app_model,
            user=end_user,
            args=args,
            from_source='api',
            streaming=False,
            outer_memory=outer_memory,
            assistant_name=app_model.name,
            user_name=user_name
        )
        return response
    else:
        return None



# 映射
model_name_dict = {
    "DJ Bot": "James Corden",
}


# 映射
def model_name_transform(model_name: str):
    if model_name in model_name_dict:
        return model_name_dict[model_name]
    return model_name


def send_message(group_id: int, message: str):
    url = "https://rm.triple3v.org/api/sys/send_chat_message"

    payload = json.dumps({
        "group_id": group_id,
        "txt": message
    })
    headers = {
        'Authorization': 'Bearer 6520|LyHTtFbuGPxYPNllyTQ5DRu0jIInQt8ZqDeyBG425c19f8cf',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    return response.json()

'''
message:
[{
    "id": 5867,
    "chat_type": "groupchat",
    "message_type": "txt",
    "from_user_id": 294,
    "to_user_id": null,
    "group_id": 32,
    "chat_text": "That's a fantastic question, Bill 000! AI, short for Artificial Intelligence, has become an integral part of our society and it has numerous benefits. Let's delve in:\n\n1. Efficiency and Productivity: AI can automate repetitive tasks, freeing up time for individuals to focus on creative and high-level tasks. \n\n2. Predictive Analysis: AI can mine through vast amounts of data to identify patterns and trends, making it helpful in predicting outcomes in fields like finance, healthcare, and more.\n\n3. Personalized Experiences: AI is used to customize recommendations in shopping, entertainment, or even learning experiences, enhancing user satisfaction.\n\n4. Improved Accessibility: Voice-activated AI helps people with disabilities get online and use technology.\n\n5. Enhancing Healthcare: AI is used in predicting disease outbreaks, diagnosing conditions, and personalizing patient treatment plans.\n\n6. In Entertainment: AI is used in gaming systems, recommending movies, music, and in augmented reality experiences.\n\nRemember, like any tool, the benefits of AI depend on how we use it. It has its challenges that society must address, but its potential is enormous! What's your take on this, Bill 000?",
    "created_at": "2023-11-01 16:25:06",
    "msg_id": "1208136099159870234",
    "timestamp": 1698855905607,
    "ai_message_id": 115,
    "from_user": {
        "id": 294,
        "name": "DJ Bot",
        "user_type": 4
    },
    "to_user": null,
    "ai_api_info": {
        "openai": {
            "conversation_id": "75f490c8-b3e5-4a00-82eb-34c3f1ebf51b"
        }
    }
},
]
'''


# 主动询问是否回话，每五分钟一次
# 同时检测历史如果最近一条消息超过两小时，主动发起对话
def chat_thread(group_id: int, main_context: AppContext):
    logger.info(f"开始监控：{group_id} {uuid.uuid4()}")
    with main_context:
        while True:
            try:
                sleep_num = 0
                while True:
                    # 获取最近聊天记录
                    recent_history = get_recent_history(group_id)
                    logger.info(f"获取最近聊天记录：{group_id} {recent_history['data'][0]['chat_text']}")
                    last_message = recent_history['data'][0]
                    ai_api_info = last_message['ai_api_info']
                    conversation_id = ai_api_info['openai']['conversation_id']
                    if conversation_id:
                        outer_memory = []
                        for message in recent_history['data'][:min(50, len(recent_history['data']))]:
                            outer_memory.append(
                                {"role": model_name_transform(message["from_user"]["name"]), "message": message['chat_text']})
                        # 倒序outer_memory
                        outer_memory.reverse()
                        if not outer_memory:
                            continue
                        elif (datetime.datetime.now() - datetime.datetime.strptime(recent_history['data'][0]['created_at'], "%Y-%m-%d %H:%M:%S")).seconds > 3600*4 and outer_memory[-1]["role"] != "James Corden":
                            logger.info(f"超过4小时，强制回复：{group_id} {uuid.uuid4()}")
                            res = model_chat(conversation_id, outer_memory=outer_memory, is_force=True)
                        # elif (datetime.datetime.now() - datetime.datetime.strptime(last_message['created_at'], "%Y-%m-%d %H:%M:%S")).seconds > 3600*24:
                        # 如果最后5条都是机器人消息，换个话题
                        elif len(outer_memory) >= 5 and \
                            all([message["role"] == "James Corden" for message in outer_memory[-5:]]) and\
                            (datetime.datetime.now() - datetime.datetime.strptime(recent_history['data'][0]['created_at'], "%Y-%m-%d %H:%M:%S")).seconds > 3600*24:
                            topic = get_topic()
                            query = topic + "Is there anything you'd like to discuss about this news?"
                            logger.info(f"超过24小时，换个话题强制回复：{group_id} {topic} {uuid.uuid4()}")
                            res = model_chat(conversation_id, outer_memory=outer_memory, is_force=True, query=query, user_name="observer")
                        # 如果倒数第二条消息是机器人且最后一条消息不是机器人且与倒数第二条间隔不超过30s,回复
                        elif len(outer_memory) > 1 and \
                            outer_memory[-2]["role"] == "James Corden" and \
                            recent_history['data'][0]['from_user']['name'] != "James Corden" and \
                                (datetime.datetime.strptime(recent_history['data'][0]['created_at'], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(recent_history['data'][1]['created_at'], "%Y-%m-%d %H:%M:%S")).seconds < 30:
                            logger.info(f"倒数第二条消息是机器人，且与最后一条消息间隔不超过30s，强制回复：{group_id} {uuid.uuid4()}")
                            res = model_chat(conversation_id, outer_memory=outer_memory, is_force=True)
                        elif outer_memory[-1]["role"] != "James Corden" and sleep_num > 20:
                            logger.info(f"上一条消息不是机器人，判断回复：{group_id} {uuid.uuid4()}")
                            res = model_chat(conversation_id, outer_memory=outer_memory)
                            sleep_num = 0
                        elif len(outer_memory) > 1 and outer_memory[-1]["role"] == "James Corden" and outer_memory[-2]["role"] == "James Corden":
                            logger.info("上两条消息是机器人，不回复")
                            res = None
                        else:
                            logger.info("未知情况，不回复")
                            res = None
                        if res and isinstance(res, dict):
                            # logger.info(f"model_chat: {res}")
                            # 发送消息
                            logger.info(f"send_message to: {group_id}, {res}")
                            send_chat_message(group_id, res["answer"])
                        else:
                            logger.info(f"{group_id}判断不回复:{datetime.datetime.now()}")
                            sleep_num += 1
                    time.sleep(60)
            except Exception as e:
                logger.error(f"chat_thread error: {traceback.format_exc()}")
                time.sleep(300)
                continue


def init_active_chat(main_app: Flask):
    # group_id_list = get_group_id_list()
    env = main_app.config.get('ENV')
    mode = main_app.config.get('MODE')
    logger.info(f"当前环境：{env}, 当前模式：{mode}")
    if env == 'production' and mode == 'api':
        group_id_list = get_all_groups()
    else:
        group_id_list = [33]
    # group_id_list = []
    logger.info(f"初始化监控群组：{group_id_list}")
    for group_id in group_id_list:
        # 新开线程监控group
        t = threading.Thread(target=chat_thread, args=(group_id, main_app.app_context()))
        t.start()


