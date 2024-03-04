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
# from core.conversation_message_task import PubHandler
# from core.completion import Completion
# from core.judge_llm_active import judge_llm_active
# from core.model_providers.error import LLMBadRequestError, LLMAuthorizationError, LLMAPIUnavailableError, LLMAPIConnectionError, \
#     LLMRateLimitError, ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError
from extensions.ext_database import db
from libs.helper import uuid_value
from services.completion_service import CompletionService
from models.model import ApiToken, App, Conversation, AppModelConfig
from mylogger import logger

from extensions.ext_redis import redis_client
from controllers.app_api import api
import traceback
# import spacy
# nlp = spacy.load("en_core_web_sm")
from controllers.app_api.base import generate_response


api_key = os.environ.get('OPENAI_API_KEY')

default_system_prompt = "You are an expert at summarising conversations. The user gives you the content of the dialogue, you summarize the main points of the dialogue, ignoring the meaningless dialogue, summarizing the content in no more than 50 words, and summarizing no more than three tags, no more than ten meaningful noun except name and no more than 10 words title. Please generate summary,title,tags,title using Chinese if the primary language of the conversation is Chinese and make sure to output the following format: Summary: 50 words or less based on the current dialogue \nTags: tag 1, tag 2, tag 3 \nNouns: noun 1, noun 2, noun 3 \nTitle: title of the summary. \n\nFor example: Summary: The cat sat on the mat. \nTags: cat, mat, sat \nNouns: cat, mat, sat \nTitle: The cat sat on the mat. \n\nPlease make sure to output the following format: Summary: 50 words or less based on the current dialogue \nTags: tag 1, tag 2, tag 3 \nNouns: noun 1, noun 2, noun 3 \nTitle: title of the summary in 10 words or less."
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
        system_prompt = args['system_prompt']
        if not system_prompt:
            system_prompt = default_system_prompt
        kwargs = args['kwargs']
        # logger.info(f"prompt: {prompt} system_prompt: {system_prompt} kwargs: {kwargs}")
        try:
            # doc = nlp(history_with_no_user)
            # nouns = [token.text for token in doc if token.pos_ == "NOUN"]
            # print(nouns)
            query = prompt if not history_str else history_str,
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
            try:
                tags = response.choices[0].message.content.split("Tags:")[1].strip().split("Nouns:")[0].strip().split(",")
                for i in range(len(tags)):
                    tags[i] = tags[i].strip()
            except:
                tags = []
            try:
                nouns = response.choices[0].message.content.split("Nouns:")[1].strip().split("Title:")[0].strip().split(",")
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
            send_feishu_bot(str(e))
            raise InternalServerError()


api.add_resource(SummarizeApi, '/summarize')



