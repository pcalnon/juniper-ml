"""
Assemble manifest.json for the owner-ruling-17 canopy fix and check its deliverables.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy lockfile-update.yml

Reads the uncommitted tree in ``--worktree`` and the scratch directory ``--scratch`` (its
harness, mutants, logs and text deliverables), hashes every changed file and deliverable,
checks the CHANGELOG entry's placement (verbatim, under the top ``[Unreleased]`` /
``### Fixed``, below an existing entry), the body rules (no CI-skip marker, no trailer in
the commit body, a ``## Requirements`` section) and, read-only, that every ``#N`` the PR
body cites exists in juniper-canopy. Static facts (commands run, open questions) come from
``--facts`` (a JSON file). Writes ``<scratch>/manifest.json``; exit 1 if a check fails.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_manifest.py --worktree <canopy worktree> \
        --scratch <worktree>/tmp/flood4-fix/r17-canopy-lockfile-print --base-sha <sha> --facts <facts.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - read-only gh api GETs
import sys
from pathlib import Path

FILES = [
    ".github/workflows/lockfile-update.yml",
    "CHANGELOG.md",
    "docs/ci_cd/CICD_MANUAL.md",
    "docs/ci_cd/CICD_QUICK_START.md",
    "docs/ci_cd/CICD_REFERENCE.md",
    "src/tests/regression/test_lockfile_regen_empty_payload.py",
]
DELIVERABLES = ["pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt"]
SKIP_MARKERS = re.compile(r"\[(skip ci|ci skip|no ci|skip actions|actions skip)\]|skip-checks\s*:", re.IGNORECASE)
TRAILER = re.compile(r"^[A-Z][A-Za-z-]+: .+$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changelog_placement(changelog: str, entry: str) -> dict:
    lines = changelog.splitlines()
    tops = [i for i, line in enumerate(lines) if line.startswith("## [")]
    unreleased = tops[0] if tops and lines[tops[0]].startswith("## [Unreleased]") else None
    next_release = tops[1] if len(tops) > 1 else len(lines)
    position = changelog.find(entry)
    found = position >= 0 and changelog.count(entry) == 1
    entry_line = changelog[:position].count("\n") if found else None
    fixed = next((i for i in range(unreleased or 0, next_release) if lines[i] == "### Fixed"), None) if unreleased is not None else None
    section_end = next((i for i in range((fixed or 0) + 1, next_release) if lines[i].startswith("### ")), next_release) if fixed is not None else None
    entries_above = sum(1 for i in range((fixed or 0) + 1, entry_line or 0) if lines[i].startswith("- **")) if found and fixed is not None else 0
    ok = bool(found and unreleased is not None and fixed is not None and fixed < entry_line < section_end and entries_above >= 1)
    return {"found_once_verbatim": found, "top_heading": lines[tops[0]] if tops else None, "entry_line": (entry_line + 1) if found else None, "fixed_heading_line": (fixed + 1) if fixed is not None else None, "section_end_line": (section_end + 1) if section_end is not None else None, "entries_above_in_subsection": entries_above, "ok": ok}


def cited_prs_exist(body: str) -> dict:
    numbers = sorted({int(n) for n in re.findall(r"juniper-canopy#(\d+)", body)} | {int(n) for n in re.findall(r"(?<![\w-])#(\d+)\b", body)})
    result = {}
    for number in numbers:
        proc = subprocess.run(["gh", "api", "-X", "GET", f"repos/pcalnon/juniper-canopy/issues/{number}", "--jq", ".number"], capture_output=True, text=True, check=False, timeout=60)  # nosec B603 B607 - read-only GET
        result[str(number)] = proc.returncode == 0 and proc.stdout.strip() == str(number)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--facts", type=Path, required=True)
    args = parser.parse_args()
    with args.facts.open(encoding="utf-8") as fh:
        facts = json.load(fh)
    scratch = args.scratch
    texts = {name: (scratch / name).read_text(encoding="utf-8") for name in DELIVERABLES}
    changelog = (args.worktree / "CHANGELOG.md").read_text(encoding="utf-8")
    placement = changelog_placement(changelog, texts["changelog_entry.txt"])
    with (scratch / "harness" / "harness_results.json").open(encoding="utf-8") as fh:
        harness = json.load(fh)
    with (scratch / "mutants" / "mutants.json").open(encoding="utf-8") as fh:
        mutants = json.load(fh)
    deliverable_checks = {
        "changelog_entry_placement": placement,
        "pr_title_one_line": texts["pr_title.txt"].count("\n") == 1,
        "no_ci_skip_marker": not any(SKIP_MARKERS.search(texts[name]) for name in DELIVERABLES),
        "commit_body_has_no_trailers": not any(TRAILER.match(line) for line in texts["commit_body.txt"].splitlines()[-3:]),
        "pr_body_has_requirements_section": "## Requirements" in texts["pr_body.txt"],
        "pr_body_cites_ruling_17": "ruling 17 (2026-11-09, recorded in the record-update PR)" in texts["pr_body.txt"],
        "cited_canopy_numbers_exist": cited_prs_exist(texts["pr_body.txt"] + texts["changelog_entry.txt"]),
    }
    failures = [k for k, v in deliverable_checks.items() if v is False]
    if not placement["ok"]:
        failures.append("changelog placement")
    if not all(deliverable_checks["cited_canopy_numbers_exist"].values()):
        failures.append("a cited number does not exist")
    manifest = {
        "repo": "juniper-canopy",
        "carrier": "r17-canopy-lockfile-print",
        "ruling": facts["ruling"],
        "base_sha": args.base_sha,
        "worktree": str(args.worktree),
        "branch": facts["branch"],
        "files": [{"path": p, "status": "modified", "sha256": sha256(args.worktree / p)} for p in FILES],
        "carried": [],
        "carried_note": facts["carried_note"],
        "fix": facts["fix"],
        "checks": facts["checks"],
        "harness_summary": {
            "failures": harness["failures"],
            "success_path_identity": harness["success_path_identity"],
            "host_temp_paths_created": [p for p, now in harness["host_temp_paths_exist_after_run"].items() if now and not harness["host_temp_paths_existed_before_run"][p]],
            "real_gh": harness["real_gh"],
            "step_temp_paths_after": harness["step_temp_paths"]["all_under_dir_after"],
        },
        "mutations": [
            {"test_file": "src/tests/regression/test_lockfile_regen_empty_payload.py", "mutant": f".github/workflows/lockfile-update.yml: {row['what']}", "id": row["id"], "result": "killed" if row.get("killed") else "survived", "failed_tests": row["failed"], "restored_sha256_matches": row.get("restored_sha256_matches"), "log": row["log"]}
            for row in mutants["results"]
            if row["id"] != "baseline-fixed"
        ],
        "mutation_restore": {"original_sha256": mutants["original_sha256"], "final_sha256": mutants["final_sha256"]},
        "deliverables": {name: sha256(scratch / name) for name in DELIVERABLES},
        "deliverable_checks": deliverable_checks,
        "helper_scripts": facts["helper_scripts"],
        "open_questions": facts["open_questions"],
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(deliverable_checks, indent=2))
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
