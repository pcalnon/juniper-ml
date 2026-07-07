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

| ID | Path | Repo | Class | Severity |
| --- | --- | --- | --- | --- |
| SEC-F23 | `scripts/juniper-canopy.service:30` (systemd `ExecStart`) | juniper-canopy | BYPASS | Medium |
| SEC-F24 | `util/juniper_canopy-demo.bash:270` (demo launcher) | juniper-canopy | BYPASS | Low–Medium |
| SEC-F25 | `conf/Dockerfile:81` (alt image `CMD`, not deploy-built) | juniper-canopy | BYPASS (latent) | Low |
| SEC-F26 | `util/juniper_canopy-demo.bash:160` (stray canopy-demo copy) | juniper-cascor | BYPASS (latent) + hygiene | Low |
| SEC-F27 | `src/api/app.py:100` (docstring documents `--host 0.0.0.0`) | juniper-cascor | Doc anti-pattern | Info |
| SEC-F28 | `util/juniper_plant_all.bash:102` (`JUNIPER_DATA_HOST` default `0.0.0.0`) | juniper-ml | Posture (unguarded service) | Info |

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
`["python", "src/main.py"]` (`Dockerfile:110`). `conf/Dockerfile` is therefore a
latent bypass: harmless unless someone builds it, but it embeds the anti-pattern
and diverges from the production image.

**Fix.** Align its `CMD` with the root Dockerfile
(`CMD ["python", "src/main.py"]`), or delete `conf/Dockerfile` if it is dead.

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

### SEC-F27 — cascor docstring documents the `--host 0.0.0.0` anti-pattern (Info)

`src/api/app.py:100` (docstring, not executable):

```text
``uvicorn api.app:create_app --factory --host 0.0.0.0`` is a documented ...
```

Not a live launcher, but it advertises a guard-bypassing invocation as a
supported way to run the service.

**Fix.** Change the documented example to `--host 127.0.0.1` (or reference
`python src/server.py`), so the docs stop recommending the bypass.

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

| Path | Repo | Evidence | Host source |
| --- | --- | --- | --- |
| Container `CMD` (deploy-built) | juniper-canopy | `Dockerfile:110` → `main.py` | `host = settings.server.host` |
| Container `CMD` (deploy-built) | juniper-cascor | `Dockerfile:102` → `server.py` | `uvicorn.run(host=settings.host)` (`server.py:22`) |
| On-host `plant_all` | juniper-canopy | `juniper_plant_all.bash:139,445` → `python main.py` | settings-driven, no `--host` |
| On-host `plant_all` | juniper-cascor | `juniper_plant_all.bash:115,424` → `python server.py` | settings-driven, no `--host` |
| systemd unit | juniper-cascor | `scripts/juniper-cascor.service:30` → `python server.py` | settings-driven, no `--host` |

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
3. **SEC-F25 / SEC-F26 / SEC-F27** — mechanical hygiene (align/delete alt
   Dockerfile, remove stray cascor demo, fix docstring). Low risk, batchable.
4. **SEC-F28** — posture decision for juniper-data on-host default; owner call,
   may fold into a future data-service bind-guard scope.

Each fix lands as its own owner-reviewed PR (never auto-merged), consistent with
the deployment-trust workflow.
