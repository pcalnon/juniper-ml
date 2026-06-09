# Juniper Code Organization Strategy — Repo Boundaries for a Multi-Model Platform

**Project**: Juniper ML Research Platform
**Scope**: Cross-repo (juniper-ml, juniper-cascor\*, juniper-data, the planned middleware/core packages, future model apps)
**Author**: Paul Calnon
**Date**: 2026-06-05
**Status**: **Proposal — pending ratification** (captures a design discussion; no code moved yet)

---

## 1. Context & motivation

Extracting `juniper-cascor-core` (the CW-05 candidate-training core; see [`JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md`](JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md)) was placed, by default, as a **subdirectory of `juniper-ml`** — mirroring the four existing
shared packages (`juniper-observability`, `juniper-ci-tools`, `juniper-doc-tools`, `juniper-config-tools`).
That worked mechanically, but it surfaced a structural question worth answering **before** more model code follows the same path:

- The Juniper platform's stated research direction is the *systematic study of many constructive / architecture-growing learning algorithms* — i.e. the project will grow to **a large (eventually open-ended) number of NN models**.
- If every model's core lands in `juniper-ml`, that repo stops being accurately described as the home of **shared / common modules** and silently becomes a dual-role repo: *shared modules* **AND** *NN-model implementations*.
- The platform is also moving toward a **dedicated middleware application** (separating cascor-specific code from common interface code), which raises the prospect of a **translation / wiring layer** between each model and that middleware — and the question of where *that* lives.
- `juniper-data` already bundles dataset- (and arguably model-) specific "plugin" generators in the same repo, raising the parallel question of whether those belong there.

This document evaluates the candidate organizing approaches, derives a rule, applies it to the open questions, and records the immediate consequence for `juniper-cascor-core`. It is a **proposal** — the final call is Paul's.

## 2. The question

> As the platform scales to many NN models — each with a model implementation, some
> model↔middleware wiring, and possibly some model-specific data handling — **where should
> each kind of code live**, so the structure stays scalable, cohesive, and intuitive?

## 3. The organizing principle

The two approaches first considered (see §4) feel opposed, but they are each right about a **different axis**. Separating the axes dissolves the apparent conflict:

- **Axis 1 — Commonality.** Is a piece of code **model-agnostic** (shared by all models) or **model-specific** (one model)?
- **Axis 2 — Mechanism.** *How* does extension happen — by direct import, or through a **plugin / port** contract?

### The rule

> **Place code by commonality. Let the dependency arrow point _specific → common_, never
> _common → specific_. Extend via _interface-in-the-common-repo_ + _adapter-with-the-model_,
> discovered (e.g. Python entry points), not bundled.**

This is just the **Dependency-Inversion** and **Open/Closed** principles applied to repos: common code is *closed for modification* and *open for extension* — a new model is a **new model repo** that depends on the common interfaces, and changes **zero** common repos.

Why this is the load-bearing constraint: a platform aiming at *many* models cannot afford a structure where adding a model edits N shared repos.
The dependency direction is what keeps the cost of "model #20" the same as the cost of "model #2".

## 4. Evaluation of the approaches

### Approach A — Encapsulate per model (the "model app owns everything")

Common middleware → middleware repo; common data → `juniper-data`; **everything for one model** (implementation + middleware wiring + model-specific data handling) → that model's **application repo** (e.g. the `juniper-cascor*` family).

- **+** Maximal cohesion ("everything cascor is in the cascor family"); scales by *addition* (new model = new repo); correct dependency direction; matches the existing polyrepo `juniper-cascor` / `-worker` / `-client` family.
- **+** Intuitive for the common developer task (working on / onboarding to *a* model).
- **−** Silent on *mechanism*: without an explicit interface/registry, "wiring" can degrade into ad-hoc coupling.

### Approach B — Plugin modules bundled in the common repos

