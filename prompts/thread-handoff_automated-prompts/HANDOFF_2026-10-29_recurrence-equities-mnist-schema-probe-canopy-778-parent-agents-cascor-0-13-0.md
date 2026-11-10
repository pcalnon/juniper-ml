# Thread Handoff — Recurrence × Equities: the cascor primary carries #731 (plan v1.15.8), mnist schema probe, juniper-canopy#778, parent AGENTS.md records cascor 0.13.0

**Date**: 2026-10-29 UTC (this host's clock is local time, UTC−5)
**Session**: `3ca2d3e4`, the Linux host, worktree `.claude/worktrees/cosmic-puzzling-lovelace`. The owner named it `y1`; `ListAgents` later lists it as `recurrence-equities-cascor-0-13-0-published-plan-v1-15-7`. Commits are signed only through the API (`util/open_signed_pr.py`, `util/push_signed_commit.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_recurrence-equities-cascor-0-13-0-published-plan-v1-15-7.md` (landed by juniper-ml#2384). Start from this file.
- That file's item 1, the post-merge re-check, passed.
- Its item 3.4 (the `mnist` schema question) is answered, and its change is now juniper-canopy#778.
- Its item 3.8 (the parent `Juniper/AGENTS.md` paragraph) is done.
- Every other item is carried below. Each was re-checked on 2026-10-29, except §6 A1 / A9 of the consolidated plan, which are the owner's decisions.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, now v1.15.8). Nothing the arc can do alone is open. What remains is:

- the owner's items, which a session surfaces and does not act on;
- juniper-canopy#778, which needs a canopy session;
- follow-ups that are blocked or optional.

## Completed this session (each probed here)

- **The predecessor's post-merge re-check passed** (from 01:55:47Z).
  - `origin/main` was `c5350c98` (ml#2384).
  - `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py --check` exited 0.
  - The plans read 1.7.23 (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`) and 1.15.7 (the consolidated plan).
  - The arc memory `project_recurrence_equities_p0_arc_2026-10-04.md` named ml#2384, not `ml#TBD`.
  - `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py` exits 0 on 0.13.0; the 0.12.0 control exits 1 with four failed checks.
- **The cascor primary carries cascor#731 since 2026-10-29 20:48:58Z.** A validator found the move about 8 minutes after this handoff's first draft was written, and I re-derived it from source.
  - The primary's `main` reflog (`juniper-cascor/.git/logs/refs/heads/main`) records `pull origin: Fast-forward` from `5b7d10dc` to `e8e8bf4d`.
  - `e8e8bf4d` is cascor `main`. `compare 5b7d10dc...e8e8bf4d` is ahead 10 and behind 0: #731, #733 (the 0.13.0 release proposal), the python-dateutil 3.0.0 and munkres 3.0.0 bumps, test and CI fixes, and cascor's `/tmp` fix. `compare 752a797f...e8e8bf4d` is ahead 8 and behind 0.
  - The primary's `classification_metrics.py` now defines `compute_classification_accuracy`, and `manager.py:2292` calls it.
  - So `util/experiment_stack.bash:171`'s default `src/` serves #731 for the canonical checkout, and a run launched that way can fill `test_accuracy`. juniper-deploy still pins 0.12.0.
  - **Who pulled is not recorded**: the reflog shows only the git identity. This session ran no git in juniper-cascor.
  - **The pull landed under a live stack.** The `:8202` uvicorn (pid 2857489, up since 2026-09-22) has its cwd in the primary's `src/`. That is the frozen-primary hazard in `reference_cascor_primary_frozen_while_any_stack_imports_it.md`: its next forkserver child imports the new code. I surfaced it and did not act on it (item 2).
- **The consolidated plan goes from v1.15.7 to v1.15.8** through `util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py` (new), which makes 9 edits.
  - It flips the two places v1.15.7 said the default `src/` lacks #731: XC-P12 action 4 and §4's P6 line. The third, v1.15.7's own status line, stays as written, as the version log.
  - It extends the Date line's probe list.
  - It adds a §5 R-CASCOR sub-bullet, which also records the `[servers]` resolve below. Under it, a line notes that the pull landed under the `:8202` stack and that O13 governs a pull of the trio's primaries.
  - It adds the record lines: Version, status, validation, the scripts list, and changed-by. The changed-by line names this session's parent `Juniper/AGENTS.md` edit, as v1.15.5's did.
  - Every line is at most 512 characters.
  - The script was applied to a pristine copy, and its second run reports all 9 edits already applied. v1.15.7's `--check` now exits 1, which is expected.
  - The recurrence plan is unchanged at v1.7.23. It names no cascor#731 or `test_accuracy`.
- **A fresh `juniper-ml[servers]==0.11.3` install resolves juniper-cascor 0.13.0.**
  - The command: `<venv>/bin/python -m pip install --dry-run --ignore-installed --no-cache-dir --quiet --report <out>.json "juniper-ml[servers]==0.11.3"`, run on Python 3.14.7. It resolves 64 packages.
  - 0.11.3's floor is `juniper-cascor[api,juniper-data]>=0.12.0`, with no cap, and 0.13.0's `requires_dist` equals 0.12.0's (33 entries).
  - The fact-checker reproduced the same 64-package set in a new venv.
- **Item 3.4 is answered: juniper-data's `mnist` schema reads without juniper-data's `[mnist]` extra.** That extra pulls `datasets[vision]>=4.0.0`; there is no `datasets` extra.
  - The new probe, `util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py`, builds a throwaway venv from `--python`, the same way canopy's drift job builds its environment: the job runs Python 3.14 (its latest run had 3.14.9; this probe ran 3.14.7). PyPI's `juniper_data-0.17.1-py3-none-any.whl` (sha256 `cce2c167…`, checked against PyPI's JSON) is installed with `[api]` only.
  - A completion marker gates reuse of the venv. Every run re-checks the wheel against PyPI. Inside the venv it checks the installed version and the 101 RECORD-hashed `juniper_data/` files against the distribution's RECORD. The 100 `.pyc` files carry no hash.
  - **The absence control** is one fact seen three ways: no `datasets` distribution is installed, `import datasets` raises `ModuleNotFoundError`, and `MnistGenerator.is_available()` is `False`.
  - **The schema reads**: `mnist` 3.0.0 has 13 properties, declares `flatten` and `n_samples`, and declares no `noise`.
  - **The silent drop**: `MnistParams(n_samples=500, noise=0.25)` validates, and `noise` is absent from `model_dump()`. So the restart modal's Noise value is lost without a word today.
  - **The drift check** comes from canopy `main` at `7fb3a159`, fetched by that sha. It runs on two fixtures that hold only an `mnist` entry, under canopy's tabular snapshot provenance:
    - with the schema as read, it exits 0 with `mnist … ok` and the "no drift" summary;
    - in the control, with `flatten`'s default flipped, it exits 1 with `DRIFT` and `field "flatten": default:`.
  - **Why the schema reads**: at juniper-data `v0.17.1`, `juniper_data/generators/mnist/generator.py:15-21` imports `datasets` inside `try` / `except ImportError`.
  - **The probe's exit contract** is 0 on a pass, 1 only on a failed check, and 2 on any other error, with earlier failures still printed. A probe adversary broke the first version with 16 negative tests: a failed check could exit 2, a checker crash could exit 1, and the verdict leaned on canopy's `equities` entry. The rewrite passes:
    - 8 negatives:
      - stub `datasets` → 1;
      - `MnistParams` with `extra="forbid"` → 1;
      - an edited installed file → 2 (RECORD);
      - a bad `--canopy-ref` → 2;
      - `--work` pointing at a file → 2;
      - a missing `--python` on reuse → 2;
      - `-OO` → 0;
      - restored → 0.
    - 11 synthetic cases of its `classify_check`. The 4 that must be errors (SIGKILL, the checker's own exit 2, a crash after the report, and silenced stdout) give exit 2.
    - Round 2's two in-venv cases: a present-but-broken `datasets`, and one whose import calls `sys.exit(1)`. Both break juniper-data's own import, so both give 2, with the recorded control failures printed first. The in-venv step now ends with a summary line that the outer probe requires.
  - **The census** (all 16 generators): of canopy's rank-2 generators, only `mnist` and flat `equities` declare no `noise`. `equities` has had a `DECLARED_PARAM_DEFAULTS` entry since canopy#776, so `mnist` is the one left.
- **juniper-canopy#778 is opened** (20:36:53Z; the owner chose an issue over a handoff-only record). It carries the evidence and the change for a canopy session.
  - Two reviewers simulated the entry against canopy `main` (`7fb3a159`), and its change list was corrected twice, at 21:16:28Z and after round 2. Item 1 checks the final body. These tests must change:
    - `src/tests/unit/test_recurrence_request.py`: `:350` (`UNDECLARED_RANK2` lists `mnist`), `:372-375` (expects `()` for every declared generator), and `:438-450` (`test_an_undeclared_generator_is_forwarded_as_staged[mnist]` asserts `stage.shaped is None`);
    - `src/tests/regression/test_restart_modal_restages_what_it_shows.py:54` (`"mnist": ("n_samples", "noise")`);
    - `src/tests/regression/test_empty_axis_commit_and_restage_zeros.py:148-157` (reads `mnist["nn_dataset_noise"]`);
    - and `test_mnist_keeps_its_seed` (`src/tests/regression/test_cascor_staging_declared_params.py:184`) should move out of `TestEveryOtherGeneratorIsForwardedAsStaged`.
  - Comments and docs to update:
    - `src/backend/recurrence_request.py:74-76`, `:238-244` and `:308`;
    - `src/backend/service_backend.py:408`;
    - `src/frontend/dashboard_manager.py:6771`;
    - `src/dataset_schema.py:545` and `:580`;
    - `docs/AGENTS_REFERENCE.md:2025` and `:2033`;
    - `util/ad-hoc/2026-10-26_capture_published_generator_schemas.py:57-58`.

    This list comes from two simulations, not from a run of canopy's suite, so the canopy session runs the full suite.
- **Item 3.8 is done: the parent `Juniper/AGENTS.md` RELEASED paragraph records cascor 0.13.0.** The owner approved the edit after the flood-3 peer `flood3-continuation-cascor-0-13-0-at-pypi-gate` stayed `waiting` through every `ListAgents` call this session.
  - It was edited at 20:30:11Z and corrected at 21:11:17Z, once the primary had moved.
  - Against the pre-edit text, there are three hunks:
    - `:6` Last Updated (2026-10-27 → 2026-10-29);
    - `:206` the re-probe date (→ 2026-10-29; every package the paragraph names was re-probed at 20:28:26Z, and only cascor had moved);
    - a 9-line juniper-cascor 0.13.0 bullet at `:240-248`, which names the uncapped `[servers]` resolve, the 0.12.0 deploy pin, and the primary at `e8e8bf4d` (for the canonical checkout).
  - Both earlier versions are archived in the primary checkout's `tmp/`, which outlives this worktree: `juniper-ml/tmp/2026-10-29-parent-agents-md-backups/` holds `AGENTS.md.pre-edit-2026-10-27T22-35Z` (sha256 `6ffd7604…`) and `AGENTS.md.after-first-edit-2026-10-29T20-30Z` (`79b17d5e…`). Claude Code's file history holds another pre-edit copy.
- **The arc memory** `project_recurrence_equities_p0_arc_2026-10-04.md` gains this session's state block and a new description, which says `ml#TBD` until this PR's number is filled in.
- **Validation**: three independent reviewers checked the first draft.
  - A fact-checker found 1 BLOCKER, 3 MAJOR, 4 MINOR and 9 NIT.
  - A residue / consistency / fresh-session auditor found 1 BLOCKER, 1 MAJOR, 13 MINOR and 12 NIT.
  - A probe adversary found 0 BLOCKER, 3 MAJOR, 5 MINOR and 9 NIT.
  - They converged on these: the cascor primary's move (both record reviewers' BLOCKER); the arc memory not yet written; the census sentence contradicting itself; "Python 3.14.7"; "#265 is the latest deploy PR"; the dropped flood-3 linkage and freeze note; and the Validation placeholder.
  - All of those were applied, plus the probe rewrite and #778's change list.
  - **Round 2**: a fresh reviewer checked the fix pass. It found 0 BLOCKER, 1 MAJOR (#778's change list, still incomplete: two more failing tests and seven more stale comments), 8 MINOR and 9 NIT. It replayed v1.15.8 on a pristine copy of `origin/main`'s plan and got a byte-identical result.
    - All of its findings were applied except the claims it marked not re-derivable, which come from this session's own transcript: the 8-minute gap, the 18-hour wait, the session's names and the reviewer counts.
    - The MINORs it raised:
      - the plan changed-by line omitted the parent `AGENTS.md` edit;
      - the "three places" wording;
      - the `:8202` note missing from the plan;
      - a misattributed freeze rule;
      - #778's PR number unassigned to any step;
      - two in-venv exit-contract gaps in the probe.
    - There is no round 3.
- **Merge approval**: the owner granted it in this session ("merge approval granted"). It covers this session's PRs only and does not carry forward.

## Remaining work, in order

1. **Post-merge re-check of this handoff's PR.**
   - On `main`, `python3 util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py --check` exits 0, and the plans read 1.7.23 and 1.15.8. v1.15.8's `--check` refuses once v1.15.9 lands, which is expected.
   - `python3 -I util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py --python /opt/miniforge3/envs/JuniperCascor1/bin/python` exits 0.
   - juniper-canopy#778's body names this PR and the probe's final filename. This session edits the body right after opening the PR, so this is a check, not a step.
   - The arc memory `project_recurrence_equities_p0_arc_2026-10-04.md` names this PR, not `ml#TBD`.
2. **The owner's items.** Surface them; do not act on them.
   - **The cascor primary was pulled under the live `:8202` stack** (2026-10-29 20:48:58Z, `5b7d10dc` → `e8e8bf4d`, actor unrecorded).
     - The auto-memory `reference_cascor_primary_frozen_while_any_stack_imports_it.md` says the primary is frozen while any stack imports it.
     - In `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.8), `:791` says the trio runs what the primaries hold, and `:793` says O13 governs a pull of them.
     - The `:8202` uvicorn's next forkserver child imports the new code.
     - Whether the pull was intended, and whether that stack should keep running, is the owner's call. Never restart the cascor on `:8202` from a session.
   - **Register row `APD-ML-002`** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`).
     - Its "in no juniper-cascor release yet" (`:1304`) and "unreleased" (`:1364`) have been stale since Release v0.13.0 (2026-10-28 00:25:28Z).
     - Its close condition is "until that column exists". By juniper-ml#2381's reading (its body, `:122`), the column exists once a cascor carrying #731 serves the run. A default cascor run launched through `util/experiment_stack.bash` from the canonical checkout now does, and a fresh `[servers]` install resolves 0.13.0. juniper-deploy still pins 0.12.0.
     - No run has filled the column yet. ml#2381 left the close to the owner: "Closing the row is a five-touch protocol, and the timing depends on the cascor release". The register's "Closing a row — the five touches" is at `:43`, and the recurrence plan's APD-ML-002 lines are `:711` and `:972`.
   - **juniper-deploy's cascor pin is 0.12.0**: `docker-compose.yml:233` and `:427`, and helm `k8s/helm/juniper/values.yaml:120` ("DEPLOY-15: pinned; bump with juniper-cascor releases"). No deploy PR is open (re-checked 2026-10-29).
     - Whether 0.13.0, which carries no cascor F-S10 fix, counts as R-CASCOR for the consolidated plan's pin route is the owner's call. That route is §4 Wave 1's Images, §8's juniper-deploy row (`:1232` in v1.15.8, "The pin PR is opened once GHCR serves the image"), and P4-39 / P4-40.
   - **R-DATA-2: juniper-data 0.17.2** (the consolidated plan's P3-03, P3-09 and W5.7). W5.7 changes a default, so whether a patch may carry it is the owner's call.
     - PyPI serves 0.17.1, and no v0.17.2 Release exists.
     - When 0.17.2 ships, canopy#777's drift job turns red, because juniper-data#486 rewrote the `symbols` description of `equities_seq` and flat `equities`. Re-capture both snapshots then; the job prints the commands. canopy#778 offers folding `mnist` into the tabular re-capture as one option.
   - **juniper-data `notify-consumers.yml`: add juniper-canopy to the matrix.** It is still `repo: [juniper-recurrence]` (`:78`).
     - canopy#777, the listener side, merged 2026-10-27. Only the juniper-data change remains.
     - The diff is in canopy#777's body, and at `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f/jd-notify/proposed-juniper-data-notify.diff`.
     - Only the owner can see whether `CROSS_REPO_DISPATCH_TOKEN` covers canopy. Once the change merges, a `workflow_dispatch` with version `0.17.1` settles it.
   - **The `index.jsonl` correction row** (`~/.local/state/juniper-experiments/index.jsonl` line 482, correcting line 477; still 482 lines) says `degraded`, where the owner's option said `failed`. Ask the owner. Append another correction row only on the owner's word, and never rewrite either line.
   - **juniper-config-tools 0.2.0**: `[Unreleased]` in `juniper-config-tools/CHANGELOG.md` is still empty, with four commits touching the package since `juniper-config-tools-v0.1.0` (PyPI 0.1.0). It must be backfilled before a cut.
   - **W0.1's service-core half.** `util/recurrence_env_preflight.bash` still refuses `JuniperCascor1` with 2 findings: juniper-service-core 0.5.0 against juniper-recurrence 0.5.0's `>=0.6.0,<0.8.0`. Never modify `JuniperCascor1`.
   - **The consolidated plan's §6 A1 and A9 remainders** are unchanged, and were not re-probed because they are the owner's decisions.
     - A1: P6 OD-2 for APD-ML-003..006, canopy#685 call (a), the data-client source fix, a cascor F-S10 fix (0.13.0 carries none), and host recurrence legs.
     - A9: DC-0.6's two numbers.
3. **Follow-ups.**
   1. **The first live run of `save_model`'s snapshot path (juniper-ml#2316): BLOCKED** until W0.1.
      - Recipe: `util/experiment_stack.bash --up --recurrence --config <abs irregular-sine-rff.yaml>`, then `util/experiments/run_experiment.py`, then `--down <RUN_ID>`.
      - Done means the run's `manifest.json` shows `save_model.source == "snapshot"`.
   2. **A cascor run that fills `test_accuracy`** no longer needs a pinned `src/` from the canonical checkout, because the primary carries #731 (above). Two cautions:
      - The primary is frozen while any live stack imports it, and the `:8202` stack does (item 2).
      - From a worktree, `util/experiment_stack.bash` derives another `PROJECT_DIR`. Pair `JUNIPER_EXP_CASCOR_SRC_DIR` with `JUNIPER_EXP_PROJECT_DIR` (`:61-74`).
      - The flood-3 arc's `v0.13.0` checkout is `worktrees/juniper-cascor--release--v0.13.0--20261027-1816--996134e5` (still present), and `juniper-ml/tmp/release-cascor-0.13.0/eco/juniper-cascor` symlinks to it.
        - Its handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`, keeps it "until 0.13.0 is on PyPI", which is now true.
        - That handoff removes nothing without an owner signal plus an API check that each PR is merged.
        - Never build a campaign on it or remove it from this arc.
   3. canopy#738 and #751 are **issues**, not PRs. Use `gh issue view`, because `gh pr view` cannot resolve them. Both are OPEN, last updated 2026-10-18.
      - #738 is canopy 0.9.x work that the arc only annotates.
      - #751 waits on Lane B.
   4. **juniper-canopy#778** (from item 3.4) needs a canopy session.
      - canopy's capture tool (`util/ad-hoc/2026-10-26_capture_published_generator_schemas.py`) needs a juniper-data checkout with the release tag, because it runs git there.
      - The change itself needs canopy commits.
      - This worktree-isolated juniper-ml session can do neither.
      - The owner may assign it, or fold it into R-DATA-2's re-capture.
   5. Optional, not run: an E-H suite run with `--shared-equities-cache <abs dir>`.
   6. **Removing the two canopy worktrees**, both still present: `worktrees/juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f` and `worktrees/juniper-canopy--feature--juniper-data-schema-drift-check--20261026-1649--da08414f`. Their `tmp/` is archived, and the commands are in `juniper-ml/tmp/worktree-cleanup-2026-10-28-canopy-p12/README.md`. This needs a canopy session or the owner.
   7. **The predecessor's worktree** `.claude/worktrees/keen-popping-wilkes` is still present.
      - Its gitignored `tmp/s4/` holds session `22169b88`'s scratch: the downloaded 0.13.0 wheel, the helpers, and the reviewers' `validation-a/`, `validation-b/` and `validation-c/`. That handoff says none of it is the only copy of a record.
      - Removing it is the owner's call under the retention rule. Check its `tmp/` first, because `git worktree remove` deletes it.
   8. **This worktree's `tmp/`** (`tmp/y1/`, `tmp/2026-10-29-mnist-schema-probe/`, and the reviewers' `tmp/validation-{a,b,c,r2}/`) holds only scratch.
      - The `AGENTS.md` backups that matter are copied to `juniper-ml/tmp/2026-10-29-parent-agents-md-backups/`, in the primary checkout.
      - Keep that directory until a later session confirms the paragraph. Then it may be deleted, or archived if the owner wants it.
   9. `MEMORY.md` is 20,940 bytes (2026-10-29, after the backup arc's ml#2385 line), 940 over the 20,000-byte target. The excess is in other arcs' active lines (canopy E2E, backup, perf, and the process and worktree trap groups), which are theirs to compact.
   10. **At the next plan revision**, cite juniper-canopy#778 in the recurrence plan's "Left out of juniper-canopy#776" sentence (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md:712`, v1.7.23). It is not worth a revision on its own.
   11. **Pre-existing staleness outside P12** in `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, not fixed here and unchanged.
       - The R-CASCOR table row (`:926` in v1.15.8, `:925` in v1.15.7; 507 characters) records only 0.12.0's bypass.
       - §6's mid-wave sitting still says data 0.17.1's (`:1054`; v1.15.7 `:1052`) and cascor 0.12.0's (`:1057`; v1.15.7 `:1055`) gates wait. Both were approved by 2026-10-25.
       - The plan keeps non-P12 paths at v1.14.0's state by design (its v1.15.0 status note: "Every other path keeps v1.14.0's state and its staleness"). Changing that is the owner's call.

## Rules that held this session

- **Re-probe a fast-moving fact immediately before recording it, and again before handing over.** The cascor primary moved 8 minutes after this handoff's first draft. Session-start probes do not cover it.
- **An "extra is absent" claim needs a control that shows it, and a test that the control can fail.** A stub `datasets` flips the probe to exit 1.
- **A probe's exit contract has to survive its own failure paths.** A failed check must not cascade into an error, and a crashed checker must not read as a result.
- **A synthetic fixture entry proves the mechanism, not a capture.** A real capture goes through canopy's tool, with its wheel-against-tag provenance. Name extras from the wheel's `provides_extra`: it is `[mnist]`, not "the `datasets` extra".
- **An uncapped floor moves with every release.** A fresh `[servers]` install resolves cascor 0.13.0 while juniper-deploy pins 0.12.0. Name the path; never write "0.13.0 is (not) running".
- **An owner question can sit for hours.** This one sat about 18 hours. After the answer, re-probe everything before acting: `main`, PyPI, the peer, and the target file's sha256.
- **Back up an unversioned file outside the worktree** (the primary checkout's `tmp/`), re-check its sha256 immediately before each edit, and diff it afterwards.
- **Carried, still true**:
  - A published wheel is not a running service; name what fills the column.
  - A recorded gate can go stale within the hour.
  - Date an approval from the deployment's statuses. `waiting` → `queued` is the approval only when it comes after the wait timer; an approval inside the timer queues at its expiry.
  - cascor's `publish.yml` builds once per job. Compare `requires_dist`, and check any repo's `publish.yml` before claiming byte-identity.
  - Make a probe check exactly what the record says, and give it a control that fails. Only a failed check exits 1; every other error exits 2.
  - Stamp times from `date -u`, never from inference.
  - Coordinate with a peer before editing a shared, unversioned file, and never treat silence as agreement. Here the owner's approval replaced the peer's silence.
  - Grep the whole plan for every item you change.
  - A record of another arc's merge or release is still a record to verify.
  - Before trimming a `MEMORY.md` hook, find its detail in the topic file; gate on the link set, not a count.
  - A waiting `pypi` gate's working deadline is day 30 from the run's `created_at`; day 35 is the outer bound.
  - Fetch and re-check `origin/main` against your paths immediately before every whole-file upload.
  - `push_signed_commit.py --expected-head` needs the FULL sha.
  - The `pypi` gates and merges are the owner's, and merge approval is per session.
  - A post-publish resolve passes `--no-cache-dir` and `--ignore-installed`.
  - A consolidated-plan line has at most 512 characters.
- **Tooling on this host**:
  - `grep` is ugrep. A regex with a bounded context on both sides, such as `.{0,200}X.{0,200}`, "exceeds complexity limits"; use a small Python helper in the worktree's `tmp/`.
  - The worktree guard refuses:
    - heredocs inside `&&` chains;
    - `gh` with nested-quote `--jq`;
    - `python3` reading `/dev/stdin` from a pipe;
    - a `for` loop around `sed -n "${n}p"`;
    - a pipeline that reads `${PIPESTATUS[0]}` (the predecessor saw it after a git command, this session after `bash … | tail`);
    - long command lines that mix `gh api … github.raw` fetches with other commands.

    Write a script file, then run it plainly.
  - Write and Edit refuse the session scratchpad, which sits under the primary checkout's `tmp/`. Write in the worktree's `tmp/` instead; the shared `.git/info/exclude` lists `/tmp/`, so it is ignored. Bash may write in the primary's `tmp/`.
  - This host's `tail` (uutils) accepts `-1` with one file but refuses it with two; use `tail -n 1`.
  - `python3` on `PATH` is `JuniperCascor1`'s interpreter. Run helpers with it and build venvs from it, but never install into it.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main            # this handoff's PR at or near the top
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.23 and 1.15.8
python3 util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py --check; echo $?    # 0 until v1.15.9 lands
python3 -I util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py --python /opt/miniforge3/envs/JuniperCascor1/bin/python; echo $?   # 0; the first run builds a venv under tmp/2026-10-29-mnist-schema-probe/
python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.13.0; echo $?    # 0
python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.12.0; echo $?    # 1: the control fails 4 checks
gh issue view 778 --repo pcalnon/juniper-canopy --json state,updatedAt    # OPEN until a canopy session lands it
grep -n 're-probed against PyPI on\|juniper-cascor 0.13.0' /home/pcalnon/Development/python/Juniper/AGENTS.md   # :206 says 2026-10-29; :240 the 0.13.0 bullet
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-cascor/json'))['info']['version'])"   # 0.13.0 until a newer cascor
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" | grep -n 'image: ghcr.io/pcalnon/juniper-cascor:'   # two lines, both 0.12.0, until a deploy bump
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-data/json'))['info']['version'])"     # 0.17.1 until R-DATA-2
gh run list --repo pcalnon/juniper-canopy --workflow juniper-data-schema-drift.yml --limit 3    # success until juniper-data's next release
bash util/recurrence_env_preflight.bash --python /opt/miniforge3/envs/JuniperCascor1/bin/python   # REFUSED (2 findings) until W0.1; read-only
wc -l ~/.local/state/juniper-experiments/index.jsonl                                            # 482 until the owner rules
grep -c 'def compute_classification_accuracy' /home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/lifecycle/classification_metrics.py   # 1 since 2026-10-29 20:48:58Z
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main               # e8e8bf4d... until the primary moves again
```

## Git state

- **This worktree** (`cosmic-puzzling-lovelace`) is on `worktree-cosmic-puzzling-lovelace` at `c5350c98`. `origin/main` was `86e6d6d1` at 21:13Z: #2385, the backup arc, touched only its own plan doc.
- This handoff's PR carries the worktree's uncommitted copies of the four files below. It is uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored scratch** in this worktree is none of it the only copy of a record:
  - `tmp/y1/`:
    - the fetch scripts and source copies;
    - the first probe pieces and the issue body;
    - the PyPI probe and the `[servers]` dry-run report (`servers-0.11.3-report.json`);
    - the negative and classifier harnesses;
    - the in-worktree `AGENTS.md` backup.
  - `tmp/2026-10-29-mnist-schema-probe/`: the probe's venv, the wheel and the fetched canopy files.
  - `tmp/validation-{a,b,c}/`: the reviewers' scratch.
- The copies that must outlive this worktree are in the primary checkout's `juniper-ml/tmp/2026-10-29-parent-agents-md-backups/`.

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.8);
  - `util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py` (new);
  - `util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py` (new);
  - this file (new).
- **Outside any repo**:
  - `/home/pcalnon/Development/python/Juniper/AGENTS.md` (unversioned): `:6`, `:206` and `:240-248`;
  - auto-memory `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block and its description). This session did not change `MEMORY.md`.
- **On GitHub**: juniper-canopy#778 (new issue; its body was later edited to correct the change list and name this PR).
- **Referenced, not changed**:
  - the superseded handoff (above) and the flood-3 handoff `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md`;
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.23: `:711`, `:712`, `:972`);
  - `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (`:43`, `:1304`, `:1364`);
  - `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (flood-3's, per the coordination split: that arc keeps it, its handoff, and its wheel-import probe);
  - canopy `main`'s `src/dataset_schema.py`, `src/model_registry.py`, `src/backend/recurrence_request.py`, `src/tests/unit/test_recurrence_request.py`, `src/tests/regression/test_restart_modal_restages_what_it_shows.py`, `util/ad-hoc/2026-10-26_capture_published_generator_schemas.py`, `util/check_juniper_data_generator_schemas.py` and `.github/workflows/juniper-data-schema-drift.yml`;
  - juniper-cascor `main`'s `src/api/lifecycle/manager.py`, and the cascor primary's `.git/logs/refs/heads/main`;
  - juniper-data `v0.17.1`'s `juniper_data/generators/mnist/generator.py` and `params.py`;
  - `util/experiment_stack.bash` (`:61-74`, `:171`);
  - `util/ad-hoc/2026-10-28_consolidated_plan_v1_15_7_cascor_0_13_0_published.py` and `util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py`;
  - `reference_cascor_primary_frozen_while_any_stack_imports_it.md` (auto-memory);
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
