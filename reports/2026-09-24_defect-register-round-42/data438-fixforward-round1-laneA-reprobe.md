<!-- Archived verbatim 2026-09-24 from subagent a6afb722d69732ae5 of session 2fba4397 (final message). -->

**Verdict: REPRODUCED, with 2 LOW and 9 NIT findings. None of them blocks merge on correctness.**

All 23 findings in `data438-round1-laneA-reprobe.md` and `data438-round1-laneB-refute.md` are fixed, documented or flagged the way `data_fixforward_pr_body.md` says. Every number in its Verification table reproduced exactly.

The lock stripes and the atomic create-if-absent hold under interleavings I forced myself, both in one process and across two processes. The same probes reproduce each defect at `0f0f7e0e`.

What does not reproduce is wording:
- The title (`data_fixforward_pr_title.txt`) says "a storage fault is a 500", and `CHANGELOG.md:118` says "only the cursor's own error is the caller's `400`". Both are false for a corrupt metadata document, which is still a 400 at head. (L-1)
- "every other route but batch delete" answers 500 is false for batch-create. (N-1)
- The widened event-loop stall (L5) is disclosed, but its cross-process arm is not. (L-2)

**How I ran it**
- **Code:** `git fetch`, then `git archive` of head `d1c66a11`, of `0f0f7e0e`, of `0f0f7e0e` with only head's test file dropped in, and of `v0.16.0` and `v0.15.0`.
- **Interpreter:** `/opt/miniforge3/envs/JuniperData/bin/python` (3.14.2, the free-threaded build), under `env -i`.
- **Import origin:** a pytest plugin asserted that every imported `juniper_data` module came from the tree under test (185 modules in the unit run).
- **Servers:** only on ports 18931-18936, all stopped. Load average was about 7-8 on 16 cores.
- **Interruption:** the session limit stopped this lane once. After the resume I re-checked every log on disk; everything listed below was produced before or after it.

## Claims table

