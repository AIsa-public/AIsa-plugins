# Host profile: Dify

Applies to every plugin with a `dify` entry under `hosts`. The host directory is a Dify
**Tool Plugin** packaged with the Dify Plugin CLI.

## Required files (host directory)

| File | Rule |
|---|---|
| `manifest.yaml` | `type: plugin`; `name`, `version`, `author`, `plugins.tools`, `meta` present; `repo` points at this repository |
| `provider/<id>.yaml` + `.py` | every tool listed exists; every tool's `extra.python.source` exists |
| `tools/<tool>.yaml` + `.py` | one pair per tool |
| `PRIVACY.md` | real content — the Dify template text fails validation |
| `README.md` | English primary; `README.zh_Hans.md` (or `readme/README_zh_Hans.md`) for Chinese |
| `.difyignore` | excludes `tests/`, `.env*`, `.github/`, `*.difypkg` |
| `requirements.txt` | `dify_plugin` pinned to a range |
| `pyproject.toml` (if present) | `name` and `version` equal `manifest.yaml` |
| `_assets/` | icon(s) referenced by `manifest.yaml` |

## Identity and versioning

- The Dify identity (`author/name` in `manifest.yaml`) may differ from the AIsa plugin name
  (`aisa-gtm` is published as `aisa-team/go-to-market`); the README says which.
- `manifest.yaml` and `pyproject.toml` are `version_sources` in `plugin.aisa.yaml`.
- A new version is packaged and submitted to `langgenius/dify-plugins` only after the
  previous one is live; the open marketplace PR is updated in place until then.

## Localization

`label` / `description` fields carry `en_US` plus any of `zh_Hans`, `ja_JP`, `pt_BR`.
Those are the only places non-English text is allowed inside the host directory.

## Validation (`.github/scripts/hosts/dify.sh`)

1. required files present, `PRIVACY.md` is not the template
2. `manifest.yaml` parses, references resolve, `pyproject.toml` agrees
3. `dify plugin package <dir>` succeeds (the `.difypkg` is a CI artifact, never committed)

Run it locally with the CLI installed: `bash .github/scripts/hosts/dify.sh plugins/<name>/dify <name>`.
