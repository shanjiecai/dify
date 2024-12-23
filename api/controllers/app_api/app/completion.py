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
from controllers.app_api.app.utils import send_feishu_bot, split_and_get_interval
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
from services.message_service import MessageService


class CompletionApi(AppApiResource):
    def post(self, app_model:App, end_user):
        if app_model.mode != 'completion':
            raise AppUnavailableError()

        parser = reqparse.RequestParser()
        parser.add_argument('inputs', type=dict, required=True, location='json')
        parser.add_argument('query', type=str, location='json', default='')
        parser.add_argument('response_mode', type=str, choices=['blocking', 'streaming'], location='json')
        parser.add_argument('user', type=str, location='json')
        parser.add_argument('retriever_from', type=str, required=False, default='dev', location='json')

        args = parser.parse_args()

        streaming = args['response_mode'] == 'streaming'

        if end_user is None and args['user'] is not None:
            end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        try:
            response = CompletionService.completion(
                app_model=app_model,
                user=end_user,
                args=args,
                from_source='api',
                streaming=streaming
            )

            return compact_response(response)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.conversation.ConversationCompletedError:
            raise ConversationCompletedError()
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except (LLMBadRequestError, LLMAPIConnectionError, LLMAPIUnavailableError,
                LLMRateLimitError, LLMAuthorizationError) as e:
            raise CompletionRequestError(str(e))
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception("internal server error.")
            raise InternalServerError()


class CompletionStopApi(AppApiResource):
    def post(self, app_model, end_user, task_id):
        if app_model.mode != 'completion':
            raise AppUnavailableError()

        PubHandler.stop(end_user, task_id)

        return {'result': 'success'}, 200


class ChatApi(AppApiResource):
    def post(self, app_model):
        # if app_model.mode != 'chat':
        #     raise NotChatAppError()

        parser = reqparse.RequestParser()
        parser.add_argument('inputs', type=dict, required=False, location='json', default={})
        parser.add_argument('query', type=str, required=False, location='json', default='')
        parser.add_argument('response_mode', type=str, choices=['blocking', 'streaming'], location='json')
        parser.add_argument('conversation_id', type=uuid_value, location='json', required=False)
        parser.add_argument('user', type=str, location='json', required=False, default="")
        parser.add_argument('retriever_from', type=str, required=False, default='dev', location='json')
        # outer_memory = [
        #     {"role": "A", "message": "hello"},
        #     {"role": "B", "message": "hi"}
        # ]

        parser.add_argument('outer_memory', type=list, required=False, default=None, location='json')
        # validate
        outer_memory = parser.parse_args()['outer_memory']
        if outer_memory is not None:
            for item in outer_memory:
                if 'role' not in item or 'message' not in item:
                    raise ValueError("outer_memory should be a list of dict with keys 'role' and 'message'")
        args = parser.parse_args()
        # if args["user"] == "default" and outer_memory:
        #     args["user"] = outer_memory[-1]["role"]
        # conversation_id和query不可以同时没有
        if args['conversation_id'] is None and args['query'] == '' and outer_memory is None:
            raise ValueError("conversation_id , query and outer_memory cannot be None all")

        streaming = args['response_mode'] == 'streaming'

        # if end_user is None and args['user'] is not None:
        end_user = create_or_update_end_user_for_user_id(app_model, args['user'])
        try:
            logger.info(f"{app_model.name} {args['conversation_id']} {args['query']} {args['user']}")
            response = CompletionService.completion(
                app_model=app_model,
                user=end_user,
                args=args,
                from_source='api',
                streaming=streaming,
                outer_memory=outer_memory,
                assistant_name=app_model.name,
                user_name=args['user']
            )

            return compact_response(response)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.conversation.ConversationCompletedError:
            raise ConversationCompletedError()
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except (LLMBadRequestError, LLMAPIConnectionError, LLMAPIUnavailableError,
                LLMRateLimitError, LLMAuthorizationError) as e:
            raise CompletionRequestError(str(e))
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception("internal server error.")
            raise InternalServerError()