| # | Claim (where) | What I measured | Verdict |
|---|---|---|---|
| 1 | #438 merged 2026-09-24T18:52:00Z as squash `0f0f7e0e`, which is `main` (`data_fixforward_pr_body.md` Summary) | `gh pr view 438`: mergedAt 18:52:00Z, merge `0f0f7e0e`, head `28fced18`. `origin/main` = `0f0f7e0e` = the head's only parent | REPRODUCED |
| 2 | One GitHub-signed commit (brief) | GitHub API: verified=true, reason=valid, 1 parent, 13 files. No PR exists for the branch | REPRODUCED |
| 3 | Title: "a create takes the conditional PATCH's locks" | create_race S1-S4 (rows 12, 13) | REPRODUCED |
| 4 | Title: "the lock files are sixteen fixed stripes" | row 7 | REPRODUCED |
| 5 | Title: "a storage fault is a 500" | A symlink out of the root: 500 on 10 routes plus the `.npz` case. A corrupt metadata document (`{not json`): **400** "Invalid request parameters" on GET `/{id}`, `/filter`, `/stats` and PATCH at head | PARTLY REFUTED (L-1) |
| 6 | `save_versioned` (`base.py:547`) re-checks and saves under `_version_lock` plus the file lock, named and unnamed, and returns what is stored. Both POST and batch-create go through it | Code read. `test_every_route_that_creates_holds_both_locks` records (True, True) at head in all 4 cases. At base: (False, False) unnamed, (True, False) named | REPRODUCED |
| 7 | 16 stripes, `sha256(id) mod 16` (`local_fs.py:98-183`, `constants.py:44-49`) | Cited lines match. A new store holds `locks/0.lock` to `locks/f.lock`: files mode 0600, dir 0700, 17 inodes. Stripe recomputed independently for 4 ids: all match | REPRODUCED |
| 8 | Opened without `O_CREAT`, with `O_NOFOLLOW` and `O_CLOEXEC`: an absent id leaves no file, a delete needs no free inode, a planted symlink is refused | **strace** of DELETE, batch-delete and cleanup-expired: head 5 opens and **0** inode-allocating syscalls; base 3 `O_CREAT` opens of `<id>.meta.json.lock`. Held descriptor has FD_CLOEXEC. **Absent ids:** 40 of them over 11 route kinds leave 17 → 17 entries at head; base gains 40 lock files. **Replaced stripe:** a symlink gives ELOOP and nothing outside; a directory gives EISDIR and is not recreated; a removed stripe is recreated at 0600 | REPRODUCED (N-4 for `locks/` itself) |
| 9 | `StorageContainmentError` is a generic 500, logged by type only (`app.py:237`) | With a symlinked metadata file: GET `/{id}`, `/filter`, PATCH, DELETE, `/stats`, cleanup, POST, `/access`, batch-export and batch-tags all answer 500 `{"detail":"Internal server error"}`. Base answers 400 on all of them | REPRODUCED |
| 10 | `/filter` decodes its cursor first (`datasets.py:552`), so the 400 detail carries no id | Base detail: "Path traversal detected for dataset_id: '…'". Head: 500, generic body. A malformed cursor keeps its own 400 detail | REPRODUCED |
| 11 | No access is recorded when the metadata is unreadable (`:1156`, `:1164`), so there is no asyncio traceback carrying the id | 3 downloads plus If-None-Match `*`. `v0.15.0`: 200×4, 4 asyncio ERROR records carrying the id. `v0.16.0`: 400×4. Base: [200,200,200,304], 4 records. Head: [200,200,200,304], **0** | REPRODUCED |
| 12 | A create cannot land inside a held conditional PATCH's window (F1/M1) | **In-process, S1, real routes:** at head, create A was still waiting 3 s after release, and its 201 describes what is stored. At base, A saved inside the window; its 201 promised `from-A` plus a TTL, and the PATCH then overwrote the create with its stale copy. **Cross-process, S3, named and unnamed:** at head the child process waits, writes nothing, and returns the edited metadata; at base it saves inside the window and is overwritten | REPRODUCED |
| 13 | Two concurrent same-id creates do not lose a write | **In-process, S2:** head makes 1 save and both 201s describe what is stored; base makes 2 saves, and one 201 describes a dataset that is not stored. **Cross-process, S3b and S4:** at head the second process waits and writes nothing; at base both save and one create is lost | REPRODUCED |
| 14 | The new test file on `0f0f7e0e`: 17 failed, 73 passed, "each failure on its own defect" | 17 failed and 73 passed exactly. 16 fail on their defect. `test_a_storage_directory_that_cannot_hold_the_stripes_still_opens` fails because base has no `locks/` (FileNotFoundError); base opens such a store fine | PARTLY REFUTED (N-2) |
| 15 | F1 row: 7 tests, all fail on base and pass at head | Base failures: "the create saved inside the conditional PATCH's window", "the late create must write nothing", the lock-state tuples, and `[] == [False]`. All pass at head | REPRODUCED |
| 16 | F2/L1: the cached store is out of the guarantee in all four texts, the OpenAPI one included. The service wires LocalFS (`app.py:43`) | Head's `/openapi.json` PATCH description contains all 3 new sentences; base's has none. `cached.py` is not in the diff. Code read of both cache-fill paths | REPRODUCED |
| 17 | F3: RFC quote verbatim; sha256 `21c1cdce…7232a`; line 3463; §8.8.1 is lines 3393-3479 | Fetched `rfc9110.txt`: sha256 `21c1cdce…ebfff47232a`. Quote at line 3463 (whitespace-normalized match). §8.8.1 heading at 3393, §8.8.2 at 3480. "possibly different" does not occur anywhere | REPRODUCED |
| 18 | F4: sweep 1.2.0 adds whitespace-only elements. Negative control 1.1.0: FAIL on base's sweeps with W8 and W11 at 0/0/0; PASS at head with 72 and 9. W11 pins the 12-element reach | Identical runs. With `STRUCTURED_MAX_ELEMENTS` cut to 11, W11 scores 0/0/0 and the control FAILs | REPRODUCED |
| 19 | F5: "anything but spaces and tabs"; h11's 0x1C-0x1F | Raw bytes to live uvicorn 0.40.0. **`v0.16.0` under h11:** `*` wrapped in 0x1C, 0x1D, 0x1E, 0x1F, 0x85 or 0xA0 read as `*` (304). **httptools:** 400 on 0x1C-0x1F, 304 on 0x85 and 0xA0. **Base and head:** all malformed (200). VT and FF are 400 under both parsers. The API doc says "a control character" rather than naming 0x1C-0x1F | REPRODUCED |
| 20 | F6/L3: on base the new test sees "Exception in callback download_artifact.<locals>.<lambda>()" | Base failure message matches | REPRODUCED |
| 21 | F7: a symlinked `.npz` is a 500, and the API doc lists 500 | Head 500, including with If-None-Match `*`; base 400. The Status Codes list has the 500 line | REPRODUCED |
| 22 | F8: flagged only. `notes_render.py` at juniper-ml `df21367d`: Added 1, Changed 1, Fixed 5, breaking NO. On `main`, same counts with the note inside Changed | `parse_unreleased`: head {Added 1, Changed 1, Fixed 5}, `_is_breaking` False, no "Moved here" bullet. Base: same counts, note inside Changed | REPRODUCED |
| 23 | M2: 17 inodes per store; creation is best effort, so a read-only directory opens; the service runs one worker | A chmod-555 directory opens (its first lock then raises PermissionError). `__main__.py` calls `uvicorn.run` with no `workers=` | REPRODUCED (N-5) |
| 24 | M2's 5 tests fail on base | ENOSPC on `doomed.meta.json.lock` ×3; per-id lock files appear for absent ids | REPRODUCED |
| 25 | L2: on base, DID NOT RAISE, and a direct probe followed the symlink, created the outside file at 0600 and deleted the dataset. At head, ELOOP, nothing outside, dataset stays | Base: returned True, outside file 0o600, dataset gone. Head: errno 40, no outside file, dataset kept | REPRODUCED |
| 26 | L4: base answers 400, and `/filter`'s detail names the id; batch delete still reports `not_found`; the cursor test passes on both trees and arm M64 fails it | Base log and the arm classifier agree (M64: `'Invalid request parameters' == 'Invalid base64…'`) | REPRODUCED |
| 27 | L5 disclosed, and this PR widens it: an unnamed create now holds the lock for its whole save | While a 1.5 s unnamed-create save runs, a GET of another dataset takes 1.507 s at head and 0.006 s at base. `LocalFS.save` of 64 MiB float32 takes 2.9 s | REPRODUCED (L-2) |
| 28 | L6: on base only the `save_versioned` case fails; the others fail under M65, M66 and M51 | Each fails with `[True] == [False]` in about 2 s. M51 is caught by the assertion, not by a timeout | REPRODUCED |
| 29 | L7 recorded; snapshot "up to five seconds old" | `_METADATA_CACHE_TTL_SECONDS = 5.0`. X re-created by a second store instance is deleted by the first instance's `delete_expired`; re-created by the same instance, it survives. Same at head and base | REPRODUCED |
| 30 | N1: "never a 200 with an ETag", as now qualified | A removal between `update_meta`'s existence check and its rename gets **200 + ETag**; the metadata comes back without its `.npz`. The same removal one step earlier gets 404 | REPRODUCED |
| 31 | N2, N3, N4 | Text present in `http_cache.py` and `REFERENCE.md`; the renderer yields no note. `update_tags` returning None becomes `not_found` (code read) | REPRODUCED |
| 32 | Unit suite 1901 passed, 7 subtests; 1880 on `28fced18`, whose tree `0f0f7e0e` shares; the 21 new tests account for the difference | Head: 1901 passed, 7 subtests (96 s). Base: 1880 passed, 7 subtests. Tree `ec075327` for both commits. Test file 69 → 90 | REPRODUCED |
| 33 | Coverage gates: 1761 passed, 140 deselected, 7 subtests, TOTAL 97.76%, "PASS: All 100 modules…" | Run on a throwaway copy of the tree: identical numbers, exit 0. All 100 measured files were inside the copy | REPRODUCED |
| 34 | api + integration 118 passed | 118 passed | REPRODUCED |
| 35 | Non-vacuity harness: "PASS: 70 mutations"; baseline 92/92; 110 CAUGHT, 0 VACUOUS, 106 controls OK, 0 over-broad | Unmodified harness, 1455 s: identical counts, verbatim PASS line, exit 0. My classifier shows every must-fail test of M51-M67 fails on an assertion or error about its own defect, never on an import or collection error | REPRODUCED |
| 36 | The first harness run went red only on M57's control, because the test's own setup raised; the added `mkdir` is a no-op on both trees | Under M57 without the `mkdir` line, the test errors in `symlink_to`; with it, it passes. Base still gives "DID NOT RAISE" | REPRODUCED (mechanism); the earlier run itself NO ARTIFACT |
| 37 | Harness coverage: 70 arms; 90 collected; 90 named, 79 must-fail, 11 control-only, 0 unnamed | Identical | REPRODUCED |
| 38 | Equivalence: 2,396,745 + 300,000 + 798,838 = 3,495,583 inputs, 0 mismatches, 926,701 accepted by both | Identical | REPRODUCED |
| 39 | pre-commit on 13 files: ruff, ruff-format, mypy, bandit and doc links pass; markdownlint excludes `CHANGELOG.md` and `docs/` | Pinned ruff 0.15.2: check, ASYNC and format all clean on the 7 `juniper_data` files. Bandit 1.9.4 (the pinned version): clean. The markdownlint exclusion is in `.pre-commit-config.yaml`. mypy was not run at its pin (1.13.0): local 1.19.1 gives the same 59-error set at base and head. The doc-links hook was not run | PARTLY; mypy and doc links NO ARTIFACT |
| 40 | `juniper-symbol-loss-check`: 7 files, 0 findings. `juniper-docs-additions-check`: 2 files, 16 WARN, 0 fail | The published juniper-ci-tools 0.9.0 wheel gives identical output, rc 0 for both | REPRODUCED |
| 41 | Hostile-id probe: 28 ids refused at 9 entry points; nothing created outside; storage holds only `locks/`; HTTP 400 or 404, never 500 | My own 28 ids at 12 entry points: 336 of 336 refused with `InvalidDatasetIdError`. Nothing created anywhere under the probe root. 70 hostile HTTP requests: 55 got 400, 15 got 404 | REPRODUCED |
| 42 | `[0.16.0]` is byte-identical to the `v0.16.0` tag (262 lines); heading-to-EOF identical to the tag and to `main` | 21,129 bytes, identical in all three. Heading-to-EOF identical (158,714 bytes). The section is 261 lines | REPRODUCED (N-6) |
| 43 | `CHANGELOG.md:118`: "so only the cursor's own error is the caller's `400`" | A corrupt metadata document makes `/filter` answer 400 at head | REFUTED (L-1) |
| 44 | `JUNIPER_DATA_API.md:995-996` "every other route but batch delete… 500"; `REFERENCE.md:1323` and `base.py:124` "Everywhere else" | batch-create answers **200**, with that item failed as "Dataset creation failed (ref: …)" | PARTLY REFUTED (N-1) |
| 45 | "One such file fails `/filter`, `/stats` and expired-dataset cleanup" (`CHANGELOG.md:126`, `REFERENCE.md:1327`, `base.py:125`) | It also fails every named create, GET `/versions` and GET `/latest` (500) | PARTLY REFUTED (N-3) |
| 46 | `REFERENCE.md:1373`: a symlink "planted at one is refused rather than followed out of the storage root" | True of a stripe file. A `locks/` swapped for a symlink after startup is followed (row 8) | PARTLY REFUTED (N-4) |
| 47 | CHANGELOG: "Four verification scripts changed"; "0.15.0 tried, and asyncio logged a traceback carrying the dataset id on every download" | At `v0.16.0` the harness and equivalence scripts exist and the other two do not. `v0.15.0`: 4 of 4 downloads carry the id | REPRODUCED |
| 48 | Noticed items: `local_fs.py:105` has no test; `update_tags` docstring is stale; the harness would reformat; #440 also edits the CHANGELOG | Coverage lists 105 as missed. Docstring at `base.py:401-403`. ruff 0.15.2 "Would reformat" the harness at both head and base. #440 is OPEN with no auto-merge, and edits `CHANGELOG.md` | REPRODUCED |
| 49 | Changed list: 13 files; `security.py` untouched | `git diff --stat`: the same 13 files | REPRODUCED |
| 50 | "No `.coverage` file or bytecode landed in the worktree" | I did not inspect the author's worktree | NO ARTIFACT |

