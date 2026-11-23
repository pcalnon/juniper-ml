"""Replay a pull request's commits in a scratch git repo and run cascor's two sequence-safety screens on it.

Usage: python3 -I probe_screens.py DEST BASE_TREE [TREE BODY_FILE ...]
DEST must not exist. Commit 0 is BASE_TREE; each TREE / BODY_FILE pair is one more commit, its message
read from BODY_FILE (first line = headline). The commits are local, unsigned and never pushed: they exist
only so the screens can read a BASE..HEAD range, as cascor's sequence-safety.yml does
(juniper-symbol-loss-check --scope 'src/**/*.py'; juniper-docs-additions-check). Prints both screens'
output and exits with the worse of their exit codes.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

IGNORE = shutil.ignore_patterns(".git", "tmp", "__pycache__", ".benchmarks", ".pytest_cache", "*.pyc")
SCREENS = "/opt/miniforge3/envs/JuniperCascor1/bin"


def git(dest: Path, *argv: str) -> str:
    cmd = ["git", "-c", "commit.gpgsign=false", "-c", "user.name=probe", "-c", "user.email=probe@localhost", *argv]
    proc = subprocess.run(cmd, cwd=dest, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(argv)} failed: {proc.stderr}")
    return proc.stdout.strip()


def load(dest: Path, tree: Path) -> None:
    for child in dest.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(tree, dest, symlinks=True, ignore=IGNORE, dirs_exist_ok=True)


def main() -> int:
    dest, base = Path(sys.argv[1]), Path(sys.argv[2])
    pairs = sys.argv[3:]
    if dest.exists() or len(pairs) % 2:
        print("REFUSED: DEST exists, or a TREE has no BODY_FILE")
        return 2
    dest.mkdir(parents=True)
    git(dest, "init", "-q")
    load(dest, base)
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "base")
    base_sha = git(dest, "rev-parse", "HEAD")
    for tree, body in zip(pairs[::2], pairs[1::2]):
        load(dest, Path(tree))
        git(dest, "add", "-A")
        git(dest, "commit", "-q", "--allow-empty", "-F", str(Path(body).resolve()))
    print(git(dest, "log", "--oneline", f"{base_sha}..HEAD"))
    worst = 0
    for argv in ([f"{SCREENS}/juniper-symbol-loss-check", "--scope", "src/**/*.py", "--base", base_sha, "--head", "HEAD"], [f"{SCREENS}/juniper-docs-additions-check", "--base", base_sha, "--head", "HEAD"]):
        proc = subprocess.run(argv, cwd=dest, capture_output=True, text=True, check=False)
        print(f"--- {Path(argv[0]).name}: exit {proc.returncode}")
        print(proc.stdout)
        print(proc.stderr)
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
