import json
import os
from typing import Any, Union

import requests

from core.prompt_const import role_model_customize_system_prompt
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

role_model_persona_url = os.environ.get('ROLE_MODEL_PERSONA_URL', 'http://127.0.0.1:8004/chat/v1')


class RoleModelPersonaTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
            invoke tools
        """
        print(tool_parameters["modelStudentId"])
        # return [self.create_text_message('RoleModelPersonaTool invoked'), self.create_text_message('RoleModelPersonaTool invoked')]

        payload = json.dumps({
            "modelStudentId": "75dd0a11-66eb-e57b-c6d5-ad20efdd6a65"
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", role_model_persona_url, headers=headers, data=payload)
        response = response.json()
        portraitDesignPromptFusion = response.get("portraitDesignPromptFusion", "")
        knowledge = response.get("knowledge", "")
        # print(portraitDesignPromptFusion)
        # print(knowledge)
        res = role_model_customize_system_prompt.format(role_set=portraitDesignPromptFusion, knowledge=json.dumps(knowledge, ensure_ascii=False))
        return self.create_text_message(res)
