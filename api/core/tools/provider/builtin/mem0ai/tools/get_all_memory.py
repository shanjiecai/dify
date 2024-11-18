import json
from typing import Any, Union

from mem0 import Memory

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.provider.builtin.mem0ai.tools.utils import (
    embedding_config,
    llm_config,
    vector_config,
)
from core.tools.tool.builtin_tool import BuiltinTool


class GetAllMemory(BuiltinTool):

    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        Retrieve all memories with optional filters
        """
        # 初始化 MemoryClient
        mem0 = Memory.from_config({"vector_store": vector_config, "llm": llm_config, "embedder": embedding_config})

        # 构建过滤器
        _filters = {
            "AND": [
                {"user_id": tool_parameters.get("user_id", user_id)}
            ]
        }

        # 添加 agent_id 筛选
        if tool_parameters.get("agent_id"):
            _filters["AND"].append({"agent_id": tool_parameters.get("agent_id")})

        # 添加时间筛选
        if tool_parameters.get("start_date") and tool_parameters.get("end_date"):
            _filters["AND"].append({
                "created_at": {
                    "gte": tool_parameters.get("start_date"),
                    "lte": tool_parameters.get("end_date")
                }
            })

        # 使用客户端检索记忆
        memories = mem0.get_all(filters=_filters, version="v2")

        # 返回检索到的记忆信息
        return self.create_text_message(json.dumps(memories, indent=2))
