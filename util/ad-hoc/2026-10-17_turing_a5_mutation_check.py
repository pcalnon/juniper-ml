"""
Show that the A5 suite kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up A5 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task A5, D2, §13);
         util/juniper_repo_ssh_setup.bash; tests/test_juniper_repo_ssh_setup.py;
         util/ad-hoc/2026-10-16_turing_a4_b9_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of util/juniper_repo_ssh_setup.bash: a dropped
idempotency check, an AddKeysToAgent yes block, an in-place (non-atomic) write, a skipped mode
check, and so on. The suite then runs against that copy in a scratch tree that mirrors the repo
layout (the suite locates the script relative to its own file). A mutant is KILLED when the suite
fails. The unmutated control must pass, or the run is void.

Nothing in the repository is modified, and nothing outside the scratch tree is touched: the suite is
hermetic (scratch HOME, explicit --ssh-dir, stub ssh-keygen/ssh/uname). Not wired into CI: it is
evidence, not a gate.

Exit codes: 0 every mutant killed and the control passed; 1 a mutant survived or the control failed;
2 a mutant's anchor text was not found (the script changed; update the mutant) or setup failed.

Usage:
    python3 util/ad-hoc/2026-10-17_turing_a5_mutation_check.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/juniper_repo_ssh_setup.bash"
SUITE = "tests/test_juniper_repo_ssh_setup.py"

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("M1", "idempotency dropped: an existing block is appended again", [('    count="$(count_blocks)"', "    count=0")]),
    ("M2", "the canonical block carries AddKeysToAgent yes", [('  AddKeysToAgent no"', '  AddKeysToAgent yes"')]),
    ("M3", "non-atomic write: the config is rewritten in place", [('    mv -f "$TMP_CONFIG" "$CONFIG"', '    cat "$TMP_CONFIG" >"$CONFIG"')]),
    ("M4", "an existing key's mode is not checked", [('    elif ! mode_is "$KEY" 600; then', "    elif false; then")]),
    ("M5", "a key without its .pub is not diagnosed", [('    if [[ ! -e "$PUB" ]]; then', "    if false; then")]),
    ("M6", "UseKeychain written on every platform", [('if [[ "$OS" == "Darwin" ]]; then', "if true; then")]),
    ("M7", "--dry-run writes", [('if [[ "$DRY_RUN" -eq 1 ]]; then', "if false; then")]),
    ("M8", "ssh -G hostname not checked", [('    if [[ "$host" != "github.com" ]]; then', "    if false; then")]),
    ("M9", "no -F for a --ssh-dir other than ~/.ssh", [('    CHECK_CONFIG="${CONFIG}"', '    CHECK_CONFIG=""')]),
    ("M10", "a non-canonical existing block (AddKeysToAgent yes) is accepted", [('        if [[ "$existing" == "$CANONICAL" ]]; then', "        if true; then")]),
    ("M11", "no blank-line separation from the preceding content", [("                printf '\\n\\n'", "                printf '\\n'"), ("                [[ -z \"${last//[[:space:]]/}\" ]] || printf '\\n'", "                true")]),
    ("M12", "a new key's modes are left as ssh-keygen made them", [('    chmod 600 "$KEY"\n    chmod 644 "$PUB"', "    true")]),
    ("M13", "the alias is matched as a substring of another Host name", [("if (pats[i] == alias) { count++; break }", "if (index(pats[i], alias)) { count++; break }")]),
    ("M14", "the candidate config is installed without the ssh -G pre-check", [('    resolve_check "$TMP_CONFIG" || rc=$?', "    true")]),
    ("M15", "the temp file is made outside the ssh directory (mv across filesystems is not atomic)", [('mktemp "${SSH_DIR}/.config.juniper_repo_ssh_setup.XXXXXX"', "mktemp")]),
    ("M16", "an extra identity file is tolerated (containment, not equality)", [('    if [[ "$ids" != "$IDENTITY" ]]; then', '    if [[ "$ids" != *"$IDENTITY"* ]]; then')]),
]


def stage(tmp: Path) -> None:
    """Mirror the files the suite needs: the suite, the env helper and the script."""
    for rel in (SCRIPT, SUITE, "tests/redacted_env.py"):
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def suite_passes(tmp: Path) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", SUITE],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.returncode == 0


def main() -> int:
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        try:
            stage(tmp)
        except OSError as exc:
            print(f"SETUP  failed to stage the scratch tree: {exc}")
            return 2
        if not suite_passes(tmp):
            print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT}")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}")

        survivors = 0
        for mid, defect, edits in MUTANTS:
            mutated = original
            for anchor, replacement in edits:
                if mutated.count(anchor) != 1:
                    print(f"ANCHOR {mid}: {anchor!r} occurs {mutated.count(anchor)} times in {SCRIPT} (need exactly 1)")
                    return 2
                mutated = mutated.replace(anchor, replacement)
            (tmp / SCRIPT).write_text(mutated, encoding="utf-8")
            try:
                killed = not suite_passes(tmp)
            finally:
                (tmp / SCRIPT).write_text(original, encoding="utf-8")
            survivors += 0 if killed else 1
            print(f"{'KILLED' if killed else 'SURVIVED':8} {mid:4} {defect}")

        total = len(MUTANTS)
        print(f"\n{total - survivors} of {total} mutants killed")
        return 0 if survivors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
