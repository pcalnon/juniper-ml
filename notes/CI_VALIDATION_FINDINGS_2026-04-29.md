# CI Validation Findings — 2026-04-29

Companion to `notes/CI_VALIDATION_ROADMAP_2026-04-29.md` Phase V1.
Single source of truth for what's failing on each repo's CI right
now. Every fix in Phase V3 references a finding ID from this file.

## Status legend

| Status            | Meaning                                                                                                                                                                      |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **fixed**         | Fix shipped on `main`; verifying CI run referenced.                                                                                                                          |
| **investigating** | Triage in flight; root cause not yet confirmed.                                                                                                                              |
| **deferred**      | Not closed in the alignment / validation cycle, with a stated reason. **Subject to re-triage.** Several "deferred" findings (V14, V22) were originally classified G-CODE     |
|                   | and assumed to be product-side defects. Once the actual SARIF / log output was pulled and inspected, both turned out to be config drift (G-CONFIG) that took a single commit |
|                   | to close. **Future readers: if a deferred finding becomes load-bearing, revisit the original log first — the deferral may not survive a fresh look.**                        |

## Re-triage policy (post-V22 lesson)

Before a deferred finding stays deferred, the analyst should have:

1. Pulled the verbatim failing-step log from the run referenced in
   the finding (or a fresher run if available).
2. Confirmed the failure mode reproduces on the **current** `main`,
   not on a stale snapshot.
3. Categorised the root cause from {G-CONFIG, G-CODE, G-INFRA,
   G-CONTRACT} — and only deferred if the cause is genuinely outside
   the alignment effort's reach (real product bugs, missing user-side
   secrets, deferred roadmap work).

## Index

