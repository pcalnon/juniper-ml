<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 4: Lanes R4-A and R4-B, verbatim

Round 4 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 86e82c0c, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R4-A re-derived round 3's new claims from their artifacts; Lane R4-B attacked round 3's corrections (3f83b9c6..86e82c0c). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR4A_phase9_ledger_brief.md and laneR4B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round4_corrections.py.

## Lane R4-A -- measurement re-creation, artifact-first

*agent `aa0e80da435510b4a` · round 1 · last-assistant-text (not resumed) · 14806 chars*

VERDICT: **SOUND-WITH-FIXES.** Every claim tied to code, commits or merges checks out against its artifact. Two statements about the morning of 09-23 do not. One of them changes a NUMBER: the ledger lists 3 unexplained arms and there were at least 9. So under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this round does not end the review. I changed no files. Scratch work is in `…/scratchpad/r4a.YzAcdv/`.

"Ledger" below means `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 9, at frozen `86e82c0c`. "Handoff" means `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`, which exists only in worktree `happy-skipping-hollerith`.

TABLE

| # | Claim (ledger `…E2E-VALIDATION-EVIDENCE.md` line) | What the artifact shows | Result | Evidence |
|---|---|---|---|---|
| 1a | A REPLAYING cascor refuses a new network, training start and stop, and restore, retrain and resume (:9129-9131) | cascor `0e016a7c`, `manager.py`: create network :1731-1732; start :2452-2453, whose check runs at :2524, before `start_fresh` at :2590; stop :2842-2843. `routes/snapshots.py`: :278, :329, :378 (the manager repeats these at :5784, :5829, :5904). It also refuses delete-network (:1789-1790) and param updates (:4742-4743). The ledger's list is a correct subset. | MATCH | `git show 0e016a7c:…` |
| 1b | While replaying it reports Stopped / Idle (`manager.py:6001-6003`), "so canopy shows Stopped" (:9132) | :6002 sets `training_state` to Stopped / Idle and :6003 broadcasts it. But `/v1/training/status` also returns `state_machine.status="REPLAYING"` (:3027, :3036). canopy's `/api/state` turns that into "Stopped" because `state_sync.py:177` defaults any unknown status to Stopped (called from `main.py:1409`). | MATCH (cause only partly stated) | Finding 6 |
| 1c | `reset()` ends the replay, is documented as REPLAYING's escape hatch, and `POST /v1/training/reset` reaches it | `manager.py:2878-2884` (docstring) and :2886-2895 (stops the session, RESET). `state_machine.py:49-51` documents the exit and :222-226 accepts RESET from any state. `routes/training.py:169-173` calls `lifecycle.reset()`; `app.py:821` mounts it under `/v1`. | MATCH | source |
| 1d | "The player's Stop is canopy's only caller of `/replay/control`" (:9132-9133) | All six player controls (Play, Pause, Stop, scrubber, speed, range) post through `_invoke_replay_control` (`replay_player_panel.py:351-391`, URL at :371, called from :684). That goes to canopy's proxy (`main.py:3021-3031`), then the adapter (`cascor_service_adapter.py:2368-2379`). Nothing else outside tests calls it. Stop (:650-653) is the only control that sends `stop`. | MATCH in substance, wording loose | Finding 5 |
| 1e | Reset Training is disabled only while its own command is in flight | Only `update_button_appearance` (`dashboard_manager.py:5345-5383`) writes `reset-button.disabled`, and it reads only `button_states["reset"]` (:8547-8552, :8571). `button-states` is written only by the click handlers (JS :144-146 and :180-182; server :8218-8219 and :8238), by the ack/timeout release (:8592-8637), and at startup, all enabled (:2380-2389). One edge case: a later ack can restore a stale copy of Reset's own loading state, which the timeout then clears. | MATCH | writer census |
| 1f | The adapter's `reset_training` reaches cascor's `/v1/training/reset` | `cascor_service_adapter.py:1137-1139` calls the installed `juniper_cascor_client` 0.8.0: `client.py:393-395` posts `/training/reset` (`constants.py:122`) under `api_url = base + "/v1"` (`client.py:137`). Building the URL offline gives `…/v1/training/reset`. Both entry points, `main.py:3770-3788` and `main.py:1043-1044`, go through `service_backend.py:214-215`. | MATCH | JuniperCanopy1 env |
| 1g | A replay session starts paused and emits only its first frame until Play | `manager.py:1076` sets `paused=True`; `_run` emits frame 0 (:1242-1244) and then waits while paused (:1252-1258). A seek also emits a frame (:1119-1121), but its control is hidden too. | MATCH | source |
| 1h | Placeholder shown at :112, controls hidden at :113 | `replay_player_panel.py:112` shows the idle view, :113 hides the active one. The placeholder text is at :154 and Stop at :230-236. | MATCH | source |
| 2a | `4c496443` (on ml#2058): committed 21:45:22Z by "Paul Calnon", not web-flow, valid PGP, 2 min before the pass's first ready | Committer "Paul Calnon" at 2026-09-23T21:45:22Z, login `pcalnon`, verified/`valid`, PGP, `wasSignedByGitHub:false`. The associated PR is ml#2058. ml#2059 was readied at 21:47:22Z, exactly 2 min later. | MATCH | commits API + GraphQL |
| 2b | `c666403b` (on ml#2045): 23:47:30Z, same properties | Same properties and the same key. It was pushed at 23:47:35Z; the disarm and re-arm were at 23:48:47Z and 23:48:52Z. | MATCH | activity API |
| 2c | Basis for "needs a touch of the owner's hardware key" | `util/push_signed_commit.py:15-16` says so. It is a statement, not a measurement. | MATCH (basis), reach limited | Finding 4 |
| 2d | No Claude Code tool call at those times | Zero tool calls in any transcript between 21:41:02Z and 01:40Z. | MATCH | own scan |
| 2e | "a rebase force-push to ml#2045 at 00:00:39Z" (:8757; the ledger marks it not re-derived) | The activity API records a plain `push`, not a force push, at 00:00:38Z (`c666403b`→`b0223f18`). The compare API shows a fast-forward: 29 ahead, 0 behind. | MISMATCH | Finding 3 |
| 3a | `pcalnon` armed ml#2032, ml#2045 and data#428 at 13:23:19Z, 13:26:23Z and 13:29:27Z | All three are `auto_squash_enabled` by `pcalnon` at those times. | MATCH | timelines |
| 3b | "no logged command names any of them between 13:15Z and 13:35Z" (:8760-8761, :9302) | The launch scan finds none. My wider scan finds session `bc31e993` naming ml#2032 at 13:18:39Z–13:19:23Z: a read, a signed push, and `gh api -X PATCH …/pulls/2032`, which is the 13:19:24Z retitle. It also used a `main428` scratch path at 13:18:23Z. Nothing names any of the three after 13:19:23Z, and nothing arms them. | MISMATCH (wording) | Finding 2 |
| 3c | "The same arming pattern that morning" is those 3 arms (:8759-8760, :9445) | At least 9 `pcalnon` arms with no arming command in the logs, 13:17:53Z–13:32:10Z: canopy#660, canopy#670, ml#2032, ml#2035, ml#2038, ml#2041, ml#2045, data#428, cascor#678. | MISMATCH (NUMBER) | Finding 1 |
| 3d | ml#2045 drafted at 03:04:45Z and readied at 03:05:02Z | Both confirmed. Also: auto-merge was disabled at 03:04:46Z and is still off; the head moved to `f6363b9a` at 03:02:06Z; no tool call on the host between 01:40Z and 03:26:44Z. | MATCH | Finding 7 |
| 4a | Re-running the scan over both windows | Byte-identical to the two archived `.out` files (705 and 506 rows). | MATCH | `diff` |
| 4b | 44 background launches on 09-23; 40 name one PR; 4 name none; 6 converge runs | 44 / 40 / 4. The four are the detect at 02:03Z, the ceremony at 15:10Z, and `run_rows_clean` twice at 18:17Z. The six converge runs: 13:50:15Z–15:19:51Z, for ml#2040 and ml#2049–2053. | MATCH | scan |
| 4c | Overlap with the 11 PRs | None of the 44 background launches names any of them. Foreground calls name them only to update a branch, disarm or draft (19:44Z, 20:04Z, 20:17Z, 20:24Z, 21:26Z); the cascor #676/#678 rows are a different repo. The only ready is `gh pr ready 2020` at 06:09:09Z, the last match is at 21:27:05.623Z, and no background launch could ready a draft from 09-20 on. | MATCH | scan |
| 5 | cascor#189 is #184's retarget, same diff, merged as `b1d19948` | Title ends "[retarget #184]" and its body says "re-targets the same change". Both are +524/−3 over two files with identical per-file counts. Merged 2026-05-03T19:52:10Z as `b1d19948`, which is an ancestor of `0e016a7c`. | MATCH | gh + git |
| 6 | `800c20bb`: date, contents, remotes, rebased copy | 2026-09-23T15:41:35-05:00 (20:41:35Z). It adds the run-2 transcript `…_idle_cuts_live_check_rebuilt_ce78e0de.json` and the 21-line census docstring edit. Only local branch `worktree-squishy-dancing-moth` contains it; GitHub returns 422. `5a0e4ea9` has the same stable patch-id, is an ancestor of `86e82c0c`, and is also absent from GitHub (422; branch 404). `51993b37` is 17:07:01Z. | MATCH | git + gh |
| 7 | Merge times | cascor#178 at 2026-05-03T00:55:26Z; it also introduced `REPLAYING`. canopy#532 at 2026-08-28T04:16:14Z. | MATCH | gh |
| 8 | Finding counts | 70 total, 19 open, 1 open P0 (F-CANOPY-059), 6 open P1. | MATCH | `e2e_finding_triage.py` |

FINDINGS

1. **MAJOR.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :8759-8760 says "`pcalnon` armed ml#2032, ml#2045 and data#428 at 13:23:19Z, 13:26:23Z and 13:29:27Z"; :9445 repeats it as "the same arming pattern ran that morning at 13:23–13:29Z".
   - **Evidence:** I swept all nine repos' timelines for 13:00–13:45Z. There were at least 9 `pcalnon` arms with no arming command in any transcript, 13:17:53Z–13:32:10Z: canopy#660 13:17:53, canopy#670 13:18:44, ml#2032 13:23:19, ml#2035 13:23:48, ml#2038 13:24:33, ml#2041 13:25:23, ml#2045 13:26:23, data#428 13:29:27, cascor#678 13:32:10. The other arms in that window follow a background `safe_merge` launch by about 4 s.
   - The handoff (`…four-prs-armed-by-an-unseen-actor…md`, lines 104-106), which the ledger itself cites, lists four of them: canopy#660, ml#2032, data#428 and cascor#678. It does not list ml#2045. Its line 104 reads "An unseen actor arms every open PR".
   - **Fix:** state the full set and span at :8759-8762 and in item 15 (:9444-9445), and cite the handoff's list.
   - **Changes a NUMBER:** yes (3 → at least 9). It also changes the evidence for the owner question. Disposition: no.

2. **MINOR.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :8760-8761 and :9302: "no logged command names any of them between 13:15Z and 13:35Z".
   - **Evidence:** false as worded for ml#2032. Session `bc31e993` named it four times between 13:18:39Z and 13:19:23Z, including the PATCH that produced the 13:19:24Z retitle. Its 13:18:23Z call names data#428 only through a `main428` scratch path.
   - **Fix:** "no logged command arms them; nothing names them after 13:19:23Z".
   - Changes a number, disposition or action: no.

3. **MINOR.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :8757: "a rebase force-push to ml#2045 at 00:00:39Z".
   - **Evidence:** the activity API shows a plain `push` at 00:00:38Z, a fast-forward from `c666403b`. It added 29 new commits, all signed by "Paul Calnon" with the same key between 23:57:24Z and 00:00:07Z. 27 of them re-create main's commits under new hashes (for example `b653557b` against main's `8e058951`).
   - **Fix:** describe it as a fast-forward push of a re-created history. This is more signed activity inside the quiet window, so it should join the owner-question evidence.
   - Changes a number, disposition or action: no.

4. **MINOR.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :8755-8756: "a locally signed commit needs a touch of the owner's hardware key".
   - **Evidence:** five of those 29 signatures are stamped 23:58:57Z. A touch per signature at that rate is not humanly possible, so one touch evidently covers a burst of signatures. A signature therefore shows the key was used around that time, not a touch at that exact second. The basis is `util/push_signed_commit.py:15-16`, which asserts this rather than measuring it.
   - **Fix:** qualify the sentence accordingly.
   - Changes a number, disposition or action: no.

5. **NIT.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :9132-9133: "The player's Stop is canopy's only caller".
   - **Evidence:** all six player controls call `/replay/control` (row 1d). Stop is the only one that ends the session.
   - **Fix:** "the player's controls are canopy's only callers; its Stop is the only exit".
   - Changes a number, disposition or action: no.

6. **NIT.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :9132: "…Stopped / Idle meanwhile, so canopy shows Stopped".
   - **Evidence:** cascor also reports `REPLAYING` in its status response, and canopy discards it (`state_sync.py:177`). By source, a failed Start relays cascor's refusal, which names the replay and points to `/replay/control` — not to Reset.
   - **Fix:** state this, and optionally add to Still owed item 16: show "Replaying" and point the alert at Reset Training.
   - Changes a number or disposition: no. Action: no (optional).

7. **NIT.** Ledger (`…E2E-VALIDATION-EVIDENCE.md`) :8758, on ml#2045's 03:04:45Z draft and 03:05:02Z ready.
   - **Evidence:** it omits the 03:04:46Z disarm, which was never re-armed, the 03:02:06Z head push, and that there were no tool calls on the host between 01:40Z and 03:26:44Z.
   - Changes a number, disposition or action: no.

8. **NIT.** The widened launch-scan pattern still misses these merge-capable forms:
   - `util/ad-hoc/2026-08-24_bot_pr_converge.py`, which does update-branch (:143); its name is not in the pattern.
   - `["gh","pr","merge"|"ready"]` argument lists inside inline Python.
   - `gh api graphql --field query=@file` and `--input <json>`.
   - f-string, quoted or printf REST paths (`pulls/{n}/merge`, `pulls/"$PR"/merge`, `pulls/%s/merge`).
   - Tools with no `command` field, such as GitHub MCP tools.

   None of these ran from 09-20 to 01:40Z on 09-24, except one `--input` on 09-21, which was a commit creation. No transcript uses GitHub MCP tools. The conclusion holds; the ledger's "a script run by a path the pattern does not name" caveat could name `bot_pr_converge.py` as an example. Changes a number, disposition or action: no.

WHAT YOU COULD NOT CHECK
- The YubiKey's touch policy. I did not query the hardware.
- Who performed any of the arms, readies or pushes. Transcripts cover only Claude Code on this host, not the web UI, other hosts or automations.
- Runtime behaviour. The REPLAYING lock-in is derived from source only; no canopy or cascor was started.
- The chain from cascor's error envelope to canopy's Start-failure alert. I read it; I did not execute it.
- R3-A's five other fixture fields.
- The converge driver's `--timeout` semantics. The arithmetic gives a latest end of about 17:19:51Z.
- "GitHub never had it": I can only show GitHub does not have those commits now.
- The count of at least 9 morning arms is a lower bound. The sweep covered each repo's 60 most recently updated PRs.
- The ml#2040 and ml#2042 arms before 13:10Z are unattributed.

SECRETS/PII: One slip. A local `git show 800c20bb -- <file>` printed a commit author's e-mail into my own tool output. It was not sent anywhere and is not repeated here. I requested no e-mail fields from GitHub. Transcript scans printed only session ids, timestamps and short, redacted excerpts. I printed no environment variables, tokens or credential files. The public GPG key id I read is not reproduced here.

---

## Lane R4-B -- adversarial, on round 3's corrections

*agent `a3f787556e2d5cce3` · round 1 · last-assistant-text (not resumed) · 15539 chars*

**VERDICT: SOUND-WITH-FIXES.** The core of the pass holds. The replay is exact, the counts reproduce, the REPLAYING lock-in and the Reset escape check out in source, and #184, the UTC dates, the line numbers and `800c20bb` are all right. One new owner-evidence claim is false, though, and it sits on the "re-derived" list. Several new statements are incomplete or contradicted elsewhere in the same commit. Findings 1–8 each change an action, and finding 1 also changes numbers, so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` calls for a round 5.

