"""Lane A1: second functional pass.

1. Re-runs the four over-cap probes of live_functional.py that were INVALID as written: their
   extra character was leading whitespace, which the HTTP parser strips before the app sees
   the field (so the app saw exactly 8192 / 8190 characters). Here the padding is INTERIOR
   OWS after a comma, which survives, so the field the app sees really is over the cap.
2. '*' followed or preceded by characters Python's str.strip() removes but RFC 9110 OWS
   (SP / HTAB) does not include -- VT, FF, NEL (0x85), NBSP (0xA0), 0x1C-0x1F.
3. A tag that survives storage but not rendering (a lone surrogate), on a SEPARATE dataset.
"""

import json
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1")
from rawhttp import build, jbody, request  # noqa: E402

PORT = int(sys.argv[1])
CAP = 8192
OUT = {}


def rec(label, status, hdrs, body, secs, expect=None):
    ok = "" if expect is None else ("  OK" if status == expect else f"  <-- EXPECTED {expect}")
    print(f"  {label:84s} -> {status}  {secs * 1000:8.1f} ms{ok}")
    OUT[label] = {"status": status, "ms": round(secs * 1000, 2), "expect": expect, "body": body[:200].decode("latin-1")}
    return status


def create(seed: int) -> str:
    s, h, b, t = request(PORT, "POST", "/v1/datasets", body=jbody({"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 50, "seed": seed}, "persist": True}))
    assert s in (200, 201), (s, b[:300])
    return json.loads(b)["dataset_id"]


DSID = create(7)
META, TAGS = f"/v1/datasets/{DSID}", f"/v1/datasets/{DSID}/tags"
s, h, b, t = request(PORT, "GET", META)
ETAG = h["etag"][0]
print("dataset", DSID, "etag", ETAG, "tags", json.loads(b)["tags"])


def interior(total: int, last: str) -> str:
    """'"",' units, then interior spaces after the last comma, then ``last``: exactly ``total`` chars, no edge whitespace."""
    unit = '"",'
    k = (total - len(last) - 1) // len(unit)
    head = unit * k
    pad = total - len(head) - len(last)
    f = head + " " * pad + last
    assert len(f) == total and f == f.strip(" \t"), (len(f), total)
    return f


print("\n[1] over-cap probes with interior padding (no edge whitespace for the HTTP layer to strip)")
at, over = interior(CAP, ETAG), interior(CAP + 1, ETAG)
rec(f"GET INM len {len(at)} current tag last", *request(PORT, "GET", META, [("If-None-Match", at)]), expect=304)
rec(f"GET INM len {len(over)} current tag last", *request(PORT, "GET", META, [("If-None-Match", over)]), expect=200)
rec(f"GET IM  len {len(at)} current tag last", *request(PORT, "GET", META, [("If-Match", at)]), expect=200)
rec(f"GET IM  len {len(over)} current tag last", *request(PORT, "GET", META, [("If-Match", over)]), expect=412)
line2 = '""' + " " * (CAP - 4) + ',""'  # interior spaces; the line itself is under the cap
rec(f"GET INM 2 lines: current / a {len(line2)}-char line -> joined {len(ETAG) + 2 + len(line2)}", *request(PORT, "GET", META, [("If-None-Match", ETAG), ("If-None-Match", line2)]), expect=200)
names_nothing_over = interior(CAP + 1, '""')
rec(f"PATCH INM len {len(names_nothing_over)} (well-formed, names nothing) -> fail closed", *request(PORT, "PATCH", TAGS, [("If-None-Match", names_nothing_over)], jbody({"add_tags": ["over1"]})), expect=412)
rec(f"PATCH IM  len {len(over)} (current tag last) -> fail closed", *request(PORT, "PATCH", TAGS, [("If-Match", over)], jbody({"add_tags": ["over2"]})), expect=412)
s, h, b, t = request(PORT, "GET", META)
print("   tags now:", json.loads(b)["tags"], "(must contain neither over1 nor over2)")
OUT["tags_after_overcap_412s"] = json.loads(b)["tags"]

print("\n[2] '*' wrapped in characters str.strip() removes but RFC OWS does not")
for label, ch in (("VT \\x0b", "\x0b"), ("FF \\x0c", "\x0c"), ("FS \\x1c", "\x1c"), ("NEL \\x85", "\x85"), ("NBSP \\xa0", "\xa0")):
    val = "*" + ch
    try:
        st = rec(f"GET  IM  '*'+{label} on a read (malformed per RFC -> 412 expected)", *request(PORT, "GET", META, [("If-Match", val)]), expect=412)
        s, h, b, t = request(PORT, "GET", META)
        cur = h["etag"][0]
        st = rec(f"PATCH IM '*'+{label} (a stale/malformed precondition must not write)", *request(PORT, "PATCH", TAGS, [("If-Match", val)], jbody({"add_tags": [f"star-{ord(ch):02x}"]})), expect=412)
    except Exception as exc:  # noqa: BLE001
        print(f"   {label}: transport error {type(exc).__name__}: {exc}")
s, h, b, t = request(PORT, "GET", META)
OUT["tags_after_star_probes"] = json.loads(b)["tags"]
print("   tags now:", OUT["tags_after_star_probes"])

print("\n[3] a tag that is stored but cannot be rendered (lone surrogate), on its own dataset")
D2 = create(99)
M2, T2 = f"/v1/datasets/{D2}", f"/v1/datasets/{D2}/tags"
body = b'{"add_tags": ["\\ud800"]}'
rec("PATCH add_tags=['\\ud800'] (unconditional)", *request(PORT, "PATCH", T2, None, body), expect=None)
rec("GET metadata of that dataset afterwards", *request(PORT, "GET", M2), expect=None)
rec("GET metadata again (is the failure persistent?)", *request(PORT, "GET", M2), expect=None)
rec("GET artifact of that dataset", *request(PORT, "GET", M2 + "/artifact"), expect=None)
rec("GET /latest-style listing: /v1/datasets/filter?tags=x", *request(PORT, "GET", "/v1/datasets/filter"), expect=None)
rec("PATCH conditional If-Match * (precondition renders the meta under the lock)", *request(PORT, "PATCH", T2, [("If-Match", "*")], jbody({"add_tags": ["y"]})), expect=None)
rec("PATCH remove the bad tag, unconditional", *request(PORT, "PATCH", T2, None, b'{"remove_tags": ["\\ud800"]}'), expect=None)
rec("GET metadata after removing it", *request(PORT, "GET", M2), expect=None)
OUT["_datasets"] = {"main": DSID, "surrogate": D2}

with open("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1/live_functional2.json", "w") as fh:
    json.dump(OUT, fh, indent=1)
print("\nwrote live_functional2.json")
