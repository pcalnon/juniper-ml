# Fix pass 7 brief: pin exact install scripts (the owner's ruling of 2026-11-24)

Written 2026-11-24 (~12:20Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up:** `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`. A `## Fix pass 7`
section means this pass finished: go to round 9 (`$W/tmp/sweep/ROUND9_BRIEF.md`). If there is no such section and
the live checker matches neither its line in `$W/tmp/arc/sweep_scripts.sha256` nor
`$W/tmp/sweep/checker-r8/checker_r7_as_reviewed.py`, the checker is a half-edit: restore that saved copy (`789287c5…`)
and run this brief with a fresh executor.

## Goal

Implement the owner's ruling (verbatim in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "The owner's ruling on the checker's
install-step judgement"): **"Pin exact scripts"**. The checker stops judging port install scripts with its own bash
reader. Instead, each port's install step must equal a pinned, reviewed script for that port. The pins are seeded from
the 15 port simulations and updated in each port's own review.

The checker is `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, now sha256
`789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2` (fix pass 6). It is our own CI tooling: it gates the
ports of juniper-cascor's publish template (#777, `f5ed3017`) into seven repos. Round 9 reviews this change once, then
the ports start.

Read first: the dispositions file's last three sections (§ "Round-8 review", the ruling, and § "Fix pass 6"), round 8's
report `$W/tmp/r8review/ROUND8_REPORT.md`, and the checker's docstring.

## Design (decide the details; state each decision in the docstring)

- **What is pinned:** every `run` script in each port's `Verify the TestPyPI install` job, keyed by (repo, workflow
  file, step name). Include cascor's own three publishers (repo `juniper-cascor`), because the template's scripts are
  pins too. Pin any other per-port `run` script the checker today judges with its bash reader, if you find one.
- **Where the pins live:** a new data file, `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`. For each key it
  holds the full normalized script text and its sha256. The checker loads it from its own directory by default.
  `--pins PATH` may override it only as an OPERATOR argument, never from anything a workflow contains.
- **The pins file joins the manifest:** `$W/tmp/arc/sweep_scripts.sha256` covers seven paths from now on.
- **Normalization MUST NOT change what bash runs.** YAML already turns `\r\n` into `\n`. Do not strip trailing
  whitespace: `\` followed by a space at the end of a line is an escaped space, and stripping the space turns it into a
  continuation. Instead, REFUSE trailing whitespace, a NUL, and non-printable characters with clear messages. Compare
  everything else byte for byte, comments included, apart from the block scalar's final newline(s) (chomping).
- **A mismatch fails with a useful message:** the key, the first differing line, and a short unified diff. It also
  tells the operator to update the pin through that port's review if the change is intended.
- **Keep everything that is not install-script judgement:** template-block identity, the jobs, `needs`, permissions,
  environments, env-key rules (`BASH_ENV`, `PIP_*`, …), the build window's exact allow-list, `--repo` scoping, and
  `LAG_ERROR`.
- **Remove the bash-reader rules wherever an exact pin now covers the script.** Keep the reader only where something
  still needs it (say where and why), apply round 8's probed fixes there
  (`$W/tmp/r8review/fixprobe/checker_r8_fixprobe.py`: R8-1's descriptor rule, R8-2's `_`, R8-3's `lex` for if
  conditions and the last command), and keep fix pass 5's line rules there. A smaller checker is the point.
- **Seeds:** take the 15 simulations' install scripts (`$W/tmp/sweep/checker-r7/port-sim/`, or fix pass 6's latest
  regenerated copies) and cascor's three from `main` (`f5ed3017`; fetch read-only with
  `$W/util/ad-hoc/2026-11-15_fetch_pr_files.py`). Several ports' FINAL scripts will differ from the simulations: R4-5's
  `find_spec` for cascor-client, cascor-worker, data, data-client, ml ci-tools and ml observability; ml `publish.yml`'s
  template lag text with `tests/test_publish_testpypi_verify.py:477` (R5-F5). Seed from the simulations anyway, and list
  these expected pin updates in the docstring and the dispositions, so each port's review knows to make them.

## Re-run (logs under `$W/tmp/sweep/checker-r8/evidence/`)

1. cascor's three publishers: 3/3 PASS, from the landing tree and from cascor `main`.
2. The 15 simulations: 15/15 PASS.
3. Every earlier mutant set must FAIL, with the controls PASSING: R8 (B8-*), N7, R6, N6, N5, R5, M, round 2's, N. Many
   now fail with a pin mismatch, which is correct. Report each set's count.
4. Harmless install-script edits from earlier rounds that used to PASS (comments, `set -eu`, renamed variables, tabs,
   redirections …) now FAIL BY DESIGN (a pin mismatch). Count and list them as "by design under the ruling".
   Harmless edits OUTSIDE install scripts must keep their earlier verdicts.
5. New proof cases in `checker_proof_r8.py` (a copy of r7's, re-baselined; state every changed verdict and why):
   - trailing whitespace: FAIL, including `\` followed by a space;
   - one changed comment character: FAIL;
   - CRLF in the YAML: PASS (YAML normalizes it);
   - a pin key for the wrong repo: FAIL;
   - a missing pin: FAIL, with a clear message;
   - `--pins` pointing at a tampered file: refused when the stored sha256 disagrees with the text.
   - Also add at least 6 new EXECUTED negative-test mutants (stand-in pip/python/sleep under `bash -e`, as
     `$W/tmp/r8review/` shows). Each must FAIL.
6. pre-commit and B914 on the checker and the pins file (juniper-ml's config); `--help`.

## Outputs

- **Before editing:** copy the checker to `$W/tmp/sweep/checker-r8/checker_r7_as_reviewed.py`, and the manifest to
  `$W/tmp/arc/sweep_scripts.r8.sha256`.
- **After:**
  - `checker-r8/checker_r7_to_r8.diff`;
  - the pins file;
  - the manifest, regenerated over SEVEN paths (the writer's line stays `c47940ad…`).
- **Append** `## Fix pass 7 (the owner's exact-pins ruling; checker-r8)` to the dispositions file, in the earlier
  sections' style. Include the list of expected per-port pin updates.
- **Write** `$W/tmp/sweep/ROUND9_BRIEF.md`, following ROUND8_BRIEF.md's structure and aimed at the r7 -> r8 interdiff
  and the pins file, with the new hashes. It must state:
  - the mutants are negative test cases for our own CI gate;
  - the report goes to `$W/tmp/r9review/ROUND9_REPORT.md`, and is also returned;
  - any undone step is reported first;
  - the stopping rule is unchanged: no port until a COMPLETE round reports no BLOCKER and no MAJOR.

  It should also ask the reviewer to try to make the normalization or the pin lookup diverge from what the runner
  executes. That is the class the ruling exists to close.

## Rules

Fix pass 6's rules apply unchanged (`$W/tmp/sweep/FIXPASS6_BRIEF.md` § Rules), with `checker-r8/` as your directory and
the pins file as an extra file you may write. Never write under `/tmp`. Delete nothing. Use read-only `gh` GETs only.
Never push, commit, open, comment on, approve or merge anything. No secrets or personal data. Write script files rather
than complex command lines, and return to `$W` after any `cd`.

## Report (your last message, under 500 words)

- The design decisions.
- The new checker's sha256, its size before and after, and the interdiff's size.
- The pins file's path and sha256, and its key count.
- Counts for every re-run, with the by-design FAIL list.
- Any mutant that still passes, and any simulation that fails.
- The expected pin updates per port.
- The path of `ROUND9_BRIEF.md`.
