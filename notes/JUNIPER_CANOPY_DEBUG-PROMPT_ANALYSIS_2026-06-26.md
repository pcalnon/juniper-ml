# Prompt-Development Analysis — juniper-canopy Runtime-Breakage Debug Session

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**Document Type**: ANALYSIS (prompt development + meta-analysis)
**Status**: Complete
**Last Updated**: 2026-06-26

---

## 1. Purpose

This session was asked to **develop a prompt** (not to fix canopy) that will start a debugging
session for the juniper-canopy application — which, after a recent multi-stage refactor across all 9
Juniper repos, has green test suites but is broken badly enough at runtime that basic functionality
does not work. The prompt must direct a downstream session to: identify all the most serious issues,
analyze behavior, determine root causes, isolate code locations, develop root-cause fixes, generate
the fix code, and fully document results. Custom agents were to be employed as needed, and any other
Juniper issues discovered were to be recorded in a **meta-analysis**.

**Deliverables produced this session:**

1. **The prompt (primary):**
   [`prompts/generated/JUNIPER_CANOPY_RUNTIME-BREAKAGE_DEBUG_2026-06-26_1520.md`](../prompts/generated/JUNIPER_CANOPY_RUNTIME-BREAKAGE_DEBUG_2026-06-26_1520.md)
   — instantiated from the `regressions` (execution-class) template, fully grounded, validated PASS.
2. **This analysis document (session record + meta-analysis).**

---

## 2. The primary deliverable and its validation

- **Template selected:** `regressions` (`prompts/agent_templates/regressions.md`, `class: execution`,
  `required_fields: [symptom, resources]`). Rationale: the task shape is precisely "something that used
  to work and now fails after a change → diagnose → root-cause → fix → guard." Execution-class pulls in
  the RUBRIC R2.6 verify-and-recover/abort contract the prompt needs (it generates code + a PR).
  Candidates considered and rejected: `audit` (changes nothing — but the task wants fixes),
  `failing-tests` (the tests are *green*, not red), `task`/`generic` (less specific than `regressions`).
- **Grounding:** a real discovery bundle was generated for canopy
  (`python util/prompt_discovery/cli.py --repo-root <canopy>`; bundle on-HEAD `c25b7a1`, all seven
  probes `ok`), then **every** asserted anchor was re-probed first-party (grep + a conda-run signature
  probe in the live env).
- **Validation:** delegated to the **`prompt-validator`** subagent (cross-repo, with the corrected
  `prompts/agent_templates/` paths). Verdict: **`overall: PASS`**, `validator_status: ok`, **0 blocker /
  0 major**, all 13 `hallucination_risk[].grounded == true`. The one `minor` finding is a suite
  data-layer staleness item (§6.2 below), not a prompt defect; the validator recorded that the prompt
  correctly used the authoritative value.

> **Terminal state:** `EMIT_WITH_CAVEATS` for the suite (one minor, non-prompt finding) — effectively
> `EMIT_CLEAN` for the prompt itself. No edits were required to the prompt.

---

## 3. How the prompt was developed (work performed)

