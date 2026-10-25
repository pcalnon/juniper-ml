"""
Show that the guard suite kills a mutant for each defect class the C9 rules (MCP-EDIT-PATH, MCP-REGISTER-*) claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — investigation (suite strength evidence for the C9 guard PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2, task C9);
         notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md (RR-10);
         util/claude_agent_guard.py; util/install_claude_agent_guard.bash; tests/test_claude_agent_guard.py;
         util/ad-hoc/2026-10-20_k12_guard_mutation_check.py (the K12 rules' check, whose shape this follows)

Each mutant re-introduces one C9 defect into a COPY of the guard or its installer. Examples:

- the settings matcher naming only the built-in tools, so no Serena call reaches the hook;
- a Serena edit tool passing silently;
- the realpath reading dropped, so a symlink in the checkout leads out unseen;
- only `.git/hooks` and `.git/config` guarded, not the rest of `.git/`;
- a memory name judged bare, not as `.serena/memories/<name>.md`;
- `replace_in_files`' glob or `repl` unread;
- Serena's shell without the Bash rules;
- the checkout root, or `CLAUDE_PROJECT_DIR`, never consulted;
- `mcp add` allowed, or allowed unless the command word is `claude`;
- `--mcp-config`, `~/.claude.json`, `.mcp.json` or the approval keys allowed;
- the installer writing the 1.1.0 matcher.

The suite then runs against that copy, in a scratch tree that mirrors the repo layout. A mutant is KILLED
when the suite fails, and it must also be killed by its own pin test. The unmutated control must pass,
or the run is void.

Nothing in the repository is modified. This is evidence, not a CI gate.

Exit codes:

- 0: every mutant killed, by the suite and by its pin;
- 1: a mutant survived, or the control failed;
- 2: an anchor was not found exactly once.

Usage:
    python3 util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py [--only ID ...]

`--only` runs just the named mutants (after the control), for a quick re-check of a strengthened pin; a
recorded result is always a full run.
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - runs the unittest suite on a scratch copy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = "util/claude_agent_guard.py"
INSTALLER = "util/install_claude_agent_guard.bash"
SUITE = "tests/test_claude_agent_guard.py"
MATCHER_PIN = "PortabilityAndCliTests.test_c9_settings_matcher_names_the_builtins_and_serenas_edit_tools"
EVERY_TOOL = "McpRuleTests.test_c9_every_serena_edit_tool_is_judged"
EDIT_PATHS = "McpRuleTests.test_c9_serena_edit_paths"
SECOND = "McpRuleTests.test_c9_second_paths_and_memory_names"
REPLACE = "McpRuleTests.test_c9_replace_in_files_scope_and_text"
SHELL = "McpRuleTests.test_c9_serena_shell_gets_the_bash_rules"
ROOTS = "McpRuleTests.test_c9_paths_resolve_against_the_checkout_and_the_project_dir"
REG_BASH = "McpRuleTests.test_c9_mcp_registration_in_bash"
REG_FILE = "McpRuleTests.test_c9_mcp_registration_files"
UPGRADE = "InstallerTests.test_c9_apply_upgrades_a_1_1_0_entry_to_the_new_matcher"

# (id, defect, file, pin test, [(anchor, replacement)])
MUTANTS = [
    ("C1", "the settings matcher names only the built-in tools", GUARD, MATCHER_PIN, [('SETTINGS_MATCHER = "|".join(COVERED_TOOLS)', 'SETTINGS_MATCHER = "|".join(("Bash",) + FILE_TOOLS + SEARCH_TOOLS)')]),
    ("C2", "Serena's edit tools pass silently", GUARD, EVERY_TOOL, [("COVERED_TOOLS = (\"Bash\",) + FILE_TOOLS + SEARCH_TOOLS + MCP_EDIT_TOOLS + MCP_SHELL_TOOLS", "COVERED_TOOLS = (\"Bash\",) + FILE_TOOLS + SEARCH_TOOLS + MCP_SHELL_TOOLS")]),
    ("C3", "the realpath reading is dropped (a symlink in the checkout)", GUARD, EDIT_PATHS, [("        real = os.path.realpath(literal)\n        for candidate, base in", "        real = literal\n        for candidate, base in")]),
    ("C4", "only .git/hooks and .git/config are guarded, not the rest of .git/", GUARD, EDIT_PATHS, [('MCP_GUARDED_DIRS = (".git",) + CRED_DIR_NAMES', "MCP_GUARDED_DIRS = CRED_DIR_NAMES")]),
    ("C5", "a checkout's .claude/settings*.json and .claude/hooks are not guarded", GUARD, EDIT_PATHS, [("        if names(parent, CLAUDE_DIR_NAME) and any(child(comp, c) for c in CLAUDE_PROTECTED_CHILDREN):\n", "        if False:\n")]),
    ("C6", "a .gitconfig or .claude.json outside home is not guarded", GUARD, EDIT_PATHS, [('MCP_GUARDED_FILES = (MCP_PROJECT_FILE, CLAUDE_STATE_FILE, ".gitconfig")', "MCP_GUARDED_FILES = (MCP_PROJECT_FILE,)")]),
    ("C7", "a memory name is judged bare, not as .serena/memories/<name>.md", GUARD, SECOND, [('"%s/%s.md" % (SERENA_MEMORY_DIR, value) if key in SERENA_MEMORY_KEYS else value', "value")]),
    ("C8", "replace_in_files' include glob is never read", GUARD, REPLACE, [('("paths_include_glob",), ("repl",))', '(), ("repl",))')]),
    ("C9", "replace_in_files' repl is never read", GUARD, REPLACE, [('("paths_include_glob",), ("repl",))', '("paths_include_glob",), ())')]),
    ("C10", "a dot-glob (.g?t, .mcp.js?n) never names a dot-name", GUARD, REPLACE, [("    return comp.startswith(\".\") and bool(_glob_literal_chars(comp).strip(\".\")) and component_matches(comp, literal)\n", "    return False\n")]),
    ("C11", "Serena's shell is not given the Bash rules", GUARD, SHELL, [("    elif tool in MCP_SHELL_TOOLS:\n        hits = check_mcp_shell(tool, tool_input, ctx)\n", "    elif tool in MCP_SHELL_TOOLS:\n        hits = []\n")]),
    ("C12", "Serena's shell cwd is not resolved through symlinks", GUARD, SHELL, [("    bases = _with_real(", "    bases = _unique(")]),
    ("C13", "the checkout that holds cwd is not a root", GUARD, ROOTS, [('            if os.path.lexists(os.path.join(cur, ".git")):\n                roots.append(cur)\n                break\n', "            if True:\n                break\n")]),
    ("C14", "CLAUDE_PROJECT_DIR is not consulted", GUARD, ROOTS, [("project = os.environ.get(PROJECT_DIR_ENV) if project_dir is None else project_dir", "project = None if project_dir is None else project_dir")]),
    ("C15", "mcp add / add-json / add-from-claude-desktop is allowed", GUARD, REG_BASH, [("            if word == MCP_SUBCOMMAND:\n", "            if False:\n")]),
    ("C16", "mcp add is denied only after the command word claude (the versions path, npx and $C slip by)", GUARD, REG_BASH, [("        folded = [t.casefold() for t in texts]\n", '        folded = [t.casefold() for t in texts] if res.index is not None and _basename(args[res.index].text) == "claude" else []\n')]),
    ("C17", "--mcp-config is allowed", GUARD, REG_BASH, [("            elif word == MCP_CONFIG_FLAG or word.startswith(MCP_CONFIG_FLAG + \"=\"):\n", "            elif False:\n")]),
    ("C18", "words fed to xargs are not read", GUARD, REG_BASH, [("            texts.extend(t for text in extra for t in text.split())\n", "            pass\n")]),
    ("C19", "the raw-text mention check is gone (comments, heredocs)", GUARD, REG_BASH, [("        m = self.ctx.mcp_register_re().search(text) or _MCP_APPROVAL_RE.search(text)\n", "        m = _MCP_APPROVAL_RE.search(text)\n")]),
    ("C20", "the approval keys are allowed in Bash", GUARD, REG_BASH, [("        m = self.ctx.mcp_register_re().search(text) or _MCP_APPROVAL_RE.search(text)\n", "        m = self.ctx.mcp_register_re().search(text)\n")]),
    ("C21", "~/.claude.json under a home spelling the raw text misses (\"$HOME\"/) is allowed", GUARD, REG_BASH, [("                if len(rest) == 1 and _comp_names(head, CLAUDE_STATE_FILE):\n", "                if False:\n")]),
    ("C22", "a resolved Bash reading of a registration file (a symlink) is missed", GUARD, REG_BASH, [('            if self.ctx.is_mcp_registration(readings):\n                self.hit("MCP-REGISTER-BASH", alt)\n', "")]),
    ("C23", "writer calls on ~/.claude.json and .mcp.json are allowed", GUARD, REG_FILE, [('        if ctx.is_mcp_registration(candidates):\n            hits.append(Hit("MCP-REGISTER-FILE", path))\n', "")]),
    ("C24", "a settings write that sets an approval key is allowed", GUARD, REG_FILE, [("        m = _MCP_APPROVAL_RE.search(_new_content(tool, tool_input)) if settings_like else None\n", "        m = None\n")]),
    ("C25", "only ~/.claude.json counts, not a .mcp.json anywhere", GUARD, REG_FILE, [(" or os.path.basename(c).casefold() == MCP_PROJECT_FILE for c in candidates)", " for c in candidates)")]),
    ("C26", "the installer writes the 1.1.0 matcher", INSTALLER, UPGRADE, [("MATCHER = matcher\n", 'MATCHER = "Bash|Read|Write|Edit|MultiEdit|NotebookEdit|Grep|Glob"\n')]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)
SUITE_MODULE = SUITE.removesuffix(".py").replace("/", ".")


def stage(tmp: Path) -> None:
    for rel in (GUARD, INSTALLER, SUITE, "tests/redacted_env.py", "tests/__init__.py"):
        if (REPO / rel).exists():
            dest = tmp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, target: str) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", "-f", target], cwd=tmp, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    match = FIRST_FAILURE.search(proc.stderr)
    first = f"{match.group(3).split('.')[-2]}.{match.group(2)}" if match else "-"
    return proc.returncode == 0, first


def main(argv: list) -> int:
    only = set(argv[argv.index("--only") + 1 :]) if "--only" in argv else None
    mutants = [m for m in MUTANTS if only is None or m[0] in only]
    if not mutants:
        print(f"no mutant matches --only {sorted(only or [])}")
        return 2
    originals = {rel: (REPO / rel).read_text(encoding="utf-8") for rel in (GUARD, INSTALLER)}
    for mid, _, rel, _, edits in mutants:
        for anchor, _ in edits:
            if originals[rel].count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {originals[rel].count(anchor)} times in {rel} (need exactly 1)")
                return 2
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        passed, first = run_tests(tmp, SUITE)
        if not passed:
            print(f"VOID   control: {SUITE} fails on the unmutated sources (first failure: {first})")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated sources", flush=True)
        survivors = pins_missed = 0
        for mid, defect, rel, pin, edits in mutants:
            mutated = originals[rel]
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / rel).write_text(mutated, encoding="utf-8")
            try:
                suite_passed, first = run_tests(tmp, SUITE)
                pin_passed, _ = run_tests(tmp, f"{SUITE_MODULE}.{pin}")
            finally:
                (tmp / rel).write_text(originals[rel], encoding="utf-8")
            survivors += 1 if suite_passed else 0
            pins_missed += 1 if pin_passed else 0
            print(f"{'SURVIVED' if suite_passed else 'KILLED':8} {mid:4} {defect}\n                first failure: {first}; {'PIN MISSED' if pin_passed else 'pin kills it'}: {pin}", flush=True)
    total = len(mutants)
    print(f"\n{total - survivors} of {total} mutants killed by the suite; {total - pins_missed} of {total} by their own pin test alone")
    return 0 if survivors == 0 and pins_missed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
