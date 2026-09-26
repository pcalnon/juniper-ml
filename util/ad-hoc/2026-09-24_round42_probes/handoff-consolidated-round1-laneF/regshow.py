import sys
from pathlib import Path
p = Path(sys.argv[1])
L = p.read_text(encoding="utf-8").split("\n")
w = int(sys.argv[2])
for spec in sys.argv[3:]:
    a, _, b = spec.partition("-")
    a = int(a); b = int(b) if b else a
    for i in range(a, b + 1):
        print(f"{i}: {L[i-1][:w]}")
    print("..")
