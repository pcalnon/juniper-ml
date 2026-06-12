# Juniper Package Placement & Relocation Plan — Operationalizing the Code-Organization Rule Across Every Package

**Project**: Juniper ML Research Platform
**Scope**: Cross-repo (juniper-ml + its 5 sub-packages, juniper-cascor\*, juniper-data\*, juniper-canopy, the planned `*-core` packages, future model apps)
**Author**: Paul Calnon
**Date**: 2026-06-09
**Status**: **Proposal — pending ratification** (planning only; no code moved, no package published on the basis of this document until Paul ratifies)
**Builds on**: [`JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md`](JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md) (the governing rule)
**Reconciles**: [`JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md`](JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md), [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md), [`CI_TOOLS_EXTRACTION_PLAYBOOK.md`](CI_TOOLS_EXTRACTION_PLAYBOOK.md)

---

## 0. Purpose and how to read this document

The [Code Organization Strategy](JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md) (2026-06-05) established **the rule** for where Juniper code should live: *place by commonality; the dependency arrow points specific → common; extend via ports/adapters, not by bundling model code into common repos.*
That document derived the rule and drew one immediate consequence (`juniper-cascor-core` should leave `juniper-ml`).
It did **not** apply the rule package-by-package to the whole ecosystem, nor did it produce an executable relocation/validation plan.

**This document is that missing operational layer.** It:

1. Records the **complete, independently verified inventory** of every Juniper Python package and its current home (ground truth captured live on 2026-06-09).
2. **Classifies each package** under the §5 placement rule and assigns a disposition: **VALIDATED-IN-PLACE**, **RELOCATE**, **CREATE (future)**, or **OUT-OF-SCOPE**.
3. Produces the **detailed, sequenced relocation plan for `juniper-cascor-core`** — the single misplaced package, and the **blocker for the PyPI deployment** of the refactor's new/modified packages.
4. Consolidates the **open decisions that require Paul's ratification**, each with evidence and a recommendation.
5. Lists **document-hygiene touch-ups** discovered during the audit (recommended, not applied here).

