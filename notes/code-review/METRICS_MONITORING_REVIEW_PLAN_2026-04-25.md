# Juniper Metrics & Monitoring — Comprehensive Code Review Plan

**Status:** PROPOSED (awaiting kickoff)
**Owner:** Paul Calnon (project)
**Date:** 2026-04-25
**Scope:** Metrics, monitoring, observability, telemetry, health surface
**Repos in scope (6):** juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client
**Companion documents:**

- [METRICS_MONITORING_ANALYSIS_2026-04-25.md](METRICS_MONITORING_ANALYSIS_2026-04-25.md) — current-state baseline (the inventory this plan consumes)
- [METRICS_MONITORING_ROADMAP_2026-04-25.md](METRICS_MONITORING_ROADMAP_2026-04-25.md) — prioritized work breakdown

---

## 1. Purpose

Establish a **rigorous, repeatable, evidence-based code review** of the metrics and monitoring surface across the six in-scope Juniper applications, ahead of release. The review must:

1. **Inventory and validate** every piece of observability functionality — endpoints, metric definitions, payload schemas, instrumentation hooks, log formatters, dependency probes, dashboard wiring.
2. **Map** the resources, infrastructure, and dependencies (libraries, CI gates, scrape config, alerting hooks) on which the surface depends.
3. **Identify** every problem and gap, **categorize** under the agreed issue taxonomy, **score** under the agreed risk model, and document **multiple remediation options** per root cause with weighted recommendations.
4. **Assess testing**: that tests exist, that they are not disabled or gated, that they actually validate target behavior (not merely exercise endpoints), and that coverage is sufficient.
5. **Verify the full test suite passes** for each repo without collection/implementation/runtime errors, runtime warnings, or criteria failures.
6. Produce per-repo deliverables in each app's `notes/` directory plus this consolidated plan.

This plan is the **single source of truth** for methodology, phase gating, sub-agent assignments, finding templates, traceability, and exit criteria.

---

## 2. Scope and boundaries

| In scope                                                                                                | Out of scope (unless directly defective)                |
|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| Production Python implementing or instrumenting metrics/monitoring/health/telemetry                     | Application business logic that does not emit metrics   |
| Pydantic/dataclass schemas for metric payloads, health responses, WS metric frames                      | Generic CRUD endpoints with no observability angle      |
| Prometheus middleware, Sentry hooks, JSON log formatters, RequestID propagation                         | Dashboard layout configuration unrelated to metric data |
| WebSocket frames carrying metric/state/topology payloads (cascor → consumers)                           | Network library internals (websockets, urllib3)         |
| Tests covering observability code; CI gating of those tests                                             | Test infrastructure unrelated to observability          |
| `pyproject.toml` extras and dependency pins relevant to monitoring                                      | Unrelated dependency hygiene                            |
| `juniper-deploy` Prometheus/Grafana/ServiceMonitor scrape config (referenced)                           | Compose orchestration unrelated to monitoring           |
| Documentation that asserts behavior of the metrics surface                                              | Prose docs unrelated to monitoring                      |

**Out of scope.** Refactors driven by aesthetics rather than defects. Architectural changes whose blast radius exceeds the review window. Dashboards in juniper-canopy that visualize metrics but do not affect their correctness.

---

## 3. Issue taxonomy

Every finding gets **one primary category** (secondary tags allowed) drawn from the standard project taxonomy:

| Category                          | Examples specific to this review                                                                                                                                  |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Architectural**                 | Duplicated `DependencyStatus`/`ReadinessResponse` across 3 repos; absence of shared observability lib; probe direction asymmetry; client/worker observability gap |
| **Logical / correctness**         | Cardinality fallback to raw URL path; readiness 200-on-degraded; liveness no-op; replay-buffer overflow undefined; demo-mode gauge drift                          |
| **Syntactic**                     | Mis-typed Prometheus label names; broken metric registration; import-time failures masked by `importorskip`                                                       |
| **Code smells**                   | Hardcoded buffer sizes; magic numbers in histogram buckets; sync I/O in async; numeric defaults without validators                                                |
| **Departure from requirements**   | Documented endpoints that don't fire metrics they claim; documented health semantics not implemented (live = no-op)                                               |
| **Deviation from best practices** | `importorskip` on Sentry; no SLO/SLI tied to metrics; no scrape config; no schema validation on inbound WS frames; no end-to-end metric tests                     |
| **Formatting and linting**        | Black/isort/flake8 violations under `[tool.*]` line-length=512 in observability files                                                                             |

