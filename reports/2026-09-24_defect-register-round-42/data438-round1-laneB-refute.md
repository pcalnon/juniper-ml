<!-- Archived verbatim 2026-09-24 from subagent a48b63fe2cf4ce38b of session 8f86dec2 (final message). -->

**Verdict: REFUTED.** The eight items hold as code, but the claim #438 publishes on top of them is still false: "every route that edits or deletes a dataset takes the same locks, so the check cannot pass and then lose a race to another writer", and "within one process" on `CachedDatasetStore`. And the new lock on the delete paths adds an availability regression that is not disclosed.

Validated at head `28fced18`. The PR is still OPEN (merge state CLEAN) and `main` is still at its parent `1afc3484`, so there was no merged `main` to attack.

## Findings

### MEDIUM

**M1 — MEDIUM. `POST /v1/datasets` still writes the metadata with neither lock, so a conditional PATCH can pass its check and then erase a create.**
- **Where the claim is made:**
  - `juniper_data/api/routes/datasets.py:1237-1243` (the `update_dataset_tags` docstring, which FastAPI publishes as the OpenAPI description);
  - `docs/api/JUNIPER_DATA_API.md:1070-1075`;
  - `docs/REFERENCE.md:1266` and `:1330-1333`;
  - `CHANGELOG.md:62-66`.
- **Why it fails.** Create checks existence (`datasets.py:248`), generates, then saves through `save_versioned` (`:447`).
  - `juniper_data/storage/base.py:547-552` takes `_version_lock` only for a named dataset, and never takes `_meta_write_lock`.
  - Two creates of the same seeded params both pass the existence check, and the later `save` overwrites the earlier one.
- **Evidence, through the real routes** (`create_race.py` → `ev-create_race-head.out`):
  - Create A is held in generation, and create B completes.
  - A conditional PATCH naming B's representation passes its check and is held before its write.
  - A saved inside that window and answered 201, with tags `from-create-A`, description `A` and an `expires_at`.
  - The PATCH then answered **200 with an ETag**. The stored result is tags `['before','conditional-edit','from-create-B']`, description `B`, `expires_at` null. A's acknowledged create, including its TTL, is gone.
- **Two other instruments agree:**
  - `race_routes.py` (scenario S6): `save_versioned` lands inside the window at both head and base.
  - `xproc_rivals.py`: across two processes, `save_versioned` is the only rival that does not wait.
- **Exposure is low.** It needs two concurrent same-seed creates and a conditional PATCH inside the generation window. The census in `data428-round3-laneB-refute.md` found no consumer that sends a conditional PATCH.
- This is the same defect class `data428-round3-laneB-refute.md` rated MEDIUM, in a writer #438 did not list.
- **Fix:** make create-if-absent atomic. Re-check existence and save under `_version_lock` plus `_meta_write_lock`, in both `save_versioned` branches. That also closes the older create-vs-create lost write. Otherwise, name `POST /v1/datasets` and `/batch-create` as exceptions in all four texts.

**M2 — MEDIUM. Lock files for absent ids now pile up 100× faster, and the delete paths now need a free inode.**
- **(a) Growth.** `lockfile_growth.py` (→ `ev-lockfile_growth-{head,base}.out`) sent requests naming random valid ids that do not exist:

  | Requests | Lock files left at head | at base |
  |---|---|---|
  | 50 × `DELETE /{id}` | 50 | 0 |
  | 2 × batch-delete, 100 ids each | 200 | 0 |
  | 2 × batch-tags, 100 ids each | 200 | 0 |
  | 50 × `PATCH /{id}/tags` | 50 | 50 |

  - The files are never removed, by design (`juniper_data/storage/local_fs.py:138-143`).
  - Auth is off by default, and the default limiter is 60 requests/min per client. So one client can leave **6,000 inodes/min** at head, against 60/min at base.
  - The uncached `GET /v1/datasets` globs the whole directory. 2,000 lock files added 3.5–6.4 ms to it, about 2–3 µs per entry, measured on tmpfs.
- **(b) The delete paths fail without a free inode.** `delete_under_lock` must `os.open(..., O_CREAT)` the lock file before it unlinks anything (`local_fs.py:155`). `enospc_probe.py` simulated ENOSPC on lock-file creation only (→ `ev-enospc-{head,base}.out`), on datasets that were never read and so had no lock file yet:
  - at head, `DELETE` returned **500**, batch-delete **500** and cleanup-expired **500**, and nothing was deleted;
  - at base, they returned 204, 200 and 200, and everything was deleted.
  - `batch_delete` catches only `ValueError`, and `delete_expired` aborts at the first error.
  - So the operations that free space fail on exactly the volume that needs them, and #438 makes exhausting it 100× cheaper.
