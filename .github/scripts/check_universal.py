#!/usr/bin/env python3
"""Enforce the universal layer of the AIsa code standard (CODE_STANDARD.md §1–§6, §9–§10).

Language- and host-agnostic by construction: everything here is derived from
``plugin.aisa.yaml`` and the repository tree. Language rules live in
``.github/scripts/lint/<language>.sh``; host rules in ``.github/scripts/hosts/<host>.sh``.

Exit status is non-zero if any check fails. Findings are printed as GitHub annotations
(``::error file=…::``) and as plain lines for local runs.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import discover

REPO = discover.REPO
SCRIPTS = REPO / ".github" / "scripts"
STANDARDS = REPO / "standards"

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HANDLE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
CODEOWNERS = REPO / ".github" / "CODEOWNERS"
VERSION_LINE = re.compile(
    r"""^\s*"?version"?\s*[:=]\s*["']?([0-9][^"'\s,]*)""", re.MULTILINE | re.IGNORECASE
)

# Scripts that are never English: CJK, kana, hangul, fullwidth forms, Cyrillic, Arabic, Thai.
NON_LATIN = re.compile("[一-鿿぀-ヿ가-힯　-〿＀-￯Ѐ-ӿ؀-ۿ฀-๿]")
# `zh_Hans:` / "ja_JP": — locale-keyed manifest fields. `en_*` is not exempt.
LOCALE_KEY = re.compile(r"""^\s*["']?(?!en[_-])[a-z]{2}[_-][A-Za-z]{2,4}["']?\s*:""")
# README.zh_Hans.md, README_zh_Hans.md, readme/README_zh.md …
LOCALE_FILE = re.compile(r"(?:^|[._-])(?!en)[a-z]{2}(?:[_-][A-Za-z]{2,4})?\.[A-Za-z0-9]+$")
I18N_MARKER = "aisa-i18n-ok"
TEXT_SUFFIXES = {
    ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".cfg", ".ini",
    ".py", ".ts", ".js", ".mjs", ".sh", ".go", ".rs", ".rb",
}  # fmt: skip

# Files that must never be tracked (§5) — matched against `git ls-files` paths.
FORBIDDEN_TRACKED = [
    (re.compile(r"(^|/)\.env(\.[^/]+)?$"), "environment file"),
    (re.compile(r"\.difypkg$"), "Dify package"),
    (re.compile(r"(^|/)__pycache__/"), "Python bytecode cache"),
    (re.compile(r"\.pyc$"), "Python bytecode"),
    (re.compile(r"(^|/)\.DS_Store$"), "macOS metadata"),
]
FORBIDDEN_EXCEPT = re.compile(r"(^|/)\.env\.example$")


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passed = 0

    def ok(self, message: str) -> None:
        self.passed += 1
        print(f"  ok   {message}")

    def fail(self, file: str, message: str) -> None:
        self.failures.append(f"{file}: {message}")
        print(f"::error file={file}::{message}")
        print(f"  FAIL {file}: {message}")

    def check(self, condition: bool, file: str, message: str) -> bool:
        if condition:
            self.ok(message)
        else:
            self.fail(file, message)
        return condition


