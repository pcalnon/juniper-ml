# Round 11 — reconciliation of three lanes into plan v1.11.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.10.0 (sha256 prefix `9ff76f5b43fbaa64`) → v1.11.0 (`51cb559a84dcc4b2`).
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, `46093b326112bdd2` → `cb39019ad9e15f2b`: docstring only (limits, one attribution, provenance), no rule changed.
  - `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases, `f17a29fa37d4b045` → `4ff312599fe66031`: the contract check widened to the line read's four clauses and to `--all`, their control.
  - `util/ad-hoc/2026-10-05_masked_finding_shape.py`, `48a962b516c58db3` → `dd2bc7f2d88ec947`: the read rewritten to its contract.
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`, `0dcbd4a701bc2b65` → `275cc45d55a81fb4`: a future `--since` refused, and the time sent normalised.
  - All three lanes read the same five frozen hashes at the start, middle and end of their windows: Lane A at 15:31:24Z, 15:44:39Z and 16:17:04Z; Lane B1 at 15:31:31Z, 16:03:01Z and 16:24:10Z; Lane B2 at 15:31:42Z, 15:46:08Z and 16:10:37Z.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 11 was briefed on round 10's corrections and the drift v1.10.0 took in (`round10-reconciliation.md`), with the plan's gate-severity rule as amended for round 11 and its ending rule (its Validation record).
- **Lane reports** (all in this directory; R11A-, R11B1- and R11B2- IDs below are theirs):
  - `round11-laneA-reprobe.md`: 0 BLOCKER, 2 MAJOR, 8 MINOR, 6 NIT;
  - `round11-laneB1-safety.md`: 0 BLOCKER, 5 MAJOR, 7 MINOR, 2 NIT;
  - `round11-laneB2-schedule.md`: 0 BLOCKER, 1 MAJOR, 12 MINOR, 9 NIT.
- **Window**:
  - The lanes ran on 2026-10-08 from 15:31Z: Lane B2 until about 16:10Z, Lane A until about 16:17Z, Lane B1 until about 16:24Z.
  - The reconciliation ran from 16:27Z until 17:28:52Z, when v1.11.0 was frozen.
- **Method**: read-only, except the plan, the four tools above, the round-11 lane reports' archive headers and this file.
  - GitHub REST reads were GETs only, by `gh api` and the census tool. Git read with `show origin/main:<path>`, `log` and `diff --stat`.
  - Every tool change was made after all three lanes had finished. Gate and tool runs used synthetic inputs and scratch copies in the session scratchpad, and the mutation runs used scratch copies of the three tools. Real-file findings were read only as masked shapes.
  - No secret was read or printed.
- **ID coverage**: v1.10 → v1.11 drops no ID (381 in each), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan, this file, the three round-11 lane reports and the 2026-10-08 handoff pass markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No plan line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| juniper-ml's experiment driver copies the relayed error text into its records | R11B2-01 | `git show origin/main:` `util/experiments/run_experiment.py` and `util/experiments/run_suite.py` | `_detail` (L497–503) keeps 500 characters of a body's `detail`. Recurrence's train phase records `HTTP {code}: {_detail(payload)}` as its failure (L2194) and raises it (L2198); cascor's training start raises the same text (L968), as the data and generator calls do (L830, L867, L884). The suite copies a manifest's `phases` into its registry row (L776–777), appends each row to `registry.jsonl` (L1076) and prints "Degraded cells" in its report (L891). **Confirmed** |
| The watchdog the plan redeploys advises a resume | R11B1-05 | `git show origin/main:util/ad-hoc/yamaguchi_watchdog.py` | PAUSED_WITH_QUEUE is a fault (L29), an indefinite pause becomes it once a run is due (L51), and its alert ends "resume with util/ad-hoc/yamaguchi_server_api.py resume" (L231). **Confirmed** |
| The read printed windows, read few separators and numbered lines unlike the gate | R11A-02, R11A-10, R11B1-01, R11B1-03, R11B1-04 | The frozen read's source (`read_r10.py` in the session scratchpad, equal to the frozen hash) | `_SEP` was `[-_ \t]*` and `webservice` one unit; a listed line printed as windows of 30 characters before each name and 70 after, a line below cut at 240; `_read` split at LF only, and KEY mode used `read_text()`'s universal newlines. **Confirmed** |
| v1.10.0's A9 dropped W5.8 (B)'s dependency | R11A-01, R11B2-03 | `plan_v1.9.0.md` and `plan_v1.10.0.md` in the session scratchpad; the equities plan's order-of-work line | v1.9.0's A9 read "W5.8 (B, with W5.10's flag) or W5.11"; v1.10.0's dropped the flag; the equities plan does W5.10 first, then (B). **Confirmed** |
| The Phase B record's listed lines did not grow | R11A-04 | `--names` with the final read over a scratch copy of `…PHASE-B-CONSENSUS-RECORD.md` from `origin/main`, counts only | 71 listed from 3,619 lines read, 0 refused, as under round 9's widening. **Confirmed** |

