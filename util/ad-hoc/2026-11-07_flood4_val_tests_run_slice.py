"""
Run test files the way ci.yml's regression step does (one `<python> -m unittest -v tests/<file>.py` process each, from the repo root).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 tests carrier, slice B)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 carrier validation (BRIEF_VALIDATE.txt); juniper-ml tests carrier on origin/main 303ccc0b

Usage: python3 <this> --python <interpreter> --root <repo root> --out <log dir> --label <label> [--jobs N] FILE [FILE ...]

Clears every __pycache__ under tests/ and util/ first (a stale .pyc can mask a source change), then runs each
file in its own process, writes <out>/<label>__<file stem>.log, and prints and saves a JSON summary
(<out>/<label>__summary.json) with each file's exit status, "Ran N tests" count and final status line.
"""

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _clear_pycache(root: Path) -> int:
    removed = 0
    for top in (root / "tests", root / "util"):
        for cache in top.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)
            removed += 1
    return removed


def _run_one(python: str, root: Path, out: Path, label: str, rel: str) -> dict:
    started = time.monotonic()
    proc = subprocess.run(  # nosec B603 -- fixed argv, no shell
        [python, "-m", "unittest", "-v", rel],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = round(time.monotonic() - started, 1)
    text = proc.stdout + proc.stderr
    log = out / f"{label}__{Path(rel).stem}.log"
    log.write_text(f"$ {python} -m unittest -v {rel}\n(cwd {root})\nexit {proc.returncode}, {elapsed}s\n\n{text}", encoding="utf-8")
    ran = re.findall(r"^Ran (\d+) tests? in", text, re.MULTILINE)
    status = [line for line in text.splitlines() if line.startswith(("OK", "FAILED"))]
    failing = re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", text, re.MULTILINE)
    return {"file": rel, "rc": proc.returncode, "ran": int(ran[-1]) if ran else None, "status": status[-1] if status else None, "seconds": elapsed, "failing": [f"{cls}.{name}" for name, cls in failing], "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.python, "--version"], capture_output=True, text=True, check=False).stdout.strip()  # nosec B603
    removed = _clear_pycache(root)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda rel: _run_one(args.python, root, out, args.label, rel), args.files))
    summary = {
        "python": args.python,
        "version": version,
        "root": str(root),
        "env": {k: os.environ.get(k) for k in ("TMPDIR", "GIT_CEILING_DIRECTORIES")},
        "pycache_dirs_removed": removed,
        "results": rows,
        "all_ok": all(r["rc"] == 0 for r in rows),
    }
    summary_path = out / f"{args.label}__summary.json"
    summary_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for r in rows:
        print(f"{r['rc']:>3} ran={r['ran']} {r['seconds']:>6}s {r['status']} {r['file']} {' '.join(r['failing'][:4])}")
    print(f"{version}: all_ok={summary['all_ok']} -> {summary_path}")
    return 0 if summary["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
