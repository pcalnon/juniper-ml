# CI Alignment + Validation — Closeout Audit

**Date**: 2026-04-29
**Author**: Paul Calnon (with Claude Opus 4.7)
**Companion docs**:

- `notes/CI_PIPELINE_ALIGNMENT_PLAN_2026-04-29.md` — original plan.
- `notes/CI_VALIDATION_ROADMAP_2026-04-29.md` — validation phases V0–V5.
- `notes/CI_VALIDATION_FINDINGS_2026-04-29.md` — single source of truth
  for every issue surfaced by the validation pass.

This document audits the original alignment plan against the final
state of the fleet after the validation + remediation pass, and
records what worked, what didn't, and what's left for a follow-up
cycle.

---

## 1. What the alignment plan committed to

§4 of the alignment plan defined a baseline shape every applicable
repo had to meet:

- **Workflows**: `ci.yml`, `codeql.yml`, `claude.yml`,
  `security-scan.yml`, `docs-full-check.yml`, `scheduled-tests.yml`,
  `lockfile-update.yml`, `publish*.yml`.
- **Pre-commit hook union**: black/isort/flake8 (or ruff) + mypy +
  bandit + shellcheck + markdownlint + yamllint +
  `no-unencrypted-env`.
- **Required-checks aggregator** + Python `3.12 / 3.13 / 3.14`
  matrix (3.11 only where the repo already supports it).
- **Coverage gate preserved** at the strictest level any repo
  carries (no fleet-wide downward harmonization).
- **Additive-only**.

## 2. What actually shipped

17 commits across 8 repos in the alignment rollout (Phase 0–4).
Plus 13 commits across 7 repos in the validation remediation
(V01–V26 fixes). All on `main`; every commit verified by
`git rev-list --left-right --count origin/main...HEAD == 0 0`.

| Layer                                        | Repos touched | Commits |
|----------------------------------------------|---------------|---------|
| Alignment plan (Phase 0–4)                   | 8             | 17      |
| Validation remediation (V01–V26)             | 7             | 13      |
| Doc / template corrections during validation | ml            | 4       |
| **Total this session**                       | **8**         | **34**  |

## 3. Alignment plan vs reality

| Plan claim                                                                 | Reality                                                                                                                                                               | Variance             |
|----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| §4.1 fleet has 7 standard workflows + publish                              | All 8 repos have them, modulo Appendix-A exclusions                                                                                                                   | ✓                    |
| §4.2 pre-commit hook union present                                         | Yes — confirmed by `grep '^\s*-\s*id:'` against every repo                                                                                                            | ✓                    |
| §4.4 required-checks aggregator                                            | Present on every repo                                                                                                                                                 | ✓                    |
| §4.4 Python 3.12/3.13/3.14 matrix                                          | Present on all repos except deploy (infra-only)                                                                                                                       | ✓                    |
| Appendix-A: cascor-client floors at 3.11                                   | **WRONG** — actual `requires-python` is `>=3.12`. Corrected during V10 remediation; Appendix A struck through.                                                        | corrected            |
| §9 risk register: `claude.yml` rollout reveals missing `ANTHROPIC_API_KEY` | Did not surface (no `@claude` mention to test against; `claude.yml` runs are `skipped` until a mention happens). User-side secret config is deferred-but-presumed-ok. | latent               |
| §9 risk register: trivy on deploy fails on transitive base-image CVEs      | Did not fire — trivy ran clean on the first deploy security-scan. Soft-fail flag can be removed safely.                                                               | better than expected |
| §9 risk register: First CodeQL run reveals findings                        | All 7 Python CodeQL workflows passed on first run. No findings to triage.                                                                                             | better than expected |
| §9 risk register: New job exposes pre-existing latent failure              | **CONFIRMED multiple times** — see §4 below                                                                                                                           | as expected          |

## 4. Pre-existing failures the validation pass exposed

