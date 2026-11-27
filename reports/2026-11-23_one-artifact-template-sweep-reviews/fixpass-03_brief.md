# Fix pass 3 brief: apply round 4's fixes, build tree `cascor-r4`, re-run every proof

Written 2026-11-23 (`date -u` ~19:55Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

## Goal

Apply the round-4 review's fixes (fix pass 3, in the numbering of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: fix pass 1
made `cascor-r2`, fix pass 2 made `cascor-r3`) to the WRITER and the CHECKER, regenerate juniper-cascor's sweep tree as
`$W/tmp/sweep/cascor-r4/`, and re-run every proof. A fresh reviewer will then review ONLY the checker's interdiff and
the cascor interdiff (round 5), so make both interdiffs clean and easy to read.

Read first: `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` in full (the "Round-4 review" table is your work list; the
"Round 3" section is the format your own section follows), then `$W/tmp/sweep/ROUND4_BRIEF.md`.

## Scope

**CHECKER** `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (now sha256 `2feceecf…`):
- R4-2 (MAJOR): the install script's last command is exactly `python`/`python3`, `-c`, one argument; refuse a `|` or a
  single `&` control operator anywhere in the install script outside `$(...)`.
- R4-3: refuse a command whose first word contains `$` or a backtick; refuse `-m\s*pip`; refuse `hash`, `eval`,
  `source`, `.`, `exec`, `bash -c`/`sh -c` and any `NAME ()` definition; require the fetch target and `--dest` quoted;
  cover `+=` (e.g. `PYTHONPATH+=`). Where a rule cannot be made sound, narrow the docstring's claim instead and say so.
- R4-4 (checker part, `:580-583` in the reviewed file): admit `concurrency` at WORKFLOW level only (the build job may
  keep it if you judge it safe; say which); keep job `timeout-minutes`.
- R4-6: refuse `defaults.run.shell` on the build job; admit `TAG_ASSERT` only for juniper-ml and its 6 sub-packages
  and `CANOPY_SMOKE` only for juniper-canopy; reword the F1-window comment to what it really admits. The checker must
  learn the port's repo from the OPERATOR (e.g. a required `--repo` argument), never from the workflow text, which a
  port controls. Update every caller you add.
- The checker NIT row: REQUIRE the template's exact lag-error text (the operator signature `docs/ci_cd/MANUAL.md`
  quotes). Relax the over-strict rules where safe (`shell: bash`; `PYTHON*` keys in build jobs; `pip --version`;
  `-i`; `for … in $(seq …)`; an `echo` naming "pip <word>"), else document why each stays. Every relaxation needs a
  negative case proving it reopens no bypass.

**WRITER** `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py` (now sha256 `a287376f…`):
- R4-4: the cascor test's key allow-lists admit `concurrency` at workflow level only; fix the test comments
  (`:182-186`, `:282` of the r3 test file), `CHANGELOG.md:292`, and `checker_proof_r3.py`'s control C5 (make a
  `checker_proof_r4.py` in `cascor-r4/`; never edit the r3 copy).
- The CHANGELOG NIT row: `:276-277` "(MANUAL.md says the same)"; `:284` "builds only from the package's own tag" (the
  guard tests the ref NAME); `:292` lists `run-name` as a job key; and correct #767's unreleased entry (`:197`, still
  "witnesses what the install check tested") IN PLACE.
- The test-comment NIT: the comment says jobs may add `timeout-minutes`, but the republish job may not (it must stay
  byte-identical).
- Line numbers above are the r3 tree's (`$W/tmp/sweep/cascor-r3/juniper-cascor`). Every fix goes into the WRITER, never
  only into a clone: a re-run on a fresh clone must reproduce the tree byte for byte.

**Out of scope:** R4-1 and R4-5 (port items, done later), any workflow behaviour change not listed above. If a fix seems
to need a change to a publish workflow's YAML behaviour, stop and report it instead.

## Bases and trees (both required)

- **Base A**: cascor `802399ab` (round 3's base). Build `cascor-r4/juniper-cascor` = `802399ab` + the new writer's
  output. Its diff against `cascor-r3/juniper-cascor`'s result is the cascor interdiff `cascor-r4/r3_to_r4.diff`.
  A clean `802399ab` tree: `$W/tmp/r4review/main-802399ab.tar`, or a copy of a round-3 clone reset to its HEAD. Check
  the HEAD you build on.
- **Base B**: cascor `main` NOW, `e9c86f83` (cascor#772 MERGED 2026-11-23 19:35Z, squash of head `31136d64`; round 3
  only saw #772's earlier head `1e6e877a`). Clone fresh:
  `python3 -I $W/util/ad-hoc/2026-11-15_publish_port_clone.py --dest-root $W/tmp/sweep/cascor-r4/main juniper-cascor`
  (it refuses an existing destination; read its header). Run the writer on it as `cascor-r4/work-main` (or wherever
  the tool puts it). Diff its result against `$W/tmp/sweep/cascor-r3/work-after772` and account for EVERY difference
  (expected: fix pass 3's own changes, plus #772's `1e6e877a` -> `31136d64` rebuild). Write the account into your
  report.
- Each tree gets `sweep.diff` and its sha256.

## Re-run on BOTH bases (evidence logs into `cascor-r4/evidence/`)

Use `/opt/miniforge3/envs/JuniperCascor1/bin/python` under `env -u JUNIPER_CASCOR_LOG_DIR`. Read each tool's header
before running it; the `final_*.bash` drivers in `cascor-r3/` are hard-wired to `work-main`/`work-after772`: copy and
adapt them into `cascor-r4/`, never edit the r3 copies.
1. Tests: `-m pytest src/tests/unit/test_publish_one_artifact.py src/tests/unit/test_publish_docs_bounds.py
   -p no:cacheprovider` (161 passed on r3; report the new count and update the writer's `--changelog-cases` value if
   the CHANGELOG's stated count must change), then the 14 files in `cascor-r3/workflow_reader_tests.txt`.
2. `cascor-r3/mutation_proof.py` (45 of 45 on r3): all caught.
3. The test-lens harness (`make_r3_harness.py`, `test_lens_mutations_r3.py`, `run_test_lens.bash`): every
   property-breaking edit caught, every harmless one passing, C4/D1/D2 failing by design. NOTE: R4-4 turns a JOB-level
   `concurrency` from harmless into property-breaking; re-classify it (a workflow-level non-cancelling `concurrency`
   stays harmless) in an r4 copy of the harness, and say so.
4. The checker proof: `cascor-r4/checker_proof_r4.py` (r3's 74 cases, C5 updated, plus a positive and a negative
   case for every R4 fix and every relaxation): all pass.
5. Port simulations: `python3 -I $W/util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py port-sim` (read its
   `--help`; the simulations are in `cascor-r3/port-sim/`). All 15 must PASS. If a faithful simulation now fails, the
   checker is over-strict: fix the checker. If it fails because the simulation deviates from the template, record the
   per-port change it needs (as round 2 did) and put corrected copies under `cascor-r4/port-sim/`, never in r3's.
6. Bypass mutants: all 7 in `$W/tmp/r2review/neg/` and every bypass mutant in `$W/tmp/r4review/mutants/` (table:
   `$W/tmp/r4review/mutants.txt`; driver: `python3 -I $W/util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py
   mutants`, read its `--help`) must FAIL the checker; the controls (T0, P0) must PASS. The earlier 43 negative cases
   keep their verdicts. Then build at least 4 NEW mutants aimed at your own new rules and relaxations; each must FAIL.
7. actionlint (`/opt/miniforge3/envs/JuniperCascor1/bin/actionlint`) on the three workflows; cascor pre-commit through
   `$W/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py SRC DEST /opt/miniforge3/bin/pre-commit
   FILE…` (the guard blocks pre-commit inside a clone); B914 (`$W/tmp/sweep/cascor-r3/venv-b914/bin/flake8 --isolated
   --select=B914 <changed .py>`); the symbol-loss screen (`/opt/miniforge3/envs/JuniperCascor1/bin/python -I
   $W/tmp/sweep/cascor-r3/predict_symbol_loss.py BASE_TREE HEAD_TREE <rel .py> --trailers <commit body>`, once per
   changed test module), the docs screen and the markdown-structure delta as `cascor-r3/final_lint_and_screens.bash`
   runs them. Run pre-commit and B914 on the changed CHECKER and WRITER too (juniper-ml's config).

## Outputs

- BEFORE editing: copy the checker to `cascor-r4/checker_r3_as_reviewed.py` and the writer to
  `cascor-r4/writer_r3_as_reviewed.py`; confirm their sha256 begin `2feceecf` and `a287376f`. Save
  `$W/tmp/arc/sweep_scripts.sha256` as `$W/tmp/arc/sweep_scripts.r3.sha256`. AFTER: write
  `cascor-r4/checker_r3_to_r4.diff` and `cascor-r4/writer_r3_to_r4.diff`, then regenerate
  `$W/tmp/arc/sweep_scripts.sha256` over the same six paths (`sha256sum -c` must pass).
- `cascor-r4/pr_body.md` and `cascor-r4/commit_message.txt`: copies of r3's, with every base and count updated to base
  B's run (base `e9c86f83`). Line 1 of `commit_message.txt` is the headline, line 2 blank, the body from line 3; keep
  the `Allow-Symbol-Loss:` line. Its last two lines become
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_016H76Aje9K5yyjAb1ZUQvPo`. The PR body ends with
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`, a blank line, then
  `https://claude.ai/code/session_016H76Aje9K5yyjAb1ZUQvPo`. Report every claim in them you could not re-derive from
  base B's run.
