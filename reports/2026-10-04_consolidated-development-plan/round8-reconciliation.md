# Round 8 — reconciliation of three lanes into plan v1.8.0

- **Artifacts**:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, v1.7.0 (sha256 prefix `c27d41d9259510f0`) → v1.8.0 (`954cbb0b189de496`).
  - The gate `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`, v5 (sha256 prefix `5a6d1bd81ce6cbec`), rewritten a sixth time as v6 (`a21289f304370d88`).
  - `util/ad-hoc/2026-10-05_gate_regression.py`, from 123 cases (`dad7dc3339bf818e`) to 163 (`ae25c2d754646d73`).
  - `util/ad-hoc/2026-10-04_plan_id_coverage.py`, corrected to count R-IDs with one digit (`P2-R8`), now `94f375d1e1a5670b`.
  - `util/ad-hoc/2026-10-05_masked_finding_shape.py`, from `83393986a6bc3192` to `79dccc0c80d563e3`: a `--names` mode for the plan's new line read (below).
  - All three lanes read the same plan and gate hashes at the start, middle and end of their windows.
- **Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §4–§5. Round 8 was briefed on round 7's corrections and the drift that v1.7.0 took in (`round7-reconciliation.md`, "Drift taken in").
- **Lane reports** (all in this directory):
  - `round8-laneA-reprobe.md`: 1 BLOCKER, 2 MAJOR, 3 MINOR, 8 NIT;
  - `round8-laneB1-safety.md`: 4 BLOCKER, 4 MAJOR, 11 MINOR, 3 NIT;
  - `round8-laneB2-schedule.md`: 0 BLOCKER, 5 MAJOR, 13 MINOR, 7 NIT.
- **Window**:
  - The lanes ran on 2026-10-08 from 10:32Z: Lane A until 11:05Z, Lane B2 until 11:14Z, Lane B1 until 11:34Z.
  - The reconciliation ran from 11:34Z until 12:20Z, when v1.8.0 was frozen.
- **Method**: read-only, except the plan, the gate, the regression, the coverage tool and the shape tool.
  - GitHub REST reads were GETs only, by `gh api`. Git read with `show origin/main:<path>`, `cat-file` and `rev-parse`.
  - Gate runs used synthetic inputs and scratch copies in the session scratchpad. Real-file findings were read only as masked shapes (`util/ad-hoc/2026-10-05_masked_finding_shape.py`).
  - No secret was read or printed.
- **ID coverage**: v1.0 → v1.8 and v1.7 → v1.8 drop no ID (381 in v1.7 and in v1.8), and all 375 extraction IDs remain placed (`util/ad-hoc/2026-10-04_plan_id_coverage.py`, exit 0).
- **Lint and structure**: the plan passes markdownlint-cli v0.42.0 with `.markdownlint.yaml` and `util/ad-hoc/2026-09-05_markdown_structure_check.py` (0 problems). No line is over 512 characters. Markdownlint caught one table row (A9) that an edit had left with an extra cell; the structure check had passed it.

<!-- markdownlint-disable MD013 -->

## Re-derived by the reconciler

