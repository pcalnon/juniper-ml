<!-- markdownlint-disable -->

# Phase 9 ledger validation, round 10: Lanes R10-A and R10-B, verbatim

Round 10 of the consensus validation of the canopy E2E evidence ledger's Phase 9 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md), on the frozen juniper-ml commit b0eb4ac1, under notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md. Lane R10-A re-derived round 9's claims from their artifacts; Lane R10-B attacked round 9's corrections (04db8614..b0eb4ac1). Each is a fresh agent, so its report is its last assistant text; 'round 1' in the per-report line is the agent's own first round. Round 10 changed no number, disposition or action, so under section 4 of the procedure the review of Phase 9's text terminated here; R10-B's one LOW finding, a code comment, was corrected in the tool directly and the round is recorded by util/ad-hoc/2026-09-24_phase9_ledger_round10_corrections.py. Briefs: reports/e2e-canopy-2026-09-02/drafts/laneR10A_phase9_ledger_brief.md and laneR10B_phase9_ledger_corrections_brief.md.

## Lane R10-A -- measurement re-creation, artifact-first

*agent `a42214cec2ef1ec33` · round 1 · last-assistant-text (not resumed) · 7145 chars*

**VERDICT: SOUND.** All seven claims re-derive exactly from the frozen artifact (`b0eb4ac1`). I have no findings, so round 10 changes no number, disposition or action, and under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` the review ends. I worked read-only and changed no repo file (`git status` shows 0 changes, HEAD `b0eb4ac1`). Scratch directory: `…/scratchpad/r10a.9DgGlt`. The ledger is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and the archiver is `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`.

**TABLE**

| # | Claim | Re-derived value | Result | Evidence |
|---|---|---|---|---|
| 1 | Replaying round 9's script (`2026-09-24_phase9_ledger_round9_corrections.py`) on `04db8614`'s ledger gives `b0eb4ac1`'s ledger | "applied 6 substitutions" (dry run also exits 0); the output is byte-identical to `b0eb4ac1`'s ledger | MATCH | I ran the script in scratch on the `04db8614` ledger. `cmp` said IDENTICAL, and both sha256 are `53a84a88…`. I also checked round 9's statement that "the replay of round 8's script is exact": the round-8 script on `3297131f`'s ledger says "applied 9 substitutions" and matches `04db8614`'s ledger (`cmp` IDENTICAL). |
| 2 | `key_material` refuses every form its docstring and the ledger list, with the header allowed | 16,986 fake cases, all refused, and `key_material` found something in every one | MATCH | I ran `claim2.py`, allowing the matching header for each of six PEM types (OPENSSH, RSA, EC, DSA, ENCRYPTED, plain). **END lines:** 72/72. **Header, whitespace, then 20+ base64 characters:** 13,992/13,992. This covers every body length from 20 to 39 plus 40/48/64/70, 11 kinds of whitespace (LF, CRLF, space, tab, two LFs, NBSP, form feed, vertical tab, 500 LFs, none), 8 endings, and bodies with `=` padding. **A 40+ run within 400 characters:** 2,382/2,382, covering six separators and every start offset from 0 to 360. **Age identities, classic and post-quantum:** 540/540, bodies of 10 to 2000 characters, with the prefix and a header allowed. **End to end** through the archiver's command line, on a fake transcript with `--out` in scratch: each form gives rc 1 and "REFUSED"; a header-only control gives rc 0. |
| 3a | The shape check passes | "0 failed" | MATCH | `python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py` exits 0. |
| 3b | Against `04db8614`'s archiver it fails once, on the 39-character case | "1 failed", on that case | MATCH | Exit 1. The only FAIL is "refuses a header then a 39-character body, allowed". |
| 3c | Round 7's own check passes beside the current four tools | "0 failed" | MATCH | `3297131f`'s check exits 0, with 63 PASS lines. |
| 4 | Rounds 6, 7 and 8 regenerate byte-identical under their scoped allows | All three identical | MATCH | I ran the current archiver with `--out` in scratch. **Round 6:** `--round 2`, markers "Resume Lane R6-A" / "Resume Lane R6-B", allow `a40a56695bf031320=` the OPENSSH PEM header; sha `cfbeeeb6…`. **Round 7:** `--round 1`, allow `aee9af37719ccc277=` the age prefix; sha `3358c06f…`. **Round 8:** allows `ae24ee966b7499c5e=` the age prefix, and `ad53f5c6414e62707=` the age prefix plus the plain PEM header; sha `e6423661…`. **Controls:** with no allow, or with each allow moved to the other lane, every round is refused (rc 1). **Extra:** round 9's report also regenerates identical (`38e561fb…`), and both round-9 briefs match each agent's first user message apart from a trailing newline. |
| 5 | No report file and no `util/ad-hoc/` script holds key material | 0 hits | MATCH | **reports/e2e-canopy-2026-09-02/:** 338 files, both committed and on disk, 0 with key material. **util/ad-hoc/:** 1002 files committed (956 of them `.py`/`.bash`/`.sh`) and 1007 on disk, 0 with key material. |
| 6 | The ledger's account of round 7's refusal and round 8's replacement matches the code at `3297131f` and `04db8614` | Consistent with both | MATCH | **Round 7 (`3297131f`):** the pattern is a PEM header, whitespace and 20+ base64 characters, or a classic age key. Run on the same fakes, it refused 13,992/13,992 header-and-body cases and 270/270 classic age keys, but 0/72 END lines and 0/270 post-quantum keys. Round 8's check fails exactly 7 cases on it: the six named forms plus an END line alone. **Round 8 (`04db8614`):** `key_material` has no PEM-body form, and 11,880 of the 20–39-character cases pass its gate. Its check case has a 48-character body, against round 7's 39, and on its own tools it reports "0 failed", which is how the drop stayed hidden. **Round 9:** its PEM-body pattern is string-equal to round 7's PEM form, and its age pattern covers everything round 7's did. |
| 7 | Triage counts | 70 findings, 19 open, 1 open P0, 6 open P1 | MATCH | `python3 -B util/ad-hoc/e2e_finding_triage.py` |

Other numbers in round 9's text, re-derived:
- **Round 7's "fails 14 times":** round 7's check on round 6's tools (`129f4880`) gives 14 failed.
- **Round 6's 17:** round 6's check on round 5's tools (`b0b17cad`) gives 17 failed, and 0 on its own tools.
- **"Fails those 7":** round 8's check on round 7's tools gives 7; so does round 9's check.
- **"A later, larger check fails more often":** the current check gives 39 failures on round 5's tools and 23 on round 6's.
- **"R9-A tested 21 fakes":** matches the round-9 report (`2026-09-24_validator_reports_phase9_ledger_round9.md`), which says "Tested with 21 independent fakes". That report also gives both lanes' verdicts as SOUND-WITH-FIXES.
- **"Re-derived before applying (round 9)":** in the parent transcript, the tool edits ran 10:22:49–57Z, the checks 10:23:04–21Z, the regenerations 10:23:39–56Z and the sweep 10:24:06Z, all before the ledger pass at 10:25:01Z.

**FINDINGS:** none.

Two things are incomplete but not false, so they are not findings:
- Round 8's archiver also let through a header followed by more than 360 whitespace characters and then a full body (192 of my cases). The restored round-7 form refuses these again. The ledger names only the 20–39-character consequence.
- The check's case-history comment does not say that round 8 added the "SHA and a path" pass case.

**WHAT YOU COULD NOT CHECK**
- I did not re-derive "every tool's `sk-` floor history held" from each tool's git history. I relied on the round-9 report for it.
- The "before applying" ordering rests on tool-call descriptions and timestamps only, not on the outputs of those calls.
- I did not test key forms that no statement claims, and did not check whether gitleaks or the pre-commit hooks would catch them.
- I did not check PR or CI state (read-only).

**SECRETS/PII:** No slips.
- I printed no environment variables, tokens, credentials or commit headers or signatures; I read commit text only through `git log -1 --format=%B`.
- Every fake was built by concatenation, and I printed only labels, booleans and counts.
- The fake-transcript fixtures are deleted and confirmed gone, and the regenerated report copies are deleted. A sweep of the 68 remaining scratch files found no key material.
- Nothing was sent to any external service, and the owner's email was not used.

---

## Lane R10-B -- adversarial, on round 9's corrections

*agent `a05ffc1d938624d4b` · round 1 · last-assistant-text (not resumed) · 6000 chars*

**VERDICT: SOUND-WITH-FIXES.** I found one LOW finding: a code comment that this pass made false. It changes no number, disposition or action, so under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` this round ends the review.

