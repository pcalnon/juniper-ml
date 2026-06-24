# Prompt Validation Rubric (R1–R5)

The validation contract the **`prompt-validator`** subagent (PR 3) applies to a drafted prompt
before the Template Agent emits it. Each check has a **stable ID** (so the verdict can reference it
and `tests/test_template_library_drift.py` can assert coverage), an objective **decision procedure**,
and a **default severity**.

- **Design-of-record:** [`../../notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`](../../notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md) (§5.3, §5.5, §5.8).
- **Inputs the validator receives:** the drafted prompt, the task description, the discovery
  **grounding bundle** (real `file:line` / symbols / versions / ports / env, stamped with provenance),
  and this rubric.
- **Goal:** a prompt that PASSES should yield deliverables that are syntactically, logically,
  idiomatically, and architecturally correct and that faithfully meet the task intent — *without the
  downstream agent having to invent unverified facts.*

## Severity & the PASS bar

| Severity | Meaning |
|----------|---------|
| `blocker` | Hard gate. Any single one fails the prompt. (Currently: **R2.0**, **R3.4**.) |
| `major` | Materially harms correctness/faithfulness. Any one fails the prompt. |
| `minor` | Worth noting; recorded as a non-blocking `accepted_warning`. Never blocks alone. |

**`overall == PASS` iff** zero `blocker` ∧ zero `major` findings ∧ every `hallucination_risk[].grounded == true`.
A finding the validator cannot back with reproducible **evidence** (an exact command + observed output)
is auto-downgraded to `minor` (prevents validator false-positives). The Skill's fix loop is bounded
(max 3 rounds, abort on no-progress) and escalates to the owner on exhaustion (§5.1).

## Verdict contract (pinned; full schema ships with the validator in PR 3)

```json
{
  "validator_status": "ok | partial | error",
  "head_sha": "<must equal bundle.head_sha and current HEAD>",
  "iteration": 1,
  "findings": [
    {"id": "R2.0", "severity": "blocker|major|minor", "location": "§Resources / line 42",
     "problem": "...", "fix": "...", "evidence": "<command + output, or null>"}
  ],
  "hallucination_risk": [
    {"claim": "...", "class": "path|symbol|version|port|env|flag", "grounded": false, "evidence": "..."}
  ],
  "overall": "PASS | FAIL"
}
```

---

## R1 — Intent fidelity

*The prompt expresses the intent of the task description.*

- **R1.1 — Requirement coverage** (`major`). Every explicit requirement in the task description maps to
  ≥1 directive or deliverable in the prompt. *Decide:* enumerate task requirements; for each, point to
  the prompt line that carries it. A requirement with no carrier fails.
- **R1.2 — No scope-creep** (`major`). The prompt introduces no requirement absent from the task
  description (and not an owner-approved expansion). *Decide:* every prompt directive traces back to the
  task or an approved expansion; an untraceable directive fails.
- **R1.3 — Faithful objective** (`major`). The `## Primary Objective` restates the task's intent and
  desired outcome without distortion. *Decide:* paraphrase mismatch or added/dropped goal fails.
- **R1.4 — Scope correctness** (`blocker`→`major`). The repo(s)/app(s) named in the prompt match the
  grounding bundle's `repo_context`, and the authorized blast radius (tools, repo count,
  worktree/no-worktree) is proportionate to the task. *Decide:* a prompt targeting a different repo than
  the bundle, or authorizing ecosystem-wide edits for a single-file task, fails.

## R2 — Actionability / sufficiency

*A competent agent could execute the prompt to a correct deliverable without further questions.*
(Deliverable correctness itself is undecidable from the prompt alone, so this criterion judges
**completeness, groundedness, and unambiguity of instruction**, not the eventual output.)

- **R2.0 — Slot completion** (`blocker`, hard gate). No unfilled `{{!REQUIRED}}` placeholder, empty
  mandated section, or bare-`-` stub remains; every `required_fields` entry for the selected template
  (per `manifest.yaml`) is populated with non-placeholder content. *Decide:* regex for residual
  `{{…}}` tokens + manifest `required_fields` lookup. (Cheapest, most objective check; the dominant
  corpus failure mode.)
- **R2.1 — Role + grounded resources** (`major`). `## Role` is set; `## Resources` cites concrete
  grounding (real `file:line`, repo/branch, relevant docs) — presence, not truthfulness (truthfulness
  is R3.4). *Decide:* empty Role or Resources-without-anchors fails.
- **R2.2 — Operational acceptance criteria** (`major`). Every acceptance criterion names a checkable
  command/artifact/observable (a test target/command, a lint invocation, a file written to a named
  path, an observable behavior with an expected value). *Decide:* an adjective-only criterion
  ("works correctly", "effectively error-free", "robust") with no check fails.
