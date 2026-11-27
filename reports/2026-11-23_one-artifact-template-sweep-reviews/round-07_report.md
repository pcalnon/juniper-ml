# Round-7 review of fix pass 5 (the cross-repo port checker, `checker-r6`)

Written 2026-11-24T02:29:23Z (work 02:08:49Z to 02:29Z, times from `date -u`) by the round-7 reviewer, worktree
`ethereal-munching-peacock` (W=`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`).
Brief: `$W/tmp/sweep/ROUND7_BRIEF.md`. Checker reviewed: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`,
sha256 `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85` (1704 lines). It equals the frozen copy
`$W/tmp/sweep/checker-r6/checker_r6_as_delivered.py`. The interdiff `$W/tmp/sweep/checker-r6/checker_r5_to_r6.diff`
hashes as the brief says (`6f629f04…`), as do the template (`b6826ee6…`) and the manifest `$W/tmp/arc/sweep_scripts.sha256`
(`3c5cfb08…`); `sha256sum -c` on the manifest passes.

## Read this first: what this round did NOT do

**Not done:**
- **Step 4.** No new bypass mutants were built or executed.
- **The bypass hunt in steps 1 and 2.** I did not look for new places where the checker and bash read a script
  differently.
- **The executed side of the two-readers question.**
- **Earlier mutants were judged again but not executed again.**

Why: partway through this session, a safety interruption stopped my work on building bypass mutants, and I did not
resume it.

**Consequence for the stopping rule** (`$W/tmp/sweep/ROUND7_BRIEF.md`, "Stopping rule"): this round found no BLOCKER
and no MAJOR, but it never ran the search that finds them. **Do not read this report as clearing the checker for
ports.** Step 4 still needs another round, or the orchestrator's own ruling.

**Done:**
- Every verdict-based proof was run again (step 3), with outputs here only.
- All 15 port simulations were regenerated and judged again.
- An over-strictness probe of 32 harmless edits (step 5).
- A review of the interdiff's claims and messages (step 1, every part except bypassability).
- Four checks of documented claims, run with `printf` alone.
- A static check of the two readers, using fix pass 5's own probe file.

**Verdict:** 0 BLOCKER, 0 MAJOR, 1 MINOR, 4 NIT. The MINOR is rated on static evidence only (see its caveat).

## Findings (most severe first)

### R7-1 (MINOR, static evidence only: bypassability not assessed) — the checker passes a pip command its pip rules never see

- **Where.**
  - The allow-list admits `pip` by name: `TOP_COMMANDS`, `:361`. `command_shape` leaves pip's arguments to other
    rules: `:876-877`, `:923`.
  - Those rules (F2-F4) see only the pip commands that `pip_calls` finds. It reads with `shell_words` (shlex):
    `:492-497`, `:1048-1055`, calls built at `:1356-1365`, F3 applied at `:1404-1409`.
  - The docstring admits the difference ("What this cannot see", `:223-226`).
- **Failure scenario.** A command in which `lex` (the allow-list's reader, which follows bash) finds a top-level pip
  command, and `pip_calls` finds none, passes the checker. F2-F4 never judge that pip command's arguments.
- **Evidence** (produced by this round, nothing executed):
  - Fix pass 5's own probe file `$W/tmp/sweep/checker-r6/shlex-probe/S1.yml` **PASSES** the live checker
    (`evidence/two_readers_files_r7.out`).
  - On its inserted line, `lex` finds `['pip', 'install', '--no-deps', '--force-reinstall', '--index-url',
    'https://pypi.org/simple/', 'juniper-cascor==0.14.0']`; `pip_calls` finds `[]`.
  - Fed those words, the checker's own F3 (`check_later`) reports "a pip command after the fetch names juniper-cascor
    again" (`evidence/f3_on_lexed_r7.out`).
  - So the PASS contradicts the checker's own rules.
  - This predates fix pass 5: `S1.yml` passes the checker round 6 reviewed too
    (`$W/tmp/sweep/checker-r6/evidence/shlex_probe.out`).
- **Caveat on the rating.** Fix pass 5 executed `S1` and the step failed (rc 1) with nothing hidden run
  (`$W/tmp/sweep/checker-r6/evidence/shlex_probe.out`). This round did not try to show an executed outcome change.
  If a later round shows one, the brief's own rule makes this a **MAJOR** (an allow-list entry, `pip`, that admits a
  bypass).
- **Fix (proven to cost no port anything).** In `check_install_job`, refuse any install command on which the two
  readers disagree about its pip commands: `pip_calls(c)` against the pip commands of `structure(lex(c))`, words
  compared after quote removal, with redirections set aside as both readers already do.
  - Over the template and the 15 simulations the two readers agree on every command: 259 install commands, 21 pip
    commands, 0 disagreements (`evidence/two_readers_ports_r7.out`). So the rule refuses no port.
  - The larger alternative: have F2-F4 read pip's words from `lex`.

### R7-2 (NIT, new in fix pass 5) — the escaped-blank rule refuses a case where both readings agree, with a message that is not true there

- **Where.** `line_problems` `:772-773`, the branch and its message. The module docstring at `:186-187` is accurate,
  since it names the indented case; the message is what overreaches.
- **Scenario.** `x\ \` followed by an **unindented** line `y`:
  - bash passes one word, `x y`, and so does the checker (`commands()` gives `x\ y`; `lex` reads `x y`);
  - it is refused anyway, with "bash keeps it in the word and ends the word at the next line's indentation". There is
    no indentation.
- **Evidence.** `evidence/claims_probe_r7.out`:
  - case C1: bash prints `[x y]` and the checker reads `x y`;
  - case C2, the next line indented: bash prints `[x ][y]` and the checker reads `x y`. That is a real divergence,
    correctly refused.
  - No port has an escaped blank (`evidence/inventory_continuations.out`: 0).
- **Fix.** Keep the refusal (it is conservative) and reword: "…whose space or tab before the backslash is itself
  escaped: where the next line is indented, bash ends the word at that indentation…". Or refuse only when the next raw
  line starts with a blank.

### R7-3 (NIT, predates fix pass 5) — a last-line continuation followed by a newline is refused with a reason that is not true

- **Where.** `line_problems` `:768-769`. The Fix pass 5 section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` says this
  case "was already refused, as a continuation into a blank line".
