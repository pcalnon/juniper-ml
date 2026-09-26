# R1-C — executability lane (round 1)

Archived verbatim from the lane's final message (2026-09-24). The only change is transport escaping: `&amp;`, `&lt;` and `&gt;` decoded.
Artifact reviewed: `r1/DRAFT_r1.md`, sha256 `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a`.

---

## Verdict

**SAFE AFTER FIXES.** Nearly every path, flag, count and state the draft (`DRAFT_r1.md`) asserts checks out against the repo. But one cleanup instruction, followed literally, deletes the last references to two commits the ledger cites. Four gaps block or mislead a successor at its first steps.

## Findings

**1. CRITICAL: the A9 cleanup destroys the only holders of `26bf27b3` and `96e7b105`, and A6 misstates what protects them.**
- **Location:** A9, "**canopy, now eligible except where A6's table holds a branch:** … `…fix--idle-cuts-round3-wording--20260923-2238--e9053227`: #684 merged. Local head `135c2782`, clean." And A6, "They are still in the object store, but no branch holds them, so a `git gc` prune can delete them."
- **If followed literally:** that branch is absent from A6's table, so the worktree reads as eligible now. Canopy's `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md:177-195` removes the worktree and then runs `branch -d`/`-D`. Those two steps delete the only references to `26bf27b3` and `96e7b105` (ledger item 13) and to `135c2782`, and a later `git gc` can prune them.
- **Evidence (reflogs):** in canopy's `.git`, `26bf27b3`/`96e7b105` appear only in `logs/refs/heads/fix/idle-cuts-round3-wording:10-12` and that worktree's `logs/HEAD:11-15`. `78c057e2` appears only in `logs/refs/heads/perf/idle-dispatch-cuts-v2:3-4` and that worktree's `logs/HEAD:4-5`.
- **Evidence (gc):** `git config --get-regexp '^gc'` is empty, so the defaults hold: a reflog keeps an unreachable commit for 30 days, and prune waits 2 weeks. A `gc` run today would not delete them; the cleanup would.
- **Evidence (the tool itself):** the draft's own tool prints `canopy 135c2782 BRANCH-ONLY … held by refs/heads/fix/idle-cuts-round3-wording`, yet the table omits that branch. A's predecessor's item 8 (`HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md`) already scheduled this exact cleanup.
- **Fix (A6 text):** replace the sentence with: "No branch holds them; only reflogs do. `26bf27b3` and `96e7b105` are in the reflogs of canopy `fix/idle-cuts-round3-wording` and its worktree's HEAD; `78c057e2` is in those of `perf/idle-dispatch-cuts-v2`. Removing either worktree or deleting either branch drops that protection, and a later `git gc` can then prune them; a `gc` run while the reflogs exist cannot."
- **Fix (A6 table):** add the row `| canopy | fix/idle-cuts-round3-wording | reflog-only: 26bf27b3, 96e7b105; head 135c2782 (cited by a handoff) |`, and append "; reflog-only: `78c057e2`" to the `idle-dispatch-cuts-v2` row.
- **Fix (A9):** change the lead-in to "canopy, eligible once A6 is answered, except where A6's table holds a branch:".

**2. MAJOR: the handoff file and the reachability tool are not reachable from either session the draft prescribes.**
- **Location:** the Goal statement, "juniper-ml `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`. Read it in full." Also the Verification line `python3 util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py`, and Git state, "No PR has been opened."
- **If followed literally:**
  - **Lane B** is told to start in `idempotent-jumping-sparkle`, whose HEAD is `5ea8e273`. It will never have the file, even after a merge.
  - **Lane A** is told to use a fresh worktree cut from `main`. It lacks both the file and the tool until a PR merges.
- **Evidence:** `ls` in `idempotent-jumping-sparkle` reports "cannot access" for the handoff, the reachability tool and `2026-09-24_secret_shape_check.py`. In `bubbly-meandering-pie` all three are `??` (untracked), and `git ls-tree origin/main util/ad-hoc/` has no reachability tool.
- **Fix:** add to the Goal statement: "If it is not in your checkout, Read `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md`. A Lane B session never has it in its tree." To Verification add: "Before this handoff's PR merges, copy the reachability tool into your own `util/ad-hoc/` first; it runs git in the checkout it sits in."

