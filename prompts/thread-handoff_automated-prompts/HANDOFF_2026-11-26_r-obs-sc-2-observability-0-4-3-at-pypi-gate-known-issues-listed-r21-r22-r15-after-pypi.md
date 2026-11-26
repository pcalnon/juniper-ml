# Handoff: R-OBS-SC-2 follow-ups. juniper-observability 0.4.3 is cut and waits at the Overtoad's `pypi` gate, with its Known Issues listed; R21's second pass, R22 and R15 (data, canopy) follow PyPI

**Written**: 2026-11-26, 01:16Z to 12:00Z (`date -u`), by session `cf970cdc`. Worktree
`.claude/worktrees/indexed-floating-umbrella`, branch `worktree-indexed-floating-umbrella`.

**Predecessor**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_r-obs-sc-2-changelog-repair-landed-observability-0-4-3-port-merging-release-cut-next.md`
(juniper-ml#2655). Each of its seven items was checked against GitHub and PyPI, not against its own table.

**The task list** is `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` (the
inventory). Its section "Checked and changed, 2026-11-26" (juniper-ml#2669) holds this session's facts and times in
full. This file adds only what the next session needs to act.

**Merge approval** is per session. This session held it three times: for ml#2666, the cut and its docs-only PRs
(answered 01:47:02Z); for ml#2669 (asked 02:20:43Z, answered 11:26:19Z); then for the whole work arc, in the
Overtoad's message after that answer ("merge approval granted for this work arc"). None of it carries over: ask again.

## Done (check each state first)

| Item | PR / action | State at handoff |
| --- | --- | --- |
| R14's port | ml#2647 | MERGED 2026-11-25 10:41:26Z (`b54f961b`), every check green on head `042030b6` |
| The 2026-11-24 inventory update | ml#2650 | MERGED 12:09:30Z (`dbe9ab30`) |
| The predecessor handoff | ml#2655 | MERGED 20:37:00Z (`0b53d2ab`) |
| The 0.4.3 proposal | ml#2666 | MERGED 2026-11-26 01:47:50Z (`b9442e3c`) |
| The cut | Release `juniper-observability-v0.4.3` | published 02:04:23Z, tag on `b9442e3c`; Known Issues filled (Release + archive) |
| The archive | ml#2667 | MERGED 02:19:08Z (`fcbc5d3c`); the file on `main` equals the filled text and the live Release body |
| The inventory update and the two scripts the Release cites | ml#2669 | MERGED 2026-11-26 11:59:27Z (`6fbcbd85`). Re-cut as one signed commit `eb845378` on `bceac63c` after CodeQL `py/log-injection` (alerts 1135, 1136) on its first cut: the probe's handler logged the body's `host` and `port`, and now logs a constant (findings unchanged on three SDKs) |
| Gate 2 | run 45739959764 | WAITING at `pypi` (the Overtoad's); TestPyPI serves 0.4.3 |

**The Overtoad's rulings of 2026-11-26** (asked 01:33:42Z, answered 01:47:02Z):

- merge ml#2666 and cut the Release;
- the Release lists the three pre-existing Sentry exposures as Known Issues, measured on the wire first (done);
- **R15 for juniper-cascor: add profiling to `configure_sentry`** in a later juniper-observability release; cascor's
  port waits for it and keeps profiling.

## Remaining work (goal)

1. **Gate 2 is the Overtoad's: never approve it.** Run
   <https://github.com/pcalnon/juniper-ml/actions/runs/45739959764>, created 2026-11-26 02:04:26Z.
   - The deadlines: day 30, 2026-12-26, is the last day to re-run it and the cap on its wait at the gate; GitHub
     cancels it on day 35, 2026-12-31. The republish job exists, so §11.8 rung 1 of
     `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` applies after either.
   - Once approved, read `/pypi/juniper-observability/0.4.3/json` (200; the aggregate endpoint lags). Its two files
     must carry TestPyPI's sha256: wheel `4817790d1cf00a3d…`, sdist `14c6c7db679910b1…`.
2. **R21, second pass**: `JuniperData` (`python3.14t`) and `JuniperCanopy1` (`python3.13`) to
   `juniper-observability==0.4.3`; service-core stays 0.7.2.
   - Use the pattern of `tmp/cosmic/r21/{dryrun,upgrade}.bash` in worktree `cosmic-percolating-kazoo`: a dry run
     first, pinned versions, and the constraint `sentry-sdk<3`. Keep the constraint until each consumer's R15 port
     lands.
   - `JuniperCascor1` holds editable installs of the primary: record the primary commit they run.
3. **R22**: re-run the per-lock probe in each environment, with the six DSNs blank and FastAPI's telemetry recorded.
   `util/ad-hoc/2026-11-09_lock_round_2_probe.py`'s steps 3–5 run against an existing interpreter.
4. **R15, data and canopy only**: one PR per repo into `[Unreleased]`, with `juniper-observability>=0.4.3` and `<4` on
   the sentry-sdk floor (data `pyproject.toml:142`, canopy `:251`). Both call only `configure_sentry`.
   - **cascor waits** for the profiling release. Before it can be designed, the Overtoad must rule its number: new
     keyword arguments are a SemVer minor, while R-OBS-SC-3 is ruled 0.4.4.
5. **R53** waits for the session that prepares service-core 0.8.0. Leave it.
6. **Raise with the Overtoad, do not act** (carried):
   - `200f0ce5` wrote a 0.4.0 note into the released `[0.3.0]` bullet;
   - whether to make the observability CI required;
   - the handoff rename on branch commit `c8f4d884` (`HANDOFF_<date>__<description>.md`), which is not on `main`;
   - the profiling release's number (item 4).
   The canopy `authkey` and proxy-header items are now listed in the Release; fixing them is R-OBS-SC-3's work.
7. A **handoff PR** for the next file, containing only that file.

## Key context

- **Signed commits only**: `util/open_signed_pr.py` (a new branch) and `util/push_signed_commit.py --expected-head`
  (an existing one). The isolation guard refuses `git -C`, and compound shells naming git; write scripts with the
  Write tool and run them.
- **Release traps that recurred** (recorded in memory `reference_release_train_ceremony_traps_2026-09-09.md`):
  - `detect.py`'s GitHub path proposed minor for a `### Fixed`-only package;
  - `propose.py` missed the `test_public_api.py` pin and the README floor;
  - the renderer hard-codes "None known at time of release.".
