<!-- markdownlint-disable -->

# Phase 10 ledger validation, round 1 (frozen 0737d573)

Four lanes on the canopy E2E ledger's Phase 10, frozen as 0737d573, briefed separately (briefs in reports/e2e-canopy-2026-09-02/drafts/lane10{A1,A2,B1,B2}_phase10_ledger_brief.md): 10-A1 re-derived every claim from source at the pins; 10-A2 from the raw evidence tree and the instruments, with its own reproductions; 10-B1 attacked dispositions and ratings; 10-B2 attacked claims beyond the evidence. Each report is the lane's final message, verbatim.

## Lane 10-A1 - source re-derivation

*agent `ade7b4fa28b66f2a7` · round 1 · last-assistant-text (not resumed) · 13525 chars*

**VERDICT:** SOUND-WITH-FIXES. Every line reference, quotation, SHA and merge fact re-derives from git objects at the four pins, and all four pins equal `main`. There is one MINOR finding (a false "every path" / "never delivers" claim) and three NITs. None of them changes a number, severity or disposition.

**TABLE**

Legend: `show R S P a-b` means `git -C <R> show <S>:<P>` printed with line numbers by `python3 -B <mktemp>/show.py`. `grep` means `git -C <R> grep -n <pat> <S> -- <P>`.

| # | Claim | Re-derived value | Result | Evidence |
|---|---|---|---|---|
| P | Each pin equals `main` | canopy `1b2dd438…`, cascor `95cdc562…`, data `29be6d35…`, client `3adc061f…` | MATCH | 4× `rev-parse` and 4× `gh api repos/pcalnon/<r>/commits/main --jq .sha` print the same full SHAs |
| 1.1 | dm `:8404` defines the function; `:8410` holds the two stops | `def _producer_detail_from_refusal(detail: str)` at `:8404`; `for stop in (" To accept it,", " The resulting dataset"):` at `:8410` | MATCH | `show canopy 1b2dd438 src/frontend/dashboard_manager.py 8355-8450` |
| 1.2 | cascor `:4270`; every remedy begins "To accept it,", comes after the producer text, and is followed by cascor's closing sentence | def at `:4270`. Five remedies (`:4356`, `:4359`, `:4362`, `:4368`, `:4371`) all begin "To accept it,". `:4372` builds `…Producer detail: {detail} {remedy} The resulting dataset is permanently annotated as partial…` | MATCH | `show cascor 95cdc562 src/api/lifecycle/manager.py 4265-4385` |
| 1.3 | `:245` `_PRODUCER_REFUSAL_REMEDY` | `"Re-submit with allow_truncation=true"`; `:246` is 422; the match rule is at `:4351` | MATCH | `show … manager.py 225-262` |
| 1.4 | `limits.py:149-168` and `:135` | Class at `:149`; message at `:168` ends "The resulting dataset will be permanently annotated as truncated."; `:135` is `EQUITIES_DEFAULT_MAX_SYMBOLS: int = 14` | MATCH | `show data 29be6d35 juniper_data/core/limits.py 120-240` |
| 1.5 | A request with no symbols list asks for all 503 | `generator.py:715-717` uses `sorted(constituents)`; `:733-740` raises unless an opt-in is sent; the bundled CSV has 503 rows and 503 unique tickers | MATCH | `show … generator.py 700-760`; `count_constituents.py` prints `rows: 503 unique tickers: 503` |
| 1.6 | Options at `:8442-8443`, buttons at `:2365-2366`; accept and drop both re-stage with `allow_truncation=true` | Texts as quoted. `:546-547` both carry `allow_truncation: True`; `:8477-8479` merges that into `nn_dataset_params`; `:8559` uses it | MATCH | `show` of dm `2340-2385`, `530-552`, `8440-8585` |
| 1.7 | Fixture at `:36-45` claims to be the describer's message; its producer detail lacks juniper-data's remedy | Comment at `:37-38`, `_REFUSAL` at `:39-46`. The producer detail at `:43` has neither "Re-submit…" nor "Either choice…", so cascor (`:4351`) would not dress it as a refusal | MATCH (range off by one, NIT 2) | `show canopy … test_dataset_shortfall_prompt.py 1-80` |
| 1.8 | canopy's CHANGELOG records the cap refusal for the restart modal's re-stage | `CHANGELOG.md:434-438` | MATCH | `grep -i "symbol cap\|503"` on `CHANGELOG.md` |
| 1.9 | Executed outcomes | My own instrument, which lifts the three functions from git objects. CAP: `TOKEN_PRESENT: True`, `CANOPY_SHOWS: …to import the first 14 symbols.`, `PRODUCER_LAST_SENTENCE_SHOWN: False`. INCOMPLETE: `…SHOWN: True`. The fix arm gives `FIX_SHOWS_LAST_SENTENCE: True \| FIX_LEAKS: False` for both | MATCH | `python3 -B <mktemp>/f060_exec.py` |
| 2 | F-061 | `7ab994e5 main.py:517` and `1b2dd438 :532` read exactly as quoted. `dc5ea02e^:517` becomes `dc5ea02e:532`. #685 is MERGED, 2026-09-24T23:24:14Z, oid `dc5ea02e…`. Its body row 3 matches word for word. `canopy_constants.py:668-674` is the docs-not-exempt comment | MATCH | `grep _docs_enabled` at all four commits; `merge-base dc5ea02e 1b2dd438` returns `dc5ea02e`; `gh pr view 685 --json …` |
| 3 | F-062 | At `7ab994e5`: comment at `security.py:350`, the only `_PADDED_KEY_WARNING` at `:355`, reached by a file source via `:384`. At the pin: `:391`, `:497` and `:378-386` as stated; the test is at `:700` | MATCH | `grep _PADDED_KEY` at both commits; `show` of the ranges |
| 4.1 | Test `:41-42`; cascor `:4841`; #690 made the change | `:42` ends "Nothing was loaded: …"; `:4841` reads "The staged dataset was not loaded: it is still staged…". #690 is MERGED, 2026-09-25T02:06:36Z, oid `0fbb447a…`. The named test is at `src/tests/unit/api/test_start_refuses_wider_staged_dataset.py:186` | MATCH | `git diff 0fbb447a^ 0fbb447a -- src/api/lifecycle/manager.py \| grep` shows the old sentence on diff line 295 and the new one on 296 |
| 4.2 | Alert sentence at `:8381`; `:8359` reads only the marker and first sentence | `:8374` is `split(MARKER,1)[-1]…split(". ",1)[0]`; `:8381` matches the quote | MATCH | `show … dm 8355-8386` |
| 4.3 | NO canopy production caller passes tensors to a training start | grep (pattern in Evidence) finds only adapter `:1110` (`json={"start_fresh": True}`) and `:1112` (`start_training(**kwargs)`). All three `backend.start_training` sites traced: `main.py:1064` and `:3727` pass `{}` unless the backend is recurrence; `:3947` passes `reset` and `start_fresh` only. The control stream is used only for `set_params` | MATCH | `grep "inline_data\|train_x\|\.start_training(\|ENDPOINT_TRAINING_START\|/v1/training/start" -- src ':!src/tests'`; `service_backend.py:146` |
| 4.4 | The staged refusal fires before anything is bound | The refusal at `manager.py:4998-4999` comes before the first assignment at `:5000`. Inline tensors bind earlier, at `:2764`, which is why #690 reworded the sentence | MATCH | `show … 2645-2800, 4975-5025` |
| 4.5 | #694 corrected `test_p2_wave_batch_a.py`; its body records no sweep | Its files include that test; the body mentions no sweep | MATCH | `gh pr view 694 --json files,body` |
| 4.6 | A grep finds nine claim-bearing comments | My pattern: `-i -E "verbatim from\|measured (on\|off) the\|exact shape"` over `src/tests`. It returns 11 lines; 2 quote #532's retracted label (`test_f059_replay_range_dict.py:14`, `test_p2_wave_batch_a.py:181`). The other 9: `availability_unknown_state:87`, `f035:139`, `f054:99`, `poller_budget:149`, `stage2_global_lane:114`, `:339`, `start_fresh…:41`, `test_dashboard_manager:612`, `:732` | MATCH (case-insensitive; a case-sensitive grep gives 7) | as listed |
| 5.1 | `monitor.py:282-298`; `manager.py:2058-2065` | Two numberings with a `kind` key; rows written with `kind="output_epoch"` and `accuracy=None` | MATCH | `show cascor …` |
| 5.2 | mp `:1951`, `:2259`, `:2264`, `:1664`, `:1610-1624` | All as stated | MATCH | `show canopy … metrics_panel.py` |
| 5.3 | Adapter `:1885` and `:1960` drop `kind`; `:463-479`, `:778` and `state_sync.py:150` call them | Neither returned dict has `kind`; all three sites call both | MATCH (labels: NIT 3) | `grep "_normalize_metric\|_to_dashboard_metric\|\"kind\""` |
| 5.4 | "Every path" goes through them | The relay's `initial_metrics` branch skips normalization | MISMATCH (Finding 1) | Finding 1 |
| 5.5 | `test_n6:51` builds rows with `kind` | `def _output_epoch_row` at `:51`; its dict with `kind` at `:54` | MATCH | `show` |
| 5.6 | cascor `:2091-2092`, `:2144-2145`, drains at `:2078`, `:2115`, `:2150` | All as stated | MATCH | `show` |
| 5.7 | `USER_MANUAL.md:266`, `:271`, `:293` | All as quoted | MATCH | `show` |
| 6 | F-065 | `manager.py:5446-5448` as quoted. `messages.py:193` sets `payload["result"]`, and `:199` puts it in `data=payload`. `ws_client.py:822` resolves with the whole frame, and `_apply_params_hot` returns it unwrapped (`:1833-1835`). Adapter `:1369` then `:1383` merge WS and REST; the REST value is the full envelope (`client.py:419`, `:547`). `:1439-1442` scans the top level and `data` only. `:1296` is `{"epochs_max"}`. `settings.py:347` is `True  # C-28: default off…` | MATCH | `show` of each range |
| 7 | F-066 | `main.py:1579` has only demo (`:1590`) and service (`:1615`) branches; `:1626` answers 503. `recurrence_backend.py:163` and `:58-60` as stated. dm `:4149` runs on the slow lane, and its handler (`:7665`) fetches details every tick with no collapse-state input. `:7798` logs the WARNING | MATCH | `show` |
| 8 | O4 and O9 | `canopy_constants.py:35-48` reads metadata and falls back to literal "0.8.1" (pyproject is 0.8.1). In JuniperCanopy1 the package reports `0.6.0`, installed editable from the primary checkout. dm `:3260` and `:1329-1331` as stated; the cited handoff records O9 at `:76-81` | MATCH | `JuniperCanopy1/bin/python -s -c "importlib.metadata…"`; `git -C <worktree> show 0737d573:prompts/…` |
| 9 | Merge facts | #685: `dc5ea02e`, 2026-09-24T23:24:14Z. #690: `0fbb447a`, 2026-09-25T02:06:36Z. Both are ancestors of their pins | MATCH | `gh pr view`; `merge-base` |

