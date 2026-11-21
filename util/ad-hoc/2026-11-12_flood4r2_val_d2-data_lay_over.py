#!/usr/bin/env python3
"""
Validator helper for juniper-data's "run the unrun tests" carrier: verify the carrier's bytes, lay its paths over a
tree of the validator's own, and rebuild three-way the files that main changed since the carrier's base.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (checks A and G), juniper-data#537 (what main
         gained after the carrier was built)

Verbs (the carrier is only ever READ: files are hashed and copied out of it, and git is asked for its status):

  verify-carrier --carrier <C> --hashes <sha256_final.txt> --manifest <manifest.json> --repo <primary> --out <json>
      Every file the hash list names is re-hashed in the carrier; `status --porcelain` there must name exactly the
      manifest's paths with the manifest's statuses; a deleted path must be absent and its base blob must hash to
      the manifest's value.

  lay-base --carrier <C> --hashes <sha256_final.txt> --manifest <manifest.json> --target <V0> --expect-head <sha>
      Copies each path over a tree whose HEAD is the carrier's base (a delete stays a delete), re-hashing each copy.

  merge --carrier <C> --manifest <manifest.json> --repo <primary> --base <sha> --main <sha> --out <dir>
      For each path: if main's blob equals the base's, the carrier's copy is taken as it is. Otherwise the three
      copies are written under <dir>/three_way/ and `git merge-file -p <carrier> <base> <main>` writes
      <dir>/three_way/<path>.merged; its exit status (the number of conflicts) is recorded. Nothing is resolved here.

  stamp --in <merged file> --out <file> --old <main's version> --new <main's version + one step> --date <stamp date>
      Sets the document stamp by rule: exactly two ``**Version:**`` lines (header and footer) must carry main's
      value and exactly two ``**Last Updated:**`` lines the landing date; the new value must not occur anywhere.

  land --carrier <C> --manifest <manifest.json> --plan <dir>/merge_plan.json --rebuilt <dir of complete rebuilt
       files, by repo path> --target <V1> --expect-head <sha>
      Applies the plan to a tree at today's main: carrier copies for the untouched paths, deletes for the deletes,
      and the validator's resolved copy for every path the plan says main changed. Refuses a rebuilt file that
      still holds a conflict marker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFLICT_MARKS = ("<<<<<<< ", ">>>>>>> ", "||||||| ", "\n=======\n")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)


def read_hashes(path: Path) -> dict[str, str]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            table[name.strip()] = digest
    return table


def manifest_files(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["files"]


def porcelain(repo: Path) -> dict[str, str]:
    done = git(repo, "status", "--porcelain", "--untracked-files=all")
    table = {}
    for line in done.stdout.decode("utf-8").splitlines():
        table[line[3:]] = line[:2]
    return table


def blob(repo: Path, rev: str, path: str) -> bytes | None:
    done = git(repo, "cat-file", "-p", f"{rev}:{path}")
    return done.stdout if done.returncode == 0 else None


def blob_id(repo: Path, rev: str, path: str) -> str | None:
    done = git(repo, "rev-parse", "--verify", "--quiet", f"{rev}:{path}")
    return done.stdout.decode().strip() if done.returncode == 0 else None


def verb_verify_carrier(ns: argparse.Namespace) -> int:
    carrier = Path(ns.carrier)
    hashes = read_hashes(Path(ns.hashes))
    files = manifest_files(Path(ns.manifest))
    base = json.loads(Path(ns.manifest).read_text(encoding="utf-8"))["base_sha"]
    problems = []
    rows = []
    for name, digest in sorted(hashes.items()):
        found = sha256_of(carrier / name) if (carrier / name).is_file() else None
        rows.append({"path": name, "recorded": digest, "found": found, "match": found == digest})
        if found != digest:
            problems.append(f"hash differs: {name}")
    status = porcelain(carrier)
    want = {"modified": " M", "deleted": " D", "added": "??"}
    manifest_status = {entry["path"]: want[entry["status"]] for entry in files}
    if status != manifest_status:
        problems.append(f"status differs from the manifest: only in status {sorted(set(status) - set(manifest_status))}, only in manifest {sorted(set(manifest_status) - set(status))}, flag mismatches {sorted(p for p in set(status) & set(manifest_status) if status[p] != manifest_status[p])}")
    for entry in files:
        if entry["status"] == "deleted":
            data = blob(Path(ns.repo), base, entry["path"])
            digest = hashlib.sha256(data).hexdigest() if data is not None else None
            if (carrier / entry["path"]).exists() or digest != entry.get("sha256_of_main_blob"):
                problems.append(f"deleted path not as recorded: {entry['path']}")
        elif entry["path"] not in hashes:
            problems.append(f"manifest path without a recorded hash: {entry['path']}")
        elif hashes[entry["path"]] != entry["sha256"]:
            problems.append(f"manifest hash differs from the hash list: {entry['path']}")
    head = git(carrier, "rev-parse", "HEAD").stdout.decode().strip()
    staged = git(carrier, "diff", "--cached", "--name-only").stdout.decode().split()
    report = {"carrier": str(carrier), "head": head, "base_sha": base, "head_is_base": head == base, "staged": staged, "status_paths": len(status), "manifest_paths": len(files), "hash_rows": rows, "problems": problems}
    Path(ns.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"carrier HEAD {head} (base {base}); status paths {len(status)}; manifest paths {len(files)}; hashed files {len(rows)}; matching {sum(1 for r in rows if r['match'])}; staged {len(staged)}; problems {len(problems)}")
    for problem in problems:
        print("PROBLEM:", problem)
    return 1 if problems or head != base or staged else 0


def copy_checked(source: Path, target: Path, digest: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha256_of(target) != digest:
        raise SystemExit(f"copy of {source} does not hash to {digest}")


def verb_lay_base(ns: argparse.Namespace) -> int:
    carrier, target = Path(ns.carrier), Path(ns.target)
    head = git(target, "rev-parse", "HEAD").stdout.decode().strip()
    if head != ns.expect_head:
        raise SystemExit(f"target HEAD is {head}, expected {ns.expect_head}")
    hashes = read_hashes(Path(ns.hashes))
    for entry in manifest_files(Path(ns.manifest)):
        if entry["status"] == "deleted":
            (target / entry["path"]).unlink(missing_ok=True)
        else:
            copy_checked(carrier / entry["path"], target / entry["path"], hashes[entry["path"]])
    api_dir = target / "juniper_data" / "tests" / "api"
    leftovers = sorted(p.name for p in api_dir.iterdir()) if api_dir.is_dir() else None
    status = porcelain(target)
    print(f"laid {len(manifest_files(Path(ns.manifest)))} paths over {target.name}; status now names {len(status)} paths; tests/api leftovers: {leftovers}")
    for name, flags in sorted(status.items()):
        print(f"  {flags} {name}")
    return 0


def verb_merge(ns: argparse.Namespace) -> int:
    carrier, repo, out = Path(ns.carrier), Path(ns.repo), Path(ns.out)
    work = out / "three_way"
    plan = []
    for entry in manifest_files(Path(ns.manifest)):
        path = entry["path"]
        base_id, main_id = blob_id(repo, ns.base, path), blob_id(repo, ns.main, path)
        row = {"path": path, "carrier_status": entry["status"], "base_blob": base_id, "main_blob": main_id, "main_changed": base_id != main_id}
        if base_id == main_id:
            row["action"] = "delete" if entry["status"] == "deleted" else "take the carrier's copy"
        elif entry["status"] == "deleted" or base_id is None or main_id is None:
            row["action"] = "FINDING: main changed a path the carrier deletes or adds"
        else:
            stem = work / path
            stem.parent.mkdir(parents=True, exist_ok=True)
            names = {"carrier": stem.with_name(stem.name + ".carrier"), "base": stem.with_name(stem.name + ".base"), "main": stem.with_name(stem.name + ".main")}
            names["carrier"].write_bytes((carrier / path).read_bytes())
            names["base"].write_bytes(blob(repo, ns.base, path))
            names["main"].write_bytes(blob(repo, ns.main, path))
            done = subprocess.run(["git", "merge-file", "-p", "-L", "carrier", "-L", "base c68e6b4c", "-L", "main", str(names["carrier"]), str(names["base"]), str(names["main"])], capture_output=True, check=False)
            merged = stem.with_name(stem.name + ".merged")
            merged.write_bytes(done.stdout)
            row.update({"action": "three-way", "merge_file_exit": done.returncode, "merged": str(merged), "merged_sha256": sha256_of(merged), "stderr": done.stderr.decode("utf-8", "replace")[-500:]})
        plan.append(row)
        print(f"{row['action']:28s} {path}" + (f"  (merge-file exit {row['merge_file_exit']})" if "merge_file_exit" in row else ""))
    out.mkdir(parents=True, exist_ok=True)
    (out / "merge_plan.json").write_text(json.dumps({"base": ns.base, "main": ns.main, "paths": plan}, indent=1) + "\n", encoding="utf-8")
    return 0


def verb_stamp(ns: argparse.Namespace) -> int:
    """Set a document's stamp by rule (main's value + one step): a clean three-way keeps main's value silently."""
    text = Path(getattr(ns, "in")).read_text(encoding="utf-8")
    old_line, new_line, date_line = f"**Version:** {ns.old}\n", f"**Version:** {ns.new}\n", f"**Last Updated:** {ns.date}\n"
    lines = text.splitlines(keepends=True)
    version_sites = [index + 1 for index, line in enumerate(lines) if line == old_line]
    date_sites = [index + 1 for index, line in enumerate(lines) if line == date_line]
    other_versions = [index + 1 for index, line in enumerate(lines) if line.startswith("**Version:**") and line != old_line]
    other_dates = [index + 1 for index, line in enumerate(lines) if line.startswith("**Last Updated:**") and line != date_line]
    if len(version_sites) != 2 or len(date_sites) != 2 or other_versions or other_dates:
        raise SystemExit(f"unexpected stamp sites: version {version_sites} (others {other_versions}), date {date_sites} (others {other_dates})")
    if ns.new in text:
        raise SystemExit(f"{ns.new} already occurs in the document")
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text("".join(new_line if line == old_line else line for line in lines), encoding="utf-8")
    print(f"stamp {ns.old} -> {ns.new} at lines {version_sites}; date '{ns.date}' at lines {date_sites}; wrote {ns.out} sha256 {sha256_of(Path(ns.out))}")
    return 0


