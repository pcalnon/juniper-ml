# Landing-prep brief: the cascor sweep PR, on cascor `main` as it is now

Written 2026-11-23 by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.
Round 5 found no BLOCKER or MAJOR in cascor's tree; its one MAJOR is in the port checker, which is not part of this
PR (`$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-5 review", the orchestrator's decision paragraph).

## Goal

Rebuild the sweep with the reviewed writer on a FRESH clone of juniper-cascor `main`, verify everything, bring the PR
texts up to date, and pass the pre-push gate. STOP before any upload: the orchestrator opens the PR and merges it.

## Inputs (READ-ONLY)

- Writer `$W/util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`: its sha256 must be
  `c47940add4abcfa6e087c3454d81a00fdb328b3e0e71c36a5aeaf2b0a31c352a` (round 5's reviewed writer plus NIT 8's one
  CHANGELOG wording fix). On a mismatch, STOP.
- Checker: use ONLY the frozen copy `$W/tmp/sweep/cascor-r4/checker_r4_as_reviewed.py` (sha256 `c826ab87…`). The live
  checker in `$W/util/ad-hoc/` is being changed by a parallel fix pass (round 5's MAJOR is in the checker, which gates
  the ports, not this PR); never run or read the live one.
- Round 5's dispositions: `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-5 review" (the decision paragraph and the
  table). The text findings you apply are R5-F1, R5-F2, R5-F6 and R5-F8 (step 5).
- The reviewed trees: `$W/tmp/sweep/cascor-r4/main/juniper-cascor` (base B, cascor `e9c86f83`), and round 5's
  report in `$W/tmp/r5review/` (plus any "Round-5 review" / fix section in `REVIEW_DISPOSITIONS.md`).
- Fix pass 3's drivers and texts in `$W/tmp/sweep/cascor-r4/` (`rerun_all.bash`, `final_*.bash`, `run_*.bash`,
  `make_r4_harness.py`, `checker_proof_r4.py`, `pr_body.md`, `commit_message.txt`) and round 3's tools in
  `$W/tmp/sweep/cascor-r3/` (`mutation_proof.py`, `workflow_reader_tests.txt`, `predict_symbol_loss.py`, `venv-b914`).
  Copy any driver you need into `$W/tmp/sweep/land/` and adapt the copy; never edit the originals.

## Steps

1. **Clones.** `python3 -I $W/util/ad-hoc/2026-11-15_publish_port_clone.py --dest-root $W/tmp/sweep/land/head juniper-cascor`
   and the same with `--dest-root $W/tmp/sweep/land/base` (read the tool's header; it refuses an existing
   destination). Both HEADs must equal `gh api repos/pcalnon/juniper-cascor/commits/main --jq .sha`; record it.
2. **Writer** on the `land/head` clone, `--date` = `date -u`'s day. Keep `--changelog-cases`/`--changelog-mutations`
   at the reviewed values unless this run's counts differ (then use this run's and say so).
3. **Account.** Diff the result against `cascor-r4/main/juniper-cascor` and explain EVERY difference. Expected: only
   what cascor merged after `e9c86f83` (#774 `829af03d`: none of the sweep's eleven files; #776 `36dd6f2d`:
   `CHANGELOG.md`), and nothing else. Any other difference: STOP and report it.