---

## 4. Risk and severity model

Each finding scored on five axes. Numbers are 1–5 unless otherwise noted.

| Axis                   | Definition                                      | 1 (low)         | 5 (high)                         |
|------------------------|-------------------------------------------------|-----------------|----------------------------------|
| **Risk profile**       | Production blast radius if defect manifests     | Cosmetic        | Service outage / data loss       |
| **Severity**           | User-facing impact when triggered               | Internal-only   | User-visible / silent corruption |
| **Likelihood**         | Probability of triggering in the release window | Hypothetical    | Already observed                 |
| **Scope**              | How many repos / components affected            | Single function | Cross-repo                       |
| **Remediation effort** | Engineer-days to fix with tests                 | < 0.5 day       | > 5 days / requires design       |

**Composite severity** = max(Risk, Severity, Likelihood). Findings with composite ≥ 4 are **release-blocking**. Findings with composite 3 are **must-have for next release**. Composite ≤ 2 are tracked but non-blocking.

---

## 5. Standard workflow per finding

```mermaid
flowchart LR
  D[Discover] --> R[Record]
  R --> V[Validate by reproduction or independent review]
  V --> S[Score]
  S --> O[Remediation options 2..N]
  O --> Rec[Recommend with weighting]
  Rec --> Wr[Write to plan]
```

### 5.1 Finding template

```markdown
### METRICS-MON-NNN — <one-line title>

**Repo:** <repo>
**File(s):** <path:line>
**Category:** <primary> [<secondary tags>]
**Risk / Severity / Likelihood / Scope / Effort:** R / S / L / Sc / E (composite: C)

**Statement of issue.** <2–4 sentences.>

**Validation evidence.** <reproduction steps, command output, test failure, or named reviewer's independent confirmation.>

**Root cause.** <Explicit; not "looks wrong".>

**Remediation options.**
1. **Option A — <name>.** Description. Strengths / Weaknesses / Risks / Guardrails.
2. **Option B — <name>.** Description. Strengths / Weaknesses / Risks / Guardrails.
3. **Option C — <do nothing / accept>.** Strengths / Weaknesses / Risks / Guardrails.

**Recommendation.** <Option chosen + rationale weighted against axes.>

**Tests required.** <Concrete test names / files; assertion-level description.>

**Traceability.** Links to PR, issue, BUG-XX-NN entry, AGENTS.md update.
```

---

## 6. Phased execution

The review is split into **eight phases**. Phase gates are mandatory; phases must complete in order, except where explicitly parallel.

### Phase 0 — Kickoff and tooling baseline (0.5 day)

**Goal.** Confirm baseline; pin commits; provision sub-agents.

- [ ] Capture HEAD SHA per repo into the plan footer.
- [ ] Confirm conda envs exist (`JuniperCanopy`, `JuniperCascor`, `JuniperData`) and dependencies install clean.
- [ ] Run baseline test suites; record baseline pass/fail per repo. Failures here are pre-existing, not introduced by review.
- [ ] Verify pre-commit hooks pass on each repo HEAD.
- [ ] Confirm none of the in-scope tests are gated/skipped at CI level (capture list of skipped/xfail/disabled).

**Exit gate.** Baseline document signed off; sub-agent task list seeded.

### Phase 1 — Functional inventory deepening (parallel, 1.5 days)

**Goal.** Convert the survey-level inventory in the analysis baseline into a complete, file-line-referenced functional spec for each repo's observability surface.

**Sub-agent assignments (parallel):**

