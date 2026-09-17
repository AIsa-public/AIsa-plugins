# Contributing to AIsa Plugins

Everything here is governed by the [AIsa Code Standard](CODE_STANDARD.md). This page is the
practical side: how work is coordinated, how to run the checks, and how to add things.

## 1. Coordinate through issues

The issue tracker is the team's live board, not just a bug list.

| You are about to… | Open | It gets |
|---|---|---|
| start any non-trivial work | **Work item** (`New issue → Work item`) | `type: work-item`, `status: in-progress` |
| report something broken | **Bug report** | `type: bug` |
| propose a change | **Feature / change proposal** | `type: feature` |

- Open the work item **before** you start, not when you open the PR. Keep the plan checklist
  in it current; it is what teammates read to see what you are on.
- Blocked? Add `status: blocked` and say what you need in a comment.
- Reference the issue from your PR (`Closes #123` / `Refs #123`). Automation moves it to
  `status: in-review`, and clears the status label when the issue closes.
- The board: [open work items](../../issues?q=is%3Aopen+label%3A%22type%3A+work-item%22),
  [blocked](../../issues?q=is%3Aopen+label%3A%22status%3A+blocked%22).

## 2. Set up

```bash
python3 -m pip install -r .github/scripts/requirements.txt   # ruff, pyyaml, check-jsonschema
# optional, for the Dify packaging check:
#   https://github.com/langgenius/dify-plugin-daemon/releases  (dify-plugin-<os>-<arch>)
```

## 3. Run the checks (same as CI)

```bash
bash .github/scripts/check_all.sh
```

It discovers every plugin from its `plugin.aisa.yaml`, then runs the universal checks, the
language lint recipes, every declared test command and every host validator. CI runs the same
scripts, so green locally means green in the PR.

## 4. Pull requests

1. Branch from `main`: `<type>/<short-slug>` (`feat/gtm-creator-filters`, `fix/search-timeout`).
2. Commits: `scope: imperative summary`, one concern per PR.
3. Open the PR against `main`, fill in the template, link the work item.
4. CI must be green (`gate`) and the `ownership` check satisfied. Who has to approve depends
   on the paths you touched — and if you are in the group, nobody does:

   | Files | Approval from |
   |---|---|
   | `plugins/<name>/**` | one of that plugin's `owners` (`plugin.aisa.yaml`) |
   | a plugin that does not exist on `main` yet | a repository admin |
   | anything else (`.github/`, `standards/`, catalogs, README) | a repository admin |

   So an owner ships changes to their own plugin unreviewed, an admin ships repository
   changes unreviewed, and touching someone else's plugin pings its owners (CODEOWNERS
   auto-requests them). The check re-runs whenever a review is submitted.
5. Do **not** bump a version while the previous one is unpublished; update the open
   marketplace PR in place instead (see the host profile).

## 5. Add a plugin

1. Create `plugins/<name>/` with a `plugin.aisa.yaml` (schema in
   [CODE_STANDARD.md §9](CODE_STANDARD.md#9-pluginaisayaml)).
2. Follow each host profile you declare (`standards/hosts/`) and the language profile
   (`standards/languages/`).
3. Add the offline tests and declare the command under `tests`.
4. Register the plugin in the marketplace catalogs the hosts use.
5. Add an `area: <name>` label to `.github/labels.json`, a path rule to `.github/labeler.yml`,
   and a `/plugins/<name>/` line in `.github/CODEOWNERS` listing the same `owners`.
6. `bash .github/scripts/check_all.sh` → open the PR.

## 6. Add a language or a host

**Language** — `standards/languages/<language>.md`, `.github/scripts/lint/<language>.sh`, and a
runtime setup step (`if: matrix.language == '<language>'`) in the `lint` and `test` jobs of
`.github/workflows/ci.yml`.

**Host** — `standards/hosts/<host>.md` and `.github/scripts/hosts/<host>.sh` taking
`<host-dir> <plugin-name>`; add any CLI install step to the `host` job of `ci.yml`.

Until both exist, CI refuses any plugin that declares the new language or host — on purpose.

## 7. Labels

| Prefix | Values |
|---|---|
| `type:` | `bug`, `feature`, `work-item`, `chore`, `docs` |
| `status:` | `planned`, `in-progress`, `blocked`, `in-review` |
| `area:` | one per plugin, plus `marketplace`, `ci`, `standard` |
| `host:` | `claude-code`, `codex`, `dify` |

Labels are declared in `.github/labels.json` and synced by a workflow; edit the file, not
the GitHub UI.
