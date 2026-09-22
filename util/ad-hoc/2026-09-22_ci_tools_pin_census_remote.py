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

``util/ad-hoc/2026-09-11_ci_tools_pin_census.py`` reads the sibling checkouts on disk, and its
own handoff warns "pull the siblings first -- local trees lag". A worktree-isolated session
cannot pull them (the harness refuses cross-repo git), so this variant downloads each repo's
``main`` as a tarball through the GitHub API and records the commit SHA it measured.

What it looks for
-----------------
Every version specifier whose first clause is a ``0.x`` release (``>=0.9.0,<0.10.0``,
``==0.9.0``, ``~=0.9``, ``<0.2.0`` ...), plus ``juniper-ci-tools 0.4.x``-style version
mentions, that belongs to juniper-ci-tools. A specifier belongs to it when

* a name TOUCHES it (``juniper-ci-tools>=…``, ``ci-tools>=…``, ``juniper_ci_tools[x]>=…``), or
  a juniper name precedes it across spaces (``juniper-ci-tools >= …``); or
* inside a markdown table row, the column's header names it (a cell under a
  ``juniper-ci-tools`` header), else an earlier cell of the same row names it; or
* prose sets it apart from the name (``juniper-ci-tools (PyPI >=…)``, a range on the next
  comment line, ``… `juniper-docs-additions-check` console scripts (pinned `>=…`)``) and the
  NEAREST earlier juniper name in the same paragraph is juniper-ci-tools or one of its
  console scripts. A markdown heading naming the package covers the paragraphs under it.

References are transparent: a possessive (``juniper-ml's``), a PR ref (``juniper-ml#319``,
``juniper-ml PR #1909``) and a URL or path segment (``/juniper-ml/pull/869``). A range
directly after ANOTHER name (``httpx>=0.27``, ``juniper-doc-tools>=…``) belongs to that name.
If another juniper name sits between an earlier ci-tools name and the range, the range is
AMBIGUOUS rather than silently dropped. The ``0.x`` restriction keeps Python and pip specifiers
out; the census refuses to run (exit 2) once juniper-ci-tools reaches 1.0.

How each is judged
------------------
Versions are compared as SETS: a specifier is judged by which releases it admits, over every
published release plus the next patch, minor and major, so ``~=0.9.0``, ``==0.9.*`` and
``>=0.9,<0.10`` all equal ``>=0.9.0,<0.10.0``.

LIVE         a non-comment line in a workflow or composite action -- must equal --expect
             TEXTUALLY (the ecosystem's other guards parse the canonical ``>=X,<Y`` form).
             A live install naming the package with no specifier is UNRESOLVED and fails.
DOC/COMMENT  a current-state description (AGENTS.md, README, docs/, scripts, workflow and
             test comments and docstrings) -- a range must admit the same releases as
             --expect; a ceiling-only statement must name --expect's ceiling; ``==X`` and
             ``0.N.x`` must fall inside --expect. A floor-only ``>=X`` states a requirement
             (REQUIREMENT, counted) unless it excludes the latest release.
DECLARATION  pyproject.toml / setup.cfg / *.in -- must ADMIT the latest published release.
LOCK         ``==X`` in requirements*.txt / *.lock -- must fall inside --expect.
FIXTURE      a test's code (string literals under tests/) -- counted only.
HISTORICAL   a path segment notes/ prompts/ reports/ releases/ history/ legacy/, a CHANGELOG,
             util/ad-hoc/, or a timestamped snapshot (``requirements_ci_2026-09-21_08-25-31.txt``)
             -- counted only.
AMBIGUOUS    a range the attribution could not assign, in text whose section names ci-tools, a
             screen pin or sequence-safety, that does not already equal --expect. It FAILS the
             census until someone reads it and either fixes the line or records a verdict in
             ADJUDICATED below. ``docs/REFERENCE.md`` once described "the two new
             ``>=0.8.0,<0.9.0`` screen pins" without naming the package; no regex attributes that.

Exceptions (EXCEPTIONS, ADJUDICATED) are keyed by (repo, path, a substring of the line, the
specifier), each with a reason, so new drift on the same line is still judged.

Usage:  python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py [--expect '>=0.9.0,<0.10.0']
        python3 util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py --self-test
        ... --ref juniper-canopy=<sha>    census that ref instead of main (repeatable)
        ... --local juniper-ml=<path>     census a local tree instead (repeatable)
Exit:   0 when nothing judged is stale; 1 when something is (each listed), including when
        --expect itself does not admit the latest release; 2 when the census could not run --
        a failed download, an unreadable tarball, a missing ``packaging``, an invalid or
        non-0.x --expect, a 1.0 release, or zero live pins found anywhere. A census that could
        not run is not clean.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tokenize
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
OWNER_NAME_RE = re.compile(r"(?:juniper[-_])?ci[-_]tools", re.IGNORECASE)
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
JUNIPER_TOKEN_RE = re.compile(r"juniper[-_][A-Za-z0-9][A-Za-z0-9_-]*", re.IGNORECASE)

_OP = r"(?:===|==|!=|~=|>=|<=|>|<)"
_VER0 = r"0\.\d+(?:\.\d+)*(?:\.\*)?"
_VERANY = r"\d+(?:\.\d+)*(?:\.\*)?"
SPEC_RE = re.compile(_OP + r"\s*" + _VER0 + r"(?:\s*,\s*" + _OP + r"\s*" + _VERANY + r")*")
XMENTION_RE = re.compile(r"juniper[-_]ci[-_]tools[`'\"]?[ \t]+(0\.\d+)\.x\b", re.IGNORECASE)
# ``ci-tools 0.8.0 is already installed`` -- a bare release named as the one CI HAS, in the present
# tense. A bare version alone is usually history ("Added in juniper-ci-tools 0.5.1", "the ci-tools 0.7.0
# stale-dunder class") and is not a claim about what CI installs, so only an install/pin verb counts.
BARE_VERSION_RE = re.compile(
    r"(?<![\w-])(?:juniper[-_])?ci[-_]tools[`'\"]?[ \t]+(0\.\d+\.\d+)\b(?!\.x)"
    r"(?=[ \t]*(?:\n[ \t]*#?[ \t]*)?(?:is|are)[ \t]+(?:already[ \t]+|now[ \t]+)?(?:installed|pinned|in use|required))",
    re.IGNORECASE,
)
DIRECT_RE = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]\n]*\])?([ \t]*)$")
CONTEXT_WORDS_RE = re.compile(r"ci[-_]tools|screen pin|sequence[-_]safety", re.IGNORECASE)
INSTALLER_RE = re.compile(r"\bpip3?\s+install\b|\buv\s+(?:pip|tool)\s+install\b|\bpipx\s+install\b|\buvx\b")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}")
HEADING_RE = re.compile(r"^#{1,6}\s")
SNAPSHOT_RE = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")

