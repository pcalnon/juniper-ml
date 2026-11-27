# Brief: port juniper-cascor's SWEPT one-artifact publish template (#777) to one repository

Written 2026-11-26 between 01:26:36Z and 01:31:46Z (bounds read from `date -u` and a file stamp) by the orchestrating session `b71989` (juniper-ml worktree
`moonlit-percolating-sun`). Read this whole file before you start; your prompt names your repository and adds only
its specifics. Paths:

- `WT=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun` -- this session's
  worktree. **You can Write/Edit only inside `$WT`.** Run every command from `$WT` unless a step says otherwise, and
  `cd "$WT"` again after any `cd` into a clone.
- `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock` -- the arc's
  record (the predecessor session's worktree). **Read-only for you**: never write, edit, delete or run git there.

## Goal and stop point

Port the swept template to your repository's publisher(s), with its tests, docs and changelog, as ONE signed commit on a
NEW branch and ONE pull request. Then fetch the PR's files, re-run the checker on them, write your report, and STOP.
Never merge, approve, arm auto-merge, update-branch, close, or edit any other PR. The orchestrator runs the independent
review, CI and the merge.

## What the template is

The template is juniper-cascor `main` (`5e3d9801`; its three publishers are byte-identical to #777's merge
`f5ed3017`). A fresh clone is at `$WT/tmp/ports/clones/juniper-cascor` (shared and READ-ONLY: never edit it). In it:

- `git diff 36dd6f2d f5ed3017` is #777 itself (11 files, +1162 -191). Read it whole: `.github/workflows/publish.yml`
  (the single-package shape), `publish-cascor-model.yml` and `publish-protocol.yml` (the sub-package shape),
  `src/tests/unit/test_publish_one_artifact.py` (+688), the new `src/tests/unit/test_publish_docs_bounds.py`, and the
  docs (`docs/ci_cd/MANUAL.md` § "One Artifact, Checked Against TestPyPI" and § "Recovering a Release That Did Not
  Reach PyPI", `docs/ci_cd/REFERENCE.md` § "One-Artifact Contract", `QUICK_START.md`, `docs/DEVELOPER_CHEATSHEET.md`,
  `AGENTS.md`, `CHANGELOG.md`).
- `gh pr view 777 --repo pcalnon/juniper-cascor` -- its PR body: model yours on it (shorter: link it, do not restate
  every review round).
- What the sweep changes, item by item (A-G): `$W/tmp/ports/SWEEP_BRIEF.md` § "What the sweep changes". The 11-15
  port brief `$W/tmp/ports/BRIEF.md` still holds for the template contract and the mechanics, EXCEPT its paths
  (`giggly-foraging-sunbeam`, `tmp/ports/clones` under it), its checker (the 2026-11-15 one) and its dates.
- cascor's sweep writer, `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`, is the MODEL for your writer:
  its constants (`FIND_NEW`, `REPUBLISH_COMMENT_NEW`, `WITNESS_NEW`, `INSTALL_JOB_COMMENT`, `CD_COMMENT_*`,
  `LAG_COMMENT`, `lag_loop()`, `RELEASE_TAG_ENV`, `env_block()`, ...) are #777's new text, and `replace_once`,
  `detect_word`, `cut` and `check_workflows` show the method. Its `TEST_EDITS` were derived for cascor's test file and do
  not apply to yours.
- Your repository's 11-15 port writer, on juniper-ml `main` (`$WT/util/ad-hoc/2026-11-15_<repo>_one_artifact_publish_port.py`),
  shows how your publisher and your test copy differ from cascor's.

**Every template block must be byte-identical to cascor's.** Extract each block from the cascor clone's workflow text
programmatically (comments included), never retype it. The template blocks are every step whose comment says
"One-artifact publish template ... copy verbatim", and the whole `republish` job with its banner comment.

## The structural target, and the checker

- A YAML-dumped simulation of your port, which passes the checker, is
  `$W/tmp/sweep/checker-r12/port-sim/<variant>/<repo>/workflows/<publisher>.yml` (variant in your prompt). It shows the
  END STRUCTURE (jobs, needs, permissions, steps, the install script). It lost every comment and its layout: never copy
  its text, only compare against it.
- **The checker is FINAL** (`$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35`; check it with `sha256sum` before each run). Never
  edit it, never copy-and-edit it. Run it exactly so, all your repo's publishers on ONE command line (if the Bash guard
  refuses a command line naming `.github` paths, put it in a script file under `$WT/tmp/ports/<repo>/` and run that):

      /opt/miniforge3/envs/JuniperCascor1/bin/python3 -I -B $W/util/ad-hoc/2026-11-23_publish_port_template_identity.py \
          --repo <repo> \
          --template $WT/tmp/ports/clones/juniper-cascor/.github/workflows/publish.yml \
          --pins <pins file> \
          <clone>/.github/workflows/<publisher>.yml [...]

  Exit 0 = every workflow passed; the last line is `N of M pass`. juniper-data: `notify-consumers.yml` must sit beside
  `publish.yml` (it does in the clone; the checker pins its sha256, `e17ddc9b…`; do not change that file).
