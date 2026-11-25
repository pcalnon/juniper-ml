#!/usr/bin/env python3
"""
List every AskUserQuestion call in the named sessions' transcripts, with the Overtoad's answer and when it was given,
dating each from the FIRST entry that carries a timestamp.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record; R-OBS-SC-2 follow-ups, item R51)
Author: Paul Calnon
Created: 2026-11-24
Version: 0.4.0
Status: ad-hoc -- extractor (the dated successor of the 2026-11-09 one)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the predecessor, kept as provenance);
         notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md (item R51);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.16's record, the finding)

Why
---
A transcript can hold more than one copy of an answer. Besides the ``user`` entry that delivered the ``tool_result``
(it has a ``timestamp``), an ``api-request-blob`` entry carries the same result with only ``hash``, ``sessionId`` and
``type``: no timestamp. The predecessor kept the LAST entry that carried each result, so when the untimed copy came
after the ``user`` entry it printed ``answered None``. Measured in session ``218ff61e`` (call 5, ruling 7 of
2026-11-13: the ``user`` entry at line 1808, stamped 10:10:51.412Z, then the blob at line 1815), session ``7d425759``
(call 1: line 545 at 2026-11-14T22:10:39.373Z, then the blob at line 563) and session ``2222e504`` (call 1: line 667
at 2026-11-23T20:32:40.333Z, then the blob at line 670). Where the blob came first, the later ``user`` entry won and
the date was right. The copies carry the same text in every case measured.

What it prints, and how it differs from the predecessor
-------------------------------------------------------
The predecessor's layout: per session a ``==`` line, per call a ``-- call N: asked …, answered …`` line, its
questions and an ``ANSWER:`` line. It differs in these ways:

1. A call's ``answered`` time is the timestamp of the first entry that carries both its result and a timestamp, and
   its ANSWER is that entry's text. An untimed copy is used only when no copy is timed, so such a call still reads
   ``answered None``. The ``asked`` time is taken the same way from the asking message's copies.
2. A ``tool_use`` seen again (an untimed copy of the asking message) is the same call. The predecessor listed it once
   per copy, so its call numbers can run ahead of these: in ``1b4fec84`` it printed 5 calls for 3, and its calls 3
   and 5 are calls 2 and 3 here. A copy seen after the answer no longer resets the call to ``asked None, answered
   None``, and when the copies' questions differ, the first copy's are printed (the predecessor printed the last's).
3. A result recorded before its ``tool_use`` still counts; the predecessor dropped it.
4. A result that is itself an error (``is_error``) is labelled from the transcript's own fields:
   ``ANSWER (user-rejected):`` from the entry's ``toolDenialKind``, else ``ANSWER (is_error):``. The text is printed
   as before. The entry's ``toolDenialKind`` names the kind only when the entry holds this one result, so a sibling
   result's rejection labels nothing. The chosen copy's label is printed, and a ``NOTE`` says when some copies are
   marked as an error and others are not (a blob copy's bare ``is_error`` beside ``user-rejected`` is no disagreement).
5. When a call's copies carry different texts, a ``NOTE`` line says how many and which one is printed.
6. A ``tool_use`` whose ``input`` or ``questions`` is null or not the expected type (no questions), one with no
   ``id`` (skipped), a question that is not an object (printed as text), and a line that is valid JSON but not an
   object (skipped) no longer stop the run.
7. An empty-string timestamp counts as none: such a call reads ``answered None`` where the predecessor printed an
   empty time.

On the 13 sessions measured (the predecessor's 11, ``21952abc`` and ``2222e504``), only items 1, 2 and 4 change the
output: three ``answered`` times, ``1b4fec84``'s repeated calls, and two ``(user-rejected)`` labels.

The transcripts are found by session-id prefix under ``~/.claude/projects/*/``, never by a fixed path: a session's
transcript moves when it leaves its worktree. They are split on "\\n" only, because ``str.splitlines()`` also splits
on U+0085 and U+2028, which occur inside JSON string values.

What it cannot do
-----------------
- Tell two sessions apart inside one file: a ``tool_use`` id that two ``sessionId`` values share is one call.
- Prefer a later copy of the question: its questions come from the first copy it reads, timed or not.

Usage
-----
    python3 util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py 218ff61e 7d425759 [--full] [--width 240]
    python3 util/ad-hoc/2026-11-24_r_obs_sc_2_owner_answers.py --self-test
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def transcript(prefix: str) -> Path:
    """The one transcript whose session id starts with ``prefix``."""
    hits = sorted(PROJECTS.glob(f"*/{prefix}*.jsonl"))
    if len(hits) != 1:
        raise SystemExit(f"session {prefix}: expected one transcript under {PROJECTS}, found {len(hits)}: {hits}")
    return hits[0]


def result_text(content: object) -> str:
    """A tool_result's text, whether it is a string or a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return repr(content)


