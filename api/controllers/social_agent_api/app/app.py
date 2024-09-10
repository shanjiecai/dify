import datetime
import json
import os
from flask_restful import abort, fields, marshal_with, reqparse

from constants.model_template import model_templates
from controllers.console.app.error import ProviderNotInitializeError

# from constants.model_template import model_templates
from controllers.social_agent_api import api
from controllers.social_agent_api.wraps import AppApiResource
from core.errors.error import LLMBadRequestError, ProviderTokenNotInitError
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from core.provider_manager import ProviderManager
from extensions.ext_database import db
from fields.app_fields import model_config_fields
from models.dataset import DatasetUpdateRealTimeSocialAgent
from models.model import App, AppModelConfig, Site
from mylogger import logger
from services.account_service import AccountService
from services.app_dsl_service import AppDslService
from services.account_service import TenantService, AccountService
from services.app_model_config_service import AppModelConfigService
from services.app_model_service import AppModelService


class AppListApi(AppApiResource):
    """Resource for app variables."""

    parameters_fields = {
        'name': fields.String,
        'id': fields.String,
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
                app_models_new.append({'name': app_model.name, 'id': app_model.id})
        return app_models_new


class AppGet(AppApiResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('app_name', type=str, required=True, location='args')
        args = parser.parse_args()
        app = AppModelService.get_app_model_by_app_name("个人助理" + args["app_name"])
        if app is None:
            return {
                "message": "App not found"
            }, 404
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
        args = parser.parse_args()
        # 读取当前目录下个人助理.yaml文件
        cur_path = os.path.dirname(__file__)
        app = AppModelService.get_app_model_by_app_name("个人助理" + args["user_name"])
        if app:
            return {
                "id": app.id,
                "name": app.name,
            }

        with open(os.path.join(cur_path, "个人助理.yaml"), "r", encoding="utf-8") as f:
            data = f.read().replace("sjc", args["user_name"])
        args.update(
            {
                "name": None,
                "description": None,
                "icon_type": None,
                "icon": None,
                "icon_background": None,
                "data": data
            }
        )

        first_user = AccountService.get_first_user()
        tenant = TenantService.get_first_tenant()

        app = AppDslService.import_and_create_new_app(
            tenant_id=tenant.id, data=args["data"], args=args, account=first_user
        )

        return {
            "id": app.id,
            "name": app.name,
        }


class PersonListApi(AppApiResource):
    person_name_fields = {
        'name': fields.String,
    }

    @marshal_with(person_name_fields)
    def get(self):
        # app_name去掉后面的()之后去重
        app_models = AppModelService.get_app_model_config_list()
        app_models = [app_model.name.split('(')[0] for app_model in app_models]
        app_models = list(set(app_models))
        return [{'name': app_model} for app_model in app_models]


app_detail_fields = {
    'id': fields.String,
    'name': fields.String,
    'mode': fields.String,
    'is_agent': fields.Boolean,
    'model_config': fields.Nested(model_config_fields, attribute='app_model_config'),
}


class AppCreateApi(AppApiResource):
    @marshal_with(app_detail_fields)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, location='json')
        parser.add_argument('model_config', type=dict, location='json')
        parser.add_argument('icon', type=str, location='json')
        parser.add_argument('icon_background', type=str, location='json')
        parser.add_argument('pre_prompt', type=str, location='json', required=False)
        args = parser.parse_args()
        args["mode"] = "chat"
        pre_prompt = args.get("pre_prompt")
        if pre_prompt and len(pre_prompt) > 0 and len(pre_prompt) < 4096:
            pass
        else:
            pre_prompt = "You are a model student in middle school, excelling academically and always willing to help your classmates."
        if not args.get("model_config") :
            args["model_config"] = {
  "opening_statement": "",
  "suggested_questions": [],
  "suggested_questions_after_answer": {
    "enabled": False
  },
  "speech_to_text": {
    "enabled": False
  },
  "text_to_speech": {
    "enabled": False,
    "voice": "",
    "language": ""
  },
  "retriever_resource": {
    "enabled": False
  },
  "annotation_reply": {
    "enabled": False
  },
  "more_like_this": {
    "enabled": False
  },
  "sensitive_word_avoidance": {
    "enabled": False,
    "type": "",
    "configs": []
  },
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
      "stop": []
    }
  },
  "user_input_form": [],
  "dataset_query_variable": "",
  "pre_prompt": "",
  "agent_mode": {
    "enabled": False,
    "max_iteration": 5,
    "strategy": "function_call",
    "tools": []
  },
  "prompt_type": "advanced",
  "chat_prompt_config": {
    "prompt": [
      {
        "role": "system",
        "text": pre_prompt
      }
    ]
  },
  "completion_prompt_config": {
    "prompt": {
      "text": ""
    },
    "conversation_histories_role": {
      "user_prefix": "",
      "assistant_prefix": ""
    }
  },
  "dataset_configs": {
    "retrieval_model": "single",
    "datasets": {
      "datasets": []
    }
  },
  "file_upload": {
    "image": {
      "enabled": False,
      "number_limits": 3,
      "detail": "high",
      "transfer_methods": [
        "remote_url",
        "local_file"
      ]
    }
  }
}
        try:
            provider_manager = ProviderManager()
            default_model_entity = provider_manager.get_default_model(
                tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259",
                model_type=ModelType.LLM
            )
        except (ProviderTokenNotInitError, LLMBadRequestError):
            default_model_entity = None
        except Exception as e:
            logger.error(f"Failed to get default model entity: {e}")
            default_model_entity = None

        admin_user = AccountService.load_user("15270d9e-94bd-4b91-8e2e-a9f33f28f259")
        if args['model_config'] is not None:
            # validate config
            model_config_dict = args['model_config']

            # Get provider configurations
            provider_manager = ProviderManager()
            provider_configurations = provider_manager.get_configurations("15270d9e-94bd-4b91-8e2e-a9f33f28f259")

            # get available models from provider_configurations
            available_models = provider_configurations.get_models(
                model_type=ModelType.LLM,
                only_active=True
            )

            # check if model is available
            available_models_names = [f'{model.provider.provider}.{model.model}' for model in available_models]
            provider_model = f"{model_config_dict['model']['provider']}.{model_config_dict['model']['name']}"
            if provider_model not in available_models_names:
                if not default_model_entity:
                    raise ProviderNotInitializeError(
                        "No Default System Reasoning Model available. Please configure "
                        "in the Settings -> Model Provider.")
                else:
                    model_config_dict["model"]["provider"] = default_model_entity.provider.provider
                    model_config_dict["model"]["name"] = default_model_entity.model


            model_configuration = AppModelConfigService.validate_configuration(
                tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259",
                account=admin_user,
                config=model_config_dict,
                app_mode=args['mode']
            )

            app = App(
                enable_site=True,
                enable_api=True,
                is_demo=False,
                api_rpm=0,
                api_rph=0,
                status='normal'
            )

            app_model_config = AppModelConfig()
            app_model_config = app_model_config.from_model_config_dict(model_configuration)
        else:
            if 'mode' not in args or args['mode'] is None:
                abort(400, message="mode is required")

            model_config_template = model_templates[args['mode'] + '_default']

            app = App(**model_config_template['app'])
            app_model_config = AppModelConfig(**model_config_template['model_config'])

            # get model provider
            model_manager = ModelManager()

            try:
                model_instance = model_manager.get_default_model_instance(
                    tenant_id="15270d9e-94bd-4b91-8e2e-a9f33f28f259",
                    model_type=ModelType.LLM
                )
            except ProviderTokenNotInitError:
                model_instance = None

            if model_instance:
                model_dict = app_model_config.model_dict
                model_dict['provider'] = model_instance.provider
                model_dict['name'] = model_instance.model
                app_model_config.model = json.dumps(model_dict)

        app.name = args['name']
        app.mode = args['mode']
        app.icon = args['icon']
        app.icon_background = args['icon_background']
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
            customize_token_strategy='not_allow',
            code=Site.generate_code(16)
        )

        db.session.add(site)
        db.session.commit()
        return app, 201

