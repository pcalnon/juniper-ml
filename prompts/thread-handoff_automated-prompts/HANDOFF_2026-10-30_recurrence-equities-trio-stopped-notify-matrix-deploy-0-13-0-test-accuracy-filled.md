# Thread Handoff — Recurrence × Equities: the trio stopped, the notify matrix and the cascor 0.13.0 deploy pin merged, `test_accuracy` filled; the plan revisions are next

**Date**: 2026-10-30 UTC (this host's clock is local time, UTC−5)
**Session**: `6f4d37` (`ListAgents` name `recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0`), the Linux host, worktree `.claude/worktrees/declarative-snuggling-sparrow`. Commits are signed only through the API (`util/open_signed_pr.py`), never `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md` (landed by juniper-ml#2386). Start from this file. Its item 1 passed. Of its owner items, this session acted on four, each on the owner's word: the index row, the trio stop, the notify matrix and the deploy pin. Its follow-up 3.2, the `test_accuracy` run, is done. Everything else is carried below.

---

## Goal

Continue the recurrence × equities arc (P12 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.15.8 on `main`). **The next step is the plan revisions this session did not write**:
- consolidated **v1.15.9**;
- recurrence **v1.7.24** (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`).

Each is written with an edit script under `util/ad-hoc/` that has `--check`, in the pattern of `util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py`. After that come the owner's items, then the follow-ups.

## Completed this session (each probed here)

- **The predecessor's post-merge re-check passed** (2026-10-29 22:43–22:50Z).
  - ml#2386 is `110d5e40` on `main`, and the plans read 1.7.23 / 1.15.8.
  - v1.15.8's `--check` exits 0, and `util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py` exits 0 on a freshly built venv.
  - canopy#778's body names ml#2386 and the probe.
- **The owner answered about 9.6 h after the question.** Every fact below was re-probed after the answer.
- **Index correction row 483** (owner: "Append 'failed'").
  - `util/ad-hoc/2026-10-30_index_correction_row_failed.py` (new; `--check`) appended it at 08:25:05Z to `~/.local/state/juniper-experiments/index.jsonl`: run `20261003T091414Z-4ba6`, outcome `failed`, `corrects: {line: 482, outcome: degraded}`.
  - Rows 477 and 482 are byte-identical to the pre-append copy, `juniper-ml/tmp/2026-10-30-recurrence-equities-y2/index.jsonl.before-row-483` (sha256 `3e559f0d…`).
  - The script was tested on copies first: wrong base → 1; second run → "already applied"; a partial last line → 1; a missing file → 2.
- **The canopy E2E trio is stopped** (the owner: "i don't think the PR was mine. let's stop the :8202 stack", then "Trio via --down").
  - The 2026-10-29 20:48:58Z primary pull's actor is still unknown.
  - `:8202` was the canopy E2E arc's trio cascor: data `:8101` pid 2856834, cascor pid 2857489, canopy `:8051` pid 2858037; guard dir `~/.local/state/juniper-experiments/e2e-trio-2026-09-22/`. It also served the service-mode legs `:8052` / `:8053`.
  - The canopy session (`canopy-phase16-round19-frozen-round20-next`) was told first. It replied "No hold needed", with four handling points, all met.
  - `JUNIPER_E2E_RUN_DIR=<guard> bash …/juniper-ml/util/isolated_stack.bash --down` ran from the juniper-ml primary at 08:25:52Z, after a `--dry-run`.
  - All five pids were gone by 08:26:12Z: the three listeners, plus cascor's forkserver 2904571 and resource_tracker 2904570. 8051 / 8202 / 8101 / 8211 are free, and the guard's three pid files are removed.
  - The logs are in `juniper-ml/tmp/2026-10-30-trio-stop/`, with `MANIFEST.tsv` (sha256) and `README.md`. The data log existed only as `/proc/2856834/fd/1` and was read before the stop; the cascor (575 MB) and canopy logs were copied after every holder exited, with `cmp` exit 0. The canopy session re-hashed all three.
  - **My deviation**: I ran `--down` about 3.5 min after my notice, not the "about 5 minutes / 08:30Z" I stated. The peer's no-hold reply had arrived, but I had not read it yet.
  - The four 2026-10-10 legs (`:8052`, `:8053`, `:8058`, `:8059`) are still up. `:8052` / `:8053` now have no cascor and no data.
- **juniper-data#501 is merged** (2026-10-30 08:37:14Z, `95163c47`): `notify-consumers.yml`'s matrix is `[juniper-recurrence, juniper-canopy]`.
  - The diff proposed in canopy#777's body missed the hidden pin at `juniper_data/tests/unit/test_notify_consumers_dispatch.py:438`, which asserts `[REPO_NAME]`. It now asserts `CONSUMERS`.
  - Tests: 27 passed. The control (the new test on the old workflow) exits 1. ruff 0.15.2 is clean.
  - The 0.17.1 `workflow_dispatch`, run 41027844552, passed on both legs. canopy's `juniper-data Schema Drift` run 41027857909 and recurrence's bench run 41027858881 both succeeded. **So `CROSS_REPO_DISPATCH_TOKEN` covers canopy.**
- **juniper-deploy#266 is merged** (08:41:07Z, `3070bd7e`): cascor 0.12.0 → 0.13.0 at `docker-compose.yml:233` / `:427` and `k8s/helm/juniper/values.yaml:120`.
  - GHCR index `sha256:721417527c4f…`, with amd64 and arm64 both labelled revision `61a67c53` (`v0.13.0`).
  - The pulled image reports cascor 0.13.0, observability 0.4.1, service-core 0.7.1 and data-client 0.6.0, on Python 3.14.10.
  - `scripts/verify_published_images.py --fail-on-stale` exits 0; the control on the old pins exits 1.
  - CI was all green, the helm tests included. They cannot run in this sandbox (see the rules).
- **`test_accuracy` fills.**
  - `util/ad-hoc/2026-10-30_test_accuracy_731_smoke_suite.yaml` (new) is one spiral-smoke cell on the cascor primary's `src/` at `e8e8bf4d`, run with `JUNIPER_EXP_PROJECT_DIR=/home/pcalnon/Development/python/Juniper`.
  - Suite `test-accuracy-731-smoke-20261030T084056Z`, run `20261030T084056Z-0ac7`: `artifacts/results/metrics_final.json` has `eval_metrics.final.split == "test"` and `accuracy == 0.575`, which equals `aggregate.csv`'s `test_accuracy`. The run took 27 s, its index row is 484, and the stack is torn down.
  - **APD-ML-002's close condition ("until that column exists") is met by evidence.** The close itself awaits the owner.
- **Arc memory** `project_recurrence_equities_p0_arc_2026-10-04.md`: a new state block and a new description. `MEMORY.md` is unchanged.

## Remaining work, in order

1. **Post-merge re-check of this handoff's PR.**
   - On `main`, both new `util/ad-hoc/2026-10-30_*` files and this handoff are present.
   - `python3 -I util/ad-hoc/2026-10-30_index_correction_row_failed.py --check` exits 0.
   - Write this PR's number into the arc memory's state block.
2. **Plan revisions** (grep the whole plan for each item; every consolidated-plan line has at most 512 characters).
   - **Consolidated v1.15.9.**
     - deploy#266 meets §8's juniper-deploy row (`:1232` in v1.15.8, "The pin PR is opened once GHCR serves the image") and P4-39 / P4-40, under the owner's ruling that 0.13.0 counts for R-CASCOR's pin route despite carrying no F-S10 fix.
     - XC-P12 action 4, §4's P6 line and §5's R-CASCOR sub-bullet now have a filled `test_accuracy`. The trio stop goes under O13, at `:791` / `:793`. data#501 and the token result go wherever the plan carries the notify-matrix item. Index row 483 is new.
   - **Recurrence v1.7.24.**
     - `:711` / `:972` (row 482's `degraded`), and `:712` (the `failed` question is answered: row 483).
     - At `:712`, cite canopy#778 in the "Left out of juniper-canopy#776" sentence.
     - APD-ML-002's lines.
3. **The owner's items** (surface them; do not act on them).
   - **Close APD-ML-002**: the five touches in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (`:43`). `:1304` / `:1364` are stale ("unreleased").
   - **The parent `Juniper/AGENTS.md` cascor 0.13.0 bullet** (`:240-248`) says "juniper-deploy still pins the 0.12.0 image", which is stale since deploy#266. It is unversioned and shared: get the owner's approval, back it up to the primary's `tmp/`, and check its sha256 before the edit.
   - R-DATA-2 (juniper-data 0.17.2; W5.7 is a default change; canopy#777's drift job goes red then by design); juniper-config-tools 0.2.0 (backfill `[Unreleased]` first); W0.1's service-core half (`util/recurrence_env_preflight.bash` still REFUSES `JuniperCascor1`, 2 findings; never modify that env); §6 A1 / A9.
   - juniper-canopy#778 needs a canopy session.
4. **Follow-ups.**
   - `save_model`'s live run (juniper-ml#2316) is BLOCKED on W0.1.
   - The canopy worktrees `…declared-param-staging-735-736…` and `…juniper-data-schema-drift-check…`, and the juniper-ml worktrees `keen-popping-wilkes` and `cosmic-puzzling-lovelace`: owner or canopy session. Check each one's `tmp/` before removing it.
   - `MEMORY.md` is about 20.9 KB, over the 20 KB target; the excess is other arcs'.

## Rules that held this session

- **Re-probe after a long owner wait.** Here the wait was 9.6 h.
- **Notify a peer before stopping its stack, and keep the window you state.** I did not keep it.
- **A log that is deleted on disk survives only through `/proc/<pid>/fd`, so copy it before the stop.** Copy the live logs after every holder has exited, children included.
- **A proposed diff is not a complete change.** grep the repo for hidden test pins: `[REPO_NAME]` was one.
- **Count, do not estimate.** I wrote "52 characters" for a 55-character path.
- **A control that must fail:** the old workflow fails the new test, and the old pins fail `--fail-on-stale`.
- **Tooling on this host**:
  - `docker run` and snap `helm` fail on AppArmor (`/sys/kernel/security` is hidden). docker takes `--security-opt apparmor=unconfined`; helm runs only in CI.
  - The worktree guard refuses `git -C <primary>`, `awk` programs, `sed` with a computed operand, and `python -m pytest` or `bash` inside complex constructs. Write a script, then run it plainly.
  - `util/safe_merge.py` and `util/wait_for_checks.py` take a bare `--repo`. Run `safe_merge` in the background and read its `MERGED` line.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -5 origin/main
git grep -n -e '^- \*\*Version\*\*' origin/main -- notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.7.23 and 1.15.8 until the revisions
python3 util/ad-hoc/2026-10-29_consolidated_plan_v1_15_8_cascor_primary_carries_731.py --check; echo $?   # 0 until v1.15.9 lands
python3 -I util/ad-hoc/2026-10-30_index_correction_row_failed.py --check; echo $?   # 0: line 483 corrects 482
wc -l ~/.local/state/juniper-experiments/index.jsonl                                 # 484 or more
gh api repos/pcalnon/juniper-deploy/contents/docker-compose.yml -H "Accept: application/vnd.github.raw" | grep -n 'image: ghcr.io/pcalnon/juniper-cascor:'   # both 0.13.0
gh api repos/pcalnon/juniper-data/contents/.github/workflows/notify-consumers.yml -H "Accept: application/vnd.github.raw" | grep -n 'repo: \['   # [juniper-recurrence, juniper-canopy]
ss -ltnpH | grep -E ':(8051|8052|8053|8058|8059|8101|8202) '                          # only the four legs
cut -f1,2 /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/2026-10-30-trio-stop/MANIFEST.tsv
grep -n 'juniper-deploy still pins' /home/pcalnon/Development/python/Juniper/AGENTS.md   # stale until the owner approves the edit
cat /home/pcalnon/Development/python/Juniper/juniper-cascor/.git/refs/heads/main     # e8e8bf4d... until the primary moves
```

## Git state

- **This worktree** (`declarative-snuggling-sparrow`) is on `worktree-declarative-snuggling-sparrow` at `110d5e40`.
- This handoff's PR carries the worktree's uncommitted copies of three files, uploaded through `util/open_signed_pr.py`, so the local branch never moves.
- **Gitignored scratch** is in `tmp/s1/` and `tmp/2026-10-29-mnist-schema-probe/`: the fetch scripts, the tarballs, the PR bodies, the test and verify logs, and the ruff venv. None of it is the only copy of a record. The copies that matter are in the primary's `juniper-ml/tmp/2026-10-30-trio-stop/` and `juniper-ml/tmp/2026-10-30-recurrence-equities-y2/`.

## Documents created or modified this session

- **juniper-ml, via this handoff's PR**: `util/ad-hoc/2026-10-30_index_correction_row_failed.py` (new), `util/ad-hoc/2026-10-30_test_accuracy_731_smoke_suite.yaml` (new), and this file (new).
- **juniper-data#501**: `.github/workflows/notify-consumers.yml`, `juniper_data/tests/unit/test_notify_consumers_dispatch.py`, `docs/REFERENCE.md`, `docs/ci_cd/CICD_MANUAL.md`, `docs/ci_cd/CICD_REFERENCE.md` and `CHANGELOG.md`.
- **juniper-deploy#266**: `docker-compose.yml`, `k8s/helm/juniper/values.yaml` and `CHANGELOG.md`.
- **Outside any repo**:
  - `~/.local/state/juniper-experiments/index.jsonl` (rows 483 and 484 appended);
  - the trio guard's three pid files (removed by `--down`);
  - `juniper-ml/tmp/2026-10-30-trio-stop/` and `juniper-ml/tmp/2026-10-30-recurrence-equities-y2/` (new);
  - the auto-memory `project_recurrence_equities_p0_arc_2026-10-04.md`.
- **Referenced, not changed**:
  - the superseded handoff (above) and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_canopy-phase16-linux-host-checks-recorded-items-35-37-next.md` (h1025, in the worktree `distributed-giggling-clarke`);
  - both plans and `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`;
  - `util/isolated_stack.bash`, `util/experiment_stack.bash`, `util/experiments/run_suite.py` and juniper-cascor's `conf/experiments/spiral-smoke.yaml`;
  - `/home/pcalnon/Development/python/Juniper/AGENTS.md`.
