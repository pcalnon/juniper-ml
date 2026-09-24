#!/usr/bin/env python3
"""Lane A, claim 10: does any primer line the defect register cites still hold the same text?

Reads (never writes) the juniper-ml worktree. Compares the WORKTREE primer (with the uncommitted
correction) against ``git show HEAD:<primer>`` line by line.

1. Whole-file proof: for every HEAD line n, worktree line n == HEAD line n, or == HEAD line n
   (right-stripped) + the E.1 marker. Anything else is a MOVED/CHANGED line.
2. Register cites: every line number in the register's ``Primer`` fields -- the 14 detail rows
   (``| **Primer** | ... |``) and the ``Primer`` column of every §4 table -- expanded over ranges,
   checked against (1). Section labels (``I.5``, ``II.6``, ``§8.8.3.1``) are stripped first.
3. Prose sweep: any other ``line(s) N`` / ``(N, M)`` citation in the register that is not in a
   Primer field, reported separately so a reader can see what the Primer-field parse did not cover.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map")
PRIMER_REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
REGISTER = WT / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
MARKER = " **[Corrected: E.1](#e1-artifact-validator)**"

head_text = subprocess.run(["git", "-C", str(WT), "show", f"HEAD:{PRIMER_REL}"], check=True, capture_output=True, text=True).stdout
wt_text = (WT / PRIMER_REL).read_text(encoding="utf-8")
head = head_text.split("\n")
wt = wt_text.split("\n")
if head and head[-1] == "":
    head = head[:-1]
if wt and wt[-1] == "":
    wt = wt[:-1]

# ---- 1. whole-file proof -------------------------------------------------------------
status: dict[int, str] = {}
for n, old in enumerate(head, start=1):
    new = wt[n - 1] if n - 1 < len(wt) else None
    if new == old:
        status[n] = "same"
    elif new is not None and new == old.rstrip() + MARKER:
        status[n] = "marker-appended"
    else:
        status[n] = "CHANGED"
changed = [n for n, s in status.items() if s == "CHANGED"]
marked = [n for n, s in status.items() if s == "marker-appended"]
appendix_start = next((i for i, ln in enumerate(wt, start=1) if ln.startswith("## Appendix E")), None)
print(f"HEAD primer lines: {len(head)}; worktree lines: {len(wt)}; appendix heading at worktree line {appendix_start}")
print(f"whole-file: {len(head) - len(changed) - len(marked)} identical, {len(marked)} marker-appended {marked}, {len(changed)} CHANGED {changed[:20]}")
print(f"worktree lines after HEAD's last line: {len(wt) - len(head)} (first extra line {len(head) + 1!r}: {wt[len(head)]!r})")

# ---- 2. register Primer fields --------------------------------------------------------
reg = REGISTER.read_text(encoding="utf-8").split("\n")
PIPE = re.compile(r"(?<!\\)\|")


def cells(row: str) -> list[str]:
    parts = PIPE.split(row.strip())
    return [c.strip() for c in parts[1:-1]] if row.strip().startswith("|") else []


primer_fields: list[tuple[int, str, str]] = []  # (register line, row id, primer cell)
i = 0
while i < len(reg):
    row = reg[i]
    c = cells(row)
    if c and c[0] == "**Primer**" and len(c) >= 2:
        # detail table: find the entry id from the nearest heading above
        h = i
        while h >= 0 and not reg[h].startswith("#"):
            h -= 1
        rid = re.search(r"APD-[A-Z]+-\d+[a-z]?", reg[h]) if h >= 0 else None
        primer_fields.append((i + 1, rid.group(0) if rid else reg[h][:40], c[1]))
        i += 1
        continue
    if c and "Primer" in c and c[0] in ("ID",):
        col = c.index("Primer")
        j = i + 2  # skip the separator row
        while j < len(reg) and reg[j].strip().startswith("|"):
            rc = cells(reg[j])
            if len(rc) > col:
                primer_fields.append((j + 1, rc[0], rc[col]))
            j += 1
        i = j
        continue
    i += 1

SECTION = re.compile(r"§\s*[\d.]+|\b[IVX]+\.\d+(?:\.\d+)*\b|\b[A-E]\.\d+(?:\.\d+)*\b|\bII?I?\b")
NUM_RANGE = re.compile(r"(?<![\w.#-])(\d{1,5})(?:\s*[-–]\s*(\d{1,5}))?(?![\w.])")


def cited_numbers(cell: str) -> list[int]:
    text = SECTION.sub(" ", cell)
    text = re.sub(r"`[^`]*`", " ", text)  # code spans (file:line of SOURCE code, not primer lines)
    text = re.sub(r"\([^)]*(?:juniper|\.py|#)[^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)  # markdown links
    out: list[int] = []
    for a, b in NUM_RANGE.findall(text):
        lo = int(a)
        hi = int(b) if b else lo
        if hi < lo or hi - lo > 60:
            continue
        out.extend(range(lo, hi + 1))
    return out


all_cited: dict[int, list[str]] = {}
print(f"\nPrimer fields parsed: {len(primer_fields)}")
for regline, rid, cell in primer_fields:
    nums = cited_numbers(cell)
    for n in nums:
        all_cited.setdefault(n, []).append(f"{rid}@R{regline}")
    if not nums:
        print(f"  (no line number) R{regline} {rid}: {cell[:120]!r}")

bad = {n: who for n, who in all_cited.items() if n > len(head) or status.get(n) == "CHANGED"}
hit_marked = {n: who for n, who in all_cited.items() if status.get(n) == "marker-appended"}
print(f"distinct primer lines cited in Primer fields: {len(all_cited)} (min {min(all_cited)}, max {max(all_cited)})")
print(f"  cited lines beyond HEAD's end or CHANGED: {len(bad)} {sorted(bad)[:20]}")
print(f"  cited lines that gained the marker (same line, text + suffix): {sorted(hit_marked)} -> {hit_marked}")

# ---- 3. prose sweep outside Primer fields -----------------------------------------------
field_lines = {regline for regline, _, _ in primer_fields}
PROSE = re.compile(r"\b(?:primer\b[^.|]{0,80}?\blines?|\blines?)\s+(\d{2,5}(?:\s*[-–]\s*\d{2,5})?(?:\s*(?:,|and)\s*\d{2,5}(?:\s*[-–]\s*\d{2,5})?)*)", re.I)
PAREN = re.compile(r"\((\d{3,5}(?:\s*[-–]\s*\d{2,5})?(?:\s*,\s*\d{3,5}(?:\s*[-–]\s*\d{2,5})?)+)\)")
prose_cited: dict[int, list[int]] = {}
for k, ln in enumerate(reg, start=1):
    if k in field_lines:
        continue
    for m in list(PROSE.finditer(ln)) + list(PAREN.finditer(ln)):
        for a, b in re.findall(r"(\d{2,5})(?:\s*[-–]\s*(\d{2,5}))?", m.group(1)):
            lo = int(a)
            hi = int(b) if b else lo
            if hi < lo or hi - lo > 60:
                continue
            for n in range(lo, hi + 1):
                prose_cited.setdefault(n, []).append(k)
prose_only = {n: ks for n, ks in prose_cited.items() if n not in all_cited}
bad_prose = {n: ks for n, ks in prose_cited.items() if n > len(head) or status.get(n) == "CHANGED"}
print(f"\nprose citations outside Primer fields: {len(prose_cited)} distinct numbers; {len(prose_only)} not also in a Primer field")
print(f"  prose-cited numbers beyond HEAD's end or CHANGED: {sorted(bad_prose)}")
print(f"  prose-only numbers (sample): {sorted(prose_only)[:40]}")

ok = not changed and not bad and appendix_start is not None and appendix_start > len(head)
print("\nVERDICT:", "NO LINE BEFORE APPENDIX E MOVED; every cited number holds HEAD's text (modulo the appended marker)" if ok else "FAIL")
sys.exit(0 if ok else 1)
