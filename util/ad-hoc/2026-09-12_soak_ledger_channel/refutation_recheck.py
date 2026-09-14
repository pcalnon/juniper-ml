#!/usr/bin/env python3
"""Reconciler re-derivation of Lane B's refutation of the ledger guard.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 3

Lane B returned DO NOT SHIP on the `ledger_target` guard. Its charges are load-bearing enough
that the reconciler re-derives them rather than accepting them. Three claims tested:

  R1  the guard's selector is one hard-coded literal, not a document-identity principle:
      the SAME shape aimed at a non-ledger file still scores `follow`.
  R3  the guard destroys the CANONICAL positive when a `description` metadata field
      happens to mention the ledger -- and every Claude Code tool input carries one.
  R6  the author's own "negative control" passes against the UNFIXED code, i.e. it is
      tautological and could never have caught R3.

Read-only: imports the module, calls pure functions.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = "reports/soak/pointer_follow_soak.jsonl"
DOC = "docs/REFERENCE.md#x"


def load(neutralise_ledger_guard: bool = False):
    """Import soak_run_probe; optionally emulate the PRE-FIX build."""
    spec = importlib.util.spec_from_file_location("srp", ROOT / "util" / "soak_run_probe.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["srp"] = mod
    spec.loader.exec_module(mod)
    if neutralise_ledger_guard:
        # A literal no path can contain collapses `ledger_target` to always-False,
        # which restores exactly the old `if not foreign_cwd: return True`.
        mod._LEDGER_PATH = "\x00NO-SUCH-PATH\x00"
    return mod


def hit(mod, inputs) -> bool:
    return mod.retrieval_channel({"tool_inputs": inputs, "answer": ""}, DOC)[
        "pointer_doc_referenced"
    ]


def main() -> int:
    fixed = load()
    prefix = load(neutralise_ledger_guard=True)

    print("=== R1: is the selector a PRINCIPLE, or one hard-coded literal? ===")
    print("    Same shape -- pointer path as a grep PATTERN -- against three targets:\n")
    for target, label in (
        (LEDGER, "the ledger"),
        ("README.md", "a DIFFERENT document (README)"),
        ("docs/QUICK_START.md", "a DIFFERENT document (QUICK_START)"),
    ):
        cmd = f'grep -n "docs/REFERENCE.md" {target}'
        print(f"    hit={str(hit(fixed, [json.dumps({'command': cmd})])):<5}  {label}")
    print("\n    If the principle were 'a different document was read', all three would")
    print("    agree. They do not: only the hard-coded literal is suppressed.\n")

    print("=== R3: does a `description` field destroy the CANONICAL positive? ===")
    canonical = [json.dumps({"file_path": "docs/REFERENCE.md"})]
    with_desc = [
        json.dumps(
            {
                "file_path": "docs/REFERENCE.md",
                "description": f"compare against {LEDGER}",
            }
        )
    ]
    print(f"    canonical open                     hit={hit(fixed, canonical)}")
    print(f"    same open + description mentioning ledger  hit={hit(fixed, with_desc)}")
    print("    (every Claude Code Bash/Read input carries a `description`)\n")

    print("    Other unqualified shapes sharing ONE input:")
    for cmd in (
        f"cat {LEDGER} && sed -n 10,40p docs/REFERENCE.md",
        f'grep -rn "{LEDGER}" docs/REFERENCE.md',
    ):
        print(f"      hit={str(hit(fixed, [json.dumps({'command': cmd})])):<5}  {cmd}")
    print()

    print("=== R6: is the author's negative control tautological? ===")
    control = [
        json.dumps(
            {
                "command": f"grep -n x {LEDGER} && sed -n '1,5p' juniper-ml/docs/REFERENCE.md",
            }
        )
    ]
    print(f"    post-fix hit={hit(fixed, control)}   pre-fix hit={hit(prefix, control)}")
    print("    Identical under both builds => the control cannot fail => it proves nothing.")
    print("    It uses a QUALIFIED path, the one shape that structurally cannot exhibit")
    print("    the bug, because the ml-segment test returns before the ledger branch.\n")

    print("=== R4 spot-check: evasion and over-fire ===")
    for cmd, note in (
        (f'cd reports/soak && grep -n "docs/REFERENCE.md" pointer_follow_soak.jsonl',
         "relative cd -> guard EVADED"),
        (f'grep -n "docs/REFERENCE.md" {LEDGER}.bak', "a .bak sibling -> OVER-fires"),
        (f'grep -n "docs/REFERENCE.md" /home/x/juniper-deploy/{LEDGER}',
         "ANOTHER repo's ledger -> OVER-fires, repo-blind"),
    ):
        print(f"    hit={str(hit(fixed, [json.dumps({'command': cmd})])):<5}  {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
