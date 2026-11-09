# Thread Handoff — R-OBS-SC-2 lock round prepared, per-lock probe ruled; both `pypi` gates still pending

**Date**: 2026-11-09 UTC (host clock is local time, UTC−6)
**Session**: `b4208d23`, the Linux host, worktree `.claude/worktrees/enchanted-foraging-rocket` (branch `worktree-enchanted-foraging-rocket`, HEAD `cef03a06` = `origin/main` at 00:17Z, nothing committed). Every file this session made is **uncommitted in that worktree**. A new session in another worktree must `cp` them in, because the isolation guard refuses `git -C` into a sibling. Commits go only through `util/open_signed_pr.py` / `util/push_signed_commit.py` (signed API commits).
**Supersedes**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_r-obs-sc-2-cut-pypi-gates-lock-round-next.md`. That handoff was uncommitted in worktree `fizzy-enchanting-deer`, and this session ported a byte-identical copy (sha256 `ab5dd4d5…`) into this worktree. Its step 1 is still blocked; steps 2–4 carry forward, refined below.

## Goal

Finish R-OBS-SC-2 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (Wave 1 "Security delivery", steps 3–4). Confirm both wheels on PyPI once the owner approves the gates. Then open the second lock round (four consumers, five locks), each PR carrying the per-lock probe the owner ruled. Record it all in plan v1.15.15, committing both handoffs and this session's four ad-hoc tools in that PR.

**Approvals are per-session** (`feedback_headless_merge_approval_policy.md`). This session held "approval to perform all necessary operations on PRs for this work arc, as appropriate" (the user's turn, 2026-11-09 ~00:15Z). **Re-ask in your session.** Paul approves every `pypi` gate; never approve one.

## Owner ruling this session (record it in v1.15.15)

**2026-11-09T00:24:20Z** (AskUserQuestion; transcript `tool_result` timestamp): **"Per-lock probe (Recommended)"**. The question established three facts. Security step 4 asks every lock PR to carry "S0.11's relay run". S0.11's relay tests were never written for data, cascor or canopy, and only recurrence has W1.14's tests (recurrence#203). A1's F-S10 rulings for data-client and cascor are still open (plan L188, L738).

The option's text: in a venv built from each new lock, run the P3-07 Sentry wire probe with the Sentry DSNs empty and a capturing transport. Run the consumer's own Sentry and security suites, plus W1.14's tests for recurrence. Record FastAPI's native-telemetry setting and any OpenTelemetry SDK or exporter in the lock. **Each PR body states that this is NOT S0.11's relay run, which does not exist yet because A1 is open.**

## Completed this session

- **Gates re-probed at 00:17Z: both still `waiting`.** Runs 42499466753 (service-core 0.7.2) and 42500706778 (observability 0.4.2) show `Publish to PyPI: waiting/null`, and both `pypi.org/pypi/<pkg>/<ver>/json` return 404. The user was told in-session.
- **No competing lock PRs.** Open PRs at 00:20Z: data#520–524 and canopy#798–801 (all Cursor drafts, none touching a lock); none in cascor or recurrence.
- **Fresh `main` trees** under `tmp/lr2/src/<repo>/`, each beside a `.sha` file, fetched by `util/ad-hoc/2026-11-09_lock_round_2_fetch_consumers.py` (REST tarballs, no `git`). They are: data `4f04fc8d`, cascor `f3dfee8c`, canopy `63a2f3d7`, recurrence `3529dfd9`. **Re-fetch with `--replace` right before the refresh, and compare the SHAs**: a whole-file upload from a stale tree reverts what merged since.
- **Lock recipes** (from `util/ad-hoc/2026-11-09_lock_round_2_facts.py`; `tmp/lr2/facts-*.txt`). Every lock pins observability 0.4.1 and service-core 0.7.1 today.

  | Lock | Recipe | Freshness gate (CI) |
  | --- | --- | --- |
  | data `requirements.lock` (69 pins) | `--extra api --extra observability --extra mnist --extra equities`, Py 3.14 | `ci.yml:686`, `--constraint requirements.lock` |
  | cascor `requirements.lock` (73) | `--extra ml --extra api --extra observability --extra juniper-data --index-strategy unsafe-best-match --no-emit-package torch`, Py 3.14 | `ci.yml:776` |
  | cascor `requirements-cpu.lock` (54, 35-line hand header) | its header's recipe: `torch==2.14.0+cpu` override file, CPU extra index, `--constraint requirements.lock`, Py 3.14; refresh AFTER the GPU lock | `lockfile-update.yml:200` + CI's "contains every image dependency" script |
  | canopy `requirements.lock` (60) | `--extra juniper-data --extra juniper-cascor --extra observability`, Py 3.14 | `ci.yml:738` |
  | recurrence `juniper-recurrence/requirements.lock` (31, 74-line header) | `--extra observability --python-version 3.13`, from inside `juniper-recurrence/`; add a dated `REGENERATED … TARGETED` header paragraph; arm64 pre-flight `util/ad-hoc/2026-09-08_lock_wheel_availability.py --python 3.13 --arch aarch64` | none in CI |

  The refresh tool is `util/ad-hoc/2026-10-10_targeted_lock_refresh.py refresh … --upgrade-package juniper-observability --upgrade-package juniper-service-core` (it refuses collateral moves and restores the header), then `check`. Change only the locks and `CHANGELOG.md` `[Unreleased]` → `### Security`: a `pyproject.toml` in a data, cascor or canopy PR fires `lockfile-update.yml --upgrade` (data#478's re-cut). Floors go in each repo's release PR; recurrence#199 moved recurrence's floors in its lock PR, so ask the owner if you would do that again.
