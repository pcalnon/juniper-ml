#!/usr/bin/env python3
"""Cite round 39's validation record and handoff from APD-DATA-050's close.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reports/2026-09-15_round-39-consensus/

``APD-CASCOR-007``'s close sets the precedent: when a validation round changes what a row says, the
row names the record. ``APD-DATA-050`` was found by round 1 and its remedy was rewritten by round 2,
so it needs the pointer more than most -- and ``tests/test_thread_handoff_archive.py`` requires any
handoff a top-level note cites to exist in ``prompts/thread-handoff_automated-prompts/``, which is
why the citation and the archived file ship in one PR.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

OLD = (
    "Three new regression tests, each verified to FAIL against the pre-fix generator; 1887 pass. |"
)
NEW = (
    "**The first remedy was itself refuted, before merge.** Judging each point against the median of "
    "the values already ACCEPTED is *absorbing*: a typo in a series' first filing that the ceiling "
    "cannot reach becomes the sole basis, every genuine value is more than a hundredfold away from "
    "it, and nothing is ever accepted again — 0 of 20 genuine counts survive, measured on a real "
    "payload shape. The shipped basis is the **lower median of prior SEEN values**: *prior* rather "
    "than prior-accepted kills the absorbing state, and the *lower* median (always a number some "
    "filing reported, never an interpolation) kills the poisoning the accepted-only rule was "
    "reaching for. All three candidates deliver identical multisets across the 483 in-bounds series "
    "of the cache — the ceiling removes the poisoners before the relative test runs — so the "
    "whole-cache sweep could not separate them and did not validate the wrong one. Four regression "
    "tests, each verified to FAIL against the implementation it replaces; 1888 pass. Found by "
    "round 1 and rewritten by round 2 of the independent-agent validation recorded in "
    "`reports/2026-09-15_round-39-consensus/`, whose handoff is "
    "`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`. |"
)

text = REGISTER.read_text()
if NEW in text:
    print("  --  already applied")
    sys.exit(0)
if text.count(OLD) != 1:
    sys.exit(f"FAIL: found {text.count(OLD)} occurrences of the APD-DATA-050 close tail")

REGISTER.write_text(text.replace(OLD, NEW, 1))
print("  ok  APD-DATA-050 close cites the validation record and the handoff")
