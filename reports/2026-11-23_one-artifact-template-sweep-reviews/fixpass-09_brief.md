# Fix pass 9 brief: upload inputs, extra jobs and action SHAs, after round 10

Written 2026-11-24 (~21:20Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up**, run `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`.
- A `## Fix pass 9` section means this pass finished. Go to round 11 (`$W/tmp/sweep/ROUND11_BRIEF.md`).
- Otherwise, check the live checker and pins file against two references: their lines in
  `$W/tmp/arc/sweep_scripts.sha256`, and `$W/tmp/sweep/checker-r10/checker_r9_as_reviewed.py` (`9cf16a2f…`) and
  `$W/tmp/sweep/checker-r10/pins_r9_as_reviewed.json` (`d539f05f…`). A file that matches neither is a half-edit: restore
  it from those copies and run this brief with a fresh executor.

## Goal

Fix round 10's findings in the port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256
`9cf16a2f13152ddc75ce2f695758a6f5df95f93c713b347b46adc5959c157bb9`, fix pass 8), implement the owner's second ruling,
re-run every proof, and write the round-11 brief. The checker is our own CI tooling; it gates the ports of
juniper-cascor's publish template (#777) into seven repos.

Read first:
- `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-10 review", the work list;
- § "The owner's ruling on action refs", verbatim and binding;
- round 10's report `$W/tmp/r10review/ROUND10_REPORT.md`, with its mutants;
- its sketch `$W/tmp/r10review/candidate_rules_r10.py`, read-only (copy what you use);
- § "Fix pass 8".

## Scope

- **B10-1 (BLOCKER):** hold every upload step (each `pypa/gh-action-pypi-publish` step, and any other step that can
  carry a credential or an index URL) to exactly the keys `{name, uses, with}`.
  - Its `with` must be the template's exact set of literal keys, with the template's values, compared case-sensitively.
  - Refuse any key that differs from a template key in case or in `-`/`_`, and any `${{ … }}` key.
  - R10-1 to R10-4 must FAIL.
- **B10-2 (BLOCKER):** refuse every job outside the template's chain, except an exact allow-list.
  - Today the allow-list holds only juniper-data's `notify-consumers`: its job keys exactly, and its called reusable
    workflow, if any, pinned by sha256 of the file. Fetch that file read-only from juniper-data `main` with
    `$W/util/ad-hoc/2026-11-15_fetch_pr_files.py`.
  - Show that the 15 simulations need no other extra job; if one does, record it as a port change.
  - R10-5, R10-6 and R10-7 must FAIL.
- **B10-3 (BLOCKER), the owner's ruling "Pin template SHAs":**
  - In the jobs that hold `id-token` (TestPyPI, PyPI, republish) and the jobs they need (build, install), every
    `uses:` must equal the template's exact `owner/repo@<40-hex SHA>`.
  - Refuse a template whose ref there is not 40 hex characters.
  - A port step whose action the template does not use in that job is refused.
  - Each repo's own CI keeps item 23's ref-free digests, which is out of scope here.
  - Report every simulation whose refs differ from the template's. Those are expected port changes under the ruling,
    not over-strictness.
  - R10-8 must FAIL.
- **m10-a (MINOR):** catch per workflow, so that a RecursionError, a UnicodeEncodeError or any other crash is reported
  and the next workflow is still judged. Exit non-zero if any workflow failed or crashed.
- **n10-a, n10-b (NIT):** true messages for `runs-on: [ubuntu-latest]` and `persist-credentials: "false"`.
- **Outside the checker, recorded only:** R10-7's root cause, that no publish job ties SHA256SUMS's version to the
  release tag (SWEEP item 28). Do not change the template.

Out of scope: the writer, every workflow, cascor's tree, every port.

## Re-run (logs under `$W/tmp/sweep/checker-r10/evidence/`)

Copy fix pass 8's drivers from `$W/tmp/sweep/checker-r9/` into `$W/tmp/sweep/checker-r10/` and adapt the copies.
Round 10's tools are read-only; copy any you use.

1. cascor's three publishers: 3/3 PASS, from the landing tree and from cascor `main` (fetch it again).
2. The 15 simulations: each PASSES, or FAILS only on action refs the ruling now requires. For those, make
   ref-corrected copies under `checker-r10/port-sim/` and show that each then PASSES; list the changes. The 18 pins
   must re-derive equal.
3. Mutants:
   - Round 10's R10-1 to R10-9 and every earlier set: each bypass FAILS, and every earlier verdict holds unless you
     state why.
   - Controls PASS.
   - At least 6 new EXECUTED negative tests aimed at your changes, where execution applies. For example: a `with` key
     given through an alias or a merge key, an extra job named like a template job, a `uses:` with a short SHA, the
     template's SHA under a different owner/repo, and a reusable workflow called from a template job.
4. `checker_proof_r10.py`, a copy of r9's: all pass, with each changed verdict stated.
5. Round 9's YAML fuzz and fix pass 8's typing differential, re-run on the new checker.
6. Run pre-commit and B914 on the checker and the pins file, then `--help`.

## Outputs

- **Before editing:** copy the checker and the pins file into `checker-r10/` as `*_r9_as_reviewed.*`, and copy the
  manifest to `$W/tmp/arc/sweep_scripts.r10.sha256`.
- **After:**
  - write the interdiffs into `checker-r10/`;
  - regenerate the manifest over its seven paths, leaving the writer's line at `c47940ad…`. If a new allow-list data
    file becomes necessary, add it as an eighth path and say so.
- **Append** `## Fix pass 9 (round 10's fixes and the action-refs ruling; checker-r10)` to the dispositions file.
  Include the per-port ref changes.
- **Write** `$W/tmp/sweep/ROUND11_BRIEF.md`, following ROUND10_BRIEF.md's structure and aimed at the r9 -> r10
  interdiffs, with the new hashes. It must:
  - state that the mutants are negative test cases for our own CI gate;
  - send the report to `$W/tmp/r11review/ROUND11_REPORT.md` as well as returning it;
  - put any step not done first;
  - keep the stopping rule unchanged;
  - ask the reviewer to look one level further out again: anything left in a workflow that the checker reads but
    does not judge, or never reads at all.

## Rules

Fix pass 8's rules hold, with `checker-r10/` as your directory:
- never write under `/tmp`;
- delete nothing;
- read-only `gh` GETs only;
- never push, commit, open, comment on, approve or merge anything;
- no secrets or personal data;
- use script files, and run Python with `-B` so no `.pyc` lands in a frozen directory;
- return to `$W` after any `cd`.

## Report (your last message, under 450 words)

- Per round-10 id: what changed.
- The new sha256s, and the size of each interdiff.
- The extra-job allow-list.
- The per-port ref changes.
- Counts for every re-run.
- Any mutant that still passes, and any simulation that fails for another reason.
- Deviations from this brief.
- The path of `ROUND11_BRIEF.md`.
