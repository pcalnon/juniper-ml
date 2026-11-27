# Round-11 review brief: fix pass 9 on the cross-repo port checker (`checker-r10`): upload inputs, extra jobs and action SHAs

Written 2026-11-24 (22:23Z) by fix pass 9's executor (session `d935c226`'s subagent, for orchestrator `ffffd3`;
worktree `ethereal-munching-peacock`). Give this file, unedited, to ONE fresh reviewer (a `general-purpose` agent).
Paths: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**What this work is.** The checker under review is our own CI tooling: it decides whether a repository's ported
publish workflow matches juniper-cascor's reviewed template, and it refuses edits that would weaken that workflow's
safety checks (a hidden install, a swallowed failure, a step that runs other code, a job that runs somewhere else, an
upload aimed elsewhere). The "mutants" in this brief are negative test cases for that gate: deliberately weakened
copies of our own workflows, run only on this host with stand-ins (a stand-in artifact store, stand-in indexes, a
stand-in OIDC token service and index on 127.0.0.1, logging stand-ins for `pip`, `python` and `sleep`), to prove the
gate refuses them. This is defensive testing of a gate we own; nothing is published, pushed or sent anywhere.

**Stopping rule (unchanged).**
- A BLOCKER or MAJOR finding is fixed in the checker (fix pass 10), and that interdiff is reviewed again.
- MINOR and NIT findings are fixed, or recorded as deferred in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, without another
  round.
- No port is built against the checker until a COMPLETE round reports no BLOCKER and no MAJOR. A round with an undone
  step clears nothing, so an interrupted step must be reported as interrupted.

## The prompt

Round-11 adversarial review of FIX PASS 9 on the cross-repo checker that gates the ports of juniper-cascor's publish
template into seven other repos. Round 10 found fix pass 8's code sound and three BLOCKERs one level further out, each
something the checker read and did not judge, or never read: the upload steps' inputs were read through four literal
keys, while GitHub matches input names case-insensitively, evaluates expression keys and the pinned action reads its
deprecated underscore aliases (B10-1: the PyPI job's OIDC token sent to a host of the workflow's choosing); jobs
outside the chain were noted, never judged, so one could replace the build's artifact or call a reusable workflow with
`secrets: inherit` (B10-2); and every action's `@ref` was dropped (B10-3). The owner ruled on B10-3: "Pin template
SHAs". Fix pass 9 holds each upload step to the template's keys and inputs exactly, refuses every job outside the chain
but an exact allow-list (juniper-data's `notify-consumers`, its called workflow pinned by sha256), requires every
`uses:` in the chain's five jobs to equal the template's exact `owner/repo@<SHA>`, and catches every crash per
workflow. Review the r9 -> r10 interdiffs (the checker; the pins file is unchanged) once, then hunt for bypasses. Treat
fix pass 9's new code as the least trustworthy part: rounds 4 to 10 each found the previous pass's new code, or the
level just outside it, the weakest. Out of scope: juniper-cascor's tree, the writer
(`util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`), `$W/tmp/sweep/land/` (never touch it), every workflow
and every port, the ports' own items (R4-1, R4-5, R5-F5: each port's review makes its own pin update), and the
template's own residual SWEEP item 28 (no publish job ties SHA256SUMS' version to the release tag; recorded, not
changed).

**The class this round exists to close: look one level further out again.** Each round has found code that runs
beside, or before, what the checker compares, or a part of the workflow it reads without judging. **Look for anything
left in a workflow that the checker reads but does not judge, or never reads at all.** Starting points, none verified:
- the build job's steps up to and including the build are each repository's own business: its checkout's inputs
  (`token`, `repository`, `ref`, `path`, `fetch-depth`) and its run steps before the build are not judged, only the
  actions they use (fix pass 9). Can one of them change what reaches the artifact in a way no port's review would
  see, or reach a job holding `id-token: write`?
- strings loaded through double-quoted escapes (`\x1b`, `​`, `\u0085`) are refused in pinned scripts and at the
  build window, and lone surrogates everywhere (fix pass 9), but not elsewhere: is any other loaded string compared,
  printed or used where such a character matters?
- the allow-listed job's called workflow is pinned by its sha256 and read beside the workflow: does what GitHub runs
  for `./.github/workflows/notify-consumers.yml` always equal that file (the caller's commit, a fork's pull request, a
  re-run after a push)?
