# juniper-observability v0.1.1a — first publishable alpha — Release Notes (archived)

> Archived verbatim from the GitHub Release [`juniper-observability-v0.1.1a`](https://github.com/pcalnon/juniper-ml/releases/tag/juniper-observability-v0.1.1a) (pcalnon/juniper-ml), backfilled 2026-06-18
> per the release-notes archival convention (see [`notes/PYPI-PUBLISH-PROCEDURE.md` §11](../PYPI-PUBLISH-PROCEDURE.md)).

---

## Summary

First publishable alpha of **`juniper-observability`** — the shared
observability primitives library for the Juniper ML platform.

> PEP 440 normalizes the source version `0.1.1a` to `0.1.1a0` on
> upload, so on PyPI / TestPyPI this distribution is registered as
> `0.1.1a0`. The pyproject source version stays `0.1.1a`.

## What's in here

- **Health models** — Pydantic `DependencyStatus` and
  `ReadinessResponse` for the standard `/v1/health/ready` shape used
  by every Juniper server.
- **`probe_dependency`** — synchronous HTTP health-check helper.
- **Structured logging** — `JuniperJsonFormatter` +
  `configure_logging` with `request_id` propagation.
- **Middleware** — `RequestIdMiddleware` and `PrometheusMiddleware`
  (bounded label cardinality per the R1.1 contract).
- **Cross-service constants** — `UNMATCHED_ENDPOINT_LABEL`,
  `READINESS_HEADER`, `LIVENESS_TICK_BUDGET_MS`,
  `LIVENESS_STALENESS_SECONDS`.
- **Prometheus utilities** — `get_prometheus_app`, `set_build_info`.
- **Sentry init** — `configure_sentry` with the SEC-10 `before_send`
  hook always installed.
- **Optional extras** — `[prometheus]`, `[sentry]`, `[all]`.

## Why this version number

Earlier publish attempts at `0.1.0a0` and `0.1.0a2` failed at the
OIDC trusted-publisher handshake (the publisher had been registered
under the wrong project). `0.1.1a` is a fresh, never-uploaded alpha
that lets the corrected pending publisher claim the project on its
first successful upload.

## Verifying installation

```bash
pip install --pre juniper-observability==0.1.1a
python -c "import juniper_observability; print(juniper_observability.__version__)"
```

## Design + migration

See `notes/code-review/METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`
in the parent juniper-ml repo for the full design and the 5-PR
migration sequence.
