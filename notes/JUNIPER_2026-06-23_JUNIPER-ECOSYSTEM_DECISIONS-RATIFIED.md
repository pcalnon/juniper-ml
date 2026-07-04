# Juniper — Owner Decisions Ratified 2026-06-23

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml (planning hub)
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-23
**Status**: **Decision-of-record.** Ratifies the 10 open decisions surfaced by the 2026-06-23 decision-point reconciliation. This note is authoritative over the "recommendation" framing in the individual design docs (esp. D5 — see §1).

---

## 0. What this is

On 2026-06-23 the owner (Paul) ratified the 10 open decision points that the decision-point reconciliation
had carried as genuinely-live. This note records each **outcome + rationale + resulting action + home doc**,
so the choices are authoritative and not re-litigated by concurrent sessions reading the older
recommendation-tense docs. **The single override to flag: D5 (DP-3 P3) was ratified GO against the design's
"lean stop" recommendation** — a parallel session reading only `JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md`
would not build it; this note is the instruction that it proceeds.

## 1. Decision register

| ID | Decision | Ratified outcome | Rationale (owner) | Resulting action | Home doc |
|----|----------|------------------|-------------------|------------------|----------|
| **D-4** | WS-6 **B4** first | **YES — B4 before the A-phase** | B4 finishes the B-phase and is the A-phase precondition | Retire the test-only `CascorModelCoreAdapter`; point conformance at production `CascorModel` | `JUNIPER_CASCOR_WS6_BPHASE_..._2026-06-19.md` §5 (B4) |
| **D1** | DR-1: B→A vs park | **COMMIT B→A** (do the A-phase after B; do **not** park-after-B) | T2 gets a real production consumer (RK-4 counterweight); kill-criterion never fired | Proceed to the WS-6 A-phase once B-phase (B4) lands | `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` §7 DR-1 |
| **D2** | Soak bar (OQ-17) | **SOAK COMPLETE** (owner waives the wait; service-core 0.2.0 trusted) | — | A-phase is **not** blocked on soak | `JUNIPER_MODEL_MIDDLEWARE_REFACTOR_..._2026-05-31.md` OQ-17; `JUNIPER_2026-06-22_JUNIPER-CASCOR_WS6-APHASE-READINESS-VALIDATION.md` A2 |
| **D3** | Manager appetite | **CONVERGE** `lifecycle/manager` onto the `ServiceLifecycleManager` seam (real convergence, not keep-divergent) | Avoids a permanently-divergent manager; gives a clean A-phase | A-phase: subclass/converge the manager (executor/thread/snapshot/torch boundary) onto the seam | `JUNIPER_2026-06-22_JUNIPER-CASCOR_WS6-APHASE-READINESS-VALIDATION.md` §6 |
| **D5** | DP-3 **P3** (torch MLP readout) | **GO — build Rung 2b** *(overrides the design's "lean stop")* | The current dataset catalog doesn't demand it, but building it insures against silently losing the capability/insight on future complex & hybrid datasets; at minimum it falsifiably shows torch adds nothing | Build `MLPReadoutSpec` (Rung 2b) + a `[torch]` extra + a bench row; keep RFF as the numpy default | `JUNIPER_2026-06-20_JUNIPER-RECURRENCE_DP3-READOUT-SPECTRUM-DESIGN.md` §8a/§9 P3 |
| **D6** | Pre-commit "B5" tail | **FULL SWEEP** | Close the fleet remediation tail completely | F10 (env-name durability) + F7 (`pre-commit-hooks`→v6) + F13 (wheel-install smoke) + recurrence MED/LOW | `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_PRECOMMIT-TESTING-AUDIT-PLAN.md` |
| **D7** | OQ-16 (recurrence env) | **Dedicated `JuniperRecurrence` conda env** | Isolation (matches the per-app env convention) | Create `JuniperRecurrence` (+ LIBTORCH-strip hook); add the recurrence block to `juniper_plant_all.bash` (OUT-6) | refactor doc OQ-16; platform roadmap OUT-6 |
| **D8** | DR-3 / OQ-2 (crossval surface) | **Start AFTER A1 lands AND after D9** | Sequencing; needs the live recurrence path + auth first | Build the **canopy** crossval consumer surface over the recurrence `/v1/crossval` endpoint *(see §2 flag — "canopy", not "cascor")* | `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` §7 DR-3; A1-enabler OQ-2 |
| **D9** | DR-4 (auth wiring) | **Group with A1, as a separate step at the END of the A1 path** | Convenient batching; gates D8 | Inbound `juniper_recurrence_api_keys` secret + outbound canopy→recurrence `X-API-Key`/`RECURRENCE_SERVICE_URL` | `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` §7 DR-4 |
| **D10** | DR-2 (`execution` field) | **Group with A1-iv — but reassess its value before implementing** | The shipped `provider`/`status` routing may make the field unnecessary | When building A1-iv's predicate, first re-evaluate whether `ModelSpec.execution` is still warranted; add only if so | `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` §7 DR-2; canopy model-selection design |

## 2. Two interpretation flags (correct me if wrong)

- **D1** — owner wrote *"concur with the A→B path."* Recorded as the **commit-to-B→A** outcome (proceed with the A-phase after the B-phase; do not park), since D-4 (B4-first) and D3 (converge the manager = A-phase work) make "park" inconsistent. If "A→B" meant something else, flag it.
- **D8** — owner wrote *"bringing the cascor code into scope for the v1/crossval implementation."* Recorded as the **canopy** crossval consumer surface: `/v1/crossval` is the **recurrence app** endpoint (already shipped on model-core 0.2.0+), and DR-3/OQ-2 concerns **canopy** consuming it — cascor is not part of DR-3. If cascor was genuinely intended, flag it.

## 3. Sequencing (dependency order)

1. **WS-6 B4** → then **WS-6 A-phase** (DR-1 committed; soak complete; converge the manager per the corrected §5.6 ledger — CLEAN re-exports, ADAPTER seams `CommandExecutor`/`WorkerTaskProtocol`, manager subclass).
2. **DP-3 P3** (torch MLP readout) — independent, parallelizable.
3. **B5 full sweep** (F10 → F7 → F13 → recurrence MED/LOW).
4. **`JuniperRecurrence` env + OUT-6 launcher** — independent.
5. **Canopy A1**: A1-iii → A1-iv (+ D10 `execution` field, *reassess first*) → **D9 auth wiring** (end of the A1 path) → then **D8** canopy crossval surface.

## 4. Execution status (dup-guard, 2026-06-23)

Most ratified items were already in flight by concurrent sessions (active worktrees, PRs not yet opened) — these decisions largely *ratify* work already underway:

- **IN FLIGHT:** D-4 WS-6 B4 (`cascor feat/ws6-b4-native-conformance`); D6 B5 tail — F7 across 6 repos (`fix/precommit-hooks-v6-audit-f7`), F10 (`cascor`+`canopy` `f10-env-docs-durable-naming`), F13 (recurrence-tail handoff); D8/D9 canopy A1 (`canopy feat/canopy-recurrence-routes`, `ml docs/canopy-a1-iii-scope` #516).
- **UNCLAIMED (no worktree):** **D5 DP-3 P3** (needs this ratification to proceed — design said stop) and **D7 `JuniperRecurrence` env / OUT-6**.

→ `gh pr list` + worktree check before touching any in-flight item (dup-race rule).

## 5. Provenance

Decisions made by Paul on 2026-06-23 in response to the decision-point reconciliation (3-agent notes+code sweep). Execution status verified against `origin/main` + the centralized worktrees dir. Companion: `JUNIPER_2026-06-22_JUNIPER-CASCOR_WS6-APHASE-READINESS-VALIDATION.md` (the A-phase decisions) and `JUNIPER_2026-06-21_JUNIPER-ECOSYSTEM_DOCS-REALITY-AUDIT.md` (current-state).
