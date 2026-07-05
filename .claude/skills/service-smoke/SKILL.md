---
name: service-smoke
description: Boot a Juniper service (default canopy) in its conda env, probe /v1/health and key endpoints over HTTP, tail the boot log, and report any live failure as file:line — the green-tests/dead-app class unit tests miss. An opt-in browser UI smoke (--ui) drives the live dashboard via the playwright MCP and reports client-side failures. Teardown (SIGTERM→SIGKILL poll-to-down + browser close + orphan-reap) always runs, even on a mid-smoke failure.
argument-hint: "[--target canopy] [--mode demo|full] [--port 8050] [--ui]"
allowed-tools: Read, Grep, Glob, Bash, mcp__playwright
model: opus
effort: max
disable-model-invocation: true
---

# service-smoke — runtime diagnostician (HTTP + opt-in UI smoke)

You **boot a real Juniper service in its conda env, probe it over HTTP, optionally drive its live
UI, and report any live failure as `file:line`** — the "green tests / dead app" class that unit
tests cannot catch (a service that imports clean and passes its units but `5xx`s on a real request,
fails to bind, dies on boot, or renders a broken dashboard). You run as a **Skill in the main
conversation** so you can hold a reference to a long-lived uvicorn process — and a live browser
session — across tool calls; a subagent's `Bash` CWD resets per call and cannot. **Teardown is
non-negotiable and leads this design:** every boot (and every browser session) is paired with a
`finally`-style teardown that reaps even when an earlier step fails.

**The HTTP smoke is the default; the browser UI smoke is opt-in via `--ui` (Stage 2).** When `--ui`
is set, after the HTTP smoke you drive the live dashboard with the **`playwright` MCP**
(`mcp__playwright__browser_*` — navigate, snapshot, console messages, network requests, close),
collect client-side failures, and report them. The `chrome-devtools` MCP is an equivalent
alternative if playwright is unavailable. You still do **not** delegate to a subagent (`Agent` is
not granted — this Skill manages the live processes itself).

## Inputs

- `--target` — the service to smoke (default: `canopy`). Stage 1/2 ship canopy support; the boot and
  dashboard contract for any other service is confirmed at runtime against that repo, never assumed.
- `--mode` — `demo` (default) or `full`. **`demo`** boots canopy **standalone**: it sets
  `JUNIPER_CANOPY_DEMO_MODE=true`, so the backend is the in-process demo and cascor is never probed
  at startup; the JuniperData startup probe still runs but is **non-fatal** (a logged warning, not a
  boot failure), so demo mode needs no other Juniper service up — prefer it for a self-contained
  smoke. **`full`** requires the real stack (JuniperData + JuniperCascor) reachable.
