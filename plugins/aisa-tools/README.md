# AIsa Tools (Cursor)

`aisa-tools` is a Cursor plugin that connects the agent to the live AIsa Tool Router
MCP at [https://tools.aisa.one/mcp](https://tools.aisa.one/mcp) over Streamable HTTP
with OAuth. The same package is the install surface for Grok Bot.

No API keys or secrets are stored in this repository. Cursor prompts for OAuth when
the MCP server is first used.

## Requirements

- Cursor IDE with plugin / MCP support (local plugin imports enabled, or Marketplace
  access)
- An AIsa account (OAuth through the Tool Router)

## Local install

1. Copy this plugin directory into Cursor's local plugins folder:

   ```bash
   mkdir -p ~/.cursor/plugins/local
   cp -R plugins/aisa-tools ~/.cursor/plugins/local/aisa-tools
   ```

   From a clone of this repository the path above is relative to the repo root. The
   install root must be exactly `~/.cursor/plugins/local/aisa-tools` with
   `.cursor-plugin/plugin.json` directly under it (not nested one level deeper).

2. Restart Cursor, or run **Developer: Reload Window**.

3. Open **Customize** and confirm the `aisa-tools` MCP server appears. Complete the
   OAuth flow when prompted.

On Teams / Enterprise, an admin may need to enable **Allow Local Plugin Imports**
under Dashboard → Settings → Security & Identity → Marketplace and Plugins.

## Marketplace publish

1. Ensure this repository (or a public fork that contains `plugins/aisa-tools`) is
   reachable over HTTPS.
2. Submit the repository at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).
3. For a multi-plugin marketplace layout, the root catalog is
   [`.cursor-plugin/marketplace.json`](../../.cursor-plugin/marketplace.json); the
   per-plugin manifest is [`.cursor-plugin/plugin.json`](.cursor-plugin/plugin.json).

Cursor reviews marketplace submissions manually. Do not claim an official featured
listing unless Cursor grants one.

## MCP endpoint

```json
{
  "mcpServers": {
    "aisa-tools": {
      "type": "http",
      "url": "https://tools.aisa.one/mcp"
    }
  }
}
```

The committed [`mcp.json`](mcp.json) also sets a `User-Agent` attribution token
(CODE_STANDARD §5a). There are no secrets in that file.

## Attribution

Every MCP request identifies this plugin to AIsa without identifying the end user:

```text
aisa-aisa-tools-cursor-plugin/<version> (+https://github.com/AIsa-public/AIsa-plugins)
```

`<version>` must match `.cursor-plugin/plugin.json` / `plugin.aisa.yaml`. Offline tests
assert the exact token.

## Offline tests

From the repository root (or from this directory with the paths adjusted):

```bash
python3 -m unittest discover -s plugins/aisa-tools/tests -v
```

Or via the plugin declaration:

```bash
cd plugins/aisa-tools && python3 -m unittest discover -s tests -v
```

No network and no credentials are required.

## Validate the host package

From the repository root:

```bash
bash .github/scripts/hosts/cursor.sh plugins/aisa-tools aisa-tools
bash .github/scripts/check_all.sh
```
