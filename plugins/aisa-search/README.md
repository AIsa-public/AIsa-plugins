# AIsa Search

`aisa-search` is a minimal Codex and Claude Code plugin for searching one topic
across Tavily web search, X/Twitter, YouTube, and Scholar. It uses one
shared Skill and a dependency-free Python client with a fixed read-only API
allowlist.

## Requirements

- Python 3.9 or newer
- An AIsa API key from <https://console.aisa.one>

Export the key in the shell that launches your agent:

```bash
export AISA_API_KEY="your-key"
```

`AISA_BASE_URL` is optional and defaults to `https://api.aisa.one`.

## Codex install

```bash
codex plugin marketplace add AIsa-plugins/marketplace
codex plugin add aisa-search@aisa
```

Start a new Codex task after installing so the new Skill is discovered.

## Claude Code install

With Claude Code installed:

```bash
claude plugin marketplace add AIsa-plugins/marketplace
claude plugin install aisa-search@aisa
```

For a one-session development load, use:

```bash
claude --plugin-dir ./plugins/aisa-search
```

The Claude marketplace format follows the official
[Claude Code plugin marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces).

## Use

Ask naturally, for example:

> Research the AI coding agent plugin market across web, X, YouTube, and
> Scholar. Return a concise brief with source links.

Codex can invoke `$research-topic`; Claude Code exposes the namespaced
`/aisa-search:research-topic` Skill.

The default workflow makes one request per source. Tavily extraction is only
used for an explicit deep-research request and accepts at most three public
URLs.

## Script contract

The Skill calls:

```bash
python3 <plugin-root>/scripts/aisa_api.py <operation>
```

with a JSON object on stdin. Supported operations are:

- `tavily_search`
- `tavily_extract`
- `twitter_advanced_search`
- `youtube_search`
- `scholar_search_web`

Successful responses use:

```json
{"ok":true,"operation":"tavily_search","data":{},"request_id":""}
```

Exit code `2` means input/configuration failure, `3` means authentication,
balance, or permission failure, and `4` means rate limit, network, timeout, or
upstream failure. API keys are never written to output.

## Validate

From the repository root:

```bash
python3 -m unittest discover -s plugins/aisa-search/tests -v
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" plugins/aisa-search/skills/research-topic
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/aisa-search
```

## Dify

The Dify Tool Plugin adapter lives in `dify/` and shares the same fixed,
read-only AIsa client implementation as the Codex and Claude Code adapters.
Package it from the repository root with:

```bash
dify plugin package ./plugins/aisa-search/dify
```

When Claude Code is available, also run:

```bash
claude plugin validate .
```

<!-- ownership-check probe: non-owner editing aisa-search -->
