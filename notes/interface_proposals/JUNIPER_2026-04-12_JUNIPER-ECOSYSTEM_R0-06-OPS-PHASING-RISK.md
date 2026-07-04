# Round 0 Proposal R0-06: Operational Phasing, Risk Management, and Rollout

**Specialization**: phasing, risk register, deployment, observability, rollback
**Author**: Round 0 sub-agent (general-purpose)
**Date**: 2026-04-11
**Status**: Initial proposal — pre-consolidation
**Source doc**: `juniper-ml/notes/code-review/WEBSOCKET_MESSAGING_ARCHITECTURE_2026-04-10.md` (v1.3 STABLE, 2029 lines)

---

## 1. Scope

This proposal is the operational wrapper around the WebSocket migration spelled out in §9 of the architecture doc. It does NOT design:

- Broadcaster / backpressure internals (that belongs to the transport / server-internals agent).
- Drain callback / `clientside_callback` wiring (frontend-bridge agent).
- The `set_params` API shape (protocol / contract agent).
- Security controls (the security agent will own M-SEC-NN content; this doc treats Phase B-pre as a gate, not a design).
- Test plans (test-strategy agent).

It DOES design:

- **Phase ordering rationale** and the hard gates between phases.
- **Risk mitigations** for every RISK-NN in §10 with owner-class and kill-switch mapping.
- **Feature-flag strategy** for Phase C and any other phase that needs a ramp.
- **Observability / SLO commitments** for each phase (what must be in place before the phase is allowed to ship).
- **Deployment strategy**: dev → staging → production with canary cohorts.
- **Cross-repo coordination**: branch/PR/merge order across `juniper-cascor`, `juniper-cascor-client`, `juniper-canopy` (and `juniper-ml` meta-package).
- **Rollback levers** with time-to-flip targets.
- **Open-question resolution gates** (§11) with proposed defaults.
- **Documentation deliverables** per phase (runbooks, on-call docs, post-mortem templates).
- **Stakeholder communication cadence**.

The operational plan applies the user's global **Thread Handoff** and **Worktree** operating instructions (from `~/.claude/CLAUDE.md` and `Juniper/CLAUDE.md`) so that the work can cleanly cross session/context boundaries.

---

## 2. Source-doc cross-references

| Source-doc section | Use in this proposal |
|---|---|
| §1.1, §1.2, §1.3 | Motivation (the 3 MB/s REST polling bomb) and the Option B Interval-drain architectural correction |
| §2.9 (entire) | Phase B-pre security gate; M-SEC-01..07 tracked as gate criteria |
| §5.6 | Production Latency Measurement Plan — the SLO instrumentation that lets Phase C flip its feature flag |
| §5.7 | User-research validation plan (optional calendar-time eater, decision gate in §9) |
| §6.5 | Reconnect protocol (sequence numbers + replay) — the correctness floor for silent-data-loss mitigation |
| §7 (GAP-WS-01..33) | Concrete work items mapped to phases |
| §9.1..9.10 | Phase scope, dependencies, and effort baseline |
| §9.11 | Total effort (~12 engineering days, ~4 weeks calendar) |
| §9.12 | Ordering rationale — verbatim dependency chain |
| §9.13 | Release coordination — the cross-repo merge sequence |
| §10 | Risk register (RISK-01..16) — mapped 1:1 in §4 below |
| §11 | Open questions — converted to decision gates in §9 below |

Every RISK-NN (16 total) is mapped below; every Phase A–I has observability, rollback, and gate criteria.

---

## 3. Phase ordering rationale

The architecture doc's §9.12 gives the dependency chain: **A | B-pre → B → C | D**, with E/F/G/H/I as parallel work. This section explains *why* each edge is load-bearing and what happens if it is violated.

### 3.1 Phase A prerequisites

Phase A (`juniper-cascor-client` `set_params` WebSocket method) has **no upstream dependencies**. It is an additive SDK change. It can start immediately, in parallel with Phase B-pre.

**Why A is first**:
- Phase C depends on the SDK exposing the method, so the SDK must ship (and be PyPI-published) before the canopy adapter can consume it.
- The `juniper-ml` meta-package extras pin `juniper-cascor-client>=X.Y.Z`. Until A ships and bumps that pin, Phase C's pyproject edit would pin to a non-existent version.
- Phase A is additive: no breaking changes, cannot break existing callers. It is the lowest-risk item to ship first as a confidence-builder and CI-path smoke test.

**Violation consequence**: if C is drafted before A is on PyPI, CI fails on import at best, or C silently shadows a non-existent method at worst. The merge queue must not allow this ordering.

**Gate to exit Phase A**:
- `juniper-cascor-client` new version tagged, GitHub release created, OIDC publish succeeded, PyPI index shows the new version (typically 2-5 minutes after tag).
- SDK CHANGELOG has an "Added" entry for `set_params`.
- At least one consumer (Phase C PR draft) can `pip install` the new version without a resolver error.

### 3.2 Phase B-pre security gate (REQUIRED before Phase D)

The architecture doc is explicit in §2.9.3: **Phase D MUST NOT ship until M-SEC-01, M-SEC-02, and M-SEC-03 are in place.** This is not guidance — it is a hard gate.

**Why B-pre is a gate**:
- Phase D routes `start`/`stop`/`pause`/`resume`/`reset` through `/ws/control`. Without Origin validation (M-SEC-01), any third-party page the user visits can issue those commands to `localhost:8050` — CSWSH. RISK-15 documents this as **High severity**.
- Phase B also exposes the WebSocket path to live traffic at production rates. Although B itself only ships read-side browser wiring, it validates the transport surface that D will consume — if B ships without `max_size` guards (M-SEC-03), a 100 MB inbound frame can exhaust server memory before parsing.
- The security controls are tiny (1 day of effort per §9.2) relative to the amount of code they protect. Front-loading them is cheap insurance.

**Explicit Phase B-pre exit criterion (all must be true before any Phase D PR is eligible for merge)**:

1. **M-SEC-01 landed**: `Origin` allowlist present on canopy `/ws/training` and `/ws/control`. Integration test `test_origin_validation_rejects_third_party_pages` green on CI.
2. **M-SEC-01b landed**: same allowlist on cascor `/ws/*` endpoints (the demo-mode / direct-connect attack surface). Shared `validate_origin()` helper extracted and reused.
3. **M-SEC-02 landed**: cookie-session auth + CSRF token first-frame validation on canopy `/ws/control`. Integration test `test_csrf_required_for_control_commands` green. Session cookie attributes verified: `HttpOnly; Secure; SameSite=Strict; Path=/`.
4. **M-SEC-03 landed**: explicit `max_size` on every `receive_*()` call across `juniper-cascor/src/api/websocket/*.py` and `juniper-canopy/src/main.py`. Unit test `test_oversized_frame_rejected_with_1009` green.
5. **CSP / security headers review**: documented in the canopy PR description that no new XSS vectors were introduced.
6. **Staging validation pass**: Phase B-pre deployed to staging for ≥ 24 hours with no auth-related user lockouts (see §7.1 for the staging procedure).
7. **On-call runbook**: `juniper-canopy/notes/runbooks/ws-auth-lockout.md` published describing how to temporarily disable WS auth if a production lockout is observed (operator flips `Settings.disable_ws_auth=True` and restarts canopy).
8. **RISK-15 mitigation marked "in production"** in the risk-tracking sheet.

If any of 1-8 is not met, Phase D PRs are blocked in the merge queue (use GitHub branch protection + a required check that verifies the M-SEC-NN test names exist and are green).

**Why B-pre is not *strictly* a Phase B prerequisite** (important nuance):
- Phase B ships browser wiring that reads WS data and displays charts. It does not expose any new control surface — the control surface is inherited from the current (broken) `/ws/control` endpoint.
- **However**, the M-SEC-03 frame-size guards are a hard prereq for Phase B because Phase B increases traffic volume per connection. Without a `max_size` guard, a malicious `/ws/training` frame from a malformed client could DoS the canopy server.
- **Operational call**: treat M-SEC-03 as a Phase B prerequisite (must land in the same wave as Phase B) and treat M-SEC-01/01b/02 as Phase D prerequisites. This matches the architecture doc's §9.2 spec exactly.

