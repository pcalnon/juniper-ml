#!/usr/bin/env python3
"""
Land the ml-propose carrier on the main of the day: rebuild it, re-derive every stamp and date, and check the result.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (finishing round 3 of the ml-propose carrier, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_assemble.py (the rebuild and the stamp rules; run unchanged)

WHY THIS EXISTS
The carrier is an uncommitted tree built on one commit of main, with document stamps for one landing day. Other
carriers land before it and bump docs/REFERENCE.md too, and a landing can slip past midnight UTC. So nothing about
a stamp or a date is typed at the landing. This script is the one command for it:

1. it runs round 3's assemble helper, unchanged, from the carrier's own copy: a file main has not changed since
   the carrier's base is copied, a file main has changed is rebuilt three-way, and both documents' stamps are
   taken out first and re-derived from main afterwards (docs/REFERENCE.md: main's Version plus one patch, the
   landing date in header and footer, the Version History row renumbered, re-dated and placed directly after
   the row that carries main's stamp; the runbook: main's Version plus one patch and the landing date);
2. it checks the result, from the assembled bytes: header and footer agree, each stamp is main's plus one patch,
   every date is the landing date, the history row sits directly after main's stamped row, and -- stamps aside --
   the lines the landing adds to and removes from main are exactly the lines the carrier adds to and removes
   from its own base, so nothing main gained is reverted and nothing of the carrier is lost. CHANGELOG.md must
   hold the carrier's entry once, under the top [Unreleased] -> ### Fixed, below another entry;
3. it re-derives the one deliverable text that names a stamp, the PR body's "Stamps" line, and writes the four
   PR texts beside the report.

--dry-run writes nothing into --dest. Exit status 0 only when the rebuild has no conflict and every check holds.

Usage (the landing; --dest is a worktree whose HEAD is the main the PR will be based on):
    python3 <carrier>/util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py --carrier <carrier worktree>
        --dest <landing worktree> --landing-date <UTC date, YYYY-MM-DD> --out <scratch dir> [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the destination worktree, and round 3's helper
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRATCH_REL = "tmp/flood4r2/ml-propose/r3b"
ASSEMBLE_REL = "util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_assemble.py"
REFERENCE = "docs/REFERENCE.md"
RUNBOOK = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
CHANGELOG = "CHANGELOG.md"
TEXTS = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt")
REF_VERSION = re.compile(r"^\*\*Version:\*\* (\d+\.\d+\.\d+)$")
REF_DATE = re.compile(r"^\*\*Last Updated:\*\* (\d{4}-\d{2}-\d{2})$")
HISTORY_ROW = re.compile(r"^\| (\d+\.\d+\.\d+)\s+\| (\d{4}-\d{2}-\d{2}) \|")
RUNBOOK_VERSION = re.compile(r"^\*\*Version\*\*: (\d+\.\d+\.\d+)$")
RUNBOOK_DATE = re.compile(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$")
STAMPS_LINE = re.compile(r"^- Stamps: .*$", re.MULTILINE)


def stamps_line(reference: tuple, runbook: tuple, landing_date: str) -> str:
    """The PR body's one line that names a stamp, from (main's value, the new value) of each document."""
    return (
        f"- Stamps: `docs/REFERENCE.md` {reference[0]} -> {reference[1]} and the runbook {runbook[0]} -> {runbook[1]}, both dated {landing_date}. "
        "`util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py` re-derives them from `main` at the landing, with `util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_assemble.py`."
    )


def blob(root: Path, rev: str, path: str) -> "bytes | None":
    done = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=root, capture_output=True, check=False)  # nosec B603 B607
    return done.stdout if done.returncode == 0 else None


def plus_one_patch(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def normalized(path: str, text: str) -> list:
    """The file's lines with every stamp value replaced by a placeholder, so two builds differ only in content."""
    lines = []
    for line in text.splitlines():
        if path == REFERENCE:
            line = REF_VERSION.sub("**Version:** <V>", line)
            line = REF_DATE.sub("**Last Updated:** <D>", line)
            row = HISTORY_ROW.match(line)
            if row:
                line = "| <V> | <D> |" + line[row.end() :]
        elif path == RUNBOOK:
            line = RUNBOOK_VERSION.sub("**Version**: <V>", line)
            line = RUNBOOK_DATE.sub("**Last Updated**: <D>", line)
        lines.append(line)
    return lines