## Findings: disposition

`data438-round1-laneA-reprobe.md`:
- **F1: fixed.** Rows 6, 12, 13 and 15.
- **F2: documented.** Row 16.
- **F3: fixed.** Row 17.
- **F4: fixed.** Row 18.
- **F5: fixed.** Row 19.
- **F6: fixed.** Rows 11 and 20.
- **F7: fixed.** A symlinked `.npz` is now a 500, and the docs say so (row 21).
- **F8: not fixed.** Flagged for an owner ruling as stated; the counts reproduce (row 22).

`data438-round1-laneB-refute.md`:
- **M1: fixed.** Same evidence as F1.
- **M2: fixed.** Stripes: rows 7, 8, 23 and 24.
- **L1: documented.** Row 16.
- **L2: fixed** (row 25). The TOCTOU is left open, as the body says. Outline N-4 too.
- **L3: fixed.** Row 11.
- **L4: fixed** for `StorageContainmentError` (rows 9, 10, 26). The same misattribution remains for a corrupt metadata document (L-1).
- **L5: documented, and widened.** Rows 27 and L-2.
- **L6: fixed.** Row 28.
- **L7: documented as a known issue.** Row 29.
- **N1: documented.** Row 30.
- **N2, N3, N4: fixed.** Rows 31 and 42.

