#!/usr/bin/env python3
"""Discover plugins from their ``plugin.aisa.yaml`` and emit the CI matrices.

Usage:
    discover.py                 # pretty JSON on stdout
    discover.py --github-output # append languages=/tests=/hosts=/plugins= to $GITHUB_OUTPUT
    discover.py --tsv           # one line per matrix entry, for shell consumers

The declaration schema is documented in CODE_STANDARD.md §9. This module only reads and
normalizes; ``check_universal.py`` is where the rules are enforced.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]
PLUGINS_DIR = REPO / "plugins"
DECLARATION = "plugin.aisa.yaml"


class DeclarationError(Exception):
    """A plugin declaration is missing or malformed."""


def plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def load_declaration(plugin_dir: Path) -> dict[str, Any]:
    path = plugin_dir / DECLARATION
    rel = path.relative_to(REPO).as_posix()
    if not path.is_file():
        raise DeclarationError(f"{rel}: missing (every directory under plugins/ needs one)")
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise DeclarationError(f"{rel}: top level must be a mapping")
    data["_path"] = rel
    data["_dir"] = plugin_dir.relative_to(REPO).as_posix()
    return data


def load_all() -> list[dict[str, Any]]:
    return [load_declaration(d) for d in plugin_dirs()]


def matrices(declarations: list[dict[str, Any]]) -> dict[str, Any]:
    plugins: list[dict[str, str]] = []
    languages: set[str] = set()
    tests: list[dict[str, str]] = []
    hosts: list[dict[str, str]] = []
    for decl in declarations:
        base = decl["_dir"]
        plugins.append({"name": decl["name"], "path": base})
        languages.update(decl.get("languages") or [])
        for test in decl.get("tests") or []:
            cwd = os.path.normpath(os.path.join(base, test.get("cwd", ".")))
            tests.append(
                {
                    "plugin": decl["name"],
                    "language": test["language"],
                    "run": test["run"],
                    "cwd": cwd,
                }
            )
        for host, sub in (decl.get("hosts") or {}).items():
            hosts.append(
                {
                    "plugin": decl["name"],
                    "host": host,
                    "path": os.path.normpath(os.path.join(base, sub or ".")),
                }
            )
    return {
        "plugins": plugins,
        "languages": sorted(languages),
        "tests": tests,
        "hosts": hosts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--github-output", action="store_true")
    output.add_argument("--tsv", action="store_true")
    args = parser.parse_args()

    try:
        result = matrices(load_all())
    except DeclarationError as exc:
        print(f"::error::{exc}")
        print(f"discover: {exc}", file=sys.stderr)
        return 1

    if args.github_output:
        target = os.environ.get("GITHUB_OUTPUT")
        if not target:
            print("discover: GITHUB_OUTPUT is not set", file=sys.stderr)
            return 1
        with open(target, "a", encoding="utf-8") as handle:
            for key, value in result.items():
                handle.write(f"{key}={json.dumps(value, separators=(',', ':'))}\n")
    elif args.tsv:
        for language in result["languages"]:
            print(f"LANG\t{language}")
        for test in result["tests"]:
            print(f"TEST\t{test['plugin']}\t{test['language']}\t{test['cwd']}\t{test['run']}")
        for host in result["hosts"]:
            print(f"HOST\t{host['plugin']}\t{host['host']}\t{host['path']}")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
