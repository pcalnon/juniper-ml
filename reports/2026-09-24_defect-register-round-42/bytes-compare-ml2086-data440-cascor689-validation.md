<!-- Archived verbatim 2026-09-24 from subagent a395fc72ec02b15d8 of session bc31e993 (final message). -->

None of the three PRs had merged when I finished. Inside their own scope all three fixes hold, and I found no correctness bug in the compare. The biggest problem is outside them: **canopy still has the exact bug**, in the file where it was first found. The other findings are pre-existing gaps and test-strength issues.

**Merge status.** ml#2086's head is now `897666228a07eaa69ce85593e0e656ef017653a6`, a merge of main `6c23fdde` into the head I validated (`4924ca98`). I checked it: the PR's 9 files are identical between the two, and the only other changes are main's notes and ad-hoc files. Its checks are 23 pass, 3 pending (Regression Tests on Python 3.12, 3.13 and 3.14), 6 skipping; auto-merge is armed. On `4924ca98` they were 27 pass, 6 skipping. data#440 is 25 pass / 7 skipping and cascor#689 is 28 pass / 6 skipping. No squash trees to compare yet.

## Findings

**F1 · no PR covers it (gap in "Fix everywhere now") · HIGH**
- **Where:** juniper-canopy main `7ab994e5` (after #683 merged): `src/security.py:115`, `src/security.py:273`, `src/csrf.py:91`.
- **What's wrong:** all three still call `hmac.compare_digest` on `str`.
  - `:115` is `APIKeyAuth.validate`, the original finding.
  - `:273` compares the `X-Canopy-Internal` header. It is reachable anonymously on the key-exempt paths `/api/csrf` and `/api/train/*`.
  - `:91` is the CSRF check. It loops over every session's token, so the frame dies holding another session's live token as `stored_token`, a name not on Sentry's denylist. A non-str `csrf_token` in a WebSocket message (`main.py:1009`) also raises there.
- **Evidence:**
  - `canopy_probe.py` raises `TypeError` at `security.py:115`, `security.py:273` and `csrf.py:91`; the CSRF frame's locals are `[expiry, now, self, stored_token, token]`.
  - Real uvicorn (httptools): `/api/status` with `X-API-Key: \xa0` → **500**, with `wrong-ascii` → 401; `/api/csrf` with `X-Canopy-Internal: \xa0` → **500**.
  - `gh pr list --repo pcalnon/juniper-canopy --state open` → `[]`.
  - Canopy's `requirements.lock:79` pins `juniper-observability==0.4.0`, so it keeps shipping locals.
- **Fix:** a fourth PR. Port the bytes compare into canopy's `validate`. Encode both sides in the other two compares, with an `isinstance(token, str)` guard for CSRF. Add a canopy suite to the harness.

**F2 · ml#2086 (pre-existing, in the docstring it edits) · MEDIUM**
- **Where:** `juniper-observability/juniper_observability/sentry.py:129-139`. The docstring claims are at `:20` and `:120-121`.
- **What's wrong:** there is no `before_send_transaction`, and transactions skip `before_send`. With `send_pii=True`, every sampled transaction carries the raw `x-api-key`. That contradicts the docstring's "still scrubs sensitive headers regardless of this flag".
- **Evidence:**
  - `sentry_txn_probe.py` on sentry-sdk 2.58.0 and 2.70.0: with `send_pii=True`, the transaction has `secret-in-item=True … "x-api-key":"txn-p…"`; the error event does not.
  - On juniper-data's own app at its PR head, with `sentry_send_pii=True`: `SECRET ON THE WIRE: True (occurrences: 4) … "x-api-key":"\u00a0, real-configured-key-LEAKMARK-9c1e"`.
  - Only juniper-data can opt in (`JUNIPER_DATA_SENTRY_SEND_PII`); the cascor and canopy wrappers never pass `send_pii`.
- **Fix:** pass `before_send_transaction=_strip_sensitive_headers` and add a test for a `send_pii=True` transaction.

**F3 · ml#2086 and data#440 · MEDIUM (test gap)**
- **Where:** `juniper-service-core/juniper_service_core/security.py:91`; `juniper_data/api/security.py:118`.
- **What's wrong:** no test that CI runs checks that `compare_digest` is used at all. Replacing it with bytes `==` never raises and returns correct results, but it leaks timing, so it is the likely "simplification".
- **Evidence:** with that mutation:

  | Copy | Tests failing | Caught by |
  |---|---|---|
  | service-core | 0 of 629 (drift gate passes) | nothing |
  | data, CI lane | 0 of 72 | only `test_validate_uses_constant_time_comparison` (`test_security.py:176`), which sits in the unmarked class at line 37 and is deselected in CI |
  | cascor | 1 of 114 | `test_validate_uses_timing_safe_comparison` |

- **Fix:** add a spy test to each copy: at least 2 keys, the matching key first, and `len(calls) == len(keys)` with bytes arguments. In data, also mark the existing spy test `unit`. The same test kills F8.

**F4 · cascor#689 (pre-existing; its tests run under it) · MEDIUM**
- **Where:** `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` imports `main` at collection time, which runs the `src/main.py:231` init. That init has traces at 1.0, profiling at 1.0 and logs enabled.
- **What's wrong:** confirmed. With a DSN exported, tests that import `main` start the **real** SDK.
- **Evidence:**
  - I pointed `SENTRY_SDK_DSN` at a sink on 127.0.0.1. The 9 files that import `main` (141 passed) sent 25 envelopes: 24 error events and 1 log batch.
  - All 24 events come from the `juniper_cascor.api` logger, in `test_auto_start_shortfall.py` and `test_allow_truncated_datasets.py`, once an earlier import has started the client: 16 "Auto-start training failed", 7 "Auto-start failed", 1 "artifact carries NEITHER a validation split".
  - The lifespan in `TestNonAsciiApiKeyThroughTheApp` would also start it if `JUNIPER_CASCOR_SENTRY_DSN` were exported.
- **Fix:** put this at module level in `src/tests/conftest.py`, after line 37:

  ```python
  for _v in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN"):
      os.environ[_v] = ""
  ```

  Set them empty rather than deleting them, so `load_dotenv()` (which does not override) cannot re-inject a DSN, and subprocess probes inherit the empty values. Tested on a scratch copy: 251 passed, and the sink stayed at 26 posts with both DSNs pointed at it.

**F5 · all three · LOW**
- **Where:** `_ENCODING_PROBES` at `juniper-service-core/tests/test_security.py:101`, `juniper_data/tests/unit/test_security.py:34`, `src/tests/unit/api/test_api_security.py:31`.
- **What's wrong:** the claim just above each (lines 99, 32, 29), "Only an encoding that is both total and injective gives validate(x) == (x in keys) for every pair below", is false.
- **Evidence:** UTF-16-LE with `surrogatepass` never raises but is not injective: U+1F511 and the pair U+D83D U+DD11 both become `=\xd8\x11\xdd`. That mutant passes service-core 629/629, data 72/72, cascor 114/114 and the drift gate. It is not exploitable, because headers cannot carry surrogates.
- **Fix:** add `"\ud83d\udd11"` to the probes; my probe catches the mutant with it.

**F6 · ml#2086 · LOW**
- **Where:** `juniper-observability/tests/test_sentry.py:122-124` (`_frames`).
- **What's wrong:** no test frame has `in_app: false`.
- **Evidence:** a mutant that strips `vars` only from `in_app` frames survives 33/33. In production the finding's frame is library code: installed service-core shows `validate in_app=False has_vars=True`.
- **Fix:** add `in_app: False` frames to `_frames`, plus one wire test with `in_app_exclude`.

**F7 · cascor#689 · LOW**
- **Where:** `src/tests/unit/test_main_sentry_no_local_variables.py:33-35`.
- **What's wrong:** the AST check only matches calls spelled `sentry_sdk.init`.
- **Evidence:** a second init through `from sentry_sdk import init as _x`, with locals on, fails 0 of 114 tests.
- **Fix:** a behavioural subprocess test with a local DSN that runs `import main` and asserts `get_client().options["include_local_variables"] is False`. My probe did exactly this: `False` at head, and at base `True` with the secret on the wire twice.

**F8 · all three (pre-existing drift gate) · LOW**
- **Where:** the gate comment at `tests/test_service_fork_drift.py:207`.
- **What's wrong:** adding `break` after `matched = True` keeps both drift markers.
- **Evidence:** the mutant survives service-core 629, data 72, cascor 114 and the gate. The comment says "no behavioural test can tell them apart", but a spy that counts `compare_digest` calls can.
- **Fix:** the F3 spy.

**F9 · all three · NIT**
- **Where:** the commit body and the CHANGELOG entries.
- **What's wrong:** they say a "4001 close"; on the wire, a rejected WebSocket handshake is HTTP **403**, because the socket closes before accept.
- **Evidence:** real uvicorn at head returns 403 for every non-ASCII key and 101 for the valid one; base returns 500.
- **Fix:** say "rejected: ASGI close 4001, HTTP 403 on the wire".

**F10 · ml#2086 · NIT**
- **Where:** `juniper-observability/CHANGELOG.md`, "Consumers inherit both on upgrade, with no code change".
- **What's wrong:** each consumer's lock pins `juniper-observability==0.4.0` (data `requirements.lock:88`, cascor `:63`, canopy `:79`), and canopy caps it at `<0.5.0`. Each needs a lock refresh and a 0.4.x release before it gets the fix. The data and cascor CHANGELOGs already say this correctly.

## Attacks that did not land
- **Compare correctness (all three copies):**
  - 0 failures over every code point U+0000–U+10FFFF, 17 adversarial pairs in both directions (surrogate pair vs astral, escape twins, NUL, whitespace, 100k-long strings), and 200k random strings.
  - A spy confirmed 7 keys give 7 bytes-only compares for every input.
- **The `surrogatepass` deviation is justified:**
  - Every code point encodes to distinct bytes and the code is prefix-free, so it is injective.
  - `surrogateescape` raises on U+D800 and maps é and U+DCC3 U+DCA9 to the same bytes.
  - A lone surrogate written as a JSON escape in `JUNIPER_DATA_API_KEYS` or `JUNIPER_CASCOR_API_KEYS` really does survive both services' settings parsing.
- **Timing:** time follows only the configured key's length. Presented keys of 1 to 2e6 bytes against a 1e6-byte key all take 677–708 µs. A 16 to 2e6-byte configured key takes 0.1 to 1351 µs. First-byte mismatch, last-byte mismatch and a match are all 638–665 µs.
- **Real uvicorn, both parsers, every single-byte key plus special cases, on service-core, data and cascor at head:**
  - 0 responses of 500; h11 gave 258×401 and 3×400, httptools 231×401 and 30×400.
  - WebSocket 403, and no exception logs.
  - Controls with the base compare gave 133×500 plus WebSocket 500, with 133–137 events carrying `"candidate":"'…LEAKMARK…'"`.
  - Base compare with head observability: 137 events, 0 frames with vars, 0 secrets.
- **Sentry, sdk 2.58.0 and 2.70.0:**
  - Chained exceptions, ExceptionGroup, `logging.exception`, `stack_info`, threads, asyncio tasks, and an event processor that writes vars are all clean, both as shipped and with only the `before_send` hook active.
  - The observability tests pass on 2.54.0, 2.58.0, 2.69.2 and 2.70.0.
  - The PureEval claim is accurate (`pure_eval.py:77`).
  - `extra` and log-message text still carry anything put in them, but the PR does not claim to cover those.
- **Direct `sentry_sdk.init` calls:** only cascor `src/main.py:231`. Canopy (`src/observability.py:58`), data (`api/app.py:46`) and cascor's service path (`api/app.py:335`) all delegate to `configure_sentry`. `server.py` never imports `main`, and recurrence has no Sentry.
- **Drift gate:**
  - On a synthetic ecosystem root holding all four copies: 11 passed, 58 subtests passed.
  - A negative control fails as it should.
  - All four markers are present in all four copies.
- **CHANGELOGs:** data#440 against `0f0f7e0e` is `122a123,160` only: 38 lines added, none lost (data main equals the base). Cascor's is `510a511,551` only. The claimed new-test counts match: service-core 565→629, observability 130→148, data 61, cascor 62.
- **Suites, with DSNs unset:**

  | Suite | Result |
  |---|---|
  | service-core | 629 passed |
  | observability | 148 passed |
  | data CI lane | 1801 passed |
  | data `test_security.py` | 72 in CI lane, 116 in total |
  | cascor CI lane | 5444 passed |

**Housekeeping:**
- I changed no repository files. My only shared-state actions were `git fetch origin pull/2086/head` and `git fetch origin main`, run from my worktree.
- Every string I wrote as `\uXXXX` in a probe file was turned into the literal character on the way in, so a surrogate-pair escape became one astral character. I rebuilt those probes with `chr()`. The PR test files do contain real escapes; I checked with `od`.
- The probe scripts are in the scratch folder `vbytes/` and will be lost with the session. Copy them to `juniper-ml/util/ad-hoc/` if you want to keep them.
