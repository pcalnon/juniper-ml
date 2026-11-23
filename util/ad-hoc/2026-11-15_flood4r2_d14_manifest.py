"""
Assemble each D-14 carrier's manifest.json from the run records, so its file list and hashes are read, not retyped.

Inputs (all written earlier in the arc): ``screens.json`` (every changed file of both carriers, status and sha256,
and the G-PATH / G-TMP / CodeQL prescreen results), ``mutation_results.json``, ``consumer_census.json``,
``landing_order.json``, ``precommit.json``, ``stamps_check.json``, and one ``manifest_static.json`` per carrier
(repo, base, worktree, checks, open questions, what stays different), which this merges with them. A juniper-ml
path under ``util/ad-hoc/`` is listed as a provenance helper, apart from the carrier's files.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import json
from pathlib import Path


def load(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def census_summary(census: list) -> list:
    rows = []
    for repo in census:
        if "families" not in repo:
            rows.append({"repo": repo["repo"], "error": repo.get("error")})
            continue
        row = {"repo": repo["repo"], "origin_main": repo["origin_main"][:8]}
        for family, found in repo["families"].items():
            code = sorted({hit["path"] for hit in found.get("lines", []) if not hit["support"]})
            row[family] = {"lines": found.get("hits"), "files_outside_tests_util_scripts_notes_docs": code}
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--scratch-ml", type=Path, required=True)
    parser.add_argument("--scratch-cascor", type=Path, required=True)
    args = parser.parse_args()
    screens = load(args.scratch_ml / "logs" / "screens.json")
    mutations = load(args.scratch_ml / "mut" / "mutation_results.json")
    census = census_summary(load(args.scratch_ml / "census" / "consumer_census.json"))
    landing = load(args.scratch_ml / "logs" / "landing_order.json")
    precommit = load(args.scratch_ml / "logs" / "precommit.json")
    stamps = load(args.scratch_ml / "stamps_check.json")
    arms = [{"arm": arm["arm"], "copy": arm["copy"], "test_file_or_target": arm["file"], "mutant": arm["what"], "result": arm["result"], "failed": arm["failed"], "log": arm["log"], "sha256_after_restore": arm["sha256_after"]} for arm in mutations["arms"]]
    for name, scratch, files_key, arm_copies in (("juniper-ml", args.scratch_ml, "juniper-ml", ("svc", "eco")), ("juniper-cascor", args.scratch_cascor, "juniper-cascor", ("cascor",))):
        static = load(scratch / "manifest_static.json")
        files = screens[files_key]
        manifest = {
            **{key: static[key] for key in ("repo", "carrier", "base_sha", "worktree")},
            "files": [item for item in files if not item["path"].startswith("util/ad-hoc/")],
            "provenance_helpers": [item for item in files if item["path"].startswith("util/ad-hoc/")],
            "carried": [],
            "checks": static["checks"],
            "screens": {key: {"command": screens[key]["command"][-300:], "exit": screens[key]["exit"], "tail": screens[key]["output"][-400:]} for key in ("G-PATH", "G-TMP", "CodeQL prescreen")},
            "precommit": precommit[files_key],
            "mutations": [arm for arm in arms if arm["copy"] in arm_copies],
            "mutation_baselines": {copy: mutations["baselines"][copy] for copy in arm_copies},
            "consumer_census": census,
            "landing_order": landing,
            "stamps": {"ok": stamps["ok"], "derived": stamps["derived"], "sites": [site for site in stamps["sites"] if (site["repo"].startswith("juniper-cascor")) == (name == "juniper-cascor")]},
            "what_stays_different": static["what_stays_different"],
            "open_questions": static["open_questions"],
        }
        with open(scratch / "manifest.json", "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=1)
            handle.write("\n")
        print(f"{name}: {len(manifest['files'])} carrier files, {len(manifest['provenance_helpers'])} helpers, {len(manifest['mutations'])} mutants -> {scratch / 'manifest.json'}")


if __name__ == "__main__":
    main()
