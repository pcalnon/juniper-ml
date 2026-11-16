# Handoff: R-OBS-SC-2 follow-ups. The one-artifact publish fix is ported to all 7 repos and two release-train gaps (plus a third the reviews found) are fixed. 1 of 8 PRs merged; the rest have independent reviews applied or in progress. Merges, a template sweep and plan v1.15.17 remain

**Written**: 2026-11-15 23:40Z (`date -u`) by session `d67643b8`. Its ListAgents name is
`r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next`, ref `08ef3e`. Worktree
`.claude/worktrees/giggly-foraging-sunbeam`, branch `worktree-giggly-foraging-sunbeam`, at `edea2eb1`.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md` (juniper-ml#2591).

**Merge approval**: at this session's start the owner wrote "merge approval granted", with "continue work arc from
handoff: …". That approval is per-session and does not carry over. Ask again, naming the PRs below.

**Still running in session `08ef3e` at writing** (it may push to the PRs below after this handoff):
- four fix-up agents, for canopy#823, data#543, the trio, and ml#2593 (the last waits for #2592 to merge, runs
  `update-branch` on #2593 once, then pushes);
- `util/safe_merge.py` on ml#2592 (log `tmp/ports/merges/ml-2592.log` in this worktree).

Session `08ef3e` merges no other PR after this handoff; it merges only this handoff's own one-file PR. The next session
reads every PR's head from GitHub before acting.

**Git status** (this worktree, 23:40Z):
- Nothing is staged.
- The tracked edits equal juniper-ml#2592's files: `util/release_train/ceremony.py`,
  `tests/test_release_train_ceremony.py`, `CHANGELOG.md`, `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
  and the runbook. Discard them once #2592 merges and `main` is pulled.
- Untracked: the `util/ad-hoc/` scripts listed under Remaining work, item 4, and the gitignored `tmp/ports/`.

## PR state

Re-read each first: `gh pr view N --repo pcalnon/<repo> --json state,headRefOid,mergeStateStatus`.

| PR | head at writing | review | next |
|---|---|---|---|
| juniper-recurrence#236 | **MERGED** 23:07:44Z (`f34c69f4`) | done, fixes applied | none |
| juniper-ml#2592 (release-train monitor: `HALT_BUILD` and `build-failed`; drops `Publish Container Image` runs; latest-attempt order; `--branch <tag>`; the publisher's dispatch runs) | `fe230b5b` | 2 rounds (3 agents), all applied | merging; **must land before the 4 ports that add a build job** |
| juniper-ml#2593 (7 publishers) | `4c464160` | MAJOR and MINORs, fix-up queued after #2592 | re-verify, then merge |
| juniper-canopy#823 | `2c0e55b6` | fix-up running (test pins, install check outside the checkout, ladder) | re-verify, then merge |
| juniper-data#543 | `a77a30fe` | fix-up running | merge after #2592 |
| juniper-cascor-client#199 | `8bc8538b` | fix-up running | merge after #2592 |
| juniper-data-client#264 | `40166ab1` | fix-up running | merge after #2592 |
| juniper-cascor-worker#232 | `97933cb4` | fix-up running | merge after #2592; AGENTS.md date = push day |

**Re-verify every new head before merging:**
1. `python3 -I util/ad-hoc/2026-11-15_fetch_pr_files.py --repo R --ref <head> --out tmp/ports/verify/R --pr N`
2. `python3 -I util/ad-hoc/2026-11-15_publish_port_template_identity.py --template tmp/ports/clones/juniper-cascor/.github/workflows/publish.yml <workflows>`, which must PASS. It now also fails a job-level `continue-on-error`.
3. Green CI.
4. `python3 -I util/safe_merge.py --pr N --repo <bare> --execute`, in the background. Read its `MERGED` line: exit 0 is not proof.

ml#2593 carries `Allow-Symbol-Loss:`. Keep the default squash message, which `safe_merge` does.

## Remaining work