LOOKBACK_CHARS = 240
TEXT_SUFFIXES = (".yml", ".yaml", ".md", ".rst", ".toml", ".txt", ".cfg", ".ini", ".py", ".bash", ".sh", ".json", ".lock", ".in", ".mk")
TEXT_BASENAMES = ("Makefile", "Dockerfile")
HISTORICAL_SEGMENTS = {"notes", "prompts", "reports", "releases", "history", "legacy"}

# (repo, path, substring of the line, normalised specifier) -> reason.
# A reason a reader cannot check is a suppression; the specifier keeps new drift on the line judged.
EXCEPTIONS = {
    ("juniper-ml", "util/release_train/propose.py", "minimum-pin note, and a", "<0.2.0,>=0.1.0"): "docstring listing the kinds of text the extras-table editor must NOT rewrite; the range is an example",
    ("juniper-ml", "pyproject.toml", "capped `<0.2.0` when its extra was added", "<0.2.0"): "history inside the pin-capping-rule comment: capped by #293, uncapped by #295",
    ("juniper-ml", "tests/test_ci_tools_drift.py", '#   pip install "juniper-ci-tools>=0.1.0,<0.2.0"', "<0.2.0,>=0.1.0"): "comment illustrating the shape _PIN_PATTERN matches; the range is an example",
    ("juniper-ml", "tests/test_coverage_gap_mapper_drift.py", '#   pip install "juniper-ci-tools>=0.1.0,<0.6.0"', "<0.6.0,>=0.1.0"): "comment illustrating the shape _PIN_PATTERN matches; the range is an example",
    ("juniper-ml", "tests/test_pyproject_extras.py", "capped ``<0.2.0`` when", "<0.2.0"): "docstring history: the extra was capped by #293 and uncapped by #295",
    ("juniper-cascor", "src/tests/unit/test_sequence_safety_retired.py", "a stale ceiling (e.g. ``<0.8.0``)", "<0.8.0"): "docstring example of the stale ceiling the test exists to catch",
}
# Ranges the attribution cannot assign, read by a person and judged correct as they stand.
ADJUDICATED = {
    ("juniper-ml", "docs/REFERENCE.md", "Scope history (2026-09-11)", "<0.7.0,>=0.6.0"): "dated history: cascor's two pins as they stood before cascor#646",
    ("juniper-ml", "util/release_train/propose.py", "the service-core row was stale at", "<0.4.0"): "juniper-service-core's range, in a docstring's worked example",
    ("juniper-ml", "util/release_train/propose.py", "2026-07-06 ci-tools incident", "<0.5.0"): "incident narrative inside generated PR text: the pins as they were",
    ("juniper-ml", "util/release_train/propose.py", "2026-07-06 ci-tools incident", "<0.7.0"): "incident narrative inside generated PR text: the pins as they were",
    ("juniper-deploy", ".github/workflows/ci.yml", "prior ``<0.7.0`` ceiling", "<0.7.0"): "dated 'Pin healed 2026-08-08' history note",
    ("juniper-deploy", ".github/workflows/ci.yml", "sequence-safety workflows' ``>=0.8.0,<0.9.0``", "<0.9.0,>=0.8.0"): "dated 'Pin healed 2026-08-08' history note",
}


@dataclass(frozen=True)
class Hit:
    repo: str
    path: str
    line: int
    spec: str
    cls: str  # LIVE DOC COMMENT DECLARATION LOCK FIXTURE HISTORICAL REQUIREMENT AMBIGUOUS EXCEPTION ADJUDICATED OWN-EXTRA UNRESOLVED
    text: str


def normalise(spec: str) -> str:
    return ",".join(sorted(part.replace(" ", "") for part in spec.split(",")))


def clauses(spec: str) -> list[str]:
    return [p.strip() for p in spec.split(",") if p.strip()]


def is_floor_only(spec: str) -> bool:
    """``>=X`` / ``>X`` clauses only: a requirement, not a claim about what CI installs."""
    return all(c.startswith(">") for c in clauses(spec))


def is_ceiling_only(spec: str) -> bool:
    return all(c.startswith("<") for c in clauses(spec))


def location_class(path: str) -> str:
    parts = path.split("/")
    dirs = set(parts[:-1])
    base = parts[-1]
    if path.startswith("util/ad-hoc/") or base.startswith("CHANGELOG") or dirs & HISTORICAL_SEGMENTS or SNAPSHOT_RE.search(base):
        return "HISTORICAL"
    if "tests" in dirs:
        return "TESTS"
    if path.startswith(".github/workflows/") or path.startswith(".github/actions/"):
        return "WORKFLOW"
    if re.match(r"requirements[^/]*\.(txt|lock)$", base) or base.endswith(".lock"):
        return "LOCK"
    if base in ("pyproject.toml", "setup.cfg") or base.endswith(".in"):
        return "DECLARATION"
    return "DOC"


