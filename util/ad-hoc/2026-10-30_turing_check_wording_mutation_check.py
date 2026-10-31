"""
Show that the G1 suites kill a mutant for each way the host check's wording fix (erratum E-H3) can regress.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-30
Status: ad-hoc — investigation (suite strength evidence for E-H3's wording follow-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (erratum E-H3 of §18.3; tasks
         D3 and D4 and decision D7; gates G-TOOLS and G-MEM of §9.3); util/host_state_check.py;
         tests/test_host_state_check.py; reports/2026-10-27_turing-bringup/2026-10-27T0135Z_macos-host-sme.md (its
         findings 3 and 4); util/ad-hoc/2026-10-20_turing_g1_mutation_check.py (the engine this runs; its 57 mutants
         still apply)

Task H3's macos-host-sme report found two wording defects in util/host_state_check.py, neither of which changed a
verdict. G-TOOLS kubectl's remediation named task D4 but not task D3, which decision D7 puts first because Docker
Desktop installs its own /usr/local/bin/kubectl. G-MEM's memory message called its figure "free + inactive", though
the figure adds vm_stat's speculative pages too, as util/macvm_ctl.bash does. Each mutant re-introduces one of them
into a COPY of the check: the pre-E-H3 kubectl fix, that fix on the missing-kubectl path alone, and the old memory
label on a failure or on a pass. The G1 engine's behavioural classes then run against that copy, in a scratch tree
that mirrors the repo layout; FailureTest is among them.

A mutant is KILLED when the suites fail; the report names the tests that failed. The unmutated control must pass,
or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once. Nothing in the
repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (a script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py [--jobs N] [--only ID[,ID...]]
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "util" / "ad-hoc" / "2026-10-20_turing_g1_mutation_check.py"

FIX_NEW = 'fix = f"task D3 (owner) first: upgrade Docker Desktop, which installs its own /usr/local/bin/kubectl (decision D7); then task D4: kubectl {cluster}.x, which needs re-planning under the D6 ruling (erratum E-D6)"'
FIX_OLD = 'fix = f"task D4: kubectl {cluster}.x; it needs re-planning under the D6 ruling (erratum E-D6)"'
MISSING = 'return Condition("kubectl", "fail", "kubectl not found", fix)'
MEM_FAIL = 'f"free + speculative + inactive {avail} MiB < {need} MiB required {detail}"'
MEM_PASS = 'f"free + speculative + inactive {avail} MiB >= {need} MiB required {detail}"'

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once in the check.
MUTANTS = [
    ("W1", "the kubectl fix names task D4 only (the text before E-H3)", [(FIX_NEW, FIX_OLD)]),
    ("W2", "a missing kubectl gets the pre-E-H3 fix", [(MISSING, 'return Condition("kubectl", "fail", "kubectl not found", "task D4: kubectl 1.36.x")')]),
    ("W3", "a failing memory figure reads free + inactive", [(MEM_FAIL, MEM_FAIL.replace("free + speculative + inactive", "free + inactive"))]),
    ("W4", "a passing memory figure reads free + inactive", [(MEM_PASS, MEM_PASS.replace("free + speculative + inactive", "free + inactive"))]),
]


def load_engine():
    spec = importlib.util.spec_from_file_location("turing_g1_mutation_check", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="mutants to run at once (default: up to 4)")
    parser.add_argument("--only", help="run only these mutant ids, comma-separated")
    args = parser.parse_args()

    engine = load_engine()
    chosen = MUTANTS
    if args.only:
        wanted = set(args.only.split(","))
        chosen = [m for m in MUTANTS if m[0] in wanted]
    original = (REPO / engine.CHECK).read_text(encoding="utf-8")
    mutated: dict[str, str] = {}
    for mid, _, edits in chosen:
        text = engine.mutate(original, edits)
        if text is None or text == original:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {engine.CHECK}; update the mutant")
            return 2
        mutated[mid] = text

    passed, failures, output = engine.run_suite(None, None)
    if not passed:
        print(f"VOID   control: the suites fail on the unmutated scripts: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {len(engine.CLASSES)} classes pass on the unmutated {engine.PROBE} and {engine.CHECK}")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, engine.run_suite(engine.CHECK, mutated[mutant[0]])), chosen))

    killed = 0
    for (mid, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {defect}")
            continue
        killed += 1
        shown = ", ".join(failures[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {defect} -- {len(failures)} failing test(s): {shown}")

    print(f"\n{killed} of {len(chosen)} mutants killed")
    return 0 if killed == len(chosen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
