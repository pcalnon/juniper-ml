<!-- Archived verbatim 2026-09-24 from subagent aee68ba42bd222c6e of session 2fba4397 (final message). -->

I have enough to write the report. One note first: a `/tmp/tmpdcuq9r3c` directory holding juniper-data store files, created at 15:38, is not mine (I never ran juniper-data), so I left it alone.

# Lane B, round 2 (adversarial refutation): correction `990ef3f9` on top of `e2f87aae`

## Verdict: REFUTED

There is no HIGH finding. There is one MEDIUM, six LOW and eleven NIT findings.

**What holds.** Almost everything the delta changed in the register reproduces from primary sources:
- **Filing and PR facts:** APD-ECO-008's filing by juniper-ml#2005; #2059's merge date; every cascor #678/#688/#690 fact; the `_dataset_shortfall` writers at `ec8b5bdb`; data#438's merge after the v0.16.0 cut.
- **The counts:** the §4 note's figures, now in one unit.
- **Wording fixes:** the park block's header and ids; "two notes, four links".
- **The tools:** every result the commit message states.

**What fails.** The correction's own new sentences about the II.11 toy's input handling are still not exact:
- A lone-surrogate string, which is valid JSON, falsifies the new 9880, 5346, 5377-5378 and 5433-5434 claims. The branch also turned one such input from a 201 on main into a plain-text 500.
- "A huge value is a plain-text 500" is false for values the process can allocate.
- The delta rewrote primer line 4199 in place, against Appendix E's own policy, and did not count it among the in-place corrections.
- Stated omission 2's reason does not hold: a same-line deep-cursor arm exists.

