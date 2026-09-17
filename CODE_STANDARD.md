# AIsa Code Standard

This is the contract every plugin in this repository is held to — whatever language it is
written in and whatever host platform it targets. CI enforces it on every pull request
(`.github/workflows/ci.yml`); the rules below are the ones a reviewer should never have to
argue about.

The standard has three layers:

| Layer | Where | Scope |
|---|---|---|
| **Universal rules** | this document | every plugin, always |
| **Language profiles** | `standards/languages/<language>.md` | formatter, linter, version floor and idioms for one language |
| **Host profiles** | `standards/hosts/<host>.md` | required files, manifests and packaging for one host (Dify, Claude Code, Codex, …) |

A plugin declares which profiles apply to it in its `plugin.aisa.yaml` (§9). CI reads that
file and runs exactly those checks. Nothing in *this* document may name a specific language
or host — if a rule only makes sense for one of them, it belongs in a profile.

## 1. Repository layout

- One plugin is one directory: `plugins/<name>/`. `<name>` is lowercase kebab-case and is the
  plugin's identity everywhere — manifests, marketplace catalogs, issue labels.
- A host-specific implementation lives in `plugins/<name>/<host>/`. A plugin that is a single
  bundle consumed by several hosts may keep that bundle at the plugin root.
- Every plugin directory carries a `plugin.aisa.yaml`. CI fails on any directory under
  `plugins/` that does not have one.
- Plugins do not share code. Hosts sandbox plugins individually, so each plugin is
  self-contained even when that means a small amount of duplication.

## 2. Required in every plugin

- `plugin.aisa.yaml` (§9)
- `README.md` — what the plugin does, how to install it on each host, configuration, and how to
  run its offline tests
- an offline test entry point, declared in `plugin.aisa.yaml` (§6)
- a single declared version (§4)
- whatever the applicable host profiles require (privacy statement, manifests, icons, …)

## 3. Language

- **English is the primary language** of everything public: code, identifiers, comments,
  commit messages, READMEs, manifests, issues and pull requests.
- Localized text is welcome, but only where it is unambiguously localized: in locale-keyed
  manifest fields (`zh_Hans:`, `ja_JP:`, `pt_BR:` …) or in locale-tagged files
  (`README.zh_Hans.md`). Non-English text anywhere else fails CI.
- A line that legitimately needs non-Latin characters (a Unicode test fixture, for example)
  carries the marker `aisa-i18n-ok` on that line.

## 4. Versioning

- A plugin has exactly one version, declared in `plugin.aisa.yaml`. Every other place the
  version appears is listed under `version_sources`, and CI checks that all of them agree.
- Semantic versioning. Host-specific build metadata may follow a `+`
  (`1.2.3+codex.20260101`); the part before `+` must match.
- Bump the version **only after the previous version has been published** to its
  marketplace(s). Never bump inside a pull request that is still under review — update the
  open PR in place instead.
- Every version bump comes with a README or changelog note saying what changed.

## 5. Secrets and safety

- No credentials in the repository — not in code, fixtures, examples or history. `.env`
  files are ignored and CI fails if one is tracked; `.env.example` files hold placeholders
  only.
- Credentials reach a plugin through the host's credential mechanism or an environment
  variable, never from a file the plugin reads.
- Network clients never trust an HTTP status alone. The response body is inspected for error
  markers before it is handed to the caller — AIsa APIs can return error payloads inside a
  `200` response.
- Every dependency is pinned and CI installs from pinned requirements. A runtime dependency
  beyond the host SDK needs a one-line justification in the pull request.
- Plugins are read-only towards third-party platforms unless writing *is* the plugin's
  purpose; write paths are opt-in and documented in the README.

## 6. Tests

- Every plugin has an **offline** test suite: no network, no API key, runnable with one
  command in a fresh checkout. It is declared in `plugin.aisa.yaml` and CI runs it on every
  pull request.
- Every tool, command or skill entry point has at least one offline test.
- Anything that spends money or needs credentials — live contract audits, quota probes — runs
  only on a schedule or manual dispatch, never on pull requests.

## 7. Formatting and linting

- Formatting and linting are automated and non-negotiable. The language profile says which
  tools apply; the checked-in configuration (`ruff.toml`, `.editorconfig`, …) is the source
  of truth, not the prose.
- A pull request that changes formatter or linter configuration contains the resulting
  reformat as a **separate commit** so the review can tell policy from mechanics.
- No per-plugin overrides of formatter settings.

## 8. Commits, pull requests and issues

- Commit subject: `scope: imperative summary` — `aisa-search: reject private extract URLs`,
  `ci: pin actions by SHA`, `docs: …`. The body explains *why*, not *what*.
- One concern per pull request. Link the issue it belongs to and fill in the PR template.
- **Who approves is decided by what the PR touches** (enforced by the `ownership` check):
  files under `plugins/<name>/` need one of that plugin's `owners`; everything else needs a
  repository admin. An author who is in the group needs no review for that group, so owners
  merge their own plugin work and admins merge repository work; a new plugin needs an admin.
- Work is coordinated through issues (see `CONTRIBUTING.md`): a **work item** is opened before
  non-trivial work starts, so the open-issue list is the live view of who is doing what.
- Reviews check against this standard. Matters of taste that are not written down here are
  not blocking comments; if they should be, change the standard first.

## 9. `plugin.aisa.yaml`

```yaml
schema: 1
name: aisa-search              # must equal the directory name
version: "0.1.2"               # the single source of truth (§4)
owners: [zhenlonghe]           # GitHub handles; their approval covers changes to this plugin (§8)
description: One sentence, English.
languages: [python]            # each needs standards/languages/<lang>.md + a lint recipe
hosts:                         # host -> directory relative to the plugin, "." for the root
  dify: dify
  claude-code: .
  codex: .
tests:                         # at least one; run from `cwd` (relative, default ".")
  - language: python
    run: python3 -m unittest discover -s tests
version_sources:               # every file that repeats the version (relative paths)
  - .claude-plugin/plugin.json
  - dify/manifest.yaml
```

`.github/scripts/discover.py` turns these files into the CI matrix;
`.github/scripts/check_universal.py` enforces §1–§6 against them.

## 10. Extending the standard

- **New language**: add `standards/languages/<language>.md`, a lint recipe at
  `.github/scripts/lint/<language>.sh`, and a runtime setup step for that language in the
  `lint` and `test` jobs of `ci.yml`. CI refuses a plugin that declares a language without
  a profile and recipe.
- **New host**: add `standards/hosts/<host>.md` and a validator at
  `.github/scripts/hosts/<host>.sh` (required files, manifest validation, and a packaging
  dry-run where the host has one). CI refuses a plugin that declares a host without them.
- This document, the profiles, the CI scripts and the workflows are owned by the
  maintainers in `.github/CODEOWNERS`; changes go through a reviewed pull request like any
  other code.
