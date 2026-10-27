#!/usr/bin/env python3
"""
Record H6's application in the turing plan (v1.4.9) and point the previous main handoff at its successor.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — one-off (the record PR of the "c9-landed-h6-audited-owner-decides" session)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.1, §18.2, §18.3);
         notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md (§8);
         util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py (what was applied);
         util/ad-hoc/2026-10-26_turing_c2_applied_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written. The facts recorded are those of the one application, at 2026-10-27T00:32:24Z.

    python3 -I util/ad-hoc/2026-10-26_turing_h6_applied_record.py [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.8 -> 1.4.9. Only from 1.4.8: another version is reported and left alone;
        2. §18's opening paragraph: the two sessions that continued from v1.4.8's handoff, and this one's handoff;
        3. §18.1: H6's resumption, after the 2026-10-25 ruling that deferred it;
        4. §18.2's H6 row: its status cell (applied);
        5. §18.2's H6 row: the deferral becomes the application record;
        6. §18.3: the new erratum E-H6-APPLY, after E-CUT;
  the previous main handoff:  7. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREV_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-26_turing-c2-applied-gate-reads-getter-sentence.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-26_turing-h6-applied-token-rotation-and-first-sync-owner.md"
APPLY = "util/ad-hoc/2026-10-26_turing_h6_apply_vscode_mcp_decisions.py"
BACKUP = "~/.local/state/juniper/quarantine/2026-10-26-vscode-mcp/"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.8 — v1.4.7 plus"
VERSION_NEW = (
    "- **Version**: 1.4.9 — v1.4.8 plus H6's application: the owner resumed H6, and the agent applied the H6 audit's §8 to "
    "VS Code's user `mcp.json` and `settings.json` on turing, for every synced host, leaving the token's rotation to the owner "
    "(§18's opening; §18.1; §18.2's H6 row; erratum E-H6-APPLY in §18.3; 2026-10-26). v1.4.8 was v1.4.7 plus"
)

INTRO_OLD = f"its handoff, `{PREV_HANDOFF}`, is now the arc's main handoff."
INTRO_NEW = (
    f"its handoff is `{PREV_HANDOFF}`. Two sessions continued from it: \"cached-enchanting-cosmos-84\" took H3, and "
    "\"c9-landed-h6-audited-owner-decides\" (v1.4.9) applied H6 once the owner resumed it. The latter's handoff, "
    f"`{THIS_HANDOFF}`, is now the arc's main handoff."
)

RULING_OLD = (
    "  - **H6:** deferred. When it resumes, its changes cover every synced host (H6-X3), and the agent makes them, backing up "
    "`mcp.json` and `settings.json` first with the token redacted. SER-P1's order stands: VS Code's Serena entry goes before "
    "E-H4-WHEEL's wheel build.\n"
)
RULING_NEW = RULING_OLD + (
    "- **H6 resumed (2026-10-26).** The owner's session prompt listed H6's decisions to complete: the scope first; VS Code's "
    "Serena entry removed before E-H4-WHEEL's wheel build; the Hugging Face token rotated; markitdown removed and Context7 kept; "
    "autostart and the gallery off; and the 20 unused inputs deleted. The scope stood as ruled on 2026-10-25: every synced host. "
    "The agent applied everything but the rotation, which needs the owner at huggingface.co. The prompt named no form for the "
    "Hugging Face entry, so the agent applied the audit's recommended token-less one (§8.4; E-H6-APPLY).\n"
)

H6_CELL_OLD = "| H6 | **done: audited** (AGENT, the `auditor` agent); **decisions deferred** (owner, 2026-10-25) |"
H6_CELL_NEW = "| H6 | **done: applied** (AGENT, 2026-10-26); audited (the `auditor` agent); **token rotation and the first sync OWNER** |"

H6_TAIL_OLD = (
    "None of the four servers has ever started from VS Code on turing (E-H6) The owner deferred the decisions on 2026-10-25 "
    "(§18.1). When they resume, the changes cover every synced host and the agent makes them. SER-P1's order stands: VS Code's "
    "Serena entry goes before E-H4-WHEEL's wheel build |"
)
H6_TAIL_NEW = (
    "None of the four servers has ever started from VS Code on turing (E-H6). The owner deferred the decisions on 2026-10-25 "
    f"and resumed them on 2026-10-26 (§18.1). **Applied** on turing at 2026-10-27T00:32:24Z (2026-10-26 local) by `{APPLY}`, "
    f"after a backup with the token redacted to `{BACKUP}`. `oraios/serena` and `microsoft/markitdown` are gone, "
    "`upstash/context7` is unchanged, `huggingface` runs token-less, and only `context7_api_key` remains of the 21 inputs. "
    "`chat.mcp.autostart` is `never` and `chat.mcp.gallery.enabled` is `false`. The script's `--check` holds 8 of 8 and its "
    "`--self-test` 15 of 15, and the audit's inventory shows the two kept servers and the one input. SER-P1's order held: uv's "
    "cache had no cryptography 50 wheel. Settings Sync carries the change to the other hosts once VS Code next runs on turing. "
    "Rotating the token is the owner's (E-H6-APPLY) |"
)

E_CUT_END = "so the entries of juniper-ml#2335 and juniper-ml#2338 ride 0.11.2.\n"
ERRATUM = (
    "- **E-H6-APPLY (H6's application, against the audit's §8).**\n"
    "  - **What changed.** VS Code's user `mcp.json` lost `oraios/serena` (SER-P1), `microsoft/markitdown` (MKD-T1), the "
    "Hugging Face entry's literal `Authorization` header (HF-P1) and the 20 inputs no server references (H6-X5). "
    "`upstash/context7` and its `context7_api_key` input are unchanged. `settings.json` gained `\"chat.mcp.autostart\": "
    "\"never\"`, and `\"chat.mcp.gallery.enabled\"` went from `true` to `false` (H6-X4). A structural diff against the backup "
    "shows nothing else changed: `mcp.json` lost 97 leaf paths and gained or changed none, and `settings.json` gained one and "
    "changed one of its 901.\n"
    f"  - **How.** `{APPLY}` prints no value: servers, headers, inputs and settings appear by key, and the token by count. It "
    "rewrites a file only when a JSON round trip reproduces it, so no comment or layout is lost, and only while VS Code is not "
    "running. Both files passed: `mcp.json` is tab-indented with one trailing comma, `settings.json` is strict JSON indented by "
    "four spaces, and neither has a comment. `--self-test` runs every path against synthetic fixtures whose token is generated "
    "at run time, so no secret sits in the repository.\n"
    f"  - **The backup.** `{BACKUP}` (mode 0700, files 0600) holds both files and a `MANIFEST.json`: one redaction in "
    "`mcp.json`, none in `settings.json`. The script re-read both copies and found no `hf_`-shaped string before it edited "
    "anything.\n"
    "  - **The Hugging Face entry's form.** The owner asked for the token's rotation, not for a form. The agent applied §8.4's "
    "recommended token-less entry, which gets only the anonymous tool set (HF-T1). `--hf password-input` references a read-only "
    "token through a password input instead, and `--hf remove` drops the server.\n"
    "  - **Every synced host.** Settings Sync carries the user `mcp.json` (H6-X3). In 1.108.2's bundle both settings are "
    "window-scoped with no `ignoreSync`, so they sync as well. Nothing reaches the sync service until VS Code runs on turing, "
    "whose newest VS Code session is still 2026-03-26. Each other host takes the change at its own next sync. If VS Code reports "
    "a conflict on any host, turing's version is the one to keep. `--check` verifies a host from its default user directory "
    "(`~/.config/Code/User` on Linux).\n"
    "  - **Where the token still sits** until it is rotated: the sync service, and VS Code's sync state on turing "
    "(`User/sync/mcp/lastSyncmcp.json`, rewritten at the next sync) and on every other synced host. VS Code's local history on "
    "turing keeps no copy of `mcp.json`. Rotation makes every copy inert, so it stays the fix (HF-P1).\n"
    "  - **No other unpinned Serena would start** once E-H4-WHEEL builds cryptography 50.0.0. `~/.claude.json` registers no "
    "MCP server, and `amp.mcpServers` is empty. `~/.claude/settings.json` holds a 23-server `mcpServers` block with an unpinned "
    "Serena, but Claude Code reads MCP servers from `~/.claude.json` and `.mcp.json`, not from `settings.json`. So E-H4-WHEEL "
    "no longer waits on H6, provided the first sync keeps turing's version.\n"
    "  - **Still the owner's:** rotating the token at huggingface.co; opening VS Code on turing once, so that Settings Sync "
    "uploads the change; and K13 before either kept server is used (H6-X2). Optional, from §8.5: \"Chat: Reset Tool "
    "Confirmations\", `workbench.mcp.resetTrust`, and `workbench.mcp.removeStoredInput` for any value stored under a deleted "
    "input.\n"
)

# ---------------------------------------------------------------------------------------------- the handoff

PREV_OLD = "\n\n- **From:** the 2026-10-26 session on turing named \"modular-meandering-crayon-bf\""
PREV_NEW = (
    "\n\n- **Continued (2026-10-26, plan v1.4.9).** Two sessions took this handoff. \"cached-enchanting-cosmos-84\" (760fde) "
    "took H3. \"c9-landed-h6-audited-owner-decides\" (bd4cfc) applied H6 on turing once the owner resumed it, and its handoff, "
    f"`{THIS_HANDOFF}`, is now the arc's main handoff. The other owner steps below still stand; H6's item under Agent next is "
    "done." + PREV_OLD
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


def edit_plan(text: str, report: list) -> str:
    if "- **Version**: 1.4.9 —" in text:
        report.append("present  plan: Version line 1.4.9")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.9")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.8 nor 1.4.9")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = edit(text, RULING_OLD, RULING_NEW, "- **H6 resumed (2026-10-26).**", "plan: §18.1 H6 resumed", report)
    text = edit(text, H6_CELL_OLD, H6_CELL_NEW, "| H6 | **done: applied** (AGENT, 2026-10-26)", "plan: §18.2 H6 row, status cell", report)
    text = edit(text, H6_TAIL_OLD, H6_TAIL_NEW, "**Applied** on turing at 2026-10-27T00:32:24Z", "plan: §18.2 H6 row, the record", report)
    return edit(text, E_CUT_END, E_CUT_END + ERRATUM, "- **E-H6-APPLY (", "plan: §18.3 erratum E-H6-APPLY", report)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, PREV_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], report)
    edited[PREV_HANDOFF] = edit(edited[PREV_HANDOFF], PREV_OLD, PREV_NEW, "- **Continued (2026-10-26, plan v1.4.9).**",
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
