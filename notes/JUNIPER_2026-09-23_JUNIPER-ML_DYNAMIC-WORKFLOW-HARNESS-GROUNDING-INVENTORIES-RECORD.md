# Dynamic workflow harness design — grounding inventories, verbatim agent reports

**Project**: juniper-ml — Meta-package & automation hub for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Document Type**: Record (evidence; decides nothing)
**Date**: 2026-09-23
**Status**: RECORD — the five read-only inventories that grounded `JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md` §2, archived verbatim so the design's citations of them resolve on disk (Lane B2 found the design citing an "arc table" that existed only in a transcript)
**Measured at**: juniper-ml `25b78f55`; inventories ran 2026-09-23 01:37–01:54Z (harness, worktree, design-path) and 01:38–01:47Z (documented behaviour), before the design was written

---

## Why this file exists

The design's §0 names five instruments and cites their findings by section (the harness inventory's gaps list, the worktree inventory's removal-criteria synthesis, the design-path inventory's arc table and status census, the two documented-behaviour probes). Those reports were delivered as subagent final messages, which live only in `~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl` and are swept after `cleanupPeriodDays`. The sections headed `## Report …` below were copied from the transcripts by `util/ad-hoc/2026-09-23_archive_subagent_reports.py`, not retyped. They are the agents' words as of that instant; counts in them (worktrees, branches, session files) had already moved by the time the round-1 validators re-counted, which is why the design states every count with its instant.

The two documented-behaviour reports were produced by the `claude-code-guide` agent type and summarise official pages; Lane A2 of the round-1 record later re-derived every claim the design took from them against the raw pages and corrected four "NOT DOCUMENTED" verdicts (see the round-1 record's Report A2 and the design's Appendix D).


---

## Report I1 — harness inventory (scripts, prompts/agent_templates, util/prompt_discovery, agents, skills, tests)

*Verbatim final message of agent `ae808584c92e263b4`, delivered 2026-09-23T01:52:27.924Z; transcript `subagents/agent-ae808584c92e263b4.jsonl`.*

## Claude Code harness inventory: juniper-ml

