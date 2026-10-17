# juniper-recurrence v0.6.0 – :lock: SECURITY RELEASE (MINOR)

**Release Date:** 2026-10-17
**Release Type:** MINOR (security-bearing)
**Priority:** High: upgrade every juniper-recurrence deployment
**Package Affected:** juniper-recurrence

---

This is a minor release of `juniper-recurrence` that carries three security fixes:

- **W1.14 (F-S10):** a 5xx from the data path no longer relays the data client's text. That text could quote a padded `JUNIPER_DATA_API_KEY` into callers' 502 bodies and into the operation record `GET /v1/training/status` serves. A padded key is now refused at settings load.
- **juniper-service-core 0.7.1:** a non-ASCII `X-API-Key` is answered 401 instead of a 500 whose Sentry event could carry the configured key, and `FailedAuthThrottle.check()` no longer grows a table entry per client address.
- **juniper-observability 0.4.1:** `configure_sentry` stops sending frame-local variables.

The release also:

- adds model snapshots and operation identity (`operation_id`, `expect_operation_id`, the `training` / `restoring` / `failed` / `restored` states);
- labels train metrics `in_sample`;
- adds `train --params` / `--params-file`;
- adds a configurable juniper-data timeout (default 120 s);
- moves the image to juniper-data-client 0.6.0, whose W1.4 validator refuses non-`float32` features and targets, and to juniper-recurrence-model 0.4.0.

The first fix needs an operator to configure a padded key, and the others need Sentry or sustained traffic from many addresses. It is therefore rated Medium.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-recurrence` |
| **Fixed in** | 0.6.0 |
| **Vulnerability class** | Generation of an error message containing sensitive information ([CWE-209](https://cwe.mitre.org/data/definitions/209.html)) and insertion of sensitive information into a log ([CWE-532](https://cwe.mitre.org/data/definitions/532.html)) (W1.14); improper handling of an exceptional condition that exposed a secret ([CWE-755](https://cwe.mitre.org/data/definitions/755.html)) and allocation of resources without limits ([CWE-770](https://cwe.mitre.org/data/definitions/770.html)) (service-core 0.7.1) |
| **Advisory** | None. Internal findings: F-S10 of juniper-ml `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, reproduced live in juniper-canopy#702; the shared patches come from the juniper-canopy#683 validation (2026-09-24) and the Cursor flood-3 evaluation (2026-10-08). There is no CVE or Dependabot alert |

---

## Changes in v0.6.0

### Added

