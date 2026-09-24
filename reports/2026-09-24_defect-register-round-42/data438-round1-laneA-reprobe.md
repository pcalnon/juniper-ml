<!-- Archived verbatim 2026-09-24 from subagent a66ebaf4cc1925e56 of session 8f86dec2 (final message). -->

**Verdict:** All eight claimed items reproduce from primary artifacts, and every count matches exactly. But the PR's headline guarantee is still universally stated and still false in one case: an unnamed `POST /v1/datasets` save can land inside a held conditional PATCH's window at head (MEDIUM). The new "cached store" scope sentence is also false (LOW). RFC 9110 §8.8.1 is still misquoted (LOW). There are five NITs.

**PR state when I finished:** OPEN, `mergeStateStatus` CLEAN, all CI checks green on `28fced18`. `main` is still `1afc3484`, so there is no merge commit to validate.

## How I ran it
- **Trees.** Extracted with `git archive` into scratch: `1afc3484` (main), `5f11fcfc` (fix), `28fced18` (head), `v0.16.0` (`39d1cab2`), `v0.15.0` (`46894ba1`). `5f11fcfc` and `28fced18` differ only in `CHANGELOG.md`, so every head code probe also covers the fix commit.
- **Import origin.** Each probe asserts that `juniper_data` imported from its own tree. Outside a tree, it resolves to the editable main checkout at `3a76a4c`.
- **Environment.** `JuniperData` (Python 3.14.2, free-threaded), uvicorn 0.40.0, h11 0.16.0, httptools 0.7.1.
- **Hygiene.** `get_secret` stubbed, `.env` reading off, servers run under `env -i` with rate limiting off. Every server I started was stopped (SIGTERM).
- **Probes are my own.** The implementer's harness and scripts were only re-run, as the brief asks.

## Claims table

