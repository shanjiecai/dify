from typing import Any, Union

import requests

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class WorkflowAPITool(BuiltinTool):
    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any]
                ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        调用 Workflow API
        """
        query = tool_parameters['query']
        response_mode = tool_parameters.get('response_mode', 'blocking')
        files = tool_parameters.get('files', [])
        user_name = tool_parameters['user_name']
        agent_name = tool_parameters['agent_name']
        # TODO agent_name to workflow_api_key

        url = "http://127.0.0.1:5001/v1/chat-messages"
        headers = {
            # "Authorization": f"Bearer {self.runtime.credentials['workflow_api_key']}",
            "Authorization": "Bearer app-kJcpTE5fyofhUZyqn2XOxjYv",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {
                "user_name": user_name,
                "agent_name": agent_name,
            },
            "query": query,
            "response_mode": response_mode,
            "conversation_id": "",
            "user": user_id,
            "files": files,
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return self.create_text_message(text=result['answer'])
        else:
            return self.create_text_message(text="Error calling Workflow API")