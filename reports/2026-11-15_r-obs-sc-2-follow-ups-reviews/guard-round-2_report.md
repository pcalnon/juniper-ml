I found 3 false statements (BLOCKER by your definition), 1 MAJOR and a handful of MINOR/NIT items. All of them are text fixes in the register, REFERENCE.md and comments. The guard itself, the mutation script's 88 forbidden-form mutations, the counts you listed, and every PR number, sha and date check out.

Paths below are relative to `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-a4c8d9de35bfc0d67/`.

## Findings

**1. BLOCKER (false statement) — register §5.1, `APD-SVCCORE-004` row (L1743), new parenthetical**
- **Text:** "The three forks, which import none of this package".
- **Evidence:** all three forks import the package root:
  - juniper-data `juniper_data/api/app.py:14` and juniper-cascor `src/api/app.py:17`: `from juniper_service_core import enforce_auth_posture`.
  - juniper-canopy `src/main.py:323` and `:337` import `enforce_dependency_floors`, `AuthPostureError` and `enforce_auth_posture`.
  - The register's own §4.2 preamble says every production import is package-root only.
- **Fix:** "which import none of this package's `security` module" (the §4.9 row already says it this way).

**2. BLOCKER (a count this change makes false, and the ID sweep misses it) — register §2, L181**
- **Text:** "…in a service the gate walks for two guards only". canopy is now a site of three guards (test L394, `_retry_after_sites("juniper-canopy", …)`).
- **Why it was missed:** the sentence names `APD-ECO-009`/`-010`, not `-016`. It is the exact case §1 warns about ("re-read any sentence that counts"). It also makes the CHANGELOG's "moves every count it changes" (L75) untrue.
- **Fix:** "…the gate then walked for two guards only (three since 2026-11-15, when canopy's `RateLimiter` became a site of `retry-after-rounds-up`)".

