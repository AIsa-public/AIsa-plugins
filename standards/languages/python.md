# Language profile: Python

Applies to every plugin that lists `python` in `languages`.

## Toolchain

- **Version floor: 3.11.** CI runs the suite on 3.12 (the version the Dify runner ships).
  Syntax and stdlib usage must stay within 3.11.
- **Formatter and linter: [ruff](https://docs.astral.sh/ruff/)**, configured once at the
  repository root in `ruff.toml`. Line length 100, target `py311`, rule set
  `E F I UP B SIM`. No per-plugin overrides.
- Lint recipe: `.github/scripts/lint/python.sh` (`ruff check` + `ruff format --check` on the
  whole repository).

## Dependencies

- Standard library first. The only expected runtime dependency is the host SDK
  (`dify-plugin` for Dify). Anything else needs a one-line justification in the PR and a pin
  in the plugin's `requirements.txt` / `pyproject.toml`.
- Test suites are dependency-free (`unittest` or plain `python3 tests/...`) except for
  `pyyaml` where manifests must be parsed. No `pytest` plugins.

## Idioms

- Type hints on every public function; use `X | None` and `list[str]` (PEP 604/585), not
  `Optional` / `List`.
- Module and public-function docstrings; module docstrings state the module's contract
  (what it guarantees to callers), not its history.
- Files are opened with a context manager; `contextlib.suppress` replaces
  `try/except: pass`.
- `zip(..., strict=...)` is always explicit.
- Network code uses `urllib` from the stdlib and enforces a response-size cap and a timeout.
  Error handling follows the universal rule: inspect the body, not just the status.
- Never `print()` credentials, request headers or raw bodies. Redact before logging.

## Layout of a Python host implementation

```
<host-dir>/
  main.py           host entry point
  <client>.py       the AIsa API client for this plugin (self-contained)
  tools/            one module per tool
  tests/            offline suite — no network, no key
  requirements.txt  pinned
```
