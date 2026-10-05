<!-- markdownlint-disable -->

# Phase 10 ledger validation, round 3 (frozen 0d3c337b)

Two lanes on round 2's corrections to the canopy E2E ledger's Phase 10, frozen as 0d3c337b, from one brief (reports/e2e-canopy-2026-09-02/drafts/lane10R3_phase10_ledger_brief.md): 10-R3A re-derived every claim the round-2 pass introduced, artifact-first; 10-R3B attacked what that pass broke. Each report is the lane's final message, verbatim. (The archiver labels each agent's only report 'round 1' because neither agent was resumed; both are round-3 lanes.)

## Lane 10-R3A - round 3, artifact-first

*agent `acbfa54f3ee566bcc` · round 1 · last-assistant-text (not resumed) · 13665 chars*

**VERDICT: SOUND-WITH-FIXES.** The pass replays exactly, the counts reproduce, and nearly every cited line, time and quote checks out. One finding changes an action (Finding 1), so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this round does not end the review.

Abbreviations:
- **L** = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `0d3c337b`.
- **M** = `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`.
- **R2** = `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round2.md`.
- Canopy is read at `1b2dd438`, cascor at `95cdc562` and juniper-data at `29be6d35`.

**TABLE (R3A)**

| # | Claim | Re-derived value | Result | Evidence |
|---|---|---|---|---|
| 1 | The round-2 script on `2134ca2a` gives `0d3c337b`, except the hand-written parts | 22 substitutions and 6 spans. Only two hunks differ: the Instruments sentence (L:10212) and the round-2 block plus `ROUND3_PENDING` | MATCH | Imported `apply()` from the script and ran it on a scratch copy, then diffed |
| 2 | Triage counts | 78 / 53 / 1 / 2 / 22. 6 open P1: F-CANOPY-055, -058, -064, -065, F-CASCOR-001, -002. 16 open P2, no P0. F-CANOPY-057 parses as P2 OPEN | MATCH | `e2e_finding_triage.py --note` on a copy of L |
| 3 | canopy#684: branch, merge time, merge oid, both files | `fix/idle-cuts-round3-wording`, MERGED 2026-09-24T11:10:28Z, `f2147403…`. Its files include `docs/USER_MANUAL.md` and `notes/development/REPLAY_V2_FAQ.md` | MATCH | `gh pr view 684 --jq`, without author fields |
| 4 | `f2147403` is an ancestor of `1b2dd438` | `merge-base --is-ancestor` exits 0 | MATCH | |
| 5 | `USER_MANUAL.md:764-766` says "Today no weight sample reaches the page" | The text is at :765-766. It is absent at `f2147403^1` | MATCH | `git show` |
| 6 | The FAQ opens with a status note that no replay weight reaches the page | The status note's second bullet, at :24. Absent before #684 | MATCH | `git show` |
| 7 | Item 13's follow-up is canopy#684 | Phase 9's item 13 (L:9718-9721) names the same branch | MATCH | read |
| 8 | `model_registry.py:267-277` holds the 5-symbol seed; `:234-238` says the array travels only as a seed | Both read as cited | MATCH | `git show` |
| 9 | From the page, a refusal needs `max_symbols` or a ceiling below 5 | Cap = `min(max_symbols or ceiling, ceiling)` (`generator.py:508-510`). `max_symbols` renders as a number field (`dataset_schema.py:283-301`, `:332-336`) and is not in `FORM_EXCLUDED_FIELDS` (`:149`) | MATCH | read |
| 10 | N is the effective cap, 14 at default; the 503-symbol case needs the API or a YAML | `limits.py:135` = 14. Experiment YAMLs pass `dataset.params` through freely (`util/experiments/suites/p4/e-h-real-data.yaml:13`) | MATCH | read |
| 11 | F-CANOPY-063: a claim-text grep "finds only the first" | 11 lines, including `test_start_fresh_refusal_and_modal_text.py:41`. None of the other three fixtures appears (`test_dataset_shortfall_prompt.py:37`, `test_n6…:51`, `test_n5…:309`) | MATCH | `git grep` at `1b2dd438` |
| 12 | F-CANOPY-064: one Accuracy point in the A-N2 capture; tiles read 96.30% and 98.75% | The A-N2 cluster has 4 exact `#28a745` pixels at y=1158 plus blends. The tile text reads 96.30% | MATCH | Pillow |
| 13 | Phase 1's cluster "is the Recall and ROC-AUC series, not Accuracy"; header "Phase 1's only scalar-series markers" | An Accuracy marker sits under the cluster, mostly covered | MISMATCH | Finding 2 |
| 14 | Pixel counts 0 / 11 / 8, attributed to Lane 10-R2B | Exact colour match gives 0/7/7, which is R2B's own count. A nearest-colour tolerance of 20 gives 0/11/8 | MATCH as numbers; attribution wrong | Finding 2 |
| 15 | `manager.py:2931`: a plain Start retains the history | `_retain_metrics_next_run = not resuming and not start_fresh` | MATCH | read |
| 16 | The burst can add zero-valued points | Monitor rows are flat, with top-level `phase` (`monitor.py:300-312`), so `:2260`/`:2264` plot accuracy 0 for `output` rows | MATCH | read |
| 17 | `metrics_panel.py:2032-2072`: the scalar series are not phase-filtered | No filter there, and the caller passes unfiltered rows (`:2289-2290`) | MATCH | read |
| 18 | `test_n5_apply_params_ux.py:309` | The flat fake is at :309 (:308 is `fake_future = MagicMock()`) | MATCH | read |
| 19 | Unwrapping recovers the three WS keys, the fourth's skip, and the REST key | Re-ran the archived `2026-10-04_phase10_r1_a2_my_o3.py` at the pins. applied = `[nn_max_iterations, nn_output_epochs, nn_max_hidden_units, cn_training_iterations]`, skipped `nn_max_total_epochs` (not-updatable). The whole-frame arm gives `['cn_training_iterations']` | MATCH | executed in JuniperCanopy1 |
| 20 | No manual or REFERENCE text makes the apply-toast promise | No toast, applied, skipped, declined or not-updatable promise in `USER_MANUAL.md` or `REFERENCE.md` | MATCH | `git grep` |
| 21 | The burst comes about 5 s after a (re)connect (`training_stream.py:60-79`) | The default wait is 5.0 s (`:281`, `settings.py:51`). The burst follows only on a non-resume (`:299-300`), and an empty burst is still sent (`:111-123`) | MATCH | read |
| 22 | `main.py:4100-4101`; `service_backend.py:460` | `create_backend` and `await new_backend.initialize()`; `start_metrics_relay()` | MATCH | read |
| 23 | W8 step 13 is the switch back to CasCor | M:1149: "Switch back to `cascor` via the modal" | MATCH | read |
| 24 | A-N2 log :34-37 times | Startup complete at L34 (`,725`); relay connected at L35 (`,768`, +43 ms); first initial-state frame (`initial_status`) at L37 (`35,770`). The burst itself is counted in L39's summary (`initial_metrics=1`), and cascor sends the frames back to back | MATCH | read |
| 25 | The relay reconnects after a socket loss; F-CANOPY-049 and F-CASCOR-004 describe drops it does not reconnect from | Reconnect loop at `cascor_service_adapter.py:657-661` and `:872-914`. Both entry headers describe silent drops with the socket left open | MATCH | read |
| 26 | `ws_dash_bridge.js:273` stamps the liveness clock | `drain._lastMetricsFrameMs = Date.now()` inside the `initial_metrics` handler | MATCH | read |
| 27 | `dashboard_manager.py:7877`, `:7941`: the REST poll replaces the store after 5 s of quiet | `:7877` skips the poll while the stream is live. The store is replaced at `:7944` unless the fetch is identical (`:7941`) or empty (`:7910`). The liveness window is 5000 ms (`canopy_constants.py:507`). Holds for an idle stream only | MATCH as cited; see Finding 1 | read |
| 28 | Tiles take the next relayed frame | The tiles read the newest row (`metrics_panel.py:1671-1672`) | MATCH | read |
| 29 | M-METRICS-32: PASS @ `04f06ff` covers the append callback; `extendTraces` was never driven and fails by source | M:449 claims both. The re-validation record (L:163, L:5776-5782) covers the append callback only. The path reads flat `e.loss` (`:1032-1037`). L has no mention of `extendTraces` before Phase 10 | MATCH | read |
| 30 | Brief paths; R2A replayed round 1 exactly | Both briefs are tracked at `0d3c337b`. My own round-1 replay gives 35 substitutions, 8 spans and two hunks | MATCH | `ls-tree`; replay |
| 31 | "the planned live check could not have failed (both lanes)" | Lane 10-R2A said the opposite | MISMATCH | Finding 3 |