- **Scenario.** A script ending `cmd \` and then a newline (`run: |` keeps one):
  - bash removes the backslash and the newline, meets the end of input and runs `cmd`;
  - `commands()` gives `cmd`, so the two readings agree;
  - the message says "where bash ends the command (and runs the next line alone)", but there is no next line.
- **Evidence.** `evidence/claims_probe_r7.out` case B: bash prints `[a]` (rc 0); `commands()` gives `printf '[%s]' a`;
  `line_problems` refuses it.
- **Fix.** Admit it, since both readings agree, or give it a message of its own. No port has one.

### R7-4 (NIT, predates fix pass 5) — sending the fetch's output to a log is refused with a message that is not true

- **Where.** `check_loop` `:1216-1218`, `:1234`, with `fetch_words` from `pip_calls` (`:1423`).
- **Scenario.** `if pip install ... "juniper-cascor==${VERSION}" > "${RUNNER_TEMP}/fetch.log"; then` is refused with
  "the fetch's line is neither `if <fetch>; then` nor …". It is that form, plus a redirection:
  - `shell_words(template_form.group(1))` keeps the redirection;
  - `fetch_words` (from `pip_calls`) drops it;
  - so they never match.
- **Evidence.** `evidence/overstrict_r7.out` row H8. It is refused the same way by the checker round 6 reviewed.
- **Fix.** Set redirections aside before comparing, as R5-F7's O1 does for later pip commands in `own_line`, or say
  "a redirection on the fetch's line is refused". No port does this.

### R7-5 (NIT, new in fix pass 5) — the docstring's "compared as YAML text"

- **Where.** `:206-207`: "The template steps and the republish job are compared as YAML text with the template's".
- **What is true.** They are compared as parsed YAML values (`by_action` dicts, `:1625-1644`), as the opening at `:20`
  says. The run scripts are therefore equal strings after parsing.
- **Fix.** "…compared as parsed YAML, so each run script equals the template's character for character…".

## Bypass-mutant table

**None built in this round** (see "Read this first"). The earlier sets were judged again by verdict only, with the
live checker, each with the repo its builder named:

| set | source | live checker, as expected | matches fix pass 5's rows |
|---|---|---|---|
| round 5's R5-1..R5-18 + controls | `judge_mutants_r6.py` (`$W/tmp/sweep/checker-r6/`) | 24 of 24 | yes |
| round 4's M1..M15 + controls (as written; `ML0` fails on the old lag error, by design) | same | 18 of 18 | yes |
| round 2's seven + control (round 2's own template) | same | 8 of 8 | yes |
| fix pass 3's N1..N14 + controls | same | 17 of 17 | yes |
| fix pass 4's N5-1..N5-16 + controls (`CN0r` fails, by design) | same | 22 of 22 | yes |
| round 6's R6-1..R6-6 + controls | same | 10 of 10; each R6 PASSES the reviewed checker and FAILS the live one | yes |
| fix pass 5's N6-1..N6-13 + controls (`checker-r6/mutants-r6new`) | `n6_on_reviewed_r7.bash`, `rerun_r7.bash` 3b | live 18 of 18 (N6-1, N6-12 PASS; the rest FAIL; controls PASS); reviewed 18 of 18 as `new_mutants_r6.py` expects (N6-4, N6-7, N6-8, N6-9 PASS it) | yes |

The verdict rows of `evidence/judge_mutants.md` equal fix pass 5's `$W/tmp/sweep/checker-r6/evidence/judge_mutants.md`
(reason lines aside). None was executed again.

## The 15 port simulations

Regenerated by round 2's probes into `$W/tmp/r7review/port-sim/`. They are byte-identical to fix pass 5's
(`evidence/port_sim_r6_vs_r7.diff`: 0 lines; the ml-F2+lag copy is equal by `cmp`). The generator's 25 variants give
19 PASS and 6 FAIL, as the brief expects.

| # | port target | simulation | checker round 6 reviewed | live checker |
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

15 of 15 PASS (`evidence/port_sim_table.md`).

## Over-strictness (step 5)

`overstrict_r7.py` made 32 harmless edits plus one control (H0), each a change a real port might make and none
changing what runs. Each was judged by the live checker and by the checker round 6 reviewed, against the landing
template (`evidence/overstrict_r7.out`). Every file read back holds the edited script.

- **Refused: 2 of 32.** Both are refused identically by the checker round 6 reviewed, so fix pass 5 did not cause
  them:
  - **H8**: the fetch's output sent to `${RUNNER_TEMP}/fetch.log`. The reason is not true (R7-4).
  - **H19**: `>&2` on the lag error. The reason ("expected … found …") is true, and the refusal is by design (round 4's
    NIT pins the operator signature exactly).
- **Admitted: 30 of 32.**
  - In the template's install step:
    - a comment line (H1), or one inside the loop (H13);
    - a blank line (H14);
    - plain echo text (H2); an echo holding a tab (H16); two strings split by a spaced continuation (H17);
    - **tab continuations** on the fetch (H3);
    - the import check split after `-c` (H4);
    - `[ -n ]` (H5) and `[ -d ]` (H6) tests;
    - an echo appended to a `.log` file (H7);
    - the loop variable renamed to lowercase (H9);
    - `set -eu` (H10) and `set -euo pipefail` (H11);
    - `python3` (H12);
    - `pip --version` (H18).
  - In the ports:
    - juniper-ml's `[ -f "${WHEEL}" ]` (H15), and `set -eu` plus a comment line (H23);
    - the recurrence model's renamed variable (H20), tab continuations (H21) and `python3` (H22);
    - canopy's extra echo (H24).
  - In the window:
    - `twine check` split by a space (W1) or a tab (W2) continuation, after a comment line (W3), or with a trailing
      newline (W4);
    - canopy's smoke-test pip line split (W5);
    - juniper-ml's tag assert with tab continuations (W6), on one line (W7), or after a comment line (W8).
- The earlier corpora: round 5's O1-O3 and round 6's OS1-OS12 all PASS except **OS11** (a trailing comment, R6-N1, left
  refused by design) (`evidence/overstrict.log`).

The window change refuses no real window: juniper-ml's four-line tag assert and canopy's five-command smoke test pass
in all 15 simulations and in W5-W8.

## Re-run counts against the "Fix pass 5" section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`

