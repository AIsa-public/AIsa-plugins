#!/usr/bin/env bash
# Lint recipe for the Python language profile (standards/languages/python.md).
# Runs against the whole repository so CI scripts are held to the same bar as plugins.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
echo "ruff $(ruff --version)"
ruff check .
ruff format --check .
