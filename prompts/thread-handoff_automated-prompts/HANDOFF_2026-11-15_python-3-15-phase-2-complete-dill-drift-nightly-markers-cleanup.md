# Handoff: Python 3.15 -- phase 2 complete (dill, the cascor-model drift, the nightly marker error); arc worktrees cleaned

**Date**: 2026-11-15 (facts read 11:36Z to 13:01Z)
**Session**: host yamaguchi, juniper-ml worktree `.claude/worktrees/warm-squishing-balloon` (session 32c8575d).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_python-3-15-phase-2-deploy-precommit-required-h5py-prs.md`
(on `main` through juniper-ml#2585). Its "#2586 is OPEN" line was stale on arrival: #2586 merged at 06:40Z (`31058eaf`).

## Goal statement

Phase 2 of the Python 3.15 migration ("work through the 3.15 problems") is done: every identified problem is fixed
and merged. The next step is **phase 3, making a 3.15 check required, which is the owner's decision. Do not start
it unasked, and do not move `/usr/bin/python3` off 3.14 (phase 4).** Merge approval for this arc was granted in this
session by the owner; **it does not carry to a new session.**

## Owner rulings this session (2026-11-15, from the dialog)

1. dill on 3.15: **"safe=True in the helper"** (over pinning dill's `master` on the 3.15 legs, switching the helper to
   stdlib pickle, or waiting for dill 0.4.2).
2. deploy's `Unit Tests (Python 3.13)` / `(Python 3.14)`: **"Require both"** in ruleset 14715370.
3. "merge approval granted for PRs on this work arc."

## Done (all squash-merged under that approval, each with its `## CI result` recorded in the PR body)

| Repo | PR -> squash | What |
|------|--------------|------|
| juniper-cascor | #765 -> `4a440ce1` | `check_object_pickleability` passes `safe=True` to all three `dill.pickles` calls, in `src/utils/utils.py` and its drift-checked copy; new test pins it. 3.15 unit leg `6123 passed`; cascor-model 3.15 `1 failed` (drift only) |
| juniper-data-client | #263 -> `225dd6bb` | `scheduled-tests.yml` selects `-m integration` |
| juniper-cascor-client | #198 -> `e8aa7361` | same |
| juniper-cascor-worker | #231 -> `3975d9ac` | same; dispatch run `5 passed, 537 deselected` on all 4 legs |
| juniper-cascor | #766 -> `1de9c6f7` | cascor-model `constants_api` re-extracted from `src/` (cascor#687's `_PROJECT_API_START_FRESH_REQUIRED_MARKER`); cascor-model 3.12 and 3.15 `438 passed`. On `main`, `ci-cascor-model.yml` run 43716586513 is green (both legs and `Build distribution`), its first green run since `0e016a7c` (2026-09-23) |
| juniper-deploy | #279 -> `413dfd12` | `ci.yml` comments and `[Unreleased]` say which legs ruleset 14715370 requires |

- **Ruleset 14715370: 14 -> 16 contexts** (`Unit Tests (Python 3.13)`, `(Python 3.14)`, integration_id 15368), one
  full-replacement PUT by `util/ad-hoc/2026-11-15_deploy_ruleset_require_unit_tests_legs.py --execute`; post-check
  passed. Before/PUT/after JSON: `juniper-ml/tmp/py315-phase2-2026-11-15/deploy-ruleset-unit-tests/` (PRIMARY).
  deploy#279 was the first PR measured against it: 16/16 required reported.
- **The nightly marker error** (the predecessor's "pre-existing defect"): pytest 9.2.0 makes an unregistered marker in a
  `-m` expression a usage error under `--strict-markers` (exit 4; 9.1.1 exits 0, measured). The three repos had kept
  the template default `slow or integration` without registering `slow`; red from 2026-10-28. Each fix was measured by
  `gh workflow run scheduled-tests.yml --ref <pr-branch>`, since PR checks never run that workflow. The template
  `notes/templates/ci/scheduled-tests.yml` TODO 2 now warns.
- **The cascor-model drift** was caught on #687 itself (2026-09-24, its `Test (Python 3.12)` failed), but no ruleset
  requires that context, so `main` stayed red seven weeks. See Open owner question 1.
- **Cleanup**: the predecessor's 18 worktrees plus `agent-a071c56ac10b0da13` were removed (both liveness probes clear;
  every PR merged; every uncommitted file proven equal to its merged PR head, or for two CHANGELOGs, every added line
  present in it), their local branches deleted, and juniper-harcot's two leftover remote branches deleted (and the
  stale tracking refs pruned in harcot, data-client and cascor-client). This session's own six worktrees went the same
  way once their PRs merged; none is left. Evidence from all 25 removals is in
  `juniper-ml/tmp/worktree-cleanup-2026-11-15/` (PRIMARY), under the owner's 2026-10-30 "evidence only" ruling.
  Final `MANIFEST.tsv` totals: 85 COPIED rows (83 files, plus 2 symlinks: `agent-a071c56ac10b0da13`'s
  `tmp/py315-local/shim/python` and `python3`), 7.5 MB; 15 SKIPPED-REGEN trees (venvs, `pre-commit-home`, caches),
  counted; 17 EMPTY-DIR rows.