The alignment work itself didn't break anything. But by adding more
checks and re-triggering pipelines, several pre-existing issues
surfaced for the first time:

| Finding | Surface                                           | What it actually was                                                                                               |
|---------|---------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| V11     | canopy ci.yml unit-tests                          | Real Dash test failures from PRs #204–#207 (Phase 6E sidebar work) — independent of alignment                      |
| V12     | canopy ci.yml lockfile drift                      | Same Phase 6E PRs added deps without refreshing the lockfile                                                       |
| V13     | data ci.yml lockfile drift                        | Same shape; pre-existing                                                                                           |
| V17     | data lockfile-update.yml                          | Missing `CROSS_REPO_DISPATCH_TOKEN` secret — never configured                                                      |
| V18     | canopy lockfile-update.yml                        | Same                                                                                                               |
| V19     | cascor scheduled-tests.yml Performance Benchmarks | Real perf bisect needed; pre-existing                                                                              |
| V20     | cascor security-scan + ci.yml bandit step         | Pre-commit bandit skips B301/B108/B311; the standalone bandit invocations don't, so they surface long-known issues |
| V22     | cascor-client gitleaks                            | Real committed secrets; needs user-side triage / allowlist / rotation                                              |
| V23     | cascor ci.yml pre-commit                          | Pre-commit drift surfaces only now that V01 startup_failure has cleared                                            |
| V24     | cascor ci.yml lockfile                            | Same                                                                                                               |
| V25     | cascor ci.yml docs                                | Same                                                                                                               |

All are explicitly **deferred** in the findings doc with reasoning;
they belong to per-repo product owners, not the alignment effort.

## 5. Closed root-cause groups

| Group                                                 | IDs                        | Result                                                          |
|-------------------------------------------------------|----------------------------|-----------------------------------------------------------------|
| G-CONFIG (cascor startup_failure)                     | V01, V02, V03              | **closed** (cascor `c136dc9`)                                   |
| G-INFRA (pip CVE-2026-3219)                           | V04–V09, V26               | **closed** (one commit per repo, plus the in-`ci.yml` mop-up)   |
| G-CONTRACT (cascor-client 3.11 mismatch)              | V10                        | **closed** (cascor-client `99a660b`; ml plan Appendix A struck) |
| G-CONFIG (gitleaks repository_dispatch)               | V15                        | **closed** (canopy `792ba89`)                                   |
| G-CONFIG (deploy yamllint document-start)             | V16                        | **closed** (deploy `926dc31`; template `b4025fa`)               |
| G-CONFIG (data markdownlint .serena)                  | V14                        | **closed** (data `4907da1`)                                     |
| G-CONFIG (canopy / cascor-client `--strict` editable) | V21                        | **closed** (canopy `d6ca33e`; cascor-client `0d5c648`)          |
| G-CODE (deferred pre-existing)                        | V11–V13, V19, V20, V22–V25 | **deferred** (out-of-scope — owners notified via this doc)      |
| G-CONFIG (deferred user-side secret)                  | V17, V18                   | **deferred** (`CROSS_REPO_DISPATCH_TOKEN` secret config)        |

## 6. Soft-fail → hard-gate promotion table

| Repo                  | Soft-fail surface                              | Status                                                                                                          | Action                                                                                                      |
|-----------------------|------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| juniper-deploy        | `trivy-fs` `continue-on-error: true`           | Two consecutive green security-scan runs (after `---` fix in `claude.yml` cleared the workflow) → criterion met | **Ready to promote** — remove `continue-on-error`.                                                          |
| juniper-data-client   | `integration-tests` warning + exit-code-5 skip | Two consecutive ci.yml greens with no integration tests in the suite — criterion met (job is currently a no-op) | **Hold** — premature to promote; the job is harmless as-is. Keep soft-fail until the suite has real tests.  |
| juniper-cascor-client | same                                           | Latest ci.yml run still failing on V22 (gitleaks real findings) — out of scope                                  | Hold                                                                                                        |
| juniper-cascor-worker | same                                           | Two greens — criterion met                                                                                      | **Hold** — same reason as data-client.                                                                      |
| All Python repos      | First CodeQL run                               | All 7 CodeQL runs already green; no shakedown findings                                                          | **Already promoted** — no flag to flip; CodeQL findings live in the Security tab, not in `required-checks`. |