- **The install step must equal its pin** in `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json` (sha256
  `d539f05f…`; read its `about` and your repo's pins), byte for byte apart from one final newline. The pins were seeded
  from the simulations; "each port's review updates that port's pin" (owner ruling "Pin exact scripts", 2026-11-24).
  When your final script must differ from the seed (R4-5 below, or a layout your repo's step needs), DO NOT touch `$W`'s
  file: copy it to `$WT/tmp/ports/<repo>/pins.proposed.json`, change only your repo's pin(s) there (`lines`, and
  `sha256` = the sha256 of `"\n".join(lines)` UTF-8, `ensure_ascii` kept, `source` saying what changed and why), and run
  the checker with `--pins` that copy. Report the pin diff. If your script equals the seed, run with `$W`'s file and say
  so.

## Per-repository changes (beyond the template; from the reviews)

| repo | publisher(s) | variant | install step changes the checker needs | R4-5 `find_spec` | digest pins (G) |
|---|---|---|---|---|---|
| juniper-cascor-client | `publish.yml` | faithful | the tag through `env: RELEASE_TAG` | yes | normalize |
| juniper-cascor-worker | `publish.yml` | faithful | the tag through `env: RELEASE_TAG` | yes | normalize |
| juniper-data | `publish.yml` (+ `notify-consumers` job) | faithful | the tag through `env: RELEASE_TAG` | yes | normalize |
| juniper-data-client | `publish.yml` | faithful | the version file read under `$GITHUB_WORKSPACE` | yes | normalize |
| juniper-canopy | `publish.yml` | faithful | one `cd`; `pyproject.toml` read through a sparse checkout under `$GITHUB_WORKSPACE` | no | -- |
| juniper-recurrence | its 3 `publish-recurrence-*.yml` | faithful | the version file under `$GITHUB_WORKSPACE` | no | -- |
| juniper-ml | `publish.yml` + 6 `publish-<pkg>.yml` | see the ml row below | the version file under `$GITHUB_WORKSPACE` | ci-tools, observability | normalize |

- **R4-5**: the install checks that end on metadata alone gain a failing `importlib.util.find_spec("<module>")` check,
  as cascor's `publish-protocol.yml` does (the module must be found with an origin; fail through
  `raise SystemExit(...)`, never `assert`, which `PYTHONOPTIMIZE` strips). Take the import name from the package's own
  source tree. This changes the pin: propose it as above.
- **G (item 23)**: the repos whose test pins the template blocks' raw-text sha256 pin a NORMALIZED block instead: every
  `uses:` line reduced to the action name, its `@ref` and trailing `# vX.Y.Z` dropped.
- **juniper-ml** (one PR, all 7): `publish.yml` takes the simulation's three edits (the flag-form fetch:
  `pip download … && { FETCHED=1; break; }` in place of the `set +e` block; `ls -la` without `|| true`; the template's
  exact lag-error text) with `tests/test_publish_testpypi_verify.py:477` moved to that text (R5-F5). `publish-config-tools.yml`
  and `publish-doc-tools.yml`: `python -c` last (variant `reorder`). **R4-1 (MAJOR)**: `tests/test_publish_testpypi_verify.py:86-90`
  and `tests/test_publish_subpackage_workflows.py:92-98` look for the install step in the TestPyPI job and SKIP when it
  is not found: retarget both to the `Verify the TestPyPI install` job, make "not found" a FAILURE, and set the
  expected TestPyPI permissions (`:237`) to `{id-token: write}`. ml's tests are `unittest`, run per ci.yml's list.
