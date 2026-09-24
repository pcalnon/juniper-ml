<!-- Archived verbatim 2026-09-24 from subagent a095601081725e701 of session bc31e993 (final message). -->

## Validation of juniper-canopy#678 (merged as `05f2dfc2`)

**Verdict:** #678's claims hold. Every figure and header behaviour reproduces from my own probes, and the `get_secret` refactor changes nothing for any caller. #678 introduces no security regression. There is one real test gap (MEDIUM), two LOW wording/behaviour mismatches, two NITs, and one MEDIUM adjacent issue that was already there before #678. **Changed:** nothing in any repo or worktree; all work is in `…/scratchpad/v678c/`.

### Findings

**1. MEDIUM — the boot regression test fakes the one step the WARNING depends on.** `src/tests/regression/test_blank_api_key_warning_boot.py:94-111`, relevant to `src/main.py:538`.
- **What:** `_read_key_as_main_does_at_import` calls `reset_security_state()` and then `get_api_key_auth()` itself. In production the WARNING only fires because `main.py:538` builds its auth handler through `get_api_key_auth()`, and nothing checks that.
- **Evidence:** mutant V8 rewrites `main.py:538` as `api_key_auth = APIKeyAuth([_k] if (_k := get_secret("CANOPY_API_KEY")) else None)`.
  - The 191 targeted tests all pass.
  - The full CI lane gives **6866 passed, 1 skipped**, the same as the unmutated tree.
  - Booted on real uvicorn with `CANOPY_API_KEY=" \t "`, it logs **0** blank-key lines on stdout, stderr and `logs/system.log`. `05f2dfc2` logs 1 on each.
- **Fix:** add a subprocess test: a fresh interpreter, a real `import main` with a blank key, the real lifespan, and an assertion of exactly one record in `logs/system.log`. At minimum, assert `main.api_key_auth is security._api_key_auth` in a fresh process.

**2. LOW — under `JUNIPER_CANOPY_REQUIRE_AUTH=true` the blank-key WARNING never appears, and nothing says so.** `src/main.py:341-356`, `CHANGELOG.md:446-447`, `docs/api/API_REFERENCE.md:87-88`.
- **What:** the posture check raises first. The only output is a CRITICAL saying "NO API key is configured … (an empty/placeholder secret *file* counts as unset)", which is wrong for a key that is set but blank. That confusion is what the WARNING exists to clear up, and it now shows up only in the secured profile. Both docs describe the startup WARNING as unconditional.
- **Evidence:** boot with blank key and `require_auth=true`: exit code 3, 0 blank-key lines, the CRITICAL present. Failing closed is acceptable for security.
- **Fix:** document it. Better: wrap the posture call in `try … except AuthPostureError: report_blank_api_key(…); raise`, worded so it does not claim routes are serving, and update `test_lifespan_reports_right_after_the_posture_check`.

**3. LOW — the WARNING's "exactly as with no key configured" is false for a whitespace-only env key.** `src/security.py:320`.
- **What:** two readers still use the raw value, as `security.py:78-81` itself says:
  - `main.py:504` keeps `/docs`, `/docs/oauth2-redirect`, `/openapi.json` and `/redoc` at 404.
  - `internal_api.py:59-60` sends the raw value, so every dashboard server-side self-call raises `requests` `InvalidHeader`.
  - An empty env var or a blank file really is identical to no key.
- **Evidence:** a route sweep of `05f2dfc2` with no key against a whitespace key: 4 pairs exist only with no key, all returning 200. The self-call probe with `' \t '` raises `InvalidHeader`.
- **Fix:** apply the blank rule in both readers (`not (v or "").strip()` and `key if key and key.strip() else None`), or drop "exactly as…" and name the two differences.

**4. NIT — "holds for spaces and tabs only" is wrong.** `src/security.py:67`, `CHANGELOG.md:421`.
- **What:** `str.strip()` also removes U+000B and U+000C, and both parsers refuse those with a 400. httptools, canopy's default parser, also refuses U+001C–U+001F. So no caller could present the key for more than just spaces and tabs. The builder's own `header-probe` includes VT and FF.
- **Evidence:** my raw-byte probe on uvicorn 0.49.0 and on 0.53.0 (the lockfile version): VT and FF get 400 under both parsers.
- **Fix:** "holds for every `str.strip()` character except U+00A0/U+0085, and, under h11 only, U+001C–U+001F."

**5. NIT — `test_get_secret_returns_exactly_the_resolved_value` checks almost nothing.** `src/tests/unit/test_secrets_util.py:159-173`.
- **What:** it compares `get_secret` against `resolve_secret()[0]`, so any change to `resolve_secret` moves both sides together.
- **Evidence:** it survives my mutants V2, V3, V5 and V7.
- **Fix:** assert literal expected values for each parameter.

**6. MEDIUM, already there before #678 (not in its diff) — a dashboard self-call can log the real key.** `src/frontend/internal_api.py:59-60` together with `src/frontend/dashboard_manager.py:3573` and similar `%s`-of-exception log calls.
- **What:** an env key that is not blank but has a leading space or trailing newline turns auth on. No parser delivers such a key intact. The self-call's `InvalidHeader` message then contains the full key, and the dashboard logs it at WARNING. Given `enable_logs=True`, that also goes to Sentry Logs.
- **Evidence:** `CANOPY_API_KEY=" leaked-key-XYZ123"` produces `frontend.dashboard_manager WARNING Selection hydration read failed (Invalid leading whitespace … ' leaked-key-XYZ123')`.
- **Related:** a `CANOPY_API_KEY_FILE` that names a missing file is silently treated as unset, with no distinct WARNING (`resolve_secret` returns `(None, None)`).
- **Fix:** stop logging the text of `requests` header errors, and refuse to boot (or strip) on a key with leading or trailing whitespace.