def tracked_files(subdir: str = "") -> list[str]:
    # Tracked plus untracked-but-not-ignored, so a local run sees files not yet `git add`ed.
    args = ["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    if subdir:
        args += ["--", subdir]
    try:
        out = subprocess.run(args, check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        root = REPO / subdir if subdir else REPO
        return sorted(
            p.relative_to(REPO).as_posix()
            for p in root.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )
    return [f for f in out.decode("utf-8").split("\0") if f]


# --- §9 declaration shape -------------------------------------------------------------


def check_declaration(decl: dict[str, Any], report: Report) -> bool:
    path = decl["_path"]
    dirname = Path(decl["_dir"]).name
    ok = True
    ok &= report.check(decl.get("schema") == 1, path, "schema: 1")
    name = decl.get("name")
    ok &= report.check(
        isinstance(name, str) and bool(NAME.match(name)) and name == dirname,
        path,
        f"name is kebab-case and equals the directory name ({dirname})",
    )
    version = decl.get("version")
    ok &= report.check(
        isinstance(version, str) and bool(SEMVER.match(version)),
        path,
        "version is a quoted semantic version",
    )
    ok &= report.check(
        isinstance(decl.get("description"), str) and decl["description"].strip() != "",
        path,
        "description present",
    )
    langs = decl.get("languages")
    ok &= report.check(
        isinstance(langs, list) and len(langs) > 0 and all(isinstance(x, str) for x in langs),
        path,
        "languages is a non-empty list",
    )
    hosts = decl.get("hosts")
    ok &= report.check(
        isinstance(hosts, dict) and len(hosts) > 0,
        path,
        "hosts is a non-empty mapping",
    )
    tests = decl.get("tests")
    ok &= report.check(
        isinstance(tests, list)
        and len(tests) > 0
        and all(isinstance(t, dict) and {"language", "run"} <= set(t) for t in tests),
        path,
        "tests is a non-empty list of {language, run[, cwd]}",
    )
    owners = decl.get("owners")
    ok &= report.check(
        isinstance(owners, list)
        and len(owners) > 0
        and all(isinstance(o, str) and HANDLE.match(o) for o in owners),
        path,
        "owners is a non-empty list of GitHub handles",
    )
    sources = decl.get("version_sources")
    ok &= report.check(
        isinstance(sources, list) and len(sources) > 0,
        path,
        "version_sources is a non-empty list",
    )
    return bool(ok)


# --- §10 profiles exist for everything declared -----------------------------------------


def check_profiles(decl: dict[str, Any], report: Report) -> None:
    path = decl["_path"]
    for language in decl["languages"]:
        profile = STANDARDS / "languages" / f"{language}.md"
        recipe = SCRIPTS / "lint" / f"{language}.sh"
        report.check(
            profile.is_file(), path, f"language '{language}' has a profile ({profile.name})"
        )
        report.check(
            recipe.is_file(), path, f"language '{language}' has a lint recipe (lint/{recipe.name})"
        )
    for host in decl["hosts"]:
        profile = STANDARDS / "hosts" / f"{host}.md"
        validator = SCRIPTS / "hosts" / f"{host}.sh"
        report.check(profile.is_file(), path, f"host '{host}' has a profile ({profile.name})")
        report.check(
            validator.is_file(), path, f"host '{host}' has a validator (hosts/{validator.name})"
        )
    for test in decl["tests"]:
        report.check(
            test["language"] in decl["languages"],
            path,
            f"test language '{test['language']}' is declared under languages",
        )


# --- §8 CODEOWNERS routing agrees with the declaration -------------------------------------


def codeowners_for(path_prefix: str) -> set[str] | None:
    if not CODEOWNERS.is_file():
        return None
    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if parts and parts[0] == path_prefix:
            return {p.lstrip("@") for p in parts[1:]}
    return None


def check_owners(decl: dict[str, Any], report: Report) -> None:
    prefix = f"/{decl['_dir']}/"
    listed = codeowners_for(prefix)
    report.check(
        listed == set(decl["owners"]),
        ".github/CODEOWNERS",
        f"{prefix} lists exactly the declared owners ({', '.join(decl['owners'])})",
    )


# --- §1, §2, §6 layout ---------------------------------------------------------------------


def check_layout(decl: dict[str, Any], report: Report) -> None:
    base = REPO / decl["_dir"]
    path = decl["_path"]
    report.check((base / "README.md").is_file(), path, "README.md present at the plugin root")
    for host, sub in decl["hosts"].items():
        report.check((base / (sub or ".")).is_dir(), path, f"host '{host}' directory exists")
    for test in decl["tests"]:
        cwd = base / test.get("cwd", ".")
        report.check(cwd.is_dir(), path, f"test cwd exists for '{test['run']}'")


# --- §4 version sync -------------------------------------------------------------------------


def check_versions(decl: dict[str, Any], report: Report) -> None:
    base = REPO / decl["_dir"]
    expected = decl["version"]
    for rel in decl["version_sources"]:
        file = base / rel
        display = f"{decl['_dir']}/{rel}"
        if not report.check(file.is_file(), display, "version source exists"):
            continue
        match = VERSION_LINE.search(file.read_text(encoding="utf-8"))
        found = match.group(1).split("+", 1)[0] if match else None
        report.check(
            found == expected,
            display,
            f"version {found!r} matches plugin.aisa.yaml ({expected})",
        )


# --- §3 English primary ------------------------------------------------------------------------


def non_english_lines(file: Path) -> list[int]:
    if file.suffix.lower() not in TEXT_SUFFIXES or LOCALE_FILE.search(file.name):
        return []
    try:
        text = file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        if not NON_LATIN.search(line) or I18N_MARKER in line or LOCALE_KEY.match(line):
            continue
        hits.append(number)
    return hits


def check_english(decl: dict[str, Any], report: Report) -> None:
    offenders = []
    for rel in tracked_files(decl["_dir"]):
        for number in non_english_lines(REPO / rel):
            offenders.append(f"{rel}:{number}")
            print(f"::error file={rel},line={number}::non-English text outside a locale field")
    report.check(
        not offenders,
        decl["_path"],
        "English-only outside locale-keyed fields and locale-tagged files"
        + (f" ({len(offenders)} lines: {', '.join(offenders[:5])}…)" if offenders else ""),
    )


# --- §5 hygiene (repository-wide) ----------------------------------------------------------


def check_hygiene(report: Report) -> None:
    for rel in tracked_files():
        if FORBIDDEN_EXCEPT.search(rel):
            continue
        for pattern, label in FORBIDDEN_TRACKED:
            if pattern.search(rel):
                report.fail(rel, f"{label} must not be tracked")
    report.ok("no forbidden files tracked (.env, *.difypkg, __pycache__, .DS_Store)")


def main() -> int:
    report = Report()
    try:
        declarations = discover.load_all()
    except discover.DeclarationError as exc:
        report.fail(str(exc).split(":", 1)[0], str(exc))
        declarations = []

    for decl in declarations:
        print(f"\n== {decl['_dir']}")
        if not check_declaration(decl, report):
            continue
        check_profiles(decl, report)
        check_owners(decl, report)
        check_layout(decl, report)
        check_versions(decl, report)
        check_english(decl, report)

    print("\n== repository")
    check_hygiene(report)

    print(f"\n{report.passed} checks passed, {len(report.failures)} failed")
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
