#!/usr/bin/env python3
"""Freshness check, GitHub-signed PR open and blob-SHA read-back for the green-informational-3.15-legs PRs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (opened juniper-data-client#262, juniper-cascor-client#197 and juniper-deploy#275)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/open_signed_pr.py (the tool ``open`` drives); util/ad-hoc/2026-11-15_py315_informational_green_legs.py
         (juniper-ml#2578, the workflow edit); util/ad-hoc/2026-11-15_py315_green_legs_changelog.py (the CHANGELOG
         entry); tmp/py315/GREEN_LEGS_BRIEF.md and tmp/py315/ROLLOUT_BRIEF.md "Mechanics" (the rules this follows)

Why this exists
---------------
``util/open_signed_pr.py`` uploads WHOLE files, so a stale base silently reverts whatever landed on ``main`` since.
``freshness`` fetches ``origin/main`` in the primary and refuses if any commit since the worktree's base touches a
path about to be uploaded, or if the primary disagrees with the API. ``open`` builds the ``--add LOCAL:REPOPATH``
arguments from a paths file, so no workflow path is typed on a command line (this host's session refuses some
commands that list ``.github/workflows/`` paths), and refuses a commit body whose last paragraph is not the two
trailer lines. ``readback`` compares each file on the branch with the local copy by git BLOB SHA (the contents API
returns no inline content for files over 1 MB, so a base64 read-back can read empty), then checks the branch head
is GitHub-verified, its message ends with the trailers, and the branch differs from ``main`` in exactly the listed
paths. This copy derives the tool path from its own location and runs under the current interpreter, so no host
path is baked in (gate G5); the run used the same logic with those two paths written out.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_green_legs_pr.py freshness --repo R --primary P --base SHA --paths F
    python3 util/ad-hoc/2026-11-15_py315_green_legs_pr.py open --repo R --worktree W --paths F --title-file T \\
        --commit-body-file C --body-file B [--dry-run]
    python3 util/ad-hoc/2026-11-15_py315_green_legs_pr.py readback --repo R --worktree W --paths F
Exit 0 = fresh / opened / identical.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - shells out to git and gh by design
import sys
from pathlib import Path

BRANCH = "ci/python-3-15-green-legs"
TOOL = Path(__file__).resolve().parents[1] / "open_signed_pr.py"
TRAILERS = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n" "Claude-Session: https://claude.ai/code/session_016H76AjZ1128MZRxWfnK2KY"


def paths_of(path: str) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)  # nosec B603


def freshness(a: argparse.Namespace) -> int:
    r = run(["git", "-C", a.primary, "fetch", "--quiet", "origin", "main"])
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        return 2
    head = run(["git", "-C", a.primary, "rev-parse", "origin/main"]).stdout.strip()
    api = run(["gh", "api", f"repos/pcalnon/{a.repo}/commits/main", "--jq", ".sha"]).stdout.strip()
    count = run(["git", "-C", a.primary, "rev-list", "--count", f"{a.base}..origin/main"]).stdout.strip()
    print(f"base={a.base[:8]} origin/main={head[:8]} api-main={api[:8]} commits-since-base={count}")
    moved = 0
    for p in paths_of(a.paths):
        out = run(["git", "-C", a.primary, "log", "--oneline", f"{a.base}..origin/main", "--", p]).stdout.strip()
        if out:
            print(f"MOVED: {p}\n    " + out.replace("\n", "\n    "))
            moved = 1
        else:
            print(f"fresh: {p}")
    if head != api:
        print("NOT FRESH: the primary's origin/main differs from the API's main")
        moved = 1
    return moved


def open_pr(a: argparse.Namespace) -> int:
    adds: list[str] = []
    for p in paths_of(a.paths):
        local = Path(a.worktree) / p
        if not local.is_file():
            print(f"missing local file: {local}", file=sys.stderr)
            return 2
        adds += ["--add", f"{local}:{p}"]
    body = Path(a.commit_body_file).read_text(encoding="utf-8")
    if not body.rstrip("\n").endswith(TRAILERS) or "\n\n" + TRAILERS not in body:
        print("REFUSED: the commit body does not end with the two trailer lines as its own last paragraph", file=sys.stderr)
        return 2
    title = Path(a.title_file).read_text(encoding="utf-8").strip()
    cmd = [sys.executable, str(TOOL), "--repo", a.repo, "--branch", BRANCH, *adds, "--message", title, "--commit-body-file", a.commit_body_file, "--title", title, "--body-file", a.body_file]
    if a.dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd).returncode  # nosec B603


def readback(a: argparse.Namespace) -> int:
    bad = 0
    for p in paths_of(a.paths):
        remote = run(["gh", "api", f"repos/pcalnon/{a.repo}/contents/{p}?ref={BRANCH}", "--jq", ".sha"]).stdout.strip()
        local = run(["git", "hash-object", "--no-filters", str(Path(a.worktree) / p)]).stdout.strip()
        same = bool(remote) and remote == local
        print(f"{'same  ' if same else 'DIFFER'} remote={remote[:12]} local={local[:12]}  {p}")
        bad |= not same
    info = json.loads(run(["gh", "api", f"repos/pcalnon/{a.repo}/commits/{BRANCH}"]).stdout)
    message = info["commit"]["message"]
    print(f"branch head={info['sha']} parents={[x['sha'][:8] for x in info['parents']]}")
    print(f"verified={info['commit']['verification']['verified']} reason={info['commit']['verification']['reason']}")
    trailers_last = message.rstrip("\n").endswith(TRAILERS) and ("\n\n" + TRAILERS) in message
    print(f"commit message ends with the two trailers as its last paragraph: {trailers_last}")
    files = run(["gh", "api", f"repos/pcalnon/{a.repo}/compare/main...{BRANCH}", "--jq", '[.files[].filename] | sort | join(",")']).stdout.strip()
    expected = ",".join(sorted(paths_of(a.paths)))
    print(f"files on the branch vs main: {files}")
    print(f"exactly the listed paths: {files == expected}")
    return int(bad or not info["commit"]["verification"]["verified"] or not trailers_last or files != expected)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freshness")
    for name in ("--repo", "--primary", "--base", "--paths"):
        f.add_argument(name, required=True)
    o = sub.add_parser("open")
    for name in ("--repo", "--worktree", "--paths", "--title-file", "--commit-body-file", "--body-file"):
        o.add_argument(name, required=True)
    o.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("readback")
    for name in ("--repo", "--worktree", "--paths"):
        r.add_argument(name, required=True)
    a = ap.parse_args()
    return {"freshness": freshness, "open": open_pr, "readback": readback}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
