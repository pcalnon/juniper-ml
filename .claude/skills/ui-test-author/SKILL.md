---
name: ui-test-author
description: Author a reviewed, never-auto-merged pytest-playwright UI test modeled on canopy's src/tests/ui/ harness. Boots the target app and drives its live dashboard via the playwright MCP to observe a real control and its outcome, then writes a @pytest.mark.ui test into the target repo's src/tests/ui/ (uncommitted) for you to review, run, and PR. Teardown (browser close + SIGTERM→SIGKILL reap) always runs.
argument-hint: "[--target canopy] [--control <selector|description>] [--port 8050] [--mode demo|full]"
allowed-tools: Read, Grep, Glob, Bash, Write, mcp__playwright
model: opus
effort: max
disable-model-invocation: true
---

# ui-test-author — click-through UI test author

You **author a click-through UI test by driving the real app**: boot the target webapp, use the
`playwright` MCP to exercise a live control and observe its outcome, then emit a pytest-playwright
test modeled on the target repo's existing UI harness — **for human review, never auto-merged**. You
run as a **Skill in the main conversation** so you can hold the live browser session across tool
calls and **ask the owner which control/outcome to capture**. **Teardown is non-negotiable** (close
the browser, reap the booted app) and runs in a `finally`-style path.

You **observe, then reproduce**. The emitted test is a reviewed artifact: you write it into the target
repo's `src/tests/ui/` **uncommitted** and present it — you never `git add`, commit, PR, or merge it,
and you never edit any other file in the target repo. This Skill builds on the `service-smoke` Skill's
boot/teardown discipline (E-1) and its proven live-UI drive.

## Inputs

- `--target` — the app to author against (default: `canopy`). Canopy is the reference harness
  (`juniper-canopy/src/tests/ui/`, ~10 pytest-playwright tests); another target's harness is confirmed
  at runtime, never assumed.
- `--control` — the control to test: a selector like `#apply-params-button`, or a description you
  resolve to a selector by exploring the live DOM. If omitted, **ask the owner** which control and what
  observable outcome to capture.
- `--port` (default `8050`) and `--mode` (`demo` default / `full`) — the boot mode, as in the
  `service-smoke` Skill; `demo` boots canopy standalone (`JUNIPER_CANOPY_DEMO_MODE=true`).

Treat every input as untrusted: confirm the harness shape, the dashboard mount, and the control
selector against the real repo before you author — never invent a selector, a value, or an outcome.

## State machine

Run these steps in order. Step 8 (teardown) is mandatory and runs in a `finally`-style path: if any of
steps 3–7 fails or raises, you still tear down the browser AND the booted app before terminating.

1. **Ingest** `--target` / `--control` / `--port` / `--mode`. If `--control` is unset, ask the owner
   which control + observable outcome to capture.
2. **Model on the harness (hard gate).** Read the target repo's `src/tests/ui/` first-party: the
   `conftest.py` fixtures (canopy exposes `canopy_url` + `dashboard_page`), an exemplar
   (`test_dashboard_loads.py`), and the `@pytest.mark.ui` convention. Match that shape exactly — do not
   invent a fixture or a marker. Confirm the dashboard mount (`/dashboard/`) and the stable control IDs
   against the real layout.
3. **Boot** the target app under its conda env as a **persistent background process** (reuse the
   `service-smoke` boot — `JUNIPER_CANOPY_DEMO_MODE=true`, uvicorn under `JuniperCanopy1`, capture the
   pid + log path). Launch it as a harness background task, not a bare `&`.
4. **Wait-for-ready (bounded — no foreground `sleep`).** `curl --retry-connrefused --retry N
   --retry-delay 1 --max-time <T>` the health endpoint (`/v1/health`) until it answers or the bounded
   timeout expires; a timeout is `BOOT_FAILED`.
5. **Observe (live).** Navigate `/dashboard/` via the `playwright` MCP, exercise the control
   (`browser_click` on a button; for inputs read the gotcha below), and **observe a deterministic
   outcome** — a DOM change (`browser_snapshot`), a console signal, or a read-back via `GET /api/state`.
   Record the exact selector and the exact observed outcome. If you cannot observe a stable,
   deterministic outcome, **do not emit a flaky test** → `NO_OBSERVABLE_OUTCOME`.

   **`dbc.Input(type=number)` gotcha — do not generate a broken test.** Playwright's `fill()` does NOT
   propagate into Dash's React-controlled numeric inputs; the callback receives `value=null` (see
   `juniper-canopy/src/tests/ui/test_apply_button_flow.py`, a documented `xfail`). So never author a
   test that fills a numeric input and asserts DOM/State propagation. Assert through a **button
   control** or a **`GET /api/state` read-back** (what the user actually observes) instead.
