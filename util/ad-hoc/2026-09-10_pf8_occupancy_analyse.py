#!/usr/bin/env python3
"""
Reduce a PF-8 occupancy trace to cores per cell, read a second run's cost off the headroom sweep's response curve under a stated assumption, and compare a two-arm pair.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc — investigation (perf lane P2 item 4.1 residue: the PF-8 occupancy probe, step 1 of §1.3 of the 2026-09-08 re-scope note)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md

WHAT IT COMPUTES

For every cell in a suite's `registry.jsonl`, the trace rows written by
`2026-09-10_pf8_occupancy_sampler.py` for that cell's run are split into the TRAINING window —
bracketed by the first and last `ts_unix` of the driver's `metrics_series.csv`, i.e. the drive
loop, the only phase the sweep measured — and the whole run (bring-up to teardown). Occupancy is
cpu-seconds / wall-seconds — CORES. Reading a core as one sweep worker (one saturated `sha256sum`
process) is an ASSUMPTION §8.4 of the sweep note disclaims ("the knee is located in worker count,
not in cores"); the readout below is conditional on it, and the two-arm pair measures the
externality directly instead.

    occupancy          cascor tree (uvicorn + forkserver + candidate pool + other) in the window
    total_occupancy    + the juniper-data service and the driver
    p95 / max          the per-second cascor-tree occupancy's tail, for the burst shape
    ambient_cores      host_busy_cores minus this run's total — everyone else on the host
    run_occupancy      cascor tree over the whole run, bring-up and teardown included

THE READOUT (§8.4 of the 2026-09-02 instrument-resolution note)

A second Juniper run is a load of W workers on the first, so the second run's cost is the sweep
curve at N = W: 6 workers cost +19.9%, INSIDE the 20.5% quiet band (not separable); 8 and 10 cost
+86.1% / +85.2% (a plateau); 12 costs +181.6%. §1.3 of the re-scope note runs the two-arm pair only
when W lands in the ~4–8 band around the knee — below 4 the host cannot separate the effect, above
8 the sweep already says "plateau".

    python3 util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py --suite SUITE_DIR --trace SUITE_DIR/occupancy.tsv [--json OUT]
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

#: §8.4 response curve: synthetic workers -> % change in mean step duration vs the quiet mean.
SWEEP_CURVE = {6: 19.9, 8: 86.1, 10: 85.2, 12: 181.6}
QUIET_BAND_PCT = 20.5
KNEE_LOW = 6.0
KNEE_HIGH = 8.0
#: §1.3 of the re-scope note: the pair is worth running only inside this band.
PAIR_BAND = (4.0, 8.0)
NUMERIC = ("epoch_s", "wall_dt", "cascor_uvicorn", "cascor_forkserver", "cascor_workers", "cascor_other", "data", "driver", "cascor_tree", "total", "n_workers", "n_pids", "vanished", "host_busy_cores", "load_1m")


def readout(worker_equivalents: float) -> dict:
    """Where one run sits on the sweep axis, and what that says about a second run."""
    w = worker_equivalents
    if w < KNEE_LOW:
        cost = f"below the 6-worker point (+{SWEEP_CURVE[6]}% there, inside the {QUIET_BAND_PCT}% quiet band): below what this host can measure — which is not 'free'"
        band = "below-knee"
    elif w < KNEE_HIGH:
        cost = f"at the knee (+{SWEEP_CURVE[6]}% at 6 -> +{SWEEP_CURVE[8]}% at 8): the sweep cannot read it; only the two-arm pair can"
        band = "knee"
    elif w < 12:
        cost = f"on the plateau: about +{SWEEP_CURVE[8]}% (8 and 10 workers indistinguishable)"
        band = "plateau"
    else:
        cost = f"+{SWEEP_CURVE[12]}% at 12 workers, and rising"
        band = "beyond-plateau"
    return {
        "worker_equivalents": w,
        "band": band,
        "second_run_cost": cost,
        "pair_worth_running": PAIR_BAND[0] <= w <= PAIR_BAND[1],
        "assumption": "one core = one sweep worker; untested — §8.4 of the sweep note locates the knee in worker count, not cores",
    }


def load_trace(path: Path) -> "list[dict]":
    rows = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            for key in NUMERIC:
                if key in row and row[key] not in (None, ""):
                    row[key] = float(row[key])
            rows.append(row)
    return rows


def registry_rows(suite_dir: Path) -> "list[dict]":
    text = (suite_dir / "registry.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def drive_window(run_dir: Path) -> "tuple[float, float] | None":
    """First and last poll timestamp of the driver's series — the drive loop's extent."""
    series = run_dir / "artifacts" / "results" / "metrics_series.csv"
    if not series.is_file():
        return None
    stamps = []
    with series.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                stamps.append(float(row["ts_unix"]))
            except (KeyError, ValueError):
                continue
    if len(stamps) < 2:
        return None
    return min(stamps), max(stamps)


def _percentile(values: "list[float]", pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, int(round(pct / 100.0 * (len(ordered) - 1)))))
    return ordered[rank]


def reduce_rows(rows: "list[dict]") -> dict:
    """Occupancy over a set of trace rows (cpu-seconds / wall-seconds), plus tail and ambient figures."""
    wall = sum(r["wall_dt"] for r in rows)
    if not rows or wall <= 0:
        return {"samples": 0, "wall_s": 0.0, "occupancy": 0.0, "total_occupancy": 0.0, "p95": 0.0, "max": 0.0, "n_workers_mode": 0, "host_busy_cores": 0.0, "ambient_cores": 0.0, "load_1m": 0.0, "vanished": 0}
    tree = sum(r["cascor_tree"] for r in rows)
    total = sum(r["total"] for r in rows)
    per_second = [r["cascor_tree"] / r["wall_dt"] for r in rows if r["wall_dt"] > 0]
    busy = statistics.fmean(r["host_busy_cores"] for r in rows)
    ambient = statistics.fmean(r["host_busy_cores"] - (r["total"] / r["wall_dt"] if r["wall_dt"] > 0 else 0.0) for r in rows)
    workers = Counter(int(r["n_workers"]) for r in rows).most_common(1)[0][0]
    # The run is not a constant load: under the default budget the INITIAL output-layer pass runs
    # in the listener at the runtime-default pool width (~11 cores, measured 2026-09-10), and every
    # later pass and the candidate phases sit near 2. Report how much of the window sits at or
    # above the sweep's knee, and the mean occupancy on each side of it, so a bimodal trace is not
    # read as its mean alone.
    high = [r for r in rows if r["wall_dt"] > 0 and r["cascor_tree"] / r["wall_dt"] >= KNEE_LOW]
    low = [r for r in rows if r["wall_dt"] > 0 and r["cascor_tree"] / r["wall_dt"] < KNEE_LOW]
    plateau = [r for r in rows if r["wall_dt"] > 0 and r["cascor_tree"] / r["wall_dt"] >= KNEE_HIGH]

    def _occ(subset: "list[dict]") -> float:
        w = sum(r["wall_dt"] for r in subset)
        return round(sum(r["cascor_tree"] for r in subset) / w, 3) if w > 0 else 0.0

    return {
        "samples": len(rows),
        "wall_s": round(wall, 3),
        "occupancy": round(tree / wall, 3),
        "total_occupancy": round(total / wall, 3),
        "p95": round(_percentile(per_second, 95), 3),
        "max": round(max(per_second), 3) if per_second else 0.0,
        "n_workers_mode": workers,
        "host_busy_cores": round(busy, 3),
        "ambient_cores": round(ambient, 3),
        "load_1m": round(statistics.fmean(r["load_1m"] for r in rows), 3),
        "vanished": int(sum(r["vanished"] for r in rows)),
        "share_at_or_above_knee": round(sum(r["wall_dt"] for r in high) / wall, 3),
        "share_at_or_above_plateau": round(sum(r["wall_dt"] for r in plateau) / wall, 3),
        "occupancy_above_knee": _occ(high),
        "occupancy_below_knee": _occ(low),
    }


def in_window(rows: "list[dict]", window: "tuple[float, float]") -> "list[dict]":
    """Rows whose interval MIDPOINT lies inside the window (a row is stamped at the end of its interval)."""
    lo, hi = window
    return [r for r in rows if lo <= r["epoch_s"] - r["wall_dt"] / 2.0 <= hi]


def summarise(suite_dir: Path, trace: "list[dict]") -> dict:
    cells = []
    for reg in registry_rows(suite_dir):
        run_id = reg.get("run_id")
        run_rows = [r for r in trace if r["run_id"] == run_id]
        run_dir = Path(reg["run_dir"]) if reg.get("run_dir") else None
        window = drive_window(run_dir) if run_dir else None
        entry = {"cell_id": reg["cell_id"], "run_id": run_id, "outcome": reg.get("outcome"), "thread_budget": reg.get("thread_budget"), "window": window, "trace_rows": len(run_rows)}
        entry["run"] = reduce_rows(run_rows)
        entry["drive"] = reduce_rows(in_window(run_rows, window)) if window else None
        if run_dir and (run_dir / "manifest.json").is_file():
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            entry["timings"] = manifest.get("timings")
            entry["completion_reason"] = manifest.get("completion_reason")
            # The registry's thread_budget is set only in parallel mode; the manifest records what
            # the driver's environment actually carried, pinned by hand or not.
            entry["thread_env"] = (manifest.get("environment") or {}).get("thread_env")
        stats = run_dir / "artifacts" / "results" / "stats.json" if run_dir else None
        if stats and stats.is_file():
            block = (json.loads(stats.read_text(encoding="utf-8")).get("cascor") or {}).get("training_step_duration") or {}
            entry["step_count"] = block.get("total_steps")
            entry["mean_step_ms"] = round(float(block["overall_mean_seconds"]) * 1000.0, 3) if block.get("overall_mean_seconds") is not None else None
        cells.append(entry)
    measured = [c["drive"]["occupancy"] for c in cells if c.get("drive") and c["drive"]["samples"] > 0 and c.get("outcome") == "succeeded"]
    aggregate = None
    if measured:
        mean = statistics.fmean(measured)
        aggregate = {"cells": len(measured), "mean": round(mean, 3), "min": round(min(measured), 3), "max": round(max(measured), 3), "spread_pct": round((max(measured) / min(measured) - 1.0) * 100.0, 1) if min(measured) > 0 else None, "readout_mean": readout(mean), "readout_max": readout(max(measured))}
    ambient_rows = [r for r in trace if r["run_id"] == "-"]
    ambient = {"samples": len(ambient_rows), "host_busy_cores": round(statistics.fmean(r["host_busy_cores"] for r in ambient_rows), 3), "load_1m": round(statistics.fmean(r["load_1m"] for r in ambient_rows), 3)} if ambient_rows else None
    windows = [c["window"] for c in cells if c.get("window") and c.get("outcome") == "succeeded"]
    return {"suite_dir": str(suite_dir), "cells": cells, "aggregate": aggregate, "between_cells": ambient, "pair_overlap": window_overlap(windows[0], windows[1]) if len(windows) == 2 else None}


def window_overlap(a: "tuple[float, float]", b: "tuple[float, float]") -> dict:
    """How aligned two drive windows were: the shared span as a fraction of each, and the start offset.

    A parallel arm's two cells are submitted back-to-back but bring their stacks up
    independently, so their training windows need not coincide; the re-scope note left that
    unmeasured. 1.0 means one window lies entirely inside the other.
    """
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    shared = max(0.0, hi - lo)
    return {
        "shared_s": round(shared, 3),
        "fraction_of_a": round(shared / (a[1] - a[0]), 3) if a[1] > a[0] else 0.0,
        "fraction_of_b": round(shared / (b[1] - b[0]), 3) if b[1] > b[0] else 0.0,
        "start_offset_s": round(abs(a[0] - b[0]), 3),
    }


def arm_cells(summaries: "list[dict]") -> "list[dict]":
    """The measurable cells of an arm: succeeded, traced inside their drive window, with a mean step."""
    return [c for s in summaries for c in s["cells"] if c.get("outcome") == "succeeded" and c.get("drive") and c["drive"]["samples"] > 0 and c.get("mean_step_ms") is not None]


def _arm_stats(cells: "list[dict]") -> dict:
    steps = [c["mean_step_ms"] for c in cells]
    occ = [c["drive"]["occupancy"] for c in cells]
    return {
        "cells": len(cells),
        "step_counts": sorted({c.get("step_count") for c in cells}, key=lambda v: (v is None, v)),
        "mean_step_ms": round(statistics.fmean(steps), 3) if steps else None,
        "min_step_ms": round(min(steps), 3) if steps else None,
        "max_step_ms": round(max(steps), 3) if steps else None,
        "spread_pct": round((max(steps) / min(steps) - 1.0) * 100.0, 1) if steps and min(steps) > 0 else None,
        "occupancy_mean": round(statistics.fmean(occ), 3) if occ else None,
        "thread_envs": sorted({json.dumps(c.get("thread_env"), sort_keys=True) for c in cells}),
    }


def compare_arms(parallel: "list[dict]", control: "list[dict]") -> dict:
    """The PF-8 pair verdict: parallel-arm mean step over control-arm mean step, with identity checked first.

    Identity before comparison, as the run tier's comparator does: the arms must carry the same
    thread env (or they differ in budget, not only in concurrency) and the same step count (or
    they did different work). The cost is then read two ways — against the sweep's 20.5% quiet
    band, which is the lane's standing rule for "located", and against the arms' own within-arm
    spread on the day, which says whether today's brackets resolve it at all.
    """
    p_cells, c_cells = arm_cells(parallel), arm_cells(control)
    p, c = _arm_stats(p_cells), _arm_stats(c_cells)
    ratio = (p["mean_step_ms"] / c["mean_step_ms"]) if p["mean_step_ms"] and c["mean_step_ms"] else None
    cost_pct = round((ratio - 1.0) * 100.0, 1) if ratio is not None else None
    pair_totals = []
    for s in parallel:
        cells = [x for x in s["cells"] if x.get("outcome") == "succeeded" and x.get("drive") and x["drive"]["samples"] > 0]
        if cells:
            pair_totals.append(round(sum(x["drive"]["occupancy"] for x in cells), 3))
    overlaps = [s["pair_overlap"] for s in parallel if s.get("pair_overlap")]
    same_budget = bool(p["thread_envs"]) and p["thread_envs"] == c["thread_envs"]
    same_work = len(p["step_counts"]) == 1 and p["step_counts"] == c["step_counts"]
    within = max(p["spread_pct"] or 0.0, c["spread_pct"] or 0.0)
    return {
        "parallel": p,
        "control": c,
        "ratio": round(ratio, 4) if ratio is not None else None,
        "cost_pct": cost_pct,
        "same_budget": same_budget,
        "same_work": same_work,
        "comparable": same_budget and same_work and ratio is not None,
        "located_vs_quiet_band": (abs(cost_pct) > QUIET_BAND_PCT) if cost_pct is not None else None,
        "resolved_vs_within_arm_spread": (abs(cost_pct) > within) if cost_pct is not None else None,
        "within_arm_spread_pct": round(within, 1),
        "pair_occupancy_totals": pair_totals,
        "overlaps": overlaps,
    }


def render_arms(result: dict) -> str:
    p, c = result["parallel"], result["control"]
    lines = ["PF-8 two-run pair", ""]
    lines.append(f"parallel arm: {p['cells']} cells, step_count {p['step_counts']}, mean step {p['mean_step_ms']} ms (min {p['min_step_ms']}, max {p['max_step_ms']}, spread {p['spread_pct']}%), occupancy per cell {p['occupancy_mean']}, thread env {p['thread_envs']}")
    lines.append(f"control arm : {c['cells']} cells, step_count {c['step_counts']}, mean step {c['mean_step_ms']} ms (min {c['min_step_ms']}, max {c['max_step_ms']}, spread {c['spread_pct']}%), occupancy per cell {c['occupancy_mean']}, thread env {c['thread_envs']}")
    lines.append(f"identity: same budget {result['same_budget']}, same work {result['same_work']} -> {'COMPARABLE' if result['comparable'] else 'NOT COMPARABLE (refuse, as compare_baseline would)'}")
    if result["comparable"]:
        lines.append(f"parallel / control mean step = {result['ratio']}  ->  a second run costs {result['cost_pct']:+.1f}%")
        lines.append(f"  vs the sweep's {QUIET_BAND_PCT}% quiet band (the lane's standing rule): {'LOCATED' if result['located_vs_quiet_band'] else 'below what this host can measure across sessions'}")
        lines.append(f"  vs today's within-arm spread ({result['within_arm_spread_pct']}%): {'resolved by the brackets on the day' if result['resolved_vs_within_arm_spread'] else 'not resolved even on the day'}")
    lines.append(f"two runs together, cascor-tree cores per pair: {result['pair_occupancy_totals']}")
    for ov in result["overlaps"]:
        lines.append(f"  drive-window overlap: {ov['shared_s']} s shared = {ov['fraction_of_a']} of A / {ov['fraction_of_b']} of B; start offset {ov['start_offset_s']} s")
    return "\n".join(lines)


def render(summary: dict) -> str:
    header = "| cell | outcome | steps | mean step ms | drive s | samples | cascor tree (cores) | + data + driver | p95 | max | share ≥ 6 | share ≥ 8 | occ ≥ 6 | occ < 6 | workers | host busy cores | ambient cores | load 1m | vanished | whole-run tree |"
    lines = [f"suite: {summary['suite_dir']}", "", header, "|" + "---|" * 20]
    for c in summary["cells"]:
        d = c.get("drive") or {}
        r = c.get("run") or {}
        drive_s = (c.get("timings") or {}).get("drive")
        cells = [
            c["cell_id"],
            c.get("outcome"),
            c.get("step_count"),
            c.get("mean_step_ms"),
            drive_s,
            d.get("samples", 0),
            f"**{d.get('occupancy', 0.0)}**",
            d.get("total_occupancy", 0.0),
            d.get("p95", 0.0),
            d.get("max", 0.0),
            d.get("share_at_or_above_knee", 0.0),
            d.get("share_at_or_above_plateau", 0.0),
            d.get("occupancy_above_knee", 0.0),
            d.get("occupancy_below_knee", 0.0),
            d.get("n_workers_mode", 0),
            d.get("host_busy_cores", 0.0),
            d.get("ambient_cores", 0.0),
            d.get("load_1m", 0.0),
            d.get("vanished", 0),
            r.get("occupancy", 0.0),
        ]
        lines.append("| " + " | ".join(str(v) for v in cells) + " |")
    envs = {json.dumps(c.get("thread_env"), sort_keys=True) for c in summary["cells"]}
    lines.append("")
    lines.append(f"thread env recorded by the driver: {', '.join(sorted(envs))}")
    agg = summary.get("aggregate")
    lines.append("")
    if agg:
        lines.append(f"cascor-tree occupancy during drive, {agg['cells']} succeeded cells: mean {agg['mean']}  min {agg['min']}  max {agg['max']}  spread {agg['spread_pct']}%  (cores; read as sweep workers only under the assumption below)")
        for label, key in (("mean", "readout_mean"), ("max", "readout_max")):
            ro = agg[key]
            lines.append(f"  readout at the {label} ({ro['worker_equivalents']:.2f}), assuming {ro['assumption']}: band={ro['band']}; a second run costs: {ro['second_run_cost']}; two-arm pair worth running: {'YES' if ro['pair_worth_running'] else 'NO'}")
    else:
        lines.append("no succeeded cell has trace rows inside its drive window — nothing to read off the curve")
    amb = summary.get("between_cells")
    if amb:
        lines.append(f"between cells (host-only rows): {amb['samples']} samples, host busy cores {amb['host_busy_cores']}, load 1m {amb['load_1m']}")
    ov = summary.get("pair_overlap")
    if ov:
        lines.append(f"drive-window overlap of the two cells: {ov['shared_s']} s shared = {ov['fraction_of_a']} of A / {ov['fraction_of_b']} of B; start offset {ov['start_offset_s']} s")
    return "\n".join(lines)


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--suite", type=Path, default=None, help="one suite dir holding registry.jsonl (single-suite mode)")
    parser.add_argument("--parallel", type=Path, nargs="+", default=None, help="parallel-arm suite dirs (pair mode, with --control)")
    parser.add_argument("--control", type=Path, nargs="+", default=None, help="control-arm suite dirs (pair mode, with --parallel)")
    parser.add_argument("--trace", type=Path, required=True, help="the sampler's TSV")
    parser.add_argument("--json", type=Path, default=None, help="also write the full summary here")
    args = parser.parse_args(argv)
    if args.suite is None and not (args.parallel and args.control):
        parser.error("give --suite, or both --parallel and --control")
    trace = load_trace(args.trace)
    if args.suite is not None:
        out: dict = summarise(args.suite, trace)
        print(render(out))
    else:
        parallel = [summarise(d, trace) for d in args.parallel]
        control = [summarise(d, trace) for d in args.control]
        for s in parallel + control:
            print(render(s))
            print()
        result = compare_arms(parallel, control)
        print(render_arms(result))
        out = {"parallel": parallel, "control": control, "pair": result}
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
