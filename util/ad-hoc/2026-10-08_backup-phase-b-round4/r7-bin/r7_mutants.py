#!/usr/bin/env python3
"""Round 7: mutants of the round-6 delta (A0 refusal, installer hint). Usage: r7_mutants.py <tree>"""
import re
import subprocess
import sys
from pathlib import Path

REST = "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash"
INST = "util/install_duplicati_service.bash"
A0 = ["tests/test_a0_restore_scripts.py"]
IR = ["tests/test_duplicati_installer_real_path.py"]
M = [
    ("Q01", REST, "production default root changed to /", '${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}', '${YAMAGUCHI_SOURCE_ROOT:-/}', A0),
    ("Q02", REST, "production default root dropped (env-only)", '${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}', '${YAMAGUCHI_SOURCE_ROOT:-/nonexistent}', A0),
    ("Q03", REST, "realpath -m back to readlink -f on OUT", 'OUT_REAL="$(realpath -m -- "${OUT}")"', 'OUT_REAL="$(readlink -f -- "${OUT}" || true)"', A0),
    ("Q04", REST, "case on raw OUT", 'case "${OUT_REAL}/" in', 'case "${OUT}/" in', A0),
    ("Q05", REST, "empty-resolution guard removed", '[[ -n "${SOURCE_ROOT}" && -n "${OUT_REAL}" ]] || { echo "refusing: cannot resolve ${OUT}" >&2; exit 2; }', ':', A0),
    ("Q06", REST, "realpath -s (no symlink resolution)", 'OUT_REAL="$(realpath -m -- "${OUT}")"', 'OUT_REAL="$(realpath -m -s -- "${OUT}")"', A0),
    ("Q07", REST, "SOURCE_ROOT not canonicalised", 'SOURCE_ROOT="$(realpath -m -- "${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}")"', 'SOURCE_ROOT="${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}"', A0),
    ("Q08", INST, "hint drops 'Then read paused-until' line", 'echo "     Then read the stored paused-until (step 8\'s read-back) before starting again."\n', '', IR),
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
        if text.count(old) != 1:
            print(f"{mid} ANCHOR {text.count(old)}x -- SKIPPED ({desc})")
            continue
        p.write_text(text.replace(old, new), encoding="utf-8")
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