**FINDINGS**

1. **MAJOR: F-CANOPY-067's new rating basis covers only an idle cascor and the tiles, and the drive meant to decide it cannot see the mid-run case.**
   - **Ledger text:** L:10170-10173 says "Severity: P2, because the zeros are transient by source … after 5 s of quiet the REST poll replaces the store (`dashboard_manager.py:7877`, `:7941`), and during a run the next relayed frame replaces the tiles. A live drive of W8 step 13 decides it". Item 18 (L:10337-10338) says the W8 drive "also settles F-CANOPY-067's rating".
   - **Evidence, the store mid-run:**
     - `:7877` skips the REST poll while the stream is live.
     - During a run, the append handler keeps the burst's flat rows (`:7833-7834`). They stay until the `metrics` frames pause for 5 s, or until `window_size` newer rows displace them (default 500, `canopy_constants.py:511`).
     - The charts read those rows as 0 (`metrics_panel.py:1952`, `:2260`).
   - **Evidence, the triggers:** two of the entry's three triggers can land mid-run: a canopy restart with a reconnecting tab, and a socket loss while cascor stays up (the relay reconnects, `:872-914`).
   - **Evidence, the drive:** W8 step 13 always lands on an idle cascor. Canopy refuses to switch away from CasCor while it trains (`main.py:4092-4097`), and from the LMU model canopy cannot start cascor. The entry itself says "How long the rows stay was not measured."
   - **Fix:** "P2 while the zeros are transient. By source they are when the burst lands on an idle cascor, and on the tiles mid-run. Mid-run, the charts keep the rows until a 5 s gap in `metrics` frames or window-size newer rows; not measured." Add a mid-run burst to item 18 alongside W8 step 13 (for example, restart canopy mid-run with the tab reconnecting inside 5 s), and to both fix directions.
   - **Changes a number, disposition or action?** Yes, an action.

