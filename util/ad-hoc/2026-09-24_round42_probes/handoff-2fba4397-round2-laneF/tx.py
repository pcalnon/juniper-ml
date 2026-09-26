#!/usr/bin/env python3
"""Transcript helper for handoff round-2 lane F2 (read-only).

Usage:
  tx.py xsession            -> list cross-session messages (ts, first 400 chars)
  tx.py grep PATTERN [N]    -> records whose text matches regex PATTERN (prints ts, type, N chars around)
  tx.py user                -> user-typed (non tool_result, non cross-session) messages
  tx.py at TS               -> full text of records whose timestamp starts with TS
  tx.py tooluse NAME        -> tool_use inputs for tool NAME (ts + input json truncated)
"""
import json
import re
import sys

PATH = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-fizzy-hugging-dream/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl"


def records(path=PATH):
    with open(path, encoding="utf-8") as fh:
        data = fh.read()
    for line in data.split("\n"):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def text_of(rec):
    msg = rec.get("message")
    out = []
    if isinstance(msg, dict):
        c = msg.get("content")
        if isinstance(c, str):
            out.append(c)
        elif isinstance(c, list):
            for part in c:
                if not isinstance(part, dict):
                    continue
                t = part.get("type")
                if t == "text":
                    out.append(part.get("text", ""))
                elif t == "tool_result":
                    cc = part.get("content")
                    if isinstance(cc, str):
                        out.append(cc)
                    elif isinstance(cc, list):
                        for p in cc:
                            if isinstance(p, dict) and p.get("type") == "text":
                                out.append(p.get("text", ""))
                elif t == "tool_use":
                    out.append("TOOL_USE " + part.get("name", "") + " " + json.dumps(part.get("input"), ensure_ascii=False))
    elif rec.get("type") == "queue-operation":
        out.append(json.dumps(rec, ensure_ascii=False))
    return "\n".join(out)


def main():
    mode = sys.argv[1]
    if mode == "xsession":
        for r in records():
            t = text_of(r)
            if "<cross-session-message" in t and r.get("type") in ("user", "queue-operation"):
                print("=====", r.get("timestamp"), r.get("type"))
                print(t[: int(sys.argv[2]) if len(sys.argv) > 2 else 600])
    elif mode == "grep":
        pat = re.compile(sys.argv[2])
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 300
        for r in records():
            t = text_of(r)
            for m in pat.finditer(t):
                s = max(0, m.start() - n)
                e = min(len(t), m.end() + n)
                print("=====", r.get("timestamp"), r.get("type"))
                print(t[s:e])
    elif mode == "user":
        for r in records():
            if r.get("type") != "user":
                continue
            msg = r.get("message", {})
            c = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(c, str):
                if "<cross-session-message" in c:
                    continue
                print("=====", r.get("timestamp"))
                print(c[:800])
            elif isinstance(c, list):
                kinds = {p.get("type") for p in c if isinstance(p, dict)}
                if "tool_result" in kinds:
                    continue
                t = text_of(r)
                if "<cross-session-message" in t:
                    continue
                print("=====", r.get("timestamp"))
                print(t[:800])
    elif mode == "at":
        ts = sys.argv[2]
        for r in records():
            if str(r.get("timestamp", "")).startswith(ts):
                print("=====", r.get("timestamp"), r.get("type"))
                print(text_of(r))
    elif mode == "tooluse":
        name = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 400
        for r in records():
            msg = r.get("message")
            if not isinstance(msg, dict):
                continue
            c = msg.get("content")
            if not isinstance(c, list):
                continue
            for part in c:
                if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == name:
                    print("=====", r.get("timestamp"), part.get("id"))
                    print(json.dumps(part.get("input"), ensure_ascii=False)[:n])


if __name__ == "__main__":
    main()
