#!/usr/bin/env python3
"""
Mutation check for the password-init helper's 1.4.0 environment (Phase D, lane A's A-8): each mutant must be
killed by tests/test_duplicati_wrapper_contract.py's RecoveryHelperGates.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (Phase D round-2 fold-in: lane R2-A's H2 and H3 survived the SAME_USER-only test)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-03_password_init_hand_start.bash 1.4.0; tests/test_duplicati_wrapper_contract.py

Each mutant is applied to a COPY of the helper inside a private copy of the files the test class reads, never to
the checkout; the class runs from the copy's root with bytecode writing off, and the exit code is read directly.
Exit 0 when the unmutated copy passes and every mutant is killed; 1 otherwise.

Usage: python3 util/ad-hoc/2026-10-29_password_init_env_mutation_check.py <scratch-directory>
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = "util/ad-hoc/2026-10-03_password_init_hand_start.bash"
TREES = ("tests", "scripts", "util/systemd", "util/ad-hoc", "util/install_duplicati_service.bash", "util/yamaguchi-pre-backup-guard.bash")
SELECT = "tests.test_duplicati_wrapper_contract.RecoveryHelperGates"
RUN = '"${AS_USER[@]}" "${RUN_ENV[@]}" "${SERVER}" \\\n'
MUTANTS = (
    ("no RUN_ENV at all", RUN, '"${AS_USER[@]}" "${SERVER}" \\\n'),
    ("RUN_ENV placed before sudo", RUN, '"${RUN_ENV[@]}" "${AS_USER[@]}" "${SERVER}" \\\n'),
    ("RUN_ENV only when SAME_USER", '"TMPDIR=${DATA_FOLDER}")\n', '"TMPDIR=${DATA_FOLDER}")\n(( SAME_USER )) || RUN_ENV=()\n'),
    ("no TMPDIR", ' "TMPDIR=${DATA_FOLDER}")\n', ")\n"),
    ("no DO_NOT_TRACK", "RUN_ENV=(env DO_NOT_TRACK=1 ", "RUN_ENV=(env "),
)


def build(root: Path) -> None:
    for rel in TREES:
        src, dst = REPO / rel, root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.exists():
            shutil.copy2(src, dst)


def run_class(root: Path) -> int:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-m", "unittest", SELECT], cwd=root, env=env, capture_output=True, text=True, check=False).returncode


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    scratch = Path(argv[1]).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    base = scratch / "unmutated"
    shutil.rmtree(base, ignore_errors=True)
    build(base)
    rc = run_class(base)
    print(f"unmutated: exit {rc} ({'passes' if rc == 0 else 'FAILS -- no mutant result below means anything'})")
    failed = rc != 0
    for n, (name, old, new) in enumerate(MUTANTS):
        root = scratch / f"mutant-{n:02d}"
        shutil.rmtree(root, ignore_errors=True)
        build(root)
        helper = root / HELPER
        text = helper.read_text(encoding="utf-8")
        if text.count(old) != 1:
            print(f"mutant {n:02d} {name}: NOT APPLIED (the old text occurs {text.count(old)} times)")
            failed = True
            continue
        helper.write_text(text.replace(old, new), encoding="utf-8")
        rc = run_class(root)
        failed |= rc == 0
        print(f"mutant {n:02d} {name}: {'killed' if rc else 'SURVIVED'} (exit {rc})")
        shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(base, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
