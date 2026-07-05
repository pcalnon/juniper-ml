# Comprehensive Test-Suite Audit & Remediation Plan — 19 Juniper Coverage Units

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**License**: MIT License
**Document Type**: PLAN (test-suite audit + remediation roadmap)
**Status**: Ratified — skeptical second pass complete (§13)
**Last Updated**: 2026-06-26

---

## 0. How to read this document

This is a **planning document only**. No tests were added, no source changed, no CI touched in the
authoring session — execution is downstream, one PR per work unit (§11).

It is grounded against the real repositories under `/home/pcalnon/Development/python/Juniper/`
(henceforth `$J`) at the time of writing. Every cited `file:line` was re-probed first-party against
the actual repo (directive 1). The starting point was the 19-unit survey in
[`notes/JUNIPER_2026-06-26_JUNIPER-ML_TEST-SUITE-AUDIT-PROMPT-ANALYSIS.md`](JUNIPER_2026-06-26_JUNIPER-ML_TEST-SUITE-AUDIT-PROMPT-ANALYSIS.md);
**§3 records every place reality differed from that survey.** Where a claim could not be grounded it
is flagged, not invented.

**Owner-pinned values carried faithfully (not softened):** per-source-file line coverage **≥90%**;
packaged-sub-module **average ≥95%**; **click-through** tests for every user-facing webapp;
**a regression test for every issue** in the canopy debug doc behind a **re-entrant ingestion**
procedure that keeps absorbing newly-appended issues. Everything else leaves owner latitude.

---

## 1. The problem this audit exists to close

After a multi-stage refactor across all 9 Juniper repos, **every test suite is green, yet
`juniper-canopy` is broken at runtime**: the local `JuniperCanopy1` env holds client wheels *below*
the code's `pyproject.toml` floors, so the adopted client APIs (`JuniperDataClient(on_request=…)`,
`CascorControlStream(origin=…)`, `JuniperCascorClient.save_snapshot(…)`) raise `TypeError` /
`AttributeError` on the first real call. CI stays green because it installs from the correct
`requirements.lock` **and the suite mocks both clients**, so the real constructor signatures are
never exercised (`$J/juniper-canopy/src/tests/conftest.py:370-511` data-client autouse fixture;
`:145-188` cascor-client `sys.modules` stub). The canopy debug doc records this as architectural
weakness **A-2** ("green tests / dead app").

The audit attacks four gaps at once:

- **(a)** no per-source-file coverage gate exists in the ecosystem (only aggregate gates), so a file
  can sit at 0% inside a 90%-aggregate pass — measured live this session: `__main__.py` is at **0%**
  in both `juniper-ci-tools` (93% aggregate) and `juniper-doc-tools` (87% aggregate).
- **(b)** only **one** click-through surface exists (canopy Playwright), and **two of the four flows
  that actually crash are not covered** by it (first-data-fetch, model-selection/Recurrence-LMU).
- **(c)** the mocked-seam pattern that hid the canopy breakage is unguarded.
- **(d)** nothing checks that an installed env satisfies a repo's dependency floors —
  `$J/juniper-ml/util/editable_install_drift_check.py` inspects only **editable** installs
  (`direct_url.json`), and canopy's drifted wheels were **plain** installs.

---

## 2. Scope — the 19 coverage units (corrected inventory)

The 9 repos resolve to **19 coverage units**: 8 top-level + 11 packaged sub-modules.
`juniper-recurrence`'s repo root is a *container* realized by 3 sub-packages (not itself a unit);
`bench/` is a repo-root API-e2e lane (not a gated unit); `juniper-deploy` has no importable source.

| # | Unit | Path (under `$J`) | Kind |
|---|------|-------------------|------|
| 1 | `juniper-ml` (meta) | `juniper-ml` | top-level (no importable pkg) |
| 2 | `juniper-canopy` | `juniper-canopy` | top-level webapp (**only click-through surface**) |
| 3 | `juniper-cascor` | `juniper-cascor` | top-level service |
| 4 | `juniper-cascor-client` | `juniper-cascor-client` | top-level client |
| 5 | `juniper-cascor-worker` | `juniper-cascor-worker` | top-level worker (torch) |
| 6 | `juniper-data` | `juniper-data` | top-level service (**has per-module gate**) |
| 7 | `juniper-data-client` | `juniper-data-client` | top-level client |
| 8 | `juniper-deploy` | `juniper-deploy` | top-level (no importable source) |
| 9 | `juniper-observability` | `juniper-ml/juniper-observability` | ml sub-module |
| 10 | `juniper-service-core` | `juniper-ml/juniper-service-core` | ml sub-module |
| 11 | `juniper-model-core` | `juniper-ml/juniper-model-core` | ml sub-module |
| 12 | `juniper-ci-tools` | `juniper-ml/juniper-ci-tools` | ml sub-module |
| 13 | `juniper-config-tools` | `juniper-ml/juniper-config-tools` | ml sub-module |
| 14 | `juniper-doc-tools` | `juniper-ml/juniper-doc-tools` | ml sub-module |
| 15 | `juniper-cascor-model` | `juniper-cascor/juniper-cascor-model` | cascor sub-module (**no gate — outlier**) |
| 16 | `juniper-cascor-protocol` | `juniper-cascor/juniper-cascor-protocol` | cascor sub-module |
| 17 | `juniper-recurrence` (app) | `juniper-recurrence/juniper-recurrence` | recurrence sub-pkg (headless FastAPI) |
| 18 | `juniper-recurrence-model` | `juniper-recurrence/juniper-recurrence-model` | recurrence sub-pkg (torch) |
| 19 | `juniper-recurrence-client` | `juniper-recurrence/juniper-recurrence-client` | recurrence sub-pkg |

The **11 packaged sub-modules** (subject to the ≥95% average bar): units 9–19.

---

## 3. Grounding corrections (directive 1 — survey vs. reality)

The re-probe **confirmed most survey rows** but found four corrections that change the audit design.
These are load-bearing — the plan is built on the corrected facts.