def comment_start(line: str) -> int:
    """Index where a YAML/shell/TOML comment begins on this line, or len(line) if none."""
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


def python_doc_lines(text: str) -> set[int]:
    """Lines of a Python file that are comments or docstrings -- prose, not fixture data."""
    lines: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                lines.add(tok.start[0])
        tree = ast.parse(text)
    except (SyntaxError, tokenize.TokenError, ValueError):
        return lines
    for node in [tree, *ast.walk(tree)]:
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            lines.update(range(body[0].lineno, (body[0].end_lineno or body[0].lineno) + 1))
    return lines


_PARA_CACHE: dict[int, tuple[str, list[int]]] = {}


def paragraph_start(text: str, pos: int) -> int:
    """Start of the paragraph holding ``pos``: just after the last blank (or bare '#') line.

    Break positions are computed once per text, so an 800 KB document is not rescanned per match.
    """
    import bisect

    cached = _PARA_CACHE.get(id(text))
    if cached is None or cached[0] is not text:
        cached = (text, [m.end() for m in re.finditer(r"\n[ \t]*#?[ \t]*(?=\n)", text)])
        _PARA_CACHE.clear()
        _PARA_CACHE[id(text)] = cached
    breaks = cached[1]
    i = bisect.bisect_right(breaks, pos) - 1
    return breaks[i] + 1 if i >= 0 else 0


def _token_is_ci_tools(token: str) -> bool:
    name = token.lower().replace("_", "-")
    return bool(NAME_RE.fullmatch(token)) or name.startswith("juniper-ci-tools-") or name in CI_TOOLS_SCRIPTS


def _transparent(window: str, tok: re.Match) -> bool:
    after = window[tok.end():tok.end() + 6]
    before = window[max(0, tok.start() - 1):tok.start()]
    return (
        after.startswith("#")
        or after.startswith("'s")
        or after.startswith("’s")
        or after.startswith("/")
        or bool(re.match(r"\s+PR\s*#", after + window[tok.end() + 6:tok.end() + 10]))
        or before == "/"
    )


def lookback_owner(window: str) -> str | None:
    """'ci-tools', 'other', 'ambiguous' or None, from the nearest earlier juniper name in ``window``."""
    # a ci-tools token is never transparent: `juniper-ci-tools/pyproject.toml` still names the package
    tokens = [t for t in JUNIPER_TOKEN_RE.finditer(window) if _token_is_ci_tools(t.group(0)) or not _transparent(window, t)]
    for i in range(len(tokens) - 1, -1, -1):
        if _token_is_ci_tools(tokens[i].group(0)):
            return "ci-tools"
        earlier = any(_token_is_ci_tools(t.group(0)) for t in tokens[:i]) or bool(NAME_RE.search(window[: tokens[i].start()]))
        return "ambiguous" if earlier else "other"
    return None


def table_owner(lines: list[str], idx: int, col_char: int) -> str | None:
    """Owner of a spec in a markdown table cell: the column header, else an earlier cell of the row."""
    row = lines[idx]
    if not row.lstrip().startswith("|"):
        return None
    col = row[:col_char].count("|") - 1
    j = idx
    while j > 0 and lines[j - 1].lstrip().startswith("|"):
        j -= 1
    # j is the table's first row (the header) when the next row is the separator
    if j + 1 < len(lines) and TABLE_SEP_RE.match(lines[j + 1]) and j != idx:
        header_cells = lines[j].split("|")[1:]
        if 0 <= col < len(header_cells):
            head = header_cells[col]
            if NAME_RE.search(head):
                return "ci-tools"
            if JUNIPER_TOKEN_RE.search(head):
                return "other"
    earlier = row[:col_char]
    owner = lookback_owner(earlier)
    return owner


def md_headings(lines: list[str]) -> set[int]:
    """0-based indices of real markdown headings -- a '# ...' line inside a code fence is not one."""
    heads: set[int] = set()
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and HEADING_RE.match(line):
            heads.add(i)
    return heads


def heading_owner(lines: list[str], idx: int, heads: set[int]) -> str | None:
    """'ci-tools' when the nearest real heading names only juniper-ci-tools; otherwise unattributed.

    A heading naming ANOTHER package is weak evidence, so it never drops a range: the range falls
    through to the AMBIGUOUS check instead.
    """
    for j in range(idx - 1, -1, -1):
        if j in heads:
            if NAME_RE.search(lines[j]) and len(JUNIPER_TOKEN_RE.findall(lines[j])) == 1:
                return "ci-tools"
            return None
    return None


COMPARISON_RE = re.compile(r"\d+(?:\.\d+)+\s*$")
VARIABLE_PIN_RE = re.compile(r"\s*(?:\[[^\]]*\])?\s*(?:===|==|~=|>=|<=|!=|<|>)\s*[\"']?\$")


def owner_of(text: str, start: int, lines: list[str], lineno: int, col: int, is_md: bool, floor: int, heads: set[int]) -> str | None:
    """Who owns the specifier at ``start``. ``floor`` bounds the lookback (a comment block, a paragraph)."""
    before = text[max(0, start - LOOKBACK_CHARS):start]
    if COMPARISON_RE.search(before):
        return "other"  # ``0.5.0 <= 0.5.0`` is arithmetic in prose, not a specifier
    m = DIRECT_RE.search(before)
    if m:
        token, extras, gap = m.group(1), m.group(2), m.group(3)
        if not gap or (JUNIPER_TOKEN_RE.fullmatch(token) and not extras):
            if OWNER_NAME_RE.fullmatch(token):
                return "ci-tools"
            if not gap or JUNIPER_TOKEN_RE.fullmatch(token):
                return "other"
    if is_md and lines[lineno - 1].lstrip().startswith("|"):
        return table_owner(lines, lineno - 1, col)
    lo = max(floor, start - LOOKBACK_CHARS)
    owner = lookback_owner(text[lo:start])
    if owner is None and is_md:
        owner = heading_owner(lines, lineno - 1, heads)
    return owner


