#!/usr/bin/env python
"""Static dispatch census of a canopy build: every dcc.Interval, its period, and what it triggers.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 7 still-owed items 2-3
         ("take a dispatch-rate census by source"; "the dead 1 Hz metrics-panel-update-interval")

WHY. Phase 7 measured the page's main thread at ~0.1% idle and put 85% of self time in
dash-renderer. Every ``dcc.Interval`` tick is a ``setProps`` on the layout -- a Redux update that
re-runs every connected component's selectors -- whether or not any callback consumes it, and each
consumer adds a renderer pass (and a server round trip if it is not clientside). This lists, for the
BUILT app (``DashboardManager({}).app``, the served ``/_dash-dependencies`` and the layout):

  * every Interval: id, period, ``disabled`` default, ``max_intervals``;
  * the callbacks that take its ``n_intervals`` as an INPUT, server or clientside, and whether one is
    ``running=``-guarded (it disables its own interval while in flight);
  * the nominal ticks per second at the layout defaults, and an upper bound on server dispatches per
    second if every consumer ran on every tick.

It is an UPPER BOUND on schedule, not a measurement: tab gating, ``running=`` guards and
``no_update`` producers all reduce what the page actually dispatches. The live rate is a separate
measurement. Intervals whose ``disabled`` is written by a callback are marked; their default is only
where they start.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_canopy_interval_census.py --canopy-src <canopy checkout>/src [--json out.json]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def _walk(node, out):
    if isinstance(node, (list, tuple)):
        for c in node:
            _walk(c, out)
        return
    if node is None or not hasattr(node, "to_plotly_json"):
        return
    j = node.to_plotly_json()
    props = j.get("props", {})
    if j.get("type") == "Interval" and j.get("namespace") == "dash_core_components":
        out.append({"id": props.get("id"), "interval_ms": props.get("interval", 1000), "disabled": bool(props.get("disabled", False)), "max_intervals": props.get("max_intervals", -1)})
    _walk(props.get("children"), out)
    for v in props.values():
        if hasattr(v, "to_plotly_json") or isinstance(v, (list, tuple)):
            if v is not props.get("children"):
                _walk(v, out)


def _split_outputs(output):
    return output[2:-2].split("...") if output.startswith("..") else [output]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy-src", required=True)
    ap.add_argument("--json")
    args = ap.parse_args()

    sys.path.insert(0, args.canopy_src)
    from frontend.dashboard_manager import DashboardManager  # noqa: E402

    dm = DashboardManager({})
    app = dm.app
    deps = json.loads(app.server.test_client().get("/_dash-dependencies").data)
    layout = app.layout() if callable(app.layout) else app.layout
    intervals = []
    _walk(layout, intervals)

    consumers = defaultdict(list)
    disabled_writers = defaultdict(list)
    for e in deps:
        outs = [] if e.get("no_output") else _split_outputs(e["output"])
        kind = "clientside" if e.get("clientside_function") else "server"
        running = bool(e.get("running"))
        for i in e.get("inputs", []):
            if i.get("property") == "n_intervals":
                consumers[i["id"]].append({"kind": kind, "outputs": [o[:90] for o in outs][:4], "n_outputs": len(outs), "running_guard": running})
        for o in outs:
            cid, _, prop = o.rpartition(".")
            if prop.split("@", 1)[0] == "disabled":
                disabled_writers[cid].append(kind)

    rows = []
    for iv in intervals:
        cs = consumers.get(iv["id"], [])
        # STEADY-STATE rate. A finite ``max_intervals`` (>= 0) stops the timer after that many ticks,
        # so it contributes nothing in steady state. The first run of this script counted
        # ``params-init-interval`` (max_intervals=1, six server consumers) as a perpetual 1 Hz source.
        finite = isinstance(iv["max_intervals"], int) and iv["max_intervals"] >= 0
        tps = 0.0 if (iv["disabled"] or finite) else 1000.0 / max(1, iv["interval_ms"])
        rows.append(
            {
                **iv,
                "ticks_per_s_default": round(tps, 3),
                "consumers": len(cs),
                "server_consumers": sum(1 for c in cs if c["kind"] == "server"),
                "clientside_consumers": sum(1 for c in cs if c["kind"] == "clientside"),
                "running_guarded": any(c["running_guard"] for c in cs),
                "disabled_written_by": disabled_writers.get(iv["id"], []),
                "consumer_detail": cs,
            }
        )
    rows.sort(key=lambda r: -r["ticks_per_s_default"])
    total_tps = sum(r["ticks_per_s_default"] for r in rows)
    server_bound = sum(r["ticks_per_s_default"] * r["server_consumers"] for r in rows)
    print(f"{len(rows)} Intervals; {total_tps:.2f} ticks/s at layout defaults; <= {server_bound:.2f} server dispatches/s if every consumer ran every tick\n")
    print(f"{'id':52s} {'ms':>6s} {'dis':>4s} {'t/s':>6s} {'srv':>4s} {'cs':>4s} {'run=':>5s}  disabled-written-by")
    for r in rows:
        print(f"{str(r['id'])[:52]:52s} {r['interval_ms']:>6} {('Y' if r['disabled'] else '-'):>4s} {r['ticks_per_s_default']:>6.2f} {r['server_consumers']:>4} {r['clientside_consumers']:>4} {('Y' if r['running_guarded'] else '-'):>5s}  {','.join(r['disabled_written_by']) or '-'}")
    dead = [r["id"] for r in rows if r["consumers"] == 0]
    print(f"\nno consumer at all ({len(dead)}): {dead}")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps({"canopy_src": args.canopy_src, "rows": rows, "total_ticks_per_s": total_tps, "server_dispatch_bound_per_s": server_bound}, indent=2), encoding="utf-8")
        print(f"json -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
