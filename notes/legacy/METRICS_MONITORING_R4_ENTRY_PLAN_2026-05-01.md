# METRICS-MON Phase R4 — Entry Plan

**Date:** 2026-05-01
**Author:** Paul Calnon
**Status:** 🟡 Plan — open for review.
**Phase:** R4 (best-practice and ergonomic improvements).
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §7.
**Companion:** [`METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md`](METRICS_MONITORING_R3_ENTRY_PLAN_2026-04-30.md) (the pattern this plan follows), [`METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md`](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) §10 (the matrix R4 will not modify, but whose remaining GAP rationales pin R4.1).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. Purpose

Phase R3 closed 2026-05-01 (juniper-ml#182): every documented metric, probe, and frame is exercised by an asserting test or has an accepted-gap rationale linked to a follow-up. R3.6's coverage-matrix sweep surfaced two implementation gaps (R4.6, R4.7) that join the four pre-planned R4 sub-tracks (R4.1–R4.4) and the R3.1-surfaced R4.5, for **7 sub-tracks total**.

Phase R4 turns to **best-practice and ergonomic improvements**: items where production code works correctly under nominal load but has known failure modes under adverse conditions (R4.2's blocking probes), missing instrumentation that would degrade R5 dashboard fidelity (R4.1, R4.3, R4.4, R4.5, R4.6), or known-uncovered code paths the operator depends on (R4.7).

This plan **sequences the 7 R4 sub-tracks** into parallelizable batches, resolves seven open questions before any implementation lands, and pins the Phase R4 exit criteria. The goal is to enter R5 (SLO catalog + scrape manifests + dashboards + alerting) with **every histogram bucket boundary defensible against an SLO target, every cross-service request hop carrying a request-id, and every probe non-blocking under load** — the three preconditions R5 dashboards and alerts will rely on.

---

## 2. The 7 sub-tracks

| ID | Repo(s) | Composite | What | Cross-repo coupling | Surfaced by |
|---|---|:---:|---|---|---|
| **R4.1** | cascor + canopy + data | 2 | Per metric, document the SLO target each histogram bucket boundary serves; adjust bucket layout if no SLO maps to current buckets. (seed-14) | **3 PRs** (one per repo, schema-similar) — but bucket choices may differ per metric | Original review (seed-14) |
| **R4.2** | canopy (verify cascor + data) | 2 (3 if blocking observed in production) | Replace `urllib.request.urlopen()` in async health-probe paths with `httpx.AsyncClient`; add stress test that fires N concurrent probes against a slow upstream and asserts event-loop latency p99 within bound. (seed-10) | None (or 3 PRs if cascor / data are also affected) | Original review (seed-10) |
| **R4.3** | juniper-data-client (+ canopy hook) | 2 | Optional instrumentation hook on the data-client API surface; default no-op; canopy provides a Prometheus-emitting hook. Avoids forcing prometheus dep into a thin client. (seed-13) | **2 PRs** (data-client + canopy hook adoption) | Original review (seed-13) |
| **R4.4** | cascor-worker | 2 | Per-task timing, RSS reporting, GPU utilization (if applicable) emitted as part of the heartbeat frame from R1.3. No new endpoint; reuses heartbeat surface. | None (single-repo; cascor server already accepts the new fields per R1.3) | Original review |
| **R4.5** | juniper-data | 2 | New `juniper_data_dataset_post_total{generator, status, cache="hit"\|"miss"}` counter bumped on every POST regardless of cache state. (Recommended option (a) per roadmap §7.) | None | R3.1 implementation (2026-05-01) |
| **R4.6** | juniper-data-client | 1 | Plumb `juniper_observability.request_id_var` through `_request()`; outbound HTTP carries `X-Request-ID` when caller has one set. Recommended option (a) per roadmap §7. | None at boundary; canopy + cascor consumers gain the propagation transparently | R3.6 sweep (2026-05-01) |
| **R4.7** | cascor-worker | 1 | Single test in `tests/test_worker_agent.py::TestMessageLoopDispatch` exercising the unknown-type branch of `CascorWorkerAgent._run`; `caplog`-asserts the structured WARNING `juniper_cascor_worker_unrecognized_ws_frame` fires with expected fields. | None | R3.6 sweep (2026-05-01) |

**Total**: 7 sub-tracks, **~10 PRs** (R4.1 fans out to 3, R4.3 to 2, others single-repo).

---

## 3. Open questions and resolutions

### Q1. R4.1 — bucket-choice methodology

**Trade-off:**

- **(a) Top-down: define SLOs first, then derive buckets.** Pure approach — every boundary is defensible against an explicit SLO target. But blocks on R5.1 (SLO catalog not yet drafted), inverting the planned phase order.
- **(b) Bottom-up: document current bucket rationale based on observed latency distributions; let R5.1 ratify or reshape.** Smaller delta now; R5.1 SLO catalog can revisit if the buckets don't bracket the chosen SLO quantiles.
- **(c) Hybrid: document current rationale (b) for now, mark each bucket layout as "tentative pending R5.1" in the metric definition's HELP string, so R5.1 has a clear update target.**

**Resolution: (c).** R4.1 should not block on R5.1 entry planning, but R5.1 will need to know which buckets are "documented and stable" vs "documented but tentative." The HELP-string marker is a lightweight commitment device. R4.1 also delivers a per-metric bucket-rationale document under `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_2026-05-XX.md` (one per server) so R5.1 has a single source of truth to ratify.

### Q2. R4.2 — scope of "async-safe probes"

**Trade-off:**

- **(a) Canopy only** (where seed-10 originally identified `urllib.request.urlopen()` in the readiness probe path). Smallest scope; matches the original finding.
- **(b) All three servers** (cascor + canopy + data) — sweep the codebase for `urllib.request` and `requests.get` in any handler reachable from an async context.
- **(c) Canopy + targeted audit of cascor/data** — fix canopy as the known offender, audit the others to mark them either clean or as a separate sub-finding. R3.6's sweep style.

**Resolution: (c).** Spawn a single Explore-style audit of cascor + data observability + health code paths during R4 implementation; if either has equivalent blocking calls, fold them into R4.2 as schema-similar PRs (matching the R1.x cross-repo pattern). If both are clean, R4.2 stays canopy-only and the audit findings get a one-line note in the PR description for the record. Don't pre-commit to (b) without evidence.

### Q3. R4.3 — instrumentation hook shape

**Trade-off:**

- **(a) Single callable: `on_request(method, url, status, duration_ms, error)`** — minimal API; canopy wraps in a closure that bumps Prometheus counters.
- **(b) Multiple callbacks: `on_request_start`, `on_request_complete`, `on_request_error`** — richer; supports streaming-progress instrumentation (R4.4-style) but more API surface to maintain.
- **(c) Pluggable observer pattern** (caller supplies an object implementing a known protocol) — most flexible; most boilerplate.

**Resolution: (a).** Mirrors HTTP middleware style; a single tuple of fields is enough for the Prometheus-emit case. Future-proofing path: the callable can be replaced with a richer interface in a SemVer-major bump if the canopy hook ever needs more granularity. Don't pre-commit to (b) or (c) for hypothetical needs.

### Q4. R4.4 — heartbeat field additions vs new metric surface

**Trade-off:**

- **(a) Append fields to the R1.3 heartbeat payload** (`per_task_duration_seconds`, `rss_mb` already present, add `gpu_utilization_pct`, `last_n_task_durations`). Single network event per heartbeat tick; cascor server side already validates additive fields. Matches the R1.3 contract.
- **(b) New `/v1/worker/instrumentation` endpoint** that returns a richer payload. Separates concerns but requires a second HTTP listener on the worker side (R1.3 added `/v1/health[/live|/ready]` — adding another endpoint is ergonomic).
- **(c) Push directly to a Prometheus pushgateway** — gives Prometheus-native semantics but introduces a new dependency surface (pushgateway container) and breaks the "worker is a simple WS client" property R2 closure committed to.

**Resolution: (a).** R1.3 explicitly designed the heartbeat to be additive; cascor's `WorkerRegistration.record_heartbeat()` already accepts keyword-only arguments with `None` defaults so older worker images stay compatible. Adding 2–3 fields per heartbeat is well under the WS frame budget. Pushgateway (c) is rejected — it inverts the R2 worker-boundary decision (worker stays Pydantic-free at runtime, no observability dep beyond what the heartbeat already requires).

### Q5. R4.5 — counter shape revisited (deferred decision from §7)

**Decision deferred** to R4 entry planning per §7 R4.5 text. Two options on the table:

- **(a)** New `juniper_data_dataset_post_total{generator, status, cache="hit"|"miss"}` counter — separates request volume from generation work.
- **(b)** Cache-hit branch calls `record_access(dataset_id)` — reuses existing instrumentation but conflates POST + GET.

**Resolution: (a).** R5.1 SLO catalog will likely define separate SLIs for "POST request volume" (capacity) vs "dataset access patterns" (cache effectiveness). Conflating them under `record_access` would force R5.1 to do label arithmetic to recover the split. The new counter keeps R5.1 dashboards orthogonal. Cost is +1 metric in the data-side surface; well below R1.1's cardinality-bound budget.

### Q6. R4.6 — data-client request-id propagation activation model

**Trade-off:**

- **(a) Always-on opt-in via `juniper-observability` import** — `_request()` reads `request_id_var` at call time; if non-empty, sets `X-Request-ID`. Requires data-client to import the lib at the call boundary.
- **(b) Constructor-time enable flag** — `JuniperDataClient(propagate_request_id=True)`. Explicit opt-in per consumer.
- **(c) Always-on, no opt-in** — `_request()` unconditionally reads `request_id_var`; if not set, generates a new request-id at the client boundary.

**Resolution: (a).** Canopy and cascor already depend on `juniper-observability` via R2.1; the import is free for them. (c) is rejected because data-client could be used standalone (e.g. notebook session) where there's no caller-side request-id chain to anchor to — generating one at the client would lie about provenance. (b) is rejected because no consumer benefits from disabling propagation; the only "opt-out" we need is the absence of `request_id_var` in the calling thread, which (a) handles for free.

### Q7. R4.7 — test-only sub-track sequencing

**Question:** Is R4.7 (single test for worker unrecognized-frame log emission) blocked on anything?

**Resolution:** No. R4.7 is a pure test addition exercising existing production code (`worker.py::CascorWorkerAgent._run` already emits the structured WARNING — R2.2.6). Belongs in Wave 1 alongside R4.5, R4.6 as the smallest single-test PRs.

---

## 4. Sequencing — what gates what?

**Independent threads** (no inter-PR coupling, can land in any order):

- **R4.5** (data, +1 metric + 1 test) — production-code change, single repo.
- **R4.6** (data-client, +1 wiring + 1 test) — production-code change, single repo.
- **R4.7** (worker, +1 test only) — test-only, single repo.
- **R4.4** (worker, +heartbeat fields + cascor-server-side acceptance test) — single repo on the worker side; cascor already accepts the new fields per R1.3 design but a confirmation test on the cascor side is a small companion PR. Tagged as **R4.4** (worker) + **R4.4b** (cascor) if cascor needs an explicit field-acceptance test.

**Cross-cutting fan-out** (one PR per repo, schema-similar):

- **R4.1** — three PRs (cascor + canopy + data) each adding HELP-string bucket rationale + tentative-pending-R5.1 marker + a per-server bucket-rationale doc under `notes/observability/`.

**Coupled pair**:

- **R4.3** — two PRs: data-client adds the optional hook, then canopy adopts it. Land in dependency order: data-client first (no consumer touch), canopy second.

**Audit-gated** (scope determined during execution):

- **R4.2** — canopy + targeted audit of cascor/data per Q2 resolution. Could end up as 1, 2, or 3 PRs.

**Recommended landing order:**

1. **Wave 1 (parallel, single-repo)**: R4.5, R4.6, R4.7, R4.4. **4 PRs** at minimum (R4.4 may add a companion R4.4b on the cascor side).
2. **Wave 2 (audit + fan-out)**: R4.2 (with audit), R4.1 (3 PRs). **4–6 PRs**.
3. **Wave 3 (coupled)**: R4.3 (data-client first, then canopy adoption). **2 PRs**.
4. **Closure**: Phase R4 close note in juniper-ml roadmap §7. **1 PR**.

**Total**: ~10–13 PRs depending on R4.2 audit and R4.4 cascor companion. Estimated wall-clock at the prior cadence (~5 PRs / day): **2–3 working days end-to-end**.

---

## 5. Phase R4 exit criteria

R4 is done when **all** of the following hold:

1. **R4.1**: every histogram metric in cascor / canopy / data has a per-bucket rationale documented in HELP string + per-server `notes/observability/HISTOGRAM_BUCKETS_RATIONALE_*.md`. Buckets that have no SLO mapping are marked "tentative pending R5.1" in HELP string.
2. **R4.2**: canopy probe path is `httpx.AsyncClient`-based; cascor + data audit complete with either equivalent fix or one-line "audit clean" note. Stress test asserting event-loop p99 latency under N concurrent slow-upstream probes is in the canopy test suite (and in cascor / data if they were affected).
3. **R4.3**: data-client offers an opt-in `on_request(method, url, status, duration_ms, error)` hook (default no-op); canopy adopts it via a Prometheus-emitting closure; per-side tests cover both ends.
4. **R4.4**: cascor-worker heartbeat payload carries `per_task_duration_seconds`, `gpu_utilization_pct` (when applicable), and any other R4.4-scoped fields; cascor server accepts them; field-acceptance test on the cascor side.
5. **R4.5**: `juniper_data_dataset_post_total{generator, status, cache}` counter live; R3.1-style live integration test asserts increment-by-2 (vs generation counter increment-by-1) for two identical POSTs.
6. **R4.6**: data-client `_request()` propagates `X-Request-ID` when `juniper_observability.request_id_var` is set; unit test pins the header presence.
7. **R4.7**: `test_worker_agent.py::TestMessageLoopDispatch` covers the unknown-type branch via `caplog`-assertion on the structured WARNING.
8. **§9 status table**: every R4 row flipped to **done** with PR refs.
9. **§7 close note**: a "Phase R4 status (2026-05-XX): ✅ COMPLETE" subsection mirroring the R3 close note, with per-track outcome and any follow-ups surfaced during execution captured as new R5.x sub-tracks (or, if non-observability, opened as separate audit findings).

After R4 closes, the program turns to **Phase R5** — SLO catalog + scrape manifests + dashboards + alerting. R5 is the production-observability deliverable; its R5.1 sub-track will revisit any R4.1 buckets marked "tentative" and either ratify them or commit a re-bucketing PR.

---

## 6. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|:---:|---|
| R4.1 audit reveals a metric whose buckets fundamentally don't bracket any plausible SLO quantile (e.g. logarithmic spread is wrong for the latency distribution) | Medium | The HELP-string "tentative" marker (Q1 resolution) gives R5.1 explicit license to re-bucket without a SemVer-major beat. Re-bucketing is a metric-version event but not a public-API break. |
| R4.2 audit finds blocking probes in cascor / data that R3 missed because the test paths didn't exercise blocking-vs-non-blocking distinction | Medium | Audit is scoped narrowly (Q2 resolution); if found, fold into R4.2 as schema-similar PRs and tag the original review's seed-10 as cross-repo (it was scoped canopy-only). |
| R4.3 data-client hook API gets locked in before a real consumer (cascor) needs richer instrumentation, forcing a SemVer-major break | Low–Medium | Q3 resolution recommends single-callable shape; SemVer-major path is documented. Cascor's data-client usage is already well-understood — no surprise consumer is likely. |
| R4.4 worker heartbeat additions push frame size past the cascor server's WS budget | Low | R1.3 design pinned the heartbeat at `worker_id + timestamp + R1.3 fields ≪ 1 KB`; adding 3–4 numeric fields is noise. Pre-commit a quick frame-size assertion in the worker test. |
| R4.5 new counter trips a cardinality alert if `cache="hit"|"miss"` is mis-typed (e.g. typo creates a `cache="miss "` bucket) | Low | The label is closed-set with two values; pin via a constants module + a unit test that constructs the counter with both values and asserts no extras. |
| R4.6 outbound `X-Request-ID` propagation breaks an existing juniper-data middleware that assumes it generates the request-id (would shadow caller-supplied IDs) | Low | `juniper-observability`'s `RequestIdMiddleware` already prefers a caller-supplied `X-Request-ID` header over a generated one (R2.1 design). The propagation just makes the existing preference path the dominant case. Pre-commit a smoke test on the canopy → data-client → data chain to assert end-to-end request-id propagation. |
| R4.7 test exercises a code path that is actually dead (worker never sees unknown types because the protocol pin in R2.2.6 prevents server drift) | Low | The structured WARNING was added defensively against a future server-side regression that escapes `test_protocol_alignment.py:102`. The test is a regression guard for that future. Acceptable cost — single test. |

---

## 7. Out of scope for R4

- **Cardinality-bounded labels in new metrics added by R4** — already handled by R1.1's UNMATCHED_ENDPOINT_LABEL pattern; new metrics inherit the discipline.
- **Worker training-loop algorithmic instrumentation** (e.g. correlation gradient norms, candidate diversity stats). Belongs to a separate "training-quality observability" track, not metrics-mon.
- **R5.1 SLO catalog drafting** — that's R5's own entry plan. R4.1 only commits to "documented bucket rationale, SLO target marked tentative or final."
- **Pushgateway adoption** — explicitly rejected in Q4.
- **Sentry coverage for client/worker libraries** — accepted as gap in R3.6 §10 sweep.

---

## 8. Cross-track dependencies surfaced by R4 entry planning

None new. R4's sub-tracks are well-isolated:

- R4.1 + R5.1 have a feedback loop documented in Q1 resolution (HELP-string marker is the handoff).
- R4.3 data-client + canopy adoption is an explicit dependency captured in §4 sequencing.
- R4.6 propagation is transparent for canopy + cascor consumers (they get it for free once data-client ships).

The R3 entry plan's discovery that R3.4 collapsed to documentation-only on first investigation is unlikely to repeat here — every R4 sub-track is a real implementation change with concrete code to write.

---

## Appendix A — PR-count reconciliation

| Wave | Sub-track | PRs |
|---|---|---|
| 1 | R4.4 (worker) | 1 |
| 1 | R4.4b (cascor field-acceptance test) | 0–1 |
| 1 | R4.5 (data) | 1 |
| 1 | R4.6 (data-client) | 1 |
| 1 | R4.7 (cascor-worker test) | 1 |
| 2 | R4.1 (cascor) | 1 |
| 2 | R4.1 (canopy) | 1 |
| 2 | R4.1 (data) | 1 |
| 2 | R4.2 (canopy) | 1 |
| 2 | R4.2 (cascor / data) | 0–2 |
| 3 | R4.3 (data-client) | 1 |
| 3 | R4.3 (canopy adoption) | 1 |
| 4 | Phase R4 close note | 1 |

**Range**: 11 PRs (no audit findings, no R4.4b) to 14 PRs (R4.2 audit hits both cascor + data, R4.4b needed).