def section_context(text: str, lines: list[str], lineno: int, start: int, is_md: bool, floor: int, heads: set[int]) -> str:
    ctx = text[floor:start + 1] + lines[lineno - 1]
    if is_md:
        for j in range(lineno - 1, -1, -1):
            if j in heads:
                ctx = lines[j] + "\n" + ctx
                break
        return ctx
    return "\n".join(ctx.split("\n")[-6:])


def _keyed(table: dict, repo: str, path: str, raw: str, spec: str) -> bool:
    return any(r == repo and p == path and s in raw and sp == spec for (r, p, s, sp) in table)


def census_text(repo: str, path: str, text: str, extra: str | None) -> list[Hit]:
    hits: list[Hit] = []
    loc = location_class(path)
    is_md = path.endswith((".md", ".rst"))
    lines = text.split("\n")
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln) + 1)
    doc_lines = python_doc_lines(text) if (loc == "TESTS" and path.endswith(".py")) else set()

    def line_of(pos: int) -> int:
        lo, hi = 0, len(lines)
        while lo < hi:
            mid = (lo + hi) // 2
            if offsets[mid + 1] <= pos:
                lo = mid + 1
            else:
                hi = mid
        return lo + 1

    def base_class(lineno: int, col: int) -> str:
        raw = lines[lineno - 1]
        if loc == "WORKFLOW":
            return "LIVE" if col < comment_start(raw) else "COMMENT"
        if loc in ("DECLARATION", "LOCK"):
            return "COMMENT" if col >= comment_start(raw) else loc
        if loc == "TESTS":
            if path.endswith((".md", ".rst")) or lineno in doc_lines:
                return "COMMENT"
            return "FIXTURE"
        return loc

    heads = md_headings(lines) if is_md else set()

    def is_comment_line(n: int) -> bool:
        if n < 1 or n > len(lines):
            return False
        if loc == "TESTS" and path.endswith(".py"):
            return n in doc_lines
        stripped = lines[n - 1].lstrip()
        return stripped.startswith("#") or stripped.startswith("- #")

    fences = [i for i, ln in enumerate(lines) if ln.lstrip().startswith(("```", "~~~"))] if is_md else []

    def floor_for(lineno: int, start: int, col: int) -> int:
        """Lookback floor: the paragraph, narrowed to the comment block when the match is in one.

        In markdown a code fence or a heading also bounds it: a name inside a fenced block, or in the
        previous section, does not own a range in this one (the heading itself is read separately).
        """
        floor = paragraph_start(text, start)
        raw = lines[lineno - 1]
        if is_md:
            bounds = [i for i in fences if i < lineno - 1] + [i for i in heads if i < lineno - 1]
            if bounds:
                floor = max(floor, offsets[max(bounds) + 1])
            return floor
        if is_comment_line(lineno) or col >= comment_start(raw):
            n = lineno
            while n > 1 and is_comment_line(n - 1):
                n -= 1
            floor = max(floor, offsets[n - 1])
        return floor

    judged_lines: set[int] = set()
    found: list[tuple[int, int, str, str | None]] = []
    for m in SPEC_RE.finditer(text):
        lineno = line_of(m.start())
        col = m.start() - offsets[lineno - 1]
        floor = floor_for(lineno, m.start(), col)
        found.append((lineno, m.start(), normalise(m.group(0)), owner_of(text, m.start(), lines, lineno, col, is_md, floor, heads)))
    for m in XMENTION_RE.finditer(text):
        found.append((line_of(m.start()), m.start(), f"=={m.group(1)}.*", "ci-tools"))
    for m in BARE_VERSION_RE.finditer(text):
        found.append((line_of(m.start()), m.start(), f"=={m.group(1)}", "ci-tools"))

    for lineno, start, spec, owner in found:
        raw = lines[lineno - 1]
        col = start - offsets[lineno - 1]
        if owner == "other":
            continue
        cls = base_class(lineno, col)
        if owner in (None, "ambiguous"):
            floor = floor_for(lineno, start, col)
            if cls in ("DOC", "COMMENT") and not is_floor_only(spec) and CONTEXT_WORDS_RE.search(section_context(text, lines, lineno, start, is_md, floor, heads)):
                cls = "ADJUDICATED" if _keyed(ADJUDICATED, repo, path, raw, spec) else "AMBIGUOUS"
                hits.append(Hit(repo, path, lineno, spec, cls, raw.strip()))
            continue
        if cls in ("DOC", "COMMENT"):
            if is_floor_only(spec):
                cls = "REQUIREMENT"
            elif _keyed(EXCEPTIONS, repo, path, raw, spec):
                cls = "EXCEPTION"
            elif extra is not None and spec == extra:
                cls = "OWN-EXTRA"
        hits.append(Hit(repo, path, lineno, spec, cls, raw.strip()))
        judged_lines.add(lineno)

    if loc == "WORKFLOW":
        logical: list[tuple[int, str]] = []
        buf, first = "", 0
        for i, raw in enumerate(lines, 1):
            body = raw[:comment_start(raw)]
            if not buf:
                first = i
            if body.rstrip().endswith("\\"):
                buf += body.rstrip()[:-1] + " "
                continue
            logical.append((first, buf + body))
            buf = ""
        for first, body in logical:
            if not INSTALLER_RE.search(body):
                continue
            span = range(first, first + body.count("\n") + 1)
            if any(n in judged_lines for n in span) or SPEC_RE.search(body):
                continue
            for n in NAME_RE.finditer(body):
                in_path = body[max(0, n.start() - 1):n.start()] == "/" or re.match(r"-(\*|\d)", body[n.end():n.end() + 2])
                variable_pin = VARIABLE_PIN_RE.match(body, n.end())  # "juniper-ci-tools==${version}"
                if not in_path and not variable_pin:
                    hits.append(Hit(repo, path, first, "(none)", "UNRESOLVED", body.strip()[:160]))
                    break
    return hits


