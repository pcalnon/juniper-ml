#!/usr/bin/env python3
"""
Re-derive the round-2 "ml-docs" carrier on any juniper-ml main: three-way its stamp-free content, then stamp by rule.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)

Two modes.

``neutralize`` takes the carrier's copies of its six files and the commit they were built on, and writes the
carrier's CONTENT with no stamp in it: every header and footer ``Version`` / date line set back to the base's value,
the carrier's own Version History row cut out of docs/REFERENCE.md (kept as ``history_row.txt``, its third cell
only), and its CHANGELOG.md entry cut out (kept as ``changelog_entry.txt``). A three-way of that content onto a
later main then never meets a stamp, a history row or a CHANGELOG position, which are the three places two
carriers that land one after the other always collide.

``derive`` puts the carrier on a main (``--main <ref>``, or ``--main-dir <dir>`` holding a main's copies):

1. each document is ``git merge-file -p <content> <base copy> <main copy>``; a conflict stops the run (exit 1)
   unless ``<content dir>/resolutions.json`` records a resolution for that exact block (its carrier side and its
   main side, byte for byte: a list of ``{"name", "path", "carrier", "main", "resolved"}``);
2. each of docs/REFERENCE.md, docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md, docs/DOCUMENTATION_OVERVIEW.md and
   docs/QUICK_START.md is bumped ONE patch step from main's value, header and footer alike (main's header and
   footer must agree), and both date lines take ``--landing-date``;
3. docs/REFERENCE.md gains its Version History row directly after main's highest row, and the new version may not
   already be a row;
4. CHANGELOG.md is main's copy with the entry appended to the group ``### Added`` of the TOP ``## [Unreleased]``,
   after that group's last entry (a group of that name is created first under the heading only when there is
   none). The entry may not already be in main's copy, and must end up there exactly once.

``.claude/agents/fleet-supervisor.md`` carries no stamp: it is merged only. Every stamp, date and position the run
set is printed as JSON (``--report`` writes it too). Nothing is written when any check fails.

``record`` stores one such resolution, read from a conflicted merge output and a file holding the resolved text.

Usage:
  2026-11-14_flood4r2_ml-docs_rederive.py neutralize --carrier-dir <dir> --base <ref> --out <content dir>
  2026-11-14_flood4r2_ml-docs_rederive.py record --merged <file> --resolved <file> --name <name> --path <doc>
      --content-dir <dir> [--content-dir <dir> ...]
  2026-11-14_flood4r2_ml-docs_rederive.py derive --content-dir <dir> --base <ref> (--main <ref> | --main-dir <dir>)
      --landing-date YYYY-MM-DD --out <tree> [--report <json>]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STAMPED = {
    "docs/REFERENCE.md": {"version": ("**Version:** ",), "date": ("**Last Updated:** ",), "history": True},
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md": {"version": ("**Version**: ", "**Version:** "), "date": ("**Date**: ", "**Last Updated:** "), "history": False},
    "docs/DOCUMENTATION_OVERVIEW.md": {"version": ("**Version:** ",), "date": ("**Last Updated:** ",), "history": False},
    "docs/QUICK_START.md": {"version": ("**Version:** ",), "date": ("**Last Updated:** ",), "history": False},
}
MERGED_ONLY = (".claude/agents/fleet-supervisor.md",)
CHANGELOG = "CHANGELOG.md"
ROW_MARKER = "Cursor flood-4 round-2 docs carrier"
ENTRY_MARKER = "- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts**"
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
ROW_RE = re.compile(r"^\| (?P<version>[^|]+?) +\| (?P<date>\d{4}-\d{2}-\d{2}) \| (?P<text>.*) \|$")


class DeriveError(Exception):
    """A check failed; nothing is written."""


def git_show(ref: str, path: str) -> str:
    """Return ``ref:path`` as text (the repository is the current directory)."""
    result = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def stamp_lines(lines: list[str], prefixes: tuple[str, ...], token: re.Pattern[str]) -> list[int]:
    """Indexes of the lines that are exactly a prefix followed by one token (a version or a date)."""
    found = []
    for index, line in enumerate(lines):
        for prefix in prefixes:
            if line.startswith(prefix) and token.fullmatch(line[len(prefix):].rstrip("\n")):
                found.append(index)
    return found


def stamp_values(text: str, doc: str) -> dict:
    """Read a document's header/footer version and date lines; there must be exactly two of each."""
    spec = STAMPED[doc]
    lines = text.splitlines(keepends=True)
    out = {}
    for kind, token in (("version", VERSION_RE), ("date", DATE_RE)):
        idx = stamp_lines(lines, spec[kind], token)
        if len(idx) != 2:
            raise DeriveError(f"{doc}: expected 2 {kind} stamp lines (header and footer), found {len(idx)} at {[i + 1 for i in idx]}")
        values = [token.search(lines[i]).group(0) for i in idx]
        out[kind] = {"lines": [i + 1 for i in idx], "values": values}
    return out


