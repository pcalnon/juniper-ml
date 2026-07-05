# Juniper Platform & Environment — State Reconciliation and Forward Roadmap

**Project**: Juniper ML Research Platform — platform/packaging/model-template environment
**Repository**: pcalnon/juniper-ml (this document); reconciles state across juniper-ml, juniper-cascor, juniper-cascor-worker, juniper-canopy, juniper-data, juniper-data-client, juniper-deploy, juniper-recurrence
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0 (reconciliation + roadmap; multi-agent validated — Rounds 1–2 in §10; §9 decisions pending Paul)
**Last Updated**: 2026-06-17

---

> **⟢ VERIFIED 2026-06-21.** The §3/§4 per-item status cells below are point-in-time 2026-06-17 snapshots.
> Current reality (reconciled): WS-6 B-phase shipped (cascor #345–#347); WS-5 A0 + 3-D viz shipped (canopy
> #372/#374–#379); OUT-11 service-core T2 merged with 0.2.0 publish pending (ml #502); model-core 0.3.0,
> recurrence-model 0.1.4, juniper-data 0.8.0. Authoritative: `JUNIPER_2026-06-21_JUNIPER-ECOSYSTEM_DOCS-REALITY-AUDIT.md`.

> **What this document is.** A single, evidence-grounded reconciliation of three ratified platform efforts — the [package-placement / relocation plan](JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md), the [build-provenance design](JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md), and the [model/middleware refactor](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md) — against the **actual current source, PyPI, and GitHub state (verified live 2026-06-17)**, followed by a prioritized design/development/testing roadmap for the genuinely-outstanding work. It exists because the three anchor plans' own status headers materially **understate** what has shipped: two are effectively complete and the third is deep in execution. This document re-baselines reality and charts the remaining tail, with multiple approach options (strengths / weaknesses / risks / guardrails) for each open decision.
>
> **Scope (ratified with Paul, 2026-06-17): "Platform + template cluster."** The three anchors plus their tightly-coupled enablers/consumers — `juniper-model-core` (incl. the new cross-validation layer), `juniper-service-core`, the recurrence app build (WS-4/WS-4b), canopy generalization (WS-5), cascor cutover (WS-6), deploy/extras (WS-7/WS-8), and provenance completion. **Out of scope:** the recurrence *model-architecture* research track (OQ-4 P-series, LMU/SSM/ESN/NEAT, Δt theory — treated here as settled input that feeds WS-4/WS-4b), the canopy UI-regression harness, and the broader V7 ~300-item backlog.
>
> **Validation depth (ratified): reconcile + risk spot-check.** Every effort's done/partial/outstanding state is established against source; the highest-risk shipped pieces were adversarially spot-checked; defects are surfaced as roadmap items, not fixed here.

---

## Table of contents

- **§0** — How this was produced (method, evidence standard)
- **§1** — Executive summary
- **§2** — The reconciliation headline: docs vs. reality
- **§3** — Current-state reconciliation, per effort (verified)
- **§4** — Outstanding-work inventory (the true tail)
- **§5** — Design / development approach options (per open decision)
- **§6** — Prioritization, ordering, grouping (the roadmap)
- **§7** — Consolidated risk register & guardrails
- **§8** — Testing roadmap for the outstanding work
- **§9** — Open questions / decisions that need Paul
- **§10** — Validation record (multi-agent)
- **Appendix A** — PR / commit ledger (evidence)
- **Appendix B** — Source documents & provenance

---

## §0. How this was produced

Method mirrors the ecosystem's verification discipline (the same adversarial, multi-agent, ground-truth-first posture the anchor docs themselves used):

1. **Reconnaissance** — the three anchor docs were read in full; the related-doc cluster (code-org strategy, cascor-core migration, model-core interface + cross-val, the WS-4/WS-4b build plans, the recurrence detailed design) was inventoried; the sibling repos and PyPI were spot-checked live.
2. **Validation fan-out** — five independent read-only sub-agents each owned one effort-cluster and reconciled it against **live source / PyPI JSON / `gh` / `git`**, under strict anti-hallucination rules: one verdict per claim from {CONFIRMED, DRIFTED, REFUTED, CANNOT-VERIFY}, primary evidence (`file:line` or command output) mandatory, doc restatements untrusted. Where cheap, agents *ran* the relevant test suites (the model-core conformance kit: 66 passed; the recurrence model conformance: 10/10; the compose-provenance regression test: 3/3).
3. **Synthesis** — this document.
4. **Adversarial validation** — independent sub-agents re-checked the load-bearing claims of this document against source (§10).

**Evidence standard.** Every "shipped / complete" verdict in §2–§3 traces to a merged PR number + a file/PyPI/issue check performed on 2026-06-17. "Doc claims X" is always distinguished from "source shows Y."

**Relationship to concurrent roadmaps.** Heavy concurrent-session activity is in flight. Two sibling roadmaps were produced the same day at a *different altitude* and are **not yet on this branch** (named here, not linked, to avoid a dangling reference): `JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md` (recurrence model/app-specific — deeper WS-4/WS-4b recovery + the model-core 0.2.0 crossval chokepoint) and `JUNIPER_2026-06-17_JUNIPER-CANOPY_REGRESSION-REMEDIATION-ROADMAP.md` (the canopy UI-regression track, which this document keeps out of scope). **This document is the platform / template-cluster view** spanning all three anchor efforts; where they overlap (WS-4b recovery, the crossval layer) the findings agree. Cross-link the three once they all land on `main`.

---

## §1. Executive summary

> **STATUS UPDATE — 2026-06-18 (reconciliation; supersedes the §1/§3/§4 status below where noted).**
> The tail advanced substantially the day after this doc was written. Verified against live PyPI releases, GitHub PRs, and repo trees:
>
> - **OUT-1 WS-4b stacked-merge — ✅ RESOLVED.** The recurrence app tree is on `origin/main`; **`juniper-recurrence` 0.1.0 is live on PyPI**. The "Priority-0 defect" in item 3 below no longer applies.
> - **OUT-3 data-client release — ✅ DONE.** **`juniper-data-client` 0.4.2** published, carrying `validate_npz_contract` (item 4b cleared).
> - **OUT-10 cross-validation layer — ✅ BUILT & PUBLISHED.** **`juniper-model-core` 0.2.0** (crossval / fold-executor) is live and the juniper-ml `[tools]` pin admits it. Crossval-API doc/polish PRs (#449, #450) are in flight in a parallel session (item 4c cleared).
> - **OUT-12 golden/snapshot gate — ✅ DONE.** Shipped to `juniper-cascor` (PR #340, merged) and **promoted to a required status check**. The first half of the WS-6 trigger-gate is armed.
> - **OUT-4 recurrence app — 🟡 PARTIAL.** Published, but **no Dockerfile exists yet** — Wave-B deploy (OUT-5) is blocked on writing it first.
> - **OUT-13 conformance wiring — ✅ DONE.** Shipped to `juniper-cascor` (PR #341, merged 2026-06-18) and **promoted to a required status check** (`model-core Conformance`). Test-only `CascorModelCoreAdapter(GrowableModel)`; no production change. **Both halves of the WS-6 trigger-gate are now armed.**
>
> **Net:** Wave A is closed and Wave D's cross-val is shipped. The live tail is **Wave B (OUT-4 Dockerfile → OUT-5/6), Wave C (client → canopy), Wave D (OUT-11 T2 surface), and Wave E (OUT-13 → WS-6)**. The §6.2 wave ordering still holds — only the completed rungs change. The per-§3/§4 status cells below are point-in-time (2026-06-17); the WS-5/WS-6 and OUT-12/13 cells were reconciled to merged reality on 2026-06-19 (see [`JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md`](JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md)); other cells remain point-in-time.

1. **Two of the three anchor efforts are done; the third is ~70% done.** Package placement and build provenance are **shipped and (provenance) live-verified**. The model/middleware refactor has shipped WS-0 through WS-4 (data foundation, both shared packages, and the first recurrence model) — all published to PyPI — and stalls at the recurrence **application** layer and its consumers.

2. **The anchor docs' status headers are stale.** All three still read as pre/partial-execution; the refactor's Status Tracker lists WS-1…WS-5 as `PLANNED` when WS-1–WS-4 have shipped. A reader trusting the headers would badly mis-sequence. Re-baselining is the first job of this document (§2).

3. **There is exactly one active defect on the critical path: a broken stacked-merge in `juniper-recurrence`.** PR#6 (app skeleton) is on `origin/main`, but PR#7 (routes/data/state/events/schemas) and PR#8 (publish workflow) were merged into *stale stacked bases* and never propagated to `main`. The app therefore serves health-only and is unpublished (PyPI 404). **This blocks the recurrence app's publish, the deploy integration, and the canopy backend.** Fixing it is Priority 0 (§5.1).

4. **The remaining tail is small and well-bounded:** (a) reconcile the WS-4b branches; (b) release `juniper-data-client` carrying `validate_npz_contract` (committed, unreleased); (c) build the ratified model-core **cross-validation layer** (design-only today); (d) create the missing **`juniper-recurrence-client`**; (e) WS-5 canopy generalization; (f) WS-7 deploy/extras + on-host launcher; (g) WS-6 cascor cutover (gated, last, and reversible); (h) build out the `juniper-service-core` **T2 surface** (websocket/worker/routes), which is designed-not-built.

5. **Nothing is broken in the production stacks.** cascor is correctly *untouched* (WS-6 deferred), service-core has a clean cascor-free dependency graph, and the both-stacks-green migration ladder (refactor Part 8) remains valid. The risk is concentrated in *new* code, not regressions to shipped systems.

6. **Recommended path: "Unblock-and-ship the first model end-to-end" (§6, Strategy S1)** — fix the merge, publish the recurrence app, wire it into deploy, then add the client + canopy UI, then deepen capability (cross-val, service-core T2), and do the production-cascor cutover **last** behind its golden-suite gate and kill-criterion. This optimizes for the refactor's actual purpose: *proving the model-addition template by getting one new model fully deployed.*

---

## §2. The reconciliation headline: docs vs. reality

| Effort | Anchor doc's stated status | Verified reality (2026-06-17) | Net |
|--------|----------------------------|-------------------------------|-----|
| **Package placement / cascor-core relocation** | "Decisions ratified; execution is a separate step" (reads pre-execution); §4 row 6 "404 — NOT published" | Relocation **+ rename executed**; `juniper-cascor/juniper-cascor-model/` published **0.1.0** on PyPI; worker repinned; CW-05 stopgap removed; issues #319/#97 closed | ✅ **COMPLETE** (Wave-2 self-adoption deferred by design) |
| **Build provenance** | "0.1.0 DRAFT — pre-implementation; PRs to open after design review" | Shipped across **all 6 repos**; observability **0.4.0** on PyPI; `make doctor` live; **Maximal** scope delivered; live-verified all-FRESH | ✅ **COMPLETE** (OQ-4 CI lane declined by Paul) |
| **Model/middleware refactor** | Status Tracker: WS-1…WS-5 `PLANNED`, WS-0 `SHIPPED` | WS-0 ratified; **WS-1/WS-2/WS-3/WS-4 shipped & published**; WS-4b **broken-merge**; WS-5/6/7/8 not started (6/8 correctly deferred); cross-val layer **design-only** | 🟡 **~70% — tail at the app/consumer layer** |

**Doc-staleness is itself a finding (and a roadmap item — §6 Wave F).** The following are factually behind reality:

- `JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md` — §6/§7 read as pending; §4 says cascor-model unpublished (it is on PyPI 0.1.0).
- `JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md` — header still "pre-implementation"; Part 4 (runtime-only `ARG`) contradicts Part 5.2 ("builder top + runtime re-declare") — implementers correctly followed Part 4.
- `JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` — Status Tracker stale (WS-1–WS-4 shipped); §8.3 calls the conformance kit a "pytest plugin" but it shipped as an importable subclass-base + `[conformance]` extra.
- `juniper-recurrence/README.md` — "Pre-implementation scaffold… WS-0 not yet ratified; no code deployed" (WS-0 ratified 2026-06-14; app skeleton is on `origin/main`).

These do not change any decision below; they are accuracy fixes recommended as a low-risk docs pass (not applied here, to keep this document investigatory and avoid colliding with concurrent sessions).

---

## §3. Current-state reconciliation, per effort (verified)

Condensed from the five validation passes. Full evidence in Appendix A.

### §3.1 Package placement / `juniper-cascor-core` relocation — ✅ COMPLETE

The entire §7 critical-path chain shipped (ml#410, cascor#328, worker#102, deploy#115; plan doc ml#398). D1–D5 are implemented in source:

| Decision | Outcome verified |
|----------|------------------|
| D1 — home | `juniper-cascor/juniper-cascor-model/` subdir (mirrors the `juniper-cascor-protocol` precedent) |
| D2 — rename | `[project].name = "juniper-cascor-model"`; import dir `juniper_cascor_model/`; tag `juniper-cascor-model-v*`; **PyPI 0.1.0 live**; `juniper-cascor-core` still 404 |
| D3 — drift-guard | co-located as `juniper-cascor/juniper-cascor-model/tests/test_drift.py`; runs in `ci-cascor-model.yml`; not double-gated |
| Worker adoption | pins `juniper-cascor-model>=0.1.0`; both lockfiles regenerated; gap fixes (`ACTIVATION_MAP`, float/int coercion, `JUNIPER_CASCOR_LOG_DIR`) present; **worker `main` green** |
| Stopgap / issues | `docker-compose.cw05-stopgap.yml` removed (deploy#115); cascor#319 + worker#97 closed 2026-06-14 |

**Benign drifts (not defects):** `--cascor-path` retained as a *legacy fallback* (primary path needs no flag); the LFS logo asset was **de-LFS'd** (43 KB plain file; excluded from the package anyway). **Risk spot-check:** `import juniper_cascor_model` → `0.1.0` clean; no actionable `cascor-core` residue in juniper-ml (only historical `notes/`/`prompts/` + two benign comments).

**Tail (deferred by design):** Wave 2 — cascor itself adopts the package and deletes its inline `candidate_unit/`/`utils/`/`log_config/`/`cascor_constants/` copies (retiring the drift-guard), and backports the `gap #3` deployment-agnostic logger (currently an allow-listed `_INTENTIONAL_DIVERGENCE`). Trigger: drift-guard friction or a `candidate_unit` change needing both copies. Off the critical path.

> ⚠️ **Process note (memory-corroborated):** worker#101's squash captured only its first commit, leaving `main` red; fixed by worker#102. Textbook "GitHub squash-and-merge ships first commit only." The same hazard class recurs in WS-4b (§3.3 / §5.1).

### §3.2 Build provenance — ✅ COMPLETE & live-verified

Maximal scope delivered across all 6 repos (obs#414, data#180/#185, cascor#333/#339, canopy#360/#362, worker#103, deploy#118/#119/#122):

- **observability 0.4.0** (PyPI): `set_build_info(ns, ver, *, git_sha=None, build_date=None)` keyword-only passthrough; `ReadinessResponse` gains optional `git_sha`/`build_date`; back-compat unit tests present. Consumers pin `>=0.4.0`; locks regenerated.
- **data / cascor / canopy**: a `provenance.py` accessor each; `git_sha`/`build_date` in the hand-built `/v1/health`; passed into `set_build_info(...)`; OQ-1 hardcoded-version → `importlib.metadata` migration done.
- **worker**: provenance in the hand-rolled `/v1/health`; OQ-5 `__version__` 0.3.0→0.4.0 fixed.
- **deploy**: all **7 service** compose build blocks carry `GIT_SHA`+`BUILD_DATE`+`APP_VERSION` (the 8th `build:` block, `test-runner`/`Dockerfile.test`, carries none by design); the Makefile builds **per-service with that repo's SHA** (R2 mislabel risk avoided, guarded by `test_no_build_block_uses_a_global_git_sha`); `scripts/doctor.sh` exists; `health_check.sh` gained GIT_SHA/DRIFT columns; the compose-provenance regression test enumerates exactly those 7 service blocks and passes 3/3; OQ-2 `-dirty` suffix shipped (deploy#122).

**Intentional, superior drifts:** `ARG` declared in the runtime stage only (the functionally-correct reading of the doc's self-contradiction); `doctor.sh` compares the **image OCI `revision` label via `docker inspect`** vs source HEAD (more robust than the doc's "GET /v1/health.git_sha"). **OQ-4** (automated drift CI lane) was **declined by Paul** — on-demand `make doctor`/`make health` deemed sufficient; this is a deliberate scope cut, the only unshipped design element.

**Tail (operational, not a design gap):** the **on-host** `juniper-deploy` checkout is ~2 commits behind `origin/main` (`provenance_sha.sh` + `-dirty` logic merged but not pulled) — same on-host bit-rot class already tracked; needs `git pull --ff-only`. **Cross-effort note:** a fastapi 0.137.0 `_IncludedRouter` breakage (data#181, cascor#334) was a prerequisite merge before provenance PRs could go green; the effort also spawned egg-info/`.dockerignore` hardening (cascor#339, data#185, canopy#362) after exposing a stale-egg-info version-shadowing class.

### §3.3 Model/middleware refactor — 🟡 PARTIAL (the live tail)

| WS | Scope | Status | Evidence / notes |
|----|-------|--------|------------------|
| **WS-0** | Design ratification | ✅ Ratified 2026-06-14 | OQ-1/2/3/4/5 resolved; rename `recurse`→`recurrence` (OQ-19); fixed-order-LMU first (OQ-20) |
| **WS-1** | juniper-data time-series/regression foundation | ✅ **Shipped (over-delivered)** | Generators multi_sine / mackey_glass / ar_p / equities_seq (+ irregular_sine); 3-D NPZ `X.ndim` dispatch (2-D back-compat); `temporal_split_index` (no-leak invariant tested); `DatasetMeta.task_type` + optional `n_classes`; data-client passthrough. PRs data#169/#170/#171/#187/#188/#189, data-client#87 |
| **WS-2** | Extract `juniper-service-core` | 🟡 **Shipped (T1 + sync lifecycle only)** | PyPI 0.1.0; `create_app()`, `SettingsBase`, security/middleware/secrets, synchronous `TrainingLifecycle` body; **clean cascor-free DAG** (deps: fastapi, pydantic, pydantic-settings, model-core). **Designed-not-built:** websocket subsystem, worker subsystem + `TaskDistributor`, generic routes (training/metrics/dataset/snapshots) — only `/v1/health` + `/ready` exist. PRs ml#417/#419/#420/#422/#428 |
| **WS-3** | Define `juniper-model-core` + conformance kit | ✅ **Shipped & dogfooded** | PyPI 0.1.0, dependency-free base; `TrainableModel`/`GrowableModel`/`TrainingEvent`/`ModelSerializer` + abstract `TrainingLifecycleBase` seam; conformance kit (importable subclass-base + `[conformance]` extra) — **66 tests pass**; D1–D10 reflected; extras-wired + drift-lints present. PRs ml#416/#418 |
| **WS-3+** | **Cross-validation / fold-executor layer** | 🟡 **DESIGN-ONLY** | [Design ratified v1.0.0 (#431, 2026-06-16)](JUNIPER_2026-06-16_JUNIPER-ML_MODEL-CORE-CROSSVAL-LAYER-DESIGN.md) but **no `crossval/` code**; model-core still 0.1.0; the targeted 0.2.0 + `[crossval]` extra are unpublished |
| **WS-4** | Build the recurrence model | ✅ **Shipped & conformant** | `LMURegressor(TrainableModel)` (fixed-order; not Growable, per D-WS4-1); **passes conformance 10/10** (run live); `juniper-recurrence-model` **0.1.0 on PyPI**; pins real PyPI versions |
| **WS-4b** | Recurrence FastAPI/CLI app | 🔴 **BROKEN STACKED-MERGE** | Skeleton (PR#6) on `origin/main`; **PR#7 routes + PR#8 publish stranded on stale stacked bases, not on `main`**; app serves health-only (`routers=()`); **no Dockerfile**; app **unpublished (404)** |
| **WS-5** | Generalize canopy (model-agnostic UI + recurrence backend) | 🟡 **In progress (A0 shipped)** | A0 model registry merged (canopy #372); A1 surface + D2 3-D display designed-only; no recurrence backend yet; `BackendProtocol` still hardcodes `accuracy`/`cascade_phase`. See [reeval](JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md) |
| **WS-6** | Refactor cascor onto shared packages | 🟡 **Gate ARMED; cutover not started** | Golden (#340) + conformance (#341) **merged + required**; cascor still keeps own `src/api/**` (zero `juniper_service_core`/`juniper_model_core` prod imports — correct). **B-phase dependency-clear; A-phase blocked on OUT-11** (service-core T2 unpublished). See [reeval](JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md) |
| **WS-7** | deploy + juniper-ml extras integration | ⚪ **Not started** | No recurrence compose block; no `juniper-recurrence-client` in extras; no on-host launcher block (shared pkgs already in `[tools]` — that was WS-2/3) |
| **WS-8** | recurrence-worker (distributed) | ⚪ **Not started (correctly deferred)** | No package; trigger = training cost + OQ-11 |
| **—** | **`juniper-recurrence-client`** | 🟡 **Does not exist** | New package (mirrors `juniper-cascor-client`); **blocks WS-5** |

**WS-1 drifts (capability confirmed, naming/shape differs):** `temporal_split` shipped as `temporal_split_index`; `scaling` is advisory **meta JSON**, not an NPZ key; `readout_mask` does not exist (`observed_mask`/`padding_mask` do); `seq_lengths`/`target_dt` are defined + passed-through but **unvalidated** in the client; walk-forward/rolling multi-fold split is explicitly **not implemented**.

**Risk spot-check on shipped work (all clean):** service-core imports zero cascor code (only docstring/provenance mentions); the conformance kit has substantive asserts (RK-6 `"accuracy" not in metrics()` guard is enforced, not stubbed); the recurrence model + app-skeleton import cleanly against installed service-core 0.1.0.

---

## §4. Outstanding-work inventory (the true tail)

Grouped by theme; dependency-ordered within each. IDs (`OUT-n`) are local to this document.

### A. Unblock (critical path)

- **OUT-1 — Reconcile the WS-4b stacked-merge.** Get PR#7 (routes/data/state/events/schemas + tests) and PR#8 (publish workflow + docs) content onto `juniper-recurrence` `origin/main`. Forensics: `origin/main` HEAD = `c2e9736` (PR#6 merge); PR#7 content lives on `feature/ws4b-app-routes` (`04f1e91`), PR#8 on `feature/ws4b-app-publish-docs` (`06bf7a5`); neither is an ancestor of `main`. **Approach options in §5.1.**
- **OUT-2 — Sync stale local checkouts.** `juniper-deploy`, `juniper-data`, and `juniper-recurrence` local working trees are 1–2 commits behind `origin/main` (`git pull --ff-only`). Operational hygiene; do before any local build/verify.

### B. Ship the first model end-to-end

- **OUT-3 — Release `juniper-data-client` with `validate_npz_contract`.** Committed (`contract.py:41`) but **unreleased** (still 0.4.1); until released, the recurrence app's NPZ-contract gate runs disabled (guarded try/except).
- **OUT-4 — Add the recurrence app Dockerfile + publish to PyPI.** No Dockerfile exists; clone the worker's **CPU-lock two-stage** pattern (not cascor's CUDA lock). Then tag `juniper-recurrence-v0.1.0`, register the trusted publisher, publish (Paul drives the PyPI/pending-publisher gate). Depends on OUT-1.
- **OUT-5 — WS-7 deploy integration.** Add a `juniper-recurrence` compose service block (host 8211 → ctr 8210, per OQ-15/G7); `RECURRENCE_PORT`/`RECURRENCE_HOST_PORT` in `.env.example`; entries in `health_check.sh`/`wait_for_services.sh`; prometheus scrape jobs in **both** `prometheus.yml` and `prometheus.demo.yml`. Depends on OUT-4 (publish-first, §8.1).
- **OUT-6 — WS-7 on-host launcher.** Add a recurrence launch block to `util/juniper_plant_all.bash` (mirror cascor; bind 8211; PID line) and resolve the env decision **OQ-16 (§9.6)** (dedicated `JuniperRecurrence` env w/ copied LIBTORCH hook vs reuse `JuniperCascor1`).

### C. Monitoring / UI

- **OUT-8 — Create `juniper-recurrence-client`.** HTTP/WS client mirroring `juniper-cascor-client`, plus a **capability/schema negotiation** surface (so canopy can ask the backend its `task_type`, metrics, model type, topology). Publish via its own rail. **Blocks WS-5.** Depends on OUT-1 (routes must exist).
- **OUT-9 — WS-5 canopy generalization.** Generalize `BackendProtocol` (add `task_type`/capabilities/agnostic topology; stop requiring `accuracy`/`cascade_phase`); add a `RecurrenceServiceBackend`; make the metrics panel `task_type`-driven (MSE/MAE/R²); conditionally render cascor-only panels (decision-boundary/candidate/cascade); adapt dataset plotter (scatter → time-series) and network visualizer (cascade → recurrent cell from `describe_topology()`); add `JUNIPER_CANOPY_RECURRENCE_SERVICE_URL`. Depends on OUT-8.
- **OUT-7 — Meta-package extras (WS-7).** Add the recurrence **app** to `juniper-ml` `[servers]` (after OUT-4) and **`juniper-recurrence-client`** to `[clients]` (after OUT-8); both flow into `[all]`. **Update `tests/test_pyproject_extras.py` in the same PR** as each addition (the lint hard-fails otherwise); optional drift-lint mirroring `test_ci_tools_drift.py`. **Depends on OUT-4 (app extra) + OUT-8 (client extra).**

### D. Capability deepening

- **OUT-10 — Build the model-core cross-validation layer.** Implement `juniper_model_core.crossval/{metrics,splits,executor}` + `[crossval]` extra per [#431](JUNIPER_2026-06-16_JUNIPER-ML_MODEL-CORE-CROSSVAL-LAYER-DESIGN.md); bump model-core 0.1.0 → 0.2.0; publish; widen the juniper-ml `[tools]` pin lockstep with `test_pyproject_extras.py`. **Approach options in §5.2.**
- **OUT-11 — Build the `juniper-service-core` T2 surface (as demanded by consumers).** Websocket subsystem, worker subsystem + `TaskDistributor`, and generic routes (training/metrics/dataset/snapshots) are designed-not-built. Needed in full by WS-6; partially exercised by WS-4b routes. **Approach options in §5.5.**

### E. Production cascor cutover (gated, last)

- **OUT-12 — Capture the cascor golden/snapshot regression suite** (two-spiral fixed-seed trajectories + API response snapshots + HDF5 round-trips). This **is** the WS-6 trigger-gate. ✅ **DONE** — cascor #340, merged + required check (`Golden / Snapshot Regression`).
- **OUT-13 — Wire cascor to the model-core conformance kit** against `CascadeCorrelationNetwork` (the other half of the trigger). ✅ **DONE** — cascor #341, merged + required check (`model-core Conformance`); test-only adapter, no production change.
- **OUT-14 — WS-6 cutover (6a mechanical re-export shim → 6b behavioral interface adoption)** behind the golden gate, honoring the kill-criterion. **Approach options in §5.4.**

### F. Deferred / housekeeping

- **OUT-15 — WS-8 `juniper-recurrence-worker`** — deferred until training cost justifies + OQ-11 resolves.
- **OUT-16 — Wave-2 cascor self-adoption of `juniper-cascor-model`** (retire drift-guard; backport `gap #3` logger) — deferred (§3.1).
- **OUT-17 — Doc-hygiene pass** — refresh the four stale doc headers/trackers (§2) and the four §9 follow-ups from the placement plan. Low-risk; anytime.

---

## §5. Design / development approach options (per open decision)

Each block gives concrete options with strengths/weaknesses/risks/guardrails and a recommendation. (Per the project's "Design First" convention, a recommendation is given — not just a survey.)

### §5.1 OUT-1 — WS-4b stacked-merge remediation `[Priority 0]`

The PR#7/PR#8 content is preserved on `feature/ws4b-app-routes` and `feature/ws4b-app-publish-docs` but is off-`main`. Three ways to land it:

| Option | Mechanic | Strengths | Weaknesses | Risks | Guardrails |
|--------|----------|-----------|------------|-------|-----------|
| **A — Re-merge branches via fresh PRs (recommended)** | Open new PR: `feature/ws4b-app-routes` → `main` (resolve conflicts vs the PR#6 merge), then `feature/ws4b-app-publish-docs` → `main`. Use **Rebase-and-merge** or squash-to-one-commit. | Preserves authored history + review trail; smallest conceptual leap; branches already hold the work | Two sequential PRs; must re-resolve any drift vs current `main` | Re-tripping the same stacked-base trap if bases aren't reset to `main` | Set **both** PR bases to `main` explicitly; verify with `git merge-base --is-ancestor` post-merge; CI green before tag |
| **B — Single reconciliation PR (cherry-pick/collapse)** | Cherry-pick the unique commits from both feature branches onto a new branch off current `origin/main`; one PR. | One review, one merge; clean linear result; sidesteps stacked bases entirely | Loses the #7/#8 PR boundary; manual cherry-pick can miss a commit | Dropping a file (the original break was exactly "content didn't propagate") | Diff the result tree against `feature/ws4b-app-publish-docs` tip (`git diff` must be empty); enumerate expected files (routers/, data.py, state.py, events.py, schemas.py, tests, publish workflow) |
| **C — Reset `main` to the publish-branch tip** | Fast-forward/reset `origin/main` to `06bf7a5` (it already contains #6+#7+#8 in order). | Trivially complete + correct by construction | Rewrites/force-moves shared `main`; hostile to any concurrent work; non-reviewable jump | History-rewrite on a shared branch (against ecosystem norms) | **Avoid unless** `main` has nothing since `c2e9736` and Paul approves a force-move |

**Recommendation: Option A**, falling back to **B** if the branches conflict badly with `main`. Either way, the **acceptance gate** is: `git ls-tree origin/main` shows the full app tree (routers/, data.py, state.py, events.py, schemas.py + tests + `publish-recurrence-app.yml`), `ci-recurrence-app.yml` is green, and the app boots past health-only. This is the textbook squash/stacked-merge hazard from project memory — whichever option, the guardrail is **explicit base = `main` + post-merge ancestor check**.

### §5.2 OUT-10 — model-core cross-validation layer

[#431](JUNIPER_2026-06-16_JUNIPER-ML_MODEL-CORE-CROSSVAL-LAYER-DESIGN.md) is ratified but unbuilt. When/how to build:

| Option | Description | Strengths | Weaknesses | Risks | Guardrails |
|--------|-------------|-----------|------------|-------|-----------|
| **A — Build now as model-core 0.2.0 (recommended)** | Implement `crossval/{metrics,splits,executor}` + `[crossval]` extra; publish 0.2.0; widen juniper-ml `[tools]` pin lockstep | Design is fresh/ratified; dependency-free base preserved (numpy in `[crossval]` extra only); unblocks both indirect (service/CLI) and direct (canopy) CV routes | Builds ahead of a hard consumer demand (recurrence works without it today) | Over-build / interface churn if the first real CV consumer wants something different | Dogfood with an **in-repo 3-D stub** (keep model-core data-clean); add recurrence's real `LMURegressor` CV test on the recurrence side (per #431 §6) |
| **B — Defer until a consumer needs it** | Leave design-only; build when WS-5/CLI first calls for folds | Zero risk of speculative abstraction; smallest near-term surface | Re-paging-in cost later; CV becomes a hidden prerequisite that surfaces late | A consumer roadmap item silently blocks on an unbuilt layer | If deferred, **annotate the #431 doc "BUILD-PENDING"** and add a tracking item so it can't be forgotten |
| **C — Minimal walk-forward only** | Ship just the temporal/walk-forward split + metric aggregation; defer parallel fold execution (OQ-11) | Matches the recurrence (time-series) need exactly; smallest correct slice | Two releases if full CV later wanted | Under-build forcing a 0.3.0 soon | Gate the slice on the recurrence model's actual CV need; keep the executor interface forward-compatible |

**Recommendation: Option A** if recurrence/canopy will show model-comparison or k-fold metrics soon (the platform thesis points that way); otherwise **C**. **Hard guardrail either way:** widen the `[tools]` `<0.2.0` cap **in the same PR** as `test_pyproject_extras.py`, or the extras lint fails.

### §5.3 OUT-8 — `juniper-recurrence-client`

| Option | Description | Strengths | Weaknesses | Risks | Guardrails |
|--------|-------------|-----------|------------|-------|-----------|
| **A — Full client mirroring cascor-client (recommended)** | HTTP + WS client with capability/schema negotiation, own publish rail | Symmetric with the cascor family; gives canopy a clean typed seam; reuses a proven template | More upfront surface than a bare HTTP call | Drift vs cascor-client conventions | Clone cascor-client's structure + publish gating; `gh workflow run` the new publish workflow before relying on it (RK-10) |
| **B — Thin client now, expand later** | Minimal training/predict/health wrappers; add WS + schema negotiation when WS-5 needs them | Fastest unblock of WS-5's happy path | Schema negotiation (the WS-5 contract) deferred — risks a second pass on canopy | Canopy hardcodes assumptions the thin client can't advertise | Define the capability-advertisement shape **before** WS-5 starts, even if implemented thinly |
| **C — No dedicated client; canopy uses a generic HTTP adapter** | Canopy talks to the recurrence app via its existing service-backend pattern | Zero new package | Breaks the per-family client symmetry; pushes recurrence-specifics into canopy | Re-introduces model coupling into the agnostic UI (the very thing the refactor removes) | Reject unless a client package is judged unwarranted long-term |

**Recommendation: Option A** (it is the journal's idea-#5 and the §2.6 plan), with the capability-negotiation surface designed up front so WS-5 consumes a stable contract.

### §5.4 OUT-14 — WS-6 cascor cutover (the only behavior-risky step)

| Option | Description | Strengths | Weaknesses | Risks | Guardrails |
|--------|-------------|-----------|------------|-------|-----------|
| **A — Full adoption: service-core + model-core (recommended *if* gate green)** | 6a re-export shims → 6b interface adoption; cascor consumes both shared packages | Realizes the template's payoff on the production model; deletes duplicate infra; single source of truth | Touches the most-coupled production node; needs the full service-core T2 surface (OUT-11) to exist first | Behavior regression in production cascor; build-green/runtime-red lock trap | Pre-captured **golden suite + conformance kit must stay green** (OUT-12/13); pin **and** regen lock in the same commit; grep container log for `ModuleNotFoundError` |
| **B — model-core only; keep cascor's service stack** | cascor implements `TrainableModel`/`GrowableModel` but keeps its own `src/api/**` | Lower blast radius; still proves the *model* interface on cascor; avoids needing service-core T2 | Leaves cascor's service infra duplicated (partial template payoff) | Interface adoption alone can still shift event/metric semantics | Conformance kit green for cascor; golden suite green; document the one-sided extraction |
| **C — Never (invoke the kill-criterion)** | cascor keeps everything; recurrence still benefits from the shared packages | Zero risk to production; honest if conformance can't go green without behavior change | Permanent duplication; template "proven" only on greenfield | Strategic: the platform never fully validates the cutover | Only after a genuine attempt; record the decision in the refactor doc |

**Recommendation:** Sequence **B → A**: adopt model-core first (smaller, proves the interface on the production model), then service-core once OUT-11 lands — but **only** behind the golden gate, and keep **C** as the explicit, pre-agreed kill-criterion. This is the *last* wave regardless (§6).

### §5.5 OUT-11 — `juniper-service-core` T2 surface (websocket / worker / routes)

> **Tier note:** "T2 surface" here is shorthand for the still-unbuilt generic service pieces — the generic **routes** (refactor §2.2 T2) plus the **websocket/worker** subsystems (refactor §2.2 classes those T1, but *contingent on OQ-11*). It is not a verbatim restatement of the anchor doc's T1/T2 split.

| Option | Description | Strengths | Weaknesses | Risks | Guardrails |
|--------|-------------|-----------|------------|-------|-----------|
| **A — Build lazily, driven by consumers (recommended)** | Extract each T2 piece (routes first for WS-4b; worker/ws later) only when a consumer needs it | Avoids the journal's over-abstraction risk (RK-4); each piece designed against ≥1 real caller | Service-core stays "incomplete" vs the §2.3 vision for a while | Piecemeal interface may need rework when the 2nd consumer (cascor) arrives | Drive every extracted interface from a real caller; re-validate against cascor before freezing (RK-4 guardrail) |
| **B — Build the full T2 surface up front** | Implement ws + worker + `TaskDistributor` + all generic routes now | Service-core matches its design; WS-6 has everything ready | Large speculative build with one (greenfield) consumer; highest over-abstraction risk | Freezing interfaces from recurrence alone, then bending them for cascor | Only with cascor's needs explicitly modeled in parallel (design against 2 implementers) |
| **C — Extract straight from cascor at WS-6 time** | Don't generalize until the cascor cutover forces it | Guarantees the interface fits the production model | Recurrence app must hand-roll routes/ws in the meantime (duplication) | Recurrence and cascor diverge before unification | Acceptable only if recurrence's route needs are trivial |

**Recommendation: Option A.** The immediate need is the recurrence app's *routes* (training/predict/metrics) — extract those into service-core (or let WS-4b carry them and harvest later), and defer the websocket/worker subsystems until WS-5 (live monitoring) or WS-8 (distributed) genuinely demand them. Honors "shared by default, override if needed" without front-running a second consumer.

### §5.6 OUT-3 — data-client release & WS-1 follow-ups

Lower-controversy; the real choice is **release cadence** for the committed-but-unreleased `validate_npz_contract`.

| Option | Description | Strengths | Weaknesses | Risks | Guardrails |
|--------|-------------|-----------|------------|-------|-----------|
| **A — Cut `juniper-data-client 0.4.2` now (recommended)** | Release just `validate_npz_contract` immediately so the recurrence app's NPZ gate engages | Unblocks OUT-4's contract gate fastest; small, independently-verifiable additive diff | A later `seq_lengths`/`target_dt`/walk-forward release means two releases close together | Same-week 0.4.2 → 0.5.0 churn doubles release/verify overhead | Patch-level (additive); TestPyPI `--no-deps` install-verify with **no** pypi.org fallback (test-enforced policy) |
| **B — Batch into one 0.5.0** | Ship `validate_npz_contract` + the unvalidated `seq_lengths`/`target_dt` validators + walk-forward split together | One release, one verify cycle; fewer version bumps | Delays OUT-4's contract gate until the whole batch is ready | The recurrence app keeps running with its NPZ gate disabled longer (R12) | Don't let the batch block OUT-4; if the batch slips, fall back to A |

**Recommendation: A now** (unblocks the contract gate), then a **B-style 0.5.0** as a follow-up — smaller, independently-verifiable releases beat a big-bang.

---

## §6. Prioritization, ordering, grouping (the roadmap)

### §6.1 Three sequencing strategies (pick one global posture)

| Strategy | Optimizes for | Order sketch | Strengths | Weaknesses / risk |
|----------|---------------|--------------|-----------|-------------------|
| **S1 — Unblock-and-ship (recommended)** | Getting the *first new model fully deployed* (the refactor's actual purpose) | OUT-1 → 2 → 3 → 4 → 5/6 → 8 → 9 → 7 → 10/11 → 12–14 | Fastest end-to-end proof of the template; momentum; each rung leaves both stacks green | Cross-val + service-core T2 arrive later (acceptable — no hard consumer yet) |
| **S2 — Risk-minimizing** | Touching production cascor as little as possible | Same as S1 but WS-6 parked indefinitely behind kill-criterion; build cross-val/T2 only on demand | Lowest blast radius; leanest | Template never fully validated on the production model |
| **S3 — Capability-first** | A "complete" template before shipping | Build service-core T2 + cross-val + client fully, *then* recurrence app + deploy | Cleanest abstractions; cascor cutover trivial afterward | Delays the end-to-end proof; highest over-abstraction risk (RK-4); WS-4b stays broken longer |

**Recommendation: S1, with S2's WS-6 discipline.** Ship the recurrence model end-to-end first; treat the production-cascor cutover as a last, gated, reversible step.

### §6.2 The wave plan (S1, dependency-honest; every wave leaves both stacks green)

```text
WAVE A — UNBLOCK            OUT-1 (fix WS-4b merge)  ·  OUT-2 (sync checkouts)
   │                        gate: full app tree on origin/main; ci-recurrence-app green
   ▼
WAVE B — SHIP FIRST MODEL   OUT-3 (data-client release) → OUT-4 (Dockerfile + publish app)
   │                        → OUT-5 (deploy compose) · OUT-6 (on-host launcher)
   │                        gate: recurrence reachable on both stacks; existing services untouched
   ▼
WAVE C — MONITORING/UI      OUT-8 (recurrence-client) → OUT-9 (WS-5 canopy generalization)
   │                        · OUT-7 (extras: app→[servers] post-OUT-4, client→[clients] post-OUT-8)
   │                        gate: canopy renders recurrence (MSE/MAE/R²); cascor path unchanged
   ▼
WAVE D — CAPABILITY         OUT-10 (cross-val 0.2.0 — build-now A *or* walk-forward-only C, §5.2)  ·  OUT-11 (service-core T2 as needed)
   │                        gate: conformance + extras lints green
   ▼
WAVE E — CASCOR CUTOVER     OUT-12 (golden suite) → OUT-13 (conformance wiring) → OUT-14 (WS-6 B→A)
   │                        gate: golden + conformance green; kill-criterion honored
   ▼
WAVE F — DEFERRED/HYGIENE   OUT-15 (WS-8) · OUT-16 (cascor self-adoption) · OUT-17 (doc hygiene, anytime)
```

### §6.3 Grouping rationale

- **Wave A is a single bug-fix wave** — nothing downstream is honestly actionable until the recurrence app is whole on `main`. (OUT-2, syncing stale local checkouts, is a *standing precondition* for any local build/verify across Waves B–E, not only a one-time Wave-A chore.)
- **Waves B/C are the template payoff** — a *new* service added to both stacks (additive, low-risk), then the UI made model-agnostic. This is the visible deliverable.
- **Wave D is opportunistic** — build cross-val and service-core T2 when a consumer pulls them; do not front-run (RK-4). The consumer that pulls **OUT-11** is WS-6's A-phase (see the Wave E note).
- **Wave E is isolated and last** — the only production-risky work, fully gated and reversible; can be parked (S2) without blocking A–D. **One cross-wave edge:** WS-6's *A-phase* (full service-core adoption, §5.4) requires the service-core T2 pieces it consumes (**OUT-11**, Wave D) to exist first; the *B-phase* (model-core only) does not, so WS-6 may begin (B) even while OUT-11 is deferred.
- **Wave F is parallelizable anytime** — doc hygiene especially is cheap and can ride alongside any wave.

### §6.4 What can run in parallel

Within a wave, independent repos parallelize: in Wave B, OUT-5 (deploy) and OUT-6 (on-host launcher) are independent once OUT-4 publishes; in Wave E, OUT-12 (golden capture) is independent of everything and could even start early as insurance. Cross-session race guardrail: land shared-CI/extras edits in **dedicated** PRs (RK-11), and `gh pr list` before starting any repo (concurrent-session hazard from memory).

---

## §7. Consolidated risk register & guardrails

| # | Risk | Likelihood × Impact | Guardrail |
|---|------|---------------------|-----------|
| R1 | **WS-4b merge re-trips the stacked-base trap** | Med × High | Explicit PR base = `main`; post-merge `git merge-base --is-ancestor` check; enumerate expected files (§5.1) |
| R2 | **Publish-first violated** (consumer pins an unpublished package) | Med × High | No consumer pins `juniper-recurrence`/data-client until on PyPI; TestPyPI soak first (§8.1 of refactor) |
| R3 | **Pin bumped without lock regen** (build-green/runtime-red) | Med × High | Pin + `requirements.lock` regen in the **same** commit; `/tmp`+`mv` recipe; grep container log for `ModuleNotFoundError` |
| R4 | **Over-abstraction** of service-core T2 / cross-val | Med × Med | Drive each interface from ≥1 real caller; design against 2 implementers before freezing (§5.5/§5.2) |
| R5 | **Destabilizing production cascor** (WS-6) | Med × High | Golden suite + conformance gate; kill-criterion; B→A sequencing; reversible commits (§5.4) |
| R6 | **Extras lint breaks** when adding recurrence-client / widening cross-val pin | Med × Low | Update `test_pyproject_extras.py` in the same PR; drift-lint the new pins |
| R7 | **New CI/publish workflow passes lint but fails first run** | Med × Low | `gh workflow run` every new workflow immediately (RK-10; 3 prior incidents) |
| R8 | **Squash-merge ships first commit only** | Med × Med | Rebase-and-merge or force-to-one-commit for multi-commit PRs (materialized twice already: worker#101, WS-4b) |
| R9 | **On-host stale checkouts** mislead local verify | High × Low | `git pull --ff-only` all sibling repos before local builds (OUT-2) |
| R10 | **PyPI/deploy approval gates** stall the chain | Med × Low | Paul drives PyPI/pending-publisher + env approval gates; agents drive *to* the gate and hand off (memory) |
| R11 | **Concurrent-session races** on shared CI/extras files | Med × Low | Dedicated PRs; `gh pr list` before touching a repo |
| R12 | **NPZ contract gate runs disabled** (data-client unreleased) | High × Low | Release data-client (OUT-3) so the recurrence app's `validate_npz_contract` engages |

---

## §8. Testing roadmap for the outstanding work

Inherits the ecosystem's hard-won defenses (block dash/playwright plugin autoload; reap multiprocessing orphans; BLAS thread limits; pyproject is the sole pytest config; `reset_prometheus_registry` for collector tests; 80% coverage gate).

- **OUT-1 (WS-4b):** acceptance = full app tree on `main` + `ci-recurrence-app.yml` green + the conformance kit still 10/10 + app boots past health-only.
- **OUT-3/4 (data-client / app publish):** TestPyPI install-verify (`--no-deps`, **no** `--extra-index-url pypi.org` fallback — test-enforced policy); recurrence app `/v1/health` + `/v1/health/ready` reachable; conformance kit green against the published model.
- **OUT-5/6 (deploy / on-host):** `docker compose --profile full config` exits 0; `make up && make wait && make health`; on-host `curl :8211/v1/health` + PID line; prometheus target `up`; existing services' invariants (§8.2 of refactor) still green.
- **OUT-8/9 (client / canopy):** backend-protocol conformance for the recurrence backend; regression-backend → MSE panel (no decision-boundary); conditional-panel tests; **UI subsuite isolated** (`--ignore=src/tests/ui` + separate job; POST to the param endpoint — Dash/Playwright `type=number` gap).
- **OUT-10 (cross-val):** the #431 §6 matrix — dogfood with an in-repo 3-D stub; recurrence adds the real LMU-CV test on its side; property tests for split leakage.
- **OUT-11 (service-core T2):** a stub model drives every newly-extracted generic route + ws channel; backward-compat golden responses captured pre-extraction.
- **OUT-12–14 (WS-6):** the golden suite (two-spiral fixed-seed trajectories + API response snapshots + HDF5 round-trips) is the gate; conformance kit green for cascor; `make test` (3-service e2e) green; kill-criterion enforced.

---

## §9. Open questions / decisions that need Paul

1. **Sequencing posture** — confirm **S1 (unblock-and-ship)** vs S2/S3 (§6.1).
2. **WS-4b remediation** — Option A (re-merge via fresh PRs) vs B (single reconciliation PR) (§5.1). Recommend A.
3. **Cross-val timing** — build now as 0.2.0 (A) vs defer (B) vs minimal walk-forward (C) (§5.2).
4. **recurrence-client shape** — full vs thin-first (§5.3).
5. **WS-6 appetite** — pursue B→A behind the gate, or pre-commit to parking it (S2/kill-criterion) (§5.4)?
6. **OQ-16** — dedicated `JuniperRecurrence` conda env (with copied LIBTORCH hook) vs reuse `JuniperCascor1` (OUT-6).
7. **Doc hygiene** — apply the §2 header/tracker refreshes now, or batch later (OUT-17)?
8. **Carried-forward open questions** (still live): OQ-11 (recurrent worker parallelism — gates service-core worker subsystem + cross-val parallel folds + WS-8), OQ-17 (TestPyPI soak window before the cascor lock pins the shared packages).

---

## §10. Validation record (multi-agent)

**Round 1 — investigation (2026-06-17).** Five independent read-only sub-agents reconciled each effort-cluster against live source / PyPI / `gh` / `git` under anti-hallucination rules (one verdict per claim; primary evidence mandatory; doc restatements untrusted). Suites were executed where cheap (model-core conformance 66/66; recurrence model conformance 10/10; compose-provenance regression 3/3). Convergent, high-confidence findings; the load-bearing results — the three anchors' completion state, the WS-4b broken-stacked-merge forensics, the cross-val "design-only" verdict, and the PyPI publication states — were each independently evidenced.

**Round 2 — adversarial validation of *this document* (2026-06-17, complete).** Three independent agents re-checked this document along orthogonal axes — **facts** (every §2/§3/Appendix-A claim re-verified against live source / PyPI / `git` / `gh`, refute-on-sight, doc restatements untrusted), **logic / structure / completeness**, and **hygiene** (markdown lint, dangling links, typos) — plus a deterministic link/whitespace pass. Outcome: the document is factually accurate — the WS-4b broken-stacked-merge forensics (`origin/main` at `c2e9736`; `04f1e91`/`06bf7a5` non-ancestors), the cross-val "design-only" state, and all 13 sampled PR numbers were independently confirmed, and the model-core (66) and recurrence (10/10) conformance counts were reproduced. No factual claim was refuted. Corrections integrated:

- **Fact (DRIFTED):** §3.2 said "all 7 compose build blocks" — there are **8** `build:` blocks; the 7 *service* blocks carry provenance, the 8th (`test-runner`) carries none by design. Corrected.
- **Logic (CRITICAL):** OUT-7 (meta-package extras) had a wrong dependency (`OUT-9`) and was scheduled in Wave B *before* its prerequisite. Corrected to depend on **OUT-4 (app extra) + OUT-8 (client extra)**, moved to **Wave C**, and added to the §6.1 S1 order sketch (it had been omitted).
- **Logic (MAJOR):** §5.6 (OUT-3) lacked the four-element option treatment — converted to the standard strengths/weaknesses/risks/guardrails table.
- **Logic (MAJOR):** the **OUT-11 → OUT-14(A)** gate is now explicit (WS-6's A-phase needs the service-core T2 surface; the B-phase does not).
- **Minor:** carried the cross-val A-vs-C conditional into §6.2; flagged OUT-2 as a standing precondition; added a "T2 surface" tier-mapping note (§5.5); linked OQ-16 between OUT-6 and §9.6; fixed two typos (§5.1 `ą`, §5.3 `unblh`).

All 10 internal links resolve; all 10 tables are column-consistent; the TOC matches the section headers; the canonical 6-field header is present. The document is considered validated; the §9 decisions remain Paul's to make.

---

## Appendix A — PR / commit ledger (evidence, 2026-06-17)

**Package placement:** ml#398 (plan), ml#410 (retire ml home, `4bfa0e8c`), cascor#328 (relocate+rename+publish/CI), cascor#329 (torch floor), worker#102 (adopt 0.1.0; fixes the #101 squash-race), deploy#115 (`dbacc90`, stopgap removal). Issues cascor#319 + worker#97 closed 2026-06-14. PyPI: `juniper-cascor-model` 0.1.0 ✓; `juniper-cascor-core` 404.

**Build provenance:** obs#414 (→0.4.0), data#180 (+#185 hardening, #181 fastapi-fix), cascor#333 (+#334 fastapi-fix, #339 dockerignore), canopy#360 (+#362 egg-info), worker#103, deploy#118/#119/#122 (incl. OQ-2 `-dirty`). PyPI: `juniper-observability` 0.4.0 ✓.

**Shared packages:** ml#416 (model-core scaffold, `47246b2`), ml#417 (service-core scaffold), ml#419 (security), ml#420 (launcher), ml#422 (sync lifecycle body), ml#418 (model-core→extras), ml#428 (service-core→`[tools]` + drift guard), ml#431 (cross-val **design** doc, `2cf4d97`). PyPI: `juniper-model-core` 0.1.0 ✓ (2026-06-14); `juniper-service-core` 0.1.0 ✓ (2026-06-16).

**WS-1 data:** data#169/#170/#171 (core), #187/#188 (generators), #189 (scaling meta); data-client#87. (#168 = umbrella issue.)

**WS-4 / WS-4b recurrence:** recurrence-model PRs #1–#5 (model; #4 = `5ad3180` publish hardening); app PRs #6 (skeleton; on `origin/main` = `c2e9736`), #7 (routes; stranded on `feature/ws4b-app-routes` = `04f1e91`), #8 (publish; stranded on `feature/ws4b-app-publish-docs` = `06bf7a5`). PyPI: `juniper-recurrence-model` 0.1.0 ✓; `juniper-recurrence` (app) 404.

## Appendix B — Source documents & provenance

- Anchors: [`JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md`](JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md), [`JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md`](JUNIPER_2026-06-14_JUNIPER-ECOSYSTEM_BUILD-PROVENANCE-DESIGN.md), [`JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`](JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md).
- Cluster: [`JUNIPER_2026-06-05_JUNIPER-ECOSYSTEM_CODE-ORGANIZATION-STRATEGY.md`](JUNIPER_2026-06-05_JUNIPER-ECOSYSTEM_CODE-ORGANIZATION-STRATEGY.md), [`JUNIPER_2026-06-03_JUNIPER-CASCOR_CORE-PYPI-MIGRATION-PLAN.md`](JUNIPER_2026-06-03_JUNIPER-CASCOR_CORE-PYPI-MIGRATION-PLAN.md), [`JUNIPER_2026-06-14_JUNIPER-ML_MODEL-CORE-INTERFACE-DESIGN.md`](JUNIPER_2026-06-14_JUNIPER-ML_MODEL-CORE-INTERFACE-DESIGN.md), [`JUNIPER_2026-06-16_JUNIPER-ML_MODEL-CORE-CROSSVAL-LAYER-DESIGN.md`](JUNIPER_2026-06-16_JUNIPER-ML_MODEL-CORE-CROSSVAL-LAYER-DESIGN.md), [`JUNIPER_2026-06-15_JUNIPER-RECURRENCE_WS4-MODEL-BUILD-PLAN.md`](JUNIPER_2026-06-15_JUNIPER-RECURRENCE_WS4-MODEL-BUILD-PLAN.md), [`JUNIPER_2026-06-15_JUNIPER-RECURRENCE_WS4B-APP-BUILD-PLAN.md`](JUNIPER_2026-06-15_JUNIPER-RECURRENCE_WS4B-APP-BUILD-PLAN.md), [`JUNIPER_2026-06-14_JUNIPER-RECURRENCE_MODEL-DETAILED-DESIGN.md`](JUNIPER_2026-06-14_JUNIPER-RECURRENCE_MODEL-DETAILED-DESIGN.md).
- Ground truth: live filesystem + PyPI JSON + `gh`/`git` inspection across the eight repos, 2026-06-17.