## FINDINGS

Paths: `…EVIDENCE.md` is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `86e82c0c`. Canopy lines are at `e9053227`; cascor lines are at `0e016a7c`.

**1. MAJOR: the morning arming-pattern bullet is false and incomplete, yet it is listed as re-derived.**
- **Quoted:**
  - `…EVIDENCE.md:8759-8762`: "`pcalnon` armed ml#2032, ml#2045 and data#428 at 13:23:19Z, 13:26:23Z and 13:29:27Z, and no logged command names any of them between 13:15Z and 13:35Z".
  - `:9302-9303` (re-derived list): "that no logged command names those PRs then".
  - Item 15, `:9445`: "the same arming pattern ran that morning at 13:23–13:29Z".
- **Evidence:**
  - A scratch scan of every tool_use from 13:15Z to 13:35Z on 09-23 found 19 of 814 calls naming #2032 or #428, all from session `bc31e993` and its subagents. They include:
    - 13:19:08Z `gh api repos/pcalnon/juniper-ml/pulls/2032 …`;
    - 13:19:19Z `2026-08-26_push_signed_fixup.py --branch docs/register-rulings-x-a-and-eco-008`, which landed commit `412b265f` on ml#2032 at 13:19:20Z;
    - 13:19:23Z `gh api -X PATCH …/pulls/2032`;
    - 16 calls in a `pr428b` extract.
  - GraphQL `AutoSquashEnabledEvent` shows the same sweep armed five PRs, not three:
    - canopy#660 at 13:17:53Z, merged 19:16:49Z;
    - ml#2032 at 13:23:19Z; ml#2045 at 13:26:23Z; data#428 at 13:29:27Z;
    - cascor#678 at 13:32:10Z, merged 20:22:13Z.
  - The handoff the bullet cites names four (bc31e993 transcript, 20:26:13Z): canopy#660, ml#2032, data#428 and cascor#678. The memory note `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md` says #660 and #678 merged ahead of their final validation rounds, which is #676's failure. I did not re-derive that part.
  - There was also an earlier sweep:
    - ml#2020 armed at 00:52:07Z, and re-armed at 01:08:14Z after its author disarmed it at 01:03:39Z;
    - canopy#655 armed at 00:54:55Z; cascor#673 armed at 01:01:42Z.
  - The archived 09-23 scan has only the author's disarm (01:03:37Z) naming any of those PRs.
