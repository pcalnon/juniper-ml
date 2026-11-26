"""
Summarise an r27-val-code2 census run: connects by process (pytest / child), port class and refusal; the :8100
connects per test, file and phase; every child-process connect to a Juniper port; the fake's answers and timeouts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2; census util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_census.py

Usage:
    python <this file> <run prefix>      (reads <prefix>.connects.jsonl, .fake.jsonl, .guard.jsonl; prints JSON)
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

JUNIPER = {*range(8050, 8060), 8100, *range(8200, 8212)}


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    prefix = sys.argv[1]
    connects = rows(Path(f"{prefix}.connects.jsonl"))
    fake = rows(Path(f"{prefix}.fake.jsonl"))
    guard = rows(Path(f"{prefix}.guard.jsonl"))
    by_class = collections.Counter()
    for r in connects:
        kind = "pytest" if r["process"] == "pytest" else "child"
        port_class = "8100" if r["port"] == 8100 else ("juniper" if r["port"] in JUNIPER else ("port9" if r["port"] == 9 else "other"))
        by_class[f"{kind}|{port_class}|refused={r['refused']}"] += 1
    c8100 = [r for r in connects if r["port"] == 8100]
    tests = sorted({r["nodeid"] for r in c8100 if r["nodeid"]})
    files = collections.Counter(t.split("::")[0] for t in tests)
    phases = collections.Counter(r["phase"] for r in c8100)
    frames = collections.Counter(" <- ".join(r.get("canopy_frames", [])[:3]) for r in c8100)
    child_juniper = collections.Counter(f"{r['host']}:{r['port']} | {r['process'][:120]}" for r in connects if r["process"] != "pytest" and r["port"] in JUNIPER)
    child_hosts = collections.Counter(f"{r['host']}" for r in connects if r["process"] != "pytest")
    other_pytest = collections.Counter(f"{r['port']}" for r in connects if r["process"] == "pytest" and r["port"] not in JUNIPER)
    outside = [r for r in connects if r["process"] == "pytest" and r["nodeid"] is None]
    timeouts = collections.Counter(json.dumps(f.get("timeout"), sort_keys=True) for f in fake)
    urls = collections.Counter(f"{f['method']} {f['url']} -> {f['answer']}" for f in fake)
    fake_tests = sorted({f["nodeid"] for f in fake if f["nodeid"]})
    header_sets = collections.Counter(",".join(f.get("header_names", [])) for f in fake)
    summary = {
        "connects_total": len(connects),
        "by_process_portclass_refusal": dict(sorted(by_class.items())),
        "c8100": {"connects": len(c8100), "tests": len(tests), "files": len(files), "phases": dict(phases), "opening_frames": dict(frames.most_common(6)), "hosts": dict(collections.Counter(r["host"] for r in c8100)), "off_main_thread": sum(1 for r in c8100 if not r["main_thread"])},
        "child_connects_to_juniper_ports": dict(child_juniper),
        "child_connect_hosts": dict(child_hosts),
        "pytest_connects_other_ports_count": sum(other_pytest.values()),
        "pytest_connects_outside_any_test": len(outside),
        "fake": {"answers": len(fake), "tests": len(fake_tests), "files": len({t.split('::')[0] for t in fake_tests}), "timeouts": dict(timeouts), "requests": dict(urls.most_common(12)), "header_name_sets": dict(header_sets)},
        "guard_reports": len(guard),
    }
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
