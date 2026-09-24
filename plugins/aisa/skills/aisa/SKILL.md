---
name: aisa
description: "Discover and invoke published AIsa tools through the aisa plugin MCP server (search, schema, quote, call). Use when the user wants AIsa tools, or needs current web, company, or social data that AIsa tools can fetch, even if they do not name AIsa. Do not use for work that does not need live AIsa data."
license: MIT
---

# AIsa

This plugin already registers the AIsa Tool Router MCP server (`aisa`, Streamable HTTP with OAuth at `https://tools.aisa.one/mcp`). Use its tools directly. Do not install packages or other skills, and do not re-add the MCP server.

If the user named another tool, or a dedicated local tool already covers the job, do not force AIsa.

## Connection

Cursor owns the OAuth browser sign-in and tokens. Never print credentials. If the `AISA_*` tools are missing or a call reports that sign-in is required, tell the user to open Cursor Settings → MCP → `aisa` → Connect (or log in), and do not claim it is connected until it is. A 401 means sign-in is required; it is not a successful call. Do not treat a domain-specific MCP server as this router.

## Tools

| MCP tool | Step |
| --- | --- |
| `AISA_SEARCH_TOOL` | Find tools for the user's goal |
| `AISA_BATCH_GET_SCHEMA` | Fetch full argument schemas |
| `AISA_BATCH_QUOTE` | Price a batch of calls without running it |
| `AISA_BATCH_USE` | Execute a batch of calls |

## Workflow

`AISA_SEARCH_TOOL` → `AISA_BATCH_GET_SCHEMA` when `has_full_schema` is false → `AISA_BATCH_QUOTE` → `AISA_BATCH_USE` inside the authorized scope and spend.

- Take tool IDs and arguments from search and schema results. Do not invent tool IDs or prices. Runtime schema and quote are authoritative.
- Quote and use share the same `calls` shape, for example `{"calls":[{"call_id":"c1","tool":"<name from search>","arguments":{}}]}`.

## Spend

- A quote does not execute and is not approval to execute.
- A missing, failed, or partial quote is not free and is not a full-batch total or cap. An estimated cost is not a cap.
- A working connection is not permission for paid execution. Reuse a still-valid explicit authorization; do not add confirmation loops for search or schema.
- Re-quote if tools, arguments, or scope change. Do not silently retry or expand the batch.
- No credit means the account needs a top-up, not an auth problem.

## License

MIT. Adapted from the `platform/aisa` skill in [AIsa-team/agent-skills](https://github.com/AIsa-team/agent-skills); see [LICENSE](LICENSE).
