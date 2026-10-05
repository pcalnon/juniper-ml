<!-- markdownlint-disable -->

# Phase 10 ledger validation, round 5 (frozen b2375a51) -- the review ends here

Two lanes on round 4's corrections to the canopy E2E ledger's Phase 10, frozen as b2375a51, run 2026-10-05 from one brief (reports/e2e-canopy-2026-09-02/drafts/lane10R5_phase10_ledger_brief.md): 10-R5A re-derived every claim the round-4 pass introduced, artifact-first; 10-R5B attacked what that pass broke. No finding of either changed a number, disposition or action, so the review ended at this round. Each report is the lane's final message, verbatim. (The archiver labels each agent's only report 'round 1' because neither agent was resumed; both are round-5 lanes. The file keeps the Phase 10 family's 2026-10-04 prefix.)

## Lane 10-R5A - round 5, artifact-first

*agent `a666d112c79daa536` · round 1 · last-assistant-text (not resumed) · 11627 chars*

**VERDICT: SOUND.** Every claim the round-4 pass introduced re-derives, with two small exceptions below. The pass replays byte for byte with no hand-written hunk, and the counts reproduce. Neither finding changes a number, disposition or action, so this lane gives no reason under §4 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` for a sixth round. The two fixes are optional for landing.

**TABLE (R5A)**

Abbreviations:
- **L** = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `b2375a51`.
- **R3** = `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round3.md`; **R4** = `…/2026-10-04_validator_reports_phase10_round4.md`.
- **P** = `util/ad-hoc/2026-10-04_phase10_ledger_round4_corrections.py`.
- Canopy is read at `1b2dd438`, cascor at `95cdc562`, cascor-client at `3adc061f`.

| # | Claim | Re-derived value | Result | Evidence |
|---|---|---|---|---|
| 1 | P on `b5cb675d` gives `b2375a51` with no hand-written hunk; "7 substitutions and 1 span rewrites" | Byte-identical, 849,551 → 853,825 chars. P has 7 SUBS and 1 SPAN, and the record takes its size from those | MATCH | `apply()` imported from a scratch copy, compared with `==` |
| 2 | 78/53/1/2/22; 6 open P1; 16 open P2; no P0; "No number or disposition changed" | Same figures. The 6 open P1 are F-CANOPY-055, -058, -064, -065, F-CASCOR-001 and -002. The triage output on copies of `b5cb675d` and `b2375a51` is identical line for line | MATCH | `e2e_finding_triage.py --note` on copies |
| 3 | `recurrence_backend.py:312-315`: the backend answers `[]` until an LMU fit lands, then one point | `[metrics] if metrics else []`. `get_metrics` returns `{}` while `_result` is None (`:301-302`). `_result` is cleared at each start (`:206`), set only on success (`:233-235`) and left None after a failure (`:221-232`). Each swap builds a fresh backend (`main.py:4100`), and the route calls this method (`main.py:1562-1575`) | MATCH | read |
| 4 | `dashboard_manager.py:7910-7912`: an empty fetch never replaces a non-empty store | `if not metrics and current_metrics: return dash.no_update`. The non-OK and exception arms do the same (`:7892`, `:7947`) | MATCH | read |
| 5 | `canopy_constants.py:476-491`: a full fetch every ~27-37 s | The comment says "roughly every 27–37 s" (`:481-482`), which is 5 × the measured 5.5–7.3 s tick (`:383-385`). The constant is 5 (`:491`) | MATCH as a citation (see Finding 2 for the record's wording) | read |
| 6 | `dashboard_manager.py:2497-2555` and `canopy_constants.py:425`: a restart strands the poll, and a 30 s watchdog releases it | The comment names "a canopy restart" (`:2504`). The `running=` guard is at `:4752`. In dash 4.2.0 (`JuniperCanopy1`), `handleError` (`dash_renderer.dev.js:987-998`) skips `completeJob` (`:925-932`). The watchdog runs on the 5 s slow lane (`:2549`, `canopy_constants.py:371`) with a 30000 ms threshold | Mechanism MATCH; "for up to 30 s" MISMATCH | Finding 1 |
| 7 | `websocket_manager.py:399`: `Client connected` is written for a page's `/ws/training` connect | INFO `Client connected: {label} (Total: N)`, written after the socket joins `active_connections` (`:380-381`), so the page can already receive broadcasts. The label is `training-client-<id>` for `/ws/training` (`main.py:850`) and `control-client-<id>` for `/ws/control` (`:985`). The A-N2 log shows both with millisecond timestamps (`juniper-canopy.log:56-59`) | MATCH | read |
| 8 | The burst lands about 5 s after `Cascor metrics stream connected` | Canopy logs the line right after `stream.connect()` (`cascor_service_adapter.py:661-662`). The client sends nothing on connect (`ws_client.py:335-353`). Cascor waits 5.0 s for a `resume` frame (`training_stream.py:60-79`, `:281`; `settings.py:51`), then sends state and the burst (`:285-300`). The A-N2 log gap is 30.768 → 35.770 | MATCH | read |
| 9 | `websocket_client.js:162-171`: jittered backoff | `random × min(60 s, 0.5 s × 2^min(n,7))`. The `/ws/training` client is `window.cascorWS` (`:569-570`) | MATCH | read |
| 10 | "nothing re-sends the burst"; canopy's own `/ws/training` sends no `initial_metrics` | The handler sends `initial_status` and `state` only, and ignores the browser's `subscribe_metrics` (`main.py:866-896`; client `:107-116`). No canopy server code emits `initial_metrics`. The relay broadcasts once, to the sockets open at that moment (`websocket_manager.py:700-712`, adapter `:780`). Neither the relay nor the client asks cascor to re-send | MATCH | `git grep` |
| 11 | The Sliding Window page "can hold the burst's rows that long for a reason of its own" | On an idle cascor only the poll replaces the window store after 5 s of quiet (`:7877`), and a stranded poll cannot. Modelled hold after the burst: about 16-33 s | MATCH | `strand_window.py` |
| 12 | The swap branches: a page keeps cascor's history unless it fetched after the fit; one that took the point is redrawn by its first cascor fetch, usually after the burst, up to about half a minute | Follows from rows 3-5 and `:7941`. The burst comes about 5 s after the swap, so the first fetch lands after it with probability ≈ 1 − 5/(27-37) ≈ 0.8. The zeros then last up to about 22-32 s | MATCH | read; arithmetic |
| 13 | Mid-run case attributed to "(Lanes 10-R3A and 10-R3B)"; round 3's record says "both lanes" | R3:57-66 (R3A's Finding 1) and R3:158 (R3B's Finding 1) | MATCH | read |
| 14 | Round 3's record on the hidden marker: Lane 10-R3A by unmixing; Lane 10-R3B by draw order, holding that the capture "neither shows nor excludes it" | R3:68-79; R3:183 and :189; corrected per R4:129-136 | MATCH | read |
| 15 | Round-4 record: lanes, date, brief and report paths; R4A's replay, counts and unmixing; the verdicts; R4B's Finding 2 changes an action | R4:5, :11, :25-26, :41, :54, :76, :127. Both paths are tracked at `b2375a51`. My own replay of round 3's pass on `0d3c337b` gives `b5cb675d` byte for byte (19 SUBS, 4 SPANS, 841,097 → 849,551) | MATCH | read; replay |
| 16 | Round-4 record: what changed and who found it | R4:107-137 (R4B's Findings 1-3). R4:52 is R4A's condition. R4A also noted both round-3 attribution points (R4:49-50) without a finding; leaving it out is an omission, not an error | MATCH | read |
| 17 | The record's quotes of round 3's reading, and that it was the orchestrator's | They match `b5cb675d`'s removed text, "(the orchestrator's reading)" | MATCH | diff |
| 18 | Reconnect odds 0.8 / 0.6 / 0.4, listed as not re-derived | Quoted exactly from R4:123. My own model gives 0.82 / 0.63 / 0.39 for one page, and 0.67 / 0.40 / 0.16 for two | MATCH | `reconnect_odds.py` |
| 19 | The "Re-derived by the orchestrator" list | Each item checks out (rows 3, 4, 6, 7, 10), except "the full-history cadence canopy measured" | One MISMATCH | Finding 2 |
| 20 | "Rounds 2 to 4 added `phase10_ledger_round{2,3,4}_corrections.py`"; "Slips: none reported" | All three are tracked at `b2375a51` with the `2026-10-04_` prefix. R4:67 and :150 both say none | MATCH | `ls-tree`; read |

**FINDINGS**

1. **MINOR: the strand's "up to 30 s" is close to a minimum, not a maximum, and a short restart may strand no poll.**
   - **Ledger text:** item 18 says "A restart also strands each page's metrics poll for up to 30 s (`dashboard_manager.py:2497-2555`, `canopy_constants.py:425`)". The round-4 record repeats "for up to 30 s".
   - **Evidence:**
     - The watchdog starts its clock at the first 5 s slow-lane tick that sees the poll disabled. It re-enables only on a later tick with `now - since >= 30000` (`dashboard_manager.py:2536-2545`, `:2549`; `canopy_constants.py:371`, `:425`).
     - So a strand normally lasts 30-35 s from its onset, or up to 40 s if the sixth tick reads just under 30,000 ms.
     - A poll is stranded only if one of its requests fails while canopy is down. At the measured ~5.5-7.3 s request cadence (`canopy_constants.py:383-385`), a ~4 s outage leaves about 0.37 of pages unstranded in my model.
     - Measured from the burst, the hold is about 16-33 s, so "that long" for the hold is roughly right. The strand's own bound is in the wrong direction, and an operator who sees a 31-37 s hold could wrongly rule out the strand.
   - **Fix:** "A restart can also strand a page's metrics poll for about 30 s (the watchdog's 30 s, counted from a 5 s slow tick; `dashboard_manager.py:2497-2555`, `canopy_constants.py:425`)". In the record: "for about 30 s".
   - **Changes a number, disposition or action?** No.

2. **NIT: the round-4 record says canopy measured the full-history cadence. Canopy derived it.**
   - **Ledger text:** "the full-history cadence canopy measured and records in its own constants".
   - **Evidence:**
     - Canopy measured the poll's tick, 5.5–7.3 s, on a completed fixture (`canopy_constants.py:383-385`, `:399-401`), and multiplied it by 5 (`:480-482`).
     - Its comment then says a full fetch lengthens the round trip and "no one has measured a full-mode round trip" (`:486-488`).
     - The body's "~27-37 s (`canopy_constants.py:476-491`)" is an accurate citation of canopy's figure.
   - **Fix:** "the full-history cadence canopy derives from its measured poll cadence and records in its own constants".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live, by rule. Persistence after W8 step 13, the strand, the reconnect timing and the full-mode cadence are all source readings or models.
- "That is the usual case" after W8 step 13 depends on how soon after the fit ends step 13 is clicked. Canopy refuses the switch until the fit ends (`main.py:4092-4097`), and the matrix has nothing between steps 12 and 13, but no run has measured that pace. R4B's word was "a likely case".
- The strand rests on dash 4.2.0 as installed in `JuniperCanopy1`. I did not confirm the stack's browser loads that renderer, or measure whether background-tab timer throttling stretches the 1 s and 5 s lanes.
- I did not judge whether a ~30 s hold on the Sliding Window page after a restart should count toward F-CANOPY-067's rating. The Severity bullet still calls the idle Sliding Window case transient by source, which is true for the swap and socket-loss triggers but not for a stranded restart. That is R5B's question.
- The `Client connected` line also fires for `/ws/control` (`control-client-…`). The instruction works only if the operator reads the `training-client-` lines. That is not a finding, because the line is written for `/ws/training`.
- I could not check that the round-4 reports were archived verbatim, or when the orchestrator's re-derivations were done. I did not read deployed overrides of cascor's resume timeout or burst size.

**SECRETS/PII:** No environment variables, tokens, credentials or e-mail addresses were printed or sent.
- **Git:** only `diff` (once with `--name-status`, which prints file names), `show <rev>:<path>`, `ls-tree`, `ls-files -s`, `cat-file -t`, `rev-parse`, `status --short` and `grep`. No `git log`, no `git show --stat`, no REST commit objects, no `gh`.
- **Services:** none touched, no port touched.
- **Scratch:** all work, including the scripts `replay.py`, `replay_r3.py`, `reconnect_odds.py` and `strand_window.py`, is in the `mktemp -d` directory `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/r5a.AR4GdM`.
- **Changed:** none. HEAD stayed at `b2375a51`.
- **Observed:** the untracked `util/ad-hoc/2026-10-05_memory_index_compaction.py` and this round's brief were already in the worktree. This lane did not write them.
- **Slips:** none.

---

## Lane 10-R5B - round 5, adversarial on the corrections

*agent `a37f77bc34411c88f` · round 1 · last-assistant-text (not resumed) · 10587 chars*

**VERDICT: SOUND-WITH-FIXES.** Round 4's new statements re-derive at canopy `1b2dd438`, and every line reference it added is right. The restart-drive check would catch a page that reconnects late. There is one MINOR overclaim and two NITs. None of them changes a number, disposition or action, so this lane gives no reason under §4 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` for a round 6.

