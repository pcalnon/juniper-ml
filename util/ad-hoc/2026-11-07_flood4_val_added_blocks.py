#!/usr/bin/env python3
# Project:      juniper-ml
# Sub-Project:  util/ad-hoc
# Application:  flood-4 docs-carrier validation (fidelity lens)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Purpose:      Read-only: for each -U0 hunk of `git diff origin/main -- <path>`, report the NEW-file line
#               range, the enclosing heading chain at the insertion point (fence-aware, CommonMark-ish
#               closing-fence rule), the block kind of the main line just before and just after the hunk
#               (table row / list item / fence / blank / paragraph / heading), and whether the insertion
#               point is inside a fence, a table, or a list on MAIN. Flags hunks that land inside a
#               table/list/fence, or right after the doc's footer stamps.
"""
Read-only placement check: for each hunk of `git diff -U0 origin/main -- <path>`, print where it lands in main's markdown structure (heading chain, neighbouring block kinds) and flag one that splits a table, list or fence, joins two blocks without a blank line, or lands beside the footer stamps.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 1, structure-and-fidelity lens (findings: tmp/flood4/ml-docs/val-fidelity/)
"""

import re
import subprocess
import sys

path = sys.argv[1]
main_text = subprocess.run(["git", "show", f"origin/main:{path}"], capture_output=True, text=True, check=True).stdout
with open(path, encoding="utf-8") as fh:
    new_text = fh.read()
main_lines = main_text.splitlines()
new_lines = new_text.splitlines()


def fence_state(lines):
    """Return per-line flag: True if line is inside a fence (including the fence lines)."""
    st = []
    fence = None
    for line in lines:
        m = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
        if fence is None:
            if m and (m.group(2)[0] != "`" or "`" not in m.group(3)):
                fence = (m.group(2)[0], len(m.group(2)))
                st.append(True)
                continue
            st.append(False)
        else:
            st.append(True)
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and m.group(3).strip() == "":
                fence = None
    return st


def kind(line, infence):
    if infence:
        return "FENCE"
    s = line.strip()
    if s == "":
        return "blank"
    if s.startswith("|"):
        return "table"
    if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
        return "list"
    if re.match(r"^#{1,6}\s", line):
        return "heading"
    if re.match(r"^\s{2,}\S", line):
        return "indented"
    if s == "---":
        return "rule"
    return "para"


def chain(lines, upto, fst):
    stack = []
    for i in range(upto):
        if fst[i]:
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*$", lines[i])
        if h:
            lvl = len(h.group(1))
            if lvl == 1:
                continue
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, h.group(2)[:70]))
    return " > ".join(f"{'#' * a} {b}" for a, b in stack)


mf = fence_state(main_lines)
nf = fence_state(new_lines)
diff = subprocess.run(["git", "diff", "-U0", "origin/main", "--", path], capture_output=True, text=True, check=True).stdout
for line in diff.splitlines():
    m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not m:
        continue
    os_, oc = int(m.group(1)), int(m.group(2)) if m.group(2) is not None else 1
    ns, nc = int(m.group(3)), int(m.group(4)) if m.group(4) is not None else 1
    # main line just before the change and just after
    before_idx = (os_ - 1) if oc == 0 else (os_ - 2)  # 0-based index of main line before the hunk
    after_idx = os_ if oc == 0 else (os_ - 1 + oc)  # 0-based index of main line after the hunk
    b = main_lines[before_idx] if 0 <= before_idx < len(main_lines) else "<BOF>"
    a = main_lines[after_idx] if 0 <= after_idx < len(main_lines) else "<EOF>"
    bk = kind(b, mf[before_idx]) if 0 <= before_idx < len(main_lines) else "BOF"
    ak = kind(a, mf[after_idx]) if 0 <= after_idx < len(main_lines) else "EOF"
    first_new = new_lines[ns - 1] if nc and ns - 1 < len(new_lines) else ""
    last_new = new_lines[ns - 2 + nc] if nc and ns - 2 + nc < len(new_lines) else ""
    fk = kind(first_new, nf[ns - 1]) if nc else "-"
    lk = kind(last_new, nf[ns - 2 + nc]) if nc else "-"
    flag = []
    if bk == "FENCE" and ak == "FENCE":
        flag.append("INSIDE-FENCE?")
    if bk == "table" and ak == "table" and fk != "table":
        flag.append("SPLITS-TABLE")
    if bk == "table" and fk not in ("table", "blank") and oc == 0:
        flag.append("TABLE-THEN-NONTABLE-NO-BLANK")
    if bk == "list" and ak == "list" and fk not in ("list", "indented"):
        flag.append("SPLITS-LIST")
    if bk in ("para", "list", "table") and fk == "heading":
        flag.append("HEADING-WITHOUT-BLANK-BEFORE")
    if lk == "heading" and ak not in ("blank",):
        flag.append("HEADING-WITHOUT-BLANK-AFTER")
    if lk in ("para", "list", "table") and ak in ("para", "list", "table") and lk != ak and oc == 0:
        flag.append(f"ADJACENT-{lk}-{ak}")
    if lk == "table" and ak == "para":
        flag.append("TABLE-THEN-PARA-NO-BLANK")
    if re.match(r"^\*\*(Version|Last Updated|Date|Maintainer)", b) or re.match(r"^\*\*(Version|Last Updated|Date|Maintainer)", a):
        if not re.match(r"^\*\*(Version|Last Updated|Date|Maintainer)", first_new):
            flag.append("NEAR-STAMPS")
    print(f"{line.split('@@')[1].strip():>22} | new {ns}-{ns + nc - 1} | before[{bk}] after[{ak}] | first[{fk}] last[{lk}] | {' '.join(flag)}")
    print(f"{'':>22} |   in: {chain(new_lines, ns - 1, nf)}")
