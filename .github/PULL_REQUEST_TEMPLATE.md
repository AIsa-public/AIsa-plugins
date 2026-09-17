<!-- One concern per PR. Link the work item it belongs to. Standard: CODE_STANDARD.md -->

## What & why

<!-- What changes, and the reason. Link context if it lives elsewhere. -->

Closes #

## Scope

- Plugin(s):
- Host(s): <!-- claude-code / codex / dify / … -->
- Language profile(s): <!-- python / … -->

## Type of change

- [ ] Fix
- [ ] Feature
- [ ] Chore / CI
- [ ] Docs
- [ ] Version bump — the previous version is already published on every marketplace

## Checklist — AIsa code standard

- [ ] `bash .github/scripts/check_all.sh` passes locally
- [ ] Offline tests cover the change (no network, no key)
- [ ] No secrets or `.env`; new dependencies are pinned and justified below
- [ ] Version untouched, or bumped everywhere listed in `version_sources`
- [ ] Attribution: every call to AIsa sends `aisa-<plugin>-<host>-plugin/<version> (+repo)` as `User-Agent`, built in one place from the manifest version, and an offline test asserts it per host (n/a if no AIsa calls changed)
- [ ] README / profile docs updated; English-only outside locale fields
- [ ] Commit subjects follow `scope: imperative summary`

## How I verified it

<!-- Commands run, hosts exercised, screenshots if UI-facing. -->
