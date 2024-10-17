import datetime
import os
import threading
import time
import traceback
from pathlib import Path

from flask import Flask
from flask.ctx import AppContext
from werkzeug.datastructures import FileStorage

from controllers.service_api.app.error import ProviderNotInitializeError
# from controllers.social_agent_api.app.utils import *
from core.errors.error import ProviderTokenNotInitError
from extensions.ext_database import db
from models.dataset import Dataset, DatasetUpdateRealTimeSocialAgent
from models.model import UploadFile

# from core.completion import Completion
from mylogger import logger
from services.account_service import AccountService
from services.app_model_service import AppModelService
from services.conversation_service import ConversationService
from services.dataset_service import DocumentService
from services.dataset_update_real_time_social_agent_service import (
    DatasetUpdateRealTimeSocialAgentService,
)
from services.file_service import FileService
from services.message_service import MessageService

api_key = os.environ.get("OPENAI_API_KEY")


def get_conversation_message_str(conversation_id: str | None = None, last_message_updated_at: datetime | None = None):
    conversation_messages_str = ""
    if conversation_id:
        messages = MessageService.pagination_by_more_than_updated_at(
            conversation_id=conversation_id, updated_at=last_message_updated_at
        )
        messages = messages.data
        conversation = ConversationService.get_conversation(app_model=None, conversation_id=conversation_id)
        app_id = conversation.app_id
        app = AppModelService.get_app_model_by_app_id(app_id)
        conversation_assistant_name = app.name.split("(")[0] if app.name else "assistant"
        if messages:
            for message in messages:
                if message.query:
                    conversation_messages_str += message.role or "user" + ": " + message.query + "\n"
                if message.answer:
                    conversation_messages_str += (
                        (message.assistant_name or conversation_assistant_name) + ": " + message.answer + "\n"
                    )
            last_id = messages[-1].id
            last_updated_at = messages[-1].updated_at
            return conversation_messages_str, last_id, last_updated_at
        else:
            return conversation_messages_str, None, None
    else:
        return None, None, None


# 将历史对话存到临时文件中
def save_conversation_to_file(conversation_id: str, app_id: str, conversation_messages_str: str):
    # 获取当前日期
    current_date = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
    # 获取当前对话的对话内容
    conversation_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "tmp", f"{current_date}_{conversation_id or app_id}.txt"
    )
    Path(conversation_file_path).write_text(conversation_messages_str)
    return conversation_file_path


# 上传文件
def upload_file_to_dify(conversation_file_path: str):
    with open(conversation_file_path, "rb") as file:
        filename = os.path.basename(conversation_file_path)
        user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
        file_storage = FileStorage(stream=file, filename=filename)
        upload_file = FileService.upload_file(file_storage, user)
    return upload_file


"""
{
    "name": "sjc's dialuage history",
    "description": "",
    "permission": "only_me",
    "indexing_technique": "high_quality",
    "retrieval_model": {
        "search_method": "hybrid_search",
        "reranking_enable": true,
        "reranking_model": {
            "reranking_provider_name": "cohere",
            "reranking_model_name": "rerank-multilingual-v3.0"
        },
        "top_k": 2,
        "score_threshold_enabled": false,
        "score_threshold": 0
    },
    "embedding_model": "text-embedding-3-small",
    "embedding_model_provider": "openai"
}
"""


def upload_document_with_dataset_id(upload_file: UploadFile, dataset_id: str):
    args = {
        "data_source": {
            "type": "upload_file",
            "info_list": {"data_source_type": "upload_file", "file_info_list": {"file_ids": [upload_file.id]}},
        },
        "indexing_technique": "high_quality",
        "process_rule": {"rules": {}, "mode": "automatic"},
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "retrieval_model": {
            "search_method": "hybrid_search",
            "reranking_enable": True,
            "reranking_model": {
                "reranking_provider_name": "cohere",
                "reranking_model_name": "rerank-multilingual-v3.0",
            },
            "top_k": 2,
            "score_threshold_enabled": False,
            "score_threshold": 0,
        },
        "embedding_model": "text-embedding-3-small",
        "embedding_model_provider": "openai",
    }
    DocumentService.document_create_args_validate(args)
    dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()
    user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
    # logger.info(user)
    try:
        documents, batch = DocumentService.save_document_with_dataset_id(
            dataset=dataset,
            document_data=args,
            account=user,
            dataset_process_rule=dataset.latest_process_rule if "process_rule" not in args else None,
            # 对话更新
            created_from="conversation_update",
        )
    except ProviderTokenNotInitError as ex:
        raise ProviderNotInitializeError(ex.description)
    logger.info(documents)
    return documents


