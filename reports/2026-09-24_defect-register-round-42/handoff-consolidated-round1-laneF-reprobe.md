<!-- Archived verbatim 2026-09-24 from subagent a597cb4528bceda28 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS. I found no wrong SHA, PR number, count or anchor. There is one MEDIUM error: the document routes the canopy items to a peer session that had already handed off. There are also four LOW and five NIT findings. Seven things in the live state have moved since 01:35Z. The largest: cascor#689 and data#440 have both merged, and the executor has pushed the data fix-forward as `94ce8b1f`.

All "L<n>" references are to the frozen snapshot `consolidated_r1_frozen.md` (sha256 `96c1b58f52fb5377…`, checked). Every other document is named by filename:
- **document 1:** `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`
- **document 2:** `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`. Its frozen copy has sha256 prefix `4ebd0143`, the same as the blob at `2e4917c2`.
- **document 3:** `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`. Its frozen copy equals `origin/main`'s (`5b9cd399`).
- **the register:** `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- **the primer:** `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`

Both were read at juniper-ml `5af9d722`.

I checked between 01:38Z and 02:03Z. I did not run L180, which the brief forbids; I read the juniper-data clone's refs and reflog instead. Every test I ran had the six DSN variables set to "". I read no environment variables and started nothing on ports 8100, 8201 or 8050.

## Findings

### HIGH
None.

### MEDIUM

**M1. The canopy peer had already handed off before this was written, and both canopy records the document cites only in other worktrees now ride an armed PR.**
- **Quoted:**
  - L169: "**Other sessions:** "canopy combined [577a1c]" and "containers [2703c8]"."
  - L243: "It is untracked there, and its bytes are on branch `docs/canopy-e2e-handoff-2026-09-24`, with no PR."
  - L248: "Recorded in `…/bubbly-meandering-pie/…/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md:165-170`."
  - L249: "All of these are in other sessions' worktrees: read only."
- **Evidence:**
  - `gh pr view 2096 --repo pcalnon/juniper-ml` returns: created 2026-09-25T01:19:18Z, "docs(handoff): canopy combined -- three canopy handoffs merged into one draft, round 1 done, fix pass owed". It is OPEN, and auto-merge was armed by `pcalnon` (squash).
  - #2096 carries byte-identical copies of both records:
    - `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` is blob `cc267d2b`. That equals `git hash-object` of graceful-sprouting-panda's file, and the blob on `docs/canopy-e2e-handoff-2026-09-24`.
    - `reports/2026-09-24_canopy-combined-handoff-consensus/r1/DRAFT_r1.md` is blob `ed4de235`, which equals bubbly-meandering-pie's draft. "Nothing was loaded" is at its line 165.
  - #2096's `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md:39-40` says of the fourth item: "It is verified and in the draft's A2(a). I acknowledged it by SendMessage and assigned no id."
  - The `ListAgents` result at 01:37:28.116Z in transcript `2fba4397-…jsonl` lists only `containers [2703c8]` (busy) and four offline Remote Control sessions. Neither `canopy combined [577a1c]` nor `defect reg [042116]` appears. The 00:18:48Z listing, which the document relied on, had both.
  - The document never mentions #2096.
- **Proposed text:**
  - L169: "**Other sessions:** "containers [2703c8]". "canopy combined [577a1c]" handed off at 01:19Z in juniper-ml#2096 (`HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md`; open, auto-merge armed) and was gone from `ListAgents` by 01:37Z. Its successor owns the fourth canopy item's id. The canopy E2E session has exited."
  - L243: "…It is untracked there. Its bytes are on branch `docs/canopy-e2e-handoff-2026-09-24` (no PR) and, byte-identical, in juniper-ml#2096 at `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`."
  - L248: "…`:165-170`, byte-identical to #2096's `reports/2026-09-24_canopy-combined-handoff-consensus/r1/DRAFT_r1.md:165-170`. Cite that path once #2096 merges."
  - L249: "Until #2096 merges, these are in other sessions' worktrees: read only."

### LOW

**L1. `happy-skipping-hollerith` is not clean: it holds #2097's 95 files, untracked.**
- **Quoted (L207):** "fast-forwarded to `5af9d722`, clean. Every new file of Lane F is in #2097."
- **Evidence:**
  - Its HEAD file reads `ref: refs/heads/worktree-happy-skipping-hollerith`, and that ref is at `5af9d722`, as stated.
  - bc31e993's last status, at 01:19:17Z (`git status --porcelain=v1 --untracked-files=all | cut -c1-2 | sort`), printed `95 ??`.
  - A blob comparison found all 95 of #2097's files present there and byte-identical to `2e4917c2`.
  - Document 2, line 229, says only "nothing tracked is modified".
- **Proposed text:** "fast-forwarded to `5af9d722`; nothing tracked is modified. Its 95 untracked files are #2097's, byte-identical to `2e4917c2`. Do not remove it before #2097 merges."

**L2. "Now evidence indexes" contradicts document 2's own rule.**
- **Quoted (L16):** "Documents 1 and 2 are now **evidence indexes**; this file's instructions replace theirs."
- **Evidence:**
  - Document 2, lines 9-11: "Once the consolidated handoff is on `main`, it governs every instruction… Until then, this file governs this lane's work."
  - `gh pr list … --head docs/handoff-round42-consolidated` prints `[]`.
- **Proposed text:** "Documents 1 and 2 become **evidence indexes** when this file reaches `main`. Until the consolidation PR merges, document 2 tells a Lane F session that it still governs; First action 3 is where you reconcile that."

**L3. The executor relaunch recipe carries a Sentry instruction that contradicts the document's own rule.**
- **Quoted (L79):** "Extract both briefs with a script, then launch a new `task-executor` on that worktree with them…"
- **Evidence:**
  - The 23:48:49.313Z brief in `agent-a46e715a6801b98ca.jsonl` says: "Unset every Sentry DSN variable (SENTRY_SDK_DSN, JUNIPER_DATA_SENTRY_DSN, SENTRY_DSN) in every run".
  - L154 says: "Set them empty, never unset: `load_dotenv` re-injects."
  - It is moot for this executor, which has finished (see "Moved since writing" below), but it applies to any relaunch that reuses these briefs.
- **Proposed addition to L79:** "…and replace the second brief's 'Unset every Sentry DSN variable (…)' with 'set all six DSN variables to ""'."

**L4. Appendix G's Lane F list leaves out Lane F's memory edits.**
- **Quoted (L489):** "**Lane F** (session `bc31e993`): #2097's 95 files, and its merged PRs (…)."
- **Evidence (bc31e993 transcript):**
  - `cat >> …/memory/feedback_validate_handoff_prompts_independently.md` ran at 2026-09-25T01:21:20.493Z. The file's mtime is 01:21:20Z.
  - Earlier in round 42 (2026-09-24, 03:31Z to 07:33Z), the session Edited `MEMORY.md` and `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`.
  - Lane R's five memory files match its transcript exactly.
- **Proposed text:** "…and its memory edits: `feedback_validate_handoff_prompts_independently.md` (appended 2026-09-25 01:21Z), and, earlier in round 42, `MEMORY.md` and `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md`."

### NIT

**N1.** L75: "Its **brief** is TWO `user` records."
- The transcript holds a third non-tool user record at 00:29:28.847Z (22,994 characters): "This session is being continued from a previous conversation that ran out of context…". The executor has worked from a compaction summary since then.
- **Proposed addition:** "(a third, at 00:29:28.847Z, is its compaction summary, not a brief)".

**N2.** L235: "parse as juniper-data's `str_as_bool` does".
- `git -C juniper-data grep str_as_bool origin/main` finds nothing.
- cascor#690's `manager.py:232` reads: "pydantic-core's ``str_as_bool`` (``src/input/shared.rs``)".
- **Proposed text:** "parse a string exactly as juniper-data's pydantic model does (pydantic-core's `str_as_bool`)".

**N3.** L399: "Its final version was tested at 01:17Z".
- In bc31e993's transcript, the case-insensitive unset was added by an Edit at 01:18:23.942Z.
- The test command (`env juniper_data_require_auth=true Juniper_Data_Csv_Import_Max_Bytes=1 bash …serve_scratch_juniper_data.bash …`) ran at 01:18:36.802Z. It printed "health 200 / POST /v1/datasets 422 … / anon generators 200" at 01:18:39.992Z.
- Document 2, line 72, carries the same 01:17Z.
- **Proposed text:** "01:18Z".

**N4.** L188: "11 OK, 3 skipped".
- The actual output is "Ran 11 tests … OK (skipped=3)": 8 passed and 3 skipped, not 14 tests.
- With `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` it is "Ran 11 tests … OK", as stated.
- **Proposed text:** "Ran 11, OK (skipped=3)".

**N5.** L471-L474: "Older; awaits the cleanup signal."
- All four have uncommitted changes. `git status --porcelain | wc -l` gives:
  - cascor nonshortcircuit: 1
  - data tri-state-allow-truncation: 16
  - data cheatsheet: 1
  - cascor tri-state-truncation-prose: 5
- **Proposed text:** add "(dirty: N entries)" to each row.

## Moved since writing (not errors)
- **MV1. The data fix-forward is pushed and the executor is done.**
  - The remote `fix/conditional-requests-round4-followups` is at `94ce8b1fa8e229c92e8674a1074d518e59142488`: verified=true (reason valid), one parent `d1c66a11`, 12 files, committed 01:46:46Z.
  - The executor's last message, at 01:49:10Z: "I pushed one more GitHub-signed commit … No PR opened."
  - The reflog shows the scratch commit made at 01:02:35Z and amended at 01:04:13Z and 01:25:31Z. Its final tree equals `94ce8b1f`, and the clone's local and remote-tracking refs are both at `94ce8b1f`. The branch still has no PR.
  - This affects L67, L69-80, L85 (round 2 now runs on `d1c66a11..94ce8b1f`), L178, L316 and Appendix F row 1.
- **MV2. cascor#689 and data#440 have merged.**
  - cascor#689 merged at 01:56:52Z as `b9484fef`. Its squash message contains "4001 close", so F9's residue has happened.
  - data#440 merged at 01:57:38Z as `26491531`.
  - Consequences:
    - L93-94's "fixups" must now be NEW PRs from fresh `main` (L123's rule).
    - ECO-013's first two close conditions (L220) are met.
    - Appendix E's merge precondition is met.
    - L88's CHANGELOG check is now against data `main` `26491531`.
- **MV3. cascor#690 has a new head and can merge before it is validated.** Its head is now `81154187` ("Merge branch 'main' into fix/shortfall-688-validation", 01:57:10Z, signed, pcalnon). Auto-merge is armed, and the PR is BLOCKED only on checks. Appendix F row 2's "HEAD is #690's head" is stale: that worktree is still at `78e99414`.
- **MV4. The durable PR draft has been re-copied.** `data438-fixforward-pr-draft.md` was re-copied at 01:49:50Z. It equals "# " + title + "\n\n" + body of the current tmpfs drafts (title updated 01:05:38Z, body 01:48:13Z). This affects L326.
- **MV5. juniper-ml `main` moved.** #2098 merged at 01:47:48Z (`09f2e677`) and #2090 at 02:02:04Z (`3055a892`). fizzy-hugging-dream is now 3 ahead and 7 behind remote `main`; L204 says 5 behind.
- **MV6. A new untracked file is missing from the ship list.** `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py` (mtime 01:36:53Z) is not in L196-L202.
- **MV7. Peer sessions at 01:37:28Z.** `ListAgents` lists only `containers [2703c8]` as a live peer (see M1).

## Claims table

| Claim (line) | What I ran or read | Result |
|---|---|---|
| L3, L7: 2fba4397 = "defect reg [24f8d8]", worktree fizzy-hugging-dream | ListAgents 00:18:48Z and 01:37:28Z; `git branch --show-current` | CONFIRMED |
| L5: owner's order about 23:25Z | user records 23:25:30.566Z and 23:25:49.935Z | CONFIRMED |
| L6, L182: document 1's path and head | `cat … \| head -3` | CONFIRMED |
| L9-L11: #2097 head `2e4917c2`; bc31e993 = [042116]; five rounds | `gh pr view 2097`; blob sha; report rounds 1-5 in #2097 | CONFIRMED |
| L12: document 2's predecessor | on main via #2072 | CONFIRMED |
| L13: split relayed by [977fa8]; "Resume both here" | 8f86dec2's call answered 07:59:05Z, its SendMessage 07:59:16Z; bc31e993's answer 08:01:26Z | CONFIRMED |
| L14: document 3 on main via #2084 | #2084 file list; sha equal to main's | CONFIRMED |
| L16: documents 1 and 2 "now" evidence indexes | document 2, lines 9-11 | REFUTED (L2) |
| L27, L232: ruling text, 10:22:00.792Z / 18:30:09.820Z, "Releases stay yours." | `owner-ruling-key-leaks-verbatim.md:7,19-20,38`; extractor `--topic key-leaks` rerun is identical except for one trailing newline | CONFIRMED |
| L37: `095a2108` on #2077; two commits on canopy#685 | `pulls/2077/commits`; `pulls/685/commits` (`78c08ec3`, `e70b54dc`) | CONFIRMED |
| L58-L60: nine merged PRs, their merge SHAs and times | `gh pr view` each | CONFIRMED |
| L58: post-merge `main` CI green on all | actions runs by `head_sha` for all nine merge commits: every push run succeeded | CONFIRMED |
| L61: 0.16.0 on PyPI at 18:35Z | run 35977786108, "Publish to PyPI" 18:35:46Z | CONFIRMED |
| L64-L66: open-PR heads | GraphQL at 01:38Z matched; at 02:02Z #689 and #440 had merged and #690's head had changed | MOVED (MV2, MV3) |
| L67, L178, L316: branch at `d1c66a11`, no PR, parent is #438's merge | `git/ref` at 01:38Z; parent `0f0f7e0e` | MOVED (MV1) |
| L70, L322, L333: 6.6 s / 10.5 s / 0.01 s; `call_soon`; 5 s x 3 readiness probe | `data438-fixforward-round1-laneB-refute.md` M-1; juniper-deploy `values.yaml:90-91` | CONFIRMED |
| L71: one signed commit on `--expected-head d1c66a11`, no PR | 23:48:49Z brief; `94ce8b1f`'s parent | CONFIRMED |
| L72: scratch commit by about 01:15Z, `[ahead 1]` | reflog: commit 01:02:35Z, amends 01:04:13Z and 01:25:31Z | CONFIRMED |
| L73-L74: transcript path; `last_report()`; `split("\n")` | `find`; archiver `:164-171` | CONFIRMED |
| L75: two briefs, their times and contents (four spec files, and so on) | user records 19:37:50.383Z and 23:48:49.313Z | CONFIRMED (N1) |
| L76: 600 s without a write while alive | gap 20:21:04Z to 20:31:04Z | CONFIRMED |
| L86: `gh pr create` form; `open_signed_pr.py` refuses an existing branch | `open_signed_pr.py:46-47`, `:275-276` | CONFIRMED |
| L88, L367, L369: file ownership; both edit `CHANGELOG.md` | diff stats: `0f0f7e0e..d1c66a11` (13 files), `..0bee089e` (3 files) | CONFIRMED |
| L89, L390-L391: #690's branch and commits; 2 MEDIUM / 3 LOW / 2 NIT | `pulls/690/commits`; `cascor688-validation.md` headings | CONFIRMED |
| L97-L99: range; primer lines; register items | `2439d049^` is `990ef3f9`. `-U0` hunks: primer lines exactly as listed (6085 is inside the arms' block and unchanged); register L512, 766, 1297, 1430, 1635, 1699 are the five named items | CONFIRMED |
| L106, L264: primer 4742-4743 stale since data#281 | primer text; data#281 "own the 422 contract" | CONFIRMED |
| L108: #2080 body L65 and L69; N6 | body; `ml2080-round1-laneA-reprobe.md:156` | CONFIRMED |
| L109: "Extended beyond the lanes"; N11 at `:120`; "which no lane named" | #2088 body L47; report L120; `2439d049` body line 14 | CONFIRMED |
| L118-L122: `push_signed_commit.py` behaviour | script `:31-33`, `:56`, `:65`, `:212-217`, `:269-270` | CONFIRMED |
| L127-L130: gh flags; update-branch; #435's duplicate heading | `gh pr merge --help` (gh 2.46.0); data#435 body line 3 | CONFIRMED |
| L133: §2 status line about L176 | register L176-177; crosscheck docstring | CONFIRMED |
| L135-L138: editor refusals; census 69/82; harness 62; mutation-check arguments; venv pins | `…_round2.py:9,40,275,286`; census run; "62 passed"; `pyvenv.cfg` and dist-info | CONFIRMED |
| L146-L150: archiver `SESSION_IDS`, `MISSING`, `HEADER` and header format; four "turn-ending" reports | archiver `:41-42`, `:55-59`; first lines of the four reports | CONFIRMED |
| L154-L156: DSN names; 1,048,576 inodes at 83%; hit 100% on 2026-09-24; `pkill -A` | `df -i`; status text at 19:02:43Z and 19:05:13Z; `pkill --help` | CONFIRMED |
| L168: `worktree_cleanup.bash` pushes and runs `gh pr create` | `:253`, `:259`, `:327-332` | CONFIRMED |
| L169: other sessions | ListAgents 01:37:28Z; #2096 | REFUTED (M1) |
| L174-L190: verification commands | ran each except L180; every output matched its annotation at 01:38Z | CONFIRMED (N4) |
| L180: data worktree `[ahead N]` | not run (forbidden); refs read from the clone instead | UNVERIFIABLE |
| L195: three unsigned scratch commits carrying #2088's content | `%G?` = N; `git diff ee0b9382 5af9d722` over #2088's 14 files is empty | CONFIRMED |
| L196-L203: ship list; #2089's files byte-identical | `git status`; 132 of 132 identical to `a2fa3ad8`, no extras | CONFIRMED (MV6) |
| L204: 5 commits behind | 3/5 at 01:39Z; now 7 behind remote `main` | MOVED (MV5) |
| L204: `SESSIONS` renamed to `SESSION_IDS`; the screen covers `util/**/*.py` | extractor diff; `ci.yml:1364` | CONFIRMED |
| L206: data worktree holds the round-4 branch | its gitdir `HEAD` file | CONFIRMED |
| L207: happy-skipping-hollerith at `5af9d722`, "clean" | HEAD file; "95 ??"; 95 of 95 identical | REFUTED (L1) |
| L213-L217: gates; ids open; three ids unfiled | `register_open_set.py`; register has 0 hits for ECO-013, ECO-014 and CASCOR-014 | CONFIRMED |
| L219-L222: ECO-013's close condition; "both agree" | document 1, line 199; document 2, line 135 | CONFIRMED |
| L223-L227: ECO-014 text; CASCOR-014 (9 files, 25 envelopes); `:25` to `:231` | ruling question; validation F4; `test_cfg_03…:25`; `main.py:231` | CONFIRMED |
| L230: DATA-055's lock half | `base.py:415`, `:484`, `:657` at `0f0f7e0e` | CONFIRMED |
| L235: #690's remedy key; old reader took "f" and "n" as true | `manager.py:245` at `78e99414`; old `_as_bool_stance` at `7f4a7213:4415` | CONFIRMED (N2) |
| L236-L241: residue anchors | fixup report `:16`; snapshot `:40` ("bind auto-start wholesale"); `canopy683-implementation-report.md:32`; canopy script `:22` with register L1290; register L1616; cascor `COMMIT_MESSAGES`; #689's commit message | CONFIRMED |
| L243-L248: reservation at 19:40:28Z; `:53-66`; `dd4413e5` with no PR; `:8410`, `:42`, `:8381`; 20:45:53Z; `4766`/`4841`; `:165-170` | queue-operation 19:40:28.837Z; blob `cc267d2b`; canopy and cascor sources | CONFIRMED (incomplete: M1) |
| L253-L254: rate limiting off by default; stale comment at `:49-50` | `settings.py:319`; the test file; canopy `ci.yml:170` | CONFIRMED |
| L255: A1 F2, F3, F4; F3 = DATA-056 | report `:23`, `:26`, `:29`; register L1303 | CONFIRMED |
| L259-L262: handler anchors | data `app.py:187`, `:214`; cascor `:856`, `:916` | CONFIRMED (outcomes not rerun) |
| L269-L279: canopy#685's report claims; `outbound_errors.py:57-61` | report `:64-67`; source file | CONFIRMED |
| L280-L282: `pr-63` and `pr-683` | both at unsigned `4caf9389`; activity API 22:55:30Z and 22:55:39Z; no PRs; upstream `origin/pr-683` | CONFIRMED |
| L284-L286: Sentry pending events; #437 marked not breaking; ML-008 remedy | implementation report `:52`; `data438-round1-laneA-reprobe.md:94-95`; register L1305 | CONFIRMED |
| L288-L292: 33 alerts / 4 high and their path; #2081's two commits; two "mitigated" dismissals (#841, #842); 59 alerts open; README rows | check-run; alerts API; README `:39-42` | CONFIRMED |
| L294: MEMORY.md is 24,929 characters | `wc -m` | CONFIRMED |
| L296: notify-consumers failed with 403 | job 107777269559 log: "Resource not accessible by personal access token" | CONFIRMED |
| L296: "The containers session owns it" | no source checked | UNVERIFIABLE |
| L297-L312: later arc items | open set; register L1284 and L1421; round-39 handoff §0.4; round-41 handoff `:37`; recurrence `data_quality` 0 hits | CONFIRMED |
| L316-L321: dispositions; 1901, 97.76%, 118, 70 mutations, 3,495,583 / 0; 2 LOW + 9 NIT; 1 MEDIUM + 5 LOW + 6 NIT | lane A report rows 32-38 and 76-99; lane B report `:17`, `:70`, `:98`, sections | CONFIRMED |
| L325-L327: draft copy "taken at 00:27Z" | mtimes; equality check | MOVED (MV4) |
| L332-L355: brief summary; anchors at `d1c66a11`; `[0.16.0]` is 261 lines | 23:48:49Z brief; `git show`; section hash `f376fdc1` identical at the tag, `d1c66a11` and `0bee089e` | CONFIRMED |
| L336: the stall probe is the executor's; staged save | Write at 00:33:25Z in its transcript; docstring | CONFIRMED |
| L375-L388: #2097's evidence | 95 files; 63 probes (21 + 10 + 19 + 13); 5 harnesses; 4 scripts; `make_nv1_tree.py:7-8`; `fix_probe_pairs.py:2-3,29` | CONFIRMED |
| L394-L400: harness mapping; import by path; serve-script behaviour | `…as_bool_stance_mutation_check.py:39,80`; the script itself | CONFIRMED (N3) |
| L406, L409: canopy compare lines; the #685 worktree lacks the two probe commits | `7ab994e5` against `dc5ea02e`; `4a8af2a0..e70b54dc` touches one probe script | CONFIRMED |
| L411-L414: #689 and #440 open and validated | validation report `:96`, `:102`, `:104`; both have since merged | MOVED (MV2) |
| L416-L427: F-table anchors | service-core `:101`; data#440 `:34`, `:37`, `:205-206`; data `ci.yml:287`; cascor `conftest.py:37`; #689 `:31` and `:33-35`; canopy `:172`; service-core `CHANGELOG.md:57-58`; observability `CHANGELOG.md:64`; `test_sentry.py:122`; no `before_send_transaction`; no "4001" in #440 | CONFIRMED |
| L429-L441: release facts | locks, caps and `Dockerfile:41-42`; recurrence has 0 Sentry hits; `app.py:335` goes through `observability.py:37`/`:122` | CONFIRMED |
| L445: agreement at 00:21Z | SendMessage at 00:21:47.415Z | CONFIRMED |
| L446-L456: marker anchors and guard counts | `security.py` in all four copies; drift test `:205-209`, `:289`; `ci.yml:500`; weekly cron; FORCE_LOCAL gives 11 OK; REFERENCE `:2977`; register L240, 252, 1106, 1751 | CONFIRMED |
| L462-L474: worktrees, HEADs, trees, signatures | `git -C` log and rev-parse on each (tree equalities hold) | CONFIRMED (N5; row 2 MOVED, MV3) |
| L470: juniper-ml sentry-locals worktree is "clean" | HEAD file only; `git status` not allowed there | UNVERIFIABLE |
| L478: stale branches | `git/ref` `e452a660`; `refs/pull/686/head`; local branches in the cascor clone | CONFIRMED |
| L483-L488: Lane R's documents | #2088 has 14 files; #2089 has 132; its memory edits are exactly the five named | CONFIRMED |
| L489: Lane F's documents | 95 files confirmed; memory edits missing | REFUTED (L4) |
| L493-L503: Appendix H | harness 62; mutation 12/12; probe 27/27; `c061a99f` gives 25 of 27 (3.13.13) and 24 of 27 (3.14.2); `34e06747` = `8917fdac` + `f2147403`, overlapping only in `CHANGELOG.md` (60 non-blank lines); #688's body; #2072's files | CONFIRMED |
| L507-L565: Appendix I mappings | section structure of all three documents | CONFIRMED |

Counts: 80 claims checked, 68 CONFIRMED, 4 REFUTED, 5 MOVED, 3 UNVERIFIABLE. Findings: 0 HIGH, 1 MEDIUM, 4 LOW, 5 NIT, plus 7 live-state moves.
