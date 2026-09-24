<!-- Archived verbatim 2026-09-24 from subagent a62472b6345e59993 of session bc31e993 (final message). -->

PR #428 should not merge yet. I found one HIGH, two MEDIUM, five LOW and several NIT issues at head `3ecb106ca4c5b1db5a0964a6da7da4fd62dac4a0`.

The PR's own claims reproduce against a copy extracted from that SHA:
- **Unit suite:** 1821 passed, which is main's 1781 plus the 40 new tests.
- **Test file:** `test_conditional_requests.py` has 40 tests, as claimed.
- **Harness:** `PASS: 22 mutations`, with 36 caught lines and no vacuous or over-broad results. I ran it with TMPDIR set to my scratch directory.

Nothing shared was written. All probes are under `…/scratchpad/v428r2/probes/`.

## Findings

**1. HIGH — `juniper_data/api/http_cache.py:70`: the entity-tag list regex backtracks exponentially, so one short header freezes the whole service.**
- **Cause:** `_ENTITY_TAG_LIST` has two `[ \t]*` quantifiers either side of an optional element, so the regex can split the same whitespace many ways. `fullmatch` at `:120` runs on any caller-supplied `If-Match` or `If-None-Match` whenever an ETag exists.
- **Timing, in process:** `", " * k + "x"` took 0.44 ms at k=10, 103 ms at k=18 and 1829 ms at k=22 (a 45-byte header). Each extra `", "` doubles the time, so about 60 bytes costs minutes and about 80 bytes costs days. `" " * 8000 + "x"` takes 1.44 s (quadratic).
- **Live uvicorn, against this head:** with a 45-byte `If-None-Match` on `GET /v1/datasets/{id}`, a concurrent `/v1/health` took 1.67 s instead of 12 ms. It runs on the event loop inside `_metadata_response` (`datasets.py:146`).
- **The PATCH path is no better:** a `PATCH .../tags` with a 45-byte `If-Match` stalled `/v1/health` for 1.49 s. It runs in a worker thread, but the regex holds the GIL. It also holds `DatasetStore._version_lock`, a class attribute shared by every store (`base.py:102`). Every GET's `record_access` is scheduled onto the event loop with `call_soon`, and it would then block on that lock even on a build without a GIL.
- **Fix, validated:**
  - Replace the pattern with `r'[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?(?:,[ \t]*(?:(?:W/)?"[^"]*"[ \t]*)?)*'`.
  - It accepts exactly the same strings: 797,871 inputs checked (exhaustive to length 6, plus 200k random), zero mismatches.
  - It is linear: a 10 KB hostile input takes about 3 ms.
  - All 40 existing tests still pass with it.
  - Add a length cap on the field, and the regression test `probes/test_proposed_redos.py`. It fails 3 of 4 cases on the current head and passes on the fix.

**2. MEDIUM — the "check inside the lock" guarantee is tested by nothing** (`storage/base.py:366`, `datasets.py:1222`).
- I wrote two mutations of my own. Both pass the entire unit suite (1821 passed each):
  - N1: `update_tags` evaluates the precondition before taking `_version_lock`.
  - N2: the route evaluates the precondition itself and passes `None` to the store.
- The harness's M13 only deletes the check outright. The PR itself names `update_tags` as the D-F merge point, which is exactly where a conflict resolution could reorder the check without any test noticing.
- **Fix:** add the two tests in `probes/test_proposed_atomicity.py`. They pass on the head; one asserts the lock is held when the precondition runs (catches N1), the other simulates a writer winning the race (catches N2).

**3. MEDIUM — `datasets.py:1058-1063`: the artifact fallback logs the caller-controlled id, contrary to its own comment.**
- The comment says "Logged without the dataset id". But `exc_info=True` puts the exception's text in the record.
- **Evidence:** on the local-filesystem store, `GET /v1/datasets/CALLER$CONTROLLED/artifact` returns 400. It also leaves a WARNING whose traceback ends `ValueError: Invalid dataset_id: 'CALLER$CONTROLLED'`. The same request on main logs only at DEBUG.
- So any caller can now create WARNING tracebacks at request rate, and a caller's 400 is reported as "metadata unreadable". Errors aren't hidden: the later artifact open fails as well.
- **Fix:** log `type(exc).__name__` without `exc_info` (the traceback is at most DEBUG). Consider not entering the fallback for id-validation failures.

**4. LOW — `datasets.py:1035`: the `download_artifact` docstring says "carries a strong ETag".** It is published as the OpenAPI operation description; I confirmed that with `app.openapi()`. It contradicts the weak ruling and the route's own 200-header description. The same stale wording is in the test class docstring at `test_conditional_requests.py:231`.