1. The merges above, in that order.
2. **One template sweep**, juniper-cascor first, then every port: `tmp/ports/SWEEP_ITEMS.md` in this worktree,
   uncommitted, 22 items. The main ones:
   - the republish banner "the ceremony never reads one", false once #2592 merges;
   - the ladder's rung 1 republishes files that failed the install check;
   - sub-package find steps accept the meta `v<version>` tag;
   - tests: retention exactly 90, no `if:`/`continue-on-error`, exact step lists, the workflow name pinned to "… to PyPI";
   - install checks import from the checkout.

   Ports that pin the template blocks' sha256 (cascor-client, data-client, worker, data, ml) move those pins with it.
   **OWNER QUESTION**: should the republish job refuse unless the release run's TestPyPI job succeeded?
3. **Plan v1.15.17** (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Record:
   - dialog 2;
   - #763/#767 and their reviews;
   - the audit (4 rebuild per job, 12 `skip-existing`, none checked sha256 before #763);
   - the 8 PRs and their reviews;
   - the findings below;
   - the sweep list;
   - ml `docs/REFERENCE.md`'s version line (#2592 did not bump it).
4. **Land the uncommitted scripts with v1.15.17.** All are in this worktree's `util/ad-hoc/`:
   - the 14 carried from `agent-a54a0a279acc3a863` (sha256 list `tmp/ports/carried_scripts.sha256`);
   - `2026-11-15_publish_port_{clone,survey,template_identity}.py`, `…_fetch_pr_files.py` and `…_build_gate_payload.py`;
   - the seven `2026-11-15_<repo>_one_artifact_publish_port.py` writers. Agents may still update these.

## Findings

- **TestPyPI and PyPI files differ:**
  - juniper-data, every release 0.4.2–0.17.1: each PyPI file differs from TestPyPI's;
  - data-client and cascor-client: every release (21 versions, 42 files);
  - canopy 0.3.0 (0.5.0–0.10.0 match);
  - all 26 recurrence releases match.
- **The monitor could read the wrong run.** Before #2592 it could read `Publish Container Image`: 5 repos, and the
  image run had the larger id in 11 of 20 Releases sampled. A failed PyPI build would have read as `RELEASED`.
- **TestPyPI provenance.** Canopy 0.10.0's TestPyPI provenance shows `environment: null` (PyPI's shows `pypi`). This
  is evidence for the plan's unverified environment-binding item.
- **Old tags.** Tags cut before a repo's port have no republish job, so they can only use "Re-run failed jobs" while
  their 7-day artifact lives.

## Key context

- task-executor agents get their OWN worktree (`.claude/worktrees/agent-<id>`). Write/Edit into this worktree is
  refused there, so they write through Bash and mirror their files here.
- Housekeeping, on the owner's word: those agent worktrees (recurrence's is 234 MB). This worktree's `tmp/ports/` holds
  the clones, the verify copies and the review scratch (hundreds of MB). Keep it under the retention rule.
- The Bash guard trips on "git" inside words and on backticks inside double quotes, which bash executes. Put any such
  text in files written with the Write tool.

## Verification commands (one per call)

```bash
gh pr view 2592 --repo pcalnon/juniper-ml --json state,headRefOid,mergeCommit
python3 -m unittest tests/test_release_train_ceremony.py               # 182 OK on #2592's tree
python3 -I util/ad-hoc/2026-11-15_ceremony_gap_fixes_mutation_check.py  # 13 of 13 KILLED, file restored
```

## Documents referenced / changed

- **Referenced:** the predecessor handoff; `tmp/ports/BRIEF.md` (the port spec); `tmp/ports/SWEEP_ITEMS.md`;
  juniper-cascor `main`'s publish workflows and `docs/ci_cd/MANUAL.md`.
- **Changed, via #2592:**
  - `util/release_train/ceremony.py` and `tests/test_release_train_ceremony.py`;
  - `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` and `docs/REFERENCE.md`;
  - `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` and `CHANGELOG.md`;
  - `util/ad-hoc/2026-11-15_ceremony_gap_fixes_mutation_check.py` and `util/ad-hoc/2026-11-15_precommit_in_clean_copy.py`.
- **Changed, the ports:** each PR's own file list.
- **This file:** lands through its own one-file PR.
