#!/usr/bin/env python3
"""
Record the owner's 2026-10-25 rulings (H4's usage report, C2's form, H6) and their two PRs in the turing plan (v1.4.7).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — one-off (the record PR of the "macos dev env setup" session)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§9.3, §18, §18.1, §18.2, §18.3);
         util/mcp_setup.bash (H4); util/host_state_check.py and util/host_state_probe.bash (C2's gate);
         util/ad-hoc/2026-10-25_turing_c9_h6_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-25_turing_rulings_1025_record.py --h4-pr N --h4-sha SHA --h4-mutants K/M \
        --c2-pr N --c2-sha SHA --c2-mutants K/M [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.6 -> 1.4.7. Only from 1.4.6: another version is reported and left alone;
        2. §9.3's G-SEC row: the firewall on and blocking all incoming connections;
        3. §18's opening paragraph: this session and its handoff, now the arc's main handoff;
        4. §18.1 gains the three rulings;
        5. §18.2's H4 row gains the usage-report opt-out;
        6. §18.2's C2 row: the form chosen, the gate landed, the owner's commands;
        7. §18.2's H6 row: the decisions deferred, and how they resume;
        8. §18.3 gains errata E-C2-GATE and E-H6-VALUE;
        9. §18.3 gains erratum E-CUT (the doc-edit scripts across the 0.11.2 cut);
  the previous main handoff:  10. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing; 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREV_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-25_turing-h4-usage-off-c2-block-all-gate-h6-deferred.md"
H4_MUTATION = "util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py"
C2_MUTATION = "util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py"
G1_MUTATION = "util/ad-hoc/2026-10-20_turing_g1_mutation_check.py"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.6 — v1.4.5 plus"
VERSION_NEW = (
    "- **Version**: 1.4.7 — v1.4.6 plus the owner's rulings of 2026-10-25 on H4's usage report, C2's form and H6, and the two "
    "PRs that apply them (§9.3's G-SEC row; §18's opening; §18.1; §18.2's H4, C2 and H6 rows; errata E-C2-GATE, E-H6-VALUE and "
    "E-CUT in §18.3; 2026-10-25). v1.4.6 was v1.4.5 plus"
)

GSEC_OLD = "| G-SEC | SIP and authenticated-root enabled; firewall on; FileVault on;"
GSEC_NEW = "| G-SEC | SIP and authenticated-root enabled; firewall on and blocking all incoming connections (C2's block-all form, 2026-10-25); FileVault on;"

INTRO_OLD = (
    "C9 landed and H6's audit ran in the session after that (v1.4.6), whose handoff, `prompts/thread-handoff_automated-prompts/"
    "HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md`, is now the arc's main handoff."
)
INTRO_NEW = (
    f"C9 landed and H6's audit ran in the session after that (v1.4.6), whose handoff is `{PREV_HANDOFF}`. The owner ruled on "
    "H4's usage report, C2's form and H6 in the next session, \"macos dev env setup\" (v1.4.7), whose handoff, "
    f"`{THIS_HANDOFF}`, is now the arc's main handoff."
)

RULINGS_OLD = "and O-5 becomes the new task H6 (§18.2).\n\n### 18.2 Task status after Session 3"
RULINGS_NEW = (
    "and O-5 becomes the new task H6 (§18.2).\n"
    "- **Three rulings (2026-10-25), asked together in one question.**\n"
    "  - **H4's usage report:** opt out. The entry `util/mcp_setup.bash` writes sets `SERENA_USAGE_REPORTING=false` "
    "(E-H6, E-H6-VALUE; juniper-ml#@H4_PR@).\n"
    "  - **C2's form:** block all incoming connections while nothing inbound is needed, over per-app inbound denies. G-SEC "
    "follows (E-C2-GATE; juniper-ml#@C2_PR@). Revisit when Arc F's VM needs inbound.\n"
    "  - **H6:** deferred. When it resumes, its changes cover every synced host (H6-X3), and the agent makes them, backing up "
    "`mcp.json` and `settings.json` first with the token redacted. SER-P1's order stands: VS Code's Serena entry goes before "
    "E-H4-WHEEL's wheel build.\n"
    "\n### 18.2 Task status after Session 3"
)

H4_OLD = "**`timeout 30 claude mcp list` waits on E-H4-WHEEL** |"
H4_NEW = (
    "**`timeout 30 claude mcp list` waits on E-H4-WHEEL**. Since juniper-ml#@H4_PR@ (`@H4_SHA@`; owner ruling 2026-10-25) the "
    "entry also sets `\"env\": {\"SERENA_USAGE_REPORTING\": \"false\"}`, so Serena sends no usage report (E-H6, E-H6-VALUE). "
    f"`tests/test_mcp_setup.py` has 38 tests, and `{H4_MUTATION}` kills @H4_MUTANTS@ mutants |"
)

C2_PREFIX = "| C2 | **changed** (v1.4.5, owner, RR-11 of the H5 risk analysis) |"
C2_ROW = (
    "| C2 | **form: block all** (owner, 2026-10-25); **gate landed** (AGENT); **apply OWNER** | Application firewall on, stealth "
    "mode on, and **block all incoming connections** while nothing inbound is needed, in place of \"allow signed software\" "
    "(v1.4.5, RR-11 of the H5 risk analysis). The owner chose this form over per-app inbound denies on 2026-10-25. Measured "
    "first with `netstat -anp tcp`: nothing on turing listened beyond loopback except Dropbox's LAN sync (`*.17500`) and "
    "link-local services on the T2 chip's internal interface (`fe80::aede:48ff:…`); there was no sshd and no Screen Sharing. "
    "juniper-ml#@C2_PR@ (`@C2_SHA@`): `util/host_state_probe.bash` captures `socketfilterfw --getblockall`, and G-SEC's firewall "
    "condition passes only when the firewall is on and that capture reports block all; its fix names the missing "
    f"`socketfilterfw` steps (E-C2-GATE). `{C2_MUTATION}` kills @C2_MUTANTS@ mutants. **OWNER**, in a terminal: "
    "`sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on`, then the same with `--setblockall on` and "
    "`--setstealthmode on`; then `python3 util/host_state_check.py --section G-SEC`. On 2026-10-25 the firewall was off "
    "(`State = 0`), block all disabled, stealth off, and downloaded signed software auto-allowed |"
)

H6_PREFIX = "| H6 | **done: audited** (AGENT, the `auditor` agent); **decisions OWNER** |"
H6_PREFIX_NEW = "| H6 | **done: audited** (AGENT, the `auditor` agent); **decisions deferred** (owner, 2026-10-25) |"
H6_APPEND = (
    " The owner deferred the decisions on 2026-10-25 (§18.1). When they resume, the changes cover every synced host and the "
    "agent makes them. SER-P1's order stands: VS Code's Serena entry goes before E-H4-WHEEL's wheel build"
)

ERRATA_ANCHOR = "\n\n## 19. Commit signing for the terminal and the IDEs"
ERRATA = (
    "\n- **E-C2-GATE (C2's gate, against its row).**\n"
    "  - **The sentences.** turing's `socketfilterfw` (macOS 15.7.1) holds these strings. `--getblockall` prints \"Firewall is "
    "set to block all non-essential incoming connections\" when on and \"Firewall has block all state set to disabled.\" when "
    "off (captured 2026-10-25), and it can report an unknown or undefined state. `--getglobalstate`'s State = 2 sentence is "
    "\"Firewall is blocking all non-essential incoming connections\", and the binary logs \"turning on the firewall and "
    "setting global state to blockall\".\n"
    "  - **Not yet observed.** Turning block all on needs the owner's sudo, so no on-state capture exists. The gate accepts "
    "either block-all sentence, and state 1 or 2; the owner's first run settles which appear.\n"
    "  - **Unjudged, not passed.** An unknown or undefined block-all state, or a probe from before the capture, exits 2 under "
    "`--check`, unless the firewall is off, which fails anyway.\n"
    "  - **Stealth.** C2's acceptance has asked for stealth mode since v1.0.0, but G-SEC only reports it, as G1 designed. "
    "Gating it is a one-line change if the owner wants it.\n"
    f"  - **G1's evidence still holds.** `{G1_MUTATION}` kills 57 of 57, C12 among them, because State = 1 with block all on "
    "must still pass.\n"
    "- **E-H6-VALUE (the usage report's opt-out value).** At `949a27ef`, `_send_usage_info` (`src/serena/agent.py:724-737`) "
    "returns early only when `SERENA_USAGE_REPORTING` is exactly `false`, or `CI` or `GITHUB_ACTIONS` is exactly `true`. "
    "`False` or `0` still send the report, so the tests pin the exact string, and `conf/hosts/turing/mcp.json`'s `verified` "
    "record names the check, so a pin bump re-reads it. No checkout on turing had an H4 entry yet, so nothing needed rewriting."
)
CUT_ANCHOR = "so nothing needed rewriting." + ERRATA_ANCHOR
CUT = (
    "so nothing needed rewriting.\n"
    "- **E-CUT (the doc-edit scripts across a release cut).** `util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py`, "
    "`util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py` and `util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py` looked for "
    "their CHANGELOG marker inside `[Unreleased]` only. The 0.11.2 proposal (juniper-ml#2339) moves those entries into "
    "`## [0.11.2]`, after which `--check` reported a pending edit and a plain run would have added each entry again. The record "
    "PR makes each marker count anywhere in the file: the three print \"nothing to do\" before and after the cut, and still "
    "insert into a CHANGELOG without the entry. The proposal held its merge for juniper-ml#@C2_PR@ by cross-session agreement, "
    "so the entries of juniper-ml#@H4_PR@ and juniper-ml#@C2_PR@ ride 0.11.2." + ERRATA_ANCHOR
)

# ---------------------------------------------------------------------------------------------- the handoff

PREV_OLD = "\n\n- **From:** the 2026-10-25 session on turing named \"dev env macos\""
PREV_NEW = (
    "\n\n- **Continued (2026-10-25, plan v1.4.7).** The \"macos dev env setup\" session took this handoff. The owner ruled on "
    "H4's usage report (opt out, juniper-ml#@H4_PR@), C2's form (block all, juniper-ml#@C2_PR@) and H6 (deferred). The arc's "
    f"main handoff is now `{THIS_HANDOFF}`. The owner steps below still stand, C2's now in its block-all form."
    + PREV_OLD
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


def replace_row(text: str, prefix: str, new_row: str, done_mark: str, label: str, report: list) -> str:
    if done_mark in text:
        report.append(f"present  {label}")
        return text
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        report.append(f"MISSING  {label}: {len(hits)} rows start with {prefix!r}")
        return text
    lines[hits[0]] = new_row
    report.append(f"applied  {label}")
    return "\n".join(lines)


def defer_h6(text: str, report: list) -> str:
    """The H6 row keeps its record; its status cell changes and the deferral is appended."""
    label = "plan: §18.2 H6 row"
    if H6_PREFIX_NEW in text:
        report.append(f"present  {label}")
        return text
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(H6_PREFIX)]
    if len(hits) != 1 or not lines[hits[0]].endswith(" |"):
        report.append(f"MISSING  {label}: {len(hits)} rows start with {H6_PREFIX!r}, or the row does not end in ' |'")
        return text
    row = lines[hits[0]]
    lines[hits[0]] = H6_PREFIX_NEW + row[len(H6_PREFIX) : -2] + H6_APPEND + " |"
    report.append(f"applied  {label}")
    return "\n".join(lines)


def edit_plan(text: str, subs: dict, report: list) -> str:
    if "- **Version**: 1.4.7 —" in text:
        report.append("present  plan: Version line 1.4.7")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.7")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.6 nor 1.4.7")
    text = edit(text, GSEC_OLD, GSEC_NEW, "firewall on and blocking all incoming connections (C2's block-all form", "plan: §9.3 G-SEC row", report)
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = edit(text, RULINGS_OLD, fill(RULINGS_NEW, subs), "- **Three rulings (2026-10-25)", "plan: §18.1 the three rulings", report)
    text = edit(text, H4_OLD, fill(H4_NEW, subs), "the entry also sets `\"env\": {\"SERENA_USAGE_REPORTING\"", "plan: §18.2 H4 row", report)
    text = replace_row(text, C2_PREFIX, fill(C2_ROW, subs), "| C2 | **form: block all**", "plan: §18.2 C2 row", report)
    text = defer_h6(text, report)
    text = edit(text, ERRATA_ANCHOR, ERRATA + ERRATA_ANCHOR, "- **E-C2-GATE (", "plan: §18.3 errata E-C2-GATE, E-H6-VALUE", report)
    return edit(text, CUT_ANCHOR, fill(CUT, subs), "- **E-CUT (", "plan: §18.3 erratum E-CUT", report)


def fill(text: str, subs: dict) -> str:
    for key, value in subs.items():
        text = text.replace(key, value)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    for task in ("h4", "c2"):
        ap.add_argument(f"--{task}-pr", required=True, help=f"{task.upper()}'s PR number")
        ap.add_argument(f"--{task}-sha", required=True, help=f"{task.upper()}'s merge commit, 8 hex or more")
        ap.add_argument(f"--{task}-mutants", required=True, help=f"{task.upper()}'s mutation result, K/M")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    subs = {}
    for task in ("h4", "c2"):
        pr, sha, mutants = getattr(args, f"{task}_pr"), getattr(args, f"{task}_sha"), getattr(args, f"{task}_mutants")
        if not (pr.isdigit() and re.fullmatch(r"[0-9a-f]{8,40}", sha) and re.fullmatch(r"\d+/\d+", mutants)):
            print(f"--{task}-pr must be a number, --{task}-sha 8-40 lower-case hex, --{task}-mutants K/M", file=sys.stderr)
            return 2
        killed, total = mutants.split("/")
        key = task.upper()
        subs.update({f"@{key}_PR@": pr, f"@{key}_SHA@": sha[:8], f"@{key}_MUTANTS@": f"{killed} of {total}"})
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, PREV_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], subs, report)
    edited[PREV_HANDOFF] = edit(edited[PREV_HANDOFF], PREV_OLD, fill(PREV_NEW, subs), "- **Continued (2026-10-25, plan v1.4.7).**",
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
