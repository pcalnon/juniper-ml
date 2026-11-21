"""
Run the port's two pull-request steps' own shell locally, to see the exact lines a live run's log will hold.

install: the "Install Gitleaks (pull request)" ``run:`` under ``bash -e`` with a stand-in ``curl`` that hands over an
         already-downloaded tarball (no network), once with the release tarball and once with a corrupted copy.
scan:    the "Run Gitleaks over the pull request" ``run:`` under ``bash -e`` with the real engine, in a scratch
         ``git init`` repository that has NO gitleaks config (this repository's case), an ``origin`` URL that is never
         contacted, a base commit and one pull-request commit: the shape of the port's own pull request. A second run
         plants a runtime-built token so the failing path's lines are seen too.

Tokens are assembled at run time and never written outside the scratch repository; the engine redacts its output.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_step_probe.py --workflow <ci.yml> --engine <gitleaks 8.24.3> --tarball <release tarball> --work <new dir>

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
import shlex
import shutil
import string
import subprocess
import sys
from pathlib import Path

import yaml

ANSI = re.compile(r"\x1b\[[0-9;]*m")
INSTALL = "Install Gitleaks (pull request)"
SCAN = "Run Gitleaks over the pull request (Secrets Detection)"
ALPHABET = string.ascii_letters + string.digits


def step_run(workflow: Path, name: str) -> str:
    steps = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    return str(next(step for step in steps if step.get("name") == name)["run"])


def step_env(workflow: Path, name: str) -> dict[str, str]:
    steps = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    return {key: str(value) for key, value in next(step for step in steps if step.get("name") == name).get("env", {}).items()}


def probe_install(workflow: Path, tarball: Path, work: Path, label: str, corrupt: bool) -> dict:
    root = work / f"install-{label}"
    runner_temp = root / "runner-temp"
    bindir = root / "bin"
    runner_temp.mkdir(parents=True)
    bindir.mkdir()
    served = root / "served.tar.gz"
    shutil.copyfile(tarball, served)
    if corrupt:
        with open(served, "ab") as fh:
            fh.write(b"\0")
    # A stand-in curl: it writes the served file to the path that follows --output, and records its argv.
    curl = bindir / "curl"
    curl.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > ' + shlex.quote(str(root / "curl-argv.txt")) + '\nwhile [ "$#" -gt 0 ]; do if [ "$1" = "--output" ]; then cp ' + shlex.quote(str(served)) + ' "$2"; fi; shift; done\n', encoding="utf-8")
    curl.chmod(0o755)
    github_path = root / "github-path.txt"
    env = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', os.defpath)}", "HOME": str(root), "LANG": "C", "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_TEMP": str(runner_temp), "GITHUB_PATH": str(github_path), **step_env(workflow, INSTALL)}
    res = subprocess.run(["bash", "-e", "-c", step_run(workflow, INSTALL)], cwd=root, env=env, capture_output=True, text=True, check=False)
    return {
        "label": label,
        "exit": res.returncode,
        "stdout": res.stdout.replace(str(root), "<root>").splitlines(),
        "stderr": res.stderr.replace(str(root), "<root>").splitlines(),
        "curl_argv": (root / "curl-argv.txt").read_text(encoding="utf-8").replace(str(root), "<root>").splitlines(),
        "github_path": github_path.read_text(encoding="utf-8").replace(str(root), "<root>").splitlines() if github_path.is_file() else None,
        "unpacked": sorted(str(path.relative_to(runner_temp)) for path in runner_temp.rglob("*") if path.is_file()),
    }


def git(repo: Path, *args: str) -> str:
    env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": str(repo.parent), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    res = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} exited {res.returncode}: {res.stderr}")
    return res.stdout.strip()


def commit(repo: Path, rel: str, text: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", "--", rel)
    git(repo, "commit", "--no-verify", "-q", "-m", rel)
    return git(repo, "rev-parse", "HEAD")


def probe_scan(workflow: Path, engine: Path, work: Path, label: str, token: bool) -> dict:
    root = work / f"scan-{label}"
    repo = root / "repo"
    repo.mkdir(parents=True)
    bindir = root / "engine-bin"
    bindir.mkdir()
    (bindir / "gitleaks").symlink_to(engine.resolve())
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "https://github.com/example-Overtoad/example-repo.git")
    base = commit(repo, "README.md", "base\n")
    planted = "gh" + "p_" + "".join(ALPHABET[(11 + i * 29) % len(ALPHABET)] for i in range(36))
    head = commit(repo, "pr/change.txt", ("GITHUB_" + "TOKEN=" + planted + "\n") if token else "a clean change\n")
    runner_temp = root / "runner-temp"
    runner_temp.mkdir()
    summary = root / "step-summary.md"
    env = {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', os.defpath)}", "HOME": str(root), "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "BASE_SHA": base, "HEAD_SHA": head, "PR_COMMITS": "1", "GITHUB_STEP_SUMMARY": str(summary), "RUNNER_TEMP": str(runner_temp)}
    res = subprocess.run(["bash", "-e", "-c", step_run(workflow, SCAN)], cwd=repo, env=env, capture_output=True, text=True, check=False)
    text = ANSI.sub("", res.stdout + res.stderr)
    clear = planted in text or any(planted in path.read_text(encoding="utf-8", errors="replace") for path in (repo / "reports").rglob("*") if path.is_file())
    return {
        "label": label,
        "exit": res.returncode,
        "base": base,
        "head": head,
        "lines": text.replace(str(root), "<root>").replace(planted, "<PLANTED TOKEN IN CLEAR>").splitlines(),
        "summary": summary.read_text(encoding="utf-8").splitlines() if summary.is_file() else None,
        "reports": sorted(str(path.relative_to(repo)) for path in (repo / "reports").rglob("*") if path.is_file()) if (repo / "reports").is_dir() else [],
        "token_in_clear_anywhere": clear,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--workflow", required=True, type=Path)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--tarball", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    out = {
        "install_ok": probe_install(args.workflow, args.tarball, work, "ok", corrupt=False),
        "install_corrupt": probe_install(args.workflow, args.tarball, work, "corrupt", corrupt=True),
        "scan_clean": probe_scan(args.workflow, args.engine, work, "clean", token=False),
        "scan_leak": probe_scan(args.workflow, args.engine, work, "leak", token=True),
    }
    with open(work / "step_probe.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(json.dumps(out, indent=1))
    # The scratch repositories hold the planted token in a commit: delete them once the lines are recorded.
    for name in ("scan-clean", "scan-leak"):
        shutil.rmtree(work / name / "repo", ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