| Sub-agent          | Repo                   | Deliverable                                                                                                                                 |
|--------------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `Explore` (cascor) | juniper-cascor         | `juniper-cascor/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`                                                                                |
| `Explore` (canopy) | juniper-canopy         | `juniper-canopy/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`                                                                                |
| `Explore` (data)   | juniper-data           | `juniper-data/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`                                                                                  |
| `Explore` (cli/wk) | cascor-client + worker | `juniper-cascor-client/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md` and `juniper-cascor-worker/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md` |
| `Explore` (dc)     | juniper-data-client    | `juniper-data-client/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`                                                                           |

**Each functional spec must enumerate:**

1. Every metric (name, type, labels, description, units, scrape path).
2. Every health endpoint (path, method, response model, dependencies probed, status codes).
3. Every WebSocket frame carrying observability data (type, schema, sequence semantics).
4. Every test that asserts metric or health behavior, with assertion summary.
5. Every middleware/hook (Prometheus, Sentry, RequestID, JSON formatter).
6. Every Prometheus/Sentry-related dependency and its pin.
7. Every cross-repo emit/consume relationship.

**Exit gate.** Specs reviewed for completeness; gaps from analysis baseline reconciled.

### Phase 2 — Resource, infrastructure, and dependency review (1 day)

**Goal.** Validate the substrate the metrics depend on.

- [ ] Audit `pyproject.toml` `[project.optional-dependencies]` per repo — confirm `prometheus-client`, `sentry-sdk` versions and bounds; check for known CVEs.
- [ ] Inspect `juniper-deploy` for Prometheus/Grafana/ServiceMonitor manifests; confirm scrape targets match `/metrics` paths; confirm port mappings (8050, 8100, 8201) align with documented service ports.
- [ ] Confirm CI gates: `.github/workflows/ci.yml` per repo runs observability tests; capture which jobs run them and which can be bypassed.
- [ ] Inspect Helm charts (if present) for liveness/readiness probe wiring; confirm probe paths match implemented endpoints; confirm probe failure thresholds are sensible.
- [ ] Check secrets management: `SENTRY_DSN`, `JUNIPER_DATA_API_KEY`, etc. — sourced from SOPS-encrypted env or runtime secrets manager?

**Exit gate.** Dependency / infra inventory documented in this plan's appendix; CVEs (if any) escalated.

### Phase 3 — Problem and gap identification (parallel, 2 days)

**Goal.** Apply the issue taxonomy and risk model to every concern surfaced by the analysis baseline plus newly-discovered issues. Produce numbered findings.

**Sub-agent assignments (parallel, one per repo for findings authoring; results consolidated):**

| Sub-agent         | Focus                                                                                 |
|-------------------|---------------------------------------------------------------------------------------|
| `general-purpose` | Cardinality fallback in 3 server middlewares (one finding per repo, share root cause) |
| `general-purpose` | Liveness/readiness contract violations across cascor, canopy, data                    |
| `Explore`         | Client/worker observability gap (architectural finding)                               |
| `Explore`         | Schema validation absence on inbound WS frames in cascor-client and worker            |
| `general-purpose` | Test-suite gap audit (skipped, mocked-only, missing end-to-end)                       |
| `Plan`            | Architectural finding: shared observability lib opportunity vs status-quo cost        |

Findings written into a dedicated section of this plan (§9), each using the §5.1 template. The roadmap consumes these IDs.

**Exit gate.** Every finding scored, validated, and assigned; no orphan concerns from baseline.

### Phase 4 — Test coverage and correctness audit (1.5 days)

**Goal.** Establish that tests do what they claim and that gaps are explicit.

For each repo:

- [ ] Run full test suite (unit + integration + regression + perf where present + security where present). Record pass/fail/skip/xfail. Any skip not justified by a documented reason is a finding.
- [ ] For every observability test, audit whether the assertion validates **correctness** (e.g., specific label set on Counter, specific bucket selected by Histogram, specific transition triggered) or merely **existence** (e.g., status code 200, endpoint did not crash). Existence-only tests are findings.
- [ ] Identify code paths in observability modules with **no test coverage** at all (`coverage` tool, branch mode where supported).
- [ ] Verify tests do not silently swallow failures (e.g., `try/except: pass` in fixtures).
- [ ] Confirm `pytest.importorskip("sentry_sdk")` usages either become unconditional or are documented as deliberate optionality.
- [ ] Identify missing test types: e2e WS metric flow (cascor → canopy), cardinality stress test, scrape-format validation, log-format snapshot.

