#!/usr/bin/env bash
# Host validator: Claude Code plugin bundle (standards/hosts/claude-code.md).
# Usage: claude-code.sh <host-dir> <plugin-name>
set -euo pipefail
dir="$1"
plugin="$2"
root="$(git rev-parse --show-toplevel)"
cd "$root"

fail() { echo "::error file=$dir::$*"; echo "FAIL: $dir: $*"; exit 1; }

manifest="$dir/.claude-plugin/plugin.json"
catalog=".claude-plugin/marketplace.json"
[ -f "$manifest" ] || fail "missing .claude-plugin/plugin.json"
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

with open(catalog, encoding="utf-8") as f:
    entries = [p for p in json.load(f)["plugins"] if p["name"] == plugin]
assert len(entries) == 1, f"{catalog}: expected exactly one entry for {plugin}"
assert entries[0]["source"] == f"./{d}", f"{catalog}: source must be ./{d}"

skills = Path(d) / "skills"
if skills.is_dir():
    for skill in sorted(p for p in skills.iterdir() if p.is_dir()):
        md = skill / "SKILL.md"
        assert md.is_file(), f"{skill}: missing SKILL.md"
        text = md.read_text(encoding="utf-8")
        head = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        assert head, f"{md}: missing YAML frontmatter"
        name = re.search(r"^name:\s*(\S+)", head.group(1), re.M)
        assert name and name.group(1) == skill.name, f"{md}: frontmatter name must be {skill.name}"
        assert re.search(r"^description:\s*\S", head.group(1), re.M), f"{md}: missing description"
print("  ok   plugin.json, catalog entry, skills")
PY

if command -v check-jsonschema >/dev/null 2>&1; then
  check-jsonschema --schemafile https://json.schemastore.org/claude-code-plugin-manifest.json "$manifest"
  check-jsonschema --schemafile https://json.schemastore.org/claude-code-marketplace.json "$catalog"
  echo "  ok   schemastore validation"
elif [ -n "${CI:-}" ]; then
  fail "check-jsonschema is required in CI"
else
  echo "  skip check-jsonschema not installed; schema validation not verified"
fi