def set_stamps(text: str, doc: str, version: str, date: str) -> str:
    """Replace the two version lines and the two date lines' tokens."""
    spec = STAMPED[doc]
    lines = text.splitlines(keepends=True)
    for kind, token, value in (("version", VERSION_RE, version), ("date", DATE_RE, date)):
        for i in stamp_lines(lines, spec[kind], token):
            lines[i] = token.sub(value, lines[i], count=1)
    return "".join(lines)


def version_key(value: str) -> tuple[int, ...]:
    """Sort key of a dotted version."""
    return tuple(int(part) for part in value.split("."))


def bump(value: str) -> str:
    """One patch step."""
    parts = value.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def history_rows(lines: list[str]) -> list[tuple[int, str]]:
    """(index, version) of every Version History row whose version is a plain dotted triple."""
    try:
        start = lines.index("## Version History\n")
    except ValueError as exc:
        raise DeriveError("docs/REFERENCE.md: no '## Version History' heading") from exc
    rows = []
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            break
        match = ROW_RE.match(lines[index].rstrip("\n"))
        if match and VERSION_RE.fullmatch(match.group("version").strip()):
            rows.append((index, match.group("version").strip()))
    return rows


def split_entry(changelog: str) -> tuple[str, str]:
    """Cut the carrier's entry (its first line through the line before the next item or heading) out of a CHANGELOG."""
    lines = changelog.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(ENTRY_MARKER)]
    if len(starts) != 1:
        raise DeriveError(f"CHANGELOG.md: expected the carrier's entry once, found it {len(starts)} times")
    start = starts[0]
    end = start + 1
    while end < len(lines) and not lines[end].startswith(("- ", "### ", "## ")) and lines[end].strip():
        end += 1
    return "".join(lines[:start] + lines[end:]), "".join(lines[start:end])


def insert_entry(changelog: str, entry: str) -> tuple[str, dict]:
    """Append ``entry`` to ``### Added`` of the top ``## [Unreleased]``; report where."""
    if ENTRY_MARKER in changelog:
        raise DeriveError("CHANGELOG.md: main already holds the carrier's entry")
    lines = changelog.splitlines(keepends=True)
    tops = [i for i, line in enumerate(lines) if line.startswith("## [")]
    if not tops or lines[tops[0]].rstrip("\n") != "## [Unreleased]":
        raise DeriveError("CHANGELOG.md: the first '## [' heading is not '## [Unreleased]'")
    top = tops[0]
    end = tops[1] if len(tops) > 1 else len(lines)
    added = [i for i in range(top + 1, end) if lines[i].rstrip("\n") == "### Added"]
    created = False
    if len(added) > 1:
        raise DeriveError("CHANGELOG.md: [Unreleased] holds two '### Added' headings")
    if not added:
        lines[top + 1:top + 1] = ["\n", "### Added\n"]
        created = True
        tops = [i for i, line in enumerate(lines) if line.startswith("## [")]
        end = tops[1] if len(tops) > 1 else len(lines)
        added = [i for i in range(top + 1, end) if lines[i].rstrip("\n") == "### Added"]
    head = added[0]
    nxt = head + 1
    while nxt < end and not lines[nxt].startswith(("### ", "## ")):
        nxt += 1
    last = nxt - 1
    while last > head and not lines[last].strip():
        last -= 1
    at = last + 1
    block = entry if entry.endswith("\n") else entry + "\n"
    block = "\n" + block
    lines[at:at] = [block]
    result = "".join(lines)
    if result.count(ENTRY_MARKER) != 1:
        raise DeriveError("CHANGELOG.md: the entry is not in the result exactly once")
    return result, {"inserted_after_line": last + 1, "group_heading_line": head + 1, "group_created": created, "next_heading": lines[nxt + 1].rstrip("\n") if nxt + 1 < len(lines) else None}