- Common data + **model-specific data plugins** both in `juniper-data`
- model-agnostic middleware + **model-specific translation-layer plugins** both in the middleware repo
- model implementations in `juniper-ml` or a new `juniper-models` repo.

- **+** Embraces *extensibility* (a plugin mechanism) — the right instinct on Axis 2.
- **−** **Inverts the dependency arrow.** If `juniper-data` / middleware *import* per-model plugins, those common repos must **know every model** → they grow with each model → adding a model edits N common repos → **coupled release cycles** → violates Open/Closed.
  - This is the disqualifying flaw for a many-model platform.
  - The plugin *mechanism* is good; the plugin *storage location* (inside the host) is wrong.

### Approach C — Ports & adapters with discovery (**recommended synthesis**)

Take **A's location** (model-specific code lives with the model) **+ B's mechanism** (a plugin/port contract).
The common repo defines the **port** (an interface/ABC/Protocol) and a **discovery mechanism** (entry points / a registry)
The **model repo** provides the **adapter** implementing that port and registers it.
The host never imports model code.

- **+** Plugin extensibility **without** the fan-in coupling — the best of A and B.
- **+** This is textbook hexagonal architecture, and (critically) it is **already the direction of the `juniper-recurse` design** (see §7).
- **−** Requires up-front interface design + a registry convention (a one-time cost the recurse work is already paying via `juniper-model-core` / `juniper-service-core`).

### Approach D — A `juniper-models` monorepo (rejected)

A single repo holding a model base + **all** model implementations as subpackages.

- **−** Re-creates the exact scaling problem we are trying to avoid: the monorepo grows with every model and couples their release cycles.
  - Note: a shared model *interface* — `juniper-model-core` — is *not* this; that is the common base, which belongs in the shared tier.
  - The implementations are what must not be monorepo'd.

### Comparison

| Criterion            | A (per-model)      | B (bundle plugins in common) | **C (ports+adapters)** | D (models monorepo) |
|----------------------|--------------------|------------------------------|------------------------|---------------------|
| Dependency direction | specific→common ✅ | **common→specific ❌**       | specific→common ✅     | mixed ❌            |
| Cost of model #N     | constant ✅        | grows ❌                     | constant ✅ | grows ❌ |
| Cohesion ("find all of X") | high ✅ | medium | high ✅ | high (but coupled) |
| Extensibility mechanism | implicit | explicit ✅ | explicit ✅ | implicit |
| Independent release per model | yes ✅ | no ❌ | yes ✅ | no ❌ |
| Matches existing direction | partly | no | **yes (recurse) ✅** | no |

## 5. The placement rule, operationalized

| Kind of code | Commonality | Home | Examples |
|---|---|---|---|
| Generic service/middleware infra | agnostic | **`juniper-service-core`** (shared pkg) | FastAPI factory, settings base, security, websocket/worker infra, generic routes, lifecycle base, `TaskDistributor` |
| Abstract model interface + contracts | agnostic | **`juniper-model-core`** (shared pkg) | `TrainableModel`/`GrowableModel` ABC, training-event + serialization contracts, conformance kit |
| Cross-cutting libraries | agnostic | shared pkgs in the **juniper-ml tier** | `juniper-observability`, `juniper-config-tools`, doc/ci-tools |
| Dataset generation/handling/delivery | agnostic | **`juniper-data`** (+ `juniper-data-client`) | spiral, equities, mnist, moon, xor, … generators |
| **Model implementation** | **specific** | **the model's app family** | cascor: `cascade_correlation`, `candidate_unit` |
| **Model↔middleware adapter (translation layer)** | **specific** | **the model's app family** (implements a `*-core` port; discovered, not imported) | a cascor `TrainableModel`/lifecycle subclass injected into `service-core` |
| **Model-specific data adaptation** (rare) | **specific** | **the model's app family** | a model-specific windowing/format adapter over `juniper-data` output |

### Dependency direction (arrows point _down_; common never imports specific)

