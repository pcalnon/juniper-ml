# Requirements Identification Plan

**Author**: Paul Calnon
**Created**: 2026-05-11
**Last updated**: 2026-05-11
**Status**: Plan locked. Execution not yet started.
**Owner**: Paul Calnon (work to be performed by Claude Code agents under supervision)

---

## 1. Goal

Search every notes document across all 8 active Juniper repositories, extract every explicit and (under an aggressive threshold) implicit project / application-level requirement, and consolidate them into a single navigable set of markdown files in `juniper-ml/notes/requirements/` with a top-level index at `juniper-ml/notes/REQUIREMENTS_INDEX.md`.

The output is a **historically-accurate snapshot** of the full requirements picture as of the execution date. Already-shipped requirements are included with `status: shipped`. Each requirement entry must trace back to at least one cited source-document path with line range; hallucinated requirements are the primary risk and the schema enforces traceability.

This is a **v1 snapshot**. Iteration toward a "living document" model is documented as future work in §10.

---

## 2. Scope

### In scope (v1)

- All files under `notes/` in each of the 8 active repos:
  - `juniper-cascor/notes/`
  - `juniper-data/notes/`
  - `juniper-data-client/notes/`
  - `juniper-cascor-client/notes/`
  - `juniper-cascor-worker/notes/`
  - `juniper-canopy/notes/`
  - `juniper-deploy/notes/`
  - `juniper-ml/notes/`
- Both **explicit** requirements (anything formally tagged: "Requirement", "Acceptance Criteria", "Must", "Shall", numbered req lists, structured checklists in plan docs) and **implicit** requirements under an **aggressive** threshold — see §4 for the explicit definition of what aggressive includes.
- Both **open** and **shipped** requirements. The list is intended to capture the full historical picture.

### Out of scope for v1 (deferred to future work — see §10)

- PR descriptions, issue text, GitHub discussions
- Design docs in `docs/` directories
- Code-level docstrings
- Conversation-derived requirements (Slack, email, in-person)
- Living-document refresh mechanisms (CI lint, scheduled re-extraction, author-side tagging conventions)

---

## 3. Locked decisions (questions and answers)

The plan was reviewed and these five questions were resolved 2026-05-11. Re-opening any of them requires a documented decision change here.

### Q1 — How aggressive should "implicit" requirement identification be?

**Question**: Should the extraction be aggressive (every "must/should/will" sentence + every TODO + every threshold/SLO/perf target) or conservative (only structured requirement-like blocks)?

**Answer (locked 2026-05-11)**: **Aggressive.** Capture as much as possible in v1. Noise can be filtered later via the `status` and `category` fields; missed items are harder to recover after the fact.

**Implication**: Phase-3 extraction agents are instructed to err on inclusion. Expect ~500-1000 candidate requirements across the 8 repos before deduplication. Dedup in Phase 4 collapses cross-repo restatements of the same requirement into single entries with multiple source references.

### Q2 — Single monolithic file or multi-file?

**Question**: One big `REQUIREMENTS.md` (~5000-15000 lines) or multi-file (per-repo / per-component / per-domain) with a navigation index?

**Answer (locked 2026-05-11)**: **Multi-file.** Output structure:

```
notes/REQUIREMENTS_INDEX.md             ← navigation entrypoint
notes/requirements/
├── README.md                           ← schema + ID convention reference
├── by-area/
│   ├── observability.md
│   ├── security.md
│   ├── api-contracts.md
│   ├── deployment.md
│   ├── ui-frontend.md
│   ├── data-pipeline.md
│   ├── training.md
│   ├── networking-and-comms.md
│   ├── testing-and-ci.md
│   └── ... (other areas as discovered)
├── by-repo/
│   ├── juniper-cascor.md               ← thin index of JR-CAS-* IDs grouped by area
│   ├── juniper-data.md                 ← JR-DAT-*
│   ├── juniper-canopy.md               ← JR-CAN-*
│   ├── juniper-deploy.md               ← JR-DEP-*
│   ├── juniper-ml.md                   ← JR-ML-*
│   ├── juniper-cascor-worker.md        ← JR-CWK-*
│   ├── juniper-cascor-client.md        ← JR-CCL-*
│   └── juniper-data-client.md          ← JR-DCL-*
└── by-status/
    ├── shipped.md                      ← thin index by status
    ├── in-progress.md
    ├── proposed.md
    ├── deferred.md
    └── ... (other statuses)
```

