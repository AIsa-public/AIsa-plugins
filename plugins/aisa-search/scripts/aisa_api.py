#!/usr/bin/env python3
"""CLI adapter for the shared, read-only AIsa Search client."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, TextIO

DIFY_ROOT = Path(__file__).resolve().parents[1] / "dify"
sys.path.insert(0, str(DIFY_ROOT))

from aisa_client import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    EXIT_INPUT,
    OPERATIONS,
    ClientError,
    build_request,
    error_envelope,
    execute,
    success_envelope,
    validate_base_url,
)

# Explicit re-exports (``name as name``) for tests/test_aisa_api.py, which patches
# ``aisa_api.request.urlopen`` and calls ``aisa_api.validate_payload`` via this module.
from aisa_client import request as request
from aisa_client import validate_payload as validate_payload

MAX_INPUT_BYTES = 64 * 1024


def read_payload(stream: TextIO) -> dict[str, Any]:
    raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ClientError(EXIT_INPUT, "invalid_input", "Input exceeds 64 KiB.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ClientError(
            EXIT_INPUT, "invalid_json", "stdin must contain one valid JSON object."
        ) from exc
    if not isinstance(payload, dict):
        raise ClientError(EXIT_INPUT, "invalid_input", "Input JSON must be an object.")
    return payload


def detect_agent_host(environ: Mapping[str, str]) -> str:
    override = environ.get("AISA_AGENT_HOST", "").strip().lower()
    if override:
        if override not in {"codex", "claude_code"}:
            raise ClientError(
                EXIT_INPUT,
                "invalid_config",
                "AISA_AGENT_HOST must be 'codex' or 'claude_code'.",
            )
        return override
    if environ.get("PLUGIN_ROOT"):
        return "codex"
    if environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude_code"
    return "codex"


def write_json(stream: TextIO, value: Mapping[str, Any]) -> None:
    json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
    stream.write("\n")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Call one fixed, read-only AIsa Search operation using JSON from stdin."
    )
    parser.add_argument("operation", choices=sorted(OPERATIONS))
    args = parser.parse_args(list(argv) if argv is not None else None)
    operation_name = args.operation

    try:
        api_key = os.environ.get("AISA_API_KEY", "").strip()
        if not api_key:
            raise ClientError(EXIT_INPUT, "invalid_config", "AISA_API_KEY is required.")
        base_url = validate_base_url(os.environ.get("AISA_BASE_URL", DEFAULT_BASE_URL))
        host = detect_agent_host(os.environ)
        payload = read_payload(sys.stdin)
        request_value = build_request(operation_name, payload, api_key, base_url, host)
        data, request_id = execute(request_value, api_key, DEFAULT_TIMEOUT_SECONDS)
        write_json(sys.stdout, success_envelope(operation_name, data, request_id))
        return 0
    except ClientError as exc:
        write_json(sys.stdout, error_envelope(operation_name, exc))
        print(exc.message, file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
