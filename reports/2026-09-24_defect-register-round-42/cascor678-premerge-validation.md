<!-- Archived verbatim 2026-09-24 from subagent a4b7e2601c9990ad3 of session bc31e993 (final message). -->

## PR #678 validation: head e02020d is not mergeable, because of 5 CodeQL alerts the PR body never mentions

The behaviour mostly holds up: 12 of the 13 X-B/X-A attacks did not land (the 13th is a CodeQL finding in the tests, not a behaviour problem), and every claim I could re-derive checked out. What stops the merge is CI, not code behaviour. The line numbers below are for `src/api/lifecycle/manager.py` at e02020d unless another file is named.

## Defects, most severe first

**1. High: CodeQL blocks the merge.** The PR body says only that the branch "needs update-branch before merge".
- **Code:** `return (*result, reader.calls)` at `src/tests/unit/api/test_truncatable_generators.py:192`.
- **What CodeQL reports:** 5 new error-level "Mismatch in multiple assignment" alerts at lines 195, 200, 206, 217 and 224, where 6 names are unpacked. CodeQL counts the starred tuple as length 2. That is wrong (it is 6 at runtime), but the alerts still block.
- **Why it blocks:** ruleset `juniper-cascor-rules` (id 15081045) has a `code_scanning` rule for CodeQL at `alerts_threshold: errors`, and also sets `required_review_thread_resolution: true`. There are 5 unresolved `github-advanced-security` review threads, created 02:12Z and still open. Updating the branch changes neither.
- **Fix:** restructure the helper rather than suppress the alert. For example, return `(result, reader.calls)` and unpack as `(params, source, wire, refused, withheld), reads = self._resolve(...)`. Once that lands, resolve the threads.

**2. Medium: the squash commit will put superseded X-B behaviour into `main`'s history.**
- The repo squashes with the PR title as the subject and all commit messages as the body.
- The title says "dataset_shortfall is **re-decided every run**". The final code keeps the annotation on a retained-data start instead of re-deciding it.
- The first commit's body (3ec64b3) says the annotation is cleared "at the start of every run", that `start_training` "re-decides it and applies it at submit", that "reset() clears it", and that "A plain Stop -> Start on retained data now reports null". All four are false at e02020d; the reset arm and the retained-start arm pin the opposite.
- The squashed body will carry both these statements and e02020d's correction.
- **Fix:** retitle the PR and merge with a curated subject and body, then check the merge commit itself: an armed auto-merge can override a curated body.

**3. Low: the fetch path still writes the annotation before the data is bound.**
- `_reload_dataset` sets `self._dataset_shortfall` at :4523, converts the artifact at :4525, and binds the tensors at :4532. `current_dataset` is set at :4551, and `get_status()` reads without the lock.
- **Evidence:** in my real-path probe, a status poll during conversion of an artifact with no validation split returned `dataset_shortfall.dataset_id == "valless"` with `current_dataset == None`. The fetch was then refused and the value restored.
- So the status briefly reports a shortfall for data that was never loaded. That contradicts the ruling recorded in `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` ("set when data is bound") and the PR's own "bound together with the tensors".
- **Fix:** assign the annotation next to `self._train_x = new_train_x`. That also makes the restore in `_consume_pending_dataset_locked` unnecessary for this failure class.

