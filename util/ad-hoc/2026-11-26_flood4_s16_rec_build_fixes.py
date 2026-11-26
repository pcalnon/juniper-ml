#!/usr/bin/env python3
"""
Build the flood-4 record update's exact replacements from a spec, check that each applies exactly once, apply them.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 16)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- builder and checker for the record update of 2026-11-26 (rulings 7, 23, 26-28 and 49)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (header, sections 0 and 6-9);
         util/ad-hoc/2026-11-24_flood4_s11_record_apply.py (the 2026-11-24 update's edits)

Why
---
The record update is delivered as old/new text pairs against ``main``'s copy of the record, applied in list order. An
old text that occurs twice, or not at all, when its turn comes would land in the wrong place or not at all, and a
line break written into a markdown table row ends the table there. This script refuses both, so the replacements
the orchestrator lands are the ones that were checked.

What it does
------------
Reads a spec file of fixes (format below), takes each fix's old text either verbatim from the spec or as whole
lines of the ORIGINAL record (``OLD-LINE: n`` / ``OLD-LINES: a-b``, so long lines are never retyped), and applies the
fixes in order to the record's text. For each fix it records how often the old text occurs at its turn (it is
applied only when that count is exactly 1), whether the old text sits on a table row while the new text holds a
line break, whether the new text adds lines that match G-TMP's pattern (``util/tmp_path_literal_check.py``) or the
home directory spelled out (G-PATH's class), any ``(Recommended)`` marker, and any ``@@NAME@@`` placeholder. Then it
writes the fixes as a JSON list of ``{"id", "file", "old", "new", "why"}``, the record with every fix applied, and a
report; and it re-applies the written JSON to the original record and checks the result equals the written copy.

Spec format (lines are split on "\\n" only; a block ends at the next line that starts with "=== "):

    === FIX <id>
    WHY: <one line>
    OLD-LINE: <n>             (or OLD-LINES: <a>-<b>, or an OLD: block)
    OLD:
    <exact text, one or more lines>
    NEW:
    <replacement text, one or more lines; trailing empty lines are dropped>
    === END

Exit status: 0 when every fix applied exactly once and no screen fired; 1 otherwise; 2 on a malformed spec.

Usage
-----
    python3 util/ad-hoc/2026-11-26_flood4_s16_rec_build_fixes.py --record <record_main.md.txt> --spec <fix_spec.txt> \\
        --fixes <fixes.json> --after <record_after.md.txt> --report <check_output.txt>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RECORD_PATH = "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md"
# The pattern of util/tmp_path_literal_check.py (G-TMP), copied so this check needs no import from the repository.
GTMP_PATTERN = re.compile(r"(?<![\w.~$})\]/])/(?:var/|private/)?tmp(?![\w-])")
PLACEHOLDER = re.compile(r"@@[A-Z0-9_]+@@")


class SpecError(Exception):
    """The spec file is malformed."""


def split_lines(text: str) -> list[str]:
    """Split on "\\n" only: ``str.splitlines()`` also splits on U+0085 and U+2028."""
    return text.split("\n")


def parse_spec(spec_text: str, original_lines: list[str]) -> list[dict]:
    """Parse the spec into fixes, resolving OLD-LINE / OLD-LINES against the ORIGINAL record's lines."""
    fixes: list[dict] = []
    cur: dict | None = None
    mode: str | None = None
    block: list[str] = []

    def close_block() -> None:
        nonlocal block, mode
        if cur is not None and mode in ("old", "new"):
            while block and block[-1] == "":
                block.pop()
            cur[mode] = "\n".join(block)
        block = []
        mode = None

    for raw in split_lines(spec_text):
        if raw.startswith("=== "):
            close_block()
            if cur is not None:
                fixes.append(cur)
                cur = None
            head = raw[4:].strip()
            if head == "END":
                break
            if not head.startswith("FIX "):
                raise SpecError(f"unknown header: {raw!r}")
            cur = {"id": head[4:].strip(), "why": "", "old": None, "new": None}
            continue
        if cur is None:
            continue
        if mode is None:
            if raw.startswith("WHY:"):
                cur["why"] = raw[4:].strip()
            elif raw.startswith("OLD-LINE:"):
                n = int(raw.split(":", 1)[1].strip())
                cur["old"] = original_lines[n - 1]
                cur["old_source"] = f"original line {n}"
            elif raw.startswith("OLD-LINES:"):
                a, b = (int(x) for x in raw.split(":", 1)[1].strip().split("-"))
                cur["old"] = "\n".join(original_lines[a - 1 : b])
                cur["old_source"] = f"original lines {a}-{b}"
            elif raw.strip() == "OLD:":
                mode = "old"
                cur["old_source"] = "spec text"
            elif raw.strip() == "NEW:":
                mode = "new"
            elif raw.strip():
                raise SpecError(f"fix {cur['id']}: unexpected line {raw!r}")
            continue
        if mode == "old" and raw.strip() == "NEW:":
            close_block()
            mode = "new"
            continue
        block.append(raw)
    close_block()
    if cur is not None:
        fixes.append(cur)
    ids = [f["id"] for f in fixes]
    if len(ids) != len(set(ids)):
        raise SpecError("duplicate fix id")
    for f in fixes:
        if not f.get("old") or f.get("new") is None:
            raise SpecError(f"fix {f['id']}: missing OLD or NEW")
    return fixes