`data438-round1-laneB-refute.md`'s "did not land": A1 F2 in `data428-round3-laneA1-security.md` is untouched (`MAX_PRECONDITION_FIELD_LENGTH` is still 8192), and so are A1 F3 and F4. `http_cache.py` changed only in comments and docstrings.

## Findings

### HIGH / MEDIUM
None.

### LOW

**L-1. "A storage fault is a 500" is true only for a file that leads out of the storage root. A corrupt metadata document is still the caller's 400.**
- **Where it is claimed:**
  - the title in `data_fixforward_pr_title.txt`;
  - `CHANGELOG.md:118`: "`/filter` now decodes its cursor before calling the store, so only the cursor's own error is the caller's `400`";
  - `juniper_data/api/routes/datasets.py:546-547`: "so that only the cursor's own error is answered as the caller's". That comment itself names "a stored metadata file that would not parse".
- **Evidence:** a `.meta.json` containing `{not json` gets 400 "Invalid request parameters" at head on GET `/{id}`, `/filter`, `/stats` and PATCH (`extra_probes.py` C).
  - Why: `JSONDecodeError` and pydantic's `ValidationError` are `ValueError`s. `app.py:237` maps only `StorageContainmentError` to 500.
  - The only change from base: `/filter`'s detail no longer echoes the parser's text.