### Attacks that did not land

- **Route counts (my own sweep):** real lifespan, keyless TestClient requests, and each tree's own `_is_exempt`/`_is_key_exempt` for classification.
  - `48074653` with a whitespace key: 56 key-gated pairs, of which 27 change state, 26 are parameterless GETs and 3 are parameterised GETs. All 56 were refused with 401 "Missing API key".
  - `3a6dea95` and `05f2dfc2`: 0 of 56 refused, and all 26 GETs return 200.
  - `26e0546f`: 55/27/25; the difference is `GET /api/selection`.
  - Every named state-changing route is among the 27. There are six `/api/train/*` POSTs.
- **Header behaviour** (raw sockets, real uvicorn, h11 0.16.0 and httptools 0.8.0):
  - Spaces and tabs arrive empty on both parsers.
  - `A0` and `85` pass both parsers, then `compare_digest` raises `TypeError`.
  - `1C`–`1F` pass h11 and get 400 on httptools.
  - End to end on `48074653`: spaces and tabs got 401 whether keyless, with the key bytes, or with a wrong key, on both parsers. NBSP and NEL got 500 on any keyed request. FS..US got 200 under h11 and 400 under httptools.
  - On `05f2dfc2`, keyless requests get 200 everywhere.
- **The `get_secret` refactor:**
  - Nine callers outside tests: `main.py:340,504`; `internal_api.py:59`; `backend/__init__.py:95` (×2); `settings.py:486,489,544,547`. `security.py` now uses `resolve_secret`.
  - A differential run of the old against the new code covers 180 cases: missing, directory, empty, blank, unreadable, non-UTF-8 and dangling-symlink files, 6 env states, and both default and custom file variables. Result: 0 mismatches, identical exceptions, 0 log records.
- **The WARNING itself:**
  - On real uvicorn, blank env (text and JSON), empty env, and blank file with a real env key each give exactly one line on stdout, stderr and `logs/system.log`. In JSON mode the record is level WARNING, logger `system`. The file case gets the file advice.
  - It stays silent for a real env key, a real file key, an unset key and a padded real key. It still fires when `JUNIPER_SKIP_AUTH_POSTURE_CHECK` is set.
  - The key value never appears in the logs.
  - With a fake Sentry DSN it arrives as a Sentry `log` item at level warn.
  - For comparison, on `3a6dea95` (#660) it appeared only as a bare, non-JSON line on stderr and never in `system.log`, which is the defect #678 claims to fix.
- **Firing more than once, and test pollution:** no production code calls `reset_security_state`. The autouse test fixture clears both recorded fields. The full suite is green with no pollution seen.
- **Mutations:** my V1–V7 were all caught.

  | Mutant | What it breaks | Caught by |
  |---|---|---|
  | V1 | a real key gets the WARNING | 3 tests, the real-key guards |
  | V2 | file contents no longer stripped | 17 tests in the secrets and API-key tests |
  | V3 | env var now stripped | 4 tests, the raw-env tests |
  | V4 | report logged through a different logger | 3 boot tests |
  | V5 | a blank file no longer takes precedence | 6 tests |
  | V6 | logged at ERROR instead of WARNING | 4 tests |
  | V7 | custom file variable dropped | 1 test, `test_custom_file_env_var` |

  The builder's own mutation script also reproduces: 10 of 10 caught.
- **CHANGELOG against `9cdfcad4`:** only #660's two superseded lines were removed, and the note that it supersedes `3a6dea95`'s message is present. Current `origin/main` differs from `05f2dfc2` only by #676's CHANGELOG lines.
- **juniper-ml drift gate:** run from a copy of the worktree file against a synthetic ecosystem root: 11 of 11 pass on `05f2dfc2`, with markers at `security.py:82,112,116`. `security.py` on `origin/main` is identical. A negative control on `48074653` fails exactly the two canopy guards.
- **Suites on `05f2dfc2`** (CI lane selector): unit 6021 passed, regression 838 passed, contract 3, performance 4 plus 1 skipped. Total 6866 passed, 1 skipped, 4 deselected.
- **`gh run list` for `05f2dfc2`:**
  - The push CI/CD run 35928615435 was **cancelled**. Its unit and integration jobs were cancelled, so Quality Gate shows failure.
  - A repository_dispatch CI/CD run on the same SHA, 35929217209, passed every job.
  - Post-Merge Main Verification and CodeQL both succeeded.
  - All of the PR's checks were green before it merged.

Everything is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678c/`. The probe scripts are `my_route_sweep.py`, `header_probe.py`, `canopy_e2e.py`, `boot_scenarios.py`, `sentry_probe.py`, `diff_get_secret.py` and `my_mutations.py`; the V8 tree is `v8tree/`. The scratchpad is temporary, so these need copying to `juniper-canopy/util/ad-hoc/` if they should be kept.