**FINDINGS**

1. **MINOR: F-CANOPY-064's "That is every path … No consumer downstream can tell the numberings apart" is false.**
   - The same claim recurs in F-064 ("a `kind` key that the relay never delivers") and in F-063 ("builds a key that the live relay never delivers").
   - **Evidence:**
     - The relay normalizes only frames with `msg_type == "metrics"` (adapter `:774-780`). It broadcasts every other frame type raw.
     - On every non-resumed `/ws/training` connect, cascor sends `state` and then `initial_metrics` (`training_stream.py:299-300`, `:107-123`). The default burst is 100 rows (`settings.py:382-383`).
     - Those rows come from `monitor.get_recent_metrics` and carry `kind` (`manager.py:3467-3471`, `monitor.py:357-360`, `:312`).
     - cascor-client never sends a resume frame (`grep -i resume ws_client.py` hits only the command docs at `:425` and `:657`), and it yields every non-ping frame (`:395-398`). So every relay connect or reconnect forwards the burst.
     - The browser pushes `data.metrics[i]` into its metrics ring (`ws_dash_bridge.js:261-270`; dispatch at `websocket_client.js:206-208`, `:275`).
     - `_append_ws_metrics_store_handler` then appends those rows unchanged to `metrics-panel-metrics-store` (dm `:7829-7834`).
     - The result: `kind` does reach the store, on flat rows that also lack the nested `metrics` dict the panel reads (mp `:1952`).
   - **Fix:** name this branch as a fourth path that bypasses normalization. Change "never delivers" to "never delivers on a dashboard-shaped row". Add the `initial_metrics` branch to the fix direction and to item 18.
   - **Changes a number or disposition?** No; P1 stands, because the tile still reads the newest normalized row. **Changes the action?** Yes, slightly: the fix scope grows by one branch.

2. **NIT: F-CANOPY-060's "`test_dataset_shortfall_prompt.py:36-45`" is off by one.** At `1b2dd438`, line `:36` is blank; the comment is `:37-38` and `_REFUSAL` is `:39-46`. **Fix:** `:37-46`. **Changes anything?** No.

