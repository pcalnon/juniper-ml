# Cursor-Fleet Flood #3 — Disposition Record

**Project**: Juniper (ecosystem-wide)
**Author**: Paul Calnon
**Status**: Complete — each of the 116 draft PRs is merged, or closed with its content carried or the reason it was rejected recorded (§5)
**Date**: 2026-10-08
**Updated**: 2026-10-08 — the owner-requested follow-up: three `ANTHROPIC_API_KEY` secrets, five §4 defects fixed, and three releases cut (§4, §8, §9)
**Applies to**: juniper-ml, juniper-data, juniper-canopy, juniper-cascor, juniper-data-client, juniper-deploy, juniper-cascor-client, juniper-cascor-worker

---

## §0 What this document is

The record of how the third Cursor-fleet draft-PR flood (opened 2026-10-04..06) was evaluated and disposed of on 2026-10-08, under the owner's instruction to evaluate each draft for quality, correctness and priority and then merge, close, update, document or complete it, with merge approval granted for the set. Round 1 is `notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`; round 2 is `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`, whose §4 lessons this round applied. §5 is the per-PR outcome; §4 lists the defects the evaluation found on `main`; §6 the process traps hit along the way.

## §1 Scope

116 open drafts across eight repositories: 115 from `app/cursor` (the "Add test coverage", "Generate docs" and "Find critical bugs" automations) and one from `app/copilot-swe-agent` (juniper-data#454). `juniper-recurrence` and the non-Juniper repositories had none. Census: `util/ad-hoc/2026-10-08_fleet_flood3_census.py` (org-enumerated roster, live required-context sets, compare API).

| repo | docs | test | fix | total |
|---|---|---|---|---|
| juniper-ml | 23 | 23 | 1 | 47 |
| juniper-data | 12 | 11 | 1 (Copilot) | 24 |
| juniper-canopy | 11 | 11 | 1 | 23 |
| juniper-cascor | 4 | 5 | 0 | 9 |
| juniper-data-client | 3 | 4 | 0 | 7 |
| juniper-deploy | 1 | 1 | 0 | 2 |
| juniper-cascor-client | 1 | 1 | 0 | 2 |
| juniper-cascor-worker | 1 | 1 | 0 | 2 |

What the census showed before any evaluation:

- **Every PR was behind `main`** (1–15 commits), and every repo's ruleset is strict (up-to-date) — so each merge forces every sibling to re-sync and re-run a full CI cycle.
- **CI had never run on a large share of them.** Either `Pre-commit` failed on the bot's own files (so the test job, which `needs:` it, skipped), or the PR was opened against another session's feature branch (`Guard PR base branch` failed and every other required context stayed MISSING).
- **Nineteen PRs carried other sessions' already-squashed commits**: twelve juniper-ml test PRs (ml#2133, #2136, #2138, #2140, #2144, #2147, #2149, #2150, #2166, #2169, #2173, #2174), data#452 and #453 (data#451), canopy#699, #701, #704 and #724 (#697, #702, #722), and data#454 (the merged dependabot group #446). Taking those branches as-is would have re-applied stale copies of work `main` had since moved past — for seven ml branches and two canopy branches, a conflict resolved toward the PR side would have reverted later work (ml#2164's W1.9/W1.10 edits, the rerun helper's 0.2.0 `--accept-degraded`, canopy#722's 401/403 wording).
- **The docs PRs conflict with each other by construction**: every one bumps the same `**Version**` lines as though its siblings had landed first (ml#2181 moved `docs/REFERENCE.md` 0.6.59 → 0.6.82 for one change). 46 of 47 juniper-ml PRs touch `docs/REFERENCE.md`.

## §2 Method

**Evaluation.** Ten parallel evaluators, one shared brief, each owning a slice (juniper-ml docs ×2, tests ×2; juniper-data docs, tests; juniper-canopy docs, tests; cascor + deploy; the three client repos). For every PR: the true delta against current `main` (`git merge-tree`, carried commits dropped); redundancy and duplicate adjudication across all 116; **tests re-run on `main`** in the repo's real environment, with one-line mutations of the code under test to prove non-vacuity (every mutated file restored byte-for-byte); **every docs claim re-derived from the code**; fixes reproduced on `main`. Each PR got a quality (SOLID / WEAK / BROKEN), a priority (P1 real defect / security / gate; P2 risky untested behaviour or a live operator contract; P3 low-risk) and a verdict. Each evaluator then prepared the accepted content, corrected, as an uncommitted patch on `main`, with the repo's pinned pre-commit and the relevant suites green.

**Landing.** Local `git commit` cannot sign headless (YubiKey), and `required_signatures` is on everywhere, so every commit is GitHub-signed through GraphQL `createCommitOnBranch`:

- A PR whose content stands alone **merged as itself** — unchanged ones by server-side `update-branch`; corrected ones **re-cut on current `main` as one signed commit** (`util/ad-hoc/2026-10-08_fleet_flood3_reset_pr_branch.py`: temp branch at `main`, signed commit, force-move of the PR head, guarded on the branch tip), with the fleet author kept as co-author.
- Clusters that collide (the docs PRs everywhere; juniper-ml's test PRs, which all edit the same three hand-maintained CI lists) and canopy's test PRs (~20 min CI per strict-lane cycle) were **consolidated into one PR per repo**, built from the evaluators' patches on fresh `main`.
- Native auto-merge (squash) armed on everything; `util/ad-hoc/2026-09-05_auto_merge_shepherd.py` re-synced one PR at a time per repo.
- A carried or superseded PR was closed **only after its carrier merged**, with a comment naming the carrier and the evaluation (`util/ad-hoc/2026-10-08_fleet_flood3_disposition_render.py --closes` + `util/ad-hoc/2026-10-08_fleet_flood3_pr_actions.py close`). Closing is not destructive: GitHub keeps a closed PR's diff.

## §3 What the evaluation found

- **Tests were behavioural, again.** Every carried suite fails under one-line mutations of the code it pins (e.g. 81/81 + 6/6 in one juniper-ml slice, 44/44 in canopy, 25/25 in the client repos). Round 2's figure (88%) holds up.
- **But about one in five of the 57 test PRs was broken or mis-shaped beyond lint as submitted** (and many others failed lint) — in ways CI never showed, because CI never ran them:
  - *global state leaks*: canopy#715 replaced `time.monotonic` / `time.sleep` on the global `time` module and never restored them, failing five unrelated tests on every leg;
  - *platform assumptions*: GNU `base64 -w0` and `date -d` inside `$(…)` (which `set -e` does not catch) made the required macOS leg fail deterministically (data#458, #467; data-client#221);
  - *interpreter assumptions*: an unclosed synthetic `HTTPError` under Python 3.14 + `filterwarnings=error` (deploy#241); a `requests` stand-in lacking `Session` that crashed at import on 3.12/3.13 (ml#2143);
  - *repo policy*: a suite that executed the watchdog deploy script, which `tests/test_yamaguchi_watchdog.py` forbids (ml#2138); raw `os.environ.copy()` that `tests/test_env_repr_safety.py` forbids (ml#2159);
  - *lint*: black / mypy / bandit / flake8 findings that failed `Pre-commit` and hid everything else.
- **Docs were well-grounded and stale.** As in round 2, almost every false claim was a snapshot that had been true when the branch was cut (a PR saying "#702 is not merged yet" written twelve minutes before #702 merged). One systematic error recurred in **five repos**: "`contains()` is case-sensitive, so `@Claude` does not start the job" — false (GitHub's `contains()` ignores case and the action's phrase match is case-insensitive). One docs PR (ml#2141) asserted the opposite of the consensus record that merged after it was cut, and was closed.
- **Three real fixes**: canopy#721 (P1, below), data#454 (FastAPI 0.142 native-telemetry opt-out — hardening, not a live leak), and ml#2129 (already landed as ml#2134, which supersedes it).

## §4 Defects found on `main`

| repo | defect | status |
|---|---|---|
| canopy | **The wheel omitted `outbound_errors`**, which `main`, `status_cache`, the cascor adapter and the recurrence backend import; `publish.yml`'s import smoke would have stopped the next release at the build job (`main`'s CI never runs the smoke) | **fixed** — canopy#721 |
| canopy | Flaky required test `TestA422DetailReachesTheOperator::test_completion_reason_and_the_warning_carry_the_detail`: a failing fit logs its WARNING after the state flips, so a preceding test's record landed in the next test's `caplog` (failed `main`'s macOS leg at #702, #708, #711) | **fixed** — canopy consolidation (autouse join of `recurrence-fit` threads) |
| cascor + service-core | `FailedAuthThrottle.check()` — documented read-only — inserts an entry per new client IP; the 10,000 cap is applied only in cleanup, which only `record_failure` runs, so the table grows without bound under open auth or valid keys (`src/api/security.py`; canonically `juniper-service-core/juniper_service_core/security.py:455`) | **fixed** — `_failures` is a plain `dict` read with `.get()` in all three copies: ml#2187 (service-core), juniper-cascor#710, and juniper-data#476 (juniper-data holds a third copy this row did not name). Each repo pins it with its own regression test, and each test fails against the old code with `assert 1000 == 0` |
| ml | `util/worktree_cleanup.bash:461`: the "These commits would be lost" list is always empty (`--not --branches` excludes the refused branch itself); the refusal itself works | **fixed** — ml#2187 (`worktree_cleanup.bash` 1.1.1, `--exclude` before `--branches`); `tests/test_worktree_cleanup_destructive_refusal.py` now asserts the commit is named |
| ml | `util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py checks` exits 1 (`NoneType.__format__`) after writing its JSON when every last-step feature column is constant | open (low) |
| ml | `util/ad-hoc/2026-10-05_rerun_after_actions_outage.py:55` — a dict-shaped `components` aborts the wait (fails closed; pinned by the harvested suite) | open (low) |
| ml | cascor headline accuracy columns are always empty — the open cascor half of APD-ML-002 | already registered (defect register §4.9) |
| data-client, cascor-client, cascor-worker | **`@claude` cannot run**: none has an `ANTHROPIC_API_KEY` secret and all three are user-owned, so no organization secret reaches them; the job has skipped on every recorded run | **fixed** for these three: the owner added the secret on 2026-10-08. **The gap was wider than this row said.** juniper-data, juniper-cascor, juniper-canopy and juniper-deploy have no `ANTHROPIC_API_KEY` either; only juniper-ml does, so `@claude` cannot run in those four. The fleet `claude.yml` header says the key is "set at the org level", and no user-owned repo can have one. The four repos remain **open (owner decision)** |
| data-client, cascor-client, cascor-worker | `lockfile-update.yml` builds the commit payload with `--arg contents "$(base64 -w0 …)"`; a failing `base64` would not trip `set -e` and would produce an empty signed lockfile commit (latent: cannot happen on `ubuntu-latest`) | open (latent) |
| data-client | the `t` / `dt` agreement check is `np.allclose` with numpy's default `rtol=1e-5` as well as `dt_atol` (9e-6 accepted at a gap of 1.0; 0.5 at 86400) | **accepted as written** — owner ruling 2026-10-08; the docs describe what the code does |
| canopy | `lockfile-update.yml:173-175` inverts `[dependabot skip]`'s meaning; #709's signed lock-regen commit was erased by Dependabot's rebase | **fixed** — canopy#730. The comment now states the tag's real effect (Dependabot may force-push over the commit). The tag stays deliberately: each Dependabot rebase is a push to `dependabot/pip/**`, which re-runs the regen, since the PAT is in the Dependabot secret store. The other five repos tag their regen commits the same way |
| data | `docs/DEVELOPER_CHEATSHEET.md` links `../AGENTS.md#adding-new-generators`, which moved; `juniper-check-doc-links` 0.1.2 checks only same-file anchors, which is how it survived | open |
| cascor, cascor-client, cascor-worker, data | Docs still call Sequence Safety "advisory / never required" (cascor `AGENTS.md:594`, `:643`; cascor-client `docs/REFERENCE.md:711-716`, `:727`; cascor-worker `AGENTS.md:256-266`; one line in data `docs/REFERENCE.md`); every ruleset requires it. data-client's copy was corrected by its consolidation | **fixed** in every repo — juniper-cascor#710, juniper-cascor-client#178, juniper-cascor-worker#207, juniper-data#476, juniper-canopy#730, juniper-deploy#244, juniper-recurrence#194, juniper-data-client#231 (two workflow comments its consolidation missed), and ml#2187 (`ci.yml`'s header and banner). cascor#710 also corrected CodeQL claims: cascor's ruleset requires `Analyze (python)` |
| juniper-ci-tools | the docs deletion screen reads `#` comments inside fenced code as headings (`docs_additions_check.py:192-195`) — five of cascor#704's six Sequence Safety findings | **fixed** in source — ml#2187: CommonMark-fence-aware, on both sides of the diff. It reaches the eight consumer repos only with a juniper-ci-tools release, since they pin `>=0.9.0,<0.10.0` (**owner decision**) |
| service-core, observability, data (**released packages**) | the non-ASCII-key 500 and Sentry frame-locals fixes (ml#2086, data#440) are in **no release**: juniper-service-core 0.7.0 still compares keys as `str`, juniper-observability 0.4.0 still captures frame locals, juniper-data 0.16.0 has the same `str` compare (cascor and canopy `main` already compare bytes) | **released** (owner instruction, 2026-10-08), each through the release train: <br>• juniper-observability **0.4.1**: bump ml#2186, notes ml#2188. <br>• juniper-service-core **0.7.1**: bump ml#2189, notes ml#2193. It also carries the `FailedAuthThrottle` fix (ml#2187). <br>• juniper-data **0.17.0**: bump data#477, notes ml#2191. It also carries data#476, X8 and the image lock moves. <br>All three Releases are cut, have published to TestPyPI, and wait at the `pypi` environment gate for the owner's approval. The security template's advisory placeholders were filled in each Release body and archive |
| ml | four places in `docs/REFERENCE.md` / the cheatsheet said a pin-stable lockfile week opens no PR; all 12 scheduled runs opened one | **fixed** — ml#2184 (#2155) |
| ml | stale on `main`, outside every PR: "in-flight docs #1675" (closed unmerged) in `docs/REFERENCE.md` and `util/ad-hoc/README.md:114`; "Live `run_fix` (open #802)" (#802 merged 2026-07-27); two isolated-stack paragraphs duplicated at the end of the Environment Floor Drift Check section; "the CLI has no `--params` flag" in `run_experiment.py:61`, `:2009` (false since juniper-recurrence#190); recurrence split lists `{train, test, full}` where the code has `{train, val, test, full}`; rows describing the deleted silent `max_symbols` slice; `stats_summary.py:251` labelling θ "data-driven" even when `service.default_theta` is set | open |
| ml | `util/ad-hoc/2026-10-04_replay_redrive.py`: the `if not snap:` check can never trigger (dead BLOCKED row), and `--snapshot` help says "instead of the newest" though the default makes a new save | open (low) |
| data, data-client | `pr-budget-alarm.yml` headers say a `jq` failure is downgraded to a warning; the script fails the step | open (low) |
| data | the Quality Gate passes when an optional lane is `cancelled` (each such lane is also its own required check, so mitigated) | open (low) |
| recurrence | `.github/workflows/memory-budget.yml:23-25` says Memory Budget is "not a required context"; ruleset `20634527` requires it (found by the 2026-10-08 Sequence Safety sweep) | open |
| cascor-client, cascor-worker, deploy, recurrence | `main-verify.yml`'s header says the catch-up base is the "most recent SUCCESSFUL" run. Since cascor-client#153 it is the newest run whose "Assert screens reached a verdict" step passed. The cascor-client line is confirmed; the other three repos' resolvers are unchecked | open |
| cascor | `docs/ci_cd/BRANCH_PROTECTION.md:28-55` lists 6 of the 24 live required checks. `:67` / `:69` say one approving review and a code-owner review are required; the ruleset requires 0 and `false` | open |
| cascor | `ci.yml:988` and `conf/memory_budget.json:36` say cascor has no `docs/REFERENCE.md`; it does | open (low) |
| cascor | `docs/DOCUMENTATION_OVERVIEW.md:811-812`: this arc's own consolidation (cascor#709) bumped the version and date inside a template example instead of the document header | open (low) |
| data | `docs/ci_cd/CICD_MANUAL.md:456` says CodeQL findings "don't block the merge". The ruleset's `code_scanning` rule blocks on CodeQL / Bandit alerts at errors / security `high_or_higher`. `docs/DEVELOPER_CHEATSHEET.md:313`'s workflow list omits `sequence-safety.yml` and `main-verify.yml` | open (low) |

## §5 Per-PR disposition

Rendered from `util/ad-hoc/2026-10-08_fleet_flood3_disposition.json` (the verdicts) and each PR's live state by `util/ad-hoc/2026-10-08_fleet_flood3_disposition_render.py`. **Carrier PRs**: juniper-ml #2182 (tests) and #2184 (docs); juniper-data #475 (docs); juniper-canopy #729 (tests + docs); juniper-cascor #709 (docs + API tests); juniper-data-client #230 (docs).

| repo | merged as itself | carried | superseded | closed: wrong | total |
|---|---|---|---|---|---|
| juniper-ml | 0 | 39 | 5 | 3 | 47 |
| juniper-data | 11 | 11 | 2 | 0 | 24 |
| juniper-canopy | 1 | 19 | 3 | 0 | 23 |
| juniper-cascor | 3 | 6 | 0 | 0 | 9 |
| juniper-data-client | 4 | 3 | 0 | 0 | 7 |
| juniper-deploy | 2 | 0 | 0 | 0 | 2 |
| juniper-cascor-client | 2 | 0 | 0 | 0 | 2 |
| juniper-cascor-worker | 2 | 0 | 0 | 0 | 2 |
| **total** | **25** | **78** | **10** | **3** | **116** |

### juniper-ml (47)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #2119 | docs(reference): operator runbook for the Duplicati web API clients | docs | WEAK | P2 | superseded; unique content in #2184; **closed** | Duplicati web API clients runbook, cut before ml#2134 merged: '--backup-id is required' (main defaults it to '' and records a durable ALERT JOB_MISSING), export without the operation-token step, and 'empty stdout is load-bearing' (main's docstring: hygiene, not protection) are false on main. Superseded by #2177's section; its duplicati_api.py row is carried. |
| #2121 | test(watchdog): pin active-task scope and a mid-scan log failure | test | SOLID | P2 | carried in #2182; **closed** | Watchdog active-task scope. Carried verbatim. |
| #2122 | docs(reference): operator runbook for the CAN-015 replay re-drive | docs | WEAK | P2 | superseded; unique content in #2184; **closed** | Same CAN-015 replay re-drive section as #2125, branched before #2120 landed (it calls the wrapper and driver 'not on main yet'). Superseded by #2125; its verified unique content (the canopy-to-cascor parameter-name table, when cascor reads the snapshot directory, the max_epochs/output_epochs fallback, the player's response unwrapping and scrubber comparison, the F-CANOPY-015/-056 tags) is carried in #2125's section. |
| #2124 | test(duplicati): pin call() 401 retry and error-body returns | test | SOLID | P2 | carried in #2182; **closed** | Duplicati call() 401 retry and error bodies. mypy annotation; bandit literals moved to named constants (the cause of its failed pre-commit). |
| #2125 | docs(reference): on-main CAN-015 replay re-drive wrapper | docs | SOLID | P2 | carried in #2184; **closed** | On-main CAN-015 replay re-drive wrapper. One false claim: cascor reads the snapshot directory per call in manager.py and once at import for the auto-writer (constants_hdf5.py), not 'at process start'. The port 8223 / --down wording, the 600 s fit wait and --skip-train are made precise; two unsupported lines dropped; a cheatsheet row moved. |
| #2127 | test(backup): pin fail-closed delete, pause read-back, and stale-while-paused | test | SOLID | P1 | carried in #2182; **closed** | Fail-closed delete, pause read-back, stale-while-paused; pins that delete without --remote-files never sends the remote-delete query. black, bandit B105. |
| #2128 | docs(reference): Duplicati export needs an operation token | docs | BROKEN | P2 | closed -- incorrect on main; **closed** | Its core claims are false since ml#2134 ('the client never calls issuetoken and never sets token='; 'the stub answers export with 200, so the suite stays green') -- it documents the bug #2134 fixed. Its job-2 helper list is carried into #2177's section, corrected to eight defaults plus four hard-coded sites. |
| #2129 | fix(backup): issue the single-operation token Duplicati 2.4 export requires | fix | WEAK | - | superseded; **closed** | The Duplicati 2.4 export-token fix landed as ml#2134, which names this PR as superseded; main's version is a safer superset (this one would print a non-error token response and accept an export with no target URL). Its test file fails 2 of 33 against main. Nothing unique to carry. |
| #2132 | docs(reference): recurrence crossval fills omitted train keys from service defaults | docs | SOLID | P2 | carried in #2184; **closed** | Recurrence crossval hyperparameters (base of the merged section with #2172). `GET /v1/crossval/status` never shows a run in flight; `enabled: false` disables CV; the driver always sends `train:` keys (pitfall reframed as a hand-written POST). |
| #2133 | test(recurrence): pin the W0.9 z-score guard and a create with no dataset id | test | SOLID | P3 | carried in #2182; **closed** | W0.9 z-score guard and a create with no dataset id. Branch conflicts with main (carries ml#2130); only its own test commit carried. mypy; stale suite count dropped. |
| #2135 | docs(reference): recurrence degraded outcome and headline r2 columns | docs | SOLID | P2 | carried in #2184; **closed** | Degraded outcome and headline r2. Three stale 'main does not contain #2145' statements corrected (it does); not_reached becomes degraded only after a successful train. |
| #2136 | test(experiments): pin degraded-phase and headline edges the W0.3/W0.4 suites do not reach | test | SOLID | P2 | carried in #2182; **closed** | Degraded-phase and headline edges. Cut from closed ml#2131's branch (v1 and v2 code are byte-identical); never ran in CI. mypy. |
| #2137 | docs(reference): Duplicati export issues the operation token; an absent watchdog id is recorded | docs | WEAK | P2 | superseded; unique content in #2184; **closed** | Written while ml#2134 was open, so every 'on main ... until #2134' sentence is false now. Its interim --backup-id 2 guidance and job-2 helper table are carried (corrected) into #2177's section. |
| #2138 | test(backup): pin export token encoding and illegal watchdog ids | test | SOLID | P1 | carried in #2182; **closed** | Export-token encoding and illegal watchdog ids. Its three tests that EXECUTED util/ad-hoc/yamaguchi_watchdog_deploy.bash are replaced by a static check (tests/test_yamaguchi_watchdog.py forbids executing it); the static check catches three refusal-gate mutations main's suite misses. bandit, mypy. |
| #2140 | test(backup): pin export-token transport leaks and a whitespace TargetURL | test | SOLID | P2 | carried in #2182; **closed** | Export-token transport leaks and a whitespace TargetURL. bandit B105. |
| #2141 | docs(reference): how to read the landed equities CV measurement | docs | BROKEN | P3 | closed -- incorrect on main; **closed** | Its core claims (checksum not the content pin; dataset_id is; the digit is unstable; F-P8 = zip timestamps) are reversed by merged ml#2168's consensus record (CV-BLOWUP investigation v1.1.2, consensus validation §4.1, reconciler F1). Four still-true rows were moved, corrected, into #2142's section. |
| #2142 | docs(reference): re-run the E-H equities crossval instruments | docs | SOLID | P3 | carried in #2184; **closed** | Re-running the E-H equities crossval instruments. 'Digits not stable' corrected (they reproduce bit-for-bit); added the theta-axis, single-RFF-seed and fold-4 caveats. |
| #2143 | test(replay): pin the re-drive's control-request accounting | test | SOLID | P3 | carried in #2182; **closed** | Replay re-drive control-request accounting. BROKEN as submitted: its requests stand-in lacked Session, so the suite crashed at import on Python 3.12/3.13 (CI installs no requests). Fixed; mypy. |
| #2144 | test(experiments): pin aux-phase timeout, non-object 200, and degraded exit without a reason | test | SOLID | P2 | carried in #2182; **closed** | Aux-phase timeout, non-object 200, degraded exit without a reason. Same base as #2136; never ran in CI. |
| #2146 | docs(reference): recurrence env preflight before serve (W0.2) | docs | SOLID | P2 | superseded; unique content in #2184; **closed** | Same W0.2 env-preflight section as #2148, worse placement and a stale 'tip f01a438c' framing. Its unique verified content (exit table, --skip vs --skip-env-preflight, prereleases=True, --help, W0.1 status, W3.0b) is folded into #2148's section. |
| #2147 | test(experiments): pin phase-error body selection and the degraded four-way count | test | SOLID | P2 | carried in #2182; **closed** | Phase-error body selection and the degraded four-way count. bandit B105 (SECRET_* -> *_ECHO_MARKER). |
| #2148 | docs(reference): recurrence env preflight before serve | docs | SOLID | P2 | carried in #2184; **closed** | W0.2 recurrence env preflight. Twelve stale 'main does not run it' statements removed (ml#2139 is on main); --grafana-bridge only for truthy values; one unverifiable claim dropped. |
| #2149 | test(preflight): pin fail-closed pin-probe, interpreter, and skip edges | test | SOLID | P2 | carried in #2182; **closed** | Fail-closed pin-probe, interpreter and skip edges. Branch conflicts with main (carries ml#2139; ml#2164 edited the same files since). black, flake8 F541. |
| #2150 | test(launcher): pin the W0.2 version-pin probe's real evaluation | test | SOLID | P2 | carried in #2182; **closed** | The W0.2 version-pin probe's real evaluation. Its prereleases=True claim is false under packaging >= 26; comment fixed and the flag pinned by text (WEAK -> SOLID). |
| #2152 | docs(reference): recurrence error text is copied into the run record | docs | SOLID | P1 | carried in #2184; **closed** | F-S10: a whitespace-padded data API key leaks into a recurrence 502 detail (map_data_error -> data-client -> InvalidHeader). Completed the list of files that carry it: stats.json, summary.md, the service log, /v1/training/status failure.detail. |
| #2153 | test(preflight): cover silent probes and a preflight that never finishes | test | SOLID | P2 | carried in #2182; **closed** | Silent probes and a preflight that never finishes. Carried verbatim (its wiring collides with #2149/#2150). |
| #2155 | docs(reference): a pin-stable lockfile week still opens a PR | docs | SOLID | P2 | carried in #2184; **closed** | A pin-stable lockfile week still opens a PR -- true, and main's docs said otherwise in four places (all 12 scheduled runs 07-20..10-05 opened one; the generator writes timestamped backups and dated headers). '164 conda entries' is 155 deps + 9 channels; a quiet Monday can mean last week's PR was updated; an unrelated security-row rewording dropped. |
| #2156 | test(replay): pin the re-drive stack's refusal to touch a foreign listener | test | SOLID | P2 | carried in #2182; **closed** | Re-drive stack refuses to touch a foreign listener. black (its tests never ran in CI); docstring cited a suite not on main; CI comment corrected. |
| #2158 | docs(reference): WITHDRAWN is a fourth finding-triage disposition | docs | SOLID | P2 | carried in #2184; **closed** | WITHDRAWN is a fourth finding-triage disposition (verified on a synthetic ledger: FIXED > ACCEPTED > WITHDRAWN; --open-only hides all three; exit always 0). Counts refreshed to main 959748c5 (79 findings: 53 fixed, 1 accepted, 2 withdrawn, 23 open); stale 'in-flight #1652/#1675' pointers relinked. |
| #2159 | test(backup): cover the Yamaguchi pre-backup guard abort and secret contract | test | SOLID | P1 | carried in #2182; **closed** | Yamaguchi pre-backup guard abort and secret contract. Four CodeQL alerts in fixtures (file modes; a hash over a PASSPHRASE-named value) fixed in code; black, bandit. |
| #2160 | docs(reference): CodeQL blocks merge on an unclosed open() | docs | SOLID | P2 | carried in #2184; **closed** | CodeQL's 'file is not always closed' threads block merges (codeql.yml runs +security-and-quality with no path filter; the ruleset requires thread resolution; ml#2157 had 20 bot threads). Added a fourth pattern (json.dump(x, open(p, 'w'))), the ruleset mechanism, and a pointer to the prescreen. |
| #2162 | docs(reference): non-ASCII API keys are a 401, and Sentry drops frame locals | docs | SOLID | P1 | carried in #2184; **closed** | Non-ASCII API keys are a 401 and Sentry drops frame locals (security). Verified against code and the published wheels; published 0.7.0 holds the key in the genexpr local k, not 'candidate'; four 3-cell rows in 2-column tables fixed; an unverified uvicorn-parser claim dropped; juniper-data#440 added (in no release yet). WEAK as submitted, SOLID after fixes. |
| #2163 | test(worktree): pin phase 4's refusal to delete dirty work or unmerged commits | test | SOLID | P1 | carried in #2182; **closed** | Worktree cleanup phase 4 refuses to delete dirty work or unmerged commits (hermetic temp repos). Carried verbatim. Led to a defect: worktree_cleanup.bash:461's 'commits would be lost' list is always empty. |
| #2165 | docs(reference): recurrence save_model uses the launcher-recorded CLI | docs | WEAK | P3 | carried in #2184; **closed** | Harvest only: written against pre-#2164 main (re-adds a heading #2164 landed; 'the CLI has no --params', false since juniper-recurrence#190). Its dry-run, --skip, version-probe/unverified behaviour, re-run flags/env/600 s and a pitfalls table are merged into main's existing section. |
| #2166 | test(experiments): pin W1.9/W1.10 launch-record edges the happy-path suites miss | test | SOLID | P2 | carried in #2182; **closed** | W1.9/W1.10 launch-record edges. black; missing description written. |
| #2167 | docs(reference): malformed env-floor input exits 2, not a traceback | docs | SOLID | P2 | carried in #2184; **closed** | Malformed env-floor input exits 2, not a traceback (every path run live; 41 suite tests OK). The ecosystem.yaml fallback applies only without --site-packages/--env; a bad extra DOES exit 2 for juniper-ml itself (its floors all live in extras); three missing cases added; stale 'open #796/#802' fixed. |
| #2169 | test(experiments): pin the recorded save_model re-run's env and zero hyperparameters | test | SOLID | P2 | carried in #2182; **closed** | Recorded save_model re-run env and zero hyperparameters. black; missing description written. |
| #2170 | docs(reference): equities_seq dataset_id does not pin array content | docs | SOLID | P2 | carried in #2184; **closed** | equities_seq dataset_id does not pin array content. Mint labels fixed; also corrects three false rows already on main's Equities Symbol Cap (15 feature columns, fill default 'nan', actions=True). |
| #2171 | test(backup): pin the Yamaguchi TargetURL repoint's refusals | test | SOLID | P1 | carried in #2182; **closed** | TargetURL repoint refusals. CodeQL alert 1035 + bandit (fixture constant renamed). |
| #2172 | docs(reference): E-H recurrence stack serves linear ridge 0.0 | docs | SOLID | P2 | carried in #2184; **closed** | Merged into #2132's section: the E-H base YAML's service.default_ridge 0.0 overrides both the env var and the class default. Canopy module path fixed. |
| #2173 | test(recovery): pin which runs the outage helper re-runs and when it may merge | test | SOLID | P2 | carried in #2182; **closed** | Actions-outage rerun helper. Carried an older helper (0.1.0); taking its side would revert 0.2.0's --accept-degraded. Retargeted, with two tests added for that untested flag; flake8 B903, mypy. |
| #2174 | test(equities): pin Lane A3 checks-report flags | test | SOLID | P3 | carried in #2182; **closed** | Equities Lane A3 checks-report flags. False 'separate suite' claim corrected; description written. |
| #2175 | docs(reference): a busy recurrence train 409 names the holder | docs | SOLID | P2 | carried in #2184; **closed** | A busy recurrence train 409 names the holder. Added that none of it is released (PyPI 0.5.0 answers a busy train with a plain string); the curl example reads ports.json. |
| #2177 | docs(reference): Yamaguchi Duplicati server client and watchdog | docs | SOLID | P2 | carried in #2184; **closed** | Yamaguchi Duplicati server client and watchdog. Two false statements corrected: the watchdog's --base and duplicati_api.py's DUPLICATI_URL can leave loopback; export does still send the login JWT (the export route ignores it). Carries #2119's duplicati_api.py row and #2128/#2137's corrected job-2 helper list. |
| #2178 | test(archive): pin the consensus archiver credential screen | test | SOLID | P1 | carried in #2182; **closed** | Consensus archiver credential screen. Carried verbatim. |
| #2180 | test(main-verify): a finding stays screened and still fails clean | test | SOLID | P2 | carried in #2182; **closed** | main-verify screen verdicts (+ its main-verify.yml battery line). black had collapsed two stub scripts into one-liners; rewritten. |
| #2181 | docs(reference): Yamaguchi Duplicati server installer, wrapper, and guard | docs | WEAK | P3 | closed -- incorrect on main; **closed** | Documents the Yamaguchi server installer, wrapper, unit and defaults that the unmerged backup Phase B rewrites, behind the design's section 8 STOP. Three statements are false on main (a first install exits 1 silently without .blessed.sha256; an empty DUPLICATI_REQUIRE_MOUNT does not skip the mount check; a hand edit in /etc/default/duplicati is overwritten by the --update-backup-behavior re-run it recommends), and it presents install + restart as operator steps despite the owner's 'stop, never restart' Tier 1 ruling. Not carried: the server's operator docs belong with Phase B; the diff stays available on this closed PR. |

### juniper-data (24)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #447 | docs: grouped Dependabot lock diffs and FastAPI 0.142 telemetry | docs | WEAK | P3 | superseded; unique content in #475; **closed** | ~75% duplicates #448; its telemetry half describes main without #454; false claim about the Dependabot table. Unique rows (four-extras lock rows, 'Grouped minor bumps', one overview line) carried. |
| #448 | docs: Dependabot conf-only bumps still upgrade the lockfile | docs | SOLID | P2 | carried in #475; **closed** | Conf-only bumps still upgrade the lockfile. conda env export YAML, not explicit-spec (3 places); token/commit semantics made precise (5 places); restored a dropped troubleshooting cause. |
| #449 | test(image): pin the credential scan and the CPU-only publish gate | test | SOLID | P1 | superseded; unique content in #450; **closed** | Same two files as #450, neither a superset. #450 is the base (9/10 mutations vs 6/10); this PR's unique cases (symlinks, all six forbidden and five pruned dirs, secrets not echoed, negative names, manifest re-check) are carried in #450, and the pair kills 10/10. |
| #450 | test(image): pin the credential scan and the CPU-only contract | test | SOLID | P1 | **merged** `f80d5a65` | In-image credential scan and CPU-only gate, plus #449's unique cases. Re-cut on main. |
| #452 | docs(equities): point operator manuals at the recurrence-ready bundle | docs | SOLID | P2 | carried in #475; **closed** | Recurrence-ready equities_seq bundle. The 400 detail example replaced with pydantic's real rendering; on main after v0.16.0, not in the release. |
| #453 | test(equities): pin cost-basis drop edges the W1.8 suite cannot see | test | SOLID | P2 | **merged** `9cc43213` | W1.8 cost-basis drop edges. Re-cut without the carried data#451 commit; six mypy errors fixed; docstring corrected. Never ran in CI before. |
| #454 | fix(api): opt out of FastAPI native telemetry in create_app | fix | SOLID | P2 | **merged** `b8237603` | Copilot. Opts create_app out of FastAPI 0.142's native telemetry (main pins 0.142.2). Hardening, not a live leak (sentry-sdk installs no OTel provider). Re-cut without the carried #446 commit; test skips on FastAPI < 0.142. Retitled fix(api): ...; merged directly (GitHub refuses auto-merge for it as a 'stacked' PR). |
| #456 | docs: FastAPI native telemetry opt-out in create_app | docs | SOLID | P3 | carried in #475; **closed** | FastAPI telemetry opt-out (lands with #454). FastAPI pin 0.142.2 not 0.141.1 (4 places); telemetry= on 0.141 is stored in app.extra, not a TypeError. |
| #457 | docs: record the image serve-and-version gate | docs | SOLID | P2 | carried in #475; **closed** | Image serve-and-version gate. Verified as written. |
| #458 | test(notify): pin that a dispatch 204 is not consumer delivery | test | SOLID | P2 | **merged** `ff982ba1` | A dispatch 204 is not delivery. mypy (6); skip guard for hosts without GNU date -d; the failing-curl test now asserts the POST (it passed vacuously under BSD tools). Re-cut. |
| #459 | test(ci): pin the sequence-safety label hatch | test | SOLID | P2 | **merged** `abe84a56` | Sequence-safety label hatch. Merged as authored. |
| #460 | docs: record the consumer release notification | docs | SOLID | P2 | carried in #475; **closed** | Consumer release notification. 'No unit test parses them' dropped (#458 adds one). |
| #461 | test(image): pin the serve-check docker driver | test | SOLID | P2 | **merged** `87c712d0` | Image serve-check docker driver. Merged as authored. |
| #464 | docs: record the Claude Code workflow contract | docs | WEAK | P3 | carried in #475; **closed** | Claude Code workflow contract. 'contains is case-sensitive' is false (4 places). |
| #465 | docs: a non-ASCII API key is a counted 401 | docs | SOLID | P2 | carried in #475; **closed** | Non-ASCII API key is a counted 401. Wording softened; the #440 fix is not in v0.16.0 (still a 500 there). |
| #466 | test(ci): pin the open-PR budget alarm and the base-branch guard | test | SOLID | P2 | **merged** `e91ca644` | Open-PR budget alarm and base-branch guard. Merged as authored. |
| #467 | test(lockfile): pin the signed regen commit and the freshness comparison | test | SOLID | P2 | **merged** `8eaf92b5` | Signed lockfile regen commit and freshness comparison. Its macOS failure was deterministic (BSD base64 has no -w); skip guard, per-test scratch dirs, exact-pin regex. Re-cut. |
| #468 | docs: an arc_agi artifact loads without pickle | docs | SOLID | P2 | carried in #475; **closed** | arc_agi loads without pickle. One phrase corrected. |
| #469 | test(ci): pin the main-verify verdict and tracker shells | test | SOLID | P2 | **merged** `1011e151` | main-verify verdict and tracker shells. 19 mypy errors (class-level annotations) and a hard-coded /usr/bin/python3 fixed. Re-cut. |
| #470 | docs: equities_seq is regression at generator 6.0.0 | docs | SOLID | P2 | carried in #475; **closed** | equities_seq is regression at 6.0.0. Added that v0.16.0 still serves 5.0.0 as classification. |
| #471 | test(ci): pin which job results fail the Quality Gate | test | SOLID | P2 | **merged** `48a23f57` | Which job results fail the Quality Gate. Merged as authored. |
| #472 | docs: HF and Kaggle loads emit the decision-11 contract | docs | SOLID | P3 | carried in #475; **closed** | HF/Kaggle loads emit the decision-11 contract. #411 issue vs #422 fix made precise. |
| #473 | test(ci): pin the AGENTS.md Last Updated date check | test | SOLID | P3 | **merged** `78a85e67` | AGENTS.md Last Updated date check. Merged as authored. |
| #474 | docs: record the dependency-docs capture contract | docs | SOLID | P3 | carried in #475; **closed** | Dependency-docs capture contract. Stale check_doc_links.py fixed; rows merged with #448's. |

### juniper-canopy (23)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #698 | docs(replay): exclusive range end, window length, and render echoes | docs | SOLID | P2 | carried in #729; **closed** | Replay exclusive range end, window length, render echoes. 16 stale 'not on main yet' lines (#697 merged 12 min after it opened); 2 false claims; also repairs two errors in main's REPLAY_V2_FAQ. |
| #699 | test(replay): pin echo guards the measured-session suite cannot see | test | SOLID | P2 | carried in #729; **closed** | Replay echo-shape guards. flake8 B903 (__slots__). Branch carries merged #697. |
| #700 | docs(replay): exclusive range end, window length, and render echoes | docs | SOLID | P3 | superseded; unique content in #729; **closed** | Same title and subject as #698, less complete. Unique pieces (USER_MANUAL replay items, cheatsheet row, TESTING_REFERENCE table, QUICK_START check) carried; its AGENTS.md Hazards line is not (fails the admission test; would use 471 of 618 chars left). |
| #701 | test(replay): pin window shapes the measured session never builds | test | SOLID | P2 | carried in #729; **closed** | Replay window shapes the measured session never builds. Carried verbatim; branch carries merged #697. |
| #703 | docs(recurrence): 4xx detail path and in-sample regression card | docs | WEAK | P2 | carried in #729; **closed** | Recurrence 4xx detail and in-sample card. ~20 sentences said #702 was unmerged; hover limit 480 not 400; the 401/403 message names the env vars; detail also appended on 429. |
| #704 | test(recurrence): pin falsy 422 details and the exact status-bar cut bounds | test | SOLID | P2 | carried in #729; **closed** | Falsy 422 details and status-bar cut bounds. Two tests pinned the pre-#722 401/403 text; retargeted to main's wording (tooltip bound 480, not 400). Taking its branch side would revert #722. |
| #706 | docs(ci): document the Claude Code workflow contract | docs | WEAK | P3 | carried in #729; **closed** | Claude Code workflow contract. 'Case-sensitive @claude' is false (5 places); five smaller fixes; an over-length line. |
| #707 | test(selection): refuse juniper-data dataset spellings for the LMU | test | SOLID | P2 | carried in #729; **closed** | Selection refuses juniper-data dataset spellings for the LMU. Carried verbatim. |
| #713 | docs: document the start-fresh refusal and parameter carry | docs | SOLID | P2 | superseded; unique content in #729; **closed** | #717 is a lint-clean superset. Unique strings (alert text, banner, toggle label, Off/On table) carried; cascor's refusal credited to juniper-cascor#687, not canopy#681. |
| #714 | docs(ci): document the image serve-and-version gate | docs | SOLID | P2 | carried in #729; **closed** | Image serve-and-version gate. ~40 claims, 0 false; one wording fix. |
| #715 | test(publish): pin the image-serve driver's fail-closed paths | test | SOLID | P2 | carried in #729; **closed** | Image-serve driver fail-closed paths. BROKEN as submitted: it overwrote time.monotonic/time.sleep globally and never restored them, failing 5 unrelated tests on every CI leg. Fixed with monkeypatch. |
| #716 | docs(ci): Dependabot floors and lockfile --upgrade are different inputs | docs | WEAK | P2 | carried in #729; **closed** | Dependabot floors vs lockfile --upgrade. ci.yml no longer installs conf/requirements_ci.txt (since canopy#650); [dependabot skip] semantics were inverted; stale example. |
| #717 | docs: runbook for a wider-dataset Start refusal | docs | SOLID | P2 | carried in #729; **closed** | Wider-dataset Start refusal runbook. The restart body is {start_fresh: <toggle>, reset: true}; cascor-client 0.8.0; juniper-cascor#687 (3 places). |
| #718 | test(ci): pin the image credential scan and the open-PR budget alarm | test | SOLID | P2 | carried in #729; **closed** | Image credential scan and open-PR budget alarm. Its macOS red was main's own flake (C2). |
| #719 | test(replay): pin control-result guards the measured session never builds | test | SOLID | P2 | carried in #729; **closed** | Replay control-result guards. Carried verbatim. |
| #720 | test(selection): pin falsy values on the shared stage payload | test | SOLID | P2 | carried in #729; **closed** | Falsy values on the shared stage payload. Its macOS red was main's own flake (C2). |
| #721 | fix(packaging): ship outbound_errors in the wheel and pin the import smoke | fix | SOLID | P1 | **merged** `c092d041` | Real defect: the wheel omitted outbound_errors, which main imports, so the next release would have stopped at publish.yml's import smoke. Re-cut on main without a stale lockfile-regen commit GitHub had not synced into the PR; CHANGELOG entry corrected; black. |
| #723 | docs(recurrence): key variables, restored models, and the service version | docs | SOLID | P2 | carried in #729; **closed** | Recurrence key variables, restored models, service version. 9 stale/false claims fixed (the 120-char cut ends inside the second variable name). |
| #724 | test(recurrence): a failed health read is not a version, and a zero wait is still a wait | test | SOLID | P2 | carried in #729; **closed** | A failed health read is not a version; a zero wait is still a wait. Branch carries merged #722. |
| #725 | docs: document the sidebar unknown-liveness sentence (X11) | docs | SOLID | P2 | carried in #729; **closed** | Sidebar unknown-liveness sentence (X11). 'NOT ACTIVE' dates from canopy#592; Start AND Apply Dataset are disabled. |
| #726 | docs: sidebar model line says Active only after the backend answers | docs | WEAK | P3 | superseded; unique content in #729; **closed** | Central premise false (the header dot is a latency indicator, not 'Active = idle'). Corrected unique pieces carried into #725's section. |
| #727 | test(ci): pin the sequence-safety hatch and the post-merge verdict shells | test | SOLID | P2 | carried in #729; **closed** | Sequence-safety hatch and post-merge verdict shells. Hermetic (tripwire gh/curl never called). |
| #728 | test(selection): refuse an empty-string dataset commit and keep restage zeros | test | SOLID | P2 | carried in #729; **closed** | Empty-string dataset commit and restage zeros. A 3-part implicit concatenation made one literal (the cause of its failed pre-commit). |

### juniper-cascor (9)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #699 | test(image): pin the serve-check driver and the optional version contract | test | SOLID | P2 | **merged** `f3c57cbc` | Image serve-check driver and optional version contract. flake8 B903 (__slots__) fixed; re-cut. |
| #700 | docs: record the Claude Code workflow contract | docs | WEAK | P3 | carried in #709; **closed** | Claude Code workflow contract. Central claims false at the pinned action (case-insensitive contains(); id-token used; checkout credential stripped; pushes only to this repo; write check before phrase check). |
| #702 | docs: record the start-fresh width refusal and param carry | docs | SOLID | P2 | carried in #709; **closed** | Start-fresh width refusal and parameter carry. Main's 409 recovery steps restored. |
| #703 | test(image): pin the in-image credential scan | test | SOLID | P1 | **merged** `a95ec0ef` | In-image credential scan. Merged as authored. |
| #704 | docs: record how the lock regen outruns conf freezes | docs | SOLID | P2 | carried in #709; **closed** | Lock regen outruns conf freezes. Its Sequence Safety failure is a deliberate rewrite (5 screen false positives + 1 rename); waived with Allow-Docs-Rewrite. Lost sentence restored; missing mv steps added. |
| #705 | test(ci): pin the open-PR budget alarm's report-only contract | test | SOLID | P3 | **merged** `445825f7` | Open-PR budget alarm report-only contract. black + bandit annotations; re-cut. |
| #706 | test: pin the key walk, resume-ready stop, and auth-throttle cap | test | SOLID | P1 | carried in #709; **closed** | In part: the throttle hard-cap and resume-ready stop tests (each catches a unique mutation); its API-key test is superseded by #708's. |
| #707 | docs: record the shared BLAS thread-width default | docs | SOLID | P2 | carried in #709; **closed** | Shared BLAS thread-width default. 'Only module' -> 'only production module'; test scope stated precisely; max_epochs/output_epochs hazard first. |
| #708 | test: pin the API-key walk, resume-ready stop, and nested snapshot exclusions | test | SOLID | P1 | carried in #709; **closed** | API-key walk, resume-ready stop, nested snapshot exclusions. Carried in full. |

### juniper-data-client (7)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #220 | docs(ci): record Sequence Safety as a required check | docs | WEAK | P2 | carried in #230; **closed** | Sequence Safety is a REQUIRED check (main said advisory). Catch-up base, renamed-step, cross-workflow needs: and squash-trailer claims corrected. |
| #221 | test(ci): pin dispatch, signed lockfile commit, and PR budget alarm | test | SOLID | P2 | **merged** `635e9495` | Dispatch, signed lockfile commit, PR budget alarm. Its macOS failure was deterministic (BSD base64); skip guard + bash 5.3 wording. Re-cut. |
| #224 | test(contract): pin per-split W1.4 bounds the shared-lookback suite misses | test | SOLID | P2 | **merged** `9c8e0331` | Per-split W1.4 bounds (catches 3 mutations main's contract tests miss). Merged as authored. |
| #225 | docs(ci): record Memory Budget and the open-PR budget alarm | docs | SOLID | P2 | carried in #230; **closed** | Memory Budget and the open-PR budget alarm. Three wrong claims about --limit, jq failure and the cheatsheet cause. |
| #226 | test(ci): pin screen-verdict thresholds and the label hatch | test | SOLID | P2 | **merged** `5d0b9e05` | Screen-verdict thresholds and label hatch. Bandit B404/B106 annotations (the cause of its failed pre-commit). Re-cut. |
| #228 | docs(contract): spell out the W1.4 dtype scope and rejection messages | docs | SOLID | P2 | carried in #230; **closed** | W1.4 dtype scope and rejection messages (+ a stale contract.py docstring). The t/dt check is np.allclose with rtol=1e-5 as well as dt_atol. |
| #229 | test(ci): pin notify dedup and the base-branch guard | test | SOLID | P2 | **merged** `d611ae8d` | Notify dedup and base-branch guard. Merged as authored. |

### juniper-deploy (2)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #240 | docs: describe the @claude workflow contract | docs | WEAK | P3 | **merged** `a84af1fb` | @claude workflow contract. Same false case-sensitivity claim as cascor#700 plus write-check order, fork pushes, id-token, UTC; duplicated separator. Re-cut corrected. |
| #241 | test: pin image-currency policy and the open-PR budget alarm | test | SOLID | P2 | **merged** `e554b054` | Image-currency policy and open-PR budget alarm. Unclosed synthetic HTTPError broke an unrelated test on Python 3.14 (filterwarnings=error); closed. Re-cut. |

### juniper-cascor-client (2)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #176 | docs(ci): record the @claude workflow contract | docs | WEAK | P3 | **merged** `b1c9546f` | @claude workflow contract. 'contains is case-sensitive' headline false; Dependabot grouping scope; repository-secret note. Re-cut corrected. |
| #177 | test(ci): pin the open-PR budget alarm and the sequence-safety label hatch | test | SOLID | P2 | **merged** `1a715500` | Open-PR budget alarm and sequence-safety label hatch. Merged as authored. |

### juniper-cascor-worker (2)

| PR | title | kind | quality | prio | outcome | evaluation |
|---|---|---|---|---|---|---|
| #205 | docs: record the Claude Code workflow contract | docs | SOLID | P3 | **merged** `c6788576` | Claude Code workflow contract (replaces a dead check_doc_links.py instruction). Case, assigned-issue, grouping and secret corrections. Re-cut. |
| #206 | test: pin the image credential scan and the open-PR budget alarm | test | SOLID | P2 | **merged** `e941f079` | Image credential scan and open-PR budget alarm. Bandit B106 + bash 5.3 wording. Re-cut. |

## §6 Process traps hit during the disposition

- **A PR's head can stop tracking its branch.** canopy#721's PR object reported head `973c8680` while `cursor/missing-test-coverage-7a79` had moved to a lockfile auto-regen commit `033d7311` (pushed 2026-10-05 14:29Z, during that day's GitHub incident) that GitHub never synced into the PR. Read the branch tip from `git/ref`, not the PR object — the re-cut tool's `--expect-tip` guard does.
- **A "stacked" PR refuses every ordinary merge path, even after its base became `main`.** data#454 was opened by Copilot from a review comment on #446, and GitHub kept it registered in a stack after #446 merged: `enablePullRequestAutoMerge` answered "Auto-merge is not supported for stacked pull requests" (while `viewerCanEnableAutoMerge` read `true`), `PUT …/pulls/454/update-branch` answered 403 "Updating a stacked PR's branch via this endpoint is not supported", and `PUT …/pulls/454/merge` answered 403 "Merging stacked PRs via this endpoint is not supported". What works: keep the branch current by re-cutting it (a ref force-move is not update-branch), wait for green, then **`PUT /repos/{owner}/{repo}/pulls/{n}/merge-async`** (`merge_method=squash`, `merge_action=direct_merge`, `sha=<head>`, `bypass_rules` left false) and poll `GET …/merge-async/{uuid}`. That endpoint merges **all open downstack PRs** with it — check the stack has none (here #446 was already merged).
- **HTTP 499 on a large `createCommitOnBranch`** (data#475's 11-file commit) created the branch at `main` and landed no commit. Check the ref, then append with `util/ad-hoc/2026-09-08_push_signed_commit.py` and open the PR with `gh pr create` (the same trap is recorded in the agent memory file `reference_signed_commit_api_499_on_large_payloads.md`).
- **A repo-wide lint suite judges new files.** ml#2182 first failed CI on `tests/test_env_repr_safety.py`, which scans every test file for raw `os.environ` mappings — the harvest had run its 25 new suites and the wiring gates, not the full list. After the fix, all 198 suites were run locally, one process each, as CI does.
- **Green checks are not mergeable.** ml#2182 then sat `BLOCKED` with every required context passing: CodeQL had posted five review threads on the harvested suites (`unittest` imported both ways in four files; `assertTrue(a <= b)` on two sets), and the conversation-resolution rule blocks on any unresolved thread. Fixing the code (`import unittest.mock as mock`, `assertLessEqual`) cleared all five threads without a manual resolve. Screen new Python with `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` before opening the PR — this record's own tooling was screened that way (five predicted alerts fixed first) — **but the prescreen models only a subset of the rules.** CodeQL still raised three on this record's own PR (ml#2185), none of which it predicts: two `py/clear-text-logging-sensitive-data` because a constant *named* `SECRETS` held a file path (`util/check_image_no_secrets.py`) that was later printed — the sensitivity heuristic reads the name, not the value — and one `py/multiple-definition` (a dead `verdict = "?"` initialiser). Renaming the constant and dropping the dead line cleared them. A clean prescreen means "none of the modelled rules", not "no alerts".
- **A skip guard can measure the wrong thing.** data-client#221's re-cut skipped its byte-level assertion when `base64 -w0` failed on empty stdin; on the macOS runner that probe passed while the step's real form, `base64 -w0 <file>`, still produced an empty payload, so the required macOS leg failed. The guard now runs the step's exact form on a one-byte file and checks the output is `eA==` (never skipping on Linux) — the probe juniper-data's equivalent suite already used, which had passed macOS. Probe the question the code under test asks, by output, not by exit code.
- **Time-box evaluators.** One evaluator spent 5.5 hours on twelve docs PRs and verified five; the remaining seven were re-split across two evaluators with a ~40-minute box and finished in ~20 minutes each.
- **A named carrier slot that resolves to nothing must block a close.** The first renderer draft treated an unopened consolidation as "no carrier", which would have closed canopy and juniper-ml docs PRs ungated; caught on the dry run, before any close.

## §7 Tooling added

All under `util/ad-hoc/` (script-placement rule; retained as provenance of record):

- `2026-10-08_fleet_flood3_census.py` — per-PR files, commits, live required-context tally, behind-by.
- `2026-10-08_fleet_flood3_reset_pr_branch.py` — re-cut a PR's branch as one GitHub-signed commit on current `main`, guarded on the branch tip.
- `2026-10-08_fleet_flood3_pr_actions.py` — `state` / `ready` / `arm` / gated `close` through the API (`gh pr edit` is dead on gh 2.46).
- `2026-10-08_fleet_flood3_wire_ml_tests.py` — registers juniper-ml suites in all three hand-maintained lists (round 2's wirer still targeted `AGENTS.md`).
- `2026-10-08_fleet_flood3_bump_doc_stamps.py` — bumps a consolidated doc's stamps once, from the tree it is applied to.
- `2026-10-08_fleet_flood3_disposition.json` + `2026-10-08_fleet_flood3_disposition_render.py` — the verdicts, and the renderer for §5 and the closing comments.
- `2026-10-08_extract_agent_final_report.py` — preserves an evaluator's final report from its transcript (the harness refuses report files from subagents).
- `2026-10-08_flood3_worktree_vs_ref.py` — classifies every changed or untracked path in a worktree against a ref as NEW / SAME / DIFF before a PR is assembled from it, so a stale copy of a file `main` has since moved is never uploaded (a whole-file upload of a stale copy reverts `main`).
- `2026-10-08_fleet_flood3_postmerge_verify.py` — for every merged PR, compares each changed file's blob at the PR's final head with `main` (SAME / MOVED by a later commit / DIFFERS); all 25 direct merges and all six carriers read SAME, except files a later carrier edited again, as expected: canopy#721's `CHANGELOG.md` (MOVED by #729) and ml#2182's `CHANGELOG.md` and `docs/REFERENCE.md` (MOVED by #2184, `1da05a92`).
- The evaluators' own instruments: mutation checkers (`2026-10-08_flood3_ml_tests_a_mutation_probe.py`, `…_ml_tests_b_mutation_check.py`, `…_data_tests_mutation_check.py`, `2026-10-08_canopy_flood3_mutation_check.py`, `…_cascor_deploy_mutation_probe.py`, `…_clients_mutate.py`), repros (`2026-10-08_canopy_recurrence_late_warning_repro.py` + `flood3_canopy_slowlog_plugin.py`, `2026-10-08_phase4_refusal_log_repro.py`, `2026-10-08_flood3_bsd_base64_repro.py`, `2026-10-08_flood3_dt_atol_probe.py`, `2026-10-08_data_docs_fastapi_telemetry_probe.py`), the uncommitted-tree Sequence Safety screen (`2026-10-08_flood3_worktree_screens.py`), the juniper-ml docs slice-A evaluator's claim checker (`2026-10-08_flood3_ml_docs_a_eval.py`), and the docs carry/anchor/stamp helpers (`2026-10-08_data_docs_*.py`, `2026-10-08_flood3_canopy_docs_*.py`, `2026-10-08_flood3_strip_stamp_hunks.py`, `2026-10-08_flood3_verify_carried_lines.py`, `2026-10-08_flood3_restore_doc_stamps.py`, `2026-10-08_flood3_g5_drop_stamp_hunks.py`, `2026-10-08_flood3_clients_*.py`).

## §8 Open items

**Follow-up, 2026-10-08 evening (owner instruction).** The owner asked for:
- the `ANTHROPIC_API_KEY` secret in the three repos;
- the `t` / `dt` check accepted as written;
- five of the §4 defects fixed;
- juniper-service-core, juniper-observability and juniper-data released.

§4 records each outcome against its row. Still open after that pass:

- **Owner decisions:**
  - the `ANTHROPIC_API_KEY` secret for juniper-data, juniper-cascor, juniper-canopy and juniper-deploy, which lack it too (§4);
  - a juniper-ci-tools release, so that the fence-aware docs screen (ml#2187) reaches the eight repos that pin `>=0.9.0,<0.10.0`;
  - the `pypi` environment approvals for the three releases. Each one parks there by design, and the gate is the owner's alone.
- **Sequenced after a release:** another session's draft ml#2190 raises juniper-ml's `[servers]` floor to `juniper-data>=0.17.0`. It should merge only once 0.17.0 is on PyPI; a floor at an unpublished version resolves nothing.
- **Not done, deliberately:** a `tests/test_service_fork_drift.py` guard for the `FailedAuthThrottle` fix. The gate requires a defect-register `APD-` id, and filing one is the register's five-touch protocol. Each of the three copies is pinned by its own repo's regression test.
- **The remaining open rows in §4**, including the six that the follow-up's Sequence Safety and throttle sweeps found.
- The fleet keeps running by owner decision. The next flood will meet the same structure: every docs PR rewrites shared version stamps, so the docs class conflicts by construction and consolidation is the default disposition.

## §9 Files changed by this arc

**Merged as themselves (re-cut where corrected):** see §5 (`route = merged`).
**Carrier PRs opened and merged:** juniper-ml #2182 and #2184; juniper-data #475; juniper-canopy #729; juniper-cascor #709; juniper-data-client #230.
**Created (this PR, ml#2185):** this file, `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md`, and the `util/ad-hoc/` tooling in §7.
**Modified (this PR, ml#2185):** `CHANGELOG.md` (one `[Unreleased]` / `Added` entry).

**Follow-up, 2026-10-08 (owner instruction):**

- **Fix PRs, all merged:**
  - ml#2187: `juniper-service-core` throttle, `util/worktree_cleanup.bash`, `juniper-ci-tools` docs screen, and the Sequence Safety wording in `ci.yml`, `docs/REFERENCE.md`, `docs/QUICK_START.md` and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`;
  - juniper-cascor#710 (throttle fork, plus Sequence Safety and CodeQL docs);
  - juniper-data#476 (throttle fork, plus Sequence Safety docs);
  - juniper-canopy#730 (the `[dependabot skip]` comment, plus Sequence Safety);
  - Sequence Safety docs: juniper-data-client#231, juniper-cascor-client#178, juniper-cascor-worker#207, juniper-deploy#244 and juniper-recurrence#194.
- **Release bumps:** ml#2186 (observability 0.4.1), ml#2189 (service-core 0.7.1) and juniper-data#477 (0.17.0).
- **Release-notes archives:** ml#2188, ml#2193 and ml#2191, which add `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md`, `RELEASE_NOTES_juniper-service-core_v0.7.1.md` and `RELEASE_NOTES_juniper-data_v0.17.0.md`.
- **This record's update PR:** this file, `CHANGELOG.md`, and `util/ad-hoc/2026-10-08_run_ci_regression_suites.py` (it runs CI's regression list locally, one process per suite; 197/198 passed before ml#2187, and the one failure is host-only because `/tmp` is tmpfs here).
