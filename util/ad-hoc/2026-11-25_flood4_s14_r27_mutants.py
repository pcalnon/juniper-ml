"""
Seam mutants for ruling 27: mutate canopy's REAL probe / readiness / degraded-mode code and record which unit tests kill each.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage:
    python3 <this file> --tree <canopy tree WITH the r27 change> --python <interpreter> --out <dir> --paths <test paths...> [--only ID ...]

Each mutant is ONE exact replacement in one source file of the tree (the old text must occur exactly once). For each:
the file's sha256 is taken, the mutant written, the named tests run through
2026-11-25_flood4_s14_r27_run_lane.py --mode files (behind the r27 connect fence, CI's selector, CI's step variables),
and the file is restored byte for byte in a `finally:` and its sha256 compared with the one taken before. A mutant is
killed when at least one test fails or errors; the failing ids are its killers. A last run on the restored tree must
pass. Writes <dir>/mutants.json (and each run's files under <dir>/runs/).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_LANE = HERE / "2026-11-25_flood4_s14_r27_run_lane.py"

MUTANTS = [
    {
        "id": "M1-readiness-verdict-inverted",
        "file": "src/main.py",
        "what": "/v1/health/ready degrades when a dependency is NOT unhealthy (the readiness decision inverted)",
        "old": '        if dep.status == "unhealthy":\n            overall = "degraded"',
        "new": '        if dep.status != "unhealthy":\n            overall = "degraded"',
    },
    {
        "id": "M2-probe-error-mapping-dropped",
        "file": "src/health.py",
        "what": "probe_dependency no longer maps a transport error to an unhealthy status: it propagates",
        "old": "    except Exception as e:  # noqa: BLE001",
        "new": "    except ValueError as e:  # noqa: BLE001",
    },
    {
        "id": "M3-probe-any-status-healthy",
        "file": "src/health.py",
        "what": "probe_dependency calls any answered HTTP status healthy (the non-200 mapping dropped)",
        "old": "        if response.status_code == 200:",
        "new": "        if response.status_code < 600:",
    },
    {
        "id": "M4-probe-message-drops-the-error-type",
        "file": "src/health.py",
        "what": "the unhealthy message no longer names the exception type",
        "old": '            message=f"{url} — {type(e).__name__}: {e}",',
        "new": '            message=f"{url} — {e}",',
    },
    {
        "id": "M5-startup-decision-inverted",
        "file": "src/main.py",
        "what": "the lifespan marks juniper-data available when its probe is NOT healthy",
        "old": '    if data_probe.status == "healthy":\n        juniper_data_available = True',
        "new": '    if data_probe.status != "healthy":\n        juniper_data_available = True',
    },
    {
        "id": "M6-startup-probe-skipped",
        "file": "src/main.py",
        "what": "the lifespan assumes juniper-data healthy without probing it",
        "old": "    data_probe = await probe_dependency(\"JuniperData\", f\"{juniper_data_url.rstrip('/')}/v1/health/live\")",
        "new": '    data_probe = DependencyStatus(name="JuniperData", status="healthy", latency_ms=0.0, message=juniper_data_url)',
    },
    {
        "id": "M7-readiness-probes-the-wrong-path",
        "file": "src/main.py",
        "what": "/v1/health/ready probes juniper-data's /v1/health instead of /v1/health/live",
        "old": "    data_dep = await probe_dependency(\"JuniperData Service\", f\"{data_url.rstrip('/')}/v1/health/live\")",
        "new": "    data_dep = await probe_dependency(\"JuniperData Service\", f\"{data_url.rstrip('/')}/v1/health\")",
    },
    {
        "id": "M8-generators-outage-not-flagged",
        "file": "src/main.py",
        "what": "the generators proxy no longer flags a juniper-data that stopped answering (canopy#653's unknown state lost)",
        "old": '            system_logger.debug("Failed to fetch generators from JuniperData: %s", e)\n            upstream_unavailable = True',
        "new": '            system_logger.debug("Failed to fetch generators from JuniperData: %s", e)\n            upstream_unavailable = False',
    },
    {
        "id": "G1-fake-never-answers",
        "file": "src/tests/conftest.py",
        "what": "the r27 juniper-data fake answers nothing (every :8100 request goes to the real transport): the guard must then refuse and FAIL each test that reaches :8100 (the revert check: the fake is needed, and the guard catches every connect it would otherwise let through)",
        "old": "        return _SERVICE_PORT_GUARD.armed_for is not None and request.url.port == self.port",
        "new": "        return False",
    },
    {
        "id": "M9-generators-proxy-ignores-the-list",
        "file": "src/main.py",
        "what": "the generators proxy drops the list juniper-data answers with and serves the built-ins",
        "old": "                    if isinstance(data, list):\n                        generators = data",
        "new": "                    if isinstance(data, list):\n                        generators = []",
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, label: str) -> dict:
    argv = [sys.executable, str(RUN_LANE), "--tree", str(args.tree), "--python", args.python, "--label", label, "--out", str(args.out / "runs"), "--mode", "files", "--paths", *args.paths]
    subprocess.run(argv, check=False, capture_output=True, text=True)  # nosec B603 - fixed argv
    summary = json.loads((args.out / "runs" / f"{label}.summary.json").read_text(encoding="utf-8"))
    junit = summary.get("junit", {})
    return {"exit": summary["exit"], "tests": junit.get("tests"), "failures": junit.get("failures"), "errors": junit.get("errors"), "failed": [entry["id"] for entry in junit.get("failed", [])], "guarded_port_connects": summary.get("connects_to_guarded_ports_at_socket_level"), "guard_failed_reports": len(summary.get("guard_failed_reports", [])), "result_line": summary.get("result_line")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Seam mutants for ruling 27.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args()
    args.tree, args.out = args.tree.resolve(), args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for mutant in MUTANTS:
        if args.only and mutant["id"] not in args.only:
            continue
        path = args.tree / mutant["file"]
        original = path.read_bytes()
        before = sha256(path)
        text = original.decode("utf-8")
        occurrences = text.count(mutant["old"])
        record = {key: mutant[key] for key in ("id", "file", "what")} | {"old_occurrences": occurrences, "sha256_before": before}
        if occurrences != 1:
            record["result"] = "NOT APPLIED (old text must occur exactly once)"
            results.append(record)
            continue
        try:
            path.write_text(text.replace(mutant["old"], mutant["new"]), encoding="utf-8")
            record["sha256_mutant"] = sha256(path)
            outcome = run(args, f"mut-{mutant['id']}")
        finally:
            path.write_bytes(original)
        record["sha256_after"] = sha256(path)
        record["restored"] = record["sha256_after"] == before
        record |= outcome
        record["result"] = "killed" if outcome["failed"] else "SURVIVED"
        results.append(record)
        print(json.dumps({key: record[key] for key in ("id", "result", "restored", "tests", "failures", "errors")} | {"killers": record["failed"][:12]}), flush=True)
    final = run(args, "mut-unmutated-after-restore")
    report = {"tree": str(args.tree), "interpreter": args.python, "paths": args.paths, "mutants": results, "unmutated_after_restore": final}
    (args.out / "mutants.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"unmutated_after_restore": {key: final[key] for key in ("exit", "tests", "failures", "errors", "result_line")}}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
