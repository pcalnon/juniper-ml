<!-- Archived verbatim 2026-09-24 from subagent a990ab20a1bd18405 of session 8f86dec2 (final message). -->

**Verdict: mostly reproduced, with one MEDIUM refutation.** The APD-ECO-008 close, the counts, the gate history, the quotes and all 14 archives reproduce. The PR's edit script, replayed on base `dcfc024f`, gives byte-identical files. The MEDIUM refutation: APD-ECO-011 names `juniper-canopy-demo` as a place the attack is reachable, and it isn't. Two corrections are incomplete, one Appendix A anchor is still stale, and there are several LOW/NIT wording defects.

## Claims table

| Claim (where) | What I measured | Verdict |
|---|---|---|
| canopy#660 fixed both divergences | `3a6dea95` merged 2026-09-23T19:16:49Z. Its parent `48074653` has `set(api_keys)` at :53 and `any(...)` at :74; `3a6dea95` has the filter at :76 and the loop at :106-110 | REPRODUCED |
| ml#2059 did what the register says | Guard registry imported at each commit: `_FORK_REPOS` gains canopy and juniper-ml; canopy and service-core become sites of both key-handling guards; anchors stay data+cascor. Merged 22:57:09Z | REPRODUCED |
| Canopy markers at `src/security.py:82`, `:112-116` (origin/main) | :82 is the filter; :112 `matched = False` through :116 `return matched` | REPRODUCED |
| Run 35975353661: 11 tests, OK, none skipped | Log: 11 `... ok`, `Ran 11 tests`, `OK`, no skips. Head `dcfc024f` contains #2059, and the clone step cloned canopy | REPRODUCED |
| Dispatched after the widening, 2026-09-24; canopy sites never ran in CI before | `workflow_dispatch` by pcalnon at 2026-09-24T08:27:32Z, 9.5 h after #2059. The previous run was the 09-21 schedule, before #2059 | REPRODUCED |
| Gate re-derived: 11 OK; pre-#660 control fails exactly the 2 canopy subtests; missing canopy FAILS | Synthetic ecosystem from each sibling's origin/main: A = 11 OK; B (canopy `48074653`) = failures=2, both canopy; C (no canopy) = FAILED (failures=2, skipped=2) | REPRODUCED |
| `SharedPackageGuardTest` runs in the required regression job | `ci.yml:500` is in the `tests` job; "Regression Tests (Python 3.12/3.13/3.14)" are required in ruleset 13805432 | REPRODUCED |
| Counts: `134 rows / 100 fixed / 34 open`, AGREE | Both repo scripts reproduce (base 126/99/27). Mutating the APD-ECO-008 marker gives 35 open and DISAGREE | REPRODUCED |
| Same counts, re-derived independently | My own parser: 134/100/34; primer 96/81/15; post-primer 38/19/19; the §2 list (81+19) equals the §5.1 set and the §4 FIXED set. All three mutation checks moved the counts | REPRODUCED |
| "thirty-eight", "nineteen", "34 = 15 + 19", "eighty-one", "12 → 19" | All follow from the parse | REPRODUCED |
| "FIFTEEN rows … different provenance" | 7 + 8 is arithmetically right, but the definition undercounts (Finding 7) | Arithmetic REPRODUCED; literal claim REFUTED (inherited) |
| Only 2 guards promoted from `KNOWN_GAP` (#1130, #1145); 3 entered at #1103, CORS at #1201, compare at #1974 | Registry imported at all 6 commits | REPRODUCED |
| CORS closed 2026-08-20, last of the ten copy-drift rows; last of the fifteen closed 2026-08-28 | data#273 / cascor#540 merged 08-20; cclient#143 merged 08-28T13:42Z | REPRODUCED |
| Primer anchors: Q26 → 9466, Q57 → 9595-9597, Q58 → 9599-9601; #1098 inserted 3 lines at 5758 | `git show HEAD:` primer confirms each. The old numbers were right at `68f62f5b`, and the register's first commit (`adbe92b0`, 05:10 CDT) predates #1098 (15:04 CDT) | REPRODUCED |
| "The Appendix A anchors — Q26, Q57 and Q58" | APD-SVCCORE-007's `9448` is also Appendix A and now lands on the wrong question (Finding 2) | REFUTED (incomplete) |
| service-core 0.7.0 still short-circuits; recurrence pins it | PyPI latest is 0.7.0 and the downloaded wheel has `return any(...)` at :66. `main` has the loop at :73-77. recurrence `requirements.lock:74` pins `==0.7.0` | REPRODUCED |
| APD-ECO-009 (`middleware.py:59-74`, both parsers) | Anchor exact. Live uvicorn on :47811/:47812, cap 32 bytes: chunked 100 B → 200 under both; CL + TE with a 64-byte chunk → h11 200 (received 64), httptools 400. Control: declared 100 B → 413 | REPRODUCED |
| APD-ECO-010: a refused key skips the limiter; FailedAuthThrottle anchors | 10 wrong keys and 5 keyless requests all 401, limiter called 0 times; right key → 200,200,200,429,429. Anchors: data `:297`, cascor `:256`, service-core `:341`; canopy `src/` has none | REPRODUCED |
| APD-ECO-011: route and demo gating, cross-site 200 | Anchor exact. Canopy main in demo mode, auth off: `text/plain` POST with a foreign Origin → 200, dataset 200 → 40 samples | REPRODUCED |
| APD-ECO-011: both deploy services have no key | Neither `juniper-canopy-demo` nor `juniper-canopy-dev` sets a key | REPRODUCED |
| APD-ECO-011: "exactly where it is reachable" | canopy-demo runs service mode, so the route returns 400 there (Finding 1) | REFUTED |
| APD-DATA-054 | Anchors exact. Served-bytes SHA-256 ≠ checksum for in-memory and LocalFS; reordering keys changes the bytes but not the checksum; artifact ETag is `weak_etag`; `If-Match` compares strongly | REPRODUCED |
| APD-DATA-055 | Stale `If-Match`: tag PATCH → 412 (control), batch-tags → 200 and applied, DELETE → 204 and gone. `_meta_write_lock` is overridden only by LocalFS (flock); the base no-op is inherited by Redis, Postgres and Cached | REPRODUCED |
| APD-DATA-056 (lone surrogate) | Reproduced in-process on data origin/main. Adding PATCH → 500 but the tag persists; later GET, PATCH and `/v1/datasets/filter` → 500; 4 ERROR logs carry `'\ud800'`; removing the tag heals it. Same at pre-#428 `7125e161`. Ordinary-tag control: all 200 | REPRODUCED |
| APD-ML-007 | Code: first heading only, no `--target`. At `af7831be` there are two `## [0.16.0]` headings; the ceremony renders 8 bullets and `_is_breaking=False`. At `7125e161`: 5 bullets, BREAKING Removed, `True`. The duplicate came from update-branch merge `583c8074`; `[Unreleased]` held #431/#434 until #435. v0.16.0 tags `39d1cab2` (main HEAD) | REPRODUCED |
| APD-ML-008: markers are satisfied by text | My 7 marker-preserving mutations (break, return True, early `any()` + dead loop, first-key loop, negated filter, pre-fix constructor with markers in a comment, `or True`) all pass the gate at both sites. A 3-key call-count / blank-key behavioural check caught all 7 on service-core and canopy | REPRODUCED |
| APD-ML-008: canopy test name; data/cascor spies use one key | `test_validate_compares_every_key_even_when_the_first_matches` was added by #660. data and cascor spy tests use `["valid-key"]` | REPRODUCED |
| APD-ML-008: adjacent gaps | The drift step has no `if: always()`. Without canopy, the link step fails on `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md:7`. The vacuity script only deletes markers. service-core's own suite catches the filter mutations and none of the compare mutations | REPRODUCED |
| Canopy route counts: 55/27/25 at `26e0546f`; 56/27/26 at `48074653`; #662 added `GET /api/selection` | Reproduced exactly with the whitespace key set; with no key, `/docs`-type routes add 4 | Counts REPRODUCED; "401 before / 200 after" NO ARTIFACT |
| cascor#678 `0e016a7` is a stale arm-time body | Auto-squash armed 13:32:10Z; `281bc524` and `71310f9b` came later and are absent from the message | REPRODUCED |
| Edit script: 58 edits, all-or-nothing | Replay on base: 58 `ok`; register and REFERENCE.md byte-identical to head; a rerun refuses and writes nothing | REPRODUCED |
| 44 tests OK (skipped=3) | Reproduced on the head extraction | REPRODUCED |
| The 14 archived reports equal each agent's last message | My own extraction (split on `"\n"`, same-id records merged), all 14: body = `"\n"` + message + `"\n"` exactly (the header ends in a blank line, plus one trailing newline) | REPRODUCED |
| The four owner-ruling quotes | "let's do option 1 now, and document this as a gap to be addressed in future work" is verbatim (free-text answer, `bc31e993` line 2300, 19:38:04.764Z). The other three are verbatim option labels; the recorded answers add " (Recommended)". "Keep while any split is fetched" is at `8f86dec2` line 562, 2026-09-24T07:53:26Z. All four question paraphrases are faithful | REPRODUCED |

## Findings

1. **MEDIUM: APD-ECO-011, "juniper-deploy's `juniper-canopy-demo` and `juniper-canopy-dev` services are open by design (no key), which is exactly where it is reachable".**
   - `juniper-canopy-demo` sets `JUNIPER_CANOPY_CASCOR_SERVICE_URL` and no demo mode (deploy `docker-compose.yml:791-835`).
   - `create_backend` then returns `ServiceBackend` (`src/backend/__init__.py:81-105`, same at v0.8.1), whose type is `"service"`, so the route answers 400 (`main.py:1645-1646`).
   - The only exception is the boot fallback when cascor-demo is unreachable (`main.py:420-434`). Only `juniper-canopy-dev` (`JUNIPER_CANOPY_DEMO_MODE: "true"`, :904) is reachable.
   - Fix: name canopy-dev, and describe canopy-demo as service mode with the fallback caveat.
2. **MEDIUM: §4 note, "The Appendix A anchors — Q26, Q57 and Q58 … are corrected".**
   - APD-SVCCORE-007's Primer column "1275, 9448" (head :963) is another Appendix A anchor past 5758.
   - At creation, 9448 was Q23 (per-replica in-memory rate limiting, the row's topic). At HEAD it is Q22's answer (circuit breaker).
   - Fix: change it to 9451, and name it in the note.
3. **MEDIUM (borderline LOW): §2 correction, "Round 42 made both false by filing … one juniper-data C (APD-DATA-055)".**
   - The Correctness sentence was already false at base: APD-DATA-046 is juniper-data, Sev C, open since 2026-09-09.
   - Fix: say so, and name APD-DATA-046.
4. **LOW: APD-ECO-011, "Routes outside `/api/train/*` carry no Origin check".**
   - With auth off, `require_browser_control_auth` returns at step 2 (`security.py:453-455`), so `/api/train/*` has no Origin check either.
   - Measured: cross-site `text/plain` POSTs to `/api/train/pause`, `/resume` and `/stop` → 200.
   - Fix: say that no HTTP route carries an Origin check in this profile.
5. **LOW: §2.3 blockquote, "The last one promoted, `cors-outside-auth`" (head :255).**
   - This is a line the PR edited, and it contradicts the PR's own correction: CORS entered at #1201 as `ENFORCED`, and #1974 came later.
6. **LOW: §4.9 preamble, "each row says which".**
   - The APD-DATA-054 and APD-DATA-055 rows name no finding round.
   - Their origin is traceable: DATA-055 to `data428-round2-validation.md` items 7/13 and round-3 lane B; DATA-054 to #428's implementation, confirmed by round-1 lane A.
7. **LOW (inherited): "FIFTEEN rows below have a different provenance".**
   - Rows with a provenance other than the round-37 validation also include APD-DATA-047 (#404), -050 (round 39), -051 (#404 work) and -052 (round-38 handoff).
   - The earlier "SEVEN" already undercounted; the PR carried the definition forward.
8. **NITs:**
   - The preamble now says "…from seven on 2026-09-24 — `APD-ML-002`–`-006` were filed that day". That reads as 09-24; they were filed 09-22.
   - "refuted them from the gate's git history" fits only the promotion claim. The CORS date was refuted from cclient#143's merge date, and "all but the compare row" from the table's "(nowhere)" cells.
   - "a failed juniper-data or juniper-cascor clone still skips every guard": the service-core sites still run (measured: `OK (skipped=3)`).
   - The §5.1 closing paragraph has a doubled "(seven since #1974)" parenthetical.
   - The APD-ECO-009/-010 rows say "found validating the ruling", while the preamble says "validating … two PRs"; the residue was recorded by #2032.
   - The PR body says "#2072 archived 8". It archived 11 `.md` files (8 final reports + 3 STOPPED-partial) and 2 patches.
   - "Byte-identical" holds for the message body; each file adds a blank line after the header and a trailing newline.

## What this evidence cannot support

- The canopy route counts' "401 before / 200 after" was not re-measured; only the counts were.
- The Redis and Postgres served-bytes claims rest on code reading.
- The link-check result used the PR head's `juniper-doc-tools`, not the PyPI copy that CI installs.
- The seven gate-passing regressions are my own constructions, not necessarily round 4's seven.
- Primer anchors past 5758 outside Appendix A (39 rows) were not checked.
- The canopy-demo finding comes from compose config and code, not from a running container.
- PyPI state was read on 2026-09-24 and may change.

Hygiene: all work stayed read-only, no environment variables or tokens were printed, and no data was sent externally except downloading one public wheel and reading PyPI's JSON. The four uvicorn servers I started on free ports 47811-47814 were stopped, and none of my processes remain. The live canopy writing to the main checkout's `logs/system.log` is not mine.

All instruments are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA/`. The key ones:
- `lane_a_count.py` (the independent parser)
- `build_eco.sh`
- `gate_history.py`
- `sc_mutations.py`
- `repro_data054.py` / `repro_data055.py` / `repro_data056.py`
- `eco009_client.py`, `eco010_limiter.py`, `eco011_repro.py`, `eco011_train.py`
- `ml007_breaking.py`
- `route_count_ws.py`
- `quotes.py`
- `reports_check.py` / `reports_diff.py`
- `replay_edit.sh`
- `appendix_anchors.py`
