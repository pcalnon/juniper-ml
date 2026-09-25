<!-- Archived verbatim 2026-09-24 from subagent ae1e0162ef5d928bd of session 2fba4397 (final message). -->

# Round 4, lane F: delta re-probe of the consolidated handoff

**Verdict:** PASS WITH CORRECTIONS. No HIGH or MEDIUM findings; 3 LOW and 5 NIT. Every r3 correction is applied or has a stated reason, and none was applied wrongly. The facts moved into Appendices C, F and H all re-probe correct. The opener's dry run is clean and ships 36 files.

**Documents cited**
- The document under test: `hc4/consolidated_r4_frozen.md` ("L<n>"). It is a frozen copy of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`.
- The previous version, called r3: `reports/2026-09-24_defect-register-round-42/handoff-frozen/handoff-consolidated-r3.md`.
- Round 3's reports: `handoff-consolidated-round3-laneF-reprobe.md` (called F3) and `handoff-consolidated-round3-laneP-fresh-session.md` (called P3).
- The frozen-copies index: `handoff-frozen/README.md`.
- Another validation report: `handoff-2fba4397-round2-laneO-amputation.md`.
- Document 2: `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, at `2e4917c2`.
- Document 3: `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.
- The 09-23 round-42 handoff: `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`.
- The register, `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, on `main` `b82d12d7` (fizzy's copy is identical).
- The word-count rule: `~/.claude/CLAUDE.md` and `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.

## Findings

### HIGH
None.

### MEDIUM
None.

### LOW

**LOW-1. L285 gets the commit numbers wrong, and its CodeQL status was stale when written.**
- Quote: "At 02:39Z its second commit, `a64d72fe` … At 03:03Z a third commit, `669b2c75` (signed) … for 216 files; its CodeQL runs again."
- Evidence from `gh api …/pulls/2089/commits`:
  - #2089 has four signed commits: `d8a495f7` (00:21:36Z), `a2fa3ad8` (00:24:59Z), `a64d72fe` (02:39:33Z) and `669b2c75` (03:03:49Z). So `a64d72fe` is the third commit and `669b2c75` the fourth.
  - CodeQL check-run 107927197304 on `669b2c75` finished at **03:07:04Z: failure, "82 new alerts including 4 high"**. The four highs are the same `stripe_probe.py` lines (:139, :148, :177, :205), and all 14 new alerts are in `handoff-consolidated-round3-laneF`.
  - The file was last written at 03:12:26Z, after that run finished.
- Replace with: "At 02:39Z its third commit, `a64d72fe` (signed), added 73 probes … On `a64d72fe` CodeQL failed again at 02:43:16Z: 68 new alerts, the same 4 high. At 03:03Z a fourth commit, `669b2c75` (signed), added the round-3 lanes' 10 probes (`handoff-consolidated-round3-lane{F,P}`), for 216 files. On it CodeQL failed at 03:07:04Z: 82 new alerts, the same 4 high."

**LOW-2. L283 lists five parked rows, but the register parks nine.**
- Quote: "**[R] The register's five parked rows.** Its §4 notes (about L1626-L1630) park `APD-DATA-054`, `-055` and `-056`, and `APD-ML-007` and `-008` …"
- Evidence:
  - In the register, "awaiting an owner ruling" also parks `APD-ECO-009`, `-010` and `-011` (L1619) and `APD-ECO-012` (L1632). Their rows are at L1298-L1300 and L1306.
  - r4 never names ECO-009 to ECO-012 (grep finds nothing).
  - No open handoff PR mentions them: #2096, #2097 and #2100 all have 0 hits.
  - The 09-23 handoff only filed ECO-009 to ECO-011 as awaiting a ruling.
  - Neither owner-ruling record mentions them (0 hits).
- Replace with: "**[R] The register's nine parked rows.** Its §4.9 notes (about L1619-L1634) park `APD-ECO-009`, `-010` and `-011` (L1619), `APD-DATA-054`, `-055` and `-056` (L1626), `APD-ML-007` and `-008` (L1629), and `APD-ECO-012` (L1632) as awaiting an owner ruling, do not action. No round-42 handoff records asking any of them. This file carries `-055`'s `If-Match` half and `-008`'s remedy (above). Ask all nine together, each with its row's own question (the rows are at about L1298-L1306)."

**LOW-3. `handoff-frozen/` does not hold every copy the reports cite by line (L19, L508, README).**
- Quotes:
  - L19: "the frozen copies its reports cite by line are in `handoff-frozen/`"
  - L508: "the eight frozen handoff copies the validation reports cite by line"
- Evidence, from `frozen_check.py` and `uncatalogued_copies.py`. Three cited documents are missing from the directory:
  - **Document 2** (`hc2/doc2_peer_final_2e4917c2.md`, sha256 `4ebd0143…`), cited by 7 reports. For example, F3 cites "document 2 L23, L84, L108, L125, L129, L134, L136, L139". It is byte-identical to the blob at juniper-ml `2e4917c2`, so git keeps it.
  - **Document 3** (`hc2/doc3_predecessor_main.md`, `5b9cd399…`), cited by 3 reports. It is byte-identical to `origin/main`'s copy.
  - **PEER**, sha256 `62f9b2bf…`: document 2's draft from 00:21Z, which `handoff-2fba4397-round2-laneO-amputation.md` cites as PEER L17, L116, L141 and L205. None of 3,079 files hashed in the scratchpad, happy-skipping-hollerith's `prompts/` and `reports/`, or fizzy's `reports/` has that hash.
- PEER survives only in session `bc31e993`'s transcript. Replaying that session's 25 Write and Edit calls on document 2, in memory, gives `62f9b2bfca40f2e4` (23,480 bytes) after the Write at 2026-09-25T00:21:05.980Z. The same replay ends at `4ebd0143`, which is `2e4917c2`, so the replay is faithful.
- Replace L508's sentence with: "…`handoff-frozen/`: the frozen copies the validation reports cite by line, which were on tmpfs, and a `README.md` mapping each report's scratch path and sha256 to its file. Git holds two cited documents byte for byte, so they are not copied: document 2 at juniper-ml `2e4917c2` (`4ebd0143…`) and document 3 on `main` (`5b9cd399…`). Document 2's 00:21Z draft (`62f9b2bf…`, PEER in `handoff-2fba4397-round2-laneO-amputation.md`) exists only in session `bc31e993`'s transcript (its Write at 00:21:05.980Z)."
- Make the matching change at L19. Add README rows for all three, and either rebuild PEER from the transcript before it ages out (about 30 days) or record that it is lost.

### NIT
- **NIT-1 (L3):** "between 02:10Z and 03:20Z" ends after the file's last write (03:12:26Z) and after the freeze (03:13:22Z). Use "between 02:10Z and 03:12Z".
- **NIT-2 (L21):** "which `~/.claude/CLAUDE.md` calls a median, not a cap" misquotes the rule. It actually reads "**Keep it under ~1,200 words** … a **target near the median**, not a description of practice" (CLAUDE.md:65-68). The canonical procedure (`…THREAD-HANDOFF-PROCEDURE.md:82-96`) says to "treat the **IQR as the real guidance**" (778–2,718 words).
  - Measured: the Goal is 1,442 words (L23-L85, heading included), down from r3's 1,480. The whole file is 12,476 words.
  - Replace with: "the ~1,200-word target ("Keep it under ~1,200 words", which `~/.claude/CLAUDE.md` calls a target near the median; juniper-ml's `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` treats the IQR, 778–2,718, as the real guidance)."
- **NIT-3 (README "Cited by" column):** two reports cite a copy by scratch path, without its sha:
  - `handoff-2fba4397-round2-laneO` cites r1 as "R1 L21, L22, L35, L45-51, L73, L118-119".
  - `handoff-consolidated-round3-laneF` cites doc1 r2 as "document 1 L41, L168, L176, L278, L368". I checked L41 against the copy.
  - Add each report to its row. Change "match a report to its copy by the sha256 prefix it quotes" to "…by the sha256 prefix it quotes, or the scratch path it names".
- **NIT-4 (L291):** the rest of P3's N14 is still open: the "[R] The next juniper-data release" row asks no question. Add: "Ask: cut it once the data fix-forward merges and validates? (yes or no; the owner cuts it)."
- **NIT-5 (L72 against L314):** "finished at 01:49Z: one signed commit, `94ce8b1f`" reads as the executor's whole output, while L314 says it pushed both commits. Use: "finished at 01:49Z: its round-1 fixes are one signed commit, `94ce8b1f` (it pushed the branch's first commit, `d1c66a11`, at 20:45Z), and it opened no PR."

## Corrections table (round 3 to r4)

| Finding | r3 L | r4 L | Verdict | Quote (r4) |
|---|---|---|---|---|
| F3 L-1 | 366 | 370 | APPLIED | "copy the preserved `serve.py` to `S/scripts/serve.py` … and the six DSN variables to `""`" |
| F3 L-2 | 192, 281 | 195, 285 | APPLIED | "**Their probes, too.** … Rounds 1-3's are on #2089" (`LANES` and `DIRS` are the right names) |
| F3 N-1 | 150 | 149 | APPLIED | "At 02:31Z no live … session was listed ("containers [5b005d]" and "canopy e2e phase 1 seg 9 [33ec49]" were listed offline)" |
| F3 N-2 | 593 | 604 | APPLIED | "a third plain-text record, at 00:29:28.847Z, is its compaction summary, not a brief" |
| F3 N-3 | 471 | 475-478 | APPLIED | "1 tracked script, 14 untracked scripts and 1 untracked directory …" (every count reproduces) |
| F3 N-4 | Goal | 21 | REASON GIVEN | "the Goal is about 1,450 words …": adequate (1,442, within the IQR guidance) but misquoted (NIT-2) |
| F3 N-5 | 249, 254 | 252 | APPLIED | "whose probes are on #2089 as `…/handoff-2fba4397-round3-laneF/probe_{data,cascor,primer}.py`" |
| F3 MV1 | 281 | 285 | APPLIED | "On `a64d72fe` CodeQL failed again at 02:43:16Z: 68 new alerts, the same 4 high." The new sentence after it has moved (LOW-1) |
| P3 M1 | 70, 192, 281 | 195 | APPLIED | as F3 L-2 |
| P3 M2 | 192 | 191-194 | APPLIED | "Archive one only if its transcript ENDS with its report …" |
| P3 L1 | 190 | 189 | APPLIED | "The body files must be ABSOLUTE paths …" |
| P3 L2 | 281 | 285 | APPLIED | as F3 MV1 |
| P3 L3 | 34 | 36 | APPLIED | "agent ids and its session's full UUID (for `SESSION_IDS` …)" |
| P3 L4 | 99 | 98 | APPLIED | "Validate every FIX … Evidence-only commits … need only the archiver's `--check` and CI." |
| P3 L5 | 593 | 604 | APPLIED | "**If round 2 refutes, or returns corrections you apply before the PR** …" |
| P3 L6 | 45 | 47 | APPLIED | "send the message with `notify_when_idle: true` …" |
| P3 L7 | 128 | 127 | APPLIED, in another form | "Fizzy's copy names an email match "owner-email" …". The archiver itself was fixed (fizzy's copy, :220-221). Adequate: both verification lines only count lines with `grep -c` |
| P3 N1 | 169 | 168 | APPLIED | "53 in fizzy at 03:05Z; 34 in a worktree at origin/main …" |
| P3 N2 | 46 | 48 | APPLIED | "`find … -name '*.jsonl' -mmin -15` must print nothing" |
| P3 N3 | 140 | 139 | APPLIED | "a heredoc inside a compound command (write the file with the Write tool instead)" |
| P3 N4 | 593 | 604 | APPLIED | as F3 N-2 |
| P3 N5 | 106 | 105 | APPLIED | "`expected_head_sha=<the PR's full headRefOid, from gh>` (not `main`'s sha)" |
| P3 N6 | 104 | 103 | APPLIED | "`--match-head-commit <validated sha>`" (gh 2.46.0 has the flag) |
| P3 N7 | 193 | 196 | APPLIED | "(every archiving run edits it)" |
| P3 N8 | 51-53 | 53-55 | APPLIED | "[F] #2097 … [R] the consolidation PR … [R] juniper-ml#2089" |
| P3 N9 | 597 | 608 | APPLIED | "reachable through `refs/pull/2088/head` (`1f116c38` …)" |
| P3 N10 | 128 | 127 | APPLIED | "(fizzy's copy only, until the consolidation PR merges)" |
| P3 N11 | Goal | 21 | REASON GIVEN | as F3 N-4 |
| P3 N12 | 190 | 189 | NOT APPLIED; none needed | "Put `Allow-Symbol-Loss: const:SESSIONS` in the commit body's last paragraph" (the dry run shows it there) |
| P3 N13 | 501 | 19, 183, 508 | APPLIED, incomplete | "`handoff-frozen/` (the frozen copies they cite, plus its `README.md`)" (LOW-3) |
| P3 N14 | 278-279, 287 | 283 (new), 291 | APPLIED, incomplete | "[R] The register's five parked rows …" (LOW-2, NIT-4) |