- **Fix:** scope all three texts to "a stored file that leads out of the storage root". Alternatively, have LocalFS raise a storage-fault error for unparseable stored metadata and map that to 500 as well.

**L-2. The disclosed L5 stall has a cross-process arm the docs do not state.**
- **In one process** (disclosed): while an unnamed create's save runs, a GET of an unrelated dataset takes 1.507 s at head and 0.006 s at base (`window_probes.py` P2).
  - Scale: `LocalFS.save` of random float32 takes 0.73 s for 16 MiB and 2.9 s for 64 MiB, so a save near the 128 MiB default cap stalls the event loop for several seconds.
- **Across processes** (not stated): a create now holds its stripe's file lock for the whole save. Another process's `record_access` for a *different* dataset on the same stripe waited the full 2.00 s at head, against 0.00 s at base (`final_probes.py` PD). `record_access` runs on that process's event loop, so that whole process stalls, on 1 in 16 datasets.
- **What the docs say instead:**
  - `local_fs.py`'s `_meta_write_lock` docstring: stripe-sharing "within a process … costs nothing";
  - `constants.py:46-47`: a stripe is "contended only between worker processes";
  - `REFERENCE.md:1357-1362` ("The cost of the locks") names only `_version_lock`.
- **Exposure:** the service runs one worker, and the Dockerfile healthcheck allows 10 s × 3 retries.
- **Fix:** write the temp files before taking the locks, and only re-check and rename under them (the lift `REFERENCE.md:1361-1362` already names). Also state that a create holds its stripe for the whole save.

