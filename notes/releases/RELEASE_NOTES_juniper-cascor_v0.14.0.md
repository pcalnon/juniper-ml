# juniper-cascor v0.14.0 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-11-15
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-cascor

---

This is a security-bearing release of `juniper-cascor` v0.14.0. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-cascor` |
| **Fixed in** | 0.14.0 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.14.0

### Added

- **API addition: `WebSocketManager.promote_to_active(websocket, *, replayed_through=None) -> bool`.** The
  keyword-only `replayed_through` argument and the `bool` return value are new (the method returned `None`).
  - **Without `replayed_through`** the promotion is unconditional, as it always was, and returns `True`. Existing
    callers, including the fresh-connect path, are unaffected.
  - **With it** (the `/ws/training` resume path passes the last seq the client now holds), a pending socket is
    first sent every buffered message numbered after that seq, in seq order, repeating until a check under the
    manager's lock finds none, and is activated with no `await` between that check and the activation. It returns
    `False`, and leaves the socket out of the broadcast set, when continuity cannot be kept: the replay buffer
    evicted a message the socket still needed, replay is disabled, `replayed_through` is above the last seq
    numbered, a send failed, or the socket was disconnected meanwhile. The caller should then close the socket. A
    socket that is already active is left alone: nothing is sent, and it returns `True`.
- **`api.websocket.training_stream.RESUME_INCOMPLETE_CLOSE_CODE` (`1011`) and `RESUME_INCOMPLETE_CLOSE_REASON`
  (`"Resume replay incomplete"`)**, the close a `/ws/training` client now receives when a resume cannot be completed
  without a gap once `resume_ok` was sent or attempted (see Fixed).
- **`replay_incomplete`, a fifth `outcome` of `cascor_ws_resume_requests_total`**
  (`api.observability.WS_RESUME_OUTCOME_REPLAY_INCOMPLETE`), counting those closes. `success` is now counted only
  once the resumed socket is active; such a resume used to count as `success`. `cascor_ws_resume_replayed_events`
  is likewise observed only for a completed resume, and still counts the replay snapshot only.

### Changed

- **`agents-md-touch-up.yml` pins `actions/checkout` to a commit SHA (owner ruling 2026-11-03).** It checked out with
  the `v7.0.1` tag, the only tag-only `actions/checkout` in `.github/workflows/`. It now uses
  `3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`, the commit that tag resolves to and the pin every other
  workflow here uses, so behaviour is unchanged. A census of the nine Juniper repositories' `main` on 2026-11-01 found
  249 `actions/checkout` uses, 242 pinned to that SHA; the seven tag-only ones were this workflow's copies, one per
  repository. juniper-data#503 pinned juniper-data's, and this change is one of the seven that pin the rest.
- **`create_app` opts out of FastAPI's native telemetry (owner ruling 2026-11-09).** FastAPI 0.142 added OpenTelemetry
  instrumentation of its own, with tracing, metrics, logs and operation spans on by default, and both locks pin FastAPI
  0.162.2. `create_app` now passes `telemetry=` with those four switches and `auto_configure` set to `False`, as
  juniper-data does (juniper-data#454), so FastAPI's instrumentation cannot overlap the service's configured
  observability (Sentry, Prometheus, structured logging). This is hardening, not a fix for a live leak: the
  instrumentation stays idle until an OpenTelemetry provider is configured, and the locks hold `opentelemetry-api`
  1.45.2 and no OpenTelemetry SDK. FastAPI can also set up export by itself, when `FASTAPI_OTEL_AUTO_CONFIGURE` is `true`
  and the environment names an OTLP endpoint; without the SDK that attempt only logs a startup warning, and the
  explicit `auto_configure: False` now rules it out. On FastAPI < 0.142, which `pyproject.toml` still admits, the
  keyword lands in `app.extra` and does nothing; the new test in `src/tests/unit/api/test_api_app.py` pins all five
  switches off and skips there.
- **The dependency locks moved** (`requirements.lock`, and `requirements-cpu.lock`, which the image installs),
  through the Dependabot updates merged since 0.13.0 (#744, #751) and #748's two security pins (Security, below).
  The notable runtime pins in `requirements-cpu.lock`: `fastapi` 0.162.0 -> 0.162.2, `pydantic` 2.14.1 -> 2.14.3
  (with `pydantic-core` 2.50.4 and `pydantic-settings` 2.16.2), `python-dateutil` 3.0.0 -> 4.0.0, `sentry-sdk`
  2.73.0 -> 2.74.0, `websockets` 17.3 -> 17.4, `anyio` 4.15.1 -> 4.16.0 and `cachetools` 7.2.5 -> 8.0.0, plus six
  smaller moves, and `six` leaves both locks. `requirements.lock` also moves the CUDA 13 wheels (`cuda-toolkit`
  13.0.3.0 -> 13.2.2, `triton` 3.8.0 -> 3.9.0 and the `nvidia-*` set). Apart from the two security floors
  (Security, below), the wheel's declared requirements are unchanged.

### Fixed

- **A 429 never says `Retry-After: 0`, and the wait it names is rounded up (APD-ECO-016; owner ruling 2026-11-09).**
  `RateLimiter.check` reported `int(window - elapsed)`, which truncates. A rejection in a window's last second
  therefore carried `Retry-After: 0` and `X-RateLimit-Reset: 0`, telling a client to retry at once into a limiter that
  rejects again, and every other fractional remainder was a second short (9.4s left said 9). The allowed path, which
  feeds `X-RateLimit-Reset`, truncated the same way. `FailedAuthThrottle.check` reported
  `max(1, int(window - elapsed))`: never 0, but still short by the fraction. All three now report
  `max(1, ceil(window - elapsed))`, as juniper-service-core's copies do (`APD-SVCCORE-004`, and its 0.7.2 for the
  throttle). juniper-cascor keeps its own copy of the limiter and the throttle (its service code imports only
  `enforce_auth_posture` from juniper-service-core), so those fixes never reached it.
  `src/tests/unit/api/test_retry_after_rounds_up.py` (44 tests, frozen clock) pins the rounding on both limiter paths,
  in the throttle, and in the headers and the message a caller receives. `test_api_security.py`'s 429 test now asserts
  `Retry-After >= 1` where it allowed 0; its 60-second window never produced a 0, so it states the contract and the
  new module is what fails on the old code. `docs/api/JUNIPER_CASCOR_API_REFERENCE.md` states the rounding. A
  robustness fix, not a leak.
- **The `Load from HDF5` benchmark times real loads. For 10 and 50 hidden units it timed the integrity gate's refusal.**
  - **The defect.** `src/tests/scripts/run_benchmarks.bash`'s serialization benchmark appended hidden units to `network.hidden_units` without resizing `output_weights`, which stayed `(2, 2)`. `85634ee` (2026-05-01) fixed the same omission in the forward-pass benchmark, which crashed on it; the serialization benchmark did not crash.
    - Its 10- and 50-unit snapshots declared 12 and 52 output-weight rows, so the serializer's integrity gate refused every load (`Output weights shape mismatch: torch.Size([2, 2]) != (12, 2)`).
    - `load_from_hdf5` returns `None` on a refusal rather than raising, so the benchmark timed the refusal and reported it as a load. `main`'s nightly run 41267421888 logged the refusals.
  - **The fix.** The benchmark resizes `output_weights` as the forward-pass benchmark does. It also loads each snapshot once before timing it, and raises if the load is refused.
  - **The exit status.** The harness ran as `eval … | tee` under `set -e` without `pipefail`, so a benchmark that raised still ended the script, and the `Performance Benchmarks` job, with 0. The script now takes the harness's failure from `PIPESTATUS` and exits non-zero. The job stays informational: the nightly's summary warns when it fails.
  - **Measured locally** on Python 3.14.7, running the harness's serialization benchmark with two iterations:
    - before the fix, 6 refused loads and a full load table;
    - after it, no refusals, 12 successful loads and a full load table;
    - a mutant without the resize raises at the 10-unit snapshot and exits 1.

    Run against a failing stub, the new exit-status lines exit 1, and the old two lines exit 0.
  - **Where it was found.** Reading that nightly for juniper-cascor#738. Owner ruling of 2026-11-01.
- **A fit that returns while its run is paused now settles `COMPLETED`. The lifecycle no longer wedges in `PAUSED` with no training thread behind it.**
  - **The defect.** Pause is honoured only at an interrupt checkpoint, which `_handle_event` runs on `epoch_end` and `phase_change` alone. A pause that landed after the fit's last checkpoint could not hold the fit, so the fit returned while the FSM was `PAUSED`. The window after the last checkpoint includes:
    - the rest of the final output pass after its last-epoch callback;
    - `CascorModel.fit`'s post-hoc `unit_added` / `training_end` events;
    - `_run_training`'s metrics drain, terminal weight capture and final evaluation.

    `_run_training` then called `mark_completed()`, which accepted only `STARTED`. It ignored the refusal and wrote `training_state` `Completed`, while the FSM stayed `PAUSED`. A start answered 409 (`Cannot start training while paused`), a resume moved the FSM to `STARTED` (still with no thread), and every later start answered 409 (`Training already in progress`) until a stop or reset.
  - **How far back.** Releases 0.10.0 to 0.13.0 wedge this way; 0.10.0 added the start-while-paused refusal (cascor#584). From 0.3.17 to 0.9.0 the FSM was left `PAUSED` too, but a start was accepted from `PAUSED` and recovered the run; a resume there moved the FSM to `STARTED` with no thread, after which every start was refused until a stop or reset. 0.3.17 also predates the interrupt checkpoint (cascor#244, first released in 0.5.0), so there no pause held the fit, and any pause still in place when it returned left the FSM `PAUSED`.
  - **The fix.** `mark_completed` accepts `PAUSED` as well as `STARTED`, as `mark_failed` already did, and `_run_training` settles a returned fit with that one transition, then reopens `_pause_event`. The run settles `COMPLETED` exactly as an unpaused run does. `TrainingStateMachine` now makes every transition under its own lock, so a pause or resume that races the settle either lands wholly before that transition and is settled with the run, or finds `COMPLETED` and is refused.
    - **Why one transition.** Neither the settle nor `pause_training` takes a lock, so releasing the pause through `RESUME` and then calling a `STARTED`-only `mark_completed` leaves a `STARTED` step between two transitions, and a second pause that lands there leaves the run `PAUSED` again. juniper-service-core can release a pause that way because its settle, pause and resume hold one manager lock; cascor's settle cannot take `self._lock`, which `swap_dataset_live` holds while it joins the training future.
    - **Why the state machine's lock.** `_handle_resume` checks `PAUSED` and then calls `_restore_from_paused`, which writes `STARTED`. A thread switch at that call let the settle's one transition complete the run in between, and the resume then wrote `STARTED` over `COMPLETED` with no thread behind it, so every start was refused until a stop or reset. Uninstrumented that needs a switch at one call boundary, and 800 runs that raced a resume against the settle never hit it, but forced it happens every time, and one transition is only safe if no other transition can run inside it. Each public `TrainingStateMachine` method that changes state, or reads more than one field, now holds the machine's own `RLock`. The machine calls nothing outside itself while holding it, other than its logger, so the lock cannot join a lock-order cycle.
    - **Still possible, and not a wedge.** A pause or resume whose state check passed just before the settle still answers 200, and leaves `training_state.status` reading `Paused` or `Started` beside a `COMPLETED` FSM until the next start; a pause can also leave `_pause_event` clear, which that start reopens. `pause_training` and `resume_training` ignore the FSM's refusal, as before.
  - **Only the run that owns the lifecycle settles it.** A run takes ownership as it enters `_run_training`, before it issues `Command.START`. A fit that returns, is interrupted or fails after a newer run has entered now leaves five things to that run: the FSM, `training_state`, the final score, the terminal session counter and the monitor session. It logs a WARNING instead.
    - **Why.** juniper-service-core's fix for the same wedge, built before this one, first released the pause without such a check, and its validation showed a stale fit resuming or completing a newer paused run.
    - **When it applies.** cascor's single-worker executor serializes runs, so the check matters only when a run is started after `shutdown()` has dropped the executor while an older fit is still alive (its bounded join timed out). The service calls `shutdown()` only as it exits, so only in-process callers, such as tests, reach it. All five settles are guarded: the post-fit stop, the completion, the interrupt, the failure and the monitor session end.
    - **What it does not cover.** A stale fit's live events, its post-fit metrics drain and its terminal weight capture still reach the shared monitor and weight history while the two fits overlap, and it still computes, then discards, a final evaluation. The check takes no lock, so a newer run that enters between a stale run's check and the writes the check guards still has those writes applied to it.
  - **Tests.** `src/tests/unit/api/test_lifecycle_paused_fit_return.py` (15 tests) drives the real manager, executor and FSM with a gated stub fit:
    - the wedge at the manager level, for a fit past its last checkpoint and for one with no checkpointed event;
    - the wedge over HTTP: pause, the fit returns, resume → 409, start → 200;
    - a pause forced into the settle just before `mark_completed`, after a pause the fit outlived and with none before it, and a resume whose own transition is held open across the settle's;
    - four controls: a resume before the fit returns, a stop after the pause, a stop while paused at a checkpoint, and a fit that raises while paused;
    - five stale-fit cases, each leaving a newer run and the terminal session counter untouched: a return, an interrupt, a return with the stop signal up, a failure, and a return while the newer run sits between its `START` and its fit.

    `src/tests/unit/api/test_lifecycle_state_machine.py` gains 18: `mark_completed` from `PAUSED`, its refusal from the six other states, a transition that another thread's cannot split, and, for each of the ten methods that take the machine's lock, a call from another thread that must wait while the lock is held. On unmodified `main` 23 of the 33 fail; the module's 4 controls and the 6 refusals pass. Against a settle that releases the pause through `RESUME`, keeps `mark_completed` `STARTED`-only and has no state-machine lock, 15 fail, among them the two forced-pause tests with the run `PAUSED`.
  - **Measured locally** on Python 3.14.7, against a clean `origin/main` worktree at `7640d42`:
    - **CI's unit job.** 5862 passed on `main` and 5895 with this change. The JUnit reports show no other test changing outcome. Both runs have one failure, `test_version_matches_pyproject`, which compares the environment's installed metadata (0.11.0) with `pyproject.toml` (0.13.0); CI's `pip install -e .` passes it.
    - **Coverage.** 96.58% → 96.61% (gate 80%), and none of the 154 lines this change adds to `manager.py` and `state_machine.py` is missed or the source of a partial branch.
    - **CI's quick-integration job.** 177 passed on both.
    - **Mutation check.** `util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py` catches 32 of 32 mutations, among them the whole fix reverted, a settle that releases the pause through `RESUME` first, the pause gate reopened early or not at all, each ownership check and each terminal count moved out of its guard, ownership claimed late, and the state machine's lock removed, altogether or from any one of the ten methods that take it.
    - **Races.** Under a client that re-sends pause until the run settles, with the service's logging, 0 of 200 runs wedged (a `RESUME`-first settle wedged 178 of 200), and 0 of 200 at a 1 µs switch interval. A pause or resume forced into the settle leaves the run `COMPLETED`.
    - **Determinism.** 500 runs of the new module passed every test: 250 at the default switch interval, and 250 pinned to one CPU with a 10 µs GIL switch interval, under a load average of 13 to 40. The 33 new tests, run 60 times each, passed all 1980 at the default switch interval and all 1980 at a 1 µs one.
    - **With the real model.** A real `CascorModel.fit` on a small growing network, paused from the manager's own event sink as it handled `training_end`, settled `COMPLETED`, and the next start ran.
  - **Reported here, fixed later in this release: the stop-then-start race.** A start sent after a stop, before the old fit reached its next checkpoint, cleared the shared `_stop_event`, so the old fit was never interrupted: it trained on to its natural end while the FSM read `STOPPED` and, still owning the lifecycle, wrote `training_state` `Completed` and counted a successful session for a run the operator had stopped. `swap_dataset_live` cleared the event the same way after its 10 s join timed out. The ownership check above could not help, because cascor's queue keeps the new run from starting until the old fit returns. This change shipped `util/ad-hoc/2026-11-08_stop_then_start_race_repro.py`, which reproduced it (exit 1). The owner's ruling 17 (2026-11-09), "cascor: stop-then-start", gave it a fix of its own: see "A start sent after a stop no longer cancels it" below, whose per-run stop signal the owner ruled on 2026-11-12 to keep, and with which the reproducer exits 0.
  - **Docs.**
    - `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`: the pause and resume sections describe the checkpoint, the paused completion, a pause or resume that races the settle, and the behaviour of earlier releases; their stale route line numbers are corrected. The start and stop sections name the FSM's states instead of a `Training` state it does not have, and the stop, pause and resume 409s name `error.message`, which carries their text.
    - `docs/api/API_SCHEMAS.md`: "Training Failure Propagation and Ownership" describes `_run_training`'s terminal settles, the ownership rule, the stop-then-start race, and the same `STOPPED` / `Completed` pair from a stop or reset that lands inside the settle. It used to describe the removed `monitored_fit` wrapper.
    - `docs/api/API_REFERENCE.md`: "Lifecycle Failure Handling Path" no longer describes `monitored_fit`; it points at `API_SCHEMAS.md`'s settle rules.
    - `docs/DEVELOPER_CHEATSHEET.md` 1.0.9: two troubleshooting rows.
  - **Where it was found.** juniper-ml's flood-4 record, `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`. Its §8 ruling 11 lists this defect (owner ruling of 2026-11-08, "Fix all four now"); §4 records the same wedge in juniper-service-core, whose lifecycle mirrors this one.
- **The Bandit SARIF upload's comment and its survey's docstring no longer claim that every upload succeeded.**
  - **The claims.** `ci.yml`'s upload comment said "165 of 165 uploads succeeded over 200 runs". `util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`'s docstring said a failed upload's step "conclusion still records `failure`".
  - **Why they fail.** GitHub's jobs API reports a step's `conclusion` after `continue-on-error`, so a masked failure reads `success`. juniper-canopy job 123689681187 logged `Path does not exist`, and its upload step reads `success`.
  - **The new wording.** The comment cites the survey's `Bandit` half, which can see a masked failure on a PR: 101 of 101 PR heads whose upload ran carry the check. It says the step count proves less. The docstring says the same, including that its RESULT line's "no upload step failed" is blind to a masked failure. No code changed.
  - **History.** The nightly-lanes entry below (juniper-cascor#735) qualifies its "165 of 165" accordingly.
  - **Where it was found.** juniper-ml's flood-3 record, `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, §4 and §6. Owner ruling of 2026-11-01.
