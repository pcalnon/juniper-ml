# Round 5 — reconciliation of two lanes into plan v1.5.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.4.0 (sha256 prefix `2cc51727a5c2b272`) → v1.5.0.
  - The scan tool `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py` (round 4's version, sha256 prefix `a248352b9ffe8a0b`), rewritten a third time.
  - Both lanes read the same hashes at the start and end of their windows.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 5 was briefed on round 4's corrections only.
- **Lane reports** (both in this directory): `round5-laneA-reprobe.md` (0 BLOCKER, 3 MAJOR, 7 MINOR, 4 NIT) and `round5-laneB-attack.md` (0 BLOCKER, 5 MAJOR, 10 MINOR, 5 NIT).
- **Re-derivations and tool tests**: 2026-10-05, 12:52Z–13:10Z, read-only except the rewritten tool. GitHub REST was read at gitleaks v8.30.1 and gitleaks-action `e0c47f4f`, and the scanner was run on synthetic inputs in the session scratchpad. Lane A's own test cases in that scratchpad were reused as the regression suite. No secret was read or printed.
- **ID coverage**: v1.0 → v1.5 drops no ID, and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan passes markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| The scanner skips files the old tool counted | R5A-01 | The pinned scanner's `dir --help`; a debug-level run | `--follow-symlinks` is off by default, and `--max-archive-depth` defaults to 0. The log line `scanned ~N bytes` reports exactly what was read: 261 for a 261-byte file. **Confirmed**, and that line became the tool's coverage check |
| How the scanner picks the secret from a multi-group regex | — (design) | gitleaks `detect/detect.go` L522–540 at v8.30.1 | With `secretGroup` unset, the first non-empty capture group is the secret. So one rule can carry the double-quoted, single-quoted and bare value forms |
| An inline allow marker can be disarmed | R5B-02 | The scanner's `--ignore-gitleaks-allow` flag (`dir --help`) | It exists. The tool passes it, so the marker in prose is no longer a finding (the old tool flagged its own documentation) |
| CI's scanner version can be pinned | R5B-13 | gitleaks-action `src/index.js` L138 at `e0c47f4f` | `GITLEAKS_VERSION` is read from the environment, with a default of 8.24.3. **Confirmed**: the step-3 PRs can set 8.30.1 |
| `from None` keeps the original on `__context__` | R5A-08, R5B-08 | Both lanes' Python checks, and sentry-sdk's `walk_exception_chain` (`utils.py` L818–821, read in round 4) | The suppress-aware walk skips it, and a cause-and-context walk finds it. The test is now specified as sentry-sdk's walk |
| The escalator puts these rounds in the top cell | R5A-03, R5B-01 | `…CONSENSUS-PROCEDURE.md` L81–98 (read in round 4) | L87–93 list "a fix or revert hangs on it" as an escalator that "moves the cell up". Medium × High becomes the top cell: 3+ Lane A, 2+ Lane B, at least two iterations. **Confirmed**; `round4-reconciliation.md` had written "escalates" and kept the medium cell |

## The rewritten gate, tested (v3)

Gitleaks v8.30.1. Cases 2–14 are Lane A's own directories in the session scratchpad; the others were built for this round. All inputs are synthetic.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 11/11; repo config zero-rule; exit 1 | Canary 11/11. Default rules alone: 2 of 11 classes. B9-class rules alone: 10 of 11. `.gitleaks.toml`: 0 of 11, ZERO-RULE. Exit 1 |
| 2 | Lane A's 37-format matrix | Every file reported | 42 findings in 37 of 37 files, exit 2 (round 5's tool: 17 findings, 20 files missed) |
| 3 | Lane A's 14 realistic misses (quoted keys, spaced flag, suffixes, `$`/`#`/`true`/`false` values, table cell) | 14/14 | 14 of 14, exit 2 |
| 4–6 | A symlinked file alone; beside a clean file; a symlinked directory | Exit 3 | Exit 3, naming the symlink, in all three |
| 7–8 | A gzip archive; a file with a SQLite header | Exit 3 | Exit 3: "not UTF-8 or BOM-marked UTF-16 text", in both |
| 9 | UTF-16LE with a BOM | Decoded and reported | Reported, exit 2 |
| 10 | CRLF line endings | Reported | Reported at the right line, exit 2 |
| 11 | 28,000 planted lines in chunk-length files without blank lines | 28,000 | 28,000 distinct lines reported, exit 2 (round 5's tool: 27,989) |
| 12 | A 30 MB file, planted at line 400,001 | Reported at that line | `big.log:400001`, exit 2 |
| 13 | A `.gitleaks.toml` beside a planted file | Reported | Reported, exit 2 |
| 14 | Every case of the allow marker (exact, upper, mixed) | All reported | 4 of 4, exit 2 |
| 15 | Lane A's `.gitleaksignore` baseline PR (XC-LEAKS note 2's shape) | Clean | 0 findings, exit 0. The file is scanned as text and never honoured |
| 16 | A mode-000 file beside a clean one | Exit 3 | `PermissionError`, exit 3 |
| 17 | `--workdir` naming a file | Exit 3 | Exit 3 (round 5's tool: exit 1) |
| 18 | `--config X --scan-dir ''` | Exit 3 | Usage error, exit 3 (round 5's tool: exit 0) |
| 19 | Three findings, each `--accept`ed after review | Exit 0, all three printed as accepted | Exit 0 |
| 20 | An `--accept` naming no finding | Exit 3 | "stale or mistyped", exit 3 |
| 21 | A tampered tarball in the workdir | Exit 3 | sha256 mismatch, exit 3 |
| 22 | This plan's own PR: 36 files | Clean | 0 findings, exit 0 (round 5's tool: 4 self-findings) |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.5.0 (plan) or v3 (tool) |
| --- | --- | --- | --- |
| R5A-01 The scanner skips what the tool counted | MAJOR | Accepted (re-derived; fixed and tested) | Tool: refuses symlinks, non-regular files, non-text files, NULs and lines over 60,000 bytes; stages flat text parts; requires the scanner's byte count to equal the staged bytes. Plan: XC-PRESERVE method |
| R5A-02 Formats juniper-ml writes get past B9 and the interim rule | MAJOR | Accepted (fixed and tested) | Tool: names with prefixes and `_`/`-` suffixes; quoted keys; `]` (Python `environ[…]`); quoted values with spaces; a `#` after the first character; spaced CLI flags; table cells (entropy above 3.0). Plan: XC-PRESERVE method; XC-LEAKS step 3 carries the B9-class rules, and the widening against B9 is stated |
| R5A-03 The rounds belong in the top cell | MAJOR | Accepted (re-derived) | §7.1: at least five agents per round, at least 22 rounds and 110 runs, in two batches, at one to two rounds a day; the one de-escalator noted. Scope & Timeframe: three to five weeks |
| R5A-04 The placeholder allowlist matched prefixes | MINOR | Accepted (fixed) | Tool: every shape is anchored at both ends, `$VAR` is matched as all-upper or all-lower only, and only `${VAR:-}` (empty default) is skipped. The canary plants a mixed-case `$` value. Plan: XC-PRESERVE method |
| R5A-05 The default global allowlist reaches the B9 rule | MINOR | Accepted (fixed) | Tool: two scans, the B9-class rules without `[extend]`; the canary plants a "true…" value. Plan: XC-PRESERVE; XC-LEAKS note 3 records the gap CI keeps |
| R5A-06 The scanner's read chunks cut long lines | MINOR | Accepted (fixed) | Tool: parts under 60,000 bytes (case 11). Plan: XC-PRESERVE; XC-LEAKS note 3 for CI |
| R5A-07 The `.gitleaksignore` option cannot pass | MINOR | Accepted (with R5B-03) | Tool: no refusal; a `.gitleaksignore` is scanned as text and never honoured (case 15). Plan: XC-LEAKS note 2 recommends the baseline and states what the fingerprints publish |
| R5A-08 The test fails its own fix | MINOR | Accepted (with R5B-08) | S0.11: each test walks the chain as sentry-sdk and `traceback` do |
| R5A-09 Sentry also receives the key as log records | MINOR | Accepted (with R5B-07) | Overview 2; H-22; the metric counts 5 paths; XC-SENTRY (a) must cover Sentry Logs |
| R5A-10 Recurrence's image gets the fix at its Release | MINOR | Accepted (with R5B-11) | §5 vehicle row; Wave 1's recurrence route names juniper-deploy's pin and a restart |
| R5A-11 Two exits outside the table | NIT | Accepted (fixed) | Tool: workdir set-up inside the `try`; an empty `--scan-dir` is a usage error (cases 17, 18) |
| R5A-12 The pin trusted a self-written stamp | NIT | Accepted (fixed) | Tool: keeps the tarball, re-verifies it against the pin on every run, and re-extracts the binary (case 21) |
| R5A-13 Round-5 files listed before they existed | NIT | Accepted (with R5B-09) | "Changed by this plan" lists round 5's files, which now exist, and marks round 6's as planned |
| R5A-14 L32 ends with W1.14 | NIT | Accepted | Group B's P12 line notes that W1.14 is A1's |
| R5B-01 Round sizing | MAJOR | Accepted (with R5A-03) | As R5A-03 |
| R5B-02 The plan's PR fails its own gate | MAJOR | Accepted (fixed and tested) | Tool: `--ignore-gitleaks-allow` instead of reporting the marker; its own source assembles the names and canary lines from parts; `--accept PATH:LINE:RULE` for reviewed false positives. This PR passes with 0 findings (case 22). Plan: XC-PRESERVE ("the PR body lists each accepted finding") |
| R5B-03 Note 2 against the gate | MAJOR | Accepted (with R5A-07) | As R5A-07; "stop the scan" now records the lost coverage |
| R5B-04 The cascor fix had no vehicle | MAJOR | Accepted | §5: R-CASCOR carries and waits for it; the vehicle row is recurrence's alone. S0.11 adds a cascor bullet. §9 splits the trio and image routes. Wave 1 delivery |
| R5B-05 A per-session cap is not account-wide | MAJOR | Accepted | §1.3 states the gap (21–24 subagents across sessions). The proposed enforcement: no other session launches subagents while a round runs, P12's task-executors included. §6 A7 rules it, and §7.1's pace assumes it |
| R5B-06 Prep held the host steps | MINOR | Accepted | Wave 0: step 1 holds only the host-gating rulings (A2, A5's O13), which need no prep. A1, A6 and A7 move to step 8. S0.9, S0.10 and S0.12 come before step 8, and the CV-blowup review does not gate the sitting |
| R5B-07 Five paths, not four | MINOR | Accepted (with R5A-09) | Metric |
| R5B-08 `from None` and the test | MINOR | Accepted (with R5A-08) | S0.11 |
| R5B-09 Files listed before they existed | MINOR | Accepted (with R5A-13) | "Changed by this plan" |
| R5B-10 The Wave 1 exit omitted delivery | MINOR | Accepted | Exit: R-DC-PATCH cut, the trio upgraded and restarted, and the recurrence fix released under vehicle (a). The mid-wave sitting holds the trio's upgrade |
| R5B-11 Independent routes forced into series | MINOR | Accepted (with R5A-10) | Wave 1's "F-S10 delivery" is three routes (trio, images, recurrence) after a common start. R-OBS-SC's lock PRs pick up the patch only if it is on PyPI first |
| R5B-12 Prefix-anchored placeholders | MINOR | Accepted (with R5A-04) | As R5A-04 |
| R5B-13 Scanner versions differ | MINOR | Accepted (re-derived) | XC-LEAKS step 1 runs both versions; step 3 sets `GITLEAKS_VERSION: 8.30.1` |
| R5B-14 ml's dispatch rescans history | MINOR | Accepted | XC-LEAKS note 2 covers every repository whose gitleaks job rescans history (data's `schedule`, ml's `workflow_dispatch`; canopy's and deploy's are checked in their PRs) |
| R5B-15 Round 5 was under-sized | MINOR | Accepted | Deviations record rounds 2–5's sizes. Round 6 runs at the top cell |
| R5B-16 "§5's delivery steps" | NIT | Accepted | XC-P12 now points to §4 Wave 1's routes |
| R5B-17 Recurrence's `pyproject.toml` paths | NIT | Accepted | `juniper-recurrence/pyproject.toml` at Wave 1 data step 3 and in the round-4 record |
| R5B-18 `map_data_error` returns; the routes raise | NIT | Accepted | S0.11 names the three raise sites and their WARNING lines |
| R5B-19 One bound for the timeframe | NIT | Accepted | Three to five weeks, in both Scope & Timeframe and §7.1 |
| R5B-20 A9's DC-0.6 source and Unblocks | NIT | Accepted | A9 cites §5 and A2-02, and adds P5 W10 |

## Unresolved dissent

None. The lanes overlapped on six findings, and they agreed on every one.

## What this reconciliation cannot support

- That round 5's corrections, or the third version of the tool, introduced no new error. Round 6 is briefed on exactly that, at the procedure's full size.
- That the gate catches every way a secret can be written. Its docstring lists the known limits: values under 8 characters, a multi-word unquoted value, names outside the B9 set, and a low-entropy table cell.
- Host state; whether any repository's history holds real hits; Sentry's server-side scrubbing.
- Any state after 2026-10-05T13:10Z.
