<!-- Archived verbatim 2026-09-24 from subagent ac62fc5b8fc7652f2 of session bc31e993 (final message). -->

No open PR touches these files either. Here is the report.

# cascor#678 validation at `0e016a7` (post-merge round)

**Verdict:** the core claims hold. Six probes over real HTTP plus 25 mutants found no defect against the rulings as written. There are two MEDIUM findings: one is a case the rulings don't cover, the other breaks a cross-repo parse contract. There are also four LOW items, two NITs, and a squash message that is wrong on six counts.

**Scope:** `origin/main` is still `0e016a7`, so nothing below has changed there, and no open PR touches the files involved. The squash tree `b83c2fa3` is identical to the PR head `71310f9b`, so all 8 commits landed.

## Findings

**1. MEDIUM: a partial fetched dataset reports `null` after an inline train-only start.** `src/api/lifecycle/manager.py:2545-2566`
- **What's wrong:** binding `X` sets `_dataset_shortfall` to `None` (`:2557`). But `X_val`/`X_test` are kept when omitted (`:2558-2566`), which is what `POST /v1/training/start` does with `inline_data {train_x, train_y}`. The run then early-stops on the partial fetch's val split and scores on its test split, while status and `/v1/metrics` both say `null`. That is the denial `APD-CASCOR-007` removed.
- **Evidence:** `probes/probe_mixed.py` prints `shortfall None | in-loop val IS the partial fetch's: True | reported test IS the partial fetch's: True | GET /v1/metrics dataset_shortfall: None`. On the parent `f7a6d57` it still reported `ds-1`.
- **Fix:** this needs a ruling on mixed provenance. Options:
  - keep the annotation while any retained partition came from the fetch;
  - drop kept val/test when new `X` arrives without them;
  - annotate each partition separately.

**2. LOW: canopy shows the WITHHELD remedy as if juniper-data wrote it.** `manager.py:4032`
- **What's wrong:** canopy's `_producer_detail_from_refusal` (juniper-canopy `src/frontend/dashboard_manager.py:8332-8341`, origin/main `9cdfcad4`) cuts the producer text off at `" To accept it,"`. The new WITHHELD remedy opens with "Retry once…", so it isn't cut.
- **Evidence:** `probes/probe_canopy_parse.py` runs canopy's function verbatim. Four of the five refusal branches return exactly the producer's text. The WITHHELD branch returns the producer's text followed by about 400 characters of cascor's retry advice.
- **Fix:** start that remedy with "To accept it, retry once…", and add a test that every refusal branch contains `" To accept it,"`.

