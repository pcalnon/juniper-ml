<!-- Archived verbatim 2026-09-24 from subagent a37985f805c0f3270 of session bc31e993 (final message). -->

## Defects

Paths are relative to `/home/pcalnon/Development/python/Juniper/juniper-canopy` and were read from git objects at the SHAs named, not from its working tree.

PR #660 is already merged (squash `3a6dea95`, 2026-09-23T19:16:49Z), so every fix below needs a follow-up PR.

### HIGH: the corrected disclosure leaves out the biggest thing that opens

**The claim.** `CHANGELOG.md` [Unreleased] › Security (the text now on main) says "What opens is the posture canopy documents for no key at all:" and then lists three bullets: the `/api/train/*` and `/api/csrf` Origin/CSRF loss, `ws_auth_enabled=true`, and the WebSocket `?api_key=` non-exposure. The PR body's "What opens" section lists the same three and calls the WebSocket bearer item "a second closed-to-open change".

**Why it's wrong.**
- **Before:** a whitespace key enabled auth on a key no ASCII header can carry, so `SecurityMiddleware` (`src/middleware.py:128`) refused every caller on every route outside the exempt and key-exempt sets.
- **After:** those routes have no auth at all.
- The 27 state-changing routes outside `/api/train/*` have no route-level auth dependency. The key gate was their only control.
- The correction also deleted the old entry's sentence "That key refused every HTTP request", which carried this, and put nothing in its place.
- Reach is small (only a bare launch with a whitespace-only env var), but explaining what opens was the whole point of the correction.

**Evidence** (scratch copies run with `CANOPY_API_KEY=$' \t  '`, demo mode):
- Sweeping `app.routes` finds 55 key-gated (method, path) pairs; 27 of them change state. Examples: `/api/set_params`, `/api/model/select`, `/api/admin/experimental_functions`, `/api/dataset/*`, `PATCH /api/v1/network/weights`, snapshot restore/retrain, `/api/remote/*`.
- On the pre-PR base `26e0546f`, all 25 parameterless GETs return 401. On the correction `246f1bf2`, all 25 return 200.
- Keyless POSTs from `Origin: https://evil.example` go from 401 to 400/422, meaning they passed auth and failed only on the empty body.
- A cross-site "simple" POST (`text/plain`, empty body) to `/api/dataset/generate` goes from 401 to **200 with a regenerated dataset**. That handler reads `await request.json()` whatever the Content-Type (`src/main.py:1642`), so it is a seventh route a hostile page can hit, beyond the "six" `/api/train/*` POSTs.
- The PR body says the owner re-confirmed the semantics "after being told the Origin/CSRF consequence". The juniper-ml register draft in this worktree (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, uncommitted) does say "That opens the keyed HTTP routes". Neither #660 file says so.

**Fix.** Add a leading bullet to that CHANGELOG entry: while the whitespace key was set, every key-gated route (55 pairs, 27 state-changing) refused every client; now all of them serve anyone who can reach the port, and `/api/dataset/generate` accepts a cross-site simple POST. Mirror it in the PR body, and put it to the owner if it wasn't.

### MEDIUM: main's commit message for #660 is the text the correction replaced

**The problem.** The squash message on `3a6dea95` is the auto-merge body stored when auto-merge was armed at 13:17:53Z. That was 3m22s before the correction was committed (13:21:15Z), and it was never re-armed. So main's history:
- keeps "the WebSocket ?api_key= query parameter, never trimmed, could still present it", which the correction retracted;
- says "One real behaviour change" and never mentions the Origin/CSRF loss, the `ws_auth_enabled` change, or the new WARNING (code on main that its commit never describes);
- keeps the unqualified "as juniper-service-core and juniper-cascor already do", although service-core 0.7.0 still ships `any()`.

**Evidence.** `autoMergeRequest.enabledAt` and `commitBody` from `gh pr view 660`, compared with `git show 3a6dea95` and the commit dates.

**Fix.** Main can't be rewritten. Note in the register row or the next release notes that the CHANGELOG entry supersedes this commit message. In future, re-arm auto-merge after pushing any correction that changes the PR body.

### LOW: the new WARNING goes out before logging is set up

