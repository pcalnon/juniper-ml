<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 6: Lanes R6-A and R6-B, verbatim

Round 6 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit b0b17cad, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R6-A re-derived round 5's claims from their artifacts; Lane R6-B attacked round 5's corrections (07aef715..b0b17cad). A session limit (HTTP 429) killed both lanes mid-review; each was resumed with its context by a message beginning 'Resume Lane R6-A' or 'Resume Lane R6-B', which asked it to continue under the same brief and settle nothing twice. Each report below is the lane's last assistant text after that resume, which is why the per-report line says round 2. R6-B's report quotes the PEM header its fake-value test used; that literal was reviewed and allowed (--allow-shape), and it carries no key material. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR6A_phase9_ledger_brief.md and laneR6B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round6_corrections.py.

## Lane R6-A -- measurement re-creation, artifact-first

*agent `a37fdcdc11b8aca19` · round 2 · last-assistant-text (after its round-2 brief) · 11139 chars*

**VERDICT: SOUND-WITH-FIXES.** Every claim in the list re-derives from its artifact. The frozen ledger (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `b0b17cad`) has two LOW false statements. Neither changes a count, a disposition or an action. Finding 1 changes one timestamp. I read the ledger's text only after deriving each value. Scratch directory: `S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r6a.ZZ4Ik7`. No repo file was changed.

**TABLE**

