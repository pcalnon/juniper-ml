<!-- Archived verbatim 2026-09-24 from subagent a7b8f376d87c32f5e of session bc31e993 (turn-ending report 1 of 5; an earlier report of a resumed agent). -->

I opened **PR #686**, read back with `gh pr view`: https://github.com/pcalnon/juniper-cascor/pull/686. It is open, not a draft, auto-merge not armed, and CI was all pending at report time; I did not wait for green.

**Head SHA:** `653bc3f58218aecd21c911fc94b356a7fd11fc6d`. It is GitHub-signed (verified), its parent is `33c965b`, and its tree is byte-identical to the one I tested. The `Allow-Symbol-Loss`, `Co-Authored-By` and `Claude-Session` trailers all parse.

**Main moved.** #684 (CI-only, plus a CHANGELOG entry under `### Added`) landed after `0e016a7`, so I rebased before opening; no release was cut. A fetch just before opening showed main still at `33c965b`. Open PR #685 (auto-merge armed) also touches `manager.py` and `CHANGELOG.md`. It test-merges cleanly with mine and has no semantic overlap, but whichever lands second will need an update-branch.

**The predecessor's work-in-progress.** It failed exactly 7 existing tests, all intended behaviour changes. I kept most of it, with two fixes:
- I restructured `_rebind_dataset_record_locked` without changing its behaviour.
- `_reload_dataset(fetch_path=...)` now defaults to `None`. The old default would have told a direct call that its dataset was still staged.

All tests, docs and the CHANGELOG entry were missing, and I wrote them.