def is_text_member(name: str) -> bool:
    base = name.rsplit("/", 1)[-1]
    return name.endswith(TEXT_SUFFIXES) or base in TEXT_BASENAMES or base.startswith("Dockerfile")


def gh(*args: str) -> bytes:
    proc = subprocess.run(["gh", *args], capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def load_remote(repo: str, ref: str) -> tuple[str, dict[str, str]]:
    sha = json.loads(gh("api", f"repos/{OWNER}/{repo}/commits/{ref}"))["sha"]
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
    return sha, members


def load_local(root: str) -> tuple[str, dict[str, str]]:
    members: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d == ".github" or not (d.startswith(".") or d in ("__pycache__", "node_modules", "venv"))]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            if is_text_member(rel):
                with open(full, encoding="utf-8", errors="replace") as fh:
                    members[rel] = fh.read()
    return f"local:{root}", members


def census_members(repo: str, members: dict[str, str]) -> list[Hit]:
    extra = None
    if "pyproject.toml" in members:
        m = re.search(r"juniper[-_]ci[-_]tools\s*(" + SPEC_RE.pattern + r")", members["pyproject.toml"], re.IGNORECASE)
        extra = normalise(m.group(1)) if m else None
    hits: list[Hit] = []
    for rel, text in members.items():
        if NAME_RE.search(text) or any(s in text for s in CI_TOOLS_SCRIPTS) or re.search(r"\bci[-_]tools\b", text, re.IGNORECASE):
            hits.extend(census_text(repo, rel, text, extra))
    return hits


def published_versions() -> tuple[str, list[str]]:
    with urllib.request.urlopen("https://pypi.org/pypi/juniper-ci-tools/json", timeout=30) as resp:
        data = json.load(resp)
    return data["info"]["version"], sorted(data["releases"])


def candidate_set(latest: str, released: list[str]) -> list[str]:
    from packaging.version import Version

    v = Version(latest)
    extra = [f"{v.major}.{v.minor}.{v.micro + 1}", f"{v.major}.{v.minor + 1}.0", f"{v.major}.{v.minor + 1}.1", f"{v.major + 1}.0.0"]
    return sorted(set(released) | set(extra), key=Version)


def verdicts(hits: list[Hit], expect: str, latest: str, candidates: list[str]) -> list[str]:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    expect_set = SpecifierSet(expect)
    admitted_expect = {c for c in candidates if Version(c) in expect_set}
    ceiling = normalise(",".join(c for c in clauses(expect) if c.startswith("<")))

    def admits_same(spec: str) -> bool:
        s = SpecifierSet(spec)
        if is_ceiling_only(spec):
            return normalise(spec) == ceiling
        if all(c.startswith("==") for c in clauses(spec)):
            return any(Version(c) in s for c in admitted_expect) and {c for c in candidates if Version(c) in s} <= admitted_expect
        return {c for c in candidates if Version(c) in s} == admitted_expect

    bad: list[str] = []
    for h in hits:
        where = f"{h.repo}/{h.path}:{h.line}  {h.spec}  [{h.cls}]"
        if h.cls == "LIVE" and h.spec != normalise(expect):
            bad.append(where)
        elif h.cls == "UNRESOLVED":
            bad.append(where + "  (a live install this census cannot resolve)")
        elif h.cls in ("DOC", "COMMENT") and not admits_same(h.spec):
            bad.append(where)
        elif h.cls == "REQUIREMENT" and Version(latest) not in SpecifierSet(h.spec):
            bad.append(where + f"  (a floor above the latest release, {latest})")
        elif h.cls == "AMBIGUOUS" and not admits_same(h.spec):
            bad.append(where + "  (read it: fix the line, or record a verdict in ADJUDICATED)")
        elif h.cls == "DECLARATION" and Version(latest) not in SpecifierSet(h.spec):
            bad.append(where + f"  (does not admit the latest release, {latest})")
        elif h.cls == "LOCK" and not (h.spec.startswith("==") and Version(h.spec[2:]) in expect_set):
            bad.append(where)
    return bad


def validate_expect(expect: str) -> None:
    from packaging.specifiers import InvalidSpecifier, SpecifierSet

    try:
        SpecifierSet(expect)
    except InvalidSpecifier as exc:
        raise ValueError(f"--expect {expect!r} is not a valid specifier: {exc}") from exc
    if not re.fullmatch(SPEC_RE.pattern, expect.strip()):
        raise ValueError(f"--expect {expect!r} must be a 0.x range; this census does not read 1.x specifiers yet")


