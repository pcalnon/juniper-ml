# juniper-data v0.17.0 – :lock: SECURITY RELEASE (MINOR)

**Release Date:** 2026-10-08
**Release Type:** MINOR (security-bearing)
**Priority:** High: upgrade every juniper-data deployment
**Package Affected:** juniper-data

---

This is a minor release of `juniper-data` that carries two security fixes. First, a non-ASCII `X-API-Key` is answered 401 instead of a 500, whose error event could carry the real configured key to Sentry. Second, `FailedAuthThrottle.check()` no longer adds a table entry for every client address, which had let the table grow without bound. It also moves `equities_seq` to generator 6.0.0 (`regression`), refuses a later `purchase_date` under `fundamentals_fill="drop"`, closes a race in conditional tag edits, and opts out of FastAPI's native telemetry. The image's dependency lock moved: FastAPI 0.142.2, Starlette 1.7.0, Uvicorn 0.54.0, sentry-sdk 2.71.0. The vectors need, respectively, Sentry to be configured and sustained traffic from many distinct addresses, so this is rated Medium.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-data` |
| **Fixed in** | 0.17.0 |
| **Vulnerability class** | Improper handling of an exceptional condition that exposed a secret ([CWE-755](https://cwe.mitre.org/data/definitions/755.html)); allocation of resources without limits ([CWE-770](https://cwe.mitre.org/data/definitions/770.html)) |
| **Advisory** | None. Internal findings from the juniper-canopy#683 validation (2026-09-24) and the Cursor flood-3 evaluation (2026-10-08); there is no CVE or Dependabot alert |

---

## Changes in v0.17.0

### Added

- **The publish path asserts that the image serves, and that it is the version it is tagged**
  (`util/check_image_serves.py`, new; `publish-image.yml`). The existing checks cover what the image
  contains and that `juniper_data` imports. Neither can see a stale version. The worker's 0.5.0 and
  0.6.0 images imported fine while their package reported `0.4.0`, and cascor's 0.11.0 stamps
  `meta.version: "0.6.0"` on every enveloped response. The script starts the image as deployed, with
  its own `CMD`, and requires liveness on :8100, plus one version across the installed metadata,
  `juniper_data.__version__` and the `/v1/health` body. On a release, that version is the one in
  the **tag**. An absent `__version__` fails: the ecosystem's class-2 sweep once scored that shape as
  a pass. The check runs on the PR arm against the image just built, and on the publish path against
  each pushed digest before the digest is exported. It passes the published `juniper-data:0.15.0`,
  and fails that image when told to expect `0.16.0`. The script is the same one the four other image
  repos carry. `juniper_data/tests/unit/test_check_image_serves.py` (new, 22 tests) needs no Docker.
  This is item 5 of the juniper-ml container-registry rollout handoff.
- **`equities_seq` documents the recurrence-ready request** (W1.1(a) of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  docs only, no behaviour change). The bare defaults are untrainable by juniper-recurrence: columns
  7, 8 and 14 of `X` carry NaN before each ticker's first SEC filing (F-P1, juniper-data#409).
  - **Dataset half:** `fundamentals_fill: "drop"`, `normalize_features: false`,
    `regression_target: "log_return"`, explicit `symbols`. `normalize_features: false` restates the
    default and hashes to the same `dataset_id`.
  - **Model half** (the juniper-recurrence `POST /v1/train` / `POST /v1/crossval` body):
    `readout: "rff"`, `ridge: 1.0`, `rff_features: 256`, `rff_gamma: "median"`. They are not
    juniper-data params, and `POST /v1/datasets` ignores them silently.
  - `normalize_features` stays `false`: producer normalisation is fitted on the pooled `train`
    partition, so it is a convenience for the happy path and not a cross-validation control, and
    the 2026-10-04 measurement (juniper-ml
    `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §3.3) gave no
    reason to enable it.
  - Written in the `equities_seq` module and class docstrings, a new `docs/REFERENCE.md` section
    (Equities Sequence: Recurrence-Ready Parameters) and `docs/DEVELOPER_CHEATSHEET.md`. Both
    documents also carried a claim that the `fundamentals_fill` default is `"zero"`; it has been
    `"nan"` since 2026-09-05, and the claim is corrected.
  - `TestRecurrenceReadyBundle` (`juniper_data/tests/unit/test_equities_seq_generator.py`) pins the
    bundle as finite and the bare defaults as non-finite in exactly columns 7, 8 and 14.

