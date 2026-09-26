#!/usr/bin/env python3
"""Lane A: run the head's tests/test_service_fork_drift.py on minimal synthetic ecosystem roots.

Each root holds juniper-ml (only the two files the test reads: the test itself and service-core's security.py,
both from the head tree) plus whichever siblings the variant keeps, populated with the registry-named files at
each sibling's current main (data 0f0f7e0e, cascor 7f4a7213, canopy 7ab994e5, fetched by ghshow.py).
Variants: all present; each of data / cascor / canopy missing; none; and the env gate (GITHUB_ACTIONS=true,
FORCE_LOCAL, neither). Prints each run's unittest summary line and return code.
"""
import os
import pathlib
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
HEAD = S / "eco/juniper-ml"
SRC = {
    "juniper-data": (S / "src/data_0f0f7e0e", ["juniper_data/api/middleware.py", "juniper_data/api/security.py", "juniper_data/api/app.py"]),
    "juniper-cascor": (S / "src/cascor_main", ["src/api/middleware.py", "src/api/security.py", "src/api/app.py"]),
    "juniper-canopy": (S / "src/canopy_main", ["src/security.py"]),
}
ROOTS = S / "drift_roots"


def build(name: str, keep: list[str]) -> pathlib.Path:
    root = ROOTS / name
    if root.exists():
        shutil.rmtree(root)
    for rel in ("tests/test_service_fork_drift.py", "juniper-service-core/juniper_service_core/security.py"):
        dst = root / "juniper-ml" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HEAD / rel, dst)
    for repo in keep:
        base, rels = SRC[repo]
        for rel in rels:
            dst = root / repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(base / rel, dst)
    return root


def run(root: pathlib.Path, env_extra: dict[str, str]) -> None:
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL")}
    env.update(env_extra)
    r = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests/test_service_fork_drift.py"], cwd=root / "juniper-ml", env=env, capture_output=True, text=True)
    lines = [ln for ln in r.stderr.splitlines() if ln.startswith(("OK", "FAILED", "Ran "))]
    skips = [ln.strip() for ln in r.stderr.splitlines() if "skipped" in ln and "..." in ln]
    print(f"  {root.name:<12} env={env_extra} rc={r.returncode} {' | '.join(lines)}")
    for s in skips:
        print(f"      {s[:170]}")


ALL = ["juniper-data", "juniper-cascor", "juniper-canopy"]
variants = {
    "all": ALL,
    "no-data": ["juniper-cascor", "juniper-canopy"],
    "no-cascor": ["juniper-data", "juniper-canopy"],
    "no-canopy": ["juniper-data", "juniper-cascor"],
    "none": [],
}
for name, keep in variants.items():
    root = build(name, keep)
    run(root, {"GITHUB_ACTIONS": "true"})
run(ROOTS / "all", {"JUNIPER_DRIFT_TEST_FORCE_LOCAL": "1"})
run(ROOTS / "all", {})
shutil.rmtree(ROOTS)
