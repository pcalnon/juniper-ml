# Handoff — Custom-Agent Suite: PR3 (validator subagent)

**Date**: 2026-06-24
**Author**: Paul Calnon
**Type**: Thread-handoff prompt
**Origin**: Juniper custom-agent suite — round-1 (design + template library complete)

## Continue

Continue building the Juniper **custom-agent suite** at **PR3 (the validator subagent)**. The
design is ratified and the template library is fully merged to `main`; the remaining work is the
executable pieces. **Read first:** `notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`
(v2, ratified). **Recall memory** `project_custom_agent_suite` (decisions, roadmap, gotchas).

## Completed (merged to `main`)

- Ratified v2 design (hardened by a 5-agent adversarial validation pass — Appendix C of the design doc).
- **#525**: `.gitignore` negation (`.claude/skills/**` + `.claude/agents/**` trackable) + design doc.
- **#526 (2a)**: template-library scaffold + `tests/test_template_library_drift.py` (16 tests).
- **#527 (2b-i)**: `prompts/templates/RUBRIC.md` (R1–R5 + verdict schema + PASS bar).
- **#528 (2b-ii)**: 6 category templates + `generic` + `tests/test_template_selection.py` (5 tests).

## Remaining (one PR each, off updated `main`)

- **PR3 — `prompt-validator` subagent** (`.claude/agents/prompt-validator.md`): headless; applies
  `RUBRIC.md` → the pinned JSON verdict (§5.3); independently re-probes claims. Ship a verdict-schema
  fixture + a static `tests/test_prompt_validator_contract.py` (frontmatter lints; every `R*.x` it
  cites exists in `RUBRIC.md`). Live dry-run = manual evidence on the PR. **Verify the installed
  Claude Code version supports subagent frontmatter + (for PR5) Skill→Agent delegation.**
- **PR4 — discovery helpers** (`util/prompt_discovery/`, path-invoked, `--repo-root`, provenance
  envelope incl. symbol_probe via Serena + dependency_facts) + unit tests. Can parallel PR3.
- **PR5 — `template-agent` Skill** (`.claude/skills/template-agent/SKILL.md`, bounded state machine;
  wires library + validator + discovery).
- **PR6 — `~/.claude` mirror** (`util/install_agents.bash`) + data layer (`prompts/templates/data/*.yaml`).
- **PR7+ — round-2** Planning/Audit/Task subagents (+ the deferred `plan`/`audit`/`task` skeletons).

## Gotchas (verified this session)

- `.claude/` is gitignored EXCEPT the negated `skills/`+`agents/` subtrees → PR3's
  `.claude/agents/prompt-validator.md` IS trackable.
- `prompts/**` is excluded from ALL pre-commit hooks → the drift+selection tests are the gate; wire
  every new test into `ci.yml`'s hardcoded list (the `tests:` job).
- **Before pushing:** `black --check` (`/opt/miniforge3/envs/JuniperData/bin/black`) on `.py`;
  `awk 'length>512' AGENTS.md` must be empty (markdownlint MD013 applies to AGENTS.md, not prompts/);
  set AGENTS.md `Last Updated` = today (UTC) so `agents-md-touch-up.yml` no-ops; `git fetch` before
  any re-push (Paul pushes fixes directly onto PR branches — do NOT force-push).
- Paul merges (admin-bypass; `mergeStateStatus=BLOCKED` with all checks green is the normal state).
- Branch `feature/custom-agent-suite-*` (`feature/**` gets push-CI). One PR per work-unit, off updated `main`.

## Verify starting state

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git checkout main && git pull
ls prompts/templates/   # manifest.yaml RUBRIC.md README.md + 7 templates
python3 -m unittest tests/test_template_library_drift.py tests/test_template_selection.py
gh pr list --state open | grep -i agent   # dup-guard (expect none)
```

## Git state

`main` @ `c1ef513` (all four PRs #525–#528 merged). No open custom-agent PRs. This session's merged
branches (`feature/custom-agent-suite-{foundations,library-scaffold,rubric,templates}`) are safe to prune.
