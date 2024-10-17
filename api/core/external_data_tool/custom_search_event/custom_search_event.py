from typing import Optional

from core.external_data_tool.base import ExternalDataTool


class YourToolNameTool(ExternalDataTool):
    name: str = "{your_tool_name}"

    @classmethod
    def validate_config(cls, tenant_id: str, config: dict) -> None:
        """
        Validate the incoming form config data.

        :param tenant_id: the id of workspace
        :param config: the form config data
        :return:
        """

        # implement your own validate logic here

    def query(self, inputs: dict, query: Optional[str] = None) -> str:
        """
        Query the external data tool.

        :param inputs: user inputs
        :param query: the query of chat app
        :return: the tool query result
        """
        # implement your own query logic here

        return ""
