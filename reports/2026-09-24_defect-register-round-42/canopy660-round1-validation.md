<!-- Archived verbatim 2026-09-24 from subagent aef8ba5499762289f of session bc31e993 (final message). -->

## Defects, ordered by severity

**Head re-checked:** `13eccae04c59bde762af6435ade8813e413072ce`. It has not moved since I started, so every read below is against the current head.

**D1 (Medium): the behaviour-change section understates what opens, and nothing new is logged.**
- **Claim.** The PR #660 body says "HTTP refused every keyed request" before the fix, and after it "every path is open. That is what the posture check's WARNING already said". The canopy `CHANGELOG.md` entry says "It now disables auth, which is what that log line said."
- **Why it's incomplete:**
  - Before the fix, a whitespace-only env key left `APIKeyAuth` enabled. `require_browser_control_auth` (`src/security.py:372-403`) therefore took step 3: keyless `/api/train/*` requests had to pass the Origin allowlist and a CSRF token.
  - After the fix, it returns at step 2 (`if not auth.enabled: return`, `:382-383`). All six state-changing `/api/train/*` POSTs (start, pause, resume, stop, reset, restart; `src/main.py:3658-3846`) now accept a cross-site POST with no Origin check and no CSRF token.
  - `api_train_start` takes an optional body (`body: _TrainStartBody | None = None`, `:3659`). A body-less POST is a CORS "simple request" with no preflight, so any web page could send it.
  - `/api/csrf` also stops refusing disallowed origins (`:685`).
- **Evidence.** I ran the real `require_browser_control_auth` in a FastAPI app with `CANOPY_API_KEY="   "` and default settings (4 localhost origins allowlisted, CSRF on).

  | Request | Old code | New code |
  |---|---|---|
  | `Origin: https://evil.example`, no key, no CSRF | 403 | 200 |
  | No Origin | 403 | 200 |
  | Allowlisted Origin, no CSRF | 403 | 200 |

- **No new signal.** `enforce_auth_posture` logs the same "running OPEN" WARNING before and after. An operator who ignored it while HTTP answered 401 gets nothing new when the surface opens.
- **Limits.** Only `require_auth=false` or `JUNIPER_SKIP_AUTH_POSTURE_CHECK` deployments are affected. juniper-deploy's `docker-compose.yml:690,696` uses `CANOPY_API_KEY_FILE` and defaults `JUNIPER_CANOPY_REQUIRE_AUTH=true`, so the composed stack is unaffected. This is also canopy's documented posture when no key is set.
- **Fix:**
  1. Disclose the lost Origin/CSRF gate in the PR body and `CHANGELOG.md`.
  2. Log a distinct WARNING in `get_api_key_auth()` when `CANOPY_API_KEY` is set but blank.
  3. Separately, and only with an owner decision, consider keeping the Origin check when auth is disabled.

**D2 (Low): the WebSocket "before" statement holds only in the default configuration, and it was never an exposure.**
- **Claim.** "WebSocket accepted the whitespace key … `?api_key=%20%20%20` authenticated."
- **(a) Opt-in bearer auth (SEC-06) reverses it.** With `ws_auth_enabled=true` (`src/settings.py:383`), `_authenticate_websocket_token` (`src/main.py:724-754`) runs next. It strips and drops blank protocol parts, so no client can present the whitespace key there.
  - Measured with real uvicorn and websockets: the old code refused every connection (403); the new code admits `bearer, anything`.
  - That is a second closed-to-open change that "Who sees the change" does not name.