| # | Claim | Re-derived value | Result | Command → output |
|---|---|---|---|---|
| 1a | Question asked at 03:34:45Z | Line 4227: AskUserQuestion at `2026-09-24T03:34:45.231Z`. Lines 4228–4259 are metadata and queue records only; nothing was asked again. | **MISMATCH (ledger text)** | `python3 -B $S/ask_scan.py <bc31e993.jsonl>`. `…E2E-VALIDATION-EVIDENCE.md:8795-8796` says "at 07:32:48Z … session `bc31e993` asked" (Finding 1). |
| 1b | Answered at 07:32:48Z | Line 4260: tool_result at `07:32:48.582Z` | MATCH | Same command. `owner_answer_extract.py … 4227 4260` prints the same two records. |
| 1c | PRs named | data#428, ml#2032, ml#2059 and canopy#678, plus "cascor#678 was armed the same way earlier" | MATCH | Line 4227 text |
| 1d | "Mine: fix forward" and its option text | "The sweeper is yours and the merges are intended. I keep validating after the merge and fix forward with follow-up PRs." | MATCH | Lines 4227 and 4260 |
| 1e | Four minutes after `07aef715` | `07aef715` committed 02:28:28-05:00 (07:28:28Z); the answer came 4 min 20 s later | MATCH | `git log --format='%h aI=%aI cI=%cI'` |
| 1f | The four were in the 21:47–22:51Z pass; canopy#678 merged with no arm event | ml#2059 ready 21:47:22, armed :26. ml#2032 ready 22:27:20, armed :27. data#428 ready 22:29:55, armed :59. canopy#678 merged 22:29:21 and has **zero** arm, ready or draft events. No host command merged it: bc31e993's subagent only viewed it and waited on checks, 21:24–21:26Z. | MATCH | `python3 -B $S/pr_events.py` (GraphQL timelineItems across 9 repos: 497 events, 154 PRs). `broad_scan.py` over 21:24–22:29:30Z for canopy#678 |
| 1g | cascor#678's arm was a morning one | Its only arm: 13:32:10Z | MATCH | `events.json` |
| 2a | Ten PRs, 00:47:31–01:08:14Z, ml#2020 twice | 11 arms on 10 PRs, all by `pcalnon`: ml#2013, 2015, 2017, 2020 (00:52:07, then 01:08:14 after `--disable-auto` at 01:03:37), 2029; canopy#655, 658; cascor#672, 673; deploy#228 | MATCH | `events.json` |
| 2b | Nine across four repos, 13:17:53–13:32:10Z | The window holds **10** arms. ml#2031's arm (13:21:08) came from ed11b865's background `safe_merge --pr 2031`, launched 13:21:04Z. The other nine are canopy#660, 670; ml#2032, 2035, 2038, 2041, 2045; data#428; cascor#678. Nine is the correct count of arms no command on this host made. | MATCH | `near_arms.py 90 3 <10 times>` and `broad_scan.py` over 11:00–13:40Z. The 13:26:21Z ceremony run was `--dry-run`. |
| 2c | ml#2057 at 20:23:01Z | Its only arm: 20:23:01Z | MATCH | `events.json` |
| 2d | No command on this host could have made them (early sweep, the nine, ml#2057) | Nothing found. I checked: (1) every tool call from every session and subagent 60 s, 90 s and 150 s before each arm; (2) every mention of these PR numbers since 09-22T12Z; (3) arming verbs in any tool input (`pr merge`, `--auto`, `enablePullRequest*`, `markPullRequestReady`, safe_merge, shepherd, converge, merge_train, sweep, ceremony); (4) Write/Edit content with arming calls since 09-22; (5) repo scripts that can arm (`bot_pr_merge_sweep`, d4 probe, `armed_snapshot_staleness`, retired seqsafety arm-merge): read or uploaded, never run since 09-20; (6) background launches since 09-18: single-PR only. ml#2057: 1f771cb0 opened it at 20:09:28Z and ran only `watch_pr_runs.bash`, which only reads (all 31 worktree copies checked); 1f771cb0 made no call 20:09:38–20:25Z. | MATCH | `near_arms.py`, `broad_scan.py`, `any_mention.py`, all in `$S` |
| 3a | Three background rows | In the ledger's launch scan over [13:17:53Z, 22:52Z] (275 rows), exactly three background rows name morning PRs: 13:35:33.868Z `shepherd_automerge.bash 2041` (it only reads state and runs update-branch; all 18 copies identical to `ab434c9b`), and `safe_merge --pr 670` at 15:29:53.931Z and 15:55:45.405Z | MATCH | `2026-09-24_merge_command_launch_scan.py --start 2026-09-23T13:17:53Z --end 2026-09-23T22:52:00Z` |
| 3b | canopy#670 disarmed 14:27:46Z and 15:52:22Z; re-armed within 6 s of each safe_merge launch | Re-arms at 15:29:59Z (+5.1 s) and 15:55:51Z (+5.6 s) | MATCH | `events.json` |
| 3c | Foreground `gh pr merge 2041 --squash --auto` at 13:35:20Z; ml#2041 has one arm, at 13:25:23Z | Foreground call by 1f771cb0 at 13:35:20.629Z. ml#2041's only arm: 13:25:23Z. | MATCH | Launch scan; `events.json` |
| 4a | 03:02:06Z fast-forward of three commits | Activity API: push, not force_push, `b0223f18→f6363b9a`, by `pcalnon`. Compare API: ahead 3, behind 0. | MATCH | `gh api "repos/…/activity?ref=refs/heads/feat/smart-checks-script-and-reports"`; `gh api …/compare/b0223f18f9c2...f6363b9af286` |
| 4b | Committed by "Paul Calnon" 03:00:20Z–03:01:48Z, valid signatures | `c1698a48` 03:00:20Z, `de3369cd` 03:00:22Z, `f6363b9a` 03:01:48Z. Committer name "Paul Calnon"; two of the three carry author name "Overtoad". All verified with reason valid. Same PGP issuer key as `c666403b`, `4c496443` and `b0223f18`; the control (`fb9b382a`, GitHub's key) differs. | MATCH | `gh api …/pulls/2045/commits --jq` (names, dates and flags only); `$S/sigkey_compare.py` prints only True/False |
| 4c | ml#2045 closed unmerged at 07:29:52Z | state closed, merged false, closed_at 07:29:52Z | MATCH | `gh api …/pulls/2045` |
| 5a | For REPLAYING, `normalize_status` leaves every flag false | The status is "REPLAYING", so `is_running`, `is_paused`, `completed`, `failed` and `monitoring_active` are all false. `is_training` is cascor's `training_active`, which is `is_started()`, which is false (cascor `manager.py:3040`, `state_machine.py:107-108`). | MATCH | `git show e9053227:src/backend/service_backend.py` (:227…); cascor `0e016a7c` |
| 5b | Falls to the `else` "Stopped" (`dashboard_manager.py:7508-7518`) | Exact | MATCH | `git show e9053227:src/frontend/dashboard_manager.py` |
| 5c | Layout default "Stopped" (`:887`) | `id="top-status-display"`, `children="Stopped"` | MATCH | Same file |
| 5d | `state_sync.py:177` feeds `/api/state`, not the bar | `_normalize_status` returns `mapping.get(key,"Stopped")`; used at `main.py:1409` (route `/api/state`, `:1323`). The bar reads `/api/status` (`dashboard_manager.py:7274`). | MATCH | `git show e9053227:src/backend/state_sync.py`, `src/main.py` |
| 6a | Ledger about 780 KB | 779,808 B; base64 1,039,744 B (the "about 1 MB encoded") | MATCH | `git cat-file -s b0b17cad:<ledger>` |
| 6b | `fb9b382a`, GitHub-signed, 683 KB | Committer GitHub, verified, reason valid. Its only file is the ledger, at 683,137 B. It is a commit on ml#2054's branch; the squash `51993b37` has the same size. | MATCH | `git cat-file -s fb9b382a:<ledger>`; `gh api …/commits/fb9b382a`; `git diff --stat fb9b382a^ fb9b382a` |
| 7a | Round 8 (Lane C8) returned MERGE | Lane C8's own transcript (`agent-ab89889ecfd04b44d`, 07:42:02Z): "VERDICT: MERGE", findings "None" | MATCH | `$S/agent_summary.py` |
| 7b | At `b07943d6` the FAQ called the player's Stop canopy's only way to stop a cascor replay | `REPLAY_V2_FAQ.md` status note: "The player's Stop is also canopy's only way to stop a cascor replay…". It is replaced by Reset Training at `26bf27b3`, whose parent is `e9053227`. The branch is not on the remote (404). | MATCH | `git -C <canopy worktree> diff e9053227 b07943d6 -- notes/development/REPLAY_V2_FAQ.md`, then `diff b07943d6 26bf27b3` |
| 8 | Counts | 70 findings (48 fixed, 1 accepted, 2 withdrawn), 19 open: 1 P0 (F-CANOPY-059), 6 P1, 12 P2 | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py`; the ledger's :9443 says the same |
| + | Scan forms: round 3's matched six background launches, round 4's none | On 09-23 the round-2 pattern gives 38 background rows. Round 3 gives 44; the six new rows are all the converge driver. Round 4 and the current version also give 44. | MATCH | `$S/run_versions.py` (each round's tool extracted by `git show`) |

**FINDINGS**

1. **LOW: the ledger gives the answer's time as the question's time.**
   - Quoted, `…E2E-VALIDATION-EVIDENCE.md:8795-8796`: "On 2026-09-24 at 07:32:48Z, four minutes after round 5's artifact was frozen, session `bc31e993` asked whether the sweeper…"
   - Evidence: the AskUserQuestion is at line 4227 at 03:34:45.231Z, and it was never re-asked. 07:32:48.582Z is the answer (line 4260). Round 5's own report states it correctly (`…phase9_ledger_round5.md:91`).
   - Fix: "asked at 03:34:45Z …; the owner answered at 07:32:48Z, four minutes after round 5's artifact was frozen."
   - Changes a number: yes, one timestamp only. Disposition: no. Action: no.

2. **LOW: a "not re-derived" item is false as worded.**
   - Quoted, `…E2E-VALIDATION-EVIDENCE.md:9408-9409`: "…and that no transcript names ml#2057 between 19:50Z and 21:00Z."
   - Evidence: session `1f771cb0` names it at 20:09:28Z (the command that opened it), at 20:09:34Z (the "PR: …/pull/2057" result), at 20:09:37Z ("Watch CI for PR 2057") and at 20:09:49Z (its report). A subagent of session `e6c1cb6d` lists the branch at 20:37:10Z. Command: `any_mention.py 19:50Z 21:00Z`, 5 records.
   - The conclusion this item supports still holds: no command on this host armed ml#2057 (row 2d).
   - Fix: "that no transcript runs an arming-capable command naming ml#2057 or its branch between 19:50Z and 21:00Z (1f771cb0 opened it at 20:09:28Z and ran only the read-only `watch_pr_runs.bash`)." My scan re-derives this, so it can move to "re-derived".
   - Changes a number, disposition or action: no.

**WHAT I COULD NOT CHECK**
- Commands outside Claude Code transcripts: a terminal, cron or systemd timers, other hosts, GitHub-side automation. I read no shell history or timer configuration. "No command on this host" rests on transcripts only; the owner's answer covers the sweeper itself.
- The mechanism of F-CANOPY-055, on which "holds its layout default whatever cascor reports" rests. I verified the status bar from source only, with no live REPLAYING drive.
- Who owns the signing key. I compared issuer key IDs without printing them: they are equal across the night's and the 03:00Z commits and differ from GitHub's.
- Lane R2-F's reflog activity (not in scope). "About 1 MB encoded" is computed, not measured: the push tool is off-limits.

**SECRETS/PII:** No environment variables, tokens or credentials were printed, and no email was requested or printed. Commit queries selected names, logins, dates, SHAs and verification flags only. Signature blobs were held in memory and never printed; only equality booleans were. Transcript reads were bounded and redacted for emails and token shapes. I did not run the forbidden F-058 census or push script, used no `git -C` against the primary checkout, and changed no files. No slips.

---

## Lane R6-B -- adversarial, on round 5's corrections

*agent `a40a56695bf031320` · round 2 · last-assistant-text (after its round-2 brief) · 11612 chars*

**VERDICT: SOUND-WITH-FIXES.** The pass's facts hold. The replay of its 16 substitutions on `07aef715`'s ledger is byte-identical to `b0b17cad`'s (`cmp`), and I confirmed every new timestamp, count and source line I checked. The problems are in the scope given to the owner's answer, one misdated sentence, a new tool whose redaction claim is false, and two over-general or stale statements. Findings 1–3 change a disposition, an action or a number, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` the review continues.

Paths: "ledger" is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `b0b17cad`. "R5 report" is `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round5.md`. Canopy was read at `e9053227` explicitly, because `origin/main` has since moved to `6c4ad9a9` (#679). Cascor was read at `0e016a7c`.

**FINDINGS**

**1. MINOR: the ledger states the scope of the owner's answer three different ways, and item 15 claims more than the owner said.**
- **Quoted:**
  - "Who", :8800-8802: "The question did not name #676, the account's later actions or ml#2045's next morning, so those remain the owner's to confirm".
  - Item 15, :9547-9548: "**Answered for the sweeper (2026-09-24):** the pass over nine PRs, 21:47–22:51Z, was the owner's sweeper ("Who", above), whose merges the owner calls intended."
  - What the evidence cannot support, :9428-9429: "it covers #676's own ready and arm by the pass's pattern, not by name".
- **Evidence:**
  - I printed transcript lines 4227 and 4260 with the extractor. The question names only data#428, ml#2032, ml#2059 and canopy#678, and says cascor#678 "was armed the same way earlier". It then says "All four merged before their final validation rounds … Is that sweeper yours?"
  - The chosen option reads "The sweeper is yours and the merges are intended". "The merges" are the four it named.
  - The pass had five PRs the question never named (:8746-8749): canopy#676, data#431, data#434, ml#2066 and data-client#212.
  - data-client#212 was not a ready-and-arm. Its timeline has only `merged` at 22:30:44Z.
  - #676 merged only after the 01:22:32Z CI re-run, which item 15 itself leaves open.
  - So #676's ready and arm are open in "Who", answered in item 15, and covered by inference in the cannot-support list. R5-B's fix said "#676's CI re-run" (R5 report :97); the pass wrote "#676".
- **Fix:** state one scope in all three places:
  - the answer names four PRs and cascor#678's arm;
  - it reaches the pass's other five PRs, #676's ready and arm included, only by the shared pattern (ready, then arm 4–8 s later);
  - "the merges are intended" was said of the four named PRs;
  - in "Who", write "#676's CI re-run", not "#676";
  - drop "whose merges the owner calls intended" for the whole pass.
- **Changes a number/disposition/action?** Yes, a disposition.

**2. LOW: "Who" gives the wrong time for the question and repeats a false premise.**
- **Quoted** (:8795-8797): "On 2026-09-24 at 07:32:48Z, four minutes after round 5's artifact was frozen, session `bc31e993` asked whether the sweeper that took four PRs out of draft and armed them 4–7 s later…"
- **Evidence:**
  - Line 4227, the question, is timestamped 03:34:45.231Z. Only the answer (line 4260) is at 07:32:48.582Z.
  - canopy#678's timeline has no `convert_to_draft`, no `ready_for_review` and no `auto_squash_enabled`; it was merged directly at 22:29:21Z. So only three of the four were taken out of draft and armed: data#428 (22:29:55Z → 22:29:59Z), ml#2032 (22:27:20Z → 22:27:27Z) and ml#2059 (21:47:22Z → 21:47:26Z).
  - The parenthetical notes the missing arm event, but not that canopy#678 was never a draft.
- **Fix:** "asked at 03:34:45Z and answered at 07:32:48Z". Also note that canopy#678 was never a draft and was merged directly.
- **Changes a number/disposition/action?** Yes, numbers: the time of the question, and four → three.

**3. MINOR: the new `util/ad-hoc/2026-09-24_owner_answer_extract.py` does not redact the tokens its docstring says it does.**
- **Quoted** (`:15-17`): "…each cut to a bound, with e-mail addresses and token shapes redacted." The same claim is in `util/ad-hoc/README.md:742-743`.
- **Evidence:**
  - I ran the extractor on a constructed two-record transcript of fake values and printed only whether each value survived.
  - These came through unredacted: `sk-ant-api03-…`, `sk-proj-…`, `hf_…`, `xoxb-…`, `pypi-…`, a `-----BEGIN OPENSSH PRIVATE KEY-----` header and a `%40`-encoded address.
  - `ghp_…`, a bare `sk-…` and a plain address were redacted.
  - The cause is `SECRET_RE` (`:28`): `sk-[A-Za-z0-9]{20,}` stops at the hyphen in `sk-ant-`.
  - The bound holds: 2,500 characters per block, cut after redaction.
  - This round's brief tells lanes to use the tool, and lane output is archived verbatim under `reports/`.
- **Fix:** widen `SECRET_RE` to cover these shapes, or name the shapes it does redact. The launch scan's `sk-[A-Za-z0-9]{32,}` has the same `sk-ant-` gap, but that predates this pass.
- **Changes a number/disposition/action?** Yes, an action.

**4. LOW: "whatever cascor reports" contradicts Phase 9's own measurement.**
- **Quoted:**
  - :9167-9168: "while F-CANOPY-055 is open it holds its layout default, also Stopped (`:887`), whatever cascor reports".
  - :9575: "while F-CANOPY-055 is open the status bar reads Stopped whatever happens".
  - The same claim is repeated at :9397-9398.
- **Evidence:**
  - :8886-8887: on the parent leg (`:8059`, `78c057e2`), where F-055 is unfixed, the bar APPLIES.
  - :8890-8894: the bar freezes where the page's latency exceeds the tick, "and not on every page".
  - :9422 lists "freezes only on pages slower than the tick" as something the evidence cannot support.
  - :8286: with a 20 s period, the bar applies.
  - During REPLAYING the bar reads Stopped anyway, through its own `else` (`dashboard_manager.py:7508-7518`). So the user-visible claim and item 16's check hold.
- **Fix:** say the bar holds its default "on a page slower than its 1 s tick", and give the `else` branch as the reason it reads Stopped during REPLAYING.
- **Changes a number/disposition/action?** No.

**5. LOW: the README repeats the push-tool size claim that R5-B refuted.**
- **Quoted** (`util/ad-hoc/README.md:759-760`): "in groups of at most 250 KB, with the ledger alone and last".
- **Evidence:** I simulated `pack()` on the 138 files in `f9c81d80..b0b17cad`. It gives nine groups of 113–249 KB, and the ledger's own group at 779,808 bytes (about 1.04 MB base64). The ledger's entry (:9253-9255) now states this correctly.
- **Fix:** add the exception: the ledger goes alone and last, at about 780 KB.
- **Changes a number/disposition/action?** No.

**Walk of round 5's findings:**
- R5-A 1–3: all APPLIED. Finding 4 concerns an overreach the pass added while applying R5-A 2.
- R5-B 1–7: all APPLIED.
  - B1 was applied with the defects in findings 1 and 2.
  - B3 was applied with finding 4's overreach.
  - B4 was applied in the ledger but not in the README (finding 5).
- R5-B's note about the 03:02:06Z push (`f6363b9a` and two others): APPLIED.
- Nothing that would have changed a number, disposition or action was dropped.

**Staleness:** nothing else in Phase 9 contradicts the corrections.
- Nothing still calls the actor unidentified.
- "Twice" survives only in round 4's record, which now carries a note.
- No text still says "two background launches".
- `state_sync.py:177` is no longer given as the status bar's cause.
- :8822 ("opens … after this phase lands and its own review terminates") is a condition now half met, not a false statement.

**CORRECTIONS YOU COULD NOT REFUTE**
- **Membership and arms from the timelines:**
  - canopy#678 has no arm event; cascor#678's only arm is at 13:32:10Z.
  - The early sweep is exactly 10 PRs, 00:47:31Z–01:08:14Z, with ml#2020 armed twice. The morning sweep is 9 PRs; ml#2031's arm came from `safe_merge`. ml#2057 was armed at 20:23:01Z. That makes 20 distinct PRs.
  - My own keyword net over every tool call found no arming command before any of those arms. The nearest calls were read-only queries, a memory append and subagents validating a handoff.
- **Later launches:**
  - The three background launches are at 13:35:33Z, 15:29:53Z and 15:55:45Z.
  - canopy#670 was disarmed at 14:27:46Z and 15:52:22Z, and re-armed at 15:29:59Z and 15:55:51Z.
  - The foreground `gh pr merge 2041 --squash --auto` was at 13:35:20.629Z. ml#2041 has a single arm event.
- **ml#2045 (verified):**
  - The activity API shows a `push` b0223f18 → f6363b9a at 03:02:06Z; compare gives ahead 3, behind 0.
  - The three commits are by "Paul Calnon", 03:00:20Z–03:01:48Z, valid.
  - `%G?`=G with key …831A, the same as `c666403b` and `4c496443`. This settles the key the pass listed as not re-derived.
  - Its draft, disarm and ready fall at 03:04:45Z–03:05:02Z; it was closed at 07:29:52Z and not re-armed.
- **Status bar and REPLAYING:**
  - `:887` is the "Stopped" default; `:7508-7518` is the flag chain with its `else` → "Stopped".
  - The bar reads `/api/status` (`:7274`), where all four flags are false for REPLAYING (`service_backend.py:243-254`).
  - `/api/state` maps REPLAYING to "Stopped" through `state_sync.py:177`.
  - cascor marks the FSM REPLAYING and reports training state Stopped/Idle.
- **Push tool:** Phase 8's `fb9b382a` is a verified web-flow commit that changes one file, the ledger at 683,137 bytes.
- **Scan:**
  - Round 4's pattern adds no rows on 09-23 (705 rows and 44 background launches under both patterns) and one foreground row on 09-20 to 09-23 (507 vs 506). So "round 4's matched no launch" holds.
  - The three forms the docstring names are unmatched (constructed test).
  - Other forms are also unmatched, such as `graphql -F query="$(cat f)"` and `pulls/$(…)/merge`. No tool call from 09-22 12:00Z to 09-24 01:40Z used any of them.
- **Canopy follow-up (item 13):**
  - `26bf27b3` sits on `e9053227` and is on no remote. C8's verdict was MERGE with no findings.
  - The FAQ text at `b07943d6` is as described, and the note now names Reset Training.
- **Archives:** R5-A (14,600 characters), R5-B (12,001) and C8 (6,960) are verbatim against their transcripts.
- **Counts:** triage gives 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open (1 P0, 6 P1).

**WHAT YOU COULD NOT CHECK**
- Nothing was driven live, so I do not know whether F-055's bar would freeze on an item-16 drive page.
- I cannot see actors off this host, nor what the owner meant beyond the option text.
- My "no arming command" nets are pattern and keyword checks; a script run by an unnamed path is outside them.
- I did not run the push tool (so the ~1 MB upload is untested), the F-058 census or the archive dry run. None of them changed in this pass.
- I only skimmed the archived briefs.

**SECRETS/PII:** No slip.
- GitHub: GETs only, selecting events, logins, dates, SHAs, committer names and verification flags. No e-mail fields.
- git: `%cn`, `%cd`, `%G?` and `%GK` only. No `cat-file commit`, `%GS`, `%ae` or `%ce`.
- Transcripts:
  - I checked lines 4227 and 4260 for secret shapes first, printing counts only (zero), then ran the extractor.
  - Other transcript reads were bounded, redacted snippets of tool-call inputs.
  - The fake tokens were checked by true/false only.
- **Changed:** no repository file. Scratch is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r6b.shYDXg/`. The existing `util/ad-hoc/__pycache__/` files all predate this session.

---
