# Round-9 review brief: fix pass 7 on the cross-repo port checker (`checker-r8`): the owner's exact-pins ruling

Written 2026-11-24 (13:15Z) by fix pass 7's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**What this work is.** The checker under review is our own CI tooling: it decides whether a repository's ported
publish workflow matches juniper-cascor's reviewed template, and it refuses edits that would weaken that workflow's
safety checks (a hidden install, a swallowed failure, a step that runs other code). The "mutants" in this brief are
negative test cases for that gate: deliberately weakened copies of our own workflows, run only on this host with
logging stand-ins for `pip`, `python`, `sleep` and `twine`, to prove the gate refuses them. This is defensive testing
of a gate we own; nothing is published, pushed or sent anywhere.

**Stopping rule (unchanged).**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 8), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a COMPLETE round reports no BLOCKER and no MAJOR. A round with an undone
  step clears nothing, so an interrupted step must be reported as interrupted.

## The prompt

Round-9 adversarial review of FIX PASS 7 on the cross-repo checker that gates the ports of juniper-cascor's publish
template into seven other repos. Fix pass 7 implements the owner's ruling of 2026-11-24, "Pin exact scripts": the
checker no longer judges port install scripts with its own bash reader. Each run step of a publisher's install job must
now equal a pinned, reviewed script, held in a new pins file. Review the r7 -> r8 interdiff and the pins file once, as
the ruling asks, then hunt for bypasses of the new design. Treat fix pass 7's new code as the least trustworthy part:
rounds 4 to 8 each found the previous pass's new code the weakest. Out of scope: juniper-cascor's tree, the writer
(`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`), `$W/tmp/sweep/land/` (never touch it), every workflow
and every port, and the ports' own items (R4-1, R4-5, R5-F5: each port's review makes its own pin update).

**The class the ruling exists to close.** Rounds 4 to 8 each found a MAJOR-or-worse bypass where the checker's reading
of shell differed from bash's. Exact pins remove the checker's shell reading from install scripts, so the class now
lives one level down: anywhere the text the checker compares can differ from the text the runner executes. **Try to make
the normalization or the pin lookup diverge from what the runner executes.** That is the centre of this round.

**Write your full report to `$W/tmp/r9review/ROUND9_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it. **If any step or sub-step below is interrupted or not done, for any
reason (a safety interruption, a time or context limit, a tool failure), say so in a FIRST section titled "What this
round did NOT do", listing exactly which steps and sub-steps were not done and why, and do not present the round as
complete.** Write that section as soon as an interruption happens, before anything else.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r9review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `039e5e6d5830955c1593ccdec4b7bfdbc0bc1558c305d21fca85b47ff4bc13e0` (953 lines); a frozen copy is
  `$W/tmp/sweep/checker-r8/checker_r8_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- The pins file it reads by default: `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`, sha256
  `fde7e0ca4686ec7ed65bdfb7f5d813e7b75987b4a4e8c0f0e56d46df9efe1906` (18 pins, 552 lines); a frozen copy is
  `$W/tmp/sweep/checker-r8/pins_as_delivered.json`. Its generator: `$W/tmp/sweep/checker-r8/make_pins.py`
  (`evidence/make_pins.out`).
- As round 8 reviewed it: `$W/tmp/sweep/checker-r8/checker_r7_as_reviewed.py`, sha256
  `789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2` (1753 lines).