- top-level keys the checker does not name (`run-name`, `defaults` beyond `run`), and the workflow's `concurrency`;
- what `actions/upload-artifact` and `actions/download-artifact` at the pinned SHAs do with inputs the template's steps
  do not give, given that template steps are compared whole;
- another workflow of the same repository, or a reusable workflow it calls, that runs in the same run.

**Write your full report to `$W/tmp/r11review/ROUND11_REPORT.md` as well as returning it as your last message.** The
orchestrating session may hand off before your report arrives; that file is what the next session reads. Write it
before you return, and again if you revise it. **If any step or sub-step below is interrupted or not done, for any
reason (a safety interruption, a time or context limit, a tool failure), say so in a FIRST section titled "What this
round did NOT do", listing exactly which steps and sub-steps were not done and why, and do not present the round as
complete.** Write that section as soon as an interruption happens, before anything else.

**Frozen inputs (READ-ONLY).** Copy anything you want to change into a directory you create under `$W/tmp/r11review/`;
never write under `/tmp` or `/var/tmp`, and never modify an existing file under `$W/tmp/` or `$W/util/`.
- The checker under review: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
  `23707ac6de0b351291372ec7a3c07eb2f328c2200d80f831dacf4976e393ba35` (1439 lines); a frozen copy is
  `$W/tmp/sweep/checker-r10/checker_r10_as_delivered.py`. If the live file's hash differs, review the frozen copy and
  report the difference.
- The pins file it reads by default: `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json`, sha256
  `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3` (18 pins, 552 lines), UNCHANGED by fix pass 9; a frozen copy is
  `$W/tmp/sweep/checker-r10/pins_r10_as_delivered.json`.
- As round 10 reviewed them: `$W/tmp/sweep/checker-r10/checker_r9_as_reviewed.py`, sha256
  `9cf16a2f13152ddc75ce2f695758a6f5df95f93c713b347b46adc5959c157bb9` (1172 lines), and
  `$W/tmp/sweep/checker-r10/pins_r9_as_reviewed.json`, sha256 `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3`.
- The interdiffs: `$W/tmp/sweep/checker-r10/checker_r9_to_r10.diff` (489 lines, +305/-38), sha256
  `f53c070e5f11d3f331304f062abe686530c72d383ea4cf7801e25d5956a62f16`, and `$W/tmp/sweep/checker-r10/pins_r9_to_r10.diff` (0 lines, empty: the pins file did not change),
  sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. If either does not hash so, STOP and report.