| # | Survey claim | Reality (grounded) | Impact |
|---|--------------|--------------------|--------|
| **K-1** | "**No per-file/-module gate anywhere**" | **Partly false → corrected after skeptical pass.** `juniper-data` already **measures** per-module coverage and parses `coverage.json` (`scripts/check_module_coverage.py:105-108` reads `files[…]["summary"]["percent_covered"]`, strips `/tests/` leaks `:96-101`), **but the per-module check is advisory/warn-only** — `exit_code=1` is set **only** on aggregate failure (`:115-117`); per-module shortfalls just print `WARN` (`:119-122`). So nothing per-file/-module actually *blocks* anywhere; enforcement is aggregate-only. | The shared tool (§7) **reuses the proven json-parsing** (same key path) and **adds the exit-code enforcement the script lacks** — a scoped generalization, not greenfield and not a no-op. |
| **K-2** | "Thresholds **frequently CI-YAML-only**… cascor/client/worker/data family via `--fail-under=$ENV`" | **Wrong cluster.** The cascor/client/worker/data family ALL also set `fail_under` in `pyproject.toml` (`juniper-cascor` :253, `cascor-client` :137, `cascor-worker` :164, `juniper-data` :231, `data-client` :127). The **actual CI-only set** is `{observability, model-core, ci-tools, config-tools, doc-tools, cascor-protocol}`; `cascor-model` has **none**. | "Move thresholds into pyproject so local runs are gated" applies to **6 named units**, not the family the survey implicated. |
| **K-3** | Partial-subset aggregates: cascor + canopy | **Three units.** `juniper-data` is also partial: `ci.yml` runs `pytest -m "unit and not slow" juniper_data/tests/unit --cov=juniper_data` (integration/slow excluded from the gate-feeding subset) — same shape as cascor. | The "headline % overstates exercised source" risk spans **3** big units. |
| **K-4** | canopy ~75 src / 278 test; recurrence-model threshold "90 ×2" | canopy is **65 src / 259 test**; both recurrence-model CI lanes (base + torch) gate at 90 — base **omits** `_readout_mlp.py`, torch lane covers **only** it via `.coveragerc.torch`. | Count corrected; the recurrence-model two-lane split is the canonical numpy-2.x pattern to reuse (§7.3). |

Additional confirmations worth pinning:

- `juniper-ml` (meta) has **no importable package** (`pyproject.toml` `packages = []`); "source" is
  `util/` (~30 .py) + `scripts/` + `tests/`. The per-file mandate needs an explicit policy here (§7.4).
- canopy gate is **dual** (ci.yml:58/187 + pyproject.toml:406); UI excluded by `--ignore=src/tests/ui`
  (pyproject.toml:337); the **blocking** `ui-tests` Playwright job is `ci.yml:293-294` / runs at
  `:341-347` / enforced at `:859-862` via the required-checks aggregator.
- `juniper-data` already emits `--cov-report=json` (the exact mechanism directive 2 needs).
- `juniper-recurrence-model/.coveragerc.torch` exists (`[report] include = */_readout_mlp.py`,
  `fail_under = 90`) and documents the numpy-2.x package-form-`--cov` workaround.

---

## 4. Per-unit coverage posture (directive 1)

Real verify command + gate + gate location + partial-subset + current aggregate. "MEASURE@S0" =
not cheaply measurable in a doc-only session (needs a specific conda env / torch / browser); the
exact measuring command is given so Step 0 (§11 Phase B2) fills it.

| Unit | Real verify command | Gate | Gate location | Partial subset? | Current aggregate |
|------|---------------------|------|---------------|-----------------|-------------------|
| `juniper-ml` (meta) | `python3 -m unittest -v tests/test_*.py` | none (intentional) | — (`pyproject` declines, `:134-136`) | n/a | n/a (no pkg) |
| `juniper-observability` | `pytest --cov=juniper_observability --cov-report=term-missing` | 90 | **CI-only** `ci-observability.yml:63` | no | **99%** (570 stmt, 4 miss) ✓measured |
| `juniper-service-core` | `pytest --cov=juniper_service_core …` | 80 | dual `ci-service-core.yml:65` + `pyproject.toml:87` | no | **82.55%** (3074 stmt, 447 miss) ✓measured |
| `juniper-model-core` | `pytest --cov=juniper_model_core …` | 95 | **CI-only** `ci-model-core.yml:71` | no | **98%** (569 stmt, 14 miss) ✓measured |
| `juniper-ci-tools` | `pytest --cov=juniper_ci_tools …` | 85 | **CI-only** `ci-ci-tools.yml:70` | no | **93%** (568 stmt, 41 miss) ✓measured |
| `juniper-config-tools` | `pytest --cov=juniper_config_tools …` | 85 | **CI-only** `ci-config-tools.yml:71` | no | **96%** (28 stmt, 1 miss) ✓measured |
| `juniper-doc-tools` | `pytest --cov=juniper_doc_tools …` | 85 | **CI-only** `ci-doc-tools.yml:69` | no | **87%** (300 stmt, 38 miss) ✓measured |
| `juniper-canopy` | `make coverage` (+ `make test-ui`) | 80 | dual `ci.yml:58/187` + `pyproject.toml:406` | **yes** (unit/+regression/ feed `--cov=src`) | MEASURE@S0 (`JuniperCanopy1`; broken app) |
| `juniper-cascor` | `bash src/tests/scripts/run_tests.bash` → `coverage report --fail-under=80` | 80 | dual `ci.yml:58/325` + `pyproject.toml:253` | **yes** (`-m "unit and not slow" src/tests/unit`) | MEASURE@S0 (`JuniperCascor1`+torch) |
| `juniper-cascor-model` | `pytest -v` | **none** (outlier) | — (`ci-cascor-model.yml:67`) | n/a | MEASURE@S0 (torch) |
| `juniper-cascor-protocol` | `pytest --cov=juniper_cascor_protocol …` | 95 | **CI-only** `ci-protocol.yml:63` | no | MEASURE@S0 (pydantic+numpy) |
| `juniper-cascor-client` | `pytest --cov=juniper_cascor_client …` → `coverage report --fail-under=$ENV` | 80 | dual `ci.yml:258` + `pyproject.toml:137` | no | MEASURE@S0 |
| `juniper-cascor-worker` | `pytest --cov=juniper_cascor_worker …` | 80 | dual `ci.yml:300` + `pyproject.toml:164` | no | MEASURE@S0 (torch) |
| `juniper-data` | `pytest -m "unit and not slow" juniper_data/tests/unit --cov=juniper_data --cov-report=json` → `check_module_coverage.py` | 80 agg **+ 85 per-module** | dual `ci.yml:300/308` + `pyproject.toml:231` | **yes** | MEASURE@S0 |
| `juniper-data-client` | `pytest --cov=juniper_data_client …` | 80 | dual `ci.yml:251` + `pyproject.toml:127` | no | MEASURE@S0 |
| `juniper-deploy` | `pytest tests/ -v --tb=short` | none (no source) | — | n/a | n/a (compose/secret tests) |
| `juniper-recurrence` (app) | `pytest --cov=juniper_recurrence …` | 90 | dual `ci-recurrence-app.yml:89` + `pyproject.toml:149` | no | MEASURE@S0 (⚠ see DISC-1) |
| `juniper-recurrence-model` | base + torch lane (`.coveragerc.torch`) | 90 ×2 | dual `ci-recurrence-model.yml:88/155` + `pyproject.toml:100` | base omits `_readout_mlp.py` | MEASURE@S0 (torch) |
| `juniper-recurrence-client` | `pytest --cov=juniper_recurrence_client …` | 90 | dual `ci-recurrence-client.yml:89` + `pyproject.toml:89` | no | MEASURE@S0 (⚠ see DISC-1) |

