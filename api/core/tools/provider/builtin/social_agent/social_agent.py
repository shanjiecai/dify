from typing import Any

from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController


class SocialAgentProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        pass
