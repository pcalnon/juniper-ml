# Round-8 review brief: fix pass 6 on the cross-repo port checker (`checker-r7`)

Written 2026-11-24 (03:12Z) by fix pass 6's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**What this work is.** The checker under review is our own CI tooling: it decides whether a repository's ported
publish workflow matches juniper-cascor's reviewed template, and it refuses edits that would weaken that workflow's
safety checks (a hidden install, a swallowed failure, a step that runs other code). The "mutants" in this brief are
negative test cases for that gate: deliberately weakened copies of our own workflows, run only on this host with
logging stand-ins for `pip`, `python`, `sleep` and `twine`, to prove the gate refuses them. This is defensive testing
of a gate we own; nothing is published, pushed or sent anywhere.

**Stopping rule.**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 7), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a COMPLETE round reports no BLOCKER and no MAJOR. Round 7 was not
  complete (its report, `$W/tmp/r7review/ROUND7_REPORT.md`, says which steps it did not do), so it cleared nothing.
- The orchestrator's ruling after round 7: if this round's executed-mutant step is interrupted again, the orchestrator
  stops and asks the owner whether the static rounds suffice. So an interrupted step must be reported as interrupted.

## The prompt

Round-8 adversarial review of a FIX PASS (the sixth) on the cross-repo checker that gates the ports of juniper-cascor's
publish template into seven other repos, AND completion of what round 7 could not do. Review the checker's interdiff,
plus anything it could have broken, and then run the bypass hunt round 7 left undone. Treat the fix pass as the least
trustworthy part: rounds 4 to 7 each found the previous pass's new code the weakest. Out of scope: juniper-cascor's
tree, the writer (`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`), `$W/tmp/sweep/land/` (never touch it),
every workflow and every port, and the ports' own items (R5-F5, R4-1, R4-5).

**Write your full report to `$W/tmp/r8review/ROUND8_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it. **If any step or sub-step below is interrupted or not done, for any
reason (a safety interruption, a time or context limit, a tool failure), say so in a first section titled "What this
round did NOT do", listing exactly which steps and sub-steps were not done and why, and do not present the round as
complete.** Write that section as soon as an interruption happens, before anything else.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r8review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2` (1753 lines); a frozen copy is
  `$W/tmp/sweep/checker-r7/checker_r7_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- As round 7 reviewed it: `$W/tmp/sweep/checker-r7/checker_r6_as_reviewed.py`, sha256
  `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85`.
- The interdiff: `$W/tmp/sweep/checker-r7/checker_r6_to_r7.diff` (120 lines, +54/-7), sha256
  `4b680c760b634293e2ae3911f142774044f4b532b33b569e52273d1aa8f9bdd5`. If it does not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor `main` is now `a68dd84e` (#778, a
  docs change) and holds the same three files byte for byte: fix pass 6 fetched them read-only at 03:01Z into
  `$W/tmp/sweep/checker-r7/cascor-main-fetch/` (`evidence/fetch_cascor_main.log`). Re-fetch with read-only GETs if you
  doubt it.
- The 15 port simulations: `$W/tmp/sweep/checker-r7/port-sim/` (byte-identical to fix pass 5's `checker-r6/port-sim/`;
  the table's rows are in `$W/tmp/sweep/checker-r7/port_sim_table_r7.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256` (sha256 `924328b11fb8d15eab8563015dcd6f08c1b2fdd146d409290dc89bb00f18e5e7`;
  run `sha256sum -c` on it from `$W`). Round 7's is kept as `sweep_scripts.r7.sha256`; only the checker's line differs.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`).

