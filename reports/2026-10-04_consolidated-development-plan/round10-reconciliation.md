# Round 10 — reconciliation of three lanes into plan v1.10.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.9.0 (sha256 prefix `ffeca51e2d86255f`) → v1.10.0 (`9ff76f5b43fbaa64`).
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, v7 (`8dc176bcf25a5b62`) → `46093b326112bdd2`: docstring only, no rule changed.
  - `util/ad-hoc/2026-10-05_gate_regression.py`, from 180 cases (`c772b21ca53db611`) to 181 (`f17a29fa37d4b045`): the line read's contract check.
  - `util/ad-hoc/2026-10-05_masked_finding_shape.py`, from `7decf250a3ae68ba` to `48a962b516c58db3`: the read given a stated contract.
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`, from `b7823b6400d30e2b` to `0dcbd4a701bc2b65`: a malformed `--since` refused.
  - All three lanes read the same five frozen hashes at the start, middle and end of their windows.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 10 was briefed on round 9's corrections and the drift v1.9.0 took in (`round9-reconciliation.md`), with the plan's gate-severity rule and its ending rule (its Validation record).
- **Lane reports** (all in this directory; R10A-, R10B1- and R10B2- IDs below are theirs):
  - `round10-laneA-reprobe.md`: 0 BLOCKER, 1 MAJOR, 7 MINOR, 6 NIT;
  - `round10-laneB1-safety.md`: 0 BLOCKER, 3 MAJOR, 10 MINOR, 3 NIT;
  - `round10-laneB2-schedule.md`: 0 BLOCKER, 2 MAJOR, 15 MINOR, 7 NIT.
- **Window**:
  - The lanes ran on 2026-10-08 from 14:10Z: Lane B2 until about 14:43Z, Lane A until about 14:52Z, Lane B1 until about 14:56Z.
  - The reconciliation ran from 14:44Z until 15:29Z, when v1.10.0 was frozen. It was cut by the session's usage limit at about 15:10Z, wrote `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-08_consolidated-development-plan-finish-round-10-reconcile-then-round-11-and-pr.md`, and resumed in the same session.
- **Method**: read-only, except the plan, the four tools above, the handoff and this file.
  - GitHub REST reads were GETs only, by `gh api` and the census tool. Git read with `show origin/main:<path>` and `show 0fca7ada:<path>`.
  - Tool changes were staged and tested on scratch copies while Lane B1 still read the frozen ones, and copied in after it finished. Gate and tool runs used synthetic inputs and scratch copies in the session scratchpad. Real-file findings were read only as masked shapes.
  - No secret was read or printed.
- **ID coverage**: v1.9 → v1.10 drops no ID (381 in each), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan, this file, the three round-10 lane reports and the handoff pass markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No plan line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| The local-branch ports are different diffs from what merged | R10B2-01 | `gh api …/juniper-recurrence/compare/be081fae...main` and `…/compare/juniper-recurrence-v0.5.0...be081fae`; the plan's Wave 1, exit, item 3 and H-22 lines | `main` 5 ahead of `be081fae`, through `routers/_common.py`, `crossval.py`, `predict.py` and `data.py`; `be081fae` 19 ahead of the tag, 26 files. No line validated a port. **Confirmed** |
| ml#2183 published transcript-extracted text that no item reads | R10B2-02, R10B1-01 | `gh api …/pulls/2183/files` (paginated); `git show 0fca7ada:` of two validator reports, counting markers | 170 files: 1 note, 5 handoffs, 28 under `reports/e2e-canopy-2026-09-02/`, 136 under `util/ad-hoc/`. The round-6 validator report holds 3 "last-assistant-text" markers, the round-1 report 22 transcript mentions. **Confirmed** |
| The line read misses a value below a name that has trailing text | R10A-01, R10B1-02 | Two synthetic files (a Kubernetes entry with a trailing comment; a bold label with a qualifier), values of class `<random>`, through the frozen gate and read | Gate exit 0, no finding; the read listed both name lines and printed no line below either. **Confirmed** |
| KEY mode prints a value's words after multibyte text | R10A-02 | Synthetic line: twelve em dashes, a passphrase assignment, a value of class `<words>`; the gate's KEY (column 39 for byte offset 37), then KEY mode | The value's words printed in clear (count 1). **Confirmed** |
| The census tool reads a malformed `--since` as "no merges" | R10A-07 | `--since notatime` on the frozen tool | Exit 0, no UNREADABLE line, an empty merges section. **Confirmed** |
| ml#2182's body and the fleet's state | R10B2-03, -04, -10, -24 | GETs of ml#2182 (its body names #2124, #2127, #2171 and `worktree_cleanup`), ml#2147 (closed 13:41:28Z, unmerged) and ml#2177 (open Cursor draft since 2026-10-05T22:26:35Z, Yamaguchi docs) | **Confirmed** |
| The data fix-forward's distance and overlap | R10B2-16 | `gh api …/juniper-data/compare/main...94ce8b1f`; data#454's and data#475's files | Diverged, 2 ahead, 22 behind, 15 files; data#454 edits `juniper_data/api/app.py`, data#475 `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, all three among them. **Confirmed** |
| F-CANOPY-063 is a test quote, half declined | R10B2-08 | `git show origin/main:` the canopy ledger, its F-CANOPY-063 rows | "a canopy test quotes cascor's refusal"; "filed as F-CANOPY-063, P2, OPEN; one half declined". **Confirmed** |

