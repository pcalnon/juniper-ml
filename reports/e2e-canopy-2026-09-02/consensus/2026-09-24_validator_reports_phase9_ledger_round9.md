<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 9: Lanes R9-A and R9-B, verbatim

Round 9 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 04db8614, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R9-A re-derived round 8's claims from their artifacts; Lane R9-B attacked round 8's corrections (3297131f..04db8614). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. R9-A's report quotes the bare prefix of an age key twice; that literal was reviewed and allowed for R9-A's report only (--allow-shape), and no key material follows it. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR9A_phase9_ledger_brief.md and laneR9B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round9_corrections.py.

## Lane R9-A -- measurement re-creation, artifact-first

*agent `a7612732b99a39397` · round 1 · last-assistant-text (not resumed) · 7695 chars*

**VERDICT: SOUND-WITH-FIXES.** All 7 claims re-derive from their artifacts. There are two LOW wording findings. Neither changes a number, disposition or action, so this round ends the review.

Paths: worktree `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda` at `04db8614`. Scratch `S=/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r9a.8GqmII`. "The ledger" is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, "the check" is `util/ad-hoc/2026-09-24_secret_shape_check.py`, and "the archiver" is `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`.

**TABLE**

| # | Claim | Re-derived value | Result | Evidence (command → output) |
|---|---|---|---|---|
| 1 | Replaying `util/ad-hoc/2026-09-24_phase9_ledger_round8_corrections.py` on `3297131f`'s ledger gives `04db8614`'s ledger | "applied 9 substitutions"; the result is byte-identical | MATCH | I copied `3297131f`'s ledger and the script into `$S/replay`, then ran `python3 -B …round8_corrections.py`. `cmp` → IDENTICAL, and both sha256 are `5ae98aae…`. A second run refuses ("REFUSED: 0 matches", rc 1). |
| 2 | First bare-`sk-` floor for each tool | Launch scan and tmpfs tool: added at `3f83b9c6`, both `sk-[A-Za-z0-9]{32,}`. Archiver: added at `51993b37`, `{32,}`. Extractor: added at `b0b17cad` with `{20,}`, then `{32,}` at `129f4880`. All four are `{20,}` at `3297131f` and `04db8614`. | MATCH | `git log --diff-filter=A` → `b0b17cad`, `3f83b9c6`, `51993b37`. `git grep -o 'sk-\[…\]{N,}'` at every commit touching them: the other three stay 32 through `129f4880`. There are no merges in `51993b37..HEAD`. |
| 3 | `key_material` refuses what its docstring and the ledger say, and the six forms are refused with the header allowed | Tested with 21 independent fakes: concatenated headers and random base64 bodies built in memory. All six forms are refused: JSON-escaped (with and without an END line), blockquote, `cat -n`, backticked header (with and without a fence), encrypted RSA with Proc-Type, and a PQ age identity. END lines of 6 key types are refused, even when the END line itself is allowed. A 40-character run ending at character 400 is refused; a 39-character run passes, matching the stated floor. The controls (header only, header plus short SHA, age prefix only) pass. No refusal came from some other shape. | MATCH | `python3 -B $S/keyprobe.py` → "0 failed of 21". The same fakes against `3297131f`'s archiver → 16 of 21 fail. End to end through `main()` (`$S/e2e_probe.py`): all 6 forms give rc 1 and write no output; the control gives rc 0. Fixtures deleted: True. |
| 4a | The check passes | rc 0, 71 PASS, "0 failed" | MATCH | `python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py` |
| 4b | Against `3297131f`'s archiver, with the current other three beside it, the check fails exactly the 7 new refusal cases | rc 1, "7 failed", 64 PASS. The 7 are JSON-escaped, blockquote, numbered lines, backticked header, encrypted RSA, END line alone and PQ age. | MATCH | `$S/check7/` |
| 5 | Round 6's and round 7's reports regenerate byte-identical under their scoped allows | Round 6 (`--round 2`, markers "Resume Lane R6-A"/"Resume Lane R6-B", allow `a40a56695bf031320=`+PEM header): rc 0, identical (`cfbeeeb6…`). Round 7 (`--round 1`, allow `aee9af37719ccc277=AGE-SECRET-KEY-`, 3 matches): rc 0, identical (`3358c06f…`). No allow, another agent's allow and an unscoped allow each give rc 1. | MATCH | `python3 -B $S/regen.py {scoped,none,wrong-agent,unscoped}`, with titles and intros taken from each file's header. The ledger names the allows by role only (:9477-9478, "round 6's PEM header, round 7's age-key prefix"). The agent ids and markers are traceable to the reports' own intros and agent lines. Extra check: round 8's report also regenerates identical (`e6423661…`). |
| 6 | No file under `reports/e2e-canopy-2026-09-02/`, and no script in `util/ad-hoc/`, holds key material | reports: 335 files (all tracked), 0 hits. `util/ad-hoc`: 1001 files (955 are .py/.bash/.sh), 0 hits. | MATCH | `python3 -B $S/kmscan.py` (counts only) |
| 7 | Triage counts | 70 findings, 19 open, 1 open P0, 6 open P1 (12 open P2) | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py`. The full output is identical on `3297131f`'s ledger, so no number or disposition moved. |
| extra | Round 6's "17", stated in round 8 as measured with the check as round 6 left it | The check at `129f4880` on `b0b17cad`'s tools: 17 (extractor 7, launch scan 7, tmpfs 3). On `129f4880`'s tools: 0. | MATCH | `$S/check6/`, `$S/check6b/` |

**FINDINGS**

1. **LOW: round 7's "fails 14 times" no longer reproduces.**
   - **Quoted:** ledger :9469-9470, "`2026-09-24_secret_shape_check.py` gained the cases that see both, and fails 14 times on round 6's tools".
   - **Evidence:** the check at `3297131f`, run on `129f4880`'s four tools, gives "14 failed". The current check gives "22 failed" (archiver 19, one each for the other three).
   - **Why it is round 8's:** round 8 grew the check. It added the "as round 6 left it" qualifier only to round 6's figures (:9445, :9452), and the check's docstring caveat names only "round 6 (17 failures)". Round 8 also rewrote this bullet into the present tense ("is now 20", "round 8 widened that").
   - **Fix:** write "and, as round 7 left it, fails 14 times on round 6's tools", and add round 7's 14 to the docstring caveat.
   - **Changes a number/disposition/action?** No.
2. **LOW: two provenance statements leave out round 7's classic-age refusal.**
   - **Quoted:**
     - ledger :9258, "Round 8 widened that refusal, which had caught only a header, whitespace and base64";
     - the check :76, "the key-material forms after the first one were added in round 8".
   - **Evidence:** `3297131f`'s archiver :48 is `KEY_MATERIAL_RE = …|AGE-SECRET-KEY-1[0-9A-Z]{10,}`, and my probe of that archiver refuses a whole classic age key, both in backticks and in JSON. The check's GATE case "a whole age key, its prefix allowed" was already there at `3297131f`:77, and it sits after the first key-material form.
   - **Fix:**
     - :9258: "…only a header, whitespace and base64, and a whole classic age key".
     - :76: "the key-material forms other than the first PEM form and the whole age key were added in round 8".
   - **Changes a number/disposition/action?** No.

**WHAT YOU COULD NOT CHECK**
- The sentence in round 7's re-derivation (:9473-9474) that says finding 4 was re-derived "by that check's 24-character case", and finding 5 "by reading the pattern … not by a run". It describes what the fix pass did in the parent session, and I did not read that transcript.
- The round-8 record's restated lane results outside my claims: cascor#678's events, both launch-scan windows, and the 36 tmpfs files. The round-8 report does record them.
- Key layouts outside the stated forms, such as bodies wrapped under 40 characters a line. Nothing claims these are covered.
- Whether gitleaks in CI would catch these forms.

**SECRETS/PII:** No slips.
- No environment variables, tokens or credential files were printed, and no GitHub API was called.
- git was used only for `%h` hashes, `git grep` and `git show <rev>:<path>`. No commit headers or signature fields were printed.
- Transcripts were read only through the archiver's own code, which prints labels and counts.
- Fakes were built by concatenation or in memory, only booleans were printed, and the end-to-end fixtures were deleted (confirmed).
- No tracked file changed, and the worktree is clean at `04db8614`. The ignored `util/ad-hoc/__pycache__/` predates this lane (mtimes 22:51–02:14).

---

## Lane R9-B -- adversarial, on round 8's corrections

*agent `a6e90f315e5a6804d` · round 1 · last-assistant-text (not resumed) · 8596 chars*

**VERDICT: SOUND-WITH-FIXES.** Replaying the round-8 script reproduces the ledger exactly. Every number the pass added checks out, and rounds 6, 7 and 8 regenerate byte-identical under the new gate. I have two LOW findings. Finding 1 changes an action if the tool is fixed, which I recommend and have tested in scratch. In that case §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` calls for a round 10. Fixing the wording only would change nothing.

