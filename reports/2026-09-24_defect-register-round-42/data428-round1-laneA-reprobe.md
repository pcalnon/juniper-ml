<!-- Archived verbatim 2026-09-24 from subagent acbd22465744eb9e5 of session bc31e993 (final message). -->

## Claim verdicts

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1a | `sha256(served bytes) != meta.checksum` for the stores | VERIFIED | InMemory served `9fbe56…`, LocalFS `3588db…`, checksum `8405dc…`. Redis and Postgres serve `savez_compressed` (`redis_store.py:107`, `postgres_store.py:392`). |
| 1b | `compute_checksum` is deterministic | VERIFIED (small wording error) | Same digest after a 2 s sleep and a TZ change. The zip entries are dated `(1980,1,1,0,0,0)`, but that is CPython `zipfile.ZipInfo`'s default. numpy passes a bare name to `ZipFile.open(name,"w")`; it pins nothing itself. |
| 1c | The checksum changes whenever the arrays change | VERIFIED | Changing one element moves it. Changing key order does not. |
| 1d | The artifact ETag is a STRONG validator (RFC 9110 §8.8.1) and "a stored artifact's bytes never change while it exists" | REFUTED in general; holds only for the one wired store (LocalFS, `api/app.py:42`) | `CachedDatasetStore(LocalFS, InMemoryDatasetStore())` serves ETag `"8405dca0…"` with two different byte sequences in one process (details under defect 5). HF and Kaggle set no checksum, so they send no ETag. Re-creation after delete or expiry keeps the same bytes unless numpy or zlib changes in between (the PR concedes this; not reproduced). |
| 2 | The self-rendered body is byte-identical to FastAPI `response_model=PublicDatasetMeta` | VERIFIED | FastAPI 0.137.0 `routing.py:701-722` validates with `validate_python(from_attributes=True)`, which passes the subclass through, then calls `dump_json` (`_compat/v2.py:231`). 21 of 21 serializable cases matched byte for byte: 1e-7, 1e22, 5e-324, -0.0, NaN/±inf→null, 2**70, non-ASCII including U+2028/NUL, naive/offset/µs datetimes, datetime/date/Decimal/UUID/bytes/set/tuple/np.float64 in `params`. `np.int64` and `np.float32` fail the same way (500) in both paths. Repeated on the lock/CI stack (FastAPI 0.141.1, pydantic 2.13.5, starlette 1.6.0) with the same result. |
| 3 | No metadata-embedding response carries the counters | VERIFIED | 26 requests covering every route in `routes/*.py`: POST new / cache-hit / persist=false, /filter, /stats, /versions, /latest, /{id}, /artifact, /preview, PATCH tags, batch-create, batch-tags, batch-delete, batch-export (ZIP members inspected), cleanup, generators, health. Only `/access` carries them. The `DatasetMeta` OpenAPI component is gone. No warnings under `-W error`. |
| 4 | No store changed; counters still persist and round-trip | VERIFIED | Nothing under `storage/` changed. `DatasetMeta.model_fields` order and every Postgres-derived constant (`_column_specs`, `_SQL_DEFAULTS`, …) are identical between base and PR. `record_access` round-trips on InMemory, LocalFS and Cached. Store suites: 226 passed. |
| 5 | RFC 9110 correctness of the 304 path | PARTLY REFUTED | 304 shape is right over a real uvicorn socket: ETag, Cache-Control, Content-Location on `/latest`, Date, `Vary: Origin` under CORS, no body or length. `/latest` returns 200 with v2 after a newer version is created. Weak comparison, lists and a comma inside a tag are handled correctly. Failures are defects 2, 4, 6, 7 and 8 below. HEAD returns 405 on all three routes, before and after the PR. |
| 6 | Consumer census finds no readers | VERIFIED | No code reads `access_count` or `last_accessed_at` in the other 8 repos (only juniper-ml notes and prompts mention them). Nothing consumes the OpenAPI schema by component name (no `components/schemas/DatasetMeta` references, no code generator or schemathesis). No consumer sends `If-None-Match` or checks checksums. In-flight worktrees only match juniper-data branches. |
| 7 | Tests | VERIFIED | New file 23/23. Full unit suite 1757 passed vs base 1734 (+23). `api/` + `integration/` 118 passed. CI ran the new file on 0.141.1. My hand mutations (below) failed the expected tests. The PR's mutation script, run in a scratch copy, PASSED 12/12 and restored the tree. |
| 8 | Docs are accurate | PARTLY REFUTED | `application/zip`, status codes and anchors are correct, and the CHANGELOG heading merge is clean. Several claims are wrong; see defects 5, 6 and 8–10. |
| 9 | CI | REFUTED ("all green") | **`Sequence Safety` FAILS and is a required check** (mergeable_state=blocked). 24 checks pass; Slow Tests, Publish manifest and 5 Cursor automations are skipped; none pending. |

