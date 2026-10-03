# Lane B agent B2 — adversarial review, lens: ACTIONABILITY / PRIORITY / SELF-CONSISTENCY

- **Procedure:** `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane B and §7
- **Target:** `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`
- **Date:** 2026-10-03
- **Brief:** refute
- **Mode:** read-only source review; no services or tests run

## 0. Instruments

| Instrument | Could it produce a different answer? | Sample size | What was NOT done |
| --- | --- | --- | --- |
| Line-by-line plan/template/procedure comparison | Yes; missing or correctly used sections produce different results | 1 target, 1 template, 1 procedure | No inference from the plan's audit artifacts |
| Finding-to-work-item census | Yes; every finding and every `Closes` cell was enumerated | 76 F rows, 49 W rows | Verified-control rows were not treated as defects needing work |
| Source declaration inspection | Yes; existence and present contracts can contradict plan prose | 8 focused declarations in four repos | No execution, imports, service starts, or tests |
| Design-of-record cross-check | Yes; H-9/R-6 and cited sections were read in their source | 1 design, 6 cited loci | No attempt to revalidate the design's historical measurements |
| Size/date arithmetic | Yes; counts use the plan's own size labels | 6 phases, 49 items, 5 milestones | No allowance for parallel engineers; the plan names no staffing model |

This is one Lane B agent, one iteration, starting from the target plan and independently opening declarations. It can assess specification and consistency, not runtime correctness.

## FATAL

### B2-F1 — The deployment blocker is scheduled last, so M1's “runnable” deliverable is false

**Claim attacked.** P1 “Make both entry points runnable” and M1 deliver a runnable canopy path by 2026-10-24.

**Evidence.** F-P4 says the published 0.16.0 metadata makes canopy refuse the pair (`:147`). Yet W5.5, the 0.17.0 release and floor bump, is deferred to P5 (`:342`), and the dependency table admits: “Until then only a `main` checkout ... serves `regression`” (`:491`). M1 nevertheless declares both entry points runnable (`:354`). W1.2/W1.9 also target juniper-data 0.17.0 in the status table, but that release is not scheduled until M4.

**Severity: FATAL.** The advertised M1 cannot work against published components. Two weeks of P0/P1 can produce a path canopy intentionally refuses.

**Smallest correction.** Move W5.5 to P0/P1 before canopy E2E acceptance; make M1 explicitly require published 0.17.0 and its floor. If checkout-only operation is intended, rename M1 and its success metric accordingly.

### B2-F2 — Scientific triage is wrongly last; the plan spends five phases operationalising an unvalidated path

**Claim attacked.** “Truthful before capable” justifies P0–P4 before W5.1 (`:259-266`).

**Evidence.** The plan measured aggregate CV r² = −18,081 (F-SCI1, `:220`), no honest held-out metric (F-SCI3, `:222`), and no acceptance band (F-SCI4, `:223`). W5.1 decides whether this is conditioning or a model defect, but is deferred until after M1 (`:470`). P0 instead includes deep readiness and a route fixture, while P1 adds new API and UI surface.

The source design's R-6 does say equities rows are informational (`JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md:1241`); that historical risk posture is not evidence that a −18,081 path deserves productisation.

**Severity: FATAL.** If W5.1 identifies a model/target defect, the first month builds launch, preview, timeout, observability, CI, and docs around the wrong path.

**Smallest correction.** Make W5.1 the first P0 investigation after the minimal env repair needed to run it. In parallel, promote W1.1 because the reported CLI symptom is inability to pass params. Gate the rest of P1 and the runbooks on a written go/no-go result. W0.7 should move out of P0.

### B2-F3 — W5.4 specifies a configuration surface that does not exist

**Claim attacked.** W5.4 says to encode a suite YAML `acceptance:` block “the driver already supports for cascor” (`:341`).

**Evidence.** `run_experiment.py` has acceptance outcomes and `EXIT_ACCEPTANCE`, but neither `run_suite.py` nor any shipped suite YAML parses an `acceptance:` configuration block. `run_suite.py:742` explicitly says comparator verdicts are reporting-only because gating remains a separate owner decision. The cited design defines acceptance criteria in prose (§10.4) and says cells inherit criteria (§10.5); it does not define this YAML block.

**Severity: FATAL.** W5.4 cannot be implemented as written, its S estimate excludes schema/parser/evaluator/reporting work, and its acceptance test cannot reach the claimed mechanism.

**Smallest correction.** Specify the YAML schema, parser locus, metric comparator, `failed` versus `flagged` state machine, report/exit semantics, and tests; resize M/L. Alternatively implement the band directly for E-H without claiming generic existing support.

## MAJOR

### B2-M1 — P0 contains scope that does not stop the four symptoms from being misreported

**Claim attacked.** Every P0 row is needed to “close the four symptoms ... as reported problems” (`:261`).

**Evidence.** W0.6 is a future route regression test, and W0.7 adds duplicate deep readiness after W0.2 already checks the same import/version. Neither changes suite outcome, metrics, 422 detail, or current env repair. W0.4 surfaces metrics but still permits absurd metrics until W5.4. W0.5 is useful feedback, not required for the suite's truthful disposition.

**Severity: MAJOR.** P0 is seven cross-repo/host items rather than the minimal W0.1/W0.2/W0.3 truth gate; this threatens M0 before user runnability starts.

**Smallest correction.** Keep W0.1–W0.3 in P0; move W0.4/W0.5 to the first runnable slice and W0.6/W0.7 to CI/hardening. Co-ship W0.6 only if needed to guard W0.1.

### B2-M2 — P0's dependency order contradicts itself

**Claim attacked.** P0 can finish in order and in one week.

**Evidence.** W0.2's fake-env test does not depend on repairing the real env, yet `:484` and `:496` make W0.1 prerequisite. Its acceptance also says “current env refuses until W0.1 is done” (`:273`), an observation impossible after executing the prescribed order. More seriously, W0.6 is P0 but the dependency table says W0.6 depends on P1 W1.5 and instructs “land W1.5 first” (`:485`). The critical graph omits this phase inversion.

**Severity: MAJOR.** The stated P0 execution order cannot satisfy its own acceptance evidence.

**Smallest correction.** Develop W0.2 against a synthetic stale env before/independently of W0.1 and retain that fixture as evidence. Remove W0.6's dependency on future validator changes or move W0.6 after W1.5.

### B2-M3 — W0.1/W0.2 ownership and acceptance are not durable

**Claim attacked.** “host env” can own W0.1 and an editable install is the repair.

**Evidence.** “host env” is not a repository or accountable owner. W0.1 proposes editable checkouts but does not pin their SHAs, identify the active worktrees, or define recovery after the next Python minor upgrade. `pip check` proves metadata consistency, not that imports resolve from the intended env rather than user site. The parent `AGENTS.md` explicitly warns that plain imports can leak from user site and recommends `python -s` checks.

**Severity: MAJOR.** The repair can pass while remaining non-reproducible or user-site dependent.

**Smallest correction.** Assign an operator/repo owner; record exact interpreter, package SHAs, editable paths, `python -s` import/version/location probes, and rollback. Make launcher preflight use the selected interpreter with user site disabled.

### B2-M4 — W1.1's acceptance does not prove the claimed runnable CLI path

**Claim attacked.** W1.1 closes F-S1/F-P1 and supports G2.

**Evidence.** The acceptance only proves JSON reaches a fake client and mutual exclusion (`:284`). It never proves JSON/file parsing errors are actionable, the real client accepts the bundle, the generated artifact is finite, or training completes. The Success Metric requires a “200-equivalent fit” (`:246`), which no listed W1.1 acceptance performs.

**Severity: MAJOR.** A wrong implementation can pass while the operator still gets the same runtime failure.

**Smallest correction.** Add an offline real-client fixture or bounded integration acceptance proving explicit params create a finite three-partition artifact and complete a CLI fit; test malformed JSON and unreadable files.

### B2-M5 — W1.2 is two mutually exclusive work items with one incompatible acceptance test

**Claim attacked.** R1 is required before an S–M implementable W1.2.

**Evidence.** W1.2 says either invent a `preset: "lmu"` generator parameter or merely document a bundle (`:285`). Source search found no general juniper-data preset mechanism, so the first choice is a new contract with precedence, schema, validation, and hashing semantics. The acceptance (“preset expands ... and is hashed”) cannot pass if R1 chooses documentation. R1 is partly an engineering recommendation the plan should make, not an owner-only question.

**Severity: MAJOR.** The implementer cannot know the deliverable or done condition, and S–M is unsupported.

**Smallest correction.** Recommend one option. If preset: specify precedence, unknown preset errors, explicit-param override rules, schema exposure, dataset-id canonicalisation, version bump, and size M/L. If docs-only: delete W1.2 as code and replace its acceptance.

### B2-M6 — W1.3 leaves the effective-parameter policy and preview UI unspecified

**Claim attacked.** W1.3 is an M-sized, directly implementable canopy change.

**Evidence.** `src/dataset_schema.py` exists, but it is a pure schema parser, not a declaration of every equities parameter. Runtime generator schema data must reach `recurrence_backend`, which currently imports only `generator_name_for_type` and unconditionally applies `_STAGED_PARAM_KEYS` plus staged params.

The plan does not name the data channel, preview component/callback, secret redaction, precedence representation, or what “explicit recurrence-aware form change” means. Its test uses staged `next_close`, yet the Change says keep the seed unless changed in an unspecified recurrence-aware form.

**Severity: MAJOR.** Multiple incompatible implementations satisfy the prose, and a static allow-list could pass the narrow test while dropping valid schema keys.

**Smallest correction.** Define the schema source and cache, seed/form/staged precedence, recurrence-aware field IDs, preview location and redaction, unavailable-schema behavior, and an exhaustive schema-key test.

### B2-M7 — W1.4 silently makes a breaking default change without a release ruling

**Claim attacked.** W1.4 is an S fix targeting model 0.4.0.

**Evidence.** It changes implicit fallback behavior to rejection by default (`:287`), while the risk table concedes non-equities artifacts may break (`:524`). “Default `reg` for the service and CLI” also leaves unclear whether model API default is `reg` or callers pass it. No owner ruling covers compatibility, migration, or whether recurrence 0.6.0/model 0.4.0 is the breaking release.

**Severity: MAJOR.** Existing callers can fail without a specified boundary or migration.

**Smallest correction.** Add a ruling/recommendation for API default and semver, census call sites, require explicit service/CLI arguments first, and retain `auto` as model default unless intentionally breaking.

### B2-M8 — W1.6 invents ambiguous status semantics and does not close non-cancellation

**Claim attacked.** W1.6 closes F-S6/F-C4/F-D5 in M size.

**Evidence.** `/v1/training/status` already exists, but its state is derived only from completed model state (`idle|trained|restored`); the lock has no persisted dataset/busy metadata. W1.6 does not define synchronization, status during dataset fetch versus fit, restart behavior, or timeout/poll termination.

Its “running (upstream)” state conflicts with the backend's `idle|training|trained|failed` vocabulary. F-S6 says no cancellation; the plan explicitly defers cancellation (`:583`), so “Closes F-S6” is false.

**Severity: MAJOR.** The API contract and state transitions are under-specified, and the finding remains open.

**Smallest correction.** Mark F-S6 partially mitigated; specify busy-state storage under the lock, response schema/state transitions, polling budget, terminal mapping, and concurrency tests. Add an owner decision on whether unresolved upstream work should make the client/suite non-zero.

### B2-M9 — Rulings R1–R5 both over-delegate engineering and omit load-bearing product decisions

**Claim attacked.** These are the five decisions needed to execute the plan (`:556-564`).

**Evidence.** R2 is already settled by the parent Data Contract: artifact dtype is `float32`; merely documenting tolerance contradicts the standing contract. R1 should receive an engineering recommendation after API-cost analysis. R3 is a genuine data-semantics ruling. R4/R5 are genuine science/product rulings, but R5 cannot be made until W5.1/W5.3 produce metrics.

Missing rulings include whether `degraded` exits non-zero for informational equities rows, whether canopy forwards staged generic params versus only recurrence-specific controls, and the W1.4 breaking/default-release policy.

**Severity: MAJOR.** One unnecessary ruling blocks P1 while three necessary decisions are hidden inside implementation prose.

**Smallest correction.** Resolve R2 to enforce float32; turn R1 into a recommendation with owner override; retain R3–R5 with prerequisites; add explicit rulings for degraded exit semantics, canopy precedence/forwarding, and target-default/semver.

### B2-M10 — Estimates and milestone dates omit integration, release, and review cost

**Claim attacked.** M0–M4 are plausible for one owner across the ecosystem.

**Evidence.** Counts from the plan: P0 = 4S+3M; P1 = 6S+3M+2S–M; P2 = 6S+4M; P3 = 3S+4M; P4 = 5S+1M; P5 = 5S+1M+2L. At the plan's own maxima, P0 alone is up to eight engineer-days before three repo PRs and host operations, yet M0 allows seven calendar days. M1 adds 11 items across five codebases and three rulings in 14 days. M2 combines 17 P2/P3 items across repos in 14 days. M3 is simultaneous. No staffing assumption, PR/release lead time, or owner availability appears.

**Severity: MAJOR.** Dates are not a schedule; they are optimistic labels disconnected from the stated units.

**Smallest correction.** State staffing and capacity, add PR/release/consensus buffers, identify parallel lanes, and rebaseline from the critical path: W5.1 → go/no-go; W5.5 → published canopy path; W1.1/W1.3 → E2E; then CI/observability/docs.

### B2-M11 — The critical-path graph contains false edges and omits real ones

**Claim attacked.** §Dependencies captures sequencing (`:493-502`).

**Evidence.** W0.3 does not depend on W0.2; both can be tested with fixtures. W1.4 does not inherently depend on W1.5. W3.1 (install local packages) should precede or run independently of W3.2, not depend on it. Real edges omitted include W5.5 → published canopy runnability/M1, W1.1 + conditioning choice → CLI E2E, schema transport → W1.3, W5.3 → any `test_r2` band, and owner/semver decision → W1.4.

**Severity: MAJOR.** Following the graph serializes independent work and misses blockers that invalidate milestones.

**Smallest correction.** Rebuild the DAG from acceptance artifacts rather than phase labels and identify the minimum E2E release path.

### B2-M12 — Success metrics and acceptance tests do not establish the stated goals

**Claim attacked.** The metric table operationalises G1–G6.

**Evidence.** `/v1/crossval` 200 proves transport, not chronological/scientific correctness. “Metrics present” proves extraction, not validity. Six route tests do not prove all listed malformed-artifact paths because the list names only five train cases plus crossval. “Unlogged non-2xx = 0” has no enumerated source-of-truth census and W2.5 spans shared middleware.

G2's canopy and CLI real fits have no P1 end-to-end acceptance. G5 requires chronology per entity, but W5.2's “no eval row precedes a train row” is backwards/insufficient: it does not assert every train timestamp is strictly before every eval timestamp per ticker or enforce embargo.

**Severity: MAJOR.** Green acceptance can coexist with the failures the goals claim to close.

**Smallest correction.** Add exact invariants and E2E cases: published-package canopy fit, CLI fit from params, all train times < eval cutoff per entity with embargo, held-out metrics labelled by split, and a checked inventory of non-2xx branches.

### B2-M13 — Template conformance is cosmetic rather than operational

**Claim attacked.** The plan follows `TEMPLATE_DEVELOPMENT_ROADMAP.md`.

**Evidence.** It lacks actionable **Scope & Timeframe** content: dates exist, but staffing/capacity does not. **Implementation Plan** is not the phase-plan link/index the template intends. **Test Coverage Requirements** omits Phase 4 and gives counts inconsistent with rows: P1 says 14, but its named multiplicities exceed or ambiguously combine that count.

**Coverage Goals** gives no current percentages/targets comparable to the template. **Out of Scope** is not tied to findings such as F-D10. Status rows collapse multiple work items with different versions and omit an owner column, making execution status non-traceable.

**Severity: MAJOR.** Required structure exists by heading but does not perform the template's planning/status function.

**Smallest correction.** Add staffing/timeframe assumptions, per-W status or one row per W, complete phase test/coverage targets including P4, and phase detail links or state that this file is itself the detail and remove the template boilerplate claim.

## MINOR

### B2-N1 — One real finding is silently uncovered

F-D10 (`isolated_stack.bash` defaults scratch to `/tmp`) has no W item or explicit out-of-scope disposition. This does not violate the parent rule because no script source is proposed in `/tmp`, but the finding register should mark it accepted/deferred. **Correction:** add a disposition, not necessarily work.

### B2-N2 — W3.7 overclaims closure

W3.7 says it closes F-C1–C4 but adds tests only; behavior changes live in W0.5/W1.3/W1.6. **Correction:** label it regression coverage, not closure.

### B2-N3 — Documentation acceptance is too weak

W4.2 allows “manual”; W4.3/W4.5 say only “Reviewed.” W4.1 tells operators to interpret r² ≈ 0 before W5.1/R5 establish a defensible band. **Correction:** defer scientific interpretation text until R5 and use source-linked doc assertions where practical.

### B2-N4 — Version language is confusing but not inherently contradictory

M0 uses recurrence 0.5.x while M1 targets breaking-capable 0.6.0. That can be intentional phased release planning, but W1.4's behavior change needs the missing semver ruling above. **Correction:** label which changes ship in patch versus minor releases.

## F→W coverage matrix

| Finding family | Covered by work items | Uncovered / disposition problem |
| --- | --- | --- |
| F-E1–E5 | W0.1, W0.2, W0.7, W4.3 | None |
| F-D1–D10 | W0.3, W0.4, W1.6, W1.10, W2.8, W5.4, W5.6, W5.7, W1.11 | **F-D10 uncovered** |
| F-S1–S8 | W1.1, W1.4–W1.6, W2.4, W5.3 | F-S4 is a verified control; F-S6 only partially mitigated despite “Closes” |
| F-P1–P7 | W1.1, W1.2, W1.5, W1.9, W5.2, W5.5, W5.8 | None |
| F-C1–C11 | W0.5, W1.3, W1.6–W1.8, W2.9, W3.7 | F-C9 explicitly future; F-C10 verified control |
| F-L1–L11 | W2.1–W2.7, W2.10, W1.11 | None |
| F-T1–T9 | W0.6, W3.1–W3.7 | None |
| F-X1–X11 | W4.1–W4.6 | None |
| F-SCI1–SCI4 | W5.1–W5.4 | None |

**Orphan W items:** none; every `Closes` token names a real finding. **Misclassified closure:** W3.7 is test coverage rather than a behavioral close; W1.6 does not fully close F-S6.

## Attacks that failed

- The H-9 reference survives: the source design really specifies per-run cache by default and an opt-in `--shared-equities-cache` (`...EXPERIMENTATION-PLAN.md:781`).
- The R-6 reference survives: the source really says equities rows are informational and never gating (`...EXPERIMENTATION-PLAN.md:1241`). The problem is importing that old disposition without revisiting it before product work, not misquotation.
- `EXIT_ACCEPTANCE` exists at `util/experiments/run_experiment.py:215`; W0.3 does not invent the constant.
- `juniper-canopy/src/dataset_schema.py` exists. W1.3 is under-specified in how runtime schema reaches the backend, not based on a nonexistent file.
- `juniper_observability.RequestIdMiddleware` exists and is publicly exported. W2.2's dependency is real.
- `/v1/training/status` already exists at `juniper_recurrence/routers/training.py:108`; W1.6 extends an existing route rather than inventing an undocumented route.
- The plan respects the three-way `train|val|test` contract and tolerates absence of `*_full`; W0.6 specifically tests a no-`_full` artifact. It does not require retired keys absent globally.
- No proposed script source lives in `/tmp`; F-D10 concerns runtime scratch, which the parent rule permits.
- The References section names every document it calls by role, including procedure, template, design, persistence design, parent guide, and repo guides. It satisfies the “name every document” rule.
- The status table broadly matches phase assignments; its defect is aggregation/actionability, not mismatched phase numbers.

## Verdict

The plan is not executable in its advertised order. It postpones both the published-package blocker and the go/no-go scientific investigation until P5, while claiming P1 is runnable; one P5 item relies on a nonexistent YAML acceptance facility. P0 is overfilled, internally phase-inverted, and dated more tightly than its own size labels permit.

The minimum rescue is to run W5.1 immediately after a minimal env repair, promote W5.5 and W1.1 into the runnable critical path, specify real end-to-end acceptance for both entry points, and rebuild the dependency graph and milestones around published artifacts rather than headings.
