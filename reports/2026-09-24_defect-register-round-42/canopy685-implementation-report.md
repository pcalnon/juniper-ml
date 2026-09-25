<!-- Archived verbatim 2026-09-24 from subagent accf63b081529855a of session bc31e993 (final message). -->

I opened PR #685 in juniper-canopy after #683 merged, and it covers all four items plus your scope addition (all three `str` compare sites). #683 merged at 19:10Z as `7ab994e5`, and this branch is rebased onto it. At open time main was still `7ab994e5`, so none of the changed files had moved.

- **PR:** https://github.com/pcalnon/juniper-canopy/pull/685, read back with `gh pr view`: OPEN, MERGEABLE, not draft, no auto-merge armed. Some CI checks had already passed (Sequence Safety, Guard PR base branch, Documentation Links); the rest were pending.
- **Head SHA:** `4a8af2a04911a8be89bd403740be9d1693ef8ea5`. GitHub signed it (verified), its parent is `7ab994e5`, and its tree `7fbccc33` is identical to the local commit I tested.
- **Every `#NNN` checked with `gh`:** #660, #678, #683 and juniper-ml#2086 are all merged.

## Items, pinning tests, mutants
The mutation harness applies each mutant to a copy of the tree: **44/44 caught**, and the unmutated copy passes all 429 of the named tests.

**1a. Outbound keys are checked where they are read** (`src/secrets_util.py`, `src/settings.py`, `src/backend/__init__.py`)
- Any value outside printable ASCII `0x21`–`0x7E` is treated as empty, and one WARNING names the variable only.
- The juniper clients re-read the raw env var when handed no key. `bind_outbound_key` switches that off at all five places canopy builds a client.
- Pinned by `src/tests/unit/test_outbound_keys.py` (70 tests), `src/tests/regression/test_outbound_secret_leaks_boot.py` (15 fresh-process boots), `test_juniper_data_api_key_resolution.py` and `test_recurrence_settings.py`.
- 23 mutants killed: the rule's bounds, every read site, every client binding, the report and its two timing points, and conftest isolation.

**1b. No transport text reaches a caller** (new `src/outbound_errors.py`, plus the adapter, `status_cache.py`, `recurrence_backend.py`, `main.py`)
- An exception that carries an HTTP status is the upstream's answer, so its text passes. Anything else is named by its type only.
- Covered: all 19 adapter error envelopes, the Start 409 (fixed at its source, so `service_backend.py:201` needed no change), the `/api/status` error, `/api/stream_health`, `completion_reason`, and 8 routes.
- Pinned by `src/tests/unit/test_outbound_errors.py` (74 tests, including a static check of every `except` handler in the adapter).
- 10 mutants killed, including both extremes of the rule (pass everything / pass nothing).

**1c. The census.** Every outbound client is listed in a table in the PR. The validator's probes are kept as `util/ad-hoc/2026-09-24_683_validation_leak_probes.py`.
- Before, on #683's head, every leak reproduced: the key in logs, in API bodies, and in the anonymous Start's 409.
- After: zero in logs, console, log files, API bodies and on the wire.

**2. Bytes compare at all three sites**, UTF-8 with `surrogatepass`, drift-gate markers kept:
- `APIKeyAuth.validate`
- the `X-Canopy-Internal` rate-limiter compare
- the CSRF store, which now also rejects a non-`str` token before comparing

New tests:
- **HTTP level** (`TestNoSecretCompareCanRaiseOverHttp`): a non-ASCII `X-API-Key` gets 401; anonymous `/api/csrf` with a non-ASCII internal header gets 200 with no exemption; a non-ASCII CSRF token gets 403.
- **WebSocket** (`/ws/control` first frame): an int, list, dict or non-ASCII `csrf_token` is closed 1008 as `invalid_token`, where the old code crashed and filed it as `malformed_auth`.
- **Spy test:** three keys, match first, one compare per key, both sides bytes.

7 mutants killed, including `validate-breaks-on-match` and `compare-bytes-surrogateescape`.

Real uvicorn plus a local Sentry sink, all four cases:
- anonymous `validate` and anonymous internal header: 500 → 401 / 200
- keyed internal header: 500 → 200
- CSRF: 500 → 403
- Zero envelopes carry a key or token after the fix.

The validation's `canopy_probe.py` and `canopy_uvicorn_probe.py` agree: before, `TypeError` everywhere and 500s; after, `False`, 401 and 200.

**3. Docs switch.** `_docs_enabled = not get_api_key_auth().enabled`. The boot tests expect 404 for `env-real` and `file-real`, and 200 for `env-empty`, `env-nbsp` and `file-blank`. It kills the validator's M2 and M3 mutants.

**4. Padded-key WARNING wording.** There is now one wording per source. Pinned by `test_a_key_file_with_a_line_break_inside_warns_naming_the_file[lf, crlf-padded-ends]`; 2 mutants killed.