**3. BLOCKER (false count) — register L183, new text**
- **Text:** "three canopy rows have joined it since, all open: …; and a fourth row, closed: `APD-ECO-016`".
- **Evidence:** `APD-ECO-008` also joined since (filed 2026-09-22, closed 2026-09-24; §2.3's "seventeenth", L240). So did `APD-CASCOR-005`, which the same sentence's tail mentions.
- **Fix:** "four canopy rows have joined it since — `APD-ECO-008`, closed 2026-09-24, and `APD-ECO-009`, `-010`, `-012`, all open — and one fork row, closed: `APD-ECO-016` …".

**4. MAJOR — the guard's blind spots are listed incompletely**
- **Where:** the register §4.9 row (L1329, "It still reads code…: arithmetic after a correct round-up, a second helper, and the header formatting… get past it") and `docs/REFERENCE.md:3736` ("It still cannot see …").
- **The missing class:** inside a scope the markers only prove the text is present. Any return path added beside the kept markers passes, unless it spells one of the eight forms. That is exactly the shape the F mutations build.
- **Evidence:** I ran the gate's own `guard_is_present` in memory (`…/buzzing-growing-whale/tmp/s2/review-eco016/probe/blind_spots.py`). These all pass on the juniper-ml, juniper-data and juniper-canopy copies:
  - helper `if left < 1: return 0` placed before the kept formula. That is APD-ECO-016's own `Retry-After: 0`.
  - an extra early `return (False, 0, 0)`, or `return (False, 0, self._window - (now - window_start))`, in `check`.
  - the allowed-path marker kept under `if False:`, with the live return unrounded.
  - `max(1, floor(left))` with `floor` imported bare.
  - `[int(left)][0]` in the throttle (juniper-ml and juniper-data, which have one).
- **Related:** `REFERENCE.md:3730` says "The exceptions are `throttle-check-never-inserts` and `retry-after-rounds-up`". That reads as if the scoped guards cannot be passed by a regression that keeps its markers.
- **What the test comment says:** L382-383 has only the narrower "a wrong rounding the forbidden list does not name (`x - x % 1`)".
- **Fix:**
  - Add to both lists: "and any return path added beside the kept markers that skips the helper or rounds in a spelling the list does not name (a literal 0, an unrounded float, `[int(x)][0]`, a bare `floor(`)".
  - Reword L3730 to say that scoping narrows the gap but does not close it.
  - Widen the test comment's item the same way.

**5. MINOR — register §4.9 row: "No release of a fork carries its fix yet"**
- It is true today (latest releases are data v0.17.1, cascor v0.13.0 and canopy v0.9.0). But it is undated and about to go stale.
- Release proposals juniper-cascor#758 (v0.14.0, opened 2026-11-14T23:58:57Z) and juniper-canopy#818 (v0.10.0, 23:58:49Z) are open, and both bodies carry APD-ECO-016. juniper-data has no open proposal.
- **Fix:** date the sentence and name both proposals.

**6. MINOR — the ruling's record is never named**
- "(round 1, ruling 3, "Row + fix all three")" (L1329) and "The Overtoad ruled the same day" (L1260) name no document.
- The ruling is recorded verbatim in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md`, § "Round 1: the Overtoad's rulings", item 3. The `APD-ECO-015` precedent names its record.
- **Fix:** name that file and section in both places.

**7. MINOR — `APD-ML-008` row (L1325)**
- "(26 and four since 2026-11-15: APD-ECO-015's guard added two…)" implies the count was 16 until 2026-11-15. It was 18 from 2026-10-26. Fix: "18 since 2026-10-26; 26, canopy's four included, since 2026-11-15".
- Pre-existing in the same row: `ci.yml:500` is stale. Line 500 is `test_publish_testpypi_verify.py`; the drift command is at :590 on base and :593 now. Cite it by anchor instead.

**8. MINOR — nothing will notice when canopy gains a throttle**
- canopy is built with `throttle=False` (L394), and `throttle-check-never-inserts` has no canopy site.
- When `APD-ECO-010` closes by porting a `FailedAuthThrottle` into canopy, nothing prompts adding the canopy throttle sites. A truncating or inserting port would pass silently.
- **Fix:** say so in `APD-ECO-010`'s row. Better, add a tripwire that fails when `scoped_code(canopy, "FailedAuthThrottle")` stops being `None`.

**9. MINOR — "2026-11-15" is a prediction of the merge date**
- `date -u` printed Sun Nov 15 00:59:40 UTC 2026 (local 2026-11-14).
- Every "entered ENFORCED / filed 2026-11-15" goes wrong if the merge slips past 2026-11-15 UTC:
  - register L177, L242, L258, L1115, L1238, L1261, the §4.9 and §5.1 rows, L1790;
  - REFERENCE.md L3730, L3736, L3737, L9435;
  - CHANGELOG L62.
- **Fix:** re-date at merge, or cite the PR number.

**10. NIT — test L201: "The space and parenthesis prefixes keep `print(` out"**
- This is true only of `" int("` and `"(int("`. The two unprefixed forms still match (`probe/false_positive.py`):
  - `print(remaining)` → `int(remaining`
  - `print(self._window - elapsed)` → `int(self._window`
  - also `round(` matches `background(`, and `//` matches a URL in a non-docstring string literal.
- All of these fail closed (a false alarm, never a vacuous pass).
- **Fix:** reword to say which forms the prefixes protect.

**11. NIT — two passages describe a draft that never reached main**
- Test L192-194: "The looser `1, self._seconds_until_reset(` it replaced". Fix: "would also match".
- CHANGELOG L70: "no longer share one subtest header". On base, no copy has more than one site per guard. Fix: "do not share".

**12. NIT — test L15: "Five register findings are exactly this"**
- It sits in the paragraph this change rewrote; §2.3 now counts twenty-one (L240).
- **Fix:** update the count or drop it.

**13. NIT — mutation script**
- **(a) No expected counts.** If a site is dropped from the guard, L391-392 skips that copy's mutations silently. The PASS line then prints smaller numbers, and the docs' 151/88/130 drift unnoticed. Fix: assert 11 sites and 151 runs.
- **(b) L147** says "``main`` checks the list"; it is `_check` (L350-353).
- **(c) L9 and L226** cite "the round-1 review" with no filename. It exists only in `toasty-prancing-karp/tmp/s1/` (gitignored, deleted by `git worktree remove`). Archive it and name it.
- **(d) The PASS line (L419)** says the 5 pre-fix copies were each caught "at the one scope". Pre-fix runs are not scope-checked.

**14. NIT — register §5.1 row (L1787): "63 wrong roundings and bypasses"**
- R3 and T4 are neither; the script's own docstring (item 3) says they change no reachable result.

**15. NIT — `docs-full-check.yml` comment (L249-256)**
- "must hold identically in every copy" overstates. Each guard is asserted only at its own sites.
- "the per-PR ci.yml run exercises the registry structure" omits `SharedPackageGuardTest`, which the new `ci.yml` comment (L590-592) correctly includes.

**16. NIT (pre-existing, worsened)** — the register (`APD-ECO-008` §4.9 row) cites `_FORK_REPOS` at `:68` and its assertion at `:338` "on main". They are at :84 and :468 on base, and :99 and :563 now. Cite them by name.

**17. Informational** — this filing makes three statements outside the change set stale:
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md:1032` ("with no register row") and `:1175`;
- `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md:153` ("has no APD-ECO-016").
- Name them in the PR body.

## Checked and correct

**Register counts**
- `register_open_set.py`: 138 rows, 103 fixed, 35 open (base: 137, 102, 35). `register_status_crosscheck.py`: AGREE at 103/103/103.
- §4.9 has 42 rows, 22 fixed and 20 open; 42 − 16 = 26 rows of different provenance, and the enumeration sums to 26.
- Twenty-one §2.3 entries; nine guards (eight copy-drift plus `throttle-check-never-inserts`); "the other six" is 3 + 1 + 1 + 1; "an eleventh" service-core copy; 26 sibling sites.
- The new table rows have the same cell count as their headers.
- All five touches are present; there is no §3 detail entry to update.

**Facts checked with `gh` and git**
- canopy#817 `55ac2168` 01:02:07Z, cascor#757 `66b39a5c` 01:07:08Z, data#537 `3cf8867c` 02:54:07Z.
- ml#1300 merged 2026-08-24T08:14:47Z and introduced the helper on both paths. ml#2524 merged 2026-11-08T15:53:33Z.
- All five parent commits match.
- Every pre-fix and current line anchor matches. The service-core file at `16f2512b` is identical to the worktree's.
- Plan v1.15.15 is ml#2532 (2026-11-09). The ruling text is verbatim in the 11-12 handoff.
- The forks' behavioural tests exist, freeze the clock, read both headers and are marked `unit`. The service-core test descriptions are right. The header-writing sites outside the scopes are where the comment says.

**The guard**
- I rendered all 11 scoped bodies with `site_code`: every marker is present and no forbidden form occurs. Each site reads the definition it names.
- The primaries' `security.py` files are identical to GitHub `main`. juniper-data `main` has since moved to `706f14a2` (#539), but `security.py` is unchanged.
- With the cross-repo arms on: 17 tests, OK, none skipped. In CI mode: OK (skipped=3).

**The mutation script** (run with `--scratch` in my worktree)
- Control passes. All 5 pre-fix copies are caught. All 151 mutations are caught, each at the scope it edits.
- 88 of them are load-bearing, and 88 = 8 forms × 11 scope-copies. Each keeps every marker and holds exactly one forbidden form.
- Matched over the whole file, the markers pass 130 of the 151. Nothing came back not caught or anchor-mismatched.
- The PASS line cannot print once anything has been flagged.

**Workflows, docs, tooling**
- Both workflow edits are comment-only (shell comments in `ci.yml`'s `run:` block, indentation preserved). No test pins the changed text.
- REFERENCE.md 0.6.71's header, footer and history row agree.
- The pinned black, isort, flake8 and mypy hooks are clean. No line is over 512 characters and there is no `/tmp` literal. The CodeQL prescreen predicts 0 alerts. The doc-link check passed over 1661 files.

**Earlier review:** all 13 of its findings are applied.

**Other suites:** the 34 suites that read the register or workflows pass, except `test_workflow_script_paths…test_raises_when_no_dot_github_workflows_in_ancestors`. That test fails identically on base, because `TMPDIR` sits inside the checkout; it is unrelated to this change.

I wrote nothing outside `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-growing-whale/tmp/s2/review-eco016/`. That folder holds the base copies, probes and logs, a 48 MB mutation scratch and a 13 MB mypy cache. Nothing was written to the agent worktree or the siblings.
