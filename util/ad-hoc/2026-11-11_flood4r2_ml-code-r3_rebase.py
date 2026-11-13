#!/usr/bin/env python3
"""
Move the ml-code carrier (round 3) from one origin/main to the next: three-way the files both sides changed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: main moved under the finished build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebuild.py (the first rebuild, from another worktree's files);
         util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_snapshot.py (the restore point taken before this runs);
         juniper-ml#2360 (the change that moved main: it edits six of the carrier's files).

Usage (from the worktree root; the carrier is the worktree's uncommitted change set, HEAD at the old base):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebase.py prepare <old base sha> <new sha> <out dir>
    git reset --mixed <new sha>
    git restore --worktree --pathspec-from-file=<out dir>/restore_paths.txt
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebase.py apply <out dir>
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebase.py check <out dir>

``prepare`` writes only <out dir>. For each file that the carrier and main both modified it writes the three inputs
and ``git merge-file -p <carrier's copy> <old base's copy> <new main's copy>`` (<stem>.carrier, .base, .main and
.merged; the exit status is the number of conflicts, and a merge with conflicts keeps its markers). The other paths
main changed go to restore_paths.txt. A path main deleted, or one that is not modified on both sides, is a problem
and exits 1: this script does not handle it.

The two git commands are run by hand between the steps. ``reset --mixed`` moves HEAD and the index and touches no
file; ``restore --worktree`` then gives main's other files their new content. ``apply`` writes each .merged file
into the worktree. ``check`` passes when the worktree's change set is the carrier's paths again, each file main
did not change still has its sha256, and each merged file is the merge. It is meant for right after ``apply``:
resolving a conflict by hand changes a merged file, as intended.
"""
import hashlib
import json
import subprocess  # nosec B404 -- fixed git argv, run in this worktree
import sys
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv


def change_set() -> dict:
    """Every path the worktree changes against the index, with its two-letter porcelain code."""
    out = git("status", "--porcelain", "--untracked-files=all").stdout.decode("utf-8")
    return {line[3:]: line[:2] for line in out.splitlines()}


def load(out: Path) -> dict:
    with open(out / "rebase.json", encoding="utf-8") as fh:
        return json.load(fh)


def prepare(old: str, new: str, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    carrier = change_set()
    report = {"old": git("rev-parse", old).stdout.decode().strip(), "new": git("rev-parse", new).stdout.decode().strip(), "carrier": {}, "merged": [], "restore": [], "problems": []}
    if git("rev-parse", "HEAD").stdout.decode().strip() != report["old"]:
        report["problems"].append("HEAD is not the old base %s" % old)
    for rel in sorted(carrier):
        report["carrier"][rel] = {"code": carrier[rel], "sha256": sha256(Path(rel).read_bytes())}
    for line in git("diff", "--name-status", "--no-renames", report["old"], report["new"]).stdout.decode("utf-8").splitlines():
        code, rel = line.split("\t", 1)
        if rel not in carrier and code != "D":
            report["restore"].append(rel)
        elif code != "M" or carrier.get(rel, "").strip() != "M":
            report["problems"].append("%s: main %s, carrier %r: not modified on both sides" % (rel, code, carrier.get(rel)))
        else:
            stem = out / rel.replace("/", "__")
            inputs = [stem.with_name(stem.name + suffix) for suffix in (".carrier", ".base", ".main")]
            inputs[0].write_bytes(Path(rel).read_bytes())
            inputs[1].write_bytes(git("show", "%s:%s" % (report["old"], rel)).stdout)
            inputs[2].write_bytes(git("show", "%s:%s" % (report["new"], rel)).stdout)
            merged = git("merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", *(str(path) for path in inputs))
            stem.with_name(stem.name + ".merged").write_bytes(merged.stdout)
            report["merged"].append({"path": rel, "merge_file_exit": merged.returncode, "merged_sha256": sha256(merged.stdout)})
            print("%-44s merge-file exit %d" % (rel, merged.returncode))
    (out / "restore_paths.txt").write_text("".join(rel + "\n" for rel in report["restore"]), encoding="utf-8")
    with open(out / "rebase.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("%s -> %s: the carrier changes %d paths; main changed %d of them (merged) and %d others (restore_paths.txt)" % (report["old"][:8], report["new"][:8], len(carrier), len(report["merged"]), len(report["restore"])))
    print("problems: %s" % (report["problems"] or "none"))
    return 1 if report["problems"] else 0


def apply(out: Path) -> int:
    report = load(out)
    if git("rev-parse", "HEAD").stdout.decode().strip() != report["new"]:
        print("HEAD is not %s: run the git reset first; nothing written" % report["new"])
        return 1
    for row in report["merged"]:
        Path(row["path"]).write_bytes((out / (row["path"].replace("/", "__") + ".merged")).read_bytes())
        print("wrote %-44s (%d conflict(s) to resolve)" % (row["path"], row["merge_file_exit"]))
    return 0


def check(out: Path) -> int:
    report = load(out)
    merged = {row["path"]: row["merged_sha256"] for row in report["merged"]}
    now = change_set()
    problems = ["%s: change-set code %r, was %r" % (rel, now.get(rel), report["carrier"].get(rel, {}).get("code")) for rel in sorted(set(now) | set(report["carrier"])) if now.get(rel) != report["carrier"].get(rel, {}).get("code")]
    for rel in sorted(report["carrier"]):
        if not Path(rel).is_file():
            problems.append("%s: missing" % rel)
        elif sha256(Path(rel).read_bytes()) != merged.get(rel, report["carrier"][rel]["sha256"]):
            problems.append("%s: is not %s" % (rel, "the merge" if rel in merged else "the file it was before the move"))
    print("HEAD %s; change set %d paths (the carrier's: %d); %d merged files, %d unchanged files compared" % (git("rev-parse", "HEAD").stdout.decode().strip(), len(now), len(report["carrier"]), len(merged), len(report["carrier"]) - len(merged)))
    print("problems: %s" % (problems or "none"))
    return 1 if problems else 0


def main(argv: list) -> int:
    if len(argv) == 5 and argv[1] == "prepare":
        return prepare(argv[2], argv[3], Path(argv[4]).resolve())
    if len(argv) == 3 and argv[1] == "apply":
        return apply(Path(argv[2]).resolve())
    if len(argv) == 3 and argv[1] == "check":
        return check(Path(argv[2]).resolve())
    print("usage: prepare <old base sha> <new sha> <out dir> | apply <out dir> | check <out dir>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
