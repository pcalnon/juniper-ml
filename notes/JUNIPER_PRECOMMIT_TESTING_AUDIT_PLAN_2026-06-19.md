# Juniper Ecosystem — Local Pre-commit & Testing Infrastructure Audit Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Date**: 2026-06-19
**Status**: **v1.1** — validated by 4 independent sub-agents (V1–V4) and corrected (see §11); pending owner review
**License**: MIT License

---

## 0. What this document is (and is not)

This is the **methodology + rubric** for auditing the *local* pre-commit checks and testing
infrastructure across the active Juniper repositories. It defines **how** the audit is run,
**what** is measured, **how findings are evidenced**, and **how the audit itself is validated**
against hallucination. It is *not* the audit report — execution happens after this plan is approved.

This plan was subjected to **independent multi-agent validation** (§9) on 2026-06-19; §11 records
every finding and the correction applied. The validation caught real factual errors in the draft
baseline (chiefly: ground truth had drifted **same-day** under concurrent sessions) and an unsafe
dynamic-execution protocol — both fixed below.

**Deliverable scope (default, confirm OQ-1):** a findings **report + prioritized remediation backlog**.
**No fixes are applied** by this audit. Remediation is a ranked backlog for separate PRs (§7).

---

## 1. Scope

### 1.1 Repositories in scope (9)

Recon snapshot **as of 2026-06-19** (point-in-time — see the drift caveat in §2). Re-derived with
fresh evidence in P0; collectors trust none of this table verbatim.

