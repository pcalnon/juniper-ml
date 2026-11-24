#!/usr/bin/env python3
"""2026-09-10_repair_cascor_demo_concat.py -- unstick two documents concatenated onto one line.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc repair (documentation structural integrity)
Author: Paul Calnon
License: MIT License

THE DAMAGE

`notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md:1046` reads

    # In _reset_state_and_history() or a network reset method:# Juniper Cascor Concurrency

That is TWO documents welded onto one line. The first half is this file's own idiom -- a
Python comment naming the method a snippet belongs in, exactly as at :350, :354 and :477,
each inside a well-formed ```python block. The second half, `# Juniper Cascor Concurrency`,
is the H1 of a DIFFERENT document that was appended here.

The ```python fence opened at :1045 therefore never receives its closer, and under
CommonMark it runs to the next bare ``` at :1205 -- swallowing **161 lines** of the
appended document, including ten H2 headings, and rendering them as Python on github.com.

WHY IT WAS NOT FOUND EARLIER

The screen's pre-2026-09-10 fence walk was a boolean toggle, which mis-modelled this file in
both directions: the 2026-09-09 review reported its damage at `:1454` ("swallowing the last
~97 lines"), and round 2 corrected that to "the toggle slips at :1200" and concluded the
file was BALANCED under CommonMark. Balanced it is -- the fence at :1045 does eventually
close at :1205. Balance was the wrong question. The right one is which lines land inside a
block, and 161 of them do.

Found only after the walker was made length- and info-string-aware, which is why this file
sat inside the set an Overtoad was asked to ratify as benign.

THE REPAIR

Split the line at the seam and close the fence:

    # In _reset_state_and_history() or a network reset method:
    ```
    <blank>
    # Juniper Cascor Concurrency

Nothing is deleted and no wording changes; three lines are inserted and one is split. The
Python block keeps the comment it actually contains, and the appended document returns to
prose.

Usage:
    python util/ad-hoc/2026-09-10_repair_cascor_demo_concat.py          # dry run
    python util/ad-hoc/2026-09-10_repair_cascor_demo_concat.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TARGET = Path("notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md")
FENCE_LINE = 1045                      # 1-based: the ```python opener
CONCAT_LINE = 1046                     # 1-based: the welded line
LEFT = "# In _reset_state_and_history() or a network reset method:"
RIGHT = "# Juniper Cascor Concurrency"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="write the file (default: dry run)")
    args = ap.parse_args(argv)

    lines = TARGET.read_text(encoding="utf-8").split("\n")

    opener = lines[FENCE_LINE - 1]
    welded = lines[CONCAT_LINE - 1]
    if opener.strip() != "```python":
        print(f"line {FENCE_LINE} is {opener!r}, expected '```python' -- refusing", file=sys.stderr)
        return 2
    if welded != LEFT + RIGHT:
        print(f"line {CONCAT_LINE} is {welded!r},\n  expected {LEFT + RIGHT!r} -- refusing", file=sys.stderr)
        return 2

    replacement = [LEFT, "```", "", RIGHT]
    print(f"{TARGET}:{CONCAT_LINE}\n")
    print(f"  - {welded}")
    for r in replacement:
        print(f"  + {r}")

    if not args.apply:
        print("\ndry run -- pass --apply to write")
        return 0

    lines[CONCAT_LINE - 1:CONCAT_LINE] = replacement
    TARGET.write_text("\n".join(lines), encoding="utf-8")
    print(f"\napplied: {TARGET} now has {len(lines)} lines (+3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
