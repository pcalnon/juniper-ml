# juniper-canopy v0.9.0 – :lock: SECURITY RELEASE (MINOR)

**Release Date:** 2026-10-17
**Release Type:** MINOR (security-bearing)
**Priority:** High: upgrade every juniper-canopy deployment
**Package Affected:** juniper-canopy

---

This is a minor release of `juniper-canopy` that carries four security fixes:

- **An outbound key with padding, a line break or a non-ASCII character is refused where it is read.** No transport error reaches a caller any more. A padded juniper-cascor key had reached an anonymous caller in a 409's `detail` (the juniper-canopy#683 validation).
- **A padded `CANOPY_API_KEY` no longer reaches the logs or Sentry** through the dashboard's self-calls.
- **`APIKeyAuth` compares every configured key without short-circuiting, and drops blank entries.** A whitespace-only `CANOPY_API_KEY` env var now disables auth, the posture canopy documents for no key. Read the Security section before upgrading a deployment that sets one.
- **The shared juniper-observability 0.4.1 and juniper-service-core 0.7.1 patches** are picked up, now as floors.

It also:

- runs recurrence fits by operation identity: a timed-out fit is followed, and a busy 409 names its holder;
- sends a recurrence fit the registry seed plus the operator's edits only, with a preview before Start;
- shows the recurrence service's 4xx detail and version;
- fixes the replay player against cascor;
- fixes the status-bar and metrics polling;
- has 33 Fixed entries in all.

The image's `requirements.lock` pins juniper-data-client **0.6.0** (juniper-canopy#750), so canopy's advisory second check on generator loads runs the W1.4 `validate_npz_contract`.

The owner rated this release **High**: two of the exposures handed a real key to a caller or to the logs once a key was mis-set.

---

