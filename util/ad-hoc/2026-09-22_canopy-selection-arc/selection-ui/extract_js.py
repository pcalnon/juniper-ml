"""Print context windows around a needle in a (minified) JS file."""

import sys

path, needle = sys.argv[1], sys.argv[2]
before = int(sys.argv[3]) if len(sys.argv) > 3 else 600
after = int(sys.argv[4]) if len(sys.argv) > 4 else 900
limit = int(sys.argv[5]) if len(sys.argv) > 5 else 3
with open(path, encoding="utf-8") as fh:
    text = fh.read()
start = 0
count = 0
while count < limit:
    idx = text.find(needle, start)
    if idx == -1:
        break
    print(f"==== hit {count} @ {idx} ====")
    print(text[max(0, idx - before) : idx + after])
    start = idx + len(needle)
    count += 1
print(f"total occurrences: {text.count(needle)}")