**FINDINGS**

1. **LOW: round 8 replaced round 7's key-material refusal rather than widening it, and it dropped one form round 7 refused. The pass also changed round 7's test value (39 to 48 characters), so the check could not see the gap.**
   - **Quoted:**
     - `…E2E-VALIDATION-EVIDENCE.md:9258`: "Round 8 widened that refusal, which had caught only a header, whitespace and base64".
     - `…E2E-VALIDATION-EVIDENCE.md:9469`: "(round 8 widened that)".
     - `2026-09-23_archive_consensus_reports_by_round.py:119`: "key material (key_material(), widened in round 8) refuses regardless".
     - `2026-09-24_secret_shape_check.py:76`: "the key-material forms after the first one were added in round 8".
   - **Evidence:**
     - Round 7's PEM pattern (`3297131f`, archiver :48) was a header, then `\s*`, then `[A-Za-z0-9+/=]{20,}`. Round 8's `BASE64_RUN_RE` (:52) needs a run of 40 or more characters.
     - Test on truncated quotes (a header, a newline, a body, then "…"), header allowed, with PKCS#8, EC and OPENSSH headers:
       - bodies of 20, 30 and 39 characters: round 7 refuses, round 8 passes;
       - a 40-character body: both refuse.
     - Round 7's own check fails once when run against round 8's archiver: `check@3297131f on tools@04db8614` gives rc=1, "1 failed", on "refuses a header followed by key material, allowed".
     - That case's body was a 39-character base64 line. The pass changed it to the 48-character `B64` (check :82, :87). The round-8 record (`…E2E-VALIDATION-EVIDENCE.md:9490-9491`, "gained a case for each form, plus an END line alone") does not mention the change.
     - Comment :76 is also false for "a whole age key, its prefix allowed" (:94). That case is in round 7's gate cases (`git show 3297131f:…check.py`, :77).
     - **Harm path, narrow:** in a P-256 "EC PRIVATE KEY" (SEC1) the private scalar starts at byte 7. A 39-character truncated body therefore carries 22 of its 32 bytes. If a lane's header allow were granted, that body would be archived verbatim, and `reports/` is outside pre-commit (R8-B, `.pre-commit-config.yaml:45`). A whole key has 64- or 70-character lines and is still refused.
   - **Fix:**
     - Keep round 7's PEM pattern inside `key_material()` as well (one `re.findall` line), and add the 39-character case back as its own gate case.
     - Checked in scratch: the old pattern matches 0 of 1,341 files under `reports/e2e-canopy-2026-09-02/` and `util/ad-hoc/`. Both round 7's and round 8's checks give "0 failed", and rounds 6, 7 and 8 regenerate byte-identical.
     - Correct :76 so it says which cases are round 7's and that the first case's body was lengthened.
     - Alternatively, say "replaced", and state that a 20–39-character body after a header passes.
   - **Changes a number/disposition/action?** Yes, an action (a tool fix), if the tool is fixed. No, if only the wording changes.

