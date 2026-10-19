"""
Summarize the F3 memory-headroom samples into p5/p50/p95 per mode, and the G-MEM pass rate at the D1 VM size.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (turing bring-up task F3: memory-headroom baseline)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-17_turing_headroom_sampler.bash (writes the samples);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§6 F3, §9.3 G-MEM, D1)

Each input is a TSV from the sampler. "Available" is free + speculative + inactive pages, the same accounting
util/macvm_ctl.bash uses for G-MEM's "free + inactive". For memory the low tail matters, so p5 is the level that
available memory stayed above 95% of the time; for swap the high tail matters, so p95 is the level swap stayed
below 95% of the time. G-MEM passes a sample when available >= VM + reserve, swap used <= the swap cap, and
Docker Desktop is not running.

Usage:
    python3 util/ad-hoc/2026-10-17_turing_headroom_summarize.py FILE.tsv [FILE.tsv ...]
        [--vm-gib 6] [--reserve-gib 4] [--max-swap-gib 2] [--min-samples 480] [--out SUMMARY.md]

Exit 0 when every mode has at least --min-samples rows; 1 when any mode is short (the summary is still written);
2 for usage errors or an unreadable file.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

MIB = 1024 * 1024


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile; values must be non-empty."""
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def as_int(row: dict[str, str], key: str) -> int | None:
    value = (row.get(key) or "").strip()
    return int(value) if value.isdigit() else None


def load(paths: list[Path]) -> dict[str, list[dict[str, str]]]:
    by_mode: dict[str, list[dict[str, str]]] = {}
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                by_mode.setdefault(row.get("mode") or "?", []).append(row)
    return by_mode


def summarize(mode: str, rows: list[dict[str, str]], vm_gib: int, reserve_gib: int, max_swap_gib: int) -> tuple[str, int]:
    available, swap, free_pct = [], [], []
    passes = usable = docker_rows = 0
    for row in rows:
        page = as_int(row, "page_size")
        parts = [as_int(row, k) for k in ("pages_free", "pages_speculative", "pages_inactive")]
        used = as_int(row, "swap_used_mib")
        docker = row.get("docker") == "1"
        docker_rows += docker
        if as_int(row, "free_pct") is not None:
            free_pct.append(float(row["free_pct"]))
        if page is None or None in parts or used is None:
            continue
        usable += 1
        avail_mib = sum(p for p in parts if p is not None) * page // MIB
        available.append(avail_mib)
        swap.append(used)
        if avail_mib >= (vm_gib + reserve_gib) * 1024 and used <= max_swap_gib * 1024 and not docker:
            passes += 1
    span = f"{rows[0].get('ts_utc', '?')} .. {rows[-1].get('ts_utc', '?')}" if rows else "-"
    lines = [f"## Mode `{mode}`", "", f"- Samples: {len(rows)} ({usable} complete), {span}", f"- Docker Desktop running in {docker_rows} of {len(rows)} samples"]
    if available:
        lines += [
            f"- Available memory (free + speculative + inactive), MiB: p5 {percentile(available, 5):.0f}, p50 {percentile(available, 50):.0f}, p95 {percentile(available, 95):.0f}",
            f"- Swap used, MiB: p5 {percentile(swap, 5):.0f}, p50 {percentile(swap, 50):.0f}, p95 {percentile(swap, 95):.0f}",
            f"- G-MEM pass rate at a {vm_gib} GiB VM (+{reserve_gib} GiB reserve, swap <= {max_swap_gib} GiB, no Docker): {passes}/{usable} = {100 * passes / usable:.1f}%",
        ]
    if free_pct:
        lines.append(f"- memory_pressure free %: p5 {percentile(free_pct, 5):.0f}, p50 {percentile(free_pct, 50):.0f}, p95 {percentile(free_pct, 95):.0f}")
    return "\n".join(lines) + "\n", len(rows)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--vm-gib", type=int, default=6)
    ap.add_argument("--reserve-gib", type=int, default=4)
    ap.add_argument("--max-swap-gib", type=int, default=2)
    ap.add_argument("--min-samples", type=int, default=480)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    missing = [str(p) for p in args.files if not p.is_file()]
    if missing:
        print(f"ERROR: not a file: {', '.join(missing)}", file=sys.stderr)
        return 2
    by_mode = load(args.files)
    sections, short = [], []
    for mode in sorted(by_mode):
        text, count = summarize(mode, by_mode[mode], args.vm_gib, args.reserve_gib, args.max_swap_gib)
        sections.append(text)
        if count < args.min_samples:
            short.append(f"{mode} ({count} < {args.min_samples})")
    report = "# turing memory-headroom baseline (task F3)\n\n" + "\n".join(sections)
    if short:
        report += f"\n**Incomplete:** fewer than {args.min_samples} samples for: {', '.join(short)}.\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if short else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
