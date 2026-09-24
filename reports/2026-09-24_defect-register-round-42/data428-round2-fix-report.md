<!-- Archived verbatim 2026-09-24 from subagent a0cf8c571a773ebe1 of session bc31e993 (final message). -->

All 13 findings are fixed and pushed as four signed commits, but main now files #428's CHANGELOG entries under the already-released 0.16.0 heading and needs a one-hunk fix. An outside actor (`pcalnon`) ran update-branch (`583c807`) and squash-merged #428 as `af7831b` at 2026-09-23T22:38:40Z. I pushed nothing after that, opened no PR, and never used `git push`, local signing, `git stash` or a CI-skip marker.

## Your three questions

1. **Harness run 3 finished.** It ran on the tree that became `bd29376`. `af7831b` differs from `bd29376` only in #433's four release files (`AGENTS.md`, `CHANGELOG.md`, `juniper_data/__init__.py`, `pyproject.toml`), so it covers main's code. Final line, verbatim:
   `PASS: 34 mutations, each caught by the tests that describe it, with every control green.`
   Exit 0, 51 CAUGHT, 45 controls green, 0 VACUOUS or OVERBRD, baseline of 49 named tests green. Runs 1 and 2 gave the same line.
2. **Commit (d) is `bd29376`, pushed.** It is signed (`verified=true`, reason `valid`), touches only the test file, and is byte-identical to my local copy. CodeQL on `95ebb40` had flagged `py/uninitialized-local-variable` at `test_conditional_requests.py:254`; (d) restructured it without suppressing anything. CodeQL on `bd29376` and on `583c807` both say "No new alerts in code changed by this pull request". Main has 36 open alerts, **none in any file I touched**; all were created between 2026-02-21 and 2026-07-21.
3. The full report follows.

## Defect now on main: the CHANGELOG

- **What is wrong.** Main's `CHANGELOG.md` at `3a76a4c` has `## [0.16.0] - 2026-09-23` twice, at lines 44 and 126. #428's `### Added` (line 46) and `### Changed` (line 92) sit under the first one, so they read as shipped in 0.16.0. They were not: 0.16.0 was cut by #433 before #428 merged.
- **How it happened.** I predicted it before pushing (c). A `git merge-file` simulation merged cleanly with 0 conflicts in both directions, yet duplicated the heading, and GitHub's own test-merge ref `1b0bab1` showed the same.
  - No push alone could avoid it. The PR's old CHANGELOG would also have merged cleanly, with #428's entries silently under 0.16.0.
  - Only one order is safe: update-branch first, then push the corrected file. Update-branch was off-limits to me.
  - I meant to report this before anyone ran update-branch, but it ran first.
  - `583c807`'s CHANGELOG is byte-identical to my simulation, and `af7831b`'s is identical to `583c807`'s.
- **Fix (needs a PR; I did not open one).** Delete lines 44–45 of main's `CHANGELOG.md` (the first `## [0.16.0] - 2026-09-23` and the blank line after it). `[Unreleased]` then holds `### Fixed` (#434), then #428's `### Added` and `### Changed`, with no duplicate category. Reordering to Added/Changed/Fixed is optional. This should land before the next release cut.

## The 13 findings

1. **ReDoS (HIGH).** In `juniper_data/api/http_cache.py`:
   - `_ENTITY_TAG_LIST` is replaced with the exact pattern you gave.
   - **Equivalence re-verified:** 2,696,745 inputs, 0 mismatches. That is every string over 8 symbols up to length 7 (2,396,745), plus 300,000 inputs built from grammar tokens.
   - The check is a new script, `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py`, placed per the script-placement rule. It imports the shipped pattern, not a copy.
   - **Timings on this box, old pattern:** `", " * 20 + "x"` took 414 ms, doubling per element. **New pattern:** `", " * 4000 + "x"` took 2.8 ms.
   - **Cap:** `MAX_PRECONDITION_FIELD_LENGTH = 8192`, counted over the joined lines. Over the cap is malformed, `*` included.
   - **Regression test:** `TestEntityTagListRunsInLinearTime` loads the imported `http_cache.py` by file path in a child interpreter, so in the harness it exercises the mutated copy.
     - It uses three hostile fields, all under the cap: `", " * 30 + "x"` (about 7 minutes under the old pattern, extrapolated, not measured), plus `",\t\t" * 22 + "x"` and `" , " * 26 + "x"`.
     - The bound is 30 s, under the suite's 60 s pytest-timeout. It asserts only that the parse finishes and what it returns; there is no wall-clock threshold.
