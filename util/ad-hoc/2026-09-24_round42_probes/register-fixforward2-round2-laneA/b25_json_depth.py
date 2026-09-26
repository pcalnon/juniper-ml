#!/usr/bin/env python3
"""Lane A round 2: the probe comment's JSON-depth claims on CPython 3.13 (run with the pinned venv's python):
a balanced 5,000-deep array parses; a balanced 10,000-deep one raises RecursionError; an UNBALANCED one fails as a
JSONDecodeError "before it recurses that far". Also the decode_cursor path: bytes -> json.loads."""
import json
import sys

print(sys.version.split()[0], "recursion limit", sys.getrecursionlimit())
for label, s in [
    ("balanced 5000", "[" * 5000 + "]" * 5000),
    ("balanced 10000", "[" * 10000 + "]" * 10000),
    ("unbalanced open 10000", "[" * 10000),
    ("unbalanced open 10000 + 1 close", "[" * 10000 + "]"),
    ("unbalanced 10000 open, 9999 close", "[" * 10000 + "]" * 9999),
    ("unbalanced 5000 open", "[" * 5000),
]:
    try:
        json.loads(s.encode("ascii"))
        print(f"  {label:36} parsed")
    except RecursionError as e:
        print(f"  {label:36} RecursionError: {e}")
    except json.JSONDecodeError as e:
        print(f"  {label:36} JSONDecodeError: {e.msg} at pos {e.pos}")
