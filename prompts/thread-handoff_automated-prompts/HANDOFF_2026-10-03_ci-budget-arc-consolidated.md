# HANDOFF 2026-10-03 — CI-budget arc (CONSOLIDATED): ml#2035 merged before round 6 reported (round 6 was killed by a session limit); round 6 is a post-merge follow-up, and five owner decisions plus two non-owner items stay open

- **Consolidated sources**:
  - `HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`. Self-declared **Validation: none** ("The owner asked for a token-minimal handoff without a validation round").
  - Carried by reference, as the arc's document of record: `HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md` (below: "the 09-09 handoff"). Validated by consensus rounds 1-5 per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`; round 5 changed a NUMBER, so its corrections are **not** independently validated (round 6 never ran).
- **Supersedes**: `HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`. The 09-09 handoff stays the document of record (it is where round 6 must be recorded); it is not superseded.
- **Live probe**: 2026-10-03 08:35-08:55 UTC, juniper-ml `origin/main` at `afb02801`.
- **Sibling path**: P10, `HANDOFF_2026-10-03_ci-tools-reevaluation-consolidated.md`. No shared remaining work; shared merge mechanics only (see § Dependencies).

## Goal statement (paste as the new thread's first prompt)

```text
Continue the CI-budget arc in juniper-ml. Document of record:
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md
(read its § Re-evaluation 2026-09-22 and its FIRST §1 block). This consolidated handoff is
prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_ci-budget-arc-consolidated.md.

Completed so far:
- ml#2017 merged 2026-09-23 01:17 UTC (7b226ca0): re-evaluation, three budget raises (owner
  ruled SHIP), the reprobe script. [VERIFIED 2026-10-03: gh pr view]
- ml#2035 MERGED 2026-09-23 20:08 UTC as c2bcb96c, through the owner's auto-merge armed 13:23Z,
  after a merge-from-main commit 114fbc3d (head). It carries consensus rounds 3-5 and their fixes.
  The squash body holds all five commit messages, including a66a1b86's corrections of 3222064b's
  "held 14" and bdd60b20's "verbatim". 114fbc3d touched none of the PR's files.
  [CHANGED SINCE HANDOFF: the 09-24 handoff said OPEN/BEHIND at bf60a716 and listed the merge
  as remaining; VERIFIED 2026-10-03: gh pr view 2035, git diff bf60a716 114fbc3d]
- Rounds 1-5 lane reports archived in reports/2026-09-22_ci-budget-reeval-consensus/
  (round1-*..round5.md + README). [VERIFIED 2026-10-03: ls on main]
- The 09-24 handoff itself merged as ml#2091 (a4b0ff17). [VERIFIED 2026-10-03]

Remaining work (ordered):
1. CONSENSUS ROUND 6 -- agent-doable, not started. It was launched 2026-09-23 against bf60a716
   and killed by the session usage limit before reporting; its session (36979dd7) has ended, so
   it CANNOT be resumed with SendMessage. Launch ONE general-purpose reviewer, in the background,
   briefed on round 5's corrections ONLY: in the 09-09 handoff, "### Corrections from consensus
   round 5", the Validation record's Round 4 and Round 5 entries, and "Added for round 5".
   Freeze it at c2bcb96c (main's squash of ml#2035; same content as bf60a716 for every file
   named here). Both jobs: re-derive each claim with its own code, and hunt what the
   corrections broke. Cross-file agreement: the 09-09 handoff, util/safe_merge.py (the dissent
   comment above REPO_TIMEOUTS and the window comment), tests/test_safe_merge.py,
   reports/2026-09-22_ci-budget-reeval-consensus/README.md, the commit messages of 3222064b,
   bdd60b20 and a66a1b86 (now also inside c2bcb96c's squash message), and ml#2035's
   description. Read-only; its scripts go under
   util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round6/ in YOUR worktree; it must never
   run the archiver in place. Final line: "Round 6 changes a NUMBER / DISPOSITION / ACTION:
   yes -- <which>" or "... : no". If a session limit kills it, SendMessage to its agent id from
   the SAME session; do not relaunch.
   [UNVERIFIED — from HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md,
   which was not validated: the brief's content; the freeze point is re-derived here]
2. ARCHIVE round 6 as reports/2026-09-22_ci-budget-reeval-consensus/round6.md with a README
   row (Frozen at: main c2bcb96c, ml#2035's squash). Archiver trap in § Context. Agent-doable.
   [UNVERIFIED — from HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md,
   which was not validated]
3. RECORD round 6 in the 09-09 handoff, in a FOLLOW-UP PR (its own Round 6 line says "recorded
   here while ml#2035 is open, or in a follow-up PR if it has merged"): replace the
   "**Round 6** -- ..." line in § Validation record 2026-09-22. If round 6 changed a NUMBER,
   DISPOSITION or ACTION: add "### Corrections from consensus round 6", apply them, push, run
   round 7 the same way (§4 of
   notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md), add an
   "Added for round N" list. Optionally PATCH ml#2035's merged description, whose line 40 still
   reads "[ ] consensus round 6 ... in progress" [VERIFIED 2026-10-03: gh pr view --json body].
   New branch: util/open_signed_pr.py. Agent-doable.
4. MERGE the follow-up -- OWNER-GATED (approval in your session). The owner's sweeper may merge
   it unseen: validate the pushed branch BEFORE opening the PR.
5. OWNER DECISIONS 1-5 of the 09-09 handoff's first §1 block -- OWNER-GATED; surface them.
   (1) SLACK_WEBHOOK_URL on the eight siblings [VERIFIED 2026-10-03 for canopy, cascor
   and data: 0 SLACK secrets; juniper-ml has one; the other repos NOT RE-PROBED — 09-09
   handoff, validated rounds 1-5]. (2) Should budgets absorb runner queue? Three
   raises ruled SHIP 2026-09-22; general question open; FOUR budgets at TIMEOUT_CEILING 3300
   (data, canopy, cascor-client, data-client) [VERIFIED 2026-10-03: REPO_TIMEOUTS on main].
   (3) Promote "Markdown Structure (advisory soak)"? Evidence says NOT YET; still advisory
   [VERIFIED 2026-10-03: ci.yml:1661 name, final exit 0 at :1733]. If yes, later (09-09 §1,
   and the PROMOTION PATH comment in .github/workflows/ci.yml): NON-OWNER 1 first; deleting the
   final `exit 0` ALONE leaves a check that cannot fail -- replace it with `exit "$rc"`; add the
   job's name as a required context IN THE RULESET, never via the Quality Gate's `needs:`;
   decide whether rc 2 ("refused to report") and the EARLY `exit 0` on a failed diff fail; move
   the diff base to HEAD^1 (base.sha can lag the test-merge commit). (4) cascor-client back
   into the pin -- ruled OUT 2026-09-15; re-measure says it would now pass. (5) The 22 flood-2
   test PRs whose production half was absent: confirm abandoned deliberately, or reopen.
   [NOT RE-PROBED beyond the tags — from the 09-09 handoff, validated rounds 1-5]
6. NON-OWNER 1 -- agent-doable: stop util/ad-hoc/2026-09-05_md_structure_check.py failing
   correct edits (C4 renamed heading; C2 wrapped prose), with the binding ACCEPTANCE, corpus
   control (22 fences at ba035cc9) and replay in the 09-09 handoff's §1 block. Unchanged on
   main since #1955 [VERIFIED 2026-10-03: git log]. Then consensus-validate before offering
   promotion. Blocks OWNER 3's "yes" path.
7. NON-OWNER 2 -- agent-doable: re-measure every budget with
   util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py first-pass -n 30 (never raw v2). All OK
   -> dated line under § Re-evaluation 2026-09-22, in a PR, stop. Any BELOW HEALTHY MAX / ABOVE
   4x p90 -> do NOT re-pin while OWNER 2 is open; report repo, max PR and its queue share
   (laneB2/span_decompose.py <repo> <pr>). Already tripped once: ml's 2800 s read 80 s above
   4x p90 on 2026-09-23. [NOT RE-PROBED: figures decay; re-measure]
8. Informational: the lockfile App-token arm, verified on n = 1 (#1970) -- re-check.
   [VERIFIED 2026-10-03: ml#2106, authored by app/juniper-release-train, carried 30 checks and
   merged 2026-10-02]

Key context: § Context the remaining work needs of
HANDOFF_2026-10-03_ci-budget-arc-consolidated.md (merge mechanics, sandbox, checks, traps).
```

