from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
from extensions.ext_database import db
from models.model import App
from services.account_service import TenantService
import requests


def _get_app(resource_id, tenant_id):
    app = App.query.filter_by(id=resource_id, tenant_id=tenant_id).first()
    return app


class ManageAnsweredQuestionsTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage]:
        """
        通过调用后端API，查看已回答的问题列表
        """
        base_url = "http://127.0.0.1:5001/backend-api/v1"  # 根据实际情况修改
        app_id = tool_parameters.get("app_id")
        if not app_id:
            return self.create_text_message(text="Please provide app_id")

        url = f"{base_url}/app/answered_questions"
        headers = {
            "Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f",  # 根据实际情况修改
            "Content-Type": "application/json"
        }

        # 调用GET请求获取answered_questions信息
        params = {"app_id": app_id}
        url = f"{url}?app_id={app_id}"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            result = response.json()
            # result结构参考AppAnsweredQuestions的返回值结构
            # {
            #   "all_completed": bool,
            #   "completed_questions": list,
            #   "incomplete_questions": list
            # }
            # answered_info = (
            #     f"All Completed: {result.get('all_completed')}\n"
            #     f"Completed Questions: {result.get('completed_questions')}\n"
            #     f"Incomplete Questions: {result.get('incomplete_questions')}"
            # )
            # return self.create_text_message(text=answered_info)
            return self.create_json_message(object=result)
        else:
            # return self.create_text_message(text=f"Error viewing answered questions: {response.text}")
            return self.create_json_message(object={"error": response.text})
