<!-- Archived verbatim 2026-09-24 from subagent a4124be3e061bf07f of session bc31e993 (final message). -->

PR #683 is open, and all six items are fixed and tested. The CI lane, integration lane, pre-commit and symbol-loss screen all pass, and the mutation harness catches 21 of 21 mutations. One deviation on item 6 needs your call: I fixed the leak at its source, not at each of the 54 logging sites.

## PR (read back via `gh pr view 683`)
- **PR:** #683, https://github.com/pcalnon/juniper-canopy/pull/683. It is OPEN and not a draft, with base `main` and head `fix/blank-key-678-followups`. It changes 15 files (+1959/−106).
- **Auto-merge:** `null`. I never pushed, merged, armed or ran update-branch.
- **Head SHA:** `8917fdac855b68fe48bc9c3a435a0b743597be58`. Its parent is current main `5907713b` (#680). GitHub reports the commit as verified (`valid`), and the trailers are its last paragraph.
- **The PR is exactly what I tested:** the remote tree (`0ea82c7f`) matches the tested local tree.
- **CI when I stopped watching:** 4 pass, 9 pending, 5 skipping, 0 failing. I did not wait for it to finish.
- **Two rebases:** main moved twice while I worked. #679 touched `CHANGELOG.md`. #680 changed `_hydrate_selection_handler`, which my leak test drives. Every run below is on the final rebased tree.
- **#NNN references:** only #660, #678 and #680 appear, and each was checked with `gh pr view`.

## Per item

1. **Boot test faked the key step (MEDIUM).**
   - **Fix:** two new tests boot canopy in a fresh interpreter (real `import main` with a blank key, real lifespan run twice). They run in a temporary working directory with the repo's logging config copied in, because canopy writes `conf/`-configured logs under `logs/` relative to the working directory.
   - **Pinned by:**
     - `test_a_fresh_process_builds_its_auth_handler_through_get_api_key_auth` checks `main.api_key_auth is security._api_key_auth`.
     - `test_a_fresh_boot_writes_the_blank_key_warning_to_system_log_once` checks for exactly one line in `logs/system.log`.
   - **Kills V8:** on a copy of the validator's `v8tree/` with the new test file added, both tests fail (identity `False`, 0 lines). On unmutated `05f2dfc2` both pass. The harness also runs V8 as an arm.
2. **No WARNING under `JUNIPER_CANOPY_REQUIRE_AUTH=true` (LOW).**
   - **Fix:** the lifespan catches `AuthPostureError`, logs the WARNING with wording for a refused boot (`boot_refused=True`) and re-raises. `CHANGELOG.md` and `API_REFERENCE.md` no longer call the WARNING unconditional.
   - **Pinned by:**
     - `test_blank_key_warns_when_require_auth_refuses_the_boot[env|file]` (new).
     - `test_lifespan_reports_right_after_the_posture_check`, updated: it now checks the code structure instead of text positions.
     - Unit test `test_a_refused_boot_gets_the_refused_wording`.
   - **Kills:** 6 arms, including #678's own behaviour (`refused-boot-unreported`), a swallowed refusal, and a report placed before the check.
   - **WIP bug fixed:** the new import line broke `test_lifespan_wires_auth_posture_check`'s text match. I widened it to a regex and kept the name.
3. **"Exactly as with no key" was false (LOW).**
   - **Fix:** `_docs_enabled` and `internal_api` now apply the blank rule.
   - **Behaviour change, disclosed in the changelog:** with a whitespace-only env key, `/docs`, `/docs/oauth2-redirect`, `/openapi.json` and `/redoc` now return 200 to anyone who can reach the port.
   - **Pinned by:**
     - Two fresh-process tests: docs routes return 200, and a self-call sends no key.
     - Two unit tests over 11 blank shapes. One takes away `requests`' own refusal, which would otherwise hide a missing blank rule.
   - **Kills:** 3 arms.
4. **Wording (NIT).** `security.py` and `CHANGELOG.md` now carry the phrase you specified, plus the measured behaviour. I re-ran #678's `header-probe` today on the installed uvicorn 0.49.0 and it matched. It is comment and changelog text, so no test pins it.
5. **`get_secret` test (NIT).** It now asserts literal values per case, and a padded env case was added. It kills V2, V3 and V5. V7 is outside this test's reach and is still killed by `test_custom_file_env_var`.
6. **Padded key leaks into logs (MEDIUM).**
   - **Deviation from the brief:** instead of editing the 54 logging sites, `internal_api` now leaves off any key `requests` refuses to send. It asks `requests` itself through its public API, so no self-call can raise the `InvalidHeader` that quotes the key.
     - The census found 64 self-call sites. 54 log or return the text: 33 at WARNING, 4 at ERROR, 9 at DEBUG, 8 return-only.
     - The only header that can carry the key is the one this helper builds, so a per-site fix would leave the next new site open. If you still want type-only logging at each site as extra defence, that is a follow-up.
   - **Boot WARNs once** about a padded key (leading or trailing whitespace, or a line break; not stripped, boot not refused) and about a `CANOPY_API_KEY_FILE` that names no file. Both warnings carry variable names only.
   - **Pinned by:**
     - `test_a_padded_key_never_reaches_a_log_record`: fresh process, every log record from any logger, 8 real handlers × 5 padded keys, and a check that every handler actually self-called.
     - `test_a_padded_key_warns_once_at_boot` and `test_a_missing_key_file_warns_once_at_boot`.
     - Unit tests in `test_security.py`, `test_internal_api_key_rules.py` and `test_secrets_util.py`.
   - **Kills:** 9 arms.
   - **Before and after:** the predecessor's leak probe finds 1 log record carrying the key on `05f2dfc2`, and 0 on this branch.

## Commands and counts
All runs used `env LIBTORCH= LD_LIBRARY_PATH=` with `/opt/miniforge3/envs/JuniperCanopy1/bin/python`.

| Run | Command | Result |
|---|---|---|
| CI lane | `-m pytest -p no:cacheprovider -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/ src/tests/performance/ --timeout=60` | 7019 passed, 1 skipped, 4 deselected. `origin/main` collects 6907 under this selector, so the PR adds 113 tests, none marked `slow`. |
| Integration lane | `-m pytest -p no:cacheprovider -m "integration and not requires_cascor and not requires_server and not slow" src/tests/integration --timeout=120` | 559 passed, 41 skipped, 461 deselected |
| Targeted | six key-handling test files, `test_middleware.py`, and #680's three test files | 361 passed |
| Mutation | `util/ad-hoc/2026-09-24_678_followup_mutation_check.py --jobs 4`, run before and after the #680 rebase | control 213/213, 21/21 caught |
| pre-commit | `/opt/miniforge3/bin/pre-commit run --files` on the 15 files | 18 hooks pass |
| Symbol-loss | the screen, against `origin/main` | fail=0. One WARN: `security.py` now imports `resolve_secret_detail` instead of `resolve_secret` (RELOCATED). No test renamed, so no waiver. |

## Not done
- **Outbound keys:** a padded `JUNIPER_DATA_API_KEY` sent through httpx may have the same leak. I did not check it end to end.
- **#678's mutation script:** `2026-09-23_blank_api_key_warning_mutation_check.py` can no longer apply its M5/M6 arms, because their anchor is gone from `main.py`. Its retire condition is already met.
- **Non-ASCII keys:** they still cause a 500. Unchanged, and documented.
- **Worktree:** left clean, with the local branch moved onto the signed commit. Remove it after merge.

## Documents
All paths are under `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227/`.

**Changed:**
- `CHANGELOG.md`
- `docs/api/API_REFERENCE.md`
- `src/main.py`
- `src/security.py`
- `src/secrets_util.py`
- `src/frontend/internal_api.py`
- `src/canopy_constants.py` (comment only)
- `src/tests/regression/test_blank_api_key_warning_boot.py`
- `src/tests/regression/test_auth_posture_boot_check.py`
- `src/tests/unit/test_security.py`
- `src/tests/unit/test_secrets_util.py`

**New:**
- `src/tests/unit/frontend/test_internal_api_key_rules.py`
- `util/ad-hoc/2026-09-24_678_followup_mutation_check.py`
- `util/ad-hoc/2026-09-24_padded_api_key_probes.py`
- `util/ad-hoc/2026-09-24_self_call_error_text_census.py`

The two `util/ad-hoc/2026-09-24_*` probes are the predecessor's. I included them, gave the leak probe a free port, and updated the census docstring.

**Referenced, not changed:**
- `canopy678-postmerge-validation.md` and `wip-canopy-followup-base-e9053227.patch`, both in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/reports/2026-09-24_defect-register-round-42/`.
- `/home/pcalnon/Development/python/Juniper/juniper-canopy/AGENTS.md`