3. **NIT: F-CANOPY-064's "`/api/state`'s sync (`state_sync.py:150`)" and "the history fetch (`:463-479`)" mislabel their paths.**
   - The sync is `CascorStateSync.sync`, called from `ServiceBackend.initialize()` (`service_backend.py:456`) at boot and on model swap.
   - `/api/state` (`main.py:1351-1364`) serves `training_state`. Nothing in production reads the synced `metrics_history`: only its topology (`service_backend.py:346-347`) and its status fields (`main.py:268-283`) are used.
   - `:463-479` covers two fetches: `get_current_metrics` (`:457-468`) and `get_recent_metrics` (`:470-482`).
   - **Fix:** relabel both. **Changes anything?** No.

4. **NIT: F-CANOPY-060's "What is missing is the permanence notice" is partly false.** The accept option on screen already says "permanently annotated as partial" (dm `:8442`). What gets cut is juniper-data's own sentence that the dataset is annotated as truncated. **Fix:** "juniper-data's own truncation notice". **Changes anything?** No.

**WHAT YOU COULD NOT CHECK**
- **Counts:** 77/53/1/2/21 and the open P1/P2 split. I did not run `e2e_finding_triage.py`.
- **A-N2 archived evidence:** the 80 WARNING lines, the 4,422-row history and its x values, the `dashboard_final.png` tiles, the `03_set_params_caps.json` files and the `logs/` lines. Not read.
- **F-064's tile reading of 2501 vs 3, and F-065's four extractor outcomes:** checked by reading source only, not executed. The ledger's three instruments do exist in `0737d573` but I did not run them.
- **Engine behaviour:** whether the engine emits `epoch_end` during the growth loop's output retraining. The engine is outside the pins.
- **juniper-data-client's 422 text format:** the client is not pinned. My F-060 run used the bare producer message, which the cut does not depend on.
- **Deployment setting:** the value of `JUNIPER_WS_INITIAL_METRICS_COUNT` in juniper-deploy (not pinned). It sets how often Finding 1's path fires.
- **Defect-register arc:** its session `bc31e993` and its NIT/LOW ratings. Not read.

**SECRETS/PII:** I printed no environment variables, tokens, credential files, emails, commit headers or signature fields. Commit content was read only through `git show <sha>:<path>`, `git grep`, `git diff`, `rev-parse` and `merge-base`. `gh pr view` fetched only number, title, state, mergedAt, mergeCommit.oid, files and body. The brief's own `gh api …/commits/main --jq .sha` calls (×4) return a REST commit object that carries author email fields; only `.sha` was printed. That conflicts with the brief's "no REST commit objects" rule; it is not a slip on my part. The JuniperCanopy1 metadata read printed a local filesystem path. All scratch work stayed in a `mktemp -d` directory. No slips.

---

## Lane 10-A2 - evidence and instruments

*agent `acd6555a96132b51a` · round 1 · last-assistant-text (not resumed) · 12924 chars*

**VERDICT: SOUND-WITH-FIXES.** Every number in claims 1–9 re-derives. Three statements in Phase 10 of the ledger are wrong or overreach. None of them changes a count or a disposition, but they do change what items 18 and 20 should say. The ledger is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `0737d573`; the run's README is `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`.

Abbreviations: `WT` = the worktree. `R` = `WT/reports/2026-09-23_canopy-a-n2-generate-stage-train-render`. `S` = my `mktemp -d` directory, `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/lane10A2.g5NzBN`. `PY` = `env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB …/JuniperCanopy1/bin/python -B`. All four pins equal both local `origin/main` and GitHub `main` (`gh api …/commits/main`).

**TABLE**

