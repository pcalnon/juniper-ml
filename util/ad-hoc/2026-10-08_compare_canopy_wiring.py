#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — provenance check; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Compare a canopy tree's callback wiring with a ``_dash-dependencies`` capture from a live leg.

Builds ``DashboardManager`` from ``<canopy src>`` and normalises every callback to its outputs (the
``allow_duplicate`` hash dropped), Inputs, States and whether it carries a ``running=`` guard, then compares that
multiset with the capture. Used to show that a commit made after a live run changed no wiring: canopy#731's
commit 5 (``65ead946``) against the leg that served ``2689a207``.

Run in JuniperCanopy1 with ``LD_LIBRARY_PATH`` / ``LIBTORCH`` / ``LIBTORCH_LIB`` unset:
    python util/ad-hoc/2026-10-08_compare_canopy_wiring.py <canopy src> <capture.json>
Exit 0 if identical, 1 if not.
"""

import json
import sys


def _norm(entries):
    out = []
    for e in entries:
        out.append(
            json.dumps(
                {
                    "o": str(e["output"]).split("@")[0],
                    "i": [(d["id"], d["property"]) for d in e["inputs"]],
                    "s": [(d["id"], d["property"]) for d in e.get("state", [])],
                    "r": bool(e.get("running")),
                },
                sort_keys=True,
            )
        )
    return sorted(out)


def main(argv):
    src, capture = argv[0], argv[1]
    sys.path.insert(0, src)
    from frontend.dashboard_manager import DashboardManager  # noqa: E402

    dm = DashboardManager({"title": "t", "update_interval": 1000, "server": {"host": "localhost", "port": 8050}})
    with open(capture, encoding="utf-8") as fh:
        leg = _norm(json.load(fh))
    head = _norm(dm.app._callback_list)
    diff = sorted(set(leg) ^ set(head))
    print(f"capture={len(leg)} tree={len(head)} {'IDENTICAL' if leg == head else 'DIFFER'} symmetric_difference={len(diff)}")
    for d in diff[:10]:
        print("  ", d)
    return 0 if leg == head else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