## The tools, tested

Gitleaks v8.30.1. All inputs are synthetic except rows 3 and 4.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 32/32; the repo config zero-rule; exit 1 | Canary 32 of 32. Default rules alone 3 of 32; B9-class rules alone 31 of 32; `.gitleaks.toml` 0 of 32, ZERO-RULE; exit 1 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases (`f17a29fa37d4b045`) | Each as its case states | **181 of 181 as expected**, exit 0, finished 2026-10-08T15:13Z |
| 2g | The read's contract (new). Values below their names: after a trailing comment, after a qualifier, below two comment lines, below two keys between a Name and its Value, below an argv item with a comment. Forms that were not listed: a passphrase label in two words, a table row naming the settings key in three, a label naming the web credential in three, a quoted `pass:` argument, `openssl`'s `-k`. A one-case lowercase value. Four values that printed in clear (after an id and a `_secret_` segment, after a lowercase API-key prefix, after an upper-case token prefix, a value of ordinary words before its name). KEY mode after twelve em dashes | Each value printed below its name or listed, random-looking; no planted value in `--names` or `--all` output; KEY mode masks the value | As expected. The same check fails on round 9's read (a planted value printed) |
| 3 | This plan's PR files, as scratch copies | 0 | Exit 0 with the one accepted key (`round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`). The widened read listed 245 lines in the 61 files and printed 743 below them. Every listed line in a file changed since round 9's read (110) and every value-shaped line below a name (60: three masked runs or fewer) was read, and none holds a credential-shaped value. An `--all` pass counted 732 random-looking tokens: 717 paths, file names or dated names, and 15 others, each identified by masked shape and context: six file names, six environment-variable names, two flat credential names in the read's own source, and one branch-like identifier that three public handoffs on `origin/main` already carry |
| 4 | The 40 real files of round 6's false-positive sample | Workable | 49 findings in 13 files, the same 49 keys as v6 |
| 5 | The census tool, with `--since notatime`, `--since '2026-10-08 13:38:00'` and `--since 2026-10-08T13:38:00` | Exit 3 before any read | Exit 3 for each, and nothing read |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.10.0 (plan) or the tools |
| --- | --- | --- | --- |
| R10A-01 The read printed nothing below a name followed by any text | MAJOR | Accepted (re-derived; with R10B1-02, R10B1-03) | The read prints the five non-blank lines under every listed line; its docstring states the contract, and row 2g tests it. Plan: XC-PRESERVE's read rule; the gate-severity rule now tests listing against the contract (Validation record) |
| R10A-02 KEY mode's window shifted after multibyte text | MINOR | Accepted (re-derived; fixed and tested) | KEY mode converts the gate's byte column to a character offset (`char_col`), and masks every value; row 2g |
| R10A-03 The config-as-text figure was v6's | MINOR | Accepted (with R10B1-12) | XC-LEAKS note 3: 44 under v7 (43 and 1), 32 under the final v6, 28 under v5 |
| R10A-04 Five of ml#2182's nine backup suites named | MINOR | Accepted (with R10B2-03) | XC-FLEET's carried row and Tier-1 item 1: nine suites from #2121, #2124, #2127, #2138, #2140, #2159 and #2171; launcher and preflight suites from five PRs |
| R10A-05 The suite counts | MINOR | Accepted (with R10B2-05) | §10's P1 list: `AGENTS.md` 169, `ci.yml` and `docs/REFERENCE.md` 198; count `ci.yml` |
| R10A-06 The record's listed lines are 71 | MINOR | Accepted | S0.3: 69 before round 9's widening, 71 after, more since round 10's; gates v6 and v7 the same 16 keys |
| R10A-07 The census tool took a malformed `--since` | MINOR | Accepted (re-derived; fixed and tested) | It refuses a value that is not ISO 8601 with a zone (row 5). Plan: the instruments |
| R10A-08 §9's push row lost the named-line read | MINOR | Accepted (with R10B1-10, R10B2-13) | §9: the named-line read with the five lines below, and `--all` for backup-arc or transcript text |
| R10A-09 "Wave 2" for ml#2182's consequence | NIT | Accepted | The header's drift line: Wave 1's Tier-1 item 1 |
| R10A-10 ml#2182 written as open | NIT | Accepted (with R10B1-15, R10B2-20) | Tier-1 item 1, §8's rows and §10 say merged; XC-PRESERVE's row r routing |
| R10A-11 Bare IDs, a matrix and a list | NIT | Accepted (with R10B2-22) | Filenames in XC-PRESERVE's gate bullets, S0.11 and the instruments; the matrix in P2's lane; `round9-reconciliation.md` moved to the reconciliations list |
| R10A-12 H-23's `sqlite3` comparison | NIT | Accepted (with R10B1-09, R10B2-14) | As R10B1-09 |
| R10A-13 Round 9's record: case counts and times | NIT | Accepted; recorded here, not in place | In `round9-reconciliation.md`: R9A-03's "179 cases" was an intermediate build, 180 final; R9B1-01's "two must-pass" is one case of two lines; R9B1-11 added five must-pass cases, and its reconciliation one more. Its drift times are merge-commit times; GitHub's `merged_at` are ml#2183 12:55:46Z, ml#2182 13:37:40Z, cascor#709 12:51:18Z and data#475 13:41:49Z |
| R10A-14 The instruments' provenance | NIT | Accepted | The gate: "six earlier versions", Related to round 10; the regression: round 9's 17 cases and round 10's check named |
| R10B1-01 No read of ml#2183's published files | MAJOR | Accepted (re-derived; with R10B2-02) | New S0.13 before sitting item 8: the gate, `--names` and `--all` over ml#2183's files, merge message, PR body and comments; keys and counts recorded; any value to XC-CRED; A10's input. Wave 2's Phase 11 block says what round 9 covered |
| R10B1-02 Layouts with the value below, missed by both instruments | MAJOR | Accepted (re-derived; with R10A-01) | As R10A-01; (b) and (d) sit within five lines. XC-PRESERVE: changed hunks with ten context lines (`git diff -U10`) |
| R10B1-03 Names in separate words and a quoted `pass:`, not listed | MAJOR | Accepted (fixed and tested) | The read: blanks as name separators, a quoted `pass:`, `-k` and `-kfile` on a line naming openssl; row 2g. The gate: listed as limits |
| R10B1-04 Round 9's skips swallow three variants | MINOR | Accepted (listed) | The gate's docstring and XC-PRESERVE list the `:` swallow, the JSON `\n` path value, the `$`-led mixed-case value and a value in braces. No rule changed; the read lists each |
| R10B1-05 The lowercase skip takes one run of any length | MINOR | Accepted (listed; read fixed) | XC-PRESERVE and the docstring list it; the read now flags a one-case letter run of 20+ at 3.3 bits |
| R10B1-06 Over-reach on argv, tuples and a compose item | MINOR | Accepted (listed) | The docstring and XC-PRESERVE; `--accept` after reading |
| R10B1-07 Values printed in clear | MINOR | Accepted (fixed and tested) | The read masks every value; only credential words stay in clear inside a name; S0.3 records counts, never output |
| R10B1-08 The telemetry check looked at the locks only | MINOR | Accepted | S0.11: the trio's environments (FastAPI 0.137.0, no OpenTelemetry); tests under each lock and in each environment; the trigger widened to an SDK, a provider or an exporter |
| R10B1-09 H-23's recipe | MINOR | Accepted (with R10A-12, R10B2-14) | H-23: DEFECT-3 is a POST to a paused server; the `sqlite3` edit only where P0 restores the databases, read back, P1-08 checks it; job 2 stays paused until AC-4's first drill or the remedy |
| R10B1-10 §9's push row | MINOR | Accepted (with R10A-08) | As R10A-08 |
| R10B1-11 The export would be unscannable | MINOR | Accepted | XC-LEAKS note 1: one decoded raw-text file per message, body or comment; annotated tags' messages |
| R10B1-12 The config-as-text figure | MINOR | Accepted (with R10A-03) | As R10A-03 |
| R10B1-13 H-22's escape wording | MINOR | Accepted | H-22: L308's wording; the read's markers list such lines |
| R10B1-14 Tag names and issue text | NIT | Accepted | XC-PRESERVE's scan item and the gate's docstring |
| R10B1-15 Row r's routing | NIT | Accepted (with R10A-10) | XC-PRESERVE: row r went in through ml#2183; S0.13 and A10 |
| R10B1-16 Row q's read | NIT | Accepted | XC-PRESERVE: this PR gets the named-line read and every random-looking line of an `--all` pass |
| R10B2-01 The ports are never validated | MAJOR | Accepted (re-derived) | Wave 1: every local port passes the fix's S0.11 tests on its commit, DSNs empty, before the restart that loads it; item 3 names the tag's branch; the exit and H-22 count a release or a validated port |
| R10B2-02 No read of ml#2183 | MAJOR | Accepted (re-derived; with R10B1-01) | As R10B1-01 |
| R10B2-03 The backup suites | MINOR | Accepted (with R10A-04) | As R10A-04 |
| R10B2-04 §8's ml rows and S0.8 | MINOR | Accepted (re-derived) | §8: ml#2182 (merged) and the suites pinning `run_suite.py`, `run_experiment.py` and the launchers; the docs row says merged; S0.8 works on current `main` |
| R10B2-05 The suite counts | MINOR | Accepted (with R10A-05) | As R10A-05 |
| R10B2-06 The FAQ was discharged | MINOR | Accepted | §10's P2 list |
| R10B2-07 F-CANOPY-063's item is done | MINOR | Accepted | Dropped from P2's lane. The optional note in P3's lane was not added |
| R10B2-08 P2-04's scope and order | MINOR | Accepted (re-derived) | The P2 ledger: P2-04 is the test quote alone, and P2-03 and P2-04 (T1) come ahead of `…phase11-landed.md`'s item 4; §8's canopy row drops P2-04 |
| R10B2-09 A10's limb had no options | MINOR | Accepted | A10: options and a recommendation, on S0.13's read; Unblocks names XC-CRED; sitting item 8's list names S0.13 |
| R10B2-10 ml#2177 was missing | MINOR | Accepted (re-derived) | §3's table, S0.7's checks and A10 |
| R10B2-11 W5.10 asked nowhere under W5.11 | MINOR | Accepted | A9 asks W5.10's acceptance and placement in their own right |
| R10B2-12 The exit's count assumed one route | MINOR | Accepted | §7.1's rounds note: under the after-P3-05 route, 11 items, 22 rounds, 110 runs |
| R10B2-13 §9's push row | MINOR | Accepted (with R10A-08) | As R10A-08 |
| R10B2-14 H-23's recipe | MINOR | Accepted (with R10B1-09) | As R10B1-09 |
| R10B2-15 P2-06 had no round or host slot | MINOR | Accepted | §7.1 item 18's place; §7.2's timing-sensitive list |
| R10B2-16 The data fix-forward | MINOR | Accepted (re-derived) | §2's P3 row and §10's P3 list. §8's data row unchanged: no other item in flight edits `api/app.py` |
| R10B2-17 Vehicle (b)'s host legs | MINOR | Accepted | Wave 1: the local route under (b) too; A1 |
| R10B2-18 Appendix B rows 23 and 25 | NIT | Accepted | As proposed |
| R10B2-19 P1's Wave 2 lane; P2-05 | NIT | Accepted | P1's lane names row k's archive PR; Appendix A's P2-05 notes its trigger half |
| R10B2-20 Method rounds; row r | NIT | Accepted (with R10B1-15) | "rounds 1–10"; row r |
| R10B2-21 The fleet bullets | NIT | Accepted | The Overview, XC-FLEET's paragraph and §10's canopy bullet |
| R10B2-22 Naming | NIT | Accepted (with R10A-11) | S0.11's IDs, its lock facts' source, the Phase 11 block's sources |
| R10B2-23 R-DATA carries data#454 | NIT | Accepted | §5's R-DATA row; its `[Unreleased]` entry is owed |
| R10B2-24 The cleanup tool's empty list | NIT | Accepted (re-derived) | XC-CLEAN |