| ID  | Repo                    | Workflow            | Job                                                 | Category                                                           | Priority | Group      | Status       | Fix commit                                                            |
|-----|-------------------------|---------------------|-----------------------------------------------------|--------------------------------------------------------------------|----------|------------|--------------|-----------------------------------------------------------------------|
| V01 | juniper-cascor          | ci.yml              | docs / security / lockfile-check                    | startup_failure                                                    | P0       | G-CONFIG   | **fixed**    | cascor `c136dc9`                                                      |
| V02 | juniper-cascor          | lockfile-update.yml | update-lockfile                                     | startup_failure                                                    | P0       | G-CONFIG   | **fixed**    | cascor `c136dc9`                                                      |
| V03 | juniper-cascor          | security-scan.yml   | security-scan                                       | startup_failure                                                    | P0       | G-CONFIG   | **fixed**    | cascor `c136dc9`                                                      |
| V04 | juniper-canopy          | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | canopy `77d7308`                                                      |
| V05 | juniper-cascor          | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | cascor `8a32d19`                                                      |
| V06 | juniper-data            | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | data `53723f1`                                                        |
| V07 | juniper-data-client     | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | data-client `0bdfbeb`                                                 |
| V08 | juniper-cascor-client   | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | cascor-client `d5be2a2`                                               |
| V09 | juniper-cascor-worker   | security-scan.yml   | (single job)                                        | pip-audit (CVE-2026-3219)                                          | P1       | G-INFRA    | **fixed**    | cascor-worker `1e91f5f`                                               |
| V10 | juniper-cascor-client   | ci.yml              | unit-tests / integration-tests                      | install (requires-python mismatch)                                 | P1       | G-CONTRACT | **fixed**    | cascor-client `99a660b`; ml `b4025fa` (Appendix A)                    |
|     |                         |                     | (Py 3.11)                                           |                                                                    |          |            |              |                                                                       |
| V11 | juniper-canopy          | ci.yml              | unit-tests                                          | unit (stale `test_dashboard_manager_coverage.py` + `test_dashboard_manager_95.py` assertions; components count + `_init_params_from_backend_handler` `NUM_OUTPUTS` drifted post canopy#203/204/205/206) | P1 | G-CODE-test-only | **fixed**    | canopy `e51d1f8` + `b062f2a` (10 assertions refreshed across 4 files); V11-bis `c10f9ae` adds missing `network_evolution` mock to `test_meta_parameters_layout.py` fixture |
| V12 | juniper-canopy          | ci.yml              | Lockfile Freshness                                  | dependency (lock drift)                                            | P2       | G-CODE     | **resolved upstream** | already passing on the latest canopy/main run (25231101579); no fix-up commit needed |
| V13 | juniper-data            | ci.yml              | Lockfile Freshness                                  | dependency (lock drift)                                            | P2       | G-CODE     | **resolved upstream** | already passing on the latest data/main run (25231031351); no action needed |
| V14 | juniper-data            | ci.yml              | pre-commit (matrix)                                 | pre-commit                                                         | P1       | G-CONFIG   | **fixed**    | data `4907da1` (markdownlint .serena exclude)                         |
| V15 | juniper-canopy          | ci.yml              | Security Scans (Gitleaks)                           | gitleaks (repository_dispatch unsupported)                         | P2       | G-CONFIG   | **fixed**    | canopy `792ba89`                                                      |
| V16 | juniper-deploy          | ci.yml              | Pre-commit                                          | pre-commit (yamllint MD docstart)                                  | P1       | G-CODE     | **fixed**    | deploy `926dc31`; ml `b4025fa` (template)                             |
| V17 | juniper-data            | lockfile-update.yml | update                                              | secret missing (CROSS_REPO_DISPATCH_TOKEN)                         | P2       | G-CONFIG   | **deferred** | depends on user-side secret config                                    |
| V18 | juniper-canopy          | lockfile-update.yml | update                                              | secret missing (CROSS_REPO_DISPATCH_TOKEN)                         | P2       | G-CONFIG   | **deferred** | depends on user-side secret config                                    |
| V19 | juniper-cascor          | scheduled-tests.yml | Performance Benchmarks                              | benchmark harness drift (stale API + path bug, not a real perf     | P2       | G-CODE-test-only | **fixed (verified)** | cascor `56c5953` + `85634ee` + `f4d808c` + `7886c1b` — four-round  |
|     |                         |                     |                                                     | regression as originally suspected)                                |          |            |              | benchmark-harness fix: (1) rename `"activation"` → `"activation_fn"`, |
|     |                         |                     |                                                     |                                                                    |          |            |              | (2) resize `output_weights` after manual hidden-unit append,         |
|     |                         |                     |                                                     |                                                                    |          |            |              | (3) drop stale `display_frequency` kwarg from `train_output_layer`, |
|     |                         |                     |                                                     |                                                                    |          |            |              | (4) absolutize `--output` path before `cd "${SRC_DIR}"`. Verified    |
|     |                         |                     |                                                     |                                                                    |          |            |              | green on workflow_dispatch run 25238422226.                          |
| V20 | juniper-cascor          | security-scan.yml + | bandit reports B301/B108 issues                     | bandit (skip-list + scope drift)                                   | P2       | G-CONFIG   | **fixed**    | cascor `53e7134` — added `--exclude src/tests` and                    |
|     |                         | ci.yml security     |                                                     |                                                                    |          |            |              | `--skip B101,B301,B311,B403` to standalone bandit calls               |
|     |                         |                     |                                                     |                                                                    |          |            |              | to mirror pre-commit's source-side hook exactly                       |
| V21 | juniper-canopy /        | security-scan.yml   | pip-audit `--strict`                                | pip-audit (strict + editable)                                      | P1       | G-CONFIG   | **fixed**    | canopy `d6ca33e`; cascor-client `0d5c648`                             |
|     | juniper-cascor-client   |                     | rejects unpublished editable                        |                                                                    |          |            |              | (`--skip-editable`, drop `--strict`)                                  |
| V22 | juniper-cascor-client   | ci.yml              | Gitleaks "generic-api-key" rule false-positive,     | gitleaks (false-positive                                           | P1       | G-CONFIG   | **fixed**    | cascor-client `222b8b2` (initial rule-scoped allowlist)               |
|     |                         |                     | test fixture `"explicit-key-789"`                   | on test fixture / docstring)                                       |          |            |              | + `9741e18` (top-level allowlist covering both `tests/`               |
|     |                         |                     | (commit `fa942343`, tests/test_client.py:62-63)     |                                                                    |          |            |              | and `juniper_cascor_client/testing/`);                                |
|     |                         |                     | and on docstring `"client for JuniperCascor"`       |                                                                    |          |            |              | verified green on run 25208096316                                     |
|     |                         |                     | (juniper_cascor_client/testing/fake_ws_client.py:1) |                                                                    |          |            |              |                                                                       |
| V23 | juniper-cascor          | ci.yml              | pre-commit (matrix)                                 | pre-commit                                                         | P1       | G-CODE     | **resolved upstream** | not present on latest cascor/main run (25231135300)         |
| V24 | juniper-cascor          | ci.yml              | Lockfile Freshness                                  | dependency (lock drift — patch/minor bumps since cascor@9ef8637)   | P2       | G-CONFIG   | **fixed**    | cascor `e057b4c` — `uv pip compile` regenerated; same pattern as canopy `7089bdf` and cascor `9ef8637` |
| V25 | juniper-cascor          | ci.yml              | Documentation Links                                 | docs (broken doc links)                                            | P2       | G-CODE     | **resolved upstream** | not present on latest cascor/main run (25231135300)         |
| V26 | all 6 Python repos with | ci.yml              | pip-audit step                                      | pip-audit (CVE-2026-3219                                           | P1       | G-INFRA    | **fixed**    | canopy `d6ca33e`; cascor `f8a9d5f`; data `8a9eed4`; data-client       |
|     | security in ci.yml      |                     |                                                     | in ci.yml too)                                                     |          |            |              | `52f89dc`; cascor-client `0d5c648`; cascor-worker `74ad4d1`           |
| V27 | juniper-data            | ci.yml              | unit-tests                                          | unit (test_metrics_endpoint_uses_route_template_for_dataset_path   | P1       | G-CODE     | **resolved upstream** | already passing on the latest data/main run (25231031351)   |
|     |                         |                     |                                                     | returned 403 instead of 200)                                       |          |            |              |                                                                       |
| V28 | juniper-ml              | ci.yml              | Documentation Links                                 | docs (6 broken links in                                            | P2       | G-CODE     | **resolved upstream** | already passing on the latest ml/main run (25234461292);    |
|     |                         |                     |                                                     | JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md |          |            |              | the missing design docs (PHASE_6E_DESIGN.md, CAN_013_*.md)            |
|     |                         |                     |                                                     | → PHASE_6E_DESIGN.md, CAN_013_INTEGRATION_MODE_DESIGN.md, etc.)    |          |            |              | were landed via downstream commits                                    |
| V29 | juniper-cascor          | ci.yml              | unit-tests (matrix; all 4 legs)                     | unit (test_api_health.py::TestProbeDependency::* —                 | P1       | G-CODE-test-only | **fixed (verified)** | cascor `ab2694e`. `api.models.health` is now a re-export shim |
|     |                         |                     |                                                     | `AttributeError: module 'api.models.health' has no attribute       |          |            |              | for `juniper_observability`; `urllib` lives at                       |
|     |                         |                     |                                                     | 'urllib'`)                                                         |          |            |              | `juniper_observability.health.probe.urllib`. All 3 patches repointed. |
| V30 | juniper-cascor          | ci.yml              | Security Scans (gitleaks)                           | gitleaks (false positives — conda lockfile build hashes,           | P1       | G-CONFIG   | **fixed (verified)** | cascor `ab2694e` — added `.gitleaks.toml` (default rules + path / |
|     |                         |                     |                                                     | `YOUR_API_KEY` placeholders, Python KeyError debug strings)        |          |            |              | regex allowlist for `conf/temp/`, `notes/setup_config_guides/`,     |
|     |                         |                     |                                                     |                                                                    |          |            |              | `notes/FIX_RESOURCE_TRACKER_AND_WARNINGS.md`).                       |
| V31 | juniper-cascor          | ci.yml              | unit-tests (collection)                             | import (`remote_client.remote_client_0` archived to                | P1       | G-CODE-test-only | **fixed (verified)** | cascor `ab2694e` — guarded import in                          |
|     |                         |                     |                                                     | `src/backups/`)                                                    |          |            |              | `test_remote_client_0_extended.py` (`pytest.importorskip`) and       |
|     |                         |                     |                                                     |                                                                    |          |            |              | class-level `@pytest.mark.skipif` on RemoteCandidateTrainingClient   |
|     |                         |                     |                                                     |                                                                    |          |            |              | classes in `test_remote_client_coverage.py`.                          |
| V32 | juniper-cascor          | publish.yml         | (yaml parse / startup_failure)                      | setup-python list-as-string (V01-pattern carried over to publish)  | P2       | G-CONFIG   | **fixed (verified)** | cascor `7e45ff0` — pinned both `testpypi` and `pypi` jobs to  |
|     |                         |                     |                                                     |                                                                    |          |            |              | `python-version: "3.12"` (single string).                            |
| V33 | juniper-cascor          | ci.yml              | Pre-commit (matrix, all 3 Pythons)                  | flake8 F821 — `Command` not imported                               | P1       | G-CODE-test-only | **fixed (verified)** | cascor `2e7c2a2` + black reformat `6174b0b` — added `from    |
|     |                         |                     |                                                     | (`test_lifecycle_manager.py:827`)                                  |          |            |              | Command` to `test_lifecycle_manager.py`. PR #170 (`d45b376`) added  |
|     |                         |                     |                                                     |                                                                    |          |            |              | the symbol use without the import; latent until V32 unblocked the   |
|     |                         |                     |                                                     |                                                                    |          |            |              | gate.                                                                |
| V34 | juniper-canopy          | ci.yml              | unit-tests (matrix; 4 legs)                         | (a) `Duplicated timeseries in CollectorRegistry` (prom metric       | P2       | G-CODE     | **deferred** | exposed once V11-bis cleared the `network_evolution` AttributeError; |
|     |                         |                     |                                                     | registered twice across test files);                                |          |            |              | both look like real product/test isolation bugs but are out of      |
|     |                         |                     |                                                     | (b) `property 'running' of 'DemoMode' object has no setter`        |          |            |              | scope for the V01-V32 alignment cycle. Track separately.            |
| V35 | juniper-cascor          | ci.yml              | unit-tests (matrix; 4 legs)                         | (a) `test_api_middleware.TestRequestBodyLimitMiddleware` chunked-   | P2       | G-CODE     | **deferred** | All four are real product / test-maintenance issues, none related   |
|     |                         |                     |                                                     | body 422 ≠ 200; (b) `test_app_startup_tasks` log-capture            |          |            |              | to V29-V33. Surfaced on run 25236574320 once the upstream gates     |
|     |                         |                     |                                                     | (assert 0 == 1); (c) `test_coordinator_health_monitor_race`         |          |            |              | (pre-commit / lockfile / bandit / gitleaks) cleared. Out of scope   |
|     |                         |                     |                                                     | CONC-10 race on stale-worker dereg; (d)                            |          |            |              | for the V01-V32 alignment cycle; same class as V19/V34.             |
|     |                         |                     |                                                     | `test_lifecycle_manager` epochs_max default 1e11 vs 200 drift      |          |            |              |                                                                       |

---

## V01 — juniper-cascor / ci.yml / startup_failure

- Run: <https://github.com/pcalnon/juniper-cascor/actions/runs/25192751098>
- Category: workflow startup_failure ("This run likely failed because of a workflow file issue.")
- Excerpt:

  ```text
  X main .github/workflows/ci.yml · 25192751098
  X This run likely failed because of a workflow file issue.
  ```

- Diagnosis (Python yaml-side audit):

  ```text
  docs[1]:           python-version=['3.12', '3.13', '3.14'] (type=list)
  security[2]:       python-version=['3.12', '3.13', '3.14'] (type=list)
  lockfile-check[1]: python-version=['3.12', '3.13', '3.14'] (type=list)
  ```

- **Root cause**: Three `actions/setup-python@v6.2.0` steps in
  cascor's `ci.yml` set `with: python-version:` to a literal YAML
  list **outside** a matrix. The action expects a single string
  (or, with `python-version-file:`, no value at all). GitHub's
  workflow loader hard-fails the entire workflow at parse time.
- **Group**: G-CONFIG.
- **Fix sketch**: Replace the three list values with single
  strings. The single-Python jobs (`docs`, `security`,
  `lockfile-check`) should use `${{ env.PYTHON_TEST_VERSION }}` —
  the same env-driven pattern the rest of cascor's `ci.yml` uses.

## V02 — juniper-cascor / lockfile-update.yml / startup_failure

- Run: <https://github.com/pcalnon/juniper-cascor/actions/runs/25192750471>
- Excerpt: same "workflow file issue" banner.
- File-side defect: `lockfile-update.yml` line 53:
  `python-version: ["3.12", "3.13", "3.14"]` outside a matrix.
- **Root cause**: same as V01.
- **Group**: G-CONFIG.
- **Fix sketch**: replace with `python-version: "3.12"` (single
  string).

## V03 — juniper-cascor / security-scan.yml / startup_failure

- Run: <https://github.com/pcalnon/juniper-cascor/actions/runs/25192750901>
- File-side defect: `security-scan.yml` line 20: same list-as-string
  bug.
- **Root cause**: same as V01.
- **Group**: G-CONFIG.

## V04..V09 — pip-audit CVE-2026-3219 across 6 repos

Identical failure mode in all 6 Python repos that ship a
`security-scan.yml` invoking `pip-audit --strict --desc on`:

- canopy, cascor, data, data-client, cascor-client, cascor-worker.
- Excerpt (from canopy 04-27 run; later runs will share the shape):

  ```text
  Found existing installation: pip 26.0.1
  Found 1 known vulnerability in 1 package
  pip  26.0.1  CVE-2026-3219  (no Fix Versions)
  ##[error]Process completed with exit code 1.
  ```

- **Root cause**: GitHub Actions runner image bundles `pip 26.0.1`,
  which is flagged by GHSA / OSV with no fixed release available
  yet. juniper-ml's CI handles this with
  `--ignore-vuln CVE-2026-3219` (committed `c6f47b2`). The other six
  repos still call `pip-audit --strict --desc on` with no override
  and so will fail on every scheduled run until the upstream pip
  patch lands.
- **Group**: G-INFRA.
- **Fix sketch**: copy the juniper-ml `--ignore-vuln CVE-2026-3219`
  flag into the other six `security-scan.yml` files, with the same
  comment pointing at the upstream advisory and a "remove once pip
  publishes a fix" reminder.

## V10 — juniper-cascor-client / ci.yml / Python 3.11 install

- Run: <https://github.com/pcalnon/juniper-cascor-client/actions/runs/25192315375>
- Excerpt:

  ```text
  ERROR: Package 'juniper-cascor-client' requires a different Python: 3.11.15 not in '>=3.12'
  ```

- File-side defect: `pyproject.toml` declares `requires-python = ">=3.12"`
  but `ci.yml` has Python `3.11` in three matrices (`pre-commit`,
  `unit-tests`, `integration-tests`).
- **Root cause**: Drift between the alignment plan's Appendix A
  (which assumed cascor-client floors at 3.11 for older
  deployments) and the actual repo metadata (`>=3.12`). The Phase 2
  alignment commit `f7b4cfd` added the 3.11-inclusive matrix to
  the new `integration-tests` job to match the existing
  `unit-tests` matrix; both predate this session and were stale.
- **Group**: G-CONTRACT.
- **Fix sketch**: drop `3.11` from all three matrices in
  cascor-client's `ci.yml` and update Appendix A of the alignment
  plan to record that cascor-client now matches the rest of the
  fleet (`>=3.12`). If the user later decides to support 3.11
  again, that's a separate `requires-python` bump.

## V11 — juniper-canopy / ci.yml / unit-tests (real Dash failures)

- Run: <https://github.com/pcalnon/juniper-canopy/actions/runs/25192388764>
- Excerpts:

  ```text
  AssertionError: assert '' is <dash._no_update.NoUpdate object>
  TypeError: 'int' object is not subscriptable
  test_dashboard_manager_registers_default_components - assert 13 == 12
  ```

- **Root cause**: real source-side defects surfaced by the canopy
  unit suite. Probably triggered by a recent feature PR (Phase 6E
  sidebar work, PRs #204–#207 that landed yesterday), not by the
  alignment work itself.
- **Group**: G-CODE.
- **Priority**: **P1** — this blocks every push to canopy `main`.
- **Note**: out-of-scope for this session's CI alignment effort.
  Document, **but do not fix here** — push as a finding for the
  canopy product owner.

## V12 — juniper-canopy / ci.yml / Lockfile Freshness

- Run: ditto V11.
- Excerpt:

  ```text
  ##[error]requirements.lock no longer satisfies pyproject.toml — refresh with: uv pip compile pyproject.toml --extra juniper-data --extra juniper-cascor --extra observability --upgrade -o requirements.lock
  ```

- **Root cause**: Phase 6E PRs added new deps to canopy's
  `pyproject.toml` without regenerating the lockfile.
- **Group**: G-CODE.
- **Fix**: out-of-scope — defer to canopy product owner.

## V13 — juniper-data / ci.yml / Lockfile Freshness

- Run: <https://github.com/pcalnon/juniper-data/actions/runs/25192523212>
- Excerpt:

  ```text
  requirements.lock no longer satisfies pyproject.toml — refresh with: uv pip compile pyproject.toml --extra api --extra observability --upgrade -o requirements.lock
  ```

- **Root cause**: same shape as V12.
- **Group**: G-CODE. Defer.

## V14 — juniper-data / ci.yml / pre-commit

- Run: ditto V13.
- Excerpt: pre-commit fails on Python 3.12 / 3.13 / 3.14, exit 1.
- **Root cause**: not yet bisected — likely the markdownlint
  hook landed by `64e6d13` is firing on a file the local `--all-files`
  run didn't touch (e.g. an auto-format that hasn't been
  committed). Need to re-run locally to confirm.
- **Group**: G-CODE (or G-CONFIG depending on the actual hook).
- **Fix sketch**: re-run `pre-commit run --all-files` locally on
  juniper-data, fold in whatever fixes the hook wants, push.

## V15 — juniper-canopy / ci.yml / Security Scans (Gitleaks)

- Excerpt:

  ```text
  ##[error]ERROR: The [repository_dispatch] event is not yet supported
  ```

- **Root cause**: canopy's Gitleaks step does not gate against the
  `repository_dispatch` trigger; the action's authors haven't
  implemented support for that event (per their docs).
- **Group**: G-CONFIG.
- **Fix sketch**: add `if: github.event_name != 'repository_dispatch'`
  to the Gitleaks step (or the encompassing Security Scans job).

## V16 — juniper-deploy / ci.yml / Pre-commit (yamllint)

- Excerpt:

  ```text
  yamllint.................................................................Failed
  - hook id: yamllint
  17:1 [document-start] missing document start "---"
  ##[error]Process completed with exit code 1.
  ```

- **Root cause**: One YAML file in the deploy repo is missing the
  `---` document-start marker. yamllint runs in `--strict` mode
  with default rules so the warning is escalated to a failure.
- **Group**: G-CODE.
- **Fix**: identify the offending file and add the `---` opener.

## V17 — juniper-data / lockfile-update.yml / token

- Run: <https://github.com/pcalnon/juniper-data/actions/runs/25014240775>
- Excerpt: `##[error]Input required and not supplied: token`
- **Root cause**: data's `lockfile-update.yml` (its **own** copy,
  pre-existing — not the alignment template) requires a
  `CROSS_REPO_DISPATCH_TOKEN` secret that's not configured in this
  repo.