- The interdiff: `$W/tmp/sweep/checker-r8/checker_r7_to_r8.diff` (1765 lines, +393/-1193), sha256
  `65253032f0279b8db45aa77874c9541a22319d3742de43a6517a2e5699849953`. If it does not hash so, STOP and report. Most of it is deletion: the
  shell reader and every install-script rule.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor at `f5ed3017` (#777, the seed of
  cascor's three pins) and at `main` `b5b28dc3` (#779) holds the same three files byte for byte: fix pass 7 fetched both
  read-only at 12:32:30Z into `$W/tmp/sweep/checker-r8/cascor-f5ed3017-fetch/` and `cascor-main-fetch/`
  (`evidence/fetch_cascor_main.log`). Re-fetch with read-only GETs if you doubt it.
- The 15 port simulations, the seeds of 15 pins: `$W/tmp/sweep/checker-r7/port-sim/` (fix pass 7's regeneration,
  `$W/tmp/sweep/checker-r8/port-sim/`, equals it byte for byte; the rows are in `checker-r8/port_sim_table_r8.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256`, now SEVEN lines (the pins file joined it), sha256 `24c8e1e12f74d5e1f9f663c4b2a4cfebbdaa70ffb6b10359acdcb9a2da59efca`;
  run `sha256sum -c` on it from `$W`. Round 8's six-line one is kept as `sweep_scripts.r8.sha256`; the checker's line
  changed, the pins file's is new, and the writer's stays `c47940ad…`.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`). `--pins PATH` replaces the
default pins file, which sits beside the checker; it is an operator argument, and nothing in a workflow chooses it. The
checker prints the pins file's path and sha256 first, and a pins file it refuses stops the run (exit 1, nothing
checked).

**Also open to you:** fix pass 7's tools and evidence in `$W/tmp/sweep/checker-r8/`: `rerun_all_r8.bash` (every
re-run, in order, about 5 minutes; `evidence/rerun_all.out`), `finish_r8.bash` (the frozen copies, the interdiff, the
manifest), `untouched_r8.bash`, `lint_checker_r8.bash`, `make_pins.py`, `r8lib.py` (shared: the install-script-versus-pin
classification, the verdicts), `checker_r8_named.py` (test plumbing: places a case file under its pinned workflow name),
`judge_all_r8.py` (every earlier mutant set and over-strict corpus by verdict), `checker_proof_r8.py` (built by
`make_proof_r8.py` from fix pass 6's proof and `proof_r8_tail.py`), `new_mutants_r8.py` (this pass's executed negative
tests) with `make_naive_r8.py` (`checker_r8_naive.py`, a checker mutant with each new refusal replaced by a weaker
normalization), `run_proof43_r8.bash` with `classify_proof43_r8.py`, `yaml_divergence_probe.py`, the surveys
(`survey_install_steps.py`, `survey_window_steps.py`, `survey_scalar_styles.py`), and `evidence/`. Earlier passes' tools
are in `$W/tmp/sweep/checker-r7/` and before; round 8's in `$W/tmp/r8review/`. Re-run rather than trust them. Run any
Python that reads a cloned tree with `python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: § "The owner's ruling on the checker's
install-step judgement" and § "Fix pass 7 (the owner's exact-pins ruling; checker-r8)" (the decisions, the counts, what
was found beyond the brief, the expected pin updates, the residual risk). The checker's docstring, § "Fix pass 7: exact
pins", states every decision. In short:
- every `run` step of the job named `Verify the TestPyPI install` must equal its pin, keyed by (`--repo`, the workflow
  file's name as the operator passes its path, the step's `name`); each pin names its package, which must be the
  workflow's `PUBLISH_PACKAGE`; a run step with no pin, a pin with no step, two run steps under one name and an install
  step key GitHub does not define each fail;
- the step's `run` string as PyYAML delivers it is refused (never normalized) for a NUL, a character other than
  printable text, a tab and a newline, trailing whitespace on any line, a final backslash, or `${{`; otherwise its final
  newline(s) are removed (chomping) and the rest is compared byte for byte, comments included;
- at the YAML level: any character in the workflow file other than printable text, a tab, LF or CR LF is refused (PyYAML
  reads a raw U+0085 as a line break, a YAML 1.2 parser does not); a repeated mapping key (by its text or PyYAML's value)
  and a merge key are refused by the loader (`UniqueKeyLoader`); the file is read as bytes, with no newline translation;
  the workflow's `defaults.run.working-directory` is refused;
- the pins file is validated whole as it loads: format, fields, repositories, keys, each text's own rules, each
  sha256 against its text, and LAG_ERROR (one retry loop and the template's lag error with the loop's try count);
- removed: the shell reader (`lex`, `structure`, `shlex`) and every install-script rule that used it (round 8's R8-1 to
  R8-3 close by construction); kept: every rule that is not install-script judgement, and the build window's reader
  (`commands()` with `line_problems`, N8-1's fix applied), because the window's allow-list is the checker's own and
  round 7's layout edits W1-W8 must keep their verdicts.

Scrutinise hardest:
- **Divergence between what is compared and what runs** (the ruling's class). Find a workflow whose install step the
  checker passes as equal to its pin while the runner executes another text, or runs it otherwise:
  - YAML: PyYAML (YAML 1.1) against GitHub's parser: escapes in double-quoted scalars, line folding in multi-line
    single- and double-quoted and plain scalars (the juniper-ml simulation's install script is one such scalar), folded
    scalars, block-scalar indentation indicators and chomping, tabs, a BOM, anchors and aliases, tags (`!!str`,
    `!!binary`), document markers, complex keys, the implicit typing of keys (`on`, `yes`, `1`, `01`) and values, keys
    that differ only in case or by a look-alike character. Where you cannot run GitHub's parser, reason from the YAML
    1.1 and 1.2 specs and from a second parser you can install into a venv under `$W/tmp/r9review/` (say which), and
    say so;
  - the file-level character rule: is there a character, or a byte sequence, PyYAML accepts and reads otherwise than
    another parser that the rule does not refuse? Is reading the file as bytes and decoding it as UTF-8 the same as what
    GitHub reads?
  - the loader: does the repeated-key test (text, or PyYAML's value) catch every key two parsers could read as one, or
    one parser as two? Can a merge reach a mapping without the `<<` tag?
  - the normalization: is removing the final newline(s) after refusing a final backslash ever a change bash sees? Is any
    other character treated as a line end anywhere?
  - `${{`: can the runner substitute anything into a run text that holds no `${{`? Can a pin hold one?
  - the runner's writing and running of the script: the step's `shell`, `env`, `working-directory`, `timeout-minutes`,
    the job's `defaults`, `container`, `services` and `strategy`, the workflow's `defaults` and `env`, earlier steps'
    `GITHUB_ENV`/`GITHUB_PATH` writes (setup-python's and checkout's included), and BASH_ENV-like inputs;
  - every way a step could run a script the checker does not compare: a key other than `run`, a step that is not a
    mapping, a job that `uses:` a reusable workflow, a composite or Docker action, a second job named alike, an alias.
- **The pin lookup.** The key's three parts (can the workflow's own text choose the file name, the repository or the
  step's name, or make two steps share a pin?), the package binding, the default pins path (`Path(__file__)`), and
  `--pins`.
- **The pins file and its loader.** Can a malformed or tampered pins file be accepted? Can a pin hold a text that runs
  otherwise than it reads (the same rules a step's text meets)? Is the LAG_ERROR check right, and can it refuse a pin a
  port legitimately needs? Re-derive each of the 18 pins from its source independently and compare.
- **What was removed.** Does any removed rule guard something a pin does not cover (a step outside the install job that
  the reader used to judge; the TestPyPI job's `installs()` check; anything `check_constructs` saw)?
- **The window's reader** (kept, with N8-1's fix): the R6-F1 class there, and the message N8-1 changed.
- **The docstring and every message**: true wherever given; the mismatch message's first differing line and diff.

A rule that admits a bypass is a MAJOR. A rule that refuses one of the 15 port simulations, or one of cascor's three
publishers, is a MAJOR too (over-strict against a real port). A pin that differs from its stated source is a MAJOR.

**Expected, by design:**
- port-sim's own run (round 2's probes) lists 6 FAIL among its 25 variants, as before: juniper-ml's `publish.yml` before
  its F2 edits (two variants), and config-tools' and doc-tools' `faithful` variants (two each), whose install scripts
  are not their pins. Only the 15-row table counts;
- every earlier install-script edit that PASSED fix pass 6's checker now FAILS on its pin, by design under the ruling:
  70 cases (`checker-r8/evidence/judge_all_r8.md`, "by design under the ruling"): fix pass 5's C6-1, N6-1 and N6-12; fix
  pass 6's C7-1, C7-2 and its two-readers control A0; round 8's B8-4 and B8-12 to B8-14; round 5's O1 to O3; round 6's
  OS1 to OS10 and OS12; round 7's H1 to H18 and H20 to H24; and round 8's O8 cases but O8-11, O8-14, O8-18, O8-25 and
  O8-26, which failed before too. Edits outside install scripts keep their verdicts (round 7's H0 and W1 to W8 PASS);
- round 8's seven bypasses (B8-1 to B8-3, B8-5 to B8-8) FAIL on their pins;
- round 4's mutant files as written: `ML0` FAILS (its install script predates the template's lag error); fix pass 4's
  `CN0r` FAILS (a widened checkout); round 2's seven are judged against round 2's own template, whose install script is
  cascor's pin;
- `checker_proof_r8.py`: fix pass 6's 306 table cases re-baselined by one stated rule (a case whose install steps are
  not their pins must FAIL on a pin reason; every other case keeps fix pass 6's verdict and reason): 43 PASS -> FAIL by
  design, 197 FAIL kept on the pin, 66 unchanged; 40 new cases (NEW8) and 3 command-line cases; 349 of 349;
- round 2's 43 cases (`run_proof43_r8.bash`): 29 as round 2 expected, C1 PASS -> FAIL by design, 13 FAIL kept with
  their reason moved to the pin's; the driver's own summary says "29 of 43" and exits 1 for that reason;
- `new_mutants_r8.py`: X8-1 to X8-8 each FAIL the live checker and PASS `checker_r8_naive.py`; X8-2 (a raw NEL) and
  X8-3 (a repeated `run:` key) also PASS fix pass 6's checker (whether GitHub's parser reads either otherwise than
  PyYAML is not verified; the live checker refuses both);
- flake8 `--isolated` at 512 columns reports 3 E203 (Black's slice spacing); pre-commit's own hooks pass.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff: the new code (`UniqueKeyLoader`, `load_text`, `load`,
   `file_problems`, `script_problems`, `lag_problems`, `load_pins`, `pin_mismatch`, `check_pinned_steps`, the changes
   to `check_install_job`, `check` and `main`, the workflow `defaults.run.working-directory` rule, N8-1's line in
   `line_problems`) and what was deleted. Hunt new bugs: does a change alter behaviour beyond its purpose; is a new rule
   wrong, over-strict or bypassable; is every docstring claim and message true?
2. **The pins file.** Re-derive each of the 18 pins from its source (cascor's three at `f5ed3017`; the 15 simulations)
   with code of your own, compare text, package, step name and sha256, and check the file's format and its `about`.
3. **Divergence hunt** (the centre of this round): every item under "Divergence between what is compared and what
   runs" and "The pin lookup" above. Probe PyYAML against a second YAML parser where you can, and EXECUTE what each
   parser would hand the runner under `bash -e` with stand-ins, as `new_mutants_r8.py` does.
4. **Re-run the proofs.** Copy `rerun_all_r8.bash` and `lint_checker_r8.bash` under `$W/tmp/r9review/` (point their
   outputs there) and run them; compare every count with the Fix pass 7 section's. Regenerate the 15 simulations with
   round 2's probes and run the 15-row table in your own copy: all 15 must PASS, and cascor's three from the landing
   tree and from `main`.
5. **Bypass mutants (EXECUTED).** Build at least 8 NEW mutants of a passing port aimed at fix pass 7's design: the
   comparison and its refusals, the pin lookup and the package binding, the YAML-level rules, the pins file's loader
   (through `--pins`), the window's kept reader, and any wiring rule a pin now leans on. EXECUTE each so it is shown to
   change the outcome, not just to pass the checker (stand-in `pip`, `python` and `sleep` under `bash -e`, as
   `new_mutants_r8.py` does; a real `python3` where the import's outcome is the point; the build window as fix pass 6's
   `new_mutants_r7.py` runs it). Each must FAIL the checker; any that passes and changes the outcome is a finding; one
   that passes and changes nothing is not a bypass (say so). Re-execute `new_mutants_r8.py`'s X8-1 to X8-8 in your copy.
6. **Over-strictness.** Try harmless edits a real port might make OUTSIDE its install script (YAML quoting and
   indentation of other steps, comments in the YAML outside a block, key order, anchors, a `shell: bash` on the install
   step, a window layout edit), and the forms a port's final pin must be able to hold (a tab, an em dash, long lines,
   `|` against `|-`). Report each refused, and whether its reason is true. An install-script edit that fails on its pin
   is by design: list any you try, but do not count it as over-strict.

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs and some command lines that
name `.github` paths: write small script files under `$W/tmp/r9review/` (with the Write tool if a heredoc is refused)
and run those. A `cd` in one Bash call persists into the next: return to `$W` afterwards.

**Report** (your last message, and `$W/tmp/r9review/ROUND9_REPORT.md`), with "What this round did NOT do" first if any
step was not done, then the findings, most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), the divergence probes and what each
parser delivered, the re-run counts against the Fix pass 7 section's, the 15-simulation table, and the checks you found
sound. Mirror your probe outputs into `$W/tmp/r9review/`.
