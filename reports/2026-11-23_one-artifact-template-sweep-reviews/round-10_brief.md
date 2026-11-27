# Round-10 review brief: fix pass 8 on the cross-repo port checker (`checker-r9`): the jobs' keys and YAML 1.2 typing

Written 2026-11-24 (15:04Z) by fix pass 8's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**What this work is.** The checker under review is our own CI tooling: it decides whether a repository's ported
publish workflow matches juniper-cascor's reviewed template, and it refuses edits that would weaken that workflow's
safety checks (a hidden install, a swallowed failure, a step that runs other code, a job that runs somewhere else).
The "mutants" in this brief are negative test cases for that gate: deliberately weakened copies of our own workflows,
run only on this host with logging stand-ins for `pip`, `python`, `sleep` and the uploads, to prove the gate refuses
them. This is defensive testing of a gate we own; nothing is published, pushed or sent anywhere.

**Stopping rule (unchanged).**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 9), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a COMPLETE round reports no BLOCKER and no MAJOR. A round with an undone
  step clears nothing, so an interrupted step must be reported as interrupted.

## The prompt

Round-10 adversarial review of FIX PASS 8 on the cross-repo checker that gates the ports of juniper-cascor's publish
template into seven other repos. Round 9 found fix pass 7's exact-pin comparison sound and four gaps one level outside
it (B9-1 BLOCKER, M9-A, M9-B, M9-C MAJOR): the jobs that hold the upload credential admitted `container`, `services` and
any `runs-on`; the install job admitted `services`; setup-python's `with:` went unread; and PyYAML typed values by YAML
1.1 where GitHub uses YAML 1.2's core schema. Fix pass 8 holds every job of the chain to an exact key set, setup-python
to `python-version` alone, and types every value as GitHub's reader does. Review the r8 -> r9 interdiffs (the checker
and the pins file) once, then hunt for bypasses. Treat fix pass 8's new code as the least trustworthy part: rounds 4 to
9 each found the previous pass's new code, or the level just outside it, the weakest. Out of scope: juniper-cascor's
tree, the writer (`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`), `$W/tmp/sweep/land/` (never touch it),
every workflow and every port, and the ports' own items (R4-1, R4-5, R5-F5: each port's review makes its own pin update).