| # | claim | re-derived value | verdict | evidence |
|---|---|---|---|---|
| 1 | F-066: 80 WARNINGs, emitted under recurrence | 80. They run 14:45:20,908–14:55:55,850 local, which is 19:45:20–19:55:55Z. Per case: 05 13, 06 14, 07 12, 08 13, 09 14, 10 14. None fall in 01–04b (19:30:47–19:43:23Z). The first comes 16.7 s after 05 selected recurrence (19:45:04Z). | MATCH | `grep -c "Network stats API returned 503" R/00_stack/logs/juniper-canopy.log` → 80. `python3 -B S/c1_timeline.py` buckets each line against the cases' `index.json` times. |
| 2 | F-065 archive | Request at 19:38:06.747Z with five params, status 200, answer `applied: ["cn_training_iterations"]`. The log shows `,752 via WS [4 keys]`, then `,758 via REST ['candidate_epochs']`, then `,763 updated [5]`. The offset is UTC−5: the response's own `state.timestamp` 1790192286.764 (19:38:06.764Z) lines up with the log's 14:38:06,763. The values landed: `04_state_before.json` at 19:38:06.766Z reads 8/60/40/32, with derived total epochs 860. | MATCH | `R/02_gaussian/03_set_params_caps.json`; `logs/canopy.slice.log:1-3` |
| 3a | History is slimmed; rows at x = 1, 26, 51; `candidate` at 9,551–10,000; final `output` at 11 | `_truncated_by_a_n2_slim`, count 4422, first_3 / last_20. Those x values. The final row is epoch 11, `output`, accuracy 0.963. No row carries `kind`. | MATCH | `13_render_api_metrics_history_limit_0.json` |
| 3b | PNG: 0–10k "Iteration" axis, no accuracy line, Accuracy 96.30%, Training Step 11 | All as stated. There is no line, but a zoomed crop shows a small marker cluster at x≈0, around 96–100%. | MATCH (wording only) | `S/crop.py` → `S/acc_left_zoom.png` |
| 3c | Caps refused with 502; Output Epochs 10000 | 502 "No network created". `nn_output_epochs` 10000. But the run used **cascor's engine defaults, not canopy's** (Finding 1). | MATCH / MISMATCH | `01_spirals_control/03_…`, `04_state_before.json`, `15_render_api_state.json` |
| 3d | Tiles 11, 13 and 22; every capture taken after its run completed | 01 (×3) = 11, 02 = 13, 03 = 22, 04 = 22. 04b reads **2**, which the ledger omits; it is also correct, since the last row is epoch 2, `output`. Every timeline sample shows Idle / Monitoring Inactive with a constant step. The terminal poll comes before each capture (01: COMPLETED at 152.05 s). | MATCH (list incomplete) | `grep -A2 "^Training Step" */dashboard*_text.txt`; `S/c3_captures.py` |
| 4 | O2: tile `2501` vs `3`; accuracy points at x 1–3 on an axis to 9976 | The script prints exactly that. | MATCH | `PY util/ad-hoc/2026-10-04_phase10_o2_rederive.py --canopy-src S/canopy/src` |
| 4' | Does the relay drop `kind` on every path the ledger names? | Yes, on all four: REST history, `/api/metrics`, the WS relay loop and the state sync. Mid-pass tiles read `441` and `1776`; with `kind` kept they read `5` and `2`. After a completed run every path reads `5`. Rows came from cascor's real `TrainingMonitor`, with budgets 700 and 3000, strides 40 and 25, and 5 and 2 steps. With the phase switched to `candidate` at the first grow iteration, only 1 of 5 step rows' accuracy reaches the chart, which supports the ledger's labelling claim. One path the ledger does not name keeps `kind` (Finding 2). | MATCH | `PY S/my_o2.py S/canopy/src S/cascor/src` |
| 5 | O3 partition | `[]`, then `['cn_training_iterations']` twice, then the mutation's three WS keys plus `nn_max_total_epochs` not-updatable. | MATCH | `PY …o3_rederive.py --canopy-src S/canopy/src` |
| 5' | Is the script's frame the frame canopy receives? | Yes. cascor's real `create_control_ack_message` has keys `[data, timestamp, type]`, `data` has `[command, command_id, result, status]`, and the partition is at `data.result`. The client resolves the whole frame (`ws_client.py:822` at `3adc061f`; the installed 0.8.0 is the same). The script nests the params echo under `"params"` where cascor's is flat, which the extractor never reads. Driving canopy's real `apply_params` gives `['cn_training_iterations']` and `skipped_detail=[]`. Removing the static backstop gives `verify mismatch {'epochs_max': {'requested': 60, 'applied': 860}}`, which confirms "only because of a static backstop". | MATCH | `PY S/my_o3.py …` |
| 6 | F-060 run, the stand-in, and the real exception | The script prints: token True, prompt True, closing sentence survives False, control True. With the fix flag, both survive and nothing leaks. The stand-in matches `origin/main` `75f15a62`: `_request` raises `JuniperDataValidationError("Validation error (422): "+str(detail), status_code=422)`, and juniper-data answers 422 with `detail=str(e)`. cascor reads only `str(exc)` and `status_code`. I used the real error classes, the real `_request` and the imported cascor describer, wrapped the result as cascor's 409, and fed it to canopy's real prompt handler. Three cap refusals (503/14, 40/7, CSV bytes) times five cascor stances all give: prompt opens, closing sentence never shown, no leak. The control is shown. With the proposed fix, all 20 cases show the sentence. The real exception class does not change the answer. | MATCH | `python3 -B …f060_rederive.py [--cut-only-at-remedy]`; `S/my_f060_stage_a.py` (cascor env) and `stage_b.py` |
| 8 | O4: installed metadata | Version 0.6.0, `editable` True, URL is the primary canopy checkout. The source says 0.8.1. | MATCH | `PY S/o4_meta.py` |
| 9 | Counts | 77 findings, 53 fixed, 1 accepted, 2 withdrawn, 21 open. Open P1 = 6 (F-CANOPY-055, -057, -058, -064, F-CASCOR-001, -002). Open P2 = 15. No P0. The parent commit `cf711cf4` gives 70/51/1/2/16, so the difference matches the seven new findings. | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py --note S/ledger_0737d573.md [--open-only]` |

**INSTRUMENT ADEQUACY** (every mutation was made in a scratch copy, never in a repo)
- **f060:** this script reads canopy from git objects, so editing a scratch tree cannot reach it. `S/f060_mutation_wrapper.py` mutates the text the script reads instead.
  - Stopping at cascor's own closing phrase: the cap's "survives" flips False→True.
  - Adding a `" Either choice"` stop: the control flips True→False.
  - Making `_is_dataset_shortfall_refusal` return False: "opens prompt" flips True→False.
  - Verdict: adequate.
- **o2:**
  - Carrying `kind` through `_normalize_metric` and `_to_dashboard_metric`: "keeps kind" flips False→True, and the relay tile flips `2501`→`3`.
  - Also skipping `output_epoch` rows in `_create_accuracy_plot`: the accuracy chart's x range flips (1, 9976)→(1, 3).
  - Verdict: adequate.
- **o3:**
  - Making `_extract_cascor_partition` also scan `data.result`: the WS-only arm flips `[]`→the three keys plus the skip. The A-N2 arm does not change.
  - Unwrapping the ack in `_apply_params_hot`: every script arm prints the same as before. The script writes its own copy of `apply_params`' merge, so no canopy change outside the extractor can move its A-N2 arm. My `apply_params` reproduction does flip under this mutation (Finding 3).
- **triage:** relabelling F-CANOPY-064 as P2 in a copy moves open P1/P2 from 6/15 to 5/16. Adequate.

**FINDINGS**
1. **MINOR.**
   - **Ledger text:** "The run used canopy's defaults, because its parameter caps were refused … Its Output Epochs (per pass) was 10000." The severity paragraph also says "For a CasCor run with canopy's default budgets, the accuracy curve cannot be read."
   - **Evidence:** the run's README, line 129, says "Control (01) ran at cascor's engine defaults … output_epochs 10000". Canopy's values before any network existed were 1000 / None / 500 / 1000 (`04_state_before.json`). After the run, `/api/state` read cascor's 1000000 / 10000 / 400 / 10. Canopy's own default is `DEFAULT_OUTPUT_EPOCHS = 25` (`src/canopy_constants.py:75`, at both `48074653` and `1b2dd438`). cascor's is `_PROJECT_MODEL_OUTPUT_EPOCHS = 10000` (`constants_model.py:300`).
   - **Fix:** say "cascor's engine defaults". At canopy's own budget of 25, the "unreadable sliver" argument does not hold.
   - **Changes a number/disposition/action?** No. P1 still stands on the cascor-default first run and on the executed tile failure.
2. **MINOR.**
   - **Ledger text:** "That is every path: the history fetch (`:463-479`), the WS relay (`:778`) and `/api/state`'s sync … No consumer downstream can tell the numberings apart."
   - **Evidence:** on every connect that is not a resume, cascor sends an `initial_metrics` burst of up to 100 raw monitor rows (`training_stream.py:282,299-300`). Neither the client nor the relay resumes, and the client yields the burst. canopy's relay normalises only `msg_type == "metrics"` (`cascor_service_adapter.py:777-780`). I drove the real relay loop with a frame from cascor's real `create_initial_metrics_message` (`S/my_o2_initial_burst.py`): the forwarded rows keep `kind` and arrive flat. The browser bridge pushes them into the metrics buffer (`ws_dash_bridge.js:261-270`), and `_append_ws_metrics_store_handler` appends them unchanged (`dashboard_manager.py:7813-7834`). Run through the real panel (`S/my_o2_burst_panel.py`), those rows plot loss and accuracy as **0**, and the tiles read Loss 0.0000 and Accuracy 0.00%. That last part is executed in isolation, not observed live.
   - **Fix:** name this fourth path. Item 18 should also normalise the forwarded burst, and the zero-painting may need its own id.
   - **Changes a number/disposition/action?** Action only: item 18's scope.
3. **MINOR.**
   - **Ledger text:** "a mutation that also scans `data.result` recovers the three WS keys and `epochs_max`'s `not-updatable` skip". The fix direction reads "read the partition from `data.result`, or unwrap the ack in `_apply_params_hot`", and item 20 reads "Read the WS leg's partition".
   - **Evidence:** that mutation arm only covers an apply sent entirely over WS. I made the same change in canopy and drove A-N2's request through the real `apply_params` (`S/my_o3.py`). It still answers `['cn_training_iterations']` with `skipped_detail=[]`, because the REST envelope's `data` overwrites the WS frame's `data` before the extractor runs. Unwrapping the ack alone recovers all four keys and the skip. A full-form Apply always mixes hot and cold keys, so this mixed case is the normal one.
   - **Fix:** say that reading `data.result` works only if the two legs are also kept apart, or that the ack is unwrapped. Reword item 20 to match. Have the instrument drive the real `apply_params`.
   - **Changes a number/disposition/action?** Action only: item 20.

**WHAT YOU COULD NOT CHECK**
- Nothing live, by rule: not the mid-pass tile, not the burst's effect in a browser.
- The A-N2 WS ack was not archived. The `epochs_max` not-updatable skip comes from cascor's `_apply_params_unlocked` source, not from an artifact. I did not execute cascor's `update_params`.
- The run used canopy `48074653` and cascor `f7a6d573`. I diffed canopy's adapter and panel against `1b2dd438`: the only changes are error-text and key-binding, with no logic change on these paths. I did not diff cascor.
- The cascor-client version the run used is not recorded in the archive.
- Capture wall-clock times are not archived. Claim 1 was bucketed by each case's HTTP index times instead.
- The history is slimmed, so it cannot show how many step rows cascor labels `output`.
- My reproduction scripts exist only in `S`. Copy them to `util/ad-hoc/` if they should be kept.

**SECRETS/PII:** I printed no environment variables, tokens or credential files. The `gh api` GETs were filtered to sha and date, and no email field was requested. One slip: `git show --stat 0737d573` printed the commit's Author line, which contains the owner's email, into my local tool output. It is not repeated here and was not sent anywhere. Driving the real relay also started canopy's control-stream supervisor, which tried and failed to connect to 127.0.0.1:9; no Juniper port was touched. Nothing was written to any repo: the worktree status is unchanged, and the canopy and cascor log files that changed during the lane contain no entries from my runs.

---

## Lane 10-B1 - adversarial, dispositions and ratings

*agent `a26e98c2b32869bdd` · round 1 · last-assistant-text (not resumed) · 11194 chars*

**VERDICT:** SOUND-WITH-FIXES. Of the ten dispositions, nine hold. One rating is wrong: F-CANOPY-065 should be P1. F-CANOPY-064's record leaves standing a PASS that the arc's own evidence refutes. Three smaller fixes concern rationale and actions.

Abbreviations: **Ledger** = `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `0737d573`. **Matrix** = `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`. **Plan** = `JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md`. Every canopy, cascor and juniper-data path is read at the brief's pinned commits.