def line_of(text: str, start: int) -> str:
    """The whole line of ``text`` that contains offset ``start``."""
    a = text.rfind("\n", 0, start) + 1
    b = text.find("\n", start)
    return text[a : b if b != -1 else len(text)]


def gtmp_lines(text: str) -> int:
    """How many lines of ``text`` match G-TMP's pattern."""
    return sum(1 for ln in split_lines(text) if GTMP_PATTERN.search(ln))


def apply_all(original: str, fixes: list[dict], home: str) -> tuple[str, list[dict], bool]:
    """Apply ``fixes`` in order; return the text, one result row per fix, and whether every check passed."""
    cur = original
    rows: list[dict] = []
    ok = True
    for f in fixes:
        old, new = f["old"], f["new"]
        count = cur.count(old)
        row = {"id": f["id"], "old_source": f.get("old_source", "json"), "old_chars": len(old), "new_chars": len(new), "count_at_turn": count, "applied": False, "flags": []}
        if count == 1:
            at = cur.find(old)
            host_line = line_of(cur, at)
            if host_line.lstrip().startswith("|") and "\n" in new:
                row["flags"].append("TABLE-ROW-LINE-BREAK")
            if gtmp_lines(new) > gtmp_lines(old):
                row["flags"].append("G-TMP-LITERAL-ADDED")
            if home and home in new and home not in old:
                row["flags"].append("HOME-LITERAL-ADDED")
            if "(Recommended)" in new:
                row["flags"].append("RECOMMENDED-MARKER")
            cur = cur[:at] + new + cur[at + len(old) :]
            row["applied"] = True
        else:
            row["flags"].append(f"OLD-COUNT-{count}")
        row["placeholders"] = sorted(set(PLACEHOLDER.findall(new)))
        if row["flags"]:
            ok = False
        rows.append(row)
    return cur, rows, ok


def table_screen(text: str) -> list[int]:
    """Line numbers of table rows that do not end with "|" (a broken row)."""
    bad = []
    for n, ln in enumerate(split_lines(text), 1):
        s = ln.strip()
        if s.startswith("|") and not s.endswith("|"):
            bad.append(n)
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--record", required=True, type=Path, help="main's copy of the record")
    ap.add_argument("--spec", required=True, type=Path, help="the fix spec (format in the module docstring)")
    ap.add_argument("--fixes", required=True, type=Path, help="where to write fixes.json")
    ap.add_argument("--after", required=True, type=Path, help="where to write the record with every fix applied")
    ap.add_argument("--report", required=True, type=Path, help="where to write the check report")
    ap.add_argument("--file", default=RECORD_PATH, help="the repository path the fixes name")
    args = ap.parse_args()

    original = args.record.read_text(encoding="utf-8")
    original_lines = split_lines(original)
    try:
        fixes = parse_spec(args.spec.read_text(encoding="utf-8"), original_lines)
    except SpecError as exc:
        print(f"SPEC ERROR: {exc}", file=sys.stderr)
        return 2

    home = str(Path.home())
    after, rows, ok = apply_all(original, fixes, home)

    out = [{"id": f["id"], "file": args.file, "old": f["old"], "new": f["new"], "why": f["why"]} for f in fixes]
    args.fixes.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    args.after.write_text(after, encoding="utf-8")

    # Re-apply the JSON as written, to prove it reproduces the same text.
    reloaded = json.loads(args.fixes.read_text(encoding="utf-8"))
    again, _rows2, ok2 = apply_all(original, reloaded, home)
    reproduces = again == after

    broken_rows = table_screen(after)
    orig_broken = table_screen(original)
    placeholders = sorted(set(PLACEHOLDER.findall(after)))
    lines = [
        f"interpreter: {sys.version.split()[0]} | {sys.executable} | {sys.base_prefix}",
        f"record: {args.record} ({len(original)} chars, {len(original_lines)} lines)",
        f"spec: {args.spec} ({len(fixes)} fixes)",
        "",
        "id | old source | old chars | count at turn | applied | new chars | flags | placeholders",
    ]
    for r in rows:
        lines.append(f"{r['id']} | {r['old_source']} | {r['old_chars']} | {r['count_at_turn']} | {r['applied']} | {r['new_chars']} | {','.join(r['flags']) or '-'} | {','.join(r['placeholders']) or '-'}")
    lines += [
        "",
        f"applied: {sum(r['applied'] for r in rows)} of {len(rows)}",
        f"fixes.json re-applied to the original reproduces record_after: {reproduces} (every fix exactly once on re-apply: {ok2})",
        f"table rows not ending in '|': after {broken_rows or 'none'}; original {orig_broken or 'none'}",
        f"G-TMP literal lines: original {gtmp_lines(original)}, after {gtmp_lines(after)}",
        f"home-directory literal in after: {home in after}",
        f"placeholders left in after: {', '.join(placeholders) or 'none'}",
        f"after: {len(after)} chars, {len(split_lines(after))} lines",
        f"RESULT: {'OK' if ok and ok2 and reproduces and not broken_rows else 'FAIL'}",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok and ok2 and reproduces and not broken_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
