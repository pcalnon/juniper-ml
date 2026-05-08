# CasCor Conda Env Fix — 2026-05-07

**Status**: shipped
**Author**: Paul Calnon (executed by Claude Code)
**Scope**: `util/juniper_plant_all.bash`, `/opt/miniforge3/envs/JuniperCascor{,1}/etc/conda/{activate,deactivate}.d/`

---

## 1. Symptom

Running `./util/juniper_plant_all.bash` failed during the cascor stage:

```
[juniper_plant_all.bash:408] === Starting juniper-cascor ===
… (60s pass) …
[juniper_plant_all.bash:wait_for_health] juniper-cascor: timeout reached, /v1/health never returned 2xx
```

The cascor server log (`juniper-cascor/logs/juniper-cascor_*.log`) showed the
process dying immediately at import time:

```
File "/home/pcalnon/Development/python/Juniper/juniper-cascor/src/api/app.py", line 11, in <module>
    import torch
File "/opt/miniforge3/envs/JuniperCascor/lib/python3.14/site-packages/torch/__init__.py", line 1013, in <module>
ImportError: Failed to load PyTorch C extensions:
    It appears that PyTorch has loaded the `torch/_C` folder
    of the PyTorch repository rather than the C extensions which
    are expected in the `torch._C` namespace.
```

The server never bound to port 8201, so `wait_for_health` looped until
`HEALTH_CHECK_TIMEOUT` expired.

---

## 2. Root cause — torch wheel layout bug under Python 3.14

The `JuniperCascor` env (Python 3.14.3 + torch 2.9.1) ships **both**:

- `torch/_C.cpython-314-x86_64-linux-gnu.so` — the actual compiled C extension
- `torch/_C/` — a directory containing `.pyi` type stubs

Under PEP 420 implicit namespace packages, `torch/_C/` is a valid namespace
package even with no `__init__.py`. Python's import system prefers packages
(directories) over modules (`.so` files) of the same name, so `import torch._C`
resolves to the stub-only directory and `_C_for_compiled_check.__file__` is
`None`. torch's `__init__.py` (line 1013) then raises the "Failed to load
PyTorch C extensions" `ImportError` shown above.

This is a torch 2.9.1 + Python 3.14 wheel issue, not user error. The
`JuniperCascor1` env (Python 3.13.13 + torch 2.11.0) was created earlier as
a known-working fallback and has the correct layout — only the `.so` is
present, no shadowing `_C/` directory.

A secondary contributor — the rust_mudgeon `LIBTORCH` / `LD_LIBRARY_PATH`
bleed-through documented in
`juniper-canopy/etc/conda/activate.d/00_isolate_from_tch_rs.sh` — does *not*
fully explain this failure (the wheel-layout error reproduces even with both
vars unset), but it would be a separate import-time failure mode if torch did
load. Both `JuniperCascor` and `JuniperCascor1` now carry matching activate
hooks to defend against it.

---

## 3. Fix

### 3.1 Switch the default cascor env in `juniper_plant_all.bash`

```bash
JUNIPER_CASCOR_CONDA="${JUNIPER_CASCOR_CONDA:-JuniperCascor1}"
```

Mirrors the existing `JUNIPER_CANOPY_CONDA="${JUNIPER_CANOPY_CONDA:-JuniperCanopy1}"`
pattern (canopy hit the LIBTORCH issue weeks earlier and migrated to a
postfixed-`1` env then). Override via `JUNIPER_CASCOR_CONDA=JuniperCascor` if
you have a known-good legacy env.

`JUNIPER_WORKER_CONDA` was also made overridable but its default stays at
`JuniperCascor` — the `juniper-cascor-worker` pip wheel is currently only
installed there. Once the worker is also installed into `JuniperCascor1`,
the worker default can flip too and the legacy env can be retired.

### 3.2 Add LIBTORCH-strip activate hooks to the cascor env

Mirroring `JuniperCanopy1`, two new files were dropped into the JuniperCascor
env tree:

- `/opt/miniforge3/envs/JuniperCascor/etc/conda/activate.d/00_isolate_from_tch_rs.sh`
- `/opt/miniforge3/envs/JuniperCascor/etc/conda/deactivate.d/00_restore_tch_rs.sh`

These strip `LIBTORCH` and any `/rust_mudgeon/` path segments from
`LD_LIBRARY_PATH` on `conda activate`, restoring them on `conda deactivate`,
so the user's `~/.bashrc`-exported `LIBTORCH` does not leak into this env.
**These files live outside the repo** — they are env-local shell hooks,
created the same way `JuniperCanopy1`'s hook was created.

These do *not* fix the wheel-layout issue (the wheel is still broken), but
they preempt the secondary failure mode if a future torch reinstall fixes
the layout while the `~/.bashrc` LIBTORCH export remains.

---

## 4. Verification

After the script change:

```
$ source /opt/miniforge3/etc/profile.d/conda.sh
$ conda activate JuniperCascor1
$ cd juniper-cascor/src
$ JUNIPER_CASCOR_HOST=localhost JUNIPER_CASCOR_PORT=8201 python server.py &
$ curl -fsS http://localhost:8201/v1/health
{"status":"ok","version":"0.4.0"}
```

Server boots cleanly, uvicorn listens on `localhost:8201`, `/v1/health`
returns `{"status":"ok","version":"0.4.0"}` immediately.

---

## 5. Follow-ups

- **DONE 2026-05-07**: `juniper-cascor-worker` installed editable into
  `JuniperCascor1` from
  `/home/pcalnon/Development/python/Juniper/juniper-cascor-worker`.
  `JUNIPER_WORKER_CONDA` default flipped to `JuniperCascor1` in commit
  `b4fd09d` and the comment block above the assignment was tidied to
  match in this PR. The legacy `JuniperCascor` env is no longer required
  by `juniper_plant_all.bash`.
- **Open**: rebuild or reinstall torch in `JuniperCascor` (or simply
  delete and recreate the env on Python 3.13 to mirror `JuniperCascor1`).
  Until then, `JuniperCascor` remains broken for any cascor module that
  imports torch and should be considered deprecated.
- **Open**: document the env split (or its retirement) in
  `juniper-cascor/AGENTS.md` if useful for future contributors.
