# Handoff: run_tests rollout -- the engine, the ci-tools 0.10.0 proposal and its notes landed; the Overtoad's Release cut is next, then the two conversions

**Date**: 2026-11-27 (written about 01:05Z, which is 2026-11-26 19:05 CST)
**From**: session 9c19e5aa, in worktree `juniper-ml/.claude/worktrees/agile-purring-pixel`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_run-tests-rollout-data-client-copy-landed-engine-extraction-ruled-next.md`.
All six of its verification commands passed at about 21:30Z on 11-26, and its traps still stand.
**Memory**: `project_run_tests_rollout_2026-11-24.md`
**The plan**: § 4.3 of the proposal, `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md`.
Its steps 1 and 2 are done, and step 3 is done except for the Overtoad's Release cut. Steps 4 and 5 remain.

---

## Goal

Continue § 4.3 of `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md`:

1. Once the Overtoad has cut the `juniper-ci-tools-v0.10.0` Release and approved its `pypi` gate, verify the
   published wheel.
2. Convert juniper-recurrence and juniper-data-client to thin specs pinned `juniper-ci-tools>=0.10.0,<0.11.0`.
3. Convert the seven other repos.

**Merge approval does not carry over.** The Overtoad granted "merge approval for this work arc" to session
9c19e5aa only, at about 21:31Z on 11-26. Ask before merging anything. The Release cut is a deploy, and the
Overtoad does it.

## Completed (this session)

- **juniper-ml#2682 MERGED** at 2026-11-26 23:27:06Z as `b91cecbc`: the engine. It squashed one signed commit,
  `d8b39d8a`, with its 160-symbol waiver intact, and Post-Merge Main Verification passed on `b91cecbc`. It holds:
  - `juniper-ci-tools/juniper_ci_tools/run_tests.py`. The public API is `__all__`: `RepoSpec`, `EnvFlag`,
    `unittest_lane()`, `step_lane()`, `job_lanes()`, `workflow_stem()`, `JOB_ID`, `Step`/`Job`/`Lane`,
    `discover`, `build_parser`, `main` and the exit codes.
  - `juniper-ci-tools/tests/test_run_tests.py`: 93 in-process tests on three fake checkouts (the ml, dc and rec
    shapes). The engine is at 98% coverage and the package pool at 97.6%.
  - juniper-ml's `util/run_tests.py`, now a thin spec that loads the in-repo engine **by path**, with its
    real-workflow and docs tests in `tests/test_run_tests.py`.
  - `docs/REFERENCE.md` 0.6.87, `juniper-ci-tools/README.md`, both CHANGELOGs, and three `util/ad-hoc/`
    tools: `2026-11-26_run_tests_engine_equivalence.py`, `..._run_tests_engine_mutation_check.py` (41 of 41
    killed) and `--message-file` on `..._probe_sequence_safety_screens.py`.
- **juniper-ml#2684 MERGED** at 2026-11-27 00:00:02Z as `7e485e9a`: the train's proposal
  (`release/juniper-ci-tools-v0.10.0`).
  - `propose.py --execute` opened it: `pyproject.toml` and `_version.py` at 0.10.0, and the CHANGELOG
    `[Unreleased]` -> `[0.10.0] - 2026-11-26` move.
  - Its first run failed `test_ml_own_workflow_pins_admit_current` (`tests/test_env_drift_check_drift.py`):
    juniper-ml's own workflows pinned `<0.10.0`.
  - Fix-up `ed8a3271` (signed) widened all 14 pins in 10 workflows to `juniper-ci-tools>=0.9.0,<0.11.0` (ceiling
    only, the 7668ad30 precedent). It also widened the juniper-ml recipe in `conf/python_versions.yaml`, which
    `tests/test_python_version_matrix_drift.py` holds equal to ci.yml's tests job. That file did not exist at 0.7.0.
  - The worker and data recipes there mirror those repos' own CI and were left alone.
  - `ci.yml` (run 45914144906), the six package CIs and Post-Merge Main Verification all passed on `7e485e9a`.
- **juniper-ml#2686 MERGED** at 00:51:06Z as `6e271984`: the notes archive,
  `notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md` (branch `release-notes/juniper-ci-tools-v0.10.0`,
  signed `523560ac`).
  - `ceremony.py --dry-run` on `7e485e9a` classified the package `CEREMONY_PLANNED` (0.9.1 -> 0.10.0) and planned
    this exact PR, then the Release.
  - `util/ad-hoc/2026-09-12_ceremony_notes_preview.py --package juniper-ci-tools --version 0.10.0 --release-date
    2026-11-27 --released-version 0.9.1` rendered the notes, because the dry run does not print them. They equal
    `propose.py`'s draft except the date.
  - `archive_guard.py` said OK locally on its name-status before the PR was opened.
- **`util/ad-hoc/2026-11-26_widen_ci_tools_pin_ceilings.py`** (in this handoff's PR) does #2684's fix-up for the
  next ci-tools minor. It covers the workflows and the juniper-ml recipe only, never the floor, and refuses
  unless the counts match.
  - Replayed on `b91cecbc` with its defaults, it reproduces all 25 files at `7e485e9a` byte for byte.
  - On `main` now, `--old 0.11.0 --new 0.12.0` finds 14 + 1.

## Remaining work

### 1. The Release (the Overtoad's), then verification

- The command, from the juniper-ml primary. It writes only the primary's `tmp/`:
  ```bash
  cd ~/Development/python/Juniper/juniper-ml && git fetch origin
  git show origin/main:notes/releases/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md > tmp/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md
  gh release create juniper-ci-tools-v0.10.0 --repo pcalnon/juniper-ml --target 7e485e9ab990662436dc9d1126ca94d64b995836 --title "juniper-ci-tools v0.10.0" --notes-file tmp/RELEASE_NOTES_juniper-ci-tools_v0.10.0.md --latest=false
  ```
  This is the ceremony's own `create_release` argv, with `--target` set to the proposal's merge commit:
  - Its `ci.yml` is green, and the notes were rendered from its CHANGELOG, which is the ceremony's
    `--target-sha` contract.
  - `git diff 7e485e9a 6e271984 -- juniper-ci-tools/` is empty, so the wheel is the same either way.
  - Like 0.9.1's tag, it will not contain the archived notes file. The notes' links point at the CHANGELOG,
    which it does contain.
- The Release fires `publish-ci-tools.yml`: build, then TestPyPI, then a wait at the `pypi` environment gate for
  the Overtoad. A waiting gate can end at day 30 (memory `project_pypi_publish_workflow_dual_gate.md`), so state
  both dates when handing one over.
- Then verify the published wheel, not a checkout. In a `tmp/` venv, `pip download juniper-ci-tools==0.10.0
  --no-deps` must hold `juniper_ci_tools/run_tests.py`, with `__version__ == "0.10.0"` and `run_tests.__all__`.
  The PyPI CDN can lag a few minutes (memory `project_pypi_cache_lag_post_publish.md`).

### 2. Convert recurrence and data-client (§ 4.3 step 4), after 0.10.0 is on PyPI

- The prototype specs are kept in the juniper-ml primary's `tmp/run-tests-engine--agile-purring-pixel/`:
  `proto_dc_run_tests_engine.py` and `proto_rec_run_tests_engine.py`. Each reuses the old copy's help text and
  `OPT_IN`.
  - The conversion inlines the prototype and adds `try: from juniper_ci_tools import run_tests as rt`.
  - On `ImportError` it prints the pip command and exits 3 (§ 4.4).
- Recurrence's spec:
  - `marker="ci-recurrence-*.yml"` and `pyproject=False`, since it has no root `pyproject.toml`.
  - `job_lanes(workflows=("ci-recurrence-*.yml",), jobs=("test", "test-*"), name=rt.workflow_stem("ci-recurrence-"),
    optional={"test-*": ...}, groups=("packages",))`.
- Data-client's spec: `lanes=(rt.unittest_lane(), rt.job_lanes())`, `opt_in=OPT_IN`, `strip_suffix="-tests"`.
- Pin `juniper-ci-tools>=0.10.0,<0.11.0` wherever the runner's suite runs: data-client's unit-tests job and
  recurrence's `ci-tooling.yml`. The required check `Local test runner suite` is in recurrence's ruleset
  `juniper-recurrent-rules` (20634527).
- Prove each conversion with the equivalence tool. The before captures and the `cases_dc.txt` / `cases_rec.txt`
  lists are in the same kept directory:
  `python3 util/ad-hoc/2026-11-26_run_tests_engine_equivalence.py export|capture|compare`.
  Re-capture "before" from each repo's current `origin/main`, because the primaries lag.
- Each repo keeps its RealWorkflows and Docs tests against `rt` and `SPEC`, and drops its fake-checkout tests,
  which now live in ci-tools.

### 3. Then

- The seven, in the 2026-11-24 order. Section 2.3 of
  `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md` says what cascor, canopy
  and deploy need from the engine first: unset variables, canopy's 134-with-JUnit exit rule, deploy's port
  preflight. Each is a ci-tools change, so each needs a 0.10.x or 0.11.0 through the train. Its proposal needs
  the pin widening above.
- `MEMORY.md` is at about 22.4 KB against its 20 KB target (`feedback_memory_index_target_is_20kb.md`). It needs a
  pass that retires entries.

## Key context and traps (this session)

- **`propose.py` does not widen juniper-ml's own pins on ci-tools, so a minor's proposal fails its CI.** Since
  2026-11-15 the widening also covers the `conf/python_versions.yaml` recipe. Run
  `util/ad-hoc/2026-11-26_widen_ci_tools_pin_ceilings.py --old <ceiling> --new <next> --write` on the proposal
  branch and push the result as a signed commit pinned to its head. A train fix that moves the ceilings inside
  `propose.py` would retire this step.
- **To test a proposal's tree locally**, apply its diff to the worktree and remove it again afterwards:
  `git diff <base> <head> --output=tmp/x.patch`, `git apply`, run, `git apply -R`. The version-reading drift tests
  only see the bump that way.
- **`ceremony.py --execute` cuts the Release.** Use `--dry-run` for the plan and the preview script for the notes,
  and open the archive PR with `open_signed_pr.py`. The archive PR went BEHIND twice while it waited, and
  `safe_merge` re-synced it both times.
- **Python 3.11's unittest exits 0 ("Ran 0 tests") when `-k` matches nothing; 3.12 and later exit 5.** The
  engine maps it in `Engine.run_job`. `/usr/bin/python3.11` (3.11.18) is on this host: a venv under a worktree's
  `tmp/` with `pip install -e "juniper-ci-tools/.[test]"` reproduces the leg.
- **The symbol-loss waiver had to name all 160 moved symbols**, because a `*` wildcard is refused. They go on one
  `Allow-Symbol-Loss:` line in the last paragraph of a single commit.
  - Rebuild a PR with the temp-branch sequence, which keeps it open with one commit:
    1. `push_signed_commit.py` to `tmp/<name>` at `main`;
    2. `PATCH` the PR ref with `force=true`;
    3. `DELETE` the temp ref.
  - Probe it first with `..._probe_sequence_safety_screens.py --message-file <the exact commit message>`.
- **`main` moved twice during #2682.** `util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py --worktree .`
  carried the uncommitted edits across. Check `git log HEAD..origin/main` before every upload.
- **The command guard** refuses a heredoc combined with `cd`, `$(...)` around git, and loops over `.github`.
  Write the script to a file and run each command alone.
- **G-TMP misreads a `/tmp/` path fragment in prose as a literal.** Reword it.
- **Local-only failures:**
  - the three `TMPDIR` rows in the regression group: `test_workflow_script_paths.py`,
    `test_e2e_f037_render_census.py` and `test_replay_redrive_stack_refusal.py`;
  - ci-tools' repo-root finder tests ("no root above a temp directory");
  - the `observability` lane's sentry-sdk 3.x check, because `JuniperCascor1` has 2.58.0.

  All of them are in `docs/REFERENCE.md`'s "Known local-only failures". Measured 11-26 on #2684's tree: the
  regression group ran 266 jobs and failed only those three.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log --oneline -5 origin/main
gh pr view 2684 -R pcalnon/juniper-ml --json state,mergeCommit --jq '.state, .mergeCommit.oid'   # MERGED 7e485e9a...
gh pr view 2686 -R pcalnon/juniper-ml --json state,mergeCommit --jq '.state, .mergeCommit.oid'   # MERGED 6e271984...
git show origin/main:juniper-ci-tools/juniper_ci_tools/_version.py | tail -1                     # __version__ = "0.10.0"
git show origin/main:.github/workflows/ci.yml | command grep -c 'juniper-ci-tools>=0.9.0,<0.11.0'  # 3
gh release view juniper-ci-tools-v0.10.0 -R pcalnon/juniper-ml --json tagName,publishedAt        # "release not found" until the Overtoad cuts it
curl -s https://pypi.org/pypi/juniper-ci-tools/json | python3 -c 'import json,sys; print(json.load(sys.stdin)["info"]["version"])'   # 0.9.1 until published
ls ~/Development/python/Juniper/juniper-ml/tmp/run-tests-engine--agile-purring-pixel | wc -l      # the kept scratch
```

## Git state

- **juniper-ml**: #2682, #2684 and #2686 are merged. This handoff's PR carries this file and
  `util/ad-hoc/2026-11-26_widen_ci_tools_pin_ceilings.py`. The worktree `agile-purring-pixel` is at `6e271984`
  and clean apart from that script. Its `tmp/engine/` holds the release-phase scratch, which is copied to the
  primary's kept directory, and a Python 3.11 venv that can be regenerated.
- **juniper-data-client, juniper-recurrence**: no branch or change from this session.
