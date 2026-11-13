#!/usr/bin/env python3
"""Rebuild the N-2 carrier's four shared documents on this worktree's HEAD, set every stamp by rule, and prove the result changes main by the carrier's own lines only.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use build step)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-12
Status:      ad-hoc -- one-off (landing step of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); util/ad-hoc/2026-11-11_flood4r2_n2-r2_assemble.py
             (the copy-or-three-way step, which stops at a conflict and sets no stamp)

The carrier was built on an older ``main``. Since then other changes bumped the same two document
versions and added entries at the same points, so a three-way merge of ``docs/REFERENCE.md`` and
``CHANGELOG.md`` conflicts, and the Version lines of ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``
merge with no conflict at a value another change already took. This does the whole step by rule.

For each of ``CHANGELOG.md``, ``juniper-service-core/CHANGELOG.md``, ``docs/REFERENCE.md`` and
``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``:

1. ``git merge-file -p <carrier's copy> <the carrier base's copy> <HEAD's copy>``.
2. Each conflict region is resolved by its shape, and any other shape is refused:
   - a CHANGELOG region whose two sides are whole entries: both are kept, HEAD's first, one blank
     line between them;
   - a region of stamp lines (Version / Last Updated / Date, with unchanged lines between): HEAD's
     side, because step 3 sets every stamp anyway;
   - a region of Version History rows: HEAD's rows, then the carrier's.
3. Stamps, never taken from what the merge produced:
   - each document's Version is HEAD's + 1 in its last component, header and footer alike;
   - every date site (header and footer) is ``--date``;
   - the carrier's own Version History row (the one row of its table the base does not have) takes
     that version and date and goes directly after HEAD's highest-version row;
   - the root CHANGELOG entry's pointer bullet names the two new versions.
4. The proof. The lines the result adds to and removes from HEAD's copy are compared, as multisets,
   with the lines the carrier's copy adds to and removes from the base's copy. Every line of
   difference must be a stamp line, the re-stamped history row or the re-stamped pointer bullet;
   anything else fails the run.
5. Text changes, after the proof and outside it. ``--text-changes`` names a JSON list of
   ``{"path", "old", "new", "why"}``: each ``old`` must occur exactly once in that file's rebuilt
   text and is replaced by ``new``. These are the sentences a later owner ruling made stale; they
   are kept apart from the rebuild so that the proof above stays a statement about the merge.

The carrier tree is read as plain files; git runs only in this worktree. The four results are
written into this worktree unless ``--check`` is given, which compares them with the files already
here instead. The inputs, the merged text, the text the rules alone give and each result's diff
against HEAD's copy are kept under ``--scratch``/rebuild/.

Exit status: 0 when all four files were rebuilt (or, with ``--check``, equal the worktree's) and
the proof holds; 1 on a refused conflict, a text change that does not apply once, a failed proof or
a ``--check`` difference; 2 on a usage error.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-12_flood4r2_n2-land_rebuild_docs.py --carrier <carrier tree> \\
        --carrier-base <commit> --date <YYYY-MM-DD> --scratch <scratch dir> --out <report.json> \\
        [--text-changes <changes.json>] [--check]
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOGS = ("CHANGELOG.md", "juniper-service-core/CHANGELOG.md")
STAMPED = {"docs/REFERENCE.md": True, "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md": False}  # path -> has a Version History table
POINTER_FILE = "CHANGELOG.md"
EDGE_LINES = 12
STAMP = re.compile(r"^(?P<label>\*\*(?P<field>Version|Last Updated|Date)(?::\*\*|\*\*:) )(?P<value>\S+)$")
ROW = re.compile(r"^\| (?P<version>\d+\.\d+\.\d+)(?P<pad>\s+)\| (?P<date>\d{4}-\d{2}-\d{2}) \| (?P<rest>.*)$")
POINTER = re.compile(r"^(?P<a>\s*- `docs/REFERENCE\.md` \()(?P<reference>\d+\.\d+\.\d+)(?P<b>\) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` \()(?P<cheatsheet>\d+\.\d+\.\d+)(?P<c>\) describe the refusal.*)$")
HISTORY_HEADING = "## Version History"


class Refused(Exception):
    """A conflict or a stamp site this script has no rule for."""


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False)


def _blob(ref: str, rel: str) -> bytes:
    shown = _git("show", f"{ref}:{rel}")
    if shown.returncode != 0:
        raise Refused(f"{ref} has no {rel}")
    return shown.stdout


def _lines(data: bytes) -> list[str]:
    return data.decode("utf-8").split("\n")


def _delta(old: list[str], new: list[str]) -> tuple[Counter, Counter]:
    """The lines ``new`` adds to and removes from ``old``, as multisets."""
    added: Counter = Counter()
    removed: Counter = Counter()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            removed.update(old[i1:i2])
        if tag in ("replace", "insert"):
            added.update(new[j1:j2])
    return added, removed


def _bump(version: str) -> str:
    parts = version.split(".")
    return ".".join([*parts[:-1], str(int(parts[-1]) + 1)])


def _regions(merged: list[str]) -> list[tuple[int, int, int]]:
    """Each conflict region of a ``git merge-file`` output as (opening marker, separator, closing marker) line indexes."""
    found = []
    opened = separator = None
    for index, line in enumerate(merged):
        if opened is None:
            if line.startswith("<<<<<<< "):
                opened = index
        elif separator is None:
            if line == "=======":
                separator = index
        elif line.startswith(">>>>>>> "):
            found.append((opened, separator, index))
            opened = separator = None
    if opened is not None:
        raise Refused("a conflict region is not closed")
    return found


def _is_stamp_region(ours: list[str], theirs: list[str]) -> bool:
    if len(ours) != len(theirs) or not ours:
        return False
    changed = 0
    for mine, main in zip(ours, theirs):
        if mine == main:
            continue
        left, right = STAMP.match(mine), STAMP.match(main)
        if left is None or right is None or left.group("field") != right.group("field"):
            return False
        changed += 1
    return changed > 0


def _is_entry(side: list[str]) -> bool:
    return bool(side) and side[0].startswith("- **") and not any(line.startswith("#") for line in side)


def _resolve(rel: str, merged: list[str]) -> tuple[list[str], list[dict]]:
    """Replace every conflict region by its rule's text; return the text and what was done."""
    out: list[str] = []
    notes = []
    cursor = 0
    for opened, separator, closed in _regions(merged):
        ours, theirs = merged[opened + 1 : separator], merged[separator + 1 : closed]
        out.extend(merged[cursor:opened])
        note = {"at_merged_line": opened + 1, "carrier_lines": len(ours), "main_lines": len(theirs)}
        if rel in CHANGELOGS and _is_entry(ours) and _is_entry(theirs):
            out.extend([*theirs, "", *ours])
            note["rule"] = "two whole entries: both kept, main's first, one blank line between"
        elif rel in STAMPED and _is_stamp_region(ours, theirs):
            out.extend(theirs)
            note["rule"] = "stamp lines: main's side (every stamp is then set by rule)"
        elif rel in STAMPED and all(ROW.match(line) for line in [*ours, *theirs]):
            out.extend([*theirs, *ours])
            note["rule"] = "Version History rows: main's rows, then the carrier's (re-stamped and placed by rule)"
        else:
            raise Refused(f"{rel}: no rule for the conflict at merged line {opened + 1} ({len(ours)} carrier lines against {len(theirs)} of main's)")
        notes.append(note)
        cursor = closed + 1
    out.extend(merged[cursor:])
    return out, notes


