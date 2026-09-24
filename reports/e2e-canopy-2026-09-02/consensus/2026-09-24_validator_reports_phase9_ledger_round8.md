<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 8: Lanes R8-A and R8-B, verbatim

Round 8 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 3297131f, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R8-A re-derived round 7's claims from their artifacts; Lane R8-B attacked round 7's corrections (129f4880..3297131f). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Both reports quote the bare prefix of an age key, and R8-B's quotes a PEM header in a JSON example, while discussing the archiver's gate; each literal was reviewed and allowed for its own lane's report only (--allow-shape), and neither report holds key material. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR8A_phase9_ledger_brief.md and laneR8B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round8_corrections.py.

## Lane R8-A -- measurement re-creation, artifact-first

*agent `ae24ee966b7499c5e` · round 1 · last-assistant-text (not resumed) · 8241 chars*

**VERDICT: SOUND-WITH-FIXES.** Every number, count and time re-derives from its artifact. Two statements round 7 added are false, both LOW. Finding 1 is wording only. Finding 2 changes an action (a tool fix) if the tool is fixed, which I recommend; narrowing the wording instead changes no number, disposition or action. Ledger = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `3297131f`. Scratch = `…/scratchpad/r8a.hyHUvR`.

**TABLE**

| Claim | Re-derived value | Verdict | Evidence |
|---|---|---|---|
| 1a. Replaying round 7's script on `129f4880` gives `3297131f`'s ledger | "applied 7 substitutions"; files identical; sha256 `80efa649…` for the replay, for `git show 3297131f:` and for the worktree file | MATCH | `2026-09-24_phase9_ledger_round7_corrections.py` run in scratch on `129f4880`'s ledger, then `cmp` |
| 1b. cascor#678 was never a draft and has one arm, 13:32:10Z on 09-23 | 16 timeline items, none a ready or draft event. Opened 02:02:52Z, not a draft. One `AutoSquashEnabled` at 2026-09-23T13:32:10Z (pcalnon); merged 20:22:13Z. The question (bc31e993 line 4227, 03:34:45Z) says "cascor#678 was armed the same way earlier", as the ledger now quotes it. The time was already in the ledger at :8772 (end of the 13:17:53–13:32:10Z sweep) | MATCH | GraphQL `timelineItems` (logins, types, times); `2026-09-24_owner_answer_extract.py` (0 secret and 0 e-mail redactions) |
| 1c. Round 6's record names the two round-5 numbers that did not hold | In `…_ledger_round6.md`: R6-A finding 1 is the question's time; R6-B finding 2 is the time plus four drafts → three. The record (:9430-9431) names both | MATCH | round-6 report lines 47-51 and 91-99 |
| 1d. Round 7's record | Both lanes returned SOUND-WITH-FIXES (`…_ledger_round7.md` lines 11 and 54). Round 6's replay: "applied 14 substitutions", identical to `129f4880`. Ready → arm gaps: data#428 4 s, ml#2032 7 s, ml#2059 4 s, #676 8 s, data#431 4 s, data#434 5 s. canopy#678 is a merge only (22:29:21Z); ml#2066 was armed at 22:27:08Z and never a draft; data-client#212 is a merge only. Round 6's report regenerates identical with the allow scoped to `a40a56695bf031320` (rc 0); scoped to R6-A it is refused, and in the unscoped form it is refused. Round 7's report regenerates identical with the allow scoped to R7-B and is refused with none. "No number or disposition" holds | MATCH, except the `sk-` floor history (Finding 1) and "refuses key material" (Finding 2) | GraphQL over 10 PRs; `2026-09-23_archive_consensus_reports_by_round.py --out` in scratch, with each lane's resume record (records 32 and 44) as the marker |
| 2. All four tools catch a bare `sk-` key of 20–31 characters | Lengths 19–33 tested in 7 contexts: 19 is not caught; 20–33 are caught by all four tools in every context | MATCH | `sk_len_probe.py` (booleans only) |
| 3a. An allow is `AGENT_ID=LITERAL` and covers only that agent's report | Own agent passes; another agent's allow, or the unscoped form, refuses | MATCH | `gate_probe.py` and the regeneration above |
| 3b. Key material after an allowed prefix is refused | Refused: a PEM header followed by LF, CRLF, a blank line or indentation, then base64; a whole age key, bare or in backticks. **Passed:** a whole fake PEM block (header, body and footer) when its newlines are escaped (`\n`), when it is in a blockquote, or when a backtick follows the header; also a legacy encrypted RSA PEM (`Proc-Type` lines) | MATCH for the stated forms, MISMATCH as stated generally | `gate_probe.py` → Finding 2 |
| 3c. Any other match still refuses | A different (RSA) header, a `ghp_` token beside an allowed header, and no allow at all are each refused | MATCH | `gate_probe.py` |
| 4a. The shape check passes | "0 failed", exit 0 | MATCH | `python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py` |
| 4b. The check fails 14 times on `129f4880`'s tools | "14 failed", exit 1. That is 3 (the 24-character key in the extractor, scan and tmpfs tool) + 6 (the archiver's sk-ant, sk-proj, 24-character key, hf_, xoxb, pypi) + 5 (the archiver has no `unreviewed_shapes`, so every gate case fails) | MATCH | The four tools from `git show 129f4880:` next to the `3297131f` check |
| 5a. Both scan windows regenerate byte-identical | `cmp` identical on both (705 and 507 rows) | MATCH | `2026-09-24_merge_command_launch_scan.py`, both windows, output in scratch |
| 5b. The tmpfs dry run re-checks 36 files, 0 failing | "would copy 0, already present 36 (re-checked; 0 failed a check)", exit 0 | MATCH | `--dry-run` |
| 5c. Every shape in consensus/ and drafts/ is a reviewed quote | 49 files. `…_ledger_round6.md` has 1 hit, the OPENSSH header; `…_ledger_round7.md` has 3 hits, each the bare `AGE-SECRET-KEY-`; 0 key material; 0 elsewhere. Extra: all 332 files under `reports/e2e-canopy-2026-09-02/` and the 26 verbatim-archived lane scripts have no other hit and no `sk-` key of 20–31 characters | MATCH | `shape_census.py`, `evidence_sweep.py` (file names and booleans only) |
| 6. Counts | 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open (1 P0, 6 P1, 12 P2) | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py` |

**FINDINGS**

1. **LOW: false history.**
   - **Quoted:** ledger :9461-9462, "the bare `sk-` floor round 6 had raised to 32 characters is back at 20 in all four shape-bearing tools". The same framing is in `2026-09-24_secret_shape_check.py:42` and `util/ad-hoc/README.md:748-749`.
   - **Evidence:** `git show <commit>:<tool>` across `51993b37`..`3297131f`. Round 6 raised only the extractor's floor (`{20,}` at `b0b17cad` → `{32,}` at `129f4880`). The launch scan and the tmpfs round-2 tool were at `{32,}` from their first commit (`3f83b9c6`). The report archiver was at `{32,}` from `51993b37`. Those three were never at 20 before round 7. No harm follows: the re-screen in 5c is clean.
   - **Fix:** "the bare `sk-` floor is now 20 in all four (round 6 had raised the extractor's from 20 to 32; the other three had been at 32 since they were written)".
   - **Changes a number/disposition/action?** No.

2. **LOW: "refuses key material after an allowed prefix" is over-claimed.**
   - **Quoted:** ledger :9255-9256 and :9462-9463; `2026-09-23_archive_consensus_reports_by_round.py:46-47`, "Key material after such a prefix is refused whatever --allow-shape says", and the same claim at :54-55 and :104-105; README :749-750, "key material always refused".
   - **Evidence:** `KEY_MATERIAL_RE` only accepts whitespace between the header and the body. With the header allowed for the agent, a whole fake key block passes the gate in the four forms in row 3b.
   - **Why it matters:** a real key in one of those forms would be archived verbatim. `reports/` is outside pre-commit's scope, so nothing stops it before the push.
   - **Fix:** add `-----END [A-Z ]*PRIVATE KEY-----` to `KEY_MATERIAL_RE`, allow `(?:\s|\\[rn]|[>\x60])*` between header and body, and add an escaped-newline case to the check's GATE list. I tested this: it refuses all four forms, still passes the bare quoted header, and has 0 hits over the 332 archived files. The alternative is to narrow the text to "a PEM header followed by whitespace and base64".
   - **Changes a number/disposition/action?** Yes, an action, if the tool is fixed; no if only the wording is narrowed.

**WHAT YOU COULD NOT CHECK**
- The follow-up's rebase (`range-diff`, 13 passed). The worktree guard refuses git outside this worktree, and the branch is not on GitHub. I checked only that `…_ledger_round7.md` reports it.
- The signing key of the 03:00Z commits (that needs signature fields).
- Anything outside Claude Code transcripts.

**SECRETS/PII:** None printed or sent. No slips.
- **GraphQL:** selected logins, event types and times only, with no REST commit object and no e-mail field.
- **Git:** no commit headers or signature fields; formats were `%h %ad %s` only.
- **Transcripts:** read through the redacting extractor, or by index, timestamp and length only.
- **Fakes:** built by concatenation, reported as booleans only, and kept in scratch.
- **Forbidden scripts:** neither was run. The tmpfs tool ran only with `--dry-run`; the report archiver wrote only to scratch.
- **Repo:** no file changed, and the worktree is clean at `3297131f`.

---

## Lane R8-B -- adversarial, on round 7's corrections

*agent `ad53f5c6414e62707` · round 1 · last-assistant-text (not resumed) · 8283 chars*

**VERDICT: SOUND-WITH-FIXES.** The ledger wording holds, the replay is exact, and the scoped allow fails closed. Finding 1 changes an action (a tool fix), so §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (:117-119) calls for another round.

**FINDINGS**

1. **MINOR: "key material always refused" is false. The allow still passes key material in common shapes.**
   - **Quoted:**
     - `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py:46-48`: "Key material after such a prefix is refused whatever --allow-shape says." The pattern is `-----\s*[A-Za-z0-9+/=]{20,}|AGE-SECRET-KEY-1[0-9A-Z]{10,}`.
     - The same file at `:55`: "(a PEM header followed by base64, a whole age key) is always returned."
     - `util/ad-hoc/README.md:749-750`: "with key material always refused".
     - `…E2E-VALIDATION-EVIDENCE.md:9255-9256` and `:9462-9463`: "refuse(s/d) key material after an allowed prefix".
   - **Evidence (probe, booleans only):** I called `unreviewed_shapes(text,"aX",["aX=<header>"])` on fake values built in scratch.
     - Refused: header, newline, then base64; and a classic age identity.
     - Passed:
       - a JSON-escaped `\n` body (the `"private_key": "-----BEGIN PRIVATE KEY-----\n…"` service-account form, and the OPENSSH form);
       - a markdown blockquote;
       - `cat -n` and Read-tool `N→` numbered lines;
       - a header in backticks with the body on the next line;
       - an encrypted RSA PEM (Proc-Type first);
       - a post-quantum age identity `AGE-SECRET-KEY-PQ-1…`. The installed sops 3.12.1 carries that prefix (`grep -c -a 'AGE-SECRET-KEY-PQ-' /usr/local/bin/sops` → 2). This repo's own recipient is classic (`age1pq1` count 0 in `.sops.yaml`), so that one case is latent here.
     - With no allow, every case is refused.
   - **End to end:** I ran `main()` on a fake transcript in scratch. Both the JSON-escaped key and the PQ identity gave `rc=0` with `key_material_archived=True`. The fixtures were deleted.
   - **Why the check misses it:** the check's GATE (`2026-09-24_secret_shape_check.py:72-79`) has one PEM form and one age form. R7-B's per-allow count was not applied.
   - **Harm path:**
     - `reports/.*` is excluded from pre-commit (`.pre-commit-config.yaml:45`).
     - Gitleaks runs only in CI, after the push (`ci.yml:1760`).
     - The pre-allow review this pass used (session `ddf7847c` transcript line 6358) sorts hits with the same two patterns. So such a report would read as "one known literal, 0 key material" and be allowed.
   - **Fix:** make the refusal tolerate separators. For example, refuse any `[A-Za-z0-9+/]{40,}` within about 400 chars of an allowed PEM header, or any `-----END … PRIVATE KEY-----` in the same report. For age, use `AGE-SECRET-KEY-[0-9A-Z-]*1[0-9A-Z]{10,}`. Add GATE cases for these forms. The alternative is to narrow the four claims to what the pattern actually catches.
   - **Changes a number/disposition/action?** Yes, an action (a tool fix). A wording-only narrowing would change none.

2. **LOW: the history of the bare `sk-` floor is false for three of the four tools.**
   - **Quoted:**
     - `…E2E-VALIDATION-EVIDENCE.md:9461-9462`: "the bare `sk-` floor round 6 had raised to 32 characters is back at 20 in all four shape-bearing tools".
     - The same file at `:9251-9252`: "restored the bare `sk-` floor that round 6 had raised".
     - `util/ad-hoc/README.md:748-749` says the same.
     - `2026-09-24_secret_shape_check.py:42`: "round 6 raised the bare floor to 32".
   - **Evidence:**
     - `git log -p` shows the launch scan and the tmpfs round-2 tool were written at `3f83b9c6` with `sk-[A-Za-z0-9]{32,}`, and the report archiver at `51993b37` with the same. `129f4880` kept 32 in the first two and did not touch the archiver's. Only the extractor went 20 (`b0b17cad`) → 32 → 20.
     - Today's check, run against `b0b17cad`'s tools, fails the 24-character case for the launch scan, the tmpfs tool and the archiver.
     - No evidence harm: at 20, both scan windows match, the 36 tmpfs files pass, and the 51 `phase9-scratch` files give 0 hits.
   - **Fix:** "restored in the extractor; lowered for the first time in the other three, which had used 32 since they were written." Apply the same to the README and the check's comment.
   - **Changes a number/disposition/action?** No.

3. **LOW: the ledger's statements of what the shape check shows no longer reproduce, and one never did.**
   - **Quoted:**
     - `…E2E-VALIDATION-EVIDENCE.md:9440-9441`: "missed seven, seven and three of the shapes `2026-09-24_secret_shape_check.py` tests".
     - The same file at `:9447-9448`: "fails 17 times on round 5's tools and passes on these".
     - The same file at `:9467`: "both tool findings, by that check".
   - **Evidence:**
     - The check at `3297131f`, run against `b0b17cad`'s tools, fails 30 times: extractor 7, launch scan 8, tmpfs tool 4, archiver 11.
     - Against `129f4880`'s tools it fails 14 times. `:9464` itself says so, which contradicts "passes on these".
     - On `129f4880`'s archiver, the five gate cases fail only because `unreviewed_shapes` does not exist there. Even the two cases that should pass ("passes a report with no shape") fail. So the check shows the function is missing, not R7-B finding 5's mechanism.
     - The check's docstring still says "(the three tools checked)".
   - **Fix:**
     - At `:9440-9448`, add "with the check as round 6 left it (`129f4880`)".
     - At `:9467`, write "finding 4 by that check; finding 5 by R7-B's fake-report run".
   - **Changes a number/disposition/action?** No; qualifiers suffice.

**CORRECTIONS YOU COULD NOT REFUTE**
- **Replay:** round 7's script run on `129f4880`'s ledger reports "applied 7 substitutions" and gives a file byte-identical to `3297131f`'s. A second run refuses. There was no hand edit.
- **cascor#678 ("Who"):**
  - GraphQL: created 09-23 02:02:52Z, `isDraft` false, one AutoSquashEnabled at 13:32:10Z (`pcalnon`), merged 20:22:13Z, and no draft or ready events.
  - Transcript `bc31e993` line 4227 (03:34:45.231Z; 0 secret and 0 e-mail shapes counted first) says "cascor#678 was armed the same way earlier".
- **Round-6 record:** R6-A's finding 1 is the question's time, and R6-B's finding 2 is the time plus four → three. Round 6's other substitutions changed no count, time or source line that round 5 added, so "except two" holds.
- **F-055 wording:** `…E2E-VALIDATION-EVIDENCE.md` shows NEVER-APPLIES at :8870 and APPLIES at :8893, and calls the latency criterion "unmeasured" at :8899-8900. This is consistent with the new text and with :9484.
- **Tools:**
  - The current check gives 0 failed (63 PASS).
  - Both launch-scan windows regenerate byte-identical (705 and 507 rows), so the 20-character floor adds no false positives.
  - The tmpfs dry run gives "already present 36 (re-checked; 0 failed a check)".
- **Allow scoping:**
  - The round-6 and round-7 reports regenerate byte-identical under their scoped allows.
  - With no allow, an allow for another agent, or an allow without `=`, the tool refuses (rc 1). There is no leak.
  - Across 49 archived reports and briefs, the only shape matches are reviewed quotes (round 6 :113; round 7 :93, :95, :100).
- **The check can fail:** it catches the allow ignoring the agent, the key-material refusal removed, a floor back at 32, and the lookbehind dropped. One blind spot is latent: `getattr(mod,"EMAIL_RE",None)` skips the e-mail cases for any tool without that name, so a consistent rename still passes with 0 failed.

**WHAT YOU COULD NOT CHECK**
- Whether any real key in the missed shapes exists on this host.
- R7-B's finding-5 mechanism on `129f4880`'s code; I relied on R7-B's run.
- Whether gitleaks would catch the JSON-escaped form in CI.
- The follow-up's rebase and tests, which this pass did not change.

**SECRETS/PII:** No slips.
- GraphQL selected logins, dates and event types only. No REST commit object was fetched, and no `cat-file commit`, `%GS`, `%ae` or `%ce` was used.
- Transcripts were read only through redacting code.
- Fake secrets were built by concatenation and reported as booleans only. The fixtures were deleted.
- No repository file changed, and the worktree is clean at `3297131f`. Scratch: `…/scratchpad/r8b.RXZBMV/`.

---
