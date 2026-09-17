#!/usr/bin/env bash
# Host validator: Dify tool plugin (standards/hosts/dify.md).
# Usage: dify.sh <host-dir> <plugin-name>
set -euo pipefail
dir="$1"
plugin="$2"

fail() { echo "::error file=$dir::$*"; echo "FAIL: $dir: $*"; exit 1; }

for f in manifest.yaml README.md PRIVACY.md .difyignore requirements.txt main.py; do
  [ -f "$dir/$f" ] || fail "missing $f"
done
[ -d "$dir/provider" ] || fail "missing provider/"
grep -q "Please fill in" "$dir/PRIVACY.md" && fail "PRIVACY.md is still the Dify template"
for pattern in 'tests/' '.env' '*.difypkg'; do
  grep -qxF "$pattern" "$dir/.difyignore" || fail ".difyignore must list '$pattern'"
done
echo "  ok   required files"

python3 - "$dir" <<'PY'
import re
import sys
from pathlib import Path

import yaml

d = Path(sys.argv[1])
with (d / "manifest.yaml").open(encoding="utf-8") as f:
    m = yaml.safe_load(f)
for key in ("version", "name", "type", "author", "plugins", "meta"):
    assert key in m, f"manifest.yaml: missing '{key}'"
assert m["type"] == "plugin", "manifest.yaml: type must be 'plugin'"
assert "AIsa-public/AIsa-plugins" in str(m.get("repo", "")), "manifest.yaml: repo must point here"
for provider in m["plugins"].get("tools", []):
    assert (d / provider).is_file(), f"manifest.yaml: {provider} does not exist"
    with (d / provider).open(encoding="utf-8") as f:
        prov = yaml.safe_load(f)
    for tool in prov.get("tools", []):
        assert (d / tool).is_file(), f"{provider}: tool {tool} does not exist"
        with (d / tool).open(encoding="utf-8") as f:
            td = yaml.safe_load(f)
        src = td["extra"]["python"]["source"]
        assert (d / src).is_file(), f"{tool}: source {src} does not exist"
pp = d / "pyproject.toml"
if pp.is_file():
    text = pp.read_text(encoding="utf-8")
    assert re.search(rf'^name\s*=\s*"{re.escape(m["name"])}"', text, re.M), "pyproject name differs"
    assert re.search(rf'^version\s*=\s*"{re.escape(str(m["version"]))}"', text, re.M), (
        "pyproject version differs from manifest.yaml"
    )
print("  ok   manifest.yaml, provider and tool references, pyproject.toml")
PY

if command -v dify >/dev/null 2>&1; then
  out="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/${plugin}-dify.difypkg"
  dify plugin package "$dir" -o "$out"
  echo "  ok   packaged $(du -h "$out" | cut -f1) -> $out"
elif [ -n "${CI:-}" ]; then
  fail "dify CLI is required in CI (host job installs it)"
else
  echo "  skip dify CLI not installed; packaging not verified"
fi
