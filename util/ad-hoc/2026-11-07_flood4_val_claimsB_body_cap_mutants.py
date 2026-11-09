"""
Mutation check for the flood-4 docs carrier's request-body-cap claim (#2456).

Copies main's juniper_service_core package (.py and py.typed only) plus the named test files
into a scratch directory, flips one `>` to `>=` in RequestBodyLimitMiddleware at a time, and
runs the given test files against each mutant. Shows whether main's shipped body-limit tests
stay green against an equality-rejecting comparison (the carrier says they do) and whether the
tests carrier's boundary file kills it. Removes the scratch copy at the end (pytest does not
ignore tmp/, so a leftover copy of test files would be collected).

Usage: python <this> <service-core dir> <scratch dir> <log path> <test file>...

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier validation (claims lens, slice B: #2456 <-> #2451)
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

MUTANTS = [
    ("middleware.py:122 Content-Length early reject", "if declared_length > self._max_bytes:", "if declared_length >= self._max_bytes:"),
    ("middleware.py:133 cumulative stream read", "if size > self._max_bytes:", "if size >= self._max_bytes:"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_package(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if "__pycache__" in item.parts or not item.is_file():
            continue
        if item.suffix != ".py" and item.name != "py.typed":
            continue
        target = dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)


def run_pytest(copy_root: Path, tests: list[str], log) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(copy_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-m", "pytest", "-c", str(copy_root / "pyproject.toml"), "--rootdir", str(copy_root), "-p", "no:cacheprovider", "-q", *tests]
    proc = subprocess.run(cmd, cwd=copy_root, env=env, capture_output=True, text=True, check=False)
    tail = "\n".join(proc.stdout.strip().splitlines()[-6:])
    log.write(f"$ {' '.join(cmd)}\nexit={proc.returncode}\n{tail}\n{proc.stderr.strip()[-400:]}\n\n")
    return proc.returncode


def main(argv: list[str]) -> int:
    svc = Path(argv[1]).resolve()
    scratch = Path(argv[2]).resolve()
    log_path = Path(argv[3]).resolve()
    test_files = [Path(p).resolve() for p in argv[4:]]
    copy_root = scratch / "svc_copy"
    if copy_root.exists():
        shutil.rmtree(copy_root)
    (copy_root / "tests").mkdir(parents=True)
    copy_package(svc / "juniper_service_core", copy_root / "juniper_service_core")
    shutil.copyfile(svc / "pyproject.toml", copy_root / "pyproject.toml")
    shutil.copyfile(svc / "tests" / "__init__.py", copy_root / "tests" / "__init__.py")
    rel_tests = []
    for tf in test_files:
        shutil.copyfile(tf, copy_root / "tests" / tf.name)
        rel_tests.append(f"tests/{tf.name}")
    target = copy_root / "juniper_service_core" / "middleware.py"
    original = target.read_text()
    before = sha256(target)
    with open(log_path, "w", encoding="utf-8") as log:
        probe = subprocess.run([sys.executable, "-c", "import juniper_service_core as m; print(m.__file__)"], cwd=copy_root, env={**os.environ, "PYTHONPATH": str(copy_root), "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=False)
        log.write(f"interpreter {sys.executable}\nimport resolves to {probe.stdout.strip()}\nmiddleware sha256 before {before}\n\n")
        log.write("== baseline (no mutant) ==\n")
        for rt in rel_tests:
            run_pytest(copy_root, [rt], log)
        for label, old, new in MUTANTS:
            if original.count(old) != 1:
                log.write(f"!! mutant {label}: anchor count {original.count(old)}, skipped\n")
                continue
            target.write_text(original.replace(old, new))
            log.write(f"== mutant {label}: {old!r} -> {new!r} ==\n")
            for rt in rel_tests:
                rc = run_pytest(copy_root, [rt], log)
                log.write(f"RESULT {label} :: {rt} :: {'KILLED' if rc != 0 else 'SURVIVED'}\n\n")
            target.write_text(original)
        after = sha256(target)
        log.write(f"middleware sha256 after {after} restored={after == before}\n")
    shutil.rmtree(copy_root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
