# METRICS-MON Phase R3 — Entry Plan

**Date:** 2026-04-30
**Author:** Paul Calnon
**Status:** 🟡 Plan — open for review.
**Phase:** R3 (test-coverage and correctness gap closure).
**Roadmap:** [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §6.
**Companion:** [`METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md`](METRICS_MONITORING_R2.1_SHARED_OBSERVABILITY_DESIGN_2026-04-28.md), [`METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md`](METRICS_MONITORING_R2.2_WS_FRAME_SCHEMA_DESIGN_2026-04-29.md) (these patterns).

---


> **STATUS 2026-05-05: COMPLETED — archived to `notes/legacy/`.** The METRICS-MON observability program closed 2026-05-03 (program-close note: `METRICS_MONITORING_PROGRAM_CLOSE_2026-05-03.md`, juniper-ml#192). All in-flight items this doc tracks are terminal (shipped, deferred-with-link, or formally cancelled). Residual follow-ups from program close are tracked in `notes/POST_METRICS_MON_TRACKER_2026-05-05.md` (parallel PR). This doc is preserved for historical reference; do not edit.

---

## 1. Purpose

Phase R2 closed 2026-04-30 (juniper-ml#175): three Juniper servers share `juniper-observability`, the WS protocol surface is single-sourced via `juniper-cascor-protocol`, probe topology is a documented DAG, and worker stays Pydantic-free at runtime. Phase R3 turns to **test-coverage gap closure**: enumerated holes in the existing observability test surface that the R2 implementation itself surfaced, plus a few standing gaps inherited from the original review (seeds 07–12).

This plan **sequences the 7 R3 sub-tracks** into parallelizable batches, resolves five open questions before any implementation lands, and pins the Phase R3 exit criteria. The goal is to enter R5 (SLO/scrape/dashboards) with **zero unjustified coverage gaps** and confidence that every documented metric, probe, and frame is exercised by an asserting test.

---

## 2. The 7 sub-tracks

| ID | Repo(s) | Composite | What | Cross-repo coupling |
|---|---|:---:|---|---|
| **R3.1** | juniper-data | 3 | Live integration test: POST `/v1/datasets`, scrape `/metrics`, assert `juniper_data_dataset_generations_total{generator,status="success"}` ↑1 + duration histogram observed exactly 1 sample. (seed-08, BUG-JD-07) | None |
| **R3.2** | juniper-canopy | 2 | Integration test toggling demo mode; assert `juniper_canopy_demo_mode_active` reflects within one update tick. (seed-11) | None |
| **R3.3** | juniper-canopy | 2 | Restore the skipped `_create_metrics_panel` test — pick approach (a) public surface OR (b) black-box endpoint. (seed-12) | None |
| **R3.4** | cascor + canopy + data | 2 | Make `sentry-sdk` a hard dev/test dep; remove `importorskip` so the SEC-15 / SEC-10 hook tests run on every CI run. (seed-09) | **3 PRs** (one per repo, schema-identical) |
| **R3.5** | juniper-cascor | 2 | Replay-buffer overflow test: drive `_PROJECT_API_METRICS_BUFFER_SIZE + 1` updates; assert oldest evicted, newest retained, no exception. (seed-07) | None |
| **R3.6** | All repos | — | Coverage-matrix gap closure: populate `METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md` §10 (currently a template) and either close every `GAP` cell or document an accepted-gap rationale. | **Multi-repo sweep** |
| **R3.7** | cascor + worker + data + canopy | 3 | Add `runs-on: macos-*` leg to each repo's `ci.yml` so cross-platform `rss_mb` sampling and POSIX-assumption coverage actually exercises macOS. (Surfaced 2026-04-27 by R1.3 design review.) | **4 PRs** (one per repo) |

**Total**: 7 sub-tracks, ~13 PRs (counting cross-cutting items as one-per-repo).

---

## 3. Open questions and resolutions

### Q1. macOS CI matrix — runner kind and test scope (R3.7)

**Trade-off:**

- **`macos-latest`** (default = ARM/Apple Silicon since 2024). Faster, cheaper, matches modern dev machines. But torch wheels for ARM macOS may differ from the worker's actual deployment surface (Linux x86_64 in Kubernetes).
- **`macos-13`** (Intel). Slower per minute, deprecated, but matches the pre-2024 CI baseline.

**Test scope:**

- **All unit + integration tests on macOS**: maximises coverage but adds ~5 minutes per CI run × 4 repos × every PR.
- **Only the platform-dependent tests on macOS**: scoped to `rss_mb` sampling, POSIX-only assumptions, and any test marked `@pytest.mark.platform_sensitive`. Saves CI minutes; smaller blast radius.

**Resolution:**

- **Runner: `macos-latest`** (ARM). The Linux runners cover Linux x86_64; macOS leg is for **POSIX-platform-divergence coverage**, not Linux fidelity. Apple Silicon is also the dominant macOS dev surface today.
- **Scope: all unit tests** (no integration / performance / e2e on macOS). Reasoning: the gap R3.7 closes is "we have zero macOS coverage". The right cure is broad unit coverage, not narrow targeted coverage that future contributors won't think to extend. CI cost is bounded by parallel matrix legs and reasonable for the security/correctness payoff.
- **Failure budget**: macOS leg starts in `continue-on-error: true` mode for the first **2 weeks** so we can identify environment-specific test failures without blocking PRs. After 2 weeks, flip to required.

### Q2. R3.3 — skipped `_create_metrics_panel` test approach

**Options:**

- **(a) Expose `_create_metrics_panel` on a public surface** and unskip the test. Adds public API surface that's pure presentation glue.
- **(b) Replace with a black-box test** against the dashboard layout endpoint that exercises the same code path. Doesn't grow public API; tests through the actual integration seam.

**Resolution: (b) — black-box.** The skip note says "not exposed as public API"; growing the public API just to test it inverts the API/test relationship. A black-box test against the layout endpoint exercises the same render path with stronger guarantees (it'll catch a regression in any of `_create_metrics_panel`'s callers, not just the function itself). The implementation note in seed-12 already lists this as the preferred path.

### Q3. R3.4 — Sentry: hard dep in test extras OR runtime?

**Status quo**: every server lists `sentry-sdk` as a runtime dep but the SEC-10 / SEC-15 `before_send` hook tests are gated by `importorskip("sentry_sdk")`. Result: the hook tests silently skip when an operator strips the optional Sentry install.

**Options:**

- **(a) Move `sentry-sdk` from runtime deps into a `[sentry]` extra** and have the hook tests skip when the extra is absent.
- **(b) Make `sentry-sdk` a hard runtime dep** (already true today for cascor/canopy/data) AND a hard dev-dep so test installs always include it. Drop the `importorskip` guard.

**Resolution: (b).** All three servers already list `sentry-sdk` in `dependencies = [...]`; the `importorskip` in tests is paranoia from before the hard pin landed. Removing it means the SEC-15 `before_send` regression tests run **every CI run**, which is exactly what seed-09 asks for. No production-time API change — the runtime dep was already there.

### Q4. R3.6 — coverage matrix execution shape

The review plan §10 has a **template** matrix (12 rows × 6 columns of `(empty)` cells) that was never populated. R3.6's literal text is "for every cell marked GAP, either close with a test or document an accepted-gap rationale". But there are no GAP cells today — there are only empty cells.

**Options:**

- **(a) Treat empty cells as implicit GAPs.** Walk every cell, audit current coverage, flip to either a test ref or `GAP`, then close.
- **(b) Pre-populate the matrix in a single audit pass** (R3.6.1), then close the resulting GAPs in a second pass (R3.6.2). Two-step.
- **(c) Roll the audit into individual sub-track PRs** (R3.1 closes the "Dataset-gen metric live integration" cell; R3.2 closes "Demo-mode gauge drift"; etc.). Each consumer-side PR also fills in its own row. R3.6 becomes the residual sweep.

**Resolution: (c) + lightweight (b).**

- Each R3.1–R3.5 PR includes a small change to the review-plan §10 matrix marking its row populated with the test reference (file:line) it ships.
- After R3.1–R3.5 land, a **single residual-audit PR (R3.6)** walks the still-empty cells, decides for each: ship a test (preferred), or write a one-line accepted-gap rationale linked to the seed finding that documents why coverage isn't worth it for that cell.
- R3.7 (macOS CI) is **not** a row in the matrix — it's a CI matrix concern, not a behavior assertion. No matrix update.

This avoids a giant standalone audit PR and keeps each implementation PR responsible for the cell it just closed.

### Q5. Sequencing — what gates what?

**Independent threads** (no inter-PR coupling, can land in any order):
- R3.1 (data) | R3.2 (canopy) | R3.5 (cascor) — pure single-repo PRs adding one test each.
- R3.3 (canopy) — single-repo PR, unrelated to R3.2 even though same repo.

**Cross-cutting fan-out** (one PR per repo, schema-identical):
- R3.4 — three small PRs (cascor, canopy, data) each removing `importorskip` and asserting Sentry-hook behavior unconditionally.
- R3.7 — four small PRs (cascor, worker, data, canopy) each adding `macos-latest` matrix leg with `continue-on-error: true` initial guard.

**Closure** (gated on the above):
- R3.6 — single juniper-ml PR (the matrix lives in the review plan, which lives in juniper-ml). Walks the still-empty cells after the per-track PRs have populated their own rows; ships any residual tests or accepted-gap rationales.

**Recommended landing order:**

1. **Wave 1 (parallel)**: R3.1, R3.2, R3.3, R3.5, R3.4×3, R3.7×4. **11 PRs, no inter-PR coupling**, can be authored simultaneously and merged as reviews complete.
2. **Wave 2 (gated on Wave 1)**: R3.6 — residual coverage-matrix sweep + Phase R3 roadmap-close PR in juniper-ml. **1 or 2 PRs**.

**Total**: ~12–13 PRs. Estimated wall-clock time at the prior cadence (~5 PRs/day): **3 working days** end-to-end.

---

## 4. Phase R3 exit criteria

R3 is done when **all** of the following hold:

1. **R3.1–R3.5** have shipped per-track PRs (one each, except R3.4 fans out to 3 repos).
2. **R3.7** has shipped 4 PRs adding `macos-latest` legs to cascor / worker / data / canopy CI; macOS legs are passing reliably for ≥ 2 weeks before being made `required`.
3. **R3.6** matrix audit is complete: every row × column cell either has a test reference or an explicit accepted-gap rationale referencing the relevant seed finding.
4. **No tests skipped without justification**: `importorskip` removed for `sentry_sdk`; any remaining `@pytest.mark.skip` has a documented rationale in the test file.
5. **Roadmap §9 R3 rows** are all flipped to `done`; the closing juniper-ml PR adds a "Phase R3 status: complete" subsection to §6.

After R3 closes, the program turns to **Phase R4** (best-practice / instrumentation, 4 sub-tracks). **Phase R5** (SLO catalog + scrape manifests + dashboards + alerting) remains gated on R3 — it is the production-observability deliverable and gating it on coverage closure is the stated R5 entry condition.

---

## 5. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|:---:|---|
| macOS CI flakes uncover real bugs that block Wave 1 PRs from merging | Medium | `continue-on-error: true` initial guard; flip to required after 2-week soak. Track flakes per-repo in a follow-up issue. |
| Coverage-matrix sweep (R3.6) discovers a gap that requires a non-trivial test (e.g. WS replay buffer end-to-end) | Medium | Allow R3.6 to spawn child sub-tracks (R3.6.x) for any GAP requiring > 50 LOC; don't block phase exit on those. |
| Sentry hard-dep change (R3.4) breaks an unrelated CI matrix that didn't have `sentry-sdk` installed | Low | All three servers already list `sentry-sdk` in `dependencies`; only test installs change. Verified by running each repo's CI on the PR branch before merge. |
| Replay-buffer overflow test (R3.5) flakes due to non-deterministic WS sequencing | Low | Drive the buffer via direct API calls to `WebSocketManager`, not real WS connections. Same pattern as existing replay-buffer unit tests. |
| `_create_metrics_panel` black-box test (R3.3) coupling to UI rendering means it fails on every UI tweak | Medium | Test against the layout endpoint's JSON response shape, not rendered HTML. UI tweaks that don't change the layout schema don't break the test. |
| R3 phase exit gated on macOS 2-week soak — extends timeline beyond the rest of R3 | Low | The soak doesn't gate R3.6 / R3.4 / individual sub-track merges; only R3.7 itself. R3 phase can be declared complete with R3.7 in "soaking" status. |

---

## 6. Definition of Done — per-PR checklist

Every R3 PR must include:

- [ ] **The asserting test** (the seed finding's named regression)
- [ ] **Coverage-matrix update** (one-line edit to §10 of the review plan flipping the relevant cell to its test ref) — except R3.4, R3.7 which don't map to a single matrix row
- [ ] **CHANGELOG entry** under `[Unreleased]` "Added" or "Changed" as appropriate
- [ ] **Pre-commit clean** (Black, isort, Flake8, MyPy, Bandit on all changed files)
- [ ] **Local verification** (test passes against the current `main` of the relevant repo with `juniper-cascor-protocol==0.1.0` and `juniper-observability==0.1.1` from PyPI installed)

---

## 7. Implementation sequence (PR list)

| # | Repo | Branch | Sub-track | What | Status |
|---|---|---|---|---|---|
| 1 | juniper-data | `metrics-mon-r3-1-dataset-gen-live-test` | R3.1 | Live `/v1/datasets` → `/metrics` integration test | not started |
| 2 | juniper-canopy | `metrics-mon-r3-2-demo-mode-gauge-test` | R3.2 | Demo-mode gauge integration test | not started |
| 3 | juniper-canopy | `metrics-mon-r3-3-metrics-panel-blackbox` | R3.3 | Black-box metrics panel test (replaces skip) | not started |
| 4 | juniper-cascor | `metrics-mon-r3-4-sentry-unconditional` | R3.4 | Remove `importorskip("sentry_sdk")` | not started |
| 5 | juniper-canopy | `metrics-mon-r3-4-sentry-unconditional` | R3.4 | Same | not started |
| 6 | juniper-data | `metrics-mon-r3-4-sentry-unconditional` | R3.4 | Same | not started |
| 7 | juniper-cascor | `metrics-mon-r3-5-replay-buffer-overflow` | R3.5 | Replay-buffer overflow regression test | not started |
| 8 | juniper-cascor | `metrics-mon-r3-7-macos-ci` | R3.7 | Add `macos-latest` matrix leg | not started |
| 9 | juniper-cascor-worker | `metrics-mon-r3-7-macos-ci` | R3.7 | Same | not started |
| 10 | juniper-data | `metrics-mon-r3-7-macos-ci` | R3.7 | Same | not started |
| 11 | juniper-canopy | `metrics-mon-r3-7-macos-ci` | R3.7 | Same | not started |
| 12 | juniper-ml | `metrics-mon-r3-6-coverage-matrix-sweep` | R3.6 | Populate review plan §10; close residual gaps | gated on 1–11 |
| 13 | juniper-ml | `metrics-mon-r3-roadmap-done` | — | Roadmap §9 close-out | gated on 12 |

---

## 8. References

- Roadmap: [`METRICS_MONITORING_ROADMAP_2026-04-25.md`](METRICS_MONITORING_ROADMAP_2026-04-25.md) §6 (R3 narrative), §9 (status tracker rows R3.1–R3.7).
- Review plan: [`METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md`](METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md) §9 (seed findings 07–12), §10 (coverage matrix template).
- Phase R2 closure: [juniper-ml#175](https://github.com/pcalnon/juniper-ml/pull/175).
- Phase R1.3 (where R3.7 was surfaced): [`METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md`](METRICS_MONITORING_R1.3_WORKER_HEARTBEAT_DESIGN_2026-04-27.md).
