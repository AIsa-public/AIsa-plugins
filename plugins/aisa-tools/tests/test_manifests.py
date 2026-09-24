"""Offline checks for the aisa-tools Cursor package (no network, no credentials)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
MCP_URL = "https://tools.aisa.one/mcp"
UA_RE = re.compile(
    r"^aisa-aisa-tools-cursor-plugin/"
    r"(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)"
    r" \(\+https://github\.com/AIsa-public/AIsa-plugins\)$"
)


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class AisaToolsManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        with (PLUGIN_ROOT / "plugin.aisa.yaml").open(encoding="utf-8") as handle:
            self.decl = yaml.safe_load(handle)
        self.plugin_json = load_json(PLUGIN_ROOT / ".cursor-plugin" / "plugin.json")
        self.mcp = load_json(PLUGIN_ROOT / "mcp.json")
        self.catalog = load_json(REPO_ROOT / ".cursor-plugin" / "marketplace.json")

    def test_declaration_identity(self) -> None:
        self.assertEqual(self.decl["name"], "aisa-tools")
        self.assertEqual(self.decl["name"], PLUGIN_ROOT.name)
        self.assertEqual(self.decl["hosts"], {"cursor": "."})
        self.assertEqual(self.decl["version"], "0.1.0")

    def test_cursor_plugin_json_matches_declaration(self) -> None:
        self.assertEqual(self.plugin_json["name"], self.decl["name"])
        self.assertEqual(self.plugin_json["version"], self.decl["version"])
        self.assertTrue(self.plugin_json.get("description"))
        self.assertEqual(self.plugin_json.get("mcpServers"), "./mcp.json")

    def test_mcp_points_at_tool_router_with_attribution(self) -> None:
        servers = self.mcp["mcpServers"]
        self.assertIn("aisa-tools", servers)
        server = servers["aisa-tools"]
        self.assertEqual(server.get("type"), "http")
        self.assertEqual(server.get("url"), MCP_URL)
        ua = server.get("headers", {}).get("User-Agent", "")
        match = UA_RE.match(ua)
        self.assertIsNotNone(match, f"User-Agent shape wrong: {ua!r}")
        self.assertEqual(match.group("version"), self.decl["version"])
        # No secrets in the committed MCP config.
        raw = (PLUGIN_ROOT / "mcp.json").read_text(encoding="utf-8").lower()
        for needle in ("api_key", "apikey", "secret", "password", "bearer "):
            self.assertNotIn(needle, raw)

    def test_marketplace_catalog_entry(self) -> None:
        entries = [p for p in self.catalog["plugins"] if p["name"] == "aisa-tools"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./plugins/aisa-tools")

    def test_readme_documents_local_and_marketplace(self) -> None:
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("~/.cursor/plugins/local", readme)
        self.assertIn("cursor.com/marketplace/publish", readme)
        self.assertIn(MCP_URL, readme)
        self.assertIn("aisa-aisa-tools-cursor-plugin/", readme)


if __name__ == "__main__":
    unittest.main()
