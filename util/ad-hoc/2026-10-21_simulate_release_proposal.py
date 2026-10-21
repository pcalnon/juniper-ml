#!/usr/bin/env python3
"""Simulate one release-train proposal on a scratch copy of the tree, then run the suites it must keep green.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — investigation (the propose.py README compatibility-table gaps)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/release_train/propose.py; prompts/thread-handoff_automated-prompts/
         HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md
         (Landing rules: "Simulate the proposal before --execute")

Why this exists
---------------
``propose.py --dry-run`` prints the proposal's diffs but runs none of the gates the proposal PR will meet.
The juniper-ml 0.11.0 cut found its README lead-in gap only because a session applied the generator's
edits to a scratch copy by hand and ran the suites, with a scratchpad script hard-coded to 0.10.0 -> 0.11.0.
This is the general form. It builds the proposal with ``propose.build_proposal`` from the COPY's own
``util/release_train/``, writes every edit's full ``new_text`` into the copy, and runs the suites that read
the version, the extras pins, README or REFERENCE. Each suite runs twice: on the untouched copy (the
baseline) and after the edits. Only a suite that passes at baseline and fails after the edits is charged
to the proposal. On macOS some suites are red at baseline, and those are reported as pre-existing.

Nothing in ``--repo-root`` is written. The copy is built under ``--sim-dir``, which must not exist yet or
must carry this script's marker from an earlier run. It is wiped and rebuilt. Sibling repos are never read:
propagation edges to them come out "unknown".

``build_proposal`` refuses to move an empty ``[Unreleased]``. ``--seed-unreleased`` adds one placeholder
bullet to the copy's CHANGELOG first, which simulates the next cut of a package whose notes are not written.

Usage
-----
    python3 util/ad-hoc/2026-10-21_simulate_release_proposal.py --package juniper-config-tools \\
        --from-version 0.1.0 --to-version 0.2.0 --sim-dir <scratch>/sim [--repo-root <tree>] \\
        [--seed-unreleased] [--suite tests/test_x.py ...]

Exit codes: 0 when the proposal builds and no suite regresses; 1 when a suite passes at baseline and fails
after the edits; 2 when the proposal is refused or the invocation is wrong.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_MARKER = ".release-proposal-sim"
_IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", "logs", "reports", "papers", "images")

#: The suites that read the package version, the extras pins, README or REFERENCE (the 0.11.0 cut's set,
#: plus the global text search the pin-raise recipe runs).
DEFAULT_SUITES = (
    "tests/test_pyproject_extras.py",
    "tests/test_agents_md_version_drift.py",
    "tests/test_agents_md_header_schema.py",
    "tests/test_agents_md_touch_up.py",
    "tests/test_service_core_drift.py",
    "tests/test_model_core_drift.py",
    "tests/test_doc_tools_drift.py",
    "tests/test_ci_tools_drift.py",
    "tests/test_template_library_drift.py",
    "tests/test_coverage_gap_mapper_drift.py",
    "tests/test_env_floor_drift_check.py",
    "tests/test_env_drift_check_drift.py",
    "tests/test_editable_install_drift_check.py",
    "tests/test_publish_testpypi_verify.py",
    "tests/test_release_train_registry.py",
    "tests/test_release_train_workflow_guard.py",
    "tests/test_global_text_search.py",
)


def _bump(from_version: str, to_version: str) -> str:
    old = [int(p) for p in re.findall(r"\d+", from_version)[:3]]
    new = [int(p) for p in re.findall(r"\d+", to_version)[:3]]
    if new[0] != old[0]:
        return "major"
    return "minor" if new[1] != old[1] else "patch"


def _fresh_sim_dir(sim: Path) -> None:
    if sim.exists():
        if not (sim / _MARKER).is_file():
            raise SystemExit(f"ERROR: {sim} exists and has no {_MARKER} marker -- refusing to wipe it")
        shutil.rmtree(sim)


def _seed_unreleased(changelog: Path) -> None:
    text = changelog.read_text(encoding="utf-8")
    heading = re.search(r"^## \[Unreleased\][ \t]*\n", text, re.MULTILINE)
    if heading is None:
        raise SystemExit(f"ERROR: {changelog}: no '## [Unreleased]' heading to seed")
    bullet = "\n### Fixed\n\n- Simulated entry (util/ad-hoc/2026-10-21_simulate_release_proposal.py --seed-unreleased).\n"
    changelog.write_text(text[: heading.end()] + bullet + text[heading.end():], encoding="utf-8")


def _run_suites(tree: Path, suites: list) -> dict:
    results: dict = {}
    for suite in suites:
        if not (tree / suite).is_file():
            results[suite] = (None, "absent")
            continue
        proc = subprocess.run([sys.executable, "-B", "-m", "unittest", suite], cwd=tree, capture_output=True, text=True)
        fails = [ln for ln in (proc.stderr or "").splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        tail = [ln for ln in (proc.stderr or proc.stdout).strip().splitlines() if ln.strip()]
        results[suite] = (proc.returncode == 0, "; ".join(fails[:6]) or (tail[-1] if tail else ""))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", required=True, help="pypi_name from util/release_train/registry.yaml")
    ap.add_argument("--from-version", required=True, help="the released version the proposal bumps from")
    ap.add_argument("--to-version", required=True, help="the version the proposal bumps to")
    ap.add_argument("--sim-dir", required=True, help="scratch directory for the copy (wiped and rebuilt)")
    ap.add_argument("--repo-root", default=str(_REPO), help="the tree to copy (default: this checkout)")
    ap.add_argument("--seed-unreleased", action="store_true", help="add a placeholder bullet to an empty [Unreleased] in the copy")
    ap.add_argument("--suite", action="append", help="a suite to run instead of the defaults (repeatable)")
    args = ap.parse_args()

    src = Path(args.repo_root).resolve()
    sim = Path(args.sim_dir).resolve()
    if sim == src or src in sim.parents:
        print(f"ERROR: --sim-dir {sim} must lie outside --repo-root {src}", file=sys.stderr)
        return 2
    _fresh_sim_dir(sim)
    shutil.copytree(src, sim, ignore=_IGNORE, symlinks=True)
    (sim / _MARKER).write_text(f"copy of {src}\n", encoding="utf-8")

    sys.path.insert(0, str(sim / "util" / "release_train"))
    import detect  # noqa: E402,PLC0415 - the copy's own release-train modules are the code under test
    import propose  # noqa: E402,PLC0415

    entries = detect.load_registry(None)
    entry = {e.pypi_name: e for e in entries}.get(args.package)
    if entry is None:
        print(f"ERROR: {args.package} is not in the registry", file=sys.stderr)
        return 2
    if entry.repo != detect.META_REPO:
        print(f"ERROR: {args.package} lives in {entry.repo}; this simulates juniper-ml packages only", file=sys.stderr)
        return 2
    if args.seed_unreleased:
        _seed_unreleased(sim / propose._changelog_rel(entry))

    suites = list(args.suite or DEFAULT_SUITES)
    baseline = _run_suites(sim, suites)

    def read_file(e, filename):
        try:
            return (detect.base_dir_for(e, sim, sim.parent / "no-siblings") / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    pkg = {
        "pypi_name": args.package,
        "repo": entry.repo,
        "released_version": args.from_version,
        "declared_version": args.from_version,
        "classification": propose.PROPOSABLE,
        "proposed_bump": _bump(args.from_version, args.to_version),
        "proposed_version": args.to_version,
        "ship_evidence": [],
        "changelog_conflict": None,
    }
    sources = propose.ProposeSources(read_file=read_file, list_open_prs=lambda repo: [])
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prop = propose.build_proposal(entry, pkg, sources, sim, sim.parent / "no-siblings", entries, date)
    if prop.skipped:
        print(f"REFUSED: {prop.skipped_reason}", file=sys.stderr)
        return 2

    print(f"proposal {args.package} {args.from_version} -> {args.to_version} [{pkg['proposed_bump']}]: {len(prop.edits)} edit(s)")
    for edit in prop.edits:
        target = sim / edit.path
        if sim not in target.resolve().parents:
            print(f"ERROR: {edit.path} resolves outside the copy ({target.resolve()}) -- refusing to write it", file=sys.stderr)
            return 2
        target.write_text(edit.new_text, encoding="utf-8")
        print(f"  wrote {edit.path}")
    for item in prop.co_change_checklist:
        if "REQUIRED" in item:
            print(f"  checklist REQUIRED: {item[:160]}")

    after = _run_suites(sim, suites)
    regressed = 0
    for suite in suites:
        was, _ = baseline[suite]
        now, detail = after[suite]
        if now is None:
            print(f"  ---- {suite}: absent")
        elif now:
            print(f"  OK   {suite}")
        elif was:
            regressed += 1
            print(f"  FAIL {suite} (passes at baseline): {detail}")
        else:
            print(f"  red  {suite} (red at baseline too, not the proposal's): {detail}")
    print(f"{regressed} suite(s) regressed by the proposal")
    return 1 if regressed else 0


if __name__ == "__main__":
    raise SystemExit(main())
