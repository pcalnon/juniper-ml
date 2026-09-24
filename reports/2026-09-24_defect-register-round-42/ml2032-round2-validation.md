<!-- Archived verbatim 2026-09-24 from subagent ad656809d6e1f3e92 of session bc31e993 (final message). -->

No preamble, as requested. Line references use these names:

- **REG** = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` at the PR head f062a6f0.
- **R40** = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md`.
- **R41** = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md`.

Sibling repos were read at origin/main: canopy 9fbd697a, data-client 9bc8870, deploy main. juniper-cascor moved from 0d2d826 to e052ef8 during the run; every claim holds at both, and the line numbers below are at e052ef8.

## Claim table

| | Verdict | Evidence |
|---|---|---|
| a | **VERIFIED** as a mechanism, but it gives an attacker nothing (see H1). | canopy `src/main.py:712` falls back from the header to `query_params.get("api_key")`. `src/secrets_util.py:62` strips a secret file; `:64` returns the env var raw. Probed in JuniperCanopy1: `QueryParams("api_key=+++")` → `'   '` (starlette 1.3.1). h11 0.16.0 and httptools 0.8.0 both return `b''` for `X-API-Key:    ` and for `\t \t`. canopy#660 is still **OPEN**, so this is live on canopy main, not "before". |
| b | **VERIFIED** | `src/settings.py:435` sets `require_auth: bool = False`. `src/security.py:352-354` returns before the Origin check (`:365`) and CSRF check (`:369-374`). Every `/api/train/*` route depends on it (`src/main.py:3658-3846`). |
| c | **VERIFIED** | `src/frontend/internal_api.py:59-60` and `:76-78` send the key. requests 2.34.2 raises `InvalidHeader: Invalid leading whitespace … '   '`. #660 changes only `CHANGELOG.md`, `src/security.py` and `src/tests/unit/test_security.py`. |
| d | **VERIFIED**; the job-level consequence the register draws from it is not (M4). | `tests/test_service_fork_drift.py:264` requires every member; `:352-353` skips when no root is found. `.github/workflows/docs-full-check.yml:110` ends the clone with `\|\| echo "WARNING…"`. Reproduced against main snapshots: as-is, 8 OK; widened with canopy present, 8 OK, 0 skips; widened with canopy absent, `OK (skipped=3)`. |
| e | **VERIFIED**, all parts | Date: REG:1323 heads "OWNER RULINGS, 2026-09-09", and `APD-CASCOR-008` sits under it at REG:1350; REG §2.4 (2026-09-11) never names it. Resolver callers: `app.py:543` and `manager.py:4205`. Auto-start: created once at `app.py:420-424`; its docstring (`:490-497`) says "Failures here are still SWALLOWED". Lock: both `_reload_dataset` callers are inside `with self._lock` (`:2335`→`:2364`, `:3164`→`:3252`). URL: `:4188` builds a fresh `Settings()` on every call. Client defaults: data-client `constants.py:193-194` (30 s, 3 retries), and GET is retried (`:212`). Remedy: `:3778` and `:3785` give the knob remedy when no opt-in went on the wire. |
| f | **VERIFIED** | service-core `security.py:73-77` has the loop, but the guard's only sites are data and cascor (`test_service_fork_drift.py:172-173`). No test under `juniper-service-core/tests/` checks it. `juniper-service-core/CHANGELOG.md:27-30` describes it as a marker in the gate. |
| g | **VERIFIED** | REG:1303-1304. juniper-ml#1974 merged 2026-09-21T13:09:18Z (commit ea24a19a) and added the guard with `status=ENFORCED` directly. |
| h | **VERIFIED** | R41:219-221: "whether `APD-ECO-008`'s gate analysis has a cheaper option nobody proposed". |
| i | **VERIFIED** as fact; the register's conclusion from it is not (M3). | The session transcript `…happy-skipping-hollerith/bc31e993-….jsonl` line 306 (the AskUserQuestion call) shows exactly the four labels. R40:168-171 frames the question as "Fail closed, fail open, or cache the last-known set". |

## New defects, by severity

### HIGH

**H1. REG:1278** *"(Refuted 2026-09-22 for the WebSocket path … a whitespace-only env key authenticated `/ws?api_key=+++`. Over HTTP the reading holds…)"*, and **REG:1476-1480** *"It did not fail closed everywhere … Over the WebSocket path it did not … the 'key' was trivially guessable there."*

- **Why it's wrong:** the mechanism is real, but the security conclusion does not follow. All three canopy WebSocket endpoints call `_authenticate_websocket(..., allow_browser_auth=True)` (`src/main.py:776`, `:913`, `:3576`). That function returns True for any connection with no key at all (`:713-714`).
- Every later gate applies to keyed and keyless connections alike: the bearer opt-in, the Origin allowlist, the connection caps, and the `/ws/control` CSRF frame (`:780-796`, `:917-933`, `:973`, `:3580-3596`). So `?api_key=+++` gets exactly what sending no key gets, whatever the configured key is.
- With `ws_auth_enabled=true` (`src/settings.py:383`), the bearer path strips and drops whitespace parts (`:743-747`), so the WebSocket path fails closed outright.
- The "probably not an auth bypass" reading therefore holds on both paths. Only its stated reason is refuted: a whitespace key *can* be presented.
- Two smaller inaccuracies: `+++` matches only a key of exactly three spaces, and the key gate admits any keyless client, not just browsers.
- As written, the canonical row asserts a live canopy WebSocket auth bypass on an open `M` row, which reads against REG:182 ("Every `Security` entry … `FIXED`").
- **Fix:** say the reason is refuted but the conclusion stands. All three endpoints admit keyless connections and gate keyed and keyless connections identically, so presenting the key gained nothing. Drop "trivially guessable".

### MEDIUM

**M1. REG:1490-1492** *"'without it' is the default configuration, not an edge"*

- **Why it's wrong:** that is only the code default. In juniper-deploy, `docker-compose.yml:690` supplies the key as `CANOPY_API_KEY_FILE`, which is stripped, and `:696` defaults `JUNIPER_CANOPY_REQUIRE_AUTH` to `true`. The demo (`:791`) and dev (`:882`) services set no key at all.
- No deploy profile reaches the changed configuration. Only a bare launch with a whitespace-only `CANOPY_API_KEY` env var does. This sentence sizes the change for the owner.
- **Fix:** state both defaults and that scope.

**M2. PR #2032's body was never updated.**

- It still says "the 2026-09-11 ruling", "a key no client can present (every request refused)", and "The one real cost is … a canopy checkout". f062a6f0 corrected all three.
- The PR has no comments or reviews, so this body is the owner's only surface. That contradicts REG:1473-1474, "surfaced to the owner rather than folded in silently".
- The repo squashes with `COMMIT_MESSAGES`, so main will also get the first commit's "the fetch is lazy, so no startup dependency".
- **Fix:** rewrite the body with `gh api -X PATCH …/pulls/2032`.

**M3. REG:1379-1383** *"The 2026-09-21 framing … named fail-closed, fail-open and a cached set; only the last reached the owner as such."*

- **Why it's wrong:** R40:168-171 frames the question at startup ("when juniper-data is unreachable at startup"). In that framing:
  - "Refuse to start" was offered ("refuse to boot if juniper-data can't be reached"), and it *is* the fail-closed option.
  - "Fall back to built-in set" was offered ("The opt-in is always forwarded"), and it is a fail-open variant.
- All three shapes reached the owner. Only the per-request forms (fail the individual request, or forward the opt-in for every generator) did not.
- The sentence also cites R40 by date with no filename.
- **Fix:** name the file and restate which forms were and were not offered.

**M4. REG:1466-1468** *"…silently switch off the whole cross-repo gate … while the weekly job stays green."*

- **What holds:** the drift test itself does go silent (reproduced: `OK (skipped=3)`).
- **What doesn't:** the job would not stay green. The cross-repo link step (`docs-full-check.yml:125-128`) runs before the drift step (`:256-259`), which has no `if: always()`. `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md:7` links into juniper-canopy.
- The published juniper-doc-tools 0.1.2, the version the workflow installs, exits 1 on an ecosystem without canopy: "file not found in juniper-canopy".
- Also unstated: the same whole-gate skip already happens today if the juniper-data or juniper-cascor clone fails.
- **Fix:** say the job goes red today only because of that unrelated link, which is a coincidence rather than a guard. Keep the requirement to anchor the root probe on the original two forks.

### LOW

1. **Wrong count (REG:1363):** "**Three** implementation constraints", followed by items (1) to (4) at REG:1364-1375. The correction introduced this.
2. **Overbroad HTTP claim (REG:1477-1478):** "a route that checks the header refuses every caller". `/api/train/*` (`src/security.py:343-374`) and `/api/csrf` (`src/main.py:676-692`) both check the header, yet admit a keyless same-origin browser. The defaults are `browser_control_auth_enabled=True` (`settings.py:376`) and `csrf_enabled=True` (`:366`). REG:1492-1494 itself says Origin + CSRF protected `/api/train/*` before the fix. Scope the sentence to routes behind `SecurityMiddleware`'s key gate.
3. **Stale counts in §2.3:**
   - REG:240 "Fifteen entries share one shape" is now 16, because this PR's new table row adds `APD-CASCOR-005`. It is 17 if `APD-ECO-008` counts, as the correction's REG:242 implies.
   - REG:298 "six of the fifteen" needs updating to match.
   - REG:181 "all three §2.3 drift groups are now closed" is unqualified, while REG:242 now scopes that closure and names an open member.

   The correction's count sweep missed all three.
4. **Wrong warning named (REG:1483-1484):** with `JUNIPER_SKIP_AUTH_POSTURE_CHECK` set, the posture check logs "Auth posture check SKIPPED …" (`auth_posture.py:107-111`), not "running OPEN" (`:124-127`).
5. **Misattributed quote (REG:1366):** the phrase "A DEFAULT, NEVER AN OVERRIDE" is in the caller (`app.py:539`). The resolver's comment reads "A DEPLOYMENT DEFAULT, NOT AN OVERRIDE" (`manager.py:3941`).
6. **Branch description (REG:1371-1372):** "no caller stance" is not what the branch tests. It tests key absence (`manager.py:3935`), and `_as_bool_stance` maps `None` and `""` to no stance (`:3884-3891`). An implementer following the gloss would change behaviour for `allow_truncation: null`.
7. **Startup dependency (REG:1376-1379):** "removes a startup dependency only on the first" does not fit the same sentence's "a failure is tolerated"; a boot-time fetch that may fail is not a dependency. The option the owner chose said "Adds no startup dependency", and the entry does not reconcile the two. Auto-start also already waits for juniper-data to be ready (`app.py:523`).
8. **Tense and dates:** "authenticated" and "before the fix" describe a condition that is still live, since #660 is OPEN. REG:253-254 ("lagged it until 2026-09-22") and REG:1613 ("the table gained its row 2026-09-22") will be wrong on main, which gets the row only when #2032 merges; it is still open on 2026-09-23.
9. **Documents cited without a filename:** "its CHANGELOG" (REG:1498) should be `juniper-service-core/CHANGELOG.md`. "The 2026-09-21 framing" (REG:1381) should name R40.
10. **Unrecorded residue (REG:1496-1498):** the unwatched service-core copy is recorded in prose only. The register's own `APD-DATA-052` row (REG:1276) says an item with no row is invisible to every count. Also, "One copy stays unwatched" covers only the compare, not the whole class. Canopy has no `FailedAuthThrottle`, and its body limit checks Content-Length only (`src/middleware.py:59-74`), which is the CR-024 shape. The register records neither. I did not check whether the canopy F-CANOPY ledger does.

## Attacks that did not land

- **Scripts at the PR head** (run on a scratch copy of f062a6f0):
  - `register_status_crosscheck.py`: 126 rows, 99 FIXED, 99 ids in the §2 list, 99 verification rows, AGREE, exit 0.
  - `register_open_set.py`: `126 rows | 99 fixed | 27 open` (DATA 15, ML 5, ECO 4, CASCOR 2, RCLIENT 1).
  - Both give the same result on main.
  - The three register test suites: 33 tests OK.
  - CI on the PR: 21 checks pass, the rest skipped.
- **Markdown:** all 32 tables have matching unescaped-pipe counts. The `APD-ECO-008` row is a single line with 7 pipes, like its table. There are no stray block starts in the edited list items, and bold/italic markers balance.
- **Widening measurement:** 8 tests, 0 failures, 0 skips, reproduced. The correction's caveat that this equality is trivial is accurate. The anchoring requirement is sound: with the probe anchored on data and cascor, a missing canopy fails `test_fork_files_named_by_the_registry_exist`. #660 carries both guards' markers (`src/security.py:69`, `:99`, `:103`).
- **Filter forms in the ECO-008 row:** data uses `list(dict.fromkeys(…))` (`juniper_data/api/security.py:73`); cascor (`src/api/security.py:40`) and service-core (`security.py:45`) use set comprehensions. Canopy does configure exactly one key (`src/security.py:266`). The posture check's `real_keys` behaves as described.
- **Truncation defaults:** "errs toward refusing partial data" holds (`juniper_data/core/limits.py:138-139` are both `False`). The comment that a non-truncatable generator would ignore a forwarded opt-in holds: `PartitionParams` does not forbid extra fields.
- **"True when written, 2026-09-21" (REG:1396):** holds. REG:123-124 still says `APD-DATA-019` needs an owner decision, but its row (REG:788) says RULED 2026-09-09. That stale sentence predates this PR and is out of scope.
- **Filing dates:** `APD-ECO-008` was filed 2026-09-22 (ml#2005) and `APD-ML-002`…`006` the same day (ml#2026).
- **Constraint (4)'s "minutes":** defensible, since a retried GET can take 4 × 30 s plus backoff. The lock also blocks `cancel_swap`, which strengthens the constraint.

**Changed:** no repository files. I wrote scratch files only, into the shared scratchpad root (`corr.diff`, `c1.diff`, `register_head.md`, `register_c1.md`, `register_main.md`) and `scratchpad/r2val/`. I ran `git fetch` in five sibling repos. I created a temporary ref `refs/remotes/origin/pr-660-r2val` in juniper-canopy and deleted it.
