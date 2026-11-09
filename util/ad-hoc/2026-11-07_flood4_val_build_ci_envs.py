"""
Build the CI-parity venvs for juniper-service-core (ci-service-core.yml: 3.12, 3.13, plus a 3.14
extra) and juniper-ci-tools (ci-ci-tools.yml: 3.11..3.14), editable from the validator worktree,
plus one gate venv holding PyPI juniper-ci-tools>=0.9.0,<0.10.0 (the per-file coverage gate both
workflows install after pytest). Logs every command and its exit status.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <worktree> <venv root> <log file>
"""

import os
import subprocess
import sys

INTERPRETERS = {
    "3.11": "/usr/bin/python3.11",
    "3.12": "/opt/miniforge3/bin/python3.12",
    "3.13": os.path.expanduser("~/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/bin/python3.13"),
    "3.14": "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14",
}
UV = "/opt/miniforge3/envs/JuniperCascor1/bin/uv"


def run(cmd, log, cwd):
    log.write(f"\n$ (cwd={cwd}) {' '.join(cmd)}\n")
    log.flush()
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write(proc.stdout)
    log.write(f"[exit {proc.returncode}]\n")
    log.flush()
    return proc.returncode


def main(argv):
    wt, root, log_path = argv[1:4]
    os.makedirs(root, exist_ok=True)
    plan = []
    for ver in ("3.12", "3.13", "3.14"):
        plan.append((f"sc-{ver}", ver, [["-e", "juniper-model-core"], ["-e", "juniper-service-core/.[test]"]]))
    for ver in ("3.11", "3.12", "3.13", "3.14"):
        plan.append((f"ct-{ver}", ver, [["-e", "juniper-ci-tools/.[test]"]]))
    plan.append(("gate-3.12", "3.12", [["juniper-ci-tools>=0.9.0,<0.10.0"]]))
    failures = 0
    with open(log_path, "w") as log:
        for name, ver, installs in plan:
            venv = os.path.join(root, name)
            rc = run([UV, "venv", "--python", INTERPRETERS[ver], venv], log, wt)
            failures += rc != 0
            for spec in installs:
                rc = run([UV, "pip", "install", "--python", os.path.join(venv, "bin", "python"), *spec], log, wt)
                failures += rc != 0
            run([UV, "pip", "freeze", "--python", os.path.join(venv, "bin", "python")], log, wt)
    print(f"failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
