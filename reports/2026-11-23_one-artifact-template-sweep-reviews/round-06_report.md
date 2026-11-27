# Round-6 adversarial review of fix pass 4 (checker `2026-11-23_publish_port_template_identity.py`)

Mirror of the final report. Reviewer: session `d935c226` round-6 subagent. 2026-11-24 ~01:15Z. Bash on host 5.3.9;
corroborated on 3.2.57 (GitHub ubuntu-latest runs 5.2; the behaviours relied on are longstanding, not version-specific).

Checker under review sha256 `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8` (matches the frozen input and
`checker_r5_as_delivered.py`); interdiff sha256 `bc14fa9f…` (matches); manifest `sha256sum -c` OK.

## Verdict: 1 BLOCKER (MAJOR defensible), 0 other MAJOR, 0 MINOR, 2 NIT.

The BLOCKER is a lexer/`commands()` vs bash divergence that lets an install step hide an arbitrary `$(...)` command
substitution (a pypi.org `pip install`, a file write, anything) from EVERY layer of the checker. It PASSES; executed,
the hidden command runs. This trips the stopping rule: fix pass 5 + another round before any port is built.

### BLOCKER — `commands()` joins a line-continuation with a space where bash deletes it; a `$\<newline>(` smuggles a command substitution into a "plain" echo

`commands()` :416-431 (join at **:425** `pending += line[:-1].strip() + " "`); gap in `line_problems` :677-702;
carriers `plain_echo` :934-946 and the raw-pip exclusion :1293; false docstring claims :83 and :114.

Scenario. A port's install step holds, inside a double-quoted echo (which the checker drops from the pip scan as inert):

    echo "verifying the import $\
    (pip install --no-deps --force-reinstall --index-url https://pypi.org/simple/ juniper-cascor==0.14.0 > /dev/null)"

`commands()` joins the continued line with a SPACE -> `echo "verifying the import $ (pip install ... )"`. Inside
double quotes a `$` followed by a space is a literal `$`, and `(` `)` are literal, so `plain_echo` is True, there are
no allow-list refusals, and `line_problems` is empty. bash instead DELETES the `\<newline>` with no separator ->
`echo "...$(pip install ...)"` -> the command substitution runs. The smuggled command is invisible to `check_allowlist`
(it reads the space-joined text), to `pip_calls`/`RAW_PIP` (the echo is plain, so excluded :1293), to `check_constructs`
(the `(` is inside quotes, no operator), and to `bash -n` (valid). Not pip-specific: any `$(cmd)` hides this way.

Evidence (`tmp/r6review/verify_roundtrip.out`, `r6_mutants_final.out`): the dumped mutant the checker judges is
byte-identical to the script executed; it is valid portable YAML (double-quoted scalar, no NUL). Executed under `bash -e`
with round 5's stand-ins, the hidden `pip install --index-url https://pypi.org/simple/ juniper-cascor==0.14.0` ran
(R6-1); the checker returned PASS. This defeats the job's whole anti-target-squatting purpose (template lines 323-328:
"TestPyPI ONLY ... no pypi.org fallback"). Rounds 4/5 rated exactly this executed-hidden-pip class a bypass.

Six faithful executed mutants in this class (all PASS the live checker):

