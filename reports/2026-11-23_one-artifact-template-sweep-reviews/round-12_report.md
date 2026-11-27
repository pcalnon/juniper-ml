# Round-12 review report: fix pass 10 on the cross-repo port checker (checker-r11)

2026-11-25T01:16:47Z to 01:58Z (from `date -u`). One fresh reviewer, given `$W/tmp/sweep/ROUND12_BRIEF.md` unedited.
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

**Verdict: 0 BLOCKER, 0 MAJOR, 3 MINOR, 7 NIT** against the checker
`util/ad-hoc/2026-11-23_publish_port_template_identity.py`, `b807d3ca…` (1750 lines). That file equals its frozen copy
`tmp/sweep/checker-r11/checker_r11_as_delivered.py`. The pins file `util/ad-hoc/2026-11-24_publish_port_install_pins.json`
(`d539f05f…`) is unchanged and equals its frozen copy.

- Fix pass 10's own rules held.
- Every count in § "Fix pass 10" of `tmp/sweep/REVIEW_DISPOSITIONS.md` was reproduced.
- 15 of 15 simulations pass, and cascor's three pass from all three trees.
- 18 of 18 pins re-derive equal from their stated sources.
- The three MINORs each reach one level past a fix-pass-10 rule:
  - files that are read without the size bound, or that block;
  - routes to the env file that the text rule does not see;
  - fake verdict rows produced by soft wrap.

One severity call is close. M12-C (soft wrap) is rated MINOR here. By fix pass 10's own screen-check standard
(`screen_check_fp10.py`), its pane is dishonest. The orchestrator may read the brief's display rule as making it a
MAJOR; the reasoning is in the finding.

## What this round did NOT do

Every step (1 to 6) was done, and every sub-step the brief names, and none was interrupted. The following were done by
substitution, or only as far as this host allows:

- **Step 4, lint.** I did not run `pre-commit run` on the live files, because its fixer hooks would write them and the
  brief makes every existing file read-only. Instead `tools/lint_copy_r12.bash` ran the content checks of those hooks on
  byte-identical copies: check-ast, check-json, end of file, trailing whitespace, merge markers, debug statements,
  private keys and size. It also ran B914, flake8 at 512 columns, and `--help`. This is round 11's method.
- **Display cases.** These were rendered in tmux 3.6 only. tmux implements no bidi algorithm and no bidi-aware terminal
  is on this host, so right-to-left reordering was reasoned, not rendered.
- **GitHub-side behaviour.** None was executable: the job timeout (N12-8), the concurrency queue (N12-7) and the
  server-side parser. Where it applied I ran GitHub's TypeScript parser and read the runner's C# sources (N12-10).
- **N12-4a to N12-4c.** These were executed with my own stand-in runner through the build job's Record SHA256SUMS,
  which fixes what the artifact carries. The TestPyPI, install and PyPI stand-ins were not re-run for them: round 11's
  M11-9 and fix pass 10's R11-1 ran that chain from the same recorded state.

## Findings (most severe first)

### M12-A (MINOR): files read without the size bound, or that block; the next workflow is never judged

- **Where.** Three places:
  - `extra_job_problems` reads the called workflow with `called.read_bytes()`, which has no bound (`:1283-1287`).
  - `read_text` (`:676-683`) bounds bytes, not time: it opens the path and calls `read(MAX_WORKFLOW_BYTES + 1)`, and
    does not check the path is a regular file.
  - The claim is untrue: "a delay, bounded, never a stop" (docstring `:291-294`), and m10-a's "nothing one workflow
    holds stops the next being judged" (`:244-250`).
- **Scenario.** A git tree can hold a symlink, and a checkout makes it. Suppose a juniper-data PR makes
  `.github/workflows/notify-consumers.yml` a symlink to `/dev/stdin` or `/dev/zero`, or makes the workflow file itself
  a symlink to `/dev/stdin`. The operator then runs the checker on that checkout. The read blocks forever on the pipe or
  terminal, or grows until memory is exhausted. The workflow after it is never judged. GitHub would not run such a file,
  so this costs the gate's availability, never a verdict. It is M11-B's class in a new form.
