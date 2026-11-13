#!/usr/bin/env python3
"""Run juniper-service-core's suite with ci-service-core.yml's command, on this tree or on an export of a ref.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-11
Status:      ad-hoc -- one-off (round 2 of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); .github/workflows/ci-service-core.yml

The command is the workflow's "Run unit tests" step, with ``PYTHONPATH`` standing in for its two
editable installs (nothing is installed into any environment):

    <python> -m pytest juniper-service-core/tests/ -v --cov=juniper_service_core \\
        --cov-report=term-missing --cov-report=json:<scratch>/coverage-<label>.json --cov-fail-under=80

run from the tree's root, plus ``-p no:cacheprovider`` and a ``--basetemp`` under ``--scratch``
(removed afterwards: the suite's fixture projects must not stay under a checkout's ``tmp/``, where
juniper-ml's ``tests/test_release_train_registry.py`` would find them). ``TMPDIR`` is left as the
session set it. ``--overlay`` copies files over the tree's before the run (a test file copied onto
an export of ``main``, to show it fails there).

The tree is this worktree, or, with ``--export <ref>``, ``git archive`` of that ref's
``juniper-service-core``, ``juniper-model-core`` and root ``pyproject.toml`` (whose coverage
settings the workflow's working directory gives it: branch coverage) unpacked under ``--scratch``;
the export is removed afterwards unless ``--keep-export`` is given (its ``pyproject.toml`` files
are removed either way). Before pytest runs, the interpreter is asked where it imports both packages from, and
anything outside the tree is a setup error. With ``--gap-map`` the workflow's blocking gate runs on
the coverage report (``<gap-map> --coverage-json <file> --enforce``).

Writes ``suite-<label>.log`` (pytest's output), ``coverage-<label>.json``, ``gapmap-<label>.log``
and ``suite-<label>.json`` (the counts, and the coverage report's own total) under ``--scratch``
and prints the JSON. ``--no-cov`` leaves the coverage options out, for a run of a few test files.

Exit status: pytest's (0 or 1), or 1 when the gate fails; 2 on a setup error.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-11_flood4r2_n2-r2_suite.py --python <interpreter> --label <name> \\
        --scratch <scratch dir> [--export <ref>] [--overlay <rel>=<file> ...] [--gap-map <executable>] [<pytest target> ...]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("juniper-service-core", "juniper-model-core")
ROOT_CONFIG = "pyproject.toml"  # the workflow runs at the repository root, whose [tool.coverage.run] turns branch coverage on
_COUNT = re.compile(r"(\d+) (failed|passed|skipped|deselected|errors?|xfailed|xpassed|warnings?)")
_SUMMARY = re.compile(r"^=+ .*\b(?:passed|failed|errors?|no tests ran)\b.* in [0-9.]+s")
_FAILED = re.compile(r"^FAILED (\S+)")


class SetupError(Exception):
    """The run could not be made as designed; no count below it would mean anything."""


def _export(ref: str, dest: Path) -> str:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    sha = subprocess.run(["git", "rev-parse", ref], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    archive = subprocess.run(["git", "archive", "--format=tar", ref, *PACKAGES, ROOT_CONFIG], cwd=REPO_ROOT, capture_output=True, check=False)
    if sha.returncode != 0 or archive.returncode != 0:
        raise SetupError(f"cannot export {ref}: {archive.stderr.decode('utf-8', 'replace').strip()}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(dest, filter="data")
    return sha.stdout.strip()


def _prove_imports(python: str, tree: Path, env: dict[str, str]) -> dict[str, str]:
    code = "import sys, juniper_service_core as s, juniper_model_core as m; print(sys.version.split()[0]); print(s.__file__); print(m.__file__)"
    probe = subprocess.run([python, "-c", code], cwd=tree, env=env, capture_output=True, text=True, check=False)
    lines = probe.stdout.split()
    if probe.returncode != 0 or len(lines) != 3:
        raise SetupError(f"import probe failed: {probe.stderr.strip()[-400:]}")
    for line in lines[1:]:
        if tree.resolve() not in Path(line).resolve().parents:
            raise SetupError(f"{line} is imported from outside the tree {tree}")
    return {"python_version": lines[0], "service_core": lines[1], "model_core": lines[2]}


def _run(args: argparse.Namespace) -> tuple[int, dict]:
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    report: dict = {"label": args.label, "python": args.python}
    export_dir = scratch / f"export-{args.label}"
    if args.export is not None:
        report["ref"] = args.export
        report["sha"] = _export(args.export, export_dir)
        tree = export_dir
    else:
        tree = REPO_ROOT
    report["tree"] = str(tree)
    basetemp = scratch / f"basetemp-{args.label}"
    coverage_json = scratch / f"coverage-{args.label}.json"
    try:
        overlays = []
        for item in args.overlay:
            rel, _, source = item.partition("=")
            target = tree / rel
            if args.export is None:
                raise SetupError("--overlay writes into the tree, so it is allowed only with --export")
            shutil.copyfile(source, target)
            overlays.append({"path": rel, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        report["overlays"] = overlays
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(str(tree / package) for package in PACKAGES)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        env["COVERAGE_FILE"] = str(scratch / f".coverage-{args.label}")
        report["imports"] = _prove_imports(args.python, tree, env)
        report["manager_sha256"] = hashlib.sha256((tree / "juniper-service-core/juniper_service_core/lifecycle/manager.py").read_bytes()).hexdigest()
        targets = args.targets or ["juniper-service-core/tests/"]
        coverage_args = [] if args.no_cov else ["--cov=juniper_service_core", "--cov-report=term-missing", f"--cov-report=json:{coverage_json}", "--cov-fail-under=80"]
        cmd = [args.python, "-m", "pytest", *targets, "-v", *coverage_args, "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
        report["command"] = " ".join(cmd)
        result = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, check=False)
        with open(scratch / f"suite-{args.label}.log", "w", encoding="utf-8") as fh:
            fh.write(result.stdout)
            fh.write(result.stderr)
        lines = result.stdout.splitlines()
        summary = next((line.strip("= ") for line in reversed(lines) if _SUMMARY.match(line)), "")
        report["pytest_exit"] = result.returncode
        report["summary"] = summary
        report["counts"] = {kind: int(number) for number, kind in _COUNT.findall(summary)}
        report["failed"] = [m.group(1) for m in map(_FAILED.match, lines) if m]
        report["coverage_total_percent"] = None
        if not args.no_cov and coverage_json.is_file():
            with open(coverage_json, encoding="utf-8") as fh:
                totals = json.load(fh)["totals"]
            report["coverage_total_percent"] = round(totals["percent_covered"], 2)
            report["coverage_totals"] = {key: totals[key] for key in ("num_statements", "missing_lines", "num_branches", "num_partial_branches")}
        status = result.returncode
        if result.returncode not in (0, 1):
            raise SetupError(f"pytest exited {result.returncode}: {(lines or [result.stderr.strip()])[-1]}")
        if args.gap_map is not None and not args.no_cov and coverage_json.is_file():
            gate = subprocess.run([args.gap_map, "--coverage-json", str(coverage_json), "--enforce"], cwd=tree, capture_output=True, text=True, check=False)
            with open(scratch / f"gapmap-{args.label}.log", "w", encoding="utf-8") as fh:
                fh.write(gate.stdout)
                fh.write(gate.stderr)
            report["gap_map_exit"] = gate.returncode
            status = status or (1 if gate.returncode != 0 else 0)
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
        if export_dir.exists():
            if args.keep_export:
                for project_file in export_dir.rglob("pyproject.toml"):
                    project_file.unlink()
            else:
                shutil.rmtree(export_dir, ignore_errors=True)
    return status, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", required=True, help="an interpreter with juniper-service-core's test dependencies (never installed into)")
    parser.add_argument("--label", required=True, help="names this run's output files")
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch directory in this worktree's tmp/")
    parser.add_argument("--export", help="run on git archive of this ref instead of on the worktree")
    parser.add_argument("--keep-export", action="store_true", help="keep the export (minus its pyproject.toml files) after the run")
    parser.add_argument("--overlay", action="append", default=[], metavar="REL=FILE", help="copy FILE over the export's REL before the run (repeatable)")
    parser.add_argument("--gap-map", help="the juniper-coverage-gap-map executable, to run the workflow's blocking gate")
    parser.add_argument("--no-cov", action="store_true", help="leave the coverage options out (for a run of a few test files, where --cov-fail-under would fail)")
    parser.add_argument("targets", nargs="*", help="pytest targets (default: juniper-service-core/tests/)")
    args = parser.parse_args(argv)

    try:
        status, report = _run(args)
    except (SetupError, OSError) as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return 2
    with open(args.scratch / f"suite-{args.label}.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({key: report.get(key) for key in ("label", "sha", "imports", "summary", "coverage_total_percent", "pytest_exit", "gap_map_exit", "failed")}, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
