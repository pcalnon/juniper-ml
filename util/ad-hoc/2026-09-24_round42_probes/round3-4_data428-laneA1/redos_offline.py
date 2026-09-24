"""Lane A1 (round 3, juniper-data#428): time every caller-controlled parse on the conditional paths.

Measures, with the code at 3a76a4c loaded from the scratch tree:

* ``_ENTITY_TAG_LIST.fullmatch`` directly (BYPASSING the cap) at sizes from 256 to 1 MiB, for
  hostile shapes -- whitespace-, comma-, quote- and ``W/``-heavy, many short elements, failing
  at the end and failing at the start. Direct calls far over the cap show the asymptotics the
  cap would otherwise hide: a quadratic parse is milliseconds at 8 KiB but minutes at 1 MiB.
* the public entry points (``if_none_match_hits``, ``if_match_fails``,
  ``if_none_match_fails_write``, ``write_preconditions_hold``, ``read_precondition_status``)
  at 8191 / 8192 / 8193 characters, so the cap path and the parse path are both timed.
* the after-parse cost: ``_ENTITY_TAG.finditer`` over a well-formed field at the cap carrying
  the maximum number of tags, compared against the current ETag.
* the dataset-id validator on the path parameter.

Each number is the MINIMUM of several timed repetitions (the least-noise estimator of the
work done), in microseconds.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time

SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1"
sys.path.insert(0, f"{SCRATCH}/tree-3a76a4c")
import juniper_data  # noqa: E402

assert juniper_data.__file__.startswith(f"{SCRATCH}/tree-3a76a4c/"), juniper_data.__file__
from juniper_data.api import http_cache as hc  # noqa: E402
from juniper_data.storage import local_fs  # noqa: E402

CAP = hc.MAX_PRECONDITION_FIELD_LENGTH
LIST = hc._ENTITY_TAG_LIST
TAG = hc._ENTITY_TAG
SERVER_ETAG = hc.body_etag(b"x")  # a real strong tag: "<64 hex>"
OPAQUE = SERVER_ETAG.strip('"')


def fit(unit: str, n: int) -> str:
    """Repeat ``unit`` to exactly n characters (truncating the last copy)."""
    return (unit * (n // len(unit) + 1))[:n]


# shape name -> builder(n) returning a string of length n (or about n)
SHAPES = {
    # the original attack family, failing on a trailing garbage char
    "', ' * k + x": lambda n: fit(", ", n - 1) + "x",
    "',\\t\\t' * k + x": lambda n: fit(",\t\t", n - 1) + "x",
    "' , ' * k + x": lambda n: fit(" , ", n - 1) + "x",
    "' ' * n + x": lambda n: fit(" ", n - 1) + "x",
    "'\\t' * n + x": lambda n: fit("\t", n - 1) + "x",
    "',' * n + x": lambda n: fit(",", n - 1) + "x",
    "', ' * k (accepted)": lambda n: fit(", ", n),
    # quote-heavy
    "'\"' * n (odd/even)": lambda n: fit('"', n),
    "'\"\"' * k + '\"'": lambda n: fit('""', n - 1) + '"',
    "'\"' + ' ,' * k (unterminated)": lambda n: '"' + fit(" ,", n - 1),
    "'\"' + ',' * k (unterminated)": lambda n: '"' + fit(",", n - 1),
    "', \"' * k (many opens)": lambda n: fit(', "', n),
    "'\" \"' + ' ' * k + x": lambda n: '" "' + fit(" ", n - 4) + "x",
    # W/-heavy
    "'W/' * k + x": lambda n: fit("W/", n - 1) + "x",
    "'W/\"' * k": lambda n: fit('W/"', n),
    "'W/\"\",' * k + 'W/'": lambda n: fit('W/"",', n - 2) + "W/",
    "'W/\"a\" ' * k + x (no commas)": lambda n: fit('W/"a" ', n - 1) + "x",
    # many short elements
    "'\"\",' * k + x": lambda n: fit('"",', n - 1) + "x",
    "'\"\",' * k (accepted)": lambda n: fit('"",', n),
    "'\"a\" , ' * k + '\"'": lambda n: fit('"a" , ', n - 1) + '"',
    "'W/\"a\",\\t' * k + '\"'": lambda n: fit('W/"a",\t', n - 1) + '"',
    # fails at the START (should be O(1))
    "x + ', ' * k": lambda n: "x" + fit(", ", n - 1),
    # accepted, maximal tag count
    "'W/\"\",' * k (accepted, padded)": lambda n: fit('W/"",', n - (n % 5)) + ' ' * (n % 5),
}

SIZES = [256, 1024, 4096, 8191, 8192, 16384, 65536, 262144, 1048576]


def tmin(fn, reps: int) -> float:
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        dt = time.perf_counter_ns() - t0
        best = min(best, dt)
    return best / 1000.0  # microseconds


results: dict = {"regex_direct": {}, "entry_points": {}, "after_parse": {}, "dataset_id": {}}
print(f"python {sys.version.split()[0]}  gil_enabled={getattr(sys, '_is_gil_enabled', lambda: True)()}  cap={CAP}")
print("\n== _ENTITY_TAG_LIST.fullmatch, direct (cap bypassed), min-of-reps microseconds ==")
hdr = f"{'shape':38s}" + "".join(f"{s:>11d}" for s in SIZES) + "   x(1M/8K)  per-char-ns@1M"
print(hdr)
worst_per_char = 0.0
for name, build in SHAPES.items():
    row = {}
    line = f"{name:38s}"
    for n in SIZES:
        s = build(n)
        reps = 30 if n <= 8192 else (8 if n <= 65536 else 3)
        us = tmin(lambda s=s: LIST.fullmatch(s), reps)
        row[n] = {"len": len(s), "us": us, "matched": LIST.fullmatch(s) is not None}
        line += f"{us:11.1f}"
    ratio = row[1048576]["us"] / max(row[8192]["us"], 1e-9)
    per_char = row[1048576]["us"] * 1000 / row[1048576]["len"]
    worst_per_char = max(worst_per_char, per_char)
    line += f"   {ratio:8.1f}   {per_char:8.2f}"
    print(line)
    results["regex_direct"][name] = row
print(f"(linear => x(1M/8K) ~ 128; quadratic => ~16384)   worst per-char cost at 1 MiB: {worst_per_char:.2f} ns")

print("\n== public entry points at / around the cap (min-of-30 microseconds) ==")
entry = {
    "if_none_match_hits": lambda f: hc.if_none_match_hits(f, SERVER_ETAG),
    "if_match_fails": lambda f: hc.if_match_fails(f, SERVER_ETAG),
    "if_none_match_fails_write": lambda f: hc.if_none_match_fails_write(f, SERVER_ETAG),
    "write_preconditions_hold(IM,INM)": lambda f: hc.write_preconditions_hold(f, f, SERVER_ETAG),
    "read_precondition_status(IM,INM)": lambda f: hc.read_precondition_status(f, f, SERVER_ETAG),
}
worst_entry = (0.0, None)
for name, build in SHAPES.items():
    for n in (8191, 8192, 8193, 1048576):
        s = build(n)
        assert len(s) == n, (name, n, len(s))
        for ename, fn in entry.items():
            us = tmin(lambda s=s, fn=fn: fn(s), 30 if n <= 8193 else 5)
            results["entry_points"].setdefault(ename, {}).setdefault(name, {})[n] = us
            if n <= 8192 and us > worst_entry[0]:
                worst_entry = (us, (ename, name, n))
print(f"worst entry-point time for a field AT OR UNDER the cap: {worst_entry[0]:.1f} us  ({worst_entry[1]})")
for ename in entry:
    at = max(results["entry_points"][ename][s][8192] for s in SHAPES)
    over = max(results["entry_points"][ename][s][8193] for s in SHAPES)
    huge = max(results["entry_points"][ename][s][1048576] for s in SHAPES)
    print(f"  {ename:34s} worst@8192={at:8.1f}us  worst@8193={over:6.2f}us  worst@1MiB={huge:6.2f}us")

print("\n== after-parse cost: many tags vs the current ETag (strong and weak compare) ==")
for label, unit in (("'\"\",' tiny tags", '"",'), ("'W/\"\",' tiny weak tags", 'W/"",'), ("64-hex non-matching tags", '"' + "f" * 64 + '",'), ("64-hex tags sharing the length and a 63-char prefix", '"' + OPAQUE[:-1] + ("0" if OPAQUE[-1] != "0" else "1") + '",')):
    k = CAP // len(unit)
    field = (unit * k).rstrip(",")
    assert len(field) <= CAP and hc._well_formed(field)
    ntags = sum(1 for _ in TAG.finditer(field))
    us_list = tmin(lambda: hc._list_names(field, SERVER_ETAG, strong=True), 30)
    us_scan = tmin(lambda: sum(1 for _ in TAG.finditer(field)), 30)
    # the same list with the CURRENT tag as its last element: the compare loop runs to the end and hits
    kk = (CAP - len(SERVER_ETAG) - 1) // len(unit)
    hitfield = unit * kk + SERVER_ETAG
    assert len(hitfield) <= CAP and hc.if_none_match_hits(hitfield, SERVER_ETAG) and not hc.if_match_fails(hitfield, SERVER_ETAG)
    us_hit_last = tmin(lambda: hc.if_none_match_hits(hitfield, SERVER_ETAG), 30)
    results["after_parse"][label] = {"len": len(field), "tags": ntags, "list_names_us": us_list, "finditer_us": us_scan, "hit_on_last_tag_us": us_hit_last}
    print(f"  {label:52s} len={len(field)} tags={ntags:5d}  _list_names={us_list:8.1f}us  finditer-only={us_scan:8.1f}us  hit-on-last={us_hit_last:8.1f}us")

print("\n== path parameter: LocalFS dataset-id validation ==")
for label, did in (("128 valid chars", "a" * 128), ("129 valid chars", "a" * 129), ("64 KiB of 'a'", "a" * 65536), ("64 KiB of '.'", "a" + "." * 65535), ("'..' at the end of 64 KiB", "a" * 65534 + "..")):
    def v(did=did):
        try:
            local_fs._validate_dataset_id(did)
            return True
        except ValueError:
            return False
    us = tmin(v, 30)
    results["dataset_id"][label] = {"us": us, "valid": v()}
    print(f"  {label:28s} valid={v()!s:5s} {us:8.2f}us")

with open(f"{SCRATCH}/redos_offline_results.json", "w") as fh:
    json.dump(results, fh, indent=1, default=str)
print("\nwrote redos_offline_results.json")
