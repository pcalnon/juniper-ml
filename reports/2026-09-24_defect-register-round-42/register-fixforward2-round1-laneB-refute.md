<!-- Archived verbatim 2026-09-24 from subagent a4ae44a7ce58056a9 of session 2fba4397 (final message). -->

**Verdict: REFUTED.** Most of the change holds up. The five primer citations land on the text they quote. The silent missing-juniper-data-clone path reproduces exactly. The create-route ETag pin is live. The NaN 500 is gone, and the four lock-less writers, #438, #2071 and #2059 facts all check against source. The editor replays byte-for-byte on main's files. But the correction adds two new false statements (MEDIUM). First, §2.3 now says round 42 filed `APD-ECO-008`, which three other sentences in the same register contradict. Second, Appendix E now says a non-integer `n_samples` went from a 500 to a 422, but `n_samples: 1.5` returns 201 both before and after. It also turns "four links" into "four notes". And the harness still misses a revert of half the new toy fix: the strict "never coerced" typing. None of these is HIGH. All are cheap same-line fixes.

**Documents** (line numbers are at head `e2f87aae`):
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`
- juniper-ml `docs/REFERENCE.md`
- Reports in `reports/2026-09-24_defect-register-round-42/`: `ml2080-round1-laneA-reprobe.md`, `ml2080-round1-laneB-refute.md`, `data438-round1-laneA-reprobe.md`, `primer-correction-round2-laneB-refute.md`, `owner-rulings-verbatim.md`
- The procedure named in the brief, `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, was **not** re-read. I followed the brief's rules.

## Findings

### HIGH
None.

### MEDIUM

**M1. `…DEFECT-REGISTER.md` L300, new sentence: "Round 42 filed three more, all in canopy: `APD-ECO-008` (closed 2026-09-24), `APD-ECO-009` and `APD-ECO-010`". This is false for `APD-ECO-008`.**
- **Evidence:**
  - `git log -S '| APD-ECO-008 |'`: the row was added by `836393cf`, juniper-ml#2005, 2026-09-22 ("file APD-ECO-008 and APD-DATA-053").
  - Round 42's own commit `6aabe4cc` (#2074) adds exactly eight rows: `ECO-009/-010/-011`, `DATA-054/-055/-056` and `ML-007/-008`. It only *modifies* `ECO-008`, by closing it.
  - The same register contradicts the new sentence three times:
    - L177: "round 42 filed eight rows and closed `APD-ECO-008`" (12 → 19 only works if `ECO-008` was not filed that day);
    - L181: "`APD-ECO-008` … filed 2026-09-22, closed 2026-09-24";
    - L240: "`APD-ECO-008` … a seventeenth, closed 2026-09-24; `APD-ECO-009` and `APD-ECO-010` … filed open that day".
- **Fix:** "`APD-ECO-008` (filed 2026-09-22 by juniper-ml#2005, closed 2026-09-24) is an eighth; round 42 filed two more, `APD-ECO-009` and `-010`, all three canopy's; `APD-ECO-012` …".

**M2. `…PRIMER.md` L9880 (Appendix E intro) says the second correction "restricted a create's `params` to JSON numbers, so that NaN, Infinity or a non-integer `n_samples` is a 422 problem where it had been a plain-text 500". The commit message says the same. This is false.**
- **Evidence** (`toy_attack.py` on the pinned venv, head and main):
  - `{"n_samples": 1.5}` returns **201** at both head and main, body `"n_samples":1,"params":{"n_samples":1.5},"size_bytes":1`.
  - `StrictFloat` admits 1.5, and L5659 `int(body.params.get("n_samples", 512))` silently truncates it.
  - A numeric string `"512"` or `true` was a **201** on main (not a 500) and is a 422 now.
- **Cause:** the probe's "non-integer n_samples" case (`util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py:42`) sends `"abc"`, which is non-*numeric*.
- **The same framing appears at L5502's comment**, "JSON numbers only, never coerced: anything else is a 422, not a 500". For every key except `n_samples`, "anything else" was a 201. And L5659 coerces anyway.
- **Fix:** say "a non-numeric `n_samples` (a string, null, a list)". Or make the claim true by refusing a non-integral or out-of-range `n_samples` with a `ProblemException` 422. Also reword the L5502 comment.

### LOW

