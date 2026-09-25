#!/usr/bin/env python3
"""Lane B: count lines both ways and list str.splitlines() line-breaking characters in given files."""
import sys

BREAKERS = "\r\x0b\x0c\x1c\x1d\x1e\x85  "
for f in sys.argv[1:]:
    s = open(f, encoding="utf-8").read()
    found = sorted({hex(ord(c)) for c in s if c in BREAKERS})
    print(f.split("/")[-1][:60], "split:", len(s.split("\n")), "splitlines:", len(s.splitlines()), "breakers:", found)
