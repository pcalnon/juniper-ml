#!/usr/bin/env python3
"""Check the ceiling rule stated for APD-ML-001 against the pins actually in pyproject.toml.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-ML-001 (item M-A)

WHY THIS EXISTS. M-A's whole deliverable is a SENTENCE -- "state the capping rule" -- and a
sentence about a set of pins is a claim that can be wrong in a way no test would catch, because
the ruling forbids turning it into an assertion. So the claim is measured once, here, and the
measurement is kept.

WHY IT IS NOT A TEST. Encoding the rule as a regression test would fail on the two known
exceptions, forcing either a dependency change or a waiver -- and the ruling is explicit that the
pins stay. A gate that fails for a reason nobody intends to fix trains people to ignore it. This
script reports; it does not gate.

WHAT IT WOULD CATCH. If someone later adds a shared library with no ceiling, or caps an
application, the exception list printed here grows and the stated rule in pyproject.toml and in
tests/test_pyproject_extras.py's docstring is out of date. Re-run it when a pin moves.

Exit 0 = the pins match the stated rule plus EXACTLY the two documented exceptions.
Exit 1 = they do not, and the stated rule needs updating (or the pin does).
"""

from __future__ import annotations

import pathlib
import sys
import tomllib

# The rule as stated in pyproject.toml and tests/test_pyproject_extras.py.
SHOULD_BE_CAPPED = {
    "juniper-config-tools",
    "juniper-doc-tools",
    "juniper-model-core",
    "juniper-service-core",
    "juniper-recurrence-model",
    "juniper-recurrence",
    "juniper-recurrence-client",
}
SHOULD_BE_UNCAPPED = {
    "juniper-canopy",
    "juniper-cascor",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
}
# Shared libraries the rule says should be capped and which are not. Both are recorded in the
# stated rule; ci-tools lost its ceiling in #295, observability never had one.
DOCUMENTED_EXCEPTIONS = {"juniper-ci-tools", "juniper-observability"}


def self_test() -> int:
    """Negative control: prove this script can report FAILURE, not just success.

    A checker that has only ever printed "matches" is indistinguishable from one whose comparison
    is broken -- the vacuous-pass class. Each case below perturbs one input and must flip the
    result to 1. Run with ``--self-test``.
    """
    global SHOULD_BE_CAPPED, SHOULD_BE_UNCAPPED, DOCUMENTED_EXCEPTIONS
    saved = (set(SHOULD_BE_CAPPED), set(SHOULD_BE_UNCAPPED), set(DOCUMENTED_EXCEPTIONS))
    cases = (
        ("drop a documented exception", lambda: DOCUMENTED_EXCEPTIONS.discard("juniper-observability")),
        ("claim an application should be capped", lambda: SHOULD_BE_CAPPED.add("juniper-canopy")),
        ("claim a shared library should be uncapped", lambda: SHOULD_BE_UNCAPPED.add("juniper-service-core")),
    )

    failures = 0
    for label, perturb in cases:
        SHOULD_BE_CAPPED, SHOULD_BE_UNCAPPED, DOCUMENTED_EXCEPTIONS = (set(saved[0]), set(saved[1]), set(saved[2]))
        perturb()
        rc = main(quiet=True)
        verdict = "OK (flipped to 1)" if rc == 1 else "VACUOUS -- still returned 0"
        if rc != 1:
            failures += 1
        print(f"  {label}: {verdict}")

    SHOULD_BE_CAPPED, SHOULD_BE_UNCAPPED, DOCUMENTED_EXCEPTIONS = saved
    rc = main(quiet=True)
    print(f"  unperturbed baseline: {'OK (returned 0)' if rc == 0 else 'BROKEN -- baseline fails'}")
    if rc != 0:
        failures += 1

    print("\nself-test: PASS" if not failures else f"\nself-test: FAIL ({failures})")
    return 1 if failures else 0


def main(quiet: bool = False) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]

    capped: set[str] = set()
    uncapped: set[str] = set()
    for name, pins in extras.items():
        if name == "all":
            continue
        for pin in pins:
            pkg = pin.split(">=")[0].strip()
            if not pkg.startswith("juniper-"):
                continue
            (capped if "<" in pin else uncapped).add(pkg)

    if not quiet:
        print(f"capped   ({len(capped)}): {', '.join(sorted(capped))}")
        print(f"uncapped ({len(uncapped)}): {', '.join(sorted(uncapped))}")
        print()

    problems: list[str] = []

    missing_cap = SHOULD_BE_CAPPED - capped
    if missing_cap:
        problems.append(f"rule says CAPPED but pin has no ceiling: {sorted(missing_cap)}")

    unexpected_cap = SHOULD_BE_UNCAPPED & capped
    if unexpected_cap:
        problems.append(f"rule says NO ceiling but pin is capped: {sorted(unexpected_cap)}")

    actual_exceptions = uncapped - SHOULD_BE_UNCAPPED
    if actual_exceptions != DOCUMENTED_EXCEPTIONS:
        problems.append(f"exception set changed: documented {sorted(DOCUMENTED_EXCEPTIONS)}, found {sorted(actual_exceptions)}")

    unclassified = (capped | uncapped) - SHOULD_BE_CAPPED - SHOULD_BE_UNCAPPED - DOCUMENTED_EXCEPTIONS
    if unclassified:
        problems.append(f"pin not covered by the stated rule at all: {sorted(unclassified)}")

    if problems:
        if not quiet:
            print("STATED RULE DOES NOT MATCH THE PINS:")
            for problem in problems:
                print(f"  - {problem}")
        return 1

    if not quiet:
        print("The stated rule matches the pins, with exactly the two documented exceptions:")
        print(f"  {', '.join(sorted(DOCUMENTED_EXCEPTIONS))}")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
