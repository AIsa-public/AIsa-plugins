#!/usr/bin/env bash
# Run every check CI runs, in the same order, from a local checkout.
#   bash .github/scripts/check_all.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
scripts=.github/scripts
status=0
section() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
run() { if "$@"; then :; else status=1; echo "FAILED: $*"; fi; }

section "discover"
python3 "$scripts/discover.py"
matrix="$(python3 "$scripts/discover.py" --tsv)"

section "universal standard"
run python3 "$scripts/check_universal.py"

while IFS=$'\t' read -r kind a b c d; do
  case "$kind" in
    LANG)
      section "lint ($a)"
      run bash "$scripts/lint/$a.sh"
      ;;
    TEST)
      section "test ($a, $b) — $d"
      run bash -c "cd '$c' && $d"
      ;;
    HOST)
      section "host ($a, $b)"
      run bash "$scripts/hosts/$b.sh" "$c" "$a"
      ;;
  esac
done <<< "$matrix"

find plugins -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
section "result"
if [ "$status" -eq 0 ]; then echo "all checks passed"; else echo "some checks FAILED"; fi
exit "$status"
