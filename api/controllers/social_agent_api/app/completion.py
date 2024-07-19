import json
import logging
import traceback
from collections.abc import Generator
from typing import Union

from flask import Response, request, stream_with_context
from flask_restful import reqparse
from werkzeug.exceptions import InternalServerError, NotFound

import services
from controllers.social_agent_api import api

# from controllers.social_agent_api.app import create_or_update_end_user_for_user_id
from controllers.social_agent_api.app.error import (
    AppUnavailableError,
    CompletionRequestError,
    ConversationCompletedError,
    NotChatAppError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from controllers.social_agent_api.app.utils import send_feishu_bot, split_and_get_interval
from controllers.social_agent_api.wraps import AppApiResource
from core.app.apps.base_app_queue_manager import AppQueueManager
from core.app.entities.app_invoke_entities import InvokeFrom

# from core.application_manager import ApplicationManager
# from core.application_queue_manager import ApplicationQueueManager
# from core.entities.application_entities import InvokeFrom
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.model_runtime.errors.invoke import InvokeError
from extensions.ext_database import db
from libs.helper import uuid_value
from models.model import App
from mylogger import logger
from services.app_generate_service import AppGenerateService


class CompletionApi(AppApiResource):
    def post(self, app_model: App, end_user):
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

        # if end_user is None and args['user'] is not None:
        #     end_user = create_or_update_end_user_for_user_id(app_model, args['user'])

        try:
            # response = CompletionService.completion(
            #     app_model=app_model,
            #     user=end_user,
            #     args=args,
            #     invoke_from=InvokeFrom.social_agent_api,
            #     streaming=streaming
            # )
            response = AppGenerateService.generate(
                app_model=app_model,
                user=end_user,
                args=args,
                invoke_from=InvokeFrom.SOCIAL_AGENT_API,
                streaming=streaming,
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
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception as e:
            logging.exception("internal server error.")
            raise InternalServerError()


class ChatStopApi(AppApiResource):
    def post(self, app_model, _, task_id):
        if app_model.mode != 'chat':
            raise NotChatAppError()

        end_user_id = request.get_json().get('user')

        AppQueueManager.set_stop_flag(task_id, InvokeFrom.social_agent_api, end_user_id)

        return {'result': 'success'}, 200


# def _plan_finish_question(conversation: Conversation, main_context: AppContext):
#     """
#     Plan finish question
#     :param conversation: conversation
#     :return:
#     """
#     with main_context:
#         plan_detail_list = []
#         plan_detail, plan, history_str = ConversationService.generate_plan(conversation.id,
#                                                                            plan=conversation.plan_question_invoke_plan)
#         plan_detail_list.append(plan_detail)
#         logger.info(f"generate_final_plan_from_conversation response: {plan_detail_list}")
#         image_list, img_perfect_prompt_list = generate_plan_img_pipeline(
#             conversation.plan_question_invoke_plan, model="search_engine")
#         # 暂时不去掉plan_question_invoke_plan
#         # conversation.plan_question_invoke_plan = None
#         # logger.info(conversation.id)
#         conversation.plan_question_invoke_user = None
#         conversation.plan_question_invoke_user_id = None
#         conversation.plan_question_invoke_time = None
#         # logger.info(conversation.__dict__)
#         conversation_plan_detail = ConversationPlanDetail(
#             conversation_id=conversation.id,
#             plan=plan,
#             plan_detail_list=plan_detail_list,
#             plan_conversation_history=history_str,
#             image_list=image_list,
#             img_perfect_prompt_list=img_perfect_prompt_list
#         )
#         time.sleep(1)
#         db.session.add(conversation_plan_detail)
#         db.session.add(conversation)
#         db.session.commit()
#         logger.info(f"plan finish commit {conversation.id} {plan}")


"""
response
{
    "event": "message",
    "task_id": "dc579871-cb30-43f9-a2cf-dfc2cac7a73c",
    "id": "c1e833a7-99d0-41cc-abb7-fa05456577d7",
    "message_id": "c1e833a7-99d0-41cc-abb7-fa05456577d7",
    "conversation_id": "6348267e-ee2a-4373-9702-e03e6f65d3d6",
    "mode": "chat",
    "answer": "Oh, hang on, we're stuck in a bit of a time loop here, aren't we? But you know, it's always good to reminisce about the good old days, especially when they involve singing at the top of your lungs with the people you love most. Keeps you grounded, doesn't it? Plus, it's a great reminder of where you've come from and the simple joys that shape us. So, Jack, got any cherished memories of your own you'd like to belt out?",
    "metadata": {
        "usage": {
            "prompt_tokens": 861,
            "prompt_unit_price": "0.01",
            "prompt_price_unit": "0.001",
            "prompt_price": "0.0086100",
            "completion_tokens": 103,
            "completion_unit_price": "0.03",
            "completion_price_unit": "0.001",
            "completion_price": "0.0030900",
            "total_tokens": 964,
            "total_price": "0.0117000",
            "currency": "USD",
            "latency": 5.549383770907298
        }
    },
    "created_at": 1715264236,
    "sentence_list": [
        "Oh, hang on, we're stuck in a bit of a time loop here, aren't we?",
        "But you know, it's always good to reminisce about the good old days, especially when they involve singing at the top of your lungs with the people you love most.",
        "Keeps you grounded, doesn't it?",
        "Plus, it's a great reminder of where you've come from and the simple joys that shape us.",
        "So, Jack, got any cherished memories of your own you'd like to belt out?"
    ],
    "interval_list": [
        23.0,
        4.4,
        12.6,
        10.3
    ]
}
"""


class ChatApi(AppApiResource):
    def post(self, app_model):
        """
        Chat API
        ---
        tags:
            - chat
        parameters:
            - in: body
              name: body
              required: true
              schema:
                type: object
                properties:
                    query:
                        type: string
                        description: The query for the chat model
                        required: false
                    user:
                        type: string
                        description: The user for the chat model
                        required: false
                    user_id:
                        type: string
                        description: The user_id for the chat model
                        required: false
                    response_mode:
                        type: string
                        description: The response mode for the chat model, blocking or streaming
                        default: blocking
                        required: false
                    conversation_id:
                        type: string
                        description: The conversation id for the chat model
                        required: false
                    outer_memory:
                        type: array
                        description: The outer memory for the chat model, deprecated
                        required: false
                    inputs:
                        type: object
                        description: The inputs for the chat model
                        required: false
                    app_id:
                        type: string
                        description: The app id for the chat model
                        required: true
        responses:
            200:
                description: The response from the chat model
                schema:
                    type: object
                    properties:
                        event:
                            type: string
                            description: The event type
                        task_id:
                            type: string
                            description: The task id
                        id:
                            type: string
                            description: The id
                        message_id:
                            type: string
                            description: The message id
                        conversation_id:
                            type: string
                            description: The conversation id
                        mode:
                            type: string
                            description: The mode
                        answer:
                            type: string
                            description: The answer
                        metadata:
                            type: object
                            description: The metadata
                        created_at:
                            type: integer
                            description: The created at
                        sentence_list:
                            type: array
                            description: The sentence list
                        interval_list:
                            type: array
                            description: The interval list


        """

        parser = reqparse.RequestParser()
        parser.add_argument('inputs', type=dict, required=False, location='json', default={})
        parser.add_argument('query', type=str, required=False, location='json', default='')
        parser.add_argument('response_mode', type=str, choices=['blocking', 'streaming'], location='json')
        parser.add_argument('conversation_id', type=uuid_value, location='json', required=False)
        parser.add_argument('user', type=str, location='json', required=False, default="")
        parser.add_argument('user_id', type=str, location='json', required=False, default="")
        parser.add_argument('retriever_from', type=str, required=False, default='dev', location='json')
        parser.add_argument('auto_generate_name', type=bool, required=False, default=True, location='json')
        # outer_memory = [
        #     {"role": "A", "message": "hello"},
        #     {"role": "B", "message": "hi"}
        # ]
        mode = app_model.mode
        parser.add_argument('outer_memory', type=list, required=False, default=None, location='json')
        # validate
        outer_memory = parser.parse_args()['outer_memory']
        if outer_memory is not None:
            for item in outer_memory:
                if 'role' not in item or 'message' not in item:
                    raise ValueError("outer_memory should be a list of dict with keys 'role' and 'message'")
        args = parser.parse_args()
        # conversation_id和query不可以同时没有
        if args['conversation_id'] is None and args['query'] == '' and outer_memory is None:
            raise ValueError("conversation_id , query and outer_memory cannot be None all")

        streaming = args['response_mode'] == 'streaming'
        # if args["conversation_id"]:
        #     conversation_filter = [
        #         Conversation.id == args['conversation_id'],
        #         # Conversation.app_id == app_model.id,
        #         Conversation.status == 'normal'
        #     ]
        #     conversation = db.session.query(Conversation).filter(and_(*conversation_filter)).first()
        #     if conversation and (
        #             not conversation.plan_question_invoke_user or conversation.plan_question_invoke_time < datetime.datetime.utcnow() - datetime.timedelta(
        #             hours=8)) and app_model.id not in ["a756e5d2-c735-4f68-8db0-1de49333501c",
        #                                                "19d2fd0b-6e1c-47f9-87ab-cc039b6d3881",
        #                                                "4cb1eee5-72d9-4cd6-befc-e4e0d4fb6333",
        #                                                "cee86a23-56ab-4b3d-a548-ca34191b23a1"] and args["query"]:
        #         # 另起线程执行plan_question
        #         threading.Thread(target=plan_question_background,
        #                          args=(current_app._get_current_object(), args["query"], conversation,
        #                                args["user"], None)).start()

        # # 补充modelStudentId
        # if args["user_id"]:
        #     args["input"]["modelStudentId"] = args["user_id"]
        # if end_user is None and args['user'] is not None:
        # end_user = create_or_update_end_user_for_user_id(app_model, args['user'])
        try:
            # raise InvokeError("test")
            logger.info(f"{app_model.name} {args['conversation_id']} {args['query']} {args['user']}")
            # 去掉outer_memory逻辑
            response = AppGenerateService.generate(
                app_model=app_model,
                user=None,
                args=args,
                invoke_from=InvokeFrom.SERVICE_API,
                streaming=streaming,
                user_name=args['user'],
                assistant_name=app_model.name,
                user_id=args['user_id'],
            )
            # if isinstance(response, dict) and response.get("answer", '').__contains__(
            #         '<finish_question>') and args["conversation_id"] and mode == AppMode.CHAT.value:
            #     logger.info(
            #         f"remove conversation {conversation.id} <finish_question> from {response.get('answer')}")
            #     threading.Thread(target=_plan_finish_question,
            #                      args=(conversation, current_app._get_current_object().app_context())).start()
            return compact_response(response)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.conversation.ConversationCompletedError:
            raise ConversationCompletedError()
        except services.errors.app_model_config.AppModelConfigBrokenError:
            # logging.exception("App model config broken.")
            logging.info(f"{traceback.format_exc(limit=5)}")
            raise AppUnavailableError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            send_feishu_bot(str(e))
            try:
                from services.account_service import AccountService
                logger.info("使用备用模型回复")
                # 新建db.session
                db.session.rollback()
                """{"provider": "zhipuai", "name": "chatglm_turbo", "mode": "chat", "completion_params": {"temperature": 0.95, "top_p": 0.7, "stop": []}}"""
                args["model_config"] = {"model": {
                    "provider": "zhipuai",
                    "name": "glm-3-turbo",
                    "mode": "chat",
                    "completion_params": {
                        "temperature": 0.95,
                        "top_p": 0.7,
                        "stop": []
                    }
                }
                }
                user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
                # 去掉outer_memory逻辑
                response = AppGenerateService.generate(
                    app_model=app_model,
                    user=user,
                    args=args,
                    invoke_from=InvokeFrom.SERVICE_API,
                    streaming=streaming,
                    user_name=args['user'],
                    assistant_name=app_model.name,
                )
                # if isinstance(response, dict) and response.get("answer", '').endswith(
                #         '<finish_question>') and args["conversation_id"] and mode == AppMode.CHAT.value:
                #     logger.info(
                #         f"remove conversation {conversation.id} <finish_question> from {response.get('answer')}")
                #     threading.Thread(target=_plan_finish_question,
                #                      args=(conversation, current_app._get_current_object().app_context())).start()
                return compact_response(response)
            except Exception as _e:
                logger.info(f"使用备用模型回复失败: {str(traceback.format_exc())}")

            raise CompletionRequestError(e.description)
        except ValueError as e:
            send_feishu_bot(str(e))
            raise e
        except Exception as e:
            send_feishu_bot(str(e))
            # logging.exception("internal server error.")
            logging.info(f"{traceback.format_exc(limit=5)}")
            raise InternalServerError()


# class ChatActiveApi(AppApiResource):
#     try:
#         # 主动询问机器人根据当前群聊历史是否应该回话
#         def post(self, app_model):
#             """
#             Chat Active API
#             ---
#             tags:
#                 - chat
#             parameters:
#                 - in: body
#                   name: body
#                   required: true
#                   schema:
#                     type: object
#                     properties:
#                         conversation_id:
#                             type: string
#                             description: The conversation id for the chat model
#                             required: true
#                         query:
#                             type: string
#                             description: The query for the chat model
#                             required: false
#                         user:
#                             type: string
#                             description: The user for the chat model
#                             required: false
#                         user_id:
#                             type: string
#                             description: The user_id for the chat model
#                             required: false
#                         response_mode:
#                             type: string
#                             description: The response mode for the chat model, blocking or streaming
#                             default: blocking
#                             required: false
#                         outer_memory:
#                             type: array
#                             description: The outer memory for the chat model, deprecated
#                             required: false
#                         app_id:
#                             type: string
#                             description: The app id for the chat model
#                             required: true
#             """
#             b = time.time()
#             parser = reqparse.RequestParser()
#             parser.add_argument('conversation_id', type=uuid_value, location='json')
#             parser.add_argument('inputs', type=dict, required=False, location='json', default={})
#             parser.add_argument('query', type=str, required=False, location='json', default='')
#             parser.add_argument('outer_memory', type=list, required=False, default=None, location='json')
#             parser.add_argument('user', type=str, location='json', required=False, default="")
#             parser.add_argument('response_mode', type=str, choices=['blocking', 'streaming'], location='json')
#             parser.add_argument("user_id", type=str, location='json', required=False, default="")
#             # validate
#             outer_memory = parser.parse_args()['outer_memory']
#             if outer_memory is not None:
#                 for item in outer_memory:
#                     if 'role' not in item or 'message' not in item:
#                         raise ValueError("outer_memory should be a list of dict with keys 'role' and 'message'")
#             mode = app_model.mode
#             args = parser.parse_args()
#
#             streaming = args.get('response_mode', 'blocking') == 'streaming'
#
#             conversation_filter = [
#                 Conversation.id == args['conversation_id'],
#                 # Conversation.app_id == app_model.id,
#                 Conversation.status == 'normal'
#             ]
#             conversation = db.session.query(Conversation).filter(and_(*conversation_filter)).first()
#
#             if conversation.plan_question:
#                 judge_result = True
#             else:
#                 app_model_config = db.session.query(AppModelConfig).filter(
#                     AppModelConfig.id == conversation.app_model_config_id
#                 ).first()
#
#                 # application_manager = ApplicationManager()
#                 # app_orchestration_config = application_manager.convert_from_app_model_config_dict(app_model.tenant_id, app_model_config.to_dict())
#                 # model_config = app_model_config.model_config
#
#                 app_config = ChatAppConfigManager.get_app_config(
#                     app_model=app_model,
#                     app_model_config=app_model_config,
#                     conversation=conversation,
#                     override_config_dict=None
#                 )
#                 model_config = ModelConfigConverter.convert(app_config)
#
#                 model_instance = ModelInstance(
#                     provider_model_bundle=model_config.provider_model_bundle,
#                     model=model_config.model
#                 )
#                 memory = TokenBufferMemory(
#                     conversation=conversation,
#                     model_instance=model_instance
#                 )
#
#                 history_list = memory.get_history_prompt_messages(
#                     max_token_limit=2000
#                 )
#                 histories = ""
#                 for history in history_list:
#                     if not history.content and not history.name:
#                         continue
#                     histories += history.name if history.name else "user"
#                     histories += ": " + history.content if history.content else ""
#                     histories += "\n"
#                 logger.info(f"histories: {histories}, app_model.name: {app_model.name}")
#                 logger.info(f"get histories in {time.time() - b}")
#                 # messages = MessageService.pagination_by_first_id(app_model, None,
#                 #                                              args['conversation_id'], None, 20)
#                 # logger.info(f"messages: {messages.data}, app_model.name: {app_model.name}")
#                 '''
#                 如果最后三条为：
#                 A：@app_model.name hello
#                 app_model.name: hi
#                 A: how are you?
#                 则认为是同一个人的追问，应该回话
#                 '''
#                 # buffer = [dict(item) for item in memory.buffer]
#                 # if memory.last_query:
#                 #     buffer.append({"role": memory.last_role, "content": memory.last_query})
#                 # if len(buffer) >= 3:
#                 #     # 截取数组最后三条
#                 #     logger.info(buffer[-3:])
#                 #
#                 # if len(buffer) >= 3 and buffer[-2].get("role", None) == app_model.name and \
#                 #             buffer[-1].get("role", None) == buffer[-3].get("role", None) and \
#                 #             buffer[-1].get("role", None) != app_model.name and \
#                 #             buffer[-3].get("role", None) != app_model.name:
#                 #     logger.info(f"last three messages are from {app_model.name} and other, should response")
#                 #     judge_result = True
#                 # else:
#                 #     judge_result = judge_llm_active(memory.model_instance.credentials["openai_api_key"], histories,
#                 #                                     app_model.name)
#                 judge_result = judge_llm_active(memory.model_instance.credentials["openai_api_key"], histories,
#                                                 app_model.name)
#             # judge_result = True
#             end_user = create_or_update_end_user_for_user_id(app_model, "")
#             if judge_result:
#                 # 对当前conversation上锁，有一个机器人认为应该回话就锁住，避免多个机器人同时回话
#                 # 暂时关掉锁
#                 # if redis_client.get(conversation.id) is None:
#                 #     redis_client.setex(conversation.id, 10, 1)
#                 # else:
#                 #     logger.info(f"conversation {conversation.id} is locked")
#                 #     return Response(response=json.dumps({"result": False}), status=200, mimetype='application/json')
#
#                 try:
#                     if args["conversation_id"]:
#                         if conversation and (
#                                 not conversation.plan_question_invoke_user or not conversation.plan_question_invoke_time or conversation.plan_question_invoke_time < datetime.datetime.utcnow() - datetime.timedelta(
#                                 hours=8)) and app_model.id not in ["a756e5d2-c735-4f68-8db0-1de49333501c",
#                                                                    "19d2fd0b-6e1c-47f9-87ab-cc039b6d3881",
#                                                                    "4cb1eee5-72d9-4cd6-befc-e4e0d4fb6333",
#                                                                    "cee86a23-56ab-4b3d-a548-ca34191b23a1"] and args[
#                             "query"]:
#                             # 另起线程执行plan_question
#                             threading.Thread(target=plan_question_background,
#                                              args=(current_app._get_current_object(), args["query"], conversation,
#                                                    args["user"], None)).start()
#                     response = AppGenerateService.generate(
#                         app_model=app_model,
#                         user=end_user,
#                         args=args,
#                         invoke_from=InvokeFrom.social_agent_api,
#                         streaming=streaming,
#                         assistant_name=app_model.name,
#                         user_name="",
#                     )
#                     logger.info(f"get response in {time.time() - b}")
#                     response["result"] = True
#                     logger.info(f"response: {response}")
#                     if isinstance(response, dict) and mode == AppMode.CHAT.value and response.get("answer",
#                                                                                                   '').__contains__(
#                             '<finish_question>') and conversation:
#                         logger.info(
#                             f"remove conversation {conversation.id} <finish_question> from {response.get('answer')}")
#                         threading.Thread(target=_plan_finish_question,
#                                          args=(conversation, current_app._get_current_object().app_context())).start()
#                     return Response(response=json.dumps(response), status=200, mimetype='application/json')
#                 except InvokeError as e:
#                     send_feishu_bot(str(e))
#                     logger.info("使用备用模型回复")
#                     try:
#                         from services.account_service import AccountService
#                         logger.info("使用备用模型回复")
#                         # 新建db.session
#                         db.session.rollback()
#                         """{"provider": "zhipuai", "name": "chatglm_turbo", "mode": "chat", "completion_params": {"temperature": 0.95, "top_p": 0.7, "stop": []}}"""
#                         args["model_config"] = {"model": {
#                             "provider": "zhipuai",
#                             "name": "glm-3-turbo",
#                             "mode": "chat",
#                             "completion_params": {
#                                 "temperature": 0.95,
#                                 "top_p": 0.7,
#                                 "stop": []
#                             }
#                         }
#                         }
#                         user = AccountService.load_user("1c795cbf-0924-4f01-aec5-1b5abef50bca")
#                         # response = CompletionService.completion(
#                         #     app_model=app_model,
#                         #     user=user,
#                         #     args=args,
#                         #     invoke_from=InvokeFrom.social_agent_api,
#                         #     streaming=streaming,
#                         #     outer_memory=outer_memory,
#                         #     assistant_name=app_model.name,
#                         #     user_name=args['user'],
#                         #     is_model_config_override=True,
#                         # )
#                         response = AppGenerateService.generate(
#                             app_model=app_model,
#                             user=user,
#                             args=args,
#                             invoke_from=InvokeFrom.SERVICE_API,
#                             streaming=streaming,
#                             user_name=args['user'],
#                             assistant_name=app_model.name,
#                         )
#                         return compact_response(response)
#                     except Exception as _e:
#                         logger.info(f"使用备用模型回复失败: {str(traceback.format_exc())}")
#
#             logger.info(judge_result)
#             logger.info(time.time() - b)
#             # return {"result": judge_result}
#             return Response(response=json.dumps({"result": judge_result}), status=200, mimetype='application/json')
#     except Exception as e:
#         logger.exception("error in chat active api")
#         send_feishu_bot(str(e))
#         raise e


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
                # for chunk in response:
                #     yield chunk
                yield from response
            except services.errors.conversation.ConversationNotExistsError:
                yield "data: " + json.dumps(
                    api.handle_error(NotFound("Conversation Not Exists.")).get_json()) + "\n\n"
            except services.errors.conversation.ConversationCompletedError:
                yield "data: " + json.dumps(api.handle_error(ConversationCompletedError()).get_json()) + "\n\n"
            except services.errors.app_model_config.AppModelConfigBrokenError:
                logging.exception("App model config broken.")
                yield "data: " + json.dumps(api.handle_error(AppUnavailableError()).get_json()) + "\n\n"
            except ProviderTokenNotInitError as ex:
                yield "data: " + json.dumps(
                    api.handle_error(ProviderNotInitializeError(ex.description)).get_json()) + "\n\n"
            except QuotaExceededError:
                yield "data: " + json.dumps(api.handle_error(ProviderQuotaExceededError()).get_json()) + "\n\n"
            except ModelCurrentlyNotSupportError:
                yield "data: " + json.dumps(
                    api.handle_error(ProviderModelCurrentlyNotSupportError()).get_json()) + "\n\n"
            except InvokeError as e:
                yield "data: " + json.dumps(api.handle_error(CompletionRequestError(e.description)).get_json()) + "\n\n"
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
# api.add_resource(ChatActiveApi, '/chat-messages-active')
# api.add_resource(ChatStopApi, '/chat-messages/<string:task_id>/stop')
