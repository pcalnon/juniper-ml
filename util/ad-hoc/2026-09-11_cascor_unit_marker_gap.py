#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (juniper-cascor CI marker gap)
Application: ad-hoc analysis
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: identify exactly which tests juniper-cascor's CI unit lane never runs, and prove
the fix afterwards.

CI runs ``pytest -m "unit and not slow" src/tests/unit`` (ci.yml:312-317). A test in that
directory carrying no ``unit`` marker is collected and then silently DESELECTED -- it never
runs, and the job still reports success.

**Counting by grep gets this wrong twice**, as a first pass at it did:

* it counts FILES when the unit of the question is TESTS. A file whose first class carries
  ``@pytest.mark.unit`` satisfies the grep while its other 18 tests carry nothing
  (``api/test_phase1c_security.py``); and a ``src/tests/unit/test_*.py`` glob misses the
  ``api/`` subdirectory entirely.
* it cannot tell an accidental hole from a deliberate exclusion. A test marked ``unit`` AND
  ``slow`` is excluded by ``not slow`` on purpose.

Method: collect the directory three ways -- unfiltered, ``-m unit``, and under CI's own
expression -- and compare per-file counts. ``unfiltered - unit`` is the accidental hole;
``unit - CI`` is the deliberate ``slow`` exclusion.

Run before and after a marker change; ``--expect-empty`` makes it a gate.
Read-only.
"""
import argparse
import os
import subprocess
import sys
from collections import Counter

CASCOR = os.environ.get("CASCOR_ROOT", "/home/pcalnon/Development/python/Juniper/juniper-cascor")
TESTS = "src/tests/unit"
CI_MARKEXPR = "unit and not slow"


def collect(markexpr=None):
    """Per-file collected counts.

    ``pytest --collect-only -q`` prints a ``path: N`` summary line per file, NOT one node id
    per line -- an earlier version of this script assumed node ids, got an empty set, and its
    own guard stopped it from reporting a difference it had not measured.
    """
    cmd = [sys.executable, "-m", "pytest", TESTS, "--collect-only", "-q", "-p", "no:cacheprovider"]
    if markexpr:
        cmd += ["-m", markexpr]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=CASCOR, check=False)
    counts = {}
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line.startswith("src/tests/") or ": " not in line:
            continue
        path, _, tail = line.rpartition(": ")
        if tail.isdigit():
            counts[path] = int(tail)
    if not counts:
        print("collection produced no per-file counts -- refusing to report a difference it did not measure")
        print(out.stdout[-1200:])
        print(out.stderr[-1200:])
        sys.exit(2)
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-empty", action="store_true",
                    help="exit non-zero if any test is still invisible to CI (use as a gate)")
    args = ap.parse_args()

    everything = collect()
    has_unit = collect("unit")
    ci_sees = collect(CI_MARKEXPR)

    # TWO populations, and conflating them overstates the defect. A test marked
    # ``unit`` AND ``slow`` is excluded by CI's ``not slow`` DELIBERATELY -- that is the
    # lane working as designed. Only a test carrying no ``unit`` marker at all is an
    # accidental hole. An earlier version of this script reported their sum.
    gap = Counter()
    for path, n in everything.items():
        missing = n - has_unit.get(path, 0)
        if missing > 0:
            gap[path] = missing

    total_all = sum(everything.values())
    total_unit = sum(has_unit.values())
    total_ci = sum(ci_sees.values())
    invisible = sum(gap.values())
    deliberate = total_unit - total_ci

    print(f"collected in {TESTS}                    : {total_all}")
    print(f"carrying the `unit` marker                        : {total_unit}")
    print(f"visible to CI ('{CI_MARKEXPR}')            : {total_ci}")
    print(f"  of which excluded DELIBERATELY as `slow`        : {deliberate}")
    print(f"MISSING the `unit` marker (the accidental hole)   : {invisible}\n")

    if gap:
        print(f"{'tests':>6}  file")
        print("-" * 74)
        for path, n in sorted(gap.items(), key=lambda kv: (-kv[1], kv[0])):
            seen = has_unit.get(path, 0)
            note = "" if seen == 0 else f"   ({seen} of {everything[path]} ARE visible)"
            print(f"{n:>6}  {path}{note}")
        print("-" * 74)
        print(f"{invisible:>6}  across {len(gap)} files")
        print("\nNote: a file can be PARTLY marked -- some tests carrying `unit`, others none.")
        print("That is why this counts by collection rather than by grepping for a marker, and why\nit separates the accidental hole from the deliberate `slow` exclusion.")
    else:
        print("Every test in the directory is visible to CI's unit lane.")

    if args.expect_empty and gap:
        print("\nFAIL: tests remain invisible to CI.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
