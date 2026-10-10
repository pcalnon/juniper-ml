# Round 7 — reconciliation of three lanes into plan v1.7.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.6.0 (sha256 prefix `c508e4e48be015c9`) → v1.7.0.
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, v4 (sha256 prefix `7445505b5a1117eb`), rewritten a fifth time as v5. Its first draft (`9a2f178d576a2136`) was amended during this reconciliation; the final v5 is `5a6d1bd81ce6cbec`.
  - `util/ad-hoc/2026-10-05_gate_regression.py`, from 89 cases (`33fa27d7c6eb6d71`) to 123 (`dad7dc3339bf818e`).
  - New: `util/ad-hoc/2026-10-05_masked_finding_shape.py` (`83393986a6bc3192`), which prints a masked shape around each gate finding, so a finding can be classified without printing its value.
  - All three lanes read the same plan and gate hashes at the start, middle and end of their windows.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 7 was briefed on round 6's corrections only, and it ran the Lane B attack that round 6 skipped (`round6-reconciliation.md`, "What did not run").
- **Lane reports** (all in this directory):
  - `round7-laneA-reprobe.md`: 1 BLOCKER, 0 MAJOR, 7 MINOR, 6 NIT;
  - `round7-laneB1-safety.md`: 2 BLOCKER, 5 MAJOR, 6 MINOR, 2 NIT;
  - `round7-laneB2-schedule.md`: 0 BLOCKER, 2 MAJOR, 11 MINOR, 7 NIT.
- **Window**:
  - The lanes ran 2026-10-05, 21:42Z–22:34Z.
  - The reconciliation ran from 22:34Z to 23:20Z, and the session then sat idle until 2026-10-08T10:13Z. It resumed by re-running the live census, took in the drift that changes an action, and closed at 10:30Z on 2026-10-08, when v1.7.0 was frozen.
- **Method**: read-only, except the plan, the gate, the regression and the new shape tool.
  - GitHub REST reads were GETs only, through `util/ad-hoc/2026-10-05_ecosystem_live_census.py` and `gh api`. Git ran `fetch origin main`, then read with `show origin/main:<path>`.
  - Gate runs used synthetic inputs and scratch copies of tracked files in the session scratchpad. Real-file findings were read only as masked shapes.
  - No secret was read or printed.
