# Round 39, round 2 — Lane A (receipts and source)

**Verdict: PASS WITH CORRECTIONS.**

Observation window 2026-09-16 01:31–01:41 UTC. **juniper-data#404 was OPEN throughout** (created
01:16:18Z, `mergeStateStatus: CLEAN`). Four of the document's claims fail on that single fact; the
rest holds up, and every number in §4/§5 re-derivable from the SEC cache reproduced exactly.

Brief: check every checkable assertion against the real repositories and the real GitHub state,
with a receipt (`path:line`, or the command and its output) for each. Never accept the document's
own wording as evidence for itself.

---

## Claims checked

| Claim | Verdict | Receipt |
|---|---|---|
| §1 `grep -cE '^\| APD-…\| \*\*FIXED'` → 94 | CONFIRMED | output `94` |
| §1 `register_open_set.py` → `119 rows \| 94 fixed \| 25 open` | CONFIRMED | first output line verbatim |
| §1 crosscheck 94/94/94 AGREE | CONFIRMED | `§4 tables : 119 rows, 94 marked **FIXED` / `94` / `94` / `AGREE` |
| §1 33 tests OK (3 register suites) | CONFIRMED | `Ran 33 tests in 0.097s` / `OK` |
| §1 archive test passes | CONFIRMED | `Ran 2 tests` / `OK` |
| §1 relative path `../../../../juniper-data` resolves | CONFIRMED | `ls -d` resolves |
| §1 expect `VERSION = "5.0.0"` on juniper-data `origin/main` | **REFUTED** | `57:VERSION = "4.0.0"` |
| §1 expect `_SHARES_ABSOLUTE_CEILING = 1.0e11` on main | **REFUTED** | `103:… = 1.0e13` |
| §1 expect the `kept_values` loop on main | **REFUTED** | `1112: running_median = …expanding(min_periods=3).median()` |
| Those three DO hold on `origin/fix/equities-head-typo-regression` | CONFIRMED | `59:VERSION = "5.0.0"`, `113:… = 1.0e11`, `1159: kept_values: list[float] = []` |
| §2 juniper-ml#1864 MERGED | CONFIRMED | `2026-09-09T23:52:27Z`, `6ccf80fa` |
| §2 juniper-ml#1898 MERGED | CONFIRMED | `2026-09-11T18:01:40Z`, `dbcde674` |
| §2 juniper-data#395 MERGED `b6ab7c1` | CONFIRMED | `b6ab7c1761f06642706e8152ba027a87145262cc`, `2026-09-12T21:40:43Z` |
| §2/§4/§5.9/§5.10/§8 juniper-data#404 **MERGED** | **REFUTED** | `gh pr view 404` at 01:31 and 01:41 → `{"mergedAt":null,"state":"OPEN"}` |
| §2 changed file `test_equities_seq_generator.py` | **REFUTED** | `git show --name-only b6ab7c1` lists `test_equities_seq_deployment_policy.py`; that file was last touched by #388 |
| §2 the 7 juniper-ml ad-hoc scripts + `2026-09-11_equities_rulings/` (4 files) | CONFIRMED | all present |
| All 28 register ids the doc names EXIST | CONFIRMED | per-id grep; every one matched (lines 761–1246) |
| The 25 open rows are exactly the ones §0 groups | CONFIRMED | OPEN ids ∩ §0 units = 25/25, no orphan, no double-assignment |
| "25 open — 17 primer + 8 post-primer" | CONFIRMED | §4.9 contains 8 of the 25 open ids |
| `APD-RCLIENT-002` closed; `APD-CASCOR-011` FIXED WON'T FIX | CONFIRMED | register:1155, :1236 |
| data-client `client.py:302` `kwargs.setdefault("timeout", self.timeout)` | CONFIRMED | exact |
| cascor-client `client.py:530` `_request` takes no `**kwargs` | CONFIRMED | signature `(self, method, path, json=None, params=None)`; `:544 timeout=self.timeout` |
| recurrence-client `client.py:265-269` per-call override | CONFIRMED | `:265` setdefault, `:269 effective_timeout = kwargs["timeout"]` |
| Three `or settings.*` sites: csv_import ×1, equities ×2 | CONFIRMED | `csv_import:153`, `equities:479`, `:509` (a 4th at `:512` is `incomplete_rows`) |
| `test_request_cannot_opt_out_of_deployment_allow_truncation` exists | CONFIRMED | `test_csv_import_generator.py:727` |
| "A client cannot opt out of the operator's choice" docstring | CONFIRMED (wording inexact) | `equities/generator.py:454-456`: `cannot opt *out* of` |
| counters: `storage/base.py` 4, `postgres_store.py` 2, `core/models.py` | CONFIRMED | base:288,294,309,310; postgres:80,137; models:116-117 |
| `Retry-After` IS sent on the auth-throttle 429 | CONFIRMED | `api/middleware.py:206` inside the `_failed_auth_throttle.check` block |
| "…with two tests asserting it" | **PARTIALLY REFUTED** | Only `test_middleware.py:240` asserts the auth-throttle 429. `test_security_integration.py:138` asserts it on the **rate-limit** 429 (`api/security.py:287`) — a different mechanism |
| APD-DATA-030's correction is in the register | CONFIRMED | register:783 |
| `hmac.compare_digest` in all three; only `any(...)` short-circuits, 2 of 3 | CONFIRMED | cascor `security.py:61`, service-core `security.py:66`; juniper-data `api/security.py:99-103` explicit flag loop |
| §4 AIZ 116,799,796,000 vs 117,926,517 = 990× | CONFIRMED | cache `0001267238.json`; ratio 990.4 |
| §4 EOG 251,931,774,000 vs 587,723,622 = 428× | CONFIRMED | cache `0000821189.json`; ratio 428.7 |
| AIZ typo at position 1, EOG at position 0 | CONFIRMED | filed-sorted lists |
| §0.5 AIZ 1.168e11 = smallest demonstrated typo | CONFIRMED | minimum of all observations >1e11 |
| §0.5 AAPL 1.70e10 = **largest genuine count in the bundled universe** | **REFUTED** | NVIDIA `2.4530e10` and Citigroup `2.9206e10` are larger and genuine |
| §0.5 "18 observations across 24 series between 1e11 and 1e13" | **REFUTED as worded** | `(1e11,1e13]` → 18 across **9**; `>1e11` → 39 across **24** |
| §5.11 / §6 cache holds **486** payloads | CONFIRMED | `wc -l` → 486; remeasure script agrees |
| §6 payloads hand-copied to `…/shares/v2/` | CONFIRMED | 486 files there |
| §5.11 183 restatement CIKs vs comment's 162 | CONFIRMED | script output vs `generator.py:1072` |
| §5.11 42 collisions vs comment's 54 | CONFIRMED | script output vs `generator.py:817` |
| §5.5 PATH breakage FIXED, `pre-commit 4.6.0` runs | CONFIRMED | `which` → JuniperCascor1 shim, shebang `python3.14`, `--version` 4.6.0, mtime `Sep 12 16:44` |
| §5.8 `Juniper/AGENTS.md` is **stale at 5.0.0** | **REFUTED (premature)** | `AGENTS.md:199` says `4.0.0`, and juniper-data `origin/main` IS 4.0.0. It becomes stale only when #404 merges |
| §5.8 `Juniper/` is not a git repository | CONFIRMED | `git rev-parse` → `fatal: not a git repository` |
| §5.9 `test_val_emission_guards.py` asserts major≥3 + allow-list | CONFIRMED | `:290-291` |
| §5.12 three repos carry `-q` in `addopts` | CONFIRMED | data:223, cascor:205, recurrence:159 |
| §5.12 three conda envs; juniper-recurrence has none | CONFIRMED | `ls -d /opt/miniforge3/envs/*` |
| §6 four named worktrees exist | CONFIRMED | all four present |
| §6 branch and "origin/main far ahead" | CONFIRMED | `git rev-list --left-right --count` → `108  0` |
| §7 `reports/2026-09-15_round-39-consensus/` | **REFUTED** | `No such file or directory` |
| §0.2 C-B "43 `Dict[str, Any]` returns" | CONFIRMED | data-client 11 + cascor-client 32 = 43 |
| §0.1 `datasets.py` ~1000 lines | CONFIRMED | 1030 |
| §0.1 D-D `/{dataset_id}` owns the slot; 201 always on create | CONFIRMED | `datasets.py:863`, `:78` |
| APD-DATA-022 "no `responses={}` anywhere" | CONFIRMED | only hit is a comment at `:203` |
| §0.1 D-C "api/app.py's three handlers" | CONFIRMED | `:187`, `:214`, `:238` |
| D-B: no ETag / Content-Location / Link anywhere in `api/` | CONFIRMED | grep returns zero real hits |
| §0.3 X-B `_dataset_shortfall` written once, never cleared | CONFIRMED | init `:1243`; writes `:4175`, `app.py:592`; no reset |
| §0.4 M-A pins inconsistently capped | CONFIRMED | `pyproject.toml:29-32`, `:46-50` uncapped vs `:51-58` capped |

