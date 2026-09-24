<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 1 -- four lanes on the frozen ledger (e624c281)

Verbatim final reports of the four round-1 lanes that validated the Phase 9 section of notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md before it landed, 2026-09-24. Frozen artifact: juniper-ml commit e624c281 (branch docs/canopy-e2e-phase9). Briefs: reports/e2e-canopy-2026-09-02/drafts/lane{A1,A2,B1}_phase9_ledger_brief.md and laneB2_phase9_ledger_corrections_brief.md. The fix pass that applied their findings is util/ad-hoc/2026-09-24_phase9_ledger_round1_corrections.py.

## Lane A1 -- measurement re-creation from git objects and the GitHub API

*agent `ae07f07db7c49877f` · round 1 · last-assistant-text (not resumed) · 15085 chars*

| G | Claim | Re-derived | Verdict | Evidence (command, then key output) |
|---|---|---|---|---|
| G1 row 1 | 19:44:37 converted to draft; a comment 1 s later: "Held as draft on purpose … Please do not arm auto-merge on it." | ConvertToDraft at 19:44:37Z. IssueComment at 19:44:38Z. The body starts "Held as draft on purpose:" and ends "Please do not arm auto-merge on it." | MATCH | `gh api repos/pcalnon/juniper-canopy/issues/676/timeline --paginate` (13 events) |
| G1 row 2 | 20:38:41 `4b4cfb16` force-pushed, collapsed onto one signed commit | Force-push at 20:38:41Z, before `2fa134f8`, after `4b4cfb16`. `4b4cfb16` is verified (reason `valid`) and its parent is `0254a7ec`. Its tree equals local `040dc5c1`'s tree (`cbe19d67`). | MATCH | GraphQL `HeadRefForcePushedEvent`; `gh api …/commits/4b4cfb16`; `rev-parse ^{tree}` |
| G1 row 3 | 22:28:04 marked ready | ReadyForReview at 22:28:04Z, actor pcalnon | MATCH | timeline |
| G1 row 4 | 22:28:09 `e581b821`, a merge of main | Committed 22:28:09Z. Parents `4b4cfb16` and `9cdfcad4`. Committer web-flow, author pcalnon. | MATCH | timeline; `gh api …/commits/e581b821` |
| G1 row 5 | 22:28:12 auto-merge armed (squash), storing `4b4cfb16`'s message as the body | AutoSquashEnabled at 22:28:12Z. `autoMergeRequest` is still populated: SQUASH, `enabledAt` 22:28:12Z, `enabledBy` pcalnon. Headline = `4b4cfb16`'s subject + " (#676)". Body = `4b4cfb16`'s body, except GitHub moved `Co-Authored-By` into a final `Co-authored-by` paragraph. `e9053227`'s message equals the stored headline and body exactly. | MATCH (trailer rewritten by GitHub) | `gh pr view 676 --json commits,mergeCommit,mergedAt,autoMergeRequest`; Python diff of the messages |
| G1 row 6 | 22:29:31 `5e52debb`, a second merge of main | Committed 22:29:31Z. Parents `e581b821` and `05f2dfc2`. | MATCH | timeline; `gh api` |
| G1 row 7 | 2026-09-24 01:38:02 merged as `e9053227` | Merged at 01:38:02Z; `mergeCommit` is `e9053227`, parent `05f2dfc2` | MATCH | timeline; `gh pr view` |
| G1 actor | "Every event reads pcalnon" | Every actor-bearing event is pcalnon. The table leaves out two `renamed` events (20:08:53Z and 20:38:41Z). | MATCH | timeline |
| G2 | `git diff e9053227^ e9053227` equals `git diff 4b4cfb16^ 4b4cfb16` outside `index` and `@@` lines; 445 lines each | Raw diffs are 468 lines each. After dropping the 23 `index`/`@@` lines: 445 each, `cmp` exit 0, sha256 `164e2bf6…` for both. The `@@` lines are identical (0 of 15 differ). Only one `index` line differs (CHANGELOG pre-image `b5734e30` vs `92817f8b`). 445 counts the compared lines, which is what the ledger counts. | MATCH | `grep -v -E '^(index \|@@)' … \| cmp`; `wc -l` |
| G3 phrases | The three quoted phrases are in `e9053227`'s message | (1) is verbatim. (2) and (3) are present but wrapped across a line break. | MATCH | `git log -1 --format=%B e9053227`, whitespace-normalised search |
| G3a | Three rounds, and rounds 1 and 2 each changed test code | `5310b81a→c360fb53` (same test blob as `f4d864df→2fa134f8`, `8811f773`) changed `sorted(p["id"] …)` to `sorted((…), key=str)`. `c360fb53→040dc5c1` added `pattern=[…]; assert not pattern, "pattern-matching Interval ids are not supported…"` and dropped `key=str` again. The rounds' non-test source edits are comments and docstrings only. The subagent `.meta.json` files under `259b4d16` show three rounds: Lane A + Lane B, then "Lane B2: round 2", then "Lane B3: round 3", which read `4b4cfb16` at 20:39:53Z. | MATCH | `git diff … -- src/tests/unit/frontend/test_idle_dispatch_cuts.py` |
| G3b | The pair checked was `ce78e0de` against `3a6dea95` | C1, C2 and C3 have `serving.git_sha` `3a6dea95`; X1 and X2 have `ce78e0de` | MATCH | `…/2026-09-23_idle_cuts_live_check_rebuilt_ce78e0de.json` |
| G3c | "3.0 of 6.6, which is 45%" | `2026-09-23_interval_census_c0530279.json` is the only file carrying `total_ticks_per_s`. The rows sum to 6.6; the drain (2.0) plus `metrics-panel-update-interval` (1.0) is 3.0, which is 45.45%. **These are not measured steady-state ticks.** They are nominal rates at the layout defaults, from a static walk of the build at `c0530279` (canopy#670's head, not the PR's parent). The script's own docstring calls this "an UPPER BOUND on schedule, not a measurement". 14 of the 18 Intervals have `disabled` written by a callback (3.4 of the 6.6 t/s). | MATCH on the arithmetic; the numbers are nominal, not steady-state | JSON rows; `util/ad-hoc/2026-09-23_canopy_interval_census.py:22-28,97` |
| G4a | `259b4d16` has `gh pr ready 676 … --undo` and no executed ready, merge or arm of #676; its last entry is 21:01:29Z | The only 676 tool input is L1536 at 19:44:36.556Z: `gh pr ready 676 --repo pcalnon/juniper-canopy --undo`. The 15 raw hits of "gh pr ready 676`, then `python3 util/safe_merge.py…" are prose, not tool inputs. Its `safe_merge.py` hits are grep/sed reads. The subagents have none. The last timestamped entry is 21:01:29.583Z (L3097), which is 86 m 35 s before the ready. | MATCH | tool_use-only scan (`scan_cmds.py`); timestamp scan |
| G4b | No transcript holds a ready or arm of canopy#676; the only other match was cascor#676 | Across 382 candidate files, the only other hits are `6452333c` L1196/L1199 (01:34Z on 09-23), `gh pr merge 676 --repo pcalnon/juniper-cascor --squash --auto`, and the validation orchestrator's own grep patterns (`ddf7847c`, 03:31Z on 09-24). Across all transcripts written after 21:00Z there is no tool call at all between 21:41:01Z and 01:40Z. | MATCH | `grep -r -l --include='*.jsonl'`, then a tool_use scan and an activity census |
| G4c | ml#2059 21:47:22Z, ml#2032 22:27:20Z, data#428 22:29:55Z, each readied and armed 4–7 s apart; #676's pair 8 s apart | ml#2059: 21:47:22 → 21:47:26 (4 s). ml#2032: 22:27:20 → 22:27:27 (7 s). data#428: 22:29:55 → 22:29:59 (4 s). All pcalnon; all three had been drafted at 20:24Z. #676: 22:28:04 → 22:28:12 (8 s). | MATCH | GraphQL `timelineItems` for each PR |
| G4d | The WIP handoff was committed at 21:00:59Z and records #676 as a draft with no auto-merge | `f6861234` (a cherry-pick of `b54e3b3f`) added `HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`. Author date 16:00:59-05:00, which is 21:00:59Z. Its lines 18–19 read "a **DRAFT** with no auto-merge". | MATCH | `git log --diff-filter=A … prompts/thread-handoff_automated-prompts/` |
| G5 | Canopy `main` cites F-CANOPY-056/057 "in the juniper-ml E2E evidence ledger"; juniper-ml `f9c81d80` has no such IDs | At `e9053227`, CHANGELOG.md lines 161–164 carry the phrase. The code comments cite the IDs without it (`replay_player_panel.py:119,542,577,580`; `ws_dash_bridge.js:28,223`; `test_idle_dispatch_cuts.py:17-18`). `git grep -c -E 'F-CANOPY-05[678]' f9c81d80` exits 1. On GitHub, juniper-ml `main` is still `f9c81d80` and canopy `main` is `e9053227`. | MATCH | `git grep`; `gh api …/commits/main` |
| G6 668380ec / 723ee812 | `668380ec` is built on `723ee812` and never pushed; `723ee812` is not an ancestor of `3a6dea95` | `668380ec`'s parent is `723ee812`; it exists only on the local branch `perf/idle-dispatch-cuts`, and GitHub says "No commit found". `merge-base --is-ancestor 723ee812 3a6dea95` exits 1. | MATCH | `branch -a --contains`; `gh api …/commits/<sha>` |
| G6 rebuild | `ce78e0de` cherry-picked onto `3a6dea95`; diff byte-identical to `668380ec`'s; snapshot is a single 76-character deletion | `ce78e0de` was committed 19:22:07Z, while `3a6dea95` was `main`'s head (19:16:48Z to 19:47:31Z). The 5-file code, docs and test diff is identical outside `index`/`@@` (311 lines, sha `71895822…`). The snapshot goes from 7678 to 7602 characters, one deletion. The test file has 9 tests. | MATCH | `cmp_patches.py`; SequenceMatcher |
| G6 PR SHAs | `f4d864df`, `2fa134f8`, `4b4cfb16` on `0254a7ec` | All on GitHub and signed. `f4d864df`'s parent is `3a6dea95` and its tree equals `78c057e2`'s (ce78e0de plus a 5-line CHANGELOG change). `2fa134f8`'s parent is `f4d864df`. `0254a7ec` is `main` (#675). | MATCH | `gh api`; `rev-parse` |
| G6 F-055 SHAs | `884d22fb`, `cf6fb1dc`, `7a4a2e33` kept as provenance; `78c057e2` has `src/` = `ce78e0de` | Local branch `fix/f055-status-bar-running-guard` holds 884d22fb → cf6fb1dc → 7a4a2e33, with `884d22fb`'s parent `ce78e0de`; none is on GitHub. `78c057e2:src` and `ce78e0de:src` are both `4938f685`. The census and drive JSONs serve `:8056` ce78e0de, `:8057` 884d22fb (60 s VOID, 150 s APPLIES), `:8058` 884d22fb and `:8059` 78c057e2. The new test file has 7 tests; `STATUS_BAR_STRAND_TIMEOUT_MS` is 30000. | MATCH | `git log`; `rev-parse`; transcript JSONs |
| G6 #674 | Merged as `894a2cc7` | `mergedAt` 2026-09-23T19:47:32Z, merge commit `894a2cc7` | MATCH | `gh pr view 674` |
| G6 run 2 rule | The script was on `main` from 17:07Z; run 2 began at 19:30Z | `51993b37` (#2054) was committed 17:07:01Z; the script is unchanged through `e624c281`. Run 2 was launched at 19:30:37.9Z (`259b4d16` L914). | MATCH | `git log --all -- <script>`; `exec_scan.py` |
| G6 run 1 rule | "the script and its JSON entered git together in `51993b37`, 3.5 h after the run" | Run 1 was launched at 13:34:36.7Z (`6280349a` L3200). Both files first entered git together in local `ada8e50c` at 16:26:49Z (≈2 h 52 m after the run; branch `worktree-partitioned-twirling-stream`). On #2054's branch they arrived separately (`8faf2126` 16:29:22Z, `eef7a96c` 16:30:10Z). `51993b37` at 17:07:01Z is when they reached `main` (3 h 32 m). | MISMATCH on the commit and the interval; the UNTRACEABLE verdict stands | `git log --all --reflog --diff-filter=A -- <script> <json>` |
| G6 Still owed item 13 lines | `replay_player_panel.py:75`, test `:120`, `:127`, `:138`, `:193`, `ws_dash_bridge.js:28`, `:113-115`, at `4b4cfb16` | `:75` "disabled unless a replay session exists". `:120` `pattern=[p["id"]…]`: KeyError, because `_intervals` appends raw props. `:127` `ids={p["id"]…}`: a dict id raises TypeError. `:138` "enables it while a replay session exists". `:193` `test_disabled_unless_a_session_exists`. js`:28` "…(F-CANOPY-057). Each carries…". js`:115` "(see g-3 emitter)". All three files are byte-identical at `e9053227` (`cmp` 0). | MATCH at both commits | `git show <sha>:<file>`; `awk` |
| G6 other | #671 (Y4/Y7/Y8), #613, #614, `COMMIT_MESSAGES`, 8 landed files, the config and manual lines, `dashboard_manager.py:445`, renderer `:925-937` / `:966-986`, cascor `weights_at` and `_emit_frame`, `_to_dashboard_metric` | `7cd8a9d4` is in `3a6dea95` and not in `723ee812`, and its CHANGELOG names Y4/Y7/Y8. #613 and #614 titles fit. Squash setting is `COMMIT_MESSAGES`. `conf/app_config.yaml:170,181` and `USER_MANUAL.md:1344` hold the stated values, and no `src` code reads them. "the lowest-priority callbacks" is at `:445`. `completeJob` releases unconditionally. `weights_at` has only test callers. Neither `_emit_frame` nor the fixed key set of `_to_dashboard_metric` has `weights`. | MATCH | `git grep`, `gh api`, the installed dash 4.2.0 build |
| G7 | 69 findings: 48 fixed, 1 accepted, 2 withdrawn, 18 open; 4 open P1s: F-CANOPY-055, F-CANOPY-058, F-CASCOR-001, F-CASCOR-002 | total 69, fixed 48, accepted 1, withdrawn 2, open 18 (P1 4, P2 14), with exactly those four P1s | MATCH | `python3 util/ad-hoc/e2e_finding_triage.py` (worktree clean at `e624c281`) |
| G8 | Item 0 takes over Phase 8's item 2; items 13 and 14 are new; Phase 8's 13 and 14 merge into item 12 | Phase 8 → Phase 9: 1→1, 2→0, 3→2, 4→3, 5→4, 6→5, 7→6, 8→7, 9→8, 10→9, 11→10, 12→11, 13+14→12; 13 and 14 are new. Every Phase 8 item has a successor. | MATCH | Ledger lines 8438–8482 compared with 8919–8965 |

**INSTRUMENT NOTES**
- **G4a/G4b.** A transcript scan can only see Claude Code tool calls on this host. It cannot see the GitHub web or mobile UI, other hosts, cloud sessions, the Cursor automations, or a script that doesn't name the PR in its command. A null result can refute a named session; it cannot identify the actor. The activity census makes it stronger: there were no tool calls between 21:41Z and 01:40Z, and no background launch that readies or arms a PR.
- **G4a, "last entry".** `259b4d16` ends with 7 entries that have no timestamp (`relocated`, `cost-state`, …). They were written when the session exited, at about 03:26:51Z (start 19:15:47Z plus a duration of 29,464.6 s). The session was alive but idle during the ready.
- **G3b.** `serving.git_sha` is the canopy process's own build stamp, which reads the same on a dirty tree. I did not re-trace `/proc`, because the ports are off-limits.
- **G3c and G7 check their inputs only for internal consistency.** G3c is arithmetic on the census's own rows. The triage script parses the ledger's own headers, so it could only disagree with the ledger's count text, not with reality.
- **G1 row 5.** Byte equality was never achievable, because GitHub always rewrites co-author trailers.
- **G6 line numbers.** Once the files were byte-identical, the "same lines at `e9053227`" check could not have come out differently.
- I changed no tracked file. All scratch work is in `lanea1.ssXnQu`, created with `mktemp -d` under the session scratchpad.

**ANYTHING ELSE THAT LOOKS WRONG**
1. **"two commits" was already fixed in the PR description.** Lane B3 read the description at 20:39:55Z (subagent `agent-a43a64bd` L45). The 20:40:10Z edit, 15 s later, replaced "Both commits…" with "one GitHub-signed commit, `4b4cfb16`" (GraphQL `userContentEdits`). The final description still says "seven files", "this PR's parent, `main` `3a6dea95`" and "Live check of the build against its exact parent". So Still owed item 13's refresh is still owed, but not for "two commits". Round 3's report, `2026-09-23_validator_reports_phase9_round3.md` line 34, is where that finding came from.
2. **"`723ee812`, canopy#670's branch" is loose wording.** `723ee812` is a local merge commit (parents `29cc9622` and `0fca86e9`) on the local branch of that name. It is not among #670's 9 commits and is not on GitHub.
3. **The 45% correction drops the word "nominal".** The ledger's "3.0 of 6.6, which is 45%" carries the "steady-state ticks" framing over from the commit message. Canopy's own PR description (line 3) is more precise: "6.6 nominal steady-state ticks/s". The census also came from a different build (`c0530279`).
4. **The host-load figure does have a raw artifact.** Transcript `259b4d16` holds the `uptime` outputs: "load average: 7.89…" at 19:30:31Z and "13.10…" at 19:40:52Z, plus `clamscan` in the second result. The figure is traceable to a raw transcript, though no committed artifact holds it.
5. **G8, minor.** Phase 8 item 2's second half ("drive F-CANOPY-025's allow arm") is not restated in item 0 for the second fix. It survives only through "Matrix effect": "stays open with F-CANOPY-055".

**SECRETS/PII:** One slip. When I dumped `autoMergeRequest` for G1, the tool output included its `authorEmail` field, the owner's commit email address. It was not sent anywhere and is not repeated here. No tokens, environment variables or credential files were printed. The transcript greps printed only file names and bounded command substrings.

---

## Lane A2 -- measurement re-creation from the raw evidence tree

*agent `ac63bcb842c91dfbf` · round 1 · last-assistant-text (not resumed) · 18790 chars*

Paths used below: `W` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda` (frozen at `e624c281`). `T` = `W/reports/e2e-canopy-2026-09-02/transcripts`. `C` = `W/reports/e2e-canopy-2026-09-02/consensus`. `S0` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814/scratchpad`, the authoring session's scratchpad (not committed, and on tmpfs). `J` = `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/259b4d16-1621-41ee-bdc9-e58cf7964814.jsonl`, the authoring session's transcript. `L` = a line of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `e624c281`. `DM` = canopy `884d22fb:src/frontend/dashboard_manager.py`.

| # | claim | re-derived | verdict | evidence |
|---|---|---|---|---|
| R1.a | Live-check table (L8540-8544), all 30 cells | C1 7115.1 ms, n 109, dead timer present, drain disabled false, 5 ticks, `3a6dea95`. X1 3912.6, 170, absent, true, 0, `ce78e0de`. C2 5336.9, 127, present, false, 7, `3a6dea95`. X2 5415.8, 136, absent, true, 0, `ce78e0de`. C3 5275.5, 131, present, false, 7, `3a6dea95`. The ledger's rounding to seconds is correct. | MATCH | `T/…live_check_rebuilt_ce78e0de.json` `windows[i].latency.{p50_ms,n}`, `.structure.*`, `.serving.git_sha` |
| R1.b | STRUCTURE PASS, SESSION PASS, LATENCY INCONSISTENT, ERRORS no worse (L8546) | I ran script lines 188-206 verbatim over the JSON with `verdicts` removed; the result equals the stored dict. X1 3912.6 < min(C1, C2) = 5336.9 holds. X2 5415.8 < min(C2, C3) = 5275.5 fails. X2 > max(C2, C3) = 5336.9, so INCONSISTENT. Run 1's JSON also recomputes to its stored CONSISTENT / 0.76. | MATCH | `W/util/ad-hoc/2026-09-23_idle_cuts_live_check.py:188-206`. The rule code matches the docstring. |
| R1.c | "X/C 0.79" | 4664.2 / 5909.17 = 0.78932 | MATCH | same |
| R1.d | "Without C1, X/C is 0.88" (L8552); run 1 "0.80" (L8612) | 0.87901 for run 2; 0.80416 for run 1 | MATCH | `T/2026-09-23_idle_cuts_live_check.json` |
| R1.e | X2 was 1.48% slower than C2 and 2.66% slower than C3 | +1.4784% and +2.6595% | MATCH | p50 values |
| R1.f | SESSION: enabled in 1.7 s with 5 ticks, disabled in 2.5 s with 0 after, "exactly at its floor" | `enabled_after_s` 1.7, `ticks_10s_enabled` 5 (the rule needs ≥ 5), `disabled_after_s` 2.5, `ticks_10s_cleared` 0 | MATCH | `windows[1].session_path` |
| R1.g | "Console errors were 0 in every window" | `console_error_count` is 0 in all five windows | MATCH, but the count covers only time after page load (R5.f) | same JSON |
| R1.h | Lane A: 5–7 drain ticks per 10 s (L8596) | drain 5 / 7 / 7; dead timer 6 / 6 / 5 | MATCH | `structure.start` and `after_10s` `n` |
| R1.i | Rule unchanged; run 2's rule traceable (on main from 17:07Z, run began 19:30Z) | `git diff 51993b37 e624c281` on the script is empty. `51993b37` was committed 17:07:01Z and is on `origin/main`. The run command was issued at 19:30:37.9Z. | MATCH (content) | git; `J` |
| R1.j | "L still sat at 3.9–5.4 s" on the cuts leg (L8935) | 3.91 s and 5.42 s | MATCH | same JSON |
| R2.a | Parent row (L8699) | 60 s window (60.8 s elapsed); 30 delivered (29 requests); 31 watched / 0 executed; 0 latency changes on recount; DOM `Stopped` / `0` / `""`. `_baseline_verdict(30,0,0)` gives NEVER-APPLIES. SHA `ce78e0de`. | MATCH | `…census_f055_parent_8056.json`; the rule was AST-extracted from `census.py:156-161` |
| R2.b | Fix row, 60 s (L8700) | 7 delivered (8 requests); 9 / 8; 7 changes; DOM `Completed — early stopped` / `76` / `Latency: 5ms`; VOID because 7 < 10 | MATCH | `…_fix_8057.json` |
| R2.c | Fix row, 150 s (L8701) | 20 delivered (19 requests); 20 / 20; 19 changes; same DOM; APPLIES (20/20 ≥ 0.25) | MATCH | `…_fix_8057_150s.json` |
| R2.d | VOID floor; windows 60 s / 150 s | `census.py:157` returns VOID when fewer than 10 are delivered; `seconds` is 60 / 60 / 150; the rule code has only docstring changes since `51993b37` | MATCH | git diff |
| R2.e | "28 of 29 responses applied across the two fix runs' 210 s" (L8793) | 28 is the executed count (8 + 20) and 29 is the watched count (9 + 20). Responses delivered on the wire were 7 + 20 = 27 (requests 27). Latency changes were 26. | MISMATCH. 29 counts in-flight requests, not responses, and executed (28) exceeds delivered (27). | `baseline.renderer` vs `baseline.wire` |
| R2.f | "(n = 3 windows, 29 responses on the fix)" (L8900) | The fix had 2 windows and 27 delivered responses | MISMATCH | same |
| R2.g | "The lane clocked itself at ~8 s" (L8704, L8710) | Mean interval between latency changes: 8.69 s (60 s run) and 8.04 s (150 s run). Median interval: 7.37 s and 7.47 s. Window ÷ executed: 7.61 s and 7.55 s. The census docstring says "~8.6 s". | MATCH (approximate). The mean runs high because identical consecutive values do not register. | `store_changes` timestamps |
| R2.h | "That matches F-CANOPY-035's measured 5.5–7.3 s" (L8706) | Every estimator gives 7.4–8.7 s, at or above the top of Phase 6's 5.5 / 6.1 / 7.3 s (L6972) | MISMATCH (loose) | as above |
| R3.a | Fix: LANDS 13.0 s after page load | 28 of 28 samples live; first enabled sample at 13.0 s (still disabled at 11.7 s). `t0` is taken after `open_dashboard` and `ensure_no_modal` return. | MATCH as a lower bound only (the ledger says so at L8748) | `…allow_arm_demo_drive.json`; `_verdicts` AST-extracted from `drive.py:125-148` equals the stored verdicts |
| R3.b | Parent: LANDS 19.7 s | 33 of 33 samples live; first enabled at 19.7 s | MATCH | `legs[1]` |
| R3.c | DENY returns at 7.8 s (fix) and 2.7 s (parent) | Fix still enabled at 1.6, 4.1 and 6.4 s, disabled at 7.8 s. Parent still enabled at 1.1 s, disabled at 2.7 s. | MATCH | `deny_samples` |
| R3.d | BAR APPLIES on both legs | Recomputed APPLIES on both | MATCH (on the fix the rule was already met at 0.3 s; R5.e) | `status_text` |
| R3.e | "step 137 → 143" | Fix: 137 at 54.0 and 55.6 s, 143 at 60.1 s; 10 step changes from 13.0 s on | MATCH | `step_text` |
| R3.f | Parent bar at its defaults for its first 18.5 s | 10 samples from 0.1 to 18.5 s at `Stopped` / `0`; first change at 19.7 s | MATCH | `allow_samples` |
| R3.g | Parent leg `78c057e2` with `src/` = `ce78e0de` | `rev-parse 78c057e2:src ce78e0de:src` gives `4938f685…` for both | MATCH | git in juniper-canopy |
| R4.a | "M1–M6 all MATCH" (L8566) | Cuts Lane A: M1c "'one sentence' MISMATCH (it is three)"; M4c n/a; M5 "MATCH for this run, with the gaps"; M6 "Count MATCH; 'at ce78e0de' corroborated only indirectly" | MISMATCH. L8569 itself lists "one sentence was three". | `C/…phase9_round1.md:16,21-23` |
| R4.b | "M1–M5 all MATCH" (L8727); "Lane A: every measurement MATCH" (L8897) | F-055 Lane A: M2 rows are CAUGHT, with (iv) "incidentally" and (v) "only when node is present"; M4b "does not discriminate"; M4c "code-identical for the parent" (the parent leg was `78c057e2`, not the claimed `ce78e0de`); M5a "one false-positive path". No row says MISMATCH. | MISMATCH (overstated; qualifiers dropped) | `round1.md:177-194` |
| R4.c | "B2 reproduced every number" (L8601) | B2 could not check the load readings (7.89 / 13.10) or "C1 started 40 s after the test suite" | MISMATCH | `round2.md:105,115` |
| R4.d | "The raw records rule each gap out, or the rule does not use the field" (L8578) | Lane A says the `ticks_10s_cleared` gap "cannot rule this out; it can only be argued improbable", and the SESSION rule (script line 194) uses that field | MISMATCH. The conclusion still holds by argument: the `disabled_after_s` read just before found the node present. | `round1.md:40` |
| R4.e | "Run 2's rule is traceable", listed under "Rule provenance (Lane A)" | Not in Lane A's report, which covers run 1 only (`:65`); the content itself re-derives (R1.i) | NO ARTIFACT (for the attribution) | — |
| R4.f | "A tab change mid-request re-opens the eviction window for one cycle", under "Lane A's corrections" (L8741) | Not in Lane A's report. It is the text of canopy `7a4a2e33` (diff lines 19-20 and 72). Lane B's repro shows one tab click giving 0 of 28 over ~120 s. | NO ARTIFACT (attribution), and contradicted by Lane B | `round1.md:275` |
| R4.g | 6806 passed / 4 skipped / 0 failed; collection count 6810 | Lane A M6 agrees. The raw log has 95 progress lines, 6806 `.`, 4 `s`, no F or E, no "passed" line and no SHA. | MATCH, but Lane A's "only indirectly" caveat is dropped | `round1.md:23`; `S0/cuts_full_suite.log` |
| R4.h | 7 of 9 fail on `3a6dea95`; `cmp` exit 0 with the same sha256; C1 40 s; 0.88 | All in Lane A's report (M3, M1a, anything-else item 3) | MATCH | `round1.md:14,18,62-64` |
| R4.i | Host load 7.89 / 13.10 and two `clamscan` processes at ~80% | Not in any report or committed transcript. The session transcript has them at 19:30:31.055Z and 19:40:52.414Z, with `clamscan` at 84.2% and 80.8% (ps lifetime averages). | NO ARTIFACT in the committed record; traceable only in `J` | `J` |
| R4.j | Lane B (cuts): 178 callbacks, 17 Intervals, MAJOR / MINOR / NITs | Present | MATCH | `round1.md:130,151` |
| R4.k | B2: five places, four comments, 0.88 / 0.80, 32–42% | Present (0.8790 / 0.8042; −41.9% / −32.3%) | MATCH | `round2.md:30-94` |
| R4.l | "168 affected tests pass, and pre-commit is clean" (L8617) | In no report or committed transcript. `S0/cuts_r2_tests.log` reads "168 passed in 128.82s" with no SHA. Per `J` (20:35:21Z) that run covered 8 named files, and pre-commit ran on 4 files with output piped through `grep -E "Failed\|modified\|reformatted"`. | NO ARTIFACT | `J`, `S0` |
| R4.m | B3: 52 + 111 + 321 tests, 7 of 9 on `0254a7ec`, 8 files, 45% | Present. 45% also re-derives from the interval census: 2.0 + 1.0 of 6.6 ticks/s. | MATCH | `round3.md:84,94-97`; `T/…interval_census_c0530279.json` |
| R4.n | 19 of the three files' 94 tests fail and 75 pass | Lane A M1b: 5/2 + 13/32 + 1/41 | MATCH | `round1.md:178` |
| R4.o | "6823 passed … the parent's 6806 plus exactly the 17 new tests" (L8689) | No lane ran this. `S0/f055_full_suite.log` has 6823 `.` and 4 `s` ("6823 passed, 4 skipped"), run at 20:04:33Z, no SHA. The +17 re-derives from an AST count over canopy objects: f055 file +7; `test_poll_gating.py` 22 → 32 (+10); stage2 42 → 42. | NO ARTIFACT in the committed record; the arithmetic matches | `git show ce78e0de` / `884d22fb` |
| R4.p | All six mutations caught; (iv) incidental; (v) only with node | Lane A M2 (i)–(vi) | MATCH | `round1.md:179-184` |
| R4.q | 20 of 20 in 150 s; 4–7 s at p50; 18.5 s; "13 s" a lower bound | Lane A: 20 watched / 20 executed; 7115 / 3913 ms (the five windows span 3.91–7.12 s); anything-else item 1 | MATCH | `round1.md:225-237` |
| R4.r | Lane B F-055: 7/7; 0/51; 4/4 then 0/28 over ~120 s; 352 s; 5 fires in 240 s, 3 evicting, 17 of 56; 0/21; 37–44 an hour; 0/24 | All present with the same values. Raw output survives for only three of them: `run_watchdog_r3.json` (5 fires at 57.8 / 92.8 / 152.8 / 187.8 / 232.8 s; 56 requests, 39 applied; drops follow fires 2, 4 and 5), `run_apply.json` (24 requests after release, 0 applied) and `run_watchdog.json` (23 / 23, no fire). No raw output exists for the other five figures. | MATCH (to the report) | `round1.md:271-305`; `S0/laneB_f055.Iywb95/` |
| R4.s | "28 of 29", placed inside Lane B's list (L8792) | Lane B says it did not read the census transcripts, so this is the orchestrator's figure; the unit is wrong (R2.e) | NO ARTIFACT (attribution) | `round1.md:339` |
| R4.t | "445 lines each, cmp exit 0" (L8657) | Both diffs are 468 raw and 445 stripped lines with identical sha256 | MATCH | git in juniper-canopy |
| R4.u | 69 findings: 48 fixed, 1 accepted, 2 withdrawn, 18 open, 4 P1 | `e2e_finding_triage.py --note <frozen ledger>` gives the same counts; the P1s are F-CANOPY-055, F-CANOPY-058, F-CASCOR-001 and F-CASCOR-002 | MATCH | — |
| R5.a | Census for "parent NEVER-APPLIES / fix APPLIES" | It could have returned NEVER / RARELY / VOID for the fix, and the period arm showed a parent-class build can score APPLIES | ADEQUATE | Lane A M3e |
| R5.b | Census "could not have produced the failure, because its window held none of the triggers" (L8900; L8506) | Two of F-058's trigger sources were live. The watchdog was armed throughout both fix windows (L8793 says "by chance, no watchdog false fire"). The gate's mount write fired on each page before its window: `DM:482` registers `(_STATUS_BAR_INTERVAL, None)`, `:2491` writes every registered lane, `:2496` sets `prevent_initial_call=False`. A cascade from either would have shown in the window. Taking Lane B's modelled 29–33 evicting fires per hour, the chance of none in 210 s is about 0.15–0.18. | MISMATCH. The census could have failed. Its clean result is weak evidence against the modelled rate and against a mount-time strand on canopy, and the ledger uses neither. | — |
| R5.c | Live check (STRUCTURE / SESSION / LATENCY) | All three can fail: LATENCY was CONSISTENT in run 1 and INCONSISTENT in run 2. The spread across control windows (5275–7115 ms) is far larger than X2's +1.5% / +2.7%. SESSION uses a synthetic setProps write (script lines 130 and 142). | ADEQUATE within the limits the ledger states (L8904) | — |
| R5.d | Drive used for "a demo page is light enough" (L8721), "froze where the page's delivery latency exceeds the tick" (L8724) and the narrowing of F-CANOPY-025 (L8912) | The drive records no latency (`drive.py:114-122`), and the ledger itself calls this unmeasured (L8746). The parent's own samples show an 18.4 s freeze at start, and step 309 held from 24.2 to 39.9 s while the server epoch ran 310 → 321. | Cannot fail on the variable these claims depend on | `legs[1]` |
| R5.e | Drive BAR on the fix | The bar already read `Running` at 0.3 s, from an apply before `t0` | Cannot fail on the fix | `drive.py:139` |
| R5.f | "Console errors were 0" | The listener is attached after `open_dashboard`'s goto and waits (script lines 111-112; `e2e_w3_params_driver.py:214-218`), so load-time errors are invisible to the JSON. The uncommitted run log has no CONSOLE lines. | Blind for the load phase | `S0/idle_cuts_live_check_rebuilt.log` |
| R5.g | "pre-commit is clean" (L8617) | The output was grep-filtered, so a pre-commit crash would also read as clean. B3's independent pinned run on `4b4cfb16` mitigates this. | Could not fail on the crash path | `J` 20:35:21Z |

INSTRUMENT FINDINGS
1. **The census mixes units.** `watched` and `executed` count renderer callback objects, while `wire.responses` counts HTTP responses. The two drift by 1–2 at window edges; in the 60 s fix run, executed is 8 against 7 delivered. The ledger's "responses" figures take the renderer counts.
2. **The census's "~8 s" is a mean of latency-change intervals.** Identical consecutive values do not register (20 executed against 19 changes; 8 against 7). The cadence per applied response is about 7.5 s.
3. **The census records no gate writes, tab changes or watchdog fires.**
   - "No tab switch" holds by source, which I checked:
     - each run gets a fresh browser context (`e2e_w3_params_driver.py:188-190`);
     - the layout default is `active_tab="metrics"` (`DM:1889`), which is "Training Metrics" (`:2582-2583`);
     - the CAN-016a restore is equality-guarded;
     - dash-renderer returns early on a setProps with no changed props (`dash_renderer.dev.js:4662-4671`, JuniperCanopy1).
   - "No watchdog fire" is inferred only from the 28 of 29.
4. **The drive's timings are coarse, and its ALLOW time is not the first apply.**
   - Samples are 1.85–2.21 s apart, not 1 s, so land and return times are accurate to about ±2 s.
   - On the fix, a feeder response had already applied before `t0` while the button stayed disabled until 13.0 s.
5. **"Predictions fixed before each run" cannot be traced in git for the census or the drive.**
   - Both entered git in `5a0e4ea9`, authored 20:41:35Z, after the runs (19:50–20:03Z).
   - They are traceable only in `J`:
     - the drive script was written at 19:35:39.9Z, and every function is AST-identical to `e624c281` (only docstring ports changed);
     - the census edits at 19:50:15.5Z and 19:55:05.3Z precede the runs at 19:50:25.8Z and 19:55:08.7Z.
   - `J` has roughly a 30-day lifetime. This is the same class Lane A flagged for run 1.

ANYTHING ELSE THAT LOOKS WRONG
1. **The fix description repeats a refuted claim.** L8675-8677 says "the tab gate never writes it, so F-CANOPY-053's hazard … cannot arise" and does not flag it. L8737 and L8849 contradict it, and so does the source (`DM:2491`, `:2496`, `:482`).
2. **"For one cycle" conflicts with F-CANOPY-058.** L8741-8742's "for one cycle" and L8745's "release one request early" sit next to F-CANOPY-058's cascade (L8846-8848) without being reconciled.
3. **The ledger both asserts and disclaims the demo-page claim.** L8722 states "a demo page is light enough" as fact; L8746-8747 calls the same claim unmeasured.
4. **The summary omits that the drive does not discriminate.** L8499-8500 says the allow arm landed on the fix, but it landed on the parent too.
5. **Much of the evidence is not durable.**
   - These exist only in `S0` (tmpfs), with no SHA stamps: `cuts_full_suite.log` (6806), `f055_full_suite.log` (6823), `cuts_r2_tests.log` (168), the file mtime behind C1's "40 s", and Lane B's repro scripts and outputs, which are the evidence for the P1 F-CANOPY-058.
   - These served canopy commits are reachable from no remote ref in the local canopy clone: `ce78e0de`, `78c057e2`, `668380ec`, `723ee812`, `884d22fb`, `cf6fb1dc` and `7a4a2e33`.
6. **Two committed figures for one cadence.** The ledger says ~8 s; the census docstring (`census.py:73,80`) says ~8.6 s.
7. **Unreconciled disagreement about node on CI.** Lane B says "CI runs the node test" (`round1.md:333`); B3 says `ci.yml` has no setup-node step (`round3.md:104`). Mutation (v) is caught only when node is present.
8. **"The latency prediction was wrong" is only half the record.** The pre-registered X/C band of 0.60–0.85 contained 0.79; only the CONSISTENT prediction failed.
9. **C1's "40 s" is measured to `read_at` (19:30:45Z).** The run command was issued about 32 s after the suite log's last write (19:30:05.5Z). The suite (19:22:18Z–19:30:05Z) overlapped both legs' launches (19:23:58Z and 19:24:07Z) in the worktree the X leg served from.
10. **The ledger drops a relevant Lane B run.** Lane B's second run at R = 7–8 s had no fire in 200 s (23 of 23), which matters for the false-fire rate.
11. **The Still-owed gap list (L8954) omits the `paths.strs` gap** that L8575 lists.

SECRETS/PII: none printed. (Changed: no repository files. Scratch output, which is extracted canopy files, diffs and commit messages but no scripts, is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/laneA2.MmtzkV/`.)

---

## Lane B1 -- adversarial review of the conclusions, from canopy/cascor source and the installed renderer

*agent `af2c02df15af1823a` · round 1 · last-assistant-text (not resumed) · 16535 chars*

**VERDICT: SOUND-WITH-FIXES.** Phase 9's main dispositions hold on canopy `main` `e9053227`: F-CANOPY-055 stays OPEN, its first fix is not mergeable, and the mechanisms of F-056, F-057 and F-058 hold. What needs fixing before landing is the scope of three findings, a live-confirmation plan that cannot fail, the lesson item 14 states, dropped residue, and one disposition that contradicts the ledger's own count.

Line references are to `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `e624c281` unless another file is named. Canopy paths are at `e9053227`; cascor paths are at `origin/main` `0e016a7c`, which matches the remote.

## FINDINGS

**1. MAJOR — F-058's trigger list misses a trigger I reproduced (B-a).**
- **Text attacked** (`…E2E-VALIDATION-EVIDENCE.md:8848-8853`): "Mid-request re-enables come from: the fused CAN-000/tab gate, which writes every registered lane on every tab switch, Apply change and mount; the Apply release; the strand watchdog's false fires."
- **The missing trigger.** In production, `update_metrics_store` has two Inputs: `metrics-store-interval.n_intervals` and `metrics-panel-display-mode-store.data` (`dashboard_manager.py:4710-4717`).
  - Canopy's own comment at `:4702-4706` says a mid-flight display-mode change "evicts exactly as a tick would". The evicted request's `completeJob` then releases the guard under its successor, which is F-058's own cascade.
  - Repro, in a synthetic dash 4.2.0 app with this exact wiring (server latency 3 s, headless Chromium, port 9471, now torn down): `f058repro.6JTgea/app.py` and `drive.py` in my scratchpad.

    | run (90 s after the trigger point) | requests | responses | applied |
    |---|---|---|---|
    | one mid-request change of the second Input (twice) | 44–45 | 45 | **0** |
    | no-trigger control (twice) | 22–23 | 23 | 23 |

  - The display-mode Store is written by user input (`metrics_panel.py:1352-1366`). Its full and hidden_units modes are exactly the ones where the REST poll is not WS-gated (`dashboard_manager.py:7836-7842`).
- **"Mount" is listed without a caveat.** Lane B could not check canopy's own mount order (`…phase9_round1.md:336`). The gate's mount write was present during #613's live verification and during this phase's 150 s census (20 of 20 applied).
- **The Apply is counted twice, and one half is wrong.** "Apply change" includes the Apply start, whose clamp write is `true` and so is not a re-enable. "The Apply release" is that same gate write: the lane has only three writers (the gate, the watchdog and the guard's `sideUpdate`).
- **Fix:** state the class as "any mid-request re-request or re-enable". Add the second-Input trigger, qualify mount, and fold the two Apply entries into "the Apply end".
- **Changes an action:** yes. Item 0, the fix's real-renderer tests and the pacer design all have to cover a non-interval Input.

**2. MAJOR — Item 0's live confirmation of F-058 cannot fail as written (B-e).**
- **Text attacked** (`:8930-8931`): "a metrics-store census with a tab switch timed mid-request, an Apply spanning a request, and ≥ 10 idle minutes."
- **Applies cannot be counted on the idle trio.** The feeder returns `no_update` in three cases: WS live in window mode (`dashboard_manager.py:7841-7842`), non-modulus ticks in the full modes (`:7847-7848`), and a fetch equal to the store (`:7905-7906`). The trio holds a completed run whose history is static, so every response after the first is a 204.
  - The arc's census rule scores `executed == 0 and lat_changes == 0` as NEVER-APPLIES (`2026-09-23_status_bar_apply_census.py:156-161`). It does not count 204s (`…phase9_round1.md:209`).
  - So a healthy lane scores NEVER-APPLIES, and the census "confirms" F-058 whether or not it occurs.
- **The Apply trigger has no permitted leg.** An Apply goes through `/api/set_params` to `backend.apply_params` (`main.py:4334`, `dashboard_manager.py:8955`), which PATCHes cascor. On a trio leg that writes the shared fixture. On a demo leg the page may be faster than the tick (`:8721-8722`), and then no cascade can form.
- **Fix:** count evictions, not applies: overlapping in-flight `update_metrics_store` requests, or removals from `watched`. Alternatively, produce a changing history with WS stale or full mode. Name a leg where an Apply is allowed, and add the display-mode trigger.
- **Changes an action:** yes.

**3. MAJOR — Item 14 states a different lesson from the one the phase names (B-e).**
- **Text attacked:** `:8963-8965` "Any future census of a self-clocked lane needs a window sized to its cadence".
- **Evidence:** the lesson the phase names is at `:8900-8901`: the census "held none of the triggers". The predecessor handoff (`HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md:107-108`) had both halves: "Size the window … and include the triggers." Item 14 kept only the window-size half.
- **Fix:** add the rule that a verification census must (a) put every known trigger inside its window, or name the ones it cannot see, and (b) count an observable that differs between pass and fail on that leg.
- **Changes an action:** yes.

**4. MAJOR — F-056 is scoped to Stop, but its mechanism drops every control's result (B-a/B-b).**
- **Text attacked:** the title at `:8805`, and the fix direction at `:8821-8822`, "handle `stop` before `if data:`".
- **Evidence:** `_merge_session` (`replay_player_panel.py:839-875`) overlays cascor's `{status, data, meta}` envelope (cascor `common.py:59-73`, passed through verbatim). None of the session's display keys sits at the envelope's top level.
  - Probe of `e9053227`'s `_merge_session` with cascor-shaped envelopes:
    - speed(−5) leaves speed at 1.0;
    - seek(40) leaves `time_index.current` at 0;
    - play leaves `playing` at None;
    - stop leaves `snapshot_id` and REPLAYING in place.
  - `render_session` then writes those stale values back into the sliders. The renderer prunes the resulting cycle (`dash_renderer.dev.js:2972-2981`), so the UI and cascor diverge.
  - As a result, the manual's documented readouts (`USER_MANUAL.md:757-758`, "readout `current / end`" and "0 pauses (`Paused (0×)`)") never reflect a control against cascor. This is from source and a probe; I did not drive it live.
- **Why it matters beyond Stop:**
  - It is F-CANOPY-013's envelope-nesting class (`:3848`) on a third site that canopy#532's sweep missed.
  - `test_success_merges_session` (`test_replay_player_panel_gate_coverage.py:167`) and `test_backend_response_overrides` (`test_replay_player_panel.py:273`) pass flat dicts the route never returns.
  - Handling Stop first fixes one of six actions. Unwrapping `data` alone would put the echoed `snapshot_id` back on Stop.
- **Fix:** widen the title; unwrap the envelope, map `result`, and handle Stop explicitly; test all six actions with the real envelope.
- **Changes a disposition and an action:** yes. By plan §6.3 ("breaks a documented behaviour") it argues P1.

**5. MAJOR — F-057's history is wrong (B-a).**
- **Text attacked** (`:8834-8835`): "either the emitter was never merged, or it lives on an unfetched branch."
- **Evidence:** the g-3 emitter was merged twice, both times into stacked feature branches, and never reached `main`:
  - cascor#187 merged 2026-05-03T07:31:04Z into `feature/can-015g-2-replay-weight-cache` (merge commit `d85c9ddd`);
  - cascor#190, "[retarget #187, stacked on #189]", merged at 20:05:12Z into `…-v2` (`dbc25277`), 13 minutes after g-2's #189 had landed on `main`;
  - both base branches return 404, and `compare main...d85c9ddd` reports diverged, 6 ahead and 519 behind.
- **What still holds:** the orphaned diff adds `metrics["weights"]` in `_emit_frame`, which is exactly the key `_to_dashboard_metric` strips. So both halves of F-057 stand.
- **Fix:** record this history. The fix is to re-land #190's diff and add canopy's relay key, and to sweep cascor for other stacked PRs merged into bases that had already landed.
- **Changes an action:** yes.

**6. MAJOR — Residue lost from Phase 8 and the handoff (B-c).**
- **(a) The redesign's live verification.** Phase 8 item 2 (`:8448-8449`, "Then drive F-CANOPY-025's allow arm…") and the handoff's item 4 (`HANDOFF_…phase9…md:89-90`, "then the census plus the triggers live, consensus rounds, PR and merge") appear nowhere. Item 0 names only real-renderer tests. This phase's F-025 drive "does not discriminate" (`:8721`), and no discriminating drive is owed anywhere.
- **(b) The Apply-clamp half of Phase 8 item 6** (`:8454-8456`). Item 5's "Superseded by F-CANOPY-058" is a dependency clause, not coverage. F-058's text never names the clamp defeat (the lane keeps polling through an Apply), although the ledger records it twice (`:8739-8742`, `:8776-8777`).
- **Changes an action:** yes.

**7. MAJOR — F-025's disposition contradicts the ledger's own count (B-b).**
- **Text attacked** (`:8912-8913`): "…narrowed to pages slower than the tick, and stays open with F-CANOPY-055."
- **Evidence:** `e2e_finding_triage.py` reports "FIXED P1 F-CANOPY-025", and the count lists 4 open P1s without it (`:8917`). The narrowing also rests on a drive that recorded no latency (`:8746-8748`).
- **Fix:** either reopen F-025, which makes the count 19 open and 5 open P1, or state that it stays counted FIXED with its regression tracked only under F-055. Move the narrowing into "cannot support".
- **Changes a number and a disposition:** yes.

**8. MINOR — F-058's production blast radius is overstated for a P1 (B-b).**
- **Text attacked:** `:8856-8857`, the "REST backstop can stop applying for minutes" sentence.
- **Evidence:** the only demonstration is the unmerged F-055 wiring, whose feeder always returns data. On the production lane a stall is visible only with WS stale or in the full modes, and only while the history is changing (see finding 2).
- **Provenance:** the ledger already carried this mechanism as "source-derived and unobserved" in Still owed (`:7853-7856`), which "found 2026-09-23" understates.
- **Fix:** justify P1 as "blocks F-055's P1 repair", and state the production conditions.
- **Changes a disposition (scope):** yes.

**9. MINOR — F-057 is rated P2 against a documented feature.**
- **Evidence:** `USER_MANUAL.md:669-670` and `:764-765` document weight-norm traces during replay.
- **Fix:** rate it P1 under plan §6.3, or owe a correction to the manual. Neither is recorded (item 13 lists only `:1344`).
- **Changes a disposition or an action:** yes.

**10. MINOR — Contradictions inside the section.**
- `:8675-8677` states, in the ledger's own voice, "the CAN-000 clamp reaches it and the tab gate never writes it… cannot arise". This is `884d22fb`'s commit claim, and the same section refutes it at `:8737-8738` and `:8776-8777`.
- `:8602-8603`, "So this phase lands before #676 merges", survives from the draft written before the merge. It is contradicted by `:8488`; `:8630` has the same problem.
- `:8722`, "A demo page is light enough…", is contradicted by `:8746-8747` ("unmeasured").
- **Changes a number, disposition or action:** no.

**11. MINOR — "What the evidence cannot support" (`:8903-8907`) is incomplete.** It omits:
- F-056, which rests on a probe with a constructed envelope and was never driven live;
- the F-025/F-055 narrowing, based on a drive that recorded no latency;
- the live check's single-run SESSION PASS at its floor, whose disable leg is a synthetic clear that no production writer performs;
- "by chance, no watchdog false fire" (`:8793`), which the census cannot observe.

No number, disposition or action changes.

**12. MINOR — Canopy statements that F-058 contradicts are not owed anywhere.**
- `dashboard_manager.py:467-472` ("harmless window"), `:4698-4701` ("Self-healing, bounded to one cycle") and `test_poll_gating.py:313` ("apply clamp alone") are not listed. Item 11 does list the equivalent comment for the FIFO finding.
- Item 13 also omits two of Lane A's instrument gaps that this section itself lists: an empty `paths.strs`, and PROBE never checking the node's id.
- **Changes an action:** yes.

**13. NIT — Overbroad wording and wrong units.**
- **Universal claims:**
  - "every HTTP outcome" (`:8844`) and "Every completion" (`:8505`) are contradicted by `:8782`: a 200 whose body fails to parse skips `completeJob`.
  - "The only stop test" (`:8818`) is false: four other stop tests exist (`test_replay_player_panel.py:211`, `…gate_coverage.py:103`, `test_main_gate_coverage_snapshots.py:378` with a non-empty body, `test_f014…:43`). What is true is that it is the only test of `_merge_session`'s stop branch.
  - "Every event reads `pcalnon`" (`:8636`): the committed rows carry the git author name "Overtoad", not an actor.
- **Merge record and the PR's parent:**
  - "byte-identical" (`:8491`) and "message is `4b4cfb16`'s" (`:8660`): the commit message is not identical — its title gains "(#676)" and GitHub rewrote the co-author trailer.
  - `:8492`, "against the PR's own parent", is the phrasing the section faults at `:8663`.
- **Units:**
  - `:8768`, `:8769` and `:8775` label Lane B's per-request time r as "cycle", although `:8781` says the cycle is completion plus at least 1 s.
  - "n = 3 windows, 29 responses" (`:8900`) mixes the parent's window with the watched count; the table's delivered count is 27.
  - "28 of 29 applied" (`:8793`) is an upper bound.
- **Mechanism:** "after the saturated page has processed the response… matches 5.5–7.3 s" (`:8704-8706`). `completeJob` runs before the apply, including for evicted responses, and ~8 s is outside that band.

**14. NIT — Smaller corrections.**
- F-055's header is still "for the life of the page", though the demo parent applied after 18.5 s.
- F-058 cites dash 4.2.0, but canopy's `requirements.lock` ships 4.4.1. The same code is at `:979-991` there, so add that citation.
- The handoff's item 6 (MEMORY.md, now 25,015 bytes) and the four canopy worktrees due for cleanup now that #676 has merged appear nowhere. They belong in the successor handoff.

## CLAIMS YOU TRIED AND COULD NOT REFUTE

- **F-058 core, on `main`:**
  - `completeJob` (`:925-937`) dispatches `runningOff` without checking whether the request is still current, called at `:966/970/979/983`.
  - Eviction happens at `:3027`, and the discard at `:2697-2704`.
  - The dcc Interval restarts its timer when `disabled` goes from true to false.
  - The gate returns every lane on mount, Apply and tab changes (`dashboard_manager.py:2465-2483`).
  - The watchdog samples every 5 s with a 30 s threshold and resets only on an enabled sample.
  - All of this is identical in dash 4.4.1.
- **F-056:** the route, adapter and client 0.8.0 pass the envelope through unchanged, and only the empty-body stop test (`:251`) reaches the stop branch.
- **F-057:** `weights_at` is called only by tests (definition at cascor `manager.py:1182`), and `_emit_frame` (`:1198-1235`) adds no `weights` key.
- **The merge record:**
  - The timeline events and times match exactly.
  - Readied and armed 4, 7 and 4 s apart for ml#2059, ml#2032 and data#428.
  - The merged diff matches the reviewed one: 445 stripped lines each, `cmp` exit 0.
  - No transcript on this host other than the authoring session holds #676's node ID or URL; the other "676" match is juniper-cascor#676.
- **Counts:** 69 findings (48/1/2/18) and 4 open P1s, reproduced.
- **Test counts:** "17 new tests" checks out: 94 collected on the fix against 77 on the parent.
- **Round-3 leftovers** remain on `main` at the cited lines, and the stale config is still at `app_config.yaml:170,181`.
- **Live check:** the SESSION hollow-pass route is ruled out by arithmetic (the drain had at least 5 ticks before the clear, so a missing node would read at most −5, not 0).

## WHAT YOU COULD NOT CHECK

- Canopy's real mount order, and F-056, F-058 and the slider snap-back in a real canopy browser; I did not run canopy.
- Whether cascor would accept an Apply on the trio.
- The design record's text that cites `d85c9ddd` and `dbc25277`.
- The 2026-08-26 f014 screenshot, which is lost. That run's transcript does show the active-view post-Stop readouts `1×` and `[0, 0]`, but they were read too early to settle F-056.

## SECRETS/PII

No token, environment variable or credential was printed or sent. One local `git show` output displayed a commit author's email; it was not transmitted. Network calls were read-only GitHub API reads and a `pip download` of dash 4.4.1 to scratch. No repository was changed. The synthetic app is stopped and nothing is listening on :9471.

---

## Lane B2 -- adversarial review of the correction pass that recorded #676's merge

*agent `a0b0a3b11b9f21c91` · round 1 · last-assistant-text (not resumed) · 14566 chars*

**VERDICT: SOUND-WITH-FIXES**

Every checkable fact the pass added holds up: the timeline, the diff identity, the squash message and the transcript search. What fails is scope. Two statements of the plan the merge broke are still written as current. The fix-scope text now contradicts itself. Two counts are too low: the false statements on `main`, and the PRs in the sweep. The "Who" bullet leaves out the evidence that excludes every Claude session on this host. The handoff note does not say which of its steps are now dead.

Files. `…E2E-VALIDATION-EVIDENCE.md` is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `e624c281`. `HANDOFF_…f058-filed.md` is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_canopy-e2e-phase9-cuts-reviewed-f055-fix1-refuted-f058-filed.md`. `…phase9_round2.md` and `…phase9_round3.md` are the reports in `reports/e2e-canopy-2026-09-02/consensus/`.

**FINDINGS**

1. **MINOR: two statements of the broken order are still in the present tense.**
   - Quoted: `…E2E-VALIDATION-EVIDENCE.md:8602-8603` "So this phase lands before #676 merges, and the canopy text cites the finding IDs." Also `:8630` "F-CANOPY-056/057 exist only in this unpushed phase (it confirms the ledger-first order)".
   - Evidence: #676 merged at 01:38:02Z. The ledger on juniper-ml `main` (`f9c81d80`, via `gh api …contents…?ref=main`) has 0 matches for `F-CANOPY-05[678]` and no Phase 9. The section's own new bullet (`:8667-8668`) records the dangling citation that this remedy was meant to prevent.
   - Fix: put both in the past tense and state the outcome. For example: "The remedy was to land this phase first. The merge overtook it, so canopy `main` cited the IDs before they existed (see 'The dangling citation')."
   - Changes a disposition: yes, because round 2's MAJOR still reads as remedied. Number: no. Action: no.

2. **MINOR: "prose only" equivalents were left in place, and the pass created a contradiction about round 3's fix scope.**
   - Quoted:
     - `:8600`, round 2: "**MERGE-WITH-FIXES, text only.**"
     - `:8632`: "Its fixes are wording in the squash message and the PR body."
     - `:8887`: "wording only (the squash message and the PR body)"
     - against the new `:8956-8962`: "Round 3's fixes, which the merge left unapplied", which lists survivors in code files and a test-code fragility.
   - Evidence:
     - Round 2's own fix was test code. `git diff 2fa134f8 4b4cfb16 -- …/test_idle_dispatch_cuts.py` adds the dict-id refusal and drops `key=str`. The corrected consensus record (`:8889-8890`) says so itself.
     - B2's report calls its findings "all about text" (`…phase9_round2.md:11`), but its own finding 7 (`:75`) needed a test change.
     - B3 marked the survivors "action: no" (`…phase9_round3.md:45`). It marked the fragility "pre-existing" and "action: no" (`:57-60`).
   - Fix:
     - `:8600`: "text, plus one test-code change (the dict-id refusal)".
     - Make `:8632`, `:8887` and item 13 agree: B3's verdict named the squash message and the PR body. Its NITs 3 and 6 were marked no-action and are carried in item 13.
   - Changes a number, disposition or action: no. The record contradicts itself.

3. **MINOR: the ledger counts three false statements in `e9053227`'s message, and there are four.**
   - Quoted: `:8660-8661` "canopy's history now carries three statements this ledger corrects".
   - Evidence:
     - `git log -1 --format=%B e9053227`, lines 30-31: "Comments that claimed cascor emits weights, that stop clears the session, and that WebSocket events write it are corrected."
     - `git show e9053227:src/frontend/assets/ws_dash_bridge.js`, lines 113-115, still says "…extracted from a replay ``epoch_end`` event (see g-3 emitter)".
     - B3 said this "contradicts the squash body's 'comments that claimed cascor emits weights … are corrected'" (`…phase9_round3.md:43`).
   - Fix: make it four statements and add this one. Consider a canopy-side erratum in item 13's follow-up PR; otherwise the correction exists only in juniper-ml.
   - Changes a number: yes (3 → 4). Action: yes, if the erratum is adopted. Disposition: no.

4. **MINOR: the ledger's sweep is narrower than what GitHub shows.**
   - Quoted: `:8654-8655` "fits the same night's sweep of drafted PRs: ml#2059 …, ml#2032 … and data#428 …, each readied and armed 4–7 s apart."
   - Evidence (issue timelines; every actor is `pcalnon`):
     - Two more drafts were readied and armed in the same pattern, and another session had drafted both at 21:26:17-18Z (e6c1cb6d runs `gh pr ready 431/434 … --undo` at 21:26:16Z):
       - data#431: ready 22:50:54Z, armed 22:50:58Z.
       - data#434: ready 22:51:07Z, armed 22:51:12Z.
     - In the 22:27–22:31Z pass the same account also:
       - armed non-draft ml#2066 at 22:27:08Z;
       - merged canopy#678 directly at 22:29:21Z, with no arm event;
       - merged data-client#212 directly at 22:30:44Z, with no arm event.
     - #676's events interleave with that pass: ml#2032 ready/armed 22:27:20/27 → #676 ready 22:28:04 → update-branch `e581b821` 22:28:09 → arm 22:28:12 → canopy#678 merged 22:29:21 → #676's second update-branch 22:29:31, ten seconds after that merge moved canopy `main` → data#428 ready/armed 22:29:55/59.
     - #676 is the only one of these PRs where the update-branch fell between the ready and the arm. That is where its 8 s comes from.
     - No draft PR is still open (`gh search prs --owner pcalnon --state open`).
     - The three-PR list matches the "Third observation" in memory `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`, which tracked only one session's PRs.
   - Fix: describe one pass by the account over nine PRs, #676 included, with drafts from three sessions. Drop "of drafted PRs". Correct the memory note as well.
   - Changes a number: yes (the sweep's membership). Disposition: no. Action: no.

5. **MINOR (C4): the "Who" bullet treats as open a candidate the transcripts rule out, and records no next step.**
   - Quoted: `:8656` "GitHub cannot tell it from the owner or any session." Also Summary `:8489-8490`.
   - Evidence:
     - Every Claude session on this host returned `rate_limit` "You've hit your weekly limit · resets 10pm (America/Chicago)" between 21:30:36Z and 21:36:13Z. That covers 25de1349, e6c1cb6d, bc31e993, 798c2868 and their subagents.
     - From 21:41:02Z to 00:07:21Z the host's only transcript entry is one task-notification (21:53:09Z).
     - At 00:07:22Z a human-origin prompt in 1f771cb0 hit the same limit. The limit reset at 03:00Z.
     - So the ready, the arm, both update-branches, every sweep event and the merge happened while no Claude session here could act. A person was at the host at 00:07Z.
     - `performed_via_github_app` is null on every #676 event, so no GitHub App did this.
     - No crontab entry, systemd timer or running process matches gh/merge/ready.
     - No schedule or workflow_dispatch Actions run appears in ml, data or canopy during the window.
     - The actor's two update-branches are not discussed, and no transcript holds them either.
   - The ledger does not overclaim. "Fits" is weaker than the interleaving allows.
   - Fix: add the lockout facts. Reword to "the transcripts exclude every Claude session on this host". Add an owner question to Still owed: was the 21:47–22:51Z pass his?
   - Changes an action: yes. Number or disposition: no.

6. **MINOR: the quoted hold comment is cut, and the cut part contradicts "exactly that order".**
   - Quoted: `:8489` "It was held as a draft for exactly that order." Also `:8640` "Held as draft on purpose … Please do not arm auto-merge on it."
   - Evidence:
     - The ellipsis removes this: "…an independent consensus round (Lane A …, Lane B …) is running against this head. It will be marked ready and merged with util/safe_merge.py once that round reports and required checks are green."
     - That condition was round 1 plus green checks. Both were met before the ready. On `4b4cfb16`, every non-Cursor check completed by 20:59:25Z (27 success, 1 skipped). Quality Gate succeeded at 20:59:20Z.
     - The ledger-first order and round 3 appeared only in the PR body.
   - Fix: say the draft was held first for round 1 (per the comment), then for the ledger order (per the body only). The ready met the comment's literal condition; the arm did not.
   - Changes a number or disposition: no. Action: minor (a hold notice must name the current condition).

7. **MINOR: "takes over Phase 8's item 2" drops half of that item.**
   - Quoted: `:8923`.
   - Evidence:
     - Phase 8's item 2 (`:8448-8449`) ends "Then drive F-CANOPY-025's allow arm…".
     - That arm was driven only on the refuted fix and on demo legs, and the drive "does not discriminate" (`:8721`).
     - The matrix keeps F-025 open with F-055 (`:8912-8913`).
     - `grep -E '025|allow arm'` over `:8919-8965` finds nothing, so F-025 is owed nowhere.
   - Fix: add an F-025 re-drive on the second fix to item 0.
   - Changes an action: yes. Number or disposition: no.

8. **MINOR (C5): the handoff note does not say what a reader of that file alone must stop doing.**
   - Quoted: `HANDOFF_…f058-filed.md:7-8` "So items 1 and 2's order was never kept." Also `:6` "(added by the successor session when archiving)".
   - Evidence:
     - Item 2 (`:69-80`) cannot be run. The head branch was deleted at 01:38:03Z, so the ref PATCH fails. `gh pr ready 676` and `safe_merge` would act on a merged PR.
     - These are stale and not flagged:
       - `:137` "#676 is open as a draft";
       - the expectation for the `:125` verification command;
       - the `:117` worktree cleanup, whose merge signal has now fired (`…idle-dispatch-cuts-v2--20260923-1418--3a6dea95` still exists);
       - the goal statement's WIP location (`:19-21`).
     - The WIP is now `5a0e4ea9`..`e624c281` on `f9c81d80`. `worktree-squishy-dancing-moth` is still at `b54e3b3f`, and its ledger has 0 occurrences of "The merge, out of order".
     - "When archiving" is wrong: the file was archived by the authoring session in `f6861234` (originally `b54e3b3f`).
     - The times carry no dates.
   - Fix: list the dead items, and point to the ledger's Still-owed item 13 follow-up.
   - Changes an action: yes. Number or disposition: no.

9. **NIT: "byte-identical" overstates what matches.**
   - Quoted: `:8490-8491` "byte-identical to the reviewed `4b4cfb16`". Also `:8658-8659` "The head round 3 reviewed is what is on `main`."
   - Evidence: the patch is identical; the raw diffs differ only in CHANGELOG.md's `index` line. `main`'s tree also carries #677 and #678, which round 3 never saw in combination. They overlap #676 only in CHANGELOG.md.
   - Fix: "the change that landed is byte-identical".
   - Changes nothing.

10. **NIT: item 13 bookkeeping.**
    - Quoted: `:8665-8666` "Still unfixed on `main`: … and the stale PR description". Also `:8962`.
    - The PR description is not on `main`, and editing #676's body is not part of a follow-up PR.
    - `:8665` lists two things; item 13 lists three.
    - Changes nothing.

11. **NIT: two "Who" facts need tightening.**
    - Quoted: `:8649-8651`.
    - 259b4d16 does contain the literal "gh pr ready 676", in the handoff's Write (20:58:11Z) and Edit (21:00:47Z) payloads. A naive grep would appear to refute the sentence; say "executed".
    - 21:00:59Z is the handoff commit's author date. On this branch that commit is `f6861234`, committed 2026-09-24T03:29:38Z. The original, `b54e3b3f`, was committed at 21:00:59Z.
    - Changes nothing.

**C6 (markdown): no finding.** The pinned markdownlint-cli 0.42.0, run on copies without `--fix`, reports nothing in `…E2E-VALIDATION-EVIDENCE.md` from line 7865 on, or in the handoff. `util/markdown_structure_delta.py --base f6861234 --head e624c281` reports 0 → 0 for both files.

**CORRECTIONS YOU COULD NOT REFUTE**
- **Timeline table.** All seven rows match the timeline API to the second: 19:44:37 draft; 19:44:38 comment; 20:38:41 force-push to `4b4cfb16`; 22:28:04 ready; 22:28:09 `e581b821`; 22:28:12 auto-squash armed; 22:29:31 `5e52debb`; 01:38:02 merged `e9053227`.
  - Every event that has an actor reads `pcalnon`, and `enabledBy.login` is `pcalnon`.
  - The stored `commitBody` is `4b4cfb16`'s message. The only differences are "(#676)" on the headline and trailers normalized.
- **Diff identity.** The raw diffs are 468 lines each. After filtering `index` and `@@` lines they are 445 each, and `cmp` exits 0.
- **Commit message.** `e9053227`'s message is `4b4cfb16`'s plus "(#676)" and a trailer reorder, and all three quoted statements are in it. 3.0 of 6.6 is 45%.
- **Authoring transcript.** 259b4d16 runs `gh pr ready 676 --repo pcalnon/juniper-canopy --undo` at 19:44:36.556Z. Its last timestamped entry is 21:01:29.583Z, 86.6 minutes before the ready.
- **Transcript search.** Across all of `~/.claude/projects/`, nothing readies or arms canopy#676. Patterns searched: `gh pr ready/merge…676`, the node id `PR_kwDORVpyr88AAAABEz-0dg`, `pulls/676/…`, and `safe_merge`/`shepherd`. The only other hit is `gh pr merge 676 --repo pcalnon/juniper-cascor --squash --auto` in 6452333c at 01:34:34Z on 09-23.
- **The three sweep times** are right, with gaps of 4, 7 and 4 seconds.
- **Dangling citation.** `e9053227`'s `CHANGELOG.md:161-165` and its code comments cite F-056 and F-057.
- **Rounds.** Round 1's only code change was `key=str`. Round 2's was the refusal. Everything else was comments or docstrings, and no behaviour changed.
- **Still-owed mapping.** Phase 8's items 1 and 3–12 become Phase 9's 1 and 2–11. Phase 8's 13–14 merge into 12. Items 13–14 are new.
- **Line numbers.** Every line number in item 13 checks out at `4b4cfb16`.

**WHAT YOU COULD NOT CHECK**
- The actor's identity. GitHub shows only `pcalnon`, and a personal account's security log cannot be read through the API.
- Other hosts, claude.ai cloud sessions, IDE or browser actions, and processes that ended before I looked.
- Whether the weekly limit also blocked this account on other machines.
- CI on the merged head `5e52debb`.
- Whether the owner intended the merge.

**SECRETS/PII:** one slip. `gh pr view 676 --json …autoMergeRequest` printed the `authorEmail` field, an owner email address, into my tool output. Nothing was sent anywhere, it is not repeated here, and later queries excluded the field. I read no tokens or credential files. Transcript greps printed only file names and bounded snippets, with token-shaped strings redacted. **Changed:** none. Scratch files are only under the session scratchpad.

---
