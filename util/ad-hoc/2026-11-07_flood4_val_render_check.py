#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only render check of a markdown file, worktree copy vs origin/main, with markdown-it-py
#               (CommonMark + GFM tables). Every source line gets a rendered-role signature (heading level,
#               table row, list depth, fence, blockquote, paragraph, hr). Reports:
#                 1. UNCHANGED main lines (difflib "equal" blocks) whose role differs between main and the
#                    worktree -- render damage such as a split table, an absorbed paragraph, or a list broken by a
#                    stray paragraph;
#                 2. ADDED lines that start with "|" but do not render as a table row, or start with a list marker
#                    but do not render as a list item, or start with "#" but are not headings (and not in a fence);
#                 3. table rows (worktree) whose cell count differs from the table's header cell count;
#                 4. totals of tables / list items / headings / fences on both sides.
"""
Read-only render check of a markdown file against origin/main with markdown-it-py: unchanged lines whose rendered role changed, added lines that do not render as what they look like, split lists and tables, and table rows whose cell count differs from the header.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import difflib
import re
import subprocess
import sys

from markdown_it import MarkdownIt

path = sys.argv[1]
md = MarkdownIt("commonmark").enable("table")


def roles(text):
    lines = text.splitlines()
    chains = [[] for _ in lines]
    tokens = md.parse(text)
    for tok in tokens:
        if tok.map is None or tok.nesting < 0:
            continue
        a, b = tok.map
        t = tok.type
        if t == "heading_open":
            t = f"h{tok.tag[1]}"
        for i in range(a, min(b, len(lines))):
            chains[i].append(t)
    sig = []
    for i, ch in enumerate(chains):
        if not lines[i].strip():
            sig.append("blank")
            continue
        s = []
        if "table_open" in ch:
            s.append("table-row")
        depth = ch.count("list_item_open")
        if depth:
            s.append(f"list{depth}")
        bq = ch.count("blockquote_open")
        if bq:
            s.append(f"bq{bq}")
        for t in ch:
            if re.fullmatch(r"h[1-6]", t):
                s.append(t)
        if "fence" in ch or "code_block" in ch:
            s.append("code")
        if "hr" in ch:
            s.append("hr")
        if "html_block" in ch:
            s.append("html")
        if not s:
            s.append("para" if "paragraph_open" in ch else "+".join(ch) or "none")
        sig.append(",".join(s))
    return lines, sig, tokens


def table_cell_checks(tokens, lines, label):
    out = []
    i = 0
    while i < len(tokens):
        if tokens[i].type == "table_open":
            header_cells = None
            j = i + 1
            row_cells = 0
            row_line = None
            while tokens[j].type != "table_close":
                t = tokens[j]
                if t.type == "tr_open":
                    row_cells = 0
                    row_line = t.map[0] if t.map else None
                elif t.type in ("th_open", "td_open"):
                    row_cells += 1
                elif t.type == "tr_close":
                    if header_cells is None:
                        header_cells = row_cells
                    elif row_line is not None:
                        # markdown-it pads/truncates; count raw pipes instead for the source line
                        raw = lines[row_line]
                        raw_cells = len(re.findall(r"(?<!\\)\|", raw.strip().strip("|"))) + 1 if raw.strip() else 0
                        if raw_cells != header_cells:
                            out.append((label, row_line + 1, header_cells, raw_cells, raw[:140]))
                j += 1
            i = j
        i += 1
    return out


main_text = subprocess.run(["git", "show", f"origin/main:{path}"], capture_output=True, text=True, check=True).stdout
with open(path, encoding="utf-8") as fh:
    new_text = fh.read()
ml, ms, mt = roles(main_text)
nl, ns, nt = roles(new_text)

sm = difflib.SequenceMatcher(a=ml, b=nl, autojunk=False)
damage = []
added = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            if ms[i1 + k] != ns[j1 + k]:
                damage.append((i1 + k + 1, j1 + k + 1, ms[i1 + k], ns[j1 + k], ml[i1 + k][:120]))
    elif tag in ("replace", "insert"):
        for k in range(j1, j2):
            added.append((k + 1, ns[k], nl[k]))

print(f"== {path}")
print(f"   main: {len(ml)} lines; worktree: {len(nl)} lines")
for label, toks in (("main", mt), ("worktree", nt)):
    counts = {}
    for t in toks:
        if t.type in ("table_open", "list_item_open", "heading_open", "fence", "bullet_list_open", "ordered_list_open", "hr"):
            counts[t.type] = counts.get(t.type, 0) + 1
    print(f"   {label}: {counts}")
print(f"   UNCHANGED-LINE ROLE CHANGES: {len(damage)}")
for d in damage[:60]:
    print(f"     main:{d[0]} wt:{d[1]}  {d[2]} -> {d[3]}  | {d[4]}")
bad_added = []
for ln, sig, text in added:
    s = text.lstrip()
    if s.startswith("|") and "table-row" not in sig and "code" not in sig:
        bad_added.append((ln, sig, text[:140], "pipe-line-not-table-row"))
    if re.match(r"^\s*([-*+]|\d+[.)])\s+\S", text) and "list" not in sig and "code" not in sig and "table-row" not in sig:
        bad_added.append((ln, sig, text[:140], "list-marker-not-list"))
    if re.match(r"^#{1,6}\s", text) and not re.search(r"\bh[1-6]\b", sig) and "code" not in sig:
        bad_added.append((ln, sig, text[:140], "hash-line-not-heading"))
    if re.match(r"^#{1,6}\s", text) and re.search(r"\bh1\b", sig):
        bad_added.append((ln, sig, text[:140], "added-H1"))
print(f"   ADDED-LINE ROLE PROBLEMS: {len(bad_added)} (of {len(added)} added/replaced lines)")
for b in bad_added:
    print(f"     wt:{b[0]} [{b[1]}] {b[3]}: {b[2]}")
absorbed = [(ln, sig, text[:140]) for ln, sig, text in added if "table-row" in sig and not text.lstrip().startswith("|")]
print(f"   ADDED NON-PIPE LINES RENDERED AS TABLE ROWS (absorbed): {len(absorbed)}")
for a in absorbed:
    print(f"     wt:{a[0]} [{a[1]}]: {a[2]}")


def container_ids(tokens, nlines):
    """Per line: id of the outermost list token and of the table token enclosing it (or None)."""
    lst = [None] * nlines
    tbl = [None] * nlines
    for idx, tok in enumerate(tokens):
        if tok.map is None or tok.nesting < 0:
            continue
        a, b = tok.map
        if tok.type in ("bullet_list_open", "ordered_list_open") and tok.level == 0:
            for i in range(a, min(b, nlines)):
                lst[i] = idx
        if tok.type == "table_open":
            for i in range(a, min(b, nlines)):
                tbl[i] = idx
    return lst, tbl


mlst, mtbl = container_ids(mt, len(ml))
nlst, ntbl = container_ids(nt, len(nl))
pairs = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        pairs.extend((i1 + k, j1 + k) for k in range(i2 - i1))
splits = []
for kind, mids, nids in (("list", mlst, nlst), ("table", mtbl, ntbl)):
    seen = {}
    for mi, ni in pairs:
        if mids[mi] is None or not ml[mi].strip():
            continue
        seen.setdefault(mids[mi], set()).add(nids[ni])
    for mid, nset in seen.items():
        if len(nset) > 1:
            first = min(i for i in range(len(ml)) if mids[i] == mid)
            splits.append((kind, first + 1, sorted(x if x is not None else -1 for x in nset)))
print(f"   MAIN LISTS/TABLES NOW SPLIT ACROSS CONTAINERS: {len(splits)}")
for s in splits:
    print(f"     {s[0]} starting main:{s[1]} -> worktree containers {s[2]}")
cells = table_cell_checks(nt, nl, "worktree")
main_cells = table_cell_checks(mt, ml, "main")
main_bad_text = {c[4] for c in main_cells}
new_cells = [c for c in cells if c[4] not in main_bad_text]
print(f"   TABLE ROWS WITH CELL COUNT != HEADER (worktree, not already on main): {len(new_cells)} (main had {len(main_cells)})")
for c in new_cells:
    print(f"     wt:{c[1]} header={c[2]} raw={c[3]} | {c[4]}")
