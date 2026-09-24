<!-- Archived verbatim 2026-09-24 from subagent ab4b18fe07b799e1b of session bc31e993 (final message). -->

**Target:** PR #2032 at head `bd3284db`, which edits `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (called `DEFECT-REGISTER.md` below). Register line numbers are at that head.

## Defects, most severe first

**1. [High] The "one real cost" of widening leaves out the part that matters: without a canopy checkout, the gate silently stops checking juniper-data and juniper-cascor too.**

Quoted (`DEFECT-REGISTER.md` §4.9 park block, `APD-ECO-008` bullet, L1432-1435, repeated in the PR body):
- *"Measured 2026-09-22 against the local sibling checkouts with the tuple widened to include `juniper-canopy`: the same 8 tests, 0 failures, 0 skips, before and after."*
- *"The one real cost is that the root finder then needs a canopy checkout, which the weekly `docs-full-check` job already clones."*

Why it is wrong: the root finder needs all the repos or none, and when it finds none the tests skip rather than fail.
- `tests/test_service_fork_drift.py:264` is `if all((candidate / repo).is_dir() for repo in _FORK_REPOS)`. No canopy means no root at all.
- `:349-353`: `_require_cross_repo` calls `skipTest("ecosystem root not found …")`, even when `GITHUB_ACTIONS=true`.
- `.github/workflows/docs-full-check.yml:110`: `git clone … || echo "WARNING: Failed to clone $repo …"`. A failed clone does not stop the job.
- The job runs only on schedule or manual dispatch (`:44-47`, `:62-65`). The per-PR run in `ci.yml:493-500` skips the cross-repo tests anyway.

I ran the gate with `_FORK_REPOS` patched, from an inline heredoc with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`:
```
baseline (data, cascor)                   ran=8 fail=0 err=0 skip=0 ok=True
widened (data, cascor, canopy)            ran=8 fail=0 err=0 skip=0 ok=True
widened, canopy clone FAILED (simulated)  root=None ran=8 fail=0 err=0 skip=3 ok=True
  SKIP: test_enforced_guards_are_present_in_every_fork / test_fork_files_named_by_the_registry_exist / test_known_gaps_are_still_open_or_get_promoted
```
In the third run all 14 data and cascor sites go unchecked, and the job step stays green.

The measurement cannot show any of this:
- "8 tests" is always 8: five structural tests plus three cross-repo tests. The sites run as subtests, so the count does not change. It still reads 8 in the blind run.
- "0 failures" is guaranteed while no guard names canopy.
- "0 skips" holds only because this dev box has a canopy checkout — exactly the condition the stated cost is about.

Reading the code is what supports the correction; the measurement adds nothing to it.

Suggested correction: state that `_find_ecosystem_root` needs every `_FORK_REPOS` member and that `_require_cross_repo` skips rather than fails. So a failed canopy clone silently turns off the whole cross-repo half. Then require the widening PR to do one of two things:
- resolve the root per repo, skipping only the sites whose repo is missing; or
- fail on a missing root when running under `GITHUB_ACTIONS`.

**2. [Medium-High] The behaviour-change paragraph overstates today's state and understates the risk. The canopy PR that implements the fix contradicts it.**

Quoted (`DEFECT-REGISTER.md` `APD-ECO-008` bullet, L1438-1446):
- *"today enables `APIKeyAuth` with a key no client can present, so every request is refused"*
- *"without it the service runs open with that warning, which is what the three siblings' `APIKeyAuth` already does."*

What it overstates: "no client can present" and "every request is refused" are both false.
- `juniper-canopy/src/main.py:712` reads `key = websocket.headers.get("X-API-Key") or websocket.query_params.get("api_key")`. A client can send a whitespace-only key as `?api_key=%20`.
- All three WebSocket endpoints pass `allow_browser_auth=True` (`:776`, `:913`, `:3576`).
- The exempt paths (health, docs, dashboard) and the browser control surface (Origin + CSRF) are not refused either.
- The round-39 handoff got this right. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` §0.3 says "a key no **HTTP** client can present". This PR dropped the word "HTTP".
- canopy PR #660 (open) says in its own CHANGELOG entry and code comment that the key "refused every HTTP request … while the WebSocket `?api_key=` query parameter could still present it".