**PER-ITEM TABLE**

| Item | Ledger | Mine | Evidence |
|---|---|---|---|
| F-060 | P2 OPEN | P2 OPEN (finding 4) | Reachable from the UI only if the operator lowers the rendered `max_symbols` below the seed's 5 symbols. All three staging paths send the seed: `dashboard_manager.py:3396`, `:7085` (both through `:3464`), and `:6638`; the seed itself is `model_registry.py:267-277`. Refusal logic: data `generator.py:507-512`, `:730-740`. P1 rejected: the counts the CHANGELOG promises do reach the modal, and Accept's text already says "permanently annotated as partial" (`:8442`). |
| F-061 | P2 FIXED | P2 FIXED, exemption to be stated (finding 3) | Verified `main.py:517` at `7ab994e5` → `:532`; `dc5ea02e` is an ancestor of `1b2dd438`. A copy of the same rule remains at `internal_api.py:91-92`, acknowledged in `security.py:94-97`. That is outside F-061's scope. |
| F-062 | P2 FIXED | same as F-061 | Verified `security.py:391`, `:497`, `test_security.py:700`. Filing with ids is right: the ids were reserved and are cited elsewhere. |
| F-063, test half | P2 OPEN | P2 OPEN | The drift is real (`test_start_fresh_refusal_and_modal_text.py:41-42` against cascor `manager.py:4841`). It is "drift" on plan §6.3. It masks nothing, but item 23 needs the id. |
| F-063, alert half | declined | declined | No canopy start path sends tensors. For cascor, `start_kwargs={}` (`main.py:1063`, `:3726`); restart passes `reset`/`start_fresh` only (`:3947`); the adapter posts with no kwargs (`cascor_service_adapter.py:1110`, `:1112`); `inline_data` appears nowhere in `src/`. The first start stages a dataset, it does not bind one (`service_backend.py:184-202`). |
| F-064 | P1 OPEN | P1 OPEN (finding 1) | **P0 rejected:** nothing is blocked, and F-055 (front-page status bar frozen) is P1. **P2 rejected:** zooming cannot recover a curve. A probe at canopy's default 500-row window, with cascor's labels (`manager.py:2087-2115`, `:2144-2150`), gives 0 accuracy points during growth and 1 after a run (x=11). The same holds at `output_epochs=25` (axis 1..25). The cause is chiefly accuracy keyed on `phase` (`metrics_panel.py:2264`), not the budget. The probe's 4,422 rows match the A-N2 archive. **Tile half is real:** its only writer is `metrics_panel.py:958-981`; the store is fed by REST (`:476`, `kind` stripped) and the WS append (`:7813-7834`, relay `:778`); `training_state.current_epoch` is only a fallback (`:1667`) and is never used once `kind` is gone; the probe's tile reads 2501 mid-pass. Treating the labelling as a cascor question is correct: cascor's schema defines `phase` only as "output"\|"candidate" (`API_SCHEMAS.md:346`). |
| F-065 | P2 OPEN | **P1** OPEN (finding 2) | Mechanism verified. The ack nests the partition at `data.result` (`messages.py:193-198`), and the client returns the whole envelope (`ws_client.py:728-729`). The extractor scans only the top level and `data` (`cascor_service_adapter.py:1439-1442`). The toast then falls through to "Parameters applied" (`dashboard_manager.py:9140-9145`). |
| F-066 | P2 OPEN | P2 OPEN | Fallthrough at `main.py:1613-1626`. The failure stays in the details output (`dashboard_manager.py:7665`). Recurrence is documented (`USER_MANUAL.md:260-262`; W8), but nothing documents the details panel under it. The 80 WARNINGs re-count to 80. |
| O4 | declined | declined | `JuniperCanopy1` metadata says 0.6.0 and is an editable install of the primary checkout. The image runs `pip install --no-deps .` (`Dockerfile:48`), so images and wheels report pyproject's version. The fallback is pinned to pyproject (`test_obs1_about_version_single_source.py:38-41`). `APP_VERSION` feeds only display and telemetry. |
| O9 | declined | declined | U-6 was specified as following the selected type (`JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md:289`; canopy `CHANGELOG.md:1910-1912`). No document promises "loaded". C4 exists in `HANDOFF_2026-10-03_canopy-consolidated.md:108`, `:379`. |
| Counts | 77 / 53 / 1 / 2 / 21; 6 P1, 15 P2 | Reproduced exactly | Ran the frozen `e2e_finding_triage.py` on the frozen Ledger. With finding 2 applied: 7 open P1, 14 open P2. |
| Still owed | items 7, 16, 18-23 | Mostly follow | Gaps in finding 5. |

