"""
Assemble manifest.json and stamps.json for round 3 of the juniper-cascor N-3 carrier from the records its other
helpers wrote.

manifest.json is built from, under the carrier worktree's tmp/flood4-fix/n3-r3/: the worktree's own status and file
hashes, runs/*.json (each pytest lane: command, interpreter, exit status, JUnit counts), mutants/results-all.json,
merge/merge_report.json and manifest_extras.json (hand-written: static checks, sweeps, what changed this round, open
questions). Every check names its exact command and exit status; nothing is recorded that no file shows.

stamps.json lists every version / date stamp line of the docs the carrier changes, as the base commit has it and as
the carrier has it, read from the files themselves, with the rule for re-deriving them on a later main.

Usage: python <this> manifest | stamps

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
D = CARRIER / "tmp" / "flood4-fix" / "n3-r3"

STAMP = re.compile(r"\*\*(Version|Document Version|Last Updated|Date|Version covered|Compiled)\*\*: ")
DOCS = ["CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET.md", "docs/api/API_SCHEMAS.md", "docs/api/JUNIPER_CASCOR_API_REFERENCE.md"]


def load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(CARRIER), *args], check=True, capture_output=True, text=True).stdout


def changed_files() -> list:
    rows = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        code, rel = line[:2], line[3:]
        if rel.startswith("tmp/"):
            continue
        status = {"??": "added", " M": "modified", "M ": "modified", " D": "deleted", "A ": "added"}.get(code, code.strip())
        digest = hashlib.sha256((CARRIER / rel).read_bytes()).hexdigest() if status != "deleted" else None
        rows.append({"path": rel, "status": status, "sha256": digest})
    return sorted(rows, key=lambda r: r["path"])


def stamp_lines(text: str) -> list:
    return [(number, line) for number, line in enumerate(text.splitlines(), 1) if STAMP.search(line) and line.startswith("**")]


def stamps() -> int:
    extras = load(D / "manifest_extras.json")
    head = git("rev-parse", "HEAD").strip()
    sites = []
    for rel in DOCS:
        base = stamp_lines(git("show", f"HEAD:{rel}"))
        now = stamp_lines((CARRIER / rel).read_text(encoding="utf-8"))
        if len(base) != len(now):
            raise SystemExit(f"{rel}: {len(base)} stamp lines at the base, {len(now)} in the carrier")
        for (base_no, base_line), (now_no, now_line) in zip(base, now):
            sites.append({"file": rel, "line_at_base": base_no, "line_in_carrier": now_no, "main_at_base": base_line, "carrier": now_line, "changed": base_line != now_line})
    out = {"base_sha": head, "utc_date_used": extras["stamps"]["utc_date_used"], "sites": sites, **{k: v for k, v in extras["stamps"].items() if k != "utc_date_used"}}
    with open(D / "stamps.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    for site in sites:
        print(("CHANGED " if site["changed"] else "kept    ") + f"{site['file']}:{site['line_in_carrier']}  {site['main_at_base']!r} -> {site['carrier']!r}")
    return 0


def manifest() -> int:
    extras = load(D / "manifest_extras.json")
    files = changed_files()
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
                "load_average_end": r.get("load_average_end"),
                "coverage_gate_exit_status": r.get("coverage_gate_exit_status"),
                "log": r["log"],
            }
        )
    checks.extend(extras["static_checks"])
    mut = load(D / "mutants" / "results-all.json")
    final_sha = {f["path"]: f["sha256"] for f in files}
    tested_equals_final = {path: final_sha.get(path) == digest for path, digest in mut["carrier_sha256"].items()}
    mutations = []
    for name, m in mut["mutants"].items():
        mutations.append(
            {
                "test_file": "src/tests/unit/api/test_websocket_resume_continuity.py (+ the five other WebSocket test files)",
                "mutant": name,
                "finding": m["finding"],
                "why": m["why"],
                "result": "killed" if m["killed"] else "survived",
                "failed": m["failed"],
                "of": m["tests"],
                "failed_in_the_new_file": m["failed_in_the_new_file"],
                "round3_tests_failing": m["round3_tests_failed"],
                "mutated_sha256_differs_from_carrier": m["mutated_sha256_differs_from_carrier"],
                "restored_sha256_verified": m["restored_sha256_verified"],
                "log": m["log"],
            }
        )
    phase_keys = ("sources", "exit_status", "tests", "failed", "failed_in_the_new_file", "round3_tests_failed", "log")
    out = {
        "status": extras["status"],
        "repo": "pcalnon/juniper-cascor",
        "carrier": "n3-r3 (round 3 of fix N-3: /ws/training resume losses; record section 8, ruling 11)",
        "base_sha": git("rev-parse", "HEAD").strip(),
        "worktree": str(CARRIER),
        "branch": extras["branch"],
        "files": files,
        "carried": [],
        "carried_note": 'No Cursor draft: a defect fix the Overtoad ruled in section 8, ruling 11 ("Fix all four now").',
        "changed_this_round": extras["changed_this_round"],
        "rebuild": {**extras["rebuild"], "merge_report": load(D / "merge" / "merge_report.json")},
        "phases": {k: {kk: v[kk] for kk in phase_keys} for k, v in mut["phases"].items()},
        "checks": checks,
        "mutations": mutations,
        "stale_pycache_dirs_deleted_before_the_mutant_run": mut["stale_pycache_dirs_deleted"],
        "carrier_unchanged_during_mutant_run": mut["carrier_sha256_unchanged"],
        "scratch_src_status_after_mutant_run": mut["scratch_src_status_after_restore"],
        "py_files_mutant_run_tested_equal_final_files": tested_equals_final,
        "facts": extras["facts"],
        "helper_scripts": extras["helper_scripts"],
        "open_questions": extras["open_questions"],
    }
    with open(D / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(f"manifest: {len(files)} files, {len(checks)} checks, {len(mutations)} mutants -> {D / 'manifest.json'}")
    print("py files the mutant run tested equal the final files:", all(tested_equals_final.values()), tested_equals_final)
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("manifest", "stamps"):
        raise SystemExit("usage: manifest | stamps")
    return manifest() if sys.argv[1] == "manifest" else stamps()


if __name__ == "__main__":
    sys.exit(main())
