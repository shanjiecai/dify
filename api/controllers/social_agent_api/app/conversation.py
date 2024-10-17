from flask import request
from flask_restful import marshal_with, reqparse
from flask_restful.inputs import int_range
from werkzeug.exceptions import NotFound

import services
from controllers.app_api.app import create_or_update_end_user_for_user_id
from controllers.social_agent_api import api
from controllers.social_agent_api.app.error import NotChatAppError
from controllers.social_agent_api.wraps import AppApiResource

# from core.model_providers.model_factory import ModelFactory
from extensions.ext_database import db
from fields.conversation_fields import (
    app_conversation_detail_fields,
    conversation_infinite_scroll_pagination_fields,
    simple_conversation_fields,
)
from libs.exception import BaseHTTPException
from libs.helper import uuid_value
from models.model import App, Conversation
from services.conversation_service import ConversationService


class ConversationApi(AppApiResource):

    @marshal_with(conversation_infinite_scroll_pagination_fields)
    def get(self, app_model):
        """
        获取会话列表
        ---
        tags:
            - conversation
        parameters:
            - in: query
              name: last_id
              type: string
              required: false
              description: 上次获取的最后一个会话的id
            - in: query
              name: limit
              type: integer
              required: false
              description: 本次获取的会话数量
            - in: query
              name: user
              type: string
              required: false
              description: 用户id
        responses:
            200:
                description: 会话列表
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                limit:
                                    type: integer
                                has_more:
                                    type: boolean
                                data:
                                    type: array
                                    items:
                                        $ref: '#/components/schemas/SimpleConversation'
        """
        if app_model.mode != "chat":
            raise NotChatAppError()

        parser = reqparse.RequestParser()
        parser.add_argument("last_id", type=uuid_value, location="args")
        parser.add_argument("limit", type=int_range(1, 100), required=False, default=20, location="args")
        parser.add_argument("user", type=str, location="args")
        args = parser.parse_args()

        # if end_user is None and args['user'] is not None:
        end_user = create_or_update_end_user_for_user_id(app_model, args["user"])

        try:
            return ConversationService.pagination_by_last_id(app_model, end_user, args["last_id"], args["limit"])
        except services.errors.conversation.LastConversationNotExistsError:
            raise NotFound("Last Conversation Not Exists.")

    def post(self, app_model: App):
        """
        创建会话
        ---
        tags:
            - conversation
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                properties:
                  app_id:
                    type: string
                    description: app id
                    required: true
        responses:
            200:
                description: 创建会话成功
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                result:
                                    type: string
                                    default: success
                                conversation_id:
                                    type: string
        """

        app_model_config = app_model.app_model_config.copy()
        model_dict = app_model_config.model_dict

        # if app_model_config.pre_prompt:
        #     system_message = PromptBuilder.to_system_message(app_model_config.pre_prompt, {})
        #     system_instruction = system_message.content
        #     # model_instance = ModelFactory.get_text_generation_model(
        #     #     tenant_id=app_model.tenant_id,
        #     #     model_provider_name=model_dict.get('provider'),
        #     #     model_name=model_dict.get('name')
        #     # )
        #     # system_instruction_tokens = model_instance.get_num_tokens(to_prompt_messages([system_message]))
        # else:
        #     system_message = ""
        #     system_instruction = ""
        #     system_instruction_tokens = 0
        # print(system_instruction)
        end_user = create_or_update_end_user_for_user_id(app_model, "")

        conversation = Conversation(
            app_id=app_model.id,
            app_model_config_id=app_model_config.id,
            model_provider=model_dict.get("provider"),
            model_id=model_dict.get("name"),
            override_model_configs=None,
            mode=app_model.mode,
            name="",
            inputs={},
            introduction=app_model_config.opening_statement,
            system_instruction="",
            system_instruction_tokens=0,
            status="normal",
            from_source="api",
            from_end_user_id=end_user.id,
            from_account_id=None,
        )

        db.session.add(conversation)
        db.session.commit()
        return {"result": "success", "conversation_id": conversation.id}, 200


class ConversationNotFoundError(BaseHTTPException):
    error_code = "app_not_found"
    description = "App not found."
    code = 404


