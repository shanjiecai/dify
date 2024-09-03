import json

from models.model import AppMode

model_templates = {
    # completion default mode
    "completion_default": {
        "app": {
            "mode": "completion",
            "enable_site": True,
            "enable_api": True,
            "is_demo": False,
            "api_rpm": 0,
            "api_rph": 0,
            "status": "normal",
        },
        "model_config": {
            "provider": "openai",
            "model_id": "gpt-3.5-turbo-instruct",
            "configs": {
                "prompt_template": "",
                "prompt_variables": [],
                "completion_params": {
                    "max_token": 512,
                    "temperature": 1,
                    "top_p": 1,
                    "presence_penalty": 0,
                    "frequency_penalty": 0,
                },
            },
            "model": json.dumps(
                {
                    "provider": "openai",
                    "name": "gpt-3.5-turbo-instruct",
                    "mode": "completion",
                    "completion_params": {
                        "max_tokens": 512,
                        "temperature": 1,
                        "top_p": 1,
                        "presence_penalty": 0,
                        "frequency_penalty": 0,
                    },
                }
            ),
            "user_input_form": json.dumps(
                [{"paragraph": {"label": "Query", "variable": "query", "required": True, "default": ""}}]
            ),
            "pre_prompt": "{{query}}",
        },
    },
    # chat default mode
    "chat_default": {
        "app": {
            "mode": "chat",
            "enable_site": True,
            "enable_api": True,
            "is_demo": False,
            "api_rpm": 0,
            "api_rph": 0,
            "status": "normal",
        },
        "model_config": {
            "provider": "openai",
            "model_id": "gpt-3.5-turbo",
            "configs": {
                "prompt_template": "",
                "prompt_variables": [],
                "completion_params": {
                    "max_token": 512,
                    "temperature": 1,
                    "top_p": 1,
                    "presence_penalty": 0,
                    "frequency_penalty": 0,
                },
            },
            "model": json.dumps(
                {
                    "provider": "openai",
                    "name": "gpt-3.5-turbo",
                    "mode": "chat",
                    "completion_params": {
                        "max_tokens": 512,
                        "temperature": 1,
                        "top_p": 1,
                        "presence_penalty": 0,
                        "frequency_penalty": 0,
                    },
                }
            ),
        },
    },
}

default_app_templates = {
    # workflow default mode
    AppMode.WORKFLOW: {
        "app": {
            "mode": AppMode.WORKFLOW.value,
            "enable_site": True,
            "enable_api": True,
        }
    },
    # completion default mode
    AppMode.COMPLETION: {
        "app": {
            "mode": AppMode.COMPLETION.value,
            "enable_site": True,
            "enable_api": True,
        },
        "model_config": {
            "model": {
                "provider": "openai",
                "name": "gpt-4o",
                "mode": "chat",
                "completion_params": {},
            },
            "user_input_form": json.dumps(
                [
                    {
                        "paragraph": {
                            "label": "Query",
                            "variable": "query",
                            "required": True,
                            "default": "",
                        },
                    },
                ]
            ),
            "pre_prompt": "{{query}}",
        },
    },
    # chat default mode
    AppMode.CHAT: {
        "app": {
            "mode": AppMode.CHAT.value,
            "enable_site": True,
            "enable_api": True,
        },
        "model_config": {
            "model": {
                "provider": "openai",
                "name": "gpt-4o",
                "mode": "chat",
                "completion_params": {},
            },
        },
    },
    # advanced-chat default mode
    AppMode.ADVANCED_CHAT: {
        "app": {
            "mode": AppMode.ADVANCED_CHAT.value,
            "enable_site": True,
            "enable_api": True,
        },
    },
    # agent-chat default mode
    AppMode.AGENT_CHAT: {
        "app": {
            "mode": AppMode.AGENT_CHAT.value,
            "enable_site": True,
            "enable_api": True,
        },
        "model_config": {
            "model": {
                "provider": "openai",
                "name": "gpt-4o",
                "mode": "chat",
                "completion_params": {},
            },
        },
    },
}
