# Lane A agent A3 — run-state, environment, git and issue re-derivation

- **Procedure:** `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §2 Lane A and §7
- **Target:** `JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`
- **Entry point:** experiment run state, installed metadata, package declarations, git history, GitHub issues, PyPI, parent inventory, and launcher text
- **Date:** 2026-10-03
- **Brief:** Read-only re-derivation independent of the target's cited behavioural source files and `.amp/in/artifacts`.

## 0. Instruments

| Instrument | Could it produce a different answer? | Sample size | What was NOT done |
|---|---|---:|---|
| JSONL index plus pointed-to manifests/meta | Yes: new runs append rows and manifests expose different versions/outcomes | 477 index rows; 2 equities-sequence manifests inspected deeply | No service started; no evidence directory opened |
| Environment-local `python -m pip show/check` and import | Yes: each environment has independent mutable installed state | 3 environments; 10 requested distributions; 1 import | No install, upgrade, or environment mutation |
| `rg` over package metadata/version/launcher/parent files | Yes: declarations and line numbers can drift | 3 recurrence versions, 3 pyprojects, 2 launchers, 1 parent guide | No behavioural source cited by the target was read |
| Git log/status/tag | Yes: repositories and worktrees can advance or become dirty | 5 repositories; 30 recent commits requested per repo; 1 tag | No checkout, fetch, commit, or modification |
| Authenticated `gh issue view` | Yes: title, state, and body can change | 11 requested issues/PRs | No issue/comment created or changed |
| PyPI JSON API | Yes: releases can appear | 2 projects | No package download or installation |

## 1. Experiment run state — **CONTRADICTED**

The historical subclaim is verified, but the current census is larger and contains a second recurrence × equities run today that the stated plan claim omits.

> `TOTAL=477`
>
> `28 {"cell_id":"c000-cd6f1c31",..."run_id":"20260809T080404Z-c951"...}`
>
> `29 {"cell_id":"c001-0d8782ae","outcome":"succeeded",..."run_id":"20260809T080424Z-33db"...}`

The old row-29 manifest confirms dataset `equities_seq-1.0.0-075eb51abb6d2dbe`, recurrence `0.2.0`, model `0.1.5`, service-core `0.5.0`, data `0.6.0`, data-client `0.4.2`, 10 features, and acceptance success:

> `"dataset_id": "equities_seq-1.0.0-075eb51abb6d2dbe"`
>
> `"n_features": 10`
>
> `"juniper-recurrence": { ... "version": "0.2.0" }`
>
> `"acceptance": { "ok": true, "reasons": [] }`

There are 42 index rows whose suite name contains `recurrence` or `e-h`: 36 recurrence rows on 2026-08-09, two cascor `e-h-real-data` rows on 2026-08-09, two more cascor rows on 2026-08-13, and two recurrence rows on 2026-10-03. Outcomes among the 36 old recurrence rows are 28 succeeded, seven `torn_down_early`, and one failed. Only one old recurrence row uses equities (`c001-0d8782ae`); the cascor E-H rows use flat `equities`, not recurrence.

Today's two rows are:

> `476 ... "cell_id": "c000-cd6f1c31", "outcome": "succeeded", ... "run_id": "20261003T091356Z-223a"`
>
> `477 ... "cell_id": "c001-0d8782ae", "outcome": "succeeded", ... "run_id": "20261003T091414Z-4ba6"`

The new equities cell used `equities_seq-6.0.0-15505731cba5b86d`, recurrence 0.5.0, model 0.1.5, service-core 0.5.0, data 0.14.0, data-client 0.5.0, and 15 features. Its index outcome says succeeded, but acceptance failed because cross-validation still required the retired key:

> `"acceptance": {"ok": false, "reasons": ["crossval failed: HTTP 422: invalid dataset: NPZ artifact is missing required key 'X_full'"]}`
>
> `"dataset_id": "equities_seq-6.0.0-15505731cba5b86d"`
>
> `"n_features": 15`
>
> `"juniper-recurrence": { ... "version": "0.5.0" }`

**Correction:** report 477 total rows and both recurrence × equities runs: 2026-08-09 accepted/succeeded at 1.0.0 with 10 features, and 2026-10-03 index-succeeded but acceptance-failed at 6.0.0 with 15 features.

## 2. Installed package metadata — **VERIFIED**

The JuniperCascor1 values match §2.2:

> `juniper-recurrence 0.5.0` / `Editable project location: .../juniper-recurrence/juniper-recurrence`
>
> `juniper-recurrence-model 0.1.5` / `Location: .../site-packages`
>
> `juniper-service-core 0.5.0`
>
> `juniper-data-client 0.5.0`; `juniper-observability 0.4.0`

`pip check` reports the two claimed recurrence conflicts (and two additional CUDA conflicts):

> `juniper-recurrence 0.5.0 has requirement juniper-recurrence-model<0.4.0,>=0.3.0, but you have ... 0.1.5.`
>
> `juniper-recurrence 0.5.0 has requirement juniper-service-core<0.8.0,>=0.6.0, but you have ... 0.5.0.`

JuniperData has editable `juniper-data 0.12.0` and `yfinance 1.4.1`. JuniperCanopy1 has editable canopy 0.6.0, torch 2.11.0+cpu, and no recurrence client:

> `WARNING: Package(s) not found: juniper-recurrence-client`
>
> `ImportError: .../libtorch_python.so: undefined symbol: _PyObject_NextNotImplemented`

## 3. Pins and declared versions — **VERIFIED**

> `"juniper-service-core>=0.6.0,<0.8.0"`
>
> `"juniper-recurrence-model>=0.3.0,<0.4.0"`
>
> app `_version.py`: `__version__ = "0.5.0"`; model: `"0.3.0"`; client: `"0.3.0"`

Canopy declares `version = "0.8.1"`; `rg` found no `juniper-recurrence*` dependency in its pyproject. The juniper-ml all/servers declaration carries:

> `"juniper-data>=0.15.0"`

An old generated `juniper-recurrence/build/lib/.../_version.py` says 0.4.0, but it is not one of the three current sub-package source version files.

## 4. Git state and data release history — **VERIFIED**

Heads and short-status counts:

> `juniper-recurrence be081fa ... (#188)` / `STATUS_COUNT 0`
>
> `juniper-canopy 72b1a5f6 ... (#690)` / `STATUS_COUNT 0`
>
> `juniper-data 1c67f8d ... (#443)` / `STATUS_COUNT 0`
>
> `juniper-data-client 0ec4b30 ... (#216)` / `STATUS_COUNT 0`
>
> `juniper-ml afb02801 ... (#2108)` / `STATUS_COUNT 229`

The requested recent logs were available. The decisive juniper-data sequence is:

> `39d1cab docs(changelog): ... 0.16.0 ... (#435)`
>
> `1afc348 fix(equities_seq): declared regression ... generator 6.0.0 (X8) (#437)`
>
> `v0.16.0`
>
> `39d1cab27a2067b8b00a5d44a8a37a739bd1d1ed 2026-09-24T03:14:12-05:00 ...`

Thus v0.16.0 is tagged at `39d1cab`, before #437's `1afc348`; 0.16.0 does not contain X8.

## 5. GitHub issues and characterisations — **CONTRADICTED**

`gh` was authenticated. Requested title/state census:

> recurrence#178 OPEN — `ci-recurrence-bench: a path-scoped lane cannot see a break introduced by a dependency...`
>
> recurrence#182 OPEN — `Drop the anyio BlockingPortal filterwarnings ignore once starlette stops importing the alias (6f)`
>
> recurrence#183 OPEN — `snapshots_dir: anchor the default to the repo, not the working directory`
>
> recurrence#184 OPEN — `snapshots_dir: refuse it in an experiment YAML (launcher-owned, like host/port)`
>
> canopy#368 OPEN — `Model selection + bidirectional dataset×model compatibility gating`
>
> canopy#631 CLOSED — `The published wheel omits 10 top-level modules that 13 of its own shipped files import`
>
> data#409 OPEN — `equities / equities_seq: at bare defaults both produce data their consumers cannot train on...`
>
> data#423 OPEN — `Decision 12: partition_provenance is owner-ruled... but unspecified, unimplemented and was untracked`
>
> data#437 MERGED — `fix(equities_seq): declared regression, not classification, at generator 6.0.0...`
>
> ml#1994 OPEN — `conf/requirements_ci.txt no longer resolves in three repos...`
>
> ml#2062 OPEN — `juniper-ml[servers] installs canopy and cascor without the clients they talk through...`

The characterisations of data#409, data#437, canopy#631, and ml#2062 match their bodies. recurrence#184 explicitly says YAML outranks environment. recurrence#183 is instead the CWD-relative default problem. Most importantly, recurrence#178 is not “dispatch PAT cannot reach recurrence repo”; it tracks a path-scoped bench lane blind to dependency changes. Its later fix commits mention dispatch, but the issue's title/body do not have the plan's characterisation.

**Correction:** characterise recurrence#178 as the open path-filter/bench-trigger gap; reserve “YAML beats env” for recurrence#184, while #183 concerns anchoring the default away from process CWD.

## 6. PyPI — **CONTRADICTED**

The data-release assumption is verified:

> `juniper-data latest: "0.16.0"`; `has_017: false`

The recurrence-model fix-wheel statement is not true on PyPI today:

> `juniper-recurrence-model latest: "0.3.0"`; `has_032: false`
>
> releases end at `"0.3.0"`

**Correction:** 0.3.2 does not exist on PyPI as of this check; latest is 0.3.0.

## 7. Parent ecosystem guide — **VERIFIED**

The parent `AGENTS.md` includes recurrence in Active Repositories and says:

> `juniper-recurrence ... LMU recurrence service + model + client...`
>
> `juniper-recurrence has no conda environment at all`

It does not include recurrence in the dependency graph, Service Ports table, or Project-Level Agent Files table. Those tables list only the older ecosystem members/services; this confirms the inventory omissions relevant to F-X7/F-E5.

## 8. Launcher defaults — **CONTRADICTED**

The defaults themselves are verified, but one claimed isolated-stack line range is off:

> `experiment_stack.bash:67 ... default: JuniperCascor1`
>
> `experiment_stack.bash:142: RECURRENCE_CONDA="${JUNIPER_EXP_RECURRENCE_CONDA:-JuniperCascor1}"`
>
> `isolated_stack.bash:44-46 ... default: JuniperCascor1 ...`
>
> `isolated_stack.bash:96: RECURRENCE_CONDA="${JUNIPER_E2E_RECURRENCE_CONDA:-JuniperCascor1}"`
>
> `isolated_stack.bash:97: RECURRENCE_BIN=...`

**Correction:** the relevant isolated-stack declaration is lines 44–46, not 43–46; executable declarations are 94–97 (assignment at 96), not 93–97. Experiment-stack lines 67 and 142 are exact.

## Tally

| Verdict | Count |
|---|---:|
| VERIFIED | 4 |
| CONTRADICTED | 4 |
| COULD NOT CHECK | 0 |

## Verdict

The plan is directionally well grounded on installed-state drift, dependency pins, git/tag ordering, parent inventory omissions, and launcher defaults, but it is not current enough to serve as an exact audit record. Run state now contains a 2026-10-03 recurrence × equities replay whose index says succeeded while acceptance failed on `X_full`; recurrence#178 is mischaracterised; PyPI has no recurrence-model 0.3.2; and the isolated-stack line citations are slightly stale.
The instruments cannot establish uninspected source behaviour, causal claims beyond issue/run records, or what an unpublished future release will contain.
