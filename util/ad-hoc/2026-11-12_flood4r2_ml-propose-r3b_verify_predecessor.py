#!/usr/bin/env python3
"""
Verify a dead builder's uncommitted carrier tree before anything is copied out of it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (finishing round 3 of the ml-propose carrier, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_mutation_check.py (the mutant lists, read from the
         predecessor's copy of it once that copy's sha256 equals its manifest's)

WHY THIS EXISTS
Round 3's builder was killed mid-task, and a kill between a mutation helper's "apply" and "restore" once left a
mutant in a carrier's source file. The carrier is uncommitted in the builder's worktree, and this session may not
run version-control commands there. So the tree is checked from here, by reading its files:

* every file the builder's last manifest lists, against the LAST sha256 it recorded: the manifest's, or the one
  in a sha256 file it wrote later (--later-record), reported side by side;
* the tree's status, re-derived without running anything in it: each path of the base commit is hashed as a blob
  from the predecessor's bytes and compared with the base's own blob id, and the files the base does not hold
  are listed (ignored ones dropped by asking THIS worktree's ignore rules). A path a checkout filter rewrites
  (a large-file pointer) never hashes to its blob, so it is compared with this worktree's checked-out bytes
  instead. The result must be the manifest's file list and nothing else;
* a leftover mutant: every mutant of the three mutation groups must still find its ``old`` text exactly once in
  the predecessor's propose.py, and no ``new`` text may be there unless it is part of the unmutated file;
* optional pairs ``--expect <path>=<sha256 prefix>`` for hashes recorded elsewhere (a progress log).

Read-only towards the predecessor's worktree. Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_verify_predecessor.py --predecessor <its worktree>
        --manifest <its manifest.json> --base <the sha it was built on> --out <json> [--expect <path>=<prefix>]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess  # nosec B404 - fixed argv: read-only plumbing in this script's own worktree
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R3_MUTATION_REL = "util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_mutation_check.py"
R2_MUTATION_REL = "util/ad-hoc/2026-11-08_flood4r2_ml-propose_mutation_check.py"
TARGET_REL = "util/release_train/propose.py"
#: Directory names never descended into when looking for files the base does not hold.
SKIP_DIRS = frozenset({".git", "tmp", "__pycache__", "node_modules", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache"})


def run(*args: str, stdin: "bytes | None" = None) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=ROOT, input=stdin, capture_output=True, check=False)  # nosec B603


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_id(data: bytes) -> str:
    """The object id the version-control system gives these bytes as a blob (sha1 of a typed, sized header)."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data, usedforsecurity=False).hexdigest()


def base_tree(base: str) -> dict:
    """path -> (mode, blob id) for every file of the base commit."""
    done = run("git", "ls-tree", "-r", "-z", base)
    if done.returncode != 0:
        raise SystemExit(done.stderr.decode("utf-8", "replace"))
    tree = {}
    for record in done.stdout.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        mode, kind, ident = meta.decode("ascii").split()
        if kind == "blob":
            tree[path.decode("utf-8")] = (mode, ident)
    return tree


def on_disk_blob(path: Path, mode: str) -> "str | None":
    """The blob id of ``path`` as it stands on disk (a link is hashed by its target text), or None when absent."""
    if mode == "120000":
        return blob_id(os.readlink(path).encode("utf-8")) if path.is_symlink() else None
    if not path.is_file():
        return None
    return blob_id(path.read_bytes())


def filtered_paths(paths: list) -> set:
    """The paths a checkout filter rewrites (large-file pointers): their bytes on disk are not their blob's."""
    if not paths:
        return set()
    done = run("git", "check-attr", "-z", "--stdin", "filter", stdin="\0".join(paths).encode("utf-8"))
    fields = done.stdout.split(b"\0")
    return {fields[i].decode("utf-8") for i in range(0, len(fields) - 2, 3) if fields[i + 2] not in (b"unspecified", b"unset")}