**Documents.** Line numbers are at head `990ef3f9` unless a commit is named.
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`
- Round-1 reports: `register-fixforward2-round1-laneA-reprobe.md` and `register-fixforward2-round1-laneB-refute.md`. Also cited: `data438-round1-laneA-reprobe.md`. All three are in `reports/2026-09-24_defect-register-round-42/`.
- RFC 9110: `rfc9110.txt` from rfc-editor.org, sha256 prefix `21c1cdce6ab0e550`.

## Findings

### HIGH
None.

### MEDIUM

**M1. A lone surrogate falsifies the delta's new input-handling claims, and the branch turned a 201 into a plain-text 500.**

Four places make the claim:
- **…PRIMER.md:9880:** "an `n_samples` that `int()` rejects, is a 422 problem where it had been a plain-text 500".
- **…PRIMER.md:5346:** "a string, a boolean, a null or a nested value is a 422 here".
- **…PRIMER.md:5377-5378:** "RFC 9457 problem details on … FastAPI's validation errors".
- **…PRIMER.md:5433-5434:** "keeps every error path it covers the same shape, including the validation errors FastAPI generates".

Measured in-process on the pinned venv, at main `df21367d`, at `e2f87aae` and at head (`b07_toy_boundaries.py`, run by `b08_run_boundaries.sh`):

| Body | main | `e2f87aae` | head |
|---|---|---|---|
| `"n_samples": "\ud800"` (`int()` rejects it) | 500 text/plain | 500 text/plain | **500 text/plain** |
| `"params": {"s": "\ud800"}` | **201** | 500 text/plain | **500 text/plain** |
| `"generator": "\ud800"`, or an extra key `"x\ud800"` | 500 | 500 | 500 |

- **Mechanism** (`b09_surrogate_mechanism.py`): `UnicodeEncodeError: … surrogates not allowed`, raised in Starlette's `JSONResponse.render` and called from `ProblemException.to_response` (…PRIMER.md:5464).
  - The 422 handler's `json.dumps(…, default=str)` escapes the surrogate, and `json.loads` restores it.
  - `JSONResponse` then renders with `ensure_ascii=False`.
- **For fairness:** on main, that string param was accepted and then made every list page a 500 (`b08`'s `cursor valid` row, main column). At head the POST itself is the 500. Neither answer is problem+json.
- **Why MEDIUM:**
  - It is the same sentence and the same defect class as round 1's MEDIUMs (lane A M1, lane B M2), in text the commit message says "now says exactly that".
  - The branch introduced a client-input 500, the very class its toy change exists to remove.
  - The probe's 13 cases never try it.
- **Fix, on the same lines:**
  - 5464: `return Response(json.dumps(body, allow_nan=False), status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)`, which uses the default `ensure_ascii=True`.
  - 5455: `-> Response`.
  - Verified in `b09`: all three cases become 422 problem+json, echoing `\ud800`.
  - Add a lone-surrogate case to the probe.

### LOW

**L1. "A huge value is a plain-text 500" (…PRIMER.md:9880, :5378) is false for allocatable values.**
- `n_samples: 100000000` gives **201** with a 100 MB artifact at all three revisions. 1e17, 1e19, 1e300 and 10^30 give 500. Measured by `b07`/`b08` under RLIMIT_AS = 2 GiB.
- An unchecked `n_samples` is therefore an unbounded allocation. Only values beyond the allocator's reach are a 500. The probe samples 1e19 only.
- Separately, 9880's "as lines 5377-5378 now say" also covers "a fraction is truncated", which 5377-5378 do not say.
- **Fix:** bound `n_samples` on the formerly blank line 5658. `b27_same_count_nsamples_bound.py` shows this keeps 9,982 lines, passes the harness, and makes 1.5, 1e8 and 1e19 422 problems. Nothing cites line 5658. Or reword: "a value too large to allocate is a plain-text 500; a large one that fits is accepted and held in memory".

**L2. Line 4199 was rewritten in place against Appendix E's policy, and the new count "a fourth line corrected in place" (9880) is one short.**
- 4199 sits in the passage 4195-4200, which ends in `[Corrected: E.2]`. The Appendix E intro (9870-9874) says such claims "are corrected here rather than rewritten in place" and that each passage "keeps its text".
- The delta inserted text into 4199: " single-dataset" and "; the list, filter, `/latest` and versions reads fire none" (`b26_show_lines.py`).
- E.2 never mentions the correction, and the intro's enumeration (3639, 4222, 5332, then 4224) omits 4199. `b25_branch_primer_lines.py` confirms 1954 and 3346 are link-only additions, which the policy allows, and that 5346 is named.
- **Fix (same line 9880):** "…and marked line 4224's bold as added emphasis and narrowed line 4199's `record_access` scope, a fourth and a fifth line corrected in place."

**L3. II.11's prose intro still claims `application/problem+json` "for every error" (…PRIMER.md:5330).**
- This is the claim the delta scoped at 5377-5378 and 5433-5434.
- The toy returns `{"detail"}` JSON for 404, 405 and the body-parse 400, and text/plain for 500s.
- The test module's heading at 6091, "One error model everywhere", repeats it.
- **Fix:** scope both on the same lines.

**L4. Stated omission 2's reason fails: the primer's own suite can pin the `RecursionError` catch without moving a line.**
- `b15_same_line_deep_cursor_arm.py` rewrites 6084 so it also fetches a 10,000-deep cursor, and 6086 to `assert response.status_code == 400 == deep.status_code`.
- The line count stays 9,982. The harness passes at head and fails with 5600 reverted (1 failed, 61 passed).
- This is the same technique the delta used at 6117/6120.

**L5. `true` and `null` are pinned only by the external probe.**
- The 5502 comment says `"512" or true is a 422`, and 5346 says "a null … is a 422".
- The harness arm tests `"512"` only. In `b14_own_mutants.py`, the "admit bool" mutant (`StrictInt | StrictFloat | bool`) and the "admit None" mutant each pass both the harness and the mutation check; only the probe notices.
- This is round-1 lane B L2's class, half fixed.
- **Fix:** add `bad_bool`/`bad_null` arms on line 6117 and to 6120's loop.

**L6. The register contradicts the §1 rule that stated omissions 3 and 4 rely on.** This is pre-existing, from juniper-ml#2080 (`f2688a95`).
- …DEFECT-REGISTER.md:1635 says "`APD-DATA-057` — filed 2026-09-24; actionable, needs no ruling."
- §1 (L127, L143) says rows become actionable only by owner ruling. L1320-1326 records exactly this wording ("no owner ruling is needed … so a session may action them") as struck.
- The correction applied §1 to APD-ML-008's silent-path remedy, but not to DATA-057's structurally similar one.
- **Fix:** cite a ruling for DATA-057, or park it, or state the exception in §1.

### NIT

- **N1. The new editor repeats round-1 lane B's N5.** `util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py:260` embeds raw U+2028 and U+2029, so the file is 321 lines by `split("\n")` and 322 by `splitlines()` (`b01_breakers_in_tools.py`). The commit fixed the first editor only. Fix: write `"\u2028\u2029"`.
- **N2. The archiver fix is narrow.** The unknown-session refusal works: "session deadbeef: not in SESSION_IDS…", rc 1. The sibling case, a known session naming an agent with no transcript, still dies with a bare `FileNotFoundError` traceback (`b13_archiver.sh`).
- **N3. The "lax union" mutant is not a revert.** Line 5502 never read `dict[str, int | float]`: it was `dict[str, Any]` on main and `StrictInt | StrictFloat` since `e2f87aae`. The `MUTANTS` comment in `2026-09-24_primer_toy_pin_mutation_check.py` ("the text that line held before the fix it pins") and the commit's "7 of 7 reverts" miscount it. The mutant is the right test; only the label is wrong.
- **N4. The probe checks less than it claims.**
  - Its fraction case asserts only 201. `round()` in place of `int()` passes all three instruments (`b14`), although 9880 says "truncated".
  - Its comment says the deep cursor "must be BALANCED". On 3.13.13, an unbalanced 10,000-deep array also raises `RecursionError`; only at 9,000 deep and below does an unbalanced one fail as a `JSONDecodeError` (`b22_json_depth.py`).
- **N5. "Past the recursion limit" names the wrong limit** (9880, and the 5600 comment). The threshold is CPython's C limit, between 9,000 and 10,000 deep. `sys.getrecursionlimit()` is 1,000, and a 2,000-deep cursor parses (`b22`).
- **N6. 9880 lost its code-line anchors.** It drops the ones `e2f87aae`'s version carried (5400, 5498, 5502, 5631, 6119, 6120) and names none of the toy lines the correction changed (5433-5434, 5502, 6117, 6120) (`b25`).
- **N7. E.1 item 3 (9943-9944) is right under §13.1.1 but incomplete under §13.1.2.**
  - Under §13.1.1 (`rfc9110.txt` 5831-5834), a false If-Match condition MUST NOT perform the method and MAY answer 412, so "spurious 412s" is right.
  - Under §13.1.2 (5928-5932), an unstable tag on an unsafe method with `If-None-Match: <tag>` makes the condition true, so the write proceeds where a 412 was due. E.2 (9970-9971) says juniper-data's PATCH evaluates If-None-Match.
  - "Costs revalidations" also names the wrong cost: under `no-cache` revalidation happens anyway, and what is lost is the 304.
- **N8.** The §4 note's "69" counts the dead anchor `6592` at L766, which the same note says was replaced.
- **N9. The APD-CASCOR-013 Source cell pins pre-#688 lines**, although the §4 note (L766) says `Source` gives the current `file:line`. The current writers are at `7f4a7213`: `_bind_start_tensors_locked` :2560, `_rebind_dataset_record_locked` :2623, `_rollback_pre_swap_state` :4104 and `_reload_dataset` :4947 (`b05_cascor_writers.py`).
- **N10.** …DEFECT-REGISTER.md:1430 still states ML-002 to ML-006's present status by range ("`APD-ML-002` … `APD-ML-006` … and still do"), so `grep -n 'APD-ML-004'` cannot reach it. This is the same shape L1312 fixed.
- **N11. Pre-existing:** one POST with a lone-surrogate tag gives 201. After that, `GET /v1/datasets` is a plain-text 500 for every caller (`b09` part 2). 5378's general "unhandled exception" clause covers this, but its only example (a huge `n_samples`) does not.

## Round-1 findings: disposition

Lane A (`register-fixforward2-round1-laneA-reprobe.md`):

| Finding | Disposition |
|---|---|
| M1 | Rewritten, still false (M1 and L1 above). |
| L1 | Fixed. |
| L2 | Fixed. |
| L3 | Fixed in text; the 4199 edit created L2. |
| L4 | Fixed; the same shape survives at L1430 (N10). |
| L5 | Fixed; the cell pins pre-#688 lines (N9). |
| N1 | Fixed for 4224; 4199 unlisted (L2). |
| N2 | Fixed for If-Match; residue in N7. |
| N3 | Fixed. |
| N4 | Not applied; lane A itself called it defensible. |
| N5 | Fixed. |
| N6 | Fixed. |
| N7 | Fixed. |

Lane B (`register-fixforward2-round1-laneB-refute.md`):

| Finding | Disposition |
|---|---|
| M1 | Fixed. |
| M2 | The 5502 comment is fixed; 9880 is still false (M1 and L1 above). |
| L1 | Fixed. |
| L2 | Partly: `"512"` is pinned by the harness, but `true` and `null` only by the probe (L5). |
| L3 | Partly: still false for lone-surrogate validation errors (M1), and 5330 is untouched (L3). |
| L4 | Fixed at 5346. The 5481 "real juniper-data scheme" docstring is defensible: juniper-data's `dataset_id.py:61` builds `{generator}-{version}-{hash16}`, and the nonce difference is now declared. |
| L5 | Fixed; residue in N7. |
| L6 | Park bullet amended (see omission 3). |
| L7 | The deep cursor is fixed; `n_samples` is not (see omission 1). |
| N1 | Fixed. |
| N2 | Fixed. |
| N3 | Fixed. |
| N4 | Fixed for 4224; 4199 unlisted (L2). |
| N5 | Fixed in the first editor; recurs in the new one (N1). |
| N6 | Fixed. |
| N7 | Fixed. |
| N8 | Fixed. |
| N9 | Fixed for an unknown session; the sibling case remains (N2). |

## Omissions assessed

1. **`n_samples` limits "documented, not fixed": does not hold as stated.** The documentation is wrong for "huge" (L1) and is missing the fraction case at 5377-5378. A fix that moves no line exists (`b27`).
2. **Deep cursor pinned only by the probe, "because adding one would move lines": the reason is refuted** (L4, `b15`).
3. **Lane B L6 answered by amending the park bullet: holds as a disposition.** Partial rulings within one row have precedent: APD-CASCOR-013 carries three, at …DEFECT-REGISTER.md:1473-1504. But the amendment leaves the remedy unreachable without a ruling, and see L6.
4. **§1 left as it stands: holds only if L1635 is also brought under it.** As the branch stands, the two contradict each other (L6).

## What I tried to refute and could not

**Primer shape.**
- 13 primer lines changed in place; 9,982 lines before and after.
- The register cites none of the 13 rewritten lines.

**Register facts** (via GitHub API reads).

| Claim | What I found |
|---|---|
| ECO-008 filed by #2005 | #2005 merged 2026-09-22T10:38:38Z; its commit `836393cf` added the row |
| ECO-008 closed by #2074 | #2074 merged 2026-09-24T09:57:40Z |
| #2059's merge date | 2026-09-23T22:57:09Z |
| Appendix E appended by #2075 | #2075 is `f4d050c6` |
| APD-CASCOR-013's fix-forward | #678 merged 2026-09-23 (`0e016a7c`); #688 merged 2026-09-24T18:56:25Z (`7f4a7213`); #690 is open, created 20:15:48Z, titled "#688's validation" |
| The writers at `ec8b5bdb` (`b05`) | Exact: :2572, :3924, :4691 |
| "Only `_reload_dataset` before #678" | Exact |
| "Four since #688" | Exact |
| #688 applies the mixed-provenance ruling, `current_dataset` included (`b28_cascor688_ruling.py`) | Its body and diff do |
| data#438 merged after the v0.16.0 cut | Merged 18:52:00Z; the Release was published 08:52:14Z |
| Claim 1a of `data438-round1-laneA-reprobe.md` | Says "2 of 3 conditional 200s erased" |

**The §4 note's counts** (`b17_recount_s4_note.py`):
- #2080: 42 citations (43 numbers) in 39 rows, 8 of them on blank lines, plus 7 prose citations.
- `e2f87aae`: the last 5 citations (7 numbers); the §3 three include two on blank lines.

**Census** (`b03_independent_census.py`): 69 citations, 82 numbers. The only numbers it excludes are the 13 RFC numbers. There are no L-, `:`- or en-dash-shaped citations, and every section label is correct.

**`record_access` scope** (`b11_record_access_routes.py`): at v0.11.0 only :672 and :698 call it. Preview, stats, list, filter, versions and `/latest` never do. The claims at 4199, L512 and L1699 hold for their eras.

**5346's `seed: null`** (`b10_data_seed_null.py`): juniper-data `0f0f7e0e` `dataset_id.py:54-55` mixes in a nonce, and spiral, checkerboard and moon accept `seed: None`.

**5600:** 10,000- and 20,000-deep cursors give 400. Twelve other cursor shapes give none a 500.

**The 404/405/400 carve-outs** at 5377-5378 and 5433-5434: exactly as measured.

**Cross-repo links:** four into cascor in two notes, one into canopy, none into juniper-data (`b24_xrepo_links.sh`, plus a direct read of the fourth link's line).

**Tools, all as stated.**
- Harness: 62/62.
- Probe: 13/13 at head, 1/13 differing at `e2f87aae`, 11/13 differing on main.
- Mutation check: 7/7 caught, control passes.
- Archiver `--check`: 32 OK, 0 DIFFER, 5 skipped.
- Register tools: `136 rows | 100 fixed | 36 open`; the crosscheck says AGREE.
- Suites: 44 tests, `OK (skipped=3)`.
- The editor refuses a second run.
- The `Allow-Symbol-Loss` trailer sits in the last paragraph of both commit bodies.

**Reverts:** no revert of the delta's toy lines escapes both the probe and the mutation check (`b14`).

## What this evidence cannot support

- **The toy under a real server.** Every toy result is in-process (httpx `ASGITransport`, `raise_app_exceptions=False`) under a 2 GiB address-space cap. I ran no uvicorn. A lone-surrogate escape is plain ASCII in the body, so a real server should deliver it, but I did not test that.
- **Memory exhaustion.** I did not test `n_samples` values between about 1e8 and the allocator's limit without the cap; host swap was 19 of 20 GB used. Whether a 1e10 request returns 201 or is killed by the OOM killer is inference.
- **Python 3.14.** Not tested; the venv is 3.13.13.
- **CI.** I dispatched no workflow and re-ran none of the per-PR screens.
- **Sibling repos.** Facts about them come from GitHub reads at the named SHAs. I ran no race and no service.
- **The other lane's output.** Not seen.

## Scripts

All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneB/`, along with the outputs `census_head.txt`, `boundaries_*.json`, `archiver_check.txt` and `rfc9110.txt`. The extracted trees are deleted.
- **Extraction:** `extract.sh`, `b06_extract_main.sh`, `b16_extract_history.sh`.
- **Stated results:** `b02_run_stated_instruments.sh`, `b20_register_suites.sh`, `b21_open_set.sh`, `b13_archiver.sh`.
- **The toy:** `b07_toy_boundaries.py`, `b08_run_boundaries.sh`, `b09_surrogate_mechanism.py`, `b09_run.sh`, `b14_own_mutants.py`, `b15_same_line_deep_cursor_arm.py`, `b22_json_depth.py`, `b27_same_count_nsamples_bound.py`.
- **Text and citations:** `b01_breakers_in_tools.py`, `b03_independent_census.py`, `b12_line_lengths.py`, `b17_recount_s4_note.py`, `b18_fstring_scan.py`, `b24_xrepo_links.sh`, `b25_branch_primer_lines.py`, `b26_show_lines.py`.
- **GitHub reads:** `b04_pr_facts.sh`, `b05_cascor_writers.py`, `b10_data_seed_null.py`, `b11_record_access_routes.py`, `b19_data_id_scheme.py`, `b23_sessions_waiver.sh`, `b28_cascor688_ruling.py`.

**Changed:** no repository file. I ran `git fetch` of the branch, read-only git commands, and `gh api` and curl GETs. Everything I wrote is in the scratch directory above.