The **canonical** definition of each requirement lives once in `by-area/<area>.md`. The `by-repo/` and `by-status/` files are thin indexes that link into `by-area/` — not duplicates. This avoids the maintenance trap of three copies of every requirement going stale independently.

### Q3 — Snapshot or living document?

**Question**: Capture state as-of-today, or also wire a refresh path?

**Answer (locked 2026-05-11)**: **Snapshot first.** The eventual need for a living-document model is real and documented in §10 ("Living-document migration plan"). Don't try to do both in v1.

### Q4 — Sources beyond `notes/`?

**Question**: Stick to `notes/` only, or also pull from PR descriptions, design docs, code docstrings, GitHub issues?

**Answer (locked 2026-05-11)**: **`notes/` only for v1.** Explicit out-of-scope sources are listed in §10.2 with the reasoning for each — so anyone reading this doc later understands the boundary was deliberate, not accidental.

### Q5 — Already-shipped requirements: include or filter?

**Question**: Include with `status: shipped` or filter out?

**Answer (locked 2026-05-11)**: **Include with `status: shipped`.** The requirements documents are intended to represent the full, historically-accurate picture of the project. Hiding shipped work loses the audit trail and makes recurring ideas look like new ideas.

---

## 4. Definition of "aggressive implicit requirement identification" (per Q1)

For Phase 3 extraction agents, the following are all treated as candidate requirements:

| Pattern | Example | Treat as | Status default |
|---|---|---|---|
| Explicit "Requirement N: …" or "REQ-N:" headings | "Requirement 4.2: cascor must expose /v1/health/ready" | requirement | based on context |
| Acceptance-criteria checklist items | "- [x] /metrics returns 200 anonymously" | requirement | inferred from checkbox state |
| "Must / shall / should / will / cannot" sentences in a design or plan doc | "Canopy shall not log API keys" | requirement | `proposed` unless context says otherwise |
| Numbered design-decision rationale | "**Decision**: use IP-allowlist on /metrics" | requirement | `shipped` if cited PR is merged |
| TODO items in a roadmap or plan | "TODO: wire OBS-WIRE-02" | requirement | `proposed` |
| Performance / latency / throughput targets | "p95 < 50 ms", "must support 100 RPS" | requirement | `proposed` unless tied to a shipped SLO |
| SLO / SLI definitions | "Availability SLI: 99.5%" | requirement | `shipped` if catalogued |
| Naming/format conventions stated as expectations | "All Helm charts: version and appVersion must match" | requirement | `shipped` if practiced |
| Architectural constraints | "Worker must not import pydantic at runtime" | requirement | `shipped` if test exists |
| Trigger conditions in deferred-design docs | The Option C triggers in CANOPY_DASHBOARD_SELF_CALL_REFACTOR_2026-05-10.md | requirement | `deferred` |
| Compatibility / pin floors stated as deliberate | "juniper-observability >= 0.2.0 floor for register_or_reuse" | requirement | `shipped` |

**Not** treated as requirements:

- Pure historical narrative ("we tried X, it failed, we did Y")
- Status reports / changelogs without a forward-looking ask
- Internal-to-Claude/agent process notes that have no project-level implication

When in doubt under the aggressive threshold, **include**. Deduplication and triage happen in Phase 4.

---

## 5. Per-requirement schema

Every requirement entry in `by-area/*.md` MUST include the following fields. The schema is enforced in Phase 5 QA.