This covers worktree `structured-inventing-fairy` at HEAD `25b78f55`. Two roots are used below:
- **W** = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy`
- **M** = `/home/pcalnon/Development/python/Juniper/juniper-ml`, the main checkout, which holds the live, untracked state.

Each section gives the absolute paths once. Citations after that are `basename:line`.

**Summary:**
- **What exists:** a flag-translating launcher (`wake_the_claude.bash`) and a user-only Skill, `/template-agent`. The Skill does discover → fill template → delegate to `prompt-validator` → write the prompt to `prompts/generated/`. There are also six subagents, all pinned to opus + max, and a deterministic fleet-triage script.
- **What does not exist:**
  - no step that runs a generated prompt;
  - no hooks, no saved workflows, no commands;
  - no general scheduler;
  - no awareness of usage limits;
  - no tracking of goal sets;
  - no worktree lifecycle wired to agents.

---

### 1. Launch layer
Files: `W/scripts/{wake_the_claude.bash, claude_interactive.bash, default_interactive_session_claude_code.bash, resume_session.bash, custom_agent_dev.bash, sessions/, test_prompt-000.md, test_prompt-001.md, test_prompt-002.md, test.bash, test_resume_file_safety.bash}`. `W/claudey` is a symlink to `scripts/claude_interactive.bash`.

**`wake_the_claude.bash`** is the only real launcher. The other scripts wrap it.

Input flags and what they forward to `claude` (`:148-163`, `:120-129`):

| Input aliases | Forwarded as | Notes |
|---|---|---|
| `-p\|--prompt\|--prompt-string <text>` | the final positional argument | **`-p` means the prompt text here. It is not Claude's `-p/--print`.** |
| `-f\|--file`, `-l\|--path` | prompt read from a file | path and file can be combined in either order (`:631-692`) |
| `-a\|--print\|--agent\|--silent\|--headless` | `--print` | headless mode (`:603-605`) |
| `-i\|--id\|--session-id\|-t\|--thread…` `[uuid\|name.txt\|0\|1]` | `--session-id <uuid>` | missing/invalid/`0` generates a UUID (uuidgen, then /proc, then python3; `:234-265`); `1` suppresses it (`:489-538`) |
| `-r\|--resume\|--resume-thread\|--resume-session <uuid\|name.txt>` | `--resume <uuid>` | clears any session-id (`:467-486`) |
| `--fork\|--fork-session\|--resume-fork…` | `--fork-session` | `:608-610` |
| `-w\|--worktree\|--work-tree\|--working-tree [name\|0\|1]` | `--worktree [name]` | `0` or missing lets Claude name it; `1` means no worktree (`:541-556`) |
| `-m\|--model…` | `--model` | hardcoded allowlist: `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-fable-5` plus the aliases (`:85-113`, `:359-375`) |
| `-e\|--effort… <low\|medium\|high\|xhigh\|max\|auto>` | `--effort` | `:136-141`, `:572-580` |
| `-c\|--remote\|--control\|--remote-control [name]` | `--remote-control [name]` | `:559-569` |
| `-s\|--skip\|--skip-permissions\|--dangerously-skip-permissions` | `--dangerously-skip-permissions` | `:612-615` |
| `-v`, `-u` (exit 1), `-h\|-?` (exit 0), `--` (no-op spacer) | — | `:695-716` |

- **Unknown flags:** any other token prints usage and exits 1 (`:719-721`). There is no way to pass arbitrary `claude` flags through.
- **Flags that are never forwarded:** a grep returned 0 hits in all four launchers for `--output-format`, `--max-turns`, `--append-system-prompt`/`--system-prompt`, `--agents`, `--allowedTools`, `--permission-mode`, `--mcp-config`, `--add-dir`, `--settings`, and `retry|backoff`.
- **Forwarding order:** resume, session-id, worktree, remote-control, effort, model, print, fork, permissions, then the prompt (`:727-756`).
- **Environment variables:**
  - `WTC_DEBUG` defaults to the hardcoded `DEBUG=TRUE` (`:35-37`). Because debug is on by default, `REQUIRE_SAVED_SESSION_ID` is FALSE: a failed session-file save is only a warning. A symlink target is still refused (`:42-45`, `:520-530`).
  - `WTC_SESSIONS_DIR` and `WTC_LOGS_DIR` default to the `scripts/sessions` and `logs` directories of the checkout the script lives in (`:47-52`).
- **Session-id persistence:**
  - Only `--id` writes a file: `${SESSIONS_DIR}/<uuid>.txt` containing the UUID, refusing symlinks (`:268-298`).
  - `--resume` never writes one, and the new id created by `--fork` is never captured.
  - Resume accepts a raw UUID, or a `.txt` basename with no `/` whose content is a UUID (`:312-357`).
- **How it runs Claude:**
  - Interactive: foreground `claude`, with a non-zero exit propagated (`:789-798`).
  - Headless: `nohup claude … >> logs/wake_the_claude.nohup.log 2>&1 &` (falls back to `$HOME`), then `exit 0` immediately (`:771-800`). There is no PID file, no exit status, and every headless run shares one plain-text log.
  - It echoes all input, including the prompt, to stdout (`:446`, `:791`).
- **Canonical usage example:** relaunching from a handoff file with `--id 0 --worktree 0 --model opus --effort max --file prompts/thread-handoff_automated-prompts/HANDOFF_… -- --dangerously-skip-permissions --remote-control` (`:435`).

**`claude_interactive.bash`** (what `claudey` runs):
- Positional `$1` is the model and `$2` is the effort (`:32-34`).
- Environment variables: `CLAUDE_MODEL` (default opus), `CLAUDE_EFFORT` (default max), `CLAUDE_PROMPT`, `CLAUDE_ID`/`CLAUDE_WORKTREE` (default `"0"`, i.e. new UUID plus an auto-named worktree), `CLAUDE_REMOTE_CONTROL` (default on), `CLAUDE_SKIP_PERMISSIONS` (`"0"` means yes) (`:61-78`).
- `DEBUG` is hardcoded TRUE (`:17`), which **forces `--dangerously-skip-permissions` on every launch** (`:109-111`; pinned by `tests/test_claude_interactive.py:161`).
- It builds a string and runs it through `eval`/`xargs` (`:97-103`, `:141-143`).
- There is no `shift` after reading the effort, so `$2` is also appended as a trailing argument (`:133-135`; pinned by `test_claude_interactive.py:275-298`). That argument lands right after `--remote-control`, and `wake_the_claude.bash:559-565` then takes it as the remote-control name.
- The model constants it exports (`claude-opus-5`, `claud-haiku-4-5`, `:40-43`) are unused and don't match wake's allowlist.

**`default_interactive_session_claude_code.bash`**:
- Runs fixed arguments: `--id --worktree --effort high --prompt "Hello World, Claude!"` (`:20-21`).
- Setting `CLAUDE_SKIP_PERMISSIONS=1` adds skip-permissions (`:27-30`). Note that this wrapper uses `"1"` for yes, the opposite of `claude_interactive`.
- Passes extra arguments through (`:35-37`).

**`resume_session.bash`**:
- Hand-edited constants: a hardcoded session UUID (`:17`) and worktree name (`:22`), with effort max, remote-control and skip-permissions all on (`:29-32`).
- Calls M's launcher by absolute path (`:47-66`, `:128`).

**`custom_agent_dev.bash`**:
- Contains **no executable code**. It is comment-only proto-specs for the Template, Planning, Audit and Task agents (`:14-109`).
- Output naming convention: `[PROJECT]_[APPLICATION]_[SUBJECT]_TASK_TYPE]_[DATE].md` (`:8`).
- "Future Work" agent types: Infrastructure, Review, Refactor, Test, Documentation, Code Review (`:110-116`).

**`scripts/sessions/`**:
- In W it contains only `.gitkeep`; `scripts/sessions/*` is gitignored (`.gitignore:101-104`).
- The live store is per checkout. `/home/pcalnon/Development/python/Juniper/juniper-ml/scripts/sessions/` holds **604 `<uuid>.txt` files, all 37 bytes** (the UUID plus a newline).
- There is no metadata: no prompt, model, worktree or status. The file's mtime is the only timestamp.
- `/home/pcalnon/Development/python/Juniper/juniper-ml/logs/wake_the_claude.nohup.log` is 33 bytes from Mar 7 (a single "Hello!"). Headless mode has essentially never been used from M.

**Test prompts and scripts:**
- `test_prompt-000.md` is "Hello World, Claude!".
- `test_prompt-001.md` is the resume check ("what is today's Julian date?").
- `test_prompt-002.md` is a 180-line troubleshooting prompt about wake's session-id recursion. It still says to hand off at "80%" (`:40`).
- `test.bash` is stale: it looks for `*.txt` in the current directory (`:10`) and cats `nohup.out` (`:21`). It is not in CI.
- `test_resume_file_safety.bash` runs in CI (`ci.yml:1079`, `main-verify.yml:479`). It checks that an invalid resume file exits non-zero and is not deleted (`:17-37`).

### 2. Prompt and template layer
Files: `W/prompts/agent_templates/{README.md, RUBRIC.md, manifest.yaml, data/{standing_rules,anti_hallucination,conventions,ecosystem,known_misses}.yaml, audit.md, code-review.md, failing-tests.md, generic.md, implement-plan.md, plan.md, proposal-analysis.md, regressions.md, release-and-deployment.md, task.md}`, `W/prompts/{generated,manual,prompt_templates,thread-handoff_automated-prompts}/`.

**`README.md`:**
- Templates are read-only. The Template Agent fills a copy and writes it to `prompts/generated/` (`:3-6`, `:55`).
- Canonical skeleton: H1, then `## Role`, `## Resources`, `## Primary Objective`, `## Assigned Tasks / Directives`, `## Key Deliverables & Requirements`, and optional `## Constraints` and `## Finalize / Validation` (`:24-35`).
- Placeholder forms: `{{NAME}}` (fill), `{{!NAME: hint}}` (required), `{{?NAME: hint}}` (optional) (`:39-47`).
- The only gate is `tests/test_template_library_drift.py`, because `prompts/**` is excluded from pre-commit (`:9-11`).

**`RUBRIC.md`:**
- Hard gates are **R2.0 and R3.4** (`:20`).
- PASS requires 0 blocker, 0 major, and every `hallucination_risk[].grounded == true` (`:24`).
- Findings without evidence are downgraded to minor. The fix loop runs at most 3 rounds and aborts on no progress (`:25-27`).
- The checks:
  - **R1** "The prompt expresses the intent of the task description." (`:51`)
    - R1.1 covers requirements and source findings, and requires source disagreements to be surfaced (`:53-61`).
    - R1.2 forbids scope-creep (`:62-64`).
    - R1.3 requires a faithful objective (`:65-66`).
    - R1.4 checks scope and blast radius against `repo_context` (`:67-70`).
  - **R2** "A competent agent could execute the prompt to a correct deliverable without further questions." (`:74`)
    - R2.0 (blocker): no residual `{{…}}` placeholders, and every manifest `required_fields` entry is filled (`:78-82`).
    - R2.1 requires a Role and grounded Resources.
    - R2.2 requires operational acceptance criteria: "an adjective-only criterion … fails".
    - R2.3 requires ordered directives; R2.4 requires internal consistency.
    - R2.5 checks conventions against `data/*.yaml`: "present-but-stale … fails" (`:96-99`).
    - R2.6 requires verify and abort paths, for the execution class only (`:100-104`).
  - **R3** "The prompt takes proactive steps so the deliverable does not incorporate hallucinations." (`:108`)
    - R3.1 requires real verify commands; R3.2 requires verify-before-claim.
    - R3.3 requires sub-agent cross-validation when stakes are high.
    - R3.4 (blocker): every path, symbol, version, port, env var and flag is in the bundle, with sub-classes a–e (`:120-127`).
    - R3.5 consults the known-miss ledger, read-only (`:128-135`).
  - **R4** clarity (`:137-144`).
  - **R5** "right-sized scope" (`:146-154`).
  - Freshness: the bundle is rejected if its `head_sha` isn't HEAD or it is past its TTL (`:163-164`).

**`manifest.yaml`** schema:
- `version: 1` (`:9`).
- `skeleton.required[]` and `skeleton.optional[]` (`:11-22`).
- `placeholders.{fill,required,optional}` (`:24-32`).
- `templates[]`: `{id, title, when_to_use, match_signals{keywords[], discovery[]?, variants{}?, always?}, file, required_fields[], class}` (`:37-130`).
- Allowed classes are generic, execution, analysis, planning and review (`:34-35`).
- The `discovery`/`variants` hints (only in failing-tests, `:50-55`) are read by nothing mechanical. `template_select_preview.py` uses keywords only (`:50-62`).

**Templates:**

| id | class | required_fields | slots | output |
|---|---|---|---|---|
| code-review | review | target, resources | !TARGET !RESOURCES ?EXTRA_FOCUS | `notes/…-CODE-REVIEW.md` (`:31`) |
| failing-tests | execution | target, resources | !TARGET !RESOURCES ?SCOPE_NOTE ?EXTRA_DIRECTIVES | PR |
| implement-plan | execution | plan, resources | !PLAN !RESOURCES ?EXTRA_DIRECTIVES ?DELIVERABLE_EXTRA | PR + status written back to the plan (`:25`) |
| proposal-analysis | analysis | subject, resources | !SUBJECT !RESOURCES ?EXTRA_DIRECTIVES | `JUNIPER_<SUBJECT>_ANALYSIS_<date>.md`, an older naming pattern (`:31`) |
| regressions | execution | symptom, resources | !SYMPTOM !RESOURCES ?EXTRA_DIRECTIVES | PR |
| release-and-deployment | planning | package, resources | !PACKAGE !RESOURCES ?EXTRA_DIRECTIVES | plan |
| plan | planning | subject, resources | !SUBJECT !RESOURCES ?EXTRA_FOCUS ?CONSTRAINTS | `notes/JUNIPER_<date>_JUNIPER-<REPO>_<PHRASE>.md`, refuses if the file exists (`:33`) |
| audit | analysis | scope, resources | !SCOPE !RESOURCES ?EXTRA_FOCUS ?CONSTRAINTS | `…-AUDIT.md` (`:32`) |
| task | execution | task, resources, acceptance | !TASK !RESOURCES ?SUBTASKS !ACCEPTANCE | PR (`:32-33`) |
| generic | generic | task_subject, deliverables | CATEGORY_TITLE !ROLE !RESOURCES !PRIMARY_OBJECTIVE !DIRECTIVES !DELIVERABLES ?CONSTRAINTS ?VALIDATION | promotion candidate |

The mapping from `required_fields` to slots is a convention only. The drift test only checks placeholder syntax by regex (`test_template_library_drift.py:31-34`). For example, generic's `task_subject` has no matching `{{!TASK_SUBJECT}}` slot.

**The `data/` layer** (every file is `version: 1`):
- `standing_rules.yaml`:
  - which actions the owner approves (`:5-7`);
  - `worktree_root: /home/pcalnon/Development/python/Juniper/worktrees` (`:9`);
  - the dup-guard (`:11`);
  - rules such as one PR per work unit, no merge without a PR, and worktree cleanup only on merge (`:13-18`).
- `anti_hallucination.yaml`: six doctrine blocks (`:6-12`).
- `conventions.yaml`: line length 512, handoff at "95-99%", deliverable locations, and `generated_prompt_name` (`:6-23`).
- `ecosystem.yaml`: repos, ports, conda envs, env vars, and the NPZ contract (`:5-36`).
- `known_misses.yaml`: one seeded miss (`:7-14`).
- Who reads it:
  - `template_data_resolver.py`;
  - the doctor;
  - `generated_prompt_index.py`, which reads `deliverable_locations`;
  - `util/env_floor_drift_check.py:74`, which reads `ecosystem.yaml`;
  - the validator, via RUBRIC R2.5 and R3.5.
- **The template-agent `SKILL.md` never references `data/` or the resolver** (grep returned 0 hits). The discovery conventions probe hardcodes the same values instead of reading the YAML (`conventions.py:27-29`).

**The other prompt directories:**
- **`generated/`**: 8 files, named `PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md` (`conventions.yaml:23`, parsed by `generated_prompt_index.py:39`).
  - The APPLICATION token is inconsistent (`ML` vs `JUNIPER-ML`).
  - TASK-TYPE is one of PLAN, TASK, IMPLEMENT or DEBUG.
  - Validator results appear only as prose headers, e.g. `JUNIPER_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION_PLAN_2026-07-28_0315.md:7`.
- **`manual/`**: 166 hand-written task prompts named `promptNNN[.M]_YYYY-MM-DD.md`. Numbers are reused across dates (054–057), and there is one outlier with spaces in the name (`prompt166_…`).
- **`prompt_templates/`**: 8 legacy free-form seed templates (`common-prompt-template_<category>_<date>.md`, plus `prompt-automation_2026-03-12.md`). The design doc maps them to the new templates in Appendix A (`notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md:526-537`).
- **`thread-handoff_automated-prompts/`**: 210 files named `HANDOFF_YYYY-MM-DD_<subject>.md` (`tests/test_thread_handoff_archive.py:23`).
- No code reads `manual/`, `prompt_templates/` or the handoff archive (grep in scripts/, util/, tests/, .github/, .claude/ returned 0).

### 3. Utilities and how they chain
Files: `W/util/prompt_discovery/{cli.py, repo_context.py, test_status.py, file_probe.py, symbol_probe.py, dependency_facts.py, conventions.py, concurrency.py, symbol_overlay.py, _util.py, README.md}`, `W/util/{template_data_resolver.py, template_select_preview.py, scaffold_template.py, generated_prompt_index.py, agent_suite_doctor.py, agent_suite_summary.py, install_agents.bash}`.

**`prompt_discovery/cli.py`:**
- Flags: `--repo-root P`, or `--target-repo P` (which wins if both are given), plus `[--subject S] [--symbols a,b]` (`:79-95`).
- Output is JSON on stdout:
  - `schema_version: 1`;
  - `provenance{captured_at, head_sha, dirty, ttl_seconds: 900, per_probe_status}`;
  - slices for `repo_context`, `test_status`, `file_probe`, `symbol_probe`, `dependency_facts`, `conventions` and `concurrency` (`:34-74`).
- It hard-stops with exit 2 and a `discovery_failed` envelope when HEAD can't be resolved (`:98-105`).
- The probes:

| Probe | What it does | Where |
|---|---|---|
| `repo_context` | `git rev-parse` / `git status` | `repo_context.py:15-36` |
| `test_status` | reads pytest lastfailed; distinguishes `cold_cache` / `stale` / `unavailable` from `ok` | `test_status.py:40-91` |
| `file_probe` | `git grep` on the subject, up to 25 hits | `file_probe.py:13-28` |
| `symbol_probe` | grep for the definition, no Serena | `symbol_probe.py:18-32` |
| `dependency_facts` | pyproject, plus ports and env vars from the parent `AGENTS.md` | `dependency_facts.py:22-57` |
| `concurrency` | `gh pr list` plus `git worktree list` | `concurrency.py:15-27` |

  All probes run through `_util.run`: 30 s timeout, never raises (`_util.py:17-37`).
- **`symbol_overlay.py`** takes `--bundle F --serena F` and merges Serena facts into the bundle; Serena results win (`:26-63`).

**The other utilities:**
- **`template_data_resolver.py`**: `[dotted.key] [--repo-root] [--json]`. Exits 1 if the key is missing (`:57-68`).
- **`template_select_preview.py`**: `"TASK" [--repo-root] [--json] [--top N]`. Ranks by keyword substring count, falls back to generic, and always exits 0 (`:11-19`, `:50-115`).
- **`scaffold_template.py`**: `--id --title --class [--keywords] [--required-fields] [--dry-run]`.
  - Writes the new template file, and only *prints* the manifest stanza.
  - Exits 1 on a name collision and 2 on bad arguments (`:13-16`, `:99-145`).
- **`generated_prompt_index.py`**: `[--older-than DAYS [--prune|--archive DIR] [--yes]] [--dry-run] [--json]`. Only acts with `--yes` and never under `--dry-run` (`:14-20`, `:100-154`).
- **`agent_suite_doctor.py`**: `[--repo-root] [--json] [--strict] [--no-discovery]`. Exits 0, 1 or 2 (`:11-14`). It checks:
  - every agent is opus + max, `name == stem`, and prompt-validator exists (`:76-101`);
  - the Skill's allowed tools include `Agent` (`:104-115`);
  - templates, RUBRIC hard-gate ids, and the data layer;
  - a live `cli.py` run (`:167-186`);
  - the mirror, via `install_agents --dry-run` (`:189-210`).
- **`agent_suite_summary.py`**: `[--agents|--templates] [--json|--markdown]`. Read-only (`:116-147`).
- **`install_agents.bash`**: `[--reverse|--uninstall] [--dry-run]`, with env overrides `JUNIPER_ML_REPO_ROOT` and `JUNIPER_CLAUDE_HOME`.
  - Symlinks each agent and skill into `~/.claude`, and never overwrites a file that isn't a symlink (`:12-13`, `:57-120`).
  - **It is not installed on this host**: `/home/pcalnon/.claude/agents` doesn't exist, and `/home/pcalnon/.claude/skills` contains only `synced/`.

**The chain.** Generate → validate → emit is documented and implemented, but as an LLM procedure inside the Skill, not as code:
1. `/template-agent` runs `cli.py`, and optionally the overlay.
2. It asks the owner clarifying questions, then selects a template from `match_signals`.
3. It fills a copy of the template.
4. It calls `Agent(prompt-validator)` with the draft, RUBRIC, the bundle and `<target>`.
5. It runs at most 3 fix rounds, then writes to `prompts/generated/`.

Terminal states are `EMIT_CLEAN`, `EMIT_WITH_CAVEATS` or `ESCALATE_TO_PAUL`. This is documented in `SKILL.md:26-75` and in the design doc (§4 at `:110-136`, §5.1 at `:146-173`).

**The "execute with task-executor" step does not exist as a mechanism:**
- The Skill stops once it has written the prompt.
- task-executor only says its input is "often a pre-generated, validated prompt" (`task-executor.md:3`, `:18-19`; design `:407`).
- The only code that reads `prompts/generated/` is `generated_prompt_index.py`.
- The hand-off is manual. `agent_suite_doctor.py:16-19` records one such run done by hand: planner → implement-plan template → validator.

### 4. Agents
Files: `W/.claude/agents/{prompt-validator,task-executor,planner,auditor,mock-seam-auditor,fleet-supervisor}.md`.

All six have `model: opus` and `effort: max`, and CI enforces this (`tests/test_agents_frontmatter.py:93-107`). Only task-executor sets `isolation: worktree` (`:5`). None of them sets permissionMode, maxTurns, hooks, memory, skills or mcpServers.

| agent | tools | what it produces | what it never does |
|---|---|---|---|
| prompt-validator | Read, Grep, Glob, Bash | only the JSON verdict as its final message (`:116-150`); re-probes every anchor with `git -C <target>` (`:86-107`); reads `known_misses` (`:109-114`); rejects a stale bundle (`:43-47`) | edits files or asks questions (`:13-15`, `:170-171`); fan-out is deliberately unused (`:158-160`) |
| task-executor | +Edit, Write, **Agent** | changes on a feature/fix branch; runs the real tests, lint and pre-commit; `gh pr create`; may start sub-agents (`:21-34`) | merges; weakens tests; deletes a worktree that has unmerged work (`:36-41`) |
| planner | +Write | exactly one `notes/JUNIPER_<date>_JUNIPER-<REPO>_<PHRASE>.md`, refusing if it exists (`:44-53`) | writes code or anything else |
| auditor | +WebFetch, Write | one `notes/…-AUDIT.md` with evidence per finding (`:38-44`) | changes anything |
| mock-seam-auditor | Read, Grep, Glob, Bash | a findings report as its final message (`:66-79`) | edits, or fails a build (`:63`) |
| fleet-supervisor | Read, Grep, Glob, Bash | a triage plan as its final message (see §6) | push, merge, close, comment or rebase (`:116-122`) |

**The pinned verdict**, verbatim from `prompt-validator.md:121-146`:
```json
{"validator_status": "ok | partial | error",
 "head_sha": "<must equal bundle.head_sha and the target HEAD: git -C <target> rev-parse HEAD>",
 "iteration": 1,
 "findings": [{"id": "R2.0", "severity": "blocker | major | minor", "location": "§Resources / line 42",
               "problem": "...", "fix": "...", "evidence": "<exact command + observed output, or null>"}],
 "hallucination_risk": [{"claim": "register_or_reuse(factory, name)", "class": "path | symbol | version | port | env | flag",
                         "grounded": false, "evidence": "<exact command + observed output>"}],
 "overall": "PASS | FAIL"}
```

The JSON Schema is at `W/tests/fixtures/prompt_validator/verdict.schema.json`, with PASS and FAIL samples alongside it. It enforces:
- `additionalProperties: false` (`:7`, `:37`, `:74`);
- `head_sha` matching `^[0-9a-f]{7,40}$` (`:25`);
- `iteration >= 1` (`:30`);
- finding `id` matching `^R[1-5](\.[0-9]+[a-e]?)?$` (`:43`);
- the enums for severity, class and overall (`:48`, `:84`, `:98`).

### 5. Skills, settings, hooks, workflows, commands
- **Skills**: `W/.claude/skills/{template-agent,service-smoke,ui-test-author}/SKILL.md`. All three are user-only (`disable-model-invocation: true`), opus + max.
  - **template-agent** (the only `/template-agent` definition anywhere):
    - `argument-hint "[task description | @file] [--repo-root <path> | --target-repo <path>]"`;
    - allowed tools: `Read, Grep, Glob, Bash, Write, Agent` (`:1-9`);
    - if the validator can't be called, it falls back to validating inline (`:84-85`);
    - all its paths are relative to juniper-ml (`:36`, `:45-46`, `:51-58`, `:66-67`).
  - service-smoke uses `…, mcp__playwright` and has no Write. ui-test-author adds Write.
- **Settings**:
  - There is no `.claude/settings.json` in W or M.
  - The tracked `.claude/settings.local-ORIG_{1..5}.json` and `-WORKING.json` are never read by Claude Code, according to `W/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARENT-AGENTS-GOVERNANCE-AND-WORKTREE-SETTINGS-ASYMMETRY.md:216-235`.
  - The live file is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/settings.local.json` (untracked).
    - It is byte-identical to the tracked `W/settings.local.json` at the repo root, which Claude Code doesn't read.
    - Contents: 41 allow entries, including a blanket `"Bash"`, `WebFetch`, `Bash(git:*)` and `Bash(python:*)`; `enableAllProjectMcpServers: true`; five `enabledMcpjsonServers`.
    - **It has no hooks, no deny list and no defaultMode.**
  - The same note reports that worktrees created by Claude Code read local settings from the main repo root (`:237-262`).
  - `.mcp.json` exists only in M (`.gitignore:170`).
  - `/home/pcalnon/.claude/settings.json` has no hooks, permissions or env.
- **Workflows and commands**: `.claude/workflows/` and `.claude/commands/` do not exist in W or M.

### 6. Fleet triage
Files: `W/util/fleet_triage/predict_merge.py`, `W/.claude/agents/fleet-supervisor.md`.

**`predict_merge.py`:**
- **Inputs:**
  - `--pr N | --batch` (one is required), plus `[--json] [--repo-root]` (`:652-675`);
  - env `JUNIPER_FLEET_SKIP_PRECOMMIT` (`:281`);
  - it needs `gh` and the juniper-ci-tools checks, and marks a screen `skip` if those are missing (`:55-59`).
- **Per PR**, it:
  1. makes a throwaway detached clone under tempdir;
  2. merges `origin/main` into the branch tip, with gpgsign off (`:101-106`, `:331-418`);
  3. runs `black, isort, flake8, ruff, ruff-format, mypy, check-ast` on the files the merge changes (`:90`);
  4. runs a symbol-loss screen and a docs-deletion screen on the merged result.
- **Per-PR JSON** has the keys `pr, branch, base_ref, base_sha, branch_sha, mergeable, behind_main, verdict, gates, true_delta, conflicted_files` (`:421-434`), plus `title`, `gh_mergeable`, `gh_merge_state` (`:512-514`).
- **Verdicts**: MERGE-CLEAN, NEEDS-UPDATE-BRANCH, DAMAGED-FIX-FIRST or CONFLICT (`:396-403`). In batch mode a failing row becomes ERROR (`:531-538`).
- **Batch output**: `{base_ref, base_sha, open_pr_count, prs, clusters, merge_order, screen_coverage}` (`:545-553`).
  - Merge order puts fix/heal/hotfix branches or titles first, then the smallest same-file clusters (`:464-489`).
- **Exit codes**: always 0 when it produces a report; 2 on a precondition failure (`:51-53`).

**fleet-supervisor's plan format:**
- It runs the script once per batch, then does the dup/supersession analysis, the cluster map and the merge order (capabilities a–e, `:45-64`).
- Its final message has five parts (`:97-106`):
  - **Summary**: counts per verdict and the contested files;
  - **Per-PR**: pr, verdict, mergeable, behind_main, the failing gate / lost symbols / deleted docs, and the true delta, citing the script's JSON;
  - **Cluster map**;
  - **Ordered merge plan**, with "re-run `predict_merge.py --pr <next>`" after each merge;
  - **DUP-CLOSE candidates**, only under the two-key rule (content overlap plus owner confirmation, `:86-95`).
- It has no `Agent` tool, so fixes are "delegated to a task-executor" by the owner, not by the agent (`:120-122`).
- **Drift:** the agent says `strict_required_status_checks_policy` is false (`:13`), but `predict_merge.py:19-24` says it is true on all nine repos.

### 7. Tests that pin the harness
All of these run in CI (line numbers are in `W/.github/workflows/ci.yml`) unless noted.

| Area | Tests |
|---|---|
| Launchers | `test_wake_the_claude.py` (`:210`; classes at `:27`, `:858`, `:1416`, `:1513`); `test_claude_interactive.py` (`:214`); `scripts/test_resume_file_safety.bash` (`:1079`). `scripts/test.bash` is manual and not in CI. |
| Library | `test_template_library_drift.py` (`:680`); `test_template_selection.py` (`:683`); `test_template_select_preview.py` (`:687`); `test_template_data_resolver.py` (`:692`); `test_scaffold_template.py` (`:696`); `test_generated_prompt_index.py` (`:350`) |
| Discovery | `test_prompt_discovery.py` (`:341`); `test_symbol_overlay.py` (`:345`) |
| Agents and skills | `test_agents_frontmatter.py` (`:774`); `test_prompt_validator_contract.py` (`:749`) with the fixtures above; `test_template_agent_skill_lint.py` (`:755`); `test_service_smoke_skill_lint.py` (`:762`); `test_ui_test_author_skill_lint.py` (`:769`); `test_fleet_supervisor_contract.py` (`:377`); `test_agent_suite_path_drift.py` (`:780`); `test_agents_md_tree_drift.py` (`:806`) |
| Suite utilities and fleet | `test_install_agents.py` (`:357`); `test_agent_suite_doctor.py` (`:361`); `test_agent_suite_summary.py` (`:365`); `test_predict_merge.py` (`:372`) |
| Adjacent | `test_thread_handoff_archive.py` (`:353`); `test_cleanup_session_worktrees.py` (`:242`); the `test_soak_*` suites (`:602-618`, `:996-1056`) |

### Adjacent machinery that affects the gaps
- **A scheduled headless dispatcher already exists, for one purpose only.** `W/util/soak_run_probe.py` runs `claude -p <task> --output-format stream-json --verbose --session-id <uuid>` (`:771-776`).
  - Each run gets `reports/soak/runs/<stamp>-<probe>/` containing `task.txt`, `meta.json`, `stream.jsonl`, `status.json` and a pidfile (`:778-848`).
  - It has a 900 s timeout (`:123`) and an exit-3 "refuse to spend a session" stopping rule (`:86-92`).
  - It unsets `ANTHROPIC_API_KEY` (`:345-355`).
  - `W/util/systemd/juniper-soak-probe.timer` fires at 03/09/15/21:23 with jitter (`:18`, `:26`). `juniper-soak-probe.path` fires on `MEMORY.md` changes, limited to 1 per hour (`:29`, `:45-46`).
  - These units are **not installed** here: `~/.config/systemd/user` has none, and `systemctl --user list-timers --all` shows none.
  - Its docstring explains why subagents, cloud routines and CronCreate were rejected for this memory experiment (`:17-27`).
- **`W/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`** is an adopted procedure for multi-agent verification (lanes, reconciler, iteration, minimum record; `:34-175`). It is run by hand, and its artifacts go under `W/reports/<date>_round-NN-consensus/`. No code implements it.
- **`W/scripts/cleanup_session_worktrees.py`** cleans up worktrees that are unlocked, clean and merged (`:1-40`). It is run manually.
- **`W/.github/workflows/claude.yml`** is the `@claude` bot, triggered by events only (`:3-11`).

### Gaps I observed, each checked by searching
1. **No general scheduler or queue.** Grepping `schedul|crontab|\bcron\b|systemd-run|\bat now\b|queue|dispatcher` across the launchers, `custom_agent_dev.bash`, `.claude/agents`, `.claude/skills`, `prompt_discovery`, the six suite utilities and `agent_templates` returned 0 hits. The only exception is the soak timer above, which is not installed.
2. **No awareness of usage or rate limits.** Grepping `usage.?limit|rate.?limit|quota|\b429\b|overloaded|5-hour|weekly.?limit|ccusage|token.?budget|max-budget|cost` across the launchers, `scripts/*.py`, agents, skills, suite utilities and templates found only prose: `prompt-validator.md:169`. `retry|backoff` in the launchers returned 0.
3. **No tracking of goal sets or work state.** Grepping `goal|backlog|state\.json|status\.json|work.?queue|todo list|task list` found only prose (`planner.md:26`, `plan.md:26`, `RUBRIC.md:12`, `:66`). The session store is UUID-only files. The closest analog is the markdown defect register `W/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, counted by `util/ad-hoc/register_open_set.py:20`.
4. **No generate → validate → execute pipeline** (see §3). Validator verdicts and discovery bundles are never saved as files.
5. **No worktree lifecycle tied to agents.**
   - Grepping for the cleanup and worktree scripts in agents, skills, launchers, the installer and templates found no invocations; the only match was the rule `worktree_cleanup_only_on_merge`.
   - Grepping for `hooks|PreToolUse|PostToolUse|SessionStart|Stop|SubagentStop|worktree` in every settings JSON returned 0.
   - There are no systemd units for claude, agents or worktrees.
6. **Headless runs are fire-and-forget:**
   - no structured output;
   - no exit status;
   - no per-run log or PID;
   - fork ids are never captured;
   - arbitrary flags can't be passed through.
7. **The CI gates block mixing models.** Every agent and skill is pinned to opus + max:
   - `test_agents_frontmatter.py:93-107`;
   - `test_template_agent_skill_lint.py:101-110`;
   - `test_prompt_validator_contract.py:126-136`;
   - `test_fleet_supervisor_contract.py:117-127`.

   The launcher's model allowlist is also hardcoded. As written, adding a cheaper worker agent would fail CI.
8. **Handoff is relaunched by a human.** The model writes the HANDOFF file (`AGENTS.md:381-390`). The only relaunch path is the example comment at `wake_the_claude.bash:435`.
9. **The suite only works when run from inside juniper-ml.** The `~/.claude` mirror is not installed, and the Skill's paths are relative to juniper-ml.

### Other drift found
- `DEVELOPER_CHEATSHEET_JUNIPER-ML.md:168` and `:173` describe `claudey` as effort high with no skip-permissions. That is `default_interactive_session_claude_code.bash`; `claudey` actually runs `claude_interactive.bash`.
- `DEVELOPER_CHEATSHEET_JUNIPER-ML.md:187` says the parameters are passed unquoted, but they are quoted (`:787`, `:792`).
- `verdict.schema.json:5` and `:41`, and `verdict.sample.fail.json:28`, still cite the old `prompts/templates/` path. `test_agent_suite_path_drift.py` only scans `.claude/agents`, `.claude/skills` and `prompts/agent_templates` (`:31-35`), so it misses these.
- The skip-permissions environment variable means the opposite in the two wrappers (`"0"` vs `"1"`).


---

## Report I2 — worktree lifecycle inventory (scripts, procedures, live counts, removal-criteria synthesis)

*Verbatim final message of agent `a6d6e4baceced0493`, delivered 2026-09-23T01:53:05.682Z; transcript `subagents/agent-a6d6e4baceced0493.jsonl`.*

# Worktree lifecycle tooling in juniper-ml: current state as of 2026-09-22

**The short version.** No tool in the repo today can decide that a worktree is safe to remove. The strongest removal spec is the V3 design note, which is unratified and none of whose rollout steps (1–7) has landed. The cleaner that targets `.claude/worktrees/` would currently delete a live secret. Several scripts do something different from what the docs say. The synthesis at the end lists the gates you would have to build.

**Conventions used below.** Everything was read-only, using git 2.53.0.
- **ROOT** is `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/`, at HEAD `25b78f55`. Inline citations are `ROOT-relative-path:line`; absolute paths for the key files are at the end.
- The sandbox refused git commands aimed at other worktrees, so I could not check whether other trees are dirty or hold ignored files.
- Your seed note `notes/dynamic_workflow_design.out` is on branch `design/dynamic-workflow` (commit `27ea09a1`), not in this checkout.

---

## 1. The scripts

| Script | CLI / flags | Directory it acts on | Naming it enforces | Checks before removal | Dry-run |
|---|---|---|---|---|---|
| `util/worktree_new.bash` | none | `~/…/Juniper/worktrees` (:3) | hardcoded `juniper-canopy-cascor--fix--connect-canopy-cascor--<date>--$(uuidgen)` (:4) | creates only; checks the directory doesn't exist (:14-18) | no |
| `util/worktree_activate.bash` | sourced function `activate_new_worktree <dir>` | any | none | n/a (only `cd`) | n/a |
| `util/worktree_close.bash` | `[pattern]`, default `fix--connect-canopy-cascor` (:9-14) | anything `git worktree list` matches by substring (:17) | none | none of its own; runs `worktree remove` without `--force` (:23) | no |
| `util/worktree_wipeout.bash` | `<name>…` | any | assumes branch `worktree-<name>` (:22) | exit 1 with no args, exit 2 if `$1` doesn't substring-match (:3-8); `worktree remove`, `branch -d`, prune (:19-25) | no |
| `util/worktree_cleanup.bash` (the V2 orchestrator) | see below | makes its new worktree in `<MAIN_REPO>/.claude/worktrees` (:47) | new tree is `cleanup-<8hex>` on branch `worktree-cleanup-<8hex>` (:267-280) | clean, pushed, `.h5` guard, git's own refusals, open-PR check | partial |
| `util/cleanup_open_worktrees.bash` | none | `<cwd>/.claude/worktrees/<n>` for branches listed as `+ worktree-*` (:7-18) | reads Claude naming | **removes nothing** | no |
| `util/remove_stale_worktrees.bash` | none | every `git worktree list` line containing `worktrees` (:8) | none | **none** | no |
| `util/prune_git_branches_without_working_dirs.bash` | `[-D\|-F]` (:61) | branches only | `BRANCH_TYPE="fix"` hardcoded (:21) | the directory it infers is missing (:53-55) | no |
| `scripts/cleanup_session_worktrees.py` | `--repo --root --gh-repo --dry-run --allow-cwd` (:312-323) | `<repo>/.claude/worktrees` (:63-64, :328) | none (acts on whatever branch is checked out) | see §3 | yes, evaluates every gate |

### Hazards and discrepancies, per script

**`worktree_new.bash`**
- It runs `git worktree add <path>` with no branch argument (:22), so it branches off whatever HEAD the caller is on, without fetching.
- It activates conda env `JuniperCascor` (:11, :40), which doesn't exist; only `JuniperCascor1` and `JuniperCascor-DEPRECATED` are in `/opt/miniforge3/envs/`.
- The suffix is a uuid, not the documented 8-character hash. It ends in `exec bash`, and :16 has a stray `}}`.
- V3 lists it as "Defect — fix or retire" (V3 note:968).

**`worktree_activate.bash`**
- The guard at :18 compares the output of `$(is_sourced)`, which is always empty, to `"1"`. The "should not be launched manually" branch can never run.

**`worktree_close.bash` and `worktree_wipeout.bash`**
- `docs/REFERENCE.md:3689-3690` swaps their descriptions. `close` removes worktrees by substring pattern only, with no branch delete and no prune. `wipeout` is the one that removes the worktree, deletes the branch and prunes.

**`worktree_cleanup.bash`**
- Flags:
  - required `--old-worktree`, `--old-branch`
  - optional `--parent-branch` (default `main`), `--new-worktree`, `--new-branch`, `--skip-pr`, `--skip-remote-delete`, `--force-destructive`, `--dry-run` (:96-117, :125-173)
  - environment variables `JUNIPER_ML_MAIN_REPO` (:46) and `WORKTREE_CLEANUP_DISCARD_SNAPSHOTS=1` (:414).
- Order of operations (:594-600):
  1. Refuse if dirty (exit 1, :234-240), then push (:243-260).
  2. Create the new worktree from `origin/main` (:282-310).
  3. Open a PR (:316-391).
  4. Remove the old worktree (:397-497).
  5. Verify.
  6. Fast-forward the new worktree to main.
  7. Return the primary checkout to main (:546-579).
- Phase 4's checks:
  - refuses if `cascor-snapshots/*.h5` exists, looking only one level deep (:409-423);
  - `worktree remove` without `--force`: on failure it refuses and prints what is there, unless `--force-destructive` is given (:435-446);
  - `branch -d`, which likewise refuses unless `--force-destructive` (:453-465);
  - deletes the remote branch only if `gh` proves there are zero open PRs; it fails closed but is hard-wired to `pcalnon/juniper-ml` (:472-493).
- **It does not wait for a merge.** Removal happens right after the PR is created, which matches the V2 design.
- It doesn't check lock, liveness, ignored files other than `.h5`, nested repos, or per-worktree refs.
- After Phase 1's `push -u`, `branch -d` succeeds for any pushed branch, so that check effectively means "pushed".
- Dry-run problems:
  - Phase 1 skips the dirty check and logs the tree as clean (:225-230).
  - `run_cmd` returns 0 under dry-run, so Phase 4's refusals can never show up in a plan (:209-216).
- Other problems:
  - When the parent branch isn't `main`, it does a local merge and push (:370-373). That merge commit is unsigned, and the repos' required-signatures rule rejects unsigned commits.
  - It creates worktrees inside the repo, which contradicts `REFERENCE.md:2294`.
  - Neither the header (:21-30) nor `REFERENCE.md:3168` mentions `--force-destructive`.
  - **There are no tests** for `--force-destructive` or the `.h5` guard; nothing in `tests/` mentions either.

**`cleanup_open_worktrees.bash`**
- In each tree it runs `git add --all`, `git pull origin main` and `git push origin HEAD`, with errors discarded (:23-30). There is no lock check, and the pull creates unsigned local merge commits.
- `REFERENCE.md:3692` says it "Removes all active worktrees", and the V2 note (:501) recommends it for batch cleanup. Both are wrong.

**`remove_stale_worktrees.bash`**
- Today it would select **170 of 171** registered worktrees, everything except the primary.
- Git would still refuse the 18 locked ones and any dirty ones. Every other tree goes, including ignored secrets and the caller's own working directory.
- `REFERENCE.md:3691` says "DO NOT RUN". CI enforces the destructive behaviour: `tests/test_cleanup_open_remove_stale_worktrees.py:76-100` asserts that removal succeeds.

**`prune_git_branches_without_working_dirs.bash`**
- The exclusion regex `^(\*\+)\ .*$` (:39, :51) is a basic regex with literal parentheses, so it matches nothing. The current branch and branches open in other worktrees survive only because git refuses to delete them; the tests at :144-189 rely on git's "used by worktree" refusal.
- The directory it infers, `.claude/${i/-/s\/}`, never exists for `fix/*` branches. Every `fix` branch is therefore deleted, with `-d`, or with `-D` when `-D`/`-F` is passed.

### Ad-hoc tools that hold the only implementations of some checks

- **`util/ad-hoc/worktree_sweep_survey.bash` / `worktree_sweep_apply.bash`** cover only `Juniper/worktrees`.
  - A tree is SAFE if it is clean with the untracked-files setting forced to normal (survey :87, apply :135) and has no commits beyond `origin/main` (survey :102, apply :143).
  - Apply re-checks each row and refuses detached HEADs (:121-125) and any ignored file unless `--include-ignored` is passed (:139-142). It then deletes the branch with `-D` (:80).
  - The header says squash-merged PRs count as SAFE (:8-12), but the code never calls `gh`, so squash-merged branches come out ACTIVE.
  - `REPO_OF` has no juniper-recurrence entry (:32-41), though that repo has 10 trees on disk.
  - Neither script checks locks or liveness.
- **`util/ad-hoc/2026-08-28_p5_worktree_cleanup.py`** checks that the newest PR is MERGED and treats a failed lookup separately (:170-194, :218-223). It also checks cwd occupancy (:69-85) and a porcelain clean check (:227). Ignored files must match an allow-list (:58-62) or be copied out with `--harvest` (:230-242). It only reports unless `--execute` is given, and deletes branches with `-D` (:266).
- **`2026-08-20_worktree_liveness_probe.py`** checks process cwd only; with no arguments it exits 0 (:66-68).
- **`2026-09-02_worktree_inuse_probe.py`** treats cwd or an open file descriptor inside the tree as a hard hit (exit 1); argv matches are only warnings (`REFERENCE.md:2169-2204`).
- **`2026-09-12_worktree_converge_precheck.py`** only checks the checkout it lives in (`REPO = parents[2]`, :32).
- **`2026-09-15_verify_worktree_content_shipped.bash`** only compares `git diff --name-only` (:47). It can't see untracked, staged, or committed-but-unpushed work.
- **`worktree_live_cwd_check.py`** always exits 0.

---

## 2. Procedure documents

The sources are:
- `docs/REFERENCE.md` § Worktree Procedures Reference (:2208-2299), moved out of `AGENTS.md` (pointer at `AGENTS.md:325`);
- `docs/REFERENCE.md` § Worktree Divergence Is a Memory Cost (:2092-2204);
- `notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`;
- `notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`;
- the design note `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`.

The parent `Juniper/AGENTS.md:260-261` still points at `notes/WORKTREE_SETUP_PROCEDURE.md` and `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`. Neither path exists in juniper-ml any more.

**"When to Use Worktrees"** (`REFERENCE.md:2236-2242`, verbatim):

| Scenario | Use Worktree? |
|---|---|
| Feature development (new feature branch) | **Yes** |
| Bug fix requiring a dedicated branch | **Yes** |
| Quick single-file documentation fix on main | No |
| Exploratory work that may be discarded | **Yes** |
| Hotfix requiring immediate merge | **Yes** |

**Naming convention** (`REFERENCE.md:2225-2232`, setup note :86-92, parent `AGENTS.md:241-252`): `<repo>--<branch, with / replaced by -->--<YYYYMMDD-HHMM>--<8-char hash>`. No tool enforces it. Of the 22 juniper-ml trees in the central directory, only 5 end in the 8-character hash; 17 use short labels such as `--anl`, `--harvest`, `--soak`.

### Removal criteria as the documents state them

- **From `REFERENCE.md`:**
  - (a) Prune worktrees on merge (:2125).
  - (b) Check not locked, then merged, clean, and not the current working directory; these are "necessary and not sufficient", because "merged-and-clean does not mean idle" (:2134-2137).
  - (c) Run the cwd liveness probe first. A hit is a hard stop; no hits is "corroboration, not proof" (:2155-2167).
  - (d) Then run the in-use probe. Remove trees one at a time, and "never with `--force`" (:2201-2204).
  - (e) Rules: push before you merge, prune after cleanup, and "Do not leave stale worktrees" (:2292-2298).
- **From the V2 note:**
  - (f) All work committed, `gh` authenticated (:15-19).
  - (g) The tree must be clean, then pushed (:48, :60-64).
  - (h) Your working directory must already be in the new worktree before removal (:100, :176).
  - (i) Run both probes, and never use `--force` (:178-200).
  - (j) Don't delete the remote branch while a PR is open (:228-240), then prune.
  - (k) Batch sweep: SAFE means no tracked or untracked changes and no commits beyond `origin/main`. Trees with only ignored files are skipped by default (:503-551).

### Contradictions in the V2 note

- "Never pass `--force`" (:199-200) conflicts with Step 9's `--force` fallback (:208-212) and with :553-557.
- `branch -D` is prescribed (:220-224, :352), but the script refuses it.
- **Removal happens after the PR is created, not after it merges** (:346-354).
- The new worktree is created inside the repo (:77), which contradicts `REFERENCE.md:2294` and parent `AGENTS.md:274`.

### The V3 design note

It is revision 2, marked DESIGN only, scoped to juniper-ml, and "has not been executed" (:1054). It is the most complete removal spec in the repo.

- **Worktree gates:**
  - G1, not locked (:266-302).
  - G2, clean including untracked files, with config pinned and exit codes checked. This includes no skip-worktree or assume-unchanged entries (:304-338).
  - G3, ignored files judged by type, not size: secrets, evidence and unknowns refuse; caches pass (:340-443).
  - G4, HEAD and every per-worktree ref reachable, and no rebase, merge or bisect in progress (:445-541).
  - G5, no nested git repository (:543-583).
- **Branch gates:**
  - B1, no unpushed commits (:712-758).
  - B2, a PR exists; advisory only (:760).
  - B3, content landed on main, checked with a three-dot diff (:764-789).
  - B4, no armed auto-merge (:791-815).
- **Also:** keep the git admin directory before removing (:817-820). A 7-day recent-modification veto applies regardless of lock (:885-888). `-f -f` is forbidden for both `remove` and `move`.
- **Status of its rollout (:982-1011):** steps 1–7 haven't landed. `cleanup_session_worktrees.py` hasn't changed since commit `64ef0435` (2026-08-21), and `remove_stale_worktrees.bash` and its test are still there. Steps 8–9 lie outside the repo: the Duplicati filters weren't checked, and the parent `AGENTS.md` (:278) still has no counterweight.

---

## 3. Claude Code's `.claude/worktrees/` compared with `Juniper/worktrees/`

| | Claude Code native (`juniper-ml/.claude/worktrees/<name>`) | Central (`Juniper/worktrees/<repo>--…`) |
|---|---|---|
| Created by | Claude Code, for sessions and subagents | `git worktree add` following the setup note |
| Branch | `worktree-<name>`; subagents get `worktree-agent-<17hex>`. Sessions often switch to another branch later. | the feature branch |
| Lock | locked while live, e.g. `claude session <name> (pid P start T)` or `claude agent agent-<id> (pid P start T)` | never locked (V3 :292-293) |
| Git admin markers | `CLAUDE_BASE` (seems to hold the starting commit: this session's is `25b78f55`) and a `locked` file (governance note :258-260) | none |
| Settings | resolve to the primary checkout's `settings.local.json`; `.mcp.json` and `.env` are absent (governance note :243-256, :326-329) | not tested |
| Cleaners | `scripts/cleanup_session_worktrees.py` | sweep scripts, P5 cleaner |
| tar backup | excluded, because `.claude` is in `EXCLUDE_DIRS` (`util/juniper-backup.bash:111`) | not included, because `APPLICATION_REPOS` (:102) has no `worktrees` |

According to V3 (:84-87), Duplicati backs up both, but deleted files are only recoverable for about 7 days.

### Live count from `git worktree list --porcelain`

- **Totals.** 171 worktrees are registered: the primary, 148 under `.claude/worktrees/`, and 22 under `Juniper/worktrees/`. There are no orphan directories in `.claude/worktrees/`.
  - `Juniper/worktrees/` actually holds **178** worktrees across 9 repos. The 156 that belong to sibling repos don't appear in juniper-ml's list. V3 counted 149 on 09-12.
- **Locks.** 18 are locked, all native: 14 sessions and 4 agents. None of the central ones are locked. All 14 lock pids are alive and their `/proc` start times match the lock text, so no lock is stale.
- **Branches.**
  - 72 are on `worktree-*` branches, 6 of those being `worktree-agent-*`.
  - 90 are on feature branches: 68 native and 22 central.
  - 8 are detached, all native and all unlocked. One is `dreamy-crunching-kettle` at `ed14f3a6`, the unreachable commit V3 describes.
  - Of the locked trees, 16 are on `worktree-*` branches and 2 on feature branches.
- **Subagent worktrees.** The 4 locked ones are held by pid 4113687, the same pid that locks session `jazzy-soaring-minsky`. So the parent session holds its subagents' locks. 2 agent worktrees are unlocked (`agent-a9d5ee2a15a651d28`, `agent-aecabbc0b4aa7fd55`).
- **Unchanged trees.** 27 of the 148 native trees are still at their `CLAUDE_BASE` commit, including all 6 agent trees.
- **Branch leftovers.** There are 596 local branches. 166 are `worktree-*`, and 94 of those aren't checked out anywhere.

### What `cleanup_session_worktrees.py` checks

It only looks at `.claude/worktrees/`. For each tree, in order (:260-301):
1. Skip anything without `.git`.
2. Skip the tree containing the current working directory (:263-266).
3. Keep if **locked** (:267-271).
4. Keep if detached (:273-278).
5. Keep if dirty (:285-288).
6. Keep unless the tip is an ancestor of `origin/main` (:282) or **any** PR on that branch is MERGED; a `gh` failure counts as not merged (:120-149).

If a tree passes, it runs `worktree remove` without `--force` (:210), then `branch -D` on the tree's current branch (:215), then `push origin --delete` (:221), then prune.

Defects, all still present (V3 :129-137, :955-958):
- The dirty check ignores git's exit code (:112-113), so an error reads as clean. It also uses a bare porcelain check, which the `showUntrackedFiles=no` setting can blind.
- "Any MERGED PR" can't see commits pushed after the merge, and those commits are then force-deleted locally and on the remote.
- Deleting the remote branch cancels an armed auto-merge.
- It deletes whatever branch is checked out. On 68 native trees that's a feature branch, and the `worktree-<name>` branch is left behind.

**Live hazard.** `curious-plotting-hummingbird` is unlocked. It's on `fix/handoff-passphrase-resolved` at `8f82ea5d`, which is already in `origin/main` (I checked). It holds a 114-byte `.env`, which `.gitignore:189` (`*.env`) hides from git status. V3 §5.1 (:664-687) identifies this file as the backup passphrase on the "do not sweep" list. This script would pass the tree and delete the file.

---

## 4. Merge tooling at the end of an arc

### `util/safe_merge.py`

Documented in `REFERENCE.md` § Utility Script Reference, :3279-3308.

- **Flags** (:1141-1170):
  - `--pr` (required), `--repo`, `--owner`
  - `--merge-method`, default squash; `rebase` exits 2
  - `--timeout`, default is the repo's entry in `REPO_TIMEOUTS`, capped at `TIMEOUT_CEILING` = 3300 (:391-409)
  - `--execute`; **without it the run is a dry-run**
  - `--no-auto-fallback`, `--verbose`
- **Budgets** (:288-383): ml 2800, cascor 2800, cascor-worker 2400, recurrence 2000, deploy 1400, data / data-client / canopy / cascor-client 3300. `DEFAULT_TIMEOUT` is 2400.
- **Exit codes** (:124-137, :1172-1210): 0 merged **or dry-run**, 1 refused, 2 misuse, 3 hard error, 4 interrupted. On exit 4 the auto-merge net is deliberately left armed.
- **The `MERGED` line.** On success it prints one of these to stdout:
  - `MERGED #N at <head8> via <method>` (:1133);
  - `MERGED #N by the armed auto-merge net…` or `MERGED #N concurrently…` (:791-808).

  Refusals go to stderr as `REFUSED: …`.
- **Traps when reading it:**
  - A PR that is already merged is **refused** with exit 1 (`is MERGED, not OPEN`, :931-932).
  - One hard-error message contains "is MERGED at" (:1119-1123), so match `^MERGED #` on stdout only.
  - The SHA in the line is the PR's head, not the squash commit. `merge-base --is-ancestor` therefore reports false after every squash merge (`HANDOFF_2026-09-09_defect-register-round-38…:273-274`).
  - Handoffs repeatedly say "exit 0 ≠ merged" (for example `HANDOFF_2026-09-17_container-registry-wave-3…:158-164`). But `main()` returns 1 on a refusal (:1204-1206), and no test checks that. The only exit-code test through `main()` is rebase → 2, at `tests/test_safe_merge.py:297`.
  - **Rely on the stdout line plus `gh pr view --json state`, not the exit code.**

### `util/wait_for_checks.py`

Documented at `REFERENCE.md:3317-3328`.

- **Flags:** `--pr`, `--repo`, `--owner`, `--anchor required|observed`, `--fail-fast`, `--timeout`, `--interval` (default 20), `--json`, `--verbose` (:534-562).
- **Default timeout:** the repo's `safe_merge` budget, read when it runs. It falls back to 1800 s only if that table can't be read (:101-103, :472-502). The budget line goes to stderr.
- **Exit codes:** 0 green, 1 failed, 2 timeout, 3 hard error. It also **exits 0 for a PR that is already MERGED or CLOSED** (:505, :403-417), which `REFERENCE.md` doesn't mention. Read `status` from `--json` instead.

### `util/open_signed_pr.py`

Documented at `REFERENCE.md:3313-3316`.

- **What it does:** creates the branch from the resolved base SHA, makes one GitHub-signed commit through the `createCommitOnBranch` API from whole files given with `--add LOCAL:REPOPATH` (plus `--delete`), then opens the PR. It needs no working tree.
- **Exit codes:** 0 opened, 1 refused (an open PR or the branch already exists), 2 error.
- **The whole-file clobber hazard:**
  - Each `--add` uploads the whole local file (:221-228). If the local copy is older than `origin/main`, the commit silently reverts every change made in between.
  - The `expectedHeadOid` guard (:280-282) only stops a concurrent push to the new branch; that is the only "clobbering" `REFERENCE.md` mentions.
  - It has already happened: ml#1869 uploaded a `REFERENCE.md` that was 7 commits stale (`HANDOFF_2026-09-09_container-registry-item-6…:85-103`), commit `27605476` repaired a clobbered changelog, and a cascor near-miss is recorded (`HANDOFF_2026-08-23…:198-205`).
  - The written mitigation: `git diff --name-only HEAD origin/main` intersected with the `--add` paths must be empty, then read the PR diff back.
  - For your workflow, **an agent worktree that has fallen behind `origin/main` is a clobber source**, even before any removal question.

---

## 5. Tests that cover the worktree scripts

| Suite | Target | What it checks | CI |
|---|---|---|---|
| `test_worktree_cleanup.py` | `worktree_cleanup.bash` | new worktree created before old removed (:728); Phase 4 remote-delete guards (:784-933); Phases 1, 2, 3, 7. **Nothing on `--force-destructive` or the `.h5` guard.** | `ci.yml:223`, `main-verify.yml:399` |
| `test_cleanup_session_worktrees.py` | session cleaner | `LockGateTest` (:525-653), including a source scan forbidding `--force`; **expects the `branch -D` + `push origin --delete` calls** (:343-364) | `ci.yml:242`, `mv:403` |
| `test_cleanup_open_remove_stale_worktrees.py` | `remove_stale`, `cleanup_open` | **asserts `remove_stale` removal succeeds** (:76-100) | `ci.yml:246`, `mv:404` |
| `test_worktree_wipeout_close.py` | `wipeout`, `close` | missing → 1, invalid → 2, removes only the match | `ci.yml:251`, `mv:405` |
| `test_prune_git_branches_without_working_dirs.py` | branch pruner | `-d`, `-D`, `-F`; git's refusals | `ci.yml:257`, `mv:407` |
| `test_worktree_activate.py` / `test_worktree_sweep_scripts.py` | activate helper / sweep pair | | `ci.yml:224-225`, `mv:400-401` |
| `test_p5_worktree_cleanup.py` | P5 cleaner | | `ci.yml:231`, **missing from `main-verify.yml`** even though its list claims to mirror `ci.yml` (:395) |
| `test_worktree_inuse_probe.py` | in-use probe | | `ci.yml:1040` |

- There are no tests for `worktree_new.bash`, the liveness probe, the converge precheck, verify-content-shipped, or `worktree_live_cwd_check.py`.
- The merge tools are covered by `test_safe_merge.py`, `test_wait_for_checks.py` and `test_open_signed_pr.py` (`ci.yml:725/714/703`).
- Two V3 fixes would require changing tests that currently enforce the destructive behaviour: fixing the cleaner's branch handling (step 3) and retiring `remove_stale` (step 7).

---

## Removal-criteria checklist

In the right-hand column, "exists" means a tool does it correctly. "Partial" means a tool does it with a defect or narrower scope. **NONE** means it must be built.

| # | A worktree is removable only if… | Source | Mechanical check today |
|---|---|---|---|
| 1 | It is the tree this workflow created, with path, branch, base SHA and PR number recorded when the agent was dispatched | V3 §8.3 "No manifest" (:975) | **NONE** |
| 2 | It is not the caller's working directory | `cleanup_session_worktrees.py:181-193` | exists |
| 3 | It is not locked (git enforces this again at removal) | `cleanup_session:155-178`; V3 G1; `REFERENCE.md:2134-2149` | exists for native trees only; central trees are never locked |
| 4 | No process has its working directory or an open file inside it | liveness and in-use probes; `REFERENCE.md:2155-2204` | partial: ad-hoc probes, not wired into any remover except P5's cwd check |
| 5 | The agent's arc is complete, or nothing written in the last 7 days | V3 :885-888 | **NONE** |
| 6 | Clean including untracked files: `-c status.showUntrackedFiles=normal status --porcelain -uall` is empty **and** exits 0 | V3 G2; `worktree_cleanup:234`; sweep :87/:135; `cleanup_session:112` | partial: four implementations, none of them V3-correct |
| 7 | No skip-worktree or assume-unchanged files (`ls-files -v \| grep '^[Ssh]'` is empty) | V3 :309-332 | **NONE** |
| 8 | No rebase, merge, cherry-pick or bisect in progress (find the paths with `rev-parse --git-path`) | V3 G4 :461-478 | **NONE** |
| 9 | Not detached, and HEAD plus every per-worktree ref is reachable; otherwise save them to `refs/salvage/…` without overwriting | V3 G4 :445-541; `cleanup_session:273-278`; `sweep_apply:121-125` | partial: detached trees are refused; the reachability check and salvage are **NONE** |
| 10 | No nested `.git` two or more levels down | V3 G5 | **NONE** |
| 11 | No secret file (`*.env`, `.env.secrets`, anything `.sops.yaml` covers), refused even at 0 bytes | V3 §5.1 :682-687 | **NONE**, and a live instance exists |
| 12 | No evidence or unknown ignored files (`--ignored=traditional -uall`), or they were copied out first | V3 G3; `worktree_cleanup:409-423`; `sweep_apply:139-142`; P5 :58-62 | partial: `.h5`-only, or any-ignored, or an allow-list without `-uall` |
| 13 | Everything is pushed: if the remote branch exists, zero commits ahead of it; if the remote is gone, the branch must be in `origin/main`; otherwise refuse | V3 B1 :712-758 | partial: Phase 1 pushes but doesn't verify |
| 14 | The content reached main: the tip is in `origin/main`, **or** a MERGED PR's `headRefOid` equals the tree's HEAD, **or** `git diff --quiet origin/main...<branch>` | V3 B3; `cleanup_session:282-292` (any-MERGED defect) | partial: equal-head and three-dot checks are **NONE** |
| 15 | The merge is confirmed: stdout has `^MERGED #N` **and** `gh pr view --json state` says MERGED | `safe_merge.py:808,1133`; `REFERENCE.md:3286,3308` | the tools exist; the workflow must build the parser |
| 16 | Before deleting a remote branch: no open PR (fail closed) **and** no armed auto-merge | `worktree_cleanup:472-493`; V3 B4 | partial: the auto-merge check is **NONE**; the session cleaner deletes the remote with no check |
| 17 | The git admin directory (`logs/HEAD`, `ORIG_HEAD`, `refs/`, `rebase-merge/`) was preserved | V3 §6.5 | **NONE** |
| 18 | Remove without `--force` (never `-f -f`), stop and print on refusal, use `branch -d`, then prune | `worktree_cleanup:425-465,496`; `REFERENCE.md:2202-2204` | exists in `worktree_cleanup.bash` |
| 19 | Afterwards, return the primary checkout to an up-to-date main if it is clean | `worktree_cleanup:546-579` | exists |

**Must be built:** items 1, 5, 7, 8, 10, 11 and 17; the reachability and salvage part of 9; the push check in 13; the equal-head and three-dot checks in 14; the auto-merge gate in 16; and the `MERGED`-line parser for 15.

**Must be fixed before reuse:**
- item 6, with the exit-code check, pinned config and `-uall`;
- item 12, judging by file type and using `-uall`;
- the branch-deletion half of `cleanup_session_worktrees.py` (the `-D`, the unchecked remote delete, and the any-MERGED test).

**Do not use to remove agent worktrees:**
- `remove_stale_worktrees.bash`, `cleanup_open_worktrees.bash` and `worktree_close.bash`;
- `cleanup_session_worktrees.py` as it stands today;
- V2's "remove after the PR is opened" sequence.

---

### Key files (absolute paths)

- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/worktree_cleanup.bash`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/scripts/cleanup_session_worktrees.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/{worktree_new,worktree_activate,worktree_close,worktree_wipeout,cleanup_open_worktrees,remove_stale_worktrees,prune_git_branches_without_working_dirs}.bash`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/{safe_merge,wait_for_checks,open_signed_pr}.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/ad-hoc/{worktree_sweep_survey.bash,worktree_sweep_apply.bash,2026-08-20_worktree_liveness_probe.py,2026-09-02_worktree_inuse_probe.py,2026-08-28_p5_worktree_cleanup.py,2026-09-12_worktree_converge_precheck.py,2026-09-15_verify_worktree_content_shipped.bash,worktree_live_cwd_check.py}`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/docs/REFERENCE.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-03-02_JUNIPER-ML_WORKTREE-SETUP-PROCEDURE.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-06-25_JUNIPER-ML_WORKTREE-CLEANUP-PROCEDURE-V2.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARENT-AGENTS-GOVERNANCE-AND-WORKTREE-SETTINGS-ASYMMETRY.md`
- `/home/pcalnon/Development/python/Juniper/AGENTS.md` (lines 229-278)
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/tests/test_{worktree_cleanup,cleanup_session_worktrees,cleanup_open_remove_stale_worktrees,worktree_wipeout_close,prune_git_branches_without_working_dirs,worktree_activate,worktree_sweep_scripts,p5_worktree_cleanup,worktree_inuse_probe,safe_merge,wait_for_checks,open_signed_pr}.py`


---

## Report I3 — design-path inventory (naming, templates, status vocabulary, decisions, active arcs, handoff procedure, gates)

*Verbatim final message of agent `a0017f63ede59bb50`, delivered 2026-09-23T01:53:57.336Z; transcript `subagents/agent-a0017f63ede59bb50.jsonl`.*

I've covered all six areas. Everything below was read at worktree HEAD `25b78f55` (2026-09-23 01:29 UTC, #2013). Paths are written as `$R/...`, where `R=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy`.

**The short version:** design paths, status and decisions are all hand-written prose. The one enforced status list in the repo belongs to the requirements snapshot, not to design docs. Status lines drift out of date. The live state of each arc is carried by the handoff chain.

---

## 1. `notes/` inventory, naming, templates, header/status vocabulary

**Counts.** 657 tracked paths: 647 regular files plus 10 symlinks. Of the regular files, 617 are `.md`, 11 `.png`, 11 `.html`, 7 yml/yaml and 1 txt. 291 files sit at the top level, all `.md`; 139 of them are dated 2026-08/09 and 45 are dated 2026-09.

| Subdirectory | Files |
|---|---|
| `legacy/` | 88 |
| `releases/` | 82 |
| `regressions/` | 27 |
| `canopy_3d_viz_mockups/` | 22 |
| `development/` | 21, plus 5 in `partials/` |
| `interface_proposals/` | 20 |
| `code-review/` | 14 |
| `proposals/` | 10 |
| `pull_requests/` | 8 |
| `templates/` | 7, plus 6 in `ci/` |
| `requirements/` | 3, plus 15 by-area, 9 by-repo, 7 by-status |
| `observability/` | 5 |
| `concurrency/` | 4 |
| `documentation/` | 3 |

**Naming convention** (`$R/notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`, status "Ratified (owner decision 2026-07-04)", :7):
- **Format (:14-23):** `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<CONTENTS-DESCRIPTION-PHRASE>.md`. Underscores separate only the four fields; the phrase is UPPER-KEBAB.
- **Date:** the creation date, or the date of a substantive re-issue (:30).
- **REPO (:31):** one of ML, CANOPY, RECURRENCE, CASCOR, CASCOR-CLIENT, CASCOR-WORKER, DATA, DATA-CLIENT, DEPLOY, ECOSYSTEM.
- **Doc-type suffix (:32):** docs from the planner/auditor/code-review agents end in `-DESIGN`, `-PLAN`, `-ROADMAP`, `-ANALYSIS`, `-AUDIT` or `-CODE-REVIEW`.
- **Tag rules (:34-39):** cross-repo work is ECOSYSTEM; sub-packages, tooling and the handoff/worktree procedures are ML; the recurrence family is RECURRENCE.
- **Exemptions (:41-51):** `notes/releases/`, `notes/templates/`, `notes/requirements/`, `notes/legacy/`, and README files.
- **Source of truth (:61-67):** update this doc first, then `.claude/agents/{planner,auditor}.md`, `prompts/agent_templates/{plan,audit,code-review}.md`, and `AGENTS.md:271`.
- **Not enforced.** No test checks it (only handoff filenames are tested). Three tracked top-level files break it:
  - `notes/backup_tests_pre-and-post_reboot.md` (added 2026-09-21)
  - `notes/PR-storm_investigation-steps.md`
  - `notes/JUNIPER_2026-07-11_JUNIPER-CANOPY_OUTSTANDING-UI-ISSUES_.md`
- **Suffixes actually used in Aug/Sep:** DESIGN 18, EVIDENCE 15, AUDIT 9, PLAN 8, ANALYSIS 6, RESULTS 4, RECORD 4, FINDINGS 4, VALIDATION 3, PROCEDURE 3, BRIEF 3, RULED 2, REGISTER 2, RUNBOOK 2, ROADMAP 1.

**`notes/templates/`.** There is no design-doc template.

| Template | Purpose | Status field |
|---|---|---|
| `TEMPLATE_DEVELOPMENT_ROADMAP.md` | "roadmaps and implementation plans" (:3). This is the de-facto plan template. | :15 `[DRAFT\|IN_REVIEW\|APPROVED\|ACTIVE\|ARCHIVED]`; header also has Last Updated / Version / Owner (:13-16). Sections include a Milestones table with Status (:67-69), a status legend Done / In Progress / Planned / Deferred / Cancelled (:119-121), Dependencies with a mermaid graph (:156), and a Change Log (:246). Its naming line (:7) predates the convention. |
| `TEMPLATE_ISSUE_TRACKING.md` | Bug/issue reports; old naming at :7 | :16 `[OPEN\|IN_PROGRESS\|IN_REVIEW\|RESOLVED\|CLOSED]` |
| `TEMPLATE_PULL_REQUEST_DESCRIPTION.md` | Long-form PR body, opt-in per `AGENTS.md:317-319`. :3 says "JuniperCanopy", a copy-paste leftover. The default PR template is `$R/.github/pull_request_template.md`. | :14 `[DRAFT\|IN_REVIEW\|READY_FOR_MERGE]` |
| `TEMPLATE_RELEASE_NOTES.md` | Release notes, `RELEASE_NOTES_v<ver>.md` in `notes/releases/` (:7) | :32 `[ALPHA\|BETA\|STABLE]` |
| `TEMPLATE_SECURITY_RELEASE_NOTES.md` | Security patch release notes | none |
| `TEMPLATE_README_PACKAGE.md`, `SNIPPET_JUNIPER_PLATFORM_CALLOUT.md` | Package README and platform callout | none |
| `ci/` (`claude.yml`, `codeql.yml`, `lockfile-update.yml`, `scheduled-tests.yml`, `security-scan-deploy.yml`, `README.md`) | GitHub workflow templates | none |

The working design/plan scaffolds live outside `notes/templates/`:
- `$R/prompts/agent_templates/plan.md`: deliverable naming at :33, "every file:line real" at :34.
- `$R/.claude/agents/planner.md`: document structure at :34-42.

**Expected header block.** The prescribed fields differ from source to source, and none of them defines a Supersedes or Superseded-by field.
- `planner.md:38`: "Project / Repository / Author / Document Type / Status / Last Updated".
- `$R/prompts/agent_templates/data/conventions.yaml:21`: `file_header_fields: [Project, Repository, Author, License, Version, Last Updated]` (no Status). Nothing in the code reads it.
- The naming doc's own header (:3-8) is a worked example of the planner form.

What Aug/Sep docs actually carry (139 docs, first 30 lines):

| Field | Docs |
|---|---|
| Project | 122 |
| Author | 117 |
| Status | 98 (41 docs have none, e.g. `PERF-LANE-P1-DESIGN`, `PERF-LANE-P2-PLAN`, `SHARED-SESSION-MEMORY-PLAN`) |
| Date | 68 |
| Sub-Project | 56 |
| License | 53 |
| Last Updated | 50 |
| Version | 43 |
| Document Type | 6 |
| Plan of record | 5 |
| Companion | 5 |
| Predecessor | 4 |
| Supersedes | 3, plus "Supersedes in part" 1 and "Supersedes (on ratification)" 1 |
| Closes | 3 |

Representative current headers:
- `$R/notes/JUNIPER_2026-09-17_JUNIPER-ML_SOAK-TEN-OWNER-DECISIONS-RULED.md:3-7`: Project, Date, Status, Supersedes, "Companion, not superseded".
- `$R/notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md:3-20`: Status, then "§8 is executable in this order", Supersedes in part, Companions.
- `$R/notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md:3-11`: list form, including `Measured at: cascor 70edfc4`.

**Frequency of Status and supersession lines.**
- Raw status lines: `**Status**:` 5,830, `**Status:**` 45, `- **Status**:` 118, plain `Status:` 5. Most come from generated requirement views (`requirements/by-status/proposed.md` alone has 1,447).
- Header status (first 25-30 lines): 337 of 617 `.md` files; 246 of 409 non-exempt; 98 of 139 in Aug/Sep.
- "supersedes": 92 lines in 72 files; 14 header-form `**Supersedes**:` lines.
- "superseded": 498 lines in 121 files.
- `Superseded-by` or `Superseded by` as a header field: 0 anywhere.

**Status vocabulary.** A header Status is free prose of the form `<UPPERCASE KEYWORD> — <qualifier, date, pointer>`. Keyword counts across the 246 non-exempt docs that have a header Status:

| Keyword | Docs | Keyword | Docs | Keyword | Docs |
|---|---|---|---|---|---|
| COMPLETE | 41 | IMPLEMENTED (3 are NOT IMPLEMENTED) | 13 | EXECUTED | 7 |
| DESIGN | 31 | PENDING | 12 | IN PROGRESS | 5 |
| ACTIVE (mostly older docs; 1 in Aug/Sep) | 21 | FINDINGS | 11 | APPROVED | 5 |
| RECORD | 18 | DRAFT | 11 | ROADMAP | 5 |
| PLAN | 16 | AWAITING | 9 | RULED | 5 |
| RATIFIED | 16 | OWNER DECISION | 9 | DEFERRED | 5 |
| SHIPPED | 16 | ANALYSIS | 9 | DESIGN OF RECORD | 7 |
| VALIDATED | 14 | CLOSED | 8 | SUPERSEDED | 4 |
| OPEN | 13 | ANSWERED / APPLIED / PROPOSED | 7 each | BLOCKED | 2 |

Rarer: SETTLED, RESOLVED, REJECTED, DECIDED (3 each); ADOPTED, DISCHARGED, ACCEPTED (2 each); CERTIFIED (1).

**The only enforced status list** is for requirements, not documents: `$R/util/requirements_consolidate.py:128` defines `STATUSES = [proposed, designed, in-progress, shipped, deferred, rejected, superseded]`. Counts in `id_assignments.yaml`: proposed 1445, shipped 177, designed 97, deferred 40, superseded 29, rejected 17, in-progress 9. The schema is in `$R/notes/requirements/README.md`, and PR verbs drive the transitions (`AGENTS.md:302-307`: `Closes` sets shipped, `Supersedes` sets superseded).

**How supersession is actually written.** Only the header Supersedes line in the successor is anything like a structured field, and it is used rarely.
1. A keyword in the superseded doc's own Status, e.g. `LOGGING-REDESIGN-DESIGN.md:9` "DESIGN — **SUPERSEDED IN PART 2026-09-02**".
2. A bold banner at the top naming the successor and the new plan of record (same doc, :13-18). 26 of the 139 Aug/Sep docs have one; kinds include "Operator surface", "RECONCILED \<date\>", "RE-BASELINED", "CORRECTED", "SUPERSEDED HEADLINE".
3. Inline `CORRECTION <date>` markers: 61 lines in 29 files.
4. "*(Superseded framing, kept for the record:)*" (`LOGGING-REDESIGN-ROADMAP.md:677`).
5. A header `**Supersedes**:` line in the successor.

**Status drift is common:**
- `$R/notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-FRONTEND-VALIDATION-PLAN.md:9` still says "DRAFT — AWAITING OWNER APPROVAL". The evidence doc `...E2E-VALIDATION-EVIDENCE.md:8` records "approved by owner 2026-08-09", and its own :7 says "PHASE 1 IN PROGRESS" although it was edited through 2026-09-12 (#1916).
- `...AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md:8` says "Draft — ratify-ready", but P1–P5 all shipped on 2026-06-25 (ml#551, #556–#559).

---

## 2. Owner decisions, rulings, blocked items, defect register

**Phrase counts:**

| Phrase | notes/ | prompts/ |
|---|---|---|
| "owner decision" (any case) | 211 lines / 77 files | 205 / 88 |
| `RULED` | 186 / 39 | 98 / 35 |
| "owner ruling" | 15 / 9 | 15 / 11 |
| "Open decisions" | 17 / 10 | 4 / 3 |
| `OPEN DECISION` | 29 / 15 | 4 / 3 |
| "blocked on" | 116 / 57 | 64 / 45 |
| `BLOCKED` | 544 / 155 | 308 / 134 |
| "decision D" | 88 / 29 | 6 / 6 |
| `D-<n>` | 1,571 lines, mostly April interface-proposal decision matrices (e.g. `...R3-02-DECISION-RESOLVED-BLUEPRINT.md`, 250 hits) | 104 |

Decision IDs are local to each document: D1, D-1, #1, "Decision A", "Decision 11", OQ-1, S-1, Q-8, N-1. There is no global decision registry; cross-references name the document, e.g. "plan §3's D-1 and D-2" in the partition design at :390.

**Example ledgers and how they move from open to ruled:**
1. **Logging roadmap** (`$R/notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`). §13 at :602-612 is a table `| # | decision | why it cannot be defaulted |`. §13.1 at :614-616 says "Ruled by the owner 2026-09-09 unless noted. This subsection is the canonical record." Transitions:
   - :618 "RESOLVED 2026-09-22 — measured 16.70 %, so P2 RUNS", with the original pre-authorisation kept at :642.
   - :665 "RULED 2026-09-10 — A2-bind".
   - :677 superseded framing kept for the record.
   - :689 "P6.1 + P6.2 + P6.3 authorised; P6.4 open."
2. **Shared-session-memory plan** §5 (`...SHARED-SESSION-MEMORY-PLAN.md:644-656`), table `| # | Decision | Recommendation |`. Row 7 at :654 reads "CLOSED 2026-09-17". The note at :658-674 links a separate brief (`...SOAK-OWNER-DECISION-7-BRIEF.md`, status "DECISION BRIEF — ... decides nothing") and the ruling document.
3. **Model persistence** (`$R/notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`):
   - §10 "Owner rulings needed" (:229-235): `| § | Question | Recommendation |`.
   - §11 "Rulings (2026-09-16)" (:243-253): `| § | Question | Ruling | vs. recommendation |`.
   - :245-247 says rulings are "recorded here rather than by rewriting §4–§6".
   - Header :6 reads "RULED 2026-09-16".
4. **Standalone ruling records:**
   - `...SOAK-TEN-OWNER-DECISIONS-RULED.md:33-44`: `| # | decision | ruling | state |` for D1–D10, where state is "implemented, ml#1952" / "recorded here" / "no change needed"; §3 "What remains open" at :179. Header :6 says it supersedes §6 of a handoff and decision #7 of the plan.
   - `$R/notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md:52-148`: each decision has a "Gate before it lands" and a "Not decided" part (:148). The table at :152-161 separates executable, host-bound, and "blocked on D2" items.
5. **Backup design** §10 (`...BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md:2132-2149`): `| ID | Decision | Recommendation |` for D-1..D-14, flagged "**Rule before P0**", "**Re-decide**" or "**New**". Notes D-12a to D-14a follow at :2151-2158.

Other forms:
- The first Cursor-flood analysis records the owner's answers inline: "- Answer: i concur with recommendation." (`...CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md:699, :707, :716`) and "- Answer: this question will require additional research, planning, and discussion" (:730).
- The partition design uses section headings for decisions (`...TRAIN-EVAL-TEST-PARTITION-DESIGN.md`): "Owner decisions — SETTLED 2026-08-29" (:363), "Still open — carried forward" (:373), "Decision 11 — ... Ruled 2026-09-02" (:856), "Decision 9 REVERSED" (:956), "Decision 10 COLLAPSED" (:972).
- Rulings record the chosen and the rejected options. The defect register explains why at :323-326: "a ruling that records only its outcome is indistinguishable later from a drift".

**How blocked items are written.** They appear as prose in status cells or sections, not as a field:
- The perf-lane P2 plan work table `| # | Item | Repo | Size | Depends on |` (:139) puts the status at the front of the Item cell: DONE 12, ANSWERED 2, SHIPPED 1, EXECUTED 1, DECIDED 1, PARTIALLY DISCHARGED 1, and "**BLOCKED 2026-09-10 — ... INERT**" (:336).
- The container-registry plan (:53, :273): "blocked on the five `DOCKERHUB_TOKEN` secrets".
- The logging roadmap (:574): "Gated on P5. Retained so the deferral is a recorded decision."
- Handoffs use sections like "### Still owner-gated — do NOT start these unprompted" (`HANDOFF_2026-09-17_container-registry...:122`).

**Defect register** (`$R/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; 1,557 lines; "Living register"; Last Updated 2026-09-22):
- **IDs** are `APD-<REPO>-<NNN>`. Retired IDs are never reused; a split becomes `-001a` / `-001b` (:25-29).
- **§4 rows** use `| ID | Finding | Sev | Source | Primer | Conf |` (:764). Sev is one of S/C/R/M/E; `†` marks entries the register found itself (:760). A row is OPEN unless the Finding cell starts with `**FIXED (<pr>)** — ...`.
- **§5.1 rows** use `| ID | Finding | Fixed by | Verification |` (:1426).
- **Closing a row** means five edits (:54-62). The machine-readable token is `**FIXED` (:70-72); `$R/util/ad-hoc/register_open_set.py:21-22` counts on it, and two tests are wired into CI (`ci.yml:1005-1006, :1047-1048`).
- **"Parked" rows** come in three forms: parked in the row itself, parked as part of a named group, or parked by text in another row's cell (:94-98). The operating rule (:104) is that all three count as parked.
- **Owner rulings** are recorded in §2.4 (:321-345). The summary is at :161-185: 96 entries, 81 fixed.
- :43-52 matters for your design: the close protocol once existed only in the handoff chain and got lost when one handoff dropped it. "A rule that lives only in the document that hands off the work stops existing the first time one successor omits it."

---

## 3. Active arcs as of 2026-09-22

**Handoff archive:** 210 files, all prefixed `HANDOFF_`. By month: Apr 6, May 14, Jun 29, Jul 11, Aug 94, Sep 56.

**15 most recent by filename date** (2026-09-11 has three more: ci-tools-0-9-0, container-registry-oq1, cursor-fleet-round-2-closed):

| # | File (`$R/prompts/thread-handoff_automated-prompts/`) | Subject (H1) |
|---|---|---|
| 1 | `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` | Container registry: ten PRs landed on 09-21; the published worker still reports 0.4.0. Header :5 "PARTLY CONSUMED". |
| 2 | `HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md` | The structure screen was blind to its founding incident; five open items in `util/experiments/`. Successor of the Cursor-fleet chain (:6). |
| 3 | `HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md` | Perf lane: `runtime:` block binds, D6's premise false. This is HEAD #2013. |
| 4 | `HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md` | Logging: Phase 1 complete; the gate opened P2; P0.4 is next. |
| 5 | `HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md` | Register round 41. |
| 6 | `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` | Canopy selection: four owner decisions shipped. Supersedes #14 (:6). |
| 7 | `HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md` | Register round 40. |
| 8 | `HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md` | Backup redesign: consensus round 1; §8 must not be executed. |
| 9 | `HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md` | Marked "SUPERSEDED 2026-09-22" at :18. |
| 10 | `HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md` | "RE-EVALUATED 2026-09-21" at :6. |
| 11 | `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` | Round 39; 10,091 words. |
| 12 | `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md` | Header :5-6 "**Successor**", "SUPERSEDED / CONSUMED 2026-09-17". |
| 13 | `HANDOFF_2026-09-12_decision-11-release-train-complete-nine-on-pypi.md` | :3-4 re-evaluation "OVERTURNS ... the arc is DONE"; §8 at :179 "the arc is NOT done". |
| 14 | `HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md` | :18 "nothing after 2026-09-12 supersedes it", later contradicted by #6. |
| 15 | `HANDOFF_2026-09-11_perf-lane-burst-terminator-is-the-result-queue-unpickle-and-the-getter-repins.md` | Perf-lane burst terminator. |

**Notes churn since 2026-08-22** (commits per file; `git log --name-only`):

| Commits | File |
|---|---|
| 61 | `DEFECT-REGISTER` |
| 49 | `CANOPY_E2E-VALIDATION-EVIDENCE` |
| 25 | `E2E-CLICK-BY-CLICK-TEST-MATRIX` |
| 21 | `PERF-LANE-P2-PLAN` |
| 18 | `DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION` |
| 15 | `TRAIN-EVAL-TEST-PARTITION-DESIGN` |
| 12 | `CONTAINER-REGISTRY-PUBLISHING-PLAN` |
| 11 | `CANOPY_SELECTION-REACHABILITY-DESIGN` |
| 10 | `SHARED-SESSION-MEMORY-PLAN` |
| 7 each | `LOGGING-REDESIGN-ROADMAP`, `POINTER-FOLLOW-SOAK-LEDGER` |
| 6 each | `SOAK-TRIGGER-DESIGN-CONVERSATION`, `ASYNC-JOB-PATTERN-DECISION-ANALYSIS`, `PERF-LANE-P1-DESIGN`, `PARTITION-IMPLEMENTATION-PLAN`, `SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN` |

In the last 10 days the leaders are `CONTAINER-REGISTRY-PUBLISHING-PLAN` (10), `DEFECT-REGISTER` (6), and `DOCKERHUB-SECRET-REGISTRATION-PROCEDURE` and `LOGGING-REDESIGN-ROADMAP` (3 each).

**Arcs, their main document, and latest handoff** (notes files under `$R/notes/`, handoffs under `$R/prompts/thread-handoff_automated-prompts/`):

| Arc | Main document(s) | Latest handoff and current state |
|---|---|---|
| **Perf lane** | `JUNIPER_2026-09-02_JUNIPER-ECOSYSTEM_PERF-LANE-P2-PLAN.md` (waves 0–5). Also the phase gate `...2026-08-16_...PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md`, `...2026-08-31_...PERF-LANE-P1-DESIGN.md`, rulings `...2026-09-11_...PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`, and the newest `...2026-09-22_...PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`. | `HANDOFF_2026-09-22_perf-lane-d2-binds-...` |
| **Logging redesign** (cascor#573) | `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`, the plan of record per the design's banner. Also `...08-29_...LOGGING-REDESIGN-DESIGN.md` (superseded in part), `...09-02_...LOGGING-CURRENT-STATE-RECONCILIATION.md`, `...09-09_...LOGGING-PER-LOGGER-LEVELS-DESIGN.md`. | `HANDOFF_2026-09-22_logging-arc-phase-1-complete-...`; P2 runs (roadmap :618). |
| **Backup redesign / Duplicati migration** | `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("VALIDATED (round 2)"), plus the ROUND-1, ROUND-2, STEP-REPORTS and HANDOFF-CONSENSUS records. Predecessors: `...08-23_...DUPLICATI-FRESH-BACKUP-SET-PLAN.md` and `...08-25_...DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`. | `HANDOFF_2026-09-21_backup-redesign-...`; reconciliation was completed 09-22 (design §12 :2265-2266). |
| **Canopy E2E** | `JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` with `...E2E-CLICK-BY-CLICK-TEST-MATRIX.md` and `...E2E-FRONTEND-VALIDATION-PLAN.md` | `HANDOFF_2026-09-10_canopy-e2e-f035-fixed-...` |
| **Canopy selection reachability** | `JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` (plus DEADLOCK proposals and validation, and the recurrence `MODEL-PERSISTENCE-DESIGN`, which "Closes: Y2") | `HANDOFF_2026-09-22_canopy-selection-four-decisions-...` |
| **Cursor fleet** | `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` ("Active — the flood is still running"); round 1 in `...07-28_...CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` | `HANDOFF_2026-09-11_cursor-fleet-round-2-closed-...`, succeeded by `HANDOFF_2026-09-22_structure-screen-...` |
| **Decision 11 / partition + release train** | `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` §9.5 (:856); `...08-30_...PARTITION-IMPLEMENTATION-PLAN.md` ("LARGELY DISCHARGED") | `HANDOFF_2026-09-12_decision-11-...`; §8 "NOT done". |
| **CI budget** | `JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` ("RECORD of a completed arc"; §7 :274-291 lists what is still the owner's) | `HANDOFF_2026-09-09_ci-budget-...`, "RE-EVALUATED 2026-09-22" (:12). |
| **Container registry** | `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` ("ACCEPTED"; Wave 4 blocked); `...2026-09-22_...DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` ("READY TO EXECUTE — owner action") | `HANDOFF_2026-09-22_ten-prs-landed-...` |
| **Defect register** | `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` | Round 41 (09-22) |
| **Soak / shared session memory** | `JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`, `...09-17_...SOAK-TEN-OWNER-DECISIONS-RULED.md` (§3 open items), `...08-18_...SHARED-SESSION-MEMORY-PLAN.md` | `HANDOFF_2026-09-09_soak-arc-evidence-recovered-...`; its §6 was superseded by the 09-17 ruling. |
| **Worktree cleanup v3** | `JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md` ("DESIGN, revision 2"; rev 1 rejected by consensus) | none newer |

There is no index of active docs under `notes/` (the only README/INDEX files are for requirements, legacy and templates/ci). The de-facto active-arc index is the Claude auto-memory `MEMORY.md`, which lives outside the repo. Its in-repo baseline is `$R/conf/memory_index_baseline.json`: 137 slugs (97 `project_*`, 21 `reference_*`, 18 `feedback_*`, 1 `user_*`); the last sample on 2026-08-24 was 137 rows and 20,620 bytes.

---

## 4. Thread-handoff procedure

**The procedure doc** (`$R/notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`, Last Updated 2026-07-04):
- **When to hand off (:22-39):** within 95–99% of the compaction threshold, after 15+ tool calls or 5+ edited files, at a phase boundary, on degraded recall, at a multi-file transition, or on user request. Also lists when not to.
- **Step 1, checkpoint (:45-53):** five questions — original task, completed, remaining, discovered, files in play.
- **Step 2, goal (:55-82):** skeleton "Continue [TASK]. / Completed so far / Remaining work / Key context". Rules: be specific, include paths, state decisions, state verification status, ~1,200 words.
- **Word-count amendment (:84-114):** raised from ~500 on 2026-08-30. A census of 148 handoffs found a median of 1,150 prose words (IQR 778–2,718). There is no gate on this number, unlike the memory budget's `Allow-Ceiling-Raise`.
- **Step 3 (:116-120):** present the goal, archive it, and state branch, git status, staged files and uncommitted work.
- **Step 4 (:122-143):** filename `HANDOFF_YYYY-MM-DD_<session-description>.md`: date first, hyphenated ASCII slug, sequencing goes in the slug.
- **Templates (:147-225):** Dependency Update, CI/CD Pipeline Change, Documentation/Package Restructure, Multi-Phase Task.
- **Best practices (:229-236):** include the verification command; state git status.

**What a handoff must contain:** `AGENTS.md:329-402` makes the procedure mandatory. Steps at :390 (archive filename), :391-392 (verification commands) and :393 (git status: branch, staged, uncommitted).

**Enforcement:** `$R/tests/test_thread_handoff_archive.py`, wired at `ci.yml:351-353`:
- :23 archive names must match `^HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md$` and be ASCII.
- :48-59 every `HANDOFF_*.md` named in a top-level `notes/*.md` must exist in the archive.

**Practice has grown beyond the template** (September, 56 handoffs):
- Verification or preflight section: 52.
- Git state stated: 44.
- Traps section: 44.
- Consensus or validation record: 33.
- Most common headings: "traps" (18), "validation record" (13), "goal statement" (12), "verify starting state" (11), "git status" (11), "git status at handoff" (10).
- Chain fields: `**Session**` 26, `**Predecessor**` 19, "Successor to" 19, `**Worktree**` 12.
- Lifecycle banners: SUPERSEDED/CONSUMED, PARTLY CONSUMED, RE-EVALUATED, and "THE PREDECESSOR IS NOT SUPERSEDED — but it has been AMENDED IN PLACE" (`HANDOFF_2026-09-22_perf-lane...:6`).

---

## 5. Existing docs on orchestration, session automation, fleet, and session memory

There are zero hits in `notes/` for `Workflow tool`, `workflow(`, `ultracode`, `agent()` or "Agent SDK". Nothing in the repo discusses Workflow-tool style scripted orchestration.

| Doc (`$R/notes/`) | Status | What it proposed, and did it ship |
|---|---|---|
| `JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md` | "Analysis — one recommendation is an owner decision, nothing implemented" (:6) | Splits soak sessions into six roles (:25-32): Subject (never automate), Orchestrator (done in ml#1561, `util/soak_run_probe.py`), Scorer (candidate), Interpreter, Registry author, Analyst (never). A keyword scorer is refuted (:69-143). An automated scorer must be a separate headless session, calibrated blind against a 36-row answer key (:145-185). Review fixed a leak of coverage data into the scorer packet and added a stopping rule (:232-244). Recommendation (:281-288): "Automate nothing further right now". **No scorer was built.** |
| `JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` | No header Status; Version 0.7.1, Last Updated 2026-08-31 | Adopt proposals C (dedup/prune) and D (ratchet); reject B; reject A's thesis (:39-43). Phases P0–P5 (:126-131). **Shipped:** P0–P4 DONE (:492-640), P5 "CUT COMPLETE" across 8 repos (:218-220), and the gate `conf/memory_budget.json` + `util/memory_budget_check.py`. Key rule at :536-539: "detail may be demoted to the corpus; STATUS may not." |
| `JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` | "COMPLETE (soak) / OPEN (ladder)", verdict INCONCLUSIVE (:5-7) | §20 (:1070-1120): local headless `claude -p` is the only usable fresh-session instrument. Subagents, cloud routines and `CronCreate` all failed (table :1093-1098). **Shipped:** `util/soak_run_probe.py` and `$R/util/systemd/juniper-soak-probe.{service,timer,path}` (timer 03/09/15/21:23; the path unit watches `MEMORY.md`). Policy since then: D1 "Named probe only, on request — no default or timer campaign" (SOAK-TEN :35). |
| `JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` | "Blue-sky ... nothing here is a decision" (:6) | Treats triggers as a sampling strategy (timer / event / retrospective scoring). Not shipped as policy. |
| `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` | "Adopted 2026-08-30" (:5) | Multi-agent verification: Lane A (re-measure from different starting points) and Lane B (argue against the conclusion) (:34-73); a sizing matrix of uncertainty × criticality (:77-98); iteration rules (:102-119); the reconciler's job (:123-136); a minimum record (:157-168). **In active use** (backup design §11, soak role analysis §6a, handoff consensus records). |
| `JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md` | "RATIFIED — round-1 build authorized" (:9) | **Shipped:** `$R/.claude/agents/{planner,auditor,task-executor,prompt-validator,fleet-supervisor,mock-seam-auditor}.md`, skills `template-agent` / `service-smoke` / `ui-test-author`, and `prompts/agent_templates/` with its manifest and RUBRIC. Follow-ons: `...06-25_...AGENT-SUITE-CONVENIENCE-UTILITIES-DESIGN.md` (header says Draft; actually shipped) and `...06-27_...CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md` ("AWAITING OWNER APPROVAL"). |
| `JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md` | "Draft" | A taxonomy of prompt types. Later realized as `prompts/prompt_templates/` and `agent_templates/`. |
| Cursor fleet: `...07-28_...CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`; `...07-30_...CURSOR-DASHBOARD-CONFIG-REQUESTS.md`; `...09-05_...CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`; `...09-06_...DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md` | Round 1 "Complete — ... three validated guardrail proposals awaiting owner decisions" (:6); dashboard pack "Owner action pack — dashboard-only" (:6); round 2 "Active" (:5); docs residue "Evidence record" (§6 closed 2026-09-11) | The fleet is 5 Cursor automations whose configuration is dashboard-only (flood-2 :33-40). Merging one PR at a time degrades (:184-211); open items are at :249-281. **Shipped:** `.claude/agents/fleet-supervisor.md` with `util/fleet_triage/predict_merge.py`; Sequence Safety (now a required check); the advisory Fleet PR Lint job (`ci.yml:1388-1402`). |
| `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARENT-AGENTS-GOVERNANCE-AND-WORKTREE-SETTINGS-ASYMMETRY.md` | "Analysis — owner decisions required, nothing implemented" (:5) | Plan §5 rows 8–9: the unversioned parent `Juniper/AGENTS.md`, and worktree sessions running without the main checkout's local settings. |
| `JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md` | "DESIGN, revision 2"; "Supersedes (on ratification)" (:6-11) | Multi-worktree cleanup policy; revision 1 was rejected by 4 reviewers. Not ratified. |

---

## 6. Memory budget and the gates that apply to `notes/`

**Memory budget.** `$R/conf/memory_budget.json` governs only `AGENTS.md` (:31-36). `CLAUDE.md` is a symlink to `AGENTS.md`, so it is governed too.
- **Ceiling:** 38,000 characters (:33). It was ratcheted down from 45,084 on 2026-08-23; the target is 32,443.
- **Current size:** 28,273 characters (28,476 bytes), so about 9.7K characters of headroom.
- `docs/REFERENCE.md` is deliberately not governed (:27-29).
- **Rules** in `$R/util/memory_budget_check.py:22-35`: a hard ceiling, no-worsening (an over-ceiling file only fails if the change grows it), and a ratchet that can only tighten.
- **Waivers:** `Allow-Budget-Overrun:` is a loan that leaves the ceiling in place (:37-42); `Allow-Ceiling-Raise:` is separate (:88-92). Missing inputs fail closed (:44-50).
- **CI:** the `Memory Budget` job is **blocking** (`ci.yml:1163-1235`), with an advisory relocation check (G3) at :1237-1253.
- `MEMORY.md` (outside the repo) has its own tool, `util/memory_index_check.py`. It silently truncates at 200 lines / 25,000 bytes (:15-16), and new entries have a 120-byte cap on the text after the link (:29-37). It is not a CI gate.

**A new `notes/` document is not subject to any size gate.** It is subject to the following:

| Gate | Applies to new notes docs? | Evidence |
|---|---|---|
| markdownlint | **No.** `notes/`, `docs/`, `prompts/` and `CHANGELOG.md` are excluded, even though `AGENTS.md:268, :270` says markdown follows `.markdownlint.yaml` (512 line length). | `$R/.pre-commit-config.yaml:241`; `$R/.markdownlint.yaml:9-10` |
| Documentation Links (`juniper-check-doc-links`) | **Yes.** Scans the whole repo, excluding dirs named templates, history, legacy, pull_requests, releases, analysis, fixes, development, plus `CHANGELOG.md`; `--cross-repo skip`. | `ci.yml:1564-1579`; `.pre-commit-config.yaml:251-278` |
| Markdown structure delta (required step in the docs job) | **Yes.** A newly added file must be clean from zero: balanced fences, no H2 inside a bare or unclosed fence, tables with a separator row. | `ci.yml:1595-1605`; `$R/util/markdown_structure_delta.py:67-80` |
| Markdown structure C1–C4 | Advisory only. C4 flags deleted or renamed headings. | `ci.yml:1607-1640` |
| Sequence Safety docs screen (required in the ruleset) | **Yes, on edits.** Covers `AGENTS.md`, `docs/**/*.md` and `notes/**/*.md`. Fails on a deleted heading (a same-hunk retitle only warns) and on 5+ consecutive deleted lines with nothing added. Waiver: an `Allow-Docs-Rewrite: <path>` commit trailer, or the owner's `docs-rewrite` label (warn-only). | `ci.yml:1357-1373`; `$R/juniper-ci-tools/juniper_ci_tools/docs_additions_check.py:21-40, :56, :62-66` |
| Handoff-reference test | **Yes**, for top-level notes that name a handoff file. | `tests/test_thread_handoff_archive.py:48-59` |
| Naming convention | **No gate.** | 3 tracked files violate it |
| Requirements source citations | Indirect. `id_assignments.yaml` cites notes paths and line ranges; CI only runs fixture tests of the checker, not a live check. | `util/requirements_drift_check.py`; `ci.yml:384-388` |
| Defect-register close protocol | Only when editing the register | `ci.yml:1005-1006, :1047-1048` |
| `prompts/**` | Excluded from all pre-commit hooks; only `tests/test_template_library_drift.py` guards the templates | `.pre-commit-config.yaml:44`; `prompts/agent_templates/README.md:9-11` |

---

## Observations that matter for your workflow

- **No machine-readable status or supersession field exists on design docs.** Status is a free-prose line (41 of 139 recent docs have none) and goes stale. Supersession is a banner or a status keyword in the older doc; there is never a `Superseded-by` field. The only enforced status list is the requirements one (`util/requirements_consolidate.py:128`).
- **The live state of each arc sits in the handoff chain, not the design doc.** Chain fields are Predecessor / Successor-to, and lifecycle is recorded as CONSUMED / RE-EVALUATED / AMENDED IN PLACE banners. Handoffs regularly correct the status their own design doc claims (e.g. decision-11 §8 at :179).
- **The repo already keeps state resident on purpose.** The shared-memory plan (:536-539) forbids relocating a status out of the index row that carries it, and the defect register (:43-52) moved its close rule out of the handoff chain after a handoff dropped it.
- **Edits to existing docs are effectively append-only.** Rulings are added in new sections rather than rewriting old ones, which is consistent with the docs screen failing on deletions.

---

## Checklist: conventions a new design doc must satisfy

Items marked **[gated]** fail CI; the rest are convention only.

1. **Filename** `JUNIPER_<YYYY-MM-DD>_JUNIPER-<REPO>_<PHRASE>.md`: UPPER-KEBAB phrase, one of the 10 repo tags (ECOSYSTEM for cross-repo, ML for juniper-ml tooling and procedures), date = creation date. Source: naming doc :14-39; `AGENTS.md:271`; `planner.md:46-52`.
2. **End the phrase with a doc type**: `-DESIGN`, `-PLAN`, `-ROADMAP`, `-ANALYSIS`, `-AUDIT` or `-CODE-REVIEW`. Source: naming doc :32; `plan.md:33`.
3. **Put it at the top level of `notes/`**, not in an exempt subdirectory. Source: `conventions.yaml:15-19`; naming doc :41-51.
4. **Never overwrite:** refuse and report if the path already exists. Source: `planner.md:51-52`; `plan.md:33`.
5. **Header block:** Project, Repository or Sub-Project, Author, Document Type, Status, Last Updated; License and Version by practice. Write Status as `<KEYWORD> — <qualifier/date/pointer>`. Source: `planner.md:38`; `conventions.yaml:21`; observed practice.
6. **Lineage in the header where it applies:** Supersedes, Supersedes in part, Companion, Plan of record, Closes, Predecessor, Tracks, Measured at \<sha\>. Source: SOAK-TEN :6-7; BACKUP :14-20; LOGGING-ROADMAP :10-11.
7. **Grounding:** every `file:line` must be real and tied to a commit SHA; anchor on quoted text rather than line numbers. Source: `planner.md:22-31, :55-61`; `plan.md:34, :43`; register :78-80.
8. **Body structure:** background, scope and non-goals, options and trade-offs, chosen approach, a roadmap of single-work-unit (one-PR) steps, open questions, risks, verification strategy. Source: `planner.md:34-42`; `plan.md:25-28`.
9. **Owner decisions** go in an explicit table (ID, question, recommendation or why it can't be defaulted). Record answers later in a "Rulings" subsection with chosen and rejected options, without rewriting the earlier sections. Source: `planner.md:26-28`; model-persistence :229-253; logging roadmap :602-616; register :323-326.
10. **Never demote or misreport open/closed status** when moving detail elsewhere. Source: SHARED-SESSION-MEMORY-PLAN :536-539.
11. **Documents of record** need independent-agent consensus sized by the §3 matrix, plus the §7 minimum record: instrument and its adequacy, sample size, agents per lane and their starting points, iterations and what the last one changed, unresolved dissent, what the evidence cannot support. Source: consensus procedure :5-7, :77-98, :157-168; `planner.md:60-61`.
12. **All links must resolve [gated].** Any handoff named in a top-level note must exist in the archive **[gated]**. Source: `ci.yml:1564-1579`; `tests/test_thread_handoff_archive.py:48-59`.
13. **Clean markdown structure for a new file [gated]:** balanced fences with info strings, no H2 swallowed by a fence, tables with separator rows. Source: `util/markdown_structure_delta.py:67-71`.
14. **Later edits and supersession are additive:** status line, banner, inline `CORRECTION <date>`. Deleting a heading or 5+ lines needs an `Allow-Docs-Rewrite: <path>` trailer in the squash commit **[gated]**. Source: `docs_additions_check.py:21-40`; LOGGING-REDESIGN-DESIGN :9-22.
15. **Name every document referenced or changed, by filename,** in summaries, PR bodies and handoffs. Source: `AGENTS.md:272-275`.
16. **Supporting scripts go under `util/` or `util/ad-hoc/`**, never `/tmp`. Source: `AGENTS.md:277-290`.
17. **Pointers belong in `docs/REFERENCE.md`, not `AGENTS.md`**; growth in `AGENTS.md` (and so `CLAUDE.md`) is capped at 38,000 characters with the no-worsening rule **[gated]**. Source: `conf/memory_budget.json:27-36`; `ci.yml:1195-1235`.
18. **Land it by PR:** one PR per work unit, the owner merges, include a `## Requirements` JR-ID section where relevant. Source: `standing_rules.yaml:5-17`; `AGENTS.md:296-315`.

**Key files** (absolute):
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/.claude/agents/planner.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/.claude/agents/fleet-supervisor.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/prompts/agent_templates/plan.md`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/prompts/agent_templates/data/conventions.yaml`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/conf/memory_budget.json`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/memory_budget_check.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/markdown_structure_delta.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/juniper-ci-tools/juniper_ci_tools/docs_additions_check.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/tests/test_thread_handoff_archive.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/util/requirements_consolidate.py`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/.github/workflows/ci.yml`
- `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/structured-inventing-fairy/.pre-commit-config.yaml`


---

## Report I4 — documented behaviour probe 1 (usage limits, Workflow tool, subagents, headless, hooks, sessions, worktrees)

*Verbatim final message of agent `ae320700a4d09c7fc`, delivered 2026-09-23T01:40:42.937Z; transcript `subagents/agent-ae320700a4d09c7fc.jsonl`.*

Based on my fetch of the Claude Code documentation, here is a precision analysis of your seven questions. I'll separate documented facts (with source URLs) from what is not documented.

---

## 1. Usage Limits: Session (5-Hour) and Weekly Limits

**DOCUMENTED:**

- **Session and weekly limits exist but are not detailed in the monitoring/usage docs.** (source: https://code.claude.com/docs/en/monitoring-usage.md — page is about OpenTelemetry telemetry, not usage limits)
- **The `/usage` command does not exist.** The documentation does not mention a command to observe current utilization or reset times. (source: searching https://code.claude.com/docs/en/cli-reference and related pages)
- **When a running session hits usage limits,** workflows pause (not fail): "When an agent hits your claude.ai [usage limit](https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset), the run pauses rather than failing that agent: the agents that hit the limit wait for the reset, and no new agents start." (source: https://code.claude.com/docs/en/workflows.md under "When a run hits your usage limit")
- **For non-interactive (`claude -p`) runs, workflows do NOT pause.** Instead, "A run doesn't pause in [non-interactive mode](https://code.claude.com/docs/en/headless) with `claude -p`... when one doesn't, the affected agent fails instead." (source: https://code.claude.com/docs/en/workflows.md)
- **The `--max-budget-usd` flag exists** for cost capping: runs stop at that cost. (source: implied in https://code.claude.com/docs/en/workflows.md cost section; also see https://code.claude.com/docs/en/costs.md)
- **Subagents respect usage limits via `autoContinueAtUsageLimit` setting.** (source: https://code.claude.com/docs/en/settings-reference#autocontinueatusagelimit)
- **Workflow runs pause when usage limit resets within 24 hours**, but if reset is >24 hours away or a subagent waits twice already, the agent fails. (source: https://code.claude.com/docs/en/workflows.md, "When a run hits your usage limit")

**NOT DOCUMENTED:**

- Exact mechanism of "5-hour rolling session limit" and "weekly limit" — the docs do not explain how these are calculated or when they reset.
- Programmatic hook for 429 / rate-limit hit (no documented `RateLimit` or `UsageLimit` hook event).
- CLI flag like `--usage` or `--remaining-budget` to query current utilization.
- Exact HTTP response body for a 429 (the phrase "You've hit your session limit · resets HH:MM" you mentioned is not in the docs).
- OTel metric or status-line field exposing remaining budget or reset time.
- **`claude` status line / statusline JSON:** The docs mention `/config statusline` for UI configuration but do not document a `rate_limit`, `remaining_usage`, or `reset_time` field. (source: https://code.claude.com/docs/en/statusline.md — fetch this if available, but it's not listed in the docs map)

---

## 2. Workflow Tool: Definition, Invocation, Budget, Resume

**DOCUMENTED:**

- **Workflow definition:** A JavaScript file at `.claude/workflows/<name>.js` with:
  - `export const meta = { name, description, ... }`  
  - Plain JavaScript body using `agent()`, `pipeline()`, `parallel()`, `phase()`, `log()` (source: https://code.claude.com/docs/en/workflows.md, "What the saved script looks like")
- **Invocation:**
  - `ultracode` keyword in a prompt triggers workflow generation (https://code.claude.com/docs/en/workflows.md, "Ask for a workflow in your prompt")
  - `/effort ultracode` to auto-generate workflows for every substantive task (https://code.claude.com/docs/en/workflows.md, "Let Claude decide with ultracode")
  - `/deep-research` bundled workflow (https://code.claude.com/docs/en/workflows.md, "Bundled workflows")
  - Saved workflows via `/<name>` command (https://code.claude.com/docs/en/workflows.md, "Save the workflow for reuse")
  - `--save-location .claude/workflows/` or `~/.claude/workflows/` (source: https://code.claude.com/docs/en/workflows.md)
- **Budget directive (undocumented in config but referenced):**
  - The docs mention a `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` environment variable for prefix stagger (default 5000ms), which can be set to 0 (https://code.claude.com/docs/en/workflows.md, "Prompt caching in a fan-out")
  - No documented `+500k token-budget` directive; token limits are inferred from the 1.5M projected-token warning (https://code.claude.com/docs/en/workflows.md, "Cost" section)
- **Concurrency cap:** "Up to 16 concurrent agents by default... set [`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`](https://code.claude.com/docs/en/env-vars#variables) to a value from 1 to 256" (https://code.claude.com/docs/en/workflows.md, "Behavior and limits")
- **Resume semantics:** Completed agents return saved results; failed agents and agents started after one fails re-run. (https://code.claude.com/docs/en/workflows.md, "Resume after a pause")
- **Headless triggering:**
  - `claude -p` with a prompt that names `/deep-research` or a saved workflow runs it non-interactively (https://code.claude.com/docs/en/headless.md — the `-p` docs show workflows can start in headless mode)
  - Workflows spawn in response to a scheduled routine's trigger (https://code.claude.com/docs/en/routines.md, "a routine is... a prompt... packaged once and run automatically")
  - No documented way to trigger a workflow from `CronCreate` / `/loop` directly; you would need to ask Claude in the loop to run a workflow

**NOT DOCUMENTED:**

- Exact syntax for the "+500k token-budget" directive (if it exists).
- Whether a workflow can be named in a `CronCreate` call to repeat its execution.
- Exact structure of `args` when a saved workflow accepts input (e.g., is it always an object, or can it be an array?).
- Whether workflow scripts can call `agent()` from within another `agent()`'s result handling (nested agent spawning).

---

## 3. Subagents: Frontmatter, Isolation, Resume, Hooks

**DOCUMENTED:**

- **Frontmatter fields** (source: https://code.claude.com/docs/en/sub-agents.md, "Key Frontmatter Fields"):
  - `name` (required) — unique identifier
  - `description` (required) — when Claude should delegate to this agent
  - `tools` — comma-separated or YAML list of allowed tools
  - `disallowedTools` — blocklist (source: same page, "Control Tools and Permissions")
  - `model` — `sonnet`, `opus`, `haiku`, `inherit`, or full model ID
  - `permissionMode` — `default`, `auto`, `plan`, `acceptEdits`, `dontAsk`
  - `skills` — skills to preload at startup
  - `memory` — `user`, `project`, or `local` for persistent memory
  - `isolation` — set to `worktree` for isolated git operations (source: https://code.claude.com/docs/en/sub-agents.md, "Isolate Git Operations")
  - `maxTurns` — maximum agentic turns before stopping
  - **Hooks:** agent frontmatter can declare hooks (source: https://code.claude.com/docs/en/sub-agents.md, "Define Lifecycle Hooks")

- **`isolation: worktree`:** "Runs the subagent in a temporary git worktree, giving it an isolated copy of the repository." Each subagent gets its own temporary worktree that Claude Code removes when the subagent finishes without changes. (source: https://code.claude.com/docs/en/sub-agents.md and https://code.claude.com/docs/en/worktrees.md, "Isolate subagents with worktrees")

- **Resume via `SendMessage`:** "When a subagent completes, Claude can resume it with `SendMessage`: ... Resumed subagents retain: Full conversation history, All previous tool calls and results, Where they left off (no restart needed)." (source: https://code.claude.com/docs/en/sub-agents.md, "Resume Subagents")

- **SubagentStart / SubagentStop hooks:**  
  - NOT explicitly named in the frontmatter fields list.
  - The docs mention `SubagentStop` and `SubagentStart` in the hooks-guide context but do NOT give their JSON input/output schema. (source: searching https://code.claude.com/docs/en/hooks-guide.md and https://code.claude.com/docs/en/hooks.md)

**NOT DOCUMENTED:**

- **Exact JSON payload for `SubagentStart` and `SubagentStop` hook events** — the hook reference summary I fetched lists them as possible events but does not show their input/output fields.
- Whether a subagent can read its own `MEMORY.md` file automatically.
- Whether `maxTurns` applies to the subagent's own conversation or the conversation that spawned it.
- Full details of what the `inherit` model option does when a subagent specifies it.

---

## 4. Headless / Scheduled Operation: CLI Flags, Routines, Cron, Hooks

**DOCUMENTED:**

- **`claude -p` flags** (source: https://code.claude.com/docs/en/headless.md):
  - `--output-format json|stream-json` — structured output
  - `--continue` — continue most recent session
  - `--resume <session-id>` — resume specific session
  - `--max-turns <n>` — documented implicitly (the tool reference lists it, source: https://code.claude.com/docs/en/cli-reference)
  - `--permission-mode auto|acceptEdits|dontAsk` — (https://code.claude.com/docs/en/headless.md, "Auto-approve tools")
  - `--allowedTools <list>` — pre-approve tools
  - `--append-system-prompt <text>` — (https://code.claude.com/docs/en/headless.md, "Customize the system prompt")
  - `--bare` — skip auto-discovery (https://code.claude.com/docs/en/headless.md, "Start faster with bare mode")
  - `--worktree <name>` / `-w` — create or reuse worktree (https://code.claude.com/docs/en/worktrees.md, "Start Claude in a worktree")
  - `--permission-prompts none` — deny unprompted requests (https://code.claude.com/docs/en/headless.md, "Turn off permission prompts in unattended runs")
  - `--agents <json>` — pass custom agent definitions (https://code.claude.com/docs/en/headless.md, "To load" table)
  - `--json-schema <schema>` — structured output schema (https://code.claude.com/docs/en/headless.md, "Get structured output")
  - **NOT `--max-budget-usd`** — I do not see this flag in the headless docs for `-p`; it appears only in the workflow section.

- **`/schedule` routine feature** (source: https://code.claude.com/docs/en/routines.md):
  - Cloud scheduled agents with cron syntax (preset: hourly, daily, weekdays, weekly; custom via `/schedule update` with cron expression)
  - Minimum interval: 1 hour
  - Triggers: schedule, API (`/fire` endpoint), GitHub events
  - Environment: cloud (Anthropic-managed by default, or org self-hosted)
  - Can access only cloned repositories, not local files
  - Runs autonomously (no permission prompts unless artifact publishing)
  - Transcripts saved to session storage

- **`/loop` for local scheduling** (source: https://code.claude.com/docs/en/scheduled-tasks.md):
  - `/loop <interval> <prompt>` — fixed schedule on cron
  - `/loop <prompt>` — Claude chooses interval dynamically
  - `/loop` — built-in maintenance prompt on dynamic interval
  - Interval units: `s`, `m` (seconds, minutes, hours, days)
  - Minimum: 1 minute
  - Cron syntax via `CronCreate` tool
  - Tasks expire after 7 days
  - Can use `CronCreate`, `CronList`, `CronDelete` tools directly

- **`CronCreate`, `CronList`, `CronDelete` tools** (source: https://code.claude.com/docs/en/scheduled-tasks.md, "Manage scheduled tasks"):
  - 5-field cron expressions
  - Up to 50 tasks per session
  - Persist on resume (except expired or past one-shot tasks)

- **`Stop` hook event** (source: https://code.claude.com/docs/en/hooks.md reference):
  - Fires when Claude finishes a turn
  - Can be used to keep a session working (e.g., re-schedule a loop)

**NOT DOCUMENTED:**

- Whether a routine can invoke a workflow directly, or whether the prompt must ask Claude to run it.
- **`/schedule` subcommand options** beyond the web UI (e.g., is there a `--days` flag? Can you pass cron directly via CLI?)
- Whether `CronCreate` can trigger a skill or only run a prompt.
- Whether a scheduled task can access MCP servers configured in the session.
- Exact structure of the `ScheduleWakeup` tool input/output (not listed in CLI reference).

---

## 5. Hooks: Full Event List, JSON Schema, Blocking Behavior

**DOCUMENTED:**

- **Hook events** (source: https://code.claude.com/docs/en/hooks.md reference summary):
  - `SessionStart` — session begins
  - `SessionEnd` — session ends
  - `UserPromptSubmit` — before prompt processing
  - `PreToolUse` — before tool call; can block with exit code 2
  - `PostToolUse` — after tool succeeds
  - `PostToolUseFailure` — after tool fails
  - `Stop` — Claude finishes turn
  - `StopFailure` — turn failed to complete
  - `Notification` — Claude needs input or permission
  - `FileChanged` — watched file changes
  - `CwdChanged` — working directory changes
  - `ConfigChange` — configuration changes
  - `PermissionRequest` — permission decision needed
  - `Elicitation` — MCP server asks for user input
  - `WorktreeCreate` — create worktree (custom hook to replace git)
  - `WorktreeRemove` — remove worktree (custom hook)
  - `Setup` — early session setup
  - **SubagentStart, SubagentStop** — referenced but no schema shown (source: inferred from hooks guide)

- **JSON input fields** (source: https://code.claude.com/docs/en/hooks.md):
  ```json
  {
    "session_id": "abc123",
    "prompt_id": "UUID",
    "transcript_path": "/path/to/transcript.jsonl",
    "cwd": "/current/working/dir",
    "permission_mode": "default|plan|auto|...",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": { "command": "npm test" },
    "tool_use_id": "toolu_..."
  }
  ```

- **JSON output / decision fields** (source: https://code.claude.com/docs/en/hooks.md):
  ```json
  {
    "hookSpecificOutput": {
      "permissionDecision": "allow|deny|elicit",
      "permissionDecisionReason": "Why blocked",
      "additionalContext": "Info for Claude",
      "updatedInput": { "modified": "input" }
    },
    "systemMessage": "Visible to Claude",
    "terminalSequence": "\u001b]0;Window Title\u0007"
  }
  ```

- **Blocking behavior:**
  - Exit code 2 blocks the action (only `PreToolUse`, `PermissionRequest`, and a few other events). (source: https://code.claude.com/docs/en/hooks.md, "Exit Codes")
  - JSON `permissionDecision: "deny"` can also block (no exit code 2 needed).
  - `additionalContext` injects text into Claude's context for the turn.

- **Hook types** (source: https://code.claude.com/docs/en/hooks-guide.md and https://code.claude.com/docs/en/hooks.md):
  - `command` — shell script
  - `http` — HTTP POST
  - `mcp_tool` — MCP server tool call
  - `prompt` — single-turn LLM evaluation
  - `agent` — spawns subagent

**NOT DOCUMENTED:**

- **Rate-limit / 429 hook event** — no documented hook for when a session hits rate limits. The docs mention `quota_auto_resume_fired`, `quota_auto_resume_stale`, `quota_auto_resume_disabled` (Notification matchers, not full events), but these are for usage limits, not rate limits.
- **SubagentStart / SubagentStop JSON schema** — the event names are mentioned in hook guides but their input/output structure is not defined.
- **Hook execution order** when multiple hooks match the same event.
- **Async hook return path** — can a hook's output be consumed by the next hook?

---

## 6. Sessions: Transcript Location, Resume, Context Window, Compaction

**DOCUMENTED:**

- **Transcript location** (source: https://code.claude.com/docs/en/sessions.md, "Where transcripts are stored"):
  - `~/.claude/projects/<project>/<session-id>.jsonl`
  - `<project>` is working directory path with non-alphanumeric chars replaced by `-`
  - For paths >200 chars, name is truncated + hash appended
  - JSONL format (one JSON object per line)
  - Configurable via `CLAUDE_CONFIG_DIR` env var

- **`--resume` semantics** (source: https://code.claude.com/docs/en/sessions.md, "Resume a session"):
  - `claude --resume` opens session picker
  - `claude --resume <session-id>` resumes by ID
  - `claude --resume <name>` resumes by name
  - `claude --resume <transcript-path>` resumes from `.jsonl` file
  - `claude --continue` reopens most recent session
  - **Can resume from another machine** if you have the `.jsonl` file path (source: implies yes, but not explicitly stated)

- **Context window size:** NOT explicitly documented. The docs reference "context window" and "compaction" but do not state the token limit for each model. (source: searching https://code.claude.com/docs/en/context-window.md — fetch this if available)

- **Compaction** (source: https://code.claude.com/docs/en/sessions.md, "Manage context within a session"):
  - `/compact [instructions]` — replace history with summary
  - `/context` — show current context use
  - `/clear` — start fresh with empty context
  - Compaction is automatic when context fills up (no `--no-auto-compact` flag documented for CLI)

- **Session restoration on resume** (source: https://code.claude.com/docs/en/sessions.md, "What a resumed session restores"):
  - Conversation history (full, including tool calls)
  - Model the session was using
  - Agent definition if started with `--agent`
  - Permission mode (with exceptions on resume)
  - Active goal if one was running
  - Scheduled tasks (except expired)

**NOT DOCUMENTED:**

- Exact context window size for each Claude model (e.g., is Opus 5 200K tokens?).
- Whether a session transcript can be resumed from a different user's machine without copying the file (no documented remote session store for `--resume`).
- **`--no-auto-compact` flag** — not documented; compaction happens automatically at a threshold.
- Exact algorithm for when compaction triggers (e.g., at 85% of window, at 95%?).

---

## 7. Git Worktree Support: Flags, Tools, Layout, Cleanup

**DOCUMENTED:**

- **`-w / --worktree` flag** (source: https://code.claude.com/docs/en/worktrees.md, "Start Claude in a worktree"):
  - `claude --worktree <name>` — create/reuse worktree under `.claude/worktrees/<name>/`
  - Creates branch `worktree-<name>` by default
  - `--worktree "#<PR-number>"` — branch from PR head (https://code.claude.com/docs/en/worktrees.md, "Branch from a pull request")

- **Tools** (source: https://code.claude.com/docs/en/worktrees.md, "Manage worktrees"):
  - `EnterWorktree` — switch to another worktree under `.claude/worktrees/`
  - `ExitWorktree` — exit current worktree, return to main checkout

- **Layout:**
  - `.claude/worktrees/<name>/` — worktree directory (git worktree)
  - `worktree-<name>` — branch (auto-created)
  - `.worktreeinclude` — file to copy gitignored files into new worktrees (source: https://code.claude.com/docs/en/worktrees.md, "Copy gitignored files into worktrees")

- **Isolation:**
  - Worktree sessions cannot edit files in main checkout (source: https://code.claude.com/docs/en/worktrees.md, "How Claude Code enforces isolation")
  - Four checks: file edits, command working directory, git redirects, command shape
  - Refusals are named `Refusing to enter worktree...` or `command blocked by worktree isolation checks`

- **Auto-cleanup rules** (source: https://code.claude.com/docs/en/worktrees.md, "Clean up worktrees"):
  - Interactive sessions: clean/unnamed → removed; clean/named → prompt to keep; dirty → prompt to keep or remove
  - Non-interactive (`-p`): no cleanup; `git worktree remove` required manually
  - Subagent/background-session worktrees: periodic sweep removes after `cleanupPeriodDays` (default 30 days) if no uncommitted work
  - Sweep honors `git worktree lock` (held while agent runs)

- **Subagent `isolation: worktree`** (source: https://code.claude.com/docs/en/sub-agents.md and https://code.claude.com/docs/en/worktrees.md):
  - Each subagent gets temporary worktree
  - Removed if it has no changes
  - Persistent if it has changes (swept later)

- **`worktree.baseRef` setting** (source: https://code.claude.com/docs/en/worktrees.md, "Choose the base branch"):
  - `"fresh"` (default) — branch from remote default branch
  - `"head"` — branch from current local HEAD

**NOT DOCUMENTED:**

- **`EnterWorktree` input parameters** — the docs say it exists and can switch between worktrees, but the exact tool input schema (does it take a path, a name?) is not specified.
- **ExitWorktree input parameters** — same.
- Whether worktree cleanup can be disabled per-session.
- Whether a worktree can be resumed from a different machine if the repository is cloned elsewhere.

---

## NOT DOCUMENTED (Summary List)

1. **Usage limits:** Exact mechanism of 5-hour rolling session and weekly limit; when they reset; API for querying remaining budget.
2. **Workflow tool:** `+500k token-budget` directive syntax; nested agent spawning.
3. **Subagents:** Exact SubagentStart/SubagentStop hook JSON schema; whether memory is auto-loaded.
4. **Headless / scheduled:** `--max-budget-usd` for `-p` (workflow-scoped only); trigger a workflow from cron; schedule skill execution via CronCreate.
5. **Hooks:** Rate-limit / 429 event; SubagentStart/SubagentStop full schema; hook execution order; async return path.
6. **Sessions:** Context window sizes per model; cross-machine resume without file copy; `--no-auto-compact` flag; compaction threshold.
7. **Worktrees:** EnterWorktree / ExitWorktree exact tool input schema; cross-machine resume.

---

**Sources (Complete List):**
- https://code.claude.com/docs/en/monitoring-usage.md
- https://code.claude.com/docs/en/workflows.md
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/agents.md
- https://code.claude.com/docs/en/headless.md
- https://code.claude.com/docs/en/routines.md
- https://code.claude.com/docs/en/scheduled-tasks.md
- https://code.claude.com/docs/en/hooks-guide.md
- https://code.claude.com/docs/en/hooks.md (reference)
- https://code.claude.com/docs/en/sessions.md
- https://code.claude.com/docs/en/worktrees.md


---

## Report I5 — documented behaviour probe 2 (goals, agent view, scheduled tasks, /batch, routines, usage-limit errors)

*Verbatim final message of agent `a98d451fd7b80c135`, delivered 2026-09-23T01:47:02.567Z; transcript `subagents/agent-a98d451fd7b80c135.jsonl`.*

## Answers (6/6 topics)

**1. Goals** ([https://code.claude.com/docs/en/goal.md](https://code.claude.com/docs/en/goal.md))

A goal is a completion condition (`/goal <condition>`) that keeps Claude looping toward a measurable end state. It survives `--resume`. In `/goal` mode you can set it in `claude -p`, and the goal keeps the session working autonomously for many turns—stopping only when the condition is met, judged impossible, or an unrecoverable error clears it. "Background work defers evaluation": when subagents or background shell commands are running at turn end, Claude Code skips evaluation and re-evaluates at the next idle turn. "Idle check-ins" (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`, default 30 min, max three per goal per user prompt) are automatic mid-session turns Claude Code fires to check on background work after 30 min idle.

**Quote on re-prompt condition**: "Each time Claude finishes a turn, Claude Code sends the condition and the conversation so far to your configured small fast model…The model returns one of three verdicts."

**2. Agent view / background sessions** ([https://code.claude.com/docs/en/agent-view.md](https://code.claude.com/docs/en/agent-view.md))

Started via `/bg` inside a session, `claude --bg` from shell, or `claude agents` UI. **Yes, they keep running after terminal exits**—a supervisor process at `~/.claude/jobs/<id>/` runs them independently. File edits isolate via **git worktree under `.claude/worktrees/`** (skipped if already in a worktree or non-git repo). Results delivered via PR labels in agent view, one-line summaries, peek panel, full transcript attachment, and `claude logs <id>` / `claude agents --json`. Usage limits: each session has independent quota; the docs don't specify hard blocking at usage limit, only that "each session uses your subscription quota independently." **No documented resumption or attachment mechanism beyond opening a session URL**—press Enter on a row to attach. **Limits**: research preview; counts above 99 show as `99+`; row summaries update max every 15 seconds.

**3. Scheduled tasks** ([https://code.claude.com/docs/en/scheduled-tasks.md](https://code.claude.com/docs/en/scheduled-tasks.md))

`/loop <interval> <prompt>` runs fixed schedule; `/loop <prompt>` lets Claude choose dynamically (1 min–1 hour); `/loop` bare runs built-in maintenance prompt. `ScheduleWakeup` tool with `stop: true` halts a `/loop`. `CronCreate` fields: 5-field cron expression, prompt, recurring vs one-shot, **no `durable` field documented** (it's research preview; 7-day expiry built in). Tasks **do restore on `--resume`** except expired recurring tasks and past one-shots. **Tasks do NOT fire at usage limit**—only while the session is running and idle. "Autonomous loop" (`/loop` no prompt): built-in maintenance prompt re-runs on dynamically chosen intervals; can self-stop via `ScheduleWakeup` with `stop: true`.

**4. `/batch` skill** ([https://code.claude.com/docs/en/commands.md](https://code.claude.com/docs/en/commands.md) / [https://code.claude.com/docs/en/skills.md](https://code.claude.com/docs/en/skills.md))

**NOT DOCUMENTED**—the skills and commands pages do not describe `/batch` inputs, work-splitting strategy, or outputs. The page mentions it as a bundled skill alongside `/run`, `/verify`, `/debug`, `/loop`; **availability in `-p` is NOT stated**.

**5. Routines** ([https://code.claude.com/docs/en/routines.md](https://code.claude.com/docs/en/routines.md))

Routines are **cloud-hosted Claude Code sessions**. They **cannot reach local machine repositories or filesystems**—each routine is "cloned at the start of a run, starting from the default branch." They **can be triggered by API call** (via `/fire` endpoint with bearer token; `text` field passed as untrusted payload). **No documented cross-session messaging**—only that the cloud session's results appear in the session URL and the web UI lists runs.

**6. Usage limits** ([https://code.claude.com/docs/en/costs.md](https://code.claude.com/docs/en/costs.md))

**Session (5-hour) and weekly windows**: "a seat-based usage window on a subscription plan, shared across all models" — hitting either resets on schedule; the developer "can't restore access by switching models with `/model`." **"Shared across all models"**: the same quota budget covers all Claude models in that window; no per-model escape.

**Utilization percentages**: Only `/usage` command (Session block shows token counts and estimated cost) and status line `rate_limits` fields expose percentages. **No other endpoint disclosed**.

**`/rate-limit-options`**: NOT DOCUMENTED as a command. The docs reference waiting to continue automatically when a usage limit resets (`/rate-limit-options` mentioned once as where "the developer picks it"), but no `/rate-limit-options` tool/command spec is provided.

Sources:
- [https://code.claude.com/docs/en/goal.md](https://code.claude.com/docs/en/goal.md)
- [https://code.claude.com/docs/en/agent-view.md](https://code.claude.com/docs/en/agent-view.md)
- [https://code.claude.com/docs/en/scheduled-tasks.md](https://code.claude.com/docs/en/scheduled-tasks.md)
- [https://code.claude.com/docs/en/costs.md](https://code.claude.com/docs/en/costs.md)
- [https://code.claude.com/docs/en/routines.md](https://code.claude.com/docs/en/routines.md)
