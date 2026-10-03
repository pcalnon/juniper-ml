# HANDOFF 2026-10-03 — dynamic-workflow harness design (CONSOLIDATED): v3 sits UNTRACKED in one worktree, round 2 never relaunched, no PR

> **UPDATE 2026-10-03 — item 0 is DONE.** At the owner's request, the six files went to `main` as v3, still DRAFT. They are byte-for-byte except for two lint fixes CI required. The grounding-inventories record's three site-relative `/docs/en/` links now point at `https://code.claude.com/docs/en/`, and the round-2 record ends with one newline instead of two. They arrived in the signed PR that also added this note. Search `gh pr list --search "dynamic-workflow harness v3"` for the PR, and see the git log of the six paths. The files are therefore no longer a sole copy.
>
> What changes for the rest of this file:
>
> - Rounds 2 and 3, the v4 fold and the gates (items 1–3) now edit the files **on `main`**, from a fresh branch. They no longer work from the untracked copies in `structured-inventing-fairy`.
> - Item 4's PR becomes a v4 **update** PR, not the PR that adds the files.
> - The worktree copies are now redundant. Leave them in place until the next session confirms that `main` holds the same content (`cmp` per file; the two lint-fixed files differ only as described above).
> - Nothing else below has changed.

**Consolidated sources**:

- `HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md` — self-declared "**Written without verification** at the owner's request; every fact below is as the predecessor left it, not re-probed." It is the arc's first handoff, so it has no predecessor. It reached `main` via juniper-ml#2090, merged 2026-09-25T02:02:04Z `[VERIFIED 2026-10-03: gh pr list]`.

**Supersedes**: the source above.
**Live probe**: 2026-10-03T08:34:45Z (UTC), from worktree `snappy-strolling-waterfall` after `git fetch origin`; `origin/main` = `afb02801`.

---

> ## SOLE-COPY RISK: read this before anything else
>
> The arc's whole work product exists in **one place only**: untracked, uncommitted files in worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy` (branch `worktree-structured-inventing-fairy` at `25b78f55`). It is **not** on `origin/main`, not on any remote branch, not in any PR, and not in any other checkout or worktree. `[VERIFIED 2026-10-03: git worktree list; ls; find over Juniper/ to depth 8; git ls-tree -r origin/main; git branch -a; gh pr list]`
>
> | File (in that worktree) | Size | mtime (CDT) |
> | --- | --- | --- |
> | `notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md` (v3) | 106,111 B | 09-23 01:24 |
> | `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md` | 176,175 B | 09-23 01:24 |
> | `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md` | 136,364 B | 09-23 01:10 |
> | `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-2-RECORD.md` (header only) | 2,627 B | 09-23 01:27 |
> | `util/ad-hoc/2026-09-22_rate_limit_record_probe.py` | 4,130 B | 09-22 20:42 |
> | `util/ad-hoc/2026-09-23_archive_subagent_reports.py` | 5,482 B | 09-23 00:35 |
>
> `git worktree remove`, any worktree sweep, `util/remove_stale_worktrees.bash` (never run it), or a `git clean` in that worktree destroys roughly 420 KB of design and validation records that cannot be regenerated without re-spending two consensus rounds of a limit-bound account. **`.claude/worktrees/` is hidden from sweeps that start from the repo root**, so a cleanup can drop it unseen. Until
> the PR lands, treat this worktree as **DO NOT SWEEP**. Getting these files committed (remaining item 0) comes before everything else. The verbatim validator reports could in principle be re-archived from the predecessor's transcripts (`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/bb39e9fe-5809-451e-aacc-ec9d703a5fe0/subagents/`, twelve `agent-*.jsonl` files, five dated
> 09-22 and seven dated 09-23) `[VERIFIED 2026-10-03: ls]`. The design text itself has no second copy, and memory notes say transcripts are kept for roughly 30 days, so that fallback starts expiring around 2026-10-22.

---

## Goal statement (paste as the new thread's first prompt)

Continue the dynamic-workflow harness design arc (juniper-ml). The design is a limit-paced, goal-driven agent dispatcher: a systemd timer runs a pure-code tick that launches one `claude -p "/juniper-cycle <plan>"` child per cycle. Secure the files, relaunch consensus round 2, apply it as v4, and open the design PR.

**Completed so far** (as of 2026-09-23; nothing has moved since):