2. **Lock atomicity (MEDIUM).** New class `TestConditionalWriteIsAtomic`:
   - One test asserts `_version_lock.locked()` inside the precondition, with a guard that the lock starts unheld. It catches N1 (harness M22).
   - The other lets a writer land between the route and the store, and asserts that edit really landed before expecting 412. It catches N2 (M23).
3. **Fallback leaked the caller's id (MEDIUM).**
   - **How an invalid id surfaces:** `local_fs._validate_dataset_id` (called via `_build_path`) raises a `ValueError`; `app.value_error_handler` returns 400 "Invalid request parameters" and logs it at DEBUG. The artifact route already returned 400, because `open_artifact_stream` raised the same error; the defect was the WARNING with its traceback.
   - **Why not `except ValueError: raise`:** `JSONDecodeError`, `UnicodeDecodeError` and pydantic's `ValidationError` are all `ValueError` subclasses, and they are exactly the corrupt-metadata cases the fallback exists for.
   - **What I did:** added `InvalidDatasetIdError(ValueError)` in `juniper_data/storage/base.py`, raised at LocalFS's three validation sites and its traversal check. The route re-raises it. The WARNING now logs `type(exc).__name__` only, with no `exc_info`.
   - Existing `pytest.raises(ValueError, …)` tests still pass. Only LocalFS validates ids; on other stores an odd id is simply unknown and 404s.
   - **Tests:** a failure whose message carries the id leaves the id out of the WARNING and gives it no `exc_info`; an invalid id returns the normal 400 body and logs no WARNING.
4. **Stale "strong".** Fixed in the `download_artifact` docstring (the OpenAPI description), the test class docstring, the test module docstring, and the intro of `docs/REFERENCE.md` § Conditional Requests and Validators. A repo-wide grep finds no other strong claim about the artifact tag.
5. **Untested case.** Added a test: a PATCH whose `If-None-Match` names the current tag (bare, in a list, or with `W/`) returns 412 and writes nothing.
6. **Orphaned artifact.** When `exists()` is false but the stream opens, the preconditions are now evaluated against a literal `None`.
   - I checked `read_precondition_status`: `If-Match: *` holds, a listed tag gives 412, and `If-None-Match: *` gives 304, the same as for any present representation.
   - The stream is closed on a 412 or 304 (new `_close_artifact_stream`). A 304 records an access, which is a no-op for a real orphan. A truly absent dataset still 404s.
   - Four tests cover this, two of them with a probe that asserts `close()` was called.
7. **DELETE and `/batch-tags` ignore If-Match: documented, no code.** Documented in `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md` (the DELETE, PATCH and batch-tags sections), the PATCH route docstring, and `CHANGELOG.md`. The register row is still yours to file.
8. **Deprecation policy.** Item 4 of `docs/api/JUNIPER_DATA_API.md` is now scoped to 1.0, the same way items 3 and 5 are. There is no `Deprecation` header anywhere in the code, so scoping the whole item promises nothing it did not.
9. **Mutation count.** `docs/REFERENCE.md` said "twenty" while the harness had 22. `docs/REFERENCE.md` and `CHANGELOG.md` now both say thirty-four.
10. **Fail closed.** New `if_none_match_fails_write`: a malformed or over-cap `If-None-Match` on a write returns 412. An empty field is a valid empty list, so the write proceeds (tested as a control). Reads are unchanged. The module docstring and the OpenAPI `_R_412_WRITE` description are updated.
11. **Unasserted behaviours and harness arms.**
    - New tests for `Cache-Control` on the artifact 304, and for an artifact 412 not being recorded as an access.
    - Requested arms: old regex restored (M20), N1 (M22), N2 (M23), If-None-Match honouring only `*` (M24), malformed If-None-Match on PATCH proceeding (M25), 304 Cache-Control (M26), 412 recorded as an access (M27), fallback logging `exc_info` (M28), orphan If-Match ignored (M30).
    - Extra arms I added: cap removed (M21), malformed id taking the fallback (M29), orphan stream left open (M31).
    - M3 now covers reads only, because writes have their own helper. M8a and M15 were updated to follow the changed code.
