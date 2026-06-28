# Juniper Custom-Agent Suite — Enhancement Plan

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-06-27

**Document Type**: PLAN
**Status**: AWAITING OWNER APPROVAL

> Grounding pin: HEAD `79a9eda` (branch `worktree-ticklish-giggling-truffle`), working tree clean apart from this
> untracked plan document (the sole dirty item — a fresh discovery bundle accordingly reports `dirty:true`). Every
> `file:line` / symbol / flag / version / path below was re-confirmed first-party against the running code in
> this worktree (`.claude/worktrees/ticklish-giggling-truffle`) and sibling repos under
> `/home/pcalnon/Development/python/Juniper/` while authoring this plan. Nothing here is taken on trust from a
> prior document without re-probe. The Phase-2 reconciliation (3 independent value/risk/feasibility lenses) is
> the authoritative scoping decision; this plan operationalizes it and does **not** re-open the prioritization.
> This is **iteration 2**: revised after a 4-lens independent validation pass (recorded in §10).

---

## 1. Executive Summary

The Juniper custom-agent suite (4 opus+max subagents, the `/template-agent` Skill, a 10-template library, a
5-file data layer, a 7-probe discovery CLI, and ~20 `tests/` gates) is **feature-complete and healthy**: the
suite doctor reports 6 OK / 1 WARN (the lone WARN is the optional `~/.claude` mirror, absent in this worktree)
and the discovery bundle is clean on HEAD. Three rounds of dogfooding (a canopy runtime-breakage debug prompt,
an ecosystem test-suite audit prompt, and the dogfooding of *this very* enhancement prompt) surfaced a small,
**validated** set of gaps and enhancement opportunities — none of which is a defect in shipped behavior, and all
of which target one recurring blind spot: **"green tests / dead app"** failure classes that the suite, being
entirely static / read-only / single-task by construction, cannot see today.

This plan accepts and sequences the reconciliation's ranked enhancement set:

- **Phase 1 (near-term core, the proposed approved scope)** — four mutually-independent, low-risk units: **D-1**
  (test_status cache-freshness guard), **E-2** (environment floor-drift checker — the actual canopy-incident
  fix), **E-5** (mocked-seam gap auditor — a new read-only `auditor` variant), and **E-3** (first-class
  cross-repo `--target-repo` mode). **G-3** (the stale `AGENTS.md` tree) rides Phase-1 on PR-2 — now as a
  **gated** rider (it ships a new tree-drift guard, not a bare doc edit). The value lens framed this as a
  **static triad (E-2 + E-5 + D-1) that *detects and diagnoses* "green tests / dead app" without runtime risk,
  plus E-3 as the cross-repo unlock** that makes the whole suite first-class for the common case (sibling-repo
  targets).
- **The true-catch / prevention layer (companion + fallback).** The static triad **detects** the "green tests
  / dead app" class; it does not, by itself, **prevent** it. The only true catches are **E-1** (live runtime,
  gated — Phase 3) and a new app-level companion, **E-8** — an **app startup self-check** that validates the
  running app's *installed* `juniper-*` wheel versions against its *own* `pyproject.toml` floors and **fails
  loud at boot**. E-8 would have caught the actual canopy incident at first start with zero human action — the
  automatic enforcement that E-2's manual / CI-less posture lacks. **E-1 Plan-B:** if the E-1 Stage-0 spike is
  killed, fall back to **E-8** (automatic, prevention) + **E-2** (manual, detection) + a small hand-run HTTP
  smoke script — recovering most of E-1's value without a live-process-managing agent.
- **Phase 2 (second wave)** — **E-7** (intent-fidelity fold-in to `prompt-validator`, *not* a second subagent),
  **E-4** (per-file coverage-gap mapper, hosted in `juniper-ci-tools`, **advisory-first**), and **M-1**
  (a RUBRIC check that **consults** `known_misses.yaml`; the auto-append pipeline is deferred at N=1). These are
  **not** all mutually independent — M-1 (PR-7) and E-7 (PR-5) edit the same two files and must be sequenced
  (PR-7 after PR-5; see §7).
- **Phase 3 (later / spike-gated)** — **E-1**, the live-runtime / service-smoke diagnostician (the
  highest-value-overall idea and the only direct suite-side answer to "green tests / dead app"), built **as a
  staged Skill, not a subagent**, behind a throwaway Stage-0 feasibility spike with an explicit kill-criterion;
  and **E-6** (Playwright click-through test author), gated on E-5 and E-1 Stage 2.
- **Rejected / deferred** — **OQ-2** (persistent prompt datastore) is **rejected** (escalated from the DOR's
  "future work"; violates the genesis "no DB backend" doctrine and is redundant with
  `util/generated_prompt_index.py`); **OQ-5** (`/template-agent` auto-invocation) and **OQ-3** (more agent
  types) are **deferred** (removing `disable-model-invocation: true` is a safety regression; more agent types
  are premature — the valuable instances are E-5 and E-7). A deferred **audit** (S-1, the ecosystem env-drift
  sweep) is the downstream *use* of E-2, gated on E-2 landing.

**The cut line** is drawn at risk × demonstrated need: everything static, additive, and default-preserving is
near-term; everything that boots a live process, writes tests, or adds a backend is gated behind a feasibility
proof or rejected outright. **Nothing in this plan is implemented until the owner approves this document** (see
§11). The recommended approved near-term scope is **Phase 1 alone** (4 PRs, with G-3 gated on PR-2); Phases 2
and 3 are presented for direction but should be re-confirmed at their own gates.

---

## 2. Phase 0 / 1 Grounding Record

All baselines below were captured first-party while authoring this plan (HEAD `79a9eda`, working tree clean
apart from this untracked plan document).

### 2.1 Suite health baseline

- **`python util/agent_suite_doctor.py --json`** → **6 OK / 1 WARN**, exit 0. The single WARN is the optional
  `~/.claude` mirror not being installed in this worktree (expected; the project is the source of truth, D-6).
- **`python util/prompt_discovery/cli.py --repo-root .`** → exit 0; provenance
  `head_sha=79a9eda56cea756db406e9584bec30585d05e126`, `dirty=false` (captured before this plan file existed; a
  re-run now reports `dirty:true`, the sole dirty item being this untracked plan document), `ttl_seconds=900`;
  all 7 probes `ok` except `test_status: cold_cache` — expected, because juniper-ml is a meta-package that runs
  `python3 -m unittest` and has no `.pytest_cache` (`util/prompt_discovery/test_status.py:18-24`). This
  `cold_cache` distinction is precisely the seam D-1 hardens.

### 2.2 Platform-feasibility findings (load-bearing for E-1's shape)

