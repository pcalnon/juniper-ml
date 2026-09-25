<!-- Archived verbatim 2026-09-24 from subagent a641405b9532742e6 of session 2fba4397 (final message). -->

# Lane B (adversarial refutation): juniper-data `fix/conditional-requests-round4-followups` at `d1c66a11`

## Verdict: REFUTED

Most of the change works:
- A create is now atomic against another create, both in one process and across two.
- The 16 lock stripes stop lock files from piling up.
- A stored file that leads out of the storage root is now a 500.
- The order the two locks are taken in is now pinned by a test.
- The implementer's non-vacuity harness reproduces: PASS, 70 mutations.

It still fails validation for four reasons:
1. **MEDIUM:** it moves a whole-service stall onto the create path every real client uses, and its own docs understate how long the stall lasts.
2. Four texts claim more than the code does: the inode claim, the `/filter` claim and the title's "a storage fault is a 500", the "every route but batch delete" claim, and "only the lock files are touched".
3. Two round-1 findings are only partly fixed: M2(b) and L2 in `data438-round1-laneB-refute.md`.
4. No test can fail on the cross-process half of the create fix. My mutant MX10 survives the unit, api and integration suites, and a two-process probe shows the lost create it allows.

## Findings

### HIGH
None.

### MEDIUM

**M-1. Every create now freezes the whole service for the rest of its save if any read arrives during it. Measured: 6.6 s for one 80 MB create and 10.5 s for two, against 0.01 s on `main`. The docs say the stall ends "when the save completes", which is false.**

How it happens:
- `save_versioned` holds `_version_lock` while `self.save` compresses and writes the NPZ (`juniper_data/storage/base.py:578-585`; `local_fs.py:258-277`).
- `_version_lock` is a class attribute, so there is one per process (`base.py:137`).
- `record_access` takes the same lock (`base.py:350`), and the routes run it on the event loop through `call_soon` (`juniper_data/api/routes/datasets.py:1009, 1157, 1165`).
- So the event-loop thread blocks on the lock, and every request waits.

Why it matters now:
- On `main` only a named create held the lock for its save.
- Every ecosystem client creates unnamed datasets:
  - juniper-cascor `src/api/lifecycle/manager.py:4873`;
  - juniper-canopy `src/demo_mode.py:1105` and `:2022`;
  - juniper-recurrence `juniper-recurrence/juniper_recurrence/data.py:46`.

Measurements (`stall_probe2.py`): a live uvicorn server with one worker over LocalFS; an unnamed create of gaussian data at 2 × 100,000 × 100 (about 80 MB); its save takes about 7.1 s on this box; a GET of an unrelated small dataset is sent 0.5 s into the save.

| Tree and read | Read latency | Max `/v1/health` latency |
|---|---|---|
| main, metadata GET | 0.009 s | 0.137 s |
| main, artifact GET | 0.010 s | 0.189 s |
| head, metadata GET | 6.560 s | 6.549 s |
| head, artifact GET | 6.614 s | 6.598 s |

- **Control** (`stall_probe.py`, head, no read during the save): health peaked at 0.173 s. The stall comes from `record_access` waiting for the lock, not from CPU load.
- **Two creates** (`stall_probe3.py`): the read's `record_access` queued behind a second create that was already waiting for the lock. The loop waited out both saves:
  - head: the read took 10.506 s, health peaked at 10.483 s, and the first create's own 201 arrived at 15.34 s although its save began at 1.63 s;
  - main: 0.008 s and 0.116 s.

Against the service's probe timeouts:
- The Helm readiness probe times out at 5 s and liveness at 10 s (juniper-deploy `k8s/helm/juniper/values.yaml:80-91`, local checkout `d589dd9`).
- Compose uses `timeout: 10s` (`docker-compose.yml:76-80`, used at `:202-204`), and the image uses `HEALTHCHECK --timeout=10s` (juniper-data `Dockerfile:110-111`).
- One large create already exceeds the readiness timeout; two exceed liveness.

Disclosure: `CHANGELOG.md:85-87` gives no size for the cost. `docs/REFERENCE.md:1357-1362` says a GET "stalls the loop until the save completes". In fact the stall lasts until every save queued ahead of the read has finished.

