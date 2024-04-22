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
from controllers.app_api.openai_base_request import generate_response
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
from core.prompt_const import (
    conversation_summary_system_prompt,
    copywriter_system_prompt,
    copywriter_user_prompt,
    plan_summary_system_prompt,
)

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

api_key = os.environ.get('OPENAI_API_KEY')


model_name_dict = {
    "DJ Bot": "James Corden",
}
def model_name_transform(model_name: str):
    if model_name in model_name_dict:
        return model_name_dict[model_name]
    return model_name


class CopywriterApi(AppApiResource):
    def post(self, app_model: App):

        parser = reqparse.RequestParser()
        parser.add_argument('prompt', type=str, required=False, location='json')
        parser.add_argument('kwargs', type=dict, required=False, default={}, location='json')
        args = parser.parse_args()
        prompt = args['prompt']
        kwargs = args['kwargs']

        try:
            query = copywriter_user_prompt.format(content=prompt)
            response = generate_response(
                query,
                copywriter_system_prompt,
                **kwargs
            )

            return {"result": response.choices[0].message.content,
                    }, 200
        except Exception as e:
            logger.info(f"internal server error: {traceback.format_exc()}")
            logger.info(f"args: {args}")
            send_feishu_bot(str(e))
            raise InternalServerError()


api.add_resource(CopywriterApi, '/copywriter')