**4. Low: an empty truncatable set is cached as a success, and the refusal then names the wrong remedy.**
- `derive()`'s docstring says a malformed listing "must be a FAILED read, never an empty set … memoised for the life of the process".
- Entries without a `schema` key derive as not truncatable, and `test_an_entry_with_no_usable_schema_is_not_truncatable` pins that.
- **Evidence:** in my probe, a listing with names only gave `frozenset()`, which was cached after 1 fetch. With the flag on and the caller silent, `withheld=False`, and a 422 then produced the "set JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true" remedy while that knob is already on. That is the wrong-remedy class constraint 5 exists to prevent (the cascor#640 class).
- **Reachability:** juniper-data has emitted `schema` as a required field since da088db (2026-01-31). The case you can actually hit is a cached list that went stale after juniper-data was redeployed with a newly truncatable generator.
- **Fix:** treat a listing in which no entry carries a schema as a failed read. When the flag is on but the generator resolved as not truncatable, don't name the flag in the remedy.

**5. Low: the "withheld" remedy text gives slightly wrong advice.** At :4029 it says "(re-stage it, or restart…)". A failed staged start leaves the config staged, so a plain restart retries. The live-swap path stages nothing; the remedy there is to re-issue the swap.

**6. Low: the operator docs were not updated.** The `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` row in `AGENTS.md` and `docs/api/JUNIPER_CASCOR_API_REFERENCE.md:867` omit three things:
- the flag now depends on `GET /v1/generators` being readable, and the opt-in is withheld when it is not;
- the new refusal remedy;
- the new lifecycle: the annotation is kept on reset and on a retained start, and is null for inline data.

Only the CHANGELOG and the docstrings describe these.

**7. Nit: the first commit is broken on its own.** At 3ec64b3, `manager.py:3932` still imports the constant that the same commit deletes, so every stance resolution raises ImportError. This only matters for a merge-commit merge, which the ruleset allows alongside squash.

**8. Nit: the PR body calls the two warnings "waived by `Allow-Symbol-Loss`", but the trailer is inert.** Removing a constant or an import is only a warning, and `apply_waivers` touches only failures (`symbol_loss_check.py:447-451`).

**9. Nit, pre-existing: a log line can misstate what is training.** `_log_dataset_shortfall` still runs before conversion on both paths (manager :4504, `app.py:614`). A refused artifact therefore leaves the log saying "this run is training on a partial dataset".

## Attacks that did not land

- **Run-start coverage:**
  - Training data is bound in only three places (:2528, :3809, :4532), and `start_training` has only three callers (the REST route, the WebSocket `start`, and auto-start). The route cannot pass `dataset_shortfall`, because `TrainingParams` forbids extra fields. Snapshot restore, retrain and resume bind no data.
  - A real-path probe, which fakes only the HTTP client, passed every path: staged fetch → Stop/Start on retained data → reset plus WebSocket start → inline start → a staged artifact refused after the annotation write. The annotation was restored and the config stayed staged. A start refused because a run is already active changes nothing.
  - Against the pre-fix manager, 7 of 13 lifecycle arms fail. Against the previous head bb5423d, exactly the 3 named arms fail.
- **X-A derivation:**
  - Against juniper-data main ce43681 (one commit past the PR's 68c3cd7), both `model_json_schema()` and the real app's `GET /v1/generators` give exactly `{csv_import, equities, equities_seq}`. The listing has 16 entries, all keyed `schema`.
  - `available: false` is ignored. That is harmless: the producer returns 501 without "422", so the remedy branch is not triggered.
- **Constraints, each checked by a hand mutation of the code:**
  - Eager read: 9 arms fail.
  - Cache keyed without the URL: 2 arms fail. A real reload after the URL changed read the new list.
  - Default client: 2 arms fail. The bounded client returned in 0.00 s when the connection was refused and 5.01 s against a blackholed address, with one attempt each time.
  - Withheld remedy branch removed: 4 arms fail. The staged-path message was verified end to end.
  - Caller's value dropped: 12 arms fail.
  - Failure cached: 2 arms fail.
  - X-B mutations (no inline binding, no swap rollback, no staged restore, reset clears, auto-start not handed the annotation) failed 5, 1, 1, 1 and 7 arms.
- **Thread safety:**
  - 16 concurrent cold reads made 16 fetches (no de-duplication, but benign) and returned 1 distinct result with no errors.
  - A reader holding the lock and a lock-free reader both completed. Locks are only ever taken manager `_lock` then cache lock, so nothing can deadlock.
- **Constant removal:**
  - `diff -r -x __pycache__` shows the two trees identical.
  - `juniper-cascor-model/tests/test_drift.py` passes 3/3.
  - No code references remain in src, tests, docs, notes or AGENTS.md; the remaining mentions describe the removal.
  - The trailer parses as a real trailer in 3ec64b3.
- **Tests:**
  - Affected files: 198 passed.
  - `src/tests/unit/api`: 2416 passed.
  - Model suite: 436 passed and 1 failed. The PR says 434; the one failure is the same environment-dependent columnar test, unrelated to this PR.
  - Updated `test_allow_truncated_datasets.py`: all 29 pass on the pre-fix code with an import-only stub.
- **CHANGELOG:**
  - `[Unreleased]` has two `### Added` and two `### Fixed` headings at both e052ef8 and current main. The PR adds 36 bullet lines and no heading.
  - A 3-way merge against current main has 0 conflicts (2703 + 36 + 34 = 2773 lines), and the entries land under the first `### Fixed`.
- **Client version:** juniper-data-client 0.3.0, the pinned minimum, already has `timeout`, `retries` and `list_generators`.

## CI state at e02020d

- All 24 required status checks pass, including Quality Gate, the integration tests, Docker Build & Smoke Test and Sequence Safety. Sequence Safety reports `fail=0`.
- **CodeQL fails** with 5 new errors, and the 5 CodeQL review threads are unresolved.
- `mergeStateStatus: BEHIND`, `mergeable: MERGEABLE`.
- To merge: fix defect 1 in code, resolve the threads, then `update-branch`.

**Changed:** nothing in any repository. The PR worktree is still clean at e02020d. All probes, mutation runners and logs are under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678/`. My first juniper-data probe created an empty `data/datasets` directory in my juniper-ml worktree; I removed it.