"The ledger" is `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, "the archiver" is `util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py`, and "the check" is `util/ad-hoc/2026-09-24_secret_shape_check.py`.

**FINDINGS**

1. **LOW: the pass made the archiver's round-8 comment false.**
   - **Quoted** (archiver :47-49): "Round 7's form ("a header, whitespace, base64") missed a JSON-escaped body, a blockquote, numbered lines, a backticked header, an encrypted PEM's Proc-Type lines and a post-quantum age identity (round 8, …), so it no longer depends on separators."
   - **What changed:** the pass added `PEM_BODY_RE` directly below this comment (:52-54). Round 9's refusal of a 20–39-character body now works only when whitespace separates it from the header.
   - **Evidence:** in-memory fakes, header allowed, booleans only.
     - At `b0eb4ac1`, 20- and 30-character bodies are refused after a newline.
     - The same bodies pass when JSON-escaped, blockquoted, in `cat -n` lines, after a backticked header, in Read-tool arrow lines, and after an encrypted RSA header's Proc-Type lines.
     - At `04db8614` all of these passed alike, so the comment was true before this pass.
   - **Not a regression:** round 9 refuses a superset of what rounds 7 and 8 refused. The ledger (:9261-9263), the README (:752-754) and the docstring (:61-63) all say "followed by whitespace", which is correct.
   - **Fix (wording):** "…, so its 40-character window no longer depends on separators; round 7's form, kept below for 20-39-character bodies, still needs whitespace after the header."
   - **Changes a number/disposition/action?** No.

**CORRECTIONS YOU COULD NOT REFUTE**
- **Replay:** running `util/ad-hoc/2026-09-24_phase9_ledger_round9_corrections.py` on `04db8614`'s ledger prints "applied 6 substitutions". The result is byte-identical to `b0eb4ac1`'s ledger (sha256 `53a84a88beda…`), and a second run refuses with rc 1. All 6 substitutions are in Phase 9 (the ledger from :8490 on).
- **The check at `b0eb4ac1`:** rc 0, 72 PASS, "0 failed".
- **The check can fail, and the 39-character case sees the dropped form:**
  - With round 8's archiver: "1 failed", and it is exactly "refuses a header then a 39-character body, allowed".
  - With `PEM_BODY_RE` removed from a scratch copy: the same single FAIL.
- **Round 7's check:**
  - on round 9's tools: 0 failed;
  - on round 8's tools: 1 failed, its 39-character case, while round 8's own check gave 0 there. So lengthening the case did hide the drop.
- **Case bodies:** round 7's first key-material case body is 39 characters, and `B64` is 48.
- **Round 7's "14":** round 7's check on `129f4880`'s tools gives "14 failed". The current check gives 23 on the same tools, so the docstring's "a later, larger check fails more often" holds.
- **Round 8's "fails those 7":** the current check on `3297131f`'s tools still gives the same 7 failures.
- **Body-length sweep** (6 header types × 5 separators, header allowed):

  | Body length | Round 7 | Round 8 | Round 9 |
  |---|---|---|---|
  | 19 | passes | passes | passes |
  | 20, 30, 39 | refuses all | passes all | refuses all |
  | 40 | refuses all | refuses all | refuses all |

- **Regeneration** with round 9's archiver, `--out` in scratch:
  - Rounds 6, 7, 8 and 9 each give rc 0 and a byte-identical file (`cfbeeeb6…`, `3358c06f…`, `e6423661…`, `38e561fb…`) under per-agent allows. Round 6 was run as `--round 2` with its R6 markers.
  - With no allow, each gives rc 1.
  - `key_material` and `PEM_BODY_RE` find 0 hits in every agent's section.
- **Key-material sweep** with `b0eb4ac1`'s `key_material`: 0 of 338 files under `reports/e2e-canopy-2026-09-02/` and 0 of 1,002 under `util/ad-hoc/`. `PEM_BODY_RE` alone also finds 0 in both.
- **Numbers and dispositions:** the output of `util/ad-hoc/e2e_finding_triage.py` is identical on the `04db8614` and `b0eb4ac1` ledgers (70 findings, 19 open: 1 P0, 6 P1, 12 P2).
- **Order of work** (parent transcript, descriptions and timestamps only):
  - tool edits 10:22:49–57;
  - check against round 8's archiver, and round 7's check against the new tools, 10:23:12–21;
  - regeneration of rounds 8, 7 and 6, 10:23:39–56;
  - sweep 10:24:06;
  - ledger pass 10:25:01.

  So "re-derived before applying" holds. The parent's sweep ran before round 9's report existed; my sweep covers it.
- **R9-A findings 1–2 and R9-B findings 1–2 are all applied:**
  - ledger :9258-9263, :9470-9472 and :9493-9494;
  - check :20-21 and :76-80;
  - archiver :52-54, :61-65 and :124;
  - README :750-754.
- **The check comment's provenance holds:** round 6's check had no gate cases, and round 7's gate list matches the comment's account.

**WHAT YOU COULD NOT CHECK**
- Whether gitleaks in CI catches these forms.
- I did not re-run round 8's six forms end to end through `main()`. Round 8's `key_material` code is unchanged; I relied on R9-A and R9-B.
- Anything off this host, and R10-A's results.

**SECRETS/PII:** No slips.
- Fakes were built in memory by concatenation and random draws; I printed only booleans, counts, lengths and sha256 prefixes.
- No environment variables, tokens, credential files, commit headers or signature fields were printed, no REST commit objects were used, and nothing was sent anywhere.
- git was used only for `git show <rev>:<path>`, `%h %ad %s` logs, `git diff` and `git status`, and never with `git -C` on the primary checkout.
- Transcripts were read only through the archiver's own code and a descriptions-only parser.
- Neither forbidden script was run. The archiver was run only with `--out` in scratch.
- The scratch directory, with every fixture, is deleted. The worktree is clean at `b0eb4ac1`, and I changed no files there.

---
