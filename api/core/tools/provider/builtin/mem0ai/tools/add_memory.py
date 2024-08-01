import json
from typing import Any, Union

from mem0 import Memory

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.provider.builtin.mem0ai.tools.utils import embedding_config, llm_config, vector_config
from core.tools.tool.builtin_tool import BuiltinTool


class AddMem0AIMemory(BuiltinTool):

    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any],
                ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        Invoke the tool to add memory
        """
        mem0 = Memory.from_config({
            "vector_store": vector_config,
            "llm": llm_config,
            "embedder": embedding_config
        })
        try:
            _metadata = json.loads(tool_parameters.get("metadata", "{}"))
        except Exception as e:
            print(e)
            _metadata = {}

        execute_results = mem0.add(
            data=tool_parameters.get("data"),
            user_id=tool_parameters.get("user_id"),
            agent_id=tool_parameters.get("agent_id"),
            run_id=tool_parameters.get("run_id"),
            metadata=_metadata,
            filters=tool_parameters.get("filters") or {},
            prompt=tool_parameters.get("prompt")
        )
        return self.create_text_message(f"{execute_results}")
