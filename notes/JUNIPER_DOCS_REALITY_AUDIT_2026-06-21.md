# Juniper Docs-vs-Reality Audit — 2026-06-21

**Project**: Juniper ML Research Platform — cross-repo documentation reality audit
**Repository**: pcalnon/juniper-ml (planning hub)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-21

---

> **What this is.** A point-in-time reconciliation of the Juniper planning/design/roadmap notes and
> the assistant memory against the **actual** state of the source (`origin/main` of every repo + PyPI),
> performed by four read-only sub-agents (WS-6/cascor, model-core/recurrence/DP-3, service-core/canopy,
> memory) plus direct `pip`/`gh`/`git` verification. Focus: **stale claims** and the **genuinely
> incomplete / not-started work register**. This doc is the authoritative current-state snapshot as of
> 2026-06-21; the per-cluster planning docs are point-in-time and trail reality by 1–4 days due to heavy
> concurrent-session velocity.

## §1. Verified current reality (2026-06-21)

**Published package versions (PyPI):** `juniper-model-core 0.3.0` · `juniper-service-core 0.1.0` (T1-only) ·
`juniper-recurrence 0.1.1` · `juniper-recurrence-model 0.1.4` · `juniper-recurrence-client 0.1.0` ·
`juniper-data 0.8.0`.

