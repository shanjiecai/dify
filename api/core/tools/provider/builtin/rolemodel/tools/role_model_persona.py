import json
import os
from typing import Any, Union

import requests

from core.prompt_const import role_model_customize_system_prompt
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
from mylogger import logger

role_model_customize_service_url = os.environ.get("ROLE_MODEL_CUSTOMIZE_SERVICE_URL", "http://13.56.82.62:8000")


class RoleModelPersonaTool(BuiltinTool):
    def _invoke(
        self, user_id: str, tool_parameters: dict[str, Any]
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        invoke tools
        """
        logger.debug(tool_parameters["modelStudentId"])

        payload = json.dumps({"modelStudentId": tool_parameters["modelStudentId"]})
        headers = {"Content-Type": "application/json"}

        response = requests.request(
            "POST", f"{role_model_customize_service_url}/chat/v1", headers=headers, data=payload
        )
        response = response.json()
        portraitDesignPromptFusion = response.get("portraitDesignPromptFusion", "")
        knowledge = response.get("knowledge", "")
        # print(portraitDesignPromptFusion)
        # print(knowledge)
        res = role_model_customize_system_prompt.format(
            role_set=portraitDesignPromptFusion, knowledge=json.dumps(knowledge, ensure_ascii=False)
        )
        return self.create_text_message(res)