Registered markers (for the partial-subset analysis): cascor 18 (`pyproject:211-230`), canopy 13
(`pyproject:339-354` + `conftest:194-201`, incl. `ui`/`e2e`/`requires_cascor`/`requires_server`/`requires_display`),
juniper-data 8, cascor-client/worker & data-client `{unit,integration[,performance]}`, deploy
`{health,data,full_stack}`; the 6 ml sub-modules + 3 recurrence sub-pkgs + 2 cascor sub-modules
register **no custom markers** (`--strict-markers` active).

**Click-through surfaces:** only `juniper-canopy` (Playwright `src/tests/ui/`). Every other unit is a
library/service/orchestration with **no browser UI**; the recurrence app is headless FastAPI tested
via Starlette `TestClient` (`tests/test_app_smoke.py:13`, `-p no:playwright` in addopts). Confirmed
this session.

---

## 5. Per-file coverage gap table (directive 2)

Seeded with the 6 live-measured units; the rest are filled by Step 0 (§11 B2) with the exact command
above. "count <90%" = source files below the per-file floor. Comprehensive counts for the 13
MEASURE@S0 units are deferred to Step 0 because measuring them needs 3 conda envs + torch + a browser
(an execution/CI activity, out of scope for a document-only session) — **not** because they are
unknown in principle. This is the honest posture; no percentages are invented.

| Unit | Current aggregate | Known files <90% (measured) | Sub-module avg vs 95% | Named remediation |
|------|-------------------|------------------------------|------------------------|-------------------|
| `juniper-observability` | 99% | none confirmed (`prometheus_helpers.py`,`testing.py` ~2 miss each — verify per-file @S0) | likely ≥95 (verify) | per-file pass; promote gate to per-file 90 |
| `juniper-service-core` | 82.55% | **multiple** — `websocket/control_stream.py`, `websocket/control_security.py` (~46-66%), `security.py` (81%) | **below 95** — largest lift | targeted tests for websocket/control + security; raise gate |
| `juniper-model-core` | 98% | none confirmed (`conformance/reference.py`,`suite.py` ~4-6 miss — verify @S0) | likely ≥95 (verify) | per-file pass; promote gate |
| `juniper-ci-tools` | 93% | **`__main__.py` 0%**; some `lint/*` 83-94% | ~ borderline 95 | test `__main__`/CLI or exclude per policy; lift `lint/*` |
| `juniper-config-tools` | 96% | `__main__.py` (1 miss of few stmts → likely <90) | ~95 | test/exclude `__main__`; verify |
| `juniper-doc-tools` | 87% | **`__main__.py` 0%, `check_doc_links.py` 88%, `cli.py` 87%** (≥3 files <90) | **below 95** | lift the 3 named files; test/exclude `__main__` |
| `juniper-canopy` | MEASURE@S0 | TBD@S0 (`make coverage`) | n/a (top-level) | canopy-first roadmap §11A |
| `juniper-cascor` | MEASURE@S0 | TBD@S0 (bash harness) | n/a (top-level) | per-file rollout §11C |
| `juniper-cascor-model` | MEASURE@S0 | TBD@S0 | **no gate today** → must reach 95 | §11B1 add gate first |
| `juniper-cascor-protocol` | MEASURE@S0 | TBD@S0 | gate 95 today | verify per-file; move gate to pyproject |
| `juniper-cascor-client` | MEASURE@S0 | TBD@S0 | gate 80 → lift to 95 | §11C |
| `juniper-cascor-worker` | MEASURE@S0 (torch) | TBD@S0 | gate 80 → lift to 95 | §11C |
| `juniper-data` | MEASURE@S0 | TBD@S0 (already has per-module json) | n/a (top-level) | tighten per-module→per-file via shared tool |
| `juniper-data-client` | MEASURE@S0 | TBD@S0 | gate 80 → lift to 95 | §11C |
| `juniper-recurrence` (app) | MEASURE@S0 | TBD@S0 (⚠DISC-1) | gate 90 → lift to 95 | resolve DISC-1, then §11C |
| `juniper-recurrence-model` | MEASURE@S0 (torch) | TBD@S0 (2 lanes) | gate 90 → lift to 95 | §11C; reuse `.coveragerc.torch` |
| `juniper-recurrence-client` | MEASURE@S0 | TBD@S0 (⚠DISC-1) | gate 90 → lift to 95 | resolve DISC-1, then §11C |
| `juniper-ml` (meta) | n/a | n/a (no pkg) | n/a | scope per-file to `util/` only, or exempt (§7.4) |
| `juniper-deploy` | n/a | n/a (no source) | n/a | exempt; keep compose/secret tests |

**Headline insight already proven without Step 0:** `doc-tools` passes its 85 aggregate gate at 87%
while harboring ≥3 files under 90%, and `ci-tools` passes at 93% with a 0%-covered `__main__.py`.
Aggregate gates demonstrably permit per-file holes — the per-file gate is the right instrument.

---

## 6. The per-file coverage **contract** (owner-pinned definitions)

1. **Per-file floor:** every source file in a unit's import package has **line coverage ≥90%**.
2. **Sub-module average:** for each of the 11 packaged sub-modules (units 9–19), the **mean of
   per-file line-coverage across its source files is ≥95%**.
3. **Source file** = a `.py` file inside the unit's importable package, minus the **excluded set**
   (§7.4). Exclusions are an explicit, reviewed allowlist — never silent.
4. **Branch vs line:** the gate is on **line** coverage (matches existing gates + the
   `.coveragerc.torch` precedent). Branch coverage stays informational unless an owner opts a unit in.
5. **OPEN — sub-module "average" interpretation (owner to ratify; skeptical-pass finding).** "Average
   ≥95%" admits two readings that **diverge for small files**: (i) coverage's standard
   **statement-weighted aggregate** (`totals.percent_covered`), or (ii) the **arithmetic mean of
   per-file %**. They differ sharply — files `{200 stmt @100%, 3 stmt @0%}` give **(i) 98.5%** vs
   **(ii) 50%**. **Recommendation:** gate the **statement-weighted aggregate ≥95%** (the conventional
   meaning of "the sub-module's coverage"), because the independent **per-file ≥90% floor already
   prevents any single file from hiding** — mean-of-files would double-penalize and reward
   "split a file to game the mean." The tool **reports both** so the choice is reversible. This flags
   the ambiguity rather than silently redefining a pinned value.

---

## 7. Measurement & enforcement design (directive 2)

### 7.1 Measure with coverage JSON (precedent: juniper-data)