```markdown
### JR-CAS-WS-014 — WebSocket resume buffer occupancy

**Status**: shipped <!-- one of: proposed | designed | in-progress | shipped | deferred | rejected | superseded -->
**Category**: observability  <!-- canonical area; matches a by-area/ file -->
**Owner**: cascor  <!-- canonical owning repo -->
**Brief**: Cascor must expose current and capacity occupancy of the WS replay
buffer as Prometheus gauges so operators can detect resume-storm pressure.

**Sources**:
- juniper-ml/notes/observability/A9_AND_3_2_STATE_ANALYSIS_2026-05-03.md §3.2 (lines 84-118)
- juniper-cascor/notes/METRICS_MONITORING_R5_ENTRY_PLAN_2026-05-02.md §4.1.4 (lines 312-340)

**Detail**: Two `Gauge` collectors named `cascor_ws_replay_buffer_occupancy`
and `cascor_ws_replay_buffer_capacity`. Updated at every replay-buffer mutation
and at one-shot init respectively. Single label set: none (process-wide).
Cardinality budget: 2 series total.

**Design**: Wire at `manager.py:317` (occupancy) and `manager.py:94` (capacity
init) using `juniper_observability.register_or_reuse`. Helper module already
exists; this requirement adds two specific call sites.

**PRs**:
- pcalnon/juniper-cascor#204 — initial wiring of two of nine WS metrics (does NOT include this one)
- OBS-WIRE-02 — proposed PR that would close this; not yet opened

**Notes**: Part of the A.9 audit. See companion JR-CAS-WS-015 ... 022 for the
sibling WS metrics. Removing the `cascor_ws_seq_gap_detected_total` and
`cascor_ws_connections_active` (endpoint label) metrics is tracked under
JR-CAS-WS-021 and JR-CAS-WS-022 respectively.
```

### Field rules

- **`Status`** — required, one of the values in §6.
- **`Category`** — required, must match a `by-area/` filename without `.md`. Add new areas only after Phase-4 dedup; don't invent areas during Phase 3.
- **`Owner`** — required, the canonical owning repo (e.g. `cascor`, `canopy`, `deploy`, `ml`). Cross-repo requirements have one owner; the others appear in `Sources`.
- **`Brief`** — required, 1-2 sentences. Reads as a standalone summary.
- **`Sources`** — required, at least one. Format: `<repo>/<path> §<section> (lines <range>)`. Hallucinated requirements without traceable sources are the main risk; the schema makes them obviously broken.
- **`Detail`** — required for non-trivial entries; may be `(none)` for one-line conventions.
- **`Design`** — optional but recommended; populated when the source doc has a design sketch.
- **`PRs`** — optional; populated when one or more PRs exist that close (or partially close) the requirement.
- **`Notes`** — optional; cross-references to sibling requirements, related deferrals, etc.

---

## 6. ID convention and status taxonomy

### Reference IDs

Format: `JR-<REPO>-<AREA>-<NNN>`

- `JR` — Juniper Requirement (constant prefix)
- `<REPO>` — 3-letter shortcode for the owning repo:
  - `CAS` = juniper-cascor
  - `CAN` = juniper-canopy
  - `DAT` = juniper-data
  - `DEP` = juniper-deploy
  - `ML`  = juniper-ml
  - `CWK` = juniper-cascor-worker
  - `CCL` = juniper-cascor-client
  - `DCL` = juniper-data-client
- `<AREA>` — 2-5 letter area code derived from the canonical category (`OBS` = observability, `SEC` = security, `API` = api-contracts, `DEP` = deployment, `UI` = ui-frontend, `DATA` = data-pipeline, `TRAIN` = training, `WS` = websocket, `TEST` = testing-and-ci, `LOCK` = lockfile-and-deps, etc.)
- `<NNN>` — zero-padded sequential within the (repo, area) namespace, starting at 001

Examples: `JR-CAS-WS-014`, `JR-CAN-METRIC-007`, `JR-DEP-OBS-003`, `JR-ML-LOCK-002`.

IDs are assigned in Phase 4 (after dedup), recorded in `id_assignments.yaml`, and **never reused** even if a requirement is later marked `rejected` or `superseded`. A `superseded` entry retains its ID and links forward to its replacement.

### Status taxonomy

| Status | Meaning |
|---|---|
| `proposed` | Identified in a notes doc but no design or implementation work has begun. |
| `designed` | A design doc exists but no implementation work has begun. |
| `in-progress` | One or more PRs are open / in active development. |
| `shipped` | Closed by one or more merged PRs; the requirement is satisfied in the current main branch of all owning repos. |
| `deferred` | Explicitly deferred with conditions for future activation (e.g. trigger criteria documented). |
| `rejected` | Explicitly decided against; retained for historical traceability. |
| `superseded` | Replaced by another requirement; the entry stays with a forward link to the replacement's ID. |

---

## 7. Phased execution plan