def moved_lines(path: str, old: str, new: str) -> tuple:
    """(lines added, lines removed) going from ``old`` to ``new``, as multisets of stamp-normalized lines."""
    before, after = Counter(normalized(path, old)), Counter(normalized(path, new))
    return after - before, before - after


def values(pattern: "re.Pattern", text: str) -> list:
    return [m.group(1) for line in text.splitlines() if (m := pattern.match(line))]


def check_reference(main: str, result: str, landing_date: str) -> tuple:
    problems, sites = [], []
    main_versions, new_versions = values(REF_VERSION, main), values(REF_VERSION, result)
    new_dates = values(REF_DATE, result)
    main_dates = values(REF_DATE, main)
    if len(main_versions) != 2 or len(set(main_versions)) != 1:
        return [f"main's {REFERENCE}: header and footer Version are not one value twice: {main_versions}"], sites, None
    expected = plus_one_patch(main_versions[0])
    if new_versions != [expected, expected]:
        problems.append(f"{REFERENCE}: header/footer Version {new_versions}, expected {expected} twice (main is {main_versions[0]})")
    if new_dates != [landing_date, landing_date]:
        problems.append(f"{REFERENCE}: header/footer Last Updated {new_dates}, expected {landing_date} twice")
    lines = result.splitlines()
    rows = [i for i, line in enumerate(lines) if (m := HISTORY_ROW.match(line)) and m.group(1) == expected]
    if len(rows) != 1:
        problems.append(f"{REFERENCE}: {len(rows)} Version History rows for {expected}, expected 1")
    else:
        row = HISTORY_ROW.match(lines[rows[0]])
        above = HISTORY_ROW.match(lines[rows[0] - 1])
        if row.group(2) != landing_date:
            problems.append(f"{REFERENCE}: the {expected} history row is dated {row.group(2)}, expected {landing_date}")
        if above is None or above.group(1) != main_versions[0]:
            problems.append(f"{REFERENCE}: the {expected} history row does not directly follow main's {main_versions[0]} row")
        sites.append({"file": REFERENCE, "field": "Version History row", "line": rows[0] + 1, "directly_after_the_row_of": main_versions[0], "new": f"{expected} / {row.group(2)}"})
    for field, old, new in (("header and footer Version", main_versions[0], expected), ("header and footer Last Updated", main_dates[0] if main_dates else None, landing_date)):
        sites.append({"file": REFERENCE, "field": field, "main": old, "new": new})
    return problems, sites, (main_versions[0], expected)


def check_runbook(main: str, result: str, landing_date: str) -> tuple:
    problems, sites = [], []
    main_versions, new_versions = values(RUNBOOK_VERSION, main), values(RUNBOOK_VERSION, result)
    main_dates, new_dates = values(RUNBOOK_DATE, main), values(RUNBOOK_DATE, result)
    if len(main_versions) != 1:
        return [f"main's runbook: {len(main_versions)} header Version lines, expected 1"], sites, None
    expected = plus_one_patch(main_versions[0])
    if new_versions != [expected]:
        problems.append(f"runbook: Version {new_versions}, expected [{expected}] (main is {main_versions[0]})")
    if new_dates != [landing_date]:
        problems.append(f"runbook: Last Updated {new_dates}, expected [{landing_date}]")
    sites.append({"file": RUNBOOK, "field": "header Version", "main": main_versions[0], "new": expected})
    sites.append({"file": RUNBOOK, "field": "header Last Updated", "main": main_dates[0] if main_dates else None, "new": landing_date})
    return problems, sites, (main_versions[0], expected)