2. **MINOR: Phase 1's cluster does hold an Accuracy marker, hidden under the later traces. The pass says it is "not Accuracy".**
   - **Ledger text:** header L:9966, "and in Phase 1's only scalar-series markers". Body L:10019-10022, "a marker cluster that is the Recall and ROC-AUC series, not Accuracy … 11 of Recall's and 8 of ROC-AUC's (round 2, Lane 10-R2B…)". Consensus record L:10282 and L:10301-10302.
   - **Evidence, draw order:** Accuracy is trace 0 (`metrics_panel.py:2271-2285`), so the Recall and ROC-AUC markers are drawn over it.
   - **Evidence, the pixels:**
     - Two pixels where the ROC-AUC and Recall markers meet, (463,1217) `#5d9c64` and (468,1217) `#598c5b`, each unmix to about 70% Accuracy `#28a745` plus ROC-AUC, with fit residual under 1.
     - No mix of the other series' colours reaches R≈90 with B≈100.
     - They sit at about 98.6%, using 2.1 px per 1% from the "80%" label. That matches the 98.75% tile and falls between ROC-AUC (≈99.5%) and Recall (≈97%).
   - **Evidence, controls:** A-N2's Accuracy marker is partly exposed in the same arrangement (positive control). A-N2's marker line below its cluster gives 0 Accuracy-weighted pixels (negative control).
   - **Evidence, the lane's own caveat:** R2B listed exactly this under what it could not check.
   - **Evidence, the counts:** R2B's exact count was 7/7, not 11/8.
   - **Fix:** "…the Recall and ROC-AUC markers over a mostly hidden Accuracy marker. No pixel matches Accuracy's colour exactly (7 Recall, 7 ROC-AUC exactly; 11 and 8 within a colour distance of 20), but two at their junction are about 70% Accuracy green, at about 98.75%." Header: "one Accuracy point after the run in both archived captures (mostly hidden in Phase 1's)". Drop "not Accuracy" from the Consensus record. W1-09 stays FAIL, because one point is not "accumulate points".
   - **Changes a number, disposition or action?** No.

