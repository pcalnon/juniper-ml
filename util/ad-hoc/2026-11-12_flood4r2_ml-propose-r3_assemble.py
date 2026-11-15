#!/usr/bin/env python3
"""
Rebuild the ml-propose carrier onto a worktree at current origin/main, and re-derive its document stamps.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The carrier is an uncommitted tree built on one commit of main, and main moves before it lands. A file main has
not changed since the carrier's base is copied. A file main HAS changed is rebuilt three-way
(`git merge-file -p <carrier> <base> <main>`), never copied over main's: a copy would revert what main gained.

Two documents carry a stamp that other changes move too, so their stamps are never merged. The carrier's stamp
edits are taken out first, and re-derived from main afterwards, whether or not main moved:

* docs/REFERENCE.md -- main's Version plus one patch, the landing date in the header and the footer, and the
  carrier's Version History row renumbered, re-dated and placed directly after the row that carries main's stamp;
* the release-train runbook (no footer, no history table) -- main's Version plus one patch and the landing date.

Used twice. Round 3 was assembled from round 2 with it (--carrier the round-2 worktree, --base 4bae7520). At
landing, run it again from the landing worktree with --carrier this round's worktree, --base the commit this
round was built on (its manifest's base_sha) and the UTC landing date; --dest defaults to the worktree that
holds this script. Adapted from the final-check validator's 2026-11-11_flood4r2_val_ml-propose-final_assemble.py.

Usage:
    python3 <this> --carrier <carrier worktree> --base <sha> --manifest <manifest.json> --out <scratch dir>
                   --landing-date YYYY-MM-DD [--dest <worktree root>] [--only <path>] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git plumbing in the destination worktree
import sys
from pathlib import Path

REFERENCE = "docs/REFERENCE.md"
RUNBOOK = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
STAMP_VERSION = re.compile(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)$", re.MULTILINE)
STAMP_DATE = re.compile(r"^\*\*Last Updated:\*\* (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
HISTORY_ROW = re.compile(r"^\| (\d+\.\d+\.\d+)\s+\| (\d{4}-\d{2}-\d{2}) \| .*\|$", re.MULTILINE)
RUNBOOK_VERSION = re.compile(r"^\*\*Version\*\*: (\d+)\.(\d+)\.(\d+)$", re.MULTILINE)
RUNBOOK_DATE = re.compile(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", re.MULTILINE)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)  # nosec B603 B607


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(root: Path, rev: str, path: str) -> "bytes | None":
    done = git(root, "show", f"{rev}:{path}")
    return done.stdout if done.returncode == 0 else None


def destamp_reference(carrier: str, base: str) -> "tuple[str, str]":
    """The carrier's REFERENCE with its stamp edits undone, and the Version History row it added."""
    base_versions = STAMP_VERSION.findall(base)
    base_dates = STAMP_DATE.findall(base)
    if len(base_versions) != 2 or len(set(base_versions)) != 1 or len(base_dates) != 2 or len(set(base_dates)) != 1:
        raise SystemExit("base REFERENCE: expected one stamp value in header and footer")
    base_version = ".".join(base_versions[0])
    base_rows = {m.group(1) for m in HISTORY_ROW.finditer(base)}
    added = [m for m in HISTORY_ROW.finditer(carrier) if m.group(1) not in base_rows]
    if len(added) != 1:
        raise SystemExit(f"carrier REFERENCE: expected exactly one new Version History row, found {len(added)}")
    row = added[0].group(0)
    text = carrier.replace(row + "\n", "", 1)
    text, n_version = STAMP_VERSION.subn(f"**Version:** {base_version}", text)
    text, n_date = STAMP_DATE.subn(f"**Last Updated:** {base_dates[0]}", text)
    if (n_version, n_date) != (2, 2):
        raise SystemExit(f"carrier REFERENCE: stamp lines replaced {n_version}/{n_date}, expected 2/2")
    return text, row


def restamp_reference(merged: str, row: str, landing_date: str) -> "tuple[str, str]":
    """Bump main's stamp by one patch, set the landing date, and add the carrier's row after main's stamped one."""
    versions = STAMP_VERSION.findall(merged)
    if len(versions) != 2 or len(set(versions)) != 1:
        raise SystemExit("merged REFERENCE: header and footer Version differ or are missing")
    major, minor, patch = (int(part) for part in versions[0])
    new_version = f"{major}.{minor}.{patch + 1}"
    rows = [m for m in HISTORY_ROW.finditer(merged) if m.group(1) == f"{major}.{minor}.{patch}"]
    if len(rows) != 1 or any(m.group(1) == new_version for m in HISTORY_ROW.finditer(merged)):
        raise SystemExit("merged REFERENCE: the stamped version has no single Version History row, or the next one is taken")
    head = HISTORY_ROW.match(row)
    if head is None:
        raise SystemExit("carrier row does not parse")
    body = row[head.end(2) :]
    new_row = f"| {new_version}  | {landing_date}{body}"
    last = rows[0]
    text = merged[: last.end()] + "\n" + new_row + merged[last.end() :]
    text = STAMP_VERSION.sub(f"**Version:** {new_version}", text)
    text = STAMP_DATE.sub(f"**Last Updated:** {landing_date}", text)
    return text, new_version


def runbook_stamp(text: str, what: str) -> "tuple[str, str]":
    versions = RUNBOOK_VERSION.findall(text)
    dates = RUNBOOK_DATE.findall(text)
    if len(versions) != 1 or len(dates) != 1:
        raise SystemExit(f"{what} runbook: expected one header Version and one Last Updated, found {len(versions)}/{len(dates)}")
    return ".".join(versions[0]), dates[0]


