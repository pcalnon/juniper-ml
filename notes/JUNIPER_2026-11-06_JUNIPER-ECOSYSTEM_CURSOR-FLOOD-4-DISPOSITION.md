# Cursor-Fleet Flood #4 — Disposition Record

**Project**: Juniper (ecosystem-wide)
**Author**: Paul Calnon
**Status**: In progress — round 1 is complete (six carriers merged; all 68 census drafts assigned to them are closed, 67 of them carried); round 2, round 3, the §4 defect fixes and four more defect fixes are open (§8)
**Date**: 2026-11-06
**Updated**: 2026-11-09
**Applies to**: juniper-ml, juniper-data, juniper-canopy

---

## §0 What this document is

The record of how the fourth Cursor-fleet draft-PR flood (census drafts opened 2026-11-04 09:16Z .. 2026-11-06 09:43Z) is disposed of. The owner's rulings of 2026-11-06: "This session, new record", and "Consolidate, incl. post-grant": each affected repository gets one signed tests PR and one signed docs PR (a *carrier*), built on current `main` from the drafts' verified content and fixed where triage found faults; a carried draft is closed, with a comment naming its carrier, only after that carrier merges. The owner's rulings of 2026-11-07: the drafts opened after the census are a **second wave**, triaged and carried after the census carriers merge; #2404 and #2406 are a **round 3**, considered individually. Earlier rounds: `notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` (flood 1), `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` (flood 2) and `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` (flood 3), whose §2 method and §6 traps this round applies. The owner's rulings of 2026-11-08 (§8) fold the 13 drafts that no ruling covered into round 2, have three of §4's four open rows fixed now, settle the fourth (the launcher's effort default), and settle juniper-ml#2271's setting. Later rulings (§8, 2026-11-08 and 2026-11-09) make the agent guard's brace cap fail closed, put both Retry-After fixes in round 2, port the gitleaks fix to the seven other repositories, fix four more defects that building the fixes found, confirm the paused-fit fix, and carry juniper-ml#2507 with `propose.py` extended.

## §1 Scope

The census (2026-11-06 09:45Z) held 74 open PRs in three repositories: 72 Cursor drafts (`app/cursor`) and two of the owner's (juniper-ml#2360 and #2271). The six other Juniper repositories had none, and on 2026-11-08 still had no open PR at all.

| repo | tests carrier | docs carrier | closed on ruling | round 3 | owner's PRs | total |
|---|---|---|---|---|---|---|
| juniper-ml | 28 | 23 | 2 (#2420, #2435) | 2 (#2404, #2406) | 2 (#2360, #2271) | 57 |
| juniper-data | 5 | 4 | 0 | 0 | 0 | 9 |
| juniper-canopy | 4 | 4 | 0 | 0 | 0 | 8 |
| **total** | **37** | **31** | **2** | **2** | **2** | **74** |

- **Closed on the owner's 2026-11-06 rulings, before consolidation:** juniper-ml#2271 (its commit `85c66d62` is unsigned, so under `required_signatures` it can never merge), #2420 (duplicates #2435 and would revert #2415's fail-closed fix) and #2435 (moot: the P12 cleanup it guarded is finished). #2271's branch was deleted on 2026-11-08, after its one setting moved to where Claude Code reads it (§8).
- **Not this arc's:** juniper-ml#2360 (armed and `DIRTY` on purpose; it merges last) and the owner's #2497 / #2498, opened after the census, which have since merged.
- **Second wave (owner, 2026-11-07):** the 35 Cursor drafts juniper-ml received after the census, up to #2509 (#2469–2472, #2475–2481, #2483–2496, #2499–2505, #2507–2509). They include follow-ups to #2468 (the launchers) and #2474 (`predict_merge.py`), and six code fixes that fit neither a tests nor a docs carrier: #2480, #2493, #2502, #2504, #2505 and #2508. #2484 is stacked on #2480's own branch (`cursor/critical-bug-resolution-68c6`). On 2026-11-08 the owner folded in the 13 drafts that no ruling covered (§8): juniper-ml #2512–#2515, juniper-data #520–#524 and juniper-canopy #798–#801. Round 2 therefore holds 48 drafts, two more of them code fixes (#2513 and #2514). #2514 was then carried outside this arc, by juniper-ml#2524 (§8, ruling 9).
- **Round 3 (owner, 2026-11-07):** juniper-ml#2404 and #2406, launcher docs whose claims `main` contradicts since #2438 and #2468; each is to be considered individually.

## §2 Method

**Triage** (2026-11-06, the session that kept the 11-06 handoff, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md`): `util/fleet_triage/predict_merge.py` predicted each draft's merge against `main`, a fleet-supervisor pass adjudicated duplicates, pairs and same-file clusters, and every test draft's suite was run on its predicted merge tree. The docs drafts all edit the same four files (`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `docs/QUICK_START.md`, `docs/REFERENCE.md`) and bump the same stamps, so every simulated pair conflicted (231 of 231).

**Consolidation** (2026-11-07): one builder per carrier set, each on a fresh worktree of current `main`, under one shared brief:

- a draft's content is taken from its head blobs, as its own `merge-base..head` hunks re-applied to `main`, never as a whole-file copy of a shared file (`ci.yml`, `docs/REFERENCE.md`, `CHANGELOG.md`, stamps);
- every docs claim is re-derived from the source of truth before it is carried; the drafts' stamp hunks are dropped and each touched document's stamp is bumped once;
- every carried test file is shown non-vacuous by a one-line mutation of the code it pins;
- the repository's pinned pre-commit hooks and the CodeQL prescreen run on every changed file, and juniper-ml's carrier runs CI's whole regression list, one process per suite.

Each carrier is then validated by independent agents with different lenses before its signed PR is opened with `util/open_signed_pr.py`, and merged with `util/safe_merge.py` after its required checks pass on its final head.

**Validation counts** (round 1 = the first independent pass; round 2 = the pass on the corrections; rounds 3–6 = the further passes one carrier needed; BLOCKER / MAJOR / MINOR):

| carrier | round 1 | round 2 | rounds 3–6 |
|---|---|---|---|
| juniper-data tests | 1 / 0 / 3 | 1 / 0 / 5 (shared with docs) | — |
| juniper-data docs | 2 / 1 / 5 | (shared with tests) | — |
| juniper-canopy tests | 0 / 1 / 3 | 0 / 0 / 6 (shared with docs) | — |
| juniper-canopy docs | 3 / 1 / 5 | (shared with tests) | — |
| juniper-ml tests (three lenses) | 3 / 0 / 10 | 1 / 0 / 4 | — |
| juniper-ml docs (three lenses) | 3 / 7 / 39 | 1 / 0 / 15 | 0 / 2 / 5; 0 / 2 / 4; 0 / 2 / 5; 0 / 1 / 1 |

The juniper-ml docs carrier took four more rounds after it was rebased onto #2517's head:

- Round 3 found that the rebase lost nothing from #2510, #2516, #2517 or #2518.
- Rounds 3 to 6 each found at least one MAJOR in the same subject: which published releases first carry the API-key byte compare, the no-500 behaviour and Sentry without frame locals. From round 5 the text states only each package's first fixed release, read from the published wheels.
- Round 6 still found a MAJOR: juniper-canopy's own `APIKeyAuth` copy was missing from every list of the copies. The builder added it before #2519 opened. The only check of that correction was the orchestrator's census of the copies (`…_api_key_copies_census.py`, 03:15Z); no seventh round ran.

Every finding was re-derived by the builder before it was acted on. Four of the juniper-ml docs carrier's were left to the orchestrator by design (two dependency findings and two merge-time ones), and one was applied elsewhere: R8 targeted a tests-carrier docstring, so it moved to that carrier. The builders also replaced one validator's wording with a better-grounded one: W9, where a window of 0 can still flag (`security.py:239-247`).

## §3 What the evaluation found

