<!-- Archived verbatim 2026-09-24 from subagent a7f3c29f8a796bb3d of session bc31e993 (final message). -->

**Round-3 validation of juniper-ml#2032.** The PR head is `27e1541d`. Its register is byte-identical to `412b265f`, and main has not touched the register since the PR branched. Line numbers below are for `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` at the head. Nothing was edited. My probe scripts are in the scratchpad `r3v2032/`.

### Fix claims

| Claim | Verdict | Evidence |
|---|---|---|
| **H1** (WebSocket reason refuted, conclusion stands) | **Partly fixed.** The substance is right, but the fix never reached `APD-CASCOR-005`'s row, which still carries the same claim (Medium 2 below). | canopy `48074653` `src/main.py`: `:712` falls back to `?api_key=` without trimming; `:713-714` admits a keyless connection. All three endpoints (`:776`, `:913`, `:3576`) use `allow_browser_auth=True`. The Origin gate and `/ws/control`'s CSRF check (`:973-998`) apply whether or not a key is presented. The bearer path strips blanks (`:744`) and refuses. I confirmed on uvicorn 0.49.0 that `?api_key=+++` arrives as `'   '`. |
| **M1** (both defaults; no deploy profile reaches it) | **Fixed** (one scope nit, Low 5) | `src/settings.py:435` has `require_auth: bool = False`. `juniper-deploy/docker-compose.yml:690` sets `CANOPY_API_KEY_FILE` and `:696` sets `JUNIPER_CANOPY_REQUIRE_AUTH:-true`. The `-demo` and `-dev` services set no key. `get_secret` strips a file but not the env var. |
| **M3** (X-A framing) | **Fixed** | §4 of `HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md` (`:166-171`) reads "unreachable at startup … Fail closed, fail open, or cache the last-known set". The file exists on main and head. Mapping the built-in fallback to "fail open" holds up. |
| **M4** (weekly red is a coincidence; the same skip exists for data or cascor) | **Fixed** | `docs-full-check.yml`: the clone failure is swallowed (`:110`) and the link check (`:125-128`) runs before the drift step (`:256-259`). The only juniper-ml link into canopy is `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md:7`. doc-tools finds the ecosystem root once 3 or more siblings exist and reports "file not found in juniper-canopy". `tests/test_service_fork_drift.py:264` needs every member of `_FORK_REPOS`, and `:353` skips otherwise. |
| **LOW1** (four constraints) | **Fixed** | (1) through (4) are all present. |
| **LOW2** (HTTP claim scoped to the key gate) | **Fixed** | `src/middleware.py:128-129` reads the header only. My probe shows both uvicorn parsers deliver ASCII-whitespace `X-API-Key` as `''`. |
| **LOW4** (skip env var logs "SKIPPED") | **Wording fixed, but it adds a new scoping error** (Low 3) | `juniper-service-core/juniper_service_core/auth_posture.py:106-112` checks the skip before `real_keys` (`:114`) and `require_auth` (`:119`). |
| **LOW5** (quote attribution) | **Fixed** | cascor `manager.py:3941` holds "A DEPLOYMENT DEFAULT, NOT AN OVERRIDE"; `app.py:539` holds "A DEFAULT, NEVER AN OVERRIDE". "its caller" is one of two callers. |
| **LOW6** (key absence; `null` claim) | **Fixed** | `manager.py:3935` tests `"allow_truncation" not in params`; `_as_bool_stance(None)` returns `None` (`:3886`). |
| **LOW7** ("no startup dependency", auto-start) | **Fixed** | `app.py`: `wait_for_ready` at `:523`, resolver at `:543`, the failure is swallowed at `:637`. Only these two paths consult the set. |
| **LOW8** (dates wrong on main) | **Both fixed; one new sentence has already expired** (Medium 1) | Line 254 and line 1641 now say "juniper-ml#2032". |
| **LOW3** (§2.3 counts; §2 closing sentence) | **Counts right; neighbouring sentences not updated** (Low 1) | I counted the ids myself: 11 + 3 + 2 = **16 unique** at head (APD-CCLIENT-005 appears twice) against 15 on main. The six service-core-copy ids are DATA-002, DATA-036, DATA-003, CASCOR-006, DATA-001 and CASCOR-004. Line 181 is correct. |
| **LOW9** (documents named) | **Mostly fixed; one new unnamed reference** (Low 4) | Both handoffs exist on main and head. §6 of the round-41 handoff records the gate question as unattacked. |
| **Ruling X-B** (`APD-CASCOR-013`) | **Recorded faithfully and matches cascor#678.** One overstatement (Low 6) and an old headline left standing (Medium 3). | "Follow the loaded data" is recorded, with "null because nothing was fetched" rejected. In #678, `start_training` sets `_dataset_shortfall` only when `X` is passed (null for inline data, the fetch's own annotation for auto-start). `reset()` deliberately does not clear it. A refused staged fetch and a refused swap both restore it. #676 is `current_dataset`, merged. #678 is still open. |
| **Ruling APD-ECO-008 re-confirmation** | **Faithful to the option labels** | "Keep: match siblings" was chosen. "Fail closed, ecosystem-wide" is recorded as "fail the boot in all four services" — I can't check that wording against the option text, but exactly four services (data, cascor, canopy, recurrence) call service-core's `enforce_auth_posture`. "Compare fix only" is recorded as "dropping the filter half". The re-confirmation is recorded as coming after the behaviour change was shown. |

