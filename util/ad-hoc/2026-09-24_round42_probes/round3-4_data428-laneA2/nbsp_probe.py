"""Is a field of '*' wrapped in NON-OWS whitespace (NBSP 0xA0, NEL 0x85) treated as '*' or as malformed?

RFC 9110 OWS is SP / HTAB only, and the list grammar here uses [ \\t]. The '*' test uses str.strip().
Sent as raw header BYTES (obs-text), which h11 accepts and Starlette decodes as latin-1.
"""

import sys
import tempfile
from pathlib import Path

L = Path(__file__).resolve().parent
sys.path.insert(0, str(L / "trees" / "3a76a4c"))

import h11._abnf as abnf  # noqa: E402
import re  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

field_value = re.compile(abnf.field_value.encode("ascii"))
for raw in (b"\xa0*", b"\x85*", b"\xa0*\xa0"):
    print(f"h11 field-value accepts {raw!r}: {field_value.fullmatch(raw) is not None}")

storage = Path(tempfile.mkdtemp(dir=str(L / "tmp"))) / "s"
storage.mkdir()
store = LocalFSDatasetStore(storage)
app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))
datasets.set_store(store)
c = TestClient(app)
dsid = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 4}, "persist": True}).json()["dataset_id"]

for raw in (b"\xa0*", b"\x85*"):
    r_inm = c.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": raw})
    r_im = c.get(f"/v1/datasets/{dsid}", headers={"If-Match": raw})
    r_art = c.get(f"/v1/datasets/{dsid}/artifact", headers={"If-None-Match": raw})
    r_patch = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["nbsp"]}, headers={"If-Match": raw})
    print(f"{raw!r}: GET If-None-Match -> {r_inm.status_code} (docs: malformed on a read names nothing -> 200); "
          f"GET If-Match -> {r_im.status_code} (docs: malformed If-Match fails -> 412); "
          f"artifact If-None-Match -> {r_art.status_code}; PATCH If-Match -> {r_patch.status_code} (docs: 412, nothing written)")
for raw in (b'\xa0"abc"',):
    print(f"control {raw!r} (a tag, not '*'): GET If-Match -> {c.get(f'/v1/datasets/{dsid}', headers={'If-Match': raw}).status_code}")
