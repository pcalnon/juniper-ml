# CI Validation Findings — 2026-04-29

Companion to `notes/CI_VALIDATION_ROADMAP_2026-04-29.md` Phase V1.
Single source of truth for what's failing on each repo's CI right
now. Every fix in Phase V3 references a finding ID from this file.

## Index

| ID | Repo | Workflow | Job | Category | Priority | Group | Status | Fix commit |
|----|------|----------|-----|----------|----------|-------|--------|-----------|
| V01 | juniper-cascor | ci.yml | docs / security / lockfile-check | startup_failure | P0 | G-CONFIG | **fixed** | cascor `c136dc9` |
| V02 | juniper-cascor | lockfile-update.yml | update-lockfile | startup_failure | P0 | G-CONFIG | **fixed** | cascor `c136dc9` |
| V03 | juniper-cascor | security-scan.yml | security-scan | startup_failure | P0 | G-CONFIG | **fixed** | cascor `c136dc9` |
| V04 | juniper-canopy | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | canopy `77d7308` |
| V05 | juniper-cascor | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | cascor `8a32d19` |
| V06 | juniper-data | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | data `53723f1` |
| V07 | juniper-data-client | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | data-client `0bdfbeb` |
| V08 | juniper-cascor-client | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | cascor-client `d5be2a2` |
| V09 | juniper-cascor-worker | security-scan.yml | (single job) | pip-audit (CVE-2026-3219) | P1 | G-INFRA | **fixed** | cascor-worker `1e91f5f` |
| V10 | juniper-cascor-client | ci.yml | unit-tests / integration-tests (Py 3.11) | install (requires-python mismatch) | P1 | G-CONTRACT | **fixed** | cascor-client `99a660b`; ml `b4025fa` (Appendix A) |
| V11 | juniper-canopy | ci.yml | unit-tests | unit (real Dash test failures) | P1 | G-CODE | **deferred** | out-of-scope (canopy product owner) |
| V12 | juniper-canopy | ci.yml | Lockfile Freshness | dependency (lock drift) | P2 | G-CODE | **deferred** | out-of-scope |
| V13 | juniper-data | ci.yml | Lockfile Freshness | dependency (lock drift) | P2 | G-CODE | **deferred** | out-of-scope |
| V14 | juniper-data | ci.yml | pre-commit (matrix) | pre-commit | P1 | G-CONFIG | **fixed** | data `4907da1` (markdownlint .serena exclude) |
| V15 | juniper-canopy | ci.yml | Security Scans (Gitleaks) | gitleaks (repository_dispatch unsupported) | P2 | G-CONFIG | **fixed** | canopy `792ba89` |
| V16 | juniper-deploy | ci.yml | Pre-commit | pre-commit (yamllint MD docstart) | P1 | G-CODE | **fixed** | deploy `926dc31`; ml `b4025fa` (template) |
| V17 | juniper-data | lockfile-update.yml | update | secret missing (CROSS_REPO_DISPATCH_TOKEN) | P2 | G-CONFIG | **deferred** | depends on user-side secret config |
| V18 | juniper-canopy | lockfile-update.yml | update | secret missing (CROSS_REPO_DISPATCH_TOKEN) | P2 | G-CONFIG | **deferred** | depends on user-side secret config |
| V19 | juniper-cascor | scheduled-tests.yml | Performance Benchmarks | unit (real benchmark failure) | P2 | G-CODE | **deferred** | out-of-scope |
| V20 | juniper-cascor | security-scan.yml + ci.yml security | bandit reports B301/B108 issues | bandit (skip-list drift) | P2 | G-CODE | **deferred** | pre-commit bandit skips B301/B108 but standalone runs don't |
| V21 | juniper-canopy / juniper-cascor-client | security-scan.yml | pip-audit `--strict` rejects unpublished editable | pip-audit (strict + editable) | P1 | G-CONFIG | **fixed** | canopy `d6ca33e`; cascor-client `0d5c648` (`--skip-editable`, drop `--strict`) |
| V22 | juniper-cascor-client | ci.yml | Gitleaks "generic-api-key" rule false-positive on test fixture `"explicit-key-789"` (commit `fa942343`, tests/test_client.py:62-63) and on docstring `"client for JuniperCascor"` (juniper_cascor_client/testing/fake_ws_client.py:1) | gitleaks (false-positive on test fixture / docstring) | P1 | G-CONFIG | **fixed** | cascor-client `222b8b2` (initial rule-scoped allowlist) + `9741e18` (top-level allowlist covering both `tests/` and `juniper_cascor_client/testing/`); verified green on run 25208096316 |
| V23 | juniper-cascor | ci.yml | pre-commit (matrix) | pre-commit | P1 | G-CODE | **deferred** | pre-existing pre-commit drift surfaced now that V01 startup_failure cleared |
| V24 | juniper-cascor | ci.yml | Lockfile Freshness | dependency (lock drift) | P2 | G-CODE | **deferred** | out-of-scope |
| V25 | juniper-cascor | ci.yml | Documentation Links | docs (broken doc links) | P2 | G-CODE | **deferred** | out-of-scope |
| V26 | all 6 Python repos with security in ci.yml | ci.yml | pip-audit step | pip-audit (CVE-2026-3219 in ci.yml too) | P1 | G-INFRA | **fixed** | canopy `d6ca33e`; cascor `f8a9d5f`; data `8a9eed4`; data-client `52f89dc`; cascor-client `0d5c648`; cascor-worker `74ad4d1` |
| V27 | juniper-data | ci.yml | unit-tests | unit (test_metrics_endpoint_uses_route_template_for_dataset_path returns 403 instead of 200) | P1 | G-CODE | **deferred** | pre-existing test failure in test_phase_2d_metrics.py |
| V28 | juniper-ml | ci.yml | Documentation Links | docs (6 broken links in JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md → PHASE_6E_DESIGN.md, CAN_013_INTEGRATION_MODE_DESIGN.md, etc.) | P2 | G-CODE | **deferred** | pre-existing doc drift; design docs were never landed |

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
- **Root cause**: real benchmark / regression bisect required.
  Out-of-scope for the alignment work.
- **Group**: G-CODE. Defer.

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
