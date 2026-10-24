# Round 13 — reconciliation of three lanes into plan v1.13.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.12.0 (sha256 prefix `d7d07c3f8931b212`) → v1.12.1, the record that ml#2214 landed (`f3b1592a6658611e`; v1.12.0's text with a new Status, Version, round-13 entry and Changed list) → v1.13.0 (`ccb1ee2b976d02cb`, frozen 2026-10-10T21:35:06Z).
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`: unchanged, `4e2158c8b6fc15e8`.
  - The line read `util/ad-hoc/2026-10-05_masked_finding_shape.py`, `f0fbf134da7f3a5b` → `795bf2e7430c4558`: no `names=`/`markers=` counts, blanks other than space and tab masked, env names after leading underscores, `BAD KEY` as a place and a masked shape, the `--keys-file` checked by `lstat`, START > END and off-line columns refused; its four clauses restated as now pinned, and its listed limits widened (R13B1-13).
  - `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases, `e2814ee7be5f5ccc` → `9db5aae3d4aa25fb` (ml#2214's CodeQL-only edits) → `5a2d73c35d976bc0`: stderr captured and checked in every read call, exact forms for every output line, each line once per file group, refusals naming file and reason, and a case per surviving mutant.
  - The harness `util/ad-hoc/2026-10-08_line_read_mutation_run.py`, `31451d79ebce51a8` → `9f32f068dd1cd54c`: every entry counted, an entry with no replacement or an unmatched anchor reported as BUILD-FAIL, each file's entry count printed (R13B1-12).
  - New: `round13-mutants.json` in this directory (`6a1abecc23f5d343`, 81 mutants) and `util/ad-hoc/2026-10-10_build_round13_mutants.py` (`5e60d17533cafb87`), which rebuilds it byte for byte from `round12-mutants.json`, the three lane files and the read.
  - New, by this session: `util/ad-hoc/2026-10-10_all_pass_token_classes.py` (`c4b610e5d9abe511`, the `--all` pass's tokens classified in-process), `2026-10-10_verify_blobs_on_ref.py` (`311195fa57ab293a`, a merged ref checked against the blobs sent) and `2026-10-10_precommit_on_path_list.py` (`85d9f35cd63b2928`, pre-commit over a path list).
  - CodeQL-only edits in ml#2214, no behaviour changed: the census tool (`275cc45d55a81fb4` → `3b990448557b7f84`), `2026-10-04_plan_id_coverage.py` (`6094f49ca6fdbf4c`) and `2026-10-08_pr_printed_line_screen.py` (`e154990f5bb3d80b`), with the regression above.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 13 was briefed on round 12's corrections (`round12-reconciliation.md`); v1.12.0 took in no drift. The plan's gate-severity and ending rules applied as its Validation record states them.
- **Lane reports** (all in this directory; R13A-, R13B1- and R13B2- IDs below are theirs):
  - `round13-laneA-reprobe.md`: 0 BLOCKER, 4 MAJOR, 2 MINOR, 7 NIT;
  - `round13-laneB1-safety.md`: 1 BLOCKER, 9 MAJOR, 6 MINOR, 1 NIT;
  - `round13-laneB2-schedule.md`: 0 BLOCKER, 3 MAJOR, 7 MINOR, 6 NIT.
  - 46 findings in all, counted from the reports' findings tables.
- **Window**:
  - The lanes ran on 2026-10-08 from 22:58Z, after v1.12.0's freeze at 22:56Z: Lane B2 until 23:10:30Z, Lane A until 23:26:21Z and Lane B1 until 23:29:59Z, each reading the same frozen hashes at its start, middle and end.
  - Session `3e8595eb` handed off at about 10:50Z on 2026-10-10 without reconciling (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`, on `main` through ml#2207). This session, `560c1ec5`, took the work up at 18:32Z.
- **The owner's rulings of 2026-10-10**, asked before reconciling, as the handoff required:
  1. Land the plan first as a record of v1.12.0, then re-baseline it as v1.13.0 in a second PR. ml#2214 is that record: v1.12.1, round 13 archived unreconciled, 81 files in seven signed commits.
  2. Fix-forward releases are owed for R-OBS-SC (P3-07, then observability 0.4.2 and service-core 0.7.2) and R-DATA (P3-03 with P3-09, then data 0.17.1), each cut after its fix validates.
  3. H-23 narrows to the window before §8 step 10's retention removals and to step 11's restore. A2's DEFECT-1 ask and the fold-in are done by ml#2199; S0.3's small docs PR stays.
  4. A round whose only MAJORs are the line read's pins may end validation, with those MAJORs recorded as listed limits.
- **Where**: the worktree `concurrent-gathering-biscuit`, which this session entered (the session's command guard refuses git in another worktree, and entering it is the documented way to honour a handoff's location). Nothing was copied out of it; the record PR was pushed from gated scratch copies.
- **Method**: read-only, except the plan, the tools named above, the new scripts, the mutant set and this file.
  - GitHub REST and GraphQL reads were GETs, except the record PR's signed commits. Git read with `show`, `ls-tree`, `archive` and `fetch` of `origin/main`.
  - The tool changes were made after all three lanes had finished. Tool runs used synthetic inputs in the session scratchpad. Real files were read only through the gate (FP40, by key) and the masked read.
  - No secret was read or printed.
- **How v1.13.0 was written**: an editor agent applied this file's dispositions, the drift brief's row-level proposals and the owner's rulings to v1.12.1 (about 150 edits), and the reconciler reviewed the consequential sections (Status, H-22, H-23, S0.14 and the sitting order, §5's release rows, §6's time-bound items), filled the tool counts, took in the drift to 21:30Z and added the KEY-form limit. Round 14 re-derives the rest.
- **ID coverage**: v1.0.0 → v1.13.0 drops no ID (381), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan and this file pass markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). The plan's longest line is 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Finding | IDs | Re-derivation | Result |
| --- | --- | --- | --- |
| H-22's lift is keyed to the service, not to when a text was written | R13B1-01 (BLOCKER), R13B2-01 | Read H-22's lift bullet, Wave 2's evidence rule and XC-FLEET's ml#2152 PR rule in v1.12.0 (§11, §4 Wave 2, §3) against XC-CRED's count search | Confirmed. Each lifts "once the running service carries that relay's fix", with no limit to text written after it, and XC-CRED's zero count leaves rotation open |
| Canopy has its own data-client relay | R13B2-02 | `gh api` contents of canopy at tag `v0.8.1`: `src/demo_mode.py` builds a `JuniperDataClient` with canopy's own data key (L1037–1039) and logs each failure at ERROR with the raw exception (L1065, L1079); `src/settings.py` has 0 matches for `screen_outbound_key` or `get_outbound_secret` (9 on `main`); juniper-deploy's `docker-compose.yml` on `main` pins `ghcr.io/pcalnon/juniper-canopy:0.8.1` at L686, L830 and L921 | Confirmed |
| XC-CRED's search waits on an item scoped by A1 | R13B2-03 | v1.12.1 L571 (one session item before sitting item 6: S0.11's search), L625 (S0.11 is "F-S10, for whatever the owner accepts at §6 A1") and L590 (A1 at item 8) | Confirmed |
| Row q names a stale worktree | R13B1-02 | v1.12.1 L291 names `unified-orbiting-fountain`; the live set was in `concurrent-gathering-biscuit` | Confirmed; row q is now done by ml#2214 |
| 17 mutants of the read survive both checks | R13A-01..04, R13B1-03..07 | `util/ad-hoc/2026-10-08_line_read_mutation_run.py` over the three lane files on the frozen read and regression: 19 entries, 18 built (the empty entry dropped without a word, as R13B1-12 says), baseline PASS, M2 caught, 17 SURVIVED, exactly the lanes' list | Confirmed |
| `names=` restores a credential word inside a value | R13B1-09 | The frozen read on a synthetic `.env` holding `API_KEY=blue-TOKEN-river` and `API_KEY=blue-SPOON-river`: identical masks, `names=2` against `names=1` | Confirmed |
| A malformed KEY prints in clear | R13B1-10 | The frozen read with a keys-file of one synthetic `SETTINGS_TOKEN=<value>` line: exit 3, and the value appears once on stderr (`grep -c` = 1) | Confirmed |
| Round 12's 57 entries build 53 reads; 23 survivors are 20 | R13A-05 | `util/ad-hoc/2026-10-10_build_round13_mutants.py` over `round12-mutants.json` collapses `R12N-names-in-clear` into `R11-M18`, `R12B1-C2a` into `R12AX11`, `R12B1-C2b` into `R12AX12` and `R12B1-C4a` into `R12AX20`, by built text | Confirmed |
| The harness drops an empty entry silently | R13B1-12 | The frozen harness over the three lane files: 19 entries, 18 built, the empty entry absent from its output | Confirmed |

## The tools, tested

The fixes were made by a tool agent briefed with the lanes' findings and proposed corrections, after every lane had finished; the reconciler reviewed the read's diff line by line and re-ran every row below itself, on the final files.

| Row | Check | Expected | Measured |
| --- | --- | --- | --- |
| 1 | Probe mode | Canary 32/32 | Canary 32 of 32. Default rules alone 3 of 32; the interim rules alone 31 of 32; the worktree's `.gitleaks.toml` (as of `81d3fbb3`) 0 of 32, zero-rule; `main`'s (ml#2203) 9 of 32 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases | Each as its case states | **181 of 181 as expected**, exit 0, the `names` and `contract` checks included; 0 FAIL. The gate's rules did not change, so no gate case could regress |
| 2m | The harness over `round13-mutants.json`: round 12's 57 entries (none needed retargeting), the lanes' 18 non-empty entries (M2 and M2b retargeted, since R13B1-09's fix removed their anchor) and 12 new `R13N-` mutants of the new code; 87 entries, 6 collapsed by built text (the four of R13A-05, `R13B1-M6` into `R13A-passin-passout`, `R13B1-M7` into `R13A-key-outside-root`), the empty entry left out by name | Baseline PASS; every mutant caught | Baseline PASS; 81 entries, 81 built (81 distinct reads), **81 CAUGHT**, 0 SURVIVED, 0 BUILD-FAIL |
| 2l | The harness over the three lane files | Their entries caught or reported | 19 entries: 16 built (14 distinct reads), all 16 CAUGHT; 3 BUILD-FAIL by name (the empty entry; M2 and M2b, whose anchor `len={len(text)} names=` is gone); exit 1, as the harness now reports a BUILD-FAIL |
| 2b | The builder | Byte for byte | `round13-mutants.json` rebuilt with sha256 `6a1abecc23f5d343…`, equal |
| 3 | FP40, the 40 real files of round 6's false-positive sample, on the unchanged gate | 49 keys, as v6's | 49 findings in 13 files, exit 2; the key list byte-identical to v6's. KEY mode with the fixed read over those 49 keys: exit 0, 0 refused, 49 headers, each line masked (the new column check refuses no real key) |
| 4 | The fixed read on the record's accepted key | Read | `round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`: exit 0, not refused |
| 5 | `util/ad-hoc/2026-10-08_pr_printed_line_screen.py` on the fixed read's `--names` output | Parses | 21 new or changed files, 404 printed lines; the fixed read lists 343 lines in ml#2214's 86 push copies, against 323 before, from its widened env names |
| 6 | `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` on the seven changed or new tools | 0 | 0 predicted alerts |

## Dispositions

| Finding | Severity | Disposition | Applied as |
| --- | --- | --- | --- |
| R13A-01 `-passin`/`-passout` are unpinned | MAJOR | Accepted (re-derived; fixed and tested) | A contract case lists a `-passin pass:` and a `-passout pass:` line, each with its value masked |
| R13A-02 KEY mode's refusals of `..`, an absolute path and a symlinked root are unpinned | MAJOR | Accepted (re-derived; fixed and tested) | KEY cases for each, wanting exit 3 and nothing on stdout |
| R13A-03 "each line once" is unpinned | MAJOR | Accepted (re-derived; fixed and tested, with R13B1-05) | A case with two listed lines inside one window and one whose line above is listed; the check fails a line number printed twice in a file's group |
| R13A-04 A refusal need not name the file | MAJOR | Accepted (re-derived; fixed and tested) | The Latin-1 and unreadable walk cases and a KEY-mode refusal must name the file and the reason on stderr |
| R13A-05 23 survivors are 20 distinct; 57 entries build 53 reads | MINOR | Accepted | Round 12's numbers are corrected below ("Corrections to round 12's record") and in the plan's Validation record; `round13-mutants.json` is deduplicated by built text |
| R13A-06 ml#2184's credential-word count | MINOR | Accepted | S0.3's ml#2184 limb: 62 added lines hold a credential word, 18 of them in the #2177 section's 141, and the hunks are built with `git diff -U10 959748c5 1da05a92`, since the API omits `docs/REFERENCE.md`'s patch |
| R13A-07 A push copy predated the last edit | NIT | Accepted; recorded here | ml#2214's push copies were made after the last edit to any file and re-gated after the PR body's last fill; v1.13.0's are made the same way |
| R13A-08 "non-blank" again | NIT | Accepted | S0.3's read prints "the nearest non-blank line above and the five non-blank lines below each" |
| R13A-09 "next-day" 14:00Z | NIT | Accepted (with R13B2-11), then overtaken | H-23's rewrite drops the DEFECT-3 POST text, which ml#2199's Procedure B supersedes; where §10 still cites `…round3-fold-in-pending.md` L145, it reads "a future 14:00Z" |
| R13A-10 Round 12's line citations are v1.11.0's | NIT | Accepted; recorded here, not in place | See "Corrections to round 12's record" |
| R13A-11 "all 16 of Lane B1's clause mutants" | NIT | Accepted | "Lane B1's 15 clause mutants and Xrl" |
| R13A-12 Lanes do not write the set | NIT | Accepted | The Validation record: a lane gives each surviving mutant as an exact replacement, and the reconciliation adds it to the set |
| R13A-13 The ml#2152 section covers recurrence's relay only | NIT | Accepted | XC-FLEET: the section describes released 0.5.0's relay, and the driver's records hold cascor's relays too; the docs PR adds cascor's relays rather than keeping a rule for them |
| R13B1-01 H-22's lift is keyed to the service, not the record | BLOCKER (conditional) | Accepted (re-derived), with R13B1-01's remedy, the stricter of the two | H-22: the lift covers only text produced after the restart that loaded the fix; anything written before stays banned until `JUNIPER_DATA_API_KEY` has been rotated after it was written (XC-CRED). Wave 2's evidence rule and XC-FLEET's ml#2152 PR say the same |
| R13B1-02 Row q names a stale worktree | MAJOR | Accepted (re-derived) | Row q is done: ml#2214 landed the record; `unified-orbiting-fountain`'s copies are stale and are not a source |
| R13B1-03 stderr is unchecked | MAJOR | Accepted (re-derived; fixed and tested) | Both checks capture stderr in every read call and apply the in-clear and planted-value tests to it |
| R13B1-04 Output-line prefixes are unchecked | MAJOR | Accepted (re-derived; fixed and tested) | Every output line's prefix is checked against its exact form |
| R13B1-05 "each line once" | MAJOR | Accepted (with R13A-03) | As R13A-03 |
| R13B1-06 Bare `TOKEN`, `PASSWORD`, `SECRET` and `-passin`/`-passout` | MAJOR | Accepted (re-derived; fixed and tested, with R13A-01) | Bare upper-case `TOKEN=`, `PASSWORD=` and `SECRET=` lines join the listed set |
| R13B1-07 KEY refusals and refusal bytes | MAJOR | Accepted (re-derived; fixed and tested, with R13A-02) | KEY cases for `..`, an absolute path and line 0; the NUL, symlink and mode-000 refusals' stderr is checked for the planted value |
| R13B1-08 Names the gate reads that `--names` does not list | MAJOR | Accepted (fixed and tested) | The env-style alternatives start after leading underscores; `__API_KEY__:` and `_TOKEN=` lines join the check |
| R13B1-09 `names=` restores a credential word | MAJOR | Accepted (re-derived; fixed and tested) | The read prints neither `names=` nor `markers=`; a case requires equal output for a credential word and a control word inside a value |
| R13B1-10 A malformed KEY prints in clear | MAJOR | Accepted (re-derived; fixed and tested) | `BAD KEY` names the keys-file line or the argument position and prints the masked shape only. One case stays, found by the reconciler and recorded as a listed limit in the plan's XC-PRESERVE method: a line that has a KEY's form is read as a KEY, and a refusal names its path part (as R13A-04 requires), so `--keys-file` must hold the gate's own KEYs |
| R13B1-11 The keys-file is not checked by `lstat` | MINOR | Accepted (fixed and tested) | The keys-file is checked as a KEY's file is; a NUL in a path and a non-UTF-8 keys-file are refused with exit 3, no byte printed |
| R13B1-12 The harness drops an empty entry silently | MINOR | Accepted (fixed and tested) | Every entry is counted; an entry with no replacement is BUILD-FAIL; each file's entry count is printed |
| R13B1-13 Unlisted layouts | MINOR | Accepted | Both docstrings' listed limits name `-pass=pass:`, `--pass=pass:`, a string-prefixed argv item, a camel-case header key and `DB_PASS=` |
| R13B1-14 Every Unicode blank prints in clear | MINOR | Accepted (fixed and tested) | Only ASCII space and tab print as they are; every other blank is masked as a tag |
| R13B1-15 ml#2184's and ml#2185's reads miss published text | MINOR | Accepted (with R13B2-10) | S0.3 adds ml#2184's commit message, title and body; S0.13 adds ml#2185's branch name and its review's body |
| R13B1-16 The watchdog's alert still advises a resume | MINOR | Accepted, under the owner's H-23 ruling | S0.3's small PR also corrects the alert text in `util/ad-hoc/yamaguchi_watchdog.py` (with its pin in `tests/test_yamaguchi_watchdog.py`, if any) to "not before §8 step 10"; the redeployed watchdog picks it up only after a primary sync |
| R13B1-17 KEY refusal messages and limits | NIT | Accepted (fixed) | START > END is named; a column past the line is refused; a symlinked ancestor of `--root` is a listed limit |
| R13B2-01 H-22's lift and records already written | MAJOR | Accepted, with R13B1-01's remedy (see Unresolved dissent) | As R13B1-01 |
| R13B2-02 Canopy's own data-client relay | MAJOR | Accepted (re-derived) | Overview 2 and H-22 name it: open in canopy 0.8.1 and any canopy before #683/#685, deploy's images among them; canopy's bodies and logs lift only where the running canopy also carries #683/#685's outbound-key screen; S0.11's canopy test drives this path |
| R13B2-03 XC-CRED's search waits on A1's item | MAJOR | Accepted (re-derived) | The count-only search becomes S0.14, a Wave 0 session item with no A1 dependency, its counts in a file of their own; if they are not ready, sitting item 6 rules XC-CRED as if the count were zero (the question open) and takes them at the mid-wave sitting |
| R13B2-04 Three `docs/REFERENCE.md` corrections, unordered | MINOR | Accepted | §8's note orders them: S0.3's small PR first, then the ml#2152 PR; each rebuilds from `origin/main` before its upload |
| R13B2-05 Re-keying is not mechanical | MINOR | Accepted | The ml#2152 PR reads every finding in its section anew with KEY mode, the old key and any new one, and lists the keys it accepts |
| R13B2-06 Security step 5's rollback is undefined | MINOR | Accepted | Record each environment's package versions before the upgrade; under stop-first, a failure means reinstalling them before any restart; under the clone option, a smoke import and the relay test's fast subset run in the live environment after its upgrade and before the restart |
| R13B2-07 S0.7's census misses Wave 0 and Wave 2 sessions | MINOR | Accepted | S0.7 recurs before each sitting and at the start of every session that works this plan |
| R13B2-08 Who lifts a declined relay's ban | MINOR | Accepted | H-22: only an owner ruling, on evidence that every service reading the data key refuses a padded value |
| R13B2-09 A10 has no ml#2185 limb | MINOR | Accepted | A10 gains the limb: keep, or remove the extraction tool, the verdicts JSON or the record's lines; a real value goes to XC-CRED |
| R13B2-10 ml#2184's and ml#2185's limbs | MINOR | Accepted (with R13B1-15) | As R13B1-15 |
| R13B2-11 "next-day" 14:00Z | NIT | Accepted (with R13A-09) | As R13A-09 |
| R13B2-12 The flood-3 record's short form | NIT | Accepted | `…CURSOR-FLOOD-3-DISPOSITION.md` at each reference |
| R13B2-13 "rounds 4–10's cases" | NIT | Accepted | "rounds 4–12's cases"; the ninth instrument cites `EX/round12-reconciliation.md` |
| R13B2-14 "now, in S0.3" | NIT | Accepted | "in S0.3, once this plan merges" |
| R13B2-15 "before the running services carry F-S10's fix" | NIT | Accepted | "before H-22 had lifted for the relays they carry" |
| R13B2-16 R-DATA's gate given as P3-03 alone | NIT | Accepted, then overtaken by the drift | R-DATA was cut as juniper-data 0.17.0 on 2026-10-08 before its gates; the owner's fix-forward ruling replaces the sentence |

## Drift taken in

v1.13.0 takes in the drift after the 2026-10-08T22:16Z census, measured by the census tool on 2026-10-10 at 18:32Z (`--since 2026-10-08T22:16:00Z`), 18:40Z (`--since 2026-10-10T10:45:00Z`), 20:12Z and 20:30Z, with spot GETs to 20:42Z, and mapped row by row in a read-only drift brief (session scratchpad, not archived; its sources are the PRs, commits, Releases and PyPI records named here). The reconciler re-checked the items that change an action.

- **Phase B merged** (ml#2199, 2026-10-09T03:53Z; its handoff ml#2201). §8's STOP is cleared, rounds 2–7 are folded in, and the owner's DEFECT-1 ruling is in the design: P0 step 10 removes retention, step 11 restores `2W:1D,6M:1W,2Y:1M,5Y:2M` after AC-4's first drill, and that first pass deletes 5 of job 2's 9 pre-recovery filesets, 2026-09-18's among them, after their dlists are copied aside. It merged with O-12 open, without B11 (P1-12) and with no pre-push scan, so S0.3's after-the-fact read now covers its 2,824 new record lines. It left `docs/REFERENCE.md`'s resume advice (L720, L779) and the watchdog's alert (L231) as they were.
- **B9** (ml#2203, 2026-10-10T10:49Z). juniper-ml's `.gitleaks.toml` loads gitleaks' defaults and one content rule, with 32 commit-scoped ignores, two of them the unrotated S-1 literal; hook and CI pin 8.24.3. juniper-data's, juniper-canopy's and juniper-deploy's configs still define no rule. Measured by the gate's probe mode on 2026-10-10: `main`'s new config finds 9 of the 32 planted classes, the gate's interim rules 31, the old config 0. XC-LEAKS's step 3 ran first for juniper-ml, before its steps 1 and 2.
- **R-OBS-SC and R-DATA released ahead of their gates.** juniper-observability 0.4.1, juniper-service-core 0.7.1 and juniper-data 0.17.0 were cut on 2026-10-08 on the owner's instruction and served by PyPI on 2026-10-10, without P3-07, P3-03 or P3-09. The first lock round followed (recurrence#199, data#478, cascor#711, canopy#739). data#479 then cut juniper-data 0.17.1 (floors and the lock only; Release `v0.17.1` at 20:37:25Z; its PyPI publish waits at the gate), so the data fix-forward the owner ruled owed is 0.17.2 unless 0.17.1 is withdrawn.
- **The P12 chain started.** juniper-recurrence-model 0.4.0 and juniper-data-client 0.6.0 were cut on 2026-10-10 and wait at their PyPI gates. data-client 0.6.0 carries F-S10 unfixed: the reconciler compared `juniper_data_client/client.py` at `v0.5.0` and `v0.6.0` (the `RequestException` wrapping is identical, and a key from `JUNIPER_DATA_API_KEY` is used unstripped). recurrence#196 and #198 widened recurrence's caps; cascor and `juniper-ml[clients]` have no ceiling on data-client; canopy's cap stays `<0.6.0`.
- **W1.11 done** (deploy#243, deploy#245, ml#2190; equities plan v1.5.2, ml#2209). The pin, floor and smoke PRs opened as drafts before juniper-data 0.17.0 was served, against the plan's rule, and merged after.
- **P12 Phase 1 wave 2 merged** (ml#2195, canopy#732, canopy#733), the last applying R7 pending A9.
- **Flood-3 follow-ups.** Five of the record's §4 defects were fixed on 2026-10-08 (ml#2187, cascor#710, data#476, canopy#730 and the Sequence Safety docs PRs), the cleanup tool's empty lost-commit list among them; juniper-ci-tools 0.9.1 waits at its PyPI gate; the owner's two remaining flood-3 decisions are settled.
- **P2-06 landed** (canopy#731, with its evidence in ml#2196; the ledger's Phase 12 is owed).
- **ml#2214** landed this plan's record, so every "once this plan's PR merges" condition holds, and the pre-push gate is on `main`.
- Smaller: `docs/REFERENCE.md`'s gate key moved from L6200 to L6228 (at `d14b86e5`), and ml#2192 left a stray line in a procedure note.

## Unresolved dissent

- **H-22's remedy (R13B1-01 against R13B2-01).** Lane B1 keeps text written before a relay's fix banned until the key has been rotated; Lane B2 would publish it after the gate, `--names` and the every-line read find no refusal text. The reconciler took Lane B1's: the gate catches the key only inside the three refusal texts, and H-22 exists because a body or log can carry it in another form, which the reads would also have to recognise. Rotation makes every earlier copy harmless at once.

## Corrections to round 12's record

- `round12-reconciliation.md` and the plan's round-12 section count "23 mutants" that survived; they are 20 distinct, since both lanes found three of them (`R12AX11`/`R12B1-C2a`, `R12AX12`/`R12B1-C2b`, `R12AX20`/`R12B1-C4a`), and round 12's set's 57 entries build 53 distinct reads (R13A-05).
- The plan's round-12 re-derivation row cites "the plan's own L646 and L1024" and "the plan's L439": those are v1.11.0's lines (R13A-10).
- "All 16 of Lane B1's clause mutants": Lane B1 had 15 clause mutants and Xrl (R13A-11).

## Corrections to the handoff this session consumed

`HO/HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md`, checked item by item against the reports and `main`:

- It summarises R13B1-04 as "`len=` and `offset=` print a value-dependent count". The finding is that the check never tests the fields before `random-looking=`, so mutants that put a value's characters there survive; Lane B1's own "Not refuted" says the frozen read's `len=` and `offset=` add no content. The read's value-dependent count is R13B1-09's `names=`.
- It dates round 13 "22:57Z–23:40Z"; the lanes' own readings run from 22:58:15Z to 23:29:59Z.
- Its drift list was right at its 10:45Z census; ml#2203 (10:49Z), ml#2206 (10:59Z), ml#2190 (11:30Z) and deploy#245 (10:45:40Z) merged just after it, which the drift above takes in.
- Everything else checked held: the 81 untracked files, the frozen hashes, "19 entries give 17 survivors", and its four owner questions, which the owner answered before reconciling.

## What this reconciliation cannot support

- That the read lists every credential, or that its checks pin every clause: each round has found new survivors, and its listed limits stay open. Round 14 attacks the new pins.
- Two host facts, recorded only outside the repository on 2026-10-10: that the watchdog redeploy for job 2 ran on 2026-10-05, and that the T0 snapshot timer has copied the empty server database since 2026-10-09. Nothing here probed the host; the plan leaves both to the owner's sitting.
- The outcome of the four PyPI gates that wait on the owner (ci-tools 0.9.1, recurrence-model 0.4.0, data-client 0.6.0, data 0.17.1): live state that moved during this reconciliation and will move again. Re-probe before acting.
