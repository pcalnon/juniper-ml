# Round-8 review of fix pass 6 (the cross-repo port checker, `checker-r7`)

Written 2026-11-24, work 03:13Z to 03:55Z (times from `date -u`), by the round-8 reviewer, worktree
`ethereal-munching-peacock` (W=`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`).
Brief: `$W/tmp/sweep/ROUND8_BRIEF.md`. Checker reviewed: `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`,
sha256 `789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2` (1753 lines), equal to the frozen copy
`$W/tmp/sweep/checker-r7/checker_r7_as_delivered.py`. Every frozen input hashes as the brief says (the interdiff
`4b680c76…`, the reviewed checker `6b2443c6…`, the template `b6826ee6…`, the manifest `924328b1…`), and `sha256sum -c`
on the manifest passes (`untouched_r8.out`). All paths below are under `$W/tmp/r8review/` unless they say otherwise.

## What this round did NOT do

**Every step and sub-step of the brief was done**, the executed-mutant step included (steps 1 to 5; evidence below).
No step was interrupted. Three limitations, none of them an undone step:

- **Nothing ran under bash 5.2**, the version GitHub's `ubuntu-latest` runs. This host has only GNU bash
  5.3.9(1)-release, and every execution here is on 5.3.9. I also tried a read-only `gh` GET of bash's `parse.y` at
  the `bash-5.2` and `bash-5.3` tags of the public GitHub mirror `bminor/bash`, to show R8-1's parser rule in 5.2's
  source. It returned HTTP 404 through this host's `gh` credentials (`bash-src/*.err`). R8-1 rests on bash's NUMBER
  token: a word of digits is a file descriptor only when a `<` or `>` ends it. I believe 5.2 has the same rule, but I
  have not verified it.
- **The lint pass skipped pre-commit's two fixer hooks** (`end-of-file-fixer`, `trailing-whitespace`), so that nothing
  could rewrite the frozen checker. Round 7 did the same. I checked both hooks' conditions directly: one final newline,
  0 lines with trailing whitespace. My copy of `lint_checker.bash` (`rerun/lint_checker.bash`) differs from fix pass
  6's only in that.
- **The proposed fixes were tried only as a checker mutant** (`fixprobe/checker_r8_fixprobe.py`). They are not a
  delivered fix; fix pass 7 owns the fix.

## Verdict

**0 BLOCKER, 3 MAJOR, 0 MINOR, 5 NIT.** All three MAJORs are executed bypasses: each passes the live checker and
changes the outcome.

- **R8-1 is new in fix pass 6 on the fetch line.** The checker round 7 reviewed refused it. R7-4's relaxation opened
  it, through a mistake in `structure()` that both readers share.
- **R8-2 and R8-3 predate fix pass 6.** The reviewed checker passes them as well.

By the brief's stopping rule, no port is built against this checker: fix pass 7 must fix R8-1 to R8-3, and its
interdiff must be reviewed again. A checker mutant with the fixes proposed below refuses the six bypasses (B8-1 to
B8-3, B8-5, B8-7 and B8-8) and B8-6.
It refuses none of the 15 port simulations and none of cascor's three publishers, keeps every over-strict verdict, and
passes all 308 of `checker_proof_r7.py`'s cases (`fixprobe/`).

## Findings (most severe first)

### R8-1 (MAJOR; new on the fetch line in fix pass 6): bash reads a digit written against `&>` or `&>>` as an argument; both of the checker's readers read it as a file descriptor

- **Where.**
  - `structure()` `:869` takes a digit word as the descriptor of any operator in `REDIRECTIONS`, `&>` and `&>>`
    included (`DIGITS.fullmatch(last.text) and last.end == token.start`).
  - `pieces()` `:535-537` pops any digit word before an operator holding `<` or `>`.
  - R7-1's comparison `:1402-1410` compares these two readings, so it cannot see a mistake they share.
  - R7-4's relaxed fetch-line comparison `:1258` and `:1264` (`pieces(shell_words(...)) == [([], fetch_words)]`) is
    what lets the mistake reach the fetch. The checker round 7 reviewed compared `shell_words(...)` whole there, so it
    refused every redirection on the fetch's line, this one included.
- **Failure scenario.** In bash, digits are a descriptor only when the character that ends them is `<` or `>`. So
  `0&>file` is the word `0` followed by the redirection `&>file`. A port writes its fetch as
  `"juniper-cascor==${VERSION}" 0&>"${RUNNER_TEMP}/fetch.log"`. Both readers see the template's fetch, and F2 passes
  it. bash runs `pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==X 0`, which fetches
  a second requirement from TestPyPI. Any digit string works (`0`, `12`), and anyone can register such a project on
  TestPyPI. Installed, its build backend runs code, or a `.pth` file it ships runs code at every Python start, before
  the import check. This is N7-3's outcome. The Fix pass 6 section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` says
  R7-1's rule refuses N7-3, which is true only of N7-3's spaced form (`0 >`).
