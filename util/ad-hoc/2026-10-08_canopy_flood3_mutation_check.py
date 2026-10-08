"""
Mutation-check the juniper-canopy tests carried by Cursor flood #3 against current ``main``.

Each mutation edits ONE production (or workflow) file in a canopy checkout, runs the named
test files, and records whether they failed (killed) or passed (survived). The original
bytes are restored after every mutation and verified by sha256, so the checkout ends exactly
as it began. ``PYTHONDONTWRITEBYTECODE=1`` keeps a mutated module from being cached as a
``.pyc`` that a same-second, same-size restore could leave stale.

Usage:
    python3 2026-10-08_canopy_flood3_mutation_check.py \
        --repo /path/to/juniper-canopy-worktree \
        --python /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        --out results.json [--only 699,701]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation (Cursor flood #3 evaluation, canopy test slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy #699 #701 #704 #707 #715 #718 #719 #720 #721 #724 #727 #728
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - runs pytest with a fixed argv
import sys
import time
from pathlib import Path

RP = "src/frontend/components/replay_player_panel.py"
DM = "src/frontend/dashboard_manager.py"
RSA = "src/backend/recurrence_service_adapter.py"
DS = "src/dataset_schema.py"
MAIN = "src/main.py"
SERVES = "util/check_image_serves.py"
IMAGE_SCAN = "util/check_image_no_secrets.py"
BUDGET = ".github/workflows/pr-budget-alarm.yml"
SEQ = ".github/workflows/sequence-safety.yml"
MV = ".github/workflows/main-verify.yml"
SMOKE = "util/wheel_import_smoke.py"
PYPROJECT = "pyproject.toml"

T699 = ["src/tests/unit/frontend/test_replay_echo_shape_guards.py"]
T701 = ["src/tests/unit/frontend/test_replay_echo_zero_and_shape_edges.py"]
T704 = ["src/tests/unit/test_recurrence_detail_cut_edges.py"]
T707 = ["src/tests/regression/test_generator_spelling_fails_closed.py", "src/tests/unit/test_dataset_schema_falsy_seeds_and_bounds.py"]
T715 = ["src/tests/unit/test_check_image_serves_driver.py"]
T718S = ["src/tests/unit/test_check_image_no_secrets.py"]
T718B = ["src/tests/unit/test_pr_budget_alarm.py"]
T719 = ["src/tests/unit/frontend/test_replay_control_result_guards.py"]
T720 = ["src/tests/regression/test_stage_payload_falsy_edges.py"]
T721 = ["src/tests/unit/test_wheel_import_smoke.py"]
T724 = ["src/tests/unit/test_recurrence_version_rate_edges.py"]
T727H = ["src/tests/unit/test_sequence_safety_label_hatch.py"]
T727V = ["src/tests/unit/test_main_verify_screen_verdicts.py"]
T727N = ["src/tests/unit/test_main_verify_notify_upsert.py"]
T728 = ["src/tests/regression/test_empty_axis_commit_and_restage_zeros.py"]

# (id, pr, file, old, new, tests, what)
MUTATIONS = [
    ("699a", 699, RP, 'if value is None or float(value) == float(summary.get("speed", SPEED_DEFAULT)):', 'if not value or float(value) == float(summary.get("speed", SPEED_DEFAULT)):', T699, "speed echo guard uses truthiness (0 is pause)"),
    ("699b", 699, RP, 'float(value) == float(summary.get("speed", SPEED_DEFAULT))', 'float(value) == float(session.get("speed", summary.get("speed", SPEED_DEFAULT)))', T699, "speed echo reads a stale top-level speed first"),
    ("699c", 699, RP, "lo, hi = int(raw[0]), int(raw[1])", "lo, hi = int(raw[0]), int(raw[1]) - 1", T699, "legacy list range treated as exclusive"),
    ("699d", 699, RP, 'start = int(unified.get("start_epoch", 0))', "start = 0", T699, "snapshot_window start_epoch dropped"),
    ("701a", 701, RP, 'end = int(unified.get("end_epoch", start + 1)) - 1', 'end = int(unified.get("end_epoch", session.get("length", start + 1))) - 1', T701, "missing end_epoch filled from length"),
    ("701b", 701, RP, 'unified = ti.get("snapshot_window") if isinstance(ti, dict) else None', 'unified = ti.get("snapshot_window")', T701, "int time_index asked for snapshot_window"),
    ("701c", 701, RP, '        if unified:\n            start = int(unified.get("start_epoch", 0))', '        if unified is not None:\n            start = int(unified.get("start_epoch", 0))', T701, "empty snapshot_window treated as present"),
    ("704a", 704, RSA, "    if detail is None:\n        return None\n    if isinstance(detail, str):", "    if not detail:\n        return None\n    if isinstance(detail, str):", T704, "falsy detail dropped by truthiness"),
    ("704b", 704, RSA, 'if isinstance(item, Mapping) and item.get("msg") is not None:', 'if isinstance(item, Mapping) and item.get("msg"):', T704, "falsy msg falls through to str(item) with input"),
    ("704c", 704, DM, "        if len(collapsed) > max_chars:\n            return collapsed[: max_chars - 1].rstrip()", "        if len(collapsed) >= max_chars:\n            return collapsed[: max_chars - 1].rstrip()", T704, "status-bar bound off by one"),
    ("704d", 704, DM, 'return collapsed[: max_chars - 1].rstrip() + "…"', 'return collapsed[: max_chars - 1] + "…"', T704, "label cut keeps a trailing space"),
    ("707a", 707, MAIN, "value = dataset_type_for_generator_name(dataset_value, [d.value for d in DATASET_TYPES])", "value = dataset_value if dataset_value in [d.value for d in DATASET_TYPES] else None", T707, "stage/live-swap resolver drops the generator-name alias"),
    ("707b", 707, DS, "if field_.name in seeded else field_ for field_ in fields]", "if seeded.get(field_.name) else field_ for field_ in fields]", T707, "seed overlay uses truthiness"),
    ("707c", 707, DS, "            if isinstance(value, (int, float)) and not isinstance(value, bool):\n                return value", "            if value and isinstance(value, (int, float)) and not isinstance(value, bool):\n                return value", T707, "zero bound treated as absent"),
    ("707d", 707, MAIN, 'raw = pending.get("nn_dataset_type") or pending.get("dataset_type")', 'raw = pending.get("dataset_type") or pending.get("nn_dataset_type")', T707, "pending dialect precedence swapped"),
    ("715a", 715, SERVES, 'if running != "true":', 'if running.lower() != "true":', T715, "inspect accepts True"),
    ("715b", 715, SERVES, "cid = out.splitlines()[-1].strip()", "cid = out.splitlines()[0].strip()", T715, "container id read from the first line"),
    ("715c", 715, SERVES, "versions = json.loads(out.splitlines()[-1])", "versions = json.loads(out.splitlines()[0])", T715, "version probe parses the first line"),
    ("718a", 718, IMAGE_SCAN, "    if files_seen == 0:", "    if files_seen < 0:", T718S, "empty scan passes"),
    ("718b", 718, IMAGE_SCAN, "dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]", "dirnames[:] = list(dirnames)", T718S, "cache dirs not pruned"),
    ("718c", 718, BUDGET, 'select(.headRefName | startswith("cursor/"))', 'select(.headRefName | startswith("cursor"))', T718B, "cursor prefix loosened"),
    ("718d", 718, BUDGET, 'warn="${PR_BUDGET_WARN:-15}"', 'warn="${PR_BUDGET_WARN-15}"', T718B, "empty warn variable not defaulted"),
    ("719a", 719, RP, "if isinstance(cur, (int, float)) and not isinstance(cur, bool):", "if isinstance(cur, (int, float)):", T719, "bool accepted as an index"),
    ("719b", 719, RP, '        if "paused" in result:\n            session["playing"] = not bool(result["paused"])', '        if True:\n            session["playing"] = not bool(result.get("paused"))', T719, "missing paused starts playback"),
    ("719c", 719, RP, '        fsm = payload.get("fsm_state")\n        if fsm:', '        fsm = payload.get("fsm_state")\n        if "fsm_state" in payload:', T719, "falsy fsm_state written"),
    ("719d", 719, RP, '            if not result["success"]:\n                return self._error_status(result["error"]), dash.no_update\n\n            new_session = self._merge_session(', '            if not result["success"] and action != "stop":\n                return self._error_status(result["error"]), dash.no_update\n\n            new_session = self._merge_session(', T719, "refused Stop still clears the session"),
    ("720a", 720, DM, "                if _value is not None:\n                    payload[_key] = _value", "                if _value:\n                    payload[_key] = _value", T720, "spiral zeros dropped"),
    ("720b", 720, DM, 'if not name or name in exclude or value is None or value == "":', "if not name or name in exclude or not value:", T720, "operator False dropped as blank"),
    ("720c", 720, DM, '            if not isinstance(gen_id, dict):\n                continue\n            name = gen_id.get("name")', '            name = gen_id.get("name")', T720, "non-dict control id raises"),
    ("721a", 721, PYPROJECT, '    "observability",\n    "outbound_errors",\n    "provenance",', '    "observability",\n    "provenance",', T721, "py-modules loses outbound_errors (main's state before #721)"),
    ("721b", 721, SMOKE, '    "observability",\n    "outbound_errors",\n    "provenance",', '    "observability",\n    "provenance",', T721, "smoke list loses outbound_errors"),
    ("721c", 721, SMOKE, 'and (cwd / "juniper_canopy" / "__init__.py").is_file() and (cwd / "src").is_dir():', 'and ((cwd / "juniper_canopy" / "__init__.py").is_file() or (cwd / "src").is_dir()):', T721, "cwd guard becomes an OR"),
    ("721d", 721, SMOKE, 'if origin != "<namespace>" and "site-packages" not in origin:', "if False:", T721, "a checkout import counts as success"),
    ("724a", 724, RSA, '        version = _version_text(self._call("GET", "/v1/health", self._status_timeout).get("version"))\n', '        try:\n            version = _version_text(self._call("GET", "/v1/health", self._status_timeout).get("version"))\n        except RecurrenceServiceError:\n            version = None\n', T724, "a failed health read falls through to openapi"),
    ("724b", 724, RSA, "{' s' if retry_after.isdigit() else ''}", "{' s' if retry_after.lstrip('+-').replace('.', '', 1).isdigit() else ''}", T724, "signed / fractional Retry-After labelled in seconds"),
    ("724c", 724, RSA, "return self.state in MODEL_PRESENT_STATES", "return str(self.state).strip().lower() in MODEL_PRESENT_STATES", T724, "model_present case-folds and strips"),
    ("727a", 727, SEQ, "grep -qx 'allow-symbol-loss'", "grep -q 'allow-symbol-loss'", T727H, "label match loses -x"),
    ("727b", 727, MV, '          if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then\n            echo "::error::sequence-safety screen invocation error (symbol=', '          if [ "${src}" -ge 3 ] || [ "${drc}" -ge 3 ]; then\n            echo "::error::sequence-safety screen invocation error (symbol=', T727V, "exit 2 read as screened"),
    ("727c", 727, MV, "map(select(.pull_request == null) | select(.title == env.TITLE))", "map(select(.title == env.TITLE))", T727N, "tracker match ignores pull_request"),
    ("727d", 727, MV, '          if [ "${src}" -ge 1 ] || [ "${drc}" -ge 1 ]; then\n            echo "::error::post-merge compositional-loss', '          if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then\n            echo "::error::post-merge compositional-loss', T727V, "clean assert treats a finding as green"),
    ("728a", 728, DM, '        if selection_axis_unset(dtype):\n            return False, "No dataset selected', '        if dtype is None:\n            return False, "No dataset selected', T728, "restage refuses only None"),
    ("728b", 728, DM, "            value = dataset_vals.get(key)\n            if value is not None:\n                payload[pkey] = value", "            value = dataset_vals.get(key)\n            if value:\n                payload[pkey] = value", T728, "restage drops zeros"),
    ("728c", 728, DM, "            if resp.status_code != 200:\n                return None\n            data = resp.json()", "            data = resp.json()", T728, "pending read fails open on non-200"),
    ("728d", 728, DM, "        if selection_axis_unset(dataset_type):\n            return False, dbc.Alert(", "        if dataset_type is None:\n            return False, dbc.Alert(", T728, "Apply refuses only None"),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _env() -> dict:
    env = dict(os.environ)
    # What the JuniperCanopy1 activate hook does: keep the rust_mudgeon libtorch off the loader path.
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LIBTORCH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _pytest(repo: Path, python: str, tests: list[str]) -> tuple[int, str]:
    argv = [python, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "--no-header", *tests]
    proc = subprocess.run(argv, cwd=repo, env=_env(), capture_output=True, text=True, timeout=900, check=False)  # nosec B603
    tail = [line for line in (proc.stdout + proc.stderr).splitlines() if line.strip()][-3:]
    return proc.returncode, " | ".join(tail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", default="", help="comma-separated PR numbers")
    args = parser.parse_args()
    only = {int(x) for x in args.only.split(",") if x.strip()}
    selected = [m for m in MUTATIONS if not only or m[1] in only]

    # Baseline: every targeted suite must be green before any mutation means anything.
    all_tests = sorted({t for m in selected for t in m[5]})
    code, tail = _pytest(args.repo, args.python, all_tests)
    print(f"baseline: exit={code} :: {tail}", flush=True)
    if code != 0:
        print("baseline is not green; refusing to score mutations", file=sys.stderr)
        return 2

    results = []
    for mid, pr, rel, old, new, tests, what in selected:
        path = args.repo / rel
        original = path.read_bytes()
        before = _sha(path)
        text = original.decode("utf-8")
        count = text.count(old)
        if count != 1:
            results.append({"id": mid, "pr": pr, "file": rel, "what": what, "status": f"ANCHOR-COUNT-{count}"})
            print(f"{mid} PR#{pr} ANCHOR-COUNT-{count} {rel}", flush=True)
            continue
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            started = time.monotonic()
            code, tail = _pytest(args.repo, args.python, tests)
            elapsed = time.monotonic() - started
        finally:
            path.write_bytes(original)
        restored = _sha(path) == before
        status = "KILLED" if code != 0 else "SURVIVED"
        results.append({"id": mid, "pr": pr, "file": rel, "what": what, "status": status, "pytest_exit": code, "tail": tail, "restored": restored, "seconds": round(elapsed, 1)})
        print(f"{mid} PR#{pr} {status} exit={code} restored={restored} ({what}) :: {tail}", flush=True)
        if not restored:
            print(f"RESTORE FAILED for {rel}; stopping", file=sys.stderr)
            break

    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    killed = sum(r["status"] == "KILLED" for r in results)
    print(f"\n{killed}/{len(results)} killed; results -> {args.out}")
    return 0 if all(r.get("restored", True) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