- `CHANGELOG.md:74-75` discloses the lock files, but not the rate or the delete regression.
- **Fix:** either pre-create a bounded set of lock stripes at store init (for example `locks/<sha256(id)[:2]>.lock`), or skip locking when the metadata is absent and fall back to an unlocked unlink when the lock file cannot be created.

### LOW

**L1 — LOW. The "within one process" claim for `CachedDatasetStore` is false.**
- **Where it is claimed:** `datasets.py:1240-1242`, `docs/api/JUNIPER_DATA_API.md:1074-1075` and `CHANGELOG.md:72-73`.
- **Mechanism:**
  - `get_meta` reads the cache first (`juniper_data/storage/cached.py:122-126`).
  - `get_artifact_bytes` repopulates the cache from a primary snapshot with no lock (`cached.py:153-159`). `warm_cache` does the same (`:292`).
- **Evidence** (`cached_race.py` → `ev-cached_race-head.out`; identical at base):
  - A download that missed the cache was held before its cache write, while an unconditional PATCH added `edit-1` (200).
  - The download then wrote the stale snapshot into the cache.
  - The download's own `record_access` wrote that stale copy back to the primary, so `edit-1` was lost before any conditional request.
  - A GET then served the stale representation, and a PATCH with that ETag as `If-Match` answered 200.
- The mechanism is pre-existing, and the app wires only LocalFS (`juniper_data/api/app.py:42`). What is new is the published guarantee.
- **Fix:** drop the cached store from the claim, or populate the cache under the locks.

**L2 — LOW. A symlink planted at `<id>.meta.json.lock` is followed out of the storage root, and three more routes now reach it.**
- `_lock_path` checks containment of the metadata path only (`local_fs.py:123-126`). `os.open` has no `O_NOFOLLOW` (`:155`), and nothing in the file uses it.
- `security_probe.py` section C used a dangling symlink to a path outside the root:
  - at head, DELETE (404), batch-delete (200) and batch-tags (200) each **created the outside file**, mode 0600;
  - at base, none did (`ev-security_probe-{head,base}.out`).
- This needs write access to the storage directory.
- By code reading only (not demonstrated): the containment check's `resolve()` (`:114`) and every later open are separate path lookups, so a symlink swapped in between them is followed.
- **Fix:** open with `O_NOFOLLOW|O_CLOEXEC`, and route the lock path through `_build_path`. The lock stripes in M2 also remove this.

**L3 — LOW. The new artifact path for a symlinked metadata file logs an ERROR traceback carrying the id on every download.**
- `record_access` (`datasets.py:1112,1145,1149`) raises `StorageContainmentError` inside a `call_soon` callback.
- asyncio then logs "Exception in callback …" at ERROR, with a traceback ending `Path traversal detected for dataset_id: 'spiral-3.0.0-symlinked0000000'`. This happens on every 200 and every 304 (`ev-security_probe-head.out`, section D).
- It contradicts the route's ERR-08 comment (`datasets.py:1076-1077`) and `docs/REFERENCE.md:1316` ("names only the exception type").
- At base the route answered 400 and logged no traceback.
- **Fix:** skip `record_access` when the metadata was unreadable, and have the new test assert on the logs.

**L4 — LOW. `StorageContainmentError` is called a storage fault but is answered as the caller's error everywhere else.**
- `security_probe.py` section D (same at base):
  - `GET /{id}`, `/access`, `PATCH`, batch-tags, batch-export, `DELETE`, `/stats` and `/cleanup-expired` all answer 400 "Invalid request parameters", logged at DEBUG only.
  - batch-delete reports the dataset as not_found, with no log.
  - `/filter` returns `Path traversal detected for dataset_id: '<id>'` as its 400 detail (`datasets.py:559-562`).
  - One such file breaks `/filter`, `/stats` and cleanup for the whole store.
- `juniper_data/api/app.py:216-231` already maps the equivalent server fault (`PydanticSerializationError`) to 500.
- `CHANGELOG.md:92` discloses the 400s. The error class's docstring ("the 400 the app's ValueError handler gives it") is wrong for `/filter`.
- **Fix:** map the error to 500 in `value_error_handler`.

