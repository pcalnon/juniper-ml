# Juniper Stack Regression — Corrections + Updated Plan — 2026-05-27

**Author**: Paul Calnon (with Claude Opus 4.7 + independent validator sub-agent)
**Date**: 2026-05-27
**Supersedes (in part)**: [`JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-ANALYSIS.md`](JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-ANALYSIS.md) §1, §3.5, §5, §7; [`JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-REMEDIATION-PLAN.md`](JUNIPER_2026-05-27_JUNIPER-ECOSYSTEM_STACK-REGRESSION-REMEDIATION-PLAN.md) §0, §1.1 (PR-2 scoping), §1.4, §3.

A second sub-agent reviewed the original analysis + plan independently, and several material errors surfaced. Live-state probes between the original report and the review showed the running stack also changed (a container restart at 22:57 UTC re-mounted cascor's `juniper_cascor_api_keys` from a populated 43-byte token, while canopy still mounts the 33-byte JSON-list placeholder). This addendum is the corrected source of truth; the original docs are kept for traceability of how the picture changed.

---

## A. Corrected Picture (One Paragraph)

The stack is currently failing because **canopy and cascor mount two different files for the same logical secret** (canopy: `secrets.example/juniper_cascor_api_keys.txt` = `["CHANGE_BEFORE_PRODUCTION_USE"]` 33 B; cascor: `secrets/juniper_cascor_api_keys.txt` = `MwxXf-rq6WF3oxiXfTqSAHpdqT4SlcQoD3Cxsk7xq-k` 43 B). Cascor's `Settings._parse_api_keys` loads the populated 43-byte token; canopy sends the placeholder; **every** canopy → cascor `/v1/*` HTTP call returns `401 Invalid API key`. Cascor's `/ws/control` is *also* broken (Origin fail-closed; canopy's client doesn't send Origin), but the WS-supervisor cascade is **not** the cause of Dataset View Save / Generate / Launch failures — those buttons use HTTP, not WS, so the auth mismatch fully explains them. The double-`/v1/v1` URL bug is real and bigger than reported (8 callsites in `cascor_service_adapter.py`, not 1).

---

## B. Confirmed Facts (Live Probe Evidence)

| # | Probe | Result |
|---|---|---|
| B-1 | `docker exec juniper-cascor python -c "from api.settings import Settings; print(Settings().api_keys)"` | `['MwxXf-rq6WF3oxiXfTqSAHpdqT4SlcQoD3Cxsk7xq-k']` |
| B-2 | `docker exec juniper-cascor cat /run/secrets/juniper_cascor_api_keys` | `MwxXf-rq6WF3oxiXfTqSAHpdqT4SlcQoD3Cxsk7xq-k` (43 B, modified 22:57) |
| B-3 | `docker exec juniper-canopy cat /run/secrets/juniper_cascor_api_keys` | `["CHANGE_BEFORE_PRODUCTION_USE"]` (33 B, modified 19:25) |
| B-4 | `docker logs juniper-cascor 2>&1 \| grep "401 Unauthorized" \| tail` | continuous stream of `172.20.0.4 (canopy) - "GET /v1/training/status" 401` |
| B-5 | `docker exec -e JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS='[…]' juniper-cascor python -c "..."` | `Settings().ws_control_allowed_origins` reflects the env value → **env hook already exists** via `env_prefix="JUNIPER_CASCOR_"` |
| B-6 | `grep -nE '_request("(GET\|POST\|PUT\|DELETE)", "/v1/' cascor_service_adapter.py` | **8 lines**: 899, 908, 917, 950, 969, 1017, 1033, 1069 |
| B-7 | Container start times | canopy: 22:52:55Z, cascor: 22:57:54Z (5-minute gap; cascor restarted independently and picked up the populated secret while canopy retained the example) |

---

## C. Errors in the Original Documents

| # | Original claim | Correction |
|---|---|---|
| **E-1** | "RC-3 secrets asymmetry is **latent**; HTTP auth works by coincidence" | **WRONG (now)**. RC-3 became *active* at 22:57 UTC when cascor restarted with the populated 43 B token while canopy retained the 33 B JSON-list placeholder. Every canopy → cascor /v1/* call is currently 401. RC-3 is the **primary** root cause, not a deferred footnote. |
| **E-2** | "RC-2 double-`/v1` bug is a single line at adapter.py:1069" | **UNDERSCOPED**. There are 8 callsites in `cascor_service_adapter.py` that pass `/v1/...` to `_request()`, all of which produce `/v1/v1/...` on the wire. The full set: lines 899, 908, 917, 950, 969, 1017, 1033, 1069 — covering `stage_dataset`, `cancel_pending_dataset`, `get_pending_dataset`, `get_experimental_functions`, `set_experimental_functions`, `swap_dataset_live`, `cancel_swap_dataset_live`, `get_dataset_swap_events`. |
| **E-3** | "cascor `ws_control_allowed_origins` has no env-var hook" | **WRONG**. `Settings` declares `model_config = SettingsConfigDict(env_prefix="JUNIPER_CASCOR_")`, so pydantic-settings *already* binds `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS`. Live-confirmed via the B-5 probe above. PR-2 is reframed from "introduce env hook" to "add CSV-shape parser via `AliasChoices` + document the existing env binding". |
| **E-4** | "Save / Generate / Launch buttons fail because the supervisor is down → cascade from RC-1" | **WRONG**. Verified callsite chain: `start_training_background` (line 583) calls `self._client.start_training(**kwargs)` (HTTP, not WS). `stage_dataset` (line 895), `swap_dataset_live` (line 1015), `cancel_pending_dataset`, experimental functions — all use `self._client._request(...)` (HTTP). Even `set_params` (line 781-805) **falls back to REST** when the WS attempt fails. The cascade table in the analysis doc §7 attributes those button failures to the wrong root cause; they fail because of **RC-3** (auth mismatch) **plus** **RC-2** (8 `/v1/v1` paths). |
| **E-5** | Cascade explanation: "status error" is the dashboard reacting to supervisor disconnect | **PARTIALLY WRONG**. The "status error" displayed by the dashboard is the consequence of `get_training_status()` (HTTP /v1/training/status) returning **401**, not of the supervisor being disconnected. The supervisor disconnect causes the *live FSM badge* to be stale (no event push), but the "status: error" state is a result of HTTP 401 swallowing into an exception → empty status payload → UI fallback to error display. |
| **E-6** | "juniper-ml `[clients]` extra bump not explicitly listed in PR-1's release plan" | Add it. Without bumping `juniper-cascor-client>=0.5.0` in juniper-ml's `pyproject.toml`, downstream `pip install juniper-ml[clients]` pulls the old client that lacks `origin=`. |
| **E-7** | "Tests should assert 404 on `/v1/v1/...`" | Tests should accept any of `{401, 403, 404}` because SecurityMiddleware 401 fires *before* router 404. Today, every `/v1/v1/...` request returns 401 (auth gate) rather than 404 (router miss). |

---

## D. Revised Root-Cause Priority

| Priority | Root cause | Fix repo(s) | User-visible effect when fixed |
|---|---|---|---|
| **P0** | **RC-3**: Asymmetric secret mounts — canopy and cascor disagree on `juniper_cascor_api_keys` content. | `juniper-deploy` (config-only, no rebuild required) | Save / Generate / Launch buttons start working (or surface RC-2 as the next blocker). Dashboard status badge stops showing "error". |
| **P0** | **RC-2 (expanded)**: 8 callsites in `cascor_service_adapter.py` pass `/v1/...` paths to `_request()` whose client already prepends `/v1`. | `juniper-canopy` | Save, dataset swap, experimental-toggle, dataset-swap-event timeline all stop 404-ing. |
| **P1** | **RC-1**: Cascor `/ws/control` fail-closed against missing Origin; canopy's WS client doesn't set one. | `juniper-cascor-client` + `juniper-canopy` + `juniper-deploy` (env-driven allowlist on cascor *already exists* via `env_prefix`) | WS supervisor reconnects; live FSM badge updates in realtime instead of polling. |
| **P2** | Long-tail: deploy-side secret-symmetry assertion, `make prepare-secrets` completeness, canopy healthcheck depth (supervisor `is_connected`), document `_request` path-prefix contract. | `juniper-deploy`, `juniper-canopy`, `juniper-cascor-client` (docstrings) | Future-proofing; no immediate user-visible effect. |

---

## E. Updated Implementation Plan

The four-PR cascade from the original plan still holds in shape, but the **content and ordering** change. Detailed:

### E.0 P0a — `juniper-deploy`: align `juniper_cascor_api_keys` mount (ship FIRST, config-only, no rebuild)

**Smallest-viable fix that unblocks the user immediately**. Two options, both `juniper-deploy`-only:

- **Option α (recommended)**: Make canopy mount the same populated 43 B token cascor has. Either (i) replace `secrets/juniper_cascor_api_keys.txt` content into canopy's mount source, or (ii) override canopy's `secrets:` block in `docker-compose.override.yml` to point at `secrets/juniper_cascor_api_keys.txt`. Then `docker compose up -d juniper-canopy`. *No code rebuild required.* Verifies in <60s.
- **Option β**: Zero out `secrets/juniper_cascor_api_keys.txt` on cascor's side (which post-cascor#311 → "auth disabled" → 200 on all calls). Lower-security; rules out auth as a future protection. Only use if Paul explicitly wants the dev stack to be authn-off.

**Acceptance**: `docker logs juniper-cascor 2>&1 | grep "401" | grep "172.20.0.4 (canopy)"` returns nothing for 60s after the fix.

### E.1 P0b — `juniper-canopy`: fix all 8 `/v1/v1` callsites

Diff scope: 8 lines in `src/backend/cascor_service_adapter.py`. Strip `/v1` prefix from each path. Add the reflective AST test from the original plan §2.2 (`test_no_callsite_passes_v1_prefix`) — but assert against **all 8** sites + every other caller in that file. Update test to accept `{401, 403, 404}` from cascor in any contract test that triggers the wrong path.

**Acceptance**: `docker logs juniper-cascor 2>&1 | grep "/v1/v1"` returns nothing post-deploy; AST test fails the build if any new `/v1/...` literal sneaks into `_request()` args.

### E.2 P1 — `juniper-cascor-client` + `juniper-canopy`: WS Origin support

Same shape as the original plan (Approach A), but the cascor-side change is *reduced*:

- `juniper-cascor`'s `Settings.ws_control_allowed_origins` already responds to the env var. The PR-2 in the original plan is reduced to (i) accept comma-CSV via `_parse_allowed_origins` validator (mirroring `_parse_api_keys`), (ii) add `AliasChoices` for clarity, (iii) document the env var in `docs/REFERENCE.md`. No new env-binding code.
- `juniper-cascor-client`'s `CascorControlStream` gains `origin=` (still required; this is the actual missing piece).
- `juniper-canopy` exposes a `cascor_ws_origin` Settings field and threads it through `ControlStreamSupervisor`.
- `juniper-deploy` sets `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://juniper-canopy:8050,http://localhost:8050,http://127.0.0.1:8050` and `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://juniper-canopy:8050`.

**Acceptance**: `docker logs juniper-canopy 2>&1 | grep "Control stream supervisor connected"` shows the success line within 30s; `docker logs juniper-cascor 2>&1 | grep "no Origin header"` returns nothing after the fix lands.

### E.3 P1.5 — juniper-ml meta-package bump

`juniper-ml/pyproject.toml` `[clients]` extra: pin `juniper-cascor-client>=0.5.0` (the release-cut from E.2). Otherwise downstream installers still pull the old client.

### E.4 P2 — long-tail follow-ups (deferred but tracked)

1. `juniper-deploy/tests/integration/test_compose_secrets_symmetry.sh` — assert every container's `/run/secrets/<X>` file matches the corresponding file in every other container that mounts the same secret name. Would have caught E-1 at PR-merge time.
2. `make prepare-secrets` completeness — touch *all* compose-referenced secret files, not a strict subset. Carries over from memory `project_make_prepare_secrets_incomplete_2026-05-10`.
3. Canopy healthcheck depth — `/v1/health` includes a `supervisor.is_connected` field; healthcheck command flips unhealthy after >60s of supervisor disconnect.
4. Document `_request` path-prefix contract in `juniper-cascor-client/juniper_cascor_client/client.py` — paths MUST NOT include `/v1` because `api_url` already includes it.

---

## F. Refreshed Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| E.0 Option α gets reverted by the next `git pull` / `make prepare-secrets` run | High | High (re-introduces the asymmetry) | E.4 #2 — make `make prepare-secrets` populate ALL secrets uniformly. Until then, document the `--env-file` invocation in `juniper-deploy/docs/LOCAL_STACK_QUICK_START.md`. |
| Cascor container rebuilt against stale juniper-cascor-client (no `origin=`) → AttributeError at runtime | Medium | High | Bump `juniper-cascor-client` to a release tag *before* canopy's PR-3 merges; pin in canopy's `pyproject.toml` in the same PR. |
| E.0 Option β chosen (auth disabled) and then a future PR enables auth by default → repeat regression | Low | Medium | Add E.4 #1 + a canary curl in the deploy integration test that asserts canopy → cascor /v1/* returns 200 with the chosen secret shape. |
| Hidden 9th-or-Nth `/v1/v1` callsite outside `cascor_service_adapter.py` | Low-Medium | Low | Expand the AST test to walk `src/juniper_canopy/**/*.py`, not just adapter file. |
| `MwxXf-…` token is a one-off rotation; next rotation produces yet another value | High | None (post-RC-3 fix) | E.4 #2 — `make prepare-secrets` produces canopy + cascor symmetrically. |

---

## G. Recommended Next Step (for Paul to approve)

I have not yet started any code changes. Two parallel paths from here:

1. **Fastest user-visible relief** (single PR, ~10 minutes): ship **E.0 P0a Option α** as a stand-alone `juniper-deploy` PR. Edit `secrets/juniper_cascor_api_keys.txt` so canopy and cascor mount byte-identical content, `docker compose up -d juniper-canopy`, verify the 401 stream stops. This *probably* re-enables Save / Generate / Launch on its own (after the WS reconnect noise quiets) **but** leaves the 8 `/v1/v1` 404s in place, which will surface as the next blocker (specifically `stage_dataset` will still 404).
2. **Single coherent fix** (four PRs, half a day): ship E.0 → E.1 → E.2 → E.3 in order. Comprehensive, but the user is blocked for the duration.

Recommended: **ship #1 first** (proves RC-3 is the active blocker; gives Paul a working dashboard within minutes), **then immediately ship #2 (E.1 in particular)** which covers the 8-callsite scope. E.2 and E.3 can follow as their own PR cluster the next day.

---

## H. Lessons / Process Notes

- **State drift mid-investigation matters.** The stack restart at 22:57 UTC invalidated my §3 evidence (which had reported cascor's loaded `api_keys = ['["CHANGE_BEFORE_PRODUCTION_USE"]']`). Future investigations should re-probe the live state after any docker-compose action, and any analysis doc should pin its evidence to specific container start times.
- **Validators that re-derive the truth from source are essential.** The independent reviewer caught the cascade misframe (E-4), the env-binding miss (E-3), and the active-vs-latent classification error (E-1) by reading the same files but reasoning forward from the routing/middleware order. The cost of a 100-token validator agent was 5× the cost of shipping the original plan and re-discovering the issues post-merge.
- **Reflective AST tests beat per-line edits for "ban this pattern" rules.** The original plan had one such test (the `/v1/...` prefix detector); we should adopt the pattern more aggressively in this codebase.
- **Container restarts in monitoring scripts during user-led investigations are a gotcha.** Consider adding a sentinel `docker-compose down --remove-orphans` step at the top of any future stack-regression playbook to lock the state before investigating.
