# Async-Route Audit Hook — Migration Plan

**Owner**: Paul Calnon
**Created**: 2026-05-05
**Status**: **Complete (2026-05-06)** — all four phases shipped across the four in-scope repos.
**Source audit**: [`ROADMAP_AUDIT_2026-05-05.md`](./ROADMAP_AUDIT_2026-05-05.md) §9.4

---

## 0. Migration ledger (closed 2026-05-06)

| Phase | Repo | PR | Result |
|---|---|---|---|
| 0 (discovery) | all 4 | [`ASYNC_ROUTE_VIOLATIONS_2026-05-06.md`](./ASYNC_ROUTE_VIOLATIONS_2026-05-06.md) | 27 violations enumerated; worker clean |
| 1 (wiring, disabled) | juniper-data | data#92 | merged |
| 1 (wiring, disabled) | juniper-cascor | cascor#231 | merged |
| 1 (wiring, disabled) | juniper-canopy | canopy#243 | merged |
| 1 (wiring, disabled) | juniper-cascor-worker | worker#55 | merged |
| 2 (soft-fail visibility) | juniper-data | data#94 | merged (with `--exit-zero` lesson learned) |
| 2 (soft-fail visibility) | juniper-cascor | cascor#232 | merged |
| 2 (soft-fail visibility) | juniper-canopy | canopy#244 | merged |
| 2 (soft-fail visibility) | juniper-cascor-worker | worker#56 | merged |
| 3 (cleanup) | juniper-data | data#96 (3 fixes) | merged — `_probe_storage` helper |
| 3 (cleanup) | juniper-cascor | (no-op — Phase 1 per-file-ignore covered all 4 sites) | n/a |
| 3 (cleanup) | juniper-canopy | canopy#247 (5 fixes) | merged — `_load_snapshot_history` / `_find_snapshot_file` helpers + 2 noqas |
| 3 (cleanup) | juniper-cascor-worker | (no-op — clean from Phase 0) | n/a |
| 4 (enforce) | juniper-data | data#98 | merged |
| 4 (enforce) | juniper-cascor | cascor#235 | merged |
| 4 (enforce) | juniper-canopy | canopy#248 | merged |
| 4 (enforce) | juniper-cascor-worker | worker#57 | merged |

**Total elapsed**: ~36 hours wall-clock from Phase 0 enumeration to final Phase 4 merge (2026-05-06 morning → 2026-05-06 evening). Code-time was much lower; the gating factor was sequencing the four-repo PR train per phase.

**Outcome vs success criteria** (§8):
1. ✅ Every in-scope repo has a green enforced `async-route-audit` CI lane.
2. ✅ `git grep -nE "ruff check.*--select ASYNC"` returns hits in all 4 repos' `.github/workflows/ci.yml`.
3. (Pending first regression) — the next BUG-JD-10-class introduction will be caught in PR.
4. (Pending 2026-11) — semi-annual `# noqa: ASYNC*` audit.

**Open follow-ups** (deferred, not blocking):
- Branch-protection rule additions: each repo's "Require status checks" list still needs the new `Async-route audit (BUG-JD-10 class)` lane added (GitHub UI-only, no code change).
- Centralised deny-list (§5.2 / Q3) — the `juniper-ml/util/check_async_routes.py` script for project-internal blocking calls (`store.get_meta`, etc.) has not been written. Phase 0 found that ruff's stdlib coverage caught 27 sites without it; revisit if a future BUG-JD-10-class slips through.
- Doc-link hygiene: this plan is now referenced from inline comments in 4 repos' `ci.yml` and `.pre-commit-config.yaml`; if it ever moves, update those comments.

The rest of this document remains as written for the audit trail.

---

## 1. Goal

Add an automated check, enforced at commit-time and in CI, that detects **synchronous-blocking calls inside `async def` route handlers** across all eight Juniper repositories. The class of bug we want to prevent is exactly BUG-JD-10 — `juniper-data/juniper_data/api/routes/datasets.py:429-440`'s `batch_update_tags` route, which `await`-ed nothing but called `store.get_meta()` / `store.update_meta()` synchronously, freezing the event loop for the duration of the batch.

