<!-- Archived verbatim 2026-09-24 from subagent a40325befd1022f04 of session 8f86dec2 (final message). -->

None of it is mine. My first possible import of `ceremony.py` was after 03:05:54, 26 minutes after those `.pyc` writes, so I wrote nothing into the juniper-ml worktree. The work is complete. Final report follows.

# Lane A2 (claims re-derivation): juniper-data#428, round 3, validated at `3a76a4c`

**Verdict:** The code, tests and scripts on `3a76a4c` do what the fix report says: every count reproduced exactly, and 79 of 79 behavioural doc checks pass. But the report's CHANGELOG diagnosis and its proposed fix are both refuted by how releases are actually cut (**HIGH**). The published "cannot lose the race" guarantee is refuted against two routes that write without the lock (**MEDIUM**). And a `*` wrapped in NBSP or NEL gets past the documented fail-closed rule (**LOW**).

**How I ran it.** I extracted `3a76a4c`, `af7831b`, `bd29376`, `3ecb106`, `583c807` and `7125e16` with `git archive` into my scratch dir and ran everything in the `JuniperData` env (Python 3.14.2 free-threaded). The brief's juniper-data worktree was **removed by another actor during this round**. Per the coordinator's correction, I switched to the main checkout for read-only git only.

## CHANGELOG at `3a76a4c` (your direct question)

```
  8  ## [Unreleased]
 10  ### Fixed        #434 (line 12), #431 (line 31)
 44  ## [0.16.0] - 2026-09-23     <- duplicate, created by the update-branch merge 583c807
 46  ### Added        #428, 4 bullets
 92  ### Changed      #428, 4 bullets
126  ## [0.16.0] - 2026-09-23     <- the section #433 cut, verbatim (all 152 lines match 7125e16)
128  ### Added / 170 ### Removed / 224 ### Fixed
278  ## [0.15.0] - 2026-09-22     (one ### Changed at 280, after #428 merged its two; ### Fixed at 346)
```

`## [0.16.0] - 2026-09-23` appears **twice** (a count of 2). The fix report's statement is **confirmed**.

## Claims table

The "Where" column refers to `reports/2026-09-24_round-42-post-merge/10-data428-round2-fix-report.md` unless another file is named.

