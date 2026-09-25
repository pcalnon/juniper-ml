<!-- Archived verbatim 2026-09-24 from subagent a8db50d2bc385a75e of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS. No source task is lost and there is no HIGH. There is one MEDIUM: the consolidation PR carries the archiver, and nothing orders other archiving PRs after it; document 2's rule on who archives Lane F's reports is also gone. There are also 9 LOW and 17 NIT findings, and 2 state changes since 02:10Z.

The target is `consolidated_r2_frozen.md`, sha256 `79c0abb4b7dbdf15…`. I checked the hash before and after.

**Documents.** Abbreviations used below:
- **C2** = `consolidated_r2_frozen.md`, the frozen copy of the untracked `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`.
- **C1** = `consolidated_r1_frozen.md`, round 1's target (`96c1b58f…`).
- **D1** = `doc1_r2_frozen.md` (`17ef7db5…`), the frozen copy of `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`.
- **D2** = `doc2_peer_final_2e4917c2.md` (`4ebd0143…`), `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`.
- **D3** = `doc3_predecessor_main.md` (`5b9cd399…`), `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.
- **S** = `reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md`.
- **R1-O / R1-F / R1-P** = `handoff-consolidated-round1-laneO-amputation.md`, `handoff-consolidated-round1-laneF-reprobe.md` and `handoff-consolidated-round1-laneP-fresh-session.md`.
- **R3-F / R3-P** = `handoff-2fba4397-round3-laneF-reprobe.md` and `handoff-2fba4397-round3-laneP-fresh-session.md`.
- **FIX** = `data438-fixforward-round1-fix-report.md`; **DRAFT** = `data438-fixforward-pr-draft.md`.
- **OPENER** = `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py`; **ARCHIVER** = `util/ad-hoc/2026-09-24_archive_round42_reports.py`.

Every "L" number refers to the document named with it.

## Findings

### HIGH
None.

### MEDIUM

**M1. The consolidation PR carries the archiver, nothing makes other archiving PRs wait for it, and D2's archiving rule is gone.**
- **D2 L139:** "**Archiving.** Its archiver byte-checks every file whose first line reads `<!-- Archived verbatim … -->` … Use that header, and send it the filenames." Here "it" is the register lane: Lane F sends Lane R its report filenames, and Lane R adds the `MISSING` entries.
- **C2 says instead:**
  - L123-124 tells every session to edit ARCHIVER itself: "Add your session's full UUID … to `SESSION_IDS`, and each report to `MISSING`."
  - L34 (Lane F's stay-out list) does not name ARCHIVER.
  - L179 ships "the archiver's new `MISSING` entries" in the consolidation PR.
  - L176 and L188 freeze fizzy's HEAD: no commits, and no `reset` or `checkout` before the consolidation PR merges.
  - L186 says OPENER refuses "a stale base".
- **Evidence:**
  - OPENER's `blob()` loop compares `HEAD:<f>` with `origin/main:<f>` for every file that `main` holds.
  - In fizzy, `git diff HEAD --stat` shows ARCHIVER +24 (Lane R's 16 `MISSING` entries) and `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` +58/-11.
  - Both files still equal `main` at HEAD `ee0b9382`, so they pass today.
  - Work 1 and Work 5 archive reports, and so do Lane F's Work 2-4. Under L124, every one of them edits ARCHIVER.
- **Consequences:**
  - Any PR that changes ARCHIVER on `main` before the consolidation PR opens makes OPENER refuse it for good, because fizzy's HEAD may not move. C2 gives no fallback.
  - If both PRs are open, the second to merge conflicts in `MISSING`. A signed commit cannot resolve that, so it must be superseded.
  - After a split, both lanes edit ARCHIVER.
- **Changes:**
  - **Add after L186:** "- **Land the consolidation PR before any other PR touches a file it carries**, above all `util/ad-hoc/2026-09-24_archive_round42_reports.py` (every lane's archiving edits it) and `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py`. The opener compares fizzy's HEAD, which must not move until that PR merges, with `origin/main`: once another PR changes either file on `main`, it refuses them for good. Then ship with `util/open_signed_pr.py --branch docs/handoff-round42-consolidated` directly, rebuilding those two files from `git show origin/main:<file>` plus fizzy's additions (read fizzy's copy with `cat`). Until the consolidation PR merges, add no `MISSING` entries elsewhere; add them afterwards, rebuilt from `origin/main`."
  - **At L34, append to Lane F's stay-out list:** "and `util/ad-hoc/2026-09-24_archive_round42_reports.py`: Lane F heads its reports with the archive header and sends Lane R their filenames (document 2, "Coordination" → "Archiving"); Lane R adds the `MISSING` entries."

### LOW

**L1. The Work 8(a) anchors are wrong at the data branch head and stale on cascor `main`. This is R3-F N6 applied wrongly, so L9's "Every correction is applied, both there and here" overclaims.**
- **D1 L101:** "at `0f0f7e0e`; `d1c66a11` shifts them to `188-213` and `:215`".
- **C2 L246:** "at `0f0f7e0e`; the data fix-forward shifts them by one line".
- **Measured with `git show`:**
  - At `94ce8b1f`, `request_validation_handler` is at `:193-218` and the `ValueError` handler at `:220`, six lines down. That is where they will sit once the fix-forward merges.
  - At data `main` `26491531` they are still `:187` and `:214`.
  - C2 L247 gives cascor `:856`/`:916`. On cascor `main` `0fbb447a` (after #690, merged 02:06:36Z) they are `:858`/`:918`. They were `:856`/`:916` at `7f4a7213` and `b9484fef`.
- **Change L246:** "(…, at `0f0f7e0e` and on data `main` `26491531`; at the fix-forward's head `94ce8b1f` they are `:193-218` and `:220`, where they will be once it merges)".
- **Change L247:** "cascor (`src/api/app.py:858`, `ValueError` handler `:918` on `main` `0fbb447a`; `:856`/`:916` before #690)".

**L2. Work 1's refutation path lost the model brief, the spec files and the brief corrections. R1-P L4 is applied only in part, with no reason given.**
- **D1 L64:** "Its **brief** is TWO `user` records. 19:37:50.383Z is the task: the regime, the upload proof, an unsigned LOCAL scratch commit, the trailers, the PR prohibitions, and four scratchpad spec files (…)".
- **D1 L71:** "brief 1's step 5 … is obsolete … brief 2 says to UNSET the DSN variables".
- **D1 L168:** "`[ahead N]` = an unsigned scratch commit: never push it; after a push and a fetch, `[ahead 1, behind 1]` is expected".
- **C2 L585** names only "the round-2 reports, both round-1 reports, `data438-fixforward-round1-fix-report.md`, and `git diff 0f0f7e0e <head>`". C2 contains the transcript path 0 times. C2 L160 now reads only "never push from it".
- **Append to L585:** "Model its brief on the first executor's: the `user` records at 19:37:50.383Z (the regime: the upload proof, an unsigned LOCAL scratch commit so the screens can run, never pushed; the trailers; the PR prohibitions) and 23:48:49.313Z in `/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`. Also pass the four tmpfs spec files, if they still exist: `data_round3_original_brief.md`, `data_round4_spec.md`, `data_round4_redirect.md` and `old_executor_summary.md`. Correct two things: `--expected-head` is the branch's current head, not brief 1's step 5, and the DSN variables are set to `""`, never unset (brief 2 says unset)."
- **Restore D1 L168's comment on C2 L160.**

**L3. The merge of R1-O M4 and R1-P M6 leaves Work 5 with no vehicle once the closes PR has merged.**
- **C2 L592:** "Its fix-forward either merges before the closes PR opens, or rides in it."
- **C2 L594** says to open the closes PR early.
- C2 L37-38 says the sweeper arms open PRs, its merges are intended, and "Do not draft or disarm a PR to hold it". An early closes PR can therefore merge before Work 5 is done.
- R1-P M6 had "Anything later goes in a fixup while the PR is open, or in one follow-up PR from fresh `main` after it merges". C2 keeps that only for row closures (L599) and Work 8 (L601).
- **Replace L592 with:** "Its fix-forward merges before the closes PR opens, rides in it while it is open, or follows it in ONE PR from fresh `main` after it merges. The same holds for Work 7 and for Appendix B answers that arrive after it merges."

**L4. D2's rule to validate every fixup and every new PR is narrowed to Work 4.**
- **D2 L108:** "Validate every fixup and every new PR with at least two lanes."
- **C2:** only L79 (Work 4) requires it. For the #690 and #685 fix-forwards, L402 and L404 say only "fix forward in a NEW PR". L402's "Once its validation holds, CASCOR-008 and -013 can close" can be read as permission to close without the fix-forward's own validation.
- **Add to L99:** "Validate every fixup and every new PR, of either lane, with at least two lanes (document 2, OPEN 4). A row closes only once its fix-forward's validation also holds (Appendix A, Gates)."

**L5. This file's own validation lanes are missing from "In flight". R1-P L6 is NOT APPLIED, with no reason given.**
- **C2 L70:** "**In flight:** nothing."
- At 02:10Z this very round's lanes were starting. They are subagents of [24f8d8] and die with it. C2 L46 then says "with nothing in flight, that is safe" to close it.
- **Replace L70's first sentence with:** "**In flight:** nothing of yours. This file's validation lanes are [24f8d8]'s subagents. If the report count (the `ls … | grep -c` check) is short, find their transcripts with `grep -l consolidated_r /home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/*.jsonl`, add their `MISSING` entries keyed by agent id, and archive them."

**L6. The instructions for running the opener yourself are incomplete, and they misstate its stale-base test.**
- **C2 L186:** "run `util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py` … refuses … a stale base (… a file that `origin/main` already holds is refused)".
- **What the script actually does:**
  - It takes `REPO = Path(__file__).resolve().parents[2]`, so it always operates on fizzy. The relative path in C2 does not exist in the successor's own worktree.
  - It requires `--title`, `--message`, `--commit-body-file` and `--body-file`. C2 supplies none of their text.
  - It refuses a file whose `origin/main` blob differs from fizzy's HEAD blob, not every file that `main` holds. ARCHIVER and the extractor are on `main` and pass.
  - After the consolidation PR merges, every path it shipped fails this test, so L188's "ship anything newer in a follow-up" cannot use the opener.
- **Change:**
  - Make it: "run `python3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py --title … --message … --commit-body-file … --body-file …`, with `--dry-run` first. It works on fizzy wherever you run it, and you write the title, the message and both bodies."
  - Make the parenthetical: "(a file whose `origin/main` copy differs from fizzy's HEAD copy)".
  - At L188: "…in a follow-up with `util/open_signed_pr.py`".

**L7. DRAFT uses its own round numbers, and they differ from C2's.**
- **C2 L327:** "round 2's reports must be added to it before the PR opens."
- DRAFT's Summary (its L8) begins "**Round 2, `94ce8b1f`**", and its L64 heading is "## Round 2: the findings in `data438-fixforward-round1-laneA-reprobe.md` and …". So a "Round 2" section already exists, and it means the fix, not the pending validation.
- **Append to L327:** "The draft's own "Round 2" (its L8 and L64) is `94ce8b1f`'s answer to `data438-fixforward-round1-*`. Add the pre-PR validation of `94ce8b1f` as a new section, and archive its reports as `data438-fixforward-round2-lane{A-reprobe,B-refute}.md`."

**L8. `hazy-beaming-map` is sent to Appendix F's gate, but Appendix F does not list it.**
- **C2 L531 (Appendix I):** "Its scripts are all on `main`; the worktree is a cleanup candidate (Appendix F's gate)."
- Appendix F (L460-483) does not list it, although the worktree exists.
- **D3 L73:** its tracked register, primer and `docs/REFERENCE.md` edits were "equal to main's current content" at 11:10Z. #2088 has since changed all three on `main`.
- **Add after L464:** "- `juniper-ml/.claude/worktrees/hazy-beaming-map` (session `8f86dec2`, ended): document 3's worktree. Its 16 `util/ad-hoc/2026-09-24_*` scripts are on `main`. Its tracked M's are pre-#2088 copies of `main`'s files, not unshipped work. It is a cleanup candidate under this gate."

**L9. The owner of the notify-consumers 403 has handed off.** This is state from before 02:10Z that C2 does not reflect, like R1-O L1 was for #2096.
- **C2 L147:** "…"containers [2703c8]", which owns the 0.16.0 notify-consumers 403". C2 L284 says "The containers session owns it."
- juniper-ml#2100 opened at 01:39:45Z. It is OPEN, and its body says "Do not merge yet".
- It carries `HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md`, whose header reads "session `containers [2703c8]`". Its item 2: "`CROSS_REPO_DISPATCH_TOKEN` cannot dispatch to juniper-recurrence … every data release fails the same way until the owner fixes the token … A replay needs the owner's approval each time."
- **Change L147 and L284 to:** "…handed off at about 01:40Z in juniper-ml#2100 (that handoff's item 2 carries the 403): route it to that handoff's successor. The next data release (Appendix B) will fail the same way until the owner fixes the token."

### NIT
- **N1.** ECO-014 lost D2 L78's "API bodies", which became "a 409 body" (C2 L206). S L17-18 lists three bodies: `main.py:3712/:3714` (the 409), `recurrence_backend.py:219→:287`, and the adapter's `{"error": str(e)}`.
- **N2.** F5 lost D2 L91's reason for `od -c` ("the Write, Edit and SendMessage paths turn a typed escape into U+1F511") and "so the pair is inert there" (C2 L425).
- **N3.** The stray-branch item lost "because the branch names differ" (D2 L125 → C2 L268).
- **N4.** The blank-key worktree row lost "HEAD `8917fdac` is #683's commit" (D2 L201 → C2 L473).
- **N5.** Appendix E lost "that survives every suite today" (D1 L368 → C2 L456). That is why F3 is rated MEDIUM.
- **N6.** The D-B bullet "(caching): data#428 and #438 merged" was dropped (D1 L278 → C2 L285).
- **N7.** The scratch commits lost their purpose, "made only so the CI screens could run" (D1 L176 → C2 L176).
- **N8.** "the recurrence ones in optional extras" was dropped (D1 L222 → C2 L438).
- **N9.** #2089's CodeQL failure time, 00:27:51Z, was dropped (D1 L41 → C2 L275).
- **N10.** D1 L166's expected archiver counts ("42 … 34 on origin/main … 52 on #2097's head") became "positive" (C2 L166). It is 48 in fizzy now.
- **N11.** Some Appendix I rows name only part of their destination:
  - D1 "Completed" also lands in Appendix A (the ruling) and Appendix B (#2089's CodeQL).
  - D1 "Remaining 2, 3, 6, 7" land in Appendix J.
  - D2 "Coordination" also lands in Appendix E (the gate file) and in the traps section (archiving).
- **N12.** The Goal (L21-L85) is 1,337 words against the ~1,200 target. R1-P N8 measured 1,315 for C1.
- **N13.** An offline [24f8d8] is ambiguous:
  - L47 says "offline: carry on".
  - L186's ship gate says "gone".
  - L188's reset guard says "listed".

  Say whether an offline row counts as gone.
- **N14.** L45 tells a listed [24f8d8] to "launch and ship nothing more". First ask whether it is about to open the consolidation PR, which was R1-P M2's question (1).
- **N15.** The reason for update-branch was dropped: "an armed, BEHIND PR waits forever" (D3 L54 → C2 L105). It matters now that #2097 and #2089 are BEHIND.
- **N16.** F-CANOPY-060 lost its fix, "cut only at ' To accept it,'", and its source line, `juniper_data/core/limits.py:168` (S L37 → C2 L228). #2096 and the reservation still hold both.
- **N17.** R3-P H1's "ask it … to forward what the peer … sends" is not in L45. A document-2 successor messages [24f8d8] first (D2 L23).

### Moved since 02:10Z
- **MV1.** Post-merge CI on cascor `0fbb447a` finished green at 02:16:38Z (C2 L62: "cascor still running at 02:07Z"). The CI/CD run on #689's own merge, `b9484fef`, was *cancelled* at 02:06:57Z, superseded by #690's push. Its other four checks passed, and `0fbb447a`'s run covers #689.
- **MV2.** At 02:12Z `mergeStateStatus` was **BEHIND** for both #2097 and #2089, not BLOCKED (C2 L66, L154, L156). `main` moved at 01:47:47Z and 02:02:03Z, so this may already have been stale at writing. CodeQL still fails on both, both are still unarmed, and landing them now also needs update-branch.

## The merge of R1-O M4 (open early) and R1-P M6 (Work 8/9 first; one register PR)

C2 keeps what each lane protected:
- **Rows filed early** (M4): Work 6 "Open it early" and files the three rows OPEN.
- **Work 7 unblocked** (M4): it waits only for the filing.
- **A destination for (a)** (M6): "in the closes PR before it merges, or in a follow-up".
- **Work 9's note** (M6): it is recorded when the PR opens.
- **One open register or primer PR** (M6): the Work preamble keeps the rule.

It loses M6's general "anything later goes in a fixup while open, or in one follow-up after it merges". That makes Work 5's "or rides in it" unworkable under the sweeper (L3). Work 7 is saved only by Appendix E's "with or after the closes PR".

The choice goes against [24f8d8]'s own 20:37Z plan ("my closes PR … waits on the data and cascor fix-forwards", R3-P N7). I judge it right: no source gates the PR itself, and D3 L41 files ECO-013 and ECO-014 as "ruled and in flight, so not parked".

## Conflicts between the sources, and C2's choice

| Conflict | C2 chose | Right? |
|---|---|---|
| Message [042116]? (D1 "if still listed, message it too"; D2 L3 "Never") | Never, with the reason (L11) | Yes |
| APD-CASCOR-014 close (D1: F4 merges AND validation holds; D2 L134: "when F4 lands") | D1 (L211-212) | Yes: it matches the general gate at L195 |
| APD-ECO-014 (D1: close once #685's validation is cited; D2 L136: "condition is met") | D1 (L206, L212) | Yes |
| F8 (D1: the marker; D2: "killed by F3") | D2 (L418) | Yes |
| F9 anchor (D1 `:57-58`; D2 `:58`) | `:57-58` | Yes |
| Recurrence lock path | D2's full path, `:70/:74` | Yes: verified `==0.4.0` and `==0.7.0` there |
| Canopy F5 (D1: no `_ENCODING_PROBES`; D2: `NON_ASCII :172` only against "key1") | D2 | Yes |
| Who asks the owner (D1 and D2 overlap on the stray branches) | Tags: [F] for the canopy items, [R] for the CodeQL blocks including #2097's | Yes; D1 had Lane R surface #2097's block |
| When the closes PR opens | Early | Yes, with L3's fix |
| #690 lanes (D2: "on each commit") | "on the merged result, covering each commit's change" | Yes, now that it has merged |

## Appendix I: do the rows land where they say?
- All 21 D1 rows, 14 D2 rows and 15 D3 rows land. The imprecise ones are listed in N11.
- The exception is D3's "Git status (hazy-beaming-map)" row, which points into Appendix F, where the worktree is absent (L8).

## Round-1 dispositions

| Finding | Disposition | Where in C2 |
|---|---|---|
| R1-O H1 (#2097's CodeQL) | APPLIED | L51-55, L154-155, L274-276, L241 |
| R1-O M1 (worktree guard; re-copy) | APPLIED | L188; re-copy done and verified (DRAFT = `"# "+title.strip()+"\n\n"+body`) |
| R1-O M2 (re-read the PR head) | APPLIED | L92 |
| R1-O M3 (lane tags) | APPLIED | L85, L254, and the tags |
| R1-O M4 (open early) | APPLIED, merged with R1-P M6 | L81, L594-599; gap in L3 |
| R1-O M5 (name this file) | APPLIED | L4 |
| R1-O L1-L3, L5-L9 | APPLIED | L234; L411; L200; L601; L17 and L48; App G; L157; L168 |
| R1-O L4 (data squashes with `COMMIT_MESSAGES`) | APPLIED, as two options | L103, L325 |
| R1-O L10 (Appendix I rows) | APPLIED; the hazy-beaming-map row APPLIED WRONGLY | L518, L530-532; see L8 |
| R1-O N1-N11, N13-N23 | APPLIED | e.g. L11, L102, L166, L344, L333/L346, L290, L584, L275, L423/L427, L270, L48/L49/L462, L206, L426, L133, L190, L91, L221, L354, L278, L33, L200, L80 |
| R1-O N12 ("not armed") | MOOT (merged) | — |
| R1-F M1 (#2096) | APPLIED | L147, L234 |
| R1-F L1, L2, L4 | APPLIED | L190; L17; L496 |
| R1-F L3, N1 (relaunch recipe; third record) | MOOT: the executor finished | but see L2 |
| R1-F N2-N5 | APPLIED | L219; L400; L169; L475-478 |
| R1-F MV1-MV7 | APPLIED as state | L62, L70-73, L186, L183, L147, L391 |
| R1-P H1 | APPLIED | L160 (`--no-optional-locks`) |
| R1-P M1 | APPLIED / MOOT | First action 2 |
| R1-P M2 | APPLIED through OPENER; its question (1) not carried | L45-46, L186; N14, L6 |
| R1-P M3-M5 | APPLIED | L4; L51; L150, L152, L167 |
| R1-P M6 | APPLIED, merged | see above |
| R1-P L1-L3, L5, L7-L8 | APPLIED / MOOT | L602; L607-608 (bodies verified: #2080 L19, L23-24, L65, L69; #2088 L47); —; L188; L254, L270, L272; L389 |
| R1-P L4 | APPLIED IN PART; spec files and briefs dropped, no reason given | L585; see L2 |
| R1-P L6 | NOT APPLIED; no reason given | see L5 |
| R1-P N1-N7, N9 | APPLIED | L14; L169; L590 (7 files verified); L40; L98; L44; L157/L163; L115 |
| R1-P N8 (length) | NOT APPLIED (informational) | N12 |

**D1's own round-3 corrections, as they reach C2:**
- **R3-F:** M1, L1, L2, L3, L5, N1, N4, N5, N8, N9, N10 and N12 are all present. N2 is partial (N10 here). N6 is **APPLIED WRONGLY** (L1). L4, N3 and N11 are moot unless the briefs are reused (L2). N7 is Goal length (N12).
- **R3-P:** H1 is present less its "forward" ask (N17). M2, L1-L5, L7, L8 and N1-N5 are present. N7 was reversed deliberately (see the merge above). N8 is lost (L2).

## Item tables

P = PRESENT, A = ALTERED, L = LOST, R = RETIRED.

### Document 1 (D1)

| Items | Content | In C2 | Class |
|---|---|---|---|
| D1-001–004, 006–007, 009–010, 012–013, 015 | Header, validation, predecessor, superseded note, state moved, paths, policy, lane merges, first actions 1-3 | L3-19, L24, L31, L37-48 | P |
| D1-005, 008 | "Superseded"; "if you hold only this file" | this file | R |
| D1-011 | The grant was [24f8d8]'s | L40, without who held it | A (trivial) |
| D1-014 | First action 2: executor alive, message first | First action 2 (message kept; executor finished) | P |
| D1-016 | Message [042116] too | "Never" (L11) | A (conflict, right) |
| D1-017, 019 | Find the peer's PR; re-copy the draft | #2097 known; draft re-copied (verified) | R |
| D1-018, 021 | Ship gate; never reset | L46, L186, L188 | P |
| D1-020 | Check `main` and open PRs; opener | L186 | A (L6) |
| D1-022–029, 031–039 | #2088; #2089; data fix-forward state; ruling; resolved list; executor finished | L60-73, App C, App G, App H, L216, L275 | P |
| D1-030 | #2089 CodeQL at 00:27:51Z | time dropped | A (N9) |
| D1-040 | Executor transcript and brief (the regime) | absent | A (L2) |
| D1-041 | Finished-or-dead test; recovery | — | R (finished) |
| D1-042 | Remaining 0 (consolidate) | this file | R |
| D1-043–059, 062–068 | Reconciliation; Remaining 1-8 steps | L212, L57, L185-186, Work 1-10, App A, App J | P |
| D1-060 | (a) data anchors | "shifts by one line" | A (L1) |
| D1-061 | (a) cascor anchors | `:856`/`:916`, stale | A (L1) |
| D1-069, 151 | Routing and the FYI: containers owns the 403 | L147, L284 | A (L9) |
| D1-070–090 | Traps | L89-146 | P |
| D1-091 | `git status --short` count | `ls` count, L168 | A (adequate) |
| D1-092, 101 | `gh pr view 2088`; transcript age check | — | R |
| D1-093–097, 099, 102–103 | Verification commands | L154-171 | P |
| D1-098 | Archiver expected counts | "positive" | A (N10) |
| D1-100 | Meaning of `[ahead N]` | "never push from it" | A (L2) |
| D1-104 | Scratch commits' purpose | dropped | A (N7) |
| D1-105–112 | Ship list; #2089 exclusion; data worktree; older worktrees | L177-189, App F | P |
| D1-113–122, 124–128, 130–150, 152–156, 158–161, 164–175, 177–179 | Appendices A, B, C, D and E; changed files | App A-E, App G, App I | P |
| D1-123 | F8 → Remaining 5 | "killed by F3" | A (conflict, right) |
| D1-129 | Caps "in optional extras" | dropped | A (N8) |
| D1-157 | The D-B bullet | lead only | A (N6) |
| D1-162, 163 | Re-copy recipe; rebuild if lost | done | R |
| D1-176 | F8 "survives every suite today" | dropped | A (N5) |

### Document 2 (D2)

| Items | Content | In C2 | Class |
|---|---|---|---|
| D2-001–010, 013–014, 016–031, 033–039, 041–049, 051–058, 060–066, 068–071, 073, 075–076, 078–099, 101–112 | Header, which document governs, evidence, Step 0, Goal, Merged, OPEN 1-5, coordination, canopy ledger, release facts, traps, worktrees, verification commands, Git status | L11-17, L28-40, First actions 2-4, App A-D, F, H, L90-147, L154-171, L190 | P |
| D2-011, 012, 015, 113 | "You replace [042116]"; send the path; no successor; `[]` → ask | — | R |
| D2-032 | "(re-probe and refute) on each commit" | post-merge form | A (adequate) |
| D2-040 | ECO-014 "API bodies" | "a 409 body" | A (N1) |
| D2-050 | F5's `od -c` reason; "inert" | dropped | A (N2) |
| D2-059 | Validate every fixup and every new PR | Work 4 only | A (L4) |
| D2-067 | "because the branch names differ" | dropped | A (N3) |
| D2-072, 074 | CASCOR-014 and ECO-014 conditions | D1's gates (L212) | A (conflict, right) |
| D2-077 | Archiving: "send it the filenames" | absent | A (M1) |
| D2-100 | Blank-key HEAD `8917fdac` | dropped | A (N4) |

### Document 3 (D3)

| Items | Content | In C2 | Class |
|---|---|---|---|
| D3-001, 003–004, 012, 016–017, 019, 021–024, 027 | Author, Goal, policy, #2081's CodeQL, Remaining 3, 4 and 6, traps, appendix | L14-15, L24, L37-40, App A, App B, L91-110, App I | P |
| D3-002, 005–011, 013–015, 018, 025 | Predecessor; Completed; In flight 1 and 3; Remaining 1, 2 and 5; verification commands | App I (all history) | R |
| D3-020 | "Armed, BEHIND waits forever" | dropped | A (N15) |
| D3-026 | Git status of hazy-beaming-map | App I → App F, absent there | A (L8) |

### Snapshot (S)

| Items | Content | In C2 | Class |
|---|---|---|---|
| S-002, 004, 008–009, 011–015, 020, 023, 028 | ECO-013 evidence, LOW 3/4, clobber warnings, peer acks, closes, residue, #683 residue, CodeQL detail, 0.16.0 defects, verify first | L200, App A, App B, L33-34, App C L369 | P |
| S-001, 005–007, 010, 017–019, 021–022, 024–027 | Ruling to extract, peer PRs, #686, status lines, second fix-forward, follow-ups | done or overtaken (primer round-2 and ml2080 lanes: archived on `main`, verified) | R |
| S-003 | ECO-014 bodies (plural) | "a 409 body" | A (N1) |
| S-016 | F-060's fix recipe | dropped | A (N16) |

## Verified this round
- **Live state (gh, 02:12-02:23Z):**
  - #2097 and #2089 are OPEN, BEHIND and unarmed, with CodeQL `fail` on both.
  - No consolidation PR exists.
  - The data branch is at `94ce8b1f`, with no PR.
  - No PR is open in juniper-data, juniper-cascor or juniper-canopy.
  - #2096 is OPEN and armed, at `00e9eb2d`.
  - #689 and #440 merged by `pcalnon` at their single validated commits (`97341680`, `0bee089e`).
  - #690's head was `81154187`; it merged as `0fbb447a`.
  - The head branches were auto-deleted (`delete_branch_on_merge` is true in all three repos).
  - Both juniper-data and juniper-cascor squash with `COMMIT_MESSAGES` / `COMMIT_OR_PR_TITLE`.
- **The data fix-forward:**
  - `94ce8b1f`'s message carries `Allow-Symbol-Loss: method:LocalFSDatasetStore.save func:_file_lock_is_held` in the paragraph above its trailers.
  - `d1c66a11`'s subject ends "a storage fault is a 500".
  - The data worktree is clean and in sync (`--no-optional-locks`).
- **FIX against C2 Appendix C:** every disposition, number and "noticed" item is carried. Omitted: the `xproc_create_race.py` result, stripe_probe's L1 and M lines, and fault_survey's extra type-only warning.
- **The #2080 and #2088 bodies:** every line number in Work 9 holds.
- **Archiver and inventory:**
  - ARCHIVER `--check` gives 48 OK and 0 DIFFER/REFUSE/Traceback.
  - The report count is 16.
  - `MISSING` holds all 15 of Lane R's subagent reports.
- **Other checks:**
  - The #2088 delta changes 7 `util/ad-hoc/` files.
  - Register L176 and L177 on `main` are as C2 describes.
  - The recurrence lock pins at `:70`/`:74` hold.
  - MEMORY.md is 24,929 characters.
  - All 7 worktrees plus the 4 older ones exist.
  - #2097 holds 95 files (12 lane reports and 10 validation reports).
  - Canopy's Appendix E anchors at `dc5ea02e` hold: `:42`, `:49`, `:52`, `:137`, and `csrf.py:97`.
  - cascor `conftest.py:37` and `test_api_security.py:31` hold at `0fbb447a`.

## What I could not verify
- `ListAgents`, which a subagent cannot load.
- Whether [24f8d8] will open the consolidation PR, and whether CodeQL will pass it.
- The four "turn-ending" Lane F reports against their transcripts.

**Side effects:**
- I ran `git fetch origin main` in the shared juniper-cascor clone, which advanced `origin/main` from `b9484fe` to `0fbb447`. Everything else was a read: `git show` and `cat-file` in the data, cascor and canopy clones; `git diff` and ARCHIVER `--check` in fizzy.
- My scratch files in `hc2/laneO/` are deleted. `/tmp` is at 82% of its inodes.

**Changed:** no repository file or report.

Counts: D1 152 PRESENT / 17 ALTERED / 0 LOST / 10 RETIRED (179); D2 100 / 9 / 0 / 4 (113); D3 12 / 2 / 0 / 13 (27); S 12 / 2 / 0 / 14 (28). Round 1: 80 findings, of which 70 APPLIED, 2 APPLIED IN PART or WRONGLY, 2 NOT APPLIED and 6 MOOT. Findings: 0 HIGH, 1 MEDIUM, 9 LOW, 17 NIT; 2 moves since 02:10Z.
