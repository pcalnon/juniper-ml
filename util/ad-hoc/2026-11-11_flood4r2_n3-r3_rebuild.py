"""
Rebuild the N-3 carrier (juniper-cascor fix/ws-resume-losses) on a newer origin/main, three-way, for round 3.

Three subcommands, run in this order around the fast-forward of the carrier worktree:

  snapshot  Check that the carrier's 11 files still hash to round 2's manifest (tmp/flood4-fix/n3-r2/manifest.json),
            then copy them to tmp/flood4-fix/n3-r3/snapshots/r2/. Nothing in the worktree is changed.
  merge     For every carrier file that main changed between the old base and the new one, write the old base's and
            the new main's copies beside the snapshot and run `git merge-file -p <carrier> <base> <main>`. The merged
            text, the conflict count and two containment checks (every line main added and every line the carrier
            added is still present) go to tmp/flood4-fix/n3-r3/merge/. A file with conflicts is also resolved with
            `--theirs` (main's side), which is accepted only when every conflict hunk holds version / date stamp
            lines and nothing else; the stamps are then set by hand.
  install   After the worktree has been fast-forwarded to the new main (which needs the changed files restored
            first), copy each merged result into the worktree and each untouched carrier file back from the
            snapshot, verifying every hash.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         tmp/flood4r2-val/n3-r2-claims-lens/findings.json F8 (the stamp traps this rebuild meets)
"""

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
R2 = CARRIER / "tmp" / "flood4-fix" / "n3-r2"
R3 = CARRIER / "tmp" / "flood4-fix" / "n3-r3"
SNAP = R3 / "snapshots" / "r2"
MERGE = R3 / "merge"

#: A conflict hunk may be resolved to main's side only when all of its lines are stamps like these.
STAMP_LINE = re.compile(r"^\*\*(Version|Document Version|Last Updated)\*\*: \S+$")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(CARRIER), *args], capture_output=True, text=True)


def flat(rel: str) -> str:
    return rel.replace("/", "__")


def carrier_files() -> dict:
    with open(R2 / "manifest.json", encoding="utf-8") as fh:
        return {row["path"]: row["sha256"] for row in json.load(fh)["files"]}


def snapshot() -> int:
    expected = carrier_files()
    bad = [rel for rel, digest in expected.items() if sha(CARRIER / rel) != digest]
    if bad:
        print("NOT round 2's validated tree; these files differ from tmp/flood4-fix/n3-r2/manifest.json:", bad)
        return 1
    for rel, digest in expected.items():
        dest = SNAP / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CARRIER / rel, dest)
        if sha(dest) != digest:
            raise SystemExit(f"snapshot of {rel} is not byte-for-byte")
    print(f"snapshot: {len(expected)} files, each equal to round 2's manifest, copied to {SNAP}")
    return 0


def added_lines(old: str, new: str) -> list:
    """The non-blank lines ``new`` adds over ``old`` (difflib, line-wise)."""
    out = []
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++") and line[1:].strip():
            out.append(line[1:])
    return out


def conflict_hunks(text: str) -> list:
    """Each conflict of a merge-file result as (ours, theirs) line lists."""
    hunks, ours, theirs, side = [], [], [], None
    for line in text.splitlines():
        if line.startswith("<<<<<<< "):
            ours, theirs, side = [], [], "ours"
        elif line.startswith("=======") and side == "ours":
            side = "theirs"
        elif line.startswith(">>>>>>> ") and side == "theirs":
            hunks.append((ours, theirs))
            side = None
        elif side == "ours":
            ours.append(line)
        elif side == "theirs":
            theirs.append(line)
    return hunks


