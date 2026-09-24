<!-- Archived verbatim 2026-09-24 from subagent af44b0238ad7dfe0c of session 8f86dec2 (final message). -->

# Lane B (refutation) final report: juniper-ml#2059 (T1) and juniper-ml#2032 (T2)

Everything was run against `origin/main` `4ab6da58`, with siblings from `git archive` of their `origin/main`: canopy `e9053227`, data `3a76a4c5`, cascor `0e016a7c`, recurrence `db41e77e`, deploy `d589dd95`. The register at `origin/main` is byte-identical to the round-3 commit `b8b24b41`; the diffs b8b24b41 → f10fd681 → 8541f4fe → main are all empty. All scripts and outputs are in the scratch dir `…/scratchpad/r42/ml-laneB/`.

## Verdicts
- **T1 (#2059): REFUTED.** The wiring works. What fails is the guarantee and the reasoning behind it:
  - The gate stays green on 7 of 7 regressions that keep the marker text, including the exact pre-#660 constructor.
  - The PR says "no behavioural test can tell the `matched` loop from `any(...)`". canopy#660's own test does exactly that.
  - The canopy sites have never run in CI.
- **T2 (#2032): REFUTED.** The round-3 fix added three new false statements. The register also merged already stale: cascor#678 and canopy#678 merged before #2032 did.

## Findings, most severe first

**T1-1, MEDIUM. The gate stays green when the guarded property breaks but the marker text survives.**
- **Where:** the sites at `tests/test_service_fork_drift.py:183-189` and `:210-217`. `guard_is_present` does a whole-file substring match (`:282-291`).
- **Evidence:** `python3 t1_marker_preserving_mutations.py`. It ran seven mutations against both copies:
  - M1 `break` after a match
  - M2 `return True` inside the loop
  - M3 `{k.strip() for k in … if isinstance(k, str)}`
  - M4 the filter gates `_enabled` only
  - M5 the loop commented out and `any()` returned
  - M6 `set(api_keys) if api_keys else set()` with the markers moved into a docstring
  - M7 `any()` returned, with the loop left below as dead code
- **Result:** the gate was GREEN on all 7, for service-core (`SharedPackageGuardTest`) and for canopy (`ServiceForkDriftTest`, FORCE_LOCAL). A behavioural check caught all 7 on service-core. It reported either "compare SHORT-CIRCUITS (compared 1 of 3 keys)" or "blank+real keys ACCEPT an empty X-API-Key".
- **Why the PR's own check missed this:** all three of its mutations delete a marker string (`util/ad-hoc/2026-09-23_verify_shared_package_guard_sites_are_not_vacuous.py:32-36`). That only shows the markers are needed, not that they are enough.
- **Fix:**
  - Scope the markers with `ast`: in `APIKeyAuth.validate`, a `for` loop with no `break`/`return` in it followed by `return matched`; `k.strip()` inside the comprehension's `if` clause.
  - Or add behavioural arms (next item).
  - Add mutations that keep the marker text to the non-vacuity script.

**T1-2, MEDIUM. The premise "no behavioural test can tell them apart" is false.**
- **Where it appears:**
  - #2059's body: "no behavioural test can tell the `matched` loop from `any(...)`"
  - `tests/test_service_fork_drift.py:205-209`: "it is the ONLY possible one"
  - the register §5.1 APD-CASCOR-005 row: "No behavioural test pins this, and none can"
  - the register ECO-008 entry at `:1540`
- **Evidence:**
  - canopy `src/tests/unit/test_security.py`, `test_validate_compares_every_key_even_when_the_first_matches`, merged with canopy#660. It counts `compare_digest` calls over 3 keys and asserts all 3 are compared.
  - My oracle catches M1, M2, M5 and M7 the same way.
  - data's and cascor's spy tests use one key, so they cannot tell the two apart.
- **Fix:** port canopy's spy test into `juniper-service-core/tests/test_security.py` (and into data and cascor), then correct those sentences.

**T1-3, MEDIUM. The only place the canopy sites run has not run since the merge, and an earlier failing step can skip it.**
- **Evidence:**
  - `gh run list --workflow docs-full-check.yml`: the latest run is 2026-09-21 (`52571621`). #2059 merged 2026-09-23T22:57Z, and nothing has been dispatched since.
  - The register's ECO-008 ruling text requires "the workflow dispatched after it" (anchor: "a label, not yet a check").
  - The drift step (`docs-full-check.yml:256-259`) has no `if: always()`. Run `34091123580` (2026-09-07) shows "Validate all documentation links=failure | Lint service-fork security-guard drift=skipped".
  - Neither `docs/REFERENCE.md:2974` ("It bites in `docs-full-check.yml`") nor `:2971` mentions any of this.
- **Fix:** dispatch Docs Full Check; add `if: always()` to the drift step, or move it into its own job; document it.

**T1-4, LOW. A failed juniper-data or juniper-cascor clone still silently blinds every guard, canopy's included.**
- **Evidence:** `t1_clone_failure_controls.py`.
  - Scenarios C and D (data or cascor missing), under both FORCE_LOCAL and `GITHUB_ACTIONS=true`: exit 0, "OK (skipped=3)", with "ecosystem root not found".
  - The fail-loud claim at `:79-87` and in `docs/REFERENCE.md:2971` covers canopy only. Scenario B (canopy missing) does fail, with 2 failures.
- **Fix:** in docs-full-check, set an env var that turns the missing-root skip in `_require_cross_repo` into a failure.

**T1-5, LOW. The service-core site guards source code that is not what's deployed.**
- **Evidence:**
  - `t1_published_wheel_check.py`: the juniper-service-core 0.6.0 and 0.7.0 wheels both report `nonshortcircuit-key-compare: ABSENT` and still contain `any(hmac.compare_digest`.
  - 0.7.0 is the latest on PyPI, and `juniper-recurrence/juniper-recurrence/requirements.lock:74` pins `juniper-service-core==0.7.0`.
  - So the only production consumer (register §2.1) still short-circuits.
  - The register's §2.3 table row ("Non-short-circuiting key compare … ~~`juniper-service-core`~~ — both fixed") is only true of the source.
- **Fix:** record "fixed on main, unreleased"; release service-core.

**T1-6, LOW. A new claim in the guard summary is false.**
- **Where:** `tests/test_service_fork_drift.py:168`: "a key no ASCII header can carry".
- **Evidence:** `t1_h11_ascii_whitespace_probe.py`. On h11 0.16.0, `\x1c\x1c` is delivered intact and `str.strip()` empties it (httptools refuses it). canopy#678 recorded this 28 minutes before #2059 merged.
- **Fix:** "a key of spaces or tabs".

**T1-7, NIT. Stale wording around the gate:**
- `docs/REFERENCE.md:2976` says "all six copy-drift guards"; there are 7. This is in the section the PR edited.
- The `ci.yml:493-499` and `docs-full-check.yml:248-255` comments still describe only data and cascor, and never mention `SharedPackageGuardTest`.
- `release-train.yml` also clones the siblings, so "the only job that clones the siblings" is loose.
- `JUNIPER_DRIFT_TEST_FORCE_LOCAL=0` turns the tests on, since any non-empty value does.
- The docstring's "Five register findings" (`:12`) is stale.

**T2-1, MEDIUM. The round-3 fix added a false date claim.**
- **Where:** register `:183` and `:242`: "the `OPTIONS`/CORS row was the last of the original fifteen to close (2026-08-20)".
- **Evidence:**
  - The fifteen cover all three §2.3 groups (`:240`).
  - APD-CCLIENT-001 closed later: cascor-client#143 merged 2026-08-28T13:42Z. The register's own §2 list says "(2026-08-28) `APD-CCLIENT-001`", and `:287` says "This was the last open row in this table".
  - CCLIENT-005, DCLIENT-004 and CCLIENT-006 also closed after 08-20.
- **Fix:** "the last of the ten original copy-drift rows".

**T2-2, MEDIUM. The round-3 fix added a false history of the guards.**
- **Where:** `:242`: "`ENFORCED` — promoted from `KNOWN_GAP`, except the compare row".
- **Evidence:**
  - The gate's first version, `d1ce9958` (ml#1103, merged 21:49Z), already had streaming-body-cap, content-length-parse-guard and narrow-serialization-error at `status=ENFORCED`. data#261 and cascor#516 had merged earlier that day.
  - cors-outside-auth arrived in #1201 and was never a `KNOWN_GAP` row: the test file says it was "tracked unencoded".
  - Only blank-api-key-filter (#1145) and pre-auth-throttle (#1130) were ever promoted from `KNOWN_GAP`.
- **Fix:** state the history as "two promoted, five entered as ENFORCED".

**T2-3, MEDIUM. Claims that were already false when #2032 merged.**
- **cascor#678** (`0e016a7c`, merged 20:22Z, titled "APD-CASCOR-013, APD-CASCOR-008") merged 2h12m before #2032 did:
  - `register_open_set.py` still lists both rows as OPEN.
  - The register never mentions cascor#678.
  - Row -013 still says "written at one line and **never cleared**". cascor `manager.py` now writes it at `:2557`, `:3857` and `:4585`.
- **canopy#678** merged 22:29Z, 5 minutes before #2032:
  - The ECO-008 entry's "(2) That CHANGELOG entry omits the largest thing that opens … canopy's own record does not say it" became false. canopy's CHANGELOG now says "This is the largest thing that opens."
  - It also fixed the "WARNING's own defects" that the register routed to canopy.
- **Fix:** a register PR with the five-touch close of -008 and -013, plus a correction to the ECO-008 entry.

**T2-4, MEDIUM. Claims false on main since #2059 merged, 23 minutes after #2032. No follow-up PR is open (`gh pr list`).**
- **What is now false:**
  - The ECO-008 row headline: "the drift gate cannot express it".
  - The anchors "`_FORK_REPOS` … at `:59`" and "assertion at `:285`". On main, `:59` is `KNOWN_GAP = "KNOWN_GAP"`, `_FORK_REPOS` is at `:68`, and the assertion is at `:338`.
  - `:242`: "service-core's copy of the compare is not a gate site at all".
  - "`_FORK_REPOS` is read in exactly three places".
  - `:1539-1541`: "watched by nothing: it is not a gate site".
- **What is missing:** the owner's 2026-09-23 ruling "Yes, same gate PR", which made service-core a site, is not recorded anywhere in the register.

**T2-5, LOW. A contradiction the round-3 fix left in a sentence it edited.**
- `:22` still says "recommends a drift check that does not exist".
- `:244` says "That drift check now exists".

**T2-6, LOW. A contradiction inside `:242`.**
- The sentence says "A drift check against `juniper-service-core` would catch these — all but the compare row".
- The same paragraph mentions "the two rows with no shared implementation", and their table cells read "(nowhere)". A check against service-core cannot catch those two either.

**T2-7, LOW. The X-B ruling as written goes beyond the recorded options.**
- **Where:** `:1459-1462`: "set when data is bound (… inline data sets null), kept … by `reset()`".
- **Evidence:** the only record of the options (#2032's body) says "Follow the loaded data … a run on retained partial data says so" versus "null because nothing was fetched". It is about Stop → Start and does not mention `reset()`.
- The X-A entry marks its own reading as "this entry's reading, not the owner's words"; this entry has no such marker.
- cascor#678's comment on `reset()` cites "owner ruling 2026-09-23" for this behaviour.
- **Fix:** add the reading marker, or confirm with the owner.

**T2-8, LOW. The route count names no commit.**
- **Where:** `:1550`: "measured: 55 method-path pairs … the 25 parameterless GETs". #2032's body repeats "all 55".
- **Evidence:** that sweep ran on canopy `26e0546f`. `@app.get("/api/selection")` was added before `48074653`, the commit #660 merged onto (`t2_route_decorators.sh`), so canopy's CHANGELOG correctly says 56 and 26.
- **Fix:** pin the count to `26e0546f`, or restate it as 56 and 26.

**T2-9, NIT. Small anchors and quotes overtaken by canopy#678:**
- `:1466` cites "(`:74`)" and "(`:53`)" without pinning a commit; on canopy main those lines are a comment and a docstring.
- The quote "disabled when unset" (`:1522`) has been rewritten by canopy#678.
- "both uvicorn parsers reduce an all-whitespace `X-API-Key` to empty" (`:1506-1507`) holds for spaces and tabs only.

## T2: round-3 findings

| Round-3 finding | Verdict |
|---|---|
| M1: "Until #660 merges", and the stale "still" anchors | FOLDED CORRECTLY. The rows are pinned to `48074653`, which I verified. `:1466` was left unpinned, and #2059 has since overtaken this text (T2-4). |
| M2: the "fails CLOSED" reason, and the pointer at `:1501` | FOLDED CORRECTLY. The truthiness test maps only `""` to None. |
| M3: -013's headline and row | FOLDED CORRECTLY, but stale after cascor#678 (T2-3). |
| L1: "fifteen" at `:22` | FOLDED CORRECTLY, but the same sentence keeps "does not exist" (T2-5). |
| L1: "CORS last one open" | **FOLDED WRONGLY** (T2-1). |
| L1: "promoted to ENFORCED" | **FOLDED WRONGLY** (T2-2). |
| L1: "a drift check against service-core would catch these" | **FOLDED WRONGLY, in part** (T2-6). |
| L2: "True when written" | FOLDED CORRECTLY. The round-40 handoff's §4 says "an owner decision is owed". |
| L3: the skip env var | FOLDED CORRECTLY. The skip check is at `auth_posture.py:106-112`, before `real_keys` and `require_auth`, and in the same order in both published wheels. |
| L4: the quote | FOLDED CORRECTLY, then overtaken by canopy#678 (T2-9). |
| L5: Helm | FOLDED CORRECTLY. `k8s/` sets no `REQUIRE_AUTH` anywhere. |
| L6, L7, L8 | FOLDED CORRECTLY. |
| L9 a, b, c | FOLDED CORRECTLY. `_docs_enabled` is still at canopy main `src/main.py:504`; `/api/csrf` is at canopy `48074653` `src/main.py:658-686`. |

## Attacks that did not land
- **`SharedPackageGuardTest` really is always on and does gate merges.**
  - `ci.yml` has no `paths` filter, and `:500` runs the file.
  - "Regression Tests (Python 3.12/3.13/3.14)" are required checks in ruleset 13805432.
  - The test has no skip path and reads no env var.
- **canopy#678 did not move the markers.**
  - They are at canopy `src/security.py:82` and `:112-116`.
  - Each marker occurs exactly once at each of the four sites, so today no comment or docstring satisfies one.
  - Every canopy key check goes through `APIKeyAuth.validate`.
- **The PR's own claims reproduced.**
  - A missing canopy checkout FAILS, with 2 failures.
  - Pre-#660 canopy fails exactly the two canopy subtests.
  - Against current sibling main: 11 tests OK. Without the opt-in: 11 OK, 3 skipped.
- **Register tools all pass:** 126 rows, 99 fixed, 27 open; the cross-check reports AGREE 99/99/99; the four suites run 44 tests OK with 3 skipped. By design, none of them can see the problems above.
- **These register facts check out:**
  - `3a6dea95`'s commit message.
  - Auto-merge armed at 13:17:53Z.
  - The four services that call `enforce_auth_posture`.
  - The round-40 handoff's §4.
  - Round 3 added no intra-document `:NNN` citations.

## What this evidence cannot support
- **Canopy mutations:** the behavioural check ran on service-core only, because canopy's module imports `secrets_util`. For canopy I show only that the gate stays green, not that canopy's own suite would catch each mutation.
- **Not verified:** ECO-008's "(3) cross-site `text/plain` POST … 200" claim. It needs a live canopy.
- **The owner's option wording** for X-B and ECO-008 is not in any artifact I found, so T2-7 is a provenance gap, not proof of an unauthorized ruling.
- **Docs Full Check was not dispatched** (read-only), so the canopy sites are still unobserved in CI. The local equivalent passes.
- **Mutation realism:** M1–M7 are constructed. I claim they are plausible regressions, not that anyone has made one.

**Slips:** none. I printed no env vars, tokens or credentials, and sent nothing externally apart from public PyPI and GitHub reads. I wrote nothing outside the scratch dir.