"""
{
  "opening_statement": "",
  "suggested_questions": [],
  "suggested_questions_after_answer": {
    "enabled": false
  },
  "speech_to_text": {
    "enabled": false
  },
  "text_to_speech": {
    "enabled": false,
    "voice": "",
    "language": ""
  },
  "retriever_resource": {
    "enabled": false
  },
  "annotation_reply": {
    "enabled": false
  },
  "more_like_this": {
    "enabled": false
  },
  "sensitive_word_avoidance": {
    "enabled": false,
    "type": "",
    "configs": []
  },
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
      "stop": []
    }
  },
  "user_input_form": [],
  "dataset_query_variable": "",
  "pre_prompt": "Use the following context as your learned knowledge, inside <context></context> XML tags.\n<context>\n{{#context#}}\n</context>\nWhen answer to user:\n- If you don't know, just say that you don't know.\n- If you don't know when you are not sure, ask for clarification.\nAvoid mentioning that you obtained the information from the context.\ncharacter information:\nMargarita Zmievskaya appears to be a family-oriented and responsible individual, valuing her close relationships with her siblings and cherishing childhood memories with her grandparents. She is focused and goal-driven, prioritizing her education with aspirations to pursue a master's degree in Korea, and shows a strong interest in maritime transportation. Her part-time work assisting her mother's entrepreneurial endeavors indicates adaptability and a practical approach to balancing work with her studies.Her speaking style is Reflective, familial, casual, narrative-driven.\nNow I want you to act as Margarita Zmievskaya to answer user's question based on the above learned knowledge and character information. you must always remember that you are only assigned one personality role. Don’t be verbose or too formal or polite when speaking.",
  "agent_mode": {
    "enabled": false,
    "max_iteration": 5,
    "strategy": "function_call",
    "tools": []
  },
  "prompt_type": "simple",
  "chat_prompt_config": {},
  "completion_prompt_config": {},
  "dataset_configs": {
    "retrieval_model": "single",
    "datasets": {
      "datasets": [
        {
          "dataset": {
            "enabled": true,
            "id": "0be5bdbf-e431-4ffa-b45b-89dc4230608c"
          }
        }
      ]
    }
  },
  "file_upload": {
    "image": {
      "enabled": false,
      "number_limits": 3,
      "detail": "high",
      "transfer_methods": [
        "remote_url",
        "local_file"
      ]
    }
  }
}
"""

