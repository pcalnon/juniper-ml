# Thread Handoff — Recurrence × Equities: juniper-cascor 0.13.0 published, consolidated plan v1.15.7

**Date**: 2026-10-28 UTC (this host's clock is local time, UTC−5)
**Session**: `22169b88`, the Linux host, worktree `.claude/worktrees/keen-popping-wilkes`. Commits are signed only through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_recurrence-equities-p5-11-closed-cascor-0-13-0-at-gate-plan-v1-15-6.md` (landed by juniper-ml#2383). Start from this file. That file's item 1 (the post-merge re-check) passed. Its owner items and follow-ups are carried below, each re-checked on 2026-10-28.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). Nothing the arc can do alone is open. What remains is the owner's items, which a session surfaces and does not act on, and follow-ups that are blocked or optional.

## Completed this session (each probed here)

- **The predecessor's post-merge re-check passed.** On `origin/main` (`9b1f4db7`: `a9a2db52` plus three Dependabot commits that touch only `.github/workflows/`), v1.15.6's script `--check` exits 0, and the plans read 1.7.23 and 1.15.6.
- **juniper-cascor 0.13.0 is published** (the flood-3 arc's release; that arc's handoff is `HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`).
  - The owner approved run 40608671287. Its approvals list `pcalnon` for `pypi` and the 5-minute wait timer, without timestamps. The run's `pypi` deployment statuses date the approval: `waiting` → `queued` at 11:39:02Z.
  - `Publish to PyPI` ran 11:42:56Z–11:43:30Z, and PyPI's wheel is from 11:43:24Z, 54 minutes after ml#2383 merged. v1.15.6's "at the gate" was stale within the hour.
  - PyPI's `requires_dist` equals TestPyPI's (33 entries). **The files do not.** cascor's `publish.yml` runs `python -m build` in the `testpypi` job (`:29`) and again in the `pypi` job (`:69`), so PyPI's wheel and sdist are a second build with a different sha256.
    - 0.13.0's two builds have the same member contents and differ only in zip timestamps.
    - 0.12.0's also differ in `WHEEL` and `RECORD` (setuptools 84.0.0 on TestPyPI, 84.2.1 on PyPI). Each job installs `build` unpinned (`:26`, `:66`), so a long gate can change the build backend.
  - **The wheel carries cascor#731.** `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` (new) parses the PyPI wheel with `ast`, without installing it:
    - `compute_classification_accuracy` is defined at module level (`api/lifecycle/classification_metrics.py:297`);
    - it is called inside `_compute_final_eval_metrics` (`api/lifecycle/manager.py:2292`);
    - the wheel ships the tree twice (`api/` and `src/api/`, 0.12.0 too), and the probe checks both copies.

    It exits 0 on 0.13.0. The 0.12.0 control fails all four checks (exit 1), and a failed download exits 2.
  - **Nothing runs it yet by default.** juniper-deploy pins `ghcr.io/pcalnon/juniper-cascor:0.12.0`: `docker-compose.yml:233` and `:427`, and helm `k8s/helm/juniper/values.yaml:120` ("DEPLOY-15: pinned; bump with juniper-cascor releases"). No deploy PR is open.
  - `util/experiment_stack.bash:171` launches `${PROJECT_DIR}/juniper-cascor/src` unless `JUNIPER_EXP_CASCOR_SRC_DIR` or `JUNIPER_EXP_PROJECT_DIR` points elsewhere. For the canonical checkout that is the cascor primary, which still has no `compute_classification_accuracy`.
  - ml#2381's own condition (its body, `:122`): "That column exists once this PR merges and a cascor carrying juniper-cascor#731 serves the run."
- **Consolidated plan v1.15.6 → v1.15.7** (this handoff's PR), by `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` (new): 10 edits.
  - **Flipped**: the four places v1.15.6 left waiting. These are the Date line, XC-P12 action 4 (two lines), §4's P6 line (it now names both defaults), and §5's R-CASCOR note (two new sub-bullets after the "cut" one).
  - **Also**: the Version line (replaced, 1.15.6 → 1.15.7). **Added**: the status line, the validation-record lines, and the two changed-by lines.
  - §2's P4 row (508 characters) has no room under 512 characters, and §5 carries the publish, as v1.15.6 decided for the cut.
  - Every line stays at or under 512 characters; the script refused one draft at 523. It was re-applied from a pristine copy after each text fix, and its second run reports all 10 edits already applied.
  - The recurrence plan is unchanged at v1.7.23. It names no cascor 0.13.0, `test_accuracy` or cascor#731; its two APD-ML-002 lines, `:711` and `:972`, are the 10-27 record.
- **Validation**: two independent read-only reviewers checked the first draft.
  - A fact-checker found 0 BLOCKER, 0 MAJOR, 6 MINOR and 8 NIT. A residue / consistency / executability reviewer found 0 BLOCKER, 0 MAJOR, 6 MINOR and 13 NIT, and no predecessor item dropped.
  - They converged on five findings, all applied:
    - the plan credited the probe with a check it did not make, so it now parses the call's enclosing function;
    - the script docstring still said "none does yet";
    - the notify-diff path was wrong;
    - "stale since 11:43Z" should be 00:25Z;
    - a saved diff was stale.
  - Also applied:
    - the probe's download failure now exits 2;
    - the memory block's time and its misplaced dual-gate bullets;
    - the default `src/` named with both variables;
    - the approval time;
    - the source list;
    - the APD-ML-002 framing;
    - items 3.2, 3.6 to 3.9;
    - the rules and the verification block.
  - Not applied:
    - the moot deadline under §5's "cut" note (`:959`) stays, resolved two lines later (`:961`), following the 0.12.0 pattern (`:952` → `:957`);
    - pre-existing staleness outside P12 is item 3.9.
  - **Round 2**: a third reviewer, briefed only on the fix pass, found 0 BLOCKER, 0 MAJOR, 5 MINOR and 9 NIT. None was in the plan, which it replayed byte-for-byte from the script on a pristine copy. All were applied except one: the plan's XC-P12 line lacks "for the canonical checkout" (no room under 512), which this handoff and the script docstring carry. The MINORs:
    - 0.12.0's two builds differ in content;
    - the plan does schedule deploy pins;
    - the flood-3 retention gate;
    - the preflight runs three checks;
    - the deploy grep's pattern.
  - **My own catches**: before validation, two overclaims ("fills nowhere", "none" serves #731). A run whose `JUNIPER_EXP_CASCOR_SRC_DIR` names the `src/` of a checkout at or after `752a797f` does serve it. I missed that the script docstring kept one; both round-1 reviewers caught it.
- **Coordination, proposed and unacknowledged**: I messaged the flood-3 peer session (`flood3-continuation-cascor-0-13-0-at-pypi-gate`) a split. This arc takes the consolidated plan. That arc keeps `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, its handoff, and its item 5 (the wheel *import* probe). It never replied (its state was `waiting`), so I did not touch the parent `Juniper/AGENTS.md` (item 3.8).
- **Auto-memory**: `project_pypi_publish_workflow_dual_gate.md` gains a section on the cascor second build, and 0.13.0's approval as a later instance. `project_recurrence_equities_p0_arc_2026-10-04.md` gains a state block and a new description. `MEMORY.md` is unchanged.
- **Merge approval**: the owner granted it in this session ("merge approval granted"). It covers this session's PRs only and does not carry forward.

## Remaining work, in order

1. **Post-merge re-check of this handoff's PR**: on `main`, the v1.15.7 script's `--check` exits 0, and `git grep -n -e '^- \*\*Version\*\*'` on the consolidated plan shows 1.15.7.
   - Run it before v1.15.8 lands. The next revision replaces anchors this script checks (the Version line at least), so its `--check` refuses once that lands. v1.15.6's exits 1 on v1.15.7's tree (five anchors), and that is expected.
   - Also check that the arc memory's description and state block name this PR, not `ml#TBD`.
2. **The owner's items.** Surface them; do not act on them.
   - **Register row `APD-ML-002`** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`).
     - Its "in no juniper-cascor release yet" (`:1304`) and "unreleased" (`:1364`) have been stale since Release v0.13.0 was published (00:25:28Z).
     - The publish does not by itself meet the row's close condition, "until that column exists": by ml#2381's reading, the column exists once a cascor carrying #731 serves the run, and neither default does.
     - ml#2381 left the close to the owner: "Closing the row is a five-touch protocol, and the timing depends on the cascor release".
   - **juniper-deploy's cascor pin is 0.12.0**, and its helm values say "bump with juniper-cascor releases" (DEPLOY-15). Moving it to 0.13.0 is how a deployed stack would get #731. The consolidated plan's deploy pins ride R-CASCOR: §4 Wave 1's Images route, §8's juniper-deploy row (`:1230`, "The pin PR is opened once GHCR serves the image"), and P4-39 and P4-40. Whether 0.13.0, which carries no cascor F-S10 fix, counts as R-CASCOR for that is the owner's call.
   - **R-DATA-2: juniper-data 0.17.2** (P3-03, P3-09 and W5.7; W5.7 changes a default, so whether a patch may carry it is the owner's call). PyPI still serves 0.17.1, and no v0.17.2 Release exists (re-probed 2026-10-28). That release turns canopy#777's drift job red, because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`. Re-capture both snapshots then; the job prints the commands.
   - **juniper-data `notify-consumers.yml`: add juniper-canopy to the matrix.** On `main` it is still `repo: [juniper-recurrence]` (`:78`).
     - The diff is in canopy#777's body, and at `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f/jd-notify/proposed-juniper-data-notify.diff`.
     - Only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers canopy. After both merge, a `workflow_dispatch` with version `0.17.1` settles it.
   - **The `index.jsonl` correction row** (`~/.local/state/juniper-experiments/index.jsonl` line 482, correcting line 477; still 482 lines) says `degraded`, where the owner's option said `failed`. Ask; append another correction row only on the owner's word, and never rewrite either line.
   - **juniper-config-tools 0.2.0**: `[Unreleased]` in `juniper-config-tools/CHANGELOG.md` is still empty, with four commits touching the package since `juniper-config-tools-v0.1.0` (PyPI 0.1.0). It must be backfilled before a cut.
   - **W0.1's service-core half.** The preflight still refuses `JuniperCascor1` with 2 findings (service-core 0.5.0; re-run 2026-10-28). Never restart the cascor on `:8202`, and never modify `JuniperCascor1`.
   - **The consolidated plan's §6 A1 and A9 remainders.**
     - A1: P6 OD-2 for APD-ML-003..006, canopy#685 call (a), the data-client source fix, a cascor F-S10 fix (0.13.0 carries none), and host recurrence legs.
     - A9: DC-0.6's two numbers.
3. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316): BLOCKED** until W0.1. Recipe: `experiment_stack.bash --up --recurrence --config <abs irregular-sine-rff.yaml>`, then `run_experiment.py`, then `--down <RUN_ID>`. Done means `manifest.json` shows `save_model.source == "snapshot"`.
   2. **A local cascor run fills `test_accuracy` only from a cascor `src/` that carries #731.** The PyPI publish does not change this. The cascor primary still lacks `compute_classification_accuracy` (re-checked 2026-10-28) and is frozen while live stacks import it. To run against #731:
      - Set `JUNIPER_EXP_CASCOR_SRC_DIR` to the `src/` of a checkout at or after `752a797f` (`v0.13.0` is one). **Pair it with `JUNIPER_EXP_PROJECT_DIR`**: `util/experiment_stack.bash:61-74` warns that otherwise the run gets pinned code against the primary's config.
      - Creating such a checkout needs git in juniper-cascor, which a worktree-isolated juniper-ml session is refused; use a juniper-cascor session, or ask the owner.
      - The one existing `v0.13.0` checkout, `worktrees/juniper-cascor--release--v0.13.0--20261027-1816--996134e5`, belongs to the flood-3 arc.
        - Its handoff keeps it "until 0.13.0 is on PyPI" (now true), and removes nothing without an owner signal plus an API check that each PR is merged.
        - `juniper-ml/tmp/release-cascor-0.13.0/eco/juniper-cascor` symlinks to it.
        - Do not build a campaign on it, and never remove it from this arc.
   3. canopy#738 and #751 are **issues**, not PRs (`gh pr view` cannot resolve them; use `gh issue view`). Both are OPEN, last updated 2026-10-18. #738 is canopy 0.9.x work the arc only annotates; #751 waits on Lane B.
   4. From canopy#776's "Left out": the restart modal still shows Noise for `mnist`, which does not declare it.
      - Capturing `mnist`'s declaration would close that, but it is not one entry. canopy's `src/dataset_schema.py` treats `mnist`'s `flatten` as shape-determining (canopy#623) and marks `mnist` as needing juniper-data's optional dataset extra.
      - First check whether the capture tool and canopy#777's drift job can read its schema without that extra.
      - Its training fields also stay cascor-only under recurrence.
   5. Optional, not run: an E-H suite run with `--shared-equities-cache <abs dir>`.
   6. **Removing the two canopy worktrees** (`worktrees/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f`, `worktrees/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f`). Their `tmp/` is archived, and the commands are in `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/README.md`. This needs a session in juniper-canopy, or the owner.
   7. `MEMORY.md` is 20,919 bytes (measured 2026-10-28), 919 over the 20,000-byte target. The excess is in other arcs' active lines (canopy E2E, backup, perf, the process and worktree trap groups), which are theirs to compact.
   8. **The parent `Juniper/AGENTS.md` RELEASED paragraph** still names cascor 0.12.0 as the latest cascor and says it was "re-probed against PyPI on 2026-10-27 UTC". It is unversioned (no git), so a clobbered edit cannot be recovered, and only one session may edit it.
      - First read the paragraph: if it already names 0.13.0, there is nothing to do.
      - Otherwise ask the flood-3 session or its successor (`ListAgents`, then `SendMessage`) whether it is editing it.
      - If none can be reached, surface it to the owner; do not edit on silence.
   9. **Pre-existing staleness outside P12**, not fixed here.
      - The R-CASCOR table row (`:925`, 507 characters) records only 0.12.0's bypass.
      - §6's mid-wave sitting still says data 0.17.1's (`:1052`) and cascor 0.12.0's (`:1055`) gates wait; both were approved by 2026-10-25.
      - The plan keeps non-P12 paths at v1.14.0's state by design (its v1.15.0 status note: "Every other path keeps v1.14.0's state and its staleness"). Changing that is the owner's call, not a P12 record's.