2. **LOW: round 7's record still quotes a check count that round 8's larger check no longer gives.**
   - **Quoted:** `…E2E-VALIDATION-EVIDENCE.md:9469-9470`: "`2026-09-24_secret_shape_check.py` gained the cases that see both, and fails 14 times on round 6's tools".
   - **Evidence:**
     - `check@3297131f on tools@129f4880` gives "14 failed", so the number was true when written.
     - `check@04db8614 on tools@129f4880` gives "22 failed":
       - 3 from the 24-character `sk-` case (one each in the extractor, the launch scan and the tmpfs tool);
       - 6 from the archiver's shapes;
       - all 13 gate cases, because `unreviewed_shapes` does not exist in round 6's archiver.
     - Round 8 qualified round 6's numbers for exactly this reason (R8-B finding 3; :9445, :9452). The check's docstring (:19-21) names only round 6's "17 failures" as measured with an earlier check.
   - **Fix:** write "(with the check as round 7 left it)" after "14 times", and name round 7's 14 next to round 6's 17 in the docstring.
   - **Changes a number/disposition/action?** No.

**CORRECTIONS YOU COULD NOT REFUTE**
- **Replay:** round 8's script run on `3297131f`'s ledger says "applied 9 substitutions". The replay, `git show 04db8614:` and the worktree file share the sha256 `5ae98aaecf3b…`. A second run refuses (rc 1).
- **`sk-` floor history, from `git show` at every commit that touched each tool:**
  - extractor: `{20,}` at `b0b17cad` (its first commit), `{32,}` at `129f4880`, `{20,}` at `3297131f`;
  - launch scan and tmpfs tool: `{32,}` from `3f83b9c6` (their first commit);
  - archiver: `{32,}` from `51993b37` (its first commit);
  - all four at `{20,}` from `3297131f`.
  - `…E2E-VALIDATION-EVIDENCE.md:9251-9253` and `:9466-9468`, README :748-750 and check :46-47 all match.
