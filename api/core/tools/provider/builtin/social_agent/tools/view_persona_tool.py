from typing import Any, Union
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
import requests


class GetPersonaTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage]:
        """
        工具功能：获取指定 App 的人设。
        """
        base_url = "http://127.0.0.1:5001/backend-api/v1"  # 后端地址
        app_id = tool_parameters.get("app_id")

        if not app_id:
            return self.create_text_message(text="请提供 app_id 参数。")

        headers = {
            "Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f",  # 替换为实际 API 密钥
            "Content-Type": "application/json",
        }

        try:
            url = f"{base_url}/app/personality"
            params = {"app_id": app_id}
            url = f"{url}?app_id={app_id}"
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return self.create_text_message(text=response.json()["personality"])
            else:
                return self.create_text_message(
                    text=f"获取人设失败：状态码 {response.status_code} - {response.text}"
                )
        except requests.RequestException as e:
            return self.create_text_message(text=f"请求失败：{str(e)}")