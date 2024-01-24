import os
import json
import logging
import time
from typing import Union, Generator

from flask import stream_with_context, Response
from flask_restful import reqparse
from sqlalchemy import and_
from werkzeug.exceptions import NotFound, InternalServerError

import services
from controllers.app_api import api
from controllers.app_api.app.utils import send_feishu_bot, get_recent_history, get_recent_history_within_timestamp
from controllers.service_api.app import create_or_update_end_user_for_user_id
from controllers.service_api.app.error import AppUnavailableError, ProviderNotInitializeError, NotChatAppError, \
    ConversationCompletedError, CompletionRequestError, ProviderQuotaExceededError, \
    ProviderModelCurrentlyNotSupportError
from controllers.app_api.wraps import AppApiResource
from core.conversation_message_task import PubHandler
from core.completion import Completion
from core.judge_llm_active import judge_llm_active
from core.model_providers.error import LLMBadRequestError, LLMAuthorizationError, LLMAPIUnavailableError, LLMAPIConnectionError, \
    LLMRateLimitError, ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError
from extensions.ext_database import db
from libs.helper import uuid_value
from services.completion_service import CompletionService
from models.model import ApiToken, App, Conversation, AppModelConfig
from mylogger import logger

from extensions.ext_redis import redis_client
from controllers.app_api import api
import traceback
from controllers.app_api.base import generate_response


api_key = os.environ.get('OPENAI_API_KEY')

default_system_prompt = "You are an expert at summarising conversations. The user gives you the content of the dialogue, you summarize the main points of the dialogue, ignoring the meaningless dialogue, summarizing the content in no more than 100 words, and summarizing no more than three tags. Please make sure to output the following format: Summary: 50 words or less based on the current dialogue \nTags: tag 1, tag 2, tag 3"
model_name_dict = {
    "DJ Bot": "James Corden",
}
def model_name_transform(model_name: str):
    if model_name in model_name_dict:
        return model_name_dict[model_name]
    return model_name


class SummarizeApi(AppApiResource):
    def post(self, app_model: App):

        parser = reqparse.RequestParser()
        parser.add_argument('prompt', type=str, required=False, location='json')
        parser.add_argument('group_id', type=int, required=False, location='json')
        parser.add_argument('system_prompt', type=str, required=False, default=default_system_prompt, location='json')
        parser.add_argument("start_timestamp", type=int, required=False, location="json", default=None)
        parser.add_argument("end_timestamp", type=int, required=False, location="json", default=None)
        parser.add_argument('kwargs', type=dict, required=False, default={}, location='json')
        args = parser.parse_args()
        prompt = args['prompt']
        history_str = ""
        if args.get("group_id", None):
            recent_history = get_recent_history_within_timestamp(group_id=args["group_id"], start_timestamp=args["start_timestamp"], end_timestamp=args["end_timestamp"])
            recent_history['data'].reverse()
            for message in recent_history['data'][:min(50, len(recent_history['data']))]:
                # outer_memory.append({"role": model_name_transform(message["from_user"]["name"]), "message": message['chat_text']})
                # role:content\n
                # print(message)
                if message['chat_text']:
                    message['chat_text'].replace("\n", " ")
                history_str += f"{model_name_transform(message['from_user']['name'])}:{message['chat_text']}\n\n"
            print(json.dumps(history_str, ensure_ascii=False))
        system_prompt = args['system_prompt']
        if not system_prompt:
            system_prompt = default_system_prompt
        kwargs = args['kwargs']
        logger.info(f"prompt: {prompt} system_prompt: {system_prompt} kwargs: {kwargs}")
        try:
            response = generate_response(
                api_key,
                prompt if not history_str else history_str,
                system_prompt,
                **kwargs
            )
            # 提取出summary和tags
            try:
                summary = response["choices"][0]["message"]["content"].split("Tags:")[0].strip().split("Summary:")[1].strip()
            except:
                summary = ""
            try:
                tags = response["choices"][0]["message"]["content"].split("Tags:")[1].strip().split(",")
            except:
                tags = []
            return {"result": response["choices"][0]["message"]["content"], "completion_tokens":
                    response["usage"]["completion_tokens"],
                    "prompt_tokens": response["usage"]["prompt_tokens"],
                    "summary": summary, "tags": tags
                    }, 200
        except Exception as e:
            logging.exception(f"internal server error: {traceback.format_exc()}")
            raise InternalServerError()


api.add_resource(SummarizeApi, '/summarize')



