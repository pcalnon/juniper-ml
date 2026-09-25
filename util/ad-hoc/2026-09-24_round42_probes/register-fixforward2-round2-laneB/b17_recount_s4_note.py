#!/usr/bin/env python3
"""Lane B r2: recount the section-4 note's figures from history.

#2080 (6aabe4cc -> f2688a95): section-4 `Primer` cells changed -- rows, citations (a range is one), numbers
(both ends); how many OLD citations / numbers landed on a blank line of the primer as it then stood; and the
primer citations (> 5758) it changed OUTSIDE section-4 cells, per line.
e2f87aae (df21367d -> e2f87aae): the same, for the "last 5".
"""
import re
import sys
from pathlib import Path

H = Path(sys.argv[1])
NUM = re.compile(r"(?<![\w#:./])(?<!RFC )(\d{4,5})(?![\w]|\.\d)")


def cites(text: str, last: int):
    """[(first, second_or_None)] for every in-range citation in text; a range 'A-B' is one citation."""
    out = []
    for m in re.finditer(r"(?<![\w#:./])(?<!RFC )(\d{4,5})(?:-(\d{4,5}))?(?![\w]|\.\d)", text):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else None
        if 5758 < a <= last:
            out.append((a, b))
    return out


def s4_rows(lines):
    rows, sec = {}, ""
    for i, l in enumerate(lines):
        if l.startswith("### "):
            sec = l[4:]
        if l.startswith("## 5."):
            break
        if sec[:3] in {f"4.{k}" for k in range(1, 10)} and l.startswith("| APD-"):
            cells = l.split("|")
            rows[cells[1].strip()] = (i + 1, cells[-3])
    return rows


def compare(old_c, new_c, primer_old):
    reg_o = (H / f"reg_{old_c}.md").read_text(encoding="utf-8").split("\n")
    reg_n = (H / f"reg_{new_c}.md").read_text(encoding="utf-8").split("\n")
    p = (H / f"primer_{primer_old}.md").read_text(encoding="utf-8").splitlines()
    last = 9982
    blank = lambda n: n <= len(p) and not p[n - 1].strip()
    ro, rn = s4_rows(reg_o), s4_rows(reg_n)
    rows_changed = cit = nums = blank_cit = blank_num = 0
    for rid, (ln, cell) in ro.items():
        if rid in rn and rn[rid][1] != cell:
            old = cites(cell, last)
            new = cites(rn[rid][1], last)
            if old != new:
                rows_changed += 1
                changed = [c for c in old if c not in new] or old
                cit += len(changed)
                nums += sum(1 if b is None else 2 for a, b in changed)
                blank_cit += sum(1 for a, b in changed if blank(a))
                blank_num += sum(blank(a) + (b is not None and blank(b)) for a, b in changed)
    print(f"{old_c}->{new_c}: s4 Primer cells: {rows_changed} rows, {cit} citations changed ({nums} numbers); old citation's first line blank: {blank_cit} (numbers on blank lines: {blank_num})")
    # outside section-4 cells: per line, the in-range citations that changed
    import difflib
    sm = difflib.SequenceMatcher(a=reg_o, b=reg_n, autojunk=False)
    prose_c = prose_n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        for a, b in zip(reg_o[i1:i2], reg_n[j1:j2]):
            if a.startswith("| APD-") and b.startswith("| APD-"):
                # only the non-Primer part of a section-4 row, and whole rows elsewhere
                in_s4 = a.split("|")[1].strip() in ro and ro[a.split("|")[1].strip()][1] == a.split("|")[-3]
                if in_s4:
                    a = "|".join(a.split("|")[:-3])
                    b = "|".join(b.split("|")[:-3])
            co, cn = cites(a, last), cites(b, last)
            gone = [c for c in co if c not in cn]
            if gone:
                prose_c += len(gone)
                prose_n += sum(1 if y is None else 2 for x, y in gone)
                print(f"   non-cell line: old {gone} -> new {[c for c in cn if c not in co]}  blank(first)={[blank(x) for x, y in gone]}  :: {b[:90]!r}")
    print(f"   outside section-4 cells: {prose_c} citations changed ({prose_n} numbers)")


compare("6aabe4cc", "f2688a95", "6aabe4cc")
compare("df21367d", "e2f87aae", "df21367d")
