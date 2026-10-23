<!-- markdownlint-disable -->

# Canopy E2E ledger Phase 15 — validator report, round 2 (2026-10-21)

Round 2 was one lane: Lane 15-B (adversarial analysis), re-run on the round-2 freeze f65541a5 after its round-1 spawn died on an API usage-credit error, with its brief revised in place (reports/e2e-canopy-2026-09-02/drafts/lane15B_phase15_ledger_brief.md). The archive tool labels the section 'round 1' because this agent was never resumed; it is the procedure's round 2. Archived verbatim by util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py.

## Lane 15-B — adversarial analysis and the handoff (round 2)

*agent `ac0bc584027937f4a` · round 1 · last-assistant-text (not resumed) · 38273 chars*

# Lane 15-B (round 2): adversarial review of the canopy E2E ledger's Phase 15 and its handoff

**Verdict: SOUND-WITH-FIXES.**

The dispositions stand: F-CANOPY-069 is FIXED at P0 and F-CANOPY-028 is FIXED at P1. Both headers carry the right tokens, and the counts are right: 80 / 63 / 1 / 2 / 14, with 0 P0, 4 P1 and 10 P2.

There are five MAJOR defects:

1. The phase explains why F-CANOPY-028's race was not re-created by saying the renderer holds the click's writer. The phase's own request bodies and the dash renderer contradict that. The stated "click times" are the driver's decision times, not the clicks.
2. Item 31b's new sentence in canopy's manual is wrong for three of the four patch targets.
3. The handoff leaves out ledger items 18 to 21, which include two of the four open P1s.
4. Item 33's owner action does not do what it says.
5. Item 27 is described as clicking through the Live Switch modal, and its drive never does that. So nobody owns F-CANOPY-069's gated-modal click-through.

Each of the five changes an action or an item. Under the procedure's termination rule, round 3 is therefore required.

**What I reviewed**

- **Worktree HEAD:** `f65541a547c81f874a5e45c17b31e953f26edca6`. The base is `907b6b3e`. `git status` shows only the untracked `item31-turing/shots/`.
- **Replay of the passes:**
  - I ran `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py --ref 907b6b3e` with its out-root in my scratch directory.
  - That replays the apply pass and round 1's corrections from the base.
  - It reproduces all six shared files byte for byte, so there are no hand edits.