**Also open to you:** fix pass 6's tools and evidence in `$W/tmp/sweep/checker-r7/`: `rerun_all.bash` (every re-run,
in order, 6 minutes), `lint_checker.bash`, `checker_proof_r7.py`, `two_readers_probe_r7.py` (R7-1's executed probe),
`two_readers_inventory_r7.py`, `new_mutants_r7.py` (this pass's executed mutants) with `make_minus_r71.py` (a checker
mutant with R7-1's comparison switched off), `judge_mutants_r7.py`, copies of every earlier executor
(`new_mutants_r5_copy.py`, `r6_mutants_rerun.py`, `new_mutants_r6_copy.py`), `run_overstrict.bash`, and `evidence/`.
Fix pass 5's tools are in `$W/tmp/sweep/checker-r6/`, round 7's in `$W/tmp/r7review/`. Re-run rather than trust them.
Run any Python that reads a cloned tree with `python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: the "Round-7 review" table (R7-1, a
MINOR rated on static evidence; R7-2 to R7-5, NITs) and the "Fix pass 6" section (what was applied, the executed
answer to R7-1, a finding beyond the review, the counts, the residual risk). In short:
- R7-1: the allow-list admits `pip` by name and leaves its arguments to the pip rules F2-F4, which judge the pip
  commands `pip_calls` finds with `shlex`, while bash runs those `lex` finds. A new `lex_pip_calls` reads them with
  `lex`, and `check_install_job` refuses any install command on which the two differ. Fix pass 6 executed the gap:
  three variants of fix pass 5's `S1` passed the checker round 7 reviewed and ran a hidden PyPI `--force-reinstall` of
  the package under test before the import check, exit 0 (so R7-1 was a MAJOR there). Fix pass 5's `S1` itself runs
  nothing hidden (its `grep` fails first).
- R7-4: `check_loop` compares the fetch's line with redirections set aside (`pieces(shell_words(...)) == [([],
  fetch_words)]`), so `> "${RUNNER_TEMP}/fetch.log"` on the fetch is admitted; the allow-list still judges each target.
  Found beyond the review (N7-3): this relaxation ALONE would admit `"pkg==${VERSION}" 0 > log`, where `pieces()` takes
  the `0` for a file descriptor and bash passes it to pip as a second TestPyPI requirement. R7-1's rule is what refuses
  it (the R7-1-off checker mutant passes it).
- R7-2, R7-3: messages only (no verdict moves); R7-5: one docstring sentence.

Scrutinise hardest:
- R7-1's rule itself: is `lex_pip_calls` exactly `pip_calls`'s rule with a different reader? (`pieces` strips leading
  RESERVED words even when quoted and pops ANY digit word before a redirection; `structure` strips RESERVED_WORDS only
  unquoted and not after `for`/`case`/`select`, and takes a descriptor only when it abuts the operator.) Does each such
  difference only refuse? Is the `ValueError` fallback (a command `lex` cannot read counts as agreeing) safe, i.e. does
  the allow-list always refuse such a command? Can a pip command escape both readers while bash runs it?
- R7-4's relaxation: every redirection on the fetch's line is now admitted by `check_loop` once `pieces()` sets it
  aside. Find one whose target passes the allow-list (`REDIRECT_TARGET`, `>&1`/`>&2`) and that changes what the fetch
  fetches, where pip writes into the import's path, what the loop's `if`/`&&` test sees, or what a later command reads
  (descriptors other than 1 and 2, `&>`, `>|`, a `.txt` file a later command could read). Look for other places where
  `pieces()`'s descriptor rule diverges from bash's.
- The messages of R7-2 and R7-3: true in every case each is given (lines holding a CR, a no-break space or other
  characters `str.strip()` treats as blank; comment lines after abutting, escaped and spaced joins; the window).
- The remaining `shlex` readers the docstring names: `check_loop`'s comparisons, the import check
  (`shell_words(step_cmds[-1])`), `own_line`, `check_constructs`' deny rules and their fetch-line exemptions, and the
  `pip --version` exemption. The docstring claims each only adds refusals to the allow-list's reading of the same
  command. Find an executed counterexample, or say none was found and how hard you looked.
- The docstring: every claim, above all the fix pass 6 bullet and "What this cannot see".

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
  them changes nothing); N6-6 and N6-10 FAIL both checkers (regression guards); round 6's OS11 (a trailing comment) and
  round 7's H19 (`>&2` on the lag error) FAIL;
- fix pass 6's controls C7-1 and C7-2 and round 7's H8 FAIL the checker round 7 reviewed and PASS the live one (R7-4);
  N7-3 FAILS both, and PASSES `checker-r7/checker_r7_minus_r71.py`; fix pass 5's `S2` FAILS both (the raw pip count);
- `checker_proof_r7.py` run against the reviewed checker shows 12 mismatches (T7a, T7b, T7c, T7f, L7a, L7b, L7c, B7a,
  B7b, B7c, E7a, E7b): the new cases that need fix pass 6;
- flake8 `--isolated` reports 14 E203 (Black's slice spacing; 12 in the reviewed copy); pre-commit's own flake8 passes.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff. Hunt new bugs:
   - does any change alter behaviour beyond its finding?
   - is any added rule wrong, over-strict (it rejects a legitimate port) or bypassable?
   - is every docstring claim and message true?
2. **Bash semantics, and the readers.** Round 7 did not do this part; do it in full. Probe under `bash -e` (the runner's
   default shell), as `$W/tmp/sweep/checker-r6/bash_semantics_probe_r6.py` does, every place where `commands()`, `lex`
   and `structure`, or `shlex` (`shell_words`, `pieces`) read a script otherwise than bash:
   - line joining in every context (unquoted, double and single quotes, `$(...)` bodies, `${...}`, after an escaped
     backslash, a blank or a tab, at a script's end with and without a newline, beside a comment, a CRLF);
   - NUL, the other control and format characters, and the spaces Python strips but bash does not;
   - comments (a whole-line comment and a trailing one, each ending in a backslash; `#` after a join);
   - quoting `lex` may model differently from bash: `$'...'`, `$"..."`, nested `"$( "..." )"`, backslashes inside
     double quotes, `${...}` holding quotes or `}`, here-documents and here-strings, `#` inside words;
   - redirections: file descriptors written against an operator or apart from it, `>&`, `&>`, `>|`, `<>`.

   Report the bash version: GitHub's `ubuntu-latest` runs 5.2, and this host 5.3.
3. **Re-run the proofs.** Run `rerun_all.bash` and `lint_checker.bash` (copy them under `$W/tmp/r8review/` and point
   their outputs there), and compare their counts with the Fix pass 6 section's. Re-check all 15 port simulations:
   regenerate them with round 2's probes and run the 15-row table (`run_port_sim.bash`, in your own copy). All 15 must
   PASS.
4. **Bypass mutants (EXECUTED; round 7 built none).**
   - Build at least 8 NEW mutants of a passing port, aimed at the reader divergences step 2 finds, at R7-1's rule (a
     pip command both readers miss, or read alike while bash runs another), at R7-4's relaxation (a redirection on the
     fetch's line), at the remaining `shlex` readers, and at the messages.
   - EXECUTE each mutant so it is shown to change the outcome, not just to pass the checker:
     - the install script under `bash -e`, with stand-in `pip`, `python` and `sleep` that log, as
       `checker-r7/new_mutants_r5_copy.py` and `checker-r7/new_mutants_r7.py` do;
     - a real `python3` where the import's outcome is the point;
     - the build window as `new_mutants_r7.py`'s `run_window` does (its twine stand-in fails on a missing file, as real
       twine 6.2.0 does).
   - Each mutant must FAIL the checker. Any that passes and changes the outcome is a finding; a mutant that passes but
     changes nothing is not a bypass (say so).
   - Independently re-check fix pass 6's executed answer to R7-1 (`two_readers_probe_r7.py`): do `S1p`, `S1g` and
     `S1g-cn` pass the checker round 7 reviewed and run a hidden install? Do they fail the live one?
   - Re-EXECUTE every earlier mutant set, not by verdict alone (round 7 judged them by verdict only): round 6's R6-1 to
     R6-6, fix pass 5's N6-1 to N6-13, fix pass 4's N5-1 to N5-16 and fix pass 6's N7-1 to N7-9 with the drivers in
     `checker-r7/` (copy them under `$W/tmp/r8review/` and move each `--out` guard there); round 4's M1 to M15 and fix
     pass 3's N1 to N14 with their own drivers (`run_mutants.bash`); and round 5's R5-1 to R5-18 with round 5's own
     drivers (`$W/tmp/r5review/s4_new_mutants*.py`, copied). All must FAIL but N6-1 and N6-12; their controls PASS.
     Round 2's seven are judged by verdict against round 2's template.
5. **Over-strictness.** Try harmless edits of passing ports that a real port might make, beyond round 7's 32 (in
   `$W/tmp/r7review/overstrict/`): a log redirection on the fetch in both loop forms, `2>&1` on a later install, a
   comment line, echo text, a continuation with a tab, a long command split over lines, an extra `[ -f ]`, a renamed
   lowercase variable, `set -eu`, `python3`. Report each one refused, and whether the reason the checker gives is true.

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs and some command lines that
name `.github` paths: write small script files under `$W/tmp/r8review/` (with the Write tool if a heredoc is refused)
and run those. A `cd` in one Bash call persists into the next: return to `$W` afterwards.

**Report** (your last message, and `$W/tmp/r8review/ROUND8_REPORT.md`), with "What this round did NOT do" first if any
step was not done, then the findings, most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), the re-executed earlier sets, the
15-simulation table, and the checks you found sound. Mirror your probe outputs into `$W/tmp/r8review/`.