1. **Canopy reconnaissance (delegated, read-only `general-purpose` agent).** Confirmed repo layout,
   entry point (`uvicorn main:app` from `src/`; `app = FastAPI(` at `src/main.py:339`), the live env,
   the recent refactor history, and — via bounded import smoke tests — that the breakage is at runtime,
   not import. **Corrected a premise:** canopy does **not** consume `juniper-service-core` /
   `juniper-model-core` (zero references); the relevant churn was the model-selection "A1" work
   (issue #368, PRs #383–#401), the 3-D dataset viewer, build-provenance (observability 0.4.0), and the
   **client floor bumps**.
2. **Suite study (direct).** Read the Template Agent Skill, the template manifest + RUBRIC, the four
   agent definitions, and the `data/` convention layer to match the suite's contract and quality bar.
3. **Discovery + first-party grounding.** Generated the canopy bundle; then independently confirmed the
   installed versions and the three API gaps in `JuniperCanopy1` (see §5), and resolved the "188 failing
   tests" anomaly to a six-week-stale pytest cache.
4. **Authoring.** Filled a copy of the `regressions` template, mapping each of the seven task directives
   to ordered, checkable prompt directives, injecting only bundle/first-party-grounded anchors.
5. **Validation (delegated, `prompt-validator` subagent).** PASS (§2).

Agents employed: `general-purpose` (recon) and `prompt-validator` (validation) — both via the Agent
tool. This satisfied "employ custom agents as needed" and dogfooded the suite end-to-end, cross-repo.

---

## 4. The downstream task in one line

Canopy is grounded and the leading root cause is **confirmed**, but the prompt is deliberately written
so the downstream session **verifies empirically and does not stop at the known crashes** — it must run
the app, enumerate *all* serious issues, and fix root causes, because the reconnaissance was bounded
(no live-service run, no UI drive).

---

## 5. Grounded canopy findings (self-contained record)

**Root cause (first-party confirmed in `JuniperCanopy1`, Python 3.13):** the local env holds client
wheels **below the code's `pyproject.toml` floors**; the refactor adopted client APIs the stale wheels
lack. The env was never reinstalled from `requirements.lock` (which is itself correct). CI is green
because it installs from the lockfile and the test suite **mocks both clients**
(`src/tests/conftest.py:370-371`, autouse session fixture `mock_juniper_data_client`), so the real
constructor signatures are never exercised.

| Package | Installed | Floor (`pyproject.toml`) | Lock pin | API the code calls | Result |
|---|---|---|---|---|---|
| `juniper-data-client` | **0.4.0** | `>=0.4.1` (:138) | `==0.4.1` (lock:69) | `JuniperDataClient(on_request=…)` | TypeError |
| `juniper-cascor-client` | **0.3.0** | `>=0.5.0` (:149) | `==0.5.0` (lock:63) | `CascorControlStream(origin=…)` | TypeError |
| `juniper-cascor-client` | 0.3.0 | `>=0.5.0` | `==0.5.0` | `JuniperCascorClient.save_snapshot(...)` | AttributeError |
| `juniper-observability` | 0.4.0 | `>=0.4.0` (:109) | `==0.4.0` (lock:71) | build-info / metrics-auth | ok |

**Confirmed crash sites (grep + validator re-probe):**

- `src/demo_mode.py:918-921` and `:1795-1798` — `JuniperDataClient(... on_request=…)`. The constructor
  sits **above** the `try:` at `:935` whose `except` (`:944`) only catches `JuniperDataClientError`, so
  the `TypeError` is uncaught; the deprecated local fallback `_generate_spiral_dataset_local` (`:1001`)
  is unreachable. Demo mode is the default; the spiral fetch is core → first data fetch kills the page.
- `src/backend/cascor_service_adapter.py:44` import; `:131-134` `CascorControlStream(origin=self._ws_origin)`
  (intent comment `:88`); `:1537` `def save_snapshot` → `:1545` `self._client.save_snapshot(...)`.
- `create_backend` at `src/backend/__init__.py:33`.

**"188 failing tests" was a red herring.** The discovery `test_status` probe reads the cached
`.pytest_cache/v/cache/lastfailed`; this checkout's cache is dated **2026-05-13** (six weeks pre-refactor,
188 entries). A bounded `pytest --co -q` in `JuniperCanopy1` **collects cleanly (exit 0)** at HEAD.

**Secondary / suspected (handed to the downstream session, lower confidence):** full cascor-client
0.5.0 adapter-surface re-verification against a live backend (incl. the private `self._client._request`
seam at lines 911/920/929/962/981/1029/1045/1081/1108); recurrence is `status="live"`
(`src/model_registry.py:188`) and Start-enabled while `recurrence_service_url` / `recurrence_api_key`
default `None` (`src/settings.py:237/246`); `validate_npz_contract` data-client API churn note in
`demo_mode.py`; misleading commented old pins in the requirements docs (§6.6).

---

## 6. Meta-Analysis

### 6.1 Additional custom-agent specializations that would help

The current suite (`planner`, `auditor`, `task-executor`, `prompt-validator`, the `template-agent`
Skill) is **entirely static / read-only or single-task-execution**; none is built to *observe live
runtime behavior*. That is exactly the blind spot the canopy incident lives in. Highest-value gaps:

1. **Live-runtime / service-smoke diagnostician (highest value).** An agent that boots a service in its
   correct conda env (`uvicorn`/Dash), drives it (HTTP endpoints, and the UI via the available
   `chrome-devtools` / `playwright` MCP servers), tails logs, and reports live tracebacks with
   `file:line`. The "green tests, dead app" failure class is invisible to every current suite member by
   construction; this agent would target it directly. It pairs naturally with the `regressions` template.
