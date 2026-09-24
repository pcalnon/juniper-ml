<!-- Archived verbatim 2026-09-24 from subagent a9d3743d17bb6ab8d of session 8f86dec2 (final message). -->

Lane A report on the Appendix E correction to `…API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`: every numbered claim was re-derived from source, a live server and RFC 9110, and no line that anything cites has moved.

Short names used below: **`PRIMER.md`** = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`; **`REGISTER.md`** = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (both in the `hazy-beaming-map` worktree). **Changed:** nothing in any repo or worktree; all probes and outputs are in `…/scratchpad/r42/primer-laneA/`.

## Verdict

The technical substance of `PRIMER.md` Appendix E is correct. But the correction is incomplete: three passages that repeat the refuted premises have no marker. Its `APD-DATA-054` citation resolves only in an uncommitted `REGISTER.md` edit. And "ships in 0.16.0" is not yet true.

## Claims

| # | Claim | What I measured | Result |
|---|---|---|---|
| 1 | `compute_checksum` hashes an uncompressed `np.savez` with sorted keys | `core/artifacts.py:33-63`. Recomputing that form from the served arrays gives the stored checksum `ca704074…` on both stores | REPRODUCED |
| 2a | The four named stores serve `np.savez_compressed` output | `local_fs.py:212`, `memory.py:71`, `redis_store.py:107`, `postgres_store.py:392`. Every served zip entry uses DEFLATE (method 8) | REPRODUCED |
| 2b | Are there other stores? | Yes, three: `cached.py`, `hf_store.py`, `kaggle_store.py`. All delegate to a backing store and serve the same compressed output. HF/Kaggle metadata carries no checksum, so those datasets get no ETag at all. The service's lifespan installs only LocalFS (`app.py:42`) | REPRODUCED |
| 2c | `sha256(served bytes) != checksum` for every store | Via the API: LocalFS `35a26704…`, in-memory `41736b55…`, both different from `ca704074…`. In-process: Redis and Postgres (fake clients, real save/serve code), Cached, HF and Kaggle also differ. 7 of 7 stores | REPRODUCED |
| 3 | In-memory sorts keys; the others don't | Source, plus served entry order: LocalFS, Redis and Postgres keep generator order; in-memory is sorted. The same dataset is served as two byte strings (LocalFS vs in-memory, and `CachedDatasetStore` across cache states) | REPRODUCED |
| 3b | Another numpy or zlib can change the bytes | numpy 2.4.1, 2.4.6 and 2.5.3 with zlib 1.3.1 and 1.3.2 all produced identical bytes (`35a26704…`) | NO ARTIFACT (key-order half reproduced) |
| 4 | Artifact `ETag: W/"<checksum>"`; strong body-SHA-256 ETag on `/{id}` and `/latest`; `private, no-cache` on all three; bodiless 304 | Ran `origin/main` 3a76a4c on :18761 (LocalFS) and :18762 (in-memory): 70 of 70 checks pass. Current main `39d1cab2` differs only in `CHANGELOG.md` | REPRODUCED |
| 5a | `If-Match` matches the artifact only through `*` | `"c"`, `W/"c"` and the served-bytes digest all get 412; `*` gets 200 | REPRODUCED |
| 5b | PATCH tags is conditional on the strong metadata ETag | Current tag: 200 with a new ETag equal to the body's SHA-256. Stale tag: 412, nothing written. The artifact's tag: 412. With no precondition at all: 200 (no 428) | REPRODUCED (precondition is optional) |
| 5c | Counters served at `/access` | 200 with `no-store`. The metadata ETag stayed stable while `access_count` went 9→10 | REPRODUCED |
| 6 | `generate_dataset_id` = generator, version, params, plus a nonce when there is no seed | `dataset_id.py:46-61` | REPRODUCED |
| 7 | `equities` `end_date=None` means today | `defaults.py:18`, `params.py:68-71`, `generator.py:315`. The binder does not bind `end_date` (`:700-701`), and the seed defaults to non-None, so the id is deterministic | REPRODUCED (source only) |
| 8 | RFC 9110 §8.8.1 defines weak/strong; §13.1.5 forbids weak validators for If-Range | Fetched rfc9110.txt: §8.8.1 defines both; §13.1.5 says a client "MUST NOT generate an If-Range header field containing an entity tag that is marked as weak" and uses strong comparison. §13.1.1 (If-Match strong) and If-None-Match (weak) also match | REPRODUCED |
| 9a | #428 merged 2026-09-23 | `2026-09-23T22:38:40Z`, commit `af7831be` | REPRODUCED |
| 9b | "It ships in juniper-data 0.16.0" | No v0.16.0 tag or Release; PyPI's latest is 0.15.0, whose route has zero ETag, Cache-Control or 304 code. #428 merged after the release PR #433 (20:24:53Z); #435 (`39d1cab2`, CHANGELOG only) folded it into the single `[0.16.0]` section | REFUTED as stated (pending) |
| 10a | `REGISTER.md` cites `PRIMER.md` by bare line number | Its `Primer` column and detail rows, e.g. `APD-DATA-017` → 3647 | REPRODUCED |
| 10b | No line before Appendix E moved | All 9866 HEAD lines are in place: 9853 identical, 13 with only the marker appended. All 153 cited lines keep HEAD's text. Mutation-checked: one inserted line gives FAIL with 148 flagged; an in-place edit gives FAIL on exactly [3647]. Re-run after a concurrent `REGISTER.md` edit gives the same result | REPRODUCED |
| — | Anchor `#e1-artifact-validator` | Resolves uniquely to L9876 under GitHub's slug rules; the repo's `_heading_to_anchor` agrees; 13 links use it | REPRODUCED |
| — | `APD-DATA-032` and `APD-DATA-054` exist | 032 is at `REGISTER.md` L801. 054 is missing at HEAD and origin/main, and present only in the uncommitted worktree `REGISTER.md` (see F2) | 032 REPRODUCED; 054 conditional |
| — | "Each affected passage … gains a Corrected link" | Three affected passages have no marker (F1) | REFUTED |
| — | Script output and lint | The worktree `PRIMER.md` is byte-identical to the script's output on HEAD; markdownlint 0.42.0 reports 0 findings | REPRODUCED |

