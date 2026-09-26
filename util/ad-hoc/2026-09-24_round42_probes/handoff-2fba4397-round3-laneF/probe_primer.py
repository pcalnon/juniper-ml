"""Lane D round-3 probe, primer venv (fastapi 0.141.1 / starlette 1.6.0), in-process, no port.

(1) FastAPI default app: a lone surrogate in a typed body field.
(2) The primer's idempotent_jobs.py (extracted from origin/main's primer): control, surrogate, surrogate replay.
Usage: <primer-venv>/bin/python -B probe_primer.py <primer.md>
"""
import asyncio
import importlib.util
import sys
from pathlib import Path

import fastapi
import httpx
import pydantic
import starlette
from fastapi import FastAPI
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
PRIMER = Path(sys.argv[1])


def extract(text: str, name: str) -> str:
    lines = text.split("\n")
    marker = f"<!-- example-file: {name} -->"
    for i, line in enumerate(lines):
        if line.strip() == marker and i + 1 < len(lines) and lines[i + 1].strip() == "```python":
            out = []
            for body_line in lines[i + 2:]:
                if body_line.strip() == "```":
                    return "\n".join(out) + "\n"
                out.append(body_line)
    raise SystemExit(f"example {name} not found")


class Body(BaseModel):
    n: int


def default_app() -> FastAPI:
    app = FastAPI()

    @app.post("/x")
    async def x(b: Body) -> dict:
        return {"ok": True}

    return app


async def main() -> None:
    print("versions: fastapi", fastapi.__version__, "starlette", starlette.__version__, "pydantic", pydantic.VERSION, "python", sys.version.split()[0])
    SUR = b'"\\ud800"'  # a JSON escape that decodes to a lone surrogate
    t = httpx.ASGITransport(app=default_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=t, base_url="http://t") as c:
        for label, raw in (("default ctl n='abc'", b'{"n": "abc"}'), ("default sur n=D800", b'{"n": ' + SUR + b"}")):
            r = await c.post("/x", content=raw, headers={"content-type": "application/json"})
            print(f"{label:24} {r.status_code} {r.headers.get('content-type')} {r.text[:60]!r}")

    src = extract(PRIMER.read_text(encoding="utf-8"), "idempotent_jobs.py")
    mod_path = HERE / "idempotent_jobs.py"
    mod_path.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("idempotent_jobs", mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    app = mod.create_app()
    t = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=t, base_url="http://t") as c:
        ctl = b'{"kind": "train", "dataset_id": "ds-1", "epochs": 1}'
        bad = b'{"kind": "train", "dataset_id": ' + SUR + b', "epochs": 1}'
        for label, key, raw in (("idem control", "k-ctl", ctl), ("idem surrogate 1st", "k-bad", bad), ("idem surrogate retry", "k-bad", bad)):
            r = await c.post("/v1/jobs", content=raw, headers={"content-type": "application/json", "Idempotency-Key": key})
            print(f"{label:24} {r.status_code} {r.headers.get('content-type')} {r.text[:60]!r} | jobs={len(app.state.jobs)} key-records={sorted(app.state.keys._records)}")
    # Where does validation fail? Validate the model directly.
    req_models = [v for v in vars(mod).values() if isinstance(v, type) and issubclass(v, BaseModel) and "dataset_id" in getattr(v, "model_fields", {})]
    for m in req_models:
        try:
            m.model_validate_json(b'{"kind": "train", "dataset_id": ' + SUR + b', "epochs": 1}')
            print(m.__name__, "validate_json: OK")
        except pydantic.ValidationError as e:
            print(m.__name__, "validate_json errors:", [(x["type"], x["loc"]) for x in e.errors()])
        try:
            m.model_validate({"kind": "train", "dataset_id": "\ud800", "epochs": 1})
            print(m.__name__, "validate(python dict): OK")
        except pydantic.ValidationError as e:
            print(m.__name__, "validate(python dict) errors:", [(x["type"], x["loc"]) for x in e.errors()])
    mod_path.unlink()


asyncio.run(main())
