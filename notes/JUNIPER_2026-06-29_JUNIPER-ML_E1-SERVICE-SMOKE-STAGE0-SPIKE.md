# Juniper-ml — E-1 Live-Runtime / Service-Smoke Diagnostician: Stage-0 Feasibility Spike

**Project**: juniper-ml — Custom-Agent Suite
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 1.0.0
**Last Updated**: 2026-06-29

---

## 1. What this is

The **Stage-0 feasibility spike** for enhancement **E-1** (live-runtime / service-smoke diagnostician),
mandated by the custom-agent-suite enhancement plan
[`notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md` §6.9](JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md)
(PR-8). E-1 targets gap **A-2** — the "green tests / dead app" failure class that none of the shipped
units catch at runtime (a service that imports clean and passes its unit tests but 500s on a real
request, fails to bind, or dies on boot).

The plan stages E-1 because it is the suite's **highest-risk** unit (R=5): it manages long-lived
processes and depends on MCP grants. Stage 0 is a **throwaway** spike whose only job is to answer one
feasibility question before any runtime surface is committed.

**The feasibility question (verbatim from §6.9).** Prove a Skill running in the main conversation can:

- **(a)** boot a service in its conda env,
- **(b)** drive it via MCP, and
- **(c)** reach it (HTTP).

**Kill-criterion.** If **any** of the three fails → stop and record a **KILL** verdict; fall back to the
§6.9 Plan-B (E-8 boot-time self-check + E-2 manual env-floor check + a hand-run `curl` smoke script — no
live-process-managing agent).

