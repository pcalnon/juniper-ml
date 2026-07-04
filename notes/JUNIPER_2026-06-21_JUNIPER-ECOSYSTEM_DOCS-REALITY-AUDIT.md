# Juniper Docs-vs-Reality Audit — 2026-06-21

**Project**: Juniper ML Research Platform — cross-repo documentation reality audit
**Repository**: pcalnon/juniper-ml (planning hub)
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-23 (§1 refreshed; see the UPDATE banner)

---

> **What this is.** A point-in-time reconciliation of the Juniper planning/design/roadmap notes and
> the assistant memory against the **actual** state of the source (`origin/main` of every repo + PyPI),
> performed by four read-only sub-agents (WS-6/cascor, model-core/recurrence/DP-3, service-core/canopy,
> memory) plus direct `pip`/`gh`/`git` verification. Focus: **stale claims** and the **genuinely
> incomplete / not-started work register**. This doc is the authoritative current-state snapshot as of
> 2026-06-21; the per-cluster planning docs are point-in-time and trail reality by 1–4 days due to heavy
> concurrent-session velocity.

> **⟢ UPDATE 2026-06-23 (refresh).** Reality moved since the 2026-06-21 snapshot below; §1 versions are
> corrected. Deltas: **`juniper-service-core` 0.2.0 LIVE on PyPI** (publish #502 MERGED) → the WS-6 A-phase
> publish-blocker is **cleared**; **`juniper-data` 0.9.0** (+ `delay_product` capacity generator);
> **WS-6 B3 fully MERGED** (cascor B3.1 #352 / B3.2 #353 / B3.3 #355 — the `on_event` manager cutover; the
> fit/grow monkey-patches are gone), so **only B4 remains** of the B-phase; **WS-5 A1-i/ii SHIPPED**
> (canopy #383 `RecurrenceServiceAdapter` + #385 `RecurrenceBackend`/provider routing; A1-iii scope = #516);
> **DP-3 P2 fully shipped** (data #203, rec #44/#45, findings ml #511; capacity gap +0.83). Accordingly the
> §1 "WS-6 B3 NOT STARTED" / "A-phase BLOCKED on publish" / "WS-5 A1 NOT STARTED" rows and the §3 register's
> WS-6-B3 / WS-5-A1 / OUT-11-publish items are **superseded**. The WS-6 A-phase is now gated on **B4 + three
> owner decisions** (DR-1 / soak-OQ-17 / manager-appetite) — see `JUNIPER_2026-06-22_JUNIPER-CASCOR_WS6-APHASE-READINESS-VALIDATION.md`.

## §1. Verified current reality (2026-06-21)

**Published package versions (PyPI):** `juniper-model-core 0.3.0` · `juniper-service-core 0.2.0` (T1+T2; ↑ from 0.1.0) ·
`juniper-recurrence 0.1.1` · `juniper-recurrence-model 0.1.4` · `juniper-recurrence-client 0.1.0` ·
`juniper-data 0.9.0` (↑ from 0.8.0). *(Versions current as of the 2026-06-23 UPDATE banner above; the rest of §1 is the 2026-06-21 snapshot.)*

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
| `JUNIPER_2026-06-19_JUNIPER-CASCOR_WS6-BPHASE-MODEL-CORE-ADOPTION-BUILD-PLAN.md` | §5 PR table reads as pending (plan-tense) | B1/B2a/B2b merged #345–#347; B3 spike-done | **Status banner added** (B1/B2a/B2b shipped; B3 OQ-B1 decided; B4 pending; A-phase ⇢ OUT-11 #502) |
| `JUNIPER_2026-06-17_JUNIPER-CASCOR_GOLDEN-REGRESSION-SUITE-BUILD-PLAN.md` | design-tense | SHIPPED cascor #340 (required check) | **Status banner added** |
| `JUNIPER_2026-06-18_JUNIPER-CASCOR_MODEL-CORE-CONFORMANCE-WIRING-PLAN.md` | design-tense | SHIPPED cascor #341 (test-only adapter) | **Status banner added** |
| `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` | §2.2 OUT-11 "step 3 remaining"; B-phase un-started | OUT-11 T2 fully merged (publish #502 pending); B-phase shipped | **Status banner added** (points here) |
| `JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` (canonical Status Tracker) | WS-6 cells pre-B-phase; WS-5 = PLANNED | B-phase shipped; WS-5 A0 shipped | **WS-6 + WS-5 cells refreshed** |
| `JUNIPER_2026-06-17_JUNIPER-ECOSYSTEM_PLATFORM-ENVIRONMENT-STATE-AND-ROADMAP.md` | §3 WS-5/WS-6/OUT-13 cells (self-disclaimed point-in-time) | as §1 above | **"verified 2026-06-21 → see this audit" pointer added** |

### Flagged for owner refresh (concurrent-session-owned — NOT edited here, to avoid conflicts)

These docs are stale on *execution framing* but are owned/maintained by active concurrent sessions; their
staleness is captured here rather than edited in-place:

- **model-core**: `JUNIPER_2026-06-17_JUNIPER-ML_MODEL-CORE-STATE-AND-ROADMAP.md` (says 0.2.0 designed-not-built →
  reality 0.3.0 + crossval built); `JUNIPER_2026-06-17_JUNIPER-ML_MODEL-CORE-CROSSVAL-BUILD-ROADMAP.md` (PR-1 executed).
- **recurrence**: `JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md` is canonical (has a
  2026-06-18 update; +3 patch versions behind now); `JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-AND-ROADMAP.md`
  is a **31-line redirect stub** → the assessment doc (proper archive+pointer, not duplication; leave).
  `JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` is "design/ratification" but Rung-2a/2 are
  already shipping (sequencing inversion, not a contradiction; DP-3 P2-remaining = ml #501 handoff).
- **service-core**: `JUNIPER_2026-06-19_JUNIPER-ML_SERVICE-CORE-T2-SURFACE-DESIGN-AND-AUDIT.md` (T2 merged; publish
  #502 open) — owner session active.
- **canopy**: `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` + `..._A1_ENABLER_SCOPE_2026-06-18.md`
  read as pre-implementation; reality = A0 + 3-D viz shipped, A1 training-integration not started. The
  `..._REGRESSION_REMEDIATION_ROADMAP_2026-06-17.md` and `..._3D_DATASET_VISUALIZATION_DESIGN_2026-06-19.md`
  are CURRENT/accurate. The two `..._2026-06-15` audit docs self-flag as superseded.

### Cruft

- **`notes/JUNIPER_2026-05-02_JUNIPER-CANOPY_TEMP.md`** — a stray scratch file (mis-titled "juniper-canopy", "notes file for a new run-all-tests
  script"). **Flagged for removal** (not deleted here — not authored by this session; confirm with Paul).

## §3. Genuinely incomplete / not-started work register

| # | Item | Status | Blocked by | Owner / next |
| --- | --- | --- | --- | --- |
| 1 | **WS-6 B3** — replace monkey-patch monitoring with `CascorModel.fit(on_event=…)` sink (retain drain side-channel for the 50 Hz `/ws/training` stream) | **NOT STARTED** (spike done; OQ-B1 = proceed) | — | **next thread** (handoff `HANDOFF_2026-06-21_ws6-bphase-b3-on-event-sink.md`) |
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