def check_changelog(result: str, entry: str) -> list:
    problems = []
    if result.count(entry) != 1:
        return [f"{CHANGELOG}: the carrier's entry occurs {result.count(entry)} times, expected 1"]
    head = result[: result.index(entry)].splitlines()
    releases = [line for line in head if line.startswith("## [")]
    sections = [i for i, line in enumerate(head) if line.startswith("### ")]
    if len(releases) != 1 or releases[0].strip() != "## [Unreleased]":
        problems.append(f"{CHANGELOG}: the entry is not under the top [Unreleased] (headings above it: {releases[-2:]})")
    if not sections or head[sections[-1]].strip() != "### Fixed":
        problems.append(f"{CHANGELOG}: the entry is not under ### Fixed")
    elif not any(line.startswith("- ") for line in head[sections[-1] :]):
        problems.append(f"{CHANGELOG}: the entry is the first of its subsection (it must sit below another entry)")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--landing-date", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.landing_date):
        raise SystemExit("--landing-date wants YYYY-MM-DD")
    # Every path is made absolute here: round 3's helper runs its merges with the destination worktree as the
    # working directory, so a relative --out would be looked up there and `git merge-file` would fail (exit 255).
    carrier, dest = args.carrier.resolve(), args.dest.resolve()
    args.out = args.out.resolve()
    scratch = carrier / SCRATCH_REL
    manifest_path = scratch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest["base_sha"]
    args.out.mkdir(parents=True, exist_ok=True)

    command = [sys.executable, "-B", str(carrier / ASSEMBLE_REL), "--carrier", str(carrier), "--base", base, "--manifest", str(manifest_path), "--out", str(args.out), "--landing-date", args.landing_date, "--dest", str(dest)]
    if args.dry_run:
        command.append("--dry-run")
    # An earlier run's report in a reused --out is removed first: round 3's helper can stop (a refused stamp, a
    # missing file) with exit 1 and no report, and a stale one must never be read as this run's.
    assemble_report_path = args.out / "assemble_report.json"
    assemble_report_path.unlink(missing_ok=True)
    done = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603
    (args.out / "assemble.stdout").write_text(done.stdout + done.stderr, encoding="utf-8")
    reported = assemble_report_path.is_file()
    assembled = json.loads(assemble_report_path.read_text(encoding="utf-8")) if reported else {"files": [], "ok": False}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = {
        "carrier": str(carrier),
        "carrier_manifest_status": manifest.get("status"),
        "dest": str(dest),
        "main_sha": assembled.get("main_sha"),
        "base_sha": base,
        "landing_date": args.landing_date,
        "today_utc": today,
        "landing_date_is_today_utc": args.landing_date == today,
        "dry_run": args.dry_run,
        "assemble_exit": done.returncode,
        "assemble_ok": bool(assembled.get("ok")),
        "written_into_dest": bool(assembled.get("written")),
        "files": [{key: row.get(key) for key in ("path", "method", "conflicts", "restamped_to", "manifest_sha256_ok", "carrier_sha256", "assembled_sha256", "ok")} for row in assembled["files"]],
        "problems": [],
        "stamp_sites": [],
    }
    problems = report["problems"]
    if not reported:
        last = (done.stdout + done.stderr).strip().splitlines()[-1:]
        problems.append(f"the assemble helper stopped without a report (exit {done.returncode}): {last[0] if last else 'no output'}; nothing was written")
    elif not report["assemble_ok"]:
        problems.append("the assemble helper did not finish cleanly (a conflict, a file whose sha256 is not the manifest's, or a refused path): see assemble.stdout; nothing was written")
        for row in assembled["files"]:
            if row.get("conflicts") == 255:
                problems.append(f"{row['path']}: `git merge-file` itself failed (exit 255 is an error, not a number of conflicts)")
            elif row.get("conflicts"):
                problems.append(f"{row['path']}: {row['conflicts']} conflict(s) in the three-way rebuild; resolve by hand from {args.out / 'assemble'}")
            elif not row.get("manifest_sha256_ok", True):
                problems.append(f"{row['path']}: the carrier's bytes are not the manifest's (sha256 {str(row.get('carrier_sha256'))[:12]})")
    listed = {row["path"]: row for row in manifest["files"]}
    if {row["path"] for row in assembled["files"]} != set(listed):
        problems.append("the assemble report does not cover the manifest's file list")

    stamps = {}
    for row in assembled["files"] if report["assemble_ok"] else []:
        path = row["path"]
        result = (args.out / "assemble" / (Path(path).name + ".assembled")).read_bytes()
        carrier_bytes = (carrier / path).read_bytes()
        base_bytes, main_bytes = blob(dest, base, path), blob(dest, "HEAD", path)
        if base_bytes is None or main_bytes is None:
            if result != carrier_bytes:
                problems.append(f"{path}: added by the carrier, but the assembled bytes are not the carrier's")
            continue
        own = moved_lines(path, base_bytes.decode("utf-8"), carrier_bytes.decode("utf-8"))
        landed = moved_lines(path, main_bytes.decode("utf-8"), result.decode("utf-8"))
        if own != landed:
            lost = sum((own[0] - landed[0]).values()) + sum((own[1] - landed[1]).values())
            extra = sum((landed[0] - own[0]).values()) + sum((landed[1] - own[1]).values())
            problems.append(f"{path}: against main the landing does not move the lines the carrier moves against its base ({lost} of the carrier's line moves missing, {extra} line moves that are not the carrier's)")
        if path == REFERENCE:
            found, sites, stamps["reference"] = check_reference(main_bytes.decode("utf-8"), result.decode("utf-8"), args.landing_date)
            problems.extend(found)
            report["stamp_sites"].extend(sites)
        elif path == RUNBOOK:
            found, sites, stamps["runbook"] = check_runbook(main_bytes.decode("utf-8"), result.decode("utf-8"), args.landing_date)
            problems.extend(found)
            report["stamp_sites"].extend(sites)
        elif path == CHANGELOG:
            problems.extend(check_changelog(result.decode("utf-8"), (scratch / "changelog_entry.txt").read_text(encoding="utf-8")))
        if b"<<<<<<<" in result or b">>>>>>>" in result:
            problems.append(f"{path}: conflict markers in the assembled bytes")

    texts_dir = args.out / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)
    report["texts"] = {}
    for name in TEXTS:
        source = scratch / name
        if not source.is_file():
            problems.append(f"{name}: not in the carrier's scratch directory")
            continue
        text = source.read_text(encoding="utf-8")
        if name == "pr_body.txt" and stamps.get("reference") and stamps.get("runbook"):
            if len(STAMPS_LINE.findall(text)) != 1:
                problems.append("pr_body.txt: expected exactly one '- Stamps: ' line")
            else:
                text = STAMPS_LINE.sub(lambda _m: stamps_line(stamps["reference"], stamps["runbook"], args.landing_date), text)
        (texts_dir / name).write_text(text, encoding="utf-8")
        report["texts"][name] = {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "changed_from_the_carriers": text != source.read_text(encoding="utf-8")}

    report["ok"] = not problems
    (args.out / "landing_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in report["files"]:
        print(f"{'ok ' if row['ok'] else 'NOT'} {row['path']}: {row['method']}" + (f" -> {row['restamped_to']}" if row.get("restamped_to") else "") + (f" (conflicts {row['conflicts']})" if row.get("conflicts") else ""))
    for site in report["stamp_sites"]:
        print("stamp", json.dumps(site))
    if not report["landing_date_is_today_utc"]:
        print(f"NOTE: --landing-date {args.landing_date} is not today's UTC date ({today}). A stamp carries the UTC date of the day the PR lands.")
    for line in problems:
        print("PROBLEM", line)
    print(f"main {str(report['main_sha'])[:8]} <- carrier base {base[:8]}; {'DRY RUN, nothing written' if args.dry_run else ('written into ' + str(dest) if report['written_into_dest'] else 'NOTHING WRITTEN')}; texts in {texts_dir}; {'OK' if report['ok'] else 'NOT OK'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