def _blocks(line: str):
    """The entry a transcript line holds and its message's content blocks; (None, []) for anything else."""
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return None, []
    message = entry.get("message") if isinstance(entry, dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("content"), list):
        return None, []
    return entry, [block for block in message["content"] if isinstance(block, dict)]


def scan_lines(lines: list[str]) -> list[dict]:
    """Every AskUserQuestion call in the order its first copy appears, each dated from its first timestamped entry.
    Two passes, so a result recorded before its question still counts."""
    uses: dict[str, dict] = {}
    order: list[str] = []
    for line in lines:
        if "AskUserQuestion" not in line:
            continue
        entry, blocks = _blocks(line)
        stamp = (entry.get("timestamp") or None) if entry else None
        for block in blocks:
            if block.get("type") != "tool_use" or block.get("name") != "AskUserQuestion" or not block.get("id"):
                continue
            record = uses.get(block["id"])
            if record is None:
                request = block.get("input")
                questions = request.get("questions") if isinstance(request, dict) else None
                record = {"asked_at": None, "questions": questions if isinstance(questions, list) else []}
                uses[block["id"]] = record
                order.append(block["id"])
            if record["asked_at"] is None:
                record["asked_at"] = stamp
    copies: dict[str, list[tuple[str | None, str, str | None]]] = {tid: [] for tid in order}
    for line in lines:
        if '"tool_result"' not in line or not any(tid in line for tid in order):
            continue
        entry, blocks = _blocks(line)
        if entry is None:
            continue
        stamp = entry.get("timestamp") or None
        results = sum(1 for block in blocks if block.get("type") == "tool_result")
        for block in blocks:
            tid = block.get("tool_use_id")
            if block.get("type") == "tool_result" and tid in copies:
                # Only a result that is itself an error is labelled. The entry's toolDenialKind names the kind only when
                # the entry holds this one result: beside sibling results (parallel calls) it may be theirs.
                kind = entry.get("toolDenialKind") if results == 1 else None
                flag = (kind or "is_error") if block.get("is_error") else None
                copies[tid].append((stamp, result_text(block.get("content")), flag))
    calls = []
    for tid in order:
        found = copies[tid]
        timed = [copy for copy in found if copy[0]]
        chosen = timed[0] if timed else (found[0] if found else (None, None, None))
        # Copies disagree only on WHETHER the result is an error: an api-request-blob copy cannot carry the entry's
        # toolDenialKind, so its "is_error" beside a "user-rejected" is the same label, less specific.
        flags = sorted({"error" if copy[2] else "none" for copy in found})
        calls.append({**uses[tid], "answered_at": chosen[0], "answer": chosen[1], "flag": chosen[2], "flags": flags, "texts": [copy[1] for copy in found]})
    return calls


def scan(path: Path) -> list[dict]:
    return scan_lines(path.read_text(encoding="utf-8").split("\n"))


def describe(prefix: str, name: str, calls: list[dict], full: bool, width: int) -> list[str]:
    out = [f"== {prefix}: {name}: {len(calls)} AskUserQuestion call(s)"]
    for n, call in enumerate(calls, 1):
        out.append(f"-- call {n}: asked {call['asked_at']}, answered {call['answered_at']}")
        for q in call["questions"]:
            text = q.get("question", "") if isinstance(q, dict) else str(q)
            if not full and len(text) > width:
                text = text[:width] + "..."
            out.append(f"   [{q.get('header', '') if isinstance(q, dict) else ''}] {text}")
        label = f"ANSWER ({call['flag']}): " if call["flag"] else "ANSWER: "
        out.append("   " + label + json.dumps(call["answer"], ensure_ascii=False))
        distinct = len(set(call["texts"]))
        which = "the first timestamped one is printed" if call["answered_at"] else "none carries a timestamp, so the first is printed"
        if distinct > 1:
            out.append(f"   NOTE: {len(call['texts'])} copies of this result carry {distinct} different texts; {which}")
        if len(call.get("flags", [])) > 1:
            out.append(f"   NOTE: some copies of this result are marked as an error and some are not; {which}")
    return out