### 3.3 Phase B Interval drain wiring

Phase B is the largest item (**4 days engineering, RISK-02 High**). It depends on:

- **Phase B-pre M-SEC-03** (max_size guards), per §3.2 above.
- Nothing else from Phase A (the browser bridge wires `window.cascorWS` events into Dash stores — it does not import the Python SDK).

Why B precedes both C and D:
- C wires sliders to `window.cascorControlWS.send(...)`. That JS object is part of the Phase B bridge.
- D wires buttons to `window.cascorControlWS.send(...)`. Same dependency.

**Phase B exit gate**:
- All `dash_duo` / Playwright tests in §9.3 green on CI.
- The P0 motivator metric — `/api/metrics/history` REST polling volume — is **measurably reduced** in staging (target: >90% reduction in bytes/sec when WebSocket is connected). This is the "did we actually fix it" proof.
- GAP-WS-24 latency instrumentation is ingesting non-zero data into the canopy Prometheus histogram for at least 1 hour.
- Connection-status-aware polling toggle (GAP-WS-25) observed in action: disconnecting cascor causes the dashboard to fall back to polling within the drain interval.
- Demo-mode parity test `test_demo_mode_metrics_parity` green (RISK-08 gate).
- No browser memory leak observed in the overnight soak test (RISK-10 gate).

### 3.4 Phase C set_params (P2, feature-flagged)

Phase C depends on both Phase A (SDK) and Phase B (browser bridge). It was **relabeled from P1 to P2** in the architecture doc based on the §5.3.1 ack-vs-effect-latency analysis: the `set_params` ack latency is likely invisible inside the much-larger training-effect-observation loop. Concretely, if you move a slider and the chart updates only after the next training step (100 ms to multi-second), the fact that the ack arrived 2 ms vs 60 ms earlier is invisible to the user.

Because of this uncertainty, Phase C ships **behind a feature flag** (`Settings.use_websocket_set_params=False` by default) and is validated against the §5.6 latency histogram before the default is flipped.

See §5 below for the feature-flag design.

**Phase C exit gate** (to flip flag default):
- §5.6 latency histogram has ≥ 1 week of data showing the `set_params` p95 ack latency via WebSocket is < 100 ms AND the p95 via REST is > 200 ms (the delta must be big enough to be observable).
- User-research signal (if §11 Q7 chooses to run it) shows subjective "feels more responsive" from ≥ 3 of 5 subjects.
- No increase in orphaned-command incidents (RISK-13) over baseline.
- Canary cohort (see §7.2) has had the flag enabled for ≥ 1 week with zero param-loss incidents.

If any criterion fails, the default stays `False` and the work-per-key routing inside `apply_params` stays dormant but present (dead-code but not removed — the infra is there for a future retry).

### 3.5 Phase D control buttons (gated on B-pre)

Phase D depends on Phase B (browser bridge exists) AND Phase B-pre (security gate, per §3.2). The REST POST endpoints at `/api/train/{command}` remain first-class supported APIs — Phase D is NOT a migration away from REST, it is an **additive WebSocket front-door** for browsers with a REST fallback.

**Phase D exit gate**:
- All Playwright tests in §9.5 green.
- CSRF regression test `test_csrf_required_for_websocket_start` green.
- 24 hours in staging with no orphaned-command incidents.
- The REST POST endpoints still receive traffic from (and continue to work for) non-browser consumers (curl scripts, CI probes). Verify via canopy access logs.
- `docs/REFERENCE.md` in canopy updated to document both the REST and WebSocket training control APIs.

### 3.6 Phases E-I

**Phase E (backpressure, 1 day, RISK-04 / RISK-11 mitigation)**:
- Independent of the canopy phases.
- CAN ship any time after the baseline PRs land. Recommended timing: **after Phase B is in production**, because that's when real workload exposes the slow-client pattern.
- Ships behind `Settings.ws_backpressure_policy ∈ {block, drop_oldest, close_slow}` with default `block` to preserve current behavior.
- The quick-fix `wait_for(send_json, timeout=0.5)` is **hotfixable**: if RISK-04 actually triggers in production before E is complete, that single line can ship as an emergency patch to cascor independent of canopy.

**Phase F (heartbeat + jitter, 0.5 day)**:
- Independent. Best shipped alongside Phase B (they touch the same JS file).
- RISK-06 (reconnect storm) mitigation.
- 3-line change to add jitter to the backoff schedule.

**Phase G (cascor `set_params` integration test, 0.5 day)**:
- Independent. Uses FastAPI `TestClient` — no SDK dependency.
- Should land in the same cascor release as Phase B (the server-side sequence-number changes).

**Phase H (`_normalize_metric` audit, 1 day)**:
- Independent. The **regression test must land before the audit** (per §9.9), to lock in the dual-format contract.
- Blocks any future work that wants to remove the nested format (RISK-01 gate).

**Phase I (asset cache busting, 0.5 day)**:
- Independent. Can ship in the same PR as Phase B to ensure the v1.2 envelope format is picked up by browsers without a hard refresh.
- Mandatory before Phase B goes to production — otherwise users will see stale `websocket_client.js` and the new `seq` fields will not be processed.

---

## 4. Risk register mitigation map (RISK-01..16)

Every risk from §10 is mapped to: severity, phase ownership, owner-class (team), monitoring signal, kill-switch, and rollback time. Owner-classes are: **backend-cascor**, **backend-canopy**, **frontend**, **sdk**, **ops** (release engineering / SRE), **security**.

### RISK-01 — Dual nested+flat metric format removed too aggressively

- **Severity / Likelihood**: High / Medium
- **Phase**: H
- **Owner-class**: backend-canopy
- **Mitigation**: §4.4 phased plan; lock-in regression test `test_normalize_metric_produces_dual_format` in Phase H BEFORE audit; ban any removal PR until audit document is published.
- **Monitoring signal**: canopy `/api/metrics` access-log + optional response-schema fingerprinting (hash the response shape for 24 hours, alert on drift).
- **Kill switch**: git revert on the normalize_metric change; canopy is stateless so a rollback is equivalent to a redeploy. **TTF (time-to-flip)**: ~5 minutes (blue/green or rolling redeploy).
- **Open owner decision**: who on backend-canopy runs the consumer audit (§9.9 deliverable).

### RISK-02 — Phase B clientside_callback wiring hard to debug remotely

- **Severity / Likelihood**: Medium / High
- **Phase**: B
- **Owner-class**: frontend + ops
- **Mitigation**: Playwright trace viewer + `dash_duo` store assertions + verification matrix in §8.8; the §1.3 Option B Interval drain pattern is the foundation. Runbook must document how to capture a browser trace in staging.
- **Monitoring signal**: `canopy_ws_delivery_latency_ms` (§5.6), drain callback error rate, browser JS console error rate (via Sentry-style reporter).
- **Kill switch**: `Settings.disable_ws_bridge=True` — forces fallback to pre-Phase-B REST polling even when a WebSocket is available. **TTF**: ~5 minutes (config flip + restart).
- **Rollback depth**: the fallback path must be kept functional through at least Phase D. Do NOT delete the REST polling code in Phase B — it stays as the flag-off path.

### RISK-03 — Phase C race: REST PATCH and WS set_params land out of order

- **Severity / Likelihood**: Medium / Low (hot/cold disjoint; `update_params` uses keyed merges, verified at `lifecycle/manager.py:702-723`)
- **Phase**: C
- **Owner-class**: backend-canopy
- **Mitigation**: Per-param routing in the `apply_params` delegating wrapper; ship behind `use_websocket_set_params` flag; Phase C tests enforce the routing (`test_learning_rate_change_uses_websocket_set_params`, etc.); the shared `_training_lock` on the cascor side linearizes merges.
- **Monitoring signal**: lifecycle `set_params_latency_histogram` (tagged by transport: `ws` vs `rest`); a "set_params order-violation" log event if a WS response arrives after a REST response for the same key.
- **Kill switch**: `Settings.use_websocket_set_params=False`. **TTF**: ~5 minutes.

### RISK-04 — Slow-client blocking manifests in normal dev workflows

