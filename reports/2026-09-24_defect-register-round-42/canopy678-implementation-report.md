<!-- Archived verbatim 2026-09-24 from subagent aca4b18595b621f0a of session bc31e993 (final message). -->

pcalnon/juniper-canopy#678 is done and merged: all seven findings are fixed, and the three requested mutation checks each made the new tests fail. Nothing was pushed or opened after the merge.

## PR (read back with `gh pr view`)
- **#678**: https://github.com/pcalnon/juniper-canopy/pull/678. It is MERGED, at 2026-09-23T22:29:21Z, by `pcalnon`.
- **Head SHA that merged:** `775768d072106b5cde69dca2b2e9a079b28cc32a`. It is a single GitHub-verified signed commit on top of `9cdfcad4`.
- **Squash commit:** `05f2dfc2a6c29811a912e078be190214c84ab7f9`, verified. Its tree (`86f2a307`) is identical to the PR head's tree.
- **CI:** all 21 required checks passed. `mergeStateStatus` read BLOCKED both at open and when the checks finished; it never showed BEHIND.

## Files changed (juniper-canopy)
- `CHANGELOG.md`: the new leading bullet (finding 1), the sentence saying the entry supersedes `3a6dea95`'s message (finding 2), a rewritten WARNING paragraph, and wording limited to spaces and tabs.
- `src/security.py`: the key is still read once, at import; that read now only records which source was blank. A new `report_blank_api_key()` logs the WARNING at most once, worded for its source. The comment wording is corrected and the unused module logger removed.
- `src/main.py`: the lifespan calls the report right after `enforce_auth_posture`.
- `src/secrets_util.py`: a new `resolve_secret()` returns the value and its source; `get_secret()` now delegates to it.
- `docs/api/API_REFERENCE.md`: finding 7.
- `src/tests/unit/test_security.py`, `src/tests/unit/test_secrets_util.py`, and a new `src/tests/regression/test_blank_api_key_warning_boot.py`, which runs the real lifespan.
- New scripts: `util/ad-hoc/2026-09-23_blank_api_key_route_sweep.py` and `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py`.

## Tests
All run in `JuniperCanopy1` from the worktree root, with `env LIBTORCH= LD_LIBRARY_PATH=`.

| Command | Result |
|---|---|
| `python -m pytest -p no:cacheprovider -m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/ src/tests/performance/ --timeout=60` | 6866 passed, 1 skipped, 4 deselected (run twice, the second on the final code) |
| `python -m pytest -p no:cacheprovider -m "integration and not requires_cascor and not requires_server and not slow" src/tests/integration --timeout=120` | 559 passed, 41 skipped, 461 deselected |
| `python -m pytest -p no:cacheprovider src/tests/unit/test_security.py src/tests/unit/test_secrets_util.py src/tests/unit/test_secrets_util_coverage.py src/tests/regression/test_blank_api_key_warning_boot.py src/tests/regression/test_auth_posture_boot_check.py src/tests/regression/test_dependency_floor_boot_check.py src/tests/unit/test_observability.py` | 146 passed |
| `/opt/miniforge3/bin/pre-commit run --files <the 10 files>` | 18 passed, 7 skipped, 0 failed |
| Symbol-loss and docs-deletion screens | 0 FAIL, warnings only |

The symbol-loss screen would have failed on the two deleted #660 test names, so I kept those names and put the new tests under them.

## Mutation checks
`python util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` runs each mutant on a scratch copy of the tree. The unmutated copy passed all 90 tests, and all 10 mutants were caught.
- **WARNING fires on every call:** caught by 3 tests (the exactly-once unit test and both lifespan tests).
- **WARNING logs `%r` of the value:** caught by 7 tests.
- **Wrong advice for the file source:** caught by 3 tests in both forms, the file source given the env message and the file message's text rewritten.
- The other 7 mutants were also caught: #660's placement, no report at all, reporting before `configure_logging`, the source misnamed, a second read of the secret, and every read re-arming the WARNING.
- I also confirmed the validation's finding 5: #660's own tests pass against both the every-call and the `%r` mutants (7 passed each).

## Route figures
My counts at the merge point are **56 key-gated pairs, 27 state-changing, 26 parameterless GETs**, not the validation's 55/27/25, so `CHANGELOG.md` states 56/27/26.
- On `26e0546f`, #660's branch base, I reproduce 55/27/25 exactly.
- The extra pair is `GET /api/selection`, added by #662 before #660 merged onto `48074653`.
- On the pre-fix code, every one of those pairs refused a keyless request with 401; after the fix, each gets past every middleware, and all 26 GETs return 200.

## Header wording (finding 6)
I measured real uvicorn (h11 and httptools) with raw bytes:
- An all-space or all-tab `X-API-Key` arrives empty under both parsers, so no caller could present such a key.
- **U+00A0 and U+0085** pass both parsers, so a key made of them could be presented. But `hmac.compare_digest` raises `TypeError` on non-ASCII text, so every request carrying the header got a 500 and never matched.
- **U+001C to U+001F** pass h11, and under h11 a key made of them authenticated normally. httptools, canopy's default parser, rejects them with a 400.
- The comment in `src/security.py` and `CHANGELOG.md` now say exactly this.

## The final sweep
The sweep I was running when the limit hit had completed before I opened the PR, with the committed script, on fresh extractions. It gave 56/27/26 on `48074653`→`3a6dea95` and 55/27/25 on `26e0546f`→`3a6dea95`, and the header results matched the earlier run. After the merge I also ran it read-only against a `git archive` of `05f2dfc2`: 56/27/26 with all pairs opened, so merged `main` matches `CHANGELOG.md`.

## Not done
- **Worktree and branch:** the worktree `/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--apikeyauth-660-followup--20260923-1516--0254a7ec` is still in place, and so is the remote branch `fix/apikeyauth-660-followup`. You told me not to push, and cleanup needs an explicit signal.
- **Defect register:** the APD-ECO-008 row in juniper-ml's `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` doesn't point to #678 yet; that's juniper-ml work and outside this task. The drift gate's markers in juniper-ml's `tests/test_service_fork_drift.py` still hold.
- **Placement trade-off:** with `JUNIPER_CANOPY_REQUIRE_AUTH=true` and a blank key, `enforce_auth_posture` raises before the report runs. That boot fails with the posture check's CRITICAL and without the blank-specific WARNING, as the "right after `enforce_auth_posture`" instruction implies.