def self_test() -> int:
    def entry(kind: str, stamp: str | None, block: dict, **extra: object) -> str:
        record: dict = {"type": kind, "message": {"content": [block]}, **extra}
        if stamp is not None:
            record["timestamp"] = stamp
        return json.dumps(record)

    def ask(call_id: str | None, questions: object = None) -> dict:
        block = {"type": "tool_use", "name": "AskUserQuestion", "input": {"questions": [{"header": "H", "question": "Q?"}]} if questions is None else questions}
        if call_id is not None:
            block["id"] = call_id
        return block

    def answer(call_id: str, content: object, **extra: object) -> dict:
        return {"type": "tool_result", "tool_use_id": call_id, "content": content, **extra}

    lines = [
        # a: the defect's shape -- the timed user entry, then its untimed blob copy.
        entry("assistant", "2026-11-13T02:41:20.747Z", ask("a")),
        entry("user", "2026-11-13T10:10:51.412Z", answer("a", "yes")),
        entry("api-request-blob", None, answer("a", "yes")),
        # b: the blob first, as in the calls the predecessor dated right.
        entry("assistant", "2026-11-13T01:50:37.407Z", ask("b")),
        entry("api-request-blob", None, answer("b", "no")),
        entry("user", "2026-11-13T01:57:00.209Z", answer("b", "no")),
        # c: only untimed copies, with two different texts.
        entry("assistant", "2026-11-14T00:00:00.000Z", ask("c")),
        entry("api-request-blob", None, answer("c", "maybe")),
        entry("api-request-blob", None, answer("c", "perhaps")),
        # d: an untimed copy of the asking message first, an empty-string timestamp next, then the timed one; two
        #    timed answers that differ; then an untimed copy of the question after them.
        entry("api-request-blob", None, ask("d")),
        entry("assistant", "", ask("d")),
        entry("assistant", "2026-11-15T00:00:00.000Z", ask("d")),
        entry("user", "2026-11-15T00:01:00.000Z", answer("d", "first")),
        entry("user", "2026-11-15T00:02:00.000Z", answer("d", "second")),
        entry("api-request-blob", None, ask("d")),
        # e: a result recorded before its question; f: a list-of-blocks answer the person rejected.
        entry("user", "2026-11-16T00:01:00.000Z", answer("e", "early")),
        entry("assistant", "2026-11-16T00:00:00.000Z", ask("e")),
        entry("assistant", "2026-11-17T00:00:00.000Z", ask("f")),
        entry("user", "2026-11-17T00:01:00.000Z", answer("f", [{"type": "text", "text": "no:"}, {"type": "text", "text": "do X"}], is_error=True), toolDenialKind="user-rejected"),
        # h: is_error with no toolDenialKind; i: a parallel entry whose other result was rejected; j: a rejection only
        #    a later copy records.
        entry("assistant", "2026-11-19T00:00:00.000Z", ask("h")),
        entry("user", "2026-11-19T00:01:00.000Z", answer("h", "tool failed", is_error=True)),
        entry("assistant", "2026-11-19T01:00:00.000Z", ask("i")),
        json.dumps({"type": "user", "timestamp": "2026-11-19T01:01:00.000Z", "toolDenialKind": "user-rejected", "message": {"content": [answer("i", "Yes, ship it"), answer("bash-1", "denied", is_error=True)]}}),
        entry("assistant", "2026-11-19T02:00:00.000Z", ask("j")),
        entry("user", "2026-11-19T02:01:00.000Z", answer("j", "stop")),
        entry("api-request-blob", None, answer("j", "stop", is_error=True)),
        # l: an entry that carries toolDenialKind and one result that is not an error.
        entry("assistant", "2026-11-19T04:00:00.000Z", ask("l")),
        entry("user", "2026-11-19T04:01:00.000Z", answer("l", "Approved"), toolDenialKind="user-rejected"),
        # o: the 7d425759 shape: a rejected answer, then its untimed blob copy, which can only say is_error.
        entry("assistant", "2026-11-19T05:00:00.000Z", ask("o")),
        entry("user", "2026-11-19T05:01:00.000Z", answer("o", "do it differently", is_error=True), toolDenialKind="user-rejected"),
        entry("api-request-blob", None, answer("o", "do it differently", is_error=True)),
        # k: an error result beside a rejected sibling in one entry.
        entry("assistant", "2026-11-19T03:00:00.000Z", ask("k")),
        json.dumps({"type": "user", "timestamp": "2026-11-19T03:01:00.000Z", "toolDenialKind": "user-rejected", "message": {"content": [answer("k", "Interrupted", is_error=True), answer("bash-2", "denied", is_error=True)]}}),
        # malformed: input null, a missing id; and noise.
        entry("assistant", "2026-11-18T00:00:00.000Z", ask("g", questions=None) | {"input": None}),
        entry("assistant", "2026-11-18T00:00:00.000Z", ask(None)),
        entry("assistant", "2026-11-18T01:00:00.000Z", ask("m") | {"input": "a string, not an object"}),
        entry("assistant", "2026-11-18T02:00:00.000Z", ask("n") | {"input": {"questions": None}}),
        "not json",
        json.dumps(["AskUserQuestion", "tool_result", "a"]),  # valid JSON, not an object, and past both line filters
        "",
    ]
    calls = scan_lines(lines)
    by_answer = {call["answer"]: call for call in calls}
    first = calls[0]
    checks = {
        "fifteen calls (a-o), d counted once, the id-less one skipped": len(calls) == 15,
        "o: a blob's bare is_error beside user-rejected is no disagreement": by_answer.get("do it differently", {}).get("flag") == "user-rejected" and not any("NOTE" in line for line in describe("x", "x", [by_answer.get("do it differently", first)], False, 240)),
        "l: an answer that is not an error is not labelled": by_answer.get("Approved", {}).get("flag", "missing") is None,
        "h: an is_error result is labelled is_error": by_answer.get("tool failed", {}).get("flag") == "is_error",
        "i: a sibling result's rejection does not label this answer": by_answer.get("Yes, ship it", {}).get("flag", "missing") is None,
        "a question that is not an object prints as text": describe("x", "x", [{"asked_at": None, "questions": ["plain"], "answered_at": None, "answer": None, "flag": None, "texts": []}], False, 240)[2] == "   [] plain",
        "j: a label only an untimed copy carries is noted, not printed": by_answer.get("stop", {}).get("flag", "missing") is None and any("some copies of this result are marked as an error and some are not" in line for line in describe("x", "x", [by_answer.get("stop", first)], False, 240)),
        "k: beside a sibling result, an error is is_error, not the entry's kind": by_answer.get("Interrupted", {}).get("flag") == "is_error",
        "a: dated from the user entry, not the later blob": first["answered_at"] == "2026-11-13T10:10:51.412Z" and first["answer"] == "yes",
        "b: dated from the user entry after the blob": calls[1]["answered_at"] == "2026-11-13T01:57:00.209Z" and calls[1]["answer"] == "no",
        "c: untimed only -> answered None, the first text": calls[2]["answered_at"] is None and calls[2]["answer"] == "maybe",
        "c: the note says none is timed": any("none carries a timestamp" in line for line in describe("x", "x", calls[2:3], False, 240)),
        "d: asked from the timed copy, not '' nor a later untimed one": calls[3]["asked_at"] == "2026-11-15T00:00:00.000Z",
        "d: the first timestamped answer wins": calls[3]["answered_at"] == "2026-11-15T00:01:00.000Z" and calls[3]["answer"] == "first",
        "d: differing timed copies are noted": any("the first timestamped one is printed" in line for line in describe("x", "x", calls[3:4], False, 240)),
        "e: a result before its question counts": "early" in by_answer and by_answer["early"]["answered_at"] == "2026-11-16T00:01:00.000Z",
        "f: list content joined, rejection labelled": any(line.startswith('   ANSWER (user-rejected): "no:\\ndo X"') for line in describe("x", "x", [by_answer.get("no:\ndo X", first)], False, 240)),
        "g, m, n: a null or string input, or null questions, read as no questions": [call["questions"] for call in calls[-3:]] == [[], [], []],
        "a: no note for identical copies": not any("NOTE" in line for line in describe("x", "x", calls[:1], False, 240)),
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name in failed:
        print(f"FAIL {name}")
    if not failed:
        print(f"self-test: all {len(checks)} checks passed")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sessions", nargs="*", help="session-id prefixes")
    ap.add_argument("--full", action="store_true", help="print each question's text in full")
    ap.add_argument("--width", type=int, default=240)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.sessions:
        ap.error("name at least one session-id prefix")
    for prefix in args.sessions:
        path = transcript(prefix)
        for line in describe(prefix, path.name, scan(path), args.full, args.width):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
