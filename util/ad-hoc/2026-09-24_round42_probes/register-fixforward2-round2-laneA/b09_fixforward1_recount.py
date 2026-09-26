#!/usr/bin/env python3
"""Lane A round 2: recount what juniper-ml#2080 (f2688a95, parent 6aabe4cc) changed in the register's primer
citations -- §4 `Primer` cells by row, and prose -- in citations (a range once) and numbers (both ends).

For every changed §4 Primer cell: old -> new, and whether each OLD number landed on a blank line of the primer
as it stood at 6aabe4cc (and at f2688a95). For prose: every line that changed where a 4-digit in-range number
changed, with the old/new number multisets.
"""
import difflib
import re
import subprocess
from collections import Counter

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRI = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
OLD, NEW = "6aabe4cc", "f2688a95"


def show(rev, rel):
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout.decode("utf-8")


def cells(line):
    # split on unescaped pipes
    parts = re.split(r"(?<!\\)\|", line)
    return [p.strip() for p in parts]


NUM = re.compile(r"(?<![0-9A-Za-z_#:./])(\d{4,5})(?:\s*[-–]\s*(\d{4,5}))?(?![0-9A-Za-z_])")


def cites(text):
    """list of (first, second_or_None) primer-number citations with first > 5758 or second > 5758."""
    out = []
    for m in NUM.finditer(text):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        if a > 5758 and a < 10000 or (b and 5758 < b < 10000):
            if text[max(0, m.start() - 4): m.start()] == "RFC ":
                continue
            out.append((a, b))
    return out


old_reg, new_reg = show(OLD, REG).split("\n"), show(NEW, REG).split("\n")
pri_old = show(OLD, PRI).split("\n")
pri_new = show(NEW, PRI).split("\n")
print(f"primer lines at {OLD}: {len(pri_old) - 1}; at {NEW}: {len(pri_new) - 1}; identical: {pri_old == pri_new}")


def s4_rows(lines):
    rows = {}
    in4 = False
    for i, ln in enumerate(lines):
        if ln.startswith("## 4."):
            in4 = True
        elif ln.startswith("## 5."):
            in4 = False
        if in4 and ln.startswith("| APD-"):
            c = cells(ln)
            rows.setdefault(c[1], []).append((i + 1, c[5] if len(c) > 5 else None))
    return rows


r_old, r_new = s4_rows(old_reg), s4_rows(new_reg)
rows_changed = 0
cit_changed = num_changed = 0
blank_cit = blank_num = 0
for rid in sorted(set(r_old) | set(r_new)):
    o = r_old.get(rid, [])
    n = r_new.get(rid, [])
    if len(o) != 1 or len(n) != 1:
        if o != n:
            print(f"  {rid}: rows old={len(o)} new={len(n)} (added/duplicated)")
        continue
    (lo, co), (ln_, cn) = o[0], n[0]
    if co == cn:
        continue
    rows_changed += 1
    oc, nc = cites(co or ""), cites(cn or "")
    # changed citations: those in old not in new (multiset)
    gone = list((Counter(oc) - Counter(nc)).elements())
    cit_changed += len(gone)
    num_changed += sum(1 if b is None else 2 for a, b in gone)
    blanks = []
    for a, b in gone:
        bl = [x for x in (a, b) if x and not pri_old[x - 1].strip()]
        blanks.append(bl)
        if bl:
            blank_cit += 1
            blank_num += len(bl)
    print(f"  {rid:16} L{ln_:<5} {co!r:>28} -> {cn!r:28} changed={gone} blank_old={blanks}")
print(f"§4 Primer cells: {rows_changed} rows changed; {cit_changed} citations ({num_changed} numbers) replaced; "
      f"{blank_cit} citations ({blank_num} numbers) whose OLD number was a blank primer line")

# Prose: every line outside §4 Primer cells whose in-range numbers changed
print("\nprose / non-§4-cell changes:")
sm = difflib.SequenceMatcher(a=old_reg, b=new_reg, autojunk=False)
p_cit = p_num = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    olds, news = old_reg[i1:i2], new_reg[j1:j2]
    for k in range(max(len(olds), len(news))):
        a = olds[k] if k < len(olds) else ""
        b = news[k] if k < len(news) else ""
        # skip §4 table rows (handled above) -- but keep their non-Primer columns? only Primer column counted
        if a.startswith("| APD-") and b.startswith("| APD-"):
            ca, cb = cells(a), cells(b)
            # compare all non-Primer columns
            a_txt = " ".join(ca[:5] + ca[6:])
            b_txt = " ".join(cb[:5] + cb[6:])
        else:
            a_txt, b_txt = a, b
        oc, nc = Counter(cites(a_txt)), Counter(cites(b_txt))
        gone = list((oc - nc).elements())
        came = list((nc - oc).elements())
        if gone or came:
            print(f"  old L{i1 + k + 1} / new L{j1 + k + 1}: gone={gone} came={came}")
print("(prose counts need hand reading: a 'gone' number that was a correction vs. text simply rewritten)")
