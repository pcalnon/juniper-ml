# Round 4 — Lane B (attack the round-3 corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-4 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round4-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` below) v1.3.0. sha256 prefix `51226ccf258bb19f` at 11:13:40Z and again at 11:43:09Z on 2026-10-05, so it was unchanged. "Lnnn" is one of its lines; "tool Lnn" is a line of `util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py`. Other short forms are the ones `…CONSOLIDATED-DEVELOPMENT-PLAN.md` defines.
  - **Read**: the v1.2→v1.3 diff, `round3-reconciliation.md`, `round3-laneA-reprobe.md`, `round3-laneB-attack.md`; the whole of `…CONSOLIDATED-DEVELOPMENT-PLAN.md`; and local files at `cf711cf4`: the probe tool, `…CONSENSUS-PROCEDURE.md`, `…RECOVERY-PLAN.md`, `…INTEGRATED-DESIGN.md`, `EX/extraction-P6-perf.md`, `juniper-observability/`.
  - **REST**, read-only, 11:14–11:43Z: `main` of cascor, cascor-client, canopy, data, data-client, recurrence (and its `juniper-recurrence-v0.5.0` tag), ml and cascor-worker; juniper-data's public scheduled-job log; `…equities-p0-executed-go-verdict-p1-next.md` on ml `main`.
  - **Installed packages, read-only**: sentry-sdk 2.58.0, requests 2.33.1, juniper-data-client 0.5.0 and juniper-observability 0.4.0 in `JuniperCascor1`.
  - **Ran**: the probe once, as briefed (`--config .gitleaks.toml --workdir` under the session scratchpad's `round4/`), and one `python3 -c` regex comparison on synthetic fakes. No secret, `.env` or transcript was read; there were no host actions.
- Entry point: the round-3 corrections (the v1.2→v1.3 diff and `round3-reconciliation.md`)

## Findings

| ID | Severity | Plan location (v1.3) | What the correction says | What it broke (evidence: file:line, command → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R4B-01 | BLOCKER | L273–277; §9 L784–785 | Every public push is Hard-gated, "permanently", on the probe's `--scan-dir` | **Fails open.** `scan()` drops gitleaks' exit code (tool L88) and reads a missing or empty report as no findings (L89–90). `--scan-dir` then prints "0 finding(s)" and exits 0 (L129–130).<br>So a mistyped path, an empty copy, a config error or CLI drift in the unpinned `latest` scanner (L104) all pass. No canary runs | Fail closed: refuse a missing or empty dir, print the files scanned, require exit 0/1 plus a report, run a canary, and pin v8.30.1 by sha256 |
| R4B-02 | MAJOR | L81, L164, L337, L364, L606, L904 | The relays are recurrence and cascor only: 3 paths | **Canopy relays cascor's 409 onward.** It logs `{e}` at ERROR and returns `outbound_error_text(e)` (canopy `src/backend/cascor_service_adapter.py:1114–1116`). That passes any error with an int `status_code` verbatim (`src/outbound_errors.py:61`), to surfaces "an anonymous caller can read" (`:25`). cascor-client sets it on a 409 (`client.py:623–624`).<br>L81's "hides 5xx" is a different path, and A1's "keep 4xx" omits this | Count 4 paths, add canopy to H-22 and XC-CRED, and say so at A1 |
| R4B-03 | MAJOR | L82, L371; S0.11 L455 | A data-client fix that never quotes a header value covers every consumer | **Every hop chains the cause**: data-client `from e` (`client.py:349–351`); cascor `from exc` (`manager.py:4955`, `training.py:337`).<br>Cascor's Sentry runs on observability 0.4.0, whose before_send scrubs headers only (`sentry.py:23–37`). It captures 5xx `HTTPException`s by default (sentry-sdk `integrations/__init__.py:12`) with `__cause__` (`utils.py:905–944`). So the key reaches Sentry | Require `from None` or a sanitized cause, with a chain test, and name Sentry in H-22 |
| R4B-04 | MAJOR | §5 L572, L582; §9 L779; L606 | The vehicle "closes the relay for PyPI and image users"; a data-client fix ships as a patch | **Cascor.** The image installs `requirements-cpu.lock` (`Dockerfile:41–42`), pinned to `juniper-data-client==0.5.0` (L120), as is `JuniperCascor1`. No cascor lock PR, image cut or environment upgrade is scheduled (compare §9 L776–777).<br>**Option (b).** The fix waits for W1.13, "publications last" (`…equities-p0-executed-go-verdict-p1-next.md` L36), and for ml's `<0.6.0` cap (`pyproject.toml:105`) | Add those steps and edges, and state (b)'s delay at A1 |
| R4B-05 | MAJOR | L226, L377, L526; L712; L664–668 | Phase 1 no longer waits for R5, and is "Next" | **Phase 1 still waits on owner rulings.** It opens with data-client W1.4 (R2), then W1.3 (R8) and W1.2 (R7) (`…equities-p0-executed-go-verdict-p1-next.md` L32, L35). The plan puts R2/R3/R7/R8 in Group B.<br>§7.1's four sittings omit Group B, so it is either an uncounted fifth sitting or falls after Wave 1. Either way Phase 1 stalls | Rule the dates and R2/R3/R7/R8 at Wave 0 step 8, or count Group B and say Phase 1 waits for it |
| R4B-06 | MAJOR | §7.1 L692, L695, L710–711 | 13–15 rounds and 20–22 runs, with one agent per F-S10 fix and per XC-LEAKS PR | **Sizing.** `…CONSENSUS-PROCEDURE.md` sizes a high-criticality item with a fix hanging on it at 2 Lane A + 1–2 Lane B (L81, L84, L93).<br>**Iteration.** A round with corrections needs another (L104–106); `…CONSOLIDATED-DEVELOPMENT-PLAN.md` took four.<br>So the totals are a floor, and rounds of three or more agents cannot overlap under the cap. "Up to five" cannot make 13 the floor | Size S rounds per §3, allow for a second round, and call the totals a floor |
| R4B-07 | MINOR | L274; §9 L785 | The interim rule is "B9-class" (`round3-reconciliation.md` L17 calls it "a superset") | **Not a superset.** Its `\b` (tool L63) cannot match after `_`. On synthetic fakes it misses `COMMENTED_PASSPHRASE=`, `TIER2_PASSPHRASE=` and `export DUPLICATI_PASSPHRASE=`, all of which B9's unanchored form (`…RECOVERY-PLAN.md` L227) matches. The first appears in `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md:69` | Drop the `\b`, and plant a prefixed name in the probe |
| R4B-08 | MINOR | L295, L301; §9 L786 | juniper-data's PR goes last and turns off the summary and artifact for `schedule` | **The job log still publishes.** Data's 06:37Z scheduled run executed `detect --redact -v --exit-code=2 …` with no `--log-opts` ("1094 commits scanned"; job 111644816909's log). `-v` prints each hit's file, line and commit.<br>Rotated hits stay in history, so without a baseline the daily run will also fail every day | Keep rotation first. Then drop or narrow data's scheduled history scan, or land the baseline in data's PR |
| R4B-09 | MINOR | L297–302 against L433, L608 | XC-LEAKS runs "in this order", with the settings as step 4, after the scans, rotation and config PRs | Wave 0 step 7 and A3 turn the settings on in the first sitting, before step 1. GitHub's alerts are not public, so the early position is the safe one, but the table says otherwise | Mark step 4 as independent of steps 1–3 |
| R4B-10 | MINOR | L345–346 | Rule, then compact with snapshots; "P6-34 … says to fix those gates first" | P6-34 reads "First fix the gates that do not read hook text" (`EX/extraction-P6-perf.md` L72). The plan quotes that order, then schedules no gate fix, so compaction follows the ruling directly | Insert the gate fix before step 2, or have the owner accept the snapshots in its place at A6 |
| R4B-11 | MINOR | §5 L572, L582; §8 L761 | A data-client fix "ships as a data-client patch"; §8 says "F-S10 first; one PR at a time" | §8 orders the PRs, not the cut, and §5's order has no slot for the patch.<br>W1.4 opens Phase 1 (`…equities-p0-executed-go-verdict-p1-next.md` L35) and is part of P12's 0.6.0 claim (L589–592). Once it merges, `main` cuts 0.6.0, past the `<0.6.0` caps in recurrence (`juniper-recurrence/pyproject.toml:54`) and canopy (`pyproject.toml:192`) | Cut the patch before W1.4 merges, and give it a §5 slot and a §9 edge |
| R4B-12 | MINOR | §7.2 L742 | The two env-variable overrides need the owner's OK | Both launchers' primary override is the `--skip-env-preflight` flag (`util/experiment_stack.bash:1309`, `util/isolated_stack.bash:663` on `main`). The refusal message itself tells the operator to pass it (`:357`, `:329`). The rule as worded does not cover the flag | Name the flag in the rule |
| R4B-13 | MINOR | §9 L785; L259, L268 | P1-09 and P1-10 are Hard-gated on the probe's scan | The tool is untracked here and absent from `main`: `contents/util/ad-hoc?ref=main` lists 963 entries, none of them the plan's five instruments. A P1-09/P1-10 session started inside `cached-swinging-summit`, as L259 requires, cannot run it, and nothing orders the `…CONSOLIDATED-DEVELOPMENT-PLAN.md` PR first | Add a §9 edge: that PR merges before P1-09 and P1-10 |
| R4B-14 | MINOR | §1.3 L203–204 | At most three validation agents at once, account-wide | The cap counts validation agents only. But the loss it cites (L200) was to the usage window, which every agent draws on: the planning session ran ten extraction agents (L1144). There is also no ledger or probe that lets a session see the account-wide count | Cap all agents, or name how a session reads the count |
| R4B-15 | MINOR | L416–434; L436–455 | A session drafts A6's set "before the sitting"; the S0 sessions then run in parallel | No S0 item drafts A6. S0.9 (A1's asks) and S0.10 (P9-13, which A8 needs at step 8) must also come before the sitting, and the plan does not say so. Step 1 also drops A1's third ruling: when to swap W0.1's service-core half (L606) | Add an S0 item for A6, mark S0.9 and S0.10 as pre-sitting, and list the W0.1 timing in step 1 |
| R4B-16 | MINOR | L7; L1144; L1151–1161 | Round 4 "is recorded in the Validation record"; "Rounds 3 and 4 ran two agents and one" | The Validation record has no round-4 entry, and L1144 states round 4's result before it ran. "Changed by this plan" omits `round3-laneA-reprobe.md`, `round3-laneB-attack.md` and `round3-reconciliation.md`. A row-q file list drawn from it would leave those three single copies behind | Say round 4 is pending, and add the three files |
| R4B-17 | NIT | L256, L295, L667–668, L1147 | R3B-11 rewrote the bare references | These forms remain:<br>- "**Method** (validation rounds 1–2)", although round 3 rewrote that method;<br>- "round-3 lane B", meaning `EX/round3-laneB-attack.md`;<br>- "that handoff", twice, in a passage that also cites `…EQUITIES-CV-BLOWUP-INVESTIGATION.md`;<br>- "`AGENTS.md` § Script placement", which is now ambiguous because the ecosystem guide is also an `AGENTS.md` | Name each file |

There are no findings at any other severity: the table holds 1 BLOCKER, 5 MAJOR, 10 MINOR and 1 NIT.

## Corrections checked and sound (short)

- **No stale forms remain.** "R-RECURRENCE-SEC", "padded", "until W1.14", "Hard until", "three sittings" and safety-round exemptions are all gone. "The W5.1 note" now appears only beside its filename (L45, L377, L700).
- **The sitting.** Each of A1–A8 has exactly one slot (A5 is split on purpose). The mid-wave, Group B and Group C lists repeat none of them; R4B-15 covers A1's W0.1 timing.
- **The probe reproduces with scanner v8.30.1.**
  - Default rules: token 1/1, passphrase 0/1. The tool's config: 1/1 and 1/1. juniper-ml's `.gitleaks.toml`: 0/1 and 0/1.
  - `scan-config.toml` is written to `--workdir` in both modes (tool L112–113). `--scan-dir` runs with `--no-git` (L88) and passes `--config` (L128), and the `GITLEAKS_CONFIG*` variables are stripped (L87).
- **juniper-data's cron** runs daily (the latest run was 2026-10-05T06:36Z) on gitleaks 8.24.3, auto-loads `.gitleaks.toml`, and passes no `--log-opts`. That is R3B-03's mechanism.
- **Row k (R3B-02).** `…INTEGRATED-DESIGN.md` L1749 and L2457 require the *reports* to be archived verbatim, not the transcripts. Archiving the lane reports' final text satisfies that.
- **F-S10 facts.**
  - Code search finds `map_data_error` called only from the train, predict and crossval routers.
  - The relay is identical at `juniper-recurrence-v0.5.0`, so option (a) has something to fix.
  - Data-client `main` is 23 ci/deps/docs commits past v0.5.0, and its `[Unreleased]` section holds only Fixed entries, so a patch cut is coherent today.
  - Cascor's data-client extra is uncapped (`>=0.3.0`), so "covers cascor once cascor runs the patched client" holds for response bodies.
  - `api/secrets.py` L35/L42 and `training.py` L130/L337 match the citations.
- **XC-FLEET.**
  - ml#2125's body says "Do not merge #2122". Canopy #698 and #700 share a title, and #700 and #701 are `dirty`.
  - ml#2122 has since turned `dirty` (drift after 10:51Z). "Close" still holds.
- **The §7.1 sums are internally consistent.** 7×2 + (1–3) + 5 gives 20–22 runs. 13–15 rounds take 5–8 days at 2–3 per day, or 7–15 days at 1–2 per day. R4B-06 disputes the premises, not the arithmetic.
- **Counts.** The six *(v)* IDs and round 3's per-lane finding counts are right. Group B's P12 order matches `…equities-p0-executed-go-verdict-p1-next.md` L32 and L34.
- **XC-LEAKS scope.** §7.1 and §8 agree on five config PRs. Data-client and cascor-worker have no `.gitleaks.toml`, and worker's CI scans with the default rules.

## Could not check

- **Host state**:
  - whether `JUNIPER_DATA_API_KEY`'s environment value has leading whitespace or a line break;
  - whether the running cascor and canopy have a Sentry DSN;
  - whether the running cascor has loaded the installed data-client 0.5.0.
- **gitleaks' behaviour on a missing or empty `--scan-dir`.** The brief allows only the planted mode. R4B-01 rests on the tool's code, which passes whatever gitleaks does short of writing findings.
- **gitleaks-action's source at `e0c47f4f`**, because of the command-hygiene rule. Its arguments come from the public job log. That a scan with hits fails the job is inferred from `--exit-code=2`.
- **Canopy's auth configuration.** Whether canopy's start-route result reaches an anonymous caller under the deployed settings; R4B-02 relies on `src/outbound_errors.py`'s own docstring (L25).
- **`pr2115.md`**, which is in another worktree.
- **Recurrence `main`'s #172/#190 content.** Round 3 re-derived it.

## What this report cannot support

- **Severities are judgement.**
  - R4B-01 rests on a code path, not on an observed bad push.
  - R4B-02 and R4B-03 both need the key condition, and R4B-03's Sentry path also needs a DSN.
- **State after 2026-10-05T11:43Z.**
- **Unchanged text**: lines outside the round-3 diff, beyond those named above.
- **Which vehicle the owner chooses.**

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round4-laneB-attack.md`. The probe's download, planted fakes and report went to a workdir under the session scratchpad, outside every repository.