```bash
        ┌───────────────────────── shared / common tier (juniper-ml family) ───────────────────────────┐
        |                                                                                              |
        │  juniper-model-core   juniper-service-core   juniper-observability   juniper-config-tools    │
        │   (ports/ABCs)         (infra + ports)        (metrics/log/mw)        (env aliasing)         │
        |                                                                                              |
        └───────▲──────────────────────▲────────────────────────────▲───────────────────────▲──────────┘       ┌──────────────────────────┐
                │                      │                            │                       │                  |                          |
                |                      |                            |                       |                  |  juniper-data + -client  |
   ┌────────────┴─────────┐  ┌─────────┴────────────┐               │                       │                  │   (agnostic datasets)    │
   │  juniper-cascor*     │  │  juniper-recurse*    │   …more model app families…           │                  |                          |
   |                      |  |                      |               |                       |                  └───────▲──────────────────┘
   │  • model impl        │  │  • model impl        │               │                       │                          |
   │  • adapter→ports     │  │  • adapter→ports     │  (each implements the ports;          └──────────────────────────┘
   │  • model data adapt  │  │  • model data adapt  │   common tier never imports them)
   └──────────────────────┘  └──────────────────────┘
```

Reading: model apps **depend on** the common ports and **register** their adapters; the common tier is oblivious to which models exist.

## 6. Answers to the specific questions raised

