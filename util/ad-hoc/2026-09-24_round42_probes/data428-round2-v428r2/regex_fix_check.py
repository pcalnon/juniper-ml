"""Check a candidate linear rewrite of _ENTITY_TAG_LIST: same language, no backtracking blowup."""

import itertools
import random
import re
import sys
import time

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr")
from juniper_data.api.http_cache import _ENTITY_TAG_LIST as ORIG  # noqa: E402

FIXED = re.compile(r'[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?(?:,[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?)*')

alphabet = [" ", "\t", ",", '"', "W", "/", "a", "x", "*"]
mismatch = 0
checked = 0
# exhaustive up to length 6
for n in range(0, 7):
    for tup in itertools.product(alphabet, repeat=n):
        s = "".join(tup)
        checked += 1
        if (ORIG.fullmatch(s) is None) != (FIXED.fullmatch(s) is None):
            mismatch += 1
            if mismatch < 5:
                print("MISMATCH", repr(s))
rng = random.Random(0)
for _ in range(200000):
    s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
    checked += 1
    if (ORIG.fullmatch(s) is None) != (FIXED.fullmatch(s) is None):
        mismatch += 1
print(f"checked={checked} mismatches={mismatch}")
for s in (", " * 5000 + "x", " " * 16000 + "x", ",   " * 3000 + "x"):
    t0 = time.perf_counter()
    FIXED.fullmatch(s)
    print(f"fixed len={len(s)} {1000 * (time.perf_counter() - t0):.2f} ms")
