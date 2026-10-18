"""
Show that tests/test_claude_agent_guard.py kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up C8 guard PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task C8;
         D11 item 4, enforcement option (b); the H3 negative tests); util/claude_agent_guard.py;
         util/install_claude_agent_guard.bash; tests/test_claude_agent_guard.py

Each mutant re-introduces one defect into a COPY of the guard or the installer: a dropped flag
spelling, an emitted allow, a fail-open on malformed input, a skipped realpath, an unscanned
``bash -c`` body, lost self-protection, a lost cc-status hook, and so on. The suite then runs
(failfast) against that copy in a scratch tree that mirrors the repo layout; the suite locates its
scripts relative to its own file. A mutant is KILLED when the suite fails. The unmutated control
must pass, or the run is void.

Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes: 0 every mutant killed and the control passed; 1 a mutant survived or the control failed;
2 a mutant's anchor text was not found exactly once (the script changed; update the mutant) or setup
failed.

Usage:
    python3 util/ad-hoc/2026-10-17_turing_c8_guard_mutation_check.py [MUTANT_ID ...]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = "util/claude_agent_guard.py"
INSTALLER = "util/install_claude_agent_guard.bash"
SUITE = "tests/test_claude_agent_guard.py"
STAGED = [GUARD, INSTALLER, SUITE, "tests/redacted_env.py"]

# (mutant id, script, defect re-introduced, [(anchor, replacement), ...])
MUTANTS = [
    ("G1", GUARD, "gh api attached / clustered short flags dropped (-XPOST, -ftitle=x, -iX)", [('elif text.startswith("-") and _cluster_has(text[1:], GH_API_SHORT, GH_API_VALUE_SHORT):', 'elif text in ("-X", "-f", "-F"):')]),
    ("G2", GUARD, "an allowed call emits an explicit allow", [('    if not hits:\n        return 0, "", ""', '    if not hits:\n        return 0, json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}) + "\\n", ""')]),
    ("G3", GUARD, "malformed input fails open (exit 0)", [('return 2, "", "%s: refusing a malformed hook payload', 'return 0, "", "%s: refusing a malformed hook payload')]),
    ("G4", GUARD, "file targets not resolved through symlinks (no realpath)", [("out.extend([literal, os.path.realpath(literal)])", "out.extend([literal])")]),
    ("G5", GUARD, "bash -c / sh -c / zsh -c bodies not scanned", [("            if saw_c:\n                self._scan_generated(text, depth, bases)", "            if saw_c:\n                pass")]),
    ("G6", GUARD, "writes to the user-level settings and hooks not refused", [("        if ctx.is_protected(candidates):", "        if False:")]),
    ("G7", GUARD, "gh api --flag=value spellings dropped (--method=POST, --field=k=v, --input=f)", [('if text[2:].split("=", 1)[0].casefold() in GH_API_LONG:', "if text[2:].casefold() in GH_API_LONG:")]),
    ("G8", GUARD, "the .ssh / .gnupg text match is case-sensitive (APFS is not)", [(r'_CRED_COMPONENT_RE = re.compile(r"(?<![A-Za-z0-9._-])\.(?:ssh|gnupg)(?![A-Za-z0-9._-])", re.IGNORECASE)', r'_CRED_COMPONENT_RE = re.compile(r"(?<![A-Za-z0-9._-])\.(?:ssh|gnupg)(?![A-Za-z0-9._-])")')]),
    ("G9", GUARD, "the component boundary becomes a substring match", [(r'_CRED_COMPONENT_RE = re.compile(r"(?<![A-Za-z0-9._-])\.(?:ssh|gnupg)(?![A-Za-z0-9._-])", re.IGNORECASE)', r'_CRED_COMPONENT_RE = re.compile(r"\.(?:ssh|gnupg)", re.IGNORECASE)')]),
    ("G10", GUARD, "$( ), backtick and process-substitution bodies not scanned", [("        for inner in lexer.nested:\n", "        for inner in []:\n")]),
    ("G11", GUARD, "NAME=value prefixes taken as the command word", [("        if _ASSIGN_RE.match(text) or text in KEYWORDS:", "        if text in KEYWORDS:")]),
    ("G12", GUARD, "ssh -G (prints config, no connection) treated as a probe", [('if dest is not None and not config_only and "github" in dest.casefold():', 'if dest is not None and "github" in dest.casefold():')]),
    ("G13", GUARD, "an unknown tool fails closed instead of passing silently", [("    if tool not in COVERED_TOOLS:\n        return []", '    if tool not in COVERED_TOOLS:\n        raise MalformedInput("unknown tool")')]),
    ("I1", INSTALLER, "--apply replaces the PreToolUse list (the cc-status hook is lost)", [("        pre[:] = [e for e in pre if not ours(e)] + [ENTRY]", "        pre[:] = [ENTRY]")]),
    ("I2", INSTALLER, "a second --apply appends a second entry (not idempotent)", [("    if mine != [ENTRY]:\n        pre[:] = [e for e in pre if not ours(e)] + [ENTRY]", "    if True:\n        pre.append(ENTRY)")]),
    ("I3", INSTALLER, "--dry-run installs the copy anyway", [('        if [[ "$DRY_RUN" -eq 1 ]]; then\n            printf \'DRY-RUN would copy', "        if false; then\n            printf 'DRY-RUN would copy")]),
    ("I4", INSTALLER, "--uninstall also removes deny rules it did not add", [('        drop = [r for r in manifest.get("deny_added", []) if r in perms["deny"]]', '        drop = [r for r in DENY if r in perms["deny"]]')]),
    ("I5", INSTALLER, "the hook entry loses onFailure block (a crashed guard would fail open)", [('"timeout": 10, "onFailure": "block"}]}', '"timeout": 10}]}')]),
]


def stage(tmp: Path) -> None:
    """Mirror the files the suite needs: the suite, the env helper, the guard and the installer."""
    for rel in STAGED:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def suite_passes(tmp: Path) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", "-f", SUITE],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=900,
    )
    return proc.returncode == 0


def main(argv: list) -> int:
    chosen = [m for m in MUTANTS if not argv or m[0] in argv]
    if not chosen:
        print("no mutant matches %s" % " ".join(argv))
        return 2
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        if not suite_passes(tmp):
            print("VOID   control: %s fails on the unmutated scripts" % SUITE)
            return 1
        print("OK     control: %s passes on the unmutated scripts" % SUITE)

        survivors = 0
        for mid, script, defect, edits in chosen:
            original = (REPO / script).read_text(encoding="utf-8")
            mutated = original
            for anchor, replacement in edits:
                if mutated.count(anchor) != 1:
                    print("ANCHOR %s: %r occurs %d times in %s (need exactly 1)" % (mid, anchor, mutated.count(anchor), script))
                    return 2
                mutated = mutated.replace(anchor, replacement)
            (tmp / script).write_text(mutated, encoding="utf-8")
            try:
                killed = not suite_passes(tmp)
            finally:
                (tmp / script).write_text(original, encoding="utf-8")
            survivors += 0 if killed else 1
            print("%-8s %-4s %s" % ("KILLED" if killed else "SURVIVED", mid, defect))

        total = len(chosen)
        print("\n%d of %d mutants killed" % (total - survivors, total))
        return 0 if survivors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