**L5 — LOW. Deletes and batch-tags now hold the process-global `_version_lock` for the whole store call, and `record_access` takes that lock on the event loop.**
- `loop_stall.py` used `CachedDatasetStore`, whose delete runs `_emit_cached_count`, a `list_datasets(limit=10000)` (`cached.py:209`). I simulated that call at 1 s.
- An unrelated `GET /v1/datasets` took **0.707 s** at head and 0.005 s at base (`ev-loop_stall-*.out`).
- On LocalFS the lock is held only for a few unlinks. The PR does not disclose this.
- **Fix:** move `record_access` off the event loop, and call `_emit_cached_count` outside the lock.

**L6 — LOW. The lock order is pinned only by a 30 s timeout, and no harness arm swaps it.**
- My mutant MB1 takes the flock first in `delete_under_lock`.
- It is a real ABBA deadlock with `record_access`: both threads were stuck at 10 s, with windows widened (`ev-mb1_detail.out`).
- Only `test_a_delete_cannot_land_inside_a_conditional_patchs_window` catches it, after 36 s, with a bare `_queue.Empty`. `test_every_route_that_deletes_holds_both_locks` passes.
- This leaves unverified what `base.py:454-456` asserts: that the acquisition order is uniform.
- **Fix:** assert `_file_lock_is_held(...) is False` when `_version_lock` is entered, and add the swap as arm M51 in `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py`.

**L7 — LOW (pre-existing). Cleanup still decides expiry outside the locks, on a snapshot up to 5 s old.**
- `base.py:477-485`. In `cleanup_toctou.py`, two store instances stood in for two workers.
- Worker B's cleanup deleted `X` after worker A had re-created it with no TTL, at both head and base.
- **Fix:** pass an expiry predicate into `delete_under_lock` and evaluate it on a fresh read under the locks.

### NIT

- **N1. "never a 200 with an ETag" is too strong.** It appears in `docs/api/JUNIPER_DATA_API.md:1076-1078`, `docs/REFERENCE.md:1335-1337`, `CHANGELOG.md:70-71` and the route docstring.
  - LocalFS `update_meta` checks existence (`local_fs.py:391`) and then renames (`:402`).
  - `gone_window_probe.py`: a removal landing between those two steps got **200 + ETag** and resurrected a metadata-only dataset, at both head and base.
  - The early window is fixed (404 at head, 200 at base).
- **N2. The two `juniper_data/api/http_cache.py` docstring errors are still there.** `primer-correction-round2-laneA-reprobe.md` N4 and `primer-correction-round2-laneB-refute.md` N-4 assigned them to this fix-forward.
  - Lines 17-19 quote "Same content, possibly different bytes" as RFC 9110 §8.8.1's definition. It is absent from `rfc9110.txt`, fetched from rfc-editor.org (sha256 `21c1cdce…`, §8.8.1 at text lines 3393-3475).
  - Line 33 still lacks "cleaned up": `datasets.py:248-267` returns an expired dataset as a cache hit.
- **N3. #437's bullet is not byte-unchanged.** A "*Moved here from `[0.16.0]`…*" sub-bullet sits inside it, so `parse_unreleased` will publish that note in the next Release body (`changelog_check.out` §2, §7).
- **N4. "with the same response" (`CHANGELOG.md:64`) is not quite true.** batch-tags now reports a dataset that was gone by the write as not_found instead of updated.

## What held (attacks that did not land)
- **Locking, in-process and across two processes** (`race_routes.py`, `xproc_rivals.py`):
  - At head, batch-tags, DELETE, batch-delete, cleanup and `record_access` all wait out a conditional PATCH's window.
  - At base, the three delete paths land inside it: the PATCH reports success for a deleted dataset.
- **The spaces-and-tabs-only `*`**, sent as raw bytes to live uvicorn with h11 and with httptools:
  - `*` wrapped in NBSP or NEL is malformed at head (GET `If-None-Match` 200, GET `If-Match` 412, PATCH 412). At base the same bytes read as a star.
  - obs-fold is unfolded to a space by h11 and rejected with 400 by httptools. RFC 9110 §5.5 allows both.
  - A tab-only, empty or lone-comma field is an empty list.
  - `* ,`, `, *` and two `*` lines are malformed, and VT or FF gets 400.
  - Every outcome is in the documented safe direction.