### New defects

**MEDIUM**

1. **Line 1494: "Until #660 merges, canopy `main` behaves as follows".** Also stale: row 1278 ("`:74` is still `any(...)`", "Canopy also diverges at `:53`", and the source anchors `:53`/`:74`), line 990 ("`:53` is a bare `set(api_keys)`") and line 1550 ("`:74` … still short-circuiting").
   - Why it's wrong: juniper-canopy#660 merged at 2026-09-23T19:16:49Z (`3a6dea95`), about six hours after `412b265f` was committed. On canopy main, `:53` is now a docstring line and `:74` a comment. The filter is at `:76` and the `matched` loop at `:106-110`.
   - Fix: change these to past tense ("Before juniper-canopy#660, merged 2026-09-23 …"), record the canopy half as shipped in the `APD-ECO-008` entry while keeping the row open for the gate half, and re-anchor the line numbers or pin them to `48074653`.

2. **Line 990 (`APD-CASCOR-005`'s §4 row) still says "that one fails CLOSED rather than open, because its only caller turns `""` into `None` via a truthiness test, so it is a divergence and not a bypass."**
   - Why it's wrong: line 1501 now says the stated REASON for "fails closed" is refuted, but this row is the only place the register states that claim, and it is left uncorrected. The round-41 handoff (`HANDOFF_2026-09-22_defect-register-round-41-…`) names "the canopy fail-closed mechanism" as unattacked, so this row is the target.
   - Also, row 1278's "(Corrected 2026-09-23: the stated REASON is refuted …)" sits against a reason the row doesn't give. The row's reason is the `""`→`None` mapping, which says nothing about whether a key can be presented.
   - Fix: add the correction at line 990, and point line 1501 at `APD-CASCOR-005`'s row.

3. **Line 1444: "RULED: actionable. Clear the annotation at the **start of every run** … a run that fetched nothing correctly reports nothing" is left standing.**
   - Why it's wrong: the 2026-09-23 paragraph (lines 1448-1456) says the annotation is "kept by a start on retained data and by `reset()`", which is the opposite. Commit `e02020d3` in #678 shows the first implementation followed this headline and was reversed ("reset() no longer clears it").
   - Row 1285 also still counts "not on reset" as part of the defect.
   - Fix: mark the headline "superseded in part 2026-09-23" and narrow the row's defect to "not replaced when new inline data is bound".

**LOW**

1. **Adding the compare row made four other claims false:**
   - Line 183 and line 242: "the `OPTIONS`/CORS row was the last one open". The compare row closed 2026-09-21; CORS closed 2026-08-20 (line 177).
   - Line 242: "each … promoted to `ENFORCED`". Line 1641 says `nonshortcircuit-key-compare` was "added directly as ENFORCED".
   - Line 242: "A drift check against `juniper-service-core` would catch these". Not for this row — service-core lacked the guard too.
   - Line 22: "§2.3 groups fifteen entries", against line 240's "Sixteen".

   These are the kind of claim, with no id in them, that the register's own warning at line 180 describes.
2. **Line 1401: "(True when written, 2026-09-21 …)".** It contradicts the PR's own lines 1354-1356 ("that had to be settled before code"), §0.3 of `HANDOFF_2026-09-15_defect-register-round-39-…` and §4 of the round-40 handoff ("an owner decision is owed", 2026-09-21). `APD-CASCOR-008` was awaiting a decision on the day that sentence was written.
3. **Lines 1505-1507: "the boot fails under `require_auth`, and otherwise logs "running OPEN" (with `JUNIPER_SKIP_AUTH_POSTURE_CHECK` set it logs … SKIPPED instead)".** The skip returns before `require_auth` is checked, so with the skip set the boot does not fail even when `require_auth` is on.
4. **Lines 1509-1510: "the same posture canopy documents for "no key set"".** No canopy file contains that phrase and no filename is given. The nearest are `src/security.py:5` ("disabled when unset") and `:370` ("no key configured").
5. **Line 1514: "juniper-deploy … defaults `JUNIPER_CANOPY_REQUIRE_AUTH=true`".** That is Compose only. `k8s/helm/juniper/templates/canopy-deployment.yaml` sets `CANOPY_API_KEY_FILE` but never sets `REQUIRE_AUTH`. The conclusion still holds, because the key comes from a stripped file.
6. **Line 1454: "a run on partial data always says so".** A run on partial data passed inline reports null by design (#678 guards against this: "new inline data after a partial run still reports `null`").
7. **Line 8: `**Last Updated**: 2026-09-22`** was not bumped, although the PR records rulings and corrections dated 2026-09-23.
8. **Lines 1352-1353: "The startup dependency this introduces …"** is not marked as superseded by the 2026-09-22 lazy-fetch ruling.
9. **Nits:**
   - Line 1366-1367: "What was not offered are the per-request forms". The ruled option is itself a per-request form.
   - "Unchanged by the fix" omits `main.py`'s `_docs_enabled`, which #660's own comment names.
   - `/api/csrf` has no CSRF check and admits a request with no Origin, so "through its Origin + CSRF checks" overstates it.

**Process (not a register defect).** `gh pr checks` shows 2 fail, 19 pass, 6 skipping. `Regression Tests (Python 3.14)` failed on `test_isolated_stack_script…test_rebuilds_venv_when_only_an_aged_out_skeleton_remains` with `OSError: [Errno 39] Directory not empty` during tempdir cleanup. The Quality Gate failed only because of that. This looks like an unrelated flake: the identical register at `412b265f` passed CI and main at `51993b37` is green. The PR shows as BLOCKED until the job is re-run.

### Attacks that did not land

- **Table integrity.** All 225 `| APD-` rows keep a constant cell count (6 in §4 tables, 4 in §5.1). My checker caught both mutated negative controls, so a clean result is meaningful.
- **Register scripts.** Run against the head copy: `register_status_crosscheck.py` gives AGREE 99/99/99, and `register_open_set.py` gives 126 rows, 99 fixed, 27 open. Main gives identical output.
- **Unicode-whitespace key.** A `0xA0` header survives both parsers, but `hmac.compare_digest` raises `TypeError` on it, giving a 500 rather than a bypass. The conclusion holds; the stated mechanism covers ASCII whitespace only.
- **Residue claims hold.**
  - A chunked body bypasses canopy's `Content-Length`-only cap under both parsers. CL plus `Transfer-Encoding` passes 64 bytes under h11; httptools rejects it with 400.
  - canopy has no failed-auth throttle.
  - No test watches service-core's `matched` loop, and `juniper-service-core/CHANGELOG.md` does call it a gate marker.
- **The four X-A constraints.** #678 follows all four: the fetch is gated on key absence, 5 s with no retries, memoised per URL, and has its own `opt_in_withheld` remedy. The data-client defaults really are 30 s and 3 retries.
- **"All seven guards".** `tests/test_service_fork_drift.py` has exactly seven, and the compare guard's sites are data and cascor only.
- **"Over HTTP the reading holds".** The browser surface admits keyless requests exactly as it would with a real key, so nothing is bypassed.
- **Pre-existing, not from this PR.** Line 177 says "Eighty-one … fixed" and then "all seventy-nine are recorded in §5". Main has the same text.
