import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock
from urllib import error

DIFY_ROOT = Path(__file__).resolve().parents[1] / "dify"
sys.path.insert(0, str(DIFY_ROOT))

from aisa_client import (  # noqa: E402
    DEFAULT_BASE_URL,
    ClientError,
    build_request,
    execute,
    parse_extract_urls,
)


class FakeResponse:
    def __init__(self, body: bytes, request_id: str = "request-1") -> None:
        self._body = BytesIO(body)
        self.headers = {"X-Request-ID": request_id}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)


class ClientTests(unittest.TestCase):
    def test_builds_search_request_without_key_in_url(self) -> None:
        request_value = build_request(
            "tavily_search",
            {"query": "dify plugins"},
            "fake-key",
            DEFAULT_BASE_URL,
            "dify",
        )
        self.assertEqual(request_value.full_url, "https://api.aisa.one/apis/v1/tavily/search")
        self.assertEqual(request_value.get_header("Authorization"), "Bearer fake-key")
        self.assertEqual(request_value.get_header("User-agent"), "dify/aisa-search/0.1.2")
        self.assertEqual(json.loads(request_value.data), {"query": "dify plugins"})

    def test_parses_one_to_three_public_urls(self) -> None:
        self.assertEqual(
            parse_extract_urls("https://example.com/a\nhttps://example.org/b"),
            ["https://example.com/a", "https://example.org/b"],
        )

    def test_rejects_unsafe_or_excessive_extract_urls(self) -> None:
        invalid_values = (
            "http://127.0.0.1/private",
            "http://user:password@example.com/private",
            "ftp://example.com/file",
            "\n".join(["https://example.com"] * 4),
        )
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ClientError):
                parse_extract_urls(value)

    def test_execute_sanitizes_api_key(self) -> None:
        response = FakeResponse(b'{"message":"token fake-key was accepted"}')
        request_value = build_request(
            "tavily_search", {"query": "q"}, "fake-key", DEFAULT_BASE_URL, "dify"
        )
        with mock.patch("aisa_client.request.urlopen", return_value=response):
            data, request_id = execute(request_value, "fake-key", 30)
        self.assertEqual(data["message"], "token [REDACTED] was accepted")
        self.assertEqual(request_id, "request-1")

    def test_http_error_does_not_leak_key(self) -> None:
        http_error = error.HTTPError(
            "https://api.aisa.one/test",
            401,
            "Unauthorized",
            {},
            BytesIO(b'{"message":"bad fake-key"}'),
        )
        request_value = build_request(
            "tavily_search", {"query": "q"}, "fake-key", DEFAULT_BASE_URL, "dify"
        )
        with (
            mock.patch("aisa_client.request.urlopen", side_effect=http_error),
            self.assertRaises(ClientError) as context,
        ):
            execute(request_value, "fake-key", 30)
        self.assertNotIn("fake-key", str(context.exception.details))


if __name__ == "__main__":
    unittest.main()
