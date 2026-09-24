<!-- markdownlint-disable -->

# The canopy follow-up to #676 (round 3's unapplied fixes) -- review rounds 1 to 8

Verbatim final reports of the lanes that reviewed juniper-canopy branch fix/idle-cuts-round3-wording before it was opened as a PR, 2026-09-24. Lane C (round 1) reviewed local commit 89dc8be0; each later lane reviewed only the previous round's corrections: C2 89dc8be0..15bd8135, C3 15bd8135..2f2bc203, C4 2f2bc203..9935b857, C5 9935b857..b07943d6, C6 b07943d6..511f8da8, C7 511f8da8..e455af03, and C8 e455af03..26bf27b3 plus a final sweep. Round 8 found nothing false and returned MERGE, which ends the review under section 4 of notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md; 26bf27b3 is the commit that opens as the PR. Each lane is a separate agent, so each report is that agent's last text. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneC*_canopy_followup_brief.md. The juniper-ml E2E evidence ledger (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9, Still owed item 13) records the follow-up.

## Lane C -- round 1, adversarial, on 89dc8be0

*agent `acdb770555b4244be` · round 1 · last-assistant-text (not resumed) · 11270 chars*

**VERDICT: MERGE-WITH-FIXES.** The code and tests hold. The runtime source is unchanged, all 12 tests pass, and each of the four guard mutants fails exactly one test. The fixes are wording: in the gate comment, the commit body (which becomes the squash body) and the CHANGELOG entry, plus one test to add. Survivors outside the five files can be fixed here or recorded as owed.

**FINDINGS**

1. **MINOR: "until the page reloads" is false on a reachable path.**
   - The text, in three places:
     - `replay_player_panel.py:76-77`: "Only a started replay writes one, and against cascor a Stop does not clear it (F-CANOPY-056), so the drain runs from this page's first replay until the page reloads."
     - The commit body: "so the drain runs from the page's first replay until it reloads."
     - `CHANGELOG.md:187-188`: the same sentence.
   - A successful model select clears the session without a reload:
     - `_select_model_handler` returns `data.get("execution", "live")` on every successful select, even when the model is unchanged (`dashboard_manager.py:3480-3482`, `:3538-3540`). It writes `model-class-store` (`:2794`).
     - `suppress_cascade_tabs` (`:2735-2742`) then rebuilds all of `visualization-tabs.children` (`:1878`), including the Replay tab (`:2603-2607`).
     - The file's own F-CANOPY-027 note (`:2725-2730`, `:3553-3555`) says a same-value write rebuilds the bar and resets the pollers' `disabled`.
     - My probe of `_visible_tabs("live")` and `_visible_tabs("one_shot")` on the head extract: `replay-player-session {'data': None}`, `weight-drain {'disabled': True, 'interval': 500}`.
   - So after a Stop, selecting any model turns the drain off and returns the player to idle.
   - The same overstatement predates this commit, in #676's text: `replay_player_panel.py:580`, `CHANGELOG.md:158` ("as it always ran before" no longer holds after a rebuild), and F-CANOPY-056's title in the local ledger (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:8805`).
   - **Fix:** "until the page reloads, or a model select rebuilds the tab bar". **Changes a number:** no. **Disposition:** no. **Action:** yes, reword before the squash body lands.

2. **MINOR: survivors outside the five files state the same false things.** The commit's own reason for fixing `replay_forward.py` ("it carried the claim #676 corrected") covers these too:
   - `docs/USER_MANUAL.md:764`: "Weight samples streamed during playback are drained every 500 ms into the buffer…"
   - `notes/development/REPLAY_V2_FAQ.md`:
     - `:135-137` "The replay session emits a `weights` block on its synthetic `epoch_end` event".
     - `:267-269` "g-3 … produces the `weights` blocks the canopy buffer consumes". This is exactly the `replay_forward.py` claim.
     - `:188` "During Stop / new Replay: buffer is cleared". Nothing clears it: the drain is the only writer of `replay-weight-buffer.data` (`/_dash-dependencies`).
     - `:193-195` "Drain Interval fires every 500 ms … Negligible CPU". The drain is now gated, and #676's A/B measured it at a 32–42% latency cost.
     - `:222` "you should see updates every 50 metric events"; `:253-255`.
   - **Changes a number:** no. **Disposition:** no. **Action:** yes, extend the sweep or record these as owed.

3. **MINOR: the CLASS guard's positive path has no test at head.**
   - Mutant m7 (`_dead_intervals` → `return []`): **12 passed.**
   - The refactor added synthetic tests for the two refusals only. Nothing asserts that the helper actually reports a dead Interval, so a regression there makes the CI guard vacuous.
   - Against #676's parent `05f2dfc2` it does still fail correctly: the head test file gives 7 failed, 5 passed, naming exactly `['metrics-panel-update-interval']`.
   - **Fix:** add `assert _dead_intervals([], [{"id": "x"}]) == ["x"]`, plus a consumed case. **Changes a number:** no. **Disposition:** no. **Action:** yes.

4. **NIT: the test docstring's falsification sentence is wrong for one of the three REFUSAL tests.**
   - Text (`test_idle_dispatch_cuts.py:42-44`): "The three REFUSAL tests … are falsified by reverting that check to bare `p["id"]` lookups".
   - Mutant m9 restored `e9053227`'s form (bare lookups, set comprehension, round 2's pattern refusal kept): **2 failed** (no-id, siblings), 10 passed.
   - `test_a_pattern_matching_id_is_refused` passes against it, because round 2's refusal already used bare lookups. Only dropping that refusal fails it (m2).
   - **Changes a number:** yes, 3 → 2 in the docstring. **Action:** reword.

5. **NIT: "the 16 suites that read the touched files, 342 passed" does not reproduce.**
   - The 16 suites that name a touched file (`grep -rlE "replay_player_panel|ReplayPlayerPanel|ws_dash_bridge|replay_forward|CHANGELOG|test_idle_dispatch_cuts" tests/`) give **347 passed** (collected 347 from both `src/` and the repo root).
   - 347 − 342 = 5, which is exactly the size of `tests/ui/test_ws_silent_poll_liveness.py`, the only browser-level exercise of `ws_dash_bridge.js`.
   - **Changes a number:** yes, in the squash body. **Fix:** name the suites and state 347, or name what was excluded.

6. **NIT: "this commit applies the rest of round 3" overclaims.**
   - Round 3's finding 2 (in `2026-09-23_validator_reports_phase9_round3.md`) was #676's stale PR body. It is not fixed: `gh pr view 676 --json body` still shows "answered a third slower", "`main` `3a6dea95`" and "all seven files".
   - The local ledger (`…E2E-VALIDATION-EVIDENCE.md`, Phase 9) still lists it as owed.
   - **Changes an action:** yes. Edit the PR body, or reword to "applies round 3's in-tree findings (3, 6, and 4's docstring half)".

7. **NIT (process): the Phase 9 citation dangles.**
   - The commit body says "The juniper-ml E2E evidence ledger (Phase 9) records that correction". `CHANGELOG.md:184-185` says "has the record (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 9)".
   - Phase 9 exists only in the unpushed local `e624c281`: `git branch -r --contains e624c281` is empty.
   - On `origin/main` (`f9c81d80`) that ledger ends at Phase 8 (`:7865`), and its highest ID is F-CANOPY-055.
   - **Changes an action:** yes, as a merge-order precondition: the ledger lands first.

8. **NIT: the CHANGELOG misdescribes the old text.**
   - `CHANGELOG.md:180` quotes "while a replay session exists" as comment text. At `e9053227` that phrase was only in a test assertion message (`test_idle_dispatch_cuts.py:138`). The comment said "disabled unless a replay session exists".
   - `:186` "the gate comment now says what the gate keys on, a truthy `snapshot_id`". The old comment already said "meaning the session Store holds a truthy ``snapshot_id``" (`e9053227` `replay_player_panel.py:75-76`).
   - **Changes a number, disposition or action:** no.

**CLAIMS YOU TRIED AND COULD NOT REFUTE**

- **"Only a started replay writes one."** The built app's `/_dash-dependencies` lists exactly two writers of `replay-player-session.data`. Both are server-side `allow_duplicate` callbacks:
  - `confirm_snapshot_op` (`hdf5_snapshots_panel.py:1265-1326`) writes only on `operation=="replay"` and HTTP 200. Canopy's route returns 200 only after the adapter call succeeds; demo mode returns 501 (`main.py:2970-3007`).
  - `dispatch_control` (`replay_player_panel.py:669-691`) refuses without a truthy id. `_merge_session` overlays the envelope, which has no top-level `snapshot_id`. It rewrites only the id it was given.
  - There is no `set_props` writer. The only `set_props` calls in `assets/`, `dashboard_manager.py` and `snapshot_context_menu.js:131` target other stores, and no Python `set_props` exists.
- **Stop does not clear the session against cascor.** Confirmed from source (`_merge_session` `:852-857`; adapter `:2379`). The Store uses memory storage, so a reload does clear it.
- **"No emitter attaches one today" and "no live input yet."**
  - Cascor `_ReplaySession._emit_frame` (`manager.py:1198-1234` at `0e016a7c`) adds no `weights` key, and `weights_at` has no caller in `src/`.
  - Canopy's relay rebuilds metrics from fixed keys (`cascor_service_adapter.py:763-764`, `:1942-1972`). Demo metrics have no `weights` key (`demo_mode.py:1589-1619`). The browser connects only to canopy's `/ws/training` (`websocket_client.js:569`).
  - The drain is the only writer of `replay-weight-buffer`.