- **juniper-ml `main`:** `d9b29f38` (#2297). None of the six shared files has changed since the base.
- **canopy `main`:** `aeeaf29b` ← `fbf01dff` ← `571743db`.
- **Ground rules:** I wrote nothing in the worktree and started no leg or service. Scratch is under `/private/tmp/claude-501/lane15B2/`.
- **The report file:** my working notes are in `/private/tmp/claude-501/lane15B2/REPORT.md`. The tool refused the final whole-file write of this report there, so this message is the complete report.

## Per question

### F-CANOPY-069

1. **Both members run; the phase's run is opener-first; Lane 15-A's two runs are inverted with the alert left open.** AGREE.
   - The phase's run is `item32-turing/pair_members.json`, label `dash-4.4.1-571743db`:

     | Pair | Member | Request | Answer |
     |---|---|---|---|
     | Restart | Opener | +0.283 | +0.638 |
     | Restart | `execute_restart` | +0.284 | +2.61 |
     | Live Switch | Accept | +0.173 | +0.926 |
     | Live Switch | Opener | +0.174 | +0.708 |

     The alert's life in the DOM was 155 ms for the Live Switch and 1.906 s for the restart.
   - Lane 15-A's runs are `lane15A_pair_members.json`:
     - The worker answered at +0.155 against the opener's +0.156, and at +0.286 against +0.287 (response orders 243/244 and 250/251).
     - `alert_after` is present, with class `fade alert alert-info show` and text "Swapping dataset…Cancel".
     - The demo swap took 41 ms and 38 ms.
     - The restart workers answered at +1.251 and +1.309.
   - One clause is not supported: see MINOR 1.
2. **"Nothing else closes it."** AGREE.
   - At `571743db`, `src/frontend/dashboard_manager.py:2291-2307` has the alert at `dismissable=False`.
   - Its only `is_open` writers are `:6313` and `:6335`, the two members of the pair.
   - `cancel_live_switch` (`:6344-6350`) writes only `live-switch-outcome-alert.children`.
   - No JS asset names the id.
3. **The `running=` idiom and the ordering.** AGREE.
   - In dash 3.3.0, `_callback.py:120-125` does not restrict `running` to background callbacks, as it does `cancel`, `progress` and `progress_default`. It is wired at `:627-652`.
   - Both `handleServerside` implementations dispatch `sideUpdate(running.running)` before the fetch.
   - Both run `completeJob()`, which applies `runningOff`, before `finishLine`. They do so on OK, on PREVENT_UPDATE and on error.
     - dash 3.3.0: `dash_renderer.dev.js:76272-76448`.
     - dash 4.4.1: `:856-1037`. Its WebSocket path (`:1065-1170`) uses the same order.
   - The 3.3.0 renderer validates unconditionally, and it accepted the fix's graph: the leg was ALIVE.
4. **The F-CANOPY-058 distinction.** AGREE. `live-swap-in-flight-store` has no reader at `fbf01dff` or `aeeaf29b`, so an evicted accept can only close the spinner early.
5. **Floor `dash>=4.0.0`.** Defensible. But the counter-position lives in canopy#760's body, not in the ledger, and the new floor is itself untested (MINOR 6).
6. **The conda lines.** AGREE.
   - conda-forge has `noarch/dash-4.4.1-pyhd8ed1ab_0` (2026-07-22). It depends on comm, flask>=1.0.4, importlib-metadata, janus>=1.0.0, nest-asyncio, plotly>=5.0.0, pydantic>=2.10, python>=3.10, requests, retrying, setuptools, typing_extensions>=4.1.1 and werkzeug.
   - `comm-0.2.3-pyhe01879c_0` and `janus-2.0.0-pyhd8ed1ab_0` both exist.
   - The file at `fbf01dff` already satisfies every other run dependency. setuptools is present only as a pre-existing `80.9.0=pypi_0` line.
   - The lock has comm 0.2.3, dash 4.4.1 and janus 2.0.0.
   - The lock diff from `571743db` to `fbf01dff` is exactly certifi, fastapi, pydantic-settings, setuptools, starlette and websockets. That is commit `a8b519c1`, signed.
   - "Two new" dependencies is really three (MINOR 5).
7. **179 callbacks; 9 tests with 7 failing on `571743db`.** AGREE.
   - All four fix legs serve 179 callbacks and the parent serves 181: the two openers are gone.
   - I read the test file rather than running it. On `571743db` the two that pass are `test_callback_map_and_served_list_agree` and the scratch-app scan. The first passes because `callback_map` is keyed by the full output string, and the pair members' strings differ.
   - canopy#760:
     - 3 signed commits, with six `Allow-Symbol-Loss` trailers on `04842906`.
     - 21 required contexts in the ruleset, all passing.
     - Post-Merge Main Verification green on `fbf01dff`.
   - canopy#761:
     - 2 signed commits on `fbf01dff`.
     - 21 required contexts, all passing.
     - Post-Merge Main Verification green on `aeeaf29b`.
   - Releases: v0.9.0 is Latest, and PyPI's 0.9.0 still requires `dash>=3.0.0`.
8. **Header.** AGREE. The first severity token is P0, and the last 170 characters carry FIXED with no OPEN, ACCEPTED or WITHDRAWN.

### F-CANOPY-028

1. **The mechanism as restated.** AGREE.
   - At `571743db`, `update_parameters_tables` (`parameters_panel.py:252-276`) re-renders all three tables from its pin Input. That is 8 + 4 + 10 = 22 boxes.
   - `_build_table` sets `value=key in pinned_set` (`:118-119`).
   - The old `_merge_pinned_params` (`dashboard_manager.py:7320-7348`) lets each rendered box decide its own key.
   - The `early#2` bodies in `item30-turing/demo_leg_8062_dash441.json` (`f028.arms["early#2"]`):
     - [2] is the mount: 22 inputs changed, `learning_rate` checked.
     - [4] is the click: 1 input changed, both checked.
     - [5] is the rebuild: 22 inputs changed, only `learning_rate` checked, State `["max_iterations","learning_rate"]`.
   - The old merge returns `['learning_rate']` on [5]. `_apply_pin_toggle` returns no_update, then `["learning_rate","max_iterations"]`, then no_update.
   - The blockquote's "stale input Phase 14 recorded" is actually the unit test's synthetic input (MINOR 3).
2. **`_apply_pin_toggle` and multi-input actions.** AGREE.
   - At `aeeaf29b` (`dashboard_manager.py:7318-7350`) it does what the blockquote says. It also returns no_update when the toggled key is not among the ids, and it drops falsy stored keys.
   - One user action means one pin input:
     - `parameters_panel.py:118` is the only place boxes are created.
     - No callback outputs a `param-pin` value.
     - dash 4.4.1 merges duplicate writer calls only within one requested batch. It drops an initial-call duplicate, and a newer request supersedes a prioritized or executing one (`dash_renderer.dev.js:3187-3245`, `:3379`).
   - Lane 15-A's fix arm `early#1` has only two firings. It is the one drive where a click met the second render, and the pin was kept.
   - There is a residual the phase does not state (MINOR 11).
3. **The adapter matches `dash.ctx.triggered_prop_ids`.** AGREE.
   - `callback_context.py:122-137`, unchanged since `571743db`, returns `dict(dash.callback_context.triggered_prop_ids)`.
   - dash 4.4.1 `__init__.py:48` sets `ctx = callback_context`.
   - In both dash lines, `_callback_context.py:88-117` maps pattern ids to `AttributeDict(json.loads(id))`, which is a dict.
   - Test mode yields `{trigger.n_clicks: 1}`, which `_apply_pin_toggle` ignores.
   - Every fix drive wrote the click through the real adapter.
4. **Is "not re-created live" stated honestly?** Yes: in Phase 15, the blockquote, "cannot support", the handoff and the INDEX.
   - **The account of why:** DISAGREE (MAJOR 1).
   - **Figures:** AGREE.

     | Measure | Value |
     |---|---|
     | Parent drives surviving | 14/14 + 6/6 + 6/6 = 26 |
     | Second render after the mount | 6.64–9.04 s |
     | Click's writer after the second render | 0.58–9.55 s |
     | Settled pin step | 26.6–29.9 s |
     | Click's writer after the second render, over the twelve | 18.3–23.6 s |
     | Fix drives surviving, all settling `["learning_rate","max_iterations"]` | 6 + 6 + 6 + 7 = 25 |
     | Second pin, early/mid arms on the fix | 2.3–2.9 s and 9.4–10.8 s |
5. **Is FIXED right on one recorded loss and a unit test?** AGREE.
   - By construction, no call with two or more triggered ids writes.
   - The real `early#2` third body maps to no_update.
   - The live drives are a regression check only, and the ledger should say so (part of MAJOR 1).
   - M-PARAMETERS-06 was not driven at all in this phase (MINOR 4).
6. **Header.** AGREE. The first severity token is P1 and the tail carries FIXED.

### Item 31b (the manual)

DISAGREE (MAJOR 2).

- **For `output_weights` the new sentence matches the code.** I extracted `_resolve_patch_values` and `_parse_float_rows` from `aeeaf29b` and ran them:
  - Newlines or semicolons separate rows.
  - A flat comma- or space-separated list is reshaped from the topology.
  - `1;2;3;4;5;6` becomes 6×1 rows, which cascor refuses on any network with more than one output.
- **Its first clause is false for the other three targets.** "Values are floats separated by commas or spaces" fails for `output_bias`, `hidden_unit_weights` and `hidden_unit_bias`.
  - Those go through `_parse_float_list` (`network_editor_panel.py:418-434`), which splits on commas, semicolons and newlines only.
  - `output_bias` with "0.1 0.2" raises `ValueError: could not convert string to float: '0.1 0.2'`, which the panel shows as its status alert (`:854-856`).

### Counts and items

- **Triage.** AGREE.
  - 80 / 63 / 1 / 2 / 14 with no P0 line.
  - Open P1s are F-CANOPY-064, -065, F-CASCOR-001 and -002; open P2s number 10.
  - `--open-only | grep -c '^OPEN   P1 '` gives 4.
- **Item 33.** Scoping it as the owner's is right: it changes host environments on turing and needs an erratum in the turing plan. Its recipe is wrong (MAJOR 4).
- **"Still owed" against Phase 14's list.** Items 25, 27, 28, 29 and 26's second step are carried. "Items 31 and 32 are DONE" overstates item 31 (MAJORs 1 and 2).
- **Round 1's "changed one action's parameter."** That is the right call. An action changed, and §4 of the procedure requires a second round after any correction anyway. The item-27 change, though, comes from no round-1 report (MINOR 7).

### Round-1 record against the reports

AGREE, with three overstatements (MINOR 7):

- Lane 15-C's 1 MAJOR and 9 MINORs are listed correctly.
- Lane 15-A's step summaries match its interim status and checkpoint notes.
- The corrections check out. I ran both canopy apply scripts with `--check` against the `-f028` tree, which equals `aeeaf29b` except `requirements.lock`, and they print `done` on every step.

### The handoff

**(a) Remaining work.** These are missing:

- Ledger items 18–21 (MAJOR 3).
- F-CANOPY-069's click-through and the restart confirm (MAJOR 5).
- Item 31b's follow-up (MAJOR 2).
- The MEMORY.md update (MINOR 8).

Everything else is present:

- landing the PR
- items 27, 25, 28, 29, 33 and 26's second step
- the canopy release (owner, P4)
- the cleanup of trees, worktree and local commits
- the parent's items 5 and 7, and O1–O17

The parent's item 6 is moot: MEMORY.md is 5,958 bytes.

**(b) Verification block.** Every command prints what its comment says. `python3` resolves to JuniperPython.

| Command | Output |
|---|---|
| `git log --oneline -3` | `f65541a5`, `6f933d07`, `907b6b3e` |
| `gh pr list … --head docs/canopy-e2e-phase15` | `[]` (expected before landing) |
| triage tail | 80 / 63 / 1 / 2 / 14 |
| open-P1 count | 4 |
| `grep -c '^## Phase 15'` | 1 |
| `gh pr view 760` / `761` | MERGED `fbf01dff` / MERGED `aeeaf29b` |
| `gh release list` | v0.9.0 Latest, 2026-10-17 |
| fix matrix check | two ALIVE |
| stuck-spinner check | True, True on the parent labels; False, False on the fix |
| `ls` of the venvs | the seven entries the comment names |
| `lsof` with the port pattern | nothing |

**(c) Claims.**

- **Completed:** AGREE except the F-028 wording (MAJOR 1).
- **Traps:**
  - The hold trap is wrong (MAJOR 1).
  - `--expected-head` belongs to `push_signed_commit.py` (MINOR 9).
  - The others check out:
    - The symlinks: root `requirements.txt` is mode 120000 with blob `dea8025a`, which the contents API reports as `file` of size 6095. `conf/requirements.txt` is a 19-byte link.
    - `--marker` exists.
    - Leg 8084 ran from 16:19 to 01:21.
- **Git state:**
  - My blob check (`/private/tmp/claude-501/lane15B2/blob_f028_vs_aeeaf29b.json`) shows `-f028` equals `aeeaf29b` on 15 files, with only `requirements.lock` different.
  - Both canopy fix branches return 404, and nothing is listening.
- **Changed list:** All 46 files in `git diff --stat 907b6b3e` are named. The entries that will be true only at landing are not marked (MINOR 8).

**(d) Banner, parent pointer and INDEX row.** They agree with the handoff and the ledger. I checked the mapping against the Phase 14 handoff's items 1–7. All three inherit the missing items 18–21 (MAJOR 3).

### Secrets and names

AGREE.

- I ran a masked scan of all 46 changed files, using only the added lines for the six pre-existing files.
- It found no e-mail shape, no key shape and no environment value. The only hits were shell variable assignments of script paths in the `.bash` wrappers.
- The records carry `"host": "turing.midcoip.net"`, as Phase 14's merged records already do.

## Defects

### MAJOR 1: F-CANOPY-028's account of why the race was not re-created is contradicted by the records

The FIXED disposition is unaffected by this defect.

**Why the "hold" account fails**

- **The bodies show the click came after the second render.**
  - A render that lands after a click resets that box. `early#2` body [5] shows it: `max_iterations` reads unchecked after the user had checked it.
  - dash fills a callback's inputs when the callback is picked to run. See 4.4.1 `dash_renderer.dev.js:1237`, called from the prioritized observer at `:3033-3051`.
  - So a click made before the second render landed would have reached the writer as unchecked, and the old merge would have dropped it. That is the LOST_B shape.
  - In all 26 parent drives, the click's writer instead read `max_iterations` **checked**, after a 22-input firing that had read it unchecked. Every click therefore landed after the second render.
- **Nothing in dash holds the writer behind the table render.** dash 4.4.1 `getReadyCallbacks` (`:1708-1757`) makes a callback wait only on outstanding outputs, and their downstream outputs, that are its own inputs. No callback outputs a `param-pin` value.
- **The recorded delay is not the click time.**
  - `second_pin_at_s_after_reload` is taken at `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py:532`.
  - After it come a log line, a screenshot and two page evaluates (`:536-540`), and only then the click.
  - The logs give the gap from the "after reload" line to the click's writer:
    - 5.4–8.1 s in the parent's `delay2`, `delay4` and early `forced` arms.
    - 1.2–3.6 s in the settled `forced` arms, where nothing was pending.
  - In the parent's early `forced` arms, the forced write's own page clock reads 17.6–20.1 s from the reloaded page's navigation start.

**Why the forced arm could not stage the race, and what `early#2` really needed**

- The renderer holds any table render requested during the click's writer flight behind that writer, because the pin store is the writer's Output and the render's Input. So a params-store write *after* the click can never stage `early#2`'s order, at either timing.
- In `early#2`, the stale render must have been requested *before* the click's writer and answered after it.

**What the records do and do not show**

- The window before the second render was never sampled.
- Its unreachability is not shown.
- Phase 14's item 31(a) asked for a pin timed before the second render. That ask is unmet, not "not reachable".

**Sentences to change**

- **Ledger `:3232-3234`.**
  - Current: "the renderer holds a click's writer behind a pending render of the checkboxes it reads, so at the driver's timings the click never precedes the second render, and the band the Phase 14 entry asked this phase to sample is not reachable by delaying the pin."
  - Replace with: "so at the driver's timings no click preceded the second render: each click's writer read `max_iterations` checked after a firing that had re-created every box with it unchecked, and a render landing after a click resets that box (`early#2`'s third body), so every click landed after that render. The recorded delay is the driver's pin step, not the click: `second_pin_at_s_after_reload` is taken before a log line, a screenshot and two page evaluates (`2026-10-20_item30_fixwave_redrive.py:532-540`), and the click's writer went out 5.4–8.1 s after that log line in the 2 s, 4 s and early `forced` arms (1.2–3.6 s at the settled timing, nothing pending). The band before the second render was therefore not sampled; nothing here shows it unreachable."
- **Ledger `:3235-3237`.**
  - Current: "The `forced` arm at the early timing (the click 2.6–3.2 s after the reload, the write 150 ms later) lost nothing in 6 (`parent_8062_dash441_forced.json`): the second render was still pending at the write, the renderer absorbed the forced rebuild into it, and no fourth writer firing appears."
  - Replace with: "The `forced` arm at the early timing (the pin step 2.6–3.2 s after the reload; the write 150 ms after the click) lost nothing in 6 (`parent_8062_dash441_forced.json`), and no fourth writer firing appears: the click came after the second render here too, and the rebuild the write requested waited for the click's writer, as at the settled timing."
- **Ledger `:3243-3245`.**
  - Current: "A synthetic store write cannot stage `early#2`'s order; what did, there, was the params-store REFRESH landing inside the click's own write latency, which no instrument here times."
  - Replace with: "A store write after the click cannot stage `early#2`'s order: the renderer holds the render it requests behind the click's writer (dash 4.4.1 `getReadyCallbacks`). In `early#2` the stale render was requested before the click's writer and answered after it; a params-store write just before the click, or a click timed to the params-store fill, could stage that order, and no drive here tried either."
- **Ledger `:13089-13093`.**
  - Current: "What this phase adds to Phase 14's record of the race is a negative result worth keeping: **at the driver's timings the click's writer is held behind the pending second render in every drive** (0 of 14 lost at fixed delays of 2–14 s on the parent), so the loss band the entry asked for cannot be sampled by delaying the pin, and a synthetic params-store write 150 ms after the click is absorbed by the pending render at the early timing (0 of 6);"
  - Replace with: "What this phase adds to Phase 14's record of the race is a negative result and its limit: **at the driver's timings every click landed after the second render** (0 of 14 lost at driver delays of 2–14 s on the parent; the driver clicks seconds after its recorded delay, behind a screenshot), so the loss band the entry asked for was not sampled, and a synthetic params-store write 150 ms after the click is held behind the click's writer and cannot stage `early#2`'s order (0 of 6 at the early timing);"
- **Ledger `:13117-13121`.** After "and the live drives on the fix (25) show no loss.", add: "Those 25 cannot discriminate: the same instrument lost nothing on the parent, so they show that a toggle still persists, not that the race is closed; the closure rests on the unit test and on `early#2`'s third body mapping to `no_update`."
- **Ledger `:13170`.** Current: "**Items 31 and 32 are DONE** (canopy#761, canopy#760)." The item 31 half is rewritten under MAJOR 2.
- **Handoff `:116-119`.**
  - Current: "**The renderer holds a click's writer behind a pending table render**, so a pin at a fixed delay after the reload never hits F-CANOPY-028's window, and a synthetic params-store write after the click (the driver's `forced` arm) produces no writer firing at all: neither instrument re-creates early#2's order, which came from the params-store refresh landing inside the click's write latency."
  - Replace with: "**The driver's click lands after the second table render at every delay it was given**: `second_pin_at_s_after_reload` is taken before a screenshot and two evaluates, which wait seconds on a page still loading, and every click's writer read the new pin checked after the rebuild had re-created it unchecked. A params-store write after the click (the `forced` arm) is held behind the click's writer by the renderer (the pin store is the render's Input), so it cannot stage early#2's order, which needs the rebuild requested before the click's writer."
- **Handoff `:47-48`.** Current: "(14 at fixed delays of 2–14 s;" Replace with: "(14 at driver delays of 2–14 s, every click landing after the second render;"
- **Scripts.** Correct the same claim in:
  - `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py:503-507` (comment);
  - `util/ad-hoc/2026-10-20_item31_f028_drives_pass2.bash:10-12`;
  - canopy#761's 2026-10-21T05:30Z drive comment (a follow-up comment).

### MAJOR 2: item 31b's new manual sentence is wrong for three of the four patch targets

- **What changed.** canopy `aeeaf29b` `docs/USER_MANUAL.md:500` reads "Values are floats separated by commas or spaces." The old sentence (`571743db` `:500`, "comma-, semicolon-, or newline-separated floats") was right for the 1-D targets.
- **What breaks.**
  - The new sentence documents an input the panel refuses: spaces for `output_bias`, `hidden_unit_weights` and `hidden_unit_bias`.
  - It drops the semicolon and newline forms those targets accept (`_parse_float_list`, `network_editor_panel.py:418-434`).
  - By Phase 13's manual rule, this is a documented behaviour broken.
- **Ledger `:13103-13105`.**
  - Current: "The sentence now states the row idiom and the flat-list reshape; the parser is unchanged, the smaller of the two changes the entry offered."
  - Replace with: "The sentence now states the row idiom and the flat-list reshape for `output_weights`; the parser is unchanged. Its first clause, 'Values are floats separated by commas or spaces' (`aeeaf29b` `docs/USER_MANUAL.md:500`), is wrong for the other three targets: `_parse_float_list` (`network_editor_panel.py:418-434`) splits on commas, semicolons and newlines only, so `0.1 0.2` for `output_bias` is refused (`could not convert string to float`), and the forms those targets do accept are no longer documented. Owed as item 34, before the release that ships canopy#761."
- **Ledger `:13170`.**
  - Current: "**Items 31 and 32 are DONE** (canopy#761, canopy#760)."
  - Replace with: "**Item 32 is DONE** (canopy#760). **Item 31 is DONE** (canopy#761) except (b): the new sentence is wrong for the 1-D targets (new item 34); (a)'s ask to time a pin before the second render was not met (the driver's clicks land after it) and is dropped now that the fix is merged."
- **New item 34.** "34. **canopy's Patch Weights sentence for the 1-D targets.** `docs/USER_MANUAL.md:500` at `aeeaf29b` says values are separated by commas or spaces; `output_bias`, `hidden_unit_weights` and `hidden_unit_bias` refuse spaces and accept semicolons and newlines. Either say so (one sentence) or have `_parse_float_list` split on whitespace, as its own docstring claims; a canopy PR, before the release that ships canopy#761. If it ships unfixed, file it (Phase 13's manual rule)."
- **Handoff `:46-47`.** Add "item 31b's sentence is wrong for the three 1-D targets (item 34)". Add item 34 to Remaining, ahead of the release item.

### MAJOR 3: the handoff's Remaining list omits ledger items 18–21

- **What is missing.** The four items are:
  - 18: F-CANOPY-064 (P1) and -067.
  - 19: F-CANOPY-060 and -063, with item 16's fixture sweep.
  - 20: F-CANOPY-065, P1 conditionally.
  - 21: F-CANOPY-066.

  Items 18 and 20 cover two of the four open P1s.
- **Where they stand.** All four are owed: Phase 10 `:10830-10858`; Phase 13 re-states 18 and 20 at `:12577-12581`; Phase 15 says "Phase 14's list stands".
- **Why no handoff carries them.** The parent's item 5 predates them, and neither the Phase 14 handoff, this handoff, the parent pointer nor the INDEX row carries them.
- **Handoff `:95`.** Insert before "9. Then the parent's items 5 and 7, and the owner batch O1–O17.":
  - "**Ledger items 18–21** (canopy code; Phase 10's list, re-stated by Phase 13): 18 F-CANOPY-064 (P1) and -067 (first decide -067's rating on unfixed `main` with the recurrence leg up and a canopy restart on an idle cascor; never the trio), 19 F-CANOPY-060 and -063 with item 16's fixture sweep, 20 F-CANOPY-065 (P1 on O17's first limb), 21 F-CANOPY-066 with the selection arc's A1-iii. Canopy PRs, verified on a leg."
- **Goal statement and INDEX row.** Add "items 18–21 (canopy fixes for F-CANOPY-064/-065/-067/-060/-063/-066)" to both "Next" lists.

### MAJOR 4: item 33's owner action does not do what it says

**What is wrong**

- **`pip install -e .` from the current tree changes nothing.**
  - The conda env `JuniperCanopy1` has dash 3.3.0 and no canopy install.
  - The editable canopy is in `~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1`, a system-site venv over it.
  - That venv's finder maps to `trees/juniper-canopy`, which is still `571743db` with floor `dash>=3.0.0`.
  - So `pip install -e .` from that tree leaves dash at 3.3.0: pip only upgrades when needed.
- **pip does not read the lock.**
- **The conda file cannot be rebuilt from as it stands.** It is a linux-64 `conda create --file` export with about 50 `=pypi_0` lines.

**Sentences to change**

- **Ledger `:13182-13183`.**
  - Current: "Owner: `pip install -e .` in the env upgrades dash (the lock's 4.4.1 resolves there; `comm` and `janus` come with it), or rebuild from the corrected conda file;"
  - Replace with: "Owner: re-sync the E2 tree to canopy `main` (`fbf01dff` or later; at `571743db` its floor is already met by 3.3.0), then `pip install -e <tree>` with the E2 venv's interpreter (`~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1`, a system-site venv over the conda env, holds the editable canopy); pip takes the newest dash 4.x (4.4.1 today) with `comm` and `janus`. Or rebuild the conda env from a copy of the corrected `conf/conda_environment.yaml` re-specified for osx-64 as juniper-ml#2282 did (the file is a linux-64 `conda create --file` export with `=pypi_0` lines);"
- **Handoff `:82-85`.** Make the same change.

### MAJOR 5: item 27 never clicks through the Live Switch modal, so F-CANOPY-069's gated click-through has no owner

**What is wrong**

- **The drive does not open the modal.** `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` turns on the flag, runs a demo training, and samples `live-dataset-switch-button`'s `disabled` attribute. It never opens the modal, never presses Accept, and never reads the progress alert. The only modal reference is `ensure_no_modal`.
- **The restart confirm has no task either.**
- **The leg's provenance stamp would be wrong.**
  - `f069_fix_leg.bash:46` hard-codes the stamp base `571743db…`.
  - `turing_canopy_leg.bash` falls back to `legs/serving-commit`, which also reads `571743db`.
  - So a leg built from the handoff's recipe reports a `571743db` stamp while serving main's code.
  - Setting `CANOPY_LEG_SRC` needs an env prefix, which the guard refuses.
- **The blob-check command is incomplete.** `2026-10-20_e2_tree_blob_sha_check.py` requires `--repo`, `--root` and the paths.

**Sentences to change**

- **Ledger `:13113-13114`.** Current: "Item 27 clicks through the Live Switch modal and will." Replace with: "Item 27's drive samples only the Live Switch button's gate; clicking through either modal is owed (item 27, extended)."
- **Handoff `:76-80`.**
  - Current: "(with `CANOPY_LEG_SRC` pointing at that tree's `src`, or `util/ad-hoc/2026-10-20_f069_fix_leg.bash`, which sets it) and `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` adapted to the chrome channel and the CDN route. It clicks through the Live Switch modal, which Phase 15's probe only fired; on `main` the spinner must close after the swap."
  - Replace with: "via `util/ad-hoc/2026-10-20_f069_fix_leg.bash up <port> <dash44 python> <tree>/src +f069+f028-fix-unlanded` (it stamps `571743db` plus the suffix; record the served tree as `-f028` = `aeeaf29b` except `requirements.lock`, or extend the wrapper to take the base sha; the guard refuses a `CANOPY_LEG_SRC=` prefix). Then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py`, adapted to the chrome channel and the CDN route, which samples the switch button's gate with the flag on and a demo run live (record in F-CANOPY-025's and -055's entries). It does not open the modal: extend it to click the enabled switch, Accept, and read `live-switch-progress-alert` (it must close after the swap on `main`), and drive the restart confirm likewise; that closes F-CANOPY-069's 'fired, not clicked'."
- **Handoff `:73-74`.** Spell out `--repo pcalnon/juniper-canopy --ref main --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028 <the 15 files #760/#761 touch>`.
- **Goal statement `:21-22`.** "the Live Switch modal's allow arm" should read "the Live Switch button's allow arm, extended to click through the modal".

### MINOR

1. **Ledger `:12819`.** Current: "the alert added at the firing and gone 1.9 s later". Replace with: "the alert added when the opener's answer landed and gone 1.9 s later, with the worker's". Nothing writes `True` before +0.64 s, and the DOM and POST clocks are not common.
2. **Ledger `:12859-12860`.** Current: "(restart 1.0–1.2 s, Live Switch 0.3–0.7 s)". Replace with: "(the responses at +1.0–1.2 s for the restart and +0.3–0.7 s for the Live Switch)". The alert lives are 1.05–1.35 s and 0.58–0.75 s.
3. **Ledger `:3215-3217`.**
   - Current: "On the stale input Phase 14 recorded (`values=[True, False, False, False]` over `learning_rate, max_iterations, patience, output_epochs`, store `["learning_rate", "max_iterations"]`)".
   - Replace with: "On the stale input Phase 14 recorded (`early#2`'s third body: 22 boxes triggered, `learning_rate` checked and `max_iterations` not, State `["max_iterations", "learning_rate"]`; the unit test pins a four-key analogue)".
   - `patience` and `output_epochs` are not Parameters-table keys.
4. **Ledger `:3251-3252`.**
   - Current: "M-PARAMETERS-04, -05 and -06 pass on their own expectations in every drive."
   - Replace with: "M-PARAMETERS-04 and -05 pass on their own expectations in every drive; -06 runs only in the driver's `settled` arm, which no Phase 15 drive used."
   - The driver returns before M-06 for any other arm (`redrive.py:569-573`).
5. **Ledger `:12848`.**
   - Current: "with dash 4's two new conda-forge run dependencies,"
   - Replace with: "with the two of the 4.4.1 build's new run dependencies the file lacked (the third, `pydantic>=2.10`, is pinned at 2.12.5),".
6. **Ledger `:12849-12851`.** After "a floor nothing tests is how this stayed invisible.", add: "The counter-position, from canopy#760's body: the fix is ALIVE on 3.3.0, so the floor is a policy choice; and 4.0.0 is itself untested (CI pins 4.1.0 in its conda lane and resolves 4.4.1 in its pip lane), so `>=4.1.0` or a CI lane at the floor would make it a tested one."
7. **Ledger Consensus record.**
   - `:13131`: "every count, and every item 31 and item 32 figure, matched" should read "every count, and every other item 31 and item 32 figure, matched".
   - `:13143-13144`: "Every figure agreed within run-to-run timing." should read "The lane reported steps 1, 2 and 5 as agreeing; the reconciler found steps 3 and 4 agreeing within run-to-run timing."
   - `:13154`: "**Round 1 changed one action's parameter** (item 27's tree), so the review continued." should read "**Round 1 changed one action's parameter** (item 27's tree, the reconciler's consequence of Lane 15-A's step 2, which no lane reported), and its corrections alone require a second round (procedure §4), so the review continued."
8. **Unmarked landing-time statements in the handoff.**
   - `:3-5`: "as its PR was opened".
   - `:55-60` and `:151-153`: the PR and the branch, which return `[]` and 404 today.
   - `:170-171` and `:177-178`: the round-2 corrections script and the round-2 report, which do not exist yet.
   - `:194`: `MEMORY.md`, whose canopy line still reads "items 31/32 next".

   Mark each "(at landing)", or add a landing check that the files exist and that MEMORY.md's line names Phase 15.

   Also, at `:69`, "A revert costs one replay: `util/ad-hoc/2026-10-20_phase15_rebuild_shared_files_for_landing.py`." is incomplete: its `DEFAULT_PASSES` stops at round 1. Add the `--pass` list, or update `DEFAULT_PASSES` in the round-2 pass.
9. **Handoff `:109-110`.**
   - Current: "Pin `--expected-head` on the PR's current head (`gh pr view N --json headRefOid`), not on your last push;"
   - Replace with: "Pin `util/push_signed_commit.py`'s `--expected-head` on the PR's current head (`gh pr view N --json headRefOid`), not on your last push (`safe_merge.py` has no such flag);".
10. **Ledger `:13054-13060`.**
    - "Every leg served a tree copied from the E2 tree" is wrong: the parent legs served the E2 tree itself.
    - "the third re-run on 2026-10-21 against the same unchanged tree … before the fix scripts ran on the copy" is wrong in two ways:
      - Run 3 is the first check of five of the files: `test_poll_gating.py`, `conf/requirements_ci.txt`, `test_p2_wave_batch_b.py`, `test_dashboard_manager_gate_coverage_inner1.py` and `docs/USER_MANUAL.md`.
      - It ran after the fix scripts.
    - Replace with: "Every leg served the E2 tree or a copy of it. The E2 tree was proved byte-identical to `571743db` for every file the apply scripts touch (runs 1 and 2 on 2026-10-20, before the fix scripts ran; run 3 on 2026-10-21 the first check of five more, against the same tree, which the scripts did not write; for those five the scripts' exact-match anchors were the check at the time)".
11. **F-CANOPY-028 "Not measured" (`:3252-3253`).** Add: "a stale render landing while the click's writer is in flight: dash evicts the older executing call (`dash_renderer.dev.js:3379`), so the click's write is discarded and the rebuild's call writes nothing; the new pin does not register (the box re-renders unchecked), and no earlier pin can be lost".
12. **Driver provenance.**
    - The landed driver's `forced` arm pins at the settled timing (`redrive.py:503`).
    - So `2026-10-20_item31_f028_drives.bash` no longer reproduces `parent/fix_*_forced.json`.
    - `--f028-forced-gap-ms`'s help (`:1010`) still says "pins at the early timing". Say both in the help text and in the blockquote's "Driven" sentence.
13. **Handoff `:174-175`.**
    - Current: "the screenshots under `shots/` are LFS PNGs and stay on turing".
    - Add: "untracked in this worktree, so they go with it at cleanup (item 8) unless copied out; only the last arm's three (each arm overwrites them)".
14. **Matrix, M-PARAMETERS-04's Expected column.** "One pattern-matched callback collects every checkbox and writes the pinned key list … (`dashboard_manager.py:3948-3952`)" still describes the old writer. Update it to "persists the one toggled key (`_apply_pin_toggle`)". This is outside "Matrix effect" as written.
15. **Pre-existing text in the rewritten F-CANOPY-069 entry** (optional erratum):
    - The header says "three callback pairs claim one `allow_duplicate` output". It is two pairs and three ids (canopy#760's body says "Two callback pairs").
    - The body's "the second registration overwrites the first's entry" is false. `callback_map` is keyed by the full output string, the members' strings differ, and both handlers ran.

## What I could not check, and why

- **I did not run the F-CANOPY-069 test on `571743db` under either dash.** That would have meant writing it into a host tree. "7 of 9 fail" is from reading the tests.
- **I could not re-drive anything, because no leg may be started.** So I have no page-clocked click timestamp to confirm MAJOR 1 directly, and I did not measure MINOR 11's eviction window.
  - MAJOR 1 rests on the request bodies, the driver code, the logs, the forced write's page clock and the renderer source.
  - The clock bound alone settles 4 of the 6 parent early `forced` arms. The body argument settles all 26.
- **dash 4.2.0 (the Linux host's version) is not on this host.**
- **I did not re-run the unit-lane counts (7954 / 10 / 2).** I checked them only against canopy#760's comment.
- **I did not fetch dash's documentation page for `running=`.** I relied on `_callback.py` and both bundles.
- **I have only the session's own word for the merge-approval quote** ("save, merge, and PR handoff").
- **I could not check the statements that will be true only at landing** (MINOR 8), or whether a concurrent upload will revert lines after the merge.

---
