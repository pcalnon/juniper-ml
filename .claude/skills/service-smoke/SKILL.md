---
name: service-smoke
description: Boot a Juniper service (default canopy) in its conda env, probe /v1/health and key endpoints over HTTP, tail the boot log, and report any live traceback as file:line — the green-tests/dead-app failure class unit tests miss. HTTP-only in Stage 1 (the browser UI smoke is Stage 2). Teardown (SIGTERM→SIGKILL poll-to-down + orphan-reap) always runs, even on a mid-smoke failure.
argument-hint: "[--target canopy] [--mode demo|full] [--port 8050]"
allowed-tools: Read, Grep, Glob, Bash
model: opus
effort: max
disable-model-invocation: true
---

# service-smoke — HTTP-only runtime diagnostician

You **boot a real Juniper service in its conda env, probe it over HTTP, and report any live
failure as `file:line`** — the "green tests / dead app" class that unit tests cannot catch (a
service that imports clean and passes its units but `5xx`s on a real request, fails to bind, or
dies on boot). You run as a **Skill in the main conversation** so you can hold a reference to a
long-lived uvicorn process across tool calls — the capability a subagent lacks (its `Bash` CWD
resets per call, so it cannot manage a persistent process). **Teardown is non-negotiable and
leads this design:** every boot is paired with a `finally`-style teardown that reaps the process
even when an earlier step fails.

**Stage 1 is HTTP-only.** You do not drive a browser; the live UI smoke (navigate the dashboard,
read client-side state) is **Stage 2**, which adds `playwright` / `chrome-devtools`. Your tool
grant is deliberately `Read, Grep, Glob, Bash` — no browser MCP, and no `Agent` delegation.

## Inputs

- `--target` — the service to smoke (default: `canopy`). Stage 1 ships canopy support; the boot
  contract for any other service is confirmed at runtime against that repo, never assumed.
- `--mode` — `demo` (default) or `full`. **`demo`** boots canopy **standalone**: it sets
  `JUNIPER_CANOPY_DEMO_MODE=true`, so the backend is the in-process demo and cascor is never
  probed at startup; the JuniperData startup probe still runs but is **non-fatal** (a logged
  warning, not a boot failure), so demo mode needs no other Juniper service up — prefer it for a
  self-contained smoke. **`full`** requires the real stack (JuniperData + JuniperCascor) reachable;
  use it only when you are deliberately smoking the integrated path.
- `--port` — the bind port (default: `8050`, canopy's `settings.py` default).

Treat every input as untrusted: confirm the env, the port, and the boot command against the real
repo before you boot — never act on an assumed path or value.

## State machine

Run these steps in order. Step 8 (teardown) is mandatory and runs in a `finally`-style path: if
any of steps 3–7 fails or raises, you still execute teardown before terminating.

1. **Ingest** `--target` (default canopy), `--mode` (default demo), and `--port` (default 8050).
2. **Pre-flight (hard gate).** Confirm the `JuniperCanopy1` conda env exists
   (`/opt/miniforge3/envs/JuniperCanopy1`); confirm the target port is **free** before boot
   (`lsof -iTCP:<port> -sTCP:LISTEN` returns nothing); and record a baseline of the currently
   listening `JuniperCanopy1` pythons so teardown can distinguish a pre-existing process from the
   one you start. Confirm canopy's boot command, demo-mode env var, and health routes first-party
   against `juniper-canopy/src/settings.py`, `juniper-canopy/src/main.py`, and
   `juniper-canopy/AGENTS.md` (do not hardcode a stale value). If the env is missing or the port is
   occupied → `BOOT_FAILED` (never boot onto a busy port).
3. **Boot.** Launch canopy under `JuniperCanopy1` as a **persistent background process** so the
   handle survives across tool calls (the Stage-0 spike confirmed only a Skill in the main
   conversation can do this). Canonical boot from `juniper-canopy/src/` (confirm against
   `juniper-canopy/AGENTS.md`):

   ```bash
   # demo mode (standalone): export the env var, then boot uvicorn from src/
   JUNIPER_CANOPY_DEMO_MODE=true \
     /opt/miniforge3/envs/JuniperCanopy1/bin/python -m uvicorn main:app \
     --host 127.0.0.1 --port <port> --log-level info > <logfile> 2>&1
   ```

   Capture the **pid** and the **log file path** — both are required for the probe, the tail, and
   the teardown. Launch it as a harness background task, not a bare `&` from a foreground step.
4. **Wait-for-ready (bounded — no foreground `sleep`).** Poll the health endpoint with a bounded
   connection-retry until it answers or the timeout expires. Canopy's real boot is **~10–15 s** (it
   imports its full stack before binding), so allow a generous bound:

   ```bash
   curl --fail --silent --show-error --retry-connrefused \
     --retry 30 --retry-delay 1 --max-time 60 \
     http://127.0.0.1:<port>/v1/health
   ```

   If the bounded timeout expires with no bind → `BOOT_FAILED` (tail the log for the boot traceback
   first — see step 6).
