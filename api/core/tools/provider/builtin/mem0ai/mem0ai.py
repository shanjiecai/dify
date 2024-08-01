from core.tools.entities.tool_entities import ToolInvokeMessage, ToolProviderType
from core.tools.tool.tool import Tool
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError

from core.tools.provider.builtin.google.tools.google_search import GoogleSearchTool

import httpx

from typing import Any, Dict


class GoogleProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        pass
