# Round-6 review brief: fix pass 4 on the cross-repo port checker (`checker-r5`)

Written 2026-11-24 (~00:40Z) by fix pass 4's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Stopping rule.**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 5), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a round reports no BLOCKER and no MAJOR.

## The prompt

Round-6 adversarial review of a FIX PASS (the fourth) on the cross-repo checker that gates the ports of juniper-cascor's
publish template into seven other repos. Review ONLY the checker's interdiff, plus anything it could have broken. Treat
the fix pass as the least trustworthy part. Out of scope: juniper-cascor's tree, the writer
(`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`), the cascor PR being landed from `$W/tmp/sweep/land/`
(never touch that directory), and the ports' own items (R5-F5, R4-1, R4-5).

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r6review/`;
never write under `/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8` (1623 lines); a frozen copy is
  `$W/tmp/sweep/checker-r5/checker_r5_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- As round 5 reviewed it: `$W/tmp/sweep/cascor-r4/checker_r4_as_reviewed.py`, sha256
  `c826ab875ecb5d6ad95891e341fb3b27020cfddf25d0161a4a44e04c74f88236`.
- The interdiff: `$W/tmp/sweep/checker-r5/checker_r4_to_r5.diff` (785 lines, +591/-46), sha256
  `bc14fa9fd71cad836042ff5d4b2055b38f0e11ed46cfff549387571df9e54489`. If it does not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`).
- The 15 port simulations: `$W/tmp/sweep/checker-r5/port-sim/` (byte-identical to fix pass 3's `cascor-r4/port-sim/`;
  the table's rows are in `$W/tmp/sweep/checker-r5/port_sim_table_r5.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256` (sha256 `81e28cbb4351df76587cda828aa9e82c7cd9bf24e4245f9fe3160e33bee7db11`;
  run `sha256sum -c` on it from `$W`). Round 5's is kept as `sweep_scripts.r5nit.sha256`; only the checker's line
  differs.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`).

**Also open to you:** fix pass 4's tools and evidence in `$W/tmp/sweep/checker-r5/` (`rerun_all.bash`,
`run_proof43.bash`, `lint_checker.bash`, `checker_proof_r5.py`, `new_mutants_r5.py`, `judge_mutants_r5.py`,
`inventory_ports.py`, `bash_semantics_probe_r5*.bash`, the drafts `checker_r5_draft1.py` and
`checker_r5_draft2_reconstructed.py`, and `evidence/`). Re-run rather than trust them.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: the "Round-5 review" table (R5-F1, R5-F2,
R5-F3, R5-F4 and R5-F7; R5-F5, R5-F6 and R5-F8 are out of scope) and the "Fix pass 4" section (the approach, what was
applied, every rule added beyond the review, what was relaxed and narrowed, the counts, the residual risk). The fix
pass replaced further deny rules with a positive allow-list over a new bash lexer. Scrutinise hardest:
- the lexer (`lex`, `_dollar`, `_double`, `_brace_end`, `structure`, `line_problems`, `unquoted_texts`): every place
  its reading of a script can differ from bash's, since a divergence is a bypass;
- every allow-list entry and shape (`TOP_COMMANDS`, `SUBST_COMMANDS`, `CONSOLE_SCRIPTS`, `ADMITTED_RESERVED`,
  `command_shape`, `SIMPLE_REFERENCE`, `PREFIX_REMOVAL`, `REDIRECT_TARGET`, `ASSIGNABLE`, `SPARSE_PATH`), the build job
  env allow-list and the env-key rules;
- the two relaxations (`own_line`, R5-F7's O1; `test_only`, O2) and the narrowed `plain_echo` (R5-F1).

An allow-list entry or relaxation that admits a bypass is a MAJOR. A rule that refuses one of the 15 faithful port
simulations is a MAJOR too (over-strict against a real port).

**Expected, by design:**
- port-sim's own run (round 2's probes) lists 6 FAIL among its 25 variants: juniper-ml's `publish.yml` before its F2
  edits (two variants) and config-tools' and doc-tools' `faithful` variants (two each). Only the 15-row table counts;