**Totals:** 54 findings (0 BLOCKER, 6 MAJOR, 32 MINOR, 16 NIT), all accepted. R10A-13 corrects `round9-reconciliation.md`; it is recorded here, not in place. With six MAJORs, round 11 runs.

## Drift taken in

None. Lane A's census at 14:24Z and 14:48Z, Lane B2's at 14:30Z and the reconciler's at 15:21Z (`--since 2026-10-08T14:02:00Z`, exit 0, no UNREADABLE line) found no merge to `main` in the nine repositories since 14:02Z, 22 open PRs, all juniper-ml Cursor drafts, and none elsewhere, and the newest Releases and PyPI's versions unchanged since 2026-09-24. A10's six rows were open drafts (Lane B2's GETs, 14:12Z–14:35Z: ml#2181 mergeable and behind, the other five dirty), and ml#2177 was open. v1.10.0 takes in no drift.

## Unresolved dissent

None. The lanes overlapped on seven themes and agreed on each: the read (R10A-01, R10B1-02, R10B1-03), ml#2183 (R10B1-01, R10B2-02), H-23 (R10A-12, R10B1-09, R10B2-14), §9's push row (R10A-08, R10B1-10, R10B2-13), ml#2182's suites (R10A-04, R10B2-03), the suite counts (R10A-05, R10B2-05) and the config-as-text figure (R10A-03, R10B1-12).

