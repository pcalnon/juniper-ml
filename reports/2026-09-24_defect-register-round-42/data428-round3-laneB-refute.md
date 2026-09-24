<!-- Archived verbatim 2026-09-24 from subagent ada46055013dac0d6 of session 8f86dec2 (final message). -->

**Verdict:** REFUTED in part. At `3a76a4c`, 11 of the 13 round-2 findings are closed. Findings #2 and #13 are only partly closed:
- A third reordering of the lock and the precondition passes all 1840 unit tests.
- `PATCH /batch-tags` and `DELETE` break the documented promise that the check "cannot pass and then lose the race", inside a single process. I reproduced this live.

Separately, the CHANGELOG at `3a76a4c` would publish 0.16.0 notes that hold only #428's 8 bullets and say "Breaking changes: NO".

**How hard I tried:**
- 16 of my own mutants: round 2's five re-derived, plus 11 new. I also re-ran the fix agent's 34-mutation harness.
- 3 interleaving probes made repeatable with explicit pauses, 2 live load runs (~99k requests logged), and a two-process lock test on the shipped code and on a mutant.
- 28 hostile ids against all 8 LocalFS entry points, and 8 encoded paths over HTTP.
- 15 hostile regex shapes at 5 lengths, 400 random fields at the cap, and live timing.
- 5 of round 2's probe scripts re-run. A consumer census over 7 sibling repos plus juniper-ml. Three trees compared: `v0.15.0`, `3ecb106` and `3a76a4c`.

**About your correction:** I pulled `3a76a4c` from the old worktree (after `git fetch`) before it was removed. `diff -r` against `git archive 3a76a4c` from `/home/pcalnon/Development/python/Juniper/juniper-data` shows the two are identical, so every result below stands.

## Per-finding table (the findings in `09-data428-round2-validation.md`)

| # | Status | Evidence at `3a76a4c` |
|---|---|---|
| 1 HIGH ReDoS | CLOSED | `http_cache.py:95` pattern replaced. In-process, the worst of 15 shapes at 8192 chars takes 9.4 ms for 4 predicate calls, and time grows about 8x for 8x the length. The worst of 400 random fields at the cap took 0.044 ms. Live uvicorn: a worst-case 8192-char field takes 8–12 ms per request. During 50 of them back to back, `/v1/health` had a median of 4.8 ms (2.1 ms idle); round 2 measured a 1.67 s stall. The equivalence script checked 2,696,745 inputs with 0 mismatches, and its old pattern is exactly `3ecb106`'s. Harness mutant M20 is caught. |
| 2 MED lock untested | PARTIALLY CLOSED | Round 2's N1 is caught by `test_the_store_evaluates_the_precondition_under_its_version_lock`, and N2 by `test_a_write_that_lands_after_the_route_and_before_the_store_is_412`. But **N7** (the precondition checked inside `_version_lock` but outside the cross-process file lock) passes the whole suite (1840 passed) and is a real defect: new finding 3. **N8** (a copy of the metadata read before the lock, checked inside it) passes both new tests too. It is caught only by accident, by `test_storage.py::TestTagUpdateAtomicity::test_update_tags_excludes_record_access_until_the_edit_commits`, which holds the *first* `get_meta` call. |
| 3 MED id in logs | CLOSED | `datasets.py:1079-1083`. An invalid id returns 400 and logs no WARNING; the DEBUG line escapes it with `!r`. The fallback WARNING carries only the exception type, with no `exc_info`. Mutant I1 (re-raise every `ValueError`) is caught. Side effect: new NIT 4. |
| 4 LOW "strong" docstring | CLOSED | The OpenAPI `download_artifact` description now reads "WEAK ``ETag``, ``W/"<checksum>"``". The `TestArtifactValidator` docstring says weak. |
| 5 LOW If-None-Match naming the current tag | CLOSED | N3, adapted to `if_none_match_fails_write`, is caught by 2 tests. |
| 6 LOW orphan If-Match | CLOSED | Live orphan: `If-Match: "nope"` gives 412; `*` gives 200; `If-None-Match: *` gives 304 with Cache-Control and no ETag; a listed tag gives 200. My mutants O1 and O2 and harness M30/M31 are caught. No stream leak or double close on any branch. |
| 7 LOW DELETE / batch-tags ignore If-Match | CLOSED (documented, code unchanged) | Live: DELETE with a stale If-Match gives 204 and the dataset is gone; batch-tags gives 200. Documented in `JUNIPER_DATA_API.md:793-794,1025-1028` and `REFERENCE.md:1321-1324`. See new finding 1: the doc sends conditional edits from batch-tags to the single PATCH without saying batch-tags skips that route's lock. |
| 8 LOW deprecation policy | CLOSED | `JUNIPER_DATA_API.md:73-78` now scopes it to 1.0. |
| 9 NIT mutation count | CLOSED | `REFERENCE.md:1371` and `CHANGELOG.md:107` say thirty-four. The harness prints `PASS: 34 mutations ...`, rc=0. |
| 10 NIT malformed If-None-Match on PATCH | CLOSED | `http_cache.py:179-189`. Live, a malformed or over-cap PATCH If-None-Match gives 412 and writes nothing. The census found no consumer that sends any conditional header. |
| 11 NIT N4 / N6 | CLOSED | N4 is caught by `test_an_artifact_304_carries_its_caching_fields`, N6 by `test_a_412_on_the_artifact_is_not_an_access`. |
| 12 NIT phantom-regression bullet | CLOSED | The bullet is gone. `CHANGELOG.md:61-62` now describes behaviour (see NIT 4). |
| 13 NIT per-host scope | PARTIALLY CLOSED | Redis and Postgres are qualified; `CachedDatasetStore` is named only in `REFERENCE.md`. The claim is still false inside one process on LocalFS: new finding 1. |