Abbreviations:
- **L** = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `b2375a51`.
- **R4** = `reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round4.md`.
- **R3** = `…/2026-10-04_validator_reports_phase10_round3.md`.
- **A-N2 log** = `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/00_stack/logs/juniper-canopy.log`.
- Canopy source is read at `1b2dd438`.

**CLAIMS ATTACKED THAT SURVIVED**
- **Line references.** All seven cited ranges match: `recurrence_backend.py:312-315`, `dashboard_manager.py:7910-7912` and `:2497-2555`, `canopy_constants.py:425` and `:476-491`, `websocket_manager.py:399`, `websocket_client.js:162-171`.
- **The failed-fit branch.** `start_training` clears `_result` before each fit (`recurrence_backend.py:206`), and a failure leaves it unset (`:221-232`), so a failed fit also answers `[]`. Canopy refuses the swap while the fit runs (`main.py:4092-4097`), so W8 step 13 always follows a fit that landed or failed. "Until an LMU fit lands" covers both.
- **The branch where the page took the fit's point.** The fit's single point differs from cascor's history, so the first cascor fetch replaces the store (`:7944`) and the figure redraws (the store is an Input, `metrics_panel.py:970-972`). The burst lands about 5 s after the swap, and that fetch can land anywhere in a ~27-37 s cycle. So "usually after the burst" and "up to about half a minute" both hold.
- **No contradiction.** The new swap text does not contradict the Severity bullet's other sub-bullets or item 18. The clicking page re-mounts in Sliding Window, so "a Full History page" is the other page. Item 18's revised reason for the idle restart matches this branch. The P1-by-source prediction holds in every branch.
- **The log lines.** `Client connected` is logged at INFO after the socket joins `active_connections` (`websocket_manager.py:381`, `:399`). `/ws/training` passes `training-client-<id>` (`main.py:850-855`), and the A-N2 log has the line (`:56-57`). Canopy logs the relay's connect as `Cascor metrics stream connected to <url>` (`cascor_service_adapter.py:662`; A-N2 log `:35`). The initial frames followed 5.002 s later (A-N2 log `:37`).
- **The check catches a late page.**
  - The relay broadcasts once, to the connections open at that moment (`websocket_manager.py:699-712`).
  - The bridge's `initial_metrics` handler is registered on the training socket only (`ws_dash_bridge.js:261-274`).
  - On reconnect a page sends `resume` and `subscribe_metrics` (`websocket_client.js:87-116`). Canopy's `/ws/training` ignores both (`main.py:891-896`) and sends only `initial_status` and `state` (`:866-875`). So "nothing re-sends the burst" holds.
  - A sequence gap after a restart only logs a warning (`websocket_client.js:239-246`), so the new process's frames are not dropped.
  - Once the check passes, the Full History page detects persisting zeros whether or not its poll is stranded, because its fetch equals the store whenever it runs.
