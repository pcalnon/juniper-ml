I found 5 BLOCKERs in the canopy v0.10.0 body and 2 in the cascor v0.14.0 body. In both, most are statements that were true when their PR merged and are false at the release head. The headers' exposure analysis holds, except canopy's "One path stays open".

Grading: **BLOCKER** means false on publication day with nothing else in the body correcting it. **MAJOR** means false on publication day, but another entry in the same body explicitly supersedes it. Line numbers refer to the filled bodies. Quotes are unwrapped where the source wraps lines.

## juniper-cascor v0.14.0 (`.../tmp/s2/filled_cascor_0_14_0.md`)

1. **BLOCKER, lines 280-282 (#734).** Quote: "**Left alone.** The same census found two other sets that no lane runs: the 153 `performance`-marked tests in `src/tests/performance/`; five unmarked tests in `src/tests/integration/test_comprehensive_serialization.py`."
   - Evidence: #735 (`453ff286`) fixed both. At the head, `scheduled-tests.yml:268` defines `performance-smoke` (`--run-performance --benchmark-disable`, `:320-321`), and all five classes carry `@pytest.mark.integration` (`test_comprehensive_serialization.py:110,180,254,304,351`). The #735 entry (lines 294, 298) never points back to this one.
   - Replace with:
     ```
       - **Left alone here, and given a lane later in this release** (the nightly-lanes entry below). The same census found two other sets that no lane ran:
         - the 153 `performance`-marked tests in `src/tests/performance/`, which the new nightly `performance-smoke` job runs;
         - five unmarked tests in `src/tests/integration/test_comprehensive_serialization.py`, now marked `integration` and run in the required integration jobs.
     ```

2. **BLOCKER, line 300 (#735).** Quote: "Five other live documents still name the file (`docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `src/tests/README.md`); they are left for a later pass."
   - Evidence: #737 (`012d4737`) is that pass. At the head none of the five names the file (`src/tests/README.md:269` "There is no `pytest.ini`."), and line 266 of this body says the opposite.
   - Replace with: "Five other live documents named the file too (`docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `src/tests/README.md`); "Five documents no longer name the nonexistent `src/tests/pytest.ini`" above corrects them in this release."

3. **MAJOR, lines 137-141 (#753).** Quote: "**Not fixed here: the stop-then-start race.** A start sent after a stop … clears the shared `_stop_event`, so the old fit is never interrupted." The item continues with "…reproduces it … (exit 1 on both). The Overtoad's ruling 17 (2026-11-09, recorded in the record-update PR) … Candidate fixes, which no ruling chose: a per-run stop signal, or a start that refuses or fences a live fit."
   - Evidence: #756 (`44b60af2`) fixes the race in this release (`_stop_event_for_new_run_locked`, `manager.py:2564`). Line 252 says the reproducer "exits … 0 with this change", and line 261 says the Overtoad ruled on 2026-11-12 to keep the per-run signal. No juniper-ml PR records ruling 17: the only flood-4 record PR is juniper-ml#2530 (rulings 1-14).
   - Line 261 also misquotes this item's heading as "Reported, not fixed here".
   - Replace the whole item, sub-items included, with:
     ```
       - **Reported here, fixed later in this release: the stop-then-start race.** A start sent after a stop, before the old fit reached its next checkpoint, cleared the shared `_stop_event`, so the old fit was never interrupted: it trained on to its natural end while the FSM read `STOPPED` and, still owning the lifecycle, wrote `training_state` `Completed` and counted a successful session for a run the operator had stopped. `swap_dataset_live` cleared the event the same way after its 10 s join timed out. The Overtoadship check above could not help, because cascor's queue keeps the new run from starting until the old fit returns. This change shipped `util/ad-hoc/2026-11-08_stop_then_start_race_repro.py`, which reproduced it (exit 1). The Overtoad's ruling 17 (2026-11-09), "cascor: stop-then-start", gave it a fix of its own: see "A start sent after a stop no longer cancels it" below, whose per-run stop signal the Overtoad ruled on 2026-11-12 to keep, and with which the reproducer exits 0.
     ```
   - In line 261, replace `("Reported, not fixed here: the stop-then-start race")` with `(the stop-then-start item of the paused-fit entry above)`.

4. **MAJOR, line 295 (#735).** Quote: "**The job caps pytest below 9.2 (Overtoad ruling 2026-10-29).** … The job therefore installs `pytest<9.2` (9.1.1) … the cap goes once a pytest-benchmark release supports 9.2."
   - Evidence: #738 (`88cccf5e`) removed the cap, and the head's `scheduled-tests.yml` has no `pytest<9.2`. Line 265 reconciles it.
   - Replace with: "**The job capped pytest below 9.2 (Overtoad ruling 2026-10-29); the cap is gone in this release** (the pytest 9.2 entry above). pytest 9.2.0 (PyPI 2026-10-27) broke pytest-benchmark 5.3.0, then the latest release, at fixture setup: `AttributeError: 'Function' object has no attribute '_nodeid'` (`pytest_benchmark/fixture.py:88`). Every benchmark test errored, and run 40970853599 logged `5 errors` and stopped at `--maxfail=5`. The job therefore installed `pytest<9.2` (9.1.1) after the project until pytest-benchmark 5.3.1 supported 9.2. The required lanes kept pytest 9.2. Locally, on 9.1.1 with pytest-benchmark 5.3.0, all 153 passed."

5. **MAJOR, line 292 (#735).** Quote: "It also catches a failure the exit status hides. `src/tests/conftest.py`'s `pytest_unconfigure` calls `os._exit(0)` whenever a non-daemon thread outlives the session, so a failing lane can exit 0 (measured: `1 failed`, exit status 0)."
   - Evidence: #736 (`d042de23`). The head's `conftest.py:1140-1145` passes `session.exitstatus` through, and `:1181` says "Until 2026-10-29 it was `os._exit(0)`".
   - Replace with: "It also catches a failure the exit status hid: `src/tests/conftest.py`'s `pytest_unconfigure` called `os._exit(0)` whenever a non-daemon thread outlived the session, so a failing lane could exit 0 (measured: `1 failed`, exit status 0). "A failing test session no longer exits 0 when a thread outlives it" below removes that mask in this release."

6. **MAJOR, line 299 (#735), with a NIT at line 152.** Quote: "165 of 165 uploads had succeeded over 200 runs (`util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`)."
   - Evidence: lines 148-151 of this body (#739) say the count cannot see a masked failure.
   - Line 152's "The 2026-10-29 entry below" points by a date that no entry in the release body carries.
   - Replace line 299's sentence with: "The survey (`util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`) counted 165 of 165 upload steps succeeding over 200 runs; a step masked by `continue-on-error` reads `success` there, so the count does not show that every upload succeeded (the Bandit SARIF comment entry above)."
   - Replace line 152 with: "  - **History.** The nightly-lanes entry below (juniper-cascor#735) qualifies its "165 of 165" accordingly."
   - If the CHANGELOG must keep #735's text as written, at least change line 152 to "The nightly-lanes entry below (juniper-cascor#735) keeps its "165 of 165" as written."

7. **MINOR, line 10 (header).** The header never says what the three leaked headers carried for cascor. cascor authenticates REST and WebSocket callers by `X-API-Key` only (`src/api/security.py:17,104`, `src/api/websocket/manager.py:68,89`) and reads no query parameter. The service path never runs `main.py`'s own `sentry_sdk.init` (`server.py` imports only `create_app`; `main.py:47`).
   - Insert after "…in every error event and transaction.": " cascor reads no credential from any of the three (it authenticates REST and WebSocket callers by `X-API-Key` alone), so they carried a secret only when a client put one there."
   - Medium and High themselves match 0.4.2's notes.

8. **MINOR, line 10 vs lines 312-313.** The header calls service-core 0.7.2 "a plain patch". The Security entry says "**The image picks up R-OBS-SC-2's two security patches.** Both locks move … and nothing else".
   - Evidence: 0.7.2's notes say PATCH with a "bug fixes" focus (`RELEASE_NOTES_juniper-service-core_v0.7.2.md:5,18`). R-OBS-SC-2 is a juniper-ml plan ID (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md:33`) that outsiders can't resolve. "and nothing else" reads release-wide, while Changed lists many more moves.
   - Replace the lead with: "- **The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #748 moved both locks from 0.4.1 and 0.7.1 to them, and nothing else (the release's other lock moves are under Changed): `requirements.lock` holds 73 pins and `requirements-cpu.lock` 54, and each reproduces under its constraint-mode freshness resolution."
   - The counts (73 and 54) hold at the head, and Lockfile Freshness passed on `668f88e9`.

9. **MINOR, line 261.** Quote: "juniper-ml's flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) adds the ruling to its §8 in its next update."
   - Evidence: on juniper-ml `main` that record says "Updated: 2026-11-09", and its §8 holds rulings 1-14.
   - Replace with: "As of this release, juniper-ml's flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) lists rulings 1 to 14 in its §8 and not this one."

10. **MINOR, lines 279 and 293.** Quotes: "The unit lane now selects 5,836 of 5,851 collected tests" and "The unit lane selects 5,860 of 5,875 tests".
    - Evidence: later entries in this body report 5,895, 5,991 and 6,004.
    - Replace with "At this change the unit lane selected 5,836 of 5,851 collected tests, up from 5,796 of 5,811." and "At that change the unit lane selected 5,860 of 5,875 tests, up from 5,836 of 5,851."

11. **NIT, line 10.** Quote: "Its image locks, and its wheel now floors, `juniper-observability>=0.4.2`". The image pins `==0.4.2` (`requirements-cpu.lock:129`).
    - Replace with: "Its image locks `juniper-observability` 0.4.2, and its wheel now floors `juniper-observability>=0.4.2`, whose …"

## juniper-canopy v0.10.0 (`.../tmp/s2/filled_canopy_0_10_0.md`)

1. **BLOCKER, line 10 (header).** Quote: "One path stays open: the `?api_key=` WebSocket query parameter reaches Sentry under the default `send_pii=False`, and query strings are juniper-observability 0.4.3's follow-up."
   - Evidence: 0.4.2's notes (`RELEASE_NOTES_juniper-observability_v0.4.2.md:58-63`) leave query strings, Sentry Logs, request bodies, breadcrumbs, exception values and list-shaped headers for 0.4.3.
   - The published 0.4.2 wheel (sha256 `8a4788a9…`) has `configure_sentry` pass `enable_logs=True` with no `before_send_log`, and canopy calls it (`src/main.py:312`).
   - The cascor header and juniper-ml 0.11.5's header both word this correctly.
   - Replace with: "0.4.2 does not close every path to Sentry: its notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for 0.4.3. For canopy the first includes the `?api_key=` WebSocket query parameter, which reaches Sentry under the default `send_pii=False`."

2. **BLOCKER, lines 397-399 (Security).** Quote: "`requirements.lock` moves `juniper-observability` 0.4.1 -> 0.4.2 and `juniper-service-core` 0.7.1 -> 0.7.2, and nothing else: 60 pins, which CI's constraint-mode freshness resolution reproduces."
   - Evidence: the head lock holds 61 pins. `lazy-importer==0.1.0` (`requirements.lock:84`) joined in #810 (`95436541`, 2026-11-10T10:56:28Z), after #806 (`b4b01904`, 2026-11-09T10:21:35Z).
   - The same "plain patch" vs "R-OBS-SC-2's two security patches" inconsistency as cascor item 8 applies here; this replacement fixes both.
   - Replace the lead with: "- **The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #806 moved `requirements.lock` from 0.4.1 and 0.7.1 to them, and nothing else; #810 later added `lazy-importer` (the release's other lock moves are under Changed), so the lock this release installs holds 61 pins, which CI's constraint-mode freshness resolution reproduces. The image installs that lock (`Dockerfile:40`)."

3. **BLOCKER, lines 212-213 (#779).** Quote: "A Dependabot PR reads the Dependabot secret store, which does not hold the token, so its upload stays tokenless."
   - Evidence: the Dependabot store has held `CODECOV_TOKEN` since 2026-11-04T11:18:47Z (`gh api …/dependabot/secrets`, names only). The head's `ci.yml:293-294` says it does, and this body's own lines 88-89 (#802) say the opposite of line 212.
   - Replace with: "A Dependabot PR reads the Dependabot secret store, which did not hold the token then, so its upload stayed tokenless until the Overtoad added the token there on 2026-11-04."

4. **BLOCKER, lines 125-126 (#777).** Quote: "(the event juniper-recurrence's bench lane receives; it reaches canopy once juniper-data's notify-consumers matrix lists it)"
   - Evidence: juniper-data `main` `notify-consumers.yml:78` has `repo: [juniper-recurrence, juniper-canopy]`, added by juniper-data#501 (`95163c47`, 2026-10-30T08:37:13Z). There has been no juniper-data release since 0.17.1, so the dispatch hasn't fired here yet.
   - Replace with: "(the event juniper-recurrence's bench lane receives; juniper-data's notify-consumers matrix has listed canopy since juniper-data#501, 2026-10-30, so juniper-data's next release sends it here)"
   - Side note: `juniper-data-schema-drift.yml:40-41` carries the same stale wording as a comment.

5. **BLOCKER, lines 372-374 (dash floor).** This is the known item, and the notes contradict it. Quote: "the conda file was the one environment on 3.x, and it was the one nobody drove."
   - Evidence: `conf/conda_environment_cpu.yaml:47` pins `dash=3.3.0` at v0.9.0, at the fix (`fbf01dff`) and at `1c2dbd01`, alongside `conf/conda_environment.yaml` (3.3.0 at v0.9.0). So the sentence was false when written too.
   - Replace with: "the two conda files (`conf/conda_environment.yaml` and `conf/conda_environment_cpu.yaml`, both `dash=3.3.0`) were the environments on 3.x, and nobody drove them. This release moves only `conf/conda_environment.yaml`: `conf/conda_environment_cpu.yaml` still pins `dash=3.3.0`, below the new floor."

6. **MINOR, lines 407-408.** Quote: "**Still open**: the `?api_key=` WebSocket query parameter reaches Sentry under the default `send_pii=False`. Query strings are juniper-observability 0.4.3's follow-up, so this lock does not close that path." It reads as the complete list (same evidence as item 1).
   - Replace with: "**Still open**: 0.4.2's notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for juniper-observability 0.4.3, so this lock does not close them. The query strings include canopy's `?api_key=` WebSocket parameter, which reaches Sentry under the default `send_pii=False`."

7. **MINOR, line 10.** Quote: "The release also raises the runtime floor to `dash>=4.0.0` (F-CANOPY-069: under every dash 3.x the dashboard was inert), so an environment still on dash 3 moves to dash 4 with it." This implies the floor is the fix, but line 374 says the fix works on dash 3.3.0 too.
   - Replace with: "The release also fixes F-CANOPY-069 (under every dash 3.x the dashboard was inert; the fix works on dash 3 too) and raises the runtime floor to `dash>=4.0.0`, the line canopy tests, so an environment still on dash 3 moves to dash 4 with it."

8. **MINOR, lines 239 and 243.** Quotes: "Same record, §4." and "(a row in the same record)". In #775 these followed the flood-3 citation directly. #814's entry, which ends "Cursor flood-4 evaluation", now sits between them.
   - Replace with "Found by the Cursor flood-3 evaluation: juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4." and "(a row in that flood-3 record)".

9. **MINOR, lines 166-168 (#815).** Quote: "which that record's next update adds to §8 of `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`". Same evidence as cascor item 9.
   - Replace with: "(the Overtoad's ruling 17 of 2026-11-09 in juniper-ml's Cursor flood-4 arc; as of this release its record, `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, lists rulings 1 to 14 in §8 and not this one)"

10. **MINOR, lines 434-438 (Gitleaks).** Quote: "so the next refresh of `conf/requirements-conda.txt` would have failed the PR scan and then the push scan of `main`."
    - Evidence: the file returns 404 at v0.9.0, at #764 (`da08414f`) and at the head.
    - Replace with: "so the next refresh of a conda environment file would have failed the PR scan and then the push scan of `main`. (`conf/requirements-conda.txt`, which the allowlist also names, has not been in the tree since before 0.9.0; its four findings are in history only.)"

11. **MINOR, line 207.** Quote: "The unit lane now selects 8,224 of 8,228 collected tests". Line 169 already counts 8290 tests at `b4b01904`.
    - Replace with: "At this change the unit lane selected 8,224 of 8,228 collected tests, up from 8,182 of 8,186".

12. **NIT, line 220.** Quote: "`.github/workflows/lockfile-update.yml` banner 0.1.2." The head banner is 0.1.3.
    - Replace with: "`.github/workflows/lockfile-update.yml` banner 0.1.2 (0.1.3 after the next entry's change)."

13. **NIT, lines 117-118.** Quote: "so a sibling capture such as flat `equities` is covered from the commit that adds it". This release ships that capture (8 generators in 2 fixtures).
    - Replace with: "so a sibling capture is covered from the commit that adds it, as flat `equities` and `mnist` are in this release".

14. **NIT, line 10.** Quote: "Its image locks, and its wheel now floors, `juniper-observability>=0.4.2,<0.5.0`". The image pins `==0.4.2` (`requirements.lock:80`).
    - Replace with: "Its image locks `juniper-observability` 0.4.2, and its wheel now floors `juniper-observability>=0.4.2,<0.5.0`, whose …"

15. **NIT.** The categories run Added, Fixed, Changed, Security; cascor uses the standard order with Changed before Fixed.

## Checked and found correct

- **Rendering:** both bodies are their CHANGELOG sections verbatim. The renderer only drops blank lines between top-level items, the sections contain no links, and both bodies are well under GitHub's size limit.
- **Exposure under 0.4.1:**
  - Both services leave `send_pii` off (cascor `src/api/observability.py:135-140` and `main.py:236`; canopy `src/observability.py:75-80`, with no switch to turn it on).
  - sentry-sdk 2.72.0 and 2.73.0 already filter `X-API-Key`, `Cookie` and `Proxy-Authorization` but not the three leaked headers, so "not reachable here" holds.
  - cascor samples every transaction (`constants_logging.py:278`, 1.0).
  - canopy's `ws_auth_enabled` defaults off, its `Sec-WebSocket-Protocol` bearer auth is at `main.py:806` and its `?api_key=` handling at `:775`.
  - Severity Medium, Priority High, the CWE and the Advisory row all match 0.4.2's notes.
- **Floors, locks and images:**
  - Both `pyproject.toml` floors are as stated.
  - Lock pins and the cascor 73 / 54 counts are as stated, and so are `Dockerfile:42` / `:40`, `app.py:335` and `main.py:312`.
  - Every named lock move, the "six" and "seven smaller moves", and the PR lists match the per-commit diffs.
  - Lockfile Freshness passed on both heads.
- **Coverage:** every shipped path in both net diffs maps to an entry. canopy's merge chain `63e22823`..`571743db` carries no net change, and cascor's `uv.lock` is an unused stub.
- **FastAPI telemetry:** 0.142.0 is the first wheel with `fastapi/telemetry`, the four switches default on, and `FASTAPI_OTEL_AUTO_CONFIGURE` behaves as described. Both code sites match, and neither lock carries an OpenTelemetry SDK.
- **PyPI and cross-repo dates:**
  - observability 0.4.2 and service-core 0.7.2 are still the latest; cascor 0.13.0 and canopy 0.9.0 are the previous releases.
  - pytest-benchmark 5.3.1 is dated 2026-11-01T03:32Z and pytest 9.2.0 2026-10-27T21:30Z.
  - The juniper-data 0.17.1 wheel's sha256 starts `cce2c167`, and its `v0.17.1` tag is `381e660b`.
  - ml#2534 merged at 2026-11-09T15:13:37Z, after service-core 0.7.2 was uploaded (09:52:45Z).
- **Code-level claims:**
  - The Added symbols in cascor match the code.
  - Both `Retry-After` fixes use a ceiling, canopy has no failed-auth throttle, and the service-core imports are as stated.
  - All `actions/checkout` uses (38 in cascor, 26 in canopy) are on `3d3c42e5`, and the census arithmetic holds (data#503 2026-11-01T19:36:48Z, then seven repos on 2026-11-03).
  - cascor's 18 markers, 60 s default and 10-300 s timeout range hold.
  - Required checks match: cascor requires `Bandit` and canopy doesn't.
  - canopy's Gitleaks, Bandit, pip-audit and Codecov steps match their entries; the drift job covers 8 generators in 2 fixtures; the root requirements symlinks resolve as described.
- **Structure:** no category heading is duplicated and no entry is misfiled.

**Changed:** no document. I wrote only scratch files: probe scripts in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/review/scripts/`, plus downloaded wheels and JSON in `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/review/`. They are kept under the retention rule.
