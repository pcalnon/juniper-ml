"""
Assemble the N-3 round-3 quick validator's own trees and check the rebuild on current main.

Three detached juniper-cascor worktrees at origin/main must already exist (the validator created them with plain
``git worktree add --detach``): COPY (gets the carrier's 11 changed files), MAIN (left pristine: the control) and R2SRC
(gets round 2's three source files, so "round 2's behaviour" can be driven on today's main). This script:

1. hashes the carrier's 11 files, copies them into COPY and checks the copies are byte-identical;
2. checks the builder's round-2 snapshot against round 2's own manifest hashes (the tree two lenses validated) and
   copies round 2's three source files into R2SRC;
3. for every carrier file, compares 7640d420 (round 2's base) with 9f632eac (round 3's base) to learn whether main
   changed it, and
   - where main changed it: re-runs the three-way rebuild (``git merge-file -p <round 2> <7640d420> <9f632eac>``) and
     records what the carrier's file differs from that by (round 3's own hand edits), plus the direct question "is
     every line main added since 7640d420 still in the carrier's file?";
   - where main did not: records round 2 -> round 3 as a unified diff.

Nothing is written into the carrier. Diffs land in the validator's scratch directory for reading.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses (N-3 round 3)
"""

import collections
import difflib
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
PRIMARY = JUNIPER / "juniper-cascor"
CARRIER = WORKTREES / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
COPY = WORKTREES / "juniper-cascor--val--n3-r3-quick--20261111-1958--9f632eac"
MAIN = WORKTREES / "juniper-cascor--val--n3-r3-quick-main--20261111-1958--9f632eac"
R2SRC = WORKTREES / "juniper-cascor--val--n3-r3-quick-r2src--20261111-1958--9f632eac"
SCRATCH = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r3-quick-s5"
R2_SNAPSHOT = CARRIER / "tmp" / "flood4-fix" / "n3-r3" / "snapshots" / "r2"
R2_HASHES = CARRIER / "tmp" / "flood4-fix" / "n3-r2" / "hashes_final.json"
R2_BASE = "7640d420be43f56df21375c11e0315cb11facc08"
R3_BASE = "9f632eaca3b93bdc547869aad9a0354208ed4076"

FILES = [
    "CHANGELOG.md",
    "docs/DEVELOPER_CHEATSHEET.md",
    "docs/api/API_SCHEMAS.md",
    "docs/api/JUNIPER_CASCOR_API_REFERENCE.md",
    "src/api/observability.py",
    "src/api/websocket/manager.py",
    "src/api/websocket/training_stream.py",
    "src/tests/unit/api/test_metrics_obs_wire_02.py",
    "src/tests/unit/api/test_training_stream_coverage.py",
    "src/tests/unit/api/test_websocket_manager.py",
    "src/tests/unit/api/test_websocket_resume_continuity.py",
]
R2_SOURCES = ["src/api/observability.py", "src/api/websocket/manager.py", "src/api/websocket/training_stream.py"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(sha: str, rel: str):
    """The file's text at a commit, or None when the commit has no such file."""
    proc = subprocess.run(["git", "-C", str(PRIMARY), "show", f"{sha}:{rel}"], capture_output=True)
    return proc.stdout.decode("utf-8") if proc.returncode == 0 else None


def unified(a: str, b: str, a_name: str, b_name: str) -> str:
    return "".join(difflib.unified_diff(a.splitlines(keepends=True), b.splitlines(keepends=True), a_name, b_name, n=2))


def main() -> int:
    out = {"r2_base": R2_BASE, "r3_base": R3_BASE, "copy": str(COPY), "main": str(MAIN), "r2src": str(R2SRC), "files": {}}
    heads = {}
    for tree in (CARRIER, COPY, MAIN, R2SRC):
        heads[tree.name] = subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out["heads"] = heads

    r2_manifest = {f["path"]: f["sha256"] for f in json.loads(R2_HASHES.read_text(encoding="utf-8"))["files"]}
    work = SCRATCH / "rebuild"
    work.mkdir(parents=True, exist_ok=True)

    for rel in FILES:
        src = CARRIER / rel
        before = sha256(src)
        dst = COPY / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        rec = {"carrier_sha256": before, "copy_identical": sha256(dst) == before and sha256(src) == before}

        snap = R2_SNAPSHOT / rel
        rec["r2_snapshot_matches_r2_manifest"] = sha256(snap) == r2_manifest[rel]
        r2_text = snap.read_text(encoding="utf-8")
        carrier_text = src.read_text(encoding="utf-8")
        base_text = blob(R2_BASE, rel)
        main_text = blob(R3_BASE, rel)
        rec["on_main"] = main_text is not None
        rec["main_changed_since_r2_base"] = base_text != main_text
        safe = rel.replace("/", "__")

        if rec["on_main"] and rec["main_changed_since_r2_base"]:
            paths = {}
            for tag, text in (("r2", r2_text), ("base", base_text), ("main", main_text)):
                paths[tag] = work / f"{safe}.{tag}"
                paths[tag].write_text(text, encoding="utf-8")
            merged = subprocess.run(["git", "merge-file", "-p", str(paths["r2"]), str(paths["base"]), str(paths["main"])], capture_output=True)
            merged_text = merged.stdout.decode("utf-8")
            rec["merge_file_exit"] = merged.returncode
            (work / f"{safe}.merged").write_text(merged_text, encoding="utf-8")
            residual = unified(merged_text, carrier_text, "three-way-rebuild", "carrier")
            (work / f"{safe}.rebuild-to-carrier.diff").write_text(residual, encoding="utf-8")
            rec["rebuild_to_carrier_changed_lines"] = sum(1 for ln in residual.splitlines() if ln[:1] in "+-" and ln[:3] not in ("+++", "---"))
            # The direct question: every line main ADDED since round 2's base must still be in the carrier's file.
            added = collections.Counter(main_text.splitlines()) - collections.Counter(base_text.splitlines())
            missing = added - collections.Counter(carrier_text.splitlines())
            rec["main_added_lines"] = sum(added.values())
            rec["main_added_lines_missing_from_carrier"] = sorted(missing.elements())
            # And every line main REMOVED must not have come back (unless round 2 itself adds it).
            removed = collections.Counter(base_text.splitlines()) - collections.Counter(main_text.splitlines())
            back = (collections.Counter(carrier_text.splitlines()) - collections.Counter(main_text.splitlines())) & removed
            rec["main_removed_lines_back_in_carrier"] = sorted(back.elements())
            (work / f"{safe}.main-to-carrier.diff").write_text(unified(main_text, carrier_text, "main-9f632eac", "carrier"), encoding="utf-8")
        else:
            (work / f"{safe}.r2-to-carrier.diff").write_text(unified(r2_text, carrier_text, "round-2", "carrier"), encoding="utf-8")
            if main_text is not None:
                (work / f"{safe}.main-to-carrier.diff").write_text(unified(main_text, carrier_text, "main-9f632eac", "carrier"), encoding="utf-8")
        out["files"][rel] = rec

    for rel in R2_SOURCES:
        shutil.copyfile(R2_SNAPSHOT / rel, R2SRC / rel)
        out["files"][rel]["r2src_matches_r2_manifest"] = sha256(R2SRC / rel) == r2_manifest[rel]

    (SCRATCH / "setup.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
