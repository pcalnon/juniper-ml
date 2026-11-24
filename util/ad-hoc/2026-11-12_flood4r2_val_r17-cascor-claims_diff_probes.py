#!/usr/bin/env python3
"""
Compare two JSON probe reports (a list of objects) key by key and print where they differ.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_r17-cascor_adjacent_probes.py (the builder's probes, re-run on the
         validator's own copies); util/ad-hoc/2026-11-12_flood4r2_val_r17-cascor-claims_http_probe.py

Reports are matched by position. Keys named in ``--ignore`` are skipped (default: the path of the module
under test). With ``--show`` the second report's full objects are printed too.

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_diff_probes.py <main.json> <carrier.json> [--ignore key ...] [--show]
Exit: 0 (it reports; it does not judge).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("main", type=Path)
    parser.add_argument("carrier", type=Path)
    parser.add_argument("--ignore", nargs="*", default=["manager_under_test"])
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    left = json.loads(args.main.read_text(encoding="utf-8"))
    right = json.loads(args.carrier.read_text(encoding="utf-8"))
    print(f"{len(left)} objects in {args.main.name}, {len(right)} in {args.carrier.name}")
    differing = 0
    for index, (a, b) in enumerate(zip(left, right)):
        label = "/".join(str(b.get(key)) for key in ("probe", "verb", "stopped_fit_has_a_checkpoint_left", "name") if key in b) or f"#{index}"
        keys = [key for key in sorted(set(a) | set(b)) if key not in args.ignore and a.get(key) != b.get(key)]
        if keys:
            differing += 1
            print(f"\nDIFF {label}")
            for key in keys:
                va, vb = a.get(key), b.get(key)
                if isinstance(va, list) and isinstance(vb, list) and len(va) == len(vb) and all(isinstance(item, dict) for item in va + vb):
                    # A list of step objects: print only the steps that differ.
                    for position, (sa, sb) in enumerate(zip(va, vb)):
                        if sa != sb:
                            print(f"  {key}[{position}] {sb.get('step')}\n    main   : {json.dumps(sa)}\n    carrier: {json.dumps(sb)}")
                    continue
                print(f"  {key}\n    main   : {json.dumps(va)}\n    carrier: {json.dumps(vb)}")
        else:
            print(f"same {label}")
        if args.show:
            print("  carrier object: " + json.dumps(b))
    print(f"\n{differing} object(s) differ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
