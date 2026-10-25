"""
Apply the C9 guard PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — landing helper (turing bring-up task C9)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2, task C9);
         util/claude_agent_guard.py; tests/test_claude_agent_guard.py;
         util/ad-hoc/2026-10-20_k12_guard_doc_edits.py (the K12 counterpart, whose shape this follows)

Why: the shared files take concurrent whole-file uploads, so each upload is built by running this against a
FRESH `origin/main` copy at upload time (the juniper-ml#2262 revert class). Every edit has a marker (skip
when present) and an anchor that must occur exactly once. The files: `.github/workflows/ci.yml`,
`docs/REFERENCE.md` and `CHANGELOG.md`. The plan's C9 record is a separate PR.

Usage:
    python3 -I util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py [--base DIR] [--check] --mutants N/M

`--mutants N/M` is the C9 mutation result to record (for example `26/26`).

Exit codes:

- 0: applied, or nothing to do;
- 1: `--check` found pending edits;
- 2: an anchor was missing or not unique.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
ANALYSIS = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md"
MUTATION = "util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py"

CI_OLD = (
    "          # git config writes, ~/.gitconfig, ~/.config/git, the system gitconfigs and .git/hooks. Payloads pipe\n"
    "          # through it with a temp\n"
)
CI_NEW = (
    "          # git config writes, ~/.gitconfig, ~/.config/git, the system gitconfigs and .git/hooks; and (task C9)\n"
    "          # Serena's edit tools reaching .git/, .ssh, Claude settings or the registration files (symlinks\n"
    "          # followed), and MCP registration: mcp add* whatever the command word, --mcp-config,\n"
    "          # ~/.claude.json, .mcp.json and the two approval keys. Payloads pipe\n"
    "          # through it with a temp\n"
)
REF_UTIL_OLD = "It denies by rule id (`--list-rules` lists the 17) and otherwise prints nothing"
REF_UTIL_NEW = "It denies by rule id (`--list-rules` lists the 20) and otherwise prints nothing"
REF_UTIL_TAIL_OLD = "  - Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`.\n"
REF_UTIL_TAIL_NEW = (
    f"  - **C9** (`{PLAN}` §18.2; RR-10 of `{ANALYSIS}`), in 1.2.0, extends the guard to Serena's edit tools and to MCP registration.\n"
    "  - **`MCP-EDIT-PATH` (Serena's 19 edit tools)** resolves each path argument against the payload `cwd`, `CLAUDE_PROJECT_DIR` and the checkout "
    "holding each, literally and through `realpath`. It denies a path that reaches `.git/`, `.ssh` or `.gnupg`, a `.claude/settings*.json` or "
    "`.claude/hooks`, `.config/git`, a file named `.mcp.json`, `.claude.json` or `.gitconfig`, or anything the writers' rules protect; a "
    "`replace_in_files` include glob that names one of them; and a `replace_in_files` `repl` that sets `disableAllHooks` or an MCP approval key. "
    "A memory name is judged as `.serena/memories/<name>.md`, and `execute_shell_command` gets the Bash rules.\n"
    "  - **`MCP-REGISTER-BASH`** denies `mcp add`, `mcp add-json` and `mcp add-from-claude-desktop` after any command word (`claude`, its versions "
    "path, `npx`), `--mcp-config`, any mention of `~/.claude.json` or a `.mcp.json` file, and any mention of `enabledMcpjsonServers` or "
    "`enableAllProjectMcpServers`.\n"
    "  - **`MCP-REGISTER-FILE` (writers)** denies writes to `~/.claude.json` and any `.mcp.json`, and a `.claude/settings*.json` write that sets "
    "either approval key. Reads stay allowed, and `util/mcp_setup.bash` keeps working.\n"
    "  - `--settings-matcher` prints the hook matcher: the eight built-in tools, then each Serena tool as `mcp__serena__<tool>`.\n"
    "  - Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`.\n"
)
REF_INSTALLER_OLD = "`--apply` merges the PreToolUse entry and the 8 `permissions.deny` rules idempotently"
REF_INSTALLER_NEW = (
    "`--apply` merges the PreToolUse entry, whose matcher it reads from the guard's `--settings-matcher` (task C9 adds Serena's edit tools; "
    "a re-run replaces an older entry in place), and the 8 `permissions.deny` rules idempotently"
)
REF_SUITE_ANCHOR = "`util/ad-hoc/2026-10-20_k12_guard_mutation_check.py` kills 18 of 18 mutants, each by its own pin.\n"
CHANGELOG_ENTRY = (
    f"- **The agent guard covers Serena's edit tools and MCP registration (task C9)** (`{PLAN}` §18.2, widened by RR-10 of\n"
    f"  `{ANALYSIS}`). An MCP tool call reached the C8 guard only through its settings matcher, which named Claude Code's own\n"
    "  tools, so Serena's edit tools could write `.git/hooks` in a primary checkout unseen (E-SERENA-EDIT). No rule covered MCP\n"
    "  registration either, and a registered server runs a command the guard never sees.\n"
    "  - `util/claude_agent_guard.py` 1.2.0 adds three rules:\n"
    "    - `MCP-EDIT-PATH` judges Serena v1.7.0's 19 edit tools. A path argument, resolved against the project roots literally\n"
    "      and through `realpath`, may not reach `.git/`, `.ssh` or `.gnupg`, Claude's settings or hooks, the owner's git\n"
    "      configuration, `~/.claude.json` or a `.mcp.json`. `replace_in_files`' include glob and `repl` are judged too, and\n"
    "      Serena's `execute_shell_command` gets the Bash rules.\n"
    "    - `MCP-REGISTER-BASH` denies `mcp add`, `add-json` and `add-from-claude-desktop` after any command word, `--mcp-config`,\n"
    "      and any mention of `~/.claude.json`, a `.mcp.json` file or the two approval keys. So `cat ~/.claude.json` is now\n"
    "      denied; the Read tool still reads it.\n"
    "    - `MCP-REGISTER-FILE` denies writer calls on `~/.claude.json` and any `.mcp.json`, and a `.claude/settings*.json` write\n"
    "      that sets `enabledMcpjsonServers` or `enableAllProjectMcpServers`. `util/mcp_setup.bash` keeps working.\n"
    "  - The settings matcher now names the eight built-in tools and Serena's tools (`--settings-matcher` prints it).\n"
    "    `util/install_claude_agent_guard.bash` reads it from the guard, and `--apply` replaces a 1.1.0 entry in place.\n"
    "  - `tests/test_claude_agent_guard.py` adds 10 tests: 46 registration Bash cases (30 denied), 15 registration file cases\n"
    "    (8 denied), every Serena edit tool, 32 path cases, 20 `replace_in_files` cases and 7 shell cases. The self-test runs\n"
    "    50 checks.\n"
    f"  - `{MUTATION}` kills @MUTANTS@ mutants, each by its own pin test.\n"
    "  - The owner re-runs `bash util/install_claude_agent_guard.bash --apply` (task C8) from an up-to-date `main` to install it.\n"
)
CHANGELOG_MARKER = "**The agent guard covers Serena's edit tools and MCP registration (task C9)**"


class AnchorError(Exception):
    pass


def replace_once(text: str, old: str, new: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(old) != 1:
        raise AnchorError(f"text occurs {text.count(old)} times (need 1): {old[:80]!r}")
    return text.replace(old, new)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mutants", required=True, help="the C9 mutation result, N/M")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d+/\d+", args.mutants):
        print("--mutants must look like 26/26", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    base = Path(args.base)
    names = (".github/workflows/ci.yml", "docs/REFERENCE.md", "CHANGELOG.md")
    texts = {name: (base / name).read_text(encoding="utf-8") for name in names}
    try:
        new = dict(texts)
        new[".github/workflows/ci.yml"] = replace_once(texts[".github/workflows/ci.yml"], CI_OLD, CI_NEW, "; and (task C9)")
        ref = replace_once(texts["docs/REFERENCE.md"], REF_UTIL_OLD, REF_UTIL_NEW, "`--list-rules` lists the 20")
        ref = replace_once(ref, REF_UTIL_TAIL_OLD, REF_UTIL_TAIL_NEW, "  - **C9** (`")
        ref = replace_once(ref, REF_INSTALLER_OLD, REF_INSTALLER_NEW, "whose matcher it reads from the guard's `--settings-matcher`")
        suite_tail = (
            " **C9** pins `MCP-EDIT-PATH` (every Serena edit tool, denied on a `.git/hooks` path and allowed on an ordinary file; 32 path cases on"
            " `replace_content`: 20 denied, 12 allowed; 20 `replace_in_files` cases: 12 denied, 8 allowed; Serena's shell under the Bash rules; the"
            " checkout and `CLAUDE_PROJECT_DIR` roots), `MCP-REGISTER-BASH` (46 Bash cases: 30 denied, 16 allowed) and `MCP-REGISTER-FILE` (15 file"
            " cases: 8 denied, 7 allowed), the matcher, and the installer's in-place upgrade of a 1.1.0 entry; the self-test runs 50 checks;"
            f" `{MUTATION}` kills {killed} of {total} mutants, each by its own pin.\n"
        )
        new["docs/REFERENCE.md"] = replace_once(ref, REF_SUITE_ANCHOR, REF_SUITE_ANCHOR[:-1] + suite_tail, "**C9** pins `MCP-EDIT-PATH`")
        changelog = texts["CHANGELOG.md"]
        start = changelog.find("## [Unreleased]")
        end = changelog.find("\n## [", start + 1)
        section = changelog[start : end if end >= 0 else len(changelog)]
        if CHANGELOG_MARKER not in section:
            entry = CHANGELOG_ENTRY.replace("@MUTANTS@", f"{killed} of {total}")
            header = "## [Unreleased]\n"
            if section.count("\n### Security\n\n") == 1:
                section = section.replace("\n### Security\n\n", "\n### Security\n\n" + entry + "\n", 1)
            elif "\n### Security\n" not in section and section.startswith(header):
                # a release proposal leaves [Unreleased] empty: open a Security subsection above whatever follows
                body = section[len(header) :].lstrip("\n")
                section = header + "\n### Security\n\n" + entry + ("\n" + body if body else "")
            else:
                raise AnchorError("the Unreleased section's '### Security' heading is not followed by a blank line")
            changelog = changelog[:start] + section + (changelog[end:] if end >= 0 else "")
        new["CHANGELOG.md"] = changelog
    except AnchorError as exc:
        print(f"ANCHOR: {exc}", file=sys.stderr)
        return 2
    changed = [name for name in names if new[name] != texts[name]]
    for name in changed:
        print(f"{'would change' if args.check else 'changed'}: {name}")
        if not args.check:
            (base / name).write_text(new[name], encoding="utf-8")
    if not changed:
        print("nothing to do: every edit is already present")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
