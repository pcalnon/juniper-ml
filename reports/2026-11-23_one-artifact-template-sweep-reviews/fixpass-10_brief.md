# Fix pass 10 brief: output escaping, aliases, the build job's pre-build steps, concurrency, after round 11

Written 2026-11-24 (~23:10Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up**, first run `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`:
- A `## Fix pass 10` section means this pass finished. Go to round 12 (`$W/tmp/sweep/ROUND12_BRIEF.md`).
- Otherwise, check the live checker against its line in `$W/tmp/arc/sweep_scripts.sha256` and against
  `$W/tmp/sweep/checker-r11/checker_r10_as_reviewed.py` (`23707ac6…`). If it matches neither, it is a half-edit:
  restore it from that copy, then run this brief with a fresh executor.

## Goal

Fix round 11's findings in the port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256
`23707ac6de0b351291372ec7a3c07eb2f328c2200d80f831dacf4976e393ba35`, fix pass 9). Then re-run every proof and write the
round-12 brief.

The checker is our own CI tooling. It gates the ports of juniper-cascor's publish template (#777) into seven repos. The
owner's two rulings stand: "Pin exact scripts" and "Pin template SHAs".

Read first:
- the work list: § "Round-11 review" of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`;
- round 11's report, `$W/tmp/r11review/ROUND11_REPORT.md`, and its `evidence/` and mutants;
- § "Fix pass 9".

## Scope

- **M11-A (MAJOR):** make what the checker prints impossible to forge.
  - Refuse, in every loaded string (keys and values, at every depth), any character other than printable text, a tab
    or a newline.
  - Refuse a newline in any key, and in any step or job `name`.
  - Print every workflow-derived value with `!r`, or an equivalent escape.
  - Escape C0 and C1 control characters in ALL output, as defence in depth.
  - M11-1, M11-2 and M11-3 must be refused. Show with a terminal emulator, as round 11 did with tmux 3.6, that the
    displayed text now matches the verdict.
- **M11-B (MINOR):** refuse anchors and aliases at load, before any walk, so an alias bomb fails fast. M11-4 must
  fail at once, and the next workflow on the command line must still be judged.
- **M11-C (MINOR):**
  - Admit `actions/upload-artifact` in the build job only as the `Upload dist artifacts` step.
  - Refuse a write to `$GITHUB_ENV` or `$GITHUB_PATH` in the build job's own `run` steps if all 37 files round 11
    listed admit it. Otherwise document it as a residual.
  - Correct the docstring's account of what steps before the build can reach.
  - M11-9 and M11-12 must be refused, or documented as residuals with the reason.
- **M11-D (MINOR):**
  - A workflow-level `concurrency` group must be exactly `<workflow file stem>-${{ github.ref_name }}` with
    `cancel-in-progress: false` (all 37 files admit it).
  - Correct the reasoning at the old `:55-58`.
  - M11-10 must be refused.
- **M11-E (MINOR):** correct the docstring at the old `:266-268`. The SHA pin does not bind the publish action's
  container image, a re-pushable registry tag, so name that as a residual.
- **n11-a to n11-e (NIT):**
  - give true messages: the CRLF-only difference in the called file, `PyPA/…` case, and the two-refs reason;
  - rename the local `installs` in `template()`;
  - record `needs: [pypi]` and `verbose: "true"` as refused by design.

Out of scope: the writer, every workflow, cascor's tree and every port.

## Re-run (logs under `$W/tmp/sweep/checker-r11/evidence/`)

Copy fix pass 9's drivers from `$W/tmp/sweep/checker-r10/` into `$W/tmp/sweep/checker-r11/` and adapt the copies. Round
11's tools are read-only: copy any you use.
1. cascor's three: 3/3 PASS, from the landing tree and from cascor `main` (fetch it again).
2. The 15 simulations: 15/15 PASS, with juniper-data's `notify-consumers.yml` beside it. The 18 pins re-derive equal.
3. Mutants:
   - M11-1 to M11-12 and every earlier set: every bypass FAILS, and earlier verdicts hold unless you state why.
   - The controls PASS.
   - At least 6 new negative tests aimed at your changes, EXECUTED where execution applies. For example: an escape in
     a key, an escape in a pins-file text, a C1 control, an alias in a `with`, a near-miss concurrency group, and
     `upload-artifact` under a second name.
4. `checker_proof_r11.py`, a copy of r10's: all cases pass, with each changed verdict stated.
5. The YAML fuzz and the typing differential, re-run.
6. pre-commit and B914 on the checker; `--help`.

## Outputs

- **Before editing:** copy the checker to `checker-r11/checker_r10_as_reviewed.py` and the manifest to
  `$W/tmp/arc/sweep_scripts.r11.sha256`.
- **After:**
  - the interdiff;
  - the manifest, regenerated over its seven paths, with the writer's line still `c47940ad…`.
- **Append** `## Fix pass 10 (round 11's fixes; checker-r11)` to the dispositions file. Include the residuals for plan
  v1.15.18: the container-image tag (M11-E), and any M11-C residual.
- **Write** `$W/tmp/sweep/ROUND12_BRIEF.md`, with ROUND11_BRIEF.md's structure, aimed at the r10 -> r11 interdiff, with
  the new hashes. It must keep:
  - the negative-test framing;
  - the report file `$W/tmp/r12review/ROUND12_REPORT.md`;
  - "not done" first;
  - the stopping rule.

  It must also ask the reviewer whether any finding class from rounds 4-11 can still be reached in a new form.

## Rules

Fix pass 9's rules hold, with `checker-r11/` as your directory:
- never write under `/tmp`;
- delete nothing;
- read-only `gh` GETs only;
- never push, commit, open, comment on, approve or merge anything;
- no secrets or personal data;
- use script files and Python `-B`;
- return to `$W` after any `cd`.

## Report (your last message, under 400 words)

- Per round-11 id: what changed.
- The new sha256 and the interdiff's size.
- The residuals.
- Counts for every re-run.
- Any mutant that still passes, and any simulation that fails.
- Deviations from this brief.
- The path of `ROUND12_BRIEF.md`.
