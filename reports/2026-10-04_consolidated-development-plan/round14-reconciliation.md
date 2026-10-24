# Round 14 — reconciliation of two lanes into plan v1.14.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.13.0 (`ccb1ee2b976d02cb`, frozen 2026-10-10T21:35:06Z, never landed) → v1.14.0 (`228ccc7ee4728c58`). `main` still holds v1.12.1 (`f3b1592a6658611e`, ml#2214), so v1.14.0's PR carries v1.13.0's changes too.
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`: unchanged, `4e2158c8b6fc15e8`.
  - `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases: unchanged, `5a2d73c35d976bc0`.
  - The line read `util/ad-hoc/2026-10-05_masked_finding_shape.py`, `795bf2e7430c4558` → `0b13a8aaefa6eb4c`: docstring only. Its listed limits gain a lower-case bare key, a URL query's `authid` and the raw PATH field (R14B-10, R14B-11), and a new paragraph lists the 12 pins as limits of the checks (R14B-01..07). Its code is unchanged.
  - The harness `util/ad-hoc/2026-10-08_line_read_mutation_run.py`, `9f32f068dd1cd54c` → `0257ddd77c2eb30f`: a repeated JSON member name refuses the file; the baseline is marked by its place, not its id; an entry whose id is `BASELINE`, or names no directory of its own under `--out`, is BUILD-FAIL; and a run fails unless CAUGHT, SURVIVED and BUILD-FAIL add up to the entry count (R14B-08, R14B-09).
  - New: `util/ad-hoc/2026-10-24_sequence_safety_on_paths.py` (`2284187a216c9162`), which runs CI's two sequence-safety screens, from juniper-ci-tools' own library, over a PR's path list against a base ref with no commit made. The PR is pushed as signed commits from untracked files, so there is no local head to give the CLIs.
  - Lane B's mutant file, `round14-mutants-laneB.json` in this directory (`ba8ad2207bf25dae`, 12 mutants), equal as JSON to the block in Lane B's report. It is kept, not merged into a caught set: its 12 entries are the listed limits, and all survive.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 14 was briefed on round 13's corrections and the drift taken in (`round13-reconciliation.md`). The plan's gate-severity and ending rules applied as its Validation record states them.
- **Lane reports** (both in this directory; R14A- and R14B- IDs below are theirs; sha256 as the lanes wrote them, before the archive header):
  - `round14-laneA-reprobe.md` (`92f4187a984de9a1`): 0 BLOCKER, 1 MAJOR, 5 MINOR, 4 NIT;
  - `round14-laneB-attack.md` (`ed8781c9afd2d66d`): 0 BLOCKER, 7 MAJOR (all pins), 7 MINOR, 2 NIT.
  - 26 findings in all, counted from the reports' findings tables: 8 MAJOR, 12 MINOR and 6 NIT.
- **Window**:
  - The lanes ran on 2026-10-10, after v1.13.0's freeze at 21:35:06Z. Lane A read the frozen hashes at 21:36:12Z, 21:53:24Z and 22:07:31Z, and Lane B at 21:36:20Z, 21:55:34Z and 22:06:49Z, all seven unchanged at every reading.
  - The session, `560c1ec5`, then asked the owner whether round 14 ends validation, and waited. The owner answered on 2026-10-24, and this reconciliation ran from about 04:39Z that day.
- **The owner's ruling of 2026-10-24**: correct and land, with no round 15. Apply R14A-01's correction and every MINOR and NIT as v1.14.0, record Lane B's 12 surviving mutants as listed limits, then gate, PR and merge. Round 14 does not meet the ending rule as written, because R14A-01 is a MAJOR that is not a pin, so validation ends on this ruling.
- **Where**: the worktree `concurrent-gathering-biscuit`, as for round 13. Nothing was copied out of it; the PR is pushed from gated scratch copies.
- **Method**: read-only, except the plan, the read's docstring, the harness, the consumed handoff's banner, the two lane reports' archive headers and this file.
  - GitHub reads were REST GETs (among them the cascor run and the two compares above), except the PR's signed commits. Git read with `show`, `log`, `ls-tree`, `rev-list` and a `fetch` of `origin/main`.
  - Tool runs used synthetic inputs in the session scratchpad. One real file was read, `docs/REFERENCE.md` at `6f5de915`, through the gate only, by key (R14A-03).
  - No secret was read or printed. No host action ran.
