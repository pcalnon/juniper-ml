<!-- Archived verbatim 2026-09-24 from subagent a46e715a6801b98ca of session 2fba4397 (final message). -->

I pushed one more GitHub-signed commit to `fix/conditional-requests-round4-followups`, and every finding the two reports raised is handled. No PR opened. Lane B's MEDIUM (a read during a create stalling the whole service) is fixed: on the live probes the new head stays responsive where `d1c66a11` stalled for 6–7 s.

**New head: `94ce8b1fa8e229c92e8674a1074d518e59142488`**
- Its parent is `d1c66a11`, GitHub reports it signed (`verified: true`), and its tree (`6769c0da…`) is identical to the worktree.
- The local branch is reset to it and in sync with origin. `main` is still at `0f0f7e0e`.
- The commit message ends with exactly the two required trailer lines. The paragraph just above them carries the symbol-loss waiver: `Allow-Symbol-Loss: method:LocalFSDatasetStore.save func:_file_lock_is_held`. Both symbols shrank because their bodies moved out into new functions, not because anything was deleted.
- **Before merging:** the waiver lives only in this second commit's message. The repo's default squash message keeps it; a hand-written squash body that drops it turns `main` red.

## One regression of my own, found and fixed before the push
Holding the storage root open meant that if someone deleted the storage directory and recreated it at the same path while the service ran, every write failed until restart. `d1c66a11` and `main` recover from that; I checked all three heads. The store now reopens the root by path when that happens. A new test and a new harness arm (M86) pin it.

## Dispositions: `data438-fixforward-round1-laneB-refute.md`
- **M-1 (MEDIUM) — fixed, both halves.**
  - Access recording now runs on its own single-thread executor, which the app shuts down on exit. Failures are logged by exception type only, and `GET /{id}/access` waits for pending recordings first, so its count stays accurate.
  - A create now compresses and writes its artifact before taking any lock. Only the existence re-check, the version, the metadata write and the renames run under the locks.
  - `REFERENCE.md`'s old lines 1357-1362, the CHANGELOG cost statement and the stripe-cost texts are corrected.
- **L-1 — fixed.**
  - If a lock stripe can't be created (disk full, read-only, no permission), the lock falls back to an exclusive lock on the storage root, which needs no new inode.
  - Leftover per-dataset lock files from earlier versions are removed when the store opens.
  - The tests' disk-full simulation now also refuses `mkdir`.
  - `CHANGELOG.md:93-94`, `REFERENCE.md:1374-1375` and the PR body are scoped.
- **L-2 (and lane A N-4) — fixed.** `locks/` is opened once without following symlinks, and each stripe is opened through that held descriptor, never by path.
  - The live-target tests are split by timing. MX23 is pinned with a *dangling* symlink planted before the store opens, because following a symlink to an existing file creates nothing visible. MX24 is pinned with a live-target symlink planted after it opens.
  - The `locks/` refusal (MX13/MX14) is pinned too.
- **L-3 (and lane A L-1) — documented, not remapped.** The title, `CHANGELOG.md`, the `/filter` comment (old `datasets.py:546-547`) and the docs now say only a stored file that leads out of the storage root is a 500. Unparseable metadata staying a 400 is recorded as a known issue, and so is a timezone-naive cursor or `created_after` being a 500.
- **L-4 — fixed as a consequence of M-1.** The event loop no longer waits on any lock. The remaining cost (a writer on the same stripe waits for the other process) is stated in the docs.
- **L-5 — fixed.** Added a two-process create test (MX10) and late-create tests for a named dataset (MX1) and for different content (MX9).
- **N-1** fixed: only a refused (out-of-root) metadata file skips the access record; `API.md:935-938` and the `/access` docstring are updated.
- **N-2** fixed in the docs: batch-create is named as the second exception.
- **N-3** fixed: stripe creation carries on past a stripe that fails.
- **N-4** fixed both ways: a non-directory `locks` stops the store from opening, and logging is configured before the store opens.
- **N-5** fixed in the PR body.
- **N-6** fixed: the stale `record_access` docstring (and the `update_tags` one).