**Exit gate.** Coverage matrix in §10 fully populated; gap list complete.

### Phase 5 — Remediation design (parallel by repo, 2 days)

**Goal.** Propose 2–N remediation options per finding with explicit trade-offs and a recommendation.

**Per-finding requirements:**

- Each remediation option includes: code sketch (function signatures, file edits, new tests required) — sketches, not full PRs.
- Strengths, weaknesses, risks, guardrails enumerated.
- Recommended option chosen by weighing risk/severity/effort/scope.
- Where multiple findings share a root cause, propose **one** unified remediation with cross-references.

Sub-agent split (parallel):

| Sub-agent         | Cluster                                                                |
|-------------------|------------------------------------------------------------------------|
| `Plan`            | Cardinality strategy (3 server repos, 1 unified design)                |
| `Plan`            | Health probe semantics + status-code propagation (3 server repos)      |
| `Plan`            | Worker liveness + heartbeat design                                     |
| `Plan`            | Client WS frame schema validation + version-tag handshake              |
| `Plan`            | Shared observability library proposal (`juniper-observability` extras) |
| `general-purpose` | Test-gap closure plan (per-repo)                                       |

**Exit gate.** Every release-blocking finding has a recommended remediation with effort estimate.

### Phase 6 — Validation (1 day)

**Goal.** Independent confirmation by a separate sub-agent that the work is sound.

- [ ] Spawn a fresh validation sub-agent (no prior session context) that reads the plan + analysis + roadmap and reports inconsistencies, missing evidence, or unsupported recommendations.
- [ ] Validation sub-agent re-runs each repo's full test suite from a clean checkout to confirm baseline pass.
- [ ] Validation sub-agent independently spot-checks 10 randomly-selected findings: confirms file:line references, reproduces evidence, agrees with category/score.
- [ ] Validation sub-agent reviews the §9 finding section for taxonomy/score consistency.

**Exit gate.** Validation report signed off; corrections (if any) merged into the plan.

### Phase 7 — Correction and finalization (variable)

**Goal.** Apply only the documentation, infrastructure, and code corrections that the review flags as in-scope and immediately required to validate the plan itself (this is **not** the implementation phase — that is in the roadmap).

In-scope corrections at this phase:

- Updating analysis/plan/roadmap documents per validation feedback.
- Restoring CI gates if review revealed observability tests were silently skipped.
- Documenting AGENTS.md / CLAUDE.md inconsistencies discovered during review.
- Fixing trivial lint/format issues blocking CI from running observability tests.

Out of scope at this phase:

- Implementation of remediations (executed via the roadmap, in separate worktrees, by separate PRs).

**Exit gate.** Plan, analysis, roadmap docs final; CI green per repo on baseline branch.

---

## 7. Deliverables (per phase)

| Phase | Deliverable                                                                   | Location                                                        |
|-------|-------------------------------------------------------------------------------|-----------------------------------------------------------------|
| 0     | Baseline SHA + test-suite baseline log                                        | This plan, Appendix A                                           |
| 1     | Per-repo functional spec (×6)                                                 | `<repo>/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`            |
| 2     | Resource/infra/dependency inventory                                           | This plan, Appendix B                                           |
| 3     | Numbered findings (METRICS-MON-NNN)                                           | This plan, §9                                                   |
| 4     | Test coverage matrix                                                          | This plan, §10                                                  |
| 5     | Remediation options + recommendations per finding                             | This plan, §9 (per finding)                                     |
| 6     | Validation report                                                             | `notes/code-review/METRICS_MONITORING_VALIDATION_2026-04-25.md` |
| 7     | Corrected plan + analysis + roadmap documents; PR(s) for in-scope corrections | This worktree; PR(s) per repo as applicable                     |