- **Evidence** (`tools/m12_unbounded.py`, `tools/m12_unbounded_b.py`; `evidence/m12_unbounded*.out`):
  - C12-1b, a faithful juniper-data copy, PASSES alone.
  - N12-2b (called file → `/dev/stdin`, an open pipe that never delivers, then C12-1b): no verdict line at all in 30 s,
    and C12-1b is never judged.
  - N12-3 (workflow → `/dev/stdin`): no verdict in 20 s.
  - N12-1b (called file → `/dev/zero`): only a 2 GB `ulimit -v` cap ended it, as a `MemoryError` after 1.5 s (FAIL,
    then C12-1b PASS). Uncapped, the read would grow until the kernel's OOM killer acts. That was not run, to keep the
    host safe.
  - C12-1 shows the checker follows a symlink to the real called file and PASSES.
- **Fix.**
  - Before reading a workflow or a called file, `lstat` it and refuse anything but a regular file: refuse symlinks, or
    open with `O_NOFOLLOW | O_NONBLOCK`, `fstat` the descriptor and require `S_ISREG`.
  - Read the called file through the same bound as `read_text`.
  - Correct the two claims.
  - The operator's inputs (`--pins`, `--template`) can take the same guard. They are not port-controlled.

### M12-B (MINOR): the env-file rule's documented gap is wider than documented; the index form of `github.env` passes

- **Where.**
  - The constant `ENV_FILE_NAMES` (`:533`) and the rule (`:1540-1544`).
  - The rule's message: "A text check: a name computed from parts is not seen".
  - The docstring (`:343-347`): "a text check that a name computed from parts passes".
