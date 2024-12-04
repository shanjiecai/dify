from typing import Any, Union

import requests

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool
from extensions.ext_database import db
from models.model import ApiToken, App
from services.account_service import TenantService


def _get_resource(resource_id, tenant_id):
    resource = App.query.filter_by(id=resource_id, tenant_id=tenant_id).first()
    return resource


def create_app_api_key(resource_id: str):
    tenant = TenantService.get_first_tenant()
    tenant_id = tenant.id
    resource_id = str(resource_id)
    _get_resource(resource_id, tenant_id)
    key = ApiToken.generate_api_key("app-", 24)
    api_token = ApiToken()
    api_token.app_id = resource_id
    api_token.tenant_id = tenant_id
    api_token.token = key
    api_token.type = "app"
    db.session.add(api_token)
    db.session.commit()


class CreateAppTool(BuiltinTool):
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage]:
        """
        处理创建 App 的操作
        """
        user_name = tool_parameters["user_name"]
        user_nick = tool_parameters.get("user_nick", None)

        url = "http://127.0.0.1:5001/backend-api/v1/app/import"
        headers = {"Authorization": "Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f", "Content-Type": "application/json"}
        # payload = {"user_name": user_name}
        payload = {
            "user_nick": user_nick,
            "user_name": user_name,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            create_app_api_key(result['id'])
            return self.create_text_message(text=f"App created: ID = {result['id']}, Name = {result['name']}")
        else:
            return self.create_text_message(text="Error creating app")
