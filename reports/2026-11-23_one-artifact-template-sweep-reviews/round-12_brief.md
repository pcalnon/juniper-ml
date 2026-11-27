# Round-12 review brief: fix pass 10 on the cross-repo port checker (`checker-r11`): what it prints, aliases, the build job's upload and file commands, concurrency

Written 2026-11-25T01:14:10Z (from `date -u`) by fix pass 10's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**What this work is.** The checker under review is our own CI tooling: it decides whether a repository's ported
publish workflow matches juniper-cascor's reviewed template, and it refuses edits that would weaken that workflow's
safety checks (a hidden install, a swallowed failure, a step that runs other code, a job that runs somewhere else, an
upload aimed elsewhere, and since fix pass 10 a result displayed other than it is). The "mutants" in this brief are
negative test cases for that gate: deliberately weakened copies of our own workflows, run only on this host with
stand-ins (a stand-in artifact store, stand-in indexes, a stand-in OIDC token service and index on 127.0.0.1, logging
stand-ins for `pip`, `twine`, `python` and `sleep`), and rendered in a local terminal emulator (tmux), to prove the gate
refuses them and reports them truly. This is defensive testing of a gate we own; nothing is published, pushed or sent
anywhere.

**Stopping rule (unchanged).**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 11), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a COMPLETE round reports no BLOCKER and no MAJOR. A round with an undone
  step clears nothing, so an interrupted step must be reported as interrupted.

## The prompt

