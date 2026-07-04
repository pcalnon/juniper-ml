# Thread Handoff — Stack Regression E.2 + E.3 (WS Origin Cascade)

**Date**: 2026-05-28
**Reason for handoff**: Context utilization > 80% after shipping E.0 + E.1; further work would force compaction.
**Triggering session**: Claude Opus 4.7 1M-context, worktree `juniper-ml/.claude/worktrees/quiet-roaming-parnas`.

---

## Goal

Continue the **Juniper Stack Regression Cascade** by shipping **E.2** (WebSocket `/ws/control` Origin support, four-repo coordination) and **E.3** (juniper-ml `[clients]` extra bump) — the remaining two phases of a four-phase plan that resolves the 2026-05-27 docker-compose-stack regression set.

---

## Completed in the Previous Thread

**E.0 — `juniper-deploy` PR #101** (https://github.com/pcalnon/juniper-deploy/pull/101)

- Awaiting merge.
- Changes the top-level `secrets:` block defaults in `docker-compose.yml` so the five auth-path secrets (`juniper_data_api_keys`, `juniper_cascor_api_key`, `juniper_cascor_api_keys`, `canopy_api_key`, `cascor_auth_token`) point at `./secrets/<name>.txt` instead of `./secrets.example/<name>.txt`. Closes the 2026-05-27 asymmetric-mount class of regression where canopy and cascor disagreed on `juniper_cascor_api_keys` content and every canopy → cascor `/v1/*` HTTP call returned 401.
- Adds `notes/SECRET_MOUNT_SYMMETRY_2026-05-28.md` (rationale + operator path) and `tests/test_compose_secret_mount_symmetry.py` (three static guards). 47/47 deploy static tests pass.

**E.1 — `juniper-canopy` PR #327** (https://github.com/pcalnon/juniper-canopy/pull/327)

- Awaiting merge.
- Strips the `/v1` prefix from **16 callsites** in `src/backend/cascor_service_adapter.py` (8 `_request` + 8 `_post`/`_patch`/`_delete` wrappers). The cascor-client's `_request` already prepends `/v1` via `self.api_url`, so passing `/v1/...` produces `/v1/v1/...` on the wire → 401/404.
- Updates 17 existing test assertions that baked the buggy paths.
- Adds `src/tests/unit/backend/test_cascor_service_adapter_v1_prefix_regression.py` — AST-level walker over every `.py` under `src/backend/` that asserts no cascor-client call (`_request`/`_get`/`_post`/`_put`/`_patch`/`_delete`) passes a `/v1/...`-prefixed path argument. Handles bare strings and `f"..."` literals.
- 398/398 backend unit tests pass; 912/912 non-UI integration tests pass; all pre-commit hooks pass.

