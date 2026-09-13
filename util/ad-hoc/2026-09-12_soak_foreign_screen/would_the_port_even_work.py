#!/usr/bin/env python3
"""Would porting the wired `foreign` guard to the screen actually catch the real shape?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 4

Why
---
The wired guard `util/soak_run_probe.py::_own_repo_occurrence` decides per occurrence, using the
`cd` target in the SAME tool input as context for unqualified paths. The screen
(`util/ad-hoc/2026-08-21_soak_probe_evidence.py::scan`) processes `tool_use` inputs and
`tool_result` content as SEPARATE blobs, in separate JSONL records.

So before proposing the port, the question is whether the guard can even see what it needs:
Sec 4 records the real P24 shape as `cd .../juniper-deploy && grep -rn 3001 .` -- whose RESULT
lines are relative (`docs/REFERENCE.md:NN:...`), with the `cd` in a different record entirely.

A fix that cannot reach the only instance it exists for is theatre. Measure first.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    srp = load(ROOT / "util" / "soak_run_probe.py", "srp")
    own = srp._own_repo_occurrence
    doc = "docs/REFERENCE.md"

    print("Applying the WIRED guard to blobs shaped like what the SCREEN sees.\n")
    print(f"{'blob (as the screen would pass it)':<62} {'guard':>6}  meaning")
    print("-" * 96)

    cases = [
        # (blob, what it represents, does the guard call it ours?)
        ('{"command": "cd /h/Juniper/juniper-deploy && grep -rn 3001 ."}',
         "tool_use: the REAL P24 command (path never appears)"),
        ('"docs/REFERENCE.md:88:Grafana defaults to 3001"',
         "tool_result of that command -- RELATIVE, no cd in this blob"),
        ('"/h/Juniper/juniper-deploy/docs/REFERENCE.md:88:Grafana 3001"',
         "tool_result, QUALIFIED sibling path"),
        ('{"command": "sed -n 1,5p docs/REFERENCE.md"}',
         "tool_use: genuine read of OUR copy"),
    ]
    for blob, meaning in cases:
        got = own([blob], doc)
        print(f"{blob[:60]:<62} {str(got):>6}  {meaning}")

    print("-" * 96)
    print("""
READ THE SECOND ROW. That is the only form in which the real P24 sibling content reaches
the screen, and the guard calls it OURS -- because the `cd` that makes it foreign lives in a
DIFFERENT JSONL record, which `scan()` has already discarded by the time it sees the result.

So a straight port of the wired guard:
  * WOULD newly suppress a qualified sibling path in a result (row 3), and
  * WOULD NOT suppress the real P24 shape (row 2), the one instance in the corpus.

Catching row 2 needs cross-record state -- carrying the `cd` from a tool_use to the
tool_result that follows it. That is new machinery, not a port, and `scan()` currently holds
no per-record context at all.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