Totals: 31 findings. 26 APPLIED (2 of them incomplete), 1 in another form, 2 with a reason given, 1 not applied as none was needed, 0 applied wrongly.

## Changed facts re-probed (all CONFIRMED except where marked)
- **Appendix H (L526-529), carried by L64:**
  - Merges: #689 `b9484fef` at 01:56:52Z, #440 `26491531` at 01:57:38Z, and #690 `0fbb447a` at 02:06:36Z.
  - `81154187` is `pcalnon`'s merge of `main` (`b9484fef`) into `78e99414`, at 01:57:10Z. Auto-merge was enabled by `pcalnon` at 01:57:06Z (SQUASH).
  - Data `26491531`: 3 of 3 runs green.
  - Cascor `0fbb447a`: CI/CD green at 02:16:38Z; its parent is `b9484fef`. `b9484fef`'s own CI/CD was cancelled at 02:06:57Z.
- **Appendix C (L314-320), carried by L72:**
  - Executor `a46e715a6801b98ca` pushed `d1c66a11` (command at 20:44:56Z; commit 20:44:58Z, parent `0f0f7e0e`, verified).
  - It pushed `94ce8b1f` (command at 01:46:42Z; commit 01:46:46Z, parent `d1c66a11`, verified).
  - Its last record is at 01:49:10.537Z, text only, and it ran no PR command.
  - The ref is at `94ce8b1f`, with no PR. The data worktree is clean and in sync.
  - Its three `user` records are at 19:37:50.383Z, 23:48:49.313Z and 00:29:28.847Z; the third is the compaction summary.
