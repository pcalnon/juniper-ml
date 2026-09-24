<!-- Archived verbatim 2026-09-24 from subagent aa5b6a0674e3d3218 of session 2fba4397 (final message). -->

**Verdict: PARTLY REFUTED. There is no HIGH and no MEDIUM finding. There are two LOW and eight NIT findings.**

Almost everything the correction `990ef3f9` claims reproduces from primary sources:
- Replaying the editor gives the head byte for byte, and every tool reproduces its stated output.
- Every new register fact checks out against source: the ECO-008 filing, the four links in two notes, `record_access`'s scope, the cascor writers, #688 and #690, #438, and the unit counts.
- Every clause of the new toy sentences matches the toy's behaviour, and the new cost clause matches RFC 9110 §8.8.1.

What does not hold:
- **LOW:** Appendix E now counts "a fourth line corrected in place", but the same commit rewrote a fifth line in place (4199) and it is named nowhere.
- **LOW:** the stated reason the deep-cursor fix has no test in the primer's own suite is false. I built a same-line test and ran it.
- **NIT:** several smaller wording and comment claims do not reproduce (listed below).

**Documents.** Line numbers are at the head `990ef3f9` unless a commit is named.
- `…DEFECT-REGISTER.md` = `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- `…PRIMER.md` = `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`
- The round-1 reports are `register-fixforward2-round1-laneA-reprobe.md` and `register-fixforward2-round1-laneB-refute.md`. Also cited: `data438-round1-laneA-reprobe.md` and `ml2080-round1-laneA-reprobe.md`. All four are in `reports/2026-09-24_defect-register-round-42/`.
- The corrections editor is `util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py`.
- The RFC is `rfc9110.txt`, fetched from rfc-editor.org (sha256 prefix `21c1cdce6ab0e550`).

## Claims table

| # | Claim (where) | What I measured | Result |
|---|---|---|---|
| 1 | Branch head `990ef3f9`, no PR | Branch API gives `990ef3f9…`; PR list for the head is empty | REPRODUCED |
| 2 | The corrections editor replays `e2f87aae` into `990ef3f9` and refuses a second run | Output is byte-identical for the register and the primer. Run 2 says "already been applied". Four controls (a perturbed line 9943, a missing PREREQ, a duplicated substitution, `--dry-run`) all refuse or write nothing. | REPRODUCED |
| 3 | The first editor's source change (F541 fix, escaped U+2028/U+2029) changes nothing | The changed editor still turns `df21367d`'s three files into `e2f87aae`'s byte for byte. Its constants are identical. | REPRODUCED |
| 4 | Primer: 13 lines changed in place, count unchanged, no line-breaker characters | 13 lines change: 4199, 5346, 5377, 5378, 5433, 5434, 5502, 5600, 6117, 6120, 9880, 9943, 9944. The file has 9,982 lines before and after, and 0 breaker characters. The register changes 14 lines, with pipe counts unchanged. | REPRODUCED |
| 5 | Appendix D harness gives 62 | "62 passed … All primer examples passed." | REPRODUCED |
| 6 | Probe: 13/13 at head, 11/13 differ on `df21367d` | Exactly that. On `e2f87aae`, 1 of 13 differs (the deep cursor). | REPRODUCED |
| 7 | Mutation check: 7/7 caught, control passes | 7/7 CAUGHT, control PASS. My discriminating runs: the lax union on `e2f87aae` passes the harness; the same revert at head is caught. | REPRODUCED |
| 8 | Lax `int \| float` passed the whole harness and turned "512" into the id of 512 (mutation-check docstring) | `"512"` gives 201 with `spiral-v1-fb1d7a72…`, and `512` then gives 200 with the same id. `true` maps to the id of `1`. | REPRODUCED |
| 9 | Census: 69 citations, 82 numbers, 9,982 lines, none on a blank line | My own digit-run census finds 95 numbers in range = 82 + 13 RFC numbers. 13 of them are range ends, so there are 69 citations. 0 land on a blank line. | REPRODUCED |
| 10 | Archiver `--check`: 32 OK; an unknown session gets a clear message | 32 OK, 5 unheaded files skipped, rc 0. My own parser, which groups by `message.id`, matches both new reports. An unknown session gives `SystemExit("…not in SESSION_IDS…")`. | REPRODUCED |
| 11 | `register_open_set`: 136 \| 100 \| 36, crosscheck AGREE; four suites give 44 OK (skipped=3) | Exactly | REPRODUCED |
| 12 | Per-PR screens: symbol 1 WARN waived, docs 0 fail, structure 0 → 0 on 5 files; pre-commit passes | Symbol screen: `const:SESSIONS` LOST, waived. Docs screen: OK. Structure: 0 → 0 on 5 files. The generic hooks and the doc-link check pass on the files they cover (`reports/` is globally excluded). | REPRODUCED (hooks run individually) |
| 13 | L229: "9,982 since juniper-ml#2075 appended Appendix E" | `f4d050c6` (#2075) inserts 116 lines at 9866, the end of the file. `FailedAuthThrottle` appears 0 times. | REPRODUCED |
| 14 | L300: ECO-008 was filed 2026-09-22 by #2005 and closed 2026-09-24; round 42 filed ECO-009 and -010; all three are canopy's | The row first appears in `836393cf` (#2005, merged 2026-09-22T10:38:38Z) and is marked FIXED in `6aabe4cc` (#2074, 2026-09-24). -009 and -010 first appear in `6aabe4cc`. All three rows are canopy's. | REPRODUCED |
| 15 | L397 and L992: #2059 merged 2026-09-23 | Merged 2026-09-23T22:57:09Z | REPRODUCED |
| 16 | L512, L1699 and primer 4199: `record_access` never fired on the list, filter, `/latest` or versions reads | An AST route map at `v0.11.0` finds it only at :672 and :698. At `1afc3484`: :999, :1105, :1137, :1141. The same holds at every revision since it entered the routes (`cbae474`, #46). | REPRODUCED (L1699 wording: N1) |
| 17 | L766: 42 citations in 39 rows (43 numbers), 8 on blank lines; 7 in the prose; the last 5 citations | My recount of #2080 (`6aabe4cc` → `f2688a95`): 39 rows, 42 citations, 43 numbers, 8 blank. Prose: 7 citations at L532, 536, 980, 1166 and 1218. Second fix-forward: 3 citations at L527 (two blank), plus one each at L1736 and L1737. | REPRODUCED |
| 18 | L766: the shift "holds for every non-blank line past 5758 that no later commit rewrote in place" | 11 non-blank lines differ from `68f62f5b`+3 at the head. All 11 were rewritten in place by later commits. #1098 is the only commit that moved a line. | REPRODUCED |
| 19 | L1297 (APD-CASCOR-013): #688 merged 2026-09-24; #690 is open and is #688's validation fix-forward | #688 merged 18:56:25Z. #690 is open; its body begins "Fixes forward the findings of **#688's independent post-merge validation**". #688 implements the 2026-09-24 ruling "keep while fetched splits stay". | REPRODUCED |
| 20 | L1297: writers at `ec8b5bdb` are :2572, :3924 and :4691; before #678 only `_reload_dataset` wrote; four writers since #688 | AST count at `0e016a7c^1`: `__init__` and `_reload_dataset` (:4237). At `ec8b5bdb`: `__init__`, then 2572, 3924, 4691. At `7f4a7213`: `__init__`, then 2560, 2623, 4104, 4947. | REPRODUCED |
| 21 | L1305: two notes hold four links into cascor | Workflow excludes, checker in check mode, empty ecosystem root, 1,327 files. Cascor: 4 links in 2 notes (the code-review plan at lines 14, 29, 143; the register-or-reuse design at line 108). Canopy: 1 link. Data: 0. | REPRODUCED |
| 22 | L1307: #438 merged after the v0.16.0 cut; claim 1a erased 2 of 3 | #438 merged 18:52:00Z. The Release was published 08:52:14Z at `39d1cab2`. `data438-round1-laneA-reprobe.md` row 1a says "2 of 3 conditional 200s erased". `ml2080-round1-laneA-reprobe.md` claim 17(B) is the forced interleaving. | REPRODUCED |
| 23 | L1309–1310 (new park header) and L1312 (all five ids named) | Every open §4.9 row is named, by full id, at the head of a park bullet | REPRODUCED |
| 24 | Primer 5346: the second divergence, including `seed: null` meaning a nonce in the real service | At `df21367d` the toy answers 201 for a string, a boolean, a null, a nested list, a nested object and `seed: null`; at head all are 422. In juniper-data, `dataset_id.py:54-55` mixes in a nonce when `seed` is None, and spiral's params declare `seed: int \| None`. | REPRODUCED |
| 25 | Primer 5377–5378 and 5433–5434: problem+json except FastAPI's own 404/405/body-parse 400 and an unhandled 500 | 404 `{"detail":"Not Found"}`. 405 `{"detail":"Method Not Allowed"}`. Both a 5,000-digit integer and invalid UTF-8 give 400 `{"detail":"There was an error parsing the body"}`. `n_samples` of 1e19, 1e300 or 10^30 gives text/plain 500. The routes' own 404, 412, 428, 400 and 422 are problem+json. | REPRODUCED |
| 26 | Primer 5502, 5600 and 6117 comments | `"512"` and `true` give 422 at head. A 10,000-deep cursor, balanced or not, gives 400 problem+json at head and 500 before. The line-6117 test addition catches the lax union. | REPRODUCED (the `true` half is not tested in the suite: N6) |
| 27 | Primer 9880: NaN, Infinity or an `n_samples` that `int()` rejects went from 500 to 422; other non-numbers from accepted to refused; a fraction is truncated; a huge value is a 500; a deep cursor is a 400 | Every clause matches my 44-case attack at `df21367d`, `e2f87aae` and head (`1.5` stores `n_samples` 1) | REPRODUCED |
| 28 | Primer 9880: "a fourth line corrected in place" | Line 4199, prose outside II.11, was also rewritten in place by this commit and is not named anywhere in Appendix E | **REFUTED** (LOW-1) |
| 29 | Primer 9943–9944, the cost clause | §8.8.1: a strong validator "changes value whenever a change occurs to the representation data". A strong validator "might change for reasons other than" that, but the server should change it only when necessary. Strong validators serve "partial content ranges, and 'lost update' avoidance". So "costs revalidations and spurious `412`s" is sound. | REPRODUCED |
| 30 | Probe `:22-24` and stated omission 2: the suite "has no line to test [the deep cursor] without moving one" | I added a same-line test on lines 6084, 6086 and 6087. The head passes 62. With 5600 reverted: "1 failed, 61 passed". The line count is unchanged. | **REFUTED** (LOW-2) |
| 31 | Probe `:51-54`: "an unbalanced one fails as a JSONDecodeError" | On CPython 3.13.13, an unbalanced `[`×10000 raises RecursionError (500 at `df21367d`). Only an unbalanced string 5,000 deep gives JSONDecodeError. | **REFUTED** (N3) |
| 32 | Probe `:51-54`: the 26.7 KB URL "uvicorn's h11 parser refuses before the app sees it" | uvicorn 0.49.0 with h11, one write on loopback: the app saw it (200). With 8 KB writes: 400 "Invalid HTTP request received." With 1 KB writes: the connection closed. httptools passed all three. | **PARTLY REFUTED** (N3) |
| 33 | Commit message: "the first editor's source no longer holds raw U+2028 / U+2029" | True of the first editor. The new corrections editor holds both at `:260`. | REPRODUCED (N4) |
| 34 | L766 "(…; each read)" | I verified the counts, the blank status, and that none of the 82 numbers points at a line this delta rewrote. I did not re-read all 69 citations myself. | Counts REPRODUCED; the reading is NO ARTIFACT |

## Round-1 findings: disposition

**Lane A (`register-fixforward2-round1-laneA-reprobe.md`)**
- **M1: addressed correctly.** Line 9880 was rewritten and every clause is true (#27). The probe case is renamed, 1.5, "512", `true` and 1e19 are added, and the RESULT line is scoped. Residual: N2.
- **L1, L2 and L5: addressed correctly** (#14, #21, #20).
- **L3: addressed.** Lines 512 and 4199 are exact. L1699 still lacks the `/latest` exception (N1).
- **L4: addressed correctly** (#23).
- **N1: addressed for 4224, but the same miss is re-created for 4199** (LOW-1).
- **N2, N3, N5, N6 and N7: addressed correctly.**
- **N4: not applied and not recorded as rejected.** Round 1 itself judged it defensible, so this is harmless.

**Lane B (`register-fixforward2-round1-laneB-refute.md`)**
- **M1, M2, L1, L4 and L5: addressed correctly.**
- **L2: addressed.** The "512" test and the lax-union mutant both discriminate. The `true` half is tested only by the external probe (N6).
- **L3: addressed.** The header comment `# 6. One error model everywhere` at line 6091 predates this change and still overclaims (N8).
- **L6: stated omission.** See below.
- **L7: addressed.** `RecursionError` is caught, and 1e300 is covered by the documented huge-value 500.
- **N1: addressed in the register.** The census docstring (`util/ad-hoc/2026-09-24_register_primer_citation_census.py:18-19`) keeps the unqualified claim (N5).
- **N2, N3, N6, N7, N8 and N9: addressed correctly.**
- **N5: fixed in the first editor, but it recurs in the new corrections editor** (N4).

## Stated omissions

- **`n_samples` documented, not fixed: holds.** Lines 5378 and 9880 document it, and the probe tests 1.5 → 201 and 1e19 → 500. The listed consequences are incomplete: see N7.
- **Deep-cursor fix tested only by the external probe: the omission is real, but its reason does not hold** (LOW-2). The harness misses a revert of line 5600.
- **L6 answered by amending the park bullet: holds as disclosed.** The bullet (L1629–1631) still says "awaiting an owner ruling, do not action". So lane B's point, that the park blocks the silent-path remedy, is deferred to a ruling rather than resolved.
- **`docs/REFERENCE.md` unchanged since `e2f87aae`: holds.** `990ef3f9` does not touch it. Its sentence carries no count and no `record_access` claim that would need these corrections.

## Findings

### HIGH / MEDIUM
None.

### LOW

**LOW-1. Appendix E miscounts the lines corrected in place (…PRIMER.md:9880).**
- …PRIMER.md:9873–9876 says affected prose keeps its text, except for the lines it names. Line 9880 ends "…marked line 4224's bold as added emphasis, a fourth line corrected in place".
- This commit also rewrote line 4199, a prose passage in §II.6 under a "[Corrected: E.2]" link. No line of Appendix E mentions it.
- The same omission is in three other places:
  - the editor's comment (`…_corrections.py:236`, "the fourth in-place correction named");
  - the editor docstring's primer bullet (`:25-28`);
  - the commit message's primer summary.
- This is the class round-1 A N1 / B N4 flagged, re-created by the fix.
- **Fix, on the same line 9880:** "…and marked line 4224's bold as added emphasis; with line 4199, whose `record_access` claim it limited to the single-dataset reads, five lines were corrected in place".

**LOW-2. The deep-cursor fix is left out of the primer's own suite on a false premise.**
- `util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py:22-24` and stated omission 2 say the suite "has no line to test without moving one".
- The technique this commit used on lines 6117 and 6120 works here too:
  - 6084: `response, deep = await client.get(".../datasets?cursor=not-a-real-cursor"), await client.get("/v1/datasets?cursor=" + __import__("base64").urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode())`
  - 6086: `assert response.status_code == deep.status_code == 400`
  - 6087: the content-type check, applied to both responses.
- Result: the head passes 62; with 5600 reverted, "1 failed, 61 passed"; the line count is unchanged (`b19_inplace_deep_cursor_arm.py`).
- **Fix:** add that test (or a cleaner variant), or reword the omission as a choice and give the reason.

### NIT

- **N1.** …DEFECT-REGISTER.md:1699 says "`record_access` fires on every single-dataset metadata read". `/latest` returns one dataset's `DatasetMeta` and never fired it (`v0.11.0` :629, `1afc3484` :933). Lines 512 and primer 4199 carry the exception; L1699 does not. Pairing "every single-dataset read" with "though not /latest" is also self-contradictory unless `/latest` is excluded by definition. Primer line 4277's "on every GET" is defensible in context. **Fix:** "the single-dataset metadata read (`GET /{id}`) and every artifact download".
- **N2.** …PRIMER.md:9880, "as lines 5377-5378 now say": those lines state the huge-value 500 but not the truncation.
- **N3.** The probe comment at `:51-54` gets two things wrong (#31, #32). An unbalanced cursor does not avoid the recursion. On uvicorn with h11, a single-write request reaches the app, so the 500 was reachable on a real server before this fix.
- **N4.** `…_corrections.py:260` holds raw U+2028 and U+2029. The file is 320 lines by `split("\n")` but 322 by `splitlines()`: lane B's N5 again, in the new file. Separately, `:288` prints "9983 lines before and after", the off-by-one the census fix removed. **Fix:** use escapes, and count with `splitlines()`.
- **N5.** The census docstring (`…citation_census.py:18-19`) still says the shift check "holds for every non-blank line past 5758". L766 now qualifies that claim.
- **N6.** Line 5502 says `true` is a 422, but only `"512"` is tested in the suite. A `StrictInt | StrictFloat | StrictBool` mutant passes the harness; the probe catches it. The mutation-check docstring (`:29-32`) credits the lax-union mutant with the whole "never coerced" half. **Fix:** add `true` to the line-6117 test, or scope the docstring.
- **N7.** The documented `n_samples` consequences are incomplete. A negative value is accepted (`-5` gives 201 with `n_samples` -5 and size 0). A value short of overflow allocates that many bytes (10^7 gives 201 with 10 MB). The probe's "fractional (truncated)" case checks only the status code.
- **N8.** (Predates this change.) The test header `# 6. One error model everywhere` (…PRIMER.md:6091) survives the scoping of lines 5377 and 5433.

## What this evidence cannot support
- **CI.** No workflow was dispatched. The screens ran locally against refs. I did not run pre-commit itself: I ran the hooks that apply to the changed files one by one, and the doc-link check through the in-repo checker, not the PyPI wheel the workflow installs.
- **The toy.** All toy runs were in-process through `httpx.ASGITransport`. The uvicorn test served a trivial ASGI app, not the toy, on uvicorn 0.49.0 from JuniperCanopy1, over loopback only. I did not try `n_samples` above 10^7.
- **Sibling repos.** juniper-data and juniper-cascor facts come from read-only `git show`/`log` on their local clones (which hold every pinned SHA) and from GitHub API GETs. I re-ran no race: the "2 of 3" is the source report's count.
- **Citation reading.** I did not re-read all 69 citations. None of them points at a line this change rewrote.

## Scripts
All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/`. The extracted trees are deleted. Re-create the head tree with `git archive 990ef3f9 | tar -x -C …/laneA/head` from the worktree.
- **Helpers:** `gshow.py`, `ghshow.py`, `ghpr.py`, `sibgit.py` (read-only git in the sibling repos).
- **Diffs and replay:** `b01` (line-breaker characters), `b02` (corrections-editor replay and controls), `b03` (positional line diff), `b21` (first-editor replay).
- **Counts:** `b04` (my own census), `b09` (#2080 recount), `b10` (the last five), `b11` (shift check), `b16` (park coverage), `b20` (citations of the rewritten lines).
- **Source facts:** `b06`, `b07` (`record_access`), `b08` (cascor writers), `b15` (cross-repo links), `b27` (ECO-008 history).
- **The toy:** `b12` (discriminating mutants), `b13` (attack across three revisions), `b14` (lax-union ids), `b19` (same-line test), `b22`–`b26` (h11, uvicorn, JSON depth).
- **Tooling checks:** `b05` (archive), `b17` (markdownlint, informational), `b18` (screens), `b28` (generic hooks).
- **Outputs kept:** `census_head.txt`, `b13_out.txt`, `reg_diff_U0.txt`, `rfc9110.txt`.

**Changed:** nothing by me. I used only `git fetch` of the branch, read-only git and `gh api` GETs. A uvicorn server started inside one script on an ephemeral loopback port and stopped before the script exited. The worktree's modified `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` and untracked `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md` were there at session start and are not mine.