- **Scenario.** A build step before the build can write `BASH_ENV` into the job's env file without spelling any of the
  five names, and the hook then runs inside the unchanged window `twine check`, as in M11-9. Three routes:
  - **N12-4a:** `for f in "$(dirname "$GITHUB_OUTPUT")"/set_env_*` (a sibling file command's directory).
  - **N12-4b:** `${{ github['env'] }}`, the index form of the very expression the rule names (`github.env`). The runner
    substitutes it into the text before bash reads it, so nothing is computed in the shell at all.
  - **N12-4c:** a `shell: python` step that globs `$RUNNER_TEMP/_runner_file_c*/set_env_*`.

  None reaches a job holding id-token. It reaches only the artifact's bytes, which the build step's own free text can
  already decide. That is the class round 11 rated MINOR (M11-C), and R11-1 is its documented residual.
- **Evidence** (`tools/m12_envfile.py`, `evidence/m12_envfile.out`).
  - Each mutant PASSES the live checker: exit 0, `2 of 2 pass` with the template after it.
  - Executed with a stand-in runner that follows actions/runner's FileCommandManager layout:
    - each step gets fresh `set_env_<guid>`, `add_path_`, `set_output_`, `save_state_` and `step_summary_` files, and
      the previous step's files are deleted;
    - expressions are substituted first;
    - `set_env` is read into later steps' environment.
  - Record SHA256SUMS then records `juniper_cascor-0.14.0-py2.py3-none-any.whl`, a wheel the build never made, beside
    the built one.
  - The control, C12-4, records one wheel.
- **Fix.**
  - State the residual truly: the rule stops only literal spellings. A sibling file command's directory, a glob, another
    expression spelling (`github['env']`, `github[format(...)]`, `toJSON(github)`) or another shell all pass.
  - Optionally add `github['env']` and `github['path']`, and refuse `_runner_file_c` as a prefix. This is cosmetic: only
    pinning the steps before the build closes the class, as fix pass 10 already wrote for plan v1.15.18.

### M12-C (MINOR, a close call): soft wrap can show a refused workflow's own PASS row and a `1 of 1 pass` row

- **Where.**
  - `upload_problems` prints an unknown input's key with `{key!r}` uncut (`:1266`; also `:1254`, `:1256`, `:1264`).
    Many other messages print uncut `!r` values as well: step labels, job ids, `env`, `if`, the workflow name.
  - `shown()`'s 200-character cut applies only where `shown()` is used.
  - The docstring (`:356-358`) says only that "a long value can begin a row on the screen".
- **Scenario.** The workflow holds an explicit YAML key (`? '…'` then `: true`, so there is no 1024-character limit).
  The key is made of printable blanks, then `PASS <its own label>  (PUBLISH_PACKAGE=…, PUBLISH_DIST_DIR=dist,
  PUBLISH_TAG_PREFIX=v)`, then `1 of 1 pass`. Each piece is placed at a line offset that is a multiple of 400, so in any
  terminal whose width divides 400 (80, 100, 200, …) each piece begins a screen row. The blank rows before them push the
  real FAIL line above the pane.
- **Evidence** (`tools/m12_wrap_b.py`, `tools/render_wrap_r12.bash`, `evidence/render_wrap_r12.out`,
  `tmux/captures/`).
  - The checker refuses N12-5b with exit 1. It prints 4 lines, each beginning with its own text, so the printed lines
    are true.
  - In tmux at both 200x50 and 80x50, the pane shows:
    - the fake row `PASS N12-5b/publish.yml  (PUBLISH_PACKAGE=juniper-cascor, …)`, which at 80 columns wraps exactly as
      a real PASS line does (compare C12-5);
    - a row `1 of 1 pass`;
    - two to five rows of the message's tail;
    - then the true `0 of 1 pass` and `[checker exit status 1]`.
  - The real FAIL line is not on the pane.
  - `screen_check_fp10.py`'s criteria would mark this pane "NO: the display does not agree with the exit status" and a
    FINDING: the visible verdict rows are `['PASS']`, two rows read as summaries, and the real FAIL row is not visible.
- **Why MINOR, not MAJOR.**
  - The exit status, the printed lines (which the docstring declares the verdict) and the last two visible rows are all
    true.
  - Unlike M11-1 and M11-2, nothing is concealed. Unlike M11-3, captured output is not forged.
  - The workflow must guess the terminal width, though a period such as 400 covers the common widths.
  - Fix pass 10 documented the mechanism (`:356-358`). Its own lead, "None can begin a line or hide one", is true of
    lines but not of rows.
- **Fix.** Either fix works:
  - hard-wrap every line the checker prints at 72 to 80 columns, with continuation lines indented, so that no row of a
    terminal at least that wide begins with workflow text;
  - or cut every value a message prints (route each `!r` through `shown()`), collapse runs of blanks in shown values,
    and state the residual for narrower terminals.

  At minimum, restate the residual: a refused port can display its own PASS row and a summary row in place of its
  FAIL line.

### NITs

- **n12-a: `place()`'s cut can make two refusals read alike** (`:736-742`, message `:806`). In N12-6, two refused
  places share their first 200 characters, and the message lists `'/kkk…...'` twice. Where each ESC stands is lost,
  though the count stays true (`evidence/m12_more.out`). Fix: keep a place's tail, or an index, when cutting.
- **n12-b: two passing publishers' groups can coincide** (rule `:1410-1413`; claims `:60-61`, `:302-306`). The claim
  that the group is "exactly its own" is not strictly true: `<stem>-<ref>` is the same string for stems `publish` and
  `publish-ci-tools` under refs `ci-tools-main` and `main`, or `ci-tools-juniper-ci-tools-v0.2.0` and
  `juniper-ci-tools-v0.2.0`. In N12-7 both files PASS and the evaluated groups are equal. The harm is nil in practice:
  both carry `cancel-in-progress: false`, so at most a pending run is replaced, and the refs must be crafted by a
  writer. Fix: word the claim as "a group no other publisher's file uses, for refs the publishers use".
- **n12-c: the checker passes files GitHub refuses.** N12-10 gives a step before the build `id: reuse`. GitHub's
  TypeScript parser and the runner's C# converter (`WorkflowTemplateConverter.cs:1682`, `IdBuilder.TryAddKnownId`)
  refuse the duplicate id, so the file would not run (`evidence/m12_dupid_b.out`). Fix pass 10's case C, an unknown
  top-level key, is the same kind. This is not a bypass. Optionally refuse a duplicate step id.
- **n12-d: a sixth path grows as the square, immaterial.** `check_pinned_steps` keeps `seen` as a list
  (`:1060-1069`). 10,000 named run steps cost 0.51 s and 20,000 cost 2.24 s, against `bash -n`'s roughly 33 s for the
  same steps (`evidence/cost_seen_r12.out`). Fix: use a set. The claim "nothing faster than linear" is then true.
- **n12-e: a size refusal is reported as a load failure.** A refusal by size reads "the workflow file does not load as
  YAML this checker can read (YAMLError): the file holds more than 262144 bytes…" (`:682` under `:1374`), though
  nothing was parsed. The inner text is true. Fix: give the size refusal its own prefix.
- **n12-f: `timeout-minutes` values are never read** (`OPTIONAL_JOB_KEYS`, `:459`, applied `:1444`). N12-8,
  `timeout-minutes: 1` on the PyPI job, PASSES. A timeout fails the job, so nothing that needs it runs: fail-closed.
  The exception is a partial upload, R4-4's availability harm. No port sets one. Record it, or hold the value to at
  least a floor.
- **n12-g: the brief names `juniper-data-main-fetch/notify-consumers.yml`.** The file is at
  `checker-r11/juniper-data-main-fetch/.github/workflows/notify-consumers.yml`, with the stated sha256 `e17ddc9b…`.

## The old-classes question, class by class

- **Rounds 4 to 8: the checker's reading of shell differed from bash's.** Not reached.
  - Install scripts are compared byte for byte after `script_problems`, and fix pass 10 did not touch that path.
  - The window's reader is unchanged, and `line_problems`' rewrite equals the old code:
    - 0 of 150,000 random scripts differ in my fuzz (CR, NBSP, tabs, backslash runs, `#`);
    - 0 of 435,923 differ in fix pass 10's own run.
- **Round 9: parts of a job not read, setup-python's inputs, typing.** Not reached in a form that changes what runs.
  - Keys are exact sets, setup-python takes `python-version` alone, and the typing fuzz and differential show 0
    divergences.
  - Still read but not judged:
    - `timeout-minutes` values (n12-f, fail-closed);
    - ids of the steps before the build (n12-c: GitHub refuses duplicates);
    - unknown top-level keys (GitHub refuses them).
  - GitHub's schema matches property names exactly (`MappingDefinition.cs:72`, `StringComparer.Ordinal`), so
    `Defaults:` or `Concurrency:` would be an "unexpected value". No case-variant key bypass exists.
- **Round 10: inputs, jobs and refs read too narrowly.** Not reached.
  - Upload inputs, extra jobs and refs are exact.
  - n11-b's case-insensitive reading (`uploads()`, `checkouts()`, the install job's check) never disagrees with
    `uses_problems` or `step_list` in a way that admits anything: every case variant is refused by `uses_problems`, and
    in a publish job by `step_list` too.
  - The called file is still gated by its sha256. Its read can block (M12-A), but it cannot admit other bytes.