(Final promotion happens inline below as runs confirm the second
consecutive green.)

## 7. Drift the validation pass introduced (and corrected)

- The canonical `claude.yml` template lacked `---`; deploy yamllint
  caught it on first land. Corrected in template + deploy in
  lockstep (`b4025fa` + `926dc31`).
- Phase 1 cascor-client `integration-tests` matrix included Python
  3.11; pyproject said `>=3.12`. Corrected by dropping 3.11 from
  three matrices + striking Appendix-A entry (`99a660b` + `b4025fa`).
- Phase 3 markdownlint addition on data left tracked-but-stale
  `.serena/` files churning in CI. Corrected by extending the
  hook's `exclude:` regex (`4907da1`).

## 8. Lessons for the next alignment cycle

1. **Audit Appendix-A claims against `pyproject.toml`** before the
   plan is finalized. Using a stale "client floors at 3.11"
   statement caused a P1 follow-up.
2. **Walk every existing pip-audit invocation** (in both
   `security-scan.yml` AND any in-`ci.yml` security job) when
   adding a `--ignore-vuln` flag for a fleet-wide CVE. Fleet
   alignment isn't just about workflow files; it's about every
   consistent invocation across them.
3. **Add `---` to every templated workflow file** so stricter
   yamllint configs don't fail on first land.
4. **Compute the gitignore-vs-git-ls-files delta** when adding a
   new auto-fix hook (markdownlint, ruff format) so
   tracked-but-gitignored stale files get excluded explicitly.
5. **First-run shakedown approach worked**. Both `trivy-fs` and
   CodeQL were green on the first run — the soft-fail flag was a
   safety net we ended up not needing. Keep the pattern; the
   savings come from never having a single bad scan block CI.
6. **Out-of-scope discipline matters**. The validation pass found
   13 pre-existing issues that have nothing to do with alignment.
   Documenting them with explicit "deferred — owner is X"
   statements lets the alignment work close cleanly without
   blocking on product-side bugs.

## 9. Final state-of-the-fleet snapshot (post Phase V3)

After the Phase V3 remediation pass (commits c136dc9 through
c431fd1 across 7 repos) and a full re-trigger of `ci.yml` +
`security-scan.yml` on every repo:

| Repo                      | `ci.yml`  | `security-scan.yml`  | Outstanding (deferred)                                                                                                                          |
|---------------------------|-----------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **juniper-ml**            | ✅        | ✅                   | — (V28 resolved upstream; design docs landed downstream)                                                                                        |
| juniper-canopy            | ⚠ pending re-run | ✅                   | V11 fixed across three commits (canopy `e51d1f8` + `b062f2a` + `c10f9ae` V11-bis network_evolution mock, 11 stale assertions across 5 files); V12 resolved upstream; V18 still deferred (user-side secret); V34 deferred (DemoMode setter / Prometheus registry duplication exposed once V11-bis cleared the AttributeError gate) |
| juniper-cascor            | ⚠ unit-tests only | ✅                   | V20 fixed (`53e7134`); V24 fixed (`e057b4c`); V29 fixed (`ab2694e` — repointed urllib patches at `juniper_observability.health.probe`); V30 fixed (`ab2694e` — `.gitleaks.toml` allowlist); V31 fixed (`ab2694e` — guarded `remote_client_0` import on archived module); V32 fixed (`7e45ff0` — `publish.yml` setup-python list-as-string); V33 fixed (`2e7c2a2` + black reformat `6174b0b`); V23 + V25 resolved upstream; **all CI gates green except Unit Tests** (verified on run 25236574320). V19 still deferred (perf bisect); V35 deferred (4 downstream unit-test issues exposed post-cycle: middleware chunked-body 422, startup-task log capture, CONC-10 worker race, lifecycle epochs_max default drift). |
| **juniper-data**          | ✅        | ✅                   | — (V13 + V27 resolved upstream); V17 still deferred (user-side secret)                                                                          |
| juniper-data-client       | ✅        | ✅                   | —                                                                                                                                               |
| **juniper-cascor-client** | ✅        | ✅                   | — (V22 fully resolved by `9741e18`)                                                                                                             |
| juniper-cascor-worker     | ✅        | ✅                   | —                                                                                                                                               |
| juniper-deploy            | ✅        | ✅                   | — (trivy promoted to hard gate)                                                                                                                 |