Run each unit's **own real command** (§4) with `--cov=<import_pkg> --cov-report=json:<out>`, then
parse `coverage.json` → `files[<path>].summary.percent_covered` per file. `juniper-data` already does
exactly this (`--cov-report=json` + `scripts/check_module_coverage.py`), so the mechanism is proven
in-ecosystem, not speculative. **Proven key path:** `check_module_coverage.py:105-108` already reads
`data["files"][f]["summary"]["percent_covered"]` and strips `/tests/` leaks (`:96-101`); the new tool
reuses this verbatim and **adds the per-file exit-code gate the existing script omits** (it blocks only
on the aggregate today — §3 K-1).

### 7.2 A shared enforcement tool in `juniper-ci-tools`

**Decision:** host the checker as a shared console script in **`juniper-ci-tools`** (it already hosts
cross-repo CI tooling like `juniper-generate-dep-docs`), generalizing `juniper-data`'s
`check_module_coverage.py` from per-module to per-file:

- Console script `juniper-check-file-coverage` (+ `python -m juniper_ci_tools.file_coverage`).
- Inputs: `--coverage-json <path> --min-file 90 --min-submodule-avg 95 --omit <globs> --warn-only`.
- Outputs: per-file table, the **count and list** of files <90% (never a silent top-N truncation —
  per the suite's "no silent caps" ethos), the sub-module average vs 95, exit 1 on violation
  (exit 0 under `--warn-only`).
- **Self-filtering (robustness, skeptical-pass fix):** the tool applies its `--omit`/exclusion +
  waiver lists **itself, on the parsed `coverage.json`** — it does **not** rely on coverage's
  `[report] include`/`omit` to pre-scope the json (that scoping is version-dependent and may not
  propagate to the json export). The tool is the single source of truth for what counts.
- **Reports both averages** (statement-weighted aggregate and mean-of-files, §6.5); gates on the
  owner-ratified one (default: aggregate ≥95).
- **Waivers** are a structured file (`coverage-waivers.yaml`: `path`, `reason`, `issue`, `expires`);
  the tool lists active waivers and **warns on expired ones — an expired waiver does NOT unblock the
  gate** (it surfaces as a violation until removed). Waivers are for "untested but kept", distinct
  from `# pragma: no cover` (unreachable lines).
- **Dogfood test in `juniper-ml/tests/`** (e.g. `tests/test_file_coverage_gate.py`), matching the
  established dogfood pattern for ci-tools console scripts. This is the **sole** gate for the tool's
  contract because `juniper-ci-tools` is a sub-module.
- Carries the numpy-2.x workaround (§7.3) and the excluded-files policy (§7.4) as first-class concerns.

Consumer wiring per unit: add `--cov-report=json` to the existing command + a
`juniper-check-file-coverage` step. Because the tool is one PyPI dependency, the 19 units adopt it
without copy-paste drift.

### 7.3 numpy-2.x dotted-`--cov` gotcha

Dotted `--cov=pkg.submodule` trips numpy-2.x's "cannot load module more than once" guard under
coverage. **Always use package-form `--cov=<top_pkg>`.** For per-file scoping, **the shared tool
filters the parsed `coverage.json` itself** (§7.2) rather than depending on coverage's
`[report] include=` to scope the json export — a skeptical-pass finding flagged that report-section
filtering may not propagate to the json, so the tool must not rely on it. The canonical
**measurement-time** precedent for isolating a torch-gated *file* remains
`$J/juniper-recurrence/juniper-recurrence-model/.coveragerc.torch` (the base lane omits
`_readout_mlp.py`; the torch CI lane covers only it; `ci-recurrence-model.yml:150-155`): replicate that
two-lane split when a file needs torch, and let the tool **union** the per-file results from each
lane's json.

### 7.4 Excluded-files & waiver policy

- **Default exclusions (allowlisted, per repo `[tool.coverage.run] omit` or tool `--omit`):**
  `__init__.py` that only re-exports; `__main__.py` / thin CLI entry points (the measured 0%-covered
  `__main__.py` files justify this — but prefer a smoke test over an exclusion where feasible);
  generated code; `bench/`; `scripts/`, `util/ad-hoc/`; `TYPE_CHECKING`-only blocks via
  `# pragma: no cover` + `[report] exclude_lines`.
- **Waivers (file genuinely below 90% but kept):** an explicit allowlist entry with a linked issue and
  an expiry date — **not** a blanket `# pragma: no cover` (which is for unreachable lines, not
  "untested"). Waivers are reviewed each rollout PR; the tool prints the active waiver list.
- **`juniper-ml` meta:** has no import package, so the per-file mandate is scoped to **`util/`** (the
  testable surface) or the unit is exempted from the % gate (it intentionally has none); owner picks
  in §11. **`juniper-deploy`** (no source) is exempt — its compose/secret tests stay as-is.

### 7.5 Move CI-only thresholds into `pyproject.toml`

For the 6 CI-only units (K-2: observability, model-core, ci-tools, config-tools, doc-tools,
cascor-protocol) the threshold moves into `pyproject.toml`/`.coveragerc`. **Caveat (skeptical pass):**
`[tool.coverage.report] fail_under` alone does **not** gate every local invocation — a bare
`pytest --cov=pkg` without `--cov-fail-under` may not fail. So each unit gets a **documented, gated
local target** (a `make coverage` / script that runs the unit's tests **then**
`juniper-check-file-coverage` + `coverage report --fail-under`); that target — not a bare `pytest` —
is the canonical local gate. The dual-gated units already gate the aggregate; all units gain the
per-file step via that target.

---

## 8. Click-through coverage design (directive 3)

**Surfaces:** canopy is the **only** browser surface (confirmed §4). The recurrence app is headless
FastAPI → its "e2e" stays **API-level** (`TestClient`); no browser harness is created for it. If any
future unit grows a web UI, it replicates canopy's harness (below) under its own `src/tests/ui/`.

**Model to replicate** — canopy's real harness (`$J/juniper-canopy/src/tests/ui/conftest.py`):
free-port pick (`:27-30`) → boot `src/main.py` in demo mode (`:46-52`) → poll `/v1/health/ready`,
45 s deadline (`:56-69`) → `page.goto(.../dashboard/)` (`:97`) → fill inputs (e.g.
`#nn-learning-rate-input`) and wait on real callback chains. Runs only in the **blocking `ui-tests`
job** (`ci.yml:341-347`), excluded from the default run by `--ignore=src/tests/ui` (pyproject:337) to
dodge the documented pytest-playwright event-loop leak. Local: `make test-ui` / `make coverage`.

**Required new click-through coverage — the flows that currently crash:**

| Flow | Crash anchor | Existing UI test | Action |
|------|--------------|------------------|--------|
| first data fetch (spiral/demo) | `demo_mode.py:918-921`, `:1795-1798` | **none** | **ADD** `test_first_data_fetch.py` — load dashboard, assert dataset renders (not an error toast) |
| dataset apply | — | `test_dataset_apply.py:23-50` ✓ | keep; assert it exercises the real fetch, not only the mock |
| train-after-reset | — | `test_train_after_reset.py:33-63` ✓ | keep |
| model selection incl. **Recurrence-LMU** | `backend/__init__.py:33` → `:132` adapter | **none** | **ADD** `test_model_selection_recurrence.py` — select Recurrence (LMU), assert defined behavior (guarded UX, not silent failure) — ties to D-3 |

New UI tests live in `$J/juniper-canopy/src/tests/ui/`, carry the `ui` marker, and run in the existing
`ui-tests` job (no new CI lane needed). Acceptance: each of the four flows maps to a named UI test
(two exist, two added).

---

## 9. Re-entrant debug-findings ingestion procedure (directive 4 — owner-pinned)

A **standing, re-runnable** procedure (a runbook; optionally backed by a helper under
`util/ad-hoc/`). It must converge as the debug doc grows new IDs, with an **append-only** traceability
table.

### 9.1 The procedure (run on every audit iteration)

1. **Locate** the current canonical canopy debug-findings doc:
   ```bash
   find "$J/juniper-ml/notes" "$J/juniper-canopy/notes" -type f -iname 'JUNIPER_CANOPY*' \
     \( -iname '*DEBUG*' -o -iname '*FINDINGS*' -o -iname '*ANALYSIS*' -o -iname '*RUNTIME*' \) \
     -printf '%T+  %p\n' | sort -r
   ```
   Then **validate content before accepting** (skeptical-pass hardening): from the most-recent down,
   take the **first** candidate that actually contains the markers — a `§5`/`## 5` crash-site section
   **and** at least one `(X-N)` issue ID. Most-recently-modified alone is **not** trusted (a `touch`ed
   or incomplete sibling could win the sort). **Proven this run:** the validated pick is
   `$J/juniper-ml/notes/JUNIPER_2026-06-26_JUNIPER-CANOPY_DEBUG-PROMPT-ANALYSIS.md` (only matching doc today;
   the `flickering-zooming-finch` seed is gone). *Robust long-term option:* keep a one-line pointer
   file `$J/juniper-ml/notes/CURRENT_CANOPY_DEBUG_DOC` so discovery is explicit, not glob-inferred.
2. **Parse two distinct, stable key spaces** (skeptical-pass fix — the §5 sites have no source IDs):
   - **§6.2 issue IDs** — `(X-N)` with prefixes `I-`/`C-`/`D-`/`A-`/`S-`; extract verbatim (these are
     the source-of-truth IDs).
   - **§5 crash sites** — keyed by their **stable `file:line` anchor** (e.g. `demo_mode.py:918-921`,
     debug-doc `:76-89`), **not** an invented ordinal (ordinals re-coin/duplicate on re-run). The §5
     package table (env-floor-drift) is keyed by the class name `EFD`.
   - Column matching is **prefix/fuzzy** (the real header reads `Floor (pyproject.toml)`,
     `API the code calls`, …), not exact-string.
   - The doc is designed to **grow** both lists.
3. **Map** each **open** item → a **named regression test with a checkable assertion** (§9.2),
   recorded in the §9.3 table.
4. **Diff & status** against the append-only table using the stable keys. Statuses:
   `UNMAPPED` (new, no test) → `MAPPED` (test authored) → `SHIPPED` (merged) → `CLOSED` (resolved
   upstream) | `BLOCKED-ON-OWNER` (test undecidable until a decision, e.g. D-2). **Closed status is
   read from the debug doc's own annotations** (its §6.2 "Status update" line self-reports closures,
   e.g. I-1/C-1 via PR #566) — **no GitHub API needed**. A key present in the table but **absent** from
   the current doc is flagged `STALE?` for human reconcile (never silently kept or dropped).
5. **Convergence & fail-loud.** A run with no new keys is a **no-op** (append-only; every row already
   in {MAPPED, SHIPPED, CLOSED, BLOCKED-ON-OWNER}). If the doc lacks the §5/§6.2 markers (format
   drift), the procedure **stops and reports** — it never skips rows (the suite's hard-stop ethos).
   Honest scope: this is a **human-driven runbook with a mechanizable locate→extract→diff core**;
   authoring a *new* regression test for a *new* issue is inherently judgment (you cannot auto-write a
   meaningful assertion), and the runbook says so.

**Idempotency:** a run with no new keys is a no-op; the append-only table preserves history (including
`CLOSED` rows); the plan therefore tolerates the debug doc growing **without rework**.

### 9.2 Mapping rules (issue class → test shape)

- **env-floor-drift class** (the §5 package rows) → one **dependency-satisfaction** test asserting the
  installed `juniper-*` versions satisfy the repo's `pyproject.toml` floors / `requirements.lock`
  (§10). One test covers the whole class; new drifted packages need no new test.
- **constructor `TypeError`/`AttributeError`** (the §5 crash-site anchors) → a test that constructs
  the **real** client and asserts either the success path **or an explicit guard** — never a silent mock.
- **mocked-seam gap** → an **un-mocked** integration test exercising the real constructor at the seam.

### 9.3 Seeded issue→test traceability table (append-only)

Seeded with **every** issue currently in the debug doc §5 + §6.2. **Keys are stable** (skeptical-pass
fix): §6.2 rows use the source `I-/C-/D-/A-/S-` ID; §5 crash-site rows use the **`file:line` anchor**
(not an ordinal); class rows use a class name (`EFD`, `SEAM`). `Home` = repo that owns the test.
Status ∈ {UNMAPPED, MAPPED, SHIPPED, CLOSED, BLOCKED-ON-OWNER}.

| Key (stable) | Class | Source | Regression test (named) | Checkable assertion | Home | Status |
|--------------|-------|--------|--------------------------|---------------------|------|--------|
| `EFD` | env-floor-drift | §5 pkg table: data-client 0.4.0<0.4.1; cascor-client 0.3.0<0.5.0 | `test_env_satisfies_floors` | every installed `juniper-*` ≥ its `pyproject` floor and within `requirements.lock` | canopy (+ shared tool) | UNMAPPED |
| `demo_mode.py:918-921` | TypeError (§5) | spiral fetch | `test_demo_spiral_fetch_real_client` | `JuniperDataClient(on_request=…)` + first spiral fetch succeeds or raises a *handled* error (no uncaught `TypeError`; cf. `:935`/`:944`) | canopy | UNMAPPED |
| `demo_mode.py:1795-1798` | TypeError (§5) | generator fetch | `test_demo_generator_fetch_real_client` | non-spiral generator fetch constructs real client without uncaught `TypeError` | canopy | UNMAPPED |
| `cascor_service_adapter.py:44` | import/seam (§5) | adapter import | `test_cascor_adapter_imports_real_client` | importing the adapter with the real (un-stubbed) `juniper_cascor_client` resolves all four names | canopy | UNMAPPED |
| `cascor_service_adapter.py:131-134` | TypeError (§5) | control stream | `test_cascor_control_stream_origin_kw` | `CascorControlStream(origin=…)` accepts the kw against the floor-pinned client | canopy | UNMAPPED |
| `cascor_service_adapter.py:1537/:1545` | AttributeError (§5) | save_snapshot | `test_cascor_save_snapshot_present` | `JuniperCascorClient.save_snapshot` exists + callable against floor-pinned client | canopy | UNMAPPED |
| `backend/__init__.py:33` | construction (§5) | create_backend | `test_create_backend_all_modes` | `create_backend()` builds Demo / Cascor / Recurrence backends without raising | canopy | UNMAPPED |
| `SEAM` (= `A-2` test) | mocked-seam | `conftest.py:370-511`, `:145-188` | `test_clients_unmocked_smoke` | an integration test with **both** client mocks disabled constructs real clients (or skips explicitly if service absent) | canopy | UNMAPPED |
| `I-1` | incomplete-dev | §6.2 | (rename-drift lint) | *reference only* — closed in **PR #566**; guard `tests/test_agent_suite_path_drift.py` exists | juniper-ml | CLOSED |
| `I-2` | incomplete-dev | §6.2 | `test_env_satisfies_floors` (= `EFD`) + documented reinstall step | env reinstalled from lock; floors satisfied | canopy + ml | UNMAPPED |
| `C-1` | configuration | §6.2 | *reference only* — `ecosystem.yaml` env staleness, closed in **PR #566** | — | juniper-ml | CLOSED |
| `C-2` | configuration | §6.2 | `test_no_stale_commented_pins` | `conf/requirements.txt`,`requirements.txt`,`requirements_ci.txt` carry no contradicting commented `# juniper-*-client==` pins | canopy | UNMAPPED |
| `D-1` | design-gap | §6.2 | `test_test_status_cache_freshness` | `prompt_discovery/test_status.py` stamps cache mtime + flags/`unavailable` past a TTL | juniper-ml | UNMAPPED |
| `D-2` | design-gap (decision) | §6.2 | `test_demo_mode_degradation_defined` | demo-mode constructor failure yields the **owner-decided** UX (guard or surfaced error), asserted once decided | canopy | **BLOCKED-ON-OWNER** |
| `D-3` | design-gap | §6.2 | `test_recurrence_start_gated_on_service` | selecting Recurrence-LMU with no `recurrence_service_url` (`settings.py:237`) is gated or shows defined failure UX | canopy | UNMAPPED |
| `A-1` | architectural | §6.2 | `test_prompt_discovery_target_repo_mode` | discovery/validator accept a cross-repo `--target-repo` | juniper-ml | UNMAPPED |
| `A-2` | architectural | §6.2 | live-runtime/service-smoke lane (§10.3) = `SEAM`/smoke | a booted-service smoke lane exists for canopy | juniper-ml + canopy | UNMAPPED |
| `S-1` | suspected | §6.2 | ecosystem env-drift audit (`EFD` applied to `JuniperCascor1`/`JuniperData`) | sibling envs satisfy their floors | juniper-ml (audit) | UNMAPPED |

*Acceptance (directive 4):* every current §5 anchor + §6.2 ID has a row mapping to a named, checkable
test (or a documented terminal status); keys are stable, the table is append-only, and the
locate→extract→diff core is re-runnable.

---

## 10. Systemic "green tests / dead app" remediation (directive 5)

Three durable guards beyond the per-issue regressions:

### 10.1 Dependency-satisfaction check (the root cause; the EFD test's engine)

A shared checker — `juniper-env-drift-check` in **`juniper-ci-tools`** — that asserts the **installed**
`juniper-*` distributions in the active interpreter satisfy the repo's `pyproject.toml` floors /
`requirements.lock`. This is a **real gap**: `util/editable_install_drift_check.py` reads only
`direct_url.json` (**editable** installs), and canopy's drift was **plain wheels**. Extends the
discovery `dependency_facts` probe (which reads pins but never compares to the live interpreter).
**Owner:** juniper-ml hosts the tool; each service repo (canopy first) wires it into CI + a local
preflight. Dogfood test in `juniper-ml/tests/`.

### 10.2 Un-mocked integration/smoke tests (exercise real construction)

Add per-service integration tests that construct the **real** clients (mocks disabled), asserting the
adopted signatures — the `SEAM`/CS tests of §9.3. **Owner:** each consuming service (canopy first).

### 10.3 Live-runtime / service-smoke lane (A-2)

A CI lane (or a `make smoke` target) that boots the service in its **correct conda env**, hits
`/v1/health/ready`, and drives one core flow (for canopy, reuse the `ui-tests` boot harness; for
headless services, an HTTP smoke). This is the only guard that can catch "green tests / dead app" by
construction. **Owner:** juniper-ml designs the shared pattern; canopy, cascor, data, recurrence-app
each own their lane.

---

## 11. Phased roadmap (directive 6)

Rules for **every** step: worktree under `$J/worktrees/` (naming per parent `CLAUDE.md`); **one PR per
work unit**; **no merge without PR**; run `gh pr list` first (duplicate-work guard — concurrent
sessions are common); deploy/PyPI approvals are Paul's.

### Phase A — canopy first (the broken app + the only click-through surface)

| Step | Work | Verify command | Acceptance |
|------|------|----------------|------------|
| A1 | EFD dependency-satisfaction guard + canopy `test_env_satisfies_floors` (MVP of §10.1) | `conda run -n JuniperCanopy1 juniper-env-drift-check --repo .` | exits non-zero on the current drift; green after lock reinstall |
| A2 | `test_clients_unmocked_smoke` — disable both mocks, construct real clients (SEAM) | `make test` (new integration test) | test exercises real constructors or skips explicitly if service absent |
| A3 | §5 crash-site anchors + D-2/D-3 regression tests | `make test` | each crash anchor has a passing named test (table §9.3) |
| A4 | New UI tests: `test_first_data_fetch`, `test_model_selection_recurrence` | `make test-ui` | the 2 uncovered crashing flows now covered (§8) |
| A5 | canopy live-runtime smoke lane (§10.3) | `make smoke` (new) | boots in `JuniperCanopy1`, hits `/v1/health/ready` + one flow |

### Phase B — no-gate outliers + the shared per-file tool

| Step | Work | Verify command | Acceptance |
|------|------|----------------|------------|
| B0 | **DISC-1 unblock** — pin/guard the recurrence `filterwarnings` Starlette class (app + client) so collection works in the live env | `cd $J/juniper-recurrence/juniper-recurrence && python -m pytest --co -q -p no:cacheprovider` | collection exits 0 in the target env; recurrence units become measurable for Phase C |
| B1 | `juniper-cascor-model`: add a coverage gate (→ per-file 90 + sub-module 95 bar) | `cd $J/juniper-cascor/juniper-cascor-model && pytest --cov=juniper_cascor_model --cov-report=term-missing` | `ci-cascor-model.yml` enforces a **blocking per-file 90 + sub-module-avg 95** gate (no longer `pytest -v` only) **and measured coverage meets both** |
| B2 | **Step 0 enabler:** ship `juniper-check-file-coverage` in `juniper-ci-tools` (generalize `juniper-data/scripts/check_module_coverage.py`) + dogfood test; then **run it across all 19 units** to fill §5 | `juniper-check-file-coverage --coverage-json cov.json --min-file 90 --min-submodule-avg 95` ; `python3 -m unittest tests/test_file_coverage_gate.py` | tool ships green + dogfooded; §5 gap table fully populated with measured per-file counts |

### Phase C — per-file gate rollout (one PR per unit, warn-only → blocking)

Order by measured/known gap (worst first): `service-core`, `doc-tools`, then `ci-tools`,
`config-tools`, then `cascor-protocol`/`observability`/`model-core` (verify per-file), then the
cross-repo units `data`, `data-client`, `cascor`, `cascor-client`, `cascor-worker`, `recurrence`
×3 (resolve DISC-1 first), `canopy`. Each PR: add `--cov-report=json` + the tool step in **warn-only**,
close the gap, then flip to **blocking** and move the threshold into `pyproject.toml`.

- **Verify (per unit):** the unit's real §4 command + `juniper-check-file-coverage … --min-file 90`.
- **Acceptance (per unit):** zero files <90% (or explicit waivers §7.4); sub-module average ≥95%;
  threshold in `pyproject.toml`; gate blocking in CI.

### Phase D — ecosystem-wide durable guards

| Step | Work | Owner | Acceptance |
|------|------|-------|------------|
| D-tool | wire `juniper-env-drift-check` into every service repo CI + preflight | juniper-ml + each repo | each service CI fails on installed-vs-floor drift |
| D-A1 | cross-repo `--target-repo` mode for `prompt_discovery` + `prompt-validator` | juniper-ml | suite grounds a sibling repo without manual overrides |
| D-D1 | `test_status` cache-freshness (stamp mtime + TTL) | juniper-ml | stale cache flagged `unavailable`, not `ok` |
| D-S1 | ecosystem env-drift audit (`JuniperCascor1`/`JuniperData`) | juniper-ml | report of sibling-env floor satisfaction |

---

## 12. Risks & verification strategy (directive 7)

| Risk | Mitigation |
|------|------------|
| **Per-file 90% on large legacy repos** (cascor & juniper-data each ~100+ source files / tens of kLOC — exact counts vary by measure; pin at Step 0) infeasible in one PR | warn-only rollout + per-unit promotion + explicit time-boxed waivers (§7.4); canopy/sub-modules prove the pattern before the big repos |
| **Flag-day red CI** if the gate lands blocking everywhere at once | Phase C is one PR per unit, warn-only → blocking only after the gap closes |
| **Browser-test flakiness / event-loop leak** | reuse canopy's proven `--ignore=src/tests/ui` + dedicated `ui-tests` job; do not add UI tests to the default lane |
| **CI wall-clock budget** (torch installs, browser, 3 conda envs) | per-file step reuses each unit's existing run (no extra suite); torch lanes reuse the `.coveragerc.torch` split; smoke lanes are one-flow |
| **Partial-subset aggregates mask gaps** (cascor, canopy, **juniper-data** — K-3) | per-file gate is computed against the **whole** `--cov` tree; flag any file only reachable by an excluded subset as a coverage hole, not a waiver |
| **numpy-2.x dotted-`--cov` crash** | package-form `--cov` everywhere; `[report] include` for isolation (§7.3) |
| **Debug doc format drift** breaks ingestion | the procedure fails loudly on missing markers (§9.1.5); contract is on stable §5 columns + ID prefixes |
| **DISC-1** blocks recurrence measurement | resolve before recurrence rollout (§14) |

**Verification strategy:** every roadmap step names a real command + a checkable acceptance criterion
(§11). The per-file tool is **dogfooded** in `juniper-ml/tests/`. The ingestion procedure is
re-runnable and self-checked by the append-only table. No step is "done" until its acceptance command
exits 0 in the unit's real environment.

---

## 13. Skeptical second pass (finalize/validation gate) — RATIFIED

Two independent adversarial reviewers challenged the highest-risk designs; the author then **verified
the load-bearing claims first-party** and revised the plan. Outcome: **ratified** with the changes
below folded in. (Over-reaching challenges were tempered with judgment, noted as such.)

**(i) Per-file measurement & enforcement (§6–§7):**

| Challenge | Verdict | Resolution |
|-----------|---------|------------|
| K-1 overstated — `juniper-data`'s per-module check is **advisory (warn-only)**, enforces aggregate-only | **Valid** — verified `check_module_coverage.py:111-122` (exit only on aggregate `:115-117`; per-module just `WARN` `:119-122`) | §3 K-1 + §7.1 corrected: json-parsing is the **proven** part; the tool **adds the exit-code gate the script lacks** |
| "average ≥95%" = mean-of-files vs statement-weighted **diverge** for small files | **Valid** (ambiguity in a pinned value) | §6.5 added — flagged for **owner ratification**; recommend statement-weighted ≥95 (per-file ≥90 already floors each file); tool reports both |
| `.coveragerc.torch` `[report] include` may **not scope `coverage.json`** | **Valid risk** | §7.2/§7.3: the tool **applies exclusions itself on the parsed json**, never relies on report-section scoping |
| `fail_under` in pyproject does **not** gate a bare local `pytest --cov` | **Valid** | §7.5: each unit gets a **documented gated local target**, not a bare pytest |
| DISC-1 blocks recurrence; make it a blocking step | **Valid — confirmed live** (pytest `--co` errors on the Starlette class) | promoted to **Phase B0** (§11); §14.2 upgraded to CONFIRMED |
| waiver expiry / cascor-model 95 / contested file counts | Minor, valid | §7.2 waiver-expiry rule; §11 B1 acceptance strengthened; §12 counts reworded |

**(ii) Re-entrant ingestion contract (§9):**

| Challenge | Verdict | Resolution |
|-----------|---------|------------|
| `CS1–CS6`/`SEAM`/`EFD` are **author-coined ordinals not in §6.2** → re-run can't re-extract → can't converge | **Valid (core defect)** | §9.1/§9.3 **re-keyed**: §5 rows keyed by stable **`file:line` anchor**, §6.2 by source ID, classes by name — all mechanically extractable, no re-coining |
| Locator "most-recent wins" can pick the **wrong/incomplete doc** | **Valid** | §9.1 step 1: **content-validate** (require §5/§6.2 markers) before accept; recommend a canonical pointer file |
| Closed-issue detection "needs GitHub API" | **Over-reach** — the debug doc **self-annotates** closures | §9.1 step 4 clarified: read closures from the doc's own "Status update" line; **no API** |
| No **terminal-status taxonomy** → D-2 stalls convergence | **Valid** | §9.1/§9.3: explicit {UNMAPPED, MAPPED, SHIPPED, CLOSED, BLOCKED-ON-OWNER}; D-2 = BLOCKED-ON-OWNER; convergence defined |
| Rewritten §5 bullet → **silent staleness** | **Valid** | anchor-keying makes a changed anchor a new key; missing keys flagged `STALE?` |
| "Requires human judgment → not re-entrant" | **Partly valid** | §9.5: stated honestly — mechanizable **locate→extract→diff** core; new-issue→test authoring is inherently judgment |
| Seed-table completeness vs real §6.2 | **Confirmed complete** (all 10 I/C/D/A/S IDs present) | no change |

**Residual (downstream, by design):** full mechanization of the parse/diff helper is left to
execution (the plan is a runbook + optional helper, not the helper itself); the
mean-of-files-vs-aggregate choice awaits the owner's one-word ratification (a sensible default is
applied meanwhile). Neither blocks ratification of the plan.

---

## 14. Meta-analysis (directive 7)

### 14.1 Additional custom-agent specializations that would accelerate this work

Building on the debug doc §6.1 (live-runtime/service-smoke diagnostician; environment/dependency-drift
checker; first-class cross-repo grounding — all directly relevant) and the prompt-analysis §6.1
(per-file coverage-gap mapper; mocked-seam gap auditor; click-through test author), the
**test-audit-specific** additions:

1. **Per-file-coverage-gap mapper** (highest test-audit value) — runs a unit's real command, parses
   `coverage.json`, emits per-file distribution + files <90% + sub-module avg vs 95. This is literally
   §7.2's tool, agent-fronted; it automates §4–§5 across 19 heterogeneous units.
2. **Click-through-test author** — given a Dash/web UI + a target flow, generates a Playwright test on
   canopy's harness (boot-demo → goto → fill → assert callback). Directly produces §8's A4 tests.
3. **Mocked-seam gap auditor** — hunts autouse/session fixtures (and `sys.modules` stubs like
   canopy's `:145-188`) that mock an integration boundary, flagging "suite mocks X at the seam → can't
   catch X-construction bugs." Turns the post-mortem into a standing check.
4. **Live-runtime/service-smoke diagnostician** (cross-cutting, highest overall) — boots a service in
   its conda env, drives it via the `chrome-devtools`/`playwright` MCP servers, reports live tracebacks
   with `file:line`. The only thing that catches "green tests / dead app" by construction.

### 14.2 Other Juniper issues discovered while planning (classified; owners)

Already recorded by the debug doc — **referenced, not re-discovered:** the
`prompts/templates/` → `prompts/agent_templates/` rename drift **(I-1, closed PR #566)** and the
`ecosystem.yaml` conda-env staleness **(C-1, closed PR #566)**.

**New this session:**

- **Design gap (systemic, partially mischaracterized before):** no per-**file** gate exists, but
  `juniper-data` *does* have a per-**module** gate (K-1) — the precedent to generalize, not a greenfield.
  *Owner:* all repos; juniper-ml leads the shared tool.
- **Configuration:** the **CI-only threshold set** (K-2) — observability, model-core, ci-tools,
  config-tools, doc-tools, cascor-protocol gate **only** in CI YAML, so bare local runs are ungated.
  *Owner:* juniper-ml (sub-modules) + juniper-cascor (protocol). Folded into §7.5.
- **Configuration — DISC-1 (CONFIRMED live this session).** The recurrence **app**
  `pyproject.toml:130-132` sets `filterwarnings = [ … "ignore::starlette.exceptions.StarletteDeprecationWarning" ]`,
  but that class is **absent** from the Starlette installed in `JuniperCascor1` (py3.13), so
  `python -m pytest --co` **errors at config parse**
  (`AttributeError: module 'starlette.exceptions' has no attribute 'StarletteDeprecationWarning'`) —
  reproduced first-party. The recurrence-**client** shares the pattern. This is itself an
  **env-drift instance** (the mirror of canopy: CI is presumably green on a pinned older Starlette
  that still has the class, while the live env drifted past it). It **blocks local coverage
  measurement** for these two units until resolved. *Owner:* juniper-recurrence. **Action:** now a
  blocking **Phase B0** step (§11) — pin/guard the filter or the Starlette version; confirm CI's
  pinned Starlette vs the live env.
- **Release-gating inconsistency:** `juniper-cascor-model` is published to PyPI yet has **no coverage
  gate** (`pytest -v` only) while peers enforce 90–95% — §11 B1. *Owner:* juniper-cascor.

**Carried from the debug doc (still open):** I-2 (env provisioning), C-2 (stale commented pins),
D-1/D-2/D-3, A-1/A-2, S-1 — all seeded in §9.3. **Syntax errors:** none found (every cited artifact
resolved), except the **DISC-1** config item flagged for verification.

---

## 15. Appendix — reproduction commands

```bash
J=/home/pcalnon/Development/python/Juniper

# Per-file gap, one unit (after the shared tool ships) — package-form --cov (numpy-2.x safe)
cd "$J/juniper-ml/juniper-doc-tools" && pytest --cov=juniper_doc_tools --cov-report=json:cov.json -q \
  && juniper-check-file-coverage --coverage-json cov.json --min-file 90 --min-submodule-avg 95

# Proof aggregate hides per-file holes (measured this session): doc-tools 87% agg, __main__.py 0%
cd "$J/juniper-ml/juniper-ci-tools" && pytest --cov=juniper_ci_tools --cov-report=term-missing -q

# Locate the canonical canopy debug doc (re-entrant ingestion, §9.1)
find "$J/juniper-ml/notes" "$J/juniper-canopy/notes" -type f -iname 'JUNIPER_CANOPY*' \
  \( -iname '*DEBUG*' -o -iname '*FINDINGS*' -o -iname '*ANALYSIS*' -o -iname '*RUNTIME*' \) \
  -printf '%T+  %p\n' | sort -r | head -1

# The green-but-dead linchpin (both mocked seams)
grep -n "mock_juniper_data_client" "$J/juniper-canopy/src/tests/conftest.py"     # 370-371 autouse
grep -n "sys.modules\[.juniper_cascor_client" "$J/juniper-canopy/src/tests/conftest.py"  # ~182 stub

# The per-module precedent to generalize (K-1)
sed -n '290,310p' "$J/juniper-data/scripts/check_module_coverage.py"

# The numpy-2.x package-form-cov precedent (K-4 / §7.3)
cat "$J/juniper-recurrence/juniper-recurrence-model/.coveragerc.torch"

# DISC-1 verify: does recurrence app collect locally?
cd "$J/juniper-recurrence/juniper-recurrence" && python -m pytest --co -q -p no:cacheprovider
```

---