**Analysis + plan docs** (all already committed on this worktree's branch `worktree-quiet-roaming-parnas` and available at `juniper-ml/notes/`):

- `STACK_REGRESSION_ANALYSIS_2026-05-27.md` — original investigation.
- `STACK_REGRESSION_REMEDIATION_PLAN_2026-05-27.md` — original A/B/C plan.
- `STACK_REGRESSION_CORRECTIONS_2026-05-27.md` — independent-validator corrections (E.0–E.3 framing lives here; **read this first**).

---

## Remaining Work

### E.2 — WebSocket Origin Support (four-repo cascade)

Symptom: `juniper-cascor` logs `Control WS: no Origin header — rejecting (fail-closed)` every 30 s; `WebSocket /ws/control 403`; canopy's `cascor_service_adapter` loops endlessly reconnecting. The fail-closed Origin policy was introduced in `juniper-cascor` PR #129 (`feat(ws): control-path security — origin validation, rate limiting, cooldown (P8)`, commit `daacb6d`, 2026-04-13). Canopy's WS client (`juniper-cascor-client/juniper_cascor_client/ws_client.py:316`) calls `websockets.connect(url, additional_headers=…)` with no `origin=` kwarg — the Python `websockets` library does not auto-emit Origin for non-browser callers, so the upgrade is rejected.

**Important correction from the previous thread**: the cascor `Settings.ws_control_allowed_origins` field **already responds to the env var** `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS` via the `Settings` class's `env_prefix="JUNIPER_CASCOR_"`. Live-confirmed by setting the env var inside the running cascor container. So PR-2 in this cascade is *not* "introduce an env hook" — it is "add a CSV-shape parser via `AliasChoices` + document the existing env binding".

#### PR-2-A — `juniper-cascor-client`

Repo: `/home/pcalnon/Development/python/Juniper/juniper-cascor-client`
Branch: `feat/ws-control-stream-origin-param-2026-05-28`
Worktree dir name pattern: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor-client--feat--ws-control-stream-origin-param-2026-05-28--<YYYYMMDD-HHMM>--<short-hash>`.

Changes:

- `juniper_cascor_client/ws_client.py`: add `origin: Optional[str] = None` to both `CascorControlStream.__init__` (around line 294-303) and `CascorTrainingStream.__init__` (the second `websockets.connect` call site around line 124). Forward to `websockets.connect(url, additional_headers=…, origin=self.origin)` only when not `None` (existing behavior preserved when caller does not pass `origin=`).
- Tests in `tests/`:
  - `test_connect_sends_origin_when_set`: mock `websockets.connect`, capture kwargs, assert `origin="http://juniper-canopy:8050"` is forwarded.
  - `test_connect_omits_origin_when_unset`: mock confirms no `origin=` kwarg → preserves M2M default.

Release: bump `juniper-cascor-client` version (currently 0.4.x) to `0.5.0`. The published package on PyPI is gated by trusted-publishing on tag push; consult `juniper-cascor-client/.github/workflows/publish.yml` for the exact trigger.

#### PR-2-B — `juniper-cascor`

Repo: `/home/pcalnon/Development/python/Juniper/juniper-cascor`
Branch: `feat/ws-control-allowed-origins-csv-parser-2026-05-28`

Changes:

- `src/api/settings.py` around line 291-296: leave the default list, but add an `_parse_allowed_origins` field validator (mirroring the existing `_parse_api_keys` at line 215-228) that accepts comma-CSV form. Add `validation_alias=AliasChoices("ws_control_allowed_origins", "JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS")` for parity with the existing `juniper_data_url` field (line 258-262). The env_prefix-derived path already works; the alias is for explicitness.
- Tests in `src/tests/unit/api/`:
  - `test_control_security.py::test_origin_allowlist_env_override`: set `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://x:1,http://y:2`; assert loaded `Settings().ws_control_allowed_origins == ["http://x:1", "http://y:2"]`.
- Document the env var in `docs/REFERENCE.md` (existing pattern shows other env vars there).

No image rebuild required for the *previous thread*'s already-merged work — but the running cascor image will need to pick up this PR for the canopy fix to take effect.

#### PR-2-C — `juniper-canopy`

Repo: `/home/pcalnon/Development/python/Juniper/juniper-canopy`
Branch: `feat/cascor-ws-origin-2026-05-28`

Changes:

- Add a `cascor_ws_origin: str = "http://juniper-canopy:8050"` field with env alias `JUNIPER_CANOPY_CASCOR_WS_ORIGIN` to canopy's Settings (path TBD — search for the canopy `Settings` class that already holds `cascor_service_url`; likely `src/config/settings.py` or similar, but verify the actual path since the previous thread's `from juniper_canopy.config.settings import get_settings` failed at runtime).
- `src/backend/cascor_service_adapter.py:227-252`: extend `CascorServiceAdapter.__init__` to accept and forward `ws_origin: Optional[str] = None`. Update the `ControlStreamSupervisor` construction at line 252 to pass `origin=ws_origin`.
- `src/backend/cascor_service_adapter.py:126-130`: pass `origin=` through to the `CascorControlStream` constructor.
- Update `pyproject.toml`: pin `juniper-cascor-client>=0.5.0` (the release from PR-2-A).
- Tests in `src/tests/unit/backend/`:
  - `test_cascor_service_adapter.py::test_supervisor_passes_origin_to_stream`: construct adapter with `ws_origin="http://juniper-canopy:8050"`, mock `CascorControlStream`, assert `origin=…` is forwarded.

#### PR-2-D — `juniper-deploy`

Repo: `/home/pcalnon/Development/python/Juniper/juniper-deploy`
Branch: `feat/ws-control-origin-env-2026-05-28`

Changes:

- `docker-compose.yml`: add `JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS=http://juniper-canopy:8050,http://localhost:8050,http://127.0.0.1:8050` to the juniper-cascor service env block. Add `JUNIPER_CANOPY_CASCOR_WS_ORIGIN=http://juniper-canopy:8050` to the juniper-canopy service env block.
- Tests: extend `tests/test_compose_security_config.py` (or sibling) to assert the two env vars are present and correctly shaped.

