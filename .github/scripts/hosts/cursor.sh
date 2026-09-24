#!/usr/bin/env bash
# Host validator: Cursor plugin bundle (standards/hosts/cursor.md).
# Usage: cursor.sh <host-dir> <plugin-name>
set -euo pipefail
dir="$1"
plugin="$2"
root="$(git rev-parse --show-toplevel)"
cd "$root"

fail() { echo "::error file=$dir::$*"; echo "FAIL: $dir: $*"; exit 1; }

manifest="$dir/.cursor-plugin/plugin.json"
catalog=".cursor-plugin/marketplace.json"
[ -f "$manifest" ] || fail "missing .cursor-plugin/plugin.json"
[ -f "$catalog" ] || fail "missing $catalog"

python3 - "$dir" "$plugin" "$manifest" "$catalog" <<'PY'
import json
import re
import sys
from pathlib import Path

d, plugin, manifest, catalog = sys.argv[1:5]
with open(manifest, encoding="utf-8") as f:
    pj = json.load(f)
for key in ("name", "version", "description"):
    assert pj.get(key), f"plugin.json: missing '{key}'"
assert pj["name"] == plugin, f"plugin.json: name {pj['name']!r} != {plugin!r}"
assert re.match(r"^\d+\.\d+\.\d+", str(pj["version"])), f"plugin.json: version not semver-like"

mcp_path = Path(d) / "mcp.json"
if mcp_path.is_file():
    with mcp_path.open(encoding="utf-8") as f:
        mcp = json.load(f)
    servers = mcp.get("mcpServers")
    assert isinstance(servers, dict) and servers, "mcp.json: mcpServers must be a non-empty object"
    secretish = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]")
    raw = mcp_path.read_text(encoding="utf-8")
    assert not secretish.search(raw), "mcp.json: looks like it embeds a secret — use OAuth or variables"
    for name, cfg in servers.items():
        assert isinstance(cfg, dict), f"mcp.json: server {name!r} must be an object"
        assert cfg.get("url") or cfg.get("command"), (
            f"mcp.json: server {name!r} needs 'url' (HTTP) or 'command' (stdio)"
        )
    print("  ok   mcp.json")
else:
    print("  skip no mcp.json")

with open(catalog, encoding="utf-8") as f:
    cat = json.load(f)
entries = [p for p in cat["plugins"] if p["name"] == plugin]
assert len(entries) == 1, f"{catalog}: expected exactly one entry for {plugin}"
source = entries[0].get("source")
expected = f"./{d}"
assert source == expected or source == d, (
    f"{catalog}: source must be {expected!r} (or {d!r}), got {source!r}"
)
print("  ok   plugin.json, catalog entry")
PY
