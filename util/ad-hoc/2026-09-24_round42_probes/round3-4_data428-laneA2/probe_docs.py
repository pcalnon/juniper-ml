"""Behavioural probe of every doc statement about juniper-data#428's changed behaviour, at a given tree.

Runs the real app (create_app) over the store the service wires (LocalFS), plus InMemory where a
doc sentence is about it. Prints one line per check: OK / MISMATCH, the doc claim, what was observed.
usage: probe_docs.py <tree>
"""

import hashlib
import io
import json
import logging
import sys
import tempfile
import zipfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(TREE))

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api import http_cache  # noqa: E402
from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.http_cache import MAX_PRECONDITION_FIELD_LENGTH, body_etag  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

assert http_cache.__file__.startswith(str(TREE)), http_cache.__file__
RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, claim: str, observed: str) -> None:
    RESULTS.append((bool(ok), claim, observed))
    print(f"{'OK      ' if ok else 'MISMATCH'} | {claim} | {observed}")


tmp = Path(tempfile.mkdtemp(prefix="probe-", dir=str(Path(__file__).resolve().parent / "tmp")))


def fresh_localfs() -> tuple[TestClient, LocalFSDatasetStore]:
    storage = Path(tempfile.mkdtemp(dir=tmp)) / "store"
    storage.mkdir()
    store = LocalFSDatasetStore(storage)
    app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))
    datasets.set_store(store)
    return TestClient(app), store


def create(client: TestClient, seed: int = 1, name: str | None = None) -> str:
    body = {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True}
    if name:
        body["name"] = name
    r = client.post("/v1/datasets", json=body)
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


def access(client: TestClient, dsid: str) -> int:
    return client.get(f"/v1/datasets/{dsid}/access").json()["access_count"]


client, store = fresh_localfs()
dsid = create(client)
r = client.get(f"/v1/datasets/{dsid}")
etag = r.headers["etag"]

# ---------------- GET /{id} ----------------
check(r.status_code == 200 and etag == body_etag(r.content) and not etag.startswith("W/"), "GET /{id}: strong ETag = SHA-256 of exact body", f"{r.status_code} etag_ok={etag == body_etag(r.content)}")
check(r.headers.get("cache-control") == "private, no-cache", "GET /{id}: Cache-Control private, no-cache", r.headers.get("cache-control"))
r2 = client.get(f"/v1/datasets/{dsid}")
check(r2.headers["etag"] == etag, "API 900-901: a read does not move the ETag", f"{r2.headers['etag'] == etag}")

