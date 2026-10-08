#!/usr/bin/env python3
"""Resolve `git apply --3way` conflict blocks in one markdown file from an explicit JSON plan.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. Consolidating twelve fleet docs PRs that append rows at the same anchors produces
many two-sided conflicts whose resolution is "keep both" or "merge these table rows". Doing that
by hand is where content gets dropped, so every block is resolved by a declared strategy and the
script refuses if the plan does not account for every block.

    python3 util/ad-hoc/2026-10-08_data_docs_resolve_conflicts.py FILE PLAN.json

PLAN.json is a list with one entry per conflict block, in file order:

    {"strategy": "ours"} | {"strategy": "theirs"} | {"strategy": "ours+theirs"} | {"strategy": "theirs+ours"}
    {"strategy": "text", "text": "replacement\\n"}
    {"strategy": "table", "order": ["**Key**", ...], "prefer": {"**Key**": "ours"}, "default": "theirs",
     "rest": "ours+theirs"}

`table` merges the leading `| ...` rows of both sides keyed by their first cell, emits them in
`order` (every key seen must be listed), then appends the non-table remainder of each side per
`rest`. Any entry may carry "replace": [[old, new], ...]; each `old` must occur exactly once in the
resolved block.
"""

import json
import sys

OURS, SEP, THEIRS = "<<<<<<< ours\n", "=======\n", ">>>>>>> theirs\n"


def blocks(text: str):
    found, i = [], 0
    while True:
        a = text.find(OURS, i)
        if a < 0:
            return found
        m = text.index(SEP, a)
        b = text.index(THEIRS, m)
        found.append((a, text[a + len(OURS) : m], text[m + len(SEP) : b], b + len(THEIRS)))
        i = b + len(THEIRS)


def split_rows(side: str) -> tuple[list[str], str]:
    lines = side.splitlines(keepends=True)
    rows = []
    for line in lines:
        if line.startswith("|"):
            rows.append(line)
        else:
            break
    return rows, "".join(lines[len(rows) :])


def key(row: str) -> str:
    return row.split("|")[1].strip()


def combine(how: str, ours: str, theirs: str) -> str:
    return {"ours": ours, "theirs": theirs, "ours+theirs": ours + theirs, "theirs+ours": theirs + ours}[how]


def resolve_one(entry: dict, ours: str, theirs: str) -> str:
    strategy = entry["strategy"]
    if strategy == "text":
        out = entry["text"]
    elif strategy == "table":
        o_rows, o_rest = split_rows(ours)
        t_rows, t_rest = split_rows(theirs)
        o_map = {key(r): r for r in o_rows}
        t_map = {key(r): r for r in t_rows}
        seen = set(o_map) | set(t_map)
        order = entry["order"]
        missing = seen - set(order)
        if missing:
            raise SystemExit(f"table plan does not order keys {sorted(missing)}")
        prefer = entry.get("prefer", {})
        default = entry.get("default", "theirs")
        rows = []
        for k in order:
            side = prefer.get(k, default)
            first, second = (o_map, t_map) if side == "ours" else (t_map, o_map)
            row = first.get(k) or second.get(k)
            if row is None:
                raise SystemExit(f"table key {k!r} absent from both sides")
            rows.append(row)
        out = "".join(rows) + combine(entry.get("rest", "ours+theirs"), o_rest, t_rest)
    else:
        out = combine(strategy, ours, theirs)
    for old, new in entry.get("replace", []):
        if out.count(old) != 1:
            raise SystemExit(f"replace anchor occurs {out.count(old)} times: {old[:80]!r}")
        out = out.replace(old, new)
    return out


def main() -> int:
    path, plan_path = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    with open(plan_path, encoding="utf-8") as fh:
        plan = json.load(fh)
    found = blocks(text)
    if len(found) != len(plan):
        raise SystemExit(f"{path}: {len(found)} conflict blocks, plan has {len(plan)}")
    out, pos = [], 0
    for (a, ours, theirs, end), entry in zip(found, plan):
        out.append(text[pos:a])
        out.append(resolve_one(entry, ours, theirs))
        pos = end
    out.append(text[pos:])
    result = "".join(out)
    if OURS in result or THEIRS in result:
        raise SystemExit("conflict markers remain")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(result)
    print(f"{path}: resolved {len(found)} block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
