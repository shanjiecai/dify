import requests
from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class UpdateAnsweredQuestionsTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage]:
        """
        调用后端API更新已回答的问题列表
        根据对话内容自动提取并更新已回答的问题
        """
        base_url = "http://127.0.0.1:5001/backend-api/v1"  # 根据实际情况修改
        app_id = tool_parameters.get("app_id")
        conversation_id = tool_parameters.get("conversation_id")

        if not app_id:
            return self.create_text_message(text="Please provide app_id")

        if not conversation_id:
            return self.create_text_message(text="Please provide conversation_id")

        url = f"{base_url}/app/answered_questions"
        headers = {
            "Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f",  # 根据实际情况修改
            "Content-Type": "application/json"
        }

        # 通过PATCH请求更新answered_questions
        # params = {"app_id": app_id}
        payload = {"conversation_id": conversation_id, "app_id": app_id}

        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            # 返回更新后的answered_questions信息
            answered_questions = result.get("answered_questions", [])
            return self.create_text_message(text=f"Answered questions updated: {answered_questions}")
        else:
            return self.create_text_message(text=f"Error updating answered questions: {response.text}")