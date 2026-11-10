# Thread Handoff — R-OBS-SC-2: P3-07 written and validated (round 1), fix pass next

**Date**: 2026-11-08 UTC (the host clock is local time, UTC−6)
**Session**: `e97264c3`, the Linux host, worktree `.claude/worktrees/witty-tickling-phoenix` (branch `worktree-witty-tickling-phoenix` at `58397dbb`, which was `origin/main` at 00:57Z). **The P3-07 change is UNCOMMITTED in that worktree. Start the new session IN that worktree**, and never `git stash`, reset or check out over it. Commits go only through `util/open_signed_pr.py` (signed API commits); never a local `git commit`.
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-07_recurrence-equities-0-11-4-published-parent-agents-edited-plan-v1-15-14.md`. Its item 1 is done (main `58397dbb` carries plan v1.15.14, all its files present); its item 2's R-OBS-SC-2 is this arc now; P5 W4 and §6 A1 carry forward unchanged.

## Goal

Ship R-OBS-SC-2 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (§5 row; Wave 1 "Security delivery" steps 1–3): P3-07, then juniper-observability 0.4.2 and juniper-service-core 0.7.2. **The owner wrote, in session `e97264c3` on 2026-11-08: "approval granted for updated observability and service-core releases" and "approval granted for merging PRs in this work arc".** Both are per-session grants (`feedback_headless_merge_approval_policy.md`): **ask the owner to re-grant them in your session** before any merge or cut. Paul approves every `pypi` gate.

## Completed this session

- **P3-07 written** (scope: F table in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` item 4; findings in `reports/2026-09-24_defect-register-round-42/bytes-compare-ml2086-data440-cascor689-validation.md`). Uncommitted files:
  - `juniper-observability/juniper_observability/sentry.py`: `before_send_transaction=_strip_sensitive_headers` (F2); the hook replaces a non-empty `request["cookies"]` (NOT in the register: found reproducing F2; under `send_pii=True` a cookie the SDK's denylist does not name, `juniper_auth`, reached error events and transactions); docstrings.
  - `juniper-observability/tests/test_sentry.py` (33 → 51 tests): init-kwarg test; cookie unit tests; `_frames` marked `in_app: False` + a mixed-frames test + an `in_app_exclude` wire test (F6); class `TestNoSensitiveRequestValueReachesTheWire` (FastAPI TestClient → real SDK → capturing transport; production / hook-alone with `_scrubbing_nothing()` / control).
  - `juniper-observability/CHANGELOG.md` `[Unreleased]` (`### Security` + `### Fixed`; F10's correction note).
  - `juniper-service-core/tests/test_security.py` (87 → 104): `_ENCODING_PROBES.append(chr(0xD83D) + chr(0xDD11))` (F5) + a guard test; the F3/F8 spy (`security_module.hmac` replaced by a `SimpleNamespace`).
  - `juniper-service-core/CHANGELOG.md` `[Unreleased]` (`### Fixed`: F3/F8, F5, F9's correction, "No module changes").
  - `tests/test_service_fork_drift.py`: one comment (F8). **REVERT IT** (fix pass item 12).
  - New: `util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py` (HEAD: `LEAK`, exit 1; worktree: `CLEAN`, exit 0) and `util/ad-hoc/2026-11-08_p3_07_mutation_check.py` (first run 23/24; the O4 row's expectation was wrong and is fixed in the script, not yet re-run).
- **Local checks (CI commands)**: observability 166 passed / 99.32% / gap-map gate PASS; service-core 647 / 98.28% / PASS; Python 3.12 and 3.13; pre-commit on the 8 files all pass except `juniper-check-doc-links`, which fails ONLY on `tmp/s1/mut/` copies (run it with `--exclude tmp`: all links valid, 1,621 files).
- **Round-1 validation, three independent agents** (final reports: the `tasks/a30dcfa5a9218f8bb.output`, `afe84f037a7e81b2a.output`, `a489db1c1b4557452.output` JSONL files under `juniper-ml/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-witty-tickling-phoenix/e97264c3-0861-4d47-8f4e-48ad2d8ba7bd/`; their probes in the worktree's `tmp/val-security/`, `tmp/val-facts/`, `tmp/val-tests/`). Security: no leak in what P3-07 claims, on sentry-sdk 2.35.0 / 2.73.0 / 2.74.0, controls non-vacuous. Fact-check: 2 MAJOR, 5 MINOR, 6 NIT. Tests: 1 MAJOR, 2 MINOR, 3 NIT.

## Owner rulings, 2026-11-08 (this session's AskUserQuestion, answered by 09:00Z)

- **0.4.2 scope: "P3-07 + header names"**: also add `sec-websocket-protocol`, `x-csrf-token`, `x-xsrf-token` and `proxy-authorization` to the hook's header set (`_SENTRY_SENSITIVE_HEADERS`). Query-string scrubbing and a Sentry Logs policy become a designed, separately validated follow-up (**0.4.3**).
- **service-core: "Include ml#2514, then cut"**: validate Cursor's draft ml#2514 (`FailedAuthThrottle` Retry-After rounds up), merge it AFTER P3-07 (its `[Unreleased]` hunk conflicts with P3-07's: main's entries verbatim, its own below), then cut 0.7.2 with real code. **The ruling approves merging ml#2514 as part of this arc** (head `aa9cd90e`, draft, at 09:00Z).
- **P3 D-03: "This arc opens them"**: after the publish, this arc opens the second lock round's PRs (juniper-data, juniper-cascor, juniper-canopy, juniper-recurrence image locks), each carrying S0.11's relay run. Merges still need the owner's approval.

## main moved: rebase before any upload

`origin/main` went `58397dbb` → **`8d73d441`** (ml#2516–#2519, to 03:35:58Z). **#2517 appended a RateLimiter class to `juniper-service-core/tests/test_security.py`**, which P3-07 also edits. `open_signed_pr.py` uploads whole files, so uploading the worktree's copy would REVERT #2517's tests. No other P3-07 file moved. Recipe, in the worktree: `git diff -- juniper-service-core/tests/test_security.py > tmp/s1/sc-test.patch`; `git checkout -- juniper-service-core/tests/test_security.py`; `git reset --keep origin/main` (it refuses if a locally modified file also changed upstream); `git apply --3way tmp/s1/sc-test.patch`; then re-check `git diff --stat origin/main`.

## Remaining work, in order

1. **Fix pass** (each item names its finding; item 13 is the owner's ruling):
   1. **[tests MAJOR] `traces_sample_rate`**: parametrize `test_before_send_transaction_hook_always_installed` over `traces_sample_rate` (0.0, 0.1, 1.0) as well as `send_pii`; add a wire case that calls `configure_sentry(..., send_pii=True, traces_sample_rate=0.0)` and sends a `sentry-trace` header ending `-1` (parent-sampled), asserting `[Filtered]` and no secret on the wire (mutant CM07, "hook only when rate > 0", leaked: `tmp/val-tests/probe_parent_sampled.py`).
   2. **[facts MAJOR] false mutant claims** in `juniper-service-core/CHANGELOG.md` and the spy's docstring: the `str` compare is CAUGHT (63 fail); `any()` is this session's mutant, not round-42's (round-42's `mutate.py`: UTF16, BREAK, SWALLOW, EQ). Say: the bytes `==` and the `break` passed everything (round 42); `any()` (APD-CASCOR-005's form) is now pinned too.
   3. **[tests MINOR] spy flakiness**: present EVERY configured key in turn (5 keys), asserting `len(calls) == len(keys)` and bytes each time (sorted-walk/list-walk + `break` survive 8/30 and 12/30 hash seeds today: `tmp/val-tests/exp3_hashseed.py`, `exp7_fix_demo.py`). Assert bytes in the mismatch half too (facts NIT).
   4. **[tests MINOR + facts MINOR] encoding probes**: PREPEND `"REAL-KEY"`, `"k" * 40 + "-1"`, `"k" * 40 + "-2"`, `chr(92) + "udcff"`, `"&#56575;"` (kills case-fold, 16/32-byte truncation, `backslashreplace`, `xmlcharrefreplace`); make the pair guard value-based (`chr(0xD83D) + chr(0xDD11) in _ENCODING_PROBES` and no duplicates), not positional; reword the comment to NAME the encodings it catches (no "each plausible"); CHANGELOG: the matrix size (13x13 if all five land) and wording. Never type `\uXXXX` pair escapes through Write/Edit (they become U+1F511; build with `chr()`; check with `od -c`/`LC_ALL=C grep -c '[^ -~]'`; non-ASCII line counts were 1/3/3 for test_sentry.py / test_security.py / sentry.py).
   5. **[security NIT] cookie shape**: a dict → `dict.fromkeys(cookies, "[Filtered]")` (Relay parses a STRING `cookies` as a raw header, and `[Filtered]` has no `=`); any other non-empty shape → drop the key. Update the unit tests and the two wire asserts.
   6. **[security MINOR] floor**: `sentry-sdk[fastapi]>=2.0.0` is false (`enable_logs` needs 2.35.0; `_scrubbing_nothing`'s `pii_denylist` fails on 2.0/2.10). Raise to `>=2.35.0` in `juniper-observability/pyproject.toml`'s `sentry` and `test` extras; CHANGELOG `### Fixed` line.
   7. **[facts MINOR] library-frame source**: canopy#683's frame was canopy's own (`in_app: True`). Say: a frame in an installed package is library code: juniper-data's image installs juniper-data (`pip install --no-deps .`), and an installed service-core's `validate` serialises `in_app: False`. Fix in the CHANGELOG, `_frames`' docstring and the F6 wire test's docstring; "Every frame was in_app" → "no test frame was marked library code".
   8. **[facts MINOR] lock sentence**: images built from locks get 0.4.2 with the next lock refresh (all four consumer locks pin 0.4.1 today); a fresh install or `pip install -U` gets it at once (no consumer caps it out).
   9. **[facts NITs]**: "Only juniper-data **can** turn `send_pii` on (opt-in, default off; no deploy config sets it)"; split "(18 new tests)" by section (re-count after the pass); `:369`'s "The option is off here" → "local-variable capture is back ON here".
   10. **[security NIT] class docstring**: scope `TestNoSensitiveRequestValueReachesTheWire` to the three named headers and the parsed cookies.
   11. **[facts MINOR] mutation script**: setup errors must exit 2 (a `SetupError` caught in `main`), not 1; docstring: `survived_old` comes from round 42 OR this script's first run (O2, O5, S3 are this session's). Add mutants for items 1, 3, 4, 5 (CM07; sorted/list walk + break under several `PYTHONHASHSEED`s; SM21/SM22/SM02/SM26; dict-only cookie filtering).
   12. **[facts MINOR] revert `tests/test_service_fork_drift.py`**: that comment is P3-14's (`reports/2026-10-04_consolidated-development-plan/extraction-P3-defect-register.md` row P3-14, after P3-11). Note it in the PR body.
   13. **[owner ruling] header names**: add `sec-websocket-protocol`, `x-csrf-token`, `x-xsrf-token`, `proxy-authorization` to `_SENTRY_SENSITIVE_HEADERS` (`sentry.py:36`); extend the unit tests and the wire tests' header set and names; a `### Security` CHANGELOG line that also names what stays open for 0.4.3 (query strings incl. canopy's `?api_key=`, Sentry Logs, bodies, breadcrumbs, exception values, list-shaped headers).
2. **Re-run everything** (both suites × 3.12/3.13, gap-map gates, the fork-drift unittest, pre-commit on the changed files, doc links with `--exclude tmp`, the probe, the mutation check). Venvs ready in the worktree: `tmp/s1/venv-obs312`, `venv-obs313`, `venv-sc312`, `venv-sc313` (uv: `/opt/miniforge3/envs/JuniperCascor1/bin/uv`). Old test files for the mutation check: `tmp/s1/head_obs/test_sentry.py`, `tmp/s1/head_sc/test_security.py`.
3. **Round-2 validation** on the fix delta (SOP: round 2 catches what round-1 fixes break): one fresh agent, refute-not-confirm, scratch only under the worktree's `tmp/`.
4. **PR**: `util/open_signed_pr.py --repo juniper-ml --branch fix/p3-07-sentry-transactions-cookies …`; body draft `tmp/s1/pr-p307-body.md` (fill its two PLACEHOLDERs; drop the drift-gate bullet; `References JR-ML-OBS-101`). Re-fetch and confirm `origin/main` first (whole-file uploads clobber a stale base). Merge with `util/safe_merge.py` under the owner's re-granted approval (read the `MERGED` line).
5. **Releases**:
   - **observability 0.4.2**: run `util/release_train/detect.py` with **`--local-git`** (the workflow's default mode proposes **0.5.0** from the repo-wide `feat:` confound, which canopy's and recurrence's `<0.5.0` caps exclude), then `propose.py`, merge the proposal, then `ceremony.py --execute --target-sha <40-char>` (archive PR alone: the Release-Train Archive Guard fails any PR mixing `notes/releases/`). Read `reference_release_train_ceremony_traps_2026-09-09.md` first.
   - **service-core 0.7.2** (owner: include ml#2514): `detect.py` says `UP_TO_DATE` while only tests changed. After P3-07 merges: validate ml#2514 (refute-not-confirm, like P3-07), un-draft and merge it, then `detect.py --local-git --package juniper-service-core` should propose the patch; propose, ceremony, archive PR, gate.
6. **The second lock round** (owner: this arc opens it), after both wheels are on PyPI: one image lock PR per consumer (juniper-data, juniper-cascor (both `requirements.lock` and `requirements-cpu.lock`), juniper-canopy, juniper-recurrence), each carrying S0.11's relay-test run (plan §4 S0.11). Merges need the owner's approval.
7. **Then**: the follow-up 0.4.3 (query strings, Sentry Logs, bodies, breadcrumbs, exception values, list-shaped headers), designed and validated on its own; plan v1.15.15 records P3-07, the three rulings, the cuts and the new findings; update memory `project_recurrence_equities_p0_arc_2026-10-04.md`.

## Pre-existing channels the security validator found (outside P3-07; for the owner and a follow-up)

- **MAJOR**: canopy's WebSocket key reaches Sentry under the DEFAULT `send_pii=False`, via `?api_key=` in `request.query_string` (canopy `src/main.py:764`) and the `Sec-WebSocket-Protocol: bearer, <key>` header (`:795`, opt-in `ws_auth_enabled`); the hook's header set lacks it and nothing filters query strings.
- **MAJOR**: Sentry Logs (`enable_logs=True`, no `before_send_log`) bypass every layer: uvicorn access lines carry query strings and client IPs.
- **MINOR**: `X-CSRF-Token`; request bodies' nested keys; breadcrumbs; exception values; outbound `spans[].data.http.query`. **NIT**: list-shaped headers skip the hook.

## Traps that held this session

- **Parallel Bash calls share one shell's cwd**: a `cd` in one call broke relative paths in its sibling. Use absolute paths, and run cwd-dependent calls sequentially.
- The isolation guard refuses a command name in a variable (`$UV …`), `sed` on a variable path, and `git` inside complex constructs: spell commands out.
- `pytester` (in `tests/test_testing_fixture.py`) run with `TMPDIR` under the repo's `tmp/` takes the worktree root's `pyproject.toml` as rootdir and writes `WT/.pytest_cache` (gitignored; harmless).
- sentry-sdk 2.74.0 deprecates `send_default_pii` for `data_collection` (17 warnings); with `data_collection` set the SDK disables event scrubbers. Not acted on.
- The G-TMP checker is not on `main` (lands with ml#2360, which merges LAST): build repo-`tmp/` paths from parts in scripts.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml/.claude/worktrees/witty-tickling-phoenix
git fetch origin && git log -1 --format=%h origin/main          # 8d73d441 at 09:00Z; re-check what moved since
git status --porcelain | grep -v '^?? tmp/'                      # the 6 M + 2 ?? files above
python3 -I util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py; echo $?   # needs tmp/s1/venv-obs312/bin/python: CLEAN, 0
gh pr list --repo pcalnon/juniper-ml --search "P3-07 OR before_send_transaction" --state open   # none expected
curl -s https://pypi.org/pypi/juniper-observability/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"   # 0.4.1
```

## Git state

Branch `worktree-witty-tickling-phoenix` at `58397dbb`, nothing staged, 6 modified + 2 untracked files (above) plus this file. `tmp/s1/` (ignored) holds the venvs, the diff (`p307-tracked.diff`), the PR body draft, coverage JSONs and `mutation-check.log`. Keep `tmp/` until the PR lands (retention rule).

## Documents created or modified this session

- Modified (uncommitted): `juniper-observability/juniper_observability/sentry.py`, `juniper-observability/tests/test_sentry.py`, `juniper-observability/CHANGELOG.md`, `juniper-service-core/tests/test_security.py`, `juniper-service-core/CHANGELOG.md`, `tests/test_service_fork_drift.py` (to revert).
- New (uncommitted): `util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py`, `util/ad-hoc/2026-11-08_p3_07_mutation_check.py`, this handoff.
- Outside the repo: memory `project_recurrence_equities_p0_arc_2026-10-04.md` (a new state block).