### Greens

- **All 8 repos** have a green `security-scan.yml` except juniper-cascor.
  cascor's `security-scan.yml` failure was V20 (bandit skip-list drift —
  fixed `53e7134`); the `ci.yml` Security Scans gitleaks step was V30
  (false positives on conda lockfile build hashes / placeholder API keys
  in setup guides — fixed via `.gitleaks.toml` in `ab2694e`).
- **3 repos** have a fully green `ci.yml`: data-client, cascor-worker,
  deploy.
- **All 7 Python repos with CodeQL** have green CodeQL runs (CodeQL
  was already green from initial deployment; no shakedown findings).

### Reds

- **5 repos** have a red `ci.yml`: ml, canopy, cascor, data,
  cascor-client. Every red is traceable to an out-of-scope deferred
  finding (V11–V13, V19–V25, V27, V28). None of the reds are caused
  by the alignment work itself.

### Soft-fail → hard-gate promotions executed

- **juniper-deploy / `trivy-fs`**: promoted (`continue-on-error:
  true` removed in `c431fd1`). Two consecutive green runs of
  `security-scan.yml` confirmed.
- **All 7 Python repos / CodeQL**: implicitly promoted (no soft-fail
  flag was used; CodeQL findings flow to the Security tab, not the
  `required-checks` aggregator).

### Soft-fail → hard-gate promotions held

- **data-client / cascor-client / cascor-worker `integration-tests`**:
  held in soft-fail. The integration suites are currently empty in
  these repos so the job is a no-op (exit-code-5 → "skip"). Promoting
  to hard-gate now would lock in a green that doesn't actually
  exercise anything. Plan: keep the soft-fail until each repo has at
  least one real `@pytest.mark.integration` test.

---

## 10. Closeout — what to hand off

1. **Out-of-scope deferred findings** (V11–V13, V17–V20, V22–V25,
   V27, V28) — owners are the per-repo product teams. The findings
   doc is the canonical reference.
2. **Pending soft-fail → hard-gate promotion** for the
   `integration-tests` jobs in data-client / cascor-client /
   cascor-worker — promote when those repos have real integration
   tests in their suites.
3. **Remove `--ignore-vuln CVE-2026-3219`** when pip publishes a
   patched 26.x release. Search across the fleet:

   ```bash
   grep -rn "CVE-2026-3219" /home/pcalnon/Development/python/Juniper/*/.github/workflows/
   ```

   …and remove the flag from every match.
4. **Configure `CROSS_REPO_DISPATCH_TOKEN`** at the org or repo
   level (V17, V18). Until that secret exists, the
   `lockfile-update.yml` workflows on data and canopy will keep
   failing on initial-trigger.
5. **Triage the gitleaks findings on cascor-client** (V22). Either
   allowlist test fixtures via a `.gitleaks.toml` config or rotate
   any actually-committed credentials.

---

## Closed.

This document, together with the alignment plan + validation
roadmap + findings file, forms the complete record of the CI
normalization effort across the 8 active Juniper repos.