All of these equal that section's counts (`evidence_rerun_r7.out`, driver `rerun_r7.bash`):

- **The checker.** Compiles with `-W error`; its sha256 is `6b2443c6…`.
- **cascor's three publishers:** 3 of 3 PASS from the landing tree, and 3 of 3 from `main` as fix pass 5 fetched it.
  `main`'s three files equal the landing tree's (`cmp`).
- **The 15-row table:** 15 of 15.
- **The checker proofs:**
  - `checker_proof_r6.py`: 289 of 289;
  - `checker_proof_r5.py` on the live checker: 261 of 261;
  - `checker_proof_r6.py` on the checker round 6 reviewed: 274 of 289. The 15 mismatches are exactly J6a, J6d, J6f,
    J6g, J6i, J6j, J6k, N6a-N6d, W6a, W6b, W6e and W6f;
  - round 2's 43 cases: 43 of 43, no verdict changed and no reason reworded against fix pass 5's log.
- **The continuation inventory:** 251 runs and 66 continuation backslashes, every one with a space before it, none
  escaped, none with a tab, every one followed by an indented line. No character outside printable text, space, tab
  and newline. It equals fix pass 5's (`evidence/inventory_continuations.out`).
- **Lint, read-only.**
  - pre-commit ran with its two fixer hooks skipped (end-of-file-fixer, trailing-whitespace): 0 failed, 9 passed, 17
    skipped. Both fixers' conditions were checked directly and hold: one final newline, and no line with trailing
    whitespace.
  - The hash is unchanged; B914 finds 0 sites; flake8 `--isolated` at 512 columns reports 12 findings, all E203;
    `--help` exits 0.
  - I skipped the fixers so that nothing could rewrite the frozen checker. Fix pass 5's run of all hooks passed with
    the file unchanged.

