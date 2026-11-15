#!/usr/bin/env python3
"""
Write the manifest.json of round 2 of the flood-4 "ml-tests" carrier from the build's own records.

Round 2 was built twice: by a builder that was stopped before its final manifest (base 26ea0ecb), and then again
on a newer main from that builder's verified tree. Nothing in the manifest is typed here. It is assembled from
files the two builds wrote as they went (all under --scratch):

  files       this worktree's change list (`status`), each path hashed now (sha256), with HOW it is built:
              the predecessor's label (copied | three-way | re-derived | round-2) for a path it recorded, or
              `session-7` for a helper the finishing session changed or added (files_s7.json, with a note). The
              landing tool reads `how`: `re-derived` is left at main's copy for the tools, anything else is copied
              or merged three-way. Each row also says how the file relates to the predecessor's last record
              (from_p2/copy_tree_final_bytes.json): identical bytes, re-derived to identical bytes, re-derived to
              different bytes (main changed the file), or changed / new in the finishing session;
  carried     carried_input.json, the 18 drafts; each entry's number, head and title are compared with the live
              state saved today (gh_pr_state.json), and a draft that is not open, not a draft or whose head or
              title moved fails the run;
  mutations   the predecessor's 40 rows (from_p2/manifest.json, from_p2/mutation_results.json). A row listed in
              mutation_rerun/rerun_rows.json was run again here, in a copy, and carries that run's result; every
              other row is KEPT, and says whether its test file and its target have the bytes the predecessor
              mutated (sha256 of both, compared with the predecessor's records);
  derived, checks, open_questions, if_main_moves      derived.json and the *_input.json files, as written.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py --scratch tmp/flood4r2/ml-tests/r2 [--status final]
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py --scratch tmp/flood4r2/ml-tests/r2 --verify

Exit 0 when the manifest was written, every carried draft is open, a draft, and at its recorded head, and no
kept mutant's bytes moved. --verify writes nothing: it compares every file with the sha256 the manifest holds and
the change list with the manifest's paths.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_manifest.py (round 1's)
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _load(path: Path, default=None):
    if not path.is_file():
        if default is None:
            raise SystemExit(f"missing input: {path}")
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _git(*argv: str) -> str:
    return subprocess.run(["git", *argv], capture_output=True, text=True, check=True).stdout


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _changed() -> list:
    return [(entry[:2], entry[3:]) for entry in _git("status", "--porcelain", "--untracked-files=all", "-z").split("\0") if entry]


def _files(scratch: Path) -> list:
    predecessor = {row["path"]: row for row in _load(scratch / "from_p2" / "manifest.json")["files"]}
    record = {row["path"]: row["here"] for row in _load(scratch / "from_p2" / "copy_tree_final_bytes.json")["rows"]}
    session7 = _load(scratch / "files_s7.json", {})
    files = []
    for code, path in _changed():
        status = "modified" if "M" in code and _git("ls-tree", "--name-only", "HEAD", "--", path).strip() else "added"
        row = {"path": path, "status": status, "sha256": _sha(Path(path))}
        if path in session7:
            row["how"] = "session-7"
            row["note"] = session7[path]
            row["vs_predecessor"] = "changed in the finishing session" if path in record else "new in the finishing session"
        elif path in predecessor:
            row["how"] = predecessor[path]["how"]
            if predecessor[path].get("note"):
                row["note"] = predecessor[path]["note"]
            same = row["sha256"] == record.get(path)
            if row["how"] == "re-derived":
                row["vs_predecessor"] = "re-derived here by the tools; bytes identical to the predecessor's" if same else "re-derived here by the tools; differs from the predecessor's because main changed the file"
            elif same:
                row["vs_predecessor"] = "copied from the predecessor's tree; bytes identical"
            else:
                raise SystemExit(f"{path}: differs from the predecessor's record and is not in files_s7.json")
        else:
            raise SystemExit(f"{path}: changed, but neither in the predecessor's manifest nor in files_s7.json")
        files.append(row)
    return files


def _carried(scratch: Path) -> tuple:
    live = {row["number"]: row for row in _load(scratch / "gh_pr_state.json")}
    carried, stale = _load(scratch / "carried_input.json"), []
    for entry in carried:
        now = live.get(entry["pr"])
        if now is None:
            stale.append(f"#{entry['pr']}: not in the saved gh state")
            continue
        if now["state"] != "OPEN" or not now["isDraft"] or now["headRefOid"] != entry["head_sha"] or now["title"] != entry["title"]:
            stale.append(f"#{entry['pr']}: live state {now['state']} draft={now['isDraft']} head={now['headRefOid'][:10]} title={now['title']!r}")
        entry["live_state"] = {"state": now["state"], "is_draft": now["isDraft"], "updated_at": now["updatedAt"], "read_at": now.get("read_at")}
    return carried, stale


def _mutations(scratch: Path) -> tuple:
    record = {row["path"]: row["here"] for row in _load(scratch / "from_p2" / "copy_tree_final_bytes.json")["rows"]}
    theirs = _load(scratch / "from_p2" / "manifest.json")["mutations"]
    their_runs = _load(scratch / "from_p2" / "mutation_results.json")
    predecessor_scratch = _load(scratch / "verify_p2.json")["predecessor"] + "/"
    rerun_rows = _load(scratch / "mutation_rerun" / "rerun_rows.json", [])
    rerun = dict(zip(rerun_rows, _load(scratch / "mutation_rerun" / "mutation_results.json", [])))
    mutations, moved = [], []
    for index, (row, run) in enumerate(zip(theirs, their_runs)):
        out = {"row": index, "test_file": row["test_file"], "mutant": row["mutant"], "pr": row["pr"], "origin": row.get("origin"), "selection": row.get("selection")}
        if row.get("why"):
            out["why"] = row["why"]
        if index in rerun:
            mine = rerun[index]
            out.update(
                {
                    "session_7": "re-run in a copy of this carrier",
                    "result": mine.get("result"),
                    "restored_byte_for_byte": mine.get("mutant_restored"),
                    "target_sha256": mine.get("mutant_sha256_before"),
                    "log": mine.get("log"),
                    "predecessor_result": row["result"],
                }
            )
        else:
            test_sha, target_sha = _sha(Path(row["test_file"])), _sha(Path(run["target"]))
            unchanged = test_sha == record.get(row["test_file"]) and target_sha == run["mutant_sha256_before"]
            out.update(
                {
                    "session_7": "kept from the predecessor's run",
                    "result": row["result"],
                    "restored_byte_for_byte": row.get("restored_byte_for_byte"),
                    "test_file_sha256": test_sha,
                    "target_sha256": target_sha,
                    "bytes_unchanged_since_the_predecessors_run": unchanged,
                    "log": predecessor_scratch + row["log"],
                }
            )
            if row.get("control_on_mains_test_file"):
                out["control_on_mains_test_file"] = row["control_on_mains_test_file"]
            if not unchanged:
                moved.append(f"row {index}: {row['test_file']} / {run['target']}")
        mutations.append(out)
    return mutations, moved


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--status", default="final")
    ap.add_argument("--verify", action="store_true", help="write nothing: compare every file with the sha256 the manifest holds")
    args = ap.parse_args()
    scratch = Path(args.scratch)
    if args.verify:
        recorded = _load(scratch / "manifest.json")["files"]
        differing = [row["path"] for row in recorded if _sha(Path(row["path"])) != row["sha256"]]
        unlisted = sorted({path for _code, path in _changed()} - {row["path"] for row in recorded})
        print(f"{len(recorded)} manifest files; differing from the recorded sha256: {differing or 'none'}; changed but not in the manifest: {unlisted or 'none'}")
        return 1 if differing or unlisted else 0
    files = _files(scratch)
    carried, stale = _carried(scratch)
    mutations, moved = _mutations(scratch)
    verified = _load(scratch / "verify_p2.json")
    manifest = {
        "status": args.status,
        "repo": "juniper-ml",
        "carrier": "ml-tests",
        "round": 2,
        "base_sha": _git("rev-parse", "HEAD").strip(),
        "worktree": str(Path.cwd()),
        "predecessor": {"worktree": verified["predecessor"], "base_sha": verified["base"], "last_record": verified["last_record"], "verification": str(scratch / "verify_p2.json"), "round_1": _load(scratch / "from_p2" / "manifest.json")["predecessor"]},
        "derived": _load(scratch / "derived.json"),
        "files": files,
        "carried": carried,
        "checks": _load(scratch / "checks_input.json", []),
        "mutations": mutations,
        "open_questions": _load(scratch / "open_questions_input.json", []),
        "if_main_moves": _load(scratch / "if_main_moves_input.json", {}),
    }
    with open(scratch / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    killed = sum(1 for row in mutations if row["result"] == "killed")
    kept = sum(1 for row in mutations if row["session_7"].startswith("kept"))
    print(f"manifest ({args.status}): {len(files)} files, {len(carried)} carried drafts, {killed} of {len(mutations)} mutants killed ({kept} kept, {len(mutations) - kept} re-run), {len(manifest['checks'])} checks")
    if stale:
        print("DRAFT STATE DIFFERS:\n" + "\n".join(stale), file=sys.stderr)
    if moved:
        print("A KEPT MUTANT'S BYTES MOVED (re-run it):\n" + "\n".join(moved), file=sys.stderr)
    return 1 if stale or moved else 0


if __name__ == "__main__":
    sys.exit(main())
