"""Print numbered line ranges of a file: lines.py FILE A-B [C-D ...]."""

import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
for spec in sys.argv[2:]:
    a, b = (int(x) for x in spec.split("-"))
    print(f"...... {spec}")
    for n in range(a, min(b, len(lines)) + 1):
        print(f"{n}\t{lines[n - 1]}")