| Claim | Finding | Re-derivation | Result |
| --- | --- | --- | --- |
| The lines the gate flags in the published Phase B record hold no credential | R8A-02 | A scratch copy of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` whose blob id equals `origin/main`'s (`80a95acd…`); gate v5, then v6; masked shapes | v5 flags five lines (L447, L492, L801, L802, L2149) and v6 two more, from its env rules (L811, L895). None is random-looking. L801 and L802 hold the same 16-letter alphabetical run; L447 a `not-a-…` placeholder; L492 a 10-letter word; L2149 a SQL list of option names; L811 a regex alternation in a code span; L895 prose naming code forms (`os.environ(`). **Confirmed**. S0.3 still gates the record once the plan merges |
| P2's handoff and its census directory | R8A-03, R8B2-01, R8B2-06 | `git cat-file -e origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-05_canopy-phase10-five-rounds-pr-open-census-ran-live-phase11-owed.md`; `ls` (names only) of `Juniper/backups/2026-10-05_f058_census_v2_final/` | The handoff is on `main` (ml#2157). The directory holds the six `2026-10-04_f058_census_v2_*.py` scripts, `run/` and `__pycache__/`, outside every repository. **Confirmed** |
| F-CANOPY-065 waits on a severity rule | R8B2-07 | `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` L357–360 | §6.3 triages P1 as "breaks a documented behaviour" and P2 as "cosmetic or drift": the rule the ledger cites as "plan §6.3". **Confirmed** |
| The fleet's size and the drafts' merge states | R8A-06, R8A-11 | The 10:13Z census (`util/ad-hoc/2026-10-05_ecosystem_live_census.py`); `gh api repos/pcalnon/juniper-ml/pulls/<n>`, `mergeable_state`, at 11:59Z | 115 open Cursor drafts: ml 47, canopy 23, data 23, cascor 9, data-client 7, and cascor-client, worker and deploy 2 each. ml#2121, #2122, #2125 and #2137 are `dirty` (in conflict) and ml#2181 is `behind`; all five are open drafts. **Confirmed** |
| The memory index's size, and the write Lane B2 saw | R8B2-02 | `wc -m` and `wc -c` of `MEMORY.md`, its mtime, and this session's own edits | 18,416 characters after the reconciler's one-count edit at 10:36Z, which is the 18,560-byte write Lane B2 measured; 18,521 characters (18,667 bytes) after another session's write at 11:21Z. Both are under the ceiling and the 20 KB target. **Confirmed**; XC-MEM and H-11 record both |
| Row k's purge rule, and what Phase C step 7 does | R8B2-13 | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` L213, L254 | L213: no transcript is purged before every round's report is archived on `main`. L254: step 7 counts transcripts and purges nothing. So row k gates no Wave 0 step and is not P1-10's. **Confirmed** |
| A restore can start job 2 | R8B1-08 | `git show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`, L136–147 and L206–213 | DEFECT-2: set `paused-until` with `sqlite3` while no server runs, read `startup-delay` back, and check that the first start reads Paused. DEFECT-3: Procedure B's rebuild tool starts an overdue job; "Pause first". The handoff's interim rule (L206–213) says only that no backup may complete. **Confirmed**; H-23 now applies both fixes before job 2's first start |
| Sentry's logs channel outlives R-OBS-SC | R8B1-07 | `grep -n enable_logs juniper-observability/juniper_observability/sentry.py` | L135: `enable_logs=True`. **Confirmed** |
| A maintenance-branch PR gets no CI by itself | R8B2-04 | `gh api` raw reads of juniper-data-client's `ci.yml` and juniper-recurrence's `ci-recurrence-app.yml` | data-client: `pull_request` to `main` and `develop`; recurrence: `pull_request` to `main`. Both also take `workflow_dispatch`, so the CI-by-hand route in Wave 1 is open to both. **Confirmed** |

## The rewritten gate, tested (v6)

Gitleaks v8.30.1, on v6. Rows 1 and 4–6 ran on earlier v6 builds (`e4885f068c8bbdfb`, and before it the scratch draft). The final v6 (`a21289f304370d88`) differs from them only in docstring wording and in one allowlist alternative written `pass(?:word|phrase)` instead of as two words, which matches the same strings; rows 2 and 3 ran on it. All inputs are synthetic except rows 3–6.

| # | Case | Expected | Observed |
| --- | --- | --- | --- |
| 1 | Probe mode, `--config .gitleaks.toml` | Canary 29/29; the repo config zero-rule; exit 1 | Canary 29 of 29. Default rules alone 3 of 29 (2 or 3 by the canary's random draw, as round 7 measured); B9-class rules alone 28 of 29; `.gitleaks.toml` 0 of 29, ZERO-RULE; exit 1 |
| 2 | `util/ad-hoc/2026-10-05_gate_regression.py`, 163 cases | Each as its case states | **163 of 163 as expected**, exit 0: on `e4885f068c8bbdfb` (finished 2026-10-08T12:05Z), and again on the final v6 (finished 12:19Z). Groups below |
| 2a | 127 formats that must be found (exit 2). Round 8 added: five swallow layouts (a prefixed name, plain then prefixed, a dunder prefix, an `export` path, no blank); three annotated unions; three argv lists; two JSON-list `*_API_KEYS`; six escaped refusal texts; five escaped-JSON forms; five env layouts; three swallow separators (`;`, `,`, `&`); a `Your-` diceware value; a `Key-file` label and a `--key-file-` flag; two lone-CR layouts | 2 | 2 in all 127 |
| 2b | 8 that must pass (exit 0): round 7's five, plus a `your-…-here` placeholder, an env-style `_FILE` path, and a path key after another assignment's separator | 0 | 0 in all 8 |
| 2c | 26 that must refuse (exit 3), unchanged | 3 | 3 in all 26 |
| 2d | Accept keys: two findings on one line | Two keys; one accepted → 2; both → 0; after an edit → 3 | As expected |
| 2e | Concurrency: a secret run and a same-size clean run sharing one `--workdir`, 5 trials | The secret run never 0; the clean run never 2 | As expected in all 5 |
| 3 | This plan's PR files, as scratch copies | 0 | Exit 0 on all 52 files, with one key accepted. The first run flagged six lines. Five were in this session's own text and were restructured, not accepted: the plan's and the gate's lists of env-style names, each written as a code-spanned name, a colon and a word; the gate's own allowlist regex; the shape tool's `TOKEN_RE =` line; and a placeholder example in this file. v6's label forms read any word after a code-spanned env name and a colon as a value, so prose can trip them. The sixth, `round8-laneB1-safety.md` L29, is a `Field(default="<random>")` example in a verbatim report: read, and accepted as `…round8-laneB1-safety.md:29:506:juniper-b9-assignment:9855b4c3b6`. Re-run on the final set, with the commit message and PR body, before the push |
| 4 | The 40 real files of round 6's false-positive sample | Workable | 49 findings in 13 files: 32 assignment, 4 pipe-cell, 5 quoted-pair, 8 swallowed. None from the default rules or the env rules |
| 4a | Against v5's 43 | Each change explained | All 43 of v5's keys are byte-identical in v6, and none is gone, so v6 narrows nothing on this sample. Six keys are new, below |
| 4b | The six new findings, by masked shape | None random-looking | **None random-looking.** Each is a `juniper-b9-swallowed` match one or two columns before an assignment finding on the same line: four shell quote-strips of the passphrase variable (`${…%…}` expansions, two lines in each of two scripts), and two placeholders after a prefixed `…=SETTINGS_ENCRYPTION_KEY=`, one of them a hyphenated `a-…-key-value-not-…` |
| 5 | `…PHASE-B-CONSENSUS-RECORD.md`, as merged | Workable | 7 findings (v5: 5), none random-looking (the first re-derivation above) |
| 6 | The gate's own interim config (`b9.toml`), scanned as text | Trips the gate (R8B1-19) | 44 findings: 43 `juniper-b9-pipe-cell` and 1 `juniper-header-refusal` (v5: 28). XC-LEAKS note 3 says how a shipped config avoids this |

**This PR's own line read.** v1.8.0 requires a masked read of every added line that names a credential, whatever the gate says, and this PR is the first under that rule. `util/ad-hoc/2026-10-05_masked_finding_shape.py --names`, with 25 characters before and 45 after each name, listed 166 such lines in the 52 PR files, and 165 once the lines below were restructured; all were read, both times. None holds a credential-shaped value: every value beside a name is a placeholder (`<random>`, `<value>`, `<key>`, `…`), a code expression, a regex or a path. Two windows held one random-looking token each, and both are a `notes/JUNIPER_2026-09-21_…` filename. The read is repeated on the final set, with the commit message and PR body, before the push.

**Escaped JSON, finished during this reconciliation.** v6's first full run passed 161 cases. R8B1-05 named five escaped-JSON files and v6 had cases for three, so two more (`escaped-json-dict`, `escaped-json-embedded`) were added and pass. No rule changed for them.

## Dispositions

| Finding | Sev | Disposition | Applied in v1.8.0 (plan) or v6 (gate) |
| --- | --- | --- | --- |
| R8A-01 A prefixed or no-blank second name still swallowed the secret on one line | BLOCKER | Accepted (fixed and tested) | Gate v6: the swallowed rule takes any prefix and zero or more blanks after the separator, and a `#`-led value. The path allowlist skips a leading `:` or `=`, so `X=PASSPHRASE_FILE=/path` stays clean. Cases `swallow-prefixed`, `-plain-then-prefixed`, `-dunder`, `-export-path`, `-no-blank` (exit 2) and `path-after-separator` (exit 0); the canary's `same-line.sh` class is now the prefixed layout. Plan: XC-PRESERVE. R7A-01's disposition, "fixed and tested", held for an unprefixed name only; recorded here, not in place |
| R8A-02 ml#2179 published the Phase B record without the gate §9 makes Hard | MAJOR | Accepted (re-derived) | S0.3: once this plan's PR merges, gate the record as merged, read the five lines, record accept keys or send a real value to XC-CRED. P1-09, row b, §9's P1-09 row and Appendix A say the record is published and not yet gated. The reconciler's masked read of the five (above) finds none credential-shaped |
| R8A-03 v1.7.0 took in ml#2157 but not the P2 handoff it carried | MAJOR | Accepted (re-derived; with R8B2-01, -06, -07) | `…phase11-owed.md` in the Documents table and Inputs; §2's P2 row; Wave 2's P2 lane and its Phase 11 note; §7.1 item 18; XC-PRESERVE row r; Group B's P2 adds the F-CANOPY-065 question; §2 says "065 pending an owner ruling" |
| R8A-04 §8 omitted ml#2150 | MINOR | Accepted | §8's `util/isolated_stack.bash` row, XC-FLEET's note and A10: ml#2149 and ml#2150 |
| R8A-05 W1.1a shipped on an answer to data#409 | MINOR | Accepted (with R8B2-08) | XC-P12's wave-1 bullet and action 1, A9, Appendix B row 17 and §10's P12 list: R1's default half was applied pending and is ratified or reverted at A9; W1.1b stays optional |
| R8A-06 Four "green" drafts are in conflict | MINOR | Accepted | XC-FLEET's rows: "in conflict on 2026-10-08" for ml#2121, #2122, #2125 and #2137; ml#2181 is only behind; the note and A10 say the sweeper could merge a green one once out of conflict |
| R8A-07 The file branch is L35 | NIT | Accepted | S0.11's cascor bullet |
| R8A-08 7 or 8 filesets from 2026-10-08 | NIT | Accepted | Overview 1, H-23 and §12's row |
| R8A-09 Three of the five drafts were opened before ml#2134 merged | NIT | Accepted | XC-FLEET's backup-test row |
| R8A-10 "(current)" handoffs were superseded | NIT | Accepted (with R8B2-20) | Scope's Inputs name `…round3-fold-in-pending.md`, `…phase11-owed.md` and `…p1-wave1-in-flight.md` as the successors |
| R8A-11 The fleet metric used 104 | NIT | Accepted | Success metrics: 115 on 2026-10-08 |
| R8A-12 data#451 departs from R3's literal wording | NIT | Accepted | XC-P12 and A9 ask the owner to ratify data#451's reading of R3 |
| R8A-13 The record also holds the fix-forward lanes | NIT | Accepted (with R8B2-21) | The Documents table: rounds 2–3, the ml#2115 fix-forward lanes, two briefs and the handoff validations, 16 sections |
| R8A-14 Row b's place and loss | NIT | Accepted (with R8B2-21) | Row b: round 4's reports in `sorted-stargazing-garden`, untracked, and in subagent transcripts until saved; lost by sweep or transcript expiry |
| R8B1-01 A PEP 604 union in an annotation passed both scans | BLOCKER | Accepted (fixed and tested) | Gate: the annotation form takes any type text of up to 81 characters before `=`, unions and nested brackets included. Cases `ann-union-field`, `ann-union-constant`, `ann-union-field-call`; canary class `annotated-union.py`. Plan: XC-PRESERVE's list of shapes ("unions included"), and the read of every added line that names a credential, whatever the gate says, which this finding proposed |
| R8B1-02 `aescrypt`'s argv as a list was missed | BLOCKER | Accepted (fixed and tested) | Gate: a new rule, `juniper-b9-aescrypt-list`, reads the list in a repr, a JSON array or `CalledProcessError` text, its quotes escaped or not. Cases `aescrypt-list-repr`, `-called-process-error`, `-json`; canary class `aescrypt-list.log`. Plan: "`aescrypt`'s argv, as a command line or a list" |
| R8B1-03 A JSON-list `*_API_KEYS` value was missed | BLOCKER | Accepted (fixed and tested) | Gate: the env rule's value takes a JSON list's first element. Cases `api-keys-json-list`, `-two`; canary class `api-keys-json.env`. Plan: Scan 2's names and layouts |
| R8B1-04 The refusal texts behind escapes were missed | BLOCKER | Accepted (fixed and tested) | Gate: `juniper-header-refusal` skips blanks, single or doubled backslash escapes (`\n`, `\t`, `\x..`, `\u....`) and HTML character references before the key. Six cases (`refusal-json-newline`, `-json-tab`, `-json-crlf`, `-repr-nbsp`, `-bytes-vt`, `-html`); canary class `header-refusal-json.json`. Plan: H-22 and XC-PRESERVE say "in their plain form and behind repr, JSON or HTML escapes", not every form |
| R8B1-05 Escaped JSON keys were missed | MAJOR | Accepted (fixed and tested) | Gate: `_KEY_TAIL`, `_Q` and the quoted-pair rule take a backslash before each quote. Five cases (`escaped-json-environ`, `-name-value`, `-argv`, `-dict`, `-embedded`), the last two added during this reconciliation. Plan: "a quoted (also JSON-escaped) or bare key" |
| R8B1-06 Env-style names in other layouts were missed | MAJOR | Accepted (fixed and tested) | Gate: the env rule takes a code span or Markdown wrappers around the name, a closing `"]` (an `environ` subscript) and blanks before `=` or `:`; a new rule, `juniper-env-pipe-cell`, reads table rows. Cases `env-environ-subscript`, `-table-row`, `-codespan-label`, `-bold-label`, `-spaced-swallow`. Plan: Scan 2's names and layouts |
| R8B1-07 S0.11's test missed the log channels | MAJOR | Accepted (re-derived) | S0.11: each test also drives every relay path with the fake key and fails if any log record carries it (`caplog`: `getMessage()`, `args`, `exc_text`), which covers Sentry's log records, its ERROR-line events and its breadcrumbs |
| R8B1-08 H-23 did not stop a restore from starting job 2 | MAJOR | Accepted (re-derived) | H-23: "Run no backup" is not enough; until the fold-in lands, apply DEFECT-2's and DEFECT-3's fixes as `…round3-fold-in-pending.md` gives them (L138–147) before job 2's first start, and check that it reads Paused |
| R8B1-09 The swallow across `;`, `,` or `&` | MINOR | Accepted (fixed and tested) | Gate: the swallowed rule starts after any of `:`, `=`, `;`, `,`, `&` or `\|`, with or without blanks. Cases `swallow-semicolon`, `-comma`, `-ampersand` |
| R8B1-10 Label and table variants | MINOR | Accepted (listed) | The gate's docstring, Known limits: "Label and table variants", all ten. The line read is their control |
| R8B1-11 Value leads | MINOR | Accepted (listed) | Known limits: "Value leads the bare-value classes refuse", all five |
| R8B1-12 Name/Value variants | MINOR | Accepted (listed) | Known limits: Name/Value settings outside JSON or a dict, a key between Name and Value, a TOML dotted suffix, and `=>` |
| R8B1-13 Two skips reached further than stated | MINOR | Accepted (fixed and tested) | Gate: `your-` is skipped only as a whole value ending `here`, `key`, `value`, `secret`, `token`, `password`, `passphrase`, `credential` or `name`; the path skip needs `_file`, `_path` or `_dir` (or with `-`) to close the key, before its separator or cell, or before a blank and a path. Cases `your-diceware`, `key-file-label-row`, `key-file-flag` (exit 2), and `your-placeholder`, `env-path`, `path-after-separator` (exit 0). A real value shaped `your-…-key` stays a listed limit. Plan: XC-PRESERVE's skip sentence |
| R8B1-14 A match over more than 9 line breaks at a part boundary | MINOR | Accepted (listed) | Known limits: "more than 9 line breaks across a part boundary (a PEM block, for example)" |
| R8B1-15 A lone CR inside an LF file | MINOR | Accepted (fixed and tested) | Gate: `_GAP` takes a lone CR as a line break, and the env rule's boundary admits it. Cases `lone-cr-env-swallow`, `lone-cr-name-value` |
| R8B1-16 `${NAME:-value}` under an env-style name | MINOR | Accepted (listed) | Known limits: "`$` or `#` under an env-style name (`${NAME:-value}` included)" |
| R8B1-17 The history-scan report is created 0664 | MINOR | Accepted | XC-LEAKS step 1 and note 1: create the report first with `install -m 600 /dev/null <path>`, or run under `umask 077`; `--redact` does not mask the commit message |
| R8B1-18 Other public text went unscanned | MINOR | Accepted | XC-PRESERVE method, §9's push row and §12: every public text, as files: the commit message, the PR title and body, and any comment, review reply or Release body |
| R8B1-19 A shipped config trips the gate | MINOR | Accepted (re-measured) | XC-LEAKS step 3 and note 3: ship all twelve interim rules, with no B9 name or refusal phrase whole (`PASS[P]HRASE`, `in header[ ]value:`). Under v6 the config as text gives 44 findings (row 6 above), not 28 |
| R8B1-20 One finding can print two keys | NIT | Accepted | The gate's docstring: a finding on a line that two parts share can print two keys, one column apart; accept both |
| R8B1-21 A workdir under a default path allowlist was blamed on binary text | NIT | Accepted (fixed) | Gate: the byte-mismatch error now says to check that the `--workdir` path matches none of the default global path allowlists |
| R8B1-22 `*_API_KEYS` was not listed | NIT | Accepted | XC-PRESERVE's Scan 2 line |
| R8B2-01 P2's Phase 11 was missing | MAJOR | Accepted (with R8A-03) | As R8A-03 |
| R8B2-02 XC-MEM's premise no longer holds | MAJOR | Accepted (re-derived) | XC-MEM restated: two 2026-10-05 compactions, made ahead of A6; S0.12 lists what they moved against the hook rule; A6 ratifies or reverts; H-11 reworded. The index's 10:36Z write that the lane saw was the reconciler's own one-count edit (`MEMORY.md`'s verification hub line, 26 → 27) |
| R8B2-03 W1.11's floor and pin PRs collide with P4-14 and R-ML-a | MAJOR | Accepted | P4-14 and R-ML-a's floor are W1.11's code half, opened once by the P4 session after PyPI and GHCR serve the release, never earlier as drafts: Wave 1's "After R-DATA", Wave 2's P12 lane, §8's extras and Compose rows, §9's W1.11 row and §10's P12 corrections |
| R8B2-04 Nothing guards a maintenance-branch PR | MAJOR | Accepted | Wave 1's F-S10 delivery: open the PR only after §7.1 item 3's round, label it `stacked-pr`, run CI by `workflow_dispatch` (or the suite locally) and read it before the cut; §5's vehicle and R-DC-PATCH rows and §9's 0.5.1 row point there |
| R8B2-05 The forward-port to `main` was required nowhere | MAJOR | Accepted | The P12 chain's "Ready when", Wave 2's P12 lane, a new §9 row (Hard), §5's branch note, and the Wave 1 exit when A1 accepts the data-client fix |
| R8B2-06 The census directory is a single copy | MINOR | Accepted | XC-PRESERVE row r; Overview 4 and the metric count 17 |
| R8B2-07 F-CANOPY-065's owner question had no slot | MINOR | Accepted | Group B's P2 entry, naming the severity rule in §6.3 of `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md` (re-derived: the ledger's "plan §6.3" cites that file, L357–360); §2's P2 row |
| R8B2-08 R1 was applied pending | MINOR | Accepted (with R8A-05) | As R8A-05 |
| R8B2-09 O7's remainder had no prep | MINOR | Accepted | S0.9 derives it; the session-item intro names it |
| R8B2-10 The 0.6.0 option for R-DC-PATCH led nowhere | MINOR | Accepted | Dropped from §5's "Ready when"; the branch note says why it is not offered |
| R8B2-11 Past W1.14 on `main` is also past wave 1 | MINOR | Accepted | Wave 1's recurrence route: under vehicle (a), sync the primary to the 0.5.1 tag's branch; move it to `main` only once everything that imports it takes wave 1. The exit says "a primary that holds it" |
| R8B2-12 P1-08's size was under the top cell | MINOR | Accepted | Tier-1 item 2 and Appendix A: top cell; §10's P1 corrections note the handoff's "at least two lanes" |
| R8B2-13 Row k does not gate P1-10 | MINOR | Accepted (re-derived) | Row k gets its own archive PR, before any transcript purge (`…RECOVERY-PLAN.md` L213; Phase C step 7 counts only, L254). P1-10's prerequisites and §9's row drop P1-09; its round-4 part rides P1-10 |
| R8B2-14 P1-09's archive half skipped the gate | MINOR | Accepted (with R8A-02) | As R8A-02 |
| R8B2-15 P1-12 had no validating round | MINOR | Accepted | P1-12 joins the fold-in (item 1) if Phase C step 5's count is non-zero, so P1-08 validates it; item 5, §9's P1-18 row, Wave 2's P1 lane and Appendix A likewise |
| R8B2-16 P2-02's M-REPLAY reconciliation was not done | MINOR | Accepted | Wave 1's P2 ledger, Wave 2's P2 lane and Appendix A carry it; §10 drops F-057's and i13's corrections, which ml#2157 discharged |
| R8B2-17 P12-11 had no lane | MINOR | Accepted | Wave 2's P12 lane: W1.1b (P12-11, optional, after R1) |
| R8B2-18 W5.8's and W5.10's release was asked too late | MINOR | Accepted | Asked with A9; Group B's P12 entry says why |
| R8B2-19 Changed lines without filenames | NIT | Accepted | R3B DEFECT-1, AC-4, §8 P0 step 10, Procedure B, the STOP, the ledger and Phase 10 now carry their documents |
| R8B2-20 Stale lines | NIT | Accepted | The Inputs, §2's P1 row (now dated to `…round3-fold-in-pending.md`, not a probe), §10's FIXED-BY line, F-057's and i13's lines dropped; W5.10 and W5.11 at T5 and in Scope |
| R8B2-21 Rows a and b, and the record's contents | NIT | Accepted (with R8A-13, R8A-14) | Row a names every uncommitted path, `util/ad-hoc/2026-10-04_ml2115_fix_forward/` among them; row b and the Documents table as R8A-13 and R8A-14 |
| R8B2-22 S0.7 must check four PRs | NIT | Accepted | XC-FLEET's note names them |
| R8B2-23 P1-05..P1-08 were re-scoped silently | NIT | Accepted | Tier-1 item 1 and Appendix A say they are re-scoped; item 2 says round 4 is not narrow |
| R8B2-24 The exit's conditions | NIT | Accepted | The exit splits the data-client and cascor conditions |
| R8B2-25 "As one round", "as three rounds" | NIT | Accepted | §7.1 items 3 and 6: "one item (at least two rounds)", "three items (at least six rounds)" |

**Totals:** 61 findings (5 BLOCKER, 11 MAJOR, 27 MINOR, 18 NIT), all accepted. Five of Lane B1's MINORs (R8B1-10, -11, -12, -14 and -16) were accepted as listed limits of the gate, not rule changes, because the plan's line read is their control. R8A-01 corrects round 7's R7A-01 disposition ("fixed and tested" held for an unprefixed name only), and R8A-13 corrects `round7-reconciliation.md` L37, which listed the record's contents without the ml#2115 fix-forward lanes F1 and F2. Both are recorded here rather than in place.

## Drift taken in

v1.8.0 takes in the following, and round 9 checks it.

- **On `main` before the 10:13Z re-probe, missed by v1.7.0** (round 8 found both):
  - P2's handoff of 2026-10-05 (`…phase11-owed.md`, ml#2157): Phase 11, which records P2-05's live census, its census directory (XC-PRESERVE row r), and F-CANOPY-065's pending ruling;
  - the two compactions of `MEMORY.md` on 2026-10-05, by the P2 and P12 sessions (XC-MEM).
- **After the round**: another session wrote `MEMORY.md` at 11:21Z (18,521 characters). XC-MEM and H-11 carry the new size.
- **Re-read at 11:59Z**: the five backup drafts' merge states, unchanged from the lanes' readings.
- **The 12:05Z re-probe** (`util/ad-hoc/2026-10-05_ecosystem_live_census.py --since 2026-10-08T10:00:00Z`): no release was cut and PyPI is unchanged.
  - ml#2129 was closed unmerged at 11:52Z, as §3's table recommended, so A10 and S0.3 drop it.
  - canopy#721 merged at 11:54Z. It ships the `outbound_errors` module that canopy#685 added but left out of the wheel, so S0.5's round on #685 covers it.
  - The fleet was being consolidated outside this plan: consolidation PRs ml#2182, data#475, data-client#230, cascor#709 and canopy#729 were open, and fleet PRs had been merged, closed or marked ready in all eight repositories that had them. Every other A10 row was still open. XC-FLEET's note says S0.7 starts from a fresh census.
  - The other merges since 10:00Z are test, docs and CI pins (data#471, data-client#224 and #229, cascor-client#176 and #177, worker#206, deploy#241) that change no action.

## Unresolved dissent

None. The lanes overlapped on six themes and agreed on each:

- the same-line swallow's variants (R8A-01, R8B1-09);
- P1-09's archive half, published before the gate (R8A-02, R8B2-14);
- P2's Phase 11 (R8A-03, R8B2-01);
- R1's default half, applied pending (R8A-05, R8B2-08);
- superseded inputs (R8A-10, R8B2-20);
- the record's contents and row b (R8A-13, R8A-14, R8B2-21).

## Slips on the lanes' constraints

None reached a repository or printed a real value. The owner may want to know:

- **Lane A**:
  - the harness saved one long `git ls-tree` output under `~/.claude/projects/…/tool-results/`; the lane did not read it;
  - it printed exit codes with `$?`, which the session's command guard admitted;
  - it read outside its worktree: the sha256 and character counts of `pr2114.md` and `pr2115.md` in `cached-swinging-summit`, and name listings of `sorted-stargazing-garden`'s round-3 directory and of the census directory. It printed no content of them.
- **Lane B1**:
  - it wrote 11 test inputs, and one edit to an input, with inline `python3 -B -c` rather than the file tool; the guard refused one such command;
  - its value generator printed the lane's invented values to the session's tool output, and three checks printed short prefixes of them. None is in its report;
  - it read four saved copies of public gitleaks sources outside its own scratch directory;
  - it downloaded a second scanner tarball, for its workdir test;
  - one masked `grep` printed fragments of four table cells, names and prose, from `…RECOVERY-PLAN.md` L110 and `…INTEGRATED-DESIGN.md` L210, L471 and L2505.
- **Lane B2**:
  - the harness saved one long `grep` output under `~/.claude/projects/…/tool-results/`; the lane did not read it;
  - it `stat`ed `MEMORY.md` for size and mtime, not content;
  - the guard refused one inline Python check, which the lane then did by reading.
- **The reconciler**: during the lanes' window, at 10:35Z–10:36Z, it created one auto-memory file (`reference_a_vanished_finding_is_a_narrowing_until_explained.md`), added one line to another (`reference_verification_discipline_hub.md`), and changed one count in `MEMORY.md` (26 → 27). None is a frozen artifact, but XC-MEM describes the index, and Lane B2 measured it after that write and took it for another session's (R8B2-02).

## What this reconciliation cannot support

- That round 8's corrections, gate v6 or the drift taken in introduced no new error. Round 9 is briefed on exactly that.
- That the gate catches every way a secret can be written. Its docstring lists some of what it does not cover, and the plan now requires a line read, whatever the gate says.
- That the 49 real-file findings, or the record's seven, hold no credential. Shape is not content.
- That the two 2026-10-05 compactions of `MEMORY.md` kept every hazard hook. S0.12 checks that.
- Host state, the running services, any repository's history, and Sentry's server-side scrubbing.
- Any state after 12:20Z on 2026-10-08.