| # | Claim (where) | What I measured | Verdict |
|---|---|---|---|
| 1 | batch-tags goes through `update_tags` (`juniper_data/api/routes/datasets.py:742`). Main does an unlocked two-hop read-modify-write (`datasets.py:737` get, `:746` write; line numbers confirmed at `1afc3484`). | `race_probe.py` forces interleavings through the real routes on LocalFS. **Main:**<br>• S1b: batch-tags landed inside a GET's `record_access` window; it answered 200 `updated=[id]`, and its tag was then erased.<br>• S2: a second batch finished while the first was paused; final tags were `['A']`, so B's addition was lost.<br>• S3: a conditional PATCH got 200, and the paused batch then erased its edit; the PATCH's ETag was no longer current.<br>**Head:** in every case the rival waited (`_version_lock` held, and the flock held as seen from a child process). Results: S1b and S2 kept both edits; in S3 the PATCH got 412 (its If-Match was stale by then) and the batch edit was kept. | REPRODUCED |
| 1a | The other lane's main numbers: GET undid the batch in 6/12 rounds; 28/144 additions kept. | `live_hammer.py`: uninstrumented uvicorn server on LocalFS.<br>• **Main:** GET undid the batch in 2/12 and 6/24 rounds. One server kept 20/144 and 42/288 additions; two processes sharing one directory kept 32/144 and 65/288.<br>• **Head:** 0/12 and 0/24; 144/144 and 288/288 kept; two processes 143/143 and 288/288.<br>• Their own `batch_race_demo.py` on my trees: main 37/144 kept, GET-undo 2/12, 2 of 3 conditional 200s erased; head 144/144, 0, 0. | REPRODUCED in kind; rates depend on load |
| 2 | `delete_under_lock` takes both locks for DELETE, batch delete and expired cleanup (`juniper_data/storage/base.py:415-439, 484, 657`; `datasets.py:1220`). | **S9:** lock state inside `store.delete` / `update_meta` was `(False, False)` on main for all four routes, and `(True, True)` on head.<br>**S4:** on main, DELETE returned 204 inside the PATCH window, `update_meta` returned False, and the PATCH still answered 200 with an ETag. On head, the PATCH finished first and DELETE followed.<br>**`xproc_probe.py`** (rival sent from another process): on main, delete, batch-tags and batch-delete each finished inside the window in about 0.06 s. On head, each blocked about 5.0 s until release, and both edits were kept. | REPRODUCED |
| 3 | `update_tags` returns `None` when `update_meta` fails, so the route answers 404 (`base.py:411-412`). | Meta and NPZ files removed by hand inside the window (S5): main 200 with ETag; head 404 and no ETag.<br>In-memory store, direct `store.delete()` (S5b): same result. | REPRODUCED |
| 4 | Item 2: `*` is matched after stripping only spaces and tabs, at both sites (`juniper_data/api/http_cache.py:146,162`). | **Function level:** main read `*` wrapped in any of 29 characters as `*`; head in 2 (U+0009, U+0020).<br>**Raw ASGI bytes 0x00–0xFF, both placements:** main 24/512 placements read as `*`; head 4/512. The other 508 were malformed on all six uses, and the bytes arrived as sent.<br>**Live raw socket:** 0x85 and 0xA0 are malformed on head under both h11 and httptools.<br>**Site 2 alone:** reverting it (my mutant O2) changes nothing observable — the first check already rejects such fields. | REPRODUCED |
| 5 | Item 3: the flock test. | My own N7 mutant (precondition checked under `_version_lock` but outside the flock): full unit suite 1879 passed, 1 failed — exactly `test_the_store_evaluates_the_precondition_under_its_cross_process_file_lock`. | REPRODUCED |
| 6 | Item 4: harness v1.2.0 prints "PASS: 53 mutations". | Re-run at head (21m09s): the line matches verbatim, exit 0. 75 CAUGHT, 74 OK, 0 VACUOUS, 0 OVERBRD; the 70-test baseline is green.<br>Every must-fail test of M32–M50 fails on an assertion about its own defect, never an import error (`classify_harness_arms.py`).<br>My own recount: 53 arms (19 new), 69 tests named, 58 must-fail, 11 control-only, 0 unnamed. | REPRODUCED |
| 7 | Item 5: new `StorageContainmentError`. | Symlinked `.meta.json`, 7 requests to the artifact route:<br>• main and `v0.16.0`: 400 on all 7;<br>• `v0.15.0`: 200 on all 7;<br>• head: 200 with no ETag; INM `*` 304; INM `"x"` or the real tag 200; IM `*` 200; IM `"x"` 412; IM `""` 412.<br>On head the exception is a `ValueError` but not an `InvalidDatasetIdError`. The other routes return 400, and batch-delete reports the id as not_found. | REPRODUCED |
| 8 | Item 6: an empty `If-Match` gives 412. | Main and head both: GET 412, artifact 412, PATCH 412 with nothing written (also for `" "`, `"\t"`, `" , "`). My mutants E1, E2 and E3 each turn the new tests red. | REPRODUCED (the tests pin existing behaviour) |
| 9 | Item 7: CHANGELOG. | • `[0.16.0]` at head is byte-identical to the tag's (261 lines), and so is everything from that heading to EOF.<br>• #437's 23-line bullet is unchanged; one note line was added; it stays under `### Changed`. #436's block is untouched.<br>• The note's facts check out: #437 merged at 09:14:53Z; the tag points at `39d1cab`; the Release was published at 08:52:14Z.<br>• All four misstatements are present in the released section.<br>• Renderer: the counter bullet's `_has_breaking_marker` is False; the published body says "Breaking changes: YES" because of the `### Removed` entry; head's `[Unreleased]` gives `_is_breaking=False`. | REPRODUCED (see F1, F2, F5) |
| 10 | Item 8: the equivalence sweep. | 2,396,745 + 300,000 + 798,331 = **3,495,076** checks, 926,194 accepted by both, 0 mismatches.<br>Negative control PASS: the at-most-7 mutant scores 0 / 1 / 787,344, the at-most-10 mutant 0 / 0 / 531,447. | REPRODUCED (see F4) |
| 11 | The test file goes 56 → 69; 9 fail on main. | 56 collected at main and 69 at head. Head's file against main's code: 9 failed, 60 passed (the 9 the PR names). On head: 69 passed. `-m "unit and not slow"` selects all 69. | REPRODUCED |
| 12 | Unit suite 1880 (main 1867); api + integration 118; coverage 97.78%. | 1880 at head and 1867 at main, both rc 0. api + integration: 118 at both. `run_coverage.bash`: 1740 passed + 140 deselected, 7 subtests, TOTAL 97.78%, "PASS: All 100 modules >= 85.0%". | REPRODUCED |
| 13 | 186 tests passed on a GIL Python 3.13. | Not re-derived: no environment here has the dependencies. | NO ARTIFACT |
| 14 | "Every route that edits or deletes a dataset" takes the locks, so the check "can no longer … lose the race". | S7 (next section). | **REFUTED** (F1) |
| 15 | The guarantee holds "within one process" on the cached store. | `cached_scope_probe.py`. | **REFUTED** (F2) |

## Findings

