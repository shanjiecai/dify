from typing import Any, Union

import requests

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class ViewAppTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage]:
        """
        处理查看 App 的操作
        """
        app_name = tool_parameters["app_name"]

        url = f"http://127.0.0.1:5001/backend-api/v1/app/check?app_name={app_name}"
        headers = {"Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f", "Content-Type": "application/json"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return self.create_text_message(text=f"App found: ID = {result['id']}, Name = {result['name']}")
        elif response.status_code == 404:
            return self.create_text_message(text="App not found")
        else:
            return self.create_text_message(text="Error viewing app")