Roadmap document drives implementation phases beyond this review; tracked separately at [METRICS_MONITORING_ROADMAP_2026-04-25.md](METRICS_MONITORING_ROADMAP_2026-04-25.md).

---

## 8. Sub-agent strategy

**Why sub-agents.** The six repos are independent enough to parallelize, and the main thread's context budget cannot hold full-fidelity inspection of all six simultaneously. Sub-agents protect main-thread context and allow concurrent file-level work.

**Selection rules.**

- **`Explore`** — for "what exists where" inventory work (Phase 1, parts of Phase 3).
- **`Plan`** — for design-level work proposing remediations (Phase 5).
- **`general-purpose`** — for multi-step investigations that may need to read, edit, run tests (Phases 3, 4, 7).
- **A separate, fresh agent** for Phase 6 validation — must not have seen earlier session context.

**Anti-pattern guard.** Do not spawn a sub-agent to "fix the metrics review" as a single-shot task. Each sub-agent is given a self-contained, narrowly-scoped prompt with: target file paths, specific question, expected output format, word cap.

**Worktree discipline.** When implementation work begins (post-roadmap), each repo gets its own worktree under the centralized location per the project's Worktree Procedures.

---

## 9. Findings register

Findings are populated during Phase 3 and refined through Phase 5. The structure is:

```text
METRICS-MON-001 ... NNN
```

Each follows the §5.1 template. Cross-references to existing bug ledger entries (`BUG-CC-07`, `BUG-JD-06`, `BUG-JD-07`, `BUG-JD-09`) are mandatory where applicable. **This section is intentionally empty in the proposed plan; it is populated during execution.**

Provisional finding seeds (to be confirmed/expanded during Phase 3):

| Seed ID | Title                                                                                       | Repo(s)                                  | Tentative category   | Tentative composite |
|---------|---------------------------------------------------------------------------------------------|------------------------------------------|----------------------|:-------------------:|
| seed-01 | Prometheus middleware cardinality fallback to raw URL path                                  | cascor, canopy, data                     | Logical              | 4                   |
| seed-02 | `/health/ready` returns 200 when `overall="degraded"`                                       | cascor (and parity check elsewhere)      | Departure from req'd | 4                   |
| seed-03 | Liveness probe is a no-op                                                                   | data (verify cascor/canopy)              | Logical              | 3                   |
| seed-04 | No worker liveness or heartbeat instrumentation                                             | cascor-worker                            | Architectural        | 4                   |
| seed-05 | No schema validation on inbound WS metric/state frames                                      | cascor-client, cascor-worker             | Best practices       | 3                   |
| seed-06 | Duplicated `DependencyStatus`/`ReadinessResponse` across 3 repos                            | cross-repo                               | Architectural        | 3                   |
| seed-07 | Replay-buffer overflow behavior undocumented and untested                                   | cascor                                   | Code smell           | 2                   |
| seed-08 | Dataset-generation metric only mocked; no live integration test (BUG-JD-07)                 | data                                     | Test gap             | 3                   |
| seed-09 | Sentry tests gated behind `importorskip`; regressions invisible when extra not installed    | cascor, canopy, data                     | Best practices       | 2                   |
| seed-10 | Blocking `urlopen()` inside async health probe                                              | canopy (verify others)                   | Logical              | 3                   |
| seed-11 | `set_demo_mode_active()` not integration-tested; gauge can drift from real state            | canopy                                   | Test gap             | 2                   |
| seed-12 | `_create_metrics_panel` test skipped with note "not exposed as public API"                  | canopy                                   | Test gap             | 2                   |
| seed-13 | No data-client request instrumentation; callers must wrap                                   | data-client                              | Architectural        | 2                   |
| seed-14 | Histogram buckets selected without documented latency-target rationale                      | cascor, canopy, data                     | Best practices       | 2                   |
| seed-15 | Probe direction asymmetric (canopy probes others; reverse not done)                         | cross-repo                               | Architectural        | 2                   |

---