3. **MINOR: the round-2 record credits both lanes with a conclusion one of them rejected.**
   - **Ledger text:** L:10279-10281, "so the planned live check could not have failed (both lanes)".
   - **Evidence:**
     - R2:94: Lane 10-R2A said "item 18's drive as written still exercises the path".
     - Only R2B argued the point, and conditionally, for a check induced by a W14 cascor restart (R2:148).
     - A reconnect after a socket loss, one of the entry's own triggers, delivers a non-empty burst.
   - **Fix:** "…so a check induced by a cascor restart (W14) could not have failed (Lane 10-R2B; Lane 10-R2A judged item 18 as written still exercised the path)".
   - **Changes a number, disposition or action?** No.

4. **NIT: F-CANOPY-057's Severity bullet still reads as current state.**
   - **Ledger text:** L:9117-9118, "canopy `main` still promises the stream (`docs/USER_MANUAL.md:764`, …)".
   - **Evidence:** at the pin it does not (rows 5-6). The new Status bullet frames the old rating, but this sentence is false in the present tense.
   - **Fix:** change "promises" to "promised (until canopy#684)".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live. Finding 1's mid-run persistence and the mid-run frame cadence come from source only.
- Finding 2 rests on pixel unmixing of one antialiased capture. Run `20260810T002233Z` archived no metrics rows, only PNGs and `statuses.tsv`, so the hidden point's value cannot be read from data.
- I did not re-run Lane 10-B2's node run or Lane 10-A2's relay and panel runs.
- The "re-derived by the orchestrator" list is process history and cannot be checked.
- I did not read deployed `.env` overrides of the burst count or the resume timeout.

**SECRETS/PII:** No environment variables, tokens, credentials or e-mail addresses were printed or sent.
- **Git:** only `show <rev>:<path>`, `merge-base`, `archive`, `rev-list -1` (SHA only), `ls-tree`, `grep`, `diff --quiet` and `status --porcelain`. No `git log`, no `--stat`, no REST commit objects.
- **gh:** `gh pr view` was filtered by `--jq` to the title, state, mergedAt, merge oid, branches and file paths.
- **Probe:** its output was filtered to its result lines, and the saved output holds 0 e-mail-shaped strings.
- **Services and files:** no service or port was touched, and no tracked file changed.
- **Scratch:** all work is in the `mktemp -d` directory `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/r3a.kGRswA`.
- **Changed:** none.
- **Slips:** none.

---

## Lane 10-R3B - round 3, adversarial on the corrections

*agent `a09866a22515100dc` · round 1 · last-assistant-text (not resumed) · 12428 chars*

**VERDICT:** SOUND-WITH-FIXES. The counts and F-CANOPY-057's re-rating hold. Findings 1–3 change an action (item 18's deciding drive), so under §4 the review does not end at this round.

**CLAIMS ATTACKED THAT SURVIVED**
- **Triage counts.** On a copy of `0d3c337b`'s ledger the tool gives 78 / 53 / 1 / 2 / 22, no P0, 6 open P1 and 16 open P2.
  - F-CANOPY-057 reads `OPEN P2`. Its first token is "P2 since canopy#684", and its 170-character tail holds no FIXED, ACCEPTED or WITHDRAWN.
  - F-CANOPY-065 reads P1 (the first token of its conditional). F-CANOPY-067 reads P2.
  - No "7 open P1" or "15 open P2" is left outside the dated round records.
