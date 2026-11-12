#!/usr/bin/env python3
"""
Attack the git filter that juniper-data's pull-request Gitleaks step puts first on the engine's PATH.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
Round 4 answers a parser defect with a shim: `"${REAL_GIT:?}" "$@" | LC_ALL=C sed -e '/^remerge /d'` under
`set -o pipefail`, written from ci.yml's heredoc. This script takes the shim's text FROM ci.yml (so it tests what
ships), installs it, and compares it with plain git byte for byte: argv with spaces, quotes, globs, an empty argument
and a newline; stdin (text and binary); binary stdout with NUL and no trailing newline; exit codes 0/1/128; git's
stderr; SIGPIPE; a git killed by SIGTERM / SIGKILL; REAL_GIT unset; sed missing. It also records which lines the
shim removes from a real `git log -p -U0 --remerge-diff` (each must be a remerge note) and shows the shim's scope: it
deletes `remerge ` lines from ANY git command's stdout, not only from `git log`.

Usage:
    python3 <this> --ci <ci.yml> --out <scratch dir>
"""

from __future__ import annotations

import argparse
import json
import re
import signal
import subprocess  # nosec B404 - fixed argv: git and the extracted shim in a scratch repository
import sys
from pathlib import Path

import yaml

STEP = "Run Gitleaks over the pull request (Secrets Detection)"
REAL_GIT = "/usr/bin/git"
BASE_ENV = {"PATH": "/usr/bin:/bin", "HOME": "", "LANG": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def shim_text(ci: Path) -> str:
    wf = yaml.safe_load(ci.read_text(encoding="utf-8"))
    steps = wf["jobs"]["security"]["steps"]
    run = next(s["run"] for s in steps if s.get("name") == STEP)
    m = re.search(r"<<'FILTER'\n(.*?)\nFILTER\n", run, re.S)
    if not m:
        raise SystemExit("no FILTER heredoc in the step")
    return m.group(1) + "\n"


def git(repo: Path, env: dict, *args: str, ok: tuple[int, ...] = (0,), stdin: bytes | None = None) -> bytes:
    res = subprocess.run([REAL_GIT, *args], cwd=repo, env=env, input=stdin, capture_output=True, check=False)  # nosec B603
    if res.returncode not in ok:
        raise SystemExit(f"git {args} -> {res.returncode}: {res.stderr!r}")
    return res.stdout


def run_both(repo: Path, env: dict, shim_dir: Path, args: list[str], stdin: bytes | None = None, real_git: str = REAL_GIT, path: str | None = None) -> dict:
    plain = subprocess.run([REAL_GIT, *args], cwd=repo, env=env, input=stdin, capture_output=True, check=False)  # nosec B603
    senv = dict(env)
    senv["REAL_GIT"] = real_git
    senv["PATH"] = path if path is not None else f"{shim_dir}:{env['PATH']}"
    shim = subprocess.run(["git", *args], cwd=repo, env=senv, input=stdin, capture_output=True, check=False)  # nosec B603 B607
    return {
        "args": args,
        "plain_rc": plain.returncode,
        "shim_rc": shim.returncode,
        "stdout_same": plain.stdout == shim.stdout,
        "stderr_same": plain.stderr == shim.stderr,
        "plain_stdout_len": len(plain.stdout),
        "shim_stdout_len": len(shim.stdout),
        "shim_stderr": shim.stderr.decode("utf-8", "replace")[:300],
        "plain_stderr": plain.stderr.decode("utf-8", "replace")[:300],
        "_plain": plain.stdout,
        "_shim": shim.stdout,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out = args.out / "shim"
    out.mkdir(parents=True, exist_ok=True)
    text = shim_text(args.ci)
    shim_dir = out / "filter"
    shim_dir.mkdir(exist_ok=True)
    (shim_dir / "git").write_text(text, encoding="utf-8")
    (shim_dir / "git").chmod(0o755)
    repo = out / "repo"
    if repo.exists():
        subprocess.run(["rm", "-rf", str(repo)], check=True)  # nosec B603 B607
    repo.mkdir()
    env = dict(BASE_ENV)
    env["HOME"] = str(out)
    git(repo, env, "init", "-q", "-b", "main")
    git(repo, env, "config", "commit.gpgsign", "false")
    (repo / "notrail.txt").write_bytes(b"line one\nlast line without newline")
    (repo / "bin.dat").write_bytes(b"\x00\x01remerge x\n\xff\xfe\r\nremerge CONFLICT (content): y\n\x00tail")
    (repo / "looks.txt").write_text("keep\nremerge CONFLICT (content): Merge conflict in fake\nkeep2\n", encoding="utf-8")
    (repo / "conf.txt").write_text("a=1\nb=2\nc=3\n", encoding="utf-8")
    git(repo, env, "add", "-A")
    git(repo, env, "commit", "-q", "-m", "root")
    git(repo, env, "checkout", "-q", "-b", "side")
    (repo / "conf.txt").write_text("a=1\nb=SIDE\nc=3\n", encoding="utf-8")
    git(repo, env, "commit", "-q", "-am", "side: pre-commit autoupdate")
    git(repo, env, "checkout", "-q", "main")
    (repo / "conf.txt").write_text("a=1\nb=MAIN\nc=3\n", encoding="utf-8")
    git(repo, env, "commit", "-q", "-am", "main change")
    git(repo, env, "merge", "-q", "--no-ff", "-m", "merge side", "side", ok=(1,))
    (repo / "conf.txt").write_text("a=1\nb=RESOLVED\nc=3\n", encoding="utf-8")
    git(repo, env, "add", "conf.txt")
    git(repo, env, "commit", "-q", "-m", "merge side")
    blob_notrail = git(repo, env, "rev-parse", "HEAD:notrail.txt").decode().strip()
    blob_bin = git(repo, env, "rev-parse", "HEAD:bin.dat").decode().strip()
    blob_looks = git(repo, env, "rev-parse", "HEAD:looks.txt").decode().strip()
    # fake "real gits" for the failure modes
    fakes = out / "fakes"
    fakes.mkdir(exist_ok=True)
    term = fakes / "git-term"
    term.write_text("#!/bin/sh\nprintf 'partial output\\n'\nkill -TERM $$\n", encoding="utf-8")
    term.chmod(0o755)
    kill9 = fakes / "git-kill9"
    kill9.write_text("#!/bin/sh\nprintf 'partial output\\n'\nkill -KILL $$\n", encoding="utf-8")
    kill9.chmod(0o755)
    cases: list[dict] = []
    tricky = ["a b", "", "x'y", "*", "$HOME", "-n", "tab\there", "l1\nl2", "--", "remerge x"]
    cases.append({"name": "argv fidelity (rev-parse --sq-quote)", **run_both(repo, env, shim_dir, ["rev-parse", "--sq-quote", *tricky])})
    cases.append({"name": "stdin binary (hash-object --stdin)", **run_both(repo, env, shim_dir, ["hash-object", "--stdin"], stdin=b"\x00\xffremerge \n\r\nz")})
    cases.append({"name": "stdin batch (cat-file --batch-check)", **run_both(repo, env, shim_dir, ["cat-file", "--batch-check"], stdin=f"{blob_notrail}\n{blob_bin}\n".encode())})
    cases.append({"name": "no trailing newline (cat-file blob)", **run_both(repo, env, shim_dir, ["cat-file", "blob", blob_notrail])})
    cases.append({"name": "NUL output (ls-files -z)", **run_both(repo, env, shim_dir, ["ls-files", "-z"])})
    cases.append({"name": "exit 128 + stderr (rev-parse --verify missing)", **run_both(repo, env, shim_dir, ["rev-parse", "--verify", "no-such-ref"])})
    (repo / "conf.txt").write_text("dirty\n", encoding="utf-8")
    cases.append({"name": "exit 1 (diff --exit-code)", **run_both(repo, env, shim_dir, ["diff", "--exit-code"])})
    git(repo, env, "checkout", "--", "conf.txt")
    cases.append({"name": "exit 128 no remote (ls-remote --quiet --get-url)", **run_both(repo, env, shim_dir, ["ls-remote", "--quiet", "--get-url"])})
    log = run_both(repo, env, shim_dir, ["-C", ".", "log", "-p", "-U0", "--remerge-diff", "HEAD~1..HEAD"])
    plain_lines = log["_plain"].split(b"\n")
    shim_lines = log["_shim"].split(b"\n")
    removed = [ln.decode() for ln in plain_lines if ln.startswith(b"remerge ")]
    log["expected_after_filter"] = [ln for ln in plain_lines if not ln.startswith(b"remerge ")] == shim_lines
    log["removed_lines"] = removed
    cases.append({"name": "log -p -U0 --remerge-diff (the engine's call)", **log})
    cases.append({"name": "SCOPE: binary blob with remerge lines (cat-file blob)", **run_both(repo, env, shim_dir, ["cat-file", "blob", blob_bin])})
    cases.append({"name": "SCOPE: text blob with a remerge line (show)", **run_both(repo, env, shim_dir, ["show", blob_looks])})
    cases.append({"name": "git killed by SIGTERM", **run_both(repo, env, shim_dir, ["log"], real_git=str(term))})
    cases.append({"name": "git killed by SIGKILL", **run_both(repo, env, shim_dir, ["log"], real_git=str(kill9))})
    cases.append({"name": "REAL_GIT empty", **run_both(repo, env, shim_dir, ["log", "-1"], real_git="")})
    cases.append({"name": "sed not on PATH", **run_both(repo, env, shim_dir, ["log", "-1"], path=f"{shim_dir}")})
    # SIGPIPE: the reader stops after 10 bytes.
    senv = dict(env)
    senv["REAL_GIT"] = REAL_GIT
    senv["PATH"] = f"{shim_dir}:{env['PATH']}"
    proc = subprocess.Popen(["git", "log", "-p", "--all"], cwd=repo, env=senv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec B603 B607
    first = proc.stdout.read(10) if proc.stdout else b""
    if proc.stdout:
        proc.stdout.close()
    err = proc.stderr.read() if proc.stderr else b""
    rc = proc.wait()
    cases.append({"name": "reader closes early (SIGPIPE)", "shim_rc": rc, "first_bytes": first.decode("utf-8", "replace"), "shim_stderr": err.decode("utf-8", "replace")[:300], "sigpipe_rc": 128 + signal.SIGPIPE})
    report = []
    for c in cases:
        report.append({k: v for k, v in c.items() if not k.startswith("_")})
    (out / "shim_attack.json").write_text(json.dumps({"shim_text": text, "cases": report}, indent=2) + "\n")
    for c in report:
        keep = {k: c[k] for k in ("name", "plain_rc", "shim_rc", "stdout_same", "stderr_same", "removed_lines", "expected_after_filter", "shim_stderr") if k in c}
        print(json.dumps(keep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