5. **Probe.** Hit `/v1/health` and `/v1/health/live` (liveness — the primary PASS signal), then
   `/v1/health/ready` and any other key endpoints. **In `demo` mode, `/v1/health/ready` is expected
   to report degraded / not-ready** because it re-probes JuniperData + JuniperCascor, which are
   intentionally down — that is **not** a "dead app". Treat only a failed **liveness** probe
   (`/v1/health`, `/v1/health/live`) or a `5xx` from a key endpoint as a real failure. On any such
   non-200, capture the full response body.
6. **Tail + resolve.** Read/grep the captured log for tracebacks (`Traceback (most recent call
   last)`, `Error`, `Exception`). For each frame, resolve the `"<file>", line <N>` reference to a
   real `file:line` in the target repo. This is the core "green tests / dead app" report: a live
   runtime failure rendered as a clickable anchor the units never surfaced.
7. **Report.** Emit a structured PASS/FAIL: the boot outcome, each probe's status code, and any
   live traceback rendered as `file:line`. A clean boot with healthy liveness → `HEALTHY`; a boot
   that binds but fails a liveness probe or surfaces a live traceback → `UNHEALTHY_REPORTED` (this
   is a *successful* diagnosis, not a tool failure).
8. **Teardown (MANDATORY — `finally`-style).** Always run, even if an earlier step failed. Follow
   the **Teardown** section below exactly: poll-to-down with a SIGTERM→SIGKILL escalation and a
   bounded timeout, then orphan-reap and confirm the port is free. If the process will not die even
   after the SIGKILL escalation and reap → `TEARDOWN_ESCALATED` (report the surviving pid; the owner
   may need `util/kill_all_pythons.bash`).

## Terminal states

- `HEALTHY` — the service booted, bound, and passed its liveness probes; teardown left no orphan.
- `UNHEALTHY_REPORTED` — the service booted but failed a liveness probe or surfaced a live
  traceback; the failure is reported as `file:line`. This is a *successful* diagnosis.
- `BOOT_FAILED` — the env was missing, the port was occupied, or the bounded wait-for-ready timeout
  expired with no bind (the boot traceback, if any, is reported as `file:line`).
- `TEARDOWN_ESCALATED` — teardown could not confirm the process down after the SIGTERM→SIGKILL
  escalation and orphan-reap; the surviving pid is reported for manual intervention.

## Teardown (non-negotiable — encode both spike gotchas)

Teardown runs in a `finally`-style path so a mid-smoke failure still reaps the process. Two gotchas
were observed first-hand in the Stage-0 spike and **must** be honoured:

