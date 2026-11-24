"""
Scan the port's own change the way its pull request's first live run will: the carrier's scan step over one commit.

A scratch ``git init`` repository gets a base commit holding main's copies of the three modified files, then one
commit holding the carrier's six files (the shape of the signed single-commit pull request), then the carrier's
"Run Gitleaks over the pull request" shell runs under ``bash -e`` with the real engine and no gitleaks config, as in
this repository. Optionally the pull-request texts are scanned too, in the engine's ``dir`` mode. A control run adds a
runtime-built token to the head commit and must fail, so a pass is not vacuous.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_own_diff_scan.py --carrier <tree> --main-blobs <dir> --engine <gitleaks 8.24.3> --work <new dir> [--texts <file> ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

import yaml

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SCAN = "Run Gitleaks over the pull request (Secrets Detection)"
MODIFIED = [".github/workflows/ci.yml", "docs/REFERENCE.md", "CHANGELOG.md"]
ADDED = ["tests/test_gitleaks_pr_scan.py", "util/ad-hoc/2026-11-11_reproduce_gitleaks_pr_commit_window.py", "util/ad-hoc/2026-11-11_verify_gitleaks_pr_scan_tests_are_not_vacuous.py"]
ALPHABET = string.ascii_letters + string.digits


def git(repo: Path, *args: str) -> str:
    env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": str(repo.parent), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    res = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} exited {res.returncode}: {res.stderr}")
    return res.stdout.strip()


def place(repo: Path, source_root: Path, rels: list[str]) -> None:
    for rel in rels:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / rel, target)
    git(repo, "add", "--", *rels)


def run_scan(carrier: Path, engine: Path, root: Path, repo: Path, base: str, head: str) -> dict:
    steps = yaml.safe_load((carrier / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    script = str(next(step for step in steps if step.get("name") == SCAN)["run"])
    bindir = root / "engine-bin"
    bindir.mkdir(exist_ok=True)
    link = bindir / "gitleaks"
    if not link.exists():
        link.symlink_to(engine.resolve())
    runner_temp = root / "runner-temp"
    runner_temp.mkdir(exist_ok=True)
    shutil.rmtree(repo / "reports", ignore_errors=True)
    env = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', os.defpath)}", "HOME": str(root), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "BASE_SHA": base, "HEAD_SHA": head, "PR_COMMITS": git(repo, "rev-list", "--count", f"{base}..{head}"), "RUNNER_TEMP": str(runner_temp)}
    res = subprocess.run(["bash", "-e", "-c", script], cwd=repo, env=env, capture_output=True, text=True, check=False)
    text = ANSI.sub("", res.stdout + res.stderr)
    keep = [line for line in text.splitlines() if any(mark in line for mark in ("Scanning ", "commits scanned", "leaks found", "RuleID", "File:", "Line:", "Fingerprint", "::error", "::warning", "gitleaks config"))]
    return {"exit": res.returncode, "lines": keep}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--main-blobs", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--texts", nargs="*", default=[], type=Path)
    args = parser.parse_args()
    root = args.work.resolve()
    root.mkdir(parents=True, exist_ok=False)
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    place(repo, args.main_blobs, MODIFIED)
    git(repo, "commit", "--no-verify", "-q", "-m", "base: main's copies of the three modified files")
    base = git(repo, "rev-parse", "HEAD")
    place(repo, args.carrier, MODIFIED + ADDED)
    git(repo, "commit", "--no-verify", "-q", "-m", "the port's one commit")
    head = git(repo, "rev-parse", "HEAD")
    out: dict = {"numstat": git(repo, "diff", "--numstat", base, head).splitlines(), "own_diff": run_scan(args.carrier, args.engine, root, repo, base, head)}

    planted = "gh" + "p_" + "".join(ALPHABET[(11 + i * 29) % len(ALPHABET)] for i in range(36))
    (repo / "control.txt").write_text("GITHUB_" + "TOKEN=" + planted + "\n", encoding="utf-8")
    git(repo, "add", "--", "control.txt")
    git(repo, "commit", "--no-verify", "-q", "-m", "control: a planted, runtime-built token")
    control_head = git(repo, "rev-parse", "HEAD")
    out["control"] = run_scan(args.carrier, args.engine, root, repo, base, control_head)

    texts = []
    for text in args.texts:
        res = subprocess.run([str(args.engine), "dir", "--redact", "--no-banner", "--exit-code=2", str(text)], cwd=root, env={"PATH": os.environ.get("PATH", os.defpath), "HOME": str(root)}, capture_output=True, text=True, check=False)
        texts.append({"file": text.name, "exit": res.returncode, "tail": ANSI.sub("", res.stdout + res.stderr).splitlines()[-2:]})
    out["texts_dir_mode"] = texts
    shutil.rmtree(repo, ignore_errors=True)
    out["scratch_repository_deleted"] = not repo.exists()
    with open(root / "own_diff_scan.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(json.dumps(out, indent=1))
    ok = out["own_diff"]["exit"] == 0 and out["control"]["exit"] == 1 and all(entry["exit"] == 0 for entry in texts)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