## The tools, tested

Gitleaks v8.30.1. All inputs are synthetic except rows 3, 4 and 6.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml`, on the final gate | Canary 32/32; the repo config zero-rule; exit 1 | Canary 32 of 32. Default rules alone 3 of 32; B9-class rules alone 31 of 32; `.gitleaks.toml` 0 of 32, ZERO-RULE; exit 1 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 181 cases, on the final tools | Each as its case states | **181 of 181 as expected**, exit 0, 17:09:50Z–17:18:11Z, the four tools' hashes checked equal to the final ones before and after |
| 2g | The read's contract check, widened. Whole lines: a value in a table cell after a long description, by a passphrase label and by an env name; a JSON value past column 245 below its name; a value line that is itself listed; a one-line JSON setting. Depth: the 4th and 5th non-blank lines below, and the line above. Markers: a PEM line, the three refusal texts, `-kfile`, `Authorization`. Names: a tab, dots, "web service" in three words, an 18-letter lowercase value. A CR-only file. Values of punctuation alone, and of letters alternating with symbols. KEY mode: bytes after multibyte text, masked text before the column, lone CRs, a KEY past the file's end. Refusals: an empty root, text that is not UTF-8 (without printing its byte), an unreadable file. `--all`: every line of every file, and five layouts outside the contract | Each value printed, masked, among its file's lines; no planted value, and no symbol of the mixed value, in any output; each refusal exit 3 | As expected |
| 2m | Mutation run: 23 mutants of the final read (its depth, its line above, its markers, its separators, its masking of names, punctuation and KEY-mode text, its numbering, its refusals and `--all`), each through the contract and names checks, on scratch copies of the three tools equal to the final hashes | The baseline passes; each mutant is caught | The baseline passes; 23 of 23 caught, every one by the contract check. The names check catches none, and this round adds no case to it |
| 3 | This plan's PR files, as scratch copies made after the last edit | 0 | Exit 0 with the one accepted key (`round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`), and exit 2 without it. The read listed 264 lines in the 65 files (10,641 lines read, none refused) and printed 129 above and 797 below them. Every printed line in the ten files changed since round 10's read (514) and every printed line above or below a listed one with three masked runs or fewer (81) was screened in-process against a word list: 78 of the first hold a run of 12 or more letters or a random-looking token, and 11 of the second a run outside the list. Each was classified in-process (the word list, a path's shape, its count across the 65 files), and the ones left were read: words, labels, code identifiers, the read's own flat credential names and one `\n` artifact. An `--all` pass counted 839 random-looking tokens: 821 paths, file names or dated names, 7 identifiers made of words, and 11 identified in-process: the bytecode switch's name (8), the read's flat credential names (2) and the regression's alphabet for synthetic values (1). None is credential-shaped |
| 4 | The 40 real files of round 6's false-positive sample, on the final gate | Workable | 49 findings in 13 files, the same 49 keys as v6 |
| 5 | The census tool, with `--since 2027-10-08T00:00:00Z`, `--since notatime` and `--since 2026-10-08T21:38:00+05:00` | Exit 3, exit 3, and the offset form sent as UTC | Exit 3 for each of the first two, and nothing read; the third exits 0 and asks for merges since `2026-10-08T16:38:00Z`, listing ml#2184 (16:40:26Z) |
| 6 | The Phase B record (S0.3), as row 5 of the re-derivations | 71 listed lines | 71 from 3,619 lines read; output kept in the scratchpad, counts only |

## Dispositions

| Finding | Sev | Disposition | Applied in v1.11.0 (plan) or the tools |
| --- | --- | --- | --- |
| R11A-01 A9 lost W5.8 (B)'s dependency on W5.10 | MAJOR | Accepted (re-derived; with R11B2-03) | A9: "W5.8 (B, needs W5.10 first) or W5.11, and its release (0.6.0 or 0.7.0), with W5.10's acceptance and placement if (B)"; Group B asks W5.10 only if A9 chose W5.11. Round 10's disposition of R10B2-11 said A9 asks W5.10; it was applied in Group B. Recorded here, not in place |
| R11A-02 Dots and other separators defeated the B9 pattern | MAJOR | Accepted (re-derived; fixed and tested, with R11B1-04) | `_SEP` takes up to three separator characters of any kind; row 2g's dotted case; mutant M16 |
| R11A-03 The 732 count read two drafts | MINOR | Accepted (re-derived) | The plan's round-10 section: 731, 717 and 14 on the frozen files (732 and 15 on the pass that read two drafts). The read's docstring: copies made after the last edit. Recorded here as a correction to `round10-reconciliation.md`'s tools row 3 |
| R11A-04 S0.3's "more since round 10" was unmeasured | MINOR | Accepted (re-measured) | S0.3: 71 after round 9's widening, and rounds 10 and 11 add none (row 6) |
| R11A-05 `Schedule.Time`'s stored format is on `main` | MINOR | Accepted | H-23: Unix seconds (`…INTEGRATED-DESIGN.md` L293), the stored value read back first and the new one after |
| R11A-06 #2166's suite pins `run_experiment.py` | MINOR | Accepted (with R11B2-11) | §8's row: #2136, #2144, #2147, #2166 and #2169 |
| R11A-07 A value shaped like a credential name printed | MINOR | Accepted (stated; see Unresolved dissent) | Clause 3 of the read's contract: the one value that shows is one spelled only in the read's credential words and shaped like a name, which the read cannot tell from a name |
| R11A-08 16–19-letter one-case runs scored 0 | MINOR | Accepted (fixed and tested) | `random_looking` flags 16–19 letters at 3.6 bits; row 2g's 18-letter case |
| R11A-09 GitHub misreads some valid `--since` forms | MINOR | Accepted (fixed and tested, with R11B1-10) | The census tool sends `--since` as UTC with a `Z` (row 5) |
| R11A-10 A CR-only file was one line to the read | MINOR | Accepted (fixed and tested, with R11B1-03) | `_read` splits a file with no LF at its CRs, in every mode; row 2g; mutant M15 |
| R11A-11 Four new bare IDs | NIT | Accepted (with R11B2-17) | Each carries its report's filename |
| R11A-12 Sitting item 8's A10 bullet | NIT | Accepted (with R11B2-15) | It names ml#2183's limb; after ml#2184 that limb is all A10 holds (Drift) |
| R11A-13 57 commits is the snapshot's count | NIT | Accepted (with R11B2-12) | Wave 1's port rule and R-CASCOR: 57 at the snapshot, 63 at v1.10.0's freeze |
| R11A-14 R10B1-06 is over-reach, not a miss | NIT | Accepted | The instruments' round-10 bullet: R10B1-03..05, with R10B1-06's over-reach listed apart |
| R11A-15 Two counts in round 10's record do not reproduce | NIT | Accepted; recorded here, not in place | In `round10-reconciliation.md`: the round-1 validator report holds 20 occurrences of "transcript" on 17 lines, not 22; the 110 listed lines in changed files reproduce as 99 against the round-9 final copies and 102 against the earlier ones |
| R11A-16 Five of round 10's six MAJORs were re-derived | NIT | Accepted | The plan's round-10 section: five of the six (R10B1-03 was fixed and tested), and R10B2-08's ledger rows |
| R11B1-01 The read printed windows, not lines | MAJOR | Accepted (re-derived; fixed and tested) | The read prints each listed line whole, the line above and the five below, each line once; a listed line below another prints as its own entry. The five layouts are in row 2g; mutant M6. A listed line now prints its value, masked, so the severity rule needs no new clause |
| R11B1-02 Punctuation and name-shaped values printed | MAJOR | Accepted in part (fixed and tested; two proposals not applied, see Unresolved dissent) | The read masks each run of other non-blank characters by its length, as it masks letters and digits (row 2g's punctuation and mixed values; mutant M19). Clause 3 states the name-shaped case (R11A-07). Row q: the random-looking count is a selector, not a proof |
| R11B1-03 KEY mode numbered lines unlike the gate | MAJOR | Accepted (re-derived; fixed and tested, with R11A-10) | KEY mode reads through `_read` and refuses as the other modes do, and a KEY whose line the file lacks is refused (exit 3); row 2g; mutants M15 and M21 |
| R11B1-04 Dotted and three-word names were not listed | MAJOR | Accepted (re-derived; fixed and tested, with R11A-02) | `_SEP` widened; "web service" read as two parts; row 2g; mutants M16 and M17 |
| R11B1-05 The watchdog advises the resume H-23 forbids, and Procedure B moved by a day | MAJOR | Accepted (re-derived) | H-23: during the hold the watchdog reports PAUSED_WITH_QUEUE once job 2 is due and advises a resume; do not resume until AC-4's first drill or the remedy. Procedure B POSTs a time past AC-4's first drill, as A0, A and A2 do |
| R11B1-06 Recurrence's training-status relay on `main` | MINOR | Accepted | Overview 2 and H-22 name it; S0.11 drives `GET /v1/training/status` after a failed run, through the recorder's mapped and unmapped branches; the port rule drives every relay on the port's own commit |
| R11B1-07 The check caught 3 of 14 mutants | MINOR | Accepted (fixed and tested) | The contract check catches each of 23 mutants (row 2m), the 11 survivors among them. The severity rule: from round 12, a reconciliation that changes the read reruns the mutation run |
| R11B1-08 An empty root passed | MINOR | Accepted (fixed and tested) | The read refuses a root with no regular file and prints how many files and lines it read; XC-PRESERVE checks that count against the PR's changed-file list; mutant M13 |
| R11B1-09 S0.13 missed ml#2183's head commits | MINOR | Accepted | S0.13 reads its head commits' messages, every version of every file in them, and the branch name |
| R11B1-10 A future `--since` read as "no merges" | MINOR | Accepted (fixed and tested, with R11A-09) | Refused, exit 3 (row 5) |
| R11B1-11 Four layouts outside the contract | MINOR | Accepted (one closed, three listed) | The read prints the line above, which closes (a); row 2g; mutant M14. (b)–(d) are listed limits in both docstrings, and row 2g now pins `--all`, their control, over five such layouts (mutants M22 and M23) |
| R11B1-12 Wikis and discussions | MINOR | Accepted | XC-LEAKS note 1: export them too, or record them as a gap |
| R11B1-13 Two stale severity phrases | NIT | Accepted | "which round 10 refuted"; "neither a name nor a marker among the lines the read prints" |
| R11B1-14 h11's refusal text | NIT | Accepted | The gate's docstring: requests' and h11's refusals, and canopy's |
| R11B2-01 The experiment driver's records are an F-S10 sink | MAJOR | Accepted (re-derived) | Overview 2, H-22's list and XC-CRED name the driver's and the suite's records; XC-CRED adds a count-only search of the run and suite directories for the refusal phrase, which also bears on §12's question |
| R11B2-02 ml#2152 was missing from XC-FLEET | MINOR | Accepted; then overtaken by drift | v1.11.0 first added it to §3's table, A10 and S0.7. ml#2184 then carried it, so W1.14's PR corrects the carried section (XC-FLEET; §4 Wave 1) |
| R11B2-03 A9 and W5.10 | MINOR | Accepted (with R11A-01) | As R11A-01 |
| R11B2-04 Row r's read is S0.13's | MINOR | Accepted | XC-PRESERVE's method names S0.13 |
| R11B2-05 H-22's lift and the exit disagreed | MINOR | Accepted | H-22 and the Phase 11 rule: "through a release, a sync to the validated branch or to `main`, or a validated port" |
| R11B2-06 §8 and §9 skipped the port's validation | MINOR | Accepted | §8's `JuniperCascor1` row and §9's relay row: "as a validated port"; a new §9 row for the recurrence host legs |
| R11B2-07 The after-upgrade run had no slot | MINOR | Accepted | Security step 5 split: the owner upgrades; a session runs S0.11's relay tests with the DSNs empty; then the owner restarts. Step 4's lock PRs get the same run |
| R11B2-08 S0.13 held up sitting item 8 | MINOR | Accepted | S0.13 gates only A10's ml#2183 limb, which moves to the mid-wave sitting if S0.13 is not done |
| R11B2-09 data#454's entry had no owner | MINOR | Accepted | R-DATA: P3-03 writes it |
| R11B2-10 P1-08 checked a step no procedure holds | MINOR | Accepted | H-23: the fold-in carries the step into A0, A and A2, so P1-08 reviews it; a restore before then applies it with the read-back as its only check |
| R11B2-11 #2166 | MINOR | Accepted (with R11A-06) | As R11A-06 |
| R11B2-12 57 or 63 | MINOR | Accepted (with R11A-13) | As R11A-13 |
| R11B2-13 Row r has no manifest | MINOR | Accepted | Row r: "Done except its manifest", which S0.1's actor writes |
| R11B2-14 A10's limb was narrow | NIT | Accepted | A10: the logs, the recordings and the reports quoting them; keep only if S0.13 finds no relay text; S0.13's record goes into A10's ask |
| R11B2-15 Sitting item 8's A10 bullet | NIT | Accepted (with R11A-12) | As R11A-12 |
| R11B2-16 §10's P2 list | NIT | Accepted | §10 puts P2-03 and P2-04 ahead of `…phase11-landed.md`'s item 4 |
| R11B2-17 Bare IDs, old and new | NIT | Accepted (with R11A-11) | Each carries its file; the drift bullet for v1.10.0 names the three reports |
| R11B2-18 A Recurrence-route bullet nested under the port rule | NIT | Accepted | Moved back under the Recurrence route |
| R11B2-19 The drafts' files and the metric | NIT | Accepted; then overtaken by drift | Brought to 14:02Z, then to 17:01Z, when none was open |
| R11B2-20 §9's quiet-window row | NIT | Accepted | P2-06's census runs and item 25's triggers added |
| R11B2-21 A10's Report column | NIT | Accepted | A10 cites `round10-laneB1-safety.md` R10B1-01, `round10-laneB2-schedule.md` R10B2-02 and R10B2-09, and `round11-laneB2-schedule.md` R11B2-14; §6's preamble says the limb carries its options in its row |
| R11B2-22 Row k's deadline in P1's lane | NIT | Accepted | "before about 11-02 (row k)" |

**Totals:** 52 findings (0 BLOCKER, 8 MAJOR, 27 MINOR, 17 NIT), all accepted, R11B1-02 in part. R11A-03 and R11A-15 correct `round10-reconciliation.md`'s counts, and R11A-01 its disposition of R10B2-11; each is recorded here, not in place. With eight MAJORs, round 12 runs.

## Drift taken in

The fleet ended after v1.10.0's freeze, outside this plan:

- **ml#2181** was closed unmerged by the owner at 16:10:16Z (Lane A's GETs), with a comment that cites the owner's flood-3 record.
- **ml#2184** merged at 16:40:27Z (`1da05a92`). It carried 16 of juniper-ml's docs drafts, corrected against `main` (ml#2125, #2152 and #2177 among them), folded in the checked pieces of #2119, #2122, #2128, #2137 and #2146, and left #2141 and #2181 closed; the drafts it names were then closed. It changed `docs/REFERENCE.md` (996 lines added, 28 removed, to 0.6.62) and eight other docs and README files.
- **ml#2185** opened at 16:57:47Z and merged at 17:17:37Z (`81d3fbb3`), with the same 49 files it held at 17:05Z. It adds `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, a `CHANGELOG.md` entry and 47 `util/ad-hoc/` files. The record was read from its branch, except its §5 per-PR tables, where one line carries a credential word. Its counts: 116 drafts in eight repositories; 25 merged as themselves, 78 carried by six consolidation PRs, 10 superseded, 3 closed as wrong, none open.
- **The census** at 17:01Z (`--since 2026-10-08T15:21:00Z`, exit 0, no UNREADABLE line): ml#2184 the only merge in the nine repositories; ml#2185 the only open PR; the newest Releases and PyPI's versions unchanged since 2026-09-24. A census at 17:26Z (`--since 2026-10-08T17:01:00Z`) found ml#2185 merged, no open PR in the nine repositories, and Releases and PyPI unchanged. Lane A's census at 15:35Z and Lane B2's at 15:33Z and 16:07Z saw 22 drafts open, and Lane A's at 16:10Z saw 21, after ml#2181's closing.