## Security Impact (High)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-canopy` |
| **Fixed in** | 0.9.0 |
| **Vulnerability class** | Insertion of sensitive information into a log file ([CWE-532](https://cwe.mitre.org/data/definitions/532.html)): a padded inbound or outbound key quoted by an HTTP client's refusal, and Sentry frame locals. Generation of an error message containing sensitive information ([CWE-209](https://cwe.mitre.org/data/definitions/209.html)): transport text that held a key in API bodies and WebSocket acks. Observable timing discrepancy ([CWE-208](https://cwe.mitre.org/data/definitions/208.html)): `APIKeyAuth`'s short-circuiting key compare |
| **Advisory** | None. Internal findings: the juniper-canopy#683 validation (2026-09-24), #660 / #678 and the Cursor flood-3 evaluation (2026-10-08). There is no CVE or Dependabot alert |

---

## Changes in v0.9.0

### Added

- **The recurrence model's version is shown (W1.7, display half; F-C8).** canopy#722 made the version the service
  reports, but `refresh_model_versions` had no production caller. Now the lifespan asks a configured recurrence
  service at startup, and a selection of the recurrence model asks again while its backend is live. Both lookups run
  in the background (`asyncio.to_thread`), and a refresh in flight is not repeated, so no page, selection or read
  waits on the service. `GET /api/selection` and `POST /api/model/select` gain an optional `version`, present only
  when a service reported one. The sidebar's Active line shows it: `Active: Recurrence (LMU) · version 0.5.0`.
  Tests: `src/tests/regression/test_recurrence_version_display.py` (20). The displayed version comes from a fake
  service, the selection answers while the lookup is blocked, and the lifespan starts the refresh and abandons an
  unfinished one at shutdown.
- **Regression suites harvested from the Cursor flood-3 test PRs** (canopy#699, #701, #704, #707, #715,
  #718, #719, #720, #724, #727, #728): 15 new test files over the replay echo, shape and control-result
  guards; the recurrence 4xx-detail and status-bar cut bounds; version lookup, `Retry-After` and the
  restored model; the LMU dataset-spelling refusal and dataset-schema falsy seeds; the stage-payload and
  restage falsy edges; the image credential scan and serve-check driver; and the open-PR budget alarm,
  sequence-safety label hatch and post-merge verdict shells. Each was re-run on `main` and
  mutation-checked against the code it pins, and corrected where the head was wrong: #715 replaced
  `time.monotonic` / `time.sleep` globally without restoring them, which failed five unrelated tests on
  every CI leg; #704 pinned the 401/403 text that #722 replaced. Test-only.
- **Operator runbook for the Snapshots Replay tab index contract (docs for canopy#697).**
  Cascor's range `end` is exclusive and `snapshot_window.end_epoch` is a history length; the
  scrubber and range slider are inclusive. `render_session` writes those slider values, and
  they are Inputs of `queue_control`, so without its equality guard every paint would queue a
  control; since #697 the guard returns `dash.no_update`. Canonical page:
  [AGENTS_REFERENCE.md § Replay index contract](https://github.com/pcalnon/juniper-canopy/blob/v0.9.0/docs/AGENTS_REFERENCE.md#replay-index-contract).
  Pins: `src/tests/unit/frontend/test_replay_range_end_and_echo.py` (13 tests, landed with
  #697). `notes/development/REPLAY_V2_FAQ.md` no longer says the player shows no session
  against cascor (F-CANOPY-059 was fixed in canopy#694), and its `curl` check now reads
  `.data.session.weights_available` and `.data.session.weight_sampling`.
- **Operator runbooks for a refused recurrence fit, the in-sample regression card, and the
  recurrence key, rate limit, restored model and service version** (documenting canopy#702 and
  canopy#722). `docs/AGENTS_REFERENCE.md` § Recurrence fit refusal and in-sample scores covers the
  4xx `detail` suffix (300 characters; a validation `input` is omitted), the 5xx omission, the
  status-bar hover (480 characters), and the in-sample card. § Recurrence key, restored model, and
  service version covers the 401/403 remedy that names `JUNIPER_CANOPY_RECURRENCE_API_KEY` and
  `JUNIPER_CANOPY_RECURRENCE_API_KEY_FILE`, the 429 `Retry-After` wait, `restored` counting as a
  model, and the service-reported model version. Pointers in `docs/REFERENCE.md`,
  `docs/DEVELOPER_CHEATSHEET.md` (procedures, the three recurrence variables, troubleshooting
  rows), `docs/QUICK_START.md` (Issues 11 and 12), `docs/USER_MANUAL.md`,
  `docs/DOCUMENTATION_OVERVIEW.md`, and the testing guides. Documentation only.
- **Operator runbook for a Start refused because the staged dataset is wider than the network
  (F1, F2).** The behaviour shipped in canopy#681. This documents the `[start_fresh_required]`
  alert, why a cascor that lacks the marker gets no second wording, what **Start fresh** keeps
  (applied parameters, snapshots) and discards (the model, retained metrics and history), and the
  confirm order (re-stage, apply parameters, then `POST /api/train/restart`). Canonical section:
  `docs/AGENTS_REFERENCE.md` § Start-fresh refusal (F1, F2); operator steps in `docs/USER_MANUAL.md`
  and `docs/QUICK_START.md`; test commands in `docs/testing/`.
- **Operator runbook for the sidebar model summary (X11; documents canopy#680).** `nn-model-summary`
  says **Active** only after a round-trip names a `backend` that serves the selection; first paint and
  a failed `GET /api/selection` read `backend status unknown`. Canonical section:
  `docs/AGENTS_REFERENCE.md` § Sidebar model summary (X11); pointers in `docs/REFERENCE.md`,
  `docs/DEVELOPER_CHEATSHEET.md`, `docs/QUICK_START.md` (Issue 14) and `docs/USER_MANUAL.md`.
- **CI/CD documentation for the image serve-and-version gate, the Claude Code workflow, and Dependabot
  floors versus the lockfile regen.** `docs/ci_cd/CICD_REFERENCE.md` gains § Container image
  (`publish-image.yml`, `util/check_image_serves.py`) and § Claude Code workflow (`claude.yml`);
  `docs/ci_cd/CICD_MANUAL.md` gains the matching runbooks and rewrites § Runbook: Dependabot lockfile automation:
  Dependabot's floor edit lands in `conf/requirements_ci.txt`, while `lockfile-update.yml` compiles
  `pyproject.toml` with `--upgrade`. `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md`'s install pattern now
  matches `ci.yml`, which installs `pyproject.toml` extras and not `conf/requirements_ci.txt`
  (since canopy#650).
- **The publish path asserts that the image serves, and that it is the version it is tagged**
  (`util/check_image_serves.py`, new; `publish-image.yml`). The existing checks cover what the image
  contains and that `juniper_canopy` imports. Neither can see a stale version. The worker's 0.5.0 and
  0.6.0 images imported fine while their package reported `0.4.0`, and cascor's 0.11.0 stamps
  `meta.version: "0.6.0"` on every enveloped response. The script starts the image as deployed, with
  its own `CMD`. With no backend reachable, the dashboard runs in demo mode and still serves
  liveness. It requires liveness on :8050, plus one version across the installed metadata,
  `juniper_canopy.__version__` and the `/v1/health` body. On a release, that version is the one in
  the **tag**. An absent `__version__` fails: the ecosystem's class-2 sweep once scored that shape as
  a pass. The check runs on the PR arm against the image just built, and on the publish path against
  each pushed digest before the digest is exported. It passes the published `juniper-canopy:0.8.1`.
  The script is the same one the four other image repos carry.
  `src/tests/unit/test_check_image_serves.py` (new, 22 tests) needs no Docker. This is item 5 of the
  juniper-ml container-registry rollout handoff.
- **Stage, live-swap and set-params requests now carry the dashboard's `nn_model`, and a stale or
  incompatible request fails closed (FR9; the `nn_model` mirror clause of canopy#368).**
  `current_nn_model` is server state, while `model-selection-store` is per-tab memory. A second
  tab, or one opened before another client changed the model, holds a stale selection, and a
  request made under it used to land on whichever backend was live. For example, a stale CasCor
  tab could stage a rank-2 dataset into the recurrence backend, which failed only at *fit* time.
  - `nn_model` is an **optional** field on both `StageDatasetRequest` and `SetParamsRequest`.
    #368's own guardrail says a field absent from a request model is silently dropped, so the key
    had to exist before anything could be checked.
  - `/api/stage_dataset`, `/api/live_dataset_swap` and `/api/set_params` answer:
    - **409** when the mirror names a model other than the server's selection;
    - **422** for an unknown model;
    - **422** on staging or live-swap when the dataset is known and that model cannot use it.
  - A request without the key behaves exactly as before, so older clients and `curl` are
    unaffected.
  - The key is a routing field. It never reaches a backend, and it is kept out of the
    applied-params store the dirty tracker reads.
  - The sidebar's Apply Dataset and Apply Parameters send it, and so do the live-swap button and
    the restart modal's re-stage and parameter apply. Each of those reads `model-selection-store`
    as State, so a stale tab's swap or edited restart is refused before anything moves.
    `/api/train/restart` itself carries no model identity, so a restart with nothing edited sends
    no mirror and is not checked. The server accepts the key's absence.
  - `src/tests/regression/test_request_nn_model_mirror.py`, mutation-checked at four sites.
- **The selection survives a page reload: both selectors now hydrate from the backend (design
  PR 2, §4.10; guardrails G7 and Y3).** The selection had no read side on either axis.
  `model-selection-store` is memory-scoped and seeded with the default model, while
  `current_nn_model` lives in the server — so every reload showed the seed over whatever was
  running. With Recurrence selected over an unconfigured service, the sidebar read *"Active:
  CasCor"* and left Start enabled against a selection the server then refused (Y3). The dataset
  dropdown showed its layout default over whatever the backend had staged or loaded, which files a
  benchmark result against the wrong dataset.
  - **`GET /api/selection`** is new. It returns the recorded model in `POST /api/model/select`'s
    shape, plus the backend's dataset: `pending` (it wins, because Start consumes it), `loaded`,
    `none` or `unknown`.
  - **Every backend reports `current_dataset`.** cascor carries it on `/v1/training/status` since
    juniper-cascor#676, and `ServiceBackend` passes it only when cascor sent it, so an older cascor
    reads *unknown*, not *nothing*. The recurrence backend records the dataset of its latest fit.
    The demo simulator reads its dataset's `source` stamp, which the two spiral builders now set too.
  - **At mount, `select_model` hydrates the model stores**, as their only writer. The gate then
    gates the hydrated dataset against the hydrated model.
    - The gate's `params-init-interval` Input is **removed**. It scheduled a second first-paint
      pass against the seed model beside the hydrated one. The renderer's dedup let the hydrated
      pass win in the end, but a seed pass that had already completed painted a state gated against
      the wrong model first — the option list greyed for CasCor on a Recurrence reload.
    - Its first-paint pass now comes from the hydration's store write, which happens on every mount,
      read failure included, so N7's availability gate still applies at first paint.
  - `⊥`-at-mount (OQ-N2) is **not** part of this change. Sources that name nothing the dropdown can
    show keep the layout seed until it lands, because D-N10 requires this hydration first.
  - `src/tests/regression/test_selection_reachability_guardrails.py` gains **G7**, asserted through
    the real route and real backends as well as the registered callbacks. It also gains the **Y3**
    read-side guardrail, which the design's §5 table lacked. Mutation-checked at four sites.
- **The dataset selector mounts at `⊥` instead of a seeded `spirals` (OQ-N2 / D-N13).** The owner
  accepted `⊥`-at-mount on 2026-09-02, on the condition that the hydration above land first
  (D-N10). With that in place, the first interaction is an explicit choice, and `⊥` appears only
  when it is true. What the mount lands on now depends on what the backend reports:
  - **pending / loaded, nameable**: that dataset (G7).
  - **none**: `⊥`. The backend holds nothing, and nothing is invented for it.
  - **loaded but unnameable** (an unseeded generator another client staged, or raw inline data):
    `⊥`, plus an informational notice naming what the backend holds. A silent `⊥` over a busy
    backend would read as "nothing is loaded".
  - **unknown** (a cascor that predates juniper-cascor#676, or a failed read): falls back to the old
    default. `⊥` there would disable Start *and* Apply Dataset after every reload over a backend
    that may be staged and ready — exactly the regression D-N10 exists to prevent. A failed read
    now writes an explicit `unknown` block, so the gate can tell it apart from "holds nothing".
  - **demo mode** still lands on spirals, because the simulator holds spirals, not because of a
    seed.
  - The restart modal's dropdown loses its seed too (it was overwritten on every open anyway), and
    its `enabled[0]` fallback is recorded in code as a deliberate exception to OQ-6 (owner ruling,
    2026-09-22).
  - Mutation-checked: re-seeding the layout, dropping the unknown fallback, a failed read writing
    `None`, and suppressing the unnameable notice each fail a test.
- **Generator loads run `juniper_data_client.validate_npz_contract` as an ADVISORY second check**
  (#559; owner ruling 2026-09-22). `regenerate_dataset_from_generator` now hands every downloaded
  artifact to the shared contract validator before its own rank probe dispatches it. For a 3-D
  artifact the validator checks sequence rules canopy's install never did: that a `t` / `dt`
  channel is present, that `dt >= 0` with `dt[:, 0] == 0`, that `t` and `dt` agree, and that
  masks are binary and correctly shaped. A violation is logged at WARNING, naming the source and
  the rule, and **the install proceeds exactly as before**. The validator fails closed, and a
  legacy `X_full`-only artifact makes it raise `KeyError`, while the ecosystem contract is
  "tolerate `*_full`, never require it". So it reports and never gates. Any exception it raises
  is caught, whatever the type, including an `ImportError` from a client too old to have the
  helper. The rank probe stays the gate, and the comment above it no longer claims that the
  helper is absent from the pinned client, a claim that has been false since the 0.5.0 floor.
  `src/tests/unit/test_npz_contract_advisory.py` covers a violation that is reported and still
  installs, a legacy artifact that is reported and still installs, an unexpected error that
  never blocks the load, a client without the helper, and a valid artifact that logs nothing.
  The unit lane runs without juniper-data-client (`src/tests/conftest.py` injects a stub module),
  so the tests drive the wrapper through a faithful fake of the helper.
  `test_the_fake_agrees_with_the_real_helper` holds the fake to the real one wherever the client
  is installed, and skips, saying why, where it is not. Eight of the ten cases fail against the
  pre-change tree. The other two are the negative control and the agreement check, and neither
  exercises canopy code.

### Changed

- **The `[juniper-data]` extra admits juniper-data-client 0.6.0**: `juniper-data-client>=0.5.0,<0.7.0`
  (ceiling `<0.6.0` → `<0.7.0`). This is W1.13 of the juniper-ml recurrence × equities plan.
  - data-client 0.6.0 tightens `validate_npz_contract` (W1.4): finite `dt`, `target_dt` /
    `seq_lengths` shape and range checks, and `float32` `X` / `y` / `y_reg`. canopy runs it as an
    ADVISORY second check on generator loads.
  - The W1.4 downstream census (juniper-data-client 0.6.0's CHANGELOG) found canopy's fake-vs-real
    agreement test still passing.
  - The release train's consumer propagation did not raise this ceiling, because the pin lives in
    an extra.
- **The registry's availability and task-type comments match what juniper-data ships, and the recurrence
  seed carries a gate note (W1.11, the canopy comment half).** The plan is juniper-ml's
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`.
  `src/model_registry.py` said `equities` and `equities_seq` are unavailable in the deployed container
  because juniper-deploy pins juniper-data 0.15.0. The pin has been 0.16.0 since juniper-deploy#230; that
  image carries `yfinance` (juniper-data#421), and juniper-deploy#231 gave the container its outbound
  network, so both are available there. The vocabulary comment now says where `equities_seq` is
  `regression`: from generator 6.0.0 (juniper-data#437, X8), on juniper-data `main` and in its releases
  from 0.17.0. Releases through 0.16.0 still declare `classification`. The gate note records that
  `compatible()` reads canopy's own label, never juniper-data's, so the pair passes the gate under
  either. juniper-deploy#245's smoke completed the fit against published juniper-data 0.16.0 on
  2026-10-08 without reaching the gate, because it staged without `nn_model`. The same stale pin claim
  is corrected in three test docstrings (`src/tests/regression/test_dataset_generator_contract.py`,
  `src/tests/unit/test_model_registry.py`), and the X8 test constant's comment gains the release
  boundary. Comments only: no behaviour or assertion changed.
- **The recurrence regression card says its numbers are in-sample (W0.7, the label half of plan
  findings F-S5 and F-SCI3).** The plan is juniper-ml's
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`.
  `POST /v1/train` scores the fit on the training split it was fitted on. The card's title in
  `MetricsPanel._build_oneshot_result` read
  `Recurrence (LMU) — final regression metrics`, which looks like a held-out score. It now reads
  `Recurrence (LMU) — in-sample (train split) regression metrics`, over a muted caption:
  *Computed on the training split the fit saw; not a held-out score.* No number changes. The
  service now returns `metrics_scope: "in_sample"` on that response (juniper-recurrence#190), and
  the adapter already ignores a response key it does not know, so canopy needs no change for it.
  A new test in `src/tests/unit/test_recurrence_service_adapter.py` pins that tolerance.
  `src/tests/unit/test_recurrence_oneshot_result.py` gains 6 tests, 4 of which fail on the parent;
  the other 2 check that the numbers and the awaiting placeholder are unchanged.

### Fixed

- **The top status bar applies its periodic responses again, and the metrics store's poll no longer evicts
  itself in chains (F-CANOPY-055, F-CANOPY-058, F-CANOPY-068).** Both polls are now paced by request/ack.
  Each feeder's only Input is a request store, written by a clientside pacer on the poll's existing
  Interval, and each feeder echoes the request's `seq` into an ack store on every return path. The pacer
  asks again only once the ack has caught up, or once the outstanding request is past its stale bound:
  `POLL_PACER_STALE_MS` (30 s) or three times the longest round trip the page has seen on that poll,
  whichever is longer, capped at 120 s. Each round trip is a lower bound (to the last pacer run that still
  saw the request unanswered), so a throttled background tab cannot inflate it. On the fix's own verify leg,
  on a host loaded by other work, requests stayed in flight up to 17.3 s, which a fixed 30 s would have
  cleared by under 2x. Because it waits for the ack, the pacer never re-requests a feeder while its
  request is in flight,
  except for that deliberate stale re-issue. Two other paths can still re-request one, each costing at most
  one response with no chain: the renderer's initial call after a live/one-shot model switch rebuilds the
  tab container, and a pacer write that lands during that call.
  - **F-CANOPY-055.** `update_unified_status_bar` rode `fast-update-interval` (1 s) directly. Its wire latency
    had a median of 1.16 s (0.21–3.08 s), plus the renderer's queue, so each response was still unprocessed
    when the next tick's request evicted it: 0 of 36 applied on the census, and status, phase, step, hidden
    units and latency held their layout defaults for the life of the page. The Live Dataset Switch gate
    computed in the same feeder could not land either.
  - **F-CANOPY-058.** canopy#613's `running=` guard on `metrics-store-interval` is removed. The renderer
    released it from `completeJob()` for an evicted request's late completion too, so any re-enable that
    let the next request be made before the in-flight response landed could start a chain of evictions.
    Two 25-minute census runs on `main` found 29 of 611 responses evicted, in runs of up to 11 and 34.8 s.
    The display mode, the feeder's second Input until now, is now State of the feeder and an Input of the
    pacer, compared by value, and a mode change reaches the handler as one even when its own request is lost (not when a raising handler acks it with
    `no_update`; the next request is then a tick). Its mid-flight change
    evicted the fetch in a synthetic app with this wiring; it was not observed in mid-request on canopy.
    The full-history modulus (`FULL_HISTORY_POLL_TICK_MODULUS`, 5) now counts requests rather
    than ticks of the guarded Interval, so `full` / `hidden_units` refetch on every fifth request
    (expected every ~5–10 s; not measured).
  - **F-CANOPY-068.** The strand watchdog is removed, with `METRICS_STORE_STRAND_TIMEOUT_MS`.
    **Correction to the `[0.8.0]` entry**, which says it re-enabled the interval "once it has been
    continuously disabled" for 30 s. It could not do that. It sampled `disabled` every 5 s, and its clock
    reset only on a sample that found the lane enabled or the Apply clamp held, so it measured how long
    every sample had found the lane disabled, not how long the lane had been. It fired 13 and 15 times in
    the two runs, about 31 and 36 an hour, every time mid-fetch, with the lane enabled for 11–15 s of the
    30 s before each fire, and 7 of those fires evicted a response. (That its samples kept phase with the
    feeder's ~4.9 s cycle is inferred from a replay, not measured.) A request that never gets a response is
    now re-issued by its own age, which measures progress, not samples of a prop.
  - The gate is again the only writer of `metrics-store-interval.disabled`, and a completion can no longer
    re-enable a lane under the CAN-000 Apply clamp. Both pacers ride clamped lanes.
  - **One cost.** A failure outside a feeder's own `try` (a non-OK reply from Dash or a middleware, or a
    network failure) lands no ack, so that lane waits out its stale bound, at least 30 s. canopy#613's guard
    retried the metrics store on the next tick after a non-OK reply, and the status bar's 1 s lane retried
    on the next tick.
  - Tests: `src/tests/unit/frontend/test_f055_f058_f068_request_ack_pacer.py`. It pins the wiring and the
    acks on every return path, runs the registered pacer under node, and simulates 10 idle minutes of a
    healthy lane whose cycle is near 5 s: no request made in flight, none stale. The same simulation of the
    old guard and watchdog fires falsely. `test_poll_gating.py` now requires one writer per `disabled` prop
    and no `running=` guard, and `test_poller_budget.py` counts the paced feeders against their pacers'
    lanes.
  - Evidence: juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phases 8,
    9 and 11.
- **`TestA422DetailReachesTheOperator` no longer reads the previous test's WARNING.** A failing recurrence
  fit logs its WARNING after the state flips, outside the lock, so a test that waited only for
  `is_training_active()` could end while its fit thread was about to log, and the record landed in the
  next test's `caplog` (main's own macOS CI failed this way at #702, #708 and #711). An autouse fixture in
  `src/tests/unit/backend/test_recurrence_backend.py` now joins every `recurrence-fit` thread after each
  test. Test-only.
- **A recurrence fit whose reply times out is followed, not failed, and a busy 409 names its holder (W1.5,
  canopy half; F-C4, F-CON1, F-CON2).** Plan: juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`; the service half is
  juniper-recurrence#192. A fit that outlived the adapter's 300 s read timeout used to be recorded `failed`
  (`RecurrenceServiceTimeoutError`). The service cannot cancel a fit, so it kept fitting, often to success, and
  answered the next Start with a 409 that named nobody.
  - Every `POST /v1/train` now sends `X-Request-ID: juniper-canopy-<uuid4 hex>`, which the service records as the
    operation's `requested_by`.
  - After a read timeout (only `httpx.ReadTimeout` means the request arrived) the backend stays `training`, with
    the phase `fitting (upstream)`. It reads `GET /v1/training/status` every 5 s for up to 30 minutes. A read that
    fails outright is tried again; three in a row settle the fit as `unknown`.
  - The fit is `trained` only when the status names canopy's request as the operation that produced the model the
    service holds. `trained` alone, a `restored` model, or a service without operation identity (0.5.0) never
    count. It is `failed`, worded as its own error, when the service says it failed. Otherwise it is `unknown`:
    `/api/status` gains `outcome_unknown: true`, and the status bar reads `Unknown — …` in amber, not `Stopped`.
  - A busy 409's object `detail` is parsed into `RecurrenceTrainInProgressError.holder`. The message names the
    holder's kind, `operation_id`, `busy_since`, `requested_by` and `dataset_id` after a remedy. The published
    0.5.0's string detail reads exactly as before.
  - A fit's `operation_id` is kept and reported on `/api/status`. Canopy calls neither `/v1/predict` nor
    `POST /v1/model/snapshots`, so it has nowhere to send `expect_operation_id` yet.
  - Runbook: `docs/AGENTS_REFERENCE.md` § Recurrence fit identity, timeouts, and one caller per service, which links
    the service's own "One caller per service" section rather than repeating it. Also `docs/api/API_REFERENCE.md`,
    `docs/USER_MANUAL.md` (item 10) and `docs/DEVELOPER_CHEATSHEET.md`.
  - Tests: `src/tests/unit/test_recurrence_operation_identity.py` (58, including the four races) and
    `src/tests/unit/backend/test_recurrence_backend_upstream.py` (19), over a fake service shaped after #192
    (`src/tests/fixtures/recurrence_service_fake.py`). `util/ad-hoc/2026-10-08_w15_w17_mutation_check.py`
    catches 19 of 19 mutations across both items.
- **The wheel again carries `outbound_errors`, which `main` imports.** canopy#631's
  `py-modules` list was not updated when #685 added `src/outbound_errors.py` and wired it into
  `main`, `status_cache`, the cascor adapter and the recurrence backend. `packages.find` does not
  collect a bare `src/*.py`, so a wheel built from `main` failed `import main` with
  `No module named 'outbound_errors'` — the same shape as the 0.5.0–0.8.0 wheels, and invisible
  to the image, which runs from `PYTHONPATH=/app/src`. `publish.yml`'s import smoke imports `main`,
  so it would have stopped the next release at the build job. `outbound_errors` is now a
  `py-module` and a target of `util/wheel_import_smoke.py`. `adapter_validation` stays out: nothing
  imports it. `demo_mode` stays out of the bare smoke: it needs torch.
  `src/tests/unit/test_wheel_import_smoke.py` pins both lists, the cwd guard, and that a module
  resolved from the checkout is a failure.
- **A recurrence fit sends the registry seed plus what the operator edited, and only parameters the
  generator declares. A preview above Start shows the request (W1.2; plan findings F-C2, F-C3).** The
  plan is juniper-ml's
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`
  (v1.4.1). **Owner ruling R7 is still open.** This applies its recommended default pending the
  ruling, as the wave-1 PRs did for R2, R3 and R8. The alternatives touch one function,
  `backend/recurrence_request.shape_staged_ref`.
  - **F-C2.** The schema-driven form renders every field, and Apply posts every rendered value. An
    untouched `equities_seq` form therefore staged seven keys beside the seed, and the fit request
    carried all of them: `start_date`, `purchase_date`, `basis_price_field`, `week52_window`,
    `normalize_features`, `max_symbols: 14` and `lookback: 64`. Under R7 the seed is the base. A
    form value is sent only when it differs from what the form showed for that field: the seed's
    value where the seed sets the key, juniper-data's default otherwise. An edited field wins over
    the seed. Nothing in the form records "edited", since Dash inputs carry no dirty flag, so it is
    read from the value. A field set back to what the form showed is not sent, which asks
    juniper-data for exactly that value.
  - **F-C3.** `nn_dataset_elements` / `nn_dataset_noise` became `n_samples` / `noise` for every
    generator. No sequence generator declares either. The restart modal re-stages them for every
    dataset type, which is how they reached one. **juniper-data did not refuse them, contrary to the
    plan's expectation.** Its params models keep pydantic's default `extra` handling and drop unknown
    keys, both on `main` (`462da218`) and at v0.16.0 (measured: `EquitiesSeqParams(n_samples=40,
    noise=0.1, …)` constructs, and `n_samples` is absent from `model_dump()`). So the operator's
    value vanished downstream while canopy reported it staged. Only declared parameters are
    forwarded now, on the staged path and the Start-body path alike. A generic field is never sent
    over a key the seed sets.
  - **The declaration** is `dataset_schema.DECLARED_PARAM_DEFAULTS`: names and defaults for the six
    rank-3 generators. It is a dated snapshot, as `KNOWN_UPSTREAM_GENERATORS` is, because canopy does
    not depend on juniper-data and the test env's copy is 0.6.0. The snapshot was captured from
    juniper-data `462da218` by `util/ad-hoc/2026-10-08_capture_sequence_generator_schemas.py`, which
    also wrote `src/tests/fixtures/juniper_data_sequence_generator_schemas.json`, the exact
    `GET /v1/generators` schemas. The field set and defaults are identical at v0.16.0. A rank-3 seed
    without a declaration fails a test. A parameter juniper-data adds is withheld with a WARNING at
    Start and named in the preview.
  - **The preview.** `POST /api/recurrence/effective_request` returns the body the next Start would
    send. It is computed by the same code Start runs, and it is read-only. The new
    `frontend/components/recurrence_request_preview.py` shows it above Start for a one-shot model. It
    lists where the request came from, the edited fields and the staged keys not sent. It refreshes
    on events only, never on an interval; a clientside edge detector keeps the 5 s banner poll from
    dispatching it. The preview and the Start both log the body at INFO with sorted keys. The JSON
    the real adapter posts is pinned to the preview's body by `httpx.MockTransport`.
  - `start_training` now reads the pending hyperparameters under its lock. It used to copy them
    before taking it, while `apply_params` writes them inside it.
  - Tests: `src/tests/regression/test_recurrence_staging.py` (+10: the plan's three, kept separate,
    plus seven for the preview route and the restart-modal path).
    `src/tests/unit/test_recurrence_request.py` (new, 68: the declaration against the capture,
    including every `equities_seq` field; the rules one at a time; the body against the real
    adapter). `src/tests/unit/frontend/test_recurrence_request_preview.py` (new, 18). One manifest row
    in `src/tests/ui_contract/control_manifest.py`. `test_operator_edits_override_the_seed` asserted
    `"n_samples": 40` for `equities_seq`, which was F-C3 itself. It now asserts the key is absent;
    the rest of the test is unchanged. The component inventories count 16 components, the new panel
    included: `src/tests/unit/frontend/test_dashboard_manager.py`,
    `src/tests/unit/frontend/test_dashboard_manager_coverage.py` and
    `src/tests/integration/test_dashboard_enhancements.py`. The hand-built manager in
    `src/tests/unit/frontend/test_meta_parameters_layout.py` gains the panel's mock.
  - `util/ad-hoc/2026-10-08_w12_mutation_check.py` puts each pre-change behaviour back at one site,
    one arm at a time, on a copy of the tree. All 17 arms fail the tests they name, including the
    pre-change merge (F-C2), the pre-change translation (F-C3), a preview that ignores the staged
    dataset, and a declaration missing one `equities_seq` field (the plan's risk row). The unmutated
    control runs 119 tests, the three files plus the harness's binding probe. 118 pass, and the
    opt-in juniper-data source check skips, because the harness clears `JUNIPER_DATA_SRC`.
- **A refused recurrence request now says what to do, and a restored model counts as a model (W1.6;
  plan findings F-C5, F-C6, F-C7).** The plan is juniper-ml's
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`
  (v1.3.0). All three changes are in `src/backend/recurrence_service_adapter.py`.
  - **401 / 403 (F-C5).** The remedy said `check recurrence_api_key`. That is the setting's Python
    name, and no operator can set it. The message now reads
    `… — set JUNIPER_CANOPY_RECURRENCE_API_KEY or JUNIPER_CANOPY_RECURRENCE_API_KEY_FILE to a key the service accepts`,
    still followed by the service's `detail`. This replaces the remedy the W0.5 entry below says the
    401 / 403 branches kept.
  - **`restored` (F-C6).** juniper-recurrence `main` reports a third `GET /v1/training/status` state:
    a model loaded from a snapshot, with `restored_from` naming the snapshot. `RecurrenceStatus` gains
    `restored_from` and a `model_present` property, true for `trained` and `restored` alike
    (`MODEL_PRESENT_STATES`). Nothing else in canopy reads the service's status states. The backend's
    `trained` belongs to its own fit state machine and is never fed from that route, and no UI mapping
    reads the enum, so the property is the one place the rule lives, ready for W1.5's status poll. The
    published 0.5.0 never sends `restored`, and its replies parse with `restored_from=None`.
  - **429 (F-C7).** A rate-limited request raised the generic `RecurrenceServiceError`. It now raises
    `RecurrenceServiceRateLimited`, a subclass, whose message carries the reply's `Retry-After` before
    the detail:
    `recurrence service error 429 on POST /v1/train — retry after 30 s: Rate limit exceeded. Try again in 30 seconds.`
    `retry_after` holds the value as sent and survives pickling. To carry it in `args`,
    `RecurrenceServiceError.__init__` now forwards any values a subclass appends (`*extra`). A plain
    error still has exactly three.
    An HTTP-date is shown as sent. The value is flattened and bounded to 64 characters. A 429 without
    the header keeps the plain wording, so the existing 429 assertions hold unchanged.
    `outbound_error_text` passes the message to `completion_reason` as is, as it does any answer with
    a status code, so the backend needs no change.
  - **The status bar's failure tooltip bound rises from 400 to 480 characters**
    (`DashboardManager._FAILURE_REASON_TOOLTIP_MAX_CHARS`). The 401 / 403 wording grew from 90 to 174
    characters, and `test_the_tooltip_holds_every_reason_the_adapter_can_build_uncut` exists to fail
    exactly when that happens. A new test holds a 429 with its wait to the same bound.
  - Checked against the real service as well as the mocks.
    `util/ad-hoc/2026-10-05_recurrence_wire_contract_probe.py` builds juniper-recurrence's app in
    process and drives canopy's adapter through the service's own middleware. It covers a wrong key, a
    third request at 2 per minute, and a snapshot restore. Before this change the 429 was a
    `RecurrenceServiceError` and `restored` had no `restored_from`. After it, the run produces the
    messages and state above.
  - Tests: `src/tests/unit/test_recurrence_service_adapter.py` (+22, `TestW16AuthRestoredRateLimit`;
    two assertions that pinned the old remedy verbatim now pin the new one verbatim),
    `src/tests/unit/backend/test_recurrence_backend.py` (+2, the real adapter's 401 and 429 reaching
    `completion_reason`) and `src/tests/unit/frontend/test_completion_reason_status_bar.py` (+3).
- **The registry no longer claims the recurrence model is version 0.1.0 (W1.7; plan finding F-C8).**
  `src/model_registry.py` seeded the recurrence model with `version="0.1.0"` while the service it
  names was 0.5.0. canopy has no package edge to the service that could keep such a constant true,
  so the seed's version is now blank, and the version comes from the service.
  - `RecurrenceServiceAdapter.service_version()` reads the `version` in `GET /v1/health`'s body when
    there is one. The plan expected one there, but juniper-recurrence 0.5.0's body is
    `{"status": "ok"}`, and the service mounts no `GET /`. So the version comes from `info.version` on
    `GET /openapi.json`, which FastAPI fills from the `version=__version__` the service passes to
    `create_app`. That route is open under juniper-service-core 0.5.0 and authenticated under 0.7.0,
    and the adapter sends its key either way.
  - `refresh_model_versions(version_sources, *, models=MODELS)` is one registry refresh. It asks each
    source at most once and returns the specs with the answers baked in, so reading the result never
    touches the network. It never raises for a version: a source that fails, times out or names no
    version yields `unknown (version lookup failed)` (`SERVICE_VERSION_UNAVAILABLE`), with a WARNING
    that names the failure. A model with no source keeps its spec.
  - **No surface renders a model's version yet.** Nothing read `ModelSpec.version` before this change
    either: not the model table, not the picker, not `/api/selection`. Wiring a refreshed registry into
    one of them is the display half the plan leaves open.
  - **The dependency floor is a documented contract floor, not a pin.** canopy imports no
    `juniper_recurrence_client`; it speaks the REST contract through its own adapter. A
    `juniper-recurrence-client` requirement would install a package nothing imports, would constrain
    nothing canopy runs, and has no `[service]` extra to live in, since canopy has none. The floor is
    `RECURRENCE_SERVICE_CONTRACT_FLOOR = "0.5.0"` in the adapter, and `docs/api/API_REFERENCE.md`
    § Recurrence Service Contract (Recurrence Mode), new, names it. A test pins the two together.
  - Tests: `src/tests/unit/test_recurrence_service_adapter.py` (+15, `TestServiceVersion`) and
    `src/tests/unit/test_model_registry.py` (+15, `TestRefreshModelVersions`).
  - `util/ad-hoc/2026-10-05_w16_w17_mutation_check.py` covers both entries. It puts each pre-change
    behaviour back at one site, one arm at a time, on a copy of the tree. All 16 arms fail the tests
    they name. The unmutated control passes all 239 tests: the four touched test files plus the
    harness's import-binding probe.
- **A failed recurrence fit now says why: the service's 422 `detail` reaches the log,
  `completion_reason` and the status bar (W0.5; plan finding F-C1).** The recurrence service
  answers a bad dataset with HTTP 422 and a JSON body such as
  `{"detail": "invalid dataset: X_train has non-finite values (NaN/Inf)"}`. canopy dropped that
  text at every hop. The adapter kept it only as `body=` on the exception, and
  `outbound_error_text` passed on a message that did not contain it. The backend logged
  `recurrence fit failed: recurrence service error 422 on POST /v1/train`, and the status bar showed
  `Failed — recurrence service error 422 on POST /v1/train`.
  - `RecurrenceServiceAdapter._parse` (`src/backend/recurrence_service_adapter.py`) appends a 4xx
    body's `detail` to the message as `…: <detail>`. That covers the generic 4xx branch and the
    409 and 401/403 branches, which keep their wording and their `check recurrence_api_key`
    remedy. A string detail is used as is. A FastAPI validation list becomes `loc -> msg` pairs
    joined by `; `, without the echoed `input`. Anything else is `str()`-ed. Whitespace is
    collapsed and the detail is bounded to 300 characters. A non-JSON body, or JSON without a
    usable `detail`, leaves the message unchanged, and `body=` still holds the raw response text.
    Reading the detail never raises. A body nested deeply enough that the JSON decoder raises
    `RecursionError`, which is not a `ValueError`, still produces the same typed error and message.
  - **A 5xx detail is never appended.** On a 5xx the recurrence service relays its own
    upstream's exception text. juniper-recurrence's `map_data_error` answers a juniper-data client
    failure with `502 data fetch failed: {exc}`, and juniper-data-client 0.5.0 words a refused
    header as `Request failed: … in header value: ' <key>'`. A padded juniper-data key on the
    service would therefore reach `completion_reason`, which an anonymous caller can read. That is
    the transport text #683 keeps from callers, relayed one hop. A 5xx message stays as it was:
    status code, method and path.
  - `outbound_error_text` (`src/outbound_errors.py`) is unchanged. A status-bearing error is the
    upstream's answer and passes as `str(exc)`, which now includes a 4xx detail. A transport
    failure carries no status code and is still named by its type only, so the #683 guarantee holds.
    `docs/api/API_REFERENCE.md` § Upstream Failures now states what the recurrence answer carries.
  - `RecurrenceBackend._run_fit` logs `recurrence fit failed (status=<code>): <message>`. The
    WARNING carries the status code, the method, the path and the detail.
  - The status bar keeps its 120-character label. When the label has to cut a failure reason, the
    status text renders as a `Span` whose `title` holds the whole reason, so hovering shows the part
    the cut dropped. The tooltip is bounded at 400 characters, which fits the adapter's longest
    wording plus a 300-character detail. A reason the label already holds gets no tooltip. Every
    other state still renders a plain string, and the callback's outputs are unchanged.
  - Tests: `src/tests/unit/test_recurrence_service_adapter.py` (+34),
    `src/tests/unit/backend/test_recurrence_backend.py` (+4),
    `src/tests/unit/frontend/test_completion_reason_status_bar.py` (+18) and
    `src/tests/unit/test_outbound_errors.py` (+6). `TestA422ReachesTheStatusBar` drives the whole
    chain: a real adapter over an `httpx.MockTransport`, the real backend, the real `/api/status`
    route and the real status-bar builder. 37 of the 62 fail on the parent. The other 25 are
    controls that pin behaviour this change must keep: a body with no usable `detail`, a body the
    JSON decoder cannot handle, a 5xx detail that relays a refused key, and a reason short enough
    for the label. The 7 5xx pins also fail when the adapter appends a 5xx detail, which is what
    makes them guards.
- **The replay player's range plays its last frame, its sliders stop at the last frame, and its own
  renders no longer send control requests (follow-ups to F-CANOPY-059 and F-CANOPY-056).**
  - cascor's range end is exclusive (`set_range`: `[start, end)`), while the range slider is
    inclusive. `queue_control` now sends the slider's upper value plus one, and `_session_range`
    shows cascor's `end` minus one. Before, a chosen range never played its last frame.
  - cascor's `snapshot_window.end_epoch` is the history length, not the last index.
    `_session_window` now ends that window at `end_epoch - 1`, so the scrubber and the range slider
    no longer offer a position cascor clamps away. The legacy `window` shape already held the last
    index and is unchanged.
  - `render_session` writes the scrubber, speed and range values, and those are `queue_control`'s
    Inputs. So every session write sent a control request whose result wrote the session again.
    This is the `can015-replay-player-control-loop` cycle in `test_f048_replay_cycle.py`, which F-059
    and F-056 had kept unreachable. `queue_control` now ignores a value equal to what the session
    already shows.
  - The local fallback stores a range in cascor's `{start, end}` shape.
  - `src/tests/unit/frontend/test_replay_range_end_and_echo.py` is new, with 13 tests; 9 of them fail
    on the parent. Fixtures that encoded the old off-by-one are corrected:
    - `test_f059_replay_range_dict.py`, `test_f056_replay_control_envelope.py` and
      `test_replay_player_panel.py`: the expected values.
    - `test_replay_player_panel_gate_coverage.py`: the outbound end.
    - `test_p2_wave_batch_a.py`: a window whose `end_epoch` disagreed with its `length`.
- **Against cascor, the replay player's controls take effect, and Stop ends the session
  (F-CANOPY-056, P1).** canopy's `/replay/control` proxy passes cascor's envelope through unchanged,
  `{status, data: {…, result}, meta}`. `_merge_session` overlaid that envelope onto the session, and
  none of the keys `render_session` reads sits at its top level. So play, pause, seek, speed and
  range never reached the session, and the sliders were written back to their stale values. A Stop
  kept the session, because its clearing branch ran only for an empty body, so the weight drain kept
  running until a reload or a model select. `_merge_session` now unwraps the envelope and maps
  cascor's `result` (`state_summary()`) onto the stored session: the integer `time_index` goes to
  `time_index.current`, `paused` sets `playing`, and the summary keys go to `data.session`, where
  `render_session` reads them. Any successful Stop clears the session. The local fallback for
  `speed` and `range` now writes to `data.session` too. `src/tests/unit/frontend/test_f056_replay_control_envelope.py`
  (new, 19 tests) drives the registered `dispatch_control` with each action's envelope as cascor's
  route builds it and renders the result. Its 9 control tests fail on the parent. Not yet driven
  against a live cascor.
- **Against cascor, the replay player shows its session again (F-CANOPY-059, P0; a regression from
  canopy#532).** cascor serves the replay `range` as a dict, `{"start": …, "end": …}`, at
  `data.session`. canopy#532 read it there but indexed it as a list, so `render_session` raised
  `KeyError: 0` on every session cascor served. The Replay tab stayed at "No active replay session"
  with no control on screen, and cascor stayed in REPLAYING. The only exit was the sidebar's Reset
  Training. The new `ReplayPlayerPanel._session_range` accepts the dict, the legacy list or nothing,
  and clamps the result to the snapshot window. `src/tests/unit/frontend/test_f059_replay_range_dict.py`
  (new) runs the registered callback on the payload the E2E ledger's Phase 1 measured live. It raises
  `KeyError: 0` on the parent. canopy#532's fixture in `test_p2_wave_batch_a.py` was labelled
  "the exact shape measured off the running service" while it typed the range as a list. It now uses
  cascor's dict shape and says what it is. This fix exposes F-CANOPY-056, which F-059 had masked:
  control results still never reach the session.
- **A Start refused because the staged dataset is wider than the network now says how to proceed
  (F1).** cascor cannot widen a network on a plain Start, which continues the current network.
  - Since juniper-cascor#687, cascor refuses such a Start **before** loading anything, and
    opens its message with `[start_fresh_required]`.
  - The alert now names the remedy and the two controls that apply it: **Stop & Restart with new
    dataset** and **Start fresh**. The pending banner stays up, because the dataset stays staged.
    The alert also says the results shown are still the previous run's.
  - It stays until dismissed, because it carries an instruction. Every other Start failure keeps
    the generic alert.
  - Before, the alert showed cascor's raw `_pad_dataset_for_network: … resize the network first`.
    By then cascor had already switched the loaded dataset, so the page showed the previous run's
    results under the new dataset's name (juniper-ml's A-N2 run, F1). `equities` (15 features)
    and `mnist` (784) hit this against any 2-feature network.
  - There is no fallback for an older cascor. It consumed the staged dataset before refusing, so
    the banner the alert points at was gone.
- **The restart modal called Start fresh "functionally a clean stack launch" (F2).** Since
  juniper-cascor#685, a start-fresh carries the applied parameters onto the rebuilt network, so
  the parameters edited in the modal survive it (owner ruling 2026-09-24). A clean launch would
  have reset them to the engine defaults.
  - The toggle label and both help texts now say the parameters carry over.
  - Against a cascor older than #685 the edits are still dropped, and the text is then wrong.
  - `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py` covers both entries.
    It pins the marker literal, and it checks that the controls the alert names exist under
    those labels.
- **The sidebar said "Active: CasCor" before anything had asked the backend (X11).**
  `_selection_is_live` answers `True`, `False` or `None`, and the model summary rendered `None`
  exactly like `True`. So the first-paint seed read *"Active: CasCor"* before any read. A mount
  whose `GET /api/selection` failed kept that text too, so the "Active" claim came from the one
  path that had just failed to reach the backend.
  - Following the owner's ruling of 2026-09-24, an unknown liveness now reads **"Selected: CasCor
    (Cascade-Correlation) · backend status unknown"**. "Active" requires a round-tripped payload
    whose backend serves the model. A lifecycle note such as `· coming soon` still comes first.
  - The failed-read path now writes that text instead of leaving the summary alone, so the summary
    follows the key store's fallback to the default model.
  - Start gating is unchanged, because unknown is still not disagreement. The `False` state still
    names the backend that is really running.
  - `TestX11UnknownLivenessIsNotActive` in
    `src/tests/regression/test_selection_reachability_guardrails.py`, mutation-checked at five
    sites against the full unit lane.
- **A model swap could strand the dashboard on a tab that no longer exists (Y4).** A one-shot model
  rebuilds the tab bar without the five cascade-only tabs, and the active-tab restore guarded only
  "no saved tab" and "saved equals shown". Measured in headless chromium: on Network Topology, a
  swap to a one-shot model left **no** tab highlighted and **zero** visible panes; a reload with a
  persisted cascade tab restored it at mount and was stranded the same way once the rebuild landed.
  The restore now reads the rendered tabs as an Input. It never restores a tab that is not rendered,
  keeps the shown tab when it is, and otherwise falls back to the first rendered tab (Training
  Metrics). The reset lives in the existing restore writer, so it adds no `active_tab` writer. The
  app has **three** such writers, not the two the source-level test counts:
  `hdf5_snapshots_panel`'s replay hand-off is the third.
- **Whether a selection control was greyed out was decided by the reason-string helpers, not by
  `compatible()` (Y8).** `gated_dataset_options` disabled an option when `dataset_reason` returned
  a string, and the model table disabled a Select when `model_reason` did. Both helpers
  re-implemented all three compatibility axes, so the load-bearing predicate had three independent
  expressions. `disabled` is now `not compatible()` on both surfaces, and the helpers only choose
  the wording, with a generic phrase for an axis they do not name, so a greyed control can never
  read `None`. A universal test pins `disabled == not compatible()` and reason-iff-disabled over
  every pair of the production registry and of a synthetic registry that fails each axis alone. The
  production registry alone cannot see a dropped temporal axis, because every shipped rank-3 model
  is Δt-aware.
- **The model table's Select button carried its reason only in `title=` (Y7, model-table half).**
  Each row's compatibility cell now has a deterministic id derived from the model key, and the
  row's Select points at it with `aria-describedby`, as
  `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §4.3 (juniper-ml) specifies.
  The accessible description is therefore the rendered reason. The control is now an `html.Button`
  carrying the class string `dbc.Button` rendered, because dbc 2.0.4's `Button` rejects `aria-*`
  props. The reason is no longer repeated in `title=` on a disabled Select: Bootstrap gives
  `.btn:disabled` `pointer-events: none`, so that tooltip could never show. Enabled Selects keep
  their hover hint.
- **An idle dashboard spent about a third of its response latency on a timer with nothing to do:
  the replay weight drain, a 2 Hz timer, ran on every tab for the life of the page.**
  `replay-player-panel-weight-drain` drains the CAN-015g replay-weight ring buffer. It ran on no
  tab gate, and every tick was a store update, which re-runs the page's selectors, plus a clientside
  callback that found nothing. Today it always finds nothing. cascor's replay frames carry no
  weights: `_emit_frame` adds none, and `weights_at` has no production caller. canopy's metrics relay
  also rebuilds each payload without that key. So no replay weight reaches the page. The page's
  main thread sits at ~0.1% idle, so the timer's cost came straight out of response delivery. An
  in-page A/B on an idle page parked the timer and compared each window with its two neighbouring
  baselines (juniper-ml `util/ad-hoc/2026-09-23_canopy_timer_park_ab.py`, two runs in opposite
  orders). It cut the median response-delivery latency by **42% and 32%**. A live check of this
  build (`ce78e0de`) against `3a6dea95`, its parent at the time (`2026-09-23_idle_cuts_live_check.py`),
  was less clear. One cuts window
  beat both of its neighbours, and the other was 1.5–2.7% slower than both, so the check scored the
  latency inconsistent. An earlier check of the same change, built on canopy#670's branch, scored
  it consistent.
  - **The drain now ships disabled** and runs only once this page has started a replay. A new
    clientside callback, the only writer of its `disabled`, enables it when
    `replay-player-session` holds a `snapshot_id`. The snapshots panel writes the session on POST
    `/replay`.
  - **Against cascor it then runs until the page reloads, or until a successful model select
    rebuilds the tab bar.** A Stop does not clear the session. `_merge_session` clears
    `snapshot_id` only when the stop response is empty, and the proxied cascor envelope never is,
    so the old id survives the overlay. That is an existing defect, F-CANOPY-056 in the juniper-ml
    E2E evidence ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`).
    Against cascor the player's Stop is not on screen anyway: the player never shows a session, because its render
    raises on cascor's `range` (F-CANOPY-059, same ledger). This change neither causes nor fixes
    either.
  - **Nothing a user sees changes.** No replay weight reaches the page (F-CANOPY-057 in the same
    ledger). The Decision Boundary consumer also ignores replay weights without a session, and the
    JS ring buffer is capped at 100 entries, so a paused drain cannot grow it.
  - **The metrics panel's own 1 Hz `-update-interval` is removed.** No callback took it as an
    Input. Its measured effect alone was nil (−1.6%), so this is hygiene. Its period setting
    (`update_interval` / `JUNIPER_CANOPY_METRICS_UPDATE_INTERVAL_MS`) is still parsed and still
    drives nothing, exactly as before, and the two docs rows now say so.
  - New `src/tests/unit/frontend/test_idle_dispatch_cuts.py` fails CI on any `dcc.Interval` in the
    built app that no callback consumes. It also pins the drain's gate: one writer, clientside, from
    the session, and no primary writer of the session that could hold it. It runs the gate under
    node. 7 of its 9 tests fail on the parent; the two premise pins hold on both.
  - **Left alone, with a reason:** the training-state store's `/api/state` rewrites that change
    only `timestamp`, the third cut the ledger listed. The rewrite is the clock of the "Phase
    Duration" readout, which computes elapsed time at callback time. Suppressing it would freeze
    the readout whenever the state is otherwise static, so it needs its own design.
- **The entry above merged before its review's third round was applied. A comment and a test
  message still tied the weight drain to a "replay session" that a Stop does not end, and comments
  and docs described a weight emitter that never reached cascor's `main`. The new Interval tests crashed, instead of
  refusing, on an Interval with no id, and one of them also on a pattern-matching id.** canopy#676's
  commit message says its review ran "two rounds; prose corrections only". It ran three, and rounds
  1 and 2 each changed test code. The message also says the comments claiming cascor emits weights
  were corrected; one was not. And it says that after a replay the drain "runs until the page
  reloads, as it always ran before"; a successful model select also ends it. Its "live check of this
  build against its parent" and "half of the page's steady-state ticks" were loose too (round 3's
  finding 4); their copies in the tree are fixed below. The juniper-ml E2E evidence ledger has the
  record
  (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 9).
  - `replay_player_panel.py`: the gate comment said the drain is disabled "unless a replay session
    exists". It keys on a stored `snapshot_id`, which a Stop against cascor does not clear
    (F-CANOPY-056). So once a replay starts, the drain runs until the page reloads, or until
    a successful model select rebuilds the tab bar and re-mounts the session Store empty. The entry
    above said "until the page reloads" and missed the second path; it is corrected in place, and so
    is the same sentence in the drain's comment. The entry's "live check of this build against its
    parent" now names the pair.
  - `ws_dash_bridge.js`: the drain comment no longer cites a "g-3 emitter" for the weight blocks,
    and the buffer comment's "Each carries…" has its antecedent back. `replay_forward.py`'s module
    docstring said cascor's g-3 emitter produces the weight payloads it decodes. None does
    (F-CANOPY-057): cascor's `_emit_frame` sets no weights. It now says the module has no live input
    yet.
  - `docs/USER_MANUAL.md` said weight samples stream during playback; it now says none reach the
    page. `notes/development/REPLAY_V2_FAQ.md` described the weight stream as shipped, said a Stop
    clears the buffer, and called the drain's CPU cost negligible. It gains a dated status note above
    its answers instead of a rewrite; the note also records that against cascor the player shows no
    session at all (F-CANOPY-059).
  - `test_idle_dispatch_cuts.py`: `_dead_intervals` refuses, by name, an Interval with no id (the
    check raised `KeyError`) or a pattern-matching id. The sibling tests look ids up through two
    helpers that accept both shapes; a dict id made the old set comprehension raise `TypeError`.
    Three new tests pin the check itself, including that it reports every unconsumed Interval and
    only an `n_intervals` Input counts as a consumer. A fourth pins the id lookups the wiring tests
    use. A mutant that drops either refusal, reverts either helper, makes the check report nothing, or
    counts as a consumer another property, a State, an Output writer or an id matched by substring
    (`fe` in `fed`) fails one of them. The gate's rule test is renamed to what it tests. The module
    docstring's "half of the page's steady-state ticks" now says the two timers fired 3.0 of the 6.6
    ticks per second the layout's enabled Intervals nominally fire (45%, by the static census, which
    leaves out the one-shot `params-init-interval`).
- **The replay controls never applied: play, step, start, end, the speed buttons and the slider
  did nothing on any page load (F-CANOPY-048).** `handle_replay_controls` (Input
  `replay-slider.value` → Output `replay-state.data`) and `update_replay_ui` (Input
  `replay-state.data` → Output `replay-slider.value`) formed a cycle across two callbacks.
  dash-renderer promotes a requested callback only when none of its Inputs, less its own Outputs,
  lies in the downstream closure of any pending callback, itself included (`getReadyCallbacks`,
  `dash_renderer.dev.js:1633-1665`, dash 4.2.0). Each covered its own Input through the other, so
  neither was ever ready, and the circular-dependency breaker (`:3064`) fires only when nothing
  else at all is pending, which canopy's pollers never allow. Measured live: all three replay
  callbacks in `requested` in 6471 of 6471 samples, and zero `replay-state` writes across ten
  clicks.

  Fixed by merging the two into one callback that reads and writes `replay-slider.value`. Its own
  Outputs are exempt from its readiness check (`differenceBasedOnId`, `:1661`), and its own writes
  never re-trigger it (`:2972`). Each control's effect is unchanged, checked against verbatim
  copies of both old callbacks. The merge also removes a defect the lock was hiding. A chain
  started by `replay_tick` or by a metrics-store write reached the old controls callback through
  the slider write without being pruned, and its slider branch would have paused playback on
  every tick. Dispatch is now on the exact triggering component id, over every entry of
  `ctx.triggered`, so a click the renderer merged behind a refresh still applies.

  **The condition this depended on:** `metrics-store.data` was an Input of the merged callback, so
  it was not ready while that store's primary writer `update_metrics_store` (or
  `update_display_mode`, upstream of it) was pending. That poll is `running=`-gated and leaves
  gaps. A primary writer pending at every renderer pass would have locked the controls again. The
  old controls callback had those same two blockers, through the slider. F-CANOPY-054 (below)
  removed the condition: the controls callback is now clientside and reads the store as State. The
  new
  `src/tests/unit/frontend/test_f048_replay_cycle.py` also fails CI on any Input-graph cycle
  across two or more distinct callbacks anywhere in the built app. Canopy never runs the dev-tools
  check that would have caught this. Two pre-existing cycles are exempted by name, CAN-016a tab
  restore/stamp and the CAN-015 replay-player control loop. Both close through `allow_duplicate`
  outputs, so neither is a readiness deadlock.
- **Pausing a metrics replay did not hold: a late tick restored `playing` with the interval off,
  so the label stuck at ⏸ and nothing moved (F-CANOPY-054).** After F-CANOPY-048 the replay state
  had two writers, each a server round trip away: the merged controls callback, and `replay_tick`,
  an `allow_duplicate` writer that computed the next state from the State read when its request was
  sent. With the page's response-delivery latency at ~5 s against a 250–1000 ms tick, a tick was
  in flight whenever the user paused. The pause disabled the interval, so no later tick evicted
  that one, and its response — computed from `playing` — landed after the pause.

  Moving only the tick clientside, the direction first recorded, does not fix it. The server
  controls callback read `replay-state.data` as an Input, so every clientside tick re-requested it,
  and dash-renderer drops an in-flight request whenever a new request of the same callback arrives
  (the requestedCallbacks observer's `wDuplicates` step). Every click made during playback would
  have been evicted. A clean room (juniper-ml
  `util/ad-hoc/2026-09-23_f054_replay_tick_cleanroom.py`, verdicts fixed before the first run, 3
  runs a shape) scored the old shape pause-undone 3/3, the tick-only shape click-dropped 3/3, and
  this one pause-held 3/3, with the pause applied within 58 ms.

  Fixed by running the whole block in the browser, with **one** clientside callback as the only
  writer of `replay-state`. It handles the eight controls, the slider and the tick, and renders the
  slider, the position and the play label from the state it just computed. A clientside callback
  has no in-flight window: once it runs, nothing lands between its read and its apply, so nothing
  computes from a stale state. `replay_tick`, the play-label callback and
  `MetricsPanel._handle_replay_controls_handler` are removed. One click of each control has the old
  effect, checked under node against a verbatim copy of the old handler over the whole grid.
  - **Events come from values, not from triggers.** Clientside callbacks share the renderer's 12
    execution slots, so a request can still lose its trigger BEFORE it runs. A request waiting in
    `prioritized` is replaced by the next tick's request of the same callback, and only requests
    still in `requested` merge their changed-prop ids. With trigger-only dispatch, review lost the
    pause 3/3 under forced slot saturation and 2 of 12 under a dynamic load (juniper-ml
    `reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_round1.md`, Lane B). So
    the state records each button's count as of its last applied click (`clicks`) and the slider
    value this callback last wrote (`slider_w`), and anything above those is applied at the next
    run, before that run's own triggers. A lost pause now applies at this callback's next run to
    get a slot (seconds, under sustained contention) instead of never.
  - **A trigger alone applies nothing.** A button applies exactly its unapplied clicks. A run can
    apply a click from its count after the click wrote `n_clicks` and before the click's own
    request ran; the first revision also applied every trigger at least once, so that request
    applied the click again, undoing the pause or stepping two rows (juniper-ml
    `…/2026-09-23_validator_reports_round2.md`, Lane B2). For the same reason, a slider trigger
    carrying the value this callback last wrote is not a seek: re-read, it can land one row low.
    The cost (round 3): a real drag that lands exactly on that value does not pause the replay.
    The value is a whole number only at row 0, the last row, or a row where the max divides
    100 × row.
  - **Several pending play clicks toggle once,** as stock Dash does for a merged double click: a
    lost pause followed by the user pausing again pauses, where counting by parity would cancel
    the two. It only helps when both are pending in one run; a repeat made after the pause
    applied, but before the page shows it, still toggles back.
  - **A cleared slider number box is not a seek.** dcc.Slider sends `NaN` when its box is cleared;
    the state keeps its index and the slider is written back.
  - **`metrics-store.data` is now State.** The store's primary writer is pending most of the time,
    and dash-renderer holds a callback while any of its Inputs is downstream of a pending one, so
    the controls waited on every poll. Now no pending callback holds back their readiness
    (`test_nothing_pending_can_hold_the_replay_controls`, on the built app). A ready run can still
    wait for an execution slot; "Events come from values" above covers what that can lose. A
    refill re-renders
    the "/ max" half of the position through a second clientside callback. The position is two
    spans, and only the controls write the index, so a refill that runs in the same renderer pass
    as a click cannot overwrite the click's index with a stale one. The slider thumb catches up on
    the next control or tick, because nothing else may write the slider this callback reads as a
    seek.
  - **Ticks are counted.** The renderer merges queued requests of one callback, and `n_intervals`
    is read at execution, so the state records the last count it consumed (`tick_n`, an optional
    key) and a tick advances by the difference.
  - **The end of the replay stops the interval.** `replay_tick` set `stopped` and left the
    interval running: a server round trip a second, and two refreshes, until the next click.
  - `src/tests/unit/frontend/test_f054_replay_block_clientside.py` is new. It covers wiring on the
    built app, a source backstop that runs without node, and the registered JavaScript executed
    under node, including lost clicks and seeks, a cleared slider box, a grown history, and a click
    applied from its count that its own request must not apply again. Every test fails on the
    parent. Each textual mutation of the fix is caught by a behavioural test, not only by the
    source pins.
  - Sixty replay tests are removed from `test_metrics_panel_handlers.py` (38) and
    `test_metrics_panel_helpers_coverage.py` (22). Forty-seven, in seven classes, never called
    production code: they re-implemented the logic inline and asserted on their own copy. Twelve
    guarded their body with `if func := callbacks.get(...)` and would have passed silently once the
    callbacks were gone; one looked the merged callback up directly. The tests in
    `test_f048_replay_cycle.py` that exercised the Python handler moved to the new file and run on
    the JavaScript; that file keeps the F-CANOPY-048 graph invariants.
- **Re-staging from the restart modal dropped a seeded generator's params, so equities 422'd.**
  `_restage_dataset` sent the typed spiral fields and never the registry seed. Confirming an
  edited dataset in the modal therefore sent `equities` without `symbols`, and a default
  deployment refuses the whole 503-name universe against the symbol cap. It also sent `mnist`
  without `flatten`. It now sends the seed as `nn_dataset_params`, exactly as Apply Dataset does.
  The modal renders no schema-driven params, so a custom list applied earlier from the sidebar
  is not carried: the modal re-stages what it displays. Found, and reproduced on `main`, by
  the registry-repair pass (canopy#665). Mutation-checked: without the seed, five of the new
  `TestRestageDataset` cases fail. Two stale comments in the same file still said the gate
  *snaps*; since canopy#652 it clears.
- **The live dataset swap dropped a seeded generator's params too, and sent the spiral fields for
  every generator.** The swap built its own body: the four typed spiral fields whatever the
  generator, and never `nn_dataset_params`. A swap to `equities` therefore lost `symbols` and a
  swap to `mnist` lost `flatten`, the restart-modal defect above on the third path that stages a
  dataset. Apply Dataset and the swap now build one body, in `_dataset_stage_payload`: the
  registry seed and the rendered schema fields for a non-spiral generator, the typed fields for
  spiral. The swap's callback reads the schema-driven fields as State, as `apply_dataset` does.
  `src/tests/regression/test_staging_paths_send_one_payload.py` pins the two bodies equal for every
  dataset type, and pins the seed itself, because parity alone still passes when the shared builder
  loses the seed on both paths. Mutation-checked at six sites, that one included.
- **The `unknown` availability state could never fire for the outage it was built for.**
  `/api/dataset/generators` caught a juniper-data failure and answered HTTP 200 with four
  built-in demo generators carrying no `available` flag, so an outage and an answer were
  indistinguishable to every caller. The dashboard therefore read availability as *known*,
  and `is_generator_available`'s fail-open default reported `equities_seq` selectable
  against a service that was not running. The route now reports `upstream_unavailable`
  (attempted and did not answer), which the dashboard translates to *unknown*. Deliberately
  false when juniper-data is unconfigured: that is demo mode, where the built-in four are
  the offering and availability is known.
- **`test_multiple_clients_receive_state_on_connect` failed on about 7% of runs locally, and
  could not see a dropped connect-time `state`.** The Scheduled Tests lane went red on
  2026-09-22 (run 35694265700, 3.13 leg) with *"initial_status was not received before
  state"*. The `/ws/training` handler unicasts `connection_established` → `initial_status` →
  `state`, strictly in that order. But `connect()` adds the socket to the broadcast set
  (`websocket_manager.py:381`) before the handler awaits `offload(backend.get_status)`
  (`main.py:830`), a thread hop since X7 slice 1a (#567). A demo `metrics` + `state` broadcast
  queued during that hop is delivered first, and the test helper took the first `state` it
  saw for the connect-time one. Reproduced at 22/300, 22/300 under pinned CPU contention and
  21/300 on a re-run. Every failing session's full wire order was `connection_established >
  metrics > state > initial_status > state`: nothing dropped, only a broadcast delivered
  early. With a synchronous `get_status` (the pre-#567 shape) patched in locally the rate was
  0/300, which pins the hop as the window.

  Not a product defect. The handler's own order never broke, and the one in-repo consumer
  (`ws_dash_bridge.js`) registers no `initial_status` handler and treats `state` as
  latest-wins. `docs/api/API_REFERENCE.md` claimed `initial_status` precedes steady-state
  messages; it now states the real contract. The test fixture tags every
  `WebSocketManager.broadcast` frame (test-only; production payloads are untouched). The
  helper skips tagged frames and asserts the exact unicast order, which makes it deterministic
  (0/300, 0/300 contended, 400/400 across 25 passes of the whole file) and strictly stronger.
  With the handler's connect-time `state` deleted, the old helper still passed, because the
  next broadcast `state` stood in for it; the new one fails, as it does for a dropped
  `initial_status` or a `state` sent before it. An instrument guard fails if the tag stops
  reaching the wire. The file's other two classes (eight tests, the helper's own regression
  pins among them) had no `integration` marker, so every CI lane deselected them; they now
  run.
- **The WS keepalive tests asserted that the loop ticked fast enough, not that it ticked.**
  Both `TestWebSocketKeepalive` tests (`test_main_import_and_lifespan.py`) slept a fixed
  0.05 s against a 0.01 s interval and required two pings, two of five expected ticks. A
  runner that stalls the event loop for a few tens of milliseconds fails them: reproduced at
  2/400 on one saturated core (`assert 1 >= 2`). They now poll until the condition holds or a
  5 s deadline passes, stop early if the task ends, and assert that it is still running. A
  loop that does not repeat, or that dies on a broadcast error, fails with a message that says
  so. `test_concurrent_broadcast_from_thread_delivers_all` (`test_async_sync_boundary.py`) had
  the same shape (a fixed 0.5 s, then `call_count >= 15`) and gets the same bounded poll.
  After: 0/400 and 0/100 on the saturated core. No production constant changed;
  `HEALTH_DEADLINE_SECONDS` is untouched (canopy#649).
- **A conflict notice claimed to have cleared a dataset that was never selected.** With the
  dataset at `⊥`, any gate re-fire rendered *"none is not compatible with CasCor
  (Cascade-Correlation), so it was cleared"* — the literal string `none` from
  `_dataset_label(None)`, describing a state change that did not occur. Reachable since the
  OQ-6 ratification made `⊥` a state the gate clears into. `⊥` is no longer treated as a
  conflict; a genuine conflict still clears and still names the real dataset.
- **Registry and test prose still described the dataset snap that the OQ-6 ratification deleted.**
  `model_registry.py` said seed order "decides which dataset the operator lands on when they pick
  Recurrence". Since canopy#652 the sidebar gate clears a stranded dataset to `⊥` instead. Order
  still decides two things: the order the dropdown offers, and the restart modal's fallback, which
  keeps its `enabled[0]` swap by owner ruling. The registry comment and six test comments and
  docstrings now say that, rather than that order no longer matters.
- **G11 was enforced by listing names, and the constant it cited did not exist.** The registry
  pointed at `UNBOUNDED_IMPORT_GENERATORS`, which occurred nowhere else in the repository, and no
  test iterated `DATASET_TYPES`, so a new seed with unbounded `default_params` passed every test.
  `SEEDED_GENERATOR_BOUNDS` now classifies every seeded generator: either bounded by its own
  defaults, with the reason, or importing an unbounded universe, with the `default_params` keys
  that bound it. `TestG11EverySeedIsBounded` fails on an unclassified seed, and on an import whose
  seed does not pin a bounding key to a bounded value.
- **No test required a seed to be trainable by any model.** juniper-data emits a `structured` task
  type (juniper-data#402) that no `ModelSpec` accepts, so a `structured` seed would be greyed out
  under every model. The test that appeared to guard this checked only that the sidebar hint was
  not `None`, and the hint for such a seed is the string "no compatible models". A per-seed test
  now requires a compatible model, and the hint test rejects the warning string.
- **Nothing pinned that canopy never sends `allow_truncation`, and since juniper-data 0.15.0 an
  explicit `false` refuses.** juniper-data#418 made the flag a tri-state, so `false` now returns 422
  on any shortfall (an over-cap universe, or unresolvable fundamentals) even where the deployment
  opted in. The form already withheld the field. The registry seed, which bypasses the form's
  filter by design, and the Apply, one-shot Start and restart-modal bodies were unpinned.
  `TestNoPathSendsAPartialDataStance` now covers each of them for every seed. The shortfall prompt,
  which sends `true`, is the one deliberate sender. An equities test that accepted a seeded
  `allow_truncation: true` in place of a `symbols` list no longer does.
- **The `equities` seed's evidence was re-measured at generator 5.0.0.** It had been measured at
  3.0.0 and marked stale. At 5.0.0 (juniper-data 68c3cd7), on the service path, the seed generates
  X_train (15877, 15), X_val (1986, 15) and X_test (1982, 15) with no non-finite values. The matrix
  has 15 columns because 4.0.0 dropped `adj_close`. CasCor fits it, recruiting 4 units. The
  `equities_seq` seed now generates 15,557 windows of (64, 15); its LMU fit was not re-measured.
  `KNOWN_UPSTREAM_GENERATORS` was re-checked against juniper-data main and is unchanged at 16.
- **The Candidate Metrics panel never applied a store write after mount, so during a live candidate
  phase its badge read `Inactive` while `/api/state` said `Training` (F-CANOPY-053, provisional id).**
  `fetch_training_state` writes `candidate-metrics-panel-training-state-store` and
  `-pool-history-store` off the panel's own `candidate-metrics-panel-update-interval`. Measured on
  `9bffaba1` with the candidates tab open: every response carried a new store value (**27 of 27** at
  idle, **34 of 34** across a live candidate phase), the wire round trip was ~30 ms, and requests
  never overlapped on the wire — yet the renderer held **one** store value across 20–27 reads, while
  a positive control (`metrics-panel-training-state-store`) changed 10 times in the same kind of run.
  The status badge, phase, pool size, epoch progress, pool details and the pool-history cards were
  all frozen at their mount values. It is F-CANOPY-035's mechanism on the next panel over: the tick
  re-requested the callback under the same `getUniqueIdentifier` before the previous response was
  applied, so dash-renderer evicted the `watched` entry (`dash_renderer.dev.js:3027`) and discarded
  the response on arrival (`:2698`).

  **Landing is period-bound, measured directly.** Writes landed / issued across three live runs were
  **0 / 225** at 1000 ms, **5 / 39** at 4000 ms and **23 / 24** at 10000 ms, so the panel now polls
  at `CANDIDATE_STATE_POLL_INTERVAL_MS` (10 s). Two supporting changes stop the store churning.
  First, a payload that differs from the store only in its per-call `timestamp`, or in
  `stale_age_seconds` during an upstream outage, returns `no_update`. The store rides as its own
  writer's State, as in F-CANOPY-039. Second, a failed fetch now holds the last good state instead
  of writing `{}`, which the badge rendered as `Inactive`.

  **Deliberately not #613's `running=` guard.** A guard's release writes a *fixed* value from
  `completeJob()` after every run, including the 204 this callback answers on page load and on every
  other tab. This lane is tab-gated, so a guard on `disabled` would write `False` right after the
  CAN-000/tab gate wrote `True` and keep the poller running on a hidden tab: F-CANOPY-027, back.
  An evicted request's release would also reopen the clock while its successor is in flight. The gate
  stays the only writer of this interval's `disabled`, and a registry-wide test now fails any
  `running=` guard that writes a tab-gated lane's `disabled`. The cost is a candidate-panel refresh
  of up to 10 s plus apply latency. That the renderer now applies the writes is a live property,
  which the unit tests cannot show.

### Security

- **canopy picks up the two shared security patches**: `requirements.lock` moves
  `juniper-observability` 0.4.0 -> 0.4.1 and `juniper-service-core` 0.7.0 -> 0.7.1, and nothing
  else. observability 0.4.1's `configure_sentry`, which canopy calls, no longer sends frame-local
  variables to Sentry, and they could hold the real API key. service-core 0.7.1 fixes `APIKeyAuth`
  and `FailedAuthThrottle`; canopy's own copies live in `src/security.py`, so that pin is
  consistency with the sibling services. The lock was regenerated with `--upgrade-package` for the
  two packages only (60 pins; the freshness gate's constraint-mode resolution reproduces them).
  `pyproject.toml` now floors both as well, at `juniper-observability>=0.4.1` and
  `juniper-service-core>=0.7.1` (owner-approved), so an install of canopy 0.9.0 cannot resolve the
  unpatched releases. The boot-time `enforce_dependency_floors` reads the **installed** metadata,
  so an existing editable install keeps booting until it is reinstalled; the reinstall upgrades it.
- **`APIKeyAuth` now carries the blank-key filter and the non-short-circuiting compare that its
  sibling copies carry (APD-ECO-008).** `src/security.py` is the fourth copy of the ecosystem's
  `APIKeyAuth`. `validate` used `any(hmac.compare_digest(...))`, which stops at the first match,
  so the number of comparisons depended on where the matching key fell. It now walks every key, as
  juniper-data does and as juniper-cascor and juniper-service-core do on `main`. The fix is
  unreleased in juniper-service-core: the 0.7.0 wheel that `requirements.lock` pins still ships
  `any(...)`. The constructor also kept blank entries, which all three siblings drop; now it drops
  them too.

  **Behaviour change: a whitespace-only `CANOPY_API_KEY` environment variable now DISABLES auth.**
  It used to enable it. Only the env var reaches this case, because `get_secret` strips a secret
  *file*, and an empty key was already treated as unset. The boot-time posture check already
  classified such a key as absent and logged "running OPEN"; that log line is now true. What
  opens is the posture canopy documents for no key at all:

  - **Every key-gated route now serves anyone who can reach the port. This is the largest thing
    that opens.** A key of ASCII spaces and tabs enabled auth on a key no caller could present:
    both uvicorn parsers, h11 and httptools, strip an all-space or all-tab `X-API-Key` to an empty
    value. So `SecurityMiddleware` refused every caller, with a key or without, on every route
    outside its exempt sets. Those routes now answer exactly as they do with no key configured. A
    sweep of `app.routes` on `48074653` (the commit #660 merged onto) and on `3a6dea95` (#660)
    counts **56** key-gated (method, path) pairs. A keyless request to each got 401 before and
    reaches its handler after. **27** of them change state, among them `/api/set_params`,
    `/api/model/select`, `POST /api/admin/experimental_functions`, `/api/dataset/generate` and
    both dataset imports, `/api/stage_dataset`, `/api/live_dataset_swap`,
    `PATCH /api/v1/network/weights`, `/api/v1/network/hidden-units`, snapshot restore, resume,
    retrain and replay, and `/api/remote/*`. All **26** parameterless GETs went from 401 to 200.
    The exempt sets (`/`, the health routes, `/dashboard`, `/metrics`) and the browser surface
    (`/api/csrf`, `/api/train/*`, next bullet) are not in these counts.
    `util/ad-hoc/2026-09-23_blank_api_key_route_sweep.py` reproduces the figures. The claim that no
    caller could present the key holds for every `str.strip()` character except U+00A0/U+0085, and,
    under h11 only, U+001C–U+001F. Measured on uvicorn 0.49.0 with raw socket bytes (the same
    script's `header-probe`): both parsers strip an all-space or all-tab value to empty and refuse
    U+000B and U+000C with a 400, and CR and LF end the header line. httptools, canopy's default
    parser, also refuses U+001C–U+001F. h11 passes them, and under h11 a key of those authenticated
    normally. U+00A0 and U+0085 pass both parsers, but `hmac.compare_digest` raises `TypeError` on
    non-ASCII text, so every keyed request got a 500. No other `str.strip()` character can arrive,
    because Starlette decodes header bytes as latin-1. All of these keys now count as no key too.
  - **The browser control surface loses its Origin/CSRF gate.** While auth was enabled, a keyless
    `/api/train/*` request had to pass the Origin allowlist and a CSRF token under the default
    flags; with `browser_control_auth_enabled` off, it needed the key outright. With auth disabled,
    `require_browser_control_auth` returns before either check, so all six state-changing
    `/api/train/*` POSTs accept a cross-site POST, and `/api/csrf` stops refusing disallowed
    origins.
  - **With `JUNIPER_CANOPY_WS_AUTH_ENABLED=true`** (SEC-06, default false), every WebSocket
    connection used to be refused, because no bearer token could match a blank key. Now any bearer
    token is admitted.
  - **Not an exposure, before or after:** the WebSocket `?api_key=` query parameter is decoded but
    never trimmed, so it could present the whitespace key. That gained nothing, because all three
    WebSocket routes already admit a keyless connection (`allow_browser_auth=True`) behind the same
    Origin and CSRF gates.

  Only a launch with a whitespace-only `CANOPY_API_KEY` env var and `JUNIPER_CANOPY_REQUIRE_AUTH`
  false (canopy's code default) reaches this configuration. Under `true`, the boot still fails with
  `AuthPostureError` unless `JUNIPER_SKIP_AUTH_POSTURE_CHECK` bypasses the check. juniper-deploy
  supplies the key through `CANOPY_API_KEY_FILE`, which is stripped, and its secured compose
  service defaults `JUNIPER_CANOPY_REQUIRE_AUTH=true`, so no deploy profile reaches it.

  Startup now logs a distinct WARNING when the key is set but blank. It is emitted once per
  process, after `configure_logging` has run, through the system logger, so it carries its level
  and format, lands in `logs/system.log`, and reaches Sentry when a DSN is configured. It follows
  the posture check whichever way that check goes. When the boot proceeds, it comes right after the
  check. When `JUNIPER_CANOPY_REQUIRE_AUTH=true` makes the check refuse to start, it follows the
  check's CRITICAL, which says no key is configured. It is then worded for a refused boot: the blank
  key counts as no key, and canopy refuses to start. The refusal propagates unchanged. (#678 logged
  nothing on that path, because the posture call raised before the report was reached; the #678
  follow-up fixed that.) The secret is read at import, before logging is configured, so the read only
  records which source was blank, and the lifespan reports it. The WARNING names that source,
  `CANOPY_API_KEY` or the file named by `CANOPY_API_KEY_FILE`, and gives the remedy for it.
  `CANOPY_API_KEY_FILE` wins whenever it names an existing file, so a blank file beside a real
  `CANOPY_API_KEY` also disables auth, as it did before #660, and the remedy there is the file. The
  WARNING never includes the value.

  This entry supersedes the message of commit `3a6dea95`, which predates #660's correction: that
  message still says the WebSocket `?api_key=` fallback "could still present" the key, and it
  names only "One real behaviour change".
- **A padded `CANOPY_API_KEY` no longer leaks into the logs, and the blank-key rule reaches the
  key's two other readers (#678 follow-up).**
  - **The leak predates #660.** A key with leading whitespace or a line break is not blank, so it
    ENABLES auth, exactly as set. The dashboard's server-side self-calls sent it as `X-API-Key`.
    `requests` refuses such a value, and its `InvalidHeader` message quotes the whole value. 54 of
    the 64 self-call sites log that text or return it, and several show it in a dashboard alert. So
    the real key reached `logs/*.log`, the console and, when a Sentry DSN is configured, Sentry
    Logs. With `CANOPY_API_KEY` set to the test value ` leaked-key-XYZ123` (one leading space), canopy
    logged `Selection hydration read failed (Invalid leading whitespace ... ' leaked-key-XYZ123')` at
    WARNING.
    - `frontend/internal_api.py` now leaves off any key `requests` refuses to send. It asks
      `requests` itself, so no self-call can raise that error. The fix is in the one helper every
      self-call uses, not in the 54 sites, so a new site cannot reopen the leak.
    - Auth stays enabled on such a key as set. The self-calls are now refused instead, and a refusal
      carries nothing of the key.
    - `util/ad-hoc/2026-09-24_self_call_error_text_census.py` lists all 64 sites.
  - **Boot WARNs once about a padded key.** It uses the system logger, beside the blank-key
    WARNING. The key is not stripped and the boot is not refused, because either would change which
    key authenticates. No HTTP header carries such a key reliably: uvicorn's parsers drop a value's
    leading spaces and tabs, h11 also drops its trailing ones, and a header cannot hold a line break.
  - **Boot WARNs when `CANOPY_API_KEY_FILE` names no existing file.** It was ignored silently,
    exactly as if unset, so a typo in the path fell through to `CANOPY_API_KEY` without a word. The
    WARNING names the variable and never the path it holds. An operator who confuses the two
    variables puts the key itself there.
  - **A whitespace-only `CANOPY_API_KEY` env var now also serves the interactive docs, and its
    self-calls send no key.** Both readers used the raw value.
    - `_docs_enabled` kept `/docs`, `/docs/oauth2-redirect`, `/openapi.json` and `/redoc` at 404.
    - The self-calls sent the whitespace key, which `requests` refuses, so every one failed although
      auth was off.
    - Both now apply `APIKeyAuth`'s blank rule. The blank-key WARNING's "exactly as with no key
      configured" is now true of every reader.
    - **The four docs routes now answer 200 to anyone who can reach the port**, as they do with no
      key.
  - **Tests.**
    - `src/tests/regression/test_blank_api_key_warning_boot.py` now also boots canopy in a fresh
      interpreter: a real `import main` with the key set, the real lifespan, and canopy's own
      `logs/system.log`. Its in-process tests rebuild the auth singleton themselves. So a `main.py`
      that built `APIKeyAuth` without `get_api_key_auth()` passed the whole CI lane (6866 tests),
      while real uvicorn logged no blank-key line anywhere. That mutant now fails.
    - A second fresh boot, with a padded key and a missing key file, drives eight real dashboard
      handlers under five padded keys. No log record from any logger carries the key, and nor do the
      log files, the console or the handlers' results.
    - Unit tests: `src/tests/unit/frontend/test_internal_api_key_rules.py` (new),
      `src/tests/unit/test_security.py` and `src/tests/unit/test_secrets_util.py`, including the new
      `secrets_util.resolve_secret_detail`. The `get_secret` test now asserts literal values.
- **Outbound keys are checked where they are read, and no transport error or compare frame can leak a
  secret (#683 validation).** The independent validation of juniper-canopy#683 found two HIGH secret
  exposures and two LOW gaps. The owner ruled on 2026-09-24: "Fix everywhere now".
  - **A padded outbound key leaked, to an anonymous caller.** canopy sends three keys as `X-API-Key`:
    juniper-cascor's (`JUNIPER_CASCOR_API_KEY`, falling back to `JUNIPER_DATA_API_KEY`), juniper-data's
    (`JUNIPER_CANOPY_JUNIPER_DATA_API_KEY`, then `JUNIPER_DATA_API_KEY`) and the recurrence service's. All
    three were read raw. An HTTP client refuses a value with padding, a line break or a non-ASCII character,
    and its refusal quotes the value: `requests`' `InvalidHeader`, httpx's `Illegal header value b'...'`,
    websockets 17.1's `invalid X-API-Key header: ...` (websockets 16.0 sent it raw instead, line breaks
    included). canopy logged that text at ERROR on every status-refresher tick, Sentry received it, and canopy
    returned it in API bodies. With canopy auth enabled, a keyless CSRF mint and a `POST /api/train/start`
    from an allowlisted Origin answered a 409 whose `detail` held the cascor key.
    - `secrets_util.get_outbound_secret` now reads each key and refuses a value that is not printable ASCII
      other than space (`0x21`-`0x7E`), the union of the three clients' rules. It refuses a space or tab
      inside a key too, which the clients would carry. A refused value is treated exactly like an empty one:
      the next variable in the order applies, or no key is sent. Boot logs one WARNING per variable, naming
      it and never its value or a path, through the system logger. The keys `settings` reads at import are
      reported right after the auth-posture check, and the cascor key right after `create_backend` reads it.
    - Handed no key, every juniper client reads the same variables itself (`api_key or
      os.environ.get(...)`), raw, so a refused key came straight back. `secrets_util.bind_outbound_key`
      switches that fallback off at canopy's five construction sites: the cascor REST client, both cascor
      WebSocket streams and both juniper-data clients. **Behaviour change:** canopy is now the only reader
      of its outbound keys, so a blank `*_API_KEY_FILE` that shadows a real env var now sends no key, as
      canopy's precedence says. The client library used to fall back to the env var.
    - **What a caller reads about a failed outbound call is the upstream's answer or the exception's
      type, never its transport text** (`outbound_errors.outbound_error_text`). This covers the cascor
      adapter's `{"error": ...}` envelopes, the Start, pause, resume and reset 409s and their WebSocket
      acknowledgements, the `/api/status` envelope's `error`, `/api/stream_health`'s
      `last_disconnect_reason`, a failed recurrence fit's `completion_reason`, and the 500 details of the
      snapshot create, replay, resume and retrain routes and the network-mutation routes. An exception that
      carries an HTTP status is the upstream's answer, so its text passes: cascor's 409 `Training data not
      provided` and a 422's field errors still reach the UI, as PR-B2, N4 and CAN-015h surface them.
      Anything else is named by type, for example `JuniperCascorConnectionError`. The full text still goes to
      canopy's logs, where it can no longer hold a key.
  - **One anonymous request wrote the real `CANOPY_API_KEY` into Sentry.** `APIKeyAuth.validate` ran
    `hmac.compare_digest` on two `str`, which raises `TypeError` for non-ASCII input, and both uvicorn
    parsers pass `X-API-Key: \xa0`. The request was a 500, and Sentry's event recorded the comparing frame's
    locals, among them `candidate`, the real key. `validate` now compares UTF-8 bytes (`surrogatepass`, so
    every `str` encodes) and refuses a key that is not a `str`. Such a header is a 401. A WebSocket
    presenting one as `X-API-Key` or `?api_key=` is closed 4001, and as a bearer token 1008, as any wrong
    key is. canopy's two other `str` compares get the same fix:
    - **The rate limiter's `X-Canopy-Internal` compare.** With rate limiting on, it runs on the key-exempt
      `/api/csrf` and `/api/train/*` too, so an ANONYMOUS caller could force the 500. A keyed caller's 500
      recorded that caller's key.
    - **The CSRF store.** It compares against every session's token, so a keyless non-ASCII `X-CSRF-Token`
      recorded another session's live token (`stored_token`, a name the SDK's scrubber does not filter).
      A `/ws/control` first frame whose `csrf_token` is not a `str`, or is non-ASCII, raised there too. The
      handler's catch-all then filed it as `malformed_auth`, and it is now an ordinary `invalid_token`.

    The markers juniper-ml's `tests/test_service_fork_drift.py` requires are kept. canopy
    configures Sentry only through `juniper_observability.configure_sentry`. In juniper-observability
    0.4.0, the release canopy's lock pins, that leaves `include_local_variables` at the SDK default, `True`.
    juniper-ml#2086 turns it off in the shared package and strips any frame `vars` that still reach
    `before_send`, but no release carries that yet. Until one does, any unhandled exception during a keyed
    request can record the caller's key. The rate-limiter 500 recorded it through the ASGI `scope` a frame
    held: the scope's `headers` list carries `x-api-key`, and the scrubber, which filters a local named
    `api_key`, does not reach into that list. This change removes the three 500s that a caller could trigger
    at will, but not that class.
  - **`_docs_enabled` is now the auth handler's own answer** (`not get_api_key_auth().enabled`). #683
    re-derived the blank rule there, with its own read and its own strip, and one sample pinned it. A copy
    that stripped only ASCII whitespace, or ignored `CANOPY_API_KEY_FILE`, passed. No behaviour changes.
  - **The padded-key WARNING names `CANOPY_API_KEY_FILE` when the file supplied the key.** A key file is
    stripped at both ends, so only a line break inside the key can pad it, and the WARNING hard-coded
    `CANOPY_API_KEY` and that variable's advice. It now has one wording per source, as the blank-key WARNING
    does, and the comment claiming that only the env var can be padded is corrected.
  - **Tests.**
    - `src/tests/unit/test_outbound_keys.py` (new) pins the rule, the report, the binding against the real
      client classes, and canopy's call sites.
    - `src/tests/unit/test_outbound_errors.py` (new) pins the describer, every adapter site, and the proxy
      routes. A static census asserts that no `except` handler in the adapter builds caller-visible text any
      other way.
    - `src/tests/regression/test_outbound_secret_leaks_boot.py` (new) boots canopy in fresh interpreters
      against a local fake upstream. No request, log record, log file, console line or API body carries a
      padded key, and the anonymous Start answers without it. A non-ASCII presented key is a 401 or a 4001.
      The docs follow the auth switch for a real env key, a real key file and every blank key, NBSP-only
      included.
    - `src/tests/unit/test_security.py::TestNoSecretCompareCanRaiseOverHttp` (new) drives each of the three
      compares over HTTP, through canopy's own `SecurityMiddleware` with the rate limiter on. A non-ASCII
      `X-API-Key` is a 401. A non-ASCII `X-Canopy-Internal` on anonymous `/api/csrf` gets a 200 and no
      exemption. A non-ASCII `X-CSRF-Token` gets a 403. The spy test on `validate` now asserts one
      comparison per key, with the match first and both sides as bytes, so a `break` after the match fails it.
    - `src/tests/unit/test_phase_b_pre_b_csrf.py`: a `/ws/control` first frame whose `csrf_token` is an int,
      a list, a dict or non-ASCII is closed 1008 as `invalid_token`.
    - Existing tests that asserted a transport failure's text now assert its type, and those that model
      cascor's answer now give the exception its HTTP status.
    - `util/ad-hoc/2026-09-24_683_validation_leak_probes.py` (new) keeps the validator's probes: the client
      libraries, the six padded-key boots, the anonymous Start, four Sentry cases under real uvicorn, the
      key-file WARNING and the docs switch. Run against #683's head, every leak reproduces. Run against this
      change, none does.
    - `util/ad-hoc/2026-09-24_683_validation_mutation_check.py` applies 44 mutations to copies of the
      tree, and every one is caught. They include the validator's M2 and M3, and they put the pre-fix code back
      at one site of each kind.
- **The WS-silent poll-liveness UI test no longer inherits a run that is about to converge** (test-only;
  `src/tests/ui/test_ws_silent_poll_liveness.py`). `_ensure_running_run` accepted any RUNNING run. On
  CI the demo converges about 31 epochs after a start, and the run the test inherited already held
  26-27 epochs. It produced no further epoch inside the 12 s window, so every later poll correctly
  answered `<no_update>` and `test_metrics_store_polls_on_long_lived_tab_with_ws_silent` failed with
  "poll starved". That happened
  twice on main at `0035253a` on 2026-10-03, and before that on canopy#636 and canopy#651 (canopy#637's
  shape). A live run past epoch 10 (`_MAX_INHERITED_EPOCH`) is now restarted with Reset then Start. That
  is the path the module's other four tests already took, and they passed in both failing runs. The
  mid-test keep-alive in `test_poll_resumes_rest_when_ws_goes_stale` passes `max_inherited_epoch=None`,
  so it never restarts a live run whose history it is about to read.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-canopy/blob/v0.9.0/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-canopy_v0.9.0.md`