**L1. `…DEFECT-REGISTER.md` L1305 (`APD-ML-008`): "since four juniper-ml notes link into cascor" is wrong. It is four *links* in *two* notes.**
- **Instrument:** `xrepo_links.py` runs the checker's own `validate_directory` in check mode, with docs-full-check's excludes and an empty ecosystem root, over 1,325 files.
- **Result:**
  - cascor: 4 links, in `notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_COMPREHENSIVE-CODE-REVIEW-PLAN.md` (×3) and `notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md` (×1);
  - canopy: 1 link, in `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md`;
  - juniper-data: 0.
- The same row's correction note, "four into cascor", has the unit right.
- **Fix:** "four links in two juniper-ml notes".

**L2. Nothing pins the strict half of the new toy fix.**
- **Evidence:** reverting L5502 to lax `dict[str, int | float]`, with `allow_inf_nan=False` kept:
  - Appendix D harness: "All primer examples passed." (MISSED);
  - `2026-09-24_primer_toy_error_paths_probe.py`: "every client-input error is a 422 problem" (MISSED);
  - `lax_mutant_behaviour.py`: `"512"` → 201 with the same id as `512`, and `true` → 201 with the same id as `1`.
- That coercion is exactly what the L5502 comment ("never coerced") and the editor's rationale comment exist to prevent.
- `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py`'s docstring (L26-29) credits its "NaN schema" mutant with pinning "params restricted to JSON numbers". It pins only the NaN refusal.
- The same class of gap as #2075's M1 (a revert the harness misses) recurs here.
- **Fix:** a same-line numeric-string/`true` arm in the validation-shape test (L6119-6120), plus a "lax union" mutant.

**L3. The toy docstring (`…PRIMER.md` L5377-5378) still overclaims "RFC 9457 problem details on every error path".**
- The new parenthetical carves out only "an exception nothing anticipated". FastAPI's own `HTTPException`s still render `{"detail": …}` as `application/json` (head and main):
  - `GET /v1/nope` → 404;
  - `DELETE /v1/datasets/x` → 405;
  - a POST body with a 5,000-digit integer → 400 "There was an error parsing the body".
- `ProblemException`'s docstring (L5433-5434), "including the ones FastAPI generates on your behalf", is false for the same responses.
- **Fix:** register a Starlette `HTTPException` handler that renders problem+json, or extend the parenthetical.

**L4. The params restriction is an undeclared divergence from the real service.**
- On main, these were **201**; at head they are 422:
  - `noise: "0.1"`;
  - `seed: null`;
  - a nested object;
  - a string param.
- `seed: null` is the input E.1 item 2 describes as meaningful in real juniper-data (a per-call nonce).
- L5346 still says "One deliberate divergence from the real service". L5481 still calls the id "the real juniper-data scheme".
- **Fix:** name the second divergence at L5346, or restrict only `n_samples`.

**L5. E.1 item 3 (`…PRIMER.md` L9942-9944) understates the cost of an unstable serialization.** It says instability "only makes it change more often than the data does, which costs revalidations but never serves stale bytes".
- For the `If-Match` flow II.11 teaches, a tag that differs between serializations of unchanged data fails a conditional PATCH with a spurious 412. One example is set order under per-process hash randomization. `If-Range` resumption restarts the same way.
- RFC 9110 §8.8.1 lists strong validators as usable for "partial content ranges, and 'lost update' avoidance", not just cache revalidation.
- **Fix:** "…costs revalidations, and spurious 412s on conditional writes, but never serves stale bytes."

**L6. The new silent-path defect sits in a row parked on an unrelated question.**
- `…DEFECT-REGISTER.md` L1629-1631 parks `APD-ML-008` "awaiting an owner ruling, do not action". It says `-008` "asks whether the drift gate should test behaviour rather than text".
- The silent-path remedy (L1305: a step-scoped variable that fails on a missing root) needs no such ruling. A session honouring the park will never action it.
- **Fix:** amend L1629-1631 to say the silent-path remedy is actionable, or file it as its own row.

**L7. Client-input 500s remain beyond the declared `10**30`** (text/plain 500 at head and main):
- `n_samples: 1e300`, a finite float the new "JSON numbers only" schema admits;
- a cursor that decodes to JSON nested 10,000 deep. `RecursionError` is not in `decode_cursor`'s except tuple.
- **Fix:** bound `n_samples`, which also prevents huge allocations, and catch `RecursionError` in `decode_cursor`.