12. **CHANGELOG entry for an unshipped regression.** The bullet was actually under `### Added`, phrased as a fix, not under Fixed. I removed it and folded the fact into the ETag entry as behaviour.
    - Diffing against `origin/main`: the only lines of main's missing from mine are the duplicate `### Changed` heading and two blank lines. Those come from the `[0.15.0]` heading merge this PR already made, which I re-applied; nothing else of main's was lost.
13. **Per-host guarantee.** Qualified in `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md` and `CHANGELOG.md`. Beyond the brief, `docs/REFERENCE.md` also names `CachedDatasetStore`: it inherits the no-op lock whatever its primary store, so a cached store over LocalFS loses the file lock too.

## Commits (all signed, no HTTP 499s)

| Commit | Contents |
|---|---|
| `d1e85f7` (a) | code, tests, harness, equivalence script |
| `98ca39f` (b) | docs |
| `95ebb40` (c) | CHANGELOG, rebuilt on main's 0.16.0 cut |
| `bd29376` (d) | the CodeQL restructure |

**PR state when I stopped:** BEHIND by 1 (#433): `mergeable_state: behind`, 11 ahead, 1 behind. I did not run update-branch. `util/wait_for_checks.py` reported: "GREEN — 22/22 required contexts finished (21 success), mergeState=BEHIND".

## Verification

- **Unit suite:** 1821 passed at `3ecb106`; **1837 passed** (7 subtests) on the final tree, and again on a `git archive` copy of `af7831b`.
- **`test_conditional_requests.py`:** 40 before, **56** after (16 new tests).
- **pre-commit** over all 10 changed files: exit 0, 16 Passed, 7 Skipped (no in-scope files), 0 Failed.
  - One interim failure was fixed before any push: MyPy on the tests wanted an annotation on `failed`.
  - markdownlint excludes `CHANGELOG.md` and `docs/` by config; the documentation-link check passed.
- **Symbol-loss screen** (`7125e16` to `bd29376`): `files_screened=8 findings=1 fail=0 by_verdict={'WAIVED': 1}`, the waived `class:DatasetMeta` only.
- **Docs-additions screen** (same range): `files_screened=4 findings=13 fail=0 by_reason={'small-deletion': 13}`, all WARN.

## Every numeric or behavioural claim changed

Line numbers are at `bd29376`. The docs lines are identical on main; main's `CHANGELOG.md` is offset by the duplicated heading.

**`docs/REFERENCE.md`**
- 1253–1259: "owner-ruled 2026-09-11: a strong `ETag`" becomes "an `ETag`…a strong one" for metadata, plus the 2026-09-23 re-ruling: the artifact tag is weak.
- 1265: artifact row. The gate is now "for a target `store.exists()` confirms; an orphaned artifact is judged against no validator". Added: "a confirmed target's 304 is decided before the artifact is opened; a 412 is not an access".
- 1266: PATCH row adds "or either malformed → 412".
- 1288–1296: new paragraph on malformed fields:
  - the 8192-character cap (`MAX_PRECONDITION_FIELD_LENGTH`, over joined lines);
  - on a read, If-None-Match names nothing;
  - If-Match fails, read or write;
  - on a write, If-None-Match fails closed;
  - the grammar is linear-time, and the cap is defence in depth.
- 1298–1311: orphan behaviour:
  - `If-Match: *` holds, `If-None-Match: *` gives 304, any other If-Match gives 412;
  - an unsent stream is closed;
  - a dataset with neither metadata nor artifact is a 404 under every precondition;
  - the warning names the exception type only;
  - `InvalidDatasetIdError` takes the normal 400.
  - Removed: "an orphaned artifact with no metadata is served unconditionally".
- 1318–1331: `TestConditionalWriteIsAtomic` pins both halves; PATCH is the only write honouring preconditions (DELETE's If-Match is not evaluated; batch-tags and all other writes ignore both headers). The atomicity is per host: file lock on LocalFS; Redis, Postgres and `CachedDatasetStore` hold it within one process only; the service wires LocalFS only.
- 1360–1365: new What-not-to-do bullet on the backtracking grammar ("`", " * 22 + "x"` took about 1.8 s, doubling per element").
- 1371–1373: "twenty" becomes "thirty-four" mutations, plus a pointer to the equivalence script.
- 1547: the streaming bullet adds the orphan evaluation after the open, with the stream closed on 412 or 304.

**`docs/api/JUNIPER_DATA_API.md`**
- 73–75: Deprecation Policy scoped to 1.0; before 1.0 a breaking change needs only a CHANGELOG **Breaking** entry.
- 793–794: batch-tags does not evaluate If-Match or If-None-Match.
- 909–910: on `GET /{id}`, a malformed or longer-than-8192 If-None-Match names nothing, and the full body is served.
- 912–913: a malformed or over-long If-Match fails with 412.
- 973–981: artifact route: evaluated before the open when `exists()` confirms the target; the orphan rules as above; absent gives 404 whatever the headers say; a malformed id gives 400.
- 1025–1028: DELETE's If-Match is not evaluated; only PATCH honours preconditions.
- 1060–1070: PATCH atomicity is per host (LocalFS lock per host; Redis and Postgres have no cross-process lock; LocalFS is what runs today). An unreadable header, or one over 8192 characters, gives 412 for either header. PATCH is the only write that honours preconditions.

**`CHANGELOG.md`**
- 19–26 (ETag entry):
  - "matches nothing" becomes the malformed-field rule (not well-formed, or over 8192 characters): on a read, If-None-Match names nothing; If-Match fails.
  - Added: an orphaned artifact's preconditions are judged against no validator, and only `*` matches it.
  - Added: when metadata cannot be read, the artifact is served without a validator; a malformed id is still 400.
- Removed the bullet "An unreadable metadata document no longer fails an artifact download…".
- 45–49 (PATCH entry): an unreadable header fails closed with 412; the atomicity is per host (file lock on LocalFS; Redis and Postgres within one process); it is the only write that evaluates preconditions, and DELETE's If-Match is not evaluated.
- 71: "twenty-two" becomes "thirty-four".
- 83–84: "…take effect at 1.0" now includes "the deprecation policy's advance notice".
- Structure: #428's entries sit in a fresh `[Unreleased]` above `[0.16.0]`. The #426 and #421 entries are verbatim under `[0.16.0]`.

**OpenAPI text** (published from code):
- The `download_artifact` description now says the tag is weak and that only `*` satisfies If-Match, and its Raises line adds 412.
- The PATCH description adds fail-closed and "no other write route evaluates preconditions".
- `_R_412_WRITE` adds "or either field is malformed".

## Files changed (all on main via `af7831b`)

- `juniper_data/api/http_cache.py`
- `juniper_data/api/routes/datasets.py`
- `juniper_data/storage/base.py`
- `juniper_data/storage/local_fs.py` (not previously in the PR)
- `juniper_data/tests/unit/test_conditional_requests.py`
- `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py`
- `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py` (new)
- `docs/REFERENCE.md`
- `docs/api/JUNIPER_DATA_API.md`
- `CHANGELOG.md`

## Not done

- The CHANGELOG fix on main (above).
- The register row for DELETE and batch-tags ignoring If-Match (yours to file, per the brief).
- #428's description is not updated; the claims list above is ready for it.
- **Worth recording in memory:** building a PR's CHANGELOG on a release cut before update-branch still mis-files silently once update-branch runs. The safe order is update-branch first, then push the corrected file.
- The local juniper-data worktree is clean at `bd29376` and the remote branch was deleted on merge, so it is ready for cleanup. I did not remove it.
