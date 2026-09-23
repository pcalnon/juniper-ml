#!/usr/bin/env python3
"""Classify every line of a cascor log capture by record-envelope SHAPE, and count them.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc, roadmap step P0.4)
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md §3.1 (P0.4 parts a and b)

WHY THIS EXISTS

P0.4(b) asks for an envelope checker: ``+`` sentinel, bracket prefix, ``(TIMESTAMP)`` INCLUDING
its precision, ``[LEVEL]``, message. Before any such checker is written into cascor's test tree
it has to be run against REAL captures, or it encodes the author's belief about the format rather
than the format. This survey does that: it classifies each line into exactly one shape and prints
per-shape counts plus the first example of each, so a shape the checker does not know about shows
up as ``UNCLASSIFIED`` with a real line beside it.

The shapes (anchored, full-line):

  A_FILE        ``+[f.py: func:LINE] (YYYY-MM-DD HH:MM:SS) [LEVEL] msg``   Path A, file sink
  A_CONSOLE     ``+[f.py: LINE] (YYYY-MM-DD HH:MM:SS) [LEVEL] msg``        Path A, stdout sink
  STD_FILE_S    ``[f.py: func:LINE] (YYYY-MM-DD HH:MM:SS) [LEVEL] msg``    stdlib file formatter, second resolution
  STD_FILE_MS   ``[f.py: func:LINE] (YYYY-MM-DD HH:MM:SS,mmm) [LEVEL] msg`` stdlib file formatter, millisecond resolution
  STD_CONSOLE   ``[f.py:LINE] (YY-MM-DD HH:MM:SS) [LEVEL] msg``            conf/logging_config.yaml formatter_console
  UNCLASSIFIED  anything else (warnings, tracebacks, uvicorn access lines, ...)

The precision is the point of separating STD_FILE_S from STD_FILE_MS: which writer produces which
is exactly the claim this survey exists to check.

USAGE

    python3 util/ad-hoc/2026-09-22_p04_log_shape_survey.py <capture> [<capture> ...]

Exit 0 always (it is a survey, not a gate); read the counts.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

_TS_S = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
_LEVEL = r"[A-Z]+"

SHAPES: list[tuple[str, re.Pattern[str]]] = [
    ("A_FILE", re.compile(rf"^\+\[(?P<file>[^\]:]+): (?P<func>[^\]:]+):(?P<line>\d+)\] \((?P<ts>{_TS_S})\) \[(?P<level>{_LEVEL})\] (?P<msg>.*)$")),
    ("A_CONSOLE", re.compile(rf"^\+\[(?P<file>[^\]:]+): (?P<line>\d+)\] \((?P<ts>{_TS_S})\) \[(?P<level>{_LEVEL})\] (?P<msg>.*)$")),
    ("STD_FILE_S", re.compile(rf"^\[(?P<file>[^\]:]+): (?P<func>[^\]:]+):(?P<line>\d+)\] \((?P<ts>{_TS_S})\) \[(?P<level>{_LEVEL})\] (?P<msg>.*)$")),
    ("STD_FILE_MS", re.compile(rf"^\[(?P<file>[^\]:]+): (?P<func>[^\]:]+):(?P<line>\d+)\] \((?P<ts>{_TS_S},\d{{3}})\) \[(?P<level>{_LEVEL})\] (?P<msg>.*)$")),
    ("STD_CONSOLE", re.compile(rf"^\[(?P<file>[^\]:]+):(?P<line>\d+)\] \((?P<ts>\d{{2}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}:\d{{2}})\) \[(?P<level>{_LEVEL})\] (?P<msg>.*)$")),
]


def classify(line: str) -> tuple[str, re.Match[str] | None]:
    for name, pattern in SHAPES:
        match = pattern.match(line)
        if match:
            return name, match
    return "UNCLASSIFIED", None


def survey(path: Path) -> None:
    counts: Counter[str] = Counter()
    levels: dict[str, Counter[str]] = {}
    first: dict[str, str] = {}
    unclassified_prefixes: Counter[str] = Counter()
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            shape, match = classify(line)
            counts[shape] += 1
            first.setdefault(shape, line[:220])
            if match is not None:
                levels.setdefault(shape, Counter())[match.group("level")] += 1
            else:
                unclassified_prefixes[line[:24]] += 1
    total = sum(counts.values())
    print(f"== {path}  ({total:,} lines, {path.stat().st_size:,} bytes)")
    for shape, _ in [*SHAPES, ("UNCLASSIFIED", None)]:
        n = counts.get(shape, 0)
        if not n:
            continue
        lv = ", ".join(f"{k}={v:,}" for k, v in sorted(levels.get(shape, Counter()).items()))
        print(f"  {shape:<13} {n:>9,}  {lv}")
        print(f"      e.g. {first[shape]}")
    if unclassified_prefixes:
        print("  UNCLASSIFIED by leading 24 chars (top 12):")
        for prefix, n in unclassified_prefixes.most_common(12):
            print(f"      {n:>7,}  {prefix!r}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    for arg in argv:
        survey(Path(arg).expanduser())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