v1.11.0 takes it in: XC-FLEET rewritten as done, with what the fleet's end adds; S0.7 a check for a new flood; A10 reduced to ml#2183's limb, and the sitting-item-8 list to five items; S0.3, the success metric, the Overview, §2's P2 row, §8's docs row, the risk row, Appendix B row 23 and the drift lines. It adds two follow-ups, because two carried sections go stale on a scheduled fix: W1.14's PR corrects the section carried from ml#2152, and the fold-in's PR the one from ml#2177. The record's §4 defects go to P3's register, and three of them were already this plan's (XC-FLEET).

## Unresolved dissent

Lane B1 proposed three changes under R11B1-02, and two were not applied as written:

- **Mask a name's words after `=` or `:`.** A Kubernetes `name:` key and a JSON `"Name":` key put real names after `:`, so the read cannot tell a name from a value spelled as one. Clause 3 states the case instead, bounded to the read's 20 credential words, as Lane A's R11A-07 proposed.
- **Count a long run of symbols as random-looking.** The count stays a letters-and-digits test, and the docstring says so. Row q calls the count a selector, not a proof. Such a value now prints as one-character runs between `<P1>` runs.

Round 12 is briefed on both. Elsewhere the lanes overlapped on six themes and agreed on each: the read's separators (R11A-02, R11B1-04), its numbering (R11A-10, R11B1-03), the census tool (R11A-09, R11B1-10), A9 (R11A-01, R11B2-03), the cascor count (R11A-13, R11B2-12) and #2166 (R11A-06, R11B2-11).

