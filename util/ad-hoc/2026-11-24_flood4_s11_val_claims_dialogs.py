#!/usr/bin/env python3
"""
Independently re-extract the Overtoad's AskUserQuestion dialogs and typed messages from juniper-ml transcripts (validator V1).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V1 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (validation of the record update's rulings 15-48)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8;
         written independently of util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py (the drafter's), so the two
         can be compared rather than one trusted

What it does
------------
Reads every ``*.jsonl`` (recursively, so sub-agent transcripts are included) under the ``~/.claude/projects/``
directories whose names start with the juniper-ml project prefix. For each AskUserQuestion ``tool_use`` it records the
session, the FIRST entry that carries a timestamp holding the tool_use (asked) and the FIRST timestamped entry holding
its ``tool_result`` (answered), counts of all entries holding each (timed and untimed), the questions with their option
labels, the ``toolUseResult.answers`` mapping when present, and the result text verbatim.

``--typed PHRASE`` instead lists user-typed text messages (not tool results) containing PHRASE, with timestamps.

Lines are split on b"\\n" only (U+2028 / U+0085 can occur inside JSON strings).

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_dialogs.py --since 2026-11-09T00:00:00Z --out <file.json>
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_dialogs.py --typed "reworded as necessary" --out <file.json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Claude Code names a project's transcript directory after its path, "/" and "." each replaced by "-".
PREFIX = str(Path.home() / "Development" / "python" / "Juniper" / "juniper-ml").replace("/", "-").replace(".", "-")


def iter_entries(path: Path):
    with open(path, "rb") as fh:
        data = fh.read()
    for lineno, raw in enumerate(data.split(b"\n")):
        if not raw.strip():
            continue
        try:
            yield lineno, json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue


def blocks(entry):
    msg = entry.get("message")
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, list):
            return [b for b in content if isinstance(b, dict)]
    return []


def result_text(block):
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def scan(roots, since, only_sessions):
    calls = {}
    for root in roots:
        for path in sorted(root.rglob("*.jsonl")):
            sid = path.stem
            if only_sessions and not any(sid.startswith(s) for s in only_sessions):
                continue
            text_probe = path.read_bytes()
            if b"AskUserQuestion" not in text_probe:
                continue
            for lineno, entry in iter_entries(path):
                ts = entry.get("timestamp")
                for b in blocks(entry):
                    if b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                        tid = b.get("id")
                        rec = calls.setdefault(tid, {"tool_use_id": tid, "session": sid, "file": str(path.relative_to(root.parent)), "asked_at": None, "asked_line": None, "answered_at": None, "answered_line": None, "n_use_entries": 0, "n_use_timed": 0, "n_result_entries": 0, "n_result_timed": 0, "questions": None, "answers": None, "result_text": None})
                        rec["n_use_entries"] += 1
                        if ts:
                            rec["n_use_timed"] += 1
                            if rec["asked_at"] is None:
                                rec["asked_at"], rec["asked_line"] = ts, lineno
                        if rec["questions"] is None:
                            qs = (b.get("input") or {}).get("questions") or []
                            rec["questions"] = [{"header": q.get("header"), "question": q.get("question"), "multiSelect": q.get("multiSelect"), "labels": [o.get("label") for o in q.get("options") or []]} for q in qs]
                    elif b.get("type") == "tool_result":
                        tid = b.get("tool_use_id")
                        if tid not in calls:
                            # result before use would be odd; record lazily
                            continue
                        rec = calls[tid]
                        rec["n_result_entries"] += 1
                        if ts:
                            rec["n_result_timed"] += 1
                            if rec["answered_at"] is None:
                                rec["answered_at"], rec["answered_line"] = ts, lineno
                                rec["result_text"] = result_text(b)
                                tur = entry.get("toolUseResult")
                                if isinstance(tur, dict):
                                    rec["answers"] = tur.get("answers")
                                    rec["annotations"] = tur.get("annotations")
                        elif rec["result_text"] is None:
                            rec["result_text_untimed"] = result_text(b)
    out = [c for c in calls.values() if (c["asked_at"] or "") >= since]
    out.sort(key=lambda c: c["asked_at"] or "")
    return out


def typed(roots, phrase, since):
    hits = []
    for root in roots:
        for path in sorted(root.rglob("*.jsonl")):
            if phrase.encode() not in path.read_bytes():
                continue
            for lineno, entry in iter_entries(path):
                if entry.get("type") != "user":
                    continue
                ts = entry.get("timestamp") or ""
                if ts < since:
                    continue
                msg = entry.get("message") or {}
                content = msg.get("content")
                texts = []
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    texts.extend(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
                for t in texts:
                    if phrase in t:
                        hits.append({"session": path.stem, "file": str(path.relative_to(root.parent)), "line": lineno, "timestamp": ts, "isSidechain": entry.get("isSidechain"), "text": t})
    hits.sort(key=lambda h: h["timestamp"])
    return hits


def show(path: str, sessions, maxlen: int) -> int:
    """Print the dialogs of an earlier --out file, filtered by session id prefix."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for c in data:
        if sessions and not any(c["session"].startswith(s) for s in sessions):
            continue
        print("=" * 100)
        print(c["session"][:8], c["tool_use_id"], "asked", c["asked_at"], "answered", c["answered_at"], "use", c["n_use_entries"], c["n_use_timed"], "res", c["n_result_entries"], c["n_result_timed"])
        for q in c["questions"] or []:
            print(" Q[%s] %s" % (q["header"], q["question"]))
            print("   labels:", q["labels"], "multi" if q["multiSelect"] else "")
        print(" ANSWERS:", json.dumps(c.get("answers"), ensure_ascii=False))
        if c.get("annotations"):
            print(" ANNOT:", json.dumps(c.get("annotations"), ensure_ascii=False)[:maxlen])
        if not c.get("answers"):
            print(" RESULT:", (c.get("result_text") or c.get("result_text_untimed") or "")[:maxlen])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--since", default="2026-11-08T00:00:00Z")
    ap.add_argument("--sessions", nargs="*", default=[])
    ap.add_argument("--typed", default=None)
    ap.add_argument("--show", default=None, help="print an earlier --out file (filtered by --sessions) and exit")
    ap.add_argument("--maxlen", type=int, default=1500)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.show:
        return show(args.show, args.sessions, args.maxlen)
    if not args.out:
        ap.error("--out is required unless --show is given")
    base = Path.home() / ".claude" / "projects"
    roots = sorted(p for p in base.iterdir() if p.is_dir() and p.name.startswith(PREFIX))
    if args.typed:
        result = typed(roots, args.typed, args.since)
    else:
        result = scan(roots, args.since, args.sessions)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, ensure_ascii=False)
    print(f"{len(result)} records -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
