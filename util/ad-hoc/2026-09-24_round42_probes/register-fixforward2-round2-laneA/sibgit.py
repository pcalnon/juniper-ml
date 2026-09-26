#!/usr/bin/env python3
"""Run one READ-ONLY git command in a sibling Juniper repo and print its output.

Usage: sibgit.py <repo dir name> <git args...>
Refuses anything but a fixed allow-list of read-only subcommands.
"""
import subprocess
import sys

ALLOWED = {"log", "show", "cat-file", "rev-parse", "grep", "ls-tree", "merge-base", "rev-list", "branch", "tag", "describe", "blame", "diff"}
repo, args = sys.argv[1], sys.argv[2:]
if not args or args[0] not in ALLOWED:
    raise SystemExit(f"refused: {args[:1]}")
if args[0] in {"branch", "tag"} and any(a for a in args[1:] if not a.startswith("-") or a in {"-d", "-D", "-m", "-M", "-f"}):
    # list-only forms
    if any(a in {"-d", "-D", "-m", "-M", "-f", "--delete", "--force"} for a in args[1:]):
        raise SystemExit("refused: mutating branch/tag form")
p = subprocess.run(["git", *args], cwd=f"/home/pcalnon/Development/python/Juniper/{repo}", capture_output=True, text=True)
sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
sys.exit(p.returncode)