- **Appendix F's hazy-beaming-map counts (L475-478).** I read the worktree with `open()` and parsed its binary index:
  - 16 entries: 1 tracked script, 14 untracked scripts and 1 untracked directory.
  - 12 of the untracked scripts are identical to `main`. The other two match `22a6b7b5` and `f4d050c6`, both on `main`.
  - 203 probe files: 201 identical, and 2 equal to the pre-`73dc109c` blobs.
  - The register, primer and `docs/REFERENCE.md` equal `5af9d722^1` (`7e8c7ff9`); the LFS images are excluded.
  - All 242 untracked files are on `main` apart from those 4, so no work would be lost.
- **#2089 (L68, L188, L252, L507):** at `669b2c75`, 216 files in 14 lane directories (8 of them handoff-validation directories), all 216 byte-identical in fizzy. The round-3 `probe_{data,cascor,primer}.py` are present.
- **L285:** partly wrong (LOW-1).
- **L36, L127:** fizzy's archiver has `SESSION_IDS` and exits "not in SESSION_IDS". It has the narrowed patterns and labels an email hit "owner-email". `main`'s copy prints `p.pattern`.
- **L168, L170:** fizzy gives 53 OK, 0 DIFFER and 0 REFUSE; `main`'s copy, in a scratch root, gives 34 OK. The report count is 21.
- **L47, L48:**
  - `notify_when_idle` is in SendMessage's schema. I loaded the schema only and sent nothing.
  - The `find` check prints this round's two running lanes. Local time is CDT.
