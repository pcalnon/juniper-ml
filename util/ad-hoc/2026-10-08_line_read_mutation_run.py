#!/usr/bin/env python3
"""
Mutation run for the line read: build each mutant of the read, and check that the regression's line-read checks catch it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-05_masked_finding_shape.py (the read it mutates);
         util/ad-hoc/2026-10-05_gate_regression.py (the checks it runs);
         reports/2026-10-04_consolidated-development-plan/round12-reconciliation.md (the run it was written for)

Rounds 11 and 12 rebuilt this run with inline Python each time, so each round's mutation claim rested on a harness
nobody could re-run. This is that harness, kept.

A mutants file is JSON: a list of ``{"id": ..., "desc": ..., "reps": [[old, new], ...]}``, or an object mapping each
id to its ``reps``. Each ``old`` must occur exactly once in the read, or the mutant is reported BUILD-FAIL and counts
as not caught. Each mutant is written to ``--out/<id>/read.py``; the regression is loaded as a module from its own
path, with bytecode writing off, its ``SHAPE`` pointed at the mutant, and its ``contract_check`` and ``names_check``
run once each. A mutant is CAUGHT when either check fails. The baseline (the read unchanged) must pass both.

Only synthetic values reach the read: the checks generate their own inputs in a temporary directory.

Usage
-----
    python3 -B util/ad-hoc/2026-10-08_line_read_mutation_run.py --mutants <file.json> [<file.json> ...] \\
        --out <scratch dir> --workdir <gate workdir> [--read <read.py>] [--regression <regression.py>]
Exit 0 when the baseline passes and every mutant is caught; 1 otherwise.
"""
import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
READ = HERE / "2026-10-05_masked_finding_shape.py"
REGRESSION = HERE / "2026-10-05_gate_regression.py"


def load_mutants(paths: list[Path]) -> list[dict]:
    mutants = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [{"id": k, "desc": k, "reps": reps} for k, reps in data.items()]
        mutants.extend(m for m in data if m.get("reps"))
    seen = set()
    for m in mutants:
        if m["id"] in seen:
            raise SystemExit(f"duplicate mutant id {m['id']}")
        seen.add(m["id"])
    return mutants


def build(source: str, reps: list) -> tuple[str, str]:
    """The mutated source, or an empty string and the reason it could not be built."""
    for old, new in reps:
        n = source.count(old)
        if n != 1:
            return "", f"replacement matched {n} times: {old[:60]!r}"
        source = source.replace(old, new)
    return source, ""


def run_checks(regression: Path, shape: Path, workdir: Path) -> dict:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("gate_regression_under_mutation", regression)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SHAPE = shape
    result = {}
    base = Path(tempfile.mkdtemp(prefix="line-read-mutation-"))
    try:
        for name, call in (("contract", lambda: mod.contract_check(base / "contract", workdir)), ("names", lambda: mod.names_check(base / "names"))):
            try:
                ok, why = call()
            except Exception as exc:  # a mutant that crashes a check is caught by it
                ok, why = False, f"raised {type(exc).__name__}"
            result[name] = (ok, why)
    finally:
        mod.restore(base)
        shutil.rmtree(base, ignore_errors=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--mutants", nargs="+", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="scratch directory for the mutant copies")
    ap.add_argument("--workdir", required=True, type=Path, help="the gate's workdir, holding its verified scanner")
    ap.add_argument("--read", type=Path, default=READ)
    ap.add_argument("--regression", type=Path, default=REGRESSION)
    args = ap.parse_args()
    source = args.read.read_text(encoding="utf-8")
    mutants = load_mutants(args.mutants)
    args.out.mkdir(parents=True, exist_ok=True)
    rows, failed = [], []
    for m in [{"id": "BASELINE", "desc": "the read unchanged", "reps": []}] + mutants:
        text, why = build(source, m["reps"])
        if why:
            rows.append(f"BUILD-FAIL {m['id']}: {why}")
            failed.append(m["id"])
            continue
        d = args.out / m["id"]
        d.mkdir(parents=True, exist_ok=True)
        shape = d / "read.py"
        shape.write_text(text, encoding="utf-8")
        res = run_checks(args.regression, shape, args.workdir)
        caught = [k for k, (ok, _) in res.items() if not ok]
        detail = "; ".join(f"{k}: {why}" for k, (ok, why) in res.items() if not ok)
        if m["id"] == "BASELINE":
            verdict = "PASS" if not caught else "BASELINE-FAILS"
            if caught:
                failed.append(m["id"])
        else:
            verdict = "CAUGHT" if caught else "SURVIVED"
            if not caught:
                failed.append(m["id"])
        rows.append(f"{verdict:9} {m['id']}: {m.get('desc', '')}" + (f" [{detail}]" if detail else ""))
        print(rows[-1], flush=True)
    summary = f"{len(mutants)} mutant(s); not caught or not built: {failed if failed else 'none'}"
    print(summary)
    (args.out / "result.txt").write_text("\n".join(rows + [summary]) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