def status_without_running_anything_there(predecessor: Path, tree: dict, head_tree: dict) -> dict:
    modified, deleted = [], []
    for rel, (mode, ident) in tree.items():
        found = on_disk_blob(predecessor / rel, mode)
        if found is None:
            deleted.append(rel)
        elif found != ident:
            modified.append(rel)
    # A filtered path never hashes to its blob. Where this worktree's HEAD still holds the base's blob for it,
    # this worktree's checked-out bytes ARE the base's, so the predecessor's bytes are compared with those.
    filtered = filtered_paths(modified)
    same_as_here = {rel for rel in filtered if head_tree.get(rel) == tree[rel] and (ROOT / rel).is_file() and (ROOT / rel).read_bytes() == (predecessor / rel).read_bytes()}
    modified = [rel for rel in modified if rel not in same_as_here]
    extra = []
    for folder, dirs, files in os.walk(predecessor):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in files:
            rel = (Path(folder) / name).relative_to(predecessor).as_posix()
            if rel not in tree and rel != ".git":
                extra.append(rel)
    ignored = set()
    if extra:
        done = run("git", "check-ignore", "-z", "--stdin", "--no-index", stdin="\0".join(extra).encode("utf-8"))
        ignored = {item.decode("utf-8") for item in done.stdout.split(b"\0") if item}
    return {
        "modified": sorted(modified),
        "deleted": sorted(deleted),
        "added": sorted(set(extra) - ignored),
        "ignored_and_dropped": len(ignored),
        "filtered_paths_compared_with_this_worktrees_bytes": len(filtered),
        "of_which_identical": len(same_as_here),
    }


