import datetime
import json
import os
import re
import copy
from typing import cast

from flask_restful import abort, fields, marshal_with, reqparse

from constants.model_template import model_templates
from controllers.console.app.error import ProviderNotInitializeError

# from constants.model_template import model_templates
from controllers.social_agent_api import api
from controllers.social_agent_api.wraps import AppApiResource
from core.errors.error import LLMBadRequestError, ProviderTokenNotInitError
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from core.provider_manager import ProviderManager
from extensions.ext_database import db
from fields.app_fields import model_config_fields
from models import Account
from models.dataset import DatasetUpdateRealTimeSocialAgent
from models.model import App, AppModelConfig, Site
from mylogger import logger
from services.account_service import AccountService, TenantService
from services.app_dsl_service import AppDslService, ImportStatus
from services.app_model_config_service import AppModelConfigService
from services.app_model_service import AppModelService
from services.conversation_service import ConversationService
from services.errors.conversation import ConversationNotExistsError
from sqlalchemy.orm import Session


class AppListApi(AppApiResource):
    """Resource for app variables."""

    parameters_fields = {
        "name": fields.String,
        "id": fields.String,
        # 'model': fields.String,
    }

    @marshal_with(parameters_fields)
    def get(self):
        """
        Get app list
        ---
        tags:
          - app
        responses:
            200:
                description: Get app list
                schema:
                id: AppList
                properties:
                    name:
                    type: string
                    id:
                    type: string
                    default: 1
                    model:
                    type: string
                    default: gpt-4-turbo
        """
        # parser = reqparse.RequestParser()
        # parser.add_argument('page', type=int_range(1), default=1, location='args')
        # parser.add_argument('size', type=int_range(1, 100), default=10, location='args')
        # args = parser.parse_args()
        app_models = AppModelService.get_app_model_config_list()
        # print(app_models)
        # 只取name和id
        app_models_new = []
        for app_model in app_models:
            # print(f"app_model:{app_model.name} {app_model.id}")
            # print(f"app_model:{app_model.model_id}")
            # app_models_new.append({'name': app_model.name, 'id': app_model.id, 'model': app_model.model_id})
            # 只获取包含“个人助理”的APP
            if "个人助理" in app_model.name and app_model.name != "个人助理":
                app_models_new.append({"name": app_model.name, "id": app_model.id})
        return app_models_new