What it understates:
- `require_auth: bool = False` is canopy's default (`src/settings.py:435`). So "without it" is the default setup, not an edge case.
- The change moves the keyed HTTP routes from failing loudly (every call returns 401) to working quietly with no authentication. The only signal is a boot-time WARNING that is already printed today.
- Turning auth off also turns off the Origin + CSRF checks on `/api/train/*`: `src/security.py:352-354` returns before those checks when `not auth.enabled`.
- Setting `JUNIPER_SKIP_AUTH_POSTURE_CHECK` produces the same fail-open result even under `require_auth`.
- The row itself still hedges ("probably not an auth bypass … never been independently refuted"), while the bullet now states the before-state as fact.

Suggested correction: say "no **HTTP** client", name the `?api_key=` query-parameter path, and say that `require_auth` defaults to false, so a deployment that fails visibly today will serve unauthenticated after the fix. Bring the text in line with PR #660's CHANGELOG.

**3. [Medium-High] X-A: "removes the startup dependency … rather than tolerating it" is false on one of the two paths the same sentence names, and the ruling leaves out a regression.**

Quoted (L1363-1365): *"The set is consulted only immediately before a dataset request, on two paths — auto-start and the staged reload — so the lazy fetch removes the startup dependency the 2026-09-11 text anticipated rather than tolerating it."* Also quoted: *"fetches again on the next request; a failure is never memoized."*

- Auto-start is itself a startup-time dataset request. `lifespan` starts it with `asyncio.create_task(_auto_start_training(...))` (`juniper-cascor/src/api/app.py:420-424`), and it already waits on juniper-data (`:523`).
- Auto-start runs once and swallows its failure (`:490-498`, `:572-575`). So on that path the fetch is still a boot-time fetch, a failure is only tolerated, and there is no next request to retry on.
- The regression: when the flag is on, the generator is truncatable and the list is unreachable, the opt-in is withheld. juniper-data then returns 422, and `_describe_dataset_fetch_failure(exc, allow_truncated=False, caller_refused=False)` builds the remedy *"re-run with --allow-truncated-datasets (or set JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true…)"* (`src/api/lifecycle/manager.py:3740-3742`). That tells the operator to turn on a flag that is already on. This is the exact failure cascor#640 removed from this path (comment at `app.py:533-537`). The staged-reload path produces the same wrong message.

Suggested correction: limit "removes" to the staged-reload path, and require a separate state meaning "opt-in withheld because the generator list was unreachable", carried into the failure message.

**4. [Medium] A sentence still says no row is awaiting an owner decision. Its subject changed in this PR, and it was left false.**

Quoted (`APD-DATA-047` bullet, L1376-1377): *"With this ruling **no row in this register is awaiting an owner decision** — every open row is implementation work."*

