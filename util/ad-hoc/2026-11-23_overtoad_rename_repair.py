#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Repair a blind "owner -> Overtoad" substitution so it renames only references to the PERSON.

Why this exists
---------------
The owner's rename PRs (2026-11-20..23, eight repos) replaced every "owner" with "Overtoad" (and in
juniper-ml every "Owner" with "The Overtoad"). The substitution also hit code identifiers
(``_lifecycle_owner``, ``owner_of``, ``test_*_ownership`` -- sequence-safety LOST), GitHub API
placeholders (``/repos/{owner}/{repo}``), paths and filenames, "ownership", technical owners (a lock's,
a slot's, a listener's), symlinks (``sed -i`` writes a regular file over the link), byte-pinned publish
templates and records that must stay verbatim. The owner's rulings (2026-11-23): records keep their
original text; the rename applies to living docs, code comments and config; the publish template moves
via a cascor re-pin, so client repos drop their publish-file edits.

What it does (run in a checkout of the PR head; BASE = merge-base with main)
---------------------------------------------------------------------------
- symlink that became a regular file            -> restore the link from BASE
- record (``--record`` globs)                   -> restore the file from BASE (a NEW record is reported)
- pinned file (``--pinned`` globs)              -> restore the file from BASE
- every other changed line that is a pure rename -> per occurrence: KEEP (the person) or RESTORE
  (technical), decided from the BASE line's context; "the The Overtoad" collapses to "the Overtoad"
- lines changed beyond the rename are left alone; any technical-looking "Overtoad" on them is reported
- ``--agents-md-date YYYY-MM-DD`` sets AGENTS.md's ``**Last Updated**:`` line

Usage
-----
    python3 2026-11-23_overtoad_rename_repair.py --repo <checkout> --base <ref> [--record GLOB ...]
        [--pinned GLOB ...] [--agents-md-date YYYY-MM-DD] [--apply] [--report out.tsv]
    python3 2026-11-23_overtoad_rename_repair.py --self-test
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import io
import os
import re
import subprocess
import sys
import tokenize

SEP = re.compile(r"(Owner|owner)")
# technical owners named by the word BEFORE "owner" (lowercase compare)
TECH_BEFORE = {
    "repo", "repository", "repositories", "lock", "file", "files", "process", "listener", "socket", "port", "slot", "lease",
    "window", "pid", "task", "job", "thread", "resource", "key", "co", "non", "its", "their", "whose", "account", "org",
    "organization", "github", "code", "lifecycle", "run", "worker", "dataset", "stack", "pr", "branch", "tag", "image",
    "package", "token", "secret", "cache", "directory", "dir", "group", "user", "fd", "mutex", "semaphore", "queue",
    "connection", "request", "row", "record", "entry", "endpoint", "service", "module", "class", "object", "instance",
    "race-window", "symbol", "content", "data", "page", "panel", "component", "callback", "store", "model",
    # a qualified owner is a generic/technical one; the person is always "the owner" / "an owner"
    "single", "second", "first", "mount", "sole", "unique", "exclusive", "previous", "current", "original",
    "legitimate", "wrong", "same", "other", "another", "each", "every", "one", "new", "project", "prop", "output",
}
STRONG_TECH = {"lock", "file", "process", "socket", "port", "slot", "lease", "window", "pid", "thread", "repo", "repository", "code", "race-window", "listener", "lifecycle", "key", "token", "mutex", "fd", "organization", "org", "account", "github"}
# technical owners named by the word AFTER "owner"
TECH_AFTER = {"process", "pid", "uid", "gid", "thread", "field", "token", "id", "ids", "column", "key", "attribute", "attr", "check", "match", "mismatch", "name", "login", "type", "outputs", "output", "callback", "callbacks", "prop", "props", "component", "slug"}
PERSON_HINT = re.compile(r"^(?:'s\b|\s+(?:ruling|rulings|ruled|decision|decisions|decided|decides|directive|request|requested|approval|approves|approved|approve|action|actions|gate|gated|call|calls|choice|chose|choose|chooses|says|said|asked|asks|confirmed|confirms|answer|answered|merges|merged|merge|runs|ran|touch|touches|instruction|instructions|preference|prefers|wants|wanted|note|notes|review|reviews|reviewed|sign-off|signs|signed|owns|must|may|can|will|should|has|had|is|was|needs|need|step|steps|card|command|commands|only|run|-only))", re.I)


