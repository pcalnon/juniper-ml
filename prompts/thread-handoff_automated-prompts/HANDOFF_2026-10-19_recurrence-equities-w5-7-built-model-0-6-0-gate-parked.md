# Thread Handoff — Recurrence × Equities: W5.7 built (juniper-data#486), the model 0.6.0 `pypi` gate still parked; #215 → 0.8.0 → #219 → the 0.8.0 pins next

**Date**: 2026-10-19
**Host**: turing (Darwin, Intel; no commit signing; bash 3.2) — every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_recurrence-equities-w5-4-landed-0-7-0-pins-followed-bench-row-open.md`
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.9**

---

## Goal

Continue the arc from plan v1.7.9. **This session (the continuation after the v1.7.8 handoff)**: with everything downstream of model 0.6.0 blocked on the owner's `pypi` gate, **W5.7 was built out of order** — juniper-data#486 (merged as `58c013e3`, signed commit `84f7ecd7`, all lanes green), the producer guards for F-P5 / F-P6 / F-P8, applied by `util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py` and recorded in the plan by `util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py`. Also recorded: a teammate session found that juniper-ml#2262 (W5.4) had carried whole-file copies of `AGENTS.md` / `docs/REFERENCE.md` from a base older than #2259 and so reverted six `~/` path lines; #2268 (`63358646`) restored them — see "Landing rules" below.

**Everything downstream of model 0.6.0 is still blocked on the owner's `pypi` gate** (run 39197693617, `waiting` at the end of this session; PyPI serves model 0.5.0, recurrence 0.7.0): juniper-recurrence#215 → recurrence 0.8.0 → juniper-recurrence#219 → the 0.8.0 pins.

## What W5.7 did (juniper-data#486)

- **F-P5**: one shared conditioning loop, `EquitiesGenerator._condition_universe(symbols, meta_map, params, end_date, log_prefix=)`, returns `(conditioned, lost)`; `_apply_incomplete_policy(params, conditioned, lost=)` refuses a lost **requested** symbol under the shut `allow_truncation` gate (422 `IncompleteDataError`, `rows_affected` 0, `incomplete_rows` not offered), records it under `data_quality.dropped_symbols` (symbol → reason) with a WARNING under the open gate, and only records a lost ticker of the default universe. `equities_seq` classifies a ticker with ≤ `lookback + 1` rows as lost **before** the policy (it keeps its `ticker_vocab` slot with zero windows — the code allocation is unchanged so existing ids keep their arrays).
- **F-P6**: `EquitiesGenerator._check_return_target_inputs(ticker, frame, mode)` refuses `return` / `log_return` over a non-positive or non-finite `close` / `next_close` with a 400 `ValueError` naming ticker, row count and first session; `next_close` unguarded. Called per ticker in both generators before the target.
- **F-P8**: `_condition_one` logs the `dividend` / `split_ratio` zero-fill at WARNING and sets an `actions_present` frame column; `build_data_quality_meta(..., dropped=, actions_present=)` records `data_quality.actions_present` (symbol → bool, every symbol in the arrays) and returns `None` only when every category is clean. yfinance 1.7.0's `history` adds both columns under `actions=True` (`scrapers/history.py`), so an absent column is an anomalous response or a cache file written from one. `dataset_id` is request-addressed: documented in the `equities_seq` module docstring and `docs/REFERENCE.md` § Equities Data Quality Annotation.
- `generator_version` **not bumped** (W1.8 precedent). `tests/unit/test_equities_producer_guards.py` (35 tests); the OHLCV fixtures in six test modules now carry `Dividends` / `Stock Splits` columns, so a fixture without them is the anomaly under test. Verified on turing: 250 passed over the equities-adjacent modules, 2182 passed / 1 environmental failure (`test_init.py::test_missing_arc_agi_sets_unavailable`, no `arc-agi` extra) over the fast unit suite; four `TestUniverseSymbolCap` / `TestEquitiesSeqSymbolCap` tests deselected because they reach the SEC ticker endpoint (times out in the sandbox; identical on the untouched tree); `ruff check / format --check juniper_data` clean at the pre-commit pin 0.15.2.
- **Consumer note**: a multi-symbol request that loses a named symbol now gets 422 by default. juniper-canopy's two equities registry seeds and juniper-ml's E-H suite request `AAPL` alone (unaffected). It ships in juniper-data's next release (`[Unreleased]`); the juniper-ml `[servers]` floor need not move.

## Remaining work, in order

1. **Owner**: approve the `pypi` gate on run 39197693617 (`juniper-recurrence-model-v0.6.0` at `2c5a419c`). Then verify 0.6.0's `requires_dist` equals 0.5.0's (`python3 -I -c` against `https://pypi.org/pypi/juniper-recurrence-model/0.6.0/json`).
2. **juniper-recurrence#215** (W5.2 service half + the `[torch]` extra fix, head `25b75832`): `gh run rerun <id> --failed` for its red lanes once 0.6.0 is on the index, then `python3 util/safe_merge.py --pr 215 --repo juniper-recurrence --execute` (its own merge approval). Then **recurrence 0.8.0**: `util/release_train/detect.py` → `propose.py --dry-run` / `--execute --cross-repo` → merge → `ceremony.py --execute --cross-repo --target-sha <merge sha>`; close the follow-on ceiling PR only if a floor raise supersedes it; the release notes must name the `[torch]` fix (0.7.0's `juniper-recurrence[torch]` cannot resolve).
3. **juniper-recurrence#219** (bench multi-ticker row, `5e409f50`): rerun its lanes after #215 merges and 0.6.0 is on PyPI; the CHANGELOG hunk may conflict after #215 — re-run `util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py` on a fresh main copy (it inserts under the existing `### Changed`).
4. **The 0.8.0 pins** (owner rulings, taken with merge approval last time): juniper-ml `[recurrence]` → `juniper-recurrence>=0.8.0,<0.9.0` and `juniper-recurrence-model>=0.6.0,<0.7.0` (copy `util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py`; pre-flight with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`; regenerate the README compat table with `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`); Compose `juniper-recurrence:0.8.0` (copy `util/ad-hoc/2026-10-19_pin_compose_recurrence_0_7_0.py`; verify GHCR first).
5. **W5.5 / W5.6** (juniper-ml, the remaining P5 rows): `stats_summary.py` regression-target summary per split (W5.5); `--shared-equities-cache <dir>` opt-in with its runbook section (W5.6).
6. **Owner**: W0.1 service-core half (cascor restart recipe in juniper-recurrence/AGENTS.md); parent `Juniper/AGENTS.md` RELEASED paragraph (recurrence 0.7.0, model 0.5.0 → 0.6.0 after the gate); juniper-data's next release carrying W5.7; refresh the juniper-recurrence checkout (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`) and the juniper-data one once #486 is merged.
7. Follow-ups unchanged from the predecessor: W1.12 / W1.11 smokes on the 0.7.0 image (a host whose Docker reaches GHCR); juniper-ml `[Unreleased]` duplicate `### Changed` headings; recurrence-client docstrings (`client.py:414`, `:522`); juniper-canopy#735–738, #751; juniper-ml#2210, #2211; juniper-deploy#250; the `ARCHIVE_B64_MAX_DEFAULT` measurement in `util/release_train/ceremony.py`; `docs/REFERENCE.md:177` pins sentence; `docs/QUICK_START.md` pip list block.