- **L98, L103:** document 2's L108 has the OPEN 4 rule, and gh 2.46.0 lists `--match-head-commit`.
- **L139:** round 3's lane P was refused on a heredoc inside a compound command at 02:53:09Z.
- **L149:** the 02:31:30Z `ListAgents` result matches.
- **L191-195:**
  - The grep matches exactly the 10 lane transcripts: 8 are `MISSING` keys, and 2 are this round's running lanes.
  - The copier's list is `LANES` and the pusher's is `DIRS`.
- **L370:** `common.py:44` runs `S/scripts/run_in_tree.bash … S/scripts/serve.py`. #2089 has `serve.py` at the lane root and no `scripts/` directory.
- **L608:** `refs/pull/2088/head` is `1f116c38`, with parents `2439d049` and `7e8c7ff9`. `refs/heads/docs/register-round-42-second-fixforward` is gone.
- **L283:** its lines and quote are right, but the list is incomplete (LOW-2).

## Frozen copies (task 3)
- All 8 README sha256 prefixes match their files, and no file is missing from the README.
- **"Cited by" against the reports that quote each sha:** an exact match on all 8 rows.
- **Reports that cite a copy by path only:** 2 are not listed (NIT-3).
- **Cited but missing from the directory:**
  - document 2 at `2e4917c2` (7 reports) and document 3 at `main` (3 reports), both kept byte for byte in git;
  - PEER `62f9b2bf…` (1 report), which is not on disk (LOW-3).
