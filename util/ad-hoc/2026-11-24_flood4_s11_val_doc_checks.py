#!/usr/bin/env python3
"""
Document-lens checks on the flood-4 record update: headings, tables, ruling numbering, times, hashes, shorthand, "owner", paths and the two CI docs screens.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V2: document lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (validates a drafted record update; reads files, writes one report)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; util/ad-hoc/2026-11-24_flood4_s11_record_pathcheck.py

What it does
------------
Reads main's copy of the record (--main) and the drafted update (--final). It runs no git command itself: the
caller supplies --tree (a ``git ls-tree -r --name-only origin/main`` listing) and --u0diff (a
``git diff --no-index --unified=0`` of the two copies). It reports:

  1. the headings of both copies, and any the update changed;
  2. every pipe table in both copies: each row's cell count against its header's (an unescaped "|" splits a
     cell even inside a code span, as GFM renders it), and any non-blank line that directly follows a table;
  3. section 8's numbered items: continuity from 1, duplicates, and for each item >= 15 a date in parentheses
     and a double-quoted label after it;
  4. in the lines the update added: clock times with no "Z", backticked hex that is not 8 long, bare 8-hex
     tokens, tokens shaped like session-internal ids, "ruling N" references beyond the last ruling, and
     every "owner" in the whole copy (added or kept, and whether it sits inside double quotes);
  5. every backticked token and link target in an added line that looks like a repository path, against --tree;
  6. the docs deletion-magnitude screen's verdict on --u0diff, using juniper-ci-tools' own parse_hunks /
     fenced_lines / classify_file loaded from --repo, plus every hunk that deletes 5 or more lines;
  7. the markdown structure screen's problem count for each copy (the module util/markdown_structure_delta.py
     loads, from --repo);
  8. trailing whitespace, the final newline, and invisible characters.

Exit 0 when it ran (the report is for a reader to judge), 2 on a usage error.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_doc_checks.py --main M.md --final F.md --tree main_tree.txt \
        --u0diff u0.diff --repo . --out report.txt
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
TIME_RE = re.compile(r"(?<![\d:.,])(\d{1,2}):(\d{2})(?::(\d{2}))?(?![\d])")
TICK_HEX_RE = re.compile(r"`([0-9a-f]{5,40})`")
BARE_HEX_RE = re.compile(r"(?<![`0-9A-Za-z_/.#-])([0-9a-f]{8})(?![`0-9A-Za-z_])")
SHORTHAND_RE = re.compile(r"(?<![\w/.#`-])([A-Z]{1,4}-?\d{1,3}[a-z]?)(?![\w])")
LOWER_SHORTHAND_RE = re.compile(r"\b(ml-code|ml-tests|ml-docs|jd-gitleaks|word-structure|code lens|claims review|code review)\b")
RULING_REF_RE = re.compile(r"\b[Rr]ulings? (\d+)(?:\s*(?:–|-|to|and)\s*(\d+))?")
OWNER_RE = re.compile(r"\bowners?\b", re.IGNORECASE)
TICK_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
INVISIBLE = {"﻿": "BOM", "​": "ZWSP", "‌": "ZWNJ", "‍": "ZWJ", "⁠": "WJ", " ": "NBSP", "­": "SHY"}
SUFFIXES = (".md", ".py", ".yml", ".yaml", ".toml", ".json", ".bash", ".sh", ".txt", ".js")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # a @dataclass in a path-loaded module needs its module registered first
    spec.loader.exec_module(module)
    return module


def fenced(lines: list[str]) -> set[int]:
    inside: set[int] = set()
    opening = None
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if opening is None:
            if m:
                opening = m.group(1)
                inside.add(i)
            continue
        inside.add(i)
        if m and m.group(1)[0] == opening[0] and len(m.group(1)) >= len(opening):
            opening = None
    return inside


def headings(lines: list[str]) -> list[tuple[int, str]]:
    fz = fenced(lines)
    return [(i + 1, line.rstrip()) for i, line in enumerate(lines) if i not in fz and HEADING_RE.match(line)]


def cells(line: str) -> int:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return len(CELL_SPLIT_RE.split(body))


def tables(lines: list[str]) -> list[dict]:
    fz = fenced(lines)
    out: list[dict] = []
    i = 0
    while i < len(lines):
        if i not in fz and lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[i + 1]):
            start = i
            header = cells(lines[i])
            bad = []
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                n = cells(lines[j])
                if n != header:
                    bad.append((j + 1, n))
                j += 1
            follower = lines[j] if j < len(lines) else ""
            out.append({"start": start + 1, "end": j, "header_cells": header, "rows": j - start - 2, "bad_rows": bad, "follower_nonblank": bool(follower.strip()), "follower": follower[:80]})
            i = j
        else:
            i += 1
    return out


def section(lines: list[str], number: int) -> tuple[int, int]:
    start = end = None
    for i, line in enumerate(lines):
        if line.startswith(f"## §{number} "):
            start = i
        elif start is not None and line.startswith("## §"):
            end = i
            break
    if start is None:
        return (0, 0)
    return (start, end if end is not None else len(lines))


def added_lines(old: list[str], new: list[str]) -> list[tuple[int, str]]:
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    out: list[tuple[int, str]] = []
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "insert"):
            out.extend((j + 1, new[j]) for j in range(j1, j2))
    return out


def inside_quotes(line: str, pos: int) -> bool:
    return line[:pos].count('"') % 2 == 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--u0diff", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--last-ruling", type=int, default=48)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    main_text = Path(args.main).read_text(encoding="utf-8")
    final_text = Path(args.final).read_text(encoding="utf-8")
    old, new = main_text.split("\n"), final_text.split("\n")
    added = added_lines(old, new)
    rep: list[str] = []
    w = rep.append

    w("== 1. HEADINGS ==")
    hm, hf = headings(old), headings(new)
    w(f"main {len(hm)}, final {len(hf)}; texts identical in order: {[h for _, h in hm] == [h for _, h in hf]}")
    for _, h in hf:
        w(f"  {h}")

    w("\n== 2. TABLES ==")
    for label, lines in (("main", old), ("final", new)):
        tbs = tables(lines)
        w(f"{label}: {len(tbs)} tables")
        for t in tbs:
            flag = "OK" if not t["bad_rows"] and not t["follower_nonblank"] else "CHECK"
            w(f"  {flag} lines {t['start']}-{t['end']} header_cells={t['header_cells']} rows={t['rows']} bad_rows={t['bad_rows']} follower_nonblank={t['follower_nonblank']} {t['follower']!r}")

    w("\n== 3. SECTION 8 NUMBERED ITEMS ==")
    s8, e8 = section(new, 8)
    nums = [(i + 1, int(m.group(1))) for i in range(s8, e8) if (m := re.match(r"^(\d+)\. ", new[i]))]
    seq = [n for _, n in nums]
    w(f"items {len(seq)}: first {seq[:1]} last {seq[-1:]}; continuous from 1: {seq == list(range(1, len(seq) + 1))}; duplicates: {sorted({n for n in seq if seq.count(n) > 1})}")
    for ln, n in nums:
        if n < 15:
            continue
        line = new[ln - 1]
        m = re.match(r"^\d+\. \*\*(.+?)\*\* \((\d{4}-\d{2}-\d{2})([^)]*)\): (.*)$", line)
        if not m:
            w(f"  ruling {n} (line {ln}): FORMAT? {line[:140]!r}")
            continue
        label_ok = m.group(4).startswith('"')
        w(f"  ruling {n} (line {ln}): date {m.group(2)}{m.group(3)}; label first: {label_ok}; subject: {m.group(1)!r}")

    w("\n== 4a. CLOCK TIMES IN ADDED LINES WITHOUT A FOLLOWING Z ==")
    for ln, line in added:
        for m in TIME_RE.finditer(line):
            tail = line[m.end() : m.end() + 6]
            if tail.startswith("Z") or re.match(r"^[–-]\d{1,2}Z", tail):
                continue
            w(f"  line {ln}: {line[max(0, m.start() - 50) : m.end() + 30]!r}")

    w("\n== 4b. BACKTICKED HEX NOT 8 LONG, AND BARE 8-HEX, IN ADDED LINES ==")
    for ln, line in added:
        for m in TICK_HEX_RE.finditer(line):
            if len(m.group(1)) != 8:
                w(f"  line {ln}: backticked {m.group(1)!r} ({len(m.group(1))} chars)")
        for m in BARE_HEX_RE.finditer(line):
            tok = m.group(1)
            if re.search(r"\d", tok) and re.search(r"[a-f]", tok):
                w(f"  line {ln}: bare 8-hex {tok!r}: {line[max(0, m.start() - 40) : m.end() + 10]!r}")

    w("\n== 4c. SHORTHAND-SHAPED TOKENS IN ADDED LINES (count added / count in main / first added line) ==")
    tok_lines: dict[str, list[int]] = {}
    for ln, line in added:
        for rx in (SHORTHAND_RE, LOWER_SHORTHAND_RE):
            for m in rx.finditer(line):
                tok_lines.setdefault(m.group(1), []).append(ln)
    for tok in sorted(tok_lines):
        in_main = len(re.findall(r"(?<![\w-])" + re.escape(tok) + r"(?![\w])", main_text))
        w(f"  {tok!r}: added {len(tok_lines[tok])} (lines {sorted(set(tok_lines[tok]))}), in main {in_main}")

    w("\n== 4d. 'RULING N' REFERENCES IN ADDED LINES BEYOND THE LAST RULING ==")
    hits = 0
    for ln, line in added:
        for m in RULING_REF_RE.finditer(line):
            for g in m.groups():
                if g and int(g) > args.last_ruling:
                    hits += 1
                    w(f"  line {ln}: {m.group(0)!r}")
    w(f"  {hits} found")

    w("\n== 4e. EVERY 'owner' IN THE FINAL COPY ==")
    added_set = {ln for ln, _ in added}
    for i, line in enumerate(new, start=1):
        for m in OWNER_RE.finditer(line):
            w(f"  line {i} ({'added' if i in added_set else 'kept'}; {'in quotes' if inside_quotes(line, m.start()) else 'NOT in quotes'}): {line[max(0, m.start() - 60) : m.end() + 40]!r}")
    w(f"  'Overtoad' in added lines: {sum(line.count('Overtoad') for _, line in added)}")

    w("\n== 5. PATHS IN ADDED LINES AGAINST THE origin/main TREE ==")
    tree = set(Path(args.tree).read_text(encoding="utf-8").split("\n"))
    dirs = {p.rsplit("/", 1)[0] + "/" for p in tree if "/" in p}
    seen: set[str] = set()
    links = 0
    for ln, line in added:
        links += len(LINK_RE.findall(line))
        for tok in TICK_RE.findall(line) + LINK_RE.findall(line):
            path = re.sub(r"(:\d+(-\d+)?(, ?\d+(-\d+)?)*|#[\w-]+)$", "", tok.strip())
            if path in seen or " " in path or not ("/" in path or path.endswith(SUFFIXES)):
                continue
            seen.add(path)
            if path in tree:
                verdict = "OK file"
            elif path.endswith("/") and any(d.startswith(path) for d in dirs):
                verdict = "OK dir"
            elif "…" in path or "*" in path or "{" in path:
                verdict = "SKIP pattern"
            else:
                verdict = "NOT ON MAIN"
            w(f"  {verdict:12} line {ln}: {tok}")
    w(f"  markdown links in added lines: {links}")

    w("\n== 6. DOCS DELETION-MAGNITUDE SCREEN (juniper-ci-tools docs_additions_check, from --repo) ==")
    dac = load_module("flood4_val_doc_dac", Path(args.repo) / "juniper-ci-tools" / "juniper_ci_tools" / "docs_additions_check.py")
    hunks = dac.parse_hunks(Path(args.u0diff).read_text(encoding="utf-8"))
    findings = dac.classify_file("notes/record.md", hunks, dac.DEFAULT_MIN_RUN, dac.fenced_lines(main_text), dac.fenced_lines(final_text))
    by: dict[str, int] = {}
    for f in findings:
        by[f"{f.severity}/{f.reason}"] = by.get(f"{f.severity}/{f.reason}", 0) + 1
    w(f"hunks {len(hunks)}; min_run {dac.DEFAULT_MIN_RUN}; findings by severity/reason: {by}; FAIL count: {sum(1 for f in findings if f.severity == 'FAIL')}")
    for h in hunks:
        if len(h.deleted) >= 5:
            w(f"  hunk deleting {len(h.deleted)} lines from main line {h.old_start} (adds {len(h.added)}): first deleted {h.deleted[0][:70]!r}")

    w("\n== 7. MARKDOWN STRUCTURE SCREEN (util/ad-hoc/2026-09-05_markdown_structure_check.py, from --repo) ==")
    msc = load_module("flood4_val_doc_msc", Path(args.repo) / "util" / "ad-hoc" / "2026-09-05_markdown_structure_check.py")
    pm, pf = msc.check(Path(args.main)), msc.check(Path(args.final))
    w(f"problems: main {len(pm)}, final {len(pf)} (the CI gate fails when final > main)")
    for p in pf:
        w(f"  final: {p}")

    w("\n== 8. WHITESPACE, FINAL NEWLINE, INVISIBLE CHARACTERS ==")
    trailing = [i for i, line in enumerate(new, start=1) if line != line.rstrip(" \t")]
    w(f"lines with trailing whitespace in final: {trailing}")
    w(f"final ends with exactly one newline: {final_text.endswith(chr(10)) and not final_text.endswith(chr(10) * 2)}")
    for name, text in (("main", main_text), ("final", final_text)):
        counts = {label: text.count(ch) for ch, label in INVISIBLE.items() if text.count(ch)}
        w(f"invisible characters in {name}: {counts or 'none'}")
    nonascii: dict[str, int] = {}
    for _, line in added:
        for ch in line:
            if ord(ch) > 127:
                nonascii[ch] = nonascii.get(ch, 0) + 1
    w(f"non-ASCII characters in added lines: {', '.join(f'U+{ord(c):04X} {c!r} x{n}' for c, n in sorted(nonascii.items()))}")

    Path(args.out).write_text("\n".join(rep) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(rep)} lines); added lines examined: {len(added)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
