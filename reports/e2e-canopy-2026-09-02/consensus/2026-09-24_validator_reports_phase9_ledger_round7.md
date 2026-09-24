<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 7: Lanes R7-A and R7-B, verbatim

Round 7 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit 129f4880, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R7-A re-derived round 6's claims from their artifacts; Lane R7-B attacked round 6's corrections (b0b17cad..129f4880). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. R7-B's report quotes the bare prefix of an age key three times while discussing the archiver; that literal was reviewed and allowed for R7-B's report only (--allow-shape), and no key material follows it. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR7A_phase9_ledger_brief.md and laneR7B_phase9_ledger_corrections_brief.md. The fix pass is util/ad-hoc/2026-09-24_phase9_ledger_round7_corrections.py.

## Lane R7-A -- measurement re-creation, artifact-first

*agent `ae345a034fa9fadde` · round 1 · last-assistant-text (not resumed) · 7270 chars*

**VERDICT: SOUND-WITH-FIXES.** Every listed claim re-derives from its artifact. There is one LOW wording finding, and it changes no number, disposition or action, so under the procedure's rule this round ends the review.

**TABLE** (ledger = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` at `129f4880`; round-6 report = `reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round6.md`)

| Claim | Re-derived value | Verdict | Evidence |
|---|---|---|---|
| 1a. Asked 03:34:45Z, answered 07:32:48Z | Question: L4227 `AskUserQuestion` at 03:34:45.231Z. Answer: L4260 `tool_result` at 07:32:48.582Z, "Mine: fix forward" | MATCH | `owner_answer_extract.py <bc31e993.jsonl> 4227 4260`. A record-shape scan of 03:33–07:34Z shows no other answer. "Four minutes after round 5's artifact": `07aef715` was committed at 07:28:28Z, so the gap is 4 min 20 s. |
| 1b. Four PRs named; three were drafts readied then armed 4–7 s later; canopy#678 never a draft and never armed | The question names data#428, ml#2032, ml#2059 and canopy#678. data#428: ready 22:29:55, armed 22:29:59 (4 s). ml#2032: 22:27:20 → 22:27:27 (7 s). ml#2059: 21:47:22 → 21:47:26 (4 s). Each had an earlier `ConvertToDraftEvent`. canopy#678 has only a `MergedEvent` (22:29:21Z) | MATCH | `gh api graphql -F query=@prs.graphql`, reading `timelineItems` for ready, draft, auto-squash/auto-merge and merge events. Actors are logins only, all `pcalnon`. |
| 1c. Other five PRs: #676, data#431, data#434 share the pattern (4–8 s); ml#2066 and data-client#212 do not | #676: 22:28:04 → 22:28:12 (8 s). data#431: 22:50:54 → 22:50:58 (4 s). data#434: 22:51:07 → 22:51:12 (5 s). All three were drafted first. ml#2066: armed 22:27:08, no draft events. data-client#212: `MergedEvent` only | MATCH | Same query. |
| 2a. `96e7b105` is on the branch, its parent is `6c4ad9a9` (canopy#679), and #679 changed `CHANGELOG.md` | `96e7b105 6c4ad9a9 fix(idle-cuts)…`. #679's merge commit is `6c4ad9a97185…`, and its `--stat` shows `CHANGELOG.md \| 14 ++`. `ls-remote --heads origin fix/idle-cuts-round3-wording` returns nothing, so "not yet pushed" holds | MATCH | Note, not a finding: canopy `origin/main` is now `5907713b` (canopy#680, 09:08:39Z). That is before `129f4880` was frozen (09:17:17Z), and #680 also changed `CHANGELOG.md` (+15). The branch reads "ahead 1, behind 1". The ledger's sentence is a true record of the rebase; the brief's "origin/main has since moved to 6c4ad9a9" is out of date. |
| 2b. `range-diff` shows an identical patch | `1:  26bf27b3 = 1:  96e7b105` | MATCH | `git range-diff e9053227..26bf27b3 6c4ad9a9..96e7b105` |
| 2c. The test file passes there | 13 passed, exit 0, at HEAD `96e7b105`; the worktree was clean afterwards | MATCH | JuniperCanopy1 pytest `-q -p no:cacheprovider`, run from the follow-up worktree with no bytecode written. |
| 3a. The check passes | `0 failed`, exit 0 (42 cases) | MATCH | `python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py` |
| 3b. The check fails 17 times on round 5's tools | Exit 1, `17 failed`: the extractor fails 7, the launch scan 7, the archive tool 3 (sk-ant-, sk-proj- and the %40-encoded address). This is also the ledger's "seven, seven and three" | MATCH | The three tools taken from `b0b17cad` with `git show`, next to a copy of the check in scratch. |
| 3c. Both launch-scan windows regenerate byte-identical | `cmp` exits 0 on both (705 and 507 rows; sha256 `d8825e0e…` and `b55d48b0…` equal) | MATCH | The scan's two `--start/--end` windows compared with the archived `merge_capable_calls_0923T00_0924T0140.out` and `merge_capable_calls_0920_0923.out`. |
| 3d. The archive tool's `--dry-run` re-checks 36 files, 0 failing | `would copy 0, already present 36 (re-checked; 0 failed a check)`, exit 0 | MATCH | Extra: the widened shapes over all 51 files under `phase9-scratch/` give 0 hits. |
| 4a. The bar shows Stopped during a replay through its own `else` (`dashboard_manager.py:7508-7518`) | Lines 7508–7518 are the failed / completed / running / paused chain, and its `else` sets "Stopped". Neither the builder nor `/api/status` (`main.py:1463-1477`) has a replay branch. `service_backend.py:250-253` gives REPLAYING four false flags. `:887` is `children="Stopped"`; `state_sync.py:177` defaults to "Stopped". After a replay, cascor's `stop_replay` sends RESET, which lands in STOPPED | MATCH | canopy `e9053227` read with `git show`; cascor `origin/main` checked for the stop path. |
| 4b. F-CANOPY-055 holds the layout default only on a page slower than its 1 s tick | Phase 9's F-055 record: the trio parent leg `:8056` NEVER-APPLIES (8869); the demo parent leg `:8059` APPLIES (8893); the latency criterion is "suggests…, unmeasured" (8898-8900) | MATCH on page-dependence. The "only" at 9429 is unsupported: see Finding 1 | 9172's conditional wording is consistent with the record. |
| 5. Counts | 70 total: 48 fixed, 1 accepted, 2 withdrawn, 19 open; open P0 1, open P1 6, open P2 12 | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py`, run from the worktree, matches ledger lines 9476-9480. |
| Extras (not on the list) | Replaying round 6's 14 substitutions on `b0b17cad`'s ledger gives a file `cmp`-identical to `129f4880`'s, so there was no hand edit. ml#2057 was created at 20:09:33Z; session `1f771cb0` ran `open_signed_pr.py` at 20:09:28Z and then only the GET-only `watch_pr_runs.bash`. The ledger is 783,241 B, about 1.04 MB base64-encoded. Both round-6 lanes returned SOUND-WITH-FIXES | MATCH | — |

**FINDINGS**
1. **LOW.** Ledger line 9429 reads: "F-CANOPY-055 freezes the bar only on a page slower than its tick".
   - **Evidence:** line 9455 of the same ledger lists "that F-CANOPY-055's bar freezes only on pages slower than the tick (the drive recorded no latency)" under "What the evidence cannot support". F-055's record (8898-8900) calls the criterion "unmeasured". Round 6's own R6-A finding 4 (round-6 report, 121-132) cites the same limit. What was measured is only that the freeze depends on the page.
   - **Fix:** drop "only". For example: "F-CANOPY-055 freezes the bar on some pages, not every page (the trio's, slower than its tick)".
   - **Changes a number, disposition or action?** No.

**WHAT YOU COULD NOT CHECK**
- A live REPLAYING page, because no service could be started. The status-bar result comes from source only.
- The latency criterion itself; the ledger cannot support it either.
- The cascor line citations at 9167-9170 at their original commit. Line numbers differ on current cascor `main`, so I checked the behaviour only.
- That a session limit killed both round-6 lanes and they were resumed.
- The signing key of the 03:00Z commits, which would need signature fields.
- Whether the follow-up rebases cleanly onto `5907713b`. I did not run `merge-tree`, to avoid writing objects.

**SECRETS/PII:** Nothing was printed or sent. GraphQL requested logins only. Transcripts were read only through the redacting extractor or bounded, redacted scans: `bc31e993` lines 4227 and 4260, and three records of `1f771cb0`. No commit headers or signature fields were read (git formats used: `%h %p %s %cI %aI`). No slips. No tracked file changed; scratch work stayed in `mktemp -d` `…/scratchpad/r7a.m6zpUC`, and both worktrees are clean.

---

## Lane R7-B -- adversarial, on round 6's corrections

*agent `aee9af37719ccc277` · round 1 · last-assistant-text (not resumed) · 10387 chars*

**VERDICT: SOUND-WITH-FIXES.** The core of the pass holds. The round-6 script, replayed on `b0b17cad`'s ledger, gives `129f4880`'s ledger byte for byte ("applied 14 substitutions"). The question's time, the three drafts, the membership of the answer's scope and every ready and arm time re-derive from the transcript and the GraphQL timelines. The pass's new text has three LOW false or misleading statements, and its tool changes have two defects. Findings 4 and 5 each change an action (a tool fix).

**FINDINGS**

1. **LOW: the round-6 record says every number round 5 added held, then lists two it changed.**
   - Quoted, `…E2E-VALIDATION-EVIDENCE.md:9423-9424`: "every count, time and source line round 5 added held, including the signing key of the 03:00Z commits."
   - Evidence: the next bullet of `…E2E-VALIDATION-EVIDENCE.md` (`:9426-9427`) corrects "the question's time (03:34:45Z; 07:32:48Z is the answer)" and "the three of its four PRs that were drafts". Round 5's pass added both (`b0b17cad`: "at 07:32:48Z … asked … took four PRs out of draft").
   - `2026-09-24_validator_reports_phase9_ledger_round6.md` scores row 1a MISMATCH ("Changes a number: yes"), and R6-B's finding 2 says "Yes, numbers: the time of the question, and four → three".
   - Fix: "…held, except the question's time and the count of drafts (R6-A 1, R6-B 2)…".
   - Changes a number/disposition/action? No.

2. **LOW: the round-6 record states as fact what the ledger lists as unsupported.**
   - Quoted, `…E2E-VALIDATION-EVIDENCE.md:9429`: "F-CANOPY-055 freezes the bar only on a page slower than its tick".
   - Evidence: `…E2E-VALIDATION-EVIDENCE.md:9455`, under "What the evidence cannot support", lists "that F-CANOPY-055's bar freezes only on pages slower than the tick (the drive recorded no latency)". R6-B's finding 4 cited that same entry.
   - The pass's F-059 text (`:9172`) is conditional, not "only", and is fine.
   - Fix: drop "only", or add "(whether only there is unmeasured)".
   - Changes a number/disposition/action? No.

3. **LOW: cascor#678's false premise is left standing in the sentence that corrects canopy#678's.**
   - Quoted, `…E2E-VALIDATION-EVIDENCE.md:8799`: "It added that cascor#678 was armed the same way that morning".
   - Evidence: GraphQL shows juniper-cascor#678 was not a draft when opened (2026-09-23T02:02:52Z). Its only events are AutoSquashEnabled at 13:32:10Z and Merged at 20:22:13Z, with no ConvertToDraft and no ReadyForReview. So, like canopy#678, it was never "taken out of draft".
   - `b0b17cad` said, neutrally, "cascor#678's morning arm". The pass wrote "the same way" right after qualifying the four PRs ("which three were"), so the sentence reads as true.
   - The question said "earlier". "That morning" follows a sentence dated 2026-09-24, but the arm was on 09-23.
   - Fix: "…armed the same way earlier (its only arm: 09-23 13:32:10Z; it too was never a draft)".
   - Changes a number/disposition/action? No.

4. **LOW: the answer extractor's bare `sk-` shape was narrowed, not widened.**
   - Quoted:
     - `util/ad-hoc/2026-09-24_owner_answer_extract.py:17-19`: "these token shapes redacted: … sk- keys (sk-ant-, sk-proj-) … A shape not in that list is printed";
     - `…E2E-VALIDATION-EVIDENCE.md:9249`: "Round 6 widened its secret shapes";
     - `util/ad-hoc/README.md:746-747`: "Round 6 widened all three".
   - Evidence: round 5's `sk-[A-Za-z0-9]{20,}` became `(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{32,}` (`:35`).
     - I tested constructed fake values of `sk-` plus 20, 24 and 31 alphanumerics, printing booleans only. `b0b17cad`'s extractor redacts all three; `129f4880`'s prints all three. At 32 characters both redact.
     - `2026-09-24_secret_shape_check.py` cannot see this: its only bare-`sk-` value is 48 characters, and it passes 42/42 on the narrowed tool.
   - Fix: restore the `{20,}` floor for the bare form, keeping the lookbehind and `_-`, and add a 20–31-character case to the check. Otherwise, state the 32-character floor in the docstring.
   - Changes a number/disposition/action? Yes: an action (a tool fix).

5. **MINOR: `--allow-shape` cannot tell a quoted header from a real key.**
   - Quoted, `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py:83-85`: "a report may QUOTE a shape without holding a secret … A match is ignored only if its whole text equals one of these literals; any other match still refuses."
   - Evidence: two of the tool's `SECRET_RE` alternatives (`:37`) match only a prefix: `-----BEGIN [A-Z ]*PRIVATE KEY-----` and `AGE-SECRET-KEY-`. So a real key produces exactly the allowed literal.
     - I built fake reports in my scratch directory and ran the tool with `--out` pointing there. With round 6's literal (the OPENSSH header) allowed, a report holding a whole fake PEM block (header, body and footer) was archived: `rc=0`, "1 match(es), each an --allow-shape literal", body archived = True.
     - With `AGE-SECRET-KEY-` allowed, a full fake age key was archived the same way.
     - Any other literal still refuses (`rc=1`).
     - An allow applies to every agent in the run, with no count limit.
     - `reports/` is in pre-commit's global exclude (`.pre-commit-config.yaml:45`), so `detect-private-key` never sees the archive. gitleaks runs only in CI (`.github/workflows/ci.yml:1765`), after the push.
     - Context, not a separate finding: this tool's own `SECRET_RE` was not widened. It still passes `sk-ant-`, `gho_`, `ghs_`, `hf_`, `xox*`, `pypi-` and JWT shapes in the lane reports it archives verbatim.
   - Fix: refuse when an allowed prefix shape is followed by key material (for example, match the PEM header plus the next base64 line, and `AGE-SECRET-KEY-1[0-9A-Z]{10,}`). Scope each allow to an agent id and a count.
   - Changes a number/disposition/action? Yes: an action (a tool fix).
   - The round-6 archive itself is clean. It regenerates byte-identically, and its only PEM-shaped text is the inline quote at `2026-09-24_validator_reports_phase9_ledger_round6.md:113`.

**CORRECTIONS YOU COULD NOT REFUTE**
- **The owner exchange.** Before printing, I counted secret and e-mail shapes on transcript lines 4227 and 4260 (0 and 0), then printed them through the redacting extractor.
  - The question is at 03:34:45.231Z and the answer at 07:32:48.582Z, 4 min 20 s after `07aef715` (07:28:28Z).
  - The question names data#428, ml#2032, ml#2059 and canopy#678, and says "cascor#678 was armed the same way earlier".
  - The chosen option reads: "The sweeper is yours and the merges are intended. I keep validating after the merge and fix forward with follow-up PRs."
  - "Who", item 15 and the cannot-support entry now agree, and none overstates the answer.
- **The timelines (GraphQL).**
  - Ready, then arm: data#428 4 s, ml#2032 7 s, ml#2059 4 s, #676 8 s, data#431 4 s, data#434 5 s.
  - canopy#678 has no draft, ready or arm event and merged at 22:29:21Z.
  - ml#2066 was armed at 22:27:08Z and was never a draft.
  - data-client#212 has only its merge, at 22:30:44Z.
- **ml#2057.** Only two tool calls between 19:50Z and 21:00Z name it or its branch, both from session 1f771cb0:
  - `open_signed_pr.py` at 20:09:28Z (it has no arming code);
  - `watch_pr_runs.bash` at 20:09:37Z.
- **The status bar, at canopy `e9053227`.**
  - `:887` is the "Stopped" default, and the `else` gives "Stopped".
  - The bar is driven by `fast-update-interval` at `FAST_UPDATE_INTERVAL_MS = 1000` (`canopy_constants.py:370`).
  - In cascor `0e016a7c`, `stop_replay` and `reset` both reset the FSM and write Stopped / Idle. So item 16's "Stopped both during … and after one" holds.
- **The tools.**
  - `2026-09-24_secret_shape_check.py` can fail: on `b0b17cad`'s tools it exits 1 with 17 FAILs (7, 7 and 3). On `129f4880`'s it passes 42/42.
  - Both launch-scan windows regenerate byte-identical (`cmp` exit 0; 705 and 507 rows), so the widened shapes produce no false positives there.
  - The tmpfs archive tool's dry run reports "already present 36 (re-checked; 0 failed a check)".
  - Every e-mail-shaped string in the archived reports is a reserved example domain.
- **The follow-up rebase.**
  - `git range-diff` gives "1: 26bf27b3 = 1: 96e7b105".
  - The branch and the commit are not on GitHub (404 and 422).
  - The test file has 13 test functions.
- **Counts.** Triage gives 70 findings: 48 fixed, 1 accepted, 2 withdrawn, 19 open (1 P0, 6 P1, 12 P2). The ledger is 783,241 B, so "about 780 KB" holds.
- **The walk.**
  - R6-A's findings 1–2 and R6-B's findings 1, 2 and 5 are applied and true.
  - R6-B's finding 3 is applied, with finding 4's regression.
  - R6-B's finding 4 is applied correctly at F-059 and item 16, but the round-6 record re-states the overreach (finding 2).
  - Nothing that changed a number, disposition or action was dropped.

**WHAT YOU COULD NOT CHECK**
- I did not run the follow-up's tests ("13 passed"). The file imports canopy's `DashboardManager` and spawns node, so I only counted its test functions.
- Canopy `main` moved to `5907713b` (canopy#680, merged 09:08:40Z) 8.5 minutes before the pass was committed (09:17:17Z). #680 touches `CHANGELOG.md` about 40 lines from the follow-up's hunks. Item 13's statement is true as history. I did not test a re-rebase, because `merge-tree` writes objects.
- Actors off this host, and what the owner meant beyond the option text.
- Whether any key in real use here has a bare `sk-` body of 20–31 characters, which would make finding 4 more than latent.
- The push tool and the F-058 census, which were off-limits.

**SECRETS/PII:** One slip.
- **The slip:** `gh api …/juniper-canopy/commits/main --jq '.sha[0:8]'` fetched a REST commit object, which carries author and committer e-mail fields. Only the 8-character SHA was printed.
- Two other REST GETs (the branch and `commits/96e7b105`) returned 404 and 422, with no data.
- Nothing else printed a secret or an address:
  - GraphQL selected logins, event types and times only.
  - Fake secrets were built by concatenation and reported as booleans; the fake PEM and age fixtures were deleted afterwards.
  - The ml#2057 scan printed two redacted snippets of 170 characters.
  - git reads used `%h`, `%cI`, `%aI` and `%s` only.
- No repository file was changed, and both worktrees are clean. Scratch: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r7b.a5HRiv/`.

---
