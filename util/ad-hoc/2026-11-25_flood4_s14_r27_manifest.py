"""
Assemble builder r27's deliverables: final/ copies, paths.txt, final.sha256 and manifest.json, from the build tree and the run records.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects

Usage:
    python3 <this file> --r27 <builder dir> [--extra-json <json file with checks/open_questions to merge>]

Reads <r27>/clone (the build tree: its change set from git status), <r27>/base.txt, the run summaries under
<r27>/runs/, the census reports under <r27>/census/, the mutant records under <r27>/mutants/*/mutants.json and the flake
records under <r27>/flakes/*/flakes.json. Copies each changed file to <r27>/final/<path> (sha256-checked), writes
<r27>/paths.txt (one path per line), <r27>/final.sha256 (sha256sum format) and <r27>/manifest.json. A run summary that
is missing is recorded as missing, never invented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path


def git(tree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607 - fixed argv


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def run_record(r27: Path, label: str) -> dict:
    summary = load(r27 / "runs" / f"{label}.summary.json")
    if summary is None:
        return {"label": label, "missing": True}
    junit = summary.get("junit", {})
    census = summary.get("census", {})
    return {
        "label": label,
        "command": " ".join(summary["argv"][2:]),
        "runner": "python3 util/ad-hoc/2026-11-25_flood4_s14_r27_run_lane.py (prefixed with tmp/flood4/session14/runenv.bash)",
        "interpreter": summary["interpreter"],
        "versions": summary["versions"],
        "cwd": summary["cwd"],
        "started_utc": summary["started_utc"],
        "ended_utc": summary["ended_utc"],
        "exit_status": summary["exit"],
        "result_line": summary.get("result_line"),
        "junit": {key: junit.get(key) for key in ("tests", "failures", "errors", "skipped", "time", "testcase_elements")},
        "failed": junit.get("failed", []),
        "connects_by_port": {port: {key: slot[key] for key in ("connects", "distinct_tests", "distinct_files", "distinct_tests_by_phase", "hosts")} for port, slot in census.items()},
        "connects_to_guarded_ports_at_socket_level": summary.get("connects_to_guarded_ports_at_socket_level"),
        "guard_failed_reports": len(summary.get("guard_failed_reports", [])),
        "log": f"runs/{label}.log (junit runs/{label}.junit.xml, census runs/{label}.census.jsonl, summary runs/{label}.summary.json)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble builder r27's deliverables.")
    parser.add_argument("--r27", required=True, type=Path)
    parser.add_argument("--extra-json", type=Path, default=None)
    args = parser.parse_args()
    r27 = args.r27.resolve()
    tree = r27 / "clone"
    files = []
    final = r27 / "final"
    for line in git(tree, "status", "--porcelain", "--untracked-files=all").splitlines():
        code, path = line[:2], line[3:]
        status = "modified" if code.strip() == "M" else "added" if code == "??" else f"unexpected {code!r}"
        digest = sha256(tree / path)
        target = final / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tree / path, target)
        files.append({"path": path, "status": status, "sha256": digest, "final_copy_equal": sha256(target) == digest})
    files.sort(key=lambda entry: entry["path"])
    (r27 / "paths.txt").write_text("".join(f"{entry['path']}\n" for entry in files), encoding="utf-8")
    (r27 / "final.sha256").write_text("".join(f"{entry['sha256']}  {entry['path']}\n" for entry in files), encoding="utf-8")

    mutants = []
    for record in sorted((r27 / "mutants").glob("*/mutants.json")):
        data = load(record)
        for mutant in data["mutants"]:
            mutants.append({key: mutant.get(key) for key in ("id", "file", "what", "result", "restored", "sha256_before", "sha256_mutant", "sha256_after", "tests", "failures", "errors")} | {"killers": mutant.get("failed", []), "record": str(record.relative_to(r27))})
        mutants.append({"id": f"unmutated-after-restore ({record.parent.name})", "result": data["unmutated_after_restore"]})
    flakes = {}
    for record in sorted((r27 / "flakes").glob("*/flakes.json")):
        data = load(record)
        flakes[record.parent.name] = {key: data[key] for key in ("runs", "trees", "tests_seen", "focus_ids", "focus_missing_from_junit", "focus_all_passed_every_run", "not_always_passed", "guarded_port_connects_total", "guard_failed_reports_total")} | {"record": str(record.relative_to(r27))}

    manifest = {
        "repo": "pcalnon/juniper-canopy",
        "ruling": "the Overtoad's ruling 27 (2026-11-12, 'A follow-up PR (Recommended)'), notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8",
        "base_sha": (r27 / "base.txt").read_text(encoding="utf-8").strip(),
        "clone": str(tree),
        "branch": git(tree, "rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": git(tree, "rev-parse", "HEAD").strip(),
        "committed": "nothing: the change is an uncommitted tree on a local branch; nothing pushed",
        "files": files,
        "census_before": load(r27 / "census" / "before_8100.json"),
        "census_after": load(r27 / "census" / "after_8100.json"),
        "runs": {label: run_record(r27, label) for label in ("lane-before-py313-cov", "lane-after-py313-cov", "lane-before-py314", "lane-after-py314", "changed-files-v1")},
        "mutants": mutants,
        "flake_runs": flakes,
    }
    if args.extra_json:
        manifest |= load(args.extra_json)
    (r27 / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "all_final_copies_equal": all(entry["final_copy_equal"] for entry in files), "mutants": len(mutants), "flake_runs": list(flakes)}, indent=1))
    return 0 if all(entry["final_copy_equal"] for entry in files) else 1


if __name__ == "__main__":
    sys.exit(main())