- **A subagent's working directory resets between tool calls.** This is a first-party platform fact (confirmed
  by this very agent's operating constraints and consistent with the DOR's Skill-vs-subagent analysis at
  `notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md:186`: "a Skill executes inline in the main loop").
  A subagent therefore cannot reliably manage a long-lived `uvicorn` / Dash process across steps. **=> E-1 must
  be a Skill** (persistent state in the main conversation, native MCP access), not a subagent. (This same
  CWD-reset property is also why E-3's validator re-probe must explicitly name `<target>` — §6.4.)
- **`chrome-devtools` and `playwright` MCP servers are configured** in `~/.claude.json` (per the Phase-0
  grounding probe; environment fact, not a repo anchor — re-confirm at build, see below). E-1 Stage 2's UI
  driving is therefore platform-supported.
- **Nested-subagent fan-out and subagent-MCP grants are "confirm-at-build."** The DOR's primitive-mechanics
  reference (`notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md:539` "Appendix B"; and lines 226-227:
  "nested subagents require a recent Claude Code version — confirm at build (Appendix B), else run checks
  sequentially in one subagent") flags these as build-time verifications, not plan-time assumptions. The E-1
  Stage-0 spike (§6.9, PR-8) exists precisely to discharge this risk.

### 2.3 Gate reality (the mechanism that lets prose drift)

- **`prompts/**` and `util/**` are excluded from all pre-commit hooks** (flake8/bandit scope to `scripts/` +
  `tests/`; markdownlint excludes `prompts/`, `notes/`, `docs/` per `AGENTS.md:419`). For any change under
  `prompts/` or `util/`, the **only** CI gate is a `tests/test_*.py` unittest **wired into a hardcoded list in
  `.github/workflows/ci.yml`** (the `python3 -m unittest -v tests/...` block spanning roughly `ci.yml:124-266`).
- That hardcoded list has **already shipped tests that existed but were unwired** — audit finding **F14**,
  annotated in-line at `ci.yml:161-163` (`test_requirements_drift_check.py`) and `ci.yml:264-266`
  (`test_juniper_plant_all.py` / `test_juniper_chop_all.py`): *"Shipped but never wired into this list (audit
  finding F14) -- added here."* **=> Every new `util/` tool or `prompts/`-surface change in this plan MUST ship
  its `tests/test_*.py` AND its `ci.yml` line in the SAME PR**, and every tracked-surface PR updates `AGENTS.md`
  (tree + Tests inventory) per the DOR standing per-PR items. The doc-only G-3 fix is therefore **upgraded to a
  gated unit** (§6.5) so it cannot itself drift again.

---

## 3. Current-State Map (verified anchors)

| Layer | Surface | Verified anchors |
|-------|---------|------------------|
| Agents (4, all `model: opus` + `effort: max`) | `.claude/agents/{planner,prompt-validator,auditor,task-executor}.md` | `planner` tools `Read, Grep, Glob, Bash, Write`; `prompt-validator` tools `Read, Grep, Glob, Bash`; `auditor` tools `…, WebFetch, Write`; `task-executor` tools `…, Edit, Write, Agent` + `isolation: worktree` (all frontmatter lines 4-7) |
| Skill (user-only) | `.claude/skills/template-agent/SKILL.md` | `allowed-tools: Read, Grep, Glob, Bash, Write, Agent` (`:5`); `model: opus` (`:6`); `effort: max` (`:7`); `disable-model-invocation: true` (`:8`); discovery at `:33`; validator delegation at `:55-56`; emit at `:61` |
| Template library (10 templates, 5 classes) | `prompts/agent_templates/manifest.yaml` | ids `code-review`(review), `failing-tests`/`implement-plan`/`regressions`/`task`(execution), `proposal-analysis`/`audit`(analysis), `release-and-deployment`/`plan`(planning), `generic`(generic) — `manifest.yaml:38-130` |
| Rubric | `prompts/agent_templates/RUBRIC.md` | R1-R5; hard gates **R2.0** (`:72`) + **R3.4** (`:114`) declared at `:20`; **R1.1** Requirement coverage (`:53`); **R2.5** Convention fidelity (`:90`); **R2.6** verify+recover, execution-class only (`:94-99`) |
| Data layer (5 files) | `prompts/agent_templates/data/{standing_rules,anti_hallucination,conventions,ecosystem,known_misses}.yaml` | `conventions.yaml`: `line_length: 512` (`:6`), `handoff_threshold: "95-99%"` (`:7`), `python_min: ">=3.12"` (`:8`), `generated_prompts: "prompts/generated/"` (`:17`); `known_misses.yaml`: **exactly 1** miss entry (`:8-14`) |
| Discovery (7 probes) | `util/prompt_discovery/cli.py` | probes `repo_context, test_status, file_probe, symbol_probe, dependency_facts, conventions, concurrency` (`cli.py:40-48`); only arg `--repo-root` default CWD (`:80`); hard-stop exit 2 on `repo_context` failure (`:96`); `repo_context.py:16` already uses `git -C <repo_root>` (cross-repo-correct); Serena overlay `symbol_overlay.py` (OQ-8, implemented) |
| Convenience utils | `util/{template_data_resolver,template_select_preview,scaffold_template,agent_suite_doctor,agent_suite_summary,generated_prompt_index}.py`, `util/install_agents.bash` | all shipped |
| Gates (~20) | `tests/test_*.py` wired in `ci.yml:124-266` | e.g. `test_prompt_discovery.py` (`ci.yml:138`), `test_agents_frontmatter.py` (`:238`), `test_prompt_validator_contract.py` (`:227`), `test_template_agent_skill_lint.py` (`:233`), `test_template_library_drift.py` (`:202`), `test_template_data_resolver.py` (`:214`), `test_editable_install_drift_check.py` (`:132`) |

---

## 4. Validated Gap / Opportunity Ledger

Every row is first-party at HEAD `79a9eda`. The "Failure-class addressed" column distinguishes **detection /
diagnosis** (surfaces the problem to a human) from **prevention / true-catch** (stops it without human action):
the Phase-1 static triad *detects*; only **E-1** (gated) and **E-8** (app-level) *catch or prevent* the "green
tests / dead app" class.

| id | One-line | First-party evidence | Severity | State | Owner repo | Failure-class addressed |
|----|----------|----------------------|----------|-------|------------|--------------------------|
| **G-1** | `prompts/templates/`→`agent_templates` rename drift | LIVE suite surface (`.claude/`, `prompts/agent_templates/`, `util/prompt_discovery/`) has **zero** `prompts/templates/` hits; remaining hits only in the guard test, a `ci.yml` comment, and historical `notes/`/handoff/`generated/` artifacts | n/a | **CLOSED** (verified swept, #566) | ml | doc/path drift |
| **G-2** | `ecosystem.yaml` stale conda envs | `ecosystem.yaml:21-23` = JuniperCanopy1/JuniperCascor1 3.13 + JuniperData 3.14, matches live envs | n/a | **CLOSED** (#566) | ml | stale-fact injection |
| **OQ-7** | `.gitignore` negations un-ignoring cruft | `.gitignore` `.claude/*` + surgical negations; tree clean; agents tracked, settings.local/worktrees ignored | n/a | **VERIFIED CLEAN** | ml | repo hygiene |
| **G-3** | `AGENTS.md` "Repository Structure" tree stale | `AGENTS.md:188` renders `prompts/templates/` (real: `agent_templates/`); the fenced tree block (`:130-267`) omits top-level `conf/` + `papers/` (both `ls`-confirmed) and 6 in-tree packaged sub-module dirs (`juniper-{ci,config,doc}-tools/`, `juniper-{model,service}-core/`, `juniper-observability/`, all `ls`-confirmed). The grep path-drift guard cannot catch the indented tree form. | low (doc-only) | **OPEN** (now gated, §6.5) | ml | doc drift |
| **D-1** | `test_status` probe has no cache-freshness/TTL guard | `util/prompt_discovery/test_status.py:15-37`: reads `.pytest_cache/v/cache/lastfailed`, returns `status:"ok"` + `failing_count=len(failing)` with **no** mtime/TTL logic. A 6-week-stale cache returned a phantom "188 failing" in the canopy incident. The probe already owns `cold_cache`/`unavailable` vocabulary (`:19,:35`). | medium | **OPEN** | ml | green tests / dead app — **detection aid** (stops stale measurement masquerading as current) |
| **A-1** | Suite single-repo by construction | `cli.py:80` exposes only `--repo-root`; **no** `--target-repo`. `prompt-validator.md:38` freshness gate runs bare `git rev-parse HEAD` on its **own** CWD, and the **whole** R3.4 re-probe block (`:80-89`) is CWD-relative → cross-repo validation probes the wrong tree. Most targets are sibling repos → cross-repo is the common case (CANOPY `:181-182`). | medium | **OPEN** (= E-3) | ml | cross-repo friction |
| **I-2** | No env-floor-drift guard (the **actual** canopy incident) | `dependency_facts.py:22-32` reads pyproject pins + `[project].version`, **never** installed versions. `editable_install_drift_check.py:13` "does NOT invoke the environment's interpreter"; `:148,:153` are **editable**-only. Canopy's drift was **plain wheels** below floors — nothing compares installed wheels. | high | **OPEN** (= E-2) | ml + canopy | green tests / dead app — **detection** (plain wheels under floors); prevention = E-8 |
| **A-2** | No live-runtime coverage | The suite is entirely static / read-only / single-task; nothing boots a service to observe behavior (CANOPY `:185`). | high | **OPEN** by design (= E-1) | ml | green tests / dead app — the **root class** (only E-1 / E-8 truly catch or prevent) |
| **M-1** | Anti-hallucination feedback loop under-exercised | `known_misses.yaml` holds exactly **1** entry (`:8-14`, 2026-06-24 register_or_reuse, `rubric_class: R3.4b`); no routine appends new misses; RUBRIC has no check that consults the ledger. | low (observation) | **OPEN** | ml | reship of a known miss |
| **S-1** | Sibling-env plain-wheel drift unaudited | Both analyses flag it: CANOPY §6.2 S-1 (`:196-200`) + TAUDIT §6.2 S-1 (`:207`) — `JuniperCascor1` / `JuniperData` may share canopy's installed-vs-lockfile drift; not checked. The downstream **use** of E-2 (an audit, gated on E-2 landing). | medium | **OPEN** (suspected) | ml (audit) | green tests / dead app — **detection** (ecosystem-wide) |
| **E-1** | Live-runtime / service-smoke diagnostician (highest value overall) | CANOPY §6.1.1 (`:116`); pairs with `regressions` template; directly closes A-2. | proposed | **BUILD** (gated) | ml | green tests / dead app — the **true catch** (live runtime) |
| **E-2** | Environment / dependency-drift checker (= I-2 fix) | CANOPY §6.1.2 (`:120`); natural extension of `dependency_facts`; new `util/` tool. | proposed | **BUILD** (Phase 1) | ml + canopy | green tests / dead app — **detection** (manual/CI-less; prevention = E-8) |
| **E-3** | Cross-repo grounding mode (= A-1 fix) | CANOPY §6.1.3 (`:124`); `repo_context.py:16` already `git -C`-correct, so the work is the validator re-probe block (`prompt-validator.md:80-89`) + the Skill delegation. | proposed | **BUILD** (Phase 1) | ml | cross-repo friction |
| **E-4** | Per-file coverage-gap mapper | TAUDIT §6.1.1 (`:149`); "No per-file coverage gate exists **anywhere**" (`:123-124`); cascor-model `ci-cascor-model.yml:67` = `python -m pytest -v`, zero gate (verified). Host in `juniper-ci-tools`. | proposed | **BUILD** (Phase 2, advisory) | ml → ci-tools | coverage blind spots |
| **E-5** | Mocked-seam gap auditor (novel `auditor` variant) | TAUDIT §6.1.2; dogfood target canopy `src/tests/conftest.py:371` `mock_juniper_data_client` (session-scoped `autouse=True` fixture, `:370-371`, verified) that mocks the data-client integration boundary. | proposed | **BUILD** (Phase 1) | ml | green tests / dead app — **detection** (mocked seam hides real path) |
| **E-6** | Click-through test author (Playwright) | TAUDIT §6.1.3; canopy is the **only** repo with click-through tests (`:89`); model on `juniper-canopy/src/tests/ui/` (verified: `test_apply_button_flow.py`, `test_dashboard_loads.py`, +8 — 10 total). | proposed | **BUILD** (Phase 3, gated) | ml | UI-path coverage |
| **E-7** | Requirement-coverage / intent-fidelity reviewer | Companion analysis §6.1 (`:144`): the `prompt-validator` PASSed anchor-grounding yet missed a dropped owner-sourced finding (became **G-3**) and flattened a source disagreement (**G-1**) on this very prompt — faithfulness defects invisible to anchor-grounding by construction. | proposed | **BUILD** (Phase 2, fold-in) | ml | intent/faithfulness drift |
| **E-8** | App startup self-check (shift-left of E-2) | The app validates its **installed** `juniper-*` wheel versions against its **own** `pyproject.toml` floors at boot and **fails loud** — would have caught the actual canopy incident at first start, zero human action. Companion to E-2; app-level (not a suite unit). | proposed | **BUILD** (app-level) | canopy (+ candidate `juniper-service-core` helper) | green tests / dead app — **prevention** (fail-loud at boot) |

---

## 5. Ranked, Scoped Enhancement Set

The reconciliation scored each candidate on **V** (value, 1-5 high-good), **R** (risk, 1-5 low-good), and a
**feasibility tier** (Tier1 small / Tier2 medium / Tier3 large), then partitioned by risk × demonstrated need.

| Cand | V | R | Feasibility | Reconciled disposition |
|------|---|---|-------------|------------------------|
| D-1 test_status TTL | 4 | 2 | Tier1 (S) | **NEAR-TERM** |
| E-2 env-floor-drift (= I-2) | 5 | 2 | Tier1 (S-M) | **NEAR-TERM** |
| E-5 mock-seam auditor | 4 | 2 | Tier2 (S-M) | **NEAR-TERM** |
| E-3 cross-repo mode (= A-1) | 4 | 3 | Tier2 (M) | **NEAR-TERM** (additive, default-preserving) |
| G-3 AGENTS.md tree | 2 | 1 | Tier1 (S) | **NEAR-TERM gated rider** (bundled into PR-2 with a tree-drift guard) |
| E-7 intent-fidelity reviewer | 3 | 3→2 | Tier2 (M) | **SECOND-WAVE** as a **FOLD-IN** (not a 2nd subagent) |
| E-4 per-file coverage mapper | 3 | 3 | Tier2 (M) | **SECOND-WAVE** as **ADVISORY** reporter (not mandatory gate) |
| M-1 known_misses routine | 2 | 2 | Tier1 (S) | **SECOND-WAVE** minimal RUBRIC-consult only (defer auto-append) |
| E-1 live-runtime diagnostician (= A-2) | 5 | 5 | Tier3 (L), PIVOT | **LATER / SPIKE-GATED**, build as a **Skill**, staged |
| E-6 click-through author | 2 | 4 | Tier3 (L) | **LATER / GATED** on E-5 + E-1 Stage 2 |
| OQ-2 datastore | 1 | 5 | n/a | **REJECT** (doctrine "no DB backend"; queryability already in `generated_prompt_index.py`) |
| OQ-5 auto-invocation | 1 | 4 | trivial | **DEFER/REJECT** (removing `disable-model-invocation` is a safety regression) |
| OQ-3 more agent types | 2 | 3 | n/a | **DEFER** (premature; the valuable instances are E-5 / E-7) |

Two items surfaced in the Phase-4 validation pass are handled **outside** this scored matrix (they were not part
of the reconciliation's candidate set): **E-8** — an app-level startup self-check, the *prevention* companion to
E-2 (§6.11) — and **S-1** — a deferred ecosystem env-drift *audit*, the downstream *use* of E-2, gated on E-2
landing (§4 ledger; run by the `auditor` agent or the E-2 tool once it exists).

### 5.1 The partition and its rationale

- **In-scope (Phase 1 — near-term core):** D-1, E-2, E-5, E-3, + the G-3 gated rider. **The value lens's
  framing:** a **static triad — E-2 + E-5 + D-1 —** that **detects and diagnoses** the "green tests / dead app"
  class with **zero runtime risk** (all read-only / static), **plus E-3 as the cross-repo unlock** that converts
  the suite from single-repo-by-construction to first-class for the common case (sibling-repo targets). The four
  units are mutually independent and parallelizable. The cut here is **"static + additive + default-preserving,
  detection-only."** Detection is not prevention — see E-1 / E-8.
- **Second-wave (Phase 2):** E-7 (fold-in), E-4 (advisory), M-1 (consult-only). Each is shaped *down* from its
  maximal form to keep risk at 2: E-7 adds a verdict dimension rather than a loop-costing subagent; E-4 reports
  rather than gates; M-1 consults rather than auto-writes. **These are not all independent:** E-7 (PR-5) and M-1
  (PR-7) both edit `RUBRIC.md` and `prompt-validator.md`, so PR-7 is sequenced **after** PR-5 (§7). The cut here
  is **"valuable but shape-constrained until the simpler form proves out."**
- **Later / gated (Phase 3):** E-1 (staged, spike-gated), E-6 (gated on E-5 + E-1 Stage 2). The cut here is
  **"boots a live process or writes tests → requires a feasibility proof or an upstream dependency first."**
- **Companion / prevention (app-level):** E-8 — the automatic boot-time enforcement E-2 lacks; canopy-owned, not
  a suite unit, and the primary E-1 Plan-B (§6.11).
- **Deferred audit:** S-1 — the ecosystem env-drift sweep, gated on E-2 landing (the tool S-1 needs is E-2).
- **Rejected:** OQ-2 — a DB/queryable backend contradicts the genesis "what NOT to build" doctrine
  (`notes/PROMPT_ANALYSIS_AND_AUTOMATION_PLAN.md`) and is redundant with `util/generated_prompt_index.py`. This
  **escalates** OQ-2 from the DOR's "YAML for round 1; a queryable store is future work if the snippet set
  grows" (`DOR:490`) to a **hard reject** — justified because the future-work trigger (queryability needed) is
  **already moot**: `generated_prompt_index.py` provides it without a backend.
- **Deferred (not built):** OQ-5 (keep `disable-model-invocation: true` — auto-invocation is a safety
  regression) and OQ-3 (more agent types are premature; E-5 and E-7 are the valuable concrete instances).

---

## 6. Per-Enhancement Detail

Each subsection carries: **design sketch · affected files (with `file:line`) · test/dogfood plan + the exact
`tests/` gate + the `ci.yml` wiring note · acceptance criteria · risk + rollback · owner repo · JR-ID**. SHAPE
decisions from the reconciliation are carried verbatim. No JR-ID is invented — where unknown, the PR author
looks one up in `notes/REQUIREMENTS_INDEX.md` at authoring time (per the `AGENTS.md` PR conventions).

### Phase 1 — near-term core

#### 6.1 D-1 — `test_status` cache-freshness guard

**SHAPE (verbatim):** *robust staleness signal.* Stamp `cache_mtime` + `age_seconds`; flag `stale` when the
cache predates the current HEAD's commit time (more robust than an arbitrary TTL) **OR** exceeds a configurable
TTL; reuse the probe's existing `cold_cache`/`unavailable` vocabulary.

- **Design sketch.** In `probe()`, after locating `lastfailed`, read its mtime. Compare against the current
  HEAD's commit time (`git -C <repo_root> show -s --format=%ct HEAD`); if the cache predates the current
  commit, OR if `age_seconds` exceeds a configurable TTL (default proposal: the bundle's existing 900 s, owner
  to confirm in OQ below), return `status: "stale"` (new value within the established vocabulary) with
  `failing_count: None` and a `reason`. A genuinely fresh cache keeps returning `ok` + the real
  `failing_count`. This makes "no failures" impossible to assert when the truth is "measured against an old
  tree."
- **Affected files.** `util/prompt_discovery/test_status.py:15-37` (the `probe()` body); downstream consumers
  that read `per_probe_status` already tolerate non-`ok` statuses (`cli.py:40-48` aggregates without
  asserting `ok`).
- **Test / dogfood plan + gate.** Extend **`tests/test_prompt_discovery.py`** (already wired at `ci.yml:138`)
  with cases: (a) fresh cache mtime ≥ HEAD commit time → `ok`; (b) cache mtime < HEAD commit time → `stale`;
  (c) cache age > TTL → `stale`; (d) absent cache → still `cold_cache`; (e) unreadable → still `unavailable`.
  **ci.yml wiring note:** the gate line already exists — **no new `ci.yml` line needed**; the PR still updates
  `AGENTS.md`'s test description if the probe's contract grows a status value.
- **Acceptance criteria.** A `lastfailed` whose mtime precedes the HEAD commit time yields
  `status == "stale"` and `failing_count is None`; a fresh cache is unchanged; the `cold_cache`/`unavailable`
  branches are byte-for-byte preserved; `cli.py --repo-root .` still exits 0 and reports `test_status` for this
  meta-package as `cold_cache` (regression check against the §2.1 baseline).
- **Risk + rollback.** Low. Risk: a clock-skew false-positive `stale`. Mitigation: HEAD-commit-time comparison
  (monotonic w.r.t. commits) is the primary signal; TTL is the secondary. Rollback: revert the single-file PR;
  the probe reverts to today's mtime-blind behavior.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

#### 6.2 E-2 — Environment floor-drift checker (the I-2 fix)

**SHAPE (verbatim):** *env-agnostic + gate-honest.* Take the env path as an arg / read `ecosystem.yaml` (never
hardcode `JuniperCanopy1`); reuse `editable_install_drift_check.py`'s dist-info reading (robust to broken
envs); state plainly the CI gate is structural (no conda in ubuntu CI) + a manual-verify note.

- **Design sketch.** New `util/env_floor_drift_check.py`: given a repo root + a conda-env site-packages path
  (arg, or resolved from `prompts/agent_templates/data/ecosystem.yaml`), read **every** installed distribution's
  version from its `*.dist-info/METADATA` (the same dist-info-direct read pattern as
  `editable_install_drift_check.py:132-160`, robust when the interpreter is broken — `:13`), parse the repo's
  `pyproject.toml` floors for `juniper-*` deps, and report each dep as `OK` / `BELOW_FLOOR` / `MISSING`. This
  closes the exact I-2 gap: `dependency_facts.py:22-32` reads pins only, and
  `editable_install_drift_check.py:153` filters to **editable** installs — neither catches a **plain wheel**
  below a floor (the canopy incident). **Companion:** E-2 is *detection* (run on demand); its *prevention*
  counterpart is **E-8** (boot-time self-check, §6.11).
- **Affected files.** New `util/env_floor_drift_check.py`; reads `prompts/agent_templates/data/ecosystem.yaml`
  (env catalog) and the target repo's `pyproject.toml`; optionally surfaced later via a `dependency_facts`
  extension (out of scope for this PR — keep the tool standalone first).
- **Test / dogfood plan + gate.** New **`tests/test_env_floor_drift_check.py`** with a **synthetic
  conda-dir fixture** (no real pip / no real conda — mirrors how `tests/test_editable_install_drift_check.py`
  builds a fake site-packages): assert `BELOW_FLOOR` when a synthetic `juniper-x` METADATA version < the
  pyproject floor, `OK` when ≥, `MISSING` when absent, exit-code semantics, and `--json` shape. **ci.yml wiring
  note (MANDATORY):** add `python3 -m unittest -v tests/test_env_floor_drift_check.py` to the hardcoded list in
  `ci.yml` **in this same PR** (else F14 repeats). **The real conda path cannot run in ubuntu CI** — state this
  in the tool docstring and AGENTS.md, and add a documented **manual-verify** invocation for the owner.
- **Acceptance criteria.** The **synthetic dist-info fixture is the real gate**: a synthetic `juniper-x` below
  its floor → `BELOW_FLOOR` (exit non-zero), at/above → `OK`, absent → `MISSING`; the tool **never** hardcodes
  an env name (greps clean for `JuniperCanopy1` as a literal). *Optional manual spot-check (not a CI criterion;
  `JuniperCanopy1` was reinstalled 2026-06-26 so it now reads clean):* a live run against a deliberately
  floor-violating env reports `BELOW_FLOOR`.
- **Risk + rollback.** Low-medium. Risk: dist-info parsing edge cases (extras, normalized names). Mitigation:
  reuse the proven `_read_dist_name` pattern (`editable_install_drift_check.py:132`). Rollback: revert the PR;
  no existing behavior changes (additive tool).
- **Owner repo.** ml (tool) + canopy (process — adopt as a post-refactor reinstall check). **JR-ID.** TBD —
  none invented.

#### 6.3 E-5 — Mocked-seam gap auditor (novel `auditor` variant)

**SHAPE:** a new read-only subagent (opus+max), in the `auditor` family, that hunts autouse/session fixtures
which mock an integration boundary and thereby leave the real construct/call path untested.

- **Design sketch.** New `.claude/agents/mock-seam-auditor.md`: `model: opus`, `effort: max`, read-only tools
  `Read, Grep, Glob, Bash` (matching `prompt-validator`'s tool set). It greps a target repo's tests for
  `@pytest.fixture(... autouse=True ...)` and session-scoped fixtures that patch/mock a known integration class
  (clients, service constructors), then cross-checks whether any non-test code path constructs/calls the real
  boundary without a corresponding un-mocked test — emitting a findings report (paths + `file:line` + the
  masked seam). Dogfood target: canopy `src/tests/conftest.py:370-371` `mock_juniper_data_client`
  (session-scoped `autouse=True`), the exact fixture that hid the canopy runtime breakage.
- **Affected files.** New `.claude/agents/mock-seam-auditor.md` only (read-only agent; no `util/` code).
- **Test / dogfood plan + gate.** Automatically covered by **`tests/test_agents_frontmatter.py`** (wired at
  `ci.yml:238`), which asserts every `.claude/agents/*.md` honors the suite frontmatter contract (name ==
  filename, substantive description, declared tools, opus+max). **Optional** dedicated contract test
  (`tests/test_mock_seam_auditor_contract.py`, modeled on `tests/test_prompt_validator_contract.py`) if the
  agent pins an output schema — if added, it ships its own `ci.yml` line. **Dogfood:** run the agent against
  canopy and confirm it flags `conftest.py:371` as a masked data-client seam. **ci.yml wiring note:** no new
  line if only the `.md` ships (frontmatter gate already covers it); one new line if the optional contract test
  is added.
- **Acceptance criteria.** `tests/test_agents_frontmatter.py` passes with the new agent present; a dogfood run
  against canopy names `src/tests/conftest.py:371` `mock_juniper_data_client` as a session-autouse mock of the
  data-client boundary and identifies at least one real construct/call path not exercised un-mocked.
- **Risk + rollback.** Low. Risk: false positives (legitimate mocks). Mitigation: the agent reports, never
  edits or fails CI; the human triages. Rollback: delete the `.md` (and its optional test + `ci.yml` line).
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

#### 6.4 E-3 — Cross-repo `--target-repo` mode (the A-1 fix)

**SHAPE (verbatim):** *additive.* Add explicit `--target-repo`; keep the `--repo-root`-default-CWD path
unchanged; fix the validator side to use `git -C <target> rev-parse HEAD` (the real gap —
`prompt-validator.md` step 1 currently runs HEAD on its own CWD). Wire the Skill delegation to pass the target.

- **Design sketch.** **(1) Discovery — nearly free.** `repo_context.py:16` already runs
  `run(["git", "-C", repo_root, "rev-parse", "HEAD"])` (verified), so the discovery side is already
  cross-repo-correct; `--target-repo` is largely an explicit, self-documenting **alias** of the working
  `--repo-root` (default-CWD behavior at `cli.py:80` preserved byte-for-byte). **(2) Validator — the real
  work.** `prompt-validator.md`'s **entire re-probe procedure** must retarget `<target>`, not just the freshness
  gate. Today: the freshness gate (`:38`) is a bare `git rev-parse HEAD` on the validator's own CWD, **and the
  whole R3.4 taxonomy block (`:80-89`) is CWD-relative** — the `ls`/`test -e` path probe (R3.4a), the `grep -rn`
  def probe (R3.4b), the `grep` the pin in `pyproject.toml` (R3.4c), and the `grep` the parent `AGENTS.md`
  (R3.4d). Because the validator's CWD is juniper-ml **and resets per Bash call**, in cross-repo mode every one
  of these would probe SIBLING anchors against the WRONG tree → false `grounded:false`. Every probe command must
  name the target (`git -C <target>`, `ls <target>/…`, `grep … <target>/…`). **(3) Skill** — `/template-agent`
  delegation passes the resolved target through (`SKILL.md:33` already accepts `--repo-root`; `:55-56` hands the
  bundle + target to the validator).
- **Affected files.** `util/prompt_discovery/cli.py:80` (add the `--target-repo` alias; `repo_context.py:16` is
  already `git -C`-correct — verify, no change likely); `.claude/agents/prompt-validator.md:38` (freshness gate)
  **AND `:80-89`** (the entire R3.4a-d re-probe taxonomy → retarget each command to `<target>`);
  `.claude/skills/template-agent/SKILL.md:22,:33,:55-56` (argument + delegation).
- **Test / dogfood plan + gate.** Extend **three** existing gates (all already wired): `test_prompt_discovery.py`
  (`ci.yml:138`) — `--target-repo` grounds a *sibling* path and the default-CWD path is unchanged;
  `test_prompt_validator_contract.py` (`ci.yml:227`) — assert the validator's re-probe block contains **no**
  CWD-relative command (every `git`/`ls`/`grep` names `<target>`) and the verdict `head_sha` binds to the
  target; `test_template_agent_skill_lint.py` (`ci.yml:233`) — the Skill delegation passes the target. **ci.yml
  wiring note:** all three lines already exist — **no new line**; PR updates each test's `AGENTS.md` description.
- **Acceptance criteria.** `cli.py --target-repo <sibling>` produces a bundle whose provenance `head_sha`
  equals `git -C <sibling> rev-parse HEAD`; the no-arg / `--repo-root .` path is byte-for-byte unchanged
  (regression vs §2.1 baseline); `prompt-validator.md` contains **no** CWD-relative probe command in its
  re-probe block. **Cross-repo dogfood (new, mandatory):** ground + validate a real **sibling-repo** anchor
  end-to-end (e.g. validate a canopy anchor from the juniper-ml worktree) and confirm the validator returns
  `grounded:true` for a true sibling anchor **and** `grounded:false` for a deliberately-wrong one — i.e. no
  false negatives from CWD confusion. All three contract/lint tests pass.
- **Risk + rollback.** Medium (touches three coupled surfaces, and the validator-side change is broader than the
  freshness gate alone). Risk: subtle default-path regression; an un-retargeted probe command silently
  re-introducing the CWD bug. Mitigation: additive flag; the contract test asserts *zero* CWD-relative probe
  commands; explicit default-preservation + cross-repo dogfood criteria. Rollback: revert the single PR; the
  manual cross-repo override (passing `--repo-root <sibling>`) still works as it does today.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

#### 6.5 G-3 — `AGENTS.md` Repository-Structure tree refresh (Phase-1 gated rider)

**SHAPE:** **now a gated unit** (was doc-only). Rides PR-2 and ships a new tree-drift guard so the indented-tree
form cannot silently re-drift — honoring this plan's own §2.3 doctrine ("a `prompts/`/`util/`/tracked-surface
change ships a wired gate").

- **Design sketch.** Correct the tree at `AGENTS.md:188` (`prompts/templates/` → `prompts/agent_templates/`)
  and add the missing top-level entries `conf/` and `papers/` plus the 6 in-tree packaged sub-module dirs
  (`juniper-{ci,config,doc}-tools/`, `juniper-{model,service}-core/`, `juniper-observability/`). All eight
  additions are `ls`-confirmed present (§2/§4 evidence).
- **Affected files.** `AGENTS.md:130-267` (the fenced Repository-Structure tree block); new
  `tests/test_agents_md_tree_drift.py`; `.github/workflows/ci.yml` (new unittest line).
- **Test / dogfood plan + gate.** **New gate (this PR):** `tests/test_agents_md_tree_drift.py` asserts that
  every top-level directory (`ls -d */`) appears as a node in the AGENTS.md Repository-Structure tree (the fenced
  block `AGENTS.md:130-267`) — catching the **indented-tree** form that the existing grep path-drift guard
  (`tests/test_agent_suite_path_drift.py`) cannot. Portable / self-locating like the other AGENTS.md lints
  (`test_agents_md_header_schema.py`). **ci.yml wiring note (MANDATORY):** add
  `python3 -m unittest -v tests/test_agents_md_tree_drift.py` to the hardcoded list **in the same PR (PR-2)**.
- **Acceptance criteria.** The tree shows `prompts/agent_templates/` (not `templates/`), lists `conf/` and
  `papers/`, and lists the 6 packaged sub-module dirs; `test_agents_md_tree_drift.py` passes and **FAILS** if a
  top-level dir is later added without a tree update (verify by a synthetic temp dir in the test fixture).
- **Risk + rollback.** Negligible (doc + a self-locating lint). Rollback: revert the hunk + remove the test +
  its `ci.yml` line.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

### Phase 2 — second wave

#### 6.6 E-7 — Intent-fidelity fold-in to `prompt-validator`

**SHAPE (verbatim):** *fold-in.* Add an intent-fidelity dimension to the existing `prompt-validator` (a new
RUBRIC check / strengthened R1.1: "every owner requirement AND every source-document finding is represented;
source disagreements are surfaced, not flattened") rather than a second subagent in the Skill's bounded (max-3)
loop. Single verdict; no loop-cost increase. Promote to a separate `intent-reviewer` agent only if fold-in
proves insufficient.

- **Design sketch.** Strengthen `RUBRIC.md` R1.1 (`:53`, "Requirement coverage") to additionally require that
  every **source-document finding** (not just every task-description requirement) is represented, and that
  **source disagreements are surfaced rather than flattened** — the exact two faithfulness defects this prompt
  exposed (a dropped finding became G-3; a flattened CANOPY/TAUDIT disagreement became G-1). Reflect the
  strengthened check in `prompt-validator.md` so the headless validator applies it. No new agent, no extra loop
  iteration.
- **Affected files.** `prompts/agent_templates/RUBRIC.md:49-64` (R1 block / R1.1); `.claude/agents/prompt-validator.md`
  (the rubric-application section that enumerates R1 checks). **Shared with M-1 (PR-7)** — see §7 sequencing.
- **Test / dogfood plan + gate.** `test_prompt_validator_contract.py` (`ci.yml:227`) — assert every rubric ID
  the validator cites exists in `RUBRIC.md` (so the strengthened R1.1 stays in sync); `test_template_library_drift.py`
  (`ci.yml:202`) — the **sole** gate for `RUBRIC.md` (the library is pre-commit-excluded), so any RUBRIC edit
  must keep the drift test green. Both gates are **structural-only** — they verify the rubric text/ID wiring, not
  that the strengthened check *behaves*; the behavioral change is **dogfood-verified** (re-run the validator on
  *this* prompt's draft and confirm the strengthened R1.1 would flag a dropped source finding). **ci.yml wiring
  note:** both lines exist — **no new line**.
- **Acceptance criteria.** R1.1's text names both "requirement coverage" and "source-document finding
  coverage + surfaced disagreements"; the validator's verdict can emit an R1.1 finding for a dropped/flattened
  source item (dogfood-demonstrated); both structural gates pass.
- **Risk + rollback.** Low-medium (3→2 after fold-in shaping). Risk: R1.1 over-triggers. Mitigation: keep it
  `major` (not a blocker), so it informs rather than hard-fails. Rollback: revert the RUBRIC/validator hunks.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

#### 6.7 E-4 — Per-file coverage-gap mapper (advisory-first)

**SHAPE (verbatim):** *advisory first.* Read-only reporter (exit 0) hosted in `juniper-ci-tools` + dogfood test
in juniper-ml; promote to a blocking per-file gate per-repo with owner sign-off only. Isolate the numpy-2.x
dotted-`--cov` workaround behind a documented shim.

- **Design sketch.** New module + console script in `juniper-ci-tools/juniper_ci_tools/` (mirroring the existing
  `cli_lint_*.py` + `[project.scripts]` console-script pattern — `juniper-ci-tools/pyproject.toml:38,:40`,
  package version `0.4.0` at `:7`): given a repo + its real test command, run coverage, parse `coverage json`,
  and emit the per-file distribution, the list of files below 90%, and each sub-module's average vs the 95%
  bar. **Exit 0 always (advisory).** Carry the numpy-2.x dotted-`--cov` workaround (package-form `--cov` +
  `[report] include` scoping) behind a documented shim. Addresses the systemic TAUDIT gap: no per-file gate
  exists anywhere (`:123-124`), and cascor-model's CI is `python -m pytest -v` with zero gate
  (`juniper-cascor/.github/workflows/ci-cascor-model.yml:67`, verified).
- **Affected files.** New `juniper-ci-tools/juniper_ci_tools/<coverage_mapper>.py` + `cli_*.py` + a
  `[project.scripts]` console-script entry in `juniper-ci-tools/pyproject.toml`; tests in
  `juniper-ci-tools/tests/`; a **dogfood** `tests/test_*.py` in juniper-ml.
- **Test / dogfood plan + gate.** Primary tests live in `juniper-ci-tools/tests/` (run by the dedicated
  ci-tools workflow). **Dogfood gate in juniper-ml:** a new `tests/test_coverage_gap_mapper_drift.py` (modeled
  on `tests/test_ci_tools_drift.py`) asserting the pin admits the published version; **ci.yml wiring note:**
  add its `python3 -m unittest -v` line to `ci.yml` in the same PR. **Cross-repo coverage cannot run in
  juniper-ml CI** — gate is structural; add a manual-verify note.
- **Acceptance criteria.** The mapper, run on a repo with a known sub-90% file, lists that file and computes
  the correct sub-module average; exit code is 0 regardless of findings (advisory); the numpy-2.x workaround is
  isolated and documented; the juniper-ml dogfood/drift test passes.
- **Risk + rollback.** Medium. Risk: coverage-tool fragility across repos. Mitigation: advisory exit-0 +
  documented shim; opt-in per repo. Rollback: do not adopt per-repo; the ci-tools module is inert until
  invoked. Promotion to a blocking gate requires separate owner sign-off (OQ below).
- **Owner repo.** ml → ci-tools. **JR-ID.** TBD — none invented.

#### 6.8 M-1 — `known_misses.yaml` RUBRIC-consult (minimal)

**SHAPE (verbatim):** *minimal.* A RUBRIC check that CONSULTS `known_misses.yaml` (so a recorded miss can't
reship); DEFER the auto-append pipeline (premature at N=1; an unvalidated write-path can pollute the ledger).

- **Design sketch.** Add a RUBRIC check directing the validator to cross-check the drafted prompt's asserted
  anchors against the `known_misses.yaml` ledger (`prompts/agent_templates/data/known_misses.yaml`, currently 1
  entry at `:8-14`, `rubric_class: R3.4b`) and flag any re-assertion of a recorded false claim. **ID choice
  (load-bearing):** add it as **a clause under the existing R3.4** OR as a new **R3.5** — **NOT `R3.4f`**,
  because the rubric-ID regex `_RUBRIC_ID = re.compile(r"\bR[1-5](?:\.\d+[a-e]?)?\b")`
  (`tests/test_prompt_validator_contract.py:53-54`) stops the sub-letter class at `[a-e]` and the `\b` would
  mis-extract a `...f` ID. **No auto-append** — the ledger stays human-curated; the write-path is explicitly out
  of scope.
- **Affected files.** `prompts/agent_templates/RUBRIC.md` (the new R3.5 / R3.4 clause); `.claude/agents/prompt-validator.md`
  (apply the consult); `tests/test_template_library_drift.py` (extend `_EXPECTED_RUBRIC_IDS` at `:39` with the
  new ID **in the same PR**, else the new ID is unguarded by the drift check); reads
  `prompts/agent_templates/data/known_misses.yaml`. **Shared with E-7 (PR-5)** — see §7 sequencing.
- **Test / dogfood plan + gate.** `test_template_data_resolver.py` (`ci.yml:214`, the **sole** gate for the
  data layer) — assert the ledger loads and the resolver can surface it; `test_template_library_drift.py`
  (`ci.yml:202`) — the new ID is in `_EXPECTED_RUBRIC_IDS` and present in `RUBRIC.md`;
  `test_prompt_validator_contract.py` (`ci.yml:227`) — the new ID is cited and regex-clean. These are
  **structural-only**; the behavioral consult is **dogfood-verified** (a drafted prompt re-asserting the
  recorded miss is flagged). **ci.yml wiring note:** all lines exist — **no new line**.
- **Acceptance criteria.** A drafted prompt that re-asserts the recorded miss (`register_or_reuse` at the wrong
  path) is flagged by the validator (dogfood); the new rubric ID is R3.5-or-R3.4-clause (regex-clean) and in
  `_EXPECTED_RUBRIC_IDS`; the ledger remains append-only-by-human (no code writes to it); the three structural
  gates pass.
- **Risk + rollback.** Low. Risk: negligible at N=1. Rollback: revert the RUBRIC/validator hunks + the
  `_EXPECTED_RUBRIC_IDS` addition.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

### Phase 3 — later / gated

#### 6.9 E-1 — Live-runtime / service-smoke diagnostician (staged Skill)

**SHAPE (verbatim):** *Skill, not subagent.* A subagent's CWD resets per tool call → it can't reliably manage a
long-lived uvicorn/Dash process; a Skill runs in the main conversation with persistent state + native MCP
(chrome-devtools/playwright are configured). **Stage it.** Mandatory teardown/timeout/orphan-reap from day one
(reuse `util/reap_pytest_orphans.bash` / `util/kill_all_pythons.bash` patterns — both verified present). CI gate
is structural-only + a documented manual smoke-verify step.

- **Stage 0 (PR-8) — throwaway feasibility spike.** Prove a Skill can (a) boot a service in its conda env, (b)
  drive it via MCP, and (c) reach it. **Kill-criterion:** if any of the three fails, stop and record the
  verdict. **Deliverable:** a `notes/` spike record + a proceed/kill decision. **No committed runtime
  surface.** This also discharges the DOR Appendix-B "confirm-at-build" items (§2.2).
- **Stage 1 (PR-9) — HTTP-only diagnostician.** New `.claude/skills/service-smoke/SKILL.md`: boot canopy in
  `JuniperCanopy1`, hit `/v1/health` + endpoints, tail logs, report live tracebacks `file:line`. No browser.
- **Stage 2 (PR-10) — UI smoke.** Add `playwright` / `chrome-devtools` driving, opt-in.
- **Plan-B (if Stage-0 is killed).** Do **not** pursue E-1. Fall back to the **E-8** automatic boot-time
  self-check (prevention) + **E-2** manual env-floor check (detection) + a small hand-run HTTP smoke script
  (`curl` the health endpoint, no Skill). This combination recovers most of E-1's value without a
  live-process-managing agent and carries none of E-1's R=5 risk.
- **Affected files.** Stage 0: none committed (spike + `notes/` record). Stage 1: new
  `.claude/skills/service-smoke/SKILL.md`; reuse teardown patterns from `util/reap_pytest_orphans.bash`,
  `util/kill_all_pythons.bash`. Stage 2: extends the Stage-1 Skill.
- **Test / dogfood plan + gate.** Stage 1/2: a new `tests/test_service_smoke_skill_lint.py` (modeled on
  `tests/test_template_agent_skill_lint.py`) asserting frontmatter (opus+max, user-only, declared MCP/tools)
  and that the bounded state machine wires to real artifacts + a teardown step. **ci.yml wiring note:** add its
  `python3 -m unittest -v` line in the same PR. **The live boot cannot run in ubuntu CI (no conda, no
  services)** — gate is **structural-only**; ship a documented **manual smoke-verify** step the owner runs.
- **Acceptance criteria.** Stage 0: a recorded proceed/kill verdict with first-party evidence. Stage 1: against
  a deliberately-broken canopy, the Skill boots, fails the health probe, and reports the live traceback
  `file:line` (the "green tests / dead app" catch); teardown leaves no orphan python (verify via the reaper
  pattern). Stage 2: a UI smoke reaches the dashboard and reports a client-side failure.
- **Risk + rollback.** **High (R=5).** Risks: orphaned long-lived processes, environment coupling, MCP-grant
  uncertainty. Mitigations: Stage-0 kill-criterion + the Plan-B fallback; mandatory teardown/timeout/orphan-reap
  from day one; structural-only CI + manual verify. Rollback: each stage is its own PR; delete the Skill (+ test
  + `ci.yml` line); Stage 0 commits nothing.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

#### 6.10 E-6 — Click-through test author (gated)

**SHAPE:** generate **reviewed (never auto-merged)** Playwright tests modeled on the canopy UI harness.

- **Design sketch.** A capability (agent or Skill step) that, given a user-facing webapp, emits Playwright
  tests modeled on `juniper-canopy/src/tests/ui/` (verified: `test_apply_button_flow.py`,
  `test_dashboard_loads.py`, +8 — 10 total). Canopy is the **only** repo with click-through tests (TAUDIT
  `:89`), so it is the sole template. Output is always human-reviewed; never auto-merged.
- **Dependencies.** Gated on **E-5** (PR-3) and **E-1 Stage 2** (PR-10) — it needs the live UI-driving
  capability proven first.
- **Affected files.** TBD at build (depends on E-1 Stage 2's shape); models on `juniper-canopy/src/tests/ui/*`.
- **Test / dogfood plan + gate.** Generated tests are reviewed artifacts, not a suite gate; if the author ships
  as a Skill, a `tests/test_*_skill_lint.py` + `ci.yml` line gate its frontmatter/wiring (structural-only;
  generated tests run in the **target** repo's CI, not juniper-ml's). Manual-verify note required.
- **Acceptance criteria.** For canopy, the author reproduces a `src/tests/ui/`-shaped test that drives a real
  control and asserts an observable outcome; the output is presented for review and is never auto-merged.
- **Risk + rollback.** Medium-high (R=4). Risk: low-value or flaky generated tests. Mitigation: human review
  gate; gated behind E-1 Stage 2. Rollback: do not adopt; delete any Skill surface.
- **Owner repo.** ml. **JR-ID.** TBD — none invented.

### Companion (app-level, not a suite PR)

#### 6.11 E-8 — App startup self-check (prevention companion to E-2)

**SHAPE:** the *automatic* boot-time enforcement that E-2's manual / CI-less posture lacks; the primary E-1
Plan-B. **App-level** — owned by the app (canopy first), **not** part of the suite PR sequence (PR-1..PR-11).

- **Design sketch.** At app startup, the app reads its **installed** `juniper-*` wheel versions (via
  `importlib.metadata.version`) and compares them against its **own** `pyproject.toml` floors; if any installed
  wheel is below its floor, **fail loud** (raise / exit non-zero with a message naming dep + floor + installed
  version) before binding the server. This would have caught the actual canopy incident at first start with zero
  human action — the gap that the "reinstall step was forgotten" left open (a manual / CI-less detector like E-2
  has the same reliability as the step that *was* forgotten). Candidate shared implementation: a small helper in
  **`juniper-service-core`** (the de-cascored service-tier package, `ls`-confirmed present) so every service can
  adopt it uniformly.
- **Affected files.** Canopy's app-startup path (exact module **TBD at build — not invented here**); candidate
  shared helper in `juniper-service-core/`. **Not** a juniper-ml suite surface.
- **Test / dogfood plan + gate.** App-level test in the owning repo: a unit test asserting the self-check
  raises when a synthetic installed version is below floor and passes when satisfied. If the helper lands in
  `juniper-service-core`, it carries its own tests + `ci.yml` there. **Not** a juniper-ml `tests/` gate.
- **Acceptance criteria.** Booting canopy with a deliberately-downgraded `juniper-*` wheel **fails loud** at
  startup with a clear dep/floor/installed message; a satisfied env boots normally; an escape-hatch env var (if
  the owner wants one) is honored and documented.
- **Risk + rollback.** Low-medium. Risk: a false-positive at boot blocking a legitimate start. Mitigation:
  clear message + an optional documented escape-hatch env var (owner to decide). Rollback: remove the
  self-check call (single call site).
- **Owner repo.** canopy (app change) + candidate `juniper-service-core` (shared helper). **JR-ID.** TBD —
  none invented.

---

## 7. Phased Single-Work-Unit PR Sequence + Dependency Graph

One PR per unit. **Never merge to main — the owner approves every merge** (and all PyPI/deploy gates). Every
`util/`- or `prompts/`-surface PR ships its `tests/test_*.py` gate **and** its `ci.yml` line **and** its
`AGENTS.md` update (tree + Tests inventory) in the **same** PR. Where CI cannot exercise the real path, the gate
is structural-only and the PR carries a documented manual-verify note (do not let "test passes / reality
untested" hide).

> **AGENTS.md contention (operational).** Several Phase-1 PRs touch `AGENTS.md` (PR-2 carries the G-3 tree fix +
> a new Tests-inventory line; PR-3 adds an agent → Tests inventory; PR-4 may touch test descriptions). Sequence
> the AGENTS.md hunks or rebase to avoid conflicts, and beware the **`agents-md-touch-up` skip-ci orphan
> hazard**: a `[skip ci]` `Last Updated` bump on HEAD can orphan required checks (BLOCKED-despite-green) — clear
> it with an empty re-trigger commit (the known touch-up-orphan gotcha).

**Phase 1 (near-term core — mutually independent, parallelizable):**

- **PR-1 — D-1** test_status freshness guard: `util/prompt_discovery/test_status.py` + `tests/test_prompt_discovery.py`
  (gate line already wired at `ci.yml:138`). Owner: ml.
- **PR-2 — E-2 (+ G-3 gated rider)** env-floor-drift checker: new `util/env_floor_drift_check.py` + new
  `tests/test_env_floor_drift_check.py` + **new `ci.yml` line**; **carries G-3** — the `AGENTS.md:130-267` tree
  refresh **plus** the new `tests/test_agents_md_tree_drift.py` guard + **its** `ci.yml` line. (Two new test
  files + two new ci.yml lines in this PR: one for E-2, one for the G-3 tree guard.) Owner: ml (tool) + canopy
  (process).
- **PR-3 — E-5** mock-seam gap auditor: new `.claude/agents/mock-seam-auditor.md` (opus+max, read-only),
  auto-covered by `tests/test_agents_frontmatter.py` (`ci.yml:238`) + optional contract test + AGENTS.md.
  Dogfood vs canopy `conftest.py:371`. Owner: ml.
- **PR-4 — E-3** cross-repo `--target-repo` mode: `util/prompt_discovery/cli.py` +
  `.claude/agents/prompt-validator.md` (freshness gate **and** the `:80-89` re-probe block) +
  `.claude/skills/template-agent/SKILL.md` +
  `tests/{test_prompt_discovery,test_prompt_validator_contract,test_template_agent_skill_lint}.py` (all gate
  lines already wired). Owner: ml.

**Phase 2 (second wave — NOT fully parallel: PR-7 depends on PR-5):**

- **PR-5 — E-7** intent-fidelity fold-in: `.claude/agents/prompt-validator.md` + `prompts/agent_templates/RUBRIC.md`
  + `tests/{test_prompt_validator_contract,test_template_library_drift}.py`. Owner: ml.
- **PR-6 — E-4** per-file coverage-gap mapper: `juniper-ci-tools` module + console script + ci-tools tests;
  dogfood/drift `tests/test_*.py` in juniper-ml + **new `ci.yml` line** + **AGENTS.md (Tests inventory)**.
  Owner: ml → ci-tools.
- **PR-7 — M-1** known_misses RUBRIC-consult: `prompts/agent_templates/RUBRIC.md` +
  `.claude/agents/prompt-validator.md` + `tests/test_template_library_drift.py` (extend `_EXPECTED_RUBRIC_IDS`)
  + `tests/test_template_data_resolver.py`. **Depends on PR-5** — both edit `RUBRIC.md` and
  `prompt-validator.md`, and `test_prompt_validator_contract.py` cross-checks cited rubric IDs against
  `RUBRIC.md`; sequence PR-7 after PR-5 to avoid a rubric-ID merge conflict. Owner: ml.

**Phase 3 (later / gated):**

- **PR-8 — E-1 Stage 0** feasibility spike: throwaway; deliverable = a `notes/` spike record + kill/proceed
  verdict. No committed runtime surface. Owner: ml.
- **PR-9 — E-1 Stage 1** HTTP-only diagnostician Skill: new `.claude/skills/service-smoke/SKILL.md` + new
  `tests/test_service_smoke_skill_lint.py` + **new `ci.yml` line** + AGENTS.md; structural gate + manual smoke
  note. **Depends on PR-8 proceed.** Owner: ml.
- **PR-10 — E-1 Stage 2** UI smoke: add chrome-devtools/playwright driving. **Depends on PR-9.** Owner: ml.
- **PR-11 — E-6** click-through test author: writes reviewed (never auto-merged) tests. **Depends on PR-3
  (E-5) AND PR-10 (E-1 Stage 2).** Owner: ml.

**Not in the suite PR sequence:** **E-8** (app-level, canopy-owned — §6.11; the E-1 Plan-B) and **S-1** (a
deferred ecosystem env-drift *audit*, run by the `auditor`/E-2 once **E-2 (PR-2)** has landed).

**Dependency graph.**

```
Phase 1 (independent, parallel):   PR-1   PR-2(+G-3 gated)   PR-3   PR-4
Phase 2 (PR-7 depends on PR-5):    PR-5 --> PR-7      PR-6 (independent)
Phase 3 (chained):                 PR-8 --> PR-9 --> PR-10 --> PR-11
                                                       PR-3 ----------^  (PR-11 also needs E-5)
Outside suite seq:  E-8 (app-level)    S-1 audit (after PR-2 / E-2)
```

- Phase-1 units are independent of each other; **G-3 is bundled into PR-2 as a gated rider**.
- Phase-2: **PR-5 → PR-7** (shared `RUBRIC.md` + `prompt-validator.md`); **PR-6** is independent.
- Phase-3 is a chain: **PR-8 → PR-9 → PR-10 → PR-11**; **PR-11 additionally depends on PR-3 (E-5)**.
- **S-1** (audit) is gated on **PR-2 (E-2)**; **E-8** is an independent app-level item.

**REJECTED:** OQ-2 (datastore). **DEFERRED (not built):** OQ-5 (auto-invocation), OQ-3 (more agent types).

### 7.1 Out of scope (cross-referenced, not re-claimed)

Deliberately excluded so their absence is intentional, not dropped:

- **Canopy-owned issues from the debug analysis** — **C-2** (misleading commented client pins in canopy
  requirements docs, CANOPY `:154`), **D-2** (canopy demo-mode degradation choice, `:167`), **D-3** (recurrence
  model `status="live"` + Start-enabled with no service URL, `:172`). Owner: **canopy**; tracked there, not in
  this suite plan.
- **A lower-priority "runtime-triage auditor" variant** (a read-only triager of existing logs/tracebacks) — a
  weaker cousin of E-1; not pursued now (E-1 + E-5 cover the high-value cases).

---

## 8. Cross-References

Each enhancement mapped to the design-of-record decisions/open-questions
(`notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`) and the dogfooding analyses' gap IDs
(`notes/JUNIPER_CANOPY_DEBUG-PROMPT_ANALYSIS_2026-06-26.md` = CANOPY;
`notes/JUNIPER_ML_TEST_SUITE_AUDIT_PROMPT_ANALYSIS_2026-06-26.md` = TAUDIT;
`notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PROMPT-ANALYSIS_2026-06-26.md` = companion).

| Enhancement | DOR decision / OQ | Dogfooding gap ID |
|-------------|-------------------|-------------------|
| D-1 test_status freshness | discovery design S5.6 (test_status `cold_cache`/`unavailable` vocabulary, `test_status.py:1-6`) | CANOPY §6.2 D-1 |
| E-2 env floor-drift | extends `dependency_facts` probe (DOR §discovery) | CANOPY §6.1.2 (`:120`); gap **I-2** |
| E-3 cross-repo mode | **D-6** (`DOR:96`, `--repo-root` to ground sibling repos); OQ-around cross-repo | CANOPY §6.1.3 (`:124`) / §6.4; gap **A-1** |
| E-5 mock-seam auditor | round-2 `auditor` family (DOR round-2 roadmap) | TAUDIT §6.1.2; dogfood canopy `conftest.py:371` |
| G-3 AGENTS.md tree | DOR standing per-PR AGENTS.md update | companion catalog row **G-3**; TAUDIT §6.2 |
| E-7 intent-fidelity fold-in | RUBRIC R1.1 (`RUBRIC.md:53`); validator contract | companion §6.1 (`:144`); surfaced G-1 + G-3 faithfulness defects |
| E-4 coverage-gap mapper | ci-tools fan-out (keep canonical in juniper-ml) | TAUDIT §6.1.1 (`:149`); "no per-file gate anywhere" (`:123-124`) |
| M-1 known_misses consult | anti-hallucination layer 4 / ledger (`known_misses.yaml:1-4`); RUBRIC R3 | companion catalog **M-1** |
| E-1 live-runtime Skill | **Appendix B** Skill-vs-subagent (`DOR:186,:539`); confirm-at-build (`:226-227`) | CANOPY §6.1.1 (`:116`); gap **A-2** |
| E-6 click-through author | n/a (new capability) | TAUDIT §6.1.3; canopy `src/tests/ui/`; canopy-only (`:89`) |
| E-8 app startup self-check | n/a (app-level; candidate `juniper-service-core` helper) | companion to gap **I-2**; the E-1 (gap **A-2**) Plan-B |
| S-1 ecosystem env-drift audit | n/a (downstream use of E-2) | CANOPY §6.2 S-1 (`:196-200`); TAUDIT §6.2 S-1 (`:207`) |
| OQ-2 datastore (REJECT) | **OQ-2** (`DOR:490`, "YAML for round 1; queryable store is future work") — **escalated** here to a hard reject (trigger moot: `generated_prompt_index.py`) | genesis "what NOT to build" |
| OQ-3 more agent types (DEFER) | **OQ-3** (`DOR:491`, "future rounds") | — |
| OQ-5 auto-invocation (DEFER) | **OQ-5** (`DOR:496`, "user-only initially") | — |

---

## 9. Open Questions for the Owner

1. **Near-term scope.** Is **Phase 1 alone** (PR-1..PR-4, with G-3 gated on PR-2) the approved near-term scope,
   with Phases 2 and 3 re-confirmed at their own gates? (Recommended.)
2. **E-1 shape.** Confirm E-1 is built **as a Skill, not a subagent**, and **staged** (Stage-0 throwaway
   feasibility spike with a kill-criterion before any committed runtime surface), with the §6.9 Plan-B as the
   kill-path fallback.
3. **E-7 shape.** Confirm E-7 is a **fold-in** to `prompt-validator` (strengthened R1.1 / new RUBRIC check),
   not a separate `intent-reviewer` subagent — promote to a standalone agent only if the fold-in proves
   insufficient.
4. **E-4 host + posture.** Confirm E-4 is hosted in **`juniper-ci-tools`** and ships **advisory-first**
   (exit 0), with promotion to a blocking per-file gate requiring separate per-repo owner sign-off.
5. **OQ resolutions.** Confirm **OQ-2 reject** (no DB backend — escalated from DOR "future work"), **OQ-5 keep
   user-only** (retain `disable-model-invocation: true`), and **OQ-3 defer** (no new agent types beyond
   E-5/E-7 now).
6. **D-1 staleness threshold.** Confirm the staleness signal is **HEAD-commit-time** (cache predating the
   current commit = `stale`) as the primary signal, with a configurable TTL secondary. If a fixed TTL is
   preferred instead, name the value (the bundle's existing `ttl_seconds=900` is the natural default).
7. **E-2 process ownership.** Confirm canopy adopts the E-2 checker as a **post-refactor reinstall check**
   (the tool is ml-owned; the process is canopy-owned).
8. **E-8 adoption (app-level).** Adopt the **app startup self-check** (E-8) — the automatic boot-time
   enforcement and primary E-1 Plan-B? If yes: canopy-only first, or as a shared `juniper-service-core` helper
   for the whole fleet? And do you want an escape-hatch env var?

---

## 10. Multi-Agent Validation Record (Phase 4)

This plan (iteration 1) was validated by **four independent sub-agents** — separate `Agent` calls, blind to one
another, each re-deriving from primary sources (the repo at HEAD `79a9eda`, the DOR, and the two dogfooding
analyses), one of them the **real `prompt-validator` subagent** returning its typed JSON verdict.
Anchor-grounding and convention/RUBRIC fidelity **passed**; the feasibility and completeness/risk lenses raised
**concerns**, all resolved in this iteration-2 revision.

| Lens | Verdict | Blockers / Majors | Resolution |
|------|---------|-------------------|------------|
| Anchor-grounding (real `prompt-validator` subagent, typed JSON) | **PASS** | 0 blocker / 0 major; ~25 anchors re-probed, all `grounded:true`; OPEN gaps confirmed open, CLOSED items confirmed fixed | minors (section-numbering, "+10" count, "clean" wording, citation range) folded into this revision |
| Feasibility / design soundness (general-purpose) | **CONCERNS** | MAJOR: E-3 under-scoped (validator re-probe stays CWD-relative) | resolved — E-3 widened to retarget the whole re-probe (`prompt-validator.md:80-89`) + a cross-repo dogfood criterion (Major #1) |
| Completeness / risk (adversarial skeptic + auditor pass) | **CONCERNS** | MAJORs: Phase-2 PR-5/PR-7 not independent; S-1 dropped; E-2 lacks an automatic enforcement hook; G-3 unguarded; Phase-1 over-claims the failure-class closure | resolved — PR-7 sequenced after PR-5; S-1 added; E-8 startup self-check added + E-1 Plan-B; G-3 guard test added; failure-class claims softened (Majors #2-5) |
| Convention / RUBRIC fidelity (general-purpose) | **PASS** | 0 blocker / major; 3 gates re-run green; R2.5 data-currency exemplary | minors (§10 numbering, M-1 new-ID drift guard + regex caveat, PR-6 AGENTS.md, stale `# this test is failing` comments) folded in |

**All majors resolved in iteration 2; no unresolved blocker/major remains.**

---

## 11. Approval Gate Statement

**Nothing in this plan is implemented until the owner explicitly approves this document.** Implementation
(Phase 6 of the enhancement effort) begins **only** on the owner's explicit approval, and **only** for the
approved scope (recommended: Phase 1 alone — PR-1..PR-4, with G-3 gated on PR-2). Each accepted unit then
proceeds as a single-work-unit PR under worktree isolation
(`/home/pcalnon/Development/python/Juniper/worktrees/`), **never merged to main without owner sign-off**, each
shipping its `tests/` gate + `ci.yml` line + `AGENTS.md` update in the same PR. This approval gate is the
natural **thread-handoff point**: the implementing thread starts fresh from the approved scope, verifying its
starting state with `git rev-parse --short HEAD` (expect a descendant of `79a9eda`),
`python util/agent_suite_doctor.py --json` (expect 6 OK / 1 WARN), and
`python util/prompt_discovery/cli.py --repo-root .` (expect exit 0, 7 probes ok except `test_status:
cold_cache`).
