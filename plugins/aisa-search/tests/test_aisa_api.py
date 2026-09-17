import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib import error

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PLUGIN_ROOT / "scripts" / "aisa_api.py"
SPEC = importlib.util.spec_from_file_location("aisa_api", SCRIPT_PATH)
aisa_api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = aisa_api
SPEC.loader.exec_module(aisa_api)


class MockResponse:
    def __init__(self, body=b'{"items":[]}', request_id="req-test"):
        self.body = body
        self.headers = {"X-Request-ID": request_id}

    def read(self, _size=-1):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class AisaAPIClientTests(unittest.TestCase):
    def test_operation_registry_is_read_only_and_fixed(self):
        expected = {
            "tavily_search": ("POST", "/apis/v1/tavily/search"),
            "tavily_extract": ("POST", "/apis/v1/tavily/extract"),
            "twitter_advanced_search": (
                "GET",
                "/apis/v1/twitter/tweet/advanced_search",
            ),
            "youtube_search": ("GET", "/apis/v1/youtube/search"),
            "scholar_search_web": ("POST", "/apis/v1/scholar/search/web"),
        }
        self.assertEqual(
            {name: (op.method, op.path) for name, op in aisa_api.OPERATIONS.items()},
            expected,
        )
        self.assertNotIn("DELETE", {op.method for op in aisa_api.OPERATIONS.values()})
        self.assertNotIn("PATCH", {op.method for op in aisa_api.OPERATIONS.values()})

    def test_codex_json_request_has_auth_user_agent_and_body(self):
        req = aisa_api.build_request(
            "tavily_search",
            {"query": "AI agents", "max_results": 5},
            "secret-key",
            "https://api.aisa.one",
            "codex",
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, "https://api.aisa.one/apis/v1/tavily/search")
        self.assertEqual(req.get_header("Authorization"), "Bearer secret-key")
        self.assertEqual(req.get_header("User-agent"), "openai-codex/aisa-search/0.1.2")
        self.assertEqual(json.loads(req.data), {"query": "AI agents", "max_results": 5})

    def test_claude_get_request_encodes_query(self):
        req = aisa_api.build_request(
            "twitter_advanced_search",
            {"query": "agent lang:en", "queryType": "Latest"},
            "secret-key",
            "https://api.aisa.one",
            "claude_code",
        )
        self.assertEqual(req.get_method(), "GET")
        self.assertIn("query=agent+lang%3Aen", req.full_url)
        self.assertIn("queryType=Latest", req.full_url)
        self.assertEqual(req.get_header("User-agent"), "claude-code/aisa-search/0.1.2")

    def test_scholar_uses_form_query_and_url_options(self):
        req = aisa_api.build_request(
            "scholar_search_web",
            {"query": "agent systems", "max_num_results": 5},
            "secret-key",
            "https://api.aisa.one",
            "codex",
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.endswith("?max_num_results=5"))
        self.assertEqual(req.data, b"query=agent+systems")
        self.assertEqual(req.get_header("Content-type"), "application/x-www-form-urlencoded")

    def test_execute_wraps_json_request_id_and_redacts_key(self):
        response = MockResponse(b'{"items":[],"echo":"secret-key"}')
        with mock.patch.object(aisa_api.request, "urlopen", return_value=response):
            data, request_id = aisa_api.execute(mock.Mock(), "secret-key", 30)
        self.assertEqual(data, {"items": [], "echo": "[REDACTED]"})
        self.assertEqual(request_id, "req-test")

    def test_auth_error_maps_to_exit_three_and_redacts_key(self):
        http_error = error.HTTPError(
            "https://api.aisa.one/test",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"message":"bad secret-key"}'),
        )
        with (
            mock.patch.object(aisa_api.request, "urlopen", side_effect=http_error),
            self.assertRaises(aisa_api.ClientError) as raised,
        ):
            aisa_api.execute(mock.Mock(), "secret-key", 30)
        self.assertEqual(raised.exception.exit_code, 3)
        serialized = json.dumps(raised.exception.details)
        self.assertNotIn("secret-key", serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_all_auth_and_quota_statuses_map_to_exit_three(self):
        for status in (401, 402, 403):
            with self.subTest(status=status):
                http_error = error.HTTPError(
                    "https://api.aisa.one/test",
                    status,
                    "failed",
                    {},
                    io.BytesIO(b"{}"),
                )
                with (
                    mock.patch.object(aisa_api.request, "urlopen", side_effect=http_error),
                    self.assertRaises(aisa_api.ClientError) as raised,
                ):
                    aisa_api.execute(mock.Mock(), "secret-key", 30)
                self.assertEqual(raised.exception.exit_code, 3)

    def test_rate_limit_and_server_errors_map_to_exit_four(self):
        for status in (429, 500):
            with self.subTest(status=status):
                http_error = error.HTTPError(
                    "https://api.aisa.one/test",
                    status,
                    "failed",
                    {},
                    io.BytesIO(b"{}"),
                )
                with (
                    mock.patch.object(aisa_api.request, "urlopen", side_effect=http_error),
                    self.assertRaises(aisa_api.ClientError) as raised,
                ):
                    aisa_api.execute(mock.Mock(), "secret-key", 30)
                self.assertEqual(raised.exception.exit_code, 4)

    def test_network_failure_maps_to_exit_four(self):
        failure = error.URLError(TimeoutError("timed out"))
        with (
            mock.patch.object(aisa_api.request, "urlopen", side_effect=failure),
            self.assertRaises(aisa_api.ClientError) as raised,
        ):
            aisa_api.execute(mock.Mock(), "secret-key", 30)
        self.assertEqual(raised.exception.exit_code, 4)
        self.assertEqual(raised.exception.error_type, "network_error")

    def test_extract_rejects_private_urls_and_more_than_three_urls(self):
        for urls in (["http://127.0.0.1/private"], ["https://example.com"] * 4):
            with self.subTest(urls=urls), self.assertRaises(aisa_api.ClientError):
                aisa_api.validate_payload("tavily_extract", {"urls": urls})

    def test_cli_rejects_invalid_json_without_leaking_key(self):
        env = os.environ.copy()
        env["AISA_API_KEY"] = "cli-secret-key"
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "tavily_search"],
            input="not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["ok"])
        self.assertNotIn("cli-secret-key", result.stdout + result.stderr)

    def test_cli_requires_api_key(self):
        env = os.environ.copy()
        env.pop("AISA_API_KEY", None)
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "youtube_search"],
            input='{"q":"AI agents"}',
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["error"]["type"], "invalid_config")


if __name__ == "__main__":
    unittest.main()