over_cap_with_current = etag + ", " + ", ".join(['"pad"'] * (MAX_PRECONDITION_FIELD_LENGTH // 7 + 1))
under_cap_with_current = etag + ', "pad"'
assert len(over_cap_with_current) > MAX_PRECONDITION_FIELD_LENGTH
for label, hdr, want in (
    ("garbage", "garbage", 200),
    ("tag in garbage", f"foo{etag}bar", 200),
    ("unterminated", '"unterminated', 200),
    ("over-cap list naming the CURRENT tag", over_cap_with_current, 200),
    ("control: same list under the cap", under_cap_with_current, 304),
    ("'*' padded over the cap", "*" + " " * MAX_PRECONDITION_FIELD_LENGTH, 200),
):
    rr = client.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": hdr})
    full = rr.status_code == 200 and rr.json().get("dataset_id") == dsid
    check(rr.status_code == want and (want != 200 or full), f"API 909-910/REF 1291: read, malformed If-None-Match names nothing ({label})", f"{rr.status_code} full_body={full}")

for label, hdr, want in (
    ("garbage", "garbage", 412),
    ("over-cap list naming the CURRENT tag", over_cap_with_current, 412),
    ("control: under-cap list naming current", under_cap_with_current, 200),
    ("W/ of the current strong tag", "W/" + etag, 412),
    ("*", "*", 200),
    ("'*' padded over the cap", "*" + " " * MAX_PRECONDITION_FIELD_LENGTH, 412),
):
    rr = client.get(f"/v1/datasets/{dsid}", headers={"If-Match": hdr})
    check(rr.status_code == want, f"API 911-913/REF 1292: If-Match strong; malformed/over-long fails ({label})", str(rr.status_code))

before = access(client, dsid)
rr = client.get(f"/v1/datasets/{dsid}", headers={"If-Match": '"stale"', "If-None-Match": etag})
check(rr.status_code == 412, "REF 1281: If-Match evaluated first; a failure wins over a matching If-None-Match", str(rr.status_code))
check(access(client, dsid) == before, "REF 1263/API 913-914: a 412 is not an access", f"{before}->{access(client, dsid)}")
before = access(client, dsid)
rr = client.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": etag})
check(rr.status_code == 304 and rr.content == b"" and rr.headers.get("etag") == etag and rr.headers.get("cache-control") == "private, no-cache", "GET /{id}: 304, no body, ETag + Cache-Control", f"{rr.status_code} body={len(rr.content)}")
check(access(client, dsid) == before + 1, "REF 1263/API 908-909: a 304 is recorded as an access", f"{before}->{access(client, dsid)}")
rr = client.get(f"/v1/datasets/{dsid}", headers=[("If-None-Match", '"zzz"'), ("If-None-Match", etag)])
check(rr.status_code == 304, "API 908: a list may span several header lines", str(rr.status_code))
lines_over = ['"zzz"', " " * (MAX_PRECONDITION_FIELD_LENGTH - 4)]
rr = client.get(f"/v1/datasets/{dsid}", headers=[("If-None-Match", lines_over[0] + ", " + etag), ("If-None-Match", lines_over[1])])
check(rr.status_code == 200, "REF 1290/API 910: cap counted over the JOINED lines (two lines, each under, join over)", str(rr.status_code))
rr = client.get(f"/v1/datasets/{dsid}", headers={"If-Match": ""})
check(True, "(info) an EMPTY If-Match on a read", f"{rr.status_code}")
rr = client.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": ""})
check(True, "(info) an EMPTY If-None-Match on a read", f"{rr.status_code}")

# ---------------- /latest ----------------
create(client, seed=1, name="lat")
newest = create(client, seed=2, name="lat")
before = access(client, newest)
lr = client.get("/v1/datasets/latest", params={"name": "lat"})
canon = client.get(f"/v1/datasets/{newest}")
check(lr.headers.get("content-location") == f"/v1/datasets/{newest}" and lr.headers["etag"] == canon.headers["etag"], "REF 1264: /latest Content-Location + the canonical route's ETag", lr.headers.get("content-location"))
before = access(client, newest)
client.get("/v1/datasets/latest", params={"name": "lat"})
l304 = client.get("/v1/datasets/latest", params={"name": "lat"}, headers={"If-None-Match": lr.headers["etag"]})
check(l304.status_code == 304 and access(client, newest) == before, "REF 1264/CHANGELOG: /latest records no access, 200 or 304", f"{l304.status_code} access {before}->{access(client, newest)}")

# ---------------- artifact, confirmed target ----------------
meta = store.get_meta(dsid)
ar = client.get(f"/v1/datasets/{dsid}/artifact")
aetag = ar.headers.get("etag")
check(aetag == f'W/"{meta.checksum}"' and ar.headers.get("cache-control") == "private, no-cache", "REF 1265/API 963: artifact ETag WEAK W/\"<checksum>\", Cache-Control", aetag)
check(hashlib.sha256(ar.content).hexdigest() != meta.checksum, "REF 1337/API 963-964: sha256(served bytes) != checksum (LocalFS)", "differs" if hashlib.sha256(ar.content).hexdigest() != meta.checksum else "EQUAL")
opened: list[str] = []
real_open = store.open_artifact_stream


def counting_open(*a, **k):
    opened.append("open")
    return real_open(*a, **k)


store.open_artifact_stream = counting_open  # instance attribute shadows the method
before = access(client, dsid)
rr = client.get(f"/v1/datasets/{dsid}/artifact", headers={"If-Match": '"stale"'})
check(rr.status_code == 412 and opened == [], "REF 1547: a failing If-Match is a 412 decided before the stream opens", f"{rr.status_code} opened={opened}")
check(access(client, dsid) == before, "REF 1265: an artifact 412 is not an access", f"{before}->{access(client, dsid)}")
rr = client.get(f"/v1/datasets/{dsid}/artifact", headers={"If-Match": aetag})
check(rr.status_code == 412, "API 968-969: If-Match cannot name the weak artifact tag", str(rr.status_code))
opened.clear()
rr = client.get(f"/v1/datasets/{dsid}/artifact", headers={"If-Match": "*"})
check(rr.status_code == 200 and len(rr.content) > 0, "API 969: If-Match: * matches the artifact", str(rr.status_code))
opened.clear()
before = access(client, dsid)
rr = client.get(f"/v1/datasets/{dsid}/artifact", headers={"If-None-Match": aetag})
check(rr.status_code == 304 and opened == [] and rr.headers.get("cache-control") == "private, no-cache" and rr.headers.get("etag") == aetag, "REF 1265/1547: confirmed 304 decided before open, carries Cache-Control + ETag", f"{rr.status_code} opened={opened}")
check(access(client, dsid) == before + 1, "REF 1277: an artifact 304 is still an access", f"{before}->{access(client, dsid)}")
rr = client.get(f"/v1/datasets/{dsid}/artifact", headers={"If-None-Match": aetag[2:]})
check(rr.status_code == 304, "REF 1282: If-None-Match compares weakly (strong form of the weak tag hits)", str(rr.status_code))
del store.open_artifact_stream

# ---------------- artifact: deleted artifact, orphan, absent ----------------
gone = create(client, seed=5)
g_etag = client.get(f"/v1/datasets/{gone}/artifact").headers["etag"]
store._npz_path(gone).unlink()
codes = [client.get(f"/v1/datasets/{gone}/artifact", headers=h).status_code for h in ({"If-None-Match": g_etag}, {"If-None-Match": "*"}, {"If-Match": "*"})]
check(codes == [404, 404, 404], "REF 1301/API 975-976: a deleted artifact is a 404, never a 304", str(codes))

orph = create(client, seed=6)
store._meta_path(orph).unlink()
closed: list[bool] = []
real_open2 = store.open_artifact_stream


class Probe:
    def __init__(self, inner):
        self.inner = inner
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.inner)

    def close(self):
        self.closed = True
        getattr(self.inner, "close", lambda: None)()


probes: list[Probe] = []


def probing_open(*a, **k):
    s = real_open2(*a, **k)
    if s is None:
        return None
    probes.append(Probe(s))
    return probes[-1]


store.open_artifact_stream = probing_open
o = {}
for label, h in (("none", {}), ("IM *", {"If-Match": "*"}), ("IM x", {"If-Match": '"x"'}), ("INM *", {"If-None-Match": "*"}), ("INM x", {"If-None-Match": '"x"'}), ("IM garbage", {"If-Match": "garbage"}), ("INM garbage", {"If-None-Match": "garbage"})):
    probes.clear()
    rr = client.get(f"/v1/datasets/{orph}/artifact", headers=h)
    o[label] = (rr.status_code, [p.closed for p in probes], "etag" in rr.headers, rr.headers.get("cache-control"))
check(o["none"][0] == 200, "orphan: unconditional GET serves it", str(o["none"]))
check(o["IM *"][0] == 200, "REF 1305/API 977: orphan, If-Match: * holds", str(o["IM *"]))
check(o["IM x"][0] == 412 and o["IM x"][1] == [True], "REF 1306/API 978: orphan, any listed If-Match is 412, stream closed", str(o["IM x"]))
check(o["INM *"][0] == 304 and o["INM *"][1] == [True] and o["INM *"][3] == "private, no-cache" and not o["INM *"][2], "REF 1305/API 978: orphan, If-None-Match: * is 304 (Cache-Control, no ETag), stream closed", str(o["INM *"]))
check(o["INM x"][0] == 200, "API 978: orphan, a listed If-None-Match names nothing -> served", str(o["INM x"]))
check(o["IM garbage"][0] == 412, "orphan: malformed If-Match fails", str(o["IM garbage"]))
check(o["INM garbage"][0] == 200, "orphan: malformed If-None-Match names nothing on a read", str(o["INM garbage"]))
del store.open_artifact_stream
codes = [client.get("/v1/datasets/never-created-0000/artifact", headers=h).status_code for h in ({}, {"If-Match": "*"}, {"If-Match": '"x"'}, {"If-None-Match": "*"}, {"If-None-Match": '"x"'})]
check(codes == [404] * 5, "REF 1307/API 979: neither metadata nor artifact -> 404 under every precondition", str(codes))

# ---------------- unreadable metadata (LocalFS: a corrupt .meta.json) ----------------
bad = create(client, seed=7)
store._meta_path(bad).write_text("{ this is not json", encoding="utf-8")
records: list[logging.LogRecord] = []


class Grab(logging.Handler):
    def emit(self, record):
        records.append(record)


h = Grab(level=logging.DEBUG)
lg = logging.getLogger("juniper_data")
lg.addHandler(h)
old_level = lg.level
lg.setLevel(logging.DEBUG)
rr = client.get(f"/v1/datasets/{bad}/artifact")
warn = [x for x in records if x.levelno >= logging.WARNING and x.name.startswith("juniper_data")]
check(rr.status_code == 200 and "etag" not in rr.headers and len(rr.content) > 0, "REF 1308/API 979-980/CHANGELOG 25: unreadable metadata -> artifact served without an ETag", f"{rr.status_code} etag={'etag' in rr.headers}")
check(len(warn) == 1 and warn[0].exc_info is None and bad not in warn[0].getMessage(), "REF 1309: the warning names the exception type only", repr([w.getMessage() for w in warn]))
codes = {k: client.get(f"/v1/datasets/{bad}/artifact", headers=v).status_code for k, v in (("IM *", {"If-Match": "*"}), ("IM x", {"If-Match": '"x"'}), ("INM *", {"If-None-Match": "*"}))}
check(True, "(info) unreadable metadata + preconditions on the artifact", str(codes))
mr = client.get(f"/v1/datasets/{bad}")
check(True, "(info) the METADATA route for the same corrupt document", f"{mr.status_code} {mr.text[:60]}")
records.clear()

# ---------------- malformed id ----------------
invalid = "CALLER$CONTROLLED"
exp = client.get(f"/v1/datasets/{invalid}")
routes = {
    "GET /{id}": lambda: client.get(f"/v1/datasets/{invalid}"),
    "GET artifact": lambda: client.get(f"/v1/datasets/{invalid}/artifact"),
    "GET artifact INM *": lambda: client.get(f"/v1/datasets/{invalid}/artifact", headers={"If-None-Match": "*"}),
    "GET access": lambda: client.get(f"/v1/datasets/{invalid}/access"),
    "GET preview": lambda: client.get(f"/v1/datasets/{invalid}/preview"),
    "DELETE": lambda: client.delete(f"/v1/datasets/{invalid}"),
    "PATCH tags": lambda: client.patch(f"/v1/datasets/{invalid}/tags", json={"add_tags": ["x"]}),
    "PATCH tags IM": lambda: client.patch(f"/v1/datasets/{invalid}/tags", json={"add_tags": ["x"]}, headers={"If-Match": '"x"'}),
}
got = {k: (f().status_code) for k, f in routes.items()}
warn = [x for x in records if x.levelno >= logging.WARNING and x.name.startswith("juniper_data")]
check(exp.status_code == 400 and exp.json() == {"detail": "Invalid request parameters"} and set(got.values()) == {400}, "REF 1310-1311/API 980-981: a malformed id is the same 400 on every route", str(got))
check(warn == [], "a malformed id logs no WARNING", repr([w.getMessage() for w in warn]))
dbg = [x for x in records if x.levelno == logging.DEBUG and invalid in x.getMessage()]
check(True, "(info) DEBUG records that carry the caller's id", f"{len(dbg)} e.g. {dbg[0].getMessage()[:70] if dbg else ''}")
lg.removeHandler(h)
lg.setLevel(old_level)

# ---------------- PATCH .../tags ----------------
w = create(client, seed=11)
we = client.get(f"/v1/datasets/{w}").headers["etag"]
pr = client.patch(f"/v1/datasets/{w}/tags", json={"add_tags": ["cas"]}, headers={"If-Match": we})
check(pr.status_code == 200 and pr.headers.get("content-location") == f"/v1/datasets/{w}" and pr.headers["etag"] == client.get(f"/v1/datasets/{w}").headers["etag"] != we, "REF 1266/API 1053-1055: PATCH returns the NEW ETag + Content-Location", f"{pr.status_code} {pr.headers.get('content-location')}")
pr = client.patch(f"/v1/datasets/{w}/tags", json={"add_tags": ["lost"]}, headers={"If-Match": we})
check(pr.status_code == 412 and "lost" not in store.get_meta(w).tags, "API 1057-1059: stale If-Match -> 412, nothing written", str(pr.status_code))
cur = client.get(f"/v1/datasets/{w}").headers["etag"]
over_cap_w = cur + ", " + ", ".join(['"pad"'] * (MAX_PRECONDITION_FIELD_LENGTH // 7 + 1))
for label, hdrs, want in (
    ("INM *", {"If-None-Match": "*"}, 412),
    ("INM current bare", {"If-None-Match": cur}, 412),
    ("INM current in list", {"If-None-Match": f'"elsewhere", {cur}'}, 412),
    ("INM W/current", {"If-None-Match": "W/" + cur}, 412),
    ("INM garbage", {"If-None-Match": "garbage"}, 412),
    ("INM tag in garbage", {"If-None-Match": f"foo{cur}bar"}, 412),
    ("INM unterminated", {"If-None-Match": '"unterminated'}, 412),
    ("INM over cap", {"If-None-Match": '"a", ' * 2000}, 412),
    ("IM garbage", {"If-Match": "garbage"}, 412),
    ("IM over-cap list naming current", {"If-Match": over_cap_w}, 412),
    ("control: IM under-cap naming current", {"If-Match": cur + ', "pad"'}, 200),
    ("control: INM another tag", {"If-None-Match": '"other"'}, 200),
    ("control: INM empty", {"If-None-Match": ""}, 200),
):
    tag = "t" + str(abs(hash(label)) % 10**8)
    pr = client.patch(f"/v1/datasets/{w}/tags", json={"add_tags": [tag]}, headers=hdrs)
    written = tag in store.get_meta(w).tags
    check(pr.status_code == want and written == (want == 200), f"API 1063-1066/REF 1266: PATCH {label}", f"{pr.status_code} written={written}")
    if want == 200:
        cur = client.get(f"/v1/datasets/{w}").headers["etag"]
        over_cap_w = cur + ", " + ", ".join(['"pad"'] * (MAX_PRECONDITION_FIELD_LENGTH // 7 + 1))
pr = client.patch("/v1/datasets/never-created-1111/tags", json={"add_tags": ["x"]}, headers={"If-None-Match": "*"})
check(True, "(info) PATCH If-None-Match: * on an ABSENT dataset", str(pr.status_code))

# ---------------- the other writes ignore preconditions ----------------
d = create(client, seed=12)
dr = client.delete(f"/v1/datasets/{d}", headers={"If-Match": '"certainly-stale"'})
check(dr.status_code == 204 and not store.exists(d), "REF 1321-1323/API 1025-1027: DELETE does not evaluate If-Match", f"{dr.status_code} exists_after={store.exists(d)}")
b = create(client, seed=13)
br = client.patch("/v1/datasets/batch-tags", json={"dataset_ids": [b], "add_tags": ["bt"]}, headers={"If-Match": '"stale"', "If-None-Match": "*"})
check(br.status_code == 200 and "bt" in store.get_meta(b).tags, "REF 1323/API 793-794: batch-tags ignores If-Match and If-None-Match", f"{br.status_code} tags={store.get_meta(b).tags}")
bd = create(client, seed=14)
bdr = client.post("/v1/datasets/batch-delete", json={"dataset_ids": [bd]}, headers={"If-Match": '"stale"'})
check(bdr.status_code == 200 and not store.exists(bd), "REF 1323-1324/API 1068-1070: other writes (batch-delete) ignore If-Match", f"{bdr.status_code} exists_after={store.exists(bd)}")

# ---------------- HEAD ----------------
hs = [client.head(u).status_code for u in (f"/v1/datasets/{dsid}", "/v1/datasets/latest?name=lat", f"/v1/datasets/{dsid}/artifact")]
check(hs == [405, 405, 405], "REF 1367: HEAD answers 405 on all three reads", str(hs))

# ---------------- /access ----------------
ac = client.get(f"/v1/datasets/{dsid}/access")
a1 = ac.json()["access_count"]
check(ac.headers.get("cache-control") == "no-store" and client.get(f"/v1/datasets/{dsid}/access").json()["access_count"] == a1, "CHANGELOG: /access is no-store, and reading it is not an access", f"{ac.headers.get('cache-control')}")

# ---------------- InMemory: exists() checks metadata only ----------------
mem = InMemoryDatasetStore()
app = create_app(settings=Settings(storage_path=str(tmp), rate_limit_enabled=False))
datasets.set_store(mem)
mc = TestClient(app)
mid = create(mc, seed=21)
m_etag = mc.get(f"/v1/datasets/{mid}/artifact").headers["etag"]
art_attr = [k for k, v in vars(mem).items() if isinstance(v, dict) and mid in v and not hasattr(v[mid], "checksum")]
for k in art_attr:
    del vars(mem)[k][mid]
rr = mc.get(f"/v1/datasets/{mid}/artifact", headers={"If-None-Match": m_etag})
check(rr.status_code == 304, "REF 1302-1303: in-memory exists() is metadata-only, so metadata-without-artifact can still 304", f"{rr.status_code} (removed artifact from {art_attr})")

# ---------------- served bytes vs checksum, InMemory vs LocalFS key order ----------------
mid2 = create(mc, seed=22)
mem_bytes = mc.get(f"/v1/datasets/{mid2}/artifact").content
mem_meta = mem.get_meta(mid2)
datasets.set_store(store)
lid2 = create(client, seed=22)
lfs_bytes = client.get(f"/v1/datasets/{lid2}/artifact").content
lfs_meta = store.get_meta(lid2)
order_mem = zipfile.ZipFile(io.BytesIO(mem_bytes)).namelist()
order_lfs = zipfile.ZipFile(io.BytesIO(lfs_bytes)).namelist()
check(mid2 == lid2 and mem_meta.checksum == lfs_meta.checksum, "same request -> same dataset_id and checksum on both stores", f"ids_equal={mid2 == lid2} checksum_equal={mem_meta.checksum == lfs_meta.checksum}")
check(hashlib.sha256(mem_bytes).hexdigest() != mem_meta.checksum, "REF 1337: sha256(served) != checksum (InMemory)", "differs" if hashlib.sha256(mem_bytes).hexdigest() != mem_meta.checksum else "EQUAL")
check(order_mem == sorted(order_mem) and order_lfs != order_mem, "REF 1338: InMemory sorts keys, LocalFS keeps the generator's -> different bytes, one checksum", f"mem={order_mem} lfs={order_lfs} bytes_equal={mem_bytes == lfs_bytes}")

# ---------------- OpenAPI text ----------------
spec = create_app(settings=Settings(storage_path=str(tmp), rate_limit_enabled=False)).openapi()
art = spec["paths"]["/v1/datasets/{dataset_id}/artifact"]["get"]
tags_op = spec["paths"]["/v1/datasets/{dataset_id}/tags"]["patch"]
desc_a, desc_t = art.get("description", ""), tags_op.get("description", "")
check("WEAK" in desc_a and "only ``*`` satisfies it" in desc_a and "412 if ``If-Match`` does not hold" in desc_a, "OpenAPI: download_artifact says weak, only * satisfies If-Match, Raises adds 412", "weak=%s star=%s raises412=%s" % ("WEAK" in desc_a, "only ``*`` satisfies it" in desc_a, "412 if ``If-Match`` does not hold" in desc_a))
check("fails closed" in desc_t and "No other write route evaluates preconditions" in desc_t, "OpenAPI: PATCH description adds fail-closed + 'no other write route evaluates preconditions'", "fails_closed=%s no_other=%s" % ("fails closed" in desc_t, "No other write route evaluates preconditions" in desc_t))
check("or either field is malformed" in tags_op["responses"]["412"]["description"], "OpenAPI: PATCH 412 (_R_412_WRITE) adds 'or either field is malformed'", tags_op["responses"]["412"]["description"])
check("400" not in art["responses"], "(info) the artifact route's declared responses", str(sorted(art["responses"])))
print("\nOpenAPI download_artifact description, verbatim:\n" + desc_a)
print("\nOpenAPI PATCH tags description, verbatim:\n" + desc_t)

print(f"\nSUMMARY: {sum(ok for ok, _, _ in RESULTS)} OK, {sum(not ok for ok, _, _ in RESULTS)} MISMATCH of {len(RESULTS)}")
