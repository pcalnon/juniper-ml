"""Lane A1: functional + boundary probes against the live scratch server (3a76a4c).

Covers task 3 (where the cap bites relative to the parse, how multi-line fields are joined
and counted, where '*' sits relative to the cap), the fail-closed write direction, the
invalid-id path on the artifact route, and the header-size limits of the HTTP layer in front
of it all. Every request is a raw HTTP/1.1 exchange on a fresh connection (rawhttp.py).
Writes live_functional.json with every observation.
"""

import json
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1")
from rawhttp import jbody, request  # noqa: E402

PORT = int(sys.argv[1])
CAP = 8192
OUT = {}


def rec(label, status, hdrs, body, secs, expect=None):
    ok = "" if expect is None else ("  OK" if status == expect else f"  <-- EXPECTED {expect}")
    print(f"  {label:78s} -> {status}  {secs * 1000:9.1f} ms{ok}")
    OUT[label] = {"status": status, "ms": round(secs * 1000, 2), "expect": expect, "etag": hdrs.get("etag"), "len": len(body)}
    return status


def joined_len(values):
    return len(", ".join(values))


# ---- setup: one dataset, created through the API --------------------------------------------
s, h, b, t = request(PORT, "POST", "/v1/datasets", body=jbody({"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 50, "seed": 7}, "persist": True}))
assert s in (200, 201), (s, b[:300])
DSID = json.loads(b)["dataset_id"]
print("dataset:", DSID)
s, h, b, t = request(PORT, "GET", f"/v1/datasets/{DSID}")
ETAG = h["etag"][0]
s, h, b, t = request(PORT, "GET", f"/v1/datasets/{DSID}/artifact")
AETAG = h["etag"][0]
print("metadata ETag:", ETAG, " artifact ETag:", AETAG, " artifact bytes:", len(b))
OUT["_dataset"] = {"id": DSID, "etag": ETAG, "artifact_etag": AETAG}
META = f"/v1/datasets/{DSID}"
ART = f"/v1/datasets/{DSID}/artifact"
TAGS = f"/v1/datasets/{DSID}/tags"

print("\n[a] multi-line joining and the cap on the COMBINED field (metadata GET, If-None-Match)")
rec("INM = current tag", *request(PORT, "GET", META, [("If-None-Match", ETAG)]), expect=304)
rec("INM on 2 lines: \"zzz\" / current", *request(PORT, "GET", META, [("If-None-Match", '"zzz"'), ("If-None-Match", ETAG)]), expect=304)
# many lines of "" then the current tag last: the largest N whose JOINED length fits, and N+1
n = 1
while joined_len(['""'] * (n + 1) + [ETAG]) <= CAP:
    n += 1
for vals in (['""'] * n + [ETAG], ['""'] * (n + 1) + [ETAG]):
    L = joined_len(vals)
    rec(f"INM on {len(vals)} lines, joined length {L} (each line <= {max(len(v) for v in vals)} chars)", *request(PORT, "GET", META, [("If-None-Match", v) for v in vals]), expect=304 if L <= CAP else 200)
# single line exactly at / over the cap, current tag last
unit = '"",'
k = (CAP - len(ETAG)) // len(unit)
at = unit * k + ETAG
at = " " * (CAP - len(at)) + at
over = " " + at
assert len(at) == CAP and len(over) == CAP + 1
rec(f"INM single line len {len(at)} (current tag last)", *request(PORT, "GET", META, [("If-None-Match", at)]), expect=304)
rec(f"INM single line len {len(over)} (current tag last)", *request(PORT, "GET", META, [("If-None-Match", over)]), expect=200)
# a line that would parse alone but pushes the joined field over the cap
rec("INM 2 lines: current tag / 8191 spaces+\"\" -> joined over cap", *request(PORT, "GET", META, [("If-None-Match", ETAG), ("If-None-Match", " " * (CAP - 2) + '""')]), expect=200)

print("\n[b] '*' and the cap")
rec("INM = *", *request(PORT, "GET", META, [("If-None-Match", "*")]), expect=304)
rec("INM = '*' + 8191 trailing spaces (the server strips OWS at the edges)", *request(PORT, "GET", META, [("If-None-Match", "*" + " " * (CAP - 1))]), expect=None)
rec("INM = '*' + 8191 spaces + ',' (len 8193, not strippable)", *request(PORT, "GET", META, [("If-None-Match", "*" + " " * (CAP - 1) + ",")]), expect=200)
rec("INM = * on two lines (joined '*, *': malformed)", *request(PORT, "GET", META, [("If-None-Match", "*"), ("If-None-Match", "*")]), expect=200)
rec("IM  = *", *request(PORT, "GET", META, [("If-Match", "*")]), expect=200)
rec("IM  = * on two lines -> malformed -> 412", *request(PORT, "GET", META, [("If-Match", "*"), ("If-Match", "*")]), expect=412)
rec("IM  = '*, \"x\"' -> malformed -> 412", *request(PORT, "GET", META, [("If-Match", '*, "x"')]), expect=412)

print("\n[c] If-Match on reads")
rec("IM = current", *request(PORT, "GET", META, [("If-Match", ETAG)]), expect=200)
rec("IM = W/current (strong compare)", *request(PORT, "GET", META, [("If-Match", "W/" + ETAG)]), expect=412)
rec("IM = garbage", *request(PORT, "GET", META, [("If-Match", "garbage")]), expect=412)
rec("IM = over cap, current tag last", *request(PORT, "GET", META, [("If-Match", over)]), expect=412)
rec("IM stale + INM current -> 412 wins", *request(PORT, "GET", META, [("If-Match", '"stale"'), ("If-None-Match", ETAG)]), expect=412)

print("\n[d] artifact route")
rec("INM = weak artifact tag", *request(PORT, "GET", ART, [("If-None-Match", AETAG)]), expect=304)
rec("INM = strong form of the checksum (weak compare)", *request(PORT, "GET", ART, [("If-None-Match", AETAG[2:])]), expect=304)
rec("IM  = weak artifact tag (strong compare never matches W/)", *request(PORT, "GET", ART, [("If-Match", AETAG)]), expect=412)
rec("IM  = *", *request(PORT, "GET", ART, [("If-Match", "*")]), expect=200)
rec("INM = original attack shape at the cap (', '*4095+'x')", *request(PORT, "GET", ART, [("If-None-Match", (", " * 4095) + "x")]), expect=200)
rec("IM  = original attack shape at the cap", *request(PORT, "GET", ART, [("If-Match", (", " * 4095) + "x")]), expect=412)
rec("artifact of an INVALID id ('bad!id')", *request(PORT, "GET", "/v1/datasets/bad!id/artifact", [("If-None-Match", '"x"')]), expect=400)
rec("artifact of a 129-char id", *request(PORT, "GET", "/v1/datasets/" + "a" * 129 + "/artifact"), expect=400)
rec("artifact of an absent valid id, INM *", *request(PORT, "GET", "/v1/datasets/absent-0-0000000000000000/artifact", [("If-None-Match", "*")]), expect=404)

print("\n[e] PATCH .../tags: fail-closed write direction (nothing may be written on a 412)")
rec("PATCH INM = *", *request(PORT, "PATCH", TAGS, [("If-None-Match", "*")], jbody({"add_tags": ["w1"]})), expect=412)
rec("PATCH INM = garbage", *request(PORT, "PATCH", TAGS, [("If-None-Match", "garbage")], jbody({"add_tags": ["w2"]})), expect=412)
rec("PATCH INM = original attack shape at the cap", *request(PORT, "PATCH", TAGS, [("If-None-Match", (", " * 4095) + "x")], jbody({"add_tags": ["w3"]})), expect=412)
rec("PATCH INM = over cap (well-formed, names nothing)", *request(PORT, "PATCH", TAGS, [("If-None-Match", " " + unit * ((CAP) // 3))], jbody({"add_tags": ["w4"]})), expect=412)
rec("PATCH INM = * on two lines", *request(PORT, "PATCH", TAGS, [("If-None-Match", "*"), ("If-None-Match", "*")], jbody({"add_tags": ["w5"]})), expect=412)
rec("PATCH IM = stale", *request(PORT, "PATCH", TAGS, [("If-Match", '"stale"')], jbody({"add_tags": ["w6"]})), expect=412)
rec("PATCH IM = W/current", *request(PORT, "PATCH", TAGS, [("If-Match", "W/" + ETAG)], jbody({"add_tags": ["w7"]})), expect=412)
s, h, b, t = request(PORT, "GET", META)
tags_now = json.loads(b)["tags"]
print("   tags after the 412s:", tags_now, "(must contain none of w1..w7)")
OUT["tags_after_412s"] = tags_now
rec("PATCH INM empty value (well-formed empty list) -> proceeds", *request(PORT, "PATCH", TAGS, [("If-None-Match", "")], jbody({"add_tags": ["e1"]})), expect=200)
s, h, b, t = request(PORT, "GET", META)
cur = h["etag"][0]
rec("PATCH IM on 2 lines: \"zzz\" / current -> proceeds", *request(PORT, "PATCH", TAGS, [("If-Match", '"zzz"'), ("If-Match", cur)], jbody({"remove_tags": ["e1"]})), expect=200)

print("\n[f] the HTTP layer in front: header size and count")
for size in (16 * 1024, 64 * 1024, 1024 * 1024, 8 * 1024 * 1024):
    val = (", " * (size // 2))[: size - 1] + "x"
    try:
        rec(f"INM single header of {size} bytes (garbage)", *request(PORT, "GET", META, [("If-None-Match", val)], timeout=120), expect=None)
    except Exception as exc:  # noqa: BLE001
        print(f"  INM single header of {size} bytes -> transport error {type(exc).__name__}: {exc}")
        OUT[f"INM single header of {size} bytes"] = {"error": f"{type(exc).__name__}: {exc}"}
for count in (1000, 20000, 100000):
    try:
        rec(f"{count} lines of 'If-None-Match: ,'", *request(PORT, "GET", META, [("If-None-Match", ",")] * count, timeout=120), expect=None)
    except Exception as exc:  # noqa: BLE001
        print(f"  {count} lines -> transport error {type(exc).__name__}: {exc}")
        OUT[f"{count} lines"] = {"error": f"{type(exc).__name__}: {exc}"}

with open("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1/live_functional.json", "w") as fh:
    json.dump(OUT, fh, indent=1)
print("\nwrote live_functional.json")
