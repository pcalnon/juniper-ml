#!/usr/bin/env python3
"""Archive the backup arc's Phase B validation reports verbatim into one notes/ record.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-10-04
Status:      ad-hoc -- validation record
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-24_archive_round4_reports.py (the round-4 record's archiver, which this extends)
             util/ad-hoc/2026-09-22_archive_consensus_reports.py (whose extraction and screen both reuse)
             notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md

The round-4 archiver lifts each report from a subagent transcript by its id. Phase B's reports come from
several sessions, and most survive only as files a session saved, so each --report names its source:

    --report '<Heading>=file:<path>|<origin>'       a report saved to a file
    --report '<Heading>=agent:<agent-id>|<origin>'  a subagent's FINAL assistant message, from --tasks-dir
    --report '<Heading>=record:<path>'              a report already archived under the same heading in a
                                                    record -- main's copy, typically -- lifted together with
                                                    its origin line, so re-assembly needs no file off main

<origin> is required for file: and agent: sources. It completes the report's line "Archived verbatim (N
characters, sha256 `<16 hex>`), lifted from <origin>.", so it should say who saved the report, when, and
from what. Until 2026-10-05 this script wrote one fixed origin for every file: source, which was false for
five of the record's sections (the round-3 handoff's validation, finding D-4).

A record is PARSED, never searched: it must be its header, then wrapped sections laid end to end to the
last byte. Each section is read by its declared length, which must end at the closing marker, and its body
must hash to the prefix in its line. So text quoted inside a report -- a marker, an opening, even a whole
self-consistent section -- is part of that report's body and is never read as structure, and a hand-edited
length breaks the tiling instead of cutting a report short or swallowing the next one. Where the tiling
stops, the rest of the record is a REMAINDER: a damaged section, or text added by hand.

Three validation rounds on 2026-10-05 broke the earlier versions; each guard below answers one of them:

- --prefer-record <path> makes one list of file: sources serve two modes: a report whose heading the record
  holds is taken from the record, and only the rest are read from their files. A file that EXISTS must
  still agree with the record, body and origin both; otherwise the run refuses, unless --replace <heading>
  says to take the file (the re-validation's D-2 and the third round's N-2).
- A run that would drop a report the existing --out holds, or its remainder, is refused unless
  --allow-drop says so, and every dropped heading is printed either way (D-2; the third round's N-3, N-4).
- A run whose header differs from the existing record's header is refused unless --accept-header says the
  .in file is meant to win: an edit made to the record's header on main would otherwise be lost (N-3).
- --check writes nothing and compares BYTES: exit 0 when the result equals the existing --out, 1 when it
  differs, 2 when a guard refuses.

Every report passes through the same credential-shape screen as the round-4 record (notes/ is committed to
a PUBLIC repository), and a hit refuses the whole archive, to be classified by hand. The wrapper names no
agent id. --header is required: a record without its disposition is a pile of reports, not a record. Each
report is wrapped in markdownlint-disable / -enable exactly as the round-4 record's are, and never
rewrapped.

Usage:
    python3 util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py --header <preamble.md> \\
        --out notes/<RECORD>.md [--tasks-dir <session>/subagents] [--prefer-record <record.md>] \\
        --report '<Heading>=<source>' [...] [--replace <Heading>] [--allow-drop] [--accept-header] [--check]

The Phase B record's own invocation is saved as util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import NamedTuple

ARCHIVER = Path(__file__).with_name("2026-09-22_archive_consensus_reports.py")
OPEN = "<!-- markdownlint-disable -->\n\n"
CLOSE = "\n<!-- markdownlint-enable -->\n"
OPENING = re.compile(r"\n---\n\n## (.+)\n\n(?=Archived verbatim \()")
ORIGIN_LINE = re.compile(r"Archived verbatim \(([0-9,]+) characters, sha256 `([0-9a-f]{16})`\), lifted from (.+?)\.\n\n")


class Parsed(NamedTuple):
    header: str
    held: dict[str, tuple[str, str]]
    remainder: str
    stopped_at_line: int


def digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def section(heading: str, body: str, origin: str) -> str:
    """The wrapper every report gets. parse() is its exact inverse."""
    return f"\n---\n\n## {heading}\n\nArchived verbatim ({len(body):,} characters, sha256 `{digest(body)}`), lifted from {origin}.\n\n{OPEN}{body}{CLOSE}"


def parse(text: str, where: Path) -> Parsed:
    """Split a record into its header, its intact sections in order, and whatever follows the last of them."""
    first = OPENING.search(text)
    if first is None:
        return Parsed(text, {}, "", 0)
    held: dict[str, tuple[str, str]] = {}
    position = first.start()
    while position < len(text):
        opening = OPENING.match(text, position)
        line = ORIGIN_LINE.match(text, opening.end()) if opening else None
        if opening is None or line is None or not text.startswith(OPEN, line.end()):
            break
        size = int(line.group(1).replace(",", ""))
        begin = line.end() + len(OPEN)
        body = text[begin : begin + size]
        if not body.endswith("\n") or not text.startswith(CLOSE, begin + size) or digest(body) != line.group(2):
            break
        heading = opening.group(1)
        if heading in held:
            raise SystemExit(f"{where}: two sections are archived under the heading {heading!r}")
        held[heading] = (body, line.group(3))
        position = begin + size + len(CLOSE)
    remainder = text[position:]
    return Parsed(text[: first.start()], held, remainder, text.count("\n", 0, position) + 1 if remainder else 0)


def load_archiver(tasks_dir: Path | None):
    spec = importlib.util.spec_from_file_location("archive_consensus_reports", ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ARCHIVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if tasks_dir is not None:
        module.TASKS = tasks_dir
    return module


def lifted(record: Path, heading: str) -> tuple[str, str]:
    """Take one report, and its origin, back out of a record that section() built."""
    if not record.is_file():
        raise SystemExit(f"no such record: {record}")
    parsed = parse(record.read_text(encoding="utf-8"), record)
    if heading not in parsed.held:
        stop = f" (the record stops parsing at line {parsed.stopped_at_line})" if parsed.remainder else ""
        raise SystemExit(f"{record}: no intact section is archived under {heading!r}{stop}")
    return parsed.held[heading]


def report_body(archiver, heading: str, source: str, tasks_dir: Path | None) -> tuple[str, str]:
    kind, _, ref = source.partition(":")
    if kind == "record":
        return lifted(Path(ref), heading)
    if kind not in ("file", "agent"):
        raise SystemExit(f"a report source is file:<path>|<origin>, agent:<id>|<origin> or record:<path>, got {source!r}")
    ref, _, origin = ref.partition("|")
    if not origin.strip():
        raise SystemExit(f"{heading!r}: a {kind}: source must say where the report came from (|<origin>)")
    if kind == "file":
        path = Path(ref)
        if not path.is_file():
            raise SystemExit(f"no such report file: {path}")
        return path.read_text(encoding="utf-8").rstrip() + "\n", origin.strip()
    if tasks_dir is None:
        raise SystemExit("an agent: report needs --tasks-dir")
    return archiver.final_report(ref).rstrip() + "\n", origin.strip()


def disagreement(source: str, held: tuple[str, str]) -> str:
    """Why a file: source disagrees with the report the record holds, or "" when it agrees. The origin is
    compared always; the body only when the file exists (on a clone of main, it does not)."""
    kind, _, ref = source.partition(":")
    if kind != "file":
        return ""
    path, _, origin = ref.partition("|")
    reasons = []
    if Path(path).is_file() and Path(path).read_text(encoding="utf-8").rstrip() + "\n" != held[0]:
        reasons.append(f"its file {path} differs from the archived body")
    if origin.strip() != held[1]:
        reasons.append("its origin differs from the archived one")
    return " and ".join(reasons)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--tasks-dir", type=Path)
    ap.add_argument("--report", action="append", required=True, metavar="HEADING=SOURCE")
    ap.add_argument("--prefer-record", type=Path, help="take every report this record holds from it")
    ap.add_argument("--replace", action="append", default=[], metavar="HEADING", help="take this report from its source even though the record holds a different one")
    ap.add_argument("--allow-drop", action="store_true", help="let the run leave out reports, or a remainder, the existing --out holds")
    ap.add_argument("--accept-header", action="store_true", help="write the --header file even though the existing record's header differs")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.tasks_dir is not None and not args.tasks_dir.is_dir():
        raise SystemExit(f"no such transcript directory: {args.tasks_dir}")
    archiver = load_archiver(args.tasks_dir)
    held: dict[str, tuple[str, str]] = {}
    if args.prefer_record is not None and args.prefer_record.is_file():
        held = parse(args.prefer_record.read_text(encoding="utf-8"), args.prefer_record).held

    header = args.header.read_text(encoding="utf-8").rstrip() + "\n"
    parts = [header]
    problems: list[str] = []
    refusals: list[str] = []
    headings: list[str] = []
    for spec in args.report:
        heading, _, source = spec.partition("=")
        if not heading or not source:
            raise SystemExit(f"--report must be HEADING=SOURCE, got {spec!r}")
        if heading in headings:
            raise SystemExit(f"{heading!r} is given twice")
        headings.append(heading)
        if heading in held and heading not in args.replace:
            why = disagreement(source, held[heading])
            if why:
                refusals.append(f"DIFFERS: {heading}: {why} (--replace {heading!r} takes the source)")
            (body, origin), kind = held[heading], "the record"
        else:
            (body, origin), kind = report_body(archiver, heading, source, args.tasks_dir), source.partition(":")[0]
        problems += archiver.screen(heading, body)
        print(f"  {heading}: {len(body):,} characters, from {kind}")
        parts.append(section(heading, body, origin))
    for name in args.replace:
        if name not in headings:
            raise SystemExit(f"--replace names {name!r}, which no --report gives")

    if args.out.is_file():
        existing = parse(args.out.read_text(encoding="utf-8"), args.out)
        dropped = [name for name in existing.held if name not in headings]
        for name in dropped:
            print(f"  {'DROPPING' if args.allow_drop else 'WOULD DROP'}: {name}", file=sys.stderr)
        if existing.remainder:
            print(f"  {'DROPPING' if args.allow_drop else 'WOULD DROP'}: {len(existing.remainder):,} characters from line {existing.stopped_at_line}, which is no intact section", file=sys.stderr)
        if (dropped or existing.remainder) and not args.allow_drop:
            refusals.append(f"{args.out} holds text this run leaves out (--allow-drop to mean it)")
        if existing.header != header and not args.accept_header:
            refusals.append(f"{args.out}'s header differs from {args.header}: port any edit made to the record into the header file, then pass --accept-header")

    if problems:
        for problem in problems:
            print(f"  SHAPED: {problem}", file=sys.stderr)
        print("\nrefusing to archive: classify every hit by hand first", file=sys.stderr)
        return 2
    if refusals:
        for refusal in refusals:
            print(f"  REFUSED: {refusal}", file=sys.stderr)
        print("\nrefusing to archive", file=sys.stderr)
        return 2

    text = "".join(parts)
    size = f"{len(text):,} characters, {len(text.encode('utf-8')):,} bytes"
    if args.check:
        same = args.out.is_file() and args.out.read_bytes() == text.encode("utf-8")
        print(f"\n--check: would write {args.out} ({size}), {'IDENTICAL to' if same else 'DIFFERENT from'} the existing file; nothing written")
        return 0 if same else 1
    args.out.write_text(text, encoding="utf-8")
    print(f"\nwrote {args.out} ({size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
