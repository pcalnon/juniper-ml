#!/usr/bin/env python3
"""
Record the owner's application of C2 and the gate's narrowing in the turing plan (v1.4.8).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — one-off (the record PR of the "modular-meandering-crayon" session)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.2, §18.3);
         util/host_state_check.py (C2's gate); util/ad-hoc/2026-10-25_turing_rulings_1025_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-26_turing_c2_applied_record.py --c2-pr N --c2-sha SHA --c2-mutants K/M \
        [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.7 -> 1.4.8. Only from 1.4.7: another version is reported and left alone;
        2. §18's opening paragraph: this session and its handoff, now the arc's main handoff;
        3. §18.2's C2 row: its status cell (applied);
        4. §18.2's C2 row: the owner's commands become the on-state record and the narrowing;
        5. erratum E-C2-GATE: "The sentences" gives the getter's observed on-sentence;
        6. erratum E-C2-GATE: "Not yet observed" becomes the observation, the allow-signed note and the owner's checkout;
  the previous main handoff:  7. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing; 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREV_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md"
C2_MUTATION = "util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.7 — v1.4.6 plus"
VERSION_NEW = (
    "- **Version**: 1.4.8 — v1.4.7 plus the owner's application of C2 and the gate's narrowing to the block-all sentence "
    "turing printed (§18's opening; §18.2's C2 row; erratum E-C2-GATE in §18.3; 2026-10-26). v1.4.7 was v1.4.6 plus"
)

INTRO_OLD = f"whose handoff, `{PREV_HANDOFF}`, is now the arc's main handoff."
INTRO_NEW = (
    f"whose handoff is `{PREV_HANDOFF}`. The owner applied C2 during the next session, \"modular-meandering-crayon\" (v1.4.8), "
    f"which narrowed G-SEC's firewall condition to the sentence turing printed; its handoff, `{THIS_HANDOFF}`, is now the arc's "
    "main handoff."
)

C2_CELL_OLD = "| C2 | **form: block all** (owner, 2026-10-25); **gate landed** (AGENT); **apply OWNER** |"
C2_CELL_NEW = "| C2 | **done: applied** (OWNER, 2026-10-26); form: block all (owner, 2026-10-25); **gate landed, then narrowed** (AGENT) |"

C2_TAIL_OLD = (
    "**OWNER**, in a terminal: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on`, then the same with "
    "`--setblockall on` and `--setstealthmode on`; then `python3 util/host_state_check.py --section G-SEC`. On 2026-10-25 the "
    "firewall was off (`State = 0`), block all disabled, stealth off, and downloaded signed software auto-allowed |"
)
C2_TAIL_NEW = (
    "On 2026-10-25 the firewall was off (`State = 0`), block all disabled, stealth off, and downloaded signed software "
    "auto-allowed. **Applied** by the owner on 2026-10-26, between 08:44Z and 08:47Z: `--getglobalstate` reports \"Firewall is "
    "blocking all non-essential incoming connections. (State = 2)\", `--getblockall` \"Firewall is blocking all non-essential "
    "incoming connections.\" and `--getstealthmode` \"Firewall stealth mode is on\"; both allow-signed settings stay ENABLED. "
    "G-SEC's firewall condition passes: in the owner's run at 08:47:40Z, from a primary checkout that predates juniper-ml#2338 "
    "and so judged the state alone, and on `main`'s gate at 08:48:50Z. juniper-ml#@C2_PR@ (`@C2_SHA@`) narrows the gate to "
    f"`--getblockall`'s own sentence, and `{C2_MUTATION}` now kills @C2_MUTANTS@ mutants (E-C2-GATE) |"
)

SENT_OLD = (
    "`--getblockall` prints \"Firewall is set to block all non-essential incoming connections\" when on and \"Firewall has block "
    "all state set to disabled.\" when off (captured 2026-10-25), and it can report an unknown or undefined state."
)
SENT_NEW = (
    "`--getblockall` prints \"Firewall is blocking all non-essential incoming connections.\" when on (observed 2026-10-26) and "
    "\"Firewall has block all state set to disabled.\" when off (captured 2026-10-25), and it can report an unknown or undefined "
    "state. v1.4.7 gave \"Firewall is set to block all non-essential incoming connections\" as the on-sentence. The strings place "
    "it beside \"Block all DISABLED!\", the shape of `--setblockall`'s on and off confirmations, and the getter never printed it."
)

OBS_OLD = (
    "  - **Not yet observed.** Turning block all on needs the owner's sudo, so no on-state capture exists. The gate accepts either "
    "block-all sentence, and state 1 or 2; the owner's first run settles which appear.\n"
)
OBS_NEW = (
    "  - **Observed (2026-10-26).** Once the owner applied C2, `--getglobalstate` printed \"Firewall is blocking all non-essential "
    "incoming connections. (State = 2)\", `--getblockall` the same sentence without the state, and `--getstealthmode` \"Firewall "
    "stealth mode is on\". The \"set to block all\" sentence never appeared, so juniper-ml#@C2_PR@ (`@C2_SHA@`) accepts only the "
    "getter's: a capture holding the setter's goes unjudged (exit 2 under `--check`), unless the firewall is off. B7 of "
    f"`{C2_MUTATION}` now re-accepts the setter's sentence, and B12 re-introduces v1.4.7's premise; it kills @C2_MUTANTS@ "
    "mutants. State 1 still passes. Block all left the global state at 2, as the binary's \"setting global state to blockall\" "
    "suggests, but the gate judges block all by its own capture, and G1's C12 pins state 1.\n"
    "  - **Allow-signed.** Both allow-signed settings stayed ENABLED. Under block all only essential services (configd, "
    "mDNSResponder, racoon) take incoming connections, so the settings matter again only if block all is turned off for Arc F's "
    "VM: revisit them then.\n"
    "  - **The owner's checkout.** The owner's own G-SEC run came from a primary checkout that predates juniper-ml#2338, so it "
    "judged the state alone. C8's step 1 (`git pull --ff-only origin main`) brings the block-all gate there.\n"
)

# ---------------------------------------------------------------------------------------------- the handoff

PREV_OLD = "\n\n- **From:** the 2026-10-25 session on turing named \"macos dev env setup\""
PREV_NEW = (
    "\n\n- **Continued (2026-10-26, plan v1.4.8).** The \"modular-meandering-crayon\" session took this handoff. The owner applied "
    "C2 (the firewall on, blocking all, with stealth mode), and juniper-ml#@C2_PR@ narrowed G-SEC's firewall condition to the "
    f"sentence turing printed. The arc's main handoff is now `{THIS_HANDOFF}`. The other owner steps below still stand." + PREV_OLD
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


def edit_plan(text: str, subs: dict, report: list) -> str:
    if "- **Version**: 1.4.8 —" in text:
        report.append("present  plan: Version line 1.4.8")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.8")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.7 nor 1.4.8")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = edit(text, C2_CELL_OLD, C2_CELL_NEW, "| C2 | **done: applied** (OWNER, 2026-10-26)", "plan: §18.2 C2 row, status cell", report)
    text = edit(text, C2_TAIL_OLD, fill(C2_TAIL_NEW, subs), "**Applied** by the owner on 2026-10-26", "plan: §18.2 C2 row, the record", report)
    text = edit(text, SENT_OLD, SENT_NEW, "when on (observed 2026-10-26)", "plan: E-C2-GATE, the sentences", report)
    return edit(text, OBS_OLD, fill(OBS_NEW, subs), "  - **Observed (2026-10-26).**", "plan: E-C2-GATE, the observation", report)


def fill(text: str, subs: dict) -> str:
    for key, value in subs.items():
        text = text.replace(key, value)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--c2-pr", required=True, help="the narrowing PR's number")
    ap.add_argument("--c2-sha", required=True, help="its merge commit, 8 hex or more")
    ap.add_argument("--c2-mutants", required=True, help="the C2 mutation result, K/M")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.c2_pr.isdigit() and re.fullmatch(r"[0-9a-f]{8,40}", args.c2_sha) and re.fullmatch(r"\d+/\d+", args.c2_mutants)):
        print("--c2-pr must be a number, --c2-sha 8-40 lower-case hex, --c2-mutants K/M", file=sys.stderr)
        return 2
    killed, total = args.c2_mutants.split("/")
    subs = {"@C2_PR@": args.c2_pr, "@C2_SHA@": args.c2_sha[:8], "@C2_MUTANTS@": f"{killed} of {total}"}
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, PREV_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], subs, report)
    edited[PREV_HANDOFF] = edit(edited[PREV_HANDOFF], PREV_OLD, fill(PREV_NEW, subs), "- **Continued (2026-10-26, plan v1.4.8).**",
                                "previous handoff: pointer to its successor", report)
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