- **The test drafts were behavioural, as in rounds 2 and 3.** Every carried test file kills at least one one-line mutant of the code it pins, and the validators' own mutants agree:
  - juniper-data: 8 of 8 (builder) and 10 of 10 (validator).
  - juniper-canopy: 4 of 4 and 5 of 5.
  - juniper-ml: the builder's 35 (33 killed, 1 inapplicable and replaced, 1 surviving because the effort default is deliberately unpinned), 41 for the sub-package suites (39 killed, 1 survivor fixed by a new `cap + 1` test, 1 equivalent), and 38 for `tests/` (all killed).
- **About one test draft in five (8 of 37) was wrong as submitted, beyond formatting:**
  - *platform:* juniper-data#514 ran `/usr/bin/bash`, which macOS lacks. juniper-canopy#792 ran coreutils `base64 -w0`, which macOS's BSD `base64` rejects; its macOS leg failed in CI.
  - *the runner's shell:* juniper-data#513 and #514 rehearsed a step under `bash -eo pipefail` and called that GitHub's default. A step that names no `shell:` runs as `bash -e {0}`, and `bash -eo pipefail` is what `shell: bash` gives.
  - *host state:* juniper-canopy#794's fixtures committed under the host's global git config (signing, `color.ui`, `core.hooksPath`). The fixed fixture is hermetic.
  - *the owner's directive:* juniper-canopy#792's poisoned-`jq` cases left the workflow's write to `/tmp/lockfile-commit.json` in place. A builder's mutant run then left that file on the host (removed the same day).
  - *a stale contract:* juniper-ml#2403's expectations predate #2438 and #2468, and its rewrite first pinned `--effort auto`, a value the real Claude Code CLI ignores with a warning (§4). juniper-ml#2407's pins predate #2468's defaults, and #2455 failed mypy.
  - *a false premise:* juniper-ml#2410's negative control assumed an undeclared `py.typed` misses the wheel. setuptools 81.0.0 and 84.2.1 both ship it.
- **The docs drafts were well-grounded and partly stale, and some of them were false.** juniper-canopy's set carried three claims about CI or API behaviour that were false on `main`:
  - removing `[extend]` from `.gitleaks.toml` "lets Gitleaks pass": the pinned 8.24.3 refuses that config and exits 1;
  - Dependabot pull requests "have no `CODECOV_TOKEN`": false since 2026-11-04 11:18Z;
  - `POST /api/stage_dataset` "does not echo the staged config": it does.

  juniper-data's had two: a pin table's "other rows unchanged" and a self-test that "fails before collection". juniper-ml#2457 was stale (recurrence 0.8.1 has been on PyPI since 2026-11-06 09:35Z).
- **The carriers' own rewrites introduced errors, and round 2 caught them.**
  - In the juniper-ml docs carrier, two of round 1's three BLOCKERs were errors in the builder's rewrites of draft text, not in the drafts: a 4001 key rejection logs a WARNING, and a re-sent task result is accepted in the next round. Round 2's only BLOCKER was a sentence written by a round-1 correction: a resumed client misses broadcasts sent during the replay.
  - Round 2 found a BLOCKER in three of the six carriers, all of them text:
    - a test's assert message that contradicted the corrected rationale beside it (juniper-data);
    - the PR and commit bodies' mutant tally, which the corrections had made false (juniper-ml tests);
    - the docs sentence a round-1 correction wrote (juniper-ml docs).
  - The SOP's rule that a correction pass is not done until it has been validated held again.

## §4 Defects found on `main`

Found while evaluating the drafts. Each was re-derived from source by a builder or a second validator before it was recorded.

