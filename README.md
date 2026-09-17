# AIsa Plugins Marketplace

Public marketplace for agent plugins maintained by AIsa.

## Available plugins

### AIsa Search

Search a topic across Tavily web search, X/Twitter, YouTube, and Scholar,
then produce a structured brief with direct source links.

- Plugin: `aisa-search`
- Skill: `research-topic`
- Version: `0.1.2`
- Requirements: Python 3.9+ and an `AISA_API_KEY`

See [plugins/aisa-search](plugins/aisa-search) for configuration, usage,
and validation details.

### AIsa Go-to-Market (Dify)

Seven tools for web research, traffic intelligence, keyword/SEO/GEO research,
social listening, prospecting, creator discovery, and AI answer visibility.

- Directory: `plugins/aisa-gtm/dify`
- Dify identity: `aisa-team/go-to-market`
- Version: `0.2.0`
- Requirements: Python 3.11+ (Dify runner: Python 3.12), Dify 1.7.1+, and an AIsa API key
- Hosts: Dify only; this bundle is not registered in the Codex or Claude Code catalogs.

See [plugins/aisa-gtm](plugins/aisa-gtm) for source provenance, packaging, and tests.

## Install with Claude Code

```bash
claude plugin marketplace add AIsa-plugins/marketplace
claude plugin install aisa-search@aisa
```

Start a new Claude Code session, then try:

```text
Research the AI coding agent plugin market across web, X, YouTube, and Scholar.
Return a concise brief with source links.
```

Claude Code exposes the Skill as `/aisa-search:research-topic`.

## Install with Codex

```bash
codex plugin marketplace add AIsa-plugins/marketplace
codex plugin add aisa-search@aisa
```

Start a new Codex task after installation so bundled Skills are discovered.

## Develop for Dify

The Dify implementation is a host-specific Tool Plugin kept separate from the
shared Codex and Claude Code bundle. It provides web search, web extraction,
X/Twitter search, YouTube search, and Scholar search tools.

Package it with the Dify Plugin CLI:

```bash
dify plugin package ./plugins/aisa-search/dify
dify plugin package ./plugins/aisa-gtm/dify -o go-to-market-0.2.0.difypkg
```

See [plugins/aisa-search/dify](plugins/aisa-search/dify) for setup and local
debugging.

## Repository layout

```text
.agents/plugins/marketplace.json     Codex marketplace
.claude-plugin/marketplace.json      Claude Code marketplace
plugins/<name>/plugin.aisa.yaml      Plugin declaration CI reads (languages, hosts, tests)
plugins/aisa-search/                 Shared plugin bundle
plugins/aisa-search/dify/            Dify-specific Tool Plugin
plugins/aisa-gtm/dify/               Dify-specific Go-to-Market Tool Plugin
standards/                           Language and host profiles of the code standard
.github/scripts/                     The CI checks; run them locally with check_all.sh
```

The plugin contains no API keys. Set `AISA_API_KEY` in the environment that
launches the agent. Do not commit `.env` files or credentials.

## Contributing

Every plugin is held to the [AIsa Code Standard](CODE_STANDARD.md) — universal rules plus
per-language and per-host profiles under [`standards/`](standards) — and CI enforces it on
every pull request. [CONTRIBUTING.md](CONTRIBUTING.md) covers how work is coordinated
through issues, how to run the checks locally (`bash .github/scripts/check_all.sh`), and
how to add a plugin, a language or a host.

<!-- ownership-check probe: admin editing outside plugins/ -->