- **ID coverage**: v1.0 → v1.7 and v1.6 → v1.7 drop no ID, and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan passes markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line is over 512 characters.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| P12's Phase 1 wave 1 and two juniper-ml records merged after the 10:25Z snapshot | Lane A's drift section | `gh api repos/pcalnon/<repo>/pulls/<n>`, `merged_at` | data-client#222 14:00:36Z, ml#2157 13:42:59Z, deploy#242 14:20:58Z, recurrence#193 14:32:26Z, data#451 14:33:41Z, recurrence#191 20:35:57Z, canopy#722 20:35:58Z, recurrence#192 21:50:11Z, ml#2164 21:52:27Z, ml#2168 22:12:10Z, all on 2026-10-05. **Confirmed** |
| A10's drafts are open | R7B2-02, R7B2-11 | `gh pr list --state open` for juniper-ml and juniper-canopy, 2026-10-08 | ml#2119, #2121, #2122, #2124, #2125, #2127, #2128, #2129, #2147, #2149 and #2150, and canopy #698–#701 and #704: all open Cursor drafts. **Confirmed**. canopy#703, a docs-only draft, is open too and left to mid-wave |
| `JuniperCascor1` holds recurrence as an editable install | R7B1-12, R7B2-12 | `__editable___juniper_recurrence_0_5_0_finder.py` and `__editable___juniper_data_client_0_5_0_finder.py`, their `MAPPING` lines | `juniper_recurrence` maps into the recurrence primary checkout, and `juniper_data_client` into the data-client primary. Recurrence's model and client, and cascor-client, are editable there too. **Confirmed** |
| Phase D's rulings need no prep, Phase D is one sitting, and step 7 needs P1-12 | R7B2-01, R7B2-05 | `…RECOVERY-PLAN.md` L201, L229, L272, L297, L309, L310 | L201: Phase D is "one sitting, passphrase in hand … with nothing else interleaved". L229: B11 is built only if step 5's counts are non-zero. L272: step 7's probe uses every candidate B11 extracted. L297, L309 and L310 each give O-1's, O-13's and O-14's recommendation. **Confirmed** |
| P1-21 is D-12's dispositions, not a Phase D input | R7B2-04 | `extraction-P1-backup.md` L48 (as archived) | "Disposition each D-12a inherited item", OWNER-DECISION (D-12). **Confirmed** |
| The unnamed twins | R7B2-10 | `extraction-P4-release-P11-k8s.md` L114–116; `extraction-P6-perf.md` L97–98; `extraction-P7-logging.md` L90; `extraction-P3-defect-register.md` L146–148 (lines as archived, header included) | D-2 is the next data release, with its version; D-3 is the obs/sc release procedure; D-4/5/6 are canopy, cascor and recurrence cut timing. P6 OD-13 is P2's O13, and OD-14 is the cascor cut. P7 D7 is the cascor and cascor-model cuts. D-08 and D-09 are questions inside D-10's parked rows. **Confirmed** |
| Lane A1's py07 and py08 are the annotated shape | R7A-04 | `round6/a1/cases/X_matrix_R/py07.py`, `py08.py` in the session scratchpad, values masked | A module constant `NAME: str = "…"`, and a dataclass field `name: str = "…"`. The final v5 reports both (exit 2). **Confirmed** |
| P1's state moved after the 22:33Z census | drift | `git show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`, and the section headings of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` (both from ml#2179, 2026-10-05T22:47:04Z) | Phase B is a local frozen commit, `c3d0e890`, in `sorted-stargazing-garden`, with a bundle under `Juniper/backups/`. Round 3 reported; R3B's DEFECT-1..4 are new, and DEFECT-1 needs an owner ruling. The record holds round 2's lanes A, B and C, the ml#2114 and ml#2115 lanes, round 3's lanes A, B and C, both briefs and the handoff validations. It does not hold `…RECOVERY-PLAN.md`'s round 1 or Phase A's narrow lane (XC-PRESERVE row k). **Confirmed** |
| The five backup drafts' CI | drift | `gh api repos/pcalnon/juniper-ml/commits/<head>/check-runs`, 2026-10-08 | ml#2137: 26 success, 1 skipped. ml#2181: 22 success. ml#2138: 4 failures. ml#2140: 1 failure. ml#2159: 5 failures. **Confirmed** |
| Script and handoff names that v1.7.0 cites | R7A-08, R7B2-20 | `ls` of each path in this worktree, and `git show origin/main:` for files added on `main` after this worktree's base | All exist. `HO/HANDOFF_2026-09/HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` exists. `…round3-fold-in-pending.md`, `…PHASE-B-CONSENSUS-RECORD.md` and `…p1-wave1-in-flight.md` are on `origin/main` (`d3971e10`), not at this worktree's base (`cf711cf4`); the PR branches from `main` |

## The rewritten gate, tested (v5)

