# Round-11 review report: fix pass 9 on the cross-repo port checker (`checker-r10`)

Reviewer: the round-11 fresh reviewer, worktree `ethereal-munching-peacock`. Brief: `tmp/sweep/ROUND11_BRIEF.md`. Ran
2026-11-24 22:25Z to 23:05Z (times from `date -u`). Every probe, driver and output is under `tmp/r11review/`
(evidence in `tmp/r11review/evidence/`).

Under review: the checker `util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256 `23707ac6…93ba35`,
1439 lines, equal to `tmp/sweep/checker-r10/checker_r10_as_delivered.py`) and the pins file
`util/ad-hoc/2026-11-24_publish_port_install_pins.json` (`d539f05f…a69b3`, 552 lines, unchanged). Every frozen input
hashed as the brief states, including the interdiffs (`f53c070e…`, empty `e3b0c442…`), the template (`b6826ee6…`) and
`notify-consumers.yml` (`e17ddc9b…`, 11039 bytes). `sha256sum -c tmp/arc/sweep_scripts.sha256` reported 7 OK, at the
start and at the end. Both files are unchanged at the end.

## What this round did NOT do

Every step (1 to 6) and every sub-step was done. These are the departures and limits, so the round's completeness can be
judged:

1. **One write outside `tmp/r11review/`.** I built a small .NET probe with round 9's .NET 8 SDK
   (`tmp/r9review/parsers/dotnet`, executed in place, every home, cache, NuGet folder and TMPDIR redirected under
   `tmp/r11review/dotnet-probe/`). The SDK still changed the mtime of its own directory
   `tmp/r9review/parsers/dotnet/metadata/` at 22:46:23Z. That directory holds no files. Nothing else under the frozen
   trees changed (`evidence/untouched_r11.final.out`: no other entry newer than the round's start, no new
   `__pycache__`, the checker and pins hashes unchanged, manifest 7 of 7 OK).
2. **GitHub itself was not available.** That covers its server-side parser, how it resolves `uses:`, its scheduler
   (concurrency groups), its artifact service and OIDC. Instead:
   - GitHub's TypeScript parser (`@actions/workflow-parser` 0.3.61, round 10's install) was **run** on every mutant
     that passes or carries a payload;
   - the runner's step-input map (`StringComparer.OrdinalIgnoreCase`, `PipelineTemplateConverter.cs:174`) was **run**
     on .NET 8.0.34, with invariant and with ICU globalization;
   - the chain was **run** with fix pass 9's own stand-ins: its artifact store, stand-in indexes and artifacts API,
     imported from my relocated copy of `new_mutants_r10.py`. I added logging stand-ins for `twine` and `pip`;
   - M11-8 and M11-10 are **not executable** here.
3. **Step 4's lint did not run pre-commit itself.** As round 10 did, I ran each content check that juniper-ml's
   pre-commit config applies to `util/ad-hoc/*.py` and `*.json`, plus flake8 and B914, on byte-identical **copies**
   (`rerun/lint_copy_r11.bash`). No fixer hook could therefore touch the live files.
4. **The terminal rendering used tmux 3.6** as the terminal emulator, not a graphical terminal. "What a viewer sees" is
   computed from tmux's own cell attributes (SGR 8, conceal) by `visible_r11.py`. The raw cell capture and the
   attribute capture are kept beside it.
5. **juniper-data's own CI was not read** (it is outside `$W`), so I have not verified whether it pins
   `notify-consumers.yml`.

**Verdict: 0 BLOCKER, 1 MAJOR, 4 MINOR, 5 NIT.** The round is COMPLETE. The MAJOR means it does **not** clear the gate
under the stopping rule: fix pass 10, then round 12.

Fix pass 9's own rules held against everything I aimed at them:
- the exact upload sets, including non-ASCII look-alikes, executed on .NET;
- the allow-list compared whole;
- the per-job SHA sets;
- the catch-all against crashes.

The MAJOR sits one level further out, in what the checker **prints**.

## Findings, most severe first

### M11-A MAJOR: workflow strings are printed raw, so a refused port can display as PASS, and can hide the next workflow's FAIL

**Where.** Fix pass 9's m10-a fix escapes only what the output stream cannot encode, `main()` `:1399-1401`. The
docstring makes the same claim at `:239-243`. ESC, CR, LF and BS are all encodable, so they pass through untouched.

The checker interpolates loaded strings without `repr` into many messages:
- `:1247` `build step {name} lacks if:`
- `:1220` `does not parse as bash … {error}`
- `:1197` `{scope} sets {key}` (the scope holds the step's name)
- `:1273` window problems
- `:1057-1068` install-step messages (`{label}`)
- `:1026` `needs`; `:1030` and `:1238` permissions; `:1113` `workflow_dispatch`; `:1120` top-level permissions;
  `:1282` environment, each whenever the value is a string

`main()` prints those messages at `:1428-1429`. Two other rules each cover only part of the path:
- the raw-file rule (`file_problems`, `:547-557`) reads the file's bytes, and a double-quoted `"\x1b"` or `"\n"` is
  printable ASCII there;
- `document_problems` (`:565-593`) refuses lone surrogates and `${{` keys only.

This is starting point 2's case: a string loaded through a double-quoted escape, then printed.

**Scenario.** A port is refused for a real weakening, R10-1's `repository_url:` on the PyPI upload. It also adds one
build step before the build. That step has no `if:`, so the checker's "lacks if:" message prints its name raw. The name
is a double-quoted escape payload:

```
"\x1b[H\x1b[2J\x1b[3J<the checker's own pins line>\nPASS juniper-cascor/publish.yml  (…)\n1 of 1 pass\n\x1b[8m"
```

On a terminal, that payload:
- clears the screen and the scrollback;
- draws the control run's real PASS output;
- conceals everything printed after it: the real reasons, `0 of 1 pass`, and even the shell's next line.

With two workflows on one command line (M11-2), the first draws `PASS`, `PASS`, `2 of 2 pass`, and the second
workflow's real FAIL is concealed.

Without any escape character (M11-3), newlines alone inject whole lines into captured output, ahead of the real ones.

The exit status stays 1 in every case. The display is what lies.

**Evidence.** `mutants_r11.py`, `render_tmux_r11.bash`, `render_history_r11.bash`, `rerun/c10/node/ts_names_r11.mjs`.

M11-1, the viewer's screen (`evidence/M11-1.screen-visible.txt`), is the whole screen:
```
pins: …/util/ad-hoc/2026-11-24_publish_port_install_pins.json (sha256 d539f05f…, 18 pins)
PASS juniper-cascor/publish.yml  (PUBLISH_PACKAGE=juniper-cascor, PUBLISH_DIST_DIR=dist, PUBLISH_TAG_PREFIX=v)
1 of 1 pass
```

What tmux holds behind that screen (`evidence/M11-1.screen-attrs.txt`):
- rows 4 to 8 carry `\x1b[8m`;
- those rows are ` lacks if: …`, the `repository_url` reason, `0 of 1 pass` and `[checker exit status 1]`.

The scrollback (`evidence/M11-1.history.txt`) holds **no** `FAIL` line, and no line printed before the run either.

The other two cases:
- **M11-2** (`evidence/M11-2.screen-visible.txt`): `PASS juniper-ml/publish-ci-tools.yml …`,
  `PASS juniper-ml/publish-doc-tools.yml …`, `2 of 2 pass`. Doc-tools' `FAIL` (`Skip_Existing`) and `0 of 2 pass` are
  concealed.
- **M11-3**: captured stdout holds the line `PASS juniper-cascor/publish.yml …`, and the summary lines `1 of 1 pass`
  then `0 of 1 pass`. My own driver's first line-oriented parse read the verdicts as `['FAIL', 'PASS']` for one
  workflow. Fix pass 9's own step-1 idiom (`run_checks_r10.bash | grep -E 'pass$'`) would list both summaries.

GitHub's TypeScript parser accepts all three files with no parse or convert error, and holds each step name with its
`U+001B` and newlines (`evidence/ts_names_r11.out`).

**Fix.** Two parts:
1. **Refuse at load.** Extend `document_problems` to refuse, in every loaded string, any character other than printable
   text, a tab and a newline, and to refuse a newline in any mapping key and in any step or job `name`. This is the
   lone-surrogate rule widened. All 37 files checked admit it (`evidence/fixcheck_r11.out`: cascor's three, the 15
   simulations, every repository's current publishers and `notify-consumers.yml`).
2. **Escape at output.** As defence in depth, interpolate every workflow-derived value with `!r`. In `main()`, also
   escape every C0 and C1 control character (and U+2028 and U+2029) in each printed line. The only newlines the checker
   itself puts inside a message are `pin_mismatch`'s diff joins, which it builds from lines it split.

### M11-B MINOR: an alias bomb stops the run, so m10-a's "nothing one workflow holds stops the next being judged" is untrue

**Where.**
- `document_problems` `:573-587` walks the loaded graph as a tree, with no record of nodes already visited;
- `UniqueKeyLoader.compose_node` `:488-493` admits YAML anchors and aliases;
- the claims are at `:239-243`, `:569-570` ("Walked without recursion, so a deep document cannot stop the walk") and in
  `main()`'s comment at `:1413-1415`.

**Scenario.** A 49 KB workflow holds an extra job whose `strategy.matrix` nests lists of ten aliases each, nine levels
deep. The loader builds it at once, because PyYAML shares the lists. `document_problems` then walks about 10**10 nodes.
The checker prints no verdict for that file, and the next workflow on the command line is never judged.

It fails closed: no PASS is printed, and the exit status is never 0. GitHub's TS parser accepts the shape
(`evidence/ts_bomb_r11.out`).

**Evidence** (`bomb_r11.py`, `evidence/bomb_r11.out`):

| depth | wall time | result |
|---|---|---|
| 3 | 0.28 s | FAIL |
| 4 | 0.32 s | FAIL |
| 5 | 1.14 s | FAIL |
| 6 | 8.28 s | FAIL |
| 9, then the template, on one command line | TIMEOUT at 120 s | no output for either |

Time grows about 8x per level, so depth 9 extrapolates to about 70 minutes.

**Fix.** Refuse an alias at load (`isinstance(event, yaml.AliasEvent)` in `compose_node`) and an anchor on any node.
No template, port or simulation holds either (`evidence/fixcheck_r11.out`). The rule also removes N10-1's class.
Alternatively, record the ids of containers already visited in every walker.

### M11-C MINOR: the build job's steps before the build reach the window and the artifact by more than the docstring states

**Where.**
- The residual statement at `:271-276`: "a step there could leave an extra wheel in the dist, which Record SHA256SUMS
  would then hash".
- R5-F4's claim at `:67-68`: `BASH_ENV`, `ENV`, `BASHOPTS`, `SHELLOPTS` "refused as env keys at every level".
- `uses_problems` (`:947-964`), with the build job's set from `template()` (`:897-912`). It admits
  `actions/upload-artifact` anywhere in the build job, because the template's build job uses it.

**Scenario and evidence.** This is starting point 1. Both cases PASS the checker and change the outcome. Each was
executed with stand-ins.

- **M11-9.** "Install build tools" also writes `BASH_ENV=<hook>` into `$GITHUB_ENV`. The window's unchanged
  `twine check dist/*` step runs the hook first, and the hook copies in a wheel the build never made. Then:
  - the template's own Record SHA256SUMS hashes that wheel;
  - TestPyPI takes it;
  - the pinned install check imports it ("A WHEEL THE BUILD NEVER MADE | TestPyPI OK: v0.14.0");
  - PyPI takes it.

  Evidence: `evidence/M11-9.log`. F1's window allow-list, F4 and R5-F4 bind the YAML text of env mappings and window
  steps. They do not bind what `$GITHUB_ENV`, `$GITHUB_PATH` or a background process makes those steps run.
- **M11-12.** A step before the build uses `actions/upload-artifact@cf430e03…`, the template's own SHA, naming
  `${{ env.PUBLISH_PACKAGE }}-dist` for files a step had staged. Then:
  - attempt 1: the template's upload is refused as a duplicate, and the build job fails;
  - attempt 2, "Re-run failed jobs": the template's reuse step finds the staged artifact (`reuse=true`);
  - TestPyPI, the install check and PyPI then take files that neither the build step made nor Record SHA256SUMS
    hashed. PyPI's wheel says "STAGED BEFORE THE BUILD, NEVER BUILT OR RECORDED BY IT" (`evidence/M11-12.log`).

  That is R10-5's outcome (B10-2) through a step rather than a job.

Neither case reaches code or a credential in a job holding `id-token: write`. Only the artifact's bytes travel, and the
repository's own build decides those anyway: a step before the build can replace the `build` tool. That is why this is
MINOR, within the zone the docstring concedes, but more than it states. A port's review must read every step before the
build as code that runs inside the window. The checker's PASS currently implies otherwise.

**Fix.**
1. State it in "What this cannot see": steps before the build can change what every later build step runs (through
   `$GITHUB_ENV`, `$GITHUB_PATH` and background processes), and can make `<PUBLISH_PACKAGE>-dist` themselves.
2. A cheap rule that admits all 37 files (`evidence/fixcheck_r11.out`): in the build job, `actions/upload-artifact`
   only in the step named `Upload dist artifacts`.
3. If the owner wants R10-5's outcome closed whatever job carries it, this zone is where it is still open. Pinning each
   port's build steps, as its install scripts are pinned, would close it.

### M11-D MINOR: a workflow concurrency group shared with another workflow cancels a publish run between its uploads (R4-4's purpose)

**Where.** `check()` `:1126-1135`, and the docstring at `:55-58`: "the workflow's admitted when it never cancels a run
in progress".

**Scenario.** M11-10 PASSES with `concurrency: {group: pr-budget-alarm, cancel-in-progress: false}`.
juniper-cascor's own `pr-budget-alarm.yml` uses that constant group with `cancel-in-progress: true`, on a schedule
(`peek_concurrency_r11.bash`).

GitHub's documented semantics:
- a concurrency group is repository-wide;
- whether a run in progress is cancelled is decided by the run queued **next**: its own `cancel-in-progress`, not the
  running one's.

So the next scheduled alarm run cancels the publish run, for example while its PyPI job waits at the `pypi` gate after
TestPyPI has taken the files. That is R4-4's harm (MINOR in round 4; availability only, recoverable through the republish
ladder). Not executable here.

**Fix.** Hold the workflow's `concurrency` to the one form all 10 publishers that carry one use: absent, or exactly
`{group: "<workflow file stem>-${{ github.ref_name }}", cancel-in-progress: false}`. All 37 files admit it
(`evidence/fixcheck_r11.out`). Also correct the docstring's reasoning.

### M11-E MINOR: the docstring's new "What an action's code does" misstates the one action that handles the OIDC token

**Where.** `:266-268`: "every action of the chain runs at the template's exact commit SHA, so its code is the code the
template's review accepted at that SHA".

**Fact** (from the pinned sources):
- `pypa/gh-action-pypi-publish@7245906f` is a composite action;
- its step writes a docker action whose image is `docker://ghcr.io/pypa/gh-action-pypi-publish:<github.action_ref>`
  (`tmp/r10review/external/pypi-publish-7245906f-create-docker-action.py:16-20`; `action.yml:127-168`);
- the code that exchanges the job's OIDC token and uploads, `/app/oidc-exchange.py`, `/app/attestations.py` and
  `twine` (`twine-upload.sh:123`, `:202`, `:211-214`), therefore lives in an image named by a registry **tag**;
- a re-pushed tag changes that code without changing any SHA in the workflow.

Not executable here (it needs the registry).

**Fix.** Say that the SHA pins the action's composite steps and the image tag's name, not the image. Then accept that in
writing, or record the image digest the template's review saw.

### NITs

- **n11-a** (`:1016-1017`, O11-10). A called file that differs from the pin only in CR LF line endings is refused with
  "what the called workflow runs has changed". That is untrue: YAML normalizes line breaks, and the checker itself admits
  a CR LF workflow (O11-11 PASS). Say "its bytes differ from the pinned file's".
- **n11-b** (`:959-963`, `:620-621`, M11-8). `PyPA/gh-action-pypi-publish@<the template's SHA>` is refused as "an
  action the template's PyPI job does not use (another owner, a fork, …)", and also as "pypi has 0 uploads". GitHub's
  repository names are case-insensitive, so it would run the same code, and the job does upload. The verdict is right.
- **n11-c** (`:1008`, `:989`). Two harmless forms are refused by exactness:
  - `needs: [pypi]` on the allow-listed job (O11-9);
  - `verbose: "true"` (O11-4d), which hands the action the same text.

  Both messages are true and no port writes either, so this is by design: record it only.
- **n11-d** (`:894`). `template()` binds the local name `installs`, which shadows the module function `installs()`.
  Harmless today.
- **n11-e** (`:908-911`). The two-refs refusal says "so no port's ref can equal the template's". The real reason is that
  the install job's widened set would take `next(iter(...))` of two refs, which is arbitrary.

## Bypass-mutant table (step 5: 11 new mutants, 3 controls)

Evidence: `evidence/mutants_r11.out`. Mutant files are under `tmp/r11review/mutants/`.

| id | target | checker | executed outcome |
|---|---|---|---|
| C11-0 | control: the template | PASS | - |
| C11-2 | control: ci-tools and doc-tools on one command line | PASS, PASS | - |
| C11-3 | control: juniper-data's simulation, its called file beside it | PASS | - |
| M11-1 | printing: R10-1 (refused) plus an ESC payload in a build step's name | FAIL, exit 1 | **displayed as PASS** (tmux): `PASS …`, `1 of 1 pass`; the real FAIL is gone from screen and scrollback, the rest concealed (M11-A) |
| M11-2 | printing, the next workflow: a payload in ci-tools; doc-tools' `Skip_Existing: true` (refused) | FAIL, FAIL, exit 1 | **displayed as `PASS`, `PASS`, `2 of 2 pass`**; doc-tools' FAIL concealed (M11-A) |
| M11-3 | printing, captured text: R10-2 (refused) plus newlines in a step's name | FAIL, exit 1 | captured stdout holds `PASS …` and `1 of 1 pass` before `0 of 1 pass`; a line parse read `['FAIL','PASS']` (M11-A) |
| M11-4 | the catch-all: an alias bomb (49 KB) in an extra job, then the template | no verdict (timeout) | 8x per level; at depth 9, nothing printed in 120 s and the template never judged (M11-B) |
| M11-7 | the upload: `reposıtory-url`, `ſkip-existing`, `attestatıons: false` | FAIL | .NET 8 `OrdinalIgnoreCase`, invariant and ICU: none equals a declared input, so the outcome is unchanged. Not a bypass |
| M11-8 | the ref rule: `PyPA/gh-action-pypi-publish@<SHA>` | FAIL | not executable; refused, harmless (n11-b) |
| M11-9 | before the build: a `BASH_ENV` hook through `$GITHUB_ENV`, run by the window's twine step | **PASS** | stand-ins: a wheel the build never made is recorded, install-checked and published (M11-C) |
| M11-10 | the workflow concurrency group shared with `pr-budget-alarm` | **PASS** | not executable; by GitHub's documented semantics the alarm cancels the run in progress (M11-D) |
| M11-11 | the top level: `run-name` naming another release | PASS | the ceremony's own `select_publish_run`, executed: the selection is unchanged. Not a bypass |
| M11-12 | before the build: `upload-artifact` at the template's SHA naming `<pkg>-dist` | **PASS** | stand-ins: after "Re-run failed jobs" both indexes take files that were never built or recorded (M11-C) |

M11-5 and M11-6 (allow-list probes) were folded into step 6 as O11-8 and O11-9.

## What each starting point came to

1. **The build job's checkout inputs and its steps before the build.** They change what reaches the artifact, by more
   than the docstring states (M11-9, M11-12; M11-C). The checkout's `repository`, `ref`, `token` and `path` can build
   other code, which is documented. Nothing reaches an id-token job except the artifact's bytes.
2. **Strings loaded through double-quoted escapes.**
   - **Printed**: M11-A (MAJOR).
   - **Compared**: every comparison is exact, so an escape changes the string and the rule refuses it. The only
     normalization, `known`, chooses a message and never admits. The runner's case folding was executed (M11-7): no
     look-alike matches.
   - **Used**: `.split()` for the sparse path splits on more whitespace than checkout does, so it fails safe.
3. **The called workflow.** GitHub resolves `./.github/workflows/notify-consumers.yml` at the caller's commit:
   - a release run, at the tag's commit;
   - a re-run, at the same SHA;
   - a dispatch, at its ref;
   - fork pull requests do not apply, because the publish workflow has no `pull_request` trigger.

   So the file read beside the workflow is the file GitHub runs, exactly when the operator fetches both at one commit:
   the same condition the `publish.yml` check itself has. Unchanged, the called file holds two run steps (curl and jq,
   values through `env`, no `${{` in the run text, no artifact action), so it cannot reach the artifact. N10-6's path
   needs a changed file, which the sha256 pin refuses.

   Observation: the pin binds only when this checker runs. Whether juniper-data's own CI pins the file was not verified.
4. **Top-level keys the checker does not name.**
   - `run-name` reaches the ceremony only as a fallback (M11-11, executed: no effect).
   - `defaults`: GitHub defines only `run.shell` and `run.working-directory`, and both are refused when set.
   - `concurrency`: M11-D.
5. **upload-artifact and download-artifact inputs the template's steps do not give.** The template steps are compared
   whole, so a port cannot add any.
   - download-artifact v8.0.2's defaults are safe: `digest-mismatch` is an error, the download is from this run, and
     the artifact is looked up by name (`download-artifact.ts:20-46`, `:88-101`).
   - upload-artifact v7.0.2 takes `overwrite`, `include-hidden-files` and `archive` from its `action.yml` defaults
     (`input-helper.ts:11-13`; that `action.yml` was not re-fetched).
6. **Another workflow, or a reusable workflow it calls.** Only a workflow this one calls runs in this run, and that is
   the allow-listed one. Every other workflow runs in its own run, so its runtime token cannot place an artifact here
   (round 10's lead 5). It can cancel this run (M11-D; or the API, with `actions: write`) or delete the artifact, which
   fails closed. It can neither swap the artifact nor mint a credential.

## Re-run counts (step 4) against § "Fix pass 9"

`tmp/r11review/rerun/c10/` is a copy of `checker-r10/`'s drivers and static inputs, every self-path repointed
(`setup_rerun.bash`). It has a fresh `evidence/`, a read-only symlink `rerun/cascor-r3` for the proof's import, and the
lint replaced by `lint_copy_r11.bash`. The run is `rerun/rerun_all_r11.out`, 22:28:37Z to 22:38:31Z.

| item | fix pass 9 | round 11 |
|---|---|---|
| cascor's three (landing tree, `f5ed3017`, main `b5b28dc3`) | 3/3 each | 3/3 each |
| port-sim regenerated: variants; diff against fix pass 6's | 18 PASS, 7 FAIL; 0 lines | 18 PASS, 7 FAIL; 0 lines |
| the 15-row table | 15/15 | 15/15, identical to fix pass 9's table |
| pins re-derived (`rederive_pins_r10.py`) | 18/18 | 18/18 |
| earlier sets (`judge_all_r10.py`) | 0 moved, 0 findings | 0 moved, 0 findings (r5 24/24 … r8-O8 28/28) |
| round 9's cases | 32/32 | 32/32 |
| X8-1 to X8-8 | live FAIL, naive PASS; 0 unexpected | the same |
| N9-1 to N9-9 / C9-1 to C9-5 | FAIL (PASS under fix pass 7's) / PASS | the same; 0 unexpected |
| round 10's cases | O10-7, O10-8 PASS -> FAIL by design; 0 findings | the same |
| N10-1 to N10-16 / C10-1 to C10-3 | 7 changing, 1 TS-refused, 8 not executable; 0 unexpected | the same; every row identical to fix pass 9's |
| the proof | 432/432, 7 message changes | 432/432, the same 7 |
| round 2's 43 | 26 of 43; K1, K2 by design; R19; C1; 13 kept | the same; 0 other changes |
| fuzz, seed 9001 / 424242 | 0 differ / Node 7 | 0 differ / Node 7 (libyaml, yd53, yd16: 0) |
| typing differential | 0 divergences, 6 refused by the checker alone | the same |
| lint | 3 E203, B914 0 | 3 E203, B914 0, `--help` 0 (on copies) |

The brief's other expectations hold as well:
- `rederive_pins_r10.py` prints "ends with newline: False" for a file that does end in one (the inherited driver bug);
- the 43-case driver exits 1.

## The 15-simulation table (regenerated by round 2's probes; `rerun/c10/evidence/port_sim_table.md`)

All 15 PASS before and after:
- juniper-canopy `publish.yml`;
- juniper-data `publish.yml`, its `notify-consumers.yml` placed beside it;
- juniper-data-client `publish.yml`;
- juniper-cascor-client `publish.yml`;
- juniper-cascor-worker `publish.yml`;
- juniper-recurrence `publish-recurrence-app.yml`, `-client.yml`, `-model.yml`;
- juniper-ml `publish.yml` (faithful+ml-F2+lag), `publish-ci-tools.yml`, `publish-config-tools.yml` (reorder),
  `publish-doc-tools.yml` (reorder), `publish-model-core.yml`, `publish-observability.yml`,
  `publish-service-core.yml`.

Cascor's three PASS from the landing tree, from `f5ed3017` and from `main`.

## Step 2: the pins file

The file is unchanged: sha256 `d539f05f…`, 18 pins, 18 distinct keys, pure ASCII, ending in a newline.

**18 of 18 pins re-derive equal** with code of my own (`rederive_pins_r11.py`, `rederive_pins_r11.out`). It reads every
source with libyaml (`CSafeLoader`), another implementation than the checker's loader. For each pin it checks:
- the text equals the source's run string less one final newline;
- the sha256 is that text's;
- the package is the source's `PUBLISH_PACKAGE`;
- the workflow name is the source's;
- no install-job run step is left unpinned;
- the text holds one retry header and one lag error.

Cascor's three are checked against `f5ed3017`, the landing tree and `main`. Every simulation pin is checked against
fix pass 6's seed and against this round's regeneration. Fix pass 9's own driver, re-run, also reports 18/18.

## Step 6: over-strictness (`overstrict_r11.py`, `evidence/overstrict_r11.out`)

| id | harmless edit | checker | reason true? |
|---|---|---|---|
| O11-1 | `timeout-minutes: 30` on the build, TestPyPI, install and PyPI jobs | PASS | - |
| O11-2 | the environment mapping `{name, url}` on both publish jobs (one url an expression) | PASS | - |
| O11-3 | the PyPI upload step's keys reordered (`with`, `uses`, `name`), every value quoted | PASS | - |
| O11-4a/b/c | `verbose: True`, `attestations: TRUE`, `verbose: !!bool true` | PASS | - |
| O11-4d | `verbose: "true"` (a string) | FAIL | yes; harmless form refused (n11-c) |
| O11-4e | `verbose: yes` (text; the action reads it as verbose on) | FAIL | yes |
| O11-5 | a flow-style `with` on the PyPI upload | PASS | - |
| O11-6 | another comment after every `uses:` SHA | PASS | - |
| O11-7 | an extra job after the PyPI job | FAIL | yes (B10-2, by design) |
| O11-8 | juniper-data's allow-listed job, its keys reordered and quoted | PASS | - |
| O11-9 | the allow-listed job with `needs: [pypi]` | FAIL | yes; harmless form refused (n11-c) |
| O11-10 | `notify-consumers.yml` with CR LF line endings | FAIL | **no** (n11-a) |
| O11-11 | the whole template with CR LF line endings | PASS | - |
| O11-12 | the PyPI job's `needs` reordered | PASS | - |
| O11-13 | the allow-listed job with `permissions:` empty (null, the default token) | FAIL | yes (a real change) |

## Step 1: the delta, checks found sound

- **B10-1, the upload sets** (`upload_problems`, `:967-998`). The template's exact inputs and values, plus `verbose` and
  `attestations` as the boolean true, are a closed set: a case variant, an alias, an expression key, a key that is not
  text, a missing input and any other input are each refused.
  - The runner builds inputs case-insensitively (`OrdinalIgnoreCase`). Executed on .NET 8, it equates no non-ASCII
    look-alike with a declared input (`dotnet-probe/probe*.out`), so the exact set has no folding hole.
  - `verbose` adds twine's `--verbose` and `print-hash.py`. The minted token is masked
    (`oidc-exchange.py:396`, `::add-mask::`).
  - `attestations: true` is the action's default.
  - Claims verified: the five underscore aliases (`action.yml:15-74`); three ports add `attestations`; cascor's sub-package
    publishers, recurrence's three, juniper-ml's six sub-packages and data-client add `verbose`.
- **B10-2, the allow-list** (`extra_job_problems`, `:1001-1018`). The job is compared whole, as GitHub types it, with no
  bool, int or float values to confuse Python's `==`. Key order and quoting are admitted (O11-8). The called file is
  compared by sha256. An extra job of any other repository, file or id is refused.
- **B10-3, the per-job SHA sets** (`uses_problems`, `:947-964`; `template()`, `:891-912`). Every `uses` of the five
  jobs is read:
  - a non-string `uses`, a job-level `uses` (refused by the key sets), a docker, local or path ref, another owner, a
    tag or a short SHA are each refused;
  - the per-kind sets stop an action moving between jobs: no `upload-artifact` is admitted in a publish or install job;
  - the install job's widening to checkout and setup-python is harmless, because its checkout is held to one sparse file
    with `persist-credentials: false`, and the pinned scripts run from `$RUNNER_TEMP`;
  - the template check (40 lowercase hex, one ref per action) is enough for what it guards (n11-e is its message).
- **m10-a, the catch-all.** Every `Exception` from judging, labelling or printing fails that workflow alone (proof CLI5,
  R10-10, R10-11, N10-13). `SystemExit` is raised only before the loop. Two gaps remain: a hang (M11-B) and a lying
  display (M11-A).
- **n10-a and n10-b**: the messages are true of every form refused.
- **`document_problems`**: the expression-key and lone-surrogate rules are sound, and no publisher holds either.
- **The checker's printed PASS line** cannot carry a payload: on a PASS every printed env value equals a pin's package or
  its derived forms.

## Files written by this round (all under `tmp/r11review/`, except the directory mtime in "What this round did NOT do")

- **Drivers:**
  - `setup_rerun.bash`, `rerun/rerun_all_r11.bash`, `rerun/lint_copy_r11.bash`, `rerun/untouched_r11.bash`;
  - `survey_toplevel_r11.py`, `rederive_pins_r11.py`, `peek_concurrency_r11.bash`;
  - `mutants_r11.py`, `render_tmux_r11.bash`, `render_history_r11.bash`, `visible_r11.py`;
  - `m11_11_ceremony_r11.py`, `bomb_r11.py`, `overstrict_r11.py`, `fixcheck_r11.py`;
  - `dotnet-probe/` (`src/`, `run_probe*.bash`);
  - `rerun/c10/node/ts_names_r11.mjs`.
- **Evidence:** `evidence/*`, `rerun/rerun_all_r11.out`, `rerun/c10/evidence/*`, `mutants/`, `exec/`, `overstrict/`,
  `dotnet-probe/probe*.out`.
- **This report:** `ROUND11_REPORT.md`.
