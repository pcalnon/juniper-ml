# juniper-cascor v0.12.0 – :lock: SECURITY RELEASE (MINOR)

**Release Date:** 2026-10-10
**Release Type:** MINOR (security-bearing)
**Priority:** High: upgrade every juniper-cascor deployment
**Package Affected:** juniper-cascor

---

This is a minor release of `juniper-cascor` that carries three security fixes. A non-ASCII `X-API-Key` is answered 401 instead of a 500 whose Sentry error event could carry the real configured key (#689). `FailedAuthThrottle.check()` no longer adds a table entry for every unseen client address, so the table stays bounded (#710). And the image now runs `juniper-observability` 0.4.1, whose `configure_sentry` no longer sends frame-local variables to Sentry (#711). It also stops a local image build from baking in the snapshot directory's authkeys (#661; no published image was affected), and makes `APIKeyAuth` walk every configured key (#659). The rest of the release is listed below.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-cascor` |
| **Fixed in** | 0.12.0 |
| **Vulnerability class** | Improper handling of an exceptional condition that exposed a secret ([CWE-755](https://cwe.mitre.org/data/definitions/755.html)); allocation of resources without limits ([CWE-770](https://cwe.mitre.org/data/definitions/770.html)); sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal findings from the juniper-canopy#683 validation (2026-09-24) and the Cursor flood-3 evaluation (2026-10-08); there is no CVE or Dependabot alert |

---

## Changes in v0.12.0

### Changed

- **Logging costs less on the training hot path; log output is unchanged** (cascor#573; #648,
  #652, #667, #670, #675).
  - **One level table** (#648). `Logger._level_numbers` is now a copy of the canonical
    `_LOGGER_LOG_LEVEL_NUMBERS_DICT` instead of a second hardcoded table, and
    `profiling.logging_utils`'s `TRACE = 5` / `VERBOSE = 15`, which nothing referenced, are
    deleted.
  - **Symbolic guards** (#652). The 8 guard sites in `candidate_unit.py` name levels by constant
    instead of as numeric literals.
  - **A cheaper guard** (#667). `isEnabledFor` resolves the level through the emit filter's memo:
    about 1,270 ns -> 341 ns per call at a disabled level.
  - **Per-epoch progress** (#670). `_display_training_progress` evaluates its guard once and passes
    `%`-args.
  - **`%`-args** (#675). 220 f-string log calls in `candidate_unit.py` and `cascade_correlation.py`
    become `%`-args, so the message is formatted only after the level filter passes. The converter
    refused 40 further sites that may hold a 0-dim tensor, because `"%s" % torch.tensor(1.5)`
    renders `tensor(1.5000)` where the f-string rendered `1.5`.
- **A partial dataset the producer accepted now tells the operator how to refuse it** (#671).
  juniper-data#418 made `allow_truncation` a tri-state. The producer clause of
  `dataset_shortfall.summary`, and of the `DATASET SHORTFALL` WARNING, read "this run sent no
  opt-in, and a client cannot opt out of the producer's choice"; it now reads "this run sent no
  opt-in; send allow_truncation=false to refuse it".
- **The published image no longer carries the test suite** (#660). `COPY src/` copied whole
  directories, so `juniper-cascor:0.11.0` shipped 268 test files. `.dockerignore` now excludes
  `**/tests/` and `**/reports/`.
- **The image's dependency lock moved** (`requirements-cpu.lock`, through the Dependabot groups
  merged since 0.11.0 and #711). The notable runtime pins: `juniper-data-client` 0.4.2 -> 0.5.0,
  `juniper-data` 0.13.0 -> 0.16.0, `juniper-model-core` 0.3.1 -> 0.3.2, `juniper-observability`
  0.4.0 -> 0.4.1, `juniper-service-core` 0.7.0 -> 0.7.1, `fastapi` 0.141.1 -> 0.142.2 (which adds
  `opentelemetry-api` 1.45.0), `starlette` 1.6.0 -> 1.7.0, `uvicorn` 0.52.4 -> 0.54.0, `sentry-sdk`
  2.68.1 -> 2.71.0, `websockets` 17.1 -> 17.2 and `filelock` 3.32.5 -> 4.0.11, plus 14 smaller
  moves. The wheel's declared requirements are unchanged apart from this release's two floors.
- **The BLAS thread policy now caps at 2 by default: owner decision D1, ruled 2026-09-23**
  (`src/parallelism/blas_threads.py`). `configure_blas_threads()` used to do nothing unless
  `JUNIPER_CASCOR_BLAS_THREADS` was set. It now sets `OMP_NUM_THREADS` / `MKL_NUM_THREADS` /
  `OPENBLAS_NUM_THREADS` to **2** wherever they are unset, on both entry points.
  `JUNIPER_CASCOR_BLAS_THREADS=<n>` still picks the width, and **`0` / `off` / `none` now opt out**
  to the old runtime default. A malformed value falls back to 2 with a stderr note, where it used
  to fall back to no cap. Anything exported explicitly still wins, including the juniper-ml
  launcher's `runtime.blas_threads`.
  **Why the old default had to go:** the constructor's `torch.set_num_threads` pin binds only the
  thread that builds the network. The service trains on another thread, and that thread ran its
  first output pass at the runtime default (16 on a 16-core host) until the first
  candidate-result collection re-pinned it to 2. Capping that pass cut it by 49.2%.
  **Why it is safe:** cascor#531 made "do nothing" the default because the cap looked costly,
  including an epoch-count channel that wall time cannot see. The flip was gated on measuring
  that channel. Against the old default, a cap of 2 reproduced every per-candidate
  `epochs_completed`, every phase's winning candidate and the final loss **bit-identically**. A
  seed change did move the counts, so the instrument could see a difference. A training thread
  held at 16 for the whole run also moved one count. Evidence:
  `juniper-ml/notes/JUNIPER_2026-09-23_JUNIPER-ECOSYSTEM_PERF-LANE-D1-EPOCH-COUNT-DEBT.md`.
  **Deployment note:** a service container that does not export these variables now runs BLAS 2
  wide instead of runtime-default wide. Set `JUNIPER_CASCOR_BLAS_THREADS=off` to restore the old
  behaviour.

### Added

- **The publish path asserts that the image serves, and that it is the version it is tagged**
  (`util/check_image_serves.py`, new; `publish-image.yml`). The published `juniper-cascor:0.11.0`
  imports, answers `/v1/health` with `0.11.0`, and stamps `meta.version: "0.6.0"` on every
  enveloped response (#668, fixed by #672), and every existing publish-path check passed it. The
  script starts the image as deployed, with its own `CMD`. It requires liveness on :8200, plus one
  version across the installed metadata, the `/v1/health` body and `/v1/workers`' `meta.version`.
  On a release, that version is the one in the **tag**. The image ships no `juniper_cascor` package,
  because the Dockerfile copies `src/`, so there is no `__version__` to read and the envelope
  carries the in-image version check. The check runs on the PR arm against the image just built,
  and on the publish path against each pushed digest before the digest is exported, so a failing
  arch never reaches the merge job. Run against the published 0.11.0 image, it fails on exactly the
  envelope: `/v1/workers meta.version 0.6.0 != metadata 0.11.0`. The script is the same one the
  four other image repos carry. `src/tests/unit/test_check_image_serves.py` (new, 24 tests) needs
  no Docker. This is item 5 of the juniper-ml container-registry rollout handoff.
- **`current_dataset` on `GET /v1/training/status` — which dataset is loaded.** Additive.
  `pending_dataset` answered "what changes at the next start" and nothing answered "what is there
  now": `_current_dataset_config` has been tracked since the live-swap work but reached the API only
  as a swap's `before_cfg`. It has three readings a client must keep apart — `null` (nothing
  loaded), `{"dataset_type": null}` (data loaded, identity unknown: raw inline tensors), and the
  config it was loaded from. juniper-canopy needs it to hydrate its dataset selector after a page
  reload, which otherwise shows its layout default over whatever this service is training on
  (juniper-ml `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §4.10, G7).
- **`start_training(dataset_config=...)`, so the record follows the data.** A start that binds
  inline tensors used to leave `_current_dataset_config` naming the previously staged dataset — the
  field above would then have reported a dataset the run was not training on. The in-process spiral
  fallback on `POST /v1/training/start` and the auto-start path now name what they loaded; raw
  inline tensors record *unknown*. A pending staged dataset still wins, as it does over the tensors.
- **The log-record envelope and named-marker contract is enforced in cascor CI** (cascor#573,
  roadmap step P0.4). juniper-ml's analysis tooling parses cascor's logs -- the `+` sentinel, the
  timestamp and its precision, the `func:LINE]` prefix, and 35 message markers such as
  `fit: Training completed.` -- and none of that breakage was visible here: a message rename left
  every cascor test green. `src/tests/unit/test_log_record_envelope_contract.py` now pins it, with
  fixtures and a README under `src/tests/fixtures/log_envelope/`:
  - the formatter goldens for all three writers, as INSTALLED -- Path A's constants, the whole
    `conf/logging_config.yaml` (its levels decide whether the INFO run-verdict markers reach the
    file at all), and Path C's handlers including the rotation parameters;
  - the real emit path, driven in a **child process** (`src/tests/helpers/log_envelope_emitter.py`)
    because `conftest.py`'s session-scoped `_cache_logging_system` stubs `Logger._log_at_level`
    to a no-op; records are compared byte for byte in both sinks, and each `func:LINE` against the
    emitter's own AST, which makes this the detector roadmap P2.1 lacked;
  - every marker juniper-ml anchors on, in order, in the file that emits it, at or above the level
    its consumers rely on (`marker_inventory.json`, generated by juniper-ml
    `util/ad-hoc/2026-09-22_p04_log_marker_census.py`);
  - negative controls, so the checker is seen to say no.

  Mutation-checked against 14 deliberate breaks (juniper-ml
  `util/ad-hoc/2026-09-22_p04_harness_mutation_check.py`): all fail it, while the unmutated tree
  and P2.1 implemented as prescribed both pass. Test-only; no runtime change.
- **An ADVISORY exact-match check on the candidate micro-benchmark's `epochs_completed`** (owner
  decision D6, ruled 2026-09-22, juniper-ml
  `notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` §5.4: build it
  non-blocking, count how often it fires on real cascor PRs, then decide whether it blocks).
  `src/tests/unit/test_candidate_epochs_completed_advisory.py` reproduces the construction of
  `src/tests/performance/test_micro_candidate.py::TestCandidateEpochScaling::test_epoch_scaling`
  verbatim at budgets 100 and 200 -- at 10 and 50 the count equals the request, so a check there is
  a tautology -- against the reference `{100: 68, 200: 68}`, verified on `6276c45` under a 1-thread
  torch pin (the micro tier's `BENCHMARK_THREAD_PIN`). It is a `unit` test because the
  `performance` tier never runs in CI, where a check could never fire. A mismatch never fails the
  build: it issues an `EpochsCompletedDriftWarning` (under a local `"always"` filter, so a future
  `-W error` cannot turn it into a gate), appends one line to `$GITHUB_STEP_SUMMARY`, and emits a
  `::warning title=D6 advisory - epochs_completed drift::` annotation, which is what gets counted. A
  count that is not an `int`, one outside `1..budget`, or an exception from training still fails.
  - **Writing the annotation to `sys.__stdout__` does not get it past pytest.** Under the default
    `--capture=fd`, fd 1 is redirected while each test runs, so a flushed write is captured and
    discarded with a passing test's output. The check suspends capture (`capsys.disabled`),
    flushes inside the suspension, and writes a newline first: the runner parses a workflow
    command only at the start of a line, and pytest has already written the test's node id or
    progress dots without one.
  - The job log renders the command as `##[warning]<message>` without its title, so every message
    starts with the title string. The module docstring gives the `gh api` recipes for counting
    firings per PR head and per matrix leg, and says what a firing on only some legs means.

  Mutation-checked with `util/ad-hoc/2026-09-23_d6_advisory_mutation_check.py`: 21 deliberate
  breaks, all caught, against a control that is clean on both of its detectors. Twenty are caught
  by the module's own tests. The twenty-first -- the real check losing `capsys.disabled` -- is
  invisible to them and is caught only by the harness's end-to-end detector, which forces a firing
  under pytest's real capture and counts the annotation lines. Test-only; no runtime change.
- **Micro-tier timing reference (juniper-ml perf lane P2 item 2.4 / PF-4).** `tests/performance/`
  now records what it measures. `save_baseline` entries carry pytest-benchmark's timing summary
  (`mean_ms` / `median_ms` / `stddev_ms` / `min_ms` / `max_ms` / `rounds` / `iterations`) for the
  forward-pass benchmarks, every entry's `environment` gains `cpu_model`, `loadavg_1m` and
  `git_sha`, and two pytest-benchmark hooks in the performance `conftest.py` stamp host identity
  into the saved run's `machine_info` (compared by `--benchmark-compare`, warns on change) and the
  load average at save time into `juniper_run` beside it (recorded, never compared). Before this
  no cascor baseline file had ever held a timing figure: all 22 `baseline_*.json` files that ever
  existed (21 tracked until commit `971d35a` deleted them, plus the live gitignored one; 312
  entries) carry parameters and memory keys only, while `save_baseline`'s docstring promised
  `mean_ms` from the start. **Report-only by owner decision** (P2 item 2.5, 2026-09-07): nothing
  asserts on a timing, and the memory gate and the two fixed `*_TIME_THRESHOLD_S` ceilings are
  unchanged. `.benchmarks/` is now gitignored — the reference is cut with `--benchmark-storage`
  pointed outside every checkout, because a `git worktree remove` deletes ignored files. Helpers in
  `tests/performance/timing_reference.py`, pinned from the CI-collected unit tier by
  `tests/unit/test_perf_timing_reference_helpers.py`. Procedure: `docs/testing/REFERENCE.md`
  § Micro timing reference.
- **`dataset_shortfall` on `GET /v1/metrics`** (additive; `null` when the producer delivered in
  full). The same field `GET /v1/training/status` has carried since cascor#624, read from the same
  attribute so the two surfaces cannot disagree. `/v1/metrics` is where the numbers are, so it is
  where the caveat has to be: the partial-data contract requires an accepted shortfall to annotate
  **progress, metrics and results**, and a consumer reading the metrics route alone — canopy's
  metric panels do — otherwise got an accuracy with no mark of the data behind it and no reason to
  go looking for one. `GET /v1/metrics/history` deliberately does **not** carry it: its rows are
  per-epoch samples, and the shortfall is a property of the run's dataset rather than of any epoch
  in it, so stamping it on every row would imply it could vary between them.
- **`auto_start_failure` on `GET /v1/training/status`** (additive; `null` normally, and on every
  deployment that never enables auto-start). `_auto_start_training` swallows its exceptions on
  purpose — the service must come up healthy whether or not the demo run starts — but until now
  the only record was a log line: `/v1/health` stayed green, `training_active` read `false`, and
  nothing distinguished *"the dataset fetch was refused"* from *"nobody has asked for a run yet"*.
  All three give-up paths now set it: the producer never becoming ready, the dataset fetch failing
  (carrying the shortfall-refusal message, remedy included), and the catch-all handler, which
  records the exception **type** as well as its message because a bare `KeyError('meta')` renders
  as `'meta'`.

### Fixed

- **`Logger.set_level()` did not change what was emitted** (#644; cascor#573 P1.1). It wrote
  `_log_level`, which only the `isEnabledFor` guards read, while `_log_at_level` filtered on
  `_level_logger_name`, which was assigned once in the class body and never written again. So a
  guard could open while its record was still discarded. The emit path now reads
  `cls._log_level`. `is_valid_level` passed the boolean `level == level` to the level check, so it
  returned `True` for every input, `"BANANA"` and `None` included; it now checks `level` itself.
  Every live `set_level` call passes `INFO`, so default output is unchanged.
- **`FailedAuthThrottle.check()` inserted every unseen source IP, so its table grew without
  bound** (`src/api/security.py`). `_failures` was a `defaultdict(lambda: (0, 0.0))`, so the
  lookup in the documented read-only `check()` added an entry for each source IP it had not seen.
  `SecurityMiddleware` calls `check()` on every non-exempt request, before authentication, while
  both prunes (the age sweep and the 10,000-entry `_MAX_ENTRIES` cap) run only from
  `record_failure()`. Under open auth or valid-key traffic nothing records a failure, so the table
  grew by one entry per distinct client, forever. `_failures` is now a plain `dict`, and `check()`
  and `record_failure()` both read it with `.get(client_ip, (0, 0.0))`, so only
  `record_failure()` writes. The juniper-service-core and juniper-data copies get the same fix in
  their own repos, each pinned by its own test. Found in the 2026-10-08 flood-3 disposition (juniper-ml
  `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4). Pinned by
  `TestFailedAuthThrottle::test_check_never_inserts_an_unseen_source_ip`
  (`src/tests/unit/api/test_api_middleware.py`): 1,000 distinct IPs through `check()` leave the
  table empty, and one `record_failure()` still makes exactly one entry. With the fix reverted it
  fails with `assert 1000 == 0`.
- **A start-fresh replaced every applied training param with an engine default (F2).**
  `_start_fresh_reset_locked` discards the model. Create-on-start then rebuilt the network from
  `create_simple_config`'s defaults, so a param applied just before the start-fresh was silently
  lost. juniper-canopy's restart modal applies the operator's edits and then restarts, so with
  **Start fresh** on, every edit was dropped. juniper-ml's A-N2 run observed `max_iterations` /
  `output_epochs` / `candidate_epochs` / `max_hidden_units` at 8 / 60 / 40 / 32 before the restart
  and 1000000 / 10000 / 400 / 10 after it.
  - Following the owner's ruling of 2026-09-24 ("apply the edits after the fresh rebuild"), the
    reset now captures the discarded network's params: `get_training_params()` less the derived
    `epochs_max` and the lifecycle's `auto_snap_*`.
  - `start_training` re-applies them to the rebuilt network through `_apply_params_unlocked`, so
    they get the same whitelist, nested setters and atomic rollback as a `PATCH`. The status
    projection is re-synced.
  - The start body's own params still land on top.
  - The weights, topology, metrics and history are still discarded, and snapshots are still
    preserved.
  - `src/tests/unit/api/test_start_fresh_carries_params.py` covers the manager and the
    `PATCH`-then-start-fresh route sequence canopy sends. It was mutation-checked at five sites.
- **A Start that continued the current network bound a wider staged dataset, then refused it
  (F1).** A plain Start continues the current network. `start_training` pads a narrower dataset
  up to it but cannot widen it, because only a live swap grows a network, so the pad step refused
  a wider dataset (409).
  - That refusal fired only after `_reload_dataset` had bound the staged dataset and cleared the
    staged slot. `current_dataset`, `/v1/dataset` and the status then named the new dataset beside
    the previous run's network, status and metrics. A retried Start refused again, with nothing
    left staged for a start-fresh to use.
  - juniper-ml's A-N2 run hit this with `equities` (15 features) over the 2x2 network
    `checkerboard` left behind.
  - Following the owner's ruling of 2026-09-24, `_reload_dataset` takes a `refuse_wider_than`
    bound, and `start_training` passes the continued network's dims. No bound is passed for a
    start-fresh, or when there is no network. A dataset wider on either axis is refused after the
    fetch and before anything is bound. The loaded data, its identity, its annotations and the
    staged slot are left exactly as they were.
  - The refusal opens with a new machine-readable token, `[start_fresh_required]`
    (`_PROJECT_API_START_FRESH_REQUIRED_MARKER`). It names both shapes and says the remedy is
    `start_fresh`. juniper-canopy matches the token to point the operator at its Start fresh
    control.
  - `mnist` (784 features, 10 outputs) and a dataset wider only in its outputs are covered.
  - Inline `X` is unchanged: it still binds first and is refused by the pad step, under the
    2026-09-23 "follow the loaded data" ruling.
  - `src/tests/unit/api/test_start_refuses_wider_staged_dataset.py`, mutation-checked at five
    sites.
- **`src/profiling/logging_utils.py` raised `TypeError` at every emit, and logged at levels cascor
  does not have** (cascor#573, roadmap P1.4 — the "fix the levels" half of owner decision 8). All
  five `logger.log(level, msg)` sites used the stdlib signature, but every cascor call site binds the
  `Logger` CLASS, so the inherited instance method received `level` as `self` and raised
  `TypeError: Logger.log() missing 1 required positional argument: 'msg'`. The module's tests never
  saw it because they inject `MagicMock` loggers, which accept any call. `SampledLogger.trace` also
  passed `5` (VERBOSE's number) and `.verbose` passed `15` (no cascor level) — the third level table
  roadmap P1.4 said must not survive. Emission now dispatches by level NAME through the classmethods
  the `Logger` exposes, falling back to `.log()` for a stdlib logger, and the levels come from the
  one canonical table (`Logger.TRACE` / `Logger.VERBOSE`). New tests drive the real `Logger` class and
  a real stdlib logger; 17 of them fail against the previous module. The fix was checkpointed on
  `wip/logging-p14-adopt-logging-utils` (`1b918e6`, unsigned) on 2026-09-21 and is re-landed here
  unchanged; decision 10 then left the helpers unwired, so no production call site changes.
- **Three version surfaces restated `"0.6.0"` while the distribution was 0.11.0** (#668).
  `juniper_cascor.__version__` was a hardcoded literal -- the value `publish.yml`'s TestPyPI check
  prints on every release; `api.models.common._API_VERSION` was another, and it is the default
  `meta.version` of **every enveloped API response**; `/v1/health`'s source-checkout fallback was
  the third. BUG-CC-04 had moved `api.app` and `/v1/health`'s installed path onto
  `importlib.metadata` and missed these. All three now read `importlib.metadata.version("juniper-cascor")`
  and fall back to the same non-release `"0.0.0-dev"` sentinel `api.app` uses, so no version literal
  is left to bump by hand. **Visible change**: enveloped responses now report the installed version
  in `meta.version` instead of `0.6.0`; no Juniper consumer reads that field.
  `src/tests/unit/test_package_version_single_source.py` pins each surface to the installed version
  and fails if any of the four assigns a release-number literal -- mutation-checked: 5 of its 6
  cases fail against the pre-fix tree.
- **`dataset_shortfall` kept the previous run's annotation, naming a dataset the run was not
  training on** (APD-CASCOR-013). It was written at one line and never cleared -- not on a new
  run, not on reset -- so a run started on inline tensors reported the last staged run's
  shortfall and its `dataset_id`. RULED: the field is named for what THIS run trains on; the
  owner settled how on 2026-09-23 -- **it follows the loaded data**. The annotation is bound
  together with the tensors it describes (in `start_training` for tensors passed as `X`, in
  `_reload_dataset` for a fetch), so a run on inline data reports `null`, a run on a new fetch
  reports that fetch's, and a run on data RETAINED from an earlier fetch -- a plain Stop -> Start,
  or a start after `reset()` -- carries that data's annotation, consistent with `current_dataset`
  (Added, above). Rejected: `null` for a retained-data start because it fetched nothing -- the
  "annotation denies the partial data it trains on" shape APD-CASCOR-007 fixed; also rejected
  earlier, clearing only on a new fetch and documenting the old behaviour. auto-start hands its
  fetch's annotation to `start_training` with the tensors (new keyword-only `dataset_shortfall`);
  an auto-start that fails between fetch and start binds nothing and leaves no annotation. Two
  adjacent paths had the same defect and are fixed with it: a cancelled or refused live swap rolls
  the annotation back with the data (a new `_PreSwapSnapshot` slot), and the fetch itself now
  assigns the annotation only AFTER the artifact is converted and its tensors bound -- it used to
  write it first, so a status poll during conversion showed a shortfall for data never loaded,
  and a refused artifact (a val-less or malformed one) left it describing data that was not.
  Pinned by `src/tests/unit/api/test_shortfall_lifecycle.py` (14 arms, including a poll taken
  mid-conversion through the real fetch path, and the over-correction guards: new inline data
  after a partial run still reports `null`, and so does a retained start on that inline data).
- **The truncatable-generator set is read from juniper-data, not restated in cascor**
  (APD-CASCOR-008). `_PROJECT_API_TRUNCATABLE_GENERATORS` is **removed** from both
  `cascor_constants` trees; the set is derived from juniper-data's `GET /v1/generators` -- a
  generator is truncatable iff its param schema declares `allow_truncation` (today exactly
  `csv_import`, `equities`, `equities_seq`, measured through the real app). RULED 2026-09-09
  (juniper-ml#1864; rejected: widening the `dataset_type` Literal, narrowing the constant). For
  the case that ruling left open, RULED 2026-09-22: **withhold the opt-in and retry** -- if the
  list cannot be read, no deployment opt-in is sent for that request, so juniper-data's own
  default governs, and only a successful read is memoised (rejected: refusing to start, a
  built-in fallback copy, a last-known set on disk). The list is read only when the resolver
  consults it (flag on, caller silent), through a dedicated client bounded to 5 s with no
  retries (the staged path holds the manager lock), and memoised per juniper-data URL; a listing
  in which no entry carries a schema (an older producer, a test double listing `parameters`)
  counts as UNREAD and is not memoised, where it used to be cached as "nothing is truncatable".
  A refusal never tells the operator to set the flag while it is on: after a withheld opt-in it
  says how to retry on each path (a failed start stays staged, a live swap is re-issued,
  auto-start needs a restart), and for a generator the list does not declare it points at the
  request's own `allow_truncation`. On the staged path this removes any startup dependency;
  auto-start is itself a boot-time request that runs once, so there the retry is the operator's.
  Operator docs: the flag's note in `AGENTS.md` and the `dataset_shortfall` entry in
  `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`. Pinned by
  `src/tests/unit/api/test_truncatable_generators.py` plus new arms in the two truncation suites.
- **#678's follow-ups: `dataset_shortfall` stays while any fetched split is loaded, and each
  refusal says what its own path can do** (APD-CASCOR-013, APD-CASCOR-008; from #678's
  post-merge validation). Corrects four statements in the two entries above: auto-start's retry
  is not "a restart" alone; inline tensors no longer always make the annotation `null`; a
  refusal for a generator the list does not declare no longer "points at the request's own
  `allow_truncation`", because it is a plain fetch failure; and a listing counts as UNREAD when
  ANY entry lacks a schema, not only when none carries one.
  - **OWNER RULING 2026-09-24, extending APD-CASCOR-013: "keep while fetched splits stay".**
    `X_val` / `X_test` are retain-on-omit (cascor#582), so an inline train-only start after a
    partial fetch early-stopped on that fetch's val and reported on its test, while
    `dataset_shortfall` and `current_dataset` both said `null` -- the denial APD-CASCOR-007
    removed. The manager now records which partitions the loaded record describes
    (`_described_partitions`, rolled back with a live swap). The fetch's annotation and
    `current_dataset` stay while ANY of its partitions is loaded and clear only once all of the
    fetch's partitions have been replaced, in one start or across several. A new fetch replaces
    everything; `reset()`, a start-fresh and a start on retained data keep it. **Visible
    change**: after such a start `current_dataset` names the fetch, where it read
    `{"dataset_type": null}` (or the in-process spiral's config).
  - **Auto-start's fetch is bound wholesale, as a staged fetch is.** It hands `start_training`
    its tensors with the new `as_fetch=True`, so a partition its artifact lacks is CLEARED
    (cascor#582) instead of kept from whatever was loaded before. Handed in as inline tensors, a
    train+val artifact kept an earlier fetch's test, and with it that fetch's clean record: the
    status said `dataset_shortfall: null` while the log said the run was on a partial dataset.
    An annotation passed without `as_fetch` is now refused, because an annotation describes a
    fetch.
  - **A withheld opt-in's refusal gives its own path's retry, and no other's.** A failed start
    stays staged (start again), a live swap stages nothing (re-issue it), and auto-start never
    runs again on its own (stage the dataset and start, or restart). The remedy listed all
    three, so auto-start was told its dataset was still staged.
  - **Every refusal remedy begins "To accept it,".** canopy's `_producer_detail_from_refusal`
    cuts juniper-data's sentence out at that phrase. #678's WITHHELD remedy began "Retry once",
    so canopy showed about 400 characters of cascor's advice as the producer's own words.
  - **A caller's `allow_truncation: null` gets its own remedy whatever the flag.** With the flag
    off it was told to set `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true`, which cannot change
    the outcome: the deployment default never overrides a key the request carries.
  - **An ordinary 422 is a plain `juniper-data fetch failed: ...`, with no refusal token, flag
    on or off.** A bare `422` in the text used to read as a refusal: it opened canopy's
    partial-data prompt, called the producer inconsistent with the flag on, and named the flag
    with it off. juniper-data answers 422 both for a refusal (`InputTooLargeError`,
    `IncompleteDataError`) and for a request that breaks its declared request schema, and only
    the refusal says "Re-submit with allow_truncation=true". With the flag on, a refusal for a
    generator the list does not declare is plain as well, whatever its text. (This entry first
    gave `spiral` with `n_spirals=1` as the ordinary 422, but juniper-data answers that one 400.
    It also said the check matched the remedy, while the check matched the field names. Both are
    corrected in the next entry.)
  - **A listing in which ANY entry lacks a schema is a failed read.** Skipping the entry
    memoised a smaller set for the life of the process, and that generator was never sent the
    opt-in again.
  - **The shortfall is logged once its data is bound, on both fetch paths.** A refused artifact
    no longer leaves "this run is training on a partial dataset" in the log. A descriptor the
    log cannot format is reported rather than raised, because the data is already loaded.

  Pinned under `src/tests/unit/api/`. `test_shortfall_lifecycle.py` drives the real fetch: a
  train-only, train+val, train+test or all-three inline start after a partial fetch; the three
  splits replaced across several starts; a new fetch; `reset()` and a start-fresh; a promoted
  val split; inline tensors beside a staged fetch; a caller's own fetch; and the swap rollback
  of the new slot. `test_auto_start_shortfall.py` covers auto-start's wholesale bind and the
  listing client's URL, key, timeout and retries, which nothing pinned.
  `test_truncatable_generators.py` covers the stance and remedy arms, and
  `test_allow_truncated_datasets.py` runs every refusal branch through a verbatim copy of
  canopy's parser.
- **#688's validation follow-ups: a juniper-data 400 is not a shortfall refusal, a caller's
  `allow_truncation` means what juniper-data takes it to mean, and auto-start's shortfall is
  logged only for data its start goes ahead on** (APD-CASCOR-008, APD-CASCOR-013; from #688's
  post-merge validation, which ran against a real juniper-data main server).
  - **A refusal is recognised by juniper-data's remedy sentence, "Re-submit with
    allow_truncation=true", and by its 422 when the error carries a status.** The check matched
    the field names `allow_truncation` and `incomplete_rows`, and juniper-data's 400s name the
    field they reject. So a 400 for `incomplete_rows='keep'` or for a blank `allow_truncation`
    carried the refusal token and opened canopy's partial-data prompt, and with the flag off it
    told the operator to set the flag. juniper-data-client 0.5.0 puts the status on
    `status_code`. An older client's error carries none, and the sentence alone decides. The
    status matters because a 400 echoes the value it rejects, so a value that quotes the
    sentence puts the sentence in a 400.
  - **A blank `allow_truncation` is not a deferral.** Only `null` defers to the producer.
    juniper-data rejects a blank string with a 400 ("Input should be a valid boolean"), so the
    resolver no longer records it as the caller deferring. Its failure no longer says the
    request "deferred to the producer".
  - **A caller's `allow_truncation` is read exactly as juniper-data reads it.** juniper-data
    types the field `bool | None` under pydantic's lax coercion, in `EquitiesParams` (which
    `EquitiesSeqParams` inherits) and `CsvImportParams`. That accepts twelve strings,
    ASCII-case-insensitively and without stripping, plus the numbers 0 and 1, and rejects
    everything else. This service fell back to truthiness and stripped whitespace. So `"f"` and
    `"n"`, which juniper-data reads as `false`, read as an opt-in: a caller that refused a
    partial dataset that way was recorded as accepting it, and the refusal came out as a plain
    fetch failure with no remedy. A value juniper-data rejects (`"maybe"`, `2`, `" true"`) is
    now no stance, as a blank string is.
  - **Auto-start's shortfall is logged once a staged dataset has had its turn.** If an operator
    staged a dataset during auto-start's boot window, `start_training` logged auto-start's
    partial fetch as soon as it bound it. The staged fetch then either replaced it, so the log
    and the status (`dataset_shortfall: null`) disagreed, or refused the start, so the log
    described a run that never began. The annotation is now logged only if it is still the one
    bound when the staged fetch is done. The staged fetch logs its own.
  - **The F1 refusal says "The staged dataset was not loaded"** where it said "Nothing was
    loaded". A start that also carried inline tensors has bound them by then.
  - The entry above is corrected where it described the check and gave `n_spirals=1` as a 422,
    and its list of corrected statements is now complete.

  Pinned under `src/tests/unit/api/`. The refusal arms now use juniper-data's own texts,
  captured from a real server. The stand-in "HTTP 422 allow_truncation" no longer reads as a
  refusal, so an arm left on it would pass without reaching its branch. New arms cover the 400s
  in both flag positions, with and without a status, and the blank string. They also cover a
  staged fetch that replaces, or refuses, a fetch handed in, and a refusal after an inline train
  start, which must leave alone the partitions the record stands on. Two more pin a clean
  auto-start fetch after a partial one, and the route's `spiral` while a fetch's splits are
  loaded. Every spelling of `allow_truncation` is checked, in both polarities, against a table
  measured from juniper-data's own params classes, and against pydantic's lax `bool | None`.
  Mutation-checked at 95 sites, all killed. They include the validation's NV1, NV2, NV3 and NV5
  verbatim, NV4 as the two clauses of the new check, and each of the twelve spellings flipped
  to the other polarity and dropped.
- **`lockfile-update.yml` regenerated `requirements.lock` alone, so every dependency bump drifted
  `requirements-cpu.lock`** -- the container image's lock, which is *derived* from the GPU lock via
  `--constraint requirements.lock`. Nothing reported it: the CI check asserts only that every image
  dependency is **present** in the CPU lock, never that its version agrees with the GPU lock's.
  juniper-cascor-worker shows where that ends up -- its two locks had diverged on 10 of their 19
  shared pins by 2026-09-09 (`setuptools` 70.2.0 vs 83.0.0, `numpy` 2.4.4 vs 2.5.1, ...) with every
  build green. The workflow now re-derives the CPU lock in the same run, reading the torch pin from
  the `Dockerfile`'s `ARG TORCH_VERSION` and **refusing** if the lock header's recipe disagrees with
  it, preserving the hand-written header uv would otherwise overwrite, and committing **both** locks
  in the **same** GitHub-signed commit so the derived pair can never land half-updated. Follow-up 6c
  of juniper-ml
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`.
- **`requirements-cpu.lock` carried an author's absolute home directory** on 18 of its `# via`
  annotation lines (`/home/pcalnon/Development/python/Juniper/juniper-cascor/pyproject.toml`), an
  artifact of the hand-compile that created it. Regenerated from the repo root so the annotations are
  relative. **Comment-only: all 53 pins are unchanged**, verified by diffing the pin lines. Doing it
  here rather than leaving it to the first automated run keeps that run a no-op instead of an
  unreviewed 18-line rewrite.
- **A broadcast that could not be serialized dropped every `/ws/training` subscriber, silently and
  without closing a socket (F-CASCOR-004).** Starlette's `send_json` serializes with stdlib
  `json.dumps` and no `default=`, so a NumPy scalar in a payload raised `TypeError` inside *every*
  client's send; `_send_json` swallowed it with no log, and `broadcast` called `disconnect()` on each
  subscriber in turn -- which forgets a socket but never closes it. On 2026-09-08 both canopy relays
  were dropped 1-3 ms after `ResumeReady -> Started` by a `state` frame carrying the NumPy-typed
  tunables of F-CASCOR-003, and sat half-open for the rest of the run while the heartbeat pings kept
  them looking healthy. juniper-cascor#632 removed that trigger; this removes the mechanism.
  `WebSocketManager` now attributes a failure to what caused it. An **unserializable message is the
  message's fault**: it is detected once per broadcast, before seq assignment and the fan-out,
  logged at ERROR (message type, exception, and on Python >= 3.14 the path to the offending value),
  counted, and skipped -- no subscriber is dropped or closed, no seq is consumed, nothing enters the
  replay buffer. There is deliberately no coercion: the producer must emit plain Python types.
  `send_personal_message` refuses such a message the same way; it returns `False`, as it did before,
  but now with the ERROR line and the counter instead of a silent send failure. **Behaviour change
  for oversized messages:** because the check runs before chunking, a message over
  `ws_max_message_size_bytes` (60,000) holding a NumPy scalar or a lone surrogate is now refused. The
  chunker sizes with `json.dumps(default=str)`, so such a message used to be delivered, with the
  NumPy value retyped (`np.int64(3)` arrived as the JSON string `"3"`) and the surrogate escaped. The
  broadcast most likely to exceed the threshold, the topology snapshot, is built from native types
  (`get_topology`). A **per-connection failure** (a send that raises or times out) drops only that subscriber,
  and now **closes** its socket (code `1011`, errors suppressed) as well as forgetting it. The
  broadcast waits at most the send timeout for that close, via `asyncio.wait`, which neither cancels
  it (uvicorn's legacy `websockets` protocol swallows a cancellation mid-handshake) nor shields it (on
  Python 3.14 a timed-out `wait_for(shield(...))` reports the close's later failure as an asyncio
  ERROR, "... exception in shielded future"). `_send_json`'s generic failure branch logs a WARNING.
  Once the server has closed the socket, the `/ws/training` receive loop drains until the ASGI server
  reports the disconnect, rather than returning. uvicorn's sans-I/O protocol (what `ws="auto"`
  selected at uvicorn 0.53.0 / websockets 17.1, the pins when this was measured) holds the close frame while its write
  buffer is full, and closes the transport as soon as the app returns. A handler that returned on
  the peer's next frame therefore left a slow reader with an abnormal `1006` instead of the `1011`
  frame. Draining also keeps a frame in flight from ending the handler with Starlette's
  `RuntimeError`, and the handler's `finally` -> `disconnect()` stays idempotent. A peer that never
  reads again still never receives the close frame: its close waits until the connection itself
  ends, which is no worse than before, when such a peer was never closed at all.
  New counter: `unserializable_messages_total` on `GET /v1/metrics/transport` and
  `cascor_ws_unserializable_messages_total{type}` in Prometheus; such a message no longer adds to
  `send_failures`, which is now per-connection failures only. Tests:
  `src/tests/unit/api/test_ws_broadcast_fault_isolation.py`; wire check:
  `util/ad-hoc/2026-09-22_f_cascor_004_live_ws_probe.py`. Ledger: juniper-ml
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, entry F-CASCOR-004.
- **`dataset_shortfall` now says WHO accepted the partial dataset — and no longer denies an
  acceptance it is annotating.** `accepted_via_allow_truncated_datasets` was the raw value of this
  service's own setting. Two live paths made it read `false` on a run training on partial data:
  the caller supplying `allow_truncation: true` in the staged params (the path canopy's options 1
  and 2 use, with the service flag off), and juniper-data accepting on its **own** deployment
  opt-in when the request is silent (since juniper-data#418 a client can refuse it with
  `allow_truncation=false`) — while nothing was sent from here. The annotation is additive: `accepted_by_this_run` (an opt-in went on the wire from this
  side), `acceptance_source` (`request_params` | `allow_truncated_datasets` | `producer`), and the
  original field kept with its literal meaning — true only when THIS service's setting supplied
  the opt-in. The `summary` sentence and the training-log line carry the same clause.

  Found by round-37 handoff validation in juniper-ml. The producer's descriptor carries no
  authority field, so the source is derived from what this run **sent**, and `producer` is
  inferred when nothing was sent and a shortfall arrived anyway. Pinned by three arms of
  `TestShortfallIsPollable` that run `_reload_dataset` up to the annotation and stop.
- **A caller's explicit `allow_truncation: false` now gets the refusal message, not a bare
  "fetch failed".** `_describe_dataset_fetch_failure` keyed the remedy off the service **setting**;
  with the flag on and the caller refusing (honoured since cascor#624), the producer's 422 came
  back as `juniper-data fetch failed: …` with no remedy — in exactly the case the remedy exists
  for. It now keys off the stance that went on the wire, and tells a caller that refused to
  re-send `allow_truncation=true` with `incomplete_rows=accept|drop` rather than pointing them at
  a service knob their own value overrides. The staged value is read as a tri-state
  (`_as_bool_stance`), because the params cross a JSON boundary and `bool("false")` is `True`.
- **The refusal message opens with a machine-readable token, `[dataset_shortfall_refused]`**
  (`_PROJECT_API_SHORTFALL_REFUSAL_TOKEN`), so a consumer can recognise the class without
  matching prose; canopy's three-way partial-data prompt keys on it. It rides inside the 409
  `detail` because that is the one channel every transport carries — the WS control path
  forwards `error` as a bare string. An ordinary outage does not carry it.
- **Correction to the 0.11.0 `dataset_shortfall` entry: it does NOT ride the WS training
  stream.** `get_status()` is read by the stream only in the one-shot `initial_status` frame at
  connect; the broadcast set has no status frame. A client already connected when
  `_reload_dataset` sets the field never sees it over WS — it polls `/v1/training/status`
  (canopy does, at 1 Hz). The manager comment that made the same claim is corrected here.
- **`util/check_image_cpu_only.py` let the `cuda-*` family through, and the merge job's
  digest-identity step accepted any number of linux images per pushed digest.** The 2026-09-07 CUDA
  worker image carried `cuda-toolkit`, `cuda-bindings` and `cuda-pathfinder` next to the `nvidia-*`
  wheels and `triton` -- the very family `requirements.lock` pins outright here -- and the census
  forbade only the latter two families, so an image with torch `X+cpu` plus those three would have
  read `cuda_stack=0`. It now forbids `nvidia-*`, `cuda-*` and `triton`. `publish-image.yml`'s merge
  job also asserts that each pushed per-arch digest resolves to exactly **one** linux image whose
  architecture is the digest file's name, so a multi-platform index could never count an image the
  census did not run on as verified. Both pinned by `src/tests/unit/test_dockerfile_cpu_torch_pin.py`.
  Follow-up 6a of juniper-ml

  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md`.
- **`CI — juniper-cascor-model` was RED on `main`, and the fix that broke it did not work
  either.** The four `_PROJECT_API_SHORTFALL_*` constants added on 2026-09-09 were never listed in
  `cascor_constants/constants_api/constants_api_defaults.py`'s `__all__`, so CodeQL reported them as
  unused globals; the remedy added a **second** `__all__` in the middle of the file, and only to the
  `juniper-cascor-model/` mirror. That is wrong twice. It broke `tests/test_drift.py`, which requires
  the extracted tree to be byte-identical to `src/` — red on `main` from `44dafe0` onward. And it had
  no effect on the finding it was meant to silence, because the module already ends with its own
  complete `__all__`, so the mid-file binding is simply replaced at import time by the one at the
  end, which still did not name the four constants. The stray block is gone and the four names are
  in the real `__all__`, in its existing alphabetical order, in **both** copies. Nothing star-imports
  this module (`constants_api/__init__.py` names every symbol explicitly), so `__all__` here is
  documentation and a CodeQL signal, never behaviour: no import changes. Verified by the drift suite
  (3 passed, previously 1 failed / 2 passed) and by `test_allow_truncated_datasets.py` (28 passed).
- **An auto-started run carried none of the partial-data contract: it forwarded no truncation
  opt-in, annotated nothing, and swallowed its failures where nothing could see them.**
  `_auto_start_training` (`src/api/app.py`) calls `create_dataset` and `download_artifact_npz`
  itself instead of going through `_reload_dataset`, so all three behaviours the staged path
  gained across cascor#621 / cascor#624 / cascor#633 were simply absent here. Concretely: a
  deployment with `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true` auto-starting on a truncatable
  generator still sent no `allow_truncation`, took the producer's 422, and came up healthy with no
  training — while the knob that would have allowed the fetch was already on. And a run that did
  receive a partial dataset reported `dataset_shortfall: null`, indistinguishable over the API
  from one that got everything it asked for, so its score carried no mark of the data behind it.

  Both paths now resolve the stance through **one** shared helper,
  `TrainingLifecycleManager._resolve_truncation_stance`, because a second, simpler reader is how
  these two drift — this same function had already re-read the artifact keys itself once and
  handed the run no held-out data at all. The deployment flag stays a DEFAULT and never an
  override (an `allow_truncation` in `JUNIPER_CASCOR_AUTO_DATASET_PARAMS` wins, in either
  polarity, so "send neither parameter and fail" stays reachable), and the pollable annotation and
  the training-log line are written from the same `acceptance_source`. Failures are still
  swallowed — the service must come up healthy either way — but a shortfall refusal is now logged
  at ERROR with the remedy the producer's 422 cannot know, and every give-up path records its
  reason on the new `auto_start_failure` status field (see Added). Round-38 follow-ups 1 and 2,
  filed in cascor#624's PR body and confirmed against source 2026-09-08. Pinned by
  `src/tests/unit/api/test_auto_start_shortfall.py` (23 arms).
- **`--allow-truncated-datasets` is inert on `src/main.py`'s own run, and now says so.** The flag
  does nothing but export `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`, and the generator `main.py`
  reaches is hardcoded `spiral` — which juniper-data synthesises server-side and always delivers
  in full, and which is not one of the truncatable generators, so no shortfall can arise here for
  the flag to act on. (Note the reason: `main.py` **does** fetch from juniper-data, and refuses to
  start when `/v1/health` is unreachable. It is the generator that cannot be partial, not the
  data path that is absent.) The readers are the SERVICE this process may launch and the API's
  dataset paths.
  The flag is deliberately **kept**, because that export is exactly how it reaches a launched
  service; what changed is that its `--help` text now names the surfaces it does and does not
  affect, and passing it emits one WARNING saying the same. An accepted flag that silently does
  nothing is worse than a rejected one: the operator concludes the shortfall was allowed, and
  nothing ever asked. The stanza moved out of `if __name__ == "__main__":` into
  `apply_allow_truncated_datasets()` so the warning is reachable by a test at all — code under
  `__main__` cannot be called, and an untested warning is one that stops firing without anyone
  noticing. Round-38 follow-up 3.

### Security

- **cascor picks up the two shared security patches**: `requirements.lock` and the image's
  `requirements-cpu.lock` each move `juniper-observability` 0.4.0 -> 0.4.1 and
  `juniper-service-core` 0.7.0 -> 0.7.1, and nothing else. observability 0.4.1's shared
  `configure_sentry`, which `src/api/observability.py` delegates to, no longer sends frame-local
  variables to Sentry, and they could hold the real API key. (The CLI's own `sentry_sdk.init` in
  `src/main.py` is covered by its own entry below.) service-core 0.7.1 fixes `APIKeyAuth` and
  `FailedAuthThrottle`; cascor's own copies in `src/api/security.py` carry the same fixes (the
  non-ASCII entry below, and the `FailedAuthThrottle.check()` entry under Fixed), so that pin is
  consistency with the sibling services. Both locks were regenerated with `--upgrade-package` for
  the two packages only: 73 pins in the GPU lock, which its freshness gate reproduces, and the CPU
  lock, derived under `--constraint requirements.lock` with its header restored. The wheel's
  floors follow in this release: `juniper-observability>=0.4.1` and
  `juniper-service-core>=0.7.1,<0.8.0`, so a pip install over an older environment upgrades both.
  (The locks moved in #711; the floors ride in the release proposal, because a `pyproject.toml`
  change on any branch but `release/` triggers `lockfile-update.yml`'s full `--upgrade` regen.)
- **`.dockerignore` exclusions now hold below the build-context root** (#661). Its patterns were
  root-anchored, so `cascor_snapshots/` never excluded `src/cascor_snapshots/`, which sits under
  the `COPY src/` that ships. That directory held 766 local `.h5` snapshots, each carrying a
  plaintext multiprocessing authkey, and a local `docker compose build` would have baked them in.
  No published image was affected: `juniper-cascor:0.11.0` was pulled and inspected, and holds no
  `.h5`. Every pattern now has a `**/` twin, keys (`*.key`, `*.pem`), `secrets/` and `.env*`
  (except `.env.example`) are excluded, and `publish-image.yml` runs the new
  `util/check_image_no_secrets.py`.
- **`APIKeyAuth.validate` checks every configured key instead of stopping at the first match**
  (#659; APD-CASCOR-005). Each compare was already constant-time; only the walk short-circuited, so
  the time taken depended on where the matching key sat. The result is identical for every input.
- **A non-ASCII `X-API-Key` is a 401, not a 500 that hands Sentry the real key**
  (`src/api/security.py`). `APIKeyAuth.validate` compared `str` with `hmac.compare_digest`, which
  raises `TypeError` when either side holds a non-ASCII character. Starlette decodes header bytes
  as latin-1, so any byte above 0x7f reaches `validate` as one. The validation of
  juniper-canopy#683 (2026-09-24) sent an anonymous `X-API-Key: \xa0`, which both uvicorn parsers
  pass. It had three consequences:
  - The `TypeError` escaped `SecurityMiddleware`'s `except HTTPException`, so the caller got a
    **500** instead of a 401. The `/ws/*` handshake calls the same `validate` from
    `ws_authenticate`, and raised instead of closing 4001.
  - Only a 401 records a failure, so a flood of such keys was **never throttled** by
    `FailedAuthThrottle`.
  - Under Sentry's default `include_local_variables=True`, the error event carried the loop's
    `candidate`, the **real configured key**.

  Both sides are now compared as UTF-8 bytes. The encoding uses `surrogatepass`, the one built-in
  error handler that is both total and injective: a lone surrogate (from a JSON-decoded
  `JUNIPER_CASCOR_API_KEYS`, say) encodes instead of raising, and no two distinct strings share
  bytes. So `validate` matches exactly when the strings are equal. `surrogateescape` raises on
  `"\ud800"` and maps `"\xe9"` and `"\udcc3\udca9"` to the same bytes. juniper-ml's
  `tests/test_service_fork_drift.py` markers (`blank-api-key-filter`,
  `nonshortcircuit-key-compare`) are unchanged. Owner ruling "Fix everywhere now" (2026-09-24),
  landing the same compare in juniper-service-core and juniper-data.
  Pinned by 62 new tests in `src/tests/unit/api/test_api_security.py`. They cover the non-ASCII
  mismatch, a 7x7 equality matrix built to separate the candidate encodings, and the
  `Request`-level 401. `TestNonAsciiApiKeyThroughTheApp` drives `create_app` with auth on and
  checks three things: a raw-byte header is a 401, ten such failures earn a 429, and
  `/ws/training` closes 4001. Reverting to the `str` compare fails 61 of them: the HTTP tests with
  `assert 500 == 401`, the handshake and the unit tests with the `TypeError`. `surrogateescape`
  fails 15 and strict UTF-8 fails 33.
- **The CLI's own Sentry init no longer captures frame-local variables** (`src/main.py`). The
  bootstrap `sentry_sdk.init` now passes `include_local_variables=False`, for the same reason: the
  SDK's scrubber redacts locals by name, and `candidate` is not a name it knows. The service path
  (`src/api/app.py` -> `api.observability.configure_sentry`) delegates to juniper-observability,
  which carries the same setting from 0.4.1. This release delivers it: both locks pin 0.4.1 (#711)
  and the floor is `juniper-observability>=0.4.1`. Pinned by
  `src/tests/unit/test_main_sentry_no_local_variables.py`, an AST check of the call's keywords
  with negative controls. Removing the keyword, or passing `True`, fails it. Mutation checks:
  juniper-ml's `util/ad-hoc/2026-09-24_bytes_compare_sentry_locals_verify.py`.

### Documentation

- **`Sequence Safety` and CodeQL's `Analyze (python)` are REQUIRED checks; the docs called both
  advisory.** The `main` ruleset (`juniper-cascor-rules`, id `15081045`) has required
  `Sequence Safety` since 2026-08-19, and `Analyze (python)` was already required when cascor#583
  documented CodeQL as a soak (2026-08-29). The ruleset's `code_scanning` rule also blocks a merge
  on a CodeQL alert at `error` or a security alert at `high` or above. cascor#643 corrected only
  `sequence-safety.yml`'s header block. Now corrected:
  - `AGENTS.md`: the workflow-table rows for both checks, the CodeQL section, and the Sequence
    Safety section's "Everything is **ADVISORY**". That section now says a green Quality Gate does
    not mean mergeable (`sequence-safety.yml` is standalone, and a `needs:` entry can only name a
    job in the same workflow), gives the ruleset query, and says the owner labels green the
    required context while only an `Allow-Symbol-Loss:` / `Allow-Docs-Rewrite:` trailer waives a
    finding in the post-merge `main-verify.yml`.
  - `docs/ci_cd/MANUAL.md` and `docs/ci_cd/REFERENCE.md`, which cited a Sequence Safety
    "convention" as the precedent for an advisory CodeQL; `docs/ci_cd/QUICK_START.md`;
    `docs/ci_cd/BRANCH_PROTECTION.md`, which also gains a pointer that the live ruleset requires
    more than its table lists; `docs/DEVELOPER_CHEATSHEET.md`; the tree comments in
    `docs/REFERENCE.md`; and the CodeQL "soak" labels in `docs/INDEX.md` and
    `docs/DOCUMENTATION_OVERVIEW.md`.
  - Comments only: `sequence-safety.yml` (its juniper-ml reference and concurrency note),
    `main-verify.yml` (now says it is not a PR status check, and how a finding is waived there),
    and the "advisory workflows" wording in `src/tests/unit/test_sequence_safety_retired.py`. No
    trigger, step, pin or job name changed.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-cascor/blob/v0.12.0/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-cascor_v0.12.0.md`