- **Evidence.**
  - bash 5.3.9 (`quick/probe_digits.sh`): `args x 0&>f1.log` writes `<x><0>` into the file. `0&>>` does the same.
    With `0>f3.log`, `0` is the descriptor and the command receives `<x>`.
  - Probe rows R1, R2, R16 and R17 (`bash_semantics_probe_r8.out`): `lex` gives `['A', 'x']` plus the redirection
    `('&>', …)`, `pieces` gives `['A', 'x']`, and bash logs `A<x><0>`. Row R17, the fetch: both `pip_calls` and
    `lex_pip_calls` give `[pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==0.15.0]`,
    while bash logs `…<juniper-cascor==0.15.0><0>`.
  - Executed mutants (`new_mutants_r8.out`). Each PASSES the live checker, FAILS the reviewed one, and PASSES the
    R7-1-off mutant:
    - **B8-1**, cascor's template: `ran: PIP install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==0.15.0 0`;
    - **B8-2**, juniper-ml's flag form with `0&>>`: `ran: PIP download --no-deps --index-url https://test.pypi.org/simple/ --dest <tmp> juniper-ml==0.15.0 0`;
    - **B8-3**, canopy's port with `12&>/dev/null`: `ran: PIP install --no-deps --index-url https://test.pypi.org/simple/ juniper-canopy==0.15.0 12`.
  - On a later install, **B8-4** PASSES both checkers, so this half predates fix pass 6: `ran: PIP install
    requests>=2.28.0 9`. F3 admits a plain requirement on another package from PyPI, so the outcome stays within F3's
    policy. It is still a pip argument that no rule judged.
  - The mistake does not reach the build window: **B8-16** fails, since the step is no longer `twine check dist/*`
    verbatim. It does not reach the import check either: **B8-17** fails, since `shlex` reads six words there.
- **Fix.** In `structure()`, take the descriptor only when the operator begins with `<` or `>`
  (`… and last.end == token.start and token.op[0] in "<>"`). In `pieces()`, pop a digit only before such an operator
  (`… isdigit() and op[0] in "<>"`). Both readers then pass the digit to pip, as bash does, and F2 refuses it as a
  second positional. The fix probe reports `its first pip command must name juniper-cascor==${<version>} alone:
  ['juniper-cascor==${VERSION}', '0']`. Add B8-1 to B8-3 as FAIL cases. Add B8-13 (`0>`) and B8-14 (`&>` alone) as
  PASS cases.

### R8-2 (MAJOR; predates fix pass 6): bash's last-argument parameter `_` is admitted as an ordinary variable, and the wheel rule trusts it

- **Where.**
  - `ASSIGNABLE_LOWER` `:423` (`[a-z_][a-z0-9_]*`) matches `_`, so `check_allowlist` admits `_` as an assigned name
    and as a loop variable `:980-983`.
  - `SIMPLE_REFERENCE` `:405` admits `$_` and `${_}` `:1002-1004`.
  - The wheel rule `:1449-1452` (`(\w+)="${<dest>}/<name>-${<version>}-py3-none-any.whl"`, assigned once) and
    `check_later` `:1229-1231` then accept `pip install "${_}"` as an install of the fetched wheel.
  - The loop variable (`LOOP_HEADER` `(\w+)` `:370`), the flag and the `--dest` can be named `_` the same way.
- **Failure scenario.** After every simple command, bash sets `_` to that command's last argument, so a value
  assigned to `_` is gone by the next line. In this scenario:
  - a download-form port names its wheel variable `_`;
  - it prints a line whose last word is `juniper-ml`;
  - it then runs `pip install --index-url https://pypi.org/simple/ "${_}"`.

  The checker reads that as an install of the wheel TestPyPI served. bash installs the package under test by name,
  from PyPI, with its dependencies. The TestPyPI artifact is never installed, and the import check judges PyPI's
  artifact. F3's rule against naming the package again never sees the name.
- **Evidence.**
  - bash 5.3.9 (`quick/probe_underscore.sh`): after `_="/dl/juniper_ml-0.15.0-py3-none-any.whl"`, `${_}` is empty.
    After `echo "installing" "juniper-ml==0.14.0"` it holds `juniper-ml==0.14.0`, and after `ls -la /dev/null` it
    holds `/dev/null`.
  - **B8-5**, juniper-ml's port with `WHEEL` renamed `_`, its `[ -f ]` block dropped (after the assignment `$_` is
    empty) and an `echo "…" "juniper-ml"` before each install. It PASSES the live and the reviewed checker. Executed,
    it runs `ran: PIP install --index-url https://pypi.org/simple/ juniper-ml`, then `juniper-ml[clients]`, then
    `juniper-ml[tools]`. The downloaded wheel is never installed, and rc is 0 with the import stand-in succeeding.
  - **B8-6**, cascor's template with loop variable `_`, run with a pip stand-in that TestPyPI never serves. It PASSES.
    Executed, the five fetches fail and `::error::` lines printed: 0, with no `exit 1`: `[ "${_}" -eq 5 ]` reads the
    failed fetch's last argument. The step goes on to the import, which fails on a runner. So this half loses the lag
    error (the operator signature F2 pins), not the verdict.