Fix:
- Run `record_access` off the loop, for example `loop.run_in_executor(None, store.record_access, dataset_id)`, with its exceptions logged by type only.
- And/or shrink the locked section: write the temp files outside the locks, then re-check existence and rename them under the locks.
- Correct the bound in `docs/REFERENCE.md`, and state the size of the cost in `CHANGELOG.md`.

### LOW

**L-1. On a volume that was already out of inodes when this version first starts, deletes still fail. The CHANGELOG states the fix without that condition. So M2(b) in `data438-round1-laneB-refute.md` is only partly fixed.**

How it happens:
- If creating `locks/` fails at startup, the store logs the error and opens anyway (`local_fs.py:121-126`).
- Every later lock then has to create the directory (`_open_lock_stripe` → `_ensure_lock_dir` → `mkdir`, `local_fs.py:177-183`), which needs a free inode.

Evidence:
- `stripe_probe.py` case H: ENOSPC is simulated on `mkdir locks` and on any new file. With the dataset already on disk, `delete_under_lock`, `batch_delete` and `delete_expired` each raise `OSError(28)`, which is a 500 through the routes, and nothing is deleted.
- Case I: when the stripes already exist before inodes run out, deletes work.

Why this is the upgrade path:
- A 0.16.0 or #438 deployment runs out of inodes through its per-id lock files.
- This version leaves those files in place: `legacy_lockfiles_probe.py` shows all five `*.meta.json.lock` files survive. It then needs 17 new inodes before it can delete anything.

The tests cannot see this:
- `_NoFreeInodes` (`test_conditional_requests.py:299`) replaces only `local_fs.os.open`. `Path.mkdir` still creates `locks/`.
- My mutant MX4, which drops the lazy `_ensure_lock_dir()` call, survives the unit, api and integration suites.

Overclaims:
- `CHANGELOG.md:93-94`: "Taking a lock needs no free inode, so on a volume out of inodes `DELETE`, batch delete and cleanup still delete".
- `docs/REFERENCE.md:1374-1375`.
- The PR body: "a delete needs no free inode".

Fix:
- When no stripe can be opened, `flock` a descriptor of the storage root, opened `O_RDONLY|O_DIRECTORY`, which needs no inode. Or fall back to an unlocked unlink for deletes.
- Remove the legacy `*.meta.json.lock` files at startup.
- Scope all three texts.

**L-2. L2 in `data438-round1-laneB-refute.md` is only partly fixed. The new lazy-create path can still create a lock file outside the storage root, and a `locks/` symlink planted after startup is followed.**

How it happens:
- `_open_lock_stripe` checks `locks/` in `_ensure_lock_dir()`, then opens `locks/<k>.lock` by path with `O_CREAT` (`local_fs.py:177-183`).
- `O_NOFOLLOW` protects only the last path component (`local_fs.py:174-176`).

Evidence from `stripe_probe.py`:
- **Case M** (a forced interleaving: `locks/` swapped for a symlink after the check): `update_tags` succeeded, and it created `outside/swapped/1.lock`.
- **Case L1** (`locks/` replaced by a symlink after startup, pointing at a directory that holds `1.lock`): `update_tags` succeeded, and the lock it took was on `outside/withstripes/1.lock`. That lock no longer excludes anyone using the real stripe, and whoever holds that file can stall the service (see L-4).

Needs write access to the storage root, which is L2's own precondition. The PR body's "Not addressed" note names only the older `_build_path` race, not this new instance.

Fix: open `locks/` once with `O_DIRECTORY|O_NOFOLLOW`, keep that descriptor, and open each stripe through it with `dir_fd=` and `O_NOFOLLOW`, never re-resolving the path.

**L-3. The PR title's "a storage fault is a 500" and `CHANGELOG.md:117-118`'s "only the cursor's own error is the caller's `400`" are both false. A corrupt or schema-invalid metadata file is still answered as the caller's 400.**

How it happens:
- Only `StorageContainmentError` is remapped to 500 (`juniper_data/api/app.py:237-242`).
- Any other `ValueError` from a store still gets 400 "Invalid request parameters" (`app.py:243-247`): `JSONDecodeError` or pydantic's `ValidationError` from `get_meta` (`local_fs.py:317-320`).

