"""
Record H5's decision (option B) and the follow-ups the owner adopted in the turing bring-up plan, idempotently (plan v1.4.5).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — one-off (the H5 decision record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.1, §18.2, §18.3);
         notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md (juniper-ml#2310; §6, §7);
         util/ad-hoc/2026-10-21_turing_h5_hardening_check.py (option B's check);
         util/ad-hoc/2026-10-21_turing_h5_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-21_turing_h5_decision_record.py [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.4 -> 1.4.5. Only from 1.4.4: another version is reported and left alone;
        2. §18's opening paragraph: the restore PR, the decision's session and handoff, and the arc's main handoff
           (the risk analysis' O-2);
        3. §18.1 gains the owner's ruling on H5's trees and the four follow-ups;
        4. §18.2's H5 row (decided: option B);
        5. §18.2's C9 row, widened by RR-10;
        6. §18.2 gains rows C0 (O-8), C2 (RR-11) and the new task H6 (O-5);
        7. §18.3 gains errata E-H5-RESTORE and E-H5-B;
  the H5 handoff:       8. a pointer to its successor;
  the arc's handoff:    9. the H5 pointer; 10. C9's widening under "Agent next".

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
H5_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md"
ARC_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md"
AUDIT = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md"
ANALYSIS = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md"
INVENTORY = "util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py"
RESTORE_CHECK = "util/ad-hoc/2026-10-21_turing_h5_restore_check.py"
HARDENING_CHECK = "util/ad-hoc/2026-10-21_turing_h5_hardening_check.py"
EVIDENCE = "reports/2026-10-21_turing-h5-hardening/"
RESTORE_PR, RESTORE_SHA = "juniper-ml#2310", "0c9a0baf"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.4 — v1.4.3 plus H5's landing"
VERSION_NEW = (
    "- **Version**: 1.4.5 — v1.4.4 plus H5's decision, option B (the trees kept, dormant and hardened), with the removal "
    "and restore that preceded it and the four follow-ups the owner adopted (§18's opening; §18.1; §18.2's H5, C9, C0, C2 "
    "and H6 rows; errata E-H5-RESTORE and E-H5-B in §18.3; 2026-10-21). v1.4.4 was v1.4.3 plus H5's landing"
)

INTRO_OLD = f"H5 landed alongside them, in the \"mac dev\" session (v1.4.4), whose handoff is `{H5_HANDOFF}`."
INTRO_NEW = (
    f"{INTRO_OLD} The same session removed and restored H5's trees and landed a risk analysis of the restored state "
    f"({RESTORE_PR}, `{RESTORE_SHA}`). The owner chose option B in the next session (v1.4.5), whose handoff is "
    f"`{THIS_HANDOFF}`. The arc's main handoff is the \"code signing\" session's `{ARC_HANDOFF}` (juniper-ml#2305), "
    "where C9 is next."
)

RULING_OLD = "A read-only Serena was the alternative.\n\n### 18.2 Task status after Session 3"
RULING_NEW = (
    "A read-only Serena was the alternative.\n"
    "- **H5's trees (2026-10-21).** The owner first chose removal, then reconsidered once it had run, and the trees were "
    "restored (E-H5-RESTORE). On the restored state's risk analysis the owner chose **option B**: keep both trees, dormant "
    "and hardened (E-H5-B). The owner also adopted all four of the analysis' follow-ups as tasks: RR-10 widens C9, RR-11 "
    "rewords C2, O-8 adds an exclusion to C0, and O-5 becomes the new task H6 (§18.2).\n"
    "\n### 18.2 Task status after Session 3"
)

H5_PREFIX = "| H5 | landed; **the owner's decision is pending** |"
H5_ROW = (
    "| H5 | **done: kept under option B** (owner, 2026-10-21); **B.4 and B.5 OWNER** | juniper-ml#2300 (`2f831b60`), in "
    f"the \"mac dev\" session (E-SPLIT): the `auditor` agent's static audit, `{AUDIT}`, with its read-only evidence script "
    f"`{INVENTORY}`. 25 findings (3 blocker, 9 major and 13 minor); it recommended removing both (E-H5). The trees were then "
    f"removed and restored, and {RESTORE_PR} (`{RESTORE_SHA}`) landed the validated risk analysis of the restored state, "
    f"`{ANALYSIS}`: 14 risks, 9 Medium and 5 Low, none High, all dormant (E-H5-RESTORE). Its recommendation stayed REMOVE, "
    "with option B as the alternative. **The owner chose B.** The agent applied B.1 to B.3; "
    f"`{HARDENING_CHECK}` checks them and the rest of the restored state, and exits 0 (`{EVIDENCE}`). B.4 (a Little Snitch "
    "rule for `node`) and B.5 (`git remote remove origin` in each tree) are the owner's (E-H5-B). The acceptance's "
    "\"enable or remove\" became \"keep, dormant and hardened\" |"
)

C9_OLD = "The owner re-installs the guard (C8's path). H3 depends on it (E-SERENA-EDIT) |"
C9_NEW = (
    "The owner re-installs the guard (C8's path). H3 depends on it (E-SERENA-EDIT). **Widened in v1.4.5 (owner, RR-10 of "
    "the H5 risk analysis):** C9 also denies MCP registration, which no rule covers today: (a) the `mcp add`, `mcp add-json` "
    "and `mcp add-from-claude-desktop` subcommands, whatever the command word, since the guard compares basenames and a rule "
    "on `claude` misses the versions path; (b) writes to `~/.claude.json` and to any `.mcp.json`, while H4's "
    "`util/mcp_setup.bash` keeps working; and (c) settings writes that set `enabledMcpjsonServers` or "
    "`enableAllProjectMcpServers`, where SELF-PROTECT-FILE blocks only `disableAllHooks` today (`util/claude_agent_guard.py:188`, "
    "`:1615`). Both of (c)'s files are gitignored (`.gitignore:166-167`, `:170`), so neither shows in `git status` or a PR. "
    "A script's internal writes stay out of reach (guard gap 1) |"
)

ROWS_ANCHOR = H5_ROW + "\n\n### 18.3 Errata"
NEW_ROWS = (
    "| C0 | **changed** (v1.4.5, owner, O-8 of the H5 risk analysis) | The encrypted Time Machine backup must not copy H5's "
    "kept trees, or a restore from it would bring them back in whatever state they then had. Before the first backup, "
    "exclude them: `tmutil addexclusion ~/.claude/mcp-servers`. Acceptance adds `tmutil isexcluded ~/.claude/mcp-servers` "
    "reporting `[Excluded]`. On 2026-10-21 it reported `[Included]`, and no Time Machine destination was configured |\n"
    "| C2 | **changed** (v1.4.5, owner, RR-11 of the H5 risk analysis) | Application firewall on, stealth mode on, and "
    "**block all incoming connections** (`socketfilterfw --setblockall on`) while nothing inbound is needed, in place of "
    "\"allow signed software\". As worded, C2 kept the default that automatically allows downloaded signed software "
    "(`socketfilterfw --getallowsigned`: ENABLED on 2026-10-21), so Docker Desktop's signed backend would keep publishing "
    "compose ports to the LAN. Where something inbound is needed, per-app inbound denies for `com.docker.backend`, `node` "
    "and the env Pythons instead; Little Snitch supports inbound rules too. Acceptance adds `socketfilterfw --getblockall` "
    "reporting enabled, or the per-app denies recorded. G-SEC's firewall condition still passes at `State = 1`, and its "
    "hint (`util/host_state_check.py:709`) still quotes the old wording; an agent updates both once the owner has chosen "
    "between the two forms |\n"
    "| H6 | **new** (v1.4.5, owner, O-5 of the H5 risk analysis; AGENT, P2) | Review the four MCP servers in VS Code's user "
    "`mcp.json`, which neither H0 nor H5 reviewed: `huggingface` and `upstash/context7` (http), `microsoft/markitdown` and "
    "`oraios/serena` (stdio). For each: provenance and pin (D10's pinning rule applies to Serena there too), the arguments, "
    "the tools it exposes (file-writing and command-running ones against C8 and C9; the rest need `permissions.deny`-style "
    "controls, H5-X1), and its egress. Secrets stay unread, as in H5: no env, header or URL-query value is printed. "
    "Acceptance: an `auditor` audit in `notes/` with a keep, pin or remove recommendation per server; the owner decides. "
    "VS Code auto-approves every terminal command here (`\"/.*/\": true`, signing plan K13), which raises the stakes |"
)

ERRATA_ANCHOR = "\n\n## 19. Commit signing for the terminal and the IDEs"
ERRATA = (
    "\n- **E-H5-RESTORE (H5's trees, removed and restored, 2026-10-21).** v1.4.4's \"decision pending\" predates both.\n"
    "  - **Removed.** After v1.4.4 landed (07:10:57Z) the owner chose \"remove both; you run it\". The agent ran `rm -rf` on "
    "both trees and `rmdir` on `~/.claude/mcp-servers`, and the owner's \"let's pause and reconsider\" arrived after all "
    "three had completed. `rm -rf` bypasses the Trash, so no repository operation could undo it.\n"
    "  - **Restored.** At 08:33Z both trees were re-cloned with `git clone --revision=<audited commit>`. At 09:04Z "
    "agi-mcp-server's March install was rebuilt offline from npm's cache, resolved `--before` the March install and with "
    "`--ignore-scripts`; `fsevents` was then removed. Every tracked file matches upstream (305 of 305, 33 of 33), as do the "
    "270 March lockfile pairs and the 174 installed versions. The deliberate deviations: agi's `origin` is `QuixiAI`, not "
    "the squatted name; both HEADs are detached at the audited commits; no install-time code ran; and the two March `.pyc` "
    "files are gone.\n"
    f"  - **Recorded** by {RESTORE_PR} (`{RESTORE_SHA}`): the risk analysis (VALIDATED: three reviewers, each "
    f"ACCEPT-WITH-CHANGES), `{RESTORE_CHECK}` and `reports/2026-10-21_turing-h5-restore/`. The analysis corrects the "
    "audit's AGOT-P1: Claude Desktop **is** installed and bound to `.dxt`, though it has never been launched (its O-1 and "
    "RR-2).\n"
    "  - **For next time:** an owner-approved removal of host state moves it to a dated quarantine directory, "
    "`~/.local/state/juniper/quarantine/<date>-<name>/`, and is purged only on a second go-ahead.\n"
    "- **E-H5-B (option B, applied 2026-10-21).** The owner chose the risk analysis' option B (its §7).\n"
    "  - **Applied by the agent** from 20:53Z to 20:54Z, each step reversible in place. sha256 and git blob ids show that "
    "the renames changed no byte, and each reversal is the opposite `mv`, or deleting `.npmrc`:\n"
    "    - B.1 renamed adaptive-graph-of-thoughts' `.claude/settings.local.json` to `settings.local.json.h5-disabled`. That "
    "closes RR-1's allow list for default, accept-edits and auto sessions; a bypass-permissions session in the tree stays "
    "exposed;\n"
    "    - B.2 renamed its three `.dxt` bundles and the `.zip` with the same suffix, so no app opens them (RR-2);\n"
    "    - B.3 wrote `agi-mcp-server/.npmrc` with `ignore-scripts=true` (RR-9).\n"
    f"  - **The check.** The restore check's provenance now fails by design. `python3 -I {HARDENING_CHECK}` accepts exactly "
    "B's deviations and judges the restore check's other checks unchanged; it exited 0 at 21:00:51Z. It reports B.5 per "
    "tree; B.4 has no machine check. Eight scenarios on copy-on-write clones of the trees gave the expected verdicts: the "
    "unchanged clone, each step reverted, a modified bundle, a squatted origin, a stray file, a second remote, and both "
    f"origins removed. Evidence in `{EVIDENCE}`: the restore check before and after B, and the hardening check.\n"
    "  - **OWNER, B.4 (RR-12):** a standing Little Snitch rule for `/usr/local/Cellar/node/25.8.1_1/bin/node` that denies "
    "`github.com` and `codeload.github.com`, and allows `registry.npmjs.org` only if npm is needed. Answer any pending alert "
    "for it with \"Deny once\". A blanket deny breaks pre-commit's node hook environments, and a rule on the Cellar path "
    "lapses at the next `brew upgrade node`.\n"
    "  - **OWNER, B.5 (RR-6):** in a separate terminal, since an agent session's worktree guard refuses git outside its "
    "worktree: `git -C ~/.claude/mcp-servers/adaptive-graph-of-thoughts remote remove origin`, then the same for "
    "`agi-mcp-server`. The hardening check then reports B.5 as done. Reverse with `git -C <tree> remote add origin <URL>`, "
    "the URLs being in the analysis' §3.1.\n"
    "  - **What B leaves** (the analysis' §7): RR-1 for bypass sessions; RR-3 to RR-5, RR-7 and RR-8 behind \"never "
    "configure\"; RR-13 and RR-14; and the host-wide RR-10 to RR-12, which C9, C2 and B.4 address. The standing rules "
    "stay: never open Claude Code or an IDE agent in either tree, never open the renamed bundles, never follow the trees' "
    "example configs or install steps, and never fetch or pull in them.\n"
    "  - **Advisories.** 92 GitHub advisories are active for the installed npm set at 20:53Z (3 critical, 29 high, 55 "
    "medium and 5 low), against the analysis' 89 at 10:11Z. They are reported, not judged, and stay dormant while nothing "
    "runs (RR-7)."
)

# ---------------------------------------------------------------------------------------------- the handoffs

H5_HANDOFF_OLD = "\n\n- **From:** the 2026-10-21 session on turing named \"mac dev\"."
H5_HANDOFF_NEW = (
    "\n\n- **Superseded (2026-10-21, plan v1.4.5).** The owner chose option B: keep both trees, dormant and hardened. "
    f"B.1 to B.3 are applied. H5's current state, the owner's B.4 and B.5, and the check are in `{THIS_HANDOFF}`. "
    "What follows is this file's state before the decision."
    + H5_HANDOFF_OLD
)

ARC_POINTER_OLD = f"`{H5_HANDOFF}` stays the authority on H5's state and the removal commands."
ARC_POINTER_NEW = (
    f"{ARC_POINTER_OLD} **Since plan v1.4.5** the owner has chosen H5's option B (keep, hardened), and the authority on H5 "
    f"is `{THIS_HANDOFF}`."
)

ARC_C9_OLD = "   - C9 can be built and landed before C8 is installed. Only its installation is the owner's.\n"
ARC_C9_NEW = (
    ARC_C9_OLD
    + "   - **Widened by plan v1.4.5 (owner, RR-10):** C9 also denies MCP registration: the `mcp add*` subcommands whatever "
    "the command word, writes to `~/.claude.json` and any `.mcp.json` (H4's `util/mcp_setup.bash` must keep working), and "
    "settings writes that set `enabledMcpjsonServers` or `enableAllProjectMcpServers`. The plan's §18.2 C9 row has the "
    "detail.\n"
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


def replace_row(text: str, prefix: str, new_row: str, label: str, report: list) -> str:
    if new_row in text:
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


def edit_plan(text: str, report: list) -> str:
    if "- **Version**: 1.4.5 —" in text:
        report.append("present  plan: Version line 1.4.5")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW)
        report.append("applied  plan: Version line 1.4.5")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.4 nor 1.4.5")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = edit(text, RULING_OLD, RULING_NEW, "- **H5's trees (2026-10-21).**", "plan: §18.1 ruling on H5's trees", report)
    text = replace_row(text, H5_PREFIX, H5_ROW, "plan: §18.2 H5 row", report)
    text = edit(text, C9_OLD, C9_NEW, "**Widened in v1.4.5 (owner, RR-10", "plan: §18.2 C9 row widened", report)
    text = edit(text, ROWS_ANCHOR, H5_ROW + "\n" + NEW_ROWS + "\n\n### 18.3 Errata", "| H6 | **new** (v1.4.5",
                "plan: §18.2 rows C0, C2 and H6", report)
    return edit(text, ERRATA_ANCHOR, ERRATA + ERRATA_ANCHOR, "- **E-H5-RESTORE (", "plan: §18.3 errata E-H5-RESTORE, E-H5-B", report)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, H5_HANDOFF, ARC_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], report)
    edited[H5_HANDOFF] = edit(edited[H5_HANDOFF], H5_HANDOFF_OLD, H5_HANDOFF_NEW, "- **Superseded (2026-10-21, plan v1.4.5).**",
                              "H5 handoff: pointer to its successor", report)
    edited[ARC_HANDOFF] = edit(edited[ARC_HANDOFF], ARC_POINTER_OLD, ARC_POINTER_NEW, "**Since plan v1.4.5**", "arc handoff: H5 pointer", report)
    edited[ARC_HANDOFF] = edit(edited[ARC_HANDOFF], ARC_C9_OLD, ARC_C9_NEW, "**Widened by plan v1.4.5 (owner, RR-10):**", "arc handoff: C9 widened", report)
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
