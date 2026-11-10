#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-2 validation (read-only)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# -----------------------------------------------------------------------------
"""Round-2 structure screen of the flood-4 ml docs carrier (read-only).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 2 (findings: tmp/flood4/ml-docs/val-round2/)

Compares each changed markdown file on main (BASE root) with the carrier (TARGET root):

* renders both with markdown-it-py (commonmark + table) and reports heading-sequence
  changes, table-row losses (a source line that starts with '|' but renders outside a
  table), and per-table column-count mismatches;
* lists every ADDED line (difflib) that carries an HTML entity or a non-ASCII character,
  and says whether that character already occurs in main's copy of the file;
* checks every in-page / sibling-doc anchor on an added line against GitHub-style slugs.

Usage: python3 <this> BASE_ROOT TARGET_ROOT OUT_JSON
Writes only OUT_JSON. Never touches either tree.
"""

import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt

FILES = [
    "CHANGELOG.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "docs/REFERENCE.md",
    "juniper-config-tools/README.md",
    "juniper-service-core/README.md",
]

ENTITY = re.compile(r"&(?:[a-zA-Z]+|#[0-9]+|#x[0-9a-fA-F]+);")
LINK = re.compile(r"\]\(([^)\s]*)\)")


def slugify(text: str) -> str:
    text = re.sub(r"`", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    out = []
    for ch in text:
        if ch.isalnum() or ch in "-_ ":
            out.append(ch)
    return "".join(out).replace(" ", "-")


def headings_and_tables(src: str):
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(src)
    heads = []
    tables = []
    table_lines = set()
    fence_lines = set()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == "heading_open":
            inline = tokens[i + 1]
            heads.append((t.tag, inline.content, t.map[0] + 1 if t.map else None))
        if t.type == "table_open":
            start, end = t.map
            for ln in range(start, end):
                table_lines.add(ln + 1)
            # count columns per row
            rows = []
            j = i
            cur = None
            while tokens[j].type != "table_close":
                if tokens[j].type == "tr_open":
                    cur = 0
                elif tokens[j].type in ("th_open", "td_open"):
                    cur += 1
                elif tokens[j].type == "tr_close":
                    rows.append(cur)
                j += 1
            tables.append({"start": start + 1, "end": end, "rows": len(rows), "cols": sorted(set(rows))})
        if t.type in ("fence", "code_block") and t.map:
            for ln in range(t.map[0], t.map[1]):
                fence_lines.add(ln + 1)
        i += 1
    return heads, tables, table_lines, fence_lines


def raw_pipe_cells(line: str) -> int:
    # count cells of a raw table row, ignoring pipes inside backtick spans and escaped pipes
    s = line.strip()
    out = 0
    in_code = False
    k = 0
    cells = 1
    while k < len(s):
        c = s[k]
        if c == "\\" and k + 1 < len(s):
            k += 2
            continue
        if c == "`":
            in_code = not in_code
        elif c == "|" and not in_code:
            cells += 1
        k += 1
    out = cells
    if s.startswith("|"):
        out -= 1
    if s.endswith("|") and not s.endswith("\\|"):
        out -= 1
    return out


def main() -> int:
    base_root = Path(sys.argv[1])
    target_root = Path(sys.argv[2])
    out_path = Path(sys.argv[3])
    report = {}
    slug_cache = {}
    for rel in FILES:
        base = (base_root / rel).read_text(encoding="utf-8")
        targ = (target_root / rel).read_text(encoding="utf-8")
        bh, _bt, _, _ = headings_and_tables(base)
        th, tt, ttl, tfl = headings_and_tables(targ)
        slug_cache[rel] = {slugify(h[1]) for h in th}
        entry = {}
        bh_s = [(h[0], h[1]) for h in bh]
        th_s = [(h[0], h[1]) for h in th]
        sm = difflib.SequenceMatcher(a=bh_s, b=th_s, autojunk=False)
        head_changes = []
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == "equal":
                continue
            head_changes.append({"op": op, "main": [f"{h[0]} {h[1]}" for h in bh_s[a0:a1]], "carrier": [f"{h[0]} {h[1]}" for h in th_s[b0:b1]]})
        entry["heading_changes"] = head_changes
        # added lines
        bl = base.splitlines()
        tl = targ.splitlines()
        sm2 = difflib.SequenceMatcher(a=bl, b=tl, autojunk=False)
        added = []
        for op, a0, a1, b0, b1 in sm2.get_opcodes():
            if op in ("replace", "insert"):
                for k in range(b0, b1):
                    added.append((k + 1, tl[k]))
        entry["added_line_count"] = len(added)
        base_chars = set(base)
        flagged = []
        for ln, text in added:
            ents = ENTITY.findall(text) if ln not in tfl else []
            nonascii = sorted({ch for ch in text if ord(ch) > 127})
            if ents or nonascii:
                flagged.append(
                    {
                        "line": ln,
                        "entities": ents,
                        "non_ascii": [f"U+{ord(c):04X} {unicodedata.name(c, '?')} (in main's file: {c in base_chars})" for c in nonascii],
                        "excerpt": text[:160],
                    }
                )
        entry["added_lines_with_entities_or_non_ascii"] = flagged
        # stray table-looking lines outside rendered tables, on added lines only
        stray = []
        for ln, text in added:
            if text.lstrip().startswith("|") and ln not in ttl and ln not in tfl:
                stray.append({"line": ln, "excerpt": text[:120]})
        entry["added_table_like_lines_outside_tables"] = stray
        # tables touching added lines: cell-count consistency per raw row
        added_set = {ln for ln, _ in added}
        bad_tables = []
        for tab in tt:
            lines = range(tab["start"], tab["end"] + 1)
            if not any(ln in added_set for ln in lines):
                continue
            counts = {}
            for ln in lines:
                if ln - 1 < len(tl):
                    raw = tl[ln - 1]
                    if raw.strip().startswith("|"):
                        counts[ln] = raw_pipe_cells(raw)
            header = counts.get(tab["start"])
            mism = {ln: c for ln, c in counts.items() if c != header}
            if mism or len(tab["cols"]) != 1:
                bad_tables.append({"table_start": tab["start"], "header_cells": header, "rendered_cols": tab["cols"], "raw_mismatch_lines": mism})
        entry["touched_tables_checked"] = sum(1 for tab in tt if any(ln in added_set for ln in range(tab["start"], tab["end"] + 1)))
        entry["touched_tables_with_problems"] = bad_tables
        entry["_added"] = added
        report[rel] = entry
    # anchors on added lines
    for rel in FILES:
        entry = report[rel]
        bad = []
        for ln, text in entry.pop("_added"):
            for target in LINK.findall(text):
                if target.startswith("http"):
                    continue
                if "#" not in target:
                    continue
                path, _, frag = target.partition("#")
                if path == "":
                    doc = rel
                else:
                    doc = str((Path(rel).parent / path).as_posix())
                    doc = str(Path(doc))
                    # normalise ../
                    parts = []
                    for p in Path(doc).parts:
                        if p == "..":
                            if parts:
                                parts.pop()
                        else:
                            parts.append(p)
                    doc = "/".join(parts)
                if doc not in slug_cache:
                    p = target_root / doc
                    if p.is_file() and p.suffix == ".md":
                        h, _, _, _ = headings_and_tables(p.read_text(encoding="utf-8"))
                        slug_cache[doc] = {slugify(x[1]) for x in h}
                    else:
                        bad.append({"line": ln, "target": target, "why": "doc not found"})
                        continue
                if frag not in slug_cache[doc]:
                    bad.append({"line": ln, "target": target, "why": "anchor not found"})
        entry["added_line_bad_anchors"] = bad
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    for rel, entry in report.items():
        print(rel, "added", entry["added_line_count"], "heads", len(entry["heading_changes"]), "flag", len(entry["added_lines_with_entities_or_non_ascii"]), "stray", len(entry["added_table_like_lines_outside_tables"]), "tables", entry["touched_tables_checked"], "badtab", len(entry["touched_tables_with_problems"]), "badanchor", len(entry["added_line_bad_anchors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