## Test commands and counts
All runs used `env LIBTORCH= LD_LIBRARY_PATH=` with the JuniperCanopy1 python; the final runs also had every Sentry DSN variable unset.
- **CI lane** (`-m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/ src/tests/performance/ --timeout=60`): 7244 passed, 1 skipped, 4 deselected. With `--cov=src --cov-fail-under=80`, run just before the last 9 tests were added, coverage was 96.38%.
- **Integration lane** (`-m "integration and not requires_cascor and not requires_server and not slow" src/tests/integration --timeout=120`): 560 passed, 41 skipped. Its first run caught two tests still asserting the old error text, which I updated.
- **Scheduled lane** (`-m "slow or integration"`): 563 passed, 43 skipped.
- **CI's environment reproduced:**
  - With juniper-data-client hidden, as in CI: 1075 passed, 3 skipped by design, and the boot tests pass (15).
  - Under websockets 17.1, the version the lock pins: 946 passed, and the boot tests pass (15).
- **New tests: 211**, 159 in the three new files and 52 added to existing ones. Collecting before and after shows none removed or renamed.
- **Checks:** pre-commit is clean on all 37 files. The symbol-loss screen reports one relocated import (`import:get_secret`), waived in the commit body; the docs screen reports two small-deletion warnings, no failure.

## Left undone and judgment calls
- **Sentry still captures frame locals in the shipped release.** juniper-ml#2086 fixes it, but PyPI's latest juniper-observability is still 0.4.0, which canopy's lock pins. I measured that until a release lands, *any* unhandled exception during a keyed request records the caller's key. It travels in the ASGI `scope` headers held as a frame local, which Sentry's name-based scrubber does not reach. Follow-up: release juniper-observability and bump canopy's lock.
- **Upstream answers still pass through.** An error that carries an HTTP status keeps its text, so cascor's own messages still reach the UI. Switching to type-only everywhere is a one-line change in `outbound_errors.py`; it's your call.
- **Behaviour change:** a blank `*_API_KEY_FILE` that shadows a real env var now sends no key.
- **Stricter than the clients:** the rule also refuses a space or tab inside a key, which the clients would send.
- **Anonymous rate-limiter 500 needs rate limiting on:** it's reachable only with `rate_limit_enabled`, which defaults to off.
- **Comment left as-is:** a pre-existing comment in `test_cascor_service_adapter_gate_coverage.py` still says CI installs only the stub cascor client; CI installs the real one.
- **`SENTRY_SDK_DSN` in the shell:** it is exported there, and some local runs before your message inherited it. Nothing reads that name, and every fresh-process boot and probe drops all Sentry variables anyway.
- **Flaky test found and fixed:** the harness exposed a thread race in my own new boot test (pytest's temp-dir factory), and I fixed it before opening.
- **Worktree left in place** while the PR is open. The local branch holds the unsigned commit `4caf9389` (same tree), never pushed.

## Documents
**Changed (37 files, in juniper-canopy):**
- **Docs:** `CHANGELOG.md` (`[Unreleased]` → Security), `docs/api/API_REFERENCE.md`
- **Source:** `src/backend/__init__.py`, `src/backend/cascor_service_adapter.py`, `src/backend/recurrence_backend.py`, `src/backend/status_cache.py`, `src/canopy_constants.py`, `src/csrf.py`, `src/demo_mode.py`, `src/main.py`, `src/outbound_errors.py` (new), `src/secrets_util.py`, `src/security.py`, `src/settings.py`
- **Test support:** `src/tests/conftest.py`
- **Integration tests:** `src/tests/integration/test_apply_dataset_flow.py`, `test_apply_params_skipped_surfaced.py`, `test_network_mutations_api.py`
- **Regression tests:** `src/tests/regression/test_outbound_secret_leaks_boot.py` (new), `test_x7_status_cache.py`
- **Backend unit tests** (`src/tests/unit/backend/`): `test_cascor_service_adapter.py`, `test_cascor_service_adapter_gate_coverage.py`, `test_dataset_swap_events_adapter.py`, `test_experimental_functions_adapter.py`, `test_recurrence_backend.py`, `test_start_fresh_forwarding.py`, `test_swap_dataset_live_adapter.py`
- **Other unit tests** (`src/tests/unit/`): `test_f007_snapshots_resolve_through_backend.py`, `test_juniper_data_api_key_resolution.py`, `test_main_snapshot_coverage.py`, `test_outbound_errors.py` (new), `test_outbound_keys.py` (new), `test_phase_b_pre_b_csrf.py`, `test_recurrence_settings.py`, `test_security.py`
- **Scripts:** `util/ad-hoc/2026-09-24_683_validation_leak_probes.py` (new), `util/ad-hoc/2026-09-24_683_validation_mutation_check.py` (new)

**Referenced, not changed:** the validator's probes in the session scratchpad (`v683/e2e_other_secrets.py`, `e2e_anon_extract.py`, `lib_probe.py`, `sentry_probe.py`, `file_linebreak_probe.py`, `docs_switch_probe.py`; `vbytes/canopy_probe.py`, `canopy_uvicorn_probe.py`); `.github/workflows/ci.yml` and `main-verify.yml` for the lane definitions; `util/open_signed_pr.py` in the juniper-ml worktree.

Worktree: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac`
