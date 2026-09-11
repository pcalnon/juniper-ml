#!/usr/bin/env python3
"""Which of §3.E's false-positive mechanisms can actually reach the WIRED channel?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Why this exists
---------------
Work item 4 of
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md``
reads: *"Harden the wired channel (§3.E, 'follow-up not done'). **Two false-positive
mechanisms remain in `util/soak_run_probe.py`** -- the path that scores real runs, not the
unwired screen."*

That is worth checking before writing a hardening PR against it, because the two mechanisms
§3.E leaves open -- a ``grep -rln`` FILENAME LIST, and the soak ledger's own NOTE -- are both
things that arrive in a tool RESULT. ``util/soak_run_probe.py`` reads tool INPUTS only
(§3.D: ``grep -rn tool_result`` across the three soak scripts returns 0), so neither can
reach it; they can reach only the unwired screen
``util/ad-hoc/2026-08-21_soak_probe_evidence.py``, which does scan results.

This drives ``_own_repo_occurrence`` -- the wired decision function -- with each mechanism's
actual command shape and prints what it returns, so the claim is settled by the code rather
than by reading it.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/wired_channel_mechanism_probe.py

Read-only. Loads the module, calls one pure function, touches nothing.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TARGET = REPO_ROOT / "util" / "soak_run_probe.py"
DOC = "docs/REFERENCE.md"

# (label, tool-input command, expected, why)
CASES = [
    ("M1  sibling repo via cd (the P24 shape)",
     "cd /home/pcalnon/Development/python/Juniper/juniper-deploy && grep -rn 3001 .",
     False, "FIXED by ml#1855 + the ordering re-fix"),
    ("M1b sibling named explicitly in the path",
     "sed -n 1,20p juniper-deploy/docs/REFERENCE.md",
     False, "explicit sibling segment outranks everything"),
    ("M1c OURS explicitly, under the ecosystem parent",
     "cd /home/pcalnon/Development/python/Juniper && sed -n 145,175p juniper-ml/docs/REFERENCE.md",
     True, "the false NEGATIVE the ordering re-fix repaired"),
    ("M2  grep -rln filename list",
     "grep -rln per_run_timeout_seconds .",
     False, "OUTPUT-side: the command never names the document"),
    ("M3  the soak ledger's own note",
     "cat reports/soak/pointer_follow_soak.jsonl",
     False, "OUTPUT-side: the command never names the document"),
    ("CTL genuine read of our copy",
     "sed -n 145,175p docs/REFERENCE.md",
     True, "negative control -- if this were False the guard is broken"),
    ("OD7 names our file but does not open it",
     "grep -c per_run_timeout docs/REFERENCE.md",
     True, "owner decision 7, NOT a defect; pinned by test_pointer_path_in_a_command_arg_*"),
]


def main() -> int:
    spec = importlib.util.spec_from_file_location("soak_run_probe", TARGET)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {TARGET}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["soak_run_probe"] = mod
    spec.loader.exec_module(mod)

    print("=" * 92)
    print("§3.E mechanisms vs the WIRED retrieval channel (_own_repo_occurrence)")
    print("=" * 92)
    print(f"{'case':<46} {'scores':<8} {'expect':<8} why")
    bad = 0
    for label, cmd, expected, why in CASES:
        got = mod._own_repo_occurrence([cmd], DOC)
        ok = got == expected
        bad += not ok
        print(f"{label:<46} {str(got):<8} {str(expected):<8} {why}")
        if not ok:
            print(f"{'':<46} ^^ MISMATCH -- the claim in this script's docstring no longer holds")
    print()
    print(f"tool_result references in the three soak scripts: "
          f"{sum((REPO_ROOT / 'util' / f).read_text(encoding='utf-8').count('tool_result') for f in ('soak_run_probe.py', 'soak_next_probe.py', 'soak_ledger.py'))}")
    print()
    if bad:
        print(f"{bad} case(s) diverged from the documented expectation.")
        return 1
    print("CONCLUSION: M2 and M3 cannot reach the wired channel -- it reads tool INPUTS and")
    print("both are tool-RESULT phenomena. The handoff's item 4 (\"two false-positive")
    print("mechanisms remain in util/soak_run_probe.py\") does not hold: they remain in the")
    print("UNWIRED screen. What remains on the wired path is OD7, an owner decision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
