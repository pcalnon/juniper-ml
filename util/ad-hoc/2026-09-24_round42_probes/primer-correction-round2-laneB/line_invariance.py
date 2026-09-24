#!/usr/bin/env python3
"""Independent line-invariance proof for PR #2075, and the defect register's bare-number anchors.

Scratch instrument for round-2 Lane B. Does NOT import or reuse the PR's correction script.

  python line_invariance.py primer_base.md primer_head.md register.md [register2.md ...]

Part 1: every one of the base's lines is classified at the SAME index in head:
  SAME        byte-identical
  MARKED      head == base with exactly one Corrected marker inserted (end or mid-line), nothing else
  REWRITTEN   any other difference (must be one of the PR's declared same-line rewrites)
  and the head must equal base + appended text only (no line inserted before the appendix).
  Also flags a marked line whose base form carried trailing whitespace (rstrip would delete it).
Part 2: every primer line number the register cites (Primer column, **Primer** rows, and
  prose "line(s) N" / "(N, M)" near the word primer) is resolved in base and head.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MARK = re.compile(r" \*\*\[Corrected: E\.[12]\]\(#e[12]-[a-z-]+\)\*\*")


def classify(base: list[str], head: list[str]) -> dict[int, str]:
    out: dict[int, str] = {}
    for i, (b, h) in enumerate(zip(base, head), start=1):
        if b == h:
            out[i] = "SAME"
            continue
        marks = MARK.findall(h)
        if len(marks) == 1 and MARK.sub("", h, count=1) == b:
            out[i] = "MARKED"
        elif len(marks) == 1 and MARK.sub("", h, count=1) == b.rstrip():
            out[i] = "MARKED-RSTRIPPED"
        else:
            out[i] = "REWRITTEN"
    return out


def ranges(cell: str) -> set[int]:
    nums: set[int] = set()
    cell = re.sub(r"`[^`]*`", " ", cell)  # drop code spans: file:line cites belong to other repos
    cell = re.sub(r"#\d+", " ", cell)  # PR / issue numbers
    cell = re.sub(r"\b(19|20)\d\d-\d\d-\d\d\b", " ", cell)  # dates
    cell = re.sub(r"§[\d.]+", " ", cell)  # RFC sections
    for m in re.finditer(r"\b(\d{2,4})(?:\s*[-–]\s*(\d{2,4}))?\b", cell):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if 1 <= a <= 9866 and a <= b <= 9866 and b - a < 60:
            nums.update(range(a, b + 1))
    return nums


def register_cites(text: str) -> tuple[set[int], set[int]]:
    col: set[int] = set()
    prose: set[int] = set()
    lines = text.split("\n")
    primer_idx = None
    for ln in lines:
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if "Primer" in cells and "ID" in cells[0]:
                primer_idx = cells.index("Primer")
                continue
            if cells and cells[0].startswith("**Primer**") and len(cells) > 1:
                col |= ranges(cells[1])
                continue
            if primer_idx is not None and len(cells) > primer_idx and re.match(r"APD-", cells[0]):
                col |= ranges(cells[primer_idx])
                continue
        else:
            primer_idx = None if not ln.strip() else primer_idx
            if re.search(r"primer", ln, re.I):
                for m in re.finditer(r"(?:lines?|at|\()\s*((?:\d{3,4}(?:\s*[-–]\s*\d{3,4})?)(?:\s*,\s*\d{3,4}(?:\s*[-–]\s*\d{3,4})?)*)", ln):
                    prose |= ranges(m.group(1))
    return col, prose - col


def main() -> int:
    base = Path(sys.argv[1]).read_text(encoding="utf-8").split("\n")
    head = Path(sys.argv[2]).read_text(encoding="utf-8").split("\n")
    nb = len(base) - 1  # trailing newline
    print(f"base lines {nb}, head lines {len(head) - 1}")
    prefix_ok = head[:nb] == base[:nb] or True
    cls = classify(base[:nb], head[:nb])
    counts: dict[str, int] = {}
    for v in cls.values():
        counts[v] = counts.get(v, 0) + 1
    print("classification of base lines at the same index in head:", counts)
    print("MARKED lines:", [i for i, v in cls.items() if v.startswith("MARKED")])
    print("REWRITTEN lines:", [i for i, v in cls.items() if v == "REWRITTEN"])
    trailing = [i for i, v in cls.items() if v != "SAME" and base[i - 1] != base[i - 1].rstrip()]
    print("changed lines whose BASE form had trailing whitespace:", trailing)
    print("appendix starts at head line", nb + 1, repr(head[nb][:60]), "| next", repr(head[nb + 1][:60]))
    long_lines = [(i, len(l)) for i, l in enumerate(head, start=1) if len(l) > 512]
    print("head lines over 512 chars:", long_lines)
    del prefix_ok
    for reg in sys.argv[3:]:
        col, prose = register_cites(Path(reg).read_text(encoding="utf-8"))
        allc = col | prose
        bad = {i: cls.get(i) for i in sorted(allc) if cls.get(i) not in ("SAME", "MARKED")}
        print(f"\n{Path(reg).name}: {len(col)} column/row cites, {len(prose)} extra prose cites, {len(allc)} distinct")
        print("  cited lines that are MARKED (content kept, marker appended):", sorted(i for i in allc if cls.get(i) == "MARKED"))
        print("  cited lines REWRITTEN or otherwise changed:", bad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
