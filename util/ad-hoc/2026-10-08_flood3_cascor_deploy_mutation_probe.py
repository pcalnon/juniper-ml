#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc
# File Name:     2026-10-08_flood3_mutation_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#    Single-use helper for the Cursor flood #3 evaluation (cascor-deploy slice). Applies ONE
#    exact-string mutation to a production file inside a DISPOSABLE sibling worktree, runs a test
#    command, records whether the tests went red, then restores the file byte-for-byte from the
#    copy it read before mutating (no git operations), and verifies the restore by sha256.
#
#    Usage:
#      2026-10-08_flood3_mutation_probe.py --file <abs path> --old <text> --new <text> \
#          --cwd <dir> --label <name> -- <test command...>
#      --old / --new accept Python unicode escapes (\n, \t, \").
#    Exit: 0 = mutation KILLED (tests failed), 1 = mutation SURVIVED (tests passed),
#          2 = usage error (anchor not matched exactly once), 3 = restore failed.
#####################################################################################################################################################################################################
from __future__ import annotations

import argparse
import hashlib
import subprocess  # nosec B404 - runs a caller-supplied local test command
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        print("no test command", file=sys.stderr)
        return 2
    path = Path(a.file)
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    old = a.old.encode("utf-8").decode("unicode_escape")
    new = a.new.encode("utf-8").decode("unicode_escape")
    n = text.count(old)
    if n != 1:
        print(f"[{a.label}] anchor must match exactly once, matched {n}: {old!r}", file=sys.stderr)
        return 2
    path.write_text(text.replace(old, new), encoding="utf-8")
    try:
        proc = subprocess.run(cmd, cwd=a.cwd, capture_output=True, text=True, check=False)  # nosec B603
    finally:
        path.write_bytes(original)
    restored = hashlib.sha256(path.read_bytes()).hexdigest() == digest
    lines = (proc.stdout + proc.stderr).splitlines()
    summary = [ln for ln in lines if (" passed" in ln or " failed" in ln or " error" in ln) and " in " in ln]
    failed = [ln for ln in lines if ln.startswith(("FAILED", "ERROR"))]
    verdict = "KILLED" if proc.returncode != 0 else "SURVIVED"
    print(f"[{a.label}] {verdict} rc={proc.returncode} restored={restored} :: {summary[-1].strip() if summary else '(no summary)'}")
    for ln in failed[:15]:
        print(f"    {ln[:200]}")
    if not restored:
        print("RESTORE FAILED", file=sys.stderr)
        return 3
    return 0 if verdict == "KILLED" else 1


if __name__ == "__main__":
    sys.exit(main())