**The problem.** `get_api_key_auth()` first runs at import (`api_key_auth = get_api_key_auth()`, `src/main.py:528`). `configure_logging` only runs later, inside `lifespan` (`src/main.py:310`). Both launch paths import first: the Dockerfile's `python src/main.py` (line 126) and `uvicorn main:app`, whose uvicorn 0.49.0 logging config doesn't touch the root logger.

**Evidence.**
- After `import main`, the root logger has no handlers.
- stderr holds exactly one line: the bare message, with no level, logger name or timestamp. That is Python's fallback handler for unconfigured logging.
- It isn't JSON when JSON logging is on, it doesn't reach Sentry, and it never reaches `logs/system.log`, the log location canopy's `AGENTS.md` documents. After my probes that file held 14 "running OPEN" lines and 0 blank-key lines.
- The test uses `caplog`, which puts a handler on the root logger and hides all of this.

**Fix.** Keep the single read in `get_api_key_auth()` but only set a flag there. Log the warning from `lifespan` through `system_logger`, right after `enforce_auth_posture`, without reading the secret a second time.

### LOW: the WARNING can't say which source was blank, and its advice is wrong for the file

**The claim.** "Set a real key, or unset CANOPY_API_KEY for an intentional open profile."

**Why it's wrong.** `get_secret` lets a blank file named by `CANOPY_API_KEY_FILE` override the env var.

**Evidence.** With a blank file plus `CANOPY_API_KEY=real-key-abc`, auth is disabled and the WARNING tells the operator to unset their real key. After unsetting it, auth is still disabled and the WARNING still fires.

**Fix.** Detect the file source and word the message for it.

### LOW: the tests don't pin two things the PR body says they pin

- **"Exactly one WARNING" is only checked for a single call.** A mutant that logs on every call passes 4/4.
- **The "no whitespace in the message" check is weak.** A mutant that logs `%r` of the value passes 4/4, because `repr` escapes the tab and U+2003. In the `[file]` case the check can never fail, because the value is already `""`.
- Runtime behaviour is correct, and the branch can only ever hold whitespace, so nothing secret can leak. **Fix:** call `get_api_key_auth()` twice and assert exactly one record, and assert the exact message text.

### LOW: "a key no HTTP header can carry" is only true for ASCII spaces and tabs

- `str.strip()` also empties U+00A0 and U+0085.
- Both h11 and httptools pass those bytes through (`b'\xa0'`, `b'\x85'`), and Starlette decodes them as latin-1.
- So before the fix, a key made only of those characters could be presented and worked. The fix opens it (the WARNING does fire).
- **Fix:** limit the wording in the `src/security.py` comment and the CHANGELOG to spaces and tabs, or name the exception.

### LOW: the API reference wasn't updated

`docs/api/API_REFERENCE.md:84-85` still says "If `CANOPY_API_KEY` is set, keyed callers must send `X-API-Key`". That is now false for a whitespace value; it was already false for an empty one.

### Outside #660, but in this worktree

The uncommitted juniper-ml gate change, `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/tests/test_service_fork_drift.py`, describes `blank-api-key-filter` as "a whitespace-only env key enables auth that canopy's untrimmed WebSocket ?api_key= fallback then accepts (canopy) -- strictly worse than auth being off".

That contradicts #660's correction and the register draft beside it. For canopy, the old key left HTTP more closed than auth-off, and WebSocket behaviour was identical.

## Attacks that did not land

**The WARNING (claim 1)**
- **Leaking the value:** not possible. The message is a constant with no arguments, and the branch is only reachable with `""` or whitespace.
- **Firing more than once:** it fires once per process. I counted one warning after import, three more calls, the lifespan and five requests. `reset_security_state()` is only used by tests, import is single-threaded, and nothing in the source re-imports `main`.
- **Firing for a real or unset key:** it doesn't. The `[None]` and `[real-key]` guard tests catch the two relevant mutants.
- **A second read that could diverge:** there isn't one. The warning checks the same value that built `APIKeyAuth`.
- **Logger name:** `juniper_canopy.security` matches `.csrf`, `.ws_security`, `.health` and `.discovery`.

**Disclosure claims confirmed by running the code (claim 2)**
- Origin/CSRF, before → after:
  - `POST /api/train/pause` from a disallowed origin: 403 → 200 `{"status":"paused"}`.
  - `GET /api/csrf` from a disallowed origin: 403 → 200 with a token.
  - `GET /api/train/status`: 403 → 200.
  - All six POSTs and the status GET go through `require_browser_control_auth`.
