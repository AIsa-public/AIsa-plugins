"""Offline checks for the aisa Cursor package (no network, no credentials)."""

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
    r"^aisa-aisa-cursor-plugin/"
    r"(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)"
    r" \(\+https://github\.com/AIsa-public/AIsa-plugins\)$"
)


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class AisaManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        with (PLUGIN_ROOT / "plugin.aisa.yaml").open(encoding="utf-8") as handle:
            self.decl = yaml.safe_load(handle)
        self.plugin_json = load_json(PLUGIN_ROOT / ".cursor-plugin" / "plugin.json")
        self.mcp = load_json(PLUGIN_ROOT / "mcp.json")
        self.catalog = load_json(REPO_ROOT / ".cursor-plugin" / "marketplace.json")

    def test_declaration_identity(self) -> None:
        self.assertEqual(self.decl["name"], "aisa")
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
        self.assertIn("aisa", servers)
        server = servers["aisa"]
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
        entries = [p for p in self.catalog["plugins"] if p["name"] == "aisa"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "./plugins/aisa")

    def test_aisa_skill_frontmatter_and_workflow(self) -> None:
        skill_dir = PLUGIN_ROOT / "skills" / "aisa"
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md needs YAML frontmatter")
        front = yaml.safe_load(match.group(1))
        self.assertEqual(front["name"], "aisa")
        self.assertEqual(front["name"], skill_dir.name)
        self.assertTrue(front.get("description"))
        for tool in (
            "AISA_SEARCH_TOOL",
            "AISA_BATCH_GET_SCHEMA",
            "AISA_BATCH_QUOTE",
            "AISA_BATCH_USE",
        ):
            self.assertIn(tool, text)
        self.assertIn(MCP_URL, text)
        self.assertIn("AIsa-team/agent-skills", text)
        # The plugin already registers the MCP server; the skill must not push CLI installs.
        self.assertNotIn("npm install", text)
        self.assertNotIn("npx", text)
        # MCP-only: no CLI fallback, no unrelated host/provider triggers.
        for needle in ("aisa connect", "aisa search", "@aisa-one/cli", "OpenClaw", "aisa-provider"):
            self.assertNotIn(needle, text)
        self.assertIn("Cursor Settings", text)
        self.assertIn("MIT License", (skill_dir / "LICENSE").read_text(encoding="utf-8"))

    def test_readme_documents_local_and_marketplace(self) -> None:
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("~/.cursor/plugins/local", readme)
        self.assertIn("cursor.com/marketplace/publish", readme)
        self.assertIn(MCP_URL, readme)
        self.assertIn("aisa-aisa-cursor-plugin/", readme)


if __name__ == "__main__":
    unittest.main()
