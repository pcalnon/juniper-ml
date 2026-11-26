"""
Recompute, from the r28 builder's raw run files, every number its texts quote (GC passes, 50-run results, probes).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test).

Usage:
    python3 -I <this file> --runs <the builder's runs/ dir> --out <file.json>

Reads (never writes) the builder's files: lane_*/gc_pauses.jsonl (the gc.callbacks recorder: generation, ms, thread,
nodeid), fifty/*.gc.jsonl (the load plugin's forced passes), fifty/*.junit.xml and mutants/*.junit.xml (pass / fail
counts and failure messages), fifty/probe_gcload.jsonl, fifty/held_*.jsonl and repro/v2_*.jsonl (probe rows), and
lane_*/*.run.json. Prints one line per quantity and writes the same as JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET  # nosec B405 - reads local junit files the builder's own pytest wrote
from pathlib import Path


def jsonl(path: Path) -> list[dict]:
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            rows.append(json.loads(ln))
    return rows


def gc_lane(path: Path) -> dict:
    rows = jsonl(path)
    big = [r for r in rows if r.get("ms", 0) >= 50]
    out = {
        "file": str(path),
        "rows": len(rows),
        "ge_50ms": len(big),
        "by_generation": {},
        "by_thread": {},
        "first_ms": big[0]["ms"] if big else None,
    }
    for r in big:
        out["by_generation"][str(r.get("generation"))] = out["by_generation"].get(str(r.get("generation")), 0) + 1
        out["by_thread"][r.get("thread")] = out["by_thread"].get(r.get("thread"), 0) + 1
    def dir_of(nodeid: str) -> str:
        if not nodeid:
            return "(none)"
        parts = nodeid.split("::")[0].split("/")
        return "/".join(parts[:3]) if len(parts) > 3 else "/".join(parts[:-1])
    by_dir: dict[str, list] = {}
    for r in big:
        by_dir.setdefault(dir_of(r.get("nodeid", "")), []).append(r)
    out["by_dir"] = {d: {"n": len(v), "ms": [x["ms"] for x in v], "gens": sorted({x.get("generation") for x in v}), "threads": sorted({x.get("thread") for x in v})} for d, v in by_dir.items()}
    out["regression"] = [{"ms": r["ms"], "gen": r.get("generation"), "thread": r.get("thread"), "nodeid": r.get("nodeid"), "phase": r.get("phase")} for r in big if "src/tests/regression/" in (r.get("nodeid") or "")]
    out["x7_hits"] = [r for r in big if "test_x7" in (r.get("nodeid") or "")]
    out["non_gen2_or_non_main"] = [r for r in big if r.get("generation") != 2 or r.get("thread") != "MainThread"]
    unit = [r for r in big if "src/tests/unit/" in (r.get("nodeid") or "")]
    out["unit_last4_ms"] = [r["ms"] for r in unit[-4:]]
    return out


def junit(path: Path) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 - local file
    cases = root.iter("testcase")
    n = fail = err = skip = 0
    msgs = []
    names: dict[str, list[int]] = {}
    for c in cases:
        n += 1
        name = c.get("name")
        st = "pass"
        for child in c:
            if child.tag == "failure":
                fail += 1
                st = "fail"
                msgs.append((child.get("message") or "")[:300])
            elif child.tag == "error":
                err += 1
                st = "error"
                msgs.append((child.get("message") or "")[:300])
            elif child.tag == "skipped":
                skip += 1
                st = "skip"
        base = re.sub(r"\[\d+-\d+\]$", "", name or "")
        names.setdefault(base, [0, 0])
        names[base][0 if st == "pass" else 1] += 1
    gaps = []
    for m in msgs:
        g = re.search(r"stalled the loop for (\d+\.\d+)s", m)
        if g:
            gaps.append(float(g.group(1)))
    uniq_msgs = sorted({re.sub(r"\d+\.\d+", "N", m) for m in msgs})
    out = {"file": str(path), "tests": n, "failures": fail, "errors": err, "skipped": skip, "per_test_pass_fail": names, "distinct_messages": uniq_msgs[:8]}
    if gaps:
        out["gap_min"] = min(gaps)
        out["gap_median"] = statistics.median(gaps)
        out["gap_max"] = max(gaps)
        out["gap_n"] = len(gaps)
    return out


def probe(path: Path) -> dict:
    rows = jsonl(path)
    cells: dict[str, list] = {}
    for r in rows:
        cells.setdefault(f"{r.get('cell')}/{r.get('procedure')}", []).append(r)
    out = {}
    for k, v in cells.items():
        gaps = [r["worst_gap"] for r in v if "worst_gap" in r]
        d = {"n": len(v), "demo_threads_alive": sorted({r.get("demo_threads_alive") for r in v})}
        if gaps:
            d.update({"gap_min": round(min(gaps), 3), "gap_max": round(max(gaps), 3), "gap_median": round(statistics.median(gaps), 3), "ge_0.2": sum(1 for g in gaps if g >= 0.2)})
        if any("stub_on_loop_thread" in r for r in v):
            d["stub_on_loop_thread"] = sorted({r.get("stub_on_loop_thread") for r in v if "stub_on_loop_thread" in r}, key=str)
        if any("released_by_loop" in r for r in v):
            d["released"] = sum(1 for r in v if r.get("released_by_loop"))
            d["off_loop"] = sum(1 for r in v if r.get("off_loop"))
            d["latency_max"] = max(r.get("release_latency", 0) for r in v)
        out[k] = d
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    runs = Path(args.runs)
    res: dict = {}
    for lane in ("lane_base_gc", "lane_fixed"):
        p = runs / lane / "gc_pauses.jsonl"
        if p.exists():
            res[f"gc_{lane}"] = gc_lane(p)
    for p in sorted((runs / "fifty").glob("*.gc.jsonl")):
        ms = [r["ms"] for r in jsonl(p)]
        res[f"load_{p.stem}"] = {"n": len(ms), "min": min(ms), "max": max(ms), "mean": round(statistics.mean(ms), 1)}
    for p in sorted(list((runs / "fifty").glob("*.junit.xml")) + list((runs / "mutants").glob("*.junit.xml")) + list((runs / "on_r27").glob("*.junit.xml")) + list((runs / "fixed").glob("*.junit.xml")) + list((runs / "changed_file_ci").glob("*.junit.xml"))):
        res[f"junit_{p.parent.name}_{p.stem}"] = junit(p)
    for p in sorted(list((runs / "fifty").glob("probe_*.jsonl")) + list((runs / "fifty").glob("held_*.jsonl")) + list((runs / "repro").glob("v2_*.jsonl")) + list((runs / "repro").glob("base_*.jsonl"))):
        res[f"probe_{p.parent.name}_{p.stem}"] = probe(p)
    for p in sorted(runs.glob("lane_*/*.run.json")):
        res[f"run_{p.stem}"] = json.loads(p.read_text(encoding="utf-8"))
    Path(args.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for k, v in res.items():
        s = json.dumps(v, default=str)
        print(f"{k}: {s[:1500]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