### Changed

- **`create_app` opts out of FastAPI's native telemetry** (#454). FastAPI 0.142, which the image
  runs since #446 (below), ships built-in telemetry with tracing, metrics, logs, operation spans and
  auto-configuration all on by default. `create_app` now passes all five as `False`, so FastAPI's own
  instrumentation cannot overlap the service's configured observability (Sentry, Prometheus,
  structured logging). This is hardening rather than a fix for a live leak: `configure_sentry`
  installs no OpenTelemetry provider, so the only visible effect before was a startup warning when
  `OTEL_EXPORTER_OTLP_ENDPOINT` is set. On FastAPI < 0.142, which `pyproject.toml` still admits, the
  keyword is inert (it lands in `app.extra`); the test pins all five flags off and skips there.
- **The image's dependency lock moved** (Dependabot #441, #446; `requirements.lock`). The notable pins:
  `fastapi` 0.141.1 → 0.142.2 (which adds `opentelemetry-api` 1.45.0 for the telemetry above),
  `starlette` 1.6.0 → 1.7.0, `uvicorn` 0.53.0 → 0.54.0, `sentry-sdk` 2.70.0 → 2.71.0, `uvloop` 0.22.1 →
  0.23.0 and `websockets` 17.1 → 17.2, plus eight smaller moves (`charset-normalizer`, `filelock`,
  `huggingface-hub`, `peewee`, `platformdirs`, `python-dotenv`, `pytz`, `soupsieve`). The wheel's declared requirements are
  unchanged; this is the image.
- **`equities_seq` is declared `regression`, not `classification`, and its `generator_version`
  is 6.0.0** (X8, owner ruling 2026-09-24). The generator emits two targets: a one-hot next-day
  direction (`y_*`) and a next-day close (`y_reg_*`). `task_type` has no word for "both".
  - The one model that trains on it, juniper-recurrence's LMU, reads `y_reg_*` by key, and
    juniper-canopy already labelled it `regression`. So the two vocabularies disagreed, and the
    owner ruled that juniper-data changes its label.
  - **What changes:** `POST /v1/datasets` dispatches meta on the registry's `task_type`, so an
    `equities_seq` artifact's `n_classes` and `class_distribution` are now `null`. The arrays,
    the checksum and every other meta field are unchanged.
  - **Why 6.0.0:** the dataset ID hashes the generator version but not the meta, and a cache hit
    serves the stored meta as-is. Without the bump, a cached 5.0.0 artifact would keep serving
    classification meta under the id a fresh request resolves to. That is how `arc_agi`'s #402
    relabel went stale until #427.
  - **The equities pair now differs for the first time.** Flat `equities` keeps
    `classification` at 5.0.0, because the ruling named `equities_seq` only.
  - **Consumer census** (all nine repos, plus juniper-slacker): nothing breaks.
    - juniper-recurrence never reads juniper-data's `task_type`: its model, crossval and bench
      use the model's own label, and pick `y_reg_*` by key.
    - `GeneratorInfo` does not carry `task_type`, so the `/v1/generators` listing is unchanged.
    - The only visible effect is juniper-ml's experiment `stats_summary`, which now prints
      "task: regression" and drops its class-distribution line for these artifacts.
  - `juniper_data/tests/unit/test_equities_seq_task_type.py` (new). `test_val_emission_guards.py`
    records the reason for the 6.0.0 bump.
  - *Moved here from `[0.16.0]`: #437 merged at 09:14Z on 2026-09-24, after `v0.16.0` was tagged at `39d1cab2`, so 0.16.0 does not carry it.*
