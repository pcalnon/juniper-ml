"""Lane B (r42d): every route against five storage faults, through the real app over LocalFS.

Faults (each on a freshly created, NAMED dataset):
  meta-symlink-out   the .meta.json is an absolute symlink to a copy outside the storage root
  npz-symlink-out    the .npz is an absolute symlink to a copy outside the storage root
  meta-corrupt-json  the .meta.json holds invalid JSON
  meta-bad-schema    the .meta.json is valid JSON missing a required field
  meta-dangling      the .meta.json is a symlink to a path outside the root that does not exist
For each route: status, detail, whether the body names the id, and every log record at WARNING or
above whose rendered form (traceback included) names the id.

Run inside a tree: run_in_tree.bash <tree> fault_survey.py <out.json>
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

import juniper_data

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

import juniper_data.api.settings as settings_module  # noqa: E402

settings_module.get_secret = lambda _name: None

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

SPIRAL = {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 7}, "persist": True, "name": "survey"}


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def lead_out(stored: Path, outside: Path) -> None:
    outside.mkdir(exist_ok=True)
    elsewhere = outside / stored.name
    elsewhere.write_bytes(stored.read_bytes())
    stored.unlink()
    stored.symlink_to(elsewhere)


def apply(fault: str, store: LocalFSDatasetStore, dataset_id: str, outside: Path) -> None:
    meta = store.base_path / f"{dataset_id}.meta.json"
    npz = store.base_path / f"{dataset_id}.npz"
    if fault == "meta-symlink-out":
        lead_out(meta, outside)
    elif fault == "npz-symlink-out":
        lead_out(npz, outside)
    elif fault == "meta-corrupt-json":
        meta.write_text("{not json")
    elif fault == "meta-bad-schema":
        doc = json.loads(meta.read_text())
        doc.pop("generator")
        meta.write_text(json.dumps(doc))
    elif fault == "meta-dangling":
        meta.unlink()
        meta.symlink_to(outside / "nowhere.meta.json")
    else:
        raise ValueError(fault)


def routes(dataset_id: str) -> list[tuple[str, str, str, dict]]:
    return [
        ("GET /{id}", "GET", f"/v1/datasets/{dataset_id}", {}),
        ("GET /{id}/access", "GET", f"/v1/datasets/{dataset_id}/access", {}),
        ("GET /{id}/artifact", "GET", f"/v1/datasets/{dataset_id}/artifact", {}),
        ("GET /{id}/artifact INM *", "GET", f"/v1/datasets/{dataset_id}/artifact", {"headers": {"If-None-Match": "*"}}),
        ("GET /{id}/preview", "GET", f"/v1/datasets/{dataset_id}/preview", {}),
        ("PATCH /{id}/tags", "PATCH", f"/v1/datasets/{dataset_id}/tags", {"json": {"add_tags": ["x"]}}),
        ("PATCH /{id}/tags IM *", "PATCH", f"/v1/datasets/{dataset_id}/tags", {"json": {"add_tags": ["x"]}, "headers": {"If-Match": "*"}}),
        ("PATCH batch-tags", "PATCH", "/v1/datasets/batch-tags", {"json": {"dataset_ids": [dataset_id], "add_tags": ["x"]}}),
        ("POST batch-export", "POST", "/v1/datasets/batch-export", {"json": {"dataset_ids": [dataset_id]}}),
        ("POST create (same params)", "POST", "/v1/datasets", {"json": SPIRAL}),
        ("POST batch-create (same params)", "POST", "/v1/datasets/batch-create", {"json": {"datasets": [SPIRAL]}}),
        ("GET /filter", "GET", "/v1/datasets/filter", {}),
        ("GET /stats", "GET", "/v1/datasets/stats", {}),
        ("GET /versions", "GET", "/v1/datasets/versions", {"params": {"name": "survey"}}),
        ("GET /latest", "GET", "/v1/datasets/latest", {"params": {"name": "survey"}}),
        ("GET list", "GET", "/v1/datasets", {}),
        ("POST cleanup-expired", "POST", "/v1/datasets/cleanup-expired", {}),
        ("POST batch-delete", "POST", "/v1/datasets/batch-delete", {"json": {"dataset_ids": [dataset_id]}}),
        ("DELETE /{id}", "DELETE", f"/v1/datasets/{dataset_id}", {}),
    ]


def survey(fault: str) -> list[dict]:
    work = Path(tempfile.mkdtemp(prefix=f"survey-{fault}-", dir=os.environ.get("SURVEY_TMP")))
    try:
        storage = work / "storage"
        storage.mkdir()
        store = LocalFSDatasetStore(storage)
        app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False, api_keys=None, _env_file=None))
        datasets.set_store(store)
        client = TestClient(app, raise_server_exceptions=False)
        created = client.post("/v1/datasets", json=SPIRAL)
        assert created.status_code == 201, created.text
        dataset_id = created.json()["dataset_id"]
        apply(fault, store, dataset_id, work / "outside")
        capture = Capture()
        root = logging.getLogger()
        root.addHandler(capture)
        root.setLevel(logging.DEBUG)
        rows = []
        try:
            for label, method, url, kwargs in routes(dataset_id):
                capture.records.clear()
                response = client.request(method, url, **kwargs)
                client.get("/v1/health")  # lets any call_soon callback run and log
                loud = [r for r in capture.records if r.levelno >= logging.WARNING]
                fmt = logging.Formatter("%(name)s %(levelname)s %(message)s")
                loud_with_id = [fmt.format(r).splitlines()[-1][:160] for r in loud if dataset_id in fmt.format(r)]
                body = response.text
                try:
                    detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") and isinstance(response.json(), dict) else None
                except Exception:
                    detail = None
                rows.append(
                    {
                        "fault": fault,
                        "route": label,
                        "status": response.status_code,
                        "detail": (str(detail)[:120] if detail is not None else None),
                        "body_names_id": dataset_id in body,
                        "json_body_head": body[:160] if response.headers.get("content-type", "").startswith("application/json") else f"<{response.headers.get('content-type')}, {len(response.content)} bytes>",
                        "loud_records": [(r.name, r.levelname) for r in loud],
                        "loud_records_naming_id": loud_with_id,
                    }
                )
        finally:
            root.removeHandler(capture)
        return rows
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> None:
    out = Path(sys.argv[1])
    rows: list[dict] = []
    for fault in ("meta-symlink-out", "npz-symlink-out", "meta-corrupt-json", "meta-bad-schema", "meta-dangling"):
        rows.extend(survey(fault))
    out.write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(f"{r['fault']:18} {r['route']:34} {r['status']}  names_id_body={r['body_names_id']!s:5} loud={len(r['loud_records'])} loud_naming_id={len(r['loud_records_naming_id'])}  detail={r['detail']!r}")


if __name__ == "__main__":
    main()
