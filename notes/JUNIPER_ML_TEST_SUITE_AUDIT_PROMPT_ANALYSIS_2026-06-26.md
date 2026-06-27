# Prompt-Development Analysis — Comprehensive Test-Suite Audit (9 Juniper Apps + Sub-Modules)

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**Document Type**: ANALYSIS (prompt development + meta-analysis)
**Status**: Complete
**Last Updated**: 2026-06-26

---

## 1. Purpose

This session was asked to **develop a prompt** (not to perform the audit) that will start a future session whose deliverable is a **rigorous, comprehensive plan to audit the test suites of all 9 Juniper applications** (and their packaged sub-modules).
The motivating premise: after a multi-stage refactor across all 9 repos, every application's test suite is **green**, yet `juniper-canopy` is broken badly enough at runtime that basic functionality does not work — which implies **systemic gaps in the test
suites themselves**.
The audit the prompt defines must, at minimum, target: per-source-file coverage **≥90%**; packaged-sub-module average coverage **≥95%**; **click-through** tests for user-facing webapp functionality; and **regression tests for every issue** found by a contemporaneous canopy
debugging session, with the plan able to **re-ingest newly-appended issues across iterations**.
Custom agents were to be employed as needed, and a **meta-analysis** was to record additional helpful agent specializations and any other Juniper issues discovered.

**Deliverables produced this session:**

1. **The prompt (primary):** [`prompts/generated/JUNIPER_ECOSYSTEM_TEST-SUITE-AUDIT_PLAN_2026-06-26_1548.md`](../prompts/generated/JUNIPER_ECOSYSTEM_TEST-SUITE-AUDIT_PLAN_2026-06-26_1548.md) — a filled copy of the `plan` (planning-class) template, fully grounded, validated against the suite RUBRIC.
2. **This analysis document:** (session record + the 19-unit survey the prompt grounds against + meta-analysis).

---

## 2. The primary deliverable and its validation

- **Template selected:** `plan` (`prompts/agent_templates/plan.md`, `class: planning`,
  `required_fields: [subject, resources]`). Rationale: the downstream deliverable is a **planning
  document** (a test-suite-audit plan), not code and not a findings report. Candidates rejected:
  `audit` (analysis-class, but it produces a *findings report*, whereas the task wants a *forward plan*);
  `failing-tests` (the suites are **green**, not red); `task`/`generic` (less specific). Planning-class
  also correctly exempts the prompt from RUBRIC **R2.6** (the verify-&-recover contract is for
  execution-class prompts that change code).
- **Grounding:** a real discovery bundle was generated for the juniper-ml worktree
  (`python util/prompt_discovery/cli.py --repo-root .`; on-HEAD `2fdea19`, all seven probes `ok` except
  `test_status: cold_cache` — expected, the meta-package uses `unittest`, so there is no pytest cache).
  Because the prompt is **ecosystem-wide** but the discovery CLI is **single-repo** (architectural
  limitation A-1, below), cross-repo anchors were grounded **first-party** (every cited sibling-repo
  path / symbol / threshold was re-probed with `test -e` / `grep` on the shared filesystem under
  `/home/pcalnon/Development/python/Juniper/`).
- **Validation:** delegated to the **`prompt-validator`** subagent with the **corrected**
  `prompts/agent_templates/` paths (the validator's own definition still points at the renamed-away
  `prompts/templates/` — issue I-1). It independently re-probed every anchor.

**Validation iteration history (honest record):**

| Iter | Verdict  | Blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Resolution                                                                                                                                                                                                                                                                                                                                                                                                     |
|------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1    | **FAIL** | **R3.4** — the "read first" companion-analysis doc cited in §Resources did not exist yet (it is *this* document, written after the prompt) **and** was cited at the main-repo absolute path while the session runs in a worktree with a separate `notes/`. Every other anchor (19 units, crash sites, the `conftest.py:371` mock fixture, client symbols, the canopy UI harness, ports, flags, conventions, the cascor-model no-gate outlier, the `.coveragerc.torch` precedent) grounded **true**. | (a) Authored this companion doc (its 19-unit survey is §4 below); (b) re-pointed the prompt's anchor to the **repo-relative** `notes/…` path; (c) **inlined a compact 19-unit survey table** into the prompt's §Resources so it is self-grounding and no longer hard-depends on reading a second file.                                                                                                         |
| 2    | **PASS** | — (one `minor` only)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Validator returned `overall: PASS`, `validator_status: ok`, **0 blocker / 0 major**, all 13 `hallucination_risk` entries `grounded: true`. Sole `minor` (R2.4): the prose said "20 coverage units" while the survey table has 19 rows — `juniper-recurrence`'s repo root is a container (no `pyproject.toml`), not a unit. **Corrected to 19** across the prompt and this document → effectively `EMIT_CLEAN`. |

