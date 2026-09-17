#!/usr/bin/env bash
# Host validator: Codex plugin bundle (standards/hosts/codex.md).
# Usage: codex.sh <host-dir> <plugin-name>
set -euo pipefail
dir="$1"
plugin="$2"
cd "$(git rev-parse --show-toplevel)"

fail() { echo "::error file=$dir::$*"; echo "FAIL: $dir: $*"; exit 1; }

manifest="$dir/.codex-plugin/plugin.json"
catalog=".agents/plugins/marketplace.json"
[ -f "$manifest" ] || fail "missing .codex-plugin/plugin.json"
[ -f "$catalog" ] || fail "missing $catalog"

python3 - "$dir" "$plugin" "$manifest" "$catalog" <<'PY'
import json
import sys
from pathlib import Path

d, plugin, manifest, catalog = sys.argv[1:5]
with open(manifest, encoding="utf-8") as f:
    pj = json.load(f)
for key in ("name", "version", "description", "skills", "interface"):
    assert pj.get(key), f"plugin.json: missing '{key}'"
assert pj["name"] == plugin, f"plugin.json: name {pj['name']!r} != {plugin!r}"
assert (Path(d) / pj["skills"]).is_dir(), f"plugin.json: skills path {pj['skills']} missing"
for key in ("displayName", "privacyPolicyURL", "termsOfServiceURL"):
    assert pj["interface"].get(key), f"plugin.json: interface.{key} missing"

with open(catalog, encoding="utf-8") as f:
    entries = [p for p in json.load(f)["plugins"] if p["name"] == plugin]
assert len(entries) == 1, f"{catalog}: expected exactly one entry for {plugin}"
assert entries[0]["source"].get("path") == f"./{d}", f"{catalog}: source.path must be ./{d}"
assert entries[0].get("policy"), f"{catalog}: installation policy missing"
print("  ok   plugin.json, catalog entry")
PY