- **Fix.**
  - Refuse `_` as an assigned name and as a loop variable: `ASSIGNABLE_LOWER = [a-z][a-z0-9_]*|_[a-z0-9_]+`.
  - Refuse `$_` and `${_}` wherever they are expanded: `SIMPLE_REFERENCE` without `_`, which the fix probe writes as
    `\$(?:(?!_(?![A-Za-z0-9_]))[A-Za-z_][A-Za-z0-9_]*|\{(?!_\})[A-Za-z_][A-Za-z0-9_]*\})`.
  - Add B8-5 and B8-6 as FAIL cases.

  The 15 simulations pass under this fix, so none of them uses `_`.

### R8-3 (MAJOR; predates fix pass 6): an `if` hidden from `shlex` swallows the failure of a later install, or of the import check

- **Where.** The allow-list admits `if`, `then` and `fi`, and any command it admits, as an if's condition
  (`ADMITTED_RESERVED` `:389`, `check_allowlist` `:968-970`). Two judgments are left to `shlex` readers:
  - "an if tests only a `[ ]` test or the fetch" is left to `check_constructs` `:1300-1308`, which reads
    `pieces(shell_words(command))`;
  - R4-2 (the step ends at its `python -c` check) reads `shell_words(step_cmds[-1])` at `:1477`.

  R7-1's comparison covers pip commands only.
- **Failure scenario.** This is fix pass 5's `S1` trick without a pip in it. Inside `"$(python -c "#'")"`, `shlex`
  reads the inner double quote as closing the outer one, and the `'` as opening a single quote. A second such
  substitution closes that quote. Between the two, `shlex` sees one word where bash sees `; if …`:
  - **B8-7** hides an if around a later install. Line 1 is `x="$(python -c "#'")"; if y="$(python -c "#'")"`, then
    `pip install "requests>=2.28.0"` stands alone on the next line, followed by `then`, `echo …` and `fi`. `own_line`
    is satisfied, since the pip line stands alone, and `check_constructs` sees no `if`. bash runs the install as part
    of the if's condition list, where `-e` does not apply.
  - **B8-8** hides an if around the import check. The import line becomes `python -c "$(python -c "#'")"; if python -c
    "<the import>"; then echo …; fi; y="$(python -c "#'")"`. That is three `shlex` words (`python`, `-c` and one
    more), so R4-2 is satisfied. bash runs the import inside an `if`.
- **Evidence** (`new_mutants_r8.out`; each PASSES both the live and the reviewed checker):
  - B8-7, with a pip stand-in whose `requests` install exits 1: `ran: PIP install requests>=2.28.0`, then `ran: PIP
    (this install FAILS, exit 1)`, then the import runs. rc(import ok) is 0.
  - B8-8, with a real `python3` and nothing installed: stderr ends `ModuleNotFoundError: No module named
    'juniper_cascor'`, and the step's rc is **0**.