- `--port` — the bind port (default: `8050`, canopy's `settings.py` default).
- `--ui` — opt-in: after the HTTP smoke, run the **browser UI smoke** against the live dashboard
  (default: off → HTTP-only, identical to Stage 1). Requires the `playwright` MCP connected
  in-session; if it is not, report that and finish as an HTTP-only smoke rather than failing.

Treat every input as untrusted: confirm the env, the port, the boot command, and the dashboard mount
against the real repo before you act — never act on an assumed path or value.

## State machine

Run these steps in order. Step 9 (teardown) is mandatory and runs in a `finally`-style path: if any
of steps 3–8 fails or raises, you still execute teardown — **the open browser AND the uvicorn
process** — before terminating.

1. **Ingest** `--target` (default canopy), `--mode` (default demo), `--port` (default 8050), and
   `--ui` (default off).
2. **Pre-flight (hard gate).** Confirm the `JuniperCanopy1` conda env exists
   (`/opt/miniforge3/envs/JuniperCanopy1`); confirm the target port is **free** before boot
   (`lsof -iTCP:<port> -sTCP:LISTEN` returns nothing); record a baseline of currently listening
   `JuniperCanopy1` pythons so teardown can distinguish a pre-existing process from the one you start.
   Confirm canopy's boot command, demo-mode env var, health routes, and the dashboard mount path
   first-party against `juniper-canopy/src/settings.py`, `juniper-canopy/src/main.py`, and
   `juniper-canopy/AGENTS.md` (do not hardcode a stale value). If `--ui` is set, note whether the
   `playwright` MCP is available. If the env is missing or the port is occupied → `BOOT_FAILED`.
3. **Boot.** Launch canopy under `JuniperCanopy1` as a **persistent background process** so the
   handle survives across tool calls. Canonical boot from `juniper-canopy/src/`:

   ```bash
   # demo mode (standalone): export the env var, then boot uvicorn from src/
   JUNIPER_CANOPY_DEMO_MODE=true \
     /opt/miniforge3/envs/JuniperCanopy1/bin/python -m uvicorn main:app \
     --host 127.0.0.1 --port <port> --log-level info > <logfile> 2>&1
   ```

   Capture the **pid** and the **log file path**. Launch it as a harness background task, not a bare
   `&` from a foreground step.
4. **Wait-for-ready (bounded — no foreground `sleep`).** Poll the health endpoint with a bounded
   connection-retry until it answers or the timeout expires. Canopy's real boot is **~10–15 s**:

   ```bash
   curl --fail --silent --show-error --retry-connrefused \
     --retry 30 --retry-delay 1 --max-time 60 \
     http://127.0.0.1:<port>/v1/health
   ```

   If the bounded timeout expires with no bind → `BOOT_FAILED` (tail the log for the boot traceback
   first — see step 6).
5. **Probe (HTTP).** Hit `/v1/health` and `/v1/health/live` (liveness — the primary PASS signal),
   then `/v1/health/ready` and any other key endpoints. **In `demo` mode, `/v1/health/ready` is
   expected to report degraded / not-ready** because it re-probes JuniperData + JuniperCascor, which
   are intentionally down — that is **not** a "dead app". Treat only a failed **liveness** probe or a
   `5xx` from a key endpoint as a real failure. On any such non-200, capture the full response body.
6. **Tail + resolve.** Read/grep the captured log for tracebacks (`Traceback (most recent call
   last)`, `Error`, `Exception`); resolve each `"<file>", line <N>` frame to a real `file:line` in
   the target repo. This is the core "green tests / dead app" report.
7. **UI smoke (opt-in — only if `--ui`).** Drive the live dashboard with the `playwright` MCP:
   - **Navigate** to `http://127.0.0.1:<port>/dashboard` (canopy mounts the Dash app there via
     `WSGIMiddleware`; confirm the mount against `juniper-canopy/src/main.py` — do not assume `/`).
   - **Wait (bounded)** for the app shell to render, then take a `browser_snapshot` to confirm the
     dashboard root mounted (not a blank page or an error shell).
   - **Collect** `browser_console_messages` (JS errors) and the failed `browser_network_requests`.
   - **Classify:** a JS console **exception**, a `5xx`/failed request to a key dashboard API, or an
     **unrendered** app shell is a **client-side failure**. A demo-mode "degraded"/"no data" banner
     (downstream deps intentionally down) is **not** — treat it like `/v1/health/ready`'s
     expected-degraded, so the UI smoke does not cry wolf.
8. **Report.** Emit a structured PASS/FAIL: boot outcome, each HTTP probe's status, any live
   traceback as `file:line`, and (if `--ui`) the UI verdict with any client-side failure. Clean HTTP
   (+ clean UI when `--ui`) → `HEALTHY`. HTTP failure / live traceback → `UNHEALTHY_REPORTED`. HTTP
   healthy but a UI client-side failure → `UI_UNHEALTHY_REPORTED`.
9. **Teardown (MANDATORY — `finally`-style).** Always run, even if an earlier step failed. Follow the
   **Teardown** section below: **close the browser first**, then poll-to-down the uvicorn process with
   a SIGTERM→SIGKILL escalation and a bounded timeout, orphan-reap, and confirm the port is free. If
   the process will not die even after SIGKILL + reap → `TEARDOWN_ESCALATED`.

## Terminal states

- `HEALTHY` — booted, bound, passed its liveness probes (and, with `--ui`, a clean UI smoke);
  teardown left no orphan process and no orphan browser.
- `UNHEALTHY_REPORTED` — booted but failed a liveness probe or surfaced a live traceback; reported as
  `file:line`. A successful diagnosis.
- `UI_UNHEALTHY_REPORTED` — HTTP-healthy but the opt-in `--ui` smoke found a **client-side failure**
  (a JS console exception, a failed key dashboard request, or an unrendered app shell). A successful
  diagnosis of the "green API / broken dashboard" case.
- `BOOT_FAILED` — the env was missing, the port was occupied, or the bounded wait-for-ready timeout
  expired with no bind (the boot traceback, if any, is reported as `file:line`).
- `TEARDOWN_ESCALATED` — teardown could not confirm the process down after the SIGTERM→SIGKILL
  escalation and orphan-reap; the surviving pid is reported for manual intervention.

## Teardown (non-negotiable — close the browser AND reap the server)

Teardown runs in a `finally`-style path so a mid-smoke failure still reaps. **If a UI smoke opened a
browser, close it first** with `mcp__playwright__browser_close` (a left-open headless browser is an
orphan too), then reap uvicorn. Two server gotchas, observed first-hand in the Stage-0 spike, **must**
be honoured:

1. **SIGTERM is graceful, not instant — a TOCTOU trap.** A liveness `curl` fired *immediately* after
   `kill <pid>` (SIGTERM) still returned **200**, because uvicorn finishes in-flight requests before
   exiting. A teardown that asserts "down" right after the kill **false-fails**. → **Poll-to-down for
   connection-refused with a bounded timeout, and escalate SIGTERM → SIGKILL after the timeout.**

   ```bash
   kill -TERM "<pid>"                          # graceful first
   for _ in $(seq 1 10); do                    # bounded poll-to-down (≤10s)
     curl --silent --max-time 1 "http://127.0.0.1:<port>/v1/health" >/dev/null 2>&1 || break
     sleep 1   # inside the bounded loop only — never a bare foreground settle
   done
   kill -KILL "<pid>" 2>/dev/null || true      # escalate if it is still listening
   ```

2. **`pgrep -af <name>` matches its own command line.** The orphan check `pgrep -af spike_app` matched
   the very bash process running the check (its argv contained the name), producing a
   **false-positive orphan**. → **Match the executable/argv precisely** (e.g.
   `ps -eo args | grep uvicorn | grep -v grep`) **or check the listening port**, and **exclude the
   checker's own PID**.

After the kill escalation: confirm the port is free (`lsof -iTCP:<port> -sTCP:LISTEN` empty) and that
no stray `JuniperCanopy1` python beyond the pre-flight baseline remains. Reuse the matching discipline
already encoded in **`util/reap_pytest_orphans.bash`** — it targets only Juniper-env/worktree pythons
and only kills a candidate whose parent is gone, is PID 1, or is the user `systemd --user`
(parent-PID safety). Run `util/reap_pytest_orphans.bash --dry-run` first, then without `--dry-run` to
reap. **`util/kill_all_pythons.bash` is the blunt last resort only** — it `sudo kill -9`s *every*
python on the host, so never use it as the primary teardown.

**Do not commit playwright artifacts.** The `playwright` MCP writes page snapshots/screenshots under
`.playwright-mcp/` (a **tracked** dir in this repo). Never `git add` them; `git restore` / discard any
that appear so a UI smoke never pollutes a commit.

## Manual smoke-verify (owner-run; cannot run in CI)

The live boot needs conda + the real service (and the UI smoke a real browser MCP), which ubuntu CI
does not have, so CI runs only the structural lint (`tests/test_service_smoke_skill_lint.py`).
Correctness of the live behaviour is verified by this **manual** procedure the owner runs locally:

1. **Real-canopy HTTP boot** (the Stage-1 acceptance test). Invoke against a healthy canopy in demo
   mode (no `--ui`). Expect: boots within the bounded wait, `/v1/health` + `/v1/health/live` return
   200, terminal `HEALTHY`, teardown leaves no orphan (`util/reap_pytest_orphans.bash --dry-run`
   shows nothing).
2. **UI smoke, clean** (the Stage-2 happy path). Boot a clean canopy in demo mode and invoke with
   `--ui`. Expect: navigates `/dashboard`, the app shell renders, no JS console exceptions → terminal
   `HEALTHY`; teardown closes the browser **and** reaps uvicorn (no orphan browser, no orphan python).
3. **UI smoke, client-side failure** (the Stage-2 acceptance test). Inject a UI fault (e.g. a JS error
   or a broken Dash callback), invoke with `--ui`. Expect: it reports the **client-side failure**,
   terminates `UI_UNHEALTHY_REPORTED`, and tears down clean.

If the real canopy boot or the UI drive proves intractable (real-boot fragility, secret/config
coupling, MCP-grant variance), do **not** force E-1: fall back to the plan's **Plan-B** (the E-8
boot-time self-check + the E-2 manual env-floor check + a hand-run `curl` smoke script) and record the
decision in a `notes/` follow-up. See
`notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md` §6.9.

## Guardrails

- **HTTP smoke is the default; the UI smoke is opt-in via `--ui`** (the `playwright` MCP). No `Agent`
  delegation — this Skill manages its live processes itself.
- **Teardown always runs** — **browser close first, then server reap** — in a `finally`-style path;
  never leave a long-lived process or a headless browser behind. A mid-smoke failure still reaps.
- **Everything is bounded.** Every wait is a bounded `--retry` / loop with a `timeout` — never an
  unbounded "wait until ready", and never a bare foreground `sleep` as a settle.
- **Never invent a path / env / port / mount.** Confirm canopy's boot command, demo-mode env var,
  health routes, and the `/dashboard` mount first-party before you act; if you cannot confirm a value,
  stop and report rather than guess.
- **Never commit `.playwright-mcp/` artifacts.**
- **Diagnose, do not fix.** Report the live failure as `file:line`; you do not edit the target service.