- **canopy#684.** It came from branch `fix/idle-cuts-round3-wording`, merged 2026-09-24T11:10:28Z as `f2147403`, is an ancestor of `1b2dd438`, and changed both docs.
  - At the pin, `USER_MANUAL.md:669-670` and `:765-766` and the FAQ's status note all say no weight reaches the page.
  - No other manual or REFERENCE text promises the stream, so the P2 basis holds.
- **F-CANOPY-065's "No manual or REFERENCE text makes this promise".** Neither file mentions the toast, skips or `set_params`. The Parameters-tab store is fed the sent `params`, not the `applied` partition.
- **"After a socket loss while cascor stays up" is reachable.**
  - The relay reconnects on peer close, liveness expiry, client/OS errors and any other exception (`cascor_service_adapter.py:657-914`).
  - cascor-client never sends `resume`, so every connect waits out the 5 s handshake and gets the burst (`training_stream.py:60-79`, `:281-300`).
  - canopy's own `/ws/training` cannot replay the burst.
- **W8 step 13's mechanism, given a real swap.** `main.py:4100-4101` reaches `service_backend.py:460`. The old backend's shutdown leaves cascor alone (`service_backend.py:470-474`), and cascor keeps its rows (`manager.py:2931`, `monitor.py:232-248`).
- **Transience on an idle page in the Sliding Window view.**
  - The burst stamps the liveness clock (`ws_dash_bridge.js:273`), and liveness is a 5000 ms check (`dashboard_manager.py:4544`).
  - The stale poll's fetch differs from a store holding flat rows, so `:7941` does not suppress it.
  - The drain runs on `fast-update-interval`, which is only clamped during an Apply.
- **A-N2 log times.** Line 34 is 14:27:30,725, line 35 is 30,768 (43 ms later), line 37 shows `initial_status` at 35,770, and line 39 counts `initial_metrics=1`.
- **F-CANOPY-064's scalar series.** They are not phase-filtered (`metrics_panel.py:2032-2072`), and cascor puts the C7 scalars on each drain's last row whatever the phase (`manager.py:2332-2394`). `manager.py:2931` is the plain-Start retain line.
- **F-CANOPY-060's page route.**
  - `max_symbols` is rendered on the page and not excluded (`dataset_schema.py:146-149`, `:314-340`).
  - juniper-data takes `cap = min(requested, ceiling)` and refuses by default (`generator.py:508-511`).
  - `symbols` travels only as the registry seed (`model_registry.py:234-238`).
- **Small references.** The N5 fake is at `:309` and the extractor docstring at `:1429-1430`. The round-2 script, briefs and reports all exist at `0d3c337b`.

**FINDINGS**