| Phase | Description | Approx wall-clock | Status |
|---|---|---|---|
| 0 | Plan written, decisions locked | done | ✅ 2026-05-11 |
| 1 | Inventory all `notes/` directories across the 8 repos | 15-30 min, 1 Explore agent | ☐ not started |
| 2 | Schema lock (already drafted in §5; re-confirm after Phase 1 size estimate) | 10 min, deterministic | ☐ not started |
| 3 | Per-repo extraction, parallel | 1-3 h wall, 8 Explore agents in parallel | ☐ not started |
| 4 | Consolidation, dedup, ID assignment, area-grouping | 30-60 min, sequential | ☐ not started |
| 5 | QA pass: random N=20 verification + coverage spot-check | 30 min, 1 Explore agent + supervisor | ☐ not started |
| 6 | Ship: commit `notes/REQUIREMENTS_INDEX.md` + `notes/requirements/*.md` to juniper-ml main | 10 min | ☐ not started |

**Pilot recommendation (still in force)**: run all phases against `juniper-ml/notes/` only first (~1 hour total), recalibrate the aggressive-threshold and schema based on what surfaces, then fan out Phase 3 to the other 7 repos. The pilot output is **disposable** — Phase 3 will re-extract `juniper-ml` from scratch in the full-fan-out run.

### Phase detail

#### Phase 1 — Inventory

- One Explore agent runs `find notes/ -type f \( -name '*.md' -o -name '*.txt' \)` across all 8 repos.
- For each file: capture path, LOC, last-modified date, first-line summary.
- Identify the ~10-20 most "requirement-dense" files (roadmaps, plan docs, design proposals) — these will dominate Phase 3 effort.
- Output: `/tmp/notes_inventory_2026-05-11.md` (single index file consumed by Phase 3 agents).

#### Phase 2 — Schema lock

- Re-confirm §5 schema after Phase 1 size estimate. If Phase 1 surfaces > 1500 candidate requirements, may add a `priority` field; otherwise leave schema as-is.
- Pin the area-code list (the `<AREA>` part of the ID convention). Phase 3 agents must NOT invent new area codes; they pick from the pinned list or use `MISC` and let Phase 4 reclassify.

#### Phase 3 — Per-repo extraction (parallel)

- One Explore agent per repo (8 agents). Each agent gets:
  - The full schema from §5
  - The aggressive-threshold definition from §4
  - The pinned area-code list from Phase 2
  - The Phase-1 inventory entries for its repo
- Output per agent: a YAML file at `/tmp/req_extract_<repo>_2026-05-11.yaml`. Each entry contains all schema fields **except** the final ID (assigned in Phase 4 after dedup).
- Hard rule: every entry MUST cite at least one source-doc path with line range. Entries failing this rule are dropped in Phase 4 dedup.

#### Phase 4 — Consolidation

- Merge the 8 YAML files.
- Dedup pass: cross-repo restatements of the same requirement collapse to a single entry with multiple `Sources`. Heuristic: same `Brief` (after fuzzy match) + same `Category` + overlapping language → merge candidate, surface for human review.
- ID assignment: walk the merged set in deterministic order (alphabetic by Brief), assign `JR-<REPO>-<AREA>-<NNN>` IDs, persist to `id_assignments.yaml`.
- Generate the markdown:
  - `notes/requirements/by-area/*.md` (canonical entries)
  - `notes/requirements/by-repo/*.md` (thin indexes linking to by-area)
  - `notes/requirements/by-status/*.md` (thin indexes linking to by-area)
  - `notes/REQUIREMENTS_INDEX.md` (navigation entrypoint with stats)
- Validate: every `Source` path resolves on disk; every PR reference resolves on GitHub.

#### Phase 5 — QA

- Pick N=20 requirements at random. One Explore agent re-verifies each against its cited source doc, confirming:
  - The requirement is actually stated in the source (not invented)
  - The `Brief` faithfully summarises the source
  - The `Status` matches what the source/PR state says
- Coverage check: pick 5 notes files that should have produced requirements but appear in few/no `Sources`. Re-extract just those with a fresh agent. Surface anything missed.
- Findings → either iterate Phase 3-4 partial re-runs, or accept and ship.

#### Phase 6 — Ship

- Commit to the cached-whistling-flute worktree.
- Push branch to origin.
- Stash any in-progress edits in juniper-ml main worktree (recurring pattern this session — see relevant memory entries).
- Local-merge to main with `--no-ff`, push main.
- Restore the stash.
- Update §11 progress tracker with completion timestamp.

