# Round 6 — Lane A1 (the pre-push gate, measured)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-6 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round6-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - the frozen gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py` (v3) in `--scan-dir` mode, on synthetic inputs and on scratch copies of tracked files, with `--workdir` always under the session scratchpad, and the pinned gitleaks v8.30.1 that the tool downloads;
  - read-only `gh api` GETs of gitleaks v8.30.1 `sources/file.go`, `sources/files.go`, `detect/detect.go` and `config/gitleaks.toml`;
  - UTC window 2026-10-05T13:11:31Z–14:00:47Z for the measurements; the final self-gate and the end readings at 14:10:35Z;
  - sha256 of the tool, at start `5ed0da7dd84e85234452a1e6b8f80889a69953e6279d3b694b41fb28f7c39b1c` and at end (14:00:47Z and 14:10:35Z) the same;
  - sha256 of the plan, at start `17a9c12de47992c28d7523c99ba7df43ca5607c7549651c1546e10e9fc2a44d4` and at end (14:00:47Z and 14:10:35Z) the same. Neither file was edited.
- Entry point: the gate (tool v3) and its claims in `reports/2026-10-04_consolidated-development-plan/round5-reconciliation.md` (the v3 test table, the R5A-01/R5A-02/R5A-04 dispositions and the known-limits bullet), with the method in `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` L275–291.
- Sample:
  - 187 gate runs (87 single runs, the last two self-gates of this report, and 50 concurrent pairs); 133 behaved as the tool's documentation predicts and 54 did not. A run counts as unexpected when its exit code differs, or, for line- and count-sensitive cases, its lines or counts. The 3 format-matrix runs exited 2 as expected; their per-format misses are reported separately.
  - 75 formats in 3 value classes (random alphanumeric, word passphrase, base64), 15 empty-key layouts, and 4 key generators × 150 keys.
  - 40 real files for false positives, plus a 76-file supplement and the plan PR's 37 files.
- Location abbreviations: "tool" is `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`; "plan" is `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`; "R5" is `round5-reconciliation.md`; "B9" is row B9 of `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` (L227).
- Every planted value was invented for this lane. No value is quoted below; inputs name the value class only (`<random>`, `<words>`, `<base64>`).

## Findings