class AppGet(AppApiResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("app_name", type=str, required=True, location="args")
        args = parser.parse_args()
        app = AppModelService.get_app_model_by_app_name("个人助理" + args["app_name"])
        if app is None:
            return {"message": "App not found"}, 404
        else:
            return {
                "id": app.id,
                "name": app.name,
            }


class AppImportApi(AppApiResource):
    def post(self):
        """Import app"""
        # The role of the current user in the ta table must be admin, owner, or editor

        parser = reqparse.RequestParser()
        parser.add_argument("user_name", type=str, required=True, location="json")
        parser.add_argument("user_nick", type=str, required=False, location="json")
        args = parser.parse_args()
        # 读取当前目录下个人助理.yaml文件
        cur_path = os.path.dirname(__file__)
        app = AppModelService.get_app_model_by_app_name("个人助理" + args["user_name"])
        if app:
            return {
                "id": app.id,
                "name": app.name,
            }

        with open(os.path.join(cur_path, "个人助理.yaml"), encoding="utf-8") as f:
            data = f.read().replace("sjc", args["user_name"])
        args.update(
            {"name": None, "description": None, "icon_type": None, "icon": None, "icon_background": None, "data": data}
        )

        first_user = AccountService.get_first_user()
        tenant = TenantService.get_first_tenant()
        first_user.current_tenant = tenant
        # account = cast(Account, first_user)
        with Session(db.engine) as session:
            import_service = AppDslService(session)
            result = import_service.import_app(
                account=first_user,
                import_mode="yaml-content",
                yaml_content=data,
            )
            session.commit()

        status = result.status

        if status == ImportStatus.FAILED.value:
            return result.model_dump(mode="json"), 400
        elif status == ImportStatus.PENDING.value:
            return result.model_dump(mode="json"), 202
        result_data = result.model_dump(mode="json")
        app_id = result_data["app_id"]
        result_data["id"] = app_id
        app = AppModelService.get_app_model_by_app_id(app_id)
        result_data["name"] = app.name
        return result_data, 200


class PersonListApi(AppApiResource):
    person_name_fields = {
        "name": fields.String,
    }

    @marshal_with(person_name_fields)
    def get(self):
        # app_name去掉后面的()之后去重
        app_models = AppModelService.get_app_model_config_list()
        app_models = [app_model.name.split("(")[0] for app_model in app_models]
        app_models = list(set(app_models))
        return [{"name": app_model} for app_model in app_models]


app_detail_fields = {
    "id": fields.String,
    "name": fields.String,
    "mode": fields.String,
    "is_agent": fields.Boolean,
    "model_config": fields.Nested(model_config_fields, attribute="app_model_config"),
}


class AppCreateApi(AppApiResource):
    @marshal_with(app_detail_fields)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, location="json")
        parser.add_argument("model_config", type=dict, location="json")
        parser.add_argument("icon", type=str, location="json")
        parser.add_argument("icon_background", type=str, location="json")
        parser.add_argument("pre_prompt", type=str, location="json", required=False)
        args = parser.parse_args()
        args["mode"] = "chat"
        pre_prompt = args.get("pre_prompt")
        if pre_prompt and len(pre_prompt) > 0 and len(pre_prompt) < 4096:
            pass
        else:
            pre_prompt = "You are a model student in middle school, excelling academically and always willing to help your classmates."
        if not args.get("model_config"):
            args["model_config"] = {
                "opening_statement": "",
                "suggested_questions": [],
                "suggested_questions_after_answer": {"enabled": False},
                "speech_to_text": {"enabled": False},
                "text_to_speech": {"enabled": False, "voice": "", "language": ""},
                "retriever_resource": {"enabled": False},
                "annotation_reply": {"enabled": False},
                "more_like_this": {"enabled": False},
                "sensitive_word_avoidance": {"enabled": False, "type": "", "configs": []},
                "external_data_tools": [],
                "model": {
                    "provider": "openai",
                    "name": "gpt-4-turbo-preview",
                    "mode": "chat",
                    "completion_params": {
                        "temperature": 0,
                        "top_p": 1,
                        "presence_penalty": 0,
                        "frequency_penalty": 0,
                        "max_tokens": 512,
                        "stop": [],
                    },
                },
                "user_input_form": [],
                "dataset_query_variable": "",
                "pre_prompt": "",
                "agent_mode": {"enabled": False, "max_iteration": 5, "strategy": "function_call", "tools": []},
                "prompt_type": "advanced",
                "chat_prompt_config": {"prompt": [{"role": "system", "text": pre_prompt}]},
                "completion_prompt_config": {
                    "prompt": {"text": ""},
                    "conversation_histories_role": {"user_prefix": "", "assistant_prefix": ""},
                },
                "dataset_configs": {"retrieval_model": "single", "datasets": {"datasets": []}},
                "file_upload": {
                    "image": {
                        "enabled": False,
                        "number_limits": 3,
                        "detail": "high",
                        "transfer_methods": ["remote_url", "local_file"],
                    }
                },
            }
        try:
            provider_manager = ProviderManager()
            default_model_entity = provider_manager.get_default_model(
                tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259", model_type=ModelType.LLM
            )
        except (ProviderTokenNotInitError, LLMBadRequestError):
            default_model_entity = None
        except Exception as e:
            logger.error(f"Failed to get default model entity: {e}")
            default_model_entity = None

        admin_user = AccountService.load_user("15270d9e-94bd-4b91-8e2e-a9f33f28f259")
        if args["model_config"] is not None:
            # validate config
            model_config_dict = args["model_config"]

            # Get provider configurations
            provider_manager = ProviderManager()
            provider_configurations = provider_manager.get_configurations("15270d9e-94bd-4b91-8e2e-a9f33f28f259")

            # get available models from provider_configurations
            available_models = provider_configurations.get_models(model_type=ModelType.LLM, only_active=True)

            # check if model is available
            available_models_names = [f"{model.provider.provider}.{model.model}" for model in available_models]
            provider_model = f"{model_config_dict['model']['provider']}.{model_config_dict['model']['name']}"
            if provider_model not in available_models_names:
                if not default_model_entity:
                    raise ProviderNotInitializeError(
                        "No Default System Reasoning Model available. Please configure "
                        "in the Settings -> Model Provider."
                    )
                else:
                    model_config_dict["model"]["provider"] = default_model_entity.provider.provider
                    model_config_dict["model"]["name"] = default_model_entity.model

            model_configuration = AppModelConfigService.validate_configuration(
                tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259",
                account=admin_user,
                config=model_config_dict,
                app_mode=args["mode"],
            )

            app = App(enable_site=True, enable_api=True, is_demo=False, api_rpm=0, api_rph=0, status="normal")

            app_model_config = AppModelConfig()
            app_model_config = app_model_config.from_model_config_dict(model_configuration)
        else:
            if "mode" not in args or args["mode"] is None:
                abort(400, message="mode is required")

            model_config_template = model_templates[args["mode"] + "_default"]

            app = App(**model_config_template["app"])
            app_model_config = AppModelConfig(**model_config_template["model_config"])

            # get model provider
            model_manager = ModelManager()

            try:
                model_instance = model_manager.get_default_model_instance(
                    tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259", model_type=ModelType.LLM
                )
            except ProviderTokenNotInitError:
                model_instance = None

            if model_instance:
                model_dict = app_model_config.model_dict
                model_dict["provider"] = model_instance.provider
                model_dict["name"] = model_instance.model
                app_model_config.model = json.dumps(model_dict)

        app.name = args["name"]
        app.mode = args["mode"]
        app.icon = args["icon"]
        app.icon_background = args["icon_background"]
        app.tenant_id = "15270d9e-94bd-4b91-8e2e-a9f33f28f259"

        db.session.add(app)
        db.session.flush()

        app_model_config.app_id = app.id
        db.session.add(app_model_config)
        db.session.flush()

        app.app_model_config_id = app_model_config.id

        # account = admin_user

        site = Site(
            app_id=app.id,
            title=app.name,
            default_language="en-US",
            customize_token_strategy="not_allow",
            code=Site.generate_code(16),
        )

        db.session.add(site)
        db.session.commit()
        return app, 201