def update_dataset_id_with_app_id_pipeline(dataset_id: str, app_id: str | None = None, last_message_updated_at=None):
    dataset_update_real_time_social_agent = DatasetUpdateRealTimeSocialAgent.query.filter_by(
        dataset_id=dataset_id, app_id=app_id
    ).first()
    conversations = ConversationService.get_conversations_by_app_id(app_id)
    last_message_updated_at_new = last_message_updated_at
    last_message_id_new = None
    for conversation in conversations:
        message_str, last_message_id, last_message_updated_at = get_conversation_message_str(
            conversation.id, last_message_updated_at=last_message_updated_at_new
        )
        logger.info(f"message_str: {message_str} last_id: {last_message_id} last_updated_at: {last_message_updated_at}")
        if not last_message_id or not message_str:
            continue
        tmp_file_path = save_conversation_to_file(conversation.id, app_id, message_str)
        logger.info(tmp_file_path)
        upload_file = upload_file_to_dify(tmp_file_path)
        logger.info(upload_file)
        upload_document_with_dataset_id(upload_file, dataset_id)
        last_message_id_new = last_message_id
        last_message_updated_at_new = last_message_updated_at

    dataset_update_real_time_social_agent.last_update_message_id = last_message_id_new
    dataset_update_real_time_social_agent.last_update_message_updated_at = last_message_updated_at_new
    db.session.commit()


class CountdownTask:

    def __init__(self):
        self._running = True  # 定义线程状态变量

    def terminate(self):
        self._running = False

    def run(self, n):
        # run方法的主循环条件加入对状态变量的判断
        while self._running and n > 0:
            print("T-minus", n)
            n -= 1
            time.sleep(5)
        print("thread is ended")

    def real_time_update(self, dataset_upload_real_time: DatasetUpdateRealTimeSocialAgent, app_context: AppContext):
        with app_context:
            while self._running:
                try:
                    # 获取当前日期
                    # current_date = datetime.datetime.utcnow()
                    update_dataset_id_with_app_id_pipeline(
                        app_id=dataset_upload_real_time.app_id,
                        dataset_id=dataset_upload_real_time.dataset_id,
                        last_message_updated_at=dataset_upload_real_time.last_update_message_updated_at,
                    )
                except:
                    logger.info(f"{traceback.format_exc()}")
                time.sleep(60 * 60 * 8)


task_list = []


def init_dataset_update_real_time_social_agent(main_app: Flask):
    env = main_app.config.get("ENV")
    mode = main_app.config.get("MODE")
    logger.info(f"init_dataset_update_real_time, 当前环境：{env}, 当前模式：{mode}")
    with main_app.app_context():
        try:
            if env == "production" and mode == "api":
                # if mode == 'api':
                dataset_upload_real_time_social_agent_list = (
                    DatasetUpdateRealTimeSocialAgentService.get_all_dataset_upload_real_time_social_agent()
                )
            else:
                dataset_upload_real_time_social_agent_list = []
        except:
            logger.info(f"{traceback.format_exc(limit=10)}")
            dataset_upload_real_time_social_agent_list = []
    logger.info(f"dataset_upload_real_time_list: {dataset_upload_real_time_social_agent_list}")
    if dataset_upload_real_time_social_agent_list:
        for dataset_upload_real_time_social_agent in dataset_upload_real_time_social_agent_list:
            task = CountdownTask()
            t = threading.Thread(
                target=task.real_time_update, args=(dataset_upload_real_time_social_agent, main_app.app_context())
            )
            t.start()
            # 便于之后关闭线程
            task_list.append(task)


def restart_dataset_update_real_time_social_agent(main_app: Flask):
    for task in task_list:
        task.terminate()
    task_list.clear()
    print()
    env = main_app.config.get("ENV")
    mode = main_app.config.get("MODE")
    logger.info(f"restart_dataset_update_real_time, 当前环境：{env}, 当前模式：{mode}")
    with main_app.app_context():
        try:
            if env == "production" and mode == "api":
                # if mode == 'api':
                dataset_upload_real_time_list = (
                    DatasetUpdateRealTimeSocialAgentService.get_all_dataset_upload_real_time()
                )
            else:
                dataset_upload_real_time_list = []
        except:
            logger.info(f"{traceback.format_exc(limit=10)}")
            dataset_upload_real_time_list = []
    logger.info(f"restart dataset_upload_real_time_list: {dataset_upload_real_time_list}")
    if dataset_upload_real_time_list:
        for dataset_upload_real_time in dataset_upload_real_time_list:
            task = CountdownTask()
            t = threading.Thread(target=task.real_time_update, args=(dataset_upload_real_time, main_app.app_context()))
            t.start()
            # 便于之后关闭线程
            task_list.append(task)


if __name__ == "__main__":
    dataset_update_real_time = DatasetUpdateRealTimeSocialAgent(
        dataset_id="5974d4dd-c20c-4665-ac65-b47801e2e9ac",
        app_id="a8e92867-2b58-4252-81d1-39473ad03d75",
        created_at=datetime.datetime.utcnow(),
        last_updated_at=datetime.datetime.utcnow(),
    )
    db.session.add(dataset_update_real_time)
    db.session.commit()
    pass