**F1 — MEDIUM — `POST /v1/datasets` still writes inside a conditional PATCH's window, so the guarantee is still false as stated.**
- **Where it is claimed:**
  - `CHANGELOG.md:55` ("can no longer pass its check and then lose the race") and `CHANGELOG.md:62` ("Every route that edits or deletes a dataset now takes the same two locks");
  - `docs/api/JUNIPER_DATA_API.md:1070`, whose list of routes leaves out create;
  - `docs/REFERENCE.md:1266` and `docs/REFERENCE.md:1330`;
  - `juniper_data/api/routes/datasets.py:1238-1240`, which is published in OpenAPI.
- **Code:**
  - The existence check is at `datasets.py:248`; the save is `datasets.py:447` → `save_versioned`.
  - `juniper_data/storage/base.py:548-552` takes `_version_lock` only for a named dataset and calls a bare `self.save` otherwise. It never takes `_meta_write_lock`.
  - `/batch-create` calls the same function.
- **Evidence** (`race_probe.py` S7 at head; identical at main):
  - POST A checks (dataset absent) and generates slowly; POST B creates the same id.
  - A conditional PATCH, whose If-Match is B's tag, is held after its check.
  - A's save finishes inside the window (tags on disk become `['from-A']`). The PATCH then answers 200 and writes B's stale snapshot over it.
  - A's 201 promised tags `['from-A']` and `ttl_seconds=3600`. The stored dataset ends with `['cond','from-B']` and no TTL.
  - Named creates wait for `_version_lock` within one process. They take no flock, so from another worker they can land in the window too (code reading only).
- **Exposure:** it needs two concurrent first creations of the same params while a conditional PATCH is in flight. The round-3 census in `data428-round3-laneB-refute.md` found no consumer that sends conditional headers. The mechanism predates #428.
- **Fix:** in `save_versioned`, take both locks, re-check existence, and return the existing metadata. This also closes the lost update between two creates. Alternatively, scope all five texts to "edits or deletes an *existing* dataset" and name create as the exception.

**F2 — LOW — The new "within one process" scope sentence is false for `CachedDatasetStore`.**
- **Where:** `CHANGELOG.md:72-73`, and `docs/api/JUNIPER_DATA_API.md:1075`, where #438 added `CachedDatasetStore`.
- **Mechanism:** on an artifact cache miss, `juniper_data/storage/cached.py:153,159` reads the primary's metadata and saves it into the cache without any lock. `get_meta` reads the cache first.
- **Evidence** (`cached_scope_probe.py`: LocalFS primary, in-memory cache, `write_through=False`, one process; identical at main):
  - A conditional PATCH answers 200 with tags `['acknowledged']`.
  - A concurrent artifact read's cache fill, followed by its `record_access`, leaves the primary's tags at `[]`.
  - GET then serves the pre-edit ETag. A PATCH carrying the ETag that the 200 handed out gets 412; one carrying the pre-edit ETag gets 200.
- **Exposure:** the service wires LocalFS only (`juniper_data/api/app.py:42`).
- **Fix:** remove the cached store from the guarantee, or make the cache fill take the locks and refuse to overwrite a newer entry.

**F3 — LOW — RFC 9110 is still misquoted.**
- **Where:** `juniper_data/api/http_cache.py:17-19` and `docs/REFERENCE.md:1362-1363` both still present "Same content, possibly different bytes" as RFC 9110 §8.8.1's definition. #438 did not touch either.
- **Evidence:** I fetched `rfc9110.txt` from rfc-editor.org (sha256 `21c1cdce…7232a`). Neither "possibly different" nor "same content" occurs in it.
  - §8.8.1 defines a weak validator as metadata that "might not change for every change to the representation data".
  - The sentence that actually supports `W/` here is: "a validator is weak if it is shared by two or more representations of a given resource at the same time, unless those representations have identical representation data."
  - `docs/api/JUNIPER_DATA_API.md:970-971` attributes the phrase to the owner ruling instead, which is fine.
- **Fix:** quote that sentence in both places.

**F4 — NIT — The equivalence sweeps cannot see a long list with a whitespace-only element.**
- **Evidence** (`sweep_blindspot.py`): the structured sweep contains no input with a whitespace-only element. My mutant W8 refuses such an element from the 9th position on. The input `',,,,,,,, '` is accepted by the old and new patterns and refused by W8, yet W8 scores 0/0/0 across all three sweeps.
- **Why the conclusion still holds:** the pattern line is byte-identical at main and head, and round 3 proved it equivalent to the old one (`data428-round3-laneA1-security.md`).
- **Fix:** add whitespace-only elements at each position to `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py`, and add W8 to `util/ad-hoc/2026-09-24_verify_equivalence_sweeps_catch_long_list_mutants.py`.

