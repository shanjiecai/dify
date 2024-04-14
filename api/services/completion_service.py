import json
import time
from collections.abc import Generator
from typing import Any, Optional, Union

from sqlalchemy import and_

from core.app.app_config.entities import InvokeFrom

# from core.application_manager import ApplicationManager
# from core.entities.application_entities import InvokeFrom
# from core.completion import Completion
# from core.conversation_message_task import PubHandler, ConversationTaskStoppedException, \
#     ConversationTaskInterruptException
from core.file.message_file_parser import MessageFileParser

# from core.model_providers.error import LLMBadRequestError, LLMAPIConnectionError, LLMAPIUnavailableError, \
#     LLMRateLimitError, \
#     LLMAuthorizationError, ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError
from extensions.ext_database import db
from models.model import Account, App, AppModelConfig, Conversation, EndUser, Message
from services.app_model_config_service import AppModelConfigService
from services.errors.app import MoreLikeThisDisabledError
from services.errors.app_model_config import AppModelConfigBrokenError
from services.errors.conversation import ConversationCompletedError, ConversationNotExistsError
from services.errors.message import MessageNotExistsError


class CompletionService:

    @classmethod
    def completion(cls, app_model: App,
                   user: Optional[Union[Account | EndUser]],
                   args: Any,
                   invoke_from: InvokeFrom,
                   streaming: bool = True,
                   is_model_config_override: bool = False,
                   outer_memory: Optional[list] = None,
                   assistant_name: str = None,
                   user_name: str = None) -> Union[dict | Generator]:
        # is streaming mode
        inputs = args['inputs']
        query = args['query']
        files = args['files'] if 'files' in args and args['files'] else []
        auto_generate_name = args['auto_generate_name'] \
            if 'auto_generate_name' in args else True

        # if app_model.mode != 'completion' and not query:
        #     raise ValueError('query is required')

        query = query.replace('\x00', '')

        conversation_id = args['conversation_id'] if 'conversation_id' in args else None
        is_new_message = True
        conversation = None
        if conversation_id:
            conversation_filter = [
                Conversation.id == args['conversation_id'],
                # Conversation.app_id == app_model.id,
                Conversation.status == 'normal'
            ]

            # if isinstance(user, Account):
            #     conversation_filter.append(Conversation.from_account_id == user.id)
            # else:
            #     conversation_filter.append(Conversation.from_end_user_id == user.id if user else None)

            conversation = db.session.query(Conversation).filter(and_(*conversation_filter)).first()

            if not conversation:
                raise ConversationNotExistsError()

            if not query:
                # 选取最后一条message的query作为query
                message = db.session.query(Message).filter(
                    Message.conversation_id == conversation.id,
                    # Message.status == 'normal'
                ).order_by(Message.created_at.desc()).first()
                if not message.answer:
                    is_new_message = False
                    query = message.query if message else ''
                    user_name = message.role if message else ''
                else:
                    is_new_message = True
                    # query = message.answer
                    # user_name = message.role if message else ''

            if conversation.status != 'normal':
                raise ConversationCompletedError()

            assistant_name = app_model.name if app_model else None
            if not conversation.override_model_configs:
                app_model_config = db.session.query(AppModelConfig).filter(
                    # AppModelConfig.id == conversation.app_model_config_id,
                    AppModelConfig.id == app_model.app_model_config_id,
                    AppModelConfig.app_id == app_model.id
                ).first()

                # print(f"assistant_name: {assistant_name}")
                if not app_model_config:
                    raise AppModelConfigBrokenError()
            else:
                conversation_override_model_configs = json.loads(conversation.override_model_configs)

                app_model_config = AppModelConfig(
                    id=conversation.app_model_config_id,
                    app_id=app_model.id,
                )

                app_model_config = app_model_config.from_model_config_dict(conversation_override_model_configs)

            if is_model_config_override:
                # build new app model config
                if 'model' not in args['model_config']:
                    raise ValueError('model_config.model is required')

                if 'completion_params' not in args['model_config']['model']:
                    raise ValueError('model_config.model.completion_params is required')

                completion_params = AppModelConfigService.validate_model_completion_params(
                    cp=args['model_config']['model']['completion_params'],
                    model_name=app_model_config.model_dict["name"]
                )

                app_model_config_model = app_model_config.model_dict
                app_model_config_model['completion_params'] = completion_params
                app_model_config.retriever_resource = json.dumps({'enabled': True})

                app_model_config = app_model_config.copy()
                app_model_config.model = json.dumps(app_model_config_model)
        else:
            if app_model.app_model_config_id is None:
                raise AppModelConfigBrokenError()

            app_model_config = app_model.app_model_config

            if not app_model_config:
                raise AppModelConfigBrokenError()

            if is_model_config_override:
                if not isinstance(user, Account):
                    raise Exception("Only account can override model config")

                # validate config
                model_config = AppModelConfigService.validate_configuration(
                    tenant_id=app_model.tenant_id,
                    account=user,
                    config=args['model_config'],
                    app_mode=app_model.mode
                )

                app_model_config = AppModelConfig(
                    id=app_model_config.id,
                    app_id=app_model.id,
                )

                app_model_config = app_model_config.from_model_config_dict(model_config)

        # clean input by app_model_config form rules
        inputs = cls.get_cleaned_inputs(inputs, app_model_config)

        # parse files
        message_file_parser = MessageFileParser(tenant_id=app_model.tenant_id, app_id=app_model.id)
        file_objs = message_file_parser.validate_and_transform_files_arg(
            files,
            app_model_config,
            user
        )

        application_manager = ApplicationManager()
        return application_manager.generate(
            tenant_id=app_model.tenant_id,
            app_id=app_model.id,
            app_model_config_id=app_model_config.id,
            app_model_config_dict=app_model_config.to_dict(),
            app_model_config_override=is_model_config_override,
            user=user,
            invoke_from=invoke_from,
            inputs=inputs,
            query=query,
            files=file_objs,
            conversation=conversation,
            stream=streaming,
            extras={
                "auto_generate_conversation_name": auto_generate_name
            },
            outer_memory=outer_memory,
            assistant_name=assistant_name,
            user_name=user_name,
            is_new_message=is_new_message,
        )

    @classmethod
    def get_real_user_instead_of_proxy_obj(cls, user: Union[Account, EndUser]):
        if isinstance(user, Account):
            user = db.session.query(Account).filter(Account.id == user.id).first()
        elif isinstance(user, EndUser):
            user = db.session.query(EndUser).filter(EndUser.id == user.id).first()
        else:
            raise Exception("Unknown user type")

        return user

    @classmethod
    def generate_more_like_this(cls, app_model: App, user: Union[Account, EndUser],
                                message_id: str, invoke_from: InvokeFrom, streaming: bool = True) \
            -> Union[dict, Generator]:
        if not user:
            raise ValueError('user cannot be None')

        message = db.session.query(Message).filter(
            Message.id == message_id,
            Message.app_id == app_model.id,
            Message.from_source == ('api' if isinstance(user, EndUser) else 'console'),
            Message.from_end_user_id == (user.id if isinstance(user, EndUser) else None),
            Message.from_account_id == (user.id if isinstance(user, Account) else None),
        ).first()

        if not message:
            raise MessageNotExistsError()

        current_app_model_config = app_model.app_model_config
        more_like_this = current_app_model_config.more_like_this_dict

        if not current_app_model_config.more_like_this or more_like_this.get("enabled", False) is False:
            raise MoreLikeThisDisabledError()

        app_model_config = message.app_model_config
        model_dict = app_model_config.model_dict
        completion_params = model_dict.get('completion_params')
        completion_params['temperature'] = 0.9
        model_dict['completion_params'] = completion_params
        app_model_config.model = json.dumps(model_dict)

        # parse files
        message_file_parser = MessageFileParser(tenant_id=app_model.tenant_id, app_id=app_model.id)
        file_objs = message_file_parser.transform_message_files(
            message.files, app_model_config
        )

        application_manager = ApplicationManager()
        return application_manager.generate(
            tenant_id=app_model.tenant_id,
            app_id=app_model.id,
            app_model_config_id=app_model_config.id,
            app_model_config_dict=app_model_config.to_dict(),
            app_model_config_override=True,
            user=user,
            invoke_from=invoke_from,
            inputs=message.inputs,
            query=message.query,
            files=file_objs,
            conversation=None,
            stream=streaming,
            extras={
                "auto_generate_conversation_name": False
            }
        )

    @classmethod
    def get_cleaned_inputs(cls, user_inputs: dict, app_model_config: AppModelConfig):
        if user_inputs is None:
            user_inputs = {}

        filtered_inputs = {}

        # Filter input variables from form configuration, handle required fields, default values, and option values
        input_form_config = app_model_config.user_input_form_list
        for config in input_form_config:
            input_config = list(config.values())[0]
            variable = input_config["variable"]

            input_type = list(config.keys())[0]

            if variable not in user_inputs or not user_inputs[variable]:
                if input_type == "external_data_tool":
                    continue
                if "required" in input_config and input_config["required"]:
                    raise ValueError(f"{variable} is required in input form")
                else:
                    filtered_inputs[variable] = input_config["default"] if "default" in input_config else ""
                    continue

            value = user_inputs[variable]

            if value:
                if not isinstance(value, str):
                    raise ValueError(f"{variable} in input form must be a string")

            if input_type == "select":
                options = input_config["options"] if "options" in input_config else []
                if value not in options:
                    raise ValueError(f"{variable} in input form must be one of the following: {options}")
            else:
                if 'max_length' in input_config:
                    max_length = input_config['max_length']
                    if len(value) > max_length:
                        raise ValueError(f'{variable} in input form must be less than {max_length} characters')

            filtered_inputs[variable] = value.replace('\x00', '') if value else None

        return filtered_inputs

    # @classmethod
    # def compact_response(cls, pubsub: PubSub, streaming: bool = False) -> Union[dict, Generator]:
    #     generate_channel = list(pubsub.channels.keys())[0].decode('utf-8')
    #     if not streaming:
    #         try:
    #             message_result = {}
    #             for message in pubsub.listen():
    #                 print(message)
    #                 if message["type"] == "message":
    #                     result = message["data"].decode('utf-8')
    #                     result = json.loads(result)
    #                     if result.get('error'):
    #                         cls.handle_error(result)
    #                     if result['event'] == 'annotation' and 'data' in result:
    #                         message_result['annotation'] = result.get('data')
    #                         return cls.get_blocking_annotation_message_response_data(message_result)
    #                     if result['event'] == 'message' and 'data' in result:
    #                         message_result['message'] = result.get('data')
    #                     if result['event'] == 'message_end' and 'data' in result:
    #                         message_result['message_end'] = result.get('data')
    #                         return cls.get_blocking_message_response_data(message_result)
    #         except ValueError as e:
    #             if e.args[0] != "I/O operation on closed file.":  # ignore this error
    #                 raise CompletionStoppedError()
    #             else:
    #                 logging.exception(e)
    #                 raise
    #         finally:
    #             db.session.remove()
    #
    #             try:
    #                 pubsub.unsubscribe(generate_channel)
    #             except ConnectionError:
    #                 pass
    #     else:
    #         def generate() -> Generator:
    #             try:
    #                 for message in pubsub.listen():
    #                     if message["type"] == "message":
    #                         result = message["data"].decode('utf-8')
    #                         result = json.loads(result)
    #                         if result.get('error'):
    #                             cls.handle_error(result)
    #
    #                         event = result.get('event')
    #                         if event == "end":
    #                             logging.debug("{} finished".format(generate_channel))
    #                             break
    #                         if event == 'message':
    #                             yield "data: " + json.dumps(cls.get_message_response_data(result.get('data'))) + "\n\n"
    #                         elif event == 'message_replace':
    #                             yield "data: " + json.dumps(
    #                                 cls.get_message_replace_response_data(result.get('data'))) + "\n\n"
    #                         elif event == 'chain':
    #                             yield "data: " + json.dumps(cls.get_chain_response_data(result.get('data'))) + "\n\n"
    #                         elif event == 'agent_thought':
    #                             yield "data: " + json.dumps(
    #                                 cls.get_agent_thought_response_data(result.get('data'))) + "\n\n"
    #                         elif event == 'annotation':
    #                             yield "data: " + json.dumps(
    #                                 cls.get_annotation_response_data(result.get('data'))) + "\n\n"
    #                         elif event == 'message_end':
    #                             yield "data: " + json.dumps(
    #                                 cls.get_message_end_data(result.get('data'))) + "\n\n"
    #                         elif event == 'ping':
    #                             yield "event: ping\n\n"
    #                         else:
    #                             yield "data: " + json.dumps(result) + "\n\n"
    #             except ValueError as e:
    #                 if e.args[0] != "I/O operation on closed file.":  # ignore this error
    #                     logging.exception(e)
    #                     raise
    #             finally:
    #                 db.session.remove()
    #
    #                 try:
    #                     pubsub.unsubscribe(generate_channel)
    #                 except ConnectionError:
    #                     pass
    #
    #         return generate()

    @classmethod
    def get_message_response_data(cls, data: dict):
        response_data = {
            'event': 'message',
            'task_id': data.get('task_id'),
            'id': data.get('message_id'),
            'answer': data.get('text'),
            'created_at': int(time.time())
        }

        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    @classmethod
    def get_message_replace_response_data(cls, data: dict):
        response_data = {
            'event': 'message_replace',
            'task_id': data.get('task_id'),
            'id': data.get('message_id'),
            'answer': data.get('text'),
            'created_at': int(time.time())
        }

        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    @classmethod
    def get_blocking_message_response_data(cls, data: dict):
        message = data.get('message')
        response_data = {
            'event': 'message',
            'task_id': message.get('task_id'),
            'id': message.get('message_id'),
            'answer': message.get('text'),
            'metadata': {},
            'created_at': int(time.time())
        }

        if message.get('mode') == 'chat':
            response_data['conversation_id'] = message.get('conversation_id')
        if 'message_end' in data:
            message_end = data.get('message_end')
            if 'retriever_resources' in message_end:
                response_data['metadata']['retriever_resources'] = message_end.get('retriever_resources')

        return response_data

    @classmethod
    def get_blocking_annotation_message_response_data(cls, data: dict):
        message = data.get('annotation')
        response_data = {
            'event': 'annotation',
            'task_id': message.get('task_id'),
            'id': message.get('message_id'),
            'answer': message.get('text'),
            'metadata': {},
            'created_at': int(time.time()),
            'annotation_id': message.get('annotation_id'),
            'annotation_author_name': message.get('annotation_author_name')
        }

        if message.get('mode') == 'chat':
            response_data['conversation_id'] = message.get('conversation_id')

        return response_data

    @classmethod
    def get_message_end_data(cls, data: dict):
        response_data = {
            'event': 'message_end',
            'task_id': data.get('task_id'),
            'id': data.get('message_id')
        }
        if 'retriever_resources' in data:
            response_data['retriever_resources'] = data.get('retriever_resources')
        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    @classmethod
    def get_chain_response_data(cls, data: dict):
        response_data = {
            'event': 'chain',
            'id': data.get('chain_id'),
            'task_id': data.get('task_id'),
            'message_id': data.get('message_id'),
            'type': data.get('type'),
            'input': data.get('input'),
            'output': data.get('output'),
            'created_at': int(time.time())
        }

        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    @classmethod
    def get_agent_thought_response_data(cls, data: dict):
        response_data = {
            'event': 'agent_thought',
            'id': data.get('id'),
            'chain_id': data.get('chain_id'),
            'task_id': data.get('task_id'),
            'message_id': data.get('message_id'),
            'position': data.get('position'),
            'thought': data.get('thought'),
            'tool': data.get('tool'),
            'tool_input': data.get('tool_input'),
            'created_at': int(time.time())
        }

        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    @classmethod
    def get_annotation_response_data(cls, data: dict):
        response_data = {
            'event': 'annotation',
            'task_id': data.get('task_id'),
            'id': data.get('message_id'),
            'answer': data.get('text'),
            'created_at': int(time.time()),
            'annotation_id': data.get('annotation_id'),
            'annotation_author_name': data.get('annotation_author_name'),
        }

        if data.get('mode') == 'chat':
            response_data['conversation_id'] = data.get('conversation_id')

        return response_data

    # @classmethod
    # def handle_error(cls, result: dict):
    #     logging.debug("error: %s", result)
    #     error = result.get('error')
    #     description = result.get('description')
    #
    #     # handle errors
    #     llm_errors = {
    #         'ValueError': LLMBadRequestError,
    #         'LLMBadRequestError': LLMBadRequestError,
    #         'LLMAPIConnectionError': LLMAPIConnectionError,
    #         'LLMAPIUnavailableError': LLMAPIUnavailableError,
    #         'LLMRateLimitError': LLMRateLimitError,
    #         'ProviderTokenNotInitError': ProviderTokenNotInitError,
    #         'QuotaExceededError': QuotaExceededError,
    #         'ModelCurrentlyNotSupportError': ModelCurrentlyNotSupportError
    #     }
    #
    #     if error in llm_errors:
    #         raise llm_errors[error](description)
    #     elif error == 'LLMAuthorizationError':
    #         raise LLMAuthorizationError('Incorrect API key provided')
    #     else:
    #         raise Exception(description)
