<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 5: Lanes R5-A and R5-B, verbatim

Round 5 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 07aef715, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R5-A re-derived round 4's claims from their artifacts; Lane R5-B attacked round 4's corrections (86e82c0c..07aef715). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR5A_phase9_ledger_brief.md and laneR5B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round5_corrections.py.

## Lane R5-A -- measurement re-creation, artifact-first

*agent `a5b69128cd058794f` · round 1 · last-assistant-text (not resumed) · 14600 chars*

**VERDICT: SOUND-WITH-FIXES.** All six claim groups re-derive from their artifacts. There are three LOW findings. Finding 1 changes one prose count (2 → 3). None changes a disposition or an action.

**TABLE**

| # | Claim | Re-derived value | Result | Evidence (command → output) |
|---|---|---|---|---|
| 1a | A replaying cascor refuses the parameter updates Apply sends | `update_params` raises `RuntimeError` under `_lock` when `is_replaying()`. The REST PATCH route turns that into a 409, and the WS `set_params` path calls the same method. canopy's Apply goes through `apply_params`, which uses REST `update_params` or WS `set_params`. | MATCH | `git show 0e016a7c:src/api/lifecycle/manager.py \| sed -n 4736,4744p` → the raise at `:4742-4743`. `git grep -n 'update_params(' 0e016a7c -- 'src/api/*.py'` → `routes/training.py:256` and `websocket/control_stream.py:503`. 409 mapping at `training.py:264-266`. canopy side: `cascor_service_adapter.py:1294-1370`. |
| 1b | canopy maps an unknown status to Stopped (`state_sync.py`) | `_normalize_status` ends `return mapping.get(key, "Stopped")` at `state_sync.py:177`, and the mapping has no `replaying` key. cascor reports the FSM enum name `REPLAYING` (`state_machine.py:372`). | MATCH for the mapping. Its link to the status bar is Finding 2. | `git show e9053227:src/backend/state_sync.py \| sed -n 158,177p` |
| 1c | The Network Editor's badge reads "FSM: Replaying" | The badge title-cases `/api/status`'s `fsm_status` (`network_editor_panel.py:621-622`). The status cache stores `normalize_status(raw)` (`main.py:178-183`, `status_cache.py:263`), which passes `fsm_status = sm.get("status")` = `REPLAYING` through unchanged (`service_backend.py:243,254`). `'REPLAYING'.title()` → `Replaying`. The only other FSM display, the player badge (`replay_player_panel.py:508`), never renders under F-059. | MATCH (source only) | Source reads as cited. |
| 1d | Text of cascor's start-training refusal | "Cannot start training while replaying a snapshot — invoke /v1/snapshots/{id}/replay/control with action='stop' first". The guard runs first inside the lock (`manager.py:2524` → `:2452-2453`). REST returns it as a 409 prefixed "Training cannot be started: " (`routes/training.py:130`). | MATCH | Source reads as cited. |
| 1e | A reset discards the run's metrics and counters but not its data | `reset()` (`manager.py:2871-2913`) calls `monitor.clear_metrics()` (`:2896`), sets `current_epoch=0` and `current_step=0` (`:2907`), and resets `_last_emitted_history_len`. It leaves `_train_x`, `current_dataset` and `_dataset_shortfall` alone (comment at `:2897-2902`). `_handle_reset` goes to STOPPED from any state. | MATCH | Source reads as cited. |
| 2 | F-CANOPY-014's precedent | Segment 6: the play button was "(visible, enabled)" and the stop button gave the "identical" error (ledger `:3887-3895`). Segment 7: all six controls, Stop included, failed "byte-identical" (`:4186-4196`), and "a direct `POST {"action":"stop"}` … returned `200` with `fsm_state: STOPPED`" (`:4200-4201`). Header `:3907-3909` gives P1 … FIXED (canopy#521). The triage tool reports `FIXED P1 F-CANOPY-014`. | MATCH | Segment 6's own REPLAY_STOPPED at 01:54:41 has no stated method. Segment 7's stop is explicitly a direct API call. |
| 3a | `4c496443` and `c666403b` | `4c496443`: committer "Paul Calnon", 21:45:22Z, `%G?`=G, GitHub `verified:true, reason:valid`, on ml#2058, pushed 21:45:23Z. That is 2:00 before ml#2059's ready at 21:47:22Z. `c666403b`: "Paul Calnon", 23:47:30Z, G, valid, pushed 23:47:35Z. ml#2045 was disarmed at 23:48:47Z and re-armed at 23:48:52Z. Both carry the same key ID (…831A). | MATCH | `git log --no-walk --format='%h cn=%cn cd=%cd G=%G? key=%GK'`; `gh api …/commits/<sha> --jq '{verified,reason,verified_at}'` |
| 3b | "five signatures stamped within one second" | 5 of the 29 pushed commits have committer time 23:58:57Z: b653557b, 6f37e98e, 068944b9, 5b706dbf, 41e3b406. No second holds more than 5. | MATCH | Committer dates only; signature packets were not read. |
| 3c | ml#2045's fast-forward push at 00:00:38Z of 29 commits signed 23:57:24Z–00:00:07Z | The activity API shows a `push` (not `force_push`) at 00:00:38Z, c666403b→b0223f18. Compare: `ahead_by:29, behind_by:0`, and `merge-base --is-ancestor` passes. The 29 committer dates run 23:57:24Z to 00:00:07Z, all G with the same key. | MATCH | Not cited by the ledger: a further push at 03:02:06Z added 3 commits signed with the same key at 03:00:20–03:01:48Z, inside the no-tool-call window. |
| 3d | At least 9 PRs armed as `pcalnon` 13:17:53Z–13:32:10Z, none by a command | My census read the timelines of all 117 PRs updated since 09-22T12Z across the 9 repos. It finds 10 arms in the window, all `pcalnon`: canopy#660 13:17:53, canopy#670 13:18:44, ml#2031 13:21:08, ml#2032 13:23:19, ml#2035 13:23:48, ml#2038 13:24:33, ml#2041 13:25:23, ml#2045 13:26:23, data#428 13:29:27, cascor#678 13:32:10. `safe_merge --pr 2031 --execute` (background, 13:21:04Z) made ml#2031's arm. The other 9, across 4 repos, have no arming command before them, either in the launch scan or in an independent grep of every tool_use input from 13:00 to 13:32:10Z. The ceremony run at 13:26:21Z was a HALTed `--dry-run`. | MATCH (the lower bound of 9 is exact) | See Finding 1 for ml#2041's 13:35:20Z arm command. |
| 3e | ml#2020, canopy#655 and cascor#673 armed 00:52:07Z–01:08:14Z | ml#2020 at 00:52:07 and again at 01:08:14, after a `--disable-auto` at 01:03:37. canopy#655 at 00:54:55, cascor#673 at 01:01:42. No arming command before any of them. | MATCH | Not a finding (incomplete, not false): the same command-free sweep also armed ml#2013 00:47:31, ml#2015 00:48:12, ml#2017 00:49:02, ml#2029 00:52:31, canopy#658 00:55:22, cascor#672 01:01:20 and deploy#228 01:05:21. That is 10 PRs across 4 repos, starting at 00:47:31Z. ml#2057 was also armed without a command at 20:23:01Z. "At least twelve" and "twice" (counted as sweeps) still hold. |
| 3f | Session `bc31e993` names ml#2032 and data#428 at 13:18–13:19Z | Main thread: an edit naming juniper-ml#2032 at 13:18:39; `gh api …/pulls/2032` at 13:19:08; a signed fix-up at 13:19:19 (`412b265f`, web-flow, verified, 13:19:20Z); `gh api -X PATCH …/pulls/2032`, the retitle, at 13:19:23. One subagent validated data#428 in `scratchpad/pr428b` from 13:18:23 to 13:19:37. None of it arms anything. The handoff `…four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md` was written at 20:28:41Z. | MATCH | In that minute data#428 is named only through the subagent's scratch path. The main thread last named it at 13:15:06. |
| 3g | Background launches naming canopy#670 (15:29Z, 15:55Z) and ml#2041 (13:35Z) | Scan rows: 13:35:33 `shepherd_automerge.bash 2041` (1f771cb0); 15:29:53 and 15:55:45 `safe_merge --pr 670` (6280349a). All come after the arms at 13:25:23 and 13:18:44. The shepherd only ever calls update-branch (script `:23`, `:70`). | MATCH on times and order; MISMATCH on the count | Finding 1 |
| 3h | ml#2045: draft 03:04:45Z, disarm 03:04:46Z, ready 03:05:02Z; no tool call on this host 01:40Z–03:26:44Z | The timeline has those three events, all by `pcalnon`, and no later arm. A host scan of all transcripts finds 0 tool_use in [01:40Z, 03:26:44Z). The last before is 21:30:32Z on 09-23; the first after is 03:26:44.867Z. | MATCH | ml#2045 was closed unmerged at 07:29:52Z, after the frozen commit. |
| 3i | Launch scan against the archived `.out` files | I re-ran both windows. `cmp` shows both outputs byte-identical to the archive (507 and 705 rows). There are 44 background launches on 09-23. | MATCH | |
| 4 | Still owed item 17, the network-swap lead | `manager.py:5977` is `outcome = self._load_snapshot_to_network(...)`; `:5734` is `self.model = CascorModel(network=network)`. Neither `reset()` (`:2871-2913`) nor `stop_replay()` (`:6063-6082`) assigns a model. `:1472` is `_auto_snap_best: bool = False`; the only other automatic snapshots are the dataset-swap pre/post ones. canopy `hdf5_snapshots_panel.py:533` (modal): "Start a read-only playback session…". `main.py:2985` (docstring): "Start a read-only replay session…". | MATCH | Two more "read-only" strings exist and the ledger does not claim its list is complete: `:964` button label and `replay_player_panel.py:108`. |
| 5a | Scan pattern and e-mail rule | Constructed forms tested against the frozen module under `python3 -B`. Matched: `gh run` with `-R`, `--repo`, `--repo=` or `-R<repo>` then `rerun`; `gh pr` with `--repo=`, `-R<repo>` or `-R <repo>` then `merge`/`ready`; `pulls/"$PR"/merge`, `pulls/"${PR}"/merge`, `pulls/$PR/merge`; graphql with `--field query=@`, `-F query=@`, `-Fquery=@` or `--input`; `bot_pr_converge`. Missed: R4-A's `pulls/{n}/merge`, `pulls/%s/merge`, and inline-Python `["gh","pr","merge"]`. `_lead@example.org` → `<email>` in both tools, which share an identical EMAIL_RE; `+@pytest.mark.unit` is left alone. | MATCH for every form the round-4 pass says it added | Finding 3 |
| 5b | Archive dry run re-checks all 36 files | `python3 -B util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence_round2.py --dry-run` → "would copy 0, already present 36 (re-checked; 0 failed a check)", exit 0. That is 19 RAW plus 17 SCRIPTS, and both loops call `_refuse(dst)` (`:144`, `:159`). The tree was unchanged afterwards. | MATCH | |
| 5c | Push tool refuses a dirty tree and a non-ancestor base | Read, not run: `:89-91` refuses when `git status --porcelain` is non-empty; `:92-94` refuses when `merge-base --is-ancestor` fails. Both run before any network call, `--dry-run` included. | MATCH | |
| 6 | Triage counts | `python3 -B util/ad-hoc/e2e_finding_triage.py` → 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open. Open P0: 1 (F-CANOPY-059). Open P1: 6 (F-CANOPY-055, -056, -057, -058, F-CASCOR-001, -002). F-CANOPY-015 is OPEN P2. | MATCH | |

**FINDINGS**

1. **LOW: the background-launch count is wrong, and an arming command is left out.**
   - **Quoted** (`…E2E-VALIDATION-EVIDENCE.md:8775-8776`): "Two background launches the pattern matches name morning PRs, and both came after those PRs' arms: `safe_merge --pr 670` at 15:29Z and 15:55Z, and a shepherd for ml#2041 at 13:35Z, which cannot arm."
   - **Evidence:** The ledger counts launches as scan rows ("44 matching background launches"). By that unit there are three: 13:35:33Z, 15:29:53Z and 15:55:45Z. Also, 13 s before the shepherd, 1f771cb0 ran `gh pr merge 2041 --squash --auto` in the foreground at 13:35:20Z. Its output was "arm exit=0 … autoMerge=SQUASH". That is an arming command for a PR which `:8771` says no command armed. It came 10 minutes after the 13:25:23Z arm, and GitHub logged no second arm event, so the conclusion holds.
   - **Fix:** "Three background launches … all came after those PRs' arms …". Add that 1f771cb0 ran `gh pr merge 2041 --squash --auto` at 13:35:20Z, after the arm, and GitHub recorded no new event.
   - **Changes a number/disposition/action?** Yes, a number (a prose count, 2 → 3). No disposition or action.

2. **LOW: the cause given for the status bar showing Stopped is wrong.**
   - **Quoted** (`:9149-9150`): "canopy maps the REPLAYING status it does not know to Stopped (`state_sync.py:177`), so the status bar shows Stopped".
   - **Evidence:** The top status bar never reads that mapping. It reads `/api/status`, where `normalize_status` sets `is_running`, `is_paused`, `completed` and `failed` all False for REPLAYING (`service_backend.py:243-253`). The bar's own flag chain then falls to its else branch, `status = "Stopped"` (`dashboard_manager.py:7518`). And while F-CANOPY-055 (OPEN P1) stands, the bar shows its layout default `children="Stopped"` (`:887`) whatever cascor reports. `state_sync.py:177` feeds `/api/state` (`main.py:1409`) and the reconnect sync. There its status only hides metrics-panel widgets (`metrics_panel.py:1462,1510,1540`). So "shows Stopped" is true, but the cited cause is not; a fix at `:177` would not change the bar. The consensus record's general wording at `:9347` is fine.
   - **Fix:** Cite `dashboard_manager.py:7518`, and `:887` while F-055 is open. Keep `:177` as the `/api/state` mapping.
   - **Changes a number/disposition/action?** No.

3. **LOW: the scan's docstring says every missed form was added.**
   - **Quoted** (`util/ad-hoc/2026-09-24_merge_command_launch_scan.py:26-27`): "Rounds 3 and 4 … found forms it first missed; each was added".
   - **Evidence:** R4-A's finding 8 (`…phase9_ledger_round4.md:81-86`) named f-string, quoted and printf REST paths; argv lists in inline Python; and tools with no `command` field. The constructed test misses `pulls/{n}/merge`, `pulls/%s/merge` and the argv-list form, and `scan()` reads only `input.command` (`:84`). The ledger's own wording (`:8712-8713`) and the code comment at `:44-45` are accurate.
   - **Fix:** Say which forms were added, and name the ones that were not.
   - **Changes a number/disposition/action?** No.

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live. The badge text, status bar, Start alert and Apply refusal are all read from source.
- I did not read signature packet timestamps, because that needs commit headers or signer IDs. I used committer dates, `%G?`/`%GK` and GitHub's verification fields instead.
- I could not tell who armed, readied or pushed. Transcripts show only Claude Code on this host, not the web UI, other hosts or automations.
- I did not check the YubiKey's touch policy.
- For the handoff I read only its filename and when it was written (20:28:41Z). The file itself was modified after the frozen commit.
- As instructed, I did not run the push tool or the F-058 census.
- My arm census covers PRs updated since 2026-09-22T12:00Z in the 9 Juniper repos only.

**SECRETS/PII:** No slip.
- GitHub: GET requests only, selecting numbers, titles, logins, timestamps, SHAs and the verification `verified`/`reason`/`verified_at` fields. I never requested e-mail, signature or payload fields.
- git: names via `%an`/`%cn`, flags via `%G?`, key IDs via `%GK`. No `git cat-file commit`, no `%GS`/`%ae`/`%ce`, and no whole-header `git show`.
- Transcripts: one deviation from the brief. I searched with Python (`rglob('*.jsonl')`) and quoted `find -name` rather than `grep -r --include`. There was no shell glob, and output was limited to timestamps, 8-character session ids, tool names and redacted substrings of about 200 characters or less.
- No repository file changed and no bytecode was written. Scratch files are only in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r5a.rCS0qu/`.

---

## Lane R5-B -- adversarial, on round 4's corrections

*agent `a508083b18dc402b4` · round 1 · last-assistant-text (not resumed) · 12001 chars*

**VERDICT: SOUND-WITH-FIXES.** The replay reproduces the ledger exactly, and most of what the pass introduced holds against source and GitHub. The problems are two wrong counts in the owner evidence, one wrong cause cited for the status bar, one false size claim about the push tool, and one post-freeze event that overtakes the owner question. Findings 1–5 change a number, a disposition or an action, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` the review continues.

Paths: "ledger" means `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `07aef715`. Canopy lines are at `e9053227` and cascor lines at `0e016a7c`.

## FINDINGS

**1. MAJOR (staleness after the freeze): the owner has answered the owner question.**
- **Quoted:**
  - ledger :8786-8787, "The actor is unidentified … **Owner question**: were that pass and the later actions his?"
  - item 15, :9496-9503
  - :9377-9379, "who readied and armed canopy#676 … beyond 'no Claude Code process on this host'"
- **Evidence:**
  - Session `bc31e993` asked the owner at 03:34:45Z (transcript `…happy-skipping-hollerith/bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl`, line 4227). The owner answered at **2026-09-24T07:32:48Z** (line 4260), 4 min after `07aef715` was committed at 07:28:28Z.
  - The exchange: "Four PRs from this arc (data#428, ml#2032, ml#2059 and canopy#678) were taken out of draft and armed 4-7 s later, as pcalnon … and cascor#678 was armed the same way earlier. Is that sweeper yours?" = **"Mine: fix forward"**.
  - The same answer is now recorded in three places:
    - line 5 of the handoff whose title the ledger cites as evidence (`HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`, modified 07:57Z);
    - memory `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`, updated 07:33Z;
    - both say "RESOLVED 2026-09-24: the sweeper is the owner's".
- **Fix:** record the answer, its date, its wording and its scope in "Who", item 15 and "What the evidence cannot support", and retire "unidentified". The question did not name #676's CI re-run, the update-branches, cascor-worker#196 or ml#2045's disarm/re-arm, so those remain the owner's to confirm.
- **Changes:** disposition yes (item 15's first question moves from open to answered for the ready-and-arm sweeper); action yes.

**2. MINOR: the arm census understates both occasions and the early sweep.**
- **Quoted:**
  - :8768-8772, "Arms like the pass's happened twice earlier that day … ml#2020, canopy#655 and cascor#673 between 00:52:07Z and 01:08:14Z, and R4-A's scan of every tool call found no command arming any of them"
  - :9500-9501, "(00:52–01:08Z and 13:17–13:32Z)"
  - :9342-9343, "ran twice … on at least twelve PRs"
- **Evidence — every auto-merge enable event on 09-23, nine repos, all PRs updated since 09-22, attributed against every tool call in the transcripts:**
  - The morning list reproduces exactly: nine PRs, 13:17:53Z–13:32:10Z.
  - The early sweep had **11 command-less arms of 10 PRs, from 00:47:31Z**:

    | PR | Arm time (UTC) |
    |---|---|
    | ml#2013 | 00:47:31 |
    | ml#2015 | 00:48:12 |
    | ml#2017 | 00:49:02 |
    | ml#2020 | 00:52:07 |
    | ml#2029 | 00:52:31 |
    | canopy#655 | 00:54:55 |
    | canopy#658 | 00:55:22 |
    | cascor#672 | 01:01:20 |
    | cascor#673 | 01:01:42 |
    | deploy#228 | 01:05:21 |
    | ml#2020 (re-arm) | 01:08:14 |

  - Between 00:30Z and 01:10Z, the only arm-capable calls were `safe_merge` runs for other PRs. The candidates it checked were fg calls ≤120 s before an arm and BG launches ≤4 h before; none names these PRs.
  - A **third** occasion: ml#2057 armed at 20:23:01Z with no command.
    - Session `1f771cb0` opened it at 20:09:28Z and launched only the read-only `watch_pr_runs.bash`.
    - It then made no tool call from 20:09:38Z to 20:25Z, and no transcript names #2057 or its branch between 19:50Z and 21:00Z.
  - Every other arm on 09-23 before 21:47Z is attributable: `safe_merge` about 4 s before, `gh pr merge … --auto` 1–7 s before, the converge driver, or the release ceremony (ml#2050).
  - R4-A's window was 13:00–13:45Z, so "R4-A's scan … any of them" misattributes the early three. They came from R4-B's pattern scan. My all-calls check agrees there was no arming command.
- **Fix:** at least three occasions: 00:47:31–01:08:14Z (≥10 PRs across ml, canopy, cascor and deploy), 13:17:53–13:32:10Z (9 PRs), and 20:23:01Z (ml#2057); ≥20 PRs in all. Alternatively, given finding 1, replace the census with the owner's answer plus a lower bound.
- **Changes a number:** yes (2 → ≥3 occasions; early sweep 3 → ≥10 PRs; start 00:52:07Z → 00:47:31Z).

**3. MINOR: wrong cause cited for the status bar's "Stopped", and item 16's new status-bar check cannot fail.**
- **Quoted:**
  - :9149-9151, "canopy maps the REPLAYING status it does not know to Stopped (`state_sync.py:177`), so the status bar shows Stopped"
  - :9347-9348
  - item 16, :9520-9521, "and what the status bar says meanwhile"
- **Evidence:**
  - `state_sync.py:177` feeds `/api/state` (`main.py:1409`), `service_backend.py:456` and the relay (`cascor_service_adapter.py:782`). It is not on the status bar's path.
  - The status bar's only writer, `update_unified_status_bar` (`dashboard_manager.py:4058-4085`), fetches `/api/status` (`:7274`). With every flag False, its own `else` branch writes "Stopped" (`:7508-7518`); `service_backend.py:243,254` passes `fsm_status` through untouched.
  - F-CANOPY-055 is still OPEN (ledger :8250, :8274-8277). While it is, the bar holds its layout default "Stopped" (`dashboard_manager.py:887`) whatever cascor is doing.
- **Fix:**
  - Cite `dashboard_manager.py:7508-7518`, plus F-055, as the bar's cause.
  - Keep `state_sync.py:177` for `/api/state` only.
  - Make item 16's check wait for F-055's fix, or read `/api/status` `fsm_status` or the Network Editor badge instead.
- **Changes an action:** yes (where a "Replaying" fix goes; the check as written is non-discriminating).

**4. MINOR: the push tool does not keep every group within 250 KB.**
- **Quoted:** :9231-9232, "lands this branch as signed commits in groups of at most 250 KB".
- **Evidence:**
  - `pack()` (`2026-09-24_push_phase9_signed_groups.py:64-78`) always appends the ledger as its own last group.
  - The ledger blob is 774,305 bytes (`git cat-file -s`), about 1.03 MB once base64-encoded.
  - Simulating `pack()` on the branch's 132 files gives 10 groups: nine of 184–249 KB, and the ledger at 774 KB.
  - The tool's own docstring cites 499/502 failures at about 330 KB, and its memory note records a single 327 KB file that needed three tries.
- **Fix:** say the ledger goes alone at about 774 KB (about 3× the failure size), and treat that upload as the untested step.
- **Changes an action:** yes.

**5. NIT: the count of later background launches is wrong.**
- **Quoted:** :8775-8776, "Two background launches the pattern matches name morning PRs, and both came after those PRs' arms".
- **Evidence:**
  - The regenerated scan has **three** background rows naming morning PRs: 13:35:33Z (shepherd for ml#2041), 15:29:53Z and 15:55:45Z (`safe_merge --pr 670`).
  - The two `safe_merge` launches re-armed canopy#670 at 15:29:59Z and 15:55:51Z.
  - `1f771cb0` also ran `gh pr merge 2041 --squash --auto` in the foreground at 13:35:20Z (a no-op, since it was already armed). So "no command arming any of them" is literally false; what holds is that no command came before those arm events.
- **Changes a number:** yes (2 → 3); nothing else.

**6. NIT: "no launch of those forms was found" is false for round 3's form.**
- **Quoted:** :8712-8713, "Rounds 3 and 4 each added forms it had missed, and no launch of those forms was found".
- **Evidence:** the converge driver, a round-3 addition, had six background launches (:8720-8726), and the 44/40 counts depend on them.
- **Changes:** nothing.

**7. NIT: item 13 mislabels the FAQ's mistake.**
- **Quoted:** :9470, "named the wrong way out of a stuck replay (an API stop or a restart)".
- **Evidence:**
  - At `b07943d6`, `REPLAY_V2_FAQ.md:15-18` said the player's Stop was "canopy's only way". That was the error, because it missed Reset Training.
  - An API stop is a valid exit, as the ledger's own :9129, :8536-8537 and :9520 say.
- **Changes:** nothing.

## CORRECTIONS I COULD NOT REFUTE
- **The replay.** Replaying the 19 substitutions on `86e82c0c`'s ledger gives a file byte-identical to `07aef715`'s (`cmp`).
- **Finding counts.** Triage gives 70 / 48 / 1 / 2 / 19, with 1 open P0 and 6 open P1.
- **The launch scan.**
  - Re-running it over both windows gives output byte-identical to the archives (705 and 507 rows).
  - There are 44 background launches on 09-23; 4 name no PR.
  - Every form round 4 says it added matches a constructed test command.
- **The signed commits.**
  - `c666403b..b0223f18` is a fast-forward (activity type `push`; compare shows 29 ahead, 0 behind).
  - Signatures are 23:57:24Z–00:00:07Z, five of them at 23:58:57Z, all by the same key as `c666403b` and `4c496443`.
  - Omitted by the pass (R4-A finding 7, partly applied): `f6363b9a`, signed 03:01:50Z with the same key and pushed at 03:02:06Z.
- **Timeline and window claims.**
  - ml#2045's draft (03:04:45Z), disarm (03:04:46Z) and ready (03:05:02Z) hold, and there were 0 tool calls from 01:40Z to 03:26:44Z.
  - `bc31e993` actually worked on canopy#660, data#428 and cascor#678 throughout 13:10–13:29Z, including a canopy#660 update-branch at 13:21:39Z. The ledger's narrower "13:18–13:19Z" is true but narrow.
- **The REPLAYING bullet, apart from the status-bar cause.**
  - Apply is refused (`manager.py:4742-4743`).
  - The Start refusal text is at `training.py:130` and `:2453`.
  - The badge is at `network_editor_panel.py:618-622`, and the player's controls post through `:371`.
  - Reset is at `:2886-2910`.
- **F-014's precedent.**
  - Its controls were visible and enabled, and every one failed, Stop included (:3887-3891).
  - Phase 1 ended the session with a direct stop (:4200-4201).
  - Both refusals predate Phase 1 (#178, #460).
- **Item 17.** `:5977`, `:5734` and `:1472` hold; `hdf5_snapshots_panel.py:533` and `main.py:2985` hold; the FAQ warns of the swap by `e455af03`.
- **The F-015 pointer.** Its text holds.
- **The archive tool.** A dry run prints "already present 36 (re-checked; 0 failed a check)".
- **The push tool.** Its clean-tree and ancestry refusals are present, and it re-reads the ref before retrying. The branch has 128 A and 4 M, with no deletions, renames or LFS files.
- **The archived reports.** C–C7, R4-A and R4-B are verbatim.
- **Walk of the round-4 findings.**
  - R4-A findings 1–8: applied. Finding 7 was only partly applied, and finding 6 was applied with the wrong cause (finding 3 above).
  - R4-B findings 1–14: applied, with the defects in findings 2, 3, 4, 6 and 7 above.

## WHAT I COULD NOT CHECK
- **Who acted.** GitHub records only `pcalnon` for every arm. The owner's answer does not say whether it covers the CI re-run or the later actions.
- **The hardware key.** I did not query the YubiKey's touch policy.
- **Anything live.** Nothing was driven.
- **The ~1 MB upload.** Whether it can land is unknown; the push tool was not run.
- **Actors off this host.**
- **The canopy follow-up's round 8.** It is still running.
- **Who made the re-derivation queries.** Subagents share the orchestrator's session id, so I cannot tell whether the orchestrator or its lanes made the "re-derived" queries.

**SECRETS/PII:** No slip.
- GitHub calls were GETs and GraphQL queries that selected logins, dates, SHAs and verification flags only.
- I parsed signatures locally and printed only times and a same-key boolean.
- Transcript output was bounded and redacted.
- **Changed:** no repository file. Scratch is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r5b.c95gwi/`.

---