Gitleaks v8.30.1, on the final v5 (`5a6d1bd81ce6cbec`) unless a row says otherwise. All inputs are synthetic except rows 3 and 4.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 25/25; the repo config zero-rule; exit 1 | Canary 25 of 25 in five runs: two on the first draft, three on the final. B9-class rules alone: 24 of 25. `.gitleaks.toml`: 0 of 25, ZERO-RULE. Exit 1. The default rules alone found 3, 3, 2, 3 and 3 of 25, because the canary draws fresh random values each run and the default rules' entropy and stopword checks keep some draws and drop others. The union found all 25 every time |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 123 cases | Each as its case states | **123 of 123 as expected**, exit 0, finished 2026-10-08T10:23Z. The first draft passed its own 121 at 2026-10-05T22:57Z. Groups below |
| 2a | 90 formats that must be found (exit 2). Round 7 added: the same-line swallow, twice; the code-span, bold, italic, underscored and qualifier labels, eleven cases; the `_FILE`-then-plain API-key layout, twice; the three refusal texts; a value containing a B9 name; `aescrypt` on argv, twice; a Python repr; JSON-escaped quotes; an annotated default; a flag value containing `-dir-`; lone-CR line numbering; a pair that spans lines, reported as START-END; the two part-boundary gaps; and a value that starts with a backslash | 2 | 2 in all 90, at the stated line where a case states one |
| 2b | 5 that must pass (exit 0): whole-value placeholders, path names, a `.gitleaksignore` baseline, the allow marker in prose, and a Markdown-escaped placeholder (`\<name\>`) | 0 | 0 in all 5 |
| 2c | 26 that must refuse (exit 3). Round 6's 18, with seven BOM layouts now refused: UTF-16 LE and BE, a BOM before ASCII in either order, UTF-32, a UTF-16 BOM before a UTF-8 line, and `FF FE` before Latin-1. Plus a second `--scan-dir` | 3 | 3 in all 26 |
| 2d | Accept keys: two findings on one line | Two keys; one accepted → 2; both → 0; after an edit → 3 | As expected |
| 2e | Concurrency: a secret run and a same-size clean run sharing one `--workdir`, 5 trials | The secret run never 0; the clean run never 2 | As expected in all 5 |
| 3 | This plan's PR files, as scratch copies | 0 | 0 findings, exit 0, on all 48 files at v1.7.0's freeze. The first two runs flagged the new shape tool's own source, a quoted B9 name beside a long word: once in its word list, then in the comment explaining it. Both were restructured, not accepted. Re-run on the final set, with the commit message and PR body, before the push |
| 4 | The 40 real files of round 6's false-positive sample | Workable | 43 findings in 13 files: 32 assignment, 4 pipe-cell, 5 quoted-pair, 2 swallowed. None from the default rules |
| 4a | Against v4's 37 | Each change explained | 35 keys are byte-identical to v4's. Two are gone: an escaped placeholder (`\<name\>`) after `--webservice-password=` and after `--settings-encryption-key=`, on one line of `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`, now skipped as a placeholder. Eight are new, below |
| 4b | The eight new findings, by masked shape (`util/ad-hoc/2026-10-05_masked_finding_shape.py`) | None random-looking | **None random-looking** by round 6's Lane A1 test (mixed-case alphanumeric, 16+ characters, entropy ≥ 4.0). One pipe-cell: a "passphrase file" label whose next cell is a path. Two swallowed: a `Settings Encryption Key:` label before an assignment whose value is an upper-case, hyphenated placeholder (`<U9>-KEY-VALUE-<D3>`, `<U9>-KEY-<D1>`). Five quoted-pair: SQL `Name IN ('…passphrase…', …)` lists of option names, four in two notes and one in a script |

**A narrowing found and reversed during this reconciliation.** Comparing v5's first draft with v4 on row 4 showed the two escaped-placeholder findings gone for the wrong reason. The draft's bare value could no longer start with a backslash, so a real value written `PASSPHRASE=\…` would also have passed. The final v5 accepts a backslash-led value, except `\"`, which starts the JSON-escaped form. It skips `\<name\>` only as a whole-value placeholder. New cases: `backslash-lead` (exit 2) and `md-escaped-placeholder` (exit 0).

## Dispositions

