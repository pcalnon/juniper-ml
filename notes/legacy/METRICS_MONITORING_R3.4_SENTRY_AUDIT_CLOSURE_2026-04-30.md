# METRICS-MON R3.4 — Sentry-tests audit closure

**Date:** 2026-04-30
**Author:** Paul Calnon
**Status:** ✅ Decided — **already satisfied; no remediation needed**.
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §6 R3.4.
**Entry plan:** [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md) §3 Q3.
**Companion pattern:** [`METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md`](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md) (no-work-needed audit closure).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. The original finding

[Review plan](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) §9 seed-09:

> Sentry tests gated behind `importorskip`; regressions invisible when extra not installed (cascor, canopy, data; best-practices; composite=2)

The [R3 entry plan](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md) §3 Q3 expected to remediate this with three fan-out PRs (one per repo) that:

- Confirm `sentry-sdk` is a hard runtime + dev/test dep
- Remove `pytest.importorskip("sentry_sdk")` from the SEC-15 / SEC-10 hook tests
- Re-run CI to confirm the hook tests run on every run (not skipped)

---

## 2. The audit

Wave 1 implementation began with R3.4. Before opening the three remediation PRs, an audit ran across the three test trees searching for the gating mechanism the seed described:

```bash
# Across cascor, canopy, data test trees:
grep -rn "importorskip.*sentry_sdk" .          # zero matches
grep -rn "importorskip" . | grep sentry        # zero matches
grep -rn "skip.*sentry\|sentry.*skip" .        # zero matches
grep -rn "sys.modules.get..sentry"             # zero matches
grep -rn "find_spec..sentry"                   # zero matches
```

**Zero matches in all three repos.** The literal `importorskip("sentry_sdk")` premise of seed-09 does not match the current codebase.

What is actually in the code (verified by reading every sentry-touching test file in cascor, canopy, and data):

| Test pattern | Behaviour without `sentry-sdk` installed |
|---|---|
| `with patch("sentry_sdk.init") as mock_init:` (in `test_api_observability.py`, `test_observability.py`, `test_r2_1_5_wire_compat.py`) | `unittest.mock.patch` resolves `sentry_sdk.init` at decoration time → **fails at collection with `ModuleNotFoundError: No module named 'sentry_sdk'`**. CI surfaces a loud regression signal. |
| `monkeypatch.setitem(sys.modules, "sentry_sdk", _FakeSentry)` (in `test_phase1c_security.py`, `test_phase1d_security.py`) | Injects a fake `sentry_sdk` into `sys.modules` so `configure_sentry`'s lazy `import sentry_sdk` resolves to the fake. **Runs even without real `sentry-sdk` installed**, asserting the hook contract via the fake's recorded call. |

Both patterns achieve seed-09's underlying goal — *regressions become visible when `sentry-sdk` is absent or its API drifts* — without ever using `importorskip`.

Combined with the runtime-dep evidence (`sentry-sdk>=2.0.0` is in the `dependencies = [...]` block of every server's `pyproject.toml` — verified for cascor, canopy, data) and the test-extras evidence (`sentry-sdk[fastapi]>=2.0.0` is in each repo's `[test]` extra via the `juniper-observability` migration), there is **no plausible CI configuration** that would skip a sentry-hook test silently.

---

## 3. Decision

**R3.4 is already satisfied. No remediation PRs.**

The seed-09 finding was either:

- **Stale** — `importorskip("sentry_sdk")` was used in an earlier version of the codebase and was removed before the original review wrote the roadmap (pre-2026-04-25), without seed-09 being updated.
- **Misidentified** — the original review confused another `importorskip` call (e.g. `importorskip("prometheus_client")`, which **is** still present in `juniper-data/juniper_data/tests/unit/test_observability.py:81`, `:101`, `:119`) with a sentry-related one.

Either way, the current state of all three repos already meets the underlying regression-visibility goal. Adding three "remove importorskip" PRs would be no-ops modifying nothing.

---

## 4. Future-proofing — is the absence preserved?

To prevent a future contributor from re-introducing `importorskip("sentry_sdk")` and silently regressing the test surface, three guard-rails already exist:

1. **Hard runtime dep on every server**: `sentry-sdk>=2.0.0` in `pyproject.toml::dependencies` for cascor / canopy / data. A contributor moving it to optional would be a visible diff in CI.
2. **`with patch("sentry_sdk.init")` pattern in observability tests**: collection-time failure if the import is unavailable.
3. **CI matrix coverage**: every server runs its full test suite on Python 3.12 + 3.13 + 3.14 with `sentry-sdk` installed; a contributor stripping it in CI would surface the missing import in the same PR as the strip.

A formal grep-based pre-commit hook checking for `importorskip("sentry_sdk")` was considered and rejected — too narrow to justify the maintenance cost, and the existing patterns already produce loud failures.

---

## 5. R3 phase impact

This closure does **not** delay Phase R3 — it accelerates it by removing 3 fan-out PRs from the Wave 1 plan.

Updated Wave 1 PR count:

| Original | Adjusted |
|---|---|
| 11 PRs (R3.1 + R3.2 + R3.3 + R3.5 + R3.4×3 + R3.7×4) | **8 PRs** (R3.1 + R3.2 + R3.3 + R3.5 + R3.7×4) |

Wave 2 unchanged (R3.6 sweep + R3 roadmap close).

The roadmap §9 R3.4 row flips directly to **done** in this PR. The remaining Wave 1 items (R3.1 / R3.2 / R3.3 / R3.5 + R3.7×4) start next.

---

## 6. References

- [Review plan](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) §9 seed-09 (the original finding).
- [Roadmap](METRICS_MONITORING_ROADMAP_2026-04-25.md) §6 R3.4 (the planned remediation).
- [R3 entry plan](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md) §3 Q3 (the open question the audit resolves).
- [R2 exit-gate worker-adoption closure](METRICS_MONITORING_R2_EXIT_GATE_WORKER_ADOPTION_2026-04-29.md) — pattern for an audit-closure note replacing planned remediation.