6. **Author.** Compose a `src/tests/ui/`-shaped test: `@pytest.mark.ui`, a function taking
   `dashboard_page` (and `canopy_url` when it reads back `/api/state`), driving the observed control and
   asserting the observed outcome with a **bounded** wait. Model the docstring + structure on the
   exemplar; keep it to one focused behaviour.
7. **Write for review (never merge).** Write the file to the target repo's
   `src/tests/ui/test_<name>.py` **uncommitted**; refuse to overwrite an existing file (pick a fresh
   name and report). Present the test, state that it is uncommitted, and remind the owner to review, run
   (`pytest -m ui src/tests/ui/test_<name>.py`), and PR it themselves → `TEST_DRAFTED`. **Never** `git
   add` / commit / PR / merge it, and never touch any other file in the target repo.
8. **Teardown (MANDATORY — `finally`-style).** Close the browser (`mcp__playwright__browser_close`),
   then poll-to-down the booted app (SIGTERM→SIGKILL, bounded timeout), orphan-reap, and confirm the
   port is free — exactly as `service-smoke` does. If the app will not die → `TEARDOWN_ESCALATED`.

## Terminal states

- `TEST_DRAFTED` — a focused `@pytest.mark.ui` test was authored from an observed outcome and written
  (uncommitted) to the target repo's `src/tests/ui/` for review; browser + app torn down clean.
- `NO_OBSERVABLE_OUTCOME` — no deterministic outcome could be observed for the control, so **no test was
  emitted** (refusing a flaky artifact is the correct result); the app was torn down.
- `BOOT_FAILED` — the env was missing, the port was occupied, or the bounded wait-for-ready timeout
  expired with no bind.
- `TEARDOWN_ESCALATED` — teardown could not confirm the app down after the SIGTERM→SIGKILL escalation
  and orphan-reap; the surviving pid is reported for manual intervention.

## Teardown (non-negotiable — close the browser AND reap the app)

Identical discipline to the `service-smoke` Skill, in a `finally`-style path: **close the browser
first** (`mcp__playwright__browser_close`), then reap the booted app. SIGTERM is graceful, not instant
(a liveness `curl` right after the kill can still return 200) — **poll-to-down** for connection-refused
with a bounded timeout, then escalate **SIGTERM → SIGKILL**. Match the process argv/port precisely (a
name-based `pgrep` matches its own command line — exclude the checker's own PID). Confirm the port is
free and reuse the parent-PID-safe, Juniper-env-scoped matching in
**`util/reap_pytest_orphans.bash`** (`--dry-run` first); **`util/kill_all_pythons.bash` is the blunt
last resort only** (it `sudo kill -9`s every python on the host). **Never commit `.playwright-mcp/`
artifacts** — the `playwright` MCP writes page snapshots there and it is a tracked dir.

## Manual smoke-verify (owner-run; cannot run in CI)

CI runs only the structural lint (`tests/test_ui_test_author_skill_lint.py`); the live authoring path
needs conda + the app + a browser MCP, which ubuntu CI does not have. Verify locally:

1. Invoke against a clean canopy for a **button** control (e.g. `#reset-button`). Expect: it boots,
   drives the control, observes the outcome, writes a `@pytest.mark.ui` test into
   `juniper-canopy/src/tests/ui/` (uncommitted), and tears down clean (no orphan browser or python).
2. **Run the generated test** in canopy — `pytest -m ui src/tests/ui/test_<name>.py` — and confirm it
   passes (drives a real control, asserts a real outcome).
3. Ask for a **numeric input** control: the Skill must NOT emit a `fill()`-then-assert-DOM test — it
   either asserts via a `/api/state` read-back or reports `NO_OBSERVABLE_OUTCOME`.

## Guardrails

- **Reviewed, never auto-merged.** Write the drafted test **uncommitted**; never `git add` / commit /
  PR / merge it, and never edit any other file in the target repo. The owner reviews, runs, and PRs it.
- **Observe before you author.** Every assertion must come from a real observed outcome — never invent a
  selector, a value, or an outcome. If you cannot observe it, report `NO_OBSERVABLE_OUTCOME`.
- **Model on the real harness.** Reuse the repo's fixtures (`dashboard_page`) and `@pytest.mark.ui`;
  never invent a fixture or a marker.
- **Respect the `dbc.Input(type=number)` wall** — assert via a button or a `/api/state` read-back, never
  a numeric DOM fill.
- **Everything bounded** — every wait is a bounded `--retry` / loop with a `timeout`; never an unbounded
  wait and never a bare foreground `sleep`.
- **Teardown always runs** — browser close + app reap — in a `finally`-style path.
- **No `Agent` delegation.** This Skill does its own observing and authoring.
