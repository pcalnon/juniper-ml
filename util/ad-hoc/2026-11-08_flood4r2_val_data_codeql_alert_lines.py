"""
Print the source line behind each CodeQL alert in a TSV (number, state, path, line) read from a checkout.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (tmp/flood4/BRIEF_VALIDATE_R2.txt); CodeQL prescreen pytestmark predictions

Usage:
    python3 util/ad-hoc/2026-11-08_flood4r2_val_data_codeql_alert_lines.py <alerts.tsv> <checkout root> <path substring>

The last line counts the alerts whose line is a module-level ``pytestmark`` assignment, and the
checkout's test files that carry one, so a "no alert ever fires on pytestmark" reading is a
measured ratio rather than an absence nobody looked for.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PYTESTMARK = re.compile(r"^pytestmark\s*=")


def main(tsv: Path, root: Path, needle: str) -> int:
    on_pytestmark = 0
    shown = 0
    for raw in tsv.read_text(encoding="utf-8").splitlines():
        number, state, path, line = raw.split("\t")
        if needle not in path:
            continue
        shown += 1
        source = root / path
        if not source.is_file():
            print(f"#{number}\t{state}\t{path}:{line}\t(file absent in this checkout)")
            continue
        text = source.read_text(encoding="utf-8").splitlines()
        idx = int(line) - 1
        content = text[idx] if 0 <= idx < len(text) else "(line beyond EOF)"
        if PYTESTMARK.match(content):
            on_pytestmark += 1
        print(f"#{number}\t{state}\t{path}:{line}\t{content[:80]}")
    files_with_mark = sum(1 for p in (root / "juniper_data" / "tests").rglob("*.py") if any(PYTESTMARK.match(ln) for ln in p.read_text(encoding="utf-8").splitlines()))
    print(f"alerts shown: {shown}; alerts on a module-level pytestmark line: {on_pytestmark}; test files with a module-level pytestmark: {files_with_mark}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]))
