"""
Write the four mutants the guard 1.4.0 builder reported as survivors (M07, M33, M40, M41) as SCRATCH copies of the
1.4.0 guard, with the builder's own mutation strings, so a validator can run kill rows against them (validator JL1).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_flood4r2_r18-guard_mutants.py (the builder's helper; its strings are copied here),
         util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_probe.py

Usage: python3 <this file> <pristine guard copy> <out dir>
Never touches the carrier or any tracked file: it reads the pristine copy and writes mut_<ID>.py beside it, checks
each mutation applied exactly once, and prints the sha256 of the pristine copy before and after.
"""

import hashlib
import sys
from pathlib import Path

MUTANTS = [
    ("M07", "            elif quoted == '\"' and c == \"$\" and nxt == \"(\":", "            elif quoted == 'x' and c == \"$\" and nxt == \"(\":"),
    ("M41", "            if s.startswith(\"<<<\", j):  # a here-string, not a here-document\n                j += 3", "            if s.startswith(\"<<<<\", j):  # a here-string, not a here-document\n                j += 3"),
    ("M33", '    if ch == "$" and nxt == "\'":\n        return _ansi_c_end(s, j + 2)', '    if ch == "$" and nxt == "x":\n        return _ansi_c_end(s, j + 2)'),
    ("M40", "        if key in self._scanned:  # the two readings meet the same nested text; one scan judges it\n            return", "        if key in self._scanned and False:  # the two readings meet the same nested text; one scan judges it\n            return"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list) -> int:
    pristine = Path(argv[0])
    out = Path(argv[1])
    before = sha(pristine)
    text = pristine.read_text()
    for mid, old, new in MUTANTS:
        count = text.count(old)
        if count != 1:
            print("%s: the old text occurs %d times, not applied" % (mid, count))
            continue
        target = out / ("mut_%s.py" % mid)
        target.write_text(text.replace(old, new))
        print("%s -> %s sha256 %s" % (mid, target.name, sha(target)[:16]))
    after = sha(pristine)
    print("pristine sha256 before %s after %s %s" % (before[:16], after[:16], "UNCHANGED" if before == after else "CHANGED"))
    return 0 if before == after else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
