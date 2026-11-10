#!/usr/bin/env python3
"""
Record E-H3's wording follow-up in the turing plan (v1.4.11).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-30
Status: ad-hoc — one-off (the record PR of the "t1" session)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.3's E-H3);
         util/host_state_check.py; util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py;
         util/ad-hoc/2026-10-27_turing_h3_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-30_turing_check_wording_record.py --pr N --sha SHA [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.10 -> 1.4.11. Only from 1.4.10: another version is reported and left alone;
        2. §18's opening paragraph: this session and its handoff, now the arc's main handoff;
        3. §18.3's E-H3, its "check's wording" bullet: the fix, in place of "candidate follow-ups";
  the previous main handoff:  4. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing; 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREV_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-27_turing-h3-passed-c8-installed-owner-steps.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-30_turing-check-wording-fixed-owner-steps.md"
MUTATION = "util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.10 — v1.4.9 plus"
VERSION_NEW = (
    "- **Version**: 1.4.11 — v1.4.10 plus E-H3's wording follow-up: `util/host_state_check.py`'s G-TOOLS kubectl fix "
    "names task D3, and its G-MEM memory message names the speculative pages its figure counts (§18's opening; erratum "
    "E-H3 in §18.3; 2026-10-30). v1.4.10 was v1.4.9 plus"
)

INTRO_OLD = f"The former ran H3 (v1.4.10) once the owner had installed C8; its handoff, `{PREV_HANDOFF}`, is now the arc's main handoff."
INTRO_NEW = (
    f"The former ran H3 (v1.4.10) once the owner had installed C8; its handoff is `{PREV_HANDOFF}`. The \"t1\" session "
    f"(8161e3) landed E-H3's wording follow-up (v1.4.11); its handoff, `{THIS_HANDOFF}`, is now the arc's main handoff."
)

WORDING_OLD = "Both are candidate follow-ups for `util/host_state_check.py`."
WORDING_NEW = (
    "Both were fixed by juniper-ml#@PR@ (`@SHA@`, v1.4.11). The kubectl fix now reads \"task D3 (owner) first: upgrade "
    "Docker Desktop, which installs its own /usr/local/bin/kubectl (decision D7); then task D4: kubectl 1.36.x, which needs "
    "re-planning under the D6 ruling (erratum E-D6)\". On turing that link is the only kubectl on PATH, and it points into "
    "Docker.app, at v1.22.4. The memory message reads \"free + speculative + inactive\"; `util/macvm_ctl.bash` keeps its "
    "own label, whose status block defines \"free\" as Pages free + Pages speculative. `tests/test_host_state_check.py` "
    f"pins both, and `{MUTATION}` kills 4 of 4 mutants through the G1 engine, which still kills 57 of 57."
)

# ---------------------------------------------------------------------------------------------- the handoff

PREV_OLD = '\n\n- **From:** the 2026-10-26/27 session on turing named "cached-enchanting-cosmos-84"'
PREV_NEW = (
    '\n\n- **Continued (2026-10-30, plan v1.4.11).** "t1" (8161e3) landed "Agent next" item 2, the check\'s wording '
    f"(juniper-ml#@PR@). The arc's main handoff is now `{THIS_HANDOFF}`, which carries this file's owner steps forward." + PREV_OLD
)


def edit(text: str, old: str, new: str, done_mark: str, label: str, report: list) -> str:
    if done_mark in text:
        report.append(f"present  {label}")
        return text
    if text.count(old) != 1:
        report.append(f"MISSING  {label}: anchor found {text.count(old)} times")
        return text
    report.append(f"applied  {label}")
    return text.replace(old, new)


def fill(text: str, subs: dict) -> str:
    for key, value in subs.items():
        text = text.replace(key, value)
    return text


def edit_plan(text: str, subs: dict, report: list) -> str:
    if "- **Version**: 1.4.11 —" in text:
        report.append("present  plan: Version line 1.4.11")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.11")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.10 nor 1.4.11")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    return edit(text, WORDING_OLD, fill(WORDING_NEW, subs), "Both were fixed by juniper-ml#", "plan: §18.3 E-H3, the check's wording", report)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--pr", required=True, help="the wording PR's number")
    ap.add_argument("--sha", required=True, help="its merge commit, 8 hex or more")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.pr.isdigit() and re.fullmatch(r"[0-9a-f]{8,40}", args.sha)):
        print("--pr must be a number, --sha 8-40 lower-case hex", file=sys.stderr)
        return 2
    subs = {"@PR@": args.pr, "@SHA@": args.sha[:8]}
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, PREV_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], subs, report)
    edited[PREV_HANDOFF] = edit(edited[PREV_HANDOFF], PREV_OLD, fill(PREV_NEW, subs), "- **Continued (2026-10-30, plan v1.4.11).**", "previous handoff: pointer to its successor", report)
    print("\n".join(report))
    if any(line.startswith("MISSING") for line in report):
        print("nothing written")
        return 1
    changed = [rel for rel in files if edited[rel] != files[rel]]
    if not args.dry_run:
        for rel in changed:
            (args.root / rel).write_text(edited[rel], encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {len(changed)} file(s)" + (f": {', '.join(changed)}" if changed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
