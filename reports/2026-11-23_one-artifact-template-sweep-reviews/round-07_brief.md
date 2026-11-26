# Round-7 review brief: fix pass 5 on the cross-repo port checker (`checker-r6`)

Written 2026-11-24 (02:07Z) by fix pass 5's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Stopping rule.**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 6), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a round reports no BLOCKER and no MAJOR.

## The prompt

Round-7 adversarial review of a FIX PASS (the fifth) on the cross-repo checker that gates the ports of juniper-cascor's
publish template into seven other repos. Review ONLY the checker's interdiff, plus anything it could have broken. Treat
the fix pass as the least trustworthy part: rounds 4, 5 and 6 each found the previous pass's new code the weakest.
Out of scope: juniper-cascor's tree, the writer (`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`),
`$W/tmp/sweep/land/` (never touch it), every workflow and every port, and the ports' own items (R5-F5, R4-1, R4-5).

**Write your full report to `$W/tmp/r7review/ROUND7_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r7review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85` (1704 lines); a frozen copy is
  `$W/tmp/sweep/checker-r6/checker_r6_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- As round 6 reviewed it: `$W/tmp/sweep/checker-r6/checker_r5_as_reviewed.py`, sha256
  `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8`.
- The interdiff: `$W/tmp/sweep/checker-r6/checker_r5_to_r6.diff` (155 lines, +86/-5), sha256
  `6f629f0492231d55be8db947bdf953d5c50ac519fbe36ba71272cfbac19ce43c`. If it does not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor `main` (`f5ed3017`, #777) holds
  the same three files byte for byte: fix pass 5 fetched them to `$W/tmp/sweep/checker-r6/cascor-main-fetch/`
  (`evidence/fetch_cascor_main.log`). Re-fetch with read-only GETs if you doubt it.
- The 15 port simulations: `$W/tmp/sweep/checker-r6/port-sim/` (byte-identical to fix pass 4's `checker-r5/port-sim/`;
  the table's rows are in `$W/tmp/sweep/checker-r6/port_sim_table_r6.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256` (sha256 `3c5cfb089087318f16c95bb50fbae27f28b31afe7d1b099e652c1d97c7195ceb`;
  run `sha256sum -c` on it from `$W`). Round 6's is kept as `sweep_scripts.r6.sha256`; only the checker's line
  differs.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`).

