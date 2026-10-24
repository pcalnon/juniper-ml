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
nobody could re-run. This is that harness, kept. A validation lane gives each surviving mutant it finds as an exact
replacement in a mutants file, and the reconciliation adds it to the set (round 13: R13A-12), as
util/ad-hoc/2026-10-10_build_round13_mutants.py does for round 13's.

A mutants file is JSON: a list of ``{"id": ..., "desc": ..., "reps": [[old, new], ...]}``, or an object mapping each
id to its ``reps``. Every entry of every file is counted, and each file's count is printed first (round 13: R13B1-12:
an entry with no replacement used to vanish, so a set could shrink with no BUILD-FAIL). A file whose JSON gives one
member name twice in any object is refused, since the parser would keep only the last (round 14: R14B-09). An entry
is reported BUILD-FAIL, and counts as not caught, when it has no replacement, when a replacement is not an
``[old, new]`` pair, when an ``old`` does not occur exactly once in the read, when its replacements leave the read
unchanged, or when its id is ``BASELINE`` or names no directory of its own under ``--out`` (empty, ``.`` or ``..``
once sanitized): such an entry used to take the baseline's branch, unbuilt and in no tally (round 14: R14B-08). An
entry that builds the same read as an earlier one is run anyway and says so. Each mutant is written to
``--out/<id>/read.py``; the regression is loaded as a module from its own path, with bytecode writing off, its
``SHAPE`` pointed at the mutant, and its ``contract_check`` and ``names_check`` run once each. A mutant is CAUGHT when
either check fails. The baseline (the read unchanged) must pass both, and the run fails unless CAUGHT, SURVIVED and
BUILD-FAIL add up to the entry count.

Only synthetic values reach the read: the checks generate their own inputs in a temporary directory.

Usage
-----
    python3 -B util/ad-hoc/2026-10-08_line_read_mutation_run.py --mutants <file.json> [<file.json> ...] \\
        --out <scratch dir> --workdir <gate workdir> [--read <read.py>] [--regression <regression.py>]
Exit 0 when the baseline passes and every entry builds and is caught; 1 on any BUILD-FAIL, survivor, failing
baseline, refused file or tally that does not account for every entry.
"""
import argparse
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
READ = HERE / "2026-10-05_masked_finding_shape.py"
REGRESSION = HERE / "2026-10-05_gate_regression.py"
BASELINE = "BASELINE"


def _members_once(pairs: list[tuple]) -> dict:
    """``json.loads``'s object hook: an object that gives one member name twice is refused, not collapsed to its last
    member, so an entry cannot vanish through the object form (round 14: R14B-09)."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"the member name {key!r} occurs twice in one object")
        obj[key] = value
    return obj


def load_mutants(paths: list[Path]) -> tuple[list[dict], list[str]]:
    """Every entry of every mutants file, none dropped, and one line per file giving its entry count (round 13:
    R13B1-12). An entry with no id is named by its file and position."""
    mutants, counts = [], []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_members_once)
        except ValueError as exc:
            raise SystemExit(f"REFUSED {path}: {exc}")
        if isinstance(data, dict):
            data = [{"id": k, "desc": k, "reps": reps} for k, reps in data.items()]
        counts.append(f"{path}: {len(data)} entr{'y' if len(data) == 1 else 'ies'}")
        for i, m in enumerate(data, 1):
            m = m if isinstance(m, dict) else {}
            mutants.append({"id": str(m.get("id") or f"{path.name}#{i}"), "desc": str(m.get("desc", "")), "reps": m.get("reps")})
    seen = set()
    for m in mutants:
        if m["id"] in seen:
            raise SystemExit(f"duplicate mutant id {m['id']}")
        seen.add(m["id"])
    return mutants, counts


def build(source: str, reps) -> tuple[str, str]:
    """The mutated source, or an empty string and the reason it could not be built: no replacement, a replacement that
    is not an [old, new] pair of strings, an old text that does not occur exactly once, or a read left unchanged."""
    if not reps or not isinstance(reps, list):
        return "", "no replacement"
    text = source
    for rep in reps:
        if not (isinstance(rep, list) and len(rep) == 2 and all(isinstance(s, str) for s in rep)):
            return "", "a replacement that is not an [old, new] pair of strings"
        old, new = rep
        n = text.count(old)
        if n != 1:
            return "", f"replacement matched {n} times: {old[:60]!r}"
        text = text.replace(old, new)
    if text == source:
        return "", "its replacements leave the read unchanged"
    return text, ""


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
    mutants, counts = load_mutants(args.mutants)
    for line in counts:
        print(line, flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    rows, failed, tally, first_of = list(counts), [], {"CAUGHT": 0, "SURVIVED": 0, "BUILD-FAIL": 0}, {}
    # The baseline is marked by its place, first, never by its id, so no entry can take its branch (R14B-08).
    for is_baseline, m in [(True, {"id": BASELINE, "desc": "the read unchanged", "reps": None})] + [(False, m) for m in mutants]:
        dirname = re.sub(r"[^A-Za-z0-9._ -]", "_", m["id"])
        if is_baseline:
            text, why = source, ""
        elif m["id"] == BASELINE:
            text, why = "", "its id is the baseline's"
        elif dirname.strip() in ("", ".", ".."):
            text, why = "", "its id names no directory of its own under --out"
        else:
            text, why = build(source, m["reps"])
        if why:
            rows.append(f"BUILD-FAIL {m['id']}: {why}")
            print(rows[-1], flush=True)
            tally["BUILD-FAIL"] += 1
            failed.append(m["id"])
            continue
        same = first_of.setdefault(text, m["id"])
        d = args.out / dirname
        d.mkdir(parents=True, exist_ok=True)
        shape = d / "read.py"
        shape.write_text(text, encoding="utf-8")
        res = run_checks(args.regression, shape, args.workdir)
        caught = [k for k, (ok, _) in res.items() if not ok]
        detail = "; ".join(f"{k}: {why}" for k, (ok, why) in res.items() if not ok)
        if is_baseline:
            verdict = "PASS" if not caught else "BASELINE-FAILS"
            if caught:
                failed.append(m["id"])
        else:
            verdict = "CAUGHT" if caught else "SURVIVED"
            tally[verdict] += 1
            if not caught:
                failed.append(m["id"])
        dup = f" (builds the same read as {same})" if same != m["id"] else ""
        rows.append(f"{verdict:9} {m['id']}: {m.get('desc', '')}{dup}" + (f" [{detail}]" if detail else ""))
        print(rows[-1], flush=True)
    distinct = len(first_of) - 1  # the baseline's read is not a mutant
    summary = (f"{len(mutants)} entr{'y' if len(mutants) == 1 else 'ies'}: {len(mutants) - tally['BUILD-FAIL']} built "
               f"({distinct} distinct reads), {tally['CAUGHT']} CAUGHT, {tally['SURVIVED']} SURVIVED, {tally['BUILD-FAIL']} BUILD-FAIL; "
               f"not caught or not built: {failed if failed else 'none'}")
    print(summary)
    rows.append(summary)
    accounted = sum(tally.values())
    if accounted != len(mutants):  # every entry is CAUGHT, SURVIVED or BUILD-FAIL, or the run is not a count (R14B-08)
        rows.append(f"TALLY-FAIL: {accounted} of {len(mutants)} entries accounted for")
        print(rows[-1])
        failed.append("TALLY")
    (args.out / "result.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