| Track | Reality | Evidence |
| --- | --- | --- |
| **WS-6 B-phase (cascor)** | B1 (#345) + B2a (#346) + B2b (#347) **MERGED**; `origin/main` = `f3ec5d9`. Gate green (golden #340 + conformance #341, both required). | cascor `git log origin/main` |
| **WS-6 B3 / B4** | **NOT STARTED.** B3 spike DONE → OQ-B1 decided = proceed with full `on_event` migration (retain side-channel). B4 follows. | this session |
| **WS-6 A-phase (6a)** | **BLOCKED on OUT-11 publish.** Seam shape ready; cascor imports nothing from service-core yet. | refactor plan §2.7 |
| **OUT-11 (service-core T2)** | Code **MERGED** (1a #473, websocket #484, worker-pool #492, coordinator #496, notes #499). PyPI still **0.1.0 (T1-only)**. **0.2.0 publish = ml #502 OPEN** (Paul-gated). | ml `git log`; `pip index`; #502 |
| **model-core** | **0.3.0 on PyPI**; `crossval/` layer BUILT (metrics/splits/executor); `predict(X, **kw)` drift RESOLVED. | `pip index`; `juniper-model-core/` source |
| **recurrence** | WS-4/WS-4b SHIPPED; app 0.1.1, model 0.1.4, client 0.1.0 all on PyPI. DP-3 implementing in parallel (Rung-2a RFF shipped in model 0.1.4); DP-3 P2-remaining + A1 training-integration are concurrent (ml #500/#501 handoffs). | `pip index`; recurrence `git log` |
| **WS-5 canopy** | A0 registry SHIPPED (#372); 3-D dataset viz D2 SHIPPED (#374–#379, all 3 phases); UI regression harness COMPLETE (#364/#366/#373, gating). **A1 training-integration NOT STARTED** (D1 paradigm unratified). | canopy `git log` |
| **juniper-data** | **0.8.0 on PyPI** (Δt generators + scaling-meta + regression-target). | `pip index` |
| **pre-commit/testing audit** | B1/B2/B3-core remediation MERGED across the fleet; ml/recurrence enforce-lane follow-ups landing (#42-class). | audit memory + `gh pr list` |

## §2. Stale claims by document (and disposition)

### Updated in this PR (WS-6 cluster + cross-cutting trackers — owned here)

| Doc | Stale claim | Reality | Action |
| --- | --- | --- | --- |
| `JUNIPER_CASCOR_WS6_BPHASE_MODEL_CORE_ADOPTION_BUILD_PLAN_2026-06-19.md` | §5 PR table reads as pending (plan-tense) | B1/B2a/B2b merged #345–#347; B3 spike-done | **Status banner added** (B1/B2a/B2b shipped; B3 OQ-B1 decided; B4 pending; A-phase ⇢ OUT-11 #502) |
| `JUNIPER_CASCOR_GOLDEN_REGRESSION_SUITE_BUILD_PLAN_2026-06-17.md` | design-tense | SHIPPED cascor #340 (required check) | **Status banner added** |
| `JUNIPER_CASCOR_MODEL_CORE_CONFORMANCE_WIRING_PLAN_2026-06-18.md` | design-tense | SHIPPED cascor #341 (test-only adapter) | **Status banner added** |
| `JUNIPER_WS5_WS6_REEVALUATION_2026-06-19.md` | §2.2 OUT-11 "step 3 remaining"; B-phase un-started | OUT-11 T2 fully merged (publish #502 pending); B-phase shipped | **Status banner added** (points here) |
| `JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` (canonical Status Tracker) | WS-6 cells pre-B-phase; WS-5 = PLANNED | B-phase shipped; WS-5 A0 shipped | **WS-6 + WS-5 cells refreshed** |
| `JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md` | §3 WS-5/WS-6/OUT-13 cells (self-disclaimed point-in-time) | as §1 above | **"verified 2026-06-21 → see this audit" pointer added** |

### Flagged for owner refresh (concurrent-session-owned — NOT edited here, to avoid conflicts)

These docs are stale on *execution framing* but are owned/maintained by active concurrent sessions; their
staleness is captured here rather than edited in-place:

- **model-core**: `JUNIPER_MODEL_CORE_STATE_AND_ROADMAP_2026-06-17.md` (says 0.2.0 designed-not-built →
  reality 0.3.0 + crossval built); `JUNIPER_MODEL_CORE_CROSSVAL_BUILD_ROADMAP_2026-06-17.md` (PR-1 executed).
- **recurrence**: `JUNIPER_RECURRENCE_STATE_ASSESSMENT_AND_ROADMAP_2026-06-17.md` is canonical (has a
  2026-06-18 update; +3 patch versions behind now); `JUNIPER_RECURRENCE_STATE_AND_ROADMAP_2026-06-17.md`
  is a **31-line redirect stub** → the assessment doc (proper archive+pointer, not duplication; leave).
  `JUNIPER_RECURRENCE_DP3_READOUT_SPECTRUM_DESIGN_2026-06-20.md` is "design/ratification" but Rung-2a/2 are
  already shipping (sequencing inversion, not a contradiction; DP-3 P2-remaining = ml #501 handoff).
- **service-core**: `JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md` (T2 merged; publish
  #502 open) — owner session active.
- **canopy**: `JUNIPER_CANOPY_MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` + `..._A1_ENABLER_SCOPE_2026-06-18.md`
  read as pre-implementation; reality = A0 + 3-D viz shipped, A1 training-integration not started. The
  `..._REGRESSION_REMEDIATION_ROADMAP_2026-06-17.md` and `..._3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md`
  are CURRENT/accurate. The two `..._2026-06-15` audit docs self-flag as superseded.

### Cruft

- **`notes/temp.md`** — a stray scratch file (mis-titled "juniper-canopy", "notes file for a new run-all-tests
  script"). **Flagged for removal** (not deleted here — not authored by this session; confirm with Paul).

## §3. Genuinely incomplete / not-started work register

| # | Item | Status | Blocked by | Owner / next |
| --- | --- | --- | --- | --- |
| 1 | **WS-6 B3** — replace monkey-patch monitoring with `CascorModel.fit(on_event=…)` sink (retain drain side-channel for the 50 Hz `/ws/training` stream) | **NOT STARTED** (spike done; OQ-B1 = proceed) | — | **next thread** (handoff `handoff_ws6-bphase-b3-on-event-sink_2026-06-21.md`) |
| 2 | **WS-6 B4** — point native conformance at production `CascorModel`; retire the test-only adapter | NOT STARTED | B3 decision | follows B3 |
| 3 | **WS-6 A-phase (6a)** — cascor `src/api/**` → service-core re-export shims | **BLOCKED** | OUT-11 service-core **0.2.0 publish** (#502) + soak | deferred (DR-1) |
| 4 | **OUT-11 publish** — `juniper-service-core` 0.2.0 (T1+T2) to PyPI | **READY** (code merged) | Paul publish gate | ml **#502 OPEN** |
| 5 | **WS-5 A1** — canopy training-integration (`RecurrenceServiceAdapter`, model→backend routing, selection surface) | NOT STARTED | **D1 paradigm ratification** (DR-2; recommend D1-A) | canopy session |
| 6 | **DP-3 remaining** — P2 (data → bench → HTTP enum) + later readout rungs | IN FLIGHT (concurrent) | — | ml #501 handoff |
| 7 | **pre-commit enforce lane** (recurrence #42-class) | OPEN | — | concurrent |
| 8 | **WS-7** — juniper-deploy compose for recurrence + meta-package extras | DESIGNED | recurrence-deploy gate | later |

**Headline:** No production system is broken; every incomplete item is new-code/forward work. The single
highest-uncertainty item (WS-6 B3) is de-risked (spike feasible) and queued for the next thread; the WS-6
A-phase is the main *blocked* item, gated entirely on the OUT-11 0.2.0 publish (ml #502, Paul's call).

## §4. Provenance

- **Method**: 4 read-only sub-agents (2026-06-21) + direct `pip index versions` / `gh pr list` / `git log
  origin/main` verification of every load-bearing claim. Cross-agent conflicts reconciled: OUT-8
  recurrence-client **does** exist (0.1.0 on PyPI, subdir-published — no standalone repo); service-core is
  0.1.0 (T1) with T2 merged-unpublished (#502 pending).
- **Lessons reaffirmed** (from prior handoffs): read `origin/main`, never stale local working trees;
  point-in-time roadmap status cells trail reality; Paul gates all merges + PyPI/deploy publishes.
