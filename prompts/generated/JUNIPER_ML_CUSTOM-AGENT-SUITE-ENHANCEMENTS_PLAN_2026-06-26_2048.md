# Plan — Evaluate & Sequence Enhancements to the Juniper Custom-Agent Infrastructure

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Application**: juniper-ml — the custom-agent suite itself is the subject of this work
**Author**: Paul Calnon
**Prompt class**: `planning` (downstream deliverable = a `notes/` PLAN document; **implementation is gated on owner approval**)
**Source template**: `prompts/agent_templates/plan.md`
**Generated**: 2026-06-26

---

## Role

You are a principal engineer / architect for the Juniper ML platform, working **on the custom-agent
infrastructure itself** — the suite of Claude Code agents, the `template-agent` Skill, the template
library, the discovery/grounding layer, the data layer, and the supporting `util/`+`tests/` tooling
that lives in `juniper-ml`. You have the judgement to weigh options, trade-offs, and risks, and to
commit to a defensible plan — but you **do not implement anything** until the owner (Paul) approves the
plan document this prompt directs you to produce.

This effort is **recursive**: the subject under improvement is the very machinery used to author and
validate prompts. Dogfood it where fitting (use the `planner` subagent to author the plan, independent
subagents to validate it, the `task-executor` pattern to implement the approved scope), and let the
experience of using each component inform the enhancements you propose.

## Resources

> **Closed-world grounding rule.** The catalog below is a *starting* inventory captured 2026-06-26, not
> an authority. The **running code in this repo is the source of truth**; the `notes/` analyses reflect a
> point in time. **Re-derive and re-verify every claim from primary sources** (re-probe each path / symbol
> / flag / line) before you rely on it. Where a "known gap" is asserted below, confirm it is *still* open
> with a first-party probe; where a fix is asserted, confirm it actually landed. Do not invent anchors.
> Several candidates reference **sibling repos** (E-1/E-6 → `juniper-canopy/src/tests/ui/`, E-4 →
> `juniper-cascor-model`); those anchors will **not** be in this repo's single-repo discovery bundle — the
> very A-1 limitation under evaluation — so re-probe them first-party on the shared filesystem under
> `/home/pcalnon/Development/python/Juniper/`.

**Generate the grounding bundle first (hard gate — Phase 0):**

```bash
python util/prompt_discovery/cli.py --repo-root . \
  --subject "custom-agent suite enhancements" \
  --symbols "prompt_discovery,template_data_resolver,prompt-validator,template-agent,test_status" --json
# capture provenance.head_sha; if exit != 0, STOP and report (never proceed on an empty bundle)
python util/agent_suite_doctor.py --repo-root . --json   # current OK/WARN/FAIL health baseline (dogfood)
```

**The suite surface (verify each exists; cite file:line in the plan):**

- Agents — `.claude/agents/{planner,prompt-validator,auditor,task-executor}.md` (all pinned `model: opus`,
  `effort: max`; `task-executor` carries `isolation: worktree`).
- Skill — `.claude/skills/template-agent/SKILL.md` (`disable-model-invocation: true`, user-invoked,
  bounded state machine: ingest → discover(hard gate) → expand/ask → categorize/select → fill copy →
  validate(delegate to `prompt-validator`) → bounded loop (max 3) → emit to `prompts/generated/`).