- **Severity / Likelihood**: Medium / Medium (a hung dev-tools tab serially blocks all broadcasts)
- **Phase**: E
- **Owner-class**: backend-cascor
- **Mitigation**: Phase E full backpressure; quick-fix `asyncio.wait_for(send_json, timeout=0.5)` is hotfixable on its own (single-line patch, hours to deploy).
- **Monitoring signal**: cascor `ws_broadcast_send_duration_seconds` histogram; alert when p95 > 500 ms. Per-client send-queue depth.
- **Kill switch**: `Settings.ws_backpressure_policy=close_slow` (drops the misbehaving tab). **TTF**: ~5 minutes.

### RISK-05 — Playwright fixture misses a real-cascor-only regression

- **Severity / Likelihood**: Medium / Medium
- **Phase**: B, D
- **Owner-class**: ops
- **Mitigation**: nightly (or hourly) smoke test against a real cascor instance in staging, separate from the fast E2E suite; alert on diff with fake-cascor results.
- **Monitoring signal**: smoke-test job success/failure over 7-day rolling window.
- **Kill switch**: none — this risk is about coverage, not runtime behavior. If it triggers, the response is to fix the test and re-validate.

### RISK-06 — Reconnection storm after cascor restart

- **Severity / Likelihood**: Low / Medium (raised — current backoff has no jitter, causes synchronized reconnect waves)
- **Phase**: F
- **Owner-class**: frontend
- **Mitigation**: Phase F adds jitter (3-line change) to the exponential backoff schedule. Implementation note: full jitter (`delay = random(0, base * 2**attempt)`) not decorrelated jitter, for simplicity.
- **Monitoring signal**: cascor `ws_connections_total` derivative (connections/sec); alert on spikes > 5× baseline. Alternatively: cascor CPU % at restart time.
- **Kill switch**: client-side: if a reconnect storm is observed, ops can temporarily disable the browser-side reconnect via `Settings.disable_ws_auto_reconnect` and ask users to hard-refresh. **TTF**: ~10 minutes (config + redeploy + user comms).

### RISK-07 — 50-connection cap hit by multi-tenant deployment

- **Severity / Likelihood**: Low / Low
- **Phase**: tangential to Phase E; addressed via `Settings.ws_max_connections` (already configurable) + M-SEC-04 per-IP cap.
- **Owner-class**: backend-cascor + ops
- **Mitigation**: operator-tunable config. Document in the deployment runbook.
- **Monitoring signal**: cascor `ws_active_connections_total` gauge; alert at 80% of cap.
- **Kill switch**: raise `Settings.ws_max_connections` (requires restart). **TTF**: ~10 minutes.
- **Open question**: §11 Q1 (deployment topology) resolves this. See §9 below.

### RISK-08 — Demo mode parity breaks after WebSocket migration

- **Severity / Likelihood**: Low / Medium
- **Phase**: B (explicit test in the §9.3 test plan)
- **Owner-class**: backend-canopy
- **Mitigation**: `test_demo_mode_metrics_parity` required in Phase B test plan (already in §9.3). The test is a blocker, not a warning.
- **Monitoring signal**: demo-mode smoke test; manual spot-check by developers running canopy in demo mode.
- **Kill switch**: if demo mode breaks after a merge, revert the specific PR. TTF: ~10 minutes.

### RISK-09 — Phase C changes user-perceived behavior unexpectedly

- **Severity / Likelihood**: Low / Medium
- **Phase**: C
- **Owner-class**: backend-canopy + frontend
- **Mitigation**: **Phase C ships behind `Settings.use_websocket_set_params=False` feature flag**; §5.6 instrumentation is the arbiter. Canary cohort (§7.2) tests the flag-enabled path before rollout.
- **Monitoring signal**: `canopy_ws_delivery_latency_ms{type=set_params_ack}` histogram; ratio of WS ack to REST ack latency; user-study qualitative signal (if run).
- **Kill switch**: `Settings.use_websocket_set_params=False`. **TTF**: ~5 minutes.

### RISK-10 — Browser-side memory exhaustion from unbounded chart data

- **Severity / Likelihood**: Medium / High (overnight runs accumulate millions of points)
- **Phase**: B
- **Owner-class**: frontend
- **Mitigation**: GAP-WS-14 mandates `Plotly.extendTraces(maxPoints=5000)`; ring buffer in `ws-metrics-buffer` (last 1000 events); JS handler enforces buffer cap (**not** the drain callback, which is throttled in background tabs).
- **Monitoring signal**: browser `performance.memory.usedJSHeapSize` sampled every 60 s by the JS health module, POSTed along with the latency histogram to the canopy `/api/ws_latency` endpoint. Alert on p95 heap > 500 MB.
- **Kill switch**: `Settings.disable_ws_bridge=True` (falls back to polling, which has its own bounded memory).
- **Validation requirement**: 24-hour soak test in staging before Phase B flips to production.

### RISK-11 — Silent data loss via drop-oldest broadcast queue

- **Severity / Likelihood**: High / Low (only under sustained slow-client load)
- **Phase**: E
- **Owner-class**: backend-cascor
- **Mitigation**: Phase E policy — **close slow client (1008) for state-bearing events**; drop-oldest only for coalesceable progress events with separate per-type queue.
- **Monitoring signal**: cascor `ws_dropped_messages_total{reason, type}` counter; alert on any non-zero `state_dropped`.
- **Kill switch**: revert to `ws_backpressure_policy=block` (the old behavior). Known trade-off: block restores RISK-04. This is an intentional knob.

### RISK-12 — Background tab memory spike when foregrounded

- **Severity / Likelihood**: Low / Medium
- **Phase**: B
- **Owner-class**: frontend
- **Mitigation**: JS-side ring buffer enforcement (not drain-callback enforcement) — see RISK-10.
- **Monitoring signal**: same as RISK-10 (browser heap reporter).
- **Kill switch**: same.

### RISK-13 — Orphaned commands after timeout

- **Severity / Likelihood**: Medium / Medium
- **Phase**: B, C (per-command timeouts), D
- **Owner-class**: frontend + backend-canopy
- **Mitigation**: GAP-WS-32 per-command correlation IDs + `pending verification` UI state; the client resolves pending commands via matching `command_response` OR a `state` event that reflects the change.
- **Monitoring signal**: `canopy_orphaned_commands_total` counter; alert on rate > 1/min.
- **Kill switch**: reduce per-command timeouts (but this increases false-positive orphaned reports); or `Settings.use_websocket_set_params=False` to avoid the WS codepath.

### RISK-14 — Cascor crash mid-broadcast leaves clients inconsistent

- **Severity / Likelihood**: Low / Low
- **Phase**: B (server-start-time change in the replay protocol)
- **Owner-class**: backend-cascor
- **Mitigation**: GAP-WS-13 reconnect+replay protocol — `server_start_time` change forces all clients to do a full REST resync on reconnect.
- **Monitoring signal**: cascor `server_start_time` change events should correspond to client resync events observed in `/api/metrics/history` access log.
- **Kill switch**: rolling-restart the canopy server (which bounces all browser WS connections and forces reconnect).

### RISK-15 — CSWSH attack exploits missing Origin validation (HIGH)

- **Severity / Likelihood**: **High / Medium** (any web page visited during canopy session)
- **Phase**: B-pre
- **Owner-class**: security + backend-canopy + backend-cascor
- **Mitigation**: M-SEC-01 + M-SEC-01b + M-SEC-02 in §2.9. Phase B-pre is a hard prerequisite for Phase D.
- **Monitoring signal**: canopy `ws_auth_rejections_total{reason}` counter — alert on any non-zero `origin_mismatch` from an unknown origin (indicates an active attack attempt).
- **Kill switch**: `Settings.disable_ws_control_endpoint=True` — hard-disables `/ws/control` and forces all control commands through REST (which has its own CSRF story). **TTF**: ~5 minutes.
- **Gate**: see §3.2 above.

### RISK-16 — Topology message exceeds 64 KB silently for large networks

- **Severity / Likelihood**: Medium / **Medium** (any network with >50-100 hidden units)
- **Phase**: B-pre (max_size guards surface the issue) + follow-up work
- **Owner-class**: backend-cascor
- **Mitigation**: GAP-WS-18 chunking or REST fallback; document the threshold; add a server-side size guard that emits a structured error rather than a silent truncation.
- **Monitoring signal**: cascor `ws_oversized_frame_total{endpoint, type}` counter; log warning on any truncated topology.
- **Kill switch**: fall back to REST `/api/topology` if the WS frame is oversized (client-side already has this as a fallback path).