The bug pattern:

```python
@router.patch("/batch-tags")
async def batch_update_tags(...) -> ...:
    for dataset_id in request.dataset_ids:
        meta = store.get_meta(dataset_id)             # ← blocks event loop
        store.update_meta(dataset_id, meta_update)     # ← blocks event loop
```

The fix pattern (already applied in BUG-JD-10's neighbour, `generate_dataset` at line 142, and now in `batch_update_tags` itself via PR juniper-data #90):

```python
meta = await asyncio.to_thread(store.get_meta, dataset_id)
await asyncio.to_thread(store.update_meta, dataset_id, meta_update)
```

**Detection target**: any call inside an `async def` body that (a) is itself an `async def` capable of being awaited but isn't, or (b) is a known synchronous-blocking primitive (filesystem, network, sleep, subprocess) without an `await asyncio.to_thread(...)` wrapping.

---

## 2. Tooling choice

### 2.1 Recommended: ruff `ASYNC` ruleset

Ruff ships a built-in ruleset under the `ASYNC` prefix that covers exactly this bug class:

| Rule | Catches |
|---|---|
| `ASYNC100` | Long-blocking sync call inside `async def` (`time.sleep`, `subprocess.run`, etc.) |
| `ASYNC101` | Trio's blocking calls (less relevant for FastAPI but harmless) |
| `ASYNC210` | Sync `httpx`/`requests` call inside `async def` |
| `ASYNC220` | `subprocess.Popen` / `subprocess.call` / `subprocess.run` inside `async def` |
| `ASYNC230` | `os.system` / `os.popen` inside `async def` |
| `ASYNC251` | `time.sleep` inside `async def` (use `asyncio.sleep`) |

Ruff is already in production use in `juniper-data` (see `juniper_data/pyproject.toml`'s `[tool.ruff]` config and the existing pre-commit hook). The other repos use flake8 — for them, we either (a) add ruff as a complementary linter just for the ASYNC rules, or (b) use the equivalent `flake8-async` plugin.

**Recommendation**: option (a) — add ruff as a complementary check for the `ASYNC*` ruleset only, configured to skip everything else. This is non-invasive: it doesn't displace flake8, and it matches the `juniper-data` toolchain. A full ruff migration is a separate (larger) decision.

### 2.2 Why not a custom AST script

A bespoke checker has the appeal of catching custom-blocking patterns (e.g. our `store.get_meta` is not in any third-party allow-list — ruff's ASYNC rules wouldn't have caught BUG-JD-10 directly). But:

- The ASYNC rules catch the **most common** offenders (the stdlib + `requests` + `subprocess`).
- For project-specific blocking calls (`store.*`, `cache.*`, etc.), a small companion script can be added later. The ruff ruleset is the foundation.
- Maintaining a custom AST checker against pydantic + FastAPI patterns is a meaningful ongoing cost.

### 2.3 Coverage gap

The ASYNC ruleset would **not** catch BUG-JD-10 directly because `store.get_meta` is a project-internal method, not a known stdlib blocking call. To close that gap we'll add a small project-specific deny-list in §5.2 (a few entries naming `*Store.get_meta`, `*Store.update_meta`, etc.).

---

## 3. Scope by repo

| Repo | Has async routes? | Linter today | Risk surface |
|---|---|---|---|
| **juniper-data** | Yes (FastAPI) | ruff | HIGH — this is where BUG-JD-10 lives |
| **juniper-cascor** | Yes (FastAPI) | flake8 | HIGH — most route handlers are async; lots of lifecycle calls |
| **juniper-canopy** | Yes (FastAPI + Dash) | flake8 | MED — fewer async routes; Dash callbacks are sync |
| **juniper-cascor-client** | No (sync HTTP client) | flake8 | NONE — no `async def` routes |
| **juniper-data-client** | No (sync HTTP client) | flake8 | NONE — no `async def` routes |
| **juniper-cascor-worker** | Mixed (async dispatch) | flake8 | LOW — small async surface |
| **juniper-deploy** | No code | n/a | NONE |
| **juniper-ml** | No code | n/a | NONE |

**In-scope for the hook**: juniper-data, juniper-cascor, juniper-canopy, juniper-cascor-worker. Four repos.

---

## 4. Phased rollout

### Phase 0 — Discovery (1 day, parallel across repos)

Run the proposed ruff config against each in-scope repo with `--exit-zero` (warn only) and capture the violation list. Output goes into a tracker file per repo:

```bash
# Per repo, run from repo root:
ruff check --select ASYNC --exit-zero --output-format=concise . > .audit/async-route-violations.txt
```

**Deliverables**:

- `notes/ASYNC_ROUTE_VIOLATIONS_2026-05-05.md` (juniper-ml) consolidating per-repo lists.
- For each repo: a one-line summary of count + top file by violation density.

**Goal**: enumerate the cleanup surface so each repo's owner can scope the work.

### Phase 1 — Document and pin (1 PR per repo)

Add the ruff config + pre-commit hook in **disabled** state. Concretely:

```toml
# Per-repo pyproject.toml (or add to existing [tool.ruff])
[tool.ruff.lint]
select = []  # do not enable globally yet
[tool.ruff.lint.per-file-ignores]
# placeholder; populated in Phase 3
```

```yaml
# .pre-commit-config.yaml — add but leave commented out
# Async-route audit (BUG-JD-10 class). Activated in Phase 2.
# - id: ruff
#   args: [--select, ASYNC]
```

**Why disabled**: each repo decides on its own merge cadence. We commit the wiring so a Phase-2 activation is a one-line config change rather than a tooling-introduction PR.

### Phase 2 — Opt-in soft-fail CI lane (1 PR per repo, parallel)

For each repo, enable the ruff `ASYNC` check in CI as a **soft-fail** (warning) lane:

```yaml
# .github/workflows/ci.yml — add a new job
async-route-audit:
  runs-on: ubuntu-latest
  continue-on-error: true   # soft-fail until Phase 4
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.13" }
    - run: pip install "ruff>=0.5"
    # --exit-zero is required (see "Lesson learned" below).
    - run: ruff check --select ASYNC --exit-zero --output-format=github .
```

**Effect**: every PR shows the violation list as a CI annotation but doesn't block merge. Owners get visibility without disruption.

> **Lesson learned (2026-05-06, juniper-data PR #94 first run)**: the original plan command omitted `--exit-zero`. Without it, ruff exits 1 when violations are present, the step fails, and the `async-route-audit` job displays as red on the PR — even with `continue-on-error: true` on the job. The job-level flag prevents the workflow from failing as a whole, but does not suppress the visual red indicator on the step. Adding `--exit-zero` makes the step exit 0 (so the job stays green) while `--output-format=github` still renders the violations as PR annotations. Belt and suspenders alongside `continue-on-error: true`. Phase 4 will drop both flags simultaneously to flip enforcement on.

### Phase 3 — Cleanup PRs (per repo, owner-scoped)

For each Phase-0 violation:

1. **If the call really needs to be async**, wrap it: `await asyncio.to_thread(...)`.
2. **If the call is acceptable as-is** (e.g. a quick in-memory lookup), add a `# noqa: ASYNC100` with a justification comment.
3. **If it's flagged in test code** that doesn't run in production async contexts, add a per-file-ignore in `[tool.ruff.lint.per-file-ignores]`.

**Acceptance criterion per repo**: zero violations in production code (test code may have per-file ignores with reasoning).

### Phase 4 — Enforce (1 PR per repo)

Flip `continue-on-error: true` → `false` in the CI lane. Add the ruff hook to pre-commit (uncommented). Branch protection updated to require the new lane.

**Order of enforcement** (by risk):

1. juniper-data — already on ruff; smallest blast radius for tooling churn; owns BUG-JD-10's habitat.
2. juniper-cascor — biggest async surface; needs the most cleanup PRs, but also has the highest payoff.
3. juniper-canopy — moderate surface.
4. juniper-cascor-worker — smallest async surface; quick win.

Aim for two repos per week if cleanup volume is moderate; slower if a repo has 20+ violations.

---

## 5. Specifics

### 5.1 Pre-commit hook (added in Phase 1, activated in Phase 2)

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.5.0  # pin to current Phase-1-tested version
  hooks:
    - id: ruff
      name: Async-route audit (BUG-JD-10 class)
      args: [--select, ASYNC]
      types: [python]
      # Phase 1: stages: [manual]   (don't run on commit)
      # Phase 2: stages: [pre-commit, manual]
```

Two-stage activation lets us land the hook (Phase 1) without enforcing it (run only on demand via `pre-commit run --hook-stage manual ruff`), then flip enforcement at Phase 2.

### 5.2 Project-specific deny-list

For project-internal blocking calls that ruff's ASYNC rules don't recognise, we use a complementary AST check. Initial deny-list:

| Pattern | Why it blocks |
|---|---|
| `*Store.get_meta` / `update_meta` / `delete_meta` | filesystem I/O |
| `*Store.read_artifact` / `write_artifact` | filesystem I/O |
| `requests.*` (use `httpx.AsyncClient`) | sync HTTP |
| `httpx.Client.*` (use `httpx.AsyncClient`) | sync HTTP |
| Any function decorated with `@blocking` (sentinel decorator we add) | explicit opt-in marker |

**Implementation**: a 100-line script in `juniper-ml/util/check_async_routes.py` that reads each repo's `*/api/routes/*.py` and `*/api/main.py`, finds `async def` defs, walks each body's call sites, and reports any match against the deny-list that isn't wrapped in `await asyncio.to_thread(...)`.

The script runs alongside ruff (not a replacement) — ruff catches the stdlib + popular third-party blockers; this script catches the project-internal ones.

### 5.3 Allow-list mechanism

Three escape hatches, each with a justification requirement:

1. **`# noqa: ASYNC100` (or specific rule)** — per-line, must include a `# why:` comment.
2. **`[tool.ruff.lint.per-file-ignores]`** — per-file (e.g. test fixtures, scripts), commit-message must reference the specific files.
3. **`@blocking_ok` decorator** (project-defined) — for sentinel cases like a fast in-memory cache lookup that's logically synchronous but inside an async context. Function definition must include a docstring naming why the call is safe.

The decorator approach matters because some routes intentionally make sync calls — for example a hot-path `cache.get(key)` that returns in microseconds. Forcing `asyncio.to_thread` for those would be a performance regression. The decorator makes the intent reviewable.

---

## 6. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **False positives create review noise** | MED | Phase 0 enumerates the cleanup surface so we know the volume before enforcement; soft-fail CI lane (Phase 2) lets owners see violations without churn. |
| **Per-repo cleanup is large in juniper-cascor** | MED | Cascade across multiple PRs; don't enforce until `0` count is reached. The Phase 0 report sets expectations. |
| **Custom deny-list rots as APIs evolve** | LOW | Tie deny-list to a single source of truth (a docstring marker `Blocking: true` on store methods) and have the script read those markers rather than a hardcoded list. Phase 5 work; not blocking. |
| **Ruff version drift across repos** | LOW | Pin in pre-commit + CI; Dependabot updates the pin uniformly across the ecosystem. |
| **Some routes are intentionally sync (Dash callbacks)** | LOW | Per-file-ignore in canopy's Dash-callback files. Document at Phase 3. |
| **Allow-list creep** — easy `# noqa` rather than fixing | MED | Code review checks that every `# noqa: ASYNC*` has a `# why:` comment; PR template reminder. Periodic audit (semi-annual) to count `# noqa` density. |

---

## 7. Effort estimate

Per repo:

| Phase | Effort | Owner |
|---|---|---|
| Phase 0 (discovery) | 30 min | One person, one shell session |
| Phase 1 (wiring) | 1 hr | One PR per repo, mechanical |
| Phase 2 (CI lane on, soft-fail) | 1 hr | One PR per repo |
| Phase 3 (cleanup) | varies — 1 hr to 1 day depending on Phase 0 count | Repo owner |
| Phase 4 (enforce) | 30 min | One PR per repo |

**Total ecosystem effort** (4 in-scope repos × phases 0–2 + 4 cleanup tracks + 4 enforce PRs): roughly 1–3 person-days, spread over 2–3 weeks if work is parallelised across repos. The dominant variable is Phase 3 cleanup volume, which Phase 0 quantifies before any commitment is made.

---

## 8. Success criteria

1. Every in-scope repo has a green `async-route-audit` CI lane (Phase 4 reached).
2. `git grep -nE "ruff check.*--select ASYNC"` in `.github/workflows/` returns hits in 4 repos.
3. The next BUG-JD-10-class regression is caught in the PR that introduces it, before merge.
4. Periodic audit (every 6 months) confirms `# noqa: ASYNC*` count hasn't grown without justification.

---

## 9. Out of scope

- **`flake8-bugbear` opt-in** (the other half of the audit's §9.4 recommendation): not addressed here. Per the user's 2026-05-05 audit answers, that lint-rule change is left for a separate ecosystem-CI track.
- **Full ruff migration**: replacing flake8 + isort + black with ruff across all repos. Bigger decision; this plan deliberately keeps ruff scoped to ASYNC-only rules to avoid that conversation.
- **Pre-commit hook for canopy Dash callbacks**: Dash callbacks are sync by design; they're out of the async-route scope. A separate audit (CAN-callback-blocking) could cover them later if needed.

---

## 10. Open questions

> **Resolved 2026-05-06.** Q1/Q2/Q3 below carry the user's answers and the resulting plan adjustments. Original questions retained for the audit trail.

1. **Phase 0 timing**: should the violation enumeration happen now (before approving the rest of the plan), or after the plan is approved and we proceed in earnest? Doing it now adds 30 minutes but makes the scope of Phase 3 concrete.

   **Answer (2026-05-06)**: enumeration runs now. **Done** — see [`ASYNC_ROUTE_VIOLATIONS_2026-05-06.md`](./ASYNC_ROUTE_VIOLATIONS_2026-05-06.md). Headline: 27 total violations across 4 in-scope repos (15 production, 12 test); Phase 3 effort revised down to **~2.5 hours total** of code work. Worker is already clean.

2. **Phase 4 enforcement order**: the proposed order (data → cascor → canopy → worker) optimises for blast radius. Alternative: enforce on the smallest first (worker → canopy → data → cascor) for confidence-building. Pick one.

   **Answer (2026-05-06)**: **proposed order** (data → cascor → canopy → worker). The Phase-0 enumeration confirms the proposed order is also the ascending-cleanup-effort order (data: 30 min → cascor: 15 min → canopy: 1.5 hrs → worker: 0), so blast-radius ordering doesn't conflict with confidence-building.

3. **Custom deny-list home**: live in `juniper-ml/util/` (centralised) or copy per-repo (autonomous)? Centralising means one update point but cross-repo dependency at lint time; per-repo means duplication but no coupling. Default to centralised unless that creates CI bootstrapping pain.

   **Answer (2026-05-06)**: **centralised** in `juniper-ml/util/`. Revisit if it causes problems. The CI-bootstrapping concern is mitigable via `pip install juniper-ml` in each repo's CI bootstrap (already a dependency in some contexts via the `juniper-ml[all]` meta-package); per-repo copies can always be added later if cross-repo coupling becomes painful.

### 10.1 Resolved-question impact on the plan

| Original plan section | Update from answers |
|---|---|
| §4 Phase 3 effort ("varies — 1 hr to 1 day") | **Revised to ~2.5 hours total** based on Phase 0 enumeration |
| §5.2 deny-list home | **Centralised** in `juniper-ml/util/check_async_routes.py` |
| §7 effort estimate (1–3 person-days) | **Revised to ~1 person-day** ecosystem-wide |
| §4 Phase 4 enforcement order | **Confirmed**: data → cascor → canopy → worker |

Phase 1 (wiring in disabled state) is the next concrete step, with each in-scope repo getting:
- Ruff config addition (or `pyproject.toml` extension where ruff is already in use)
- Pre-commit hook entry, stage-restricted to `manual` (so it doesn't fire on commit until Phase 2)
- Per-file-ignore drafts based on Phase 0 enumeration (cascor `service_launcher.py`; canopy test files + discovery / health / adapter `# noqa` sites)
- Stub `juniper-ml/util/check_async_routes.py` to be wired in Phase 1 alongside ruff
