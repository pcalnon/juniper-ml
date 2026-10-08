"""Docs deletion-magnitude screen -- BASE vs HEAD markdown (sequence-safety gate G2 / G3).

Library implementation behind the ``juniper-docs-additions-check`` console script
(the thin argparse wrapper is :mod:`juniper_ci_tools.cli_docs_additions_check`).
Productionized (deletion-magnitude only, not the full LOST-IN-MERGE reconstruction)
from the 2026-07-28 Cursor-fleet docs census (Proposal P2 S2; juniper-ml
``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md``) and
migrated into ``juniper-ci-tools`` as the single, PyPI-distributed source of truth
(sequence-safety rollout plan
``notes/JUNIPER_2026-08-07_JUNIPER-ECOSYSTEM_SEQUENCE-SAFETY-ROLLOUT-PLAN.md`` Wave 0).

The flood's docs class (a *net section deletion*) was one no existing check could see:
the doc-links validator only catches dangling anchors, and markdownlint excludes
``notes/`` + ``docs/``. So a merge that dropped a whole runbook section stayed green.

A bare "any ``-`` hunk fails" rule is too blunt -- the UPDATE-target docs
(``REFERENCE.md``, the runbooks, the cheatsheet) take legitimate line *replacements* on
nearly every edit, so it would paint honest docs PRs red or train a reflex
``docs-rewrite`` waiver. Instead a **magnitude-gated** rule:

  * FAIL on a deleted Markdown **heading** line (a ``-`` hunk whose content matches
    ``^\\s{0,3}#{1,6}\\s``) UNLESS the same hunk also adds a heading (a retitle -> WARN).
    A line inside a fenced code block is never a heading, on either side: a ``# comment``
    in a ```` ```bash ```` block matches the pattern, but CommonMark renders it as code,
    and before this was fence-aware five of juniper-cascor#704's six findings were such
    comments (:func:`fenced_lines` builds the map from the BASE / HEAD file contents).
  * FAIL on a run of **>= N consecutive deleted lines with no adjacent addition**
    (``added == 0 and deleted >= min_run``; default N = 5) -- the net-section-removal
    signature.
  * WARN (annotate, not fail) on smaller deletions and small in-place swaps (a few
    deleted lines bracketed by additions -- a normal edit).

Blind spot (stated honestly, mirrors the symbol screen's WEAKENED note). A *lopsided
swap* that deletes a large block but adds a line or two in the same hunk evades the
pure-run rule (added > 0). The heading-deletion rule usually still catches it (sections
carry headings), but a section-body gut that removes no heading and adds one filler line
can slip to WARN. That residue is for human review, not this magnitude screen.

Escape hatch. A ``Allow-Docs-Rewrite: <path>[, ...]`` trailer in any commit of the
BASE..HEAD range waives the enumerated files (``*`` waives all docs in the diff); it
travels in git history so it works for both the per-PR and the post-merge gate.

Scope. By default (no ``scope``) the universal docs cluster is used: ``AGENTS.md`` (and
its ``CLAUDE.md`` symlink), ``docs/**/*.md``, and ``notes/**/*.md``. A caller may pass
``scope`` globs (from the CLI ``--scope`` flag) to screen a different markdown surface;
a path is then in scope iff it matches any glob AND ends ``.md``. An explicit ``files``
list bypasses the scope filter (any ``.md`` path).

Exit codes (surfaced by the CLI): 0 = clean (no unwaived FAIL), 1 = >= 1 unwaived FAIL,
2 = usage / invocation error. WARN / WAIVED never fail.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_MIN_RUN = 5  # >= this many consecutive deleted lines (no adjacent add) -> FAIL

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_HUNK_RE = re.compile(r"^@@ ")
# ``@@ -<old_start>[,<old_len>] +<new_start>[,<new_len>] @@`` -- only the starts are needed.
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
# A CommonMark fence: >= 3 backticks or tildes, indented at most 3 spaces, then the info string.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def in_docs_scope(path: str) -> bool:
    """AGENTS.md (+ its CLAUDE.md symlink), docs/**/*.md, notes/**/*.md."""
    if path in ("AGENTS.md", "CLAUDE.md"):
        return True
    if path.endswith(".md") and (path.startswith("docs/") or path.startswith("notes/")):
        return True
    return False


# ---- scope globs (--scope override; POSIX path globs, 3.11-floor safe) ------


def _glob_to_regex(glob: str) -> str:
    """Translate a POSIX path glob into a regex source (used with ``re.fullmatch``).

    Explicit ``**`` recursion, so it does not depend on ``PurePath.full_match`` (3.13+,
    unavailable on the ci-tools 3.11 floor):

      * ``**/`` matches zero or more whole path segments, so ``docs/**/*.md`` matches BOTH
        ``docs/a.md`` and ``docs/sub/a.md``. A trailing / embedded ``**`` matches anything.
      * ``*`` matches within a single segment (any run of non-``/`` characters).
      * ``?`` matches a single non-``/`` character. Every other char is literal.
    """
    i, n = 0, len(glob)
    out: list[str] = []
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                i += 2
                if i < n and glob[i] == "/":
                    out.append("(?:[^/]+/)*")  # **/ -> zero or more whole segments
                    i += 1
                else:
                    out.append(".*")  # trailing / embedded ** -> anything
            else:
                out.append("[^/]*")  # * -> within a single segment
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def _match_scope(path: str, globs: list[str]) -> bool:
    """True iff ``path`` matches any glob in ``globs`` (POSIX path-glob semantics)."""
    return any(re.fullmatch(_glob_to_regex(g), path) is not None for g in globs)


# ---- git helpers (standalone so the module needs no cross-import) ----------


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def resolve_ref(root: str, ref: str) -> Optional[str]:
    cp = _git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    out = cp.stdout.strip()
    return out if cp.returncode == 0 and out else None


def changed_files(root: str, base: str, head: str) -> list[str]:
    cp = _git(root, "diff", "--name-only", f"{base}...{head}")
    return [ln for ln in cp.stdout.splitlines() if ln]


def file_diff(root: str, base: str, head: str, path: str) -> str:
    """Unified=0 base->head diff for one file (minimal, tight hunks)."""
    return _git(root, "diff", "--unified=0", "--no-color", base, head, "--", path).stdout


def range_messages(root: str, base: str, head: str) -> str:
    return _git(root, "log", "--format=%B", f"{base}..{head}").stdout


def file_text(root: str, ref: str, path: str) -> Optional[str]:
    """The file's content at ``ref``, or None when it does not exist there (added / deleted)."""
    cp = _git(root, "show", f"{ref}:{path}")
    return cp.stdout if cp.returncode == 0 else None


