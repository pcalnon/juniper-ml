"""
Seam-mutant harness for the r27-val-code2 lens: apply each mutant of canopy's REAL juniper-data handling to a tree that
carries carrier r27, run a test set through the census runner, record which tests kill it, restore byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2; runner util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py,
    junit helper util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_junit.py

Usage:
    python <this file> --python <venv python> --tree <mutant tree> --out <dir> --spec <spec.json> --targets <file list>
        --runner <run_lane.py> --census <census.py> --junit-tool <junit.py> [--ids ID,ID ...]

Each spec entry: {"id", "file" (tree-relative), "old" (must occur exactly once), "new", "desc"}. The tree's file is
read as bytes, sha256-recorded, mutated, the tests run (CI's unit-lane marker selector, no coverage, no maxfail), and
the original bytes written back in a ``finally``; the sha256 after must equal the one before, or the harness stops.
Results go to <out>/results.json after every mutant (always valid JSON).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs this lens's own runner
import sys
import time
from pathlib import Path

CI_MARKERS = "not requires_cascor and not requires_server and not slow"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("--python", "--tree", "--out", "--spec", "--targets", "--runner", "--census", "--junit-tool"):
        parser.add_argument(name, required=True)
    parser.add_argument("--ids", default="")
    args = parser.parse_args()
    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    wanted = [i for i in args.ids.split(",") if i]
    if wanted:
        spec = [m for m in spec if m["id"] in wanted]
    targets = [line.strip() for line in Path(args.targets).read_text(encoding="utf-8").splitlines() if line.strip()]
    results_path = out / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
    for mutant in spec:
        path = tree / mutant["file"]
        original = path.read_bytes()
        before = sha(original)
        text = original.decode("utf-8")
        occurrences = text.count(mutant["old"])
        entry = {"desc": mutant["desc"], "file": mutant["file"], "sha256_before": before, "occurrences": occurrences}
        if occurrences != 1:
            entry["status"] = f"NOT APPLIED: old occurs {occurrences} times"
            results[mutant["id"]] = entry
            results_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
            continue
        start = time.time()
        try:
            path.write_bytes(text.replace(mutant["old"], mutant["new"], 1).encode("utf-8"))
            entry["sha256_mutated"] = sha(path.read_bytes())
            label = mutant["id"]
            command = [args.python, args.runner, "--python", args.python, "--tree", str(tree), "--out", str(out / label), "--label", label, "--census", args.census, "--no-cov", "--no-maxfail", "--", "-m", CI_MARKERS, "-p", "no:cacheprovider", *targets]
            proc = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603
            entry["runner_exit"] = proc.returncode
            entry["runner_stdout"] = proc.stdout[-600:]
        finally:
            path.write_bytes(original)
        after = sha(path.read_bytes())
        entry["sha256_after"] = after
        entry["restored"] = after == before
        entry["seconds"] = round(time.time() - start, 1)
        junit = out / label / f"{label}.junit.xml"
        if junit.exists():
            parsed = json.loads(subprocess.run([sys.executable, "-I", args.junit_tool, "failed", str(junit)], capture_output=True, text=True, check=True).stdout)  # nosec B603
            entry.update({"tests": parsed["tests"], "failed_count": parsed["failed_count"], "error_count": parsed["error_count"], "killers": parsed["failed"] + parsed["errors"]})
            run_json = out / label / f"{label}.run.json"
            bash_exit = json.loads(run_json.read_text(encoding="utf-8"))["bash_exit"] if run_json.exists() else None
            entry["pytest_bash_exit"] = bash_exit
            if parsed["tests"] == 0 or bash_exit not in (0, 1, 134):
                entry["status"] = f"INVALID (tests={parsed['tests']}, pytest exit {bash_exit}): not a survival"  # a usage error or an empty collection proves nothing
            else:
                entry["status"] = "KILLED" if entry["killers"] else "SURVIVED"
        else:
            entry["status"] = "NO JUNIT (run did not complete)"
        results[mutant["id"]] = entry
        results_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
        print(json.dumps({"id": mutant["id"], "status": entry["status"], "killers": len(entry.get("killers", [])), "restored": entry["restored"], "seconds": entry["seconds"]}), flush=True)
        if not entry["restored"]:
            print("RESTORE FAILED: stopping", flush=True)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
