#!/usr/bin/env python3
"""In-process probe (no port) of the primer's idempotent_jobs.py: a lone surrogate in dataset_id.

Run with the primer venv. Extracts the example by the harness convention (via probe.py's extract()).
"""
import asyncio
import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("toyprobe", HERE / "probe.py")
toyprobe = importlib.util.module_from_spec(spec)
sys.modules["toyprobe"] = toyprobe
spec.loader.exec_module(toyprobe)

import httpx  # noqa: E402


async def main(primer: Path):
    source = toyprobe.extract(primer.read_text(encoding="utf-8"), "idempotent_jobs.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "idempotent_jobs.py"
        path.write_text(source, encoding="utf-8")
        s = importlib.util.spec_from_file_location("idempotent_jobs", path)
        mod = importlib.util.module_from_spec(s)
        sys.modules[s.name] = mod
        s.loader.exec_module(mod)
        app = mod.create_app()
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            ctl = b'{"kind": "train", "dataset_id": "ds-1", "epochs": 1}'
            bad = b'{"kind": "train", "dataset_id": "\\ud800", "epochs": 1}'
            for label, key, raw in (("control", "k-ctl", ctl), ("surrogate first", "k-bad", bad), ("surrogate replay", "k-bad", bad)):
                r = await c.post("/v1/jobs", content=raw, headers={"content-type": "application/json", "Idempotency-Key": key})
                print(f"{label:18} {r.status_code} {r.headers.get('content-type')} {r.text[:70]!r}")
                recs = {k: getattr(v, "state", "?") for k, v in app.state.keys._records.items()}
                print(f"{'':18} jobs={len(app.state.jobs)} key-records={recs}")
            jobs = getattr(app.state, "jobs", {})
            for jid, job in jobs.items():
                r = await c.get(f"/v1/jobs/{jid}")
                print(f"GET /v1/jobs/{jid[:12]}… {r.status_code} {r.headers.get('content-type')}")


asyncio.run(main(Path(sys.argv[1])))