1. **MAJOR — F-CANOPY-067's "transient by source" is false in two views, and the drive named to decide it can only see the transient case.**
   - **Ledger text:** "**Severity: P2, because the zeros are transient by source** … after 5 s of quiet the REST poll replaces the store … during a run the next relayed frame replaces the tiles. A live drive of W8 step 13 decides it: P1 if the zeros persist beyond a few seconds" (:10170-10173). The header says "P2 while the zeros are transient" (:10135).
   - **Evidence, canopy `1b2dd438`:**
     - The clientside `extendTraces` callback (`metrics_panel.py:1015-1142`, triggered by `ws-metrics-buffer` at `:1139`) has no display-mode check. It writes a missing accuracy as `0` (`:1037`) onto the Accuracy trace (`:1095`) by changing the page's figure directly, and returns `no_update`.
     - In Full History and Between Hidden Units the store never changes after a burst:
       - the WS append opts out (`dashboard_manager.py:7827-7828`);
       - an idle fetch equals the store, so `:7941` returns `no_update`;
       - those two callbacks are the store's only writers (`:4747`, `:4780`).
     - The figure callback's only inputs are the store, the theme and the view (`metrics_panel.py:970-972`). So the burst's zero-accuracy points (about 99 for a growth run's last 100 rows) stay until the next run, a theme or view change, or a reload.
     - W8 step 13 rebuilds the tab bar of the clicking page only (`dashboard_manager.py:2748-2754`). That page's panel re-mounts in its default Sliding Window view (`metrics_panel.py:642`), so a drive "with a page open" sees only the transient case. Every other open page gets the burst and keeps its view.
     - During a run, only the tiles recover at the next frame. The store keeps the burst rows while the stream is live (`:7877`, last 500 rows kept, `:7833-7834`); Lane 10-R2B itself recorded "Burst rows stay in the store while the stream is live". The source does not bound the charts' zeros to a few seconds.
   - **Fix:**
     - Restate the basis: transient by source for the tiles, and for the charts only on an idle page in the Sliding Window view. In Full History and Between Hidden Units, the ungated `extendTraces` path paints zero accuracies that nothing redraws while cascor is idle.
     - Hold a second page in Full History through the deciding W8 step 13 drive.
   - **Changes a number/disposition/action?** Yes: an action, and F-CANOPY-067's rating if the drive confirms the source, since the ledger's own rule makes persisting zeros P1.

2. **MINOR — Item 18 runs the rating drive after the fix that removes the zeros, so it cannot return P1.**
   - **Ledger text:** "normalize or drop the `initial_metrics` burst … Then drive it live: … W8 step 13 …, which also settles F-CANOPY-067's rating" (:10335-10338). F-CANOPY-067 adds "A live drive of W8 step 13 decides it … (Still owed, item 18)" (:10172-10173).
   - **Evidence:** once the burst is normalized or dropped, no zero can appear. Round 2 replaced the trigger but kept round 1's order (`2134ca2a`, item 18).
   - **Fix:** run the W8 step 13 rating drive on unfixed `main` before the fix, with pages in both views. Repeat it after the fix as verification.
   - **Changes a number/disposition/action?** Yes (action).

3. **MINOR — W8 step 13 fires only when the recurrence leg is configured.**
   - **Ledger text:** "on a switch back to CasCor from the LMU model, W8 step 13 … `/api/model/select` runs `_swap_backend`, which awaits the new backend's `initialize()`" (:10158-10160). The Consensus record says "fires it every time" (:10279).
   - **Evidence:**
     - `recurrence_service_url` defaults to `None` (`src/settings.py:262`).
     - Without it, no selection targets the recurrence backend (`src/main.py:3980`), so both selects take the no-op branch (`:4086-4089`). No relay starts and no burst is sent.
     - The isolated stack's recurrence leg is opt-in (`util/isolated_stack.bash:98`, `WITH_RECURRENCE=0`), and the matrix marks every W8 step N-A without it (matrix `:1131-1135`).
     - On a default stack the check reads clean. That is the same failure as the cascor-restart trigger round 2 replaced.
   - **Fix:** in the bullet and in item 18, add "with the recurrence leg up (`--with-recurrence`), else both selects are no-ops and no burst is sent". Change "every time" to "every time the swap is real".
   - **Changes a number/disposition/action?** Yes (action).

4. **MINOR — F-CANOPY-064's reading of Phase 1's capture claims more than a colour count can show, and contradicts its own new count.**
   - **Ledger text:** "a marker cluster that is the Recall and ROC-AUC series, not Accuracy. The cluster holds no pixel of Accuracy's colour against 11 of Recall's and 8 of ROC-AUC's (round 2, Lane 10-R2B, reproduced by the orchestrator)" (:10020-10022). The header has "in Phase 1's only scalar-series markers" (:9966); the Consensus record repeats the reading (:10282-10283).
   - **Evidence:**
     - Accuracy is trace 0, drawn beneath F1, Precision, Recall and ROC-AUC (`metrics_panel.py:2274-2290`). The order is the same at `67bf9c82`, canopy `main` when Phase 1 ran, and the y-axis is fixed at [0, 1].
     - In the Phase 1 capture, ROC-AUC fills rows 1214-1217 and Recall rows 1218-1222 (columns 463-468). An Accuracy point at the tile's 98.75% would sit about 2.6 px below the top, inside that band, and be fully hidden.
     - F1's trace exists (it is in the legend) and rides the same rows, yet it also shows 0 pixels in the cluster. Occlusion is visibly at work.
     - The A-N2 capture has the same cluster, offset +65 px. Its Accuracy point (96.30%, below Recall) shows only as a 4-pixel sliver under Recall's marker (`dashboard_final.png`, row 1158, x 571-574).
     - The entry's own new count, "one after it, at any budget", predicts exactly that hidden point.
     - Lane 10-R2B reported 7 and 7 (exact colour match). The ledger's 11 and 8 need a tolerance of about ±15; they are the orchestrator's figures, not R2B's.
   - **Fix:** describe the cluster as one where only Recall's and ROC-AUC's colours show. Say that an Accuracy point at 98.75% would be hidden between their markers, so the capture neither shows nor excludes it. Give the exact-colour counts 0 / 7 / 7 (Lane 10-R2B). In the header, write "none visible in Phase 1's".
   - **Changes a number/disposition/action?** No. W1-09 stays FAIL, since at most one point is not "accumulating".

5. **MINOR — F-CANOPY-057 is still called P1 as current state in two places.**
   - **Ledger text:**
     - its own Severity bullet: "**Severity: P1** … canopy `main` still promises the stream" (:9117-9118);
     - Phase 9's item 15: "F-CANOPY-056 and F-CANOPY-057 P1, F-CANOPY-059 P0" (:9762-9764), which Phase 10 carries forward as standing (:10326).
   - **Evidence:** "still promises" is false at `1b2dd438`, where the manual says "Today no weight sample reaches the page" (`:765-766`).
   - **Fix:**
     - Severity bullet: "P1 until canopy#684 (status above); canopy `main` then promised …".
     - Phase 10's change list: add "Item 15: F-CANOPY-057 is now P2; F-CANOPY-056 and F-CANOPY-059 are FIXED".
   - **Changes a number/disposition/action?** No.

6. **NIT — F-CANOPY-065's condition was not carried into four places.**
   - **Ledger text:** ":9814 (P1, OPEN)", ":9834 P1 … OPEN", ":9794 two of them P1", ":10343 (P1)".
   - **Evidence:** the header (:10059) and the severity bullet now make P1 conditional on the owner's question. Lane 10-R2B's Finding 2 named these exact places.
   - **Fix:** append "(conditional; the owner's question)" in each place.
   - **Changes a number/disposition/action?** No.

7. **NIT — The Consensus record says both lanes reached a conclusion that one lane contradicted.**
   - **Ledger text:** "…while a cascor restart's burst is empty, so the planned live check could not have failed (both lanes)" (:10279-10281).
   - **Evidence:** Lane 10-R2A found the swap trigger, not the empty burst, and concluded that "item 18's drive as written still exercises the path" (round-2 reports file, :94).
   - **Fix:** attribute the empty burst and the conclusion to Lane 10-R2B, and record Lane 10-R2A's contrary reading.
   - **Changes a number/disposition/action?** No.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live, by rule. The Full History persistence, the view reset on the W8 re-mount, how long zeros last during a run, and the W8 timing are all read from source.
- I did not replay the round-2 script; that is R3A's check.
- Phase 1's plot height is taken from the A-N2 capture, which uses the same layout code. The hidden marker's position is computed, not observed.
- I did not check whether Phase 1's cascor (v0.6.0) labelled rows the way `95cdc562` does.
- I did not read any deployed overrides of the burst size or the handshake timeout.

**SECRETS/PII:** Nothing was printed or sent. Git use was limited to `show <rev>:<path>`, `diff`, `diff --stat`, `rev-list --parents`, `merge-base`, `cat-file -t`, `ls-tree`, `grep`, and `log` with `%h %cs %s` / `%s %cI` only, so no author fields. `gh pr view 684` returned only `mergedAt`, `headRefName`, `state` and `title`. Scratch work stayed in `/tmp/tmp.GavgXsxy0c`. No service, port or tracked file was touched. No slips.

---