- Design **v3** at `notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md`. Header verified: "Document Version: v3"; "Status: DRAFT — consensus round 1 complete … round 2 on the corrections pending; owner decisions D-1..D-12 (§10) open"; "Measured at: juniper-ml `25b78f55` (#2013); Claude Code `2.1.280`" `[VERIFIED 2026-10-03: head of file]`. Round 1 ran Lane A ×3 and Lane B ×2.
  Every finding was either applied or recorded: Appendix D maps Lane A (29 rows) and Appendix E maps Lane B (30 rows). The v3 changes are the controller (timer plus one `-p` child per cycle), worktrees created by code in the task's repo, and V3's B3 gate amended to a patch-id test (D-12). D-7 is retired. `[UNVERIFIED — from
  HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated]`
- `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md`: five reports (A1, A2, A3, B2, B1) plus Lane A and Lane B reconciliation sections `[VERIFIED 2026-10-03: grep "^## " headings]`. That the reports are verbatim copies is `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated]`.
- `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md`: Reports I1–I5 `[VERIFIED 2026-10-03: grep "^## " headings]`.
- `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-2-RECORD.md`: header only `[VERIFIED 2026-10-03: read; no "## Report" sections]`.
- Two scripts: `util/ad-hoc/2026-09-22_rate_limit_record_probe.py` and `util/ad-hoc/2026-09-23_archive_subagent_reports.py`. The archiver takes `--session-dir`, `--out`, repeatable `--agent <id>=<label>`, `--header-file` and `--dry-run`. It is idempotent by section label: a label that already heads a section is skipped `[VERIFIED 2026-10-03: archiver :30-31, :74-78, :98]`.
- Local gates passed on v3 and both records (structure check 0 problems, links resolve, fences even, the design's §6.2 script wrapped-parse OK, five phases declared and used) `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated]`.

**Remaining work** (ordered):

0. **Secure the sole copy** (agent-doable; no blocker). This runs before any agent launch. Open the PR as a draft or WIP **now** with the six files, using `util/open_signed_pr.py` (item 4's mechanics). Alternatively, if the owner prefers, push the files to a backup branch through the signed API path. Either way the content gets a remote copy. Then iterate v4 onto that branch. If the owner wants no
   PR until v4 exists, then at minimum copy the six files to a durable non-`/tmp` location the owner names. **Do not move or delete them from the worktree.** `[VERIFIED 2026-10-03: sole copy, see banner]`
1. **Relaunch round 2** (agent-doable; blocked only by account usage limits). Launch two `general-purpose` agents together, never more than three at once. They are read-only with respect to the repo and `~/.claude`, write scratch only under the session scratchpad, and the artifact stays frozen while they run. Both briefs are reproduced in full under *Context → Round-2 briefs* below. If a launch
   dies with `You've hit your session limit · resets HH:MM`, wait for the reset and `SendMessage` the **same** agent ids ("continue from where you stopped, deliver the FINAL REPORT"). Do not relaunch within the session. The predecessor's dead round-2 ids cannot be resumed from a new session. `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which
   was not validated]`
2. **Archive and reconcile** (agent-doable). Command: `python3 util/ad-hoc/2026-09-23_archive_subagent_reports.py --session-dir ~/.claude/projects/<slug>/<session-id> --out notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-2-RECORD.md --agent <id>="A — round 2 — execution" --agent <id>="B — round 2 — refutation of the corrections"`. **`[CHANGED SINCE HANDOFF: slug]`**
   The source said a worktree session's slug is `-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-<name>`. The predecessor's own worktree session transcript actually lives under the **main-repo** slug `-home-pcalnon-Development-python-Juniper-juniper-ml/bb39e9fe-…`. So `ls -d ~/.claude/projects/*/<session-id>` to find it rather than constructing it. Next, add a
   "Reconciliation" section that follows `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §5: re-derive every lone load-bearing finding by opening the artifact, and record dissent. Then apply all accepted findings **in one pass** as **v4**, with an **Appendix F** map. Update the design header (Version; Status → "DRAFT — rounds 1–2 applied; awaiting owner rulings
   D-1..D-12"), the design's §0 round table and §12: add a round-2 row plus the §7 minimum record of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (instruments, sample size, agents/entry points, iterations and what the last one changed, unresolved dissent, what the evidence cannot support). **Run round 3 only if round 2 changed a number, a disposition or an
   action** (`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4).
3. **Gates before un-drafting the PR** (agent-doable):
   - `python3 util/ad-hoc/2026-09-05_markdown_structure_check.py` on all four notes files and the handoff.
   - Relative links resolve, and the fence count is even.
   - §6.2 script wrapped-parse with `node --check`. The predecessor's checker lived in a dead scratchpad, so recreate it: regex-extract the ```javascript fence, wrap it as `async function run(args, agent, pipeline, parallel, log) { … }`, and turn `export const meta` into `const meta`. Node v24.13.1 and jq 1.8.1 are present `[VERIFIED 2026-10-03: --version]`.
   - `juniper-check-doc-links --exclude templates --exclude history --exclude legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude CHANGELOG.md --cross-repo skip` (binary under `/opt/miniforge3/envs/JuniperCascor1/bin/`).
   - `notes/` is exempt from markdownlint.
4. **Open the design PR** (agent-doable; merge is owner-gated). Run `util/open_signed_pr.py` from `origin/main`; local commits hang on signing. Args: `--repo juniper-ml --branch design/dynamic-workflow-harness --add <local>:<repo path>` for the six files, `--title "docs(design): dynamic-workflow harness — limit-paced, goal-driven agent dispatch (consensus rounds 1-2)"`, `--body-file <scratch>/body.md`.
   - **The branch must not already exist**: `open_signed_pr.py` refuses an existing branch, and `--append`, `--reuse` and `--expect-base` do not exist. If item 0 already opened that branch, later uploads need another path, e.g. a GraphQL `createCommitOnBranch` commit. `[VERIFIED 2026-10-03: grep open_signed_pr.py — find_open_pr at :175, called :251; no --append/--reuse/--expect-base]` `design/dynamic-workflow-harness` does not exist locally or on origin `[VERIFIED 2026-10-03: git branch -a]`.
   - The **handoff no longer needs uploading**. **`[CHANGED SINCE HANDOFF]`** It is already on main via #2090.
   - Body contents: summary; the twelve decisions D-1..D-12 as the ask; **name every document** (the design, three records, both scripts, plus the source handoff and this consolidated handoff as context); note that the seed branch `design/dynamic-workflow` (`27ea09a1`) is superseded by Appendix A and can be deleted after merge (owner's call); `## Requirements`: no JR id identified, and say so rather than invent one; end with the attribution lines in force.
   - **Do not merge; do not delete any branch.**
5. **After the PR** (agent-doable): rewrite memory `project_dynamic_workflow_harness_design_2026-09-23.md` and its `MEMORY.md` line. **`[CHANGED SINCE HANDOFF: memory is staler than the source says]`** The memory still records "**v2**" and "Ten owner decisions D-1..D-10", but the design is v3 with D-1..D-12 `[VERIFIED 2026-10-03: read memory file]`. Update both to the PR number and v4. Leave the worktree in place until the PR merges, then follow the cleanup procedure.
6. **Owner rulings D-1..D-12** (owner-gated; not agent work). D-10 is go/no-go after P0 measures tokens-per-percent (`k`), because the weekly window bounds throughput and `k` has never been measured (memory file); the source's Lane A brief asserts §0 of `JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md` states P0's exemption. `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md and memory, not validated]`

**Key context**: see the sections below. Do not re-derive the design facts listed there.

## Dependencies on other paths

- **None blocking.** The arc is self-contained in juniper-ml.
- **Soft, P1–P10 (all paths)**: they compete for the same account's 5-hour and weekly usage windows. Round 2 should launch when no other arc is mid-consensus-round, because the predecessor lost three round-1 validators and both round-2 validators to the 5-hour window.
- **Soft, P10 (ci-tools) and P9 (CI budget)**: §7.3 of `JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md` amends V3's B3 gate (`JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`, on main `[VERIFIED 2026-10-03: ls]`) with a patch-id test. It touches worktree-cleanup tooling, not CI. No conflict was found. Re-check if either path edits `util/open_signed_pr.py` or the worktree-cleanup scripts.

## Context the remaining work needs

**Round-2 briefs** (verbatim substance from the source; reproduce them fully when launching) `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated]`. **Every bare § number and "Appendix D/E" in both briefs (§0, §3.1, §4.1, §4.3, §5.1, §6.1, §6.2, §6.4, §6.5, §6.9, §7.3, §8.1, §8.2, §8.5, §9.2) refers to `JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md`.**

**Lane A — execute the corrections**:

1. Extract the ```javascript fence from §6.2, wrap it as `async function run(args, agent, pipeline, parallel, log) { … }` with `export const meta` changed to `const meta`, and `node --check` it. Run it under a stub runtime: stages get `(prev, item, index)`; a throw means null and skip; `parallel` gives null on failure. Three scenarios:
   - Execution task PASS plus 3×`refuted:false` reaches Maintain with `launched=3`.
   - Executor returns `decisions_raised`: Verify is short-circuited and Maintain gets `decision`.
   - `prompt:<path>` planning task: no executor, `prompt_validated:true`, one lens.

   List undefined identifiers. Judge whether §6.4's "⌈launched/2⌉+… concretely 2 of 3, or 1 of 1" is a computable rule.
2. Implement §8.1–§8.2 exactly as written, and list every invented detail. Fixtures:
   - (a) `u5=23.5 r5=4h, u7=41.2 r7=3d, k=100000`, tasks S,S,M,L, `m=1.2`, timer 600 s, 40 ticks with no owner consumption: find the first S/M dispatch tick.
   - (f) A 5-hour reset between ticks: is "`A_w := 0` then accrue only from `resets_at_old`" unambiguous?
   - (g) `u7=92, r7=26h` and `u7=100` must both give exit 3 `weekly_wall`.
   - (h) A stale odometer with a future fallback reset: is "that window is at its wall until then" computable?
   - (i) Spend > A gives floor 0.
3. Run the §7.3 patch-id test on six squash-merged branches: `git diff origin/main...<branch> | git patch-id --stable` vs `git show <mergeCommit> | git patch-id --stable`. Report pass/fail honestly. If merge-base drift breaks it, say what to compare instead (`<mergeCommit>^` as base). The branches, all **verified**:

   | PR | Branch | Merge commit |
   | --- | --- | --- |
   | #1854 | `analysis/soak-stratum-predictors-main` | `e075f440` |
   | #1113 | `arc/canopy-e2e-phase1-seg10` | `dccd564b` |
   | #1106 | `arc/canopy-e2e-phase1-seg9` | `4afaf5e6` |
   | #1459 | `chore/ad-hoc-ceiling-bump-opener` | `5194a925` |
   | #1110 | `chore/ad-hoc-signing-arc-status` | `afcd8498` |
   | #1792 | `chore/adhoc-changelog-reorder-tool` | `94e24934` |

   `[VERIFIED 2026-10-03: gh pr list; git branch -a]` All six branches exist **locally only, not on origin**, and seg10 is checked out in some worktree. A branch cleanup removes this test's evidence, so do not prune them before round 2.
4. `util/open_signed_pr.py`: the DUP-GUARD is keyed on branch name (`find_open_pr` at `:175`, called at `:251`); the base is resolved from the remote ref (`:83-84`); an existing branch is refused (`:276`); `--append`, `--reuse` and `--expect-base` do not exist.
5. `scripts/claude_interactive.bash:17` (`DEBUG="${TRUE}"`) and `:84` (`--dangerously-skip-permissions`) still hold at those lines `[VERIFIED 2026-10-03: sed -n]`; `claudey` symlink.
6. §5.1 merge rule on three synthetic session files: a stale re-render with lower % and older hash; a fresh one; a passed window.
7. Grep all tracked `notes/*.md` first-30-line Status lines for ` — (COMPLETE|SUPERSEDED) \d{4}-\d{2}-\d{2}$` (the design claims 0). Count `**Supersedes…**:` lines naming plausible ledger docs.
8. Appendix E rows 3, 5, 11, 13, 15 and 30 resolve to text that says what they claim. D-7's "retired" status is referenced nowhere else. §0 states P0's exemption. `~/.claude/juniper-dispatch/` paths are consistent across §3.1, §4.1, §6.1, §6.9 and §8.5.

**Output**: results per check with outputs; underspecified/broken list; demonstrated failures; instrument adequacy; cannot-verify.

**Lane B — refute the corrections**. Grant §2 and round 1; "the fix pass is the least trustworthy part"; the agent may fetch `code.claude.com/docs/en/<page>.md`.

1. The timer + `-p` child surface:
   - Does `-p` start a saved project workflow by name?
   - Is anything needed in bypass mode?
   - Does the child stay open with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`?
   - At a 429, do agents fail to null, and can `--resume` continue the *workflow* or only the turn (§8.2 step 7 assumes the former)?
   - Does any write from the briefs land in the main checkout?
   - Cross-session delivery direction for a bypass sender → bypass receiver (§9.2).
2. The heartbeat (§5.1):
   - Does a status line render with no project?
   - Does a `/loop` turn produce an API response with fresh `rate_limits`?
   - Do user CLAUDE.md and MEMORY.md still load?
   - Daily token cost vs "one small turn per 45 min".
   - Is it an 8th/9th concurrent session?
3. Code-created worktrees plus `dispatch-executor` without isolation: where a relative-path habit writes into the main checkout or tests the wrong tree; regression vs v2's isolation for juniper-ml tasks.
4. The docs-branch model (§6.5) across the first squash merge: conflicts; the docs screen and Sequence Safety on the reopened PR; who resets the branch; `one_pr_per_work_unit`; PR-storm lessons (`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`).
5. §4.3 case 2 vs case 3 liveness: is case 2 dead code, and can a human produce the suffix accidentally?
6. `VERIFY_PENDING` plus one refuter in the docs pilot: a single false refutation blocks a task, so what does the owner see?
7. Own-token debit vs account-wide `H_w`: construct the case where `A_w` exceeds true headroom after heavy owner use; post-reset front-loading; jitter for 5-hour resets.
8. Calibration resolution: what `k` range can a 250 K burst resolve, given the status line's decimal granularity (`23.5` observed)? Does D-10's threshold fall inside it?
9. Is "loses the `/workflows` live view" over- or under-claimed (stream-json subagent messages, `parent_tool_use_id`)?
10. Appendix E rows 2, 4, 14, 16, 19 and 27 vs the text.

**Output**: numbered refutations with severity/quote/scenario/evidence/repair; corrections that hold (≤12 lines); new risks; cannot-judge.

**`[CHANGED SINCE HANDOFF: Claude Code is 2.1.288, not 2.1.280]`** `[VERIFIED 2026-10-03: claude --version]` Lane B's CLI-surface questions (items 1, 2 and 9) must be answered against the installed version and current docs. Keep "Measured at: 25b78f55 … 2.1.280" in the design as the measurement instant, and add a note if a round-2 finding depends on a version difference. `main` is 74 commits past
`25b78f55` `[VERIFIED 2026-10-03: git rev-list --count]`; that commit is the measurement instant, not the PR base.

**Traps the predecessor hit** `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated; corroborated by memory project_dynamic_workflow_harness_design_2026-09-23.md]`:

- The account is limit-bound. The 5-hour window killed three round-1 validators and both round-2 validators within a minute of launch, and the weekly window was exhausted on 2026-09-22. Launch ≤3 agents at once, and resume rather than relaunch within a session.
- Freeze the design while a lane runs. Apply all findings in one pass with a finding→resolution map, so the next round can be briefed on the corrections alone.
- Archive reports by copying them from transcripts (the archiver script), never by re-emitting them.
- The worktree isolation shim refuses compound shell: heredocs, `$(…)` feeding a command, `awk`, and loops or `jq` string templates around `gh`/`git` (the last two re-observed 2026-10-03). Put such commands in a scratchpad script and run that. Heredocs that only touch `~/.claude` were allowed, which matters for the memory update in item 5.
- `util/ad-hoc/2026-09-05_markdown_structure_check.py` is the single-file structure gate. `util/markdown_structure_delta.py` needs a base/head and cannot see untracked files.

**Design facts not to re-derive wrongly** (from the source and memory) `[UNVERIFIED — from HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md, which was not validated]`, except the `:84` item, which is verified:

- `quotaLimits` sits at the transcript line's **root**, as a sibling of `message`.
- Transcript records lag a limit hit by **hours**, so a transcript scan never proves "no hit".
- A self-paced `/loop` is **not** restored on `--resume`.
- `autoContinueAtUsageLimit` in a project/local settings file turns auto-continue **off**.
- `isolation: worktree` is single-repo.
- V3's B1/B3 refuse squash merges 6/6.
- **Six** CI tests pin agents and skills to opus+max.
- Every `claudey` session runs with `--dangerously-skip-permissions` (verified at `:84`).
- Agent teams ON makes any named subagent a teammate, so keep `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` unset for dispatch.
- Before a design claims a count from a probe, make the probe print record **dates**.

**Documents of record**: the four design and record notes, both in the worktree (see banner). Companions on main `[VERIFIED 2026-10-03: ls]`:

- `notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`
- `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
- `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`
- `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` §20

The seed is on branch `design/dynamic-workflow` at `27ea09a1` (local and origin; one file, `notes/dynamic_workflow_design.out`, 15 lines) `[VERIFIED 2026-10-03: git show --stat]`.

## Verification commands

```bash
W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy
git worktree list | grep structured-inventing-fairy        # expect 25b78f55 [worktree-structured-inventing-fairy]
ls -la $W/notes/JUNIPER_2026-09-2[23]_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-*.md   # expect 4 files, sizes as in the banner
ls -la $W/util/ad-hoc/2026-09-22_rate_limit_record_probe.py $W/util/ad-hoc/2026-09-23_archive_subagent_reports.py
git fetch -q origin && git ls-tree -r --name-only origin/main | grep -c DYNAMIC-WORKFLOW-HARNESS   # expect 0 until the PR merges
git branch -a | grep -E 'dynamic-workflow'                  # expect design/dynamic-workflow (+ origin) and remotes/origin/docs/handoff-dynamic-workflow-harness-round-2 (#2090's head); no design/dynamic-workflow-harness yet
gh pr list -R pcalnon/juniper-ml --state all --search "dynamic-workflow harness in:title"   # expect only #2090 (the handoff)
python3 util/ad-hoc/2026-09-05_markdown_structure_check.py $W/notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md
ls -d ~/.claude/projects/*/bb39e9fe-5809-451e-aacc-ec9d703a5fe0   # predecessor transcripts (main-repo slug)
claude --version                                            # 2.1.288 at 2026-10-03
```

In a worktree-isolated session, run `git` in your own worktree only. Read the `structured-inventing-fairy` files with `ls`/`cat`, not `git -C`.

## Dispositioned / closed items

| Item | Source | Disposition | Evidence |
| --- | --- | --- | --- |
| Upload "this handoff" with the PR | HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md item 4 | **Moot**: the handoff is already on main | #2090 merged 2026-09-25T02:02:04Z `[VERIFIED 2026-10-03]` |
| Predecessor's dead round-2 agent ids | HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md item 1 | **Moot**: cannot be resumed from a new session; relaunch fresh | source statement; no round-2 reports in record `[VERIFIED 2026-10-03: read record]` |
| `util/ad-hoc/2026-09-22_archive_consensus_reports.py` (untracked-looking in the worktree, not in the source's list) | live probe | **Already on main**, byte-identical; not part of the PR | `diff -q` vs `git show origin/main:…` `[VERIFIED 2026-10-03]` |
| Branch `worktree-dynamic-orbiting-seal` | live probe | **Unrelated** (`9d2cf6fb` API primer); not this arc | `git log -1` `[VERIFIED 2026-10-03]` |
| Possible later pickup of this arc by another session | live probe | **None found**: no transcript after 2026-09-25 03:00 mentions the design file except this session's | grep over `~/.claude/projects/*/*.jsonl` `[VERIFIED 2026-10-03]` |
| Predecessor snippet checker in scratchpad | HANDOFF_2026-09-24_dynamic-workflow-harness-design-round-2-relaunch-and-pr.md key context | **Lost**; recreate (item 3) | source statement |

## Git state

As probed 2026-10-03T08:34Z:

- Worktree `structured-inventing-fairy`: branch `worktree-structured-inventing-fairy` at `25b78f55`. It holds the six untracked files listed in the banner, plus `util/ad-hoc/2026-09-22_archive_consensus_reports.py` (identical to main) and a copy of the 09-24 handoff (on main via #2090). Running `git status` was not possible from this isolated session, and file content was inferred via
  `ls`/`find`/`diff`, so the next thread should run `git status --short` there. Nothing was ever staged or committed per the source.
- `design/dynamic-workflow` at `27ea09a1`, local and origin: the seed, untouched.
- `origin/docs/handoff-dynamic-workflow-harness-round-2` at `5085cfba`: #2090's merged head. It is deletable by the owner; it is not this arc's design branch.
- `design/dynamic-workflow-harness`: does **not** exist (item 4 will create it).
- This consolidation: worktree `snappy-strolling-waterfall`, branch `docs/handoff-consolidation-2026-10-03`. It is uncommitted; the coordinator owns its commit.
