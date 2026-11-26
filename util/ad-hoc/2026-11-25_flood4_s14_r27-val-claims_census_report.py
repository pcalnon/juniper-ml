"""
Summarise one census run of 2026-11-25_flood4_s14_r27-val-claims_census.py into connect and outcome counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r27 (juniper-canopy unit-lane :8100 connects)

Usage:
    python -I <this file> <census output dir> <summary json path>

Reads connects.jsonl and reports.jsonl and writes one JSON summary: test outcomes counted the way pytest's terminal
summary counts them (passed / failed / skipped / error / xfailed / xpassed), connects to port 8100 (total, tests, files,
tests by phase, the request and the app frame pair that opened each), connects to the other fenced Juniper ports, other
destination ports, and every report the conftest network guard flagged.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

JUNIPER_PORTS = frozenset({*range(8050, 8060), 8100, *range(8200, 8212)})


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _outcomes(reports: list[dict]) -> dict:
    counts: collections.Counter = collections.Counter()
    for report in reports:
        when, outcome = report["when"], report["outcome"]
        if when == "call":
            if report["wasxfail"]:
                counts["xfailed" if outcome == "skipped" else "xpassed"] += 1
            else:
                counts[outcome] += 1
        elif outcome == "failed":
            counts["error"] += 1
        elif outcome == "skipped":
            counts["xfailed" if report["wasxfail"] else "skipped"] += 1
    return dict(sorted(counts.items()))


def _opener(record: dict) -> str:
    request = record.get("request") or {}
    frames = request.get("app_frames") or record.get("app_frames") or []
    return " <- ".join(reversed(frames[-2:])) if frames else "(no app frame)"


def main() -> int:
    run_dir, summary_path = Path(sys.argv[1]), Path(sys.argv[2])
    connects = _load(run_dir / "connects.jsonl")
    reports = _load(run_dir / "reports.jsonl")
    to_8100 = [record for record in connects if record["port"] == 8100]
    tests_by_phase: dict[str, set] = collections.defaultdict(set)
    for record in to_8100:
        tests_by_phase[record["phase"] or "outside-a-phase"].add(record["nodeid"])
    tests_8100 = {record["nodeid"] for record in to_8100}
    files_8100 = collections.Counter()
    for nodeid in tests_8100:
        files_8100[(nodeid or "?").split("::")[0]] += 1
    openers = collections.defaultdict(lambda: {"connects": 0, "tests": set()})
    for record in to_8100:
        key = _opener(record)
        openers[key]["connects"] += 1
        openers[key]["tests"].add(record["nodeid"])
    other_juniper = [record for record in connects if record["port"] in JUNIPER_PORTS and record["port"] != 8100]
    other_ports = collections.Counter(record["port"] for record in connects if record["port"] not in JUNIPER_PORTS)
    guard_flagged = [{"nodeid": report["nodeid"], "when": report["when"], "guard": report["guard"]} for report in reports if report["guard"]]
    failed = [{"nodeid": report["nodeid"], "when": report["when"], "longrepr_tail": report["longrepr"]} for report in reports if report["outcome"] == "failed"]
    setup_only = tests_by_phase.get("setup", set())
    call_only = tests_by_phase.get("call", set())
    summary = {
        "run_dir": str(run_dir),
        "outcomes": _outcomes(reports),
        "reports": len(reports),
        "port_8100": {
            "connects": len(to_8100),
            "tests": len(tests_8100),
            "files": len(files_8100),
            "tests_by_phase": {phase: len(nodeids) for phase, nodeids in sorted(tests_by_phase.items())},
            "tests_in_setup_and_call": sorted(setup_only & call_only),
            "hosts": dict(collections.Counter(record["host"] for record in to_8100)),
            "requests": dict(collections.Counter((record.get("request") or {}).get("request") for record in to_8100)),
            "off_main_thread": sum(1 for record in to_8100 if record["thread"]),
            "openers": {key: {"connects": value["connects"], "tests": len(value["tests"])} for key, value in sorted(openers.items())},
            "files_by_test_count": dict(sorted(files_8100.items(), key=lambda item: (-item[1], item[0]))),
            "tests_with_more_than_one_connect": dict(sorted((nodeid, count) for nodeid, count in collections.Counter(record["nodeid"] for record in to_8100).items() if count > 1)),
        },
        "other_juniper_port_connects": len(other_juniper),
        "other_ports": dict(sorted(other_ports.items())),
        "guard_flagged": guard_flagged,
        "failed_reports": failed,
    }
    summary_path.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    brief = {key: summary[key] for key in ("outcomes", "other_juniper_port_connects", "other_ports")}
    brief["port_8100"] = {key: summary["port_8100"][key] for key in ("connects", "tests", "files", "tests_by_phase", "hosts", "requests", "off_main_thread", "openers")}
    brief["guard_flagged"] = len(guard_flagged)
    brief["failed_reports"] = [item["nodeid"] + " [" + item["when"] + "]" for item in failed]
    print(json.dumps(brief, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