Hand mutations, run in a scratch copy:
- **A** (counters declared on `PublicDatasetMeta` again, i.e. the pre-PR representation): `test_metadata_etag_survives_recorded_accesses`, `test_body_carries_no_access_counter` and `test_no_representation_that_embeds_metadata_carries_a_counter` all went red; the control stayed green.
- **B / C** (`SerializeAsAny` on `CreateDatasetResponse.meta` / on `versions`): the embed test went red.
- **D** (artifact route with no validator): `test_etag_is_the_stored_checksum` and the artifact 304 test went red.

## Defects, most severe first

1. **HIGH – a required CI check fails, which blocks the merge.** The job log says `[FAIL/WEAKENED] juniper_data/core/models.py :: class:DatasetMeta {'base_lines': 99, 'head_lines': 11, 'ratio': 0.11}`. None of the three commits has an `Allow-Symbol-Loss` trailer, and the PR's Testing section never mentions the failure.
   - Evidence: job 107015404206; the main ruleset's required contexts include `Sequence Safety`.
   - Fix: add a signed commit whose final paragraph is `Allow-Symbol-Loss: DatasetMeta` (`_waives` accepts `DatasetMeta` or `class:DatasetMeta`), and make sure the trailer is in the squash body that reaches main. Alternatively the owner can apply the `allow-symbol-loss` label, which downgrades it to a warning.

2. **MEDIUM – `If-Match` is never evaluated.** This breaks RFC 9110 §13.1.1 ("MUST evaluate … MUST NOT perform the requested method if the condition evaluates to false") and step 1 of the §13.2.2 order.
   - Measured: GET with `If-Match:"wrong"` returns 200; add a matching `If-None-Match` and it returns 304 (RFC: 412).
   - `PATCH /tags` with `If-Match:"stale"` returns 200 and applies the tag. `PATCH` with `If-None-Match:*` is also applied.
   - This was always missing, but the PR now hands out strong ETags and documents that PATCH returns the new one, which invites clients to try optimistic concurrency. The docs mention only `If-None-Match` as unevaluated.
   - Fix: evaluate `If-Match` (strong comparison, return 412) before `If-None-Match` on all four routes, or at least document that it is ignored.

3. **LOW (new regression) – the artifact route now depends on the metadata being readable.** The route now reads metadata before opening the artifact. With truncated `.meta.json`, the base serves the artifact (200); the PR returns 400, which also blames the client for server-side corruption.
   - Fix: catch metadata read failures in `download_artifact` and fall back to no ETag.

4. **LOW – a 304 is sent where the unconditional answer is 404.** The code comment says "the 404 below still keys off the artifact", but the 304 is decided first (`datasets.py:1017-1024` runs before the existence check at `:1039-1041`). With metadata present and the `.npz` deleted, the route returns 404 without `If-None-Match` but 304 with a matching tag or `*`. RFC 9110 §13.2.1 says the server "MUST ignore all received preconditions if its response … without those conditions … would have been [non-2xx]".
   - Fix: open the stream (or call `exists`) before the 304, or stat the artifact without reading it.

5. **LOW (latent) – the same strong ETag is sent with different bytes, and the docs over-claim.**
   - Claims: `http_cache.py:14-15` "`sha256(served bytes) != checksum` for every store … a stored artifact's bytes never change while it exists: stores write it once"; `docs/REFERENCE.md:1273` and `docs/api/JUNIPER_DATA_API.md:947` say the same.
   - Cause: `InMemoryDatasetStore` re-serializes with sorted keys (`memory.py:70-71`), while LocalFS, Redis and Postgres keep the generator's key order (`local_fs.py:211`). `CachedDatasetStore` serves a cache hit from the cache store and a miss from the primary, then re-populates the cache from `np.load` (`cached.py:118-142`).
   - Measured: a cache hit returned sha `9fbe56…` (members in sorted order); after a restart the miss returned `3588db…` (generator order); both carried ETag `"8405dca0…"`. A client holding the hit bytes got a 304 from the process serving the miss bytes. That breaks §8.8.1's "changes value whenever a change occurs to the representation data".
   - The module comment in `cached.py` names InMemory as an expected cache backend.
   - Fix: pick one key order in every store, or cache raw bytes in `CachedDatasetStore`; otherwise limit the docs to LocalFS/Redis/Postgres.