**5. LOW — a PATCH whose `If-None-Match` is a tag naming the current representation is untested.** Only `*` is tested (`:395`). My mutation N3, which honours only `*`, passes all 1821 tests. The real behaviour is correct: my matrix gives 412 with nothing written.

**6. LOW — an orphaned artifact ignores a failing `If-Match` (`datasets.py:1077`).**
- On the local-filesystem store, with the metadata deleted and the NPZ still present, `If-Match: "definitely-not-current"` returns 200 and the body.
- RFC 9110 §13.1.1 says an origin server "MUST NOT perform the requested method if a received If-Match condition evaluates to false". The PR documents the orphan case for `*`, but not for a failing `If-Match`.
- **Fix:** when preconditions are present and `exists()` is false but the stream opens, evaluate them with `etag=None`.

**7. LOW (follow-up, out of stated scope) — `DELETE /v1/datasets/{id}` (`:1157`) and `/batch-tags` ignore `If-Match`.** A DELETE with a stale `If-Match` returns 204 and the dataset is gone, on the very resource that now carries a strong ETag. Either record this or document that `PATCH .../tags` is the only write that honours preconditions.

**8. LOW — `docs/api/JUNIPER_DATA_API.md:73-74`: the deprecation policy is not scoped to 1.0.** It still says features are "announced at least 2 minor versions in advance". Items 3 and 5 were amended for 0.x, but this release removes fields with no notice period. Scope item 4 the same way.

**9. NIT — `docs/REFERENCE.md:1333-1334` says "twenty mutations".** The harness, CHANGELOG and PR description all say 22.

**10. NIT — a malformed `If-None-Match` on PATCH is ignored and the write goes ahead (`http_cache.py:140/:173`).** The module's reason for failing a malformed `If-Match` — that proceeding is "the unsafe direction" (`:147`) — applies equally to a write's `If-None-Match`.

**11. NIT — two behaviours are unasserted:**
- the `Cache-Control` header on the artifact 304 (my mutant N4 survives);
- "a 412 on the artifact route is not an access" (N6 survives).

My control mutant N5, which swaps the evaluation order, is caught.

**12. NIT — `CHANGELOG.md:81`: "An unreadable metadata document no longer fails an artifact download" describes a regression that never shipped.** The 0.15.0 artifact route never read the metadata, so users will read this as a fix to something they had.

**13. NIT — the optimistic-concurrency guarantee is per host.** The Redis and Postgres stores inherit the no-op cross-process lock. The service only wires the local-filesystem store today, but the docs state the guarantee without that qualification.

## Attacks that did not land
- **Header grammar:** 18 edge inputs behave correctly. These include `W/abc`, an unterminated quote, `w/"abc"`, a missing comma, `*` mixed with tags, leading, trailing and empty elements, tab whitespace, and a comma inside quotes. Malformed fields make If-None-Match name nothing and make If-Match fail. The opaque part accepts spaces and control characters, which is harmless.
- **Conditional PATCH:** 16 of 16 header combinations gave the right result on both the in-memory and local-filesystem stores, and nothing was written on any 412.
- **Missing datasets (§13.2.1):** a missing id with `If-Match: *` or `If-None-Match: *` gets 404 on `GET /{id}`, `/artifact`, `/latest` and PATCH.
- **304 contents (§15.4.5):** each 304 carries ETag and Cache-Control, and `/latest` also carries Content-Location. There is no body and no Content-Type.
- **Metadata ETag:** it equals `sha256` of the bytes sent. Those bytes are identical to FastAPI's own `response_model` rendering for `1e-07`, `1e22`, `-0.0`, `5e-324`, `2**63`, NaN, inf, U+2028, emoji, nested dicts, and datetimes with microseconds or without a timezone, on both stores. On the local-filesystem store the PATCH ETag equals the next GET's.
- **Store coverage:** `update_tags` is defined only in `base.py`. All seven store subclasses inherit it, and the check runs under both locks.
- **Counters:**
  - no response model embeds the stored model;
  - there is no `SerializeAsAny` and no `model_dump` into a response;
  - batch, export and stats responses carry no metadata;
  - the OpenAPI `PublicDatasetMeta` schema has no counter property;
  - Pydantic emits no serialization warnings;
  - `/access` records no access and its operation id is pinned.
- **Consumer census:** across the eight sibling repos, only a juniper-ml ad-hoc register script mentions the counters, and it is not a consumer.
- **Docs and branch state:**
  - HEAD returns 405, as `REFERENCE.md` says;
  - the store-by-store claims about key sorting check out;
  - the CHANGELOG `[Unreleased]` headings are Added, Changed, Removed, Fixed, and the diff from main deletes only the three lines of the duplicate `[0.15.0]` heading, so no entry was lost;
  - the `Allow-Symbol-Loss` trailer is on commit `975e501`;
  - CI is green and auto-merge is not armed.