- **`juniper-recurrence train` gains `--params <json>` / `--params-file <path>`** (mutually
  exclusive). This is W0.6 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`,
  and it closes F-S1. `train --generator` had no way to pass generator params: the CLI called
  `load_sequence_data` without `params`, so `create_dataset` always received `{}` and an
  `equities_seq` dataset was built from the generator's bare defaults, which are not trainable
  (F-P1). The only CLI route to a trainable equities fit was `--dataset <id>` of an artifact minted
  elsewhere. The parsed JSON object is now threaded into `load_sequence_data(params=…)`, the channel
  `POST /v1/train` already uses for `dataset.params`. Either flag without `--generator`, malformed
  JSON, JSON that is not an object, or an unreadable file exits 2 with a message on stderr, before
  any dataset is requested. Both flags together is an argparse usage error (exit 2). `train --help`
  shows an `equities_seq` example. `tests/test_cli_train.py` gains 18 tests, among them the plan's
  bounded offline E2E: the explicit params reach `create_dataset`, the real `validate_npz_contract`
  checks a three-partition artifact, and the fit prints its metrics.
- **`POST /v1/train` labels its metrics: `TrainResponse.metrics_scope` is `"in_sample"`** (W0.7,
  service half; the label half of F-S5 / F-SCI3 in the same plan). `final_metrics` are scored on the
  split the fit was trained on (`dataset.split`), so they are in-sample, and the response did not say
  so; the r2 that canopy and the juniper-ml suite surfaced from it is in-sample too. The field is a
  one-value constant for now because this route reports no held-out metric; plan item W5.3 adds
  further scopes. No number changes. The field is additive, and `juniper-recurrence-client` returns
  the response object as-is, so it needs no change. `tests/test_routes.py` gains 3 tests.
- **The image's publish path asserts that it serves, and that it is the version it is tagged**
  (`util/check_image_serves.py` at the repo root, new; `.github/workflows/publish-image.yml`). The
  existing checks cover what the image contains and that `juniper_recurrence` imports. Neither can
  see a stale version: the worker's 0.5.0 and 0.6.0 images imported fine while their package
  reported `0.4.0`. The script starts the image as deployed (`juniper-recurrence serve`). It requires
  liveness on :8210, plus one version across the installed metadata and
  `juniper_recurrence.__version__`. On a release, that version is the one in the **tag**, and the
  step strips `juniper-recurrence-v` from it. This service's `/v1/health` body is
  `{"status": "ok"}`, with no version field, so the check runs with `--health-version optional`. An
  absent field passes, and a present one that disagrees fails. The check runs on the PR arm against
  the image just built, and on the publish path against each pushed digest before the digest is
  exported. It passes the published `juniper-recurrence:0.5.0`. The script is the same one the four
  other image repos carry. `juniper-recurrence/tests/test_check_image_serves.py` (new, 20 tests)
  needs no Docker. This is item 5 of the juniper-ml container-registry rollout handoff.
- **Model snapshots: `POST`/`GET /v1/model/snapshots`, `GET`/`POST /v1/model/snapshots/{id}[/restore]`.**
  The service's **first persisted artifact** — until now it wrote nothing to disk.

  This closes **Y2** of the canopy selection-reachability arc, where canopy's snapshot workflow
  reported success at **both ends** while never touching model state: its h5py fallback wrote
  timestamps and cascor-shaped `nn_*`/`cn_*` params, `stat()`ed the file and returned a real byte
  size; restore read it back, rewound canopy's *display* counters, and reported
  *"Restored from snapshot X"*. The trained LMU was never written and never read.

  **No serialisation was written here.** `LMUSerializer` already round-trips an `LMURegressor`
  losslessly (versioned `schema: 2`, `allow_pickle=False`, memory eigendecomposition recomputed
  from `d`/θ on load). These routes are HTTP surface over it.

  Design of record: `JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` (juniper-ml).
- **`JUNIPER_RECURRENCE_SNAPSHOTS_DIR`** (`Settings.snapshots_dir`, default `recurrence-snapshots`).
  In the container this is a **bind mount** of the host's snapshot store, not a named volume —
  juniper-deploy tried a named volume for cascor and retired it: it mounted where cascor never
  wrote, so it held nothing while real snapshots died with the container. The bind mount survives
  `docker compose down -v`, is the same directory the host CLI and systemd tiers use, and sits
  inside the Juniper tree so the offline backup captures it.

  **Retention is inherited, not invented**: §6.4 of the ecosystem snapshot-lifecycle design was
  ratified no-deletion (juniper-ml#1296), which also says do not build deletion tooling. Nothing
  here prunes, ages out or caps, and a test pins that absence.
- **Operation identity: every fit and restore is an operation with an `operation_id`** (W1.5,
  service half, of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  F-S6, F-CON1, F-CON2). The id is a uuid4 hex minted when the request takes `train_lock`.
  `POST /v1/train` and `POST /v1/model/snapshots/{id}/restore` return it. A restored model carries
  the restore's own id, not the id of the fit that produced the snapshot. `GET /v1/training/status`
  gains `operation_id`, `operation` (`train` / `restore`), `busy_since` (ISO-8601 UTC, set only while
  the operation holds the lock), `dataset_id`, `requested_by` (the request's `X-Request-ID`, verbatim,
  or null), `model_operation_id` (the operation that produced the model `/v1/predict` would score)
  and `failure` (`{detail, status_code}`, set only under `failed`). Before this, a caller that hit a
  busy service could not tell whose run it was, and a caller could not prove that a prediction or a
  snapshot came from the model it trained. `tests/test_operation_identity.py` (new, 30 tests) holds a
  real fit under the lock, with a data client or a fit that blocks on a `threading.Event`, while a
  second request arrives on another thread.
- **`expect_operation_id` on `POST /v1/predict` and `POST /v1/model/snapshots`** (W1.5). It is
  optional. When present and different from the operation that produced the in-memory model, the
  route answers `409` and the detail names both ids. The save then writes nothing. The model and its
  id are read together, so a fit publishing in between cannot pair one with the other. When it is
  omitted the routes behave as before. The no-model `409` keeps its string detail.
- **`JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS`** (`Settings.juniper_data_timeout_seconds`,
  default `120`, must be `> 0`; W1.5, F-S9, the service half of F-D5). `load_sequence_data` built
  `JuniperDataClient(base_url=…, api_key=…)` with no `timeout`, so the client's 30 s default governed
  dataset creation, which is where a cold `equities_seq` fetch happens. No setting could raise it,
  and canopy's and the driver's own budgets stayed green while the fit failed inside. The train,
  predict and cross-validation routes and the CLI `train` now pass the setting as
  `JuniperDataClient(timeout=…)`. A direct caller of `load_sequence_data` that names no timeout gets
  `data.DEFAULT_JUNIPER_DATA_TIMEOUT_SECONDS` (`120.0`), not 30 s. There is deliberately no
  unprefixed alias. `tests/test_data_timeout.py` (new, 12 tests) asserts the keyword that reaches the
  client constructor on each of those paths.
- **README: "One caller per service".** A recurrence service is exclusively owned by one caller at a
  time: one `train_lock`, one in-memory model, one snapshot directory. The operation id is how a
  caller proves whose model it is scoring, and a fit is not cancellable. The juniper-ml launcher's
  per-run ports (8260-8289) are what keep a CLI suite and canopy apart, and canopy's service URL is
  not in that range (F-CON3). The root README points to the section.

### Changed

- **The image runs juniper-data-client 0.6.0 and juniper-recurrence-model 0.4.0** (W1.13 of
  juniper-ml `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`).
  `requirements.lock`, which the image installs, moves those two pins (0.5.0 -> 0.6.0, 0.3.0 -> 0.4.0)
  and nothing else; the count stays 31. Neither release changed its own requirements. The
  `pyproject.toml` ranges already admitted both, so a `pip install` resolves them without this
  change. What the service now refuses:
  - **data-client 0.6.0's `validate_npz_contract` (W1.4)** answers `422 invalid dataset: …` for an
    artifact with a non-finite `dt_*`, a mis-shaped, non-finite or negative `target_dt_*`, a
    `seq_lengths_*` that is not an integer or lies outside `[1, L]`, or an `X_*` / `y_*` / `y_reg_*`
    that is not `float32`. The dtype rule is the breaking one: a `float64` artifact used to load.
    juniper-data's sequence windowing casts `X` / `y` / `y_reg` / `dt` / `target_dt` to `float32`
    (`juniper_data/generators/_sequence.py`), and `equities_seq` goes through it, so a juniper-data
    artifact is unaffected.
  - **model 0.4.0 (W1.3)** logs a WARNING when a split falls back to a one-hot `y_*` because it has
    no `y_reg_*`. It also refuses a `(W, 1)` `target_dt` and a float or bool `seq_lengths`, which
    mirrors the W1.4 rules.
- **`GET /v1/training/status` gains a third `state`: `restored`, plus a `restored_from` field.**
  A model loaded from a snapshot is present and predictable, but **this process never fitted it** —
  so `final_metrics`, `stopped_reason` and `events` are absent rather than carried over or
  synthesised. Inventing a `TrainResult` to keep the status shape uniform would report a run that
  never happened, which is the defect class Y2 is about. `restored_from` names *which* snapshot,
  because "loaded from disk" without an id is precise about the wrong thing.

  A fit **supersedes** a restore: `set_trained` clears the marker, so a freshly-fitted model never
  keeps reporting itself as loaded from disk.

  `state` remains a bare `str` rather than a `Literal`, matching the field as it shipped — widening
  it would be a contract change for every consumer.
- **The `[bench]` and `[bench-equities]` extras admit `juniper-data` 0.15.0** (ceiling `<0.15.0` →
  `<0.16.0`; floor unchanged at `>=0.9.0`). juniper-data 0.15.0 (PyPI, 2026-09-22) is the first
  release to publish `equities` / `equities_seq` at `generator_version` **5.0.0** — the owner-ruled
  causal share history and 15-column feature set (juniper-data#395) plus the fix for #395's
  scale-typo regression (juniper-data#404). The old ceiling excluded exactly that release, so a
  fresh `.[bench,bench-equities]` install resolved 0.14.0 and its **3.0.0** equities generator,
  never the corrected one — and the bench's `equities_seq` row is the in-process consumer of it.
  The synthetic generators the offline bench runs are all still at 3.0.0 in 0.15.0; nothing in
  its changelog touches them. **The bench lane does not check a change like this on its own**:
  its `test` job runs only when `bench/` or its workflow changes (#178), so a ceiling move
  reaches it through `workflow_dispatch` on the branch, or not at all.
- **The `[bench]` and `[bench-equities]` extras admit `juniper-data` 0.17.0** (ceiling `<0.17.0` →
  `<0.18.0`; floor unchanged at `>=0.9.0`). This is a W1.13 prerequisite in juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`.
  - **Why.** juniper-data 0.17.0 (PyPI, 2026-10-10) is the first release to serve `equities_seq` at
    `generator_version` **6.0.0** with `task_type: regression` (owner ruling X8, juniper-data#437).
    Under the old ceiling, a fresh `.[bench,bench-equities]` install resolved 0.16.0, with its
    5.0.0 / `classification` label.
  - **No bench number moves.** The bench's `equities_seq` row calls `EquitiesSeqGenerator.generate()`
    in-process and reads `y_reg_*`. X8 changed the registry's label and the version constant, not
    the arrays.
  - **Nothing else in 0.17.0 reaches the bench.** No synthetic generator changed between 0.16.0 and
    0.17.0. The only other generator change is juniper-data#451's 400 for a late `purchase_date`
    under `fundamentals_fill="drop"`, which the bench never requests.
  - **Tested.** The `juniper-data-published` dispatch for 0.17.0 ran the bench smoke against it past
    the old ceiling, and it is green on Python 3.12, 3.13 and 3.14 (`36 passed, 1 skipped` on 3.12).
    The 3.12 job's first attempt failed only because PyPI had not propagated the upload within the
    job's 10-minute wait; its re-run passed.
  - The intermediate move `<0.16.0` → `<0.17.0`, which admitted 0.16.0 (#188, Dependabot), carried no
    entry here.
- **`GET /v1/training/status` gains `training`, `restoring` and a terminal `failed` state** (W1.5).
  Every existing field and state is kept. A fit that raised used to leave no record: the route's
  `finally` released the lock and the status went on describing an earlier run, or `idle`. It now
  reads `failed` with the operation's id and `failure`, and any earlier model stays loaded and
  predictable (`model_operation_id` names it). The route still re-raises or maps every error exactly
  as before; only the record is new. A run in flight reads `training`, with `busy_since`. `restored_from`
  is still non-null only under `restored`. `AppState.status()` keeps its 3-tuple, now derived from
  the new `AppState.status_snapshot()`.
- **The busy `409` of `POST /v1/train` carries an object `detail`** (W1.5): `{message, operation_id,
  operation, busy_since, requested_by, dataset_id}`, where `message` is the old string. It was the
  bare string `"a training run is already in progress"`. The type change was checked against the
  in-ecosystem consumers. canopy's adapter keeps the raw body text, `juniper-recurrence-client`
  attaches `detail` as decoded to `JuniperRecurrenceConflictError.detail`, and the juniper-ml driver
  `str()`s it. The restore route's `409` keeps its string detail.
- **A fit publishes its model last** (W1.5). `set_trained` now runs after the metrics are recorded
  and the response is built, so the status reads `trained` only for a run whose caller is about to
  receive its result.

### Security

- **The service picks up the two shared security patches**: `juniper-service-core>=0.7.1,<0.8.0`
  and `juniper-observability[prometheus]>=0.4.1,<0.5.0`, and the image lock moves those two pins
  (0.7.0 -> 0.7.1, 0.4.0 -> 0.4.1) and nothing else. service-core 0.7.1 answers a non-ASCII
  `X-API-Key` with a 401 instead of a 500 whose Sentry event could carry the real configured key,
  and `FailedAuthThrottle.check()` no longer adds a table entry for every unseen client address.
  observability 0.4.1's `configure_sentry` no longer sends frame-local variables, which could hold
  the key. Until now the lock pinned 0.7.0 and 0.4.0, so an image built from `main` carried neither
  fix. The lock was regenerated with `--upgrade-package` for the two packages only; the pin count
  stays 31 and the arm64 wheel pre-flight passes.
- **A 5xx from the data path no longer relays the data client's text, so a padded juniper-data
  key can no longer reach callers** (W1.14, which closes F-S10, in juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  CWE-209, CWE-532). `map_data_error` answered every juniper-data client failure with the
  client's own text, e.g. `502 "data fetch failed: {exc}"`. requests refuses a header value with
  leading whitespace and quotes it, and juniper-data-client words that as
  `Request failed: … in header value: ' <key>'`. A padded `JUNIPER_DATA_API_KEY` therefore reached
  the 502 body of every `/v1/train`, `/v1/predict` and `/v1/crossval` caller, and the operation
  record that `GET /v1/training/status` serves to any caller. The juniper-ml experiment driver
  writes that detail into each run's manifest (`phases.<phase>.error`). Two changes:
  - **Every 5xx detail is now a fixed phrase**, with juniper-data's status when it answered one:
    `juniper-data unreachable: the connection failed` or `…: the request timed out`,
    `data-client misconfigured`, `data fetch failed: juniper-data answered <status>` and
    `data fetch failed: the request to juniper-data did not complete`, each followed by
    `(details in the service log)`. The full text stays in the WARNING that each route already
    logs before it maps the error. The 404 and 422 details still carry the text: they describe
    this request, and they are what canopy shows (W0.5).
  - **A padded key is refused at settings load.** `juniper_data_api_key` with leading or trailing
    whitespace, or a control character, fails `Settings()` with a message that names
    `JUNIPER_DATA_API_KEY` / `JUNIPER_RECURRENCE_JUNIPER_DATA_API_KEY` and not the value. A
    `JUNIPER_DATA_API_KEY_FILE` secret is still stripped first, so a file's trailing newline still
    works. `Settings` now sets `hide_input_in_errors`, so no `ValidationError` prints the value it
    refused; before, a refused key would have been echoed as pydantic's `input_value`.

  The 502 wording changed, so a caller that matched the old `…: {exc}` text no longer finds the
  upstream text in it. Canopy's adapter appends no 5xx detail (W0.5), so canopy is unaffected. The
  juniper-ml driver records whatever detail it is given, so it now records the fixed phrase.
  Tests: `tests/test_routes.py` gains 2, including F-S10 reproduced through the real data client
  with no network, and `tests/test_settings.py` gains 17.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-recurrence/blob/juniper-recurrence-v0.6.0/juniper-recurrence/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-recurrence_v0.6.0.md`