---

## 8. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hallucinated requirements (extracted but no traceable source) | medium | high (corrupts the artifact's audit value) | Schema mandates at least one `Source` with line range. Phase 5 QA sample of N=20 catches a meaningful fraction. |
| ID collisions / shifting IDs on re-runs | medium | medium (breaks external links) | Persist `id_assignments.yaml`. Future re-runs reuse IDs for matched entries. Never reuse a retired ID. |
| Aggressive threshold produces overwhelming volume (>1500 entries) | medium | medium (output unreviewable) | Phase 1 inventory sizes the corpus before Phase 3 commits. If Phase 1 forecasts > 1500 entries, Phase 2 adds a `priority` field and Phase 4 surfaces a `priority: high` view. |
| Cross-repo restatements miss dedup (same requirement, two entries) | high | low (cosmetic; can be re-merged later) | Phase 4 fuzzy-match dedup with human review of the merge candidates. |
| Aggressive scope misses an explicit requirement (false negative) | low-medium | medium | Phase 5 coverage check on 5 high-density files catches obvious misses. |
| In-progress edits in main worktree get clobbered during Phase 6 commit | medium (already happened twice this session) | low (stash recovers) | Standard stash + merge + pop pattern, documented in `project_juniper_ml_concurrent_session_activity.md`. |
| Phase 3 agent token cost exceeds expectations | medium | low | Run pilot on juniper-ml first (~1 hour, single-repo cost); use that to project full-fan-out cost before committing. |

---

## 9. Effort estimate

| Phase | Wall-clock | Notes |
|---|---|---|
| 1 — Inventory | 15-30 min | Mostly `find` + `wc` operations, single agent. |
| 2 — Schema lock | 10 min | Deterministic, mostly already done in §5. |
| 3 — Extraction (full fan-out) | 1-3 hours wall | 8 agents in parallel. Token cost is the dominant resource here. |
| 3 — Extraction (juniper-ml pilot only) | ~1 hour | Single agent against the densest repo. |
| 4 — Consolidation | 30-60 min | Sequential, agent-assisted but supervisor-driven. |
| 5 — QA | 30 min | One agent + spot-check. |
| 6 — Ship | 10 min | Standard commit-push-merge flow. |
| **Total (pilot only)** | **~2-2.5 hours** | Recommended starting point. |
| **Total (full fan-out)** | **~3-5 hours** | After pilot validates the approach. |

---

## 10. Future work (deferred, with rationale)

Per Q3 (snapshot first) and Q4 (notes/ only for v1), the following are explicitly deferred. Each entry includes the conditions under which it should be promoted to active work.

### 10.1 Living-document refresh

**What**: Convert this from a periodic snapshot into a continuously-maintained artifact that stays in sync with notes/ as new requirements are written or status changes.

**Why deferred**: A living model requires every notes-doc author to follow a tagging convention (e.g. `<!-- req: ID -->` markers, or a structured frontmatter block). Adoption is a separate culture change, and trying to do both v1 capture and v1 living-doc tooling at once dilutes both.

**Promote when**:
- The v1 snapshot has been used for at least one project planning cycle and the value is confirmed.
- A tagging convention has been proposed and adopted.
- A CI lint exists that fails when a new notes file mentions a requirement-shaped phrase without a tag.

**Sketch**:
- Notes-doc authors annotate requirements inline: `<!-- req: JR-CAS-WS-014 status:in-progress -->`
- A scheduled (or PR-triggered) extractor reads these tags + any new untagged candidates, regenerates `notes/requirements/`, and opens a PR with the diff.
- The CI lint catches new requirement-shaped content that wasn't tagged.

### 10.2 Sources beyond notes/

The following sources contain real requirement-shaped content but are deferred from v1.