| Finding | Sev | Disposition | Applied in v1.7.0 (plan) or v5 (gate) |
| --- | --- | --- | --- |
| R7A-01 An empty `_FILE=` swallowed the secret on the same line | BLOCKER | Accepted (fixed and tested) | Gate: a new rule, `juniper-b9-swallowed`, finds a B9 assignment that starts right after another assignment's separator on one line, because matches never overlap. The path allowlist reads the key alone (R7A-03). Cases `same-line-swallow` and `same-line-webcred`; canary class `same-line.sh`. Plan: XC-PRESERVE method. Round 6's R6A1-01 disposition, "fixed and tested", held for the next-line layout only; recorded here, not in place |
| R7A-02 A Name/Value pair could be cut at a part boundary | MINOR | Accepted (fixed and tested) | Gate: the Name/Value gap is at most 3 line breaks. Each part repeats up to 9 lines of the one before it, within 20,000 bytes, and never fewer than 3. Cases `name-value-gap-boundary` and `default-gap-boundary`, each with the 60,000-byte boundary between key and value. Plan: "The gate fails closed". R6A1-09's reasoning ("no rule matches a value below its name") is corrected here, not in place |
| R7A-03 The path skip read the value | MINOR | Accepted (fixed and tested) | Gate: the `_file`/`_path`/`_dir` allowlist is anchored at the match's start and stops at `:`, `=`, `,`, `\|`, a quote or whitespace. Case `flag-dir-in-value`. Plan: "judged on the key alone" |
| R7A-04 Five matrix shapes were listed nowhere | MINOR | Accepted (fixed in part; the rest listed) | Gate: a rule for annotated assignments, which catches py07 and py08 (re-derived above; case `annotated-default`). py12 (a value set after a name check), py13 (a comparison) and m12 (a label followed by a dash) are in the docstring's known limits. Plan: "lists some of what it does not cover" |
| R7A-05 Four more repositories rescan history on dispatch | MINOR | Accepted | XC-LEAKS: "What CI rescans" names all eight; note 2 gives the four outside step 3's config PRs a small PR of their own after step 2; the rescan warning covers "any of the eight". H-17 and §9's XC-LEAKS row likewise |
| R7A-06 Each ERROR line also becomes a Sentry error event | MINOR | Accepted | Overview 2, XC-CRED and H-22 add the error event from sentry-sdk's default logging integration. "Without raising" no longer appears as a reason canopy sends no event |
| R7A-07 §6.6 was cited for rulings it does not hold | MINOR | Accepted | Wave 0 item 1 cites `…RECOVERY-PLAN.md` §6.6 for O-10 only, `EX/extraction-P1-backup.md` for N-1 and N-2, and `EX/extraction-P2-canopy.md` for O13. Group B's P1 entry now holds only Phase E's rulings, so its parenthetical names §6.6 for O-5 and O-9 |
| R7A-08 O8's 09-22 source was not named | MINOR | Accepted (re-derived) | §10 names `HO/HANDOFF_2026-09/HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` |
| R7A-09 The F-S10 restart waited for R-OBS-SC | NIT | Accepted (with R7B2-03) | Mid-wave sitting: the restarts are owner actions, each when its own input exists; one restart serves both if both are ready |
| R7A-10 B9's literal also misses `:` and quoted keys | NIT | Accepted | XC-PRESERVE: "misses all of these but a bare `NAME=`" |
| R7A-11 The sample is files, not documents | NIT | Accepted | "40 real backup files" in XC-PRESERVE and the validation record |
| R7A-12 P1-25 was called hygiene but sat at T2 | NIT | Accepted | Appendix A puts P1-25 at T6; S0.3 and Wave 2's P1 lane say so |
| R7A-13 Round 6's window end was misstated | NIT | Accepted; recorded here, not in place | Round 6's window closed at 21:40Z, not 21:45Z: `round6-reconciliation.md` was last written at 21:40:07Z and the plan at 21:40:13Z. Its L14 and L117 should read 21:40Z |
| R7A-14 Round 6 said the CLI-flag rule takes `=` | NIT | Accepted; recorded here, not in place | In `round6-reconciliation.md` L56, read: the `=` form is an assignment (`juniper-b9-assignment`), and the space-separated form has its own rule (`juniper-b9-cli-flag`). The behaviour held: the `settings-flag-*` cases exit 2 |
| R7B1-01 Code-spanned, italic and underscored names were missed | BLOCKER | Accepted (fixed and tested) | Gate: after a name, `_KEY_TAIL` takes a closing backtick, `*` and `_` wrappers, and a parenthesised qualifier. The pipe-cell name cell takes a short label with those wrappers and a trailing `:`. Eleven cases (`md-codespan-*`, `md-bold-codespan`, `md-table-bold`, `-italic`, `-colon`, `-bold-codespan`, `md-underscored-label`, `qualifier-label`, `bold-qualifier-label`); canary class `codespan-label.md`. Plan: XC-PRESERVE's list of shapes |
| R7B1-02 The default rules' separators cross lines, so the swallow remained for API keys | BLOCKER | Accepted (fixed and tested) | Gate: scan 2's line-bounded `juniper-env-credential` rule covers `*_API_KEY(S)`, `*_TOKEN`, `*_PASSWORD` and `*_SECRET` in env style. Cases `api-key-absorb` and `api-key-absorb-canopy`; canary class `api-key-absorb.env`. The docstring's "every rule matches within ONE line" now reads "every B9-class rule". Plan: XC-PRESERVE. R6A1-09's reasoning is corrected here (with R7A-02) |
| R7B1-03 The gate could not see F-S10's text | MAJOR | Accepted (fixed and tested) | Gate: `juniper-header-refusal` matches the three refusal texts that quote a key verbatim. Cases `header-refusal-502`, `-bytes` and `-canopy`; canary class `header-refusal.log`. H-22: the gate catches those three, not a body or log line carrying the key in another form, so the never-paste rule is the control. §12's F-S10 row points to H-22 |
| R7B1-04 The printed line was not always the value's line | MAJOR | Accepted (fixed and tested) | Gate: KEY's LINES is START-END when a match spans lines; lines are numbered by LF, as `sed` does, and a file with no LF at all is split at lone CRs. Cases `lone-cr-numbered-by-lf` and `multiline-key-range` (expects `3-4`). Plan: "A finding the session has read on its lines … the value can sit on the last of them" |
| R7B1-05 Realistic shapes fell outside both the rules and the list | MAJOR | Accepted in part | Gate, items 1–5 fixed: a B9 name is skipped only as the whole value (`value-holds-name`); `aescrypt` on argv (`aescrypt-ps`, `aescrypt-p`; canary `aescrypt.txt`); Python reprs, since the Name/Value rules take either quote (`python-repr-setting`); JSON-escaped quotes (`json-escaped-quotes`); annotated defaults (`annotated-default`). The docstring lists the rest: item 6 (`printf`, `echo … \| tee`), here-strings, `==`, Makefile and Go `:=`, CSV, sqlite3 `-box`, ANSI colour, XML, bytes literals, `PASS_PHRASE`, a value in double backticks, `os.environ.get(…) or "…"`, and a name and value separated only by a space. Plan: "lists some of what it does not cover" |
| R7B1-06 A second `--scan-dir` replaced the first | MAJOR | Accepted (fixed and tested) | Gate: a repeated `--scan-dir` exits 3. Case `repeat-scan-dir`. Plan: "given once"; the refusal list includes it |
| R7B1-07 S0.11's test did not say what "carries" means | MAJOR | Accepted | S0.11: each test builds the event with `sentry_sdk.utils.event_from_exception` under observability 0.4.0's options and under R-OBS-SC's, and fails if the key appears anywhere in it. The plan states what that event holds: `.message` and `.detail` before `str()`, `__notes__`, and every frame's locals unless `include_local_variables` is off, which 0.4.0 does not do. Overview 2: frame locals stay exposed until R-OBS-SC |
| R7B1-08 A BOM-led file could hide UTF-8 or Latin-1 text | MINOR | Accepted (fixed and tested) | Gate: any UTF-16 or UTF-32 BOM is refused (exit 3), R6A1-06's first option. This reverses round 6's decode-and-stage fix. The seven BOM cases in row 2c. Plan: "a file that is not UTF-8 text (a UTF-16 or UTF-32 byte-order mark included)" |
| R7B1-09 Parts overlapped by too few lines | MINOR | Accepted (fixed and tested, with R7A-02) | As R7A-02. The residue, a match across more than 3 breaks at a boundary when the lines are long, is in the docstring's known limits |
| R7B1-10 XC-LEAKS step 1 did not pin its scan | MINOR | Accepted | XC-LEAKS step 1 and note 1: a fresh `--mirror` clone; the shipped config as well as the gate's two; `--ignore-gitleaks-allow`, an empty ignore path and an explicit exit code; note 2's fingerprints from the shipped config's run. Note 3: `-U0` hunks miss a pair whose Value line alone changed. The gate's history recipe says the same |
| R7B1-11 Cascor's `get_secret` and pydantic | MINOR | Accepted | S0.11's cascor bullet: check `get_secret`'s value from both branches; raise only for the data-key callers (`app.py` L517, `manager.py` L4922), outside pydantic, with no value in the message; plant a fake inbound key too |
| R7B1-12 Recurrence runs editable from the primary | MINOR | Accepted (re-derived) | Wave 1's recurrence route and exit: host legs need the recurrence primary past W1.14. §8's `JuniperCascor1` row |
| R7B1-13 Three ways around "only exit 0 passes" | MINOR | Accepted | XC-PRESERVE method and §9: before every signed upload, with the commit message and PR body as files, run unpiped. The docstring adds `${PIPESTATUS[0]}`. This plan's own PR follows it (row 3) |
| R7B1-14 The separator claim covered only multi-word names | NIT | Accepted | XC-PRESERVE and the docstring: "inside the three multi-word names". `PASS_PHRASE` is a known limit |
| R7B1-15 Scan 1 is not CI's | NIT | Accepted | XC-PRESERVE: "gitleaks v8.30.1's default rules, with no repository allowlist. CI runs gitleaks-action's 8.24.3 with each repository's own allowlists." The gate's docstring and the title of its scan-1 config say the same |
| R7B2-01 Group B held Phase D behind late rounds | MAJOR | Accepted (re-derived) | O-1, O-13 and O-14 move to the first sitting's item 8, beside O-2 and O-7. Group B is "later sittings, each item when its input exists" and gates no Phase D step. Wave 1 item 5, §6 A2, §7.1's sittings bullet and §9's P1-18 row likewise |
| R7B2-02 A fleet draft held a Wave 0 fix and had no first-sitting slot | MAJOR | Accepted (re-derived) | ml#2147, #2149 and #2150 join §3's table and A10, as "Close (or fix by rebasing onto ml#2164)". §8 holds P2-16 and the `util/experiments/` items on ml#2147 and #2149 |
| R7B2-03 The mid-wave restart depended on its own sitting | MINOR | Accepted (with R7A-09) | The restarts leave the sitting's rulings: XC-SENTRY's after R-OBS-SC is on PyPI (Security step 5), F-S10's after the data-client fix is on its branch or R-DC-PATCH is on PyPI. The mid-wave sitting splits: D-02/D-03 once P3-07 validates, D-12/D-07 once P3-03 validates |
| R7B2-04 P1-21 sat under Phase D | MINOR | Accepted (re-derived) | P1-21 moves to "P1, before Phase E", beside O-5 |
| R7B2-05 Phase D step 7 needs P1-12 | MINOR | Accepted (re-derived) | Wave 1 item 5, §9's P1-18 row and Appendix A: P1-12 at T1, before P1-18, if Phase C step 5's count is non-zero. Wave 2's P1 lane says it moved |
| R7B2-06 Two T2 IDs were in no lane | MINOR | Accepted | P4-45 joins the P4 lane after R-CANOPY-A; P8-05 records P8-27's residuals |
| R7B2-07 P12's W1.x were scheduled in two waves | MINOR | Accepted; overtaken by drift | Phase 1's wave 1 merged (XC-P12), so Appendix A lists it as Done. Phase 1's rest is at T2 in Wave 2's P12 lane; Wave 4 holds W2–W5, with W5.4 after R5; P12-10..P12-19 left T5 |
| R7B2-08 The exit counted P3-05 through a serialization the sources lack | MINOR | Accepted | Cascor's image lock PR is Security step 4's and follows R-OBS-SC only; R-CASCOR follows P3-05 and P3-08. §7.1: 10 exit-gating items, 20 rounds, 100 runs, 10–20 days |
| R7B2-09 Group C's gating rulings had no slot | MINOR | Accepted | Group C is "asked with Group B", and the ones that gate something come before it: D4, D5 and O15 before the XC-CLEAN signal, N-3 before P1-25 |
| R7B2-10 Twins asked twice, unnamed | MINOR | Accepted (re-derived) | P4 D-6 only if A1's vehicle ruling and A9's R8 leave it open. D-7 = P7 D7's cascor-model half. A5 names D-5 = P6 OD-14 and P7 D7's cascor half, and O13 = P6 OD-13. Mid-wave names D-3 = P3 D-02/D-03, and D-2 = P3 D-12/D-07 with P2 O14's data cut, asking the data release's version with them. Group B names D-08 and D-09 inside D-10's five parked rows |
| R7B2-11 Three green drafts waited for mid-wave | MINOR | Accepted (re-derived) | ml#2121, ml#2125 and canopy#698 join §3's table and A10, with #698 as "Fix (or close)" |
| R7B2-12 The recurrence route named only PyPI and images | MINOR | Accepted (with R7B1-12) | As R7B1-12 |
| R7B2-13 Cascor's `CHANGELOG.md` was not in §8 | MINOR | Accepted | §8's cascor row includes `CHANGELOG.md` `[Unreleased]`, which P3-08's F9 edits, with P3-08 first |
| R7B2-14 S0.5 and §7.1 item 4 disagreed | NIT | Accepted | Both: the validation round runs now; the fix-forward and its own round wait for A1 and A4 |
| R7B2-15 "The rest" included O-6 | NIT | Accepted | A2: "item 8, the rest. O-6 comes with P1-10's merge (H-2)" |
| R7B2-16 Strict order held item 8 behind Tier-2's runs | NIT | Accepted | Wave 0's sitting intro: items 4–8 go ahead while item 3's runs complete unattended |
| R7B2-17 The exit could not be met if A1 accepted only W1.14 | NIT | Accepted | The exit is conditional: R-DC-PATCH and the trio restart only if A1 accepts the data-client or cascor fix; host recurrence legs only if A1 chose vehicle (a) |
| R7B2-18 The `JuniperCascor1` row omitted the trio route | NIT | Accepted | §8's row adds F-S10's trio route (a wheel swap, or primary syncs) and recurrence host legs |
| R7B2-19 "→" and rows 17 and 25 | NIT | Accepted | Appendix A's "→" covers §6 and the release steps; row 17's P4-30..P4-32 sit at T3 with the row named; row 25 lists O1 (XC-GRANT), O10 (XC-CRED at A3) and O14 (mid-wave) |
| R7B2-20 Six references without a filename | NIT | Accepted | "`…INTEGRATED-DESIGN.md`'s §8 STOP"; §7.1 gives each line citation its document; "P12's plan" is `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`; Lane A1 is named as `EX/round6-laneA1-gate.md`, and the later classification as `EX/round7-laneA-reprobe.md`; P3-08's dependency is cited by row ("P3-08's row") rather than by an archived line number |

