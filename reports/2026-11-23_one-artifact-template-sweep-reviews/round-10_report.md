# Round-10 review report: fix pass 8 on the cross-repo port checker (`checker-r9`)

Reviewer: the round-10 fresh reviewer (a subagent of session `d935c226`), worktree `ethereal-munching-peacock`.
Brief: `tmp/sweep/ROUND10_BRIEF.md`. Ran 2026-11-24 15:05Z to 15:52Z (times from `date -u`). Every probe, driver and
output is under `tmp/r10review/` (evidence in `tmp/r10review/evidence/`).

Under review: the checker `util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256 `9cf16a2f…`, 1172 lines,
equal to `checker_r9_as_delivered.py`) and the pins file `util/ad-hoc/2026-11-24_publish_port_install_pins.json`
(`d539f05f…`, 552 lines, equal to `pins_r9_as_delivered.json`). Every frozen input hashed as the brief states, and
`sha256sum -c tmp/arc/sweep_scripts.sha256` reported 7 OK (`evidence/hashes.out`). Both files are unchanged at the end.

## What this round did NOT do

Every step (1 to 6) and every sub-step was done. These are the departures and limits, so the round's completeness can be
judged:

1. **Step 4's lint did not run pre-commit itself.** I ran each check juniper-ml's pre-commit applies to
   `util/ad-hoc/*.py` and `*.json` (trailing whitespace, final newline, AST, JSON, debug statements, private keys, the
   `/tmp` and home-path literals) plus flake8 and B914 on byte-identical **copies** (`rerun/lint_copy_r10.bash`), so that
   no fixer hook could rewrite the live files. Result: 3 E203, as fix pass 8 reported.
2. **GitHub itself was not available.** That covers its server-side parser, how it resolves `uses:` refs, its artifact
   service and its job scheduling. Instead:
   - GitHub's C# lineage was **read** at actions/runner `aea9aaa3`. That covers the server-side parser's port
     (`src/Sdk/WorkflowParser/Conversion/WorkflowTemplateConverter.cs`) and the runner's `PipelineTemplateConverter.cs`,
     `TemplateReader.cs`, `TemplateEvaluator.cs`, `ActionRunner.cs`, `CompositeActionHandler.cs`,
     `ContainerActionHandler.cs` and `DictionaryContextData.cs`. All are in `external/` or round 9's `external/`.
   - GitHub's TypeScript lineage was **run**: `@actions/workflow-parser` 0.3.61 and `@actions/expressions` 0.3.61,
     installed under `node/`. Their two schema-JSON imports were given `with { type: "json" }` for Node 24; no logic was
     changed.
   - R10-6 and R10-8 are **not executable** here.
   - R10-5 and R10-7 use a **stand-in** artifact store and stand-in indexes. The R10-5 race was not timed on GitHub.
3. The publish action's `oidc-exchange.py` ran with this host's `requests` 2.33.1 (the action pins 2.34.2) and
   `id` 1.6.1 (as pinned).
4. **One stray write outside `tmp/r10review/`.** My survey script, run without `-B`, created
   `tmp/sweep/checker-r9/__pycache__/checker_r9_as_delivered.cpython-314.pyc` at 15:14:58Z. I removed that file and its
   directory at 15:48Z. `checker-r9/` holds its 12 entries again; only its mtime changed. A `find -newer` over
   `tmp/sweep`, `tmp/r9review` and `util` now reports 0 files changed since the round began.

**Verdict: 3 BLOCKER, 0 MAJOR, 1 MINOR, 2 NIT.** The round is COMPLETE. Under the stopping rule it does **not** clear the
gate: fix pass 9, then round 11. All three blockers sit one level outside fix pass 8's key sets, beside or inside the jobs
that hold `id-token: write`. Fix pass 8's own new code held: the key sets, setup-python, the YAML 1.2 typing and the
ASCII and newline rules. Its only defects are m10-a (a claim) and n10-a (a message).

## Findings, most severe first

### B10-1 BLOCKER: the upload steps' `with` is read through four literal keys, so the PyPI job's OIDC token can be sent to any host

**Where:** checker `:1125-1137`. These lines read `skip-existing`/`skip_existing`, `attestations`, `packages-dir` and
`repository-url`, each by a literal key. No other key of the upload step, and no other key of its `with`, is ever read.
The comment at `:1043-1045` ("what a job that can mint runs is its template steps and the upload") is untrue as a bound.

**Scenario.** A port's PyPI upload step adds any one of these, and the checker passes it:
- `repository_url: https://<host>/legacy/` (R10-1). The pinned action (7245906f) declares `repository_url` as a
  deprecated alias, and its trampoline passes `repository-url: ${{ inputs.repository-url || inputs.repository_url }}`.
  `repository-url` has no default, so the alias wins whenever `repository-url` is empty, as it is in every PyPI job.
- `Repository-URL: …` (R10-2). GitHub builds step inputs in a case-insensitive map: `PipelineTemplateConverter.cs:174`,
  and the server lineage's `WorkflowTemplateConverter.cs:805`. The composite action's `inputs` context is looked up
  case-insensitively too (`CompositeActionHandler.cs:99-102`, `DictionaryContextData.cs:77`).
- `${{ 'repository-url' }}: …` (R10-3). `step-with` carries a context in both schemas, so the reader admits an
  expression key in that loose mapping (`TemplateReader.cs:313-328`). Early validation skips it (`WorkflowTemplateConverter.cs:818-822`),
  and the runner evaluates it before building the inputs (`TemplateEvaluator.cs:307-321`, `:404-408`).

What GitHub then runs: the action's `oidc-exchange.py:320-357` asks `<host>` for its audience, mints the PyPI job's
GitHub OIDC token for that audience, and POSTs it to `https://<host>/_/oidc/mint-token`.
- `<host>` answers audience `pypi`. So it receives a token that PyPI's own mint-token endpoint accepts for this
  repository's trusted publisher: the token's repository, workflow and `environment: pypi` claims are genuine.
- The result is an upload credential for the project, usable outside every check: TestPyPI, the install check and both
  JSON checks.
- The only trace on GitHub is R10-1's deprecation warning (`ActionRunner.cs:192`). R10-2 and R10-3 leave none.

**The same root, R10-4.** `Skip-Existing: true` on the TestPyPI upload and `${{ 'attestations' }}: false` on the PyPI
upload turn on `--skip-existing` and drop `--attestations`. The two checker rules that claim to refuse exactly that are
bypassed.

**Evidence** (`evidence/r10_mutants.out`, driver `r10_mutants.py`):
- R10-1 to R10-4: the checker PASSes each, and GitHub's TS parser reports no error.
- The driver builds the inputs as the runner does (case-insensitive, defaults merged, `ActionRunner.cs:207-217`). It
  then evaluates the action's own trampoline expressions with `@actions/expressions` (`node/inputs.mjs`). For R10-1, 2
  and 3 this gives `INPUT_REPOSITORY-URL='https://127.0.0.1:<port>/legacy/'`.
- Running the pinned `oidc-exchange.py`, unmodified, then logs:
  - `stand-in index chosen by the workflow: asked for its audience, answers 'pypi'`;
  - `stand-in token service: a token requested for audience 'pypi' with the job's request token (bearer present)`;
  - `stand-in index chosen by the workflow: RECEIVED the job's OIDC token (676 chars; aud='pypi', environment='pypi', …)`.
- Control C10-0, the template: `INPUT_REPOSITORY-URL='https://upload.pypi.org/legacy/'`.
- R10-4, from the action's own `twine-upload.sh` lines:
  - TestPyPI: `TWINE_EXTRA_ARGS=--attestations --verbose --disable-progress-bar --skip-existing`;
  - PyPI: `TWINE_EXTRA_ARGS=--verbose --disable-progress-bar`.

**Fix.** Hold each TestPyPI and PyPI upload step to exactly `{name, uses, with}`, and its `with` to an exact set of
literal keys, as cascor's own test does (`UPLOAD_INPUTS`):
- TestPyPI: `repository-url: https://test.pypi.org/legacy/` and `packages-dir: ${{ env.PUBLISH_DIST_DIR }}/`;
- PyPI: `packages-dir` alone;
- either may add `verbose: true` and `attestations: true`, the only additions in the 15 simulations
  (`evidence/survey_r10.out`).

This refuses the underscore aliases, case variants, expression keys, `password`/`user` and an upload-step `env`.
`candidate_rules_r10.py` (rule U) refuses R10-1 to R10-4 and R10-9, and admits cascor's three and all 15 simulations
(`evidence/candidate_rules_r10.out`).

### B10-2 BLOCKER: extra jobs are noted, never judged; one can replace `<PUBLISH_PACKAGE>-dist`, and fix pass 8's candidate rule does not close it

**Where:** checker `:908-910` (the note) and the docstring at `:212-215`. Contrast cascor's own test,
`src/tests/unit/test_publish_one_artifact.py:453`, which asserts `sorted(jobs) == [the five]`.

**Scenario R10-5.** An extra job builds the package itself, writes a SHA256SUMS that agrees with it, and runs
`actions/upload-artifact` with `name: ${{ env.PUBLISH_PACKAGE }}-dist` and `overwrite: true`.
- `upload-artifact.ts:68-69` (v7.0.2) deletes the build job's artifact, then uploads the new one.
  `download-artifact.ts:85-101` (v8.0.2) takes this run's artifact of that name.
- So both publish jobs download the extra job's files:
  - "Verify the dist against SHA256SUMS" compares the swapped dist with the swapped SHA256SUMS;
  - both JSON checks compare each index with the swapped SHA256SUMS;
  - the install check installs and imports the swapped wheel.

How the timing works on GitHub:
- The `testpypi` environment holds only a branch policy, with no reviewer and no wait timer (`gh api …/environments`,
  15:22Z). So the TestPyPI job starts as soon as `build` ends.
- An extra job with no `needs` can poll this run's artifact list, as the template's own reuse step does, and overwrite
  the moment the build's artifact appears.
- If the swap lands mid-download, the TestPyPI job fails. Its documented recovery, "Re-run failed jobs", then downloads
  the swapped artifact.
- The race was not timed on GitHub.

**R10-6.** The same swap through a reusable workflow (`uses: <owner>/<repo>/.github/workflows/x.yml@main`,
`secrets: inherit`). Its jobs are jobs of this run: an artifact upload is bound to the run named in the runtime token's
`scp` claim (`@actions/artifact` `util.ts:21-47`). The checker never reads that workflow's text, and `secrets: inherit`
also hands every repository secret to another repository's file at a mutable ref.

**R10-7.** An extra job *after* the PyPI job (`needs: pypi`, `if: always()`) leaves a 0.14.1 `<pkg>-dist` behind when
attempt 1's TestPyPI check fails on index lag. Then:
- "Re-run failed jobs" re-runs the TestPyPI job, which uploads 0.14.1;
- the install job installs the tag's 0.14.0 and passes;
- the PyPI job publishes 0.14.1, which no install check ran and the build job never made.

So fix pass 8's candidate rule ("every extra job needs the PyPI job …") is not sufficient. Its other clause, "or holds no
`needs` on the build or TestPyPI jobs", is exactly R10-5's polling job.

**Evidence** (`evidence/r10_mutants.out`). The template's own scripts (Record SHA256SUMS, Verify the dist, both JSON
checks) ran unchanged under `python3`, and the pinned install script ran under `bash -e` with a real pip in a fresh venv.
- R10-5: TestPyPI and PyPI both hold the extra job's two files, and the wheel PyPI holds prints "RUNS CODE THE BUILD JOB
  NEVER MADE". Every check returned rc 0, and the install check's output is `RUNS CODE THE BUILD JOB NEVER MADE |
  TestPyPI OK: v0.14.0`.
- R10-7: PyPI holds only `juniper_cascor-0.14.1-*`. The install check printed "the wheel the build job made | TestPyPI
  OK: v0.14.0".
- Control C10-0: the build job's files reach both indexes.

**Fix.**
- Refuse every job outside the chain's five except an exact, per-repository allow-list. Today it has one entry:
  juniper-data's `notify-consumers`, exactly as its port holds it (`needs: pypi`, `permissions: {}`,
  `uses: ./.github/workflows/notify-consumers.yml`, its `with` and its one named secret).
- Pin the called file by sha256, read and compared as the install scripts are. Today it holds run steps only, under
  `permissions: {}` (fetched read-only: blob `ab0cade2…`, 11039 bytes, `external/juniper-data-notify-consumers.yml`).
- Refuse `secrets: inherit` and any reusable workflow outside the repository.

`candidate_rules_r10.py` (rule X) refuses R10-5, R10-6 and R10-7 and admits every simulation.

For the template's owner (cascor's tree, outside this checker): either of these would close both swaps at the template,
whatever a port adds:
- the publish jobs download the build job's `artifact-id` (a build-job output) rather than the artifact's name;
- the dist check refuses a SHA256SUMS whose version is not the tag's.

### B10-3 BLOCKER (item 23's documented residual; it needs an owner ruling): a dropped `@ref` lets the credential-holding jobs run an action at a commit that exists only in a fork

**Where:** `by_action` `:471-477`, `step_list` `:484-486`, the prefix tests in `uploads`/`checkouts` `:494-499`, the
docstring at `:35` and `:212-213`, and the comment at `:1045`.

**Scenario.** The PyPI job writes `uses: pypa/gh-action-pypi-publish@dc25d13879709b53eaba744662c7b08ff2aff167`, or
`actions/download-artifact@main`, and the checker passes it (R10-8).
- `dc25d138…` is a commit of the fork `ossprey/gh-action-pypi-publish`, which has diverged from upstream by 3 commits.
- GitHub's API serves that commit under the **upstream** name, with the fork's own `action.yml` (blob `dc414d52`,
  7032 bytes, against upstream's `f0b2c506`, 6501 bytes; `evidence/imposter_probe.out`, read-only GETs, 15:31Z).
- Not executed here: whether `uses:` resolution follows the same path. Public reports (the "imposter commits" write-up,
  2023) say it does; I have not verified that.
- If it does, the fork's code runs in a job holding `id-token: write`.

**Fix.** In the TestPyPI, PyPI and republish jobs at least, require each action's ref to equal a pinned SHA for that
action. That is the owner's "Pin exact scripts" applied to actions.
- Today the pin would be the template's SHA for each action. Every simulation and every real workflow uses exactly
  those (`evidence/survey_r10.out`, "action refs seen").
- The pinned SHAs would sit beside the install pins and move through review when Dependabot bumps one.
- `candidate_rules_r10.py` (rule A) refuses R10-8 and admits every simulation.
- Alternatively, the owner accepts the residual in writing. The docstring and `:1043-1045` must then say that these jobs
  run whatever code their actions' refs name.

### m10-a MINOR: n9-c's claim is untrue, because a workflow can still stop the run after `main()`'s catch-all

**Where:** `main()` `:1157-1160`, where the label's `load` catches only `OSError`, `UnicodeDecodeError`, `YAMLError`,
`AttributeError` and `TypeError`; and `:1163-1165`, the prints. The claims are in the docstring at `:193-194` and the
comment at `:1161`.

**Scenario.**
- R10-10, a file holding 1000 nested flow sequences: `check()`'s `RecursionError` is caught, and then the label's
  `load()` raises it again, uncaught.
- R10-11, `PUBLISH_PACKAGE: "juniper-cascor\ud800"`: the file loads with a lone surrogate, and `print` raises
  `UnicodeEncodeError`.

In both cases the run ends in a traceback with exit 1. No verdict line is printed for that workflow, the next workflow on
the command line (the template) is never judged, and no summary line is printed. It fails closed, so no PASS is hidden.

**Evidence:** `evidence/r10_shapes_overstrict.out`.

**Fix:**
- compute the label inside a `try` that catches `Exception`;
- print with `errors="backslashreplace"` (`sys.stdout.reconfigure`);
- refuse a lone surrogate in any loaded string;
- optionally, cap nesting depth before parsing.

### n10-a NIT: `runs-on: [ubuntu-latest]` is refused with an untrue reason

**Where:** `:927-928`, fix pass 8's new rule. The message reads: "a job holding id-token: write runs on ubuntu-latest,
never on a runner the repository chooses". A one-label list chooses the same runner (O10-11). No port writes it.

**Fix:** reword it: "runs-on is the string ubuntu-latest, as the template writes it".

### n10-b NIT: `persist-credentials: "false"` is refused with an untrue reason

**Where:** `:806-808`, fix pass 4's rule. The message says the checkout "keeps a credential in the workspace". In a
string-typed position the reader turns a boolean into its text (`TemplateReader.cs:453-462`), and the runner hands an
action every input as a string (`ConvertToStepInputs`), so `"false"` and `false` reach checkout as the same input
(O10-13). No port writes it quoted.

**Fix:** reword it, or compare the value as the runner hands it to the action.

### Observations (not checker findings)

- **O-1 (the template, outside this checker):** no publish job ties SHA256SUMS' version to the release tag, and the
  install check tests only the tag's version. That is what lets R10-7 publish 0.14.1 from a v0.14.0 run.
- **O-2:** GitHub's TS lineage accepts an expression key at the **step** level (`${{ 'continue-on-error' }}: true`, the
  `K-step-expression-key` case), and the checker passes it. GitHub's C# lineage refuses it, so it is not a bypass on
  GitHub:
  - its `regular-step` and `run-step` carry no context in either schema;
  - `WorkflowTemplateConverter.cs:1665` and `PipelineTemplateConverter.cs:469` assert that each step key is a string.

  Cheap hardening anyway: refuse a key holding `${{` wherever the checker reads keys.
- **O-3:** in the typing differential against the TS lineage (`evidence/typing_keys_r10.out`), 71 of 75 documents
  agree. The checker refuses 3 that GitHub's C# runner also refuses: `! 90`, `!!int '90'` and a redefined `!!` handle
  (`YamlObjectReader.cs:39-72`). `!!float 90` is 90.0 to the checker and to the C# `MatchFloat`, and the text "90" only
  to the TS lineage.

## Bypass-mutant table (step 5: 11 new cases plus a control; `evidence/r10_mutants.out`, `evidence/r10_shapes_overstrict.out`)

| id | target | checker | executed outcome |
|---|---|---|---|
| C10-0 | control: the template | PASS | the build job's files reach both indexes; trusted publishing exchanges with upload.pypi.org |
| R10-1 | PyPI upload `repository_url:` (the action's deprecated alias) | **PASS** | the PyPI job's OIDC token (aud `pypi`) POSTed to the named host (B10-1) |
| R10-2 | PyPI upload `Repository-URL:` | **PASS** | the same (B10-1) |
| R10-3 | PyPI upload `${{ 'repository-url' }}:` (expression key) | **PASS** | the same (B10-1) |
| R10-4 | TestPyPI `Skip-Existing: true`; PyPI `${{ 'attestations' }}: false` | **PASS** | twine `--skip-existing` on; `--attestations` off (B10-1) |
| R10-5 | extra job, `needs: build`, upload-artifact `overwrite: true` | **PASS** (note) | both indexes hold files the build never made; every check rc 0 (B10-2) |
| R10-6 | extra job: a remote reusable workflow `@main`, `secrets: inherit` | **PASS** (note) | not executable: another file; R10-5's mechanism (B10-2) |
| R10-7 | extra job after PyPI (`needs: pypi`, `if: always()`), version 0.14.1 | **PASS** (note) | after "Re-run failed jobs", PyPI holds 0.14.1, never install-checked (B10-2) |
| R10-8 | PyPI job: `download-artifact@main`, the upload at a fork-only commit | **PASS** | not executable; GitHub serves the fork commit under the upstream name (B10-3) |
| R10-9 | control: upload-step `env` with an expression key `${{ 'PYTHONPATH' }}` | FAIL | refused (identifier rule) |
| R10-10 | 1000 nested flow sequences, then the template | exit 1, traceback | the template never judged (m10-a) |
| R10-11 | `PUBLISH_PACKAGE` holding `\ud800`, then the template | exit 1, traceback | the template never judged (m10-a) |

## What each lead came to

1. **Extra jobs:** B10-2. R10-5 and R10-7 were executed; R10-6 was judged only, since it is not executable here.
2. **`secrets: inherit`:** R10-6 passes. Its jobs can swap the artifact, as R10-5's can, and it hands every repository
   secret to an unseen file. Rule X closes it.
3. **The upload steps' own `with` and `env`:** `with` is B10-1. For `env` no path was found:
   - the upload step's literal env keys go through the F4, R5-F4 and identifier rules, and an expression key fails the
     identifier rule (R10-9);
   - GitHub refuses a case-variant step key such as `Env:`, by the same Ordinal property match that refused
     `Continue-On-Error` in the `K-step-case-variant` case ("Unexpected value");
   - an `INPUT_*` env key cannot supply an input, because every declared input is filled by the runner
     (`ActionRunner.cs:207-217`);
   - `ACTIONS_ID_TOKEN_REQUEST_*` are set by the handler after the step's env (`ContainerActionHandler.cs:234-235`,
     `ScriptHandler.cs:317-318`);
   - `TWINE_USERNAME`, `TWINE_PASSWORD` and `TWINE_REPOSITORY_URL` are overwritten on `twine-upload.sh`'s exec line.

   B10-1's fix refuses an upload `env` outright in any case; no port has one.
4. **Dropped refs:** B10-3.
5. **Another workflow on the same release, or `workflow_run`:** its runtime token names its own run (`util.ts:21-47`),
   so it cannot place an artifact into the publish run. With `actions: write` it can delete the artifact, after which
   the publish jobs fail closed, or re-run or cancel the publish run. That is not a bypass on its own. Not executed.
6. **What an earlier attempt leaves behind:** R10-7. The artifact an extra job left in attempt 1 is what "Re-run failed
   jobs" publishes. On "Re-run all jobs", the build job's reuse step likewise accepts any unexpired `<pkg>-dist` in the
   run.

## Re-run counts (step 4) against § "Fix pass 8"

`rerun/c9/` is a copy of `checker-r9/` with its own path repointed (`rerun/repoint_files.txt`), a fresh `evidence/`, and
`TMPDIR` under `tmp/r10review/tmpdir`. The live checker and pins file were used read-only, and their hashes are equal
before and after (`rerun/frozen_*.sha256`). Step 4a first failed in the copy, because the generated proof imports
`HERE.parent / "cascor-r3"`. A read-only symlink `rerun/cascor-r3` fixed that, and 4a was re-run alone
(`rerun/run_proof_only_r10.bash`); it wrote 0 files under `tmp/sweep/cascor-r3`.

| item | fix pass 8 | round 10 |
|---|---|---|
| cascor's three (landing tree, `f5ed3017`, main as fix pass 8 fetched it) | 3/3 each | 3/3 each |
| cascor main re-fetched by me, 15:28:43Z (`b5b28dc3`, byte-equal to the landing tree) | - | 3/3 (`evidence/fetch_cascor_main_r10.out`) |
| port-sim regenerated: variants; diff against fix pass 6's | 19 PASS, 6 FAIL; 0 lines | 19 PASS, 6 FAIL; 0 lines |
| the 15-row table | 15/15 | 15/15 |
| pins re-derived (`rederive_pins_r9.py`) | 18/18 | 18/18 |
| earlier sets (`judge_all_r9.py`) | 0 moved, 0 findings | 0 moved, 0 findings (r5 24/24 … r8-O8 28/28) |
| round 9's cases | 32/32 | 32/32 |
| X8-1 to X8-8 | live FAIL, naive PASS | the same; 0 unexpected |
| N9-1 to N9-9 / C9-1 to C9-5 | FAIL (PASS under fix pass 7's) / PASS | the same; 0 unexpected |
| the proof | 396/396 | 396/396 |
| round 2's 43 | 29/43; C1 by design; 13 FAIL kept | the same; 0 other changes |
| fuzz, seed 9001 / seed 424242 | 0 differ / Node 7 | 0 differ / Node 7 (libyaml, yd53, yd16: 0) |
| typing differential | 0 divergences, 6 refused by the checker alone | the same |
| lint | 3 E203 | 3 E203; B914 0 (on copies; see "What this round did NOT do") |

## The 15-simulation table (`rerun/c9/evidence/port_sim_table.md`; regenerated by round 2's probes)

All 15 PASS:
- juniper-canopy `publish.yml`;
- juniper-data `publish.yml`;
- juniper-data-client `publish.yml`;
- juniper-cascor-client `publish.yml`;
- juniper-cascor-worker `publish.yml`;
- juniper-recurrence `publish-recurrence-app.yml`, `-client.yml`, `-model.yml`;
- juniper-ml `publish.yml` (faithful+ml-F2+lag), `publish-ci-tools.yml`, `publish-config-tools.yml` (reorder),
  `publish-doc-tools.yml` (reorder), `publish-model-core.yml`, `publish-observability.yml`, `publish-service-core.yml`.

Cascor's three PASS from the landing tree, from `f5ed3017` and from `main`.

## Step 2: the pins file

- **18 of 18 pins re-derive equal from their stated sources** with code of my own (`rederive_pins_r10.py`,
  `evidence/rederive_pins_r10.out`). It reads the sources with GitHub's TS parser, not PyYAML. Each pin passes: its text
  equals the source's run text less one final newline, its sha256 is that text's, its package is the source's
  `PUBLISH_PACKAGE`, no line holds a newline and the last is not empty. Cascor's three were checked at `f5ed3017`, at
  main `b5b28dc3` and in the landing tree.
- **Only `about` changed** (`pins_r8_to_r9.diff`, hash as stated).
- **Each statement in `about` is true:**
  - the pin key is (repo, workflow file name, step name in the job named "Verify the TestPyPI install");
  - the package must be `PUBLISH_PACKAGE`;
  - the text is the lines joined by newlines, with no final newline;
  - a port's step equals its pin apart from one final newline, and more than one is refused;
  - a sha256 mismatch is refused;
  - the file is ASCII-escaped, and a non-ASCII pins file is refused.
- The file is pure ASCII, ends in a newline, and holds exactly `format`, `about` and `pins`.

## Step 1: the delta, checks found sound

- **The key sets** (`:305-313`) equal cascor's test's `BUILD_JOB_KEYS`, `PUBLISH_JOB_KEYS`, `INSTALL_JOB_KEYS`,
  `REPUBLISH_JOB_KEYS` and `OPTIONAL_JOB_KEYS` (`test_publish_one_artifact.py:178-190`).
  - No key reaches GitHub under a name the set does not see. GitHub matches well-known keys Ordinal and refuses keys equal
    but for case (`TemplateReader.cs:182`, `:214-218`; K-job-case-variant: "Unexpected value 'Container'"). An alias or
    tag resolves to the key the set reads (N9-1). An expression key on a job is refused by the key set.
  - `timeout-minutes` stops a job, which then fails closed.
  - A sub-package's `defaults` is compared whole.
  - The environment mapping is held to `{name, url}`, the two keys `job-environment-mapping` defines; the `url` type
    excludes secrets.
- **setup-python:** with `python-version` alone, the mirror is the action's default
  (`raw.githubusercontent.com/actions/python-versions`). A fork or a sub-path action is refused in the install job by
  `INSTALL_ACTIONS`. A step `env: INPUT_CACHE` cannot supply an input, because every declared input is filled.
- **`GITHUB_SCALARS`** agree with the C# runner: 0 divergences in fix pass 8's differential, re-run here, and C#
  `MatchFloat` accepts `90`. Tags follow `YamlObjectReader.cs:39-72`. The merge key is refused by its text. A document
  that is not a mapping is refused.
- **The rest of the delta:**
  - `file_problems`' message is true;
  - the ASCII rule holds (P9a and P9b refused);
  - the pins file a mismatch names is the one loaded;
  - a script ending in more than one newline is refused (C9a, C9b, N9-8);
  - `shape_problems` names the shapes it refuses;
  - the catch-all never turns a FAIL into a PASS (but see m10-a).

## Step 6: over-strictness (`evidence/r10_shapes_overstrict.out`)

| id | harmless edit | checker | GitHub's TS lineage | reason true? |
|---|---|---|---|---|
| O10-1 | `timeout-minutes: 30` on the build, TestPyPI, install and PyPI jobs | PASS | accepts | - |
| O10-2 | environment as a mapping (`{name}`; `{name, url: ${{ format(…) }}}`) | PASS | accepts | - |
| O10-3 | the PyPI job's keys reordered and quoted | PASS | accepts | - |
| O10-4 | `runs-on: 'ubuntu-latest'` on all five jobs | PASS | accepts | - |
| O10-5 | `python-version: '3.12'` (single-quoted) | PASS | accepts | - |
| O10-6 | `!!str` on the PyPI job's name, runs-on and environment | PASS | accepts | - |
| O10-7 | an extra job after the PyPI job (a run step) | PASS (note) | accepts | - (closed by rule X unless allow-listed) |
| O10-8 | upload `verbose: true`, `print-hash: true` | PASS | accepts | - (rule U as proposed would refuse `print-hash`; no port uses it) |
| O10-9 | `needs: [build]` on the TestPyPI job | PASS | accepts | - |
| O10-10 | `retention-days: +90` | PASS | accepts | - |
| O10-11 | `runs-on: [ubuntu-latest]` on the PyPI job | FAIL | accepts | **no** (n10-a) |
| O10-12 | `timeout-minutes` on the republish job | FAIL | accepts | yes (by design: compared whole) |
| O10-13 | canopy's install checkout `persist-credentials: "false"` | FAIL | accepts | **no** (n10-b) |
| O10-14 | recurrence-model's build `defaults` with the directory quoted | PASS | accepts | - |

## Files written by this round (all under `tmp/r10review/`)

- **Drivers:**
  - `hashes.bash`, `survey_r10.py`, `r10_mutants.py`, `r10_shapes_overstrict.py`;
  - `rederive_pins_r10.py`, `typing_keys_r10.py`, `candidate_rules_r10.py`;
  - `imposter_probe.bash`, `fetch_cascor_main_r10.bash`, `debug_oidc.py`;
  - `node/tsparse.mjs`, `node/inputs.mjs`, `node/install_steps.mjs`, `node/typing_probe.mjs`;
  - `rerun/run_rerun_r10.bash`, `rerun/rerun_all_r10.bash`, `rerun/lint_copy_r10.bash`,
    `rerun/run_proof_only_r10.bash`.
- **Evidence:** `evidence/*.out`, `rerun/c9/evidence/*`, `mutants/`, `exec/`.
- **Fetched (read-only GETs):**
  - `external/` (the publish action's `oidc-exchange.py`, `create-docker-action.py`, `attestations.py` and requirements
    at 7245906f; the runner sources at `aea9aaa3`; upload-artifact and download-artifact sources at their pinned SHAs;
    the toolkit artifact `util.ts`; juniper-data's `notify-consumers.yml`);
  - `cascor-main-r10/`.
- **This report:** `ROUND10_REPORT.md`.
