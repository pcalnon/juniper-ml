# Round 6 — reconciliation of three lanes into plan v1.6.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.5.0 (sha256 prefix `17a9c12de47992c2`) → v1.6.0.
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, v3 (sha256 prefix `5ed0da7dd84e8523`), rewritten a fourth time as v4 (sha256 prefix `7445505b5a1117eb`).
  - New: `util/ad-hoc/2026-10-05_gate_regression.py` (sha256 prefix `33fa27d7c6eb6d71`), which replays the cases that broke v1–v3.
  - All three lanes read the same plan hash at the start and end of their windows, and Lane A1 the same gate hash.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 6 was briefed on round 5's corrections only.
- **Lane reports** (all in this directory):
  - `round6-laneA1-gate.md`: 2 BLOCKER, 3 MAJOR, 5 MINOR, 1 NIT;
  - `round6-laneA2-claims.md`: 0 BLOCKER, 1 MAJOR, 8 MINOR, 2 NIT;
  - `round6-laneA3-consistency.md`: 0 BLOCKER, 1 MAJOR, 16 MINOR, 10 NIT.
- **What did not run: the Lane B batch.** Round 6 was planned as three Lane A, then two Lane B, under the three-agent cap. The Lane A batch's corrections superseded v1.5.0 before Lane B could launch, so a Lane B on v1.5.0 would have attacked a dead artifact. Round 7 runs the Lane B pair on v1.6.0, with one Lane A re-deriving these corrections (the plan's Deviations).
- **Window**: 2026-10-05, 14:10Z–21:45Z, including a pause for a usage-limit cut. The session wrote `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-05_consolidated-development-plan-finish-v1.6-round-7-then-pr.md` at the cut and resumed from it, re-reading every lane report and the whole plan rather than relying on memory.
- **Method**: read-only, except the rewritten gate and the plan. GitHub REST reads were GETs only. Gate runs used synthetic inputs and scratch copies of tracked files in the session scratchpad. No secret was read or printed.
- **ID coverage**: v1.0 → v1.6 and v1.5 → v1.6 drop no ID, and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan passes markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| The trio runs editable installs of the primary checkouts | R6A2-01 | `JuniperCascor1`'s `site-packages`: the `__editable__` finders | `juniper_data_client` 0.5.0 and `juniper_cascor` 0.11.0 both map into the primary checkouts of `juniper-data-client` and `juniper-cascor`. **Confirmed**. Recurrence 0.5.0 and its model and client are editable there too |
| Which phase each backup ruling gates | R6A2-06, R6A3-07, R6A3-08 | `…RECOVERY-PLAN.md` §6.6 (L295–310); `extraction-P1-backup.md` §2 | O-1: Phase D step 9. O-2: D step 7. O-7: D, and P1-10 as the STOP's exit condition (the extraction). O-8, O-12: B. O-10: C. O-13, O-14: D. O-5, O-9: E. **Confirmed** |
| The procedure's cells and escalators | R6A2-07, R6A2-08 | `…CONSENSUS-PROCEDURE.md` L84–97 | Medium × High is 2 Lane A + 1–2 Lane B (L84); the top cell is L85. The escalators are L89–94: an instrument "wrong before" at L91, a universal at L92, "a fix or revert" at L93. The de-escalator needs "a different instrument" (L96–97). **Confirmed** |
| History rescans on `workflow_dispatch` | R6A2-04, R6A3-02 | gitleaks-action `src/index.js` at `e0c47f4f` (L138, L176–181); the four `ci.yml` files on `main` | The action defaults `GITLEAKS_VERSION` to 8.24.3, and it scans on `workflow_dispatch` or `schedule`. `workflow_dispatch` triggers: ml L55, data L51 (plus `schedule` L49), canopy L53, deploy L41. Canopy's step guard skips `repository_dispatch` only (L508). **Confirmed** |
| CI's git mode reads hunks whole | R6A2-05 | gitleaks v8.30.1 `sources/git.go` L393–404; `sources/file.go` L21 | Git mode yields each hunk's added lines as one fragment (`textFragment.Raw(gitdiff.OpAdd)`); `defaultBufferSize = 100 * 1_000` belongs to the file source. **Confirmed**: the chunk limit binds only the local gate |
| Cascor's further relays; the loader must raise | R6A2-03 | cascor `main`: `manager.py` L189–195, L3361; `app.py` L589–591. data-client `client.py` L88, L213 | A loader returning `None` lets the client re-read the raw variable. **Confirmed** |
| P3-08 does not wait on P3-05 | R6A3-14 | `extraction-P3-defect-register.md` L64 | **Confirmed** |
| Twin owner questions | R6A3-09 | `extraction-P12-equities.md` §2 (O8 and O12 are P2's; P4-Q6 is P4 item 6); `extraction-P4-release-P11-k8s.md` L116 (D-4/5/6), L120 (D-10), L124 (D-14); `extraction-P6-perf.md` OD-11; `extraction-P5-partition.md` OD-9 | **Confirmed**. Each is now asked once, with its twin named |
| Script and handoff names | R6A3-11, R6A3-17, R6A3-24 | `ls` of each path in this worktree and in `HO/HANDOFF_2026-09/` | All exist. The P12 handoff `HANDOFF_2026-10-04_recurrence-equities-p0-executed-go-verdict-p1-next.md` exists on `origin/main` (`1dea3b39`), not at this worktree's base, so `tests/test_thread_handoff_archive.py` fails locally on it. The PR branches from `main` |

## The rewritten gate, tested (v4)

Gitleaks v8.30.1; all inputs synthetic except the last two rows.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 20/20; the repo config zero-rule; exit 1 | Canary 20 of 20. Default rules alone: 3 of 20 classes. B9-class rules alone: 19 of 20. `.gitleaks.toml`: 0 of 20, ZERO-RULE. Exit 1 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 89 cases | Each as its case states | **89 of 89 as expected**, exit 0. Groups below |
| 2a | 65 formats that must be found (exit 2), including Lane A1's: the 7 absorption layouts (`absorb-*`, `empty-then-tier2`, `value-holds-dir-eq`); the settings flag with `+`, `/` and a space; Name/Value, Value/Name, `Option` and sqlite rows, argv; bold labels and multi-word table cells; `#`-leading values; BOM-prefixed ASCII, UTF-32, CR-only and CRLF | 2 | 2 in all 65 |
| 2b | 4 that must pass (exit 0): whole-value placeholders, path names, a `.gitleaksignore` baseline, the allow marker in prose | 0 | 0 in all 4 |
| 2c | 18 that must refuse (exit 3): missing and empty directories; symlinked file and directory; gzip, SQLite and a PDF signature on text; UTF-16 without a BOM, Latin-1, UTF-16 holding U+0000; mode-000 file, mode-000 and mode-0311 directories; a 25,000-byte line; `--workdir` naming a file; an empty `--scan-dir`; an unpinned release; a stale `--accept` | 3 | 3 in all 18 |
| 2d | Accept keys: two findings on one line | Two keys; one accepted → 2; both → 0; after an edit → 3 | As expected |
| 2e | Concurrency: a secret run and a same-size clean run sharing one `--workdir`, 5 trials | The secret run never 0; the clean run never 2 | As expected in all 5 |
| 3 | This plan's PR files, as scratch copies | 0 | 0 findings, exit 0, on all 43 files at v1.6.0's freeze. It is re-run on the final set before the push |
| 4 | The 40 real files of Lane A1's false-positive sample | Workable | 37 findings in 12 files (34 assignment, 3 pipe-cell; none from the default rules), each with its own key. v3 gave 30 in 11 |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.6.0 (plan) or v4 (gate) |
| --- | --- | --- | --- |
| R6A1-01 Rules crossed a line, so an empty `_FILE=` swallowed the secret below | BLOCKER | Accepted (fixed and tested) | Gate: rule separators are `[ \t]`, never `\s`; only the Name/Value rules span whitespace, at most 40 characters. Cases 2a's absorption layouts. Plan: XC-PRESERVE method |
| R6A1-02 `--settings-encryption-key=` matched no B9-class rule | BLOCKER | Accepted (fixed and tested) | Gate: names are separator-agnostic (`SETTINGS[_-]*ENCRYPTION[_-]*KEY`, …), and a CLI-flag rule takes `=` or a space; the canary plants a `+`-leading key. Plan: XC-PRESERVE method |
| R6A1-03 Accept keys covered several findings and outlived an edit | MAJOR | Accepted (fixed and tested) | Gate: KEY is `PATH:LINE:COLUMN:RULE:HASH`, the hash covering the matched line(s); one key per finding; an `--accept` that matches nothing exits 3 (case 2d). Plan: XC-PRESERVE method |
| R6A1-04 An unreadable directory was skipped silently | MAJOR | Accepted (fixed and tested) | Gate: `os.walk` has an `onerror` that refuses (exit 3), and every directory needs read and search permission (case 2c) |
| R6A1-05 Many B9-named shapes fell outside the listed limits | MAJOR | Accepted (fixed in part; the rest listed) | Gate: rules for Name/Value pairs in both orders, pipe rows (`(?im)`), bold labels, and quoted pairs (argv, SQL `Option` rows); the docstring's known limits name prose, a value on another line, and a value not in the cell after its name. Plan: XC-PRESERVE method. Round 5's "the known limits" (`round5-reconciliation.md` L98) should read "some known limits"; corrected here, not in place |
| R6A1-06 BOM-prefixed ASCII passed; NUL was checked only in UTF-8 | MINOR | Accepted (fixed and tested) | Gate: text behind a UTF-16 or UTF-32 BOM is staged decoded and, when the bytes after the BOM are UTF-8, as UTF-8 too; a decoded U+0000 is refused |
| R6A1-07 Runs sharing a `--workdir` shared their state | MINOR | Accepted (fixed and tested) | Gate: a per-run `mkdtemp` for everything but the verified tarball, removed in `finally` (case 2e). Plan: "Each run works in its own directory" |
| R6A1-08 A value could not start with `#` | MINOR | Accepted (fixed and tested) | Gate: `#` directly after `=` or `:` starts a value; `= # comment` stays unmatched |
| R6A1-09 A two-line match could be cut at a part boundary | MINOR | Accepted (documented) | After R6A1-01's fix no rule matches a value below its name, so the cut cannot arise. Gate docstring and plan list the two-line form as a known limit |
| R6A1-10 Placeholder shapes skip real values | MINOR | Accepted in part | The residual is a known limit in the gate's docstring and in the plan. Widening the expansion shapes is deferred to XC-LEAKS S0.2, which tunes rules on real files (case 4) |
| R6A1-11 A binary-signature refusal named no cause | NIT | Accepted (fixed) | Gate: on a byte-count mismatch it reruns the scanner at debug level and names each skipped part's source file |
| R6A2-01 The trio runs editable installs | MAJOR | Accepted (re-derived) | §4 Wave 1's trio route and exit; §5's R-DC-PATCH row; §6's mid-wave sitting; §9's trio row: sync the primaries (never past W1.4) or swap in the wheel, pull the cascor primary (O13), restart, and verify code, not version |
| R6A2-02 Sentry receives it differently by service | MINOR | Accepted | Overview 2 and H-22: cascor's log lines and 502 chain; canopy's ERROR line; recurrence starts no Sentry |
| R6A2-03 Cascor has further relays; the loader must raise | MINOR | Accepted (re-derived) | S0.11's cascor bullet; H-22 and Overview 2 add the 200 status body; §8's cascor row adds `src/api/app.py` |
| R6A2-04 Four repositories rescan history on dispatch | MINOR | Accepted (re-derived) | XC-LEAKS "What CI rescans" and note 2; H-17; §9's XC-LEAKS row; §7.1 item 6 |
| R6A2-05 CI's git mode does not chunk | MINOR | Accepted | XC-LEAKS note 3 |
| R6A2-06 Four of A2's rulings gate no Wave 0 host step | MINOR | Accepted (re-derived) | Sitting item 1 holds O-10, N-1, N-2 and A5's O13; O-2, O-7, O-8 and O-12 move to item 8; A2's row says which item takes which |
| R6A2-07 No base row was stated | MINOR | Accepted (re-derived) | §7.1 "Size": Medium × High, one escalator for all 11 items, and a second for items 1–6 |
| R6A2-08 The de-escalator example was the instrument itself | MINOR | Accepted | §7.1 "Totals": the example is dropped; no item has a different instrument, and XC-LEAKS stays in the top cell |
| R6A2-09 The timeframe outran its own arithmetic | MINOR | Accepted | Scope & Timeframe and §7.1: the rounds set an 11–22-day floor; "What fills the rest" names the serial work, and the range is a judgement |
| R6A2-10 The scanner reads, not skips, a long line | NIT | Accepted | XC-PRESERVE method |
| R6A2-11 The 8.24.3 run's purpose | NIT | Accepted | XC-LEAKS note 1 |
| R6A3-01 Which release carries the `[recurrence]` caps | MAJOR | Accepted | R-ML-a carries them: XC-P12 action 2, §5's vehicle and R-ML-a rows, Appendix B row 6. A1 names only W1.13 as vehicle (b)'s wait |
| R6A3-02 Only data's cron was said to rescan | MINOR | Accepted (with R6A2-04) | As R6A2-04. "No repository rescans history" holds only if every one stops |
| R6A3-03 Lock PRs "pick up both"; vehicle (a) sequenced | MINOR | Accepted | §5's order: step 2 conditional; vehicle (a) listed outside the order |
| R6A3-04 One explicit config, not two unioned scans | MINOR | Accepted | §9's push row; §12's push risk; Appendix B row 22 ("B9-class rules") |
| R6A3-05 "Step 8" was ambiguous | MINOR | Accepted (with R6A2-06) | "Before sitting item 8"; item 3 is "Tier 2 install (`…RECOVERY-PLAN.md` §6.3 step 8)", and item 4 names §6.3 step 9 |
| R6A3-06 The between-round cap contradicted the default | MINOR | Accepted | §1.3: three account-wide during a round; three per session between rounds, which can reach 21–24 |
| R6A3-07 O-2 does not gate Phase B | MINOR | Accepted (re-derived) | Wave 1: P1-10 needs O-7, O-8 and O-12, with O-7 named as the STOP's exit condition; §9 likewise |
| R6A3-08 Phase D's rulings had no slot | MINOR | Accepted (re-derived) | Wave 1 item 5 and §9: P1-18 needs O-1, O-2, O-7, O-13 and O-14. Group B gates Phase D; O-5 and O-9 are "before Phase E". §7.1's sittings bullet |
| R6A3-09 One question in up to three groups | MINOR | Accepted (re-derived) | P2 O8 and O12 under Group B's P2, named as P12's; P4-Q6 named as P4 D-10; data#409 at A9 (R1); cascor#582 at P5 OD-9; data#423 alone in P4 D-14; OD-11 in Group B with P6-22 |
| R6A3-10 Three OD-3s | MINOR | Accepted | "P6 OD-3" in XC-P12, Wave 1 and §9 |
| R6A3-11 "The census" meant two scripts | MINOR | Accepted | §12 names `util/release_train/detect.py`, `util/ad-hoc/2026-09-22_p04_log_marker_census.py`, `util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py` and `util/ad-hoc/register_status_crosscheck.py`, and says the live census ran |
| R6A3-12 Known fleet closes waited for mid-wave | MINOR | Accepted | §6 A10 rules them at the first sitting (sitting item 8; XC-FLEET); §12 says triage closes nothing |
| R6A3-13 The trio route omitted the cascor pull | MINOR | Accepted (with R6A2-01) | §4 and §9: pull the cascor primary (O13) |
| R6A3-14 P3-05 held P3-08 and the cascor fix | MINOR | Accepted (re-derived) | Wave 1's cascor line: independent. §8's cascor row: F-S10's fix waits on P3-08 only on a shared file |
| R6A3-15 S0.5 could fix forward on the wrong scope | MINOR | Accepted | S0.5 and §7.1 item 4 wait for A1 and A4 |
| R6A3-16 T2 IDs in no lane | MINOR | Accepted | Wave 2 adds P2-R8 and P2-R10 (P2), P3-33 (P3) and P8-06 (P8). P6-27 moves to T6, as its extraction row's HYGIENE says. P12-35 and P12-36 move to T5 under Wave 4 |
| R6A3-17 Moved handoffs without filenames | MINOR | Accepted (re-derived) | §10 names each one at its `HO/HANDOFF_2026-09/` path |
| R6A3-18 Merged pairs at different tiers | NIT | Accepted | P9-17 moves to T3 with P1-24; P3-20 and P3-21 move to T1 with P2-01 and P2-03; P4-27 leaves the T3 range |
| R6A3-19 P2-26 waited on itself | NIT | Accepted | "P2-27..P2-30, after O7 (= P2-26)" in Wave 2 and Appendix A |
| R6A3-20 Three stale phrases | NIT | Accepted | "Rounds 1–6"; Goals "the fixes §6 A1 accepts"; XC-CRED "as a log record" |
| R6A3-21 Release versions mixed current and target | NIT | Accepted | §5: "PyPI x.y.z"; R-DC-PATCH "target 0.5.1; PyPI 0.5.0" |
| R6A3-22 D6 does not gate XC-CLEAN | NIT | Accepted | Group C: "D4 and D5, which gate XC-CLEAN; D6 (record only)" |
| R6A3-23 "→" targets without an Appendix B row | NIT | Accepted | Appendix B rows 23–25: XC-FLEET, XC-PRESERVE, §6 |
| R6A3-24 Role references without a filename | NIT | Accepted | Each is named, or given a short form in the Documents table ("the live census", "the gate") |
| R6A3-25 "Wave 4" and "round 6" each had two meanings | NIT | Accepted | "P4's Wave 4" and "P9's round 6" wherever those are meant |
| R6A3-26 Four gaps | NIT | Accepted | §5 lists R-CASCOR-2 and R-CASCOR-MODEL outside the order; §8 adds P6-07; P1-25 stays in Wave 2 only, with S0.3 pointing to it; the canopy cut question is A5's P4 D-4 only |
| R6A3-27 The coverage tool checks presence, not placement | NIT | Accepted | Scope & Timeframe: "checks that every extraction ID appears in the plan (anywhere, so it does not check the tier)" |

**Totals:** 49 findings (2 BLOCKER, 5 MAJOR, 29 MINOR, 13 NIT), all accepted, R6A1-10 in part.

## Unresolved dissent

None. The lanes overlapped on three themes, and they agreed on each: the history rescans (R6A2-04, R6A3-02), the sitting's step 1 (R6A2-06, R6A3-05, R6A3-07) and the trio route (R6A2-01, R6A3-13).

## What this reconciliation cannot support

- That round 6's corrections, or gate v4, introduced no new error. Round 7 is briefed on exactly that, and it adds the Lane B attack that round 6 did not run.
- That the gate catches every way a secret can be written. Its docstring lists the known limits.
- That the 37 real-file findings hold no credential. v4's 37 were not classified one by one; Lane A1 classified v3's 30 on the same files, by shape.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after 2026-10-05T21:45Z.