- **Under `fundamentals_fill="drop"`, a `purchase_date` after `start_date` is refused** (W1.8,
  F-P2). This applies the plan's recommended R3 pending the owner's ruling (alternatives: a
  documented finite sentinel; dropping rows without refusing).
  - **Before:** `cost_basis` is NaN on every row before the purchase session (APD-DATA-042), and
    `drop` removed only the rows lacking shares, so such a request minted a non-finite
    `cost_basis` in an artifact the caller had asked to be complete.
  - **Now:** `EquitiesParams` refuses it with **400** `Invalid parameters: …`, naming both dates
    and the fill mode. The check runs before the `dataset_id` is hashed and looked up, so an
    artifact minted before this change cannot answer the refused request. A pre-purchase row
    that still reaches conditioning (a provider row dated on a weekend, or before `start_date`)
    is dropped exactly like a row without shares, with a WARNING.
  - **"After" means at least one weekday apart.** The defaults (`2000-01-01`, a Saturday, and
    `2000-01-03`, a Monday) stay accepted, and with them juniper-canopy's two equities registry
    seeds, which send `drop` with the default dates. Exchange holidays are not modelled, so a
    start on one with a purchase on the next session is refused.
  - **Unchanged:** `nan` and `zero`, which still emit the pre-purchase rows with a NaN
    `cost_basis`.
  - **`generator_version` is not bumped** (`equities` 5.0.0, `equities_seq` 6.0.0). A refused
    request mints nothing, and every request that still mints emits the arrays it emitted before:
    with no weekday between the two dates its frame holds a pre-purchase row only if the provider
    dates one on a weekend or before `start_date`, and none of the 3,193,942 rows in the
    development host's download cache is either.
  - Both generators are affected: they share `EquitiesGenerator._condition_one` and both emit
    `cost_basis`. Pins: `TestCostBasisUnderDrop` (`test_equities_generator.py`) and
    `test_create_dataset_refuses_drop_with_a_later_purchase_before_the_cache`
    (`test_api_routes.py`).

### Fixed

