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
from controllers.app_api.app.utils import (
    get_recent_history,
    get_recent_history_within_timestamp,
    send_feishu_bot,
)
from controllers.app_api.img.utils import generate_img_pipeline

# from controllers.app_api.openai_base_request import generate_response
from controllers.app_api.wraps import AppApiResource
from models.model import ApiToken, App, AppModelConfig, Conversation
from mylogger import logger

# from services.completion_service import CompletionService

api_key = os.environ.get("OPENAI_API_KEY")


# 获取图片，支持dalle和search_engine
class ImgApi(AppApiResource):
    def post(self, app_model: App):
        """
        img api
        ---
        tags:
          - img
        parameters:
          - in: body
            name: body
            schema:
              id: img
              required:
                - prompt
              properties:
                prompt:
                  type: string
                  description: img prompt
                model:
                  type: string
                  description: dalle3 or search_engine
                shape:
                  type: string
                  description: square, vertical, horizontal
        responses:
          200:
            description: img
            schema:
              id: img
              properties:
                images:
                  type: array
                  items:
                    type: object
                    properties:
                      uuid:
                        type: string

        """
        parser = reqparse.RequestParser()
        parser.add_argument("prompt", type=str, required=True, help="img prompt")
        parser.add_argument("model", type=str, default="search_engine", required=False, help="dalle3 or search_engine")
        parser.add_argument("shape", type=str, default=None, required=False, help="shape: square, vertical, horizontal")
        args = parser.parse_args()
        prompt = args.get("prompt")
        model = args.get("model")
        shape = args.get("shape")
        images = generate_img_pipeline(prompt, model=model, shape=shape)
        return {"images": images}, 200


api.add_resource(ImgApi, "/img")