**Deliverable.** This `notes/` record + a proceed/kill decision. **No committed runtime surface** (no
Skill, no `util/` code; the spike's only artifact is this document).

## 2. Method

The spike was run **in the main conversation** (not a subagent), deliberately mirroring how E-1 must run
as a **Skill**: a subagent's `Bash` CWD resets per tool call, so it cannot hold a reference to a
long-lived process — the structural reason §6.9 makes E-1 a Skill, not a subagent. The spike used a
**minimal throwaway stand-in service** rather than the real canopy app (rationale in §6): the question is
whether the *mechanism* works, which a representative ASGI service proves without the real app's heavy
boot, secrets, and downstream-service coupling (those are Stage 1's concern).

Stand-in: a ~20-line FastAPI app (`/v1/health` + a trivial HTML index, matching the Juniper
health-endpoint convention), booted under the **JuniperCanopy1** conda env's `uvicorn` on `127.0.0.1:8765`.

## 3. Findings — first-party evidence

Pre-flight survey: no Juniper service was listening on 8050/8100/8201; all three active conda envs present
(JuniperCanopy1 / JuniperCascor1 @ 3.13, JuniperData @ 3.14); both teardown tools present
(`util/reap_pytest_orphans.bash`, `util/kill_all_pythons.bash`); the canopy env ships the real ASGI stack
(**uvicorn 0.49.0 + fastapi 0.137.0**).

### (a) Boot a service in its conda env — ✅ PASS

`/opt/miniforge3/envs/JuniperCanopy1/bin/python -m uvicorn spike_app:app --host 127.0.0.1 --port 8765`
(launched as a harness background task so the process persists across tool calls — the
persistent-state capability a Skill has and a subagent lacks). Boot log:

```text
INFO:     Started server process [4128189]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

The listener (`lsof -iTCP:8765 -sTCP:LISTEN`) was the canopy-env python, pid 4128189.

### (c) Reach it via HTTP — ✅ PASS

`curl --retry-connrefused --retry 20 --retry-delay 1 http://127.0.0.1:8765/v1/health` (connection-retry to
await bind; no foreground `sleep`):

```text
{"status":"ok","service":"e1-spike","env":"JuniperCanopy1"}  -> HTTP 200 in 0.0093s
```

### (b) Drive it via MCP — ✅ PASS

The **Playwright MCP** server (configured + granted in-session) navigated a real browser to the live
service and read its DOM via JavaScript evaluation:

```text
navigate http://127.0.0.1:8765/  ->  Page URL: http://127.0.0.1:8765/
evaluate document.querySelector('#spike').textContent  ->  "E-1 spike OK"
```

This exercises exactly the **Stage-2 UI-smoke** capability (navigate a live app + read client-side state).
(One harmless console 404 — a favicon — was observed and is irrelevant.)

### Teardown (the R=5 risk) — ✅ clean, with two recorded gotchas

`kill <pid>` (SIGTERM) → after settle: `curl` → connection refused (port free); no listener on 8765;
no `uvicorn`/`spike_app` process; `kill -0 4128189` → gone. **No orphan.**

**Two teardown gotchas observed first-hand (must be baked into the Stage-1 Skill's teardown step):**

1. **SIGTERM is graceful, not instant — a TOCTOU trap.** A `curl` fired *immediately* after `kill` still
   got a 200 (uvicorn was finishing in-flight requests before exiting). A teardown step that asserts
   "down" right after the kill **false-fails**. → poll for connection-refused with a bounded timeout
   (and escalate SIGTERM → SIGKILL after the timeout), do not assert immediately.
2. **`pgrep -af <name>` matches its own command line.** The orphan check `pgrep -af spike_app` matched the
   very bash process running the check (its argv contained "spike_app"), producing a **false-positive
   orphan**. → match the process *executable*/argv precisely (e.g. `ps -eo args | grep uvicorn` with
   `grep -v grep`, or check the listening port), and exclude the checker's own PID. This is the same
   class of care `util/reap_pytest_orphans.bash` already encodes — reuse it.

## 4. Verdict — **PROCEED**

All three feasibility claims passed with first-party evidence, and clean teardown was demonstrated. The
kill-criterion is **not** triggered. E-1 is **feasible** in this environment; proceed to **Stage 1**
(HTTP-only diagnostician). This spike also discharges the design-of-record Appendix-B "confirm-at-build"
items for E-1 (Skill-vs-subagent + MCP availability).

## 5. Carry-forward into Stage 1 (PR-9)

- **Teardown is non-negotiable and must lead the design.** Encode gotchas (1) and (2) above: poll-to-down
  with a SIGTERM→SIGKILL escalation + bounded timeout, port-based liveness checks, and reuse the
  `util/reap_pytest_orphans.bash` / `util/kill_all_pythons.bash` patterns. Teardown runs in a `finally`
  path so a mid-smoke failure still reaps the process.
- **Skill, not subagent** — confirmed structurally (persistent process handle + in-session MCP both
  required and both only available in the main conversation).
- **Gate**: structural-only `tests/test_service_smoke_skill_lint.py` (modeled on
  `tests/test_template_agent_skill_lint.py`) — frontmatter (opus + max, user-only, declared MCP/tools) +
  wiring to real artifacts **+ an explicit teardown step** — plus a documented **manual** smoke-verify the
  owner runs (the live boot cannot run in ubuntu CI: no conda, no services).
- **Acceptance for Stage 1**: against a *deliberately broken* canopy, the Skill boots, fails `/v1/health`,
  reports the live traceback `file:line`, and **leaves no orphan python**.

## 6. Scope, caveats, and honesty notes

- **Stand-in, not the real canopy.** The spike booted a minimal FastAPI app in the canopy env, not the
  real canopy (whose boot is ~10–15 s and pulls in its full stack + secrets + the data service). This
  proves the *mechanism* (conda-env boot → HTTP → MCP-drive → teardown); **booting the real canopy
  cleanly is Stage 1's first acceptance test**, not yet proven here. This is a deliberate
  spike-scope choice, stated plainly so "feasible" is not over-read as "the real app boots".
- **One MCP driver tested.** Playwright was exercised and passed; `chrome-devtools` (also configured) was
  not separately tested — Stage 2 can use either, and one working driver satisfies claim (b).
- **No runtime surface committed.** Per §6.9, the spike's stand-in (`spike_app.py`) lived only in the
  session scratchpad and is discarded; this document is the sole committed artifact.
- **Plan-B remains the fallback** if Stage 1 surfaces a blocker the spike's minimal scope did not (real
  canopy boot fragility, secret/config coupling, MCP-grant variance in headless/cron runs).
