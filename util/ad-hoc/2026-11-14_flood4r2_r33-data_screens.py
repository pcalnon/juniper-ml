#!/usr/bin/env python3
"""
Local screens for the juniper-data benchmark smoke-run carrier: the pinned pre-commit on every changed file, actionlint
on the workflow (main's copy and the carrier's), the CodeQL prescreen on the changed Python files, the freeze
directory the sequence-safety probe reads, and the sha256 of every carrier file.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, juniper-data benchmark smoke run)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: the Overtoad's ruling of 2026-11-14, a daily smoke run of the 41 benchmarks)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads the <out-dir>/freeze directory this writes),
         util/ad-hoc/2026-10-05_codeql_python_prescreen.py

The changed files are read from `git status --porcelain --untracked-files=all` in the carrier tree, so the list
cannot drift from the tree. pre-commit runs from the tree's root with the session-8 python shim first on PATH and the
six Sentry DSN variables empty; each file's sha256 is taken before and after, so a hook that rewrites a file shows.
actionlint 1.7.12 runs with shellcheck on the `run:` blocks; it is not one of juniper-data's own gates, so its result
is informational, and main's copy is screened too so that a finding already on main is not charged to the carrier.

Usage:
    python3 <this> --tree <carrier tree> --main-copy <main tree copy> --base <main sha> --out-dir <scratch>
        --o-dir <orchestrator worktree>
Exit 0 = pre-commit passed without rewriting anything and the CodeQL prescreen found nothing; 1 = otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv: git (read-only), pre-commit, actionlint and the prescreen
import sys
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
PRE_COMMIT = "/opt/miniforge3/bin/pre-commit"
ACTIONLINT = "/opt/miniforge3/envs/JuniperCascor1/bin/actionlint"
SHELLCHECK = "/usr/bin/shellcheck"
WORKFLOW = ".github/workflows/scheduled-tests.yml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def env_with_shim(o_dir: Path) -> dict[str, str]:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env["PATH"] = f"{o_dir / 'tmp' / 'flood4' / 'session8' / 'pyshim'}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
    return env


def changed_files(tree: Path) -> list[tuple[str, str]]:
    done = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=tree, capture_output=True, text=True, check=True)  # nosec B603 B607
    rows = []
    for line in done.stdout.splitlines():
        code, path = line[:2], line[3:]
        rows.append(("added" if code == "??" else "deleted" if "D" in code else "modified", path))
    return sorted(rows, key=lambda row: row[1])


def run_logged(argv: list[str], cwd: Path, env: dict[str, str], log: Path, timeout: int = 1800) -> int:
    done = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout)  # nosec B603
    log.write_text(f"$ {' '.join(argv)}\n(cwd {cwd})\n{done.stdout}{done.stderr}\nexit={done.returncode}\n", encoding="utf-8")
    return done.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--main-copy", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--o-dir", required=True, type=Path)
    ns = parser.parse_args()
    tree, out = ns.tree.resolve(), ns.out_dir.resolve()
    env = env_with_shim(ns.o_dir.resolve())
    files = changed_files(tree)
    paths = [path for status, path in files if status != "deleted"]
    result: dict = {"tree": str(tree), "base": ns.base, "files": [{"path": path, "status": status} for status, path in files]}

    before = {path: sha256(tree / path) for path in paths}
    result["pre_commit_exit"] = run_logged([PRE_COMMIT, "run", "--files", *paths], tree, env, out / "pre_commit.log")
    after = {path: sha256(tree / path) for path in paths}
    result["pre_commit_rewrote"] = sorted(path for path in paths if before[path] != after[path])
    result["pre_commit_log"] = str(out / "pre_commit.log")

    lint_env = {**env}
    result["actionlint_tree_exit"] = run_logged([ACTIONLINT, "-shellcheck", SHELLCHECK, WORKFLOW], tree, lint_env, out / "actionlint_tree.log", timeout=300)
    result["actionlint_main_exit"] = run_logged([ACTIONLINT, "-shellcheck", SHELLCHECK, WORKFLOW], ns.main_copy.resolve(), lint_env, out / "actionlint_main.log", timeout=300)

    python_files = [path for path in paths if path.endswith(".py")]
    prescreen = ns.o_dir.resolve() / "util" / "ad-hoc" / "2026-10-05_codeql_python_prescreen.py"
    result["codeql_prescreen_files"] = python_files
    result["codeql_prescreen_exit"] = run_logged(["python3", str(prescreen), *python_files], tree, env, out / "codeql_prescreen.log", timeout=300) if python_files else None

    freeze = out / "freeze"
    if freeze.exists():
        shutil.rmtree(freeze)
    (freeze / "snapshot").mkdir(parents=True)
    lines = []
    for status, path in files:
        if status == "deleted":
            lines.append(f"delete {path}")
            continue
        target = freeze / "snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tree / path, target)
        lines.append(f"add {path}")
    (freeze / "paths.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (freeze / "plan.json").write_text(json.dumps({"main_sha": ns.base, "tree": str(tree)}, indent=1) + "\n", encoding="utf-8")
    result["freeze"] = str(freeze)

    result["sha256"] = {path: sha256(tree / path) for path in paths}
    (out / "sha256_final.txt").write_text("".join(f"{digest}  {path}\n" for path, digest in sorted(result["sha256"].items())), encoding="utf-8")
    (out / "screens.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "sha256"}, indent=1))
    ok = result["pre_commit_exit"] == 0 and not result["pre_commit_rewrote"] and result["codeql_prescreen_exit"] in (0, None)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