### NIT

- **N-1. batch-create is a second exception to "a 500 on every other route".**
  - Where: `docs/api/JUNIPER_DATA_API.md:995-996`, `docs/REFERENCE.md:1323`, `juniper_data/storage/base.py:124-125`.
  - Evidence: batch-create answers HTTP 200 with the item failed. `datasets.py:704` (`logger.exception`) logs the traceback, including the server-derived id, at ERROR.
  - Fix: name batch-create beside batch delete.
- **N-2. One of the 17 base failures is not a base defect.**
  - `test_a_storage_directory_that_cannot_hold_the_stripes_still_opens` fails on base at `test_conditional_requests.py:1351` (the test's own `iterdir` of the absent `locks/`). Base opens such a store without complaint.
  - Fix: say "16 fail on their defect; the 17th pins the new best-effort stripe creation" in `data_fixforward_pr_body.md`.
- **N-3. The list of what one such file breaks is incomplete.**
  - Where: `CHANGELOG.md:126`, `docs/REFERENCE.md:1327`, `base.py:125`.
  - Missing: every named create (`next_version_number` reads every document), GET `/versions` and GET `/latest` all answer 500. This predates the PR (400 at base).
  - Fix: add them to the list.
- **N-4. `locks/` containment is checked only when the store opens and when a stripe is missing** (`local_fs.py:101-105`, `:178-183`).
  - `O_NOFOLLOW` covers only the last path component. So a `locks` swapped for a symlink after startup, pointing at a directory that holds `{0..f}.lock`, is followed: the outside files are opened and locked, though nothing is created or written (`stripe_probe.py` H). This needs write access to the storage directory.
  - It overstates `REFERENCE.md:1373`, and the L2 row of `data_fixforward_pr_body.md` ("whose containment is checked").
  - Fix: open the stripes through a directory descriptor for `locks/`, opened once with `O_DIRECTORY` and `O_NOFOLLOW`; or soften the text.
- **N-5. "A stripe missing then is created when first locked" is not true for a read-only directory.**
  - Where: `docs/REFERENCE.md:1376` and `local_fs.py:117-118`.
  - Evidence: on a read-only directory the store opens, but the first lock raises PermissionError.
  - Fix: "…when first locked, once the directory is writable".
- **N-6. The `[0.16.0]` section is 261 lines, not 262.** `data_fixforward_pr_body.md` says 262, which counts the `## [0.15.0]` heading; the bytes are identical either way.
- **N-7. The stripe-count rationale overstates its numbers.**
  - `constants.py:46-48` says the suite "builds hundreds of stores, which at 256 stripes would cost a hundred thousand".
  - The full unit suite built 84 store directories, which is about 21,600 inodes at 256 stripes.
- **N-8. `record_access`'s docstring is stale** (`base.py:345-347`, "per-process lock … best-effort counting"), exactly as the `update_tags` one that `data_fixforward_pr_body.md` notices. It predates this PR.
- **N-9. A metadata-only dataset is a cache hit forever** (code reading only; predates this PR).
  - That is what N1's window leaves behind. The route's check (`datasets.py:248`) and `save_versioned`'s re-check both use `get_meta`, not `exists()`, so no create can ever repair it, and its artifact answers 404.
  - Fix: re-check with `exists()`.

## What this evidence cannot support
- **Forced interleavings** show only that the code allows or prevents each race. I measured no loss rates under load. Cross-process results are two processes on one host, on tmpfs; I tested no NFS and no multiple hosts.
- **ENOSPC** comes from the test's simulation and an strace syscall count. I did not exhaust a real volume, because the shared `/tmp` is at 85% of its inodes.
- **Save timings** are `LocalFS.save` of random float32 on tmpfs, not a real generator or a real disk.
- **Live parsing** ran on uvicorn 0.40.0 on the free-threaded 3.14.2 (httptools re-enabled the GIL). I did not test the production pins or a default-GIL build.
- **Not run:** mypy at its pinned 1.13.0, the doc-links hook, and pre-commit itself.
- **Code reading only:** the cached, Redis and Postgres stores, and L2's TOCTOU.
- **The harness ran once.** I did not sample it for flakiness.
- **I cannot re-derive** the author's first harness run, or the state of the author's worktree.

## Scripts
Scripts are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneA/scripts/`, and logs in `../logs/`. The same directory keeps `rfc9110.txt` and the renderer copy `notes_render_df21367d.py`. The extracted trees, the coverage copy and all temp data have been deleted.
- **Runners:** `run_in_tree.bash`, `origin_guard.py`, `run_suites.bash`, `run_coverage_copy.bash`, `run_harness_head.bash`, `run_equivalence_head.bash`, `run_negctl_vs_base_sweeps.bash`, `run_w11_reach_check.bash`, `run_counter_head.bash`, `run_ci_screens.bash`, `lint_changed.bash`, `mypy_diff.bash`, `run_probe.bash`, `run_*.bash`.
- **Probes:** `stripe_probe.py`, `create_race.py` with `create_child.py`, `inode_trace.py` with `inode_trace_parse.py`, `ows_live.py`, `symlink_meta_probe.py`, `window_probes.py`, `extra_probes.py`, `final_probes.py`, `classify_arms.py`, `m57_control_history.py`.
- **Checks:** `changelog_check.py`, `renderer_check.py`, `line_refs.py`, `v016_checks.bash`, `misc_git_checks.bash`.
- **Tree handling:** `extract_trees.bash`, `extract_tags.bash`, `make_basex.bash`, `check_origin.bash`, `cleanup.bash`.

**Documents referenced:** `data438-round1-laneA-reprobe.md`, `data438-round1-laneB-refute.md`, `data428-round3-laneA1-security.md`, `data_fixforward_pr_body.md`, `data_fixforward_pr_title.txt`, `rfc9110.txt`, juniper-ml `util/release_train/notes_render.py`. In juniper-data: `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md`, `.pre-commit-config.yaml`, `Dockerfile`, the changed `juniper_data/` files, and the four `util/ad-hoc/` scripts.

**Changed:** none in any repository. Outside scratch my only actions were:
- two `git fetch` runs in the juniper-data checkout: `origin fix/conditional-requests-round4-followups main` and `refs/pull/438/head`;
- read-only `gh` API calls;
- downloads of `rfc9110.txt` and the `ruff==0.15.2` and `juniper-ci-tools==0.9.0` wheels into scratch.