def fenced_lines(text: str) -> set[int]:
    """1-based line numbers inside fenced code blocks, the fence lines themselves included.

    CommonMark's rules, which is what decides whether a ``#`` line renders as a heading:
    an opening fence is a run of >= 3 backticks or tildes indented at most 3 spaces (a
    backtick fence's info string may not itself contain a backtick); the block closes on a
    line of the SAME character, at least as long as the opening run, indented at most 3
    spaces, with nothing after it but whitespace; an unclosed fence runs to the end of the
    document, as it renders. A longer outer fence can therefore quote a shorter inner one.
    """
    inside: set[int] = set()
    opening: Optional[str] = None
    # split("\n"), not splitlines(): git numbers lines by "\n" alone, and splitlines() also
    # breaks on \f, \v, \x1c-\x1e, \x85,   and  , which would shift every later line.
    for number, line in enumerate(text.split("\n"), start=1):
        match = _FENCE_RE.match(line)
        if opening is None:
            if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
                opening = match.group(1)
                inside.add(number)
            continue
        inside.add(number)
        if match and match.group(1)[0] == opening[0] and len(match.group(1)) >= len(opening) and not match.group(2).strip():
            opening = None
    return inside


# ---- hunk parsing ----------------------------------------------------------


@dataclass
class Hunk:
    deleted: list[str] = field(default_factory=list)  # content of '-' lines
    added: list[str] = field(default_factory=list)  # content of '+' lines
    # 1-based line of the first '-' line in the BASE file / first '+' line in the HEAD file,
    # from the hunk header; 0 = unknown (a hand-built Hunk), which disables the fence check.
    old_start: int = 0
    new_start: int = 0


