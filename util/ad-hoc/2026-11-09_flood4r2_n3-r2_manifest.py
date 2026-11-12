"""
Assemble manifest.json for the juniper-cascor N-3 round-2 carrier from the run records the other n3-r2 helpers wrote.

Reads, under the carrier worktree's tmp/flood4-fix/n3-r2/: hashes_final.json (files and sha256), runs/*.json (each
pytest lane: command, interpreter, exit status, JUnit counts), mutants/results-all.json, merge_simulation.json and
manifest_extras.json (hand-written: rebase record, static checks and sweeps, open questions). Every
check in the manifest names its exact command and exit status; nothing is recorded that no file shows.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import json
import sys
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
D = CARRIER / "tmp" / "flood4-fix" / "n3-r2"


def load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    hashes = load(D / "hashes_final.json")
    extras = load(D / "manifest_extras.json")
    checks = []
    for run in sorted((D / "runs").glob("*.json")):
        r = load(run)
        c = r["counts"]
        checks.append(
            {
                "what": r["label"],
                "command": f"(cwd {r['tree']}) {r['command']}",
                "interpreter": r["interpreter"],
                "exit_status": r["exit_status"],
                "result": "pass" if r["exit_status"] == 0 else "fail",
                "counts": {k: c.get(k) for k in ("tests", "passed", "failures", "errors", "skipped")},
                "failed_ids": c.get("failed_ids", []),
                "seconds": r["seconds"],
                "coverage_gate_exit_status": r.get("coverage_gate_exit_status"),
                "log": r["log"],
            }
        )
    checks.extend(extras["static_checks"])
    mut = load(D / "mutants" / "results-all.json")
    final_sha = {f["path"]: f["sha256"] for f in hashes["files"]}
    tested_equals_final = {path: final_sha.get(path) == sha for path, sha in mut["carrier_sha256"].items()}
    mutations = []
    for name, m in mut["mutants"].items():
        mutations.append({"test_file": "src/tests/unit/api/test_websocket_resume_continuity.py (+ the five other WebSocket test files)", "mutant": name, "finding": m["finding"], "why": m["why"], "result": "killed" if m["killed"] else "survived", "failed": m["failed"], "of": m["tests"], "round2_tests_failing": m["round2_tests_failed"], "restored_sha256_verified": m["restored_sha256_verified"], "log": m["log"]})
    manifest = {
        "repo": "pcalnon/juniper-cascor",
        "carrier": "n3-r2 (round-2 fix-up of N-3: /ws/training resume losses; record section 8, ruling 11)",
        "base_sha": hashes["base"],
        "worktree": str(CARRIER),
        "branch": "fix/ws-resume-losses (local only; fast-forwarded f3dfee8c -> base_sha, never pushed)",
        "files": hashes["files"],
        "carried": [],
        "carried_note": "No Cursor draft: a defect fix the owner ruled in section 8, ruling 11 (\"Fix all four now\").",
        "rebase": extras["rebase"],
        "phases": {k: {kk: v[kk] for kk in ("sources", "exit_status", "tests", "failed", "round2_tests_failed", "log")} for k, v in mut["phases"].items()},
        "checks": checks,
        "mutations": mutations,
        "carrier_unchanged_during_mutant_run": mut["carrier_sha256_unchanged"],
        "py_files_mutant_run_tested_equal_final_files": tested_equals_final,
        "merge_simulation": str(D / "merge_simulation.json"),
        "codeql_bare_await": extras["codeql_bare_await"],
        "helper_scripts": extras["helper_scripts"],
        "open_questions": extras["open_questions"],
    }
    with open(D / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print(f"manifest: {len(manifest['files'])} files, {len(checks)} checks, {len(mutations)} mutants -> {D / 'manifest.json'}")
    print("py files the mutant run tested equal the final files:", all(tested_equals_final.values()), tested_equals_final)
    return 0


if __name__ == "__main__":
    sys.exit(main())
