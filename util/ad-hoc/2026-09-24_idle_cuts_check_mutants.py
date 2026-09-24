#!/usr/bin/env python
"""Mutation-check canopy's test_idle_dispatch_cuts.py CHECK tests: each guard's mutant must fail exactly one test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation (canopy E2E arc, Phase 9: the round-3 follow-up to canopy#676)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy branch fix/idle-cuts-round3-wording; reports/e2e-canopy-2026-09-02/consensus/
         2026-09-24_validator_reports_phase9_canopy_followup.md (Lanes C and C2)

WHAT. canopy's ``src/tests/unit/frontend/test_idle_dispatch_cuts.py`` pins its own CLASS check
(``_dead_intervals``, ``_consumers``) and the id lookups (``_interval_ids``, ``_with_id``) with four CHECK
tests. Each MUTANT below reverts or loosens one guard with an exact, asserted substitution. The mutant file is
written beside the real one (the test computes its import root from its own path), run with pytest, and
deleted. The claim under test: every mutant fails EXACTLY one test, and it is the named one.

Usage (from anywhere; needs the JuniperCanopy1 conda env):
    python3 util/ad-hoc/2026-09-24_idle_cuts_check_mutants.py --canopy <canopy worktree root>
"""

import argparse
import subprocess  # nosec B404 - runs pytest on test-authored mutants
import sys
from pathlib import Path

MUTANTS = {
    "no-id refusal dropped": (
        [('    anonymous = [p for p in intervals if "id" not in p]\n', ""), ('    assert not anonymous, f"an Interval with no id can have no consumer: {anonymous}"\n', "")],
        "test_an_interval_with_no_id_is_refused",
    ),
    "pattern refusal dropped": (
        [
            ('    pattern = [p["id"] for p in intervals if not isinstance(p["id"], str)]\n', ""),
            ('    assert not pattern, f"pattern-matching Interval ids are not supported by this check; extend _consumers before adding one: {pattern}"\n', ""),
        ],
        "test_a_pattern_matching_id_is_refused",
    ),
    "_interval_ids bare lookup": ([('    return [p.get("id") for p in intervals]\n', '    return [p["id"] for p in intervals]\n')], "test_the_sibling_lookups_accept_both_shapes"),
    "_with_id bare lookup": ([('    return [p for p in intervals if p.get("id") == component_id]\n', '    return [p for p in intervals if p["id"] == component_id]\n')], "test_the_sibling_lookups_accept_both_shapes"),
    "check reports nothing": (
        [('    return sorted(p["id"] for p in intervals if not _consumers(deps, p["id"]))\n', "    return []\n")],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
    "consumer ignores property": (
        [('i["id"] == component_id and i["property"] == "n_intervals" for i in e.get("inputs", [])', 'i["id"] == component_id for i in e.get("inputs", [])')],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
    "consumer counts State": (
        [('for i in e.get("inputs", []))]', 'for i in e.get("inputs", []) + e.get("state", []))]')],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
    "check reports only the first": (
        [('    return sorted(p["id"] for p in intervals if not _consumers(deps, p["id"]))\n', '    return sorted(p["id"] for p in intervals if not _consumers(deps, p["id"]))[:1]\n')],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
    "consumer counts an Output writer": (
        [('for i in e.get("inputs", []))]', 'for i in e.get("inputs", [])) or str(e.get("output", "")).startswith(component_id + ".")]')],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
    "consumer matches by substring": (
        [('i["id"] == component_id and i["property"] == "n_intervals"', 'component_id in str(i["id"]) and i["property"] == "n_intervals"')],
        "test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not",
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy", required=True, help="canopy worktree root")
    args = ap.parse_args()
    src = Path(args.canopy).resolve() / "src"
    real = src / "tests/unit/frontend/test_idle_dispatch_cuts.py"
    base = real.read_text(encoding="utf-8")
    failures = 0
    for i, (name, (subs, expected)) in enumerate(MUTANTS.items(), 1):
        text = base
        for old, new in subs:
            if text.count(old) != 1:
                print(f"REFUSED: mutant '{name}' substitution matches {text.count(old)} times: {old[:70]!r}", file=sys.stderr)
                return 2
            text = text.replace(old, new)
        mut = real.with_name(f"test_zz_mutant_{i}.py")
        mut.write_text(text, encoding="utf-8")
        try:
            proc = subprocess.run(  # nosec B603 B607 - fixed argv, test-authored mutant
                ["conda", "run", "--no-capture-output", "-n", "JuniperCanopy1", "python", "-m", "pytest", str(mut.relative_to(src)), "-p", "no:cacheprovider", "-rf"],
                cwd=src,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        finally:
            mut.unlink()
        failed = [ln.split("::")[-1].split(" ")[0] for ln in proc.stdout.splitlines() if ln.startswith("FAILED ")]
        ok = failed == [expected]  # exactly one test fails, and it is the named one
        failures += not ok
        print(f"{'CAUGHT' if ok else 'SURVIVED'}  {name:30s} failed={failed}")
    left = sorted(p.name for p in real.parent.glob("test_zz_mutant_*.py"))
    print(f"leftover mutant files: {left or 'none'}")
    print(f"{len(MUTANTS) - failures} of {len(MUTANTS)} mutants caught by their named test")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
