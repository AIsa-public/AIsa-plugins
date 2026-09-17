import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "aisa-search"


class ManifestTests(unittest.TestCase):
    def test_gtm_dify_identity_and_version_match(self):
        root = REPO_ROOT / "plugins" / "aisa-gtm"
        manifest = (root / "dify" / "manifest.yaml").read_text(encoding="utf-8")
        project = (root / "dify" / "pyproject.toml").read_text(encoding="utf-8")
        version = re.search(r"^version: (\S+)$", manifest, re.MULTILINE).group(1)
        name = re.search(r"^name: (\S+)$", manifest, re.MULTILINE).group(1)
        self.assertEqual(name, "go-to-market")
        self.assertIn('name = "{}"'.format(name), project)
        self.assertIn('version = "{}"'.format(version), project)
        self.assertIn("Dify-only", (root / "README.md").read_text(encoding="utf-8"))
        for catalog_path in (
            REPO_ROOT / ".agents" / "plugins" / "marketplace.json",
            REPO_ROOT / ".claude-plugin" / "marketplace.json",
        ):
            names = {plugin["name"] for plugin in self.load_json(catalog_path)["plugins"]}
            self.assertTrue(names.isdisjoint({"aisa-gtm", name}))

    def load_json(self, path):
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_plugin_names_and_versions_match(self):
        codex = self.load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
        claude = self.load_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json")
        dify_manifest = (PLUGIN_ROOT / "dify" / "manifest.yaml").read_text(encoding="utf-8")
        self.assertEqual(codex["name"], PLUGIN_ROOT.name)
        self.assertEqual(claude["name"], PLUGIN_ROOT.name)
        self.assertEqual(codex["version"].split("+", 1)[0], "0.1.2")
        self.assertEqual(claude["version"], "0.1.2")
        self.assertTrue(dify_manifest.startswith("version: 0.1.2\n"))
        self.assertIn("\nname: aisa-search\n", dify_manifest)
        self.assertEqual(codex["skills"], "./skills/")

    def test_marketplaces_point_to_the_same_plugin(self):
        codex = self.load_json(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
        claude = self.load_json(REPO_ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(codex["name"], "aisa")
        self.assertEqual(claude["name"], "aisa")
        self.assertEqual(codex["plugins"][0]["name"], "aisa-search")
        self.assertEqual(codex["plugins"][0]["source"]["path"], "./plugins/aisa-search")
        self.assertEqual(claude["plugins"][0]["source"], "./plugins/aisa-search")
        self.assertEqual(
            codex["plugins"][0]["policy"],
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        )


if __name__ == "__main__":
    unittest.main()
