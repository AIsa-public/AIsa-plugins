from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.common import invoke_aisa


class WebSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        result = invoke_aisa(
            "tavily_search",
            {"query": tool_parameters.get("query")},
            str(self.runtime.credentials.get("aisa_api_key", "")),
        )
        yield self.create_json_message(result)