| repo | defect | status |
|---|---|---|
| juniper-ml | `scripts/wake_the_claude.bash:259` (from #2396) sets `EFFORT_DEFAULT` to `auto`. The launcher sends that default for `--effort 0` (its boolean true) and also accepts `auto` as an explicit value. Claude Code's `--help` lists only `low`, `medium`, `high`, `xhigh` and `max`, and no `auto` (its parser also takes the aliases `med` and `ultracode`). 2.1.316–2.1.319 answer `auto` with `Unknown --effort value 'auto' — ignoring it and using the default effort`, exactly as for a made-up value | **ruled** (owner, 2026-11-08): the default becomes `max` (line 258 restored), and an explicit `auto` sends no `--effort` flag at all. The fix rides in round 2's launcher code carrier (§8). The tests carrier pinned neither |
| juniper-ml | `tests/test_subpackage_py_typed.py`'s text said an undeclared `py.typed` misses the wheel. setuptools 81.0.0 and 84.2.1 both ship it (re-derived with probe builds) | **fixed** — juniper-ml#2517 |
| juniper-ml | `docs/REFERENCE.md`'s CR-024 bullet contradicted the code it describes, a body limit was written "100 MB" (it is 100 MiB), and the overview row said juniper-service-core 0.7.1 was unreleased | **fixed** — juniper-ml#2519. Rounds 3–6 then cut every published-release statement down to each package's first fixed release. On 2026-11-08, `git grep` found no "unreleased" or "not yet released" claim about service-core 0.7.x left in `main`'s docs |
| juniper-canopy | `.gitleaks.toml:26`, `ci.yml:293-294` and `src/tests/regression/test_gitleaks_config.py:92` carry, as comments, the false claims of §3: removing `[extend]` would pass, and Dependabot PRs lack `CODECOV_TOKEN`. No logic depended on either | **fixed** (comment-only; both config files parse to identical data) — juniper-canopy#802 |
| juniper-service-core | The "paused-fit wedge": after a resume nothing is running, yet every start is refused (a 409; a start with no data is a 400) until a stop or reset: the refusal is `lifecycle/manager.py:165-166`, the 409 `routes/training.py:61`, and `mark_completed` refuses any state but `STARTED` (`lifecycle/state_machine.py:239-248`). Cursor draft juniper-ml#2460 (2026-11-04), titled "… a paused fit stays paused", had filed the behaviour in `docs/REFERENCE.md`'s shared service-core contracts, its list of load-bearing invariants. No person ruled that, and `main` never carried it as one: #2519 carried #2460 with the clause rewritten as a known defect. Neither the lifecycle's design, juniper-ml#468, nor its build PR, juniper-ml#473 (both 2026-06-19), addresses a fit that returns while paused. No consumer imports service-core's lifecycle manager; juniper-cascor runs its own (§8, ruling 11) | **ruled: fix now** (owner, 2026-11-08; §8), and confirmed once the owner had #2460's provenance (ruling 12). A fix was built. Its two validators returned SHIP-WITH-FIXES, and one found a regression in it: a stale fit returning while a new run is paused resumed or completed the new run. On 2026-11-09 the corrected fix was rebuilt on `main` `4bae7520` and put through a second validation round. Its code validator returned SHIP-WITH-FIXES with one more regression, a MINOR: on a paused completion, releasing the shared pause gate also wakes a stopped run's `fit` that the stop-then-start race (ruling 11) left parked there. Its docs validator returned REFUTED as written, with one MAJOR: the docs say a stale fit leaves the newer run's monitor alone, but only the settle is fenced. Its PR opens once both are corrected, after this record merges. Until it lands, #2519 describes the wedge as current behaviour |
| juniper-service-core | A successful resume (`resume_ok`) can still miss broadcasts. A broadcast made while no client is connected is never buffered (`manager.py:451-452`). One that lands while `_handle_resume` sends the replay is buffered but goes only to active sockets, and the resuming client is not active until afterwards | **ruled: fix now** (owner, 2026-11-08; §8). A fix was built, and its two validators returned SHIP-WITH-FIXES; among their findings, its new `replayed_through` keyword is public API, so it ships in a minor release of juniper-service-core, and juniper-ml's `[tools]` cap (`<0.8.0`) must rise when that release ships; juniper-cascor, juniper-data (its `[api]` extra), juniper-canopy and juniper-recurrence cap it `<0.8.0` too, on `main` and in their latest releases, so `juniper-ml[all]` stays on 0.7.x until theirs rise. No consumer imports service-core's `websocket` package; juniper-cascor runs its own copy (§8, ruling 11). On 2026-11-09 the corrected fix was rebuilt on `main` `4bae7520` and put through a second validation round: its code validator returned SHIP-WITH-FIXES with no correctness regression, and its docs validator returned REFUTED as written, with one MAJOR (the PR's session link is misspelt). Its PR opens once both are corrected, after this record merges. The race was reproduced against the real `WebSocketManager` with a yielding send (buffered seqs 1–7, client received 3, 4, 5, 7; `util/ad-hoc/2026-11-07_flood4_val_round2_resume_race_probe.py`), not over uvicorn |
| juniper-data | gitleaks-action's pull-request scan reads one unpaginated page of the PR's commits (30 by default), so a longer PR would not be fully scanned, and it walks that page with `--first-parent`, which drops the commits a merge brought in | **ruled: fix now** (owner, 2026-11-08; §8), for juniper-data. A fix was built. Its two validators returned SHIP-WITH-FIXES, none of their findings a regression, and on 2026-11-09 its corrections were applied, among them scanning a merge commit's own changes (`--remerge-diff`); its PR opens after this record merges. The fix's builder found the page to be the PR's **oldest** 30 commits, so the pull-request scan never reaches commit 31 onward, the head included. The action passes `--no-merges --first-parent` on every pull-request scan, whatever its length, so at any length the walk skips the commits a merge brought in as a second parent; and its range runs from the parent of the page's oldest commit, not from the merge base, so it can also walk into the base branch (`src/gitleaks.js:113-117, 160-172` at the pinned SHA). juniper-ml#1797's run (88 commits) logged `12 commits scanned.`, but only one of the 12, its commit 30, was the pull request's own; the other 11 were already on `main`. juniper-data#370 (18 commits, nine of them merges) logged `14 commits scanned.`: one of its nine non-merge commits, and 13 already on `main`. The seven other Juniper repositories that run Gitleaks in CI (all but juniper-recurrence) run the action the same way, at the same SHA, and the one fix built changes juniper-data alone: its `ci.yml`, its Gitleaks test file, two CI docs and its CHANGELOG (ruling 10). Only juniper-ml has had pull requests over 30 commits: four (#729, #1100, #1797 and #2045) |

## §5 Per-PR disposition

Rendered on 2026-11-08 by `util/ad-hoc/2026-11-07_flood4_disposition_render.py`. Its inputs are the six carriers' manifests and the rows no carrier holds, archived under `reports/2026-11-08_flood4-disposition/` (its README says how to re-render), and each PR's live state and title. A re-render therefore shows the states and titles at that moment, and needs an authenticated `gh`: without one the renderer still exits 0, printing every carrier as "(open)" and every state as "?". A draft split across two carriers has one row naming both. "Carried with fixes" means the carrier changed the draft's content where triage or validation found it wrong. The evaluation column is the builder's one-line reason, cut at 420 characters; the manifest holds the whole of it.

### juniper-canopy (8)

| PR | title | kind | outcome | evaluation |
|---|---|---|---|---|
| #789 | test(security): pin the Bandit SARIF install and PR upload failure | tests | carried in #797 (`733b6a3e`); **closed** | 7 tests pass on main; mutant bare `pip install bandit` killed |
| #790 | docs(ci): document the Gitleaks ruleset contract | docs | carried with fixes in #802 (`63a2f3d7`); **closed** | content re-derived on main: .gitleaks.toml [extend] useDefault, the AND-scoped generic-api-key allowlist and its conda paths, gitleaks-action v3.0.0 pin, GITLEAKS_VERSION 8.24.3, GITLEAKS_PARITY_REQUIRED 1; the weekly-scan runbook corrections (`pip install -e ".[dev]"`, `pip-audit --desc on --skip-editable`, no gitleaks in security-scan.yml) |
| #791 | docs(ci): document the unit-lane Codecov token and the test-tree root | docs | carried with fixes in #802 (`63a2f3d7`); **closed** | DAMAGED verdict re-derived as a false positive: the fence-aware docs screen (juniper-ci-tools 0.9.1 source with base_fenced/head_fenced maps, util/ad-hoc/2026-11-07_flood4_worktree_docs_screen.py) gives 0 FAIL; the flood-3 helper, which omits the fence maps, still reports the deleted ```yaml comment '# Check GitHub Actions logs' as a heading. Codecov inputs and lane wiring re-derived; agrees with #795's pins. |
| #792 | test(ci): pin the lockfile regen's refusal of an empty payload | tests | carried with fixes in #797 (`733b6a3e`); **closed** | 10 tests pass; guard mutant killed with no host write; a simulated macOS leg reproduces CI's exact 5 failures without the stand-in and passes with it |
| #793 | docs(ci): document the AGENTS.md date check | docs | carried with fixes in #802 (`63a2f3d7`); **closed** | content re-derived on main: workflow 'AGENTS.md Date Check', job verify-date, verify-only; the workflow header still names tests/test_agents_md_{header_schema,version_drift}.py, absent from the tree (the doc says so). Agrees with #794's case list. |
| #794 | test(ci): pin the AGENTS.md date check's verify step | tests | carried with fixes in #797 (`733b6a3e`); **closed** | 18 tests pass under four hostile global configs; future-date mutant killed; the draft's fixture fails 5 under a signing config |
| #795 | test(ci): pin the unit lane's Codecov token and the xml pytest writes | tests | carried in #797 (`733b6a3e`); **closed** | 16 tests pass on main and 16 against the docs carrier's ci.yml (comment change); token-swap mutant killed. Body's 'PR #788 is the unmerged MNIST fix' is stale (#788 merged 2026-11-04); not carried into any text. |
| #796 | docs(staging): document the mnist declared-param filter | docs | carried with fixes in #802 (`63a2f3d7`); **closed** | stacked draft carried by its own hunks, so no retarget is needed; DECLARED_PARAM_DEFAULTS['mnist'] re-derived (13 fields, n_samples and flatten declared, noise absent, no spiral/xor/gaussian entry). Its body claim 'not on main' is stale (#788 merged 2026-11-04); not carried. |

### juniper-data (9)

| PR | title | kind | outcome | evaluation |
|---|---|---|---|---|
| #509 | docs(ci): record the v1.0.265 @claude checkout pin | docs | carried with fixes in #519 (`4d8380dd`); **closed** | CI class U (never screened: only the base-branch guard ever ran on e7182b2); content re-derived locally instead -- claude.yml pin/triggers on main, and branch.ts / tag/index.ts at 6d5ae526 for every quoted error string and mechanism (claim_check.log). |
| #510 | docs(ci): record what the Documentation Links job actually runs | docs | carried with fixes in #519 (`4d8380dd`); **closed** | CI green; claims re-derived: ci.yml docs job and pins, the hook's juniper-doc-tools>=0.1.1,<0.2.0 and its .md-only trigger, pyproject/AGENTS.md 0.17.1, agents-md-touch-up.yml names and verify-only, the three absent scripts, and juniper-ci-tools 0.9.1 (PyPI latest) lint sources at tag juniper-ci-tools-v0.9.1 (sibling prefixes, working-directory precedence, exit codes, six header fields, pattern-only date, the stale... |
| #511 | docs(ci): record the Gitleaks ruleset and engine pin | docs | carried with fixes in #519 (`4d8380dd`); **closed** | CI green; claims re-derived against main (ci.yml pin/engine/skip/self-test, .gitleaks.toml, security-scan.yml, test_gitleaks_config.py) and upstream at the pinned refs (gitleaks-action e0c47f4f src/index.js + src/gitleaks.js; gitleaks v8.24.3 cmd/root.go, sources/git.go, config/config.go, config/rule.go). |
| #512 | test(ci): pin local coverage gates and the Bandit SARIF upload | tests | carried in #518 (`4f04fc8d`); **closed** | Required checks green (triage); all three files byte-identical to the head blobs; 22 pass alone; mutants M1-M3 killed. Triage note kept: 2 of 4 asserts in the 7-row parametrize test the table against itself (padding, not vacuous: M1 kills 7). Validator T-F2 (kept as drafted, per the orchestrator): 6 of the 7 parametrize rows add nothing -- every row runs the same two workflow-binding asserts, and the other two res... |
| #513 | test: pin the published image manifest's digest identity | tests | carried with fixes in #518 (`4f04fc8d`); **closed** | Required checks green incl. macOS (triage); content TRUE; 8 pass alone under `bash -e`; mutant M4 killed. Carrier differs from the head blob only by the T-F1 fix. |
| #514 | test(image): pin the publish job's tag gates | tests | carried with fixes in #518 (`4f04fc8d`); **closed** | Content TRUE on main (12 pass under `bash -e`; mutant M5 killed after the fixes). Carrier differs from the head blob only by the bash-path, shell-semantics and fail-not-skip fixes (blob_compare.log). |
| #515 | docs: record sequence windowing and the full generator catalog | docs | carried in #519 (`4d8380dd`); **closed** | CI green; claims re-derived: GENERATOR_REGISTRY (juniper_data/api/routes/generators.py) has exactly the 16 names; versions synthetics 3.0.0, equities 5.0.0, equities_seq 6.0.0, arc_agi 4.0.0; SyntheticSequenceParams defaults 2000/32/1/1.0/0.8/0.1/0, W = n_steps - lookback - horizon + 1 >= 3, train+val < 1; equities_seq lookback 64; EQUITIES_FEATURE_COLUMNS = 15; the windowers, temporal_split_indices and the four c... |
| #516 | test(publish): pin the TestPyPI install verify | tests | carried with fixes in #518 (`4f04fc8d`); **closed** | Required checks green (triage); 6 pass alone; mutant M6 (add --extra-index-url pypi.org) killed, 4 failed. Carrier differs from the head blob only by the T-F3 docstrings. |
| #517 | test(security): pin the failed-auth throttle cap, prune horizon, and window reset | tests | carried in #518 (`4f04fc8d`); **closed** | test_middleware.py and api/security.py unchanged on main since the draft's merge-base c7c5685, so the result equals the head blob; the 3 new tests pass; mutants M7 (cutoff 2w->1w) and M8 (evict newest) each killed by a NEW test. |

### juniper-ml (57)

| PR | title | kind | outcome | evaluation |
|---|---|---|---|---|
| #2271 | chore(settings): add idleCompaction setting to local configuration | owner | closed on the owner's ruling (2026-11-06); **closed** | The owner's own PR. Its commit 85c66d62 is unsigned, so under required_signatures it can never merge. Its only change, "idleCompaction": false in the repo-root settings.local.json (a file Claude Code does not read), now lives in the owner's ~/.claude/settings.json, and its branch was deleted on 2026-11-08 (owner ruling, sec 8). |
| #2360 | fix(tmp): repo tmp/ instead of /tmp -- fixed E2E run dir + reaper roots, launcher TMPDIR + git ceiling, gate G-TMP (2026-10-26 rule) | owner | not this arc's; **open** | Armed and DIRTY on purpose; it merges last (another arc). |
| #2403 | test(launchers): pin wake_the_claude boolean and alias flag edges | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | 4 of its 5 tests expected the pre-#2438 argv (10 failures with subtests: 1 + 1 + 4 + 4); rewritten against current main, near-miss refusals (--remote-controls, --dangerously-skip-permission) kept because no main test pins them. VALIDATION (tests F1): the effort test keeps only its --effort 1 half (now test_effort_false_omits_the_effort); its --effort 0 half pinned `--effort auto`, which Claude Code 2.1.316-2.1.319... |
| #2404 | docs(reference): local Claude launcher contract after #2396 | docs | round 3 (owner, 2026-11-07); **open** | Launcher docs whose claims main contradicts since #2438/#2468; to be considered individually. |
| #2406 | docs(reference): wake_the_claude -v, remote-control name, and launch errors | docs | round 3 (owner, 2026-11-07); **open** | Launcher docs whose remote-control-name claim main contradicts since #2438; to be considered individually. |
| #2407 | test(launchers): pin claudey flag, env, and version edges | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | conflicted with main and failed mypy; rebuilt from main's file |
| #2409 | docs(reference): config-tools alias pitfalls and the untyped 0.1.0 wheel | docs | carried with fixes in #2519 (`8d73d441`); **closed** | config-tools alias pitfalls and the py.typed history verified (code, PyPI wheels, tags); two false statements fixed |
| #2410 | test(packaging): built wheels must ship py.typed | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | positive wheel test kept and mutation-checked (a packages.find mutant that every source check misses kills it) |
| #2412 | docs(reference): host-check wording for kubectl D3 and G-MEM pages | docs | carried with fixes in #2519 (`8d73d441`); **closed** | E-H3 wording verified against host_state_check.py and macvm_ctl.bash; three false sentences and one unsupported sentence fixed |
| #2413 | test(experiments): a zero score and a zero theta stay measured values | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2414 | test(agents-md): pin three-dot, whitespace, and unset BASE_SHA on the date check | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2416 | test(turing): pin which capture decides G-SEC block-all | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2417 | docs(reference): a zero score and a zero theta stay measured values | docs | carried with fixes in #2519 (`8d73d441`); **closed** | zero handling verified by probe (summary, plot, columns, theta); the column scope, -inf, theta 0.0 and fixture sentences fixed, and the section moved out of the Eval scalars section it had split |
| #2418 | docs(reference): Phase D trial drop-in and settings-key write | docs | carried with fixes in #2519 (`8d73d441`); **closed** | drop-in and key-writer contract verified line by line; the reset-list, LoadCredential, wrapper, NONE and symlink sentences fixed |
| #2419 | test(service-core): cap live failed-auth source IPs by dropping the oldest | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | carried test clean; a trigger-boundary pin added |
| #2420 | fix(ad-hoc): keep P12 worktree cleanup from deleting uncommitted files | fix | closed on the owner's ruling (2026-11-06); **closed** | Duplicates #2435, and would revert #2415's fail-closed fix. |
| #2421 | test(backup): pin how the Phase D trial drop-in merges onto the live unit | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | test/CI half only (docs pair #2418 is the docs carrier's); wording corrected |
| #2422 | docs(reference): the failed-auth table drops the oldest source IPs | docs | carried with fixes in #2519 (`8d73d441`); **closed** | failed-auth cap mechanics verified by probe; the 255-address test description and the 10,000 peak wording fixed, and the expiry-test sentences name #2419's cap test (tests carrier) |
| #2424 | docs(reference): G-SEC block-all is the getblockall capture | tests + docs | carried with fixes in #2517 (`7bc9d3e2`); **closed**; and not carried; closed with #2519 (`8d73d441`); **closed** | util/host_state_check.py reads sec = ctx.probe['security'] and get_capture(sec, 'blockall', 'socketfilterfw --getblockall'); #2416's carried test_state_2_global_line_is_not_the_block_all_capture pins it (state 2 + getblockall disabled -> fail, remediation only --setblockall on) / same claim as #2426, which is better grounded: #2424 has two false statements, drops still-true util-entry text, puts its section just b... |
| #2425 | test(ci-tools): a list-item fence indented 3 spaces is not a heading | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2426 | docs(reference): G-SEC's firewall gate reads getblockall | docs | carried with fixes in #2519 (`8d73d441`); **closed** | G-SEC getblockall gate verified (decision table confirmed by probe); the State-0 message sentence fixed and the State-1 sentence qualified |
| #2427 | test(service-core): an exhausted rate-limit window admits again at the boundary | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2428 | docs(reference): the safe_merge success SHA is the verified head | docs | carried with fixes in #2519 (`8d73d441`); **closed** | MERGED-line SHA semantics verified; the --repo owner/repo consequence (measured), the exit-3 stream, the squash-only 'Expected' and the net-row label fixed |
| #2429 | test(experiments): a non-object stats.json is not an empty headline | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2430 | test(service-core): a connection burst refills only up to its cap | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2431 | test(experiments): a failed snapshot save leaves no model and does not re-fit | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2432 | docs(reference): an empty stats.json is not a missing file | tests + docs | carried with fixes in #2517 (`7bc9d3e2`); **closed**; and carried with fixes in #2519 (`8d73d441`); **closed** | util/experiments/run_suite.py _read_stats returns None for a missing file, OSError/ValueError and a non-dict; #2429's carried tests pin {} beating recorded metrics and non-object JSON falling back / _read_stats/_row_metrics verified by probe; the overview scope and the /1 re-derivation exception fixed, and the section moved below the jq block it had swallowed |
| #2433 | docs(reference): the worker connection bucket refills only up to its burst | docs | carried with fixes in #2519 (`8d73d441`); **closed** | token-bucket maths verified by probe; HandshakeCooldown scoped to /ws/control, the cleanup-pass timing, the rate-0 refusal and the test path fixed, and the section moved below the symptom table it had swallowed |
| #2434 | test(experiments): a schema-1 eval_scalars block is not the final evaluation | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2435 | fix(ad-hoc): keep P12 worktree cleanup from deleting uncommitted files | fix | closed on the owner's ruling (2026-11-06); **closed** | Moot: the P12 worktree cleanup it guarded is finished. |
| #2436 | test(service-core): pin how a stuck worker's scores become a duplicate | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2437 | docs(reference): a failed snapshot save does not re-fit | docs | carried with fixes in #2519 (`8d73d441`); **closed** | save path verified (operation_id branch, failed phase, degraded exit 1); the cheatsheet symptom label and the overview row's dropped text fixed, and the cheatsheet Tip moved below the line it had split |
| #2439 | test(service-core): pin control-channel refill and handshake boundaries | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2440 | docs(reference): claudey defaults, prompt after --, and version flags | docs | not carried; closed with #2519 (`8d73d441`); **closed** | carries #2438's pre-squash commit and conflicts in five files; its launcher docs describe the scripts before #2468, whose own cheatsheet text (DEVELOPER_CHEATSHEET 173-188 on main) is current; its one still-true correction (the -- in the --fork-session example) is carried once, through #2452 |
| #2441 | test(service-core): pin replay continuity at the buffer edge | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | tests clean; docstring claim corrected |
| #2442 | docs(reference): a worker anomaly warning does not reject the result | docs | carried with fixes in #2519 (`8d73d441`); **closed** | anomaly detector bounds, duplicate window and accept-with-warning verified by probe; the duplicate-rule sentence fixed, windows 0, 1 and 2 and total_results stated as the code computes them (security.py:239-247, :263), and the section moved out of the REFERENCE footer |
| #2443 | test(workers): an anomaly warning still accepts the result | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2444 | docs(reference): a training resume one seq before the window is still continuous | docs | carried with fixes in #2519 (`8d73d441`); **closed** | replay continuity, chunking and connection caps verified by probe; the out-of-range sentence, the 60000 framing and three pre-accept-close rows fixed |
| #2445 | test(service-core): pin replay speed, range, and paused terminal transitions | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | tests clean; docstring claim corrected |
| #2446 | docs(reference): /ws/control banks at most its burst and blocks on the Nth handshake | docs | carried with fixes in #2519 (`8d73d441`); **closed** | burst, Origin and cooldown edges verified by probe; the retry_after path and four sentences claiming a log carries the close code fixed (uvicorn logs only the 403) |
| #2447 | test(service-core): a measured zero heartbeat overwrites, and the exact timeout is stale | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2448 | test(experiments): refuse a per-run timeout equal to the driver budget | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | test clean; registration completed in all three lists; coverage-gap text corrected |
| #2449 | docs(reference): a measured zero heartbeat overwrites, and the exact timeout is stale | docs | carried with fixes in #2519 (`8d73d441`); **closed** | heartbeat None-versus-zero contract verified by probe; seven rows or sentences fixed (idle pool at equality, clock clamp, StatisticsError on 3.12 only, a zero is not idle, a raising source) |
| #2451 | test(service-core): admit a request body that exactly fills the cap | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2452 | docs(reference): local Claude launcher prompt, defaults, and version flags | docs | carried with fixes in #2519 (`8d73d441`); **closed** | only its still-true correction is carried: main's --fork-session example comment now shows the -- that wake_the_claude.bash:342 sends before the prompt (tests/test_wake_the_claude.py:1331); the rest of its launcher page predates #2468, whose own cheatsheet text is current |
| #2455 | test(release-train): pin archive and PR-body caps at equality | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | mypy failed on the draft; tests passed |
| #2456 | docs(reference): a request body that fills the cap is delivered | docs | carried with fixes in #2519 (`8d73d441`); **closed** | body-cap equality verified by probe; the table scoped to the ASGI layer (under uvicorn the parser answers a bad Content-Length first), the worker binary-frame cap given as 100 MiB (worker_stream.py:72), and one sentence added naming the boundary suite the tests carrier lands first |
| #2457 | docs(reference): recurrence 0.8.0 crossval 500 on model-core 0.2.0 | docs | carried with fixes in #2519 (`8d73d441`); **closed** | 0.8.0 + model-core 0.2.0 crossval 500 verified at the tags; remedy rewritten: 0.8.1 on PyPI since 2026-11-06 09:35Z, and juniper-ml 0.11.4 floors [recurrence] at >=0.8.1 |
| #2458 | test(service-core): admit a WebSocket frame that fills the 64KB cap | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2459 | test(host): pin kubectl skew and the throughput floor | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2460 | docs(reference): replay speed clamps to 10, and a paused fit stays paused | docs | carried with fixes in #2519 (`8d73d441`); **closed** | replay clamps and paused completion verified by probe; the router-mount sentence and the 'this checkout' provenance sentence fixed |
| #2461 | test(service-core): pin task reassignment at the exact timeout | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2462 | docs(reference): a WebSocket text frame of 65536 characters is delivered | docs | carried with fixes in #2519 (`8d73d441`); **closed** | 65536-character equality verified (code points, not bytes); the 100 MiB total cap, the receive() path and the JSON-object qualifier fixed, and the boundary suite named |
| #2463 | test(service-core): admit a worker result that fills each attachment budget | tests | carried in #2517 (`7bc9d3e2`); **closed** | own hunks 3-way applied onto origin/main; carried tests pass and kill a one-line mutant |
| #2464 | docs(reference): a task at the reassignment timeout stays assigned | docs | carried with fixes in #2519 (`8d73d441`); **closed** | strict > at the reassignment timeout verified by probe; the late-result, tail-dispatch and ~130 s sentences fixed |
| #2465 | docs(reference): root settings file does not disable idle compaction | docs | carried with fixes in #2519 (`8d73d441`); **closed** | the root settings.local.json is not a Claude Code settings file (repo files, and the code.claude.com settings pages re-fetched 2026-11-07); #2271's closed state and the worktree nuance fixed |
| #2466 | test(guard): pin brace expansion at the 64-alternative cap | tests | carried with fixes in #2517 (`7bc9d3e2`); **closed** | test clean on the merged tree; REFERENCE.md limited to suite registrations per the brief |

## §6 Process traps hit during the disposition

- **A worktree-isolated session cannot Write into the primary checkout's `tmp/`**, so the session scratchpad the harness names is refused there. Bash writes are allowed. The arc kept its scratch files in its own worktree's `tmp/flood4/` instead, as `.txt` / `.json` / `.log` only. Until juniper-ml#2522 (merged 2026-11-09 00:27Z) the doc-link hook scanned `tmp/`, and it reads `.txt` as well as markdown, so neither keeping scratch as `.txt` nor renaming one validator's 54 scratch `.md` copies to `.md.txt` kept them out of it: all 13,857 broken links its last run here reported were under `tmp/`.
- **A test that executes a workflow step inherits the step's absolute paths.** juniper-canopy#792's `lockfile-update.yml` step writes `/tmp/lockfile-commit*.json`. A builder's mutant run therefore wrote one under `/tmp` on the host (0 bytes; removed). Relocate every write path the step names, in every case, before running any mutant.
- **The Cursor fleet runs on the carriers themselves.** A pending, non-required `Cursor Automation: Add test coverage` check left juniper-data#518 `UNSTABLE` while every required context was green, and `util/safe_merge.py` merged it correctly. The fleet also opened new drafts about a carrier's subjects within minutes of the carrier **opening**, mostly before it merged:
  - juniper-data #520–#524, 7–32 minutes after #518 and #519 opened; #523 came after #519 had merged, and #524 after both had;
  - juniper-canopy #798–#801, 6–10 minutes after #797 opened, all before it merged.

  Then it stopped. No Cursor draft has followed a PR opened after 00:58Z, #802 and #2519 among them, and on #2519 all five `Cursor Automation` checks finished `neutral` within a second (03:22:39–40Z). Whether this record's PR draws any is open (§8).
- **`main` moved under a built carrier.** juniper-ml#2510 changed eight lines of `docs/QUICK_START.md` after the docs carrier was built on `303ccc0b`. A whole-file upload would have reverted it. `util/ad-hoc/2026-11-07_flood4_signed_push_batches.py` refuses any carrier path that `main` changed since the carrier's base, and the docs carrier was rebased onto #2517's head before it opened (§2).
- **The canopy carriers' `CHANGELOG.md` entries collided at the same insertion point.** The docs carrier was opened only after the tests carrier merged, its `CHANGELOG.md` re-merged three ways onto the new `main`. That avoided the three-step signed update-branch dance.
- **A merge under an open carrier needed that three-step.** juniper-ml#2517 went `DIRTY` when #2516 (`147263ec`) merged under it, in four shared files: `ci.yml`, `AGENTS.md`, `CHANGELOG.md` and `docs/REFERENCE.md`. Every commit here goes through GitHub's signed `createCommitOnBranch`, which cannot write a merge commit, so the repair took three steps:
  1. push `main`'s four files verbatim;
  2. `update-branch`, twice, because #2518 merged in between;
  3. push the three-way-merged files, `main`'s lines first.

  Three of the four files conflicted three ways with `main`, and `update-branch` refuses a merge that conflicts, so the branch first had to carry `main`'s copies. Afterwards the branch tree equalled the builder's validated merge tree (`c1313645`).
- **A draft split across two carriers must be closed only after the last of them merges.** The tests carrier's manifest also listed docs drafts #2424 and #2432, whose Test Suite Reference lines rode in #2517. So the close script closed both when #2517 merged, while #2519 still carried the rest. Both were reopened with an explanation, and closed again after #2519 merged.
- **Copies of one script diverged across worktrees.** A validator's worktree held older revisions of three of the juniper-ml tests builder's scripts (`…_ml_tests_manifest.py`, `…_ml_tests_rewrite_2403.py` and `…_ml_tests_rewrite_2407.py`). The older `…_rewrite_2403.py` still pins `--effort auto`. The harvest refuses a name whose copies differ unless an explicit rule picks one, and the builder's copies were taken (§7).
- **A gate that has not landed still binds what ships now.** Four validator probes named the system temp directory in 11 lines: detectors that read it to prove nothing was written there, a guard that refuses a `TMPDIR` under it, and docstrings. G-TMP (`util/tmp_path_literal_check.py`, juniper-ml#2360) gives each file a baseline count when it lands and lets an unlisted file carry none. These files would therefore either fail it or have to be listed in its baseline. The detector and guard lines now carry G-TMP's allow pragma, and the docstrings were reworded; no behaviour changed.
- **The gates already on `main` caught what the local screens missed.** Two of the record PR's validators ran them on the harvested scripts and found two failures the required checks would have reported:
  - G-PATH (`util/home_path_literal_check.py`) refuses the owner's home directory spelled out, and 8 lines in 7 scripts did. Six code paths now come from `os.path.expanduser` or `Path.home()`, which give the same strings on this host, a docstring usage line now says `~/`, and one line of recorded findings text keeps its literal under G-PATH's pragma.
  - One probe sent RFC 6455's sample `Sec-WebSocket-Key` nonce, which gitleaks' generic-api-key rule matches. It is now built at run time from its decoded text.

  The repository's pre-commit secrets hook had passed only because it scans staged changes, and nothing was staged.
- **Some juniper-ml tests fail only on this host.**
  - Five regression suites run alone, and 9 juniper-ci-tools tests, fail locally, identically on a clean `main`. Those 9 also trip the per-file coverage gate.
  - The 9 ci-tools tests pass on GitHub at identical content (juniper-ci-tools workflow run 41757850549), and the five suites pass in the required Regression Tests jobs that every juniper-ml carrier merged with. CI is the authority there.
  - The likely cause is this host's `TMPDIR`, which sits inside a checkout and the ecosystem root. No run with `TMPDIR` outside a checkout has been made to confirm it.
- **Large signed uploads went through in file-sized batches.** The juniper-ml tests carrier went up as ten `createCommitOnBranch` commits, one of them the 1.1 MB `docs/REFERENCE.md` alone, with no HTTP 499 or 502. Each later batch was pinned to the branch head, and every blob was read back afterwards.
- **The isolated session's classifier refused a `grep` whose pattern contained `git/ref`.** Redirecting the tool's output to a log and grepping the log separately ran.

## §7 Tooling added

All under `util/ad-hoc/`, dated `2026-11-07_flood4_*` (and `2026-11-08_flood4_*` for this record's PR), and kept as provenance (owner policy 2026-08-25). They ship in this record's PR, harvested from the nine of this arc's worktrees that held them:

- **The landing path (the orchestrator):**
  - `…_prep_pr_texts.py` freezes a carrier's validated files into a snapshot with sha256s, and writes the PR title, the body with its attribution, the commit body with its trailers, and the upload list. It never uploads `util/ad-hoc/` or `tmp/`.
  - `…_signed_push_batches.py` opens the PR as GitHub-signed commits in size-bounded batches. It refuses any carrier path `main` changed since the carrier's base, pins each later batch to the branch head, and reads every blob back.
  - `…_close_carried.py` closes a carried draft only when its carrier is MERGED, and skips any draft whose head moved after it was carried.
  - `…_disposition_render.py` renders §5 from the manifests and live PR states.
  - `…_docs_test_name_xcheck.py` checks that every test a docs carrier names exists.
- **The builders' instruments:** hunk extractors, stamp strippers and bumpers, carry and rebuild checks, claim checkers, mutation checkers, and the fence-aware heading screen `…_worktree_docs_screen.py`, which reads a `#` comment inside a code fence the way CI's juniper-ci-tools 0.9.1 does, not as the host's 0.8.0 did before its upgrade on 2026-11-08 (§8). The prefixes are `…_data_*`, `…_canopy_*` and `…_ml_tests_*` / `…_ml_docs_*`.
- **The validators' probes (`…_val_*`):**
  - `…_val_round2_resume_race_probe.py`, the §4 replay race;
  - `…_val_data_named_shell_probe.py`, which runs the real step under each `shell:`;
  - `…_val_r2_canopy_gitleaks_variants.py`, the pinned binary on each `.gitleaks.toml` variant;
  - `…_val_r2_canopy_comment_only.py`, YAML and TOML parsed before and after a comment edit;
  - the claim, fidelity and mutant harnesses.
- **This record's PR (`2026-11-08_flood4_*`):**
  - `…_harvest_scripts.py` lists every flood-4 script copy in the arc's worktrees (175 copies under 153 names). It refuses a name whose copies differ unless an explicit rule picks one, then copies the chosen ones.
  - `…_gtmp_pragma_pass.py` makes the harvested probes clean under G-TMP (§6) without changing what they do; `--check` only counts.
  - `…_archive_render_inputs.py` copies §5's six manifests into `reports/2026-11-08_flood4-disposition/`, checking each copy's sha256, and writes a render config with repo-relative paths. With an authenticated `gh`, the archived inputs re-rendered §5 byte for byte on 2026-11-08; a later re-render shows each PR's live state and title (§5).
  - `…_gpath_secret_pass.py` makes the harvested scripts pass G-PATH and the secret scan (§6), with exact single-occurrence edits.
  - `…_splice_sec5.py` writes the rendered tables into §5.
  - `…_record_round1_fixes.py` applies this record's first validation round.
  - `…_record_round2_fixes.py` applies the second, third and fourth validation rounds (V4's, V5's and V6's findings) and the next session's update: rulings 8–14, the new defects, round 2's triage outcome and the fixes' status.
  - `…_record_freeze.py` freezes this PR's validated files into the snapshot that the signed batch push uploads. The carriers' `…_prep_pr_texts.py` refuses `util/ad-hoc/` paths by design.

  With these, the PR ships 160 scripts. Before upload, the harvested scripts were also edited without changing what they compute:
  - 21 of 28 predicted CodeQL alerts were fixed in 16 scripts. The other 7 are the fields of a pydantic model defined inside a function, which the prescreen misreads as unused locals and CodeQL's unused-variable query does not consider.
  - 29 probes gained the `util/ad-hoc/README.md` provenance fields: 26 full headers, while three round-5 probes gained only `Related:`, which their usage text now prints as well.

## §8 Open items

**The owner's rulings of 2026-11-08 and 2026-11-09** (option labels verbatim, less the "(Recommended)" marker on the option each question advised):

1. **Approval**: "Merge, update, close". It covers this record's PR and the round-2 carriers. Ruling 5's chosen option extends it to the defect-fix PRs ("merged under this session's approval"). Each merges once its required checks pass on its final head. A carried draft is closed, with a comment naming its carrier, only after that carrier merges. No Cursor draft is merged, retargeted or un-drafted directly.
2. **The 13 drafts no ruling covered** (§1): "Fold into round 2".
3. **The launcher's default effort** (§4), in the owner's words: "let's go with option 2, restoring max as default. however, let's also add functionality descripted in option 1: if auto is selected, send no --effort flag." So `EFFORT_DEFAULT` becomes `max`, and `auto` sends no `--effort` flag. The change rides in round 2's launcher code carrier.
4. **juniper-ml#2271's setting**: "User settings + delete branch". **Done** on 2026-11-08.
   - `idleCompaction` is a real setting. Claude Code 2.1.319's settings schema describes it as "Set to false to stop Claude Code from compacting a long conversation while the session is idle. Defaults to true."
   - The repo-root `settings.local.json` is tracked but never read. Claude Code reads `.claude/settings.local.json`: 2.1.319 resolves it, for a worktree session, to the main checkout's untracked copy (as `main`'s `docs/REFERENCE.md` also says), and also reads the worktree's own copy, if it has one, as "the legacy local settings file". Neither that copy nor the four byte-identical copies in older worktrees holds an `idleCompaction` key. User settings were chosen because every repository's sessions read them.
   - `"idleCompaction": false` is now in the owner's `~/.claude/settings.json`, which every session reads.
   - The branch (`feat/disable-idle-compress-setting-for-claude-code`, at `dd98974e`) is deleted. Its only change was that one line. The closed PR keeps its diff.
5. **The §4 defects still open**: "Fix now", each in its own validated, signed PR:
   - the paused-fit wedge;
   - the `resume_ok` broadcast losses, both the no-client case and the replay race;
   - gitleaks-action's unpaginated commit list.
6. **Host state**: "Upgrade both, checked first".
   The check the ruling named was for `JuniperCanopy1`, and it preceded all three upgrades.
   - **Not done**: the check failed. Four live canopy E2E legs, another arc's, run from `JuniperCanopy1` (ports 8052, 8053, 8058 and 8059, up since 2026-10-10). Its juniper-observability 0.4.0 and juniper-service-core 0.5.0, both below canopy's floors, stay until the owner decides.
   - **Done anyway, on a per-environment reading of the ruling**: the host's juniper-ci-tools went from 0.8.0 to CI's 0.9.1. It lives in `JuniperCascor1`, which supplies the `pre-commit` and `juniper-check-doc-links` on `PATH` (`JuniperCanopy1` holds a separate 0.6.0, untouched), and `JuniperCascor1` got its own check: no live Python service (only five Serena MCP launchers running its `uv` binary) and a dry run with no dependency changes. It is reversible with `pip install juniper-ci-tools==0.8.0` there.
7. **Worktrees**: "All, after record merges". This arc's worktrees, and the five the 11-06 handoff still owed, are removed once this record merges. Each goes only after its PR is confirmed merged and its `tmp/` is checked under the retention rule.
8. **The agent guard's brace cap**: "Fail closed". `util/claude_agent_guard.py` expands a brace list only up to `MAX_BRACE_ALTERNATIVES` (64), so a word that spells `.ssh` or `.gnupg` only in its 65th or a later alternative passes its credential check. The guard is to refuse such a word instead. That inverts the test #2517 carried (`tests/test_claude_agent_guard_brace_cap.py:63-71`), and #2470, which documents the bypass as the cap to keep, is to be rewritten; both ride in round 2's juniper-ml carriers.
9. **Retry-After**: "Both in round 2". Two services truncate a `Retry-After`:
   - juniper-service-core's failed-auth throttle (`security.py:468` used `int()` where the rate limiter, at `:236`, rounds up), from #2514;
   - juniper-data's `RateLimiter`, which can send `Retry-After: 0` (`juniper_data/api/security.py:250`, `int()` with no floor of 1; the allowed path's `X-RateLimit-Reset`, `:254`, truncates the same way), and its failed-auth throttle (`:427`).

   Both fixes go into round 2, juniper-data's in a code carrier of its own. The service-core one was then carried outside this arc, by juniper-ml#2524 (merged 2026-11-08 15:53Z; it is in juniper-service-core 0.7.2, which PyPI did not yet serve when this was written), and #2514 was closed with a comment naming it.
10. **gitleaks-action outside juniper-data**: "All, after data's lands". Ruling 5 was given on juniper-data's case, and the same scan runs, at the same SHA, in the seven other repositories that use the action (all but juniper-recurrence). Only juniper-ml has had pull requests longer than the 30-commit page. After this ruling, a validator of juniper-data's fix found that the action's `--first-parent` walk cuts a scan short at any length (§4): modelled over every pull request of 30 commits or fewer, it drops commits in five of the eight repositories. The ruling predates that finding. Once juniper-data's fix has run green live, it is ported to juniper-ml, juniper-canopy, juniper-cascor, juniper-data-client, juniper-cascor-client, juniper-cascor-worker and juniper-deploy, one PR each. A port is not a copy: the repositories differ in where the scan's report is uploaded, whether the engine's version is pinned, and their own Gitleaks tests.
11. **Four more defects, found while ruling 5's fixes were built**: "Fix all four now", each in its own validated, signed PR:
    - juniper-cascor's own lifecycle manager has the paused-fit wedge (found by reading it and probing its state machine; not yet run at the manager level);
    - juniper-service-core's stop-then-start race: a start soon after a stop, before the old fit's next event, cancels the stop, and the old fit's return then marks the new run `COMPLETED` (reproduced with a probe);
    - juniper-cascor's own WebSocket manager has both resume losses (`src/api/websocket/manager.py:829-830`; in `training_stream.py`, the replay at `:390-416` and the promotion at `:290`);
    - juniper-service-core's broadcast drops a socket whose send fails without closing it; juniper-cascor already fixed its copy (F-CASCOR-004).

    The next update of this record gives each one's evidence and PR.
12. **The paused-fit fix, asked again with the missing context** (2026-11-09): "Confirm the fix". A side agent noted that a `docs/REFERENCE.md` text had called the behaviour an invariant to preserve, and that ruling 5 was given without that fact. The text came only from a Cursor draft, juniper-ml#2460, and `main` never carried it as one (§4); no person ruled it.
13. **Approval for the session that lands this record** (2026-11-09): the owner wrote "merge approval granted for this work arc", then chose "Merge, update, close" again. Ruling 1's approval held for its own session only; this one covers the next session, and adds the gitleaks port PRs to ruling 1's set: this record's PR, the defect-fix PRs, the gitleaks port PRs and the round-2 carriers.
14. **juniper-ml#2507** (2026-11-09), a round-2 tests draft that pins four `docs/REFERENCE.md` sites to `pyproject.toml` (the Package Overview Version cell, the "declares the following pins" sentence, the current series row of the Ecosystem Compatibility matrix and the recurrence "sets them to" clause): "Carry + extend propose.py". `util/release_train/propose.py` edits none of the four, so the tests alone would fail every juniper-ml release proposal, and any other that moves one of those pins, until someone fixed them by hand; the script is to be extended to rewrite them, in a small carrier of its own.

**Still open:**

- **Round 2**, 48 drafts, 47 of them open (#2514 is closed, carried by juniper-ml#2524):
  - the 35 juniper-ml drafts #2469–#2509;
  - juniper-ml #2512–#2515, juniper-data #520–#524 and juniper-canopy #798–#801.

  Eight of them change code: #2480, #2493, #2502, #2504, #2505, #2508, #2513 and #2514. All 48 were triaged against `main` on 2026-11-08, and the carried ones are to land in per-repository tests, docs and code carriers; the launcher's effort fix rides in the juniper-ml code carrier. #2484 is stacked on #2480's own branch, and #2513 follows up #2474. The triage leaves seven uncarried, still open and to be closed as superseded or duplicates (#2471, #2476, #2477, #2486, #2488, #2500 and #2501), and puts the other 40, whole, in part or rewritten, into juniper-ml's code, tests and docs carriers and juniper-data's and juniper-canopy's tests and docs carriers; #2514 went to juniper-ml#2524 instead, and juniper-data's code carrier holds ruling 9's fix and no draft. The next update of this record holds the triage table.
- **Round 3:** juniper-ml#2404 and #2406, each considered individually.
- **The three defect fixes** (ruling 5), and the `JuniperCanopy1` upgrade, not done because its check failed, which waits for the owner (ruling 6).
- **The four further defect fixes** (ruling 11), and the gitleaks fix's port to the seven other repositories once juniper-data's has run green live (ruling 10).
- **#2507's tests, with `util/release_train/propose.py` extended** (ruling 14), in the juniper-ml carriers.
- **A follow-up the docs carrier left.** `main`'s `CHANGELOG.md` entry for #2517 says #2424's Test Suite Reference line lacks "its link to a section only the docs carrier adds". That holds for #2432, but not for #2424, whose own section was not carried. #2426's equivalent section is `#the-firewall-gate-reads-getblockall`, and a follow-up could give that line #2426's link (round 4's F6; the juniper-ml docs manifest's `open_questions`).
- **Any drafts this record's PR draws.** None had followed a PR since 00:58Z (§6). Any that do are covered by no ruling.
- **Round 2's helper scripts.** The `util/ad-hoc/2026-11-0[89]_flood4r2_*.py` scripts round 2's agents wrote into the orchestrator's worktree are untracked there. Among them are the juniper-data gitleaks fix's five, renamed out of this PR's glob. They are to be committed as provenance before the worktree cleanup (ruling 7), which checks only `tmp/`, removes that worktree. Those five still fail G-PATH and G-TMP (`…_jd-gitleaks_run_pytest.py:50-51` and `:16`).
- **The evidence in `tmp/`.** The archived manifests cite 167 paths under `tmp/flood4/` (194 references, such as `claim_check.log`): the juniper-data and juniper-canopy manifests' in the orchestrator's worktree, the juniper-ml manifests' in their builders'. This PR's own corrections rest on `tmp/flood4/val-record/`, `tmp/flood4/round2-triage/`, `tmp/flood4/round2-fixes/pristine/` and `tmp/flood4/round2-session/codeql_orig/` in the orchestrator's worktree, on each fix's validator findings under `tmp/flood4-fix/` in that fix's worktrees (each service-core fix has two: its first build's and its rebuild's), and on `tmp/val-a-m1/` in juniper-ml's primary checkout. None is in `reports/`. Each worktree copy is to be archived before the worktree cleanup (ruling 7) removes it, and `tmp/val-a-m1/`, which that cleanup does not touch, falls under the retention rule.

## §9 Documents created or modified

The carriers (each merged 2026-11-08):

- **juniper-data#518** (tests; 00:46Z, `4f04fc8d`): `CHANGELOG.md`, and seven files under `juniper_data/tests/unit/`: `test_bandit_sarif_upload.py`, `test_check_module_coverage.py`, `test_middleware.py`, `test_publish_image_manifest_identity.py`, `test_publish_manifest_tag_gates.py`, `test_run_coverage_gates.py` and `test_testpypi_install_verify.py`.
- **juniper-data#519** (docs; 00:38Z, `4d8380dd`): `CHANGELOG.md`, `docs/{DEVELOPER_CHEATSHEET,DOCUMENTATION_OVERVIEW,QUICK_START,REFERENCE,USER_MANUAL}.md` and `docs/ci_cd/CICD_{MANUAL,QUICK_START,REFERENCE}.md`.
- **juniper-canopy#797** (tests; 00:58Z, `733b6a3e`): `CHANGELOG.md`, `src/tests/regression/{test_bandit_sarif_upload,test_codecov_token_upload,test_lockfile_regen_empty_payload}.py` and `src/tests/unit/test_agents_md_date_check.py`.
- **juniper-canopy#802** (docs; 01:21Z, `63a2f3d7`):
  - `CHANGELOG.md`;
  - `.github/workflows/ci.yml`, `.gitleaks.toml` and `src/tests/regression/test_gitleaks_config.py`, comment-only;
  - `docs/{DEVELOPER_CHEATSHEET,QUICK_START,REFERENCE,USER_MANUAL}.md` and `docs/api/API_REFERENCE.md`;
  - `docs/ci_cd/CICD_{ENVIRONMENT_SETUP,MANUAL,QUICK_START,REFERENCE}.md`.
- **juniper-ml#2517** (tests; 01:49Z, `7bc9d3e2`), 34 paths:
  - `.github/workflows/ci.yml`, `AGENTS.md`, `CHANGELOG.md` and `docs/REFERENCE.md`, for the suite registrations;
  - 14 test files under `juniper-service-core/tests/`, 1 under `juniper-ci-tools/tests/` and 15 under `tests/`. The PR lists them.
- **juniper-ml#2519** (docs; 03:35Z, `8d73d441`): `CHANGELOG.md`, `docs/{DEVELOPER_CHEATSHEET_JUNIPER-ML,DOCUMENTATION_OVERVIEW,QUICK_START,REFERENCE}.md`, `juniper-config-tools/README.md` and `juniper-service-core/README.md`.

This record's PR:

- `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` (new);
- `CHANGELOG.md`, for its entry;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md` (new), round 1's closing handoff;
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md` (new), its successor's, archived as written: where it differs from this record (its table lists ruling 12 among the rulings of 2026-11-08, it calls #473 the lifecycle's design PR, and its title calls the three fixes validated), this record is current;
- `reports/2026-11-08_flood4-disposition/` (new): its README, the six manifests and the render config;
- the `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts (new; §7).

Outside any repository: the owner's `~/.claude/settings.json`, which gained `"idleCompaction": false` (§8, ruling 4).