## Dependencies on other paths

- **P10** (`HANDOFF_2026-10-03_ci-tools-reevaluation-consolidated.md`): no shared work item. Both share the merge mechanics: the owner's sweeper ("Mine: fix forward", 2026-09-24), strict rulesets, signed commits only.
- **P6** (perf lane; its source `HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md`): ADJACENT, not dependent. P6 works the REQUIRED gate's engine `util/ad-hoc/2026-09-05_markdown_structure_check.py` / `util/markdown_structure_delta.py`; NON-OWNER 1 here is the ADVISORY soak's engine `util/ad-hoc/2026-09-05_md_structure_check.py`. Pairs that differ by one word — do not edit the wrong one.
- **P1** (backup arc) `[ALSO P1]`: the 09-09 handoff flags `notes/backup_tests_pre-and-post_reboot.md` (a shell script with a `.md` name and no `JUNIPER_<date>_` prefix) as the backup arc's, design `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. Still on main [VERIFIED 2026-10-03: git ls-tree]. Not this arc's to fix.

## Context the remaining work needs

**Owner rulings (quoted from the 09-09 handoff)**: "THE THREE RAISES ARE RULED: the owner approved shipping them on 2026-09-22, over a recorded dissent." OWNER 4: "Ruled OUT on 2026-09-15." The SHIP
ruling "covers the three raises only" — it does not settle OWNER 2. Both sides of OWNER 2 (HOLD / SHIP and the counter to each) are written out above `REPO_TIMEOUTS` in `util/safe_merge.py` and in the
09-09 handoff's §1 block; options there: keep raises and decide only the at-ceiling case; size on queue-free span; size on uncontended heads; raise the ceiling (risk above ~3600 s, the worker lease);
keep the auto-merge net armed on a timeout refusal. [NOT RE-PROBED — 09-09 handoff, validated rounds 1-5]