- **Context.** What the `python -c` check asserts is each repository's own business, so a port could write a trivial
  check instead. But the two rules bypassed here exist so that a failure reaches the step (`own_line`: "so its failure
  fails the step"; R4-2: "`| tee log` or `&` after it hides its status"), and refusing a swallowed failure is the
  checker's stated purpose. Written plainly, each is refused: an `if pip install …` line, or a trailing `&`.
- **Fix.**
  - Judge an if's condition in the allow-list, which reads with `lex`. In `check_allowlist`, at the top level, refuse
    a simple command opened by `if` or `elif` whose first word is not `[` or `pip`. A `pip` there is the fetch, which
    `check_loop` holds to the template's line; a later pip inside an if is refused by `own_line` or R7-1.
  - Read R4-2's last command with `structure(lex(…))` as well: one simple command, with no control operator, no
    redirection and no reserved word, whose words are `python`/`python3`, `-c` and one more.
  - Add B8-7 and B8-8 as FAIL cases.

  The fix probe refuses both mutants. Its messages: `tests a command other than a [ ] test or the fetch in an if or
  elif, as bash reads it`, and R4-2's own message. The wider class stays open wherever a verdict rests on
  `shell_words` alone, since `shlex` misreads `"$(… "…'…" …)"`. After this fix, the `shlex`-read rules left are:
  - `own_line` (its operators come from `skeleton`, which reads `$(...)` as bash does);
  - `check_loop`'s fetch line (R7-1 guards it);
  - the `pip --version` exemption (exact words);
  - the deny rules the allow-list already covers.

### N8-1 (NIT): R7-3's first message is false where the "blank" line holds a character Python strips and bash does not

- **Where.** `line_problems` `:778` (`following = lines[at + 1].strip()`) and `:788-793`.
- **Scenario.** A continuation into a line holding only a CR, a vertical tab, a form feed or a no-break space gets
  "bash ends the command at a blank line …". bash continues the command into that line's word: it is not blank to bash.
  A no-break-space line at the script's end also gets this message, not the end-of-script one. Every such script is
  refused as well, by the line-break or character rule, whose message is true. So the false message is never the only
  one given.
- **Evidence.** Probe rows C2, C3, C3e, C4 and C5 (`bash_semantics_probe_r8.out`): bash logs `A<a><\r>`,
  `A<a><\xa0>`, `A<a><\x0b>` and `A<a><\x0c>`, then runs the next line. Mutant **B8-15** (`new_mutants_r8.out`) gets
  both messages. In probe row J16 (CRLF), the older message "which bash reads as an escaped space" is not exact
  either: bash reads an escaped CR.
- **Fix.** Compute `following` with `.strip(" \t")`. A line holding another character then falls through to the
  rules that name it.

### N8-2 (NIT; over-strict; predates fix pass 6): a one-line `if [ -f "${WHEEL}" ]; then echo …; fi` is refused for a reason that is not true

- **Where.** The dest-naming rule `:1462-1470` and `test_only` `:1048-1061`, which accepts `if [ … ]; then` only on a
  line of its own.
- **Evidence.** **O8-11** (`overstrict_r8.out`) is refused with "names the fetch's --dest or wheel in a command that
  could write there". Executed, it changes nothing. The same test over three lines (**O8-12**) passes.
- **Fix.** Accept, in `test_only`, a one-line `if [ … ]; then <plain echo>; fi`, or judge each of the line's simple
  commands.

### N8-3 (NIT; over-strict; predates fix pass 6): `set -e -u` before the `cd` is refused by the cd-first rule, though the allow-list admits it

- **Where.** `:1370`. Its set-line filter, `set -[a-z]+(?: -o [a-z]+)?(?: [a-z]+)?`, does not match `set -e -u`, while
  `command_shape` `:908-921` admits that line.
- **Evidence.** **O8-14** (`set -o errexit`, then `set -e -u`, then the `cd`) is refused with "does not run every command
  from $RUNNER_TEMP". `set -eu` passes (round 7's H10).
- **Fix.** Filter the lines with `command_shape("set", …)`.

### N8-4 (NIT; over-strict; predates fix pass 6): the loop's retry echo sent to stderr is refused as "not an echo of a quoted string"

- **Where.** `check_loop` `:1275-1276`. `PLAIN_ECHO` fullmatches `echo "…"` with no redirection.
- **Evidence.** **O8-18** (`… (attempt ${attempt}/5)" >&2`) is refused with "inside the loop only an echo of a quoted
  string and one sleep may follow the fetch's test". It is an echo of a quoted string, onto another stream.
- **Fix.** Admit `>&2` on the loop's echo, or name the redirection in the message.

### N8-5 (NIT): three docstring claims are false or misleading, as this round's findings show

- **`:236-238`**, "every place found where the two readings differ is refused": R8-1 and R8-3 are such places, and
  neither is refused.
- **`:245-246`**, the `shlex` readers each "only adding refusals to the allow-list's reading of the same command": the
  allow-list leaves the if-condition and R4-2 to these readers (R8-3), and the relaxed loop comparison admits what
  bash reads otherwise (R8-1).
- **The fix pass 6 bullet `:222-223`**, "so F2 to F4 judge the pip words bash runs": true only as far as `lex` reads
  them as bash does, which the bullet itself says. R8-1 is where it does not.
- **Fix.** Reword with fix pass 7.

## The bypass-mutant table (step 4: 17 new mutants, 5 controls, every one executed)

Driver `new_mutants_r8.py`, output `new_mutants_r8.out`, files `mutants-r8/`. "old" is the checker round 7 reviewed
(6b2443c6), "new" the live one (789287c5), "-R71" the live one with R7-1's comparison off (`rerun/checker_r7_minus_r71.py`,
a7622303). Every file the checkers read holds the script executed (round trip True). Verdicts other than expected: none.