## Slips on the lanes' constraints

None reached a repository or printed a real value. The owner may want to know:

- **Lane A**: one command refused by the guard and re-issued plainly; two inline Python reads of one PR-file line outside the line read, printing only counts and indices; scratch copies of real repository files made with `git archive`, `tar`, `cp` and redirects; the shared `JuniperCascor1` Python run without `PYTHONDONTWRITEBYTECODE` (no bytecode was written); and KEY mode writing a synthetic value's words to a scratch file, confirmed by count.
- **Lane B1**: one loop refused by the guard and re-run plainly; two files copied into its scratch with `cp` (the scanner tarball, checked against its pin, and the gate's generated `b9.toml`); a `find` that listed three paths in Lane A's scratch, none opened; and one command's output (a public round-9 report) saved by the harness to a tool-result file, not read.
- **Lane B2**: two commands refused by the guard and re-issued plainly; one scratch copy of ml#2182's public PR body written by shell redirection.
- **The reconciler**: three commands refused by the guard and re-issued plainly; plan edits made by inline Python fed on standard input (no script file); the usage-limit cut and its handoff, above.

## What this reconciliation cannot support

- That round 10's corrections, the read's contract or the tools' changes introduced no new error. Round 11 is briefed on exactly that.
- That the gate, or the gate with the line read, catches every way a secret can be written: the contract states what the read covers, and the docstrings list what both miss.
- That ml#2183's files hold no credential. S0.13 owes that read.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after 15:29Z on 2026-10-08.