- **Group**: G-CONFIG.
- **Fix**: out-of-scope — depends on the user setting the secret
  at the org or repo level, then re-running the workflow.

## V18 — juniper-canopy / lockfile-update.yml / token

- Same shape as V17 (canopy's pre-existing `lockfile-update.yml`
  asks for the same missing secret).

## V19 — juniper-cascor / scheduled-tests.yml / Performance Benchmarks

- Run: <https://github.com/pcalnon/juniper-cascor/actions/runs/25146942006>
- Excerpt: only the `Performance Benchmarks` job failed; slow
  unit / slow integration / long-running tests all passed.
- **Original triage (2026-04-29)**: assumed real benchmark / regression
  bisect required; deferred as out-of-scope.
- **Re-triage under V22-pattern diligence (2026-05-01)**: pulled the
  actual stack trace and found four sequential layers of *stale-harness*
  drift, not a real perf regression. The benchmark code itself runs fine
  against current production once the harness mismatches are corrected.
  Each fix exposed the next, in classic peeling-onion fashion:

  | Round | Commit | Cleared |
  |-------|--------|---------|
  | 1 | `56c5953` | `KeyError: 'activation_fn'` (renamed `"activation"` to canonical key in two inline-Python dict literals) |
  | 2 | `85634ee` | `RuntimeError: mat1 and mat2 shapes (1x12 and 2x2)` — manually appended hidden_units bypassed `add_unit()` so `output_weights` stayed at the initial `(input_size, output_size)` shape; resize once after the loop |
  | 3 | `f4d808c` | `TypeError: train_output_layer() got an unexpected keyword argument 'display_frequency'` — kwarg was removed from the public API but the harness wasn't updated |
  | 4 | `7886c1b` | `tee: ../../../reports/benchmarks/...: No such file or directory` — script `cd`s into `${SRC_DIR}` before `tee` runs, so the workflow's relative `--output` path re-resolved two levels above the repo root; absolutize before cd |