- **The probe**: `util/ad-hoc/2026-11-09_lock_round_2_probe.py`, which uses `…_env_record.py` and `2026-11-08_p3_07_sentry_wire_probe.py`. It builds a venv from one lock (`uv`, constrained, freeze compared with the lock: `pin_drift`), sets the six H-14 DSNs to `""`, unsets `LD_LIBRARY_PATH` and `JUNIPER_CASCOR_LOG_DIR`, and writes `tmp/lr2/runs/<repo>-<label>/summary.json`. The exact invocations (suites, marker expressions, interpreters) are in this session's transcript and are reproduced in `tmp/lr2/runs-*-before.out` and each `summary.json` (`pytest.suites`).
- **Baselines on today's locks (`--label before`)**. FastAPI 0.162.0's default telemetry (what cascor's and canopy's factories get, since neither passes `telemetry=`) is `tracing`/`metrics`/`logs`/`operation_spans` True and `auto_configure` False, with no providers. Only `opentelemetry-api` 1.45.2 is installed, so the provider is `ProxyTracerProvider`: no SDK, no exporter, no span path.
  - **data**: wire probe **LEAK** (6 items; `sec-websocket-protocol`, `x-csrf-token` and `x-xsrf-token` under both `send_pii` values; `x-api-key` and the `juniper_auth` cookie under `True`), which is P3-07's finding on 0.4.1. 7 suites, 247 tests, exit 0. That run predates the driver's summary fix (its own `-q` plus the addopts' `-q` suppressed the line), so re-run it. data's app passes `telemetry=` with every signal off (data#454).
  - **recurrence**: PASS. 364 passed. No sentry-sdk in the lock (no Sentry path in the image: wire probe N/A). FastAPI 0.141.1 has no native telemetry, and no OpenTelemetry is installed.
  - **cascor** (image lock `requirements-cpu.lock` + `torch==2.14.0+cpu`, `-m "unit and not slow"`, 11 suites): wire probe **LEAK** (6 items, as data); **290 passed**; `pin_drift` empty. The GPU lock got no venv (it pins ~3 GB of CUDA wheels). Its shared pins equal the CPU lock's by construction (`--constraint`).
  - **canopy** (`requirements.lock` + CPU torch, CI's `-m "not requires_cascor and not requires_server and not slow"`, 16 unit and regression suites): wire probe **LEAK** (6 items); **454 passed**; `pin_drift` empty.

## Remaining work, in order

1. **When the owner approves both gates**: version endpoints 200, and both runs' `Publish to PyPI` = success.
2. **Per consumer** (data, cascor, canopy, recurrence): re-fetch the tree, refresh, `check`, `--label after` probe (expect wire probe **CLEAN**, same suites green, `pin_drift` empty), CHANGELOG entry, and `open_signed_pr.py` (lock + CHANGELOG). The body should carry: before/after probe results, the telemetry record, the freshness replay, and the NOT-S0.11 sentence, with `References` to `RELEASE_NOTES_juniper-observability_v0.4.2.md` / `…service-core_v0.7.2.md`. Before opening, re-resolve `main` and refuse if it moved. Merge with `util/safe_merge.py` (read its `MERGED` line) once the required checks pass, under your session's re-granted approval.
3. **Plan v1.15.15**: an ad-hoc writer modelled on `util/ad-hoc/2026-11-07_consolidated_plan_v1_15_14_juniper_ml_0_11_4_published.py`. It records P3-07 (#2523), the carry (#2524), the proposals (#2525, #2526), both cuts and their gate state, rounds 2/3's findings, the 00:24:20Z ruling, the lock PRs, Security step 4's probe in place of S0.11's run, and the follow-ups below. Commit both handoffs and the four ad-hoc tools in it.
4. **Memory**: update `project_recurrence_equities_p0_arc_2026-10-04.md`'s top block.
5. **Owner items to surface (report, do not act)**: the juniper-ml `[tools]` floor `>=0.4.2` needs meta 0.11.5. The forks' truncating `RateLimiter`/`FailedAuthThrottle` (data `security.py:250/:254/:427`, cascor `:229/:233/:386`, canopy `src/security.py:270/:274`) leave APD-SVCCORE-004's `Retry-After: 0` live, with no register row. Also: the 0.4.3 design; the `/tmp/juniper-e2e/canopy-805{2,3}.log` writer; S0.11's relay tests still unwritten (A1); and cascor and canopy running FastAPI's default telemetry. That last one is inert while the locks hold no OTel SDK, but data#454's opt-out is missing in both.

## Traps (new this session, plus the carried ones)

- **Reading any file under `tmp/lr2/src/<repo>/` injects that repo's whole `CLAUDE.md` into context** (~10k tokens each; it happened for cascor and canopy). Work on those trees only through scripts that print what you need.
- The sandbox refuses `for` loops and complex pipelines whose text mentions `git` or `.github`, `git -C`, and `$VAR`-built `gh`/`git` commands. Write a script in `util/ad-hoc/` and run it.
- `grep` is ugrep and honours `.gitignore`, so a recursive grep skips `tmp/`. Use `command grep`.
- Repos whose pytest `addopts` carry `-q` (data) lose the summary line under an added `-q`. The driver adds none now.
- The `tarfile` `data` filter refuses cascor's and canopy's out-of-tree symlinks (`claudey`, some `notes/` links). The fetcher skips and names them.

## Verification commands

```bash
cd ~/Development/python/Juniper/juniper-ml/.claude/worktrees/enchanted-foraging-rocket   # or cp the files below from it
git fetch origin && git log -1 --format='%h %s' origin/main                       # cef03a06 or later
gh api repos/pcalnon/juniper-ml/actions/runs/42499466753/jobs --jq '.jobs[] | "\(.name): \(.status)/\(.conclusion)"'
gh api repos/pcalnon/juniper-ml/actions/runs/42500706778/jobs --jq '.jobs[] | "\(.name): \(.status)/\(.conclusion)"'
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-observability/0.4.2/json
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-service-core/0.7.2/json
python3 -c "import json;print(json.load(open('tmp/lr2/runs/juniper-data-before/summary.json'))['wire_probe'])"
```

Run each `gh` and `curl` as its own command: the sandbox refuses loops.

## Git state and files

Worktree `enchanted-foraging-rocket` at `cef03a06`, nothing staged. Uncommitted (all new):

- `util/ad-hoc/2026-11-09_lock_round_2_fetch_consumers.py`
- `util/ad-hoc/2026-11-09_lock_round_2_facts.py`
- `util/ad-hoc/2026-11-09_lock_round_2_env_record.py`
- `util/ad-hoc/2026-11-09_lock_round_2_probe.py`
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_r-obs-sc-2-cut-pypi-gates-lock-round-next.md` (the ported copy)
- this file

Ignored `tmp/lr2/` holds the trees, facts, runs and venvs. Keep it until the lock round lands (retention rule). Worktree `fizzy-enchanting-deer`'s `tmp/` (the predecessor's evidence) is also still needed.

## Documents referenced / changed

- **Referenced**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (Security delivery L817–826, S0.11 L781–797, H-14 L496/L1450, A1 L1093); `reports/2026-10-04_consolidated-development-plan/round11-laneB2-schedule.md` (R11B2-07); the two predecessor handoffs named above; juniper-data#454, #478, cascor#711, canopy#739, recurrence#199 (PR bodies).
- **Changed**: the six files listed under Git state. Outside the repo: none.
