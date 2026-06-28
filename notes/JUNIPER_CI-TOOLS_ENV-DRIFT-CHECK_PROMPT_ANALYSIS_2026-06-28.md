# Prompt-Development Analysis — `juniper-env-drift-check` (Test-Suite Audit Phase A1 / §10.1)

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**License**: MIT License
**Document Type**: ANALYSIS (prompt development + meta-analysis)
**Status**: Complete
**Last Updated**: 2026-06-28

---

## 1. Purpose

This session was asked to **develop a validated, correct, effective prompt** (not to perform the work) that **begins implementing** the ecosystem test-suite audit plan
([`JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md`](JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md), merged as juniper-ml#569), using the custom-agent suite ("appropriate sub-agents").

**Deliverables produced this session:**

1. **The prompt (primary):** [`prompts/generated/JUNIPER_CI-TOOLS_ENV-DRIFT-CHECK_TASK_2026-06-27_1655.md`](../prompts/generated/JUNIPER_CI-TOOLS_ENV-DRIFT-CHECK_TASK_2026-06-27_1655.md) — a filled copy of the `task` (execution-class) template, fully grounded, validated **PASS** by the `prompt-validator` subagent.
2. **This analysis document** (session record + scope-evolution + validation history + meta-analysis).

---

## 2. The primary deliverable and its validation

- **Template selected:** `task` (`prompts/agent_templates/task.md`, `class: execution`, `required_fields: [task, resources, acceptance]`). Rationale: the downstream deliverable is **code** (a console script + tests) landed as a PR. Candidates rejected: `regressions` (the root cause is already diagnosed + documented — this is forward implementation, not a fresh diagnosis), `failing-tests` (the suites are green), `plan`/`audit` (the plan already exists; this executes it), `generic` (less specific). Execution-class correctly pulls in RUBRIC **R2.6** (verify-&-recover), which the prompt needs (it changes code + opens PRs).
- **Grounding:** a real discovery bundle was generated for canopy (`python util/prompt_discovery/cli.py --repo-root <canopy>`; on-HEAD `31c7c995`, all seven probes `ok`). Because the work spans `juniper-ml` (primary) + `juniper-canopy` (consumer) and the discovery CLI is single-repo (architectural limitation A-1), all cross-repo anchors were re-probed **first-party** by two read-only `Explore` sub-agents on the shared filesystem.
- **Validation:** delegated to the **`prompt-validator`** subagent, which independently re-probed every asserted path / symbol / version / port / env / flag and applied the RUBRIC.

**Validation iteration history (honest record):**

| Iter | Verdict  | Blocker | Resolution |
|------|----------|---------|------------|
| 1 | **FAIL** | **R2.4** (`major`, internal consistency). The prompt directed a minor `_version` bump (`0.4.0`→`0.5.0`) and required `tests/test_ci_tools_drift.py` to stay green, but accounted only for the **canopy** pin (deferred to PR2) and juniper-ml's unbounded `[tools]` pin. It **missed** that juniper-ml's OWN three workflows pin `juniper-ci-tools>=0.1.0,<0.5.0` (`ci.yml:459`, `docs-full-check.yml:226`, `lockfile-update.yml:48`) and that `test_juniper_ml_own_workflows_pin_current_version` is **ungated** (runs every PR), so `0.5.0` would fail that dogfood test *inside PR1*. Every other anchor grounded `true`. | Directive 3e now mandates **widening those three own-workflow pins (→ `<0.6.0`) in the same PR1** as the bump; §Resources names the ungated test + the three pins; §Constraints locates the `<0.5.0` bound in both PR1 (own workflows) and PR2 (canopy). |
| 2 | **PASS** | — | Validator returned `overall: PASS`, `validator_status: ok`, **0 findings**, all `hallucination_risk[].grounded == true`. The three newly-cited workflow anchors re-probed exact; no new inconsistency introduced. |

> The iteration-1 blocker was a genuine cross-file consistency defect (a version bump silently breaking an ungated dogfood lint two directories away), not a grounding error — exactly the class the `prompt-validator` exists to catch. The suite earned its keep.

---

## 3. How the prompt was developed (work performed)

1. **Owner scoping (two `AskUserQuestion` rounds).** The plan is multi-phase; the owner first chose the **entry point** (Canopy A1 — the env-floor guard, the plan's mandated canopy-first start). Grounding then discovered A1's canopy deliverable already exists (§5), so a second question confirmed the **rescope** to §10.1's shared tool.
2. **Grounding (two read-only `Explore` sub-agents + the discovery CLI).** Re-confirmed at current HEAD: the floor drift the guard targets, the crash sites, the mocked seams, the existing canopy floor test, the `juniper-ci-tools` packaging/console-script idiom, the CI gate, the publish flow, the canopy CI insertion point, and the consumer-pin guards.
3. **Authoring.** Filled a copy of `task.md`, mapping the owner's intent to ordered directives + measurable acceptance criteria, injecting only grounded anchors.
4. **Validation (`prompt-validator` subagent).** Iter-1 FAIL → fix → iter-2 PASS (§2).
5. **Emission.** Written to `prompts/generated/` under the convention `JUNIPER_<APP>_<SUBJECT>_<TYPE>_<DATE>_<HHMM>.md` (confirmed parseable by `util/generated_prompt_index.py`).

Agents employed — all via the Agent tool: `Explore` ×2 (grounding), `prompt-validator` (validation). This dogfooded the suite end-to-end, cross-repo.

---

## 4. Scope evolution (the load-bearing discovery)

The owner's chosen entry point — **Canopy A1, "a dependency-satisfaction check + canopy `test_env_satisfies_floors`"** — turned out **partly shipped**: `juniper-canopy/src/tests/unit/test_client_version_floors.py` already implements the floor check (reads installed versions via `importlib.metadata` — bypassing the conftest mocks — and compares against `pyproject.toml` floors parsed with `tomllib` + `packaging`; its docstring even cites the 2026-06-26 incident).

What is **genuinely missing** (plan §10.1's durable guard) and therefore what the prompt targets:

- A **shared, reusable** `juniper-env-drift-check` console script in `juniper-ci-tools` (today there is no env-drift checker there) — so any repo, not just canopy, can assert its active environment satisfies its declared floors.
- **Closing the plain-wheel gap:** `util/editable_install_drift_check.py:148,153-154` inspects only *editable* installs (`direct_url.json` / `dir_info.editable`); canopy's drift was **plain wheels**, so that class is unguarded ecosystem-wide.

The prompt therefore directs **generalize, do not duplicate** (the canopy test stays).

---

## 5. The downstream task in one line

Generalize canopy's proven client-floor-drift guard into a reusable **`juniper-env-drift-check`** console script in `juniper-ci-tools` (plain wheels included; `--check-lock` validates `requirements.lock` vs floors), with its own unit tests (≥85% gate) and a `juniper-ml/tests/` dogfood test, landed as a **self-contained juniper-ml PR1**; then — after the owner publishes `juniper-ci-tools` — wire canopy to run it as a preflight (**PR2**). PR1 also widens juniper-ml's own three `<0.5.0` workflow pins alongside the `0.5.0` bump.

---

## 6. Meta-Analysis

### 6.1 Suite friction observed this session

1. **Discovery cannot detect "deliverable already (partly) exists."** The single most consequential fact this session — that A1's canopy test was already written — was found only by a grounding `Explore` agent, not by any discovery probe, and forced a mid-flight rescope (a second owner question). A **"prior-art / already-shipped" probe** (grep the target repo for an existing test/symbol matching the task's intent before drafting) would catch this class up front. Builds on the debug doc's §6.1 agent-specialization wishlist.
2. **The single-repo limitation (A-1) bit again.** A `juniper-ml`+`juniper-canopy` task had to be grounded against a single-repo discovery bundle + manual cross-repo `Explore` re-probes. A first-class `--target-repo` / multi-repo mode remains the highest-value suite fix for cross-repo prompts (the common case).
3. **The validator's value was concrete.** R2.4 (a version bump breaking an ungated lint two directories away) is precisely the cross-file consistency a human author misses; the `prompt-validator`'s independent re-probe caught it with reproducible evidence.

### 6.2 Other Juniper issues (referenced, not re-discovered)

- **DISC-1 (configuration / env-drift, CONFIRMED live; still unfiled).** `juniper-recurrence` app + client `pyproject.toml:132` filter `starlette.exceptions.StarletteDeprecationWarning`, absent from the live env's Starlette → `pytest --co` errors at config-parse. Recorded in the audit plan §14.2; owner: juniper-recurrence. A separate fix, surfaced again here only because it is the same env-drift class this prompt's tool guards against.
- The **env-floor-drift guard gap itself** (no shared, plain-wheel-aware checker) is the design gap this prompt closes (plan §10.1 / A-2).

No syntax errors encountered; every cited artifact resolved (validator iter-2: all anchors `grounded: true`).

---

## 7. Appendix — key reproduction commands

```bash
J=/home/pcalnon/Development/python/Juniper

# Regenerate the canopy discovery bundle
cd "$J/juniper-ml" && python util/prompt_discovery/cli.py \
  --repo-root "$J/juniper-canopy" \
  --subject "canopy A1 env-floor-drift guard" \
  --symbols "JuniperDataClient,CascorControlStream,save_snapshot,create_backend"

# The already-shipped canopy floor test (generalize, do NOT duplicate)
sed -n '1,40p' "$J/juniper-canopy/src/tests/unit/test_client_version_floors.py"

# The plain-wheel gap (editable-only)
sed -n '145,156p' "$J/juniper-ml/util/editable_install_drift_check.py"

# The R2.4 catch: juniper-ml's own <0.5.0 pins the bump must widen in PR1
grep -rnE 'juniper-ci-tools>=' "$J/juniper-ml/.github/workflows/"*.yml

# Confirm the emitted prompt name parses the convention
cd "$J/juniper-ml" && python util/generated_prompt_index.py | grep ENV-DRIFT-CHECK
```

---
