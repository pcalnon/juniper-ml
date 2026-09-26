#!/usr/bin/env python3
"""Lane A: my own census of primer-line citations past 5758 in the register, independent of the repo's census.

Candidate set: EVERY maximal 4-digit run (not inside a longer digit run) whose value is 5759..9983, whatever
precedes or follows it -- including shapes the repo census's regex excludes (`L7950`, `PRIMER.md:7950`,
`#L7950`, `7,950`-style groups are listed separately). Each candidate is then bucketed by explicit, printed
rules; nothing is dropped silently. The 'primer?' bucket is printed with the head primer's text for reading.

usage: a07_my_citation_census.py <register> <primer> [--all]
"""
import re
import sys

reg_path, primer_path = sys.argv[1], sys.argv[2]
show_all = "--all" in sys.argv
reg = open(reg_path, encoding="utf-8").read().split("\n")
primer = open(primer_path, encoding="utf-8").read().split("\n")
LAST = len(primer)

RUN = re.compile(r"\d+")
buckets: dict[str, list] = {}


def bucket(name, item):
    buckets.setdefault(name, []).append(item)


for i, line in enumerate(reg, 1):
    for m in RUN.finditer(line):
        s = m.group(0)
        if len(s) != 4:
            continue
        n = int(s)
        if not 5758 < n <= LAST:
            continue
        a, b = m.start(), m.end()
        pre = line[max(0, a - 40) : a]
        post = line[b : b + 25]
        prev = line[a - 1] if a else ""
        nxt = line[b] if b < len(line) else ""
        item = (i, n, pre, post)
        if prev and (prev.isalpha() and prev not in "L") or (nxt and nxt.isalpha()):
            bucket("glued-to-letters (sha/identifier)", item)
        elif prev == "L":
            bucket("L-prefixed", item)
        elif prev == "#":
            bucket("#-prefixed", item)
        elif prev == ",":
            bucket("comma-group (x,NNNN)", item)
        elif prev == ":" and re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0|host|http)[^ ]*:$", pre):
            bucket("host:port", item)
        elif prev == ":" and re.search(r"PRIMER[^ ]*:$", pre):
            bucket("PRIMER.md:NNNN anchor", item)
        elif prev == ":":
            bucket("file:line (other file)", item)
        elif re.search(r"(?i)\bports?\b[^.]{0,20}$", pre) or re.search(r"^/(tcp|udp)", post):
            bucket("port", item)
        elif prev in "./" or nxt == ".":
            bucket("dotted/path", item)
        else:
            bucket("primer?", item)

for name, items in buckets.items():
    print(f"== {name}: {len(items)}")
    if name == "primer?" or show_all:
        for i, n, pre, post in items:
            t = primer[n - 1].strip()
            print(f"  L{i:<5} {n}  ...{pre[-40:]}[{n}]{post}...")
            print(f"            primer {n}: {'<BLANK>' if not t else t[:140]}")
    else:
        for i, n, pre, post in items:
            print(f"  L{i:<5} {n}  ...{pre[-40:]}[{n}]{post}...")
# thousands-grouped numbers that would read as a primer line if the comma were dropped
grouped = []
for i, line in enumerate(reg, 1):
    for m in re.finditer(r"(?<![\d,])(\d),(\d{3})(?![\d,])", line):
        n = int(m.group(1) + m.group(2))
        if 5758 < n <= LAST:
            grouped.append((i, m.group(0), line[max(0, m.start() - 40) : m.end() + 20]))
print(f"== thousands-grouped 5,759..9,983: {len(grouped)}")
for i, g, ctx in grouped:
    print(f"  L{i:<5} {g}  ...{ctx}...")