4. **Verify** on `land/head` (conda env `JuniperCascor1`, `env -u JUNIPER_CASCOR_LOG_DIR`), logs into
   `$W/tmp/sweep/land/evidence/`:
   - both test modules (161 on round 4's run) and the 14 files in `cascor-r3/workflow_reader_tests.txt`;
   - `cascor-r3/mutation_proof.py` (all caught), and the round-4 test-lens harness (all property-breaking edits caught,
     all harmless pass, C4/D1/D2 fail by design);
   - the frozen checker copy (`checker_r4_as_reviewed.py --repo juniper-cascor --template <land/head publish.yml>`) on
     the three workflows: PASS (do not re-run `checker_proof_r4.py`; it belongs to the checker's own fix pass);
   - actionlint on the three workflows; pre-commit through
     `$W/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/precommit_in_copy.py SRC DEST /opt/miniforge3/bin/pre-commit FILE…`
     on the eleven files; B914 on the changed `.py`; the symbol-loss screen once per changed test module with
     `land/base` as BASE_TREE and `--trailers <the commit body>`; the docs screen and the markdown-structure delta as
     fix pass 3's `final_lint_and_screens.bash` runs them.
5. **Texts.** Copy `cascor-r4/pr_body.md` and `cascor-r4/commit_message.txt` into `$W/tmp/sweep/land/`. Update every
   base, SHA and count to THIS run's (state the landing base; say #774 and #776 merged after `e9c86f83`, and what #776
   changed). Apply every round-5 text finding:
   - R5-F6: the base, the Testing table's columns, #774 and #776;
   - R5-F8: "a `concurrency` group that never cancels a run" becomes "a `concurrency` group without
     `cancel-in-progress`" in the PR body and the commit body (the writer already says so in `CHANGELOG.md`);
   - R5-F1/R5-F2: the PR body must make NO claim about what the cross-repo checker refuses or closes (round 5 broke
     those claims; the checker is being fixed separately and is not part of this PR). Replace the checker's coverage
     paragraph(s) (round 5 cites `pr_body.md:348-356`) with one neutral sentence: the juniper-ml checker
     `util/ad-hoc/2026-11-23_publish_port_template_identity.py` passes these three workflows, and its own review
     continues in juniper-ml before any port. Keep the facts round 5 re-measured.
   Keep the `Allow-Symbol-Loss:` line and the attribution lines exactly:
   commit body ends `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` then
   `Claude-Session: https://claude.ai/code/session_016H76Aje9K5yyjAb1ZUQvPo` (the LAST paragraph, nothing after); the
   PR body ends `🤖 Generated with [Claude Code](https://claude.com/claude-code)`, a blank line, then
   `https://claude.ai/code/session_016H76Aje9K5yyjAb1ZUQvPo`. Write `land/commit_headline.txt` (line 1 of the message)
   and `land/commit_body.txt` (line 3 onward). The PR body must stay under 65,000 characters.
6. **Gate.** `python3 -I $W/util/ad-hoc/2026-11-15_build_gate_payload.py --out $W/tmp/sweep/land/gate --tree <land/head clone> --base-tree <land/base clone> --text $W/tmp/sweep/land/pr_body.md --text $W/tmp/sweep/land/commit_body.txt <the eleven paths>`
   (read its header first), then `bash $W/util/ad-hoc/2026-11-15_pre_push_gate_run.bash $W/tmp/sweep/land/gate`. Only
   exit 0 passes. Read every masked-read line it prints and classify each.
7. **ARGS.** Write `$W/tmp/sweep/land/ARGS.json` for
   `$W/util/ad-hoc/2026-11-15_cascor_one_artifact_helpers/run_open_signed_pr.py` (read its header): `repo`
   `juniper-cascor`, `base` `main`, `branch` `fix/publish-one-artifact-sweep`, `tree` = the land/head clone, `paths` =
   the eleven files, `message` = the headline, `commit_body_file`, `title` = the headline, `body_file`. Confirm the
   branch does not exist yet (`gh api repos/pcalnon/juniper-cascor/branches/fix/publish-one-artifact-sweep` → 404).

The eleven paths: `.github/workflows/publish.yml`, `.github/workflows/publish-cascor-model.yml`,
`.github/workflows/publish-protocol.yml`, `src/tests/unit/test_publish_one_artifact.py`,
`src/tests/unit/test_publish_docs_bounds.py`, `docs/ci_cd/MANUAL.md`, `docs/ci_cd/REFERENCE.md`,
`docs/ci_cd/QUICK_START.md`, `docs/DEVELOPER_CHEATSHEET.md`, `AGENTS.md`, `CHANGELOG.md`.

## Rules

- Never write under `/tmp` or `/var/tmp`; everything new goes under `$W/tmp/sweep/land/`. Delete nothing that existed
  before you started.
- Read-only `gh` GETs only. Never push, never run `open_signed_pr.py` or `run_open_signed_pr.py` (not even
  `--dry-run`), never `git commit` in `$W`, never open, comment on, approve or merge a PR.
- The Bash guard refuses `git -C`, `cd` into another worktree combined with git, and some heredocs: use script files.
- No secrets, tokens, e-mail addresses or personal data in any output. Take times from `date -u`; never estimate one.

## Report (your last message, under 500 words)

The landing base SHA; the account of differences; each check's command and counts; the gate's exit and the masked-read
classification; the text changes you made; the paths of `ARGS.json`, `pr_body.md`, `commit_headline.txt`,
`commit_body.txt`; anything that made you stop.