| ID | Severity | Location (tool "tool Lnn", or plan "Lnnn") | Claim or behaviour | Measured (input → exit code, findings) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R6A1-01 | BLOCKER | tool L140, L124–127; plan L280–282 | `\s*` after `[:=]` crosses lines and matches never overlap: an empty B9-named key swallows the next line, and the path allowlist (on the whole match) drops it | 11 layouts exit 0, canary 11/11 (tests 3–7, 9, 12, 13, 15, 16), e.g. empty `PASSPHRASE_FILE=` then `PASSPHRASE=<random>` (note 1) | `[ \t]*` for `\s*`/`\s+` at L140, L145, L150; anchor the allowlist to the key; add the layouts to the canary |
| R6A1-02 | BLOCKER | tool L133–134, L145; plan L280–281 | `--settings-encryption-key=<key>`, the ecosystem's form (8 repo lines; 1 uses a space), matches no B9-class rule; only the default `generic-api-key` can | Caught of 150 keys per generator: base64-48 143, base64-32 142, urlsafe 145, hex 150 (test 35); word keys missed in 3 of 4 formats; B9 misses it too (note 2) | Separator-agnostic `_NAMES` (`settings[-_]encryption[-_]key`, …); plant a `+`-leading key in the canary |
| R6A1-03 | MAJOR | tool L306–307, L372–377, L42–44; plan L276 | Keyed `PATH:LINE:RULE` by start line only, one key accepts several findings and outlives an edit; "a stale list cannot pass silently" is false | Accepting the reported empty line passes the value below (tests 10, 11, 32); one accept passes 2 values (31, 33) or an edited line (34); real files: 8 of 22 keys cover 2–3 | Key by `START-END` and a hash of those staged lines; refuse an accept covering 2+ findings; fix L42–44, plan L276 |
| R6A1-04 | MAJOR | tool L223, L30–32; plan L285 | `os.walk` has no `onerror`, so an unreadable subdirectory is skipped without a word | Secret in a mode-000 directory (U01), a 0311 directory (U02) or below a 000 directory (U04): exit 0. A 0444 directory (U03): exit 3 | Pass an `onerror` that records a problem (exit 3); refuse any directory without read and search permission |
| R6A1-05 | MAJOR | tool L64–65; R5 L98; plan L281 | R5 L98 calls the docstring's list the known limits; many B9-named shapes fall outside it | 29 of 75 formats missed in every class (test 36); realistic here and missed by B9 too: bold labels (43 lines), prose, 3 table shapes, `Name`/`Value` JSON, `Option` rows, argv items, annotated defaults (note 3) | List them in L64–65 and the plan; add rules for Name/Value pairs, pipe rows, bold labels, cells right of a B9 name; R5 L98 "the" → "some" |
| R6A1-06 | MINOR | tool L209–216, L30–32; plan L285 | Any `FF FE` or `FE FF` prefix is decoded as UTF-16, and the NUL check covers the UTF-8 branch only | `FF FE` or `FE FF` followed by a plain ASCII secret: exit 0 (E01, E02). UTF-32LE with BOM: 0 (E03). UTF-16 holding U+0000: not refused (E04, exit 2) | Refuse UTF-16 and UTF-32 (exit 3), or refuse decoded U+0000 and also stage the raw bytes when they decode as UTF-8 |
| R6A1-07 | MINOR | tool L201–205, L268–270, L297–301, L343–350 | Runs that share `--workdir` share staging, canary, report and binary | Secret run and clean run of equal staged size, started 0–1.6 s apart, 33 trials: the secret run exited 0 ×21, 2 ×8, 3 ×4; the clean run reported the other's secret ×4. Unequal sizes, 17 trials: never 0 | A per-run `mkdtemp(dir=workdir)` for everything but the tarball, or an exclusive `flock`; document one run per workdir |
| R6A1-08 | MINOR | tool L106 | A bare value may not start with `#` | `PASSPHRASE=#<value>` missed in all 3 value classes. B9's literal `NAME=` form would match it: the only regression against B9 found | Allow `#` directly after `=`; keep the comment guard for `= #` |
| R6A1-09 | MINOR | tool L33–35; plan L286 | "No line is ever cut" holds, but a match that spans two lines can be cut at a part boundary | YAML `passphrase:` with the value on the next line: exit 2 inside one part, exit 0 when the 60,000-byte boundary falls between them (test 30) | Document it; after R6A1-01's fix the form is never matched, so list it as a known limit |
| R6A1-10 | MINOR | tool L114–121 | Whole-value placeholder shapes skip real values, and common expansions still flag | Real-looking values shaped `<v>`, `your_backup_key_v`, `%v%`, `$` + lower case and digits, `$` + upper case and digits: 6 of 6 skipped (PH, P01). 14 of 30 real-file findings are `$VAR`, `${VAR}` or `<…>` forms with extra characters | Add the residual to the known limits; widen the expansion shapes after checking the forms the real files use |
| R6A1-11 | NIT | tool L279–281 | A part that starts with a binary signature fails closed, but the error names no cause | 17 of 17 text inputs starting `MZ`, `%PDF`, `%!`, `SQLi` and the like, or with `ustar` at byte 257: exit 3, "scanner read 0 bytes … something was skipped" | On a mismatch, rerun at debug level and name the source file of each "skipping binary file" part |

Notes on the findings:

1. **R6A1-01.** The trigger uses this ecosystem's own names: `PASSPHRASE_FILE=` appears in 2 design notes and `DUPLICATI_WEB_CREDENTIAL_FILE` in 4 code files. The swallowed line is never matched on its own, because gitleaks' matches do not overlap. The default `generic-api-key` rule crosses the line the same way and then drops the result on a stopword, so even a random `DUPLICATI_WEB_CREDENTIAL` value exits 0 (test 15). Of the path-suffix layouts only test 8 was caught, and only by that default rule.
2. **R6A1-02.** All 20 misses are explained: 12 keys start with `+` or `/`, which the default rule's value class cannot start with, and 8 contain one of its 1,446 stopwords. That is about 1 key in 20 for the base64 generators the backup arc uses (`openssl rand -base64 48`, 32 random bytes in base64). The same separator gap covers `DUPLICATI__WEBSERVICE_PASSWORD` and camelCase keys, where word values are missed.
3. **R6A1-05.** Prose: "is", "set to", "rotated from". Tables: a multi-word name cell, the value in a third column, a note after the value. The `Name`/`Value` settings shape is the one `util/ad-hoc/yamaguchi_*.py` reads and writes; 14 lines in 12 files mention the `Option` table; 3 files hold argv items, and 3 hold annotated passphrase or credential names.