| Source | Why deferred | Promote when |
|---|---|---|
| **PR descriptions** | Rich requirement context, but volume is large and history is fragmentary. Triples Phase-3 scope. | After v1 surfaces the highest-value PRs that the notes/ extraction *cited*, focus a follow-up pass only on those PR descriptions. |
| **`docs/` directories** | Polished user-facing docs sometimes encode requirements implicitly ("the API supports X"). Different style, requires separate extraction prompt tuning. | After v1 ships and we have a stable extraction-prompt template that can be adapted. |
| **GitHub issues** | High signal for `proposed` status entries, but tracking issue lifecycle (open/closed/superseded) is a separate state machine. | When the project adopts a more structured issue-template that includes a `JR-` ID field. |
| **Code-level docstrings** | Mostly describe what code does, not what it should do. Lower yield. | Probably never as a primary source; useful as a cross-reference during QA. |
| **Conversation-derived (Slack, email, in-person)** | Not searchable in a structured way. | When/if the team adopts a "decision-of-record" practice (e.g. ADRs) that captures conversational outcomes in notes/. |

### 10.3 Priority field

If Phase 1 forecasts > 1500 candidate requirements, add a `priority` field to the schema (P0 = ship-blocking, P1 = next-cycle, P2 = backlog, P3 = nice-to-have). Defer until Phase-1 numbers are in.

### 10.4 Cross-repo dependency graph

Some requirements depend on others (e.g. canopy's "use juniper-observability register_or_reuse" depends on juniper-observability's "ship register_or_reuse helper"). v1 captures both as independent entries with a `Notes` cross-reference. A proper dependency-graph view (DOT/Mermaid) is deferred.

---

## 11. Progress tracker

This section is the canonical record of where the effort stands. Update at each phase boundary.

### Phase status

| Phase | Status | Started | Completed | Output | Notes |
|---|---|---|---|---|---|
| 0 — Plan | ✅ done | 2026-05-11 | 2026-05-11 | This document | Decisions locked per §3 |
| 1 — Inventory | ☐ not started | — | — | `/tmp/notes_inventory_2026-05-11.md` | — |
| 2 — Schema lock | ☐ not started | — | — | (this doc, updated) | — |
| 3 — Extraction (pilot: juniper-ml) | ☐ not started | — | — | `/tmp/req_extract_juniper-ml_2026-05-11.yaml` | Pilot first per §7 recommendation |
| 3 — Extraction (full fan-out, other 7 repos) | ☐ not started | — | — | `/tmp/req_extract_<repo>_2026-05-11.yaml` x7 | Gated on pilot acceptance |
| 4 — Consolidation | ☐ not started | — | — | `notes/requirements/**`, `notes/REQUIREMENTS_INDEX.md`, `id_assignments.yaml` | — |
| 5 — QA | ☐ not started | — | — | (findings appended below) | — |
| 6 — Ship | ☐ not started | — | — | merged to juniper-ml main | — |

### Decisions made during execution

(append entries here as work proceeds)

| Date | Decision | Rationale | Phase |
|---|---|---|---|
| 2026-05-11 | All five plan-locking questions answered (see §3) | Reviewed by owner | 0 |

### Phase-1 inventory results (to be filled in)

| Repo | notes file count | total LOC | density-ranked top files |
|---|---|---|---|
| juniper-cascor | — | — | — |
| juniper-data | — | — | — |
| juniper-data-client | — | — | — |
| juniper-cascor-client | — | — | — |
| juniper-cascor-worker | — | — | — |
| juniper-canopy | — | — | — |
| juniper-deploy | — | — | — |
| juniper-ml | — | — | — |
| **Total** | — | — | — |

### Phase-3 extraction yields (to be filled in)

| Repo | candidate requirements (pre-dedup) | dropped (no source) | net contributed to v1 |
|---|---|---|---|
| juniper-cascor | — | — | — |
| juniper-data | — | — | — |
| juniper-data-client | — | — | — |
| juniper-cascor-client | — | — | — |
| juniper-cascor-worker | — | — | — |
| juniper-canopy | — | — | — |
| juniper-deploy | — | — | — |
| juniper-ml | — | — | — |
| **Total** | — | — | — |

### Phase-5 QA findings (to be filled in)

| QA sample # | ID | Verdict | Notes |
|---|---|---|---|
| 1-20 | — | — | (random sample for hallucination check) |
| Coverage 1-5 | — | — | (high-density files re-checked for misses) |

### Phase-6 ship record (to be filled in)

| Item | Value |
|---|---|
| PR / merge commit | — |
| Files added | — |
| Files modified | — |
| Total requirements published | — |
| Date shipped | — |

---

## 12. Open issues / questions discovered during execution

(append as they arise; resolve before Phase 6 ships)

(none yet)