- round 4's mutant files as written (`$W/tmp/r4review/mutants/`): `ML0` FAILS on juniper-ml's old lag error, which those
  files predate; regenerated by round 4's driver, `ML0` passes;
- round 2's seven mutants (`$W/tmp/r2review/neg/`) are judged against round 2's own template,
  `$W/tmp/sweep/cascor-r2/work-main/.github/workflows/publish.yml`;
- in `new_mutants_r5.py`, `CN0r` (N5-6's execution baseline, a widened checkout) FAILS the checker;
- Black at 512 columns would re-quote two f-strings in `check_fetch` that the reviewed copy holds too.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff. Hunt new bugs:
   - does any change alter behaviour beyond its finding?
   - is any added rule wrong, over-strict (it rejects a legitimate port) or bypassable?
   - is every docstring claim true, the "What this cannot see" paragraph and each "closes" claim above all?
2. **Bash semantics.** Probe, under `bash -e`, the constructs the allow-list admits and the places the lexer could
   misread bash, as round 5's `$W/tmp/r5review/bash_semantics_probe.bash` did. Cover:
   - quoting inside `$(...)`, nested `${...}` and `$(...)`, comments and `#`, line continuations;
   - here-documents, `$'...'` and `$"..."`;
   - `[ ]` with each admitted operator: does any evaluate arithmetic or a subscript?
   - the redirection forms (`2>&1`, `>&2`, `&>`, `>|`), `set -o` long names, and the options of `sed`, `grep` and
     `head`.

   Report the bash version: GitHub's `ubuntu-latest` runs 5.2, and this host 5.3.
3. **Re-run the proofs.** Run `rerun_all.bash`, `run_proof43.bash` and `lint_checker.bash`, and compare their counts with
   the Fix pass 4 section's. Re-check all 15 port simulations: regenerate them with round 2's probes and run the 15-row
   table (`run_port_sim.bash`, or your own copy of it under `$W/tmp/r6review/`). All 15 must PASS.
4. **Bypass mutants.**
   - Build at least 8 NEW mutants of a passing port, aimed at fix pass 4's changes:
     - the lexer's edges (quoting, `$(...)` bodies, nested forms, comments, continuations, line breaks);
     - each allow-list entry's shape;
     - the assignable names and the redirection targets;
     - the checkout, build-runner and env-key rules;
     - the relaxations.
   - EXECUTE each mutant so it is shown to change the outcome, not just to pass the checker:
     - the install script under `bash -e`, with stand-in `pip`, `python` and `sleep` that log, as
       `$W/tmp/r5review/s4_new_mutants.py` and `$W/tmp/sweep/checker-r5/new_mutants_r5.py` do;
     - a real `python3` where the import's outcome is the point;
     - the build window as `run_window` there does.
   - Each mutant must FAIL the checker. Any that passes and changes the outcome is a finding; a mutant that passes but
     changes nothing is not a bypass.
   - Also re-judge every earlier mutant: round 5's R5-1 to R5-18, round 4's M1 to M15, round 2's seven, fix pass 3's
     N1 to N14 and fix pass 4's N5-1 to N5-16. All must FAIL; their controls PASS.
5. **Over-strictness.** Try harmless edits of passing ports that a real port might make: a comment, echo text, an extra
   `[ -f ]`, a log redirection, a renamed lowercase variable, `set -eu`, `python3`. Report each one refused, and whether
   the reason the checker gives is true.

**Rules.** Use read-only `gh` GETs only. Never comment on, edit, approve, merge or push anything. Put no secrets,
tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one.

**Report** (your last message), most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), the 15-simulation table, and the
checks you found sound. Mirror the report and your probe outputs into `$W/tmp/r6review/`.
