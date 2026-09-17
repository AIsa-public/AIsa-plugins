"""Shared, dependency-free client for the read-only AIsa Search API."""

from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
from urllib import error, parse, request


VERSION = "0.1.2"
DEFAULT_BASE_URL = "https://api.aisa.one"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

EXIT_INPUT = 2
EXIT_AUTH = 3
EXIT_UPSTREAM = 4


@dataclass(frozen=True)
class Operation:
    method: str
    path: str
    encoding: str
    required_fields: Tuple[str, ...]


OPERATIONS: Mapping[str, Operation] = {
    "tavily_search": Operation("POST", "/apis/v1/tavily/search", "json", ("query",)),
    "tavily_extract": Operation("POST", "/apis/v1/tavily/extract", "json", ("urls",)),
    "twitter_advanced_search": Operation(
        "GET", "/apis/v1/twitter/tweet/advanced_search", "query", ("query",)
    ),
    "youtube_search": Operation("GET", "/apis/v1/youtube/search", "query", ("q",)),
    "scholar_search_web": Operation(
        "POST", "/apis/v1/scholar/search/web", "scholar_form", ("query",)
    ),
}


class ClientError(Exception):
    def __init__(
        self,
        exit_code: int,
        error_type: str,
        message: str,
        http_status: Optional[int] = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.error_type = error_type
        self.message = message
        self.http_status = http_status
        self.details = details


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _validate_public_url(raw_url: Any) -> None:
    if not isinstance(raw_url, str):
        raise ClientError(EXIT_INPUT, "invalid_input", "Extract URLs must be strings.")
    parsed = parse.urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ClientError(EXIT_INPUT, "invalid_input", "Extract URLs must use HTTP or HTTPS.")
    if parsed.username or parsed.password:
        raise ClientError(EXIT_INPUT, "invalid_input", "Credential-bearing URLs are not allowed.")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise ClientError(
            EXIT_INPUT, "invalid_input", "Local or private-network URLs are not allowed."
        )
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if not address.is_global:
        raise ClientError(
            EXIT_INPUT, "invalid_input", "Local or private-network URLs are not allowed."
        )


def parse_extract_urls(value: Any) -> list[str]:
    """Parse one to three newline- or comma-separated public URLs."""
    if not isinstance(value, str):
        raise ClientError(EXIT_INPUT, "invalid_input", "URLs must be provided as text.")
    urls = [item.strip() for item in value.replace(",", "\n").splitlines() if item.strip()]
    if not 1 <= len(urls) <= 3:
        raise ClientError(EXIT_INPUT, "invalid_input", "Provide between one and three URLs.")
    for raw_url in urls:
        _validate_public_url(raw_url)
    return urls


def validate_payload(operation_name: str, payload: Mapping[str, Any]) -> None:
    operation = OPERATIONS[operation_name]
    missing = [field for field in operation.required_fields if not _nonempty(payload.get(field))]
    if missing:
        raise ClientError(
            EXIT_INPUT,
            "invalid_input",
            "Missing required field(s): " + ", ".join(missing) + ".",
        )
    if operation_name == "tavily_extract":
        urls = payload.get("urls")
        if not isinstance(urls, list) or not 1 <= len(urls) <= 3:
            raise ClientError(
                EXIT_INPUT,
                "invalid_input",
                "tavily_extract requires between one and three URLs.",
            )
        for raw_url in urls:
            _validate_public_url(raw_url)


def validate_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    parsed = parse.urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ClientError(
            EXIT_INPUT,
            "invalid_config",
            "AISA_BASE_URL must be an HTTP(S) origin without credentials, path, query, "
            "or fragment.",
        )
    return value


def user_agent_for(host: str) -> str:
    if host == "claude_code":
        return "claude-code/aisa-search/" + VERSION
    if host == "dify":
        return "dify/aisa-search/" + VERSION
    return "openai-codex/aisa-search/" + VERSION


def _query_pairs(payload: Mapping[str, Any]) -> Iterable[Tuple[str, Any]]:
    for key, value in payload.items():
        if isinstance(value, dict):
            raise ClientError(
                EXIT_INPUT, "invalid_input", "Query parameters cannot contain nested objects."
            )
        if isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    raise ClientError(
                        EXIT_INPUT,
                        "invalid_input",
                        "Query parameter arrays must contain scalar values.",
                    )
                yield key, item
        elif value is not None:
            yield key, value


def build_request(
    operation_name: str,
    payload: Mapping[str, Any],
    api_key: str,
    base_url: str,
    host: str,
) -> request.Request:
    operation = OPERATIONS[operation_name]
    validate_payload(operation_name, payload)
    url = base_url + operation.path
    body: Optional[bytes] = None
    content_type: Optional[str] = None

    if operation.encoding == "query":
        query_string = parse.urlencode(list(_query_pairs(payload)), doseq=True)
        if query_string:
            url += "?" + query_string
    elif operation.encoding == "json":
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        content_type = "application/json"
    elif operation.encoding == "scholar_form":
        body = parse.urlencode({"query": payload["query"]}).encode("utf-8")
        query_payload = {key: value for key, value in payload.items() if key != "query"}
        query_string = parse.urlencode(list(_query_pairs(query_payload)), doseq=True)
        if query_string:
            url += "?" + query_string
        content_type = "application/x-www-form-urlencoded"
    else:  # pragma: no cover
        raise ClientError(EXIT_INPUT, "invalid_operation", "Unsupported request encoding.")

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + api_key,
        "User-Agent": user_agent_for(host),
    }
    if content_type:
        headers["Content-Type"] = content_type
    return request.Request(url, data=body, headers=headers, method=operation.method)