def parse_hunks(diff_text: str) -> list[Hunk]:
    """Split a unified diff into hunks, collecting deleted / added line contents.

    With ``--unified=0`` each hunk's deleted lines are contiguous in the old file, so a
    hunk with ``added == 0`` is a run of that many consecutive deletions with no
    adjacent addition -- exactly the P2 S2 magnitude signal.
    """
    hunks: list[Hunk] = []
    cur: Optional[Hunk] = None
    for line in diff_text.splitlines():
        if _HUNK_RE.match(line):
            header = _HUNK_HEADER_RE.match(line)
            cur = Hunk(old_start=int(header.group(1)), new_start=int(header.group(2))) if header else Hunk()
            hunks.append(cur)
            continue
        if cur is None:
            continue  # pre-hunk file header (diff --git / index / --- / +++)
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("-"):
            cur.deleted.append(line[1:])
        elif line.startswith("+"):
            cur.added.append(line[1:])
    return hunks


# ---- classification --------------------------------------------------------


@dataclass
class Finding:
    path: str
    reason: str  # heading-deletion | deletion-run | small-deletion
    severity: str  # FAIL | WARN | WAIVED
    detail: dict = field(default_factory=dict)


def _headings(lines: list[str], start: int, fenced: Optional[set[int]]) -> list[str]:
    """The lines that render as headings: they match the pattern AND sit outside a code fence.

    ``start`` is the file line of ``lines[0]``; with ``--unified=0`` a hunk's '-' (and '+')
    lines are contiguous, so ``lines[i]`` is file line ``start + i``. Without a fence map or
    a known start, every pattern match counts (the pre-fence behaviour).
    """
    if not fenced or start <= 0:
        return [ln for ln in lines if _HEADING_RE.match(ln)]
    return [ln for i, ln in enumerate(lines) if _HEADING_RE.match(ln) and (start + i) not in fenced]


def classify_file(path: str, hunks: list[Hunk], min_run: int, base_fenced: Optional[set[int]] = None, head_fenced: Optional[set[int]] = None) -> list[Finding]:
    """Classify one file's hunks. ``base_fenced`` / ``head_fenced`` are :func:`fenced_lines` maps
    of the BASE and HEAD contents: a '-' line is judged against BASE, a '+' line against HEAD."""
    findings: list[Finding] = []
    for h in hunks:
        deleted, added = len(h.deleted), len(h.added)
        if deleted == 0:
            continue  # pure addition -- the additions-only happy path
        del_headings = _headings(h.deleted, h.old_start, base_fenced)
        add_headings = _headings(h.added, h.new_start, head_fenced)
        if del_headings and not add_headings:
            findings.append(Finding(path, "heading-deletion", "FAIL", {"headings": [ln.strip()[:120] for ln in del_headings], "deleted": deleted, "added": added}))
        elif added == 0 and deleted >= min_run:
            findings.append(Finding(path, "deletion-run", "FAIL", {"deleted": deleted, "min_run": min_run}))
        else:
            findings.append(Finding(path, "small-deletion", "WARN", {"deleted": deleted, "added": added}))
    return findings


# ---- escape-hatch trailer parsing ------------------------------------------

