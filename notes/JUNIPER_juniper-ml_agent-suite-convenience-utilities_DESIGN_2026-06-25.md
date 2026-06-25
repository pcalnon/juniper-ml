# Custom-Agent Suite — Convenience Utilities (Design / Analysis)

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (design authored by the `planner` subagent, dogfooding)
**Document Type**: DESIGN
**Status**: Draft — ratify-ready
**Last Updated**: 2026-06-25

---

## 1. Background and genesis

The Juniper custom-agent suite is merged on `main`: four subagents
(`.claude/agents/{planner,auditor,task-executor,prompt-validator}.md`), one user-invoked Skill
(`.claude/skills/template-agent/SKILL.md`), a template library
(`prompts/templates/` — `manifest.yaml`, `RUBRIC.md`, seven `*.md` templates, a five-file
`data/` layer), a path-invoked discovery helper (`util/prompt_discovery/`), a data resolver
(`util/template_data_resolver.py`), and a cross-repo mirror installer (`util/install_agents.bash`).
Each component is gated by a `tests/test_*.py` unittest wired into `.github/workflows/ci.yml`
(lines 138–214), because `.claude/**` and `prompts/**` are excluded from every pre-commit hook
except markdownlint (`tests/test_agents_frontmatter.py:10-13`).

This document was produced **by the suite's own `planner` agent** as a dogfooding exercise: every
proposal below validates the design by *consuming* it. The full design-of-record is
`notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`.

## 2. Purpose and scope

**Goal.** Propose a prioritized, immediately-implementable set of **3–5 convenience utilities** that
make the suite easier to **use** (lower friction for the owner and downstream agents) and easier to
**maintain** (catch drift, surface health), and that — as a side effect of being built — exercise and
validate the existing components.

**Hard constraints (apply to every proposal).**

1. **Consume an existing component.** Each utility reads/drives at least one shipped suite component,
   so building it exercises that component's real contract.
2. **House idioms.** Path-invoked `util/` script — Python **stdlib-only** or bash — never a new package
   (`util/` is not importable; the house pattern is `sys.path.insert` or invoke-by-path, see
   `util/prompt_discovery/cli.py:4-7` and `tests/test_prompt_discovery.py:30-39`). Behavioural coverage
   via a `tests/test_*.py` unittest **wired into `ci.yml`** (since `util/` is not pre-commit-lint-gated).
   PyYAML is the only allowed third-party dependency (already used by every suite test).
3. **No new heavy dependencies.** PyYAML only.
4. **Conventions.** Repo-root discovery by walking up for `.github/workflows/`
   (`tests/test_template_selection.py:29-33`); synthetic-fixture + `subprocess` test style
   (`tests/test_install_agents.py:32-53`); the data layer is the source of truth for conventions
   (`prompts/templates/data/conventions.yaml`, resolved via `util/template_data_resolver.py:46`).

**Non-goals.** No change to any agent/Skill/template/RUBRIC/probe behaviour; no new agent or template
(the *scaffold-a-template* idea is proposed but de-prioritized); no MCP/Serena dependency (the
discovery layer is deliberately MCP-free at the `util/` tier, `util/prompt_discovery/symbol_probe.py:4-9`);
no CI-topology change beyond adding `python3 -m unittest …` lines next to the existing block.

## 3. The component surface these utilities can consume (grounded inventory)

| Component | Anchor | Contract a utility can consume |
|-----------|--------|--------------------------------|
| Template manifest | `prompts/templates/manifest.yaml:36-103` | 7 templates; each has `id/title/when_to_use/match_signals/file/required_fields/class`; `generic` is the sole `always:true` fallback (`:95-102`). |
| Match-signal selection | `manifest.yaml:40-44,98-100`; `tests/test_template_selection.py:50-78` | keyword sets per template, exactly one always-match, no duplicate keyword sets. |
| RUBRIC | `prompts/templates/RUBRIC.md` | stable IDs R1.1…R5; PASS bar (`:24-27`); R2.0 hard gate (`:72-78`); R3.4 a–e claim taxonomy (`:114-121`). |
| Template data layer | `util/template_data_resolver.py:22` (`DATA_FILES`), `:46` (`resolve`) | five `data/*.yaml`, dotted lookup, canonical convention values (`conventions.yaml`). |
| Discovery bundle | `util/prompt_discovery/cli.py:38-98` | JSON bundle + provenance envelope; hard-stop exit 2 on non-git root (`:89-96`). |
| Agents frontmatter | `.claude/agents/*.md`; `tests/test_agents_frontmatter.py:77-107` | `name`==filename, `tools` declared, `model: opus`, `effort: max`. |
| Skill spec | `.claude/skills/template-agent/SKILL.md:1-9` | frontmatter `name/description/allowed-tools/model/effort/disable-model-invocation`. |
| Mirror installer | `util/install_agents.bash:57-89` | idempotent symlink mirror of `.claude/{agents,skills}` into `~/.claude`. |

