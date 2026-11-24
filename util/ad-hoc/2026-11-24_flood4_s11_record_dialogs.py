#!/usr/bin/env python3
"""
List the Overtoad's AskUserQuestion dialogs (and, with --text, typed instructions) in juniper-ml transcripts, timed.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- extractor for the record update (rulings 15-48)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 15-48);
         util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the pattern; it keeps the LAST result entry)

Why
---
The record dates each ruling from the transcript, not from a handoff's paraphrase. A tool_result can appear in more
than one transcript entry, and one copy can carry no timestamp, so the 2026-11-09 extractor, which keeps the LAST
entry, can print "answered None". This one keeps the FIRST entry that carries a timestamp, for the ask (the
assistant entry holding the tool_use) and for the answer (the user entry holding the tool_result) alike, and says
how many entries carried each.

What it does
------------
Scans every ``*.jsonl`` directly under the ``~/.claude/projects/`` directories whose names start with the juniper-ml
project prefix (the primary checkout and its ``.claude/worktrees/`` sessions), or only the sessions named by id
prefix. Writes one JSON list (``--out``): per AskUserQuestion call, the session id, the project directory, the
tool_use id, ``asked_at``, ``answered_at``, each question (header, text, multiSelect, option labels and
descriptions) and the answer text verbatim. ``--since`` drops calls asked before that UTC instant.

``--text PHRASE`` instead lists every user-typed message (not a tool_result) containing PHRASE, with its timestamp,
for rulings given as free text.

Lines are split on "\\n" only: ``str.splitlines()`` also splits on U+0085 and U+2028, which occur inside JSON strings.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py --since 2026-11-08T00:00:00Z --out <file.json>
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py --sessions 90e102f7 f2b4e7c3 --out <file.json>
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py --text "reworded as necessary" --since 2026-11-15T00:00:00Z
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
# Claude Code names a project directory after the session's start directory, every "/" and "." made "-".
PROJECT_PREFIX = str(Path.home() / "Development" / "python" / "Juniper" / "juniper-ml").replace("/", "-").replace(".", "-")


def transcripts(sessions: list[str] | None) -> list[Path]:
    """Every juniper-ml transcript, or the ones whose session id starts with one of ``sessions``."""
    dirs = sorted(p for p in PROJECTS.glob(PROJECT_PREFIX + "*") if p.is_dir())
    found: list[Path] = []
    for d in dirs:
        for f in sorted(d.glob("*.jsonl")):
            if sessions is None or any(f.name.startswith(s) for s in sessions):
                found.append(f)
    return found


def result_text(content: object) -> str:
    """A tool_result's text, whether it is a string or a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return repr(content)


def entries(path: Path):
    """Each parsed JSON entry of a transcript, in file order."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    for line in raw.split("\n"):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def scan_dialogs(path: Path) -> list[dict]:
    asked: dict[str, dict] = {}
    order: list[str] = []
    for entry in entries(path):
        message = entry.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            continue
        stamp = entry.get("timestamp")
        for block in message["content"]:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                tid = block.get("id")
                if tid not in asked:
                    asked[tid] = {
                        "session": path.stem,
                        "project_dir": path.parent.name,
                        "tool_use_id": tid,
                        "asked_at": None,
                        "ask_entries": 0,
                        "answered_at": None,
                        "result_entries": 0,
                        "questions": block.get("input", {}).get("questions", []),
                        "answer": None,
                    }
                    order.append(tid)
                rec = asked[tid]
                rec["ask_entries"] += 1
                if rec["asked_at"] is None and stamp:
                    rec["asked_at"] = stamp
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in asked:
                rec = asked[block["tool_use_id"]]
                rec["result_entries"] += 1
                if rec["answer"] is None:
                    rec["answer"] = result_text(block.get("content"))
                if rec["answered_at"] is None and stamp:
                    rec["answered_at"] = stamp
                    rec["answer"] = result_text(block.get("content"))
    return [asked[i] for i in order]


def scan_text(path: Path, phrase: str) -> list[dict]:
    hits: list[dict] = []
    for entry in entries(path):
        if entry.get("type") != "user":
            continue
        message = entry.get("message")
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        texts: list[str] = []
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            texts.extend(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        for text in texts:
            if phrase in text:
                hits.append({"session": path.stem, "project_dir": path.parent.name, "timestamp": entry.get("timestamp"), "text": text})
    return hits


def entry_kind(entry: dict) -> str:
    """A one-line description of an entry: its block types (tool names for tool_use) or its text's start."""
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return "text: " + content[:80].replace("\n", " ")
    if isinstance(content, list):
        kinds = []
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get("type") or "?"
            if kind == "tool_use":
                kind += ":" + str(block.get("name"))
            elif kind == "text":
                kind += ": " + block.get("text", "")[:60].replace("\n", " ")
            kinds.append(kind)
        return ", ".join(kinds)
    return ""


def inspect(path: Path, needle: str, before: int, after: int) -> None:
    """Print every entry within ``before``/``after`` lines of each line holding ``needle``, with its timestamp."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    marks = [n for n, line in enumerate(lines) if needle in line]
    print(f"== {path.name}: {len(marks)} line(s) hold {needle!r}: {marks}")
    if not marks:
        return
    lo, hi = max(0, marks[0] - before), min(len(lines), marks[-1] + after + 1)
    for n in range(lo, hi):
        if not lines[n].strip():
            continue
        try:
            entry = json.loads(lines[n])
        except json.JSONDecodeError:
            continue
        flag = "*" if n in marks else " "
        print(f"{flag}{n} {entry.get('type')} {entry.get('timestamp')} {entry_kind(entry)[:110]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", nargs="*", help="session-id prefixes (default: every juniper-ml transcript)")
    ap.add_argument("--since", default=None, help="drop calls/messages stamped before this ISO UTC instant")
    ap.add_argument("--text", default=None, help="list user-typed messages containing this phrase instead")
    ap.add_argument("--inspect", default=None, help="with one --sessions prefix: list the entries around each line holding this string")
    ap.add_argument("--before", type=int, default=3)
    ap.add_argument("--after", type=int, default=3)
    ap.add_argument("--out", default=None, help="write the JSON list here (default: print it)")
    args = ap.parse_args()

    files = transcripts(args.sessions or None)
    if args.inspect is not None:
        for f in files:
            inspect(f, args.inspect, args.before, args.after)
        return 0
    results: list[dict] = []
    for f in files:
        if args.text is not None:
            found = scan_text(f, args.text)
            results.extend(h for h in found if not args.since or (h["timestamp"] or "") >= args.since)
        else:
            found = scan_dialogs(f)
            results.extend(d for d in found if not args.since or (d["asked_at"] or "9999") >= args.since)
    key = "timestamp" if args.text is not None else "asked_at"
    results.sort(key=lambda r: r.get(key) or "")
    payload = json.dumps(results, indent=1, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"{len(results)} record(s) from {len(files)} transcript(s) -> {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
