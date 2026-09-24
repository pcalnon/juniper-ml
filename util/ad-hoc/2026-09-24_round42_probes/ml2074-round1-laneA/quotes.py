#!/usr/bin/env python3
"""Lane A: find the owner-ruling answers in two session transcripts (read-only).
Records are split on "\\n" (never splitlines()). Prints only question/answer text around the target
timestamp, or around the quoted strings, truncated."""
from __future__ import annotations

import json
import sys

T1 = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-happy-skipping-hollerith/bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl"
T2 = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-hazy-beaming-map/8f86dec2-21ea-43f2-911a-bb2314a822ec.jsonl"
QUOTES = [
    "Yes, same gate PR",
    "let's do option 1 now, and document this as a gap to be addressed in future work",
    "Amend policy: 0.x may break v1",
    "Keep while any split is fetched",
]


def records(path: str):
    with open(path, encoding="utf-8") as fh:
        data = fh.read()
    for i, line in enumerate(data.split("\n")):
        if not line.strip():
            continue
        try:
            yield i, json.loads(line)
        except json.JSONDecodeError:
            continue


def texts(obj) -> list[str]:
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(texts(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(texts(v))
    return out


def describe(path: str, ts_target: str | None) -> None:
    print(f"######## {path.rsplit('/', 2)[-2][-40:]}/{path.rsplit('/', 1)[-1]}")
    for i, rec in records(path):
        ts = rec.get("timestamp", "")
        blob = "\n".join(texts(rec.get("message", rec)))
        hit = [q for q in QUOTES if q in blob]
        if (ts_target and ts == ts_target) or (hit and rec.get("type") == "user"):
            role = rec.get("type")
            tur = rec.get("toolUseResult")
            print(f"--- line {i} ts={ts} type={role} quotes={hit} isSidechain={rec.get('isSidechain')}")
            if isinstance(tur, dict):
                qs = tur.get("questions")
                ans = tur.get("answers")
                if qs:
                    for q in qs:
                        print("   Q:", (q.get("question") or "")[:600])
                        for o in q.get("options", []) or []:
                            print("      opt:", (o.get("label") or "")[:200], "|", (o.get("description") or "")[:300])
                if ans:
                    for k, v in ans.items():
                        print("   A[", k[:300], "] =", repr(v)[:300])
            else:
                print("   text:", blob[:1500].replace("\n", " \\n "))


describe(T1, "2026-09-23T19:38:04.764Z")
describe(T2, None)