**Also open to you:** fix pass 5's tools and evidence in `$W/tmp/sweep/checker-r6/`: `rerun_all.bash` (every re-run,
in order), `lint_checker.bash`, `checker_proof_r6.py`, `new_mutants_r6.py` (this pass's executed mutants and the
window executor), `r6_mutants_rerun.py`, `new_mutants_r5_copy.py` (fix pass 4's executors), `judge_mutants_r6.py`,
`bash_semantics_probe_r6.py`, `inventory_continuations.py`, `twine_missing_file_probe.bash`, `shlex_probe.py`, and
`evidence/`. Re-run rather than trust them. Run any Python that reads a cloned tree with `python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: the "Round-6 review" table (R6-F1, the
BLOCKER; R6-N1 and R6-N2, NITs) and the "Fix pass 5" section (the approach, what was applied, every rule added, the
counts, the residual risk). In short: `line_problems` now also refuses a continuation whose backslash no space or tab
precedes, or whose blank there is itself escaped; a continuation on a script's last line; a NUL; and every other
character but printable text, a tab and a newline. And it now runs at the build window (every step between the build
and `Record SHA256SUMS`) as well as in the install steps. R6-N1 and R6-N2 were left refused, and documented.
`commands()`, the lexer, the allow-list and the deny rules did not change. Scrutinise hardest:
- the new `line_problems` rules: every way a line can still be joined, split or stripped differently by `commands()`
  (Python's `str.strip()`, `str.splitlines()`, the space it inserts at a join) and by bash. The fix pass's argument is
  that with an unescaped blank before the backslash each join is a run of blanks in both readings; test it in every
  quoting context, inside `$(...)` bodies and nested forms, at the end of a script and next to comments;
- the escape count (`spaced`, the backslash run before the blank) and the order of the `elif` chain;
- the character rule: does `str.isprintable()` leave any character `commands()` or the lexer reads otherwise than bash
  does?
- the window change: is every step between the build and the record now read as bash reads it, and could the change
  refuse a real port's window (juniper-ml's tag assert spans four lines with continuations; canopy has a five-command
  smoke test)?
- the docstring: is every claim true, above all the "places checked" list and "What this cannot see";
- the two readers named under "What this cannot see": the allow-list reads each command with `lex`, while the pip
  rules (F2 to F4), the loop's and the import check's comparisons and the deny rules read its words with
  `shell_words` (`shlex`), which models no `$(...)`. Fix pass 5 probed this (`evidence/shlex_probe.out`): one
  command on which `lex` and `pip_calls` disagree about a pip command passes both checkers, but executed it fails the
  step and runs nothing hidden, so no bypass was shown. Decide, with executed evidence, whether this reading can let
  the pip rules judge other arguments than bash passes, or miss a pip command bash runs.

An allow-list entry or rule that admits a bypass is a MAJOR. A rule that refuses one of the 15 faithful port
simulations is a MAJOR too (over-strict against a real port).

**Expected, by design:**
- port-sim's own run (round 2's probes) lists 6 FAIL among its 25 variants: juniper-ml's `publish.yml` before its F2
  edits (two variants) and config-tools' and doc-tools' `faithful` variants (two each). Only the 15-row table counts;
- round 4's mutant files as written (`$W/tmp/r4review/mutants/`): `ML0` FAILS on juniper-ml's old lag error, which those
  files predate; regenerated by round 4's driver, `ML0` passes;
- round 2's seven mutants (`$W/tmp/r2review/neg/`) are judged against round 2's own template,
  `$W/tmp/sweep/cascor-r2/work-main/.github/workflows/publish.yml`;
- fix pass 4's `CN0r` (N5-6's execution baseline, a widened checkout) FAILS the checker;
- fix pass 5's N6-1 and N6-12 PASS (a tab before the backslash: to bash `$` then a tab is a literal `$`, so executing
  them changes nothing); N6-6 and N6-10 FAIL both checkers (regression guards); round 6's OS11 (a trailing comment)
  FAILS (R6-N1, left refused);
- `checker_proof_r6.py` run against the reviewed checker shows 15 mismatches: they are the new cases that need fix
  pass 5;
- flake8 `--isolated` reports 12 E203 (Black's slice spacing) in both copies; pre-commit's own flake8 passes.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff. Hunt new bugs:
   - does any change alter behaviour beyond its finding?
   - is any added rule wrong, over-strict (it rejects a legitimate port) or bypassable?
   - is every docstring claim true?
2. **Bash semantics.** Probe under `bash -e` (the runner's default shell), as `bash_semantics_probe_r6.py` does:
   - line joining in every context: unquoted, double and single quotes, `$(...)` bodies, `${...}`, after an escaped
     backslash, a blank, a tab, at the end of a script, with and without a newline after it, beside a comment, and a
     CRLF;
   - NUL and the other control and format characters, and the spaces Python strips but bash does not;
   - comment handling: a whole-line comment and a trailing comment, each ending in a backslash, and `#` after a join.

   Report the bash version: GitHub's `ubuntu-latest` runs 5.2, and this host 5.3.
3. **Re-run the proofs.** Run `rerun_all.bash` and `lint_checker.bash` (copy them under `$W/tmp/r7review/` and point
   their outputs there), and compare their counts with the Fix pass 5 section's. Re-check all 15 port simulations:
   regenerate them with round 2's probes and run the 15-row table (`run_port_sim.bash`, in your own copy). All 15 must
   PASS.
4. **Bypass mutants.**
   - Build at least 8 NEW mutants of a passing port, aimed at line joining, NUL and comment handling (and at the window
     and the two readers above).
   - EXECUTE each mutant so it is shown to change the outcome, not just to pass the checker:
     - the install script under `bash -e`, with stand-in `pip`, `python` and `sleep` that log, as
       `new_mutants_r5_copy.py` and `new_mutants_r6.py` do;
     - a real `python3` where the import's outcome is the point;
     - the build window as `new_mutants_r6.py`'s `run_window` does (its twine stand-in fails on a missing file, as
       real twine 6.2.0 does).
   - Each mutant must FAIL the checker. Any that passes and changes the outcome is a finding; a mutant that passes but
     changes nothing is not a bypass (say so).
   - Also re-judge every earlier mutant: round 6's R6-1 to R6-6, fix pass 5's N6-1 to N6-13, fix pass 4's N5-1 to
     N5-16, round 5's R5-1 to R5-18, round 4's M1 to M15, round 2's seven and fix pass 3's N1 to N14. All must FAIL but
     N6-1 and N6-12; their controls PASS.
5. **Over-strictness.** Try harmless edits of passing ports that a real port might make: a comment line, echo text, a
   continuation with a tab, a long command split over lines, an extra `[ -f ]`, a log redirection, a renamed lowercase
   variable, `set -eu`, `python3`. Report each one refused, and whether the reason the checker gives is true.

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs and some command lines that
name `.github` paths: write small script files under `$W/tmp/r7review/` and run those.

**Report** (your last message, and `$W/tmp/r7review/ROUND7_REPORT.md`), most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), the 15-simulation table, and the
checks you found sound. Mirror your probe outputs into `$W/tmp/r7review/`.
