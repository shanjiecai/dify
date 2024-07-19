from flask_restful import fields, marshal_with, reqparse
from flask_restful.inputs import int_range
from werkzeug.exceptions import NotFound

import services
from controllers.social_agent_api import api

# from controllers.social_agent_api.app import create_or_update_end_user_for_user_id
from controllers.social_agent_api.app.error import NotChatAppError
from controllers.social_agent_api.wraps import AppApiResource
from core.app.entities.app_invoke_entities import InvokeFrom
from libs.helper import TimestampField, uuid_value
from models.model import App, AppMode
from mylogger import logger
from services.message_service import MessageService


class MessageListApi(AppApiResource):
    feedback_fields = {
        'rating': fields.String
    }
    retriever_resource_fields = {
        'id': fields.String,
        'message_id': fields.String,
        'position': fields.Integer,
        'dataset_id': fields.String,
        'dataset_name': fields.String,
        'document_id': fields.String,
        'document_name': fields.String,
        'data_source_type': fields.String,
        'segment_id': fields.String,
        'score': fields.Float,
        'hit_count': fields.Integer,
        'word_count': fields.Integer,
        'segment_position': fields.Integer,
        'index_node_hash': fields.String,
        'content': fields.String,
        'created_at': TimestampField
    }

    message_fields = {
        'id': fields.String,
        'conversation_id': fields.String,
        'inputs': fields.Raw,
        'query': fields.String,
        'answer': fields.String,
        'feedback': fields.Nested(feedback_fields, attribute='user_feedback', allow_null=True),
        'retriever_resources': fields.List(fields.Nested(retriever_resource_fields)),
        'created_at': TimestampField,
        'role': fields.String,
        'assistant_name': fields.String,
    }

    message_infinite_scroll_pagination_fields = {
        'limit': fields.Integer,
        'has_more': fields.Boolean,
        'data': fields.List(fields.Nested(message_fields))
    }

    @marshal_with(message_infinite_scroll_pagination_fields)
    def get(self, app_model: App):
        # if app_model.mode != 'chat':
        #     raise NotChatAppError()

        parser = reqparse.RequestParser()
        parser.add_argument('conversation_id', required=True, type=uuid_value, location='args')
        parser.add_argument('first_id', required=False, type=uuid_value, location='args')
        parser.add_argument('limit', type=int_range(1, 100), required=False, default=20, location='args')
        parser.add_argument('user', type=str, location='args')
        args = parser.parse_args()

        # if end_user is None and args['user'] is not None:
        # end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        try:
            messages = MessageService.pagination_by_first_id(app_model, None,
                                                         args['conversation_id'], args['first_id'], args['limit'])
            logger.info(messages)
            # 获取与app_model相关的dataset_id
            # app_dataset_joins = db.session.query(AppDatasetJoin).filter(
            #     AppDatasetJoin.app_id == "a756e5d2-c735-4f68-8db0-1de49333501c"
            # ).all()
            # dataset_id_list = []
            # if app_dataset_joins:
            #     for app_dataset_join in app_dataset_joins:
            #         dataset_id_list.append(app_dataset_join.dataset_id)
            # logger.info(f"update dataset_id_list: {dataset_id_list}")
            # for dataset_id in dataset_id_list:
            #     update_dataset_id_with_conversation_id_pipeline(args['conversation_id'], dataset_id)
            # update_dataset_id_with_conversation_id_pipeline(conversation_id="14889eb6-267c-41b4-878b-3e3bd75bcf82", dataset_id="d5839cd2-6f76-4a5f-8915-36b22757903a")
            # update_dataset_id_with_conversation_id_pipeline(group_id="316", dataset_id="d5839cd2-6f76-4a5f-8915-36b22757903a")
            # message_str, last_id = get_conversation_message_str(args['conversation_id'])
            # logger.info(f"{message_str} {last_id}")
            # prompt = f"{message_str}\n请从上述对话中总结出james Corden的基本信息，注意不要脱离对话内容，分段回答。"
            # logger.info(generate_response(prompt))
            return messages
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.message.FirstMessageNotExistsError:
            raise NotFound("First Message Not Exists.")


class MessageFeedbackApi(AppApiResource):
    def post(self, app_model, end_user, message_id):
        message_id = str(message_id)

        parser = reqparse.RequestParser()
        parser.add_argument('rating', type=str, choices=['like', 'dislike', None], location='json')
        parser.add_argument('user', type=str, location='json')
        args = parser.parse_args()

        # if end_user is None and args['user'] is not None:
        #     end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        try:
            MessageService.create_feedback(app_model, message_id, end_user, args['rating'])
        except services.errors.message.MessageNotExistsError:
            raise NotFound("Message Not Exists.")

        return {'result': 'success'}


class MessageSuggestedApi(AppApiResource):
    def get(self, app_model, end_user, message_id):
        message_id = str(message_id)
        app_mode = AppMode.value_of(app_model.mode)
        if app_mode not in [AppMode.CHAT, AppMode.AGENT_CHAT, AppMode.ADVANCED_CHAT]:
            raise NotChatAppError()

        try:
            questions = MessageService.get_suggested_questions_after_answer(
                app_model=app_model,
                user=end_user,
                message_id=message_id,
                invoke_from=InvokeFrom.SOCIAL_AGENT_API
            )
        except services.errors.message.MessageNotExistsError:
            raise NotFound("Message Not Exists.")

        return {'result': 'success', 'data': questions}


api.add_resource(MessageListApi, '/messages')
# api.add_resource(MessageFeedbackApi, '/messages/<uuid:message_id>/feedbacks')
# api.add_resource(MessageSuggestedApi, '/messages/<uuid:message_id>/suggested')
