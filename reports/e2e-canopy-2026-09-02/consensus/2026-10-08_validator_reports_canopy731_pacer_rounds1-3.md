# Validator reports — canopy#731 (request/ack pacer for F-CANOPY-055, -058, -068), rounds 1–3, 2026-10-08

Independent adversarial review, under the SOP that every generated artifact gets multiple independent lanes.
Each lane was a fresh `general-purpose` agent with its own brief and lens, and no lane saw another's verdict. Each
report below is the lane's final message, **condensed in transcription** to its verdict, findings, mutation
outcomes and refutation list: severities and conclusions are kept, and some citations and scenarios are dropped.
The full texts are in this session's transcript (session `d75a921d`, 2026-10-08). The orchestrator's disposition
of each round follows its reports.

- Round 1 reviewed `7aed1f2b` (commit 1). Lane B also read the unpushed worktree as it then stood.
- Round 2 reviewed `b344ff97` (commit 2).
- Round 3 reviewed `957176de` (commit 3), scoped to its diff.

The review ended on round 3, which changed no behaviour-relevant conclusion.

---

## Round 1

### Lane A: renderer mechanics

> I did not refute the core mechanism: the pacer never re-requests either feeder while a request is in flight. Two of the PR's absolute claims are false in letter, but neither failure stalls a lane or cascades. The one regression is slower recovery after a canopy-side (Dash-level) failure. I found no BLOCKER and no MAJOR.
>
> The three key renderer sites match between dash 4.2.0 (`JuniperCanopy1`) and 4.4.1 (wheel unpacked in scratch): `getUniqueIdentifier`, `getReadyCallbacks` reading only `getInputs` and the stale-result check. Line numbers below are 4.2.0.
>
> 1. **MINOR: "Nothing re-requests a feeder while its request is in flight" is false. A model-class switch evicts one response, then heals.** The renderer re-runs, as an initial call, any callback that writes into a newly rendered piece of layout and does not set `prevent_initial_call` (`dash_renderer.dev.js:6965-6977`, `handleOneId`). `update_metrics_store` sets `prevent_initial_call=False`; its output lives inside the metrics panel, inside `visualization-tabs`, whose children `suppress_cascade_tabs` rebuilds on every live/one_shot change. A second variant: the layout's initial call is in flight, and the next tick's pacer sees "acked" and writes N+1, which evicts that initial call. The impact is bounded: one lost response, no stall, no chain.
> 2. **MINOR (regression): recovery after a canopy-side failure goes from about 1 s to about 30-31 s.** On a non-OK HTTP reply, `handleServerside` calls `completeJob()` and rejects (`:978-984`), and no ack lands. The `try/except` in each feeder covers only the handler. These still give a 500 outside it: Dash output serialisation, a middleware 401/403, `ws_liveness.get(...)` before the `try`, and a non-iterable status-bar result. On `main` the status bar rode the 1 s tick and retried at the next one, and the metrics guard re-enabled in `completeJob()`. Network-level failures are unchanged for the metrics store (watchdog ~30-35 s vs pacer ~30-31 s). The status bar now waits 30 s too.
> 3. **NIT: a display-mode change can be absorbed as a "tick", so the full-history fetch waits up to 4 cycles.** This happens when the seq-0 request has no `extra_key`, or when a stale re-issue folds the new mode into `stale`.
> 4. **NIT: the stale timer uses the wall clock.**
>
> Tried and could not refute: a pacer writing while the feeder is in flight, through merging or queueing; renderer blocking that strands the feeder (State is never checked by `getReadyCallbacks`); the mount race; request/ack stores inside a rebuilt container (they are top-level); other writers of the lanes' `disabled` (the gate is now the only one); PreventUpdate / 204 (every return carries an ack); a late ack of an evicted request (discarded by the `watched` check); a stale re-issue evicting a slow request (only past 30 s).
>
> *(Abridged in transcription to the findings and the refutation list. The full report, with its file:line citations, is in this session's transcript.)*

### Lane B: regressions and test vacuity

> **Verdict: REFUTED as pushed.** The pushed head `7aed1f2b` has one MAJOR undisclosed regression. The worktree also holds an unstaged round-2 revision in progress, and that revision adds a second MAJOR.
>
> - **MAJOR-1:** any failure outside the Python handler (a non-200 reply, an exception before the `try`, a network failure) stalls both lanes for 30 s, and the PR doesn't say so.
> - **MAJOR-2 (unstaged worktree revision only):** the adaptive stale bound can be inflated permanently by one throttled tick. `maxRtt` was measured at the pacer run that saw the ack, never decays, and a ~60 s throttled tick made the bound ~180 s (probe `scratchpad/laneB/probe_maxrtt.py`).
> - **MINOR-1 (pushed head):** a display-mode change that rides a stale re-issue is lost.
> - **MINOR-2:** the full-history modulus now counts requests, not ticks (disclosed in the constants comment, not in the CHANGELOG).
> - **MINOR-3:** the paced-feeder census depends on naming (`-request.data`).
> - **NIT:** `metrics_panel.py:1226` still says "a `running=`-gated poll".
> - **Test vacuity:** the 10-idle-minute node simulation assumes its conclusion: ack and "not in flight" coincide by construction, and round trips are clipped below the stale bound. `test_the_simulation_can_fail` is a weak non-vacuity check.
> - **Mutations:** 16 run (M1–M16, with M7 in two variants); every one was killed except M2 (never stale), which survived the simulation though not the unit cases.
>
> *(Abridged in transcription; the mutation table and scenarios are in this session's transcript.)*

### Lane C: claims re-probed

> No numbers wrong in a way that changes conclusions. Four material problems:
>
> - "Rule fixed before the first run" omits that the first scoring failed and the scorer changed.
> - The branch's own live run shows requests in flight up to 16.4 s, while the stale constant's comment cites 5.4 s.
> - Two mechanisms are stated as observed on canopy when they were inferred or synthetic: the display-mode eviction, and the watchdog's phase-locking.
> - "Nothing re-requests a feeder while in flight" is absolute, but the 30 s stale path re-requests by design.
>
> Also: the F-055 "round trip ~1.2 s" is wire latency p50 1.16 s (0.21–3.08 s); the leg SHAs cannot tell the fix from main; the load range is one post-run reading; and the README's strand footnote and cycle wording need correcting.
>
> *(Abridged in transcription; the 26-row claim table is in this session's transcript.)*

### Round 1 disposition

Commit 2 (`b344ff97`) addressed every finding. Its message lists the changes:

- the adaptive stale bound with a lower-bound measurement (answering MAJOR-2 before it shipped) and a 120 s cap;
- `extra` precedence;
- the liveness read moved inside the `try`, and a check on the status-bar result's shape;
- the cost disclosed in code, the CHANGELOG and the PR;
- corrected claims;
- the `_PACED_POLLS` registry with a structural completeness test;
- a simulation with delayed acks and a stranded request;
- the UI collector fixed for the multi-output key, which CI caught.

---

## Round 2

### Lane R2-A: mechanics and code

> No BLOCKER or MAJOR. The round-1 answers hold under code reading and mutation.
>
> - **MINOR 1:** a forward step of the wall clock causes a false stale re-issue (+50 s step) or a permanently inflated bound (+20 s step gives a 61.5 s bound). Fix: `performance.now()`.
> - **MINOR 2:** window state is keyed by lane, not by request store, and nothing tests that the lanes stay separate. Mutation M18 (one shared key) survived every suite.
> - **NIT 3:** the request's `stale` flag is dead data on the server.
> - **NIT 4:** the status bar's shape check counts outputs rather than validating them.
> - **NIT 5:** the registry test misses a paced feeder that has a second Input.
>
> Mutations: 20 run. 17 were killed. M7 survived but is equivalent to the code, M12 survived but is benign, and M18 survived (MINOR 2). Tried and could not refute: the lower-bound measurement under throttling, an Apply-clamp gap, queue delay and suspend; a request store resetting; the initial call after a tab rebuild; ack ordering; `extra` precedence; acks on every return path; and that the simulation is not vacuous.

### Lane R2-B: claims re-probed

> Most numbers are right; two claims are wrong and several overstated.
>
> - **T-apply was never a mid-request test.** The clamp was released ~58–60 s after it was set, which fits E-3. The PR's explanation of its NO-EFFECT was wrong.
> - **"always" is false for a lost `extra` request**: its stale re-issue reads `stale`.
> - **Provenance:** the renderer run, the F-055 census, run 1 and most of run 2 predate commit 1. They ran an unhashed uncommitted tree, and "the commit-2 code is in the page" belongs to the later leg.
> - **The commit-2 F-055 census read VOID** (9 responses in 60 s).
>
> Also: the load figures are post-run readings; the cadence should be given for both runs; several docstrings still cite `POLL_PACER_STALE_MS`; `test_poll_gating.py` states the phase-locking as fact; the attribution "round 1 measured ~180 s" is inconsistent; and Phase 11's load range is 1.9–4.6.

### Round 2 disposition

Commit 3 (`957176de`) made these changes:

- `performance.now()`;
- state keyed by request-store id, with a node test that drives both pacers on one `window`;
- a lost `extra` request re-issued as `extra`;
- every text correction.

The PR body was rewritten: T-apply described accurately, each run's provenance stated, both runs' cadence and the load readings given as post-run, and the VOID reported.

Three mutations each failed their new test (`util/ad-hoc/2026-10-08_pacer_round2_mutation_check.py`). The registry-test gap (NIT 5) and the shape check (NIT 4) were left as recorded.

---

## Round 3

### Lane R3: commit-3 diff, mechanics and claims

> **Verdict: no BLOCKER or MAJOR.** The three code changes in commit 3 work as claimed, and nothing here changes a behaviour-relevant conclusion.
>
> - **MINOR 1:** no test guarded against `extra` sticking forever. Mutation M1, which drops the `!acked &&` guard, survived, and it would make every request bypass the full-history modulus.
> - **MINOR 2:** "post-run load averages 13.8-32.7": the 13.8 has no archived source.
> - **MINOR 3 (juniper-ml instrument):** the renderer check treats any `extra` request as proof of an ack, which commit 3's carry-over makes false for a lost `extra`.
> - **NIT 4:** the docstring's "the server reads `reason` only" is inaccurate, the stale bound is described per lane though it is per poll, and the CHANGELOG lacks the raising-handler caveat.
> - **NIT 5:** the node harness runs the `Date.now()` fallback almost everywhere.
>
> Tried and could not refute: a null `req` (it short-circuits); `extra` re-issues are bounded; nothing reads `issued_at` as epoch milliseconds (the stores are memory-only); no caller passes a lane id.

### Round 3 disposition: the review ends

Commit 4 (`2689a207`) made these changes:

- `test_an_acknowledged_mode_fetch_returns_to_ticks`, which kills the sticky-`extra` mutation;
- the wording fixes.

The instrument now logs each request's `stale` flag and derives acks and stale re-issues from it; re-scoring the earlier runs is byte-identical.

The 13.8 reading is recorded in `../pacer-live/README.md`, from this session's `uptime` output after run 2.

Round 3 changed no behaviour-relevant conclusion, so the review ends here. Commit 5 (`65ead946`) answers a CodeQL "unused global" thread on `_PACED_POLLS` by wiring the pacers' lanes from it. Its callback graph is identical to the final leg's capture. `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` did not predict that alert, which is a gap in the prescreen.

## What the review cannot support

- That a non-OK reply or network failure on a real page recovers as the stale bound says. Only the scratch app strands a request.
- Any renderer but dash 4.2.0 (the 4.4.1 sites were compared by Lane A, not run), or any browser but headless Chromium.
- Live training (WS-primary) or the full-history views on a leg.