_ALLOW_RE = re.compile(r"^\s*Allow-Docs-Rewrite:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def parse_allow_trailers(messages: str) -> tuple[set[str], bool]:
    """Return (enumerated file tokens, wildcard_seen). A ``*`` waives all docs files."""
    allowed: set[str] = set()
    wildcard = False
    for m in _ALLOW_RE.finditer(messages or ""):
        for tok in re.split(r"[,\s]+", m.group(1).strip()):
            tok = tok.strip()
            if not tok:
                continue
            if tok == "*":
                wildcard = True
                continue
            allowed.add(tok)
    return allowed, wildcard


def _waives(path: str, allowed: set[str], wildcard: bool) -> bool:
    if wildcard:
        return True
    return path in allowed or path.rsplit("/", 1)[-1] in allowed


def apply_waivers(findings: list[Finding], allowed: set[str], wildcard: bool) -> None:
    for f in findings:
        if f.severity == "FAIL" and _waives(f.path, allowed, wildcard):
            f.severity = "WAIVED"
            f.detail = {**f.detail, "waived_by": "Allow-Docs-Rewrite trailer"}


# ---- driver ----------------------------------------------------------------


def run(root: str, base: str, head: str, files: Optional[list[str]], min_run: int, scope: Optional[list[str]] = None) -> tuple[int, dict]:
    """Return (exit_code, report). exit_code: 0 clean, 1 findings, 2 invocation error.

    ``scope`` (from the CLI ``--scope`` flag) is an optional list of POSIX path globs.
    When None/empty the universal :func:`in_docs_scope` predicate is used verbatim;
    otherwise a discovered path is in scope iff it matches any glob AND ends ``.md``.
    An explicit ``files`` list bypasses scope entirely.
    """
    base_sha = resolve_ref(root, base)
    head_sha = resolve_ref(root, head)
    if base_sha is None or head_sha is None:
        bad = base if base_sha is None else head
        return 2, {"error": f"could not resolve ref: {bad!r}"}

    if files:
        scoped = [p for p in files if p.endswith(".md")]
        skipped = [p for p in files if p not in scoped]
    else:
        discovered = changed_files(root, base, head)
        if scope:
            # A discovered path is in scope iff it matches any --scope glob AND ends .md.
            scoped = [p for p in discovered if p.endswith(".md") and _match_scope(p, scope)]
        else:
            # No --scope: reproduce the universal in_docs_scope() predicate verbatim.
            scoped = [p for p in discovered if in_docs_scope(p)]
        skipped = [p for p in discovered if p not in scoped]

    findings: list[Finding] = []
    for path in sorted(set(scoped)):
        hunks = parse_hunks(file_diff(root, base_sha, head_sha, path))
        # Fence maps are read only for the side a hunk actually needs.
        base_text = file_text(root, base_sha, path) if any(h.deleted for h in hunks) else None
        head_text = file_text(root, head_sha, path) if any(h.added for h in hunks) else None
        base_fenced = fenced_lines(base_text) if base_text is not None else None
        head_fenced = fenced_lines(head_text) if head_text is not None else None
        findings.extend(classify_file(path, hunks, min_run, base_fenced, head_fenced))

    allowed, wildcard = parse_allow_trailers(range_messages(root, base_sha, head_sha))
    apply_waivers(findings, allowed, wildcard)

    fails = [f for f in findings if f.severity == "FAIL"]
    by_reason: dict[str, int] = {}
    for f in findings:
        by_reason[f.reason] = by_reason.get(f.reason, 0) + 1

    report = {
        "base": base_sha,
        "head": head_sha,
        "min_run": min_run,
        "stats": {
            "files_screened": len(scoped),
            "skipped_out_of_scope": sorted(set(skipped)),
            "findings_total": len(findings),
            "fail_count": len(fails),
            "by_reason": by_reason,
            "waived_files": sorted(allowed),
            "wildcard_waiver": wildcard,
        },
        "findings": [{"path": f.path, "reason": f.reason, "severity": f.severity, "detail": f.detail} for f in sorted(findings, key=lambda x: (x.path, x.reason))],
    }
    return (1 if fails else 0), report