Evidence from `fault_survey.py` (same on `main` and head for these rows):
- Faults `meta-corrupt-json` and `meta-bad-schema` answer 400 on 11 of 19 route cases: GET, `/access`, both PATCH forms, batch-tags, create, `/filter`, `/stats`, `/versions`, `/latest` and cleanup.
- One such file fails `/filter`, `/stats` and cleanup for the whole store, and blames the caller.
- Head did remove the echo: `/filter`'s 400 detail is now generic.

Pre-existing, and still a 500 on both trees (`client_error_probe.py`): a cursor that encodes a naive datetime, and a naive `created_after`. Each raises `TypeError` at `base.py:81-83` and `base.py:640-643`. The new cursor pre-decode (`datasets.py:545-556`) was the natural place to catch it.

Fix:
- Scope the title and the CHANGELOG sentence to "a stored file that leads out of the storage root".
- Optionally map unparseable metadata to 500 through a dedicated error.
- Reject timezone-naive datetimes in `decode_cursor`.

**L-4. The stripes let another process's lock on an unrelated dataset stall the whole service.**

How it happens:
- Every lock taker takes `_version_lock` first and holds it while it waits for the file lock (`base.py:447, 578`).
- One in 16 unrelated ids share a stripe (`local_fs.py:156-164`).

Evidence (`xproc_stall_probe.py` with `stripe_holder.py`): a second process holds the lock of an absent id for 5 s. At head that id shares stripe 3 with dataset T.

| | DELETE T | GET of a third dataset (stripe 1) | Max `/v1/health` |
|---|---|---|---|
| head | 4.983 s | 4.697 s | 4.68 s |
| main (per-id lock files) | 0.010 s | 0.006 s | 0.054 s |

What the code says: `constants.py:45-46` ("a stripe is contended only between worker processes, and the service runs one") and `local_fs.py:200-202` state the premise. Nothing says that the price is a service-wide stall whenever a second process uses the directory. `docs/REFERENCE.md:313` already allows for several workers.

Fix: the M-1 fix removes the loop stall. Otherwise, state the cost in the CHANGELOG.

**L-5. No test can fail on the cross-process half of lane A F1 / lane B M1, or on the named-create re-check. Mutants of each survive the unit, api and integration suites.**

Instrument: `my_mutants.py`, first against seven related test files, then (`14_mutants_full_suite.bash`) against `juniper_data/tests/{unit,api,integration}`.