- **juniper-recurrence**: restore `#        owner       = pcalnon` (aligned with `repository  =`) at line 22 of all three
  publishers, in the "TRUSTED-PUBLISHER REGISTRATION" header, where #237's rename wrote `Overtoad`: that field is PyPI's
  technical owner (the GitHub account). Its tests: `juniper-recurrence/tests/test_publish_one_artifact.py` and
  `juniper-recurrence-model/tests/test_publish_smoke_pins.py:47`.
- **juniper-data**: `notify-consumers` keeps its trigger semantics; say in the PR body what a republish dispatch does
  and does not do for it.
- **No action-ref change is needed anywhere**: every repo already uses the template's action SHAs (the checker pins
  them). If the checker says otherwise, stop and report.

## Tests

- Port #777's changes to cascor's `test_publish_one_artifact.py` into your repo's copy (inventory: canopy and cascor
  have it under `src/tests/unit/`, data under `juniper_data/tests/unit/`, recurrence under `juniper-recurrence/tests/`,
  the clients, worker and ml under `tests/`), adapted to your publishers: every hardening of SWEEP item E (retention
  exactly 90; the reuse exemption by the step's NAME; no `if:`/`continue-on-error` on template or check steps; each
  job's exact step list; the workflow name ends "to PyPI"; the install check cannot be switched off; A's wiring
  exactly; B's rehearsal cases; C's rehearsal; exact install commands per the test lens). Keep every rehearsal.
- `TestFindReleaseRun.test_the_newest_release_run_that_still_holds_the_artifact_is_found` goes, as in #777 (the find
  step no longer prefers a run that holds the artifact). Your commit body therefore carries the waiver line (below).
- `test_publish_docs_bounds.py`: port it, adapted, if your repo's docs state the bounds' numbers (poll count, interval,
  timeouts, tries, waits); if they do not, say so in the report and do not add the numbers just to pin them.
- Update every other test that pins publish text (grep the test tree for each publisher's file name and for the moved
  step names). **No new skip** in any publish test (a skipped pin is no pin; never `importorskip` PyYAML). Match the
  repo's lane: if CI selects tests by marker, the module carries that marker (an unmarked test is silently deselected).
- No implicit string concatenation in any Python you write (flake8-bugbear B914 is on).
- Run, in the repo's own environment (its `AGENTS.md`; canopy `JuniperCanopy1`, data `JuniperData`, cascor-family
  and others `JuniperCascor1`, via `/opt/miniforge3/envs/<env>/bin/python -m pytest ...` or the repo's own runner):
  the full publish test module(s) and every test you touched, and report counts (passed / failed / skipped).
- **Mutation proof**: at least 8 mutations across A, B, C and the hardening (e.g. drop the install job's `needs`; give
  it `id-token: write`; put the checkout back in the TestPyPI job; retention 90 -> 30; one character inside the find
  step; `PUBLISH_TAG_PREFIX` disagreeing with the guard; `|| true` on the install's pip line; remove the
  `find_spec`), each applied to a COPY, each failing the suite, each restored. Tabulate them in the PR body.

## Docs and changelog

- Wherever your repo documents its publish pipeline (inventory: canopy `docs/ci_cd/CICD_MANUAL.md`,
  `CICD_REFERENCE.md`; data `docs/ci_cd/CICD_MANUAL.md`, `CICD_REFERENCE.md`, `CICD_QUICK_START.md`,
  `docs/DEVELOPER_CHEATSHEET.md`, `docs/REFERENCE.md`; the clients `docs/REFERENCE.md`; worker `AGENTS.md`,
  `docs/DEVELOPER_CHEATSHEET.md`; recurrence `juniper-recurrence/README.md`, `juniper-recurrence-client/AGENTS.md`;
  ml `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`): state the new contract in a few lines (the install
  job, the republish gate, `PUBLISH_TAG_PREFIX`) and the ladder's new facts (SWEEP_BRIEF item D's ladder bullets), with
  your repo's own `gh workflow run <file> --repo pcalnon/<repo> --ref <tag> -f republish_from_testpypi=true`. Link
  cascor's two MANUAL sections (`https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi`,
  `…#recovering-a-release-that-did-not-reach-pypi`); do not copy them wholesale. Correct any text the sweep makes false.