def _read_limited(response: Any) -> bytes:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ClientError(EXIT_UPSTREAM, "response_too_large", "AIsa response exceeded 5 MiB.")
    return body


def _decode_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClientError(
            EXIT_UPSTREAM, "invalid_response", "AIsa returned a non-JSON response."
        ) from exc


def _sanitize(value: Any, api_key: str) -> Any:
    if isinstance(value, str):
        return value.replace(api_key, "[REDACTED]") if api_key else value
    if isinstance(value, list):
        return [_sanitize(item, api_key) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize(item, api_key) for key, item in value.items()}
    return value


def execute(request_value: request.Request, api_key: str, timeout: int) -> Tuple[Any, str]:
    try:
        with request.urlopen(request_value, timeout=timeout) as response:
            body = _read_limited(response)
            request_id = response.headers.get("X-Request-ID", "")
    except error.HTTPError as exc:
        body = exc.read(MAX_RESPONSE_BYTES + 1)
        details: Any = None
        if len(body) <= MAX_RESPONSE_BYTES and body:
            try:
                details = _sanitize(json.loads(body.decode("utf-8")), api_key)
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
        exit_code = EXIT_AUTH if exc.code in {401, 402, 403} else EXIT_UPSTREAM
        error_type = "authentication_or_quota" if exit_code == EXIT_AUTH else "http_error"
        raise ClientError(
            exit_code,
            error_type,
            "AIsa request failed with HTTP status " + str(exc.code) + ".",
            http_status=exc.code,
            details=details,
        ) from exc
    except (error.URLError, TimeoutError) as exc:
        raise ClientError(
            EXIT_UPSTREAM,
            "network_error",
            "Could not reach AIsa before the request timed out.",
        ) from exc
    return _sanitize(_decode_json(body), api_key), request_id


def success_envelope(operation_name: str, data: Any, request_id: str) -> Dict[str, Any]:
    return {"ok": True, "operation": operation_name, "data": data, "request_id": request_id}


def error_envelope(operation_name: str, exc: ClientError) -> Dict[str, Any]:
    error_value: Dict[str, Any] = {"type": exc.error_type, "message": exc.message}
    if exc.http_status is not None:
        error_value["http_status"] = exc.http_status
    if exc.details is not None:
        error_value["details"] = exc.details
    return {"ok": False, "operation": operation_name, "error": error_value}


def invoke(
    operation_name: str,
    payload: Mapping[str, Any],
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    host: str = "dify",
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    key = api_key.strip()
    if not key:
        raise ClientError(EXIT_INPUT, "invalid_credentials", "AIsa API key is required.")
    origin = validate_base_url(base_url)
    request_value = build_request(operation_name, payload, key, origin, host)
    data, request_id = execute(request_value, key, timeout)
    return success_envelope(operation_name, data, request_id)