- **Should the translation layer live in `juniper-ml`?** The **port/interface** — yes, in a shared `*-core` package. The **cascor adapter** — no; it lives in the cascor app and is discovered, not imported.
- **Should translation layers be pluggable modules _in the middleware repo_?** The plugin **interface + discovery** belongs in the middleware (`service-core`); the **per-model adapter** ships with the model. Bundling adapters in the middleware re-introduces the fan-in coupling (Approach B's flaw).
- **Should `juniper-data`'s model-specific plugins move out?** Distinguish **"dataset-specific"** (e.g. the `spiral` / `equities` / `mnist` generators — usable by *any* model) from **"model-specific"**. The generators are **model-agnostic datasets** → they belong in `juniper-data` exactly as they are (the recurse design assigns *all* dataset capability to `juniper-data`). Only a genuinely *model-specific data adaptation* would move to the model app — and that is expected to be rare.
- **Model implementations in `juniper-ml` or a `juniper-models` repo?** Neither — in their **own app families**. Only the shared **`juniper-model-core` interface** belongs in the common tier.
- **Net for `juniper-ml`'s identity:** it remains the **shared / common** tier. It hosts model-*agnostic* cores and libraries; model-*specific* code never lands there.

## 7. Consistency with existing direction

This proposal does not invent a new direction — it **generalizes one already in flight**:

- **`juniper-recurse` design** ([`JUNIPER_RECURSE_DESIGN_AND_PLAN_2026-05-31.md`](JUNIPER_RECURSE_DESIGN_AND_PLAN_2026-05-31.md), in review) ratifies extracting **`juniper-service-core`** (generic FastAPI/settings/security/middleware/websocket/worker/lifecycle-base) and **`juniper-model-core`** (the abstract `TrainableModel`/`GrowableModel`, event/serialization contracts, conformance kit).
  - Reuses `juniper-observability` / `juniper-data-client` / `juniper-config-tools`; and **assigns all dataset capability to `juniper-data`**.
  - Its T1/T2/T3 tiering (pure-infra → `service-core`; semi-generic base + cascor subclass; cascor-specific stays in cascor) *is* the commonality axis; "apps subclass routes/lifecycle and inject their `TrainableModel`" *is* the ports-and-adapters mechanism.
- **Architectural Design Journal** (`Juniper/notes/JUNIPER_ARCHITECTURAL_DESIGN_JOURNAL.md`) ideas **#2 Common API**, **#4 New ABC**, **#7 Split up juniper-cascor** point the same way (extract shared base; keep model-specific subclasses), and the journal's **"shared by default, override if needed"** rule is the per-symbol version of the same principle.

The only adjustment this document makes is to state the rule **explicitly and platform-wide** (so it governs *every* repo-placement decision, not just the cascor refactor), and to draw the immediate conclusion in §8.

## 8. Immediate consequence — `juniper-cascor-core`

By the rule, **`juniper-cascor-core` is model-specific → it should not live in `juniper-ml`** (the shared/common tier). Placing it there made it the *first* model-specific thing in a shared repo — which is precisely the smell that prompted this review.

- **Where it belongs:** the **cascor family**.
  - Recommended: a **standalone `juniper-cascor-core` repo** (a peer of `juniper-cascor` / `-worker` / `-client`, depended on equally by server and worker, independently released), over a subdirectory of `juniper-cascor` (which would couple the core's release to the server repo).
  - Either beats `juniper-ml`.
- **The move is cheap right now:** the package is **not yet published to PyPI** (404 as of 2026-06-05).
  - The PyPI **name `juniper-cascor-core` is independent of the host repo**, so the worker's `juniper-cascor-core>=0.1.0` dependency **does not change** — only the publish source moves.
  - Deciding the home *before* the first publish avoids ever publishing from `juniper-ml` and later having to migrate a live package + its trusted-publisher config.
- **Boundary nuance:** the extracted package currently **mixes commonality tiers** — generic `utils` / `log_config` (which the recurse refactor will route to `service-core`) bundled with cascor-specific `candidate_unit`.
  - For the CW-05 *interim* that bundle is acceptable, but it should be **homed in cascor and labeled the interim cascor model core**, so its shape does not entrench the wrong long-term boundary.
  - The recurse `service-core` / `model-core` extraction is what eventually refines it.

## 9. Recommendation & open decisions

**Recommended:**

1. **Adopt the §3 rule as a platform convention** (this doc, once ratified, becomes the
   reference; consider a short ADR pointer from `Juniper/AGENTS.md`).
2. **Move `juniper-cascor-core` out of `juniper-ml` into the cascor family before publishing**
   (standalone repo preferred).
3. Treat the recurse `service-core` / `model-core` extraction as the mechanism that refines
   the interim bundle's boundary.

**Genuinely open (Paul's call):**

- **Standalone `juniper-cascor-core` repo vs subdirectory of `juniper-cascor`.** (Lean: standalone, for the symmetric server+worker dependency and independent release.)
- **Sequencing vs the currently-red worker `main`** (which depends on the not-yet-published package):
  - **(a) move first, then publish from the cascor home** (cleanest; worker `main` stays red a little longer)
  - **(b) publish from `juniper-ml` now to unblock, migrate the source repo later** (messier — the trusted-publisher is bound to the repo). (Lean: **(a)**.)
- **Whether to align the interim bundle's boundary with the recurse split now** (pull `utils`/`log_config` toward `service-core` immediately) **or after** the recurse extraction lands (keep the verbatim bundle for now).
  - (Lean: after — don't front-run the recurse work.)

## 10. Migration sketch (if §9.2 is approved)

Low-risk because the package is unpublished and consumer pins are name-stable:

1. Create the new home (standalone repo **or** `juniper-cascor/juniper-cascor-core/`); move the package contents + `publish-cascor-core.yml` + the drift-guard there.
    - Set up the PyPI project + trusted publisher against the **new** repo.
2. Revert the package's addition to `juniper-ml` (keep this strategy doc + the migration plan doc; drop the `juniper-cascor-core/` tree and `tests/test_cascor_core_drift.py` from `juniper-ml`, or relocate the drift-guard to the new home / cascor).
3. Publish `juniper-cascor-core v0.1.0` from the new home; regenerate the worker `requirements.lock`; worker `main` goes green.
4. Proceed to the deploy-stack acceptance (the #319 repro → 0→3) and revert the temporary `docker-compose.cw05-stopgap.yml`.

(If §9.2 is **not** approved and the package stays in `juniper-ml`, only step 3-onward applies — see the migration-plan doc's unblock sequence.)

## 11. Open questions

- **OQ-1 — Registry convention. RESOLVED 2026-06-09.**
  - The recurse middleware-refactor design adopts **compile-time subclassing + dependency injection** (apps subclass routes/lifecycle and inject their `TrainableModel`), *not* a runtime entry-point registry. The §3 rule's "discovered (e.g. Python entry points)" is illustrative only; the operative mechanism is subclass + inject.
  - Placement conclusions are mechanism-independent, so nothing in §5/§8 changes. (Original question, now answered: what discovery mechanism do the `*-core` ports use for adapters — entry-points group, or an explicit `register()` at import?)
- **OQ-2 — Where do the shared `*-core` packages physically live?**
  - Same `juniper-ml` subdirectory-published pattern as the other shared packages, or standalone repos?
    - (They are genuinely common, so the `juniper-ml` tier is consistent — but the volume of model-core / service-core code may argue for standalone.)
- **OQ-3 — Client libraries.**
  - `juniper-cascor-client` / future `juniper-recurse-client` are model-specific by name but thin; confirm they follow the per-model-family rule (they already do).
- **OQ-4 — Naming.**
  - "core" is doing double duty (`model-core`/`service-core` = shared abstractions; `cascor-core` = a specific model's code).
  - Consider a clearer convention to avoid implying `cascor-core` is shared.
    - (e.g. `juniper-cascor-model` for the specific tier)

---

## Appendix A — Originating discussion (verbatim prompt)

Preserved per the project's "keep the design conversation" convention.
The response to this prompt is the body of this document (§3–§9).

> before we continue, let's reconsider the repo location of juniper-cascor-core.
>
> as the juniper project continues to grow, there will be other, and eventually a large
> number of, nn model designs included in the project. if we move the model specific code,
> e.g., juniper-cascor-core, into juniper-ml for all implemented models, juniper-ml will no
> longer be accurately described as the repo for "shared modules". instead, it will come to
> serve a dual role as the repo for "shared modules" AND "NN Model implementations".
> additionally, the juniper project is moving toward a dedicated middleware application —
> refactoring to separate cascor specific code from potentially common interface code. this
> suggests a real possibility that some form of "translation layer" might need to be added
> between the nn model code and the project middleware. should the translation layer also be
> stored in the juniper-ml repo? should translation layers be stored as "plugable" modules in
> the middleware repo? similarly, the juniper-data application design currently includes
> dataset-specific or nn model-specific "plugin" modules bundled in the same juniper-data
> repo. should these non-common modules be kept in the juniper-data repo, or should they be
> moved into a nn model specific application repo?
>
> approach to consider: keep all middleware functionality common to all NN models in a
> middleware repo; keep all dataset functionality common to all NN models in the juniper-data
> repo; bundle in a model-specific application repo (e.g. juniper-cascor): the nn model
> implementation, whatever translation / wiring layer is needed to connect the model to the
> middleware application, and any model specific modules needed for custom data handling not
> common to all NN models. this would potentially allow anything related to a specific NN
> model to be encapsulated in a single application repo.
>
> alternate (plugin style): juniper-data stores modules common to all datasets plus nn-model
> specific plugins; the new middleware contains model & dataset agnostic code plus model
> specific translation-layer plugins; the nn model implementations could be kept in juniper-ml
> or in a new juniper-models repo.
>
> at this point, i'm uncertain which approach would be better, cleaner and more intuitive.
> let's evaluate these and other possible approaches to project organization before we go too
> far down the refactoring path.

The two named approaches map to **A** (encapsulate per model) and **B** (bundle plugins in the common repos) in §4; the recommendation is the **C** synthesis (A's location + B's mechanism), which is also the `juniper-recurse` design's direction.
