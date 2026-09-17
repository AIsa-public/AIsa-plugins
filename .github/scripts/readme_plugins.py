#!/usr/bin/env python3
"""Keep the plugin table in README.md in sync with the plugin declarations.

    readme_plugins.py --write   # regenerate the block between the markers
    readme_plugins.py --check   # exit 1 if README.md is out of date (CI)

The table is rendered from every plugins/*/plugin.aisa.yaml, so version, description, hosts
and owners in the README are always the declared ones.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import discover

README = discover.REPO / "README.md"
START = "<!-- plugins:start -->"
END = "<!-- plugins:end -->"
HOST_LABELS = {"claude-code": "Claude Code", "codex": "Codex", "dify": "Dify"}


def render() -> str:
    rows = ["| Plugin | Version | Hosts | Description | Owners |", "|---|---|---|---|---|"]
    for decl in discover.load_all():
        hosts = ", ".join(HOST_LABELS.get(h, h) for h in decl["hosts"])
        owners = ", ".join(f"@{o}" for o in decl["owners"])
        rows.append(
            f"| [`{decl['name']}`]({decl['_dir']}) | `{decl['version']}` | {hosts} "
            f"| {decl['description']} | {owners} |"
        )
    return "\n".join(rows)


def splice(text: str, block: str) -> str:
    start = text.index(START) + len(START)
    end = text.index(END)
    return text[:start] + "\n" + block + "\n" + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    current = README.read_text(encoding="utf-8")
    if START not in current or END not in current:
        print(f"::error file=README.md::missing {START} / {END} markers")
        return 1
    updated = splice(current, render())
    if args.write:
        README.write_text(updated, encoding="utf-8")
        print("README.md plugin table regenerated")
        return 0
    if updated != current:
        print(
            "::error file=README.md::plugin table is out of date — run "
            "`python3 .github/scripts/readme_plugins.py --write`"
        )
        return 1
    print("  ok   README.md plugin table matches the plugin declarations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
