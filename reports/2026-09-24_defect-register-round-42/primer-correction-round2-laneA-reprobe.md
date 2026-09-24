<!-- Archived verbatim 2026-09-24 from subagent a7631c36ca821d652 of session 8f86dec2 (final message). -->

# Lane A, round 2: re-derivation of juniper-ml PR #2075 (primer correction v2)

**Verdict: v2 is correct on everything mechanical and almost everything factual, but its fix pass added one new false claim and left one release-state sentence already stale.**
- **What holds:** line invariance (22 markers + 30 rewrites), all three instruments, Appendix E's juniper-data claims, the RFC 9110 quotes and the anchors.
- **The new false claim:** the II.11 docstrings say juniper-data#428 ended a tag lost-update. juniper-data#263 and #282 had already closed it; I measured this on the published pre-#428 wheel.
- **The stale sentence:** the release-state wording was overtaken by the v0.16.0 Release 2.5 minutes after it was written.

**Documents cited** (short forms used on every reference below):
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`. Line numbers are at `b6129bf8` unless stated.
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
- `…CONSENSUS-PROCEDURE.md` = `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
- `…round1-laneA-reprobe.md` / `…round1-laneB-refute.md` = `reports/2026-09-24_defect-register-round-42/primer-correction-round1-lane{A-reprobe,B-refute}.md`.
- `ml_primer_v2_pr_body.md` = the PR body in the session scratchpad.

**Changed:** nothing in any repository. All work is under `…/scratchpad/r42/primer-r2-laneA/`.