2. **Environment / dependency-drift checker (a tool, possibly fronted by an agent).** Given a repo and a
   conda env, assert the **installed** `juniper-*` versions satisfy the repo's `pyproject.toml` floors /
   `requirements.lock`. This is the *exact* defect that broke canopy, and nothing currently catches it:
   `util/editable_install_drift_check.py` only inspects **editable** installs (`direct_url.json`), while
   canopy's were plain wheels. A natural extension to the discovery `dependency_facts` probe (which today
   reads pins but never compares them to the active interpreter).
3. **Cross-repo grounding support** (see §6.4 — currently an architectural limitation; a first-class
   `--target-repo` mode or a "cross-repo validator" variant would remove the manual workarounds this
   session needed).

A lighter-weight "runtime triage" variant of `auditor` (fast prioritized issue list feeding fixes,
rather than a full notes report) may also help, but is lower priority than 1–3.

### 6.2 Other Juniper issues discovered

Classified per the requested taxonomy. Each was **documented, not fixed** during the analysis
(deliverables were the prompt + this analysis); recommended owners noted. **Status update (2026-06-26):**
items **I-1**, **C-1** (canopy + cascor envs), and a new drift guard (`tests/test_agent_suite_path_drift.py`)
were fixed in **PR #566** (merged 2026-06-26; it also restored an `AGENTS.md` header line a prior commit had
dropped); the remaining items below stand.

**Incomplete development**

- **(I-1) Stale `prompts/templates/` references after the `prompts/agent_templates/` rename (functional,
  not cosmetic).** `.claude/agents/prompt-validator.md` instructs reading
  `prompts/templates/RUBRIC.md` and `prompts/templates/manifest.yaml` — **paths that no longer exist** —
  so the validator fails to find its own contract unless the caller overrides the path (this session had
  to). `RUBRIC.md` (R2.5 text + design links), `planner.md` / `auditor.md` descriptions, and `AGENTS.md`
  (≥8 hits: lines 219, 222, 241, 244, 300, 306, 328, 332) also still say `prompts/templates/`. The
  library tests pass because they reference the new path; the drift lives in **agent prose**, which tests
  don't execute. *Recommend:* sweep `prompts/templates/` → `prompts/agent_templates/` across `.claude/`
  and `AGENTS.md`, and add a lint that greps the agent/Skill bodies for the dead path. **Owner: juniper-ml.**
- **(I-2) Env provisioning gap (the actual canopy incident).** `JuniperCanopy1` was never reinstalled
  from `requirements.lock` after the floor bumps, and no guard enforces that an env satisfies the repo's
  floors. *Recommend:* the drift checker in §6.1.2 + a documented post-refactor reinstall step.
  **Owner: juniper-canopy + juniper-ml (tooling).**

**Configuration problems**

