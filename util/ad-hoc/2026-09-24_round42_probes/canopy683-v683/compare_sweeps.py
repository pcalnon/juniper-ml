"""Compare GET-only route sweeps of base vs head for each key configuration."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
for K in ["unset", "ws", "empty", "real", "padded"]:
    b = json.loads((HERE / f"sweep-base-{K}.json").read_text())
    h = json.loads((HERE / f"sweep-head-{K}.json").read_text())
    rb = {(r["kind"], r["path"], tuple(r["methods"])) for r in b["routes"]}
    rh = {(r["kind"], r["path"], tuple(r["methods"])) for r in h["routes"]}
    pb = {(p["method"], p["path"]): (p["tier"], p["status"], p["detail"]) for p in b["pairs"]}
    ph = {(p["method"], p["path"]): (p["tier"], p["status"], p["detail"]) for p in h["pairs"]}
    tierdiff = [k for k in set(pb) & set(ph) if pb[k][0] != ph[k][0]]
    statdiff = [(k, pb[k][1:], ph[k][1:]) for k in set(pb) & set(ph) if k[0] == "GET" and pb[k][1:] != ph[k][1:]]
    print(f"== key={K}: auth base={b['auth_enabled_main']} head={h['auth_enabled_main']}; docs base={b['docs_enabled']} head={h['docs_enabled']}")
    print(f"   routes only in head: {sorted(rh - rb)}")
    print(f"   routes only in base: {sorted(rb - rh)}")
    print(f"   pairs total base={len(pb)} head={len(ph)}; tier changes: {tierdiff}")
    print(f"   GET status changes on common pairs: {statdiff}")
    print(f"   head-only pairs + keyless status: {[(k, ph[k][1]) for k in sorted(set(ph) - set(pb))]}")
    print(f"   base-only pairs + keyless status: {[(k, pb[k][1]) for k in sorted(set(pb) - set(ph))]}")
    gets = [k for k in ph if k[0] == "GET"]
    print(f"   head GET pairs probed={len(gets)}; keyless 200s={sum(1 for k in gets if ph[k][1] == 200)}; 401s={sum(1 for k in gets if ph[k][1] == 401)}")