## Per item (mutant name, then how many tests it fails)
1. **Keep while fetched splits stay.** New `_described_partitions`: a fetch sets it, the new `_rebind_dataset_record_locked` moves it one partition at a time, and a live swap rolls it back.
   - Pinned by `test_shortfall_lifecycle.py::TestKeepWhileFetchedSplitsStay` (10 tests, through the real fetch: train-only, train+val, train+test, all three, across several starts, new fetch, reset, a clean fetch, auto-start's shape), plus `TestTheLiveSwap::test_a_cancelled_swap_restores_which_splits_the_record_stands_on`.
   - Kills I1a–I1j: never kept (10), fetch records nothing (9), fetch leaves the set stale (9), val/test-only start keeps the record (2), train-only `bound` (5), caller record describes nothing (2), `has_record` ignores config (1), snapshot omits the set (1), rollback keeps the swap's set (1), `reset()` clears it (1).
   - The validator's `probe_mixed.py` now reports `ds-1` on status and metrics.
2. **Every remedy begins "To accept it,".**
   - Pinned by `test_allow_truncated_datasets.py::TestRunFailureMessage::test_every_refusal_branch_leaves_canopy_the_producers_own_text` (9 branches, run through a verbatim copy of canopy's parser), plus a test that counts `stance =` branches in the describer's source so a new branch cannot go unlisted.
   - Kills I2a WITHHELD opens with "Retry once" (5), I2b (2), I2c unlisted branch (1).
3. **A null stance defers whatever the flag** (`_OPT_IN_SKIPPED_CALLER_DEFERRED`).
   - Pinned by, in `test_truncatable_generators.py`: the resolver test (null / empty / blank, flag on and off), the live-path `test_a_null_stance_reaches_the_producer_as_sent_and_its_refusal_names_no_knob[flag-on|flag-off]`, the request-model reach test, and the describer test.
   - Kills **M21** (2), I3a (8), I3b (6).
4. **A not-truncatable 422 is a plain failure with no token.** Pinned by the describer test, the staged `[equities-undeclared|spiral-param-error]` test, and the auto-start test. Kills I4a (4).
5. **Any schema-less entry fails the read.**
   - Pinned by `TestDerivation::test_any_entry_without_a_usable_schema_fails_the_read`, which replaces the old test (the waived symbol), and `TestLazyResolution::test_a_partly_schemad_listing_is_not_memoised_as_a_smaller_set`.
   - Kills I5a (7), I5b (1).
6. **The auto-start listing client is pinned.** Pinned by `test_auto_start_shortfall.py::...::test_the_listing_client_carries_the_auto_start_url_and_key`. Kills **M22** (1), **M23** (1), timeout 30 (2), retries 3 (2).
7. **Each path gives only its own retry.**
   - Pinned by the per-path describer tests (plus a no-path case), `TestEachPathNamesItsOwnRetry` (real start and real swap; each also checks that the retry it names actually works), and the auto-start withheld test.
   - Kills I7a (1), I7b (1), I7c (1), I7d (2), I7e (6), I7f (7).
8. **Log only once the data is bound.**
   - Pinned by `TestTheShortfallIsLoggedOnceItsDataIsBound` (3 tests), plus the auto-start real-start log test and the refused-artifact no-log test.
   - Kills I8a (2), I8b (1), I8c (1), I8d (1), I8e (2).

**Mutation total:** 35 of 35 killed, 0 survived, 0 skipped, on a scratch copy over a green control (167 passed). Reverting `manager.py` and `app.py` whole to `0e016a7` fails 16 new tests; the other two files fail at import there, because the constants they test are new.

## Commands (from `src/`)
All run with `env -u JUNIPER_CASCOR_LOG_DIR -u SENTRY_SDK_DSN -u JUNIPER_CASCOR_SENTRY_DSN PYTHONDONTWRITEBYTECODE=1 /opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest ... -p no:cacheprovider`.

| Command | Result |
|---|---|
| The four named files | **167 passed** (39 / 36 / 29 / 63; 121 at `0e016a7`) |
| `tests/unit/api` | **2472 passed**, 0 failed |
| The 17 files outside `unit/api` that import `manager.py` / `app.py`, with `--integration -rs` (listed in the PR body) | **210 passed**, 3 skipped, 10 subtests passed |
| The 3 skipped, with `--integration --slow --golden` | **3 passed** |
| `/opt/miniforge3/bin/pre-commit run --files <9 files>` | all passed, nothing rewritten |
| Symbol-loss screen, base `33c965b` | OK; 1 finding, waived (`method:TestDerivation.test_an_entry_with_no_usable_schema_is_not_truncatable`) |
| Docs-additions screen | OK; 3 WARN small in-place edits, 0 FAIL |

## Left undone
- **Flag off, ordinary 422:** a generator that cannot be short still gets the token and the knob remedy, because the list is never read with the flag off. Unchanged here.
- **Defect register:** §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` does not record the 2026-09-24 ruling yet. That is a juniper-ml change.
- **#678's squash message** still misstates the landed code; it is history and cannot be amended.
- **Visible change for canopy:** after an inline start that replaces only some partitions (including the in-process spiral start), `current_dataset` now names the fetch. Canopy hydrates its dataset selector from this field.
- **Unreachable edge case:** a caller annotation passed with X alone while a fetch's val/test are still loaded is logged but not adopted. Only auto-start passes one, and it binds all three partitions at boot.
- **Uncommitted in juniper-ml:** the validation report and my mutation harness.

**Changed (cascor, all in #686):**
- `AGENTS.md`
- `CHANGELOG.md` (additions only)
- `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`
- `src/api/app.py`
- `src/api/lifecycle/manager.py`
- `src/tests/unit/api/test_allow_truncated_datasets.py`
- `src/tests/unit/api/test_auto_start_shortfall.py`
- `src/tests/unit/api/test_shortfall_lifecycle.py`
- `src/tests/unit/api/test_truncatable_generators.py`

**Created (untracked):** `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/util/ad-hoc/2026-09-24_cascor678_followup_mutation_check.py`

**Referenced:**
- `reports/2026-09-24_defect-register-round-42/cascor678-postmerge-validation.md`
- `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- juniper-canopy `src/frontend/dashboard_manager.py`

The worktree's local branch now points at the signed `653bc3f`, with a clean status.