| # | Repo | Last commit (2026-) | pre-commit cfg? | Test surface | Notes |
|---|------|--------------------|-----------------|--------------|-------|
| 1 | `juniper-canopy` | 06-16 | ✅ | yes | Dash/Playwright UI tests (loop-leak class) |
| 2 | `juniper-cascor` | 06-17 | ✅ | yes | backend; **3×** `run_tests.bash` (`src/tests/`, `src/tests/scripts/`, `util/`); torch |
| 3 | `juniper-cascor-client` | 05-29 | ✅ | yes | HTTP/WS client |
| 4 | `juniper-cascor-worker` | 06-15 | ✅ | yes | distributed worker; torch |
| 5 | `juniper-data` | 06-19 | ✅ | yes | FastAPI service; **ruff** stack |
| 6 | `juniper-data-client` | 06-15 | ✅ | yes | HTTP client |
| 7 | `juniper-deploy` | 06-15 | ✅ | **yes** (`pyproject.toml` + `tests/` + `Dockerfile.test` + `requirements-test.txt`) | Docker orchestration; non-Python-lint profile |
| 8 | `juniper-ml` | 06-19 | ✅ | yes | meta-package + 6 internal sub-packages |
| 9 | `juniper-recurrence` | 06-19 | ❌ **none** | yes | **current with origin (HEAD 2fd2b81 #27, 0/0)**; **3 sub-packages** (app, client, model) |

### 1.2 Audit units (granularity = per-package, per owner decision)

- **Pre-commit checks** → audited per **git repository** (one config governs the repo).
  8 repos have a config; **`juniper-recurrence` has none** (a finding — §C5; note it also has **no root
  `pyproject.toml`**, so root-level governance is wholly absent).
- **Testing infrastructure** → audited per **package** (`pyproject.toml` + `tests/`):
  - 8 repo-level packages (incl. `juniper-deploy`, which **does** have a suite).
  - **6 internal sub-packages of `juniper-ml`** sharing its single root pre-commit config:
    `juniper-ci-tools`, `juniper-config-tools`, `juniper-doc-tools`, `juniper-model-core`,
    `juniper-observability`, `juniper-service-core`.
  - **3 sub-packages of `juniper-recurrence`**: `juniper-recurrence` (app), `juniper-recurrence-client`,
    `juniper-recurrence-model` — each with its own `pyproject.toml` + `tests/`.
  - → **~17 distinct test surfaces** (exact count finalized in P0).

### 1.3 Out of scope

- **`juniper-slacker`** — excluded (owner decision): zero commits (`git log` → exit 128, unborn `main`),
  no `pyproject.toml` / tests / pre-commit / `AGENTS.md`. A single "pre-project, non-compliant" line in
  D1 (OQ-3); not scored.
- **`juniper-legacy`** — no top-level git repo (contains nested legacy git repos); out of scope.
- **CI internals** beyond local↔CI parity (§A7/§B12/§C7/§C8).
- **Applying fixes** — backlog only.

### 1.4 Verify depth = **hybrid** (owner decision), with a realistic dynamic fraction

Static review for **every** unit; **dynamic** verification only where a healthy env exists. Per §B11
discovery, only **canopy, cascor, data** document an env, and ~6/9 repos document none — so dynamic
coverage is structurally a minority. Mitigations: (a) a **default audit env** for env-agnostic
pure-Python packages (clients, ml sub-packages, doc/ci/config-tools) so they are still run; (b) the
rubric does **not** penalize a statically-correct config for lacking dynamic evidence — static-correct
reaches **2**; dynamic-clean + parity is required only for **3** (§4). Genuinely broken/torch-gated
envs yield `NOT VERIFIED — <reason>`, never a guess (§8).

---

## 2. Recon baseline — POINT-IN-TIME, re-derived in P0

> **Drift caveat (load-bearing).** This baseline is a 2026-06-19 snapshot. Ground truth **moves
> same-day**: `juniper-recurrence` advanced from a model-only checkout to 3 sub-packages *during this
> session* (concurrent Claude sessions actively commit to these repos). Therefore **every fact in §2 is
> a recon hypothesis, re-confirmed with fresh evidence in P0** (§8.10). Collectors cite their own
> freshly-captured evidence, never this section.

Verified structural facts (this session): 10 git repos under `…/Juniper/`; 9 in scope. 8
`.pre-commit-config.yaml` present; **recurrence + slacker have none**. **No `pytest.ini` / `tox.ini` /
`noxfile.py` anywhere** → pytest config lives in each `pyproject.toml`. `juniper-ml` sub-packages =
6 (named above); `juniper-recurrence` sub-packages = 3.

**Conda envs (verified `ls /opt/miniforge3/envs/` + `conda env list`):** the documented CLAUDE.md map
(`JuniperCanopy`/`JuniperCascor`/`JuniperData`) is **stale** — bare names are `*-DEPRECATED`; live envs
are **`JuniperCanopy1`**, **`JuniperCascor1`** (currently active), **`JuniperData`**, plus
`JuniperCassandra`. Evidence-based starting map (confirm in P0): canopy→`JuniperCanopy1`;
cascor & cascor-worker→`JuniperCascor1`; data→`JuniperData`; clients/ml/deploy/recurrence→no documented
env (run in the default audit env). **The stale map is itself a finding (§C3).**

### 2.1 Two fully-read configs proving real variation (V1-confirmed, exact)

Directly read this session (V1 independently re-derived and **CONFIRMED all** line refs):

| Aspect | `juniper-ml/.pre-commit-config.yaml` | `juniper-data/.pre-commit-config.yaml` |
|--------|--------------------------------------|----------------------------------------|
| `pre-commit-hooks` rev | **v4.6.0** (L63) | **v6.0.0** (L56) → **version drift** |
| Lint/format | black 26.3.1 + isort 8.0.1 + flake8 7.1.1 + mypy v1.13.0 | ruff v0.15.2 (`ruff`+`ruff-format`) + mypy v1.13.0 |
| Python scope | `^(scripts\|tests)/.*\.py$` | `^juniper_data/.*\.py$` (+ test split) |
| Coverage gate | **none** (pyproject L132-137: no `fail_under`, "intentional") | `coverage-check` local hook, `stages:[pre-push]`, 85%/80% |
| Extra guards | `no-unencrypted-env` | `+ruff-async-audit` (`--select ASYNC`, `stages:[pre-commit,manual]`), `require-requirements-lock` |
| doc-links dep | `juniper-doc-tools>=0.1.1,<0.2.0` (L214) | `juniper-doc-tools>=0.1.1,<0.2.0` (L196) — consistent |

`juniper-ml/pyproject.toml`: `[tool.pytest.ini_options] addopts=["-p","no:dash","-p","no:playwright"]`
(L100-103); `[tool.coverage.report]` has **no `fail_under`** (L132-137). Both configs pass
`pre-commit validate-config`. These prove the audit will find real drift (versions, stacks, coverage
gates, hook stages, guards) — they are *examples from two repos*; the full inventory is collected in P1.

---

## 3. Audit dimensions (the rubric)

> Incident-/best-practice-derived checks are **hypotheses to verify per unit**, not asserted facts.
> The only confirmed instance carried as fact is the juniper-ml autoload guard (§2.1).

### Area A — Pre-commit checks (unit: git repo)

| ID | Dimension | Key checks (beyond presence) | Mode |
|----|-----------|------------------------------|------|
| A1 | Config presence & validity | parses; `minimum_pre_commit_version` set **and** ≥ what its `stages:` syntax requires | S/D |
| A2 | **Install & stage wiring** | installed `.git/hooks/*` vs config `stages:`; **`default_install_hook_types`/`default_stages` set?** (root cause: data's `pre-push` coverage gate never fires after a plain `pre-commit install`); `manual` hooks reachable; `commit-msg` stage | S |
| A3 | Hook inventory & pinning | every remote `rev` pin; **local-hook `additional_dependencies` pin tightness** (the loose `juniper-doc-tools>=0.1.1,<0.2.0` re-resolves; no `rev`) | S |
| A4 | Tool-stack consistency | black/isort/flake8 vs ruff. **"Intentional" iff** documented in AGENTS.md **and** line-length/ignore-set equivalent across stacks | S/P |
| A5 | File-surface coverage | `files`/`types`/`exclude` precision; **does top-level `exclude` exempt security hooks** (`detect-private-key`, large-file, `no-unencrypted-env`) from `notes/`, `resources/`, `images/`? (secret-leak class) | S |
| A6 | Security hooks | bandit (+skips justified), detect-private-key, `no-unencrypted-env`, async-audit; **pre-commit-time content secret scanning beyond `detect-private-key`** (gitleaks/detect-secrets) — currently CI-only? | S |
| A7 | Local↔CI parity (pre-commit) | fixed tuple per §P3; **CI workflow-pinned rev vs repo config rev**; distinguish intentional CI `SKIP:` (e.g. cascor `SKIP: pytest-unit,coverage-gate`) from accidental drift | P |
| A8 | Hook health (dynamic) | `pre-commit run --all-files` in a throwaway worktree; **autofix diff = PASS-with-noise, not FAIL** | D |
| A9 | Autoupdate currency & **pin-break risk** | staleness vs upstream; `autoupdate_schedule`; does a monthly autoupdate bump (e.g. v4.6.0→v6.0.0) get CI-gated before merge? `autofix_prs:false` paired with review | S |
| A10 | Performance & DX | slow/`always_run` hooks; `fail_fast` policy | D |
| A11 | Incident-derived guards (verify) | `no-unencrypted-env`, `require-requirements-lock`, async-audit, gitleaks-node24 — which repos, consistently applied where relevant | S |
| A12 | File-header compliance | documented file-header schema present (per CLAUDE.md/AGENTS.md convention) | S |

### Area B — Testing infrastructure (unit: package)

| ID | Dimension | Key checks | Mode |
|----|-----------|------------|------|
| B1 | Framework & config location | pytest vs unittest; config in `pyproject`; no stray `pytest.ini`; **`--strict-config`** | S |
| B2 | Discovery & layout | `testpaths`; tree; naming. (verified safely via `pytest --co -q`) | S/D |
| B3 | Markers | registered + **`--strict-markers`**; **usage (`@pytest.mark.*`) vs registration** (dead/typo); **vs the CI `-m` expression** (the `-m "unit or integration"`-skips-path-suites class) | S/D |
| B4 | Coverage config & enforcement | `fail_under` value; **is it enforced by any *locally-runnable* command?** (no repo has `--cov` in `addopts` → `fail_under` may be inert locally); **equals CI `--cov-fail-under`?**; **`parallel`/`combine` coherent with xdist?**; branch; pytest-cov vs `coverage run` divergence | S/D |
| B5 | **Async test config** | `asyncio_mode` set & consistent with `pytest-asyncio` usage (strict default → undecorated `async def test_` silently never awaited) | S |
| B6 | **Warnings policy** | `filterwarnings`/`-W error` baseline; per-ignore justification (over-broad `ignore::DeprecationWarning:*` masks real removals) | S |
| B7 | Isolation & determinism | order-independence (`pytest-randomly`); **seed/determinism** (`torch/numpy` seeds, `PYTHONHASHSEED`) for the golden/snapshot tests; **socket/network isolation** (`pytest-socket`/mocks enforced for the unit lane); `tmp_path` vs hardcoded `/tmp`; fixtures (prometheus reset, singleton/lru_cache, `.env`-leak) | S/D |
| B8 | Plugin-autoload defenses (verify) | `-p no:dash` / `-p no:playwright` / `PYTEST_DISABLE_PLUGIN_AUTOLOAD` (confirmed present in juniper-ml) | S |
| B9 | Process hygiene (verify) | multiprocessing/forkserver orphan reaping; clean exit-flush | S/D |
| B10 | Invocation & doc accuracy | AGENTS.md command actually collects/runs (`--co` first); `run_tests*.bash` (cascor has 3) | S/D |
| B11 | Env requirements & health | **discover env empirically** (`conda env list` + import probe), NOT the stale CLAUDE.md map; record env identity (name, py version, key tool versions); default audit env for env-agnostic packages | S/D |
| B12 | Local↔CI parity (test lane) | fixed tuple per §P3 | P |
| B13 | Flakiness & known issues | xfail/skip inventory + reasons + **`xfail_strict`**; segfault/loop-leak history; silently-skipped suites | S/D |
| B14 | Speed & bounded execution | `--co` first; `timeout` + `--maxfail`; torch cost; UI suites excluded from auto-run | D |
| B15 | Test-surface coverage | packages with no tests; does each package's CI actually run its tests? (deploy **has** tests — verify CI runs them) | S/P |

### Area C — Cross-cutting / ecosystem consistency

| ID | Dimension |
|----|-----------|
| C1 | Inter-repo **drift matrix** (hook versions, stacks, markers, thresholds, async/warnings posture) |
| C2 | Shared-tooling pin consistency (`juniper-doc-tools` / `juniper-ci-tools`) |
| C3 | Documentation accuracy — incl. **stale conda-env map** (CLAUDE.md names deprecated envs) and AGENTS.md test-command accuracy |
| C4 | Monorepo governance — root pre-commit coverage of sub-package Python (ml ×6, recurrence ×3); per-package CI/publish workflows |
| C5 | New-repo gaps — recurrence has **no root pre-commit AND no root pyproject**; define a **target compliance profile** (clone ml's root-config-over-subpackages pattern); recurrence has **no JR-ID shortcode** |
| C6 | Checkout integrity — local vs `origin/main` divergence (capture HEAD + `origin/main` SHAs at the instant); concurrent-session race awareness; orphaned editable installs |
| C7 | **CI matrix parity** — python-version (3.12/3.13/3.14) & OS matrix: a local single-version/Linux run **cannot certify the matrix** → recorded as a parity gap, not a pass |
| C8 | **CI install-mode parity** — editable (`-e`) vs wheel vs `git+…@main`: does CI install as the dev does **and** as it ships? (wheel-only failures: missing `MANIFEST.in`/package-data) |

---

## 4. Scoring model (per-dimension predicates — not prose)

General rule: **2 = compliant (static evidence)**; **3 = "2" + clean dynamic run + at CI-parity**;
**1 = present-but-drifted/partial**; **0 = absent/broken**; **N/A = does not apply** (recorded with
reason, never silently skipped). A static-only dimension caps at **2** with `verify=static` (it is
*not* penalized to 1 merely for lacking a dynamic run). **Autofix-hook diffs count as PASS-with-noise,
not FAIL.** "Best practice" is defined **only** by the §6 enumerated sources — no auditor's personal
standard. "No test suite" = **0 for B15** (real gap) but **N/A for B3/B5/B7/B14** (nothing to mark).

Representative per-dimension predicates (the full table is finalized as a one-time **calibration
artifact** all collectors share before Wave 1, so scoring is produced identically):

| Dim | 0 | 1 | 2 | 3 |
|-----|---|---|---|---|
| A3 pinning | unpinned/floating | >3 minors behind or local-hook loose-pinned | all remote `rev` pinned | +within 1 minor of latest **and** local-hook deps tightly bounded |
| A9 currency | unpinned | >3 minors behind | within ~2 minors + `autoupdate_schedule` set | within 1 minor + autoupdate CI-gated |
| B4 coverage | no coverage config | `fail_under` set but **inert locally** or ≠ CI | `fail_under` enforced locally **and** = CI | + parallel/combine coherent + dynamically verified |
| B5 async | `pytest-asyncio` dep + `asyncio_mode` unset + undecorated async tests | mode set but inconsistent w/ usage | mode set, consistent | + dynamically collected with 0 "never awaited" |
| A8 hook health | hooks error | some hooks fail (non-autofix) | config valid, static-clean | `--all-files` clean (autofix-noise OK) in worktree |

Rollups: per-unit (area means + min), per-repo, ecosystem.

---

## 5. Methodology (execution — after approval)

**Waves (V4-08), with an owner checkpoint between each:**
- **Wave 1** — static + parity for all 9 repos / ~17 surfaces (cheap, parallel).
- **Wave 2** — dynamic only for healthy-env repos (canopy/cascor/data + env-agnostic pure-Python pkgs in the default audit env), worktree + timeout bounded.
- **Wave 3** — bounded adversarial verification (§P5).

**P0 — Prep & ground-truth manifest.** Per repo: capture `git rev-parse HEAD` **and** `origin/main`
SHAs + branch + dirty state + `rev-list --left-right --count origin/main...HEAD` (instant snapshot;
`git fetch` updates remote-tracking refs only, working tree untouched — acceptable per OQ-2; skip/flag
if a concurrent session is mid-operation). **Discover conda envs empirically** (`conda env list` +
`python -V`/import probes); bind repo→env by evidence; treat `*-DEPRECATED` as out-of-bounds; record
doc-vs-reality drift (§C3). **Re-emit every §2 fact with fresh evidence — trust nothing from §2.**

**P1 — Static collection.** Per unit, read `.pre-commit-config.yaml`, `pyproject [tool.*]`,
`.github/workflows/*.yml`, `AGENTS.md`, `run_tests*.bash`, conftest/fixtures → evidence table: **every
claim → `file:line`**.

**P2 — Dynamic verification (env-gated, genuinely non-mutating).** **All dynamic execution runs in a
throwaway worktree, never the live checkout** (V4-01): `git worktree add --detach <scratch>/audit-<repo> HEAD`
→ run there → `git worktree remove --force`. This is lossless (live tree untouched), always gives a
clean tree, and makes "revert" a no-op. If editable-install path-coupling makes a worktree infeasible,
fall back to copy-to-tmp; **never in-place `git checkout -- .` on a live repo.** Inside the worktree:
1. **Collect-only first** (`pytest --co -q`) — satisfies B1/B2/B3 discovery safely.
2. Full run only under `timeout <N>s` + `--maxfail` + autoload guard (`-p no:dash -p no:playwright` /
   `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`); **exclude Playwright/UI suites** from auto-run (record
   `NOT VERIFIED — UI/loop-leak class, run manually`).
3. `pre-commit run --all-files` (autofix-noise = PASS).
4. After each run, invoke `util/reap_pytest_orphans.bash` (dry-run then live); record orphans as B9
   evidence. Record env identity with every result. Broken/absent env → `NOT VERIFIED — <reason>`.

**P3 — Parity mapping (fixed field tuple).** Per lane, compare the tuple
`{hooks_set, per_hook_rev, per_hook_args, stages_invoked, test_command, marker_expr, testpaths/--ignore,
coverage_fail_under, python_version, env}`; parity score = matching/total; any version or selection
mismatch auto-flags; cite the CI job name + step line. Distinguish **intentional CI `SKIP:`** from drift.
Record python-version/OS matrix coverage as a parity **gap** (local can't certify the matrix — §C7) and
install-mode (editable/wheel/git-main — §C8).

**P4 — Scoring & synthesis (mechanical).** Apply §4 predicates; **merge by `(repo, dimension_id)`**;
**C1 = pivot of scores**; **backlog = filter score ≤ 1, sorted by severity × effort** (D3).

**P5 — Independent adversarial verification of findings.** Re-verify **all high-severity** findings +
a **fixed random sample (20%, seed logged per §8.8)** of score-0/1 findings. The refuter receives the
**claim + repo only** (not the original agent's evidence trail) and must **re-derive** evidence from
scratch; a finding survives only if independently-derived evidence matches (§8.6). The two-source rule
(§8.7) requires evidence of **different classes** (static config + dynamic behavior), not two agents
reading the same line. Residual conflicts → owner is final arbiter.

### 5.1 Execution shape (multi-agent) + frozen output contract

Per-repo collection fans out: **one collector agent per repo** (parallel), each emitting the **frozen
contract** — a Markdown table + embedded JSON with fixed keys per dimension:
`{repo, dimension_id, score, verify_mode ∈ {static,dynamic,parity,not_verified}, evidence:[{file,line}|{cmd,exit,snippet}], not_verified_reason?, confidence}`.
Collectors receive the **exact commands** to run and the **shared §4 predicate table**, so output is
machine-mergeable and scores are produced identically. Read-only tools + the §P2 worktree protocol only.

### 5.2 Tooling placement

Helper scripts → **`juniper-ml/util/ad-hoc/`** (never `/tmp/` for source). Transient JSON dumps may use
`/tmp/` as scratch only.

---

## 6. Best-practices & documented-requirements basis (sole definition of "best practice")

- **pre-commit.com**: pin `rev`; `pre-commit autoupdate`; run in CI; hook `stages` &
  `default_install_hook_types`.
- **pytest**: `conftest`/`testpaths` layout; **`--strict-markers`/`--strict-config`**; `asyncio_mode`;
  `filterwarnings`; `xfail_strict`; order-independence; seed/determinism.
- **coverage.py**: `fail_under`; `branch`; `parallel`+`combine`.
- **Documented Juniper conventions** (`CLAUDE.md` / per-repo `AGENTS.md`): line-length **512 for all
  linters incl. markdownlint**; black+isort (ruff for data); pytest markers; **80% coverage threshold
  *(verify per repo — ml exempts itself; data is 85%/80% — so it is NOT universal; treat the number as
  a claim per §8.2)***; extended log levels; **file-header schema** (scored at A12);
  **script placement** (`util/`, never `/tmp/`); worktree & handoff procedures.
- **Hard-won incident-derived checks** (hypotheses to verify; documented in `notes/`/prior PRs):
  autoload-SIGSEGV guard; orphan reaping; `.env` test-leak; Playwright loop-leak; doc/ci-tools pin
  drift; local↔CI path-scope mismatch; orphaned editable installs; stale env map.

---

## 7. Deliverables

| ID | Artifact | Location |
|----|----------|----------|
| D1 | **Master audit report** — exec summary, C1 drift matrix, per-unit scorecards, findings register (evidence-cited) | `notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_REPORT_2026-06-19.md` |
| D2 | **Ground-truth manifest** — repo states (HEAD + origin SHAs, divergence) + discovered env identities | report appendix or `util/ad-hoc/*.json` |
| D3 | **Prioritized remediation backlog** — finding, severity, effort, repos, action (**no fixes applied**) | report section |
| D4 | **Evidence/provenance log** — every claim → evidence + verify method + verifier id + confidence; sampling/seed logged | report appendix |

**Backlog conventions (V3-01/02):** cite a `JR-<REPO>-<AREA>-<NNN>` ID **only where a tracked
requirement applies** — valid areas here are `TEST`/`TOOL`/`DOC`, and only the **8 shortcoded repos**
(`ml, can, cas, dat, ccl, dep, cwk, dcl`) have IDs; **`juniper-recurrence` has no shortcode** and most
gaps are net-new → file as new findings with **no ID**. Use the verb table (`Closes`/`Partially
closes`/`References`/`Supersedes`); never grep `id_assignments.yaml` for content; link to `by-area/*.md`
anchors. **Remediation PRs follow the worktree procedure** (one worktree per affected repo, centralized
`…/Juniper/worktrees/`, **PR-to-main, never direct commit**, cross-repo changes merged in dependency
order) and carry the `## Requirements` PR section. The audit *itself* is read-only and runs in the
current worktree (no new worktrees needed for collection; throwaway worktrees only for dynamic runs).

---

## 8. Anti-hallucination protocol

1. **Evidence-or-silence.** Every assertion cites `file:line` or captured `cmd + exit + snippet`. No
   claim from memory/inference.
2. **Docs are claims, not evidence.** CLAUDE.md/AGENTS.md/README verified against the repo (the stale
   env map is the canonical example).
3. **`NOT VERIFIED` is first-class** — recorded with reason, never back-filled.
4. **Local-checkout vs origin** never conflated; both SHAs captured.
5. **Env attribution** on every dynamic result (name, py version, tool versions).
6. **Independent adversarial re-verification** — refuter gets **claim + repo only**, re-derives
   evidence; survives only if independently matched.
7. **Two-source rule (high severity)** — corroboration from **different evidence classes** (config +
   behavior), not two readers of one line.
8. **No silent truncation** — any bound (skipped repo, sample size + seed) logged in D4.
9. **Non-mutating** — throwaway-worktree execution; no commits; nothing written to live repos.
10. **§2 baseline is a snapshot** — drifts same-day under concurrent sessions; re-derived in P0;
    collectors trust none of it.

---

## 9. Multi-agent validation of THIS plan — **COMPLETED 2026-06-19**

Four independent agents (no cross-talk, adversarial, read-only). Verdicts:

| Agent | Lens | Verdict | Headline catch |
|-------|------|---------|----------------|
| V1 | Hallucination/fact-check | facts-need-correction | recurrence mischaracterized (stale recon); 3 stale dates; cascor 3 not 2 run_tests |
| V2 | Completeness/best-practice | dimensions-have-gaps | coverage `fail_under` inert locally; `asyncio_mode` unset; top-level `exclude` exempts security hooks |
| V3 | Convention alignment | needs-alignment | JR-ID framing wrong (8 shortcodes, recurrence has none); worktree path for remediation; stale env map |
| V4 | Methodology/feasibility | methodology-needs-fixes | **non-mutating protocol unsafe** → mandate throwaway worktrees; stale env map; bound the scope into waves |

The same four-lens structure is reused in P5 to validate the **findings**. §11 logs every disposition.

---

## 10. Risks & constraints

| Risk | Mitigation |
|------|------------|
| **Live-repo corruption** during "non-mutating" audit (autofix hooks rewrite files) | Throwaway-worktree execution for ALL dynamic runs (§P2); never in-place revert |
| **Stale env map** → false `NOT VERIFIED` | Empirical env discovery in P0; `*-DEPRECATED` excluded; map drift recorded as §C3 finding |
| ~6/9 repos have no documented env → hybrid skews static | Default audit env for pure-Python pkgs; rubric doesn't penalize static-only (§1.4/§4) |
| torch / SIGSEGV / orphan / loop-leak / ~15s import | `--co` first; `timeout`+`--maxfail`+autoload guard; reap orphans; UI suites excluded |
| **Same-day ground-truth drift** (concurrent sessions) | §2 re-derived in P0; instant SHA capture; concurrent-session race flagged |
| Scope (9 × ~17 × ~35 dims × modes) | Wave staging + frozen schema + bounded P5 (all-high-sev + 20% of 0/1) + owner checkpoints |
| Scoring subjectivity | Per-dimension predicate table + shared calibration artifact before Wave 1 |

## 11. Validation corrections log (V1–V4 → dispositions)

**Accepted — baseline facts (V1/V4):** stale dates fixed (data/ml/recurrence → 06-19); **recurrence
rewritten** (current 0/0, 3 sub-packages, no pre-commit, no root pyproject); cascor `run_tests.bash`
**3 not 2**; deploy **has** a test suite; juniper-legacy reworded; §2 demoted to re-derive-in-P0
snapshot with explicit same-day-drift caveat (§8.10).

**Accepted — methodology/safety (V4):** V4-01 **throwaway-worktree execution** replaces in-place revert
(critical); V4-02 **empirical env discovery** replaces the stale map; V4-03 default audit env + rubric
decoupling; V4-04 bounded execution (`--co`, `timeout`, `--maxfail`, reap, UI-excluded); V4-05
per-dimension predicates + calibration artifact + 2-vs-3 rule + N/A-vs-0 rule; V4-06 frozen output
contract + mechanical synthesis; V4-07 fixed parity tuple; V4-08 wave staging + bounded P5; V4-10 git
fetch reworded + SHA capture; V4-11 folded into V4-01; V4-12 refuter independence + different-class
two-source rule.

**Accepted — completeness (V2):** added B5 async config, B6 warnings policy, A5 security-exclude
interaction, A6 content secret-scanning, A2 `default_install_hook_types`, A3 local-hook pin, A9
pin-break; folded `--strict-markers/--strict-config` (B1/B3), `pytest-randomly`/seed/socket/`tmp_path`
(B7), `xfail_strict` (B13), parallel-coverage & pytest-cov-vs-coverage-run & CI-`fail_under` divergence
(B4), marker-usage-vs-registration (B3), C7 matrix parity, C8 install-mode parity, A10 `fail_fast`, A2
`commit-msg`. Dimension sharpenings (A4 "intentional" rule; A8 autofix-as-noise; deploy non-Python
profile; recurrence target profile) accepted.

**Accepted — conventions (V3):** D3 JR-ID reframed (8 shortcodes, recurrence none, net-new = no ID,
verb table, no-grep caution); remediation worktree/PR-to-main note + `## Requirements` PR section;
markdownlint added to the 512 basis; A12 file-header dimension added; `JuniperCascor1`/`JuniperCanopy1`
live-env correction (§C3/§B11).

**Partially accepted:** V4-05 calibration — adopted a shared predicate **artifact** (one-time, before
Wave 1) but **not** a formal inter-rater agreement study (overhead vs value). V2's ~26 raw items —
**consolidated** into clustered dimensions to respect V4-08's scope warning rather than added 1:1.

**Rejected:** none material — all findings were evidence-backed and correct or improving. (The only
trims were to avoid rubric bloat, recorded above.)

---

## Appendix A — Owner decisions (this session)

1. **Repo scope:** 9 (8 documented + `juniper-recurrence`); exclude `juniper-slacker`.
2. **Verify depth:** hybrid (static all + dynamic where env healthy; realistic minority-dynamic — §1.4).
3. **Granularity:** per-package surfaces (~17); pre-commit per repo.
4. **Local↔CI parity:** included (A7/B12/C7/C8).
5. **Deliverable (default, confirm OQ-1):** report + prioritized backlog; no fixes.

**Evidence-based env map (confirm P0):** canopy→`JuniperCanopy1`; cascor & cascor-worker→`JuniperCascor1`;
data→`JuniperData`; clients/ml/deploy/recurrence→default audit env. `*-DEPRECATED` out of bounds.

## Appendix B — Open questions

- OQ-1: Deliverable depth = backlog only (vs. also staging draft fix PRs)?
- OQ-2: `git fetch` (remote-tracking refs only) per repo in P0 OK? (Proposed: yes.)
- OQ-3: Include `juniper-slacker` as a one-line "pre-project, non-compliant" note in D1? (Proposed: yes.)
- OQ-4: D2/D4 as committed JSON under `util/ad-hoc/`, or report appendices only?
- OQ-5 (new): Default audit env for env-agnostic pure-Python packages — dedicated `JuniperAudit` env, or `base`/JuniperData?
- OQ-6 (new): May the audit create throwaway `git worktree`s (auto-removed) for dynamic runs? (Proposed: yes — it is the safe path.)