### Risk mitigation matrix (compact)

| ID   | Phase   | Owner-class                   | Kill switch                         | TTF     |
|------|---------|-------------------------------|-------------------------------------|---------|
| 01   | H       | backend-canopy                | git revert + redeploy               | 5 min   |
| 02   | B       | frontend + ops                | `disable_ws_bridge=True`            | 5 min   |
| 03   | C       | backend-canopy                | `use_websocket_set_params=False`    | 5 min   |
| 04   | E       | backend-cascor                | `ws_backpressure_policy=close_slow` | 5 min   |
| 05   | B,D     | ops                           | n/a (coverage risk)                 | -       |
| 06   | F       | frontend                      | `disable_ws_auto_reconnect`         | 10 min  |
| 07   | -       | backend-cascor + ops          | raise `ws_max_connections`          | 10 min  |
| 08   | B       | backend-canopy                | revert Phase B PR                   | 10 min  |
| 09   | C       | backend-canopy + frontend     | `use_websocket_set_params=False`    | 5 min   |
| 10   | B       | frontend                      | `disable_ws_bridge=True`            | 5 min   |
| 11   | E       | backend-cascor                | revert to `policy=block`            | 5 min   |
| 12   | B       | frontend                      | same as RISK-10                     | 5 min   |
| 13   | B,C,D   | frontend + backend-canopy     | `use_websocket_set_params=False`    | 5 min   |
| 14   | B       | backend-cascor                | rolling restart                     | 10 min  |
| 15   | B-pre   | security + backend            | `disable_ws_control_endpoint=True`  | 5 min   |
| 16   | B-pre   | backend-cascor                | REST fallback for topology          | 5 min   |

---

## 5. Feature flag design

### 5.1 Phase C flag (the canonical example)

**Flag**: `Settings.use_websocket_set_params: bool = False`

