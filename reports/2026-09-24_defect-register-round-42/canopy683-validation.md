<!-- Archived verbatim 2026-09-24 from subagent ac6e0cc793b7c6adb of session bc31e993 (final message). -->

## Validation of juniper-canopy#683 at `8917fdac` (not merged)

**Verdict:** everything #683 claims reproduces. The fix is complete for `CANOPY_API_KEY`. But the same leak is still open for canopy's three *outbound* keys (HIGH, not introduced by #683). A second path, also older than #683, puts the real canopy key into Sentry on one anonymous request (HIGH). There are two LOWs.

The earlier validation I checked against is `reports/2026-09-24_defect-register-round-42/canopy678-postmerge-validation.md`. **Changed:** nothing in any repo or worktree; all work is in `…/scratchpad/v683/`.

### Findings

**1. HIGH (older than #683, outside its diff): the leak #683 closes for `CANOPY_API_KEY` stays open for the cascor, data and recurrence keys, and the cascor key is served to callers with no key.**
- **Where** (`file:line` at `8917fdac`):
  - Keys read raw from the env: `src/backend/__init__.py:95` (`JUNIPER_CASCOR_API_KEY`, falling back to `JUNIPER_DATA_API_KEY`); `src/settings.py:486-489` (data) and `:544-547` (recurrence).
  - Logged: `cascor_service_adapter.py:2030` (ERROR on every status-refresher tick), `:1542`, `:1560`; `demo_mode.py:560`, `:1114`, `:1128`, `:2028`; `recurrence_backend.py:221`; `main.py:1948` (DEBUG).
  - Returned in API bodies: the adapter's `{"error": str(e)}` returns; `service_backend.py:201` → `main.py:3712` (also written to system.log) and `:3714` (the 409 body); `recurrence_backend.py:219` → `:287` (`completion_reason` in `/api/status`).
- **What:** each client quotes the key when it refuses to send it:
  - `requests` raises `InvalidHeader` (cascor REST and the data-client).
  - httpx/h11 raises `Illegal header value b'…'` (recurrence). It is stricter than `requests` and also refuses trailing spaces and VT.
  - websockets 17.1, the lockfile version, raises `invalid X-API-Key header: <raw value>` for CR/LF, VT or non-latin-1, with the newline unescaped. websockets 16.0 in the dev env writes the CR/LF onto the wire instead.
- **Evidence** (`e2e_other_secrets.py`: fresh interpreter, real lifespan, both envs):
  - `JUNIPER_CASCOR_API_KEY=" LEAKME-cascor-key-2"`: 8 log records, e.g. `[ERROR] …cascor_service_adapter: Failed to get training status (refresher): … header value: ' LEAKME-cascor-key-2'`. One line in `logs/system.log`. The `GET /api/status` body carries `"error":"… ' LEAKM…"`, and so does the `POST /api/train/start` 409.
  - With canopy auth **enabled** (a real `CANOPY_API_KEY`) and `JUNIPER_CASCOR_API_KEY="…-key-6\n"` (the trailing newline a k8s secret leaves; `e2e_anon_extract.py`):
    - A keyless `/api/status` gets 401.
    - A keyless `GET /api/csrf`, then `POST /api/train/start` with `Origin: http://localhost:8050`, returns `409 {"detail":"Training could not be started: … 'LEAKME-cascor-key-6\\n'"}`.
    - Identical on `5907713b`.
  - `JUNIPER_DATA_API_KEY=" LEAKME-data-key-1"` logs `[ERROR] demo_mode: JuniperData create_dataset failed: … ' LEAKME-data-key-1'` plus a WARNING. With a DSN configured, 2 Sentry envelopes carry it; the ERROR level makes it a Sentry *event*.
  - `JUNIPER_RECURRENCE_API_KEY="LEAKME-rec-key-5 "` (trailing space, which `requests` would send) logs `[WARNING] … recurrence fit failed: … Illegal header value b'LEAKME-rec-key-5 '`, and `/api/status` serves it too.
- The CHANGELOG entry is correctly limited to `CANOPY_API_KEY`. The PR title ("a padded key can no longer leak into the logs") claims more than that.
- **Fix:** validate each outbound key where it is read (`backend/__init__.py:95` and the two settings validators). Log a WARNING naming the variable, and do not send a key where `key != key.strip()` or any character falls outside 0x21–0x7E (the union of the three clients' rules). Stop returning transport exception text in API bodies (`service_backend.py:201`, `main.py:3714`, the status envelope's `error`); return the type name only. At minimum, retitle the PR and file the rest as an issue.

**2. HIGH (older than #683): one anonymous request writes the real `CANOPY_API_KEY` into Sentry.**
- **Where:** `src/security.py:113-117`; `juniper_observability/sentry.py`, whose `before_send` scrubs only request headers while the SDK's default `include_local_variables=True` stays on.
- **What:** `hmac.compare_digest` on `str` raises `TypeError` for non-ASCII input. The frame's local `candidate` holds the configured key. The scrubber filters `api_key` but not `candidate`. The PR's own comment (`security.py:72-73`) records this as harmless: "a 500, never a match".
- **Evidence** (`sentry_probe.py`: real uvicorn 0.53.0, sentry-sdk 2.69.2, DSN pointed at a local sink):
  - A raw `GET /api/status` with `X-API-Key: \xa0` gets a 500.
  - The error envelope's vars are `"api_key":"[Filtered]","matched":"False","candidate":"'real-canopy-key-REALKEYMARK-7f3a'"`.
  - Same on base and under h11.
  - A configured key ending in NBSP, which the PR's tests expect to be sent as set, sends every keyed self-call down the same path.
- **Fix:** compare bytes (`hmac.compare_digest(api_key.encode("utf-8", "surrogateescape"), candidate.encode(…))`), or treat `TypeError` as no match. Keep `matched = False` / `return matched`, which the juniper-ml drift gate needs. Also pass `include_local_variables=False` in the shared `configure_sentry`, and check the forks that copy this loop.

**3. LOW: only one test sample pins `_docs_enabled` (`src/main.py:517`), and two new mutants survive all 7020 CI-lane tests (`my_mutations.py lane`).**
- **M2**, which strips only ASCII whitespace: with an NBSP-only env key, the docs return 404 while `/api/status` serves keyless (head returns 200). That is the defect #683 fixes, brought back for non-ASCII blank keys.
- **M3**, which reads the env var and ignores `CANOPY_API_KEY_FILE`: with a real key only in the file, `/openapi.json` with the key returns 200 (head returns 404).
- **Fix:** `_docs_enabled = not get_api_key_auth().enabled`, so there is one rule. Add tests that expect docs 404 for a real env key and for a real key file, and docs 200 for every blank-key case.

**4. LOW: the padded-key WARNING names the wrong variable for a key file with an interior line break, and a comment says this cannot happen.**
- **Where:** `src/security.py:350` says "Only the env var can be padded". The text at `:355-358` hard-codes `CANOPY_API_KEY`. `:384` records the source as `CANOPY_API_KEY_FILE`, but nothing reads it.
- **Evidence** (`file_linebreak_probe.py`): a key file containing `part1\npart2\n`, with the env var unset:
  - auth is enabled, and the recorded source is `CANOPY_API_KEY_FILE`;
  - the WARNING says "CANOPY_API_KEY has leading or trailing whitespace…";
  - the self-call sends no key.
- **Fix:** word the WARNING per source, as the blank-key WARNING already is, and correct the comment.

### Attacks that did not land
- **`CANOPY_API_KEY` outbound:**
  - It is read in exactly four places (`security.py:378`, `internal_api.py:91`, `main.py:353`, `main.py:517`). Only `internal_api` builds a header from it; no URL, cookie or WebSocket use exists.
  - The per-process internal token is url-safe.
  - The census reproduces: 64 sites, of which 42 log the text and 12 log text plus type, i.e. 54.
- **The `requests` check is the right one:**
  - Path: `Request.prepare()` → `models.py:570` → `check_header_validity` (`utils.py:1087`) → the regex `^\S[^\r\n]*\Z|^\Z` (`_internal_utils.py:16`).
  - It refuses leading (Unicode) whitespace and any CR/LF. It accepts trailing whitespace and non-ASCII.
  - The only other check that quotes the value, at `http/client.py:1335`, is unreachable after it.
  - The accepted side is pinned by `test_a_key_requests_sends_goes_on_the_self_call_exactly_as_set`.
- **Omitting the key is not a bypass:**
  - Auth stays on: with `" real-key-1"`, 29 keyless GETs get 401 and 7 exempt ones get 200, the same as base.
  - `/api/train/*` falls to the Origin + CSRF path.
  - No configuration that used to work breaks, because every omitted key raised before reaching the server.
- **`require_auth` path** (real uvicorn):
  - A blank env or file key exits 3, as base does.
  - Exactly one blank-key line reaches stderr and `system.log`, worded for a refused boot, after the CRITICAL.
  - The traceback shape matches base, with no chaining, and the handler catches only `AuthPostureError`.
  - With the skip flag, canopy boots and logs the open-boot wording.
- **Docs exposure:** in a GET-only route sweep of base against head, across unset, `" \t "`, `""`, real and padded keys, only the whitespace-only key differs. Exactly `/docs`, `/docs/oauth2-redirect`, `/openapi.json` and `/redoc` appear, each 200 keyless. None of the other 70 pairs changes tier or status.
- **Header claims** reproduce on uvicorn 0.53.0 (the lockfile version).
- **Sentry transactions** do not carry the inbound `X-API-Key` (the SDK filters `HTTP_X_API_KEY`). Redis and Cassandra log hosts, not passwords.
- **Mutations:**
  - My M1 (a blank key also recorded as padded) is caught by 3 tests.
  - My M4 (the posture check reads the env var only) is caught by `…refuses_the_boot[file]`.
  - The builder's harness: control arm 213 passed, 21/21 caught.
- **Claims 4 and 5 hold** (the `str.strip()` wording, and six literal `get_secret` cases).
- **Docs against code:** 8 CHANGELOG lines were removed against `5907713b`, all inside #678's own entry and each replaced; no other PR's line is lost. `API_REFERENCE.md` is accurate.
- **Drift gate:** the markers are at `security.py:83` (both), `:113` and `:117`. The gate passes 11/11 against a synthetic ecosystem root.
- **Runs:**
  - CI lane: 7019 passed, 1 skipped.
  - Integration lane: 559 passed, 41 skipped.
  - `gh pr checks 683`: every check passes; "claude", "Publish manifest" and the 5 Cursor automations were skipped.
- **Merge status:** open at 10:18Z. It is now BEHIND main by #681 and #682, which touch only `CHANGELOG.md` (an entry hunk at line 121, not a release heading) among #683's files, and add no self-call. Since it has not merged, there is no squash tree to compare yet. An `update-branch` would create a new head SHA that needs re-checking.

The probe scripts are in the scratchpad (`e2e_other_secrets.py`, `e2e_anon_extract.py`, `sentry_probe.py`, `lib_probe.py`, `boot_refused.py`, `route_sweep_get.py`, `my_mutations.py`). The scratchpad is temporary, so copy them to `juniper-canopy/util/ad-hoc/` if they should be kept.
