# Thread Handoff Prompt — 2026-05-31 (obs-demo + canopy diagnosability arc)

Continue Juniper ML cleanup + small-PR work. Previous thread shipped the POC observability remediation §6 follow-up, the `make obs-demo` end-to-end arc, and two canopy UI diagnosability fixes. Stack is at a clean stopping point — 0 open PRs across all 8 repos, 0 stale worktrees in `worktrees/`. Continue with the punch-list below.

## Completed in the prior thread (verify, don't redo)

- juniper-observability 0.3.1 (juniper-ml#337) + cascor#314 + data#158 — inline `MetricsAuthMiddleware` cleanup, all consumers now on `>=0.3.1`.
- juniper-deploy#107 — POC plan §6 doc closure for inline-copy + canopy items.
- juniper-deploy#108–#111 — `make obs-demo` + `prometheus.demo.yml` + demo-seed X-API-Key + METRICS_ENABLED wiring on demo services + canopy↔cascor demo WS Origin allowlist + cascor-demo outbound X-API-Key. Demo profile is now end-to-end functional on a clean checkout.
- juniper-canopy#339 — `Settings.cascor_ws_origin` default switched to `socket.gethostname()`-derived factory.
- juniper-canopy#341 — circuit-open `/api/status` renders "Unreachable" not "Stopped".
- juniper-canopy#344 — Network Info / Network Stats panels surface specific failure label (Rate Limited / Unauthorized / 5xx / Timeout / Unreachable) instead of opaque "Unable to fetch …".
- 47 stale worktrees cleaned from `/home/pcalnon/Development/python/Juniper/worktrees/`.

Memory updates: see `project_obs_demo_arc_complete_2026-05-31.md` + `project_juniper_observability_0_3_1_metrics_auth_cleanup_2026-05-30.md`. The `project_juniper_cascor_worker_file_indirection_gap_2026-05-27.md` note was updated to RESOLVED.

## Remaining work (pick by appetite, each is independent)

From `juniper-canopy/notes/fixes/FIX_FRONTEND_REGRESSIONS_2026-05-30.md`:

- **#1 Tab feedback loop** — clientside callback cycle in `dashboard_manager.py:2270` (Reader B, store→tab) ↔ `:2327` (Writer A, tab→store). Reader needs an equality guard; collapse the two redundant tab-persistence systems into one (delete `:2070` + `:2085`). Behavioral proof needs `dash[testing]`/`pytest-dash` migration — currently blocked on harness work.
- **#2a Rate limiter scope** — canopy's per-IP 60/min limiter shared across dashboard polling causes spurious 429s on `/api/status`, `/api/network/stats`, `/api/set_params`. Design decision needed (Paul): **exempt internal-marker traffic** via `internal_api_headers()` (`security.py:91-223`) OR **re-key by session/API-key**. Larger refactor than today's batches.
- **#3 cascor 0-unit completion** — already shipped in cascor#315 per doc rev v0.3; needs a live `make obs-demo` rerun to verify the candidate-result-collection fix + adaptive timeout actually grow hidden units > 0 end-to-end. If still broken, see doc §5.1 for the dual-defect analysis.
- **#4 Apply-Dataset force-blur** — numeric inputs (`nn-dataset-elements-input`, `nn-dataset-noise-input`) commit `null` to Dash State because Apply-Dataset has no force-blur (Apply-Params got one in PR-2 of the 2026-05-09 effort). Also blocked on `dash[testing]` for the regression test (`memory: project_playwright_dash_react_input_gap`).

Other trigger-conditioned items (no signal yet, leave alone):

- POC §6 hostname-based allowlist in `MetricsAuthMiddleware` — only matters if CIDR turns out insufficient in shared/CNI environments.
- gitleaks Node24 override removal — waiting on upstream v2.3.9 to ship node24 (`memory: project_gitleaks_node24_override_followup`).
- juniper-doc-tools 0.1.1 patch + §5 drift-detection guard rails.
- juniper-ml requirements drift checker `--mode full / --mode rewrite`.
- juniper-deploy#110's `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` override on canopy-demo is now redundant with juniper-canopy#339 (default auto-derives correctly); kept intentionally as belt-and-suspenders.

## Key context

- `juniper-canopy/notes/fixes/FIX_FRONTEND_REGRESSIONS_2026-05-30.md` is the authoritative design doc for the four UI regressions; revisions track what shipped.
- Two pattern-helpers established in this thread that future work should reuse: `DashboardManager._classify_response_failure(response)` / `_classify_exception_failure(exc)` / `_network_info_error_div(panel_label, status_label, detail)` in `src/frontend/dashboard_manager.py` — for any new dashboard panel that polls `/api/*` and needs a diagnosable failure mode.
- The demo profile uses `make obs-demo` (loads `.env.observability` + `PROMETHEUS_CONFIG_FILE=prometheus.demo.yml`); ports: canopy 8050, cascor 8201→8200, data 8100, prometheus 9090, grafana 3001 (host).
- Worktree V2 procedure: all worktrees in `/home/pcalnon/Development/python/Juniper/worktrees/<repo>--<branch>--<timestamp>--<sha>`; cleanup needs two gates (Paul says "PR merged" AND `gh pr view` confirms `state=MERGED`).
- Two-gate squash-merge lesson: GitHub default squash carries first commit's diff only — multi-commit cleanup PRs lose follow-ups. Single-commit or force-push to a single commit before merge.

## Verification commands for the fresh thread

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cosmic-booping-scott
# Verify clean state
gh pr list --repo pcalnon/juniper-canopy --state open --json number  # expect []
gh pr list --repo pcalnon/juniper-deploy --state open --json number  # expect []
ls /home/pcalnon/Development/python/Juniper/worktrees/               # expect only `logs/`

# Verify recent merges landed
cd /home/pcalnon/Development/python/Juniper/juniper-canopy && git log --oneline -5
# expect: a0c24ed (#344), 8237714 (#342), ...

# Optional: run obs-demo end-to-end (rebuilds image since #344 merged)
cd /home/pcalnon/Development/python/Juniper/juniper-deploy && make obs-demo
curl -sf http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets[] | {service: .labels.service, health}'
# expect: 4 targets all `up`
```

## Branch / staging

Current branch: `main` on all repos, fully up-to-date with origin/main.
No uncommitted changes.
Session worktree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cosmic-booping-scott/` (Claude-managed; stays alive across handoff).

End of handoff prompt.