- **This session's own evidence** (PR bodies, commit messages, CI logs, inventories, the survey output) is in
  `juniper-ml/tmp/py315-phase2-2026-11-15/session-32c8575d-evidence/` (PRIMARY), 115 files.

## Phase-2 status (`util/ad-hoc/2026-11-15_py315_leg_survey.py`, read 12:42Z)

Every 3.15 leg on every repo's `main` reported `every step passed on Python 3.15`, except:
- cascor-model on `4a440ce1`: the drift test. #766 fixed it; `main`'s run on `1de9c6f7` (43716586513) passed;
- the three nightly lanes' 06:00Z runs, which predate the fixes. Their next runs are 2026-11-16 ~06:00Z.

cascor's `main` run on `4a440ce1` shows a `cancelled` 3.15 leg with a warning: it was superseded by later runs on
the same SHA, not failed. The newest run (`7802aef5`) passes every step. Read the newest run, never a cancelled one.

## Remaining work

1. **After 2026-11-16 06:00Z**: confirm the nightly `scheduled-tests.yml` runs are green in data-client, cascor-client
   and cascor-worker (`gh run list --repo pcalnon/<repo> --workflow scheduled-tests.yml --limit 1`).
2. **dill floor**: dill 0.4.1 (2026-01-19) is still the newest release; its `master` handles 3.15 since 2026-05-23
   (commit `37d2bf71`). Raise cascor's and cascor-model's dill floors when a release ships. Do not cite the upstream
   PR number in a PR body (it posts a backlink). Any PR for it needs the owner's merge approval again.
3. **Phase 3**: the owner's go-ahead first.

## Open owner questions

1. Should cascor's `CI — juniper-cascor-model` `Test (Python 3.12)` become a required context in ruleset 15081045?
   It caught #687's drift and was ignored because nothing requires it.
2. Phase 3: which 3.15 checks become required, and when?

## Key context / traps

- **Isolation**: refuses git inside `$(...)`, loops naming git, heredocs, and any compound command containing a
  `.github` path. Use the Edit tool for edits and one plain command per git call; read remote files with
  `util/ad-hoc/2026-11-15_read_remote_files.py`.
- **`JuniperCascor1` has juniper-cascor-model 0.1.0 installed**, whose top-level `utils` and `cascor_constants`
  shadow a worktree's copies for the cascor-model suite: run it with `PYTHONPATH=<wt>/juniper-cascor-model` and
  check `__file__`. It also lacks `columnar`, so `test_reload_without_columnar_sets_fallback_flags` fails locally only.
- **A `--system-site-packages` venv over `JuniperCascor1` inherits anyio's pytest plugin**, which errors at load
  under pytest 9.2.0. Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` with explicit `-p` plugins.

## Verification commands

```bash
/usr/bin/python3 --version                                   # 3.14.x
gh pr view 766 --repo pcalnon/juniper-cascor --json state,mergedAt                    # MERGED 2026-11-15T12:58:57Z
gh api repos/pcalnon/juniper-deploy/rules/branches/main --jq '[.[]|select(.type=="required_status_checks")|.parameters.required_status_checks[].context]|length'   # 16
gh run list --repo pcalnon/juniper-cascor --workflow ci-cascor-model.yml --branch main --limit 1 --json conclusion   # success
python3 util/ad-hoc/2026-11-15_py315_leg_survey.py           # every leg: "every step passed on Python 3.15"
```

The survey's nightly-lane rows stay `warning` until the 2026-11-16 ~06:00Z runs replace the 2026-11-15 ones.

## Git status

The juniper-ml worktree `warm-squishing-balloon` is on `worktree-warm-squishing-balloon` at `57c76b63`; its new
`util/ad-hoc/2026-11-15_*` scripts, the template edit and this file reach `main` through the provenance PR on branch
`docs/handoff-py315-phase2-complete`. No other branch of this arc is open in any repository, and no arc worktree
remains under `/home/pcalnon/Development/python/Juniper/worktrees/`.