- **R2.3 — Ordered, enumerated directives** (`minor`→`major`). Directives are ordered and individually
  actionable; deliverables are enumerated (not a vague "and so on").
- **R2.4 — Internal consistency** (`major`). No two directives/constraints/acceptance-criteria are
  mutually exclusive; referenced file paths, script names, and extensions are internally consistent;
  numeric thresholds do not conflict across sections. *Decide:* contradiction or `name.md` vs
  `name.bash` mismatch fails (corpus had a `wake_the_claude.md` vs `.bash` bug).
- **R2.5 — Convention fidelity** (`major`). Each injected standing convention matches the **current**
  canonical value in `prompts/templates/data/*.yaml` / the parent `AGENTS.md` (handoff threshold,
  deliverable locations, service ports, line-length, worktree root). *Decide:* a *present-but-stale*
  convention (e.g. an "80%" handoff threshold vs the current 95–99%) fails — being present is not enough.
- **R2.6 — Verification & recoverability** (`major`; **execution-class templates only**, per the
  template's `class` in `manifest.yaml`). The prompt instructs how to verify success
  (tests/lint/observable) and how to recover or abort (no merge without a PR, worktree cleanup only on
  merge, `gh pr list` dup-guard). *Decide:* doc/plan-class prompts are exempt; execution-class prompts
  lacking a verify or an abort path fail.

## R3 — Anti-hallucination

*The prompt takes proactive steps so the deliverable does not incorporate hallucinations.*

- **R3.1 — Task-specific verify commands** (`major`). The prompt names the *actual* verification
  commands for this task (the real test/lint command surfaced by discovery), not a generic "run the
  tests". *Decide:* only a generic instruction with no concrete command fails.
- **R3.2 — Verify-before-claim doctrine** (`major`). The prompt instructs the downstream agent to
  re-confirm each cited `file:line`/symbol in-task and to **stop-and-report rather than invent** if a
  path/symbol/flag is not found; and embeds a Deliverable-acceptance block whose commands produce the
  evidence. *Decide:* absence of an enforceable self-verification contract fails.
- **R3.3 — Cross-validation for high-stakes work** (`minor`→`major`). For high-blast-radius or
  irreversible tasks, the prompt instructs sub-agent cross-validation of the result. *Decide:* gate by
  task stakes; low-stakes tasks are exempt.
- **R3.4 — Anchor grounding bind** (`blocker`, hard gate). Every asserted path / symbol / API / flag /
  version / port / env-var in the prompt's `## Resources` (and elsewhere) is present in the grounding
  bundle. Any anchor **not** in the bundle is recorded in `hallucination_risk` and fails R3. The
  validator re-probes each claim independently (grep the path, resolve the symbol via the bundle's
  symbol facts, check the pin) and attaches the command + output as evidence. **Claim taxonomy:**
  - **R3.4a** paths/files · **R3.4b** symbols/signatures · **R3.4c** dependency versions ·
    **R3.4d** ports/env-vars · **R3.4e** CLI flags.
  The validator emits a per-class checked/flagged count so the drift test can assert each class is exercised.

## R4 — Clarity / unambiguity

*Distinct from R1 (coverage) and R2 (sufficiency): a prompt can cover all intent and be actionable yet
be ambiguous about which of two things is meant.* (`major`)

- No undefined referent ("the issue", "this file", "that branch") without a concrete, resolvable bound.
- Each directive admits a single materially-reasonable interpretation; reading order is unambiguous.
- *Decide:* a directive that two competent agents would reasonably execute two materially different ways fails.

## R5 — Right-sized scope (non-over-specification)

*Counterpart to R1.2's scope-creep check: a fully-grounded, unambiguous, consistent prompt can still be
bad by boxing the agent into a predetermined, possibly wrong design.* (`minor`→`major`)

- The prompt states the **what/why** and the constraints, leaving implementation latitude **unless the
  owner pinned a specific design**.
- *Decide:* a prompt that over-specifies the *how* (mandating a brittle/incorrect implementation the
  task did not call for) fails; a prompt faithfully relaying an owner-pinned design does not.

---

## Notes for the validator (PR 3)

- **De-overlap:** grounding *presence* is R2.1; grounding *truthfulness* is R3.4. Do not double-count.
- **Evidence rule:** every `blocker`/`major` finding must carry reproducible `evidence`; evidence-free
  findings downgrade to `minor`.
- **Freshness:** reject the bundle (set `validator_status` accordingly) if `bundle.head_sha` ≠ current
  HEAD or the bundle exceeds its TTL; the Skill must re-discover before re-validating.
- **Fan-out conflict rule:** when checks are fanned out, **any** checker failing a criterion fails that criterion.