# class ConversationAddMessage(AppApiResource):
#     # 将message添加到conversation中
#     def post(self, app_model: App):
#         """
#         添加消息到会话
#         ---
#         tags:
#             - conversation
#         parameters:
#             - in: body
#               name: body
#               required: true
#               schema:
#                 type: object
#                 properties:
#                   conversation_id:
#                     type: string
#                     description: 会话id
#                     required: true
#                   message:
#                     type: string
#                     description: 消息内容
#                     required: true
#                   user:
#                     type: string
#                     description: 用户角色
#                     required: true
#                   user_id:
#                     type: string
#                     description: 用户id
#                     required: false
#                   mood:
#                     type: string
#                     description: 用户情绪
#                     required: false
#         responses:
#             200:
#                 description: 添加消息成功
#                 content:
#                     application/json:
#                         schema:
#                             type: object
#                             properties:
#                                 result:
#                                     type: string
#                                     default: success
#
#         """
#         app_model_config = AppModelConfig.query.filter_by(app_id=app_model.id).first()
#         model_dict = app_model_config.model_dict
#         parser = reqparse.RequestParser()
#         parser.add_argument('conversation_id', type=str, required=True, location='json')
#         parser.add_argument('message', type=str, required=True, location='json')
#         parser.add_argument('user', type=str, location='json')
#         parser.add_argument('user_id', type=str, location='json')
#         parser.add_argument('mood', type=str, required=False, location='json')
#         args = parser.parse_args()
#
#         if app_model.mode != 'chat':
#             raise NotChatAppError()
#
#         conversation_id = args.get('conversation_id')
#         message = args.get('message')
#         user = args.get('user')
#         user_id = args.get('user_id', None)
#         mood = args.get('mood')
#
#         conversation = Conversation.query.filter_by(id=conversation_id).first()
#         if conversation is None:
#             raise ConversationNotFoundError()
#         # message_id = str(uuid.uuid4())
#         message_class = Message(
#             app_id=app_model.id,
#             model_provider=model_dict.get('provider'),
#             model_id=model_dict.get('name'),
#             override_model_configs=None,
#             conversation_id=conversation.id,
#             inputs={},
#             query=message,
#             message=[],
#             message_tokens=0,
#             message_unit_price=0,
#             message_price_unit=0,
#             answer="",
#             answer_tokens=0,
#             answer_unit_price=0,
#             answer_price_unit=0,
#             provider_response_latency=0,
#             total_price=0,
#             currency="USD",
#             from_source='api',
#             from_end_user_id=None,
#             from_account_id=None,
#             agent_based=True,
#             role=user,
#             role_id=user_id,
#             mood=mood,
#         )
#
#         intent = Intent.NONE
#         metadata = {}
#         judge_force_plan_res = judge_force_plan(message)
#         if judge_force_plan_res == "yes":
#             intent = Intent.JUDGE_FORCE_PLAN
#         else:
#             # 如果没有或生成时间超过8小时，就生成plan_question
#             if not conversation.plan_question_invoke_user or not conversation.plan_question_invoke_time or not conversation.plan_question_invoke_time or conversation.plan_question_invoke_time < datetime.datetime.utcnow() - datetime.timedelta(
#                     hours=8) and app_model.id != "a756e5d2-c735-4f68-8db0-1de49333501c":
#                 # 另起线程执行plan_question
#                 judge_plan_res = judge_plan(message)
#                 if not judge_plan_res.startswith('no'):
#                     intent = Intent.JUDGE_PLAN
#                     metadata = {"judge_plan_res": judge_plan_res}
#                     logger.info(f"add {user}:{message} to conversation {conversation_id} with intent {intent.value} metadata {metadata}")
#                     threading.Thread(target=plan_question_background,
#                                      args=(current_app._get_current_object(), message, conversation,
#                                            user, user_id, judge_plan_res)).start()
#         if intent == Intent.JUDGE_FORCE_PLAN:
#             logger.info(f"add {user}:{message} to conversation {conversation_id} with intent {intent.value} ")
#         elif intent == Intent.NONE:
#             logger.info(f"add {user}:{message} to conversation {conversation_id} ")
#         db.session.add(message_class)
#         db.session.commit()
#         return {"result": "success", "intent": intent.value, "metadata": metadata}, 200


class ConversationDetailApi(AppApiResource):
    @marshal_with(simple_conversation_fields)
    def delete(self, app_model, end_user, c_id):
        if app_model.mode != "chat":
            raise NotChatAppError()

        conversation_id = str(c_id)

        user = request.get_json().get("user")

        if end_user is None and user is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, user)

        try:
            ConversationService.delete(app_model, conversation_id, end_user)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        return {"result": "success"}, 204

    @marshal_with(app_conversation_detail_fields)
    def get(self, app_model, conversation_id):
        conversation = db.session.query(Conversation).filter(Conversation.id == str(conversation_id)).first()
        if not conversation:
            raise NotFound("Conversation Not Exists.")
        return conversation


class ConversationRenameApi(AppApiResource):

    @marshal_with(simple_conversation_fields)
    def post(self, app_model, end_user, c_id):
        if app_model.mode != "chat":
            raise NotChatAppError()

        conversation_id = str(c_id)

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, location="json")
        parser.add_argument("user", type=str, location="json")
        args = parser.parse_args()

        if end_user is None and args["user"] is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, args["user"])

        try:
            return ConversationService.rename(app_model, conversation_id, end_user, args["name"])
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")


# api.add_resource(ConversationRenameApi, '/conversations/<uuid:c_id>/name', endpoint='conversation_name')
api.add_resource(ConversationApi, "/conversations")
# api.add_resource(ConversationApi, '/conversations/<uuid:c_id>', endpoint='conversation')
# api.add_resource(ConversationAddMessage, '/conversations/add_message', endpoint='conversation_message')

api.add_resource(ConversationDetailApi, "/conversations/plan/<uuid:conversation_id>", endpoint="conversation_detail")
# api.add_resource(ConversationDetailApi, '/conversations/<uuid:c_id>', endpoint='conversation_detail')
