<!-- Archived verbatim 2026-09-24 from subagent a9498cdd07e19a630 of session 8f86dec2 (final message). -->

## Lane A final report: juniper-ml#2059 and #2032's round-3 corrections

`origin/main` moved from `4ab6da58` to `dcfc024f` during the run (#2067, #2072). Neither commit touches any target file (empty `git diff --stat`), so every line number below holds at both. Sibling `main`s used: canopy `e9053227`, cascor `0e016a7c`, data `3a76a4c5`. Data later moved to `39d1cab` (#435), which leaves all three data gate files unchanged.

### Verdicts
- **T1 (#2059): REPRODUCED, with three caveats.** Every numbered test claim re-derives, and every mutation that removes a guarded construct at a new site is caught and attributed to the right guard. The caveats:
  - The cross-repo half has **never run in CI since the merge**.
  - Three regressions that keep the marker text pass the gate silently.
  - Two claims about what watches these guards are false.
- **T2 (`b8b24b41` in `…DEFECT-REGISTER.md`): mostly REPRODUCED, with two new false statements.** The file on `main` is byte-identical to `b8b24b41`, the counts reproduce, and every round-3 finding was folded in. But two of the corrections **introduced new false statements**, one pre-existing false claim survives in an edited line, and several sentences went stale within hours as later PRs merged.

### Claims table

| # | Claim | Source | What I measured | Result |
|---|---|---|---|---|
| 1 | 11 tests OK (skipped=3) locally | #2059 body | `unittest` on the `main` extraction: `Ran 11 … OK (skipped=3)` | REPRODUCED |
| 2 | Cross-repo run against every sibling's `origin/main`: OK, 0 skips | #2059 body | Synthetic root built from archives; the probe confirmed it resolved to my scratch root. 11 OK, 0 skipped, 18 of 18 enforced subtests PASS. Also OK at the PR's own cited SHAs (canopy `0254a7ec`, data `90ad035`, cascor `f7a6d57`, ml `f770fe5e`) | REPRODUCED |
| 3 | Pre-#660 canopy `48074653` fails exactly the two canopy guards | #2059 body | `48074653` is `3a6dea95^`, with the identical `security.py` blob. failures=2, exactly `blank-api-key-filter@canopy` and `nonshortcircuit-key-compare@canopy`. The defect shapes are present (`:53` bare `set(api_keys)`, `:74` `any(...)`) | REPRODUCED |
| 4 | Vacuity script: `PASS: 3 mutations` | #2059 body | Same output from my extraction | REPRODUCED |
| 5 | A missing canopy checkout FAILS `test_fork_files_named_by_the_registry_exist` instead of skipping | #2059 body, test `:79-87` | 2 FAIL plus 2 subtest skips. True at unit level only; CI would not show it (Finding 1) | REPRODUCED (unit level) |
| 6 | juniper-ml sites read this checkout, and the always-on test needs no sibling | #2059 body | `_site_path` `:294-300`. The default run fails on S1/S2/S3. The CI log for `f5222f9d` shows the test ran ok while the 3 cross-repo tests skipped ("ecosystem root not found"). `ci.yml` has no path filter | REPRODUCED |
| 7 | Site paths and markers exist at `origin/main` and point at the named construct | test `:183-217` | canopy `src/security.py:82` (filter), `:112`/`:116` (loop); service-core `security.py:45`, `:73`/`:77`. Each marker occurs exactly once per file | REPRODUCED |
| 8 | Service-core's copy "was watched by nothing" | #2059 body; test `:187-188` | Service-core's own `test_security.py:63` catches filter removal, strip removal and enabled-from-raw. It does not catch `any()` or `break` | REFUTED for the filter, REPRODUCED for the compare |
| 9 | "No behavioural test can tell the `matched` loop from `any(...)`" | #2059 body; test `:205-209`; `…DEFECT-REGISTER.md:1580` | A spy on `compare_digest` counts 3 calls vs 1. Canopy #660's own `test_validate_compares_every_key_even_when_the_first_matches` fails on both `any()` and `break` | REFUTED |
| 10 | Canopy configures exactly one key | test `:212-214` | `[api_key] if api_key else None` | REPRODUCED |
| 11 | pre-commit passes | #2059 body | PR checks: Pre-commit 3.12/3.13/3.14 pass (not re-run locally) | REPRODUCED via CI |
| 12 | Register on `main` equals `b8b24b41` | brief | Blob `45d34c6e` at `b8b24b41`, `6c60f154`, `f10fd681`, `8541f4fe` and `main` | REPRODUCED |
| 13 | `126 rows \| 99 fixed \| 27 open`; crosscheck AGREE | `b8b24b41` message | Both scripts, run from the extraction | REPRODUCED (marker counts only) |
| 14 | §2.3 has 16 entries, 15 before the compare row (`:22`, `:240`) | register | 11 + 3 + 2 unique ids in §2.3's tables | REPRODUCED |
| 15 | CORS closed 2026-08-20; the compare row closed 2026-09-21 (`:183`) | register | data#273 09:00:00Z and cascor#540 09:00:20Z; cascor#659 and ml#1974 on 09-21 | REPRODUCED |
| 16 | CORS was "the last of the original fifteen to close" (`:183`, `:242`) | register | Five of the fifteen closed later (Finding A) | REFUTED |
| 17 | Service-core lacked the compare guard until it was fixed alongside the forks (`:242`) | register | `ea24a19a^` still has `any(hmac…)`; #1974 merged the same day as cascor#659 | REPRODUCED |
| 18 | Every guard was "promoted from KNOWN_GAP, except the compare row" (`:242`) | register | Git history of the test file (Finding B) | REFUTED |
| 19 | The truthiness test maps only `""` to None, so a whitespace env key enabled auth (`:990`, `:1278`) | register | canopy `48074653` `src/security.py:265-267`; `src/secrets_util.py:38-65` strips a file, not the env var | REPRODUCED |
| 20 | WS `?api_key=` is never trimmed; all three WS endpoints admit keyless connections at the same gate | register | `src/main.py:712`, `:713-714`; exactly three `@app.websocket`, each with `allow_browser_auth=True` (`:776`, `:913`, `:3576`) | REPRODUCED |
| 21 | #660 merged 2026-09-23 as `3a6dea95` and fixed both divergences; `:53`/`:74` are anchored at `48074653` | register | Merged 19:16:49Z; `3a6dea95` `src/security.py:76` and `:106-110` | REPRODUCED |
| 22 | Row 1278's ml anchors `:59` / `:285` | register | Correct at `27e1541d` and `b8b24b41`; `:68` / `:338` on `main` | STALE on `main` |
| 23 | APD-CASCOR-013 narrowing; inline data reports null by design; fetched partial data says so (`:1285`, `:1449-1451`, `:1460-1462`) | register | cascor #678 as merged: `manager.py:2542-2557`, `:2897-2901`, `:4585` | REPRODUCED |
| 24 | "Fetches lazily, on the first dataset request, so no startup dependency" (`:1353-1355`) | register | Faithful to the ruling text. The shipped code reads only when the resolver consults the set, and auto-start is a boot-time read (`manager.py:72-91`) | REPRODUCED (NIT) |
| 25 | "The ruled option is itself a per-request form; the other two were not offered" (`:1368-1370`) | register | "Per-request" holds by reading. What the owner was offered exists in no file | NO ARTIFACT (options) |
| 26 | Handoff §4 recorded a decision owed; ECO-008 was filed 2026-09-22; APD-ML-002..006 still need a decision (`:1403-1408`) | register | `HANDOFF_2026-09-21_…round-40-….md:166-171`; commit `836393cf` (#2005); `HANDOFF_2026-09-22_structure-screen-….md:122`, and no ruling for them in the register | REPRODUCED |
| 27 | `/api/csrf` has no CSRF check and admits a request with no Origin (`:1508-1509`) | register | `48074653` `src/main.py:658-692` | REPRODUCED |
| 28 | The posture-check skip returns before `require_auth`; the log strings (`:1517-1519`) | register | service-core `auth_posture.py:106-112`, `:114`, `:119` | REPRODUCED |
| 29 | Docstring "disabled when unset"; Compose defaults REQUIRE_AUTH true, Helm sets none, demo/dev set no key (`:1522-1528`) | register | canopy `src/security.py:5`; juniper-deploy `d589dd9` `docker-compose.yml:690`, `:696`, demo `:791`, dev `:882`, `canopy-deployment.yaml:78` | REPRODUCED |
| 30 | `requests` refuses a whitespace key header (`InvalidHeader`); `_docs_enabled` tests the raw value (`:1529-1533`) | register | requests 2.34.2 raises `InvalidHeader`; canopy `src/main.py:504`, `:511-513` | REPRODUCED |
| 31 | Auto-merge was armed at 13:17:53Z and never re-armed; `3a6dea95`'s message predates its own correction (`:1544-1548`) | register | Timeline: `auto_squash_enabled` 13:17:53Z, then commits at 13:21:15, 13:21:40 and 18:59:51, no re-arm; the message text matches | REPRODUCED |
| 32 | "The merge did not wait for" the second validation round | register | Nothing on GitHub records the round's timing | NO ARTIFACT |
| 33 | The CHANGELOG entry omits the key-gated routes opening; "55 pairs, 27 state-changing, 25 parameterless GETs all 401 before and 200 after" (`:1548-1551`) | register | The omission holds at `3a6dea95` (`CHANGELOG.md:376-411`). The route census gives 56 / 27 / 26 at `48074653` and `3a6dea95`: 26 × 401 before, 26 × 200 after with the lifespan running | Phenomenon REPRODUCED; counts off by one (Finding E) |
| 34 | The owner was told "auth is off everywhere" | register | The quote appears in no file except the register | NO ARTIFACT |
| 35 | A cross-site `text/plain` POST to `/api/dataset/generate` returns 200 in the auth-off profile, not introduced by #660 | register | 200, and the dataset actually changed from 200 to 40 samples, at both `48074653` and `3a6dea95` | REPRODUCED |
| 36 | #660's blank-key WARNING fires before logging is configured, and its advice is wrong for a blank file | register | `3a6dea95` `src/security.py:297-309`; called at import (`src/main.py:528`) while `configure_logging` runs in the lifespan (`:310`) | REPRODUCED |
| 37 | Cascor `security.py:68,72` and service-core `:73,77` (`:1580`) | register | Line numbers match | REPRODUCED |
| 38 | Every finding in `04-ml2032-round3-corrections.md` was folded in | `b8b24b41` message | Each maps to a hunk (Medium 1 → hunks 5/6/12/14; Low 1 → 2/3/4; Low 2 → 9; Low 3-5 → 12; Low 6 → 11; Low 7 → 1; Low 8 → 7; nits → 8/12) | REPRODUCED; two fixes are themselves wrong (A, B) |

### Findings (line numbers at `origin/main`)

**1. MEDIUM (T1): the cross-repo gate has never run in CI since #2059 merged, and can be skipped outright.**
- **Evidence:**
  - `.github/workflows/docs-full-check.yml:62-65` runs only on the Monday schedule and manual dispatch. The last run was 35568824732 at 2026-09-21T06:30Z, before the merge at 2026-09-23T22:57Z. The first real run will be 2026-09-28.
  - The drift step (`:256-259`) has no `if:`. On 2026-09-07 (run 34091123580) the link check (step 6) failed and the drift step (11) was skipped.
  - With canopy absent, doc-tools fails the link check on `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md:7` (measured with the in-repo 0.1.2). So in CI the "missing canopy FAILS the file-existence test" design would never execute. The job goes red for a doc-link reason while all 18 sites go unchecked that week.
- **Fix:** add `if: ${{ !cancelled() }}` to the drift step, or move it before the link check. Dispatch the workflow once now.

**2. LOW (T1): regressions that keep the marker text pass the gate.**
- **Evidence:** at both new sites, a `break` after `matched = True`, a `matched = any(...)` assignment, and `self._enabled = bool(api_keys)` each leave the gate at 11 OK, 0 skips.
  - The comment at test `:199-203` ("walk to the end, then return") claims more than the markers check.
  - Canopy's own suite catches all three. Service-core's suite misses both compare variants, so for the canonical copy nothing catches them.
- **Fix:** port canopy's spy test into `juniper-service-core/tests/test_security.py` (and into data and cascor), or make the gate check the syntax tree.

**3. LOW (T1 and T2): the claim that no behavioural test can distinguish the loop from `any()` is false.**
- **Where:** test `:205-209`, the #2059 PR body, and `…DEFECT-REGISTER.md:1580`.
- **Why it matters:** #660 — the very PR line 1580 now cites — ships a behavioural test that distinguishes them. This premise is what justified choosing a source marker as the instrument.
- **Fix:** correct the text and add the spy test.

**4. LOW (T1): "Unwatched until then" is wrong for the blank-key filter.**
- **Where:** test `:187-188`.
- **Evidence:** service-core's `test_security.py:63` (from #993) runs in `ci-service-core.yml` and catches that filter being removed. Only the compare loop was unwatched.
- **Fix:** scope the comment to the compare guard.

**5. NIT (T1): two workflow comments still name only data and cascor** (`docs-full-check.yml:248-249`, `ci.yml:493-494`). Separately, and pre-existing: `test_known_gaps_are_still_open_or_get_promoted` iterates zero guards, so it passes vacuously.

**A. MEDIUM (T2, introduced by `b8b24b41`): CORS was not the last of the original fifteen to close.**
- **Where:** `…DEFECT-REGISTER.md:183` and `:242`.
- **Evidence:** five of the fifteen closed after CORS on 08-20:

  | Id | PR | Merged |
  |---|---|---|
  | APD-DATA-004 | data#275 | 08-21 |
  | APD-DCLIENT-004 | data-client#165 | 08-24 |
  | APD-CCLIENT-005 | cclient#129 | 08-24 |
  | APD-CCLIENT-006 | cclient#135 | 08-25 |
  | APD-CCLIENT-001 | cclient#143 | 08-28 |

  The register's own line 177 already lists APD-DATA-004 after the CORS pair.
- **Fix:** "last of the original copy-drift rows (2026-08-20); the last of the fifteen was APD-CCLIENT-001 (2026-08-28)".

**B. MEDIUM (T2, introduced by `b8b24b41`): only two guards were ever promoted from `KNOWN_GAP`.**
- **Where:** `…DEFECT-REGISTER.md:242`.
- **Evidence:** only `pre-auth-throttle` (#1130) and `blank-api-key-filter` (#1145) were ever `KNOWN_GAP`. Five entered already `ENFORCED`:
  - `streaming-body-cap`, `content-length-parse-guard` and `narrow-serialization-error`, at gate creation (#1103);
  - `cors-outside-auth` (#1201);
  - the compare (#1974).
- **Fix:** state two promoted and five entered already enforced.

**C. LOW (T2): the register went stale as later PRs merged; each sentence was true when written.**
- **#2059 widened the gate**, so these are now false: `:242` ("not a gate site at all"), `:990` ("Widening … is follow-up"), `:1278` ("no guard can reference canopy", anchors `:59`/`:285`, "stays open for the gate half") and `:1580` ("cannot yet express it").
- **cascor#678**, merged 8 minutes after `b8b24b41`, implements APD-CASCOR-008 and -013, which are still marked open.
- **canopy `05f2dfc2`** addressed the CHANGELOG omission and both WARNING defects.
- **Fix:** the pending register PR that #2059's body promises should close or annotate these, and pin the ml anchors to a SHA.

**D. NIT (T2): smaller wording issues.**
- `:1278` "Over HTTP the reading holds as written": the conclusion holds, but the stated reason does not (auth was enabled and refused every caller).
- `:1353-1355`: the laziness wording is broader than what the code does.

**E. NIT (T2): the route counts are off by one at the commits the entry pins.**
- **Where:** `…DEFECT-REGISTER.md:1550-1551`.
- **Evidence:** 55 / 25 is correct at #660's base `26e0546f` (per `reports/2026-09-24_defect-register-round-42/canopy660-round2-validation.md:21-22`). `@app.get("/api/selection")` was added before `48074653`, so the counts there and at `3a6dea95` are 56 / 27 / 26.
- **Fix:** pin the commit the count was taken on, or restate it as 56 / 26.

### Instrument adequacy
- **Could each measurement have come out differently if the claim were false?** Yes, for the gate:
  - Canopy filter: removing it (C1) or dropping its `strip()` (C2) each fail `blank-api-key-filter@juniper-canopy`, and nothing else.
  - Canopy compare: replacing the loop with `any()` (C3) fails `nonshortcircuit-key-compare@juniper-canopy`.
  - Service-core: S1, S2 and S3 each fail both the cross-repo subtest and `SharedPackageGuardTest`, including in the default run with no opt-in.
  - The pre-#660 negative control fails exactly 2 subtests; a missing canopy checkout gives 2 FAILs.
  - Limits: C4/S4 (`break`), C5 (`matched = any(...)`) and C6/S5 (enabled from raw) are NOT caught.
- **Vacuity checker:** with an always-true matcher it reports FAIL; with the compare guard reduced to a single marker it reports M3 as VACUOUS. So it discriminates.
- **Register scripts:** un-marking a fixed row and marking an open row fixed are both detected. A stray `**FIXED` token in the wrong cell fools `register_open_set.py` (100/26) but not the crosscheck. A phantom open row is invisible to the crosscheck (127/28 vs AGREE). So "27 open" rests on one instrument that counts markers, and neither script can see a marker that has gone stale against code.
- **Route census and suites:** the census uses the middleware's own exemption predicates and imports from the scratch trees. The before/after flip, and the canopy and service-core suites going red only under mutation, prove the mutated copies were the ones loaded.

### What this evidence cannot support
- That the cross-repo gate passes in CI (it has not run there), or that the PyPI build of doc-tools behaves like the in-repo 0.1.2 I used.
- Anything about the owner's words or the options put to the owner: rows 25, 32 and 34 have no artifact.
- Deployed canopy behaviour: a checkout is not a deployment.
- Route totals under a different counting convention (I excluded HEAD and counted only HTTP routes).
- The h11 / httptools header-stripping behaviour, which I did not re-measure. It underlies the unchanged "Over HTTP" reading.

### Slips and hygiene
- No environment variables or credentials were printed, and nothing was sent externally.
- I edited no repository file. My only repo-side effects were `git fetch` into the repos' `.git` directories.
- The `hazy-beaming-map` worktree now shows a modified `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` and new untracked files under `reports/2026-09-24_defect-register-round-42/`. They are **not mine**; they come from concurrent sessions.
- **Documents referenced:** `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, `reports/2026-09-24_round-42-post-merge/04-ml2032-round3-corrections.md`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md`, `reports/2026-09-24_defect-register-round-42/canopy660-round2-validation.md`, `notes/JUNIPER_2026-05-09_JUNIPER-CANOPY_FRONTEND-ISSUES-PLAN.md`.
- **Changed:** none in any repo. Probe scripts and logs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/ml-laneA/`; the ones that matter are `probe_run.py`, `mutate.py`, `svc_behavioural_mutations.py`, `canopy_behavioural_mutations.py`, `canopy_route_census.py`, `canopy_textplain_probe.py`, `register_script_mutations.py` and `guard_status_history.py`.
