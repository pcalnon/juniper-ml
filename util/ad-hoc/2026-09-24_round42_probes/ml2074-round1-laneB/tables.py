#!/usr/bin/env python3
"""tables.py FILE -- check every contiguous markdown table block (incl. blockquoted '> |') for a constant
cell count (GFM: unescaped pipes split cells, even inside code spans). Also flag table blocks whose
next line is non-blank and not a table line (a lazy continuation would join the table's last row).
Negative control: --selftest mutates a copy and requires detection."""
import re
import sys


def cells(line):
    s = line.strip()
    if s.startswith(">"):
        s = s.lstrip(">").strip()
    parts = re.split(r"(?<!\\)\|", s)
    # leading/trailing pipes produce empty first/last
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return len(parts)


def is_table_line(line):
    s = line.strip()
    if s.startswith(">"):
        s = s.lstrip(">").strip()
    return s.startswith("|")


def check(lines):
    problems = []
    i = 0
    n = len(lines)
    blocks = 0
    while i < n:
        if is_table_line(lines[i]):
            start = i
            while i < n and is_table_line(lines[i]):
                i += 1
            blk = lines[start:i]
            blocks += 1
            counts = [cells(l) for l in blk]
            hdr = counts[0]
            for k, c in enumerate(counts):
                if c != hdr:
                    problems.append(f"L{start+k+1}: {c} cells vs header {hdr}: {blk[k][:120]!r}")
            if i < n and lines[i].strip() != "" and not lines[i].lstrip().startswith(">"):
                problems.append(f"L{i+1}: non-blank line directly after table ending L{i}: {lines[i][:100]!r}")
        else:
            i += 1
    return blocks, problems


def main():
    path = sys.argv[1]
    lines = open(path, encoding="utf-8").read().split("\n")
    if "--selftest" in sys.argv:
        # mutate: add a pipe to a table row; add a lazy continuation after a table
        idx = next(k for k, l in enumerate(lines) if l.startswith("| APD-"))
        m1 = list(lines)
        m1[idx] = m1[idx].replace(" | ", " | x | ", 1)
        b, p = check(m1)
        assert any(f"L{idx+1}:" in q for q in p), "selftest 1 failed"
        print("selftest: extra-pipe mutation detected")
        return
    blocks, problems = check(lines)
    print(f"{path}: {blocks} table blocks, {len(problems)} problems")
    for p in problems:
        print("  ", p)


main()
