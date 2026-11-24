#!/usr/bin/env python3
"""
Check the ml-propose carrier's landing on the main of the day from the landed bytes, independently of the landing helper.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The carrier's landing helper checks its own result with a multiset of moved lines, which cannot say WHERE a line
went. This script reads the landed worktree (a detached worktree of origin/main that the helper wrote into) and
re-derives, with zero-context diffs:

* the status of the landed tree against the manifest's file list;
* for every file, the change blocks main -> landed against the change blocks base -> carrier, stamps normalised,
  each with the line above and the line below it (so a block that moved shows);
* docs/REFERENCE.md's stamp (header == footer, main's + one patch), every Version History row, the versions that
  occur twice, main's highest row and the row directly above the carrier's row;
* the runbook's stamp and CHANGELOG.md's entry (its release heading, its subsection, its place among the entries);
* every line a named merged commit ADDED to a file the carrier touches that the landing REMOVES (a revert).

Usage:
    python3 <this> --landed <landing worktree> --out <dir> --since <sha> [--since <sha> ...]
Exit 0 = nothing unexpected; 1 otherwise (each problem is printed on a line that starts with PROBLEM).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the validator's own landing worktree
import sys
from collections import Counter
from pathlib import Path

ML = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml"
CARRIER = ML / ".claude" / "worktrees" / "agent-a211deee35ec85ad3"
DELIVERABLES = CARRIER / "tmp" / "flood4r2" / "ml-propose" / "r3b"
REFERENCE = "docs/REFERENCE.md"
RUNBOOK = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
CHANGELOG = "CHANGELOG.md"
REF_VERSION = re.compile(r"^\*\*Version:\*\* (\d+\.\d+\.\d+)$")
REF_DATE = re.compile(r"^\*\*Last Updated:\*\* (\d{4}-\d{2}-\d{2})$")
HISTORY_ROW = re.compile(r"^\| (\d+\.\d+\.\d+)\s+\| (\d{4}-\d{2}-\d{2}) \|")
RUNBOOK_VERSION = re.compile(r"^\*\*Version\*\*: (\d+\.\d+\.\d+)$")
RUNBOOK_DATE = re.compile(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def run(root: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=root, capture_output=True, check=False)  # nosec B603 B607


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(root: Path, rev: str, path: str) -> "bytes | None":
    done = run(root, "show", f"{rev}:{path}")
    return done.stdout if done.returncode == 0 else None


def normalise(path: str, line: str) -> str:
    """A line with every stamp value replaced by a placeholder."""
    if path == REFERENCE:
        line = REF_VERSION.sub("**Version:** <V>", line)
        line = REF_DATE.sub("**Last Updated:** <D>", line)
        row = HISTORY_ROW.match(line)
        if row:
            line = "| <V> | <D> |" + line[row.end() :]
    elif path == RUNBOOK:
        line = RUNBOOK_VERSION.sub("**Version**: <V>", line)
        line = RUNBOOK_DATE.sub("**Last Updated**: <D>", line)
    return line


def blocks(root: Path, old_file: Path, new_file: Path, path: str) -> list:
    """Change blocks old -> new from a zero-context diff: removed lines, added lines, and the neighbours in ``new``."""
    done = run(root, "diff", "--no-index", "--no-color", "-U0", str(old_file), str(new_file))
    if done.returncode not in (0, 1):
        raise SystemExit("diff failed: " + done.stderr.decode("utf-8", "replace"))
    new_lines = new_file.read_text(encoding="utf-8").split("\n")
    found, current = [], None
    for line in done.stdout.decode("utf-8").split("\n"):
        head = HUNK.match(line)
        if head:
            start, count = int(head.group(3)), int(head.group(4) if head.group(4) is not None else 1)
            current = {"new_start": start, "new_count": count, "removed": [], "added": []}
            first = start if count else start + 1
            current["above"] = new_lines[first - 2] if first >= 2 else None
            current["below"] = new_lines[first - 1 + count] if first - 1 + count < len(new_lines) else None
            found.append(current)
        elif current is not None and line.startswith("-") and not line.startswith("---"):
            current["removed"].append(line[1:])
        elif current is not None and line.startswith("+") and not line.startswith("+++"):
            current["added"].append(line[1:])
    for block in found:
        block["key"] = json.dumps([[normalise(path, item) for item in block["removed"]], [normalise(path, item) for item in block["added"]]])
    return found


STAMP_LINES = frozenset({"**Version:** <V>", "**Last Updated:** <D>", "**Version**: <V>", "**Last Updated**: <D>"})


def stamp_only(key: str) -> bool:
    """True for a change block whose removed and added lines are all stamp lines."""
    removed, added = json.loads(key)
    return bool(removed or added) and set(removed) | set(added) <= STAMP_LINES


def history(text: str) -> list:
    return [(index + 1, m.group(1), m.group(2)) for index, line in enumerate(text.split("\n")) if (m := HISTORY_ROW.match(line))]


def as_tuple(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def check_reference(main: str, landed: str, report: dict, problems: list) -> None:
    main_lines, landed_lines = main.split("\n"), landed.split("\n")
    stamp = {}
    for label, lines in (("main", main_lines), ("landed", landed_lines)):
        stamp[label] = {
            "versions": [(index + 1, m.group(1)) for index, line in enumerate(lines) if (m := REF_VERSION.match(line))],
            "dates": [(index + 1, m.group(1)) for index, line in enumerate(lines) if (m := REF_DATE.match(line))],
        }
    main_rows, landed_rows = history(main), history(landed)
    main_highest = max(main_rows, key=lambda row: as_tuple(row[1]))
    main_stamp = stamp["main"]["versions"][0][1]
    landed_versions = [value for _, value in stamp["landed"]["versions"]]
    expected = ".".join(str(part) for part in (*as_tuple(main_stamp)[:2], as_tuple(main_stamp)[2] + 1))
    duplicates_main = sorted(version for version, count in Counter(row[1] for row in main_rows).items() if count > 1)
    duplicates_landed = sorted(version for version, count in Counter(row[1] for row in landed_rows).items() if count > 1)
    new_rows = [row for row in landed_rows if row[1] not in {item[1] for item in main_rows}]
    info = {
        "stamp": stamp,
        "main_stamp": main_stamp,
        "expected_landed_stamp": expected,
        "history_rows_main": len(main_rows),
        "history_rows_landed": len(landed_rows),
        "main_highest_row": {"line": main_highest[0], "version": main_highest[1], "date": main_highest[2]},
        "versions_twice_on_main": duplicates_main,
        "versions_twice_landed": duplicates_landed,
        "rows_new_in_landed": [{"line": row[0], "version": row[1], "date": row[2]} for row in new_rows],
    }
    if len(stamp["main"]["versions"]) != 2 or len({value for _, value in stamp["main"]["versions"]}) != 1:
        problems.append(f"{REFERENCE}: main's header/footer Version are not one value twice")
    if landed_versions != [expected, expected]:
        problems.append(f"{REFERENCE}: landed header/footer Version {landed_versions}, expected {expected} twice")
    if main_highest[1] != main_stamp:
        problems.append(f"{REFERENCE}: main's highest history row {main_highest[1]} is not main's stamp {main_stamp}")
    if duplicates_landed != duplicates_main:
        problems.append(f"{REFERENCE}: versions twice in the landed history {duplicates_landed}, on main {duplicates_main}")
    if len(new_rows) != 1 or new_rows[0][1] != expected:
        problems.append(f"{REFERENCE}: new history rows {new_rows}, expected one row for {expected}")
    else:
        line = new_rows[0][0]
        above = HISTORY_ROW.match(landed_lines[line - 2])
        below = landed_lines[line]
        info["row_directly_above_the_new_row"] = landed_lines[line - 2][:80]
        info["row_directly_below_the_new_row"] = below[:80]
        info["new_row_text"] = landed_lines[line - 1]
        if above is None or above.group(1) != main_highest[1]:
            problems.append(f"{REFERENCE}: the {expected} row does not directly follow main's highest row {main_highest[1]}")
        if landed_lines[line - 2] != main_lines[main_highest[0] - 1]:
            problems.append(f"{REFERENCE}: the row above the new row is not main's highest row, byte for byte")
        if above is not None and as_tuple(expected) <= as_tuple(above.group(1)):
            problems.append(f"{REFERENCE}: the new row's version is not higher than the row above it")
    report["reference"] = info


def check_runbook(main: str, landed: str, report: dict, problems: list) -> None:
    info = {}
    for label, text in (("main", main), ("landed", landed)):
        lines = text.split("\n")
        info[label] = {
            "versions": [(index + 1, m.group(1)) for index, line in enumerate(lines) if (m := RUNBOOK_VERSION.match(line))],
            "dates": [(index + 1, m.group(1)) for index, line in enumerate(lines) if (m := RUNBOOK_DATE.match(line))],
        }
    main_version = info["main"]["versions"][0][1]
    expected = ".".join(str(part) for part in (*as_tuple(main_version)[:2], as_tuple(main_version)[2] + 1))
    if [value for _, value in info["landed"]["versions"]] != [expected]:
        problems.append(f"runbook: landed Version {info['landed']['versions']}, expected {expected}")
    report["runbook"] = info


def check_changelog(main: str, landed: str, entry: str, report: dict, problems: list) -> None:
    info = {"entry_occurrences_landed": landed.count(entry), "entry_occurrences_main": main.count(entry)}
    if info["entry_occurrences_landed"] != 1:
        problems.append(f"{CHANGELOG}: the entry occurs {info['entry_occurrences_landed']} times")
        report["changelog"] = info
        return
    head = landed[: landed.index(entry)].split("\n")
    tail = landed[landed.index(entry) + len(entry) :].split("\n")
    releases = [line for line in head if line.startswith("## ")]
    sections = [index for index, line in enumerate(head) if line.startswith("### ")]
    entries_above = [line for line in head[sections[-1] :] if line.startswith("- ")]
    entries_below = []
    for line in tail:
        if line.startswith("## ") or line.startswith("### "):
            break
        if line.startswith("- "):
            entries_below.append(line)
    info.update(
        {
            "release_headings_above": releases,
            "subsection": head[sections[-1]] if sections else None,
            "subsections_above_in_this_release": [head[index] for index in sections],
            "entries_above_in_subsection": len(entries_above),
            "entries_below_in_subsection": len(entries_below),
            "entry_above_starts": entries_above[-1][:110] if entries_above else None,
            "entry_below_starts": entries_below[0][:110] if entries_below else None,
            "landed_first_line_of_entry": landed[: landed.index(entry)].count("\n") + 1,
        }
    )
    unreleased = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", main, re.MULTILINE | re.DOTALL)
    info["entries_in_mains_unreleased"] = sum(1 for line in (unreleased.group(1) if unreleased else "").split("\n") if line.startswith("- "))
    if releases != ["## [Unreleased]"] or info["subsection"] != "### Fixed":
        problems.append(f"{CHANGELOG}: the entry is not under the top [Unreleased] -> ### Fixed (release headings above it: {releases})")
    elif not entries_above and info["entries_in_mains_unreleased"]:
        problems.append(f"{CHANGELOG}: the entry is the first of ### Fixed although main's [Unreleased] holds {info['entries_in_mains_unreleased']} entries")
    report["changelog"] = info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--landed", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--since", action="append", default=[], help="a merged commit whose added lines must survive the landing")
    args = parser.parse_args()
    landed, out = args.landed.resolve(), args.out.resolve()
    work = out / "inputs"
    work.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((DELIVERABLES / "manifest.json").read_text(encoding="utf-8"))
    base = manifest["base_sha"]
    head = run(landed, "rev-parse", "HEAD").stdout.decode().strip()
    status = [line for line in run(landed, "status", "--porcelain").stdout.decode().split("\n") if line]
    report = {"landed": str(landed), "head": head, "base_sha": base, "status_lines": status, "files": []}
    problems: list = []

    listed = {entry["path"]: entry for entry in manifest["files"]}
    seen = {line[3:] for line in status}
    if seen != set(listed):
        problems.append(f"status differs from the manifest's list: only in status {sorted(seen - set(listed))}, only in manifest {sorted(set(listed) - seen)}")

    removed_by_landing: dict = {}
    for path, entry in sorted(listed.items()):
        carrier_bytes = (CARRIER / path).read_bytes()
        landed_bytes = (landed / path).read_bytes()
        base_bytes, main_bytes = blob(landed, base, path), blob(landed, "HEAD", path)
        row = {"path": path, "carrier_sha256": sha256(carrier_bytes), "landed_sha256": sha256(landed_bytes), "manifest_sha256_ok": sha256(carrier_bytes) == entry["sha256"], "landed_equals_carrier": landed_bytes == carrier_bytes}
        if base_bytes is None or main_bytes is None:
            row["kind"] = "added"
            if base_bytes is not None or main_bytes is not None or not row["landed_equals_carrier"]:
                problems.append(f"{path}: an added file that is on base or main, or whose landed bytes are not the carrier's")
            report["files"].append(row)
            continue
        row["kind"] = "modified"
        row["main_equals_base"] = main_bytes == base_bytes
        name = Path(path).name
        files = {}
        for label, data in (("base", base_bytes), ("main", main_bytes), ("carrier", carrier_bytes), ("landed", landed_bytes)):
            files[label] = work / f"{name}.{label}"
            files[label].write_bytes(data)
        own = blocks(landed, files["base"], files["carrier"], path)
        got = blocks(landed, files["main"], files["landed"], path)
        # A block made of stamp lines only is compared by the stamp checks below, not here: main's date can already be
        # the landing date, so the carrier's date edit has no twin in the landing and the block shapes differ.
        own_keys = Counter(block["key"] for block in own if not stamp_only(block["key"]))
        got_keys = Counter(block["key"] for block in got if not stamp_only(block["key"]))
        if path == CHANGELOG and own_keys != got_keys:
            # After a release proposal emptied [Unreleased], the entry is the section's first: the landing then adds
            # the carrier's lines plus one `### Fixed` heading and one blank line, and removes nothing.
            own_added = Counter(line for block in own for line in block["added"])
            got_added = Counter(line for block in got for line in block["added"])
            if not any(block["removed"] for block in own + got) and not (own_added - got_added) and (got_added - own_added) == Counter({"### Fixed": 1, "": 1}):
                row["changelog_entry_opens_a_new_fixed_subsection"] = True
                got_keys = own_keys
        row["blocks_carrier_vs_base"] = len(own)
        row["blocks_landed_vs_main"] = len(got)
        row["lines_added_landed_vs_main"] = sum(len(block["added"]) for block in got)
        row["lines_removed_landed_vs_main"] = sum(len(block["removed"]) for block in got)
        row["lines_added_carrier_vs_base"] = sum(len(block["added"]) for block in own)
        row["lines_removed_carrier_vs_base"] = sum(len(block["removed"]) for block in own)
        row["blocks_only_in_the_landing"] = [json.loads(key) for key in (got_keys - own_keys).elements()]
        row["blocks_only_in_the_carrier"] = [json.loads(key) for key in (own_keys - got_keys).elements()]
        if row["blocks_only_in_the_landing"] or row["blocks_only_in_the_carrier"]:
            problems.append(f"{path}: the landing's change blocks are not the carrier's (stamps normalised): {len(row['blocks_only_in_the_landing'])} only in the landing, {len(row['blocks_only_in_the_carrier'])} only in the carrier")
        moved = []
        by_key = {block["key"]: block for block in own}
        for block in got:
            twin = by_key.get(block["key"])
            if twin is not None and (normalise(path, block["above"] or "") != normalise(path, twin["above"] or "") or normalise(path, block["below"] or "") != normalise(path, twin["below"] or "")):
                moved.append(
                    {
                        "landed_line": block["new_start"],
                        "carrier_line": twin["new_start"],
                        "first_added_line": (block["added"] or [""])[0][:100],
                        "landed_above": (block["above"] or "")[:100],
                        "carrier_above": (twin["above"] or "")[:100],
                        "landed_below": (block["below"] or "")[:100],
                        "carrier_below": (twin["below"] or "")[:100],
                    }
                )
        row["blocks_whose_neighbours_differ_from_the_carriers"] = moved
        removed_by_landing[path] = Counter(line for block in got for line in block["removed"])
        (out / f"{name}.landed-vs-main.diff").write_bytes(run(landed, "diff", "--no-color", "HEAD", "--", path).stdout)
        (out / f"{name}.carrier-vs-base.diff").write_bytes(run(landed, "diff", "--no-index", "--no-color", str(files["base"]), str(files["carrier"])).stdout)
        if path == REFERENCE:
            check_reference(main_bytes.decode("utf-8"), landed_bytes.decode("utf-8"), report, problems)
        elif path == RUNBOOK:
            check_runbook(main_bytes.decode("utf-8"), landed_bytes.decode("utf-8"), report, problems)
        elif path == CHANGELOG:
            check_changelog(main_bytes.decode("utf-8"), landed_bytes.decode("utf-8"), (DELIVERABLES / "changelog_entry.txt").read_text(encoding="utf-8"), report, problems)
        if b"<<<<<<<" in landed_bytes or b">>>>>>>" in landed_bytes:
            problems.append(f"{path}: conflict markers")
        report["files"].append(row)

    report["reverts"] = []
    for sha in args.since:
        named = run(landed, "show", "--no-color", "--format=%H %s", "--name-only", sha).stdout.decode().split("\n")
        touched = [line for line in named[1:] if line]
        entry = {"commit": named[0], "files_it_touched": len(touched), "carrier_files_it_touched": sorted(set(touched) & set(listed)), "lines_it_added_that_the_landing_removes": []}
        for path in entry["carrier_files_it_touched"]:
            done = run(landed, "diff", "--no-color", "-U0", f"{sha}^", sha, "--", path).stdout.decode("utf-8")
            added = Counter(line[1:] for line in done.split("\n") if line.startswith("+") and not line.startswith("+++"))
            overlap = added & removed_by_landing.get(path, Counter())
            for line, count in overlap.items():
                entry["lines_it_added_that_the_landing_removes"].append({"path": path, "count": count, "line": line[:160]})
                if not (REF_VERSION.match(line) or REF_DATE.match(line) or RUNBOOK_VERSION.match(line) or RUNBOOK_DATE.match(line)):
                    problems.append(f"{path}: the landing removes a line {sha[:8]} added: {line[:120]}")
        report["reverts"].append(entry)

    report["problems"] = problems
    report["ok"] = not problems
    (out / "landing_check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in report["files"]:
        if row["kind"] == "added":
            continue
        print(f"{row['path']}: main==base {row['main_equals_base']}; landed==carrier {row['landed_equals_carrier']}; +{row['lines_added_landed_vs_main']}/-{row['lines_removed_landed_vs_main']} vs main, +{row['lines_added_carrier_vs_base']}/-{row['lines_removed_carrier_vs_base']} carrier vs base; blocks {row['blocks_landed_vs_main']}/{row['blocks_carrier_vs_base']}; neighbours differ: {len(row['blocks_whose_neighbours_differ_from_the_carriers'])}")
    print("added files equal to the carrier's:", sum(1 for row in report["files"] if row["kind"] == "added" and row["landed_equals_carrier"]), "of", sum(1 for row in report["files"] if row["kind"] == "added"))
    print("reference:", json.dumps({key: report["reference"][key] for key in ("main_stamp", "expected_landed_stamp", "main_highest_row", "versions_twice_on_main", "versions_twice_landed", "rows_new_in_landed")}))
    print("runbook:", json.dumps(report["runbook"]))
    print("changelog:", json.dumps(report["changelog"]))
    for entry in report["reverts"]:
        print("since", entry["commit"][:60], "| carrier files:", entry["carrier_files_it_touched"], "| removed lines it added:", entry["lines_it_added_that_the_landing_removes"])
    for line in problems:
        print("PROBLEM", line)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
