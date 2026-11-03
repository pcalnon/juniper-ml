# Handoff: Cursor flood-3 arc, the owner's fourth continuation. The pytest cap is dropped, every low row is fixed, and the ruled cleanup is done; only owner calls remain

**Date**: 2026-11-01 (UTC)

**Arc**: The Cursor flood-3 disposition and its follow-ups. This stretch is the owner's request of 2026-11-01: "continue from handoff: …HANDOFF_2026-10-30_flood3-third-continuation-sarif-everywhere-cleanup-done.md", with "merge approval granted".

**Record**: `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, cited below as `…FLOOD-3-DISPOSITION.md`. This handoff's PR makes the record's eleventh update: the header, §4, §6, §8 and §9.

**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_flood3-third-continuation-sarif-everywhere-cleanup-done.md`, cited below as `HANDOFF_…cleanup-done.md`.

**Host**: the Linux host.
- **This session:** the same process as the predecessor's session (pid 945136, `--session-id 719f66a2`), its context cleared by `/clear`; worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/proud-crunching-neumann`, locked by that pid.
- **No other session continues this arc.**
- **Commits** go only through GraphQL `createCommitOnBranch`: `util/open_signed_pr.py` and `util/push_signed_commit.py`.

**Git status**: the worktree's branch, `worktree-proud-crunching-neumann`, is at `d6b29bb5`, behind `origin/main`; no commit is made locally. This PR's two files were uploaded from the worktree's uncommitted copies. The predecessor's four files are also uncommitted there, identical to `main`'s.

---

## Goal

Nothing is owed unless the owner asks. What remains is owner calls (Remaining work, item 1) and the cleanup inventory, whose removals each need an owner signal (item 2).

## Completed (verified on GitHub, PyPI or the host)

- **The owner's rulings of 2026-11-01**, in one dialog:
  - **The worktrees:** remove `prancy-whistling-knuth`, "The six 10-30 PR worktrees" and "Today's cascor#738 worktree". `iridescent-sniffing-snail` was offered and not chosen.
  - **The low fixes:** all four, namely cascor's HDF5 load benchmark (new), cascor's SARIF wording, data's checkout pin and `make coverage`'s gate.
  - **Promoting the claim-backing scripts:** "Not now".
- **The PRs, all merged under this session's approval:**

  | PR | Squash | What it did |
  |---|---|---|
  | juniper-cascor#738 | `88cccf5e` | dropped the smoke job's `pytest<9.2` cap: pytest-benchmark 5.3.1 (PyPI 2026-11-01 03:32Z) supports pytest 9.2 |
  | juniper-cascor#739 | `9fb75198` | the HDF5 load benchmark times real loads, and a failed harness fails the job; the SARIF comment and survey docstring stop claiming 165 of 165 |
  | juniper-data#503 | `d83ca589` | `make coverage` runs CI's per-file gate (`juniper-coverage-gap-map --enforce`); `agents-md-touch-up.yml` pins `actions/checkout` to `3d3c42e5` |
  | this PR | | the record's eleventh update and this file |

  - **#738.** A local probe on pytest 9.2.0 errored with pytest-benchmark 5.3.0 (the control) and passed with 5.3.1. The nightly dispatched on its branch (run 41338629019) printed `pytest 9.2.0 | pytest-benchmark 5.3.1` and `153 passed`.
  - **#739.** The benchmark was found on 2026-11-01 in `main`'s nightly 41267421888, which refused 12 loads (`Output weights shape mismatch`). Locally, a mutant without the resize raised and exited 1. Its dispatched nightly (run 41340867452) logged no refusal.
  - **#503.** Its first push failed `Memory Budget`: `AGENTS.md` reached 27,182 against a 26,965 ceiling. The second commit kept a pointer, +12 characters with 32 to spare (§6). The full local run exited 0 in 114 s with `Enforcing gate: PASS`, and without the tool on `PATH` the script exits 2 before the tests.