- **Round 11.**
  - **What is printed:** sound at the level of lines. The 91 raw expressions in 220 fields were all re-judged safe, and
    M11-1 to M11-3 render truthfully. Screen rows via soft wrap: M12-C.
  - **A workflow that holds up the run:** M12-A (symlinks to devices and pipes). Every rewrite is linear and
    equivalent, and PyYAML's scanner and `bash -n` are linear. n12-d is immaterial.
  - **The steps before the build:** M12-B (three more routes, including the index form of `github.env`).
  - **A group shared with another workflow:** n12-b, and the documented residual (another workflow naming the group).
  - **The claim about an action's code (M11-E):** true. `REPO_ID` is the calling repository's id (action.yml at
    `7245906f`), so `set_image` (`create-docker-action.py:16-20`) yields
    `docker://ghcr.io/pypa/gh-action-pypi-publish:<action_ref>`, a mutable registry tag.

## Bypass mutants (new, executed; `tmp/r12review/mutants/`, `tmp/r12review/exec-envfile/`)

| id | target | checker verdict | executed outcome or display |
|---|---|---|---|
| C12-1 / C12-1b | control: juniper-data simulation, called file a symlink to the real file, or a copy of it | PASS / PASS | the checker follows the symlink |
| N12-1, N12-1b | called file → `/dev/zero` (`:1285`) | FAIL only through a 2 GB cap (`MemoryError`, 1.5 s) | unbounded read (M12-A) |
| N12-2, N12-2b | called file → `/dev/stdin`, a silent open pipe | no verdict; killed at 20 s and 30 s | the next workflow, PASS alone, never judged (M12-A) |
| N12-3 | workflow file → `/dev/stdin` (`:680`) | no verdict; killed at 20 s | hang (M12-A) |
| C12-4 | control: the template on round 12's stand-in runner | PASS | Record records 1 wheel |
| N12-4a | `$(dirname "$GITHUB_OUTPUT")/set_env_*` | PASS | Record adds a wheel never built (M12-B) |
| N12-4b | `${{ github['env'] }}` | PASS | same (M12-B) |
| N12-4c | `shell: python`, glob `_runner_file_c*` | PASS | same (M12-B) |
| N12-5 | first try: a simple key of more than 1024 characters | FAIL at load (ScannerError) | kept as written |
| N12-5b | soft wrap through an uncut `{key!r}` (`:1266`) | FAIL, exit 1, lines true | pane shows a fake PASS row and `1 of 1 pass`, the FAIL line off the pane, the true summary last (M12-C) |
| C12-5 | control: the template rendered | PASS, exit 0 | — |
| N12-6 | two refused places alike for 200 characters | FAIL | places print alike (n12-a) |
| N12-7 | stem groups of two publishers | PASS, PASS | groups equal for crafted refs; queue not executable (n12-b) |
| N12-8 | `timeout-minutes: 1` on the PyPI job | PASS, by design | not executable; a timeout fails the job (n12-f) |
| N12-9 | combining, wide, RTL, look-alike and filler text in a name | FAIL | tmux: kept within its row; FAIL, PASS, `1 of 2 pass`, exit 1, nothing concealed |
| C12-10 / N12-10 | a step before the build with `id: reuse`, writing `reuse=true` | PASS / PASS | GitHub refuses the duplicate id: not a bypass (n12-c) |

