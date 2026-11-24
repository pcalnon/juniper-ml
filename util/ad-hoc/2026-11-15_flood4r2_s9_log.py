#!/usr/bin/env python3
"""Append one clock-stamped entry to the flood-4 session-9 running log.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc, session 9; a copy of the session-8 helper with its log path moved)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why it exists: session 6's handoff records that log stamps typed from memory ran up to five minutes ahead of the
clock, and session 7 repeated the mistake by fourteen minutes within its first quarter of an hour. This helper reads
the entry text on standard input and writes the stamp from the clock, so a stamp can no longer be typed.

Usage:
    python3 util/ad-hoc/2026-11-15_flood4r2_s9_log.py <<'EOF'
    THREE AGENTS LAUNCHED: ...
     continuation lines keep their own indentation
    EOF

The first line is prefixed with two spaces and the stamp `[HH:MMZ]`; later lines are indented by three spaces unless
they are already indented. The log path is fixed: tmp/flood4/session9/STATE_S9.txt under the worktree that holds this
script. Pass `--date` to write the stamp as `[HH:MMZ MM-DD]` (used after a UTC midnight).
"""

from __future__ import annotations

import argparse
import datetime
import pathlib
import sys

LOG_RELATIVE = pathlib.Path("tmp") / "flood4" / "session9" / "STATE_S9.txt"


def build_entry(text: str, now: datetime.datetime, with_date: bool) -> str:
    """Return the entry as it is appended: a stamped first line, then indented continuation lines."""
    lines = [line.rstrip() for line in text.strip("\n").split("\n")]
    if not lines or not lines[0].strip():
        raise ValueError("the entry is empty")
    stamp = now.strftime("%H:%MZ %m-%d") if with_date else now.strftime("%H:%MZ")
    out = [f"  [{stamp}] {lines[0].strip()}"]
    for line in lines[1:]:
        out.append(line if line.startswith(" ") or not line else f"   {line}")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--date", action="store_true", help="write the stamp with the UTC month and day")
    args = parser.parse_args(argv)
    log_path = pathlib.Path(__file__).resolve().parents[2] / LOG_RELATIVE
    if not log_path.is_file():
        print(f"refusing: {log_path} does not exist", file=sys.stderr)
        return 2
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        entry = build_entry(sys.stdin.read(), now, args.date)
    except ValueError as error:
        print(f"refusing: {error}", file=sys.stderr)
        return 2
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    print(entry, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
