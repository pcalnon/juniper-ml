#!/usr/bin/env python3
"""
Re-run chosen rows of the "ml-tests" carrier's mutation spec in a COPY of the carrier, with its hashes logged first.

The rebuilt carrier keeps the predecessor's result for a mutant whose test file and target have the bytes the
predecessor mutated, and runs again every mutant whose target was rebuilt. A killed mutation helper once left a
mutant in a carrier's source file, so this run never touches the carrier:

  1. --root must be a scratch worktree that is NOT this one; every target the chosen rows name is hashed there
     (sha256) and must equal this carrier's copy of the same file;
  2. those hashes are appended to PROGRESS.txt, stamped from the clock, BEFORE anything is mutated;
  3. round 1's mutation helper runs in --root on the chosen rows (it passes the selection on the real code,
     applies the one-line mutant, re-runs, restores in a `finally:` block and compares the sha256 after every
     mutant), with the six Sentry DSN variables set to the empty string;
  4. every target is hashed again in --root AND in this carrier; both must equal the hashes of step 2. The result
     is appended to PROGRESS.txt.

Writes <scratch>/mutation_rerun/{spec.json, rerun_rows.json, mutation_results.json, mut*.log, hashes.json}.

Usage (from the carrier worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_mutants_rerun.py --root <scratch worktree>
        --scratch tmp/flood4r2/ml-tests/r2 --spec <mutants.json> --rows N [N ...]

Exit 0 when every chosen mutant is killed and every hash is unchanged.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, the finish of round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_mutation_check.py (the runner); tmp/flood4/session7/BRIEF_S7_ADDENDUM.txt section 1
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUNNER = "util/ad-hoc/2026-11-09_flood4r2_ml-tests_mutation_check.py"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _progress(scratch: Path, message: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(scratch / "PROGRESS.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {message}\n")
    print(f"{stamp} {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--rows", required=True, nargs="+", type=int)
    args = ap.parse_args()
    carrier, root, scratch = Path.cwd().resolve(), args.root.resolve(), args.scratch.resolve()
    if root == carrier or carrier in root.parents:
        raise SystemExit("refusing: --root is this carrier (or inside it); mutants run in a copy")
    out = scratch / "mutation_rerun"
    out.mkdir(parents=True, exist_ok=True)
    with open(args.spec, encoding="utf-8") as fh:
        everything = json.load(fh)
    chosen = [everything[index] for index in args.rows]
    for row in chosen:
        row.pop("control_root", None)
    (out / "spec.json").write_text(json.dumps(chosen, indent=2) + "\n", encoding="utf-8")
    (out / "rerun_rows.json").write_text(json.dumps(args.rows) + "\n", encoding="utf-8")
    touched = sorted({row["target"] for row in chosen} | {row["test_file"] for row in chosen})
    before = {path: {"copy": _sha(root / path), "carrier": _sha(carrier / path)} for path in touched}
    unequal = [path for path, pair in before.items() if pair["copy"] != pair["carrier"]]
    if unequal:
        raise SystemExit(f"refusing: the copy differs from the carrier on {unequal}")
    _progress(scratch, f"MUTATION RE-RUN about to start in the COPY {root} (never in the carrier), rows {args.rows}. sha256 of every file it may touch or read, copy == carrier: " + "; ".join(f"{path} {pair['copy']}" for path, pair in before.items()))
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1"}
    done = subprocess.run([sys.executable, "-B", str(carrier / RUNNER), str(out / "spec.json"), str(out)], cwd=str(root), capture_output=True, text=True, check=False, env=env, timeout=3600)
    (out / "mutation_run.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    after = {path: {"copy": _sha(root / path), "carrier": _sha(carrier / path)} for path in touched}
    moved = [path for path in touched if after[path] != before[path]]
    results = json.loads((out / "mutation_results.json").read_text(encoding="utf-8")) if (out / "mutation_results.json").is_file() else []
    killed = sum(1 for row in results if row.get("result") == "killed")
    restored = all(row.get("mutant_restored") for row in results)
    (out / "hashes.json").write_text(json.dumps({"root": str(root), "carrier": str(carrier), "rows": args.rows, "before": before, "after": after, "moved": moved}, indent=2) + "\n", encoding="utf-8")
    _progress(scratch, f"MUTATION RE-RUN done: runner rc {done.returncode}; {killed} of {len(results)} killed ({len(chosen)} chosen); every mutant restored: {restored}; files whose sha256 moved (copy or carrier): {moved or 'none'}. Evidence: {out.relative_to(carrier)}/mutation_run.log, mutation_results.json, hashes.json")
    print(done.stdout)
    return 0 if done.returncode == 0 and len(results) == len(chosen) and killed == len(chosen) and restored and not moved else 1


if __name__ == "__main__":
    sys.exit(main())
