#!/usr/bin/env python3
"""
A-N2 (item 18): drive generate -> stage -> train -> render THROUGH canopy, once per §12-seeded generator.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: item 18 (A-N2) of prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_canopy-selection-six-prs-queued-live-swap-mirror-staged.md;
         §12.4 of notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md;
         evidence written to reports/2026-09-23_canopy-a-n2-generate-stage-train-render/

What it drives, and how
-----------------------
Every MUTATING step goes through canopy's HTTP API on :8061 -- the routes the dashboard's own
callbacks and buttons use -- never directly to cascor / juniper-data / recurrence:

  select   POST /api/model/select {"nn_model": <key>}                 (_select_model_handler)
  caps     POST /api/set_params  {nn_model, nn_*/cn_* caps}             (the params panel's Apply)
  stage    POST /api/stage_dataset {nn_dataset_type, nn_dataset_params | spiral typed fields, nn_model}
                                                                        (_apply_dataset_handler)
  start    POST /api/train/start [one-shot body for recurrence]        (the Start button's REST
           transport, restFallback() in dashboard_manager's clientside JS; the WS transport is not used)
  restart  POST /api/train/restart {"start_fresh": true}               (the restart modal, only when asked)
  poll     GET  /api/train/status
  render   GET  /api/metrics, /api/metrics/history?limit=0, /api/dataset, /api/state, /api/status,
                /api/selection, /api/topology, /api/network/stats, /api/decision_boundary

Requests carry what a same-origin dashboard request carries: the session cookie, an Origin of
http://127.0.0.1:8061 and an X-CSRF-Token minted by GET /api/csrf (require_browser_control_auth).

juniper-data (:8111) is READ ONLY here, as an observer: its dataset list before/after each case is
how "generate" is evidenced (the dataset canopy's run caused to exist, with its metadata). The four
service logs are sliced by byte offset per case and saved (token-shaped strings redacted).

Subcommands
-----------
  provenance            which code each leg runs: /v1/health git_sha vs worktree HEAD, the process
                        cwd/cmdline, which worktree files the running process compiled, the data venv's
                        juniper_data.__file__, and the recurrence leg's import locations + versions
  run <case> [opts]     one generator end to end; writes <evidence>/<case>[__<tag>]/
  postflight            my four ports free; the other session's three pids alive on 8101/8202/8051
  summarize             per-stage PASS/FAIL for every case dir, from the saved evidence -> verdicts.json
  archive-logs          copy the four full service logs into 00_stack/logs (redacted) -- before --down
  slim                  truncate bulky captures in place (history lists, dataset arrays, grids,
                        per-candidate-epoch log chatter), marking every cut; run AFTER summarize
  list                  print the case table

Run with the JuniperCascor1 interpreter (``python3`` on this host); needs ``requests``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any

import requests

ML_ROOT = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE = ML_ROOT / "reports" / "2026-09-23_canopy-a-n2-generate-stage-train-render"
SCRATCH = pathlib.Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/317c1df2-5970-4312-96f5-ab61df517bb2/scratchpad")
RUN_DIR = SCRATCH / "a-n2-run"
LOG_DIR = RUN_DIR / "logs"
WT_ROOT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees")
WORKTREES = {
    "data": WT_ROOT / "juniper-data--verify--a-n2-loop--20260923-1415--ce436819",
    "cascor": WT_ROOT / "juniper-cascor--verify--a-n2-loop--20260923-1415--f7a6d573",
    "canopy": WT_ROOT / "juniper-canopy--verify--a-n2-loop--20260923-1415--48074653",
}
RECURRENCE_CHECKOUT = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-recurrence")
CASCOR_ENV_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
CANOPY_ENV_PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
PORTS = {"data": 8111, "cascor": 8212, "canopy": 8061, "recurrence": 8221}
PROTECTED = {2856834: 8101, 2857489: 8202, 2858037: 8051}
CANOPY = f"http://127.0.0.1:{PORTS['canopy']}"
DATA = f"http://127.0.0.1:{PORTS['data']}"
CASCOR = f"http://127.0.0.1:{PORTS['cascor']}"
RECURRENCE = f"http://127.0.0.1:{PORTS['recurrence']}"

# canopy's registry and alias map, imported from the canopy WORKTREE (both are stdlib-only). The
# assert below is the point: an installed juniper_canopy must never answer for the worktree.
sys.path.insert(0, str(WORKTREES["canopy"] / "src"))
import dataset_schema as DS  # noqa: E402
import model_registry as MR  # noqa: E402

assert pathlib.Path(MR.__file__).resolve().is_relative_to(WORKTREES["canopy"]), MR.__file__
assert pathlib.Path(DS.__file__).resolve().is_relative_to(WORKTREES["canopy"]), DS.__file__

# CasCor caps, sent through canopy's /api/set_params (canopy key -> cascor key per
# CascorServiceAdapter._CANOPY_TO_CASCOR_PARAM_MAP). Mirrors the bounded trainability probe of
# util/ad-hoc/2026-09-10_rank2_cascor_fit.py (max_iterations 8, output AND max epochs 60,
# candidate_epochs 40) so the numbers are comparable with §12.7 / §12.8.
#
# Resident hazard (AGENTS.md): max_epochs alone governs only the INITIAL output pass. canopy's Start
# sends no max_epochs, so cascor's fit() falls back to output_epochs for that pass too
# (cascade_correlation.py fit(): ``max_epochs = (max_epochs, self.output_epochs)[max_epochs is None]``).
# Both the max-epochs-style field (nn_max_total_epochs -> epochs_max) and nn_output_epochs are sent,
# at the same value; cascor reports epochs_max skipped(not-updatable) since C2b (it is derived).
#
# nn_max_hidden_units is 32, not 8: canopy's Start CONTINUES the current model (C5 default), so the
# control's network (up to 10 units at cascor's defaults) carries into the next run, and a total cap
# below that would forbid any growth. Growth per run is bounded by nn_max_iterations=8 instead.
CASCOR_CAPS: dict[str, Any] = {
    "nn_max_iterations": 8,
    "nn_output_epochs": 60,
    "nn_max_total_epochs": 60,
    "cn_training_iterations": 40,
    "nn_max_hidden_units": 32,
}

CASES: dict[str, dict[str, str]] = {
    "01_spirals_control": {"model": "cascor", "value": "spirals", "role": "pre-§12 control (rank-2, CasCor)"},
    "02_gaussian": {"model": "cascor", "value": "gaussian", "role": "§12 rank-2 (§12.7)"},
    "03_checkerboard": {"model": "cascor", "value": "checkerboard", "role": "§12 rank-2 (§12.7)"},
    "04_equities": {"model": "cascor", "value": "equities", "role": "§12 rank-2 (§12.8)"},
    "05_multi_sine": {"model": "recurrence", "value": "multi_sine", "role": "§12 rank-3 (§12.6)"},
    "06_mackey_glass": {"model": "recurrence", "value": "mackey_glass", "role": "§12 rank-3 (§12.6)"},
    "07_irregular_sine": {"model": "recurrence", "value": "irregular_sine", "role": "§12 rank-3 (§12.6)"},
    "08_ar_p": {"model": "recurrence", "value": "ar_p", "role": "§12 rank-3 (§12.6)"},
    "09_delay_product": {"model": "recurrence", "value": "delay_product", "role": "§12 rank-3 (§12.6)"},
    "10_equities_seq_control": {"model": "recurrence", "value": "equities_seq", "role": "LMU incumbent control (rank-3)"},
}

_TOKEN_PATTERNS = [re.compile(r"hf_[A-Za-z0-9]{20,}"), re.compile(r"pypi-[A-Za-z0-9_\-]{20,}"), re.compile(r"(?i)(x-api-key['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+")]


def redact(text: str) -> str:
    for pat in _TOKEN_PATTERNS:
        text = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "<redacted>", text)
    return text


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


def write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(json.dumps(obj, indent=2, sort_keys=False, default=str)) + "\n")


def sh(cmd: list[str], cwd: str | None = None, env: dict[str, str] | None = None, timeout: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "cwd": cwd, "rc": proc.returncode, "stdout": redact(proc.stdout), "stderr": redact(proc.stderr[-4000:])}
    except Exception as exc:  # recorded, never raised: provenance must report what it could not read
        return {"cmd": cmd, "cwd": cwd, "error": repr(exc)}


def git_head(path: pathlib.Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


def listener_pid(port: int) -> int | None:
    out = subprocess.run(["ss", "-tlnpH", f"sport = :{port}"], capture_output=True, text=True).stdout
    m = re.search(r"pid=(\d+)", out)
    return int(m.group(1)) if m else None


def listener_lines(ports: list[int]) -> str:
    out = subprocess.run(["ss", "-tlnpH"], capture_output=True, text=True).stdout
    keep = [ln for ln in out.splitlines() if any(re.search(rf":{p}\b", ln) for p in ports)]
    return "\n".join(keep)


_ENV_KEYS = (
    "JUNIPER_DATA_URL",
    "JUNIPER_DATA_GIT_SHA",
    "JUNIPER_CASCOR_GIT_SHA",
    "JUNIPER_CASCOR_BUILD_DATE",
    "JUNIPER_CASCOR_WS_CONTROL_ALLOWED_ORIGINS",
    "JUNIPER_CASCOR_SNAPSHOTS_DIR",
    "JUNIPER_CANOPY_GIT_SHA",
    "JUNIPER_CANOPY_BUILD_DATE",
    "JUNIPER_CANOPY_DEMO_MODE",
    "JUNIPER_CANOPY_SERVER__PORT",
    "JUNIPER_CANOPY_CASCOR_SERVICE_URL",
    "JUNIPER_CANOPY_JUNIPER_DATA_URL",
    "JUNIPER_CANOPY_RECURRENCE_SERVICE_URL",
    "JUNIPER_CANOPY_CASCOR_WS_ORIGIN",
    "JUNIPER_CANOPY_SNAPSHOT_DIR",
    "JUNIPER_RECURRENCE_METRICS_ENABLED",
    "JUNIPER_RECURRENCE_RATE_LIMIT_ENABLED",
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
    "PYTHONPATH",
    "LD_LIBRARY_PATH",
)


def proc_info(pid: int) -> dict[str, Any]:
    """cwd / exe / cmdline and a NAMED subset of the environment. Never the whole environ: this
    host's shell exports tokens, and the stack legs inherit them."""
    base = pathlib.Path(f"/proc/{pid}")
    info: dict[str, Any] = {"pid": pid}
    try:
        info["cwd"] = os.readlink(base / "cwd")
        info["exe"] = os.readlink(base / "exe")
        info["cmdline"] = (base / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
        env = {}
        for item in (base / "environ").read_bytes().split(b"\0"):
            key, _, value = item.decode(errors="replace").partition("=")
            if key in _ENV_KEYS:
                env[key] = value
        info["env_selected"] = env
        info["start_epoch_s"] = _proc_start_epoch(pid)
    except OSError as exc:
        info["error"] = repr(exc)
    return info


def _proc_start_epoch(pid: int) -> float:
    stat = pathlib.Path(f"/proc/{pid}/stat").read_text()
    start_ticks = int(stat.rsplit(")", 1)[1].split()[19])
    btime = next(int(ln.split()[1]) for ln in pathlib.Path("/proc/stat").read_text().splitlines() if ln.startswith("btime"))
    return btime + start_ticks / os.sysconf("SC_CLK_TCK")


def compiled_since(root: pathlib.Path, since: float) -> list[str]:
    """.pyc files under ``root`` written at/after ``since`` -- i.e. worktree SOURCE the leg imported."""
    hits = []
    for pyc in root.rglob("__pycache__/*.pyc"):
        try:
            if pyc.stat().st_mtime >= since - 2:
                hits.append(str(pyc.relative_to(root)))
        except OSError:
            continue
    return sorted(hits)


def get_json(url: str, timeout: float = 30) -> dict[str, Any]:
    t = time.time()
    try:
        r = requests.get(url, timeout=timeout)
        try:
            body: Any = r.json()
        except ValueError:
            body = r.text[:4000]
        return {"url": url, "status": r.status_code, "elapsed_s": round(time.time() - t, 3), "body": body}
    except requests.RequestException as exc:
        return {"url": url, "error": repr(exc), "elapsed_s": round(time.time() - t, 3)}


# --------------------------------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------------------------------
def cmd_provenance(_args: argparse.Namespace) -> int:
    out = EVIDENCE / "00_stack" / "provenance.json"
    report: dict[str, Any] = {"recorded_utc": utc_now(), "legs": {}}
    heads = {name: git_head(path) for name, path in WORKTREES.items()}
    report["worktree_heads"] = heads
    report["worktree_status_porcelain"] = {name: sh(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"])["stdout"] for name, path in WORKTREES.items()}

    health_urls = {
        "data": [f"{DATA}/v1/health"],
        "cascor": [f"{CASCOR}/v1/health"],
        "canopy": [f"{CANOPY}/v1/health"],
        "recurrence": [f"{RECURRENCE}/v1/health", f"{RECURRENCE}/v1/health/ready"],
    }
    verdicts = {}
    for leg, port in PORTS.items():
        pid = listener_pid(port)
        leg_rec: dict[str, Any] = {"port": port, "listener_pid": pid, "health": [get_json(u) for u in health_urls[leg]]}
        pidfile = RUN_DIR / f"juniper-{leg}.pid"
        leg_rec["pidfile"] = pidfile.read_text().strip() if pidfile.exists() else None
        if pid:
            leg_rec["proc"] = proc_info(pid)
        body = leg_rec["health"][0].get("body") if leg_rec["health"] else None
        reported = body.get("git_sha") if isinstance(body, dict) else None
        leg_rec["health_git_sha"] = reported
        if leg in heads:
            leg_rec["worktree_head"] = heads[leg]
            verdicts[leg] = "MATCH" if reported == heads[leg] else f"MISMATCH (health={reported!r}, head={heads[leg]!r})"
        # Which worktree source the running process compiled since it started. The worktrees were
        # created fresh at 2026-09-23T19:15Z with no __pycache__, so every .pyc here was written by a
        # process importing THIS tree's source; the legs are the only processes run from them.
        if leg in ("cascor", "canopy") and pid and "proc" in leg_rec and "start_epoch_s" in leg_rec["proc"]:
            hits = compiled_since(WORKTREES[leg], leg_rec["proc"]["start_epoch_s"])
            leg_rec["worktree_pyc_written_since_start"] = {"count": len(hits), "sample": hits[:40]}
        report["legs"][leg] = leg_rec
    report["git_sha_verdicts"] = verdicts

    # Same-interpreter, same-cwd import probes: how module resolution goes for each leg's command.
    report["import_probes"] = {
        "cascor (uvicorn app-dir = cwd = worktree src)": sh(
            [CASCOR_ENV_PY, "-c", "import api, cascade_correlation, cascor_constants; print(api.__file__); print(cascade_correlation.__file__); print(cascor_constants.__file__)"],
            cwd=str(WORKTREES["cascor"] / "src"),
            env={**_clean_env(), "LD_LIBRARY_PATH": ""},
        ),
        "canopy (python main.py: sys.path[0] = worktree src)": sh(
            [CANOPY_ENV_PY, "-c", "import sys; import model_registry, dataset_schema, backend, frontend, communication; print(model_registry.__file__); print(dataset_schema.__file__); print(backend.__file__); print(frontend.__file__); print(communication.__file__)"],
            cwd=str(WORKTREES["canopy"] / "src"),
            env=_clean_env(),
        ),
        "data (dedicated venv)": sh(
            [str(RUN_DIR / ".venv-data" / "bin" / "python"), "-c", "import juniper_data, importlib.metadata as m; print(juniper_data.__file__); print(m.version('juniper-data'))"],
            cwd=str(RUN_DIR),
            env=_clean_env(),
        ),
        "data venv pip show": sh([str(RUN_DIR / ".venv-data" / "bin" / "python"), "-m", "pip", "show", "juniper-data", "yfinance", "datasets", "pandas"], cwd=str(RUN_DIR), env=_clean_env()),
        "recurrence (console script, cwd = run dir)": sh(
            [
                CASCOR_ENV_PY,
                "-c",
                "import importlib.metadata as m\n"
                "import juniper_recurrence, juniper_recurrence_model, juniper_recurrence_client, juniper_data_client\n"
                "for mod in (juniper_recurrence, juniper_recurrence_model, juniper_recurrence_client, juniper_data_client): print(mod.__name__, mod.__file__)\n"
                "for d in ('juniper-recurrence', 'juniper-recurrence-model', 'juniper-recurrence-client', 'juniper-data-client', 'torch'): print(d, m.version(d))\n",
            ],
            cwd=str(RUN_DIR),
            env={**_clean_env(), "LD_LIBRARY_PATH": ""},
        ),
        "recurrence pip show": sh([CASCOR_ENV_PY, "-m", "pip", "show", "juniper-recurrence", "juniper-recurrence-model"], cwd=str(RUN_DIR), env=_clean_env()),
        "recurrence checkout HEAD": sh(["git", "-C", str(RECURRENCE_CHECKOUT), "rev-parse", "HEAD"]),
        "recurrence checkout status": sh(["git", "-C", str(RECURRENCE_CHECKOUT), "status", "--porcelain", "--branch"]),
        "recurrence checkout origin/main": sh(["git", "-C", str(RECURRENCE_CHECKOUT), "log", "-1", "--format=%H %cI %s", "origin/main"]),
    }
    write_json(out, report)
    print(json.dumps({"git_sha_verdicts": verdicts, "heads": heads}, indent=2))
    for leg in ("cascor", "canopy"):
        pyc = report["legs"][leg].get("worktree_pyc_written_since_start", {})
        print(f"{leg}: worktree .pyc written since process start: {pyc.get('count')}")
    for name, probe in report["import_probes"].items():
        print(f"--- {name} (rc={probe.get('rc')})\n{probe.get('stdout', '')}{probe.get('error', '')}")
    print(f"wrote {out}")
    return 0


def _clean_env() -> dict[str, str]:
    """A minimal environment for probes: PATH/HOME only (no inherited tokens, no PYTHONPATH)."""
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/tmp")}


# --------------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------------
class Recorder:
    """Numbered JSON files, one per HTTP exchange, plus an in-memory index."""

    def __init__(self, out: pathlib.Path, session: requests.Session, headers: dict[str, str]) -> None:
        self.out = out
        self.session = session
        self.headers = headers
        self.n = 0
        self.index: list[dict[str, Any]] = []

    def call(self, step: str, method: str, url: str, body: Any = None, timeout: float = 120, save: bool = True) -> dict[str, Any]:
        self.n += 1
        t0 = time.time()
        rec: dict[str, Any] = {"step": step, "t_utc": utc_now(), "method": method, "url": url}
        if body is not None:
            rec["request_body"] = body
        try:
            resp = self.session.request(method, url, json=body, headers=self.headers, timeout=timeout)
            rec["status"] = resp.status_code
            try:
                rec["response"] = resp.json()
            except ValueError:
                rec["response"] = resp.text[:20000]
        except requests.RequestException as exc:
            rec["status"] = None
            rec["error"] = repr(exc)
        rec["elapsed_s"] = round(time.time() - t0, 3)
        if save:
            write_json(self.out / f"{self.n:02d}_{step}.json", rec)
        self.index.append({k: rec.get(k) for k in ("step", "t_utc", "method", "url", "status", "elapsed_s")})
        return rec


def _log_sizes() -> dict[str, int]:
    return {leg: (LOG_DIR / f"juniper-{leg}.log").stat().st_size if (LOG_DIR / f"juniper-{leg}.log").exists() else 0 for leg in PORTS}


_INTERESTING = re.compile(r"ERROR|CRITICAL|WARNING|Traceback|Exception|refus|reject|exceeds|422|409|502|500 |/v1/datasets|/v1/train|/v1/training/(start|dataset)|stage|staged|_reload_dataset|create_dataset|dataset_id|complet|converg|fit ", re.I)


def _save_log_slices(out: pathlib.Path, offsets: dict[str, int]) -> dict[str, dict[str, Any]]:
    summary = {}
    (out / "logs").mkdir(parents=True, exist_ok=True)
    for leg, start in offsets.items():
        path = LOG_DIR / f"juniper-{leg}.log"
        if not path.exists():
            continue
        with path.open("rb") as fh:
            fh.seek(start)
            raw = fh.read()
        text = redact(raw.decode(errors="replace"))
        if len(text) > 3_000_000:
            text = text[:1_000_000] + "\n...[middle elided by the A-N2 driver: slice > 3 MB]...\n" + text[-2_000_000:]
        (out / "logs" / f"{leg}.slice.log").write_text(text)
        lines = [ln for ln in text.splitlines() if _INTERESTING.search(ln)]
        (out / "logs" / f"{leg}.excerpt.log").write_text("\n".join(lines[:600]) + ("\n...[excerpt truncated at 600 lines]\n" if len(lines) > 600 else "\n"))
        summary[leg] = {"bytes": len(raw), "excerpt_lines": min(len(lines), 600)}
    return summary


def _stage_payload(case: dict[str, str], state: dict[str, Any]) -> dict[str, Any]:
    """The body canopy's Apply Dataset sends (DashboardManager._apply_dataset_handler at canopy
    48074653): spiral's typed fields for spirals; otherwise the registry seed as nn_dataset_params
    (omitted when empty, as the handler omits an empty params dict). The untouched form's rendered
    schema-default values are NOT added: juniper-data fills the same defaults for an omitted key.
    The spiral values are the sidebar's service-mode values, read from /api/state."""
    value = case["value"]
    payload: dict[str, Any] = {"nn_dataset_type": value}
    if DS.generator_name_for_type(value) == "spiral":
        for key in ("nn_dataset_elements", "nn_dataset_noise", "nn_spiral_rotations", "nn_spiral_number"):
            if state.get(key) is not None:
                payload[key] = state[key]
    else:
        seed = MR.dataset_default_params(value)
        if seed:
            payload["nn_dataset_params"] = seed
    payload["nn_model"] = case["model"]
    return payload


def _oneshot_body(case: dict[str, str]) -> dict[str, Any] | None:
    """DashboardManager._resolve_oneshot_start_body_handler, reproduced from the same registry."""
    if case["model"] != "recurrence":
        return None
    ref: dict[str, Any] = {"generator": DS.generator_name_for_type(case["value"])}
    seed = MR.dataset_default_params(case["value"])
    if seed:
        ref["params"] = seed
    return {"dataset": ref}


_STATUS_KEYS = ("fsm_status", "phase", "is_running", "is_training", "completed", "failed", "current_epoch", "hidden_units", "completion_reason")


def _poll(rec: Recorder, model: str, t_start: float, timeout: float) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """Poll /api/train/status to a terminal state. A cascor start is asynchronous, so a
    ``completed`` read before the run was ever seen running may be the PREVIOUS run's; the
    history-growth check in ``render`` is what ties the result to this run."""
    timeline: list[dict[str, Any]] = []
    last_key = None
    seen_running = False
    status: dict[str, Any] = {}
    while True:
        now = time.time() - t_start
        try:
            resp = rec.session.get(f"{CANOPY}/api/train/status", headers=rec.headers, timeout=30)
            status = resp.json() if resp.ok else {"http_status": resp.status_code, "text": resp.text[:500]}
        except requests.RequestException as exc:
            status = {"error": repr(exc)}
        key = tuple(status.get(k) for k in _STATUS_KEYS)
        if key != last_key:
            timeline.append({"t_s": round(now, 2), **{k: status.get(k) for k in _STATUS_KEYS}})
            last_key = key
        running = bool(status.get("is_running") or status.get("is_training"))
        seen_running = seen_running or running
        terminal_flag = bool(status.get("completed") or status.get("failed"))
        if model == "recurrence":
            # RecurrenceBackend.start_training sets state="training" and clears the result
            # synchronously before /api/train/start returns, so any terminal flag now is this fit's.
            if terminal_flag:
                return ("completed" if status.get("completed") else "failed"), status, timeline
        else:
            if seen_running and not running:
                return _classify(status), status, timeline
            if terminal_flag and not seen_running and now > 20:
                return _classify(status) + " (never observed running)", status, timeline
            if not running and not seen_running and not terminal_flag and now > 60:
                return "never-started", status, timeline
        if now > timeout:
            return "timeout", status, timeline
        time.sleep(0.2 if now < 15 else 2.0)


def _classify(status: dict[str, Any]) -> str:
    if status.get("failed"):
        return "failed"
    if status.get("completed"):
        return "completed"
    return f"stopped:{status.get('fsm_status')}"


def _data_ids() -> list[str]:
    """Every dataset id the isolated juniper-data holds (``GET /v1/datasets`` caps ``limit`` at 1000)."""
    ids: list[str] = []
    offset = 0
    while True:
        r = requests.get(f"{DATA}/v1/datasets", params={"limit": 1000, "offset": offset}, timeout=30)
        r.raise_for_status()
        page = r.json()
        if not isinstance(page, list) or not page:
            return ids
        ids.extend(page)
        if len(page) < 1000:
            return ids
        offset += len(page)


def cmd_run(args: argparse.Namespace) -> int:
    case = CASES[args.case]
    out = EVIDENCE / (args.case + (f"__{args.tag}" if args.tag else ""))
    out.mkdir(parents=True, exist_ok=True)
    offsets = _log_sizes()
    session = requests.Session()
    csrf = session.get(f"{CANOPY}/api/csrf", timeout=30).json()
    headers = {"Origin": CANOPY, "X-CSRF-Token": csrf.get("csrf_token", "")}
    rec = Recorder(out, session, headers)
    summary: dict[str, Any] = {"case": args.case, **case, "tag": args.tag, "start_route": args.start_route, "started_utc": utc_now(), "csrf_enabled": csrf.get("enabled")}
    t_case = time.time()

    rec.call("selection_before", "GET", f"{CANOPY}/api/selection")
    sel = rec.call("model_select", "POST", f"{CANOPY}/api/model/select", {"nn_model": case["model"]})
    summary["model_select"] = {"status": sel.get("status"), "backend": (sel.get("response") or {}).get("backend") if isinstance(sel.get("response"), dict) else None}

    if case["model"] == "cascor" and not args.no_caps:
        caps = rec.call("set_params_caps", "POST", f"{CANOPY}/api/set_params", {"nn_model": "cascor", **CASCOR_CAPS})
        resp = caps.get("response") if isinstance(caps.get("response"), dict) else {}
        summary["caps"] = {"status": caps.get("status"), "applied": resp.get("applied"), "skipped_detail": resp.get("skipped_detail"), "error": resp.get("error")}

    state = rec.call("state_before", "GET", f"{CANOPY}/api/state")
    state_body = state.get("response") if isinstance(state.get("response"), dict) else {}
    summary["effective_params_before"] = {k: state_body.get(k) for k in ("nn_max_iterations", "nn_output_epochs", "nn_max_total_epochs", "cn_training_iterations", "nn_max_hidden_units", "cn_pool_size", "nn_patience")}

    ids_before = _data_ids()
    payload = _stage_payload(case, state_body)
    stage = rec.call("stage_dataset", "POST", f"{CANOPY}/api/stage_dataset", payload)
    summary["stage"] = {"status": stage.get("status"), "elapsed_s": stage.get("elapsed_s"), "payload": payload}
    rec.call("status_after_stage", "GET", f"{CANOPY}/api/status")
    rec.call("selection_after_stage", "GET", f"{CANOPY}/api/selection")
    hist_before = rec.call("metrics_history_before", "GET", f"{CANOPY}/api/metrics/history?limit=0")
    hb = hist_before.get("response", {}).get("history") if isinstance(hist_before.get("response"), dict) else None
    summary["history_len_before"] = len(hb) if isinstance(hb, list) else None

    if stage.get("status") != 200 and not args.start_anyway:
        summary["train"] = "skipped (stage failed)"
    else:
        if args.start_route == "restart-fresh":
            start = rec.call("train_restart_fresh", "POST", f"{CANOPY}/api/train/restart", {"start_fresh": True, "reset": True}, timeout=180)
        else:
            start = rec.call("train_start", "POST", f"{CANOPY}/api/train/start", _oneshot_body(case), timeout=180)
        t_start = time.time()
        summary["start"] = {"status": start.get("status"), "elapsed_s": start.get("elapsed_s"), "response": start.get("response"), "body": _oneshot_body(case) if args.start_route == "start" else {"start_fresh": True, "reset": True}}
        started_ok = start.get("status") == 200 and (args.start_route != "restart-fresh" or bool((start.get("response") or {}).get("success")))
        if started_ok:
            outcome, final, timeline = _poll(rec, case["model"], t_start, args.timeout)
            summary["train_outcome"] = outcome
            summary["train_wall_s"] = round(time.time() - t_start, 2)
            write_json(out / "poll_timeline.json", {"final_status": final, "timeline": timeline})
            if outcome == "timeout" and case["model"] == "cascor" and args.stop_on_timeout:
                rec.call("train_stop_after_timeout", "POST", f"{CANOPY}/api/train/stop")
        else:
            summary["train_outcome"] = "start refused"

    # render: what the dashboard's panels read
    render_routes = ["/api/train/status", "/api/status", "/api/metrics", "/api/metrics/history?limit=0", "/api/dataset", "/api/state", "/api/selection", "/api/topology", "/api/network/stats", "/api/decision_boundary", "/api/stream_health"]
    render: dict[str, Any] = {}
    for route in render_routes:
        step = "render_" + re.sub(r"[^a-z0-9]+", "_", route.strip("/").lower()).strip("_")
        r = rec.call(step, "GET", f"{CANOPY}{route}")
        render[route] = r
    summary["render_status_codes"] = {route: r.get("status") for route, r in render.items()}
    hist = render["/api/metrics/history?limit=0"].get("response")
    hist_list = hist.get("history") if isinstance(hist, dict) else None
    summary["history_len_after"] = len(hist_list) if isinstance(hist_list, list) else None
    if isinstance(hist_list, list) and hist_list:
        summary["history_last"] = hist_list[-1]
        new_rows = hist_list[summary["history_len_before"] :] if isinstance(summary.get("history_len_before"), int) else []
        summary["history_new_rows"] = len(new_rows)
        if new_rows:
            summary["history_first_new"] = new_rows[0]
    summary["metrics"] = render["/api/metrics"].get("response")
    summary["dataset_view"] = render["/api/dataset"].get("response")
    tstat = render["/api/train/status"].get("response")
    if isinstance(tstat, dict):
        summary["current_dataset"] = tstat.get("current_dataset")
        summary["final_status"] = {k: tstat.get(k) for k in _STATUS_KEYS}
    topo = render["/api/topology"].get("response")
    if isinstance(topo, dict):
        summary["topology_shape"] = {k: (len(v) if isinstance(v, list) else v) for k, v in topo.items() if k in ("nodes", "connections", "input_size", "output_size", "hidden_units", "num_hidden")}

    # generate: what juniper-data (the isolated leg, read only) holds that it did not before
    ids_after = _data_ids()
    new_ids = [i for i in ids_after if i not in set(ids_before)]
    metas = {i: get_json(f"{DATA}/v1/datasets/{i}") for i in new_ids}
    write_json(out / "data_new_datasets.json", {"ids_before": len(ids_before), "ids_after": len(ids_after), "new_ids": new_ids, "meta": metas})
    summary["generated"] = [
        {"dataset_id": i, "generator": (m.get("body") or {}).get("generator"), "generator_version": (m.get("body") or {}).get("generator_version"), "n_train": (m.get("body") or {}).get("n_train"), "n_val": (m.get("body") or {}).get("n_val"), "n_test": (m.get("body") or {}).get("n_test"), "n_features": (m.get("body") or {}).get("n_features"), "n_classes": (m.get("body") or {}).get("n_classes")}
        for i, m in metas.items()
    ]
    summary["log_slices"] = _save_log_slices(out, offsets)
    summary["case_wall_s"] = round(time.time() - t_case, 2)
    summary["finished_utc"] = utc_now()
    write_json(out / "index.json", rec.index)
    write_json(out / "summary.json", summary)
    brief = {k: summary.get(k) for k in ("case", "model_select", "caps", "stage", "start", "train_outcome", "train_wall_s", "render_status_codes", "history_len_before", "history_len_after", "history_new_rows", "metrics", "current_dataset", "generated", "final_status", "topology_shape", "effective_params_before")}
    print(redact(json.dumps(brief, indent=2, default=str)))
    print(f"wrote {out}")
    return 0


# --------------------------------------------------------------------------------------------------
# summarize: per-stage verdicts from the saved evidence (never from memory)
# --------------------------------------------------------------------------------------------------
_DATA_POST = re.compile(r'"POST /v1/datasets HTTP/1\.1" (\d{3})')
_DATA_ARTIFACT = re.compile(r'"GET /v1/datasets/([^/\s]+)/artifact HTTP/1\.1" (\d{3})')


def _load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text()) if path.exists() else None


def _verdicts(case_dir: pathlib.Path) -> dict[str, Any]:
    s = _load(case_dir / "summary.json") or {}
    value = s.get("value")
    generator = DS.generator_name_for_type(value) if value else None
    data_log = (case_dir / "logs" / "data.slice.log").read_text() if (case_dir / "logs" / "data.slice.log").exists() else ""
    posts = _DATA_POST.findall(data_log)
    artifacts = [(i, code) for i, code in _DATA_ARTIFACT.findall(data_log) if generator and i.startswith(f"{generator}-")]
    generated = [g for g in (s.get("generated") or []) if g.get("generator") == generator]
    row: dict[str, Any] = {"case": case_dir.name, "model": s.get("model"), "value": value, "generator": generator}

    # generate: a dataset of THIS generator came into existence (new id), or the run's own
    # create+download of it is in the data leg's log slice (an id minted earlier is re-served).
    if generated:
        g = generated[0]
        row["generate"] = ("PASS", f"{g['dataset_id']} train/val/test {g['n_train']}/{g['n_val']}/{g['n_test']}, {g['n_features']} feature(s)")
    elif artifacts and posts:
        row["generate"] = ("PASS", f"re-served {artifacts[0][0]} (POST /v1/datasets {posts[0]}, artifact GET {artifacts[0][1]})")
    else:
        row["generate"] = ("FAIL", f"no dataset of generator {generator!r}; data POSTs {posts}")

    stage = s.get("stage") or {}
    row["stage"] = ("PASS" if stage.get("status") == 200 else "FAIL", f"POST /api/stage_dataset -> {stage.get('status')}")

    start = s.get("start") or {}
    outcome = s.get("train_outcome")
    if outcome == "completed":
        fs = s.get("final_status") or {}
        row["train"] = ("PASS", f"{s.get('start_route')} -> {start.get('status')}; {fs.get('fsm_status')} ({fs.get('completion_reason')}) in {s.get('train_wall_s')} s")
    else:
        detail = start.get("response")
        row["train"] = ("FAIL", f"{s.get('start_route')} -> {start.get('status')}: {json.dumps(detail)[:300]}")

    codes = s.get("render_status_codes") or {}
    hist_after = s.get("history_len_after") or 0
    ds_view = s.get("dataset_view") if isinstance(s.get("dataset_view"), dict) else {}
    tied = False
    tie_note = ""
    if s.get("model") == "recurrence":
        tied = str(ds_view.get("dataset_name", "")).startswith(f"{generator}-")
        tie_note = f"/api/dataset names {ds_view.get('dataset_name')}"
    else:
        gen_feats = generated[0]["n_features"] if generated else None
        cur = (s.get("current_dataset") or {}).get("dataset_type")
        feats_ok = gen_feats is None or ds_view.get("num_features") == gen_feats
        tied = cur in (value, generator) and feats_ok and outcome == "completed"
        tie_note = f"current_dataset={cur}, /api/dataset num_features={ds_view.get('num_features')}"
    shots = sorted(case_dir.glob("dashboard*_timeline.json"), key=lambda p: p.stat().st_mtime)
    shot = _load(shots[-1]) if shots else {}
    shot_status = ((shot.get("samples") or [{}])[-1]).get("top_status") if shot else None
    render_ok = codes.get("/api/metrics") == 200 and codes.get("/api/metrics/history?limit=0") == 200 and codes.get("/api/dataset") == 200 and hist_after > 0 and tied
    detail = f"history {s.get('history_len_before')}->{hist_after} rows; {tie_note}; dashboard status bar at last sample ({shots[-1].name if shots else 'no capture'}): {shot_status!r}"
    if outcome != "completed":
        row["render"] = ("N/A", "no run to render -- " + detail)
    else:
        row["render"] = ("PASS" if render_ok else "FAIL", detail)

    m = s.get("metrics") if isinstance(s.get("metrics"), dict) else {}
    if "r2" in m:
        row["final_metric"] = f"r2={m['r2']:.4g} mse={m.get('mse', float('nan')):.3g}"
    elif isinstance(m.get("metrics"), dict):
        mm = m["metrics"]
        final = ((m.get("eval_metrics") or {}).get("final") or {})
        row["final_metric"] = f"loss={mm.get('loss', float('nan')):.4g} train_acc={mm.get('accuracy', float('nan')):.4g} val_acc={mm.get('val_accuracy', float('nan')):.4g} test_f1={final.get('f1', float('nan')):.3g}; hidden={(m.get('network_topology') or {}).get('hidden_units')}"
    row["train_wall_s"] = s.get("train_wall_s")
    row["case_wall_s"] = s.get("case_wall_s")
    return row


def cmd_summarize(_args: argparse.Namespace) -> int:
    rows = [_verdicts(d) for d in sorted(EVIDENCE.iterdir()) if d.is_dir() and (d / "summary.json").exists()]
    write_json(EVIDENCE / "verdicts.json", rows)
    for r in rows:
        print(f"{r['case']:32s} {r['model']:10s} gen={r['generate'][0]} stage={r['stage'][0]} train={r['train'][0]} render={r['render'][0]} wall={r['train_wall_s']} {r.get('final_metric', '')}")
        for stage_name in ("generate", "stage", "train", "render"):
            print(f"    {stage_name:8s} {r[stage_name][1]}")
    return 0


# --------------------------------------------------------------------------------------------------
# slim + archive-logs: keep the evidence reviewable (the raw capture was 61 MB)
# --------------------------------------------------------------------------------------------------
_CANDIDATE_CHATTER = re.compile(r"^\+?\[candidate_unit\.py:")


def _slim_value(obj: Any) -> tuple[Any, bool]:
    """Truncate the three bulky shapes, marking every cut: a metrics history list (keep first 3 /
    last 20), /api/dataset's echoed ``inputs`` / ``targets`` arrays, and decision-boundary grids."""
    changed = False
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key == "history" and isinstance(value, list) and len(value) > 25:
                out[key] = {"_truncated_by_a_n2_slim": True, "count": len(value), "first_3": value[:3], "last_20": value[-20:]}
                changed = True
            elif key in ("inputs", "targets", "xx", "yy", "Z", "z", "grid", "predictions") and isinstance(value, list) and len(value) > 5:
                width = len(value[0]) if value and isinstance(value[0], list) else None
                out[key] = {"_truncated_by_a_n2_slim": True, "rows": len(value), "cols": width, "first_3": value[:3]}
                changed = True
            else:
                sub, sub_changed = _slim_value(value)
                out[key] = sub
                changed = changed or sub_changed
        return out, changed
    if isinstance(obj, list):
        items = []
        for item in obj:
            sub, sub_changed = _slim_value(item)
            items.append(sub)
            changed = changed or sub_changed
        return items, changed
    return obj, False


def _slim_log(path: pathlib.Path, cap: int = 1_000_000) -> None:
    lines = path.read_text().splitlines()
    kept = [ln for ln in lines if not _CANDIDATE_CHATTER.search(ln)]
    dropped = len(lines) - len(kept)
    text = "\n".join(kept)
    note = f"# a_n2 slim: dropped {dropped} per-candidate-epoch lines ([candidate_unit.py:...] INFO chatter) of {len(lines)}"
    if len(text) > cap:
        text = text[: cap // 3] + "\n...[middle elided by a_n2 slim]...\n" + text[-(2 * cap) // 3 :]
        note += f"; middle elided to cap at ~{cap} bytes"
    path.write_text(note + "\n" + text + "\n")


def cmd_slim(_args: argparse.Namespace) -> int:
    before = sum(p.stat().st_size for p in EVIDENCE.rglob("*") if p.is_file())
    for path in sorted(EVIDENCE.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except ValueError:
            continue
        slim, changed = _slim_value(data)
        if changed:
            path.write_text(json.dumps(slim, indent=2, default=str) + "\n")
    for path in sorted(EVIDENCE.rglob("cascor*.log")):
        if path.stat().st_size > 200_000 and not path.read_text()[:20].startswith("# a_n2 slim"):
            _slim_log(path)
    after = sum(p.stat().st_size for p in EVIDENCE.rglob("*") if p.is_file())
    print(f"evidence: {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB")
    return 0


def cmd_archive_logs(_args: argparse.Namespace) -> int:
    """Copy the four full service logs into 00_stack/logs (redacted; cascor's slimmed) before --down."""
    dest = EVIDENCE / "00_stack" / "logs"
    dest.mkdir(parents=True, exist_ok=True)
    for leg in PORTS:
        src = LOG_DIR / f"juniper-{leg}.log"
        if src.exists():
            (dest / src.name).write_text(redact(src.read_text(errors="replace")))
    cascor = dest / "juniper-cascor.log"
    if cascor.exists():
        _slim_log(cascor, cap=2_000_000)
    for p in sorted(dest.iterdir()):
        print(f"{p.name}: {p.stat().st_size} bytes")
    return 0


# --------------------------------------------------------------------------------------------------
# postflight
# --------------------------------------------------------------------------------------------------
def cmd_postflight(_args: argparse.Namespace) -> int:
    report: dict[str, Any] = {"recorded_utc": utc_now()}
    report["my_ports"] = {port: listener_pid(port) for port in PORTS.values()}
    report["my_ports_free"] = all(v is None for v in report["my_ports"].values()) and not listener_lines(list(PORTS.values()))
    report["protected"] = {}
    for pid, port in PROTECTED.items():
        alive = pathlib.Path(f"/proc/{pid}").exists()
        report["protected"][str(pid)] = {"expected_port": port, "alive": alive, "listening_pid_on_port": listener_pid(port), "listening_matches": listener_pid(port) == pid, "cmdline": proc_info(pid).get("cmdline") if alive else None}
    report["ss_relevant_ports"] = listener_lines([8101, 8202, 8051, 8055, 8056, 8111, 8212, 8061, 8221, 8211])
    out = EVIDENCE / "99_postflight" / "postflight.json"
    write_json(out, report)
    print(json.dumps(report, indent=2))
    return 0 if report["my_ports_free"] and all(v["listening_matches"] for v in report["protected"].values()) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("provenance")
    sub.add_parser("postflight")
    sub.add_parser("summarize")
    sub.add_parser("slim")
    sub.add_parser("archive-logs")
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("case", choices=sorted(CASES))
    run.add_argument("--tag", default="", help="suffix for the evidence dir (a second observation of the same case)")
    run.add_argument("--start-route", choices=("start", "restart-fresh"), default="start")
    run.add_argument("--no-caps", action="store_true", help="skip /api/set_params (e.g. no network exists yet)")
    run.add_argument("--timeout", type=float, default=900.0)
    run.add_argument("--stop-on-timeout", action="store_true")
    run.add_argument("--start-anyway", action="store_true", help="press Start even if staging failed")
    args = parser.parse_args()
    if args.cmd == "provenance":
        return cmd_provenance(args)
    if args.cmd == "postflight":
        return cmd_postflight(args)
    if args.cmd == "summarize":
        return cmd_summarize(args)
    if args.cmd == "slim":
        return cmd_slim(args)
    if args.cmd == "archive-logs":
        return cmd_archive_logs(args)
    if args.cmd == "list":
        for name, case in CASES.items():
            print(f"{name:28s} {case['model']:11s} {case['value']:15s} seed={MR.dataset_default_params(case['value'])} one-shot={_oneshot_body(case)}")
        return 0
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