**F5 — NIT — The OWS entry names only NBSP and NEL.**
- **Evidence** (`live_ows.py`): on main under h11, `*` wrapped in 0x1C or 0x1F was also read as `*` (httptools rejects those bytes with 400). At function level, the released code accepted 29 characters.
- The fix covers all of them. The `CHANGELOG.md` entry and the sentences in `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md` are true but incomplete.
- **Fix:** say "anything but SP/HTAB".

**F6 — NIT — Serving a dataset with a symlinked metadata file logs the dataset id at ERROR on every download.**
- **Evidence** (`containment_probe.py`, head): the route's own WARNINGs name the exception type only. But each served request also produced an asyncio "Exception in callback" ERROR whose traceback carries the id (from the message at `juniper_data/storage/local_fs.py:116`): 5 of 5.
- `v0.15.0` did the same, 7 of 7. The PR's "noticed" note mentions the ERROR but not that it carries the id.
- **Fix:** skip `record_access` when `metadata_readable` is False, or have the callback log the type only.

**F7 — NIT — The storage-fault fix covers the metadata file only; a symlinked `.npz` still gets the caller's 400.**
- **Evidence** (`containment_probe.py` case N): the artifact route returns 400 on all 7 requests at head, main and `v0.15.0`.
- The PR's "noticed" list names only the other routes.
- **Fix:** add this case to that list for the same ruling.

**F8 — NIT (outside #438's own change) — The next release's notes would not be flagged breaking.**
- Head's `[Unreleased]` renders "Breaking changes: NO" with #437's `generator_version` 6.0.0 inside it. That bump changes every `equities_seq` dataset_id; 0.15.0 flagged the analogous 4.0.0 bump "BREAKING (contract)".
- The PR body's renderer counts ("Added 1, Fixed 5") predate `28fced18`. It is now Added 1, Changed 1, Fixed 5.
- **Fix:** an owner ruling on #437's marker, and refresh the PR body.

## Could each instrument have answered differently?
- **Race, cross-process and live probes:** each gave opposite results on main and head.
- **OWS probe:** a recording ASGI wrapper confirms the bytes arrived as sent.
- **CHANGELOG check:** it can report a difference — main's `[0.16.0]` does not match the tag's.
- **My 15 own mutants:** 14 were caught; O2 is unobservable by construction.

## What this evidence cannot support
- **Forced interleavings** show only that the code allows each race. The live loss rates depend on load; the box ran at a load average of about 10–15.
- **One unexplained head result:** in head's first two-process run, one batch request (1 of 144) got no 200 and its cause was not captured. The re-run with logging gave 288/288.
- **Main's live runs** each hit one client-side httpx `TypeError` inside a GET job. It did not affect any batch verdict.
- **Environment:** production uses a default-GIL 3.14 and newer uvicorn; I did not test that.
- **Stores assessed by reading code only:** Redis, Postgres, HF and Kaggle, and cross-host locking or NFS. S7's cross-worker variant for named creates is also from code reading.
- **Not re-run by me:** pre-commit and the ci-tools screens. GitHub's checks were green.

## Scripts I wrote
All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data438-laneA/scripts/`:
- **Shared helper:** `common.py`
- **Race and lock probes:** `race_probe.py`, `xproc_probe.py`, `live_hammer.py`, `serve.py`, `cached_scope_probe.py`, `deadlock_probe.py`
- **Header, containment and CHANGELOG probes:** `ows_probe.py`, `live_ows.py`, `containment_probe.py`, `changelog_check.py`, `renderer_check.py`
- **Mutants and harness checks:** `mutants.py`, `classify_harness_arms.py`, `harness_coverage_recount.py`, `sweep_blindspot.py`
- **Runners for the implementer's scripts, the suites and coverage:** `run_suites.bash`, `run_equivalence.bash`, `run_coverage_head.bash`

Logs are in `../logs/`. I also ran the other lane's `primer-r2-laneB/batch_race_demo.py`, unmodified.

**Documents referenced:**
- juniper-ml: `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, `data428-round3-laneA1-security.md`, `data428-round3-laneA2-claims.md`, `data428-round3-laneB-refute.md`, `util/release_train/ceremony.py`, `util/release_train/notes_render.py`
- juniper-data: `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/api/JUNIPER_DATA_API.md`, `juniper_data/api/http_cache.py`, `juniper_data/api/routes/datasets.py`, `juniper_data/storage/base.py`, `juniper_data/storage/local_fs.py`, `juniper_data/storage/cached.py`, `juniper_data/api/app.py`, the four `util/ad-hoc/` scripts
- RFC 9110 (`rfc9110.txt`)

**Changed:** no repository file. Outside scratch, my only writes were `git fetch origin` and `git fetch origin refs/pull/438/head`, in the juniper-data checkout.
