#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.1)
Application: ad-hoc probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: measure P1.1's BLAST RADIUS before it ships.

P1.1 makes ``Logger.set_level()`` effective for emission for the first time. Five live call
sites already call it, and two of them -- ``candidate_unit.py:188`` and ``:297`` -- run on
the construction of every candidate, i.e. in the innermost training loop. If the level they
pass is more verbose than the current effective threshold (INFO), then merely FIXING the
defect switches on records that have been suppressed for the life of the codebase: a volume
and throughput regression delivered by a correctness fix.

This resolves what each site actually passes, and reports whether the fix would open
anything up.

Read-only.
"""
import os
import subprocess
import sys

CASCOR_SRC = "/home/pcalnon/Development/python/Juniper/juniper-cascor/src"

CHILD = r'''
import sys
sys.path.insert(0, "@@CASCOR@@")
from cascor_constants import constants as C

NUM = C._LOGGER_LOG_LEVEL_NUMBERS_DICT
WANT = (
    ("effective threshold today (_LOGGER_LOG_LEVEL_NAME)", "_LOGGER_LOG_LEVEL_NAME"),
    ("candidate_unit.py:188/:297", "_CANDIDATE_UNIT_LOG_LEVEL_NAME"),
    ("cascade_correlation.py:3187", "_CASCADE_CORRELATION_NETWORK_LOG_LEVEL_NAME"),
    ("spiral_problem", "_SPIRAL_PROBLEM_LOG_LEVEL_NAME"),
    ("log_config.py:202 default", "_LOG_CONFIG_LOG_LEVEL_NAME"),
)
for label, const in WANT:
    val = getattr(C, const, None)
    num = NUM.get(val) if isinstance(val, str) else None
    print(f"ROW|{label}|{const}|{val!r}|{num}")
'''


def main():
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    out = subprocess.run([sys.executable, "-c", CHILD.replace("@@CASCOR@@", CASCOR_SRC)],
                         capture_output=True, text=True, env=env, check=False)
    if out.returncode != 0:
        print(out.stderr[-1500:])
        return 2

    rows = []
    for line in out.stdout.splitlines():
        if line.startswith("ROW|"):
            _, label, const, val, num = line.split("|", 4)
            rows.append((label, const, val, None if num == "None" else int(num)))

    baseline = next((n for lbl, _, _, n in rows if lbl.startswith("effective threshold")), None)
    print(f"{'call site':<44} {'constant':<46} {'level':<10} {'num':>4}")
    print("-" * 110)
    for label, const, val, num in rows:
        print(f"{label:<44} {const:<46} {val:<10} {num!s:>4}")
    print("-" * 110)
    print(f"\nEffective emit threshold today: {baseline} (records with level >= {baseline} are emitted)\n")

    opens = [(lbl, val, num) for lbl, _, val, num in rows
             if num is not None and baseline is not None and num < baseline
             and not lbl.startswith("effective threshold")]

    if opens:
        print("!! P1.1 WOULD OPEN NEW RECORDS at these sites -- a volume regression delivered")
        print("   by a correctness fix. Each needs a decision before P1.1 ships:")
        for lbl, val, num in opens:
            print(f"     {lbl}: sets {val} ({num}) < threshold {baseline}")
        return 1

    print("P1.1 opens NOTHING: every live set_level call passes a level at or above the")
    print("current effective threshold, so making the call effective changes no emission")
    print("decision under the default environment. The fix is volume-neutral here.")
    print("\nCaveat: this resolves the DEFAULTS. A caller passing an explicit")
    print("CandidateUnit__log_level_name, or JUNIPER_CASCOR_LOG_LEVEL set in the")
    print("environment, moves both the threshold and the argument together -- but an")
    print("explicit per-object argument more verbose than the global level WOULD now take")
    print("effect where it previously did not. That is the intended behaviour of the fix,")
    print("and it is what P4's per-logger levels build on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