**State used:**
- PR #2075: OPEN at `b6129bf8`.
- juniper-ml main: `602094e3`. Its 3 new commits don't touch `…PRIMER.md`, `…DEFECT-REGISTER.md` or the harness.
- juniper-data main: `1afc3484` (#437). It moved past the brief's `3adb33ea`. Since #428 the only changes in api/storage/core are logging in `storage/cached.py` and an equities_seq change in `routes/generators.py`.
- The fix-forward branch `fix/conditional-requests-round3-followups` does not exist on the remote and has no PR. Appendix E is judged against `1afc3484`.
- Entry points: git objects, juniper-data run in-process, the PyPI wheel, rfc-editor.org. None are the PR body's numbers.

## Claims

| # | Claim (where) | What I measured | Result |
|---|---|---|---|
| 1 | The first 9,866 lines don't move; the rest is the appendix (`ml_primer_v2_pr_body.md`; `…PRIMER.md` L9873) | My own classifier (`line_invariance.py`). Its self-test catches all 5 mutation types. 9,814 unchanged, 52 changed, 0 missing. Head has 9,958 lines = 9,866 + 92 appended, starting with a blank L9867 and the heading at L9868 | REPRODUCED |
| 2 | "22 prose passages" gain a marker | 22 marker-only lines: the base text survives verbatim and only the marker is added. 22 markers at head, 0 at base | REPRODUCED |
| 3 | "30 same-line rewrites" | 25 rewrites plus 5 that keep the old text verbatim but add non-marker prose (L5, L4222, L5654, L5672, L5774). That is L5, L3639, L4222 and 27 II.11 lines | REPRODUCED |
| 4 | No line over 512 characters | Only the existing L786, L1344 and L9481, all unchanged. Longest changed line is 443 | REPRODUCED |
| 5 | Register citations unaffected | `…DEFECT-REGISTER.md` cites 154 primer lines at main, 155 at #2074. 3 of them changed (L3647, L4200, L4279), all marker-only | REPRODUCED |
| 6 | Build script `--check`: working tree MATCHES | Scratch copy with `git show HEAD:` replaced by the `dcfc024f` primer: "22 markers + 30 … MATCHES", rc 0, nothing written. Mutations: 1 character in Appendix E → DIFFERS; 1 character on L100 → DIFFERS; base with an inserted line → REFUSED | REPRODUCED (pre-commit state only; see L1) |
| 7 | Harness: 6 files, 62 tests pass, same count as base | Toolchain pinned to Appendix D (CPython 3.13.13, FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2): head 62 and base 62 passed (15/15/32). Latest toolchain (3.14.7, Starlette 1.7.0, Pydantic 2.13.5, pytest 9.1.1): head 62 passed. Only the two II.11 files differ | REPRODUCED |
| 8 | Toy probe: head MATCH 4/4, base MISMATCH 4/4 | Same result on each of 3 toolchains (pinned, latest, JuniperData with Starlette 0.50.0) | REPRODUCED |
| 9 | "its metadata responses now send exactly the bytes their strong `ETag` hashes" (`…PRIMER.md` L9937) | My own probe over every route, including a non-ASCII parameter. At head every 200 that carries an ETag matches its body. At base the metadata responses mismatch; the artifact matches at both | REPRODUCED |
| 10 | The anchors resolve | My GitHub slugger and the repo's doc-tools agree. `#e1-artifact-validator` → L9878 (18 uses); `#e2-conditional-tag-writes` → L9940 (4 uses); `#appendix-e--corrections` → L9868 (1 use). All three are unique. 122 in-document fragment links, 0 unresolved (base: 99, 0) | REPRODUCED |
| 11 | The TOC omits Appendix E; the Status line points to it | TOC at L92-111 lists A-D; the L5 link resolves | REPRODUCED |
| 12 | Lint clean | markdownlint 0.42.0 (pinned) and 0.48.0: 0 findings at head and base. A mutant copy triggers MD009/MD013/MD022/MD024, so the linter can fire | REPRODUCED |
| 13 | #428 merged 2026-09-23 | 2026-09-23T22:38:40Z, `af7831be` | REPRODUCED |
| 14 | "#428 is queued for juniper-data 0.16.0, unreleased when this was written" (L9883) | Release v0.16.0 published 08:52:14Z, tagging `39d1cab2`, which contains `af7831be`. The text's commit is `855f39db`, authored 08:49:45Z | Time-scoped clause REPRODUCED (by 2m29s); present-tense "is queued" REFUTED as of this run (M2) |
| 15 | "0.15.0, the latest on PyPI, sends none of the headers below" | PyPI at 09:21:33Z and 09:46:44Z: latest 0.15.0, no 0.16.0 files. The wheel's sha256 `8b8434a7…` matches PyPI's digest. Its `api/` has 0 ETag/Cache-Control/If-Match/304/Content-Location tokens (main has 22+). Run live: no validator headers; `If-None-Match: *` → 200 with the full body; `access_count` still in the metadata body | REPRODUCED (as of 09:46Z) |
| 16 | `compute_checksum` = SHA-256 of an uncompressed, key-sorted `np.savez` | `core/artifacts.py:33-63`. Recomputing it from the served arrays gives the stored checksum (`995412b1…`) | REPRODUCED |
| 17 | Every store serves `np.savez_compressed`, so `sha256(served) != checksum` | Live: LocalFS `92fa9ce7…`, in-memory `d015c26b…`, all DEFLATE entries. From source: `local_fs.py:212`, `memory.py:71`, `redis_store.py:107`, `postgres_store.py:392`; HF and Kaggle delegate to `_cache_store`, default in-memory | REPRODUCED (Redis/Postgres from source only) |
| 18 | One checksum, two byte strings: in-memory sorts keys; `CachedDatasetStore` differs by cache state | Same id and checksum on both stores. LocalFS keeps generator order (X_train, y_train, …); in-memory is sorted. Cached store: 1st read `92fa9ce7…`, 2nd read `d015c26b…`, same ETag | REPRODUCED |
| 19 | "another numpy or zlib could do the same" | Not tested | NO ARTIFACT |
| 20 | RFC 9110 §8.8.1 quote (L9897-9899) | Verbatim, located in §8.8.1; a one-word mutation is not found | REPRODUCED |
| 21 | `W/"<checksum>"` per the owner's 2026-09-23 ruling | Live `W/"995412b1…"`. The ruling is recorded in #428's PR body, juniper-data's CHANGELOG, `http_cache.py`, and APD-DATA-054 in #2074 | REPRODUCED (secondary records) |
| 22 | `If-None-Match` compares weakly; `If-Match` compares strongly, so only `*` matches | Live: INM `W/"c"` → 304, `"c"` → 304, other → 200; IM `W/"c"`, `"c"` and `"sha(served)"` → 412, `*` → 200. §13.1.1 and §13.1.2 sentences verbatim | REPRODUCED |
| 23 | `If-Range` takes only a strong validator (§13.1.5) | "A client MUST NOT generate an If-Range header field containing an entity tag that is marked as weak." is verbatim in §13.1.5 | REPRODUCED |
| 24 | PATCH can be made conditional on a strong metadata ETag; the precondition is optional; no 428 | Live: no precondition → 200; stale `If-Match` → 412 and nothing written; current → 200 with a new ETag equal to sha256(body); the artifact's tag → 412; `If-None-Match: *` → 412. No `428` in non-test code | REPRODUCED |
| 25 | The counters left the body (APD-DATA-032) and are served at `/access` | Live: the body has neither counter; `/access` → 200, `no-store` | REPRODUCED |
| 26 | Rows APD-DATA-054 and -055 exist | Absent from `…DEFECT-REGISTER.md` at main; present at #2074's head `6a9af70c` (L1294-1295). #2074 is OPEN | NOT ON MAIN (L2) |
| 27 | `generate_dataset_id` hashes the request, not the bytes | `dataset_id.py:46-61`; the route hashes `params.model_dump()` | REPRODUCED |
| 28 | Since #322 (2026-09-03) the default seed is `DEFAULT_GENERATOR_SEED`, so an omitted seed gives a deterministic id | #322 merged 2026-09-03T20:37:09Z. Census of 16 generators: 10 use DGS (42), spiral uses `SPIRAL_DEFAULT_SEED` (42), and 5 synthetic ones default to `0` with `seed: int`. The omitted-seed id is stable for all 16 | Conclusion REPRODUCED; the premise is over-general (N1) |
| 29 | A deleted-and-re-created dataset serves whatever the generator produces now, at the same URI | Live with csv_import: `csv_import-3.0.0-dcc99011773c30e9`. After editing the upstream file, both checksum and bytes change. Control (file unchanged): identical bytes | REPRODUCED |
| 30 | For equities, `end_date=None` means today, so one id covers different data | `defaults.py:18` is `None`; `generator.py:315`; the binder updates only `max_symbols`/`allow_truncation`; seed defaults to 42 | REPRODUCED (from source) |
| 31 | `private, no-cache` on the artifact and both metadata reads; bodiless 304 | Live on all three; the 304 has length 0 and carries ETag and Cache-Control | REPRODUCED |
| 32 | `http_cache.py`'s docstring records the corrected reasoning | Its lines 10-41 do. Its lines 17-19 put "Same content, possibly different bytes" in quotes as the §8.8.1 definition; that phrase is not in RFC 9110 | REPRODUCED with a caveat (N4) |
| 33 | E.2: #263 (2026-08-14) made tag updates atomic; #282 (2026-08-23) did it across processes on LocalFS | Merged 20:49:51Z and 20:22:46Z. #263's diff moves the read-modify-write under `_version_lock`; `local_fs.py:124-156` takes a `flock` | REPRODUCED |
| 34 | E.2: #428 evaluates preconditions inside the store's lock; 412 writes nothing; new strong ETag | `base.py` `update_tags` checks `precondition` inside `_version_lock` + `_meta_write_lock`; live | REPRODUCED |
| 35 | E.2: protection is per host; Redis, Postgres and cached stores hold a per-process lock | Only `local_fs.py` overrides `_meta_write_lock`. The cached store takes only the per-process lock, even over a LocalFS primary | REPRODUCED (wording, N2) |
| 36 | E.2: `/latest` and the PATCH response carry `Content-Location` | Live: `/v1/datasets/spiral-3.0.0-8182cad20862431f` on both | REPRODUCED |
| 37 | E.2: "Each was true when written" | The E.2-linked lines blame to `8d3d4573` (2026-08-14T02:11:45Z), before #263 merged | REPRODUCED |
| 38 | II.11 (L5362-5364, L5786-5787): the lost update lasted "until juniper-data#428" | 12 concurrent unconditional PATCHes keep 12/12 tags on main and on the pre-#428 0.15.0 wheel. The negative control (pre-#263 read-modify-write restored) keeps 1/12 and 2/12 | REFUTED (M1) |
| 39 | L5366 "unauthenticated"; L5419-5421 and L5901 say immutability comes from deterministic synthesis | The toy has no auth. `_synthesize_artifact(id, n_samples)` is pure, and `n_samples` comes from the params the id hashes | REPRODUCED |
| 40 | L3639 no longer reuses the id's digest | `9c4b7e2d01f5a863` vs `a3f8e12b4c567890` | REPRODUCED |
| 41 | L4222 restores "applied to the representation data"; the quote at L4222-4224 is verbatim | Both verbatim in §8.8.1 | REPRODUCED |
| 42 | E.1 names II.2's table row and heading and II.11's motivation paragraph | L3426, L3431 (whose text contains "content-addressed dataset ID"), L5332 | REPRODUCED |
| 43 | "Each affected prose passage … gains a **Corrected** link" (L9871-9872) | L594, L4213 and L4220 are unmarked and not named (L1954 and L3871 are borderline) | REFUTED (L3) |

## Findings

### MEDIUM

**M1. The II.11 rewrites credit juniper-data#428 with ending a tag lost-update that #263 and #282 had already closed.**

The phrases:
- `…PRIMER.md` L5362-5364: "Tags are mutable, so two clients that read / the same dataset and both PATCHed it produced a silent lost update -- until / juniper-data#428 made that PATCH conditional on ``If-Match``."
- `…PRIMER.md` L5786-5787: "it is the scenario / juniper-data's tag PATCH got wrong until juniper-data#428."

Evidence:
- **The PATCH is a delta.** Its body is `UpdateTagsRequest{add_tags, remove_tags}` (`core/models.py:245-249`), so a stale PATCH cannot erase another client's tag. Live, two unconditional deltas in sequence both survive.
- **The lock arrived in #263 and #282.** #263 (`da2be273`) moved the whole read-modify-write under the process-wide `_version_lock`, and #282 added LocalFS's per-host `flock`.
- **Measured before #428.** 12 concurrent unconditional PATCHes keep 12/12 tags on main, and also on the published 0.15.0 wheel, which predates #428 (its `update_tags` has no precondition parameter). Restoring the pre-#263 two-hop read-modify-write keeps only 1/12 and 2/12.
- **It contradicts the same document.** `…PRIMER.md` L4277-4279 says an `If-Match` check "would buy a correct 412 and change nothing about the race … The storage layer is what would have to change first". E.2 (L9946-9948) credits #263 and #282, and APD-DATA-007 in `…DEFECT-REGISTER.md` reads "FIXED (data#282)".
- **It repeats a round-1 finding.** L5364 brings back the unqualified "conditional" that `…round1-laneA-reprobe.md` F7 flagged. #428's precondition is optional, so it protects only clients that send `If-Match`.

**Fix** (keep the same number of lines). For example:
- L5362-5364: "…Tags are mutable, and until juniper-data#263 / (2026-08-14) two concurrent tag PATCHes could silently lose one; since / juniper-data#428 a PATCH may also carry an optional ``If-Match``."
- L5786-5787: "whole reason optimistic concurrency exists. juniper-data's add/remove tag PATCH / gained an optional ``If-Match`` in #428; its lost update was closed by #263."
- Then re-run the harness.

**M2. Release-state wording is stale as of this run, and E.1 contradicts II.11.**

The phrases:
- `…PRIMER.md` L9883-9884: "#428 is queued for juniper-data 0.16.0, unreleased when this was written; 0.15.0, the latest on PyPI, sends none of the headers below."
- `…PRIMER.md` L5358: "juniper-data#428 has since shipped the fix".

Evidence:
- GitHub Release v0.16.0 was published at 2026-09-24T08:52:14Z. It tags `39d1cab2`, which contains `af7831be` (#428).
- The v0.16.0 container image run 35977785708 succeeded.
- The "Publish to PyPI" run 35977786108 is `waiting` (it was still waiting at 09:46:44Z), so PyPI still serves 0.15.0.
- The text was written in `855f39db` at 08:49:45Z, 2m29s before the Release.

What that means for each phrase:
- "Is queued … unreleased" now reads false for the Release.
- "The latest on PyPI" becomes false as soon as run 35977786108 is approved.
- "Has since shipped" was false by E.1's own standard when it was written.

**Fix:** use wording that doesn't age. L9883-9884: "#428 is in juniper-data 0.16.0 (tagged 2026-09-24); 0.15.0 sends none of the headers below." L5358: "juniper-data#428 (0.16.0) has since added the fix -- with a WEAK artifact tag,".

### LOW

**L1. `--check` can only verify the uncommitted state; on the PR branch or after merge it refuses.**
- The claim, in `util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py` L40-42: "v2 always rebuilds from ``git show HEAD:<primer>`` and PROVES the result". `ml_primer_v2_pr_body.md` says the same.
- It is not vacuous: with HEAD at the base it reports MATCHES, and my mutations report DIFFERS.
- But when HEAD already carries Appendix E, it exits with "REFUSED: HEAD's primer already carries Appendix E". A reviewer cannot re-run the proof from the committed branch. I could only do it by substituting `git show dcfc024f:`.
- "Every other line byte-identical" is true by construction; the MATCH comparison is what actually proves anything.
- **Fix:** add `--base <rev>` (default `HEAD`).

**L2. E.1 and E.2 cite register rows that main doesn't have.**
- `…PRIMER.md` L9915 "defect-register row `APD-DATA-054`" and L9952-9953 "(defect-register row `APD-DATA-055`)".
- There are 0 occurrences in `…DEFECT-REGISTER.md` at main `602094e3`. They exist only at #2074's head (L1294-1295), and #2074 is OPEN.
- `ml_primer_v2_pr_body.md` says "Land that first"; that hasn't happened.
- **Fix:** gate #2075 on #2074.

**L3. Appendix E claims to cover every affected passage, and it doesn't.**
- `…PRIMER.md` L9871-9872: "Each affected prose passage keeps its text and gains a **Corrected** link to its entry below."
- Unmarked and not named in E.1:
  - L594: "Caching benefits are claimed and not implemented (as in `juniper-data`)." #428 overtook this.
  - The L4213 heading: "ETag generation, and the fix already sitting in juniper-data".
  - L4220: "| Hash of serialized JSON | usually weak |". juniper-data's metadata ETag and the corrected toy are both strong hashes of serialized JSON. This and L4213 were LOW items in `…round1-laneB-refute.md` and remain unaddressed.
- Borderline:
  - L1954 is scoped to v0.11.0.
  - L3871 ("juniper-data declares no `responses={...}` anywhere") falls under L9870's scope. Main has declared `responses=` on four routes since #428.
- **Fix:** add a marker on L594 (it fits under 512), name L4213 and L4220 in E.1, and narrow L9870-9872.

### NIT
- **N1.** L9918-9919, "a generator's documented default seed is `DEFAULT_GENERATOR_SEED`", holds for 10 of 16 generators. 5 default to `0` and reject `seed=None`; spiral uses `SPIRAL_DEFAULT_SEED`. The conclusion is right. Suggested: "every generator's seed now has a fixed default".
- **N2.** L9951-9952, "and per host only: the Redis, Postgres and cached stores hold a per-process lock". The colon reads as an explanation, but those stores' lock is narrower than per host. Suggested: "per host at most (LocalFS's flock); … hold only a per-process lock".
- **N3.** The L3400 marker points to E.2, but that line's false premise ("juniper-data emits no cache headers at all") is corrected only in E.1 (L9926-9928).
- **N4.** L9937-9938 sends readers to `http_cache.py` as "the corrected reasoning". That docstring (lines 17-19) still quotes "Same content, possibly different bytes" as RFC 9110 §8.8.1's definition, and it lacks the cleanup qualifier. Those are the two errors round 1 removed from E.1; they belong to juniper-data's fix-forward.
- **N5 (out of scope, predates this PR).** The L3638-3642 example sends `{"tags": [...]}` as merge-patch to an id shaped `spiral-v1.0.0-…`. juniper-data actually takes `add_tags`/`remove_tags` and mints `spiral-3.0.0-…` ids. The new 16-hex tag at L3639 also doesn't look like juniper-data's 64-hex ETag.

## Round 1's findings, one by one ("v2 line" means `…PRIMER.md` at `b6129bf8`)

**`…round1-laneA-reprobe.md`**

| Finding | v2 status |
|---|---|
| F1: L3685, L5332 and L9510 unmarked | FIXED. Markers on L3685 and L9510; L5330 marked and L5332 named in E.1 (L9884-9886); docstring rewritten (L5352-5366) |
| F2: APD-DATA-054 only in an uncommitted edit | PENDING. Now in #2074, which is OPEN (L2) |
| F3: release status stated as fact | FIXED when written (L9883), stale now, and L5358 contradicts it (M2) |
| F4: markers on mostly-true paragraphs | FIXED. "What stands" (L9930-9935) |
| F5: move the L462 marker to L463 | FIXED (L463) |
| F6: paraphrase quoted as RFC text | FIXED. L9897-9899 is verbatim |
| F7: "is conditional on" overstates | FIXED in E.1 (L9908-9911) and E.2 (L9953); reintroduced at L5364 (M1) |
| F8: expiry qualifier | FIXED (L9920) |
| F9: lead with the observable mechanism | FIXED (L9894-9897) |

**`…round1-laneB-refute.md`**

| Finding | v2 status |
|---|---|
| Q37 (9509-9510) | FIXED (L9510) |
| II.11 motivation (5332) | FIXED (L5330 marker + E.1) |
| Docstring 5352-5366 | FIXED, but it now carries M1 and "shipped" (M2) |
| 5419-5422 / 5901 | FIXED by attributing immutability to deterministic synthesis. `public` is kept and justified by L5366 "unauthenticated", which is true of the toy |
| 3685 | FIXED |
| 3452-3453 | FIXED (L3453 + E.1 item 2) |
| 3426 / 3431 | FIXED, by naming them in E.1 |
| 463 | FIXED |
| 3399-3400 | FIXED (L3400 → E.2), with N3 |
| 4171-4279 and 5362 / 5785 tag passages | FIXED (markers on L4174, L4200, L4279; E.2), but the II.11 rewrites misattribute (M1) |
| 5537 metadata_etag | FIXED. Probes MATCH |
| 1563 / 1565 | FIXED (L1565) |
| 3639 | FIXED |
| 4213 / 4220 | NOT ADDRESSED (L3) |
| 4222 | FIXED |
| 1952 / 1954, 4314, 543, 594 (optional) | NOT ADDRESSED. L594 now contradicts L9871 (L3) |
| Dangling APD-DATA-054 | PENDING (L2) |
| `--check` vacuous | FIXED; now runs only before commit (L1) |
| Stale nonce wording | FIXED, with N1 |
| "Wrong on two counts" overreach | FIXED. Phrase removed; marker moved from 3650 to 3647 |
| "Ships in 0.16.0" | See M2 |
| "Is conditional on" | See M1 |
| Nothing points to Appendix E | FIXED (L5) |
| Markers after a colon (1960, 1974) | FIXED by inserting them mid-line |
| Expiry | FIXED |
| Anchor drift (9463 / 9592); register L340-343 | Out of scope. Both are fixed in #2074's `…DEFECT-REGISTER.md` (now 9466 / 9595, plus a re-ruling note), not by #2075 |

## What this evidence cannot support
- **Store coverage.** Redis and Postgres are covered from source only (no servers or fakes this round). The HF and Kaggle stores are known to delegate only from reading the code.
- **Generator coverage.** Only spiral and csv_import ran live. The equities wall-clock mechanism is from source.
- **Transport.** Everything ran in-process over ASGI, with no socket server, proxy or shared cache. Auth was off: I mounted the router without the security middleware. The numpy/zlib variation was not tested (NO ARTIFACT).
- **Release state is a snapshot** (09:21:33Z, re-checked 09:46:44Z). Approving run 35977786108 changes it.
- **Sweep limits.** The unmarked-passage sweep is keyword-driven (27 candidate paragraphs, reviewed by eye). The register-citation parser is my own (154/155 lines found). I checked no document other than `…DEFECT-REGISTER.md` for citations of `…PRIMER.md` line numbers.
- **The `--check` re-run substituted `git show HEAD:`** rather than using a real git HEAD. The worktree does hold exactly that state (primer sha256 `a2c0fe76…` and script `7b71f5dd…` match the PR head, and its HEAD is `dcfc024f`), but I left it untouched.
- **The 2026-09-23 ruling** is confirmed only by secondary records.
- **The concurrency probe** is one run of 12 requests per configuration on one host. The lock in the source is the proof; the run is a sample. The negative control shows the instrument can detect loss.
- **Python lint.** I did not run flake8 or bandit on the two scripts. The flake8 hook only covers `scripts/` and `tests/` anyway.

## Scripts (all in `…/scratchpad/r42/primer-r2-laneA/`)
- `line_invariance.py` (with a self-test), producing `line_invariance.json`.
- `buildcheck_runner.py`: re-runs `--check` plus the four mutations.
- `run_toy_probe_matrix.py`: runs the PR's toy probe over 3 toolchains × {head, base}.
- `probe_toy_all_routes.py`: my own check of every ETag-bearing toy response.
- `probe_jd_http.py`, producing `probe_jd_http.json`.
- `probe_seed_census.py`, producing `probe_seed_census.json`.
- `probe_recreate_same_uri.py`.
- `probe_concurrent_tag_patches.py` and `probe_concurrent_tag_patches_0_15_0.py`.
- `wheel_header_census.py` and `probe_wheel_0_15_0_headers.py`.
- `rfc_quote_check.py`, which reads `rfc9110.txt` (sha256 `21c1cdce…`).
- `link_check.py`.
- `register_cites_vs_changes.py`.
- `sweep_unmarked.py`, producing `sweep_unmarked.out`.
- `show_lines.py` and `env_check.py`.
- Extracted inputs: `primer_{base,head,855f}.md`, `pr_{build_script,toy_probe,harness}.py`, `register_{main_602094e3,pr2074_6a9af70c}.md`, `jd_main_1afc3484/`, `pypi/`, `doctools/`, `venv_pinned/`, and `tmp_harness/` (the kept example trees and the latest venv).

**Hygiene.**
- Nothing in any repository was written. No commits, pushes, comments or refs, apart from `git fetch origin` in juniper-ml and juniper-data.
- Outbound traffic was limited to read-only `gh`, PyPI (JSON, simple index, and files, including pip installs into two scratch venvs) and rfc-editor.org.
- `get_secret` was stubbed in every juniper-data probe, and no environment variable or secret was printed.
- No servers were started.
- Other sessions added files to the worktree during this run (`ml2074-round1-*` reports and three `util/ad-hoc/2026-09-24_register_*` scripts); none are mine.
