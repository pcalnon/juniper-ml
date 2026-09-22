#!/usr/bin/env python3
"""
Census every juniper-ci-tools version specifier at each repo's REMOTE main, not a local checkout.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md
         (its "want 0 and 0" pin check), juniper-cascor#646, juniper-ml#1909, juniper-cascor-worker#193

``util/ad-hoc/2026-09-11_ci_tools_pin_census.py`` reads the sibling checkouts on disk,
and its own handoff warns "pull the siblings first -- local trees lag". A
worktree-isolated session cannot pull them (the harness refuses cross-repo git), so
this variant downloads each repo's ``main`` as a tarball through the GitHub API and
records the commit SHA it measured. No git, no local checkout.

What it looks for
-----------------
Every version specifier for a ``0.x`` release (``>=0.9.0,<0.10.0``, ``==0.9.0``,
``~=0.9``, ``<0.2.0`` ...) that belongs to juniper-ci-tools. A specifier belongs to it
when either

* the package name immediately precedes it -- ``juniper-ci-tools>=…``, in any case, with
  ``-`` or ``_``, with extras, with spaces around the operator; or
* it is set apart from the name by prose (``juniper-ci-tools (PyPI >=…)``, ``juniper-ci-tools
  package\\n#    (>=…)``, ``… `juniper-docs-additions-check` console scripts (pinned `>=…`)``)
  and the NEAREST earlier juniper name in the same paragraph is juniper-ci-tools or one of
  its console scripts. Repo names used as possessives or PR references (``juniper-ml's``,
  ``juniper-ml#319``) do not count as the nearest name.

A specifier directly preceded by another name (``httpx>=0.27``, ``juniper-doc-tools>=…``)
belongs to that name and is ignored. The ``0.x`` restriction keeps Python and pip
specifiers (``>=3.12``, ``pip>=26.1.1``) out; it must widen if juniper-ci-tools reaches 1.0.

How each is judged
------------------
LIVE              a non-comment line in a workflow or composite action -- must EQUAL --expect.
                  A live ``pip install`` naming the package with no specifier is UNRESOLVED
                  and also fails.
DOC / COMMENT     a current-state description (AGENTS.md, README, docs/, scripts, workflow
                  comments) stating a range with an UPPER bound -- must equal --expect, or the
                  repo's own pyproject extra. A floor-only ``>=X`` states a requirement (the
                  release that introduced a feature), cannot go stale the same way, and is
                  counted as REQUIREMENT.
DECLARATION       pyproject.toml / setup.cfg / *.in -- must ADMIT the latest published release.
LOCK              ``==X`` in requirements*.txt / *.lock -- must fall inside --expect.
FIXTURE           anything under a ``tests/`` directory -- counted only (synthetic inputs).
HISTORICAL        a path segment notes/ prompts/ reports/ releases/ history/ legacy/, a
                  CHANGELOG, or util/ad-hoc/ -- counted only (dated records).
AMBIGUOUS         an upper-bounded 0.x range the attribution could not assign, near text that
                  names ci-tools, a screen pin or sequence-safety -- LISTED for a human to
                  read, never failed. ``docs/REFERENCE.md`` described "the two new
                  ``>=0.8.0,<0.9.0`` screen pins" without naming the package at all; no
                  regex attributes that, so it is surfaced rather than guessed.

Exceptions are explicit (EXCEPTIONS below), each keyed by (repo, path, a substring of the
line) with a reason, so new drift cannot hide behind an old entry.

Usage:  python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py [--expect '>=0.9.0,<0.10.0']
        python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test
Exit:   0 when nothing judged is stale; 1 when something is (each listed); 2 when the census
        could not run -- a failed download, an unreadable tarball, a missing ``packaging``.
        A census that could not run is not clean. Exit 0 does NOT clear the AMBIGUOUS list.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass

OWNER = "pcalnon"
REPOS = (
    "juniper-ml",
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
    "juniper-deploy",
    "juniper-recurrence",
)

NAME_RE = re.compile(r"juniper[-_]ci[-_]tools", re.IGNORECASE)
CI_TOOLS_SCRIPTS = (
    "juniper-symbol-loss-check",
    "juniper-docs-additions-check",
    "juniper-lint-workflow-paths",
    "juniper-coverage-gap-map",
    "juniper-generate-dep-docs",
    "juniper-env-drift-check",
    "juniper-lint-agents-md-version",
    "juniper-lint-agents-md-header",
)
# Any juniper-* token. A trailing possessive or PR reference makes it transparent.
JUNIPER_TOKEN_RE = re.compile(r"juniper[-_][A-Za-z0-9][A-Za-z0-9_-]*", re.IGNORECASE)

_OP = r"(?:===|==|!=|~=|>=|<=|>|<)"
_VER = r"0\.\d+(?:\.\d+)*(?:\.\*)?"
SPEC_RE = re.compile(_OP + r"\s*" + _VER + r"(?:\s*,\s*" + _OP + r"\s*" + _VER + r")*")
# a package-looking token immediately before a specifier (``httpx>=`` or ``juniper-ci-tools[x] >=``)
DIRECT_OWNER_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]\n]*\])?\s*$")
CONTEXT_WORDS_RE = re.compile(r"ci[-_]tools|screen pin|sequence[-_]safety", re.IGNORECASE)

LOOKBACK_CHARS = 240
TEXT_SUFFIXES = (".yml", ".yaml", ".md", ".rst", ".toml", ".txt", ".cfg", ".ini", ".py", ".bash", ".sh", ".json", ".lock", ".in", ".mk")
TEXT_BASENAMES = ("Makefile", "Dockerfile")
HISTORICAL_SEGMENTS = {"notes", "prompts", "reports", "releases", "history", "legacy"}

# (repo, path, substring of the line) -> reason. A reason a reader cannot check is a suppression.
EXCEPTIONS = {
    ("juniper-ml", "util/release_train/propose.py", "minimum-pin note, and a"): "docstring listing the kinds of text the extras-table editor must NOT rewrite; the range is an example, not a claim about CI",
    ("juniper-ml", "pyproject.toml", "capped `<0.2.0` when its extra was added"): "history inside the pin-capping-rule comment: the extra was capped by #293 and uncapped by #295",
}


@dataclass(frozen=True)
class Hit:
    repo: str
    path: str
    line: int
    spec: str
    cls: str  # LIVE DOC COMMENT DECLARATION LOCK FIXTURE HISTORICAL REQUIREMENT AMBIGUOUS EXCEPTION UNRESOLVED
    text: str


def normalise(spec: str) -> str:
    return ",".join(sorted(part.replace(" ", "") for part in spec.split(",")))


def has_upper_bound(spec: str) -> bool:
    return any(part.lstrip().startswith(("<", "==", "===", "~=")) for part in spec.split(","))


def location_class(path: str) -> str:
    """The class a path puts its mentions in, before comment/floor refinement."""
    parts = path.split("/")
    dirs = set(parts[:-1])
    base = parts[-1]
    if path.startswith("util/ad-hoc/") or base.startswith("CHANGELOG") or dirs & HISTORICAL_SEGMENTS:
        return "HISTORICAL"
    if "tests" in dirs:
        return "FIXTURE"
    if path.startswith(".github/workflows/") or path.startswith(".github/actions/"):
        return "WORKFLOW"
    if re.match(r"requirements[^/]*\.(txt|lock)$", base) or base.endswith(".lock"):
        return "LOCK"
    if base in ("pyproject.toml", "setup.cfg") or base.endswith(".in"):
        return "DECLARATION"
    return "DOC"


def comment_start(line: str) -> int:
    """Index where a YAML/shell comment begins on this line, or len(line) if none.

    A '#' counts when it starts the line (after indentation or a list dash) or follows
    whitespace outside quotes -- so ``echo "#1"`` and ``url#frag`` are not comments.
    """
    stripped = line.lstrip()
    if stripped.startswith("#") or stripped.startswith("- #"):
        return len(line) - len(stripped)
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and i > 0 and line[i - 1] in " \t":
            return i
    return len(line)


def paragraph_start(text: str, pos: int) -> int:
    """Start of the paragraph holding ``pos``: just after the last blank (or bare '#') line."""
    cut = 0
    for m in re.finditer(r"\n[ \t]*#?[ \t]*\n", text[:pos]):
        cut = m.end()
    return cut


def owner_of(text: str, start: int) -> str | None:
    """'ci-tools', 'other', or None (unattributable) for the specifier starting at ``start``."""
    before = text[max(0, start - LOOKBACK_CHARS):start]
    m = DIRECT_OWNER_RE.search(before)
    if m:
        token = m.group(1)
        touching = not before[m.end(1):].strip("[] \t") and (m.group(2) or not before[m.end(1):].strip() or JUNIPER_TOKEN_RE.fullmatch(token))
        # ``httpx>=`` (no space) or ``juniper-x >=`` / ``juniper-x[e]>=``: the token owns the specifier.
        if touching and (before.endswith(token) or m.group(2) or JUNIPER_TOKEN_RE.fullmatch(token)):
            if NAME_RE.fullmatch(token):
                return "ci-tools"
            if JUNIPER_TOKEN_RE.fullmatch(token) or before.endswith(token):
                return "other"
    lo = max(paragraph_start(text, start), start - LOOKBACK_CHARS)
    window = text[lo:start]
    for tok in reversed(list(JUNIPER_TOKEN_RE.finditer(window))):
        after = window[tok.end():tok.end() + 2]
        if after.startswith("#") or after.startswith("'s"):
            continue  # juniper-ml#319, juniper-ml's -- a reference, not a package mention
        name = tok.group(0).lower().replace("_", "-")
        if NAME_RE.fullmatch(name) or name in CI_TOOLS_SCRIPTS:
            return "ci-tools"
        return "other"
    return None


def census_text(repo: str, path: str, text: str, extra: str | None) -> list[Hit]:
    hits: list[Hit] = []
    loc = location_class(path)
    lines = text.split("\n")
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln) + 1)

    def line_of(pos: int) -> int:
        lo, hi = 0, len(lines)
        while lo < hi:
            mid = (lo + hi) // 2
            if offsets[mid + 1] <= pos:
                lo = mid + 1
            else:
                hi = mid
        return lo + 1

    judged_lines: set[int] = set()
    for m in SPEC_RE.finditer(text):
        lineno = line_of(m.start())
        raw = lines[lineno - 1]
        col = m.start() - offsets[lineno - 1]
        spec = normalise(m.group(0))
        owner = owner_of(text, m.start())
        if owner == "other":
            continue
        cls = loc
        if loc == "WORKFLOW":
            cls = "LIVE" if col < comment_start(raw) else "COMMENT"
        elif loc in ("DECLARATION", "LOCK") and col >= comment_start(raw):
            cls = "COMMENT"  # a '#' comment inside pyproject/requirements describes, it does not declare
        if owner is None:
            # the same paragraph as the range, at most three lines back -- the boundary attribution uses
            ctx = text[max(paragraph_start(text, m.start()), offsets[max(0, lineno - 4)]):offsets[lineno]]
            if has_upper_bound(spec) and cls in ("DOC", "COMMENT") and CONTEXT_WORDS_RE.search(ctx):
                hits.append(Hit(repo, path, lineno, spec, "AMBIGUOUS", raw.strip()))
            continue
        if cls in ("DOC", "COMMENT") and not has_upper_bound(spec):
            cls = "REQUIREMENT"
        if cls in ("DOC", "COMMENT") and any(r == repo and p == path and s in raw for (r, p, s) in EXCEPTIONS):
            cls = "EXCEPTION"
        if cls in ("DOC", "COMMENT") and extra is not None and spec == extra:
            cls = "OWN-EXTRA"
        hits.append(Hit(repo, path, lineno, spec, cls, raw.strip()))
        judged_lines.add(lineno)

    if loc == "WORKFLOW":
        for i, raw in enumerate(lines, 1):
            body = raw[:comment_start(raw)]
            if i in judged_lines or "pip install" not in body:
                continue
            # a name inside a path or a built-artifact filename (dist/juniper_ci_tools-*.whl) is a
            # local install, not an index pin; only a bare requirement token is unresolved
            if any(not (body[max(0, n.start() - 1):n.start()] == "/" or re.match(r"-(\*|\d)", body[n.end():n.end() + 2])) for n in NAME_RE.finditer(body)):
                hits.append(Hit(repo, path, i, "(none)", "UNRESOLVED", raw.strip()))
    return hits


def is_text_member(name: str) -> bool:
    base = name.rsplit("/", 1)[-1]
    return name.endswith(TEXT_SUFFIXES) or base in TEXT_BASENAMES or base.startswith("Dockerfile")


def gh(*args: str) -> bytes:
    proc = subprocess.run(["gh", *args], capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def census_repo(repo: str) -> tuple[str, list[Hit]]:
    sha = json.loads(gh("api", f"repos/{OWNER}/{repo}/commits/main"))["sha"]
    blob = gh("api", f"repos/{OWNER}/{repo}/tarball/{sha}")
    members: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not is_text_member(member.name):
                continue
            rel = member.name.split("/", 1)[1] if "/" in member.name else member.name
            handle = tar.extractfile(member)
            if handle is not None:
                members[rel] = handle.read().decode("utf-8", errors="replace")
    extra = None
    if "pyproject.toml" in members:
        m = re.search(r"juniper[-_]ci[-_]tools\s*(" + SPEC_RE.pattern + r")", members["pyproject.toml"], re.IGNORECASE)
        extra = normalise(m.group(1)) if m else None
    hits: list[Hit] = []
    for rel, text in members.items():
        if NAME_RE.search(text) or any(s in text for s in CI_TOOLS_SCRIPTS):
            hits.extend(census_text(repo, rel, text, extra))
    return sha, hits


def latest_published() -> str:
    with urllib.request.urlopen("https://pypi.org/pypi/juniper-ci-tools/json", timeout=30) as resp:
        return json.load(resp)["info"]["version"]


def verdicts(hits: list[Hit], expect: str, latest: str) -> list[str]:
    from packaging.specifiers import SpecifierSet

    expect_n = normalise(expect)
    bad: list[str] = []
    for h in hits:
        where = f"{h.repo}/{h.path}:{h.line}  {h.spec}  [{h.cls}]"
        if h.cls == "LIVE" and h.spec != expect_n:
            bad.append(where)
        elif h.cls == "UNRESOLVED":
            bad.append(where + "  (a live install this census cannot resolve)")
        elif h.cls in ("DOC", "COMMENT") and h.spec != expect_n:
            bad.append(where)
        elif h.cls == "DECLARATION" and latest not in SpecifierSet(h.spec):
            bad.append(where + f"  (does not admit the latest release, {latest})")
        elif h.cls == "LOCK" and not (h.spec.startswith("==") and h.spec[2:] in SpecifierSet(expect)):
            bad.append(where)
    return bad


def self_test() -> int:
    """Crafted cases, one per blind spot a review lane demonstrated in this script's first version."""
    cases = [
        # (path, text, expected {(line, class)} for ci-tools hits, description)
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools>=0.9.0,<0.10.0"\n', {(1, "LIVE")}, "plain live pin"),
        (".github/workflows/a.yml", '  CI_TOOLS_PIN: "juniper-ci-tools>=0.9.0,<0.10.0"\n', {(1, "LIVE")}, "hoisted env pin"),
        (".github/workflows/a.yml", "      run: pip install 'juniper_ci_tools>=0.8.0,<0.9.0'\n", {(1, "LIVE")}, "underscore spelling"),
        (".github/workflows/a.yml", '      run: pip install "Juniper-CI-Tools>=0.8.0,<0.9.0"\n', {(1, "LIVE")}, "mixed case"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools[x]>=0.8.0,<0.9.0"\n', {(1, "LIVE")}, "extras"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools >= 0.8.0, < 0.9.0"\n', {(1, "LIVE")}, "spaces around operators"),
        (".github/workflows/a.yml", "      run: pip install juniper-ci-tools\n", {(1, "UNRESOLVED")}, "unpinned live install"),
        (".github/workflows/a.yml", "#    juniper-ci-tools package (>=0.8.0,<0.9.0) via its\n", {(1, "COMMENT")}, "prose comment, same line"),
        (".github/workflows/a.yml", "#    consumed from the PyPI juniper-ci-tools\n#    package (>=0.8.0,<0.9.0) via its\n", {(2, "COMMENT")}, "prose comment, range on the next line"),
        (".github/workflows/a.yml", "#    juniper-ci-tools package via `juniper-docs-additions-check`\n#    console scripts (pinned `>=0.8.0,<0.9.0`) -- one source\n", {(2, "COMMENT")}, "nearest name is a ci-tools console script"),
        (".github/workflows/a.yml", "#    - juniper-ci-tools (PyPI >=0.8.0,<0.9.0): juniper-symbol-loss-check /\n", {(1, "COMMENT")}, "a word between name and range"),
        (".github/workflows/a.yml", '      - # pip install "juniper-ci-tools>=0.8.0,<0.9.0"\n', {(1, "COMMENT")}, "commented-out list item is not live"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools>=0.9.0,<0.10.0"  # juniper-ci-tools>=0.8.0 was the floor\n', {(1, "LIVE"), (1, "REQUIREMENT")}, "trailing comment is not live"),
        ("docs/REFERENCE.md", "Runs the shared `juniper-ci-tools` (`>=0.8.0,<0.9.0`) sequence-safety screens\n", {(1, "DOC")}, "backticked doc prose"),
        ("AGENTS.md", "> Requires `juniper-ci-tools>=0.5.1`\n", {(1, "REQUIREMENT")}, "floor-only requirement"),
        ("AGENTS.md", "`juniper-doc-tools>=0.1.0,<0.2.0` and `juniper-ci-tools`\n", set(), "another package's range"),
        ("AGENTS.md", "uses juniper-ci-tools and httpx>=0.27.0,<0.28.0\n", set(), "a non-juniper package's range after a ci-tools mention"),
        ("AGENTS.md", "juniper-ci-tools is used here.\n\nThe prior ``<0.7.0`` ceiling was wrong.\n", set(), "a paragraph break ends attribution"),
        ("docs/REFERENCE.md", "`main-verify.yml` enforces the two new `>=0.8.0,<0.9.0` screen pins still admit current.\n", {(1, "AMBIGUOUS")}, "context-only range is surfaced, not guessed"),
        ("AGENTS.md", "(see juniper-ml#319) juniper-ci-tools, then juniper-ml's tree (`>=0.8.0,<0.9.0`)\n", {(1, "DOC")}, "possessive and PR refs are transparent"),
        ("requirements.in", "juniper-ci-tools (>=0.8.0,<0.9.0)\n", {(1, "DECLARATION")}, "PEP 508 parenthesised form"),
        ("conf/requirements_ci.txt", "juniper-ci-tools==0.8.0\n", {(1, "LOCK")}, "lock pin"),
        ("tests/test_x.py", 'PIN = "juniper-ci-tools>=0.1.0,<0.2.0"\n', {(1, "FIXTURE")}, "test fixture"),
        ("notes/X.md", "juniper-ci-tools>=0.1.0,<0.2.0\n", {(1, "HISTORICAL")}, "historical record"),
        ("docs/release_notes/x.md", "juniper-ci-tools>=0.1.0,<0.2.0\n", {(1, "DOC")}, "a notes-like substring is not a notes/ segment"),
        ("Makefile", "\tpip install 'juniper-ci-tools>=0.8.0,<0.9.0'\n", {(1, "DOC")}, "Makefile is scanned"),
        (".github/workflows/a.yml", "          /tmp/v/bin/pip install --quiet dist/juniper_ci_tools-*.whl\n", set(), "a locally built wheel is not an index pin"),
        ("pyproject.toml", "#   * juniper-ci-tools — capped `<0.2.0` when its extra was added (#293)\n", {(1, "COMMENT")}, "a comment inside pyproject is not a declaration"),
        ("pyproject.toml", 'tools = ["juniper-ci-tools>=0.1.0"]\n', {(1, "DECLARATION")}, "a real declaration"),
    ]
    failed = 0
    for path, text, expected, desc in cases:
        got = {(h.line, h.cls) for h in census_text("juniper-x", path, text, None)}
        ok = got == expected
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {desc:<58} expected={sorted(expected)} got={sorted(got)}")
    if not is_text_member("repo-sha/Makefile") or not is_text_member("repo-sha/Dockerfile.test") or not is_text_member("repo-sha/requirements-cpu.lock"):
        failed += 1
        print("  FAIL is_text_member misses Makefile / Dockerfile.* / *.lock")
    lock_bad = verdicts([Hit("r", "conf/requirements_ci.txt", 1, "==0.8.0", "LOCK", "")], ">=0.9.0,<0.10.0", "0.9.0")
    lock_ok = verdicts([Hit("r", "conf/requirements_ci.txt", 1, "==0.9.0", "LOCK", "")], ">=0.9.0,<0.10.0", "0.9.0")
    decl_bad = verdicts([Hit("r", "requirements.in", 1, "<0.9.0,>=0.8.0", "DECLARATION", "")], ">=0.9.0,<0.10.0", "0.9.0")
    if not lock_bad or lock_ok or not decl_bad:
        failed += 1
        print(f"  FAIL verdicts: lock_bad={lock_bad} lock_ok={lock_ok} decl_bad={decl_bad}")
    print(f"self-test: {len(cases) + 2 - failed} passed, {failed} failed")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n", 1)[0])
    ap.add_argument("--expect", default=">=0.9.0,<0.10.0", help="the specifier every live pin should carry")
    ap.add_argument("--self-test", action="store_true", help="run the crafted-case checks and exit")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    latest = latest_published()
    all_hits: list[Hit] = []
    for repo in REPOS:
        sha, hits = census_repo(repo)
        print(f"{repo:<24} main={sha[:12]}  mentions={len(hits)}")
        all_hits.extend(hits)

    by_class = Counter(h.cls for h in all_hits)
    live = [h for h in all_hits if h.cls == "LIVE"]
    per_repo: dict[str, int] = defaultdict(int)
    for h in live:
        per_repo[h.repo] += 1
    print(f"\nlatest published juniper-ci-tools: {latest}")
    print(f"mentions by class: {dict(sorted(by_class.items()))}")
    print(f"live pins: {len(live)}  by repo: {dict(per_repo)}")
    print(f"distinct live ranges: {dict(Counter(h.spec for h in live))}   (one entry, equal to --expect, is clean)")

    bad = verdicts(all_hits, args.expect, latest)
    print(f"\n--- STALE (judged, fails the census) against {args.expect} ---")
    print("\n".join("  " + b for b in bad) if bad else "  (none)")
    ambiguous = [h for h in all_hits if h.cls == "AMBIGUOUS"]
    print("\n--- AMBIGUOUS (a range near ci-tools context the census could not attribute -- READ each) ---")
    print("\n".join(f"  {h.repo}/{h.path}:{h.line}  {h.spec}" for h in ambiguous) if ambiguous else "  (none)")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # a census that could not run is not clean
        print(f"ERROR: census could not run: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