**The 13 marked lines in `PRIMER.md`:**
- **Refuted on the line itself or its paragraph:** 462, 1956, 1958, 1960, 1974, 2015, 2026, 3995, 4245.
- **Paragraph-level only:** 3650 and 4233 carry true text on the marked line; the refuted text is on 3647 and 4231-4232.
- **Mostly TRUE:**
  - 4018: "could carry an ETag for free and support conditional GETs" is exactly what #428 shipped; only "immutable blob" is wrong.
  - 4251: the access-counter trap and "split them into a sub-resource" are what #428 adopted. Only "the artifact endpoint's would work perfectly" is wrong, and the counters-in-body statement has been overtaken.

## Findings

- **F1 — MEDIUM. Three affected passages have no marker.**
  - `PRIMER.md` L3685: "Emit an `ETag` whenever you already compute a digest — juniper-data computes one and discards it — and support `If-Match`…". This is the same claim as the marked L2015 and L3647.
  - `PRIMER.md` L5332, II.11's motivation: "identifiers are already content-addressed… strongest possible candidate for `ETag` plus `Cache-Control: immutable`… The validator it needs is already sitting in the codebase". The example's docstring at L5352-5360 repeats it; the example's own code is self-consistent.
  - `PRIMER.md` L9509-9510, Appendix A Q37: "Juniper's dataset artifacts are content-addressed and would qualify… the right header is `private, max-age=31536000, immutable`". This is the exact prescription E.1 item 2 says would serve stale data for a year.
  - **Fix:** append the marker to L3685 (216 characters with it) and L9510 (413). L5332 would reach 543 characters, over the 512 limit, so name it (and its docstring) by line number inside E.1. Or reword the "Each affected passage" sentence.
- **F2 — LOW. E.1 cites a row that exists only in an uncommitted edit.**
  - E.1 calls the gap "defect-register row `APD-DATA-054`". The row is absent at HEAD and origin/main, and was absent everywhere when I first checked.
  - It appeared in the worktree `REGISTER.md` (L1294) at 08:33:46Z, written by a concurrent session via `util/ad-hoc/2026-09-24_register_round42_close_eco008_file_eight.py`. That row in turn points back to "its Appendix E".
  - **Fix:** ship both edits in one PR, or land the register row first.