**3. LOW: flag off plus `allow_truncation: null` tells the operator to turn on a flag that can't help.** `manager.py:4040-4042`, gated at `:4033`
- **What's wrong:** the resolver checks whether the key is present, not its value (`:4212`). With the flag on, the same request gets "the service setting cannot change this outcome". A `null` inside `params` survives both routes' `model_dump(exclude_none=True)`.
- **Evidence:** in `probes/probe_xa2.py` section C, `flag=false` names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true`, and `flag=true` says "carried allow_truncation with no value".
- **Test gap:** mutant M21 (`params.get("allow_truncation") is None` instead of key absence) survives all 2426 `unit/api` tests and the integration tier. Register constraint (4) is not pinned anywhere.
- **Fix:** have the resolver return a "caller deferred" reason and pick the null remedy whatever the flag says. Add a live-path null test.

**4. LOW: an ordinary validation 422 is described as a producer inconsistency.** `manager.py:4024`, `:4034-4036`
- **What's wrong:** `looks_like_shortfall` matches any "422". With the flag on, a plain param error on `spiral` now carries the refusal token (which opens canopy's partial-data prompt). The text also says "A producer that refuses for a shortfall on a generator whose schema does not declare allow_truncation is inconsistent".
- **Evidence:** `probes/probe_ordinary422.py` (spiral, `n_spirals=1`) prints `token=True` plus that sentence.
- **Fix:** when the reason is not-truncatable, the generator cannot be short by construction, so return the plain `juniper-data fetch failed: …` without the token.

**5. LOW: a listing where only some entries have a schema is cached for the life of the process.** `manager.py:127-128`, `:180`
- **What's wrong:** entries with no schema are silently skipped, and the result is cached. That contradicts the reasoning in `derive`'s own docstring. It is pinned by `src/tests/unit/api/test_truncatable_generators.py:125`.
- **Evidence:** `probes/probe_xa.py` 1b: with `equities`' schema removed, the set is `['csv_import']`. After the producer recovers it is still `['csv_import']`, with `gen_calls=1`.
- **Reach:** real juniper-data (`7125e16`, through its own app) emits a schema for all 16 entries, so this only bites a non-conforming producer or proxy.
- **Fix:** treat any entry without a schema as unknown: fail the read, or don't cache.

**6. LOW (test gap): nothing pins auto-start's listing URL or API key.** `src/api/app.py:562`
- **What's wrong:** the code is correct today, but the fake client in `src/tests/unit/api/test_auto_start_shortfall.py:132-134` ignores its constructor arguments. juniper-data's auth-exempt list is `/v1/health*` plus `/metrics` (`juniper_data/api/constants.py:72`), so `/v1/generators` needs the key when auth is configured. Dropping the key would silently withhold the opt-in on every such auto-start.
- **Evidence:** M22 (`api_key=None`) and M23 (hard-coded URL) each pass 121/121 named tests, 2426/2426 `unit/api` tests and the integration tier.
- **Fix:** record the constructor kwargs and assert `base_url`, `api_key`, `timeout=5`, `retries=0`.

**7. NIT: the WITHHELD remedy lists every path's instructions instead of the caller's.** `manager.py:4032`
- One string is emitted everywhere, so auto-start is told "a failed start leaves its dataset staged".
- "Retried only by restarting" disagrees with `manager.py:90` ("stage the dataset, or restart") and the note at `AGENTS.md:~182-189`.
- **Fix:** pass the path to the describer.

**8. NIT: the shortfall is logged as accepted before the artifact is converted.** `manager.py:4525`, `app.py:615`
- A refused artifact therefore leaves a log line saying a partial dataset was accepted, for data that was never loaded.

## Squash message (`0e016a7`): false statements about the landed code

It is the arm-time body. It lists 5 of the 8 commits and leaves out `281bc524`, `40c1c5ea` and `71310f9b`.
1. **Title**, "dataset_shortfall is re-decided every run": it follows the loaded data.
2. **Body 8-9**, "clear … at the start of every run … what THIS run fetched, or it is null": superseded; there is no clear at run start.
3. **Body 9-10**, "re-decides it and applies it at submit": it is bound with the tensors (`:2557`, `:4585`).
4. **Body 13**, "reset() clears it": it keeps it (`:2897-2902`). The later e02020d bullet in the same body says the opposite.
5. **Body 14-15**, "a staged fetch refused after its annotation was written restores the previous one": no restore exists; `281bc524` removed it.
6. **Body 15-17**, "Stop -> Start on retained data now reports null": it keeps the annotation (probe: `ds-1` retained).
7. **Body 29**, `Allow-Symbol-Loss:` is not a parseable trailer (`%(trailers)` shows only `Co-authored-by`). main-verify honoured it anyway: "waived … OK: no unwaived symbol-loss findings".

## Tests and CI
- **The four named files:** 121 passed (29/34/14/44).
- **`src/tests/unit/api`:** 2426 passed, 0 failed.
- **The 19 other files that import `manager.py`/`app.py`,** run with `--integration`: 252 passed, 3 skipped (they need `--slow`).
- **Main CI for `0e016a7`, all green:**
  - CI/CD Pipeline: Unit 5274 passed on py3.12/3.13/3.14 on ubuntu and on py3.12 on macOS; Full Integration 172 passed.
  - Post-Merge Main Verification, CodeQL, Golden Regression, Conformance and cascor-model: all success.
- **CodeQL:** 0 open alerts in the changed files. #6407-6411 are `fixed`, not dismissed, and the diff adds no suppression markers.

## Mutations (25)
22 were killed by the named files.
- **Mutations you asked for:**
  - memoise a failed read: 4 tests catch it;
  - set the annotation before the tensors: 2;
  - set it between conversion and the validation split: 1;
  - send the opt-in when membership is unknown: 5;
  - clear on `reset()`: 1.
- **Also killed:**
  - no rollback restore: 1;
  - inline start keeps the stale annotation: 5;
  - key the memo without the URL: 2;
  - eager fetch: 9;
  - auto-start writes early / drops the annotation: 1 / 7;
  - retries or timeout loosened: 1 each.
- **Survivors:** M21, M22 and M23 (findings 3 and 6).
- M24 was discarded because it was malformed.

## Attacks that did not land
- **Failures are never cached.** A 7 s delay gives up in 5.01 s. A 500 fails in 0.00 s (the zero-retry setting holds), as do bad JSON, `[]`, a dict payload, a schema-less listing and a refused connection. Each returns `None`, the cache stays empty, and the next read caches the set.
- **No opt-in goes out when membership is unknown.** The POST body carries no `allow_truncation`. After recovery the retry sends `True`, and the third start hits the cache.
- **Changing the URL at runtime works.** Swapping `JUNIPER_DATA_URL` means each producer is read once and its own answer applied, under two cache keys.
- **Concurrency is safe.** 8 cold concurrent reads produce 8 GETs (not coalesced) and identical results. No lock is held during I/O, and no failure is stored.
- **The real producer matches the CHANGELOG.** The derived set is exactly `{csv_import, equities, equities_seq}`, all at top-level `properties`.
- **Lifecycle, via the real `_reload_dataset`:**
  - staged fetch, Stop→Start, reset, start after reset and start_fresh all keep the fetch's annotation;
  - inline data gives `null`, and a new fetch replaces the annotation;
  - a refused artifact or a 422 keeps both the data and its annotation, and the config stays staged;
  - a live swap that succeeds takes the new annotation; a 422, refused artifact, cancel or post-fetch failure rolls it back;
  - a poll mid-conversion saw the old annotation;
  - auto-start: on success the annotation reaches status; a refused artifact leaves none and the failure is recorded.
- **No flag-on refusal names the flag,** on either the staged or auto-start path.
- **Constants and CHANGELOG.** The two `cascor_constants` copies are byte-identical, and nothing else in the ecosystem uses the removed constant. `CHANGELOG.md` drops 0 lines against the parent; the duplicate `### Added`/`### Fixed` headings were already there.
- **Docs match the code**, apart from item 7: the note in `AGENTS.md` and the `dataset_shortfall` entry in `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`.

**Documents referenced:** `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (§4.9 rulings, rows `APD-CASCOR-008`/`-013`), cascor `AGENTS.md`, `docs/api/JUNIPER_CASCOR_API_REFERENCE.md` and `CHANGELOG.md`.

**Changed:** none. Everything was read-only. Probes and logs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678/probes/`, which is temporary. Copy them to `util/ad-hoc/` if they should be kept.
