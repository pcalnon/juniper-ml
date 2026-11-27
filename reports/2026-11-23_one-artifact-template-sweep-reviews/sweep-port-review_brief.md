# Brief: independent review of one one-artifact SWEEP port pull request

Written 2026-11-26 by the orchestrating session `b71989` (juniper-ml worktree `moonlit-percolating-sun`). Your prompt
names the repository and the pull request. You review it cold: you get the PR and the requirements, not the porting
session's account of it. Run things; do not take a claim (the PR body's included) on trust.

- `WT=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun` -- you may
  Write/Edit only inside `$WT`. Your scratch dir: `$WT/tmp/ports/<repo>/review/` (create it).
- `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock` -- read-only.

## What the PR must be

The requirements the porting session worked from: `$WT/tmp/ports/SWEEP_PORT_BRIEF.md` (read it whole), which builds on
`$W/tmp/ports/SWEEP_BRIEF.md` § "What the sweep changes" (items A-G). The template is juniper-cascor #777 (`git diff
36dd6f2d f5ed3017` in the read-only clone `$WT/tmp/ports/clones/juniper-cascor`; `gh pr view 777 --repo
pcalnon/juniper-cascor` for its body).

## What to do

1. **Fetch the PR as GitHub holds it**, never the porting session's local tree:
   `cd $WT/tmp/ports/<repo>/review && git clone https://github.com/pcalnon/<repo> head && cd head && git fetch origin pull/<N>/head && git checkout FETCH_HEAD`
   (plain `cd … && git …`; never `git -C`). Record the head sha and confirm it is the PR's `headRefOid`
   (`gh pr view <N> --repo pcalnon/<repo> --json headRefOid,baseRefOid,files`). Read the whole diff against its base.
2. **The checker**, FINAL, never edited (`$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
   `a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35`), on the fetched head's publishers, all on one
   command line, with the pins the PR proposes (`$WT/tmp/ports/<repo>/pins.proposed.json` if it exists, else
   `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`):

       /opt/miniforge3/envs/JuniperCascor1/bin/python3 -I -B <checker> --repo <repo> \
           --template $WT/tmp/ports/clones/juniper-cascor/.github/workflows/publish.yml --pins <pins> <head>/.github/workflows/<publisher>.yml ...

   (If the Bash guard refuses a line naming `.github` paths, put it in a script under your scratch dir.) Then judge the
   proposed pin change itself, if any: diff it against `$W`'s pin; is each changed line what the step needs, and does it
   do what it claims under `bash -e {0}` (run the script against stub `pip`/`python` if in doubt)? A `find_spec` check
   must fail when the module is absent or a bare namespace directory (no origin), including with `PYTHONOPTIMIZE=1`.
3. **Template fidelity**: every template block (steps whose comment says "copy verbatim", the whole `republish` job)
   byte-identical to cascor `main`'s; the install job's wiring (name `Verify the TestPyPI install`, `needs` the TestPyPI
   job, exactly `contents: read`, no environment, every command from `$RUNNER_TEMP`, nothing run from a checkout); the
   TestPyPI job (`id-token: write` alone, no checkout/setup-python left, ends at `Verify TestPyPI serves exactly these
   files`); the PyPI job (`needs` both, `id-token: write` alone); `PUBLISH_TAG_PREFIX` and its agreement with the build
   guard; the comment corrections (SWEEP items 1, 2, 12). Anything the repo kept (its own build, smoke, tag-assert steps,
   extra jobs) must keep its behaviour.
4. **Tests**: run the repo's publish test module(s) and every test the PR touches, in the repo's environment (its
   `AGENTS.md`; JuniperCanopy1 for canopy, JuniperData for data, otherwise JuniperCascor1), on the fetched head. Count
   passed/failed/skipped; any NEW skip in a publish test is a finding. Then make at least 5 mutations of your own (not
   the PR body's list) to a COPY of the head's workflow(s) -- each a change the sweep exists to prevent -- and confirm the
   suite fails on each. A mutation the suite misses is a finding. Check the port of #777's test hardening is complete
   (SWEEP item E, the B and C rehearsals) and that the removed `TestFindReleaseRun` case is what #777 removed.
5. **Docs and changelog**: every statement the PR adds or keeps about the publish pipeline is true of the head's
   workflows (job names, permissions, bounds, the ladder's rungs, the dispatch command for THIS repo); no text the
   sweep makes false is left; links resolve to real anchors in cascor `main`'s `docs/ci_cd/MANUAL.md`;
   `**Last Updated**` lines are what CI's date check wants; `CLAUDE.md` stays a symlink; wording ("Overtoad"/"owner")
   follows the brief, and no technical `owner` was renamed.
6. **CI**: `gh pr checks <N> --repo pcalnon/<repo>`; report each failing or pending required check with its reason (read
   the log for a failure). Do not re-run anything.
7. **The commit**: one commit, signed and verified (`gh api repos/pcalnon/<repo>/commits/<sha> --jq .commit.verification`);
   its body holds the `Allow-Symbol-Loss:` line for each symbol the repo's symbol-loss screen reports, and its trailers
   are the LAST paragraph.

## Severity

- **BLOCKER**: the PR would publish wrong bytes, mint where it must not, let a failed check pass, break a release or a
  republish, or fails the checker.
- **MAJOR**: a defect that can mislead an operator into a wrong recovery, a test that misses a regression the sweep is
  meant to stop, a template block not byte-identical, a doc statement false of the workflow.
- **MINOR**: a real but contained defect (an incomplete doc, a weak test, a wording-rule miss).
- **NIT**: style.

## Hard rules

- Read-only on GitHub: `gh` GETs only (`gh pr view`, `gh pr checks`, `gh api` GET, `gh run view --log-failed`). Never
  comment, review, approve, push, merge, arm, re-run, close or edit anything.
- Never write under `/tmp` or `/var/tmp`, never edit the checker or anything under `$W`, never touch any other clone,
  worktree or sibling primary checkout. Mutations go on copies in your scratch dir.
- Quote only numbers and SHAs a tool printed. No secrets or personal data in any file.

## Report

Write `$WT/tmp/ports/<repo>/review/REVIEW.txt` BEFORE your final message, and make the final message the same text.
First section: **What was not done** (any step skipped or cut short, and why). Then the verdict line
(`BLOCKER n, MAJOR n, MINOR n, NIT n`), then each finding: id, severity, file:line on the head, what is wrong, the
command or mutation that shows it, and the fix you propose. Then the checker's output lines, the test counts, your
mutation table, and the CI state.
