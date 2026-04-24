# Metrics & Monitoring Code Review — Ecosystem Roadmap

**Scope**: juniper-canopy, juniper-cascor, juniper-cascor-client, juniper-cascor-worker, juniper-data, juniper-data-client
**Focus**: Metrics & monitoring (functionality, resources, infrastructure, dependencies, problems, gaps, testing)
**Author**: Paul Calnon (lead developer)
**Created**: 2026-04-24
**Last revised**: 2026-04-24 (post-audit pass)
**Status**: Draft v2 — planning + per-plan audit corrections applied;
reviews not yet executed

---

## 1. Purpose

This roadmap sequences and coordinates six per-app code review plans (one per
target application). Each per-app plan is the authoritative work artifact for
that application; this document exists to:

- Sequence the per-app reviews in dependency order so upstream contracts are
  validated before downstream consumers are reviewed.
- Capture cross-cutting concerns (data contract, ports, env vars, shared
  observability libraries) that no single per-app review owns.
- Define the ecosystem-wide validation gates that must pass before this review
  cycle is considered complete.
- Establish the issue-classification framework, severity rubric, and
  remediation-evidence requirements that all per-app plans inherit.

This document does **not** duplicate per-app inventories or per-app remediation
plans — those live in the per-app plan files
(`<app>/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md`).

---

## 2. Per-app plan index

| # | Application | Plan path (target) | Staging copy in this worktree |
|---|-------------|-------------------|-------------------------------|
| 1 | juniper-data | `juniper-data/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `01_juniper-data.md` |
| 2 | juniper-data-client | `juniper-data-client/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `02_juniper-data-client.md` |
| 3 | juniper-cascor | `juniper-cascor/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `03_juniper-cascor.md` |
| 4 | juniper-cascor-worker | `juniper-cascor-worker/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `04_juniper-cascor-worker.md` |
| 5 | juniper-cascor-client | `juniper-cascor-client/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `05_juniper-cascor-client.md` |
| 6 | juniper-canopy | `juniper-canopy/notes/CODE_REVIEW_PLAN_METRICS-AND-MONITORING.md` | `06_juniper-canopy.md` |

The ordering is deliberate (see §4).

### 2.1 Reference catalogs (added 2026-04-24)

| File | Purpose |
|------|---------|
| `07_ENV_VAR_INVENTORY.md` | All 70 observability-related env vars across the 6 apps, grouped and flagged. Feeds §5.3 and §5.4. |
| `08_METRIC_CATALOG.md` | All 38 Prometheus metrics defined across the 3 FastAPI services, with emission status. Feeds §5.7, §5.9, §5.10. |

These two catalogs are **living documents**. Re-generate before each
review pass if the code has moved.

---

## 3. Issue-classification framework (inherited by every per-app plan)

### 3.1 Issue type taxonomy

Every finding in every per-app review must be assigned exactly one of the
following types:

| Type | Definition |
|------|------------|
| **Architectural** | Structural problems crossing module/process/service boundaries: wrong layering, leaky abstractions, race-prone designs, missing isolation. |
| **Logical** | Bug in business logic — code does the wrong thing for some input or state. |
| **Syntactical** | Code does not parse or violates language rules; usually surfaced by compiler/parser/linter. |
| **Code Smell** | Maintainability problem: dead code, duplication, deep nesting, over-broad except, magic numbers, large functions. |
| **Departure from Requirements** | Behavior diverges from a documented requirement (CLAUDE.md, README, OpenAPI contract, parent CLAUDE.md). |
| **Deviation from Best Practices** | Project- or community-standard violations not otherwise enumerated (missing histogram buckets, label-cardinality risk, fire-and-forget IO, missing timeouts). |
| **Formatting & Linting** | Pre-commit / linter / formatter violations only; no semantic impact. |

Findings that span multiple types should be split into multiple findings.

### 3.2 Issue characteristics — required for every finding

| Characteristic | Scale / definition |
|----------------|---------------------|
| **Risk profile** | What can go wrong if left unfixed (one of: data loss, observability blackout, performance degradation, security exposure, user-visible regression, cleanup-only). |
| **Severity** | `Critical` (release-blocker), `High` (should not ship), `Medium` (fix before next minor), `Low` (cleanup), `Informational` (note only). |
| **Likelihood** | `Certain` (will occur on every run), `Likely` (will occur under normal load), `Possible` (will occur under specific conditions), `Unlikely` (requires unusual state). |
| **Scope** | `In-process`, `Cross-process`, `Cross-service`, `Cross-repo`, `External-facing`. |
| **Remediation effort** | `Trivial` (<1 hr), `Small` (<1 day), `Medium` (1–3 days), `Large` (>3 days, may need design). |

A combined **Priority** label may be derived as `Severity × Likelihood`, but
the five raw characteristics must be recorded individually so future readers
can re-prioritize.

### 3.3 Remediation framework

For every finding ranked Medium or higher, the per-app plan must capture:

1. **Root cause analysis** — what underlying decision/omission produced the
   finding; not the symptom.
2. **Remediation options** — at least one, ideally two-to-three for
   Critical/High findings, each with:
   - Description of code/config change
   - Strengths
   - Weaknesses
   - Risks introduced by the fix itself
   - Guardrails (tests, monitoring, feature flags) that must accompany the fix
3. **Recommended approach** — explicit recommendation with the reasoning that
   weighs the trade-offs.
4. **Validation plan** — how the fix will be proven correct (specific tests
   to add or run, manual verification steps, metrics to observe post-deploy).

Low/Informational findings may be captured as a single line.

---

## 4. Sequencing & rationale

The per-app reviews are sequenced in **dependency-graph order** so that
upstream contract drift is identified before downstream consumers are
re-validated against it.

```
Phase A (Foundation contracts)
    1. juniper-data            — observability surface of upstream data service
    2. juniper-data-client     — client-side instrumentation for that contract
