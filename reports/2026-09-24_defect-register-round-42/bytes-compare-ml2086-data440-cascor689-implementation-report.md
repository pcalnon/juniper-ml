<!-- Archived verbatim 2026-09-24 from subagent a100243c3f4f5b4d4 of session bc31e993 (final message). -->

All three PRs are open, none is merged or armed, and each has green required checks.

## PR 1 — juniper-ml (as read back by `gh pr view`)
- **PR:** #2086, https://github.com/pcalnon/juniper-ml/pull/2086. OPEN, not draft, auto-merge null.
- **Head:** `4924ca98c069dc0bd2508c97fcf1da9e6442904e`, on base `df21367d`. The commit is GitHub-signed ("valid") and the trailer is its last paragraph.
- **Checks:** 28 success, 1 skipped, 5 neutral (Cursor). The PR now shows **BEHIND** because #2087 (docs only, none of my paths) merged after it. The ruleset needs an update-branch before merge, and that step is yours.
- **Changed:**
  - `juniper-service-core/juniper_service_core/security.py`: `validate` now compares UTF-8 bytes with `surrogatepass`.
  - `juniper-observability/juniper_observability/sentry.py`: `configure_sentry` passes `include_local_variables=False` unconditionally.
  - The same file's `before_send` hook now also deletes frame `vars`. It isn't strictly needed for the SDK's own capture paths, but the opt-in `PureEvalIntegration` writes `vars` regardless of the option (sentry-sdk 2.58.0, `pure_eval.py:77`). The hook keeps its name because data and cascor import it.
  - Tests: `juniper-service-core/tests/test_security.py`, `test_middleware.py`, `test_t2_websocket.py` and `juniper-observability/tests/test_sentry.py`.
  - The observability test uses the real SDK with a local capturing transport. It passes with the option alone, with the hook alone, and a control confirms the harness does see the leak when both are off.
  - Both sub-package `CHANGELOG.md` files gain a `### Security` section under `[Unreleased]`.
  - `util/ad-hoc/2026-09-24_bytes_compare_sentry_locals_verify.py` (new) is the run, baseline, mutate and drift-marker harness used for all three repos.
