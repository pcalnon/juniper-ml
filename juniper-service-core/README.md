# juniper-service-core

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Application**: juniper-service-core (subdirectory of juniper-ml)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.1.0

Shared **service-tier scaffolding** for Juniper ML model services: a model-agnostic
FastAPI application factory, a `pydantic-settings` base, and a generic
liveness/readiness health router. This is WS-2 of the model/middleware refactor
(`notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` in the
juniper-ml repo).

The `-core` suffix marks it as genuinely shared: it carries **no** model,
classification, or training logic — those stay in the owning service (e.g.
`juniper-cascor`) and are passed in.

## Install

```bash
pip install juniper-service-core
```

## What's in this scaffold

| Surface | Module | Purpose |
|---------|--------|---------|
| `create_app(...)` | `juniper_service_core.app` | FastAPI app factory: mounts the health router, then any service-supplied routers. Model-agnostic. |
| `SettingsBase` | `juniper_service_core.settings` | `pydantic-settings` base with generic fields (`service_name`, `host`, `port`, `log_level`). Subclasses set their own `env_prefix`. |
| `health_router()` | `juniper_service_core.health` | Generic `APIRouter` exposing `GET /v1/health` (liveness) and `GET /v1/health/ready` (readiness). |

### Dependency-free top-level import

`import juniper_service_core` pulls **no** third-party runtime dependency. Only
`__version__` is exposed eagerly; `create_app` and `SettingsBase` are imported lazily
on attribute access (PEP 562 `__getattr__`) from submodules that require `fastapi` /
`pydantic-settings`. This lets the TestPyPI publish-verify run a clean `--no-deps`
import check.

## Usage

```python
from juniper_service_core import create_app, SettingsBase
from pydantic_settings import SettingsConfigDict


class MyServiceSettings(SettingsBase):
    model_config = SettingsConfigDict(env_prefix="JUNIPER_MYSVC_")


app = create_app(title="My Service", version="1.0.0", routers=[...])
# GET /v1/health      -> {"status": "ok"}
# GET /v1/health/ready -> {"status": "ready"}
```

## What's deferred

This first PR is an additive package skeleton. The following are intentionally **not**
in this scaffold and arrive in later WS-2 follow-ups:

- Extraction of the **security / middleware / websocket / worker / generic-route**
  helpers from `juniper-cascor`.
- The `TrainingLifecycleBase` body, which depends on `juniper-model-core`
  (this scaffold does not yet depend on `juniper-model-core`).

## Development

```bash
pip install -e ".[test]"
pytest tests/ -v
```
