"""
Show that the A4 and B9 suites kill a mutant for each defect class they claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-16
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up A4/B9 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (tasks A4, B9;
         regressions R-A4, R-B9); util/juniper_clone.bash; util/find_encryption_readme_notes.bash;
         tests/test_juniper_clone.py; tests/test_find_encryption_readme_notes.py

Each mutant re-introduces one defect into a COPY of a script: the eval of juniper-ml#2222, word
splitting, the alias-bypassing origin, a skipped check, and so on. The script's suite then runs
against that copy in a scratch tree that mirrors the repo layout (the suites locate their script
relative to their own file). A mutant is KILLED when the suite fails. The unmutated control must
pass, or the run is void.

Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes: 0 every mutant killed and both controls passed; 1 a mutant survived or a control failed;
2 a mutant's anchor text was not found (the script changed; update the mutant) or setup failed.

Usage:
    python3 util/ad-hoc/2026-10-16_turing_a4_b9_mutation_check.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FINDER = "util/find_encryption_readme_notes.bash"
CLONER = "util/juniper_clone.bash"
SUITES = {
    FINDER: "tests/test_find_encryption_readme_notes.py",
    CLONER: "tests/test_juniper_clone.py",
}

# (script, mutant id, defect re-introduced, [(anchor, replacement), ...])
MUTANTS = [
    (FINDER, "F1", "eval of a found path (the juniper-ml#2222 injection)", [("        printf '%s\\t==> Valid\\n' \"$path\"", "        eval \"ls -d ${path}\" >/dev/null 2>&1 || true\n        printf '%s\\t==> Valid\\n' \"$path\"")]),
    (FINDER, "F2", "word-split find output", [("while IFS= read -r -d '' path; do", 'for path in $("$FIND" "$ROOT" -name "*${PATTERN}*"); do'), ('done < <("$FIND" "$ROOT" -name "*${PATTERN}*" -print0)', "done")]),
    (FINDER, "F3", "CDPATH leaks into the resolved root", [("ROOT=\"$(CDPATH='' cd -- \"$ROOT\" && pwd)\"", 'ROOT="$(cd -- "$ROOT" && pwd)"')]),
    (FINDER, "F4", "an invalid match still exits 0", [('[[ "$invalid" -eq 0 ]] || exit 1', "true")]),
    (FINDER, "F5", "no match exits 0", [("under ${ROOT}\" >&2\n    exit 1", 'under ${ROOT}" >&2\n    exit 0')]),
    (FINDER, "F6", "host-specific default root", [('ROOT="${HOME}/Development"', 'ROOT="/Users/pcalnon/Development"')]),
    (FINDER, "F7", "a '/' in --name is not refused", [("    */*) die_usage", "    */*/*/*/*) die_usage")]),
    (FINDER, "F8", "a directory counts as Valid", [('if [[ -f "$path" ]]; then', 'if [[ -e "$path" ]]; then')]),
    (FINDER, "F9", "a relative root prints relative paths", [("ROOT=\"$(CDPATH='' cd -- \"$ROOT\" && pwd)\"", "true")]),
    (CLONER, "C1", "clone URL bypasses the alias (the old helper)", [('URL="git@${ALIAS}:${OWNER}/${FULL}.git"', 'URL="git@github.com:${OWNER}/${FULL}.git"')]),
    (CLONER, "C2", "persisted origin not verified", [('if [[ "$origin" != "$URL" ]]; then', "if false; then")]),
    (CLONER, "C3", "origin read through insteadOf (remote get-url)", [('origin="$("$GIT" -C "$DEST" config --get remote.origin.url || true)"', 'origin="$("$GIT" -C "$DEST" remote get-url origin || true)"')]),
    (CLONER, "C4", "existing destination not refused", [('if [[ -e "$DEST" || -L "$DEST" ]]; then', "if false; then")]),
    (CLONER, "C5", "alias resolution not enforced", [("    github.com | ssh.github.com) ;;", "    *) ;;")]),
    (CLONER, "C6", "--dry-run still clones", [('if [[ "$DRY_RUN" -eq 1 ]]; then', "if false; then")]),
    (CLONER, "C7", "repo name not validated before ssh", [("name_re='^[a-z0-9][a-z0-9-]*$'", "name_re='.*'")]),
    (CLONER, "C8", "a live ssh call instead of config evaluation", [('"$SSH" -G "$ALIAS"', '"$SSH" -T "$ALIAS"')]),
]


def stage(tmp: Path) -> None:
    """Mirror the files the suites need: the two suites, the env helper and the two scripts."""
    for rel in [*SUITES, *SUITES.values(), "tests/redacted_env.py"]:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def suite_passes(tmp: Path, script: str) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", SUITES[script]],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return proc.returncode == 0


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        for script in SUITES:
            if not suite_passes(tmp, script):
                print(f"VOID   control: {SUITES[script]} fails on the unmutated {script}")
                return 1
            print(f"OK     control: {SUITES[script]} passes on the unmutated {script}")

        survivors = 0
        for script, mid, defect, edits in MUTANTS:
            original = (REPO / script).read_text(encoding="utf-8")
            mutated = original
            for anchor, replacement in edits:
                if mutated.count(anchor) != 1:
                    print(f"ANCHOR {mid}: {anchor!r} occurs {mutated.count(anchor)} times in {script} (need exactly 1)")
                    return 2
                mutated = mutated.replace(anchor, replacement)
            (tmp / script).write_text(mutated, encoding="utf-8")
            try:
                killed = not suite_passes(tmp, script)
            finally:
                (tmp / script).write_text(original, encoding="utf-8")
            survivors += 0 if killed else 1
            print(f"{'KILLED' if killed else 'SURVIVED':8} {mid}  {defect}")

        total = len(MUTANTS)
        print(f"\n{total - survivors} of {total} mutants killed")
        return 0 if survivors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