- **Round 6's numbers, "as round 6 left it":** `check@129f4880` fails 17 times on `b0b17cad`'s tools (7, 7 and 3) and 0 times on `129f4880`'s.
- **"Fails those 7 on round 7's archiver":** `check@04db8614` on `3297131f`'s tools gives exactly the six named forms plus the END line alone. On its own tools it gives 0 failed (71 PASS).
- **`key_material` refuses every form it names**, even with every `SECRET_RE` literal allowed:
  - END lines for PKCS#8, RSA, EC, DSA, OPENSSH and ENCRYPTED keys, alone or closing a block;
  - each of those headers followed by a body with no END line;
  - a JSON-escaped body (LF and CRLF), a blockquote, `cat -n` lines, Read-tool `N→` lines, a backticked header, an encrypted RSA key with an AES-256 IV, a single-line PEM, and a one-line Ed25519 body;
  - classic age identities (bare, backticked) and post-quantum ones (bare, in JSON).
  - The window behaves as stated: a 40-character run whose last character is the 400th is refused; a run starting at character 361 is not.
- **Regeneration:** run in-process with `--out` in scratch, rounds 6, 7 and 8 regenerate byte-identical under their scoped allows (rc 0), and each is refused with no allow (rc 1).
- **"No file … holds key material":** `key_material()` finds 0 hits in 1,341 files.
- **How rounds 7 and 8 re-derived their findings**, from the parent transcript (ddf7847c; timestamps, tool descriptions and booleans only):
  - Round 7: before its tool edits, the only archiver probe was "Show the report archiver's secret pattern" (line 6240). The 24-character case ran against round 6's tools (6313) before the ledger pass (6344).
  - Round 8: "Confirm each tool's original sk- floor" (6495) and "Run the check against round-7's archiver" (6560) both precede the ledger pass (6616).
- **The check can fail.** Changes I made to scratch copies of the archiver, and how many cases each failed:
  - `key_material()` returning nothing: 9;
  - END lines no longer refused: 1;
  - post-quantum age identities no longer refused: 1;
  - window of 0 characters: 5; window of 100: 1;
  - minimum base64 run of 50: 5; minimum run of 8: 1;
  - key material checked only when the agent has an allow: 1;
  - an allow that ignores the agent: 1.
- **Legitimate text refused, and not allowable (not a finding):** the gate now refuses a quoted PEM END line, and a full 40-character hex SHA or a sha256 digest within 400 characters after a quoted header. No --allow-shape can pass either, but it fails closed and no archived report is affected. Separately, "any PEM END line" (:9259, :9488, README :752) covers only private-key END lines; a certificate's is not refused, which is harmless.

**WHAT YOU COULD NOT CHECK**
- Whether gitleaks in CI catches a truncated key body.
- Both scan windows and the finding counts. This pass changed neither tool, so I relied on R8-A and R8-B.
- Anything off this host.

**SECRETS/PII:** None printed or sent; no slips. No REST commit objects, no GraphQL, and no commit headers or signature fields; git was used only for `git show <sha>:<path>` and `%h %ad %s` formats. Lane transcripts were read only through the archiver's own gate, and the parent transcript as booleans, timestamps and tool descriptions. Fakes were built in memory by concatenation and random draws and reported as booleans only. Scratch fixtures and report copies are deleted. Neither forbidden script was run. The worktree is clean at `04db8614`; nothing changed.

---