- **Traversal:** I sent 32 hostile ids to `delete_under_lock`, `batch_delete` and `update_tags`, 30 in a batch-delete body, and 7 percent-encoded DELETE paths. Nothing was created outside the root.
- **Instruments:**
  - The harness at head printed `PASS: 53 mutations`: 75 CAUGHT, 74 controls OK, 0 vacuous or over-broad, exit 0.
  - The coverage script `util/ad-hoc/2026-09-24_count_conditional_request_harness_coverage.py` reports 53 arms, 69 tests, 58 must-fail, 11 control-only and 0 unnamed.
  - The unit suite collected 1880 tests and exited 0.
  - I ran the head's 11 new test functions against base: 7 fail, each for its own defect, and 4 pass, as the commit says.
  - My mutants MB2–MB6 were all caught.
- **Equivalence:** `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py` found 0 mismatches in 3,495,076 inputs. Its negative control, `util/ad-hoc/2026-09-24_verify_equivalence_sweeps_catch_long_list_mutants.py`, passes, and it fails when the structured sweep is cut to 7 elements.
- **CHANGELOG:**
  - At head, `[0.16.0]` is byte-identical to the tag's section.
  - `[Unreleased]` runs Added, Changed, Fixed, which is Keep-a-Changelog order.
  - origin/main's `parse_unreleased` gives Added 1, Changed 1, Fixed 5, breaking False.
  - `changelog_version_section("0.16.0")` gives 6/4/1/4, breaking True, which matches the published Release's "Breaking changes: YES".
  - #436's and #437's entries match the tree.
  - The Redis, Postgres and in-memory `exists()` do check metadata alone, as the docs now say.

## What did not land
- A1 F2 in `data428-round3-laneA1-security.md` (lower the field-length cap): still 8192 at `http_cache.py:77`.
- N2 above, from `primer-correction-round2-laneA-reprobe.md` and `primer-correction-round2-laneB-refute.md`.
- Lock files for absent ids, from `data428-round3-laneB-refute.md`: widened, not closed.
- A1 F3 and F4 in `data428-round3-laneA1-security.md`: out of scope and untouched.

## What this evidence cannot support
- **ENOSPC was simulated**, by wrapping `os.open` in `local_fs` only. No real filesystem was exhausted: this host's shared `/tmp` was at 99% of its inodes, so I capped the listing test at 2,000 files. The per-entry cost is from tmpfs, and anything at millions of files is extrapolation.
- **The races are forced interleavings**, not frequencies. MB1's deadlock used 0.3 s widened windows.
- **Library-level only:** the cached-store and loop-stall results, since the app wires LocalFS. The 1 s scan is simulated. Redis and Postgres were read, not run.
- **Parser versions:** live parsing ran on uvicorn 0.40.0, h11 0.16.0 and httptools 0.7.1, not the production pins.
- **Equivalence reach:** the 0 covers lists of 12 elements or fewer. A mutant that differs only from the 13th element on was caught by no sweep (`eq_instruments.py` run 4).
- **Not assessed:** #435; the ceremony's `--target-sha`; each harness arm's failure reason (I checked counts only). The v0.16.0 PyPI publish is parked "waiting" at the pypi gate, and PyPI's latest is still 0.15.0.
- **Record:** one Lane B agent, one iteration. Entry points were code, `git archive` extracts of `28fced18`, `1afc3484`, `39d1cab2` and `5f11fcfc`, and live probes.

## Scripts
All are under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data438-laneB/`.
- **Runners:** `run_py.bash`, `run_pytest.bash`, `run_in_tree.bash`, `run_harness_head.bash`, `ows_driver.bash`, `serve_scratch.py`.
- **Probes:** `race_routes.py`, `create_race.py`, `xproc_rivals.py`, `cached_race.py`, `lockfile_growth.py`, `enospc_probe.py`, `security_probe.py`, `ows_live.py`, `gone_window_probe.py`, `cleanup_toctou.py`, `loop_stall.py`.
- **Instrument checks:** `my_mutants.py`, `mb1_detail.py`, `eq_instruments.py`, `cross_run.py`, `changelog_check.py`.
- **Evidence:** the `ev-*.out` files, `harness-head.log`, `suite-head.log`, `collect-head.log`, `changelog_check.out`, `rfc9110.txt`, and the extracted trees `tree-head/` and `tree-base/`.

I wrote to no repository. Outbound traffic was GitHub, PyPI and rfc-editor.org reads only, and all three servers I started were stopped.

**Documents referenced:** `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, `data428-round3-laneA1-security.md`, `data428-round3-laneA2-claims.md`, `data428-round3-laneB-refute.md`, `primer-correction-round2-laneA-reprobe.md` and `primer-correction-round2-laneB-refute.md`.

**Changed:** none.