- **Fix:**
  - Say "no command matching the launch pattern". Record that bc31e993 was working on #2032 and #428 in that window.
  - List all five arms and add the 00:52–01:08Z sweep.
  - Change item 15 to 13:17–13:32Z.
  - Take the claim off the re-derived list.
- **Changes a number:** yes (3→5 PRs; the time range). **Disposition:** no. **Action:** yes.

**2. MINOR: the P0-versus-F-CANOPY-014 paragraph misdescribes the precedent and leaves out that the precedent had the same lock-in.**
- **Quoted:** `…EVIDENCE.md:9147-9150`: "it leaves cascor refusing training. F-CANOPY-014, which disabled the same controls … was rated P1 … This one is worse".
- **Evidence:**
  - F-014's controls were "(visible, enabled)" (`:3888`) and every action failed, Stop included (`:3891`). The controls were not disabled.
  - So F-014 also stranded cascor in REPLAYING. Phase 1 ended that session with a direct API `stop` (`:4195-4196`).
  - The lock-in therefore does not distinguish the two findings; only the missing session view does. Item 15 (`:9448-9450`) carries the same framing.
- **Fix:** Describe F-014 accurately, and state in the rating question that F-014 shared the lock-in.
- **Changes a disposition:** possibly (the owner's P0/P1 ruling). **Action:** yes.

**3. MINOR: the same commit contradicts the new Reset escape.**
- **Quoted:**
  - Ledger `:9133-9137`: "The one way out on the page is the sidebar's Reset Training".
  - The C5 brief added in `86e82c0c` (`reports/e2e-canopy-2026-09-02/drafts/laneC5_canopy_followup_brief.md:24-25`): "the player's Stop is canopy's only way to stop a cascor replay … until the replay is stopped through its API or it restarts".
  - The canopy follow-up `b07943d6` (`notes/development/REPLAY_V2_FAQ.md:15-18`) says the same thing.
- **Evidence:** Source backs the ledger:
  - cascor's `reset()` stops the session and sends RESET (`manager.py:2886-2895`), and the FSM's `_handle_reset` returns to STOPPED from any state (`state_machine.py:222-226`).
  - canopy's Reset path: `/ws/control` (`main.py:1043-1044`) or `/api/train/reset` (`:3770-3781`) → `cascor_service_adapter.py:1137-1139` → the client's `/training/reset`.
- **Fix:** Correct the follow-up's FAQ and the next round's brief. Note the contradiction in item 13.
- **Changes an action:** yes.

**4. MINOR: "canopy shows Stopped while Start fails" understates what the page shows, and the refusal list is incomplete.**
- **Quoted:** `…EVIDENCE.md:9132` and summary `:8531`, "while canopy shows Stopped".
- **Evidence:**
  - The Network Editor tab's badge reads "FSM: Replaying" (`network_editor_panel.py:618-630`, from `/api/status` `fsm_status`, `service_backend.py:243,254`).
  - A failed Start shows a red "Start failed." alert (`dashboard_manager.py:8307-8310`) with cascor's 409 text: "Cannot start training while replaying a snapshot — invoke /v1/snapshots/{id}/replay/control with action='stop' first" (cascor `routes/training.py:130`, `manager.py:2453`; canopy `main.py:3696-3701`).
  - "Stopped" comes from canopy mapping unknown FSM names to Stopped (`state_sync.py:165-177`), which a fix must also handle.
  - The bullet leaves out the parameter-update (Apply) refusal that R3-B listed (`manager.py:4742-4743`).
  - It also leaves out that Reset clears the monitor's metrics and counters (`:2896-2908`).
- **Fix:** Reword the bullet. Make item 16 check Apply as well as Start after a Replay.
- **Changes an action:** yes.

**5. MINOR: the widened launch scan is still stale, and it misses the re-run analog of the form it fixed.**
- **Quoted:**
  - `2026-09-24_merge_command_launch_scan.py:2`: "List every Claude Code Bash tool call … that could ready, arm, merge or update-branch"; `:19-21`: "For each Bash tool_use … the command's first line".
  - Ledger `:8718`: "The widened pattern catches them".
- **Evidence:** I ran the frozen regex against constructed commands in scratch (`pattern_forms.py`). It misses:
  - `gh run -R <repo> rerun N` and `gh run --repo <repo> rerun`. gh accepts that order: `gh run -R pcalnon/juniper-ml list` exits 0. The "Who" conclusion covers #676's CI re-run.
  - `--repo=`, `-Rrepo`, `pulls/"$PR"/merge`.
  - `--field query=@`, `-Fquery=@`, `--input`.
  - `bot_pr_converge`, which R3-B asked for by name. `2026-08-24_bot_pr_converge.py:143` calls update-branch.
  - I found no launch of any of these from 09-20 to 09-24T01:40Z, so 44 and 40 stand.
- **Fix:** Update the docstring, widen the pattern, and name pushes and these forms in the ledger's caveat.
- **Changes an action:** yes.

**6. MINOR: the tools still refuse and redact less than stated.**
- **Quoted:** `…EVIDENCE.md:9205-9207`: "refuses … any file holding an e-mail address other than a `noreply` one or the Codecov uploader's public key address".
- **Evidence:**
  - `EMAIL_RE` is unchanged in both tools (`archive…round2.py:52`, `launch_scan.py:52`). `_lead@example.org`, R3-B's exact case, still passes.
  - The code exempts any address containing "noreply" and any `@codecov.io` address (`:127`).
  - The widened `SECRET_RE` never checks the 36 files that already exist, because the loop skips them before `_refuse` (`:141-143`, `:155-157`). A dry run prints "would copy 0, already present 36". My count-only scan of those files found none.
  - Unprefixed 40-character tokens pass the scan's redaction.
- **Fix:** Widen the local-part rule, exempt exact addresses, re-check existing destinations, or narrow the wording.
- **Changes an action:** yes.

**7. MINOR: the new push tool `2026-09-24_push_phase9_signed_groups.py` can overwrite newer `main` content on the PR branch, and its final check cannot catch it.**
- **Evidence:**
  - It diffs `--base..HEAD` (`:83`) with no check that `--base` is an ancestor of HEAD.
  - It uploads working-tree bytes (`:101`) with no clean-tree check.
  - If the branch is created at a `main` that has moved past `f9c81d80`, every file main changed is uploaded as the branch's older copy. The final blob check compares against HEAD (`:127`), so it passes.
  - This is latent: GitHub `main` is still `f9c81d80`, 0 ahead.
  - The docstring's "near 1 MB" 499 threshold contradicts the memory note it cites (`reference_signed_commit_api_499_on_large_payloads.md`: about 330 KB).
  - The default `--max-bytes` of 450,000 is above that threshold. The ledger alone is 768,415 bytes, about 1.02 MB in base64, and cannot be split.
  - "119 files ~2.4 MB" is now 126 files and 2,557,556 bytes.
- **Fix:** Require `merge-base --is-ancestor` and a clean tree, or upload `HEAD:` blobs. Correct the threshold.
- **Changes an action:** yes.

**8. MINOR: Lane C4 is cited, but its report is not archived.**
- **Quoted:** `…EVIDENCE.md:9128` "(Lane C4)", `:9035` "(Lanes C4, …)", `:9414` "Its review rounds are archived in `…canopy_followup.md`".
- **Evidence:** That file holds only C, C2 and C3 (headings at `:7`, `:113`, `:239`). C4's claim is on neither re-derived list. It does hold: `manager.py:1076` and `:1242-1258`.
- **Fix:** Archive C4's report and list its claim as re-derived.
- **Changes an action:** yes.

**9. NIT:** `:9285-9286` says "every number and date R3-A re-derived holds". R3-A's own MISMATCH rows (3h, `:114/:115`), its findings 6 and 9, and this pass's changes (38→44, 34→40, two dates, two line numbers) contradict that. Changes nothing.

**10. NIT: two round-3 defects of the same kind came back.**
- `:9299` says "all in `…round3_corrections.py`", but the scan pattern and the secret shapes were hand-edited code.
- The script's docstring (`:14`) says "the three REPLACE_ALL entries"; there are two.
- `ledger_r2_orchestrator/` now holds round 3's output under round 2's names.
- New bare role references: "§4 of the consensus procedure" at `:9307` and `:9413-9414`.
- Changes nothing.

**11. NIT:** `:8641`, "so GitHub never had it", becomes false when this phase lands. It should read "not before #676 merged". Changes nothing.

**12. NIT:** ml#2045's 03:04:45Z draft and 03:05:02Z ready (`:8758`) are recorded without why they matter: no session on this host made a tool call from 02:55Z to 03:10Z (the activity tool reports 0 calls). They also sit under a heading about signed commits "in that window", and they are neither. Changes nothing.

**13. NIT: two wording points in F-CANOPY-059.**
- `:9132-9133` says "The player's Stop is canopy's only caller of … `/replay/control` (`:371`)". Line `:371` sends all six actions; Stop is only the sole sender of `stop`.
- The header and summary say "until someone presses Reset Training", while item 16 also names an API stop.
- Changes nothing.

**14. NIT: two round-3 fixes were only partly made, and one edit is unrecorded.**
- F-015's own entry header (`:3932-3934`) still does not point to F-059.
- The 09-10 handoff's "204 `no_update`" (`HANDOFF_2026-09-10_canopy-e2e-f035…md:159`) is not recorded.
- "What round 3 changed" omits the in-place edit of Phase 4's row (`:6161`).
- Changes nothing.

## CORRECTIONS YOU COULD NOT REFUTE

- **The replay.** I replayed `2026-09-24_phase9_ledger_round3_corrections.py` on `3f83b9c6`'s ledger in scratch. It printed "applied 2 replace-alls and 34 substitutions", and `cmp` against `86e82c0c` is identical. So there is no hand edit to the ledger.
- **The scan counts.** Re-running the frozen scan gives output byte-identical to both archives (705 and 506 rows).
  - There are 44 background launches on 09-23, all Bash. 40 name one PR. The other four are `detect.py`, `ceremony.py` and two `run_rows_clean.bash`.
  - Six converge launches ran from 13:50:15Z to 15:19:51Z. None names a PR of the pass.
  - The only ready that is not an undo is at 06:09:09Z, and the last match is at 21:27:05Z.
- **The REPLAYING lock-in, in source:**
  - the refusals at `manager.py:1731-1732`, `2452-2453` and `2842-2843`, and `routes/snapshots.py:278`, `329` and `378`;
  - the Stopped/Idle report at `6001-6003`;
  - the reset route at `routes/training.py:169-173`;
  - the Reset button's `disabled` comes only from `button-states["reset"]` (`dashboard_manager.py:8547-8571`), and the button is always in the sidebar (`:1041-1045`);
  - no other on-page path ends a replay: the restart route is refused at start, and `main.py:2785` is demo-only.
- **The signed commits.** Both `4c496443` (21:45:22Z) and `c666403b` (23:47:30Z) are committed by "Paul Calnon" with valid PGP signatures. The YubiKey-touch requirement is at `util/push_signed_commit.py:15-16`.
- **The GitHub events.** The five update-branches made during the pass are web-flow commits at the stated times. ml#2045's draft and ready times are correct.
- **The dates.** cascor#178 merged 2026-05-03T00:55:26Z and canopy#532 merged 2026-08-28T04:16:14Z.
- **#189.** Its title is "[retarget #184]": base `main`, +524/−3 over 2 files, `b1d19948`, which is an ancestor of `0e016a7c`.
- **`800c20bb`.** Committed 20:41:35Z, only on local `worktree-squishy-dancing-moth`, with a diffstat identical to `5a0e4ea9`.
- **The rest:**
  - the line numbers 112, 113, 371, 505-506 and 532;
  - the Poisson figures;
  - the triage counts: 70, 48, 1, 2 and 19, with 1 open P0 and 6 open P1;
  - the round-3 report matches the lanes' last texts (13,913 and 19,402 characters) except for the final newline.
- **Walk of R3-A's findings:** all 11 were applied, but three only partly: 1 (the docstring, `git push` and `gh run -R`), 2 (the 02:55–03:10Z qualifier was dropped) and 3 (Apply is missing).
- **Walk of R3-B's findings:**
  - Applied: 1, 5, 7, 10, 11, 12, 14, 17, 19 and 20.
  - Partly applied: 2 (`bot_pr_converge`), 3 (Apply), 6 (C4 not archived), 9 (`_x@`), 13 (the entry header) and 18 (the handoff).
  - Applied, but the text is wrong: 4 (finding 2 above) and 8 (finding 1 above).
  - Applied, but the defect came back: 15 and 16 (finding 10 above).

## WHAT YOU COULD NOT CHECK

- **Nothing live.** No canopy, cascor or browser was run. The Reset escape and the Start alert are read from source only.
- **Who acted.** I could not identify the actor for any arm. Nothing off this host is visible to me.
- **Items labelled not re-derived.** I did not check these: the 00:00:39Z force-push, the converge timeouts, the fixture's five fields, and "merged ahead of validation" for #660 and #678.
- **Unreadable files.** Lane C4's full report is not archived, and the `run_rows_clean.bash` contents are in another session's scratchpad. So "two experiment runs" is unverified.
- **The push tool was not run.** Its dry run needs a remote branch that does not exist yet.

**SECRETS/PII:** No slip. GitHub calls were GETs and GraphQL queries selecting logins, names, dates, SHAs and the signature's first line, never e-mail fields. Transcript greps printed only file names and bounded, redacted substrings. Secret checks printed counts only. **Changed:** no repository file. Scratch files are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r4b.Uzi4wP/`.

---