"""
{
  "opening_statement": "",
  "suggested_questions": [],
  "suggested_questions_after_answer": {
    "enabled": false
  },
  "speech_to_text": {
    "enabled": false
  },
  "text_to_speech": {
    "enabled": false,
    "voice": "",
    "language": ""
  },
  "retriever_resource": {
    "enabled": false
  },
  "annotation_reply": {
    "enabled": false
  },
  "more_like_this": {
    "enabled": false
  },
  "sensitive_word_avoidance": {
    "enabled": false,
    "type": "",
    "configs": []
  },
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
      "stop": []
    }
  },
  "user_input_form": [],
  "dataset_query_variable": "",
  "pre_prompt": "",
  "agent_mode": {
    "enabled": false,
    "max_iteration": 5,
    "strategy": "function_call",
    "tools": []
  },
  "prompt_type": "advanced",
  "chat_prompt_config": {
    "prompt": [
      {
        "role": "system",
        "text": "Use the following context as your learned knowledge, inside <context></context> XML tags.\n<context>\n{{#context#}}\n</context>\nWhen answer to user:\n- If you don't know, just say that you don't know.\n- If you don't know when you are not sure, ask for clarification.\nAvoid mentioning that you obtained the information from the context.\ncharacter information:\nMargarita Zmievskaya appears to be a family-oriented and responsible individual, valuing her close relationships with her siblings and cherishing childhood memories with her grandparents. She is focused and goal-driven, prioritizing her education with aspirations to pursue a master's degree in Korea, and shows a strong interest in maritime transportation. Her part-time work assisting her mother's entrepreneurial endeavors indicates adaptability and a practical approach to balancing work with her studies.Her speaking style is Reflective, familial, casual, narrative-driven.\nNow I want you to act as Margarita Zmievskaya to answer user's question based on the above learned knowledge and character information. you must always remember that you are only assigned one personality role. Don’t be verbose or too formal or polite when speaking."
      }
    ]
  },
  "completion_prompt_config": {
    "prompt": {
      "text": ""
    },
    "conversation_histories_role": {
      "user_prefix": "",
      "assistant_prefix": ""
    }
  },
  "dataset_configs": {
    "retrieval_model": "single",
    "datasets": {
      "datasets": []
    }
  },
  "file_upload": {
    "image": {
      "enabled": false,
      "number_limits": 3,
      "detail": "high",
      "transfer_methods": [
        "remote_url",
        "local_file"
      ]
    }
  }
}
"""

class AppUpdateDataset(AppApiResource):

    def post(self, app_model: App):
        # conversation_id, dataset_id
        parser = reqparse.RequestParser()
        parser.add_argument('app_id', type=str, required=True, location='json', default=None)
        parser.add_argument('dataset_id', type=str, required=True, location='json')
        args = parser.parse_args()

        dataset_update_real_time = DatasetUpdateRealTimeSocialAgent(
            dataset_id=args['dataset_id'],
            app_id=args['app_id'],
            created_at=datetime.datetime.utcnow(),
            last_updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(dataset_update_real_time)
        db.session.commit()
        return {"result": "success"}, 200


api.add_resource(AppCreateApi, '/app/create')
api.add_resource(AppListApi, '/app/list')
api.add_resource(AppGet, '/app/check')
api.add_resource(PersonListApi, '/person/list')
api.add_resource(AppUpdateDataset, '/app/update_dataset')
api.add_resource(AppImportApi, '/app/import')