class AppUpdateDataset(AppApiResource):

    def post(self, app_model: App):
        # conversation_id, dataset_id
        parser = reqparse.RequestParser()
        parser.add_argument("app_id", type=str, required=True, location="json", default=None)
        parser.add_argument("dataset_id", type=str, required=True, location="json")
        args = parser.parse_args()

        dataset_update_real_time = DatasetUpdateRealTimeSocialAgent(
            dataset_id=args["dataset_id"],
            app_id=args["app_id"],
            created_at=datetime.datetime.utcnow(),
            last_updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(dataset_update_real_time)
        db.session.commit()
        return {"result": "success"}, 200


# 获取当前文件所在的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
personality_questions_v1_list = open(os.path.join(current_dir, "personality_questions_v1.txt")).readlines()
personality_questions_v1_list = [question.strip() for question in personality_questions_v1_list]


from controllers.social_agent_api.app.openai_base_request import llm_generate_response


# 从app.memory_metadata_dict里获取
# memory_metadata_dict中存personality和answered_questions，answered_questions是一个list，里面存的是已经回答过的问题
# 两种修改方式，用户直接修改和大模型根据对话信息
class AppPersonality(AppApiResource):
    def get(self, app_model: App):
        personality = app_model.memory_metadata_dict.get("personality", "")
        return {"result": "success", "personality": personality}, 200

    def post(self, app_model: App):
        parser = reqparse.RequestParser()
        parser.add_argument("conversation_id", type=str, required=True, location="json")
        args = parser.parse_args()

        # 从 memory_metadata_dict 中获取已回答的问题列表
        answered_questions = app_model.memory_metadata_dict.get("answered_questions", [])

        # 获取对话
        conversation = ConversationService.get_conversation(
            app_model=app_model, conversation_id=args["conversation_id"]
        )
        if not conversation:
            raise ConversationNotExistsError()

        model_manager = ModelManager()
        model_instance = model_manager.get_model_instance(
            tenant_id=app_model.tenant_id,
            provider="openai",
            model_type=ModelType.LLM,
            model="gpt-4o-mini",
        )

        # 获取对话历史
        memory = TokenBufferMemory(conversation=conversation, model_instance=model_instance)
        histories = memory.get_history_prompt_messages(
            max_token_limit=3000,
            message_limit=50,
        )
        histories = [f"{history.role}:{history.content}" for history in histories]

        # 获取之前存储的个性
        previous_personality = app_model.memory_metadata_dict.get("personality", "")

        # 使用优化后的 prompt 进行人格更新
        prompt = (
                "请根据以下对话历史和已回答的问题列表更新个性。\n"
                "确保在更新个性时保留所有重要信息，并仅在必要时进行细微调整。\n"
                "对话历史：\n" + "\n".join(histories) + "\n\n" +
                "已回答的问题列表：\n" + "\n".join(
            [f"- {q['question']}" for q in answered_questions]
        ) + "\n\n"
            "之前的个性：\n" + previous_personality + "\n\n" +
                "请直接开始生成更新后的人格描述："
        )
        # 调用模型生成新的个性描述
        new_personality = llm_generate_response(
            prompt=prompt,
            model="gpt-4o-mini"
        )

        memory_metadata = app_model.memory_metadata_dict
        memory_metadata["personality"] = new_personality
        # 更新个性
        app_model.memory_metadata = memory_metadata
        db.session.commit()

        return {"result": "success", "new_personality": new_personality}, 200
    
    def put(self, app_model: App):
        parser = reqparse.RequestParser()
        parser.add_argument("personality", type=str, required=True, location="json")
        args = parser.parse_args()
        
        # 强制覆盖个性
        if not app_model.memory_metadata:
            app_model.memory_metadata = {}
        new_memory_metadata = copy.deepcopy(app_model.memory_metadata)
        new_memory_metadata["personality"] = args["personality"]
        print("Before commit:", app_model.memory_metadata)
        app_model.memory_metadata = new_memory_metadata
        print("After commit:", app_model.memory_metadata)
        db.session.commit()
        return {"result": "success"}, 200


class AppAnsweredQuestions(AppApiResource):
    def get(self, app_model: App):
        if app_model.memory_metadata_dict:
            answered_questions = app_model.memory_metadata_dict.get("answered_questions", [])
        else:
            answered_questions = []
        answered_question_set = {q["question"] for q in answered_questions}  # 已回答问题的集合

        # 获取所有问题列表
        all_questions = personality_questions_v1_list  # 假设这是所有问题的列表

        # 构建已完成和未完成的问题列表
        completed_questions = [question for question in all_questions if question in answered_question_set]
        incomplete_questions = [question for question in all_questions if question not in answered_question_set]

        # 检查是否所有问题都已完成
        all_completed = len(incomplete_questions) == 0

        return {
            "all_completed": all_completed,
            "completed_questions": completed_questions,
            "incomplete_questions": incomplete_questions,
            "answered_questions": answered_questions,
        }

    def patch(self, app_model: App):
        parser = reqparse.RequestParser()
        parser.add_argument("conversation_id", type=str, required=False, location="json")
        parser.add_argument("histories", type=str, required=False, location="json")
        args = parser.parse_args()

        if not args["conversation_id"] and not args["histories"]:
            raise ("conversation_id or histories is required")
        if args.get("histories"):
            histories = args["histories"]
        else:
            # 获取对话
            conversation = ConversationService.get_conversation(
                app_model=app_model, conversation_id=args["conversation_id"]
            )
            if not conversation:
                raise ConversationNotExistsError()

            model_manager = ModelManager()
            model_instance = model_manager.get_model_instance(
                tenant_id=app_model.tenant_id,
                provider="openai",
                model_type=ModelType.LLM,
                model="gpt-4o-mini",
            )

            # 获取对话历史
            memory = TokenBufferMemory(conversation=conversation, model_instance=model_instance)
            histories = memory.get_history_prompt_messages(
                max_token_limit=3000,
                message_limit=50,
                with_current_query=True,
            )
            if len(histories) <= 2:
                return {"result": "success"}, 200
            histories = "\n".join([f"{history.role.value}:{history.content}" for history in histories])


        # 从 memory_metadata_dict 中获取已回答的问题列表
        if app_model.memory_metadata:
            answered_questions = app_model.memory_metadata.get("answered_questions", [])
        else:
            answered_questions = []
        answered_question_set = {q["question"] for q in answered_questions}  # 已回答问题的集合

        # 生成尚未回答的问题列表
        unanswered_questions = [
            question for question in personality_questions_v1_list
            if question not in answered_question_set
        ]

        # 使用优化后的 prompt 进行问题提取
        prompt = (
                "您的任务是作为一位对比专家，来检查用户是否已经回答了所有未回答的问题。请根据以下步骤完成指定的任务：\n\n"
                "1. 从提供的对话历史中提取用户针对问题列表中的问题的回答。\n"
                "2. 检查用户回答的问题是否与问题列表中的问题相匹配。\n"
                "3. 对于每个匹配的问题，整理出问题及其对应的用户回答，\n"
                "4. 请确保按照以下格式输出每个已回答的问题和对应的回答，多个已回答问题需要换行，如果同一问题回答多次，请只返回最新的一次。：\n"
                "   - 格式为：“问题：用户回答”。\n"
                "   - 例如：问题：你更喜欢直接表达想法还是委婉地表达？\n用户回答：更喜欢直接表达想法。\n"
                "5. 如果用户没有回答任何问题，直接输出“用户没有回答任何问题”。\n"
                "6. 在输出时，确保不要包含任何XML标签。\n\n"
                "对话历史：\n" + histories + "\n\n" +
                "问题列表：\n" + "\n".join(unanswered_questions)  # 使用未回答的问题列表
        )

        # 调用模型生成回答
        response = llm_generate_response(prompt=prompt, model="gpt-4o-mini")
        response = response.choices[0].message.content

        # 处理模型返回的结果
        new_answered_questions = []
        if response:
            response = response.strip()
            # 检查是否用户没有回答任何问题
            if response.startswith("用户没有回答任何问题"):
                return {"result": "success", "answered_questions": answered_questions}, 200

            # 使用正则表达式匹配“问题”和“用户回答”
            # 支持以下格式：
            # 1. 问题: ...\n用户回答: ...
            # 2. 问题: ... 用户回答: ...
            pattern = re.compile(r"问题[:：]\s*(.*?)\s*用户回答[:：]\s*(.*)")

            # 分割响应内容为行
            lines = response.splitlines()
            buffer = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue  # 跳过空行

                buffer += " " + line  # 累积行内容

                match = pattern.search(buffer)
                if match:
                    question = match.group(1).strip()
                    answer = match.group(2).strip()

                    # 检查问题是否已经在已回答列表中
                    if question not in [q["question"] for q in answered_questions] and \
                            question not in [q["question"] for q in new_answered_questions]:
                        new_answered_questions.append({"question": question, "answer": answer})

                    buffer = ""  # 清空缓冲区
                else:
                    # 如果当前缓冲区没有匹配到完整的“问题”和“用户回答”，继续累积
                    continue

            # 处理那些没有换行但包含多个“问题”和“用户回答”的情况
            # 例如：问题: ... 用户回答: ... 问题: ... 用户回答: ...
            multiple_matches = pattern.findall(response)
            for question, answer in multiple_matches:
                question = question.strip()
                answer = answer.strip()
                if question not in [q["question"] for q in answered_questions] and \
                        question not in [q["question"] for q in new_answered_questions]:
                    new_answered_questions.append({"question": question, "answer": answer})

        # 更新 memory_metadata_dict
        if not app_model.memory_metadata:
            app_model.memory_metadata = {}
        answered_questions = copy.deepcopy(app_model.memory_metadata.get("answered_questions", []))
        answered_questions.extend(new_answered_questions)
        new_memory_metadata = copy.deepcopy(app_model.memory_metadata)
        new_memory_metadata["answered_questions"] = answered_questions
        app_model.memory_metadata = new_memory_metadata
        # print("Before commit:", app_model.memory_metadata)
        db.session.commit()
        # print("After commit:", app_model.memory_metadata)

        return {"result": "success", "answered_questions": new_answered_questions}, 200


api.add_resource(AppCreateApi, "/app/create")
api.add_resource(AppListApi, "/app/list")
api.add_resource(AppGet, "/app/check")
api.add_resource(PersonListApi, "/person/list")
api.add_resource(AppUpdateDataset, "/app/update_dataset")
api.add_resource(AppImportApi, "/app/import")
api.add_resource(AppPersonality, "/app/personality")
api.add_resource(AppAnsweredQuestions, "/app/answered_questions")