**Budgets on main** [VERIFIED 2026-10-03: ast-parsed `REPO_TIMEOUTS`]: ml 2800, data 3300, cascor 2800, cascor-worker 2400, canopy 3300, cascor-client 3300, data-client 3300, deploy 1400, recurrence 2000; `TIMEOUT_CEILING = 3300`. `util/safe_merge.py` unchanged since c2bcb96c.

**Archiver trap (round 6)** [UNVERIFIED — from `HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`, which was not validated]:
`util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round4-fix/archive_round_reports.py` reads ONE session's subagents directory, derived from the transcript path passed. Its LANES table maps rounds
1-5 to agents of session `36979dd7-9695-4932-8e7f-158acf63af9c`; round 6 will run in YOUR session. Give each lane its own session id, or archive round 6 in a separate invocation; never re-take rounds
1-5 from the wrong session. A session's transcript tree MOVES when it ends (from the worktree-suffixed project dir to `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/<uuid>/`),
so glob `~/.claude/projects/*/<uuid>*` and refuse unless exactly one matches. [VERIFIED 2026-10-03: 36979dd7's tree is now under the unsuffixed dir, 34 subagent files]

**The killed round-6 lane left scratch**: `.claude/worktrees/ancient-yawning-biscuit/util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round6/` holds 19 untracked scripts (c2_candidate.py,
c2_corpus.py, budget_history.py, verify_archive.py, …) written 2026-09-23 ~06:07-06:31 UTC, after bf60a716. Unreviewed agent code with no report: do not upload it; a new round-6 reviewer must not be
briefed with it. Its partial transcript may be among 36979dd7's subagent files (read-only). [VERIFIED 2026-10-03: ls]

**Sandbox** (worktree-isolated session) [VERIFIED 2026-10-03 in this session: compound git commands and loops over gh were refused]: refuses heredocs containing "git", `$(...)`, `<(...)`, `bash <file>`, `git -C <other repo>`, and loops running git or gh over a variable. Put non-trivial logic in a python script under `util/ad-hoc/` and run it with `python3`.

**Checks before each push** [UNVERIFIED — from `HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`, which was not validated]: tracked files `/opt/miniforge3/bin/pre-commit run --files <files>`; untracked Python (pre-commit `--files` skips it): flake8 and
bandit with `.pre-commit-config.yaml`'s args plus the cached `~/.cache/pre-commit/repof9pb13t8/py_env-python3/bin/isort --profile=black --line-length=512`; markdown `python3
util/ad-hoc/2026-09-05_markdown_structure_check.py <md>` and `python3 util/ad-hoc/2026-09-05_md_structure_check.py --base <PR head> <md>`; links `juniper-check-doc-links` with AGENTS.md's exclude list;
tests `python3 -m unittest tests/test_safe_merge.py tests/test_wait_for_checks.py` (124 OK on 2026-09-23).

**Pushing / merging** [NOT RE-PROBED — 09-09 handoff "MERGING IN THIS LANE", validated, except where tagged]: every commit GitHub-signed (local `git commit` hangs on the YubiKey; `PUT /contents` does not sign). New branch
`util/open_signed_pr.py` (refuses an existing branch); append `util/push_signed_commit.py` (promoted by ml#2036) or `util/ad-hoc/2026-09-08_push_signed_commit.py`, which uploads WHOLE files — confirm
main has not changed the file first. Payloads of more than 8 files may hit HTTP 499, so split commits [UNVERIFIED — from
`HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`, which was not validated]. Order, one PR at a time: `python3 util/safe_merge.py --repo juniper-ml --pr <N> --execute`
and read its MERGED line, not the exit status. Its refusal under contention DISARMS any net, so on refusal ARM native auto-merge first, `gh pr merge <N> --repo pcalnon/juniper-ml --squash --auto`,
then keep it synced with `python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo pcalnon/juniper-ml --pr <N> --max-syncs 4 --per-pr-timeout 3300`; the shepherd never merges and returns
NOT-ARMED on an unarmed PR. Never run `safe_merge --execute` on a PR the shepherd is shepherding. `--auto` on a MERGEABLE PR merges on the spot. Finish every commit before arming. The squash
message is built from COMMIT messages, not the PR body, so a correction to a commit-message claim needs a new commit message [UNVERIFIED — from
`HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md`, which was not validated]. `gh pr edit` is broken on gh 2.46; use `gh api -X PATCH repos/pcalnon/juniper-ml/pulls/<N> -F body=@<file>`, starting from the live body.

**The sweeper** [UNVERIFIED — from `HANDOFF_2026-09-24_ci-tools-reevaluation-all-nine-prs-merged-and-the-banner-still-says-three-are-open.md`, which was not validated]: owner ruling
2026-09-24, quoted, "Mine: fix forward". It readies, arms and merges open PRs as `pcalnon` with the default squash body. The ruling post-dates ml#2035's arming: an owner-armed auto-merge (enabled
2026-09-23 13:23Z, consistent with the sweeper) merged ml#2035 before round 6 reported. Validate the pushed branch before opening the PR.

**Measurement traps and tool pairs**: the 09-09 handoff's §1 "MEASUREMENT TRAPS THIS RE-EVALUATION PAID FOR" (v2 `filter=latest` inflation; dropping heads lowers max; a run LIST shows the latest
attempt; enumerate lockfile PRs by `--head`; job logs echo script text; a comma ends a workflow-command property; Slack-webhook repos leave no annotation; date-only `--since`; `pull_requests` empty
after merge; a 30-head window moves with every merge; stamp figures at enumeration time; queued jobs are in flight, not lost; a PR can merge while its round runs) and "USE THE RIGHT TOOL" (CI span:
`..._reprobe.py first-pass`, not v1/v2). Carried by reference because they are long and verbatim there; read them before NON-OWNER 2. [NOT RE-PROBED — validated rounds 1-5]

**What the evidence cannot support** (09-09 handoff § Validation record): budgets sized on a 30-head window staying valid; first-pass being *the* right statistic; SHIP settling OWNER 2; the soak's false-positive rate beyond five days / 62 PRs; the backtest's 2026-09-16 date; that no other residue was dropped.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your-worktree>
git fetch -q origin
gh pr view 2035 --repo pcalnon/juniper-ml --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'   # MERGED c2bcb96c
git log --oneline -3 origin/main -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md   # c2bcb96c on top unless round 6 has been recorded
grep -n '^\*\*Round 6\*\*' prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md   # still the placeholder line
git diff --stat c2bcb96c origin/main -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md util/safe_merge.py tests/test_safe_merge.py reports/2026-09-22_ci-budget-reeval-consensus util/ad-hoc/2026-09-22_ci-budget-reeval-consensus   # expect empty
ls reports/2026-09-22_ci-budget-reeval-consensus/   # no round6.md yet
gh pr list --repo pcalnon/juniper-ml --state open   # none open at 2026-10-03 08:50 UTC
ls -d ~/.claude/projects/*/36979dd7*                 # exactly one tree + one .jsonl
```

## Dispositioned / closed items

| Item | Source | Disposition | Evidence |
| --- | --- | --- | --- |
| Remaining 4: merge ml#2035 (owner approval, safe_merge / shepherd) | 09-24 handoff | **DONE** — merged by the owner's armed auto-merge before the handoff was written | `gh pr view 2035`: MERGED 2026-09-23 20:08Z, `c2bcb96c`; autoMerge enabled 13:23Z by pcalnon |
| "CI GREEN on bf60a716, merge state BEHIND, no main commit touched the PR's files" | 09-24 handoff | **MOOT** — merged; head became `114fbc3d` (merge from main), which changed none of the PR's files | `git diff --stat bf60a716 114fbc3d` empty for those paths |
| SendMessage-resume of the killed round-6 agent | 09-24 handoff | **MOOT** — its session 36979dd7 has ended | transcript tree moved to the unsuffixed project dir |
| Squash-message correctness (a66a1b86 corrects earlier commit-message claims) | 09-24 handoff | **DONE** — the squash body includes all five commit messages | ml#2035 `autoMergeRequest.commitBody` |
| Verify-starting-state block ("expect OPEN at bf60a716…") | 09-24 handoff | **SUPERSEDED** by § Verification commands above | — |
| 09-24 handoff's own PR | 09-24 handoff | **MERGED** ml#2091 `a4b0ff17` 2026-09-25 | `gh pr view 2091` |
| 09-09 §3 items 1-10 | 09-09 handoff | Closed / ruled / informational per its § Re-evaluation 2026-09-22; the residue is OWNER 1-5 and NON-OWNER 1-2 above | 09-09 handoff header banner |
| Planning-slack negative margins | 09-09 handoff | **INFORMATIONAL** — `docs/REFERENCE.md` "Memory-Budget Slack (Planning)" says not to start a relocation for it | 09-09 handoff §1 block |

## Git state

- juniper-ml `origin/main` at `afb02801`; no open juniper-ml PRs [VERIFIED 2026-10-03].
- PR branch `fix/ci-budget-arc-2026-09-23-round-3-follow-up`: merged as ml#2035; not needed further.
- Worktree `.claude/worktrees/ancient-yawning-biscuit` still exists, branch `worktree-ancient-yawning-biscuit` at `18d3d5e3` — an **UNSIGNED local-only commit: never push it** [VERIFIED 2026-10-03:
  `git worktree list`]. Its working tree holds ml#2017/ml#2035 content uncommitted (all merged), the stale `round2-laneA/r2a_spans.py` that predates the owner's CodeQL fix `6f17aea5` (never upload
  it), the untracked `round5-fix/compare_to_ref.py <ref> <paths...>` helper (compares local files, including untracked ones, to any ref), and the round-6 scratch above. Removal needs the owner's
  cleanup signal and the cleanup procedure (`worktree remove` deletes ignored files).
- Tracked lane scripts under `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/` on main: `laneA2/{span_all_attempts,queue_share}.py`, `laneB2/span_decompose.py`, `round2-laneA/{r2a_spans,r2a_common}.py`, `round3-fix/{check_first_pass_window,check_soak_in_flight}.py`, `round4-fix/archive_round_reports.py` [VERIFIED 2026-10-03: git ls-tree].
