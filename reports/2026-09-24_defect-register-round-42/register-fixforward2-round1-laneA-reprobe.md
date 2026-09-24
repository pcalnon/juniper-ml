<!-- Archived verbatim 2026-09-24 from subagent a0511a4be64379a82 of session 2fba4397 (final message). -->

**Verdict: PARTLY REFUTED. There is no HIGH finding. There is one MEDIUM, five LOW and seven NIT findings.**

Most of what the change claims reproduces from primary sources:
- The five moved citations now land on the text their sentences quote.
- My own unrestricted census of the register finds 82 primer citations past line 5758 at the head. I read every one, and every one is right.
- The primer changes on exactly 21 lines, in place.
- The silent missing-juniper-data-clone path in `docs-full-check.yml` is real, and I measured it end to end.
- The four lock-less writers and `record_access`'s real call sites are correct.
- The new ETag pin and NaN arm are what catch their reverts.
- Replaying the editor on the base gives the head byte for byte, and every repo tool reproduces its stated output.

What fails:
- **MEDIUM:** a claim the change added to the primer's Appendix E intro about the toy's input handling is false, by direct test.
- **LOW:** the change introduced one misattributed filing and one unit miscount, and it applied three corrections in one place while the same false or unapplied text stands elsewhere.

**Documents.** Line numbers are at the head `e2f87aae` unless a commit is named.
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`
- `docs/REFERENCE.md` is juniper-ml's.
- The specification is `ml2080-round1-laneA-reprobe.md` and `ml2080-round1-laneB-refute.md`.
- Also cited: `owner-rulings-verbatim.md`, `primer-correction-round2-laneB-refute.md` and `data438-round1-laneA-reprobe.md`.
- All reports are in `reports/2026-09-24_defect-register-round-42/`.

## Claims table

| # | Claim (where) | What I measured | Result |
|---|---|---|---|
| 1 | L527 §3 field `7953-7954, 7965, 7967-7971` | 7953 "The most interesting trade…"; 7965 "instead: eleven distinct names…"; 7967-7971 "The benefit is genuine decoupling… forever, silently." | REPRODUCED |
| 2 | L1736 "(7947)" | 7947 starts the sentence ("must. The two Protocols use different member conventions…"). The quoted words are on 7948-7949. The row's §4 cell (L967) is also `7947`. | REPRODUCED (NIT N4) |
| 3 | L1737 "(8092)" | 8092 starts "**Composition-only — risks.** Publishing a concrete default…"; the quote runs 8093-8096 | REPRODUCED |
| 4 | No other wrong citation past 5758 | My own census: every 4-digit number from 5759 to 9983, whatever precedes it. That gives 95 = 82 + 13 RFC numbers. All 82 read against their rows and sentences: all correct, 0 on a blank line. No `L7950`, `…PRIMER.md:NNNN` or `#L` shapes exist. | REPRODUCED |
| 5 | The census script sees every shape | It excludes `L`-, `:`-, `#`- and `/`-prefixed numbers; none exist today. It counts range ends separately, and `last = 9983` is off by one. | No defect today (NIT N6) |
| 6 | §4 note (L766): #1098 restored a 4-line block that `68f62f5b` collapsed; the only commit to move a line; #2075 moved none | difflib over all 5 primer revisions: `8d3d4573→68f62f5b` 4 lines → 1 at 5758; `68f62f5b→f7b89745` 1 → 4; `f7b89745→f4d050c6` only appends 116 lines; `f4d050c6→e2f87aae` 0 size-changing edits | REPRODUCED |
| 7 | L766 counts: 43 / 39 rows / 7 / last 5 / "three, two on blank lines" / 82 | My recount of #2080: 39 rows, 42 citations, 43 numbers. The last 5 are 5 citations (7 numbers); 7950 and 7962 were blank at base. 82 counts numbers, which is 69 citations. | REPRODUCED, units mixed (NIT N3) |
| 8 | §6 L1781: two §5.1 citations copied 2026-08-28 from creation-era cells; `8188-8195` written 2026-08-30 and right | "(7944)" entered in `655c5909` and "(8089)" in `c8b80080`, both 2026-08-28, equal to the §4 cells then. `8188-8195` entered in `2ffbe7c4` on 2026-08-30. It is one blank-bounded paragraph at `f7b89745` and identical at the head. | REPRODUCED |
| 9 | ML-008: `docs-full-check.yml:110` swallows a failed clone | `git clone … \|\| echo "WARNING: Failed to clone …"` | REPRODUCED |
| 10 | Links: 1 into canopy, 4 into cascor, 0 into data | Checker's own `validate_file` (the PyPI 0.1.2 wheel is byte-identical to the in-repo copy), workflow excludes: canopy 1 link in 1 file; cascor 4 links in **2 files**; data 0 | Links REPRODUCED; "four juniper-ml notes" **REFUTED** (L2) |
| 11 | With data missing, the link check passes | Check mode on a synthetic root. Nothing missing: 0 errors. No data: 0. No cascor: 4. No canopy: 1. | REPRODUCED |
| 12 | Drift test with data missing: no root, `OK (skipped=3)` | Minimal synthetic roots, registry files fetched at each sibling's main, `GITHUB_ACTIONS=true`. No data: `OK (skipped=3)`, "ecosystem root not found". No cascor: the same. No canopy: `FAILED (failures=2, skipped=2)`. All present: `OK`, 11 tests. | REPRODUCED |
| 13 | 16 sibling sites (7 data, 7 cascor, 2 canopy) | Registry: 7 / 7 / 2, plus 2 self sites | REPRODUCED |
| 14 | "the job stays green" | Both pin lints print WARN and `continue` (`test_doc_tools_drift.py:260-262`, `test_ci_tools_drift.py:309-311`). Downstream steps skip a missing clone. The workflow was green on 7 of its last 8 runs. | REPRODUCED (static plus local runs) |
| 15 | `ci.yml:500` runs the file without siblings, so a remedy keyed on `GITHUB_ACTIONS=true` alone would fail every CI run | Line 500 sits in the unconditional "Regression Tests" job, and `ci.yml` has no sibling checkout. A no-sibling root with `GITHUB_ACTIONS=true` gives `OK (skipped=3)`. | REPRODUCED |
| 16 | `docs/REFERENCE.md` L2972 | Same measurements as rows 10-12 | REPRODUCED |
| 17 | DATA-055: `batch_delete` (:590-615) and `delete_expired` (:423-431) call `delete` unlocked at data `1afc3484` | Ranges are exact; `LocalFS.delete` takes no lock; identical at `v0.16.0` (`39d1cab2`) | REPRODUCED |
| 18 | #438 merged after the cut; at data `0f0f7e0e` the four writers lock and create takes no per-dataset lock | Merged 18:52:00Z; the Release was published 08:52:14Z. All four go through `delete_under_lock` or `update_tags`. Create uses `save_versioned`, which takes the global `_version_lock` only for a named dataset. | REPRODUCED |
| 19 | `record_access` call sites `:999`, `:1105`, `:1137`, `:1141`; none in `/latest`, list, filter, versions | Exactly those four, in GET `/{id}` and the artifact route | REPRODUCED |
| 20 | "(once, n=1)" | `primer-correction-round2-laneB-refute.md` L19: "(1 of 1)" | REPRODUCED |
| 21 | data438 claim 1 and F1 | Claim 1 is batch-tags going through `update_tags`; F1 is create writing inside the PATCH's window | REPRODUCED |
| 22 | ECO-010 middleware ranges and class lines | data 199-221, cascor 195-217, service-core 216-238; classes at :297, :256, :341 | REPRODUCED |
| 23 | ML-007: #2071 merged 52 s before the cut; target SHA vs `main` | 08:51:22Z vs 08:52:14Z. `target_commitish` is `39d1cab2…` for v0.16.0 and `main` for 0.14.0 and 0.15.0. `39d1cab2` was main's HEAD until 08:57:15Z. `target_sha` entered in `b8165386` (#2071). | REPRODUCED |
| 24 | §2 L180: two new tool blind spots | My own mutations. M7 gives `136\|101\|35` while the crosscheck says AGREE. M8 changes nothing in either tool. The control gives `136\|99\|37` and DISAGREE. | REPRODUCED |
| 25 | L182 "its fix-forward `APD-DATA-057`" | DATA-055 first appears in `6aabe4cc` (#2074); DATA-057 in `f2688a95` (#2080) | REPRODUCED |
| 26 | L300 "Round 42 filed three more … `APD-ECO-008`" | ECO-008 first appears in `836393cf` (#2005, 2026-09-22); ECO-009/-010 in `6aabe4cc` | **REFUTED** for ECO-008 (L1) |
| 27 | L302: group closed 2026-08-28 (cclient#143); exception-context fix 2026-08-21 | cclient#143 merged 08-28; dclient#158, cclient#123 and recurrence#124 all merged 08-21 | REPRODUCED |
| 28 | L997: #2059 merged 2026-09-23 | 22:57:09Z | REPRODUCED (NIT N5) |
| 29 | Ruling quotes now say "begins", carry ellipses, and are archived in full | Both are exact openings of the archived descriptions (168 of 300 chars; 129 of 240), and each cut remainder is non-empty | REPRODUCED |
| 30 | L1246 park wording | APD-ML-003 is covered only by a range, and the L1309 header is unchanged | **PARTLY REFUTED** (L4) |
| 31 | Primer: 21 lines, count unchanged, no line-breaker characters | 21 positional changes; 9983 / 9982 lines both sides; 0 breaker characters. The editor's `LINE_BREAKERS` equals the full `splitlines()` set. | REPRODUCED |
| 32 | Appendix D harness passes 62 at the head | "62 passed … All primer examples passed." | REPRODUCED |
| 33 | Error-path probe: 7/7 at the head, 7/7 escaped at `df21367d` | Exactly as stated | REPRODUCED (scope: M1) |
| 34 | Pin mutation check: 6/6 caught, control passes | 6/6 CAUGHT, control PASS. My discriminating controls: create revert plus the old line 5838 is MISSED; schema revert with no NaN arm is MISSED; reverting 5498 alone or 5502 alone is CAUGHT. | REPRODUCED |
| 35 | …PRIMER.md:9880 "NaN, Infinity or a non-integer `n_samples` is a 422 problem where it had been a plain-text 500" | `n_samples: 2.5` gives 201 at head and base. `"512"` and `true` were 201 at base, not 500. 1e19, 1e300 and 10^30 give a text/plain 500 at the head. | **PARTLY REFUTED** (M1) |
| 36 | E.1 item 3 against RFC 9110 §8.8.1 and the code | The bold rule matches §8.8.1's definition (checked in rfc-editor.org's text), and line 4220's table says "usually weak". Neither service compresses; data sends `PrerenderedJSONResponse(content=body)` with `ETag: body_etag(body)`. The cost clause is incomplete. | REPRODUCED (NIT N2) |
| 37 | 4224 "(Emphasis added.)"; 5363, 5378 and 5631 comments | The RFC text has no emphasis. The batch route's two-hop write shipped through 0.16.0. An unhandled error returns Starlette's text/plain 500. The 422 body echoes "NaN", "Infinity" and "-Infinity" as strings. | REPRODUCED (NIT N1) |
| 38 | Editor replay on base; a second run refuses | Byte-identical on all 3 files. Run 2: "FAIL: this second fix-forward has already run", nothing written. A perturbed-input control refuses and writes nothing. | REPRODUCED |
| 39 | Archive `--check`: every report equals its agent's last message | 30 OK, 5 unheaded files skipped, rc 0. My own parser (grouping by `message.id`) also gives 30/30. The base script dies with `FileNotFoundError`. | REPRODUCED |
| 40 | `136 rows \| 100 fixed \| 36 open`, AGREE, 44 tests `OK (skipped=3)` | All three exactly | REPRODUCED |
| 41 | Commit message: "the dated or miscounted prose both lanes named" | Lane A's N1 (L1297) was not applied and not recorded as rejected | **PARTLY REFUTED** (L5) |

## Findings

### HIGH
None.

### MEDIUM

**M1. The claim added to the primer's Appendix E intro about the toy's input handling (…PRIMER.md:9880) is false as worded.**

The sentence: "restricted a create's `params` to JSON numbers, so that NaN, Infinity or a non-integer `n_samples` is a 422 problem where it had been a plain-text 500". Measured with my own probe, `a13_toy_params_edge_probe.py`, on the pinned venv, POSTing each body in-process:

| Input | base `df21367d` | head |
|---|---|---|
| `n_samples: 2.5` | 201 (stored `n_samples=2`) | **201** (stored `n_samples=2`) |
| `n_samples: "512"` / `true` | **201** / **201** | 422 / 422 |
| `n_samples: "abc"` / `null` / `[512]` | 500 | 422 |
| `n_samples: 1e19` / `1e300` / `10^30` | 500 | **500 text/plain** |
| NaN / Infinity / `1e400` | 500 | 422 |
| `"mode": "fast"` (string param) | 201 | 422 |

Why:
- `StrictInt | StrictFloat` (…PRIMER.md:5502) admits any finite float.
- `n_samples = int(body.params.get("n_samples", 512))` (:5659) silently truncates it.
- `_synthesize_artifact` (:5550-5553) overflows on a huge value.

So:
- A non-integer number is still accepted.
- Some newly refused inputs had been 201, not 500.
- A JSON number can still escape as a plain-text 500.

The commit message repeats the claim. The probe `util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py` labels `"abc"` "non-integer n_samples" (:42) and prints "every client-input error is a 422 problem" (:93) after trying only 7 cases.

Fix, on the same line so nothing moves: "…so that NaN, Infinity or a non-number (a string, list, null or boolean) in `params` is a 422 problem, where most had been a plain-text 500 and a numeric string or boolean had been accepted; `n_samples` itself is still unchecked (a fraction is truncated, a huge value is a 500)". Also rename the probe's case to "non-numeric n_samples", scope its RESULT line to "every probed case", and add 2.5, `"512"`, `true` and 1e19 to it. Alternatively, validate `n_samples` itself (a strict int with bounds) and keep the sentence.

### LOW

**L1. The new §2.3 sentence misattributes ECO-008's filing (…DEFECT-REGISTER.md:300).** It says "Round 42 filed three more, all in canopy: `APD-ECO-008` (closed 2026-09-24), `APD-ECO-009` and `APD-ECO-010`". ECO-008's row first appears in `836393cf`, which is juniper-ml#2005, merged 2026-09-22T10:38:38Z. Round 42 (`6aabe4cc`, #2074) closed it. The same register says so at L240 ("a seventeenth, closed 2026-09-24; … -009 and -010 … filed open that day"), at L1234 ("found on 2026-09-22") and at L1429 ("`APD-ECO-008` was filed that day"). Fix: "Three more followed, all in canopy: `APD-ECO-008` (filed 2026-09-22 by juniper-ml#2005, closed 2026-09-24), and `APD-ECO-009` and `APD-ECO-010`, filed by round 42; …".

**L2. "four juniper-ml notes link into cascor" (…DEFECT-REGISTER.md:1305) counts the wrong unit.** There are four links in two notes:
- `notes/code-review/JUNIPER_2026-04-04_JUNIPER-CASCOR_COMPREHENSIVE-CODE-REVIEW-PLAN.md`, lines 14, 29 and 143;
- `notes/observability/JUNIPER_2026-05-05_JUNIPER-ML_REGISTER-OR-REUSE-HELPER-DESIGN.md`, line 108.

The row's own later parenthetical ("four into cascor") is right. Fix: "since two juniper-ml notes hold four links into cascor".

**L3. The `record_access` scope was corrected at L1307 only; the same false claim stands elsewhere.**
- …DEFECT-REGISTER.md:1699 (§5.1) still says, in the present tense, "`record_access` fires on every metadata read and every artifact download".
- L512 (§3) and …PRIMER.md:4199 say the same in the past tense.
- It was never true. At juniper-data `v0.11.0`, `/latest` (:628), `/filter` (:276) and `/versions` (:604) do not call it; only :672 and :698 do.

Fix: carry L1307's wording to L1699, and qualify L512 and primer line 4199 the same way (same-line edits).

**L4. The park-sentence fix is half-applied.**
- L1246 now says each row's park status is "stated … in a sentence that names it". But `APD-ML-003` appears only in its own row (L1293). Its park bullet (L1312) covers it by the range "`APD-ML-002` … `APD-ML-006`", so the close protocol's `grep -n 'APD-ML-003'` misses it.
- The park block's header, L1309, still says "(row-level sentences; a sentence here parks or unparks its row and nothing else)". The grouped bullets at L1312, L1619, L1626 and L1629 contradict it.

Fix: name all five ids in L1312, or say "names it, or a range that contains it", and align L1309 with L1246.

**L5. Lane A's NIT N1 from the specification was not applied, and not recorded as rejected.** The Source cell at …DEFECT-REGISTER.md:1297 still reads "(init, the single write in `_reload_dataset` — three since juniper-cascor#678 — …)", and the editor has no entry for it.
- At cascor `ec8b5bdb`, `_dataset_shortfall` is written in `start_training` :2572, `_rollback_pre_swap_state` :3924 and `_reload_dataset` :4691 (plus `__init__`).
- At cascor main `7f4a7213`, after cascor#688, there are four writers: :2560, :2623, :4104 and :4947.

Fix: name the writers at a pinned commit, or record N1 as rejected, with a reason.

### NIT

- **N1.** The Appendix E intro (…PRIMER.md:9876) says "Three other lines were corrected in place". Line 4224's "(Emphasis added.)" is now a fourth such correction, outside II.11 and unlisted. Fix: mention it in the 9880 addition.
- **N2.** E.1 item 3's cost clause (…PRIMER.md:9942-9944) is incomplete: "only makes it change more often than the data does, which costs revalidations but never serves stale bytes".
  - In §8.8.1's terms, field-order churn *is* a change to the representation data.
  - The cost is a 200 where a 304 would do, plus a spurious 412 on `If-Match` writes, which is the tag PATCH that E.1 item 1 and E.2 discuss.
  - The rest of item 3 checks out against the RFC text.
- **N3.** The L766 counts mix units. "43 anchors" counts numbers (42 citations), while "7 in the prose" and "the last 5" count citations (the last 5 are 7 numbers). "(82 …)" counts range ends (69 citations). Fix: state the unit once.
- **N4.** L1736's "(7947)" is the sentence's first line; the quoted words are on 7948-7949. It follows the §4 cell's convention (L967), so this is defensible.
- **N5.** L397 and L992 keep the "#2059 (`APD-ECO-008`, closed 2026-09-24)" wording that lane A's N2 flagged. The change clarified it at L997 only.
- **N6.** `util/ad-hoc/2026-09-24_register_primer_citation_census.py` computes `last = len(split("\n"))`, which is 9983 for a 9,982-line primer, and prints "primer has 9983 lines". Its "citation(s)" count counts range ends. Its regex would miss `L7950`, `PRIMER.md:7950` and `#L7950` shapes, none of which exist today.
- **N7.** Outside this change's claims: cascor#688 ("the annotation stays while any fetched split is loaded", merged 18:56:25Z, 37 minutes before this commit was authored) looks like the fix-forward that `APD-CASCOR-013` waits on. The register records data#438's merge, four minutes earlier, but not #688's. I did not validate #688.

## What this evidence cannot support

- **CI.** I dispatched no workflow. The silent-path conclusion rests on:
  - the workflow YAML;
  - the published checker (byte-identical to the in-repo copy), run on synthetic roots;
  - the drift test, run on minimal roots holding each sibling's registry-named files at main (data `0f0f7e0e`, cascor `7f4a7213`, canopy `7ab994e5`).
- **Live HTTP.** The toy ran in-process through httpx's `ASGITransport` with `raise_app_exceptions=False`. I ran no uvicorn server.
- **Memory.** I tried no `n_samples` value that would actually allocate memory. A moderate value (for example 10^10) may exhaust memory; I did not test it.
- **juniper-data behaviour.** The DATA-055 and DATA-057 claims were checked from source at pinned commits through GitHub's contents API; I re-ran no race. "(1 of 1)" is the source report's count. The worktree-isolation hook refused git against the sibling repos, so every sibling source came from GitHub read-only.
- **Reading.** I cannot verify the author's "each read". I read all 82 citations myself.
- **Transcripts.** The transcript check covers the 30 reports that carry an agent header. The 5 unheaded files are not transcript-backed.
- **Other documents.** For documents other than the register, I checked only for citations of the 21 rewritten lines. None exist outside the primer and ad-hoc tools, and no line moved, so no anchor shifted.

## Scripts

All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b/laneA/`. The extracted trees are deleted. Re-create them with `garchive.py` (the head tree), `gshow.py` (files at a commit) and `ghshow.py` (sibling files at a SHA).

- **Helpers:** `gshow.py`, `garchive.py`, `ghshow.py`, `ctx.py`.
- **Primer and toy:**
  - `a01_linebreakers_and_primer_diff.py`, `a11_primer_history_structure.py`
  - `a13_toy_params_edge_probe.py` (M1), `a14_pin_discrimination.py`, `a15_nan_echo_body.py`
- **Citations:** `a06_s4_primer_cells.py`, `a07_my_citation_census.py`, `a08_read_s4_citations.py`, `a09_read_prose_citations.py`, `a10_cites_of_rewritten_lines.py`, `a12_fixforward1_cell_units.py`.
- **Drift gate:** `a02_doctools_wheel_vs_repo.py`, `a03_xrepo_link_census.py`, `a04_drift_synthetic_roots.py`, `a05_linkcheck_missing_sibling.py`, `a24_ci_job_of_line.py`.
- **Register and provenance:**
  - `a16_replay_editor.py`, `a17_archive_independent.py`, `a18_register_tool_mutants.py`
  - `a19_filing_commits.py`, `a20_pr_dates.py`, `a21_ruling_quotes.py`, `a22_pr_merge_shas.py`, `a23_stale_restatements.py`
- **Outputs kept:** `rfc9110.txt` (fetched from rfc-editor.org) and the census, read-out and archive-check text files.

**Changed:** nothing, by me. All git use in this session's worktree was read-only (fetch, show, log, diff, archive); every other read was a GitHub, PyPI or RFC GET. During the run, two changes appeared in this shared worktree that I did not make and did not read: a modified `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (14:42:08) and an untracked `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md` (14:42:13). They are not part of `e2f87aae`.