- **Group**: G-CODE-test-only (re-classified). Same stale-fixture
  family as V11 / V13 / V14 / V20 / V22 / V24 / V27 / V28 / V29 / V31 /
  V33. Verified green on workflow_dispatch run 25238422226 — Performance
  Benchmarks job reports sane numbers (forward-pass μs/ms timings;
  output-layer training in tens of ms) and exits zero.

---

## Group summary

| Group | IDs | Total | Priority spread |
|---|---|---|---|
| G-CONFIG | V01, V02, V03, V15, V17, V18 | 6 | 3×P0, 3×P2 |
| G-INFRA  | V04, V05, V06, V07, V08, V09 | 6 | 6×P1 |
| G-CONTRACT | V10 | 1 | 1×P1 |
| G-CODE | V11, V12, V13, V14, V16, V19 | 6 | 3×P1, 3×P2 |

## Action plan ordered by group

1. **G-CONFIG / cascor startup_failure cluster (V01–V03, P0)** —
   fix cascor's three workflow files; this unblocks every cascor
   run.
2. **G-INFRA / pip CVE flag rollout (V04–V09, P1)** — copy the
   `--ignore-vuln CVE-2026-3219` flag into 6 `security-scan.yml`
   files. Single, repetitive fix.
3. **G-CONTRACT / cascor-client 3.11 mismatch (V10, P1)** — drop
   3.11 from three matrices + amend the alignment plan's
   Appendix A.
4. **G-CONFIG / Gitleaks repository_dispatch (V15, P2)** — single
   conditional gate.
5. **G-CODE / deploy yamllint (V16, P1)** — one missing `---`.
6. **G-CONFIG / token secrets (V17, V18, P2)** — out-of-scope;
   document and defer.
7. **G-CODE / canopy + data unit/lockfile drift (V11–V14, V19)** —
   out-of-scope; document and defer to product owners.