### NIT
- **N1.** `…DEFECT-REGISTER.md` L766: "that check holds for every non-blank line past 5758" is false for 10 lines. At head these are 5773, 5774, 5786, 5787, 5838, 5857, 5901, 5945, 6120 and 9510, all rewritten in place since (`shift_check.py`). The conclusion still stands.
- **N2.** L766 and the commit message mix units:
  - "82" counts range ends: 82 numbers, but 69 citations with ranges counted once (`citation_units_and_pipes.py`);
  - "7 in the prose" and "the last 5" count citations;
  - "43 anchors" counts ends.
  - The census also prints "82 citation(s)".
- **N3.** `util/ad-hoc/2026-09-24_register_primer_citation_census.py` has three small defects:
  - it labels §5.1 rows "S4-cell" (L72);
  - it prints "primer has 9983 lines" for a 9,982-line file (L61-62, `split("\n")`);
  - its regex (L45) cannot see `…PRIMER.md:NNNN`, `LNNNN` or `9,466`-style citations. None exist in the register today, so nothing is missed now.
- **N4.** `…PRIMER.md` L9876-9879, "Three other lines were corrected in place": L4224's new "(Emphasis added.)" is a fourth, and it is not listed.
- **N5.** `util/ad-hoc/2026-09-24_register_round42_second_fixforward.py:391` embeds raw U+2028 and U+2029 in `LINE_BREAKERS`. Its own source is 453 lines to `split("\n")` and 454 to `splitlines()`, the very discrepancy it refuses in the primer. Use `"\u2028\u2029"`. L56-59 also has an f-string with no placeholders (F541).
- **N6.** The probe's RESULT line, "every client-input error is a 422 problem" (L93), is true of its 7 cases only.
- **N7.** `APD-DATA-057` (L1307) still reads "#438, open when this was filed" with no merge noted, although `APD-DATA-055` and the park bullet were updated. Its "once, n=1" also omits that `data438-round1-laneA-reprobe.md` claim 1a re-ran the same demo and saw 2 of 3 conditional 200s erased.
- **N8.** (Not introduced by this change.) L229, "9,866 since juniper-ml#1098": the primer has been 9,982 lines since #2075.
- **N9.** `util/ad-hoc/2026-09-24_archive_round42_reports.py`: a report header naming a session missing from `SESSION_IDS` raises a bare `KeyError` in `subagents_dir`, where a clear `SystemExit` would match its style.