- **(C-1) Data-layer `ecosystem.yaml` staleness** (the validator's lone `minor`). `conda_envs` lists
  `JuniperCanopy {python: 3.14}`; the live env is `JuniperCanopy1 {python: 3.13}` (canopy `AGENTS.md`;
  commit `a06abb1`). Because RUBRIC **R2.5 validates injected conventions against this data layer**, a
  stale data layer risks **false rubric failures** for correct prompts. *Recommend:* update
  `prompts/agent_templates/data/ecosystem.yaml` `conda_envs`. **Owner: juniper-ml.**
- **(C-2) Misleading commented client pins in canopy requirements docs.** `conf/requirements.txt`,
  `requirements.txt`, `requirements_ci.txt` carry old `# juniper-cascor-client==0.3.0` /
  `# juniper-data-client==0.4.0` (lines ~82/84) while `requirements.lock` is correct. Anyone reinstalling
  from those could re-introduce the drift. *Recommend:* refresh or delete the commented pins.
  **Owner: juniper-canopy.**

**Design gaps**

- **(D-1) `test_status` discovery probe has no cache-freshness guard.** It returns a 6-week-old
  `lastfailed` count as `status: "ok"` (`util/prompt_discovery/test_status.py:15-37`). The probe's own
  docstring promises "no failures can never masquerade as fact" — but the inverse failed here: a **stale
  failure count masqueraded as current** and misdirected the initial read toward "188 failing." *Recommend:*
  stamp the cache mtime into the output and flag/`unavailable` it past a TTL. **Owner: juniper-ml.**
- **(D-2) Canopy demo-mode degradation choice.** The data client is constructed above the `try:`
  (`demo_mode.py:918`/`:935`) and the `except` (`:944`) only catches `JuniperDataClientError`, so a
  constructor `TypeError` hard-crashes despite a deprecated local fallback existing (`:1001`). "No local
  fallback" is documented as intentional, so this is a **choice to revisit**, not a clear bug. *Recommend:*
  the downstream session raises it for an owner decision. **Owner: juniper-canopy (decision).**
- **(D-3) Recurrence model `status="live"` + Start-enabled with no service URL.** `model_registry.py:188`
  marks it live and D8 Train-gating allows Start, but `recurrence_service_url` defaults `None`
  (`settings.py:237`) and the demo path sets neither URL nor key → selecting "Recurrence (LMU)" and
  starting fails to reach a service with no obvious UX guard. *Recommend:* gate Start on a resolvable
  service, or define the failure UX. **Owner: juniper-canopy.**

**Architectural weaknesses**

- **(A-1) The suite is single-repo by construction.** `prompt_discovery/cli.py` and `prompt-validator`
  assume CWD == target repo (the freshness gate runs `git rev-parse HEAD` on CWD; re-probes are
  CWD-relative). Authoring a canopy-targeted prompt *from* juniper-ml (the suite's home) required manual
  cross-repo overrides. Since the suite's home is juniper-ml and most targets are **sibling repos**,
  cross-repo is the common case. *Recommend:* a first-class `--target-repo` mode. **Owner: juniper-ml.**
- **(A-2) No live-runtime coverage in the suite** (the §6.1.1 gap, framed as a weakness): the suite
  cannot, by design, catch "green tests / dead app." **Owner: juniper-ml.**

**Syntax errors**

- **None found.** No syntax errors were discovered this session (canopy collected cleanly in the live
  env). Recorded explicitly so the absence is not mistaken for "not checked."

**Suspected (unverified this session)**

- **(S-1) Sibling-env plain-wheel drift.** `JuniperCascor1` / `JuniperData` may show the same
  installed-vs-lockfile drift; not checked here. The prompt instructs the downstream session to note (not
  fix) it; a short ecosystem env-drift audit is warranted. **Owner: juniper-ml (audit).**

### 6.3 What worked (process note)

Dogfooding the suite **cross-repo** succeeded: the recon agent grounded the prompt, the discovery CLI
produced a clean on-HEAD bundle for a *sibling* repo, and the `prompt-validator` independently re-probed
13 anchors and returned PASS — all from the juniper-ml worktree, with only the documented cross-repo and
rename workarounds. The suite is usable today; §6.2 lists what would make it frictionless.

---

## 7. Appendix — key reproduction commands

```bash
# Linchpin: installed versions + the three API gaps (the smoking gun)
conda run -n JuniperCanopy1 python -c "import importlib.metadata as m,inspect; \
from juniper_data_client import JuniperDataClient as D; from juniper_cascor_client import CascorControlStream as S, JuniperCascorClient as C; \
print('data-client', m.version('juniper-data-client'), 'on_request', 'on_request' in inspect.signature(D.__init__).parameters); \
print('cascor-client', m.version('juniper-cascor-client'), 'origin', 'origin' in inspect.signature(S.__init__).parameters, 'save_snapshot', hasattr(C,'save_snapshot'))"

# Stale-cache proof
stat -c '%y' /home/pcalnon/Development/python/Juniper/juniper-canopy/.pytest_cache/v/cache/lastfailed

# Clean collection in the live env (cache-safe)
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && conda run -n JuniperCanopy1 python -m pytest --co -q -p no:cacheprovider

# Regenerate the discovery grounding bundle for canopy
cd /home/pcalnon/Development/python/Juniper/juniper-ml && python util/prompt_discovery/cli.py \
  --repo-root /home/pcalnon/Development/python/Juniper/juniper-canopy \
  --subject "canopy runtime breakage post-refactor client floor drift" \
  --symbols "JuniperDataClient,CascorControlStream,save_snapshot,create_backend"
```