def merge(base: str, main: str) -> int:
    changed = git("diff", "--name-only", base, main)
    if changed.returncode:
        raise SystemExit(changed.stderr)
    main_touched = set(changed.stdout.split())
    expected = carrier_files()
    shared = sorted(rel for rel in expected if rel in main_touched)
    MERGE.mkdir(parents=True, exist_ok=True)
    report = {"base": base, "main": main, "main_changed_files": len(main_touched), "carrier_files_main_changed": shared, "files": {}}
    status = 0
    for rel in shared:
        stem = MERGE / flat(rel)
        texts = {}
        for name, rev in (("base", base), ("main", main)):
            shown = git("show", f"{rev}:{rel}")
            if shown.returncode:
                raise SystemExit(shown.stderr)
            texts[name] = shown.stdout
            Path(f"{stem}.{name}").write_text(shown.stdout, encoding="utf-8")
        carrier_text = (SNAP / rel).read_text(encoding="utf-8")
        args = ["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(SNAP / rel), f"{stem}.base", f"{stem}.main"]
        plain = subprocess.run(args, capture_output=True, text=True)
        if plain.returncode < 0 or plain.returncode > 127:
            raise SystemExit(f"merge-file failed on {rel}: {plain.stderr}")
        Path(f"{stem}.merged-with-markers").write_text(plain.stdout, encoding="utf-8")
        entry = {"conflicts": plain.returncode}
        merged = plain.stdout
        if plain.returncode:
            hunks = conflict_hunks(plain.stdout)
            entry["conflict_hunks"] = [{"carrier": ours, "main": theirs} for ours, theirs in hunks]
            only_stamps = all(STAMP_LINE.match(line) for ours, theirs in hunks for line in ours + theirs)
            entry["every_conflict_line_is_a_stamp"] = only_stamps
            if not only_stamps or len(hunks) != plain.returncode:
                status = 1
                print(f"{rel}: {plain.returncode} conflicts, NOT all stamp lines -- resolve by hand")
            theirs_run = subprocess.run(args[:3] + ["--theirs"] + args[3:], capture_output=True, text=True)
            if theirs_run.returncode:
                raise SystemExit(f"merge-file --theirs failed on {rel}: {theirs_run.stderr}")
            merged = theirs_run.stdout
            entry["resolution"] = "main's side of each conflict (stamps are then set by hand to main's value + 1)"
        Path(f"{stem}.merged").write_text(merged, encoding="utf-8")
        merged_lines = set(merged.splitlines())
        lost_main = [line for line in added_lines(texts["base"], texts["main"]) if line not in merged_lines]
        lost_carrier = [line for line in added_lines(texts["base"], carrier_text) if line not in merged_lines]
        entry["lines_main_added_missing_from_merged"] = lost_main
        entry["lines_carrier_added_missing_from_merged"] = lost_carrier
        entry["merged_sha256"] = hashlib.sha256(merged.encode("utf-8")).hexdigest()
        entry["merged_equals_carrier"] = merged == carrier_text
        entry["merged_equals_main"] = merged == texts["main"]
        report["files"][rel] = entry
        print(f"{rel}: {plain.returncode} conflicts; main-added lines missing {len(lost_main)}; carrier-added lines missing {len(lost_carrier)}")
        for line in lost_main:
            print("   MAIN LINE NOT IN MERGED:", line[:160])
        for line in lost_carrier:
            print("   carrier line not in merged:", line[:160])
    with open(MERGE / "merge_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print("report ->", MERGE / "merge_report.json")
    return status


def install() -> int:
    with open(MERGE / "merge_report.json", encoding="utf-8") as fh:
        report = json.load(fh)
    head = git("rev-parse", "HEAD").stdout.strip()
    if head != report["main"]:
        print(f"the carrier worktree is at {head}, not at the new main {report['main']}: fast-forward it first")
        return 1
    expected = carrier_files()
    for rel, digest in expected.items():
        if rel in report["files"]:
            source = Path(f"{MERGE / flat(rel)}.merged")
            want = report["files"][rel]["merged_sha256"]
        else:
            source, want = SNAP / rel, digest
        shutil.copyfile(source, CARRIER / rel)
        if sha(CARRIER / rel) != want:
            raise SystemExit(f"install of {rel} is not byte-for-byte")
        print(f"installed {rel} from {'the three-way merge' if rel in report['files'] else 'the round-2 snapshot'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    mp = sub.add_parser("merge")
    mp.add_argument("--base", required=True, help="the sha the carrier was built on")
    mp.add_argument("--main", required=True, help="the new origin/main sha")
    sub.add_parser("install")
    args = ap.parse_args()
    if args.cmd == "snapshot":
        return snapshot()
    if args.cmd == "merge":
        return merge(args.base, args.main)
    return install()


if __name__ == "__main__":
    sys.exit(main())