def mutant_groups(script: Path) -> list:
    """(group, id, old, new) for round 2's, the final check's and the live-control mutants, read from round 3's script."""
    spec = importlib.util.spec_from_file_location("flood4r2_ml_propose_r3_mutation_check", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    carrier_mutants, _selection = module.r2_mutants()
    rows = [("r2", ident, old, new) for ident, _what, old, new in carrier_mutants]
    rows += [("own", ident, old, new) for ident, _what, old, new in module.OWN_MUTANTS]
    rows += [("live", ident, old, new) for ident, _what, old, new in module.LIVE_MUTANTS]
    return rows


def leftover_mutants(text: str, script: Path) -> dict:
    rows = mutant_groups(script)
    not_once = [{"group": group, "id": ident, "old_occurrences": text.count(old)} for group, ident, old, _new in rows if text.count(old) != 1]
    applied = []
    for group, ident, old, new in rows:
        # A mutant is "applied" when its new text is present where the old text is not. ``new`` may be a
        # substring of the unmutated file (a shortened line), so presence alone proves nothing.
        if text.count(old) == 0 and new and new in text:
            applied.append({"group": group, "id": ident})
    return {"mutants_checked": len(rows), "old_text_not_exactly_once": not_once, "applied": applied}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--predecessor", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expect", action="append", default=[], metavar="PATH=SHA256_PREFIX")
    parser.add_argument("--later-record", type=Path, help="a `<sha256>  <path>` file the predecessor wrote AFTER its manifest: where it names a path, it is that path's last recorded hash")
    parser.add_argument("--write-verified-manifest", type=Path, help="when everything holds, write the file list with each file's last recorded sha256: the --manifest the assemble helper is given")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    later = {}
    if args.later_record is not None:
        for line in args.later_record.read_text(encoding="utf-8").splitlines():
            digest, _, rel = line.partition("  ")
            if rel:
                later[rel.strip()] = digest.strip()
    files = []
    for entry in manifest["files"]:
        path = args.predecessor / entry["path"]
        data = path.read_bytes() if path.is_file() else None
        last = later.get(entry["path"], entry.get("sha256"))
        files.append(
            {
                "path": entry["path"],
                "status": entry["status"],
                "manifest_sha256": entry.get("sha256"),
                "last_recorded_sha256": last,
                "last_record_is": "the later record" if entry["path"] in later else "the manifest",
                "sha256": sha256(data) if data is not None else None,
                "matches_manifest": data is not None and sha256(data) == entry.get("sha256"),
                "matches_last_record": data is not None and sha256(data) == last,
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if data is not None else None,
            }
        )
    by_path = {row["path"]: row for row in files}
    expected = []
    for item in args.expect:
        rel, _, prefix = item.partition("=")
        found = by_path.get(rel, {}).get("sha256") or ""
        expected.append({"path": rel, "recorded_prefix": prefix, "sha256": found, "matches": bool(prefix) and found.startswith(prefix)})

    status = status_without_running_anything_there(args.predecessor, base_tree(args.base), base_tree("HEAD"))
    listed = {"modified": sorted(r["path"] for r in files if r["status"] == "modified"), "added": sorted(r["path"] for r in files if r["status"] == "added"), "deleted": sorted(r["path"] for r in files if r["status"] == "deleted")}
    status_equals_manifest = all(status[key] == listed[key] for key in ("modified", "added", "deleted"))
    # The mutant lists are read from the predecessor's own two mutation scripts, and only once both are shown
    # to be the files its manifest recorded: nothing of an unverified file is executed.
    scripts_verified = all(by_path.get(rel, {}).get("matches_last_record") for rel in (R3_MUTATION_REL, R2_MUTATION_REL))
    if scripts_verified:
        mutants = leftover_mutants((args.predecessor / TARGET_REL).read_text(encoding="utf-8"), args.predecessor / R3_MUTATION_REL)
    else:
        mutants = {"mutants_checked": 0, "old_text_not_exactly_once": ["NOT RUN: a mutation script does not match the manifest"], "applied": []}

    report = {
        "predecessor": str(args.predecessor),
        "manifest": str(args.manifest),
        "manifest_status": manifest.get("status"),
        "manifest_base_sha": manifest.get("base_sha"),
        "base": args.base,
        "later_record": str(args.later_record) if args.later_record is not None else None,
        "files": files,
        "every_file_matches_the_manifest": all(row["matches_manifest"] for row in files),
        "files_that_differ_from_the_manifest": [row["path"] for row in files if not row["matches_manifest"]],
        "every_file_matches_its_last_recorded_sha256": all(row["matches_last_record"] for row in files),
        "expected_elsewhere": expected,
        "status_rederived": status,
        "status_equals_the_manifest_file_list": status_equals_manifest,
        "leftover_mutants": mutants,
    }
    report["ok"] = report["every_file_matches_its_last_recorded_sha256"] and all(row["matches"] for row in expected) and status_equals_manifest and not mutants["old_text_not_exactly_once"] and not mutants["applied"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["ok"] and args.write_verified_manifest is not None:
        verified = {
            "note": "The predecessor's file list, each file with the LAST sha256 the predecessor recorded for it, all verified against its bytes on disk. Written by this script; the predecessor's own manifest.json is not modified.",
            "source_manifest": str(args.manifest),
            "later_record": str(args.later_record) if args.later_record is not None else None,
            "base_sha": manifest.get("base_sha"),
            "worktree": str(args.predecessor),
            "files": [{"path": row["path"], "status": row["status"], "sha256": row["last_recorded_sha256"], "last_record_is": row["last_record_is"]} for row in files],
        }
        args.write_verified_manifest.write_text(json.dumps(verified, indent=2) + "\n", encoding="utf-8")
    for row in files:
        verdict = "ok      " if row["matches_manifest"] else ("ok-LATER" if row["matches_last_record"] else "MISMATCH")
        print(verdict, row["path"], (row["sha256"] or "ABSENT")[:12], "manifest", (row["manifest_sha256"] or "")[:12], "last", (row["last_recorded_sha256"] or "")[:12], row["mtime_utc"])
    print("status re-derived:", {key: len(value) if isinstance(value, list) else value for key, value in status.items()}, "equals the manifest's list:", status_equals_manifest)
    print("leftover mutants:", {"checked": mutants["mutants_checked"], "old_text_not_exactly_once": mutants["old_text_not_exactly_once"], "applied": mutants["applied"]})
    print("expected elsewhere:", expected)
    print("OK" if report["ok"] else "NOT OK")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