**FINDINGS**

1. **MAJOR — F-064 refutes a standing PASS that Phase 10 leaves in place, and its provenance understates.**
   - Ledger text: "observed 2026-09-23 by the canopy selection arc's A-N2 run as its O2" (Ledger:9929) and "No matrix row changes, because nothing was driven." (Ledger:10082).
   - Evidence: the arc's own Phase 1 run `reports/e2e/20260810T002233Z/M-METRICS-29__post-run-plots.png` shows the same chart: a 0–10k axis, one marker cluster at x≈11 under "+Unit #10", no accuracy line, beside Accuracy 98.75% and Training Step 11.
   - The same run's `statuses.tsv:81` scores `W1-01..11 PASS`. That range includes W1 step 9, "loss and accuracy plots accumulate points" (Matrix:972), and no later run re-scores it.
   - `statuses.tsv:75` passes M-METRICS-30 on "accuracy plot 6 traces", a trace count taken over that empty chart.
   - Fix: record the chart half as present since at least 2026-08-10. Record W1-09 as FAIL (F-CANOPY-064) from that archived capture; no drive is needed. Drop the "default budgets" scoping, since it holds at any budget.
   - Changes a number, disposition or action? **Yes**: a recorded verdict and the finding's provenance. The P1 rating is unchanged. Overturning a recorded PASS is an escalator under §3 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

2. **MAJOR — F-065 should be P1.**
   - Ledger text: "**Severity: P2**, drift. The values land, and the manual documents no applied or skipped list." (Ledger:10018).
   - Evidence: canopy `CHANGELOG.md:1975-1980`, released under `[0.6.0]` (`:1786`), says "the toast shows what the live network took vs. declined with the reason (e.g. `epochs_max (not-updatable)`)", with "REST-nested and WS-flat shapes both handled". The design plan says canopy renders both sets (`JUNIPER_2026-07-11_JUNIPER-CANOPY_TRAINING-RUNTIME-DEFECTS-PLAN.md:311`).
   - On the default WS leg that exact example never appears: `settings.py:347` is True and `epochs_max` is a hot param (`cascor_service_adapter.py:1240`).
   - The Ledger already counts non-manual canopy documents. F-057 is P1 on the manual plus a FAQ, and "returns to P2 when the … follow-up that corrects both files merges" (Ledger:9110-9115).
   - Counter-reading: Plan:741 (A-2) names only USER_MANUAL and REFERENCE. If that reading is adopted, the Ledger must say so, and it undercuts F-057's basis too.
   - Fix: re-rate P1 (open P1 6→7, open P2 15→14), and update the Summary and the counts.
   - Changes a number, disposition or action? **Yes**.

3. **MINOR — F-061 and F-062 are FIXED on merge alone, against the Ledger's own discipline, with no reason given.**
   - Ledger text: "FIXED by canopy#685, merged 2026-09-24 as `dc5ea02e`" (Ledger:9871, :9884).
   - The discipline: "stays OPEN with a fix-merged rider until the post-T6 live re-drive" (Ledger:5823-5825; also :6154-6155, :9020, :9207).
   - Fix: state the exemption in both entries. Neither was ever observable in E2E, neither has a matrix row, and each is verified by the source diff plus a pinning unit test. The alternative is to hold both OPEN (fixed 53→51, open 21→23).
   - Changes a number, disposition or action? **No**, if the exemption is recorded.

4. **MINOR — F-060's severity basis cites a retired route and a wrong omission.**
   - Ledger text: "A request without a symbols list … the restart modal's old re-stage" (Ledger:9843-9844) and "What is missing is the permanence notice" (Ledger:9865-9866).
   - Evidence: every canopy staging path now sends the seed's 5 symbols (see the F-060 row). The live route is the operator lowering the rendered `max_symbols` below 5 (`dataset_schema.py:105-149`), or a deployment ceiling below 5. Accept's text already states permanence (`dashboard_manager.py:8442`).
   - Fix: replace the route, and drop "the permanence notice" from what is missing. P2 stands.
   - Changes a number, disposition or action? **No**.

5. **MINOR — The fixture class's actions do not follow from the dispositions.**
   - Ledger text: "Item 16 is DONE (2026-10-04)." (Ledger:10093) against "records no sweep" (Ledger:9921). The sweep is defined as a grep for claim text (Ledger:9924-9927).
   - Problem: the class as the Ledger counts it includes fixtures whose shape is wrong but which carry no claim text, and a claim-text grep cannot find them. Two examples:
     - the N6 fixture (`test_n6_counter_semantics.py:45-55`), which the Ledger itself lists;
     - the N5 WS-ack fake (`test_n5_apply_params_ux.py:309`), which is flat while the real envelope nests the partition. It masked F-065, and the extractor's docstring makes the same false "flat" claim (`cascor_service_adapter.py:1429-1430`).
   - Neither F-065's entry nor item 20 names the N5 fake, whereas item 18 does correct N6's fixture.
   - Fix: say item 16's sweep moved to item 19; define that sweep as comparing each fixture to the live shape; add the N5 fake and the docstring to item 20.
   - Changes a number, disposition or action? **Yes**: actions.

**WHAT YOU COULD NOT CHECK**
- No live drive was possible (read-only brief). The empty chart during a run and the mid-pass tile reading come from source plus executed code. Every archived capture was taken after its run finished.
- The `phase` labels on cascor's step rows 1..N-1 are source-derived; I did not read the event order in model-core's `CascorModel.fit`, and the archives are slimmed. My probe's row count and its final `output` row do match A-N2.
- Whether a CHANGELOG or design-plan promise counts as "documented" under plan §6.3 is for the reconciler or the owner to decide.
- The 2026-08-10 capture is cropped below about 90% of the chart.
- One lead, outside scope and not driven: the clientside `extendTraces` path (`metrics_panel.py:1015-1143`) reads flat `e.loss` and `e.accuracy`, while the relay delivers nested rows (`ws_dash_bridge.js:249`). In service mode it therefore appends nothing.
- I did not run the Ledger's F-060 or O3 instruments, and made no GitHub calls.

