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
- has 33 Fixed entries in all, condensed below to one line each.

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

33 entries. Each line below is the entry's lead; the full text of every entry is in [CHANGELOG.md `[0.9.0]`](https://github.com/pcalnon/juniper-canopy/blob/v0.9.0/CHANGELOG.md). This section is condensed so that the archive fits one GitHub-signed commit (owner ruling 2026-10-17); every other section is complete.

- **The top status bar applies its periodic responses again, and the metrics store's poll no longer evicts itself in chains (F-CANOPY-055, F-CANOPY-058, F-CANOPY-068).**
- **`TestA422DetailReachesTheOperator` no longer reads the previous test's WARNING.**
- **A recurrence fit whose reply times out is followed, not failed, and a busy 409 names its holder (W1.5, canopy half; F-C4, F-CON1, F-CON2).**
- **The wheel again carries `outbound_errors`, which `main` imports.**
- **A recurrence fit sends the registry seed plus what the operator edited, and only parameters the generator declares. A preview above Start shows the request (W1.2; plan findings F-C2, F-C3).**
- **A refused recurrence request now says what to do, and a restored model counts as a model (W1.6; plan findings F-C5, F-C6, F-C7).**
- **The registry no longer claims the recurrence model is version 0.1.0 (W1.7; plan finding F-C8).**
- **A failed recurrence fit now says why: the service's 422 `detail` reaches the log, `completion_reason` and the status bar (W0.5; plan finding F-C1).**
- **The replay player's range plays its last frame, its sliders stop at the last frame, and its own renders no longer send control requests (follow-ups to F-CANOPY-059 and F-CANOPY-056).**
- **Against cascor, the replay player's controls take effect, and Stop ends the session (F-CANOPY-056, P1).**
- **Against cascor, the replay player shows its session again (F-CANOPY-059, P0; a regression from canopy#532).**
- **A Start refused because the staged dataset is wider than the network now says how to proceed (F1).**
- **The restart modal called Start fresh "functionally a clean stack launch" (F2).**
- **The sidebar said "Active: CasCor" before anything had asked the backend (X11).**
- **A model swap could strand the dashboard on a tab that no longer exists (Y4).**
- **Whether a selection control was greyed out was decided by the reason-string helpers, not by `compatible()` (Y8).**
- **The model table's Select button carried its reason only in `title=` (Y7, model-table half).**
- **An idle dashboard spent about a third of its response latency on a timer with nothing to do: the replay weight drain, a 2 Hz timer, ran on every tab for the life of the page.**
- **The entry above merged before its review's third round was applied. A comment and a test message still tied the weight drain to a "replay session" that a Stop does not end, and comments and docs described a weight emitter that never reached cascor's `main`. The new Interval tests crashed, instead of refusing, on an Interval with no id, and one of them also on a pattern-matching id.**
- **The replay controls never applied: play, step, start, end, the speed buttons and the slider did nothing on any page load (F-CANOPY-048).**
- **Pausing a metrics replay did not hold: a late tick restored `playing` with the interval off, so the label stuck at ⏸ and nothing moved (F-CANOPY-054).**
- **Re-staging from the restart modal dropped a seeded generator's params, so equities 422'd.**
- **The live dataset swap dropped a seeded generator's params too, and sent the spiral fields for every generator.**
- **The `unknown` availability state could never fire for the outage it was built for.**
- **`test_multiple_clients_receive_state_on_connect` failed on about 7% of runs locally, and could not see a dropped connect-time `state`.**
- **The WS keepalive tests asserted that the loop ticked fast enough, not that it ticked.**
- **A conflict notice claimed to have cleared a dataset that was never selected.**
- **Registry and test prose still described the dataset snap that the OQ-6 ratification deleted.**
- **G11 was enforced by listing names, and the constant it cited did not exist.**
- **No test required a seed to be trainable by any model.**
- **Nothing pinned that canopy never sends `allow_truncation`, and since juniper-data 0.15.0 an explicit `false` refuses.**
- **The `equities` seed's evidence was re-measured at generator 5.0.0.**
- **The Candidate Metrics panel never applied a store write after mount, so during a live candidate phase its badge read `Inactive` while `/api/state` said `Training` (F-CANOPY-053, provisional id).**

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
    Logs. `CANOPY_API_KEY=" leaked-key-XYZ123"` logged `Selection hydration read failed (Invalid
    leading whitespace ... ' leaked-key-XYZ123')` at WARNING.
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