def _stamp_sites(lines: list[str]) -> list[dict]:
    """The stamp lines in the file's first and last few lines: 1-based line, field, value, and where it sits."""
    sites = []
    for index, line in enumerate(lines):
        if index < EDGE_LINES or index >= len(lines) - EDGE_LINES:
            match = STAMP.match(line)
            if match:
                sites.append({"line": index + 1, "field": match.group("field"), "value": match.group("value"), "where": "header" if index < EDGE_LINES else "footer"})
    return sites


def _history_rows(lines: list[str]) -> list[str]:
    start = lines.index(HISTORY_HEADING)
    stop = next((index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")), len(lines))
    return [line for line in lines[start:stop] if ROW.match(line)]


def _set_stamps(rel: str, lines: list[str], main: list[str], base: list[str], carrier: list[str], date: str) -> dict:
    """Set the Version and date sites of ``lines`` in place (and the history row, for a file that has one)."""
    main_sites = _stamp_sites(main)
    main_versions = {site["value"] for site in main_sites if site["field"] == "Version"}
    if len(main_versions) != 1:
        raise Refused(f"{rel}: main's header and footer Version disagree or are missing: {sorted(main_versions)}")
    main_version = main_versions.pop()
    new_version = _bump(main_version)
    sites = _stamp_sites(lines)
    if [(site["where"], site["field"]) for site in sites] != [(site["where"], site["field"]) for site in main_sites] or len(sites) != 4:
        raise Refused(f"{rel}: the result's stamp sites are not main's four")
    record = {"main_version": main_version, "new_version": new_version, "date": date, "sites": []}
    for site, main_site in zip(sites, main_sites):
        value = new_version if site["field"] == "Version" else date
        label = STAMP.match(lines[site["line"] - 1]).group("label")
        lines[site["line"] - 1] = label + value
        record["sites"].append({"field": f"{site['where']} {site['field']}", "line_on_main": main_site["line"], "text_on_main": main[main_site["line"] - 1], "old": main_site["value"], "new": value})
    if STAMPED[rel]:
        own = [row for row in _history_rows(carrier) if row not in set(_history_rows(base))]
        if len(own) != 1 or lines.count(own[0]) != 1:
            raise Refused(f"{rel}: expected one Version History row of the carrier's own, once in the merge; found {len(own)}")
        main_rows = _history_rows(main)
        highest = max(main_rows, key=lambda row: tuple(int(part) for part in ROW.match(row).group("version").split(".")))
        if lines.count(highest) != 1:
            raise Refused(f"{rel}: main's highest Version History row is not in the merge exactly once")
        parsed = ROW.match(own[0])
        row = f"| {new_version}{parsed.group('pad')}| {date} | {parsed.group('rest')}"
        lines.remove(own[0])
        lines.insert(lines.index(highest) + 1, row)
        record["history_row"] = {
            "carrier_row_starts": own[0][:60],
            "new_row_starts": row[:60],
            "placed_after_main_row": highest[:60],
            "main_highest_row_line_on_main": main.index(highest) + 1,
            "main_highest_is_main_version": ROW.match(highest).group("version") == main_version,
        }
    return record


def _set_pointer(lines: list[str], base: list[str], carrier: list[str], versions: dict[str, str]) -> dict:
    """Name the two new document versions in the root CHANGELOG entry's pointer bullet."""
    own_added, _ = _delta(base, carrier)
    own = [line for line in own_added if POINTER.match(line)]
    if len(own) != 1 or lines.count(own[0]) != 1:
        raise Refused(f"{POINTER_FILE}: expected one pointer bullet of the carrier's own, once in the merge; found {len(own)}")
    parsed = POINTER.match(own[0])
    new = parsed.group("a") + versions["docs/REFERENCE.md"] + parsed.group("b") + versions["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"] + parsed.group("c")
    at = lines.index(own[0])
    lines[at] = new
    return {"line_in_result": at + 1, "old": own[0].strip(), "new": new.strip()}


def _explained(line: str, row_rests: set[str]) -> bool:
    """Is this line one the stamp rules account for: a stamp line, the carrier's history row, or the pointer bullet?"""
    if STAMP.match(line) or POINTER.match(line):
        return True
    row = ROW.match(line)
    return row is not None and row.group("rest") in row_rests


def _prove(rel: str, base: list[str], carrier: list[str], main: list[str], result: list[str]) -> dict:
    own_added, own_removed = _delta(base, carrier)
    got_added, got_removed = _delta(main, result)
    row_rests = {ROW.match(line).group("rest") for line in own_added if ROW.match(line)} if rel in STAMPED else set()
    differences = {
        "added_to_main_but_not_the_carriers_own": sorted((got_added - own_added).elements()),
        "the_carriers_own_additions_not_added_to_main": sorted((own_added - got_added).elements()),
        "removed_from_main_but_not_the_carriers_own": sorted((got_removed - own_removed).elements()),
        "the_carriers_own_removals_not_removed_from_main": sorted((own_removed - got_removed).elements()),
    }
    unexplained = [line for group in differences.values() for line in group if not _explained(line, row_rests)]
    return {
        "carrier_vs_base": {"inserted_lines": sum(own_added.values()), "deleted_lines": sum(own_removed.values())},
        "result_vs_main": {"inserted_lines": sum(got_added.values()), "deleted_lines": sum(got_removed.values())},
        "differences_all_stamp_lines": {key: [line[:110] for line in value] for key, value in differences.items()},
        "unexplained": [line[:200] for line in unexplained],
        "holds": not unexplained,
    }


def _apply_text_changes(rel: str, text: str, changes: list[dict], row: dict) -> str:
    """Apply this file's recorded replacements, each exactly once, and note where each landed."""
    row["text_changes"] = []
    for change in changes:
        if change["path"] != rel:
            continue
        if text.count(change["old"]) != 1:
            raise Refused(f"{rel}: a text change's old text occurs {text.count(change['old'])} times in the rebuilt file, not once: {change['old'][:70]!r}")
        row["text_changes"].append({"at_line": text[: text.index(change["old"])].count("\n") + 1, "old_lines": change["old"].count("\n"), "new_lines": change["new"].count("\n"), "why": change.get("why", "")})
        text = text.replace(change["old"], change["new"], 1)
    return text


def _rebuild(rel: str, carrier_root: Path, base_ref: str, work: Path) -> tuple[dict, list[str], list[str], list[str], list[str]]:
    carrier_bytes = (carrier_root / rel).read_bytes()
    base_bytes, main_bytes = _blob(base_ref, rel), _blob("HEAD", rel)
    work.mkdir(parents=True, exist_ok=True)
    for name, data in (("carrier", carrier_bytes), ("base", base_bytes), ("main", main_bytes)):
        (work / name).write_bytes(data)
    merged = _git("merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(work / "carrier"), str(work / "base"), str(work / "main"))
    if merged.returncode < 0 or merged.returncode > 127:
        raise Refused(f"{rel}: git merge-file failed ({merged.returncode}): {merged.stderr.decode('utf-8', 'replace')}")
    (work / "merged_as_git_left_it").write_bytes(merged.stdout)
    lines, notes = _resolve(rel, _lines(merged.stdout))
    if len(notes) != merged.returncode:
        raise Refused(f"{rel}: merge-file reported {merged.returncode} conflicts and {len(notes)} regions were found")
    row = {"path": rel, "conflicts": merged.returncode, "resolved": notes, "carrier_sha256": hashlib.sha256(carrier_bytes).hexdigest(), "main_sha256": hashlib.sha256(main_bytes).hexdigest()}
    return row, lines, _lines(base_bytes), _lines(carrier_bytes), _lines(main_bytes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--carrier", type=Path, required=True, help="the carrier tree (read as plain files)")
    parser.add_argument("--carrier-base", required=True, help="the commit the carrier's copies were made on")
    parser.add_argument("--date", required=True, help="the landing date in UTC, YYYY-MM-DD: every date site takes it")
    parser.add_argument("--scratch", type=Path, required=True, help="a scratch directory in this worktree's tmp/")
    parser.add_argument("--out", type=Path, required=True, help="the JSON report to write")
    parser.add_argument("--text-changes", type=Path, help="a JSON list of {path, old, new, why}: replacements made once each, after the proof")
    parser.add_argument("--check", action="store_true", help="write nothing into the worktree: compare the results with the files already there")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error("--date is YYYY-MM-DD")
    changes: list[dict] = []
    if args.text_changes is not None:
        with open(args.text_changes, encoding="utf-8") as fh:
            changes = json.load(fh)
        strangers = sorted({change["path"] for change in changes} - {*STAMPED, *CHANGELOGS})
        if strangers:
            parser.error(f"--text-changes names files this script does not rebuild: {strangers}")

    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    origin_main = _git("rev-parse", "origin/main").stdout.decode().strip()
    report = {"head": head, "origin_main": origin_main, "head_is_origin_main": head == origin_main, "carrier": str(args.carrier), "carrier_base": args.carrier_base, "date": args.date, "text_changes": str(args.text_changes) if args.text_changes is not None else None, "mode": "check" if args.check else "write", "files": []}
    built: dict[str, tuple[dict, list[str], list[str], list[str], list[str]]] = {}
    versions: dict[str, str] = {}
    texts: dict[str, str] = {}
    try:
        for rel in (*STAMPED, *CHANGELOGS):
            built[rel] = _rebuild(rel, args.carrier, args.carrier_base, args.scratch / "rebuild" / rel.replace("/", "__"))
            row, lines, base, carrier, main_lines = built[rel]
            if rel in STAMPED:
                row["stamps"] = _set_stamps(rel, lines, main_lines, base, carrier, args.date)
                versions[rel] = row["stamps"]["new_version"]
            if rel == POINTER_FILE:
                row["pointer_bullet"] = _set_pointer(lines, base, carrier, versions)
            row["proof"] = _prove(rel, base, carrier, main_lines, lines)
            texts[rel] = _apply_text_changes(rel, "\n".join(lines), changes, row)
    except Refused as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 1

    ok = True
    for rel, (row, lines, _base, _carrier, main_lines) in built.items():
        text = texts[rel]
        final = text.split("\n")
        work = args.scratch / "rebuild" / rel.replace("/", "__")
        (work / "result_by_rule").write_text("\n".join(lines), encoding="utf-8")
        (work / "result").write_text(text, encoding="utf-8")
        diff = difflib.unified_diff(main_lines, final, fromfile=f"main/{rel}", tofile=f"result/{rel}", lineterm="", n=0)
        (work / "result_vs_main.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")
        added, removed = _delta(main_lines, final)
        row["final_vs_main"] = {"inserted_lines": sum(added.values()), "deleted_lines": sum(removed.values())}
        row["result_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if rel in STAMPED:
            for site, now in zip(row["stamps"]["sites"], _stamp_sites(final)):
                site["line_in_result"] = now["line"]
            if "history_row" in row["stamps"]:
                row["stamps"]["history_row"]["line_in_result"] = next(index + 1 for index, line in enumerate(final) if line.startswith(row["stamps"]["history_row"]["new_row_starts"]))
        target = REPO_ROOT / rel
        if args.check:
            row["equals_worktree"] = target.read_bytes() == text.encode("utf-8")
            ok = ok and row["equals_worktree"]
        else:
            target.write_text(text, encoding="utf-8")
        ok = ok and row["proof"]["holds"]
        report["files"].append(row)
        print(
            f"{rel}: conflicts {row['conflicts']}; by rule vs main +{row['proof']['result_vs_main']['inserted_lines']} -{row['proof']['result_vs_main']['deleted_lines']}; "
            f"carrier vs its base +{row['proof']['carrier_vs_base']['inserted_lines']} -{row['proof']['carrier_vs_base']['deleted_lines']}; proof {'holds' if row['proof']['holds'] else 'FAILS'}; "
            f"text changes {len(row['text_changes'])}; final vs main +{row['final_vs_main']['inserted_lines']} -{row['final_vs_main']['deleted_lines']}" + (f"; equals worktree {row['equals_worktree']}" if args.check else "")
        )
        if rel in STAMPED:
            print(f"    Version {row['stamps']['main_version']} -> {row['stamps']['new_version']}, dates {args.date}")
    report["ok"] = ok
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
