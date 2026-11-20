"""
Re-derive the git claims juniper-ml#2515's sign-edges suite rests on, on this host's git.

Claims checked, each in a fresh throwaway repository under --root (never the checkout):
  1. git's LAST `-c` wins: `-c commit.gpgsign=false -c commit.gpgsign=true` reads back `true`, and a
     commit under that pair asks gpg.program to sign;
  2. `git commit -mS x` is the message `S` and does not sign;
  3. `git pull -h`, `git am -h`, `git revert -h`, `git cherry-pick -h` and `git commit-tree -h` list `-S`.
gpg.program is a recording stub that exits 1, so "signing was attempted" is visible as the stub's
marker file and a failed commit; nothing is ever signed. Prints one line per claim and exits 0 only
when every claim holds.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_git_probe.py --root <empty scratch dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2515 (tests/test_claude_agent_guard_sign_edges.py)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k == "GIT_CEILING_DIRECTORIES"}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False, env=env)


def _repo(root: Path, name: str, stub: Path) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "probe@example.invalid")
    _git(repo, "config", "user.name", "Probe")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "gpg.program", str(stub))
    return repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    root = Path(ap.parse_args().root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "gpg_called.txt"
    stub = root / "gpg_stub.sh"
    stub.write_text(f"#!/bin/sh\necho \"$@\" >> '{marker}'\nexit 1\n", encoding="utf-8")
    stub.chmod(0o755)
    ok = True
    print(_git(root, "--version").stdout.strip())

    repo = _repo(root, "later_c", stub)
    value = _git(repo, "-c", "commit.gpgsign=false", "-c", "commit.gpgsign=true", "config", "--get", "commit.gpgsign").stdout.strip()
    marker.unlink(missing_ok=True)
    commit = _git(repo, "-c", "commit.gpgsign=false", "-c", "commit.gpgsign=true", "commit", "--allow-empty", "-m", "x")
    signed = marker.exists()
    claim1 = value == "true" and commit.returncode != 0 and signed
    ok &= claim1
    print(f"claim 1 last -c wins: config --get={value!r} commit_rc={commit.returncode} gpg_stub_called={signed} -> {'HOLDS' if claim1 else 'FAILS'}")

    repo = _repo(root, "message_s", stub)
    (repo / "x").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "x")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "x").write_text("y\n", encoding="utf-8")
    marker.unlink(missing_ok=True)
    commit = _git(repo, "commit", "-mS", "x")
    message = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    sig = _git(repo, "log", "-1", "--format=%G?").stdout.strip()
    claim2 = commit.returncode == 0 and message == "S" and not marker.exists() and sig == "N"
    ok &= claim2
    print(f"claim 2 -mS is a message: rc={commit.returncode} message={message!r} %G?={sig!r} gpg_stub_called={marker.exists()} -> {'HOLDS' if claim2 else 'FAILS'}")

    lists = {}
    for sub in ("pull", "am", "revert", "cherry-pick", "commit-tree"):
        out = _git(root, sub, "-h")
        lists[sub] = "-S" in (out.stdout + out.stderr)
    claim3 = all(lists.values())
    ok &= claim3
    print(f"claim 3 -h lists -S: {lists} -> {'HOLDS' if claim3 else 'FAILS'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
