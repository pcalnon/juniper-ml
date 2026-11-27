# Round-9 review: fix pass 7 (checker-r8, the owner's exact-pins ruling)

Reviewer: a fresh general-purpose agent in worktree `ethereal-munching-peacock`, from 2026-11-24 13:17Z to about 14:05Z
(times from `date -u`). Brief: `$W/tmp/sweep/ROUND9_BRIEF.md`. Where this report says `$W` it means
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`, and `$R` means
`$W/tmp/r9review`. Every output is under `$R`. No existing file under `$W/tmp/` or `$W/util/` was modified. The live
checker and pins file hash the same before and after every run (`$R/evidence/live_hashes_*_rerun.txt`). The only GitHub
calls were read-only `gh api` GETs.

## What this round did NOT do

Steps 1 to 6 and every sub-step the brief lists were done, so the round is **COMPLETE**. The limits below do not
leave any required sub-step undone:

- **GitHub's own server-side workflow parser was not run.** It is not available. What I ran instead is its
  open-source lineage:
  - actions/runner's `WorkflowParser`, read at `aea9aaa3`: `YamlObjectReader.cs`, `TemplateReader.cs`, the workflow
    schema and `ScriptHandler.cs`, all saved in `$R/external/`;
  - YamlDotNet **5.3.0**, the version actions/runner's `src/Sdk/Sdk.csproj` references, built and run here;
  - YamlDotNet **16.3.0**, libyaml (through PyYAML's C loader) and Node `yaml` 2.8.1, which is YAML 1.2.

  .NET 8 and the npm packages are installed under `$R/parsers/`, with every home and cache redirected there.
- **Three effects that need GitHub's runner were executed with local stand-ins, not on GitHub:**
  - the service containers of M9-1 and M9-14;
  - the interpreter that setup-python installs from a `mirror` (M9-2);
  - the job container (M9-13).

  In each case the mechanism is quoted from GitHub's source or schema, which I fetched. M9-15 shares M9-13's mechanism
  and was not run separately. M9-16 (a self-hosted runner) cannot be executed here.
- **Five extra mutants were not run to an outcome, beyond the required eight:**
  - M9-4: what GitHub does with the string default `"no"` for a boolean dispatch input is not verifiable here;
  - M9-5 (`cache: pip`): no outcome change could be shown;
  - M9-6 (`update-environment: false`): expected to fail closed;
  - M9-15 and M9-16, as above.

  Each is labelled so in the mutant table.
- **Step 4 needed one repair in my copy.** My copy of fix pass 7's tools first failed step 5b (`FileNotFoundError` for
  `../cascor-r3/checker_proof_r3.py`). The proof imports that file by a path relative to its own folder, and my copy
  had moved the proof. I copied that one file beside the copy, byte-identical (sha256 `63887250…`), and the proof then
  ran: 349 of 349.

## Findings, most severe first

| # | Severity | Short name | New in fix pass 7? |
|---|---|---|---|
| B9-1 | **BLOCKER** | TestPyPI and PyPI jobs (`id-token: write`) admit `container`, `services` and any `runs-on` | no (pre-existing; never covered) |
| M9-A | **MAJOR** | install job admits `services` | no (pre-existing) |
| M9-B | **MAJOR** | install job's setup-python `with:` unjudged: `mirror` + `check-latest` choose the interpreter that runs the pin | no (pre-existing; its residual note understates it) |
| M9-C | **MAJOR** | YAML 1.1 implicit typing (PyYAML) against GitHub's YAML 1.2 core: `retention-days: 1:30` is 90 to the checker, 1 day on GitHub | no (the docstring's new "known differences are refused" claim does not hold for it) |
| m9-a | MINOR | chomping: `|+` is not always "the same script" to bash (final unterminated here-document) | yes |
| m9-b | MINOR | pins loader does not enforce the ASCII-escaped form the docstring promises | yes |
| n9-a | NIT | X8-2 and X8-3 checked against GitHub's own parser: the wording of two messages, and two harmless over-strict refusals | yes |
| n9-b | NIT | the mismatch message names the default pins file under `--pins` | yes |
| n9-c | NIT | a step that is not a mapping crashes the checker (traceback; fails closed) | no |

Under the stopping rule, B9-1, M9-A, M9-B and M9-C require fix pass 8 and another review. **None of the four is in fix
pass 7's interdiff.** All four are the ruling's class, a gap between what the checker compares and what the runner
executes, and each sits one level outside the install script:
- B9-1, M9-A and M9-B: *where and with what* the compared text runs;
- M9-C: *how a compared value is typed*.

### B9-1 (BLOCKER): the jobs holding `id-token: write` admit `container`, `services` and any `runs-on`

- **Where.** `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`:
  - `check()` lines 850-864 (TestPyPI and PyPI jobs) and 824-844 (chain, environment, minting, `if`,
    `continue-on-error`) hold some of those jobs' keys and never look at `container`, `services` or `runs-on`;
  - the comment at line 830 claims "the job that can mint runs nothing but the template and the upload";
  - for comparison, the build job refuses `container` and `services` (line 776), the install job refuses `container`
    (line 637), and the republish job is compared whole.
- **Scenario.** A port adds `container: <image of its choosing>` to the PyPI job. Every run step of that job then runs
  inside the image, among them the template's `shell: python3 {0}` checks ("Verify the dist against SHA256SUMS",
  "Verify TestPyPI still serves exactly these files", "Verify PyPI serves exactly these files"). The runner's
  `ScriptHandler.cs` says a script "is written to local path (ie host) but executed relative to the StepHost, which may
  be a container". The image's `python3` can report every check as passed and put files of its own in the dist, and
  the upload step, which holds the OIDC credential, sends them to PyPI. PyPI files are immutable.

  With `services:` instead, the template checks run on the true dist. A service container then rewrites the dist before
  the upload reads it: it can bind-mount the work tree (`volumes`, documented as "bind mounts on the host"), set its own
  `entrypoint`/`command` (GitHub's schema, `service-container-mapping`) and use `--pid=host`. Because the publish action's
  files are downloaded at job set-up, before services start, a mounted service can also rewrite those files,
  deterministically. `runs-on: [self-hosted, …]` moves the whole job to a machine the repository chooses. TestPyPI's job
  is open the same way.
- **Evidence.** `$R/mutants/build_mutants3.py` → `$R/evidence/mutants_part3.md`:
  ```
  | M9-13 | PyPI job: container (the template's python3 checks run in a port-chosen image) | PASS |
  | M9-14 | PyPI job: services (… the work tree bind-mounted, host pid namespace) | PASS |
  | M9-15 | TestPyPI job: container (string form) | PASS |
  | M9-16 | PyPI job: runs-on a self-hosted runner | PASS |
  ```
  Executed with `$R/mutants/exec_part3.py` → `$R/evidence/exec_part3.out`. The template's own verify step, read from the
  mutant by the checker's loader and run as `python3 <file>`:
  ```
  control: the runner's python3, a dist other than SHA256SUMS records -> verify step rc 1
  M9-13: verify step rc 0: OK (the image says so); the upload would then send: [… 'replaced by the image' …]
  M9-14: verify step (runner's python3) rc 0 … ; the upload step then reads and sends: [… 'swapped by the service' …]
         (the same check run again now: rc 1; the post-upload PyPI check would see it only after PyPI took the files)
  ```
- **Fix.** Hold each job of the chain to an exact key set, as the republish job already is:
  - TestPyPI and PyPI: `set(job) == {name, needs, runs-on, environment, permissions, steps}` (the template's keys), and
    `runs-on == "ubuntu-latest"`;
  - the install job: `{name, needs, runs-on, permissions, steps}`, which also closes M9-A;
  - the build job: its template keys, with `defaults` refused or limited.

  Also fix the line 830 comment, and add M9-13 to M9-16 to the proof.

### M9-A (MAJOR): the install job admits `services`

- **Where.** `check_install_job` lines 619-668. It refuses `defaults`, `env` and `container` (lines 633-638) but not
  `services`. The module docstring (lines 47-49) lists the install job's rules and does not mention services.
- **Scenario.** A service container starts before the job's first step; the runner waits for its health check. It can
  bind-mount `/home/runner` and run its own `command`, writing `~/.config/pip/pip.conf` with
  `find-links = https://…`. pip merges `find-links` from its config with the pinned command line's `--index-url`, so
  the pinned, byte-equal script installs a wheel that never came from TestPyPI, imports it, and passes. With
  `/opt/hostedtoolcache` mounted, a `.pth` file runs code at every `python` and `pip` start.
- **Evidence.** M9-1 PASSES the live checker (`$R/evidence/mutants_first.md`). Executed with
  `$R/mutants/exec_install.py` → `$R/evidence/exec_install.out`, pin 1's own text under `bash -e`, a real pip 26.2.1 in
  a venv built here, TestPyPI unreachable, and `sleep` a stand-in. The only difference between the two runs is the
  config file the service writes:
  ```
  === control: rc 1   … ::error::juniper-cascor 0.14.0 is not installable from TestPyPI after 5 tries …
  === M9-1: rc 0      Looking in links: …/service-wheels
                      Successfully installed juniper-cascor-0.14.0
                      IMPORTED A WHEEL THAT DID NOT COME FROM TESTPYPI
                      TestPyPI OK: v0.14.0
  ```
- **Fix.** The install-job key allow-list in B9-1's fix.

### M9-B (MAJOR): the install job's setup-python `with:` is unjudged, so the port chooses the interpreter that runs the pin

- **Where.** `check_install_job` lines 660-661 admit `actions/setup-python` by name, and nothing reads its `with:`. The
  docstring's "What this cannot see" (line 169) calls this "setup-python's inputs (`cache` restores a pip cache)".
- **Scenario.** At the template's own setup-python SHA `6d4fd22b` ("v7.1.0"), `action.yml` (lines 21-26) has a `mirror`
  input, "Base URL for downloading Python distributions". In `src/find-python.ts`, lines 82-121, `check-latest: true`
  resolves the version against the mirror's manifest, and a release not in the tool cache is installed. In
  `src/install-python.ts`, lines 431-452 download `release.files[0].download_url` (any URL the manifest names) and
  line 427 runs `bash ./setup.sh` from it. Lines 152-174 of `find-python.ts` then export `LD_LIBRARY_PATH` and add the
  install directory to PATH (`core.addPath`) for every later step.

  So `with: {python-version: "3.12", check-latest: true, mirror: https://…}` runs a script of the port's choosing in the
  install job and puts its `pip` and `python` first under the pinned step. The pin stays byte-equal, and what it runs is
  not what its review read.
- **Evidence.**
  - M9-2 PASSES the live checker. Sources: `$R/external/setup-python-6d4fd22b-*`.
  - Executed (`$R/evidence/exec_install.out`) with the mirror's interpreter stood in for, first on PATH:
    `=== M9-2: rc 0  TestPyPI OK: v0.14.0`, its log `mirror pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==0.14.0`.
    The control is rc 1.
  - M9-5 (`cache: pip`) and M9-6 (`update-environment: false`) also PASS, but no outcome change was shown for them (see
    the mutant table).
- **Fix.** In the install job, admit setup-python only with `with == {"python-version": <a version string>}`, at most
  once and before the first run step, or require it to equal the template's install-job step by action name. Refuse
  `mirror`, `mirror-token`, `check-latest`, `cache`, `cache-dependency-path`, `update-environment`, `pip-version`,
  `python-version-file`, `token`, `architecture`, `freethreaded` and `allow-prereleases`. Then correct the line-169
  residual text.

### M9-C (MAJOR): YAML 1.1 implicit typing against GitHub's YAML 1.2 core schema

- **Where.**
  - `load_text`, lines 306-314: `UniqueKeyLoader` is a `SafeLoader`, so it keeps PyYAML's YAML 1.1 resolvers (`yes`,
    `no`, `on`, `off`, `0NNN` octal, `1:30` base 60, `0b…`, `_` digit separators, timestamps).
  - The checker compares the typed values: the template-step identity (lines 867-887), `retention-days` (lines 821-823,
    against `RETENTION_DAYS = 90`), the dispatch default, and `persist-credentials is not False`.
  - GitHub reads plain scalars with YAML 1.2 core rules. In actions/runner's `YamlObjectReader.cs`, `MatchInteger`
    (lines 618-700) matches only `[0-9]+`, `[-+][0-9]+`, `0x…` and `0o…`, and every `with:` value reaches the action as
    a string (schema `step-with`: `loose-value-type: string`).
  - The docstring (lines 118-125) says "Where the two are known to differ, the file is refused". This difference is
    known and is not refused.
- **Scenario.** `retention-days: 1:30` in the build job's "Upload dist artifacts" step (a template step). PyYAML reads
  90, so the template-identity check and the retention rule both pass. GitHub hands upload-artifact the string `"1:30"`,
  and its `src/upload/input-helper.ts:39` (`cf430e03`) runs `parseInt("1:30") = 1`, a one-day retention. The template's
  own comment (`publish.yml` lines 157-159) says why 90 days is load-bearing: the PyPI job downloads the artifact only
  after the `pypi` gate is approved, "which may wait 30 days … An artifact that expired first would strand the release,
  because a rebuild cannot reproduce the files TestPyPI already holds".
- **Evidence.** M9-3, M9-3b and M9-4 PASS the live checker (`$R/evidence/mutants_first.md`). Executed
  (`$R/mutants/exec_part2.py` → `$R/evidence/exec_part2.out`):
  ```
  M9-3:  the checker (PyYAML) reads 90; YamlDotNet 5.3.0 delivers {"value": "1:30", "style": "Plain"}; GitHub's core-schema match: string '1:30'; node yaml: "1:30"
         upload-artifact … parseInt('1:30') = 1
  M9-3b: the checker reads 90; YamlDotNet "0132"; GitHub's core-schema match: number 132; parseInt('0132') = 132
  M9-4:  the checker reads False; YamlDotNet "no"; GitHub: string 'no'
  ```
  `attestations: yes` and `persist-credentials: no` are not divergences in outcome. pypi-publish tests
  `"${INPUT_ATTESTATIONS}" != "false"` (`twine-upload.sh:102`), and checkout reads anything but TRUE as false.
  `cancel-in-progress: no` fails safe: GitHub's `TemplateReader.Validate` refuses a string where its schema says
  `boolean`.
- **Fix.** Resolve plain scalars as GitHub does. A `SafeLoader` subclass whose implicit resolvers are exactly YAML 1.2
  core would do it: null (`~`, `null`, `Null`, `NULL`, empty), `true`/`True`/`TRUE`/`false`/`False`/`FALSE`, the
  integer forms above, and core floats, with everything else a string. `on` then needs no restoring, and `1:30`, `0132`
  (132) and `no` all fail their comparisons. The alternative is to refuse any plain scalar whose YAML 1.1 and YAML 1.2
  core readings differ. Neither changes a verdict on cascor's three or the 15 simulations: their only typed leaves are
  `90` and `false`, which both readings agree on.

### m9-a (MINOR): `|`, `|-` and `|+` do not always deliver "the same script"

- **Where.** `check_pinned_steps` line 576 (`text = run.rstrip("\n")`); the docstring, lines 112-114.
- **Scenario.** A script that ends inside an unterminated here-document reads its final newlines as body lines. A step
  written `|+` with two trailing blank lines equals the pin after `rstrip`, yet bash gives the here-document two more
  empty lines.
- **Evidence.** `$R/mutants/chomp_probe.bash` → `$R/evidence/chomp_probe.out` (bash 5.3.9):
  ```
  ending 2 $'grep -qx "" <<EOF\nfoo'  newlines 0: rc 1 | newlines 1: rc 1 | newlines 3: rc 0
  ending 3 $'wc -l <<EOF\nfoo'        newlines 0: stdout 1 | 1: stdout 1 | 3: stdout 3
  ```
  M9-11 (a pin, through `--pins`, ending in such a here-document; the step written `|+`) PASSES the checker. Executed:
  `step |+ … rc 0`, `step | (the pin's own reading) … rc 1`. None of the 18 current pins ends inside a here-document,
  so the hole is latent, but a pin update can open it.
- **Fix.** Accept at most one final newline (`|` or `|-`): refuse `run.endswith("\n\n")`, and compare
  `run[:-1] if run.endswith("\n") else run`. Zero and one final newline read alike in every case probed. Then reword
  lines 112-114.

### m9-b (MINOR): the pins loader does not enforce the ASCII-escaped form the docstring promises

- **Where.** The docstring, lines 94-95 ("The file is written with every character outside ASCII escaped, so a reviewer
  sees each one"), and `load_pins`, lines 497-501, which decode UTF-8 and accept any printable character.
- **Scenario.** A pin update hand-edited during a port's review writes TestPyPI's host with Cyrillic look-alikes. The
  loader accepts it, and the workflow's step, which holds the same raw text, equals it.
- **Evidence.** M9-7 PASSES (`$R/evidence/mutants_part2.md`). Executed (`$R/evidence/exec_part2.out`):
  `pins file ASCII only: False; the host as written: 'https://test.руpi.org/simple/'`, `that host in IDNA … test.xn--pi-kmcm.org`,
  and the pinned step ran `pip [install] [--no-deps] [--index-url] [https://test.руpi.org/simple/] …`.
- **Fix.** In `load_pins`, refuse `not raw.isascii()`. Every non-ASCII character in a pin then shows as `\uXXXX` in the
  pins file's review. The delivered file is pure ASCII (`$R/evidence/rederive_pins.out`), so nothing current is refused.

### n9-a (NIT): X8-2 and X8-3 checked against GitHub's own parser

- **X8-2 (a raw NEL).** YamlDotNet 5.3.0 and 16.3.0 read it exactly as PyYAML does; only Node `yaml` (YAML 1.2) keeps
  it in the line (`$R/evidence/x8_2_nel_values.out`).
- **X8-3 (a repeated `run:`).** Every parser delivers both keys, and GitHub's `TemplateReader` refuses the workflow:
  `keys = new HashSet<String>(StringComparer.OrdinalIgnoreCase)`, then `ValueAlreadyDefined` (lines 182 and 215-218).
  Neither case is a bypass on GitHub.
- **What to change.** Keep both refusals as defence in depth. Reword the `file_problems` message (line 330), which
  implies the runner reads a raw NEL otherwise, and correct the dispositions' X8-2/X8-3 text.
- **Two harmless edits are refused with a reason that is not true for them:** O9-7 (a leading BOM, which PyYAML strips)
  and O9-8 (a no-break space inside a YAML comment). No real port has either: all 18 current publish workflows pass the
  file-level rule (`$R/evidence/realports_scan.out`).

### n9-b (NIT): the mismatch message names the default pins file under `--pins`

`pin_mismatch` (line 542) always names `PINS_FILE`. It should name the pins path actually loaded.

### n9-c (NIT; pre-existing): a step that is not a mapping crashes the checker

P9-1 (`- echo a step that is a string` in the install job) raises `AttributeError` at line 741 (`s.get`), with exit 1.
That fails closed, but any later workflows on the same command line go unchecked
(`$R/evidence/wiring_probes.out`). Refuse a non-mapping job or step with a message instead.

## Bypass mutants (new, aimed at fix pass 7's design and the wiring a pin leans on)

Builders: `$R/mutants/build_mutants.py`, `build_mutants2.py` and `build_mutants3.py`. Executors:
`exec_install.py`, `exec_part2.py` and `exec_part3.py`. Every mutant is a copy of cascor's template (or of the ci-tools
simulation, for M9-8) judged with `--repo`. Executions use `bash -e`, as the runner does, with stand-ins for `pip`,
`python`, `sleep` and `twine`, or a real pip where its behaviour is the point.

| id | target | checker | executed outcome | verdict |
|---|---|---|---|---|
| M9-1 | install job `services:` (host bind mount, own `command`, health check) | **PASS** | rc 1 → rc 0: a wheel not from TestPyPI installed and imported (real pip) | bypass, M9-A |
| M9-2 | install job setup-python `mirror` + `check-latest` | **PASS** | rc 1 → rc 0 through the mirror's interpreter (stand-in); mechanism from setup-python's source | bypass, M9-B |
| M9-3 | `retention-days: 1:30` | **PASS** | PyYAML 90; GitHub "1:30"; upload-artifact `parseInt` → 1 day | bypass of the retention rule, M9-C |
| M9-3b | `retention-days: 0132` | **PASS** | PyYAML 90; GitHub 132 | divergence; no harm shown |
| M9-4 | dispatch `default: no` | **PASS** | PyYAML False; GitHub the string "no"; GitHub's use of it NOT verified | divergence, outcome unverified |
| M9-5 | setup-python `cache: pip` | **PASS** | not run: pip revalidates index pages and checks file hashes, so no outcome change shown | admitted; not a bypass shown |
| M9-6 | setup-python `update-environment: false` | **PASS** | not run: the pin would run the runner image's own pip (expected to fail closed) | admitted; not a bypass |
| M9-7 | `--pins` file written raw, Cyrillic look-alike TestPyPI host, sha256 updated | **PASS** | pip asked `test.xn--pi-kmcm.org` | m9-b |
| M9-8 | package binding: ci-tools' pin in a workflow publishing juniper-observability | FAIL | would test juniper-ci-tools while publishing observability | refused, correct |
| M9-9 | `--pins` line ending `\ ` (backslash, space) | FAIL (pins refused, exit 1) | pip ran `install ' '`; `--no-deps: command not found` | refused, correct |
| M9-10 | window: `twine check dist/* \` then `\_# \|\| cp stash/*.whl dist/` (YAML escape: the file is ASCII) | FAIL (the no-break-space rule alone) | bash ran twine with a `$'\xa0#'` argument, it failed, `cp` ran: the stash wheel in dist, rc 0 | refused, correct |
| M9-11 | `--pins` pin ending in an unterminated here-document; step `\|+` | **PASS** | `\|+` rc 0 against the pin's `\|` rc 1 | m9-a |
| M9-12 | the pinned run anchored, aliased by an extra job | PASS | all five parsers read identical events | changes nothing (control) |
| M9-13 | PyPI job `container:` | **PASS** | the image's python3 passes the verify step and replaces the dist the upload sends | bypass, B9-1 |
| M9-14 | PyPI job `services:` (work tree mounted, `--pid=host`) | **PASS** | verify passes on the true dist; rewritten before the upload | bypass, B9-1 |
| M9-15 | TestPyPI job `container:` | **PASS** | M9-13's mechanism (not run separately) | bypass, B9-1 |
| M9-16 | PyPI job `runs-on: [self-hosted, linux]` | **PASS** | not executable here | B9-1 |
| P9-1 | install job step that is a string | crash, exit 1 | — | n9-c |
| P9-2 | install job calls a reusable workflow | FAIL (`runs on None`) | — | refused, correct |

Fix pass 7's X8-1 to X8-8, re-executed in my copy (`$R/rerun/c8/evidence/new_mutants_r8.out`): each FAILS the live
checker and PASSES `checker_r8_naive.py`. Fix pass 6's checker refuses all but X8-2 and X8-3. Unexpected: 0. This is as
the fix pass reported.

## Divergence probes: what each parser delivered

The parsers are PyYAML pure (the checker's reader), libyaml, YamlDotNet 5.3.0, YamlDotNet 16.3.0 and Node `yaml`
2.8.1. Drivers are in `$R/parsers/`.

| probe | cases | result |
|---|---|---|
| cascor's template, whole | 1 | all five read the same 439 events |
| hand-built install-step forms (`diffhunt.py`): headers `\|`, `\|-`, `\|+`, `\|1`-`\|3`, `>`, `>1`, `>2`, tags `!`, `!!str`, `!<…>`, anchors, leading and trailing blank lines (0-14 spaces), trailing comments, `...`, `---`, emitter `"` and `'` at widths 20-100000, one-line and escaped-break double-quoted, plain and single-quoted multi-line, a flow step, keys `"run"`, `'run'`, `!!str run`, `&k run`, `"r\x75n"`, `? run`, `%YAML 1.1/1.2`, `%TAG`, CRLF | 84 | PyYAML parses 75; **0** where another parser reads other events. 12 where another parser errors (fail-safe), e.g. YamlDotNet 5.3.0 refuses `! \|` and `%YAML 1.2`, which the checker passes: GitHub would reject those files outright |
| random mutants, seed 9001 (`fuzz.py`) | 1,500 kept | libyaml, YamlDotNet 5.3.0, 16.3.0 and Node: 0 differ |
| random mutants, seed 424242, more seeds (`fuzz_b.py`) | 3,000 kept | libyaml and both YamlDotNets: 0 differ. Node: 7 differ, all one construct (below) |
| all 18 pins in every emitter style (`\|`, `>`, `"`, `'`; widths 20-unlimited; indent 2 and 4) plus hand forms (`\|+` trailing, `\|2`, `\|-`, folded by hand, double-quoted with `\ ` escapes) (`pin_styles.py`) | 810 | PyYAML reads the pin in 674; in **all 674** every other parser reads the same text (0 divergent, 0 errors) |
| X8-2 raw NEL | 1 | YamlDotNet 5.3.0 and 16.3.0 = PyYAML (a line break); Node keeps it in the line |
| X8-3 repeated `run:` | 1 | every parser emits both keys; GitHub's TemplateReader refuses (`ValueAlreadyDefined`) |
| escaped line break then an empty line (`escbreak_probe.py`) | 3 | PyYAML, libyaml and both YamlDotNets: `"first line \nsecond"` (per the spec); Node alone: `"first line  second"` |
| typed values (M9-3, M9-3b, M9-4) | 3 | PyYAML 90, 90, False; GitHub "1:30", 132, "no" |

Two further facts:
- YamlDotNet 5.3.0 has no `\/` escape and refuses it ("unknown escape character"). That is fail-safe.
- The runner writes the `run` text unchanged on Linux (`ScriptHandler.cs`: UTF-8 without BOM; line endings are
  converted only `#if OS_WINDOWS`), and an expression is recognized only by `${{` (`TemplateConstants.OpenExpression`).

## Re-run counts, against the Fix pass 7 section

My copy of the tools is `$R/rerun/c8`, repointed by `$R/rerun/make_copy.py`. The log is `$R/evidence/rerun_all.out`,
13:45:40Z to 13:49:01Z, plus `rerun_proof_r8.out`.

| step | Fix pass 7 section | round 9 |
|---|---|---|
| 1. cascor's three (landing tree, `f5ed3017`, `main`) | 3/3 ×3 | 3/3 ×3. `main` is still `b5b28dc3`; re-fetched read-only, byte-identical (`$R/evidence/fetch_cascor.out`) |
| 2. port-sim variants | 19 PASS / 6 FAIL; diff 0 lines; 15 of 15 | 19 / 6; diff 0 lines; 15 of 15; ml-F2+lag equals the seed |
| 3-4. judge_all | 70 by design; 7 bypasses FAIL; 9 outside kept; 0 findings | the same, set by set (r5 24/24 … r8-O8 28/28) |
| 5a. X8-1..X8-8 | live FAIL, naive PASS; reviewed PASSES X8-2 and X8-3 | the same; unexpected 0 |
| 5b. proof | 349 of 349 (43 PASS→FAIL by design, 197 kept, 40 NEW8, 3 command line) | 349 of 349, the same breakdown |
| 5c. round 2's 43 | 29 of 43; C1 by design; 13 kept; 0 other | the same |
| 6. lint | pre-commit 12/0/14, files unchanged; B914 0; flake8 3 E203; `--help` 0 | the same (E203 at lines 436, 810, 907) |

## The 15 port simulations, and cascor's three

From `$R/rerun/c8/evidence/port_sim_table.md`, regenerated by round 2's probes:

| # | port | variant | before (fix pass 6) | after (live, default pins) |
|---|---|---|---|---|
| 1 | juniper-canopy/publish.yml | faithful | PASS | PASS |
| 2 | juniper-data/publish.yml | faithful | PASS | PASS |
| 3 | juniper-data-client/publish.yml | faithful | PASS | PASS |
| 4 | juniper-cascor-client/publish.yml | faithful | PASS | PASS |
| 5 | juniper-cascor-worker/publish.yml | faithful | PASS | PASS |
| 6 | juniper-recurrence/publish-recurrence-app.yml | faithful | PASS | PASS |
| 7 | juniper-recurrence/publish-recurrence-client.yml | faithful | PASS | PASS |
| 8 | juniper-recurrence/publish-recurrence-model.yml | faithful | PASS | PASS |
| 9 | juniper-ml/publish.yml | faithful+ml-F2+lag | PASS | PASS |
| 10 | juniper-ml/publish-ci-tools.yml | faithful | PASS | PASS |
| 11 | juniper-ml/publish-config-tools.yml | reorder | PASS | PASS |
| 12 | juniper-ml/publish-doc-tools.yml | reorder | PASS | PASS |
| 13 | juniper-ml/publish-model-core.yml | faithful | PASS | PASS |
| 14 | juniper-ml/publish-observability.yml | faithful | PASS | PASS |
| 15 | juniper-ml/publish-service-core.yml | faithful | PASS | PASS |

cascor's `publish.yml`, `publish-cascor-model.yml` and `publish-protocol.yml` PASS from the landing tree, from
`f5ed3017` and from `main` (step 1).

## Step 2: the pins file, re-derived independently

`$R/pins/rederive_pins.py` → `$R/evidence/rederive_pins.out`. Each source was read by libyaml (not the checker's
loader) and by YamlDotNet 5.3.0. cascor's three were re-fetched at `f5ed30177766…` with read-only GETs. Result:
**18 of 18 equal** in repo, workflow, step name, package (the workflow's `PUBLISH_PACKAGE`), text, line split and
sha256, and both parsers agree on every source text. The file is format `juniper-publish-install-pins/1`, with exactly
the keys `format`, `about` and `pins` and exactly the seven fields on every pin. It is pure ASCII and ends in a newline.
Every statement in `about` is true.

## Step 6: over-strictness

Cases O9-1 to O9-12, in `$R/evidence/mutants_part2.md`:

| id | edit | verdict |
|---|---|---|
| O9-1 | quote another step's name | PASS |
| O9-2 | a YAML comment outside any block | PASS |
| O9-3 | install-step key order: `run`, then `env`, then `name` | PASS |
| O9-4 | `shell: bash` on the install step | PASS |
| O9-5 | window layout: a block holding a comment line | PASS |
| O9-6 | quote style of setup-python's version | PASS |
| O9-7 | a UTF-8 BOM at the file's start | FAIL (file-level rule; n9-a) |
| O9-8 | a no-break space in a header comment | FAIL (file-level rule; n9-a) |
| O9-9 | an em dash in a header comment | PASS |
| O9-10 | the install job's steps indented two more spaces | PASS |
| O9-11 | a pin holding a tab (`--pins`), the step equal | PASS |
| O9-12 | the install step as `\|-` | PASS |

**Real ports.**
- The current publish workflows of all eight repositories (18 files, fetched from each `main` read-only into
  `$R/realports/`) all pass the file-level rule and the loader (`$R/evidence/realports_scan.out`).
- Each verifies the install in exactly one run step (`$R/evidence/realports_install_steps.out`), so one pin per step,
  with one loop and one lag error, is not over-strict against them.
- Long lines and an em dash are held by cascor's own pin.

Edits to install scripts fail on their pin by design and are not counted here.

## Checks found sound

- **The interdiff.** Every removed rule judged only install-job run scripts; exact pins cover each one. `installs()`
  on the TestPyPI job, `bash -n` on every run step, the window's allow-list and `line_problems`, and every env rule are
  all kept.
- **N8-1's change.** It only reroutes messages: CR, VT, FF and NBSP are each refused by an earlier rule. M9-10 is
  refused by the NBSP rule alone.
- **`UniqueKeyLoader`.**
  - Repeated keys are refused by their text and by PyYAML's value, and `<<` is refused before `flatten_mapping` can
    apply it. A merge cannot happen without the merge tag.
  - Keys GitHub would read as one (case variants) make GitHub refuse the file, so that is fail-safe.
  - `!!omap`/`!!pairs` skip the hook but yield lists, which fail or crash closed.
  - GitHub's reader has no merge handling at all.
- **`script_problems`.** Its refusals (NUL, non-printable characters, trailing blanks, a final backslash, `${{`) hold.
  `${{` is GitHub's only expression marker.
- **The pin lookup.**
  - The key's file name and repository come from the operator. A workflow's own text chooses only the step name, and
    each pin's text must still match exactly.
  - Two steps under one name, a pin without its step, and a step without its pin each FAIL.
  - The package binding holds (M9-8).
  - `--pins` and the default `Path(__file__).resolve()` lookup are not workflow-controlled.
- **`load_pins`.** It refuses repeated JSON keys, a wrong format, wrong fields, a bad repo, workflow or step, bad
  lines, a repeated key, a stale sha256, and a text refused by `script_problems` (M9-9). The LAG_ERROR check is right
  for all 18 pins.
- **The comparison and the reading of the file.** The comparison is byte for byte apart from final newlines (with
  m9-a's exception). The file is read as bytes and decoded as strict UTF-8, which is at least as strict as GitHub.
- **No `run`-text divergence between PyYAML and GitHub's parser lineage** in any of 84 hand-built forms, 4,500 random
  mutants or 810 renderings of the pins.
- **Acknowledged residual, not re-raised.** Item 23 drops every action's `@ref`, so an action ref can name any commit
  of the action's fork network. With B9-1 and M9-B fixed, this is the remaining way code the checker does not compare
  could run in the install and credential jobs.
