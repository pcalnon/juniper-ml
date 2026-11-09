"""
Assemble the flood-4 juniper-ml tests carrier's manifest.json from the build's own records.

Inputs, all under <scratch>: survey.json (draft heads, titles, own-diff files), tests/name_status.txt
(`git diff --cached --name-status origin/main`), mutation*/mutation_results.json, checks.json (the checks
run, written by hand from their logs) and decisions.json (per-draft fixes / drops, written by hand).
Output: <scratch>/tests/manifest.json in the brief's schema.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_manifest.py <scratch-dir> <worktree> <base-sha>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md (flood-4 consolidation)
"""

import json
import sys
from pathlib import Path

STATUS = {"A": "added", "M": "modified", "D": "deleted"}
SECTION_NAME = "'## Test Suite Reference'"


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    scratch, worktree, base = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    survey = _load(scratch / "survey.json")
    decisions = _load(scratch / "decisions.json")
    files = []
    for line in (scratch / "tests" / "name_status.txt").read_text(encoding="utf-8").splitlines():
        code, path = line.split("\t", 1)
        files.append({"path": path, "status": STATUS.get(code[0], code)})
    carried = []
    for p in survey["prs"]:
        d = decisions.get(str(p["pr"]), {})
        carried.append(
            {
                "pr": p["pr"],
                "head_sha": p["head"],
                "title": p["title"],
                "taken": d.get("taken") or [f"{row[2]} (+{row[0]}/-{row[1]}, own hunks via git apply --3way)" for row in p["numstat"]],
                "fixes": d.get("fixes", []),
                "dropped": d.get("dropped", []),
                "outcome": d.get("outcome", "carried"),
                "reason": d.get("reason", "own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant"),
            }
        )
    mutations = []
    for results in sorted(scratch.glob("mutation*/**/mutation_results.json")) + sorted(scratch.glob("mutation/mutation_results.json")):
        for r in _load(results):
            mutations.append(
                {
                    "pr": r["pr"],
                    "test_file": r["test_file"],
                    "mutant": f"{r['target']}: {r['old'].strip()!r} -> {r['new'].strip()!r}",
                    "result": r["result"],
                    "selection": r.get("selection"),
                    "baseline_rc": r.get("baseline_rc"),
                    "restored_sha256_match": r.get("restored"),
                    "log": r["log"],
                }
            )
    seen = set()
    unique = []
    for m in mutations:
        key = (m["pr"], m["test_file"], m["mutant"])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "tests",
        "base_sha": base,
        "worktree": worktree,
        "index_state": "every carrier path is staged in the worktree's index (git apply --3way implies --index); nothing is committed",
        "files": files,
        "carried": carried,
        "checks": _load(scratch / "checks.json"),
        "mutations": unique,
        "main_text_fixes": decisions.get("_main_text_fixes", []),
        "validation_fixes_outside_drafts": decisions.get("_validation_fixes_outside_drafts", []),
        "docs_handoff": decisions.get("_docs_handoff", {}),
        "open_questions": decisions.get("_open_questions", []),
    }
    for hunk in manifest["docs_handoff"].get("hunks", []):
        carried.append(
            {
                "pr": hunk["pr"],
                "head_sha": hunk["head_sha"],
                "title": f"docs draft #{hunk['pr']}: its {SECTION_NAME} hunk only (the docs carrier carries the rest)",
                "taken": [f"docs/REFERENCE.md {hunk['hunk']}"],
                "fixes": [hunk["fix"]],
                "dropped": ["the hunk's cross-link"],
                "outcome": hunk["outcome"],
                "reason": hunk["verified"],
            }
        )
    with open(scratch / "tests" / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"files={len(files)} carried={len(carried)} mutations={len(unique)} killed={sum(m['result'] == 'killed' for m in unique)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
