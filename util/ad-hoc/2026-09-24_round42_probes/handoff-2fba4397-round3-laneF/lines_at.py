"""Print numbered lines of a file: lines_at.py FILE N [N ...] (N may be A-B). Truncates at 420 chars."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").split("\n")
for spec in sys.argv[2:]:
    if "-" in spec:
        a, b = (int(x) for x in spec.split("-"))
    else:
        a = b = int(spec)
    for n in range(a, b + 1):
        print(f"L{n}: {lines[n - 1][:420]}")
    print("---")
