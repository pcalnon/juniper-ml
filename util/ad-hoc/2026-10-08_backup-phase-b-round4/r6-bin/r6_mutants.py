#!/usr/bin/env python3
"""Round 6: a few fresh mutants of the round-5 delta (A0 scripts, installer hint/mode check).

Usage: r6_mutants.py <tree>   (a git-archive extraction of ee7fcee7; files restored after each mutant)
"""
import re
import subprocess
import sys
from pathlib import Path

PREM = "util/ad-hoc/2026-09-22_confirm_a0_premise.bash"
REST = "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash"
INST = "util/install_duplicati_service.bash"
A0 = ["tests/test_a0_restore_scripts.py"]
IR = ["tests/test_duplicati_installer_real_path.py"]
M = [
    ("N01", REST, "frozen index handed over as --dbpath", '"--dbpath=${TMPDB}"', '"--dbpath=${JOBDB}"', A0),
    ("N02", REST, "temporary -journal not removed", '"${TMPDB}-shm" "${TMPDB}-journal"', '"${TMPDB}-shm"', A0),
    ("N03", REST, "restore dir made 0755", 'install -d -m 0700 "${OUT}"', 'install -d -m 0755 "${OUT}"', A0),
    ("N04", REST, "passphrase also on argv", '--version=0 "--dbpath=${TMPDB}" "--restore-path=${OUT}"', '--version=0 "--dbpath=${TMPDB}" "--restore-path=${OUT}" "--passphrase=${PASSPHRASE}"', A0),
    ("N05", REST, "sibling -wal copied but -journal not", 'for sfx in -wal -journal; do', 'for sfx in -wal; do', A0),
    ("N06", PREM, "premise lists version 1", "--version=0", "--version=1", A0),
    ("N07", INST, "symlink refusal does not exit", 'replace it with a regular file, ${ENV_MODES_ACCEPTED}" >&2\n        exit 2\n', 'replace it with a regular file, ${ENV_MODES_ACCEPTED}" >&2\n', IR),
    ("N08", INST, "hint drops 'do not pause' reason line", 'echo "     be running, and step 10\'s resume would continue it with the options it started with."\n', '', IR),
    ("N09", INST, "restart sentence moved BEFORE the guard block", None, None, IR),
    ("N10", INST, "0600 root:duplicati accepted (service cannot read)", "        root:duplicati:640|duplicati:duplicati:600) ;;", "        root:duplicati:640|root:duplicati:600|duplicati:duplicati:600) ;;", IR),
]


def run(tree, suites):
    r = subprocess.run([sys.executable, "-m", "unittest", *suites], cwd=tree, capture_output=True, text=True, timeout=900,
                       env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(tree)})
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", r.stderr, re.M)))
    return r.returncode == 0, ", ".join(fails)


def main():
    tree = Path(sys.argv[1])
    killed = total = 0
    for mid, rel, desc, old, new, suites in M:
        p = tree / rel
        orig = p.read_bytes()
        text = orig.decode()
        if mid == "N09":
            blk = ('echo "  5. Then, on A0, A2 and B, restart the unit before resume (step 10): sudo systemctl stop duplicati.service,"\n'
                   'echo "     then sudo systemctl start duplicati.service; serverstate must exit 2 again; read the edits back with"\n'
                   'echo "     export <id> (step 10 lists what to check) -- and only then resume. On Procedure A, P0.5b runs here instead."\n')
            anchor = 'echo "  4. Before any resume (step 10)'
            if text.count(blk) != 1 or text.count(anchor) != 1:
                print(f"{mid} ANCHOR missing -- SKIPPED")
                continue
            text = text.replace(blk, "").replace(anchor, blk + anchor)
        else:
            if text.count(old) != 1:
                print(f"{mid} ANCHOR {text.count(old)}x -- SKIPPED ({desc})")
                continue
            text = text.replace(old, new)
        p.write_text(text, encoding="utf-8")
        try:
            ok, fails = run(tree, suites)
        finally:
            p.write_bytes(orig)
        total += 1
        killed += not ok
        print(f"{mid} {'KILLED  ' if not ok else 'SURVIVED'} {desc} [{fails}]", flush=True)
    print(f"killed {killed} of {total}")


if __name__ == "__main__":
    main()