## 4. Proposed utilities (prioritized)

### P1 — `util/agent_suite_doctor.py` (suite health-check / "doctor") — **#1 recommendation**

**Purpose.** One command that answers "is the suite coherent and installed?" It aggregates the
*existence + structural validity* of every component and the *mirror status*, emitting a human report or
`--json`, exit 0 = healthy / exit 1 = problems. It is the natural "front door" a user (or another agent)
runs before relying on the suite.

**Components it validates (and how).**
- **Agents** — counts `.claude/agents/*.md`, parses frontmatter, asserts `model: opus` / `effort: max`
  hold (re-using the contract in `tests/test_agents_frontmatter.py:93-107`). Exercises the agent
  frontmatter contract from a *runtime* angle (the test gates commits; the doctor gates a session).
- **Skill** — confirms `.claude/skills/template-agent/SKILL.md` exists and declares `allowed-tools`
  including `Agent` (the delegation tool the Skill's state machine needs, `SKILL.md:5,46-49`).
- **Templates** — every `manifest.yaml` template `file` exists; the sole `always:true` is `generic`
  (`manifest.yaml:98-100`); consumes the manifest exactly as the selection test does.
- **RUBRIC** — present and contains the stable check IDs (`R2.0`, `R3.4`) the validator references
  (`RUBRIC.md:72,114`).
- **Data layer** — calls `template_data_resolver.load()` and asserts all five `DATA_FILES` resolve
  (`util/template_data_resolver.py:22,35-43`) — directly drives the resolver.
- **Discovery** — shells `util/prompt_discovery/cli.py --repo-root <root>` and asserts a well-formed
  bundle with `schema_version`/`provenance.head_sha` (consumes the CLI's real output contract,
  `cli.py:58-75`).
- **Mirror** — runs `util/install_agents.bash --dry-run` and reports whether `~/.claude` links are
  present/stale (consumes the installer's idempotent dry-run path, `install_agents.bash:57-75`).

**Interface.**
```text
python util/agent_suite_doctor.py [--repo-root PATH] [--json] [--strict] [--no-discovery]
  --repo-root    target repo (default: walk up for .github/workflows/)
  --json         machine-readable report instead of the text table
  --strict       treat WARN as failure (exit 1); default counts only FAIL
  --no-discovery skip the discovery-CLI subprocess (offline / fast mode)
exit 0 = all checks OK (WARN allowed unless --strict); exit 1 = ≥1 FAIL; exit 2 = bad arguments
```
Output: one line per check — `OK` / `WARN` / `FAIL` + a one-line reason — followed by a summary count,
mirroring the `auditor` agent's "verified pass / verified fail / could not verify" discipline
(`.claude/agents/auditor.md:46-48`).

**Test approach.** `tests/test_agent_suite_doctor.py`, stdlib-only. Walk-up repo-root discovery; (a)
run against the real repo and assert exit 0 + every check present; (b) point `--repo-root` at a synthetic
tree (`tempfile`) missing one component and assert the matching check is `FAIL` and exit 1 (the
synthetic-fixture idiom from `tests/test_install_agents.py:32-53` and the hard-stop test in
`tests/test_prompt_discovery.py:159-164`); (c) `--json` parses and carries a `checks` list + `summary`;
(d) `--no-discovery` skips the subprocess. Wire into `ci.yml` next to the suite block (after line 214).

**Effort: S.** **Risk/note:** the only subprocess is the discovery CLI (already proven by
`tests/test_prompt_discovery.py`); guard it behind `--no-discovery` so the doctor stays fast and offline
when needed, and never let the doctor *write* anything (read-only, like the `planner`/`auditor` agents).

---

### P2 — `util/template_select_preview.py` (offline match-signal selector preview)

**Purpose.** Given a task string, print which template the Skill's step-4 selection would pick
(`SKILL.md:38-43`), with the matched keywords and the runner-up — an offline preview of the selection the
Skill performs interactively. Lets the owner sanity-check "will this task land on `regressions` or
`failing-tests`?" without launching the Skill.

**Components it validates (and how).** Consumes `manifest.yaml` `match_signals` (`:40-44`) and the
selection invariants enforced by `tests/test_template_selection.py:50-78` — by *implementing* the
keyword-substring scoring + `generic` always-match fallback, it executes the selection design end-to-end
(the design the Skill *describes* but no `util/` code yet *runs*). It is the highest-value validator of
the selection layer because that layer currently has only a static coherence lint, not an executable
matcher.

**Interface.**
```text
python util/template_select_preview.py "TASK TEXT…" [--repo-root PATH] [--json] [--top N]
  → prints: selected id, class, matched keyword(s); then the next N-1 ranked candidates
  exit 0 always (generic is the guaranteed fallback, manifest.yaml:98-100)
```
Scoring (kept deliberately simple and documented): case-insensitive substring count of each template's
`match_signals.keywords` in the task text; ties broken by manifest order; `generic` selected iff no
keyword matches (mirrors the Skill's "no match → generic + promotion candidate", `SKILL.md:42-43`).

**Test approach.** `tests/test_template_select_preview.py`: feed strings containing a template's own
keyword (e.g. "the test suite is failing" → `failing-tests`, keyword from `manifest.yaml:51`) and assert
the pick; feed a no-keyword string → `generic`; assert it never crashes on the real manifest (drives the
same file the Skill uses). Use the real manifest, not a fixture, so the test also guards selection
drift. **Effort: S.** **Risk/note:** the scoring must be documented as a *preview heuristic*, not a
claim to reproduce the Skill's LLM judgement byte-for-byte — the Skill may additionally ask the owner on
a thin margin (`SKILL.md:42`); state this in `--help` so the preview is not mistaken for ground truth.

---

### P3 — `util/agent_suite_summary.py` (suite quick-reference / "list")

**Purpose.** A `--list`-style quick reference: one table of the agents (name, one-line `description`,
tools, model/effort) and one of the templates (id, `when_to_use`, class, `required_fields`), so the owner
can recall "which agent / which template" without opening eight files. The human counterpart to the
machine `doctor`.

**Components it validates (and how).** Parses every `.claude/agents/*.md` frontmatter (consuming the
same `_split_frontmatter` shape as `tests/test_agents_frontmatter.py:34-41`) and the full `manifest.yaml`
template list (`:36-103`). Building it proves the frontmatter + manifest are *machine-summarizable* (a
weaker but useful check than the gates) and gives a single rendering both humans and the `doctor` can
share.

**Interface.**
```text
python util/agent_suite_summary.py [--repo-root PATH] [--agents|--templates] [--json|--markdown]
  default: render both sections as an aligned text table; --markdown for pasteable docs
```

**Test approach.** `tests/test_agent_suite_summary.py`: assert all four agents and all seven templates
appear; `--json` round-trips; `--markdown` is valid (line-length ≤ 512, `conventions.yaml:6`). Real files,
walk-up root. **Effort: S.** **Risk/note:** overlaps P1 in parsing logic — factor the shared
frontmatter/manifest readers into a tiny stdlib module both import (or have `summary` expose the parse
that `doctor` reuses) to avoid drift between two parsers.

---

### P4 — `util/generated_prompt_index.py` (`prompts/generated/` index + stale-cleanup helper)

**Purpose.** The Skill emits validated prompts to `prompts/generated/` with a dated, collision-safe name
`PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md` (`SKILL.md:54-56`;
`conventions.yaml` `generated_prompt_name`). Today that directory has only a `.gitkeep`. This utility
lists generated prompts (parsed by the naming convention), and with `--older-than DAYS --prune` archives
or deletes stale ones — keeping the working surface tidy as the Skill is used.

**Components it validates (and how).** Consumes the generated-prompt **naming contract** the Skill
produces and the `conventions.yaml` `generated_prompt_name` / `deliverable_locations.generated_prompts`
values (resolved via `util/template_data_resolver.py:46`). Building it validates that the emit-name
contract is *parseable* and that the data-layer location value is authoritative (not hard-coded).

**Interface.**
```text
python util/generated_prompt_index.py [--repo-root PATH] [--json]
                                       [--older-than DAYS [--prune | --archive DIR]] [--dry-run]
  default: list each generated prompt with parsed {project,app,subject,task-type,date,time}
  --prune deletes; --archive moves; --dry-run previews (default-on when --prune given without it)
```

**Test approach.** `tests/test_generated_prompt_index.py`: synthetic `prompts/generated/` with
well-named + malformed files; assert parsing, that `.gitkeep` is ignored, that `--older-than … --prune
--dry-run` reports but deletes nothing, and that the destination is read from `conventions.yaml`. The
**file-safety / dry-run-default** discipline mirrors `scripts/test_resume_file_safety.bash`.
**Effort: M.** **Risk/note:** destructive `--prune` must default to dry-run and require an explicit
`--prune` *and* a non-dry flag to actually delete (never reap an unmerged or hand-authored file); restrict
the glob to the convention's name shape so a stray hand-placed file is never deleted.

---

### P5 — `util/scaffold_template.py` (new-template / new-agent generator) — *de-prioritized*

**Purpose.** Generate a new `prompts/templates/<id>.md` pre-populated with the canonical skeleton in
order and well-formed placeholders, plus the matching `manifest.yaml` stub — so adding the round-2
plan/audit/task skeletons (or a promoted `generic` output) cannot drift from the skeleton/placeholder
contract.

**Components it validates (and how).** Consumes the skeleton + placeholder convention enforced by
`tests/test_template_library_drift.py` (skeleton order check `:146-158`; placeholder regex `:33`) and the
manifest schema (`:140` `required_keys`). Generating a template that *passes* the drift test on first run
is a strong validation of that contract.

**Interface.**
```text
python util/scaffold_template.py --id NEW_ID --title "…" --class execution \
       --keywords "k1,k2" --required-fields "a,b" [--repo-root PATH] [--dry-run]
  → writes prompts/templates/NEW_ID.md (skeleton+placeholders) and prints the manifest stanza to add
```

**Test approach.** `tests/test_scaffold_template.py`: scaffold into a temp tree, then run the
library-drift assertions against the generated file (import the drift test's helpers) and assert it
passes; assert refuse-on-collision. **Effort: M–L.** **Risk/note:** must **refuse to auto-edit
`manifest.yaml`** (the manifest is the human-curated selection contract and `prompts/**` is unlinted —
an auto-edit could silently break selection); print the stanza for the owner to paste instead. This is
why it is P5: higher blast-radius, lower day-to-day frequency than P1–P4.

## 5. Prioritization rationale

| Rank | Utility | Component validated | Effort | Self-validation strength |
|------|---------|---------------------|--------|--------------------------|
| **P1** | `agent_suite_doctor.py` | all components (existence+structure) + mirror | **S** | Highest — touches every layer; read-only |
| P2 | `template_select_preview.py` | `manifest.yaml` match-signal selection | S | High — first *executable* matcher for the selection design |
| P3 | `agent_suite_summary.py` | agents frontmatter + manifest | S | Medium — proves machine-summarizable |
| P4 | `generated_prompt_index.py` | Skill emit-name contract + data layer | M | Medium — validates the emit/location contract |
| P5 | `scaffold_template.py` | skeleton/placeholder + manifest schema | M–L | High but higher-risk; lower frequency |

**Recommendation: implement P1 (`agent_suite_doctor.py`) first.** It is the smallest meaningful unit
(read-only, stdlib-only, one new test file), the highest-value (a single "is my suite OK?" command), and
the *most self-validating* (it consumes every other component's contract at runtime, complementing the
commit-time gates). P3's frontmatter/manifest parsers can be lifted out of P1, so P1 also seeds P3.

## 6. #1 recommendation — concrete interface and test cases

### 6.1 CLI

```text
python util/agent_suite_doctor.py [--repo-root PATH] [--json] [--strict] [--no-discovery]
```
- `--repo-root PATH` — default: walk up from the script for `.github/workflows/`
  (`tests/test_template_selection.py:29-33`).
- `--json` — emit `{"checks": [{"name","status","detail"}…], "summary": {"ok","warn","fail"}}`.
- `--strict` — exit 1 if any `WARN`; default: exit 1 only on `FAIL`.
- `--no-discovery` — skip the `cli.py` subprocess (offline/fast).
- Exit: `0` healthy · `1` ≥1 FAIL (or WARN under `--strict`) · `2` argument error.

### 6.2 Checks (each → OK / WARN / FAIL + reason)

1. `agents.present` — ≥4 `.claude/agents/*.md` parse; FAIL if any unparseable or `<4`.
2. `agents.defaults` — every agent `model: opus` ∧ `effort: max` (`test_agents_frontmatter.py:93-107`);
   FAIL on drift.
3. `skill.present` — `template-agent/SKILL.md` exists ∧ `allowed-tools` includes `Agent`
   (`SKILL.md:5`); FAIL otherwise.
4. `templates.files` — every `manifest.yaml` template `file` exists; FAIL on a missing file.
5. `templates.fallback` — exactly one `always:true`, and it is `generic` (`manifest.yaml:98-100`);
   FAIL otherwise.
6. `rubric.ids` — `RUBRIC.md` contains `R2.0` and `R3.4` (`:72,114`); WARN if absent.
7. `data.layer` — `template_data_resolver.load()` returns all five `DATA_FILES` (`:22`); FAIL on a
   missing file.
8. `discovery.bundle` — `cli.py --repo-root <root>` exits 0 with `schema_version==1` ∧
   `provenance.head_sha` present (`cli.py:58-75`); FAIL on non-zero / malformed; **skipped** under
   `--no-discovery` (reported as `SKIP`).
9. `mirror.status` — `install_agents.bash --dry-run` succeeds; WARN (never FAIL) if links are absent
   (the mirror is optional, `install_agents.bash:8`).

### 6.3 Test cases (`tests/test_agent_suite_doctor.py`, stdlib-only)

- `test_real_repo_is_healthy` — run on the real repo: exit 0; every check name present; no `FAIL`.
- `test_missing_agent_fails` — synthetic `--repo-root` with an empty `.claude/agents/`: `agents.present`
  = FAIL, exit 1.
- `test_model_drift_fails` — synthetic agent with `model: sonnet`: `agents.defaults` = FAIL.
- `test_missing_template_file_fails` — manifest references a non-existent `file`: `templates.files` = FAIL.
- `test_bad_fallback_fails` — two `always:true` templates: `templates.fallback` = FAIL.
- `test_json_shape` — `--json` parses; has `checks` (list) + `summary` with `ok/warn/fail` ints.
- `test_no_discovery_skips_subprocess` — `--no-discovery`: `discovery.bundle` = SKIP; no `cli.py` call.
- `test_strict_promotes_warn` — a WARN-only run: exit 0 normally, exit 1 under `--strict`.
- `test_argument_error_exit_2` — unknown flag → exit 2.

(Synthetic-fixture + `subprocess` style from `tests/test_install_agents.py:32-53`; hard-stop assertion
style from `tests/test_prompt_discovery.py:159-164`.) Wire `python3 -m unittest -v
tests/test_agent_suite_doctor.py` into `.github/workflows/ci.yml` immediately after the existing suite
block (after line 214).

## 7. Open questions, risks, testing strategy

**Open questions (owner decisions).**
- **OQ-1.** Should the `doctor`'s mirror check be WARN (proposed) or FAIL? The mirror is optional per
  `install_agents.bash:8`; recommend WARN.
- **OQ-2.** Should P3 (`summary`) be folded into P1 as `--summary` rather than a separate script? Saves a
  file but mixes "health" and "reference" concerns; recommend separate, sharing one parser module.
- **OQ-3.** For P4, archive-vs-delete default for stale generated prompts (recommend archive + explicit
  `--prune` for delete).

**Risks.** (a) **Parser drift** between P1 and P3 — mitigate with one shared stdlib reader. (b) **Coupling
to internal contracts** — these utilities read the *same* anchors the gates assert, so a contract change
breaks utility + test together (acceptable: that is the dogfooding signal). (c) **Destructive P4 `--prune`**
— dry-run default + name-shape glob restriction. (d) **Discovery subprocess latency** in P1 — `--no-discovery`
escape hatch.

**Testing strategy.** Every utility ships with a `tests/test_*.py` unittest wired into `ci.yml` (the only
gate, since `util/` and `prompts/**` are unlinted by pre-commit). Tests run against the **real** suite
files where they double as drift gates (P2, P3) and against **synthetic** trees for failure paths (P1, P4,
P5), following the established `tempfile` + `subprocess` idiom. No utility writes to the repo except P4
(guarded) and P5 (refuse-on-collision); P1/P2/P3 are read-only, matching the `planner`/`auditor` posture.

## 8. Verification of this document (anti-hallucination)

Every `file:line` cited above was read in-repo during grounding (agents, Skill, manifest, RUBRIC, data
resolver, discovery CLI + symbol probe, installer, and the five `test_*.py` gates), and the discovery
bundle at HEAD `21d77008` was consulted. The target path
`notes/JUNIPER_juniper-ml_agent-suite-convenience-utilities_DESIGN_2026-06-25.md` was confirmed absent
before writing. No API, path, flag, or version above is asserted that was not observed in the repository.
For ratification, recommend a cross-validation read of §6 against the live `manifest.yaml` and
`util/prompt_discovery/cli.py` before P1 implementation begins.