| id | carrier / target | verdict | executed outcome |
|---|---|---|---|
| R6-1 | `$\<newline>(` in a main-path double-quoted echo | PASS | hidden `pip install ... pypi.org juniper-cascor==0.14.0` ran |
| R6-2 | `$\<newline>(echo __version__=0 > juniper_cascor.py)` | PASS | real `python -c` import PASSED with nothing installed (rc=0; control T0r rc=1) |
| R6-3 | continuation then `$\<newline>{x@P}` (round 5's R5-1 behind a continuation) | PASS | hidden pypi.org install ran |
| R6-4 | continuation in the retry-loop echo, index-lag path | PASS | hidden pypi.org install ran on the first-fetch-lag retry |
| R6-5 | `$<NUL>(` in a double-quoted echo (bash drops NUL) | PASS | hidden pypi.org install ran (PyYAML round-trips NUL; a strict YAML parser may reject it — lower confidence) |
| R6-6 | `\<NUL>"` splitting an echo into three commands | PASS | hidden pypi.org install ran (same NUL caveat) |

Root cause: line :425 inserts a space; bash deletes `\<newline>` with no separator. They agree only when a separator
exists on at least one side of the join; they diverge when the char before `\` and the first char of the next line are
both non-whitespace (`$` abutting `(`). `line_problems` flags four continuation divergences but not this one.
R6-2 shows it is broader than pip: it spoofs the import itself (a planted module + rc 0 with nothing installed). R6-3
shows the continuation re-opens the very class fix pass 4's R5-F1 narrowing was meant to close.

Docstring overclaim (part of this finding): :83 "fix pass 4's allow-list, below, is what closes the class" and :114
"the allow-list is what closes R4-3's class" are false — the class is reachable through the `$(...)` body again via this
divergence. "What this cannot see" (:174-186) names only Python-level and action-level gaps; it does not disclose any
shell-lexing/`commands()` divergence.

Fix. The divergence is in `commands()` (shared, pre-existing) but `line_problems` is fix pass 4's reconciliation of it
with bash, so fix it there. Build the bash join (delete `\<newline>`, keep the next line's leading whitespace) and the
`commands()` join (strip + one space) and refuse when they tokenize differently; or, minimal and sufficient for every
port, refuse a continuation unless the backslash is preceded by whitespace (or the continued line begins with
whitespace). All 66 continuation backslashes in the template + 15 ports have whitespace before `\` and none abut on both
sides (`check_continuations.out`), so this rejects R6-1..R6-4 while passing all 15 ports. Also reject a NUL byte
anywhere in a run script (same class; bash drops it), and correct the :83/:114 "closes the class" claims.

### NIT 1 — a trailing inline comment on a command is refused (documented corner)

`check_allowlist` comment handling + the python -c end rule; OS11 in `tmp/r6review/overstrict.out`. A legitimate port
could write `python -c "..."  # done`; the checker refuses it ("holds a comment after a command"). Fix pass 4 already
lists this under over-strict corners ("a trailing # comment"), and it hits none of the 15 ports (all 15 PASS), so it is
not over-strictness against a real port. Could be admitted (strip a trailing unquoted `#...` outside `$( )`), or left.

### NIT 2 — `${NAME##literal}`/`${NAME%...}` refused

`PREFIX_REMOVAL` :184 admits only a single `#`. `${RELEASE_TAG##v}` (valid, equivalent) would be refused. No port uses
it (all use `${RELEASE_TAG#v}`). Cosmetic; note or widen the pattern.

## Over-strictness (step 5): no finding against a real port

All 15 ports PASS. Harmless edits of a passing port (`tmp/r6review/overstrict.out`): comment line (OS1), extra plain
echo (OS2), standalone `[ -f "${WHEEL}" ]` (OS3), a later install redirected to `${RUNNER_TEMP}/*.log` (OS4), renamed
lowercase var (OS5), `set -eu`/`set -euo pipefail` (OS6/7), `python3` for the final check (OS8), `echo >&2` (OS9),
`ls -la "${RUNNER_TEMP}"` (OS10), a bare console script (OS12) — all PASS. Only OS11 (trailing inline comment) refused
(NIT 1).

## Checks found sound

- 15/15 port simulations PASS (`port_sim_table.md`); regenerated with round 2's probes byte-identical to fix pass 3's
  AND fix pass 4's (0 diff lines); 25-variant generator keeps 19 PASS / 6 FAIL.
- cascor's three publishers 3/3 PASS.
- Every earlier mutant re-judged FAILs, every control PASSes: round 5 R5-1..R5-18 + controls (24/24), round 4 M1..M15 +
  controls (18/18), round 2's 7 + control (8/8), fix pass 3 N1..N14 + controls (17/17); 0 mismatches
  (`judge_mutants.md`). Regenerated by their own drivers: M1..M15 all FAIL, N1..N14 all FAIL, 0 unexpected.
- Fix pass 4's N5-1..N5-16: each PASSES the reviewed checker and FAILS the live one, 16 executed bypasses closed, 0
  unexpected (`new_mutants_r5.out`) — the rules fix pass 4 added for set/`[ ]`/redirect/`${#}`/cd/sed/env-key/checkout/
  build-runner/`$[`/backtick-in-`$()`/ASSIGNABLE all work as claimed. CN0r (the widened-checkout baseline) FAILS as
  designed.
- R5-F7 relaxations: O1 and O2 now PASS, O3 still PASS (`overstrict.log`); `own_line` and `test_only` spot-checked —
  a redirected-and-piped later install (O5c) and a `{ }`-grouped one (O5d) still FAIL.
- `checker_proof_r5.py` 261/261; round 2's 43 cases 43/43 (every verdict kept, reasons reworded only).
- Allow-list shapes spot-checked and sound: `SPARSE_PATH` admits all 15 ports' paths and no traversal; `REDIRECT_TARGET`
  admits `.log/.txt` under `${RUNNER_TEMP}` and `&1/&2`/`/dev/null` only (no `.py`); `set`/`[ ]`/`sed`/`grep`/`head`/
  `mktemp`/`seq` shapes; env-key rules (`SHELL_ENV`, non-identifier, `BASH_FUNC_`, non-mapping, build-job BUILD_PYTHON_ENV).
- Lint: compile clean (no warnings); pre-commit 11 passed / 0 failed with the file left unchanged (sha256
  `ebeb7556…` before and after); B914 0 sites; `--help` exit 0.

Outputs mirrored under `tmp/r6review/`: `show_installs.*`, `probe_*.{py,out}`, `verify_roundtrip.*`, `inspect_r6_1.*`,
`check_continuations.*`, `overstrict.*`, `r6_mutants.py`, `r6_mutants_final.out`, `r6_mutants_R6-4_lag.out`,
`mutants/*.yml`, and `rerun/` (redirected copies of fix pass 4's drivers + `evidence/`).