def self_test() -> int:
    """Crafted cases: one per blind spot a review lane demonstrated, plus the verdict branches."""
    cases = [
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools>=0.9.0,<0.10.0"\n', {(1, "LIVE")}, "plain live pin"),
        (".github/workflows/a.yml", '  CI_TOOLS_PIN: "juniper-ci-tools>=0.9.0,<0.10.0"\n', {(1, "LIVE")}, "hoisted env pin"),
        (".github/workflows/a.yml", "      run: pip install 'juniper_ci_tools>=0.8.0,<0.9.0'\n", {(1, "LIVE")}, "underscore spelling"),
        (".github/workflows/a.yml", '      run: pip install "Juniper-CI-Tools>=0.8.0,<0.9.0"\n', {(1, "LIVE")}, "mixed case"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools[x]>=0.8.0,<0.9.0"\n', {(1, "LIVE")}, "extras"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools >= 0.8.0, < 0.9.0"\n', {(1, "LIVE")}, "spaces around operators"),
        (".github/workflows/a.yml", "      run: pip install juniper-ci-tools\n", {(1, "UNRESOLVED")}, "unpinned live install"),
        (".github/workflows/a.yml", "      run: pip3 install juniper-ci-tools\n", {(1, "UNRESOLVED")}, "pip3 unpinned"),
        (".github/workflows/a.yml", "      run: |\n        pip install \\\n          juniper-ci-tools\n", {(2, "UNRESOLVED")}, "backslash continuation unpinned"),
        (".github/workflows/a.yml", "      run: uv tool install juniper-ci-tools\n", {(1, "UNRESOLVED")}, "uv tool install unpinned"),
        (".github/workflows/a.yml", "          /tmp/v/bin/pip install --quiet dist/juniper_ci_tools-*.whl\n", set(), "a locally built wheel is not an index pin"),
        (".github/workflows/a.yml", "#    juniper-ci-tools package (>=0.8.0,<0.9.0) via its\n", {(1, "COMMENT")}, "prose comment, same line"),
        (".github/workflows/a.yml", "#    consumed from the PyPI juniper-ci-tools\n#    package (>=0.8.0,<0.9.0) via its\n", {(2, "COMMENT")}, "prose comment, range on the next line"),
        (".github/workflows/a.yml", "#    juniper-ci-tools package via `juniper-docs-additions-check`\n#    console scripts (pinned `>=0.8.0,<0.9.0`) -- one source\n", {(2, "COMMENT")}, "nearest name is a ci-tools console script"),
        (".github/workflows/a.yml", "#    - juniper-ci-tools (PyPI >=0.8.0,<0.9.0): juniper-symbol-loss-check /\n", {(1, "COMMENT")}, "a word between name and range"),
        (".github/workflows/a.yml", '      run: pip install "juniper-ci-tools>=0.9.0,<0.10.0"  # juniper-ci-tools>=0.8.0 was the floor\n', {(1, "LIVE"), (1, "REQUIREMENT")}, "trailing comment is not live"),
        ("docs/REFERENCE.md", "Runs the shared `juniper-ci-tools` (`>=0.8.0,<0.9.0`) sequence-safety screens\n", {(1, "DOC")}, "backticked doc prose"),
        ("AGENTS.md", "> Requires `juniper-ci-tools>=0.5.1`\n", {(1, "REQUIREMENT")}, "floor-only requirement"),
        ("AGENTS.md", "`juniper-doc-tools>=0.1.0,<0.2.0` and `juniper-ci-tools`\n", set(), "another package's range"),
        ("AGENTS.md", "uses juniper-ci-tools and httpx>=0.27.0,<0.28.0\n", set(), "a non-juniper package's range after a ci-tools mention"),
        ("AGENTS.md", "juniper-ci-tools is used here.\n\nThe prior ``<0.7.0`` ceiling was wrong.\n", set(), "a paragraph break ends attribution"),
        ("docs/REFERENCE.md", "`main-verify.yml` enforces the two new `>=0.8.0,<0.9.0` screen pins still admit current.\n", {(1, "AMBIGUOUS")}, "context-only range is surfaced, not guessed"),
        ("AGENTS.md", "(see juniper-ml#319) juniper-ci-tools, then juniper-ml's tree (`>=0.8.0,<0.9.0`)\n", {(1, "DOC")}, "possessive and PR refs are transparent"),
        ("AGENTS.md", "juniper-ci-tools, landed in [#869](https://github.com/pcalnon/juniper-ml/pull/869) (`>=0.8.0,<0.9.0`)\n", {(1, "DOC")}, "a URL segment is transparent"),
        ("AGENTS.md", "juniper-ci-tools, see juniper-ml PR #1909 (`>=0.8.0,<0.9.0`)\n", {(1, "DOC")}, "'PR #' after a repo name is transparent"),
        ("AGENTS.md", "juniper-ci-tools and juniper-cascor (`>=0.8.0,<0.9.0`) screens\n", {(1, "AMBIGUOUS")}, "another juniper name in between is ambiguous, not dropped"),
        ("AGENTS.md", "CI installs ci-tools>=0.8.0,<0.9.0 here\n", {(1, "DOC")}, "short-form ci-tools name"),
        ("docs/X.md", "### juniper-ci-tools\n\nThe CI pin is >=0.8.0,<0.9.0 today.\n", {(3, "DOC")}, "a heading naming the package covers its section"),
        ("docs/X.md", "| repo | juniper-ci-tools | juniper-doc-tools |\n|---|---|---|\n| 0.8.x | >=0.8.0,<0.9.0 | >=0.1.0,<0.2.0 |\n", {(3, "DOC")}, "table cell attributed by its column header"),
        ("docs/X.md", "|  | `juniper-config-tools` | `>=0.1.0,<0.2.0` |\n", set(), "table row: an earlier cell names another package"),
        ("docs/QUICK_START.md", "juniper-ci-tools         0.4.x\n", {(1, "DOC")}, "a 0.N.x version mention is judged"),
        ("requirements.in", "juniper-ci-tools (>=0.8.0,<0.9.0)\n", {(1, "DECLARATION")}, "PEP 508 parenthesised form"),
        ("pyproject.toml", "#   * juniper-ci-tools — capped `<0.2.0` when its extra was added (#293)\n", {(1, "COMMENT")}, "a comment inside pyproject is not a declaration"),
        ("pyproject.toml", 'tools = ["juniper-ci-tools>=0.1.0"]\n', {(1, "DECLARATION")}, "a real declaration"),
        ("conf/requirements_ci.txt", "juniper-ci-tools==0.8.0\n", {(1, "LOCK")}, "lock pin"),
        ("conf/requirements_ci_2026-09-21_08-25-31.txt", "juniper-ci-tools==0.8.0\n", {(1, "HISTORICAL")}, "a timestamped lock snapshot is history"),
        ("tests/test_x.py", 'PIN = "juniper-ci-tools>=0.1.0,<0.2.0"\n', {(1, "FIXTURE")}, "test fixture data"),
        ("tests/test_x.py", '"""Operator runbook:\n\n    pip install "juniper-ci-tools>=0.6.0,<0.7.0"\n"""\n', {(3, "COMMENT")}, "a test DOCSTRING is prose, judged"),
        ("tests/README.md", "Install `juniper-ci-tools>=0.6.0,<0.7.0` first.\n", {(1, "COMMENT")}, "a README under tests/ is prose, judged"),
        ("notes/X.md", "juniper-ci-tools>=0.1.0,<0.2.0\n", {(1, "HISTORICAL")}, "historical record"),
        ("docs/release_notes/x.md", "juniper-ci-tools>=0.1.0,<0.2.0\n", {(1, "DOC")}, "a notes-like substring is not a notes/ segment"),
        ("Makefile", "\tpip install 'juniper-ci-tools>=0.8.0,<0.9.0'\n", {(1, "DOC")}, "Makefile is scanned"),
        ("AGENTS.md", "requires juniper-ci-tools>=0.8.0,<1.0 for the screens\n", {(1, "DOC")}, "a non-0.x second clause is kept"),
        ("docs/X.md", "```bash\n# and run under the dedicated `CI -- juniper-doc-tools` workflow.\n```\n`main-verify.yml` enforces the two new `>=0.8.0,<0.9.0` screen pins\n", {(4, "AMBIGUOUS")}, "a '# ...' line inside a code fence is not a heading"),
        ("docs/X.md", "### juniper-doc-tools\n\nThe ci-tools screen pins are `>=0.8.0,<0.9.0` here.\n", {(3, "AMBIGUOUS")}, "a heading naming another package never drops a range"),
        (".github/workflows/a.yml", '            if pip install \\\n              "juniper-ci-tools==${version}" ; then\n', set(), "a variable pin is not unresolved"),
        ("tests/test_y.py", 'f("juniper-ci-tools>=0.1.0")\n# the other extra is capped <0.5.0 here\n', {(1, "FIXTURE")}, "a comment block does not inherit a code line's name"),
        ("AGENTS.md", "juniper-ci-tools ceilings: 0.5.0 <= 0.5.0 satisfies, 0.5.1 escapes\n", set(), "arithmetic in prose is not a specifier"),
        (".github/workflows/a.yml", "      # gate above. ci-tools 0.8.0\n      # is already installed by the preflight step.\n", {(1, "COMMENT")}, "a bare 'ci-tools 0.8.0' is judged"),
        ("AGENTS.md", "juniper-ci-tools 0.9.0 is installed by CI today.\n", {(1, "DOC")}, "a present-tense install claim inside --expect is a mention too"),
        ("docs/REFERENCE.md", "  - Added in `juniper-ci-tools` 0.5.1 after #580 dropped the entry point; the ci-tools 0.7.0 stale-dunder class.\n", set(), "a bare version naming history is not an install claim"),
    ]
    failed = 0
    for path, text, expected, desc in cases:
        got = {(h.line, h.cls) for h in census_text("juniper-x", path, text, None)}
        ok = got == expected
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {desc:<64} expected={sorted(expected)} got={sorted(got)}")

    # Verdict branches: each must flag the stale form AND pass the current one.
    cand = ["0.1.0", "0.6.0", "0.8.0", "0.9.0", "0.9.1", "0.10.0", "0.10.1", "1.0.0"]
    exp = ">=0.9.0,<0.10.0"
    verdict_cases = [
        ("LIVE", "<0.9.0,>=0.8.0", True), ("LIVE", "<0.10.0,>=0.9.0", False),
        ("DOC", "<0.9.0,>=0.8.0", True), ("DOC", "~=0.9.0", False), ("DOC", "==0.9.*", False), ("DOC", "<0.10,>=0.9", False),
        ("DOC", "<0.2.0", True), ("DOC", "<0.10.0", False), ("DOC", "==0.9.0", False), ("DOC", "==0.4.*", True), ("DOC", "!=0.9.0,>=0.8.0", True),
        ("COMMENT", "==0.8.0", True), ("COMMENT", "==0.9.1", False),
        ("COMMENT", "<0.9.0,>=0.8.0", True), ("AMBIGUOUS", "<0.9.0,>=0.8.0", True), ("AMBIGUOUS", "<0.10.0,>=0.9.0", False),
        ("REQUIREMENT", ">=0.5.1", False), ("REQUIREMENT", ">=0.10.0", True),
        ("DECLARATION", "<0.9.0,>=0.8.0", True), ("DECLARATION", ">=0.1.0", False),
        ("LOCK", "==0.8.0", True), ("LOCK", "==0.9.0", False),
        ("EXCEPTION", "<0.2.0,>=0.1.0", False), ("ADJUDICATED", "<0.7.0,>=0.6.0", False), ("OWN-EXTRA", ">=0.1.0", False),
        ("UNRESOLVED", "(none)", True), ("FIXTURE", "<0.2.0,>=0.1.0", False), ("HISTORICAL", "<0.2.0,>=0.1.0", False),
    ]
    for cls, spec, should_flag in verdict_cases:
        flagged = bool(verdicts([Hit("r", "p", 1, spec, cls, "")], exp, "0.9.0", cand))
        ok = flagged == should_flag
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} verdict {cls:<12} {spec:<18} flag={flagged} expected={should_flag}")

    # Exceptions are keyed by the specifier: the SAME substring with a different range is still judged.
    line = "    ``\\\\`juniper-observability>=0.2.0\\\\``` minimum-pin note, and a ``\\\\`juniper-ci-tools>=0.1.0,<0.2.0\\\\``"
    same = census_text("juniper-ml", "util/release_train/propose.py", line + "\n", None)
    other = census_text("juniper-ml", "util/release_train/propose.py", line.replace("<0.2.0", "<0.3.0") + "\n", None)
    key_ok = [h.cls for h in same] == ["EXCEPTION"] and [h.cls for h in other] == ["DOC"]
    failed += not key_ok
    print(f"  {'ok  ' if key_ok else 'FAIL'} an exception does not cover a different range on the same line")

    # --expect is validated before any download, and a lagging --expect fails the census.
    try:
        validate_expect("garbage")
        bad_expect = False
    except ValueError:
        bad_expect = True
    lag = latest_lag_message(">=0.9.0,<0.10.0", "0.10.0")
    no_lag = latest_lag_message(">=0.9.0,<0.10.0", "0.9.0")
    guard_ok = bad_expect and bool(lag) and not no_lag
    failed += not guard_ok
    print(f"  {'ok  ' if guard_ok else 'FAIL'} --expect validated up front, and a range that excludes the latest release fails")

    for probe in ("repo-sha/Makefile", "repo-sha/Dockerfile.test", "repo-sha/requirements-cpu.lock"):
        if not is_text_member(probe):
            failed += 1
            print(f"  FAIL is_text_member misses {probe}")
    total = len(cases) + len(verdict_cases) + 2
    print(f"self-test: {total - failed} passed, {failed} failed")
    return 1 if failed else 0