> The iteration-1 blocker was a pure **sequencing/forward-reference** defect, not a substantive
> grounding error — the validator did its job (caught a cited-but-absent artifact) and the rest of the
> prompt was already sound. This is exactly the failure mode the RUBRIC's R3.4 hard gate exists to catch.

---

## 3. How the prompt was developed (work performed)

1. **Suite study (direct).**
    - Read the `template-agent` Skill, the template `manifest.yaml` + `RUBRIC.md`, the `plan`/`audit` templates, the `planner` / `prompt-validator` agent definitions, and the `data/` convention layer (`conventions.yaml`, `ecosystem.yaml`, `standing_rules.yaml`) to match the suite's contract and quality bar, and to select the right template + class.
2. **Test-infrastructure survey (delegated, read-only `general-purpose` agent).**
    - Surveyed all 9 repos **plus** their packaged sub-modules for runner, exact test command, CI-enforced coverage threshold + where it lives, test layout/markers, E2E presence, and source/test file counts.
    - This produced §4 and surfaced the count correction (the ecosystem is **19 coverage units**, not 9 — see §4).
3. **Debug-doc reconnaissance (delegated, read-only `Explore` agent).**
    - Located and summarized the contemporaneous canopy debug-findings document, its issue-ID taxonomy, and its current issue set — the regression-test source the prompt must wire in re-entrantly.
