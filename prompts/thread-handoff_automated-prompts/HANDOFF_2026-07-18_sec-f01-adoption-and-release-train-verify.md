# HANDOFF 2026-07-18 — SEC-F01 per-service adoption + release-train pin-fix verification + checkout sync

**Origin**: session "ci red: test failures" (juniper-ml), after the `juniper-service-core` 0.5.0 release arc completed.
**Target**: a fresh Claude Code session started in `/home/pcalnon/Development/python/Juniper/juniper-ml`.
**Scope**: Item 0 (bootstrap sync) + two work items, across juniper-ml, juniper-canopy, juniper-recurrence (+ scoped decisions for juniper-cascor, juniper-data).

Every `file:line` below was verified 2026-07-18 (juniper-ml @ `27521e5`; sibling repos at their on-disk mains) and re-probed by independent validator agents. **Re-verify each anchor at current HEAD before editing — treat any drifted anchor as a stop-and-re-ground signal, not something to power through.** Do not invent env vars, flags, paths, or config keys: if a needed signal does not exist, stop and ask the owner.

---

## Completed so far (do NOT redo)

- `juniper-service-core` **0.5.0 is LIVE on PyPI** (wheel + sdist), released via GitHub Release `juniper-service-core-v0.5.0`; notes archived at `notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md` (ml#660).
- 0.5.0's headline: **`enforce_auth_posture(...)`** (SEC-F01 boot-time auth-posture self-check), stdlib-only, exported lazily from the top level (`juniper-service-core/juniper_service_core/__init__.py:45,119-122`). Signature: `enforce_auth_posture(api_keys, *, require_auth, service_name="service", skip_env_var="JUNIPER_SKIP_AUTH_POSTURE_CHECK", logger=None)`; also `auth_is_configured(...)`, `AuthPostureError`. Semantics: real key → INFO; no real key + `require_auth=False` → loud WARNING (running OPEN); no real key + `require_auth=True` → CRITICAL + raise (startup refused). Blank/whitespace keys count as unset.
- juniper-ml `[tools]` pin is `juniper-service-core>=0.2.0,<0.6.0` (`pyproject.toml:57`); recurrence app ceiling already bumped to `<0.6.0` (juniper-recurrence#85, merged).
- The #657 propose-mode pin gap was **already fixed by ml#661** ("propose emits in-repo consumer-pin co-changes", plan §5.4; `util/release_train/propose.py:295` region). Release-train Phases 3.1/3.2 (ml#659/#662) also landed. **Item 2 below is verification only — do not re-implement.**

## Remaining work

### Item 0 — FIRST: sync the juniper-ml primary checkout (bootstrap; 2 minutes)

The primary checkout `/home/pcalnon/Development/python/Juniper/juniper-ml` is parked on the local branch `release/juniper-service-core-v0.5.0` (its remote was deleted on merge; ml#657 merged via a true merge commit, so the branch is fully contained in main). **Until this runs, that checkout shows pre-#661 code — the verification fence below will false-alarm.** After confirming `git -C /home/pcalnon/Development/python/Juniper/juniper-ml status --porcelain` is clean:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git checkout main && git pull --ff-only origin main
git branch -d release/juniper-service-core-v0.5.0   # -d proves merged-ness; refuse = stop and report
```

If the checkout is dirty, or `git checkout main` fails because `main` is held by another worktree, stop and report instead of forcing.

### Item 1 — Per-service SEC-F01 adoption (the substantive item)

Goal per service: depend on `juniper-service-core>=0.5.0` and call `enforce_auth_posture(...)` at startup, before binding, mirroring the E-8 floors-check adoption. One PR per repo, in its own worktree (central `worktrees/` dir, house naming), owner merges — never self-merge.

**`require_auth` wiring (read this first)**: neither canopy nor recurrence has an existing require-auth flag today (verified: canopy `src/settings.py` carries only sub-feature flags like `browser_control_auth_enabled`; recurrence `settings.py` has none). So for this wave: **call with `require_auth=False`** — the loud-WARNING posture, which already closes the silent-open gap by making OPEN visible at boot — and in each PR description propose a `JUNIPER_<SVC>_REQUIRE_AUTH`-style flag (with a suggested per-profile default) as the owner-approved follow-up that flips the posture to CRITICAL-and-refuse. Do not add such a flag without owner approval.

**1a. juniper-canopy (anchored — do first; the pattern repo):**
- Dep: `pyproject.toml:117` currently `"juniper-service-core>=0.4.0"` → raise floor to `>=0.5.0`. Floor bump ⇒ **lockfile regen** (canopy's lockfile-update workflow auto-regenerates on pull_request; verify the freshness gate goes green rather than regenerating by hand first).
- Call site: `src/main.py:234-236` already does `from juniper_service_core import enforce_dependency_floors` + `enforce_dependency_floors(distribution="juniper-canopy", logger=system_logger)`. Add the auth-posture call adjacent, passing canopy's resolved API keys — resolved via `get_secret("CANOPY_API_KEY")` in `src/security.py:265` — with `service_name="juniper-canopy"`.
- Test: mirror `src/tests/regression/test_dependency_floor_boot_check.py` with an auth-posture sibling.
- Gotcha: canopy local verify must match CI path scope (`-m` subsets skip path-run tests; regen layout snapshot only if `get_layout()` changes — it should not here).

**1b. juniper-recurrence (anchored):**
- Dep: `juniper-recurrence/pyproject.toml:43` currently `"juniper-service-core>=0.3.0,<0.6.0"` → raise floor to `>=0.5.0,<0.6.0`. juniper-recurrence has **no lockfile/freshness gate** (verified) — no lockfile action needed.
- Call site: `juniper_recurrence/app.py` — lifespan at `:62`, and `build_api_key_auth(settings.resolve_api_keys())` at `:118` feeding `SecurityMiddleware` (`:123`). Call `enforce_auth_posture(settings.resolve_api_keys(), require_auth=False, service_name="juniper-recurrence")` at startup before binding (see the wiring note above).
- Test: add a boot-check regression test alongside the app's existing test suite.

**1c. juniper-cascor and juniper-data (decision-first — smaller commitment):**
- **Verified: neither repo's `pyproject.toml` depends on `juniper-service-core` today.** Adoption therefore means adding a new runtime dependency (stdlib-only import; light) plus the startup call.
- Verified starting anchors — cascor: app factory `src/api/app.py`, uvicorn entries `src/server.py` / `src/main.py` (packages live directly under `src/`; there is **no** `src/cascor/`). data: app under `juniper_data/api/`; `Settings` with the server-side `api_keys` field at `juniper_data/api/settings.py:93` / `:129`. DISCOVER the exact pre-bind call sites from there.
- Because "new dependency in cascor/data" is an architecture call, present the per-repo plan (call site, key source, `require_auth` wiring, test) to the owner via `AskUserQuestion` or in the PR description **before** merging — or deliver as draft PRs. Do not silently expand scope.

### Item 2 — Verify-and-close the release-train pin co-change fix (ml#661)

- Run: `python3 -m unittest tests.test_release_train_propose -v` (juniper-ml; 47 tests at `27521e5` — must pass at your HEAD).
- Read `util/release_train/propose.py` (the §5.4 `consumer_pin_cochanges` block, `:295` onward) and confirm the co-change set covers all three lockstep artifacts that #657 missed: root `pyproject.toml` extras pin, `tests/test_pyproject_extras.py` exact-string contract, `AGENTS.md` extras-table row — and that cross-repo consumers surface as `propagation_edges` follow-ons (recurrence-class). Origin-session validators already confirmed all of this at `27521e5` (`propose.py:300-302` names the three artifacts; `:305`/`:512` the edges); your job is to re-confirm at your HEAD and close the loop.
- Deliverable: a short verification comment on ml#661 (or the release-train tracker) stating what was confirmed with evidence; open an issue ONLY if a concrete residual gap is found. No code changes expected.

## Key context / gotchas

- **Concurrent sessions are active in this ecosystem** (release-train work shipped 3 PRs in parallel with the origin session). Before opening any PR: `gh pr list` in the target repo as a dup-guard, and re-check `git log origin/main` freshness.
- **juniper-ml main enforces `required_signatures`**: automation commits made with `-c commit.gpgsign=false` leave PRs BLOCKED even when all checks are green (gh auto-merge is disabled repo-wide). Owner merges handle this; do not use `--admin` except for the notes-archive-only exemption class.
- The HO-2 incident class is the *reason* for Item 1: an empty/placeholder secret silently disables `APIKeyAuth` and the service serves open with a healthy health check. `JUNIPER_SKIP_AUTH_POSTURE_CHECK` is the escape hatch — mention it in each adoption PR.
- Never paste local pytest failure output into public places without scrubbing: pytest's failure repr can include `subprocess.run`'s `env` kwarg, with `ANTHROPIC_API_KEY` near the visible front (observed first-hand in the origin session's failure paste).
- juniper-service-core's dependency-free top-level `import juniper_service_core` guarantee must survive (auth_posture is stdlib-only; nothing to do, just don't break it).

## Session verification commands (run AFTER Item 0)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline -3 origin/main        # expect 27521e5 or newer
grep -n "juniper-service-core" pyproject.toml               # expect >=0.2.0,<0.6.0 at [tools]
curl -s https://pypi.org/pypi/juniper-service-core/0.5.0/json | head -c 200   # expect 200 JSON (released)
python3 -m unittest tests.test_release_train_propose -q     # expect OK (47 tests at 27521e5)
grep -n "juniper-service-core" ../juniper-canopy/pyproject.toml ../juniper-recurrence/juniper-recurrence/pyproject.toml
```

If the pin reads `<0.5.0` or the propose suite reports ~34 tests, you are on the parked pre-#661 branch — Item 0 was skipped; do it now.

## Git state at handoff

- juniper-ml: main @ `27521e5` (clean); primary checkout parked as described in Item 0; session worktrees under `.claude/worktrees/` belong to other sessions — leave them.
- juniper-canopy / juniper-cascor / juniper-data: on their mains, no known dirty state (re-verify).
- juniper-recurrence: main @ `0fbb940` (post-#85), clean and synced.

## Acceptance criteria

1. Item 0 done: juniper-ml primary checkout on current main; stale local release branch deleted (or a clean report of why not).
2. canopy + recurrence PRs open (owner-merge), each: floor `>=0.5.0`, one `enforce_auth_posture(..., require_auth=False, ...)` call at the anchored startup site wired to the real resolved keys, the `JUNIPER_<SVC>_REQUIRE_AUTH` follow-up proposed in the PR description, one regression test, repo's full local gate green.
3. cascor + data: a concrete, evidence-backed adoption proposal (or draft PR) each, with the new-dependency decision explicitly surfaced to the owner — no unilateral merge.
4. ml#661 verification comment posted with evidence (tests run + co-change artifact list confirmed).

## Validation record

Drafted and validated 2026-07-18 by the origin session using three independent agents: the suite's `prompt-validator` (RUBRIC R1-R5 + per-claim re-probe against juniper-ml @ `27521e5` and all four sibling repos), an adversarial fact-refuter (51 claims: 46 confirmed, 3 refuted), and a feasibility reviewer (command dry-runs, staleness, convention, safety). All refuted/blocking findings — a phantom `src/cascor/` path, a nonexistent recurrence lockfile gate, a mis-pointed juniper-data config location, bootstrap ordering, and the missing `require_auth` signal in both anchored repos — are corrected in this revision; corrected anchors carry the validators' own probe evidence.