## Checks found sound

- **Every change in the interdiff only refuses; none admits.**
  - The NUL and character rules, and the two new continuation branches, only append problems.
  - Moving `following is None` ahead of the blank/comment branch adds a refusal and leaves that branch's effect
    unchanged.
  - Every branch of the `elif` chain refuses, so its order changes only which message is shown.
- **`commands()` has exactly two call sites**, install steps (`:1328`) and the window (`:1568`). Each is now paired
  with `line_problems` (`:1346`, `:1577`), so the docstring's "in every install step and in every step between the
  build and Record SHA256SUMS" is true.
- **The character rule covers its claim.** On this Python, 3.14.7, every code point `str.strip()` removes (26) and
  every one `str.splitlines()` ends a line at (9), besides space, tab and newline, is refused
  (`evidence/strip_coverage_r7.out`). So "in a script that passes it, `str.strip()` meets only ASCII blanks" holds.
- **Messages and claims checked against bash 5.3.9** (`evidence/claims_probe_r7.out`):
  - the last-line rule's message (case D: bash passes `\` on as an argument, `[a][\]`, and `commands()` drops it);
  - the escaped-blank message when the next line is indented (C2);
  - "shlex keeps a backslash bash removes inside double quotes" (A: shlex reads `a\$b`; bash and `lex` read `a$b`).
- **The two readers agree on every real port's pip commands** (R7-1's evidence), so the proposed agreement rule is not
  over-strict.

**Not verified by this round:**
- that bash drops a NUL, and that `bash -n` does too;
- "two differences it admits, as text that runs nothing" (`:220-223`). That is the bypass question, not assessed;
- the runner's bash version. Per the brief, `ubuntu-latest` runs 5.2; this host runs `GNU bash, version
  5.3.9(1)-release`.

## Files

**Created**, all under `$W/tmp/r7review/`:
- the drivers: `rerun_r7.bash`, `overstrict_r7.py`, `inventory_r7.bash`, `strip_coverage_r7.py`,
  `n6_on_reviewed_r7.bash`, `claims_probe_r7.py`, `two_readers_ports_r7.py`, `two_readers_files_r7.py`,
  `f3_on_lexed_r7.py` and `untouched_r7.bash`;
- their outputs, in `evidence/` and `evidence_rerun_r7.out`;
- generated trees: `port-sim/`, `overstrict/`, `claims/` and `scratch-proof-*/`;
- this report.

**Changed:** no existing file. `untouched_r7.bash` confirms this:
- the manifest passes;
- the frozen hashes are as the brief gives them;
- no file under `tmp/sweep/`, `tmp/r2review/`, `tmp/r4review/`, `tmp/r5review/`, `tmp/r6review/` or `util/` is newer
  than this review's first driver.

**Read:**
- `$W/tmp/sweep/ROUND7_BRIEF.md`;
- the round-6 table and the "Fix pass 5" section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`;
- the checker, the interdiff and the template;
- fix pass 5's drivers in `$W/tmp/sweep/checker-r6/`, used read-only.