- APPEND a section `## Fix pass 3 (round 4's fixes; tree cascor-r4)` to `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, in the
  Round 3 section's style: trees and sha256s, the interdiffs, the new writer/checker sha256s, what was applied per R4
  id, every rule ADDED beyond the review (named), every relaxation, results on both bases, residual risks. Append
  only; change nothing above it.

## Rules

- Never write under `/tmp` or `/var/tmp`. Scratch goes under `$W/tmp/sweep/cascor-r4/`.
- Edit only the writer, the checker, new files under `$W/tmp/sweep/cascor-r4/`, the manifest and the dispositions
  file (append). READ-ONLY: `$W/tmp/sweep/cascor`, `cascor-r2`, `cascor-r3`, `$W/tmp/r2review`, `$W/tmp/r4review`
  and every other existing file. Delete nothing under `$W/tmp/` (retention rule).
- Read-only `gh` GETs only. Never push, never `git commit` in `$W`, never open, comment on, approve or merge a PR.
- The Bash guard refuses `git -C`, `cd` into another worktree with git, `git/trees` in a URL and some heredocs: write
  small script files under `cascor-r4/` and run those.
- Run Python that reads a cloned tree with `python3 -I`. Take dates from `date -u`; never estimate a duration.
- No secrets, tokens, e-mail addresses or personal data in any output.
- If a fix needs a decision only the owner can make, stop that item, finish the rest, and report it.

## Final report (your last message, under 700 words)

Per R4 id: what changed and where. New writer/checker sha256s. Base A and base B `sweep.diff` sha256s and line counts.
Counts per proof on both bases. Any mutant that still passes; any faithful port that fails; every deviation from the
dispositions; the base-B account of differences against `work-after772`; anything needing the orchestrator's decision.
