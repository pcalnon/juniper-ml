"""
Flood-4 validation: the CI matrix runs 3.12 / 3.13 (and 3.14); the builder ran everything on 3.14.7, whose
deferred annotations (PEP 649) can hide a NameError that 3.12 / 3.13 raise at definition time. For each given
interpreter: py_compile every changed .py; run every carrier-touched top-level suite (`-m unittest -v`) and
every carrier-touched sub-package test file (pytest, as its workflow does) in THIS worktree; re-run each failure
in the clean origin/main worktree under the same interpreter and report whether it fails identically there.

Usage: python3 <this> <out.json> <clean_main_tree> <python> [<python> ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"


def changed() -> list[str]:
    return subprocess.run(["git", "diff", "--name-only", BASE, TREE], cwd=HERE, capture_output=True, text=True, check=True).stdout.split()


def run_unit(py: str, tree: Path, suite: str) -> dict[str, object]:
    if not (tree / suite).exists():
        return {"rc": None, "absent": True}
    r = subprocess.run([py, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, timeout=1800)
    text = r.stdout + r.stderr
    return {"rc": r.returncode, "failed": sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", text, re.M))), "errs": sorted(set(re.findall(r"^(\w+Error: .{0,160})$", text, re.M)))[:5], "last": text.strip().splitlines()[-1:]}


def run_pytest(py: str, tree: Path, path: str) -> dict[str, object]:
    if not (tree / path).exists():
        return {"rc": None, "absent": True}
    pkg = path.split("/")[0]
    env = dict(os.environ, PYTHONPATH=str(tree / pkg))
    if pkg == "juniper-service-core":
        cmd, cwd = [py, "-m", "pytest", path, "-q", "-p", "no:cacheprovider"], tree
    else:
        cmd, cwd = [py, "-m", "pytest", path.split("/", 1)[1], "-q", "-p", "no:cacheprovider"], tree / pkg
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1800, env=env)
    text = r.stdout + r.stderr
    return {"rc": r.returncode, "failed": sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", text, re.M))), "errs": sorted(set(re.findall(r"^E\s+(\w+Error: .{0,160})$", text, re.M)))[:5], "last": text.strip().splitlines()[-1:]}


def main() -> int:
    out = Path(sys.argv[1])
    clean = Path(sys.argv[2])
    pys = sys.argv[3:]
    files = changed()
    pyfiles = [f for f in files if f.endswith(".py")]
    suites = [f for f in files if re.match(r"^tests/test_[^/]+\.py$", f)]
    subs = [f for f in files if f.startswith(("juniper-service-core/tests/", "juniper-ci-tools/tests/")) and f.endswith(".py")]
    res: dict[str, object] = {}
    for py in pys:
        ver = subprocess.run([py, "-c", "import sys; print(sys.version.split()[0])"], capture_output=True, text=True).stdout.strip()
        comp = subprocess.run([py, "-m", "py_compile", *pyfiles], cwd=HERE, capture_output=True, text=True)
        with ThreadPoolExecutor(max_workers=6) as pool:
            unit = dict(zip(suites, pool.map(lambda s: run_unit(py, HERE, s), suites)))
            sub = dict(zip(subs, pool.map(lambda s: run_pytest(py, HERE, s), subs)))
        cmp = {}
        for name, r in list(unit.items()) + list(sub.items()):
            if r["rc"] not in (0, None):
                m = run_unit(py, clean, name) if name in unit else run_pytest(py, clean, name)
                cmp[name] = {"carrier": r, "clean_main": m, "same_failed_ids": m.get("failed") == r["failed"]}
        res[ver] = {"py_compile_rc": comp.returncode, "py_compile_err": comp.stderr[-600:], "suites_run": len(suites), "sub_files_run": len(subs), "failing": cmp, "passed": [n for n, r in list(unit.items()) + list(sub.items()) if r["rc"] == 0]}
        print(f"python {ver}: py_compile rc={comp.returncode}; {len(suites)} suites + {len(subs)} sub-package files; failing {len(cmp)}")
        for n, c in cmp.items():
            print(f"   FAIL {n}: carrier failed {len(c['carrier']['failed'])} {c['carrier']['errs'][:2]}; main rc={c['clean_main']['rc']} same ids={c['same_failed_ids']}")
    out.write_text(json.dumps(res, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
