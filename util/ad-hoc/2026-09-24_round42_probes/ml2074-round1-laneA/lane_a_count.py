#!/usr/bin/env python3
"""Lane A independent register counter (written without reading register_open_set.py /
register_status_crosscheck.py's parsers).

Counts, per subsection of section 4:
  * table rows whose FIRST cell is an APD id
  * rows whose SECOND cell (the status / title cell) contains '**FIXED'
and lists the section 5.1 verification-row ids and the section 2 status-paragraph ids.

usage: lane_a_count.py <register.md> [--mutate KIND]
  --mutate drop-fixed-marker : remove the first '**FIXED' in section 4 (expect fixed -1, open +1)
  --mutate add-row           : duplicate the last 4.9 row with a fresh id (expect rows +1, open +1)
  --mutate unfix-in-51       : drop the APD-ECO-008 row from 5.1 (expect 5.1 set to lose one id)
"""
from __future__ import annotations

import re
import sys
from collections import Counter, OrderedDict

ID_RE = re.compile(r"APD-[A-Z]+-\d{3}[a-z]?")


def split_cells(line: str) -> list[str]:
    # A markdown table row: strip the outer pipes, split on '|' not preceded by a backslash.
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def main() -> int:
    path = sys.argv[1]
    mutate = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--mutate" else None
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")

    # section boundaries by heading text
    def find(prefix: str) -> int:
        for i, ln in enumerate(lines):
            if ln.startswith(prefix):
                return i
        raise SystemExit(f"heading not found: {prefix}")

    s4 = find("## 4. Full register")
    s5 = find("## 5. Fixed findings")
    s51 = find("### 5.1 ")
    s52 = find("### 5.2 ")
    s2 = find("## 2. Summary")
    s21 = find("### 2.1 ")

    if mutate == "drop-fixed-marker":
        for i in range(s4, s5):
            if "**FIXED" in lines[i] and lines[i].lstrip().startswith("| APD-"):
                lines[i] = lines[i].replace("**FIXED", "**OPENED", 1)
                break
    elif mutate == "add-row":
        last = max(i for i in range(s4, s5) if lines[i].lstrip().startswith("| APD-"))
        lines.insert(last + 1, "| APD-ZZZ-999 | synthetic open row | M | x | — | High |")
        s5 += 1
        s51 += 1
        s52 += 1
    elif mutate == "unfix-in-51":
        for i in range(s51, s52):
            if lines[i].lstrip().startswith("| APD-ECO-008 "):
                del lines[i]
                s52 -= 1
                break

    # --- section 4 rows, per subsection
    sub = None
    per_sub: "OrderedDict[str, list[tuple[str, bool]]]" = OrderedDict()
    all_rows: list[tuple[str, bool, int]] = []
    for i in range(s4, s5):
        ln = lines[i]
        if ln.startswith("### "):
            sub = ln[4:].strip()
            per_sub.setdefault(sub, [])
            continue
        if not ln.lstrip().startswith("|"):
            continue
        cells = split_cells(ln)
        if len(cells) < 2:
            continue
        m = ID_RE.fullmatch(cells[0].replace("†", "").strip())
        if not m:
            continue
        fixed = "**FIXED" in cells[1]
        per_sub.setdefault(sub or "(none)", []).append((m.group(0), fixed))
        all_rows.append((m.group(0), fixed, i + 1))

    ids = [r[0] for r in all_rows]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    fixed_ids = {r[0] for r in all_rows if r[1]}
    open_ids = sorted(set(ids) - fixed_ids)
    print(f"section 4: {len(all_rows)} rows | {len(fixed_ids)} fixed | {len(set(ids)) - len(fixed_ids)} open | duplicates: {dup}")
    primer_rows = primer_fixed = 0
    for name, rows in per_sub.items():
        nf = sum(1 for _, f in rows if f)
        print(f"  {name[:48]:48s} rows={len(rows):3d} fixed={nf:3d} open={len(rows) - nf:3d}")
        if not name.startswith("4.9"):
            primer_rows += len(rows)
            primer_fixed += nf
    post = per_sub.get(next((k for k in per_sub if k.startswith("4.9")), ""), [])
    post_fixed = sum(1 for _, f in post if f)
    print(f"primer (4.1-4.8): rows={primer_rows} fixed={primer_fixed} open={primer_rows - primer_fixed}")
    print(f"post-primer (4.9): rows={len(post)} fixed={post_fixed} open={len(post) - post_fixed}")

    # --- a '**FIXED' anywhere in a 4.x row but NOT in cell 2 (would be missed by a cell-2 parser)
    stray = []
    for i in range(s4, s5):
        ln = lines[i]
        if ln.lstrip().startswith("| APD-"):
            cells = split_cells(ln)
            if "**FIXED" not in cells[1] and "**FIXED" in ln:
                stray.append((i + 1, cells[0]))
    print(f"rows with **FIXED outside cell 2: {stray}")

    # --- section 5.1 verification rows (first cell may hold 'A / B')
    v51: list[str] = []
    for i in range(s51, s52):
        ln = lines[i]
        if ln.lstrip().startswith("| APD-"):
            first = split_cells(ln)[0]
            v51.extend(ID_RE.findall(first))
    print(f"section 5.1: {len(v51)} ids in first cells, {len(set(v51))} unique; dup={[k for k, v in Counter(v51).items() if v > 1]}")

    # --- section 2 status paragraph: the line beginning '**Eighty-one of the 96'
    status_line = next(ln for ln in lines[s2:s21] if ln.startswith("**Eighty-one of the 96") or ln.startswith("**Eighty"))
    pre, _, post_part = status_line.partition("**Post-primer rows**")
    primer_list = ID_RE.findall(pre)
    post_list = ID_RE.findall(post_part.split("— and ")[0])
    print(f"section 2 primer-fixed list: {len(primer_list)} ids ({len(set(primer_list))} unique)")
    print(f"section 2 post-primer fixed list (up to '— and'): {len(post_list)} ids ({len(set(post_list))} unique): {post_list}")
    s2set = set(primer_list) | set(post_list)
    print(f"section 2 union: {len(s2set)}")
    print(f"sets equal? s4fixed==s51: {fixed_ids == set(v51)}  s4fixed==s2: {fixed_ids == s2set}")
    print(f"  s4fixed - s51: {sorted(fixed_ids - set(v51))}  s51 - s4fixed: {sorted(set(v51) - fixed_ids)}")
    print(f"  s4fixed - s2: {sorted(fixed_ids - s2set)}  s2 - s4fixed: {sorted(s2set - fixed_ids)}")
    # primer-fixed ids should all live in 4.1-4.8
    post_ids = {i for i, _ in post}
    print(f"  section-2 primer list ids that are 4.9 rows: {sorted(set(primer_list) & post_ids)}")
    print(f"  section-2 post list ids that are NOT 4.9 rows: {sorted(set(post_list) - post_ids)}")
    print("OPEN:", " ".join(open_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