- **The strand.** The mechanism is right.
  - In the installed dash 4.2.0, `handleError` (`dash_renderer.dev.js:987-998`) never calls `completeJob` (`:925-937`).
  - The metrics poll carries `running=` (`dashboard_manager.py:4752`); the WS append does not (`:4779-4785`).
  - The watchdog checks on the 5 s slow lane against a 30 s threshold (`:2527-2555`, `canopy_constants.py:371`, `:425`).
  - Two qualifications. A strand needs a poll request to fail during the downtime, which is likely but not certain for a short restart. And 30 s is the watchdog's minimum, so a strand lasts about 30-35 s from when the watchdog first sees it. Counted from the burst, the Sliding Window page holds the rows about 20-30 s, so "up to 30 s" and "that long" are fair approximations.
- **"For a reason of its own."** This is true on the idle restart.
  - Mid-run, the poll is skipped while `metrics` frames flow (`:7877`), stranded or not. The strand adds hold time only across a pause of 5 s or more, such as a candidate phase: only `metrics` and `initial_metrics` stamp the liveness clock (`ws_dash_bridge.js:253`, `:273`). "Can" keeps the sentence true.
  - The Severity bullet's "transient" idle Sliding Window case stays unqualified for a canopy restart. That is an omission, not a finding.
- **Round 4's record.** It matches R4:
  - R4A: SOUND, a byte-for-byte replay, the counts and the unmixing (R4:11, :25-26, :40-41, :54), and the empty-store condition (R4:52).
  - R4B: only its Finding 2 changes an action (R4:116, :127, :137).
  - The reconnect odds (R4:123) are recorded as not re-derived.
  - R4A also noted both round-3 attribution points but judged them not to be errors (R4:49-50), so crediting the correction to R4B alone is fair.
