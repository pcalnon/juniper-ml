"""
Rebuild fix N-1's carrier files that juniper-cascor main changed, three-way, and check the CHANGELOG placement.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge);
         tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (``git merge-file -p <carrier> <base> <main>`` is the rebuild that works)

Usage:
    python3 <this> plan --base <old base sha> --main <new main sha>
    python3 <this> install --main <new main sha>
    python3 <this> check --main <new main sha>

plan     For every carrier file (git status in the N-1 worktree, tmp/ excluded) that main changed
         between the two shas, writes <file>.{carrier,base,main,merged} under n1-r3/rebuild/ and runs
         ``git merge-file -p carrier base main``. Exit status 0 = clean merge. For CHANGELOG.md it
         also checks that main -> merged is ONE pure insertion equal to base -> carrier's, and that
         the entry sits under the top ``## [Unreleased]``, inside ``### Fixed``, below at least one
         existing entry (brief rule 9).
install  Refuses unless HEAD is <new main sha>; copies each merged file into the worktree and
         re-runs the checks on the installed file.
check    Re-runs the CHANGELOG checks on the worktree's CHANGELOG.md against <new main sha>.
Writes n1-r3/rebuild/rebuild.json. Exit 1 on any failed check.
"""

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess  # nosec B404 -- fixed-argv git calls
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
OUT = TREE / "tmp" / "flood4-fix" / "n1-r3" / "rebuild"
ENTRY_HEAD = "- **A fit that returns while its run is paused now settles `COMPLETED`."


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(TREE), *args], check=check, capture_output=True, text=True)  # nosec B603 B607


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def carrier_paths() -> list:
    out = git("status", "--porcelain", "--untracked-files=all").stdout
    return sorted(line[3:] for line in out.splitlines() if not line[3:].startswith("tmp/"))


def insertions(old: str, new: str) -> list:
    """(opcode, old-range, new lines) for every non-equal opcode of old -> new, by line."""
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            ops.append((tag, i1, i2, "".join(b[j1:j2])))
    return ops


def placement(text: str) -> dict:
    """Where the N-1 entry sits: its release section, subsection, and the entries above it there."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(ENTRY_HEAD)]
    result = {"entry_lines": [i + 1 for i in starts]}
    if len(starts) != 1:
        result["ok"] = False
        return result
    at = starts[0]
    releases = [i for i, line in enumerate(lines) if line.startswith("## [")]
    top = releases[0] if releases else None
    release = max((i for i in releases if i < at), default=None)
    sub = max((i for i, line in enumerate(lines) if line.startswith("### ") and release is not None and release < i < at), default=None)
    above = [lines[i][:90] for i in range(sub + 1, at) if lines[i].startswith("- ")] if sub is not None else []
    result.update({
        "top_release_heading": lines[top] if top is not None else None,
        "entry_release_heading": lines[release] if release is not None else None,
        "entry_subsection": lines[sub] if sub is not None else None,
        "entries_above_in_subsection": above,
        "line": at + 1,
    })
    result["ok"] = bool(release is not None and release == top and lines[release].startswith("## [Unreleased]") and result["entry_subsection"] == "### Fixed" and above)
    return result


def changelog_checks(carrier: str, base: str, main: str, merged: str) -> dict:
    ours = insertions(base, carrier)
    theirs = insertions(main, merged)
    pure = len(ours) == 1 and ours[0][0] == "insert" and len(theirs) == 1 and theirs[0][0] == "insert" and ours[0][3] == theirs[0][3]
    return {
        "base_to_carrier_ops": [(op[0], op[1], op[2], len(op[3].splitlines())) for op in ours],
        "main_to_merged_ops": [(op[0], op[1], op[2], len(op[3].splitlines())) for op in theirs],
        "one_pure_insertion_equal_to_the_carriers": pure,
        "placement": placement(merged),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("plan", "install", "check"))
    parser.add_argument("--base")
    parser.add_argument("--main", required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / "rebuild.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    failed = 0

    if args.cmd == "plan":
        changed = set(git("diff", "--name-only", args.base, args.main).stdout.split())
        both = [rel for rel in carrier_paths() if rel in changed]
        report = {"base": args.base, "main": args.main, "main_changed": sorted(changed), "carrier_files_main_changed": both, "files": {}}
        for rel in both:
            stem = OUT / rel.replace("/", "__")
            carrier = (TREE / rel).read_text(encoding="utf-8")
            base = git("show", f"{args.base}:{rel}").stdout
            main_text = git("show", f"{args.main}:{rel}").stdout
            for suffix, text in (("carrier", carrier), ("base", base), ("main", main_text)):
                Path(f"{stem}.{suffix}").write_text(text, encoding="utf-8")
            proc = subprocess.run(["git", "merge-file", "-p", f"{stem}.carrier", f"{stem}.base", f"{stem}.main"], capture_output=True, text=True, check=False)  # nosec B603 B607
            Path(f"{stem}.merged").write_text(proc.stdout, encoding="utf-8")
            entry = {"merge_file_exit": proc.returncode, "sha256": {"carrier": sha256(carrier), "base": sha256(base), "main": sha256(main_text), "merged": sha256(proc.stdout)}}
            if rel == "CHANGELOG.md":
                entry["checks"] = changelog_checks(carrier, base, main_text, proc.stdout)
                failed += not (entry["checks"]["one_pure_insertion_equal_to_the_carriers"] and entry["checks"]["placement"]["ok"])
            failed += proc.returncode != 0
            report["files"][rel] = entry
            print(f"{rel}: merge-file exit {proc.returncode}; {json.dumps(entry.get('checks', {}), indent=1)}")
    elif args.cmd == "install":
        head = git("rev-parse", "HEAD").stdout.strip()
        if head != args.main:
            print(f"refusing: HEAD is {head}, not {args.main}")
            return 1
        for rel in report.get("files", {}):
            stem = OUT / rel.replace("/", "__")
            shutil.copyfile(f"{stem}.merged", TREE / rel)
            installed = (TREE / rel).read_text(encoding="utf-8")
            ok = sha256(installed) == report["files"][rel]["sha256"]["merged"]
            failed += not ok
            print(f"installed {rel}: sha256 {'matches' if ok else 'DIFFERS FROM'} the merge result")
        report["installed_on_head"] = head
    if args.cmd in ("install", "check"):
        main_text = git("show", f"{args.main}:CHANGELOG.md").stdout
        planned = insertions(main_text, (OUT / "CHANGELOG.md.merged").read_text(encoding="utf-8"))
        current = (TREE / "CHANGELOG.md").read_text(encoding="utf-8")
        theirs = insertions(main_text, current)
        check = {"main_to_worktree_ops": [(op[0], op[1], op[2], len(op[3].splitlines())) for op in theirs], "one_pure_insertion": len(theirs) == 1 and theirs[0][0] == "insert", "placement": placement(current)}
        # The entry's TEXT may change after the plan (measured numbers); its POSITION in main may not.
        check["inserted_where_the_merge_put_it"] = len(theirs) == 1 and len(planned) == 1 and theirs[0][1] == planned[0][1]
        failed += not (check["one_pure_insertion"] and check["placement"]["ok"] and check["inserted_where_the_merge_put_it"])
        report[f"{args.cmd}_check"] = check
        print(json.dumps(check, indent=1))
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(f"{'FAILED' if failed else 'ok'}: report {report_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