| id | target | old | new | -R71 | executed outcome |
|---|---|---|---|---|---|
| T0 | control: cascor's template | PASS | PASS | PASS | rc 0/1 (import ok/fails) |
| T0r | control: template, real python, nothing installed | PASS | PASS | PASS | rc 1, ModuleNotFoundError |
| ML0 | control: juniper-ml's port (flag form) | PASS | PASS | PASS | rc 0/1 |
| CN0 | control: canopy's port | PASS | PASS | PASS | rc 0/1 |
| W0 | control: build window | PASS | PASS | PASS | rc 0, dist/ unchanged |
| **B8-1** | R8-1 x R7-4: `0&>` on the fetch | FAIL | **PASS** | PASS | **BYPASS**: `pip install … juniper-cascor==0.15.0 0` from TestPyPI |
| **B8-2** | R8-1 x R7-4: `0&>>` on the flag form's fetch | FAIL | **PASS** | PASS | **BYPASS**: `pip download … juniper-ml==0.15.0 0` |
| **B8-3** | R8-1 x R7-4: `12&>` on canopy's fetch | FAIL | **PASS** | PASS | **BYPASS**: `pip install … juniper-canopy==0.15.0 12` |
| B8-4 | R8-1 on a later install | PASS | PASS | PASS | also installs PyPI's `9`: within F3's policy (no bypass of it); an unjudged argument |
| **B8-5** | R8-2: `_` as the wheel variable | PASS | **PASS** | PASS | **BYPASS**: `pip install --index-url https://pypi.org/simple/ juniper-ml` (x3, with extras); the TestPyPI wheel never installed |
| B8-6 | R8-2: `_` as the loop variable | PASS | PASS | PASS | 5 failed fetches, no `::error::`, no `exit 1`; the step fails later, at the import (loses the lag error, not the verdict) |
| **B8-7** | R8-3: a later install in a shlex-hidden if | PASS | **PASS** | PASS | **BYPASS**: the install exits 1, the step goes on (rc 0) |
| **B8-8** | R8-3: the import check in a shlex-hidden if | PASS | **PASS** | PASS | **BYPASS**: ModuleNotFoundError, step rc 0 |
| B8-9 | R7-1: a quoted reserved word (`"time" pip …`) | FAIL | FAIL | FAIL | /usr/bin/time ran a PyPI `--force-reinstall` (refused: allow-list, R7-1, F3) |
| B8-10 | R7-1: a quoted digit against `>` | PASS | FAIL | PASS | pip got `0` (refused by R7-1) |
| B8-11 | R7-1's ValueError fallback (`x$[`) | FAIL | FAIL | FAIL | bash syntax error, rc 2 (refused: allow-list cannot read it, bash -n) |
| B8-12 | R7-4: fetch output to `juniper_cascor.txt` | FAIL | PASS | PASS | real python: the import still fails (changes nothing) |
| B8-13 | R7-4: `0>` on the fetch (bash's descriptor) | FAIL | PASS | PASS | pip's arguments unchanged (changes nothing) |
| B8-14 | R7-4: `&>` alone on the fetch | FAIL | PASS | PASS | changes nothing |
| B8-15 | R7-3's message, a no-break-space line | FAIL | FAIL | FAIL | refused; its second message false (N8-1) |
| B8-16 | R8-1 at the build window | FAIL | FAIL | FAIL | twine fails on `0` (refused: not verbatim) |
| B8-17 | R8-1 on the import check | FAIL | FAIL | FAIL | python gets `0`; refused by R4-2 (six shlex words) |

Fix probe (`fixprobe/judge_fix_probe_r8.out`): B8-1, B8-2, B8-3, B8-5, B8-6, B8-7 and B8-8 FAIL. B8-4 and B8-12 to
B8-14 PASS (harmless or within policy). The rest FAIL as before, and the controls PASS.

## Fix pass 6's executed answer to R7-1, re-checked (`rerun/evidence/two_readers_probe_r7.out`)

S1p, S1g and S1g-cn each PASS the checker round 7 reviewed and FAIL the live one. Executed, each runs
`pip install --no-deps --force-reinstall --index-url https://pypi.org/simple/` of the package under test after the
TestPyPI fetch, and exits 0 with the import succeeding. S1 PASSES the reviewed checker but fails at its `grep` (rc 1)
before the hidden install. S2 FAILS both, on the raw pip count. Fix pass 6's account holds.

## The earlier sets, re-EXECUTED (step 4)

| set | driver (my copy) | live checker | executed |
|---|---|---|---|
| round 6's R6-1..R6-6 + T0, T0r, P0, ML0 | `rerun/r6_mutants_rerun.py` | each R6 FAILS (PASSES ebeb7556); controls PASS | yes, as round 6 did; 0 unexpected |
| fix pass 5's N6-1..N6-13 + T0, T0r, P0, W0, C6-1 | `rerun/new_mutants_r6_copy.py` | N6-1, N6-12 PASS (execution changes nothing); the rest FAIL; controls PASS | yes; 0 unexpected |
| fix pass 4's N5-1..N5-16 + controls (CN0r FAILS by design) | `rerun/new_mutants_r5_copy.py` | each N5 FAILS (PASSES c826ab87) | yes; 0 unexpected |
| fix pass 6's N7-1..N7-9 + T0, T0r, ML0, W0, C7-1, C7-2 | `rerun/new_mutants_r7.py` | N7 all FAIL; C7-1, C7-2 FAIL reviewed, PASS live; N7-3 PASSES the R7-1-off mutant | yes; 0 unexpected |
| round 4's M1..M15 + T0, P0, ML0 | round 4's own driver (`util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py mutants`) via `rerun/run_mutants.bash` | M1..M15 FAIL; controls PASS | yes; output equals fix pass 6's (path lengths aside) |
| fix pass 3's N1..N14 + T0, ML0, P0 | `tmp/sweep/cascor-r4/new_mutants_r4.py` via `rerun/run_mutants.bash` | N1..N14 FAIL; controls PASS; 0 unexpected | yes; output equals fix pass 6's (path lengths aside) |
| round 5's R5-1..R5-18 + T0, ML0, S1..S4 | round 5's own `tmp/r5review/s4_new_mutants{,2,3,4,5}.py`, copied to `r5copy/` (only the `--out` guard and the shared module's path moved) | R5-1..R5-18 FAIL; T0, ML0, S3, S4 PASS; S1, S2 FAIL by design | yes; every executed column (round-3 verdict, rc values, R5-13's window, R5-14's run) equals round 5's own output (`r5copy/compare_with_round5.out`) |
| round 2's seven + control | by verdict against round 2's template (`judge_mutants_r7.py`) | 7 FAIL, control PASS | not executed (the brief: by verdict) |

`judge_mutants_r7.py` on every set as its builder wrote it: r5 24/24, r4 18/18, r2 8/8, fp3 17/17, fp4 22/22, r6
10/10, fp5 18/18; 0 mismatches.

## The 15 port simulations (step 3)

Regenerated by round 2's probes into `rerun/port-sim/`. They equal fix pass 5's and fix pass 6's byte for byte
(`rerun/evidence/port_sim_r6_vs_r7.diff` and `port_sim_r7_vs_r8.diff`: 0 lines each). The generator's 25 variants give
19 PASS and 6 FAIL, as the brief expects.

| # | port target | simulation | checker round 7 reviewed | live checker | fix probe |
|---|---|---|---|---|---|
| 1 | juniper-canopy/publish.yml | faithful | PASS | PASS | PASS |
| 2 | juniper-data/publish.yml | faithful | PASS | PASS | PASS |
| 3 | juniper-data-client/publish.yml | faithful | PASS | PASS | PASS |
| 4 | juniper-cascor-client/publish.yml | faithful | PASS | PASS | PASS |
| 5 | juniper-cascor-worker/publish.yml | faithful | PASS | PASS | PASS |
| 6 | juniper-recurrence/publish-recurrence-app.yml | faithful | PASS | PASS | PASS |
| 7 | juniper-recurrence/publish-recurrence-client.yml | faithful | PASS | PASS | PASS |
| 8 | juniper-recurrence/publish-recurrence-model.yml | faithful | PASS | PASS | PASS |
| 9 | juniper-ml/publish.yml | faithful+ml-F2+lag | PASS | PASS | PASS |
| 10 | juniper-ml/publish-ci-tools.yml | faithful | PASS | PASS | PASS |
| 11 | juniper-ml/publish-config-tools.yml | reorder | PASS | PASS | PASS |
| 12 | juniper-ml/publish-doc-tools.yml | reorder | PASS | PASS | PASS |
| 13 | juniper-ml/publish-model-core.yml | faithful | PASS | PASS | PASS |
| 14 | juniper-ml/publish-observability.yml | faithful | PASS | PASS | PASS |
| 15 | juniper-ml/publish-service-core.yml | faithful | PASS | PASS | PASS |

15 of 15 PASS under each (`rerun/evidence/port_sim_table.md`, `fixprobe/port_sim_table_fixprobe.md`).

## Step 3: the re-runs against the Fix pass 6 section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`

`rerun/rerun_all.bash` ran from 03:28:09Z to 03:34:03Z (`rerun/evidence/rerun_all.out`). Its drivers are fix pass 6's,
copied by `mirror_drivers_r8.py` with every output moved to `rerun/`; the substitutions are logged in
`mirror_drivers_r8.out`. Every count equals that section's:

- the checker compiles with `-W error`;
- cascor's three publishers: 3 of 3 from the landing tree, and 3 of 3 from `main` as I fetched it (`main` is now
  `b5b28dc3`, #779; its three files are byte-identical to the landing tree's: `rerun/evidence/fetch_cascor_main.log`);
- the 15-row table: 15 of 15;
- every earlier set by verdict: 0 mismatches;
- the re-executions above: 0 unexpected;
- the over-strict corpora: 46 PASS, OS11 and H19 FAIL, H8 FAIL -> PASS;
- the checker proofs:
  - `checker_proof_r7.py`: 308 of 308;
  - round 2's 43 cases: 43 of 43, no verdict changed and no reason reworded since fix pass 5;
  - `checker_proof_r6.py` on the live checker: 289 of 289;
  - `checker_proof_r7.py` on the reviewed checker: 296 of 308, and the 12 mismatches are exactly T7a, T7b, T7c, T7f,
    L7a, L7b, L7c, B7a, B7b, B7c, E7a and E7b;
- the continuation inventory: 251 runs, 66 continuations, all blank-preceded, none escaped, no odd character;
- the two-readers inventory: 259 commands, 21 pip commands by each reader, 0 disagreements;
- lint (`rerun/evidence/lint.out`): pre-commit 0 failed, 9 passed, 17 skipped (its two fixers skipped; see the first
  section); the hash is unchanged; B914 finds 0 sites; flake8 `--isolated` at 512 columns reports 14 findings, all E203;
  `--help` exits 0.

## Step 2: bash's reading against the checker's readers (`bash_semantics_probe_r8.py`, 79 cases, bash 5.3.9)

Each snippet was run under `bash -e` with logging stand-ins and read by `commands()`, `line_problems`, `lex` with
`structure`, `shell_words` with `pieces`, `operators`, the allow-list and both pip readers. By area:

- **Line joining** (J1-J19): unquoted, tab, abutting, `$\` + `(`, inside double quotes, single quotes, `$(...)` and
  `${...}`; after an escaped backslash; escaped blanks (flush, indented, escaped tab, escaped then unescaped); the
  script's end with and without a newline and with trailing blank lines; beside a comment (spaced, abutting, escaped,
  indented); CRLF.
  - Every divergence is refused, except those the docstring admits: the blank run's length inside quotes (J5) and the
    backslash and newline kept inside single quotes (J6).
  - R7-2's message is true in J10a to J10d.
  - R7-3's messages are true in J12-J14 and J17-J19.
- **Characters** (C1-C9): a NUL, and lines holding only CR, VT, FF or a no-break space; U+2028, a zero-width space, a
  trailing no-break space, NEL. All are refused, by the NUL, line-break or character rule. R7-3's message is false in
  C2 to C5 (N8-1).
- **Comments** (K1-K5, J15): a trailing comment ending in a backslash is refused. A whole-line comment ending in a
  backslash reads alike in bash and `commands()`; neither continues it. `#` inside words and after quotes reads alike.
  `$#` is refused as a form.
- **Quoting** (Q1-Q13): `$'...'`, `$"..."`, `${...}` holding quotes or braces, here-documents and here-strings are all
  refused as forms or as input redirections. Nested `"$( "..." )"` reads alike in `lex` (`shlex` differs, which is
  R7-1's and R8-3's class). Q4 is a `$(...)` inside a double-quoted string inside a `$(...)`, where `_closing` does not
  recurse: `lex` misreads it, and the misreading is refused (a stray `)`). A comment that hides a substitution's close
  (Q11) and a case pattern's `)` (Q12) are refused.
- **Redirections** (R1-R18): a digit against `&>` or `&>>` is **R8-1**. Against `>`, `>&`, `>|` or `<>`, a digit is
  read alike by bash and `lex`. A spaced digit or a quoted one is read alike by bash and `lex`, and R7-1 refuses it.
  `{fd}>`, `>&-`, `&>1`, input redirections and `>&` onto a file are refused, or harmless where admitted.
- **Reserved words** (W1-W5): a quoted `if`, a reserved word after `for`, a brace group, `}` as an argument and `if`
  after an assignment all read alike, or are refused.
- **Tilde** (T1-T4): bash expands `~` in an assignment-like argument (`x=~/a`), and both readers keep it literal. No
  judged decision depends on it: `REQUIREMENT`, F2's exact options and `OPTION` all exclude such a word. Found, with
  no consequence.
- **Beyond the lexer**:
  - bash's `$_` is R8-2: `_` is a word the readers treat as a variable that bash keeps resetting.
  - A shlex-hidden `if` is R8-3, found by executing what the allow-list admits but leaves to the deny rules.

## Step 5: over-strictness (`overstrict_r8.py`, 28 new harmless edits, each executed against its base)

**Admitted: 23 of 28.** Each executed as its base did: the same rc and, apart from the respelled ones (python3, option
order, `--index-url=`, `-i`), the same pip and python calls.

- On the fetch: `>>` to a `.log` (O8-1); the flag form with `>` to a `.log` and `2>&1` (O8-2); `2>&1` alone (O8-3);
  `&>` to a `.log` (O8-27). The checker round 7 reviewed refused all four; fix pass 6 admits them.
- On later installs: `2>&1` (O8-4); output to `install.log` (O8-5); split by a tab continuation (O8-9); split over
  three lines (O8-10).
- Comments: a whole-line comment ending in a backslash (O8-6); a comment after the import (O8-20).
- Echo: text with `: ; -> ( )` and an apostrophe (O8-7); single-quoted text (O8-8); `::notice::` (O8-24).
- Tests and listings: a `[ -s ]` test over three lines (O8-12); `ls -la` of the `--dest` (O8-16).
- Names and options: a lowercase version variable (O8-13); `python3` in the version substitution (O8-15); the fetch's
  options reordered (O8-21), written `--index-url=` (O8-22) or as `-i` (O8-23).
- Spacing and timing: a blank line in the loop (O8-17); `sleep 60` (O8-19); a trailing space (O8-28).

**Refused: 5.**
- O8-11, a one-line `[ -f ]` if: a false reason (N8-2).
- O8-14, `set -e -u` before `cd`: a misleading reason (N8-3).
- O8-18, the retry echo with `>&2`: a false reason (N8-4).
- O8-25 (`printf`) and O8-26 (`set -x`): refused by design, with true reasons.

All five are refused by the checker round 7 reviewed as well, and the fix probe keeps every verdict.

## Checks found sound

- **The interdiff's own changes, read hunk by hunk.**
  - R7-2's and R7-3's message hunks refuse what they refused; only the messages change.
  - `lex_pip_calls` has exactly `pip_calls`'s form with another reader.
  - R7-1's comparison only adds refusals: none in the template, the 15 simulations, the 48 earlier harmless edits or
    this round's 28.
  - R7-5's sentence is true: the template steps are compared as parsed YAML, each action by name.
  - The change that does more than its finding is R7-4's (R8-1).
- **R7-1's rule, against each way its two readers differ.** Each difference refuses:
  - a quoted reserved word (B8-9);
  - a spaced digit (N7-3) and a quoted digit (B8-10);
  - the reserved words only `structure` knows (`fi`, `for`, `done`, `case` and the rest);
  - the `ValueError` fallback is safe: `check_allowlist` lexes the same command and refuses it, and `bash -n` refuses
    it too (B8-11).

  The hole is where both readers share a mistake (R8-1). No whole pip command was found that both readers miss while
  bash runs it: a quoted `time`, a computed name, a glob, a substitution, an alias, a function and `python -m pip` are
  each refused.
- **R7-4's relaxation, apart from R8-1.** Every admitted redirection on the fetch line was executed and changes
  nothing: `>`, `>>`, `&>`, `2>&1`, `0>` and a `.txt` file in the import's directory. A `.py` file target (N7-5), the
  wheel's path (N7-6) and an input redirection stay refused.
- **The remaining `shlex` readers, apart from R8-3.**
  - `own_line`'s operator test reads `skeleton()`, which handles `$(...)` as bash does, so the `#'` trick cannot hide
    a `;`, `&&` or `|` from it.
  - The `pip --version` exemption needs exactly two `shlex` words, so it cannot hide another command.
  - `check_loop`'s fetch line is guarded by R7-1.
- **The messages of R7-2 and R7-3** are true in every case probed (J10a-J10d, J12-J14, J17-J19, the window's N7-9),
  except N8-1.
- **This round changed no existing file** (`untouched_r8.out`). The one file outside `tmp/r8review/` modified after
  03:13:00Z is `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, at 03:13:23Z: the orchestrator's Status section, which I read at
  about 03:15, before my first driver ran at about 03:26. No `__pycache__` directory was created outside
  `tmp/r8review/`. The frozen hashes hold, and the manifest's 6 lines pass `sha256sum -c`.

## Files

**Created**, all under `$W/tmp/r8review/`:
- this report, `ROUND8_REPORT.md`;
- the drivers:
  - `mirror_drivers_r8.py` and its copies in `rerun/` (fix pass 6's drivers, outputs moved; `lint_checker.bash`
    skips the fixers);
  - `bash_semantics_probe_r8.py`, `new_mutants_r8.py`, `overstrict_r8.py`;
  - `run_r5_drivers_r8.bash` and its copies in `r5copy/`;
  - `make_fix_probe_r8.py` and `fixprobe/judge_fix_probe_r8.bash`;
  - `bash52_number_rule.bash`, `untouched_r8.bash`;
  - the shell probes in `quick/`;
- their outputs: `*.out`, `rerun/evidence/`, `r5copy/*.out`, `fixprobe/*.out`, `fixprobe/*.log`, `bash-src/`;
- the generated trees: `rerun/port-sim/`, the `rerun/mutants-*` trees, `rerun/two-readers/`, the `rerun/scratch-*`
  trees, `mutants-r8/`, `overstrict/`, `bash-probe/`, `r5copy/out/`, `fixprobe/port-sim/`, `fixprobe/scratch-proof-r7/`;
- the checker mutants (never deliverables): `rerun/checker_r7_minus_r71.py`, a copy of fix pass 6's, a7622303; and
  `fixprobe/checker_r8_fixprobe.py`, 8a7bee7e.

**Changed:** no existing file.

**Read:**
- `$W/tmp/sweep/ROUND8_BRIEF.md`;
- the Round-7 review table and the Fix pass 6 section of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`;
- `$W/tmp/r7review/ROUND7_REPORT.md`;
- the checker, its interdiff `$W/tmp/sweep/checker-r7/checker_r6_to_r7.diff`, and the template;
- fix pass 6's drivers in `$W/tmp/sweep/checker-r7/`, fix pass 5's `bash_semantics_probe_r6.py` in
  `$W/tmp/sweep/checker-r6/`, and round 5's drivers in `$W/tmp/r5review/`, all read-only.