def verb_land(ns: argparse.Namespace) -> int:
    carrier, target, rebuilt = Path(ns.carrier), Path(ns.target), Path(ns.rebuilt)
    head = git(target, "rev-parse", "HEAD").stdout.decode().strip()
    if head != ns.expect_head:
        raise SystemExit(f"target HEAD is {head}, expected {ns.expect_head}")
    plan = json.loads(Path(ns.plan).read_text(encoding="utf-8"))
    if plan["main"] != ns.expect_head:
        raise SystemExit("the plan was made for another main")
    applied = []
    for row in plan["paths"]:
        path = row["path"]
        if row["action"] == "delete":
            (target / path).unlink(missing_ok=True)
        elif row["action"] == "take the carrier's copy":
            (target / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(carrier / path, target / path)
        elif row["action"] == "three-way":
            text = (rebuilt / path).read_text(encoding="utf-8")
            if any(mark in text for mark in CONFLICT_MARKS):
                raise SystemExit(f"{rebuilt / path} still holds a conflict marker")
            shutil.copyfile(rebuilt / path, target / path)
        else:
            raise SystemExit(f"no action for {path}: {row['action']}")
        applied.append({"path": path, "action": row["action"], "sha256": sha256_of(target / path) if (target / path).is_file() else None})
    status = porcelain(target)
    print(f"applied {len(applied)} paths to {target.name}; status now names {len(status)} paths")
    for name, flags in sorted(status.items()):
        print(f"  {flags} {name}")
    Path(ns.out).write_text(json.dumps({"target": str(target), "head": head, "applied": applied, "status": status}, indent=1) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    verbs = parser.add_subparsers(dest="verb", required=True)
    for name, func, options in (
        ("verify-carrier", verb_verify_carrier, ("carrier", "hashes", "manifest", "repo", "out")),
        ("lay-base", verb_lay_base, ("carrier", "hashes", "manifest", "target", "expect-head")),
        ("merge", verb_merge, ("carrier", "manifest", "repo", "base", "main", "out")),
        ("stamp", verb_stamp, ("in", "out", "old", "new", "date")),
        ("land", verb_land, ("carrier", "manifest", "plan", "rebuilt", "target", "expect-head", "out")),
    ):
        sub = verbs.add_parser(name)
        for option in options:
            sub.add_argument(f"--{option}", required=True)
        sub.set_defaults(func=func)
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