6. **LOW – `If-None-Match: *` on an artifact with no checksum returns 200.** §13.1.2 says `*` is false (so 304) whenever a current representation exists. `test_conditional_requests.py:240-245` pins the 200, yet `docs/REFERENCE.md:1267-1268` claims the route "follows RFC 9110 §13.1.2 — `*`".
   - Fix: evaluate `*` from existence alone, or document the exception.

7. **LOW – `If-None-Match` split across two header lines is not combined.** The parameter is `str | None = Header(...)`, so only the first line is read. `"zzz"` on one line and the current tag on a second gets 200, while the same list on one line gets 304. RFC 9110 §5.2/§5.3 treats the two as the same list. This errs toward a full 200, so it is safe.
   - Fix: declare the header as `list[str] | None` and join the values with `", "`.

8. **NIT – "An absent, empty or unparseable field matches nothing"** (`http_cache.py:83`, `docs/REFERENCE.md:1268`) is false. The scanner finds quoted tags anywhere in the field, so `foo"<etag>"bar` and `x, "<etag>"` both return 304. `test_unparseable_field_serves_the_full_body` (line 108) only tries `abc`.
   - Fix: check the whole field against the `#entity-tag` grammar before scanning, or reword the docstring.

9. **NIT – docs.**
   - `/latest` claims "the same … `If-None-Match` handling" (`JUNIPER_DATA_API.md:519`), but its 304 is not recorded as an access, unlike `/{id}` (`:897`).
   - "maintained on every metadata read" (`JUNIPER_DATA_API.md:910`, `CHANGELOG.md:75`, `models.py:136`) is not true: `/latest`, `/filter` and `/versions` never record an access.
   - The `/access` example timestamp `".114Z"` (`JUNIPER_DATA_API.md:919`) is not something pydantic emits; it writes `.114000Z`.

10. **NIT – test gaps.**
    - No test covers recording an access on an artifact 304. The behaviour works; I checked it by hand. The PR script's M10 covers only the metadata route.
    - `test_etag_is_strong_and_is_the_hash_of_the_exact_body` stays green when the sent bytes are re-rendered through `JSONResponse` after hashing, because the spiral fixture renders the same under both encoders. `test_bytes_match_fastapi_rendering_of_the_public_model` does catch it.

Outside this PR's scope:
- HEAD returns 405 on all three routes, before and after the PR (RFC 9110 §9.1 requires HEAD support).
- The PR's argument for `private` applies equally to `/preview` (which returns data rows), `/filter`, `/versions` and `/stats`, and those still send no `Cache-Control`.

## Attacks that did not land

- Encoder differences on awkward values, and subclass serialization warnings: none on either FastAPI stack.
- Counters leaking through any route, including the batch-export ZIP, a cache-hit POST and `persist=false`: none.
- Postgres column drift: none.
- Metadata ETag churn on LocalFS after `record_access`: none. The PATCH ETag equals the next GET's ETag, and `/latest`'s equals the canonical route's.
- `/latest` after a newer version returns 200 with v2; after v2 is deleted it correctly returns 304 for v1. The 5 s cross-process metadata-cache staleness is pre-existing and not reachable, since `__main__.py` runs one uvicorn worker.
- `Range` and `If-Range` are ignored and a full 200 is served, so no byte splicing is possible.
- HF and Kaggle stores have no checksum, so no ETag is emitted.
- Unseeded requests get a per-call nonce in the dataset id (`core/dataset_id.py`), so there is no same-id / different-arrays race.
- The 304 shape over real HTTP is complete.
- No operation-id parity consumer exists.
- The CHANGELOG `[0.15.0]` merge is clean and the #426 entry is carried over unchanged.
- The PR worktree was confirmed untouched: its status is unchanged and no file is newer than the start of validation.

**Changed**: nothing in any repository. Scratch-only files: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428/scripts/*.py|*.sh`, plus the logs `unit_full_pr.log`, `unit_full_base.log`, `adhoc_run.log` and `census.log` in `…/scratchpad/v428/`.

**Key paths**:
- `/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--conditional-requests-etag--20260922-2024--68c3cd7c/juniper_data/api/http_cache.py`
- `…/juniper_data/api/routes/datasets.py`
- `…/juniper_data/storage/cached.py`
- `…/juniper_data/storage/memory.py`
- `…/juniper_data/tests/unit/test_conditional_requests.py`
- `…/docs/REFERENCE.md`
- `…/docs/api/JUNIPER_DATA_API.md`
- `…/CHANGELOG.md`

The worktree content is byte-identical to PR head `760a957`.