Phase B (Core service)
    3. juniper-cascor          — primary metrics producer; biggest surface
    4. juniper-cascor-worker   — distributed metric emitter, feeds (3)
Phase C (Consumers)
    5. juniper-cascor-client   — REST + WebSocket metric consumer
    6. juniper-canopy          — end-user dashboard; aggregates (1) + (3)
Phase D (Cross-cutting)
    7. Ecosystem-level validation (this document, §6)
```

Reviewers may parallelize within a phase but should not enter Phase B before
Phase A reviews are complete enough to lock the contracts in writing.

---

## 5. Cross-cutting concerns (owned by this roadmap, not any single app)

The following are explicitly out-of-scope for individual per-app reviews and
must be treated here so no concern falls through the cracks.

### 5.1 Service ports & endpoint contract

Source of truth: `Juniper/CLAUDE.md` "Service Ports" table.

| Service | Host port | Container port | Health endpoint |
|---------|-----------|----------------|-----------------|
| juniper-data | 8100 | 8100 | `/v1/health` |
| juniper-cascor | 8201 | 8200 | `/v1/health` |
| juniper-canopy | 8050 | 8050 | `/v1/health` |

**Cross-cutting check**: every per-app plan must verify port and health-path
references match this table; mismatches are flagged as
`Departure from Requirements`.

### 5.2 Standardized observability libraries

The surveys revealed that the three FastAPI services (juniper-data,
juniper-cascor, juniper-canopy) each implement their own `observability.py`
with overlapping but **not identical** Prometheus-middleware shapes (label
sets, histogram buckets, metric naming conventions). The cross-cutting
concern is whether to:

- **Option A**: Continue duplicated implementations (current state).
- **Option B**: Extract a shared `juniper-observability` micro-library.
- **Option C**: Standardize via convention (documented contract in
  `juniper-ml/docs/REFERENCE.md`) without code sharing.

This roadmap does not pre-decide; the per-app plans should each surface
naming/bucket/cardinality drift as Findings, and the post-review synthesis
(§7) chooses among A/B/C with full evidence.

### 5.3 Environment-variable conventions

Surveys + audit found inconsistent env-var prefixing:

- juniper-canopy: `JUNIPER_CANOPY_*`, with legacy `CASCOR_*` aliases
  emitting deprecation warnings (multiple validators in `settings.py`)
- juniper-cascor: `JUNIPER_CASCOR_*` **plus** `JUNIPER_WS_*` alias
  via Pydantic `AliasChoices` (settings.py:138, 144) — a second
  prefix for the same fields, currently undocumented
- juniper-data: `JUNIPER_DATA_*` (clean)
- juniper-cascor-worker: **bare** `CASCOR_*` (no `JUNIPER_` prefix)
- juniper-cascor-client: bare `JUNIPER_CASCOR_*` (clean)
- juniper-data-client: `JUNIPER_DATA_API_KEY` only (clean)

**Cross-cutting check**: catalog every observability-related env var across
all six apps, flag prefix inconsistencies, and recommend a normalization
plan in the post-review synthesis. The cascor `JUNIPER_WS_*` alias is
the most recent surprise — decide whether to keep, deprecate, or
document as a stable second name.

### 5.4 Metrics-disabled-by-default risk

juniper-data (`JUNIPER_DATA_METRICS_ENABLED=false`), juniper-cascor
(`JUNIPER_CASCOR_METRICS_ENABLED=false`), and juniper-canopy
(`metrics_enabled=false`) all default Prometheus exposition **off**.

**Cross-cutting question for the synthesis**: should release defaults flip
to `true` so production deployments have metrics out-of-the-box? Per-app
plans flag the symptom; the synthesis owns the policy choice.

### 5.5 WebSocket framing & metric streaming protocol

juniper-cascor (`/ws/training`), juniper-canopy (`/ws/train`, `/ws/control`),
and juniper-cascor-client/juniper-cascor-worker all hand-roll WebSocket
message envelopes. There is no central schema document; the cross-cutting
concern is **schema drift between producer and consumer**. Each per-app
plan documents its local view; this roadmap demands a unified schema audit
in the synthesis phase.

### 5.6 `/metrics` endpoint security posture (added 2026-04-24)

The audit pass surfaced the same finding in three independent reviews:

- juniper-data H11 — `/metrics` not in `EXEMPT_PATHS`; behavior depends
  on whether auth is enabled, undocumented either way
- juniper-cascor H15 — `make_asgi_app()` mounted with **no auth layer**;
  exposes training topology, loss values, hidden_units, candidate
  correlation
- juniper-canopy H18 — `/metrics` exposure posture undocumented

This is the same problem in three places. The synthesis must produce
**one ecosystem decision** spanning all three services:

- **Option A** — All `/metrics` endpoints require an API key
  (Prometheus scrape config carries the header).
- **Option B** — All `/metrics` endpoints bind to localhost / are
  reachable only via sidecar; trust enforced at the network layer.
- **Option C** — `/metrics` are explicitly public on the deployment's
  trusted network, with that decision documented prominently.

The choice is the **same** for all three services; reviewing it
service-by-service produces inconsistent results.

### 5.7 Prometheus label cardinality bounds (added 2026-04-24)

juniper-data H12 and juniper-cascor H8 both flag `endpoint` labels
populated from `request.url.path` (raw). FastAPI offers a stable
template via `request.scope["route"].path` (e.g.
`/v1/datasets/{dataset_id}` not `/v1/datasets/abc-123`). The fix is
mechanical and identical in both services; coordinate via synthesis to
land it in lock-step.

### 5.8 Trace / correlation context propagation (added 2026-04-24)

juniper-canopy H16 found that `request_id` (an HTTP-side ContextVar)
does **not** flow into outgoing WebSocket messages, so a logical
"session" cannot be traced from REST → WS → cascor stream. juniper-data
H10 found logs lack W3C trace IDs entirely. The two findings are paired:

- The narrow fix is to thread `request_id` through WS envelopes (no new
  dependency, no protocol break).
- The broad fix is to adopt OpenTelemetry across all FastAPI services
  (depends on §5.2 decision).

Synthesis owns the broad-vs-narrow choice; per-app plans should
implement the narrow fix as a default unless the broad fix lands in
the same release cycle.

### 5.9 "Defined-but-unused" Prometheus metrics (added 2026-04-24)

Phase D extraction (`08_METRIC_CATALOG.md`) produced a hard count:
**~20 of 38 metrics defined across the ecosystem are never emitted
from production code**. The pattern originally identified as the
juniper-data H1 hypothesis ("operationally hollow") is actually
ecosystem-wide:

- juniper-data: 3 of 6 metrics unused (H1 already captures this)
- juniper-cascor: **24 of 26** metrics unused — all training,
  inference, and all 15 Phase-0 WebSocket metrics
- juniper-canopy: 3 of 6 metrics unused (WS gauges + demo-mode gauge)

This is the **single highest-impact finding** surfaced by the planning
cycle. A Grafana dashboard built today against the declared metric
names will show empty panels for training, WebSocket, and
dataset-generation — every metric that would actually indicate what
the services are doing.

**Decision required in synthesis**:

- **Option A** — Wire every declared metric at its natural emission
  site. ~20 integration points; non-trivial testing; realizes the
  intended design.
- **Option B** — Delete defined-but-unused metrics; ship "HTTP +
  build only" as the truthful contract for this release; commit to
  Option A as a follow-up.
- **Option C** — Keep declarations; emit a startup warning listing
  unused metrics. Doesn't fix, only discloses.

**Provisional recommendation**: Option A for the release; Option B if
scope-constrained.

### 5.10 Metric-name prefix drift (added 2026-04-24)

juniper-cascor uses two prefix styles in the same module:
`juniper_cascor_*` for training/inference/HTTP, and `cascor_ws_*`
(no `juniper_` namespace) for 15 WebSocket metrics. Rename carries a
dashboard-breakage cost; synthesis must pick: rename now with dual
emission, rename later, or document the split as permanent.

### 5.11 Data contract NPZ artifact

Out of scope for metrics review specifically (it is a data contract, not a
metrics contract), but flagged here so reviewers do not get pulled into
audit work that belongs in a separate review cycle.

---

## 6. Ecosystem-wide validation gates

Before the review cycle is signed off, the following must all pass.

### 6.1 Per-app gates (each per-app plan owns)

- All findings classified per §3.1–3.2.
- Critical and High findings have remediation plans per §3.3.
- All test suites for the app run green (unit, integration, regression,
  e2e, performance, security where the app provides them) with no
  collection errors, no implementation errors, no runtime errors, no
  unhandled runtime warnings, no skipped tests that mask the metrics
  surface.
- Every test that exercises a metrics path is verified to actually assert
  on the metric value/shape (not merely `assert response.status_code == 200`).

### 6.2 Cross-app gates (this roadmap owns)

- All client/server contract drift documented in §5.1, §5.5 is reconciled or
  has tickets filed.
- Env-var inventory (§5.3) compiled into a single table and checked into
  `juniper-ml/docs/REFERENCE.md`.
- Observability-library decision (§5.2) made and recorded with rationale.
- `/metrics` security posture (§5.6) decided ecosystem-wide and applied
  uniformly across data, cascor, canopy.
- Prometheus label-cardinality fix (§5.7) landed in lock-step across
  data and cascor.
- Defined-but-unused metric decision (§5.9) made and, if Option A,
  every cascor/canopy metric listed in `08_METRIC_CATALOG.md` has a
  production emission site.
- Metric-name prefix (§5.10) chosen and applied (dashboards updated).
- Trace/correlation propagation (§5.8) decided narrow-vs-broad with
  reasoning recorded.
- Cross-repo integration tests defined in `juniper-ml/CLAUDE.md`
  "Integration Testing" section all execute successfully against the
  current branch heads:
  - `cd juniper-data-client && pytest tests/ -v`
  - `cd juniper-cascor/src/tests && bash scripts/run_tests.bash`
  - `cd juniper-data && pytest juniper_data/tests/ -v`
  - `cd juniper-deploy && docker compose config`

### 6.3 Documentation gates

- One per-app plan exists at each of the six target paths.
- This roadmap is updated with the date of completion for each per-app
  review and the synthesis decisions for §5.2, §5.3, §5.4, §5.5, §5.6,
  §5.7, §5.8.

---

## 7. Post-review synthesis (Phase D)

After Phases A, B, and C complete, a synthesis pass produces:

1. **Ecosystem findings register** — flat union of all per-app findings,
   sorted by Severity × Likelihood, deduplicated where the same root cause
   appears in multiple apps.
2. **Cross-cutting decisions** — explicit choice on §5.2, §5.3, §5.4, §5.5
   with the evidence each per-app review surfaced.
3. **Release readiness verdict** — explicit go/no-go per app for the
   upcoming release, with the specific blocking findings listed.
4. **Follow-up work backlog** — Low/Informational and any deferred
   Medium findings, filed as GitHub issues in the appropriate repo.

---

## 8. Procedural constraints (inherited from project CLAUDE.md)

- **Worktrees**: Each per-app review that produces code changes must be
  performed in a worktree under
  `/home/pcalnon/Development/python/Juniper/worktrees/`, named per the
  convention in the parent `Juniper/CLAUDE.md`.
- **Thread handoff**: Reviewer agents must follow the thread-handoff
  protocol when context utilization approaches compaction — see
  `juniper-ml/notes/THREAD_HANDOFF_PROCEDURE.md`. Per-app plans are
  designed to be self-contained so a fresh thread can pick one up.
- **No fix without plan**: Even Critical findings should be remediated only
  after their per-app plan entry has the §3.3 remediation block populated
  (root cause + options + recommendation + validation).
- **Pull-request hygiene**: Per the prompt's Cleanup section, every
  remediation lands via PR; no direct merges to main.

---

## 9. Open questions for the user

Items deferred to the user before the cycle proceeds:

1. **Distribution of plan documents**: copy each per-app plan into its
   target repo via dedicated worktrees + PRs, or direct commit on `main`?
   (Currently staged in `juniper-ml/notes/code-review-plans/`.)
2. **Standardization decision** (§5.2): is extracting a shared
   `juniper-observability` micro-library acceptable scope for this release
   cycle, or should that be deferred to a follow-up?
3. **Default-flip decision** (§5.4): should the release flip
   `*_METRICS_ENABLED` defaults to `true`?
4. **`/metrics` security posture** (§5.6, added by audit): which of
   Options A/B/C across the three FastAPI services?
5. **Trace context approach** (§5.8, added by audit): narrow fix
   (thread `request_id` into WS envelopes) or broad (adopt OpenTelemetry)?
6. **Defined-but-unused metrics** (§5.9, added by extraction):
   Option A (wire all emission sites), B (delete declarations and ship
   "HTTP + build only"), or C (startup warning to disclose)?
7. **Metric-name prefix drift** (§5.10, added by extraction):
   rename cascor's 15 `cascor_ws_*` metrics to `juniper_cascor_ws_*`
   or document the split as permanent?
8. **Rate-limit default posture** (follow-up to §5.4): juniper-data
   defaults `True`; juniper-cascor and juniper-canopy default
   `False`. Align or document divergence?
9. **Owner assignments**: who executes each per-app review? (All Claude,
   all human, or split?)
