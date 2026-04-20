# `_normalize_metric` Consumer Audit

**Phase**: H (P16)
**Date**: 2026-04-13
**Author**: Paul Calnon
**Contract**: C-22 (dual-format: flat + nested keys both present)
**Gate**: D-27 (CODEOWNERS hard merge gate on shape changes)

---

## Function

`CascorServiceAdapter._normalize_metric(entry: dict) -> dict`

**Location**: `juniper-canopy/src/backend/cascor_service_adapter.py:568`

Normalizes a single metric entry from either CasCor field names (`loss`, `accuracy`, `validation_loss`, `validation_accuracy`) or Canopy field names (`train_loss`, `train_accuracy`, `val_loss`, `val_accuracy`) into a dual-format dict containing **both** flat keys and nested dicts.

---

## Output Shape (Canonical)

```python
{
    # Flat keys (API/client consumers)
    "epoch": int,
    "train_loss": float | None,
    "train_accuracy": float | None,
    "val_loss": float | None,
    "val_accuracy": float | None,
    "hidden_units": int,
    "phase": str | None,
    "timestamp": str | None,

    # Nested keys (dashboard metrics_panel.py consumers)
    "metrics": {
        "loss": float | None,
        "accuracy": float | None,
        "val_loss": float | None,
        "val_accuracy": float | None,
    },
    "network_topology": {
        "hidden_units": int,
    },
}
```

---

## Production Consumers

### 1. `_ServiceTrainingMonitor.get_current_metrics()` — line 103

```python
flat = CascorServiceAdapter._normalize_metric(data)
return CascorServiceAdapter._to_dashboard_metric(flat)
```

**Consumer**: REST `/api/metrics/current` endpoint → dashboard initial load.

### 2. `_ServiceTrainingMonitor.get_recent_metrics()` — lines 116, 119

```python
return [CascorServiceAdapter._to_dashboard_metric(
    CascorServiceAdapter._normalize_metric(m)) for m in data]
```

**Consumer**: REST `/api/metrics/history` endpoint → chart backfill, reconnect reconciliation.

### 3. `start_metrics_relay()` relay loop — line 250

```python
data = CascorServiceAdapter._to_dashboard_metric(
    CascorServiceAdapter._normalize_metric(data))
```

**Consumer**: WebSocket `/ws/training` broadcast → real-time metrics panel, latency beacon.

### 4. `CascorStateSync.sync()` — `state_sync.py:150`

```python
state.metrics_history = [CascorServiceAdapter._to_dashboard_metric(
    CascorServiceAdapter._normalize_metric(m)) for m in raw_history]
```

**Consumer**: Periodic state reconciliation → training state cache.

---

## Downstream Consumers of Nested Format

All production call sites pipe output through `_to_dashboard_metric()`, which extracts:

- `m.get("metrics", {}).get("loss", 0)` — `metrics_panel.py` (chart Y-axis)
- `m.get("metrics", {}).get("accuracy", 0)` — `metrics_panel.py` (chart Y-axis)
- `m.get("network_topology", {}).get("hidden_units", 0)` — `metrics_panel.py` (topology badge)

---

## Regression Protection

| Guard             | Location                                               | What it catches                     |
|-------------------|--------------------------------------------------------|-------------------------------------|
| Golden shape file | `tests/fixtures/normalize_metric_shape.golden.json`    | Key removal from output             |
| Shape hash test   | `test_normalize_metric_shape_hash_matches_golden_file` | Structural drift                    |
| Dual-format test  | `test_normalize_metric_produces_dual_format`           | Missing flat or nested keys         |
| Zero-value test   | `test_normalize_metric_preserves_zero_values`          | `_first_defined()` regression       |
| CODEOWNERS        | `.github/CODEOWNERS`                                   | Unreviewed changes to adapter/panel |
| Pre-commit hook   | `normalize-metric-format-guard`                        | Golden file deletion                |

---

## Rules

1. **NO removal** of either flat or nested keys without an RFC (D-21, C-22).
2. **Additions** to the output are allowed (golden shape test permits supersets).
3. Changes to `cascor_service_adapter.py` or `metrics_panel.py` require `@pcalnon` review.
4. The golden shape file must not be deleted (pre-commit hook enforced).
