#!/usr/bin/env python3
"""
Summarise the r49 claims lens's CI census of juniper-canopy's X7 health test, and set it against the builder's figures.

Reads the census output directory (census.json, unit_jobs.json, runs_all.json, digests/, logs/) written by
util/ad-hoc/2026-11-26_flood4_s16_r49-val-claims_ci_census.py and reports:
  * every job in which the health test FAILED or ERRORED (latency message or a -ra summary line naming it), with run,
    attempt, event, branch, head sha, runner image, Python, latency and every other failing test of the job;
  * the probe timeline of each such failure, from the failure block's captured log: the loop's setup line, the ten
    /v1/health/live answers and the three /api/status answers (seconds after setup; spread);
  * the builder's selection reproduced on the builder's own run list (--builder-runs): runs whose latest attempt failed
    or whose attempt count is above 1, their unit-lane jobs and the failed ones; and the unit-lane jobs that ran
    (success or failure) on main against pull requests, over the same run list;
  * every failed unit-lane job outside that selection, and what the Python 3.15 legs show.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 28, 49)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

TEST = "test_health_stays_fast_while_upstream_is_slow"
STAMP_RE = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) ")


def stamp(text: str) -> float | None:
    m = STAMP_RE.search(text)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f").timestamp()


def timeline(log_text: str) -> dict:
    """The health test's failure block: setup line, probe answers, driver answers (seconds)."""
    lines = log_text.splitlines()
    start = next((i for i, ln in enumerate(lines) if "_ TestLoopStaysAnswerable." + TEST + " _" in ln), None)
    if start is None:
        return {"error": "no failure block"}
    setup, probes, drivers = None, [], []
    for ln in lines[start + 1 :]:
        body = ln.split(" ", 1)[1] if ln[:4].isdigit() and " " in ln else ln
        if body.startswith("____") or "short test summary info" in body:
            break
        if "Captured log" in body:
            continue
        if "Using selector:" in body and setup is None and STAMP_RE.search(body):
            setup = stamp(body)
        elif "HTTP Request: GET http://x7.test/v1/health/live" in body and STAMP_RE.search(body):
            probes.append(stamp(body))
        elif "HTTP Request: GET http://x7.test/api/status" in body and STAMP_RE.search(body):
            drivers.append(stamp(body))
    out = {"probes": len(probes), "drivers": len(drivers)}
    if setup is not None and probes:
        out["probes_after_setup_s"] = [round(min(probes) - setup, 3), round(max(probes) - setup, 3)]
        out["probe_spread_s"] = round(max(probes) - min(probes), 3)
    if probes and drivers:
        out["drivers_after_last_probe_s"] = [round(min(drivers) - max(probes), 3), round(max(drivers) - max(probes), 3)]
    if setup is not None and drivers:
        out["drivers_after_setup_s"] = [round(min(drivers) - setup, 3), round(max(drivers) - setup, 3)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="summarise the r49 claims lens's CI census")
    ap.add_argument("--census", required=True, help="the census output directory")
    ap.add_argument("--builder-runs", required=True, help="the builder's runs_all.json (its run list)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cdir = Path(args.census)
    with (cdir / "unit_jobs.json").open(encoding="utf-8") as fh:
        unit_jobs = json.load(fh)
    with (cdir / "runs_all.json").open(encoding="utf-8") as fh:
        runs = {r["id"]: r for r in json.load(fh)}
    with open(args.builder_runs, encoding="utf-8") as fh:
        builder_runs_raw = json.load(fh)
    builder_runs = builder_runs_raw if isinstance(builder_runs_raw, list) else builder_runs_raw.get("runs", builder_runs_raw.get("workflow_runs", []))
    builder_ids = {int(r["id"]) for r in builder_runs}
    builder_state = {int(r["id"]): (r.get("conclusion"), int(r.get("run_attempt", 1)), r.get("status")) for r in builder_runs}

    digests = {}
    for path in (cdir / "digests").glob("*.json"):
        with path.open(encoding="utf-8") as fh:
            digests[int(path.stem)] = json.load(fh)

    health = []
    for job in unit_jobs:
        d = digests.get(job["id"])
        if not d:
            continue
        named = [t for t in d.get("failed_tests", []) if TEST in t]
        if d.get("latencies") or named:
            row = {
                "run_id": job["run_id"], "attempt": job["attempt"], "job_id": job["id"], "job": job["name"], "job_conclusion": job["conclusion"],
                "event": job["run_event"], "branch": job["head_branch"], "head_sha": job["head_sha"], "run_created_at": job["run_created_at"],
                "python": d.get("python"), "image": d.get("image"), "image_version": d.get("image_version"), "latencies": d.get("latencies"),
                "health_summary_lines": named, "other_failed_tests": [t for t in d.get("failed_tests", []) if TEST not in t], "pytest_summary": d.get("summary"),
                "in_builder_run_list": job["run_id"] in builder_ids,
            }
            log = cdir / "logs" / f"{job['id']}.log"
            if log.exists():
                row["timeline"] = timeline(log.read_text(encoding="utf-8", errors="replace"))
            health.append(row)
    health.sort(key=lambda r: r["run_created_at"])

    def ran(job: dict) -> bool:
        return job["conclusion"] in ("success", "failure")

    in_list = [j for j in unit_jobs if j["run_id"] in builder_ids]
    selected = {rid for rid, (concl, att, _st) in builder_state.items() if concl == "failure" or att > 1}
    sel_jobs = [j for j in in_list if j["run_id"] in selected]
    failed_all = [j for j in unit_jobs if j["conclusion"] == "failure"]
    failed_in_list = [j for j in in_list if j["conclusion"] == "failure"]
    outside = [j for j in failed_in_list if j["run_id"] not in selected]
    py315 = [j for j in unit_jobs if "Python 3.15" in j["name"]]
    py315_rows = []
    for j in py315:
        d = digests.get(j["id"], {})
        py315_rows.append({"job_id": j["id"], "run_id": j["run_id"], "attempt": j["attempt"], "conclusion": j["conclusion"], "summary": d.get("summary"), "python": d.get("python"), "health_failed": bool(d.get("latencies") or [t for t in d.get("failed_tests", []) if TEST in t]), "failed_tests": d.get("failed_tests"), "note": d.get("error") or d.get("skipped")})

    report = {
        "census_runs_listed": len(runs),
        "census_unit_lane_jobs": len(unit_jobs),
        "health_failures": health,
        "health_failure_count": len(health),
        "builder_run_list": {
            "runs": len(builder_ids),
            "selected_runs_failure_or_rerun": len(selected),
            "unit_lane_jobs_in_selected": len(sel_jobs),
            "failed_unit_lane_jobs_in_selected": sum(1 for j in sel_jobs if j["conclusion"] == "failure"),
            "failed_unit_lane_jobs_all_attempts_in_list": len(failed_in_list),
            "failed_unit_lane_jobs_outside_selection": [{"job_id": j["id"], "run_id": j["run_id"], "attempt": j["attempt"], "name": j["name"], "branch": j["head_branch"], "event": j["run_event"], "run_conclusion_now": runs.get(j["run_id"], {}).get("conclusion"), "failed_tests": digests.get(j["id"], {}).get("failed_tests")} for j in outside],
            "unit_jobs_ran_main": sum(1 for j in in_list if ran(j) and j["head_branch"] == "main" and j["run_event"] != "pull_request"),
            "unit_jobs_ran_not_main": sum(1 for j in in_list if ran(j) and not (j["head_branch"] == "main" and j["run_event"] != "pull_request")),
            "unit_jobs_ran_total": sum(1 for j in in_list if ran(j)),
            "unit_jobs_ran_by_event": {e: sum(1 for j in in_list if ran(j) and j["run_event"] == e) for e in sorted({j["run_event"] for j in in_list})},
            # The builder's denominator read only runs whose conclusion (in its listing) was success or failure.
            "unit_jobs_ran_in_runs_concluded_success_or_failure_per_builder_listing": {
                "runs": sum(1 for rid, (concl, _a, _s) in builder_state.items() if concl in ("success", "failure")),
                "main": sum(1 for j in in_list if ran(j) and builder_state[j["run_id"]][0] in ("success", "failure") and j["head_branch"] == "main"),
                "not_main": sum(1 for j in in_list if ran(j) and builder_state[j["run_id"]][0] in ("success", "failure") and j["head_branch"] != "main"),
            },
            "unit_jobs_ran_by_builder_run_conclusion": {str(c): {"main": sum(1 for j in in_list if ran(j) and builder_state[j["run_id"]][0] == c and j["head_branch"] == "main"), "not_main": sum(1 for j in in_list if ran(j) and builder_state[j["run_id"]][0] == c and j["head_branch"] != "main")} for c in sorted({str(v[0]) for v in builder_state.values()})},
        },
        "all_failed_unit_lane_jobs_now": len(failed_all),
        # A job whose log GET answered 404: did its unit-test step ever run? (steps from the jobs listing)
        "log_404_jobs": {
            "count": sum(1 for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", ""))),
            "unit_step_conclusions": {
                str(c): sum(1 for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", "")) and str(next((s["conclusion"] for s in j.get("steps", []) if s["name"] == "Run Unit Tests with Coverage Gate"), "no-step")) == c)
                for c in sorted({str(next((s["conclusion"] for s in j.get("steps", []) if s["name"] == "Run Unit Tests with Coverage Gate"), "no-step")) for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", ""))})
            },
            "job_conclusions": {
                str(c): sum(1 for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", "")) and str(j["conclusion"]) == c)
                for c in sorted({str(j["conclusion"]) for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", ""))})
            },
            "with_any_step": sum(1 for j in unit_jobs if "404" in str(digests.get(j["id"], {}).get("error", "")) and j.get("steps")),
        },
        "all_runs_now_unit_jobs_ran": {"runs": len(runs), "main": sum(1 for j in unit_jobs if ran(j) and j["head_branch"] == "main"), "not_main": sum(1 for j in unit_jobs if ran(j) and j["head_branch"] != "main"), "total": sum(1 for j in unit_jobs if ran(j))},
        "runs_after_builder_list": sorted(({"id": r["id"], "created_at": r["created_at"], "event": r["event"], "branch": r["head_branch"], "status": r["status"], "conclusion": r["conclusion"]} for r in runs.values() if r["id"] not in builder_ids), key=lambda r: r["created_at"]),
        "py315_jobs": {"count": len(py315), "health_failed": sum(1 for r in py315_rows if r["health_failed"]), "with_pytest_summary": sum(1 for r in py315_rows if r["summary"]), "by_conclusion": {c: sum(1 for r in py315_rows if r["conclusion"] == c) for c in sorted({str(r["conclusion"]) for r in py315_rows})}, "rows": py315_rows},
    }
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("census_runs_listed", "census_unit_lane_jobs", "health_failure_count", "all_failed_unit_lane_jobs_now")}, indent=1))
    print(json.dumps(report["builder_run_list"], indent=1))
    print(json.dumps({k: v for k, v in report["py315_jobs"].items() if k != "rows"}, indent=1))
    for h in health:
        print(json.dumps({k: h[k] for k in ("run_id", "attempt", "job_id", "event", "branch", "python", "image", "image_version", "latencies", "other_failed_tests", "in_builder_run_list")}))
        print("   timeline", json.dumps(h.get("timeline")))
    print("runs after the builder's list:", json.dumps(report["runs_after_builder_list"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
