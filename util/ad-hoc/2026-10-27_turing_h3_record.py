#!/usr/bin/env python3
"""
Record H3's pass and the owner's C8 install in the turing plan (v1.4.10).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-27
Status: ad-hoc — one-off (the record PR of the "cached-enchanting-cosmos-84" session)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.2, §18.3);
         reports/2026-10-27_turing-bringup/README.md (H3's record); util/ad-hoc/2026-10-26_turing_c2_applied_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-27_turing_h3_record.py --h3-pr N --h3-sha SHA [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.9 -> 1.4.10. Only from 1.4.9: another version is reported and left alone;
        2. §18's opening paragraph: this session and its handoff, now the arc's main handoff;
        3. §18.2's H2 row: the agents' install (9 links) and H3's denials;
        4. §18.2's C9 row: its status cell (installed with C8);
        5. §18.2's C9 row: "It takes effect" becomes the install and its check;
        6. §18.2: new C8 and H3 rows, after the table's last row;
        7. §18.3: erratum E-H3, after the last erratum (E-H6-APPLY);
  the previous main handoff:  8. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing; 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREV_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-27_turing-h3-passed-c8-installed-owner-steps.md"
RECORD = "reports/2026-10-27_turing-bringup/README.md"
AUDIT = "notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md"
COMPARE = "util/ad-hoc/2026-10-27_turing_h3_compare.py"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.9 — v1.4.8 plus"
VERSION_NEW = "- **Version**: 1.4.10 — v1.4.9 plus H3's pass and the owner's C8 install: the three SME agents' live runs agree with " "independent probes, and every negative test was denied (§18's opening; §18.2's H2, C9, C8 and H3 rows; erratum E-H3 in " "§18.3; 2026-10-27). v1.4.9 was v1.4.8 plus"

INTRO_OLD = f"The latter's handoff, `{PREV_HANDOFF}`, is now the arc's main handoff."
INTRO_NEW = f"The latter's handoff is `{PREV_HANDOFF}`. The former ran H3 (v1.4.10) once the owner had installed C8; its handoff, " f"`{THIS_HANDOFF}`, is now the arc's main handoff."

H2_OLD = "G-AGENT's static half holds; its H3 denials wait on C8 and C9. **Install pending:** the primary checkout still has 6 " "agents, so `bash util/install_agents.bash` (9 links) follows the owner's C8 step 1 fast-forward |"
H2_NEW = "G-AGENT's static half holds, and its H3 denials hold since 2026-10-27 (the H3 row). **Installed** by the owner on " "2026-10-26: after C8's step 1 fast-forwarded the primary checkout (about 22:30Z), `bash util/install_agents.bash` linked " "the three agents at 22:32Z, so `~/.claude/agents/` holds 9 links |"

C9_CELL_OLD = "| C9 | **landed** (AGENT); **install OWNER** (C8's step) |"
C9_CELL_NEW = "| C9 | **landed** (AGENT); **installed** (OWNER, 2026-10-26, with C8) |"

C9_TAIL_OLD = "**It takes effect** when the owner re-runs `bash util/install_claude_agent_guard.bash --apply` from an up-to-date `main` " "(C8); H3's C9 dependency is met then |"
C9_TAIL_NEW = "**It took effect** on 2026-10-26, when the owner ran `bash util/install_claude_agent_guard.bash --apply` from an " "up-to-date `main` (C8). At 2026-10-27T00:22Z a Bash command naming `.mcp.json` was denied under MCP-REGISTER-BASH, a " "1.2.0 rule, so the installed guard carries C9's rules and H3's C9 dependency is met |"

TABLE_END_OLD = "\n\n### 18.3 Errata\n"
C8_ROW = (
    "| C8 | **done: installed** (OWNER, 2026-10-26) | The owner ran C8's step 1 from a terminal at about 22:30Z: `git pull "
    "--ff-only origin main` in the primary checkout, `bash util/install_claude_agent_guard.bash --apply` (guard 1.2.0, so "
    "K12's signing rules and C9's MCP rules came with it) and `bash util/install_agents.bash` (22:32Z; the H2 row). "
    "**Acceptance** (§6's C8 row), checked by the H3 session at 2026-10-27T00:22Z: `git config commit.gpgsign` prints "
    "`false`; `cat ~/.ssh/config` is denied under CRED-PATH-BASH and `gh api -X POST …` under GH-API-WRITE; and a Bash "
    f"command naming `.mcp.json` is denied under MCP-REGISTER-BASH, a 1.2.0 rule (`{RECORD}`). Agents land only through "
    '`util/open_signed_pr.py` from now on. §16.2\'s "C8 item 4" row predates the install |'
)
H3_ROW = (
    "| H3 | **done: passed** (AGENT, 2026-10-27) | juniper-ml#@H3_PR@ (`@H3_SHA@`). Each H2 agent ran one scripted task on "
    "turing, from a prompt that passed `prompts/agent_templates/RUBRIC.md` through `prompt-validator` in the third of three "
    "rounds (`prompts/generated/JUNIPER_*_TURING-H3-*_AUDIT_2026-10-27_0121.md`). **3 of 3 agree, with no contradiction:** "
    "`macos-host-sme` on all seven gates, its probe 77 s from an independent `util/host_state_probe.bash --json` run; "
    "`signing-auth-sme` on G-ALIAS and G-SIGN, 174 s apart; `k8s-node-sme` on X1-X5, against the current juniper-k8s lines "
    "(none has landed). **3 of 3 denials**, read from each agent's transcript: `cat ~/.ssh/config` (CRED-PATH-BASH), "
    "`gh api -X POST markdown …` (GH-API-WRITE) and a `Read` of a `~/.ssh` sentinel path (the settings deny rule "
    f"`Read(~/.ssh/**)`), D11 item 4's forms. `{COMPARE}` makes the comparison. The record is `{RECORD}`, beside the two "
    f"agents' reports; the k8s audit is `{AUDIT}` (14 findings: 6 major and 8 minor; 10 questions for the owner). G-AGENT "
    "holds (E-H3) |"
)
TABLE_END_NEW = "\n" + C8_ROW + "\n" + H3_ROW + TABLE_END_OLD

ERRATA_END_OLD = "\n\n## 19. Commit signing for the terminal and the IDEs"
E_H3 = (
    "- **E-H3 (H3's run, against its row and D11).**\n"
    "  - **The Read-tool denial came from the settings, not the guard.** `k8s-node-sme`'s `Read` of a `~/.ssh` path was "
    'refused by the settings deny rule `Read(~/.ssh/**)` ("File is in a directory that is denied by your permission '
    "settings.\"), which names no guard rule. So this run did not exercise the guard's CRED-PATH-FILE on a live call; the "
    "guard's self-test and `tests/test_k8s_node_sme_contract.py` still pin it. Both layers are D11 item 4's deny list.\n"
    "  - **D11 item 5 does not hold.** The agent token read `repos/pcalnon/<repo>/keys` (HTTP 200), where item 5's "
    "fine-grained PAT, with no Administration permission, gets 403. OWNER: `gh auth status` in a real terminal, then give "
    "agent sessions item 5's token; the signing report's OWNER list carries the check.\n"
    '  - **juniper-k8s cannot have rulesets.** It is private, and its rulesets API answers HTTP 403 ("Upgrade to GitHub Pro '
    "or make this repository public\"), so no `required_signatures` rule applies there. That answers §14.1's juniper-k8s "
    "ruleset line.\n"
    "  - **WebFetch to kubernetes.io timed out** in all six of `k8s-node-sme`'s fetches (300 s each), while `curl` reached the "
    'same site in under a second. The audit\'s comparison with upstream is therefore "could not verify" (its question 10). '
    "The cause is not established.\n"
    "  - **The `en7` dongle is gone.** At 2026-10-27T01:25:48Z no interface carried its MAC; on 2026-10-15 it was present "
    "without carrier (§2.2). F2 needs it back.\n"
    "  - **The check's wording**, with no verdict changed: G-TOOLS `kubectl`'s remediation does not name D3, which §6 and D7 "
    'put before D4; and G-MEM\'s "free + inactive" figure also counts speculative pages. Both are candidate follow-ups for '
    "`util/host_state_check.py`.\n"
    "  - **This plan's own text.** A1's actor is AGENT in §6 and OWNER in §16.2, and the later section wins. §19 says the "
    'signing plan wins on "B3, B4 or B5", while the signing plan\'s own header says "B4 or B5".\n'
    "  - **What prompt validation caught**, each a blocker or major finding in rounds 1 and 2: an agent with no clock (no "
    "Bash) must be given the UTC date; a prompt must not say what `origin/main` points at, because a fetch moves it; and D11 "
    "item 4 names H3's two Bash negative-test forms.\n"
    "  - **The k8s audit's majors** wait on the owner: no reservation values exist for the 6 GiB node; no join step applies "
    'the taint, and F6\'s "nd-* macvm" script does not exist; the VM, as written, has no route out and no admin path; the '
    "primer's autostart (its :409) bypasses G-MEM; and X1-X5 are open (E5, which waits on A6). Its questions bear on F1, F4, "
    "F6, F7, D1, D4, E5, C2 and H3.\n"
    "  - **G-AGENT holds:** the frontmatter and contract suites are green (H2), and H3's denials held."
)
ERRATA_END_NEW = "\n" + E_H3 + ERRATA_END_OLD

# ---------------------------------------------------------------------------------------------- the handoff

PREV_OLD = '\n\n- **From:** the 2026-10-26 session on turing named "c9-landed-h6-audited-owner-decides"'
PREV_NEW = '\n\n- **Continued (2026-10-27, plan v1.4.10).** "cached-enchanting-cosmos-84" ran H3, which passed (juniper-ml#@H3_PR@), ' f"once the owner had installed C8. The arc's main handoff is now `{THIS_HANDOFF}`, which carries this file's owner steps " "forward." + PREV_OLD


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
    if "- **Version**: 1.4.10 —" in text:
        report.append("present  plan: Version line 1.4.10")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.10")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.9 nor 1.4.10")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = edit(text, H2_OLD, H2_NEW, "its H3 denials hold since 2026-10-27", "plan: §18.2 H2 row", report)
    text = edit(text, C9_CELL_OLD, C9_CELL_NEW, "| C9 | **landed** (AGENT); **installed** (OWNER, 2026-10-26, with C8) |", "plan: §18.2 C9 row, status cell", report)
    text = edit(text, C9_TAIL_OLD, C9_TAIL_NEW, "**It took effect** on 2026-10-26", "plan: §18.2 C9 row, the install", report)
    text = edit(text, TABLE_END_OLD, fill(TABLE_END_NEW, subs), "| H3 | **done: passed** (AGENT, 2026-10-27) |", "plan: §18.2 C8 and H3 rows", report)
    return edit(text, ERRATA_END_OLD, ERRATA_END_NEW, "- **E-H3 (H3's run, against its row and D11).**", "plan: §18.3 erratum E-H3", report)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--h3-pr", required=True, help="the H3 evidence PR's number")
    ap.add_argument("--h3-sha", required=True, help="its merge commit, 8 hex or more")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.h3_pr.isdigit() and re.fullmatch(r"[0-9a-f]{8,40}", args.h3_sha)):
        print("--h3-pr must be a number, --h3-sha 8-40 lower-case hex", file=sys.stderr)
        return 2
    subs = {"@H3_PR@": args.h3_pr, "@H3_SHA@": args.h3_sha[:8]}
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, PREV_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], subs, report)
    edited[PREV_HANDOFF] = edit(edited[PREV_HANDOFF], PREV_OLD, fill(PREV_NEW, subs), "- **Continued (2026-10-27, plan v1.4.10).**", "previous handoff: pointer to its successor", report)
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