1. **SIGTERM is graceful, not instant — a TOCTOU trap.** A liveness `curl` fired *immediately* after
   `kill <pid>` (SIGTERM) still returned **200**, because uvicorn finishes in-flight requests before
   exiting. A teardown that asserts "down" right after the kill **false-fails**. → **Poll-to-down for
   connection-refused with a bounded timeout, and escalate SIGTERM → SIGKILL after the timeout.**
   Never assert down immediately after the signal:

   ```bash
   kill -TERM "<pid>"                          # graceful first
   for _ in $(seq 1 10); do                    # bounded poll-to-down (≤10s)
     curl --silent --max-time 1 "http://127.0.0.1:<port>/v1/health" >/dev/null 2>&1 || break
     sleep 1   # inside the bounded loop only — never a bare foreground settle
   done
   kill -KILL "<pid>" 2>/dev/null || true      # escalate if it is still listening
   ```

2. **`pgrep -af <name>` matches its own command line.** The orphan check `pgrep -af spike_app`
   matched the very bash process running the check (its argv contained the name), producing a
   **false-positive orphan**. → **Match the executable/argv precisely** (e.g.
   `ps -eo args | grep uvicorn | grep -v grep`) **or check the listening port**, and **exclude the
   checker's own PID**.

After the kill escalation: confirm the port is free (`lsof -iTCP:<port> -sTCP:LISTEN` empty) and that
no stray `JuniperCanopy1` python beyond the pre-flight baseline remains. Reuse the matching discipline
already encoded in **`util/reap_pytest_orphans.bash`** — it targets only Juniper-env/worktree pythons
and only kills a candidate whose parent is gone, is PID 1, or is the user `systemd --user`
(parent-PID safety). Run `util/reap_pytest_orphans.bash --dry-run` to see what it would reap, then
without `--dry-run` to reap. **`util/kill_all_pythons.bash` is the blunt last resort only** — it
`sudo kill -9`s *every* python on the host, so never use it as the primary teardown.

## Manual smoke-verify (owner-run; cannot run in CI)

The live boot needs conda + the real service, which ubuntu CI does not have, so CI runs only the
structural lint (`tests/test_service_smoke_skill_lint.py`). Correctness of the live behaviour is
verified by this **manual** procedure the owner runs locally:

1. **Real-canopy boot (the first acceptance test).** Invoke the Skill against a healthy canopy in
   demo mode. Expect: it boots within the bounded wait, `/v1/health` + `/v1/health/live` return 200,
   the terminal state is `HEALTHY`, and teardown leaves no orphan (confirm with
   `util/reap_pytest_orphans.bash --dry-run` showing nothing to reap).
2. **Deliberately-broken canopy (the diagnosis test).** Introduce a boot-time fault (e.g. a syntax
   error or a bad import in a startup module), then invoke the Skill. Expect: it boots, fails the
   liveness probe (or never binds), **reports the live traceback as `file:line`**, terminates
   `UNHEALTHY_REPORTED` (or `BOOT_FAILED`), and **leaves no orphan python**.

If the real canopy boot proves intractable (real-boot fragility, secret/config coupling, MCP-grant
variance), do **not** force E-1: fall back to the plan's **Plan-B** (the E-8 boot-time self-check +
the E-2 manual env-floor check + a hand-run `curl` smoke script) and record the decision in a
`notes/` follow-up. See `notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md` §6.9.

## Guardrails

- **HTTP-only (Stage 1).** Do not drive a browser; the UI smoke is **Stage 2**. Your grant is
  `Read, Grep, Glob, Bash` — no browser MCP, no `Agent` delegation.
- **Teardown always runs.** Pair every boot with a `finally`-style teardown; never leave a
  long-lived process behind. A mid-smoke failure still reaps.
- **Everything is bounded.** Every wait is a bounded `--retry` / loop with a `timeout` — never an
  unbounded "wait until ready", and never a bare foreground `sleep` as a settle.
- **Never invent a path / env / port.** Confirm canopy's boot command, demo-mode env var, and health
  routes first-party against the canopy repo before you boot; if you cannot confirm a value, stop and
  report rather than guess.
- **Diagnose, do not fix.** Report the live failure as `file:line`; you do not edit the target
  service.