## 10. Test coverage matrix (template)

To be populated in Phase 4. Each cell either references an asserting test (file:line) or is marked **GAP**.

| Behavior to assert                                          | cascor | canopy | data | client | worker | data-client |
|-------------------------------------------------------------|:------:|:------:|:----:|:------:|:------:|:-----------:|
| `/metrics` Prometheus scrape format valid                   |        |        |      |   —    |   —    |      —      |
| Cardinality bounded under unmatched routes                  |        |        |      |   —    |   —    |      —      |
| Liveness probe checks actual code path                      |        |        |      |   —    |   —    |      —      |
| Readiness 503 when overall degraded                         |        |        |      |   —    |   —    |      —      |
| Sentry hook fires on uncaught exception                     |        |        |      |        |        |             |
| RequestID propagated from HTTP to logs                      |        |        |      |   —    |   —    |             |
| WS metric frame schema validated end-to-end                 |        |        |  —   |        |        |      —      |
| Replay buffer overflow behavior                             |        |   —    |  —   |   —    |   —    |      —      |
| Worker heartbeat / in-flight task count                     |   —    |   —    |  —   |   —    |        |      —      |
| Dataset-gen metric live integration                         |   —    |   —    |      |   —    |   —    |      —      |
| Demo-mode gauge drift                                       |   —    |        |  —   |   —    |   —    |      —      |
| Histogram bucket selection covers SLO target                |        |        |      |   —    |   —    |      —      |

`—` = N/A for this repo.

---

## 11. Exit criteria for the review (release-readiness gate)

The review is complete when **all** of the following hold:

1. **All in-scope functionality** is documented in the per-repo functional specs (Phase 1).
2. **All identified problems** are categorized, scored, validated, and have remediation recommendations (Phases 3, 5).
3. **All user-visible behavior** for documented endpoints matches the documentation (or a deviation finding exists).
4. **No tests are disabled, commented out, or gated** without an explicit, accepted justification recorded in the plan.
5. **All tests are verified to assert correctness**, not merely existence.
6. **All test-coverage gaps** are enumerated in §10.
7. **Full test suites pass** (unit, integration, regression, e2e where applicable, performance where applicable, security where applicable) per repo, with **zero collection errors, zero implementation errors, zero runtime errors, zero runtime warnings, zero criteria failures**.
8. **Phase 6 validation report** is signed off with no open dissent.
9. **Roadmap** has consumed every finding ID and produced an execution sequence.

---

## 12. Constraints, conventions, and procedures

