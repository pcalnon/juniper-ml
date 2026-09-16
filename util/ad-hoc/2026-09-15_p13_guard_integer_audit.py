#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.3)
Application: ad-hoc probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: prove what P1.3 changes, and what it does not, before the 8 guard integers in
``candidate_unit.py`` are replaced by symbolic constants.

The guards are ``_log_X = self.logger.isEnabledFor(level=N)``, and each gates a block containing
ONLY calls at that level (verified by reading all six blocks). So the correctness criterion is
exact:

    the guard must equal whether the gated call would EMIT.

Two ways to be wrong, and they are not symmetric:

    guard True  while the call discards -> wasted work, no output difference
    guard False while the call emits    -> LOST RECORDS

The three integers in the source, against the canonical table (TRACE=1, VERBOSE=5, DEBUG=10):

    isEnabledFor(level=10)  # DEBUG    -> correct
    isEnabledFor(level=8)   # VERBOSE  -> 8 is not a level at all
    isEnabledFor(level=5)   # TRACE    -> 5 is VERBOSE's number

This computes, for every configured level, the old guard, the new guard, and the emit decision,
and reports where each disagrees. Pure arithmetic over the real table -- no cascor import, so it
runs even while torch is unimportable in JuniperCascor1 (the env moved to Python 3.14 while torch
2.11.0 remains under lib/python3.13/site-packages).
"""
import sys

#: The canonical table (cascor_constants ``_PROJECT_LOG_LEVEL_NUMBER_*``), restated here only so
#: this probe needs no import; equality with the real table is what P1.2's probe established.
LEVELS = {"TRACE": 1, "VERBOSE": 5, "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50, "FATAL": 60}

#: (guard name, integer written today, level the gated calls actually use, count of sites)
SITES = [
    ("_log_debug", 10, "DEBUG", 4),
    ("_log_verbose", 8, "VERBOSE", 2),
    ("_log_trace", 5, "TRACE", 2),
]


def enabled(level_num, configured_num):
    """``Logger.isEnabledFor`` post-P1.1: level >= configured."""
    return level_num >= configured_num


def main():
    print("For each configured level: does the guard agree with whether the gated call emits?\n")
    wasted, lost, changed = [], [], []

    for guard, old_int, call_level, n_sites in SITES:
        new_int = LEVELS[call_level]
        print(f"=== {guard}  ({n_sites} sites)   written: isEnabledFor({old_int})"
              f"   ->   Logger.{call_level} = {new_int}")
        if old_int == new_int:
            print("    the integer is already correct; this is a readability change only\n")
            continue
        print(f"    {'configured':<10} {'old guard':>10} {'new guard':>10} {'call emits':>11}   verdict")
        print(f"    {'-'*10} {'-'*10:>10} {'-'*10:>10} {'-'*11:>11}   {'-'*28}")
        for cname, cnum in LEVELS.items():
            old_g = enabled(old_int, cnum)
            new_g = enabled(new_int, cnum)
            emits = enabled(new_int, cnum)  # the gated call is AT call_level
            verdict = "agree"
            if old_g != new_g:
                changed.append((guard, cname))
                if old_g and not emits:
                    verdict = "OLD wasted work (no output)"
                    wasted.append((guard, cname))
                elif not old_g and emits:
                    verdict = "OLD LOST RECORDS"
                    lost.append((guard, cname))
            print(f"    {cname:<10} {old_g!s:>10} {new_g!s:>10} {emits!s:>11}   {verdict}")
        print()

    print("=" * 74)
    print(f"configured levels where the guard's ANSWER changes : {len(changed)}")
    for g, c in changed:
        print(f"    {g} at configured {c}")
    print(f"\n  of those, OLD did wasted work (no output change) : {len(wasted)}")
    print(f"  of those, OLD LOST RECORDS                       : {len(lost)}")

    if lost:
        print("\n  !! P1.3 CHANGES OUTPUT: the old guard suppressed records that should have emitted.")
        print("     That must be stated in the PR, not buried as a cleanup.")
    else:
        print("\n  => P1.3 is OUTPUT-NEUTRAL. Every disagreement is the old guard opening a block")
        print("     whose calls the emit filter then discarded -- work paid for nothing. No record")
        print("     appears or disappears at any configured level.")
        print("\n     Note this only became true with P1.1: before it, the emit filter read state")
        print("     set_level never wrote, so guard and emit could not be compared at all.")

    print("\n  The level=8 sites: 8 is not in the table, and 8>=c differs from 5>=c only for")
    print("  c in {6,7,8} -- no such level exists, so those two sites are inert. Real, but a")
    print("  readability defect rather than a behavioural one.")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
