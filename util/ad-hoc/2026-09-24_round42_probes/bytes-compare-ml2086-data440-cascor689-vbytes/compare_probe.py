"""Adversarial correctness probe for APIKeyAuth.validate's bytes compare.

Usage: python compare_probe.py <module> [<sys.path entry> ...]
  module is one of: juniper_service_core.security | juniper_data.api.security | api.security

Checks, against the REAL class:
  1. totality + exactness over EVERY code point U+0000..U+10FFFF as a one-char presented key,
     against a configured set that mixes ASCII, latin-1, astral and lone-surrogate keys;
  2. exactness over a hand-built adversarial pair list (surrogate pairs vs astral, escape twins,
     NUL, whitespace, empty, long, combining vs precomposed) in BOTH directions;
  3. 200k random strings drawn from mixed ranges (incl. lone surrogates) vs a random key set;
  4. the loop walks every key (a spy counts compare_digest calls) whatever the match position;
  5. compare_digest is only ever handed bytes, never str;
  6. validate never raises for any str; None -> False; disabled -> True.
"""

import hmac
import importlib
import random
import sys
import time

mod_name = sys.argv[1]
for entry in reversed(sys.argv[2:]):
    sys.path.insert(0, entry)
mod = importlib.import_module(mod_name)
print("module:", mod.__file__)
APIKeyAuth = mod.APIKeyAuth

failures = []


def check(configured, presented, expect=None):
    auth = APIKeyAuth(list(configured))
    real = {k for k in configured if isinstance(k, str) and k.strip()}
    if expect is not None:
        want = expect
    elif not real:
        want = True  # every configured key blank -> auth disabled -> open
    else:
        want = presented in real
    try:
        got = auth.validate(presented)
    except Exception as exc:  # noqa: BLE001
        failures.append(("RAISE", configured, presented, repr(exc)))
        return
    if got is not want:
        failures.append(("WRONG", configured, presented, f"got {got!r} want {want!r}"))


# 1. every code point as a single-char key, against a mixed configured set
configured = ["real-key", "cl\xe9", "\xe9", "\udcc3\udca9", "\ud800", "\udcff", "\U0001f511", "\x85", "\xa0x"]
auth = APIKeyAuth(configured)
real = {k for k in configured if k.strip()}  # "\x85" is whitespace-only -> filtered by the blank rule
t0 = time.perf_counter()
raised = wrong = 0
for cp in range(0x110000):
    s = chr(cp)
    try:
        got = auth.validate(s)
    except Exception as exc:  # noqa: BLE001
        raised += 1
        if raised < 5:
            failures.append(("RAISE", "mixed-set", s, repr(exc)))
        continue
    if got is not (s in real):
        wrong += 1
        if wrong < 5:
            failures.append(("WRONG", "mixed-set", s, f"got {got}"))
print(f"[1] 0x110000 code points: raised={raised} wrong={wrong} ({time.perf_counter() - t0:.1f}s)")

# 2. adversarial pairs, both directions
pairs = [
    (chr(0x1F600), chr(0xD83D) + chr(0xDE00)),  # astral vs its surrogate pair as two code units
    (chr(0x1F511), chr(0xD83D) + chr(0xDD11)),
    (chr(0x10000), chr(0xD800) + chr(0xDC00)),  # a pair that UTF-16 would join
    (chr(0x10FFFF), chr(0xDBFF) + chr(0xDFFF)),
    (chr(0xE9), chr(0xDCC3) + chr(0xDCA9)),  # surrogateescape twins
    (chr(0xFF), chr(0xDCFF)),  # latin-1 vs escaped byte
    ("e" + chr(0x301), chr(0xE9)),  # combining vs precomposed
    ("key" + chr(0), "key"),
    (chr(0), chr(0) * 2),
    ("k", "k "),
    (" k", "k"),
    (chr(0xA0) + "k", " k"),
    (chr(0x85) + "k", chr(10) + "k"),
    ("ab", "ab" + chr(0xD800)),
    ("a" * 100_000, "a" * 99_999 + "b"),
    (chr(0x10FFFF) * 10_000, chr(0x10FFFF) * 10_000),
    (chr(0xD800) * 10_000, chr(0xD800) * 9_999 + chr(0xDC00)),
]
for a, b in pairs:
    for configured_key, presented in ((a, b), (b, a), (a, a), (b, b)):
        if configured_key.strip():
            check([configured_key], presented)
# empty / whitespace presented against a real key
for presented in ["", " ", "\t", chr(0xA0), chr(0x2028), chr(0x3000)]:
    check(["real-key"], presented)
print(f"[2] adversarial pairs done; failures so far: {len(failures)}")

# 3. random strings
rng = random.Random(20260924)
ranges = [(0x20, 0x7E), (0x00, 0xFF), (0x100, 0xD7FF), (0xD800, 0xDFFF), (0xE000, 0xFFFF), (0x10000, 0x10FFFF)]


def rand_str(n):
    out = []
    for _ in range(n):
        lo, hi = rng.choice(ranges)
        out.append(chr(rng.randint(lo, hi)))
    return "".join(out)


t0 = time.perf_counter()
for i in range(200_000):
    keys = [rand_str(rng.randint(1, 6)) for _ in range(rng.randint(1, 3))]
    if rng.random() < 0.3:
        presented = rng.choice(keys)
    else:
        presented = rand_str(rng.randint(0, 6))
    check(keys, presented)
print(f"[3] 200k random strings done in {time.perf_counter() - t0:.1f}s; failures so far: {len(failures)}")

# 4 + 5. spy: every key walked, bytes only
calls = []
orig = hmac.compare_digest


def spy(a, b):
    calls.append((type(a).__name__, type(b).__name__))
    return orig(a, b)


keys = [f"key-{i}" for i in range(7)]
auth = APIKeyAuth(keys)
mod.hmac.compare_digest = spy
try:
    for presented in keys + ["nope", "\xa0", ""]:
        calls.clear()
        auth.validate(presented)
        if len(calls) != len(keys):
            failures.append(("SHORT-CIRCUIT", keys, presented, f"{len(calls)} compares for {len(keys)} keys"))
        if any(t != ("bytes", "bytes") for t in calls):
            failures.append(("NON-BYTES", keys, presented, str(set(calls))))
finally:
    mod.hmac.compare_digest = orig
print(f"[4/5] walk-every-key + bytes-only spy done; failures so far: {len(failures)}")

# 6. None, disabled
if APIKeyAuth(["k"]).validate(None) is not False:
    failures.append(("NONE", ["k"], None, "not False"))
if APIKeyAuth([]).validate("\xa0") is not True:
    failures.append(("DISABLED", [], "\xa0", "not True"))
if APIKeyAuth(["", "  ", "\t"]).enabled:
    failures.append(("BLANK-ENABLES", ["", "  "], None, "enabled"))

print(f"TOTAL FAILURES: {len(failures)}")
for f in failures[:20]:
    kind, conf, pres, detail = f
    print("  ", kind, repr(conf)[:60], repr(pres)[:40], detail[:120])
