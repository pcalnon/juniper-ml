"""
Assemble each D-14 carrier's manifest.json for the fix-up round from the run records, hashing every file as it is now.

Per carrier: the changed and untracked paths (``git status --porcelain --untracked-files=all``, ``tmp/`` skipped) with
their status and sha256, read when this runs (a juniper-ml path under ``util/ad-hoc/`` is listed as a provenance
helper); then the records: ``manifest_static.json`` (repo, base, worktree, checks, the review findings and how each
was answered, open questions, what stays different, census, landing order), the stamps check (its sites split by
repository), the pinned pre-commit record, the screens, and the mutant results of the groups that belong to the
carrier (service-core and drift-gate arms to juniper-ml, cascor arms to juniper-cascor).

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_manifest.py --ml <juniper-ml carrier> --cascor <juniper-cascor carrier>
        --mutants <dir holding svc_a.json svc_b.json eco.json cascor.json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table);
    util/ad-hoc/2026-11-15_flood4r2_d14_manifest.py (round 1's assembler)
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SCRATCH = Path("tmp/flood4-fix/d14-resume")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def changed(repo: Path) -> list[dict]:
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in status.splitlines():
        code, path = line[:2].strip(), line[3:]
        if path.startswith("tmp/"):
            continue
        state = {"??": "added", "A": "added", "M": "modified", "D": "deleted"}.get(code, code)
        digest = hashlib.sha256((repo / path).read_bytes()).hexdigest() if state != "deleted" else None
        rows.append({"path": path, "status": state, "sha256": digest})
    return sorted(rows, key=lambda row: row["path"])


def arms(mutants: Path, names: tuple) -> tuple[list, dict]:
    rows, baselines = [], {}
    for name in names:
        report = load(mutants / f"{name}.json")
        baselines[name] = {"root": report["root"], "baseline_sha256": report["baseline_sha256"], "runs": [{key: run[key] for key in ("command", "exit", "seconds", "log")} for run in report["baselines"]]}
        for arm in report["arms"]:
            rows.append({"arm": arm["arm"], "source": arm["source"], "what": arm["what"], "result": arm["result"], "killed_by": arm["killed_by"], "restored": arm["restored"], "logs": [run["log"] for run in arm["runs"]]})
    return rows, baselines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--ml", type=Path, required=True)
    parser.add_argument("--cascor", type=Path, required=True)
    parser.add_argument("--mutants", type=Path, required=True)
    args = parser.parse_args()
    ml_scratch = args.ml / SCRATCH
    stamps = load(ml_scratch / "stamps_check.json")
    precommit = load(ml_scratch / "logs" / "precommit.json")
    screens = load(ml_scratch / "logs" / "screens.json")
    for name, repo, groups in (("juniper-ml", args.ml, ("svc_a", "svc_b", "eco")), ("juniper-cascor", args.cascor, ("cascor",))):
        scratch = repo / SCRATCH
        static = load(scratch / "manifest_static.json")
        files = changed(repo)
        mutation_rows, baselines = arms(args.mutants, groups)
        manifest = {
            **{key: static[key] for key in ("repo", "carrier", "round", "base_sha", "worktree")},
            **({"round1_worktree": static["round1_worktree"]} if "round1_worktree" in static else {}),
            "files": [row for row in files if not row["path"].startswith("util/ad-hoc/")],
            "provenance_helpers": [row for row in files if row["path"].startswith("util/ad-hoc/")],
            "carried": [],
            "review_findings": static["review_findings"],
            "checks": static["checks"],
            "screens": {key: {"exit": screens[key]["exit"], "tail": screens[key]["output"][-300:]} for key in ("G-PATH", "G-TMP", "CodeQL prescreen")} if name == "juniper-ml" else "the CodeQL prescreen of juniper-ml's screens.json covers this carrier's .py (1 predicted: the module-level pytestmark)",
            "precommit": precommit[name],
            "mutations": mutation_rows,
            "mutation_summary": {"arms": len(mutation_rows), "killed": sum(1 for row in mutation_rows if row["result"] == "killed"), "all_restored": all(row["restored"] for row in mutation_rows)},
            "mutation_baselines": baselines,
            "stamps": {"ok": stamps["ok"], "derived": stamps["derived"], "sites": [site for site in stamps["sites"] if site["repo"].startswith("juniper-cascor") == (name == "juniper-cascor")]},
            "consumer_census": static["consumer_census"],
            "landing_order": static["landing_order"],
            "what_stays_different": static["what_stays_different"],
            "open_questions": static["open_questions"],
        }
        (scratch / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        print(f"{name}: {len(manifest['files'])} carrier files, {len(manifest['provenance_helpers'])} helpers, {manifest['mutation_summary']} -> {scratch / 'manifest.json'}")


if __name__ == "__main__":
    main()
