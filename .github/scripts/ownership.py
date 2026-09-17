#!/usr/bin/env python3
"""Path-scoped approval policy for pull requests (CONTRIBUTING.md §4).

Who has to approve depends on what the PR touches:

- ``plugins/<name>/**``  -> that plugin's ``owners`` (from ``plugin.aisa.yaml`` on the base branch)
- a plugin with no declaration on the base branch (i.e. a new plugin) -> repository admins
- anything else          -> repository admins

Each group is satisfied when the PR author belongs to it or a current member of it has an
approving review. Runs from the base branch (see ``.github/workflows/ownership.yml``); the
decision itself is the pure function :func:`decide`, covered by ``tests/test_ownership.py``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

API = "https://api.github.com"
PLUGIN_PATH = re.compile(r"^plugins/([^/]+)/")
ADMIN_GROUP = "repository admins"


# --- decision (pure) ---------------------------------------------------------------------


def latest_approvals(reviews: list[dict]) -> set[str]:
    """Logins whose most recent decisive review is an approval.

    ``reviews`` is in submission order (as the API returns it). COMMENTED reviews never
    change a reviewer's standing; CHANGES_REQUESTED and DISMISSED revoke an earlier approval.
    """
    standing: dict[str, bool] = {}
    for review in reviews:
        login = review["user"]["login"]
        state = review["state"]
        if state == "APPROVED":
            standing[login] = True
        elif state in ("CHANGES_REQUESTED", "DISMISSED"):
            standing[login] = False
    return {login for login, approved in standing.items() if approved}


def groups_for(files: list[str], plugin_owners: dict[str, set[str]], admins: set[str]):
    """Map each approval group touched by the PR to (owners, files)."""
    groups: dict[str, tuple[set[str], list[str]]] = {}

    def add(label: str, owners: set[str], file: str) -> None:
        groups.setdefault(label, (set(owners), []))[1].append(file)

    for file in files:
        match = PLUGIN_PATH.match(file)
        if not match:
            add(ADMIN_GROUP, admins, file)
            continue
        name = match.group(1)
        owners = plugin_owners.get(name)
        if owners:
            add(f"plugin {name} (owners: {', '.join(sorted(owners))})", owners, file)
        else:
            add(f"new plugin {name} -> {ADMIN_GROUP}", admins, file)
    return groups


def decide(
    files: list[str],
    author: str,
    approvers: set[str],
    admins: set[str],
    plugin_owners: dict[str, set[str]],
) -> tuple[bool, list[str]]:
    """Return (ok, human-readable lines), one line per approval group."""
    lines = []
    ok = True
    for label, (owners, touched) in groups_for(files, plugin_owners, admins).items():
        if author in owners:
            lines.append(f"ok   {label}: author @{author} is a member ({len(touched)} files)")
        elif approvers & owners:
            who = ", ".join(f"@{u}" for u in sorted(approvers & owners))
            lines.append(f"ok   {label}: approved by {who} ({len(touched)} files)")
        else:
            ok = False
            if label.endswith(ADMIN_GROUP):
                need = "a repository admin"
            else:
                need = ", ".join(f"@{u}" for u in sorted(owners)) or "(nobody is listed!)"
            sample = ", ".join(touched[:3]) + (" …" if len(touched) > 3 else "")
            lines.append(f"NEED {label}: approval from one of {need} — touches {sample}")
    if not lines:
        lines.append("ok   no files changed")
    return ok, lines


# --- GitHub plumbing -------------------------------------------------------------------------


def api(path: str, token: str, params: dict | None = None) -> list | dict:
    """GET a REST endpoint, following pagination for list responses."""
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    collected: list = []
    while url:
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "aisa-plugins-ownership-check",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            link = response.headers.get("Link", "")
        if not isinstance(payload, list):
            return payload
        collected.extend(payload)
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = match.group(1) if match else ""
    return collected


def is_admin(repo: str, login: str, token: str) -> bool:
    """Per-user permission lookup — readable with the workflow token, unlike the
    collaborator listing, which silently comes back empty."""
    try:
        info = api(f"/repos/{repo}/collaborators/{urllib.parse.quote(login)}/permission", token)
    except urllib.error.HTTPError:
        return False
    return info.get("role_name") == "admin" or info.get("permission") == "admin"


def owners_on_base(root: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for declaration in sorted(root.glob("plugins/*/plugin.aisa.yaml")):
        with declaration.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        owners = data.get("owners") or []
        result[declaration.parent.name] = {str(o).lstrip("@") for o in owners}
    return result


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["PR_NUMBER"])
    root = Path(os.environ.get("BASE_CHECKOUT", "."))

    pr = api(f"/repos/{repo}/pulls/{number}", token)
    author = pr["user"]["login"]
    page = {"per_page": 100}
    files = [f["filename"] for f in api(f"/repos/{repo}/pulls/{number}/files", token, page)]
    reviews = api(f"/repos/{repo}/pulls/{number}/reviews", token, page)
    approvers = latest_approvals(reviews)
    # Only the people who can satisfy a group matter: the author and the current approvers.
    admins = {login for login in {author, *approvers} if is_admin(repo, login, token)}
    ok, lines = decide(files, author, approvers, admins, owners_on_base(root))

    heading = "Ownership check: " + ("satisfied" if ok else "approval still needed")
    print(f"PR #{number} by @{author}; approvals: {', '.join(sorted(approvers)) or 'none'}")
    print(heading)
    for line in lines:
        print("  " + line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"### {heading}\n\n```\n" + "\n".join(lines) + "\n```\n")
    if not ok:
        print("::error::" + "; ".join(line for line in lines if line.startswith("NEED")))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
