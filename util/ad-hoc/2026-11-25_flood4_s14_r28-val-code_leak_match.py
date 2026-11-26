"""
Match the DemoMode threads alive at the setup of juniper-canopy's X7 tests to the test that started each one, from an
r28-val-code lane record.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code; input written by util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_plugin.py

Usage:
    python <this file> <lane .r28v.jsonl>

Prints, for every thread name alive (target DemoMode.*) at the first and last X7 setup, the test whose run started it
(the "leak" record that first names it), and every test that leaked a DemoMode thread.
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    leaks = [r for r in rows if r["kind"] == "leak"]
    origin: OrderedDict = OrderedDict()
    for row in leaks:
        for thread in row["threads"]:
            if "DemoMode" in (thread.get("target") or ""):
                origin.setdefault(thread["name"], row["test"])
    setups = [r for r in rows if r["kind"] == "threads_at_setup"]
    out = {"demo_leak_tests": sorted(set(origin.values())), "demo_threads_started_by": dict(origin)}
    for tag, row in (("first_x7_setup", setups[0] if setups else None), ("last_x7_setup", setups[-1] if setups else None)):
        if row is None:
            continue
        alive = [t["name"] for t in row["threads"] if "DemoMode" in (t.get("target") or "")]
        out[tag] = {"test": row["test"], "demo_threads": [{"name": n, "started_by": origin.get(n)} for n in alive]}
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
