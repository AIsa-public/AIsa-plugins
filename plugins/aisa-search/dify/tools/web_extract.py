from collections.abc import Generator
from typing import Any

from aisa_client import ClientError, parse_extract_urls
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.common import invoke_aisa


class WebExtractTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            urls = parse_extract_urls(tool_parameters.get("urls"))
        except ClientError as exc:
            yield self.create_json_message(
                {
                    "ok": False,
                    "operation": "tavily_extract",
                    "error": {"type": exc.error_type, "message": exc.message},
                }
            )
            return
        result = invoke_aisa(
            "tavily_extract",
            {"urls": urls},
            str(self.runtime.credentials.get("aisa_api_key", "")),
        )
        yield self.create_json_message(result)