- **Census figure (3.0 of 6.6, 45%).** I recomputed it: #676's parent `05f2dfc2` and the census tree `c0530279` both have the same 18 Intervals at 6.6 ticks/s. `c0530279` is F-054's branch commit and not an ancestor of `e9053227`, but its Interval layout is identical, so the figure transfers. Head has 17 Intervals at 3.6/s.
- **Tests.**
  - The file: 12 passed; the RULE test ran under node v24.13.1 (not skipped).
  - m1 (drop no-id refusal): the no-id test fails.
  - m2 (drop pattern refusal): the pattern test fails.
  - m3 (`_interval_ids` → `p["id"]`): the sibling test fails, KeyError.
  - m4 (`_with_id` → `p["id"]`): the sibling test fails, KeyError.
  - Extra mutants: m5 (set comprehension) fails with TypeError; m6 (refusal order swapped) fails; m8 (gate `!(session)`) fails the RULE test.
  - The sibling test does depend on Dash not auto-assigning ids. In Dash 4.2.0, ids are assigned only when a component object is passed to a dependency (`dash/dependencies.py:49-50`), so this is stable. If Dash changed that, the test would fail loudly.
- **No runtime change.** `replay_player_panel.py`'s AST is identical, `replay_forward.py`'s is identical apart from the docstring, all 19 changed JS lines are `//` comments, and `node --check` passes.
- **Symbol-loss waiver.** The trailer is the last paragraph and parses with `%(trailers:key=Allow-Symbol-Loss)`. Both the 0.8.0 binary and 0.9.0 from source report "WAIVED 2, fail=0", with 11 → 6 lines as stated. The docs screen has 0 findings.
- **Pinned pre-commit** is clean (run in a throwaway repo).
- **History.** The #676 timeline (convert_to_draft 19:44:37, ready 22:28:04, auto-squash 22:28:12, merged 01:38:02Z), "two rounds; prose corrections only" in `e9053227`, round 1's `key=str` change (`8990f65c`→`c360fb53`), the entry's placement directly below #676's, and remote `main` still at `e9053227`.

**WHAT I COULD NOT CHECK**

- Finding 1 live: I did not drive a browser, so the rebuild path is established from source and the layout probe only.
- CI on the eventual signed commit. `89dc8be0` is unsigned (`%G?`=N).
- How GitHub will reformat the squash trailer. The screens read the trailer by regex, so a split is expected to be harmless.
- Dash 4.4.1, the locked version, for the id-less behaviour.
- Whether node is present on CI runners.

**SECRETS/PII:** No environment variables, tokens or credentials printed or sent. The commit's author email appeared in local git output only.

One slip against the hard rules: running `tests/ui/test_ws_silent_poll_liveness.py` let its session fixture (`src/tests/ui/conftest.py`) boot a demo-mode canopy (`src/main.py`) and headless chromium from my scratch extract. It used an ephemeral port (range 32768–60999), so none of :8051, :8101, :8202 or :805x was touched. The fixture terminated them, and I confirmed no leftover process.

No repo was changed. Scratch work is in `…/scratchpad/laneC_r3fix.JuqKSY/`.

---

## Lane C2 -- round 2, adversarial, on the corrections 89dc8be0..15bd8135

*agent `a379763f6f0ae1ce5` · round 1 · last-assistant-text (not resumed) · 10045 chars*

**VERDICT: MERGE-WITH-FIXES.** Every mechanism the corrections added holds up in source and in the installed renderer. The mutation claim and the counts reproduce. Two statements need settling before this message becomes `main`'s squash body: finding 1 is false today, and finding 2 is a wrong attribution the fix pass introduced. Line numbers are at `15bd8135` unless noted. The ledger is the WIP `acf1a93a` on `docs/canopy-e2e-phase9`, which moved from `e624c281` while I worked.

**FINDINGS**

1. **MINOR: "Its finding 2, #676's PR description, is refreshed on the PR itself."** (commit message)
   - **Not done.** `gh api repos/pcalnon/juniper-canopy/pulls/676` returns `merged_at 2026-09-24T01:38:02Z` and `updated_at 2026-09-24T01:38:03Z`, so there has been no edit since the merge.
   - **The body still carries round 3's stale text:**
     - line 3: "answered a third slower than it had to";
     - line 14: "Against cascor the drain then runs until the page reloads, as it always ran before" (the same claim this commit corrects);
     - line 64: "Pre-commit is clean on all seven files";
     - line 98: "Round 3 … : running."
   - **The ledger agrees it is owed.** `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` lists it as "Still owed" (`:8713-8714`, `:9142`).
   - **Fix:** refresh the body before this merges, adding the model-select path to line 14. `gh pr edit` is broken on gh 2.46.0, so use `gh api -X PATCH`. Or reword to "is owed as an edit of the PR".
   - **Changes an action:** yes, a merge precondition like round 1's #7. Number: no. Disposition: no.

2. **MINOR: "The four CHECK tests came later, from round 3 of #676's review."** (`test_idle_dispatch_cuts.py:43-44`)
   - Only three came from round 3. Round 3's finding 6 (`2026-09-23_validator_reports_phase9_round3.md`) covers only the refusal and lookup fragility.
   - The fourth test, `test_an_unconsumed_interval_is_reported_and_a_consumed_one_is_not` (`:168-170`), answers this change's own round-1 finding 3.
   - The fix pass turned `89dc8be0`'s accurate "three REFUSAL tests … from round 3" into "four" without moving the provenance.
   - **Fix:** "three from round 3 of #676's review, the fourth from this change's review".
   - **Changes a number:** yes (the attributed count). Disposition and action: no.

3. **MINOR: a survivor in `docs/USER_MANUAL.md:669-670`.**
   - Quote: "Weight norms — per-unit weight-norm traces, revealed only while a snapshot replay streams weight samples".
   - It is the same claim as the corrected `:764`, reworded, so the "streamed during playback" grep misses it.
   - It matters because the ledger rates F-CANOPY-057 P2 "because the canopy follow-up corrects the docs that promised the stream … Until that merges, the manual documents a behaviour that does not exist" (`:8933-8935`).
   - **Fix:** append "; none do today (see Replay Tab)".
   - **Changes a disposition:** possibly, the ledger's P2 rationale. Number: no. Action: a one-line edit.

4. **MINOR (test gap): the check's own criterion is unpinned.** I ran mutants through a scratch harness, 13 tests each:
   - **The claimed set.** Each claimed mutant fails exactly one of the four new tests and nothing else (1/13):
     - drop the no-id refusal;
     - drop the pattern refusal;
     - revert `_interval_ids` (as a list or as the old set);
     - revert `_with_id`;
     - make the check `return []` or `return None`.
   - **Survivors.** These pass 13/13:
     - `_consumers` ignoring `property`;
     - `_consumers` also counting `state`;
     - the check reporting only the first dead Interval.
   - The module defines CLASS as "takes its `n_intervals` as an Input" (`:27-28`), and nothing tests that. It is latent today: all 17 built Intervals are consumed only through `n_intervals`, per my census of the built app.
   - **Fix:** add `{"id":"idle","property":"disabled"}` and a second dead id to the synthetic deps.
   - **Changes:** no.

5. **NIT: "those traces stay empty during a replay"** (`docs/USER_MANUAL.md:766`, and `notes/development/REPLAY_V2_FAQ.md:12-13`).
   - With an empty buffer, `network_evolution.py:185-186` returns `{"display": "none"}`. The whole "Replay weight evolution" section is hidden (`:94-96`), not empty.
   - **Fix:** "stay hidden". **Changes:** no.

6. **NIT: "Four new tests pin the check itself"** (`CHANGELOG.md`, commit message) and "mutants of the check … reverting either lookup helper" (docstring `:44-45`).
   - The sibling test pins `_interval_ids` and `_with_id`. `_dead_intervals` never calls them; they serve the wiring tests at `:154` and `:191`.
   - Three of the four tests pin the check. **Changes:** no.

7. **NIT: "applies round 3's in-tree findings (its 3 and 6, and the docstring half of 4)".**
   - Finding 4's other half also has an in-tree copy, still unapplied: `CHANGELOG.md:149-150` "A live check of this build against its parent … was less clear".
   - Round 3 said to name the SHAs (`ce78e0de` against `3a6dea95`).
   - **Changes:** no.

8. **NIT: the FAQ note says "the weight answers below describe the design, not what runs today". Some text contradicts it and the note does not cover it:**
   - `:4` "V2 ships";
   - `:58-63` "not yet wired to the buffer". g-7 wired both consumers (`decision_boundary.py:227-250`, `network_evolution.py:155-165`), so that answer describes neither the design nor today;
   - `:266` and `:268` (glossary) and `:280-282` ("g-3 … produces the `weights` blocks"), which are not "answers".
   - **Changes:** no.

9. **NIT: "a weight emitter that does not exist"** (title, `CHANGELOG.md` headline).
   - cascor#190, "emit weight payloads … (g-3)", merged 2026-05-03T20:05:12Z into `feature/can-015g-2-replay-weight-cache-v2`. That branch has diverged from `main`: 3 commits ahead, 512 behind (`gh api`).
   - So the emitter exists but never reached `main`, which is exactly what the cited ledger's F-CANOPY-057 History says.
   - **Changes:** no.