def classify(line: str, s: int, e: int, in_name_token: bool) -> tuple[str, str]:
    """Return (KEEP|RESTORE|REVIEW, reason) for the occurrence line[s:e] of owner/Owner in a BASE line."""
    if in_name_token:
        return "RESTORE", "python identifier"
    prev = line[s - 1] if s > 0 else ""
    prev2 = line[s - 2 : s] if s > 1 else prev
    nxt = line[e] if e < len(line) else ""
    after = line[e:]
    if prev.isalnum() or prev == "_":
        return "RESTORE", "inside a word/identifier"
    if nxt.isalnum() or nxt == "_":
        return "RESTORE", "inside a word/identifier (owners/ownership/owner_x)"
    # NB: "" in "..." is True in Python -- every membership test needs a non-empty operand
    if (prev and prev in "{<$/\\") or (nxt and nxt in "}>/=(\\"):
        return "RESTORE", "placeholder/path/assignment"
    if prev and nxt and prev in "\"'`" and nxt in "\"'`":
        return "RESTORE", "quoted token"
    if prev == "." and s > 1 and (line[s - 2].isalnum() or line[s - 2] in "_)]"):
        return "RESTORE", "attribute access"
    if nxt == "." and e + 1 < len(line) and (line[e + 1].isalnum() or line[e + 1] == "_"):
        return "RESTORE", "attribute/dotted name"
    if prev == "-":
        return "RESTORE", "hyphen-prefixed (co-owner, --owner, non-owner)"
    if nxt == ":" and re.match(r"^\s*(?:-\s*)?$", line[:s]):
        return "RESTORE", "mapping key at line start"
    if prev == "#" and prev2 != " #":
        return "RESTORE", "anchor fragment"
    # the word directly before, separated by whitespace only ("pull request (owner ruling" has none)
    m_before = re.search(r"([A-Za-z][A-Za-z-]*)\s+$", line[:s])
    before = m_before.group(1).lower() if m_before else ""
    m_after = re.match(r"\s+([A-Za-z]+)", after)
    after_word = m_after.group(1).lower() if m_after else ""
    if re.search(r"\|\s*$", line[:s]) and re.match(r"\s*\|", after):
        return "REVIEW", "a whole table cell"
    if nxt == "-" and re.match(r"-[A-Za-z]", after):
        # owner-gated / owner-ruled / owner-approved: the person, unless a strongly technical noun precedes
        if before in STRONG_TECH:
            return "RESTORE", f"technical compound ('{before} owner-')"
        return "KEEP", "person compound (owner-<verb>)"
    if re.match(r"\s+of\b", after):
        return "RESTORE", "technical 'owner of <thing>'"
    if PERSON_HINT.match(after):
        if before in TECH_BEFORE and before not in ("its", "their", "whose"):
            return "REVIEW", f"person verb after a technical noun '{before}'"
        return "KEEP", "person (verb/possessive follows)"
    if before in TECH_BEFORE:
        return "RESTORE", f"technical owner ('{before} owner')"
    if after_word in TECH_AFTER:
        return "RESTORE", f"technical owner ('owner {after_word}')"
    return "KEEP", "person (default)"


def name_token_spans(src: str) -> dict[int, list[tuple[int, int]]]:
    spans: dict[int, list[tuple[int, int]]] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.NAME and tok.start[0] == tok.end[0]:
                spans.setdefault(tok.start[0], []).append((tok.start[1], tok.end[1]))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # not tokenizable as a whole (a fragment, a template): keep the spans read before the error; every other
        # occurrence is classified as prose, which only means "restore" when the context says technical
        return spans
    return spans


