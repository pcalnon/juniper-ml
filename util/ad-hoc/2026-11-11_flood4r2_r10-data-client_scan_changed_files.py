#!/usr/bin/env python3
"""
Scan a port's changed files with the pinned secret-scan engine, against main's copies, and prove the scan can find a token.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         util/ad-hoc/2026-11-09_flood4r2_land_gitleaks.py (the same idea for a repository that HAS a .gitleaks.toml)

WHY THIS EXISTS
The port adds files that build token-shaped values, and its own pull request is the first thing the new scan step
reads. This copies the named files of a working tree into a snapshot, and origin/main's copies of the same paths into
a baseline, then runs the engine's `dir` mode over each, WITHOUT --config: the engine auto-discovers
`<source>/.gitleaks.toml`, so the snapshot and the baseline each carry the repository root's own gitleaks files when
it has any, and the built-in ruleset applies when it has none (juniper-data-client's case). A finding is keyed by
(path, rule, the text of its line); a finding the baseline also has is main's own content and is not counted.
The control copies the snapshot, adds one file holding a GitHub-PAT-shaped value built at run time from random
letters (never a credential), and requires exactly one new finding, in that file: a scan that reads nothing would
otherwise pass. Extra files outside the tree (a pull-request body, for example) can be scanned too, with --also.

Usage:
    python3 <this> --tree <checkout> --gitleaks <binary> --out <new dir> --paths <repo-relative> [...] [--also <file> ...]
Exit 0 = no counted finding and the control caught; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import string
import subprocess  # nosec B404 - fixed argv: git show and the engine's dir mode
import sys
from pathlib import Path

GITLEAKS_FILES = (".gitleaks.toml", ".gitleaksignore")
PLANTED = "planted_control_token.txt"


def scan(binary: Path, target: Path, out: Path, name: str) -> set[tuple[str, str, str]]:
    report = out / f"scan_{name}.json"
    env = {k: v for k, v in os.environ.items() if k not in ("GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")}
    proc = subprocess.run([str(binary), "dir", str(target), "--redact", "--no-banner", "--log-level=debug", "--report-format", "json", "--report-path", str(report)], capture_output=True, text=True, env=env, check=False)  # nosec B603
    (out / f"scan_{name}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode not in (0, 1) or not report.exists():
        raise SystemExit(f"the engine failed on {target} (exit {proc.returncode}); read {out / f'scan_{name}.log'}")
    keys = set()
    for finding in json.loads(report.read_text(encoding="utf-8") or "[]"):
        rel = os.path.relpath(Path(finding["File"]).resolve(), target.resolve())
        lines = (target / rel).read_text(encoding="utf-8", errors="replace").split("\n")
        text = lines[finding["StartLine"] - 1].strip() if 0 < finding["StartLine"] <= len(lines) else ""
        keys.add((rel, finding["RuleID"], text))
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--gitleaks", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--paths", nargs="+", required=True)
    ap.add_argument("--also", nargs="*", default=[], type=Path)
    ap.add_argument("--base-ref", default="origin/main")
    args = ap.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit(f"{out} is not empty; give a new directory")
    snapshot, baseline, control = out / "snapshot", out / "baseline", out / "control"
    on_main = []
    for rel in args.paths:
        (snapshot / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tree / rel, snapshot / rel)
        shown = subprocess.run(["git", "-C", str(tree), "show", f"{args.base_ref}:{rel}"], capture_output=True, check=False)  # nosec B603 B607
        if shown.returncode == 0:
            (baseline / rel).parent.mkdir(parents=True, exist_ok=True)
            (baseline / rel).write_bytes(shown.stdout)
            on_main.append(rel)
    for extra in args.also:
        (snapshot / "_also").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(extra, snapshot / "_also" / extra.name)
    baseline.mkdir(parents=True, exist_ok=True)
    for name in GITLEAKS_FILES:
        if (tree / name).is_file():
            shutil.copyfile(tree / name, snapshot / name)
            shutil.copyfile(tree / name, baseline / name)
    found, known = scan(args.gitleaks, snapshot, out, "snapshot"), scan(args.gitleaks, baseline, out, "baseline")
    counted = sorted(found - known)
    shutil.copytree(snapshot, control)
    token = "gh" + "p_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
    (control / PLANTED).write_text("GITHUB_" + "TOKEN=" + token + "\n", encoding="utf-8")
    planted = sorted(scan(args.gitleaks, control, out, "control") - found)
    shutil.rmtree(control)
    caught = len(planted) == 1 and planted[0][0] == PLANTED
    result = {
        "engine": str(args.gitleaks),
        "repository_gitleaks_files": [name for name in GITLEAKS_FILES if (tree / name).is_file()],
        "files_scanned": sorted(args.paths) + sorted("_also/" + extra.name for extra in args.also),
        "of_which_on_main": sorted(on_main),
        "findings_also_on_main": sorted(f"{rel}: {rule}" for rel, rule, _ in found & known),
        "counted_findings": [f"{rel}: {rule}" for rel, rule, _ in counted],
        "control_new_findings": [f"{rel}: {rule}" for rel, rule, _ in planted],
        "control_caught": caught,
        "token_left_in_a_log_or_report": any(token in p.read_text(encoding="utf-8", errors="replace") for p in out.glob("scan_*")),
    }
    with open(out / "scan_changed_files.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(json.dumps(result, indent=1))
    return 0 if not counted and caught and not result["token_left_in_a_log_or_report"] else 1


if __name__ == "__main__":
    sys.exit(main())