## What each starting point came to

1. **Printable text in a terminal.**
   - Combining marks, wide characters, fillers and look-alikes stay within their row (N12-9).
   - RTL reordering was not renderable here. Every verdict line begins with an LTR checker token ("PASS", "FAIL", the
     summary), and terminal paragraphs are lines, so a value cannot reorder another line.
   - Soft wrap: M12-C.
2. **`ENV_FILE_NAMES`.**
   - Routes it misses: M12-B (a sibling directory, the index form, `shell: python`).
   - An action that writes the env file: only setup-python, held to `python-version`. checkout and upload-artifact
     write none.
   - `GITHUB_STATE`: inert for run steps.
   - `GITHUB_OUTPUT` of a step the window reads: a later step cannot set `steps.reuse.outputs` (n12-c: a duplicate id
     is refused by GitHub).
   - A background process: documented.
3. **`MAX_WORKFLOW_BYTES`.**
   - Is anything faster than linear?
     - PyYAML stays linear over 18 shapes, at most 3.4 s at the bound (`evidence/cost_r12.out`).
     - `bash -n` stays linear over 15 shapes, at most 0.13 s for one script of 229 KB (`evidence/bash_n_cost.out`);
       deep nesting segfaults bash, which is a refusal.
     - `seen` is quadratic but immaterial (n12-d).
   - Files outside the workflow: the called file is read unbounded and can block (M12-A). The pins file is the
     operator's (`read_bytes`, and `keys.count` is quadratic). It is not port-controlled.