**What this document deliberately does not do:** it does not re-derive the rule (that is the strategy doc's job, and the rule is treated here as the governing proposal awaiting ratification); it does not move code, edit package files, or publish anything; and it does not pre-empt the un-ratified middleware/model-core refactor — it only records where that refactor's packages are *planned* to live and flags the placement questions it leaves open.

---

## 1. Executive summary

- **The ecosystem is almost entirely well-placed already.** Of the 13 publishable packages that exist today, **12 satisfy the §5 rule in their current home** and are **VALIDATED-IN-PLACE**. Exactly **one** violates it.
- **The single misplacement is `juniper-cascor-core`.** It is a *model-specific* package (it bundles cascor's `candidate_unit` implementation) currently sitting in `juniper-ml`, the *shared/common* tier. It is **version 0.1.0 and not yet on PyPI (verified 404 on 2026-06-09)**, so moving it is cheap and risk-free *right now* — and decisively so *before its first publish*.
- **A working precedent already proves the target pattern.** `juniper-cascor-protocol` (v0.1.0, **published**) lives as an independently-versioned, independently-published **subdirectory of `juniper-cascor`**, consumed by the cascor app via a plain PyPI pin. This is the exact "model-family package homed in the model repo" shape that `juniper-cascor-core` should adopt — and it shows the worker↔server symmetric-dependency concern is already a solved problem in the cascor repo.
- **The relocation unblocks the PyPI deployment chain.** Deciding `juniper-cascor-core`'s home *before* first publish avoids ever binding a live PyPI project + OIDC trusted-publisher to the wrong repo (`juniper-ml`) and later having to migrate it. Publishing from the correct home → worker pin + lockfile regen → worker `main` green → remove the live `juniper-deploy` CW-05 stopgap → close `juniper-cascor#319` / `juniper-cascor-worker#97`.
- **Three genuinely open decisions need Paul's ratification** (consolidated in §8): (a) **standalone `juniper-cascor-core` repo vs. subdirectory of `juniper-cascor`**; (b) **whether to rename** the distribution to `juniper-cascor-model` while it is still unpublished (the strategy doc's OQ-4 naming concern); (c) **where the future `*-core` shared packages physically live** (juniper-ml subdir vs. standalone — the strategy doc's OQ-2). This plan recommends an answer to each.
- **Nothing here depends on the un-ratified recurse refactor.** The `juniper-cascor-core` relocation is independent of, and should not wait for, WS-0 ratification or the OQ-4 recurrent-model pick. The refactor later *refines* the relocated package's internal boundary; it does not gate the move.

---

## 2. Scope and method

### 2.1 In scope

Every Juniper Python distribution (anything with a `[project]` table in a `pyproject.toml`) across the eight ecosystem repos, plus the future packages named in ratified-or-in-review design docs. Orchestration-only and non-package directories are noted and excluded.

### 2.2 Method — adversarial, multi-agent, ground-truth-first

This plan was produced and checked with independent sub-agents to minimize hallucination, per the project's verification discipline:

1. **Discovery** — an Explore agent inventoried every `notes/` document bearing on package placement, extraction, or PyPI migration (7 thematic clusters).
2. **Document extraction** — separate agents deep-read the PyPI-extraction-precedent cluster and the middleware/model-core refactor cluster, returning conclusions, open questions, and stated statuses with `file:line` citations.
3. **Ground truth** — an agent established, **live against the real sibling repos and PyPI on 2026-06-09**, every package's physical home, version, publish workflow, and PyPI status (network was available; all 15 names checked).
4. **Precedent + blast-radius** — agents characterized the `juniper-cascor-protocol` precedent end-to-end and produced a file-level relocation impact inventory for `juniper-cascor-core`.
5. **Adversarial validation** — independent agents attempted to refute the factual, cross-document, and logical claims of this plan's draft (see §10).

Every factual claim about a current home, version, or PyPI status in this document traces to the 2026-06-09 ground-truth pass; every claim about what a design doc *says* traces to a `file:line` citation in the source.

---

## 3. The governing placement rule (recap + reconciliations)

### 3.1 The rule (verbatim from the strategy doc §3)

> **Place code by commonality. Let the dependency arrow point _specific → common_, never _common → specific_. Extend via _interface-in-the-common-repo_ + _adapter-with-the-model_, discovered (e.g. Python entry points), not bundled.**

This is Dependency Inversion + Open/Closed applied to repos: the common tier is closed for modification and open for extension; a new model is a **new model repo** that depends on common interfaces and changes **zero** common repos. The load-bearing constraint for a many-model platform is that adding "model #20" must cost the same as "model #2".

### 3.2 The placement table (strategy doc §5, restated)

| Kind of code | Commonality | Home |
|---|---|---|
| Generic service/middleware infra | agnostic | `juniper-service-core` (future shared pkg) |
| Abstract model interface + contracts | agnostic | `juniper-model-core` (future shared pkg) |
| Cross-cutting libraries | agnostic | shared pkgs in the **juniper-ml tier** |
| Dataset generation/handling/delivery | agnostic | `juniper-data` (+ `juniper-data-client`) |
| Model implementation | **specific** | the model's **app family** |
| Model↔middleware adapter (translation layer) | **specific** | the model's **app family** (implements a `*-core` port) |
| Model-specific data adaptation (rare) | **specific** | the model's **app family** |

### 3.3 Reconciliations this plan applies

The audit surfaced three points where the source documents are inconsistent or stale. Resolving them is a prerequisite for an accurate package-by-package application of the rule.

- **R1 — Extension *mechanism* (strategy OQ-1).** The §3 rule's phrase "discovered (e.g. Python entry points)" describes a *runtime plugin-registry* mechanism, but the [middleware refactor design](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) actually chose **compile-time subclassing + dependency injection** ("apps subclass routes/lifecycle and inject their `TrainableModel`"), *not* an entry-point registry.
  The strategy doc's own **OQ-1 flags this as open and defers it to the recurse `juniper-model-core` work** — which has since landed on subclass+inject.
  **Resolution:** the *placement* conclusion (model-specific code lives with the model; the common tier never imports it) holds **identically** under either mechanism, so no package placement in this plan changes.
  The strategy doc's mechanism wording should be annotated to point at the refactor's subclass+inject decision (see §9). This plan adopts **subclass + inject** as the operative mechanism.
- **R2 — `juniper-cascor-core`'s home (migration plan §3 vs. strategy §8).** The [cascor-core migration plan](JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md) (2026-06-03) fixes the home as "`juniper-ml/juniper-cascor-core/` subdirectory".
  The strategy doc (2026-06-05, two days later) **supersedes that**: it states cascor-core "should not live in `juniper-ml`" and, under "**Where it belongs:**", assigns it to "the **cascor family**".
  **Resolution:** the migration plan's home assignment is **superseded**; all of its other mechanics (the Wave 0/1/2 extraction boundary, the gap fixes, the drift-guard, the publish workflow) **remain valid** and are reused verbatim in §6.3.
- **R3 — "core" naming overload (strategy OQ-4).** "core" is doing double duty: `model-core` / `service-core` denote *shared abstractions*, while `cascor-core` denotes *a specific model's code*. The strategy doc suggests `juniper-cascor-model` for the specific tier. This is a live decision **because the package is still unpublished** (renaming is free now, costly later). It is carried as an open decision in §6.5 / §8.

---

## 4. Complete verified package inventory (ground truth, 2026-06-09)

All rows below were verified live against the real repos under `/home/pcalnon/Development/python/Juniper/` and against PyPI on 2026-06-09. "Home" is the **repo** that owns the package; "subdir" marks a package published from a subdirectory of a larger repo.

| # | Package | Physical home | Version | Publish workflow (trigger) | PyPI (live 2026-06-09) | §5 class | Disposition |
|---|---|---|---|---|---|---|---|
| 1 | `juniper-ml` | juniper-ml (root) | 0.6.0 | `publish.yml` (release) | **0.6.0** | meta / shared-tier host | **VALIDATED** |
| 2 | `juniper-observability` | juniper-ml (subdir) | 0.3.1 | `publish-observability.yml` (`juniper-observability-v*`) | **0.3.1** | cross-cutting lib (agnostic) | **VALIDATED** |
| 3 | `juniper-ci-tools` | juniper-ml (subdir) | 0.4.0 | `publish-ci-tools.yml` (`juniper-ci-tools-v*`) | **0.4.0** | cross-cutting dev tool (agnostic) | **VALIDATED** |
| 4 | `juniper-doc-tools` | juniper-ml (subdir) | 0.1.1 | `publish-doc-tools.yml` (`juniper-doc-tools-v*`) | **0.1.1** | cross-cutting dev tool (agnostic) | **VALIDATED** |
| 5 | `juniper-config-tools` | juniper-ml (subdir) | 0.1.0 | `publish-config-tools.yml` (`juniper-config-tools-v*`) | **0.1.0** | cross-cutting lib (agnostic) | **VALIDATED** |
| 6 | **`juniper-cascor-core`** | **juniper-ml (subdir)** | 0.1.0 | `publish-cascor-core.yml` (`juniper-cascor-core-v*`) | **404 — NOT published** | **model implementation (specific)** | **RELOCATE → cascor family** |
| 7 | `juniper-cascor` | juniper-cascor (root) | 0.5.0 | `publish.yml` (release) | **0.5.0** | model app (specific) | **VALIDATED** |
| 8 | `juniper-cascor-protocol` | juniper-cascor (subdir) | 0.1.0 | `publish-protocol.yml` (`juniper-cascor-protocol-v*`) | **0.1.0** | model-family wire schema (specific) | **VALIDATED** (precedent) |
| 9 | `juniper-data` | juniper-data (root) | 0.6.0 | `publish.yml` (release) | **0.6.0** | dataset tier (agnostic) | **VALIDATED** |
| 10 | `juniper-data-client` | juniper-data-client (root) | 0.4.1 | `publish.yml` (release) | **0.4.1** | dataset-tier client (agnostic) | **VALIDATED** |
| 11 | `juniper-cascor-client` | juniper-cascor-client (root) | 0.5.0 | `publish.yml` (release) | **0.5.0** | model-family client (specific) | **VALIDATED** |
| 12 | `juniper-cascor-worker` | juniper-cascor-worker (root) | 0.4.0 | `publish.yml` (release) | **0.4.0** | model-family worker (specific) | **VALIDATED** |
| 13 | `juniper-canopy` | juniper-canopy (root) | 0.5.0 | `publish.yml` (release) | **0.5.0** | UI app (agnostic by design) | **VALIDATED** |
| — | `juniper-deploy` | juniper-deploy (root) | n/a (no `[project]`) | none | n/a | orchestration (not a package) | **N/A** |

### Future packages (named in design docs; do not yet exist on disk or PyPI)

| Package | Source doc | Planned class | Planned home | Placement status |
|---|---|---|---|---|
| `juniper-service-core` | [refactor](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) | generic infra (agnostic) | shared tier | **home OPEN** (juniper-ml subdir vs standalone — strategy OQ-2) |
| `juniper-model-core` | [refactor](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md) | abstract model interface (agnostic) | shared tier | **home OPEN** (strategy OQ-2) |
| `juniper-recurse` | [recurse model](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md) | model app (specific) | own repo `pcalnon/juniper-recurse` | DECIDED (own repo); gated on WS-0 ratification + OQ-4 model pick |
| `juniper-recurse-client` | refactor (WS-7) | model client (specific) | own repo (implied) | follows per-family rule; not yet scoped |
| `juniper-recurse-worker` | refactor (WS-8) | model worker (specific) | own repo (implied) | DEFERRED (trigger-gated) |

### Out of scope

- **`juniper-deploy`** — Docker-Compose orchestration; its `pyproject.toml` carries only `[tool.pytest.ini_options]` (no `[project]`, no `[build-system]`). Not a distributable package.
- **`juniper-slacker`** — a local-only, unregistered git repo (no remote, no `pyproject.toml`, no `[project].name`, not in the ecosystem registry). It is a standalone Slack→host ops bridge, not a Juniper ML library/service. Shares only the `juniper-` directory prefix. **Disregard for placement.**

---

## 5. Per-class disposition and rationale

### 5.1 Shared / common tier — the `juniper-ml` subdirectory packages

**`juniper-observability`, `juniper-ci-tools`, `juniper-doc-tools`, `juniper-config-tools` → VALIDATED-IN-PLACE.**

All four are **model-agnostic cross-cutting libraries** (metrics/logging middleware; dependency-doc and lint generators; the doc-link validator; the env-alias helper).
They map exactly to the strategy §5 row "Cross-cutting libraries → shared pkgs in the juniper-ml tier." Each is published from a juniper-ml subdirectory via a namespaced `juniper-<pkg>-v*` tag workflow, and all four are live on PyPI.
This is the **established, proven extraction pattern** (the [CI-tools extraction playbook](CI_TOOLS_EXTRACTION_PLAYBOOK.md), proven 3×). No change.
`juniper-ml` itself remains the meta-package and the host of this tier — its identity as the *shared/common* tier is **preserved precisely because** the one model-specific intruder (cascor-core) leaves.

### 5.2 Data tier

**`juniper-data`, `juniper-data-client` → VALIDATED-IN-PLACE.**

Dataset generation/handling/delivery is model-agnostic by the rule and belongs in `juniper-data` (+ client).
The strategy doc §6 explicitly resolves the parallel question raised about juniper-data's bundled generators: the `spiral` / `equities` / `mnist` / `moon` / `xor` generators are **datasets usable by any model**, not model-specific plugins, so they belong in `juniper-data` exactly as they are.
Only a genuinely *model-specific data adaptation* would move to a model app, and that is expected to be rare. No package moves.
(One narrow open item — **the middleware-refactor doc's OQ-8**, *not* the strategy doc, whose own open-question list stops at OQ-4 — asks whether cascor's `spiral_problem` should migrate *into* `juniper-data` as a dataset; that is a cascor-internal question, not a relocation of an existing published package, and is out of this plan's critical path.)

### 5.3 Model application families

**`juniper-cascor`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-cascor-protocol` → VALIDATED-IN-PLACE.**

The cascor family is already a correct instance of the rule: the model app, its client, its worker, and its wire-protocol schema package all live in the cascor family, depend *downward* on shared/agnostic packages, and are never imported by the common tier.
`juniper-cascor-client` is model-specific by name but thin (strategy OQ-3 confirms it already follows the per-family rule).
**`juniper-cascor-protocol` is the key validated case**: it is a model-family-specific package that already lives as a **published subdirectory of `juniper-cascor`** — the precedent this plan leans on in §6.

**`juniper-canopy` → VALIDATED-IN-PLACE.** Canopy is an **application, not a shared library**, so it correctly lives in its own repo rather than the juniper-ml library tier — that disposition is unconditional.
Its *model-agnostic* character is **by design intent and not yet fully realized**: its base `[project].dependencies` still hard-depend on `juniper-cascor-protocol` (with `juniper-cascor-client` carried in canopy's `[juniper-cascor]` extra), and full agnosticism arrives only with the planned `describe_topology()` seam.
The placement is correct today regardless of how far the agnosticism has progressed. No change.

> **One forward-looking nuance (not an action):** `juniper-cascor-protocol` is *currently* cascor-specific and correctly homed — it is consumed only by the cascor family today and is named/scoped to it.
> Honesty note: its `worker/` sublayer (a numpy `BinaryFrame` codec + a `WorkerMessageType` enum) is largely model-agnostic *transport* plumbing, so it is *already* a latent candidate for `juniper-service-core` generalization, while the cascor-specific content concentrates in the `envelope/` training schemas.
> If the refactor's **OQ-11** ("is the worker layer truly model-agnostic?") resolves to "yes," a *future, generic* worker protocol could be generalized into `juniper-service-core` — a **new abstraction**, not a relocation of the existing cascor-protocol package, which stays in the cascor family until that lands (and until a second consumer exists). No action now.

### 5.4 The one misplacement — `juniper-cascor-core` → RELOCATE

`juniper-cascor-core` bundles cascor's `candidate_unit` implementation (a **model implementation**, the §5 "specific" row) together with some currently-generic helpers (`utils`, `log_config`). It sits in `juniper-ml`, the shared tier.
By the rule it must leave the shared tier and join the cascor family. It is the **first and only** model-specific thing in a shared repo — precisely the smell that prompted the strategy review.
Because it is **unpublished (404)**, the move is cheap now and gets more expensive the moment it is first published from the wrong repo (a live PyPI project + OIDC trusted-publisher binding would then have to be migrated). The full, sequenced plan is §6.

> **Interim-bundle nuance (strategy §8).** The extracted package presently *mixes commonality tiers* — generic `utils`/`log_config` (which the recurse refactor will eventually route to `juniper-service-core`) bundled with cascor-specific `candidate_unit`.
> For the CW-05 interim this bundle is acceptable, but it must be **homed in cascor and labeled the interim cascor model core**, so its shape does not entrench the wrong long-term boundary.
> The recurse `service-core`/`model-core` extraction is what later refines it (§6.6). This is an argument for the *home* (cascor) but **not** an argument to wait for the refactor.

### 5.5 Future packages from the middleware / model-core refactor

These do not exist yet and are **gated on WS-0 ratification** (the refactor is in-review, *not ratified*) and, for the recurse app, on the **OQ-4** recurrent-model pick (open, under active research). Placement guidance under the rule:

- **`juniper-service-core` and `juniper-model-core` are genuinely agnostic → shared tier.** Under the rule they belong with the other shared libraries.
  **Where they *physically* live (a juniper-ml subdirectory like the existing four, vs. their own standalone repos) is strategy OQ-2 and remains open.**
  Recommendation (§8): default to the **juniper-ml subdirectory** pattern for consistency with the four proven shared packages, unless their code volume grows large enough to justify standalone repos — a judgment best made when WS-2/WS-3 are actually scoped.
  Either way, the §5 *classification* (agnostic, shared tier) is settled; only the physical hosting is open.
- **`juniper-recurse` (+ future `-client`, `-worker`) are model-specific → own repos.** This is already the decided direction and is consistent with the cascor family. No new question.
- **Sequencing note:** the refactor's own Part 8 makes "**publish-first is mandatory**" and "**bump the pin and regenerate the lock in the same change**" the load-bearing rules for *its* PyPI rollout. Those rules are downstream of WS-0 and are **not** part of this plan's critical path, but they reinforce the same lesson that drives the cascor-core move: decide the home, publish from it, and pin+lock atomically.

### 5.6 Non-packages

`juniper-deploy` (orchestration) and `juniper-slacker` (local ops tool) are not distributable packages and require no placement decision (see §4 "Out of scope").

---

## 6. The `juniper-cascor-core` relocation — detailed, blocking plan

This is the actionable core of the document. It is the one relocation, and it is the PyPI-deployment blocker.

### 6.1 Decision required — standalone repo vs. subdirectory of `juniper-cascor`

Both options place the package in the **cascor family** and both satisfy the rule; the choice is about release cadence and operational overhead. The strategy doc §9 *leaned standalone*. The audit surfaced **new, decisive evidence** that the strategy doc did not weigh: the `juniper-cascor-protocol` precedent.

**The precedent (verified end-to-end):** `juniper-cascor-protocol` already lives as a self-contained subdirectory of `juniper-cascor` with its own `pyproject.toml`, package dir, `tests/`, `README`, `CHANGELOG`.
It is published by a dedicated `publish-protocol.yml` on `juniper-cascor-protocol-v*` tags (decoupled from cascor's `v*` app releases, `working-directory: juniper-cascor-protocol`, OIDC trusted publishing, TestPyPI→PyPI gates), and it has its own path-filtered `ci-protocol.yml`.
The cascor app consumes it via a **plain PyPI pin** (`juniper-cascor-protocol>=0.1.0a0` in `[project].dependencies`), *not* a path/editable reference; the worker and canopy pin the same package at `>=0.1.0`, so the symmetric server+worker consumption is real and already in production.
This is exactly the shape `juniper-cascor-core` needs, already working in the destination repo.

| Criterion | Option S — standalone `juniper-cascor-core` repo | Option D — subdirectory of `juniper-cascor` |
|---|---|---|
| Satisfies the §5 rule (in cascor family) | ✅ | ✅ |
| Symmetric server+worker dependency | ✅ (peer of both) | ✅ — **already demonstrated**: worker already depends on cascor-protocol, published from the cascor repo, with no problem |
| Release cadence decoupled from cascor app | ✅ strongest | ✅ namespaced `*-v*` tag already decouples it from app `v*` releases (proven by protocol) |
| Operational overhead to stand up | Higher — new repo, branch protection, CODEOWNERS, CI bootstrap, fresh trusted-publisher | **Lower — copy the protocol wiring; trusted publisher is a new project on an existing repo** |
| Wiring template available | Must be authored | **Exists verbatim** (`publish-protocol.yml` + `ci-protocol.yml`) |
| Conceptual "peer of cascor/worker/client" cleanliness | ✅ cleanest | Slightly less (lives "inside" the server repo), but protocol already accepts this |
| Drift-guard simplification (vs. cascor `src`) | Cross-repo (needs sibling clone) | In-repo once cascor adopts (Wave 2) — simplest end state |
| Insulation from host-repo incidents | Isolated (standalone) | Shared fate — a cascor-repo history-rewrite / CI outage also affects the core's release |

**Recommendation:** **Option D — subdirectory of `juniper-cascor`** — as the default, because it is a proven, lower-friction path whose entire publish + CI + consumption wiring can be copied from `juniper-cascor-protocol`, and because the protocol precedent demonstrates that the strategy doc's stated reason for leaning standalone (symmetric server+worker dependency) is *already satisfied* by a cascor-subdirectory package.
**Option S remains fully valid** and is preferable if Paul wants the strongest possible release decoupling, a clean peer-of-the-family conceptual model, and insulation of the core's release from cascor-repo incidents; the cost is one-time repo bootstrap + a fresh trusted-publisher registration.
**This is Paul's call (strategy §9 open decision).** Either option unblocks the publish; neither should be delayed by the recurse refactor.

### 6.2 Relocation impact inventory — the blast radius in `juniper-ml`

Verified file-by-file. On relocation, each artifact either **MOVES** with the package, **STAYS** in juniper-ml, is **DELETED** from juniper-ml, or has a **reference UPDATED**.

| Artifact (in juniper-ml) | On relocation |
|---|---|
| `juniper-cascor-core/` (entire tree, 41 git-tracked files: `pyproject.toml`, `juniper_cascor_core/{__init__,_version}.py`, `candidate_unit/`, `utils/`, `log_config/`, `cascor_constants/`, `tests/`, `README.md`, `CHANGELOG.md`, `LICENSE`) | **MOVES** with the package |
| `juniper-cascor-core/pyproject.toml` repo URLs → `pcalnon/juniper-ml` | **MOVES + UPDATE** to the new home's repo URL |
| `juniper-cascor-core/images/Juniper_Logo_150px.png` (Git-LFS tracked via juniper-ml root `.gitattributes`) | **MOVES** — new home must replicate LFS config or de-LFS the asset |
| `.github/workflows/publish-cascor-core.yml` (trigger `juniper-cascor-core-v*`; `working-directory: juniper-cascor-core`; `sparse-checkout: juniper-cascor-core/pyproject.toml`; artifact path `juniper-cascor-core/dist/`) | **MOVES + UPDATE** the 3 layout bindings (drop the subdir prefix if standalone; or copy `publish-protocol.yml`'s subdir form if Option D) |
| `.github/workflows/ci.yml` — `cascor-core-tests` job (`pip install -e "./juniper-cascor-core[test]"`, `pytest -v juniper-cascor-core/tests/`) | **DELETE from juniper-ml**; recreate in the new home's CI (Option D: copy `ci-protocol.yml`) |
| `.github/workflows/ci.yml` — `required-checks` gate (`needs: […, cascor-core-tests, …]`, status echo, gate `if`) | **UPDATE** — remove `cascor-core-tests` from `needs`/gate in the same change, or the gate fails on a missing job |
| `.github/workflows/ci.yml` — drift-guard invocation (`python3 -m unittest -v tests/test_cascor_core_drift.py`) | **DELETE or UPDATE** — coupled to the drift-guard disposition (below) |
| `tests/test_cascor_core_drift.py` (locates the package via `…/juniper-cascor-core`; compares byte-identity vs sibling `juniper-cascor/src`) | **AMBIGUOUS — see disposition below** |
| `docs/REFERENCE.md`, `docs/QUICK_START.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `README.md` (subpackage listings, install snippets, "not an extra yet" notes) | **UPDATE references** to point at the new home |
| Root `pyproject.toml` `[project.optional-dependencies]` | **STAYS — no change.** Verified: cascor-core is **not** in any extra (`clients`/`worker`/`doc-tools`/`servers`/`tools`/`all`) |
| `tests/test_pyproject_extras.py` | **STAYS — no change** (cascor-core was never an extra) |
| `MANIFEST.in`, `.github/dependabot.yml`, `security-scan.yml`, `docs-full-check.yml`, `agents-md-touch-up.yml`, `claude.yml`, `lockfile-update.yml`, `.pre-commit-config.yaml`, `AGENTS.md`/`CLAUDE.md`, `CHANGELOG.md` | **STAYS — no change** (grep-verified: no cascor-core coupling) |
| `notes/*` planning docs (this plan, the migration plan, the strategy doc, roadmaps, handoffs) | **STAY** in juniper-ml (authoring repo); optional cross-link updates |

**Drift-guard disposition (the one real ambiguity).** `tests/test_cascor_core_drift.py` enforces byte-identity between the extracted modules and `juniper-cascor/src` — its purpose is *cross-repo* (cascor src ↔ the extracted copy), so it is not intrinsically a juniper-ml concern.
On relocation it can: (1) **move into the new cascor-core home** (still needs `juniper-cascor` as a sibling clone), (2) **move into `juniper-cascor`** (the most natural home for "my src vs. the extracted copy"), or (3) be **deleted** if Wave 2 (cascor adopts the package and deletes its inline copies) lands as part of the move, which eliminates the two-copies-can-drift risk entirely.
**Recommendation:** under Option D, the cleanest end state is to **co-locate the drift-guard with the package in `juniper-cascor`** during the interim, and **retire it at Wave 2** when cascor imports from the subdir package and the two copies collapse into one.
The choice is coupled to the Wave-2 timing decision (§6.6) and must be reconciled with the `ci.yml` invocation in the same change.

> **Scope note on `tests/test_workflow_script_paths.py` (precise coupling).** This lint's path regex matches only invocations ending in `.py`/`.sh`/`.bash`, so it does **not** couple to the two non-script cascor-core lines (`pip install -e "./juniper-cascor-core[test]"` and `pytest … juniper-cascor-core/tests/` — neither ends in a script extension).
> It **does**, however, validate the drift-guard invocation `python3 -m unittest -v tests/test_cascor_core_drift.py` (a real `.py` path). Therefore the drift-guard test file and that `ci.yml` line must be removed/updated **atomically** (already required by the drift-guard row above), or this lint goes red. The lint module itself **STAYS** in juniper-ml.

### 6.3 Sequenced relocation + publish steps

This reuses the [migration plan](JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md)'s Wave 0/1/2 mechanics (valid) with the **home corrected to the cascor family** per R2, and follows the strategy §10 migration sketch.

**Phase 1 — Ratify the home (Paul).** Choose Option S or D (§6.1) and the name (§6.5). This is the only true blocker; everything else is mechanical.

**Phase 2 — Stand up the new home.**

1. Create the home (standalone repo **or** `juniper-cascor/juniper-cascor-core/`). Move the package tree + `publish-cascor-core.yml` + (per disposition) the drift-guard there. Under Option D, copy the `publish-protocol.yml` / `ci-protocol.yml` wiring and adjust names/paths.
2. Register the PyPI project + **OIDC trusted publisher against the new repo** (owner, repo, workflow filename, environment must match exactly — see §6.4).
3. Apply the migration plan's Wave-0 substance that is **not** about home: deployment-agnostic logging (`JUNIPER_CASCOR_LOG_DIR` override + stderr/no-op fallback, gap #3), the `torch`/`numpy`/`PyYAML` deps, the smoke test, and the byte-identical drift-guard.
4. **Verify the workflow before first cron**: `gh workflow run publish-cascor-core.yml` (per the "verify new CI workflows before first cron" rule) so a hand-authored path/permission error is caught immediately.

**Phase 3 — Revert the addition from `juniper-ml`.** Per the §6.2 inventory, in a single change: drop the `juniper-cascor-core/` tree; delete the `cascor-core-tests` CI job; update the `required-checks` gate (`needs`/echo/`if`) in the same edit.
Also remove or update the drift-guard `ci.yml` invocation **atomically with** deleting `tests/test_cascor_core_drift.py` (so the workflow-paths lint stays green), and update the `docs/` + `README.md` references. Keep this plan, the migration plan, and the strategy doc in juniper-ml.

- **GitHub-side gate (do not miss):** Juniper repos enforce required status checks via **rulesets**, not in-YAML `needs:` alone.
  Before/with removing the `cascor-core-tests` job, audit juniper-ml's ruleset required-status-checks (`gh api repos/pcalnon/juniper-ml/rulesets`); if the `juniper-cascor-core Tests` job is individually listed as required, remove it in the same change, or PRs block forever on a check that never reports.
  If only the umbrella `required-checks` / quality-gate is the required check, no ruleset edit is needed — confirm which it is.
- **Sequencing choice (made explicit):** this plan adopts strategy §9 **option (a)** — relocate, *then* publish — over option (b) (publish-from-`juniper-ml`-now).
  Consequence: `juniper-cascor-worker` `main` **remains red from Phase 3 until Phase 5 completes**.
  This is safe: the worker is *already* red (its `pyproject.toml` requires the unpublished `juniper-cascor-core` and its lockfile omits it), and nothing in juniper-ml build-depends on cascor-core, so the revert changes nothing for the worker.
  Option (b) is rejected to avoid binding the trusted publisher to the wrong repo (§6.4).

**Phase 4 — Publish `v0.1.0` from the new home.** Tag `juniper-cascor-core-v0.1.0`; the workflow gates at TestPyPI then PyPI (both manual-approval). Verify with the PyPI JSON endpoint.

**Phase 5 — Worker adoption (migration-plan Wave 1).** Add/confirm `juniper-cascor-core>=0.1.0` in `juniper-cascor-worker` (**the pin string does not change** — the PyPI name is host-repo-independent), **regenerate `requirements.lock`** (currently stale — it predates the dependency and omits cascor-core), drop the `--cascor-path` indirection, use core's `ACTIVATION_MAP` (gap #4), fix the float/int param coercion (gap #5), set `JUNIPER_CASCOR_LOG_DIR`, rebuild the worker image.

**Phase 6 — Acceptance + stopgap removal.** Run the `juniper-cascor#319` repro on the deploy stack (spiral, `max_hidden_units=3`, network grows 0→3, `worker tasks_completed > 0`, `All N remote tasks completed successfully`). Then **remove the temporary `juniper-deploy/docker-compose.cw05-stopgap.yml`**. Close `juniper-cascor-worker#97` and `juniper-cascor#319`.

**Phase 7 (deferred — migration-plan Wave 2).** cascor itself adopts the package and deletes its inline copies (single source of truth), retiring the drift-guard. Trigger: drift-guard friction or a `candidate_unit` change that must land in both. Not part of the unblock critical path.

### 6.4 Trusted-publisher / OIDC implications (why home-before-publish matters)

PyPI trusted publishing binds the project to an exact **(owner, repository, workflow filename, environment)** tuple. The subdir publish workflows additionally assume the monorepo layout (`working-directory:`, sparse-checkout paths). Consequences:

- **Publishing `juniper-cascor-core` from `juniper-ml` now would bind the PyPI project + OIDC trusted-publisher to `pcalnon/juniper-ml`.** Relocating afterward would then require migrating a *live* project and re-registering the trusted publisher — exactly the avoidable mess the strategy doc warns against.
- Therefore **decide the home first, register the trusted publisher against the new home, and publish from there once.** The worker's `juniper-cascor-core>=0.1.0` dependency is unaffected because the **PyPI name is independent of the host repo**.
- Under **Option D**, the trusted publisher is a *new project on an existing, already-trusted repo* (`pcalnon/juniper-cascor` already publishes `juniper-cascor-protocol`), which is the lowest-friction registration path.

### 6.5 Naming decision — keep `juniper-cascor-core` or rename to `juniper-cascor-model`?

The strategy doc's **OQ-4** notes "core" wrongly implies *shared*. `juniper-cascor-model` would more honestly mark the specific tier. The package is **unpublished**, so renaming is **free now and costly after first publish** (a published name is effectively permanent; a rename means a new project + deprecation of the old).

- **Lean: ship `v0.1.0` as `juniper-cascor-core`** to keep the unblock minimal and because the name is already threaded through the migration plan and the worker pin. Treat the broader "core" naming convention (OQ-4) as a *platform-wide* decision to settle alongside `service-core`/`model-core` naming, not as a rider on the time-sensitive unblock.
- **Counter-argument worth Paul's explicit ruling:** because before-first-publish is the *only cheap moment to rename*, if a rename to `juniper-cascor-model` is at all likely, doing it now (a one-line worker-pin change, since both are unpublished) is far cheaper than later. **This is a genuine "decide now" because publishing forecloses it.** Recorded as an open decision in §8.

### 6.6 Relationship to the recurse middleware refactor (do not couple)

The relocated package is an **interim bundle**: its generic `utils`/`log_config` will, *eventually*, be pulled toward `juniper-service-core` by the refactor; its `candidate_unit` is the durable cascor-specific core. The correct sequencing:

- **Relocate and publish cascor-core now**, homed in cascor and labeled the interim cascor model core. Do **not** wait for the refactor (WS-0 is un-ratified; OQ-4 is open).
- **Do not pre-split** the interim bundle to match the future `service-core`/`model-core` boundary (strategy §9 leans "after, don't front-run the recurse work"). When `service-core`/`model-core` land, they refine the boundary; until then the verbatim bundle is the lowest-risk unblock.

---

## 7. PyPI deployment unblock — the critical path

The user-stated blocker — "completing this package relocation is a blocker for the PyPI deployment of the new and modified packages created during the refactor" — resolves to this chain. The **only** item requiring a decision is the first; the rest are mechanical.

```text
[Paul ratifies home + name]          ← the sole blocking decision (§6.1, §6.5)
        │
        ▼
[Stand up new home + trusted publisher]   (§6.3 Phase 2, §6.4)
        │
        ▼
[Revert cascor-core from juniper-ml]      (§6.3 Phase 3, §6.2 inventory)
        │
        ▼
[Publish juniper-cascor-core v0.1.0 from the cascor family]   (§6.3 Phase 4)
        │
        ▼
[Worker: pin (unchanged string) + regen stale lock + drop --cascor-path + gap fixes + rebuild]  (Phase 5)
        │
        ▼
[#319 acceptance on deploy stack 0→3]  →  [remove docker-compose.cw05-stopgap.yml]  →  [close #97 / #319]  (Phase 6)
```

**What is and isn't blocked:**

- **Blocked on this relocation:** the *first publish* of `juniper-cascor-core`, and everything downstream of it (worker `main` going green without the stopgap, deploy-stack dual-path, #319/#97 closure).
- **Not blocked on this relocation:** the future `service-core`/`model-core`/`recurse` packages. Those are gated on **WS-0 ratification** and **OQ-4**, an independent track. This plan only needs to ensure cascor-core is published from the *right* home so the shared tier stays clean as those land.

---

## 8. Open decisions requiring ratification (consolidated)

| # | Decision | Options | Recommendation | Blocks | Time-sensitivity |
|---|---|---|---|---|---|
| D1 | `juniper-cascor-core` home | **S** standalone repo · **D** subdir of `juniper-cascor` | **D** (proven by the protocol precedent, lowest friction); S valid if maximal release decoupling is wanted | The entire §7 unblock chain | **High** — first publish should not happen from the wrong home |
| D2 | Rename to `juniper-cascor-model`? | keep `juniper-cascor-core` · rename now | **Lean keep** for a minimal unblock; **but rename-now is the only cheap window** if a rename is at all likely | Worker pin + package name + publish-workflow bindings + ~49 doc refs (all cheap pre-publish, permanent post-publish) | **High** — first publish forecloses a cheap rename |
| D3 | Drift-guard disposition | move to new home · move to `juniper-cascor` · delete at Wave 2 | Co-locate with the package in cascor; retire at Wave 2 | The `ci.yml` drift invocation edit | Medium |
| D4 | Where do `juniper-service-core` / `juniper-model-core` physically live? (strategy OQ-2) | juniper-ml subdir (like the 4 shared pkgs) · standalone repos | **Default to juniper-ml subdir** for consistency; revisit if code volume is large | The refactor's PyPI rollout (downstream of WS-0) | Low — decide when WS-2/WS-3 are scoped |
| D5 | Extension mechanism wording (strategy OQ-1) | entry-point discovery (as §3 reads) · subclass+inject (as the refactor chose) | **Subclass+inject**; annotate the strategy doc | Nothing (placement is mechanism-independent) | Low — doc hygiene |

Decisions **D1** and **D2** are the gates for starting the relocation. **D3** is settled inside the relocation PR. **D4** and **D5** are not on the critical path.

---

## 9. Recommended follow-up document touch-ups (not applied in this pass)

Discovered during the audit; each is a low-risk accuracy fix. They are **listed, not applied**, to keep this pass strictly investigatory and to avoid colliding with concurrent sessions. Recommend a separate small docs PR.

- **Stale status headers (factual drift):** `JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md` still reads "Status: Proposed" though doc-tools is shipped and on PyPI (0.1.1); `JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md` still reads "Status: Draft — pending design sign-off" though config-tools is shipped (0.1.0). Update both headers to "Shipped".
- **`JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md` §3 "Home" row** says "`juniper-ml/juniper-cascor-core/` subdirectory". Annotate it as **superseded by the strategy doc §8 and this plan** (home = cascor family), keeping all other mechanics.
- **`JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md` OQ-1** — annotate that the recurse refactor resolved the extension mechanism to **subclass + dependency injection** (not entry-point discovery), and soften the §3 rule's "discovered (e.g. Python entry points)" wording accordingly.
- **`META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`** lists `[tools]` with three members (predating config-tools); the live `[tools]` extra has four (ci-tools, config-tools, doc-tools, observability). Back-fill the doc.

---

## 10. Validation record

This plan was checked adversarially. The following were independently verified by sub-agents whose task was to *refute* the draft, not confirm it:

- **Ground truth (live, 2026-06-09):** every package home/version/PyPI-status row in §4 was confirmed against the real repos and the PyPI JSON API. The load-bearing facts — `juniper-cascor-core` is 0.1.0, exists only as a juniper-ml subdir, and returns **404** on PyPI; `juniper-cascor-protocol` is 0.1.0 and **published** from a juniper-cascor subdir — were both confirmed.
- **Precedent:** the `juniper-cascor-protocol` wiring (own pyproject, `publish-protocol.yml` on `juniper-cascor-protocol-v*`, `ci-protocol.yml`, consumed via a plain PyPI pin) was verified file-by-file.
- **Blast radius:** the §6.2 inventory (what moves/stays/deletes/updates) was built from a grep-level sweep of juniper-ml; the "cascor-core is not in any extra" fact was checked directly, as was the *precise* coupling of `test_workflow_script_paths.py` (it validates the drift-guard `.py` invocation but not the install/pytest lines — see §6.2).
- **Cross-document claims:** the strategy §3/§5/§8/§9 content, the migration plan's Wave structure, and the refactor's "subclass+inject" mechanism + WS-0 "not ratified" status were each cited to `file:line` in their sources.

Residual caveats recorded honestly: "shipped/merged" PR claims in the source docs (e.g. cascor#321/#322, ml#345, worker#98, cascor#324) were taken **as asserted by those docs and the project memory and were not independently re-verified against GitHub** in this pass; if any of them is not actually merged, the §7 chain's *starting* state shifts but the *plan* is unchanged. The recurse refactor's package homes (D4) are recorded as *planned*, not decided, because WS-0 is un-ratified.

**Post-adversarial revision.** This document was revised after the adversarial pass to correct the defects it surfaced: the §3.1 rule quote was restored to include "(e.g. Python entry points)"; the OQ-8 citation was corrected to the middleware-refactor doc (the strategy doc lists only OQ-1…OQ-4); and the `test_workflow_script_paths.py` coupling was stated precisely (it validates the drift-guard `.py` invocation, not the install/pytest lines).
The revision also added the GitHub-ruleset required-check teardown (§6.3 Phase 3), made the strategy §9 option-(a) sequencing consequence explicit (worker `main` stays red Phase 3 → Phase 5), added an Option-S insulation row to the §6.1 comparison, corrected the rename-cost framing (D2), and qualified the canopy and `juniper-cascor-protocol` agnosticism labels as design-intent rather than current-state.

---

## Appendix A — Package → rule mapping (one line each)

- `juniper-ml` — the shared-tier host + meta-package; stays.
- `juniper-observability` / `juniper-ci-tools` / `juniper-doc-tools` / `juniper-config-tools` — agnostic cross-cutting libraries → juniper-ml tier; **validated**.
- `juniper-cascor-core` — model implementation (cascor `candidate_unit`) → **relocate** to the cascor family.
- `juniper-cascor` / `juniper-cascor-client` / `juniper-cascor-worker` / `juniper-cascor-protocol` — cascor model family → **validated** in the cascor family.
- `juniper-data` / `juniper-data-client` — agnostic dataset tier → **validated**.
- `juniper-canopy` — UI app (agnostic by design; currently cascor-coupled) → **validated** (own repo).
- `juniper-service-core` / `juniper-model-core` — future agnostic shared packages → shared tier (physical home D4 open).
- `juniper-recurse` (+ future `-client`, `-worker`) — future model app family → own repos.
- `juniper-deploy` (orchestration) / `juniper-slacker` (local ops tool) — **not packages; out of scope**.

## Appendix B — Source documents and provenance

- Governing rule: [`JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md`](JUNIPER_CODE_ORGANIZATION_STRATEGY_2026-06-05.md) — proposal, pending ratification.
- Cascor-core mechanics (home superseded by the strategy doc): [`JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md`](JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md).
- Extraction pattern: [`CI_TOOLS_EXTRACTION_PLAYBOOK.md`](CI_TOOLS_EXTRACTION_PLAYBOOK.md), [`JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md`](JUNIPER_CI_TOOLS_PYPI_MIGRATION_PLAN_2026-05-20.md), [`JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md`](JUNIPER_DOC_TOOLS_PYPI_MIGRATION_PLAN_2026-05-18.md), [`JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md`](JUNIPER_CONFIG_TOOLS_PYPI_MIGRATION_PLAN_2026-05-22.md).
- Future packages: [`JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md), [`JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md).
- Extras contract: [`META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md`](META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md).
- Parent architectural journal: `../../notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md` (ideas #2 Common API, #4 New ABC, #7 Split up juniper-cascor; "shared by default, override if needed").
- Ground truth: live filesystem + PyPI inspection, 2026-06-09.
