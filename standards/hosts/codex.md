# Host profile: Codex

Applies to every plugin with a `codex` entry under `hosts`. The host directory is the same
bundle Claude Code uses, plus a Codex manifest.

## Required files (host directory)

| File | Rule |
|---|---|
| `.codex-plugin/plugin.json` | `name` equals the AIsa plugin name; `version` is `<plugin version>+codex.<build>`; `skills` points at an existing directory; `interface.privacyPolicyURL` and `interface.termsOfServiceURL` present |
| `skills/` | shared with the Claude Code profile |

## Catalog

The plugin is listed in `/.agents/plugins/marketplace.json` with
`source.path: ./plugins/<name>`, an installation policy and a `category`.

## Validation (`.github/scripts/hosts/codex.sh`)

1. `plugin.json` present, required fields, name matches, version base matches
2. catalog entry present and pointing at the plugin directory