- **A `/ws/training` client that resumes no longer misses broadcasts behind a `resume_ok`.** These are cascor's own
  copies of two defects that juniper-ml's shared `juniper-service-core` also had: juniper-ml#2534 fixed them on
  juniper-ml's `main` on 2026-11-09. juniper-service-core 0.7.2, the latest on PyPI on 2026-11-12, was published
  before that fix and still has both.
  - **Broadcasts made while no client was active were never numbered.** `WebSocketManager.broadcast` returned before
    assigning a seq when no socket was active (`src/api/websocket/manager.py:829-830` before this change). So a
    broadcast made while nobody was connected, or while the only client was still in its resume handshake, got no
    seq and no replay-buffer slot. A client resuming from its last seq was answered `resume_ok` with nothing
    replayed, over a gap it could not see. Every broadcast is now numbered, and buffered unless replay is disabled;
    with no client active the fan-out is simply empty.
  - **Broadcasts made during the replay were lost.** `_handle_resume` sent its replay snapshot
    (`src/api/websocket/training_stream.py:390-416` before this change), and the handler promoted the socket only
    afterwards (`:290`). A broadcast made while the replay was going out was numbered and buffered, but its fan-out
    reached only the sockets already active, so it reached the resuming socket by neither path: a client resuming
    from seq 2 received 3, 4, 5 and 7, never 6, and saw only that hole in `seq`. `_handle_resume` now promotes the
    socket itself, through `promote_to_active(websocket, replayed_through=<last replayed seq>)` (see Added), which
    sends what was broadcast meanwhile before the socket joins the broadcast set.
  - **A resume that cannot be kept gap-free is closed.** From `resume_ok` on, a send that fails or times out
    (`resume_ok`'s own included), or a replay buffer that evicts a message the client still needs before it can be
    sent, ends the resume: the socket is closed with `1011`, reason `Resume replay incomplete`, and never promoted.
    The client should reconnect and resume again, and is then replayed the rest, or answered `resume_failed`
    `out_of_range` and starts from a fresh snapshot. Such a resume used to carry on past the hole.
  - **A cursor that matches no seq this server sent is refused.** `json.loads` accepts `NaN` and `Infinity`, and
    Python counts a bool as an int, so a `last_seq` of `NaN`, `Infinity`, `2.5` or `true` was answered `resume_ok`,
    as was one above the last seq numbered; for `NaN`, `Infinity` and a cursor above the last seq nothing was
    replayed, yet the client was told its resume had succeeded. A `last_seq` that is not a plain integer is now
    answered `resume_failed` `malformed_resume`, and `WebSocketManager.replay_since` refuses a cursor above the last
    seq numbered with `ReplayOutOfRange`, which the resume answers `out_of_range`.
  - **Two more resume frames are answered by what they say.** A frame whose `data` is not an object (`null`, a
    list, a string, a number) got no resume reply at all: reading it raised inside the handshake, which went on as a
    fresh connect, with no `resume_failed` and no outcome counted. It is now answered `malformed_resume`. A negative
    `last_seq` was answered by the state of the buffer: `resume_ok` with nothing buffered, `out_of_range` once
    anything was, even with seq 1 still buffered, where a `last_seq` of `0` got a full replay. It is now read as `0`,
    the cursor of a client that holds nothing, in the handshake and in the catch-up alike.
  - **What a `resume_ok` now guarantees, and what it does not.** Every buffered seq after the client's `last_seq`
    is sent once, in seq order, before the socket joins the live fan-out; after that it receives broadcasts as any
    other active socket does. `replayed_count` still counts the replay snapshot only, not the catch-up. The catch-up
    has no bound of its own: while broadcasts keep pace with its sends it keeps sending, in order, and the socket
    stays pending, with no heartbeat or receive loop, until it catches up.
  - **Side effects.** With no client connected, each broadcast now pays the serialization check, the chunking size
    check and a replay-buffer slot. The buffer holds at most `ws_replay_buffer_size` messages (default 1,024), each
    about `ws_max_message_size_bytes` (default 60,000) or less, since a larger message is buffered as chunks; that
    is the bound it already had while any client was connected.
    An unserializable message is now refused, logged at ERROR and counted (the F-CASCOR-004 refusal) with no client
    connected too; the early return used to drop it silently. A broadcast send that fails still drops and closes
    that subscriber (F-CASCOR-004), unchanged.
  - **Measured locally** on Python 3.14.7, against `main` at `9f632ea`, with at most 4 xdist workers on a host shared
    with other test runs.
    - Of the 96 tests in the new `src/tests/unit/api/test_websocket_resume_continuity.py`, 87 fail against `main`'s
      sources, and all 96 pass with the fix.
    - Fourteen mutants, each breaking one guard, are all caught, each by a test written for it. Among them: activating
      the socket in a second lock section after the final check, a range check on the first catch-up pass only, no
      catch-up when nothing was replayed, a cursor check that lets `NaN` or a bool through, and a handler that promotes
      a resumed socket a second time.
    - A 20,000-seed sweep of random resume interleavings on in-memory sockets, with injected send failures, found no
      hole, duplicate or reordering. Against `main`'s code the same sweep finds a violation in 1,282 of 2,000 seeds.
    - The 96 tests ran 300 times each over 4 xdist workers: 28,800 passed, none failed. They set send and handshake
      timeouts far above any wait, except the two that test the send timeout, which block a send forever.
    - CI's unit selection passes 5,991 tests, 96 more than on `main`. Both runs share one failure, an
      environment-only version check (this host's editable install reports 0.11.0).
  - **Where it was found.** While juniper-service-core's copies were being fixed (juniper-ml#2534). juniper-ml's
    flood-4 record, `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, §8, ruling 11, records
    it, with the owner's ruling: "Fix all four now".
- **A start sent after a stop no longer cancels it: the stopped fit stops, and the new run waits for it (the stop-then-start race).**
  - **The defect.** A stop is cooperative. `stop_training` raised the one stop event every run shared and moved the FSM to `STOPPED` at once, but the fit sees the event only at its next interrupt checkpoint, or as it returns. `start_training` accepts a start from `STOPPED`, and it cleared that event, so a start sent in between cancelled the stop:
    - the old fit trained on to its natural end while the FSM read `STOPPED`, and the new run waited queued behind it on the single-worker executor;
    - the old fit, still owning the lifecycle, then wrote `training_state` `Completed` beside the `STOPPED` FSM (`mark_completed` was refused) and counted a successful session, for a run the operator had stopped.

    A fit paused at a checkpoint was released the same way (the start reopens the pause gate), a `reset` followed by a start raced the same way, and `swap_dataset_live` cleared the event after its 10 s join on the old fit timed out. A start that was then refused for its params (the route's `409`) had cancelled the stop too, with no new run behind it: the clear came before that check.
  - **Who reached it.** canopy's Restart (`POST /api/train/restart`) stops, waits until `training_active` is `false`, which reads the FSM and so is `false` at once, and then starts. That is this path, whenever the running fit is between checkpoints.
  - **How far back.** Every release tag with an interrupt checkpoint, `v0.5.0` to `v0.13.0`, clears the signal in both `start_training` and `swap_dataset_live` (it was named `_stop_requested` in 0.5.0). `v0.3.17` has no checkpoint, so a stop never interrupted a fit there at all; its start cleared the signal too (`_stop_requested`), which there changed only how the stopped run settled (`Completed`, not `Stopped`). Read per tag from each tag's own `manager.py`.
  - **The fix.** A start never clears a raised stop signal.
    - `_stop_event_for_new_run_locked` gives the run being accepted a fresh signal when the current one is raised, and otherwise lets it share the current one. `start_training` and `swap_dataset_live` submit each run with its signal, and `_run_training` watches that signal at both interrupt checkpoints and after the fit. `_handle_event` and `_check_for_interrupt` take it as an argument; a direct call still reads `self._stop_event`.
    - Every run accepted since the last stop shares the newest signal, so a stop, a reset, a live swap or `shutdown()` still reaches a running fit and every run queued behind it, and never a run accepted after it.
    - `stop_training` raises the signal before its FSM transition, as it already did. That order now matters: a start accepted once the FSM reads `STOPPED` always finds the signal raised.
    - A run's signal is chosen only as the run is submitted, after the last check that can refuse the start, and a stopped fit keeps its own: a refused start cancels nothing.
    - The routes answer as before: a start after a stop is still accepted (`200`).
  - **Designs not taken.**
    - Refusing the start while the stopped fit is alive changes the HTTP contract: canopy's Restart would answer `409` "Could not start the new run", which it does not retry. Making the start wait for the old fit blocks the request, and the event loop the route runs on, for up to a candidate round while it holds the manager's lock.
    - Fencing the old run's settle alone leaves the old fit training to its natural end on the single worker, so the stop is still not honoured and the new run still waits for it.
    - Moving the clear into `_run_training`'s entry loses a stop sent while the new run is queued.
    - A fresh signal for every start lets a stop miss a run queued behind another.
  - **The ownership check (#753).** In the `shutdown()` overlap #753's ownership tests build, a stale fit now keeps the stop signal `shutdown()` raised, so it takes the stop path instead of completing. #753's two stale-fit tests still pass, on that path: it is the post-fit stop's ownership check they now exercise, and their docstrings say so. The completion's ownership guard still holds a stale run that was already past its stop check, and a new test pins it there. #753's mutation check, `util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py`, now names the new module in its detector for that reason.
  - **Not changed.** A stopped fit still runs on until its next checkpoint while the FSM reads `STOPPED`, so whatever is admitted on the FSM is admitted while that fit is alive. Each of these was probed on `main` and with this change, and is the same on both:
    - a `start` binds its data and params (and, with `start_fresh`, replaces the model) under that fit before its run queues, and one refused after its FSM check has still bound the inline data it carried (and, refused for its params with `start_fresh`, has replaced the model);
    - the snapshot restore, retrain, resume and replay verbs load their model under that fit. Its settle then writes `training_state` `Stopped`, counts a cancelled session and ends the monitor session, and a fit that returns without meeting another checkpoint first drains the loaded model's history rows into the live metrics buffer;
    - a run that is already queued when one of those verbs lands still enters once the stopped fit has unwound. After a `restore` it trains the restored model while the FSM reads `INVESTIGATING`, where `stop` and `pause` are refused (`409`), and `reset` stops it at its next checkpoint;
    - a fit that reaches no further checkpoint and does not return keeps the single worker: later starts answer `200` and never begin, and `reset` does not free it;
    - a run stopped while it is queued still issues its `START`, and stops at its first checkpoint.
  - **Tests.** `src/tests/unit/api/test_lifecycle_stop_then_start.py` (13 tests) drives the real manager, executor, FSM and (for one) HTTP routes with a gated stub fit, using events and gates and no sleeps:
    - a start after a stop, at an `epoch_end` checkpoint, at a `phase_change` one and after a `reset`; a fit past its last checkpoint; a fit paused at a checkpoint that the start's reopened gate wakes; a start refused for its params;
    - a second stop reaching two runs queued behind the stopped fit; stop, start, stop, start, where only the last run trains; a start forced in between the stop's FSM transition and its return;
    - a live swap whose join timed out, and a swapped run stopped while queued;
    - a stale run in the `shutdown()` overlap, past its stop check, leaving a newer paused run alone;
    - canopy's Restart over HTTP: stop, `training_active` `false`, start `200`.

    On `main`, 11 of the 13 fail; the two that pass guard behaviour `main` already had (a stop reaching queued runs, and the completion's ownership guard).
  - **Measured locally** on Python 3.14.7, against a clean `main` worktree at `b9167bd`, with at most 4 workers on a host shared with other test runs.
    - `util/ad-hoc/2026-11-08_stop_then_start_race_repro.py`, which #753 shipped, exits 1 on `main` and 0 with this change.
    - CI's unit selection passes 6,004 tests, 13 more than on `main`. Both runs share one failure, an environment-only version check (this host's editable install reports 0.11.0). Coverage is 96.61% against the 80% gate, and no line this change adds to `manager.py` is missed or half-covered. CI's quick integration selection passes 177 tests on both.
    - Seventeen mutants of the fix, each undoing one part of it, are all caught by the new tests.
    - #753's mutation check, run with `--base 7640d42` (#753's parent), catches 32 of 32 with the new module in its detector. With the detector it shipped with, #753's two test files, it catches 28 of 32 on this change: the four that guard a completing stale run (the gate reopened before the ownership check, the completion ignoring ownership, the final score kept before the check, the terminal count outside the guard) survive those two files, because the stale fit in #753's overlap now takes the stop path, and the new stale-run test catches all four. On `main`, as shipped, it catches 32 of 32.
    - The 13 tests ran 40 times each at the default switch interval, and 40 times each with `sys.setswitchinterval(1e-6)`: 520 passed both times, none failed.
  - **Docs.**
    - `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`: the stop section describes the cooperative stop and a start sent while the stopped fit unwinds; the start section says such a start queues.
    - `docs/api/API_SCHEMAS.md`: "Training Failure Propagation and Ownership" describes the fix in place of the known defect it listed, and lists what a stopped fit that is still running leaves open.
    - `docs/DEVELOPER_CHEATSHEET.md`: two troubleshooting rows.
  - **Where it was found.** juniper-cascor#753 reported the race (the stop-then-start item of the paused-fit entry above) and shipped the reproducer. The owner's ruling 17 (2026-11-09), "cascor: stop-then-start", gives the race a fix of its own, in its own PR. That ruling named no design: the per-run stop signal is this change's, and the owner ruled on 2026-11-12 to keep it. As of this release, juniper-ml's flood-4 record (`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`) lists rulings 1 to 14 in its §8 and not this one.
- **The nightly performance smoke runs on pytest 9.2 again: its `pytest<9.2` cap is gone.** pytest-benchmark 5.3.1 (PyPI 2026-11-01) reads pytest's public `nodeid` instead of the private `_nodeid` that pytest 9.2.0 removed, and its changelog calls that pytest 9.2 support. So `scheduled-tests.yml`'s `performance-smoke` job no longer downgrades pytest after installing the project. It still prints the pytest and pytest-benchmark versions it got.
  - **Measured locally** on Python 3.14.7, in fresh venvs, with a one-test file that takes the `benchmark` fixture. Under pytest 9.2.0, pytest-benchmark 5.3.0 errors at setup with the `AttributeError` that run 40970853599 logged, and 5.3.1 passes, both timed and under `--benchmark-disable`.
  - **No floor.** `pyproject.toml` keeps `pytest-benchmark>=4.0.0`, so a fresh install resolves 5.3.1. If the lane ever pairs pytest 9.2 with 5.3.0 again, every benchmark test errors at setup and the lane fails; it cannot pass quietly.
  - **Where it came from.** The cap is juniper-cascor#735's (its entry is below), which said to drop it once a pytest-benchmark release supported pytest 9.2. juniper-ml's flood-3 handoffs carried that as a watch item.
- **Five documents no longer name the nonexistent `src/tests/pytest.ini`.** pytest's configuration is `[tool.pytest.ini_options]` in the repo-root `pyproject.toml` (`AGENTS.md` said so from juniper-cascor#735).
  - The directory trees in `docs/REFERENCE.md`, `docs/testing/MANUAL.md` and `src/tests/README.md` drop the file. `src/tests/README.md`'s configuration section now describes `pyproject.toml`, and `docs/DOCUMENTATION_OVERVIEW.md` names it.
  - `docs/ci_cd/MANUAL.md`'s marker list was a copy of the old file's: it now names all 18 markers in `pyproject.toml`, adding `long`, `requires_juniper_data`, `critical`, `golden` and `conformance`.
  - `src/tests/README.md` said every slow test had its own 300-second timeout. The default is 60 seconds, and the per-test `@pytest.mark.timeout(...)` values run from 10 to 300.
  - **Where it was found.** juniper-cascor#735's body, from the 2026-10-08 flood-3 disposition (juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4).
- **The memory-budget gate's own 40 tests now run in the required unit legs; they had never run in CI.**
  - **Where #585 put them.** juniper-cascor#585 (2026-08-25) ported `util/memory_budget_check.py` and its suite from juniper-ml. The suite went to `src/tests/test_memory_budget_check.py` with no marker, where no CI lane selects it:
    - the unit job collects only `src/tests/unit`, under `-m "unit and not slow"` (`ci.yml`);
    - nothing in `src/tests/conftest.py` adds `unit` by directory;
    - the one nightly lane that walks all of `src/tests` selects only `long`.
  - **What never ran.** So the negative controls that keep the `Memory Budget` check honest had never run against this repo's copy of the checker. Each of these raises `BudgetError` (exit 2): a missing governed file, and a missing, unreadable or empty budget. So does a non-positive ceiling. A waiver leaves the ceiling where it was, and a ceiling may only move down.
  - **The move.** The suite moves to `src/tests/unit/test_memory_budget_check.py` with `pytestmark = pytest.mark.unit`, and its repo root goes from `parents[2]` to `parents[3]`. No test body changed.
  - **The docstring.** The checker's docstring now names the suite's real path; it named juniper-ml's `tests/`.
  - **The effect.** At this change the unit lane selected 5,836 of 5,851 collected tests, up from 5,796 of 5,811. The 40 added are this suite, and all 40 pass locally on Python 3.12, 3.13 and 3.14. No workflow changed.
  - **Left alone here, and given a lane later in this release** (the nightly-lanes entry below). The same census found two other sets that no lane ran:
    - the 153 `performance`-marked tests in `src/tests/performance/`, which the new nightly `performance-smoke` job runs;
    - five unmarked tests in `src/tests/integration/test_comprehensive_serialization.py`, now marked `integration` and run in the required integration jobs.
  - **Where it was found.** Found on 2026-10-26 in the 2026-10-08 flood-3 disposition (juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4).
- **The nightly long and slow-integration lanes run their tests, `src/tests/performance/` gets an untimed nightly smoke and loses an exit hang, five integration tests that no lane selected now run in the required integration jobs, and a failed Bandit SARIF upload fails a PR.**
  - **The long lane ran nothing.** `scheduled-tests.yml`'s `long-running-tests` passed only `--run-long`, so job 121983548401 logged `1 skipped, 6214 deselected` and passed. `src/tests/conftest.py` gives the lane's one pick, `test_deterministic_training_resume`, two more skips:
    - it is also marked `slow`;
    - the conftest tests `"integration" in item.keywords`, and the keywords hold the `src/tests/integration` directory's name, so every test there needs `--integration`, marked or not.
  - **The long lane's fix.** The job now also passes `--slow --integration`. Locally the test runs and XFAILs (`1 xfailed, 6236 deselected`); its `xfail` stays.
  - **The slow-integration lane ran nothing as well (owner ruling 2026-10-29, "Fix in #735").** `slow-integration-tests` passed `--slow` without `--integration`. main's nightly run 40809669816 (job 123236747466) logged `20 skipped, 178 deselected` and passed. The job now also passes `--integration`. Locally it runs 15 tests, all passing, and skips the 5 golden picks: they need `--golden`, and `golden-regression.yml` runs them.
  - **A lane that executes nothing now fails.** New `util/check_junit_executed.py` reads a lane's `--junitxml` report and fails when no test executed, or when one failed or errored.
    - An XFAIL counts as executed, although pytest writes it as `<skipped type="pytest.xfail">`.
    - It also catches a failure the exit status hid: `src/tests/conftest.py`'s `pytest_unconfigure` called `os._exit(0)` whenever a non-daemon thread outlived the session, so a failing lane could exit 0 (measured: `1 failed`, exit status 0). "A failing test session no longer exits 0 when a thread outlives it" below removes that mask in this release.
    - It runs after the slow-integration and long lanes and after the new performance smoke. Its 24 tests (`src/tests/unit/test_check_junit_executed.py`) include two real pytest runs and pin the `scheduled-tests.yml` wiring. At this change the unit lane selected 5,860 of 5,875 tests, up from 5,836 of 5,851.
  - **The performance smoke (owner ruling 2026-10-29, "Nightly smoke, no timing").** The new `performance-smoke` job runs all 153 tests in `src/tests/performance/` with `--run-performance --benchmark-disable`. A failure fails the nightly through the `summary` job; `performance-benchmarks` stays informational. The pytest step's `timeout-minutes: 30` turns a hang into a failure instead of a 6-hour run. Locally all 153 pass in about 23 s.
  - **The job capped pytest below 9.2 (owner ruling 2026-10-29); the cap is gone in this release** (the pytest 9.2 entry above). pytest 9.2.0 (PyPI 2026-10-27) broke pytest-benchmark 5.3.0, then the latest release, at fixture setup: `AttributeError: 'Function' object has no attribute '_nodeid'` (`pytest_benchmark/fixture.py:88`). Every benchmark test errored, and run 40970853599 logged `5 errors` and stopped at `--maxfail=5`. The job therefore installed `pytest<9.2` (9.1.1) after the project until pytest-benchmark 5.3.1 supported 9.2. The required lanes kept pytest 9.2. Locally, on 9.1.1 with pytest-benchmark 5.3.0, all 153 passed.
  - **The exit hang, fixed.** `TestQueueThroughput::test_burst_throughput` drained its queue with `get_nowait()` until `Empty`, which can stop while the queue's feeder thread is still flushing. The leftovers fill the pipe, the feeder blocks, and the interpreter's exit-time join never returns. Run alone, the test hung in 6 of 6 runs, and the full smoke in 1 of 2. It now drains exactly the 320 items its five bursts put. Afterwards 12 of 12 runs alone and 6 of 6 full-smoke runs exited cleanly. The measured drain is unchanged.
  - **Not fixed here.** `--benchmark-disable` reaches only the pytest-benchmark fixture. Eight assertions time their own code against a ceiling or against each other: `test_baselines.py:464` and `:467`, `test_concurrency_scaling.py:551` and `:582`, `test_endtoend_profiling.py:251`, and `test_shared_memory.py:523`, `:525` and `:576`.
  - **Five unmarked integration tests.** `TestHiddenUnitsPreservation`, `TestConfigRoundtrip`, `TestActivationFunctionRestoration`, `TestTorchRandomStateRestoration` and `TestHistoryPreservation` in `src/tests/integration/test_comprehensive_serialization.py` get the class-level `@pytest.mark.integration` the other modules use. The required integration jobs now select 177 of 198 tests, up from 172 of 198, and all 177 pass locally.
  - **The Bandit SARIF upload (owner ruling 2026-10-29).** `ci.yml`'s upload step is now `continue-on-error: ${{ github.event_name != 'pull_request' }}`. On a PR a failed upload fails Security Scans, with the cause in the step log, instead of leaving the required `Bandit` context unposted. Pushes and dispatches still tolerate it. The survey (`util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`) counted 165 of 165 upload steps succeeding over 200 runs; a step masked by `continue-on-error` reads `success` there, so the count does not show that every upload succeeded (the Bandit SARIF comment entry above). `AGENTS.md`, `docs/ci_cd/MANUAL.md`, `docs/ci_cd/REFERENCE.md` and `docs/ci_cd/BRANCH_PROTECTION.md` called the upload best-effort everywhere, and now say so for pushes and dispatches only.
  - **`AGENTS.md`** listed a `src/tests/pytest.ini`, which does not exist: pytest's configuration is `[tool.pytest.ini_options]` in the repo-root `pyproject.toml`. Five other live documents named the file too (`docs/REFERENCE.md`, `docs/testing/MANUAL.md`, `docs/ci_cd/MANUAL.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `src/tests/README.md`); "Five documents no longer name the nonexistent `src/tests/pytest.ini`" above corrects them in this release.
  - **Where it was found.** The 2026-10-08 flood-3 disposition (juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4), in rows found on 2026-10-27.
- **A failing test session no longer exits 0 when a thread outlives it.**
  - **The defect.** `src/tests/conftest.py`'s `pytest_unconfigure` ends the process with `os._exit` whenever a non-daemon thread is still alive, so that the thread cannot hang the job. It called `os._exit(0)`, which replaced pytest's exit status. A session with a failing test and a surviving thread exited 0, and the lane passed. juniper-cascor#735's probe measured it on 2026-10-29: `1 failed`, exit status 0.
  - **The fix.** A `trylast` `pytest_sessionfinish` hook records `session.exitstatus` in `config.stash`, and the forced exit passes it on. A session that never reached `pytest_sessionfinish` recorded no status, so it exits with pytest's internal-error code (3) rather than 0. The output flush and the child reaping are unchanged.
  - **The test.** `src/tests/unit/test_conftest_exit_status.py` runs a real pytest in a subprocess, over a one-test tree whose conftest loads only this conftest's two exit hooks. A failing session with a surviving non-daemon thread must exit 1, and a passing one 0. A failing one without a survivor must exit 1, as a control. Against the old conftest the first case fails (`1 failed`, exit status 0) and the other two pass.
  - **What it removes.** It removes the mask that juniper-cascor#735's `util/check_junit_executed.py` worked around, by failing a lane whose report shows a failure even when the exit status reads 0. That script's docstring now records the mask as history (0.1.1). Failing an empty lane stays its main job. Two `src/tests/conftest.py` comments that called the forced exit `os._exit(0)` now say `os._exit`.
  - **Why it found nothing broken.** `main`'s latest `ci.yml` run before this change (40768508350, `e8e8bf4d`) recorded 0 failures and 0 errors in all five JUnit reports, so no required lane depended on the mask.
  - **Owner ruling** of 2026-10-29: "Fix now, own PR".

### Security

- **The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #748 moved both locks from 0.4.1 and 0.7.1 to them, and nothing else (the release's other lock moves are under Changed): `requirements.lock` holds 73 pins and `requirements-cpu.lock` 54, and each reproduces under its constraint-mode freshness resolution. The image installs
  `requirements-cpu.lock` (`Dockerfile:42`).
  - **observability 0.4.2** fixes `configure_sentry`, which `src/api/app.py:335` calls through
    `src/api/observability.py`'s wrapper. Under 0.4.1, once `JUNIPER_CASCOR_SENTRY_DSN` was set, a request's
    `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` headers reached Sentry in every error event and
    transaction, and the wrapper samples every transaction (`_LOGGER_SENTRY_TRACES_SAMPLE_RATE` is 1.0). 0.4.2 runs its
    scrubbing hook on transactions too (`before_send_transaction`), redacts the parsed cookies, and filters those three
    headers and `Proxy-Authorization`. The wrapper leaves `send_pii` off, so the `X-API-Key` and cookie leaks that 0.4.2
    also closes were not reachable here.
  - **service-core 0.7.2** rounds `FailedAuthThrottle`'s `Retry-After` up instead of truncating it. juniper-cascor
    imports only `enforce_auth_posture` from service-core, so the change does not reach its own throttle in
    `src/api/security.py`, and the pin is consistency with the sibling services.
  - Regenerated with `--upgrade-package` for the two packages only, compiled onto a copy of each lock so every other pin
    is held: `requirements.lock` first, then `requirements-cpu.lock` by its header's command, with that header kept
    (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The wheel's floors follow in this release:
    `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2,<0.8.0`, so a pip install over an older environment
    upgrades both. The locks moved in #748; the floors ride in the release proposal, because a `pyproject.toml` change on
    any branch but `release/` triggers `lockfile-update.yml`'s full `--upgrade` regen.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-cascor/blob/v0.14.0/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md`
