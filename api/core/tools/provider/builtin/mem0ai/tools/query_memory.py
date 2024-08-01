import os
import httpx
import json

from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage

from typing import Any, Dict, List, Union
from mem0 import Memory
from core.tools.provider.builtin.mem0ai.tools.utils import vector_config, llm_config, embedding_config


class QueryMem0AIMemory(BuiltinTool):

    def _invoke(self,
                user_id: str,
                tool_parameters: Dict[str, Any],
                ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        """
        Invoke the tool to query memory
        """
        mem0 = Memory.from_config({
            "vector_store": vector_config,
            "llm": llm_config,
            "embedder": embedding_config
        })

        execute_results = mem0.search(
            query=tool_parameters.get("query"),
            user_id=tool_parameters.get("user_id"),
            agent_id=tool_parameters.get("agent_id"),
            run_id=tool_parameters.get("run_id"),
            limit=tool_parameters.get("limit", 100),
            filters=tool_parameters.get("filters") or {}
        )
        return self.create_text_message(f"{execute_results}")