## Gate tests

| # | Input (synthetic) | Expected | Observed |
| --- | --- | --- | --- |
| 1 | A clean markdown file | 0 | 0 |
| 2 | `.env` with `PASSPHRASE=<random>` | 2 | 2, line 1 |
| 3 | F01 `.env`: empty `PASSPHRASE_FILE=`, then `PASSPHRASE=<random>` | 2 | **0** |
| 4 | F02 YAML: empty `passphrase_file:`, then `passphrase: <random>` | 2 | **0** |
| 5 | F03 nested YAML: empty `passphrase_path:`, then `tier2_passphrase: <random>` | 2 | **0** |
| 6 | F04: test 3 with two blank lines between | 2 | **0** |
| 7 | F05, one shell line: empty `PASSPHRASE_FILE=`, `PASSPHRASE=<random>`, then the backup script | 2 | **0** |
| 8 | F06: empty `SETTINGS_ENCRYPTION_KEY_FILE=`, then the key as `<base64>` | 2 | 2 (generic-api-key only) |
| 9 | F07 YAML: empty `webservice-password-file:`, then `webservice-password: <words>` | 2 | **0** |
| 10 | F08 `.env`: empty `PASSPHRASE=`, then `TIER2_PASSPHRASE=<random>` | 2 at line 2 | 2 at line 1 only |
| 11 | F09 YAML: empty `passphrase:`, then `tier2_passphrase: <random>` | 2 at line 3 | 2 at line 2 only |
| 12 | F10 YAML: empty `passphrase_dir:`, then a quoted `<words>` with spaces | 2 | **0** |
| 13 | F11: a value that itself contains `_dir=` | 2 | **0** (contrived) |
| 14 | F12, fenced CLI: `--passphrase=` ends a line, `--webservice-password=<random>` starts the next | 2 at the value line | 2: B9 rule at the empty line, generic-api-key at the value line |
| 15 | F13, F14: empty `DUPLICATI_WEB_CREDENTIAL_FILE=`, then `DUPLICATI_WEB_CREDENTIAL=<random>` or `<words>` | 2, 2 | **0**, **0** |
| 16 | F15, contract-style env: comment, empty `PASSPHRASE_FILE=`, `PASSPHRASE=<words>`, a tier-2 file path | 2 | **0** |
| 17 | M01–M17: UTF-8 text starting with a binary signature (`MZ`, `%PDF`, `%!`, `SQLi`, `{\rtf`, `BZh`, `PK` 03 04, `FWS`, `CWS`, `LZIP`, `MSCF`, `!<arch>`, DEL `ELF`), one at a fixed offset (`ustar`@257, `DICM`@128, `CD001`@32769), or a 2-part file whose part 2 starts `MZ` | 3 (or 2) | 3 in 17 of 17 |
| 18 | E01, E02: bytes `FF FE` or `FE FF`, then plain ASCII `PASSPHRASE=<random>` | 2 or 3 | **0**, **0** |
| 19 | E03: UTF-32LE with BOM | 2 or 3 | **0** |
| 20 | E04: UTF-16LE with BOM, a U+0000 line and a secret | 3 (docstring: NUL refused) | 2, not refused |
| 21 | E05 UTF-8 BOM; E08 mixed CRLF and LF; E10 UTF-16LE BOM with CRLF; E11 UTF-16BE BOM | 2 at the planted line | as expected |
| 22 | E06 UTF-16 without BOM; E07 Latin-1; E18 odd-length UTF-16 | 3 | 3 |
| 23 | E09: CR-only line endings, secrets on CR-lines 2 and 4 | 2 | 2, both at line 1 |
| 24 | E12–E16, E19, E20: zero-byte files, names like `00001-000.txt`, a 60-deep path, space, unicode and newline in names, U+2028, a BOM-only file | as documented | as expected |
| 25 | E17: a non-UTF-8 byte in a file name, file holds a secret | 2 or 3 | 3 (`UnicodeEncodeError` while printing) |
| 26 | U01 mode-000 subdirectory; U02 mode 0311; U04 a mode-000 directory two levels up | 3 | **0**, **0**, **0** |
| 27 | U03: mode-0444 subdirectory | 3 | 3 |
| 28 | L01: 3-part file, secrets at L1, L751 (last of part 0), L752 (first of part 1), L1053, L1354 (no final newline) | 2 at those lines | exact |
| 29 | L02: one 60,000-byte line; L03: 60,001 bytes | 2; 3 | 2; 3 |
| 30 | YAML `passphrase:`, value on the next line; without and with a part boundary between | 2; 2 | 2; **0** |
| 31 | A01: two values on one line, one `--accept cmd.sh:1:juniper-b9-assignment` | 2, one open | **0**, both ACCEPTED |
| 32 | F08 and F09 with `--accept` of the reported (empty) line | 2 | **0**, **0** |
| 33 | E09 with `--accept mac.env:1:juniper-b9-assignment` | 2 | **0** |
| 34 | ST1: the accept for a reviewed `${PASSPHRASE:?…}` line, reused after the line becomes `PASSPHRASE=<random>` | 0, then 2 | 0, then **0** |
| 35 | K1–K4: 150 files each of `ExecStart=… --settings-encryption-key=<key>`, keys shaped like `openssl rand -base64 48`, 32 random bytes in base64, `secrets.token_urlsafe(32)`, `openssl rand -hex 32` | 150 each | 143, 142, 145, 150 |
| 36 | X: 75 formats × 3 value classes | every format caught | 38 caught in all classes; 29 in none; 8 caught only for random and base64 values |
| 37 | PH, P01: real-looking values in whole-value placeholder shapes | skipped (by design) | skipped, 6 of 6 |
| 38 | Concurrent pair, shared `--workdir`, equal staged size, 33 offsets over 0–1.6 s | secret run never 0; clean run never 2 | secret run 0 ×21, 2 ×8, 3 ×4; clean run 2 ×4 |
| 39 | As test 38, unequal sizes, 17 offsets | secret run never 0 | 3 ×14, 2 ×3 |
| 40 | W1: `--workdir` inside `--scan-dir` | 3 | 3 |
| 41 | The plan PR's 37 untracked files (round 5's case 22, round-6 reports excluded) | 0 | 0 |
| 42 | This report, as a self-gate before and after its last edits | 0, 0 | 0, 0 |