- `ws_auth_enabled=true`: before, every connection is closed (1008/4001); after, a bearer token with any value is accepted.
- The WebSocket `?api_key=` parameter was never an exposure:
  - Keyless and `?api_key=<whitespace>` connections were both accepted, identically.
  - All three WebSocket routes use `allow_browser_auth=True`.
  - The Origin and CSRF gates don't depend on the key.
- service-core:
  - 0.7.0 is the latest on PyPI. Its wheel has the filter at `security.py:45` and `any(...)` at `:66`, and canopy's `requirements.lock` pins it.
  - The service-core, cascor and data `main` branches all have the `matched` loop. cascor#659 and ml#1974 are real and merged.
- Deploy:
  - canopy's `require_auth` defaults to false (`settings.py:435`).
  - The compose canopy service supplies the key through `CANOPY_API_KEY_FILE`, defaults `JUNIPER_CANOPY_REQUIRE_AUTH` to `true`, and has no `env_file`; the demo and dev services set no key.
  - helm also uses the file, with a non-optional secret. It doesn't set REQUIRE_AUTH, but the CHANGELOG only makes that claim for compose.
  - No deploy profile reaches a whitespace env var.

**Tests (claim 3)**
- With the previous head's `security.py` swapped in, both `[env]` and `[file]` fail with `assert 0 == 1`, and both guards pass.
- On the correction, 4/4 pass. A `%s` leak is caught by `[env]`.
- The ten files the PR body names: 244 passed.

**CHANGELOG merges (claim 4)**
- 0 lines removed and 39 added at `f7231f49` vs main, `dfd682b8` vs main, and `3a6dea95` vs `48074653`.
- One each of Added, Fixed and Security under [Unreleased], and no conflict markers.
- `git diff origin/main origin/fix/apikeyauth-sibling-parity -- CHANGELOG.md` shows changes today only because main has moved on to `894a2cc7` (#674).

**Filter and compare code (claim 5)**
- `APIKeyAuth`'s code, ignoring comments, is identical in `13eccae` and `246f1bf2`.
- All four markers (`isinstance(k, str)`, `k.strip()`, `matched = False`, `return matched`) appear exactly once at `13eccae`, `246f1bf2`, `dfd682b8`, `3a6dea95` and `894a2cc7`.

**Other measurements**
- Space/tab-only `X-API-Key` headers arrive empty in both parsers, and folded header lines can't carry them either.
- `requests` raises `InvalidHeader` on `'   '`.
- There are 64 `internal_api_headers()` calls in 9 files on current main (63 at the PR's base).
- `enforce_auth_posture` words a blank key exactly like an unset one.

**Pre-existing gaps the claim doesn't cover**
- A `CANOPY_API_KEY_FILE` naming a missing path silently falls back to the env var, with no warning.
- An env key with surrounding spaces (`" k "`) stays enabled but can't be presented over HTTP, and the posture check reports it as OK.

## CI state

- The PR is **merged** at 19:16:49Z; auto-merge was armed at 13:17:53Z.
- The merged head is `dfd682b8`, not `f7231f49`: a second update-branch merge landed at 18:59:51Z. It left `src/security.py` and the test file unchanged.
- `gh pr checks 660`: 25 pass, 6 skipping (five Cursor automations neutral, "Publish manifest" skipped), 0 fail.
- `mergeStateStatus` and `mergeable` are both UNKNOWN, because the PR is merged.
- Main's CI after the merge, on `3a6dea95`: 20 success, 3 skipped, including "Symbol & Docs Screen".

**Documents referenced:**
- juniper-canopy: `CHANGELOG.md`, `src/security.py`, `src/main.py`, `src/middleware.py`, `src/tests/unit/test_security.py`, `docs/api/API_REFERENCE.md`, `AGENTS.md`, the PR #660 body, and commit `3a6dea95`.
- juniper-deploy: `docker-compose.yml`, `k8s/helm/juniper/templates/canopy-deployment.yaml`, `k8s/helm/juniper/values.yaml`.
- juniper-ml (uncommitted in this worktree): `tests/test_service_fork_drift.py`, `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.

**Changed:** nothing in any repo. My probe scripts are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/r2v660/`, which is deleted when the session ends. They need moving to `util/ad-hoc/` if you want to keep them.