## Slips on the lanes' constraints

None reached a repository or printed a real value. The owner may want to know:

- **Lane A**: four commands refused by the guard and re-issued plainly; a `git grep` that printed one public line of a certification note carrying a 16-hex passphrase fingerprint (a hash prefix on `main`, not a credential), read outside the line read; a `find` that hashed census-tool copies in earlier rounds' lane scratch; public PR text written to scratch by shell redirection; `od -c` printing two synthetic values; and the tools under test writing synthetic values to scratch files, confirmed by count.
- **Lane B1**: two commands refused and re-issued; three synthetic inputs first named `.env`, then renamed; bare CRs written into synthetic inputs with `sed -i`, after which the harness echoed those synthetic files, with their invented values, back into the session; a scratch copy of the read made and mutated as a script file, restored at the end; and a harness task-output file left unread.
- **Lane B2**: two commands refused and re-issued; one command that printed ml#2152's added `docs/REFERENCE.md` lines, two of them carrying requests' refusal sentence as a template and as a placeholder; one locate that printed the first 12 characters of 17 lines of `…round3-fold-in-pending.md`; a public file list written by redirection; and directory listings of the three trio environments.
- **The reconciler**:
  - two commands refused by the guard (a loop, and `sed` with a program computed at run time) and re-issued plainly;
  - plan edits made by inline Python on standard input;
  - `python3 -m py_compile` wrote three bytecode files into `util/ad-hoc/__pycache__/` (gitignored), removed at once;
  - two background runs stopped: one tested tools that were about to change, and one wrote to the harness's task file, which this session does not read;
  - the harness compacted the session's context once during the reconciliation, where the handoff rule asks for a handoff. Every input was re-read from files afterwards.

## What this reconciliation cannot support

- That round 11's corrections, the read's four clauses or the drift edits introduced no new error. Round 12 is briefed on exactly that.
- That the gate, or the gate with the line read, catches every way a secret can be written: the contract states what the read covers, and both docstrings list what they miss.
- That ml#2183's files hold no credential (S0.13 owes that read), or that ml#2185's do not: this session read its record but for §5's tables, and of its 47 tools only the extraction script's opening lines.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after the freeze.
