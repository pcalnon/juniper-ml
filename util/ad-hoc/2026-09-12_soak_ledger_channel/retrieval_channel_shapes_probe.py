#!/usr/bin/env python3
"""What does the WIRED scoring path return for ledger-shaped and pattern-shaped inputs?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 10

Why
---
Sec 10 of that note says the three false-positive mechanisms are code defects in
`util/soak_run_probe.py`'s `retrieval_channel` and in the ad-hoc screen's `scan()`, and that
hardening them "belongs in its own PR". `foreign` is already fixed. `filename` is explicitly an
owner decision (the retrieval standard). That leaves `ledger`.

MEASURE BEFORE CLAIMING. This does not assert a defect -- it feeds `retrieval_channel` a set of
realistic tool-input shapes and prints what it actually returns, so the defect (if any) is a
measurement rather than an inference. Each shape is labelled with what a correct scorer SHOULD
say, from Sec 3's four-mechanism table.

Read-only: imports the module and calls one pure function. Touches no repo state.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
POINTER = "docs/REFERENCE.md#ecosystem-compatibility"
LEDGER = "reports/soak/pointer_follow_soak.jsonl"

# (label, tool_inputs, what a correct scorer should say, which Sec 3 class)
SHAPES: list[tuple[str, list, bool, str]] = [
    (
        "opened our copy by name",
        [{"command": "sed -n '145,175p' docs/REFERENCE.md"}],
        True, "content",
    ),
    (
        "grep -rn in our repo, pointer named in NO input",
        [{"command": "grep -rn 3001 docs/"}],
        # CORRECTED 2026-09-12: this row's expectation was MINE and it was wrong.
        # The input never contains `docs/REFERENCE.md`, so an inputs-only scorer
        # returning False is correct. The first run of this probe reported it as a
        # disagreement -- an instrument defect in the instrument built to find
        # instrument defects.
        False, "correctly not a hit; the doc is named in no input",
    ),
    (
        "sibling repo's copy, foreign cd",
        [{"command": "cd /home/u/Juniper/juniper-deploy && grep -rn 3001 docs/REFERENCE.md"}],
        False, "foreign",
    ),
    (
        "ecosystem-parent cwd, qualified path to OURS",
        [{"command": "cd /home/u/Juniper && sed -n '1,5p' juniper-ml/docs/REFERENCE.md"}],
        True, "content (the 51.2% regression case)",
    ),
    (
        "READ THE LEDGER, naming the doc as a grep PATTERN",
        [{"command": f'grep -n "docs/REFERENCE.md" {LEDGER}'}],
        False, "ledger -- nothing of the pointer document was read",
    ),
    (
        "READ THE LEDGER by absolute path, doc named as pattern",
        [{"command": f"grep -rn 'docs/REFERENCE.md' /home/u/Juniper/juniper-ml/{LEDGER}"}],
        False, "ledger",
    ),
    (
        "ledger named in a Read tool input, doc in the pattern field",
        [{"file_path": LEDGER, "pattern": "docs/REFERENCE.md"}],
        False, "ledger",
    ),
    (
        "bare grep PATTERN, no file read at all",
        [{"command": "grep -rn 'docs/REFERENCE.md' ."}],
        # DELIBERATELY LEFT TRUE. Whether merely NAMING the path counts is the
        # retrieval standard -- owner decision, pinned by
        # test_pointer_path_in_a_command_arg_currently_counts_as_a_hit.
        True, "owner-gated: naming != reading, but that is not ours to decide",
    ),
    (
        "NEGATIVE CONTROL -- ledger read AND a qualified read of OURS, one command",
        [{"command": f"grep -n x {LEDGER} && sed -n '1,5p' juniper-ml/docs/REFERENCE.md"}],
        # This is the shape that must NOT regress. Discarding a whole input on a
        # contextual signal is what produced the 51.2% headline; the ledger guard is
        # per-occurrence for exactly that reason.
        True, "a genuine qualified read survives a ledger read in the same command",
    ),
]


def load():
    spec = importlib.util.spec_from_file_location(
        "soak_run_probe", ROOT / "util" / "soak_run_probe.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["soak_run_probe"] = mod          # @dataclass et al need this
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = load()
    print(f"pointer = {POINTER}\n")
    print(f"{'shape':<52} {'scored':>7} {'should':>7}  verdict")
    print("-" * 96)
    disagreements = 0
    for label, inputs, should, why in SHAPES:
        got = mod.retrieval_channel({"tool_inputs": inputs}, POINTER)
        hit = got["pointer_doc_referenced"]
        agree = hit == should
        if not agree:
            disagreements += 1
        print(f"{label:<52} {str(hit):>7} {str(should):>7}  "
              f"{'ok' if agree else 'DISAGREES'}   [{why}]")
    print("-" * 96)
    print(f"{disagreements} shape(s) disagree with the Sec 3 classification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