def repair_line(base_line: str, head_line: str, name_spans: list[tuple[int, int]] | None) -> tuple[str, list[tuple[str, str, str]]] | None:
    """Rebuild head_line keeping only the person-renames. None if head differs beyond the rename."""
    pieces = SEP.split(base_line)
    if len(pieces) == 1:
        return None
    pat = "".join(re.escape(p) if k % 2 == 0 else "(Owner|owner|The Overtoad|Overtoad)" for k, p in enumerate(pieces))
    m = re.fullmatch(pat, head_line)
    if not m:
        return None
    out = [pieces[0]]
    decisions = []
    pos = len(pieces[0])
    for k in range(1, len(pieces), 2):
        orig = pieces[k]
        got = m.group((k + 1) // 2)
        s, e = pos, pos + len(orig)
        if got == orig:
            out.append(orig)
            decisions.append(("UNCHANGED", "", orig))
        else:
            in_name = any(a <= s and e <= b for a, b in (name_spans or []))
            verdict, why = classify(base_line, s, e, in_name)
            if verdict in ("RESTORE", "REVIEW"):  # REVIEW = technical noun context; restore by default, reported
                out.append(orig)
            else:
                rep = got
                prior = "".join(out)
                # "the Owner" -> "the The Overtoad": drop the doubled article
                if got == "The Overtoad" and re.search(r"(?i)\bthe\s+$", prior):
                    rep = "Overtoad"
                out.append(rep)
            decisions.append((verdict, why, f"{base_line[max(0, s - 40):e + 40].strip()}"))
        out.append(pieces[k + 1])
        pos = e + len(pieces[k + 1])
    return "".join(out), decisions


def git(repo: str, *args: str, text: bool = True):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=text)


def ls_tree_mode(repo: str, ref: str, path: str) -> str | None:
    r = git(repo, "ls-tree", ref, "--", path)
    return r.stdout.split()[0] if r.returncode == 0 and r.stdout.strip() else None


def matches(path: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, g) for g in globs)


