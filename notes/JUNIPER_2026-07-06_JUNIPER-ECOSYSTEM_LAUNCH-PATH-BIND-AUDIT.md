# Juniper Stack — Launch-Path Bind Audit (SEC-F22 Completeness)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.6.0
**Last Updated**: 2026-07-06

---

## 1. Purpose

The two-flag bind-attestation guard (SEC-F22 / SEC-F19; shipped in cascor #393,
deploy #148, canopy #432) refuses a non-loopback application bind unless the
operator attests to it. The guard reads the **bind host from settings** —
`settings.server.host` (canopy) / `settings.host` (cascor) — and evaluates
whether that value is loopback.

This audit answers a single completeness question: **does every way the two
guarded services can be launched actually route the bind host through the
setting the guard inspects?** A launcher that hands `--host 0.0.0.0` to
`uvicorn` on the command line binds all interfaces *without the setting ever
being consulted* — the guard still runs (it is in the app lifespan), but it
evaluates the settings default (now `127.0.0.1`), returns "loopback, safe", and
passes **while the socket is actually bound to `0.0.0.0`**. The guard is not
skipped; it is evaluating the wrong value. That is the bypass class this audit
enumerates.

This is the launch-path companion to
[`JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md`](JUNIPER_2026-07-02_JUNIPER-ECOSYSTEM_STACK-SECURITY-AUDIT-PLAN.md)
and the design-of-record
[`JUNIPER_2026-07-03_JUNIPER-CANOPY_CONTROL-SURFACE-AUTH-AND-NAT-DESIGN.md`](JUNIPER_2026-07-03_JUNIPER-CANOPY_CONTROL-SURFACE-AUTH-AND-NAT-DESIGN.md).
Finding IDs continue the `SEC-F` series (F01–F22 defined in the security plan).

## 2. Method

For each guarded service (canopy, cascor), every launch path was enumerated from
`origin/main` and classified by **how the bind host reaches uvicorn**:

- **SAFE (settings-driven)** — the launcher invokes the app entrypoint
  (`python src/main.py` / `python src/server.py`), which calls
  `uvicorn.run(host=<settings value>)`. uvicorn binds exactly the value the
  guard inspects, so the guard's verdict matches the real socket. The guard is
  authoritative on this path.
- **BYPASS (CLI `--host`)** — the launcher runs `uvicorn <app> --host 0.0.0.0`.
  uvicorn binds `0.0.0.0`; the guard independently reads the settings default
  and passes. The guard's verdict does not match the real socket.

Launch paths surveyed: container `CMD` (root + `conf/`), the on-host
`util/juniper_plant_all.bash` orchestrator, per-repo `systemd` units, and demo
launchers. Evidence is `file:line` on `origin/main` as of 2026-07-06.

## 3. Findings summary

| ID      | Path                                                                      | Repo           | Class                       | Severity   |
|---------|---------------------------------------------------------------------------|----------------|-----------------------------|------------|
| SEC-F23 | `scripts/juniper-canopy.service:30` (systemd `ExecStart`)                 | juniper-canopy | BYPASS                      | Medium     |
| SEC-F24 | `util/juniper_canopy-demo.bash:270` (demo launcher)                       | juniper-canopy | BYPASS                      | Low–Medium |
| SEC-F25 | `conf/Dockerfile:81` (alt image `CMD`, not deploy-built)                  | juniper-canopy | BYPASS (latent)             | Low        |
| SEC-F26 | `util/juniper_canopy-demo.bash:160` (stray canopy-demo copy)              | juniper-cascor | BYPASS (latent) + hygiene   | Low        |
| SEC-F27 | `src/api/app.py:100` (docstring documents `--host 0.0.0.0`)               | juniper-cascor | Doc anti-pattern            | Info       |
| SEC-F28 | `util/juniper_plant_all.bash:102` (`JUNIPER_DATA_HOST` default `0.0.0.0`) | juniper-ml     | Posture (unguarded service) | Info       |

All confirmed bypasses are **canopy-side stragglers**. cascor's launch paths are
uniformly settings-driven (see §5). Severity ranking, highest first: SEC-F23
(on-host production path) > SEC-F24 (demo) > SEC-F28 ≈ SEC-F26 ≈ SEC-F25 >
SEC-F27.

## 4. Findings detail

### SEC-F23 — canopy systemd unit binds `0.0.0.0`, guard blind (Medium)

`scripts/juniper-canopy.service:30`:

```ini
ExecStart=/opt/miniforge3/envs/JuniperCanopy/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8050
```

This is a real on-host production launch path (installed via `systemctl`). It
binds all interfaces while the guard, reading `settings.server.host`
(`127.0.0.1` default), passes silently. This is the exact footgun SEC-F22 was
built to prevent, defeated on the systemd path. It is the highest-severity
finding because it is a production launcher, and because it is **asymmetric**:
cascor's equivalent unit (`scripts/juniper-cascor.service:30`) is
`ExecStart=... python server.py` — settings-driven and safe.

**Fix.** Change `ExecStart` to run the settings-driven entrypoint and drop the
CLI host:

```ini
ExecStart=/opt/miniforge3/envs/JuniperCanopy/bin/python src/main.py
```

If on-host exposure to other interfaces is genuinely intended, express it
through the guarded setting plus the attestation flag so the guard evaluates the
real bind host in-band, e.g.:

```ini
Environment=JUNIPER_CANOPY_SERVER__HOST=0.0.0.0
Environment=JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true
```

**Behavior implication (owner decision).** Today this unit binds `0.0.0.0` by
default. The fix makes it bind `127.0.0.1` by default (matching the container
and `plant_all` paths), requiring explicit attestation to expose. Any operator
relying on the current on-host systemd unit to be reachable off-loopback would
need to set the two `Environment=` lines above. This is the intended posture
change, but it changes on-host reachability and should be signed off before
merge.

### SEC-F24 — canopy demo launcher binds `0.0.0.0`, guard blind (Low–Medium)

`util/juniper_canopy-demo.bash:270`:

```bash
exec "$CONDA_PREFIX/bin/uvicorn" main:app --host 0.0.0.0 --port 8050 --log-level info
```

The demo legitimately wants to be reachable, but `--host` bypasses the guard
entirely — no attestation trail, no warning. The script exports
`JUNIPER_DATA_URL` but never `JUNIPER_CANOPY_SERVER__HOST`, so the setting stays
at its loopback default and the guard is blind.

**Fix.** Keep the `0.0.0.0` bind but express it through the setting + attestation
so the guard sees it and warns/attests in-band (consistent with the
"demo may stay warning-only" decision):

```bash
export JUNIPER_CANOPY_SERVER__HOST=0.0.0.0
export JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true
exec "$CONDA_PREFIX/bin/python" src/main.py
```

### SEC-F25 — canopy `conf/Dockerfile` alt image hardcodes `--host 0.0.0.0` (Low, latent)

`conf/Dockerfile:81`:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8050"]
```

This is **not** the image `juniper-deploy` builds — `docker-compose.yml:129`
builds canopy from the repo-root `Dockerfile`, whose `CMD` is the safe
`["python", "src/main.py"]` (`Dockerfile:110`). `conf/Dockerfile` is paired with
`conf/docker-compose.yaml`, a **legacy/superseded** local compose: it publishes
all interfaces (`ports: 8050:8050`, not the loopback host publish the deploy
compose uses), sets no bind attestation, and still wires a dead `cascor-backend:8000`
service (commented out in the same file; the real backend is `juniper-cascor:8200`).
The maintained orchestration is `juniper-deploy`. So `conf/` is a latent bypass
inside stale infra, not a live production path.

**Fix (owner decision — deprecate vs modernize).** Because `conf/` is superseded
and internally inconsistent with the guard model (all-interfaces publish, no
attestation), a bare `CMD` align would leave the container binding loopback
*inside* the container and unreachable via its own publish. Two coherent options:
(a) **deprecate** — remove `conf/Dockerfile` + `conf/docker-compose.yaml` and the
existence assertion in `src/tests/regression/test_docker_demo_mode_default.py`,
pointing demos at `juniper-deploy`; or (b) **modernize** — route the `CMD` through
the guard (`python src/main.py`) and rewrite `conf/docker-compose.yaml` to the
deploy posture (loopback host publish + `JUNIPER_CANOPY_SERVER__HOST=0.0.0.0` +
`JUNIPER_CANOPY_LOOPBACK_PUBLISH_ATTESTED=true`). **Resolved: option (a), deprecate** — shipped in juniper-canopy #435 (merged).

### SEC-F26 — cascor carries a stray canopy demo with `--host 0.0.0.0` (Low, latent + hygiene)

`juniper-cascor/util/juniper_canopy-demo.bash:160`:

```bash
exec "$CONDA_PREFIX/bin/uvicorn" main:app --host 0.0.0.0 --port 8050 --log-level info
```

This is a copy of the canopy demo living in the cascor repo. Its header declares
`Sub-Project: JuniperCascor`, but it execs canopy's `main:app` on port 8050 —
cascor has no `main:app` (its entrypoint is `server.py` / `api.app:app` on
8200/8201), so the script is broken in-place as well as being a `--host 0.0.0.0`
artifact.

**Fix.** Remove the stray copy from cascor (repo-hygiene); the canonical demo
lives in canopy and is addressed by SEC-F24.

### SEC-F27 — canopy lacks the uvicorn-CLI bind-parity shim that cascor has (reclassified)

> **Reclassified during remediation (2026-07-06).** The original reading — "cascor
> docstring documents an anti-pattern, change it to `127.0.0.1`" — was wrong.
> `src/api/app.py:100` documents cascor's *defense*, not a bypass. See §7.

`src/api/app.py:97` defines `_settings_with_uvicorn_cli_bind()`, and `create_app`
calls it before the guard runs (`settings = _settings_with_uvicorn_cli_bind(get_settings())`,
`app.py:577`; `enforce_bind_attestation_guard(settings)` in the lifespan,
`app.py:314`). The shim overlays a uvicorn CLI `--host` / `--port` onto a transient
`Settings` copy, so a launch via `uvicorn api.app:create_app --factory --host 0.0.0.0`
makes the guard see the **real** CLI bind host, not the settings default. The
`--host 0.0.0.0` in that docstring is the scenario the shim *defends against* — so
cascor's factory / uvicorn-CLI path is already guard-authoritative.

The genuine finding is the **inverse**: canopy has no equivalent shim.
`main.lifespan` calls `enforce_loopback_bind_guard(settings.server.host, ...)`
directly (`main.py:240`), so any `uvicorn main:app --host X` launch bypasses the
guard — the shared root cause of SEC-F23 / SEC-F24 / SEC-F25.

**Fix (recommended).** Port cascor's `_settings_with_uvicorn_cli_bind` shim to
canopy so the guard evaluates the real CLI bind on *any* launch path — a generic
defense covering future launchers, not just the three found here. Do **not** change
the cascor docstring; it correctly documents the defended case. The per-launcher
fixes (SEC-F23/F24) close the known bypasses; the shim is the defense-in-depth that
stops the class recurring. **Resolved: ported now** — shipped in juniper-canopy #434
(merged) as `security.settings_with_uvicorn_cli_bind`, applied in `main.py` after
`get_settings()`, with 7 tests in `TestUvicornCliBindParity`.

### SEC-F28 — `plant_all` defaults juniper-data to `0.0.0.0` (Info, posture)

`util/juniper_plant_all.bash:102`:

```bash
JUNIPER_DATA_HOST="${JUNIPER_DATA_HOST:-0.0.0.0}"
```

used at line 402: `nohup uvicorn juniper_data.api.app:get_app --factory --host
"${JUNIPER_DATA_HOST}" ...`. This is **not** a guard bypass — juniper-data has
no bind guard (SEC-F22 covers canopy + cascor only) — but it is the same "binds
all interfaces on-host by default" posture the guard exists to discourage,
applied to an unguarded service. Recorded so the posture is explicit; the guard
itself is not defeated here because there is no guard on this path.

**Fix (owner call).** Default `JUNIPER_DATA_HOST` to `127.0.0.1` for the on-host
orchestrator, or extend a bind guard to juniper-data (larger scope; out of band
for this audit).

## 5. Confirmed-safe paths (guard authoritative)

These launch paths route the bind host through the setting the guard inspects.
uvicorn binds exactly the guarded value, so the guard's verdict matches the real
socket. No action needed; recorded so the audit is exhaustive.

| Path                           | Repo           | Evidence                                                 | Host source                                        |
|--------------------------------|----------------|----------------------------------------------------------|----------------------------------------------------|
| Container `CMD` (deploy-built) | juniper-canopy | `Dockerfile:110` → `main.py`                             | `host = settings.server.host`                      |
| Container `CMD` (deploy-built) | juniper-cascor | `Dockerfile:102` → `server.py`                           | `uvicorn.run(host=settings.host)` (`server.py:22`) |
| On-host `plant_all`            | juniper-canopy | `juniper_plant_all.bash:139,445` → `python main.py`      | settings-driven, no `--host`                       |
| On-host `plant_all`            | juniper-cascor | `juniper_plant_all.bash:115,424` → `python server.py`    | settings-driven, no `--host`                       |
| systemd unit                   | juniper-cascor | `scripts/juniper-cascor.service:30` → `python server.py` | settings-driven, no `--host`                       |

The two container `CMD`s are what `juniper-deploy` actually builds
(`docker-compose.yml:129` canopy, `:186` cascor — both `dockerfile: Dockerfile`,
the repo-root file), so the **production containerized path is guard-authoritative
on both services**. The bypasses are confined to on-host / alt / demo launchers.

## 6. Recommended remediation

**Uniform rule.** Every launcher for a guarded service must drive the bind host
through the guarded setting and invoke the app entrypoint
(`python src/main.py` / `python src/server.py`); no launcher should pass
`uvicorn --host`. Where a non-loopback bind is genuinely wanted (the demo, an
intentionally-exposed on-host unit), set the setting
(`JUNIPER_CANOPY_SERVER__HOST=0.0.0.0`) **and** the matching attestation flag, so
the guard evaluates the real bind host in-band (warns/attests) instead of being
bypassed. This keeps the guard authoritative on every path and preserves the
attestation trail.

Suggested sequencing:

1. **SEC-F23** (canopy systemd) — highest severity; carries the on-host
   reachability behavior change flagged in §4. Fix first, with owner sign-off on
   the loopback-by-default posture.
2. **SEC-F24** (canopy demo) — route through setting + attestation; keeps demo
   reachable, restores the attestation trail.
3. **SEC-F26** — mechanical hygiene: remove the stray cascor demo. Low risk.
   **SEC-F25** and **SEC-F27** were resolved by owner decision (deprecate `conf/`;
   port the canopy parity shim) and both shipped — see the status in §7.
4. **SEC-F28** — posture decision for juniper-data on-host default; owner call,
   may fold into a future data-service bind-guard scope.

Each fix lands as its own owner-reviewed PR (never auto-merged), consistent with
the deployment-trust workflow.

## 7. Remediation status (2026-07-06)

All six findings are shipped and **merged** as owner-gated PRs (none auto-merged).
The audit report itself is juniper-ml PR #630 (merged).

| ID      | Disposition                                                                                                                                                              | PR                           |
|---------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|
| SEC-F23 | Fixed — systemd `ExecStart` → `python main.py`, loopback-default + attested-exposure docs                                                                                | juniper-canopy #433 (merged) |
| SEC-F24 | Fixed — demo launcher → `python main.py`, loopback-default + attested-exposure docs                                                                                      | juniper-canopy #433 (merged) |
| SEC-F25 | Fixed — legacy `conf/Dockerfile` + `conf/docker-compose.yaml` **deprecated** (superseded by juniper-deploy); live refs repointed to the root Dockerfile / juniper-deploy | juniper-canopy #435 (merged) |
| SEC-F26 | Fixed — stray cascor canopy-demo removed                                                                                                                                 | juniper-cascor #394 (merged) |
| SEC-F27 | Fixed — cascor's `_settings_with_uvicorn_cli_bind` parity shim **ported to canopy** (`security.settings_with_uvicorn_cli_bind`, applied in `main.py`, 7 tests)           | juniper-canopy #434 (merged) |
| SEC-F28 | Fixed — `JUNIPER_DATA_HOST` default → `127.0.0.1` (consumers use `JUNIPER_DATA_URL`, unaffected)                                                                         | juniper-ml #631 (merged)     |

The two canopy launchers (SEC-F23/F24) close the *known* bypasses; the ported shim
(SEC-F27) makes the guard authoritative on any future `uvicorn main:app --host X`
launch, closing the class rather than the instances. SEC-F25's owner decision was
to **deprecate** the legacy `conf/` files. The behavior change flagged for SEC-F23
(on-host systemd now binds loopback by default) was approved before merge.
