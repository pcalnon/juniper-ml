#!/usr/bin/env python3
"""Where does the lone-surrogate POST to the primer's idempotent_jobs.py fail? (in-process, no port)"""
import asyncio
import importlib.util
import sys
import tempfile
import traceback
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
        if "--show-errors" in sys.argv:
            from fastapi.exceptions import RequestValidationError
            from fastapi.responses import PlainTextResponse

            @app.exception_handler(RequestValidationError)
            async def show(request, exc):
                print("ERRORS", ascii(exc.errors())[:600])
                return PlainTextResponse("shown", status_code=422)
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            bad = b'{"kind": "train", "dataset_id": "\\ud800", "epochs": 1}'
            try:
                r = await c.post("/v1/jobs", content=bad, headers={"content-type": "application/json", "Idempotency-Key": "k-bad"})
                print("status", r.status_code, r.text[:200])
            except Exception as exc:  # noqa: BLE001
                tb = traceback.extract_tb(exc.__traceback__)
                print("EXC", type(exc).__name__, str(exc)[:160])
                for fr in tb[-6:]:
                    print(f"   {Path(fr.filename).name}:{fr.lineno} {fr.name}: {(fr.line or '')[:110]}")


asyncio.run(main(Path([a for a in sys.argv[1:] if not a.startswith("--")][0])))