- **The dialog misnamed CI's per-file gate.** It said `scripts/check_module_coverage.py`; the gate is `juniper-coverage-gap-map --enforce`. #503 wired in the real one, which is what the ruling asked for (§8).
- **APD-ML-002** was closed by another session on the owner's word (juniper-ml#2397), so `HANDOFF_…cleanup-done.md` item 1.1 needs nothing more.
- **The cleanup.** The ledger is `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-01/`: `REMOVED.tsv` (its header holds the gates), `MANIFEST.tsv` and `_work/`.
  - **Removed:** eight worktrees and eight local branches. They were `prancy-whistling-knuth`, the six 2026-10-30 PR worktrees (data#502, canopy#781, data-client#249, cascor-client#189, cascor-worker#220, cascor#737) and #738's.
  - **Gates:**
    - the holder check: all eight clear, with this worktree as a positive control that read HELD;
    - every PR merged and its head branch gone (404);
    - the six HEADs equal their PRs' final heads, and prancy's `110d5e40` and #738's base `012d4737` are on `main`;
    - #738's two uncommitted files' blobs are in `main`'s tree.
  - **The branches:** five were deleted with `-d`. cascor's `docs/pytest-ini-stale-references` needed `-D`, after its tip matched #737's head, because this session's `fetch --prune` had removed its stale remote ref.
  - **Kept:** prancy's `tmp/`, 461 files (32 MB), with 0 bad re-hashes.
    - Skipped as regenerable: `venv-cascor-probe/` (950 MB), `venv-bandit/`, `venv-pytest92/` and two `__pycache__/`.
    - Nothing outside `tmp/` was unique in any of the eight.
    - `diff -rq` is clean, after four empty directories were recreated in the copy.

## Remaining work

1. **Owner calls.** A session acts on none of these without the owner's word, and on 1.5 not even then.
   1. **`CODECOV_TOKEN` in the Dependabot stores** of juniper-data and juniper-canopy. Only the owner can add it. `python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py` re-reads the stores (GET only): `dependabot=-` in all nine rows on 2026-11-01.
   2. **The stopped duplicate's own worktree,** `.claude/worktrees/iridescent-sniffing-snail`: HEAD `c77b7be5`, on `main`, unlocked, `tmp/` 12 KB (`session-0f840224/`). Offered on 2026-11-01 and not chosen.
      - Route B (the gates, then `git worktree remove` and `git branch -d worktree-iridescent-sniffing-snail`) keeps the session record.
      - Route A (`claude rm 2fc3f4e1`) deletes both; check the branch afterwards.
      - Either way, preserve its `tmp/` first.
   3. **SHA-pin the other seven copies of `agents-md-touch-up.yml`?** juniper-ml, canopy, cascor, data-client, cascor-client, cascor-worker and deploy all use `actions/checkout@v7.0.1` by tag, read from each repository's `main` on 2026-11-01. #503 pinned juniper-data's alone.
   4. **Promote the ledgers' claim-backing scripts?** "Not now" (2026-11-01). The candidates are 59 scripts under `…/tmp/worktree-cleanup-2026-10-30/` and 3 under `…-2026-10-29/`; no list marks which back a claim.
   5. **Host environments**, the owner's own action, never a session's.
      - `JuniperCanopy1` holds juniper-observability 0.4.0 and juniper-service-core 0.5.0, below canopy's floors (two local test failures).
      - `JuniperCascor1`'s editable install still reports juniper-cascor 0.11.0, so `test_version_matches_pyproject` fails locally.
      - `JuniperData` has no `juniper-ci-tools`, so its `make coverage` now stops before the tests with the install line (`pip install "juniper-ci-tools>=0.9.0,<0.10.0"`).
2. **Cleanup inventory (this pass).** Nothing here is removed; each needs an owner signal.
   - **The two centralized worktrees made after the ruling.** Each is on its PR's branch at the base it is named for, with the PR's changes uncommitted. The local `-d` branch check therefore needs the uncommitted files' blobs on `main` (as #738's were), plus the holder check.
     - `worktrees/juniper-cascor--fix--hdf5-load-benchmark-and-sarif-survey-wording--20261101-1308--88cccf5e` (#739, merged). Ignored: `logs/` from this session's test runs, and `__pycache__/`.
     - `worktrees/juniper-data--fix--make-coverage-gate-and-checkout-pin--20261101-1316--8e710d20` (#503). Ignored: `.coverage`, `reports/`, `.hypothesis/` and `.pytest_cache/`, from the 114 s run, and `__pycache__/`.
   - **This session's worktree,** `.claude/worktrees/proud-crunching-neumann`, once pid 945136 has ended and its lock is gone.
     - Preserve three directories first:
       - `tmp/session/`, the predecessor's (6.8 MB);
       - `tmp/session2/`, this session's (25 MB): the PR and commit bodies, the CI job logs, the benchmark runners and their logs, the `PIPESTATUS` probe, `venv-ci-tools/`, the cleanup listings and the merge logs;
       - `tmp/factcheck/` (88 MB).
     - The pytest-benchmark probe and its two venvs are in this session's scratchpad, `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-proud-crunching-neumann/94f3e0a5-1f09-4c71-a2dc-6f27b0af39ba/scratchpad/`, under the primary's `tmp/`, so removing the worktree does not delete them.
     - The branch is at `d6b29bb5`, on `main`.
   - **Keep until the owner says otherwise:**
     - `…/tmp/release-cascor-0.13.0/`;
     - `…/tmp/worktree-cleanup-2026-10-26/`, `-27/`, `-28-canopy-p12/`, `-29/`, `-30/` and `-2026-11-01/`;
     - `…/tmp/flood3-deleted-branches.tsv`;
     - 89 `cascor-test-snapshots-*` directories in `…/tmp/`. Five are new on 2026-11-01, made by this session's cascor test runs.

## Key context and traps

- **Merge approval is per session** (memory `feedback_headless_merge_approval_policy.md`). This file cannot carry it.
- **Never attach or resume `2fc3f4e1`.** `claude attach` would resume a session that believes it holds merge approval.
- **The cascor primary:** never pull, check out or edit it from a session. Run `ss -ltnp` and `util/ad-hoc/2026-10-29_worktree_holder_check.py` before relying on its state.
- **juniper-ml#2360** (the `/tmp` arc) is OPEN, CONFLICTING, with auto-merge armed. Its re-sync must keep `main`'s side of its five shared files. juniper-ml#2396 (the owner's, 2026-10-31) is open and armed; it is not this arc's.
- **Measure a budgeted `AGENTS.md` before pushing:** `python3 -I util/memory_budget_check.py --base-ref <base> --trailers-file <empty file>` in the repository (§6). juniper-data's now has 32 characters of headroom.
- **A timed call that fails quietly is measured as if it worked.** Check its result once before timing it (§6).
- **Under `set -e`, `eval` in a pipeline reports any failure as 1** (bash 5.3.9). It is still non-zero (§6).
- **`fetch --prune` in a primary turns a squash-merged branch's `-d` into a refusal.** `-D` is then right only after the tip equals the PR's final head.
- **Count a step's failures by an effect, never by its API `conclusion`** (§6).
- **Worktree isolation refuses some shell shapes:**
  - `git -C` into this repository's shared checkout or its sibling `.claude/worktrees/`;
  - variables, loops or `$(…)` around git or gh, and a `python3 -c` that runs git;
  - `env -u … PATH=…:$PATH bash …`, and `bash <file>` on a script it cannot read;
  - arithmetic on variables inside `bash -c`.

  The Write tool also refuses the primary checkout's `tmp/`, the scratchpad included, so this session wrote its files to the worktree's `tmp/session2/`.
- **`util/safe_merge.py` and `util/wait_for_checks.py` take a bare `--repo` name.** Read the `MERGED` line, not the exit status. A background `safe_merge` of a PR you are about to push to should be stopped first.
- **Release dates are UTC.** No release is pending in this arc.

## Verification

Run these first. On any mismatch, stop, re-probe and report to the owner rather than act.

```bash
gh pr view 738 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 88cccf5e
gh pr view 739 --repo pcalnon/juniper-cascor --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'   # MERGED 9fb75198
gh pr view 503 --repo pcalnon/juniper-data --json state,mergeCommit --jq '"\(.state) \(.mergeCommit.oid[0:8])"'     # MERGED d83ca589
gh api repos/pcalnon/juniper-cascor/contents/.github/workflows/scheduled-tests.yml -H "Accept: application/vnd.github.raw" | grep -c 'pytest<9.2'   # 0
python3 -I util/ad-hoc/2026-10-29_codecov_token_secret_census.py                                                 # dependabot=- in all nine rows until the owner acts (item 1.1)
git worktree list --porcelain | grep -E '^worktree .*(iridescent-sniffing-snail|prancy-whistling-knuth)$'        # iridescent only
ls /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-01/                          # MANIFEST.tsv REMOVED.tsv _work prancy-whistling-knuth
```

## Residue: the remaining work of `HANDOFF_…cleanup-done.md`, item by item

1. **Owner calls:**
   - 1.1, APD-ML-002: closed by another session (juniper-ml#2397).
   - 1.2, Codecov in the Dependabot stores: still open (item 1.1 here).
   - 1.3, `iridescent-sniffing-snail`: offered, not chosen (item 1.2 here).
   - 1.4, `prancy-whistling-knuth`: removed, its evidence kept.
   - 1.5, the three low items: fixed (#739, #503), with a fourth, new one fixed in #739.
   - 1.6, promoting scripts: "Not now" (item 1.4 here).
   - 1.7, host environments: unchanged, plus `JuniperData`'s missing tool (item 1.5 here).
2. **The pytest cap:** dropped (#738).
3. **The cleanup inventory:**
   - its six centralized worktrees are removed;
   - "This session's worktree" carries on as item 2 here, because the same process continued;
   - the keep list is carried, with this pass's ledger added.

**Its traps** are carried under Key context, except the HTTP 502 survey trap, the preservation traps and the torch `LD_LIBRARY_PATH` trap. Those three live in `…FLOOD-3-DISPOSITION.md` §6 and in the auto-memory, and this pass did not need them.

## Documents created or modified

- **This file's PR:** this file (new) and `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`.
- **Other PRs:**
  - juniper-cascor#738: `.github/workflows/scheduled-tests.yml`, `CHANGELOG.md`;
  - juniper-cascor#739: `src/tests/scripts/run_benchmarks.bash`, `.github/workflows/ci.yml`, `util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py`, `CHANGELOG.md`;
  - juniper-data#503: `util/run_coverage.bash`, `Makefile`, `AGENTS.md`, `docs/REFERENCE.md`, `.github/workflows/agents-md-touch-up.yml`, `docs/ci_cd/CICD_REFERENCE.md`, `CHANGELOG.md`.
- **Unversioned:** `/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-cleanup-2026-11-01/` (`MANIFEST.tsv`, `REMOVED.tsv`, `_work/`, the preserved files).
- **Unversioned auto-memory** (`/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/`), which every concurrent session reads:
  - `project_worktree_branch_cleanup_playbook.md`: `--prune` turns a squash-merged branch's `-d` into a refusal, and `-D` is right only after the tip equals the PR's final head;
  - `reference_verification_discipline_hub.md`: a timed call that fails quietly is timed as if it worked.
- **Referenced:** `HANDOFF_…cleanup-done.md`; `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (APD-ML-002).