Round-12 adversarial review of FIX PASS 10 on the cross-repo checker that gates the ports of juniper-cascor's publish
template into seven other repos. Round 11 found fix pass 9's rules sound and one MAJOR one level further out, in what
the checker PRINTS: loaded strings were interpolated raw into messages, so a step name loaded through a double-quoted
escape (`"\x1b[2J..."`, `"...\nPASS ..."`) made a refused port DISPLAY as `PASS ... 1 of 1 pass` in a terminal, could
conceal the next workflow's FAIL, and could inject whole lines into captured output (M11-A; the exit status stayed 1).
It also found four MINORs: an alias bomb that held the run for hours (M11-B); the build job's steps before the build
reaching the window and the artifact through `$GITHUB_ENV` and an early `upload-artifact` (M11-C); a workflow
concurrency group another workflow can name and cancel (M11-D); and a docstring claim about the publish action's code
(M11-E, its container image named by a re-pushable tag). Fix pass 10 refuses at load every character but printable
text, a tab and a newline in any loaded string, and a newline in a key or in a workflow, job or step name; prints every
workflow-derived value through `shown()` (a plain token as it stands, anything else as its repr) and every output line
through `visible()`; refuses anchors and aliases at load, bounds a workflow file at 256 KiB and makes the duplicate-key
check linear; admits `upload-artifact` in the build job only as its `Upload dist artifacts` step and refuses a build
step that names the runner's env or path file; holds the workflow's concurrency to `<file stem>-${{ github.ref_name }}`
with `cancel-in-progress: false`; and corrects five messages and three docstring passages. After its second full run
it also made five paths linear that grew as the square of a file, each giving what it gave (a key's text copied into
the place of every node beneath it, a job's id into a scope or a message for each of its steps, the `${{ }}`
substitution before `bash -n`, the window's check of a continuation into a blank line, and keys that are lists), and
it cuts a value or a place a message holds at `SHOWN_CHARS` (200) characters. Review the r10 -> r11 interdiff (the
checker; the pins file is unchanged) once, then hunt for bypasses. Treat fix pass 10's new code as the
least trustworthy part: rounds 4 to 11 each found the previous pass's new code, or the level just outside it, the
weakest. Out of scope: juniper-cascor's tree, the writer (`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`),
`$W/tmp/sweep/land/` (never touch it), every workflow and every port, the ports' own items (R4-1, R4-5, R5-F5: each
port's review makes its own pin update), the template's own residual SWEEP item 28 (no publish job ties SHA256SUMS'
version to the release tag), and the residuals fix pass 10 records for plan v1.15.18 (below): judge whether each is
stated truly, not whether the template should change.

**Ask this first: can any finding class from rounds 4 to 11 still be reached in a new form?** Each round's MAJOR or
worse was a class the previous fix closed in the form it was found and left open in another. Go through each class and
try to reach it again through fix pass 10's code, or around it, and say for each whether you could:
- rounds 4 to 8: the checker's reading of a shell script differed from bash's (R4-2, R5-F1, R6-F1, R7-1, R8-1 to R8-3;
  install scripts are now pinned exactly, the build window keeps its own reader);
- round 9: a part of a job the checker did not read (its keys, setup-python's inputs, YAML 1.1 typing; B9-1, M9-A to
  M9-C);
- round 10: inputs, jobs and refs read through too narrow a view (B10-1 to B10-3);
- round 11: what is printed (M11-A), a workflow that holds up the run (M11-B, and the five paths that grew as the square
  of the file which fix pass 10 then found in its own and earlier code), the steps before the build (M11-C), a group
  shared with another workflow (M11-D), and a claim about an action's code (M11-E).

**Starting points one level further out, none verified:**
- `shown()` prints a string of `[A-Za-z0-9._/@+-]` as it stands and everything else as its repr; `visible()` escapes
  every character `str.isprintable()` rejects (Python 3.14.7's Unicode tables). What a terminal does with PRINTABLE text
  is outside both: combining marks, wide and ambiguous-width characters, right-to-left letters (a bidi-aware terminal),
  look-alikes, and a long line's soft wrap (documented as a residual). Can any of them make a displayed verdict
  disagree with the exit status, or make a FAIL line or the last summary line read otherwise?
- `ENV_FILE_NAMES` is a text check (`github_env`, `github_path`, `github.env`, `github.path`, `_runner_file_commands`,
  any case) over a build step's `run` and `env`. Fix pass 10's own R11-1 (an indirect name, `${!f}`) passes it, by
  design and documented; what else reaches the same outcome (an action of the build job that writes the env file, a
  `shell:` that is not bash, `GITHUB_STATE`, `GITHUB_OUTPUT` of a step the window reads, a background process)?
- `MAX_WORKFLOW_BYTES` (256 KiB) bounds the work. After its second full run fix pass 10 found five paths that grew as
  the square of the file and made each linear (`evidence/cost_probe_square_fp10.before.out` and `.after.out`;
  `equivalence_fp10.out` compares old and new input by input); the slowest file it then measured is `bash -n`'s, the
  most run steps the bound holds (42,762 single-pair `run:` mappings in a flow list: about 140 s). Is there another
  path whose time or memory grows faster than the file (a regular expression that backtracks, a rule that scans the
  document per step, a message or a list that repeats a long value for each child, PyYAML's own scanner), or a file
  outside the workflow that is read unbounded (the called `notify-consumers.yml`, the pins file)?
- `shown()` and `place()` now cut a value or a place at `SHOWN_CHARS` characters (then `... (N more characters)`, or
  `...`). Can a cut make a message false, hide what makes a value refused, or make two refusals read alike?
- No rule reads the workflow's top-level keys beyond those it names (`name`, `on`, `permissions`, `env`, `defaults`,
  `concurrency`, `jobs`): fix pass 10's cost case C, the template with an extra top-level key over a long list,
  PASSES both deliveries (GitHub refuses a workflow with an unknown top-level key, so it would not run; `run-name` is
  valid and displays only). Is there a key GitHub accepts, at the top level or in a job or a step, that no rule reads
  and that changes what runs?
- The concurrency rule compares with `path.stem`, the name the operator passes. Is that the name GitHub runs the
  workflow under in every way the operator can pass it (`.yaml`, a renamed copy, the named copies the drivers make)?
- `uploads()`, `checkouts()` and the install job's action check now read an action's owner and repository without
  regard to case (n11-b), while `uses_problems` and `step_list` still compare exact text: do the two readings ever
  disagree in a way that admits something?
- The refusals at load (`document_problems`, `compose_node`, `read_text`) run before the other rules, and every other
  rule still runs after them: can a refused string still reach a message raw through a rule that runs anyway?

**Write your full report to `$W/tmp/r12review/ROUND12_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it. **If any step or sub-step below is interrupted or not done, for any
reason (a safety interruption, a time or context limit, a tool failure), say so in a FIRST section titled "What this
round did NOT do", listing exactly which steps and sub-steps were not done and why, and do not present the round as
complete.** Write that section as soon as an interruption happens, before anything else.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r12review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `b807d3ca9c45f14ba3a5771c562fecb5df5f82dc905fb294b88c5622628ea92d` (1750 lines, 144784 bytes); a frozen copy is
  `$W/tmp/sweep/checker-r11/checker_r11_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference. Fix pass 10's first delivery, before the five paths were made linear, is kept as
  `checker-r11/checker_r11_as_delivered.run2.py` (`26b6a70c…`, 1680 lines; its interdiff `checker_r10_to_r11.run2.diff`):
  the "before" side of `cost_probe_square_fp10.py` and `equivalence_fp10.py`, not the file under review.
- The pins file it reads by default: `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`, sha256
  `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3` (18 pins, 552 lines), UNCHANGED by fix pass 10; a
  frozen copy is `$W/tmp/sweep/checker-r11/pins_r11_as_delivered.json`.
- As round 11 reviewed them: `$W/tmp/sweep/checker-r11/checker_r10_as_reviewed.py`, sha256
  `23707ac6de0b351291372ec7a3c07eb2f328c2200d80f831dacf4976e393ba35` (1439 lines), and
  `$W/tmp/sweep/checker-r11/pins_r10_as_reviewed.json`, sha256 `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3`.
- The interdiffs: `$W/tmp/sweep/checker-r11/checker_r10_to_r11.diff` (1106 lines, +451/-140), sha256
  `fd6fb7c08f677d6d02d56287bd27f6d2f5297a9fa017de76b56efbd38f94e1a3`, and `$W/tmp/sweep/checker-r11/pins_r10_to_r11.diff` (0 lines, empty: the pins file did not change),
  sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. If either does not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor at `f5ed3017` (#777) and at `main`
  `ea8e68b8` (#773, a CI bump) holds the same three files byte for byte: fix pass 10 re-fetched `main` read-only at
  2026-11-24T23:36:49Z into `$W/tmp/sweep/checker-r11/cascor-main-fetch/` (`evidence/fetch_main_r11.log`). Re-fetch
  with read-only GETs if you doubt it.
- juniper-data's called workflow, `notify-consumers.yml`, fetched read-only from juniper-data `main` (`607bae32`, #550)
  into `$W/tmp/sweep/checker-r11/juniper-data-main-fetch/`: sha256
  `e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078`, 11039 bytes, blob `ab0cade2`, the bytes rounds 10
  and 11 read. `EXTRA_JOBS` pins that sha256.
- The 15 port simulations, the seeds of 15 pins: `$W/tmp/sweep/checker-r7/port-sim/` (fix pass 10's regeneration,
  `$W/tmp/sweep/checker-r11/port-sim/`, equals it byte for byte, plus `notify-consumers.yml` placed beside juniper-data's
  simulation, as juniper-data's tree holds it).
- Round 11's cases and tools, read-only: `$W/tmp/r11review/` (`ROUND11_REPORT.md`, `mutants/`, `overstrict/`, `evidence/`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256`, SEVEN lines, sha256 `40f09c653bec74af59d0bb34bb5d87027c7bcfdba6f2b964ffda2ad1937dc16b`; run `sha256sum -c` on it from
  `$W`. Fix pass 9's is kept as `sweep_scripts.r11.sha256`, and the first delivery's (`dbc85acc…`) as
  `checker-r11/sweep_scripts.run2.sha256`; only the checker's line changed (the pins file's and the writer's,
  `c47940ad…`, are as before).

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`). `--pins PATH` replaces the
default pins file, which sits beside the checker; it is an operator argument, and nothing in a workflow chooses it. A
copy of the checker placed elsewhere finds no pins file beside it: pass `--pins`. The checker prints the pins file's
path and sha256 first; a pins file it refuses, and a template it refuses (since fix pass 10 also one that does not load,
an anchor among the reasons), stop the run (exit 1, nothing checked, the refusal on stderr with every character but
printable text escaped). A workflow whose job calls an allow-listed reusable workflow needs the called file beside it.
A workflow file over 262144 bytes is refused before it is parsed. A value or a place in the document that a message
names is printed cut after 200 characters (`SHOWN_CHARS`), the rest counted. Every line the checker prints begins with `pins: `,
`PASS `, `FAIL `, `    - ` (a reason), eight spaces (a reason's continuation: a pin mismatch's diff) or is the summary
`N of M pass`, the last line; read verdicts anchored at the line's start.

**Also open to you:** fix pass 10's tools and evidence in `$W/tmp/sweep/checker-r11/`: `rerun_all_r11.bash` (every
re-run, in order, about 9 minutes; `evidence/rerun_all.out`), `extras_r11.bash` (run after it:
`equivalence_fp10.py`, the old and new code input by input; `cost_probe_square_fp10.py`, the five square paths before
and after and the most run steps the bound holds; `compare_runs_r11b.py`, the second full run against the third),
`aside_run1_r11.bash` and `aside_run2_r11.bash` (the earlier full runs moved aside, `.run1` and `.run2`),
`compare_runs_r11.py` (the first against the second), `finish_r11.bash` (the frozen copies, the
interdiffs, the manifest), `untouched_r11.bash`, `lint_checker_r11.bash`, `survey_fp10.py` (each new rule over the 37
files round 11 listed, the build jobs' file commands and the pins file, run BEFORE any edit), `cost_probe_fp10.py`
(before) and `cost_probe_live_fp10.py` (after: the size bound's worst cases), `audit_interpolations_r11.py` (every
f-string field printed raw, by line), `fetch_main_r11.bash`, `adapt_r11.py`, `adapt_r11_expectations.py` and
`adapt_r11_labels.py` (how fix pass 9's drivers were copied, re-pointed and, where fix pass 10's rules required, their
expectations changed, each stated), `r11lib.py` and `checker_r11_named.py` (shared plumbing), `judge_all_r11.py`,
`judge_r9_mutants_r11.py`, `new_mutants_r8_rerun_r11.py`, `new_mutants_r9_rerun_r11.py`, `judge_r10_mutants_r11.py`,
`new_mutants_r10_rerun_r11.py`, `judge_r11_mutants.py` (round 11's cases), `new_mutants_r11.py` (this pass's negative
tests N11-1 to N11-11, its residual probe R11-1 and controls, executed with fix pass 9's stand-ins and round 11's
methods), `render_tmux_fp10.bash` and `screen_check_fp10.py` (the terminal emulator, before and after), `visible_fp10.py`
(round 11's `visible_r11.py`), `checker_proof_r11.py` (built by `make_proof_r11.py` from fix pass 9's proof and
`proof_r11_tail.py`), `run_proof43_r11.bash` and `classify_proof43_r11.py`, `rederive_pins_r11.py`, `parsers/`, `node/`,
and `evidence/`. The development runs before the final one are kept beside it (suffixes `.dev`, `.dev1`, `.dev2`,
`.pre`, and the first two full runs' `.run1` and `.run2`). Round 11's tools are in `$W/tmp/r11review/`, round 10's and GitHub's sources in `$W/tmp/r10review/external/`,
round 9's in `$W/tmp/r9review/external/`. Re-run rather than trust them. Run any Python that reads a cloned tree with
`python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: § "Round-11 review" (the findings) and
§ "Fix pass 10 (round 11's fixes; checker-r11)" (the decisions, the counts, the deviations, the leads, the residuals).
The checker's docstring, § "Fix pass 10: what is printed, aliases, the build job's upload and file commands,
concurrency", states every decision. In short:
- M11-A at load (`document_problems`, `unprintable`): a character other than printable text, a tab or a newline in any
  key or string refused, a lone surrogate keeping fix pass 9's message; a newline in a mapping key or in the workflow's,
  a job's or a step's `name` refused; every string of the pins file printable text alone (`load_pins`);
- M11-A at output: `shown()` for every workflow-derived value a message names (job ids, step labels, env keys, needs,
  permissions, environments, packages, paths), `visible()` for a YAML error's, a crash's and bash's own text and for
  every line `main()` prints, a message's further lines indented, a refused pins file or template reported through
  `visible()` on stderr;
- M11-B: an anchor or alias refused in `compose_node`; beyond the brief, `read_text` refuses a file over
  `MAX_WORKFLOW_BYTES` before it is parsed and the duplicate-key check reads sets; a template that does not load is
  refused with a message; and, after the second full run, five paths made linear: `place()` (a document place, cut at
  `SHOWN_CHARS`), `shown()`'s cut, `expression_words` (for `bash_parses`), `line_problems`' `later`, and `frozen` (list
  and mapping keys in `construct_mapping`);
- M11-C: `actions/upload-artifact` in the build job only as `Upload dist artifacts`; a build step whose `run` or `env`
  names `ENV_FILE_NAMES` refused; the docstring's account of the steps before the build corrected;
- M11-D: the workflow's `concurrency` absent or exactly `{group: <file stem>-${{ github.ref_name }}, cancel-in-progress:
  false}`, compared with its types; the R4-4 reasoning corrected;
- M11-E: the docstring says the SHA pins the publish action's composite steps and the NAME of its image, not the image;
- n11-a, n11-b, n11-e: true messages (a called file's bytes; an action in another case, and an upload so named counted
  as one; the two-refs reason); n11-d: `template()`'s local is `install_jobs`; n11-c: `needs: [pypi]` and
  `verbose: "true"` stay refused by design.

Scrutinise hardest:
- **The new classes, and old classes in new forms** (the centre of this round): the question above, then the starting
  points. EXECUTE each candidate as far as this host allows (say what is a stand-in); render a display case in a
  terminal emulator.
- **The output layer**: is every value read from a workflow, or from the pins file, printed through `shown()`, `!r` or
  `visible()` (re-run `audit_interpolations_r11.py` and judge each remaining raw field)? Can a message's own words be
  forged by a value printed bare (`shown()`'s plain class), or a line begin with workflow text?
- **The load rules**: is any loaded string not walked (a key that is not a string, a value inside a type the walk skips)?
  Is any name a message prints as one line not covered by the newline rule?
- **The size bound, the anchor rule and the five linear rewrites**: is the claim "a delay, bounded, never a stop" true,
  in time and in memory? Re-run `equivalence_fp10.py` and widen it where you doubt a rewrite.
- **The build job's two rules and the concurrency rule**: exact as stated, over-strict for any real port, or bypassable?
- **Every message and docstring claim**: true wherever given.

A rule that admits a bypass is a MAJOR (a BLOCKER where it reaches a job holding `id-token: write`). A display that
disagrees with the exit status is a MAJOR. A rule that refuses one of the 15 port simulations, or one of cascor's three
publishers, is a MAJOR too (over-strict against a real port). A pin that differs from its stated source is a MAJOR.

**Expected, by design:**
- `checker_proof_r11.py`: 479 of 479 (fix pass 6's 306, fix pass 7's 40 NEW8, fix pass 8's 46 NEW9, fix pass 9's 33
  NEW10, 41 NEW11, 13 command-line). Six earlier expectations changed, each a message only, each stated on its row:
  W6a, W6b, W6e, W6f and B7b (`build: step 'Check package' ...`: a name with a space now printed as its repr, M11-A) and
  K9h (an alias: now refused at load, M11-B); CLI7 also requires n11-e's true reason;
- every earlier mutant set and corpus keeps fix pass 9's recorded verdicts (`judge_all_r11.py`: 0 moved); round 9's
  cases 32 of 32; round 10's as fix pass 9 recorded them (O10-7, O10-8 FAIL by design, from fix pass 9);
- X8-1 to X8-8 FAIL the live checker and PASS `checker-r8/checker_r8_naive.py`; N9-1 to N9-9 FAIL and PASS fix pass 7's;
  their controls PASS; the N9 re-run's stand-in runner reads each case through fix pass 9's loader (N9-1 holds an
  anchor, which the live loader refuses: that is the checker's verdict, not how GitHub's runner reads the file);
- N10-1 to N10-16 FAIL the live checker and PASS fix pass 8's, every executed row as fix pass 9 recorded it; N10-1's
  reason is now the anchor's (M11-B);
- round 11's cases (`judge_r11_mutants.py`): M11-1 to M11-3 FAIL, printed as printable text alone with every line the
  checker's own; M11-4's bombs FAIL at once and the template after depth 9 PASSES within a second; M11-7, M11-8, M11-9,
  M11-10, M11-12 FAIL, M11-11 PASSES (not a bypass, round 11); C11-0, C11-2, C11-3 PASS; O11 as round 11 recorded;
- the terminal (`screen_check_fp10.py`): every case's display agrees with its exit status under the live checker; under
  fix pass 9's, M11-1, M11-2, N11-1 and N11-10 display PASS with cells concealed, M11-3 and N11-11 show injected rows;
- `new_mutants_r11.py`: 21 negative tests FAIL as expected, 12 of which PASSED fix pass 9's checker, 6 controls PASS, 0 unexpected; R11-1 PASSES and its execution changes the outcome: the documented residual;
- the fuzz: 0 differ for libyaml and both YamlDotNets, Node 7 (round 9's construct); more cases tried than in fix pass
  9 (3066, 6390), because the fuzz alphabet holds `&a ` and `*a` and the live loader now refuses them;
- `typing_diff.py`: 6 cases the checker alone refuses (`0x`/`0o` above 0x7FFFFFFF);
- round 2's 43 cases: 26 as round 2 expected, the rest as fix pass 9 recorded; the driver says "26 of 43" and exits 1;
- `rederive_pins_r11.py` prints "ends with newline: False" for a file that ends in one (the inherited driver bug);
- flake8 `--isolated` at 512 columns reports 2 E203 (Black's slice spacing; the third, `lines[at + 1 :]` in
  `line_problems`, went with the linear rewrite); pre-commit's own hooks pass;
- `equivalence_fp10.py`: 0 differ (its first run found an editing slip of this pass's own, a lost space in a message,
  kept as `evidence/equivalence_fp10.dev.out`, fixed before any full run);
- `cost_probe_square_fp10.py`: every case's file FAILS but case C's, and the template after it PASSES; case C's file
  (an unknown top-level key, see the starting points) PASSES both deliveries; before, the time or memory of A to E grows
  as the square of the size, after, linearly.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff: the docstring's fix pass 10 section and its corrections,
   `MAX_WORKFLOW_BYTES`, `PLAIN`, `FEW`, `SHOWN_CHARS`, `UPLOAD_ARTIFACT`, `ENV_FILE_NAMES`, `CONCURRENCY_GROUP`,
   `ALIAS_REASON`, `frozen`, `UniqueKeyLoader.compose_node` and `construct_mapping`, `read_text`, `load`, `unprintable`,
   `visible`, `shown`, `place`, `few`, `action_name`, `document_problems`, `uploads`, `checkouts`, `line_problems`,
   `lag_problems`, `load_pins`, `pin_mismatch`, `check_pinned_steps`, `expression_words`, `bash_parses`, `template()`,
   `setup_python_problems`, `runs_on_problem`, `uses_problems`, `upload_problems`, `extra_job_problems`,
   `check_install_job`, `shape_problems`, `check()` (every message, the concurrency rule, the build job's two rules) and
   `main()`. Hunt new bugs: does a change alter behaviour beyond its purpose; is a new rule wrong, over-strict or
   bypassable; does each linear rewrite give exactly what the code it replaced gave; is every docstring claim and
   message true?
2. **The pins file.** It is unchanged: confirm its sha256, and re-derive each of the 18 pins from its source with code of
   your own (or re-run `rederive_pins_r11.py` and read it). Confirm the new pins-file rule admits it.
3. **Old classes in new forms, then one level further out** (the centre of this round): the question above, every item
   under "Scrutinise hardest", the starting points.
4. **Re-run the proofs.** Copy `rerun_all_r11.bash`, `extras_r11.bash` and the drivers they call under
   `$W/tmp/r12review/` (point their outputs there; a copy of the reviewed checker needs `--pins`; place
   `notify-consumers.yml` beside juniper-data's simulation) and run them; compare every count with the Fix pass 10
   section's. Regenerate the 15 simulations with
   round 2's probes and run the 15-row table in your own copy: all 15 must PASS, and cascor's three from the landing
   tree and from `main`. Re-run round 9's fuzz and `typing_diff.py` from your copies. Render round 11's M11-1 to M11-3 in
   a terminal emulator against the live checker and say what a viewer sees.
5. **Bypass mutants (EXECUTED).** Build at least 8 NEW mutants of a passing port aimed at fix pass 10's design and at
   the level outside it. EXECUTE each so it is shown to change the outcome, or the display, not just to pass the
   checker (stand-ins, as `new_mutants_r11.py` does; a terminal emulator for a display case). Each must FAIL the checker,
   or display what its exit status says; any that passes and changes the outcome, or displays a verdict other than its
   own, is a finding; one that passes and changes nothing is not a bypass (say so).
6. **Over-strictness.** Try harmless edits a real port might make: printable non-ASCII in a step name or a comment, a
   tab in a run, quoting, key order, `timeout-minutes`, the environment mapping, a flow-style `with`, comments after a
   `uses:` SHA, the exact concurrency group in other spellings GitHub reads alike, a build step writing its own
   `$GITHUB_OUTPUT`, a workflow file near the size bound. Report each refused, and whether its reason is true. An
   install-script edit that fails on its pin is by design, and so is a port ref that is not the template's (the owner's
   ruling).

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs, some command lines that name
`.github` paths and some that name git's environment variables: write small script files under `$W/tmp/r12review/`
(with the Write tool if a heredoc is refused) and run those. A `cd` in one Bash call persists into the next: return to
`$W` afterwards. Run Python with `-B`, so no `.pyc` lands in a frozen directory. A tmux socket path must be short:
create it relative to a directory under `$W/tmp/r12review/`, as `render_tmux_fp10.bash` does. Delete nothing; move an
earlier run aside with `mv`.

**Report** (your last message, and `$W/tmp/r12review/ROUND12_REPORT.md`), with "What this round did NOT do" first if any
step was not done, then the findings, most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the answer to the old-classes question (class by class), the bypass-mutant table (id, target, checker
verdict, executed outcome or display), what each starting point came to, the re-run counts against the Fix pass 10
section's, the 15-simulation table, and the checks you found sound. Mirror your probe outputs into `$W/tmp/r12review/`.
