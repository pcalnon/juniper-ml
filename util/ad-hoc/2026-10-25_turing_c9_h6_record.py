#!/usr/bin/env python3
"""
Record C9's landing and H6's audit in the turing bring-up plan and the handoffs, idempotently (plan v1.4.6).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — one-off (the C9 and H6 record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.2, §18.3);
         notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md (the H6 audit);
         util/claude_agent_guard.py (C9); util/ad-hoc/2026-10-21_turing_h5_decision_record.py (the pattern)

Why: the plan and the handoffs are shared files, so the edits are anchored on text and re-run on a fresh origin/main
copy before the upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing,
nothing is written.

    python3 -I util/ad-hoc/2026-10-25_turing_c9_h6_record.py --c9-pr N --c9-sha SHA --mutants K/M [--root DIR] [--dry-run]

The edits:
  plan  1. the Version line, 1.4.5 -> 1.4.6. Only from 1.4.5: another version is reported and left alone;
        2. §18's opening paragraph: this session and its handoff, now the arc's main handoff;
        3. §18.2's C9 row (landed; its installation is the owner's);
        4. §18.2's H6 row (audited; the decisions are the owner's);
        5. §18.3 gains errata E-C9 and E-H6;
  the option-B handoff:  6. a pointer to its successor;
  the arc's handoff:     7. a pointer to its successor.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
ARC_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md"
OPTION_B_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h5-option-b-applied-owner-b4-b5.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-25_turing-c9-landed-h6-audited-owner-decides.md"
AUDIT = "notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md"
INVENTORY = "util/ad-hoc/2026-10-25_turing_h6_vscode_mcp_inventory.py"
MUTATION = "util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py"

# ---------------------------------------------------------------------------------------------- the plan

VERSION_OLD = "- **Version**: 1.4.5 — v1.4.4 plus"
VERSION_NEW = (
    "- **Version**: 1.4.6 — v1.4.5 plus C9's landing and H6's audit (§18's opening; §18.2's C9 and H6 rows; errata E-C9 and E-H6 "
    "in §18.3; 2026-10-25). v1.4.5 was v1.4.4 plus"
)

INTRO_OLD = (
    "The arc's main handoff is the \"code signing\" session's `prompts/thread-handoff_automated-prompts/"
    "HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` (juniper-ml#2305), where C9 is next."
)
INTRO_NEW = (
    "The arc's main handoff was the \"code signing\" session's `prompts/thread-handoff_automated-prompts/"
    "HANDOFF_2026-10-21_turing-h2-h4-h5-landed-rs9-fixed-c9-next.md` (juniper-ml#2305), where C9 was next. C9 landed and H6's "
    f"audit ran in the session after that (v1.4.6), whose handoff, `{THIS_HANDOFF}`, is now the arc's main handoff."
)

C9_PREFIX = "| C9 | **new** (owner ruling 2026-10-21; AGENT) |"
C9_ROW = (
    "| C9 | **landed** (AGENT); **install OWNER** (C8's step) | juniper-ml#@PR@ (`@SHA@`): `util/claude_agent_guard.py` 1.2.0 adds "
    "MCP-EDIT-PATH, MCP-REGISTER-BASH and MCP-REGISTER-FILE. Its settings matcher now names the eight built-in tools plus Serena "
    "v1.7.0's 19 edit tools and its shell (`--settings-matcher`, which `util/install_claude_agent_guard.bash` now reads). "
    "MCP-EDIT-PATH resolves each Serena path against the payload `cwd`, `CLAUDE_PROJECT_DIR` and the checkout holding each, "
    "literally and through `realpath`. It denies `.git/`, `.ssh` or `.gnupg`, Claude's settings or hooks, the owner's git "
    "configuration, `~/.claude.json` and any `.mcp.json`, a `replace_in_files` include glob that names one of them, and a `repl` "
    "that sets `disableAllHooks` or an approval key. A memory name is judged as `.serena/memories/<name>.md`, and "
    "`execute_shell_command` gets the Bash rules. MCP-REGISTER-BASH denies `mcp add*` whatever the command word, `--mcp-config`, "
    "and any mention of `~/.claude.json`, a `.mcp.json` or the approval keys; MCP-REGISTER-FILE denies writer calls on those files "
    "and settings writes that set either key. `util/mcp_setup.bash` keeps working. `tests/test_claude_agent_guard.py` gains 10 "
    f"tests (48 in all), the self-test runs 50 checks, and `{MUTATION}` kills @MUTANTS@ mutants, each by its own pin (E-C9). "
    "**It takes effect** when the owner re-runs `bash util/install_claude_agent_guard.bash --apply` from an up-to-date `main` "
    "(C8); H3's C9 dependency is met then |"
)

H6_PREFIX = "| H6 | **new** (v1.4.5, owner, O-5 of the H5 risk analysis; AGENT, P2) |"
H6_ROW = (
    f"| H6 | **done: audited** (AGENT, the `auditor` agent); **decisions OWNER** | `{AUDIT}`, landed with this record, with its "
    f"evidence script `{INVENTORY}`. The script prints VS Code's MCP configuration as a default-deny projection, with no env, "
    "header, URL-query or input value. 19 findings: 2 blocker, 8 major and 9 minor. The recommendations (the audit's §8): "
    "`oraios/serena` **remove**, or pin it to H4's commit with the `vscode` context; `microsoft/markitdown` **remove**, or pin "
    "0.0.1a8 with its markitdown; `upstash/context7` **keep**, used only after K13; `huggingface` **keep only re-credentialed** "
    "(rotate the token first), or remove. Also: autostart off, the gallery off, and the 20 unreferenced inputs pruned. The "
    "blockers are SER-P1, an unpinned Serena whose `main` defaults new users to an exec-capable REPL interface, and HF-P1, a "
    "plaintext token in `mcp.json` that Settings Sync carries to other hosts. None of the four servers has ever started from "
    "VS Code on turing (E-H6) |"
)

ERRATA_ANCHOR = "\n\n## 19. Commit signing for the terminal and the IDEs"
ERRATA = (
    "\n- **E-C9 (C9's scope, against its row).**\n"
    "  - **19 edit tools, not the row's nine.** Every `ToolMarkerCanEdit` tool at H4's pin is covered: the row's list plus "
    "`create_text_file`, `safe_delete_symbol`, the four JetBrains editors and the four memory writers. `execute_shell_command`, "
    "excluded twice (by the claude-code context and by `.serena/project.yml`), gets the Bash rules as defence in depth.\n"
    "  - **`--mcp-config` too.** It loads MCP servers for one session: a registration path that RR-10's list missed.\n"
    "  - **Bash reads by mention.** As K12 does for `~/.gitconfig`, MCP-REGISTER-BASH denies any mention of `~/.claude.json` or "
    "a `.mcp.json` file, so `cat ~/.claude.json` is now denied; the Read tool still reads both. Reads were never the risk, but "
    "shell text cannot reliably tell a read from a write.\n"
    "  - **Two roots.** In a worktree session `CLAUDE_PROJECT_DIR` stays at the primary checkout while `cwd` follows the "
    "worktree (Claude Code's hooks reference). A worktree session's Serena can therefore be rooted at the primary checkout, "
    "whose `.git/hooks` are live. The guard reads every path against both, and against the checkout holding each.\n"
    "  - **Residuals** (the guard's gaps 1, 10 and 11): a script's internal writes; the language-server edits of "
    "`rename_symbol` and `safe_delete_symbol`; an unscoped `replace_in_files` that reaches a tracked `.claude/settings.json` or "
    "`.mcp.json`, judged there only on its `repl`; and other clients' MCP configuration. Any writer can also change "
    "`.serena/project.yml` or `project.local.yml`, Serena's own exclusions, which a Serena restart applies.\n"
    "- **E-H6 (H6's findings that reach past VS Code).**\n"
    "  - **Order with E-H4-WHEEL.** Building cryptography 50.0.0 once for H4, E-H4-WHEEL's first option, leaves the wheel in "
    "uv's cache, and that also lets VS Code's unpinned Serena entry start. Remove or pin that entry first (SER-P1).\n"
    "  - **H4's Serena reports usage.** Serena v1.7.0 calls `https://oraios-software.de/serena_usage.php` on every start unless "
    "`SERENA_USAGE_REPORTING=false` (`src/serena/agent.py:725-735` at `949a27ef`), and `util/mcp_setup.bash` writes "
    "`\"env\": {}`. Candidate follow-up (AGENT; the owner decides): set the variable in the entry, with `tests/test_mcp_setup.py`'s "
    "pins.\n"
    "  - **Settings Sync.** VS Code syncs the user `mcp.json` (H6-X3), so the Hugging Face token also sits in the sync service, "
    "and an edit made on turing reaches every synced host. Decide the scope of the H6 changes first.\n"
    "  - **Nothing ran from VS Code.** No VS Code log records a start of any of the four servers, and VS Code's newest log "
    "session is 2026-03-26. uv's second Serena checkout, v0.1.4 at `0c915bd1`, was resolved by another client on 2026-03-21 "
    "(SER-H1)."
)

# ---------------------------------------------------------------------------------------------- the handoffs

OPTION_B_OLD = "\n\n- **From:** the 2026-10-21 session on turing now named \"mac dev\""
OPTION_B_NEW = (
    "\n\n- **Continued (2026-10-25, plan v1.4.6).** C9 landed (juniper-ml#@PR@) and H6's audit ran; the arc's state and next "
    f"steps are in `{THIS_HANDOFF}`. The owner steps below (B.4, B.5, C0 and C2) still stand."
    + OPTION_B_OLD
)

ARC_OLD = "\n\n- **From:** the 2026-10-20/21 session on turing named \"code signing\""
ARC_NEW = (
    "\n\n- **Superseded (2026-10-25, plan v1.4.6).** C9 landed (juniper-ml#@PR@) and H6's audit ran. The arc's main handoff is "
    f"now `{THIS_HANDOFF}`. What follows is this file's state before C9."
    + ARC_OLD
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


def edit_plan(text: str, subs: dict, report: list) -> str:
    if "- **Version**: 1.4.6 —" in text:
        report.append("present  plan: Version line 1.4.6")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW, 1)
        report.append("applied  plan: Version line 1.4.6")
    else:
        report.append("MISSING  plan: Version line: the plan is at neither 1.4.5 nor 1.4.6")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "plan: §18 opening paragraph", report)
    text = replace_row(text, C9_PREFIX, fill(C9_ROW, subs), "| C9 | **landed** (AGENT)", "plan: §18.2 C9 row", report)
    text = replace_row(text, H6_PREFIX, H6_ROW, "| H6 | **done: audited**", "plan: §18.2 H6 row", report)
    return edit(text, ERRATA_ANCHOR, ERRATA + ERRATA_ANCHOR, "- **E-C9 (", "plan: §18.3 errata E-C9, E-H6", report)


def fill(text: str, subs: dict) -> str:
    for key, value in subs.items():
        text = text.replace(key, value)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--c9-pr", required=True, help="C9's PR number")
    ap.add_argument("--c9-sha", required=True, help="C9's merge commit, 8 hex or more")
    ap.add_argument("--mutants", required=True, help="the C9 mutation result, K/M")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.c9_pr.isdigit() and re.fullmatch(r"[0-9a-f]{8,40}", args.c9_sha) and re.fullmatch(r"\d+/\d+", args.mutants)):
        print("--c9-pr must be a number, --c9-sha 8-40 lower-case hex, --mutants K/M", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    subs = {"@PR@": args.c9_pr, "@SHA@": args.c9_sha[:8], "@MUTANTS@": f"{killed} of {total}"}
    report: list[str] = []
    files = {rel: (args.root / rel).read_text(encoding="utf-8") for rel in (PLAN, OPTION_B_HANDOFF, ARC_HANDOFF)}
    edited = dict(files)
    edited[PLAN] = edit_plan(edited[PLAN], subs, report)
    edited[OPTION_B_HANDOFF] = edit(edited[OPTION_B_HANDOFF], OPTION_B_OLD, fill(OPTION_B_NEW, subs), "- **Continued (2026-10-25, plan v1.4.6).**",
                                    "option-B handoff: pointer to its successor", report)
    edited[ARC_HANDOFF] = edit(edited[ARC_HANDOFF], ARC_OLD, fill(ARC_NEW, subs), "- **Superseded (2026-10-25, plan v1.4.6).**",
                               "arc handoff: pointer to its successor", report)
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
