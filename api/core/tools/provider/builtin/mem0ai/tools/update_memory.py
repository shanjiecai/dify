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


class UpdateMem0AIMemory(BuiltinTool):

    def _invoke(
        self,
        memory_id: str,
        tool_parameters: dict[str, Any],
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        Invoke the tool to update memory
        """
        # 初始化 MemoryClient
        mem0 = Memory.from_config({"vector_store": vector_config, "llm": llm_config, "embedder": embedding_config})

        # 检查是否提供了更新的文本内容
        if not tool_parameters.get("text"):
            raise ValueError("No text content provided for update")

        # 更新记忆
        response = mem0.update(memory_id, tool_parameters.get("text"))

        # 返回更新后的记忆信息
        return self.create_text_message(json.dumps(response, indent=2))
