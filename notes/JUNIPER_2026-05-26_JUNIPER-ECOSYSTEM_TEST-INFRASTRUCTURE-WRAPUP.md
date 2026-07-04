# Test Infrastructure Investigation Wrap-Up — 2026-05-26

**Scope**: Two interleaved investigations, 2026-05-24 → 2026-05-26.

1. Scheduled-nightly `Slow Unit Tests` failing every night since 2026-05-04 (cascor).
2. 19 unit-test failures locally with the user's `pytest --slow --integration --run-performance` command (cascor).

Both root-caused, fixed, and shipped. This doc itemizes what was done, what's still open, what's latent, and what to do next.

---

## 1. Shipped

| Date | Repo | PR | Merge SHA | What it does |
|---|---|---|---|---|
| 2026-05-24 | juniper-cascor | [#303](https://github.com/pcalnon/juniper-cascor/pull/303) | `0a33ee3` | Drop `--cov=src` from `scheduled-tests.yml` `slow-unit-tests` step. Coverage gate (80%) is unsatisfiable over a 10-test slice (~34% coverage). Adds workflow-lint regression test `src/tests/unit/test_workflow_coverage_gate.py`. |
| 2026-05-26 | juniper-cascor | [#309](https://github.com/pcalnon/juniper-cascor/pull/309) | `6bb76c2` | Add session-scoped autouse fixture `_disable_settings_env_file_for_tests` in `src/tests/conftest.py`. Sets `Settings.model_config["env_file"] = None` for the test session so pydantic-settings stops reading the developer's local `.env`. Adds `src/tests/unit/test_env_file_isolation.py` regression test (2 cases). |
| 2026-05-26 | juniper-canopy | [#325](https://github.com/pcalnon/juniper-canopy/pull/325) | `966ea72` | Pre-emptive port of cascor #309. Same fixture pattern, canopy import paths (`from settings import ...`). 2 regression tests. |
| 2026-05-26 | juniper-data | [#153](https://github.com/pcalnon/juniper-data/pull/153) | `a216ce2` | Pre-emptive port of cascor #309. Same fixture pattern, data import paths (`from juniper_data.api.settings import ...`). 2 regression tests. |

---

## 2. Verified gaps closed

### 2.1 Scheduled-nightly `Slow Unit Tests` (cascor)

- 2026-05-04 → 2026-05-24: 21 consecutive nightly failures.
- After PR #303: 2026-05-25 and 2026-05-26 nightlies both `success`. ✅

### 2.2 Developer-local `.env` leaking into tests (ecosystem)

- Before: 18 cascor unit tests fail locally when `~/Development/python/Juniper/juniper-cascor/.env` contains `JUNIPER_DATA_URL=...`. CI never reproduces.
- After cascor #309: full local `pytest --slow --integration --run-performance` run from cascor main = `3958 passed, 11 skipped, 0 failed`. ✅
- canopy + data have the same vulnerability shape (different victims) but no test was actively failing — pre-emptive fix in both. Regression test in each repo pins the contract.

### 2.3 Stale cascor editable install (1 of 19)

- Was the cause of `test_phase_2e_topology_correlation_phase.py::TestBugCC04VersionSingleSource::test_version_matches_pyproject` failing (`importlib version '0.4.0' disagrees with pyproject '0.5.0'`).
- Resolved by `pip install -e ".[all]" --no-deps` from the cascor **main** repo (not a transient worktree), which re-points the editable install at the stable path. ✅
- **NOT a code bug.** See memory `project_stale_editable_install_after_worktree_cleanup` for the recurring pattern.

---

## 3. Remaining gaps

### 3.1 `juniper-data` editable install in `JuniperCascor1` is stale (HIGH ergonomic impact, LOW risk)

- `pip show juniper-data` reports version 0.6.0 installed, `Editable project location: /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--cln-jd-03-lazy-app-factory-2026-05-20--20260520-0439--d987adf0` — a worktree that no longer exists.
- `python -c "import juniper_data"` fails with `ModuleNotFoundError`.
- Consequence: 11 cascor e2e tests (`src/tests/integration/test_juniper_data_e2e.py`) are silently skipped with the `juniper-data package not installed` message — they could run but the import-check at fixture setup says they can't.
- **Fix**: `pip install -e /home/pcalnon/Development/python/Juniper/juniper-data --no-deps` from any shell with `JuniperCascor1` active. One command.
- Trigger to re-test: after the reinstall, re-run `pytest src/tests/integration/test_juniper_data_e2e.py --integration` from cascor main. If any of the 11 currently-skipped tests fail when actually executed, that's a *new* gap to track.

### 3.2 `.env.example` ↔ runtime-default drift (LOW priority, latent docs bug)

- cascor's `.env.example` does **not** define `JUNIPER_DATA_URL` at all, but the user's hand-edited local `.env` contained `JUNIPER_DATA_URL="http://127.0.0.1:8100"`. The example is not the source of the developer's pollution — they added it manually.
- canopy `.env.example` defines `JUNIPER_CANOPY_JUNIPER_DATA_URL=http://localhost:8100` (canonical localhost, matches code default).
- data `.env.example` defines `JUNIPER_DATA_HOST=0.0.0.0` etc. (production-style, intentionally differs from code defaults so a `cp .env.example .env` produces a runnable dev config).
- **No active drift bug.** But there's no automated check that `.env.example`'s values stay consistent with code defaults or documented AGENTS.md defaults. A future drift would only surface when a developer hits a confused failure mode.
- **Optional follow-up**: a lint that scans `.env.example` and verifies each commented variable either has no value (just the name) or matches the documented AGENTS.md default. Defer until a real drift incident.

### 3.3 cascor pytest summary-line truncation under stdout-to-file (LOW priority, cosmetic)

- Memory `project_cascor_pytest_summary_truncation_2026-05-03` claims this was RESOLVED by cascor #205 (explicit `sys.stdout.flush()` before `os._exit(0)` in `pytest_unconfigure`).
- Observed in this investigation: when `pytest ... 2>&1 > /tmp/file.txt`, the trailing summary line is still missing from the captured file. Exit code is correct, so all assertions about pass/fail still work.
- The fix is in place but apparently doesn't catch all paths. Worth re-investigating the next time someone is bitten by it, not now.

### 3.4 `xfail` deterministic training resume (KNOWN, accepted)

- `src/tests/integration/test_comprehensive_serialization.py::TestDeterministicTrainingResume::test_deterministic_training_resume` is `xfail` with reason "Serialization does not yet fully preserve optimizer/random state for deterministic resume".
- Long-standing, intentional. No action proposed in this investigation.

---

## 4. Open issues / latent risks (monitor)

### 4.1 Stale editable install is the highest-recurrence local-env friction

Three distinct manifestations observed in this investigation:
- Cascor at v0.4.0 instead of v0.5.0 → version-test failure (2026-05-25).
- Cascor pointed at a deleted worktree from PR #303 cleanup → version-test failure (2026-05-26).
- juniper-data pointed at a deleted worktree from 2026-05-20 → 11 e2e tests skipped (2026-05-26).

Current mitigation = memory entry telling Claude/devs to `pip install -e <path> --no-deps`. No durable fix.

**Possible durable fixes (not implemented, awaiting trigger)**:
1. Add a post-worktree-cleanup hook that re-pins the editable install at the main repo path. Easy to add to `juniper-ml/util/worktree_cleanup.bash`. Single-line `pip install -e $MAIN_REPO --no-deps` after the prune.
2. Add a `make doctor` / `juniper-ml/util/check_editable_installs.bash` that scans all Juniper editable installs and reports those pointing at non-existent paths. Run periodically or as a pre-test hook.
3. Move the editable install from the worktree path to the main repo path as a convention.

### 4.2 Future Juniper services using pydantic-settings

If a new Juniper service is added that uses `pydantic_settings.BaseSettings` with `env_file=".env"`, it needs the same isolation fixture pattern. Currently no enforcement.

**Possible enforcement (not implemented, awaiting trigger)**:
- Add a juniper-ml lint test (similar to `tests/test_workflow_script_paths.py` pattern) that scans each Juniper repo's `conftest.py` for the `_disable_settings_env_file_for_tests` fixture when the repo's `settings.py` declares `env_file=".env"`. Deferred until a 4th pydantic-settings service exists or a leak is observed in a new repo.

### 4.3 Coverage gate ↔ partial-marker pytest invocation

cascor #303's regression test `src/tests/unit/test_workflow_coverage_gate.py` only scans **cascor's own** `.github/workflows/`. The same pattern (e.g. `pytest -m "unit and slow" --cov=src` failing the 80% gate) could exist in canopy/data/cascor-worker workflows. Not yet audited.

**Possible follow-up**: copy the lint to each repo's `tests/` (mirroring the per-repo ports of the .env-leak fixture), or move it to `juniper-ci-tools` as a shared console script.

---

## 5. Trigger-conditioned follow-ups

| Condition | Action |
|---|---|
| `juniper-data` editable install gets reinstalled in `JuniperCascor1` | Re-run `pytest src/tests/integration/test_juniper_data_e2e.py --integration` from cascor main. If any of the 11 currently-skipped tests fail when actually executed, file a new ticket. |
| A 4th Juniper repo adopts `pydantic_settings.BaseSettings` with `env_file=".env"` | Port the `_disable_settings_env_file_for_tests` fixture + `test_env_file_isolation.py` regression test from cascor/canopy/data. Pattern is identical except for the Settings import path. |
| Stale editable install bites a third time | Implement durable mitigation (option 1, 2, or 3 from §4.1). |
| Anyone hits an actual `.env.example` ↔ runtime-default drift | Implement the lint described in §3.2. |
| A workflow file is added to canopy/data/cascor-worker that runs `pytest --cov=src` with a partial marker filter | Port cascor's `test_workflow_coverage_gate.py` lint to that repo. |
| pytest summary-line truncation under stdout-to-file is re-observed and someone has time to investigate | Bisect what's still firing `os._exit` without flushing — the conftest fix from #205 covers the non-daemon-thread escape hatch but evidently not all paths. |

---

## 6. Memory entries created or updated

- **NEW**: `project_pydantic_settings_dotenv_test_leak_2026-05-25.md` — symptom signature, fix shape, per-repo status table (all 3 pydantic-settings repos fixed 2026-05-26; cascor-worker not vulnerable because it uses a dataclass + `WorkerConfig.from_env()`).
- **NEW INDEX LINE** in `MEMORY.md`.
- No updates to existing memories were needed — `project_stale_editable_install_after_worktree_cleanup` and the cascor pytest-related entries are still accurate.

---

## 7. Files of record

- cascor `src/tests/conftest.py::_disable_settings_env_file_for_tests` — canonical implementation.
- cascor `src/tests/unit/test_env_file_isolation.py` — canonical regression test.
- cascor `src/tests/unit/test_workflow_coverage_gate.py` — canonical workflow-lint regression test for the coverage-gate-on-partial-set pattern.
- canopy `src/tests/conftest.py` + `src/tests/unit/test_env_file_isolation.py` — port.
- data `juniper_data/tests/conftest.py` + `juniper_data/tests/unit/test_env_file_isolation.py` — port.

---

## 8. Worktrees remaining open

(As of writing.)

```
juniper-ml          .claude/worktrees/snoopy-stirring-fiddle  worktree-snoopy-stirring-fiddle
```

This is the juniper-ml worktree the wrap-up doc is being written from. All other investigation worktrees (cascor PR #303, cascor PR #309, canopy PR #325, data PR #153) have been removed and their branches deleted.