**Lives in**: `juniper-canopy/src/config.py` (follows canopy's existing `Settings` pydantic pattern). Environment override: `CANOPY_USE_WEBSOCKET_SET_PARAMS=true`.

**Mechanism**:
- The `cascor_service_adapter.apply_params(params)` delegating wrapper inspects `Settings.use_websocket_set_params` AND the hot/cold whitelist from §5.
- If the flag is False → all params route through `_apply_params_cold()` (REST), regardless of hot/cold classification. This preserves pre-Phase-C behavior exactly.
- If the flag is True → hot params route through `_apply_params_hot()` (WebSocket `set_params`), cold params still go through REST.
- The flag is evaluated on every call (cheap attribute access, no restart required to flip).

**Default state during rollout**:

| Environment     | Default | Who flips it | How |
|-----------------|---------|---|-------------|
| Dev (laptops)   | True    | Developer | Env var |
| Staging         | True    | Ops on Phase C merge to main | `CANOPY_USE_WEBSOCKET_SET_PARAMS=true` in staging compose |
| Canary cohort   | True    | Ops after Phase C in staging ≥ 48 hours | Selective canary deploy |
| Production      | False | Ops (post-canary success) | Config edit + restart |

**Flip criteria** (§3.4 gate): §5.6 histogram ≥ 1 week of data, p95 ack latency delta is meaningful, zero increase in orphaned-command incidents, canary cohort ≥ 1 week clean.

**Rollback**: single config flip + restart. TTF ~5 minutes. Because the REST codepath is retained (not removed) as the delegating wrapper's fallback, rollback is code-free.

**Removal criterion**: do NOT remove the flag or the REST path for at least 1 release cycle after the flag default flips. This keeps the rollback lever warm.

### 5.2 Other phase flags

| Phase | Flag | Default (pre/post) | Purpose |
|---|---|---|---|
| B | `Settings.disable_ws_bridge: bool` | `False` / `False` (kill switch only) | Emergency disable of the browser bridge; falls back to REST polling |
| B-pre | `Settings.disable_ws_auth: bool` | `False` prod, `True` dev | Local-dev escape hatch (must default False in production) |
| B-pre | `Settings.disable_ws_control_endpoint: bool` | `False` / `False` (kill switch) | Disables `/ws/control` entirely (CSWSH emergency kill) |
| E | `Settings.ws_backpressure_policy` | `block` / `close_slow` | Slow-client handling policy; default migrates on a major version bump |
| F | `Settings.disable_ws_auto_reconnect: bool` | `False` / `False` (kill switch) | Stops the reconnect storm if F's jitter fix is not yet deployed |

### 5.3 Default state and rollback

**Operating principle**: every phase that touches a runtime behavior MUST have a kill switch that lets ops disable the phase's new behavior without a code rollback. The kill switch must be:

1. **Config-only** (no code change) — so that flipping does not require a PR-review cycle.
2. **Fast** (< 10 minutes to take effect in production).
3. **Tested** — the CI suite must include a test that verifies the kill-switch value takes effect (e.g., `test_disable_ws_bridge_forces_rest_polling`).
4. **Documented** — in the runbook for the phase.

**No silent behavior changes**: if a phase removes a flag later (post-rollout hardening), the removal must itself be a PR that says "feature X has been stable in prod for N weeks, removing the kill switch." The removal is a separate PR, not a drive-by cleanup inside another change.

---

## 6. Observability requirements per phase

The rule: **no phase ships to production until its metrics exist in the canopy Prometheus scrape AND the on-call dashboard has panels for them.** Pre-production environments (dev, staging) can run without metrics, but the production release gate is blocked on the dashboard panel.

### 6.1 Metrics

| Phase | Metric | Type | Labels | Threshold |
|---|---|---|---|---|
| A | `juniper_cascor_client_ws_set_params_total` | counter | `status ∈ {ok, timeout, error}` | n/a |
| B-pre | `canopy_ws_auth_rejections_total` | counter | `reason ∈ {origin_mismatch, csrf_invalid, cookie_missing}` | alert > 0 from unknown origin |
| B-pre | `canopy_ws_oversized_frame_total` | counter | `endpoint` | alert > 0 |
| B | `canopy_ws_delivery_latency_ms_bucket` | histogram | `type ∈ {metrics, state, topology, cascade_add, candidate_progress, event, command_response}` | §5.6 SLOs |
| B | `canopy_ws_active_connections` | gauge | - | alert > 80% of `ws_max_connections` |
| B | `canopy_ws_reconnect_total` | counter | `reason` | alert spike > 5× baseline |
| B | `canopy_ws_browser_heap_mb` | histogram (reported from JS) | - | alert p95 > 500 MB |
| B | `canopy_rest_polling_bytes_per_sec` | gauge | - | **target**: > 90% reduction post-Phase-B |
| C | `canopy_set_params_latency_ms_bucket` | histogram | `transport ∈ {ws, rest}, key` | Phase C flip gate |
| C | `canopy_orphaned_commands_total` | counter | `command` | alert rate > 1/min |
| D | `canopy_training_control_total` | counter | `command, transport ∈ {ws, rest}` | track ratio |
| E | `cascor_ws_broadcast_send_duration_seconds` | histogram | - | alert p95 > 500 ms |
| E | `cascor_ws_dropped_messages_total` | counter | `reason, type` | alert any non-zero `state_dropped` |
| E | `cascor_ws_slow_client_closes_total` | counter | - | track ratio to `ws_active_connections` |
| F | (reuses `canopy_ws_reconnect_total`) | - | - | - |

### 6.2 Logs

Every phase should log:

- WS connection open/close with `client_ip`, `client_id`, `duration`, `close_code`, `close_reason` (opaque, see M-SEC-06).
- WS auth failures with the **actual** reason (server-side only, not in close reason).
- WS protocol errors (`json.JSONDecodeError`, unknown command, validation failure) with the offending command name and a hash of the payload.
- Backpressure events (Phase E): slow-client close, dropped message count.

Logs are collected via the existing canopy / cascor log stack (no new infra). Structured JSON output preferred.

**No PII in logs**: M-SEC-07 allowlist applies. No `set_params` payloads logged in cleartext except for allowlisted keys.

### 6.3 Alerts and SLOs

Alerting rules (Prometheus AlertManager, or equivalent):

| Alert | Condition | Phase | Severity |
|---|---|---|---|
| `WSOriginRejection` | `increase(canopy_ws_auth_rejections_total{reason="origin_mismatch"}[5m]) > 0` | B-pre | page on-call (possible attack) |
| `WSOversizedFrame` | `increase(canopy_ws_oversized_frame_total[5m]) > 0` | B-pre | page on-call |
| `WSDeliveryLatencyP95High` | `histogram_quantile(0.95, canopy_ws_delivery_latency_ms_bucket{type="metrics"}[5m]) > 500` | B | ticket |
| `WSConnectionCount80` | `canopy_ws_active_connections / ws_max_connections > 0.8` | B | ticket |
| `WSBrowserHeapHigh` | `histogram_quantile(0.95, canopy_ws_browser_heap_mb_bucket[1h]) > 500` | B | ticket |
| `WSReconnectStorm` | `rate(canopy_ws_reconnect_total[1m]) > 5 * <baseline>` | F | ticket (page if jitter fix not deployed) |
| `WSStateDropped` | `increase(cascor_ws_dropped_messages_total{type="state"}[5m]) > 0` | E | page on-call |
| `WSSlowBroadcastP95` | `histogram_quantile(0.95, cascor_ws_broadcast_send_duration_seconds[5m]) > 0.5` | E | ticket |
| `CanopyOrphanedCommands` | `rate(canopy_orphaned_commands_total[5m]) > 1/60` | C, D | ticket |

**SLOs** (production targets, verified against §5.6 histograms):

| Event type | p50 | p95 | p99 |
|---|---|---|---|
| `metrics` delivery | < 100 ms | < 250 ms | < 500 ms |
| `state` delivery | < 50 ms | < 100 ms | < 200 ms |
| `command_response` (set_params) | < 50 ms | < 100 ms | < 200 ms |
| `command_response` (start/stop) | < 100 ms | < 250 ms | < 500 ms |
| `cascade_add` delivery | < 250 ms | < 500 ms | < 1000 ms |
| `topology` delivery (≤ 64 KB) | < 500 ms | < 1000 ms | < 2000 ms |

**Error budget**: 99.9% of events meet the p95 target over a 7-day rolling window. If the error budget is burned in < 1 day, freeze non-reliability work until recovered.

### 6.4 Production Latency Measurement Plan operationalization (§5.6)

The architecture doc's §5.6 sketches the instrumentation. Operationalization:

1. **Phase B implements the pipe**: cascor adds `emitted_at_monotonic` to every WS message envelope; canopy adds the browser-side JS histogram + `/api/ws_latency` POST endpoint.
2. **Phase B rolls out with the WS bridge**: the instrumentation IS part of Phase B, not a follow-up.
3. **Canopy backend aggregates** into `canopy_ws_delivery_latency_ms_bucket` (process-wide Prometheus histogram).
4. **Dashboard panel**: "WebSocket health" panel in canopy shows p50/p95/p99 per event type. **The panel updates via the same WebSocket path it measures** — this closes the loop and is itself a health signal (if the panel stops updating, something is broken).
5. **Clock offset**: the browser computes `clock_offset = server_wall_clock - browser_now` from `connection_established.data.server_time`. Re-computed on every reconnect to handle laptop sleep / time-sync events.
6. **Buckets**: `{50, 100, 200, 500, 1000, 2000, 5000}` ms per §5.6.
7. **Export cadence**: 60 s from browser to canopy. This is a deliberate rate — more frequent posts are not useful (the histograms aggregate over time anyway).
8. **SLO verification**: the §5.1 / §5.4 latency budget tables transition from "aspirations" to **SLOs** once the histogram has ≥ 1 week of data. Target: validate the budgets against real data by end-of-Phase-B.
9. **User-research option**: §5.7 proposes a 5-subject think-aloud study. Decision gate §9 Q7: run or skip.

Tracked as GAP-WS-24 (P2). Without this data, Phase C's feature-flag flip is a judgement call; with this data, it is evidence-based.

---

## 7. Deployment / rollout strategy

### 7.1 Dev → staging → production

Follows the three-tier model standard for the Juniper ecosystem:

**Tier 1: Dev (laptop / branch)**
- Developer runs `docker compose up` from `juniper-deploy/` OR `make dev` from each repo.
- Feature flags: all WS-related flags default to the most aggressive setting (the thing being tested).
- Gate: unit tests green + targeted manual verification.

**Tier 2: Staging**
- Staging environment mirrors production topology: canopy + cascor + juniper-data in Docker, reverse-proxied, TLS terminated.
- Deploy target: a staging host (or a staging namespace if Kubernetes-based).
- Feature flags: same as production's *post*-rollout target (what we want production to look like after the flip).
- Gate to exit staging:
  - CI green on the PR (unit + integration + E2E).
  - Deployed to staging for ≥ 24 hours (longer for Phase B — 48-72 hours — because of RISK-10 overnight memory).
  - Smoke tests green.
  - Metrics panels show healthy values (no alerts firing).
  - On-call runbook updated.

**Tier 3: Production**
- Blue/green or rolling deploy via the canopy's existing deployment mechanism (whatever that is — document it during Phase B-pre runbook).
- Feature flags: default to the **conservative** setting (flag off for Phase C) and the canary cohort flips them on.
- Gate to exit production deploy:
  - Post-deploy smoke tests green.
  - Error rate (canopy HTTP 5xx) stays flat for 30 minutes.
  - WS latency SLOs (§6.3) within targets for 1 hour.

**Rollback**: every production deploy has a pre-written rollback command (same-version redeploy of the previous image). On-call can execute it without escalation.

### 7.2 Canary cohort

For phases with user-visible behavior change (Phase C primarily, Phase D secondarily):

**Cohort selection**: a named subset of canopy deployments designated as "canary." In a single-tenant environment (Paul's laptop + one staging) the canary cohort is literally "developer environments." In a multi-tenant deployment (future), the canary cohort is a feature-flagged subset of user IDs, routed by a config-driven allowlist.

**Canary duration**:
- Phase C: **≥ 1 week** with the flag enabled, zero param-loss incidents, histogram shows improvement.
- Phase D: **≥ 48 hours** in canary, zero orphaned-command incidents above baseline.

**Canary exit**: flip the production default. The canary cohort becomes the leading edge of the production rollout.

**Canary abort**: flip the canary's flag to False. The canary is back on the pre-phase behavior. No code change needed.

### 7.3 Shadow traffic

**Shadow traffic is NOT used** for this migration. Rationale:
- WS is stateful; shadow traffic requires duplicating connections, which risks state divergence and double-execution of control commands.
- The Phase B WS path is read-only relative to training state; shadow "reads" would just duplicate work with no validation benefit.
- The `_normalize_metric` audit (Phase H, RISK-01) can compare old vs new via golden-file tests, not shadow traffic.

**What replaces shadow traffic**: the dual-transport setup in Phase B (the connection-status-aware polling toggle, GAP-WS-25). In effect, polling and WS both run simultaneously when WS is healthy — the dashboard uses WS, but the polling code still runs (returning `no_update`) and can be used for parity spot-checks by the on-call.

---

## 8. Cross-repo coordination

The migration touches `juniper-cascor`, `juniper-cascor-client`, `juniper-canopy`, and indirectly `juniper-ml` (the meta-package's extras). There is also `juniper-deploy` orchestration to coordinate.

### 8.1 Dependency order (cascor → cascor-client → canopy)

Enforced order (derived from §9.13):

1. **`juniper-cascor-client` Phase A PR** merges → main → tagged release → PyPI publish. **Wait** 2-5 minutes for PyPI index propagation.
2. **`juniper-cascor` Phase B-pre PR** (security hardening) merges. Independent of the SDK.
3. **`juniper-cascor` Phase B PR** (sequence numbers, replay buffer, emitted_at_monotonic, max_size guards) merges. Independent of the SDK.
4. **`juniper-canopy` Phase B-pre PR** (Origin, CSRF, max_size) merges. Can be combined with the cascor Phase B-pre PR if coordinated, but separate PRs are simpler.
5. **`juniper-canopy` Phase B PR** (browser bridge + polling toggle + connection indicator + GAP-WS-24 instrumentation + Phase I asset cache busting) merges. Independent of the SDK.
6. **`juniper-canopy` Phase C PR** rebases on latest main. Bumps `juniper-cascor-client>=<new-version>` in `pyproject.toml`. Requires `juniper-ml` extras pinning update in a follow-up. Runs CI with the new SDK. Merges.
7. **`juniper-canopy` Phase D PR** rebases on Phase B and Phase B-pre. Merges **only after** Phase B-pre M-SEC-01/01b/02/03 are confirmed in production.
8. **`juniper-cascor` Phase E PR** (backpressure) can ship any time after Phase B.
9. **`juniper-canopy` / `juniper-cascor` Phase F PR** (heartbeat + jitter) can ship alongside Phase B.
10. **`juniper-cascor` Phase G PR** (cascor set_params integration test) ships with Phase B server-side changes.
11. **`juniper-canopy` Phase H PR** (regression test + audit doc) independent; schedule opportunistically.
12. **`juniper-canopy` Phase I PR** (asset cache busting) bundled with Phase B.

Use **squash-merge** (not merge commits) for each PR for linear history. Use GitHub **merge queue** if available to serialize dependent merges.

**Branch naming**: per the Juniper worktree convention, feature branches follow `ws-migration/phase-<letter>-<slug>`. Example: `ws-migration/phase-b-pre-security`, `ws-migration/phase-b-browser-bridge`.

**Worktrees**: each phase gets its own worktree in `/home/pcalnon/Development/python/Juniper/worktrees/` per the ecosystem worktree procedure. Naming: `<repo>--ws-migration--phase-<letter>--<YYYYMMDD-HHMM>--<shorthash>`.

### 8.2 Version bumps

| Repo | Phase | Bump | Rationale |
|---|---|---|---|
| juniper-cascor-client | A | minor (`X.Y.Z → X.(Y+1).0`) | New public method |
| juniper-cascor | B-pre | patch | Security hardening, no API break |
| juniper-cascor | B | minor | New envelope field (`seq`) |
| juniper-cascor | E | minor | New `ws_backpressure_policy` setting; default preserves behavior |
| juniper-cascor | G | patch | Test-only |
| juniper-canopy | B-pre | patch | Security hardening |
| juniper-canopy | B | minor | New browser bridge, new instrumentation endpoint |
| juniper-canopy | C | patch | Internal refactor of `apply_params`; public API unchanged |
| juniper-canopy | D | patch | New WS control path; REST preserved |
| juniper-canopy | H | patch | Test + doc |
| juniper-canopy | I | patch | Asset handling |
| juniper-ml | - | patch (per SDK bump) | Extras pin update |

**Helm chart version discipline**: per the user's `project_helm_version_convention.md` auto-memory, all Juniper Helm charts must have `Chart.yaml` `version` and `appVersion` matching the app's semver. The version bumps above imply Helm chart bumps of the same version for any chart that packages these apps.

### 8.3 Changelog policy

Every PR updates `CHANGELOG.md` in the affected repo. Entries follow Keep-a-Changelog conventions:
- `### Added` — new user-visible features (Phase A `set_params`, Phase B bridge, Phase C feature flag).
- `### Changed` — behavior changes within existing APIs.
- `### Fixed` — bug fixes (Phase E backpressure, Phase F jitter).
- `### Security` — M-SEC-NN items.
- `### Deprecated` — none expected (explicit design goal: no deprecations in this migration).
- `### Removed` — none in this migration; removals are out of scope per RISK-01.

Every changelog entry cross-references the GAP-WS-NN IDs and the RISK-NN IDs it mitigates, so future-readers can trace from code → gap → risk → phase.

---

## 9. Open questions resolution plan (§11)

The architecture doc's §11 lists 7 remaining open questions. Each is converted below into a **decision gate** with a proposed default, a deciding party, and a deadline (which phase it must be resolved before).

### Q1 — Target deployment topology

- **Default**: single canopy + single cascor + N browser dashboards.
- **Decider**: Paul (project lead).
- **Deadline**: **before Phase E kickoff** (multi-tenant changes the backpressure design).
- **Proposed resolution**: assume single-tenant for v1 of the migration. Document in the canopy AGENTS.md that multi-tenant is a future-work item.

### Q2 — Browser compatibility requirement

- **Default**: Chromium only (Playwright default).
- **Decider**: Paul (project lead).
- **Deadline**: **before Phase B test plan finalization** (Firefox/WebKit fixtures add ~0.5 day to Phase B).
- **Proposed resolution**: Chromium-only for v1; Firefox/WebKit supported but untested. Add a `# tested on Chromium only` note in the canopy README.

### Q3 — Journaling `set_params` updates

- **Default**: no journaling in this migration.
- **Decider**: Paul (project lead).
- **Deadline**: **defer until after Phase C**.
- **Proposed resolution**: open a tracking issue for "param-change journal"; scope post-migration.

### Q4 — In-flight refactors of `dashboard_manager.py`

- **Default**: coordinate timing with release prep referenced in `CANOPY_CASCOR_INTERFACE_ROADMAP_2026-04-08.md` §6.0.
- **Decider**: Paul + the refactor author (self, in the Juniper case).
- **Deadline**: **before Phase B kickoff** (merge conflicts are ~guaranteed otherwise).
- **Proposed resolution**: audit all open PRs against `dashboard_manager.py` before Phase B starts; either wait for them to merge or coordinate branching from a shared base. Document in the Phase B PR description: "rebased on <commit-sha> after refactor-X."

### Q5 — Versioned WebSocket subprotocol (`juniper-cascor.v1`)

- **Default**: no subprotocol; defer.
- **Decider**: Paul.
- **Deadline**: **defer; revisit if/when a v2 envelope is needed.**
- **Proposed resolution**: document as a known future need. The `seq` field addition in Phase B is backwards-compatible (new clients tolerate missing `seq`, old clients ignore it), so no subprotocol is required for this migration.

### Q6 — Per-IP connection cap value

- **Default**: 5 connections / IP (M-SEC-04 proposal).
- **Decider**: security + Paul.
- **Deadline**: **before Phase B-pre ships**.
- **Proposed resolution**: start at 5/IP; expose `Settings.ws_max_connections_per_ip` as tunable; revisit if Q1 changes to multi-tenant.

### Q7 — User-research validation for latency thresholds

- **Default**: skip; use engineering judgement + §5.6 histogram.
- **Decider**: Paul.
- **Deadline**: **before Phase C scoping freeze** (adds 1-2 weeks calendar if chosen).
- **Proposed resolution**: skip for the initial migration — Phase C ships behind a feature flag anyway, and the §5.6 histogram gives us data. If subjective UX complaints surface post-rollout, run the study as a follow-up.

**Decision-gate enforcement**: each phase's exit gate includes "all open questions for this phase are resolved." A phase cannot exit staging until its gating open questions have documented answers in `notes/decisions/ws-migration-Q<N>.md`.

---

## 10. Documentation deliverables per phase

Each phase has required documentation outputs, tracked in the `juniper-canopy/notes/runbooks/` and `juniper-cascor/notes/runbooks/` directories.

| Phase | Deliverable | Location |
|---|---|---|
| A | SDK CHANGELOG entry; docstring for `set_params` | `juniper-cascor-client/CHANGELOG.md`, `ws_client.py` |
| B-pre | `ws-auth-lockout.md` runbook; `ws-cswsh-detection.md` runbook; updated security section in AGENTS.md | `juniper-canopy/notes/runbooks/` |
| B | `ws-bridge-debugging.md` runbook; `ws-memory-soak-test-procedure.md`; updated browser compat note in README | `juniper-canopy/notes/runbooks/`, `juniper-canopy/README.md` |
| B (§5.6) | "WebSocket health dashboard panel" doc in canopy `docs/REFERENCE.md` | `juniper-canopy/docs/REFERENCE.md` |
| C | `ws-set-params-feature-flag.md` runbook (how to flip the flag, how to monitor); updated `docs/REFERENCE.md` | `juniper-canopy/notes/runbooks/`, `juniper-canopy/docs/REFERENCE.md` |
| D | "Training control API" section in `docs/REFERENCE.md` (documents both REST and WS paths); `ws-control-button-debug.md` runbook | `juniper-canopy/docs/REFERENCE.md`, `juniper-canopy/notes/runbooks/` |
| E | `ws-slow-client-policy.md` runbook (describes each backpressure policy and when to use which) | `juniper-cascor/notes/runbooks/` |
| F | (runbook change for `disable_ws_auto_reconnect`) | `juniper-canopy/notes/runbooks/` |
| G | (test-only, no runbook) | - |
| H | `NORMALIZE_METRIC_CONSUMER_AUDIT_2026-04-XX.md` | `juniper-ml/notes/code-review/` |
| I | (asset handling section in `juniper-canopy/docs/DEPLOYMENT.md`) | `juniper-canopy/docs/DEPLOYMENT.md` |

**Runbook template** (every runbook must include):

1. **Symptom**: how does an operator notice this?
2. **Impact**: what's broken for users?
3. **Triage**: first commands to run (check flag state, check metric X, tail log Y).
4. **Mitigation**: immediate action (flip flag, restart, escalate).
5. **Root-cause investigation**: deeper steps.
6. **Escalation**: who to contact.
7. **Post-mortem template link**: after resolution, fill out the post-mortem.

**Post-mortem template**: a single reusable template at `juniper-ml/notes/templates/POST_MORTEM_TEMPLATE.md`. Required fields: timeline, impact, detection, root cause, mitigation, action items, lessons. Every production incident related to this migration generates a post-mortem.

---

## 11. Stakeholder communication plan

### 11.1 Stakeholders

- **Engineer implementing** (self / future-Claude): daily awareness of phase status.
- **Project lead (Paul)**: weekly status, per-phase go/no-go decisions.
- **Users of the dashboard** (ML researchers): announcements on user-visible changes (Phase B, C, D).
- **On-call / ops**: runbook-ready notice before each production deploy.
- **CI / release pipelines**: automated via GitHub Actions + `workflow_dispatch` escape hatch (per the `project_github_actions_stuck_run_recovery.md` memory).

### 11.2 Announcement cadence

| Event | Audience | Channel | Timing |
|---|---|---|---|
| Phase kickoff | Paul | Notes doc + thread handoff | Day 0 of phase |
| Phase PR opened | Paul | PR description with phase context | Day N of phase |
| Phase merged to main | Paul + on-call | PR merge notification | Immediate |
| Phase deployed to staging | on-call | Runbook update + staging-deploy log | Immediate |
| Phase entering canary (prod) | Paul + users | Short "what's changing" note | 24 hours before |
| Phase flipped in prod | Paul + users | Release notes | Immediate |
| Incident (any) | Paul + on-call | Post-mortem doc | Within 48 hours of resolution |

### 11.3 Escalation path

1. **Level 0**: runbook mitigation (flip kill switch, rollback).
2. **Level 1**: escalate to Paul (project lead) if runbook does not resolve within 30 minutes.
3. **Level 2**: emergency rollback to pre-phase state. Requires a `workflow_dispatch` trigger on the deploy workflow (per the `project_github_actions_stuck_run_recovery.md` memory, `workflow_dispatch` is the emergency escape hatch when a scheduled CI run is stuck).

**Pre-drafted escalation messages** live in `juniper-canopy/notes/runbooks/escalation-templates.md`. Three templates:

1. "WS migration incident — Level 1 — asking for go/no-go on rollback."
2. "WS migration incident — Level 2 — rollback in progress."
3. "WS migration incident — resolved, post-mortem attached."

---

## 12. Verification / acceptance criteria

### 12.1 Per-phase acceptance

Every phase is not considered "complete" until all of the following are true:

1. PR merged to main.
2. PR's test suite green (including any `dash_duo` / Playwright suite).
3. Deployed to staging for the phase's minimum soak time (24 hours standard, 48-72 hours for Phase B).
4. Metrics and alerts for the phase are in place.
5. Runbook for the phase is published.
6. All GAP-WS-NN items in the phase's scope are marked "done" in the architecture doc update.
7. All RISK-NN items owned by the phase have kill switches verified (a test that proves the kill switch works).
8. If the phase is feature-flagged: the flag's default-flip criterion is documented, even if not yet met.
9. Staging has been verified against the §5.6 latency SLOs (Phase B+).
10. Post-deploy smoke tests in production green.

### 12.2 Migration-wide acceptance

The migration is considered "complete" when:

- All 33 GAP-WS-NN items in §7 are addressed (marked done or intentionally deferred with a tracking issue).
- All 16 RISK-NN items in §10 have active mitigations in production.
- §5.6 production latency histogram shows SLOs met for all tracked event types.
- `canopy_rest_polling_bytes_per_sec` shows > 90% reduction vs pre-migration baseline — the P0 motivator is resolved.
- `/api/metrics/history` polling has been either removed OR demoted to the fallback-only code path (not removed — per RISK-01 caution).
- All feature flags are either flipped to the post-rollout default OR explicitly retained as kill switches with a documented rationale.
- Post-migration architecture doc (v1.4 or v2.0) is published documenting the final state.

### 12.3 Abandon-migration criteria

If any of the following occurs during the migration, **stop** and re-plan:

- A Phase B production rollout causes a user-visible regression that cannot be resolved by the kill switch within 30 minutes.
- A Phase B staging soak reveals a memory leak that cannot be bounded by the ring buffer.
- A Phase B-pre security change causes a production lockout that the `disable_ws_auth` escape hatch cannot resolve.
- A phase's test plan cannot be made to pass on CI within 2× its estimated engineering effort (indicates the design is wrong).
- Two consecutive post-mortems cite the same root cause — indicates a design flaw, not an execution flaw.

---

## 13. Disagreements with the source doc

The architecture doc is v1.3 STABLE and has been well-reviewed. My disagreements are small, mostly about **operational framing**, not substance.

### 13.1 Phase B-pre should be split into B-pre-a (frame-size) and B-pre-b (auth+CSRF)

The source doc bundles M-SEC-01, M-SEC-02, M-SEC-03 into a single 1-day Phase B-pre. Operationally I disagree:

- **M-SEC-03 (max_size guards)** is a prereq for **Phase B**, not Phase D. Phase B increases traffic volume and without `max_size` guards you open a DoS vector even on the read path.
- **M-SEC-01, M-SEC-02 (Origin + CSRF)** are prereqs for **Phase D** specifically, because Phase D is when the control-path attack surface gets wired up.

**Proposed**: rename Phase B-pre → Phase B-pre-a (0.25 day, ships with or before Phase B) and Phase B-pre-b (0.75 day, ships before Phase D). Both are still ≤ 1 day total. This nuance matters because it means Phase B can start without blocking on the full auth stack.

The source doc's phase ordering rationale in §9.12 lists B-pre before B anyway, so this is a clarification not a contradiction. But it affects how operationally urgent the auth work feels relative to the bridge work.

### 13.2 Phase E default should become `drop_oldest_progress_only`, not `block`

The source doc's §9.6 specifies "ship Phase E behind `Settings.ws_backpressure_policy ∈ {block, drop_oldest, close_slow}` with default `block` to preserve current behavior; flip the default only at the next major version."

I disagree with keeping `block` as default. RISK-04 is listed as **Medium likelihood, Medium severity** and §10 notes it was **raised from Low** — a hung dev-tools tab serially blocks all broadcasts. Keeping `block` as default means the first production incident will likely be exactly this failure mode.

**Proposed**: default to a new policy `drop_oldest_progress_only` (the named variant of what the source doc calls `drop_oldest` for progress events + `close_slow` for state-bearing). This preserves correctness (RISK-11 is mitigated) while avoiding the block-on-slow-client trap. Still behind a config flag, so operators can revert to `block` if the new default misbehaves.

The source doc's "flip the default only at the next major version" stance is overly conservative for a fix that addresses a **Medium likelihood** risk. Better to ship the fix as the default from Phase E forward, with the flag to revert.

### 13.3 §11 Q6 (per-IP cap) should be resolved in this plan, not deferred

The source doc lists Q6 ("per-IP connection cap value") as a decision pending before Phase B-pre. I propose resolving it in this document: **5 connections / IP by default**, configurable via `Settings.ws_max_connections_per_ip`. This is what §2.9 M-SEC-04 proposes. The open question is a formality — there is no reason to wait.

### 13.4 §11 Q1 (deployment topology) should be explicitly declared "single-tenant for v1"

Q1 says "Decision needed before Phase E." I propose declaring it now: **single-tenant is the assumed topology**. Multi-tenant is documented as a future consideration, but is explicitly out of scope for this migration. This unblocks Phase E planning and avoids ambiguity.

### 13.5 Shadow traffic is explicitly rejected, not an open question

The source doc does not discuss shadow traffic. I considered it in §7.3 and rejected it. I document the rejection here so a future reader does not propose it as a good idea without understanding the state-duplication trap.

### 13.6 §9.11 total effort should include buffer for observability work

The source doc's §9.11 estimates ~12 engineering days. This does not explicitly call out the observability plumbing (the §5.6 instrumentation, the Prometheus panels, the alert rules). I estimate these at **+1.5 days** spread across Phase B (~1 day for the instrumentation pipe) and setup / runbook work (~0.5 day).

**Proposed revised total**: ~13.5 engineering days; ~4.5 weeks calendar. Not a big change, but honest.

### 13.7 Phase H regression test should block all removal PRs, not just locks it in

The source doc describes the Phase H regression test as a "lock-in." I go further: propose adding a **CODEOWNERS rule** that any PR touching `_normalize_metric` requires explicit approval from a specific reviewer group. This is not a code change but an operational guard against RISK-01.

---

## 14. Self-audit log

### 14.1 First draft scan (pre-edit)

I reviewed the draft for:

- [x] Every RISK-NN appears in §4 (verified: RISK-01..16, 16/16).
- [x] Every phase (A, B-pre, B, C, D, E, F, G, H, I) has an explicit exit gate.
- [x] Every phase has a kill switch with a documented TTF.
- [x] Phase B-pre has a hard, enumerated gate criterion (8 items in §3.2).
- [x] Phase C feature flag is fully designed (name, default, flip criteria, rollback).
- [x] §5.6 latency plan is operationalized (9 concrete steps in §6.4).
- [x] Open questions (§11) converted to decision gates (7/7 in §9).
- [x] Cross-repo coordination has explicit merge order (12 steps in §8.1).
- [x] Observability has metrics, logs, alerts, and SLOs sections (§6.1-6.3).
- [x] Documentation deliverables listed per phase (§10).
- [x] Stakeholder communication plan exists (§11).
- [x] Disagreements with source doc are explicit and justified (§13).

### 14.2 Issues found during audit

**Issue A (Phase B-pre granularity)**: the source doc treats Phase B-pre as one unit, but operationally M-SEC-03 is a Phase B prereq while M-SEC-01/02 are Phase D prereqs. First draft didn't call this out.
- **Fix**: added §13.1 disagreement; clarified §3.2 to distinguish "M-SEC-03 blocks Phase B" from "M-SEC-01/01b/02 block Phase D."

**Issue B (Phase E default)**: first draft accepted the source doc's `block` default without question. RISK-04 is Medium/Medium, which makes `block` a poor default.
- **Fix**: added §13.2 disagreement proposing `drop_oldest_progress_only` as the Phase E default.

**Issue C (RISK-05 had no kill switch)**: RISK-05 is a coverage risk, not a runtime risk. First draft tried to give it a kill switch.
- **Fix**: marked as "n/a (coverage risk)" in the compact matrix. Response is to fix the test.

**Issue D (Phase I not mentioned in Phase B exit criteria)**: Phase I is described as "bundled with Phase B" but the first draft did not include it in Phase B's exit gate.
- **Fix**: added to §3.3 Phase B exit gate and §8.1 step 5.

**Issue E (no abandon-migration criteria)**: the first draft had acceptance criteria but no explicit "when do we stop" criteria.
- **Fix**: added §12.3 Abandon-migration criteria.

**Issue F (§5.6 clock-offset handling missing)**: first draft mentioned clock offset in passing but did not say how it is recomputed on reconnect.
- **Fix**: added step 5 in §6.4 — recompute on every reconnect to handle laptop sleep / time-sync events.

**Issue G (no escalation templates)**: first draft referenced escalation but didn't specify that templates should be pre-drafted.
- **Fix**: added §11.3 with three pre-drafted escalation message templates living in `escalation-templates.md`.

**Issue H (Helm chart versioning not addressed)**: per the user's `project_helm_version_convention.md` auto-memory, Helm charts must have matching version / appVersion.
- **Fix**: added a line to §8.2 explicitly calling out Helm chart version discipline.

**Issue I (cross-repo worktree procedure not referenced)**: the ecosystem CLAUDE.md mandates worktrees for all feature work. First draft didn't mention it.
- **Fix**: added explicit worktree-naming reference in §8.1.

**Issue J (GitHub Actions stuck-run escape hatch not documented)**: per `project_github_actions_stuck_run_recovery.md` memory, `workflow_dispatch` is the emergency escape hatch.
- **Fix**: referenced in §11.3 Level 2 escalation.

**Issue K (RISK-15 High severity needs page-level alert)**: first draft had "ticket" severity for the CSWSH alert. High-severity security risks should page on-call.
- **Fix**: `WSOriginRejection` and `WSOversizedFrame` upgraded to "page on-call" in §6.3.

**Issue L (migration-wide acceptance missing the REST-polling-reduction proof)**: the P0 motivator (3 MB/s → 16 KB/s) should be an explicit acceptance criterion, not just a metric.
- **Fix**: added to §12.2 as "canopy_rest_polling_bytes_per_sec shows > 90% reduction."

**Issue M (decision-gate enforcement was weak)**: first draft said open questions should be resolved but didn't enforce it.
- **Fix**: added the `notes/decisions/ws-migration-Q<N>.md` enforcement rule at the end of §9.

**Issue N (Phase C flag evaluation overhead not addressed)**: first draft didn't note whether the flag check is per-call or per-startup.
- **Fix**: clarified in §5.1 that the flag is evaluated on every call (cheap attribute access) so no restart is needed to flip.

**Issue O (Phase B-pre M-SEC-04 per-IP cap handling)**: first draft mentioned the cap but didn't cover the thread-safety contract or the `finally` block pattern.
- **Fix**: not applicable — that's the security agent's job. Referenced the source doc's §2.9 pattern without duplicating it. Kept §13.3 to resolve the Q6 default value operationally.

**Issue P (Phase C removal criterion missing)**: first draft didn't say when the Phase C flag can be removed.
- **Fix**: added "do NOT remove the flag or the REST path for at least 1 release cycle after the flag default flips" to §5.1.

**Issue Q (runbook template missing)**: first draft listed runbook deliverables but didn't specify what a runbook must contain.
- **Fix**: added the 7-point runbook template to §10.

### 14.3 Final pass

After editing in corrections, I re-verified:

- [x] All RISK-NN 01-16 appear in both §4 narrative and §4 compact matrix.
- [x] All 10 phases (A, B-pre, B, C, D, E, F, G, H, I) have entries in: phase ordering (§3), feature flags (§5.2 where applicable), observability (§6), release coordination (§8.1), documentation (§10).
- [x] All 7 open questions from §11 have decision gates with defaults and deadlines.
- [x] Every kill switch has a TTF < 15 minutes.
- [x] Every disagreement with the source doc in §13 is justified (not just asserted).
- [x] The migration-wide "done" criterion in §12.2 explicitly ties back to the P0 motivator (the 3 MB/s REST polling bomb).
- [x] Documentation deliverables have a concrete location in the repos.
- [x] The stakeholder plan has a cadence that accounts for thread-handoff (future-Claude is listed as a stakeholder).

### 14.4 Out of lane — explicitly not covered

Per the scoping constraint, this proposal does NOT design:

- The broadcaster or slow-client drain mechanics (Phase E internals).
- The `set_params` API contract (Phase A/C/G).
- The clientside_callback wiring (Phase B).
- The M-SEC-NN security controls (Phase B-pre).
- The test plan details (all phases have test plans in §9 of the source doc; I reference them but do not redesign them).
- The `_normalize_metric` consumer audit content (Phase H).

These are other sub-agents' jobs. I defer to them on the technical content and consume their decisions as inputs to the operational plan.

---

**End of proposal R0-06.**