- **(b) The key gained nothing.** All three WS routes (`:776`, `:913`, `:3576`) call `_authenticate_websocket(..., allow_browser_auth=True)`. A keyless connection passed that gate before the fix too; I measured "no key → ADMITTED" under the old code. The whitespace key got nothing a keyless client didn't already have.
  - The uncommitted APD-ECO-008 edit in `juniper-ml/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (worktree `happy-skipping-hollerith`, around line 1278) says this "Refuted" the "probably not an auth bypass" reading. It does not refute it.
- **Fix.** Qualify the sentence ("with `ws_auth_enabled=false`; keyless connections were admitted at the same gate"). Add the SEC-06 case to "Who sees the change". Correct the register sentence before it lands.

**D3 (Low): two other readers of the raw secret still treat whitespace as a configured key.**
- **Claim.** The code comment at `src/security.py:66` says "Filtering makes all three agree". The PR body says "every path is open".
- **Why it's wrong:**
  - `src/main.py:494` (`_docs_enabled = not get_secret(...)`): the docs stay unmounted. Harmless.
  - `src/frontend/internal_api.py:59-60,77-78`: the dashboard's self-call helper still sends `X-API-Key: '   '`.
  - Before the fix, both agreed with `APIKeyAuth`; after it, `APIKeyAuth` disagrees with both.
- **Evidence (after the fix).** `auth.enabled` is False, but `internal_api_headers()["X-API-Key"] == '   '`. `requests` then raises `InvalidHeader` before sending, at all 63 call sites in 9 modules. The dashboard was broken the same way before the fix, so this is not a regression, but the claim is overstated.
- **Fix.** Apply one rule, `key if key and key.strip() else None`, to all readers. Or make `get_secret` strip env values the way it strips file values; that is a separate decision because it changes `" k "` keys.

**D4 (Low): "already fixed" is true only of juniper-service-core's source, not its release.**
- **Claim.** "the only copy still carrying the two defects the other three had already fixed"; "the behaviour all three siblings already have."
- **Evidence.** The published juniper-service-core 0.7.0 wheel (latest on PyPI, and canopy's `requirements.lock:81` pin) still ships `return any(hmac.compare_digest(api_key, k) for k in self._api_keys)`. Only juniper-ml `main` (#1974) has the flag loop.
- **Fix.** Say "on main; unreleased in juniper-service-core".

**D5 (Low): the cited ruling isn't in the versioned register.**
- **Claim.** "as the owner ruled it on 2026-09-22", citing the defect register.
- **Evidence.** On juniper-ml `origin/main`, `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md:1406` still says APD-ECO-008 "needs an owner decision". The ruling exists only as an uncommitted local edit.
- **Fix.** Land the register edit first, or with this PR.

**D6 (Nits):**
- **The "ten files that exercise `APIKeyAuth`" list isn't exhaustive.** The 240-pass count reproduces exactly, but `unit/test_middleware.py` and `unit/test_concurrent_load.py` also construct `APIKeyAuth`. Those, plus `unit/frontend/test_internal_api_gate_coverage.py` and `unit/test_secrets_util.py`, give 32 more tests; all pass on the branch.
- **The local env's juniper-service-core is stale.** `JuniperCanopy1` has 0.5.0 while the lock pins 0.7.0. The `real_keys` predicate is the same in both, so the results hold.
- **The compare change has no practical effect in canopy.** `get_api_key_auth` only ever builds a one-key list, so there is no key position to leak.

## Attacks that did not land

1. **Semantic parity holds.** I extracted `APIKeyAuth` from canopy (this PR), service-core, data and cascor (`origin/main`) and ran the same 26 inputs through each, with 9 presented keys per input. There were 0 mismatches in `enabled`, the key set, `validate` results or exceptions.
   - Inputs covered blanks, non-str entries (None, 123, bytes, dict, list), Unicode whitespace, zero-width space, duplicates, and tuple, str, set, dict and generator containers.
   - The filter predicate and `_enabled` are identical, and non-str entries are dropped before hashing.
   - juniper-data's `dict.fromkeys` list has the same members as the sets.
2. **Fork-drift markers are present and discriminating.** `isinstance(k, str)` and `k.strip()` are at `:69`, `matched = False` at `:99`, `return matched` at `:103`. They appear only in code, with no other `k.strip()` substring, and none exist on main.
3. **No path goes open silently.** The filter uses the same predicate as `real_keys` on the same input. Nothing in `src/` writes `CANOPY_API_KEY` between import (`main.py:528`) and lifespan (`:340`). Posture outcomes verified:
   - WARNING when `require_auth` is false.
   - `AuthPostureError` when it is true.
   - "SKIPPED" WARNING under the skip env var.
   - A secret file and keys with only partial whitespace behave identically before and after.
4. **The HTTP parser claim holds.** httptools and h11 both yield `b''` for all-whitespace headers. Real uvicorn with the old code returned 401 with or without the header, under both parsers.
5. **The WS claim reproduces end to end.** With real uvicorn and the real `_authenticate_websocket`, the old code admitted `%20%20%20` and `+++` and refused `wrong` with 403; the new code admits all of them.
6. **The tests are not vacuous.**
   - Against the old `security.py`, injected via `sys.modules`: 8 failed and 5 passed, with exactly the symptoms the PR states. On the branch, 13/13 pass.
   - The compare-count test patches `validate.__globals__["hmac"]`, the dict `validate` actually resolves `hmac` from. It counted 1 call on the old code and 3 on the new.
   - CI ran all 13 new tests: 6513 passed on main at the base, 6526 on the PR.
7. **CHANGELOG is clean.** There is one `### Security` heading under `[Unreleased]`. A 3-way merge with current main (#658 and #662 both add `[Unreleased]` entries) is clean, leaving Added, Fixed and Security once each. `src/security.py` is unchanged on main.
8. **References check out.** juniper-cascor#659 and juniper-ml#1974 are merged. There are exactly four `class APIKeyAuth` copies in the ecosystem (cascor, data, canopy, service-core).

## CI (head 13eccae0)

| Check | Result |
|---|---|
| Unit Tests + Coverage: 3.12, 3.13, 3.14 on ubuntu-latest; 3.12 on macos-latest | pass on all four (6526 passed / 5 skipped / 4 deselected each) |
| Pre-commit 3.12 / 3.13 / 3.14 | pass |
| Quality Gate, Integration Tests, UI Sub-suite (Playwright), Docker Build & Smoke Test, Build Distribution, Build linux/amd64 + arm64 | pass |
| Security Scans, CodeQL, Analyze (python), Sequence Safety, Async-route audit | pass |
| Documentation Links, Dependency Documentation, Lockfile Freshness, Memory Budget, Guard PR base branch, Build Notification | pass |
| 5 Cursor Automation jobs, Publish manifest | skipping |
| **Total** | 25 pass, 6 skipping, 0 fail, 0 pending; all 21 required checks pass |

- **Merge state: BEHIND.** Main gained #658 and #662 since the PR was cut, and the strict ruleset means it needs an update-branch before merging. The simulated merge is clean.
- **Reviews:** 0 review threads.

**Changed:** nothing. One side effect: my test runs appended to the gitignored `logs/system.log` in the canopy worktree (ignored by `.gitignore:25`). No tracked file was touched.
