#!/usr/bin/env python3
"""
Run the round-3 validator's --remerge-diff shapes through ci.yml's pull-request scan step, before and after round 4, on a real gitleaks.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (round 4 of the juniper-data pull-request Gitleaks fix: findings R3-01 and R3-02)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
The round-3 validator proved two defects of the round-2 step on gitleaks 8.24.3: an octopus merge's own changes pass
silently (R3-01), and a finding in a merge's own changes loses its commit when the conflict note holds the word
"commit" (R3-02). Round 4 adds an octopus refusal and a git filter. This driver builds the validator's own shapes with
its own builders (probe_shapes.py, probe_subject.py and validator A's scan_harness.py, imported READ-ONLY from the
validator's scripts directory with bytecode writing off) and runs each through the step's run: block, extracted from a
given ci.yml, under `bash -e`, once for round 2's ci.yml and once for round 4's. It differs from the validator's own
step() in one way: the round-4 step needs RUNNER_TEMP, which GitHub sets for every step, so the driver sets it.

Fail-closed probes run through both steps too: a git that rejects --remerge-diff (as git < 2.36 does), no engine on
PATH, and, for round 4, RUNNER_TEMP unset. Tokens are validator A's FAKE-marked values, built at runtime and committed
only into synthetic repositories under --out, which have no remote. Reports are redacted; the driver prints no token.

Usage:
    python3 -B <this> --engine <gitleaks 8.24.3> --validator-scripts <dir> --r2-ci <ci.yml> --r4-ci <ci.yml> --worktree <juniper-data worktree> --out <dir>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess  # nosec B404 - fixed argv: bash running the extracted step, git
import sys
from pathlib import Path

import yaml

STEP_NAME = "Run Gitleaks over the pull request (Secrets Detection)"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extract(ci: Path, dest: Path) -> Path:
    steps = yaml.safe_load(ci.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    found = [s for s in steps if s.get("name") == STEP_NAME]
    if len(found) != 1 or "shell" in found[0]:
        raise SystemExit(f"{ci}: expected one {STEP_NAME!r} step that names no shell")
    dest.write_text(found[0]["run"], encoding="utf-8")
    return dest


def run_step(probe, harness, repo, engine_bin: Path, stepfile: Path, base: str, head: str, n: str, runner_temp: Path | None, extra_path: list[Path] | None = None, path_override: str | None = None) -> dict:
    """probe_shapes.step(), plus RUNNER_TEMP, which GitHub sets for every step (None leaves it unset)."""
    sarif = repo.dir / "reports" / "security" / "gitleaks.sarif"
    if sarif.exists():
        sarif.unlink()
    env = harness.git_env(repo.home)
    path = f"{engine_bin}{os.pathsep}{env['PATH']}"
    if extra_path:
        path = os.pathsep.join(str(p) for p in extra_path) + os.pathsep + path
    if path_override is not None:
        path = path_override
    env.update({"PATH": path, "BASE_SHA": base, "HEAD_SHA": head, "PR_COMMITS": n, "GITHUB_STEP_SUMMARY": str(repo.root / "step-summary.md")})
    if runner_temp is not None:
        runner_temp.mkdir(parents=True, exist_ok=True)
        env["RUNNER_TEMP"] = str(runner_temp)
    res = subprocess.run(["bash", "-e", str(stepfile)], cwd=repo.dir, env=env, capture_output=True, text=True, timeout=600, check=False)  # nosec B603 B607
    log = res.stdout + res.stderr
    (repo.root / "step.log").write_text(log, encoding="utf-8")
    facts = probe.log_facts(log)
    results = probe.sarif_details(sarif)
    return {"exit": res.returncode, "reported": sorted({(r.get("commit", ""), r.get("uri", "")) for r in results if "uri" in r}), "results": results, **facts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--validator-scripts", type=Path, required=True, help="the round-3 validator's scripts/ directory (read only)")
    ap.add_argument("--r2-ci", type=Path, required=True, help="round 2's ci.yml (the pre-round-4 copy)")
    ap.add_argument("--r4-ci", type=Path, required=True, help="round 4's ci.yml (the carrier's)")
    ap.add_argument("--worktree", type=Path, required=True, help="the juniper-data worktree whose .gitleaks.toml and .gitleaksignore seed each repository")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.dont_write_bytecode = True  # importing the validator's modules must not write into its directory
    probe = load("probe_shapes", args.validator_scripts / "probe_shapes.py")
    subject = load("probe_subject", args.validator_scripts / "probe_subject.py")
    harness = probe.H
    harness.WT = args.worktree
    engine = args.engine.resolve()
    report: dict[str, dict] = {}
    for label, ci in (("r2", args.r2_ci), ("r4", args.r4_ci)):
        out = (args.out / label).resolve()
        out.mkdir(parents=True, exist_ok=True)
        harness.OUT = out
        engine_bin = out / "engine-bin"
        engine_bin.mkdir(exist_ok=True)
        link = engine_bin / "gitleaks"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(engine)
        stepfile = extract(ci, out / "pr_scan_step.sh")
        runner_temp = out / "runner-temp"
        shapes = {
            "octopus_clean": probe.octopus(out, evil=False),
            "octopus_evil": probe.octopus(out, evil=True),
            "two_parent_evil_control": probe.two_parent_evil(out),
            "commit_path_precommit_config": probe.conflict_path_with_commit(out, ".pre-commit-config.yaml"),
            "control_path_without_commit": probe.conflict_path_with_commit(out, ".pre-flight-config.yaml"),
            "subject_with_the_word": subject.build(out, "chore: pre-commit autoupdate", "subject-with-the-word"),
            "subject_without_it": subject.build(out, "chore: hooks autoupdate", "subject-without-it"),
            "deletion_only": probe.deletion_only(out, token_on_base_side=False),
            "deletion_only_base_token": probe.deletion_only(out, token_on_base_side=True),
            "binary_conflict_then_token": probe.binary_conflict_then_token(out),
            "clean_merge_main_token_plus_pr_token": probe.clean_merge_main_token_plus_pr_token(out),
        }
        rows: dict[str, dict] = {}
        for name, (repo, base, head, meta) in shapes.items():
            res = run_step(probe, harness, repo, engine_bin, stepfile, base, head, str(len(repo.pr_list(base, head))), runner_temp)
            res.pop("results")
            rows[name] = {**meta, **res}
            print(json.dumps({label: {name: {k: rows[name][k] for k in ("exit", "reported", "annotations", "scanned")}}}), flush=True)
        # Fail-closed probes through the same step.
        oldgit = out / "oldgit-bin"
        oldgit.mkdir(exist_ok=True)
        (oldgit / "git").write_text('#!/bin/sh\nfor a in "$@"; do\n  if [ "$a" = "--remerge-diff" ]; then\n    echo "fatal: unrecognized argument: --remerge-diff" >&2\n    exit 128\n  fi\ndone\nexec /usr/bin/git "$@"\n', encoding="utf-8")
        (oldgit / "git").chmod(0o755)
        clean = harness.Repo(out / "fc-clean")
        b = clean.commit("main/m1.txt", "m1\n")
        h = clean.linear("pr", 3, {})[-1]
        tokened = harness.Repo(out / "fc-token")
        bt = tokened.commit("main/m1.txt", "m1\n")
        shas = tokened.linear("pr", 3, {2: harness.fake_token(127)})
        empty = out / "empty-bin"
        empty.mkdir(exist_ok=True)
        fail_closed = {
            "old_git_clean_range": run_step(probe, harness, clean, engine_bin, stepfile, b, h, "3", runner_temp, extra_path=[oldgit]),
            "old_git_token_range": run_step(probe, harness, tokened, engine_bin, stepfile, bt, shas[-1], "3", runner_temp, extra_path=[oldgit]),
            "missing_binary": run_step(probe, harness, clean, empty, stepfile, b, h, "3", runner_temp, path_override=f"{empty}{os.pathsep}/usr/bin{os.pathsep}/bin"),
            "runner_temp_unset_token_range": run_step(probe, harness, tokened, engine_bin, stepfile, bt, shas[-1], "3", None),
        }
        for name, res in fail_closed.items():
            res.pop("results")
            print(json.dumps({label: {name: {k: res[k] for k in ("exit", "reported", "annotations", "git_error_lines")}}}), flush=True)
        report[label] = {"ci": str(ci), "shapes": rows, "fail_closed": fail_closed}
    (args.out / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"results: {args.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