## Landing rules learned this session

- **Build every whole-file API upload of a shared file on the current `origin/main` copy** (`AGENTS.md`, `docs/REFERENCE.md`, `CHANGELOG.md`, `ci.yml`, the plan): `git show origin/main:<path>` into the staging dir, re-run the apply script against that copy, then upload; re-do it after any `update-branch`. juniper-ml#2262 uploaded `AGENTS.md` / `REFERENCE.md` from a base older than #2259 and reverted six lines (restored in #2268). The plan scripts now take `--plan PATH` for exactly this.
- **Sibling-repo work**: `rsync -a --exclude .git` the checkout into the scratchpad, verify it against `origin/main` by API (`scratchpad/verify_data_scratch_vs_main.py` pattern: `contents/<path>?ref=<sha>`, sha256 compare), build a venv from JuniperPython with `--system-site-packages` and `pip install -e "<scratch>[api,equities,test,observability]" ruff==<pin>`, edit and test there, land with `util/open_signed_pr.py --repo <repo>`. Never touch the owner's checkout.
- **Merge approvals do not carry over.** This session's covered juniper-ml#2260, #2262, #2264, juniper-deploy#255 and juniper-data#486 (all within the arc the governing handoff named). #215, 0.8.0's proposal, #219, the 0.8.0 pins, W5.5 / W5.6 and the plan / handoff PR that follows need their own.
- The `pypi` environment gate is the owner's: report the run id and the approval command, never click it (`current_user_can_approve: true` notwithstanding).
- The worktree guard refuses `$VAR` in compounds, `cd` + several commands, `git -C <sibling>`, and `sed` with computed arguments; use literal paths, one command per call, `python3 -I <script>`, or `nohup /bin/bash <script>`.

## Verification commands for the new thread

```bash
gh run view 39197693617 --repo pcalnon/juniper-recurrence --json status,conclusion
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-recurrence-model/json'))['info']['version'])"
gh pr view 486 --repo pcalnon/juniper-data --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'
gh pr view 215 --repo pcalnon/juniper-recurrence --json state,headRefOid,mergeable -q '.state + " " + .headRefOid + " " + .mergeable'
gh pr view 219 --repo pcalnon/juniper-recurrence --json state,headRefOid,mergeable -q '.state + " " + .headRefOid + " " + .mergeable'
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hidden-popping-zephyr` on branch `worktree-hidden-popping-zephyr`; nothing committed locally; every change landed through the API. The worktree's untracked files (`util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py`, `util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py`, this handoff, and the v1.7.8 trio) are all on `origin/main` once the plan / handoff PR merges; `git checkout -- . && git clean -fd` on the worktree is safe after that.
- juniper-data checkout at `7465d5a4` (main before #486; main is now `58c013e3`); the scratch copy with W5.7 applied is `/private/tmp/claude-501/-Users-pcalnon-Development-python-Juniper-juniper-ml/06FC5F28-2F3C-4FD8-80E5-5AF582EFFF2D/scratchpad/juniper-data` (gone with the session).

## Documents created or modified this session

- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.8 → v1.7.9)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_recurrence-equities-w5-7-built-model-0-6-0-gate-parked.md` (this file)
- `util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py`, `util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py` (new)
- juniper-data#486: `juniper_data/core/limits.py`, `juniper_data/generators/equities/generator.py`, `juniper_data/generators/equities_seq/generator.py`, `juniper_data/generators/equities/params.py`, `juniper_data/tests/unit/test_equities_producer_guards.py` (new), five fixture-bearing test modules, `docs/REFERENCE.md`, `CHANGELOG.md`
- Referenced: `notes/JUNIPER_2026-10-04_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-INVESTIGATION.md` §1.1; `notes/JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md` §4.1; the predecessor handoff above