## New findings

**1. MEDIUM: `PATCH /batch-tags` and `DELETE` take neither lock, so a conditional PATCH can pass its check and then lose the race.**
- **Code:** `datasets.py:737`/`:746` (batch-tags reads with `get_meta` and writes with `update_meta` in two unlocked hops); `datasets.py:1208` (delete, unlocked); `base.py:385` (`update_meta`'s `False` is ignored).
- **Docs that overclaim:** `JUNIPER_DATA_API.md:1060` ("cannot pass and then lose the race — on one host"), `CHANGELOG.md:76-80` ("a stale copy gets `412` and nothing is written"), `REFERENCE.md:1326-1331`.
- **Evidence, repeatable interleaving** (`scripts/batch_race_probe2.py`; the only instrumentation holds the conditional PATCH's own `update_meta` open):
  - Batch-tags case: `get_meta -> [] (version_lock held: True)` → batch writes `['batch-edit']` → `second request finished inside the window: True` → the conditional PATCH writes `['conditional-edit']`. Final GET: `['conditional-edit']`. The batch request's acknowledged edit is erased, and the conditional PATCH answered 200 although its If-Match was stale when it wrote.
  - Control, a second single-dataset PATCH: `finished inside the window: False`, and the final tags hold both edits.
  - DELETE case: DELETE returns 204 inside the window, then the PATCH answers `200` with an ETag for a dataset whose final GET is `404`.
- **Evidence, live and not instrumented** (`live_race_hammer2.py`, uvicorn with 1 worker on LocalFS; ETags come from `/latest`, which records no access; one batch thread, so batch cannot race itself):
  - Conditional PATCH plus batch-tags: `LOST batch writes: 1 ['b-28']` of 240.
  - Control: 0 lost of 240.
- **Pre-existing part:** the unlocked batch read-modify-write was already there at `v0.15.0`. What #428 added is the guarantee and the ETag on that 200.
- **No current exposure:** no consumer makes conditional PATCHes (census).
- **Fix:**
  - Have batch-tags call `store.update_tags(id, add, remove)` for each id, so it takes both locks.
  - Take both locks in `delete`.
  - `update_tags` should return `None` (so the route answers 404) when `update_meta` returns `False`.
  - Or, at minimum, scope the docs claims to lock-taking writers.

**2. MEDIUM: `CHANGELOG.md:44` and `:126` both read `## [0.16.0]`, so the release ceremony would publish only #428's section.** Details in the next section. The notes would drop 5 real 0.16.0 entries, including a BREAKING removal, and say "Breaking changes: NO".

**3. LOW: nothing tests that the precondition runs under the cross-process file lock** (`base.py:375-380`). `REFERENCE.md:1318` claims `TestConditionalWriteIsAtomic` "pins both halves".
- **Evidence:** mutant N7 passes all 1840 unit tests.
- **Two-process test** (`xproc_precondition.py`):
  - Shipped code: `B finished while A sat between its PASSED check and its write: False`.
  - N7: `True | wrote tags=['from-B']`, then `A: OK`. A's If-Match was stale when it wrote, and it still succeeded.
- **Fix:** add the in-process test in `proposed_flock_test.py`: inside the precondition, `flock(LOCK_EX|LOCK_NB)` on a second open of the lock file must fail. It gives `[True]` on the shipped code and `[False]` on N7. Add N7 as a harness mutant.

**4. NIT: the containment check raises `InvalidDatasetIdError` for a storage fault** (`local_fs.py:111`). The class docstring (`base.py:95-105`) says "never a storage fault".
- **Evidence** (`symlink_meta_probe.py`): a valid dataset whose `.meta.json` is a symlink outside the storage root. `GET .../artifact` returns 200 at `v0.15.0` and at `3ecb106`, but **400** at `3a76a4c`.
- This makes `CHANGELOG.md:61` ("When the metadata cannot be read, the artifact is served without a validator") false for that case.
- Mutant I2 (the traversal site raising a plain `ValueError`) passes the whole suite, so nothing pins this behaviour.
- **Fix:** raise a separate storage error at that check, or document the 400. Correct the docstring either way.

**5. NIT: an empty `If-Match:` returns 412 on GET, the artifact route and PATCH (live), and no test pins it.** Mutants C3 (PATCH decides "conditional" by truthiness) and C4 (`bool(if_match)`) both pass the whole suite. **Fix:** add a test for the empty header.

**6. NIT: `CHANGELOG.md:57` says "A precondition is never answered for a target that would 404" with no qualification.** The in-memory and Redis `exists()` check metadata only (`memory.py:84`, `redis_store.py:175`). **Fix:** add the store qualification.

**7. NIT: `CHANGELOG.md:102` flags the change as "**Breaking**" mid-bullet, and the renderer does not detect that form.**
- `notes_render._is_breaking` returns `False` on #428's section alone. Once folded with #422's `### Removed`, it returns `True`.
- **Fix:** use the uppercase `BREAKING` marker, or list the counter removal under `### Removed`.

**8. NIT: `CHANGELOG.md:97` says "every `GET /{dataset_id}`" records an access.** A 412 on that route does not. **Fix:** qualify it.

## CHANGELOG / release answer (item 7)

**What the 0.16.0 notes would contain today.** `changelog_version_section(CHANGELOG@3a76a4c, "0.16.0")` from `util/release_train/ceremony.py`:
```
-- Added: 4 bullet(s)   ETags...; PATCH .../tags optimistic-concurrency; Content-Location /latest; GET .../access
-- Changed: 4 bullet(s) access counters out; OpenAPI shape; 0.x policy; [0.15.0] duplicate heading
== total bullets: 8
== '## [0.16.0]' heading lines in file: [44, 126]
rendered: "- **Breaking changes:** NO"
```
The function stops at the first `## [0.16.0]` match (`ceremony.py:443-455`). The notes would drop #426, #421, the BREAKING #422 Removed entry, #429/#430 and #420.

**Where the tag goes.** `create_release` (`ceremony.py:847`) passes no `--target`. The gh 2.46.0 help says: "If a matching git tag does not yet exist, one will automatically get created from the latest state of the default branch." None exists yet:
- `ls-remote` shows only `v0.15.0`, `v0.15.0-alpha` and `v0.15.1-alpha`.
- `gh release list` shows `v0.15.0` as latest.
- PyPI's latest is `0.15.0`.

`publish.yml` runs on `release: published` and checks out the tag.

**So #428 ships in 0.16.0.** So do #434's code (`cached.py`, the arc_agi generator) and #431's workflow, whose entries sit in `[Unreleased]`.

**Which repair makes the published notes true: FOLD.**
- **Fold** (delete lines 126–127): 13 bullets (Added 6, Changed 4, Removed 1, Fixed 2), "Breaking changes: YES".
- **Move #428 to `[Unreleased]`** (delete lines 44–45): this is the fix agent's proposal in `10-data428-round2-fix-report.md`. It gives 5 bullets, and #428's shipped breaking change goes unlisted.
- The fix report's premise, "0.16.0 was cut by #433 before #428 merged", is false: #433 only bumped the version and moved the heading.
- Folding #428 alone is not enough. `[Unreleased]` (#431, #434) must fold too, or those two ship unlisted. #434's wording ("0.16.0 turned…", "#430's entry is under `[0.16.0]`") would then need rewording.
- **Ceremony hardening for juniper-ml:** refuse a CHANGELOG with duplicate version headings, and either pass `--target` set to the commit whose CHANGELOG was rendered or refuse while `[Unreleased]` is non-empty.

## Attacks that did not land
- **Traversal:** all 28 hostile ids (`..`, `%2e%2e`, NUL, `\n`, `/etc/passwd`, fullwidth dot and solidus, U+2215, U+2044, Cyrillic а, 129 characters, empty, and others) are refused by all 8 LocalFS entry points with `InvalidDatasetIdError`. Nothing was created outside the root. Over HTTP, encoded paths give 404 or 400, with or without preconditions.
- **`ValueError` callers:** `batch_delete` (`base.py:604`) still returns not_found, and the `pytest.raises(ValueError, match=...)` tests still pass. Only LocalFS raises the new error.
- **Orphan path:** no leak, no double close, no access recorded wrongly, and no 404↔200 flip.
- **Length cap:** it applies identically to both headers on reads and writes. Over the cap: GET If-None-Match gives 200; GET If-Match gives 412; PATCH If-None-Match gives 412. A 66-character tag means about 120 tags fit in a field. The server accepted a 20 KB field, so the cap is the limit that binds.
- **Consumer census:** in data-client, canopy, cascor, cascor-client, cascor-worker, recurrence (all three packages plus `bench/`) and deploy, all at an `origin/main` equal to the remote's main, nothing sends If-Match or If-None-Match, PATCHes a single dataset's tags, or reads the access counters. `cachecontrol` appears only in conda manifests, never in code.
- **Mutants caught:** N1, N2, N3, N4, N6, O1, O2, C1, C2 and I1. Harness: PASS 34.
- **Round-2 probes re-run:**
  - The PATCH matrix is 16/16 on both stores. The only change is If-None-Match malformed going 200 → 412, which is the intended fix for finding 10.
  - The 18 grammar inputs are unchanged.
  - The metadata ETag equals the SHA-256 of the body and matches FastAPI's `response_model` rendering, and the PATCH ETag equals the next GET's.
  - Missing datasets return 404 under every precondition.
  - Each 304 carries ETag and Cache-Control and no body.
  - The OpenAPI `PublicDatasetMeta` has no counter properties; it only mentions them in its description.
  - HEAD still returns 405.

## What this evidence cannot support
- Every live run used one uvicorn worker, and the server re-enabled the GIL for httptools. The cross-process claims rest on the two-process store-level test, not on a multi-worker server.
- The live loss rate of 1 in 240 depends on contention and says nothing about production rates.
- Past the cap, the regex alone grows faster than linear on comma-heavy shapes: 16x the length (8k → 128k) cost 25–45x the time, measured on a loaded box. The cap makes those lengths unreachable.
- Redis, Postgres, Cached, HF and Kaggle were assessed from the code only.
- Out of scope: #435 (per your note), security (Lane A) and CodeQL.
- `record_access` and `update_tags` create a `.meta.json.lock` file for any valid id, including a PATCH that returns 404. That behaviour dates from before #428 and I did not assess it.
- **Hygiene:** no repository was written. I used only a scratch API key and made read-only queries to PyPI and GitHub. I stopped only my own server, pid 3902276.

**Documents changed:** none in any repository. Everything is in the scratch dir `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneB/`:
- `scripts/`: `mutants.py`, `batch_race_probe2.py`, `live_race_hammer2.py`, `xproc_precondition.py`, `proposed_flock_test.py`, `run_changelog_section.py`, `symlink_meta_probe.py`, `traversal_probe.py`, `redos_probe.py`
- logs: `mutants_run1.log`, `harness.log`, `equivalence.log`, `live_probe.log`, `live_race.log`, `live_race2.log`