- `CHANGELOG.md`: one entry under `[Unreleased]`, in the repo's own style (recurrence: `juniper-recurrence/CHANGELOG.md`
  unless its conventions say otherwise).
- **Wording**: in NEW text avoid naming the person; where you must, use the word the base file already uses (detect it
  at run time, as cascor's writer does). Never change "owner" where it is not the person (`/repos/{owner}/{repo}`,
  `repository_owner`, PyPI's trusted-publisher `owner`).
- An `AGENTS.md`/`CLAUDE.md` edit sets `**Last Updated**:` to `date -u`'s day **at upload time** (CI's
  `Verify AGENTS.md Last Updated` compares the UTC day when it runs; re-run the writer with `--date` if midnight UTC
  passes before the upload). `CLAUDE.md` is usually a symlink to `AGENTS.md`: edit the target, never replace the link.

## Your writer

`$WT/util/ad-hoc/2026-11-26_<repo>_one_artifact_sweep_port.py --tree <fresh clone> [--date YYYY-MM-DD]`: exact-once
anchored replacements; refuses and writes NOTHING on any anchor miss or failed post-condition; header like cascor's
writer (Project, Sub-Project, Author Paul Calnon, Created 2026-11-26, Status, `Retire when: RETAINED`, Related, Why);
re-runnable on a fresh clone of `main` (the orchestrator may need to re-apply it after `main` moves). The test-file
edits may be written as anchored hunks or, if you replace the test module whole, as a file the writer installs; either
way the writer produces the final tree.

## Where to work

- Your clone: `$WT/tmp/ports/clones/<repo>` (a fresh `main` clone made 2026-11-26 01:25Z). Edit only there, your
  writer, and your scratch dir `$WT/tmp/ports/<repo>/`. Before writing, confirm the clone's `HEAD` equals GitHub's `main`
  (`python3 -I $WT/tmp/s2/clone_heads.py $WT/tmp/ports/clones` prints it); if `main` moved, `git pull --ff-only` it.
- git inside the clone works with a plain `cd <clone> && git ...` (never `git -C`). Never `git commit`, `git tag`,
  `git push`, or anything that signs (a YubiKey prompt hangs headless). Never touch another repo's clone, the sibling
  primary checkouts under `/home/pcalnon/Development/python/Juniper/<repo>`, any other worktree, or `$WT`'s own git
  state (no add, commit, stash, reset, checkout in `$WT`).
- Never write under `/tmp` or `/var/tmp`. Temporary files go under `$WT/tmp/ports/<repo>/`.

## Verification (all before the push)

1. Your publish tests and every touched test, in the repo's env: counts.
2. `actionlint` (on PATH) on every changed workflow: clean.
3. pre-commit on every changed file: `cd <clone> && /opt/miniforge3/bin/pre-commit run --files <files>` (or
   `python3 -I $WT/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py SRC DEST /opt/miniforge3/bin/pre-commit FILE...`).
   Never edit `.pre-commit-config.yaml`.
4. The checker on all your publishers (above): `N of N pass`, with the pins file you used and its sha256.
5. The mutation proof.
6. The sequence-safety screens your repo runs (read its `.github/workflows/sequence-safety.yml` for each screen's
   scope; juniper-ml has no such file: its screens run in `ci.yml`, `--scope 'tests/*.py' --scope 'util/**/*.py'
   --scope 'util/**/*.bash'`), on a local replay: `python3 -I $WT/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/probe_screens.py <dest under $WT/tmp/ports/<repo>/> <base tree> <your tree> <commit body file>`
   (it runs cascor's two screens with cascor's scope: if your repo's scope differs, run its screens yourself the same
   way, from `/opt/miniforge3/envs/JuniperCascor1/bin`). The symbol-loss screen must pass WITH the waiver line.
7. The pre-push gate: `bash $WT/util/ad-hoc/2026-11-15_pre_push_gate_run.bash $WT/tmp/ports/<repo>/gate` with
   `gate/files/` = copies of exactly the files to be pushed, `gate/text/` = the PR body and the commit message files,
   `gate/added/` = the added lines. Only exit 0 lets you push. Report every masked-read line you judged.

## Landing (only after every verification passes)