def neutralize(args: argparse.Namespace) -> int:
    out = Path(args.out)
    for doc in list(STAMPED) + list(MERGED_ONLY):
        carrier = (Path(args.carrier_dir) / doc).read_text(encoding="utf-8")
        if doc in STAMPED:
            base_stamps = stamp_values(git_show(args.base, doc), doc)
            carrier = set_stamps(carrier, doc, base_stamps["version"]["values"][0], base_stamps["date"]["values"][0])
            if STAMPED[doc]["history"]:
                lines = carrier.splitlines(keepends=True)
                mine = [i for i, line in enumerate(lines) if ROW_RE.match(line.rstrip("\n")) and ROW_MARKER in line]
                if len(mine) != 1:
                    raise DeriveError(f"{doc}: expected the carrier's history row once, found {len(mine)}")
                text = ROW_RE.match(lines[mine[0]].rstrip("\n")).group("text")
                (out / "history_row.txt").parent.mkdir(parents=True, exist_ok=True)
                (out / "history_row.txt").write_text(text + "\n", encoding="utf-8")
                del lines[mine[0]]
                carrier = "".join(lines)
        dest = out / doc
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(carrier, encoding="utf-8")
    _, entry = split_entry((Path(args.carrier_dir) / CHANGELOG).read_text(encoding="utf-8"))
    (out / "changelog_entry.txt").write_text(entry, encoding="utf-8")
    (out / "content_base.txt").write_text(args.base + "\n", encoding="utf-8")
    print(f"content written to {out} (base {args.base}); entry {len(entry.splitlines())} lines")
    return 0


