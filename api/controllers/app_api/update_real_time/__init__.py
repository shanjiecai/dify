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
from controllers.service_api.app.error import ProviderNotInitializeError
from core.errors.error import ProviderTokenNotInitError
from extensions.ext_database import db
from models.dataset import Dataset
from models.model import Conversation, App, AppModelConfig, UploadFile
from mylogger import logger

import threading
import time
import random
import requests

from core.judge_llm_active import judge_llm_active
from services.account_service import AccountService
from services.app_model_service import AppModelService
from services.completion_service import CompletionService
from controllers.app_api.app.utils import *
from controllers.app_api.app.search_event import get_topic, download_from_url
from extensions.ext_redis import redis_client
from services.conversation_service import ConversationService
from services.dataset_service import DocumentService
from services.file_service import FileService
from services.message_service import MessageService

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


def get_conversation_message_str(conversation_id: str, limit=100):
    messages = MessageService.pagination_by_first_id(None, None,
                                                     conversation_id, "", limit)
    messages = messages.data
    conversation_messages_str = ""
    conversation = ConversationService.get_conversation(
        # app_model=app_model,
        app_model=None,
        # user=user,
        conversation_id=conversation_id
    )
    app_id = conversation.app_id
    app = AppModelService.get_app_model_by_app_id(app_id)
    conversation_assistant_name = app.name.split("(")[0]
    for message in messages:
        if message.query:
            conversation_messages_str += message.role + ": " + message.query + "\n"
        if message.answer:
            conversation_messages_str += conversation_assistant_name + ": " + message.answer + "\n"
    return conversation_messages_str


# 将历史对话存到临时文件中
def save_conversation_to_file(conversation_id: str, conversation_messages_str: str):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # 获取当前对话的对话内容
    conversation_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tmp',
                                          f"{current_date}_{conversation_id}.txt")
    with open(conversation_file_path, "w") as f:
        f.write(conversation_messages_str)
    return conversation_file_path


# 上传文件
def upload_file_to_dify(conversation_file_path: str):
    file = open(conversation_file_path, 'rb')
    filename = os.path.basename(conversation_file_path)
    user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
    upload_file = FileService.upload_file(file, user, filename=filename)
    return upload_file


def upload_document_with_dataset_id(upload_file: UploadFile, dataset_id: str):
    args = {
        "data_source": {"type": "upload_file",
                        "info_list": {"data_source_type": "upload_file",
                                      "file_info_list": {"file_ids": [upload_file.id]}}},
        "indexing_technique": "high_quality",
        "process_rule": {"rules": {}, "mode": "automatic"},
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "retrieval_model":
            {"search_method": "hybrid_search",
             "reranking_enable": False,
             "reranking_model": {
                 "reranking_provider_name": "xinference",
                 "reranking_model_name": "bge-base"},
             "top_k": 3,
             "score_threshold_enabled": False,
             "score_threshold": None
             }
    }
    DocumentService.document_create_args_validate(args)
    dataset = db.session.query(Dataset).filter(
        Dataset.id == dataset_id
    ).first()
    user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
    try:
        documents, batch = DocumentService.save_document_with_dataset_id(
            dataset=dataset,
            document_data=args,
            account=user,
            dataset_process_rule=dataset.latest_process_rule if 'process_rule' not in args else None,
            # 对话更新
            created_from='conversation_update'
        )
    except ProviderTokenNotInitError as ex:
        raise ProviderNotInitializeError(ex.description)
    logger.info(documents)
    return documents


def update_dataset_id_with_conversation_id_pipeline(conversation_id: str, dataset_id: str):
    message_str = get_conversation_message_str(conversation_id)
    logger.info(message_str)
    tmp_file_path = save_conversation_to_file(conversation_id, message_str)
    logger.info(tmp_file_path)
    upload_file = upload_file_to_dify(tmp_file_path)
    logger.info(upload_file.__dict__)
    upload_document_with_dataset_id(upload_file, dataset_id)


if __name__ == '__main__':
    pass