10. **NIT: #676's message on `main` has a third error this message does not list.**
    - #676's message on `main` (`e9053227`) also says "the drain runs until the page reloads, as it always ran before".
    - This message corrects #676's message on two counts but not this one. The ledger's "four statements" list (`:8704-8712`) omits it too.
    - **Changes:** no.

11. **NIT: "runs from this page's first replay until the page reloads, or until a successful model select…"** (`replay_player_panel.py:77-78`, `CHANGELOG.md:190-191`, commit message).
    - Once the model-select path exists, a later replay restarts the drain, so "first" describes only the first cycle.
    - **Changes:** no.

**CORRECTIONS I COULD NOT REFUTE**

- **The model-select path (round 1's #1).**
  - A successful select always writes `model-class-store` (`dashboard_manager.py:3482`).
  - The renderer re-triggers on every write, with no equality check (`dash_renderer.dev.js:2502-2505`).
  - `suppress_cascade_tabs` (`:2735-2742`) rebuilds through `_all_visualization_tabs` (`:2604`). That re-creates the session Store (`data=None`, serialised as explicit null), the buffer (`[]`) and the drain (`disabled=True`) at `replay_player_panel.py:124`, `:141` and `:146`.
  - `Store.react.js` adopts an explicit null whether React re-mounts or reuses the instance.
  - A new chunk re-runs the gate (`prevent_initial_call=False`, `:598`; `dash_renderer.dev.js:6966-6978`).
- **No other path clears the session or resets the drain.**
  - The model clear and the mount hydration both return `no_update` for the class store (`:3535`, `:3570`).
  - `hydrate_model_class` fires once, and before any replay (`max_intervals=1`, `:1971`).
  - No `set_props` in the assets writes these ids.
- **Counts.**
  - 13 passed.
  - The 16-file list reproduces exactly under the stated grep.
  - The 15 non-UI suites plus the panel snapshots give **345 passed**. The UI file defines 5 tests (`:266`, `:297`, `:332`, `:399`, `:425`), so 350 is consistent.
- **Pre-commit.** The pinned hooks are clean on all 7 files, run in a throwaway `git init` copy.
- **Symbol loss.** The screen reports 2 findings, both waived, exit 0. `git interpret-trailers` parses all three trailers.
- **Markdown.** The FAQ note renders as one blockquote holding a paragraph and a 4-item list. No table changed.
- **Staleness grep.** Only intentional quotes remain, plus the note-superseded FAQ `:208` and the "By design"-hedged manual `:764`.
- **Round 1's other findings are resolved as described:**
  - #2: the manual paragraph and the FAQ note were added.
  - #4: the docstring's mutation sentence is fixed and now matches the mutant runs.
  - #6: the round-3 scope sentence was reworded.
  - #8: "a comment and a test message" matches `e9053227:75` and `:138`.
- **"These three files are outside #676's":** true. #676 touched eight files (`git diff --stat 05f2dfc2 e9053227`).
- **FAQ note facts:**
  - cascor's `_emit_frame` sets no weights (`manager.py:1198-1234`).
  - canopy's `_to_dashboard_metric` rebuilds each payload without `weights`.
  - The drain is the only writer of the buffer, and the only thing that empties the JS ring (`ws_dash_bridge.js:125-128`).
  - The ledger records an in-page A/B at −41.9% and −32.3% (`:8322`, `:8329`).
- **Round 1's #7 still applies.** The ledger on juniper-ml `origin/main` (`f9c81d80`) mentions F-CANOPY-057 zero times, and the FAQ note adds two more citations of it.

**WHAT I COULD NOT CHECK**

- The 5 tests in `tests/ui/test_ws_silent_poll_liveness.py`, which the hard rules forbid running.
- The rebuild on a live page; I checked it in source and in the renderer only.
- Whether the renderer can drop a successful select's response when a newer request for the same callback supersedes it.
- CI on the commit, which is unpushed and unsigned.
- The follow-up's own round-1 report, which I did not find archived. I relied on the brief's summary for provenance.

**SECRETS/PII:** None printed or sent. The `gh` calls were reads only. No repository file changed; all scratch work is under `…/scratchpad/c2r2.8lkiNl/`.

---

## Lane C3 -- round 3, adversarial, on the corrections 15bd8135..2f2bc203

*agent `a06614151069df962` · round 1 · last-assistant-text (not resumed) · 8077 chars*

**VERDICT: MERGE-WITH-FIXES.** The code and tests hold up: 13 passed, 8 of 8 mutants caught, and the head test file gives 7 failed / 6 passed against the parent. The problems are in the text. The correction pass added one false mechanism and one false location to the squash body and the FAQ. It also generalised a test claim past what the test pins, and left round 2's finding 1 unanswered. Line numbers are at `2f2bc203`.

**FINDINGS**

1. **MINOR: the new g-3 mechanism is false.**
   - Text: "The g-3 emitter was merged only into a stacked cascor branch that never reached `main`" (`notes/development/REPLAY_V2_FAQ.md:11-12`). The commit message says the same: "The emitter was merged only into a stacked cascor branch that never reached main".
   - It was merged twice, according to `gh pr view --repo pcalnon/juniper-cascor`:
     - #187 went into `feature/can-015g-2-replay-weight-cache` at 07:31:04Z.
     - #190 went into `feature/can-015g-2-replay-weight-cache-v2` at 20:05:12Z.
   - That second branch did reach `main`. It was the head of #189 (base `main`), which merged at 19:52:10Z, 13 minutes earlier. Its squash `b1d19948` is an ancestor of cascor `0e016a7c` (`git merge-base --is-ancestor`).
   - The FAQ's own Related work names #190 (`:284`).
   - The cited ledger's History (`…E2E-VALIDATION-EVIDENCE.md:8922-8927`) says "merged twice" and "13 minutes after the branch's own PR, cascor#189, had landed". Its lead sentence carries the same "never reached `main`" slip.
   - The real class is "merged into a base that had already landed", which is what the ledger's fix direction says to sweep for.
   - **Fix:** "merged twice; the second time (cascor#190) 13 minutes after its base's own PR (#189) had landed on `main`, so it never reached `main`." Apply it in the note, the squash body and the ledger's lead sentence.
   - **Changes a number** (one branch becomes two merges) **and an action** (reword before the squash lands): yes.

2. **MINOR: "loosening what counts as a consumer" is not pinned.**
   - Text:
     - The docstring (`test_idle_dispatch_cuts.py:46-47`): "or loosening what counts as a consumer each fails one of them".
     - The CHANGELOG (`:208-211`): "only an `n_intervals` Input counts as a consumer … or loosens what counts as a consumer".
     - The commit message: "counts only an n_intervals Input as a consumer".
   - A `_consumers` mutant that also counts a callback writing the Interval as an Output gives **13 passed**. So does a substring id match.
   - The Output-writer loosening matters: my census of the built app found **15 of 17** Intervals have an Output writer (their `disabled`), so this loosening would leave the CLASS check blind to 15 of them.
   - **Fix:** add `{"inputs": [{"id": "x", "property": "data"}], "state": [], "output": "idle.disabled"}` to the synthetic deps. Verified: head still passes 13 of 13, and the mutant then fails only that test (`['idle_state'] == ['idle', 'idle_state']`). Alternatively, narrow the wording to "another property or a State".
   - **Changes an action:** yes.

3. **MINOR: round 2's finding 1 is unanswered.**
   - Text: "Its finding 2, #676's PR description, is refreshed on the PR itself."
   - `gh api …/pulls/676` shows `updated_at` 01:38:03Z, still the merge time.
   - The PR body still has, at line 14, "runs until the page reloads, as it always ran before". It also still has "all seven files" (:64) and "Round 3 … running" (:98).
   - The ledger lists it as still owed (`:9142`).
   - **Fix:** refresh the body with `gh api -X PATCH` before merging, or reword to "is owed".
   - **Changes an action** (a merge precondition): yes.

4. **NIT: the status note's location is wrong.**
   - The commit message says "a dated status note above its status line, answers and glossary". The note itself says "the status line … below" (`REPLAY_V2_FAQ.md:8`).
   - The only status line is at `:4`, above the note, which starts at `:8`.
   - The CHANGELOG's older wording, "above its answers" (`:203-204`), is the accurate one.
   - **Fix:** "the status line above, and the weight answers and glossary below"; in the message, "under its header".
   - **Changes an action** (reword the squash body): yes.

5. **NIT (process): the cited mutant script is not committed anywhere.**
   - The message cites `juniper-ml util/ad-hoc/2026-09-24_idle_cuts_check_mutants.py`.
   - It is untracked: `git log --all -- <path>` is empty, and it is not on juniper-ml `origin/main` (`f9c81d80`).
   - Its docstring promises "must fail exactly one test", but `:90` checks only that the named test fails. In this run each mutant did fail exactly one test.
   - **Changes an action:** yes. Land the script with the ledger before the canopy squash.

6. **NIT: the FAQ note still misses text round 2's finding 8 cited.**
   - Related work (`:284-286`, "g-3 … produces the `weights` blocks", and `:294-296`, "deferred … g-7") is not the status line, an answer or the glossary.
   - "An answer below" is singular. The not-yet-wired text at `:62-67` is not an answer, and `:79-82` and `:214-215` also say the rendering has not shipped.
   - **Changes:** no.

7. **NIT: the CHANGELOG list is now out of step with the message.** The CHANGELOG (`:185-187`) still lists two errors in #676's message, while the squash body now lists three. **Changes:** no.

**CORRECTIONS I COULD NOT REFUTE**
- **The positive-path test.**
  - 13 passed, and node ran the RULE test.
  - The mutant script, run against my extract, caught 8 of 8; each failed only its named test.
  - The head file on `05f2dfc2` gives 7 failed and 6 passed, so "7 of the original 9" and "not the parent" hold.
  - Dash serves the `state` key (dash 4.2.0).
- **The provenance sentence.**
  - `e9053227` had 9 tests, with the pattern refusal inline and no test of its own.
  - Three tests answer round 3's finding 6. The positive-path test answers the follow-up's round-1 finding 3.
- **"Once a replay starts."**
  - `suppress_cascade_tabs` has one Input, `model-class-store` (`dashboard_manager.py:2735-2740`).
  - That store has two writers, `:2717` (which returns `no_update` when unchanged) and `:2794`.
- **The USER_MANUAL fixes: "none do today" and "stay hidden".**
  - `network_evolution.py:185-186` returns `display: none` for an empty buffer.
  - The readout returns `""` (`replay_player_panel.py:607-613`).
- **"The consumers are wired (g-7)".**
  - `decision_boundary.py:235-250` and `network_evolution.py:159-169` read the buffer.
  - g-7 (`f4924108`, #222) landed after the FAQ commit `2b8ff236`, so "predates g-7" is true.
- **"Never reached cascor's `main`."** `_emit_frame` (cascor `0e016a7c`, `manager.py:1198-1236`) sets no weights, and `dbc25277` is 3 ahead and 512 behind `main`.
- **The in-place CHANGELOG edit.**
  - The parent of `ce78e0de` is `3a6dea95`.
  - Transcript `…_live_check_rebuilt_ce78e0de.json` alternates the two builds and reports LATENCY INCONSISTENT, with 5415.8 against 5336.9 and 5275.5 (+1.5% and +2.7%).
- **The commit message's other claims.**
  - Its quote of `e9053227`'s message is exact.
  - "Both halves of 4" matches round 3's report (`:47-50`).
  - The 16-file grep reproduces.
  - The 15 non-UI suites plus the panel layout snapshots give 345 passed.
  - "Records those corrections" holds (the ledger has it at `:9141`).
- **The screens.**
  - Pinned pre-commit is clean on all 5 changed files.
  - The symbol-loss screen (0.8.0, scope `src/**/*.py`) reports WAIVED 2, fail=0.
  - The docs screen reports 2 WARN and fail=0.

**WHAT I COULD NOT CHECK**
- The 5 `tests/ui` tests, which the rules forbid, so 350 is checked by count only.
- The model-select rebuild on a live page, including whether an evicted select response (the F-CANOPY-058 class) skips it.
- CI: the commit is unpushed and unsigned (`%G?`=N).
- Symbol-loss screen 0.9.x, the range CI pins.
- How GitHub reflows the squash body.

**SECRETS/PII:** None printed or sent. The `gh` calls were reads only. No repository was changed. Mutants and probes ran only inside `…/scratchpad/c3r3.d5ppVd/`, and no mutant files were left behind.

---

## Lane C4 -- round 4, adversarial, on the corrections 2f2bc203..9935b857

*agent `a852e379791ecd038` · round 1 · last-assistant-text (not resumed) · 10277 chars*

**VERDICT: MERGE-WITH-FIXES.** The code and test changes hold up. The test file gives 13 passed, and each of the ten mutants gives "1 failed, 12 passed". The non-UI suites give 345 passed. Both sequence-safety screens and pinned pre-commit are clean. Three things still need fixing before the squash body lands:
- Round 2's finding 1 is unanswered for the third round running.
- F-CANOPY-059 makes one sentence in the CHANGELOG bullet this change rewrote false today.
- This round widened the FAQ note's scope so that it now mislabels work that shipped.

Line numbers are at `9935b857` unless noted.

**FINDINGS**

1. **MINOR (NOT ANSWERED; round 2 #1 and round 3 #3).**
   - Text (commit message, lines 12-13): "Its finding 2, #676's PR description, is refreshed on the PR itself."
   - `gh api repos/pcalnon/juniper-canopy/pulls/676` gives `updated_at` 01:38:03Z, one second after `merged_at`. The body still says:
     - "answered a third slower" (line 3);
     - "runs until the page reloads, as it always ran before" (line 14);
     - "Round 3 … running" (line 98).
   - The ledger this message cites says the opposite. `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md:9345-9348` (Still owed item 13) and `…E2E-VALIDATION-EVIDENCE.md:8762-8764` both list the edit as owed and "not part of the follow-up".
   - `2026-09-24_validator_reports_phase9_canopy_followup.md:5` says round 3's findings "were applied as 9935b857". This one was not.
   - **Fix:** run the `gh api -X PATCH` first, or reword the sentence to "is owed as an edit of the PR".
   - **Changes an ACTION** (merge precondition): yes. Number: no. Disposition: no.

2. **MINOR (the F-CANOPY-059 cross-check).** One sentence is false today; the rest are only incomplete.
   - **The mechanism holds at 9935b857.** I executed it with a `registered_panel`-style app.
     - The session was built the way `confirm_snapshot_op` stores cascor's `/replay` data block (`hdf5_snapshots_panel.py:1316-1324`; cascor `routes/snapshots.py:449`, `manager.py:1165`).
     - `render_session` raises `KeyError(0)` at `replay_player_panel.py:534`, with `range_value` taken from `:508`. The ledger's `:505-506` and `:532` are `e9053227`'s lines; this change's longer comment shifts them by 2.
     - The same session with a list `range` renders the active view. A V2 session also raises.
     - In the built app's `/_dash-dependencies`, `render_session` is the only writer of `-active.style` and `-idle.style`. There is no `on_error` handler in `src/`.
     - The drain gate is a separate clientside callback (`:594-599`), so the drain still starts.
     - cascor's session starts paused (`manager.py:1076`) and emits only frame 0 (`:1244`) until a play arrives. Since Play is never on screen, a cascor replay never gets past its entry frame. The ledger's "while cascor replays" (`…E2E-VALIDATION-EVIDENCE.md:9095`) overstates this.
   - **FALSE:** `CHANGELOG.md:162-163`, "The player also keeps its session view."
     - Against cascor the player never shows a session view, before or after a Stop.
     - The sentence is #676's, but it sits in the bullet this change rewrote. The change's own entry says that bullet "is corrected in place" (`CHANGELOG.md:195`).
   - **INCOMPLETE:** each is true of `_merge_session`, but against cascor no Stop is ever on screen, so F-056 is masked.
     - message lines 17-18: "which a Stop against cascor does not clear";
     - `replay_player_panel.py:76-77` and `:580-581`: "keeps running after a Stop";
     - `CHANGELOG.md:160-161`, `:182` and `:192`;
     - `REPLAY_V2_FAQ.md:21-22`: "A Stop clears nothing … so the drain keeps running";
     - `REPLAY_V2_FAQ.md:15-16`: "`last sample` readout … stay[s] empty". The readout sits in the hidden active view (`replay_player_panel.py:203-211`), so it is not on screen at all;
     - `USER_MANUAL.md:763` (a context line): "Every control posts…".
   - **Still true:** "once a replay starts, the drain runs until the page reloads, or until a successful model select…", "those traces stay hidden", and "The drain starts only once…".
   - **Outside this diff:** `USER_MANUAL.md:753` ("until a replay is confirmed") is false; `test_idle_dispatch_cuts.py:19` is incomplete.
   - **Fix:**
     - Replace the `CHANGELOG.md:162-163` sentence with "Against cascor the player never shows a session (F-CANOPY-059), so no Stop is on screen."
     - Add an F-059 bullet to the FAQ note. The note is the dated "what runs today" record, and this is the fact a reader needs most.
   - **Changes an ACTION:** yes. Number: no. Disposition: no.

3. **NIT (new this round).**
   - Text (`REPLAY_V2_FAQ.md:8-9`): "…related-work notes and glossary below, describe the design, not what runs today."
   - Most of those related-work notes describe code that runs today:
     - g-1 `_load_weight_history`, g-2 `weights_available`, g-5a `SNAPSHOT_SCHEMA_V2.md` and g-6 `_WeightHistoryRecorder` are all on cascor `origin/main`;
     - g-4 (canopy #220) merged to canopy `main`.
   - Only the g-3 note (`:286-288`) and the g-7 note (`:296-298`) are stale.
   - **Fix:** "the g-3 and g-7 related-work notes".
   - **Changes:** no.

4. **NIT.** "loosening what counts as a consumer" (`test_idle_dispatch_cuts.py:47`, `CHANGELOG.md:213`) and "by exact id" (`test_idle_dispatch_cuts.py:170`, message line 45) claim more than the tests pin.
   - Swapping the id comparison in `_consumers` for `endswith` gives **13 passed**, and so does a case-insensitive comparison.
   - A `startswith` mutant is caught.
   - **Fix:** name the four loosenings, or narrow the wording.
   - **Changes:** no.

5. **NIT.** The message (lines 5-9) and `CHANGELOG.md:185-189` list three errors in #676's squash body. The ledger lists five (`…E2E-VALIDATION-EVIDENCE.md:8749-8760`).
   - The two missing are "against its parent" (`e9053227` message lines 21-22) and "half of the page's steady-state ticks" (lines 5-6).
   - Those two are round 3's finding 4 itself: "two loose claims in the squash body" (`2026-09-23_validator_reports_phase9_round3.md:47-50`).
   - The message says it applies "both halves of 4", but only their copies in the tree were fixed.
   - **Changes:** no.

6. **NIT.** The census wording dropped "steady-state".
   - At `05f2dfc2`, the built layout has 18 Intervals, 13 of them enabled, at 7.6 ticks/s.
   - Leaving out the one-shot `params-init-interval` (`max_intervals=1`) gives 6.6, and 3.0/6.6 is 45%. Read literally, the figure is 3.0/7.6, or 39%.
   - `2026-09-23_canopy_interval_census.py:97-101` leaves the one-shot out on purpose. The docstring keeps "by the static census"; the message (lines 52-54) does not.
   - **Changes:** no.

7. **NIT.** The note's scope still leaves out "Verifying everything wired correctly" (`REPLAY_V2_FAQ.md:231-264`).
   - Steps 2-4 fail today: F-057 breaks steps 3-4, and against cascor F-059 breaks steps 2-3.
   - Its `jq '.data.weights_available'` (`:260`) reads a key that cascor nests under `.data.session`, so it prints null. This predates the change.
   - **Changes:** no.

8. **NIT.** Message line 37 is a reflow slip, 117 characters long. **Changes:** no.

**CORRECTIONS YOU COULD NOT REFUTE**

Round 3's findings:

- **#1 ANSWERED, correctly.** From `gh pr view`:
  - #190 merged into the g-2-v2 branch at 20:05:12Z. That branch had landed on `main` as #189 at 19:52:10Z.
  - `gh pr list --head` shows only #189 for the g-2-v2 branch. `dbc25277` has diverged from `main` (3 ahead, 512 behind), and `test_replay_weight_emission.py` has no history on `main`.
  - The text omits the first merge, #187, into the g-2-v1 branch 88 minutes after #184 had merged that branch (`d85c9ddd`: 6 ahead, 519 behind). It states no count, so this is incomplete, not false. `REPLAY_V2_FAQ.md:286` names #187.
- **#2 ANSWERED.** The test now pins four loosenings: another property, State, an Output writer, and a substring match.
- **#3 NOT ANSWERED.** See finding 1.
- **#4 ANSWERED.** "under its header" is right: the status line is at `:4` and the note at `:8`.
- **#5 PARTLY.**
  - Done: the mutant script now checks "exactly one" (`2026-09-24_idle_cuts_check_mutants.py:98`), and it is committed in juniper-ml `3f83b9c6`.
  - Open: that commit is unpushed (`git branch -r --contains` is empty and `ls-remote` shows no branch). The ledger-first merge order still applies.
- **#6 ANSWERED** for the passages round 3 cited. See findings 3 and 7.
- **#7 ANSWERED.** Both lists now have three items. See finding 5.

Other claims I tried and could not break:

- **Quotes from #676's message:** exact (`e9053227` lines 15, 30-31 and 35).
- **Tests:**
  - 13 passed, and node ran the rule test.
  - The mutant script reports 10 of 10 caught with no leftover files.
  - The 16-file grep reproduces. The 15 non-UI suites plus `test_panel_layout_snapshots.py` give 345 passed; the UI file defines 5 tests.
- **Census:** 3.0 of 6.6 (45%) reproduces under the census's own definition.
- **Symbol-loss waiver:**
  - The trailer is the last paragraph and parses.
  - The 0.9.0 screen, run from source, reports WAIVED 2 and fail=0, including the 11 → 6 line shrink.
  - The docs screen reports 2 WARN and fail=0.
  - The waiver is read by a line regex (`symbol_loss_check.py:418`), and `main-verify.yml:244` runs the same screen after the merge. So GitHub moving `Co-authored-by` into its own paragraph is harmless. On `894a2cc7`, `%(trailers)` is empty yet the regex still finds it.
- **Pinned pre-commit:** clean on all 7 files.
- **For the ledger:** #184's diff did reach `main`, through #189 (`b1d19948` is an ancestor of `main`). That answers the "unchecked" at `…E2E-VALIDATION-EVIDENCE.md:9010`.

**WHAT YOU COULD NOT CHECK**

- The 5 `tests/ui` tests, which the rules forbid; 350 is checked by count only.
- F-059 and the model-select path on a live page.
- CI on a signed commit: `9935b857` is unsigned (`%G?`=N).
- The published 0.9.x wheel; I ran 0.9.0 from source.
- Whether the PR-description edit will happen before the merge.

**SECRETS/PII:** Nothing printed or sent. The `gh` calls were reads. No repository file changed (changed documents: none). Scratch work is under `…/scratchpad/c4r4.cuBcYT/`. Mutant files were written only in my extract and deleted, with none left over. No service was started and no port touched.

---

## Lane C5 -- round 5, adversarial, on the corrections 9935b857..b07943d6

*agent `a1be7635b1a68430b` · round 1 · last-assistant-text (not resumed) · 9011 chars*

**VERDICT: MERGE-WITH-FIXES.** Two of the corrections added new false statements. Everything mechanical passes. I checked canopy `b07943d6` (extracted to scratch) and cascor `0e016a7c`.

**FINDINGS**

1. **MINOR. The FAQ now names the wrong way out of a stuck cascor replay.**
   - Quoted, `notes/development/REPLAY_V2_FAQ.md:15-18`: "The player's Stop is also canopy's only way to stop a cascor replay, so a Replay started from the page leaves cascor replaying: it refuses training, a new network, and restore, resume and retrain until the replay is stopped through cascor's own API or cascor restarts." Also `:13-14`: "no control, readout or badge is on screen".
   - Evidence, canopy side:
     - The "↻ Reset Training" button is at `src/frontend/dashboard_manager.py:1041-1045`. The Training Controls card "is always visible" (`:308`), and the Replay tab keeps a sidebar (`ui_standards.py:49`).
     - Its only `disabled` writer is the loading-state callback (`:5355`, `:8547-8571`).
     - The click is mapped to `reset` (`:122-128`). It goes to canopy's own `/ws/control` (`websocket_client.js:576-577`, `main.py:1043-1044`) or to `/api/train/reset` (`main.py:3770-3788`).
     - From there: `service_backend.py:214-215`, then `cascor_service_adapter.py:1137-1143`, then the client's `/training/reset`. Nothing in that chain guards on replay state.
   - Evidence, cascor side:
     - The route `routes/training.py:169-174` has no replay guard.
     - `manager.py:2871-2903` `reset()` says "The FSM documents RESET as the REPLAYING escape hatch". It stops and clears `_replay_session`, and `state_machine.py:222-226` goes to STOPPED from any state.
     - cascor's own `test_reset_while_replaying_stops_session` (`test_training_route_coverage.py:440`) and its two sibling tests: I ran them on `0e016a7c`, 3 passed.
     - Stop Training, by contrast, is refused while replaying (`manager.py:2842`).
   - This claim is new in this round. The ledger's F-CANOPY-059 entry does not make it (`…E2E-VALIDATION-EVIDENCE.md:9081-9110`).
   - Fix: say that the player's controls are off screen and that Stop Training is refused, but Reset Training ends a cascor replay (it also clears cascor's metrics and counters). Change "no control" to "none of the player's controls, readouts or badges".
   - Changes a number/disposition/action? **Yes, an action** (the text must change before merge).

2. **MINOR. The CHANGELOG and the squash body misquote the tree.**
   - Quoted, `CHANGELOG.md:218-221` and message lines 57-61: the docstring "now reads 3.0 of the 6.6 steady-state ticks per second the layout's enabled Intervals nominally fire, leaving out the one-shot `params-init-interval` (45%)".
   - Evidence: `test_idle_dispatch_cuts.py:10-11` actually reads "fired 3.0 of the 6.6 ticks per second that the layout's enabled Intervals nominally fire (45%, by the static census)". The diff `9935b857..b07943d6` touches only `:44-48` and `:170-176` of that file. Round 4's finding 6 was applied to the two descriptions, not to the docstring.
   - The numbers themselves are right. The census on #676's parent `05f2dfc2` gives 6.60 ticks/s; the drain (2.00) plus `metrics-panel-update-interval` (1.00) make 3.00; `params-init-interval` counts 0.00.
   - Fix: edit the docstring, or revert the two descriptions to match it.
   - Changes a number/disposition/action? **Yes, an action.**

3. **NIT. Round 4's finding 1 was answered in wording only.**
   - Quoted, message lines 14-15: "which is corrected by editing the PR, not by this commit."
   - Evidence: #676's PR body was last edited at 2026-09-23T20:40:10Z, before it merged at 01:38:02Z. The ledger still lists that edit as owed (`:9425-9428`, item 13). A reader of `main` will take "is corrected" as done.
   - Fix: write "is owed as an edit of the PR", or make the PATCH before this merges.
   - Changes a number/disposition/action? No.

4. **NIT. Two places still claim more than the tests pin.**
   - Quoted, `CHANGELOG.md:216-218` and the module docstring `:45-48`: "counts as a consumer … an id that merely contains the Interval's fails one of them".
   - Evidence: I replaced `_consumers` at `:113` with `str(i["id"]).endswith(component_id)`, a mutant that also counts ids containing the Interval's. The file still gave 13 passed. Only the test's own docstring (`:175-176`) says it "does not pin every other way of matching an id".
   - Changes a number/disposition/action? No.

5. **NIT. The FAQ's `curl` note is incomplete.**
   - Quoted, FAQ `:19-20`: it names only `.data.weights_available`.
   - Evidence: the same `jq` (`:271`) also reads `.data.weight_sampling`, which is nested under `session` too (cascor `manager.py:1173-1179`, `snapshots.py:447-450`). The `curl` is also a POST that starts a replay (`snapshots.py:411-452`), and the note says a replay leaves cascor refusing training.
   - Changes a number/disposition/action? No.

6. **NIT, outside the diff. The user manual still describes the player as working against cascor.**
   - Quoted, `docs/USER_MANUAL.md:753`: "'No active replay session' until a replay is confirmed on the Snapshots tab". Items 2-8 (`:754-761`) also describe controls that never render against cascor.
   - This follow-up edits `:763-767` of the same section; the FAQ gets an F-CANOPY-059 note, the manual does not.
   - Changes a number/disposition/action? No.

**CORRECTIONS YOU COULD NOT REFUTE**

- **Round 4's finding 2, the CHANGELOG sentence** (`CHANGELOG.md:164-166`): holds. I ran `render_session` on a cascor-shaped session and it raised `KeyError(0)`; with a list range it rendered the active view. The probe is outside the repo, as the brief requires: `…/scratchpad/c5.hOQygT/probe_render_session.py`.
- **The FAQ's F-CANOPY-059 bullet, apart from finding 1:**
  - The placeholder claim holds (`replay_player_panel.py:114-115`, `:156`).
  - A replay does start paused at frame 0 (`manager.py:1076`, `:1244`), and only `play()` un-pauses it (`:1102-1105`).
  - The refusals hold: training `:2452`, a new network `:1731`, restore `:5784`, retrain `:5829`, resume `:5904`.
  - "Fails from step 2" holds.
- **The rewritten Stop bullet and the buffer sentence:** hold. The session Store has only two writers (`hdf5_snapshots_panel.py:1269`, `replay_player_panel.py:673`), and the weight buffer only one (`:565`).
- **Round 4's findings 3 to 8:**
  - 3: only the g-3 and g-7 notes are stale; g-6 is on cascor `main` (`manager.py:436`).
  - 4: "by exact id" is gone.
  - 5: all five of the ledger's corrections (`:8773-8786`) are now listed.
  - 6: the numbers are right (finding 2 is about the quote).
  - 7: the key claim is right (finding 5 is about what it leaves out).
  - 8: the longest body line is now 73 characters.
- **The new round-3 sentences:** both quoted phrases are in #676's message (`e9053227`).
- **Mechanical checks:**
  - `test_idle_dispatch_cuts.py`: 13 passed.
  - Mutant script, pointed at my extract: 10 of 10 caught, each by its named test, no leftover files.
  - The 15 non-UI suites that name a touched file, plus the panel layout snapshots: 345 passed.
  - Symbol-loss screen `e9053227..b07943d6`: 2 findings, both waived, exit 0.
  - Docs-additions screen: exit 0.
  - Pinned black 26.3.1 and flake8 7.3.0: clean on the test file.
  - Trailer paragraph: still the last paragraph, parsed by `git interpret-trailers`, and it names both methods.
  - FAQ blockquote structure is intact. markdownlint does not apply to either file: canopy's pre-commit excludes `CHANGELOG.md` and `notes/.+/`.
- **Staleness check:** no sentence inside the diff or the message is made false by F-CANOPY-059, other than the new one in finding 1.

**WHAT YOU COULD NOT CHECK**

- **The message's "350 passed":** the 5 remaining tests are `@pytest.mark.ui` tests in `tests/ui/test_ws_silent_poll_liveness.py`, which the brief forbids me to run. 345 plus 5 matches the claim.
- **No live drive:** finding 1 rests on source plus cascor's own route test, not on a running page.
- **Round 4's own list of "incomplete" sentences:** I had only the brief's summary of it.
- **The squash result:** when GitHub squashed #676, it moved `Co-authored-by` into its own final paragraph (compare `e9053227` with `4b4cfb16`). If that happens again, `Allow-Symbol-Loss` will not be in the last paragraph on `main`. canopy's gate still finds it, because it regex-scans the whole message (`symbol_loss_check.py:170-172`, `:418`).
- **The ledger IDs:** F-CANOPY-056, 057 and 059 are not on juniper-ml `origin/main`, and `docs/canopy-e2e-phase9` has no remote branch. The cross-references resolve only if the ledger lands first, as the ledger itself plans.
- **Signing:** `b07943d6` is GPG-signed (G), not unsigned as the brief says.

**SECRETS/PII:** I printed no environment variables, tokens or credential files, and the one GraphQL query asked for no email field. One slip: `git log --format=%GS` and `git cat-file commit b07943d6` printed the owner's email in local tool output only. Nothing was sent to any external service.

---

## Lane C6 -- round 6, adversarial, on the corrections b07943d6..511f8da8

*agent `af45b059a1f3e9101` · round 1 · last-assistant-text (not resumed) · 8363 chars*

VERDICT: MERGE-WITH-FIXES

FINDINGS

1. **MINOR: the FAQ's new way-out text leaves out that a replay has already replaced cascor's live network.**
   - Quoted text, from `notes/development/REPLAY_V2_FAQ.md:17-21` in canopy at 511f8da8: "The sidebar's **Reset Training** ends it: cascor documents reset as a replay's escape hatch, and a reset also discards the run's metrics and counters, not its data." and "…and its POST starts a replay."
   - What is true: each sentence is correct about `reset()` itself.
   - What is missing: the note now lists what it costs to enter a replay (the refusals) and to leave one (metrics and counters). It never says that starting a replay swaps cascor's live network for the snapshot's network, and that neither Reset nor Stop puts the old one back.
   - How it misleads a reader into an action:
     - Running the FAQ's `curl` POST against a cascor that holds a trained network nobody has saved.
     - Doing Replay, then Reset, then Start Training, expecting the earlier run to continue. What actually trains is the snapshot's network.
   - Evidence (cascor at 0e016a7c):
     - `start_replay` calls `_load_snapshot_to_network` (`src/api/lifecycle/manager.py:5977`), and that sets `self.model = CascorModel(network=network)` (`:5734`).
     - `reset()` (`:2871-2910`) and `stop_replay()` (`:6063-6085`) never touch `self.model`.
     - `_auto_snap_best` defaults to `False` (`:1472`), so a trained network nobody saved is simply dropped.
     - The next plain start "trains on" the data that is still bound (`:2899-2901`).
   - Evidence (canopy): the Replay confirmation modal calls it "read-only playback" (`src/frontend/components/hdf5_snapshots_panel.py:533`), and so does the proxy route's docstring (`src/main.py:2985`). Both predate this pass. The E2E evidence ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) has no entry for this.
   - Fix: add one clause, for example: "Starting one, from the page or with this POST, also loads the snapshot's network in place of cascor's live one, and neither Reset nor a Stop restores it: save a snapshot first."
   - Changes a number/disposition/action? **Yes: an ACTION** (one clause in the note, and possibly a new ledger entry for the "read-only" wording, the owner's call).

2. **NIT: the FAQ's "no Stop is on screen" has lost what it referred to.**
   - Quoted text, from `REPLAY_V2_FAQ.md:32-33`: "Against cascor a Stop does not clear the session (F-CANOPY-056), and today no Stop is on screen (F-CANOPY-059)."
   - Evidence:
     - This pass removed the sentence that bullet 5 pointed back to, "The player's Stop is also canopy's only…" (at b07943d6, line 15).
     - Bullet 1 now names the sidebar's "Stop Training" instead (`:16`), and that button is always on screen (`dashboard_manager.py:8569`).
     - As a result, "no Stop is on screen" now contradicts the same note.
   - Fix: "no player Stop is on screen".
   - Changes a number/disposition/action? No (optional wording; it can go in with finding 1).

3. **NIT: the commit message cites a script that is on no published branch.**
   - Quoted text, from the 511f8da8 message: "(juniper-ml util/ad-hoc/2026-09-24_idle_cuts_check_mutants.py)".
   - Evidence:
     - The script exists only in commit 3f83b9c6 on the local branch `docs/canopy-e2e-phase9`.
     - `git ls-remote --heads origin docs/canopy-e2e-phase9` returns nothing.
     - `git branch -r --contains 3f83b9c6` returns nothing.
     - `gh api .../contents/util/ad-hoc/2026-09-24_idle_cuts_check_mutants.py?ref=main` returns 404.
   - This was already in b07943d6's message, so this pass did not introduce it.
   - Fix: land the juniper-ml branch before or together with the canopy squash.
   - Changes a number/disposition/action? No change to the artifact; it is a merge-ordering note only.

CORRECTIONS YOU COULD NOT REFUTE

- **Finding 1, "refuses training, a new network, restore, resume, retrain, Stop Training".** Every refusal is in cascor's source:
  - start: `manager.py:2452`
  - create network: `:1731`
  - restore, retrain, resume return 409: `snapshots.py:278`, `:329`, `:378`
  - stop: `manager.py:2842`, which the route turns into a 409 at `training.py:142`
- **Finding 1, "The sidebar's Reset Training ends it".** The full path checks out:
  - The button (`dashboard_manager.py:1043`) sends either a POST to `/api/train/reset` (`main.py:3770-3788`) or the WS `reset` command (`main.py:1043`).
  - Both reach `ServiceBackend.reset_training`, then the adapter (`cascor_service_adapter.py:1137-1144`), then juniper-cascor-client 0.8.0's `/training/reset`.
  - cascor's `reset()` stops the replay session and clears it (`manager.py:2888-2894`), then applies FSM RESET, which always moves to STOPPED (`state_machine.py:222-226`).
  - The button's disabled state tracks only its own clicks, not the FSM (`dashboard_manager.py:8547-8571`).
  - "Documents reset as a replay's escape hatch" is in `state_machine.py:49-51` and `manager.py:2878`.
  - "Metrics and counters, not its data" matches `manager.py:2896-2908` and `monitor.py:387-390`.
- **"None of the player's controls, readouts or badges is on screen".** `render_session` raises at `range_value[0]` on cascor's dict-shaped `range` (`replay_player_panel.py:508`, `:534`; cascor `manager.py:1165`). Every control, readout (including last-sample at `:204`) and badge sits inside the active container (`:169-352`), which stays at `display:none`.
- **The `curl` sentence.** Both keys come from `state_summary()` (`manager.py:1172-1179`) and sit under `data.session` (`snapshots.py:447-450`). The POST moves the FSM to REPLAYING (`manager.py:6001`).
- **Finding 2, the docstring paraphrase.** "Now says" matches `test_idle_dispatch_cuts.py:10-11`. I ran the census script on #676's merge parent 05f2dfc2:
  - It prints "18 Intervals; 6.60 ticks/s at layout defaults".
  - The drain is 2.00 and `metrics-panel-update-interval` is 1.00, so the two timers are 3.00 (45%).
  - `params-init-interval` is 0.00 because its `max_intervals` is finite (`2026-09-23_canopy_interval_census.py:97-101`).
- **Finding 3, "left to a separate edit".** PR 676's `updatedAt` is 01:38:03Z, one second after `mergedAt`, so its description has not been edited yet.
- **Finding 4, "matched by substring (fe in fed)".**
  - The mutant script, run on my extract, caught 10 of 10, each failing exactly its named test.
  - I added three more mutants: a `startswith` mutant is caught; `endswith` and the reverse direction (`str(i["id"]) in component_id`) survive, with 13 passing each.
  - That is consistent with the new wording, which names only the fe-in-fed direction, and with the test's own disclaimer at `:176-177`.
- **Structure.**
  - The markdown-it block-token sequence is identical at b07943d6 and 511f8da8 for both `CHANGELOG.md` and `REPLAY_V2_FAQ.md`.
  - The changed lines have no trailing whitespace or tabs.
  - Both files are excluded from the markdownlint hook (`.pre-commit-config.yaml:237`).
- **Trailer.** `git interpret-trailers --parse` returns `Allow-Symbol-Loss` (naming both methods), `Co-Authored-By` and `Claude-Session`, all in the last paragraph. Both waived symbols exist at e9053227 (`:113`, `:193`).
- **Tests.**
  - `test_idle_dispatch_cuts.py`: 13 passed.
  - The 15 non-ui suites that name a touched file, plus `test_panel_layout_snapshots.py`: 345 passed. The message's 350 equals 345 plus the 5 test functions in the ui suite, which I did not run.

WHAT YOU COULD NOT CHECK

- `tests/ui/test_ws_silent_poll_liveness.py` is forbidden to run, so "350 passed" matches by count only.
- "Pinned pre-commit clean": not run, because my extract is not a git repo and the worktree is read-only.
- There was no live cascor, so the Reset behaviour and the network swap come from reading source, not from a run.
- The census was run at the merge parent 05f2dfc2, not at #676's original base.

SECRETS/PII: I printed no environment variables, tokens or credential files. I requested no email field from GitHub, and used no `git cat-file commit` and no `%GS`, `%ae` or `%ce` formats. The `%B` bodies I was told to read, and the `git interpret-trailers --parse` output, show only the `Co-Authored-By` bot address `noreply@anthropic.com`, not the owner's. No slip. No repo file was changed; all scratch work stayed in `mktemp -d` extracts under the session scratchpad.

---

## Lane C7 -- round 7, adversarial, on the corrections 511f8da8..e455af03

*agent `aad44df9cd97a6a01` · round 1 · last-assistant-text (not resumed) · 6950 chars*

**VERDICT: MERGE-WITH-FIXES.** Both FAQ edits are true and the note's structure is intact. The one fix is a sibling copy of the claim round 6 corrected, which the correction did not touch.

**FINDINGS**

1. **MINOR: `CHANGELOG.md:164` (in `e455af03`) still makes the claim round 6 had narrowed in `REPLAY_V2_FAQ.md`.**
   - **Quoted:** "Against cascor no Stop is on screen anyway: the player never shows a session, because its render raises on cascor's `range` (F-CANOPY-059, same ledger)."
   - **Evidence it is false:** the sidebar's "Stop Training" button is on screen on every tab, the Replay tab included:
     - `dashboard_manager.py:308`: "Training Controls card is always visible".
     - `dashboard_manager.py:1031` renders "Stop Training".
     - `ui_standards.py:49`: `"replay": NARROW_SIDEBAR`, so on that tab the sidebar is narrow but not hidden.
     - The button is disabled only while its own command is in flight (`dashboard_manager.py:8219`), so during a replay it is enabled. Pressing it gets a refusal (`manager.py:2842-2843`).
   - **Not introduced by the correction:** `git show 511f8da8:CHANGELOG.md | grep -n "no Stop is on screen"` gives `164:` too. So this is the second copy of a corrected fact, left standing.
   - **Fix:** "Against cascor the player's Stop is not on screen anyway: …"
   - **Changes a number:** no. **A disposition:** no. **An action:** yes, one extra line edit before merge, but only if the reconciler keeps round 6's standard. If the colon clause is judged to scope "no Stop" to the player, this changes nothing and the review ends.

**CORRECTIONS YOU COULD NOT REFUTE**

1. **Sentence 1 is true in every clause.**
   - **"that way":** the FAQ's curl (line 273) posts to cascor `/v1/snapshots/<id>/replay`. That route (`routes/snapshots.py:411-438`) calls `start_replay` (`manager.py:5947`), which calls `_load_snapshot_to_network` (`:5977`), which sets `self.model = CascorModel(...)` (`:5734`).
   - **"from the page":** "Load ▼ → Replay — read-only playback" (`hdf5_snapshots_panel.py:964`) posts `/api/v1/snapshots/{id}/{operation}` (`:573`). The canopy route (`main.py:2983`) calls `adapter.replay_snapshot`, which posts `_client._post("/snapshots/{id}/replay")` (`cascor_service_adapter.py:2361`). The client prefixes `/v1` (juniper-cascor-client `constants.py:24`; the installed 0.8.0 prints `/v1`), so this reaches the same `start_replay`.
   - **Nothing restores the old network:**
     - `self.model` is assigned only at `:1295`, `:1754`, `:1796`, `:3004` and `:5734`. None of these puts back a pre-replay network; there is no stash.
     - The `network` setter's only non-test write in `src/` is `_WeightHistoryRecorder` at `:487`, a different object.
     - `reset()`, `stop_replay()` and `_ReplaySession.stop()` never assign it.
     - Every reset path calls bare `lifecycle.reset()`: REST `training.py:169-173`, WebSocket `control_stream.py:487`, canopy `reset_training` at `:1137-1143`.
     - A new replay loads the new snapshot.
     - Restore (Investigate), Resume and Retrain are refused while REPLAYING (`:5784`, `:5829`, `:5904`).
   - **"save a snapshot first" works:** `save_snapshot` serializes `self.network` with `include_training_state=True` (`:5672`), with no state guard. The page's "Create Snapshot" button reaches it (`main.py:2600-2625`). No cascor code deletes snapshot files.
   - **Executed** on a `git archive 0e016a7c` export (manager loaded from the scratch copy; snapshots and logs redirected to scratch). Setup: save S, change the live weights to make L, save A. Results:
     - `start_replay(S)`: REPLAYING; network is S, not L.
     - `replay_control("stop")`: STOPPED; network still S, not L.
     - Replay then `reset()`: STOPPED; network still S, not L.
     - Restore or resume of A while REPLAYING: `loaded=False`, "rejected: lifecycle is REPLAYING".
     - After a reset, `resume(A)` gives RESUME_READY and `restore(A)` gives INVESTIGATING. In both, the network equals L exactly.
2. **Sentence 2 is true, and the note still reads consistently.**
   - `render_session` does `range_value = summary.get("range") or [start, end]` (`replay_player_panel.py:508`) and then indexes it as a list (`:534`). Cascor serves `range` as a dict, so this raises `KeyError: 0`.
   - When the callback raises, the `-active` div (`:115`), which holds the player's Stop (`:233-234`), keeps `display: none`. This matches the ledger's F-CANOPY-059, which was reproduced by executing the callback.
   - No other replay Stop exists on the page; the context menu offers only restore, replay, resume and retrain.
   - The narrowing is what makes the sentence true, because the sidebar's Stop Training is on screen (Finding 1).
   - F-CANOPY-056's "a Stop" is the player's Stop, so both clauses of that bullet share one referent. Sentence 1's "a Stop" is true under either reading.
3. **The blockquote is intact.** A CommonMark parse (markdown-it-py 4.0.0) of both versions gives an identical token shape for the whole document (350 tokens each). Only the two inline texts differ. All edited lines keep the `>` prefix and the three-space continuation, with no tabs or CRs. Line 35 grew to 113 characters, but canopy's markdownlint hook excludes `notes/.+/` (`.pre-commit-config.yaml:237`).

**WHAT YOU COULD NOT CHECK**

- **No live page was driven**, per the hard rules. Sentence 2 rests on source code plus the ledger's executed callback.
- **The executed check was narrow.** It used an untrained 2-to-1 network with no dataset and compared only output weights and bias. It proves the lifecycle swaps and restores the model as claimed. It does not prove that every field of a trained network (hidden units, history) round-trips; cascor's own serializer round-trip tests cover that, and I did not run them.
- **Two older, known limits** (not part of the correction):
  - Whether the curl's `localhost:8200` reaches cascor depends on the setup (host-run versus compose mapping).
  - The page's Restore looks up snapshots in canopy's own snapshot directory (`main.py:2750-2765`). That only works where canopy and cascor share it, as in the shipped compose; this is already in the ledger around lines 3265-3280. Resume and Retrain do not have this dependency.

**SECRETS/PII:** nothing printed or sent. I read no env vars, tokens, credential files, email-bearing commit headers or signature fields, and called no external service. The executed run wrote only to `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/c7.5RlS/`. The live `juniper-cascor/logs/juniper_cascor.log` was last written at 02:23:19, before my run at 02:23:48, and contains none of my run's snapshot ids. **Changed:** no repo files. The ledger (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) and `util/ad-hoc/2026-09-24_phase9_ledger_round{3,4}_corrections.py` changed in this worktree during the review; those edits are not mine.

---

## Lane C8 -- round 8, adversarial, on the correction e455af03..26bf27b3 and a final sweep

*agent `ab89889ecfd04b44d` · round 1 · last-assistant-text (not resumed) · 6960 chars*

**VERDICT: MERGE.** Canopy `26bf27b3` makes one correction since round 7, and it is true in both places it appears. The final sweep found no false sentence, and every mechanical check passes. No number, disposition or action changes, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` the review ends here.

**FINDINGS**

None.

**CORRECTIONS YOU COULD NOT REFUTE**

1. **The correction is true in both contexts: `CHANGELOG.md:164` and message lines 28-29.**
   - **Scope.** `git diff e455af03 26bf27b3` changes exactly one `CHANGELOG.md` line. The two `%B` bodies differ only in that one message line. Both commits sit directly on `e9053227`.
   - **I ran the render on the `26bf27b3` extract.** I called `render_session` with a session shaped like cascor's `/replay` data block. That block is built by `_build_unified_payload`, plus `session: state_summary()`, whose `range` is `{"start","end"}` (cascor `manager.py:1165`).
     - With cascor's dict `range`, it raises `KeyError(0)`.
     - With a list `range`, it renders `-active` as `display: block`.
   - **The Stop is inside the hidden container.** A walk of the layout places `replay-player-panel-stop-btn` under `replay-player-panel-active`.
     - `-active` ships with `display: none` (`replay_player_panel.py:115`).
     - Its only writer is `render_session` (`:459`). No other Python Output writes it, and nothing in `src/frontend/assets/` calls `set_props` on it.
   - **The sidebar's Stop Training is not the player's Stop.** No other replay Stop exists on the page.
   - **In the CHANGELOG, "anyway" is accurate.** It follows F-CANOPY-056's "A Stop does not clear the session", which the unreachable Stop masks.
   - **"This change neither causes nor fixes either" holds.** #676's eight files (`git diff --stat 05f2dfc2 e9053227`) never touch `render_session`.
   - **The message's quote is exact.** "also keeps its session view" is in `e9053227`'s `CHANGELOG.md` ("The player also keeps its session view."), and that sentence is gone at `26bf27b3`.

2. **The final sweep found nothing false.**
   - **Quotes of #676's message are exact** (checked against `e9053227` `%B`):
     - "two rounds; prose corrections only"
     - "runs until the page reloads, as it always ran before"
     - "Comments that claimed cascor emits weights … are corrected"
     - "live check of this build against its parent"
     - "half of the page's steady-state ticks"
   - **Review history.** "Rounds 1 and 2 each changed test code" (`key=str`, then the dict-id assertion) matches finding 1 of `2026-09-23_validator_reports_phase9_round3.md`.
     - That report's numbering matches the message: 2 is the PR description; 3 lists the surviving phrases, including the one uncorrected comment, `ws_dash_bridge.js:113-115` "see g-3 emitter"; 4 is the two loose squash-body claims; 6 is the no-id and dict-id crashes.
   - **The #676 timeline, via GraphQL.** Converted to draft at 19:44:37Z, marked ready at 22:28:04Z, auto-squash armed at 22:28:12Z, merged at 2026-09-24T01:38:02Z.
     - Its description was last edited at 2026-09-23T20:40:10Z, before the merge, so "left to a separate edit" still holds.
   - **The emitter history, via GraphQL.**
     - cascor#189 (head `feature/can-015g-2-replay-weight-cache-v2`, base `main`) merged at 19:52:10Z.
     - cascor#190 merged into that branch at 20:05:12Z, 13 minutes later.
     - #189 is the only PR ever opened from that branch, and #190 the only one from the g-3-v2 branch.
     - Remote cascor `main` is still `0e016a7c`. There `_emit_frame` sets no weights, and `weights_at` has no caller outside tests.
   - **Other facts checked:**
     - `ce78e0de^` is `3a6dea95`.
     - #676's eight files exclude `replay_forward.py`, `USER_MANUAL.md` and `REPLAY_V2_FAQ.md`.
     - `replay_forward.py`'s only importers are `network_evolution.py:31` and `decision_boundary.py:47`. Both are fed only by `replay-weight-buffer`, so "no live input yet" holds.
     - cascor's `notes/development/SNAPSHOT_SCHEMA_V2.md` exists at `0e016a7c`.
     - The `USER_MANUAL.md` anchors resolve (`:657`, `:747`).
     - All of the player's controls, readouts and badges, including the dataset-swap graph, sit inside `-active`.

3. **Mechanics.**
   - **Trailer.** `git interpret-trailers --parse` returns `Allow-Symbol-Loss` (both methods), `Co-Authored-By` and `Claude-Session`. They form the last paragraph.
   - **The test file.** `test_idle_dispatch_cuts.py`: 13 passed, none skipped.
   - **Mutants.** `util/ad-hoc/2026-09-24_idle_cuts_check_mutants.py`, run against my extract, caught 10 of 10. Each failed exactly its named test, and no mutant files were left.
   - **Against #676's parent.** The head test file on `05f2dfc2` gives 7 failed and 6 passed; the 4 CHECK tests and the 2 premise pins pass. That matches the docstring.
   - **Wider suites.** The grep of the 16 suites reproduces. The 15 non-UI suites plus `test_panel_layout_snapshots.py` give 345 passed.
   - **Formatting.**
     - `git diff --check` is clean.
     - `CHANGELOG.md` has no trailing whitespace and ends in a newline.
     - `CHANGELOG.md` and `notes/development/` are excluded from the markdownlint and doc-links hooks (`.pre-commit-config.yaml:237`, `:270-271`).
     - The JS changes are comment-only, and `node --check` passes.
   - **Signing and base.** `26bf27b3` shows `%G?` = G. Remote canopy `main` is still `e9053227`.

**WHAT YOU COULD NOT CHECK**

- **The 5 tests in `tests/ui/test_ws_silent_poll_liveness.py`**, which the rules forbid me to run. "350 passed" matches by count only (345 + 5).
- **The full pinned pre-commit run.** I did not build hook environments. I checked only whitespace, end-of-file and hook exclusions for the one changed line.
- **A live page or a live cascor.** F-CANOPY-059 and the model-select path rest on source and the executed callback.
- **Merge-order items from earlier rounds**, which still stand and are not new findings:
  - The Phase 9 ledger (`JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`) and the mutant script exist only in local juniper-ml commits (`86e82c0c`, `3f83b9c6`). `git branch -r --contains 86e82c0c` is empty, and remote `docs/canopy-e2e-phase9` points at `f9c81d80`, which is also where juniper-ml `main` is.
  - The edit to #676's PR description is still owed.

**SECRETS/PII:** None printed or sent. I read no environment variables, tokens or credential files. I used no `git cat-file commit`, `%GS`, `%ae` or `%ce`; the only signature output was the `%G?` status letter. The GraphQL queries asked for numbers, states, dates, branch names and types only, with no email fields. The `%B` bodies show only the `noreply@anthropic.com` bot address. No slip. **Changed:** no repository file. All scratch work (extracts, the mutant run and a throwaway probe, `probe_render.py`) is in `/tmp/tmp.uRykx5SBEr/`. No service was started, no port was touched, and no process was left running.

---