- **A conditional `PATCH /v1/datasets/{dataset_id}/tags` can no longer pass its check and then
  lose the race.** 0.16.0 promised that it could not (#428). On one host it could.
  `PATCH /v1/datasets/batch-tags` read and wrote the metadata in two unlocked hops, and
  `DELETE /v1/datasets/{dataset_id}` took no lock, so either could land between a conditional
  PATCH's passed check and its write. The PATCH then erased the batch's acknowledged edit, or
  answered `200` with a new `ETag` for a dataset the delete had just removed, because
  `update_tags` ignored `update_meta` reporting it gone.
  - **Every route that edits or deletes a dataset now takes the same two locks, in
    `update_tags`' order.** batch-tags applies each dataset's edit through `update_tags`, still
    without evaluating preconditions and with the same response. `DELETE`, batch delete and
    expired-dataset cleanup delete through the new `DatasetStore.delete_under_lock`.
  - **Why the lock is taken outside each store's `delete`.** `delete_under_lock` wraps each
    store's own `delete` and is never called from inside one: `_version_lock` is one
    non-reentrant lock shared by every store, and `CachedDatasetStore.delete` calls two other
    stores' `delete`.
  - **A dataset gone by the write is a `404`.** One removed between the read and the write, by
    something outside the locks, no longer gets a `200` with an `ETag`.
  - **Scope.** The guarantee holds across processes on one host with LocalFS, and within one
    process with the Redis, Postgres and cached stores.
  - **Lock files for absent ids.** `DELETE`, batch delete and batch-tags now also leave the
    lock file for an id that does not exist, as `PATCH .../tags` already did.
  - **Tests.** Interleaving tests hold a conditional PATCH inside its window and send
    batch-tags or `DELETE`. A stand-in for `_version_lock` announces any thread that has to wait
    for it, so both outcomes are observed events, not timeouts.
- **A `*` wrapped in NBSP (0xA0) or NEL (0x85) is malformed.** 0.16.0 read it as `*`, because
  `http_cache` matched `*` after `str.strip()`, which strips those obs-text bytes too. So a read
  answered `304` where the full body was owed, and a `PATCH` that should have failed closed
  wrote. Both sites now strip RFC 9110 OWS, spaces and tabs, only. The tests send raw bytes
  through `httpx.ASGITransport`, because Starlette's TestClient re-encodes `0xA0` as UTF-8.
- **A metadata file that leads out of the storage root is a storage fault, not the caller's
  error.** LocalFS's containment check raised `InvalidDatasetIdError`, so for such a dataset
  0.16.0's artifact route answered with the caller's `400`, where 0.15.0 served the artifact.
  - The check now raises `StorageContainmentError`, still a `ValueError` but not an
    `InvalidDatasetIdError`.
  - The artifact is served without a validator.
  - A conditional request skips the `exists()` gate, which consults the same metadata, and is
    judged after the open, as for an orphan.
  - The other routes keep the `400` they gave through 0.15.0.
- **0.16.0's entries for conditional requests misstated four things.** The section below is left
  as released; `docs/api/JUNIPER_DATA_API.md` and `docs/REFERENCE.md` state them correctly.
  - **Malformed.** A malformed field is one that is not `*` or a well-formed entity-tag list. The
    entry left out `*`.
  - **404 targets.** "A precondition is never answered for a target that would 404" holds on
    LocalFS. The in-memory, Redis and Postgres stores' `exists()` checks the metadata alone, so on
    them a dataset whose artifact is gone can still answer `304`.
  - **Accesses.** A `412` reads nothing and records no access. The entry said every
    `GET /{dataset_id}` records one.
  - **The breaking flag.** The access-counter removal was flagged in bold mid-bullet, a form
    juniper-ml's release renderer does not read. The v0.16.0 notes still marked the release as
    breaking, because the same release removes `X_full` from the HF and Kaggle stores. The
    versioning policy in `docs/api/JUNIPER_DATA_API.md` now says the flag is the word in capitals,
    the form the renderer reads.
- **The conditional-request tests pin what they did not.** Nothing tested either of these:
  - that the PATCH precondition runs under the cross-process lock. A check inside
    `_version_lock` but outside the `flock` passed all 1840 unit tests;
  - that an empty `If-Match` is a `412`.

  Three verification scripts changed:
  - **The non-vacuity harness.**
    `util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py` now applies
    fifty-three mutations. Every test in `test_conditional_requests.py` is named by one, 58 of
    its 69 as a test that must go red.
  - **The equivalence script.** `util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py`
    adds a structured sweep over lists of up to twelve elements, with 0 mismatches in 3,495,076
    inputs.
  - **Two new scripts beside them** re-derive the harness's coverage counts and show that the
    sweeps catch long-list mutants.
- **`FailedAuthThrottle` no longer grows its table by one entry per distinct client**
  (`juniper_data/api/security.py`). `check()` is documented as a read-only probe, but `_failures`
  was a `defaultdict(lambda: (0, 0.0))`, so `self._failures[client_ip]` inserted an entry for every
  unseen source IP. `SecurityMiddleware` calls `check()` on every non-exempt request before
  authentication, while pruning (`_maybe_cleanup`, including the 10,000-entry `_MAX_ENTRIES` cap)
  runs only from `record_failure()`. Under open auth or valid-key traffic nothing calls
  `record_failure()`, so the table grew without bound for the life of the process.
  - **Fix.** `_failures` is a plain `dict`, and `check()` and `record_failure()` both read
    `self._failures.get(client_ip, (0, 0.0))`, so only a recorded failure allocates. The
    `defaultdict` import is gone; nothing else in the module used it.
  - **Pin.** `test_check_never_allocates_an_entry` (`juniper_data/tests/unit/test_middleware.py`)
    probes 1,000 distinct IPs and requires an empty table, then exactly one entry after one
    `record_failure()`. Against the old code it fails with `assert 1000 == 0`.
  - The copies in juniper-service-core and juniper-cascor carry the same defect and get the same
    fix in their own repos, each pinned by its own test.
- **`docs/REFERENCE.md` called the `Sequence Safety` check advisory, "never required, never blocks
  a merge".** The `main` ruleset (`juniper-data-rules`, id `14748749`) requires that context, so a
  red run blocks merge. `sequence-safety.yml` is a standalone workflow, so its job is absent from
  `ci.yml`'s Quality Gate `needs:`, and a green Quality Gate does not mean a PR is mergeable. #393
  corrected the workflow header on 2026-09-11; this corrects what it left:
  - the workflow-table row, now marked **Required** and linked to a new section, Sequence Safety
    (required check), with the ruleset query, the Quality Gate distinction, and the waivers. The
    `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` commit trailers are what the post-merge
    `main-verify.yml` honours. The owner labels `allow-symbol-loss` / `docs-rewrite` demote the
    matching per-PR screen to WARN-only and do not reach the post-merge net;
  - the Main Verify row, which called that net advisory. It runs after the merge, so it is not a
    PR status check and cannot block the merge; a finding turns its run red and upserts a tracking
    issue;
  - two leftover "advisory" comments in `sequence-safety.yml` and one in `main-verify.yml`
    (comments only; the job name stays `Sequence Safety`);
  - `docs/ci_cd/CICD_MANUAL.md` § Quality Gate, which presented the Quality Gate as the merge gate.
    It now says the ruleset requires contexts outside the gate's `needs:`.

### Security

- **A non-ASCII `X-API-Key` is a 401, not a 500 that hands Sentry the real key**
  (`juniper_data/api/security.py`). `APIKeyAuth.validate` compared `str` with
  `hmac.compare_digest`, which raises `TypeError` when either side holds a non-ASCII character.
  Starlette decodes header bytes as latin-1, so any byte above 0x7f reaches `validate` as one. The
  validation of juniper-canopy#683 (2026-09-24) sent an anonymous `X-API-Key: \xa0`, which both
  uvicorn parsers pass. It had three consequences:
  - The `TypeError` escaped `SecurityMiddleware`'s `except HTTPException`, so the caller got a
    **500** instead of a 401.
  - Only a 401 records a failure, so a flood of such keys was **never throttled** by
    `FailedAuthThrottle`.
  - Under Sentry's default `include_local_variables=True`, the error event carried the loop's
    `candidate`, the **real configured key**.

  Both sides are now compared as UTF-8 bytes. The encoding uses `surrogatepass`, the one built-in
  error handler that is both total and injective: a lone surrogate (from a JSON-decoded
  `JUNIPER_DATA_API_KEYS`, say) encodes instead of raising, and no two distinct strings share
  bytes. So `validate` matches exactly when the strings are equal. `surrogateescape` raises on
  `"\ud800"` and maps `"\xe9"` and `"\udcc3\udca9"` to the same bytes. The keys stay in a `list`,
  and juniper-ml's `tests/test_service_fork_drift.py` markers (`blank-api-key-filter`,
  `nonshortcircuit-key-compare`) are unchanged. Owner ruling "Fix everywhere now" (2026-09-24),
  landing the same compare in juniper-service-core and juniper-cascor.
  **Sentry:** juniper-data configures Sentry only through juniper-observability's
  `configure_sentry` (`juniper_data/api/app.py`), so there is no local setting to change. It
  inherits `include_local_variables=False` from the juniper-observability release that carries
  it, once the `juniper-observability>=0.4.0` floor is raised to that release.
  Pinned by 61 new tests in `juniper_data/tests/unit/test_security.py`, in two classes marked
  `unit` so that CI's `-m "unit and not slow"` lane runs them. `TestAPIKeyAuth` is unmarked, so a
  test added there would never run in CI. `TestNonAsciiApiKey` covers the non-ASCII mismatch, a
  7x7 equality matrix built to separate the candidate encodings, and the `Request`-level 401.
  `TestNonAsciiApiKeyThroughTheApp` drives `create_app` with auth on and checks that a raw-byte
  header is a 401 and that ten such failures earn a 429. Reverting to the `str` compare fails 60
  of them, the app tests with `assert 500 == 401`. `surrogateescape` fails 15 and strict UTF-8
  fails 33 (juniper-ml's `util/ad-hoc/2026-09-24_bytes_compare_sentry_locals_verify.py`).
  `test_validate_uses_constant_time_comparison` now expects the bytes that `compare_digest`
  receives.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-data/blob/v0.17.0/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-data_v0.17.0.md`
