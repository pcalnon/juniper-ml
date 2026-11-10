"""
Flood-4 validation: the two docs-draft lines (#2424, #2432) the carrier takes into REFERENCE.md's Test
Suite Reference. For each, find the draft's own '+' line for the same entry, remove its cross-link, and
compare word-for-word with the carrier's line; also show main's line so the delta is visible.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import difflib
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
CASES = {2424: "- `tests/test_host_state_check.py` -- ", 2432: "  APD-ML-002 (`CascorHeadlineMetricsTest`"}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout


def main() -> int:
    carrier = (HERE / "docs/REFERENCE.md").read_text().splitlines()
    main_lines = git("show", f"{BASE}:docs/REFERENCE.md").splitlines()
    for n, prefix in CASES.items():
        head = f"refs/flood4/pr/{n}"
        mb = git("merge-base", BASE, head).strip()
        diff = git("diff", "-U0", mb, head, "--", "docs/REFERENCE.md")
        plus = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++") and l[1:].startswith(prefix)]
        minus = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---") and l[1:].startswith(prefix)]
        car = [l for l in carrier if l.startswith(prefix)]
        mai = [l for l in main_lines if l.startswith(prefix)]
        print(f"== #{n}: draft +{len(plus)} -{len(minus)}; carrier {len(car)}; main {len(mai)}")
        if len(plus) != 1 or len(car) != 1 or len(mai) != 1:
            print("   unexpected counts")
            continue
        stripped = re.sub(r" \(\[[^\]]+\]\(#[^)]+\)\)", "", plus[0])
        print("   draft line minus its link == carrier line:", stripped == car[0])
        print("   draft's own '-' line == main's line:", (minus[0] == mai[0]) if minus else None)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=mai[0].split(" "), b=car[0].split(" "), autojunk=False).get_opcodes():
            if op != "equal":
                print(f"   main->carrier {op}: [{' '.join(mai[0].split(' ')[i1:i2])}] -> [{' '.join(car[0].split(' ')[j1:j2])}]")
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=plus[0].split(" "), b=car[0].split(" "), autojunk=False).get_opcodes():
            if op != "equal":
                print(f"   draft->carrier {op}: [{' '.join(plus[0].split(' ')[i1:i2])}] -> [{' '.join(car[0].split(' ')[j1:j2])}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
