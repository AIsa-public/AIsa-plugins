# Host profile: Claude Code

Applies to every plugin with a `claude-code` entry under `hosts`. The host directory is a
Claude Code plugin bundle; it is normally the plugin root and is shared with Codex.

## Required files (host directory)

| File | Rule |
|---|---|
| `.claude-plugin/plugin.json` | valid against `https://json.schemastore.org/claude-code-plugin-manifest.json`; `name` equals the AIsa plugin name; `version` is a `version_source` |
| `skills/<skill>/SKILL.md` | YAML frontmatter with `name` (equal to the directory) and `description`; the body is the skill |
| `scripts/` | helper scripts the skill calls; read-only towards the AIsa API unless documented otherwise |
| `README.md` | install instructions using `claude plugin marketplace add` / `claude plugin install` |

## Attribution

Host token: `claude-code` → `User-Agent: aisa-<plugin>-claude-code-plugin/<version> (+…)` (CODE_STANDARD.md §5a).

## Catalog

The plugin is listed in `/.claude-plugin/marketplace.json` with `source: ./plugins/<name>`
and a `category`. The catalog itself validates against
`https://json.schemastore.org/claude-code-marketplace.json`.

## Validation (`.github/scripts/hosts/claude-code.sh`)

1. `plugin.json` present, schema-valid, name matches
2. catalog entry present and pointing at the plugin directory
3. every skill has a well-formed `SKILL.md`
