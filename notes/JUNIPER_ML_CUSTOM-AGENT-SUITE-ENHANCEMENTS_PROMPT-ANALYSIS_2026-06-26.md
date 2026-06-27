# Prompt-Development Analysis — Custom-Agent Suite Enhancement-Evaluation Plan

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**Document Type**: ANALYSIS (prompt development + meta-analysis)
**Status**: Complete
**Last Updated**: 2026-06-27

---

## 1. Purpose

This session was asked to **develop a prompt** (not to perform the work) that will start a future session
whose deliverable is a **rigorous, multi-agent-validated plan to evaluate enhancements to the Juniper
custom-agent infrastructure** — the suite of agents, the `template-agent` Skill, the template library, the
discovery/grounding layer, the data layer, and the supporting `util/`+`tests/` tooling that lives in
`juniper-ml`.

The owner's constraints on the prompt: the downstream work must **begin with an investigatory / analysis
phase**, then a **planning phase**; **every aspect of the plan must be vetted and validated by multiple,
independent sub-agents**; and **implementation must be gated on the owner's approval of the planning
document**. The owner directed particular attention to the two most-recent dogfooding analyses
(`notes/JUNIPER_ML_TEST_SUITE_AUDIT_PROMPT_ANALYSIS_2026-06-26.md` and
`notes/JUNIPER_CANOPY_DEBUG-PROMPT_ANALYSIS_2026-06-26.md`). Custom agents were to be employed as needed,
and a meta-analysis was to record additional helpful agent specializations and any other Juniper issues
discovered.

**Deliverables produced this session:**

1. **The prompt (primary):** `prompts/generated/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-26_2048.md`
   — a planning-class prompt modeled on `prompts/agent_templates/plan.md`, fully grounded, validated PASS.
2. **This analysis document** (session record + the candidate-enhancement catalog the prompt grounds
   against + meta-analysis).

---

## 2. The primary deliverable and its validation

- **Template selected:** `plan` (`prompts/agent_templates/plan.md`, `class: planning`,
  `required_fields: [subject, resources]`). Rationale: the downstream deliverable is a **planning document**
  (an enhancement-evaluation plan), not code and not a findings report; implementation is explicitly deferred
  behind an approval gate. Planning-class also correctly exempts the prompt from RUBRIC **R2.6** (the
  verify-&-recover contract is for execution-class prompts that change code). Candidates rejected: `audit`
  (analysis-class, but it produces a *findings report*, whereas the task wants a *forward plan*);
  `implement-plan` / `task` (execution-class — but there is no ratified plan yet to execute);
  `regressions` / `failing-tests` (no regression symptom; the suite tests are green).
- **Grounding:** a real discovery bundle was generated for the `juniper-ml` worktree
  (`python util/prompt_discovery/cli.py --repo-root . --json`; on-HEAD `b76658a`, `dirty: true` — the new
  prompt file was uncommitted — all seven probes `ok` except `test_status: cold_cache`, expected because the
  meta-package uses `unittest`, so there is no pytest cache). The candidate catalog injected into the prompt
  was first-party re-verified (greps + `ls` on the real repo).
- **Validation:** delegated to the **`prompt-validator`** subagent (with the corrected
  `prompts/agent_templates/` paths) and, **in parallel, an independent effectiveness review** by a
  read-only `general-purpose` agent. The two lenses are deliberately different — anchor-grounding/RUBRIC
  vs. requirement-coverage/intent-fidelity.

**Validation iteration history (honest record):**