TECH_HEAD = re.compile(r"[A-Za-z0-9_{$/.\\<-]Overtoad|Overtoad[A-Za-z0-9_}/=(\\>]|`Overtoad`|\"Overtoad\"")


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--record", action="append", default=[])
    ap.add_argument("--pinned", action="append", default=[])
    ap.add_argument("--agents-md-date")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    repo = a.repo
    st = git(repo, "diff", "--name-status", "--no-renames", a.base, "HEAD").stdout.splitlines()
    report: list[str] = []
    counts: dict[str, int] = {}

    def note(kind: str, path: str, detail: str = "") -> None:
        counts[kind] = counts.get(kind, 0) + 1
        report.append(f"{kind}\t{path}\t{detail}")

    for row in st:
        status, path = row.split("\t", 1)
        base_mode = ls_tree_mode(repo, a.base, path)
        head_mode = ls_tree_mode(repo, "HEAD", path)
        full = os.path.join(repo, path)
        if base_mode == "120000" and head_mode != "120000":
            note("SYMLINK-RESTORE", path, f"base link -> {git(repo, 'show', f'{a.base}:{path}').stdout.strip()}")
            if a.apply:
                git(repo, "checkout", a.base, "--", path)
            continue
        if matches(path, a.record):
            if base_mode is None:
                note("RECORD-NEW", path, "added by the PR; no original to restore (review by hand)")
            else:
                note("RECORD-RESTORE", path)
                if a.apply:
                    git(repo, "checkout", a.base, "--", path)
            continue
        if matches(path, a.pinned):
            if base_mode is None:
                note("PINNED-NEW", path)
            else:
                note("PINNED-RESTORE", path)
                if a.apply:
                    git(repo, "checkout", a.base, "--", path)
            continue
        if status.startswith("D") or head_mode is None:
            note("DELETED", path)
            continue
        if base_mode is None:
            # a file the PR added: report technical-looking Overtoad
            try:
                with open(full, encoding="utf-8") as handle:
                    txt = handle.read()
            except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
                continue
            for i, ln in enumerate(txt.splitlines(), 1):
                if TECH_HEAD.search(ln):
                    note("NEWFILE-TECH?", f"{path}:{i}", ln.strip()[:160])
            continue
        try:
            base_txt = git(repo, "show", f"{a.base}:{path}").stdout
            with open(full, encoding="utf-8") as handle:
                head_txt = handle.read()
        except (UnicodeDecodeError, IsADirectoryError):
            note("BINARY", path)
            continue
        base_lines = base_txt.splitlines(keepends=True)
        head_lines = head_txt.splitlines(keepends=True)
        spans = name_token_spans(base_txt) if path.endswith(".py") else {}
        out_lines = list(head_lines)
        changed = False
        sm = difflib.SequenceMatcher(a=base_lines, b=head_lines, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace" and (i2 - i1) == (j2 - j1):
                for off in range(i2 - i1):
                    bl, hl = base_lines[i1 + off], head_lines[j1 + off]
                    res = repair_line(bl.rstrip("\n"), hl.rstrip("\n"), spans.get(i1 + off + 1))
                    if res is None:
                        if "Overtoad" in hl and TECH_HEAD.search(hl):
                            note("MANUAL-TECH?", f"{path}:{j1 + off + 1}", hl.strip()[:160])
                        continue
                    new_line, decisions = res
                    nl = new_line + ("\n" if hl.endswith("\n") else "")
                    if nl != hl:
                        out_lines[j1 + off] = nl
                        changed = True
                    for verdict, why, ctx in decisions:
                        if verdict != "UNCHANGED":
                            note(verdict, f"{path}:{j1 + off + 1}", f"{why} | {ctx[:150]}")
            else:
                for j in range(j1, j2):
                    if "Overtoad" in head_lines[j] and TECH_HEAD.search(head_lines[j]):
                        note("MANUAL-TECH?", f"{path}:{j + 1}", head_lines[j].strip()[:160])
        if path == "AGENTS.md" and a.agents_md_date:
            for k, ln in enumerate(out_lines):
                if ln.startswith("**Last Updated**:"):
                    want = f"**Last Updated**: {a.agents_md_date}\n"
                    if ln != want:
                        out_lines[k] = want
                        changed = True
                        note("AGENTS-DATE", path, a.agents_md_date)
                    break
        if changed and a.apply:
            with open(full, "w", encoding="utf-8") as fh:
                fh.write("".join(out_lines))
    if a.report:
        with open(a.report, "w") as fh:
            fh.write("\n".join(report) + "\n")
    print(" ".join(f"{k}={v}" for k, v in sorted(counts.items())) + ("  APPLIED" if a.apply else "  (dry run)"))
    return 0


def self_test() -> int:
    cases = [
        ("self._lifecycle_owner = run_token", "self._lifecycle_Overtoad = run_token", "self._lifecycle_owner = run_token"),
        ("# GET /repos/{owner}/{repo}/pulls", "# GET /repos/{Overtoad}/{repo}/pulls", "# GET /repos/{owner}/{repo}/pulls"),
        ("A run takes ownership as it enters", "A run takes Overtoadship as it enters", "A run takes ownership as it enters"),
        ("(F1, owner ruling 2026-09-24)", "(F1, Overtoad ruling 2026-09-24)", "(F1, Overtoad ruling 2026-09-24)"),
        ("until the owner makes 3.15 required", "until the Overtoad makes 3.15 required", "until the Overtoad makes 3.15 required"),
        ("the suspected race-window owner.", "the suspected race-window Overtoad.", "the suspected race-window owner."),
        ("def owner_of(x):", "def Overtoad_of(x):", "def owner_of(x):"),
        ("Owner decision #4, applied", "The Overtoad decision #4, applied", "The Overtoad decision #4, applied"),
        ("approved by the Owner today", "approved by the The Overtoad today", "approved by the Overtoad today"),
        ("  const byOwner = {};", "  const byThe Overtoad = {};", "  const byOwner = {};"),
        ("see HANDOFF_2026-09-09_arc-owner-rulings.md", "see HANDOFF_2026-09-09_arc-Overtoad-rulings.md", "see HANDOFF_2026-09-09_arc-owner-rulings.md"),
        ("use --owner pcalnon", "use --Overtoad pcalnon", "use --owner pcalnon"),
        ("the lock owner releases it", "the lock Overtoad releases it", "the lock owner releases it"),
        ("the owner's recovery ladder", "the Overtoad's recovery ladder", "the Overtoad's recovery ladder"),
        ("an owner label", "an Overtoad label", "an Overtoad label"),
        ("owner: pcalnon", "Overtoad: pcalnon", "owner: pcalnon"),
        ("x = repo.owner.login", "x = repo.Overtoad.login", "x = repo.owner.login"),
        ("${{ github.repository_owner }}", "${{ github.repository_Overtoad }}", "${{ github.repository_owner }}"),
        ("co-owner and non-owner", "co-Overtoad and non-Overtoad", "co-owner and non-owner"),
        ("owner-gated roll-out", "Overtoad-gated roll-out", "Overtoad-gated roll-out"),
        ("the owner and the owners", "the Overtoad and the Overtoads", "the Overtoad and the owners"),
        ("# (its owner-ruled `enabled[0]` swap).", "# (its Overtoad-ruled `enabled[0]` swap).", "# (its Overtoad-ruled `enabled[0]` swap)."),
        ("a pull request (owner ruling 2026-10-30)", "a pull request (Overtoad ruling 2026-10-30)", "a pull request (Overtoad ruling 2026-10-30)"),
        ("| Task | Owner | Status |", "| Task | The Overtoad | Status |", "| Task | Owner | Status |"),
        ("as the lifecycle owner's, as", "as the lifecycle Overtoad's, as", "as the lifecycle owner's, as"),
        ("An organization owner has to set it", "An organization Overtoad has to set it", "An organization owner has to set it"),
        ("the single owner of every poller interval", "the single Overtoad of every poller interval", "the single owner of every poller interval"),
        ("would be a second owner of its clock", "would be a second Overtoad of its clock", "would be a second owner of its clock"),
        ("guard writes, as (owner outputs, phase, prop).", "guard writes, as (Overtoad outputs, phase, prop).", "guard writes, as (owner outputs, phase, prop)."),
        ("``hydrate_model_class``, its mount owner: writing", "``hydrate_model_class``, its mount Overtoad: writing", "``hydrate_model_class``, its mount owner: writing"),
        ("after the owner added the secret", "after the Overtoad added the secret", "after the Overtoad added the secret"),
    ]
    fails = 0
    for base, head, want in cases:
        got = repair_line(base, head, None)
        got_line = got[0] if got else None
        if got_line != want:
            fails += 1
            print(f"FAIL {base!r}: got {got_line!r} want {want!r} ({got[1] if got else ''})")
    # python identifier via tokenize: a bare NAME token
    src = "if owner is token:\n    pass\n"
    spans = name_token_spans(src)
    got = repair_line("if owner is token:", "if Overtoad is token:", spans.get(1))
    if not got or got[0] != "if owner is token:":
        fails += 1
        print(f"FAIL bare python identifier: {got}")
    if repair_line("the owner", "the Overtoad (edited)", None) is not None:
        fails += 1
        print("FAIL: a line edited beyond the rename must be left alone")
    print(f"self-test: {len(cases) + 2} case(s), {fails} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
