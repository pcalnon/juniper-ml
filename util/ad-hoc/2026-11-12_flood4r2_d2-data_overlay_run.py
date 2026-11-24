#!/usr/bin/env python3
"""
Run named juniper-data tests with ONE file of the tree replaced, for the run only, by another tree's copy of it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (do the newly selected rate-limiter tests pass against the pending Retry-After security.py?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --tree <juniper-data tree to run in> --from-tree <tree whose copy is borrowed, read only>
                   --path <repo-relative file> --nodes <file with one node id or path per line> --out <dir> --tag <name>
                   --python <name>=<venv interpreter> [--python ...]

The other tree is only read. The borrowed bytes are written over --path in --tree, the tests run once per interpreter
(one after another: they share the file), and the original bytes go back in a ``finally:`` block; the file's sha256
after the restore must equal its sha256 before, or the script stops. Compiled caches of the module are deleted first
and no run writes bytecode. A control run with the tree's own copy precedes the borrowed one, so the two are
comparable. The six Sentry DSN variables are set to "", three token variables are removed, TMPDIR is left alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this script's own pytest runs just wrote
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_TOKEN_NAMES = ("HF_TOKEN", "JUNIPER_ML_PYPI", "JUNIPER_ML_TEST_PYPI")
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|errors?|skipped|deselected)\b.*? in [0-9.]+s.*?)\s*=*$")


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in DROPPED_TOKEN_NAMES}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")})
    return env


def _read(path: Path) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _run(python: str, wt: Path, nodes: list[str], out: Path, stem: str) -> dict:
    junit = out / f"{stem}.xml"
    argv = [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-rA", f"--junitxml={junit}", *nodes]
    proc = subprocess.run(argv, cwd=wt, env=_env(), capture_output=True, text=True, check=False, timeout=1800)  # nosec B603
    with open(out / f"{stem}.log", "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={wt}) {' '.join(argv)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    hits = [m.group(1) for ln in proc.stdout.splitlines() if (m := SUMMARY_RE.match(ln.strip()))]
    bad = []
    if junit.is_file():
        for case in ET.parse(junit).getroot().iter("testcase"):  # nosec B314
            if {child.tag for child in case} & {"failure", "error"}:
                bad.append(f"{case.get('classname')}::{case.get('name')}")
    return {"argv": argv, "exit": proc.returncode, "summary": hits[-1] if hits else "<no summary line>", "failed_tests": bad, "log": str(out / f"{stem}.log")}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--from-tree", type=Path, required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--nodes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--python", action="append", required=True, help="<name>=<venv interpreter>")
    args = ap.parse_args()
    wt = args.tree.resolve()
    target = wt / args.path
    out = args.out.resolve() / f"overlay_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    with open(args.nodes, encoding="utf-8") as fh:
        nodes = [ln.strip() for ln in fh if ln.strip()]
    original = _read(target)
    borrowed = _read(args.from_tree.resolve() / args.path)
    before = hashlib.sha256(original).hexdigest()
    pythons = [item.split("=", 1) for item in args.python]
    record: dict = {"tree": str(wt), "from_tree": str(args.from_tree.resolve()), "path": args.path, "nodes": nodes, "sha256_own": before, "sha256_borrowed": hashlib.sha256(borrowed).hexdigest(), "runs": []}
    for name, python in pythons:
        record["runs"].append({"python": name, "copy": "own", **_run(python, wt, nodes, out, f"own_{name}")})
    for pyc in sorted(target.parent.glob(f"__pycache__/{target.stem}.*.pyc")):
        pyc.unlink()
    try:
        with open(target, "wb") as fh:
            fh.write(borrowed)
        record["sha256_during"] = hashlib.sha256(_read(target)).hexdigest()
        for name, python in pythons:
            record["runs"].append({"python": name, "copy": "borrowed", **_run(python, wt, nodes, out, f"borrowed_{name}")})
    finally:
        with open(target, "wb") as fh:
            fh.write(original)
    after = hashlib.sha256(_read(target)).hexdigest()
    record.update({"sha256_after": after, "restored_byte_for_byte": after == before, "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES), "token_names_removed": list(DROPPED_TOKEN_NAMES)})
    with open(out / "result.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")
    for run in record["runs"]:
        print(json.dumps({k: run[k] for k in ("python", "copy", "exit", "summary", "failed_tests")}))
    print(json.dumps({k: record[k] for k in ("sha256_own", "sha256_borrowed", "sha256_during", "sha256_after", "restored_byte_for_byte") if k in record}))
    print(f"wrote {out / 'result.json'}")
    if after != before:
        raise SystemExit(f"{target} was not restored: {after} != {before}")
    return 0 if all(run["exit"] == 0 for run in record["runs"]) else 1


if __name__ == "__main__":
    sys.exit(main())
