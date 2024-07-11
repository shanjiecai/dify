import json
import logging
import os
import time
import traceback
from collections.abc import Generator
from typing import Union

from flask import Response, stream_with_context
from flask_restful import reqparse
from sqlalchemy import and_
from werkzeug.exceptions import InternalServerError, NotFound

import services
from controllers.app_api import api
from controllers.app_api.app.utils import get_recent_history, get_recent_history_within_timestamp, send_feishu_bot

# import spacy
# nlp = spacy.load("en_core_web_sm")
# from controllers.app_api.openai_base_request import generate_response
from controllers.app_api.wraps import AppApiResource

# from controllers.service_api.app import create_or_update_end_user_for_user_id
from controllers.service_api.app.error import (
    AppUnavailableError,
    CompletionRequestError,
    ConversationCompletedError,
    NotChatAppError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from core.prompt_const import conversation_summary_system_prompt, plan_summary_system_prompt

# from core.conversation_message_task import PubHandler
# from core.completion import Completion
# from core.judge_llm_active import judge_llm_active
# from core.model_providers.error import LLMBadRequestError, LLMAuthorizationError, LLMAPIUnavailableError, LLMAPIConnectionError, \
#     LLMRateLimitError, ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.helper import uuid_value
from models.model import ApiToken, App, AppModelConfig, Conversation
from mylogger import logger
from services.completion_service import CompletionService
from services.openai_base_request_service import generate_response

api_key = os.environ.get('OPENAI_API_KEY')


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
        parser.add_argument('type', type=str, required=False, default="default", location='json')
        parser.add_argument("start_timestamp", type=int, required=False, location="json", default=None)
        parser.add_argument("end_timestamp", type=int, required=False, location="json", default=None)
        parser.add_argument('kwargs', type=dict, required=False, default={}, location='json')
        args = parser.parse_args()
        prompt = args['prompt']
        history_str = ""
        history_with_no_user = ""
        if args.get("group_id", None):
            recent_history = get_recent_history_within_timestamp(group_id=args["group_id"], start_timestamp=args["start_timestamp"], end_timestamp=args["end_timestamp"])
            recent_history['data'].reverse()
            for message in recent_history['data'][:min(50, len(recent_history['data']))]:
                # outer_memory.append({"role": model_name_transform(message["from_user"]["name"]), "message": message['chat_text']})
                # role:content\n
                # print(message)
                if message['chat_text']:
                    message['chat_text'].replace("\n", " ")
                    # history_str += f"{model_name_transform(message['from_user']['name'] if message['from_user'] else message['from_user_id'])}:{message['chat_text']}\n\n"
                    history_str += f"{message['from_user']['name'] if message['from_user'] else message['from_user_id']}:{message['chat_text']}\n\n"
                    history_with_no_user += f"{message['chat_text']}\n\n"
            print(json.dumps(history_str, ensure_ascii=False))
            # print(json.dumps(history_with_no_user, ensure_ascii=False))
        type = args['type']
        if type == "default":
            system_prompt = conversation_summary_system_prompt
        elif type == "plan":
            system_prompt = plan_summary_system_prompt
        else:
            system_prompt = conversation_summary_system_prompt
        kwargs = args['kwargs']
        # logger.info(f"prompt: {prompt} system_prompt: {system_prompt} kwargs: {kwargs}")
        try:
            # doc = nlp(history_with_no_user)
            # nouns = [token.text for token in doc if token.pos_ == "NOUN"]
            # print(nouns)
            query = prompt if not history_str else history_str
            if not query:
                logger.info(f"query is empty args: {args}")
                return {"result": "", "completion_tokens": [], "prompt_tokens": [], "summary": "", "tags": [], "nouns": [], "title": ""}, 200

            response = generate_response(
                query,
                system_prompt,
                **kwargs
            )
            # 提取出summary和tags
            try:
                summary = response.choices[0].message.content.split("Tags:")[0].strip().split("Summary:")[1].strip()
            except:
                summary = ""
            if args['type'] == "plan":
                return {"result": response.choices[0].message.content, "completion_tokens":
                        response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "summary": summary}, 200
            else:
                try:
                    print(response.choices[0].message.content)
                    tags = response.choices[0].message.content.split("Tags:")[1].strip().split("Keywords:")[0].strip().split(",")
                    for i in range(len(tags)):
                        tags[i] = tags[i].strip()
                except:
                    tags = []
                try:
                    nouns = response.choices[0].message.content.split("Keywords:")[1].strip().split("Title:")[0].strip().split(",")
                    for i in range(len(nouns)):
                        nouns[i] = nouns[i].strip()
                except:
                    nouns = []
                try:
                    title = response.choices[0].message.content.split("Title:")[1].strip()
                except:
                    title = ""
                for n in nouns:
                    if n in ["I", "i", "you", "You", "He", "he", "She", "she", "It", "it", "We", "we", "They", "they"]\
                            or "dj bot" in n.lower() or "djbot" in n.lower():
                        nouns.remove(n)
                return {"result": response.choices[0].message.content, "completion_tokens":
                        response.usage.completion_tokens,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "summary": summary, "tags": tags,
                        "nouns": nouns,
                        "title": title
                        }, 200
        except Exception as e:
            logger.info(f"internal server error: {traceback.format_exc()}")
            logger.info(f"args: {args}")
            send_feishu_bot(str(e))
            raise InternalServerError()


api.add_resource(SummarizeApi, '/summarize')



