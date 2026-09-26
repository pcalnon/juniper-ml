#!/usr/bin/env python3
"""Lane B r2: an independent, permissive census of 4-5 digit numbers in the register in (5758, primer_len].

Reports every digit run of length 4-5 in range, with the character before and after it, and flags those the
committed census's regex would exclude, so excluded SHAPES can be read by hand. Also scans for en-dash /
"to" ranges, `L`-prefixed and `PRIMER.md:` shapes, and numbers inside the thousands-grouped form.
"""
import re
import sys
from pathlib import Path

reg_p, primer_p = Path(sys.argv[1]), Path(sys.argv[2])
reg = reg_p.read_text(encoding="utf-8").split("\n")
primer = primer_p.read_text(encoding="utf-8").splitlines()
last = len(primer)
CENSUS = re.compile(r"(?<![\w#:./])(?<!RFC )(\d{4,5})(?![\w]|\.\d)")
ANY = re.compile(r"(?<!\d)(\d{4,5})(?!\d)")

included = set()
for i, line in enumerate(reg):
    for m in CENSUS.finditer(line):
        n = int(m.group(1))
        if 5758 < n <= last:
            included.add((i + 1, m.start()))

excluded = []
for i, line in enumerate(reg):
    for m in ANY.finditer(line):
        n = int(m.group(1))
        if not (5758 < n <= last):
            continue
        if (i + 1, m.start()) in included:
            continue
        before = line[max(0, m.start() - 25): m.start()]
        after = line[m.end(): m.end() + 25]
        excluded.append((i + 1, n, before, after))

print(f"census-included numbers: {len(included)}")
print(f"in-range digit runs the census excludes: {len(excluded)}")
for ln, n, b, a in excluded:
    print(f"  L{ln} {n}: ...{b!r} [{n}] {a!r}...")

print("\n-- shape scans --")
for pat, label in [
    (r"\d{4,5}\s*[–—]\s*\d{4,5}", "en/em-dash range"),
    (r"\bL\d{4,5}\b", "L-prefixed"),
    (r"PRIMER\.md:\d+", "PRIMER.md:NNNN"),
    (r"#L\d+", "#L anchor"),
    (r"\b\d{4,5}\s+to\s+\d{4,5}\b", "'A to B' range"),
    (r"\blines?\s+\d,\d{3}", "thousands-grouped line cite"),
]:
    hits = [(i + 1, m.group(0)) for i, line in enumerate(reg) for m in re.finditer(pat, line)]
    print(f"{label}: {len(hits)}")
    for ln, h in hits[:40]:
        print(f"   L{ln}: {h}")
