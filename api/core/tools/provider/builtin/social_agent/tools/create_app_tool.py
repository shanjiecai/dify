from typing import Any, Union

import requests

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class CreateAppTool(BuiltinTool):
    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any]
                ) -> Union[ToolInvokeMessage]:
        """
        处理创建 App 的操作
        """
        user_name = tool_parameters['user_name']

        url = "http://127.0.0.1:5001/backend-api/v1/app/import"
        headers = {
            "Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f",
            "Content-Type": "application/json"
        }
        payload = {
            "user_name": user_name
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return self.create_text_message(text=f"App created: ID = {result['id']}, Name = {result['name']}")
        else:
            return self.create_text_message(text="Error creating app")