def resolve_conflicts(doc: str, text: str, resolutions: list[dict]) -> tuple[str, list[str]]:
    """Replace each conflict block by a recorded resolution whose carrier side AND main side match it exactly.

    A block with no exact match stops the run: a resolution recorded for one wording of main never applies to
    another wording, so a later change to main's side of the hunk comes back to a person.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    used: list[str] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("<<<<<<< carrier"):
            out.append(lines[index])
            index += 1
            continue
        middle = next((i for i in range(index + 1, len(lines)) if lines[i].startswith("=======")), None)
        end = next((i for i in range(middle + 1, len(lines)) if lines[i].startswith(">>>>>>> main")), None) if middle is not None else None
        if middle is None or end is None:
            raise DeriveError(f"{doc}: an unterminated conflict block at line {index + 1}")
        carrier_side = "".join(lines[index + 1:middle])
        main_side = "".join(lines[middle + 1:end])
        match = [r for r in resolutions if r["path"] == doc and r["carrier"] == carrier_side and r["main"] == main_side]
        if len(match) != 1:
            raise DeriveError(f"{doc}: conflict at line {index + 1} has no recorded resolution (main's side begins {main_side[:160]!r}): resolve by hand")
        out.append(match[0]["resolved"])
        used.append(f"{doc}: {match[0]['name']}")
        index = end + 1
    return "".join(out), used


def record(args: argparse.Namespace) -> int:
    """Append a resolution for the first conflict block of ``--merged`` (labels carrier / main) to resolutions.json."""
    lines = Path(args.merged).read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("<<<<<<< ")), None)
    if start is None:
        raise DeriveError(f"{args.merged}: no conflict block")
    middle = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("======="))
    end = next(i for i in range(middle + 1, len(lines)) if lines[i].startswith(">>>>>>> "))
    entry = {"name": args.name, "path": args.path, "carrier": "".join(lines[start + 1:middle]), "main": "".join(lines[middle + 1:end]), "resolved": Path(args.resolved).read_text(encoding="utf-8")}
    for content_dir in args.content_dir:
        target = Path(content_dir) / "resolutions.json"
        existing = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else []
        existing = [row for row in existing if row["name"] != args.name] + [entry]
        target.write_text(json.dumps(existing, indent=1) + "\n", encoding="utf-8")
        print(f"{target}: {len(existing)} resolution(s); recorded {args.name!r} for {args.path}")
    return 0


def main_copy(args: argparse.Namespace, path: str) -> str:
    if args.main_dir:
        return (Path(args.main_dir) / path).read_text(encoding="utf-8")
    return git_show(args.main, path)


def derive(args: argparse.Namespace) -> int:
    content = Path(args.content_dir)
    if not DATE_RE.fullmatch(args.landing_date):
        raise DeriveError("--landing-date must be YYYY-MM-DD")
    results: dict[str, str] = {}
    report: dict[str, object] = {"base": args.base, "main": args.main or f"dir:{args.main_dir}", "landing_date": args.landing_date, "docs": {}}
    resolutions_path = content / "resolutions.json"
    resolutions = json.loads(resolutions_path.read_text(encoding="utf-8")) if resolutions_path.is_file() else []
    with tempfile.TemporaryDirectory(dir=args.work_dir or str(content)) as tmp:
        for doc in list(STAMPED) + list(MERGED_ONLY):
            base_text = git_show(args.base, doc)
            main_text = main_copy(args, doc)
            paths = []
            for label, text in (("content", (content / doc).read_text(encoding="utf-8")), ("base", base_text), ("main", main_text)):
                path = Path(tmp) / f"{label}__{doc.replace('/', '__')}"
                path.write_text(text, encoding="utf-8")
                paths.append(str(path))
            merged = subprocess.run(["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", *paths], capture_output=True)
            if merged.returncode < 0 or merged.returncode > 127:
                raise DeriveError(f"{doc}: git merge-file failed (exit {merged.returncode})")
            text = merged.stdout.decode("utf-8")
            if merged.returncode != 0:
                text, used = resolve_conflicts(doc, text, resolutions)
                report.setdefault("resolved_conflicts", []).extend(used)
            entry_report: dict[str, object] = {}
            if doc in STAMPED:
                stamps = stamp_values(main_text, doc)
                header, footer = stamps["version"]["values"]
                if header != footer:
                    raise DeriveError(f"{doc}: main's header version {header} and footer version {footer} differ")
                new = bump(header)
                text = set_stamps(text, doc, new, args.landing_date)
                entry_report.update({"main_version": header, "version": new, "date": args.landing_date})
                if STAMPED[doc]["history"]:
                    lines = text.splitlines(keepends=True)
                    rows = history_rows(lines)
                    if any(version == new for _, version in rows):
                        raise DeriveError(f"{doc}: version {new} is already a Version History row")
                    top_index, top_version = max(rows, key=lambda row: version_key(row[1]))
                    row_text = (content / "history_row.txt").read_text(encoding="utf-8").rstrip("\n")
                    lines.insert(top_index + 1, f"| {new.ljust(7)} | {args.landing_date} | {row_text} |\n")
                    text = "".join(lines)
                    entry_report.update({"history_row_after": top_version, "history_row_line": top_index + 2})
                check = stamp_values(text, doc)
                if check["version"]["values"] != [new, new] or check["date"]["values"] != [args.landing_date, args.landing_date]:
                    raise DeriveError(f"{doc}: stamps did not take: {check}")
                entry_report["stamp_lines"] = {"version": check["version"]["lines"], "date": check["date"]["lines"]}
            if "<<<<<<<" in text or ">>>>>>>" in text:
                raise DeriveError(f"{doc}: a conflict marker is left")
            results[doc] = text
            report["docs"][doc] = entry_report
    changelog, where = insert_entry(main_copy(args, CHANGELOG), (content / "changelog_entry.txt").read_text(encoding="utf-8"))
    results[CHANGELOG] = changelog
    report["docs"][CHANGELOG] = where
    out = Path(args.out)
    for path, text in results.items():
        (out / path).write_text(text, encoding="utf-8")
    rendered = json.dumps(report, indent=2)
    if args.report:
        Path(args.report).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="mode", required=True)
    neu = sub.add_parser("neutralize")
    neu.add_argument("--carrier-dir", required=True)
    neu.add_argument("--base", required=True)
    neu.add_argument("--out", required=True)
    der = sub.add_parser("derive")
    der.add_argument("--content-dir", required=True)
    der.add_argument("--base", required=True)
    group = der.add_mutually_exclusive_group(required=True)
    group.add_argument("--main")
    group.add_argument("--main-dir")
    der.add_argument("--landing-date", required=True)
    der.add_argument("--out", required=True)
    der.add_argument("--report")
    der.add_argument("--work-dir", default=None, help="parent of the run's temporary directory (default: --content-dir)")
    rec = sub.add_parser("record")
    rec.add_argument("--merged", required=True, help="a git merge-file -p output (labels carrier / main) holding the conflict")
    rec.add_argument("--resolved", required=True, help="a file holding the text that replaces the block")
    rec.add_argument("--name", required=True)
    rec.add_argument("--path", required=True, help="the document, repo-relative")
    rec.add_argument("--content-dir", required=True, action="append")
    args = parser.parse_args(argv)
    modes = {"neutralize": neutralize, "derive": derive, "record": record}
    try:
        return modes[args.mode](args)
    except DeriveError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