- **F3 — LOW. The release status is stated as fact.**
  - "It ships in juniper-data 0.16.0" and the present-tense "juniper-data sends…" are true only of unreleased `main`. PyPI 0.15.0 sends none of these headers.
  - **Fix:** "queued for juniper-data 0.16.0, unreleased as of 2026-09-24; 0.15.0, the latest on PyPI, sends none of these headers."
- **F4 — LOW. Two markers sit on paragraphs whose main advice was right.**
  - The markers on `PRIMER.md` L4251 and L4018 flag paragraphs whose principal claims #428 vindicated. E.1 never says which part is corrected, so a reader could take L4251's marker as refuting the sub-resource advice that juniper-data followed.
  - **Fix:** add one sentence to E.1 saying what stands.
- **F5 — NIT. The L462 marker sits mid-paragraph.** The refuted sentence at L463 ("a stable strong validator, was already done") renders after the marker, although the script's docstring says each target is a paragraph's last line. **Fix:** target L463.
- **F6 — NIT. A paraphrase is quoted as if from the RFC.** "Same content, possibly different bytes" is in quotation marks next to "(RFC 9110 §8.8.1)" but is not RFC text. **Fix:** drop the quote marks, or quote §8.8.1: "a validator is weak if it is shared by two or more representations of a given resource at the same time, unless those representations have identical representation data".
- **F7 — NIT. "Is conditional on" overstates PATCH.** A PATCH with no precondition returns 200; there is no 428. Since the corrected passage is about 428 Precondition Required, say the precondition is optional.
- **F8 — NIT. "Deleted or expires, then re-created" needs a qualifier.** Expiry alone removes nothing on LocalFS, in-memory or Postgres: `create_dataset` checks `get_meta` with no expiry test (`routes/datasets.py:248-267`). Only `cleanup_expired` (`base.py:430`) or Redis's TTL removes it. **Fix:** "deleted (or expired and cleaned up)".
- **F9 — NIT. Lead with the mechanism that can be observed.** The numpy/zlib mechanism didn't reproduce on this host (3b). The key-order mechanism does, today: dataset `spiral-3.0.0-cce9718de3a8bca7` is served as two different byte strings under one checksum.

## What this evidence cannot support

- Redis and Postgres ran in-process with fake clients (`redis` and `psycopg2` are absent from the env; no server).
- Only the `spiral` generator was exercised, with auth off, on the JuniperData env's FastAPI, Starlette and uvicorn versions. No container image, proxy or shared-cache behaviour was tested.
- The `equities` wall-clock regeneration and the delete → re-create → different-bytes path were checked from source only.
- The 2026-09-23 owner ruling is corroborated by the #428 PR body, the CHANGELOG, `http_cache.py`'s docstring and the new register row, not by a primary record.
- Whether #428 actually ships in 0.16.0 depends on a Release that hasn't been cut.
- The unmarked-passage sweep was regex-driven, so a claim phrased differently could have been missed.
- `REGISTER.md` changed mid-validation; I checked both the pre-edit (140 Primer fields) and post-edit (148) snapshots.
- I did not enumerate other documents that cite `PRIMER.md` line numbers. Since no HEAD line moved, such citations would still resolve.

**Hygiene:**
- No slips: no environment variables, tokens or credentials were printed, nothing was sent externally, and all `gh` calls were read-only.
- Both servers stopped (rc=-15) and no processes are left.
- Others changed the worktree during this run: `docs/REFERENCE.md`, `REGISTER.md`, the new `data428-round3-*` reports and the register script. None of that was me.

**Key files** (in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneA/`):
- `probe_http.py`, with its results in `probe_http.json` and `probe_http.log`
- `probe_store_bytes.py` and `probe_store_bytes.out`
- `register_primer_cites.py` and `register_primer_cites.rerun.out`
- `anchor_check.py`
- `find_unmarked_wide.py`
- `cross_numpy.bash`
- `replay_script.bash`
- `lint_copy.bash`
- `rfc9110.txt`