- **Test counts:**
  - service-core: 565 → **629** (+64). Coverage 98.28%, `security.py` 96%, per-file gate PASS.
  - observability: 130 → **148** (+18). `sentry.py` 100%, gate PASS.
  - `tests/test_service_fork_drift.py`: 11 OK with 3 skipped; with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`, 11 OK. The gate's own matcher, run against all three task worktrees, finds **16/16 sites present**, including every `isinstance(k, str)`, `k.strip()`, `matched = False` and `return matched`.
  - 7 nearby root suites: 178 OK, 6 skipped.
  - pre-commit passed on every changed file; the symbol-loss and docs screens found 0 issues.
- **Mutations:**
  - Reverting to the `str` compare fails **63 of 64**; the HTTP tests fail with `assert 500 == 401`. The only survivor is the ASCII-ASCII matrix pair.
  - `surrogateescape` fails 15 and strict UTF-8 fails 33.
  - Each observability mutation is caught: 4, 6 and 12 failures for no-option, no-hook and neither, plus 1 each for the threads and top-level walks.

## PR 2 — juniper-data
- **PR:** #440, https://github.com/pcalnon/juniper-data/pull/440. OPEN.
- **Head:** `0bee089e758d0a77b0031555ea865c7417b3013c`, on base `0f0f7e0e` (main after #438). Signed. Checks: 25 success, 2 skipped, 5 neutral, CLEAN.
- **Which case happened:** I followed your change of plan and did not wait. No PR from `fix/conditional-requests-round4-followups` existed at open time (19:39Z). After `git fetch`, `git log 0f0f7e0e..origin/main -- CHANGELOG.md` was empty.
- **CHANGELOG subset proof:** `git diff --numstat origin/main -- CHANGELOG.md` gives **38 added, 0 deleted**, as one pure insertion hunk `@@ -122,0 +123,38 @@`. It sits under `[Unreleased]`, directly above `[0.16.0]`, and GitHub shows +38/-0.
- **Files:** only `CHANGELOG.md`, `juniper_data/api/security.py` and `juniper_data/tests/unit/test_security.py`.
- **Sentry:** juniper-data only calls juniper-observability's `configure_sentry` and has no config of its own, so nothing changed here.
- **CI-lane trap:** CI runs `-m "unit and not slow"`, and `TestAPIKeyAuth` is unmarked, so tests added there would never run in CI. The 61 new tests are in two new classes marked `unit`. One existing unmarked test now expects bytes.
- **Counts:** unit 1880 → **1941** (+61); CI lane 1740 → **1801** (+61). Reverting fails 60 of 61, with `assert 500 == 401` on the app tests; `surrogateescape` fails 15 and strict UTF-8 fails 33.

## PR 3 — juniper-cascor
- **PR:** #689, https://github.com/pcalnon/juniper-cascor/pull/689. OPEN.
- **Head:** `97341680fc7d794f9e2a00a22615126c12cb0358`, on base `7f4a7213`. I rebased because #688, the supersession of #686, merged and touched `CHANGELOG.md`. Signed. Checks: 28 success, 1 skipped, 5 neutral, CLEAN.
- **Changed:** `src/api/security.py`, `src/tests/unit/api/test_api_security.py` (+62 tests: HTTP 401, the throttle reached, and `/ws/training` closing 4001) and `CHANGELOG.md` (+41/-0).
- **Judgement call, drop it if you disagree:** `src/main.py` gets `include_local_variables=False` in the CLI's own bootstrap `sentry_sdk.init`. That is cascor's only direct Sentry config. It is pinned by the new `src/tests/unit/test_main_sentry_no_local_variables.py`, an AST check with 4 tests. `app.py` and `manager.py` are untouched.
- **Counts:** `tests/unit/api` 2506 → **2568**; the unit CI lane 5378 → **5444**. Reverting fails 61 of 62; the HTTP tests fail with `assert 500 == 401` and the handshake with `TypeError`. Both `main.py` mutations are caught.

## Deviations, undone items and observations
- **`surrogatepass` instead of the brief's `surrogateescape`.** `surrogateescape` raises on `"\ud800"`, which a JSON-decoded key list can carry. It also maps `"\xe9"` and `"\udcc3\udca9"` to the same bytes. `surrogatepass` is total and injective, so a key matches exactly when the strings are equal.
- **Not changed anywhere:** the root juniper-ml `CHANGELOG.md`, every `docs/REFERENCE.md`, and the defect register. So there are no sections or line ranges to pass on. For the root CHANGELOG, the precedent is #993, #1082, #1300 and #1974, which put sub-package fixes only in the sub-package CHANGELOG.
- **Owner steps still needed, since no Release or tag was cut:**
  - The Sentry half reaches data, canopy and cascor's service path only after an observability release plus raising their `juniper-observability>=0.4.0` floors.
  - The service-core half reaches recurrence only after a service-core release.
- **Not added:** a drift-gate guard for the bytes compare, because that section belongs to the register session.
- **Possible events on the live Sentry project:** the shell exports `SENTRY_SDK_DSN`, and several cascor unit tests `import main`, which starts the real SDK. My first `tests/unit/api` run, before I stripped the DSN variables from the harness, ended with "Sentry is attempting to send 2 pending events". Those were likely test events sent to the live project with frame locals attached. Worth a follow-up: a cascor conftest that clears the DSN variables.

Worktrees are kept until merge:
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-ml--fix--sentry-locals-and-bytes-compare--20260924-1337--48fc09e5`
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480`
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb`

All scratch trees were removed automatically. Only logs and junit files remain under the scratchpad's `bytescmp/`, 82 files in total.