- **How v1.14.0 was written**: the reconciler applied every disposition below by hand, then re-checked the plan's line lengths, lint, structure and ID coverage. No agent edited the plan.
- **ID coverage**: v1.12.1 (`main`) → v1.14.0 drops no ID (381 → 381), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0). With round 13's v1.0.0 → v1.13.0 check, which v1.12.1 also passed, no ID has been dropped since v1.0.0.
- **Lint and structure**: the plan and this file pass markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line of the plan is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Finding | IDs | Re-derivation | Result |
| --- | --- | --- | --- |
| Cascor 0.12.0's image was public before the final census | R14A-01 (MAJOR) | `gh api repos/pcalnon/juniper-cascor/actions/runs/38085392650`: "Publish Container Image", event `release`, `completed`/`success`, 20:51:40Z–20:56:03Z, head `41ea53e5` | Confirmed |
| Canopy is 74 commits past v0.8.1; the data branch is 26 behind `main` | R14A-02 | `compare/v0.8.1...c25ca20c` (canopy#739's merge, `main` at 10-10): ahead 74, behind 0. `compare/381e660b...94ce8b1f` (data#479's merge against the fix-forward branch): diverged, 2 ahead, 26 behind | Confirmed |
| The gate prints two keys on L6228 | R14A-03 | The gate (`--scan-dir`) on a scratch copy of `docs/REFERENCE.md` at `6f5de915`: canary 32 of 32; 2 findings, `…:6228:120:juniper-header-refusal:617fbd3a74` and `…:6228:121:…:617fbd3a74`, both open. The run was piped through `tail`, so only its keys are used, not its exit | Confirmed |
| The `…RECOVERY-PLAN.md` citations moved with ml#2199 | R14A-04 | The file on `main` at `f694a450`, unchanged since `6f5de915` (`git log`): L224 is the release's second limit, L240 B11 and L296 P0 step 3's key probe | Confirmed, and still true on today's `main` |
| 12 mutants of the read survive both checks | R14B-01..07 | The harness over `round14-mutants-laneB.json` on the frozen read and harness: baseline PASS, 12 built (12 distinct reads), 0 CAUGHT, 12 SURVIVED, 0 BUILD-FAIL, exactly Lane B's list | Confirmed |
| The harness's accounting is open | R14B-08, R14B-09 | Lane B's runs, not re-run. The frozen harness's code agrees: its loop keys the baseline's branch on `m["id"] == "BASELINE"`, and `load_mutants` calls `json.loads` with no member check | Confirmed by inspection |

Not re-derived, applied as the lanes proposed: R14A-05..10 (each a line citation, wording or count with its source named in the lane's table) and R14B-10..16 (Lane B's probes and the design's lines, which the reconciler read for H-23's edits: `…INTEGRATED-DESIGN.md` L2750–2762 and L2784–2793 on `main`).

## The tools, tested

The harness fix and the read's docstring were made by the reconciler after both lanes had finished, and every row below ran on the final files.

| Row | Check | Expected | Measured |
| --- | --- | --- | --- |
| 1 | `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases, on the edited read | Each as its case states | **181 of 181 as expected**, exit 0, the `names` and `contract` checks included. The gate did not change, so no gate case could regress |
| 2 | The harness over `round13-mutants.json` | Baseline PASS; every mutant caught | Baseline PASS; 81 entries, 81 built (81 distinct reads), **81 CAUGHT**, 0 SURVIVED, 0 BUILD-FAIL, exit 0 |
| 3 | The harness over `round14-mutants-laneB.json` | The 12 survive (the listed limits) | Baseline PASS; 12 built (12 distinct reads), 0 CAUGHT, **12 SURVIVED**, 0 BUILD-FAIL, the tallies complete, exit 1. So the docstring edit left every anchor in place |
| 4 | The harness on a file repeating a member name: in the object form (`{"DUP": …, "DUP": …}`), and inside one entry (two `id` members) | Refused | `REFUSED <file>: the member name 'DUP' occurs twice in one object`, and the same for `'id'`, exit 1 each, before any check runs |
| 5 | The harness on an entry with the id `BASELINE` and entries with the ids `..` and `.`, each holding a valid replacement | BUILD-FAIL each; nothing written outside `--out` | Baseline PASS; 3 entries, 0 built, **3 BUILD-FAIL** ("its id is the baseline's"; "its id names no directory of its own under --out", twice), 3 of 3 accounted, exit 1. `--out`'s parent holds only `--out` |
| 6 | `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` on the PR's seven Python files | 0 | 0 predicted alerts |
| 6s | `util/ad-hoc/2026-10-24_sequence_safety_on_paths.py` over the PR's 15 paths against `origin/main` (`f694a450`), with juniper-ci-tools 0.9.1's library from `main`; and a negative control on synthetic text | No unwaived FAIL; the control fails | Symbol screen: 7 files in scope, 0 findings. Docs screen: the plan, 158 WARN (each a replaced run of lines), 0 FAIL. The control: a deleted function is `LOST`/`FAIL`, and six deleted lines a `deletion-run` FAIL |
| 7 | FP40, round 6's 40 real files | — | Not re-run: the gate is byte-identical to the one that gave 49 keys on 2026-10-10, and the scratch corpus did not survive the gap. The PR's own push scan stands in for a real-file run of the unchanged gate |

## Dispositions

| Finding | Severity | Disposition | Applied as |
| --- | --- | --- | --- |
| R14A-01 Cascor 0.12.0's image is public | MAJOR (not a pin) | Accepted (re-derived) | §5's R-CASCOR note: a bullet for the image (run 38085392650, 20:56Z), the second on the new locks, installing `requirements-cpu.lock` (observability 0.4.1, service-core 0.7.1, data-client 0.5.0), with juniper-deploy still on cascor 0.11.0. §6's mid-wave cascor item: approving the gate publishes the 0.12.0 wheel; the image is already public, so withholding the gate withdraws nothing. The Overview's lock bullet names cascor's image the second, and the Overview's, §9's and §12's 0.12.0 entries read "image published 20:56Z" |
| R14A-02 Canopy's and the data branch's counts | MINOR | Accepted (re-derived) | "74 commits past v0.8.1" in §2's P2 row, §5's R-CANOPY-A row and §10's P2 list, which names canopy#739 the last; "26 behind `main` after data#479" in §2's P3 row and §10's P3 list |
| R14A-03 Two keys on L6228 | MINOR | Accepted (re-derived) | S0.3's upload bullet and §8's `docs/REFERENCE.md` paragraph: at `d14b86e5` and on `main` the gate prints two keys on L6228, columns 120 and 121; read the line once and accept both, or the gate fails closed; the gate re-keys it before each upload |
| R14A-04 `…RECOVERY-PLAN.md` citations | MINOR | Accepted (re-derived) | Wave 1's P1-12 citation reads "L240, L296 on `main`, L229 and L272 before ml#2199"; XC-PRESERVE's row k reads "L224" for "L213". The validation record's citations of earlier rounds' reads stay as those rounds made them |
| R14A-05 Canopy's second relay site | MINOR | Accepted | The Overview's canopy relay gains a sibling bullet for `regenerate_dataset_from_generator` (L1958–1962, L1970); H-22's canopy citation adds the same lines; S0.11's canopy test drives both client paths and both log sinks |
| R14A-06 Withdrawing 0.17.1 | MINOR | Accepted | §5's data-versions note and §6's time-bound data item: withdrawing 0.17.1 means deleting its Release, tag and GHCR image as well, and 0.17.2 avoids both. R-DATA-2's row and Wave 1's step 6 now say "0.17.1 only if the owner withdraws the cut 0.17.1, its Release, tag and image with it" |
| R14A-07 The release pause's start | NIT | Accepted | The Overview: "after juniper-data 0.16.0 (2026-09-24) until 2026-10-08" |
| R14A-08 Non-provider patterns | NIT | Accepted | Wave 0's scanning-settings bullet: "non-provider patterns are off in all nine" |
| R14A-09 `AGENTS.md`'s suite count | NIT | Accepted | §10's ml#2199 bullet: "204 suites, unchanged by ml#2203, after which CI and `docs/REFERENCE.md` run 205" |
| R14A-10 Round 13's window | NIT | Accepted | Round 13's heading: "run 22:58Z–23:30Z" |
| R14B-01 Numeric fields are held to their form, not their value (M1–M4) | MAJOR (pin) | Accepted as a listed limit (owner rulings of 2026-10-10 and 2026-10-24; re-derived) | The read's docstring, "Limits of the checks, not of the read"; §3's XC-PRESERVE method (round 14's bullets), and its round-13 sentence narrowed to "each line's form, not each field's value"; the mutants kept in `round14-mutants-laneB.json` |
| R14B-02 Refusal reasons held by their first words; whole-value planted test (M5, M6) | MAJOR (pin) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-03 One malformed KEY shape (M7) | MAJOR (pin) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-04 Lower-case prefixed TOKEN, SECRET and API_KEY names unplanted (M8) | MAJOR (pin) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-05 `-pass`'s spellings after a double quote or as argv items unplanted (M9, M10) | MAJOR (pin) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-06 A run of two or more tagged blanks unplanted (M11) | MAJOR (pin; prints no character) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-07 An END past the file's end unplanted (M12) | MAJOR (pin) | Accepted as a listed limit (as R14B-01) | As R14B-01 |
| R14B-08 A `BASELINE` or `..` id escapes the accounting | MINOR | Accepted (fixed and tested) | The harness: the baseline marked by its place; such an entry BUILD-FAIL; a TALLY-FAIL line and exit 1 when the tallies miss an entry (tools rows 3 and 5); the plan's §3 and Instruments |
| R14B-09 A repeated id vanishes through the object form | MINOR | Accepted (fixed and tested) | The harness parses with an `object_pairs_hook` that refuses a repeated member name in any object (tools row 4); the plan's §3 and Instruments |
| R14B-10 The PATH field prints a file name raw | MINOR | Accepted as a listed limit | The read's docstring: the PATH field prints a file's name as it is, so a control character in a name can overprint a terminal's lines, and the PR's own changed-file list is the control; the plan's §3 |
| R14B-11 Lower-case bare keys and `authid` queries | MINOR | Accepted as a listed limit | The read's docstring and the plan's gate list (§3): `--names` misses a lower-case bare key (`password:`, `token:`, `api_key =`) and a Duplicati `TargetURL`'s `authid`, which the gate reports when the value looks random, so KEY mode reads them |
| R14B-12 Step 11's date bound | MINOR | Accepted | H-23(b): the five are for a first pass by 2027-02-27, after which it deletes more and the list is the port's (`util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py --policy`), and the copy-aside takes that list; the Overview's ruling bullet and §12's row carry the bound |
| R14B-13 Procedure B's Repair | MINOR | Accepted | H-23 gains (c): a Repair deletes remote files, the 09-18 dlist among them, and step 10's dry-run log and copy-aside come first; H-23's title, §12's row and Wave 1's P1 status bullet name it |
| R14B-14 No row for the 0.6.x F-S10 patch | MINOR | Accepted | §5: an R-DC-PATCH-6 row (the forward-port's 0.6.x patch, its number ruled at A9, P5's spec claiming 0.6.1), a place in the order's step 1, and the P12 note; §6 A9 and the DC-0.6 note name its number; A1's time-bound paragraph says approving 0.6.0's gate leaves 0.5.1 out of reach of unpinned installs that admit 0.6 |
| R14B-15 H-23(a)'s window ends at step 10's restart | NIT | Accepted | H-23(a)'s heading and rule, S0.3's two corrected texts, Wave 0's H-23 line, XC-FLEET's resume sentence and Wave 1's P1 status bullet read "before P0 step 10's restart". The Status's record of the 2026-10-10 ruling keeps its wording, with a note |
| R14B-16 The watchdog docstring's "Always a fault" | NIT | Accepted | S0.3's PR also qualifies `util/ad-hoc/yamaguchi_watchdog.py` L29–31 for H-23(a)'s window |

## Drift

None taken in. v1.14.0 is v1.13.0's snapshot, 2026-10-10T21:30Z, with round 14's corrections, and its Snapshot marks it stale. By 2026-10-24T04:55Z juniper-ml's `main` was 91 commits past `6f5de915`, at `f694a450`, among them W1.13's cap and floor PRs, juniper-ml 0.11.0's proposal and the `[tools]` floors. Of the files this plan cites by line, `…RECOVERY-PLAN.md`, `…INTEGRATED-DESIGN.md` and the watchdog are unchanged since `6f5de915`; `docs/REFERENCE.md` changed in 27 of those commits, which S0.3's re-keying rule already covers.

## Unresolved dissent

None. The lanes did not contradict each other: Lane B's "Not refuted" places the accepted line at L6228 on `main` without counting its keys, and Lane A's R14A-03 counts two.

## Corrections to round 13's record

- `round13-reconciliation.md`'s "Drift taken in" ends with the spot GETs to 20:42Z. The reconciler's later intake, to the 21:30Z census (cascor 0.12.0's cut, ml#2215, ml#2216), is in v1.13.0's text but not in that section, and it missed cascor's image (R14A-01).
- Its "Smaller" bullet says `docs/REFERENCE.md`'s gate key moved to L6228 at `d14b86e5`. At that line the gate prints two keys, columns 120 and 121 (R14A-03).

## What this reconciliation cannot support

- That v1.14.0's text is right where no round has read it. By the owner's ruling, no round checks v1.14.0; its corrections were re-derived where the table above says so and otherwise applied as the lanes proposed.
- State after 2026-10-10T21:30Z. Every gate, cut and open PR the plan names as waiting or open may have moved in the 13 days since.
- That the read is right in the 12 places its checks do not pin. Lane B showed the frozen read behaving as its clauses say in each (its demos, not re-run here); a later edit there would pass the checks, which is why the docstring requires the mutation run over `round14-mutants-laneB.json` for any edit to the read.
- FP40 on the final tools (tools row 7).
