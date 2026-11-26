"""
Print the in-test timeline of each failed X7 ticker test from juniper-canopy CI job logs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test).

Usage:
    python3 -I <this file> --logs <dir of job_<id>.log files> --out <file.json> [--test <substring>] ...

For every FAILURES block whose header names a --test substring, it reads the "Captured stderr setup/call" sections
(the app's own formatter: "YYYY-MM-DD HH:MM:SS,mmm [LEVEL] logger: message"), and prints each line's time in seconds
relative to the first setup line, the interval since the previous line, and which source it is (demo_mode or the
code under test). It also reports the worst_gap the assertion printed, and for demo_mode lines the intervals between
consecutive demo_mode lines. The log lines carry no thread name, so two demo threads cannot be told apart.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TS_PREFIX = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z ")
APP_LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \[(\w+)\] ([\w.]+): (.*)$")
HEADER = re.compile(r"^_+ (\S+) _+$")
SECTION = re.compile(r"^-+ Captured (stderr|stdout|log) (setup|call|teardown) -+$")
GAP = re.compile(r"(?:stalled the loop for|health took|took) (\d+\.\d+)s")
ASSERT_NUM = re.compile(r"^E\s+assert (\d+\.\d+) (<|>=|<=|>) (\d+\.\d+)")


def parse(path: Path, tests: list[str]) -> list[dict]:
    lines = [TS_PREFIX.sub("", ln.rstrip("\r\n")) for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    blocks = []
    cur = None
    section = None
    for ln in lines:
        m = HEADER.match(ln)
        if m:
            cur = {"header": m.group(1), "events": [], "assert": None, "gap_message": None}
            blocks.append(cur)
            section = None
            continue
        if cur is None:
            continue
        if ln.startswith("=" * 10):
            cur = None
            continue
        m = SECTION.match(ln)
        if m:
            section = (m.group(1), m.group(2))
            continue
        m = ASSERT_NUM.match(ln)
        if m and cur["assert"] is None:
            cur["assert"] = [float(m.group(1)), m.group(2), float(m.group(3))]
        m = GAP.search(ln)
        if m and ln.startswith("E ") and cur["gap_message"] is None:
            cur["gap_message"] = ln[:300]
        if section and section[0] == "stderr":
            m = APP_LINE.match(ln)
            if m:
                t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
                cur["events"].append({"phase": section[1], "t": t, "level": m.group(2), "logger": m.group(3), "msg": m.group(4)[:160]})
    out = []
    for b in blocks:
        if not any(s in b["header"] for s in tests):
            continue
        ev = b["events"]
        if not ev:
            out.append({"header": b["header"], "assert": b["assert"], "events": []})
            continue
        t0 = ev[0]["t"]
        prev = None
        rows = []
        demo_times = []
        for e in ev:
            rel = (e["t"] - t0).total_seconds()
            dt = None if prev is None else round(rel - prev, 3)
            prev = rel
            src = "DEMO" if e["logger"] == "demo_mode" else "CODE"
            if src == "DEMO":
                demo_times.append(rel)
            rows.append({"phase": e["phase"], "rel_s": round(rel, 3), "dt_s": dt, "src": src, "clock": e["t"].strftime("%H:%M:%S.%f")[:-3], "logger": e["logger"], "msg": e["msg"]})
        demo_iv = [round(b2 - a, 3) for a, b2 in zip(demo_times, demo_times[1:])]
        out.append({"header": b["header"], "assert": b["assert"], "gap_message": b["gap_message"], "events": rows, "demo_lines": len(demo_times), "demo_intervals_s": demo_iv})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--test", action="append", default=[])
    args = ap.parse_args()
    tests = args.test or ["test_relay_cascade_add_does_not_block_the_loop", "test_initialize_sync_does_not_block_the_loop"]
    result = {}
    for p in sorted(Path(args.logs).glob("job_*.log")):
        blocks = parse(p, tests)
        if blocks:
            result[p.stem] = blocks
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    for job, blocks in result.items():
        for b in blocks:
            print(f"== {job} {b['header']} assert={b['assert']} demo_lines={b.get('demo_lines')} demo_intervals={b.get('demo_intervals_s')}")
            for r in b["events"]:
                print(f"   {r['phase']:5s} {r['clock']} +{r['rel_s']:7.3f} (dt {r['dt_s']}) {r['src']} {r['logger'][-40:]}: {r['msg'][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
