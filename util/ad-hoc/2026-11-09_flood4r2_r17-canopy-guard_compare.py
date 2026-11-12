"""
Compare a guarded ruling-17 census run against the base run: outcomes, arming, and connects past the guard.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). Reads two merged census JSONs (the base
tree's and the guarded tree's, from util/ad-hoc/2026-11-09_flood4r2_r17-canopy-guard_run_groups.py) and prints:
the failures of each and the difference; the tests the guard was NOT armed for (``--probe-guard`` runs); every
connect to a guarded service port that reached the census fence, i.e. got PAST the guard (must be none); the
:8100 connects (deferred, so expected); and the node ids present in one run and not the other (none may be lost).
Exits 1 when a guarded port leaked, a test was lost, or the guarded run failed a test the base run passed.

Usage:
  python3 <this file> <base census json> <guarded census json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GUARDED = set(range(8050, 8060)) | {8200, 8201, 8202, 8210, 8211}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("base", type=Path)
    parser.add_argument("guarded", type=Path)
    args = parser.parse_args()
    with open(args.base, encoding="utf-8") as fh:
        base = json.load(fh)
    with open(args.guarded, encoding="utf-8") as fh:
        guarded = json.load(fh)

    base_ids, guarded_ids = set(base["outcome_by_test"]), set(guarded["outcome_by_test"])
    lost = sorted(base_ids - guarded_ids)
    added = sorted(guarded_ids - base_ids)
    new_failures = sorted(set(guarded["failed"]) - set(base["failed"]))
    leaked = {port: (entry["connects"], entry["tests"]) for port, entry in guarded["by_port"].items() if int(port) in GUARDED}
    data = guarded["by_port"].get("8100", {})
    print(f"base:    collected={base['collected']} outcomes={base['outcomes']} failed={base['failed']}")
    print(f"guarded: collected={guarded['collected']} outcomes={guarded['outcomes']} failed={guarded['failed']}")
    print(f"armed={len(guarded.get('armed', []))} not_armed={guarded.get('not_armed', [])}")
    print(f"failures new under the guard: {new_failures}")
    print(f"guarded-port connects that got past the guard: {leaked or 'none'}")
    print(f":8100 (deferred): base {base['by_port'].get('8100', {}).get('connects')} connects / {base['by_port'].get('8100', {}).get('n_tests')} tests; guarded {data.get('connects')} / {data.get('n_tests')}")
    print(f"test ids lost: {lost or 'none'}")
    print(f"test ids added: {len(added)} ({', '.join(sorted({nodeid.split('::', 1)[0] for nodeid in added})) or 'none'})")
    return 1 if (leaked or lost or new_failures) else 0


if __name__ == "__main__":
    sys.exit(main())
