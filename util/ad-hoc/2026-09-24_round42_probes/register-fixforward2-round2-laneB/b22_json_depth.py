#!/usr/bin/env python3
"""Lane B r2: what json.loads raises for balanced and unbalanced nesting at several depths (tests the probe's comment)."""
import json
import sys

print(sys.version.split()[0], "recursionlimit", sys.getrecursionlimit())
for depth in (1000, 2000, 5000, 8000, 9000, 10000, 20000):
    for label, s in (("balanced", "[" * depth + "]" * depth), ("unbalanced", "[" * depth)):
        try:
            json.loads(s)
            r = "parsed"
        except RecursionError:
            r = "RecursionError"
        except json.JSONDecodeError:
            r = "JSONDecodeError"
        print(f"  depth {depth:6} {label:10} {r}")