### E.3 — juniper-ml `[clients]` extra bump

Repo: `/home/pcalnon/Development/python/Juniper/juniper-ml` (or this same Claude-managed worktree if still active)
Branch: `chore/bump-cascor-client-0.5.0-2026-05-28`

Changes:

- `pyproject.toml` `[project.optional-dependencies]` → `clients`: update `juniper-cascor-client>=0.4.0` to `juniper-cascor-client>=0.5.0`. Tests in `tests/test_pyproject_extras.py` will need to assert the new pin if a CHANGELOG-style table is added there.

---

## Ordering Hazards

- **PR-2-A (cascor-client) must release to PyPI before PR-2-C (canopy) merges**, otherwise downstream installers pulling the canopy image will get the old client and the `origin=` kwarg call will `TypeError`. Mitigation in PR-2-C: pin `juniper-cascor-client>=0.5.0` in the same commit that introduces the `origin=` thread-through.
- **The running cascor image must be rebuilt** for the running stack to pick up the env-binding (PR-2-B's `AliasChoices`). `docker compose build juniper-cascor` after E.0 + PR-2-B merge.
- **Stale `juniper_cascor_client` install in JuniperCascor1 conda env** can mask test failures locally. If running canopy tests on the host: `pip install --force-reinstall --no-deps juniper-cascor-client` against the local worktree of the new client before running canopy tests.

---

## Verification (post-merge of all four E.2 PRs + E.3)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-deploy
docker compose down
bash scripts/prepare_secrets.bash
docker compose build --parallel juniper-canopy juniper-cascor
docker compose up -d

# Within 30 s the canopy supervisor connects:
docker logs juniper-canopy 2>&1 | grep "Control stream supervisor connected"

# And cascor stops fail-closing on Origin:
docker logs juniper-cascor 2>&1 | grep "no Origin header"   # should be empty

# And canopy → cascor /v1/* HTTP calls authenticate cleanly:
docker logs juniper-cascor 2>&1 | grep "401 Unauthorized" | grep "172.20.0"   # should be empty after E.0 + E.1

# Browser open: http://localhost:8050 → Dataset View → Save / Generate / Launch → all complete without error
```

---

## Key Files & References

- `juniper-cascor-client/juniper_cascor_client/ws_client.py:124, 309-326` — WS connect points
- `juniper-cascor/src/api/websocket/control_security.py:30` — fail-closed log
- `juniper-cascor/src/api/settings.py:108-121, 291-297` — Settings + allowlist
- `juniper-canopy/src/backend/cascor_service_adapter.py:121-152, 227-252` — supervisor reconnect loop + adapter init
- `juniper-deploy/docker-compose.yml:147-208, 364-412` — cascor + canopy service env blocks
- `juniper-ml/notes/STACK_REGRESSION_CORRECTIONS_2026-05-27.md` — corrected E.0–E.3 framing (read first)
- `juniper-ml/notes/STACK_REGRESSION_ANALYSIS_2026-05-27.md` — original analysis (now partly superseded; see corrections doc)

---

## Git State at Handoff

- `juniper-ml` branch: `worktree-quiet-roaming-parnas` (Claude-managed local worktree at `.claude/worktrees/quiet-roaming-parnas`); has the three analysis/plan/corrections docs committed but unpushed.
- `juniper-deploy` branch: `fix/align-secret-mount-defaults-2026-05-28` (pushed; PR #101 open).
- `juniper-canopy` branch: `fix/cascor-adapter-v1-prefix-callsites-2026-05-28` (pushed; PR #327 open).
- `juniper-cascor-client`, `juniper-cascor`: clean on `main` (no new branches yet — start with the worktree-setup procedure in juniper-ml's CLAUDE.md).

---

## Recommended Approach

Spawn parallel sub-agents to scaffold each PR-2-* in its own worktree (E.2 is genuinely parallel work across the four repos). Sync on the cascor-client release timing — that is the only hard dependency. Then ship E.3 as a one-line bump once cascor-client 0.5.0 is on PyPI.

After all merge, perform the worktree-cleanup-v2 procedure per `juniper-ml/notes/WORKTREE_CLEANUP_PROCEDURE_V2.md` for each branch.

Total estimated wall time for E.2 + E.3: 60–90 min plus PyPI publish delay (5 min trusted-publishing).