class ChatActiveApi(AppApiResource):
    try:
        # 主动询问机器人根据当前群聊历史是否应该回话
        def post(self, app_model):
            b = time.time()
            parser = reqparse.RequestParser()
            parser.add_argument('conversation_id', type=uuid_value, location='json')
            parser.add_argument('inputs', type=dict, required=False, location='json', default={})
            parser.add_argument('query', type=str, required=False, location='json', default='')
            args = parser.parse_args()

            conversation_filter = [
                Conversation.id == args['conversation_id'],
                # Conversation.app_id == app_model.id,
                Conversation.status == 'normal'
            ]
            conversation = db.session.query(Conversation).filter(and_(*conversation_filter)).first()
            if not conversation:
                raise NotFound("Conversation Not Exists.")
            app_model_config = db.session.query(AppModelConfig).filter(AppModelConfig.id==conversation.app_model_config_id).first()
            memory = Completion.get_memory_from_conversation(
                tenant_id=app_model.tenant_id,
                app_model_config=app_model_config.copy(),
                conversation=conversation,
                return_messages=False,
                human_prefic="Human",
                assistant_name=app_model.name
            )

            memory.ai_prefix = app_model.name
            memory_key = memory.memory_variables[0]
            external_context = memory.load_memory_variables({})
            histories = external_context[memory_key]
            if memory.last_query:
                histories += "\n" + memory.last_role + ": " + memory.last_query
            logger.info(f"histories: {histories[-100:]}, histories_len: {len(histories)} app_model.name: {app_model.name}")
            logger.info(f"get histories in {time.time() - b}")
            # messages = MessageService.pagination_by_first_id(app_model, None,
            #                                              args['conversation_id'], None, 20)
            # logger.info(f"messages: {messages.data}, app_model.name: {app_model.name}")
            '''
            如果最后三条为：
            A：@app_model.name hello
            app_model.name: hi
            A: how are you?
            则认为是同一个人的追问，应该回话
            '''
            buffer = [dict(item) for item in memory.buffer]
            if memory.last_query:
                buffer.append({"role": memory.last_role, "content": memory.last_query})
            # if len(buffer) >= 3:
            #     # 截取数组最后三条
            #     logger.info(buffer[-3:])
            #
            # if len(buffer) >= 3 and buffer[-2].get("role", None) == app_model.name and \
            #             buffer[-1].get("role", None) == buffer[-3].get("role", None) and \
            #             buffer[-1].get("role", None) != app_model.name and \
            #             buffer[-3].get("role", None) != app_model.name:
            #     logger.info(f"last three messages are from {app_model.name} and other, should response")
            #     judge_result = True
            # else:
            judge_result = judge_llm_active(memory.model_instance.credentials["openai_api_key"], histories,
                                                app_model.name)
            end_user = create_or_update_end_user_for_user_id(app_model, "")
            if judge_result:
                # 对当前conversation上锁，有一个机器人认为应该回话就锁住，避免多个机器人同时回话
                if redis_client.get(conversation.id) is None:
                    redis_client.setex(conversation.id, 40, 1)
                else:
                    logger.info(f"conversation {conversation.id} is locked")
                    return Response(response=json.dumps({"result": False}), status=200, mimetype='application/json')
                response = CompletionService.completion(
                    app_model=app_model,
                    user=end_user,
                    args=args,
                    from_source='api',
                    streaming=False,
                    outer_memory=None,
                    assistant_name=app_model.name,
                    user_name=""
                )
                logger.info(f"get response in {time.time() - b}")
                response["result"] = True
                logger.info(f"response: {response}")
                return Response(response=json.dumps(response), status=200, mimetype='application/json')

            logger.info(judge_result)
            logger.info(time.time() - b)
            # return {"result": judge_result}
            return Response(response=json.dumps({"result": judge_result}), status=200, mimetype='application/json')
    except Exception as e:
        logger.exception("error in chat active api")
        send_feishu_bot(str(e))
        raise e


# class ChatStopApi(AppApiResource):
#     def post(self, app_model, end_user, task_id):
#         if app_model.mode != 'chat':
#             raise NotChatAppError()
#
#         PubHandler.stop(end_user, task_id)
#
#         return {'result': 'success'}, 200


def compact_response(response: Union[dict | Generator]) -> Response:
    if isinstance(response, dict):
        if "answer" in response and response["answer"] is not None and len(response["answer"]) > 200:
            sentence_list, interval_list = split_and_get_interval(response["answer"])
            response["sentence_list"] = sentence_list
            response["interval_list"] = interval_list
        return Response(response=json.dumps(response), status=200, mimetype='application/json')
    else:
        def generate() -> Generator:
            try:
                for chunk in response:
                    yield chunk
            except services.errors.conversation.ConversationNotExistsError:
                yield "data: " + json.dumps(api.handle_error(NotFound("Conversation Not Exists.")).get_json()) + "\n\n"
            except services.errors.conversation.ConversationCompletedError:
                yield "data: " + json.dumps(api.handle_error(ConversationCompletedError()).get_json()) + "\n\n"
            except services.errors.app_model_config.AppModelConfigBrokenError:
                logging.exception("App model config broken.")
                yield "data: " + json.dumps(api.handle_error(AppUnavailableError()).get_json()) + "\n\n"
            except ProviderTokenNotInitError as ex:
                yield "data: " + json.dumps(api.handle_error(ProviderNotInitializeError(ex.description)).get_json()) + "\n\n"
            except QuotaExceededError:
                yield "data: " + json.dumps(api.handle_error(ProviderQuotaExceededError()).get_json()) + "\n\n"
            except ModelCurrentlyNotSupportError:
                yield "data: " + json.dumps(api.handle_error(ProviderModelCurrentlyNotSupportError()).get_json()) + "\n\n"
            except (LLMBadRequestError, LLMAPIConnectionError, LLMAPIUnavailableError,
                    LLMRateLimitError, LLMAuthorizationError) as e:
                yield "data: " + json.dumps(api.handle_error(CompletionRequestError(str(e))).get_json()) + "\n\n"
            except ValueError as e:
                yield "data: " + json.dumps(api.handle_error(e).get_json()) + "\n\n"
            except Exception:
                logging.exception("internal server error.")
                yield "data: " + json.dumps(api.handle_error(InternalServerError()).get_json()) + "\n\n"

        return Response(stream_with_context(generate()), status=200,
                        mimetype='text/event-stream')


# api.add_resource(CompletionApi, '/completion-messages')
# api.add_resource(CompletionStopApi, '/completion-messages/<string:task_id>/stop')
api.add_resource(ChatApi, '/chat-messages')  # 只有被@才会调用，后续合并到chat-messages-active
api.add_resource(ChatActiveApi, '/chat-messages-active')
# api.add_resource(ChatStopApi, '/chat-messages/<string:task_id>/stop')