def destamp_runbook(carrier: str, base: str) -> str:
    """The carrier's runbook with its header stamp put back to the base's, so the merge sees no stamp edit."""
    base_version, base_date = runbook_stamp(base, "base")
    runbook_stamp(carrier, "carrier")
    text = RUNBOOK_VERSION.sub(f"**Version**: {base_version}", carrier)
    return RUNBOOK_DATE.sub(f"**Last Updated**: {base_date}", text)


def restamp_runbook(merged: str, landing_date: str) -> "tuple[str, str]":
    """Main's runbook Version plus one patch, and the landing date."""
    version, _ = runbook_stamp(merged, "merged")
    major, minor, patch = (int(part) for part in version.split("."))
    new_version = f"{major}.{minor}.{patch + 1}"
    text = RUNBOOK_VERSION.sub(f"**Version**: {new_version}", merged)
    return RUNBOOK_DATE.sub(f"**Last Updated**: {landing_date}", text), new_version


def merge_three_way(root: Path, work: Path, name: str, carrier: bytes, base: bytes, main: bytes) -> "tuple[bytes, int]":
    """``carrier`` rebuilt onto ``main``; a plain copy when main has not moved from ``base``."""
    if main == base:
        return carrier, 0
    work.mkdir(parents=True, exist_ok=True)
    paths = {}
    for label, data in (("carrier", carrier), ("base", base), ("main", main)):
        paths[label] = work / f"{name}.{label}"
        paths[label].write_bytes(data)
    done = git(root, "merge-file", "-p", str(paths["carrier"]), str(paths["base"]), str(paths["main"]))
    return done.stdout, done.returncode


def assemble_one(args: argparse.Namespace, work: Path, entry: dict) -> "tuple[dict, bytes, bool]":
    """-> (report row, assembled bytes, ok)."""
    path = entry["path"]
    carrier_bytes = (args.carrier / path).read_bytes()
    row = {"path": path, "carrier_sha256": sha256(carrier_bytes), "manifest_sha256_ok": sha256(carrier_bytes) == entry.get("sha256")}
    base_bytes = blob(args.dest, args.base, path)
    main_bytes = blob(args.dest, "HEAD", path)
    if base_bytes is None:
        row["method"] = "copy (added by the carrier)" if main_bytes is None else "REFUSED: main now has this path"
        return row, carrier_bytes, main_bytes is None
    if main_bytes is None:
        row["method"] = "REFUSED: main no longer has this path"
        return row, carrier_bytes, False
    moved = "main moved since base: three-way" if main_bytes != base_bytes else "main unchanged since base"
    if path == REFERENCE:
        destamped, history_row = destamp_reference(carrier_bytes.decode("utf-8"), base_bytes.decode("utf-8"))
        merged, conflicts = merge_three_way(args.dest, work, "REFERENCE.md", destamped.encode("utf-8"), base_bytes, main_bytes)
        row["method"] = f"{moved}; stamp edits taken out, then re-derived from main"
        row["conflicts"] = conflicts
        if conflicts:
            return row, merged, False
        restamped, row["restamped_to"] = restamp_reference(merged.decode("utf-8"), history_row, args.landing_date)
        return row, restamped.encode("utf-8"), True
    if path == RUNBOOK:
        destamped = destamp_runbook(carrier_bytes.decode("utf-8"), base_bytes.decode("utf-8"))
        merged, conflicts = merge_three_way(args.dest, work, "RUNBOOK.md", destamped.encode("utf-8"), base_bytes, main_bytes)
        row["method"] = f"{moved}; stamp edits taken out, then re-derived from main"
        row["conflicts"] = conflicts
        if conflicts:
            return row, merged, False
        restamped, row["restamped_to"] = restamp_runbook(merged.decode("utf-8"), args.landing_date)
        return row, restamped.encode("utf-8"), True
    merged, conflicts = merge_three_way(args.dest, work, Path(path).name, carrier_bytes, base_bytes, main_bytes)
    row["method"] = moved
    row["conflicts"] = conflicts
    return row, merged, conflicts == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--landing-date", required=True)
    parser.add_argument("--dest", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--only", action="append", help="rebuild only this manifest path (repeatable)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.landing_date):
        raise SystemExit("--landing-date wants YYYY-MM-DD")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    head = git(args.dest, "rev-parse", "HEAD").stdout.decode().strip()
    work = args.out / "assemble"
    work.mkdir(parents=True, exist_ok=True)
    report = {"dest": str(args.dest), "main_sha": head, "base_sha": args.base, "landing_date": args.landing_date, "files": []}
    results = []
    for entry in manifest["files"]:
        if args.only and entry["path"] not in args.only:
            continue
        row, result, ok = assemble_one(args, work, entry)
        row["assembled_sha256"] = sha256(result)
        row["ok"] = ok
        (work / (Path(entry["path"]).name + ".assembled")).write_bytes(result)
        report["files"].append(row)
        results.append((entry["path"], result, ok))
    report["ok"] = bool(results) and all(ok for _, _, ok in results) and all(item["manifest_sha256_ok"] for item in report["files"])
    if report["ok"] and not args.dry_run:
        for path, result, _ in results:
            target = args.dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(result)
    report["written"] = report["ok"] and not args.dry_run
    (args.out / "assemble_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
