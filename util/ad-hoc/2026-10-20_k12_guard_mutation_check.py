"""
Show that the guard suite kills a mutant for each defect class the K12 rules (GIT-SIGNING-*) claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (suite strength evidence for the K12 guard-rules PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (S9, task K12);
         util/claude_agent_guard.py; tests/test_claude_agent_guard.py;
         util/ad-hoc/2026-10-17_turing_c8_guard_mutation_check.py (the C8 rules' own mutation check)

Each mutant re-introduces one K12 defect into a COPY of the guard. Examples:

- `git -c include.path=` allowed;
- `--config-env` allowed;
- a `git config` write of a signing key allowed;
- a read flag misread as a write;
- a `.git/hooks` path in the text missed;
- a file-tool write to `.git/hooks/` allowed;
- the signing tool's `--apply` allowed.

The suite then runs against that copy, in a scratch tree that mirrors the repo layout. A mutant is KILLED
when the suite fails, and it must also be killed by its own pin test. The unmutated control must pass,
or the run is void.

Nothing in the repository is modified. This is evidence, not a CI gate.

Exit codes:

- 0: every mutant killed, by the suite and by its pin;
- 1: a mutant survived, or the control failed;
- 2: an anchor was not found exactly once.

Usage:
    python3 util/ad-hoc/2026-10-20_k12_guard_mutation_check.py
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - runs the unittest suite on a scratch copy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/claude_agent_guard.py"
SUITE = "tests/test_claude_agent_guard.py"
BASH = "BashRuleTests.test_k12_owner_signing_configuration"
FILES = "FileAndSearchRuleTests.test_file_tools"

MUTANTS = [
    ("K1", "git -c include.* / includeIf.* / gpg.*program is allowed", BASH, [('GIT_DASH_C_SIGNING_RE = re.compile(r"^(?:include\\..*|includeif\\..*|gpg\\.(?:[^.]+\\.)?program)$", re.IGNORECASE)', 'GIT_DASH_C_SIGNING_RE = re.compile(r"^(?!)$")')]),
    ("K2", "git --config-env is allowed", BASH, [('                elif text == "--config-env" or text.startswith("--config-env="):\n', "                elif False:\n")]),
    ("K3", "git config is never examined", BASH, [('                    if sub == "config":\n                        self._check_git_config(rest[i:])\n                        return\n', "")]),
    ("K4", "the implicit set form (git config <key> <value>) is allowed", BASH, [('(mode == "write" or (mode == "implicit" and len(positionals) >= 2))', '(mode == "write")')]),
    ("K5", "git config --edit is allowed", BASH, [("            if lowered in GIT_CONFIG_EDIT_FLAGS:\n", "            if False:\n")]),
    ("K6", "removing or renaming a signing section is allowed", BASH, [("            if positionals and GIT_SIGNING_SECTION_RE.match(positionals[0]):\n", "            if False:\n")]),
    ("K7", "a read flag is taken as a write, so reads are denied", BASH, [('                mode = "read" if mode == "implicit" else mode\n', '                mode = "write"\n')]),
    ("K8", "the raw-text mention check is gone (comments, heredocs)", BASH, [('        m = self.ctx.signing_re().search(text)\n        if m:\n            self.hit("GIT-SIGNING-CONFIG", m.group(0))\n', "")]),
    ("K9", "the lexed-word check is gone (a quoted $HOME)", BASH, [('            m = self.ctx.signing_re().search(word.text)\n            if m:\n                self.hit("GIT-SIGNING-CONFIG", m.group(0))\n', "")]),
    ("K10", "file-tool writes to the signing configuration are allowed", FILES, [('        if ctx.is_signing_config(candidates):\n            hits.append(Hit("GIT-SIGNING-FILE", path))\n', "")]),
    ("K11", "file-tool writes under .git/hooks/ are allowed", FILES, [('if after[:1] == ["hooks"] or after in', "if after in")]),
    ("K12", "util/configure_commit_signing.py --apply is allowed", BASH, [('        if writes and "--dry-run" not in texts:\n', "        if False:\n")]),
    ("K13", "--dry-run does not exempt the signing tool", BASH, [('        if writes and "--dry-run" not in texts:\n', "        if writes:\n")]),
    ("K14", "core.hooksPath is not a signing key", BASH, [("|core\\.hookspath|core\\.fsmonitor|", "|core\\.fsmonitor|")]),
    ("K15", "~/.config/git is not protected in Bash text", BASH, [("(?:\\.gitconfig|\\.config/+git)", "(?:\\.gitconfig)")]),
    ("K16", "file-tool writes to the system gitconfigs are allowed", FILES, [(" + list(SYSTEM_GITCONFIGS))", ")")]),
    ("K17", "the system gitconfigs are not protected in Bash text", BASH, [('re.compile(r"%s|%s|%s" % (home, hooks, system), re.IGNORECASE)', 're.compile(r"%s|%s" % (home, hooks), re.IGNORECASE)')]),
    ("K18", "file-tool writes to a repository's .git/config or config.worktree are allowed", FILES, [('after in (["config"], ["config.worktree"]) or (len(after) == 3 and after[0] == "worktrees" and after[2] == "config.worktree")', "False")]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)
SUITE_MODULE = SUITE.removesuffix(".py").replace("/", ".")


def stage(tmp: Path) -> None:
    for rel in (SCRIPT, SUITE, "tests/redacted_env.py", "tests/__init__.py", "util/install_claude_agent_guard.bash"):
        if (REPO / rel).exists():
            dest = tmp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, target: str) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "unittest", "-f", target], cwd=tmp, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    match = FIRST_FAILURE.search(proc.stderr)
    first = f"{match.group(3).split('.')[-2]}.{match.group(2)}" if match else "-"
    return proc.returncode == 0, first


def main() -> int:
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    for mid, _, _, edits in MUTANTS:
        for anchor, _ in edits:
            if original.count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {original.count(anchor)} times in {SCRIPT} (need exactly 1)")
                return 2
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        passed, first = run_tests(tmp, SUITE)
        if not passed:
            print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT} (first failure: {first})")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}", flush=True)
        survivors = pins_missed = 0
        for mid, defect, pin, edits in MUTANTS:
            mutated = original
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / SCRIPT).write_text(mutated, encoding="utf-8")
            try:
                suite_passed, first = run_tests(tmp, SUITE)
                pin_passed, _ = run_tests(tmp, f"{SUITE_MODULE}.{pin}")
            finally:
                (tmp / SCRIPT).write_text(original, encoding="utf-8")
            survivors += 1 if suite_passed else 0
            pins_missed += 1 if pin_passed else 0
            print(f"{'SURVIVED' if suite_passed else 'KILLED':8} {mid:4} {defect}\n                first failure: {first}; {'PIN MISSED' if pin_passed else 'pin kills it'}: {pin}", flush=True)
    total = len(MUTANTS)
    print(f"\n{total - survivors} of {total} mutants killed by the suite; {total - pins_missed} of {total} by their own pin test alone")
    return 0 if survivors == 0 and pins_missed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