**Totals:** 49 findings (3 BLOCKER, 7 MAJOR, 24 MINOR, 15 NIT), all accepted, R7B1-05 in part. R7A-13 and R7A-14 correct round 6's reconciliation, and are recorded here rather than in place.

## Drift taken in

v1.7.0 takes in the drift that changes an action, and round 8 checks it.

- **From the 2026-10-05 22:33Z census**:
  - P12's Phase 1 wave 1 merged pending the owner's rulings (the first table above). data-client#222 is a breaking contract change on `main`, so R-DC-PATCH now needs a branch off `v0.5.0`, and a trio sync to `main` would bring W1.4 too (XC-P12, §5, Wave 1).
  - The W5.1 review is done (ml#2168), so R5 can be ruled (Group B).
  - The canopy ledger's Phase 10 is filed (ml#2157): P2-01 and P2-02 are done, and its FIXED records reopen if P3-06 refutes canopy#685.
  - Five fleet drafts were added to A10: ml#2147, #2149, #2150 and canopy #704 (in `…p1-wave1-in-flight.md`), and canopy#698.
  - The fleet grew to 104.
- **From the 2026-10-08 10:13Z re-probe**:
  - No release was cut and PyPI is unchanged. juniper-data, juniper-data-client and juniper-canopy took dependency and CI bumps.
  - The fleet grew to 115.
  - ml#2179, the backup arc's Phase B handoff and record, merged at 2026-10-05T22:47:04Z. In the plan:
    - R3B DEFECT-1 becomes an owner ruling at the first sitting (A2, with S0.3 drafting its menu) and a new hazard, H-23: the first backup after recovery would delete 6 to 8 of job 2's 9 filesets.
    - P1-05..P1-08 become round 3's fold-in and round 4. P1-09's archive half is done for rounds 2–3, while row k stays open.
    - XC-PRESERVE row a moves to `sorted-stargazing-garden` and its bundle, and row b's originals are archived.
    - The watchdog's primary is already synced.
  - Five backup fleet drafts were added to A10: ml#2137 and #2181 are green docs, and ml#2138, #2140 and #2159 are red tests.

## Unresolved dissent

None. The lanes overlapped on five themes and agreed on each:

- the part-boundary overlap (R7A-02, R7B1-09);
- unlisted shapes (R7A-04, R7B1-05);
- the restart's coupling (R7A-09, R7B2-03);
- recurrence's editable install (R7B1-12, R7B2-12);
- the first-sitting gaps (R7B2-01, R7B2-02, R7B2-11).

## Slips on the lanes' constraints

None reached a repository or printed a value. The owner may want to know:

- Lane A loaded the gate in-process, so Python wrote `util/ad-hoc/__pycache__/2026-10-04_gitleaks_zero_rule_probe.cpython-314.pyc`. It is gitignored and was left in place.
- Lane B1:
  - read the first 4 bytes of every file of 2 MB or less in six checkouts, which may have included `.env` files, and printed only a count;
  - ran a recursive `grep -c` over juniper-deploy, which matched nothing;
  - listed `.env.example` and `.env.secrets.example` by name;
  - re-read its own masked tool output under `~/.claude/projects/`.

## What this reconciliation cannot support

- That round 7's corrections, gate v5 or the drift taken in introduced no new error. Round 8 is briefed on exactly that.
- That the gate catches every way a secret can be written. Its docstring lists some of what it does not cover.
- That the 43 real-file findings hold no credential. Shape is not content. `round7-laneA-reprobe.md` classified the 35 kept from v4, and this reconciliation the 8 new ones.
- That ml#2179's record meets XC-PRESERVE's "done" test for row b, or that `cached-swinging-summit`'s state was all carried into `c3d0e890`.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after 10:30Z on 2026-10-08.