**The class this round exists to close, one level further out again.** Each round has found code that runs beside, or
before, what the checker compares. Fix pass 8 closed the five chain jobs' keys. **Look at anything still outside the
job-key sets that could run code beside the credential-holding jobs** (the TestPyPI, PyPI and republish jobs, which hold
`id-token: write`), or change what they upload. Fix pass 8 noted three leads and did not verify them (§ "Fix pass 8" of
the dispositions file, "Found beyond the brief"):
- **extra jobs** are noted, never judged: one with `needs: build` might replace the `<PUBLISH_PACKAGE>-dist` artifact
  (upload-artifact's `overwrite: true`) before the TestPyPI job downloads it, so that every template check passes on
  files the build job never made; and an extra job can call a reusable workflow with `secrets: inherit`;
- the **upload steps' own** `env` and `with` beyond the four inputs checked (a `TWINE_*` env key is not refused);
- item 23's residual: every action's `@ref` is dropped.

Also consider another workflow of the same repository triggered by the same release, `workflow_run`, and anything a
run's earlier attempt leaves behind.

**Write your full report to `$W/tmp/r10review/ROUND10_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it. **If any step or sub-step below is interrupted or not done, for any
reason (a safety interruption, a time or context limit, a tool failure), say so in a FIRST section titled "What this
round did NOT do", listing exactly which steps and sub-steps were not done and why, and do not present the round as
complete.** Write that section as soon as an interruption happens, before anything else.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r10review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `9cf16a2f13152ddc75ce2f695758a6f5df95f93c713b347b46adc5959c157bb9` (1172 lines); a frozen copy is
  `$W/tmp/sweep/checker-r9/checker_r9_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- The pins file it reads by default: `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`, sha256
  `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3` (18 pins, 552 lines); a frozen copy is
  `$W/tmp/sweep/checker-r9/pins_r9_as_delivered.json`. Only its `about` changed (`update_pins_about_r9.py`).
- As round 9 reviewed them: `$W/tmp/sweep/checker-r9/checker_r8_as_reviewed.py`, sha256
  `039e5e6d5830955c1593ccdec4b7bfdbc0bc1558c305d21fca85b47ff4bc13e0` (953 lines), and
  `$W/tmp/sweep/checker-r9/pins_r8_as_reviewed.json`, sha256 `fde7e0ca4686ec7ed65bdfb7f5d813e7b75987b4a4e8c0f0e56d46df9efe1906`.
- The interdiffs: `$W/tmp/sweep/checker-r9/checker_r8_to_r9.diff` (530 lines, +270/-51), sha256
  `f019b759b0b829354e18dfa5447f6e90689cdf008a89d81aa9359332e16c0f29`, and `$W/tmp/sweep/checker-r9/pins_r8_to_r9.diff` (10 lines), sha256 `ac7dcc1238c68e450ff545a2e3c6c44f26066dff1e174dc0a2558e097f078994`. If either does
  not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor at `f5ed3017` (#777) and at `main`
  `b5b28dc3` (#779) holds the same three files byte for byte: fix pass 7 fetched `f5ed3017` into
  `$W/tmp/sweep/checker-r8/cascor-f5ed3017-fetch/`, and fix pass 8 re-fetched `main` read-only at 14:29:46Z into
  `$W/tmp/sweep/checker-r9/cascor-main-fetch/` (`evidence/fetch_cascor_main.log`). Re-fetch with read-only GETs if you
  doubt it.
- The 15 port simulations, the seeds of 15 pins: `$W/tmp/sweep/checker-r7/port-sim/` (fix pass 8's regeneration,
  `$W/tmp/sweep/checker-r9/port-sim/`, equals it byte for byte; the rows are in `checker-r9/port_sim_table_r9.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256`, SEVEN lines, sha256 `ba75d4c7cfd6bd3dbb17043da2f179a70404ae88dbbcfbb2bc2e7a909c8ca4fd`; run `sha256sum -c` on it from `$W`.
  Fix pass 7's is kept as `sweep_scripts.r9.sha256`; the checker's and the pins file's lines changed, the writer's stays
  `c47940ad…`.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`). `--pins PATH` replaces the
default pins file, which sits beside the checker; it is an operator argument, and nothing in a workflow chooses it. A
copy of the checker placed elsewhere finds no pins file beside it: pass `--pins`. The checker prints the pins file's
path and sha256 first, and a pins file it refuses stops the run (exit 1, nothing checked).

**Also open to you:** fix pass 8's tools and evidence in `$W/tmp/sweep/checker-r9/`: `rerun_all_r9.bash` (every re-run,
in order, about 10 minutes; `evidence/rerun_all.out`), `finish_r9.bash` (the frozen copies, the interdiffs, the
manifest), `untouched_r9.bash`, `lint_checker_r9.bash`, `survey_job_keys.py` (every job's keys in cascor's three, the
15 simulations and every repository's current workflows), `r9lib.py` and `checker_r9_named.py` (shared plumbing; the
reviewed checker runs through `--checker`), `judge_all_r9.py` (every earlier set, against fix pass 7's recorded
verdicts), `judge_r9_mutants.py` (round 9's own cases), `new_mutants_r8_rerun.py` (fix pass 7's X8 set),
`new_mutants_r9.py` (this pass's executed negative tests N9-1 to N9-9 and controls C9-1 to C9-5),
`checker_proof_r9.py` (built by `make_proof_r9.py` from fix pass 7's proof and `proof_r9_tail.py`),
`run_proof43_r9.bash`, `rederive_pins_r9.py`, `parsers/` (copies of round 9's parser drivers: `fuzz.py` adapted to the
live checker's own filter, `typing_diff.py`, the YamlDotNet 5.3.0 and 16.3.0 dumpers, Node `yaml`; `dn.bash` runs round
9's .NET runtime in place with every home redirected under `checker-r9/parsers/`), and `evidence/`. Earlier passes'
tools are in `$W/tmp/sweep/checker-r8/` and before; round 9's in `$W/tmp/r9review/` (its `external/` holds GitHub's
sources: the runner's `YamlObjectReader.cs`, `TemplateReader.cs`, the workflow schema, setup-python's and
upload-artifact's). Re-run rather than trust them. Run any Python that reads a cloned tree with `python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: § "Round-9 review" (the findings) and
§ "Fix pass 8 (round 9's fixes; checker-r9)" (the decisions, the counts, the leads, the residual risk). The checker's
docstring, § "Fix pass 8: the jobs' keys and YAML 1.2 typing", states every decision. In short:
- B9-1, M9-A: the five chain jobs hold exactly cascor's own test's key sets (`CHAIN_JOB_KEYS`), with `timeout-minutes`
  on all but the republish job (compared whole) and, on a sub-package's build job only, `defaults` exactly
  `{run: {working-directory: <PUBLISH_PACKAGE>}}`; `runs-on: ubuntu-latest` on all five; the environment's `{name,
  url}` mapping holds those keys alone;
- M9-B: every setup-python step of the build and install jobs takes `with: {python-version: "3.N"}` alone (a deviation
  from "the template's value": canopy's port uses "3.14");
- M9-C: `GITHUB_SCALARS`, the runner's MatchNull/MatchBoolean/MatchInteger/MatchFloat transcribed, replaces PyYAML's
  YAML 1.1 resolvers; tags as GitHub's reader admits them; `on` no longer restored; a `0x`/`0o` integer above
  0x7FFFFFFF refused;
- m9-a: one final newline at most; m9-b: an ASCII-only pins file; n9-a: true messages; n9-b: the pins file loaded named;
  n9-c: `shape_problems` and a catch-all in `main()`, so one workflow's shape never stops the next.

Scrutinise hardest:
- **One level further out** (the centre of this round): the three leads above, and anything else outside the five jobs'
  keys that runs code in, beside or before a job holding `id-token: write`, or changes the artifact it uploads.
  EXECUTE each candidate as far as this host allows (the artifact store can be stood in for; say what is a stand-in).
- **The key sets**: is each set exactly the template's? Can a key reach GitHub under a name the set does not see (an
  alias, a tag, a case variant, a key GitHub folds)? Is `timeout-minutes` harmless on every job where it is admitted? Is
  `defaults` on a sub-package's build job held tightly enough? Does an admitted value (the environment's `url`, a
  `needs` list, a `runs-on` string with an expression) open anything?
- **setup-python**: can a `python-version` of the admitted form make setup-python fetch or run anything other than an
  official interpreter? Is matching the action by name enough (a fork of setup-python, a sub-path action)?
- **The typing**: compare the live loader with GitHub's typing beyond `typing_diff.py`'s corpus (keys, flow
  collections, aliases, explicit tags with handles, `%TAG` directives, multi-line plain scalars, very long numbers).
  GitHub's server-side parser is not available; if you can, also run GitHub's TypeScript workflow parser
  (`@actions/workflow-parser` on npm) in a venv-like directory under `$W/tmp/r10review/`, and say which lineage you ran.
- **The shapes**: can a workflow make the checker crash before `main()`'s catch-all, or make the catch-all hide a PASS?
- **Every message and docstring claim**: true wherever given.

A rule that admits a bypass is a MAJOR (a BLOCKER where it reaches a job holding `id-token: write`). A rule that refuses
one of the 15 port simulations, or one of cascor's three publishers, is a MAJOR too (over-strict against a real port).
A pin that differs from its stated source is a MAJOR.

**Expected, by design:**
- `checker_proof_r9.py`: 396 of 396 (fix pass 6's 306, fix pass 7's 40 NEW8, 46 NEW9, 4 command-line). Three earlier
  verdicts changed, each stated on its row: PYa (PYTHONUNBUFFERED in the build job's own env) PASS -> FAIL; R46f
  (`defaults: {run: {working-directory: .}}` on a root package's build job) PASS -> FAIL; CH8b (`run: |+` ending in two
  newlines) PASS -> FAIL. Fix pass 7's re-baselining is unchanged (43 / 192 / 5);
- every earlier mutant set and corpus keeps fix pass 7's recorded verdicts (`judge_all_r9.py`: 0 moved);
- round 9's cases: its 13 bypasses FAIL, M9-8 to M9-10 and P9-2 FAIL, P9-1 FAILS cleanly, M9-11c and M9-12 PASS, the
  O9 cases keep round 9's verdicts (O9-7 and O9-8 FAIL, with a true message now);
- X8-1 to X8-8 FAIL the live checker and PASS `checker-r8/checker_r8_naive.py`;
- N9-1 to N9-9 FAIL the live checker and PASS fix pass 7's; N9-9 is not executable here;
- port-sim's own run lists 6 FAIL among its 25 variants, as before; only the 15-row table counts;
- `typing_diff.py`: 6 cases the checker alone refuses (`0x`/`0o` above 0x7FFFFFFF, which GitHub reads as negative);
- `rederive_pins_r9.py` prints "ends with newline: False" for a file that ends in one: its f-string tests `b'\\n'` (a
  driver bug inherited from round 9's copy; `od` shows the final newline);
- round 2's 43 cases: 29 as round 2 expected, C1 PASS -> FAIL by design, 13 FAIL kept; the driver says "29 of 43" and
  exits 1 for that reason;
- flake8 `--isolated` at 512 columns reports 3 E203 (Black's slice spacing); pre-commit's own hooks pass.

Do these, in order:

1. **The delta.** Read every hunk of both interdiffs: the key sets and their messages, `setup_python_problems`,
   `GITHUB_SCALARS` with `github_int` and `github_float`, `UniqueKeyLoader` (`compose_node`, `construct_github`, the
   merge-key rule by text), `load_text`, `file_problems`' message, `load_pins`' ASCII rule, `pin_mismatch`'s file,
   `check_pinned_steps`' newline rule, `shape_problems`, the environment rule, the catch-all and the label in `main()`,
   and the docstring. Hunt new bugs: does a change alter behaviour beyond its purpose; is a new rule wrong, over-strict
   or bypassable; is every docstring claim and message true?
2. **The pins file.** Re-derive each of the 18 pins from its source with code of your own and compare; check that only
   `about` changed and that every statement in it is true.
3. **One level further out** (the centre of this round): every item under "Scrutinise hardest", the leads first.
4. **Re-run the proofs.** Copy `rerun_all_r9.bash` and the drivers it calls under `$W/tmp/r10review/` (point their
   outputs there; a copy of the reviewed checker needs `--pins`) and run them; compare every count with the Fix pass 8
   section's. Regenerate the 15 simulations with round 2's probes and run the 15-row table in your own copy: all 15
   must PASS, and cascor's three from the landing tree and from `main`. Re-run round 9's fuzz and `typing_diff.py` from
   your copies.
5. **Bypass mutants (EXECUTED).** Build at least 8 NEW mutants of a passing port aimed at fix pass 8's design and at
   the level outside it. EXECUTE each so it is shown to change the outcome, not just to pass the checker (stand-ins
   under `bash -e`, as `new_mutants_r9.py` does; a real pip in a venv built under `$W/tmp/r10review/` where pip's
   behaviour is the point). Each must FAIL the checker; any that passes and changes the outcome is a finding; one that
   passes and changes nothing is not a bypass (say so).
6. **Over-strictness.** Try harmless edits a real port might make: `timeout-minutes` on any chain job, the environment
   mapping, quoting and key order of the jobs' keys, `runs-on: 'ubuntu-latest'` quoted, `python-version` written
   `'3.12'`, a tag `!!str` on a value, an extra job after the PyPI job. Report each refused, and whether its reason is
   true. An install-script edit that fails on its pin is by design.

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs and some command lines that
name `.github` paths: write small script files under `$W/tmp/r10review/` (with the Write tool if a heredoc is refused)
and run those. A `cd` in one Bash call persists into the next: return to `$W` afterwards.

**Report** (your last message, and `$W/tmp/r10review/ROUND10_REPORT.md`), with "What this round did NOT do" first if any
step was not done, then the findings, most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), what each lead came to, the re-run
counts against the Fix pass 8 section's, the 15-simulation table, and the checks you found sound. Mirror your probe
outputs into `$W/tmp/r10review/`.
