---
name: aisa
description: "Discover and invoke published AIsa tools through the aisa-tools plugin MCP server (search, schema, quote, call). Use when the user wants AIsa tools, or needs current web, company, or social data that AIsa tools can fetch, even if they do not name AIsa. Do not use for OpenClaw Chinese model provider setup (aisa-provider), installing other catalog skills, or work that does not need live AIsa data."
license: MIT
---

# AIsa

This plugin already registers the AIsa Tool Router MCP server (`aisa-tools`, Streamable HTTP with OAuth at `https://tools.aisa.one/mcp`). Use its tools directly. Do not install `@aisa-one/cli`, npm packages, or skills, and do not re-add or re-connect the MCP server.

If the user named another tool, or a dedicated local tool already covers the job, do not force AIsa.

## Connection

Cursor owns the OAuth browser sign-in and tokens. Never print credentials. Search and schema may work anonymously; they are not proof of auth. Discovery or a 401 is not a protected call. If a call needs sign-in, tell the user to complete the Cursor OAuth prompt for `aisa-tools` and do not claim it is connected until it is. Do not treat a domain-specific MCP server or `aisa connect`'s default web-search server as this router.

Only if the `aisa-tools` MCP tools are unavailable and the user already has a working AIsa CLI may you use it instead; setup details live at https://aisa.one/docs/agent-quickstart.md.

## Tools

| MCP tool | Step | CLI equivalent |
| --- | --- | --- |
| `AISA_SEARCH_TOOL` | Find tools for the user's goal | `aisa search` |
| `AISA_BATCH_GET_SCHEMA` | Fetch full argument schemas | `aisa schema` |
| `AISA_BATCH_QUOTE` | Price a batch of calls without running it | `aisa quote` |
| `AISA_BATCH_USE` | Execute a batch of calls | `aisa call` |

## Workflow

`AISA_SEARCH_TOOL` → `AISA_BATCH_GET_SCHEMA` when `has_full_schema` is false → `AISA_BATCH_QUOTE` → `AISA_BATCH_USE` inside the authorized scope and spend.

- Take tool IDs and arguments from search and schema results. Do not invent tool IDs or prices. Runtime schema and quote are authoritative.
- Quote and use share the same `calls` shape, for example `{"calls":[{"call_id":"c1","tool":"<name from search>","arguments":{}}]}`.

## Spend

- A quote does not execute and is not approval to execute.
- A missing, failed, or partial quote is not free and is not a full-batch total or cap. An estimated cost is not a cap.
- A working connection is not permission for paid execution. Reuse a still-valid explicit authorization; do not add confirmation loops for search or schema.
- Re-quote if tools, arguments, or scope change. Do not silently retry or expand the batch.
- No credit means the account needs a top-up, not a missing key.

## License

MIT. Adapted from the `platform/aisa` skill in [AIsa-team/agent-skills](https://github.com/AIsa-team/agent-skills); see [LICENSE](LICENSE).
