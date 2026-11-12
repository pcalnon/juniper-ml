#!/usr/bin/env python3
"""
Scan a frozen landing snapshot with gitleaks ``dir``, then prove the scan reads files: rescan a copy with one planted
fake token and require exactly one NEW finding.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: landing the fix carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (freezes what this scans, and writes main's copies of the same
         paths to <freeze>/main/ for --baseline)

Usage:
  2026-11-09_flood4r2_land_gitleaks.py <snapshot dir> <log dir> [--baseline <dir>] [--config <.gitleaks.toml>]
      [--gitleaks <binary>]

The binary defaults to pre-commit's cached gitleaks (v8.24.3; its ``version`` prints "version is set by build
process", the tag is in pre-commit's db.db). ``--config`` defaults to this checkout's ``.gitleaks.toml``; pass the
carrier repository's own config for a sibling repo.

A finding is keyed by (relative path, rule id, the text of the line it is on), so a line that only MOVED is the same
finding. With ``--baseline`` (main's copies of the same paths), a snapshot finding that the baseline also has is
pre-existing content of main, reported but not counted; without it, every finding counts. Clean = no counted finding.
The control copy (snapshot + one planted random github-pat-shaped token, never a real credential) must add exactly one
finding, in the planted file; the copy is deleted after its scan. Exit 0 = clean AND control caught; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path

DEFAULT_BINARY = Path.home() / ".cache/pre-commit/repotw5tescj/golangenv-system/bin/gitleaks"
PLANTED = "planted_control_token.txt"


def scan(binary: Path, target: Path, config: Path, logdir: Path, name: str) -> set[tuple[str, str, str]]:
    report = logdir / f"gitleaks_{name}.json"
    proc = subprocess.run([str(binary), "dir", str(target), "--config", str(config), "--redact", "--no-banner", "--report-format", "json", "--report-path", str(report)], capture_output=True, text=True)
    (logdir / f"gitleaks_{name}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode not in (0, 1) or not report.exists():
        raise SystemExit(f"gitleaks failed on {target} (rc={proc.returncode}); read {logdir / f'gitleaks_{name}.log'}")
    keys = set()
    for finding in json.loads(report.read_text(encoding="utf-8") or "[]"):
        # gitleaks reports File as the path it walked (relative to this process's cwd unless the target was absolute)
        rel = os.path.relpath(Path(finding["File"]).resolve(), target.resolve())
        lines = (target / rel).read_text(encoding="utf-8", errors="replace").split("\n")
        text = lines[finding["StartLine"] - 1].strip() if 0 < finding["StartLine"] <= len(lines) else ""
        keys.add((rel, finding["RuleID"], text))
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot")
    parser.add_argument("logdir")
    parser.add_argument("--baseline")
    parser.add_argument("--config", default=".gitleaks.toml")
    parser.add_argument("--gitleaks", default=str(DEFAULT_BINARY))
    args = parser.parse_args()
    snapshot = Path(args.snapshot)
    logdir = Path(args.logdir)
    logdir.mkdir(parents=True, exist_ok=True)
    binary = Path(args.gitleaks)
    config = Path(args.config).resolve()
    found = scan(binary, snapshot, config, logdir, "snapshot")
    baseline = scan(binary, Path(args.baseline), config, logdir, "baseline") if args.baseline else set()
    counted = sorted(found - baseline)
    pre_existing = sorted(found & baseline)
    control = logdir / "gitleaks_control_copy"
    if control.exists():
        shutil.rmtree(control)
    shutil.copytree(snapshot, control)
    token = "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
    (control / PLANTED).write_text(f"github_token = {token}\n", encoding="utf-8")
    try:
        control_found = scan(binary, control, config, logdir, "control")
    finally:
        shutil.rmtree(control)
    added = sorted(control_found - found)
    caught = len(added) == 1 and added[0][0] == PLANTED
    report = {"snapshot_findings": len(found), "pre_existing_on_main": [list(k) for k in pre_existing], "counted": [list(k) for k in counted], "control_added": [list(k)[:2] for k in added]}
    (logdir / "verdict.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for rel, rule, _text in pre_existing:
        print(f"pre-existing on main (not counted): {rel} {rule}")
    print(f"snapshot: {len(found)} finding(s), {len(counted)} counted -> {'CLEAN' if not counted else 'NOT CLEAN: ' + '; '.join(f'{r} {u}' for r, u, _ in counted)}")
    print(f"control:  {len(added)} added -> {'caught exactly 1 (the planted file)' if caught else 'CONTROL FAILED'} (copy deleted)")
    return 0 if not counted and caught else 1


if __name__ == "__main__":
    sys.exit(main())
