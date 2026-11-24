"""
Assemble the D-14 carriers onto the validator's own worktrees of today's mains (copies; carriers stay read-only).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --out <json path>
juniper-ml: every manifest file and provenance helper is copied over (main has not moved any of them since the
carrier's base; the script re-checks that with `git diff --quiet <base> <main> -- <paths>` in the orchestrator
worktree, which shares the object store). juniper-cascor: a file main moved since the carrier's base is rebuilt
three-way (`git merge-file -p <carrier> <base> <main>`); the others are copied. Writes the sha256 of every
assembled file to --out.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ORCHESTRATOR = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
ML_CARRIER = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
ML_COPY = JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-d14-code--20261115-1554--edea2eb1"
CASCOR_PRIMARY = JUNIPER / "juniper-cascor"
CASCOR_CARRIER = JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d"
CASCOR_COPY = JUNIPER / "worktrees" / "juniper-cascor--val--flood4r2-d14-code--20261115-1554--67588488"
ML_MAIN = "edea2eb16700aa0a712cfbaeea7a7e2291aac1e7"
CASCOR_MAIN = "675884888f5a5d6b906842cbf1bf7071cdc3dafe"


def sha256_of(path: Path) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=120, check=False)


def manifest(root: Path) -> dict:
    with open(root / "tmp" / "flood4-fix" / "d14-resume" / "manifest.json", encoding="utf-8") as handle:
        return json.load(handle)


def assemble_ml(report: dict) -> None:
    data = manifest(ML_CARRIER)
    paths = [entry["path"] for entry in data["files"]] + [entry["path"] for entry in data["provenance_helpers"]]
    moved = git(["diff", "--quiet", data["base_sha"], ML_MAIN, "--", *paths], ORCHESTRATOR)
    report["ml"] = {"base": data["base_sha"], "main": ML_MAIN, "main_moved_any_file": moved.returncode != 0, "files": {}}
    if moved.returncode != 0:
        raise SystemExit("juniper-ml main moved a carrier file since the base: rebuild three-way first")
    for rel in paths:
        target = ML_COPY / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ML_CARRIER / rel, target)
        report["ml"]["files"][rel] = {"how": "copied", "sha256": sha256_of(target), "carrier_sha256": sha256_of(ML_CARRIER / rel)}


def assemble_cascor(report: dict) -> None:
    data = manifest(CASCOR_CARRIER)
    base = git(["rev-parse", "HEAD"], CASCOR_CARRIER).stdout.strip()
    report["cascor"] = {"base": base, "main": CASCOR_MAIN, "files": {}}
    for entry in data["files"]:
        rel = entry["path"]
        target = CASCOR_COPY / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        moved = git(["diff", "--quiet", base, CASCOR_MAIN, "--", rel], CASCOR_PRIMARY).returncode != 0
        if entry["status"] == "added" or not moved:
            shutil.copyfile(CASCOR_CARRIER / rel, target)
            how = "copied"
        else:
            base_text = git(["show", f"{base}:{rel}"], CASCOR_PRIMARY)
            scratch_base = ORCHESTRATOR / "tmp" / "flood4r2-val" / "d14-code-lens" / "assemble" / (rel.replace("/", "__") + ".base")
            scratch_base.parent.mkdir(parents=True, exist_ok=True)
            with open(scratch_base, "w", encoding="utf-8") as handle:
                handle.write(base_text.stdout)
            merged = git(["merge-file", "-p", str(CASCOR_CARRIER / rel), str(scratch_base), str(target)], CASCOR_COPY)
            if merged.returncode != 0:
                raise SystemExit(f"three-way rebuild of {rel} conflicted ({merged.returncode} conflicts)")
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(merged.stdout)
            how = "three-way"
        report["cascor"]["files"][rel] = {"how": how, "sha256": sha256_of(target), "carrier_sha256": sha256_of(CASCOR_CARRIER / rel)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report: dict = {}
    assemble_ml(report)
    assemble_cascor(report)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    for repo in ("ml", "cascor"):
        for rel, row in report[repo]["files"].items():
            print(f"{repo}\t{row['how']}\t{row['sha256'][:16]}\t{rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
