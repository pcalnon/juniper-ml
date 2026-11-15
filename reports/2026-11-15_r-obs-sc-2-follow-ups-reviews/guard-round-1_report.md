# Review: `retry-after-rounds-up` guard and its mutation check

No blockers. One MAJOR finding: the guard cites `APD-ECO-016`, which is not in the defect register on `main` yet. The rest is MINOR or NIT, mostly guard gaps and inaccurate prose. The guard passes on all four current copies with no false positive, and fails on every pre-fix state.

**Files reviewed** (paths under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/toasty-prancing-karp/`):
- `tests/test_service_fork_drift.py` (sha `98ead3169bcc1fbe…`)
- `util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py` (sha `6cf393ce32bf9d76…`)

Both hashes match the ones handoff `HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md` names. "Battery" below means 33 regressions I built and scored in memory (`tmp/s1/review/probe_regressions.py`). I did not run the mutation-check script; I read the author's log, `tmp/s1/guard_mutation_check.log`.

## Findings

**1. MAJOR: the guard cites a register ID that does not exist on `main`.**
- **Defect:** `register_ids=("APD-ECO-016", …)` at `test_service_fork_drift.py:351`. The comment at `:358` ("the forks by one PR each, which the register row names") sends the reader to a row that isn't there.
- **Evidence:** `git show origin/main:notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md | grep -c APD-ECO-016` returns `0`. Nothing in CI would notice:
  - `test_register_ids_look_like_register_ids` (`test_service_fork_drift.py:572-576`) checks only the `APD-` prefix.
  - `tests/test_register_open_set.py` and `tests/test_register_close_protocol.py` never read `GUARDS`.
- **Fix:** land the row in the same PR, as item 2 of the 2026-11-13 handoff plans. Also name the fork PRs inline (juniper-data#537, juniper-cascor#757, juniper-canopy#817), as the `APD-ECO-015` guard does at `:326`.

**2. MINOR: the summary's date is a local date; the fixes merged on 2026-11-13 UTC.**
- **Defect:** "kept truncating until 2026-11-12" (`test_service_fork_drift.py:349`).
- **Evidence:** `gh pr view` merge times are canopy#817 `2026-11-13T01:02:07Z`, cascor#757 `01:07:08Z` and data#537 `02:54:07Z`. The 2026-11-13 handoff itself records "#537 merged at 02:54:07Z".
- **Fix:** write "until 2026-11-13 (UTC)", or name the three PRs instead of a date. The register row should use the same form.

**3. MINOR: a wrong rounding passes whenever the marker text survives beside it.** The forbidden list only names specific spellings.
- **Evidence:** these battery cases pass while wrong, in every copy they apply to:
  - h08: a rare branch keeps `max(1, math.ceil(…))` and the main path returns `int(window - elapsed)`.
  - h09: the same, with `//`.
  - h12: the marker sits in a non-docstring string, and the helper returns `int(window - …)`.
  - c05: `self._seconds_until_reset(…) // 2`.
  - t04: the marker sits in a log string, and the throttle returns `max(1, int(left))`.
  - t06: `math.ceil(remaining // 1)`.
- **Measurement:** none of the 11 current scoped bodies contains `int(` or `//`. Re-scored with both forbidden, the silent passes drop from 11 to 5, and none of the 11 current bodies is flagged. The 5 left are h10 (second helper), h11/c04/t03 (`- 1` after the round-up) and c14 (finding 9).
- **Fix:** add `" int("`, `"(int("` and `"//"` to `_WRONG_ROUNDINGS` (`:192`). The space and paren prefixes avoid matching `print(`.

**4. MINOR: the mutation check does not show the forbidden list is load-bearing.**
- **Evidence:** I re-scored the script's own 63 mutations with the forbidden list removed (`tmp/s1/review/probe_forbidden_coverage.py`). Only M2 depends on it (4 runs, all in the helper scope), and only on `int(self._window`.
  - `int(remaining`, `math.floor(`, `math.trunc(` and `round(` could be deleted or mistyped and every mutation would still be caught.
  - No forbidden entry is exercised in `RateLimiter.check` or `FailedAuthThrottle.check`.
- **Fix:** add mutations that keep the marker beside each forbidden form, in each scope. For example: `if False: return max(1, math.ceil(…))` followed by `return math.floor(…)` in the helper; an extra early `return (False, 0, int(remaining))` in `check`; a dead-branch marker plus `max(1, int(remaining))` in the throttle.

**5. MINOR: the new docstring paragraph gives the wrong reason for scoping.**
- **Defect:** "A whole-file marker could not tell … one that fixed the helper and left a `check` path … truncating" (`test_service_fork_drift.py:51-56`).
- **Evidence:** the author's log shows R6–R9 (`check` returns truncating or skipping the helper) as `whole-file form: FAIL` in all four copies. The `check` markers occur only in `check`, so a whole-file match catches those regressions. Scoping is actually needed for two other reasons:
  - The helper and the throttle share the `max(1, math.ceil(` text. R1–R5, M1–M3 and T1–T5 read `PASS (vacuous)` whole-file, and the `#2524^` pre-fix file reads `whole-file form: PASS`.
  - The forbidden list needs a scope, because `int(` is legitimate elsewhere in these files (juniper-data's `_warn_on_capacity_locked`, canopy's `int(port)`).
- **Fix:** reword the paragraph around those two reasons.

**6. MINOR: text on `main` will contradict the guard once it lands.**
- `docs/REFERENCE.md:3727` (canopy is a site of the two key-handling guards only), `:3733` ("all eight guards are `ENFORCED`") and `:4544` (tree comment).
- `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md:1111` ("eight since 2026-10-26").
- `ci.yml:566-572` comment (names data and cascor only).
- **Fix:** update all of these in the same PR. The handoff lists only the `REFERENCE.md` entry.

**7. MINOR: module docstring wording around canopy and the shared package (`test_service_fork_drift.py:7-11`).**
- "a site of those two guards as well" now follows a sentence that names three guards. The shared package is a site of four (`:265`, `:293`, `:341`, `:372`).
- The new sentence starts with a lowercase "canopy is…", and the paragraph was not reflowed (`:9`, `:91`).
- **Fix:** list the four guards, capitalise, reflow.

**8. NIT: "juniper-canopy forks only `APIKeyAuth` … and `RateLimiter`" overstates it (`test_service_fork_drift.py:88-89`).**
- canopy also has its own `SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware` and `SecurityMiddleware` (canopy `src/middleware.py:32/59/77` on `origin/main`).
- **Fix:** say "the only canopy code this gate checks is…".

**9. NIT: the second `check` marker keys on the wrong text (`test_service_fork_drift.py:191`).**
- **Defect:** `"1, self._seconds_until_reset("` matches the text before the call, not the allowed return itself. Battery case c14 passes in all four copies: the new-window return is changed to call the helper, and the allowed return regresses to an unrounded float.
- **Brittleness:** both `check` markers also fail correct refactors (c06: a local `reset_in`, which was the pre-fix shape; c10: a `max(0, …)` clamp; c11: a local `remaining`). The failure message then calls the change "a regression of APD-ECO-016".
- **Fix:** use the full prefix `"(True, self._limit - count - 1, self._seconds_until_reset("`, which is byte-identical in all four copies. Note in the comment that the brittleness is deliberate.

**10. NIT: the comment describing the remaining gap is inaccurate (`test_service_fork_drift.py:363-368`).**
- "a wrong rounding written in a form it does not name … would pass" is wrong as written: a full replacement in any spelling fails, because the marker goes. The real residue is unmentioned:
  - Arithmetic after a correct round-up: c04 `self._seconds_until_reset(...) - 1`, h11 and t03. This reintroduces `Retry-After: 0`. The fork tests do pin it behaviourally.
  - The header formatting, which happens outside every scope. Each copy's limiter `__call__` builds the 429 headers, and data/cascor/canopy middleware carries the values out (`middleware.py:206`, `:202`, `:145`).
- "frozen-clock tests: … `tests/test_security.py`" is only partly true. Its `APD-SVCCORE-004` class (`:341-419`) uses `time.sleep`; only the later window-boundary class freezes the clock.

**11. NIT: a release is cited where a PR belongs.** "its throttle (0.7.2)" (`:349`) and "for the throttle, its 0.7.2" (`:357-358`). The fix is juniper-ml#2524, merged `2026-11-08T15:53:33Z` and first released in service-core 0.7.2 (PyPI 2026-11-09). Name #2524.

**12. NIT: mutation-script docstring and scratch handling.**
- Item 2's "the only guard any failure names is this one" is false for the `#1300^` case (`SELF_FIXES`, `:63`).
- Item 3 calls R3 and T4 "wrong roundings", but removing the floor changes no reachable result (cascor's own helper docstring says so).
- The `mkdtemp` scratch directory (`:225`) is neither removed nor printed, so each run leaves 69 synthetic ecosystems under `$TMPDIR` at an unreported path. The 2026-10-26 predecessor used `TemporaryDirectory`.

**13. NIT: subTest keys collide.** This is the first guard with several sites per repo. The subTest keys (`:713` guard and repo; `:786` guard only) omit the scope, so up to three failures print identical headers. Add `scope=site.scope`.

## Questions 1–5

1. **Each site can fail for its regression.**
   - All five pre-fix states fail under Python 3.12, 3.13, 3.14 and 3.15.
   - Every single-edit regression in the battery that replaces the formula or a return is caught: truncation, `//`, `max(0, …)`, ceil without the floor, a literal 0 or `self._window` return, a comment-only marker, a shadowing definition. A renamed or inlined helper fails loudly.
   - Silent passes need marker text kept beside an unlisted spelling, arithmetic after the round-up, a second helper, or the c14 double edit (findings 3, 9, 10).
2. **It passes on `main` with no false positive.**
   - Local HEAD, local `origin/main` and GitHub `main` all agree: data `3cf8867c`, cascor `66b39a5c`, canopy `55ac2168`. The guarded files are clean, and the worktree is at `4a786c81`.
   - Through the DSN wrapper with `FORCE_LOCAL=1`: 17 tests, OK, no skips, under 3.15, 3.12 and 3.14.
   - The ecosystem root resolved to `/home/pcalnon/Development/python/Juniper`, and all 11 sites pass under 3.12–3.15.
3. **Facts:**
   - **Correct:** all five PR numbers, merge commits and pre-fix parents; canopy has a `RateLimiter` and no `FailedAuthThrottle`; `APD-ECO-010` is open; 0.7.2 carries the throttle fix; the forks import no limiter or throttle code; "11 scoped sites in 4 copies".
   - **Wrong:** the register row (1), the date (2), the scoping rationale (5) and the prose in findings 7, 8, 10 and 11.
4. **The mutation check holds up, with one gap.**
   - A vacuous guard would fail it: PRE-FIX catches it per copy, and the mutations catch it per site and per marker (R6/R8 and R7/R9 each break one `check` return).
   - All five anchors occur exactly once in every copy, except `THROTTLE`, which is absent in canopy and skipped there by design. There is no CRLF, and the helper precedes `check` everywhere, so M3 is valid.
   - It has no dependence on fork test names. It keys only on the gate's own messages and unittest's summary lines, and both fail closed.
   - The gap is findings 4 and 12.
5. **Conventions and tooling:**
   - It matches the `APD-ECO-015` precedent and passes the structural checks.
   - No line exceeds 512 characters (max added line 251; script 217).
   - The pinned black, isort, flake8 and mypy hooks are clean on the test module. The script's flake8 comprehension warnings fall outside the hook's `^(scripts|tests)/` scope.
   - G-TMP passes, and the CodeQL prescreen predicts 0 alerts.
   - Only `ci.yml` (without siblings) and `docs-full-check.yml` (siblings at their default branch) run this module.

## Housekeeping

- **Changed:** no reviewed or tracked file.
- **Created:** scratch files under `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/toasty-prancing-karp/tmp/s1/review/`: eight `*_security.py` snapshots and four `probe_*.py` scripts.
- **Cleaned up:** my `python3 -I` probe runs wrote four gitignored `.pyc` files (`tests/__pycache__/test_service_fork_drift.cpython-312/313/314.pyc` and one in `util/ad-hoc/__pycache__/`). I removed them and the `util/ad-hoc/__pycache__` directory they created. `git status` matches its starting state.