**SECRETS/PII:** No environment variables, tokens or credential files were printed or read, no email was requested or sent, and no slips occurred. I wrote no repository file. Scratch files are under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/lane10B1.8nGM/`: `o2_window_probe.py`, `crop.py` and `meta_check.py`.

---

## Lane 10-B2 - adversarial, claims beyond evidence

*agent `af49f9902414f16db` · round 1 · last-assistant-text (not resumed) · 12871 chars*

**VERDICT: SOUND-WITH-FIXES**

**FINDINGS**

1. **MAJOR. F-CANOPY-064's claim that every relay path drops `kind` is false.**
   - **Quoted:** "That is every path: the history fetch (`:463-479`), the WS relay (`:778`) and `/api/state`'s sync … No consumer downstream can tell the numberings apart." Also "builds its `output_epoch` rows with a `kind` key that the relay never delivers" (the same claim appears again in F-CANOPY-063's class bullet), and "went through canopy's real relay and panel".
   - **Evidence, source:**
     - The relay normalizes only frames where `msg_type == "metrics"` (`cascor_service_adapter.py:774-780`). Every other frame type is broadcast untouched.
     - cascor sends an `initial_metrics` burst of raw monitor rows on every fresh `/ws/training` connect (`training_stream.py:282`, `:300`, `:111-123`; 100 rows by default, cascor `settings.py:382`). There is no override in juniper-deploy `origin/main`. So the burst arrives on every relay connect, at startup and at each reconnect.
     - The browser bridge pushes those rows raw into the metrics buffer (`ws_dash_bridge.js:261-270`), and the store append keeps any dict (`dashboard_manager.py:7829-7834`).
   - **Evidence, executed:**
     - I ran canopy's real `start_metrics_relay` loop against a fake stream. The frames came from cascor's real `TrainingMonitor` and message builders.
       - The relayed `metrics` frame lost `kind`.
       - The 4 burst rows kept `kind` (`output_epoch`, `output_epoch`, `training_step`, `output_epoch`), with a flat `loss` and no nested `metrics` dict.
     - With the burst rows in the store:
       - The Training Step tile read `'1'`, against `'2501'` from the relayed `metrics` frame.
       - The loss values were `[0,0,0,0]`.
       - Accuracy trace 0 was `[0,0,None,None]`.
     - I ran the real `websocket_client.js`, `ws_dash_bridge.js` and the `extendTraces` callback (`metrics_panel.py:1015`, which reads flat `e.loss`/`e.accuracy` at `:1032-1037`) in node.
       - The relayed `metrics` frame extended nothing.
       - The burst rows extended loss trace 0 with x = `[1,26,1,2501]` and accuracy trace 0 with y = `[0,0,0.6,0]`.
     - The o2 instrument's "real relay" is only the two normalizer functions, not the relay loop.
   - **Replacement:** "The history fetch, the relay of cascor `metrics` frames (`:778`) and `/api/state`'s sync rebuild rows without `kind`. The relay forwards cascor's `initial_metrics` burst (up to 100 rows, on every relay connect) untouched (`:774-780`). Those rows keep `kind` but lack the nested `metrics` dict, so the store-driven charts read their loss and accuracy as 0. The clientside `extendTraces` path keys on neither `kind` nor `phase`, acts only on flat-keyed rows, and plots both numberings on trace 0. No path delivers rows in the dashboard shape with `kind`, which is the shape N6's fixture builds."
   - **Fix direction and item 18 should add:** normalize (or drop) the burst in the relay, align the `extendTraces` callback, and include a relay reconnect in the live re-drive.
   - **Changes a number, disposition or action?** Number no, disposition no, action **yes**.

2. **MINOR. F-CANOPY-065 misdescribes the apply toast.**
   - **Quoted:** the title's "and the toast built from it, omits every key sent over `/ws/control`", and "The toast lists only REST-routed keys as applied".
   - **Evidence:**
     - `_compose_apply_toast` (`dashboard_manager.py:9091-9145`) never lists applied keys. `applied` only feeds a count, and only when `skipped_detail` is non-empty (`:9140-9144`). Otherwise the toast reads "Parameters applied" (`:9145`).
     - Executed on the archived A-N2 answer (`02_gaussian/03_set_params_caps.json`): `'Parameters applied'`.
     - With the partition the WS ack carried: `'Applied 4 parameter(s); 1 skipped: nn_max_total_epochs (not-updatable)'`.
   - **Replacement:** "The toast lists no keys. It reads 'Parameters applied' unless a skip partition reaches it, which is exactly what the A-N2 answer gives. So a key cascor declines on the WS leg is never reported, and when the REST leg reports a skip, the applied count leaves out the WS keys." Reword the title the same way.
   - **Changes a number, disposition or action?** No.

3. **MINOR. F-CANOPY-064's "sliver" explanation contradicts the entry's own labelling paragraph and the archived capture.**
   - **Quoted:** "Accuracy therefore sits at x = 1…N, the steps" and "The accuracy sliver's width is the step count over that budget, so it narrows as the budget grows."
   - **Evidence:**
     - The chart keeps accuracy only on rows whose phase contains `output` (`:2264`). By the entry's own labelling analysis, step rows drained during growth carry `candidate`. By the same source, the only `output` step row in a growth run is the last one, drained at `:2150`.
     - The capture used canopy's default Sliding Window of 500 rows (`canopy_constants.py:511`; the image shows "Window: 500").
     - Each pass contributes 401 sample rows (4,422 = 11×401 + 11), so that window holds only steps 10 and 11.
     - The PNG crop shows one marker cluster at x ≈ 11 and about 96%. There is no sliver.
   - **Replacement:** "Whatever accuracy reaches the chart sits at x ≤ N, on an axis that runs to the inner-epoch budget. In the archived capture it is one point, at x = 11." Drop the sliver sentence.
   - **Changes a number, disposition or action?** No.

4. **MINOR. F-CANOPY-060's analysis of the prompt's options, and its fix direction, are overstated.**
   - **Quoted:** "For a cap refusal, either one imports the first 14 symbols." / "A cap refusal has no broken rows and no placeholder values." / "or key the copy on the class".
   - **Evidence (source-read):**
     - Accept and Drop both send `allow_truncation: True`, with `incomplete_rows` set to accept or drop (`dashboard_manager.py:546-547`).
     - juniper-data applies the cap at `generator.py:314`, then runs `_apply_incomplete_policy` on the kept symbols at `:338`, using the same flag (`:544-548`).
     - So after a cap refusal, Accept keeps any unresolvable symbol among the 14 with fill values, and Drop removes it — exactly what the options say.
   - **Replacement:** "Both import at most the first 14 symbols. The choice then decides, as for a shortfall, whether any of those the producer cannot resolve are kept with placeholder values or dropped. The options never mention the cap."
   - **Fix direction:** word each option for both cases (the cap, then accept or drop), and do not key away the accept/drop distinction for a cap refusal.
   - **Changes a number, disposition or action?** Action **yes**.

5. **NIT. F-CANOPY-060's prompt-text claims.**
   - (a) "is the only text that says what accepting does". The Accept option itself says "train on the partial dataset as delivered … permanently annotated as partial" (`:8442`). Replace with "the only text that says what accepting imports (the first 14 symbols)".
   - (b) "What is missing is the permanence notice". The same line carries canopy's own run-level permanence notice. Replace with "juniper-data's dataset-level permanence sentence, and any mention of the cap".
   - (c) "so it is refused unless an opt-in is sent". When the request omits the flag, `_resolve_bounds` (`generator.py:505-512`) applies the deployment's own opt-in and ceiling. Replace with "so, at juniper-data's defaults, it is refused unless the request opts in".
   - **Changes a number, disposition or action?** No.

6. **NIT. Execution labels claim more than ran.**
   - (a) The Summary says "Where a function could be lifted out, it was also executed". cascor's `TrainingMonitor` and canopy's static `_compose_apply_toast` both lift out and run (I executed both here). Yet F-CANOPY-064's labelling half is marked not executed, and F-CANOPY-065's toast claim was not executed (and is wrong, finding 2). Replace with "For F-CANOPY-060, F-CANOPY-064's tile and F-CANOPY-065's extractor, the functions were also executed; the rest is source-read."
   - (b) "Rows built as cascor's monitor builds them". The o2 script's `synthetic_run` (`:76-79`) labels every row `phase: "output"`, which contradicts the entry's own labelling paragraph. The tile result does not depend on phase, but the accuracy-chart extents the script prints (x 1–3, n = 3) are artefacts of that labelling. Replace with "rows with cascor's keys and numbering (all labelled `output`) went through canopy's two normalizers and its real panel".
   - **Changes a number, disposition or action?** No.

7. **NIT. Fixture-sweep bookkeeping.**
   - (a) "Item 16 is DONE (2026-10-04)", while item 19 still owes "the rest of item 16's fixture sweep" and F-CANOPY-063 says canopy#694 "records no sweep" (confirmed from #694's body). Replace with "DONE except its fixture sweep, which moves to item 19".
   - (b) "finds nine claim-bearing comments" is not reproducible as stated.
     - `grep -rni` gives 11 lines. Excluding `test_f059_replay_range_dict.py:14` and `test_p2_wave_batch_a.py:181`, which only quote an old claim, leaves 9.
     - A case-sensitive grep also gives 9 lines, but includes those two and misses `test_stage2_global_lane.py:339` and `test_f035_candidate_loss_from_history.py:139`.
     - State the grep flag and list the nine.
   - **Changes a number, disposition or action?** No.

**CLAIMS YOU ATTACKED THAT SURVIVED**
- **"Only step rows carry accuracy":** the only row writers are `manager.py:2058-2065` (accuracy `None`) and `:2386`.
- **cascor labelling paragraph:** CCN's grow callback (`cascade_correlation.py:4860`) fires before the retrain. The only other drains are `:2150` and `:3029`, and the only other phase setter is `:2988`, at run start. The source also predicts that only a run's last step row is `output`; the ledger understates this.
- **"Candidate Training" trace plots output-retraining loss:** confirmed on the store-rebuild path.
- **Tile 2501 vs 3:** reproduced. Archive slices (first 3 rows, last 20, count 4,422) re-read and correct.
- **F-CANOPY-060 cut and fix:** both modes reproduced. "Producer detail:" and "To accept it," were introduced together in cascor `58a0d42`, so the proposed fix cannot leak cascor's closing sentence on an older cascor. The second stop can fire only inside juniper-data's text. There are 503 constituents.
- **"No production caller passes tensors":** start calls pass only reset/start_fresh (`main.py:1064`, `:3727`, `:3947`), and `inline_data` appears nowhere in canopy's source.
- **cascor#690:** merged 2026-09-25T02:06:36Z as `0fbb447a`; the cited test exists.
- **"A-N2's answer exactly", including `skipped`:** the archived answer has no `skipped`/`skipped_detail`, the route omits empty lists (`main.py:4410-4417`), and the instrument's arm gives `skipped=[]`.
- **"The WS leg is the default":** no override in canopy's tree or juniper-deploy `origin/main`, and the archived log shows the WS leg was used.
- **F-CANOPY-066 "every slow tick":** the only Input is the slow interval, the details call is unconditional (`dashboard_manager.py:7665`), 80 warnings re-counted, and only recurrence falls through to 503.
- **Archived handoff banner:** `dd4413e5` is the branch tip and is not an ancestor of `0737d573`; the consolidated handoff names it predecessor A; below the banner the file is byte-identical (cmp) to both the branch copy and `main`'s frozen copy.
- **Counts:** the triage tool on a frozen copy gives 77/53/1/2/21, no open P0, the six named P1s, 15 P2.
- **Other entries:** O4 confirmed (installed metadata 0.6.0, editable from the primary checkout). F-CANOPY-061/-062 lines and PR rows correct. All three instruments ran and reproduced the ledger's outputs. Every cited line number checked out.

**WHAT YOU COULD NOT CHECK**
- **No live stack or browser:** the burst path ran on a fake stream and in node with inert WebSocket/XHR stubs. How often a relay reconnect lands while a dashboard is open was not measured.
- **Finding 4 is conditional:** whether any of the first 14 symbols is unresolvable needs juniper-data's network fetch.
- **CCN event order is source-read:** `_handle_event` was not executed, though `TrainingMonitor` was.
- **The single accuracy point:** this is a visual read of a crop of the PNG.
- **Deployed-host `.env` files** were not checked.

Probes, all in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/lane10B2.eZmWfY/`: `probe_relay.py`, `probe_bridge.js`, `probe_toast.py`.

**SECRETS/PII:** No environment variables, tokens or credential files were printed or read, and nothing was sent anywhere. The GitHub calls were `gh pr view` reads with no email field requested. **One slip:** `git show --stat dd4413e5` printed that commit's author line, which contains a personal email address, into my local tool output. It is not repeated here and was not sent.

---