Test 36 in detail:

- **Missed in every value class (29).**
  - Shell: writes into B2's `web-credential` file by `printf` or heredoc, with no name; a here-string; `aescrypt -p`; `openssl -pass pass:`; a `#`-leading value; a flag and its value split by a line continuation.
  - Python: `getenv` and `environ.get` defaults; annotated module and dataclass defaults; argv items; the Duplicati settings dict and its `st["Value"]` assignment; a comparison.
  - Data: a YAML block scalar; Duplicati job-export JSON (pretty-printed, and with `--passphrase` as the name); sqlite3 output and an SQL dump of `Option`.
  - Markdown: the prose, bold-label and table shapes in R6A1-05 (9).
- **Caught only for random and base64 values (8):** `DUPLICATI__WEBSERVICE_PASSWORD` in env, compose and systemd; camelCase helm keys (`webservicePassword`, `settingsEncryptionKey`); the server API login body; and `--settings-encryption-key` in a unit, a CLI line and an argv list.

## False positives on real files

- Sample: 40 tracked files by the brief's patterns (13 backup and Duplicati notes, 7 backup handoffs, 8 backup scripts and units, 12 Duplicati ad-hoc tools; 2.15 MB), copied by content. One gate run: exit 2, **30 findings in 11 files**, all from the B9-class scan (27 `juniper-b9-assignment`, 3 `juniper-b9-table-cell`); the default rules found nothing. They need **22 distinct `--accept` keys**, 8 of which cover 2 or 3 findings.
- Supplement: all 76 files the patterns match gave 38 findings in 15 files (28 keys), again none from the default rules. The plan PR's own 37 files gave 0.
- Shape only (length, character classes, entropy, markers; no matched value was read or printed): 14 shell or template expansions with extra characters (8 `$VAR` or `${VAR}`, 2 `<…>`, 1 command substitution, 3 other), 12 word-joined placeholder phrases, 4 code tokens. None is random-looking (a mixed-case alphanumeric token of 16+ characters with entropy ≥ 4.0). Nothing looked like a real credential.
- Workability: about 22 reviewed accepts for a PR that spans the backup corpus, a handful for an ordinary PR, so the volume is workable. The meaning is not safe: one key covers several findings, a swallowed value is reported at the wrong line, and a key outlives an edit (R6A1-03).

