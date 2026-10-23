"""
Record H2's and H4's landing, the owner's 2026-10-21 rulings and the new task C9 in the turing bring-up plan (v1.4.3).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — one-off (the H2 / H4 record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.1, §18.2, §18.3);
         juniper-ml#2294 (H2), juniper-ml#2295 (H4); util/ad-hoc/2026-10-20_turing_g1_g4_record.py (the pattern)

Why: the plan is a shared file, so the edits are anchored on text and re-run on a fresh origin/main copy before the
upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing, nothing is written.

    python3 -I util/ad-hoc/2026-10-21_turing_h2_h4_record.py [--root DIR] [--dry-run]

The edits, all in the plan:
  1. the Version line, 1.4.2 -> 1.4.3. Only from 1.4.2: another version is reported and left alone;
  2. §18's opening paragraph names the following session and its handoff;
  3. §18.1 gains the owner's two rulings of 2026-10-21: the split of H2, H4 and H5, and Serena's edit tools;
  4. §18.2 gains rows for H2 and H4 (landed), C9 (new) and H5 (with the "mac dev" session);
  5. §18.3 gains errata E-SPLIT, E-H4-WHEEL and E-SERENA-EDIT.

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PICKED_UP = HANDOFF_DIR + "HANDOFF_2026-10-20_turing-g1-landed-g4-promoted-h2-next.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md"
AUDIT = "notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md"
H2_PR, H2_SHA = "juniper-ml#2294", "b16121ac"
H4_PR, H4_SHA = "juniper-ml#2295", "a005063e"

VERSION_OLD = "- **Version**: 1.4.2 — v1.4.1 plus G1's landing and G4's promotion (§18.2's G1 and G4 rows; errata E-G1 and E-DUP in §18.3; 2026-10-20). v1.4.1 was"
VERSION_NEW = (
    "- **Version**: 1.4.3 — v1.4.2 plus H2's and H4's landing and the owner's rulings of 2026-10-21 (§18.1; §18.2's H2, H4, C9 and H5 rows;"
    " errata E-SPLIT, E-H4-WHEEL and E-SERENA-EDIT in §18.3; 2026-10-21). v1.4.2 was v1.4.1 plus G1's landing and G4's promotion (§18.2's G1 and G4"
    " rows; errata E-G1 and E-DUP in §18.3; 2026-10-20). v1.4.1 was"
)

INTRO_ANCHOR = f"G1 and G4's promotion landed in the following session (v1.4.2), whose handoff is `{PICKED_UP}`."
INTRO_ADDED = f" H2 and H4 landed in the session after that (v1.4.3), whose handoff is `{THIS_HANDOFF}`."

RULINGS_ANCHOR = "- No new decision ruling. The E2-first order of §17.1 stood. E2 went first, and the G-arc ran while E2 waited on the owner's Little Snitch approval.\n"
RULINGS_ADDED = (
    "- **The split of H2, H4 and H5 (2026-10-20).** H2 and H4 to the \"code signing\" session, H5 to the \"mac dev\" session (E-SPLIT).\n"
    "- **Serena's edit tools (2026-10-21).** H4 follows D10 as written: the stock claude-code context, which excludes the shell tool, with Serena's"
    " file-writing tools left on. Those tools are outside the C8 guard, so the new task C9 extends the guard to them, and H3 waits on it"
    " (E-SERENA-EDIT). A read-only Serena was the alternative.\n"
)

G1_ROW_TAIL = "Each failure is an open task: A1; C1, C2 and C3; D4; E4; A6 and F2; node mode (F3) and D7; and the I-SIGN record (signing plan K10) |\n"
ROWS = (
    f"| H2 | landed | {H2_PR} (`{H2_SHA}`), in the session after G1's. The three §11 agents, `.claude/agents/{{macos-host-sme,signing-auth-sme,k8s-node-sme}}.md`,"
    " each with a contract suite: `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py` and `tests/test_k8s_node_sme_contract.py`,"
    " which share `tests/agent_contract_support.py` (49 tests). Each suite pins the agent's tool set and its §11 Must-never items, and runs"
    " `util/claude_agent_guard.py` to show the guard denies each item under the rule the agent cites (43 cases) and passes the agent's own"
    " procedure (25). `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py` kills 28 of 28 mutants, six of them in the guard. G-AGENT's static"
    " half holds; its H3 denials wait on C8 and C9. **Install pending:** the primary checkout still has 6 agents, so `bash util/install_agents.bash`"
    " (9 links) follows the owner's C8 step 1 fast-forward |\n"
    f"| H4 | landed; **live check blocked** | {H4_PR} (`{H4_SHA}`). `util/mcp_setup.bash [checkout]` writes `<checkout>/.mcp.json`'s Serena entry:"
    " `uvx --from git+https://github.com/oraios/serena@<commit> serena start-mcp-server --context <context> --project <checkout>"
    " --open-web-dashboard False`. The pin is `conf/hosts/turing/mcp.json`: v1.7.0 at `949a27ef1e5fda1a6e7b561e777bcece345c6ffd`, on the claude-code"
    " context, whose `excluded_tools` hold `execute_shell_command` at that commit (read through `gh api`); 2.x was passed over for its"
    " code-executing `--agent-interface REPL`. `.serena/project.yml` excludes the shell tool too, and `.gitignore` covers the script's backups."
    f" `--project` fixes audit A2-F1 and running it per checkout fixes A2-F4 (`{AUDIT}`). 35 tests in `tests/test_mcp_setup.py`, also on"
    " `host-tooling-macos`; `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py` kills 20 of 20 mutants. **`timeout 30 claude mcp list` waits on"
    " E-H4-WHEEL** |\n"
    "| C9 | **new** (owner ruling 2026-10-21; AGENT) | Extend `util/claude_agent_guard.py` and its settings matcher to MCP file-writing tools, Serena's"
    " first: `replace_content`, `replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`, `rename_symbol`, `replace_in_files`, the line"
    " tools and the memory writers. Deny a call whose path, resolved against the server's project root, reaches `.git/`, `~/.ssh`, `~/.gnupg` or"
    " the Claude settings, with a test per tool and rule in `tests/test_claude_agent_guard.py`. The owner re-installs the guard (C8's path)."
    " H3 depends on it (E-SERENA-EDIT) |\n"
    "| H5 | with the \"mac dev\" session | The `auditor` agent audits `~/.claude/mcp-servers/`'s two unvetted entries, one `notes/` audit. Its"
    " record (PR, merge, the owner's enable-or-remove decision) joins the next revision. A server it would enable with file-writing tools"
    " falls under C9 |\n"
)

ERRATA_ANCHOR = (
    "Before starting a handoff's task, check `gh pr list` for it and `ListAgents` for another session on the same handoff.\n"
)
ERRATA_ADDED = (
    "- **E-SPLIT (two answers to one question).** The \"code signing\" and \"mac dev\" sessions each asked the owner how to split H2, H4 and H5."
    " \"code signing\" got H2 and H4 for itself and H5 for \"mac dev\" (2026-10-20). \"mac dev\" got all three for itself, about 10 hours later"
    " and after H2 had merged. The sessions kept the first split by cross-session message, and the owner was told. One session asks; the"
    " other hears the answer by message.\n"
    "- **E-H4-WHEEL (Serena on Intel macOS).** Serena v1.7.0, like 2.0.0 and 2.1.0, pins `cryptography==50.0.0` exactly (\"transitive deps pinned"
    " for security\"), and cryptography ships no x86_64 or universal2 macOS wheel from 49 on. On turing, `uvx` therefore builds 50.0.0 from"
    " source, which needs Rust 1.83 (its `rust-version`); turing's rustup default is 1.71.0, and the build fails (\"lock file version `4` was"
    " found, but this version of Cargo does not understand this lock file\").\n"
    "  - Serena v1.6.1 pins cryptography 48.0.1, which has Intel wheels, but OSV lists CVE-2026-69247, CVE-2026-69248 and CVE-2026-69249 against it,"
    " so it was not taken.\n"
    "  - OWNER, one of: install a Rust 1.83+ toolchain beside 1.71 (`rustup toolchain install <version> --profile minimal`) and build once"
    " (`RUSTUP_TOOLCHAIN=<version> uvx --from git+https://github.com/oraios/serena@949a27ef1e5fda1a6e7b561e777bcece345c6ffd serena --version`,"
    " likely with Homebrew `openssl@3`'s headers); accept v1.6.1 and its CVEs; or keep Serena off turing. A built wheel lives in uv's cache, so"
    " pruning the cache means another build.\n"
    "- **E-SERENA-EDIT (an MCP write channel outside C8).** C8's settings matcher is `Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob`, so an"
    " MCP server's tools never reach the guard.\n"
    "  - Serena v1.7.0's editing tools confine a path to the project root (`Project.validate_relative_path`), but most call it without"
    " `require_not_ignored`, which skips Serena's own rule that ignores `.git`. In a primary checkout, `.git/hooks/` and `.git/config` are"
    " therefore writable through Serena: the class signing plan K12's GIT-SIGNING-FILE rule closes for Claude Code's own tools. In a worktree"
    " `.git` is a file, and the hooks sit outside the root.\n"
    "  - Serena's `read_only: true` (in `.serena/project.yml`, or per checkout in `.serena/project.local.yml`) removes every editing tool, the"
    " shell tool included. The owner kept the tools and ruled C9 instead (§18.1).\n"
)


def edits():
    return [
        ("Version line -> 1.4.3", "- **Version**: 1.4.3 — ", VERSION_OLD, VERSION_NEW),
        ("§18 opening paragraph: the following session", INTRO_ADDED.strip(), INTRO_ANCHOR, INTRO_ANCHOR + INTRO_ADDED),
        ("§18.1 rulings of 2026-10-21", "- **The split of H2, H4 and H5 (2026-10-20).**", RULINGS_ANCHOR, RULINGS_ANCHOR + RULINGS_ADDED),
        ("§18.2 H2, H4, C9 and H5 rows", f"| H2 | landed | {H2_PR}", G1_ROW_TAIL, G1_ROW_TAIL + ROWS),
        ("§18.3 errata E-SPLIT, E-H4-WHEEL, E-SERENA-EDIT", "- **E-SPLIT (two answers to one question).**", ERRATA_ANCHOR, ERRATA_ANCHOR + ERRATA_ADDED),
    ]


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    original, missing = text, 0
    for label, marker, anchor, repl in edits():
        if marker in text:
            print(f"present  {label}")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"applied  {label}")
        else:
            print(f"MISSING  {label}: anchor found {text.count(anchor)} times")
            missing += 1
    if missing:
        print(f"{missing} edit(s) missing; nothing written")
        return 1
    if text != original and not args.dry_run:
        path.write_text(text, encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {1 if text != original else 0} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