- Template library — `prompts/agent_templates/`: `manifest.yaml` (registers 9 named templates + the
  always-match `generic` fallback = 10 ids total); `RUBRIC.md` (R1–R5; hard gates **R2.0** slot-completion# Plan — Evaluate & Sequence Enhancements to the Juniper Custom-Agent Infrastructure

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Application**: juniper-ml — the custom-agent suite itself is the subject of this work
**Author**: Paul Calnon
**Prompt class**: `planning` (downstream deliverable = a `notes/` PLAN document; **implementation is gated on owner approval**)
**Source template**: `prompts/agent_templates/plan.md`
**Generated**: 2026-06-26

---

## Role

You are a principal engineer / architect for the Juniper ML platform, working **on the custom-agent
infrastructure itself** — the suite of Claude Code agents, the `template-agent` Skill, the template
library, the discovery/grounding layer, the data layer, and the supporting `util/`+`tests/` tooling
that lives in `juniper-ml`. You have the judgement to weigh options, trade-offs, and risks, and to
commit to a defensible plan — but you **do not implement anything** until the owner (Paul) approves the
plan document this prompt directs you to produce.

This effort is **recursive**: the subject under improvement is the very machinery used to author and
validate prompts. Dogfood it where fitting (use the `planner` subagent to author the plan, independent
subagents to validate it, the `task-executor` pattern to implement the approved scope), and let the
experience of using each component inform the enhancements you propose.

## Resources

> **Closed-world grounding rule.** The catalog below is a *starting* inventory captured 2026-06-26, not
> an authority. The **running code in this repo is the source of truth**; the `notes/` analyses reflect a
> point in time. **Re-derive and re-verify every claim from primary sources** (re-probe each path / symbol
> / flag / line) before you rely on it. Where a "known gap" is asserted below, confirm it is *still* open
> with a first-party probe; where a fix is asserted, confirm it actually landed. Do not invent anchors.
> Several candidates reference **sibling repos** (E-1/E-6 → `juniper-canopy/src/tests/ui/`, E-4 →
> `juniper-cascor-model`); those anchors will **not** be in this repo's single-repo discovery bundle — the
> very A-1 limitation under evaluation — so re-probe them first-party on the shared filesystem under
> `/home/pcalnon/Development/python/Juniper/`.

**Generate the grounding bundle first (hard gate — Phase 0):**
**Generated**: 2026-06-26

  --symbols "prompt_discovery,template_data_resolver,prompt-validator,template-agent,test_status" --json
# capture provenance.head_sha; if exit != 0, STOP and report (never proceed on an empty bundle)
python util/agent_suite_doctor.py --repo-root . --json   # current OK/WARN/FAIL health baseline (dogfood)
```

**The suite surface (verify each exists; cite file:line in the plan):**

- Agents — `.claude/agents/{planner,prompt-validator,auditor,task-executor}.md` (all pinned `model: opus`,
  `effort: max`; `task-executor` carries `isolation: worktree`).
- Skill — `.claude/skills/template-agent/SKILL.md` (`disable-model-invocation: true`, user-invoked,
  bounded state machine: ingest → discover(hard gate) → expand/ask → categorize/select → fill copy →
  validate(delegate to `prompt-validator`) → bounded loop (max 3) → emit to `prompts/generated/`).
- Template library — `prompts/agent_templates/`: `manifest.yaml` (registers 9 named templates + the
  always-match `generic` fallback = 10 ids total); `RUBRIC.md` (R1–R5; hard gates **R2.0** slot-completion
  and **R3.4** anchor-grounding; **R2.5** convention fidelity validates injected values against the data
  layer); the template `.md` files; and the canonical skeleton (Role / Resources / Primary Objective /
  Assigned Tasks / Key Deliverables [+ Constraints / Finalize]).
- Data layer — `prompts/agent_templates/data/{standing_rules,anti_hallucination,conventions,ecosystem,known_misses}.yaml`.
- Discovery layer — `util/prompt_discovery/` (`cli.py`; probes `repo_context`, `test_status`, `file_probe`,
  `symbol_probe`, `dependency_facts`, `conventions`, `concurrency`; `symbol_overlay.py` Serena overlay).
- Convenience utilities — `util/{template_data_resolver,template_select_preview,scaffold_template,agent_suite_doctor,agent_suite_summary,generated_prompt_index}.py`, `util/install_agents.bash`.
- Gates — the suite's ~20 `tests/test_*.py` lint/behavioural tests (e.g. `test_template_library_drift`,
  `test_template_selection`, `test_prompt_validator_contract`, `test_template_agent_skill_lint`,
  `test_agents_frontmatter`, `test_template_data_resolver`, `test_prompt_discovery`, `test_symbol_overlay`,
  `test_agent_suite_doctor`, `test_agent_suite_summary`, `test_generated_prompt_index`,
  `test_scaffold_template`, `test_template_select_preview`, `test_agent_suite_path_drift`). **`prompts/**`
  and `util/**` are excluded from pre-commit**, so these unittests wired into `ci.yml` are the *sole* gate —
  the mechanism that let prose drift slip historically.

**The design & analysis record (read these in Phase 0):**

- `notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md` — **design-of-record** (D-1…D-6 decisions;
  OQ-1…OQ-8 open questions; the round-1/round-2 PR roadmap).
- `notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md` — convenience-utilities design (all 5 shipped).
- `notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` — genesis analysis (6 prompt types; "what NOT to build").
- `notes/JUNIPER_2026-06-26_JUNIPER-ML_TEST-SUITE-AUDIT-PROMPT-ANALYSIS.md` — dogfooding analysis (§6 gaps). **Read in full.**
- `notes/JUNIPER_2026-06-26_JUNIPER-CANOPY_DEBUG-PROMPT-ANALYSIS.md` — dogfooding analysis (§6 gaps, richest source). **Read in full.**

**Candidate enhancement catalog (starting point — re-verify status, then evaluate; NOT exhaustive, NOT authoritative):**

| ID | Candidate | Source (re-confirm) | Status @ 2026-06-26 |
|----|-----------|---------------------|---------------------|
| D-1 | `test_status` probe has no cache-freshness/TTL guard — a stale `lastfailed` masquerades as current (phantom "188 failing"). Stamp cache mtime; flag/`unavailable` past a TTL. | CANOPY §6.2 D-1; `util/prompt_discovery/test_status.py` | **OPEN (confirmed: no ttl/mtime logic)** |
| A-1 | Suite is single-repo by construction (`cli.py` + `prompt-validator` assume CWD==target; only `--repo-root`). Add a first-class `--target-repo` cross-repo mode. | CANOPY §6.2 A-1; TAUDIT §6.2 A-1; `util/prompt_discovery/cli.py:80` | **OPEN (confirmed: no --target-repo)** |
| A-2 | No live-runtime coverage — the suite cannot, by design, catch "green tests / dead app". | CANOPY §6.2 A-2; TAUDIT §6.2 A-2 | OPEN |
| I-2 | No env-floor-drift guard (the *actual* canopy incident): installed `juniper-*` wheels below `pyproject` floors. `editable_install_drift_check.py` only inspects *editable* installs; `dependency_facts` reads pins but never compares to the active interpreter. | CANOPY §6.1.2 / §6.2 I-2 | OPEN |
| E-1 | **Live-runtime / service-smoke diagnostician agent** (highest value overall): boot a service in its conda env, drive HTTP + UI via `chrome-devtools`/`playwright` MCP, tail logs, report live tracebacks file:line. Pairs with the `regressions` template. | CANOPY §6.1.1; TAUDIT §6.1 | proposed |
| E-2 | **Environment / dependency-drift checker** (tool, optionally agent-fronted) = the I-2 fix; natural extension of the `dependency_facts` probe. | CANOPY §6.1.2 | proposed |
| E-3 | **Cross-repo grounding mode** = the A-1 fix (or a cross-repo `prompt-validator` variant). | CANOPY §6.1.3 | proposed |
| E-4 | **Per-file coverage-gap mapper** (host in `juniper-ci-tools`, dogfood test in `juniper-ml/tests/`; carry the numpy-2.x dotted-`--cov` workaround). | TAUDIT §6.1.1 | proposed |
| E-5 | **Mocked-seam gap auditor** (novel `auditor` variant): hunt autouse/session fixtures that mock an integration boundary, leaving the real construction/call path untested. | TAUDIT §6.1.2 | proposed |
| E-6 | **Click-through test author**: generate Playwright tests modeled on canopy's `src/tests/ui/` harness. | TAUDIT §6.1.3 | proposed |
| OQ-2 | Persistent/queryable prompt datastore (vs. today's YAML). GEN's "what NOT to build" cautions against a DB backend — weigh carefully. | DOR §10 OQ-2; GEN | deferred |
| OQ-3 | Additional agent types (Infrastructure / Review / Refactor / Test / Documentation). | DOR §10 OQ-3 | deferred |
| OQ-5 | `/template-agent` auto-invocation (currently user-only) — revisit after dogfooding. | DOR §10 OQ-5 | open |
| OQ-7 | Verify `.gitignore` negations don't un-ignore session cruft. | DOR §10 OQ-7 | open (verify-at-build) |
| GEN-x | Genesis unbuilt ideas: prompt index, handoff auto-generator. | GEN | unbuilt |
| M-1 | Anti-hallucination feedback loop under-exercised: `known_misses.yaml` holds ~1 entry; no routine that appends new misses. | DOR §5.8; `data/known_misses.yaml` | observation |
| G-1 | Dead `prompts/templates/` path drift. **The two emphasized analyses disagree:** CANOPY §6.2 I-1 reports it fixed in PR #566 (+ guard `tests/test_agent_suite_path_drift.py`); TAUDIT §6.2 I-1 *re-hit* it in agent/rubric **prose** after that fix claim ("two independent sessions"). Verify the prose sweep is complete — `prompt-validator` body, `RUBRIC.md` R2.5 text, `AGENTS.md` — not merely that the guard test exists. | CANOPY §6.2 I-1; TAUDIT §6.2 I-1 | **likely FIXED — re-verify prose, not just guard** |
| G-2 | Already fixed — stale `ecosystem.yaml` conda envs (PR #566). **Confirm currency vs live envs.** | CANOPY §6.2 C-1; `data/ecosystem.yaml:21-23` | **FIXED (verify)** |
| G-3 | `AGENTS.md` "Repository Structure" tree stale: still labels the template dir `templates/` (real: `prompts/agent_templates/`, `AGENTS.md:188`) and omits the present top-level `conf/`+`papers/` dirs and the in-tree packaged sub-modules. Folds into the G-1 prose sweep. | TAUDIT §6.2 (Configuration problems) | **OPEN (confirmed)** |

**Conventions** (from `prompts/agent_templates/data/conventions.yaml` + the parent/`AGENTS.md`): line-length 512;
canonical 6-field file headers; worktree isolation under `/home/pcalnon/Development/python/Juniper/worktrees/`;
one PR per work unit; **never merge to `main` (owner approves merges)**; never delete/disable/weaken a test;
PR descriptions carry `JR-…` requirement cross-refs; thread-handoff (not compaction) at 95–99% context.

## Primary Objective

Investigate the current state of the Juniper custom-agent infrastructure, **evaluate a prioritized set of
enhancements** to it (grounded in the two 2026-06-26 dogfooding analyses, the design-of-record's open
questions, and the platform's real Claude Code capabilities), and produce **one owner-actionable PLAN
document** in `notes/` that sequences the accepted enhancements as single-work-unit steps. **Every aspect
of that plan must be independently vetted and validated by multiple, independent sub-agents** before it is
presented. **Implementation is gated on Paul's explicit approval of the plan document** — produce no
production code, configuration, or PRs until that approval is given.

## Assigned Tasks / Directives

Execute the phases in order. Phases 0–5 are **document-and-analysis only**; Phase 6 is reached **only after
owner approval**.

### Phase 0 — Ground (hard gate)

1. Generate the discovery bundle and the `agent_suite_doctor` health baseline (commands in *Resources*).
   If discovery fails, STOP and report — never proceed on an empty/partial bundle. Record `head_sha`; if
   HEAD moves later, re-discover.
2. Read the five design/analysis docs listed in *Resources* (the two dogfooding analyses **in full**).
3. Re-confirm the recently-fixed items (G-1, G-2) are still clean by first-party probe.

### Phase 1 — Investigation & analysis

4. **Verify, don't re-derive.** Confirm the suite inventory in *Resources* against the running code; captu
**Generated**: 2026-06-26
ll
   open (or already addressed) with a command + result, not a citation to the notes. You may delegate breadth
   to read-only `Explore` / `general-purpose` / `auditor` sub-agents (give each a bounded, self-contained
   scope and require file:line evidence).
6. **Assess effectiveness against current platform capability.** Use `context7` / `WebFetch` / the
   `claude-code-guide` agent to ground proposed mechanisms against *current* Claude Code features (subagents,
   Skills, `disable-model-invocation`, `allowed-tools`, model/effort frontmatter, MCP access, nested-subagent
   fan-out caveats). Flag any suite component using a stale or sub-optimal pattern, and any proposed
   enhancement that the platform does **not** actually support.
7. Produce a **current-state map + a validated gap/opportunity ledger**: for each item — id, one-line
   description, first-party evidence (`file:line` / `notes:line` + probe result), severity, open/fixed,
   likely owner repo, and the failure-class it addresses (esp. the "green tests / dead app" class the suite
   cannot currently see).

### Phase 2 — Enhancement evaluation & prioritization

8. For **each** candidate (catalog + anything Phase 1 surfaces), evaluate across: **value** (which failure
   class / friction it removes), **feasibility** (platform support; build cost), **blast radius / risk**,
   **dependencies**, **dogfood/test story** (how it is gated, given `prompts/**`+`util/**` are
   pre-commit-excluded), and **owner**. Explicitly mark each **in-scope / out-of-scope / deferred** with a
   reason.
9. Use **multiple, independent sub-agents with distinct lenses** for this evaluation (e.g. one scoring
   value, one scoring feasibility-against-the-platform, one scoring risk), launched as separate Agent calls
   with no shared scratchpad, then reconcile divergence yourself. Be willing to recommend **against** a
   candidate (e.g. weigh OQ-2's queryable datastore against GEN's "what NOT to build").
10. Produce a **ranked, scoped enhancement set** with rationale for the ordering and the cut line. Bias the
    **near-term** cut line toward a few cheap, contained, highest-value units (e.g. the D-1 `test_status` TTL
    fix and the I-2/E-2 env-floor-drift guard are low-risk wins); explicitly **defer** large builds (e.g. the
    E-1 live-runtime diagnostician) to later rounds rather than designing all candidates in depth at once.

### Phase 3 — Planning (author the plan document)

11. Author **one** document via the `planner` subagent (or directly, following its contract), written to
    `notes/` with the canonical name `JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_<YYYY-MM-DD>.md` (TYPE =
    PLAN; use the session's actual date); refuse and report if the path already exists. It must contain:
    - the current-state map + validated gap/opportunity ledger (Phase 1);
    - the ranked, scoped enhancement set (Phase 2) with explicit in/out/deferred;
    - **per accepted enhancement**: design sketch, affected files (`file:line`), test/dogfood plan + the
      `tests/` gate it ships with, acceptance criteria, risk + rollback, owner repo, and JR-ID(s) if known;
    - a **phased, single-work-unit PR sequence** (the DOR round model) with a dependency graph;
    - cross-references to DOR `D-#`/`OQ-#` and the two analyses' gap IDs;
    - an **Open Questions for the owner** section;
    - the Phase-4 validation record (added in Phase 4);
    - an explicit statement that **nothing is implemented until the owner approves this document**.
12. Cite only real anchors present in the grounding bundle / first-party probes. No invented paths, symbols,
    flags, versions, or ports.

### Phase 4 — Independent multi-agent validation of the plan (mandatory)

13. Subject **every aspect** of the plan to **at least three independent sub-agents**, each a *separate*
    Agent invocation, each blind to the others' conclusions, each re-deriving from primary sources — at
    minimum these distinct lenses:
    - **Grounding / correctness** — delegate to the **actual `prompt-validator` subagent** (it returns a
      pinned typed JSON verdict): independently re-probe every `file:line` / symbol / flag / version / path
      the plan asserts; confirm each "open" gap is open and each "fixed" item is fixed; flag any unverifiable
      claim. (Add an `auditor` pass for evidence the validator's schema does not capture.)
    - **Feasibility / design soundness**: does each proposed enhancement actually work given Claude Code's
      real capabilities and the suite's contracts (RUBRIC, discovery hard-gate, bounded loop, nested-fan-out
      caveat)? Are the test/dogfood stories real and CI-wireable?
    - **Completeness / risk (adversarial skeptic)**: what is missing? Does the plan close the failure classes
      it claims? Are sequencing, dependencies, blast radius, and the cut line right? Is any item net-negative
      or premature?
    - *(recommended fourth)* **Convention / RUBRIC fidelity**: worktrees, one-PR-per-unit, no test weakening,
      data-layer currency (R2.5), line-length 512, JR-IDs — and would artifacts the plan generates pass the
      RUBRIC?
14. Each validator returns a structured verdict (`PASS` / `CONCERNS` / `FAIL` + findings with reproducible
    evidence). **Reconcile**: resolve or explicitly accept-with-rationale every blocker/major; revise the
    plan; re-validate the changed parts. **Record the full validation iteration history in the plan** (the
    suite's honest-record convention). Do not declare the plan ready while any unresolved blocker/major
    stands.

### Phase 5 — APPROVAL GATE (STOP)

15. **STOP here.** Present to Paul: the plan document path, an executive summary (proposed scope + ordering,
    the cut line and why, the independent-validation verdicts and how each concern was resolved, and the open
    questions), and the current git status/branch. **Do not begin Phase 6 until Paul replies with explicit
    approval.** If Paul approves only part of the scope, only that part is authorized. Treat this gate as the
    natural **thread-handoff** point — expect Phase 6 to run as a fresh session seeded by the approved plan
    (per the project's thread-handoff procedure), not a continuation of a near-exhausted context.

### Phase 6 — Implementation (ONLY after owner approval)

16. For the **approved scope only**, implement via the `task-executor` pattern: a dedicated git worktree
    under the centralized location, a `feature/…` or `fix/…` branch, **one PR per work unit**, grounded in
    the real repo. Run the repo's **actual** tests + lint + pre-commit; **ship a `tests/` gate with every new
    `util/` tool** (since `util/**`/`prompts/**` are pre-commit-excluded); **never weaken or delete a test**.
    Dogfood after each change (`agent_suite_doctor.py`; the drift tests). Update the data layer (and append to
    `known_misses.yaml`) where the change warrants it. **Open PRs; never merge — Paul approves all merges and
    any PyPI/deploy gates.** Re-verify each change and report PR URLs + a verification summary.

## Key Deliverables & Requirements

1. A captured, HEAD-pinned discovery bundle and an `agent_suite_doctor` baseline (Phase 0).
2. A current-state map + **validated** gap/opportunity ledger, every item carrying first-party evidence
   (Phase 1).
3. A ranked, scoped enhancement evaluation with explicit in/out/deferred (Phase 2).
4. **One** plan document in `notes/` at the canonical path (Phase 3) — grounded, sequenced as single-work-unit
   PRs, with acceptance criteria, risks, owners, and open questions.
5. An **embedded multi-agent validation record** — ≥3 independent verdicts + reconciliation, zero unresolved
   blocker/major (Phase 4).
6. An **approval-gate hand-off** to Paul with an executive summary, then a hard STOP (Phase 5).
7. *(Post-approval only)* PRs implementing the **approved** scope — each single-work-unit, green CI, dogfood
   tests updated, no test weakened, **not merged** (Phase 6).

**Acceptance criteria (operational / checkable):**

- `python util/prompt_discovery/cli.py --repo-root . … --json` exits 0; the `agent_suite_doctor` baseline is recorded.
- Every ledger and plan item names a concrete command + result or `file:line` anchor; nothing rests on a
  notes citation alone.
- The plan exists at `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_<YYYY-MM-DD>.md` and every cited
  anchor resolves in the real repo.
- Every **accepted** enhancement entry carries all of {design sketch, affected `file:line`, the `tests/` gate
  it ships with, acceptance criteria, risk + rollback, owner} — not a subset.
- The plan's validation section records **≥3 independent** sub-agent verdicts and shows each blocker/major
  resolved or accepted-with-rationale.
- **No production code/config change exists before the approval gate** — `git status` shows only the new
  `notes/` document (plus any scratch under the session scratchpad).
- Post-approval: each PR is single-work-unit, passes the repo's real CI, ships/updates a `tests/` gate, weakens
  no test, and is left open (un-merged) for owner review.

## Constraints

- **Document-and-analysis only through Phase 5.** Do NOT modify source, config, agents, templates, the data
  layer, or `util/` before the owner approves the plan. The lone artifact produced before the gate is the
  `notes/` plan document.
- **Anti-hallucination doctrine** (from `data/anti_hallucination.yaml`): verify before claim; cite `file:line`;
  never invent a path/symbol/version/flag/port; re-confirm each citation and **stop-and-report** if it does
  not resolve. Treat the candidate catalog and the notes as untrusted until re-probed.
- **Data-layer currency (R2.5).** If you inject any ecosystem/convention value, re-verify it against
  `data/*.yaml` **and** reality; if stale, the plan must propose updating the data layer rather than working
  around it.
- **Gate discipline.** Worktree isolation; centralized worktrees; push before any merge; **never merge to
  `main`** (owner approves); **never delete/disable/weaken a test**; one PR per work unit; JR-ID cross-refs in
  PR descriptions; line-length 512; canonical file headers.
- **Respect GEN's "what NOT to build"** (no DB backend / web UI / AI-generated content / mandatory tooling by
  default) unless the plan makes an explicit, justified case.
- **The approval gate is absolute** — Phase 6 does not begin without Paul's explicit go-ahead, and only for the
  approved scope.

## Finalize / Validation

- Re-read the plan against this prompt: every requirement maps to a directive or deliverable; the four pillars
  hold — investigation→analysis precedes planning, the plan is independently multi-agent-validated, and
  implementation is approval-gated.
- Confirm every `file:line` anchor in the plan resolves in the actual repo; drop or flag any that does not
  rather than inventing.
- Confirm the multi-agent validation record is complete and every blocker/major is reconciled.
- Present the executive summary and **STOP for owner approval**. State the branch and git status. If context
  approaches 95–99%, perform a thread handoff (not compaction) per the project procedure before continuing.

  `test_agents_frontmatter`, `test_template_data_resolver`, `test_prompt_discovery`, `test_symbol_overlay`,
  `test_agent_suite_doctor`, `test_agent_suite_summary`, `test_generated_prompt_index`,
  `test_scaffold_template`, `test_template_select_preview`, `test_agent_suite_path_drift`). **`prompts/**`
  and `util/**` are excluded from pre-commit**, so these unittests wired into `ci.yml` are the *sole* gate —
  the mechanism that let prose drift slip historically.

**The design & analysis record (read these in Phase 0):**

- `notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md` — **design-of-record** (D-1…D-6 decisions;
  OQ-1…OQ-8 open questions; the round-1/round-2 PR roadmap).
- `notes/JUNIPER_2026-06-25_JUNIPER-ML_AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md` — convenience-utilities design (all 5 shipped).
- `notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` — genesis analysis (6 prompt types; "what NOT to build").
- `notes/JUNIPER_2026-06-26_JUNIPER-ML_TEST-SUITE-AUDIT-PROMPT-ANALYSIS.md` — dogfooding analysis (§6 gaps). **Read in full.**
- `notes/JUNIPER_2026-06-26_JUNIPER-CANOPY_DEBUG-PROMPT-ANALYSIS.md` — dogfooding analysis (§6 gaps, richest source). **Read in full.**

**Candidate enhancement catalog (starting point — re-verify status, then evaluate; NOT exhaustive, NOT authoritative):**

| ID | Candidate | Source (re-confirm) | Status @ 2026-06-26 |
|----|-----------|---------------------|---------------------|
| D-1 | `test_status` probe has no cache-freshness/TTL guard — a stale `lastfailed` masquerades as current (phantom "188 failing"). Stamp cache mtime; flag/`unavailable` past a TTL. | CANOPY §6.2 D-1; `util/prompt_discovery/test_status.py` | **OPEN (confirmed: no ttl/mtime logic)** |
| A-1 | Suite is single-repo by construction (`cli.py` + `prompt-validator` assume CWD==target; only `--repo-root`). Add a first-class `--target-repo` cross-repo mode. | CANOPY §6.2 A-1; TAUDIT §6.2 A-1; `util/prompt_discovery/cli.py:80` | **OPEN (confirmed: no --target-repo)** |
| A-2 | No live-runtime coverage — the suite cannot, by design, catch "green tests / dead app". | CANOPY §6.2 A-2; TAUDIT §6.2 A-2 | OPEN |
| I-2 | No env-floor-drift guard (the *actual* canopy incident): installed `juniper-*` wheels below `pyproject` floors. `editable_install_drift_check.py` only inspects *editable* installs; `dependency_facts` reads pins but never compares to the active interpreter. | CANOPY §6.1.2 / §6.2 I-2 | OPEN |
| E-1 | **Live-runtime / service-smoke diagnostician agent** (highest value overall): boot a service in its conda env, drive HTTP + UI via `chrome-devtools`/`playwright` MCP, tail logs, report live tracebacks file:line. Pairs with the `regressions` template. | CANOPY §6.1.1; TAUDIT §6.1 | proposed |
| E-2 | **Environment / dependency-drift checker** (tool, optionally agent-fronted) = the I-2 fix; natural extension of the `dependency_facts` probe. | CANOPY §6.1.2 | proposed |
| E-3 | **Cross-repo grounding mode** = the A-1 fix (or a cross-repo `prompt-validator` variant). | CANOPY §6.1.3 | proposed |
| E-4 | **Per-file coverage-gap mapper** (host in `juniper-ci-tools`, dogfood test in `juniper-ml/tests/`; carry the numpy-2.x dotted-`--cov` workaround). | TAUDIT §6.1.1 | proposed |
| E-5 | **Mocked-seam gap auditor** (novel `auditor` variant): hunt autouse/session fixtures that mock an integration boundary, leaving the real construction/call path untested. | TAUDIT §6.1.2 | proposed |
| E-6 | **Click-through test author**: generate Playwright tests modeled on canopy's `src/tests/ui/` harness. | TAUDIT §6.1.3 | proposed |
| OQ-2 | Persistent/queryable prompt datastore (vs. today's YAML). GEN's "what NOT to build" cautions against a DB backend — weigh carefully. | DOR §10 OQ-2; GEN | deferred |
| OQ-3 | Additional agent types (Infrastructure / Review / Refactor / Test / Documentation). | DOR §10 OQ-3 | deferred |
| OQ-5 | `/template-agent` auto-invocation (currently user-only) — revisit after dogfooding. | DOR §10 OQ-5 | open |
| OQ-7 | Verify `.gitignore` negations don't un-ignore session cruft. | DOR §10 OQ-7 | open (verify-at-build) |
| GEN-x | Genesis unbuilt ideas: prompt index, handoff auto-generator. | GEN | unbuilt |
| M-1 | Anti-hallucination feedback loop under-exercised: `known_misses.yaml` holds ~1 entry; no routine that appends new misses. | DOR §5.8; `data/known_misses.yaml` | observation |
| G-1 | Dead `prompts/templates/` path drift. **The two emphasized analyses disagree:** CANOPY §6.2 I-1 reports it fixed in PR #566 (+ guard `tests/test_agent_suite_path_drift.py`); TAUDIT §6.2 I-1 *re-hit* it in agent/rubric **prose** after that fix claim ("two independent sessions"). Verify the prose sweep is complete — `prompt-validator` body, `RUBRIC.md` R2.5 text, `AGENTS.md` — not merely that the guard test exists. | CANOPY §6.2 I-1; TAUDIT §6.2 I-1 | **likely FIXED — re-verify prose, not just guard** |
| G-2 | Already fixed — stale `ecosystem.yaml` conda envs (PR #566). **Confirm currency vs live envs.** | CANOPY §6.2 C-1; `data/ecosystem.yaml:21-23` | **FIXED (verify)** |
| G-3 | `AGENTS.md` "Repository Structure" tree stale: still labels the template dir `templates/` (real: `prompts/agent_templates/`, `AGENTS.md:188`) and omits the present top-level `conf/`+`papers/` dirs and the in-tree packaged sub-modules. Folds into the G-1 prose sweep. | TAUDIT §6.2 (Configuration problems) | **OPEN (confirmed)** |

**Conventions** (from `prompts/agent_templates/data/conventions.yaml` + the parent/`AGENTS.md`): line-length 512;
canonical 6-field file headers; worktree isolation under `/home/pcalnon/Development/python/Juniper/worktrees/`;
one PR per work unit; **never merge to `main` (owner approves merges)**; never delete/disable/weaken a test;
PR descriptions carry `JR-…` requirement cross-refs; thread-handoff (not compaction) at 95–99% context.

## Primary Objective

Investigate the current state of the Juniper custom-agent infrastructure, **evaluate a prioritized set of
enhancements** to it (grounded in the two 2026-06-26 dogfooding analyses, the design-of-record's open
questions, and the platform's real Claude Code capabilities), and produce **one owner-actionable PLAN
document** in `notes/` that sequences the accepted enhancements as single-work-unit steps. **Every aspect
of that plan must be independently vetted and validated by multiple, independent sub-agents** before it is
presented. **Implementation is gated on Paul's explicit approval of the plan document** — produce no
production code, configuration, or PRs until that approval is given.

## Assigned Tasks / Directives

Execute the phases in order. Phases 0–5 are **document-and-analysis only**; Phase 6 is reached **only after
owner approval**.

### Phase 0 — Ground (hard gate)

1. Generate the discovery bundle and the `agent_suite_doctor` health baseline (commands in *Resources*).
   If discovery fails, STOP and report — never proceed on an empty/partial bundle. Record `head_sha`; if
   HEAD moves later, re-discover.
2. Read the five design/analysis docs listed in *Resources* (the two dogfooding analyses **in full**).
3. Re-confirm the recently-fixed items (G-1, G-2) are still clean by first-party probe.

### Phase 1 — Investigation & analysis

4. **Verify, don't re-derive.** Confirm the suite inventory in *Resources* against the running code; capture
   concrete `file:line` anchors for every component you will reason about. Note any drift from `AGENTS.md`.
5. **Re-probe every OPEN candidate (D-1, A-1, A-2, I-2, OQ-5, OQ-7, M-1) first-party** — prove each is still
   open (or already addressed) with a command + result, not a citation to the notes. You may delegate breadth
   to read-only `Explore` / `general-purpose` / `auditor` sub-agents (give each a bounded, self-contained
   scope and require file:line evidence).
6. **Assess effectiveness against current platform capability.** Use `context7` / `WebFetch` / the
   `claude-code-guide` agent to ground proposed mechanisms against *current* Claude Code features (subagents,
   Skills, `disable-model-invocation`, `allowed-tools`, model/effort frontmatter, MCP access, nested-subagent
   fan-out caveats). Flag any suite component using a stale or sub-optimal pattern, and any proposed
   enhancement that the platform does **not** actually support.
7. Produce a **current-state map + a validated gap/opportunity ledger**: for each item — id, one-line
   description, first-party evidence (`file:line` / `notes:line` + probe result), severity, open/fixed,
   likely owner repo, and the failure-class it addresses (esp. the "green tests / dead app" class the suite
   cannot currently see).

### Phase 2 — Enhancement evaluation & prioritization

8. For **each** candidate (catalog + anything Phase 1 surfaces), evaluate across: **value** (which failure
   class / friction it removes), **feasibility** (platform support; build cost), **blast radius / risk**,
   **dependencies**, **dogfood/test story** (how it is gated, given `prompts/**`+`util/**` are
   pre-commit-excluded), and **owner**. Explicitly mark each **in-scope / out-of-scope / deferred** with a
   reason.
9. Use **multiple, independent sub-agents with distinct lenses** for this evaluation (e.g. one scoring
   value, one scoring feasibility-against-the-platform, one scoring risk), launched as separate Agent calls
   with no shared scratchpad, then reconcile divergence yourself. Be willing to recommend **against** a
   candidate (e.g. weigh OQ-2's queryable datastore against GEN's "what NOT to build").
10. Produce a **ranked, scoped enhancement set** with rationale for the ordering and the cut line. Bias the
    **near-term** cut line toward a few cheap, contained, highest-value units (e.g. the D-1 `test_status` TTL
    fix and the I-2/E-2 env-floor-drift guard are low-risk wins); explicitly **defer** large builds (e.g. the
    E-1 live-runtime diagnostician) to later rounds rather than designing all candidates in depth at once.

### Phase 3 — Planning (author the plan document)

11. Author **one** document via the `planner` subagent (or directly, following its contract), written to
    `notes/` with the canonical name `JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_<YYYY-MM-DD>.md` (TYPE =
    PLAN; use the session's actual date); refuse and report if the path already exists. It must contain:
    - the current-state map + validated gap/opportunity ledger (Phase 1);
    - the ranked, scoped enhancement set (Phase 2) with explicit in/out/deferred;
    - **per accepted enhancement**: design sketch, affected files (`file:line`), test/dogfood plan + the
      `tests/` gate it ships with, acceptance criteria, risk + rollback, owner repo, and JR-ID(s) if known;
    - a **phased, single-work-unit PR sequence** (the DOR round model) with a dependency graph;
    - cross-references to DOR `D-#`/`OQ-#` and the two analyses' gap IDs;
    - an **Open Questions for the owner** section;
    - the Phase-4 validation record (added in Phase 4);
    - an explicit statement that **nothing is implemented until the owner approves this document**.
12. Cite only real anchors present in the grounding bundle / first-party probes. No invented paths, symbols,
    flags, versions, or ports.

### Phase 4 — Independent multi-agent validation of the plan (mandatory)

13. Subject **every aspect** of the plan to **at least three independent sub-agents**, each a *separate*
    Agent invocation, each blind to the others' conclusions, each re-deriving from primary sources — at
    minimum these distinct lenses:
    - **Grounding / correctness** — delegate to the **actual `prompt-validator` subagent** (it returns a
      pinned typed JSON verdict): independently re-probe every `file:line` / symbol / flag / version / path
      the plan asserts; confirm each "open" gap is open and each "fixed" item is fixed; flag any unverifiable
      claim. (Add an `auditor` pass for evidence the validator's schema does not capture.)
    - **Feasibility / design soundness**: does each proposed enhancement actually work given Claude Code's
      real capabilities and the suite's contracts (RUBRIC, discovery hard-gate, bounded loop, nested-fan-out
      caveat)? Are the test/dogfood stories real and CI-wireable?
    - **Completeness / risk (adversarial skeptic)**: what is missing? Does the plan close the failure classes
      it claims? Are sequencing, dependencies, blast radius, and the cut line right? Is any item net-negative
      or premature?
    - *(recommended fourth)* **Convention / RUBRIC fidelity**: worktrees, one-PR-per-unit, no test weakening,
      data-layer currency (R2.5), line-length 512, JR-IDs — and would artifacts the plan generates pass the
      RUBRIC?
14. Each validator returns a structured verdict (`PASS` / `CONCERNS` / `FAIL` + findings with reproducible
    evidence). **Reconcile**: resolve or explicitly accept-with-rationale every blocker/major; revise the
    plan; re-validate the changed parts. **Record the full validation iteration history in the plan** (the
    suite's honest-record convention). Do not declare the plan ready while any unresolved blocker/major
    stands.

### Phase 5 — APPROVAL GATE (STOP)

15. **STOP here.** Present to Paul: the plan document path, an executive summary (proposed scope + ordering,
    the cut line and why, the independent-validation verdicts and how each concern was resolved, and the open
    questions), and the current git status/branch. **Do not begin Phase 6 until Paul replies with explicit
    approval.** If Paul approves only part of the scope, only that part is authorized. Treat this gate as the
    natural **thread-handoff** point — expect Phase 6 to run as a fresh session seeded by the approved plan
    (per the project's thread-handoff procedure), not a continuation of a near-exhausted context.

### Phase 6 — Implementation (ONLY after owner approval)

16. For the **approved scope only**, implement via the `task-executor` pattern: a dedicated git worktree
    under the centralized location, a `feature/…` or `fix/…` branch, **one PR per work unit**, grounded in
    the real repo. Run the repo's **actual** tests + lint + pre-commit; **ship a `tests/` gate with every new
    `util/` tool** (since `util/**`/`prompts/**` are pre-commit-excluded); **never weaken or delete a test**.
    Dogfood after each change (`agent_suite_doctor.py`; the drift tests). Update the data layer (and append to
    `known_misses.yaml`) where the change warrants it. **Open PRs; never merge — Paul approves all merges and
    any PyPI/deploy gates.** Re-verify each change and report PR URLs + a verification summary.

## Key Deliverables & Requirements

1. A captured, HEAD-pinned discovery bundle and an `agent_suite_doctor` baseline (Phase 0).
2. A current-state map + **validated** gap/opportunity ledger, every item carrying first-party evidence
   (Phase 1).
3. A ranked, scoped enhancement evaluation with explicit in/out/deferred (Phase 2).
4. **One** plan document in `notes/` at the canonical path (Phase 3) — grounded, sequenced as single-work-unit
   PRs, with acceptance criteria, risks, owners, and open questions.
5. An **embedded multi-agent validation record** — ≥3 independent verdicts + reconciliation, zero unresolved
   blocker/major (Phase 4).
6. An **approval-gate hand-off** to Paul with an executive summary, then a hard STOP (Phase 5).
7. *(Post-approval only)* PRs implementing the **approved** scope — each single-work-unit, green CI, dogfood
   tests updated, no test weakened, **not merged** (Phase 6).

**Acceptance criteria (operational / checkable):**

- `python util/prompt_discovery/cli.py --repo-root . … --json` exits 0; the `agent_suite_doctor` baseline is recorded.
- Every ledger and plan item names a concrete command + result or `file:line` anchor; nothing rests on a
  notes citation alone.
- The plan exists at `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_<YYYY-MM-DD>.md` and every cited
  anchor resolves in the real repo.
- Every **accepted** enhancement entry carries all of {design sketch, affected `file:line`, the `tests/` gate
  it ships with, acceptance criteria, risk + rollback, owner} — not a subset.
- The plan's validation section records **≥3 independent** sub-agent verdicts and shows each blocker/major
  resolved or accepted-with-rationale.
- **No production code/config change exists before the approval gate** — `git status` shows only the new
  `notes/` document (plus any scratch under the session scratchpad).
- Post-approval: each PR is single-work-unit, passes the repo's real CI, ships/updates a `tests/` gate, weakens
  no test, and is left open (un-merged) for owner review.

## Constraints

- **Document-and-analysis only through Phase 5.** Do NOT modify source, config, agents, templates, the data
  layer, or `util/` before the owner approves the plan. The lone artifact produced before the gate is the
  `notes/` plan document.
- **Anti-hallucination doctrine** (from `data/anti_hallucination.yaml`): verify before claim; cite `file:line`;
  never invent a path/symbol/version/flag/port; re-confirm each citation and **stop-and-report** if it does
  not resolve. Treat the candidate catalog and the notes as untrusted until re-probed.
- **Data-layer currency (R2.5).** If you inject any ecosystem/convention value, re-verify it against
  `data/*.yaml` **and** reality; if stale, the plan must propose updating the data layer rather than working
  around it.
- **Gate discipline.** Worktree isolation; centralized worktrees; push before any merge; **never merge to
  `main`** (owner approves); **never delete/disable/weaken a test**; one PR per work unit; JR-ID cross-refs in
  PR descriptions; line-length 512; canonical file headers.
- **Respect GEN's "what NOT to build"** (no DB backend / web UI / AI-generated content / mandatory tooling by
  default) unless the plan makes an explicit, justified case.
- **The approval gate is absolute** — Phase 6 does not begin without Paul's explicit go-ahead, and only for the
  approved scope.

## Finalize / Validation

- Re-read the plan against this prompt: every requirement maps to a directive or deliverable; the four pillars
  hold — investigation→analysis precedes planning, the plan is independently multi-agent-validated, and
  implementation is approval-gated.
- Confirm every `file:line` anchor in the plan resolves in the actual repo; drop or flag any that does not
  rather than inventing.
- Confirm the multi-agent validation record is complete and every blocker/major is reconciled.
- Present the executive summary and **STOP for owner approval**. State the branch and git status. If context
  approaches 95–99%, perform a thread handoff (not compaction) per the project procedure before continuing.
