#!/usr/bin/env python3
"""
Re-derive, independently of the builder's probe, what the ml-docs carrier says about predict_merge's scratch:
a shallow cut above the merge base, the same cut with the shallow copy switched off, a cut below the merge base
(and a linked worktree of that source), and an inherited GIT_DIR on a .py and on a .md delta.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check C)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/fleet_triage/predict_merge.py; tests/test_predict_merge.py (NoMutationTest)

Every fixture lives under --work (a directory the caller owns); nothing is pushed and no checkout but the
fixtures is touched. Run with juniper-symbol-loss-check / juniper-docs-additions-check on PATH for the GIT_DIR cases.

Usage:
  2026-11-14_flood4r2_val_ml-docs_scratch_probe.py --repo <juniper-ml checkout> --work <dir> --out <report.json>
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

FIXTURE_ENV = {"GIT_AUTHOR_NAME": "Probe", "GIT_AUTHOR_EMAIL": "probe@example.invalid", "GIT_COMMITTER_NAME": "Probe", "GIT_COMMITTER_EMAIL": "probe@example.invalid"}


def sh(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(FIXTURE_ENV)
    done = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, env=env, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {cwd}: {done.stderr.strip()}")
    return done.stdout


def init(path: Path) -> None:
    path.mkdir(parents=True)
    sh(path, "init", "-q", "-b", "main")
    sh(path, "config", "commit.gpgsign", "false")


def commit(repo: Path, rel: str, text: str, msg: str) -> None:
    (repo / rel).write_text(text, encoding="utf-8")
    sh(repo, "add", "-A")
    sh(repo, "commit", "-q", "-m", msg)


def load(repo: Path):
    spec = importlib.util.spec_from_file_location("predict_merge_probe_target", repo / "util" / "fleet_triage" / "predict_merge.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def attempt(pm, *args, **kw) -> dict:
    try:
        v = pm.simulate_merge(*args, **kw)
        gates = v.get("gates", {})
        return {"verdict": v["verdict"], "true_delta": v.get("true_delta"), "ast": gates.get("ast_symbol_screen"), "docs": gates.get("docs_additions_only")}
    except pm.PredictMergeError as exc:
        return {"error": str(exc)}


def cut_above(work: Path) -> Path:
    up = work / "up_above"
    init(up)
    commit(up, "fileA.txt", "A0\n", "m0")
    commit(up, "fileB.txt", "B\n", "m1")
    src = work / "src_above"
    sh(work, "clone", "-q", f"file://{up}", str(src))
    sh(up, "checkout", "-q", "-b", "pr")
    commit(up, "fileP.txt", "P\n", "c1")
    commit(up, "fileA.txt", "A-pr\n", "c2")
    sh(up, "checkout", "-q", "main")
    commit(up, "fileA.txt", "A-main\n", "m2")
    sh(src, "fetch", "-q", "origin", "main:refs/remotes/origin/main")
    sh(src, "fetch", "-q", "--depth=1", "origin", "pr:refs/remotes/origin/pr")
    return src


def cut_below(work: Path) -> Path:
    up = work / "up_below"
    init(up)
    for i in range(4):
        commit(up, f"m{i}.txt", f"{i}\n", f"m{i}")
    sh(up, "checkout", "-q", "-b", "pr")
    commit(up, "fileP.txt", "P\n", "c1")
    sh(up, "checkout", "-q", "main")
    commit(up, "m4.txt", "4\n", "m4")
    src = work / "src_below"
    sh(work, "clone", "-q", "--depth=3", "--no-single-branch", f"file://{up}", str(src))
    return src


def git_dir_case(work: Path, name: str, rel: str) -> Path:
    repo = work / name
    init(repo)
    commit(repo, "fileA.txt", "A0\n", "c0")
    sh(repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
    sh(repo, "checkout", "-q", "-b", "clean")
    commit(repo, rel, "def f():\n    return 1\n" if rel.endswith(".py") else "# Title\n\ntext\n", "add file")
    return repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    work = Path(args.work)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    scratch = work / "scratch"
    scratch.mkdir()
    pm = load(Path(args.repo))
    report = {"git_version": subprocess.run(["git", "--version"], capture_output=True, text=True, check=False).stdout.strip()}

    src = cut_above(work)
    report["shallow_source_above"] = sh(src, "rev-parse", "--is-shallow-repository").strip()
    report["cut_above_merge_base"] = attempt(pm, src, "origin/pr", run_gates=False, scratch_parent=scratch)
    real_copy = shutil.copyfile

    def no_shallow_copy(a, b, *rest, **kw):
        if str(a).endswith("/shallow"):
            return b
        return real_copy(a, b, *rest, **kw)

    with mock.patch.object(pm.shutil, "copyfile", no_shallow_copy):
        report["cut_above_without_shallow_copy"] = attempt(pm, src, "origin/pr", run_gates=False, scratch_parent=scratch)

    below = cut_below(work)
    report["shallow_source_below"] = sh(below, "rev-parse", "--is-shallow-repository").strip()
    report["cut_below_merge_base"] = attempt(pm, below, "origin/pr", run_gates=False, scratch_parent=scratch)
    wt = work / "wt_below"
    sh(below, "worktree", "add", "-q", "--detach", str(wt), "origin/main")
    report["cut_below_linked_worktree"] = attempt(pm, wt, "origin/pr", run_gates=False, scratch_parent=scratch)

    for name, rel in (("gitdir_py", "mod.py"), ("gitdir_md", "docs/page.md")):
        if rel.startswith("docs/"):
            repo = work / name
            init(repo)
            (repo / "docs").mkdir()
            commit(repo, "docs/page.md", "# Title\n\none\ntwo\nthree\nfour\nfive\nsix\n", "c0")
            sh(repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
            sh(repo, "checkout", "-q", "-b", "clean")
            commit(repo, "docs/page.md", "# Title\n\none\n", "cut a run")
        else:
            repo = git_dir_case(work, name, rel)
        report[f"{name}_plain"] = attempt(pm, repo, "clean", run_gates=False, scratch_parent=scratch)
        with mock.patch.dict(os.environ, {"GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo)}):
            report[f"{name}_inherited_GIT_DIR"] = attempt(pm, repo, "clean", run_gates=False, scratch_parent=scratch)
    report["scratch_left"] = sorted(p.name for p in scratch.iterdir())
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
