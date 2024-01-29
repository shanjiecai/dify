import datetime
import traceback
import uuid
import os

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
from controllers.app_api.app.search_event import get_topic, download_from_url
from extensions.ext_redis import redis_client
api_key = os.environ.get('OPENAI_API_KEY')




# 根据对话实时更新知识库
# 每天导出AI bot所有对话为一个文件，新文件重新加入当前AI bot知识库，并总结当日对话内容

def real_time_update():
    while True:
        try:
            # 获取当前日期
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            # 获取所有对话
            conversations = Conversation.query.all()
            # 获取所有对话的对话内容
            conversation_content = [conversation.content for conversation in conversations]
            # 获取所有对话的对话时间
            conversation_time = [conversation.created_at for conversation in conversations]
            # 获取所有对话的对话id
            conversation_id = [conversation.id for conversation in conversations]
            # 获取所有对话的对话用户
            conversation_user = [conversation.user_id for conversation in conversations]
            # 获取所有对话的对话app
        except:
            logger.info(f"{traceback.format_exc()}")
            time.sleep(60)
            continue


def init_real_time_update(main_app: Flask):
    # group_id_list = get_group_id_list()
    env = main_app.config.get('ENV')
    mode = main_app.config.get('MODE')
    logger.info(f"当前环境：{env}, 当前模式：{mode}")
    try:
        if env == 'production' and mode == 'api':
            group_id_list = get_all_groups(only_dj_bot=False)
        else:
            # group_id_list = []
            group_id_list = []
    except:
        logger.info(f"{traceback.format_exc()}")
        group_id_list = []
    # group_id_list = []
    logger.info(f"初始化实时更新群组：{group_id_list}")
    for group_id in group_id_list:
        # 新开线程监控group
        t = threading.Thread(target=real_time_update, args=(group_id, main_app.app_context()))
        t.start()




