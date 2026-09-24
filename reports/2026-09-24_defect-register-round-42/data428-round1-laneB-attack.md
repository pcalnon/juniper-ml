<!-- Archived verbatim 2026-09-24 from subagent a58faf1967ffc6372 of session bc31e993 (final message). -->

**Scope.** Every `juniper_data/…`, `docs/…` and `CHANGELOG.md` path below is juniper-data at the PR head `760a957`. The juniper-ml documents are named by filename. I ran everything in scratch copies made with `git archive`. **Changed: nothing** in any repository.

## Defects, by severity

**1. HIGH (tracking; silent lost update). Closing APD-DATA-017 on this PR would close the row's own worked example without implementing it.**
- **Quoted:**
  - `routes/datasets.py:1147-1149`: "conditional writes are not part of this change", then `return _metadata_response(meta, None)`.
  - `docs/api/JUNIPER_DATA_API.md:1018-1019`: "carries its **new** `ETag`, so a client can hold the edited copy … `If-None-Match` is not evaluated here." `If-Match` is not mentioned at all.
  - The PR body says the register closes "land separately … after this merges".
- **Evidence:**
  - In `…DEFECT-REGISTER.md` (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`), row `APD-DATA-017` at :782 anchors line 3647 of `…API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`. That line sits inside "Conditional requests: making an unsafe operation safe to retry" (:3633). Its example (:3637-3645) is `PATCH /v1/datasets/…/tags` with `If-Match`, answered 412.
  - Searching `…DEFECT-REGISTER.md` for `If-Match` or `412` finds no other row that tracks conditional writes.
  - On `760a957`, a PATCH with a stale `If-Match` returned 200 and applied the tags.
- **Why it matters:** the PR now advertises an ETag on PATCH, which invites exactly this pattern.
- **Fix:**
  - Partially close APD-DATA-017 (reads only) and file a residual row for `If-Match` / `If-None-Match` on PATCH and DELETE.
  - Until that lands, document that `If-Match` is ignored.
  - **Heads-up:** the shared PR worktree now holds an uncommitted revision (`update_tags(precondition=…)`, `PreconditionFailedError` → 412) that edits `storage/base.py`. If it lands:
    - the close can be full;
    - the PR body's "no store changes (this does not collide with D-F)" becomes false;
    - the `base.py` conflict that `HANDOFF_2026-09-15_…arc-sequenced.md` §0.1 (:139-143) predicted comes back.

**2. MEDIUM. The artifact validator rests on a premise the PR disproved, the PR settled that itself, and it points the follow-up at the wrong row.**
- **Quoted:**
  - `juniper_data/api/http_cache.py:18-21`: "strong for everything this route does … storage work (APD-DATA-019's territory)".
  - The PR body: "`APD-DATA-019` storage work".
- **The premise:** the ruling followed `…API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` :3647 and :4227-4232, which say `checksum` is "a SHA-256 over the serialised NPZ bytes", calling it "the textbook strong-validator case". The PR measured `sha256(served) != checksum`.
- **Why it is a problem:**
  - RFC 9110 §8.8.1 defines "strong" without a "for what this route does" qualifier.
  - The same primer's judgement call (:4285) is "Prefer an honest `W/` to a dishonest strong tag."
  - A false premise found after a ruling goes back to the owner. `…DEFECT-REGISTER.md` §2.4 requires rulings to be taken "against evidence re-derived that day".
- **Wrong row:** `APD-DATA-019` (`…DEFECT-REGISTER.md` :784) is the `/filter` full-population pushdown row (D-F), not an artifact digest. D-F will close it without doing this, so the residual becomes untracked.
- **Runtime exposure is low:** the service only wires LocalFS (`api/app.py:42`), whose artifact files are written once.
- **Fix:**
  - Put the choice to the owner: strong with a caveat, `W/"<checksum>"`, or a stored byte digest.
  - File a real row for it.
  - Correct both pointers (`http_cache.py` and the PR body).

**3. MEDIUM. `private, no-cache` is right, but not for the stated reason, and the ruling's source document prescribes the opposite three times.**
- **Quoted:**
  - `docs/REFERENCE.md:1267`: "`no-cache` because a dataset can be deleted or re-tagged at any time".
  - Same wording in `http_cache.py:27-29`.
- **Why the stated reason fails:**
  - Tags are not part of the artifact.
  - `…API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` prescribes `private, max-age=31536000, immutable` for the artifact at :1980, :4239 and :9510, on the grounds that artifacts are content-addressed.
- **Why artifacts are not content-addressed:**
  - `core/dataset_id.py` hashes the request (generator, version, params), not the content.
  - `equities` defaults `end_date` to `None`, meaning today (`generators/equities/defaults.py:18`). `params.py:137` says "the same params yield different data on different days", and the seed is non-None, so the id stays the same.
  - So deleting or expiring a dataset and recreating it serves different arrays at the same URL. `no-cache` plus the checksum ETag is what keeps that safe; `immutable` would serve stale equities data for a year.
- **Risk:** a successor following the primer will "fix" this header.
- **Fix:** record the real reason, record that the primer's `immutable` prescription is rejected, and correct the primer.

**4. MEDIUM-LOW. The published OpenAPI changes are undisclosed, and the new headers are undeclared.**
- **Evidence** (`app.openapi()` on main vs `760a957`):
  - The schema components change from `['DatasetMeta']` to `['DatasetAccessStats','PublicDatasetMeta']`.
  - No 200 or 304 response on the three reads or on PATCH declares `ETag`, `Cache-Control` or `Content-Location` headers.
- **Quoted:** `CHANGELOG.md:80`: "The wire format is otherwise byte-identical".
- **Why it matters:** renaming a component renames the generated SDK model. That is the same class of break `APD-DATA-023` (operationIds pinned via `PUBLISHED_OPERATION_IDS`) guarded against. Impact is latent: no generated SDK exists in any of the nine repos.
- **Fix:** add a CHANGELOG line, and declare the headers in `responses`.

**5. LOW-MEDIUM. The PATCH ETag the ruling didn't ask for is attached to the wrong resource.**
- **Code:** `routes/datasets.py:1149` sends no `Content-Location`.
- **Why:**
  - The request target is `/v1/datasets/{id}/tags`, which has no GET.
  - Under RFC 9110 §8.8, validators on a state-changing response describe the target's new representation.
  - RFC 5789 §2.1's own example pairs the ETag with `Content-Location`.
- **Fix:** `content_location=_canonical_path(dataset_id)`. The helper already exists for `/latest`, which is the same two-URIs-one-representation case as `APD-DATA-029`.

**6. LOW-MEDIUM. Blind spots in the tests and the non-vacuity harness.**
- **Artifact-304 access recording is unpinned:** I removed the `record_access` call (`routes/datasets.py:1023`) and all 23 tests stayed green.
- **"A revalidation costs no artifact I/O" is only half-pinned:** reading the whole artifact via `get_artifact_bytes` before the 304 also stayed green. The test only counts `open_artifact_stream`.
- **The embed test can go empty silently:** `test_no_representation_that_embeds_metadata_carries_a_counter` never asserts that `listed` or `versions` is non-empty. D-D is about to rework exactly those list routes; today each holds one row.
- **One test pins the mechanism, not the behaviour:** `test_etag_is_strong_and_is_the_hash_of_the_exact_body` asserts `etag == sha256(body)`. A stored-digest design, the natural one for If-Match compare-and-swap, would fail it while behaving correctly.
- **The harness:** its PASS reproduced (12/12 caught, controls green, files restored per sha256). But it mutates the checkout in place with no clean-tree precondition. Right now a harness run (pid 929882) is live in the shared PR worktree, alongside uncommitted edits to `http_cache.py`, `routes/datasets.py`, `storage/base.py` and the test file. Consequences:
  - any lane reading that worktree may be reading mutated source;
  - any edit saved to a file while it is mutated gets reverted by `restore()`, which "verifies" only against its own snapshot.
- **Fix:** mutate a copy, not the checkout.

**7. LOW. A 304 is not cheap on the server, and access counting is applied inconsistently.**
- **Measured on LocalFS** (the only wired store): one 304 on `/{id}` or on `/artifact` rewrote the whole `.meta.json` and set `_metadata_cache` to None. Any later `/filter`, `/versions`, `/latest` or `/stats` then pays the full O(N) walk that APD-DATA-019 is about. The write runs on the event-loop thread via `call_soon`.
- **Not a new amplification:** the old 200s cost the same number of writes. But `http_cache.py:29` says "the 304 is what makes that cheap", and D-F must know every revalidation is a whole-document write.
- **Inconsistent counting:**
  - `/latest` recorded 0 accesses over a 200 plus a 304.
  - Yet `docs/api/JUNIPER_DATA_API.md:519` promises `/latest` "the same … If-None-Match handling" as `/{id}`, and :897 says there that "A 304 still counts as an access".
  - `CHANGELOG.md:75` ("maintained on every metadata read and artifact download") is false for `/latest`, `/filter`, `/versions`, `/preview` and `/batch-export`.

**8. LOW. `Content-Location` is oversold, and cross-origin JavaScript cannot read it.**
- **Quoted:**
  - `docs/api/JUNIPER_DATA_API.md:522`: "how a client or cache knows they are one resource".
  - `routes/datasets.py:897-898` makes the same claim.
- **Contradicting sources:**
  - `…API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` :3399-3400 says setting it "would not have merged anything", because the cache key is the target URI (RFC 9111 §2).
  - RFC 9110 §8.7 says such an assertion "cannot be trusted".
- **CORS:** the `CORSMiddleware` in `api/app.py` sets no `expose_headers`. With CORS enabled, browser JavaScript cannot read `ETag` or `Content-Location`.

**9. LOW. Documentation drift.**
- `/access` is missing from three endpoint tables: `docs/REFERENCE.md` (~:46-68), `docs/DEVELOPER_CHEATSHEET.md` (~:40-58) and `docs/USER_MANUAL.md` (~:238-256).
- The example timestamp `…08.114Z` (`JUNIPER_DATA_API.md:919`) doesn't match what the service emits, e.g. `…01.521749Z`.
- The `/access` handler (`routes/datasets.py:977`) uses the exact render form that `docs/REFERENCE.md:1281` forbids. It is harmless for these field types.

## Things a successor must know
- HF and Kaggle stores build metadata with no `checksum`, so their datasets never get an artifact ETag. Neither store is wired today.
- Expired datasets are still answered 200 or 304, indefinitely. Cleanup is manual only, while `/filter` hides expired datasets by default.
- No Juniper client sends `If-None-Match`, so only the tests exercise the 304 paths.
- **D-C:** the register's note that "the only textual match for `responses=`" is a comment is now stale.
- **D-E:** PATCH now returns a pre-rendered `Response`. Idempotency replay must preserve its headers, and any `If-Match` check must run after the replay lookup.
- The required Sequence Safety check is failing, so the PR is blocked (per the re-probe lane).
- main has moved to `ce43681` (#422): `CHANGELOG.md`'s `[Unreleased]` now has `### Removed`, so the PR needs a rebase.
- `HEAD` returns 405 on these routes (pre-existing).

## Attacks that did not land
- **Metadata ETag not literally "derived from the stored SHA-256":** a checksum-based tag would not change on a tag edit and would give stale 304s. Hashing the body is the reading that works. Only the PR summary's framing is loose.
- **`/access` as scope creep:** the primer itself offers that option at :4251 ("split them into a sub-resource"), and the ruling says nothing about where the counters go.
- **`PrerenderedJSONResponse`:** needed so the exact hashed bytes are sent.
- **The `PublicDatasetMeta` split:** field order is identical between main and the PR (verified). Postgres columns and Python imports are unaffected, and `760a957` has no store edits.
- **`private`:** correct under RFC 9111 §3.5, because `X-API-Key` is not `Authorization`.
- **`no-cache` too conservative, or TTL datasets needing `Expires`/`max-age`:** neither holds (see #3); `Expires` means nothing next to `no-cache`.
- **Per-route `responses={304}` vs `APD-DATA-022`:** it follows the ruling's "only route-specific codes inline".
- **Pre-empting D-D:** `_metadata_response` makes `/named/{name}/latest` trivial; nothing is pre-empted.
- **Remote-store performance:** only LocalFS is wired.
- **Consumer breakage:**
  - Zero references to the counters in the 7 consumer repos (origin/main).
  - No OpenAPI snapshot or generated SDK anywhere in the ecosystem.
  - The deploy, cascor and canopy tests read neither the counters nor the new headers.
- **Render drift:** the byte-equality test passes on FastAPI 0.137 and would catch drift under the lock's 0.141.1.
- **Multi-worker staleness on `/latest`:** the service runs as a single process.

**What I ran:** the new tests (23 pass), the harness (PASS), two extra mutations (both uncaught), OpenAPI dumps of main vs the PR, LocalFS probes, and cross-repo greps. All ran in scratch copies of `760a957`.