4. **The cuts.** Messages stay true. A cut can hide where a refused character stands and make two refusals read alike
   (n12-a). The cut does not hide why a value is refused.
5. **Unread keys.** Top level: GitHub refuses unknown keys, and `run-name` only displays (O12-13b passes). Jobs are
   exact. Steps: the install job's are exact; those before the build are free (documented) and their ids unread
   (n12-c). `timeout-minutes` values are unread (n12-f).
6. **`path.stem`.**
   - `.yaml` gives the same stem.
   - A renamed copy fails the pin key anyway, so the two readings agree.
   - The drivers' named copies keep the pinned name.
   - Two files `publish.yml` and `publish.yaml` would share a stem, and stem prefixes can coincide (n12-b).
7. **Case-insensitive versus exact readings:** no disagreement admits anything (above).
8. **Refusals at load, then the rules that run anyway:** every other rule prints through `shown()`, `!r` or
   `visible()`, and `main()` escapes every line. No refused string reaches the output raw. I verified this by the audit
   and by rendering M11-1 to M11-3 and N12-9.

## Re-run counts against § "Fix pass 10"

The full run is `rerun/rerun_all_r12.out` (01:29:44Z to 01:38:29Z); the extras are `rerun/extras_r12.out`. Every count
matches.

**Steps 1 and 2.**
- Cascor's three publishers: 3 of 3 PASS from the landing tree, from `f5ed3017`, and from main as fetched.
- The 15 simulations:
  - the probes give 18 PASS and 7 FAIL;
  - the regenerated files show 0 diff lines against fix pass 6's seeds;
  - the table gives 15 of 15 PASS;
  - 18 of 18 pins re-derive equal.

