# R1-D — adversarial analysis of the conclusions (round 1)

Archived verbatim from the lane's final message (2026-09-24). The only change is transport escaping: `&amp;`, `&lt;` and `&gt;` decoded.
Artifact reviewed: `r1/DRAFT_r1.md`, sha256 `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a`.

---

## Verdict
**SAFE AFTER FIXES.** Archived as written, `DRAFT_r1.md` has two problems. Its A9 cleanup list removes the only remaining anchors of two commits that its own A6 says to keep. And it puts a false premise ("already unreachable") and an unworkable option ("make 2b's preflight warn") to the owner. All fixes are text-level.

`S` below means `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle/reports/2026-09-23_y2-wave2-consensus/session-state/`.

## Findings

**1. MAJOR (could cause irreversible loss): A9 marks the last holder of two A6-protected commits as eligible now.**
- **Location:** A9, "canopy, now eligible except where A6's table holds a branch: `…fix--idle-cuts-round3-wording--20260923-2238--e9053227`: #684 merged. Local head `135c2782`, clean." A6's table has no `fix/idle-cuts-round3-wording` row.
- **Attack:** The only things still holding `26bf27b3` and `96e7b105` are that branch's reflog and that worktree's HEAD reflog. The canopy cleanup procedure removes both.
- **Evidence:**
  - Searching all of canopy's `.git` except `objects/` for the three SHAs finds them only in `logs/refs/heads/fix/idle-cuts-round3-wording`, `logs/refs/heads/perf/idle-dispatch-cuts-v2`, and those two worktrees' `logs/HEAD`.
  - `git -C juniper-canopy reflog show fix/idle-cuts-round3-wording` shows `96e7b105 …@{2}` and `26bf27b3 …@{3}`.
  - canopy `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md:177-195`: Step 9 is `git worktree remove [--force]`, which deletes the worktree's `logs/HEAD`. Step 10 is `git branch -d`, then `-D`, which deletes the branch reflog.
  - GitHub returns 422 for all three SHAs, and the primary is the only canopy clone on the host.
  - Once both reflogs are gone, the next auto-gc after the 2-week grace deletes the objects. The content survives on main via `135c2782` → `f2147403` (#684), but the SHAs the ledger cites do not.
  - `78c057e2` is protected only incidentally, because `perf/idle-dispatch-cuts-v2` is in the table for other commits.
- **Confidence:** 0.85.
- **Fix:**
  - Add an A6 table row: "| canopy | `fix/idle-cuts-round3-wording` (worktree `…idle-cuts-round3-wording…`) | `135c2782`; its branch reflog and its worktree's HEAD reflog are the ONLY holders of `26bf27b3` and `96e7b105` |".
  - Change that A9 bullet to: "…#684 merged, clean, but HELD: its reflogs are the only holders of `26bf27b3` and `96e7b105` (A6)."
  - Add to A6: "Removing a worktree deletes its HEAD reflog. Deleting a branch deletes the branch's reflog."

**2. MAJOR: A6's premise is false, and the owner question is built on it.**
- **Location:**
  - A6: "…are already UNREACHABLE. They are still in the object store, but no branch holds them, so a `git gc` prune can delete them."
  - Goal statement: "**A6, urgent:** … or accept their loss. Three are already unreachable."
  - Verification comment: "# at writing: 78c057e2, 26bf27b3, 96e7b105 UNREACHABLE".
- **Attack:** The draft reasons from "no branch contains it" to "gc can delete it". `git gc` also keeps objects that reflogs reference. The reachability script only runs `git branch -a --contains`; its own docstring lists cat-file, merge-base, branch --contains and worktree list. So the instrument answers a different question from the one the draft asserts.
- **Evidence:**
  - The reflogs hold all three: `78c057e2 perf/idle-dispatch-cuts-v2@{3}`, `26bf27b3 …round3-wording@{3}`, `96e7b105 …@{2}`.
  - Nothing overrides gc or maintenance: canopy `.git/config`, `~/.gitconfig` and user timers have no such settings. No juniper-ml `util/` or `scripts/` tool runs `gc --prune=now` or `reflog expire`; they only use `worktree prune` and `fetch --prune`.
  - With git's default 30-day expiry for unreachable reflog entries, these entries last until about 2026-10-23, and then a 2-week prune grace applies.
  - "Urgent" therefore points at the wrong threat: the risk is cleanup (finding 1), not gc. The question also offers only "push" or "lose"; an interim local ref, with no push, is a third option.
- **Confidence:** 0.9.
- **Fix:**
  - A6: "…are held by no branch, only by reflogs (`78c057e2`: `perf/idle-dispatch-cuts-v2@{3}`; `26bf27b3`/`96e7b105`: `fix/idle-cuts-round3-wording@{3}`/`@{2}`, plus each worktree's HEAD reflog). Default `git gc` keeps them until about 2026-10-23 plus a 2-week grace. The near-term threat is deleting either branch or worktree (A9). GitHub has none of them."
  - Goal statement: "Three are held only by reflogs that a cleanup would delete."
  - Relabel the script's `UNREACHABLE` as `NO-BRANCH`, and have it report reflog holders.

**3. MAJOR: X1's option 2 cannot remove the stake it is offered against.**
- **Location:** X1, "approve the preflight-warns change, which is a code change and so takes the delta route". The goal statement repeats it as "approve making 2b's preflight warn until 2a ships".
- **Evidence:**
  - `S/r15/pr_wave2b_deploy.md:14`: "With the long form, Docker refuses to start the container on **every** path, bare `docker compose up` included… Verified against a real daemon."
  - `S/r15/2b_deploy.diff` defines the mount as `type: bind` … `create_host_path: false`.
  - `ls …/juniper-recurrence/recurrence-snapshots` returns "No such file or directory".
  - So with a warning preflight, deploy main's full, demo, dev and test bring-ups still fail, just later and at Docker. R15D's "Alternatively…" (`R15D.md:43`) carries this flaw, and the draft passes it on unexamined.
- **Confidence:** 0.8.
- **Fix:** "The owner chooses: exclude the four PRs from the sweeper, or accept a fix-forward. Under fix-forward, if 2b lands first, deploy main's recurrence profiles refuse to come up, with the preflight's pull hint, until 2a is merged and the shared checkout is pulled. (Suggestion: creating `juniper-recurrence/recurrence-snapshots/` in the shared checkout before opening 2b removes that on this host.) R15D's warning-preflight alternative does not help: 2b's long-form mount with `create_host_path: false` makes Docker itself refuse a missing source (`pr_wave2b_deploy.md`, 'The mount is long form')."

**4. MAJOR: the goal statement's only pointer to the details resolves in neither prescribed session.**
- **Location:** Goal statement, "one combined handoff: juniper-ml `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`. Read it in full." Session layout sends Lane B to `idempotent-jumping-sparkle` and Lane A to a fresh worktree cut from main.
- **Evidence:**
  - Searching every juniper-ml worktree and the primary finds the file only in `bubbly-meandering-pie`, untracked.
  - `git cat-file -e origin/main:<path>` reports "exists on disk, but not in 'origin/main'".
  - `idempotent-jumping-sparkle` is at `5ea8e273`, so even a merged copy will never appear in its tree.
  - Git state says "The owner decides whether to open one".
  - Everything Lane B needs is only in this file: the fix list, the two overtaken items and the traps.
- **Confidence:** 0.75.
- **Fix:** "Read it in full at `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`. It is untracked there. Reading another worktree's files is allowed; running git there is not. Once its PR merges, `git show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md` also works, including from `idempotent-jumping-sparkle`."

**5. MINOR: the X2 hint collides with Lane B's own procedure and tools.**
- **Location:** X2, "**A pushed branch with no PR keeps a claim alive without exposing it to the sweeper**…"
- **Evidence:**
  - `S/main/PLAN.md:103`: "nothing is opened or pushed from an unvalidated state".
  - `util/open_signed_pr.py:46-47` and `:276` refuse a branch that already exists.
  - `S/r15/tools/2026-09-23_open_pinned_pr.py:78-84` hard-code the four branch names and upload through that tool.
  - `util/push_signed_commit.py` only adds a commit to an existing branch.
  - § B of `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` requires a branch that "carries the work". Wave 3 and X10 are unstarted.
- **Confidence:** 0.8.
- **Fix:** append "For wave 2 this collides with `S/main/PLAN.md` ('nothing is opened or pushed from an unvalidated state'), and `open_signed_pr.py` refuses a branch that already exists. Never push a planned PR branch name to hold a claim; if you must, push an approved-freeze state under another name. Wave 3 and X10 are unstarted, so no branch can carry them. Their claims lapse on the date."

**6. MINOR: "Both moved sets include a CHANGELOG, so R15D MINOR 1 is now on the critical path" is right for 2b only.**
- **Evidence:**
  - **2a:** #186's CHANGELOG change (`@@ -11,6 +11,20 @@`) is a pure insertion above #172's entry. 2a's first hunk (`@@ -14,11 +14,16 @@`) edits from base line 17, so three unchanged lines separate them and the insertion is identical on both sides. `already_merged` (`freeze_round.py:82-108`) should therefore pass for 2a.
  - **2b:** #231/#232 insert `### Fixed` at base line 81/82 (`@@ -79,6 +124,65 @@`). 2b's `@@ -79,6 +265,24 @@` inserts its own `### Fixed` at the same point. After the three-way merge the two blocks are adjacent, which is the case R15D MINOR 1 describes as "an own edit on the adjacent line ('conflicts')".
  - Neither main patch adds a `+## [` heading, so neither is a release cut.
  - Not executed, because that needs scratch files.
- **Confidence:** 0.7.
- **Fix:** "#186 sits three lines clear of 2a's first edit, so `--merged 2a_recurrence.diff` should pass as-is. 2b's `### Fixed` block and main's sit at the same point above `## [0.3.0]`, the adjacent-edit case MINOR 1 refuses. So MINOR 1 is on 2b's critical path. Neither change is a release cut."

**7. MINOR: B3 blocks on X1 with no default, and the stake is understated.**
- **Location:** "**B3. Open, then merge, per `S/main/PLAN.md`, after X1 is settled.**"
- **Evidence:**
  - The owner's standing ruling covers the default: "Mine: fix forward", and `reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md` says "Its merges are intended… fix forward".
  - The opening order (2b→2a→2c→addendum) is the reverse of the merge order, so a sweeper that merges on green likely inverts all of it.
  - The draft drops R15D's other two consequences (`R15D.md:37-38`): 2b's comment is false until 2c, and the merge-time checks never run. 2a's CHANGELOG ("as juniper-ml's `util/isolated_stack.bash` does") is likewise false until 2c merges.
- **Confidence:** 0.65.
- **Fix:** "If X1 is unanswered when round 16 approves a freeze, proceed under the standing fix-forward ruling. Run R15D's steps: `gh pr view` all four before each merge, and for any out-of-order merge, run its post-merge checks and a squash blob-compare at once."

**8. MINOR: the "one message" owner batch omits owner-only calls the draft itself records.**
- **Evidence:**
  - A7's items 3 ("owner: F-CANOPY-004's contract"), 9 ("the owner's question") and 10 ("owner question").
  - Git state's "The owner decides whether to open one, and whether it also archives the two off-`main` predecessors". B's predecessor exists only untracked in `idempotent-jumping-sparkle`; I verified this with `ls`.
  - B5 defers the leaked-token rotation reminder to the end of Lane B.
  - X4's "explicit decision" to stop the trio names no decider, and C6 waits on it.
- **Confidence:** 0.75.
- **Fix:** add bullets for:
  - ledger items 3, 9 and 10;
  - opening this handoff's PR and archiving both off-`main` predecessors in it;
  - confirming the `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens were rotated;
  - who may decide to stop the trio.

**9. MINOR: "What moved" #5 says R15C M1's last step "catches this", but it will not catch this handoff.**
- **Evidence:** `R15C.md:51` says the step "lists canopy-selection handoffs on juniper-ml `main`". This file's name lacks `canopy-selection`, and it is not on main.
- **Fix:** "It catches #2069/#2082/#2087, not this combined handoff. If this handoff merges before the addendum opens, point the addendum at it by name."

**10. NIT: C6's holder list is incomplete.**
- **Evidence:** from `/proc/*/cwd`, bash pid 2963582 holds the canopy primary and bash pid 2966837 holds the data primary, both started 2026-09-19. The data leg, pid 2856834, runs from `/tmp/juniper-e2e` and holds no primary.
- **Fix:** name both shells, and say the data leg holds no primary.

**11. NIT: main moved inside the draft's own "at writing" window.**
- **Evidence:** `gh api …/juniper-ml/commits/main` returns `c061a99f 2026-09-24T20:37:12Z` (#2086), inside the 20:25–20:45Z window. The header and #3 still say `6c23fdde` / "18 commits". The #3 path log is still empty at `c061a99f`, so the conclusion stands.
- **Fix:** "`6c23fdde` at the window's start; `c061a99f` (#2086) landed 20:37:12Z and touches no upload path."

**12. NIT: "the worktree status [is] re-probed" (Lane B Done) conflicts with "This session could not run git there".**
- **Fix:** "the recurrence and deploy worktrees' status is re-probed; `idempotent-jumping-sparkle`'s is carried."

**13. NIT: the Verification line `cd …/r15 && sha256sum …` persists into the next three commands.** Those commands need the worktree root.
- **Fix:** wrap it in a subshell, `( cd … && … )`, as B's predecessor did.

**14. NIT: "items 4 and 20 of … § B".**
- **Evidence:** item 20 sits under § F of the 09-22 handoff (heading at line 353), "on the same terms as § B".
- **Fix:** "items 4 (§ B) and 20 (§ F, on § B's terms)".

**15. NIT: B2's "must be deleted from every clone" drops the source's scope.**
- **Evidence:** `S/r15_reports/R15B.md:5` ("I deleted it from my clones") and `S/main/lane_R15B.md:37` ("your own rebuild") refer to the lanes' own rebuilds.
- **Fix:** "from every scratch rebuild a lane makes (never the primary checkout or the PR worktree)".

**16. NIT: "held by ONE local branch only" contradicts the table's `723ee812` row, which is held by two.**
- **Fix:** "one local branch (two for `723ee812`)".

## Attacks that failed
- **X1 quotes and facts:**
  - R15D's fix text (`R15D.md:40-43`) and B's predecessor's "Open … as drafts" are quoted verbatim.
  - "use drafts" is indeed not in R15D's fix.
  - Drafts do not hold. ml#2059's GraphQL timeline reads ConvertToDraft 20:24:28Z → Ready 21:47:22Z → AutoSquash 21:47:26Z → Merged 22:57:09Z, and the memory note agrees.
  - The stake matches `pr_wave2b_deploy.md:57` ("Until that pull, every bring-up path refuses").
- **X4 is true:**
  - The trio started 19:37:41–19:38:00Z on 09-22.
  - The E2E arc's `reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_fixture_grow_54.json` records cascor `build_date 2026-09-22T19:37:53Z`; pid 2857489 started 19:37:52Z.
  - The data leg's cwd is `/tmp/juniper-e2e`, and ledger line 7368 is Phase 7's relaunch.
  - Only the trio's canopy connects to `:8202`.
- **Merge approval "none is carried"** matches `feedback_headless_merge_approval_policy.md` ("A HANDOFF DOCUMENT CANNOT CARRY THE APPROVAL FORWARD") and `S/main/handoff_v4.md:6`.
- **Claims:**
  - § B's terms are paraphrased correctly.
  - Successor inheritance is consistent with `handoff_v4.md:10` and B's predecessor, line 14.
  - A pushed branch with no PR is not swept: `dd4413e5` has sat on origin since 19:41:07Z with no PR. No deploy or recurrence workflow creates PRs, and juniper-ml's `ci.yml` has no topic-branch push trigger.
- **Session layout:** the tools hard-code the worktree at `freeze_round.py:48`, `open_pinned_pr.py:73` and `placeholder_census.py:38`, and the guard's refusals are real (I hit one).
- **Lane B's "What moved" 1–8** all check out:
  - Recurrence has one commit (#186) touching `juniper-recurrence/CHANGELOG.md`.
  - Deploy has #230/#231/#232, touching `CHANGELOG.md`, `docker-compose.yml` and a non-uploaded `values.yaml`.
  - The 2c and addendum paths are unmoved (18 commits at `6c23fdde`).
  - There are six canopy merges after 04:43:49Z, with PR numbers and SHAs matching.
  - #2069, #2082 and #2087 landed at the stated times.
  - data v0.16.0 was released at 08:52:14Z, and the probe docstring's 45/46 note is at lines 48–50.
- **Delta route:** both PRs follow `S/main/PLAN.md` step 2. `docker-compose.yml` merges cleanly: main's hunks are at lines 161–520 and 1228, 2b's at 623. The stale subnet test would not false-fail on the merged compose, because it iterates only its four named networks.
- **Worried-about duplicate `### Fixed` heading after theirs-then-ours:** not established. Zealous `merge-file` likely factors the shared heading out of the conflict.
- **Freeze and git state:**
  - The r15 digest is `66742624…4a3171`, with 140 entries, `sha256sum -c` all OK, written 04:43:49Z.
  - The recurrence and deploy worktree statuses match the draft.
  - None of the four Y2 branches is on origin, and no PR exists.
  - The secret-leaks branch is absent, with no PR.
  - #2083 is `48fc09e5`, #684 is `f2147403`, data#438 is `0f0f7e0e`. #184 is OPEN (03:36:08Z), and cascor#690 is OPEN at `78e99414`.
- **Other checks:**
  - MEMORY.md measures 24,962 characters and 25,158 bytes.
  - Every cited tool exists.
  - The C1 branches have no commits beyond main, and none of those worktrees is in use.
  - canopy#368 is still open, so R15C M2 is not overtaken.
  - All the A6 table commits are local-only (GitHub 422), so they have no remote or `refs/pull` holder.
  - "Delete none" errs only toward keeping things, which costs nothing.
- **Prioritisation:** no harmful ordering. The lanes run in separate sessions, and the 09-29 lapse only lets others start work; it destroys nothing.

## Could not check
- Tools not on my safe list: `e2e_finding_triage.py` counts, `cascor_freeze_tell.py` exit code, `secret_shape_check.py`, the census, `check_open_pinned_pr`. Test suites were not allowed.
- An executed `already_merged` or `git merge-file` run for finding 6, which would need scratch files.
- Whether the sweeper can exclude PRs, and its cadence.
- The code line numbers in A1–A5.
- The ListAgents name of `bc31e993`.
- Other hosts' clones.
- Whether the tokens were rotated.

## Housekeeping
- **sha256** at start and at end: `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a`, which matches `r1/SHA256SUMS`.
- **I modified nothing.** No file was written.
  - Git commands were read-only, in this worktree and the canopy primary.
  - Against the recurrence and deploy worktrees I ran `git status --short`, `log -1` and `diff HEAD --stat`. `git status` may refresh the index stat cache (metadata only).
  - GitHub calls were GET or read-only GraphQL, and I ran the allowed reachability script.
  - The trio was touched only by `ss`, `ps` and `/proc` reads.
  - The guard refused one computed-argument `sed`.
- **PII disclosure:** one `grep` of canopy reflog files printed whole reflog lines, which include the git author's email address, to my local tool output only. It was not sent anywhere and is not repeated here. Later commands cut that field.
- No secrets or environment values were read or printed.