## Dispositions: `data438-fixforward-round1-laneA-reprobe.md`
- L-1, N-1, N-2, N-4 and N-8 are the same as lane B's L-3, N-2, N-5, L-2 and N-6 above.
- **L-2** — fixed with M-1.
- **N-3** — fixed: `/versions`, `/latest` and every named create are added to the lists of routes one bad file breaks.
- **N-5** — fixed: the text now says "once the directory is writable".
- **N-6** — fixed: `[0.16.0]` is re-measured at 261 lines, byte-identical to the tag.
- **N-7** — fixed with a new measurement. The unit suite actually builds 161 store directories here and 144 on `d1c66a11`. Lane A's 84 was only the directories left behind in pytest's temp folder. `constants.py` now says "some 160 … about 41,000".
- **N-9** — recorded as a known issue rather than changed, because re-checking with `exists()` would change what a create answers for a half-written dataset.
- Your item 15 (`datasets.py:1282` comment) and item 16 (the 16-of-17 wording and 261 lines) are both done.
- The out-of-scope items (F8, L7, data428 A1 F2-F4, `security.py`, data#440) are untouched.

## Verification
| Check | Result |
|---|---|
| Unit suite | 1923 passed, 7 subtests |
| `run_coverage.bash` | 1783 passed, 140 deselected; 97.60%; PASS |
| api + integration | 118 passed |
| Non-vacuity harness (89 arms) | PASS; 132 caught, 0 vacuous, 135 controls OK |
| Coverage counter | 89 arms; 111/111 tests named, 100 must-fail |
| pre-commit (12 files) | all Passed or Skipped |
| Symbol-loss screen, `--base 0f0f7e0e` | 2 findings, both waived, exit 0 |
| Docs screen, `--base 0f0f7e0e` | 19 warnings, 0 fail, exit 0 |
| New test files on `d1c66a11` / `0f0f7e0e` | 17 / 39 of 123 fail, each classified in the PR body |
| Merge with data#440 (head `0bee089e`) | clean in either order |

The equivalence sweep was not re-run because `http_cache.py` was not touched.

Lane B's probes, new head against `d1c66a11`:
- **`stall_probe2.py`:** 6.05 s read and 6.04 s health stall on `d1c66a11`. It cannot measure the new head: the temp file it waits for now appears only after the create has finished. A variant that reads throughout the create (`util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py`) shows slowest reads of 7.4 s on `d1c66a11` against 0.66–0.74 s here.
- **`xproc_stall_probe.py`:** GET 4.693 s → 0.011 s; health 4.686 s → 0.014 s.
- **`xproc_create_race.py`:** the first create is not overwritten on either head; with MX10 applied it is overwritten on both.
- **`stripe_probe.py`:**
  - H: deletes fail with ENOSPC on `d1c66a11` and succeed here.
  - L1: the lock is now taken on the real stripe.
  - M: nothing is created outside the root.
- **`access_suppression_probe.py`:** count 0→0 on `d1c66a11`, 0→1 here.
- **`fault_survey.py`:** the same status on all 95 rows. The one difference is on the 4 unparseable-metadata artifact rows, where this head logs an extra type-only warning that names no id.

## Noticed, not changed
- A large create still blocks the event loop once for about 0.73 s: `compute_checksum` runs on the loop (`datasets.py:446` here, `:392` on `main`).
- While `locks/` can't be created, every lock repeats the warning.
- `/access` and shutdown wait for the recorder with no time limit.
- A few defensive error branches in `local_fs.py` have no test (lines 175, 183, 237, 243-248, 325-326).
- Batch-create still logs a traceback for a symlinked metadata file, as `main` does; the id in it is server-computed.
- A process that forks while a store is open would share the root's lock with its child.
- The ad-hoc harness would reformat under `ruff format`.

## Files
**Pushed (juniper-data):** `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md`, `juniper_data/api/app.py`, `juniper_data/api/routes/datasets.py`, `juniper_data/storage/base.py`, `juniper_data/storage/constants.py`, `juniper_data/storage/local_fs.py`, `juniper_data/tests/unit/test_conditional_requests.py`, `juniper_data/tests/unit/test_meta_cross_process_lock.py`, `juniper_data/tests/unit/test_phase_2d_metrics.py`, `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py`.

**Updated drafts** (both reports cited in the new round-2 section):
- `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/data_fixforward_pr_title.txt`
- `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/data_fixforward_pr_body.md`

**New, uncommitted, in your juniper-ml worktree** (the throughout-read probe; commit it or not as you see fit): `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py`

I pruned the extracted trees and temp directories under `scratchpad/r5`, and kept the outputs, the commit message files and lane B's adapted scripts. Every server I started is stopped, and `/tmp` inodes are at 82%.