| File | Line (rule; `a` = `juniper-b9-assignment`, `t` = `juniper-b9-table-cell`) |
| --- | --- |
| `notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md` | 191 a |
| `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` | 372 a ×2, 401 a, 411 a, 745 t |
| `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md` | 1029 a, 1124 a ×3, 1125 a ×2, 1134 a |
| `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` | 2229 t |
| `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` | 1471 a, 2429 a |
| `util/ad-hoc/2026-09-22_reconcile_backup_design.py` | 1457 t |
| `util/ad-hoc/duplicati_build_fresh_job.py` | 178 a |
| `util/ad-hoc/duplicati_drill_run.py` | 139 a, 204 a |
| `util/ad-hoc/duplicati_first_backup.bash` | 67 a ×2, 68 a ×2 |
| `util/ad-hoc/duplicati_gpg_macro_repro.bash` | 118 a, 207 a |
| `util/ad-hoc/duplicati_verify_passphrase.bash` | 53 a ×2, 54 a ×2 |
| Supplement only: `util/ad-hoc/duplicati_dlist_crosscheck.py`, `duplicati_dlist_query.py`, `duplicati_drill_fresh.py`, `duplicati_purge_dryrun.bash` | 197 a; 131 a; 508 a, 542 a; 145 a ×2, 146 a ×2 |

## Checked and holds (short)

- The byte-count check catches every scanner-side skip I could trigger: 17 of 17 binary-signature parts exit 3 (gitleaks counts bytes per yielded fragment, `detect/detect.go`, so a sniffed-out part is never counted). At default log level the only "scanned ~N bytes" text is the INF summary line.
- Line mapping is exact across part boundaries (L1, L751, L752, L1053, L1354), for CRLF, UTF-16 with CRLF, and a UTF-8 BOM. The 60,000-byte line bound behaves as documented.
- Refusals hold for UTF-16 without BOM, Latin-1, odd-length UTF-16, a `--workdir` nested in `--scan-dir`, a 0444 subdirectory. The report and exit-code agreement checks caught cross-run swaps ("scanner wrote no report", "exit code 0 disagrees with 2 reported finding(s)").
- Unequal-size concurrent runs never exited 0. The canary passed 11/11 in every run, including every exit-0 failure above: it shows the rules load, not that the target scan worked.
- 38 of 75 formats are caught in every value class, including the prefix, suffix, quoted-key, `environ[…]`, spaced-flag and two-column-table forms R5 says v3 added. Round 5's case 22 reproduces: 0 findings on the plan PR's 37 files.

## Could not check

- CI's gitleaks 8.24.3, history scans (XC-LEAKS step 1) and `--config` probe mode beyond the canary.
- Whether the real-file findings hold a real value: classified by shape only, by design; no matched value was read.
- Exact RE2 behaviour in my shape classifier (Python `re`, used only to describe findings the gate reported).
- Platforms other than Linux x86-64; very large or memory-exhausting inputs; how often sessions run gates concurrently with a shared `--workdir`.
- Lane A2's and Lane A3's reports, which exist in the same directory and were not read.

## What this report cannot support

- That shapes outside the 75 formats and 15 empty-key layouts are caught.
- That the 38 real-file findings hold no credential; the judgment rests on shape, not content.
- That fixing these findings makes the gate correct; each fix needs its own re-test, and R6A1-01's fix changes which two-line forms match at all.
- Host state, repository history, CI behaviour, or anything after 2026-10-05T14:10:35Z.
