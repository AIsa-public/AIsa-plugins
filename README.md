# AIsa Plugins

Public marketplace for agent plugins maintained by AIsa. One repository, many plugins, many
host platforms (Claude Code, Codex, Dify today) and, over time, many languages — all held to
one [code standard](CODE_STANDARD.md) that CI enforces on every pull request.

## Plugins

<!-- plugins:start -->
| Plugin | Version | Hosts | Description | Owners |
|---|---|---|---|---|
| [`aisa-gtm`](plugins/aisa-gtm) | `0.2.0` | Dify | Go-to-market data tools (traffic, keywords, social, prospects, creators, AI visibility) for Dify. | @lhymmEU |
| [`aisa-search`](plugins/aisa-search) | `0.1.2` | Claude Code, Codex, Dify | Search across the web, X, YouTube, and Scholar with linked evidence. | @zhenlonghe |
<!-- plugins:end -->

The table is generated from each plugin's `plugin.aisa.yaml`; CI fails if it drifts. Every
plugin needs an `AISA_API_KEY` from [aisa.one](https://aisa.one), supplied through the host's
credential mechanism — never committed.

### Install

**Claude Code**

```bash
claude plugin marketplace add AIsa-public/AIsa-plugins
claude plugin install aisa-search@aisa
```

Start a new session; the skill is exposed as `/aisa-search:research-topic`.

**Codex**

```bash
codex plugin marketplace add AIsa-public/AIsa-plugins
codex plugin add aisa-search@aisa
```

**Dify** — install from the Dify marketplace (`aisa-team/go-to-market`, `aisa-search`) or
package from source with the Dify Plugin CLI:

```bash
dify plugin package ./plugins/aisa-gtm/dify -o go-to-market.difypkg
dify plugin package ./plugins/aisa-search/dify -o aisa-search.difypkg
```

Per-plugin setup, configuration and usage live in each plugin's own README (linked above).

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

## Read this before contributing (humans and agents)

Read in this order — the first three are the whole contract:

| File | What it tells you |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Work-item flow, local checks, how to add a plugin / language / host, labels |
| [`CODE_STANDARD.md`](CODE_STANDARD.md) | The universal rules every plugin must meet, and the `plugin.aisa.yaml` schema |
| [`standards/`](standards) | Per-language (`languages/python.md`) and per-host (`hosts/dify.md`, `claude-code.md`, `codex.md`) profiles — required files, tooling, packaging |
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
standards/                          language and host profiles of the code standard
.github/scripts/                    the CI checks (check_all.sh runs them all locally)
.github/workflows/                  ci.yml (gate), ownership.yml, labels, status automation
```

No API keys live in this repository. `.env` files are ignored and CI fails if one is tracked.
