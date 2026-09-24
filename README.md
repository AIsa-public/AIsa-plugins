# AIsa Plugins

Public marketplace for agent plugins maintained by AIsa. One repository, many plugins, many
host platforms (Claude Code, Codex, Dify, Cursor today) and, over time, many languages — all held to
one [code standard](CODE_STANDARD.md) that CI enforces on every pull request.

## Plugins

<!-- plugins:start -->
| Plugin | Version | Hosts | Description | Owners |
|---|---|---|---|---|
| [`aisa-gtm`](plugins/aisa-gtm) | `0.2.0` | Dify | Go-to-market data tools (traffic, keywords, social, prospects, creators, AI visibility) for Dify. | @lhymmEU |
| [`aisa-search`](plugins/aisa-search) | `0.1.2` | Claude Code, Codex, Dify | Search across the web, X, YouTube, and Scholar with linked evidence. | @zhenlonghe |
| [`aisa-tools`](plugins/aisa-tools) | `0.1.0` | Cursor | Connect Cursor (and Grok Bot) to the AIsa Tool Router MCP at tools.aisa.one. | @eddiearc |
<!-- plugins:end -->

The table is generated from each plugin's `plugin.aisa.yaml`; CI fails if it drifts.
Installation, configuration and usage for each host live in the plugin's own README
(linked above). Every plugin needs an `AISA_API_KEY` from [aisa.one](https://aisa.one),
supplied through the host's credential mechanism — never committed.

## How a pull request works

1. **Open a [Work item](../../issues/new/choose)** before non-trivial work. It is labelled
   `status: in-progress` automatically — the open-issue list is the team's live board.
2. **Branch from `main`** (`feat/<slug>`, `fix/<slug>`), commit as `scope: imperative summary`,
   and run `bash .github/scripts/check_all.sh` — the exact sequence CI runs.
3. **Open the PR** with the template filled in and `Closes #<work item>`. Path labels are
   applied automatically; the work item moves to `status: in-review`.
4. **CI (`gate`)** discovers every plugin from its `plugin.aisa.yaml` and runs: universal
   standard checks → language lint → each plugin's offline tests → host validators (Dify
   packaging, Claude Code / Codex manifests and catalogs) → workflow lint → secret scan.
   A plugin declaring a language or host without a profile fails loudly.
5. **Approval (`ownership`)** depends on the paths you touched — and if you are in the
   group, nobody has to approve:

   | Files | Approval from |
   |---|---|
   | `plugins/<name>/**` | one of that plugin's `owners` |
   | a plugin not yet on `main` | a repository admin |
   | anything else | a repository admin |

   Owners ship their own plugin on green CI; admins ship repository changes on green CI;
   touching someone else's plugin pings its owners and waits for one of them.
6. **Merge** (merge, squash or rebase) once both required checks are green and the branch is
   up to date. Nobody pushes to `main` directly, admins included.
7. **After merge** the work item closes and its status label clears; a version bump is only
   made after the previous version is live on its marketplace.

## Attribution

Every plugin tells AIsa *which plugin, on which host, at which version* made a call — and
nothing about who the user is. That is how AIsa knows how much usage each plugin drives.
The rule is [CODE_STANDARD.md §5a](CODE_STANDARD.md#5a-attribution); the practice that makes
it work:

- **One token, one place.** Build the `User-Agent` in the plugin's AIsa client and route
  every request through it — tools, quotes, retries, fallbacks. A second code path that
  forgets the header is unattributed traffic.
  `aisa-<plugin>-<host>-plugin/<version> (+https://github.com/AIsa-public/AIsa-plugins)`
- **Version from the manifest, never a literal.** Read it at runtime from `manifest.yaml`
  / `plugin.json` so a bump can't leave the token behind (`aisa-gtm` reads
  `manifest.yaml`; that is the reference implementation).
- **Host in the token.** The same plugin on Dify and on Claude Code should be two lines in
  AIsa's dashboard, not one — pass the host through to the client rather than guessing it.
- **No user data.** AIsa counts distinct users from the API key. Prompts, e-mails, IDs and
  tenant names never go into headers.
- **Test it offline.** Capture the outgoing request in the plugin's test suite and assert
  the exact token for each host; it is a one-line test and the only thing that catches a
  silent regression.
- **Keep billing mode separate.** Quote/dry-run calls use the same token plus
  `X-AISA-Cost-Mode`; don't encode mode into the token.

CI can't observe runtime traffic, so this is confirmed in the PR checklist and in review.

## Read this before contributing (humans and agents)

Read in this order — the first three are the whole contract:

| File | What it tells you |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Work-item flow, local checks, how to add a plugin / language / host, labels |
| [`CODE_STANDARD.md`](CODE_STANDARD.md) | The universal rules every plugin must meet, and the `plugin.aisa.yaml` schema |
| [`standards/`](standards) | Per-language (`languages/python.md`) and per-host (`hosts/dify.md`, `claude-code.md`, `codex.md`, `cursor.md`) profiles — required files, tooling, packaging |
| [`plugins/<name>/plugin.aisa.yaml`](plugins/aisa-search/plugin.aisa.yaml) | A real declaration to copy: name, version, owners, languages, hosts, tests, version sources |
| [`.github/scripts/check_all.sh`](.github/scripts/check_all.sh) | One command that runs everything CI runs; the scripts next to it are the checks themselves |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) · [`ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE) | What a PR and a work item must say |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) · [`ownership.yml`](.github/workflows/ownership.yml) | The gate and the approval policy, as executed |
| [`.github/CODEOWNERS`](.github/CODEOWNERS) | Who gets asked to review what (routing; the policy is `ownership.yml`) |

Agents: the standard is machine-checked, so run `check_all.sh` and fix what it reports rather
than guessing; never hand-edit generated blocks (this README's plugin table) — regenerate them.

## Repository layout

```text
plugins/<name>/                     one plugin; plugin.aisa.yaml + README.md at the root
plugins/<name>/<host>/              host-specific implementation (e.g. dify/)
.claude-plugin/marketplace.json     Claude Code catalog
.agents/plugins/marketplace.json    Codex catalog
.cursor-plugin/marketplace.json     Cursor catalog
standards/                          language and host profiles of the code standard
.github/scripts/                    the CI checks (check_all.sh runs them all locally)
.github/workflows/                  ci.yml (gate), ownership.yml, labels, status automation
```

No API keys live in this repository. `.env` files are ignored and CI fails if one is tracked.