## Rules that held this session

- **A published wheel is not a running service either.** Name what fills the column. Here, juniper-deploy pins 0.12.0, and the experiment stack runs the primary's `src/` by default, so the plan says "neither default", never "none".
- **A recorded gate can go stale within the hour.** v1.15.6 was true when it merged (10:49:20Z). The owner approved about 50 minutes later (the deployment's `queued` status, 11:39:02Z), and PyPI had the wheel 4 minutes after that. Re-probe a gate immediately before recording it, and again before handing over.
- **Date an approval from the deployment's statuses**, not the approvals API, which has no timestamps. `waiting` → `queued` is the approval only when it comes after the wait timer; here the timer expired about 00:31Z. An approval inside the timer queues at the timer's expiry.
- **Never write "with the sha256 TestPyPI took" for a cascor publish.** Its `publish.yml` builds once per job. Compare `requires_dist`, and probe the PyPI wheel itself. Check any repo's `publish.yml` before claiming byte-identity.
- **Make a probe check exactly what the record says it shows, and give it a control that fails.** The first probe only grepped for a call line, yet the plan said it showed the final evaluation calls the function; both reviewers caught it. No error other than a failed check may exit with the control's failing status (1): the probe exits 2 on a failed fetch, a sha256 mismatch or any unexpected error.
- **Stamp times from `date -u`, never from inference.** I wrote "~13:00Z" into memory from a guess; it was 21:11Z.
- **Coordinate with a peer session before editing a shared, unversioned file**, and never treat silence as agreement.
- **Carried, still true**:
  - Grep the whole plan for every item you change.
  - A record of another arc's merge or release is still a record to verify.
  - Before trimming a `MEMORY.md` hook, find its detail in the topic file, in any case. Gate on the link set, not a count.
  - A waiting `pypi` gate's working deadline is day 30 from the run's `created_at`; day 35 is the outer bound.
  - Fetch and re-check `origin/main` against your paths immediately before every whole-file upload.
  - `push_signed_commit.py --expected-head` needs the FULL sha.
  - The `pypi` gates and merges are the owner's, and merge approval is per session.
  - A post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.
  - A consolidated-plan line has at most 512 characters.
- **Tooling on this host**:
  - `grep` is ugrep, and a regex with a bounded `.{0,N}` context "exceeds complexity limits". Use a small Python helper in the worktree's `tmp/`.
  - The worktree guard refuses:
    - heredocs inside `&&` chains;
    - `gh` with nested-quote `--jq`;
    - `python3` reading `/dev/stdin` from a pipe;
    - a `for` loop around `sed -n "${n}p"`;
    - a pipeline that reads `${PIPESTATUS[0]}` after a git command.

    Write a file, then run it plainly.
  - This host's `tail` (uutils) accepts `-1` with one file but refuses it with two; use `tail -n 1`.
  - `python3` on `PATH` is `JuniperCascor1`'s interpreter. Run helpers with it, but never install into it.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main            # this handoff's PR at or near the top
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.23 and 1.15.7
python3 util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py --check; echo $?    # 0 (until v1.15.8 lands; see item 1)
python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.13.0; echo $?    # 0: PASS, 0 failed checks
python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.12.0; echo $?    # 1: the control fails 4 checks (2 would mean an error, not a check)
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-cascor/json'))['info']['version'])"   # 0.13.0 until a newer cascor (which would change the "neither default" analysis)
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" | grep -n 'image: ghcr.io/pcalnon/juniper-cascor:'   # exactly two lines, both 0.12.0, until a deploy bump
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-data/json'))['info']['version'])"     # 0.17.1 until R-DATA-2
gh run list --repo pcalnon/juniper-canopy --workflow juniper-data-schema-drift.yml --limit 3    # success until juniper-data's next release
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python   # still REFUSED (2 findings) until W0.1; read-only: pip check, a version-pin probe, an import probe
wc -l ~/.local/state/juniper-experiments/index.jsonl                                            # 482 until the owner rules
grep -c 'def compute_classification_accuracy' /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/lifecycle/classification_metrics.py   # 0 until the cascor primary moves to or past 752a797f
```

## Git state

- **This worktree** (`keen-popping-wilkes`) is on `worktree-keen-popping-wilkes` at `a9a2db52`, the branch's base. It was created at 20:52Z, after `origin/main` had moved to `9b1f4db7` through three workflow-only Dependabot commits, none touching these files.
- Its uncommitted copies of the four files below are what this handoff's PR carries. The PR is uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored `tmp/s4/`** holds this session's scratch, none of it the only copy of a record:
  - the state probe;
  - the downloaded 0.13.0 wheel (sha256-verified against PyPI);
  - cascor's `publish.yml`, and juniper-deploy's `docker-compose.yml` and helm values;
  - the approvals and deployment-status helpers;
  - ml#2381's body and the final v1.15.7 diff (`v1_15_7.diff`);
  - the probe's synthetic and download-failure harnesses;
  - the small helpers (`show_lines.py`, `wheel_context.py`, `plan_blob_scan.py`);
  - the two reviewers' scratch (`validation-a/`, `validation-b/`).

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.7);
  - `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` (new);
  - `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` (new);
  - this file (new).
- **Outside any repo**, in auto-memory:
  - `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description);
  - `project_pypi_publish_workflow_dual_gate.md` (a section on the cascor second build; 0.13.0's approval as a later instance; how to date an approval).

  `MEMORY.md` is unchanged.
- **Referenced, not changed**:
  - the superseded handoff (above) and the flood-3 handoff `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`;
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23, unchanged);
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (row `APD-ML-002`, unchanged);
  - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (the flood-3 record, that arc's);
  - `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/README.md` (the canopy worktree removal commands);
  - `util/experiment_stack.bash` (`:61-74`, `:171`);
  - `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_6_p5_11_closed_cascor_0_13_0_at_gate.py` (the pattern);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
