# Host profile: Cursor

Applies to every plugin with a `cursor` entry under `hosts`. The host directory is a
Cursor Plugin bundle (`.cursor-plugin/plugin.json` plus optional MCP, skills, rules,
agents, commands, and hooks).

## Required files (host directory)

| File | Rule |
|---|---|
| `.cursor-plugin/plugin.json` | `name` equals the AIsa plugin name; `version` is a `version_source`; `description` present |
| `mcp.json` | when the plugin ships MCP servers: top-level `mcpServers` mapping; each server has a `url` (HTTP / Streamable HTTP) or `command` (stdio); no secrets |
| `README.md` | install instructions for local (`~/.cursor/plugins/local`) and Marketplace submit notes |

Optional Cursor components (`skills/`, `rules/`, `agents/`, `commands/`, `hooks/`) follow
the [Cursor plugins reference](https://cursor.com/docs/reference/plugins).

## Attribution

Host token: `cursor` → `User-Agent: aisa-<plugin>-cursor-plugin/<version> (+…)`
(CODE_STANDARD.md §5a). When the plugin reaches AIsa only through an HTTP MCP URL, put the
token on the MCP request (`headers.User-Agent` in `mcp.json`) and keep that version in sync
via `version_sources`.

## Catalog

The plugin is listed in `/.cursor-plugin/marketplace.json` with
`source: ./plugins/<name>` (or a path that resolves to the host directory) and a `category`.

## Validation (`.github/scripts/hosts/cursor.sh`)

1. `plugin.json` present, required fields, name matches, version base matches the declaration
2. if `mcp.json` exists: parses, `mcpServers` non-empty, every entry has `url` or `command`, no obvious secrets
3. catalog entry present and pointing at the plugin / host directory

Cursor has no packaging CLI; the validator is file- and schema-level only.