- The template every run uses: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`, sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, with its siblings `publish-cascor-model.yml` and
  `publish-protocol.yml` (each judged with `--repo juniper-cascor`). juniper-cascor at `f5ed3017` (#777) and at `main`
  `b5b28dc3` (#779) holds the same three files byte for byte: fix pass 9 re-fetched `main` read-only at 21:26:47Z into
  `$W/tmp/sweep/checker-r10/cascor-main-fetch/` (`evidence/fetch_main_r10.log`). Re-fetch with read-only GETs if you
  doubt it.
- juniper-data's called workflow, `notify-consumers.yml`, fetched read-only from juniper-data `main` (`6b734fd9`) into
  `$W/tmp/sweep/checker-r10/juniper-data-main-fetch/`: sha256
  `e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078`, 11039 bytes, blob `ab0cade2`, the bytes round 10
  read. `EXTRA_JOBS` pins that sha256.
- The 15 port simulations, the seeds of 15 pins: `$W/tmp/sweep/checker-r7/port-sim/` (fix pass 9's regeneration,
  `$W/tmp/sweep/checker-r10/port-sim/`, equals it byte for byte, plus `notify-consumers.yml` placed beside juniper-data's
  simulation, as juniper-data's tree holds it; the rows are in `checker-r10/port_sim_table_r10.py`).
- The manifest `$W/tmp/arc/sweep_scripts.sha256`, SEVEN lines, sha256 `e701709e2b11585f30511e96f9823c28c9c44e5b405b10232713b6636ca3f42d`; run `sha256sum -c` on it from
  `$W`. Fix pass 8's is kept as `sweep_scripts.r10.sha256`; only the checker's line changed (the pins file's and the
  writer's, `c47940ad…`, are as before). No allow-list data file was added: `EXTRA_JOBS` is a constant of the checker.

**Checker usage.** Run it with `--help` first. `--repo` is required (one of its `REPOS`). `--pins PATH` replaces the
default pins file, which sits beside the checker; it is an operator argument, and nothing in a workflow chooses it. A
copy of the checker placed elsewhere finds no pins file beside it: pass `--pins`. The checker prints the pins file's
path and sha256 first; a pins file it refuses, and a template it refuses (fix pass 9: a `uses:` in its chain that is
not `owner/repo@<40 lowercase hex>`, or one action at two refs), stop the run (exit 1, nothing checked). A workflow
whose job calls an allow-listed reusable workflow needs the called file beside it (a missing file fails).

**Also open to you:** fix pass 9's tools and evidence in `$W/tmp/sweep/checker-r10/`: `rerun_all_r10.bash` (every
re-run, in order, about 9 minutes; `evidence/rerun_all.out`), `finish_r10.bash` (the frozen copies, the
interdiffs, the manifest), `untouched_r10.bash`, `lint_checker_r10.bash`, `survey_fp9.py` (every chain job's `uses`,
every upload step's keys and inputs, every extra job, every expression key and lone surrogate, in cascor's three, the
15 simulations and every repository's current workflows), `fetch_main_r10.bash`, `adapt_r10.py` (how fix pass 8's
drivers were copied and re-pointed), `r10lib.py` and `checker_r10_named.py` (shared plumbing), `judge_all_r10.py`,
`judge_r9_mutants_r10.py`, `new_mutants_r8_rerun_r10.py`, `new_mutants_r9_rerun_r10.py`, `judge_r10_mutants.py`
(round 10's own cases), `new_mutants_r10.py` (this pass's executed negative tests N10-1 to N10-16 and controls C10-1 to
C10-3, with round 10's execution methods: GitHub's TypeScript parser, the runner's input building, the pinned action's
own `oidc-exchange.py` and `twine-upload.sh` lines, a stand-in release run with "Re-run all jobs"), `checker_proof_r10.py`
(built by `make_proof_r10.py` from fix pass 8's proof and `proof_r10_tail.py`), `run_proof43_r10.bash` and
`classify_proof43_r10.py`, `rederive_pins_r10.py`, `parsers/` (copies of round 9's parser drivers and fix pass 8's
`typing_diff.py`), `node/` (copies of round 10's `tsparse.mjs` and `inputs.mjs` with their modules), and `evidence/`.
The development runs before the final one are kept beside it (suffixes `.pre`, `.run1` to `.run4`). Round 10's tools
and GitHub's sources are in `$W/tmp/r10review/` (`external/`: the runner's C# readers and handlers, the publish
action's `oidc-exchange.py`, upload-artifact's and download-artifact's sources, the toolkit's artifact `util.ts`), and
round 9's in `$W/tmp/r9review/external/` (the publish action's `action.yml` and `twine-upload.sh`, the runner's
`YamlObjectReader.cs`). Re-run rather than trust them. Run any Python that reads a cloned tree with `python3 -I`.

**What the fix pass was meant to do.** `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`: § "Round-10 review" (the findings),
§ "The owner's ruling on action refs" (verbatim) and § "Fix pass 9 (round 10's fixes and the action-refs ruling;
checker-r10)" (the decisions, the counts, the deviations, the leads, the residual risk). The checker's docstring,
§ "Fix pass 9: upload inputs, extra jobs and action SHAs", states every decision. In short:
- B10-1: each TestPyPI and PyPI upload step holds exactly `{name, uses, with}` (`UPLOAD_STEP_KEYS`); its `with` exactly
  the template's inputs by literal name, with the template's values as GitHub types them, adding only `verbose` and
  `attestations`, each the boolean true (`UPLOAD_OPTIONAL_INPUTS`; cascor's sub-package publishers add `verbose`, three
  ports `attestations`); a key equal to an input but for case or `-`/`_`, and an expression key, each with its own
  message (`upload_problems`); beyond the brief, a mapping key holding `${{` refused anywhere (`document_problems`);
- B10-2: every job outside the chain's five refused unless `EXTRA_JOBS` holds it for (`--repo`, the workflow file's
  name, the job id), compared whole, its called reusable workflow read beside the workflow and compared by sha256
  (`extra_job_problems`); today the list holds juniper-data's `notify-consumers` alone;
- B10-3 (the owner's ruling): every `uses:` in the five chain jobs equals the template's exact `owner/repo@<SHA>` for
  an action the template's corresponding job uses (`uses_problems`); the install job may use the template's
  setup-python and checkout (`INSTALL_ACTIONS`, a deviation: the root template's install job uses setup-python alone,
  cascor's sub-package publishers' a sparse checkout); a template whose chain refs are not 40 lowercase hex, or that
  pins one action at two refs, is refused;
- m10-a: per-workflow catch-all over judging, labelling and printing; stdout and stderr with `backslashreplace`; a
  `RecursionError` at load is a load failure; a lone surrogate refused in any string;
- n10-a, n10-b: true messages for `runs-on` (the string `ubuntu-latest`, as the template writes it) and
  `persist-credentials` (the boolean false).

Scrutinise hardest:
- **One level further out** (the centre of this round): the starting points above, and anything else the checker
  reads but does not judge, or never reads, that runs code in, beside or before a job holding `id-token: write`, or
  changes the artifact it uploads. EXECUTE each candidate as far as this host allows (say what is a stand-in).
- **The upload rule**: is every way GitHub can deliver an input to the publish action covered (a key through an alias,
  a tag, an escape, a merge key, a flow mapping, a case or `-`/`_` variant, an expression key, an input the action
  declares that the template does not give)? Is `verbose: true` or `attestations: true` harmless at the pinned SHA?
- **The allow-list**: is the job compared exactly as GitHub types it? Is reading the called file beside the workflow
  the file GitHub runs? Can an allow-listed job, unchanged, still reach the artifact (R10-7's re-run path, round 10's
  lead 6 on "Re-run all jobs")?
- **The ref rule**: is every `uses:` of the five jobs read (a step `uses` that is not a string, a job-level `uses`, a
  composite or docker action, a ref with a path)? Is the install job's widened set (`INSTALL_ACTIONS`) right? Is the
  template check (40 lowercase hex, one ref per action) enough?
- **The catch-all**: can a workflow still stop the run, hide a PASS, or make the next workflow's verdict wrong?
- **Every message and docstring claim**: true wherever given.

A rule that admits a bypass is a MAJOR (a BLOCKER where it reaches a job holding `id-token: write`). A rule that refuses
one of the 15 port simulations, or one of cascor's three publishers, is a MAJOR too (over-strict against a real port).
A pin that differs from its stated source is a MAJOR. A ref the ruling requires a port to change is a port change, not
over-strictness: fix pass 9 found none (every simulation and every repository's current workflow uses exactly the
template's five SHAs).

**Expected, by design:**
- `checker_proof_r10.py`: 432 of 432 (fix pass 6's 306, fix pass 7's 40 NEW8, fix pass 8's 46 NEW9,
  33 NEW10, 7 command-line). Seven earlier expectations changed, each a message only, each stated on its row: B5ap,
  B5aq, B5ar (the build job's runs-on message, n10-a), K9d, K9e (the publish jobs' runs-on message, n10-a), Y9j
  (persist-credentials: no, n10-b) and N9d (the catch-all's message, m10-a). Fix pass 7's and 8's re-baselining is
  unchanged (43 / 192 / 5; PYa, R46f, CH8b);
- every earlier mutant set and corpus keeps fix pass 8's recorded verdicts (`judge_all_r10.py`: 0 moved);
- round 9's cases: 32 of 32 as expected; M9-12 (a control holding an extra job) PASS -> FAIL by design (B10-2);
- round 10's cases: R10-1 to R10-8 FAIL, each with fix pass 9's rule named; R10-9 FAIL; R10-10 and R10-11 FAIL with the
  template judged after them (exit 1, no traceback); C10-0 PASS; O10-7 (an extra job) and O10-8 (`print-hash: true`)
  PASS -> FAIL by design; O10-11 and O10-13 FAIL with true messages; every other O10 keeps round 10's verdict;
- X8-1 to X8-8 FAIL the live checker and PASS `checker-r8/checker_r8_naive.py`; N9-1 to N9-9 FAIL the live checker and
  PASS fix pass 7's; their controls PASS;
- `new_mutants_r10.py`: N10-1 to N10-16 FAIL the live checker and PASS fix pass 8's (N10-13: fix pass 8's stops with a
  traceback, leaving the template unjudged); 7 executed with the outcome changing; N10-1 (an alias key) is refused by
  GitHub's TypeScript parser too, so it is not a bypass on GitHub; 8 are not executable here (GitHub resolves refs and
  secrets); C10-1 to C10-3 PASS;
- port-sim's own run lists 7 FAIL among its 25 variants: fix pass 8's 6, and juniper-data's [faithful], because the
  probe writes no `notify-consumers.yml` beside it (the called file is placed before the table); only the 15-row table
  counts;
- `typing_diff.py`: 6 cases the checker alone refuses (`0x`/`0o` above 0x7FFFFFFF); the fuzz: 0 differ for libyaml and
  both YamlDotNets, Node 7 (round 9's construct);
- `rederive_pins_r10.py` prints "ends with newline: False" for a file that ends in one (a driver bug inherited from
  round 9's copy);
- round 2's 43 cases: 26 as round 2 expected, C1 PASS -> FAIL and 13 FAIL kept (fix pass 7), K1 and K2 (item 23's
  "a Dependabot bump in one publisher only") PASS -> FAIL by design under the owner's ruling, R19 FAIL kept with
  n10-b's message; the driver says "26 of 43" and exits 1 for that reason;
- flake8 `--isolated` at 512 columns reports 3 E203 (Black's slice spacing); pre-commit's own hooks pass.

Do these, in order:

1. **The delta.** Read every hunk of the interdiff: `UPLOAD_STEP_KEYS`, `UPLOAD_OPTIONAL_INPUTS`, `UPLOAD_ALIASES`,
   `PINNED_USES`, `EXTRA_JOBS`, `lone_surrogate`, `document_problems`, `by_action`'s docstring, `template()`'s new
   checks and outputs, `runs_on_problem`, `uses_problems`, `upload_problems`, `extra_job_problems`, the install job's
   checkout and runs-on messages, `check()`'s new calls (the load's `RecursionError`, the extra jobs, the refs, the
   uploads, the build job's runs-on message, the guards on a `with` that is not a mapping), `main()`'s catch-all and
   stream settings, and the docstring. Hunt new bugs: does a change alter behaviour beyond its purpose; is a new rule
   wrong, over-strict or bypassable; is every docstring claim and message true?
2. **The pins file.** It is unchanged: confirm its sha256, and re-derive each of the 18 pins from its source with code of
   your own (or re-run `rederive_pins_r10.py` and read it).
3. **One level further out** (the centre of this round): every item under "Scrutinise hardest", the starting points
   first.
4. **Re-run the proofs.** Copy `rerun_all_r10.bash` and the drivers it calls under `$W/tmp/r11review/` (point their
   outputs there; a copy of the reviewed checker needs `--pins`; place `notify-consumers.yml` beside juniper-data's
   simulation) and run them; compare every count with the Fix pass 9 section's. Regenerate the 15 simulations with
   round 2's probes and run the 15-row table in your own copy: all 15 must PASS, and cascor's three from the landing
   tree and from `main`. Re-run round 9's fuzz and `typing_diff.py` from your copies.
5. **Bypass mutants (EXECUTED).** Build at least 8 NEW mutants of a passing port aimed at fix pass 9's design and at
   the level outside it. EXECUTE each so it is shown to change the outcome, not just to pass the checker (stand-ins, as
   `new_mutants_r10.py` does; a real pip in a venv built under `$W/tmp/r11review/` where pip's behaviour is the point).
   Each must FAIL the checker; any that passes and changes the outcome is a finding; one that passes and changes
   nothing is not a bypass (say so).
6. **Over-strictness.** Try harmless edits a real port might make: `timeout-minutes` on any chain job, the environment
   mapping, quoting and key order, `verbose`/`attestations` in other forms, a flow-style `with`, a comment after a
   `uses:` SHA, an extra job after the PyPI job, juniper-data's allow-listed job with its keys reordered or quoted.
   Report each refused, and whether its reason is true. An install-script edit that fails on its pin is by design, and
   so is a port ref that is not the template's (the owner's ruling).

**Rules.** Use read-only `gh` GETs only. Never commit, push, comment on, edit, approve or merge anything. Put no
secrets, tokens, e-mail addresses or personal data in the report. Take times from `date -u`; never estimate one. The
Bash tool refuses `git -C`, `cd` into another worktree combined with git, some heredocs, some command lines that name
`.github` paths and some that name git's environment variables: write small script files under `$W/tmp/r11review/`
(with the Write tool if a heredoc is refused) and run those. A `cd` in one Bash call persists into the next: return to
`$W` afterwards. Run Python with `-B`, so no `.pyc` lands in a frozen directory.

**Report** (your last message, and `$W/tmp/r11review/ROUND11_REPORT.md`), with "What this round did NOT do" first if any
step was not done, then the findings, most severe first. Give each finding:
- its severity and file:line;
- the failure scenario;
- the evidence (code, or a command and its output);
- the fix.

Then give the bypass-mutant table (id, target, checker verdict, executed outcome), what each starting point came to,
the re-run counts against the Fix pass 9 section's, the 15-simulation table, and the checks you found sound. Mirror
your probe outputs into `$W/tmp/r11review/`.
