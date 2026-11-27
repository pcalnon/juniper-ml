# Fix pass 8 brief: the port checker's job structure and YAML typing, after round 9

Written 2026-11-24 (~14:10Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up**, run `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`:
- A `## Fix pass 8` section means this pass finished. Go to round 10 (`$W/tmp/sweep/ROUND10_BRIEF.md`).
- No such section: compare the live checker and pins file with their lines in `$W/tmp/arc/sweep_scripts.sha256` and
  with the copies `$W/tmp/sweep/checker-r9/checker_r8_as_reviewed.py` (`039e5e6d…`) and
  `$W/tmp/sweep/checker-r9/pins_r8_as_reviewed.json` (`fde7e0ca…`). Where they match neither, they are half-edits:
  restore those copies and run this brief with a fresh executor.

## Goal

Fix round 9's findings in the port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256
`039e5e6d5830955c1593ccdec4b7bfdbc0bc1558c305d21fca85b47ff4bc13e0`, fix pass 7) and, where needed, the pins file
`$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json` (`fde7e0ca…`). Re-run every proof and write the round-10
brief. The checker is our own CI tooling: it gates the ports of juniper-cascor's publish template (#777, `f5ed3017`)
into seven repos, and the owner's ruling "Pin exact scripts" stands. Round 9 found fix pass 7's pin code sound. Its
findings are one level out: what runs beside, or before, the pinned script, and how values are typed.

Read first, in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: § "Round-9 review" (your work list), then round 9's report
`$W/tmp/r9review/ROUND9_REPORT.md` with its `mutants/`, `parsers/` and `evidence/`, then § "Fix pass 7".

## Scope

- **B9-1 (BLOCKER) and M9-A (MAJOR).** Hold every job in the template's chain (the build, TestPyPI, install, PyPI
  and republish jobs) to an exact job-key set.
  - The set is the template's own keys plus only the extras the reviewed policy admits: a job's `timeout-minutes`,
    except on the republish job.
  - Compare the values wherever the template fixes them: `runs-on: ubuntu-latest`, `permissions`, `environment`,
    `needs`, `if`.
  - This refuses `container:`, `services:` and any other `runs-on` on every one of these jobs. Check that the 15
    simulations and cascor's three still pass, and say which keys each job may carry.
- **M9-B (MAJOR).** In the install job, setup-python's `with:` admits `python-version` only, with the template's
  value. Do the same wherever else the chain uses setup-python, if it does. Correct the note at `:169`.
- **M9-C (MAJOR).** Values must be typed as GitHub types them (YAML 1.2 core).
  - Either load plain scalars with YAML 1.2 core resolvers, or refuse every plain scalar whose 1.1 and 1.2 readings
    differ: `yes`/`no`/`on`/`off` and their cases, sexagesimal `1:30`, leading-zero `0132`, `0b…`, `0o…`, `.inf`, `~`.
  - Prove that `retention-days: 1:30`, `0132` and `default: no` all FAIL, and that every current file keeps its
    verdict.
- **m9-a (MINOR).** Accept at most one final newline after a pinned script, which settles `|`, `|-` and `|+`.
  M9-11 must FAIL.
- **m9-b (MINOR).** Refuse a pins file that is not pure ASCII, and make every pinned text escaped. M9-7 must FAIL.
- **n9-a, n9-b, n9-c (NIT).**
  - Write true messages for the NEL, BOM and no-break-space refusals; keep the refusals.
  - Name the pins file actually used in the mismatch message.
  - Refuse a step that is not a mapping cleanly, and go on to check the remaining workflows.

Out of scope: the writer, every workflow, cascor's tree, every port.

## Re-run (logs under `$W/tmp/sweep/checker-r9/evidence/`)

Copy fix pass 7's drivers from `$W/tmp/sweep/checker-r8/` into `$W/tmp/sweep/checker-r9/` and adapt the copies (never
edit fix pass 7's). Round 9's tools in `$W/tmp/r9review/` (its mutants, parsers and drivers) are read-only; copy any you
use.
1. cascor's three publishers: 3/3 PASS, from the landing tree and from cascor `main`.
2. The 15 simulations: 15/15 PASS. The 18 pins must re-derive equal.
3. Every mutant set:
   - Round 9's M9-1 to M9-16 and P9-2, and fix pass 7's X8-1 to X8-8: every bypass FAILS.
   - Every earlier set keeps the verdicts fix pass 7 recorded.
   - The controls PASS.
   - Build at least 6 new EXECUTED negative-test mutants aimed at your changes, for example a job-key alias, a
     `runs-on` list, a flow-style `services`, and a `with:` given through an anchor. Each must FAIL.
4. `checker_proof_r9.py`, a copy of r8's: earlier cases keep their verdicts unless you state why; add FAIL and PASS cases
   for each change. All must pass.
5. Run round 9's YAML divergence fuzz again on the new checker, using copies of its drivers: still no case where PyYAML
   and GitHub's lineage both parse and read different text.
6. Run pre-commit and B914 on the checker and on the pins file, then `--help`.

## Outputs

- **BEFORE editing**, copy:
  - the checker to `checker-r9/checker_r8_as_reviewed.py`;
  - the pins file to `checker-r9/pins_r8_as_reviewed.json`;
  - the manifest to `$W/tmp/arc/sweep_scripts.r9.sha256`.
- **AFTER**: write the interdiffs (checker, and pins if it changed) into `checker-r9/`. Regenerate the manifest over the
  seven paths; the writer's line stays `c47940ad…`.
- **Append** `## Fix pass 8 (round 9's fixes; checker-r9)` to the dispositions file, in the earlier sections' style.
- **Write `$W/tmp/sweep/ROUND10_BRIEF.md`**, following ROUND9_BRIEF.md's structure and aimed at the r8 -> r9 interdiffs,
  with the new hashes. It must state:
  - the mutants are negative test cases for our own CI gate;
  - the reviewer writes its report to `$W/tmp/r10review/ROUND10_REPORT.md` and also returns it;
  - any step not done is reported first;
  - the stopping rule is unchanged.

  It should also ask the reviewer to look one level further out again, at anything still outside the job-key sets that
  could run code beside the credential-holding jobs.

## Rules

Fix pass 7's rules hold unchanged (`$W/tmp/sweep/FIXPASS7_BRIEF.md` § Rules), with `checker-r9/` as your directory:
- never write under `/tmp`;
- delete nothing;
- read-only `gh` GETs only;
- never push, commit, open, comment on, approve or merge anything;
- no secrets or personal data;
- use script files rather than complex command lines;
- return to `$W` after any `cd`.

## Report (your last message, under 450 words)

Per round-9 id: what changed. The new sha256s and the interdiffs' sizes. The key sets per job. Counts for every
re-run, including the fuzz. Any mutant that still passes; any simulation that fails; deviations; the path of
`ROUND10_BRIEF.md`.