- **MX10** moves the re-check outside the file lock: the check runs under `_version_lock`, then the file lock is taken for the save. It survives every suite.
  - `xproc_create_race.py` shows what it allows: two processes create one id.
  - At head, the late create waited and wrote nothing.
  - Under MX10, it overwrote the first create, which had already been acknowledged: stored tags became `['from-A']`.
  - On `main`, the later save also won, which is the original defect.
  - Why the tests miss it: `test_every_route_that_creates_holds_both_locks` (`test_conditional_requests.py:1236`) checks that the lock is held during `save`, not during the check. `update_tags` has a dedicated test for exactly this (lane A's N7 / harness M32); creates do not.
- **MX1** re-checks unnamed creates only. It survives every suite.
- **MX9** overwrites the stored dataset when its checksum differs. It survives every suite. This matters because unseeded or `end_date=None` generators produce different data under one id.
- **MX23** drops `O_NOFOLLOW` from the startup create. It survives every suite.
- **MX24** drops `O_NOFOLLOW` from the first, non-creating open. It survives the seven files. The only symlink test plants a dangling symlink after startup, which only the lazy `O_CREAT` open sees.
- **MX13 and MX14** remove or swallow the `locks/` containment refusal. They survive the seven files; the PR body already discloses that line 105 is untested.
- **Caught:** MX2 (a per-process `hash()` picks the stripe; `test_meta_cross_process_lock.py` catches it) and MX17.

Fix:
- Add a two-process create test modelled on `test_meta_cross_process_lock.py`.
- Add a late-create test for a named dataset, and one where the content differs.
- Plant a symlink with a live target, before the store opens.

### NIT

- **N-1. A transient metadata failure now drops a real access record, and two texts still promise every download is counted.**
  - Any exception sets `metadata_readable = False` (`datasets.py:1094-1097`).
  - `access_suppression_probe.py` injects one EMFILE on the artifact route's first `get_meta`: `main` counted the access (0 → 1); head did not (0 → 0).
  - `docs/api/JUNIPER_DATA_API.md:935-938` and the `/access` docstring (`datasets.py:1020-1022`, published as OpenAPI) still say every 200 or 304 download is recorded.
  - Fix: skip only for `StorageContainmentError`, or catch the error inside the callback and log it by type; update both texts.
- **N-2. Batch-create contradicts the new "500 everywhere but batch delete, logged by type only".**
  - `fault_survey.py`, symlinked or dangling metadata file: batch-create answers 200 with the per-item error "Dataset creation failed (ref: …)".
  - It also logs an ERROR traceback ending `StorageContainmentError: Path traversal detected for dataset_id: '…'` (`datasets.py:698-704`). `main` does the same.
  - Contradicted texts: `docs/api/JUNIPER_DATA_API.md:994-997`, `docs/REFERENCE.md:1321-1325`, `CHANGELOG.md:115` and `base.py:124-126`.
  - The id there is a hash the server computes, so the ERR-08 exposure is small; the texts are simply wrong.
- **N-3. Creating the stripes stops at the first bad entry** (`local_fs.py:121-126`).
  - `stripe_probe.py` case E: a dangling symlink planted at stripe 1 before startup. Only `0.lock` was created; the other 14 stripes now need an inode on first use.
  - The only signal is one WARNING, which says "each is created when first locked".
  - Every lock on the planted stripe fails with ELOOP (500). That covers 6.2% of 1,000 sample ids.
- **N-4. With a regular file at `locks`, the service starts healthy but every write 500s** (`locks_file_live_probe.py`).
  - Health answers 200; create, PATCH and DELETE answer 500 (`NotADirectoryError`).
  - The warning is emitted from the store constructor (`app.py:43`), before `configure_logging` (`app.py:46`). It therefore reaches the log as a bare line with no timestamp, level or logger name, unlike every other startup line.
  - Also: a `locks` symlink that points inside the root is refused at startup too (case B), which is stricter than the docstring's "leads out of the root".
- **N-5. One of the 17 tests that "fail on 0f0f7e0e, each on its own defect" fails for a different reason.**
  - `15_new_tests_on_main.bash` confirms 17 failed and 73 passed (collected tests go 69 → 90).
  - But `test_a_storage_directory_that_cannot_hold_the_stripes_still_opens` fails on `main` at `iterdir()` of a `locks/` directory that does not exist. On `main` such a store opened fine.
  - Harness arm M63 shows the test can fail for its own defect.
- **N-6. `record_access`'s docstring is stale** (`base.py:343-348`: "multi-process deployments accept best-effort counting"). The file lock has ordered processes since APD-DATA-007. The PR body notices only the same stale sentence in `update_tags`.

## Findings: disposition

Findings in `data438-round1-laneA-reprobe.md`:

| Finding | Disposition |
|---|---|
| F1 MEDIUM: a create lands inside the window | **Fixed** in one process and across two (`xproc_create_race.py`). The cross-process and named halves are unpinned (L-5). |
| F2 LOW: cached-store scope | **Fixed** (docs). |
| F3 LOW: RFC 9110 misquote | **Fixed.** Verbatim at `rfc9110.txt` line 3463, inside §8.8.1 (lines 3393–3479); sha256 `21c1cdce…7232a`; applied correctly. |
| F4 NIT: sweep blind spot | **Fixed.** Structured sweep catches W8 72 times and W11 9 times; 3,495,583 inputs, 0 mismatches. |
| F5 NIT: OWS characters | **Fixed** (docs). h11 0.16.0 passes 0x1C–0x1F; httptools 0.7.1 refuses them; both refuse VT and FF (`parser_bytes_check.py`). |
| F6 NIT: id logged at ERROR on download | **Fixed** on the artifact route, at the cost in N-1. |
| F7 NIT: `.npz` answered 400 | **Fixed** (500). |
| F8 NIT: breaking marker | Not acted on (owner ruling), as the PR says. |

Findings in `data438-round1-laneB-refute.md`:

| Finding | Disposition |
|---|---|
| M1 | Same as F1. |
| M2 | (a) **Fixed.** (b) **Partly fixed** (L-1). |
| L1 | **Fixed** (docs). |
| L2 | **Partly fixed** (L-2). |
| L3 | Same as F6. |
| L4 | **Fixed** for `StorageContainmentError`: 500 on 13 of 19 route cases for a symlinked metadata file. Batch delete reports `not_found`; batch-create gives a per-item error (N-2). Other storage faults are still 400 (L-3). |
| L5 | Disclosed, not fixed, and **widened** to every create (M-1). |
| L6 | **Fixed.** Harness arms M51 and M65–M67 are caught by the lock-order test itself. |
| L7 | Disclosed as a known issue, not fixed. |
| N1–N4 | **Fixed.** The "Moved here" note is gone. |

The earlier "What did not land" items (A1 F2, F3 and F4 in `data428-round3-laneA1-security.md`) are still out of scope, as the PR says.

## What did not land (attacks that failed)

- **Deadlock.** `nesting_probe.py` drove 20 dataset routes over four store setups: LocalFS; cached over LocalFS and LocalFS; cached over two LocalFS stores sharing one directory; cached over LocalFS and in-memory. It recorded zero nested file locks and zero re-entries of `_version_lock`. No path holds two datasets' locks at once.
- **Correctness-changing contention.** None found; only waiting (M-1, L-4).
- **Stripe and directory edge cases:**
  - 12 processes opening a fresh directory at once: no failures, exactly 16 stripes.
  - `locks/` deleted mid-run: recreated on the next lock.
  - A FIFO at a stripe: no hang.
  - A dangling symlink at a stripe: ELOOP, nothing created outside the root.
  - A `locks` symlink present at startup: refused (fail closed).
  - A read-only directory: the store opens; writes fail, as on `main`.
- **Legacy lock files.** They are invisible to the list, `/filter`, `/stats`, `/versions` and the readiness count, and writes still work.
- **The losing create.** It gets a 201 with the stored dataset (the winner's tags, TTL and description). That matches the cache-hit path and is documented (`docs/api/JUNIPER_DATA_API.md:256-258, 394, 401`).
- **No new 400 names an id, and no new client error is a 500.** A bad cursor, a malformed id and rejected params behave the same on `main` and head.
- **CHANGELOG `[0.16.0]`.** It and everything below it are byte-identical to `v0.16.0` (`39d1cab2`): 261 newline-terminated lines by my count, where the PR body says 262.
- **Merge with juniper-data#440** (head `0bee089e`). It merges cleanly in either order in a throwaway `--shared` clone: `git merge-tree` exits 0 and gives the same tree, `dc536271`, both ways. `[Unreleased]` becomes Added, Changed, Fixed, Security.
- **Instruments:**
  - Harness 1.3.0 at head: "PASS: 70 mutations"; baseline 92/92; 110 CAUGHT, 0 VACUOUS, 106 OK, 0 OVERBRD.
  - The harness-coverage counter: OK.
  - The equivalence negative control: PASS.
  - Nine runs of `test_conditional_requests.py` plus `test_meta_cross_process_lock.py`: 94 passed each time, 21–26 s per run, no flakes.

## What this evidence cannot support

- **Stall sizes.** They come from a loaded shared box (load average 10–15), free-threaded CPython 3.14.2, uvicorn 0.40.0, one worker, and an 80 MB dataset I chose. The mechanism does not depend on those; the durations do. I did not run a real probe until it restarted a container.
- **Simulated conditions.** ENOSPC (case H), the `locks/` swap (case M) and the transient EMFILE (N-1) were all patched in. No volume was actually exhausted and no race was won naturally.
- **L-4's second process** is `stripe_holder.py`, not a second uvicorn worker.
- **Other stores.** Redis, Postgres, HF and Kaggle were read, not run.
- **Mutant runs.**
  - Five mutants were run against the full unit, api and integration suites: MX1, MX4, MX9, MX10 and MX23. MX13, MX14 and MX24 were run against the seven files only.
  - `test_real_mnist_generation_satisfies_npz_contract` fails in my mutant runner only, because the runner points HOME at scratch, where there is no dataset cache. It fails the same way on the unmutated baseline and passes with the normal HOME.
- **Not re-run.** The coverage script, pre-commit, the ci-tools screens and the hostile-id traversal probe.

## Scripts

Scripts are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB/scripts/`, outputs in `../out/`.

- **Runners:**
  - `00_extract.bash`;
  - `run_in_tree.bash`, which asserts where `juniper_data` imports from;
  - `run_pytest.bash`, `run_client.bash`, `serve.py`, `common.py`.
- **Stall:** `stall_probe.py`, `stall_probe2.py`, `stall_probe3.py`, `xproc_stall_probe.py`, `stripe_holder.py`.
- **Locks and stripes:**
  - `stripe_probe.py` and `04_stripe_probe.bash`;
  - `nesting_probe.py` and `13_nesting_probe.bash`;
  - `xproc_create_race.py`, `10_xproc_create.bash` and `apply_mx10.py`;
  - `legacy_lockfiles_probe.py`, `locks_file_live_probe.py`.
- **Faults:**
  - `fault_survey.py`, `03_fault_survey.bash`, `fault_survey_compare.py`, `fault_survey_counts.py`;
  - `client_error_probe.py` and `11_client_errors.bash`;
  - `access_suppression_probe.py` and `08_small_probes.bash`.
- **Tests and instruments:**
  - `02_repeat_new_tests.bash`;
  - `my_mutants.py`, `14_mutants_full_suite.bash`, `mutants_full_compare.py`;
  - `15_new_tests_on_main.bash`, `17_collect_counts.bash`;
  - `09_harness_head.bash`, `12_coverage_and_equivalence.bash`, `16_mnist_check.bash`.
- **Docs and git:**
  - `05_git_reads.bash`, `06_merge_predict.bash`, `changelog_check.py`;
  - `07_rfc_check.bash` and `rfc_check.py`;
  - `parser_bytes_check.py`;
  - `99_cleanup.bash`.

## Documents cited

- **juniper-ml:**
  - `reports/2026-09-24_defect-register-round-42/data438-round1-laneA-reprobe.md`;
  - `reports/2026-09-24_defect-register-round-42/data438-round1-laneB-refute.md`;
  - `data428-round3-laneA1-security.md`;
  - the author's PR body `data_fixforward_pr_body.md` and title `data_fixforward_pr_title.txt`, both in the session scratchpad.
- **juniper-data at `d1c66a11`:**
  - `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md`, `Dockerfile`;
  - `juniper_data/api/app.py`, `juniper_data/api/routes/datasets.py`;
  - `juniper_data/storage/base.py`, `juniper_data/storage/local_fs.py`, `juniper_data/storage/constants.py`, `juniper_data/storage/cached.py`;
  - `juniper_data/tests/unit/test_conditional_requests.py`, `juniper_data/tests/unit/test_meta_cross_process_lock.py`;
  - `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py`, `util/ad-hoc/2026-09-24_count_conditional_request_harness_coverage.py`, `util/ad-hoc/2026-09-24_verify_equivalence_sweeps_catch_long_list_mutants.py`.
- **juniper-deploy (`d589dd9`):** `docker-compose.yml`, `k8s/helm/juniper/values.yaml`.
- **juniper-cascor:** `src/api/lifecycle/manager.py`.
- **juniper-canopy:** `src/demo_mode.py`.
- **juniper-recurrence:** `juniper-recurrence/juniper_recurrence/data.py`.
- **RFC 9110:** `rfc9110.txt`, from rfc-editor.org.

## Changed

None. I wrote no repository file.
- Outside scratch, my only actions were:
  - `git fetch` of the branch, `main` and `refs/pull/440/head` into the juniper-data checkout;
  - read-only `gh pr view` and `gh pr list`.
- The merge check ran in a throwaway `--shared` clone under scratch, since deleted.
- Every server I started used a free port between 18700 and 18780, never 8100, and all are stopped.
- The extracted trees are deleted; the scripts and outputs are kept.