4. **First-party anchor verification (direct).**
    - `test -e` / `grep` confirmed every cross-repo anchor the prompt asserts (the 19 units' `pyproject.toml`s, the canopy `src/tests/ui/` harness + crash sites, the `mock_juniper_data_client` fixture at `conftest.py:371`, the cascor bash harness, the recurrence-model `.coveragerc.torch`, the gate-less `ci-cascor-model.yml`).
5. **Authoring + validation (delegated, `prompt-validator` subagent).**
    - Filled a copy of `plan.md`, mapped every task requirement to an ordered directive / enumerated deliverable, then validated (§2; iter-1 FAIL → fixes → iter-2 PASS).

Agents employed — all via the Agent tool:

- `general-purpose` (infra survey)
- `Explore` (debug-doc recon),
- `prompt-validator` (validation)

This satisfied "employ custom agents as needed" and dogfooded the suite end-to-end, cross-repo.

---

## 4. The 19-unit test-infrastructure survey (the grounded inventory)

**Scope correction:** the 9 Juniper repos resolve to **19 coverage units** — 8 top-level (the 7 source repos + `juniper-deploy`, which is tests-only/no importable source) + 11 packaged sub-modules; `juniper-recurrence`'s repo root is a container realized by its 3 sub-packages, not a separate unit.
The survey found more packaged sub-modules than the 9-app brief implied: `juniper-cascor` ships `juniper-cascor-model` + `juniper-cascor-protocol`; `juniper-recurrence` is a **container** whose testable code is three sub-packages (`juniper-recurrence` app, `-model`, `-client`) plus a `bench/` API-e2e lane.
The recurrence app is **headless FastAPI** (Starlette `TestClient`) — **`juniper-canopy` is the only repo in the ecosystem with real click-through / browser tests.**

| Coverage unit                      | Runner             | Coverage gate (CI-enforced)                                               | Threshold | Click-through E2E?                          | src/test .py (approx) |
|------------------------------------|--------------------|---------------------------------------------------------------------------|-----------|---------------------------------------------|-----------------------|
| `juniper-ml` (meta)                | unittest           | **none** (intentional)                                                    | —         | no                                          | 30 / 32               |
| ml · `juniper-observability`       | pytest             | `--cov-fail-under` in `ci-observability.yml`                              | **90**    | no                                          | 15 / 12               |
| ml · `juniper-service-core`        | pytest             | `ci-service-core.yml` (+ `pyproject` `fail_under=80`)                     | **80**    | no                                          | 41 / 16               |
| ml · `juniper-model-core`          | pytest             | `ci-model-core.yml`                                                       | **95**    | no                                          | 17 / 7                |
| ml · `juniper-ci-tools`            | pytest             | `ci-ci-tools.yml`                                                         | **85**    | no                                          | 11 / 7                |
| ml · `juniper-config-tools`        | pytest             | `ci-config-tools.yml`                                                     | **85**    | no                                          | 4 / 3                 |
| ml · `juniper-doc-tools`           | pytest             | `ci-doc-tools.yml`                                                        | **85**    | no                                          | 6 / 4                 |
| `juniper-canopy`                   | pytest             | `ci.yml` unit gate (`unit/ + regression/` only)                           | **80**    | **YES — Playwright (`ui-tests`, blocking)** | 75 / 278              |
| recurrence · app                   | pytest             | `ci-recurrence-app.yml`                                                   | **90**    | no (FastAPI `TestClient`)                   | 20 / 15               |
| recurrence · `-model`              | pytest             | `ci-recurrence-model.yml` (+ torch job)                                   | **90** ×2 | no                                          | 8 / 8                 |
| recurrence · `-client`             | pytest             | `ci-recurrence-client.yml`                                                | **90**    | no                                          | 5 / 7                 |
| `juniper-cascor`                   | pytest + bash      | `ci.yml`: `pytest -m "unit and not slow" … --cov=src` → `coverage report` | **80**    | no                                          | 109 / 194             |
| cascor · `juniper-cascor-model`    | pytest             | **none** — `ci-cascor-model.yml` = `pytest -v` (the outlier)              | —         | no                                          | 27 / 10               |
| cascor · `juniper-cascor-protocol` | pytest             | `ci-protocol.yml`                                                         | **95**    | no                                          | 10 / 3                |
| `juniper-cascor-client`            | pytest             | `ci.yml` → `coverage report --fail-under`                                 | **80**    | no                                          | 11 / 13               |
| `juniper-cascor-worker`            | pytest             | `ci.yml` → `coverage report --fail-under`                                 | **80**    | no                                          | 9 / 18                |
| `juniper-data`                     | pytest (ruff lint) | `ci.yml` → `coverage report --fail-under`                                 | **80**    | no                                          | 101 / 68              |
| `juniper-data-client`              | pytest             | `ci.yml` → `coverage report --fail-under`                                 | **80**    | no                                          | 8 / 15                |
| `juniper-deploy`                   | pytest             | **none** (no importable source; Compose-config tests)                     | —         | no                                          | 0 / 21                |

Canonical commands per unit (representative):

- `cd juniper-ml && python3 -m unittest -v tests/test_*.py`
- `cd juniper-canopy && make coverage` (+ `make test-ui`)
- `bash juniper-cascor/src/tests/scripts/run_tests.bash`
- `cd <dir> && pytest --cov=<import_pkg> --cov-report=term-missing`
  - run for each sub-module

### Systemic gaps (the heart of why the suites are green but canopy is dead)

1. **No per-file coverage gate exists anywhere.** Every gate is an **aggregate** `--cov-fail-under` / `coverage report --fail-under`.
    - The owner's "per-file ≥90% / sub-module-avg ≥95%" target is therefore **greenfield in all 19 units** — there is no existing mechanism to extend.
2. **Thresholds often live only in the CI YAML, not `pyproject.toml`** (observability, model-core, ci-tools, config-tools, doc-tools, and the cascor/client/worker/data family via `coverage report --fail-under=$ENV`).
    - A bare local `pytest` is therefore **ungated** — drift can land green locally.
3. **Aggregate computed from a partial subset.** The two biggest repos compute their gate from a **unit-only** subset against the **whole** `src/` tree (cascor: `-m "unit and not slow"`; canopy: `unit/ + regression/` only).
    - Integration / UI / golden / conformance suites exist but feed **no** coverage number — the headline % overstates exercised source.
4. **Mocked integration seams hide real breakage.** Canopy's suite mocks both Juniper clients (autouse session fixture `mock_juniper_data_client`, `src/tests/conftest.py:371`), so the **real client constructor signatures are never exercised** — which is exactly why a constructor `TypeError` from a version-drifted wheel sailed past a green suite.
    - This "green tests / dead app" class is the audit's central target.
5. **One published package has zero coverage enforcement:** `juniper-cascor-model` (a real PyPI package, 27 source files, `pytest -v` only).
6. **Only one click-through surface exists** (canopy Playwright) — the pattern the audit must replicate for any other user-facing webapp.

---

## 5. The downstream task in one line

Produce a grounded, owner-actionable **plan** that, when executed, makes the 20 Juniper coverage units reach per-file ≥90% / sub-module-avg ≥95%, gives every user-facing webapp click-through tests modeled on canopy's harness, adds a **regression test for every issue** in the contemporaneous canopy debug doc via a **re-runnable ingestion procedure** that keeps absorbing newly-appended issues, and installs durable guards against the "green tests / dead app" class itself.

---

## 6. Meta-Analysis

### 6.1 Additional custom-agent specializations that would help

The current suite (`planner`, `auditor`, `task-executor`, `prompt-validator`, the `template-agent` Skill) is **static / read-only or single-task-execution**; none observes live runtime behavior or computes coverage.
Building on the sibling canopy debug session's §6.1 (which proposed a **live-runtime / service-smoke diagnostician**, an **environment / dependency-drift checker**, and **first-class cross-repo grounding** — all directly relevant here too), this test-audit effort additionally wants:

1. **Per-file coverage-gap mapper (highest test-audit-specific value).** Given a repo + its real test command, run coverage, parse `coverage json`, and emit the per-file distribution, the list of files below 90%, and each sub-module's average vs the 95% bar — automating audit directives 1–2 across 19 heterogeneous units.
    - Naturally hosted as a shared tool in `juniper-ci-tools` (with a dogfood test in `juniper-ml/tests/`), carrying the numpy-2.x dotted-`--cov` workaround as a first-class concern.
2. **Mocked-seam gap auditor (novel, high value).** A variant of `auditor` that hunts the exact pattern that hid the canopy breakage: autouse/session fixtures that **mock an integration boundary**, leaving the real construction/call path at that boundary untested.
    - It would flag "suite mocks X at the seam, so it cannot catch X-construction/-signature bugs" — turning the post-mortem insight into a standing check.
3. **Click-through test author.** Given a Dash/web UI and a target flow, generate a Playwright test modeled on canopy's `src/tests/ui/` harness (boot-in-demo → `goto` → fill → assert callback chain).
    - Pairs with the live-runtime diagnostician.

A live-runtime / service-smoke diagnostician (debug-doc §6.1.1) remains the single highest-value addition overall, because the "green tests, dead app" class is invisible to every current suite member by construction; the three above make the *coverage-and-regression* half of this audit tractable.

### 6.2 Other Juniper issues discovered this session

Classified per the requested taxonomy.
Each is **documented, not fixed** (this session's deliverables were the prompt + this analysis).
Where the sibling canopy debug doc already recorded an issue, it is **cross-referenced, not re-claimed**.

**Incomplete development:**

- **(I-1, corroborated) `prompts/templates/` → `prompts/agent_templates/` rename drift in suite prose.**
  - Independently re-hit this session: delegating to `prompt-validator` required **overriding** the rubric/ manifest paths because `.claude/agents/prompt-validator.md` still instructs reading `prompts/templates/RUBRIC.md` / `…/manifest.yaml` (renamed away), and `prompts/agent_templates/RUBRIC.md` itself still references `prompts/templates/data/*.yaml` (e.g. R2.5 text). The library **tests** pass because they use the new path; the drift lives in **agent/rubric prose** that tests don't execute.
  - Now confirmed by **two independent sessions**.
  - *Recommend:* sweep the dead path across `.claude/` + `AGENTS.md` + `RUBRIC.md`, and add a lint that greps agent/Skill/rubric bodies for `prompts/templates/`.
  - **Owner: juniper-ml.**

**Configuration problems:**

- **(NEW) `AGENTS.md` "Repository Structure" tree is stale.**
  - It documents a top-level `prompts/templates/` (the real dir is `prompts/agent_templates/`) and omits the present top-level `conf/` and `papers/` directories and the in-tree packaged sub-modules (`juniper-model-core/`, etc.).
  - *Recommend:* refresh the tree; fold into the I-1 sweep.
  - **Owner: juniper-ml.**
- **(C-1, cross-ref) Data-layer `ecosystem.yaml` conda-env staleness** (`JuniperCanopy 3.14` vs the live `JuniperCanopy1 3.13`) — recorded by the debug doc; relevant here because the prompt deliberately **avoided** injecting conda-env values to dodge a false R2.5 failure.
  - **Owner: juniper-ml.**

**Design gaps:**

- **(NEW, systemic) No per-file coverage gate anywhere; thresholds frequently CI-YAML-only; aggregates from partial subsets.**
  - See §4 systemic gaps 1–3. This is the test-strategy design gap that lets a broken app ship green.
  - *Recommend:* the per-file gate + a shared enforcement tool (6.1.1); move thresholds into `pyproject.toml` so local runs are gated; measure the gate against the suite actually run.
  - **Owner: all repos (juniper-ml to lead the shared tool).**
- **(A-2, cross-ref) No live-runtime coverage in the suite** — by design it cannot catch "green tests / dead app."
  - **Owner: juniper-ml.**

**Architectural weaknesses:**

- **(A-1, corroborated) The custom-agent suite is single-repo by construction.**
  - Hit directly this session: an **ecosystem-wide** prompt had to be grounded against a **single-repo** discovery bundle, and the validator had to be told to re-probe cross-repo anchors on the shared filesystem.
  - Since the suite's home is juniper-ml and most targets are sibling repos, **cross-repo is the common case**.
  - *Recommend:* a first-class `--target-repo` (cross-repo) mode for `prompt_discovery` + `prompt-validator`.
  - **Owner: juniper-ml.**
- **(NEW) Release-gating inconsistency:** `juniper-cascor-model` is published to PyPI yet has **no coverage gate** (`pytest -v` only), while peer sub-packages enforce 90–95%.
  - *Recommend:* bring it to the sub-module bar as part of the audit rollout.
  - **Owner: juniper-cascor.**

**Syntax errors:**

- **None found.** No syntax errors were encountered this session (every cited artifact parsed/resolved).  Recorded explicitly so the absence is not mistaken for "not checked."

**Suspected (unverified this session):**

- **(S-1, cross-ref) Sibling-env plain-wheel drift** (`JuniperCascor1` / `JuniperData` may share canopy's installed-vs-lockfile drift) — flagged by the debug doc; a short ecosystem env-drift audit is warranted.
  - **Owner: juniper-ml (audit).**

### 6.3 What worked (process note)

Dogfooding the suite **cross-repo** again succeeded: a delegated survey agent inventoried 20 coverage units, a delegated recon agent located and parsed the live debug-findings doc, the discovery CLI produced a clean on-HEAD bundle, and the `prompt-validator` independently re-probed every anchor and **caught a real forward-reference defect** (the not-yet-written companion doc) — proving the R3.4 hard gate earns its keep.
The single-repo and rename workarounds (A-1, I-1) remain the only friction.

---

## 7. Appendix — key reproduction commands

```bash
# Regenerate the discovery grounding bundle for the juniper-ml worktree
cd <juniper-ml worktree> && python util/prompt_discovery/cli.py --repo-root . \
  --subject "test-suite audit plan across 9 Juniper apps + sub-modules" \
  --symbols "prompt_discovery,template_data_resolver,editable_install_drift_check"

# The 19-unit count: 8 top-level units + 11 packaged sub-modules
J=/home/pcalnon/Development/python/Juniper
for d in juniper-ml/juniper-observability juniper-ml/juniper-service-core juniper-ml/juniper-model-core \
         juniper-ml/juniper-ci-tools juniper-ml/juniper-config-tools juniper-ml/juniper-doc-tools \
         juniper-cascor/juniper-cascor-model juniper-cascor/juniper-cascor-protocol \
         juniper-recurrence/juniper-recurrence juniper-recurrence/juniper-recurrence-model \
         juniper-recurrence/juniper-recurrence-client; do test -f "$J/$d/pyproject.toml" && echo "OK $d"; done

# The green-but-dead linchpin: the suite mocks the client seam that the real bug lives behind
grep -n "mock_juniper_data_client" "$J/juniper-canopy/src/tests/conftest.py"   # -> 371: def mock_juniper_data_client()

# The no-coverage-gate outlier
grep -nE "pytest|--cov|fail-under" "$J/juniper-cascor/.github/workflows/ci-cascor-model.yml"  # -> only 'python -m pytest -v'

# Locate the current canopy debug-findings doc (re-entrant ingestion seed)
find "$J/juniper-ml/notes" "$J/juniper-canopy/notes" -iname 'JUNIPER_CANOPY_*DEBUG*' -o -iname 'JUNIPER_CANOPY_*FINDINGS*' 2>/dev/null
```

---
