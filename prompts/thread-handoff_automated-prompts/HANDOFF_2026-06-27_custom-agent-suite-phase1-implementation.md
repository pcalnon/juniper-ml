# Thread Handoff — Custom-Agent Suite Enhancement, Phase 1 Implementation

**Date**: 2026-06-27
**Repo**: pcalnon/juniper-ml
**Trigger**: planning→implementation phase boundary; owner approved Phase 1 at the plan's approval gate.

---

Continue the **custom-agent suite enhancement effort** by implementing **Phase 1 (owner-approved 2026-06-27)** of the ratified plan. Implementation is now authorized for Phase 1 ONLY.

## The authoritative plan (read it first)

`notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md` — read **§6.1–6.5** (per-enhancement design/files/gate/acceptance/risk) and **§7** (PR sequence + the AGENTS.md-contention note).
The plan was authored, 4-independent-agent validated (anchor-grounding + convention/RUBRIC = PASS; feasibility + completeness/risk = CONCERNS, all majors resolved), and is the source of truth.
Use the plan's **recommended designs** for the two Phase-1-relevant open questions (D-1 staleness = HEAD-commit-time primary + configurable TTL secondary; E-2 is ml-owned, canopy-process adoption is a separate follow-up).

## Completed so far (this effort)

- Phases 0–5 of prompt #570: grounded (HEAD `79a9eda`, discovery exit 0, doctor 6 OK/1 WARN), investigated (all candidates re-probed first-party), evaluated (3 independent value/feasibility/risk lenses), authored the plan, validated it (4 blind sub-agents incl. the real `prompt-validator`), and got owner approval for **Phase 1 only**.
- Confirmed CLOSED (no action): G-1, G-2, OQ-7. Confirmed OPEN: D-1, A-1, I-2, A-2, M-1, G-3.

## Remaining work — Phase 1, one PR per unit, off `main`, worktree isolation, **never merge (Paul approves)**

- **PR-0 — DONE in this PR.**
  - The approved plan doc + this handoff were committed together on `docs/custom-agent-suite-enhancement-plan` and opened as a PR (owner merges).
  - Start at PR-1: branch off `main` once that docs PR merges, or off the `docs/custom-agent-suite-enhancement-plan` branch in the meantime so the plan is present.
- **PR-1 — D-1** `test_status` freshness guard.
  - Edit `util/prompt_discovery/test_status.py:15-37`: stamp `cache_mtime`+`age_seconds`; return `status:"stale"` when the cache predates the current HEAD commit time (`git -C <repo> show -s --format=%ct HEAD`) OR exceeds a TTL; keep `cold_cache`/`unavailable`/`ok` branches.
  - Gate: extend `tests/test_prompt_discovery.py` (already wired `ci.yml:138` — no new ci.yml line).
  - Acceptance: stale-cache→`stale`+`failing_count is None`; fresh unchanged; this meta-pkg still reports `cold_cache`.
- **PR-2 — E-2 (+ G-3 gated rider).**
  - New `util/env_floor_drift_check.py`: read installed `juniper-*` versions from `*.dist-info/METADATA` (reuse the `editable_install_drift_check.py:132` `_read_dist_name` dist-info-direct pattern; env path as arg or from `prompts/agent_templates/data/ecosystem.yaml`, NEVER hardcode env names), compare to the target repo's `pyproject.toml` floors → `OK`/`BELOW_FLOOR`/`MISSING`, exit 1 on any below-floor.
  - New `tests/test_env_floor_drift_check.py` (synthetic dist-info fixture; structural — conda can't run in ubuntu CI; add manual-verify note) **+ new ci.yml line (MANDATORY)**.
  - **G-3 rider:** fix the `AGENTS.md` Repository-Structure tree (`templates/`→`agent_templates/`; add `conf/`, `papers/`, the 6 in-tree sub-module dirs) **+ new `tests/test_agents_md_tree_drift.py`** asserting `ls -d */` ⊆ the tree **+ its ci.yml line**.
- **PR-3 — E-5** mocked-seam auditor.
  - New `.claude/agents/mock-seam-auditor.md` (`model: opus`, `effort: max`, tools `Read, Grep, Glob, Bash`) — hunts autouse/session fixtures mocking an integration boundary.
  - Auto-covered by `tests/test_agents_frontmatter.py` (`ci.yml:238`).
  - Dogfood vs canopy `src/tests/conftest.py:371 mock_juniper_data_client`.
  - Update AGENTS.md.
- **PR-4 — E-3** cross-repo `--target-repo` mode.
  - Add `--target-repo` to `util/prompt_discovery/cli.py:80` (additive; `--repo-root` default-CWD preserved; `repo_context.py:16` already uses `git -C`).
  - **Retarget the WHOLE re-probe in `.claude/agents/prompt-validator.md`** — the freshness gate (`:38` bare `git rev-parse HEAD` → `git -C <target>`) AND the R3.4a-e re-probe block (`:80-89`, all CWD-relative).
  - Wire the Skill delegation (`SKILL.md`) to pass the target.
  - Gates already wired: `tests/{test_prompt_discovery,test_prompt_validator_contract,test_template_agent_skill_lint}.py`.
  - Add a cross-repo dogfood acceptance check.

## Key context / gotchas (verified)

- `prompts/**` AND `util/**.py` are pre-commit-excluded → the SOLE gate is a `tests/test_*.py` unittest WIRED INTO `ci.yml`'s hardcoded list (which has shipped unwired tests before — F14). Ship test + ci.yml line in the SAME PR; never weaken/delete a test.
- `AGENTS.md` lines must be ≤512 (`awk 'length>512' AGENTS.md` empty). Black runs in CI on `tests/`+`scripts/` — `/opt/miniforge3/envs/JuniperData/bin/black --check`. The `agents-md-touch-up` `[skip ci]` bump can orphan required checks → clear with an empty re-trigger commit. `.claude/*.md` ARE markdownlinted (unlike `prompts/**`).
- Each new test at a DISTINCT ci.yml anchor so independent PRs don't collide. Branch `feature/…` (gets push-CI).

## Verification (run from the worktree)

```bash
git rev-parse --short HEAD                         # expect descendant of 79a9eda
python util/agent_suite_doctor.py --json           # expect 6 OK / 1 WARN, exit 0
python util/prompt_discovery/cli.py --repo-root .  # exit 0; 7 probes ok except test_status: cold_cache
python3 -m unittest -v tests/test_prompt_discovery.py tests/test_agents_frontmatter.py
```

## Git status at handoff

Forked from HEAD `79a9eda` (= main tip). Remote `origin git@github.com-juniper-ml:pcalnon/juniper-ml.git`. The approved plan doc + this handoff are committed on branch `docs/custom-agent-suite-enhancement-plan` and opened as a docs PR (owner merges; never auto-merged). No production code touched — these are planning/process docs only.

## Out of approved scope (do NOT implement now)

Phase 2 (E-7, E-4, M-1), Phase 3 (E-1 staged, E-6), the app-level E-8, and the S-1 audit — all await separate owner approval at their own gates. OQ-2 rejected; OQ-3/OQ-5 deferred.

---