- **Round 3's corrected attributions are now true.** Both lanes reported the mid-run case (R3:57-66, R3:158). R3B held that the capture "neither shows nor excludes" the marker (R3:189), and only R3A's pixels show it (R3:72-75).
- **Side checks.** The pass's `apply()`, run on `b5cb675d`'s ledger, gives `b2375a51`'s byte for byte (853,825 chars; 7 substitutions, 1 span). The triage on a copy gives 78/53/1/2/22, with 6 open P1, 16 open P2 and no P0.

**FINDINGS**

1. **MINOR — "the usual case" overclaims. Indefinite persistence after W8 step 13 also needs the Full History page to have fetched the end of the run before the switch to LMU.**
   - **Ledger text:** L:10201, "After W8 step 13 that is the usual case (round 4, Lane 10-R4B; re-derived by the orchestrator)", with L:10203-10205. The record repeats it at L:10415-10416: "…unless it fetched after the fit landed, so its first fetch after the swap is equal and the zeros persist".
   - **Evidence:**
     - In Full History the WS append opts out (`dashboard_manager.py:7827-7828`). The poll fetches only on every 5th tick (`:7883-7884`), about every 27-37 s (`canopy_constants.py:476-491`), and does so during a run as well (`:7877`).
     - Only user changes write the display-mode store (`metrics_panel.py:1352-1367`), so nothing refreshes the store when a run ends. It lags the run's end by up to one cycle.
     - W8 can start at once, because canopy refuses a switch only while training (`main.py:4092-4097`).
     - So a W8 begun within that cycle carries the stale history through the LMU steps (`:7910-7912`). After step 13 the first cascor fetch differs, `:7941` does not suppress it, and `:7944` redraws the chart. That is the outcome of the branch where the page took the fit's point.
     - Operator speed works against both conditions at once. A fast start leaves the store stale; a slow step 13 lets the page take the fit's point. R4B called it "a likely case" and tied it to step 13's timing (R4:77, :113); "usual" was added by the correction pass.
   - **Narrowest true fix:**
     - At L:10201, replace "that is the usual case" with "that holds when the page fetched after the run ended and not after the fit landed".
     - At L:10205-10206, write "A page that did take the fit's single point, or whose store missed the run's last rows, is redrawn by its first fetch from cascor, …".
     - In the record (L:10415-10416), write "unless it fetched after the fit landed or missed the run's last rows".
     - Optionally, add to item 18: "start W8 one full-fetch cycle (~40 s) after the run ends, or set the second page to Full History after the run, which fetches at once". That one would be an action change.
   - **Changes a number/disposition/action?** No. In every branch the zeros still last at least until the first cascor fetch, up to about half a minute, and indefinitely if that fetch lands before the burst. The drives and the P1-by-source prediction stand.