**Step 3, the mutant sets.**
- 3a: 0 verdicts moved and 0 findings.
- 3b: 32 of 32 as expected (13 bypasses present).
- 3c: X8-1 to X8-8 each FAIL the live checker, PASS the naive one and FAIL the reviewed one; 0 unexpected.
- 3d: N9-1 to N9-9 FAIL, and C9-1 to C9-5 PASS.
- 3e: only O10-7 and O10-8 moved (fix pass 9's changes); 0 findings.
- 3f: 7 executed with the outcome changing, 1 refused by GitHub's TS parser, 2 controls, 8 not executable, 0 unexpected.
- 3g: none moved; 0 findings.
- 3h: 21 negative tests FAIL as expected, 1 residual probe as expected, 6 controls PASS, 0 unexpected.
- 3i: the screen check gives 0 findings.

**Step 4, the proofs.**
- 479 of 479 as expected, with fix pass 10's 6 message-only changes.
- Round 2's 43 cases: 26 of 43 as expected, with 17 mismatches as fix pass 9 recorded them.

**Step 5, the fuzz and the typing differential.**
- Seed 9001: 3066 tried, 1500 kept, 0 differ for libyaml, yd53, yd16 and Node.
- Seed 424242: 6390 tried, 3000 kept, Node 7 differ.
- The typing differential: 3320 documents; 2453 agree, 861 both refuse, 6 refused by the checker alone, 0 by GitHub
  alone, 0 divergences.

**Step 6, lint** (content checks on copies): B914 0, flake8 2 E203, `--help` exit 0.

**Step 7, cost and audit.**
- 14,254 run steps took 50.3 s (fix pass 10 measured 44.9 to 48.5 s); 6,288 env keys took 1.0 s.
- The f-string audit finds 91 raw expressions in 220 fields.

**Extras.**
- Equivalence: 0 differ in 688,281, 435,923, 90,445, 3,000, 30,000 and 30,000 inputs.
- Square-cost probe, before: A 22.7 s, B 5.2 s, C 795 MB, D 463 MB, E 3.6 s.
- After: A 0.6 s, B 1.3 s, C 64 MB, D 65 MB, E 2.8 s, F 149.4 s at 116 MB (fix pass 10 measured F at 143.7 s).

**My own checks.**
- `tools/equivalence_r12.py`: 0 differ in 535,923 strings, 150,000 scripts, 30,000 documents for `load_text`, 30,000
  plus 3,000 for `document_problems`, and 100,000 values for `shown()`.
- `tools/rederive_pins_r12.py`, using libyaml's C loader: 18 of 18.
- A read-only re-fetch (`evidence/fetch_main_r12.log`, 01:56:48Z): juniper-cascor `main` is now `5e3d9801` (#775) and
  juniper-data `main` is `8e08d209` (#548). All five files are byte-identical to the frozen copies, and the called file
  is still `e17ddc9b…`.
- Untouched check: no file or directory outside `tmp/r12review/` is newer than this round's start, and the manifest
  passes 7 of 7.

## The 15-simulation table (`rerun/c11/evidence/port_sim_table.md`)

Each row PASSES under fix pass 9's checker and under the live one:

| # | target | simulation | before | after |
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

## Over-strictness (step 6; `evidence/m12_overstrict*.out`)

**Passes.** Each of these harmless edits passes:
- printable non-ASCII in a step name, in a comment (an emoji with VS16, CJK) and in the workflow name;
- a tab in a run and in a name;
- quoting, key order, and a folded `if`;
- `timeout-minutes` on the build job;
- a flow-style `with`;
- a new comment after a SHA;
- the exact concurrency group in flow style, with its keys swapped, or with `False`;
- a build step writing its own `$GITHUB_OUTPUT` and `$GITHUB_STEP_SUMMARY`;
- `SOURCE_DATE_EPOCH` in the build step's own env;
- `run-name`;
- an id on a step before the build;
- the `{name, url}` environment mapping;
- a file of exactly 262,144 bytes;
- CRLF line endings throughout.

**Refused by design.** Each message is true, and no port is affected:
- the concurrency group as `${{github.ref_name}}`, in its string form, or as `${{ github['ref_name'] }}`, all of which
  GitHub reads alike (exactness);
- `SOURCE_DATE_EPOCH` written through `$GITHUB_ENV` (M11-C);
- a second upload-artifact in the build job (M11-C);
- a ZWJ emoji in a comment (U+200D, the file rule since fix pass 7);
- 262,145 bytes.

## Checks found sound

- `compose_node` refuses every anchor and alias before any node is composed.
- `frozen` and the sets equal the old list check exactly (`1`, `True` and `1.0` alike; NaN as before).
- `document_problems` walks every key and string. Non-string keys hold no text, and the newline rule covers every name
  printed on one line.
- `visible()` and `shown()` escape every character `isprintable()` rejects. Every printed line begins with the checker's
  own text, and M11-1 to M11-3 render truthfully.
- The upload-artifact rule is exact, and the concurrency rule is exact with its types.
- The pins file's printable rule admits the real pins file and refuses control characters.
- The five rewrites are equivalent, and PyYAML and `bash -n` are linear under the bound.
- GitHub's schema keys are case-sensitive.
- The M11-E docstring is true.
- The 15 simulations and cascor's three publishers pass; the 18 pins are true to their sources.
