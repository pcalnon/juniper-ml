#!/usr/bin/env python3
"""Re-derive every soak figure docs/REFERENCE.md quotes, after the D5 invalidation.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Owner decision D5 (ruled 2026-09-17, implemented by ml#1952) invalidated one row
-- the single run that demonstrably READ the ledger it was being scored against.
That moved the corpus 43 -> 42 and every derived figure with it.

`docs/REFERENCE.md` quotes eight of those figures inline: the pooled rate, both
era rows, four per-probe intervals, and retention. RE-RUN THEM; do not transcribe
the old ones and adjust by hand. The arc has already shipped one headline that was
wrong because a figure was carried forward rather than re-derived, and the ledger's
own `analyse()` applies invalidate / rescore / in_scope filters that a hand count
does not.

    python3 util/ad-hoc/2026-09-17_soak_post_ruling_recount.py
"""

from __future__ import annotations

import importlib.util
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER_TOOL = ROOT / "util" / "soak_ledger.py"
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"
ERA = "2026-08-31"


def _load():
    spec = importlib.util.spec_from_file_location("soak_ledger_recount", LEDGER_TOOL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    sl = _load()
    rows = [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]

    # Go through analyse() rather than filtering by hand: it is what `report`
    # prints, so anything derived another way is a different number by definition.
    def line(tag: str, st: dict) -> str:
        s = st["seeded"]
        return (f"{tag:9s} {s['follows']}/{s['denom']} = {(s['rate'] or 0):.1%}  "
                f"ci=[{s['ci_low']:.3f}, {s['ci_high']:.3f}]  verdict={st['verdict']}"
                f"  ({st['note']})")

    st = sl.analyse(rows)
    print(line("pooled", st))
    s = st["seeded"]
    print(f"          misses={s['misses']}  src-recovered={s['source_recovered']}  "
          f"correct={s['denom'] - s['misses']}/{s['denom']}  "
          f"retention={s['retention']:.1%} ci=[{s['retention_ci'][0]:.3f}, {s['retention_ci'][1]:.3f}]")

    # The era split analyse() cannot do (item C: no era filter). Same filters,
    # applied by replaying analyse() over each half.
    eras: dict[str, list] = {"pre": [], "post": []}
    for r in rows:
        ts = str(r.get("ts", ""))
        if r.get("kind") != "observation":
            continue
        eras["pre" if ts < ERA else "post"].append(r)
    for name, half in eras.items():
        print(line(name, sl.analyse(half + [r for r in rows if r.get("kind") != "observation"])))

    # Per-probe, on effective outcomes -- the same quantity the per-probe line in
    # docs/REFERENCE.md quotes.
    per: dict[str, list] = defaultdict(list)
    eff = sl.effective_outcomes(rows) if hasattr(sl, "effective_outcomes") else None
    print("\nper-probe (follows/n, Wilson):")
    if eff is None:
        inval = {r.get("invalidates") for r in rows if r.get("kind") == "invalidate"}
        resc = {r.get("rescores"): r.get("to_outcome") for r in rows if r.get("kind") == "rescore"}
        for r in rows:
            if r.get("kind") != "observation" or r.get("arm") != "seeded":
                continue
            rid = r.get("obs_id")
            if rid in inval:
                continue
            per[r["probe_id"]].append(resc.get(rid, r.get("outcome")))
    for pid in sorted(per):
        outs = per[pid]
        k, n = sum(1 for o in outs if o == "follow"), len(outs)
        lo, hi = sl.wilson(k, n)
        wrong = sum(1 for o in outs if o == "miss")
        print(f"  {pid:34s} {k}/{n}  [{lo:.3f}, {hi:.3f}]   misses={wrong}")

    misses = [(r["probe_id"], r.get("run_id")) for r in rows
              if r.get("kind") == "observation" and r.get("outcome") == "miss"]
    print(f"\nmiss rows (pre-invalidation): {misses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