- The `APD-ML-002`…`-006` bullet says *"These five need an owner decision before code is written"*.
- This PR removes two items (`APD-ECO-008`, and X-A's open question) from exactly the set this sentence describes, and leaves it standing.
- Read as written, it gives a session licence to act on five rows the rest of the register parks.
- The register's §1 ("The limit of the sweep") says to re-read any sentence that counts or ranks something.

Suggested correction: append a dated correction naming `APD-ML-002`…`-006` as still awaiting a decision.

**5. [Medium] The X-A ruling cannot be implemented as written without decisions it does not mention.**

Quoted (L1356-1357): *"cascor fetches the list **lazily**, the first time a dataset request needs it, and memoizes a success."*

What stands in the way:
- The resolver is a `@staticmethod _resolve_truncation_stance(params, *, generator, allow_truncated)` with no client in reach (`manager.py:3855-3856`). It imports the constant inside the function (`:3889`).
- Auto-start deliberately calls it on the class, not an instance (`app.py:543`; reason at `:600-602`).
- Each path builds its own `JuniperDataClient` (`app.py:519`, `manager.py:4147`).
- So the memo has to be process-wide state and the resolver's inputs have to change. Otherwise the membership test ends up duplicated in each path, which is the drift the resolver's docstring warns against (`:3859-3863`).

What the text leaves out:
- **Memo key.** `_reload_dataset` re-reads `Settings().juniper_data_url` on every call so it picks up environment changes (`:4139-4145`). A memo not keyed by that URL pins whichever service answered first.
- **Staleness.** A success memoized forever is itself a copy of the set free to drift for the life of the process — the same reason the ruling gives for rejecting the built-in fallback copy.
- **When the fetch is needed.** The set is consulted only when `allow_truncated` is true and the caller sent no stance (`:3892`). Fetching before that check adds a network call and a new failure mode to every deployment with the flag off.
- **Cost of failure.** A failed fetch on the reload path happens while holding `_lock` (`:4100`), on every retry, at up to a 30 s timeout with 3 retries each (`juniper-data-client` `constants.py:193-194`).
- **How to derive the set.** `/v1/generators` has no truncatable flag. `GeneratorInfo` holds name, version, description, available, install_hint and schema (`juniper-data` `core/models.py:143`, `routes/generators.py:248-259`). The set has to come from `allow_truncation` in each schema; only `csv_import/params.py:66` and `equities/params.py:107` declare it, and `EquitiesSeqParams` inherits it.
- **The mirrored copy.** The constant is duplicated byte-for-byte at `juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py:139`, and `juniper-cascor-model/tests/test_drift.py:27` checks `cascor_constants` against it. The round-39 handoff §0.3 flags this and notes that `Test (Python 3.12)` is not a required check. The row's Source column names only the `src/` copy.
- **A docstring.** `src/main.py:663` names the constant.

**6. [Medium] The new §2.3 row claims gate coverage that does not exist, and that undercuts the ruling's own reasoning.**

Quoted: *"| Non-short-circuiting key compare | `juniper-data` | ~~`juniper-cascor`, `juniper-service-core`~~ — **both fixed** … | `ENFORCED` |"*. The §2.3 prose also says the gate "encodes this table".

- The guard's sites are only data and cascor (`test_service_fork_drift.py:172-173`). juniper-service-core cannot be a member of `_FORK_REPOS`.
- Nothing tests service-core's `matched` loop (`juniper_service_core/security.py:73,77`). `git grep` for `matched = False` finds only the drift test's markers and ad-hoc scripts, and service-core's tests never mention `compare_digest`.
- service-core's CHANGELOG nonetheless says the guard *"is therefore a source marker in juniper-ml's `tests/test_service_fork_drift.py`"*.
- So the chosen option also "leaves the class open", which is the ruling's own objection to fixing the line alone: service-core's copy becomes the one copy of four that nothing watches.

Suggested correction: have the Gate cell name the two watched sites and say service-core is unwatched, and say the same in the ruling.

**7. [Medium-Low] A stale pointer.**

Quoted (L1303-1304): *"**These five need an owner decision before code is written**, exactly as `APD-ECO-008` states for itself."*

After this PR, the `APD-ECO-008` bullet opens *"RULED 2026-09-22"*. This line is one of five hits for `grep APD-ECO-008` (L255, L1228, L1278, L1304, L1422), and §1's close protocol ("Closing a row — the five touches") says to grep the whole file for the id and read every hit.

Suggested correction: "…as `APD-ECO-008` did until its 2026-09-22 ruling."

**8. [Medium-Low] Two other sentences still say six guards, and one now contradicts the table this PR extended.**

- §4.3: *"its six guards cover the body cap, `Content-Length` parsing, serialization-error narrowing, blank-key filtering, the pre-auth throttle and CORS ordering"*.
- §5.1 closing paragraph: *"now holds **all six** copy-drift guards as `ENFORCED` … — every row in §2.3's table."*

`GUARDS` has seven entries (`test_service_fork_drift.py:100-213`), and the new parenthetical ("lagged it until 2026-09-22") implies the lag is fixed. Update both sentences to seven, or stop counting.

**9. [Low-Medium] Wrong ruling date.**

Quoted: *"The 2026-09-11 text did not say…"* and *"…the startup dependency the 2026-09-11 text anticipated…"*. The PR body also says "the 2026-09-11 ruling".

- `git log -S 'Derive the truncatable set from juniper-data'` finds `6ccf80fa`, dated 2026-09-09 (ml#1864). A search for the "design constraint" sentence finds the same commit.
- The bullet sits under "OWNER RULINGS, 2026-09-09".
- `APD-CASCOR-008` appears 3× in `util/ad-hoc/register_owner_rulings_2026-09-09.py` and 0× in `util/ad-hoc/register_owner_rulings_primer_2026-09-11.py`.
- §2.4's 2026-09-11 block does not contain it.

Change the date to 2026-09-09.

**10. [Low] "ENFORCED" is a label; the first actual check comes later.**

Quoted: *"Canopy's PR lands first, so both guards are `ENFORCED` from the moment they name it."* The PR body says *"ENFORCED from their first commit"*.

The cross-repo checks run only in the weekly or dispatched `docs-full-check` (`:44-47`); the per-PR run skips them. So the canopy sites are first actually checked up to a week after merge. A successor should dispatch that workflow, or run locally with `FORCE_LOCAL=1` against up-to-date siblings, before merging the widening.

**11. [Low] X-A's list of rejected options is incomplete.**

`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md` §4 posed the choice as "fail closed, fail open, or cache the last-known set". Two options are not recorded as considered:
- failing the individual request closed;
- failing open, i.e. sending the opt-in when membership is unknown. cascor's own comment says non-truncatable generators ignore the parameter (`manager.py:3893-3896`).

The register's §2.4 rule requires the rejected options precisely so a later reader can tell a decision from a drift.

**12. [Low] Gaps a successor on the canopy half would hit.**
- The guard summaries are written for the two forks. The blank-key filter's summary says *"an empty secret file enables auth that then accepts an empty X-API-Key"* (`:136`), which is false for canopy: an empty file becomes no key and turns auth off.
- The module docstring and the `_FORK_REPOS` comment (`:1-8`, `:56-58`) describe *"the two services that fork the service-core code"*, and `docs/REFERENCE.md:2969` and `:3609` describe the gate as data and cascor only.
- canopy's production `APIKeyAuth` only ever holds one key (`security.py:265-267`), so the compare fix there brings the copies in line but stops no leak.

## Attacks that did not land
- `_FORK_REPOS` is read in exactly three places (`:264`, `:285`, `:353`), and nothing else in the repo reads it. Every guard lists its sites explicitly. The core correction holds.
- The 8/0/0 figures reproduce before and after widening. `docs-full-check` does clone canopy (`ECOSYSTEM_REPOS`, `:82`).
- "juniper-data's own deployment default then governs, which errs toward refusing" holds:
  - The resolver only ever adds `allow_truncation: True` (`:3892-3906`).
  - Withholding never drops a caller's explicit `false`.
  - juniper-data's defaults are `False` (`core/limits.py:138-139`).
- The code readers of the set really are the two named paths. The other hits are the mirrored copy, exports and a docstring.
- `get_secret` does strip a secret file (`secrets_util.py:62`) and returns the environment variable unstripped (`:64`). `enforce_auth_posture` treats a blank key as no key (`auth_posture.py:61-71`) and runs in `lifespan` before serving (`main.py:336-346`).
- The siblings behave the same way. Their `require_auth` defaults are also false: data `settings.py:81/163`, cascor `settings.py:286`.
- Scoping the change to keys "supplied through the environment variable" is correct: compose and helm pass the key as a file.
- Both rulings record a chosen option and rejected options. Both rows' own ruling bullets are updated.
- The open-row count, re-derived on both versions, is 126 rows, 99 fixed, 27 open — unchanged.
- ml#1974 merged 2026-09-21, as the §2.3 parenthetical says. The round-41 "unattacked" claim is accurate (`HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md:220-221`).
- canopy PR #660 matches the guards' literal markers (`isinstance(k, str)` / `k.strip()`, `matched = False` / `return matched`).

**Changed:** no repository file. The only files written were scratch copies of `DEFECT-REGISTER.md` at `main` and at the PR head, in the session scratchpad.
