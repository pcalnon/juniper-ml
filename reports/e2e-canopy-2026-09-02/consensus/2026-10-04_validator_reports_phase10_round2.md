<!-- markdownlint-disable -->

# Phase 10 ledger validation, round 2 (frozen 2134ca2a)

Two lanes on round 1's corrections to the canopy E2E ledger's Phase 10, frozen as 2134ca2a, briefed separately (briefs in reports/e2e-canopy-2026-09-02/drafts/lane10R2A_phase10_ledger_brief.md and lane10R2B_phase10_ledger_corrections_brief.md): 10-R2A re-derived every claim the corrections introduced, artifact-first; 10-R2B attacked what the correction pass broke. Each report is the lane's final message, verbatim. (The archiver labels each agent's only report 'round 1' because neither agent was resumed; both are round-2 lanes.)

## Lane 10-R2A - round 2, artifact-first

*agent `a29c5733548ec921f` · round 1 · last-assistant-text (not resumed) · 15425 chars*

**VERDICT: SOUND-WITH-FIXES.** The correction pass replays exactly. Every factual claim in the nine I was briefed on checks out from its source, with four exceptions. One of them (Finding 1) changes a count and a severity rating, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this round does not end the review.

**How I read the sources.** Canopy came from `git archive 1b2dd438`. Cascor (`95cdc562`), juniper-data (`29be6d35`) and cascor-client (`3adc061f`) came from `git -C <repo> show <sha>:<path>`. juniper-ml came from the worktree at `2134ca2a`. Everything went into `mktemp -d` → `/tmp/tmp.n0ikDp2aec`. Line numbers are read from those copies, and "ledger" line numbers refer to `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `2134ca2a`.

**TABLE**

| # | Claim | Re-derived value | Result | Evidence (command → output) |
|---|---|---|---|---|
| 1 | Replaying `2026-10-04_phase10_ledger_round1_corrections.py` on `0737d573`'s ledger reproduces `2134ca2a`'s ledger, except two hand-written parts | Only those two parts differ | MATCH | `replay.py` loads the script with importlib, runs `apply()` on `git show 0737d573:<ledger>`, and diffs against `2134ca2a` → `SUBS=35 SPANS=8 placeholder_present=True`. Two hunks remain: `@@ -10177,0 +10178,3 @@` (the Instruments addition) and `@@ -10181 +10184,47 @@` (the `CONSENSUS_RECORD_PENDING` placeholder becomes the Consensus record plus `ROUND2_PENDING`). |
| 2a | cascor `training_stream.py:281-300` | `:282` sets the count with a default of 100; `:299-300` calls `_send_initial_state` when the connect is not a resume. That function (`:82-123`) sends `initial_status`, then `state`, then `initial_metrics`. | MATCH | The cited range is the call site. The ledger leaves out `initial_status`; that is an omission, not an error. |
| 2b | cascor `settings.py:382` | `ws_initial_metrics_count: int = Field(default=100…` | MATCH | read from `git show` |
| 2c | The burst rows are flat and carry `kind` | `monitor.py:300-310` builds flat rows with `loss`, `accuracy` and `kind`. The burst comes from `get_metrics_history`, which calls `monitor.get_recent_metrics` (`manager.py:3467-3471`). | MATCH | read from `git show` |
| 2d | canopy adapter `:774-780` | `data = message.get("data", message)`. Only `metrics` frames are normalized; every frame type is broadcast. | MATCH | read |
| 2e | `ws_dash_bridge.js:261-270` | The `initial_metrics` handler pushes each `data.metrics[i]` into the buffer, and `drainMetrics` (`:84-88`) passes them on unchanged | MATCH | read |
| 2f | `dashboard_manager.py:7813-7834` | Appends the events unchanged. The callback output is `metrics-panel-metrics-store` (`:4779-4788`). | MATCH | read |
| 2g | `metrics_panel.py:1671-1672`, `:1952`, `:2260` | All three read `.get("metrics", {}).get(…, 0)` | MATCH | read |
| 2h | "The relay connects at canopy's startup, before any page is open, so that burst reaches no page" | False as a general statement | MISMATCH | Finding 2 |
| 2i | "It reaches pages on a relay reconnect" | True. The relay loop reconnects (`:657-661`, `:880-914`). cascor-client never sends a `resume` frame (`ws_client.py:335-353`), so every connect gets a burst. | MATCH | read |
| 3a | `get_current_metrics` / `get_recent_metrics` at `:457-482` | Both call `_to_dashboard_metric(_normalize_metric(…))` | MATCH | read |
| 3b | State sync "at boot and on a model swap" (`state_sync.py:150`) | Its only caller is `service_backend.py:456`, inside `initialize()`. `initialize()` runs at startup (`main.py:452`/`:457`) and from `_swap_backend` (`main.py:4101`). | MATCH | `grep -rn "CascorStateSync(" src` (tests excluded) → one hit |
| 3c | `extendTraces` at `metrics_panel.py:1015` and `:1032-1037` | Reads `e.loss \|\| e.error \|\| e.current_error` and pushes a missing accuracy as 0. The output of `_to_dashboard_metric` (`:1968-1991`) has none of those top-level keys. | MATCH | read |
| 3d | Only a growth run's last step row, drained at `:2150`, carries `output` | Phase goes to candidate at `:2091-2092` and back to output at `:2144-2145`. Of the drains at `:2078`, `:2115`, `:2150` and `:3029`, only `:2150` and `:3029` run after the return to output. The initial pass's history append (`cascade_correlation.py:1962`) is followed by `grow_network` with no event in between. | MATCH (source only) | read |
| 3e | 401 rows per pass; 4,422 = 11 × 401 + 11 | Archived `count` 4422. Within-pass epochs run 1, 26 … 9976, 10000, which is 401 rows; the final step row is epoch 11, labelled `output`, accuracy 0.963. | MATCH | `c3_hist2.py` on `13_render_api_metrics_history_limit_0.json` |
| 3f | Default Sliding Window of 500 | `canopy_constants.py:511`, used by `metrics_panel.py:642`. The last 500 rows hold only step rows 10 and 11. | MATCH | read |
| 3g | canopy's default of 25 epochs per pass (`canopy_constants.py:75`) | `DEFAULT_OUTPUT_EPOCHS: Final[int] = 25`; the control run's `03_set_params_caps.json` returned 502 | MATCH | read |
| 3h | Archived tiles read "11, 13, 22 and 2" (side check) | 11, 13, 22, 22, 2 | MATCH | `tiles.py` over the `dashboard*_text.txt` captures |
| 4a | `M-METRICS-29__post-run-plots.png` | Viewed. Window 500; Training Step 11; Accuracy 98.75%. The axis runs 0–10k, and the accuracy chart's gridlines line up with the loss chart's ticks. One marker cluster sits at the "+Unit #10" line and there is no accuracy line; the chart is cropped at about 90%. | MATCH | Read plus a cropped zoom |
| 4b | `statuses.tsv:75` and `:81` | `M-METRICS-30 PASS(post-run) accuracy plot 6 traces…` and `W1-01..11 PASS …` | MATCH | read |
| 4c | Matrix W1 step 9 | `9. Metrics tab: KPI tiles populate; loss and accuracy plots accumulate points.` (`…E2E-CLICK-BY-CLICK-TEST-MATRIX.md:972`). The text is identical at the run-era revision `e835e2b4` (`:723`). M-METRICS-30 is "zoom / pan" (`:447`). | MATCH | read; `git log --format='%h %cs %s'` |
| 4d | "No later run re-scored it" | No W1-09 or W1-01..11 verdict after 2026-08-10. The only later W1 row is `20260826T215010Z/statuses.tsv:4 W1-12`. The ledger mentions W1-09 only in Phase 10's corrections. | MATCH | `grep` over every run's `statuses.tsv`, `grep -rln` over `reports/` and the ledger |
| 5a | `_compose_apply_toast` at `:9091-9145` | The function spans exactly 9091–9145 | MATCH | AST parse |
| 5b | The two toast strings | On the archived answer: `'Parameters applied'`. Archived answer plus the WS partition (three WS keys applied, one REST key applied, one WS skip): `'Applied 4 parameter(s); 1 skipped: nn_max_total_epochs (not-updatable)'`. The WS partition alone gives "Applied 3". | MATCH | `c5_toast.py` runs the real function, lifted by AST |
| 5c | canopy `CHANGELOG.md:1975-1980` under `[0.6.0]` | The quoted text is there; the `[0.6.0]` heading is at `:1786` | MATCH | read |
| 5d | Defects plan `:311` (juniper-ml) | "T3 — Apply reporting contract … canopy renders both sets." | MATCH | read |
| 5e | `test_n5_apply_params_ux.py:308` | `:308` is `fake_future = MagicMock()`. The flat fake is on `:309`. | MISMATCH | Finding 3 |
| 5f | Adapter `:1429-1430` | "…the WS ack carries it flat," | MATCH | read |
| 6a | Seed at `model_registry.py:267-277` | The `equities` seed has the five symbols AAPL, MSFT, GOOGL, AMZN, NVDA | MATCH | read |
| 6b | "Every canopy staging path sends the seed" | The sidebar Apply (`:3464`, where `symbols` is never rendered so it always travels), the restart modal (`:6638-6640`), the one-shot dataset reference (`:2943-2945`), and the re-stage (`:8464-8480`, which re-sends the staged params) | MATCH | read |
| 6c | juniper-data `generator.py:314`, then `:338` | `:314` is `_resolve_symbols`, which applies the cap (`ordered[:cap_symbols]` at `:746`). `:338` is `_apply_incomplete_policy`. | MATCH | read |
| 7a | Tests at `:420` and `:429` | `docs_enabled is False` and `docs_enabled is True` | MATCH | read |
| 7b | "Phase 4's status correction" states the keep-OPEN rule | Ledger `:6144-6156`: "Every one of those entries still needs its live row re-drive before its header token changes…" | MATCH | read |
| 8 | The eleven grep lines and the nine claim-bearing ones | 11 lines. The two that quote #532's retracted label are `test_p2_wave_batch_a.py:181` and `test_f059_replay_range_dict.py:14`; the other nine are exactly as listed. | MATCH | `grep -rniE "verbatim from\|measured o(n\|ff) the\|exact shape" src/tests` |
| 9a | "35 substitutions and 8 span rewrites" | 35 / 8 | MATCH | replay output |
| 9b | "25 files" | 12 from Lane A2, 4 from B1 and 9 from B2: 25 | MATCH | `git ls-tree -r --name-only 2134ca2a -- util/ad-hoc/` filtered on `2026-10-04_phase10_r1_(a2\|b1\|b2)_` |
| 9c | Counts | 78 findings, 53 fixed, 1 accepted, 2 withdrawn, 22 open. 7 open P1 (F-CANOPY-055, -057, -058, -064, -065, F-CASCOR-001, -002), 15 open P2, no P0. | MATCH as read by the tool | `python3 -B util/ad-hoc/e2e_finding_triage.py --note <copy>`. The tool only echoes the ledger's own heading tokens, so it cannot see Finding 1. |

**FINDINGS**

1. **MAJOR — F-CANOPY-057's P1 rating is out of date at the pins, and three corrections rely on it.**
   - **Quoted text:**
     - `:10089-10090`: "This ledger already treats a promise outside the manual as documented: F-CANOPY-057 is P1 on the manual and a FAQ."
     - `:10220-10221`: "If it does not, F-CANOPY-065 and F-CANOPY-057 both return to P2."
     - `:9814` and `:10239-10240`: "**7 open P1:** F-CANOPY-055, F-CANOPY-057, …"
   - **What F-057's own entry says (`:9110-9115`):** its P1 rests on "canopy `main` still promises the stream (`docs/USER_MANUAL.md:764`, `notes/development/REPLAY_V2_FAQ.md:253`)". It also says "It returns to P2 when the canopy follow-up that corrects both files merges (branch `fix/idle-cuts-round3-wording` …); that re-rating is owed with the merge."
   - **That follow-up has merged:**
     - `gh pr view 684 … --jq` → `headRefName fix/idle-cuts-round3-wording`, `MERGED`, `2026-09-24T11:10:28Z`, oid `f2147403…`.
     - `git merge-base --is-ancestor f2147403 1b2dd438` → exit 0, so it is in the pinned canopy.
     - `git diff --stat f2147403^ f2147403` shows it changed both files.
     - At `1b2dd438`, `USER_MANUAL.md:764-766` now reads "…Today no weight sample reaches the page", and the FAQ's new status note reads "No replay weight reaches the page (F-CANOPY-057…)".
   - **Consequences:**
     - The precedent cited for F-065 no longer exists at the pins.
     - F-057 was never rated on a CHANGELOG or design-plan promise, so the owner's ruling on that question could not move it in either direction.
     - The triage tool's 7 counts F-057.
   - **Scope:** the out-of-date rating was already in round 1's freeze. The corrections repeat it and build on it.
   - **Fix:**
     - Apply F-057's owed re-rating to P2, citing canopy#684 / `f2147403`.
     - Counts become 22 open: 6 open P1 (F-CANOPY-055, -058, -064, -065, F-CASCOR-001, -002) and 16 open P2.
     - Delete the F-057 precedent sentence from F-065's severity bullet. F-065's P1 then rests on Lane 10-B1's reading of plan §6.3 alone.
     - Reword the Unresolved item to "If it does not, F-CANOPY-065 returns to P2."
   - **Changes a number/disposition/action? Yes.** Open P1 goes 7→6, open P2 goes 15→16, and F-057 goes P1→P2.

2. **MINOR — F-CANOPY-067's "When it fires" is wrong about startup, and it misses a trigger a page can cause.**
   - **Quoted text (`:10137-10139`):** "The relay connects at canopy's startup, before any page is open, so that burst reaches no page. It reaches pages on a relay reconnect, after a cascor restart or a dropped socket…"
   - **The relay also connects on a model swap, with the page open:**
     - The model picker posts `/api/model/select` (`dashboard_manager.py:3474`).
     - That calls `_swap_backend`, which awaits `new_backend.initialize()` (`main.py:4100-4101`).
     - `initialize()` calls `start_metrics_relay()` (`service_backend.py:460`), which starts the relay as a task that connects (`cascor_service_adapter.py:953`, `:661`).
     - The page's own canopy socket is untouched, and `broadcast` (`websocket_manager.py:679-734`) reaches every connection open at that moment.
   - **The startup burst is delayed about 5 seconds:**
     - cascor-client's `connect()` sends no frame.
     - cascor therefore waits out its resume window, `_await_resume_frame` (`training_stream.py:60-79`), whose default is 5.0 s (`settings.py:51`, `:367-371`), before sending the burst.
     - By then canopy's startup has finished and it is serving. A page that has reconnected across a canopy restart (`websocket_client.js:158-169`) can receive the burst. I did not measure this timing.
   - **Fix:** say the relay connects at startup, on every swap back to cascor, and on reconnects. Say the burst lands about 5 s after each connect and reaches every page open then. Add the model swap to item 18 as a trigger that fires every time.
   - **Changes a number/disposition/action? No.** The rating rule is unchanged, and item 18's drive as written still exercises the path.

3. **NIT — wrong line reference.**
   - **Quoted text (`:10081`):** "(`src/tests/integration/test_n5_apply_params_ux.py:308`)"
   - **Evidence:** `:308` is `fake_future = MagicMock()`. The flat fake `{"applied": ["learning_rate"]}` is on `:309`, and round 1's Lane 10-B1 cited `:309` (`2026-10-04_validator_reports_phase10_round1.md:218`).
   - **Fix:** change it to `:309`.
   - **Changes a number/disposition/action? No.**

4. **NIT — wrong key count.**
   - **Quoted text (`:10068-10069`):** "unwrapping the ack in `_apply_params_hot` alone recovered all four WS keys and the skip."
   - **Evidence:**
     - Only four keys go over WS: max_hidden_units, epochs_max, max_iterations and output_epochs (`cascor_service_adapter.py:1167-1170`, hot set at `:1233-1256`). One of them, epochs_max, is the skip.
     - `cn_training_iterations` goes over REST (`:1178`, cold set at `:1258-1280`).
     - Lane 10-A2's report says "all four keys and the skip" (round-1 report `:141`), meaning three WS keys plus one REST key.
     - The same ledger paragraph says "the three WS keys" two lines earlier.
   - **Fix:** "recovered all four applied keys (three WS, one REST) and the skip".
   - **Changes a number/disposition/action? No.**

**WHAT YOU COULD NOT CHECK**
- I did not re-run the round-1 lanes' executions: Lane 10-A2's relay-loop and panel run, Lane 10-B2's node run, and the `TrainingMonitor` reproductions.
- Claim 3d (only the last step row carries `output`) is confirmed from source only. The event order is read in source, and there is no unslimmed history to count against.
- Whether a page is actually connected when the startup burst lands (Finding 2) is a timing question I could not measure without a live stack.
- Phase 1's capture is cropped at about 90%, so "no accuracy line" is confirmed only in the visible top band.
- I did not re-view the A-N2 `dashboard_final.png` zoom ("one point at x = 11"); it was outside my claim list.

**SECRETS/PII**
- No environment variables, tokens or credential files were printed or sent anywhere. No author fields were printed: I used no `git show --stat`, my `git log` used `%h %cs %s` only, and `gh pr view` was filtered by `--jq` to the branch name, state, merge time and oid. No REST commit objects were fetched.
- No service or port was touched, and no tracked file was changed. Scratch work is only in `/tmp/tmp.n0ikDp2aec`.

---

## Lane 10-R2B - round 2, adversarial on the corrections

*agent `aa273d8de4d7f5fbf` · round 1 · last-assistant-text (not resumed) · 16096 chars*

**VERDICT: SOUND-WITH-FIXES.** The counts, the entry headers, the line references and most of the rewrites hold. Two corrections are wrong in ways that change an action or a count:
- F-CANOPY-067's trigger analysis would lead item 18 into a live check that cannot fail.
- F-CANOPY-065's re-rating rests on an F-CANOPY-057 precedent whose own P1 lapsed before the pin.

Abbreviations: **L** = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `2134ca2a`. **M** = `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`. **R1** = `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md`. Canopy paths are at `1b2dd438`, cascor at `95cdc562`.

**FINDINGS**

1. **MAJOR — F-CANOPY-067's "When it fires" names the wrong triggers and misses the reliable one.**
   - **Ledger text:** "The relay connects at canopy's startup, before any page is open, so that burst reaches no page. It reaches pages on a relay reconnect, after a cascor restart or a dropped socket (F-CANOPY-049, F-CASCOR-004)" (L:10137-10140). The header scopes it to "after a relay reconnect while a page is open" (L:10117). Item 18 drives it "across a relay reconnect with a page open, which also settles F-CANOPY-067's rating" (L:10254-10255).
   - **Evidence, model switch:** `/api/model/select` calls `_swap_backend` (`src/main.py:4117`, `:4070`), which awaits `new_backend.initialize()` (`:4101`). That starts a fresh relay (`service_backend.py:443-460`, then `cascor_service_adapter.py:953`). Switching back to CasCor from the LMU model is W8 step 13 (M:1149), clicked on the open page. Cascor still holds its rows: they live in memory (`monitor.py:191`) and are kept across runs by default (`monitor.py:232-248`, `manager.py:2931`). So that page receives the burst on every such switch, with no fault needed.
   - **Evidence, canopy startup:** in the A-N2 log (`reports/2026-09-23_canopy-a-n2-generate-stage-train-render/00_stack/logs/juniper-canopy.log`):
     - "Application startup complete" at 14:27:30,725 (:34);
     - the relay connects at 14:27:30,768 (:35);
     - the burst's first frame arrives at 14:27:35,770 (:37).
     - Cascor waits out its 5 s resume handshake before sending the burst (`training_stream.py:60-79`, `:282-300`; the 5.0 s default is at `settings.py:51`).
     - Canopy is already serving pages during that window. A tab left open across a canopy restart reconnects on jittered backoff (`websocket_client.js:162-164`).
   - **Evidence, cascor restart:** a new cascor process has an empty buffer, and `_send_metrics_burst` still sends the frame (`training_stream.py:110-123`). That burst carries no rows. This fits F-CANOPY-002's Phase 1 record that `initial_metrics` "stamps the drain at reconnects" with "buffer 0" (L:161).
   - **Evidence, the cited findings:** F-CASCOR-004 and F-CANOPY-049 (L:6388-6412) describe drops the relay never reconnects from.
   - **Consequence:** if item 18 induces the reconnect the usual way (W14: stop and restart cascor), the burst is empty, no zeros appear, and the check reads clean.
   - **Narrowest replacement:** "Every page open when the burst lands, 5 s after the relay (re)connects to a cascor that still holds monitor rows. That happens on a switch back to CasCor from the LMU model (W8 step 13), on a canopy restart whose open tabs reconnect inside that window, and on a reconnect after a socket loss while cascor stays up. A cascor restart sends an empty burst." Header: "after the relay (re)connects while a page is open". Item 18 and F-064's fix direction: drive "W8 step 13 after a CasCor run, with a page open (not a cascor restart)".
   - **Changes:** the action, yes; no number or disposition.

2. **MAJOR — F-CANOPY-065's precedent and the owner question misstate F-CANOPY-057, whose own P1 has lapsed.**
   - **Ledger text:**
     - "This ledger already treats a promise outside the manual as documented: F-CANOPY-057 is P1 on the manual and a FAQ" (L:10089-10090);
     - "If it does not, F-CANOPY-065 and F-CANOPY-057 both return to P2" (L:10220-10221);
     - "7 open P1: …F-CANOPY-057…" (L:10239).
   - **Evidence, the basis:** F-057's P1 rests on `docs/USER_MANUAL.md:764` plus the FAQ (L:9110-9115). Plan A-2 itself counts USER_MANUAL claims as documented. So F-057 is no precedent for a promise made only outside the manual, and its rating never turned on the owner's question.
   - **Evidence, its own rule has retired it:** F-057 says it "returns to P2 when the canopy follow-up that corrects both files merges (branch `fix/idle-cuts-round3-wording`…); that re-rating is owed with the merge" (L:9113-9115).
     - `gh pr view 684`: branch `fix/idle-cuts-round3-wording`, MERGED 2026-09-24T11:10:28Z as `f2147403`.
     - `merge-base --is-ancestor f2147403 1b2dd438` returns true.
     - At the pin, the manual (`USER_MANUAL.md:764-766`) says "Today no weight sample reaches the page", and `REPLAY_V2_FAQ.md` opens with a status note: "No replay weight reaches the page".
     - L never records #684, and Phase 9's item 13 ("not yet pushed", L:9704-9714) is carried forward as standing (L:10245).
   - **Evidence, inconsistency:** F-065's header, the Summary, the provenance table and the counts all state P1 without a condition, while the Consensus record leaves its only basis to the owner.
   - **Narrowest replacement:**
     - F-065: "P1 if a CHANGELOG or design-plan promise counts as documented under plan §6.3 (the owner's question); no manual or REFERENCE text makes this promise, so it is P2 if not." Delete the F-057 sentence.
     - Consensus record: "…If it does not, F-CANOPY-065 returns to P2."
     - Apply F-057's owed re-rating to P2: 6 open P1, 16 open P2. Mark item 13's follow-up as merged.
   - **Changes:** yes. Open P1 goes 7→6, open P2 15→16, F-057 becomes P2, and F-065's P1 becomes conditional.

3. **MINOR — F-CANOPY-064's accuracy count and its header overgeneralise.**
   - **Ledger text:** "So the accuracy chart shows no point during growth and at most one after a run, at any budget" (L:10026-10027). The header adds "one point after the run, in both archived captures" (L:9955). The body says "Whatever accuracy reaches the chart sits at x ≤ N" (L:9965).
   - **Evidence, (a) retained runs:**
     - A plain Start keeps cascor's history (`manager.py:2931`), and canopy's Start is plain (`cascor_service_adapter.py:1109-1112`).
     - Phase 1 recorded exactly such a second run (`reports/e2e/20260810T002233Z/statuses.tsv:91`, "RETAINING").
     - Each retained growth run keeps its own last `output` step row. Full History therefore shows one Accuracy point per run, and so does the 500-row window when passes are short: at canopy's default of 25 epochs per pass there are about 3 rows per step.
   - **Evidence, (b) the other series:**
     - The chart's F1, Precision, Recall and ROC-AUC series have no phase filter (`metrics_panel.py:2032-2072`), and cascor puts those scalars on every drained step row (`manager.py:2380-2394`). So the chart does gain points during growth.
     - Phase 1's marker cluster is ROC-AUC and Recall. A pixel count over (440,1200)-(500,1252) of that capture finds 0 pixels of the Accuracy colour #28a745, against 7 ROC-AUC and 7 Recall pixels. The same image's legend swatch has 44.
   - **Evidence, (c) the burst:** F-067's burst rows that carry `output` plot accuracy 0 at inner-epoch x (`metrics_panel.py:2260`, `:2264`). The entry's own extendTraces bullet adds zeros during growth (L:9975-9978).
   - **Narrowest replacement:** "From the store, one growth run's Accuracy trace has no point during growth and one after it, at any budget. Earlier runs that a plain Start retains each add one point, and F-CANOPY-067's burst can add zero-valued points. The scalar series are not phase-filtered." Header: "one Accuracy point in the A-N2 capture; in Phase 1's, scalar-series markers and no visible Accuracy point".
   - **Changes:** no.

4. **MINOR — "No matrix-table row changes" (L:10234) leaves M-METRICS-32's PASS covering a half that the corrected text says fails.**
   - **Evidence:**
     - M:449 expects "a clientside `Plotly.extendTraces` path appends to both figures without a rebuild", status "PASS (re-validated @ 04f06ff)".
     - That re-score was on "the WS append path" only (F-CANOPY-002's closure, L:163).
     - The callback reads flat `e.loss` (`metrics_panel.py:1031-1037`), and the drain does not flatten rows (`ws_dash_bridge.js:84-87`).
     - The corrected F-064 text now says the path "extends nothing from a relayed `metrics` frame" (L:9976).
   - **Narrowest replacement:** add "M-METRICS-32's PASS covers its append callback only; its extendTraces half was never driven and fails by source (F-CANOPY-064, item 18)."
   - **Changes:** yes, it scopes a recorded verdict.

5. **MINOR — F-CANOPY-067's rating rule is applied to no other entry, and its escalation test cannot tell P1 from P2.**
   - **Ledger text:** "Severity: P2 until observed live. If a live check shows the tiles reading 0, it … becomes P1" (L:10141-10142).
   - **Evidence, practice:** the ledger rates unobserved findings P1 elsewhere. F-CANOPY-058 is "NOT yet observed on canopy itself" (L:9169). F-CANOPY-065's toast was "executed in isolation" (L:10225-10226). Lane 10-A2 already executed tiles reading 0 for F-067.
   - **Evidence, the real basis:** what actually distinguishes F-067 is that the zeros are transient, and the entry never says so.
     - The burst stamps the liveness clock (`ws_dash_bridge.js:273`).
     - After 5 s of quiet (`canopy_constants.py:507`), the REST poll replaces the store (`dashboard_manager.py:7877`, `:7941`) at a 5.5–7.3 s cadence (`:4719`).
     - During a run, the next nested frame fixes the tiles.
   - **Consequence:** any drive with a working trigger will see the tiles read 0 for a few seconds, so the stated rule re-rates it mechanically.
   - **Narrowest replacement:** state transience as the basis for P2, and make P1 depend on how long the zeros persist on a live drive (W8 step 13), not on their appearing.
   - **Changes:** no, if the basis is reworded.

6. **MINOR — the Consensus record misreports Lane 10-A2's instrument verdicts.**
   - **Ledger text:** "mutated each instrument to show it could answer otherwise" (L:10188-10189); "its mutations showed all three instruments adequate" (L:10193-10194).
   - **Evidence:**
     - R1:113-126 gives f060 and o2 "Verdict: adequate". o3 gets no verdict, and under the ack-unwrap mutation "every script arm prints the same … no canopy change outside the extractor can move its A-N2 arm".
     - A2's Finding 3 (R1:139-143) asks to "Have the instrument drive the real `apply_params`".
     - Item 20 omits that fix.
   - **Narrowest replacement:** "…showed f060 and o2 adequate. o3 copies `apply_params`' merge, so it cannot verify F-CANOPY-065's fix until it drives the real one." Add that to item 20.
   - **Changes:** the action, yes.

7. **NIT — four small false statements introduced by the pass.**
   - **(a) F-CANOPY-060's page route (L:9853-9854, :9871, :9877).** The ledger lists "a custom list of more than 14 symbols" as a page route, and says accepting imports "the first 14 symbols".
     - The form does not render array fields (`dataset_schema.py:317-340`), and `symbols` "can only travel as a registry seed" (`model_registry.py:235-238`), as Lane 10-B1 said (R1:170).
     - From the page, the cap must therefore be below the seed's 5 symbols, and accepting imports fewer than 5.
     - Replacement: "`max_symbols`, or a deployment ceiling, below 5; the 503-symbol case needs the API or YAML"; "the first N symbols, N the effective cap".
   - **(b) F-CANOPY-063's grep claim (L:9944).** "A claim-text grep finds only the first two kinds" is wrong. Re-running the grep gives the same 11 lines the entry lists, and none is F-CANOPY-060's fixture, whose claim is at `test_dataset_shortfall_prompt.py:37`. Replacement: "finds only the first".
   - **(c) F-CANOPY-065's unwrap result (L:10068-10069).** "recovered all four WS keys and the skip" is wrong. Re-running the archived `util/ad-hoc/2026-10-04_phase10_r1_a2_my_o3.py` prints applied `[nn_max_iterations, nn_output_epochs, nn_max_hidden_units, cn_training_iterations]` plus a `nn_max_total_epochs` skip. That is three WS keys, the fourth WS key as the skip, and the REST key. Replacement: "recovered the three WS keys the network took, the fourth's not-updatable skip, and the REST key".
   - **(d) Consensus attribution (L:10201-10203).**
     - "cascor's defaults … (Lanes 10-A2 and 10-B2)": only Lane 10-A2 reported the budgets (R1:129-133).
     - "Accuracy keyed on `phase`" as the main cause is also Lane 10-B1's (R1:175).
   - **Changes:** no.

**CLAIMS YOU ATTACKED THAT SURVIVED**
- The triage tool on `2134ca2a` gives 78 findings, 53 fixed, 1 accepted, 2 withdrawn, 22 open, 7 open P1 and 15 open P2. Every Phase 10 header parses as intended.
- Canopy's own `/ws/training` sends only `connection_established`, `initial_status` and `state` on connect (`main.py:855-875`, `websocket_manager.py:417`), with no replay buffer, so it cannot replay cascor's burst.
- Burst rows stay in the store while the stream is live. The first REST poll after it goes stale replaces them, unless the fetch is identical or empty (`dashboard_manager.py:7813-7834`, `:7877`, `:7910`, `:7941`). They never enter in the full or hidden_units modes. The ledger's "not measured" is honest.
- F-CANOPY-067 duplicates nothing: F-002, F-049, F-CASCOR-004 and F-036 cover different defects.
- "No path delivers a row in the dashboard shape that carries `kind`" holds: canopy production code reads `kind` only at `metrics_panel.py:1664`.
- "Only a growth run's last step row carries `output`" holds for a single run (`manager.py:2087-2150`); the archive's final row 11 is `output` with accuracy 0.963.
- W1-09 as FAIL holds:
  - Phase 1 credited starved during-run rows from post-run reads (L:3143-3147), and that capture shows no Accuracy line.
  - No `statuses.tsv` in the 21 run directories, and no ledger text, re-scores it.
  - M-METRICS-30's PASS stands.
  - In that run the panel was also starved during the run, on F-002/004 (`statuses.tsv:68`, `:76`).
- F-CANOPY-065's CHANGELOG `[0.6.0]` promise (`:1975-1980`), defects-plan T3 (`:311`), the N5 fake (`:308`), the extractor docstring (`:1429-1430`) and the toast text all check.
- F-CANOPY-060's cap-then-policy order (`generator.py:314`, `:338`) and fixture range `:37-46` check. The F-061/-062 exemption tests (`:420`, `:429`, `test_security.py:700`) exist.
- F-CANOPY-063's nine claim-bearing hits and two retracted-label hits reproduce exactly.
- The Consensus record's "three lanes", the re-rating and W1-09 attributions, and the slips all check; the archive and probes hold 0 e-mail-shaped strings.
- Replaying the correction script on `0737d573` reproduces the landed ledger, except the Instruments bullet and the Consensus record, which were written outside it.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live, by rule. That W8 step 13 delivers the burst to a page, and how long the zeros last, both come from reading the source.
- Round 1's relay and node executions were not re-run; only A2's o3 probe was.
- Phase 1's capture shows only about the top tenth of the chart, so an Accuracy marker may be hidden under the Recall and ROC-AUC markers.
- Deployed `.env` overrides of the burst count and of the resume-handshake timeout were not read.
- `juniper-canopy/.git/config` changed (17:13:33) during this lane. Every command I ran there was read-only, and I did not investigate the cause.

**SECRETS/PII:** No environment variables, tokens, credential files or e-mail addresses were printed or sent. Git use was `show <rev>:<path>`, `diff`, `archive`, `rev-parse`, `merge-base` and `log --format='%h %cs %s'`, with no author fields. `gh pr view 684` printed only number, title, branch, state, mergedAt and oid. The e-mail-pattern checks printed counts only. All scratch work was in `/tmp/tmp.OVkXCSFixw`, and the primary canopy log has no entries from my probe run. No slips.

---