def latest_lag_message(expect: str, latest: str) -> str | None:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    if Version(latest) not in SpecifierSet(expect):
        return f"--expect {expect} does not admit the latest published release, {latest}: every pin that equals it LAGS (the 2026-07-06 incident class)"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n", 1)[0])
    ap.add_argument("--expect", default=">=0.9.0,<0.10.0", help="the specifier every live pin should carry")
    ap.add_argument("--self-test", action="store_true", help="run the crafted-case checks and exit")
    ap.add_argument("--ref", action="append", default=[], metavar="REPO=REF", help="census REF instead of main for REPO")
    ap.add_argument("--local", action="append", default=[], metavar="REPO=PATH", help="census a local tree for REPO")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    validate_expect(args.expect)
    refs = dict(item.split("=", 1) for item in args.ref)
    locals_ = dict(item.split("=", 1) for item in args.local)
    latest, released = published_versions()
    if not latest.startswith("0."):
        raise ValueError(f"juniper-ci-tools {latest} is not 0.x; widen _VER0 before trusting this census")
    candidates = candidate_set(latest, released)

    all_hits: list[Hit] = []
    for repo in REPOS:
        if repo in locals_:
            sha, members = load_local(locals_[repo])
        else:
            sha, members = load_remote(repo, refs.get(repo, "main"))
        if not members:
            raise RuntimeError(f"{repo}: no text files read from {sha} -- nothing was censused")
        hits = census_members(repo, members)
        live = sum(1 for h in hits if h.cls == "LIVE")
        warn = "   WARNING: no live pins" if live == 0 else ""
        print(f"{repo:<24} {sha[:40]:<40}  mentions={len(hits)}  live={live}{warn}")
        all_hits.extend(hits)

    by_class = Counter(h.cls for h in all_hits)
    live = [h for h in all_hits if h.cls == "LIVE"]
    if not live:
        raise RuntimeError("zero live pins across every repo -- the census read nothing it could judge")
    per_repo: dict[str, int] = defaultdict(int)
    for h in live:
        per_repo[h.repo] += 1
    print(f"\nlatest published juniper-ci-tools: {latest}")
    print(f"mentions by class: {dict(sorted(by_class.items()))}")
    print(f"live pins: {len(live)}  by repo: {dict(per_repo)}")
    print(f"distinct live ranges: {dict(Counter(h.spec for h in live))}")

    bad = verdicts(all_hits, args.expect, latest, candidates)
    lag = latest_lag_message(args.expect, latest)
    if lag:
        bad.insert(0, lag)
    print(f"\n--- STALE (fails the census) against {args.expect} ---")
    print("\n".join("  " + b for b in bad) if bad else "  (none)")
    # An AMBIGUOUS range that admits the same releases as --expect passes, but its owner is a
    # guess. List it, so "passes" is never mistaken for "was read".
    failing = {b.split("  (")[0] for b in bad}
    unread = [h for h in all_hits if h.cls == "AMBIGUOUS" and f"{h.repo}/{h.path}:{h.line}  {h.spec}  [{h.cls}]" not in failing]
    if unread:
        print(f"\n--- AMBIGUOUS, matching {args.expect}: passes, but the owner is unproven -- read each ---")
        print("\n".join(f"  {h.repo}/{h.path}:{h.line}  {h.spec}" for h in unread))
    adjudicated = [h for h in all_hits if h.cls == "ADJUDICATED"]
    print(f"\n({len(adjudicated)} adjudicated ranges not listed; see ADJUDICATED in this script for each verdict)")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # a census that could not run is not clean
        print(f"ERROR: census could not run: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2)