- **The probe and its venvs**: `util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py` (run with
  `PYTHONPATH=juniper-observability`) uses the venvs in `cosmic-percolating-kazoo`'s
  `tmp/cosmic/sentry3/venv-{2.35.0,2.76.0,3.0.0}`. Keep that `tmp/` under the retention rule.
- **This session's records** are in this worktree's `tmp/obs043/`: the manifests and their builder, the simulated
  copy's test logs, the carrier and post-cut drivers, the probe outputs, the rendered and filled notes, and the
  ceremony logs. The simulated copy is in the primary checkout's
  `tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/cf970cdc-c79e-4ad3-b850-f79f2afe6d76/scratchpad/sim-obs043/`.
  Keep both under the retention rule.

## Verification commands (one per call)

```bash
gh api repos/pcalnon/juniper-ml/actions/runs/45739959764/jobs --jq '.jobs[] | "\(.name): \(.status)/\(.conclusion)"'
gh api repos/pcalnon/juniper-ml/actions/runs/45739959764/pending_deployments --jq '.[].environment.name'   # pypi until approved
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/juniper-observability/0.4.3/json          # 404 until approved
gh pr view 2667 --repo pcalnon/juniper-ml --json state,mergedAt
gh pr view 2669 --repo pcalnon/juniper-ml --json state,mergedAt
```

## Git status (12:00Z)

- This worktree, branch `worktree-indexed-floating-umbrella`, is at `6fbcbd85` (= `origin/main` at 12:00Z) and clean,
  apart from the ignored `tmp/`. This file is new, and lands in its own PR.

## Documents referenced / changed

- **Referenced**: the predecessor; `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`;
  `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§11.7, §11.8);
  `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`.
- **Changed, through PRs**:
  - `juniper-observability/pyproject.toml`, `juniper-observability/juniper_observability/_version.py`,
    `juniper-observability/CHANGELOG.md`, `juniper-observability/tests/test_public_api.py` and
    `juniper-observability/README.md` (ml#2666);
  - `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.3.md` (ml#2667);
  - `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`,
    `util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py` and
    `util/ad-hoc/2026-11-26_observability_0_4_3_known_issues_notes.py` (ml#2669);
  - this file.
- **Changed outside the repo**: the Release body of `juniper-observability-v0.4.3`, and the memories
  `reference_sentry_sdk_3_is_a_redesign.md`, `reference_release_train_ceremony_traps_2026-09-09.md` and
  `reference_codeql_unused_global_cascor.md`.