**3. MAJOR: C6 and the Goal statement assert a primary state that was already false when the draft was written.**
- **Location:** Goal statement, "a primary fast-forward that a live stack blocks"; C6, "fast-forward the canopy, cascor and data primaries once nothing holds them."
- **If followed literally:** the successor waits on the trio to fast-forward two primaries that are already at `main`. It also keeps treating the trio as a frozen fixture (A4, X4).
- **Evidence:**
  - canopy reflog: `7ab994e5 HEAD@{2026-09-24 19:39:45 +0000}: pull --tags origin main: Fast-forward`.
  - cascor reflog: `7f4a721 … 19:39:46 +0000`, which is cascor `main` (`7f4a7213`, #688). Canopy's HEAD `7ab994e5` equals canopy `main`.
  - The data primary is `[behind 1]`: `1afc348` against `main` `0f0f7e0e` (#438).
  - Both pulls came before C's predecessor merged at 19:42:44Z (`HANDOFF_2026-09-24_canopy-selection-cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md` says "The primaries are not pulled") and before the draft's 20:25–20:45Z window.
  - `cascor_freeze_tell.py` still exits 1 with the same five holders, so the pulls happened while the freeze was in force.
- **Fix (C6):** "canopy and cascor were already fast-forwarded at 19:39:45–46Z (`pull --tags origin main`, actor unknown) while the trio held them. Only data is behind: `1afc348`, one commit short of `0f0f7e0e` (#438). The trio's cascor (pid 2857489) and canopy (pid 2858037) run code loaded before those pulls, over newer files, so treat A4's reads of `:8202` as a mixed-version fixture."
- **Fix (Goal statement):** "…the data primary's one-commit fast-forward, which a live stack blocks…".

**4. MAJOR: A2 gives no way to create a branch without opening a PR.**
- **Location:** A2 Mechanics, "Push it in its own signed commit (`util/push_signed_commit.py`)." and "`open_signed_pr.py` uploads whole files, so rebase onto the live `main` immediately before it runs."
- **The tools:** `push_signed_commit.py:2` says "Add ONE GitHub-signed commit to an EXISTING branch", and `:22-24` says `open_signed_pr.py` "deliberately REFUSES a branch that already exists". `open_signed_pr.py:192-213` requires `--title` and `--body-file`, with no draft or no-PR mode.
- **If followed literally:** the only route the text leaves is `open_signed_pr.py` first. That puts a PR up before the 791 KB ledger lands and before validation, and the sweeper can merge a partial Phase 10. That breaks the draft's own "Validate BEFORE opening a PR".
- **Evidence:** #2083's 12 signed uploads landed 10:39:35–10:41:29Z, and its PR was created at 10:43:28Z. The driver used was `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py`, whose usage is `gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/<branch> -f sha=<full base sha>` followed by `… --base <sha> --branch <branch>`.
- **Fix:** "Land it as Phase 9 did. Validate on local frozen commits. Create the branch without a PR (`gh api -X POST repos/pcalnon/juniper-ml/git/refs -f ref=refs/heads/<branch> -f sha=<full live main sha>`). Upload with `util/ad-hoc/2026-09-24_push_phase9_signed_groups.py --base <that sha> --branch <branch>`; it sends the ledger alone and last. Only then open the PR, with `gh pr create --head <branch>`. Never use `open_signed_pr.py` here."

**5. MINOR: the "any lane" verification misleads in Lane B's session.**
- **Location:** "# From a juniper-ml checkout (any lane)".
- **If followed literally:** `e2e_finding_triage.py` reads `notes/…EVIDENCE.md` relative to the current directory (`DEFAULT_NOTE` at `:33`). In `idempotent-jumping-sparkle` that is the 602,764-byte pre-Phase-9 ledger, which has no F-CANOPY-055…059, so the counts differ and there is no P0. Two of the tools do not exist there.
- **Fix:** "(Lane A/C: a checkout at or after `48fc09e5`. In the Lane B session run only the `gh`/`ss`/`wc` lines.)"

**6. MINOR: the wrapper A1 names refuses to run as-is.**
- **Location:** "Use a wrapper that refuses the defaults, such as `util/ad-hoc/2026-09-23_a_n2_stack.bash`."
- **Evidence:** it hard-codes `SCRATCH=/tmp/claude-1000/…/317c1df2-…/scratchpad`, and all three `a-n2-eco/juniper-*` symlinks there dangle; their `…verify--a-n2-loop--20260923-1415--…` worktrees were removed in W5. It exits 2 with "does not resolve". That failure is safe, but it leaves no usable wrapper.
- **Fix:** "…is the pattern (hard-set ports, forbidden ports, protected pids, a recorded-pid `--down`), not runnable as-is. Copy it with your own scratch dir, fresh detached data and cascor worktrees at `origin/main`, and the fix's canopy worktree."

**7. MINOR: a `cd` in Lane B's verification leaks the working directory.**
- **Location:** "cd …/session-state/r15 && sha256sum -c --quiet SHA256SUMS && sha256sum SHA256SUMS".
- **If followed literally:** the session keeps its working directory between calls, so the unittest, census and check lines then run inside `r15` and fail. B's predecessor (`HANDOFF_2026-09-24_y2-wave2-round-15-fix-pass.md:145`) used a subshell; the rewrite to literal paths dropped the parentheses.
- **Fix:** follow the line with `cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle`, or move it to the end of the block.

**8. MINOR: "deleted from every clone" is broader than the source.**
- **Location:** B2, "must be deleted from every clone before a suite runs."
- **If followed literally:** it covers the owner's juniper-deploy primary and the 2b worktree. `git ls-files` lists `.env.secrets.enc` in both, and the 2b worktree's uncommitted state is the only copy (X5).
- **Evidence:** `R15B.md:5` says "I deleted it from my clones"; the memory note `reference_deploy_tracks_env_secrets_enc.md` says "in a scratch clone".
- **Fix:** "…deleted from each scratch clone a lane rebuilds, before the full deploy suite runs there. Never from the juniper-deploy primary or the 2b worktree."

**9. MINOR: a pinned re-probe will now print 45/46, not 46/46.**
- **Location:** "re-probe 46/46 at the pins" in the freeze evidence, and move 7.
- **Evidence:** the shared juniper-data checkout already has tag `v0.16.0`, which contains #421's merge commit `68c3cd7c` (`git tag --contains 68c3cd7c` → `v0.16.0`). The probe's docstring (`:48-50`) says that tag makes the pinned run print 45/46. `S/main/handoff_v4.md` still says "46/46 at the pins".
- **Fix:** add to move 7: "The tag is already present locally, so expect 45/46, with `6 packaging (release)` BROKEN. Update `handoff_v4.md` and the addendum row."

**10. MINOR: "the newest selection-arc handoff" is ambiguous.**
- **Location:** move 5, "Point the addendum at the newest one at open time.", and B4.
- **Evidence:** this handoff's filename does not contain `canopy-selection`, so the "list the canopy-selection handoffs" step that R15C M1 asks for would miss it. By that listing, #2087's (`c32e5f2a`) is the newest on `main`.
- **Fix:** "The newest is this combined handoff once its PR merges; until then it is #2087's `…cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md`. The listing must also match `canopy-combined`."

**11. MINOR: A2(b) gives the wrong source for O9.**
- **Location:** "The source is `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md` … lines 188–226".
- **Evidence:** those lines hold O1–O8, and the README has no O9 anywhere. O9 is at line 80 of `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`.
- **Fix:** add "O9 is recorded in `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`, line 80."

**12. NIT: A3's and A5's line numbers have drifted.**
- At canopy `7ab994e5`, `main.py:2985` is `_require_service_adapter`'s docstring. The proxy route's "Start a read-only replay session" is at `:2998`.
- "Self-healing, bounded to one cycle" is at `dashboard_manager.py:4736`, not `:4698-4701`.
- At cascor `7f4a7213`, `start_replay`'s `_load_snapshot_to_network` call is at `manager.py:6351` (not `:5977`), and `_auto_snap_best: bool = False` is at `:1526` (not `:1472`). `:5734` is a docstring line.
- **Fix:** add "(the ledger's line numbers; locate by symbol or quote)".

**13. NIT: B3 drops PLAN.md's precondition for the pull.**
- **Location:** "After 2a, `git pull --ff-only` the shared … checkout."
- `S/main/PLAN.md:177-179` says to "confirm it is clean and on `main`" first. It is clean and on `main` today.
- **Fix:** add that clause.

**14. NIT: the A8 link-set tool needs a file argument.**
- `2026-09-12_memory_index_linkset.py` requires `snapshot <file>` and `compare <file>` (`:23-24`, `:61`, `:67`).
- **Fix:** "`… snapshot <scratch>/before.txt`, then `… compare <scratch>/before.txt`".

**15. NIT: the guard's refusal list varies by session.**
- In this session, a `for` loop, a `jq` string containing `#`, `echo "exit=$?"` and the brace expansion in C1 all ran unrefused.
- A `sed` whose argument came from `$(find …)` was refused.
- **Fix:** "The refusals vary by session. Arguments computed by command substitution are refused reliably."

**16. NIT: the steps in the Goal statement are out of order.**
- Step 1 ("Run the verification block") includes a Lane-B-only half that assumes step 3 ("Choose lanes") has happened.
- **Fix:** swap steps 1 and 3.

**17. NIT: B2's freeze command leaves its inputs unstated.**
- `--addendum` resolves under `S/main/` (`freeze_round.py:116`, `:166-167`).
- The spliced 09-08 handoff is copied from the Lane B worktree (`:168`).
- `S/fix16/logs16` must already exist (`copytree` at `:176`).
- `S` must be spelled out. A literal `S` fails harmlessly at `:125`.
- **Fix:** "(Spell `S` out. Write `addendum_v14.md` in `S/main/` and splice it into the worktree's 09-08 handoff. Put the fix pass's logs in `S/fix16/logs16/` first.)"

## First five actions per lane

**Lane A** (fresh juniper-ml worktree from `main`)
1. Open the handoff at the Goal statement's path. **STUCK** (finding 2).
2. Run the verification block. **PASS except one line.**
   - These match the draft: triage 70/48/1/2/19 (P0 1, P1 6, P2 12); #2083 MERGED at `48fc09e5…`; canopy#684 MERGED at `f2147403…`; "0 failed"; `[]` for the secret-leaks branch; data `v0.16.0` Latest; `exit=1` from the freeze tell; the `ss` pids (2856834/:8101, 2858037/:8051, 2857489/:8202); MEMORY.md at 24,962 characters; both `compare` lists; #184 OPEN at 03:36:08Z.
   - The reachability tool is missing in a main-cut worktree. Run from `bubbly-meandering-pie`, it gave the stated three UNREACHABLE commits.
   - `main` has since moved to `c061a99f` (#2086), which touches no lane path.
3. Ask the owner questions. **PASS**, but A6's question rests on the wrong mechanism (finding 1).
4. A1, the F-059 fix, in a new canopy worktree at `7ab994e5`. **PASS**: `replay_player_panel.py:530-534` holds the `range_value` readout, and `test_p2_wave_batch_a.py:179-190` claims "The exact shape measured…" while typing `"range": [3, 37]`.
5. A1's drive on a writable cascor. **STUCK** (finding 6). Phase 10 would also stall at finding 4.

**Lane B** (session in `idempotent-jumping-sparkle`)
1. Open the handoff. **STUCK** (finding 2).
2. Run the verification. **PARTIAL.**
   - The any-lane half misleads (finding 5).
   - The digest check passes: `66742624…4a3171`, 140 entries, mtime 04:43:49Z. It then strands the working directory (finding 7).
   - I re-derived the census by counting tokens: 2c 6/4, 2a 4/0, 2b 0/0, addendum 3.
   - The `BASES.txt` recipe shows the live 2a and 2b diffs byte-identical to `r15/2a_recurrence.diff` and `r15/2b_deploy.diff`.
3. Read `S/main/PLAN.md`. **PASS.** Every flag it names exists (`open_pinned_pr.py:283-292`; `main`'s `safe_merge.py:1153-1175`). The three `ML =` hard-codes are at the cited lines. The worktree uploader equals `main`'s blob `5563ce07`.
4. B1, the fix pass. **PASS with friction.**
   - Recurrence `db41e77e` and deploy `7ff6ff32` moved exactly the stated paths.
   - 2c's and the addendum's 12 paths are unmoved since `f9c81d80`, also at `c061a99f`.
   - Both worktrees match the draft's description.
   - The CHANGELOG resolver is not in this tree, so it must run from another checkout by path.
   - `already_merged` re-merges with `git merge-file`, so R15D MINOR 1 really is on the critical path.
5. B2, the re-freeze. **PASS with friction** (finding 17). X1's reading of `R15D.md:39-43` is accurate: that fix does not say "use drafts".

**Lane C**
1. Ask about C2, C3 and C4. **PASS**: the Y7 note is in §4.3 of the reachability design (`:220-244`), and #437/#438 are on data `main`.
2. C1's in-use probe, run verbatim with its brace expansion. **PASS**: all four "free", and the guard did not refuse it.
3. C1's content probe. **Exists on `main`, not run.** It is absent from Lane B's tree.
4. C1's owner block. **PASS**: each branch name matches its worktree's `HEAD` ref. `origin/main..<branch>` is empty for jazzy, bright, tender and enumerated, so `branch -D` loses no commit.
5. C6. **MISLED** (finding 3).

## Could not check
- The ListAgents name `defect reg [042116]`, and whether a second session also named "defect reg" exists: no ListAgents tool in this lane.
- Any git in `idempotent-jumping-sparkle` (its `git status`, the 2c and addendum ties): forbidden by rule 4.
- The 193-test launcher suites, `check_open_pinned_pr.py` and `placeholder_census.py`: not run (rules 1 and 5). I substituted as described above.
- Whether `git -C` into a sibling worktree is refused: not tested. The refusal message I did get names that rule.
- Whether R15D MINOR 1's CHANGELOG conflict actually fires after the three-way merge: that needs a scratch merge, which would be a write.
- Whether `135c2782`'s tree equals #684's head `dfb7ac0b`: that commit is not in the local object store, and fetching is not allowed.

## Housekeeping
- **Artifact hash:** sha256 `8c2fa29042da0c6f0168ad551a7d2009217a520b86a9c16ee21aa58eaf61898a` at start and at end, unchanged. The untracked `prompts/…/HANDOFF_2026-09-24_canopy-combined-…md` is byte-identical to it.
- **Nothing modified.** My own worktree's `git status` at the end still shows exactly the three original `??` entries. Git in other repos was read-only, with `--no-optional-locks` for `status`. No processes were touched; the trio was observed only through `ss` and `ps` (pid, start time, command name).
- **Disclosures:**
  - I passed juniper-deploy's tracked `.env.example` (part of 2b's upload set) through `grep -c` and `git diff … | cmp`. The only output was a count (0) and "equal".
  - `.env.secrets.enc` was only `stat`-ed and listed with `git ls-files`, never read.
  - `git hash-object` (without `-w`) read the Lane B worktree's `util/open_signed_pr.py` by path from my own worktree.
  - No secret, environment value or email address was printed.
- **Documents referenced:** `DRAFT_r1.md`; `S/main/PLAN.md`, `S/main/handoff_v4.md`, `R15D.md`, `R15B.md`, `lane_R15B.md`; `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`; `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md`; the three predecessor handoffs; `HANDOFF_2026-09-24_canopy-selection-four-rulings-shipped-cleanup-and-carry-forwards-remain.md`; the A-N2 `README.md`; canopy's `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`; memory notes `reference_deploy_tracks_env_secrets_enc.md` and `feedback_memory_index_target_is_20kb.md`.
- **Changed:** none.