| # | Claim | Where | Measured | Verdict |
|---|---|---|---|---|
| 1 | Unit suite: 1821 passed at `3ecb106` | §Verification | 1821 passed, 7 subtests, 0 failed. The suite imported the tree's own `juniper_data` | REPRODUCED |
| 2 | 1837 passed (7 subtests) on a `git archive` copy of `af7831b` | §Verification | 1837 passed, 7 subtests. `3a76a4c` gives 1840 (#434 adds 3) | REPRODUCED |
| 3 | `test_conditional_requests.py`: 40 tests before, 56 after, 16 new | §Verification | Collected 40 at `3ecb106` and 56 at `bd29376`, `af7831b` and `3a76a4c`. 16 added, 0 removed | REPRODUCED |
| 4 | Harness: "PASS: 34 mutations…"; 51 CAUGHT, 45 controls, 0 VACUOUS/OVERBRD, baseline of 49, exit 0 | §Q1 | Re-run on `3a76a4c` (930 s): same final line verbatim, 51/45/0/0/49, exit 0 | REPRODUCED |
| 5 | "Runs 1 and 2 gave the same line" | §Q1 | — | NO ARTIFACT |
| 6 | `af7831b` differs from `bd29376` only in #433's four release files | §Q1 | Exactly `AGENTS.md`, `CHANGELOG.md`, `juniper_data/__init__.py`, `pyproject.toml`. The changed lines equal #433's own diff | REPRODUCED |
| 7 | So the harness run on `bd29376` covers main's code | §Q1 | No file the harness mutates or runs differs between `bd29376` and `3a76a4c` | REPRODUCED |
| 8 | Update-branch `583c807` lost nothing of main's (your ask) | brief | Main's changed lines (`90ad035..7125e16`) equal `bd29376..583c807`; the feature side's equal `7125e16..583c807`. `583c807` and `af7831b` share tree `e8a3407` | REPRODUCED |
| 9 | All 4 commits signed; `bd29376` touches only the test file | §Q2, §Commits | GitHub API: all four `verified=true`, `reason=valid`; file lists as stated | REPRODUCED |
| 10 | `bd29376` is "byte-identical to my local copy" | §Q2 | That worktree has been removed | NO ARTIFACT |
| 11 | CodeQL flagged `py/uninitialized-local-variable` at `test_conditional_requests.py:254` on `95ebb40`; fixed without suppression | §Q2 | Check-run annotation at line 254, verbatim. `bd29376` adds no noqa, lgtm or pragma | REPRODUCED |
| 12 | CodeQL on `bd29376` and `583c807`: "No new alerts…" | §Q2 | Both check-run titles verbatim | REPRODUCED |
| 13 | 36 open alerts, none in touched files, created 2026-02-21 to 2026-07-21 | §Q2 | 36 alerts, created 2026-02-21T20:14:15Z to 2026-07-21T18:50:19Z, none in any #428 file | REPRODUCED |
| 14 | Merged by `pcalnon` as `af7831b` at 2026-09-23T22:38:40Z | intro | PR record matches; head was `583c807` | REPRODUCED |
| 15 | `[0.16.0]` at lines 44 and 126; #428's Added at 46 and Changed at 92 | §Defect | Exactly as stated | REPRODUCED |
| 16 | #428 "was not" shipped in 0.16.0: "0.16.0 was cut by #433 before #428 merged" | §Defect | There is no v0.16.0 tag or Release, and PyPI's latest is 0.15.0. The ceremony creates the tag at main HEAD (F1) | **REFUTED** |
| 17 | Fix: delete lines 44–45 | §Defect | Leaves one heading, but the resulting v0.16.0 notes omit all 8 of #428's bullets (F1) | **REFUTED** |
| 18 | `merge-file`: 0 conflicts in both directions, duplicated heading; `583c807` byte-identical to that result | §Defect | Re-simulated: 0/0 conflicts, 2 headings, byte-identical to `583c807` | REPRODUCED |
| 19 | Test-merge ref `1b0bab1` showed the same | §Defect | 2 headings; byte-identical to `583c807` | REPRODUCED |
| 20 | The PR's old CHANGELOG would also have merged cleanly with #428 under 0.16.0 | §Defect | `3ecb106`'s file: 0 conflicts; the ETag entry lands under `[0.16.0]` | REPRODUCED |
| 21 | Equivalence: 2,696,745 inputs (2,396,745 + 300,000), 0 mismatches; imports the shipped pattern | §F1 | Same counts, exit 0 (128,955 accepted by both). NEW comes from the tree; OLD equals `3ecb106`'s literal | REPRODUCED |
| 22 | Old `", "*20+"x"` took 414 ms, doubling per element; new `", "*4000+"x"` took 2.8 ms | §F1 | Old: 434–557 ms (load 7–14), about 2x per element. New: 4.0–4.5 ms in the script; 1.3 ms at 8192 chars (best of 5) | REPRODUCED (same scaling; absolute times depend on the machine) |
| 23 | `", "*22+"x"` took about 1.8 s | `http_cache.py:89`, `REFERENCE.md:1363` | 1.94 s | REPRODUCED |
| 24 | Cap of 8192, counted over the joined lines; over the cap is malformed, `*` included | §F1 | An over-cap list naming the current tag gives 200 on a read, 412 for If-Match and 412 on a PATCH. `*` plus 8192 spaces behaves the same. Two lines that join to over the cap give 200 | REPRODUCED |
| 25 | The grammar is linear-time | `REFERENCE.md:1295` | 12 adversarial input families all scale linearly, 1.4 ms or less at 8192 chars | REPRODUCED |
| 26 | The child interpreter exercises the mutated copy | §F1 | Proven (see instrument adequacy) | REPRODUCED |
| 27 | 3 hostile fields, all under the cap; `", "*30` would take about 7 min under the old grammar (extrapolated) | §F1 | Lengths 61, 67 and 79; 434 ms × 2^10 ≈ 7.4 min. The other two families grow about 3x per element | REPRODUCED |
| 28 | Bound of 30 s under the 60 s pytest-timeout; "no wall-clock threshold" | §F1 | Both values confirmed, but the 30 s bound is itself a generous wall-clock limit | REPRODUCED (wording) |
| 29 | `TestConditionalWriteIsAtomic` catches M22 and M23 | §F2 | Both CAUGHT, controls green | REPRODUCED |
| 30 | `InvalidDatasetIdError` raised at 3 validation sites and the traversal check; the WARNING names the type only, with no `exc_info` | §F3 | `local_fs.py:53,55,57,111`. Corrupt metadata produces one WARNING "(JSONDecodeError)" with `exc_info=None` | REPRODUCED |
| 31 | Before the fix, the malformed id already got 400; the defect was the WARNING with its traceback | §F3 | `3ecb106`: 400, plus a WARNING whose traceback carries the caller's id. `3a76a4c`: 400, no WARNING | REPRODUCED |
| 32 | Only LocalFS validates ids; other stores 404 | §F3 | InMemory returns 404 on both routes. Redis and Postgres checked by code reading only | REPRODUCED |
| 33 | No other claim that the artifact tag is strong | §F4 | Paragraph-level scan of docs, README, `AGENTS.md` and code: none | REPRODUCED |
| 34 | Orphan rules; stream closed on 412/304; absent dataset is 404; 4 tests, 2 with close() probes | §F6 | All as stated on LocalFS; tests present | REPRODUCED |
| 35 | DELETE and batch-tags ignore If-Match | §F7 | DELETE with a stale tag: 204, dataset gone. batch-tags with a stale If-Match plus `If-None-Match: *`: 200, applied | REPRODUCED |
| 36 | No `Deprecation` header anywhere in the code | §F8 | None found | REPRODUCED |
| 37 | "thirty-four" in both docs | §F9 | `REFERENCE.md:1371`, `CHANGELOG.md:107` | REPRODUCED |
| 38 | Writes fail closed on a malformed field; an empty field proceeds | §F10 | garbage, a tag inside garbage, an unterminated tag and over-cap all give 412 with nothing written; empty gives 200 | REPRODUCED, except F3 |
| 39 | Bullet removed; the only lines of main's lost are the duplicate `### Changed` and 2 blanks | §F12 | Exactly `''`, `''`, `### Changed` removed; no non-blank line lost | REPRODUCED |
| 40 | Atomicity is per host; `CachedDatasetStore` inherits the no-op lock | §F13 | Only `local_fs.py` overrides `_meta_write_lock`; `cached.py` overrides neither it nor `update_tags` | REPRODUCED |
| 41 | pre-commit: exit 0, 16 Passed, 7 Skipped | §Verification | CI Pre-commit (3.12, 3.13, 3.14) green on `bd29376` and `583c807` | NO ARTIFACT for the tally; exit 0 corroborated by CI |
| 42 | markdownlint excludes `CHANGELOG.md` and `docs/` | §Verification | `.pre-commit-config.yaml:196` | REPRODUCED |
| 43 | Symbol-loss screen: 8/1/0, `{'WAIVED': 1}`, `class:DatasetMeta` | §Verification | Re-run (ci-tools 0.8.0, scope `juniper_data/**`): verbatim | REPRODUCED |
| 44 | Docs-additions screen: 4/13/0, `{'small-deletion': 13}` | §Verification | Re-run: verbatim | REPRODUCED |
| 45 | Every cited `REFERENCE.md` / `JUNIPER_DATA_API.md` line exists, identical on main | §Every claim | Docs byte-identical between `bd29376` and `3a76a4c`; every sentence at its cited line | REPRODUCED |
| 46 | And the code behaves as each says | §Every claim | 79/79 checks OK on LocalFS | REPRODUCED, except F2 and F3 |
| 47 | CHANGELOG lines 19–26, 45–49, 71, 83–84 (cited at `bd29376`) | §Every claim | At `3a76a4c` lines 55–62, 81–85, 107, 119–120 | REPRODUCED |
| 48 | Main's CHANGELOG "is offset by the duplicated heading" | §Every claim | The offset is 36 lines: 34 from `[Unreleased]`'s `### Fixed` block (#434/#431) plus 2 | REFUTED (NIT) |
| 49 | #428's entries sit in a fresh `[Unreleased]`; #426/#421 are verbatim under `[0.16.0]` | §Every claim | The first half is true only at `bd29376`. The second half holds at main | REFUTED at main / REPRODUCED |
| 50 | OpenAPI: artifact tag weak, only `*` satisfies If-Match, Raises adds 412; PATCH text; `_R_412_WRITE` | §Every claim | `app.openapi()` text verbatim | REPRODUCED |
| 51 | The 10 files changed; `local_fs.py` not previously in the PR | §Files | `3ecb106..bd29376` is exactly those 10; `3ecb106..af7831b` adds #433's 3; `local_fs.py` absent from `90ad035..3ecb106` | REPRODUCED |
| 52 | Remote branch deleted on merge | §Not done | Branch lookup returns 404 | REPRODUCED |
| 53 | PR was BEHIND by 1; `wait_for_checks` GREEN 22/22 | §Commits | Historical state | NO ARTIFACT |
| 54 | Lesson: "update-branch first, then push the corrected file" | §Not done | The file it calls "corrected" (#428 under `[Unreleased]`) is itself wrong (F1) | REFUTED (premise) |
| 55 | InMemory sorts keys, so bytes differ under one checksum; `sha256(served) != checksum` | `REFERENCE.md:1336-1340` | Confirmed on both InMemory and LocalFS | REPRODUCED |
| 56 | HEAD returns 405 on all three reads | `REFERENCE.md:1367` | 405, 405, 405 | REPRODUCED |

## Findings

**F1 — HIGH — `CHANGELOG.md:44` (juniper-data).** The duplicate heading is real. The fix report's diagnosis ("not shipped in 0.16.0") and its fix (delete lines 44–45) both misread how 0.16.0 will ship.
- **Evidence.**
  - `gh release view v0.16.0` returns "not found", the tag ref returns 404, and PyPI's latest juniper-data is 0.15.0. #433 only bumped the version; no release has been cut.
  - juniper-ml `util/release_train/ceremony.py:847` cuts the Release with `gh release create <tag>` and no `--target`. The tag therefore lands on main HEAD, which contains #428, #431 and #434.
  - `ceremony.py:443-448` reads only the **first** `## [0.16.0]` heading.
  - I ran that parser on both versions of the file (`ev-ceremony_notes.out`):
    - **Main as it stands:** the v0.16.0 notes are #428's 8 bullets alone. All 5 bullets #433 cut are dropped, including the **BREAKING** HF/Kaggle `X_full` removal.
    - **The report's fix:** the notes are #433's 5 bullets and none of #428's. The ETag feature and the **Breaking** access-counter removal would ship in v0.16.0 with no release note.
  - `ceremony.py:431` records that a Release body cannot be re-cut.
- **Fix.**
  - Fold #428, #431 and #434 into the single `[0.16.0]` section before the release is cut, and check the result with `changelog_version_section(text, "0.16.0")`.
  - Open PR #435 (head `014a5c3`) says it does exactly this, per an owner ruling of 2026-09-24. **This lane has not validated #435.**
  - Add a CI guard that fails on a repeated `## [x.y.z]` heading.

**F2 — MEDIUM — the "cannot lose the race" guarantee is false for two routes.**
- **Where it is claimed.** `routes/datasets.py:1225-1227` (published in OpenAPI), `docs/api/JUNIPER_DATA_API.md:1059-1062`, `docs/REFERENCE.md:1313-1317` and `CHANGELOG.md:78-80` all say the PATCH precondition "cannot pass and then lose a race to another writer" (the API doc adds "on one host").
- **Why it fails.**
  - `PATCH /batch-tags` (`datasets.py:736-747`) and `DELETE` (`datasets.py:1208`) take neither `_version_lock` nor the file lock.
  - `update_tags` ignores `update_meta`'s `False` return (`storage/base.py:385-386`). That flaw predates #428 (the same code is at `7125e16`).
- **Evidence.** `race_probe.py`, on LocalFS, one process, through the real routes (`ev-race_probe.out`):
  - A conditional PATCH with `If-Match: E0` returned **200** after batch-tags committed an edit between the PATCH's check and its write. batch-tags had also returned 200, and its edit was lost.
  - A conditional PATCH returned **200 with a new ETag** for a dataset a concurrent DELETE (204) had removed. Nothing was persisted.
  - The control, a second PATCH that takes the lock, serialised correctly and kept both tags.
- **Fix.** Either qualify the four texts to "against writers that take the store lock", or make the routes honour the lock:
  - batch-tags calls `store.update_tags` per id;
  - DELETE takes `_version_lock` plus `_meta_write_lock`;
  - `update_tags` returns `None` when `update_meta` returns `False`.
  - Either way, add a regression test like `race_probe.py`.

**F3 — LOW — `juniper_data/api/http_cache.py:138` and `:154`: `field.strip() == "*"` strips Unicode whitespace.**
- **Effect.** A `*` wrapped in NBSP or NEL is treated as `*`, not as malformed. h11 accepts these bytes as obs-text.
- **Evidence.** Measured on a real uvicorn 0.40.0/h11 server (`ev-nbsp_real_server.out`):
  - a read with `If-None-Match: \xa0*` gets **304**;
  - a read with `If-Match: \xa0*` gets **200**;
  - a PATCH with `If-Match: \xa0*` gets **200 and writes**.

  This contradicts `http_cache.py:49-54`, `REFERENCE.md:1288-1294` and `JUNIPER_DATA_API.md:909-913,1064-1066`.
- **Tests can't see it.** Starlette's TestClient re-encodes `b'\xa0*'` as `b'\xc2\xa0*'`, so no TestClient-based test can pin this.
- **Fix.** Use `strip(" \t")` in both places, and add a test that sends raw bytes through `httpx.ASGITransport`.

**F4 — NIT — the equivalence script's random sweep barely reaches long lists** (`2026-09-23_verify_entity_tag_list_regex_equivalence.py:54-61`). A mutant that differs only at 8 or more list elements produced **1** mismatch in 300,000 inputs, and the exhaustive sweep (7 characters max) cannot see it. The conclusion still holds algebraically: optional-whitespace followed by optional-whitespace is the same language as a single optional-whitespace run. **Fix:** add a structured sweep over element counts up to 12.

**F5 — NIT — `CHANGELOG.md:54-55` defines "malformed" as "not a well-formed entity-tag list" and omits `*`.** Every other text says "not `*` or a well-formed list". Taken literally, it calls `*` malformed.

**F6 — NIT — the harness docstring overclaims** (`2026-09-22_…not_vacuous.py:15-17`). It says "every behaviour the PR claims is reverted", but 7 of the 56 tests are named by no mutation. For example, "a 412 on a read is not an access" has no arm.

## Instrument adequacy

**1. Does the harness restore the tree, and can a mutation leak into the next one?** It restores, and nothing leaked.
- `apply()` saves each touched file's text. `restore()` runs in a `finally`, rewrites the file and re-reads it to prove equality. Neither run reported a restore failure.
- No stale bytecode is possible:
  - every pytest subprocess gets `PYTHONDONTWRITEBYTECODE=1`, and the child interpreter inherits it;
  - the copy excludes `__pycache__`;
  - mid-run I found 0 `__pycache__` directories and 0 `.pyc` files in the live copy.
  - This matters for M20, the only same-length edit (102 = 102 characters), which is exactly the case a stale `.pyc` could mask.
- No process-state leak:
  - each test id runs in its own interpreter with `-p no:cacheprovider`;
  - the named tests write nothing into the copy's working directory;
  - M20's timed-out child was killed and reaped (0 orphans afterwards).
- The source tree the harness copies from was byte-identical after the run.

**2. Does the child interpreter see the mutated copy?** Yes. Proven four ways:
- The parent imports the copy's `http_cache` (even when run from `/`), so `http_cache.__file__` names the copy.
- A mutation only the child can observe flipped the child's own output to `[False, False, False]` and turned the test red.
- M20 fails on the 30 s bound with the intended message.
- In both harness runs, M20 was CAUGHT while its in-process controls stayed green. The old grammar accepts the same language, so only the child could have noticed.

One caveat. Outside a tree, `import juniper_data` resolves to the **editable main checkout**. The pyproject's `pythonpath=["."]` is what keeps pytest runs on the tree under test.

**3. Would each count have come out differently had the claim been false?**
- **Suite pass counts:** yes. Failures lower them, and the import-origin probe shows each run tested its own tree's code.
- **Test counts (56 total, 16 new):** yes; they come from collection.
- **34/51/45/49:** these are fixed properties of the mutation list and cannot fail. What can fail is each arm's verdict, and I showed it does:
  - a comment-only edit came back VACUOUS;
  - an import-breaking edit came back OVERBRD;
  - a nonexistent test id turned the baseline RED;
  - each made the run exit 1.
- **What CAUGHT means:** CAUGHT is any non-zero exit. I classified every one: 31 arms failed on assertions, M13 on `pytest.raises` ("DID NOT RAISE"), and M6, M19 and M26 on a `KeyError` for the very header the mutation strips. None was a collection or import error.
- **Equivalence (0 mismatches):** all 7 language-changing mutants I fed it were caught, one of them only thinly (F4).
- **Timings:** printed, never asserted, so they cannot fail. I re-measured the scaling independently.
- **My own instrument:** one early probe of mine was misleading. The NBSP test through TestClient looked consistent with the docs until I re-probed with raw bytes.

## What this evidence cannot support

- It does not validate PR #435. It only confirms #435's premise against `ceremony.py` as it stands in this juniper-ml worktree. If v0.16.0 is cut by hand with `--target 7125e16`, F1's conclusion changes.
- The race probe forces an interleaving the code permits. It says nothing about how often the race happens under real load.
- Redis, Postgres and cross-process `flock` behaviour are from code reading only.
- The NBSP result is from uvicorn with h11 only; httptools and proxies were not tested.
- Absolute timings depend on this machine and its load.
- There are no surviving artifacts for:
  - the fix agent's runs 1–2;
  - its local pre-commit tally;
  - its `merge-file` output;
  - its "byte-identical local copy";
  - the historical BEHIND / GREEN 22/22 state.
- No security assessment; that is another lane.

**Documents referenced:**
- `reports/2026-09-24_round-42-post-merge/10-data428-round2-fix-report.md`
- juniper-data `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md`
- juniper-data `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py` and `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py`
- juniper-ml `util/release_train/ceremony.py`
- juniper-data PR #435's description

**Changed:** no repository file.

**Evidence files:** the `ev-*.out`, `suite-*.out`, `harness-main.out`, `harness-classify.out` and `probe_docs-3a76a4c.out` outputs, plus the probe scripts, are all in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA2/`.

**Operations and slips:**
- In the since-removed worktree I ran the two instructed `git fetch`es.
- In the main checkout I ran read-only git only (the screens' `cat-file`/`diff`/`log`/`rev-parse` included).
- I made GitHub API GETs only, using the existing `gh` auth, and posted nothing.
- My first doc probe tripped the app's own in-process rate limiter, with no external effect.
- The three `.pyc` files under `util/release_train/__pycache__` in the juniper-ml worktree predate my first import by 26 minutes; they are not mine.
- No credentials or email address were printed or sent anywhere.
