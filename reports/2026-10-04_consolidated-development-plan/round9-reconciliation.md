# Round 9 — reconciliation of three lanes into plan v1.9.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.8.0 (sha256 prefix `954cbb0b189de496`) → v1.9.0 (`ffeca51e2d86255f`).
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, v6 (`a21289f304370d88`), rewritten a seventh time as v7 (`8dc176bcf25a5b62`).
  - `util/ad-hoc/2026-10-05_gate_regression.py`, from 163 cases (`ae25c2d754646d73`) to 180 (`c772b21ca53db611`), a check of the line read among them.
  - `util/ad-hoc/2026-10-05_masked_finding_shape.py`, from `79dccc0c80d563e3` to `7decf250a3ae68ba`: the line read widened and made to fail closed.
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`, made to fail closed (`b7823b6400d30e2b`).
  - All three lanes read the same four frozen hashes at the start, middle and end of their windows.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 9 was briefed on round 8's corrections and the drift v1.8.0 took in (`round8-reconciliation.md`, "Drift taken in"), with the plan's gate-severity rule (its Validation record).
- **Lane reports** (all in this directory; R9A-, R9B1- and R9B2- IDs below are theirs):
  - `round9-laneA-reprobe.md`: 0 BLOCKER, 1 MAJOR, 7 MINOR, 4 NIT;
  - `round9-laneB1-safety.md`: 2 BLOCKER, 4 MAJOR, 9 MINOR, 1 NIT;
  - `round9-laneB2-schedule.md`: 0 BLOCKER, 4 MAJOR, 6 MINOR, 6 NIT.
- **Window**:
  - The lanes ran on 2026-10-08 from 12:21Z: Lane B2 until 12:54Z, Lane A until about 13:02Z, Lane B1 until 13:13Z.
  - The reconciliation ran from 13:13Z until 14:08Z, when v1.9.0 was frozen.
- **Method**: read-only, except the plan, the four tools above and this file.
  - GitHub REST reads were GETs only, by `gh api` and the census tool. Git read with `show origin/main:<path>`.
  - Gate and tool runs used synthetic inputs and scratch copies in the session scratchpad. Real-file findings were read only as masked shapes.
  - No secret was read or printed.
- **ID coverage**: v1.8 → v1.9 drops no ID (381 in each), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan passes markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| ml#2182 carries nine of A10's rows | R9A-07, R9B2-01 | `gh api repos/pcalnon/juniper-ml/pulls/2182`, and the PR numbers its body names | Open, created 11:37:54Z by the owner's account, auto-merge armed, 29 files. Its body names ml#2121, #2124, #2127, #2138, #2140, #2147, #2149, #2150 and #2159, and none of #2119, #2122, #2125, #2128, #2137 or #2181. **Confirmed** (it merged at 13:37:39Z; Drift) |
| canopy#729 carried A10's canopy rows | R9B2-01, drift | `gh api repos/pcalnon/juniper-canopy/pulls/729` | Created 12:03:03Z, merged 12:25:33Z; its body names #698, #699, #700, #701 and #704. **Confirmed** |
| A branch from the recurrence tag rolls the primary back | R9B2-03 | `gh api repos/pcalnon/juniper-recurrence/compare/juniper-recurrence-v0.5.0...be081fae` | `ahead`, 19 ahead, 0 behind. **Confirmed** (`be081fae` is the primary's commit in `…p1-wave1-in-flight.md`; the checkout itself was not read) |
| P2's Phase 11 is an open PR carrying the census evidence | R9A-01, R9B2-02 | `gh api repos/pcalnon/juniper-ml/pulls/2183` | Open, created 12:30:25Z, not armed, 170 files. **Confirmed** (it merged at 12:55:44Z; Drift); its files were not read here (both lanes read them masked, and Lane A gated them) |
| The final v6's own config, as text | R9A-02 | The frozen v6's `b9.toml` (sha256 prefix `731951c4ab1718b2`, 12 rule blocks each spelling `pass(?:word\|phrase)`), copied and gated | Exit 2, 32 findings: 31 `juniper-b9-pipe-cell`, 1 `juniper-header-refusal`. **Confirmed**: round 8's row 6 (44) ran on a pre-final build |
| The census tool fails open | R9A-08 | Read: `gh()` returned `None` on any failure and every caller substituted an empty list. After the fix, a run with `GH_HOST=gh.invalid`, so that every `gh api` call fails | 27 UNREADABLE lines (nine repositories, three sections), no "0 open", exit 3. **Confirmed and fixed** |

## The rewritten gate, tested (v7)

Gitleaks v8.30.1, on the final v7 (`8dc176bcf25a5b62`). All inputs are synthetic except rows 3 and 4.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 32/32; the repo config zero-rule; exit 1 | Canary 32 of 32. Default rules alone 3 of 32; B9-class rules alone 31 of 32; `.gitleaks.toml` 0 of 32, ZERO-RULE; exit 1 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 180 cases (`c772b21ca53db611`) | Each as its case states | **180 of 180 as expected**, exit 0, finished 2026-10-08T14:04Z. An earlier full run failed 2f by chance (2f) |
| 2a | 136 formats that must be found (exit 2). Round 9 added the nine swallow layouts of R9B1-01: after `cd …;`, inside a longer `--set` list, after another query parameter, an empty `_FILE` after `MODE=full;`, a systemd `Environment=` line, after `&&`, after `MODE=full;` and a blank, inside a table cell, and after a YAML `command:` key | 2 | 2 in all 136 |
| 2b | 15 that must pass (exit 0). Round 9 added: a path key after `cd …;` and in an `Environment=` line (R9B1-01's fix must not report it), an env table description cell, a prose word after a code-spanned env name, `Field(default=None)` under an annotated union, an f-string placeholder, an italic `*(required)*` cell (R9B1-11), and a credential name assigned a placeholder after an empty path key, as `round8-laneA-reprobe.md` L25 quotes it (row 3) | 0 | 0 in all 15 |
| 2c | 26 that must refuse (exit 3), unchanged | 3 | 3 in all 26 |
| 2d, 2e | Accept keys; concurrency | As before | As expected |
| 2f | The line read (`--names`, new): a Kubernetes `env:` list, an argv list one item per line, five name and marker forms, values made of structural words and of non-ASCII letters, a clean control; then a symlink, UTF-16 text without a byte-order mark, and a mode-000 directory | Every planted line listed, the lines below printed, no planted value in the output; exit 3 for each refusal | As expected. One earlier full run failed it by chance: a value that must show as random-looking fell under the shape tool's 4.0-bit cut, as about 4% of the regression's 24-character random values do (200,000 draws). The two such values are now 24 distinct characters, about 4.58 bits; alone, the check passed 30 of 30 |
| 3 | This plan's PR files, as scratch copies | 0 | Exit 0 with one key accepted after reading: `round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`, a placeholder example that lane quoted verbatim. A first pass of v7 also flagged eight placeholder examples at L25 of `round8-laneA-reprobe.md` (an empty path key, then a credential name assigned a placeholder), which R9B1-01's fix had exposed. The final v7 skips an assignment of a placeholder to a credential name, lists it under Known limits, and row 2b covers it. The line read listed 230 lines in the 56 files and refused none. Read in full, none holds a credential-shaped value; its two random-looking windows are `notes/` filename tokens |
| 4 | The 40 real files of round 6's false-positive sample | Workable | 49 findings in 13 files, the same 49 keys as v6: R9B1-01's fix, R9B1-11's allowlists and the placeholder-assignment skip change nothing on this sample |

**The census tool, re-run.** Now failing closed, it ran at 13:38Z with no UNREADABLE line. juniper-ml had 45 open PRs, all Cursor drafts; juniper-data had 13, twelve Cursor drafts and the owner's data#475 (a docs consolidation); the other seven repositories had none. Since 12:05Z, 22 PRs had merged to `main` in seven repositories (Drift, below). The newest GitHub Release per repository was unchanged since 2026-09-24, and PyPI served the same versions. Re-run at 14:02Z for the freeze, it exited 0: data#475 had merged at 13:41:48Z, juniper-data had no open PR, juniper-ml's 22 open PRs were all Cursor drafts, and Releases and PyPI were unchanged.

## Dispositions

| Finding | Sev | Disposition | Applied in v1.9.0 (plan) or v7 and the tools |
| --- | --- | --- | --- |
| R9A-01 Phase 11 would publish canopy leg logs and census recordings that H-22 keeps out of every PR | MAJOR | Accepted (re-derived; with R9B2-02) | Wave 2's Phase 11 block: the scripts and the results note go in under the scan and the masked read of every added line; the leg logs and recordings stay local until F-S10's fix runs. ml#2183 carried both and merged at 12:55:44Z, before this was applied, so A10 now asks whether they stay on `main`. XC-PRESERVE row r's route and the read rule (row r's census files read in full) likewise |
| R9A-02 The config-as-text figure came from a pre-final build | MINOR | Accepted (re-derived) | XC-LEAKS note 3: 32 under the final v6 (31 and 1), 44 on a pre-final build, 28 under v5. Round 8's row 6 and R8B1-19's disposition said 44; corrected here, not in place |
| R9A-03 XC-PRESERVE's "Measured" block gave v5's figures | MINOR | Accepted (with R9B2-09, R9B1-12) | The block now gives v7's: 179 cases, the PR's result, 49 findings in 13 files with v6's keys, citing this file |
| R9A-04 §8's `JuniperCascor1` row kept "past W1.14" | MINOR | Accepted (with R9B2-03) | §8's row: the fix in the recurrence primary (§4 Wave 1) |
| R9A-05 S0.3 kept the gate-flagged lines only | MINOR | Accepted (with R9B2-04, R9B1-03) | As R9B1-03 |
| R9A-06 `--names` read a narrower set of names than the gate | MINOR | Accepted (fixed and tested; with R9B1-08) | The shape tool's names are the gate's: B9's in any case with any separators, env-style names with an optional prefix and suffixes, any-case prefixed forms, and the API-key headers. The regression's line-read check covers a bare `API_KEY`, a doubled-underscore settings key, a prefixed `db_` name and a header |
| R9A-07 The plan named ml#2182 but not what it carries | MINOR | Accepted (re-derived; with R9B2-01) | As R9B2-01 |
| R9A-08 The census tool printed "0 open" for a failed read | MINOR | Accepted (fixed and tested) | The tool prints UNREADABLE and exits 3; a full page says more may exist. Re-derived above |
| R9A-09 A quotation had no source | NIT | Accepted | XC-P12 quotes data#409's own sentence; §10 drops the quotation marks |
| R9A-10 The P2 compaction script records its own hook check | NIT | Accepted | XC-MEM: no independent check; the P2 script records its own, the P12 pass none |
| R9A-11 The placeholder list omitted `your-…-key` and seven other endings | NIT | Accepted | XC-PRESERVE's skip sentence |
| R9A-12 Round 8 cited the fold-in handoff's lines one or two early | NIT | Accepted; recorded here, not in place | In `round8-reconciliation.md`, R8B1-08's re-derivation should read L138–147 for DEFECT-2 and DEFECT-3, and L208–213 for the interim rule. H-23 cites L138–147, which is exact |
| R9B1-01 The swallow returned whenever the `_FILE` key followed a separator | BLOCKER | Accepted (fixed and tested) | Gate: the path skip applies only when no second assignment follows in the match (`[^=]*$`), with a second skip for a path key whose value is another path-key assignment. Nine regression cases (2a) and two must-pass (2b); canary class `yaml-command.yml`. Plan: XC-PRESERVE's swallow history and fix |
| R9B1-02 The line read could not see a value below its name or a credential with no name | BLOCKER | Accepted (fixed and tested) | Shape tool: markers for `aescrypt`, `-pass pass:`, a private-key line and the refusal texts; the two lines below a name or marker with no value beside it; `--all`. Plan: the read is "beside or below"; changed files are copied with their hunk context; the gate-severity rule demotes only variants the read lists. Gate docstring: such layouts listed as limits |
| R9B1-03 S0.3 covered 1 of ml#2179's 37 files | MAJOR | Accepted (with R9A-05, R9B2-04) | S0.3: the gate, the `--names` read and the `--all` read over all 37 files, the commit message and the PR body; keys and the read recorded in P1-10's PR body; a real value to XC-CRED. §9's P1-09 row likewise |
| R9B1-04 Step 1 read no commit message and no PR, issue or Release text | MAJOR | Accepted | XC-LEAKS note 1: export commit messages and every repository's PR, issue, review, comment and Release text to an owner-only directory, scan and read them, hits to step 2; list committed binaries |
| R9B1-05 S0.11 missed response bodies and canopy | MAJOR | Accepted | S0.11: each relay test also checks the response body, raw and JSON-decoded; canopy gets its own test whatever A1 accepts |
| R9B1-06 S0.11's test could pass while the key reached Sentry | MAJOR | Accepted | S0.11: plant the key with a leading blank and a line break and search its escapes; search `vars(record)`; capture on each relay logger at the production level or by hooking `callHandlers` |
| R9B1-07 Same-line variants and two refusal escapes | MINOR | Accepted (listed) | Gate docstring, Known limits: the eight same-line variants and the two refusal escapes. Plan: "behind blanks, one or two backslash escapes and numeric HTML references". The line read lists each: a name is on its line, or a marker |
| R9B1-08 `--names` missed seven lines the gate reads, and the header | MINOR | Accepted (fixed and tested; with R9A-06) | As R9A-06, with `X-API-Key` and `Authorization` |
| R9B1-09 `--names` failed open on unreadable input | MINOR | Accepted (fixed and tested) | It walks with `os.walk(onerror=…)`, refuses symlinks, non-regular files, NUL text and non-UTF-8 text, and exits 3; the regression checks three refusals |
| R9B1-10 The masked read printed some values in clear | MINOR | Accepted (fixed and tested) | Unicode runs are masked (`<N…>`); after a name only names stay in clear; the regression checks a structural-word value and a non-ASCII value. Punctuation is still kept, and the docstring says never to paste the output |
| R9B1-11 Scan 2 flagged ordinary prose and code | MINOR | Accepted (fixed and tested) | Gate: env-style rules skip lowercase words joined by hyphens; all rules skip `{x}`, `Field(default=None…` and an italic `*(word)*`. Six must-pass cases (2b). The narrowing is listed, and the line read lists such values |
| R9B1-12 The figures were v5's | MINOR | Accepted (with R9A-02, R9A-03) | As R9A-02 and R9A-03 |
| R9B1-13 §9 omitted row k and the backup-arc clause | MINOR | Accepted | §9: "P1-09, P1-10, row k's archive PR"; the push row names the every-line read |
| R9B1-14 Paths and ref names are public and unscanned | MINOR | Accepted | XC-PRESERVE's scan item and the gate's docstring: the pushed file list, the branch name and any Release title go into a scanned file |
| R9B1-15 H-23's Paused check came after the start | MINOR | Accepted | H-23: also move job 2's `Schedule.Time` to the future before the first start; if it does not read Paused, the owner stops the service at once |
| R9B1-16 Two rules had no canary class | NIT | Accepted (fixed) | Canary classes `env-table.md` and `value-name.json`; the canary has 32 classes |
| R9B2-01 ml#2182 and canopy#729 already disposed of 14 of A10's 20 rows | MAJOR | Accepted (re-derived; with R9A-07) | XC-FLEET's table: the nine carried rows close with ml#2182; canopy's are done (drift: canopy#729 merged). A10 keeps six, plus ml#2183's logs. The fold-in keeps ml#2182's backup suites green (Tier-1 item 1); §8's ml file row names ml#2182; P2-16 rebases onto its suites; §10's suite count moves by 25 |
| R9B2-02 Phase 11 contradicted H-22 | MAJOR | Accepted (with R9A-01) | As R9A-01 |
| R9B2-03 A sync to the 0.5.1 branch would roll the recurrence primary back 19 commits | MAJOR | Accepted (re-derived) | Wave 1's recurrence route: under (a), the fix on the primary's own commit, never the tag's branch; under (b), host legs run unfixed until wave 1 is taken everywhere, said in A1; §8's row |
| R9B2-04 S0.3 read only the flagged lines | MAJOR | Accepted (with R9A-05, R9B1-03) | As R9B1-03 |
| R9B2-05 XC-P12 still gave W1.11's code half to the P12 session | MINOR | Accepted | XC-P12 action 6: the P4 session opens it once PyPI and GHCR serve the release |
| R9B2-06 Two lists omitted R1's default half | MINOR | Accepted | §9's P12 Phase 1 row and Appendix A |
| R9B2-07 A9 asked a placement before the choice | MINOR | Accepted | A9 asks W5.8 (B) or W5.11, and where it ships; Group B keeps W5.9 and F-P8 |
| R9B2-08 Reverting the P12 pass returns the index near its ceiling | MINOR | Accepted | A6 and XC-MEM step 3 |
| R9B2-09 The "Measured" block was v5's | MINOR | Accepted (with R9A-03) | As R9A-03 |
| R9B2-10 A cascor pull to `main` brings R-CASCOR's unreleased content into the trio | MINOR | Accepted | Wave 1's trio route, the exit, §8 and §9: after P3-05 with #683's note applied, or on the primary's own commit |
| R9B2-11 §7.1 said "rounds 4–7" | NIT | Accepted | "rounds 4–9", with round 8's and round 9's citations |
| R9B2-12 P8-09 was "net-negative" | NIT | Accepted | Appendix A and Appendix B: an index line rewrite |
| R9B2-13 §10 did not note P1-12 in the fold-in | NIT | Accepted | §10's P1 list |
| R9B2-14 Item 3 did not name the forward-port | NIT | Accepted | §7.1 item 3 |
| R9B2-15 Changed lines cited IDs and a lane without filenames | NIT | Accepted | The Validation record's round sections map their ID prefixes to files; the stray IDs, the lane and the verbatim report carry filenames; the matrix is named in the P2 ledger; the 75-of-318 count is "this session's link count" |
| R9B2-16 Row k's archive PR had no place | NIT | Accepted | Appendix A, P1, T2 |

**Totals:** 44 findings (2 BLOCKER, 9 MAJOR, 22 MINOR, 11 NIT), all accepted. R9A-02 and R9A-12 correct `round8-reconciliation.md`; they are recorded here, not in place.

## Drift taken in

v1.9.0 takes in the following, and round 10 checks it.

- **From round 9's lanes and the reconciler's re-probes after 12:05Z**:
  - canopy#729 merged at 12:25:33Z and closed A10's five canopy rows (and canopy#703); §8's canopy row no longer waits on the fleet; Appendix B row 23's canopy part is done.
  - ml#2182 is armed for auto-merge; when it merges, nine A10 rows close as carried and its suites land ahead of the P1 fold-in and P2-16.
  - ml#2183, P2's Phase 11, opened at 12:30:25Z with the census evidence (Wave 2's Phase 11 block, A10).
  - data-client#230 merged at 12:17:18Z (docs, and one docstring line in `contract.py`); the other merges were tests and docs, and no release was cut.
- **From the reconciler's census at 13:38Z and REST GETs**:
  - ml#2183 merged at 12:55:44Z, with the leg logs and census recordings that R9A-01's disposition would have kept out; A10 now asks whether they stay on `main` (Wave 2's Phase 11 block). P2's next handoff, `HANDOFF_2026-10-08_canopy-phase11-landed-f058-live-f068-filed-redesign-next.md`, files F-CANOPY-068 and makes P2-06 one design for F-055, -058 and -068, with items 25 and 26 and O17's two limbs (§2, Wave 2, Group B).
  - ml#2182 merged at 13:37:39Z, and its 25 suites are on `main` ahead of the P1 fold-in and P2-16. The nine A10 rows it carried were closed unmerged at 13:40–13:41Z (GETs at 14:02Z); A10's other six are open drafts.
  - cascor#709 (12:51:17Z) consolidated six cascor fleet PRs, and data#475 merged at 13:41:48Z. juniper-data, data-client, cascor, cascor-worker and deploy also merged fleet test and docs PRs (XC-FLEET's paragraph).
  - data#454 (13:33:18Z, authored by Copilot) turned off FastAPI 0.142's native telemetry in juniper-data's app factory. On `main`, cascor locks FastAPI 0.142.2 and canopy 0.142.4, neither sets the option, and each lock holds `opentelemetry-api` with no SDK; recurrence locks 0.141.1 (GETs of each `requirements.lock`). S0.11 records the setting.
  - No release was cut, and PyPI was unchanged.

## Unresolved dissent

None. The lanes overlapped on four themes and agreed on each:

- Phase 11 against H-22 (R9A-01, R9B2-02);
- what S0.3 must read (R9A-05, R9B2-04, R9B1-03);
- ml#2182's carried rows (R9A-07, R9B2-01);
- the recurrence primary's route (R9A-04, R9B2-03), where Lane B2 went further: the tag's branch itself would roll the primary back.

## Slips on the lanes' constraints

None reached a repository or printed a real value. The owner may want to know:

- **Lane A**: a `git fetch --dry-run` at the start, which updated no ref but may have written objects to the shared object store; seven commands refused by the command guard and re-run plainly; name, size and count-only reads outside the worktree (the census backup directory and the auto-memory directory); a v5 gate run that overwrote its scratch `b9.toml`, caught and re-run; and one exit code taken through a pipe, so its report gives the tool's printed result instead.
- **Lane B1**: two commands refused by the guard and re-issued plainly; scratch copies of real repository files made with shell commands rather than the file tool (no planted values); cascor's logging configuration and three code-search listings read by REST GET outside this repository; and two synthetic values typed into a `grep -c` command line (only a count was printed).
- **Lane B2**: two compound commands refused by the guard and re-issued plainly; the shape tool's KEY mode used with hand-built keys on four lines of ml#2183's public logs (masked output only); scratch copies written by shell redirection.
- **The reconciler**: none. It edited no repository file during the lanes' window. Its census failure test pointed `GH_HOST` at an invalid host name, so that each of its 27 calls failed.

## What this reconciliation cannot support

- That round 9's corrections, gate v7, the widened line read or the drift taken in introduced no new error. Round 10 is briefed on exactly that.
- That the gate, or the gate with the line read, catches every way a secret can be written.
- That ml#2183's census files hold no credential. Two lanes read them masked and one gated them; shape is not content.
- That the recurrence primary is still at `be081fae`.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after 14:08Z on 2026-10-08.