- **Worktree procedures** (mandatory): all implementation work — including any in-scope corrections in Phase 7 — uses centralized worktrees per `notes/WORKTREE_SETUP_PROCEDURE.md` and `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.
- **Thread handoff** (mandatory): if context utilization exceeds 80% or is projected to exceed 90% before the current task completes, perform a thread handoff per `notes/THREAD_HANDOFF_PROCEDURE.md`. Write the handoff prompt under `juniper-ml/prompts/thread-handoff_automated-prompts/` and invoke `juniper-ml/scripts/wake_the_claude.bash` with `--worktree <name> --effort high --dangerously-skip-permissions`. Cease operation once `wake_the_claude.bash` is called.
- **Line length**: 512 across all linters per cross-repo conventions.
- **Pre-commit**: must pass on every commit; do not bypass with `--no-verify`.
- **Commit/PR cadence**: small, focused PRs per finding cluster; **never merge directly to main**; create PR per worktree-cleanup-v2.

---

## 13. Validation requirements (Phase 6, expanded)

Phase 6 must verify, by a fresh sub-agent:

- **Work performed** — every claimed file:line reference exists; every claimed test exists and runs; every recorded test result is reproducible.
- **Analyses completed** — every score is defensible against the §4 model; every remediation option has the required strengths/weaknesses/risks/guardrails block; every recommendation cites the axes that drove it.
- **Documentation compiled** — analysis, plan, roadmap, per-repo functional specs are internally consistent; cross-references resolve; AGENTS.md updates (if any) match the implemented behavior.

If validation surfaces a discrepancy, the **document is corrected first** (analysis/plan/roadmap), then code/infra (per the roadmap, not this plan).

---

## 14. Cleanup (post-review)

After the review (and any in-scope Phase 7 corrections) merge:

1. Commit, push, and open PRs for any document/code/infra changes.
2. After PRs merge, perform Worktree Cleanup V2 per `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` (Phase 1–4) for the worktree(s) created during review.
3. Run `git worktree prune` and confirm no stale worktrees remain.
4. Capture post-review HEAD SHAs in this plan's Appendix A so the roadmap has a stable starting point.

---

## Appendix A — Baseline (to be filled at Phase 0)

| Repo                  | HEAD SHA | Branch | Test-suite baseline | Pre-commit baseline |
|-----------------------|----------|--------|---------------------|---------------------|
| juniper-canopy        |          |        |                     |                     |
| juniper-cascor        |          |        |                     |                     |
| juniper-cascor-client |          |        |                     |                     |
| juniper-cascor-worker |          |        |                     |                     |
| juniper-data          |          |        |                     |                     |
| juniper-data-client   |          |        |                     |                     |

---

## Appendix B — Resource / infra / dependency inventory (to be filled at Phase 2)

| Resource                                  | Per-repo state | Findings |
|-------------------------------------------|----------------|----------|
| `prometheus-client` pin                   |                |          |
| `sentry-sdk` pin                          |                |          |
| `sentry-sdk[fastapi]` pin                 |                |          |
| Prometheus scrape config (juniper-deploy) |                |          |
| Grafana dashboards (juniper-deploy)       |                |          |
| Helm liveness/readiness probe wiring      |                |          |
| CI observability test gating              |                |          |
| SOPS-managed secrets (Sentry DSN, etc.)   |                |          |

---

## Appendix C — Sub-agent prompt skeletons

**Phase 1 functional-spec prompt (per repo):**

You are auditing the metrics/monitoring functional surface of `<repo>` at HEAD `<sha>`.
Produce a functional spec at `<repo>/notes/METRICS_FUNCTIONAL_SPEC_2026-04-25.md`.

Enumerate:

1. every metric — name, type, labels, units, scrape path
2. every health endpoint — path, response model, dependencies probed, status codes
3. every WS frame carrying observability data
4. every test asserting metric/health behavior with assertion summary
5. every middleware/hook
6. every Prom/Sentry dependency and pin
7. every cross-repo emit/consume relationship

Use grep/glob aggressively; cite file:line for every claim. Cap output at 5000 words. Do not propose changes. Do not edit code.

**Phase 3 finding-authoring prompt:**

> Author findings METRICS-MON-NNN for `<finding cluster>` per the template in §5.1 of `notes/code-review/METRICS_MONITORING_REVIEW_PLAN_2026-04-25.md`. For each, provide: statement, validation evidence (reproducible), root cause, score per §4 axes. Do not propose remediations yet — that is Phase 5. Cite file:line; do not invent paths.

**Phase 5 remediation prompt:**

> For findings `<list>`, propose 2–N remediation options each per the template in §5.1. Include code sketches (signatures + file edits + new tests). Enumerate strengths/weaknesses/risks/guardrails per option. Recommend one option per finding, weighted against the §4 axes. Where findings share a root cause, propose a unified remediation. Do not implement; output is a design.

**Phase 6 validation prompt:**

You are a fresh validation agent with no prior context.
Read `notes/code-review/METRICS_MONITORING_{ANALYSIS,REVIEW_PLAN,ROADMAP}_2026-04-25.md`.

Re-verify:

1. every file:line reference exists in the named repo at the named SHA
2. every claimed test exists and passes
    - ensure that the actual testing functionality is not:
      - disabled
      - commented out
      - gated to not run
      - in any other manner, rendered ineffective
3. every score is defensible per the model in §4
4. the documents are internally consistent.
    - Spot-check five random findings end-to-end
    - Report the following as a list of corrections:
      - inconsistencies
      - missing evidence
      - unsupported claims
5. Do not edit any documents — propose corrections only.
