# Thread Handoff — Implement E-1 Stage 1 (HTTP-only service-smoke diagnostician Skill)

**Project**: juniper-ml — Custom-Agent Suite (Enhancement effort, Phase 3 / E-1)
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**Document Type**: THREAD HANDOFF PROMPT (paste this as the new thread's opening instruction)
**Date**: 2026-06-29
**Predecessor**: E-1 Stage-0 feasibility spike — verdict **PROCEED** (PR #586)

> Paste this whole file as your first message in a fresh Claude Code thread. It is self-contained.
> Every `file:line` below was re-confirmed first-party while authoring this handoff. **Re-verify each
> before you rely on it** (HEAD moves): the grounding pins are juniper-ml @ `f2ce007` (branch
> `feature/e1-stage1-handoff`) and juniper-canopy @ `79292bdc`. If any cited anchor no longer matches,
> stop and re-ground — do not invent.

---

## Goal

Continue the Juniper custom-agent-suite enhancement effort by implementing **E-1 Stage 1 (PR-9)** — a new
**HTTP-only** service-smoke diagnostician **Skill** at `.claude/skills/service-smoke/SKILL.md` that boots
**canopy** in the `JuniperCanopy1` conda env, hits `/v1/health` plus key endpoints, tails logs, and
reports any live traceback as `file:line` (the "green tests / dead app" catch). **No browser** — that is
Stage 2. The Stage-0 feasibility spike is **approved (PROCEED)**: the boot → HTTP → MCP-drive → clean
teardown mechanism is proven first-party, so this stage builds the committed runtime surface. Deliver it
as **one PR off `main`** carrying four coupled changes (Skill + structural lint test + `ci.yml` line +
AGENTS.md inventory), gated structurally in CI with a documented **manual** smoke-verify the owner runs.
Spec: `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md` §6.9 (lines 491–526; PR-9 at
628–630). Spike record: `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md`.

---

## Completed so far

- **Phases 1–2 of the enhancement roadmap (PR-1..PR-7) are merged.** The custom-agent suite is
  feature-complete and healthy (plan §1, lines 26–30): 4 opus+max subagents, the `/template-agent` Skill,
  a template library under `prompts/agent_templates/`, a data layer, a 7-probe discovery CLI, and ~20
  `tests/` gates. (Verify the suite still exists at start — see Verification.)
- **E-1 Stage 0 (PR-8) is DONE — verdict PROCEED**, merged as **PR #586** (`git log`:
  `f2ce007 docs(agent-suite): E-1 Stage-0 feasibility spike — PROCEED verdict (#586)`). The spike booted a
  minimal FastAPI stand-in under `JuniperCanopy1`'s uvicorn, got `curl /v1/health` → 200, drove the live
  DOM via the Playwright MCP, and tore down clean with no orphan. Full record:
  `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md`. **The kill-criterion did not fire.**
- This handoff document was authored on branch `feature/e1-stage1-handoff`; it is the only artifact of the
  authoring step. Your implementation work starts fresh off `main`.

---

## Remaining work — the Stage-1 build (one PR, four coupled changes)

Do all four in the **same PR** (the lint, the CI line, and the AGENTS.md inventory are not optional
trailers — they are the gate and the convention contract). Each step is independently checkable.

### Step 1 — Author `.claude/skills/service-smoke/SKILL.md` (new)

Model its **shape** on the existing Skill `.claude/skills/template-agent/SKILL.md` (frontmatter +
numbered bounded state machine + explicit terminal states), but its **content** is an HTTP-only runtime
diagnostician, not a prompt builder. Concretely:

- **Frontmatter** (mirror `template-agent/SKILL.md:1–9`):
  - `name: service-smoke` (must equal the filename stem — the lint asserts this).
  - `description:` — substantive (≥ 60 chars): what it boots, what it probes, that it is HTTP-only
    (Stage 2 adds the browser), and that teardown always runs.
  - `argument-hint:` — e.g. `"[--target canopy] [--mode demo|full] [--port 8050]"`.
  - `allowed-tools: Read, Grep, Glob, Bash` — the **Stage-1 HTTP-only** set. **Do NOT** grant `Agent`
    (no subagent delegation) and **do NOT** grant any browser MCP (`playwright` / `chrome-devtools` are
    Stage 2). Add `Write` **only** if you decide to persist a report file (then update the lint to match).
  - `model: opus` and `effort: max` (suite standing defaults — `template-agent/SKILL.md:6–7`).
  - `disable-model-invocation: true` (user-only invocation — `template-agent/SKILL.md:8`).
- **Bounded state machine** (sketch — refine at build; mirror the numbered-steps style of
  `template-agent/SKILL.md:26–68`):
  1. **Ingest** target (default: canopy) + boot `--mode` (demo vs full — see Key Context) + `--port`.
  2. **Pre-flight (hard gate).** Confirm the `JuniperCanopy1` env exists; confirm the target port is
     **free** before boot; record a baseline of listening pythons. (Mirrors the spike pre-flight, record §3.)
  3. **Boot.** Launch uvicorn under `JuniperCanopy1` as a **persistent background process** (so the
     handle survives across tool calls — the capability a Skill has and a subagent lacks; spike §2, §3a).
     Capture the **pid** and the **log file path**.
  4. **Wait-for-ready (bounded, no foreground sleep).** `curl --retry-connrefused --retry N --retry-delay
     1` the health endpoint until it answers or the bounded timeout expires; a timeout is `BOOT_FAILED`.
  5. **Probe.** Hit `/v1/health` (and `/v1/health/live`, `/v1/health/ready`, plus key endpoints). On any
     non-200, capture the response body.
  6. **Tail + resolve.** Read/grep the captured log for tracebacks; resolve each frame to a real
     `file:line`. This is the core "green tests / dead app" report.
  7. **Report.** Structured PASS/FAIL with any live traceback rendered as `file:line`.
  8. **Teardown (MUST run in a `finally`-style path — see the two gotchas below).** Poll-to-down with a
     SIGTERM→SIGKILL escalation and a bounded timeout; orphan-reap; verify the port is free; confirm no
     stray `JuniperCanopy1` python remains. Reuse the `util/reap_pytest_orphans.bash` matching discipline;
     `util/kill_all_pythons.bash` is the documented last-resort only.
- **Terminal states** (mirror `template-agent/SKILL.md:70–75`; name them explicitly so the lint can
  assert them), e.g.: `HEALTHY`, `UNHEALTHY_REPORTED`, `BOOT_FAILED`, `TEARDOWN_ESCALATED`.
- **Encode the two spike teardown gotchas verbatim** (next section). Teardown is non-negotiable and must
  **lead** the design, not trail it (spike §5).

### Step 2 — Author `tests/test_service_smoke_skill_lint.py` (new structural gate)

Copy and adapt `tests/test_template_agent_skill_lint.py` (read it end-to-end — it is 145 lines and is the
exact pattern). Keep its self-locating repo-root helper (`_find_repo_root`, walks up for
`.github/workflows/`, lines 44–48) and its frontmatter split/assert scaffolding. The new lint must assert:

- **Frontmatter shape** (model after `test_template_agent_skill_lint.py:84–109`):
  - `name == "service-smoke"` (equals filename stem).
  - `model` base is `opus` (or `claude-opus*`) — line 101–103 pattern.
  - `effort == "max"` — line 105–106 pattern.
  - `disable-model-invocation is True` (user-only) — line 108–109 pattern.
  - `allowed-tools` ⊇ the Stage-1 set `{Read, Grep, Glob, Bash}` (adapt `_REQUIRED_TOOLS`, line 28).
- **HTTP-only boundary (Stage-1-specific, NOT in the template-agent lint):** assert the frontmatter does
  **not** grant a browser MCP — `playwright` / `chrome-devtools` must be absent (those arrive in Stage 2).
  This keeps the staged boundary honest and is the assertion that makes this lint Stage-1-shaped.
- **Wiring to real artifacts exist on disk** (adapt `_REFERENCED_PATHS` + `test_referenced_paths_exist`,
  lines 32–39 and 111–114): the body references `util/reap_pytest_orphans.bash` and
  `util/kill_all_pythons.bash`, and both exist on disk.
- **Explicit teardown step** (Stage-1-specific): assert the body documents teardown with a
  SIGTERM→SIGKILL escalation / poll-to-down / `finally`-style reap (grep for the markers you used in the
  Skill). The spike's §5 carry-forward makes this mandatory.
- **Terminal states + bounded behavior** documented (adapt lines 132–135): each named terminal state
  appears, and a bounded timeout is described (no unbounded "wait until ready").

Why a structural-only lint: `.claude/**` is git-tracked but excluded from every pre-commit hook except
markdownlint (see the header docstring of `test_template_agent_skill_lint.py:11–13`), so this unittest is
the **gate** for the Skill surface. **The live boot cannot run in ubuntu CI (no conda, no services)** — so
the gate is deliberately structural; correctness of the live behavior is covered by the manual
smoke-verify (below), not CI.

### Step 3 — Wire the new test into `.github/workflows/ci.yml` (same PR)

The CI "Run Python unit tests" step uses a **hardcoded** list of `python3 -m unittest -v tests/...` lines
(`ci.yml:128–297`). Add a line for the new test, with a short comment block matching the house style.
Insert it adjacent to the other `.claude/skills`/`.claude/agents` surface gates — natural home is right
after the `test_template_agent_skill_lint.py` line (`ci.yml:260`, whose comment block is `255–259`) or
after `test_agents_frontmatter.py` (`ci.yml:265`). Exact line to add:

```yaml
          # tests/test_service_smoke_skill_lint.py: structural gate for the E-1 Stage-1
          # service-smoke Skill (.claude/skills/service-smoke/SKILL.md) -- frontmatter (opus +
          # effort max, user-only, HTTP-only tool set, NO browser MCP), wiring to the real
          # teardown utilities, and an explicit teardown step. Live boot cannot run in ubuntu CI
          # (no conda/services); gate is structural-only + a documented manual smoke-verify.
          python3 -m unittest -v tests/test_service_smoke_skill_lint.py
```

### Step 4 — Update juniper-ml `AGENTS.md` (Tests inventory + Repository-Structure tree)

The plan (§6.9 test/gate plan) and the suite convention require the new test to appear in the AGENTS.md
inventory. Three touch-points (use the `template-agent` lint's existing entries as the model):

- The **"Run all tests"** command block near the top — add the `python3 -m unittest -v` line next to
  `tests/test_template_agent_skill_lint.py` (`AGENTS.md:62`).
- The **Repository-Structure tree** — add a `test_service_smoke_skill_lint.py` leaf next to the existing
  `test_template_agent_skill_lint.py` node (`AGENTS.md:240`).
- The **`### Tests` prose inventory** (`AGENTS.md:334`) — add a one-line description modeled on the
  `test_template_agent_skill_lint.py` entry (`AGENTS.md:361`).

Note: `tests/test_agents_md_tree_drift.py` (`ci.yml:291`) enforces only **top-level** directory presence
in the tree (its contract, docstring lines 10–13) — `tests/` and `.claude/skills/` already appear, so it
will **not** auto-catch the new sub-entries. The AGENTS.md edits are therefore a deliberate convention
step, not something CI will force; do them in this PR.

---

## Key context (read before you touch anything)

### Why a Skill, not a subagent (settled — do not relitigate)

A subagent's `Bash` CWD resets per tool call, so it cannot hold a reference to a long-lived
uvicorn/Dash process across steps. A **Skill runs in the main conversation** with persistent state and
in-session MCP. The Stage-0 spike confirmed this structurally (spike record §2 and §5). Build E-1 as a
**Skill**. (Plan §6.9 "SHAPE (verbatim)", lines 493–497.)

### The two teardown gotchas — encode BOTH in the Skill (spike record §3, lines 98–108)

These are **given facts from the completed spike**, not anchors to re-probe:

1. **SIGTERM is graceful, not instant (a TOCTOU trap).** A liveness `curl` fired *immediately* after
   `kill` still returned **200** — uvicorn was finishing in-flight requests before exiting. A teardown
   step that asserts "down" right after the kill **false-fails**. → **Poll for connection-refused with a
   bounded timeout, and escalate SIGTERM → SIGKILL after the timeout.** Run this in a `finally`-style path
   so a mid-smoke failure still reaps the process.
2. **`pgrep -af <name>` matches its own command line.** The orphan check `pgrep -af spike_app` matched the
   very bash process running the check (its argv contained "spike_app"), producing a **false-positive
   orphan**. → **Match the process executable/argv precisely** (e.g. `ps -eo args | grep uvicorn` with
   `grep -v grep`) **or check the listening port**, and **exclude the checker's own PID**. This is the
   same class of care `util/reap_pytest_orphans.bash` already encodes — reuse it.

### Teardown utilities to reuse (both verified present)

- `util/reap_pytest_orphans.bash` — finds and kills orphaned multiprocessing forkserver/worker children
  with **parent-PID safety**: it only kills a candidate whose parent is gone, is PID 1, or is the
  user-session `systemd --user`, and it targets only pythons whose command line references a Juniper
  conda env / worktree path (header docstring, lines 14–20). It exposes `JUNIPER_REAP_PROC_ROOT` /
  `JUNIPER_REAP_KILL_CMD` test hooks (lines 40–41) and `--dry-run`/`--verbose`. **Reuse this matching
  discipline** for the Skill's orphan check.
- `util/kill_all_pythons.bash` — the **blunt last resort**: `ps aux | grep python ... sudo kill -9`
  (line 4) kills *every* python on the host. Document it as an emergency escape hatch only; never the
  primary teardown.

### The CI / verification model (structural gate + manual smoke — why)

The live boot needs conda + the real service, which **ubuntu CI does not have**. So CI runs only the
**structural** lint (Step 2). Correctness of the live behavior is verified by a **documented manual
smoke-verify** that the owner runs locally (write this verify procedure into the Skill or a short note,
and reference it from the PR). This split is mandated by plan §6.9 (lines 513–521) and reaffirmed by the
spike (§5).

### The real-canopy-boot caveat (the first real risk Stage 1 must discharge)

The spike booted a **minimal stand-in**, not the real canopy. Its scope note is explicit (spike §6, lines
132–145): "**booting the real canopy cleanly is Stage 1's first acceptance test**, not yet proven here."
The real canopy:
- has a **~10–15 s** boot (it imports its full stack before binding);
- couples to downstream services at startup — it probes **JuniperData** (`src/main.py:254`) and
  **JuniperCascor** (`src/main.py:265`), and `/v1/health/ready` re-probes both (`src/main.py:948–953`);
- has **demo mode** (`JUNIPER_CANOPY_DEMO_MODE`, read at `src/settings.py:353`) as the **standalone**
  path that does not require the data/cascor services to be up.

**Build decision for you:** boot canopy in **demo mode** for a self-contained smoke (no data/cascor
needed) vs **full mode** (requires the stack up). Recommend demo mode for the default smoke; make the mode
a Skill argument. Confirm the exact env-var contract at build against `src/settings.py` (do not assume the
value — the spike used a stand-in, so canopy's real demo-mode wiring is unproven here).

### Plan-B (the fallback if Stage 1 surfaces a blocker the spike's scope did not)

If the real canopy boot proves intractable (real-boot fragility, secret/config coupling, MCP-grant
variance), **do not force E-1**. Fall back to the §6.9 **Plan-B** (lines 506–509): the **E-8** automatic
boot-time self-check (prevention) + **E-2** manual env-floor check (detection) + a small hand-run `curl`
HTTP smoke script — recovering most of E-1's value with none of its R=5 live-process risk. Record the
decision in a `notes/` follow-up; do not silently abandon.

### Process & ownership

- **One PR off `main`, never auto-merged.** Open the PR and hand off to the owner — Paul approves merges
  and any deployment gate. Do not merge to main yourself.
- **Worktree isolation** (mandatory): create a worktree under
  `/home/pcalnon/Development/python/Juniper/worktrees/` per `notes/WORKTREE_SETUP_PROCEDURE.md`. Never
  create a worktree inside the repo.
- **Each stage is its own PR** (rollback = delete the Skill + test + `ci.yml` line; plan §6.9 line 524).

---

## Verification (run these to confirm start state, then to check your work)

**Confirm starting state (before editing):**

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git checkout main && git pull --ff-only origin main
git log --oneline -8 | grep '#586'                       # spike (PR-8) is on main
ls .claude/skills/template-agent/SKILL.md                # model Skill present
ls .claude/skills/service-smoke 2>&1                      # MUST be absent (you create it)
ls tests/test_service_smoke_skill_lint.py 2>&1            # MUST be absent (you create it)
python3 -m unittest -v tests/test_template_agent_skill_lint.py   # model lint is green
sed -n '255,266p' .github/workflows/ci.yml               # the CI insertion neighborhood
```

If `#586` is **not** yet on `main`, stop and confirm with the owner before branching (the spike record is
the gate for proceeding). Then create your worktree/branch off `main`.

**Check your work (after editing):**

```bash
# 1. The new structural gate passes:
python3 -m unittest -v tests/test_service_smoke_skill_lint.py
# 2. The model gate still passes (you didn't break shared scaffolding):
python3 -m unittest -v tests/test_template_agent_skill_lint.py
# 3. The CI line you added points at a real path:
python3 -m unittest -v tests/test_workflow_script_paths.py
# 4. The AGENTS.md schema/tree lints still pass:
python3 -m unittest -v tests/test_agents_md_header_schema.py tests/test_agents_md_tree_drift.py
# 5. YAML sanity on the workflow:
python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml OK')"
```

**Manual smoke-verify (owner-run, local; cannot run in CI).** Document this procedure in the PR and ship a
runnable version of it. Acceptance (plan §6.9 lines 518–521; spike §5 lines 129–130): against a
*deliberately broken* canopy, the Skill **boots, fails `/v1/health`, reports the live traceback
`file:line`, and leaves no orphan python** (verify with `util/reap_pytest_orphans.bash --dry-run` showing
nothing to reap). A clean canopy should report `HEALTHY` and tear down clean. **Booting the REAL canopy
cleanly is the first acceptance test** — do that before the broken-canopy case.

Canopy boot reference (env `JuniperCanopy1` at `/opt/miniforge3/envs/JuniperCanopy1`, Python 3.13; ships
uvicorn 0.49.0 + fastapi 0.137.0 per spike §3):

```bash
# Canonical (juniper-canopy/AGENTS.md:85-86):
cd /home/pcalnon/Development/python/Juniper/juniper-canopy/src
uvicorn main:app --host 0.0.0.0 --port 8050 --log-level info
# or, explicit interpreter (juniper-canopy/AGENTS.md:980):
/opt/miniforge3/envs/JuniperCanopy1/bin/python main.py
# Health route: juniper-canopy/src/main.py:902-903  @app.get("/v1/health") / async def health_check()
# Port default 8050: juniper-canopy/src/settings.py:122
```

Launch the boot as a **harness background task** (like the spike) so the process handle persists across
tool calls; do not background with a bare `&` from a foreground step.

---

## Git status & gotchas

- **Start clean off `main`** once PR #586 is confirmed merged (it was, at the time of writing). Do all
  Stage-1 work in a dedicated worktree/branch (e.g. `feat/e1-stage1-service-smoke`).
- **`[skip ci]` orphan caveat (known, recurring).** `.github/workflows/agents-md-touch-up.yml` auto-bumps
  AGENTS.md's `Last Updated` on PR pushes that touch AGENTS.md, committing as `github-actions[bot]` with
  `[skip ci]`. If that bot commit lands as the PR HEAD, it can **orphan the required checks** (PR shows
  BLOCKED despite green) — the fix is an **empty re-trigger commit** to move HEAD off the skip-ci commit
  (precedent: ml #418). Watch for it after your AGENTS.md edit.
- **Do NOT put a literal `[skip ci]` token inside your own commit message body or PR body** — it has been
  parsed and suppressed CI runs unintentionally. If you must reference the token in prose, break it (e.g.
  `skip-ci`) so the CI trigger parser does not match it.
- **Never auto-merge.** Push the branch, open the PR against `main`, and hand off to the owner for review
  and merge. Deployment/merge approval is Paul's.

---

## Reference docs (by path — open them, do not work from memory)

- Spec: `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md` — §6.9 (E-1 detail, lines
  491–526), PR-9 roadmap entry (628–630), Plan-B (506–509).
- Spike record: `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md` — verdict §4, teardown
  gotchas §3 (98–108), carry-forward §5 (117–131), scope caveats §6 (132–145).
- Model Skill: `.claude/skills/template-agent/SKILL.md`.
- Model gate: `tests/test_template_agent_skill_lint.py`.
- Worktree setup: `notes/WORKTREE_SETUP_PROCEDURE.md`. Cleanup: `notes/WORKTREE_CLEANUP_PROCEDURE_V2.md`.

---

## Anchor ledger (re-verify each before relying on it)

**juniper-ml @ `f2ce007` (branch `feature/e1-stage1-handoff`; will be on `main` once #586 + this land):**

- `.claude/skills/template-agent/SKILL.md:5` — `allowed-tools: Read, Grep, Glob, Bash, Write, Agent`
- `.claude/skills/template-agent/SKILL.md:6` — `model: opus`
- `.claude/skills/template-agent/SKILL.md:7` — `effort: max`
- `.claude/skills/template-agent/SKILL.md:8` — `disable-model-invocation: true`
- `.claude/skills/template-agent/SKILL.md:26–68` — numbered bounded state machine (steps 1–8)
- `.claude/skills/template-agent/SKILL.md:70–75` — terminal-states block
- `tests/test_template_agent_skill_lint.py:11–13` — `.claude/**` pre-commit-excluded → unittest is the gate
- `tests/test_template_agent_skill_lint.py:28` — `_REQUIRED_TOOLS`
- `tests/test_template_agent_skill_lint.py:32–39` — `_REFERENCED_PATHS` (wire-to-real-artifacts list)
- `tests/test_template_agent_skill_lint.py:44–48` — `_find_repo_root` (self-locating)
- `tests/test_template_agent_skill_lint.py:84–109` — frontmatter asserts (name/tools/model/effort/user-only)
- `tests/test_template_agent_skill_lint.py:111–114` — `test_referenced_paths_exist` (on-disk wiring)
- `tests/test_template_agent_skill_lint.py:132–135` — bounded loop + terminal states asserts
- `.github/workflows/ci.yml:128–297` — hardcoded `python3 -m unittest -v` test list
- `.github/workflows/ci.yml:255–260` — `test_template_agent_skill_lint.py` line + comment (insertion model)
- `.github/workflows/ci.yml:265` — `test_agents_frontmatter.py` line (alt insertion neighbor)
- `.github/workflows/ci.yml:291` — `test_agents_md_tree_drift.py` line (top-level-tree gate)
- `tests/test_agents_md_tree_drift.py:10–13` — contract: top-level dirs only (won't force sub-entries)
- `util/reap_pytest_orphans.bash:14–20` — orphan-reap role + parent-PID safety + Juniper-path matching
- `util/reap_pytest_orphans.bash:40–41` — `JUNIPER_REAP_PROC_ROOT` / `JUNIPER_REAP_KILL_CMD` test hooks
- `util/kill_all_pythons.bash:4` — blunt `ps aux | grep python ... sudo kill -9` (last-resort only)
- `AGENTS.md:62` — Run-all-tests `python3 -m unittest -v tests/test_template_agent_skill_lint.py`
- `AGENTS.md:240` — Repository-Structure tree leaf for `test_template_agent_skill_lint.py`
- `AGENTS.md:334` — `### Tests` section header
- `AGENTS.md:361` — Tests-prose entry for `test_template_agent_skill_lint.py` (prose-entry model)
- `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md:491–526` — §6.9 E-1 detail
- `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md:628–630` — PR-9 roadmap entry
- `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md:98–108` — the two teardown gotchas
- `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md:117–131` — Stage-1 carry-forward + acceptance
- `notes/JUNIPER_ML_E1-SERVICE-SMOKE_STAGE0-SPIKE_2026-06-29.md:132–145` — real-canopy scope caveat

**juniper-canopy @ `79292bdc`:**

- `src/main.py:902` — `@app.get("/v1/health")`
- `src/main.py:903` — `async def health_check()`
- `src/main.py:933` — `/v1/health/live` route
- `src/main.py:939` — `/v1/health/ready` route
- `src/main.py:254` — JuniperData startup probe (`probe_dependency("JuniperData", …/v1/health/live)`)
- `src/main.py:265` — JuniperCascor startup probe
- `src/main.py:948–953` — `/v1/health/ready` dependency probes
- `src/main.py:3683` — `def main()`
- `src/main.py:3696` — `uvicorn.run(app, host=host, port=port, …)`
- `src/settings.py:122` — `port: int = 8050`
- `src/settings.py:353` — `JUNIPER_CANOPY_DEMO_MODE` read (standalone boot path)
- `AGENTS.md:85–86` — boot command `cd src && uvicorn main:app --host 0.0.0.0 --port 8050 --log-level info`
- `AGENTS.md:89` — `./demo` script note (handles conda activation; symlink → `util/juniper_canopy-demo.bash`)
- `AGENTS.md:30, 942, 948` — `JuniperCanopy1` env at `/opt/miniforge3/envs/JuniperCanopy1` (Python 3.13)

---

*End of handoff. Build the four coupled changes in one PR off `main`, gate it structurally, ship the
manual smoke-verify, and hand the PR to the owner — do not merge.*