2. **NIT — "the full-history cadence canopy measured".**
   - **Ledger text:** L:10430.
   - **Evidence:** Canopy measured the per-tick gap: medians of 5.5, 6.1 and 7.3 s, on a completed fixture (`canopy_constants.py:380-385`, `:399-401`). The ~27-37 s is its arithmetic at N = 5 (`:481-482`), and the same comment says "no one has measured a full-mode round trip" (`:488`).
   - **Fix:** "the full-history cadence canopy derives in its own constants from its measured tick".
   - **Changes a number/disposition/action?** No.

3. **NIT — the `Client connected` line is also written for each page's `/ws/control` socket.**
   - **Ledger text:** L:10477-10478, "every page's `/ws/training` connect (`Client connected`, …)".
   - **Evidence:** Every endpoint goes through the same `connect()` (`websocket_manager.py:347-349`), and `/ws/control` logs `control-client-<id>` (`main.py:985-990`). So two pages write four such lines; the A-N2 log has one pair per page load (`:56-59`). A count of these lines before the burst can pass with only one page's training socket connected, which is the case the check exists to catch.
   - **Fix:** "(`Client connected: training-client-…`, …)".
   - **Changes a number/disposition/action?** No.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live, by rule. Every runtime conclusion comes from source at the pins and the A-N2 log.
- How much the Full History store lags at a run's end in a real drive, and the operator's timing in item 18's W8 drive, which decides which branch is the common one.
- Whether the isolated stack's canopy serves the dash 4.2.0 renderer I read in JuniperCanopy1.
- Whether a real restart's downtime always strands the poll.
- R4B's model of the reconnect odds, and any deployed overrides of the burst size or the handshake timeout.

**SECRETS/PII:** No environment variables, tokens, credentials or e-mail addresses were printed or sent, and the A-N2 log lines I printed hold none.
- **Git:** only `show <rev>:<path>`, the brief's `diff`, `ls-tree -r --name-only` and `grep`. No `git log`, no `--stat`, no REST commit objects, no `gh`.
- **Services:** none touched, and no port.
- **Files:** I read the installed dash renderer under `/opt/miniforge3` without changing it. All work is in the `mktemp -d` directory `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/r5b.JEQcdx`.
- **Changed:** none.
- **Slips:** none.

---