- Right before the upload, confirm again that the clone's `HEAD` equals GitHub's `main` (a whole-file upload from a stale
  base silently reverts someone's merge). If `main` moved: pull, re-run the writer on a fresh clone if needed, re-verify.
- Branch `fix/publish-one-artifact-sweep` (if it exists, stop and report). One signed commit through
  `python3 -I $WT/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/run_open_signed_pr.py $WT/tmp/ports/<repo>/ARGS.json --dry-run`,
  then without `--dry-run` (ARGS.json: `repo` (bare name), `base` `main`, `branch`, `tree` (your clone), `paths`
  (repo-relative, exactly the changed files), `message`, `commit_body_file`, `title`, `body_file`). Run it from `$WT`.
- Commit subject: `fix(publish): port of juniper-cascor#777 -- the install check gets a job that cannot mint, the
  republish job checks the release run's TestPyPI jobs, and PUBLISH_TAG_PREFIX` (shorten if your repo's subject limit
  needs it). Body: what changed, then a paragraph that is exactly
  `Allow-Symbol-Loss: TestFindReleaseRun.test_the_newest_release_run_that_still_holds_the_artifact_is_found` (adapt
  the symbol to your repo's copy if its class or test name differs, and name every symbol the screen reports), and as
  the LAST paragraph exactly these two lines and nothing after them:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
      Claude-Session: https://claude.ai/code/session_016H76AnduzwfVyhVtsQqJeJ

- PR body: Summary; the two rulings of 2026-11-16 (quote them as #777 does) and the engineering proposal note; what
  changed per workflow; what a republish dispatch does now; the ladder; the per-repo changes above; the pin (unchanged,
  or the proposed diff); testing evidence (commands and results, the checker's lines, actionlint, pre-commit, the
  mutation table, the screens, the gate's exit); a `## Requirements` section if the repo's PR template has one (JR ids
  only if you find real ones; never invent one). It must END with exactly:

      🤖 Generated with [Claude Code](https://claude.com/claude-code)

      https://claude.ai/code/session_016H76AnduzwfVyhVtsQqJeJ

- After the push: `python3 -I $WT/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/readback_branch.py $WT/tmp/ports/<repo>/ARGS.json`
  (every blob equals the local file; the commit verified; no extra or missing file). Then
  `python3 -I $WT/util/ad-hoc/2026-11-15_fetch_pr_files.py --repo <repo> --ref fix/publish-one-artifact-sweep --pr <N> --out $WT/tmp/ports/<repo>/pr-head`
  (plus `.github/workflows/notify-consumers.yml` for juniper-data, which the PR does not change) and re-run the checker
  on the fetched files.

## Hard rules

- Quote only PR numbers, SHAs and run ids a tool printed. No secrets, tokens, e-mail addresses or other personal data
  in any file, PR, commit or report.
- Never edit the checker, `$W`'s pins file, or anything else under `$W`.
- Never estimate a time; use `date -u`.
- If something in your repo contradicts this brief: the repo wins on its own conventions, the template wins on the
  template, and you report it.

## Addenda from the pilots (2026-11-26, after juniper-cascor-client#206 opened at 02:19:17Z)

- **You run in your own worktree** (`.claude/worktrees/agent-<id>`): your Write/Edit tools refuse `$WT` paths, and the
  Bash guard may refuse `cd <clone> && git …`. Draft in your own worktree's `tmp/`, copy into `$WT` with Bash `cp`, and
  keep the sources in your scratch dir's `drafts-source/` (your own worktree may be deleted when you finish: anything
  left only there is lost). Run git in the clone through a small script file (Python `subprocess` with `cwd=`).
- **The screens' scope**: `probe_screens.py` hardcodes cascor's `src/**`. Copy it into your scratch dir with your repo's
  own scope from its `sequence-safety.yml` (the pilot's copy, `$WT/tmp/ports/juniper-cascor-client/probe_screens_ccc.py`,
  shows the change).
- **Every removed symbol is waived**: the pilot's screen also reported
  `TestUnchanged.test_the_testpypi_job_keeps_its_setup_and_its_install_check` (the TestPyPI job no longer has an
  install check); name each symbol the screen reports on its own `Allow-Symbol-Loss:` line.
- **A sparse checkout only where the script reads the workspace**: an install job whose version comes from the tag
  needs no checkout (cascor's `publish.yml` has none); one that reads a version file takes the sparse checkout of that
  file, with `persist-credentials: false`, as cascor's sub-package publishers do.
- **Re-read the PR body against what you did** before the upload: the pilot's body carried three small inaccuracies.
- **A worked example** (under independent review, not yet merged: compare, never copy blindly): the pilot's writer
  `$WT/util/ad-hoc/2026-11-26_juniper-cascor-client_one_artifact_sweep_port.py`, its scratch dir
  `$WT/tmp/ports/juniper-cascor-client/` (`REPORT.txt`, `mutations.py`, `make_pins.py`, `build_gate.py`), and the PR
  `https://github.com/pcalnon/juniper-cascor-client/pull/206`.
- **From #206's review** (BLOCKER 0, MAJOR 0, MINOR 1, NIT 6; `$WT/tmp/ports/juniper-cascor-client/review/REVIEW.txt`):
  - never carry a sentence from cascor's CHANGELOG or docs that is true only of cascor: e.g. "the package it imported
    ran with that job's OIDC token-request variables" is false where your base check read metadata alone (R1);
  - an R4-5 check prints cascor's neutral line, exactly as `publish-protocol.yml:389` does, with no "OK" before the
    check has passed: `print('TestPyPI install', m.version('<dist>'), 'package at', origin); raise SystemExit(0 if
    origin else 'the installed wheel holds no <module> package')` (R5);
  - a recovery list's lead-in must not exclude one of its own bullets (a failed `Verify PyPI serves exactly these
    files` is AFTER the upload), and a "never re-cut" line states ruling 1's consequence: the re-cut's run becomes
    the tag's newest release run, TestPyPI refuses its files, and rung 1 then refuses the tag (R2, R3);
  - a writer argument with a placeholder default must be required, or refuse a placeholder left unreplaced (R7);
  - one `Allow-Symbol-Loss:` line per symbol (R6).
- **From #274's review** (BLOCKER 0, MAJOR 1, MINOR 3, NIT 1; `$WT/tmp/ports/juniper-data-client/review/REVIEW.txt`):
  - **(MAJOR) a failed `Verify PyPI serves exactly these files` has TWO causes; never send both to a new patch
    version.** A mismatch (PyPI lists a file this run did not build, or another sha256): only a new patch version ships
    tested files under a clean version. A check that gave up waiting (PyPI's JSON did not list the files in time): index
    lag; the files are already on PyPI; "Re-run failed jobs" uploads the same bytes again, which the index accepts, and
    repeats the check (re-running the PyPI job needs a fresh `pypi` approval). cascor's `docs/ci_cd/MANUAL.md` keeps
    the two apart (its failure table's mismatch row and its "A JSON check gives up after 20 attempts" row). Never call
    the timeout "past the ladder";
  - never say the install job "runs" the package where the check reads metadata or `find_spec` only: it INSTALLS the
    package TestPyPI serves (cascor's banner comments in the workflow stay as the template has them);
  - #274's own R5 form ("TestPyPI OK: v…" before the `SystemExit`) is being fixed to cascor's neutral line, as above.
- **From #238's review** (BLOCKER 0, MAJOR 0, MINOR 1, NIT 2): `Verify PyPI serves exactly these files` runs in TWO
  jobs, the PyPI job (the release run) and the republish job (the dispatch run, the usual case after the release run's
  30 days). Its "gave up waiting" remedy names the run whose check gave up: "Re-run failed jobs on the run whose check
  gave up (the release run, or the republish's dispatch run), within 30 days of that run", never "on the release run"
  alone.
- **Concurrent PRs on your repo**: before the upload, list the repo's open PRs (`gh pr list --repo pcalnon/<repo>`)
  and report any that change a file you change (a CHANGELOG entry, a doc): the one merged second must take the other's
  text.

## Report

Write it to `$WT/tmp/ports/<repo>/REPORT.txt` (a `.txt`; write it BEFORE your final message), and make your final
message the same text. Include: the PR number, URL and head sha (as printed); the writer's path; the clone's base
`HEAD`; `git diff --stat`; every verification's command and result (test counts, actionlint, pre-commit, the checker's
lines with the pins file and sha256 used, the mutation table, the screens, the gate's exit and every masked line you
judged); the proposed pin diff, if any; every judgement call; anything you could not do; anything that contradicts this
brief.
