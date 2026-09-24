<!-- Archived verbatim 2026-09-24 from subagent a833573c5bbdf2a36 of session 8f86dec2 (final message). -->

**Verdict: REFUTED.** Two HIGH findings. The fix-forward's central claim, that it "corrected all the rest" of the primer anchors, is false in three places. And a sentence it rewrote now says a failed juniper-data clone fails CI loudly, when in fact CI goes green with every sibling guard skipped. The primer's v3 has two MEDIUM errors: the toy's tests do not pin the fourth metadata route, and E.1 item 3's bold rule is broader than its argument.

**Documents cited.** Every reference below uses one of these filenames:
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, as on main (`f2688a95`; #2082/#2083 do not touch it).
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`, as on main (`f4d050c6`).
- juniper-ml `docs/REFERENCE.md` (main); juniper-data `docs/REFERENCE.md` (main `1afc3484`, or #438's head `28fced18` where stated).
- Reports in `reports/2026-09-24_defect-register-round-42/`: `ml2074-round1-laneA-reprobe.md`, `ml2074-round1-laneB-refute.md`, `primer-correction-round2-laneB-refute.md`, `data428-round3-laneB-refute.md`.
- PR bodies: `ml_register_fixforward_pr_body.md` (#2080) and `ml_primer_v3_pr_body.md` (#2075).
- Procedure: `…CONSENSUS-PROCEDURE.md` = `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

I did not open `scratchpad/r42/pr2080-laneA/`.

---

## HIGH

**H1. `…DEFECT-REGISTER.md` line 766, "its fix-forward then corrected all the rest — 43 anchors in 39 rows' `Primer` cells, … and 7 in the prose — each proven by content", and line 1781, "every anchor past it was three short until 2026-09-24", are false.** Three places, holding five citations, are still three lines short.
- **Line 527**, `APD-SVCCORE-003`'s §3 field: "`| **Primer** | III.7 — lines 7950-7951, 7962, 7964-7968`".
  - It dates from creation: it is line 221 at `adbe92b0`, and `76e4513b` only re-padded the table.
  - In today's `…PRIMER.md`, lines 7950 and 7962 are blank. The text is at 7953-7954, 7965 and 7967-7971. Those are the numbers #2080 wrote into the same entry's prose at lines 532 and 536.
  - `ml2074-round1-laneB-refute.md` finding 8 names "`7950`/`7962` (SVCCORE-003)", and 7962 appears only on line 527. The report #2080 was applying pointed at this line.
- **Line 1736** reads '"…pick one per package**" (7944)'.
  - `…PRIMER.md` line 7944 now reads "`websocket/control_stream.py:230`. A `commands` property…". The quote is at 7948-7949; the row's §4 anchor is 7947.
  - It was written on 2026-08-28 (`188117e3`), after #1098, by copying the pre-shift §4 cell.
- **Line 1737** reads "The primer states the risk precisely (8089)".
  - Line 8089 now reads "ABC's: `@runtime_checkable`…". The quoted text is at 8092.
  - It was written on 2026-08-28 (`c8b80080`).
- **Mechanism.** `util/ad-hoc/2026-09-24_register_primer_anchor_audit.py` reads only tables whose header starts `ID` and has a `Primer` column. The hand list in `util/ad-hoc/2026-09-24_register_round42_fixforward.py` (lines 152-157) contains exactly the 7 prose citations it fixed and none of these three places. So `ml_register_fixforward_pr_body.md`'s "The anchor audit on the result finds nothing left to shift" says nothing about §3 or §5.1.
- **The audit's premise is wrong.** It assumes "anchors a row gained after creation were taken against the shifted primer". Of the three §5.1 primer citations added after creation, lines 1736 and 1737 are stale. Line 1742's "8188-8195" (2026-08-30) is correct. Only reading the content tells them apart.
- **The "proof by content" is weaker than stated.** Its check (line N at `68f62f5b` equals line N+3 now) holds for every non-blank line past 5758, so it cannot tell a right anchor from a wrong one. I read all 43 table anchors and the 7 prose shifts against their rows' findings. All are correct, so the conclusion stands; the proof does not establish it.
- **Fix.**
  - Line 527 → "7953-7954, 7965, 7967-7971"; line 1736 → "(7948-7949)"; line 1737 → "(8092)". Correct the claims at lines 766 and 1781.
  - Audit every `\b\d{4}\b` in the range 5759–9866 across the whole file, and check each one by content.

**H2. `…DEFECT-REGISTER.md` line 1305 (`APD-ML-008`), "a failed juniper-data or juniper-cascor clone skips every guard the same way, since juniper-ml's notes link into both (run on its own, the test would skip only those forks' sites: `OK (skipped=3)`)", and juniper-ml `docs/REFERENCE.md` line 2972, "the cross-repo link check runs first and fails on a missing sibling", are false for juniper-data. The truth is the silent case.**
- **No link fails.** `xrepo_links.py` applies the checker's own `_LINK_PATTERN` and `CROSS_REPO_PATTERN` to all 1,187 juniper-ml markdown files outside templates, history and legacy. It finds 1 cross-repo link into canopy, 4 into cascor and **0 into juniper-data**. The positive control is the canopy link that `ml2074-round1-laneA-reprobe.md` measured failing.
- **No earlier step fails.** `docs-full-check.yml` swallows clone failures (line 110, `|| echo "WARNING…"`). Both pin-lint steps print WARN and `continue` on a missing consumer (`test_doc_tools_drift.py:260-262`, `test_ci_tools_drift.py:309-311`).
- **The drift test then passes green.** `drift_missing_sibling.py` ran `tests/test_service_fork_drift.py` from main in a minimal synthetic root:

| Missing sibling | Result |
|---|---|
| juniper-data | rc 0, `OK (skipped=3)` |
| juniper-cascor | rc 0, `OK (skipped=3)` |
| juniper-canopy | `FAILED (failures=2, skipped=2)` |

  - With data missing, `_ROOT_ANCHOR_REPOS` finds no root, so all three `ServiceForkDriftTest` tests skip. That leaves **all 16 sibling sites** unchecked (data 7, cascor 7, canopy 2). Only the 2 service-core sites run.
  - "Skip only those forks' sites" is also false: canopy's sites are skipped as well.
  - This is the silent-blind case that the test file's own comment (lines 79-86) warns about.
- **Knock-ons.**
  - The PR rejected `ml2074-round1-laneA-reprobe.md`'s nit ("the service-core sites still run") because "the sentence is about CI, where the step never runs". For juniper-data the step does run, and the nit was right.
  - `…DEFECT-REGISTER.md` line 1751, "so they cannot silently lose their markers", is false on the same path.
- **Fix.**
  - State that a missing data clone passes the link check and the drift step then skips every sibling site green, while a missing cascor or canopy clone fails first.
  - Add a remedy candidate to `APD-ML-008`: make the drift step fail when `GITHUB_ACTIONS=true` and no root is found.

## MEDIUM

**M1. `…PRIMER.md` lines 9879-9880, "II.11's tests (lines 5791, 5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent", is false for the 201 create response.** `ml_primer_v3_pr_body.md`'s "makes each `JSONResponse` revert fail" is false for the same reason.
- Line 5838 hashes `second.content` (the 200) and never the 201's own body.
- `toy_mutants.py` reverted lines 5671-5672 to the base text (`return JSONResponse(` / `dataset.metadata(),`). All 15 II.11 tests still pass (MISSED).
- The REUSE, GET and PATCH reverts are each caught by one test. A one-line own-body assertion catches the create revert.
- `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py`'s `MUTANTS` lists only GET, PATCH and POST-reuse.
- Control: 62/62 pass unmutated.
- **Fix:** on line 5838, also assert `first.headers["etag"] == '"' + hashlib.sha256(first.content).hexdigest()[:32] + '"'`, and add a CREATE mutant to the check script.

**M2. `…PRIMER.md` line 9939, "**A hash of serialized JSON is a strong validator.**", is broader than its own argument.**
- The body (9940) argues only that a hash of the **exact bytes sent** is strong.
- By E.1 item 1's own reasoning, a hash of some other serialization is weak: a serializer change alters the bytes but not the hash. That is line 4220's "usually weak" case.
- The same material holds two counterexamples:
  - the v2 toy, whose `JSONResponse` re-render #2075 fixed;
  - juniper-data's `_metadata_response` docstring, which says `json.dumps` writes `1e-07` where pydantic-core writes `1e-7`.
- **The quotation at 9942-9943 is cut mid-sentence.** "A strong validator might change for reasons other than a change to the representation data" continues in RFC 9110 §8.8.1 (checked on rfc-editor.org): "…such as when a semantically significant part of the representation metadata is changed (e.g., Content-Type), but it is in the best interests of the origin server to only change the value when it is necessary…". Field-order churn in the bytes sent *is* a change to the representation data, so the quoted clause does not cover it.
- **Fix:** "**A hash of the exact bytes sent is a strong validator**; a hash of a separate serialization is not." Complete or drop the second quotation.

## LOW

- **L1. Lock-less writers are under-counted.** `…PRIMER.md` 9973-9974 says "`PATCH /v1/datasets/batch-tags` and `DELETE` took none; juniper-data#438 makes them take it". `…DEFECT-REGISTER.md` line 1302 says "Neither of those two takes the lock".
  - On main `1afc3484`, `batch_delete` (`storage/base.py:590-615`) and `delete_expired` (`:423-431`) call `delete` unlocked too, via `POST /batch-delete` and `POST /cleanup-expired`.
  - #438's own docs (juniper-data `docs/REFERENCE.md` at `28fced18`, lines 1331-1332) name all four routes.
  - #438 is still **OPEN**, yet the primer says "makes" in the present tense.
- **L2. `…DEFECT-REGISTER.md` line 1307: "`record_access`, which every metadata read and artifact download fires".**
  - `/latest` "records no access", per juniper-data `docs/REFERENCE.md` line 1264 and `data428-round3-laneB-refute.md` line 45. List, filter and versions don't either.
  - The only call sites are `datasets.py:999`, `:1105`, `:1137` and `:1141`.
- **L3. `…PRIMER.md` 5362-5363: "Its tag PATCH … lost tags to a concurrent race until juniper-data#263 and #282".** The batch tag PATCH kept losing tags through 0.16.0 (`APD-DATA-057`: 28 of 144 kept). v3 scoped E.2 but not this docstring.
- **L4. A NaN or Infinity POST returns a text/plain 500** at v3, and also at base `dcfc024f`. That breaks the toy's own claim at 5377, "RFC 9457 problem details on every error path". `ml_primer_v3_pr_body.md` calls this "refuses `NaN` again", but it is an unhandled error. Fix: return a 422 `ProblemException`.
- **L5. `…DEFECT-REGISTER.md` line 302: "The sibling-package-drift group is CLOSED** (2026-08-21)" is false.**
  - The table's rows closed on 2026-08-24 (dclient#165, cclient#129) and 2026-08-28 (cclient#143).
  - Line 242, which #2080 edited, now says that group's last row "closed 2026-08-28".
- **L6. The blind-spot disclosure at line 180 is accurate but incomplete.**
  - Mutant M7 (`tools_mutcheck.py`) puts `**FIXED` in an open row's Source cell: `register_open_set.py` then reports 136 | 101 | 35 while the crosscheck says AGREE. `register_open_set.py` tests the whole line; the crosscheck tests only the status cell.
  - A duplicated row is invisible to both tools (M8).
- **L7. Two `ml2074-round1-laneB-refute.md` NITs (#15) were neither applied nor rejected.**
  - Line 1299, "each wire a `FailedAuthThrottle` (… `api/security.py:297`, … `src/api/security.py:256`": both lines are `class FailedAuthThrottle:`. The wiring is at data `:455` and cascor `:413`.
  - The park bullets group three, three and two rows under one sentence each, while line 1246 says "each row's park status is stated in its own row-level sentence".

## NIT

- `util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py`'s proof checks only `\n`. A bare `\r` or U+2028 in a rewrite passes with "none moved", while `splitlines()` counts 9,983 lines instead of 9,982. The shipped file is clean.
- The owner-ruling quotes at `…DEFECT-REGISTER.md` 1495-1500 are cut after two sentences with no ellipsis.
- `APD-DATA-057`'s "a batch write erased a conditional PATCH's acknowledged 200" is n=1 and doesn't say so.
- `…DEFECT-REGISTER.md` line 300, "`APD-CASCOR-005` is a seventh of the kind", is stale: `APD-ECO-008`, `-009` and `-010` are further copies of service-core code missing a guard.
- `…PRIMER.md` 3346, "a content-addressed identifier", is unmarked; E.1 item 2 says the scheme is not content-addressed.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-24_defect-register-clients-swept-46-fixed.md:119` still says "Q26 at 9463". It is an archived record.
- The status line (177) satisfies the crosscheck by leaving out ids, and says so honestly. The cost: naming an open id there makes the crosscheck report DISAGREE (mutant M5).

## Rejected findings in `ml_register_fixforward_pr_body.md`

- **B12 ("`-054` is a fifth"): rightly rejected.** The gap between the checksum and the served bytes predates #428.
- **B15 (severity scale): rightly rejected.** The round-42 handoff wrote "Sev M" and "Sev L", and L is not a register category. The S rows match precedent (`APD-DATA-001`, `-002`).
- **The A-nit on `APD-ML-008`: wrongly rejected** (see H2).

## What did not land

These were checked and held:

**Counts and tools**
- 136 / 100 / 36 rows, fixed and open; 96 / 81 / 15 primer plus 40 / 19 / 21 post-primer.
- Post-primer open history: 7 → 7 → 12 → 12 → 19 → 21.
- **TWENTY-FOUR** = 40 − 16, by filing commit: #1858 16, #1864 1, #1947 6, #2026 5, #2005 2, #2074 8, #2080 2.
- §2.3's twenty (15 + 3 + 2 distinct ids); four zero-open prefixes; each of the ten rows filed 2026-09-24 names its finder.
- The crosscheck says AGREE. Its disclosed blind spots reproduce, and exactly three ids appear twice on the status line.
- The four suites give 44 tests, `OK (skipped=3)`.

**Anchors**
- All 43 shifted anchors and the 7 prose shifts are semantically correct. The "8 on blank lines" count reproduces, and 6592 → 6596 is right.
- No anchor sits on a line #2075 changed, and no anchor cites #1098's in-place lines (3732, 5649).

**New and revised rows**
- `APD-ECO-012`:
  - Anchors are identical at `5907713b` and canopy main `14a0e4c7`, and the ordering and missing `OPTIONS` bypass are as stated.
  - It is latent: no `JUNIPER_CANOPY_CORS_ORIGINS` in any tracked juniper-deploy file, and canopy's `conf/app_config.yaml` `cors:` block is read by nothing.
  - The gate's own matcher gives canopy False, canopy with CORS moved last True, and data True.
- `APD-DATA-057`: anchors are exact, and "a third" writer holds at the route level. The v0.16.0 tag and `1afc3484` are identical in `api/` and `storage/`.
- `APD-DATA-054`, the `APD-ECO-011` rewrite, the `APD-ML-007` update (244/244 lines in order, 15 top-level bullets, `ceremony.py:462` and `:1011`) and juniper-ml `docs/REFERENCE.md`'s sentence about `release-train.yml` and `ci.yml` all hold.
- The two ruling quotes are verbatim, apart from the truncation noted above.

**Primer**
- `--base dcfc024f` rebuilds `f4d050c6` byte-for-byte. A smuggled `\n` is refused, and `-O` changes nothing.
- The 22 markers and 36 changed lines match "22 + 35 + 1". Appendix E's in-place list is complete, and the lines it names are right.
- Line 5332 is 484 characters, and nothing cites the sentence it removed.
- The examples pass 62/62 on two toolchains and at base.
- All RFC quotations are verbatim. E.1 item 2 matches `dataset_id.py`. LocalFS is the only `_meta_write_lock` override. #428 is in v0.16.0.
- My unmarked-passage sweep found 11 candidates and no false caching or tag-write claim.

## What this evidence cannot support

- H2's CI behaviour is derived from three things: the workflow YAML, a local synthetic-root run, and a static link classification. I dispatched no CI run and forced no clone to fail.
- I did not re-measure `APD-DATA-057`'s race counts or `APD-ECO-011`'s 200s. `APD-ECO-012` rests on code reading only.
- The toy ran on JuniperCanopy1 (CPython 3.13.13, FastAPI 0.137.0, Starlette 1.3.1) and JuniperData (3.14.2), not the exact Appendix D.2 pins. **/tmp is at 100% inode use** (`df -i`), so a pinned venv could not be built.
- I did not replay `util/ad-hoc/2026-09-24_register_round42_fixforward.py`, and I did not check the archived reports against transcripts.
- The anchor check is my own reading of 50 lines. The primer sweep is keyword-driven.
- #438 was still OPEN at head `28fced18` at the end of this run. If it merges, L1's present tense becomes true.

## Scripts

All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2080-laneB/`:
- anchors and citations: `anchor_semantic.py`, `prose_cites.py`, `other_doc_cites.py`, `filing_commits.py`, `postprimer_history.py`, `split_counts.py`, `idfree_counts.py`
- register tools and suites: `tools_mutcheck.py`, `run_register_suites.py`
- the drift gate: `drift_missing_sibling.py`, `xrepo_links.py`, `cors_gate_probe.py`
- the primer and toy: `toy_mutants.py`, `toy_full_control.py`, `build_mutcheck.py`, `primer_line_classify.py`, `unmarked_sweep.py`, `rfc_quotes.py`
- release notes: `notes_vs_tag.py`
- helper: `show.py`

**Changed:** nothing in any repository. I ran `git fetch` in juniper-ml, juniper-data, juniper-canopy, juniper-cascor and juniper-deploy, and created no branches, worktrees or servers. External calls were read-only: `gh`, PyPI and rfc-editor.org. A scratch venv install failed on the full inode table; I deleted the partial venv and two reproducible extractions to return about 3,800 inodes.