| Iter | Lens | Verdict | Finding(s) | Resolution |
|------|------|---------|------------|------------|
| 1 | `prompt-validator` (RUBRIC + anchor re-probe) | **PASS** | `validator_status: ok`, **0 blocker / 0 major**, all 7 `hallucination_risk[]` `grounded: true` (independently re-confirmed D-1 open, A-1 open, G-1/G-2 fixed, the suite surface present). One **minor** R2.4: the "10 templates + always-match `generic`" parenthetical reads arithmetically as 11. | Reworded to "9 named templates + the always-match `generic` fallback = 10 ids total". |
| 1 | independent effectiveness review (`general-purpose`) | **Ship-ready, no must-fix** | 3 should-fixes + 5 nice-to-haves. Most important: the **two emphasized analyses disagree** on whether the `prompts/templates/` drift (G-1) is fully swept (CANOPY says fixed in #566; TAUDIT re-hit it in prose), and one named TAUDIT finding (stale `AGENTS.md` tree) had **dropped out** of the catalog. | Applied all 3 should-fixes (un-flattened G-1 to "re-verify prose, not just the guard"; added the missing finding as catalog row **G-3**; pinned validation lens-1 to the *actual* `prompt-validator` subagent) and the nice-to-haves (cross-repo-anchor caveat, approval-gate handoff note, per-enhancement completeness acceptance criterion, near-term-scope steer, `<YYYY-MM-DD>` date slot). |

> Unlike the test-suite-audit session (whose iter-1 FAILed on an R3.4 forward-reference), this prompt
> **passed `prompt-validator` on the first pass**. The substantive refinements came from the *second,
> independent* lens — a requirement-coverage review that caught faithfulness gaps invisible to
> anchor-grounding. That contrast is the headline process finding (§6.1, §6.3).

**Terminal state:** effectively `EMIT_CLEAN` (the lone validator finding was a `minor` wording fix; the
effectiveness review surfaced no blocker).

---

## 3. How the prompt was developed (work performed)

1. **Suite + design study (delegated, three parallel read-only agents).**
   - `Explore` ×2 inventoried the `.claude/` agent+skill surface and the `prompts/agent_templates/` library
     + data layer + `util/` + `tests/`, each citing `file:line`.
   - `general-purpose` ×1 deep-read the `notes/` design history (the design-of-record
     `JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`, the convenience-utilities design, the genesis
     `PROMPT_ANALYSIS_AND_AUTOMATION_PLAN.md`, and both 2026-06-26 dogfooding analyses) and consolidated the
     gap ledger.
2. **First-party verification (direct).** Confirmed the load-bearing open/fixed states rather than trusting
   the notes: D-1 (`test_status` has no ttl/mtime guard) **open**; A-1 (`cli.py:80` exposes only
   `--repo-root`, no `--target-repo`) **open**; G-1 (zero `prompts/templates/` string refs remain in
   `.claude/` / `RUBRIC.md` / `AGENTS.md`) **swept**; G-2 (`ecosystem.yaml:21-23` now lists
   `JuniperCanopy1`/`JuniperCascor1` at 3.13) **fixed**; `conf/` + `papers/` exist; `AGENTS.md:188` tree
   still labels the dir `templates/`.
3. **Authoring (direct).** Filled a copy of `plan.md`, mapped each owner requirement to an ordered, phased
   directive, and inlined a re-verified candidate-enhancement catalog so the prompt is self-grounding.
4. **Validation (delegated).** `prompt-validator` (PASS) + an independent effectiveness review; applied the
   minor fix and the should-fixes (§2).

Agents employed — all via the Agent tool: `Explore` (×2), `general-purpose` (×2: design synthesis +
effectiveness review), `prompt-validator` (×1). This satisfied "employ custom agents as needed" and
dogfooded the suite **on a prompt about the suite itself** — which validated cleanly, a good signal the
architecture generalizes.

---

## 4. The candidate-enhancement catalog (the grounded inventory)

The prompt grounds against this catalog (re-verified this session) and instructs the downstream session to
re-prove every row first-party. `OPEN` items are the higher-value targets; `G-#` are housekeeping.

| ID | Candidate | Source | Status @ 2026-06-26 |
|----|-----------|--------|---------------------|
| D-1 | `test_status` probe has no cache-freshness/TTL guard (stale `lastfailed` masqueraded as current → phantom "188 failing"). | CANOPY §6.2 D-1 | **OPEN (confirmed)** |
| A-1 | Suite single-repo by construction; add a first-class `--target-repo` cross-repo mode. | CANOPY/TAUDIT §6.2 A-1 | **OPEN (confirmed)** |
| A-2 | No live-runtime coverage — cannot catch "green tests / dead app" by design. | CANOPY/TAUDIT §6.2 A-2 | OPEN |
| I-2 | No env-floor-drift guard (the actual canopy incident); `dependency_facts` reads pins but never compares to the active interpreter. | CANOPY §6.1.2 | OPEN |
| E-1 | Live-runtime / service-smoke diagnostician agent (highest value overall). | CANOPY §6.1.1 | proposed |
| E-2 | Environment / dependency-drift checker (= I-2 fix). | CANOPY §6.1.2 | proposed |
| E-3 | Cross-repo grounding mode (= A-1 fix). | CANOPY §6.1.3 | proposed |
| E-4 | Per-file coverage-gap mapper (host in `juniper-ci-tools`). | TAUDIT §6.1.1 | proposed |
| E-5 | Mocked-seam gap auditor (novel `auditor` variant). | TAUDIT §6.1.2 | proposed |
| E-6 | Click-through test author (Playwright, modeled on canopy `src/tests/ui/`). | TAUDIT §6.1.3 | proposed |
| OQ-2/3/5/7 | Deferred design-of-record open questions (queryable datastore; new agent types; auto-invocation; `.gitignore` negations). | DOR §10 | deferred/open |
| M-1 | Anti-hallucination feedback loop under-exercised (`known_misses.yaml` ≈1 entry). | DOR §5.8 | observation |
| G-1 | `prompts/templates/` rename drift — string-form swept (#566 + guard); **re-verify prose, not just the guard**. | CANOPY/TAUDIT §6.2 I-1 | likely FIXED (re-verify) |
| G-2 | Stale `ecosystem.yaml` conda envs — fixed in #566. | CANOPY §6.2 C-1 | FIXED (verify) |
| G-3 | `AGENTS.md` Repository-Structure tree stale (labels dir `templates/`; omits `conf/`/`papers/`/in-tree sub-modules). | TAUDIT §6.2 | **OPEN (confirmed this session)** |

---

## 5. The downstream task in one line

Investigate the current state of the custom-agent infrastructure, evaluate and prioritize a grounded set of
enhancements, author **one** owner-actionable `notes/` PLAN document sequencing them as single-work-unit
PRs, have **every aspect independently validated by ≥3 sub-agents**, and **stop at an approval gate** so no
implementation begins until the owner approves the plan.

---

## 6. Meta-Analysis

### 6.1 Additional custom-agent specializations that would help

The two prior dogfooding analyses already proposed the highest-value additions (live-runtime diagnostician,
dependency-drift checker, cross-repo grounding, per-file coverage mapper, mocked-seam auditor, click-through
author). This session surfaces one **new** specialization, distinct from all of those:

1. **Requirement-coverage / intent-fidelity reviewer (new).** The `prompt-validator` returned a clean
   **PASS** (anchor-grounding and RUBRIC structure were sound), yet an independent effectiveness lens still
   found a **dropped requirement-sourced finding** (G-3, a named item from a doc the owner told us to attend
   to) and a **collapsed source-disagreement** (G-1, where the two emphasized analyses actually conflict).
   These are *faithfulness* defects — the prompt was internally consistent and fully grounded but slightly
   unfaithful to the owner's intent and sources. They are invisible to an anchor-grounding validator by
   construction. A second standing validator (or a second RUBRIC lens) that checks "every owner requirement
   and every source-document finding is represented, and source disagreements are surfaced not flattened"
   would catch this class. Recommend prototyping it as a sibling subagent (`intent-reviewer`) or folding an
   intent-fidelity check into the Skill's validation step. **Owner: juniper-ml.**

This also reinforces the already-proposed **cross-repo mode (A-1)**: this very prompt's candidates span
sibling repos (`juniper-canopy/src/tests/ui/`, `juniper-cascor-model`), whose anchors are absent from the
single-repo discovery bundle.

### 6.2 Other Juniper issues discovered this session

Classified per the requested taxonomy. Each is **documented, not fixed**; cross-referenced where a prior
analysis already recorded it.

**Configuration problems:**

- **(G-3, confirmed) `AGENTS.md` "Repository Structure" tree is stale.** Line `AGENTS.md:188` still labels
  the template dir `templates/` (real: `prompts/agent_templates/`), and the tree omits the present
  top-level `conf/` and `papers/` directories and the in-tree packaged sub-modules. Verified this session
  (`ls -d conf papers` → both present; `grep -n templates/ AGENTS.md` → `:188`). First raised by TAUDIT §6.2;
  it had been **dropped from the prompt's first-draft catalog** and was restored during validation. Folds
  into the G-1 prose sweep. **Owner: juniper-ml.**

**Incomplete development:**

- **(G-1, reconciled) `prompts/templates/` rename cleanup is substantively — but not provably — complete.**
  The validator-blocking **string-form** drift is swept (zero `prompts/templates/` hits across `.claude/`,
  `RUBRIC.md`, `AGENTS.md`), corroborating CANOPY's "fixed in #566". But the two emphasized analyses
  *disagree* (TAUDIT independently re-hit prose drift after the fix claim), and the `AGENTS.md` **tree-label**
  form remains (= G-3). Net: the validator can now find its own contract; the residue is the tree label +
  missing dirs. The prompt records the disagreement rather than collapsing it. **Owner: juniper-ml.**

**Design gaps / Architectural weaknesses / Syntax errors / Suspected:**

- **None new.** D-1, A-1, A-2, I-2, S-1 and the systemic test-strategy gaps are all cross-referenced from
  the two 2026-06-26 analyses, not re-claimed. No syntax errors were encountered (every cited artifact
  parsed/resolved). Recorded explicitly so the absence is not mistaken for "not checked."

### 6.3 What worked (process note)

Dogfooding the suite **on itself** succeeded: two `Explore` inventory agents and a `general-purpose`
synthesis agent grounded the prompt, the discovery CLI produced a clean on-HEAD bundle, and the
`prompt-validator` returned PASS on the first pass. The decisive process insight is that the **two-lens
validation** (anchor-grounding *and* intent-fidelity) was strictly more powerful than either alone — the
grounding lens PASSed while the intent lens caught a dropped finding and a flattened source-disagreement.
That argues directly for the §6.1 requirement-coverage reviewer as a standing suite member.

---

## 7. Appendix — key reproduction commands

```bash
# Regenerate the discovery grounding bundle for the juniper-ml worktree
python util/prompt_discovery/cli.py --repo-root . \
  --subject "custom-agent suite enhancements" \
  --symbols "prompt_discovery,template_data_resolver,prompt-validator,template-agent,test_status" --json

# Suite health baseline (dogfood)
python util/agent_suite_doctor.py --repo-root . --json

# Confirm the load-bearing open/fixed states
grep -niE 'ttl|mtime|getmtime|stale|fresh' util/prompt_discovery/test_status.py   # D-1: (no matches) -> open
grep -n 'add_argument' util/prompt_discovery/cli.py | grep -i repo                  # A-1: only --repo-root
grep -rn 'prompts/templates/' .claude prompts/agent_templates/RUBRIC.md AGENTS.md  # G-1: (no string hits)
sed -n '21,23p' prompts/agent_templates/data/ecosystem.yaml                        # G-2: 3.13/3.13/3.14
ls -d conf papers && grep -n 'templates/' AGENTS.md                                # G-3: dirs exist; :188 stale label
```