## New finding not in the document

**The register closed `APD-DATA-050` against an unmerged PR** (register:1243), so the headline
`94 fixed / 25 open` depended on a merge that had not happened — and
`tests/test_register_close_protocol.py` passes anyway, because the close protocol does not check PR
state. *(Resolved: #404 merged 2026-09-16T02:08:43Z, squash `1bbb6976`, verified by content on
`main`.)*

## Could not check

- §5.6 (GraphQL rate limit) and §5.7 (`open_signed_pr.py` created a branch then failed the commit
  with HTTP 499) — transient session observations with no durable artifact. The named recovery tool
  exists; the incidents are unreproducible.
- §3's claim that thirty rulings were taken *interactively, in batches of four* — the rulings are in
  the register; the interaction mode leaves no trace.
- §5.1's "measured twice" and §5.3/§5.4's fixture narratives — conclusions consistent with the code,
  but re-running the measurements would require modifying juniper-data, which this lane may not do.
- Whether the ruled rows are implementable as sequenced beyond §0.1's collisions.

## Side observation, raised unverified

Pentair (`0000077360`) carries a max of `9.84e10` against a median of `1.66e8` — a ~600× scale typo
**below** the new 1e11 ceiling. PKG (`8.99e10`), REG (`8.19e10`) and MAA (`7.50e10`) look the same.
Possibly relevant to the `APD-DATA-047` decision; not confirmed as typos rather than a unit change.

*Resolved after the lane: all four are typos, all four are caught by the relative filter (delivered
maxima 2.10e8 / 1.04e8 / 1.85e8 / 1.17e8), and none is reachable by any absolute bound that leaves
Citigroup's genuine 2.92e10 intact. That became the argument for the two-instrument design.*