## Omissions assessed
- **N1 (`APD-CASCOR-013` Source cell) — holds.**
  - cascor at `7f4a7213` (#688) has four `_dataset_shortfall` writes (2560, 2623, 4104, 4947); `ec8b5bdb` has three.
  - Caveat: #688 merged 18:56Z, 37 minutes before this commit, so the row's "open until the fix-forward … lands" is now met but unrecorded. This change recorded #438's merge in two rows and not #688's.
- **The `2026-09-24_primer_correct_artifact_validator.py` "\n"-only proof — holds.** It is a retained record. The new editor does refuse every `splitlines()` breaker in new lines, and I verified that by replay. The irony is N5.
- **The handoff's "Q26 at 9463" — holds.** It is an archived record.
- **The status-line constraint — holds.** L177 states it honestly.
- **N6 → PR body — unverifiable.** No PR exists yet. The commit message, which is the default squash body, does not mention it.
- **The huge-`n_samples` 500 — holds only partly.**
  - It is disclosed only generically.
  - The same 500 is reachable with `1e300`, which the new schema admits (L7).
  - The new L5502 comment and L9880 read as though the params 500 class were closed.
  - A one-line bound would close it.
- **Lane B's remedy not adopted as written — holds.** Only `ci.yml:500` and `docs-full-check.yml:259` run the test, and every Actions job sets `GITHUB_ACTIONS`. A test-level `GITHUB_ACTIONS` gate would therefore fail every `ci.yml` run. A variable set in the drift step only would catch the silent path and affect no other job. It is still a design, not implemented.

## What did not land
- **Editor replay.** On main's three files the output is byte-identical to head. A second run gives "FAIL: this second fix-forward has already run".
- **Primer shape and citations.**
  - 21 lines rewritten in place; 9,982 lines before and after.
  - The register cites no rewritten line.
  - All 82 census entries past 5758 land on the text their sentence quotes, including 7953-7954/7965/7967-7971, 7947 and 8092. None is blank.
- **Primer history.** `68f62f5b` collapsed four lines into one at 5758, and #1098 restored them. #1098 is the only commit to move a primer line.
- **Toy instruments.**
  - Harness 62/62.
  - Mutation check 6/6 CAUGHT, control PASS.
  - Probe 7/7 REFUSED at head, 7/7 ESCAPED on main.
  - My own mutants were all CAUGHT by the harness: `allow_inf_nan` dropped alone; `Any` with `allow_inf_nan` kept; the echo reverted alone; the create route serialized with `json.dumps`. The probe also caught the first three.
  - A NaN echoes as `"input": "NaN"`. NaN in tags, generator, version or an extra key is now a 422 (a 500 on main).
- **H2, the silent path — exact.**
  - The juniper-data link count is 0.
  - Synthetic roots under `GITHUB_ACTIONS=true`: data missing → `OK (skipped=3)`; cascor missing → `OK (skipped=3)`; canopy missing → `FAILED (failures=2, skipped=2)`; none missing → `OK`.
  - There are 16 sibling sites (data 7, cascor 7, canopy 2).
  - The intervening steps warn and continue. The later steps skip missing repos. Recent Docs Full Check runs are green.
  - `docs-full-check.yml:110` and `ci.yml:500` are cited correctly.
- **juniper-data facts.**
  - At `1afc3484`: `base.py:590-615` and `:423-431`; the `batch-delete` and `cleanup-expired` routes; `record_access` at 999/1105/1137/1141, and none on `/latest`, list, filter or versions.
  - #438 merged 18:52Z, after v0.16.0 (published 08:52:14Z). It routes all four writers through `delete_under_lock` / `update_tags`. `save_versioned` takes no per-dataset lock at `0f0f7e0e`.
- **Release timing.** #2071 merged 08:51:22Z, 52 seconds before the cut. v0.16.0's `target_commitish` is a SHA; for 0.14.0 and 0.15.0 it is `main`.
- **Other dates.** #2059 merged 2026-09-23 22:57Z. cclient#143 merged 2026-08-28.
- **`APD-ECO-010` wiring.** The ranges are exact in all three copies, and the class lines are right.
- **Owner-ruling quotes.** Each is the opening of its description in `owner-rulings-verbatim.md`.
- **Lane A's `claim 17` case B.** It uses the conditional (`precondition`) path.
- **RFC 9110 §8.8.1.** I fetched it (sha256 `21c1cdce…7232a`). The L4222-4224 quote is verbatim, "(Emphasis added.)" is right, and item 3's rule matches the definition.
- **Register tools and CI screens.**
  - `register_open_set.py`: 136 | 100 | 36. The crosscheck says AGREE. `test_register_close_protocol.py` and `test_register_open_set.py` give 12 OK.
  - Pipe counts are unchanged on every edited line.
  - The markdown structure screen gives 0 → 0 for all three files.
  - The symbol-loss screen reports `SESSIONS` LOST and waived by the trailer. The docs-additions screen is OK.
- **Archiver `--check`.** rc 0, and every archived body equals its agent's last message.

## What this evidence cannot support
- **The silent path in live CI.** No CI run was dispatched with a forced clone failure. The green-job claim rests on:
  - reading the YAML;
  - the synthetic-root runs;
  - recent runs being green;
  - the checker's own link classification.
- **The transcript-move mechanism.** The explanation for why 8f86dec2's transcripts moved is the author's. I saw only where they are now.
- **The toy under a real server.** The toy was driven in-process with ASGITransport. On uvicorn with h11, the ~26.7 KB nested cursor URL would be refused (400) before it reaches the app. Under httptools it might not be.
- **Memory-exhausting `n_samples`.** I deliberately did not send values between 1e9 and 1e17.
- **The signature.** The local signature check shows `E` (no key). I did not verify GitHub's signature.

## Scripts
All in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b/laneB/`:
- **Diffs and counts:** `linediff.py`, `ctx.py`, `shift_check.py`, `citation_units_and_pipes.py`, `breakers.py`, `md_structure_delta.py`
- **The toy:** `toy_attack.py`, `run_toy_attack.sh`, `extra_mutants.py`, `run_mutants.sh`, `lax_mutant_behaviour.py`, `run_harness_and_probe.sh`
- **The drift gate:** `drift_roots.sh`, `xrepo_links.py`
- **Replay and screens:** `replay_editor.sh`, `run_screens.sh`
- **Outputs kept:** `census_head.txt`, `census_main.txt`, `reg_diff.txt`, `primer_diff.txt`

The extracted trees were deleted. I also removed two `/tmp/tmp*` directories that my own script had left.

**Changed:** no repository file. I ran only `git fetch` of the branch, read-only git commands and read-only `gh api` GETs. The session worktree shows a modified `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` and an untracked `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`. Neither was made by this lane.