- `hc1/dry_body.md` and `hc1/pending_corrections.md` are cited too, but they are not handoff copies.

## Opener (task 4)
- I ran the command exactly as given, with `--dry-run`. It exited 0, printed "DRY-RUN pcalnon/juniper-ml", base `main @ b82d12d7`, branch `docs/handoff-round42-consolidated`, and "(nothing written)". It reported no problems.
- **36 files, matching r4's Git status list and Appendix G:**
  - the two handoffs;
  - 5 reports (key-leaks ruling, 3 data438-fixforward reports and the PR draft);
  - 8 `handoff-2fba4397-*` and 8 `handoff-consolidated-*` reports;
  - `handoff-frozen/` (8 copies and the README);
  - the archiver, the extractor, the stall probe and the opener.
- None of #2089's four path prefixes is in the list.
- The commit body's last paragraph carries `Allow-Symbol-Loss: const:SESSIONS` together with the trailers.
- The stale-base check passed, with fizzy 8 commits behind `origin/main`.

## Integrity and scripts
- **sha256 before and after:** `6a052d09a1d2db6e69285596401e6ad3654723f9f19c6f4658a9166f7c737d9b` both times. The live untracked file was identical at both points.
- **Changed:** no repository file.
  - No fetch. Git ran read-only in fizzy, plus `status`/`rev-parse` with `--no-optional-locks` in the juniper-data worktree.
  - I printed no environment value, and redacted email-shaped text in everything I displayed.
  - /tmp inode use is at 82%.
- **Probe scripts,** in `…/scratchpad/hc4/laneF/`:
  - `archiver_check.py`, `archiver_probe.py`, `context.py`, `executor_pushes.py`, `executor_transcript.py`, `find_peer_62f9.py`, `frozen_check.py`
  - `gh_2089.py`, `gh_codeql.py`, `gh_probe.py`, `gh_runs.py`
  - `hazy.py`, `hazy_redactions.py`, `hazy_untracked.py`
  - `listagents.py`, `parked_rows_elsewhere.py`, `pr2089_identity.py`, `rebuild_peer_62f9.py`, `refusals.py`, `unarchived.py`, `uncatalogued_copies.py`, `wordcount.py`
