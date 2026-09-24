"""Time the shipped (new) and replaced (old) entity-tag list grammars on adversarial families.

Linear means: doubling n roughly doubles the time. Each measurement is the best of 5 runs.
"""

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from juniper_data.api import http_cache  # noqa: E402

NEW = http_cache._ENTITY_TAG_LIST
OLD = re.compile(r'[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*(?:,[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*)*')
print("module:", http_cache.__file__)


def best(pattern: re.Pattern, text: str, reps: int = 5) -> float:
    out = []
    for _ in range(reps):
        t0 = time.perf_counter()
        pattern.fullmatch(text)
        out.append(time.perf_counter() - t0)
    return min(out)


FAMILIES = {
    "', ' * n + 'x'": lambda n: ", " * (n // 2) + "x",
    "',\\t\\t' * n + 'x'": lambda n: ",\t\t" * (n // 3) + "x",
    "' , ' * n + 'x'": lambda n: " , " * (n // 3) + "x",
    "unterminated '\"' + 'a'*n": lambda n: '"' + "a" * n,
    "'W/' * n": lambda n: "W/" * (n // 2),
    "'\"\",' * n + 'x'": lambda n: '"",' * (n // 3) + "x",
    "'W/\"' * n": lambda n: 'W/"' * (n // 3),
    "'\"a\" ' * n + 'x' (no commas)": lambda n: '"a" ' * (n // 4) + "x",
    "'\",' * n": lambda n: '",' * (n // 2),
    "', \"' * n (open quotes)": lambda n: ', "' * (n // 3),
    "'\"a\" \\t,' * n + 'x'": lambda n: '"a" \t,' * (n // 6) + "x",
    "' ' * n + 'x'": lambda n: " " * n + "x",
}
print("\nNEW pattern, ms at n = 1024, 2048, 4096, 8192 chars (ratio 8192/4096):")
for label, make in FAMILIES.items():
    times = [best(NEW, make(n)) * 1000 for n in (1024, 2048, 4096, 8192)]
    print(f"  {label:34s} " + "  ".join(f"{t:8.3f}" for t in times) + f"   x{times[3] / max(times[2], 1e-9):.2f}")

print("\nOLD pattern on the test's three hostile families (ms), growth per element:")
for label, unit, ks in (("', '", ", ", (14, 16, 18, 20, 21)), ("',\\t\\t'", ",\t\t", (8, 9, 10, 11, 12)), ("' , '", " , ", (8, 9, 10, 11, 12))):
    prev = None
    row = []
    for k in ks:
        t = best(OLD, unit * k + "x", reps=1) * 1000
        row.append(f"k={k}:{t:9.1f}" + (f" (x{t / prev:.2f})" if prev else ""))
        prev = t
    print(f"  {label:8s} " + "  ".join(row))

print("\nNEW on the test's HOSTILE fields (ms):")
for f in (", " * 30 + "x", ",\t\t" * 22 + "x", " , " * 26 + "x"):
    print(f"  len={len(f):3d} {best(NEW, f) * 1000:.4f} ms, matches={NEW.fullmatch(f) is not None}")
