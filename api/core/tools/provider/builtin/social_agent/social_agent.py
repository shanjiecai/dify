from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController

from typing import Any, Dict


class SocialAgentProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        pass
