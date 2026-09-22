#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   experiments
# File Name:     run_suite.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Sequential multi-run experiment suite driver (CLI experimentation plan §13.1/§13.2, Wave 7.1).
#   Expands a suite YAML (base configs × a dotted-path override matrix + include/exclude) into an
#   ordered cell list, materialises each cell as a standalone driver-validated experiment YAML,
#   executes cells sequentially (per-cell experiment_stack --up → run_experiment → --down), records
#   each outcome in the append-only SUITE_DIR/registry.jsonl + the global RUN_ROOT/index.jsonl, and
#   aggregates into aggregate.csv + REPORT.md + suite_manifest.json. Wave 7.5 adds bounded
#   parallelism (execution.mode: parallel + max_parallel; H-11 thread-budget split recorded per
#   cell; cascor parallel>1 still refused from one checkout — Q-6's override landed (cascor#523) but
#   run_suite cannot verify the installed cascor honours it (H-7) — recurrence is free).
#####################################################################################################################################################################################################
"""Run an experiment suite (sequential, or bounded-parallel for recurrence).

Usage:
    python util/experiments/run_suite.py --suite SUITE.yaml [--dry-run] [--resume SUITE_ID]
                                         [--only CELL_ID ...]

Exit codes: 0 = every executed cell succeeded; 1 = suite completed with failed
cells (or aggregation found none succeeded); 2 = misuse / suite-validation error.

Test seams: ``JUNIPER_SUITE_LAUNCHER`` / ``JUNIPER_SUITE_DRIVER`` override the
launcher script and driver script paths; ``JUNIPER_SUITE_PYTHON`` overrides the
interpreter used for the driver (defaults to this interpreter).

``JUNIPER_SUITE_GRAFANA_BRIDGE=1`` adds ``--grafana-bridge`` to every ``--up``, so the
run's metrics are scraped into Prometheus (socat relay + file_sd target). Off by default:
without it a run is UNSCRAPED and ``metrics_scraped.scrape_confirmed`` is ``false``.
It is an env toggle rather than a suite key on purpose — see ``execute_cell``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import yaml

# `util/` on the path so `from experiments import ...` resolves whether this file is run as a
# script (sys.path[0] = util/experiments) or imported as a module. Without it the sibling imports
# in _gate_metrics / _run_comparison raise ImportError and their features degrade to blank
# columns -- silently, which is how a feature ships doing nothing.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LAUNCHER = REPO_ROOT / "util" / "experiment_stack.bash"
DEFAULT_DRIVER = Path(__file__).resolve().parent / "run_experiment.py"
DEFAULT_RUN_ROOT = Path(os.environ.get("JUNIPER_EXP_RUN_ROOT", str(Path.home() / ".local" / "state" / "juniper-experiments")))

RUN_ID_BANNER = re.compile(r"Experiment run (\S+) is up")

SUITE_KEYS = frozenset({"schema_version", "suite", "execution", "matrix", "include", "exclude", "outputs"})
SUITE_SUITE_KEYS = frozenset({"name", "description", "app", "base_config", "seed_policy"})
EXECUTION_KEYS = frozenset({"mode", "max_parallel", "continue_on_failure", "per_run_timeout_seconds", "stall_seconds", "max_wall_seconds"})
TERMINAL_OUTCOMES = frozenset({"succeeded", "failed", "stalled", "timed_out"})


class SuiteError(Exception):
    """Suite-validation misuse — exits 2."""


def _sha8(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()[:8]


def _require_mapping(doc: dict, key: str) -> None:
    """`doc[key]`, if present and non-empty, must be a mapping.

    Absent / None / empty stays legal -- every caller writes `doc.get(key) or {}` and an empty
    block is a valid suite. What must not pass is a TRUTHY NON-MAPPING, which is exactly what
    the falsy guard lets through.
    """
    value = doc.get(key)
    if value and not isinstance(value, dict):
        raise SuiteError(f"{key}: must be a mapping, got {type(value).__name__}")


def _require_sequence(doc: dict, key: str) -> None:
    """`doc[key]`, if present and non-empty, must be a list -- not a mapping or a string.

    A string is the trap worth naming: `exclude: foo` iterates as CHARACTERS, so the
    per-entry check downstream reports "entries must be non-empty mappings" about letters.
    """
    value = doc.get(key)
    if value and not isinstance(value, list):
        raise SuiteError(f"{key}: must be a list, got {type(value).__name__}")


def load_suite(path: Path) -> dict:
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise SuiteError(f"cannot read suite YAML {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SuiteError("suite YAML must be a mapping")
    unknown = set(doc) - SUITE_KEYS
    if unknown:
        raise SuiteError(f"unknown top-level suite keys: {sorted(unknown)}")
    if doc.get("schema_version") != 1:
        raise SuiteError("schema_version must be 1")
    # `or {}` is a FALSY guard, not a TYPE guard: it fixes None and {} and passes a value that
    # is truthy and not a mapping straight through. This function type-checks `doc` itself two
    # lines above and then trusted `or {}` for every nested block, so a suite whose `suite:` is
    # a LIST reached `set(suite) - SUITE_SUITE_KEYS` and died with
    # `TypeError: unhashable type: 'dict'` -- an internal traceback from the one function whose
    # entire job is to turn malformed operator YAML into a clean SuiteError. Reproduced before
    # this fix on `schema_version: 1` + `suite:` as a two-item list.
    _require_mapping(doc, "suite")
    _require_mapping(doc, "execution")
    _require_mapping(doc, "matrix")
    _require_mapping(doc, "outputs")
    _require_sequence(doc, "include")
    _require_sequence(doc, "exclude")
    suite = doc.get("suite") or {}
    unknown = set(suite) - SUITE_SUITE_KEYS
    if unknown:
        raise SuiteError(f"unknown suite: keys: {sorted(unknown)}")
    if suite.get("app") not in ("cascor", "recurrence"):
        raise SuiteError("suite.app must be 'cascor' or 'recurrence'")
    if not suite.get("name"):
        raise SuiteError("suite.name is required")
    base = suite.get("base_config") or []
    if not isinstance(base, list) or not base:
        raise SuiteError("suite.base_config must be a non-empty list")
    seed_policy = suite.get("seed_policy", "fixed")
    if seed_policy not in ("fixed", "per_cell"):
        raise SuiteError("suite.seed_policy must be 'fixed' or 'per_cell'")
    execution = doc.get("execution") or {}
    unknown = set(execution) - EXECUTION_KEYS
    if unknown:
        raise SuiteError(f"unknown execution: keys: {sorted(unknown)}")
    mode = execution.get("mode", "sequential")
    if mode not in ("sequential", "parallel"):
        raise SuiteError("execution.mode must be 'sequential' or 'parallel'")
    max_parallel = int(execution.get("max_parallel", 1))
    if max_parallel < 1:
        raise SuiteError("execution.max_parallel must be >= 1")
    return doc


def check_cascor_parallel_floor(doc: dict) -> None:
    """Refuse a parallel cascor suite whose LAUNCH tree is below the Q-6 version floor.

    Wave 7.5 / Q-6: cascor's file logger targets the shared checkout logs/juniper_cascor.log
    (H-7); N parallel cascor instances from ONE checkout race it, and because that file is the
    ONLY place the parent logger writes, the race destroys run evidence rather than merely
    interleaving it. Recurrence suites parallelise freely.

    The blanket refusal is LIFTED as of cascor 0.10.0 (2026-08-30), the first release carrying
    the JUNIPER_CASCOR_LOG_DIR override (cascor#523) that experiment_stack.bash exports per run.
    What replaces it is the version floor the old comment demanded — read from the tree that will
    actually be LAUNCHED, not from the driver's own environment.

    FAILS CLOSED. An undeterminable version refuses, because "we could not read it" and "it is
    new enough" must not resolve the same way: the failure this guards is silent, so a guard that
    defaults to permissive would restore the exact race it exists to prevent.

    **Why this is NOT part of ``load_suite``** (owner decision D5, 2026-09-11;
    ``notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md``).
    ``tests/test_experiment_suite_yamls.py::test_every_suite_loads`` calls ``load_suite`` on every
    checked-in suite. CI clones only juniper-ml, so ``_cascor_tree_version()`` finds no sibling,
    returns ``None``, and this check fires — turning the R-6 drift gate **red on every CI run**
    for a suite that is perfectly valid and passes locally. Structural validation ("is this YAML
    well-formed?") must not depend on a sibling repo being present; "may this suite launch here
    and now?" legitimately does. Splitting the two is what lets a parallel cascor suite live under
    ``suites/perf/``.

    The guard itself is unchanged in strength: ``main`` calls this before any cell is
    materialised or launched, and before ``--dry-run`` prints its plan, so an operator sees the
    same refusal at the same point in the workflow as when it lived in ``load_suite``.
    """
    suite = doc.get("suite") or {}
    execution = doc.get("execution") or {}
    mode = execution.get("mode", "sequential")
    max_parallel = int(execution.get("max_parallel", 1))
    if not (mode == "parallel" and max_parallel > 1 and suite.get("app") == "cascor"):
        return
    version, how = _cascor_tree_version()
    if version is None:
        raise SuiteError(
            f"app: cascor with max_parallel > 1 needs a verifiable cascor >= "
            f"{'.'.join(map(str, CASCOR_PARALLEL_FLOOR))} (JUNIPER_CASCOR_LOG_DIR, cascor#523), "
            f"and the version could not be read: {how}. Refusing rather than assuming — the "
            f"shared-log race (Q-6 / H-7) destroys run evidence silently. Use mode: sequential."
        )
    if version < CASCOR_PARALLEL_FLOOR:
        raise SuiteError(
            f"app: cascor with max_parallel > 1 needs cascor >= "
            f"{'.'.join(map(str, CASCOR_PARALLEL_FLOOR))}; the tree that will run is "
            f"{'.'.join(map(str, version))} ({how}). Below that floor "
            f"JUNIPER_CASCOR_LOG_DIR is silently ignored and parallel cells race the shared "
            f"logs/juniper_cascor.log (Q-6 / H-7). Use mode: sequential, or point "
            f"JUNIPER_EXP_CASCOR_SRC_DIR at a tree >= the floor."
        )


#: Q-6: the first cascor release carrying JUNIPER_CASCOR_LOG_DIR (cascor#523, published
#: 2026-08-30). Below this the export is silently ignored and parallel cells race the shared
#: logs/juniper_cascor.log — the H-7 evidence-destroying race, with no signal that it happened.
CASCOR_PARALLEL_FLOOR = (0, 10, 0)


def _cascor_tree_version() -> "tuple[tuple | None, str]":
    """Version of the cascor tree the stack will LAUNCH, and how it was resolved.

    Returns ``(version_tuple_or_None, description)``.

    **Not** ``importlib.metadata.version("juniper-cascor")``. That reads the DRIVER's
    environment, which is not necessarily what runs: ``experiment_stack.bash`` launches uvicorn
    with the cascor tree as CWD, and ``JuniperCascor1``'s editable finder registers itself with
    ``sys.meta_path.append`` — *after* the default ``PathFinder`` — so CWD wins and the installed
    distribution is only a fallback (measured, ml#1488). A metadata read would therefore be a
    vacuous check: it can report a compliant version while a pinned worktree runs an older tree.

    Resolution mirrors ``experiment_stack.bash:112`` exactly, so the version reported here is the
    version of the code that will actually serve the run.
    """
    src = os.environ.get("JUNIPER_EXP_CASCOR_SRC_DIR", "").strip()
    project = os.environ.get("JUNIPER_EXP_PROJECT_DIR", "").strip()
    if src:
        tree, how = Path(src).parent, "JUNIPER_EXP_CASCOR_SRC_DIR"
    elif project:
        tree, how = Path(project) / "juniper-cascor", "JUNIPER_EXP_PROJECT_DIR"
    else:
        # No fixed parent depth. From the canonical checkout the ecosystem root is parents[3],
        # but from a session worktree the same index lands on `.../.claude/worktrees` — the trap
        # experiment_stack.bash calls out at its own PROJECT_DIR resolution, and which the first
        # version of this function walked straight into. Probe upward for the ancestor that
        # actually contains a juniper-cascor sibling instead of asserting a layout.
        tree, how = None, "ancestor probe (no JUNIPER_EXP_* override set)"
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "juniper-cascor"
            if (candidate / "pyproject.toml").is_file():
                tree, how = candidate, "ancestor probe"
                break
        if tree is None:
            return None, f"{how}: no juniper-cascor sibling found above {Path(__file__).resolve()}"
    pyproject = tree / "pyproject.toml"
    if not pyproject.is_file():
        return None, f"{how} -> {tree} (no pyproject.toml)"
    m = re.search(r'(?m)^version\s*=\s*"([0-9]+(?:\.[0-9]+)*)"', pyproject.read_text(encoding="utf-8"))
    if not m:
        return None, f"{how} -> {tree} (no static version in pyproject.toml)"
    return tuple(int(p) for p in m.group(1).split(".")), f"{how} -> {tree} @ {m.group(1)}"


def _resolve_base_config(suite_path: Path, config_rel: str) -> Path:
    """Resolve a base_config entry relative to the suite file.

    Sibling-repo references (``../../../../juniper-cascor/...``) assume the
    canonical ecosystem layout; from a session worktree the relative walk lands
    outside the ecosystem. When ``JUNIPER_EXP_PROJECT_DIR`` is set (the launcher's
    own worktree override), the path is rebased onto it from its first
    ``juniper-*`` component.

    The override WINS over a literal walk that happens to resolve. It used to be
    consulted only when the literal missed, which made it an override in name and a
    fallback in fact: launched from the canonical juniper-ml checkout the literal
    always resolves, so a campaign that pinned cascor to a worktree would silently
    take its CODE from the worktree and its CONFIG from the primary. That mixed tree
    is worse than either pure one, and nothing in the manifest would have shown it.
    An override that does not exist on disk still falls back, so a stale or
    mistyped ``JUNIPER_EXP_PROJECT_DIR`` degrades rather than hard-failing the suite.
    """
    literal = (suite_path.parent / config_rel).resolve()
    project_dir = os.environ.get("JUNIPER_EXP_PROJECT_DIR", "").strip()
    if project_dir:
        parts = Path(config_rel).parts
        for i, part in enumerate(parts):
            if part.startswith("juniper-"):
                rebased = (Path(project_dir) / Path(*parts[i:])).resolve()
                if rebased.exists():
                    return rebased
                break
    return literal


def _set_dotted(config: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    node = config
    for part in parts[:-1]:
        nxt = node.get(part)
        if nxt is None:
            nxt = {}
            node[part] = nxt
        if not isinstance(nxt, dict):
            raise SuiteError(f"override path {dotted!r} crosses non-mapping node {part!r}")
        node = nxt
    node[parts[-1]] = value


def expand_cells(doc: dict, suite_path: Path) -> "list[dict]":
    """Ordered cell list: configs × matrix product, minus exclude, plus include."""
    suite = doc["suite"]
    matrix = doc.get("matrix") or {}
    include = doc.get("include") or []
    exclude = doc.get("exclude") or []
    for row in exclude:
        if not isinstance(row, dict) or not row:
            raise SuiteError("exclude entries must be non-empty mappings of dotted path -> value")

    combos: "list[dict]" = [{}]
    if matrix:
        keys = list(matrix)
        for key, values in matrix.items():
            if not isinstance(values, list) or not values:
                raise SuiteError(f"matrix.{key} must be a non-empty list")
        combos = [dict(zip(keys, values)) for values in itertools.product(*(matrix[k] for k in keys))]

    def excluded(overrides: dict) -> bool:
        return any(all(overrides.get(k) == v for k, v in row.items()) for row in exclude)

    cells: "list[dict]" = []
    index = 0
    for config_rel in suite["base_config"]:
        config_path = _resolve_base_config(suite_path, config_rel)
        for overrides in combos:
            if excluded(overrides):
                continue
            # Hash the RELATIVE reference, not the resolved path — cell ids stay
            # identical between the canonical checkout and a worktree (JUNIPER_EXP_PROJECT_DIR rebase).
            cell_id = f"c{index:03d}-{_sha8(config_rel + json.dumps(overrides, sort_keys=True))}"
            cells.append({"cell_id": cell_id, "index": index, "name": None, "config_path": str(config_path), "overrides": dict(overrides)})
            index += 1
    for item in include:
        if not isinstance(item, dict) or "overrides" not in item:
            raise SuiteError("include entries must be mappings with an 'overrides' key")
        config_rel = item.get("config", suite["base_config"][0])
        config_path = _resolve_base_config(suite_path, config_rel)
        overrides = dict(item["overrides"])
        cell_id = f"c{index:03d}-{_sha8(config_rel + json.dumps(overrides, sort_keys=True))}"
        cells.append({"cell_id": cell_id, "index": index, "name": item.get("name"), "config_path": str(config_path), "overrides": overrides})
        index += 1
    if not cells:
        raise SuiteError("suite expands to zero cells")
    return cells


def materialise_cell(cell: dict, suite: dict, suite_dir: Path, validate) -> Path:
    """Write the fully-resolved standalone experiment YAML for one cell."""
    config_path = Path(cell["config_path"])
    try:
        config = yaml.safe_load(config_path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise SuiteError(f"{cell['cell_id']}: cannot read base config {config_path}: {exc}") from exc
    for dotted, value in cell["overrides"].items():
        _set_dotted(config, dotted, value)
    if suite.get("seed_policy", "fixed") == "per_cell":
        base_seed = int(config.get("experiment", {}).get("seed", 0))
        derived = base_seed + cell["index"]
        config.setdefault("experiment", {})["seed"] = derived
        params = config.get("dataset", {}).get("params")
        if isinstance(params, dict) and "seed" in params:
            params["seed"] = derived
    exp = config.setdefault("experiment", {})
    exp["name"] = f"{suite['name']}-{cell['cell_id']}"
    cell_dir = suite_dir / "cells" / cell["cell_id"]
    cell_dir.mkdir(parents=True, exist_ok=True)
    out = cell_dir / "experiment.yaml"
    out.write_text(yaml.safe_dump(config, sort_keys=False))
    if validate is not None:
        try:
            validate(out)
        except Exception as exc:
            raise SuiteError(f"{cell['cell_id']}: resolved config rejected by the driver: {exc}") from exc
    return out


def _driver_validator():
    """The real driver's load_config, imported by path — None if unavailable."""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_experiment_for_suite", DEFAULT_DRIVER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return lambda path: mod.load_config(path)
    except Exception:
        return None


_JSONL_LOCK = threading.Lock()


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _JSONL_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def thread_budget_env(app: str, max_parallel: int) -> "dict[str, str]":
    """H-11 budget split for parallel cells: CASCOR_NUM_PROCESSES (or the BLAS vars for
    recurrence) = max(1, floor(nproc / (2 * max_parallel))); cascor BLAS pinned at 2."""
    nproc = os.cpu_count() or 1
    split = max(1, nproc // (2 * max_parallel))
    if app == "cascor":
        return {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "CASCOR_NUM_PROCESSES": str(split)}
    return {"OMP_NUM_THREADS": str(split), "MKL_NUM_THREADS": str(split), "OPENBLAS_NUM_THREADS": str(split)}


#: ``runtime:`` key -> the process environment variables it sets. D2 (below) chose the
#: environment route, so every entry here is a variable name, never a Python-level setter.
#: ``blas_threads`` fans out to all three BLAS families because which one binds depends on the
#: BLAS the environment resolved -- ``JuniperCascor1`` ships MKL and OpenBLAS both, and pinning
#: only one leaves the other at its default of "every core".
RUNTIME_BLAS_VARS: "tuple[str, ...]" = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")

#: `runtime:` sub-key -> the variables it sets. Used to decide which of a cell's runtime values
#: were asked for BY THE SUITE (matrix / include) rather than inherited from a base config.
RUNTIME_KEY_VARS: "dict[str, tuple[str, ...]]" = {
    "blas_threads": RUNTIME_BLAS_VARS,
    "num_processes": ("CASCOR_NUM_PROCESSES",),
    "eval_metrics_enabled": ("JUNIPER_CASCOR_EVAL_METRICS_ENABLED",),
}

#: The variables the H-11 parallel budget also sets, and therefore the only ones whose
#: precedence is contested. Everything else in a `runtime:` block applies unconditionally.
_H11_CONTESTED_VARS: frozenset = frozenset(RUNTIME_BLAS_VARS) | {"CASCOR_NUM_PROCESSES"}


def _explicit_runtime_vars(overrides: dict) -> "set[str]":
    """The env vars this cell's own overrides name, via dotted `runtime.<key>` paths."""
    named: "set[str]" = set()
    for path in overrides or {}:
        if isinstance(path, str) and path.startswith("runtime."):
            named.update(RUNTIME_KEY_VARS.get(path.split(".", 1)[1], ()))
    return named


def runtime_block_env(doc: dict, app: str = "cascor") -> "dict[str, str]":
    """Map a cell's ``runtime:`` block onto the environment the launcher exports to the service.

    **Owner decision D2**
    (``notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md``):
    implement ``runtime:`` as *the launcher exporting the variables at cascor bring-up* -- the
    process-tree-wide route -- and not as ``torch.set_num_threads`` on the training thread. The
    alternative was put to the owner and declined: cascor's two width mechanisms are independent,
    and only the environment one reaches the candidate workers, which inherit the ancestor's pool
    through ``forkserver``.

    **The gate on that ruling is PARTLY discharged, and the remaining part is named here so this
    docstring does not become the place the gap goes to die.**
    ``notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md`` §2 establishes
    the two things that justify wiring the route up at all: ``icv_in`` equals the requested width
    in every arm (so the route *binds*), and capping at 2 measurably reduces output-pass time.
    Do NOT re-quote that note's "-33%" -- its §2 correction of 2026-09-22 shows the column it was
    computed from sums every output pass rather than the first, so the figure is real but
    mislabelled, and it UNDERSTATES the true initial-pass benefit.
    What the note does NOT establish is the gate's item 4, *"epoch counts per phase"*:
    ``util/ad-hoc/2026-09-16_thread_width_arm.py`` emits ``later_pass_count`` and
    ``candidate_phase_count``, which are counts of STAGES, not of epochs -- the string "epoch"
    does not occur anywhere in the 40 evidence files, though the arm's own docstring claims it
    reports "epochs completed". So the note's headline that cascor#531's 1.52x penalty "does not
    reproduce" rests on candidate-phase WALL TIME alone. Wall time is epochs x time-per-epoch, so
    a flat wall is consistent with no effect **and** with two effects cancelling -- and cancelling
    is the live possibility, because the ruling's §1 records exactly two channels moving in
    opposite directions (throughput 1.26x -> 1.14x, epoch count 1.21x -> 1.03x). The epoch-count
    channel is numerics-driven (thread count changes BLAS reduction order, hence where a
    patience-based loop stops), so it bears on result IDENTITY, not merely speed.

    None of that blocks this function: a ``runtime:`` key that is accepted and discarded is a
    defect whichever way the penalty question resolves. It does mean **no one should cite this
    code as evidence that the penalty question is closed.**

    **Until this function existed the whole block was accepted and discarded.**
    ``run_experiment.py`` validates all three keys (``RUNTIME_KEYS``, :171) and rejects unknown
    ones, and nothing anywhere read a value. Three consequences, in increasing order of harm:

    1. A suite that wrote ``runtime: {blas_threads: 2}`` ran 16-wide anyway -- i.e. paid the full
       burst the cap was written to avoid.
    2. A **matrix** that varied the key measured one configuration N times. That is the inert-axis
       failure PF-2 was re-specified to escape, and it is exactly what D3's ruling tells the next
       session to dry-run-check for before committing PF-3's ~6.7 h matrix ("verify that the
       cell's ``thread_env`` is non-null"). That check is only meaningful once something binds.
    3. ``eval_metrics_enabled`` was the worst of the three, because the schema *herds* authors
       into it: putting it in ``service:`` raises *"eval_metrics_enabled belongs in runtime:
       (process env), not service:"* (``run_experiment.py:604``). The error message routed people
       to a key that did nothing.

    Values are validated here rather than coerced. A ``blas_threads: 0`` that silently became
    "unset" would reproduce the original defect one layer down -- a key that looks applied and
    is not -- so a bad value raises ``SuiteError`` and the suite refuses to start.

    Returns ``{}`` for a cell with no ``runtime:`` block, which leaves the launcher's inherited
    environment exactly as it is today.
    """
    # `doc` itself is type-checked before `.get` for the same reason its `runtime` block is
    # below: a materialised cell is always a mapping TODAY, but a hand-edited or truncated one
    # would reach here as a list or a string and raise AttributeError -- an internal traceback
    # from a function whose entire job is to turn malformed YAML into a clean SuiteError. That
    # is exactly the failure `load_suite` already documents against itself.
    if not isinstance(doc, dict):
        raise SuiteError(f"cell YAML must be a mapping, got {type(doc).__name__}")
    raw = doc.get("runtime")
    if raw is None:
        return {}
    # `or {}` guards ABSENCE, not TYPE: `runtime: []` is truthy-empty and would sail through it
    # into `.get`, which lists do not have. Type-check instead.
    if not isinstance(raw, dict):
        raise SuiteError(f"runtime block must be a mapping, got {type(raw).__name__}")

    env: "dict[str, str]" = {}

    def _present(key: str) -> bool:
        """Present AND non-null.

        ``null`` means CLEAR, not "error". This repo's dotted-override mechanism cannot delete a
        key -- ``_set_dotted`` WRITES ``None`` -- so ``runtime.blas_threads: null`` in a matrix
        is the only way an author can say "this cell runs unpinned", and
        ``suites/p4/e-e-recurrence-readout-spectrum.yaml`` already uses exactly that idiom on
        ``train.rff_features``. Treating ``None`` as a validation error would mean that the very
        change which made ``blas_threads`` matter also removed the only way to turn it off --
        and it would do so by refusing the whole suite with exit 2.
        """
        return key in raw and raw[key] is not None

    def _positive_int(key: str) -> int:
        value = raw[key]
        # bool is an int subclass and `runtime: {blas_threads: true}` would otherwise become 1.
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise SuiteError(f"runtime.{key} must be a positive integer, got {value!r}")
        return value

    if _present("blas_threads"):
        width = str(_positive_int("blas_threads"))
        env.update({var: width for var in RUNTIME_BLAS_VARS})
    if _present("num_processes"):
        # Withheld for recurrence for the same reason `thread_budget_env` withholds it: it is a
        # cascor knob (`cascade_correlation.py` reads the bare `CASCOR_NUM_PROCESSES`), and
        # exporting it into a recurrence run would put a meaningless variable into that run's
        # manifest `thread_env` and its baseline `HOST.json.thread_budget` -- where it becomes a
        # host-identity field and can refuse a comparison over a knob nothing read.
        if app == "cascor":
            env["CASCOR_NUM_PROCESSES"] = str(_positive_int("num_processes"))
        else:
            _positive_int("num_processes")  # still validated, so a typo is not silently ignored
    if _present("eval_metrics_enabled"):
        flag = raw["eval_metrics_enabled"]
        if not isinstance(flag, bool):
            raise SuiteError(f"runtime.eval_metrics_enabled must be a boolean, got {flag!r}")
        # cascor's `_env_flag` (manager.py:45, called at :1212) reads 1/0, true/false, yes/no, on/off and treats
        # BLANK as the default -- so emitting "" for false would enable it. Emit the word.
        env["JUNIPER_CASCOR_EVAL_METRICS_ENABLED"] = "true" if flag else "false"
    return env


def _read_registry(suite_dir: Path) -> "dict[str, dict]":
    registry = suite_dir / "registry.jsonl"
    rows: "dict[str, dict]" = {}
    if registry.exists():
        for line in registry.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["cell_id"]] = row
    return rows


def _headline_metrics(run_dir: Path) -> dict:
    stats_file = run_dir / "artifacts" / "results" / "stats.json"
    out: dict = {}
    if not stats_file.exists():
        return out
    try:
        stats = json.loads(stats_file.read_text())
    except (OSError, ValueError):
        return out
    for key in ("cascor", "recurrence"):
        block = stats.get(key)
        if isinstance(block, dict):
            for metric in ("final_accuracy", "test_accuracy", "val_accuracy", "train_r2", "cv_r2", "r2"):
                if isinstance(block.get(metric), (int, float)):
                    out[metric] = block[metric]
    return out


def execute_cell(cell: dict, cell_yaml: Path, app: str, timeout: float, launcher: Path, driver: Path, python_bin: str, extra_env: "dict[str, str] | None" = None, stall_seconds: "float | None" = None, max_wall_seconds: "float | None" = None, suite_name: "str | None" = None, runtime_env: "dict[str, str] | None" = None) -> dict:
    """--up → driver → --down for one cell; never raises for a cell-level failure.

    ``stall_seconds`` forwards ``execution.stall_seconds`` to the driver's Q-2 stall
    detector. It matters because the detector watches ``current_epoch``, which only
    advances during OUTPUT-layer training — no progress is reported while the CANDIDATE
    pool trains. A cell whose candidate phase runs longer than the driver default (120 s)
    is therefore marked ``stalled`` while perfectly healthy, and the suite has no way to
    say otherwise. Observed on the P4 E-A grid: every ``candidate_pool_size >= 16`` cell
    stalled at ~130 s, then completed normally in 513–1258 s once the window was raised.

    ``runtime_env`` is the cell's ``runtime:`` block resolved by ``runtime_block_env`` (D2).
    It is applied AFTER ``extra_env``, so a per-cell value **overrides** the H-11 parallel
    budget split. That precedence is not a preference, it is what makes PF-3 expressible:
    PF-3's second axis IS per-cell thread width, so if the H-11 split won, every cell of that
    matrix would run at the same width and the axis would be inert -- the identical defect that
    wasted PF-2's dataset axis and that D3's ruling now demands a one-cell run to rule out.

    ``main`` narrows that override to the keys the SUITE NAMES before calling this, so a width
    merely inherited from a base config still loses to H-11 and cannot silently oversubscribe a
    parallel run. Both values are recorded on the registry row (``thread_budget`` and
    ``runtime_env``) so the contest is legible **in ``registry.jsonl``** -- note that
    ``aggregate()`` writes neither to ``aggregate.csv`` nor to ``REPORT.md``, so a reader who
    only opens the report will not see it.

    ``max_wall_seconds`` forwards ``execution.max_wall_seconds`` to the driver's Q-2
    wall-clock budget, and is the same class of defect one field over. A suite could
    always reach the budget through a dotted ``matrix`` / ``include`` override — the
    widest suite in the repo does exactly that
    (``suites/p4/e-i-cascor-cap-ceiling.yaml`` sets ``outputs.max_wall_seconds``) — but
    an un-overridden cell silently inherited ``base_config``'s value (3600 s for
    ``spiral-baseline``) with no signal at all. Measured on the E-I run
    (``20260814T091542Z``), its cap-128 cell took 4243.6 s and would have been truncated by
    that inherited default, while cap 64 cleared it by only 693 s. Note this is NOT
    ``per_run_timeout_seconds``, which kills the driver from the OUTSIDE and records
    ``timed_out`` where the driver would otherwise write an honest ``timed_out``
    manifest of its own.
    """
    started = time.time()
    # D-C: the suite is the only layer that knows the cell id, and the launcher passes
    # it through to cascor's process env so every snapshot this cell writes records
    # which cell produced it. Note the launcher is invoked with ``--experiment
    # cell_id`` below, so without this the cell id would be the ONLY identity recorded
    # and the suite it belongs to would be lost.
    provenance_env = {"JUNIPER_CASCOR_CELL_ID": cell["cell_id"]}
    if suite_name:
        provenance_env["JUNIPER_CASCOR_EXPERIMENT"] = suite_name
    env = {**os.environ, **provenance_env, **(extra_env or {}), **(runtime_env or {})}

    # Grafana bridge: OPT-IN via environment, deliberately NOT a suite key.
    #
    # Two reasons, and the first is the load-bearing one. (1) A suite key would change the suite
    # file, and therefore every cell's `config_sha256`, between a bridged and an unbridged run of
    # the SAME scenario — destroying the comparability that repeat-measurement scenarios like PF-1
    # exist to provide. An env toggle leaves the YAML byte-identical. (2) The bridge is a
    # host-capability concern (it needs docker and the monitoring network) rather than a property
    # of the experiment; a suite that hard-declared it would simply fail on a host without them,
    # and `bridge_up` failing tears the whole run down.
    bridge = os.environ.get("JUNIPER_SUITE_GRAFANA_BRIDGE", "").strip().lower() in ("1", "true", "yes", "on")
    up_args = ["/bin/bash", str(launcher), "--up", f"--{app}", "--config", str(cell_yaml), "--experiment", cell["cell_id"]]
    if bridge:
        up_args.append("--grafana-bridge")

    row = {"cell_id": cell["cell_id"], "name": cell["name"], "overrides": cell["overrides"], "config_sha256": hashlib.sha256(cell_yaml.read_bytes()).hexdigest(), "run_id": None, "outcome": "failed", "exit_code": None, "error": None, "thread_budget": dict(extra_env) if extra_env else None, "runtime_env": dict(runtime_env) if runtime_env else None, "grafana_bridge": bridge}
    up = subprocess.run(up_args, capture_output=True, text=True, timeout=max(timeout, 300), env=env)
    match = RUN_ID_BANNER.search(up.stdout + up.stderr)
    if up.returncode != 0 or not match:
        row["error"] = f"launcher --up failed (exit {up.returncode}): {(up.stderr or up.stdout)[-500:]}"
        row["wall_seconds"] = round(time.time() - started, 3)
        return row
    run_id = match.group(1)
    row["run_id"] = run_id
    run_dir = DEFAULT_RUN_ROOT / run_id
    try:
        try:
            drv_argv = [python_bin, str(driver), "--config", str(cell_yaml), "--run-dir", str(run_dir)]
            if stall_seconds is not None:
                drv_argv += ["--stall-seconds", str(stall_seconds)]
            if max_wall_seconds is not None:
                drv_argv += ["--max-wall-seconds", str(max_wall_seconds)]
            drv = subprocess.run(drv_argv, capture_output=True, text=True, timeout=timeout, env=env)
            row["exit_code"] = drv.returncode
        except subprocess.TimeoutExpired:
            row["exit_code"] = None
            row["outcome"] = "timed_out"
            row["error"] = f"driver exceeded per_run_timeout_seconds={timeout}"
            return row
        manifest_file = run_dir / "manifest.json"
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text())
                row["outcome"] = manifest.get("outcome", "failed")
            except (OSError, ValueError):
                row["outcome"] = "failed"
                row["error"] = "unreadable manifest.json"
        else:
            row["outcome"] = "failed"
            row["error"] = f"driver exit {drv.returncode} with no manifest: {(drv.stderr or drv.stdout)[-300:]}"
        row["metrics"] = _headline_metrics(run_dir)
        row["run_dir"] = str(run_dir)
    finally:
        down = subprocess.run(["/bin/bash", str(launcher), "--down", run_id], capture_output=True, text=True, timeout=300, env=env)
        row["teardown_ok"] = down.returncode == 0
        row["wall_seconds"] = round(time.time() - started, 3)
    return row


def _gate_metrics(suite_dir: Path, cells: "list[dict]") -> "dict[str, dict]":
    """Per-cell WORK and SPEED, the perf lane's two ratified gate inputs (P2 item 1.4).

    ``aggregate.csv`` used to carry ``wall_seconds`` and nothing else -- and ``wall_seconds`` is
    DE-RATIFIED: it absorbs plot rendering and stack bring-up, and enabling the Grafana bridge alone
    moves it ~5%. A reader who opened the aggregate was analysing the wrong quantity with nothing
    flagging it. These columns put the right ones beside it.
    """
    # NOT wrapped in try/except ImportError. The first draft was, and when the import failed the
    # columns came out BLANK and REPORT.md said "work invariant: BROKEN -- step_count not measured"
    # -- indistinguishable from a genuinely broken suite. A missing sibling module is a packaging
    # bug and should say so loudly.
    from experiments import read_run_metrics as rrm

    out: "dict[str, dict]" = {}
    registry = _read_registry(suite_dir)
    for cell in cells:
        row = registry.get(cell["cell_id"], {})
        run_dir = row.get("run_dir")
        if not run_dir:
            continue
        metrics = rrm.read_run(Path(run_dir))
        metrics["workload_fingerprint"] = rrm.workload_fingerprint(suite_dir, cell["cell_id"])
        out[cell["cell_id"]] = metrics
    return out


def _run_comparison(tag: str, suite_dir: Path) -> str:
    """Render a baseline comparison for REPORT.md, never changing the suite's own exit code.

    REPORTING ONLY, and deliberately so. Wiring a comparator verdict to run_suite's exit status
    would silently make the run tier a gate -- and §6 of the P1 design records that as a SEPARATE
    owner decision, still open. A failure here is information for a person, not a build outcome.
    """
    from experiments import compare_baseline as cb

    try:
        payload, host = cb._load_baseline(DEFAULT_RUN_ROOT, tag)
    except cb.CompareError as exc:
        return f"comparison could not run: {exc}"
    return cb.render(cb.compare(payload, host, [suite_dir]))


def aggregate(suite_dir: Path, suite: dict, cells: "list[dict]", comparison: "str | None" = None) -> int:
    registry = _read_registry(suite_dir)
    metric_keys = sorted({k for row in registry.values() for k in (row.get("metrics") or {})})
    override_keys = sorted({k for cell in cells for k in cell["overrides"]})
    gate = _gate_metrics(suite_dir, cells)
    csv_path = suite_dir / "aggregate.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        # step_count / mean_step_seconds sit next to wall_seconds deliberately: the de-ratified
        # metric stays for continuity, but it is no longer the only thing on offer.
        writer.writerow(["cell_id", "name", "run_id", "outcome", "exit_code", "wall_seconds", "step_count", "mean_step_seconds", *override_keys, *metric_keys])
        for cell in cells:
            row = registry.get(cell["cell_id"], {})
            cell_gate = gate.get(cell["cell_id"], {})
            writer.writerow(
                [
                    cell["cell_id"],
                    cell["name"] or "",
                    row.get("run_id") or "",
                    row.get("outcome") or "not-run",
                    row.get("exit_code"),
                    row.get("wall_seconds"),
                    cell_gate.get("step_count", ""),
                    cell_gate.get("mean_step_seconds", ""),
                    *[cell["overrides"].get(k, "") for k in override_keys],
                    *[(row.get("metrics") or {}).get(k, "") for k in metric_keys],
                ]
            )
    succeeded = [c for c in cells if registry.get(c["cell_id"], {}).get("outcome") == "succeeded"]
    failed = [c for c in cells if registry.get(c["cell_id"], {}).get("outcome") not in (None, "succeeded")]
    lines = [
        f"# Suite report — {suite['name']}",
        "",
        f"{suite.get('description', '')}".strip(),
        "",
        f"Cells: {len(cells)} total, {len(succeeded)} succeeded, {len(failed)} failed/other, {len(cells) - len(succeeded) - len(failed)} not run.",
        "",
        "| cell | outcome | step_count | mean step (ms) | wall (s) | " + " | ".join(override_keys + metric_keys) + " |",
        "|---|---|---|---|---|" + "---|" * (len(override_keys) + len(metric_keys)),
    ]
    for cell in cells:
        row = registry.get(cell["cell_id"], {})
        cell_gate = gate.get(cell["cell_id"], {})
        mean_step = cell_gate.get("mean_step_seconds")
        values = [str(cell["overrides"].get(k, "")) for k in override_keys] + [str((row.get("metrics") or {}).get(k, "")) for k in metric_keys]
        lines.append(
            f"| {cell['cell_id']} | {row.get('outcome') or 'not-run'} | {cell_gate.get('step_count') or ''} | "
            f"{f'{mean_step * 1000:.3f}' if isinstance(mean_step, float) else ''} | {row.get('wall_seconds') or ''} | " + " | ".join(values) + " |"
        )

    counts = {g.get("step_count") for g in gate.values() if g.get("step_count") is not None}
    fingerprints = {g.get("workload_fingerprint") for g in gate.values() if g.get("workload_fingerprint")}
    # ASK `summarise`, do not re-derive. `len(counts) == 1` is the vacuous form ml#1776
    # removed from `summarise` -- it is True for one measured cell beside one unmeasured
    # one, so a half-measured suite printed HOLDS here long after the gate itself stopped
    # saying so. Re-deriving a predicate next to the function that owns it is how the two
    # drift apart with nothing failing.
    from experiments import read_run_metrics as _rrm

    _rows = [dict(g, run_id=cid) for cid, g in gate.items()]
    _summary = _rrm.summarise(_rows)
    if _rows and not _summary.get("work_countable", True):
        # `_rows and` is load-bearing. `summarise([])` reports work_countable False because
        # it saw no countable kind, and without this guard an EMPTY gate would print the
        # recurrence third state instead of the cascor-unmeasured one (#1685).
        #
        # Recurrence exposes no work counter; BROKEN would claim these cells disagreed
        # about something that was never counted.
        _work_state = "not countable"
        _work_detail = f"kind {_summary.get('kinds')} has no work counter"
    elif _summary.get("work_invariant"):
        _work_state = "HOLDS"
        _work_detail = f"step_count {sorted(int(c) for c in counts)}"
    else:
        _work_state = "BROKEN"
        _work_detail = f"step_count {sorted(int(c) for c in counts) if counts else 'not measured'}"
        if counts and len(counts) == 1:
            _work_detail += f" measured on {len(counts)} of {len(_rows)} cell(s)"
    lines += [
        "",
        "## Gate inputs",
        "",
        "**`wall_seconds` is DE-RATIFIED** — it absorbs plot rendering and stack bring-up, and enabling the",
        "Grafana bridge alone moves it ~5%. It is kept for continuity only. The gated quantity is",
        "**`step_count`** (work, compared exactly); **mean step duration** is reported and never gated,",
        "because this host's own drift floor is 13–20.5%.",
        "",
        f"- **work invariant**: {_work_state} — {_work_detail}",
        f"- **single workload**: {'yes' if len(fingerprints) == 1 else 'NO'} — fingerprint {sorted(f[:12] + '...' for f in fingerprints) if fingerprints else 'unknown'}",
    ]
    if _work_state == "BROKEN":
        lines.append("- These cells are **not repeats of each other**; a baseline must not be cut from them.")
    if _work_state == "not countable":
        # Say what WAS measured. "The gate does not apply" is only half an answer; the
        # third state exists because the run is still worth reporting.
        _epochs = sorted({str(g.get("n_epochs")) for g in gate.values() if g.get("n_epochs") is not None})
        _stopped = sorted({str(g.get("stopped_reason")) for g in gate.values() if g.get("stopped_reason")})
        _windows = sorted({str(g.get("n_windows")) for g in gate.values() if g.get("n_windows") is not None})
        lines.append(
            f"- **reported instead**: n_epochs {_epochs or 'unknown'}, stopped_reason {_stopped or 'unknown'}, "
            f"n_windows {_windows or 'unknown'} — these are INPUT size and readout type, not work done, "
            f"so they are reported and never gated."
        )
    if comparison is not None:
        lines += ["", "## Baseline comparison", "", "```text", comparison, "```", ""]
        lines.append("The suite's own exit code does NOT reflect this verdict — whether the run tier gates is a")
        lines.append("separate owner decision (§6 of the P1 design). Read the verdict, or run `compare_baseline.py`.")
    (suite_dir / "REPORT.md").write_text("\n".join(lines) + "\n")
    return 0 if len(succeeded) == len(cells) else 1


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Print the expanded cell list and every command; write nothing")
    parser.add_argument("--resume", metavar="SUITE_ID", default=None, help="Resume an existing suite dir, skipping cells already terminal in registry.jsonl")
    parser.add_argument("--only", nargs="*", default=None, metavar="CELL_ID", help="Execute only these cell ids")
    parser.add_argument(
        "--compare-baseline",
        metavar="TAG",
        default=None,
        help="After aggregating, compare against this Q-8 baseline and record the verdict in REPORT.md. "
        "REPORTING ONLY: the suite's exit code is unchanged by the verdict (whether the run tier gates is a separate owner decision).",
    )
    args = parser.parse_args(argv)

    try:
        doc = load_suite(args.suite)
        cells = expand_cells(doc, args.suite)
        # D5 (2026-09-11): the Q-6 launch gate lives HERE, not in load_suite — structural
        # validation must not need a cascor sibling, but launching must. Before --dry-run prints
        # and before any cell is materialised, so the refusal reaches the operator at exactly the
        # point it always did. Still fail-closed.
        check_cascor_parallel_floor(doc)
    except SuiteError as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return 2

    suite = doc["suite"]
    execution = doc.get("execution") or {}
    outputs = doc.get("outputs") or {}
    timeout = float(execution.get("per_run_timeout_seconds", 3600))
    # None => omit the flag entirely, so the driver keeps owning its own default.
    stall_seconds = float(execution["stall_seconds"]) if execution.get("stall_seconds") is not None else None
    max_wall_seconds = float(execution["max_wall_seconds"]) if execution.get("max_wall_seconds") is not None else None
    continue_on_failure = bool(execution.get("continue_on_failure", True))
    launcher = Path(os.environ.get("JUNIPER_SUITE_LAUNCHER", str(DEFAULT_LAUNCHER)))
    driver = Path(os.environ.get("JUNIPER_SUITE_DRIVER", str(DEFAULT_DRIVER)))
    python_bin = os.environ.get("JUNIPER_SUITE_PYTHON", sys.executable)

    if args.resume:
        suite_id = args.resume
    else:
        suite_id = f"{suite['name']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    suite_dir = Path(outputs.get("suite_dir") or (DEFAULT_RUN_ROOT / "suites" / suite_id))

    if args.dry_run:
        print(f"suite {suite['name']} ({suite['app']}): {len(cells)} cells -> {suite_dir}")
        for cell in cells:
            print(f"  {cell['cell_id']}  config={Path(cell['config_path']).name}  overrides={json.dumps(cell['overrides'], sort_keys=True)}" + (f"  name={cell['name']}" if cell["name"] else ""))
            print(f"    $ {launcher} --up --{suite['app']} --config {suite_dir}/cells/{cell['cell_id']}/experiment.yaml --experiment {cell['cell_id']}")
            stall_flag = f" --stall-seconds {stall_seconds}" if stall_seconds is not None else ""
            wall_flag = f" --max-wall-seconds {max_wall_seconds}" if max_wall_seconds is not None else ""
            print(f"    $ {python_bin} {driver} --config …/experiment.yaml --run-dir <RUN_DIR>{stall_flag}{wall_flag} && {launcher} --down <RUN_ID>")
        return 0

    if args.resume and not suite_dir.is_dir():
        print(f"suite error: --resume {suite_id}: no such suite dir {suite_dir}", file=sys.stderr)
        return 2

    suite_dir.mkdir(parents=True, exist_ok=True)
    validate = _driver_validator()
    registry_rows = _read_registry(suite_dir) if args.resume else {}
    selected = [c for c in cells if args.only is None or c["cell_id"] in args.only]
    if args.only is not None and len(selected) != len(args.only):
        missing = set(args.only) - {c["cell_id"] for c in selected}
        print(f"suite error: --only ids not in the expansion: {sorted(missing)}", file=sys.stderr)
        return 2

    (suite_dir / "suite_manifest.json").write_text(
        json.dumps({"schema": "juniper-experiment-suite/1", "suite_id": suite_id, "suite": suite, "execution": execution, "cells": [{k: c[k] for k in ("cell_id", "index", "name", "config_path", "overrides")} for c in cells], "suite_yaml_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest()}, indent=2, sort_keys=True)
        + "\n"
    )

    mode = execution.get("mode", "sequential")
    max_parallel = int(execution.get("max_parallel", 1)) if mode == "parallel" else 1
    budget = thread_budget_env(suite["app"], max_parallel) if mode == "parallel" else None

    runnable = []
    for cell in selected:
        prior = registry_rows.get(cell["cell_id"])
        if prior and prior.get("outcome") == "succeeded":
            print(f"[suite] {cell['cell_id']}: already succeeded — skipped (resume)")
            continue
        runnable.append(cell)
    try:
        materialised = {cell["cell_id"]: materialise_cell(cell, suite, suite_dir, validate) for cell in runnable}
        # D2: resolve every cell's `runtime:` block BEFORE the first `--up`. A bad value must
        # refuse the suite rather than one cell, for the same reason D5 moved the cascor floor
        # check onto the execution path: a guard that fires after N cells have run has already
        # let N runs of unusable evidence onto disk. `execute_cell` deliberately never raises,
        # so this cannot live there.
        runtime_envs = {cell_id: runtime_block_env(yaml.safe_load(path.read_text()) or {}, suite["app"]) for cell_id, path in materialised.items()}
        # ...then, under a parallel budget, keep only the thread keys this SUITE actually asked
        # for. The override exists to make PF-3's per-cell width axis expressible, and that
        # argument reaches exactly as far as keys the suite names in its matrix/include. A value
        # merely INHERITED from a base config carries no such intent: `spiral-baseline.yaml` sets
        # `num_processes: 4`, so without this filter any parallel cascor suite built on it would
        # silently beat the H-11 split -- 4 cells x 4 processes on a 16-core host, 2x
        # oversubscribed, and invisible because `REPORT.md` prints neither budget.
        # `eval_metrics_enabled` is exempt: it is not a thread budget and H-11 has no opinion.
        if budget:
            for cell in runnable:
                named = _explicit_runtime_vars(cell["overrides"])
                runtime_envs[cell["cell_id"]] = {var: value for var, value in runtime_envs[cell["cell_id"]].items() if var not in _H11_CONTESTED_VARS or var in named}
    except SuiteError as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return 2
    except (OSError, yaml.YAMLError) as exc:
        # OSError is the realistic one -- the YAMLError branch is near-unreachable because
        # `materialise_cell` wrote these files with `yaml.safe_dump` moments ago, while an
        # unreadable path (permissions, a full or unmounted suite dir) is an ordinary failure
        # that would otherwise escape as a traceback from the suite's own validation phase.
        print(f"suite error: cannot read a materialised cell YAML: {exc}", file=sys.stderr)
        return 2

    def _record(cell: dict, row: dict) -> None:
        row["suite_id"] = suite_id
        _append_jsonl(suite_dir / "registry.jsonl", row)
        _append_jsonl(DEFAULT_RUN_ROOT / "index.jsonl", {"suite_id": suite_id, "cell_id": cell["cell_id"], "run_id": row.get("run_id"), "outcome": row.get("outcome"), "run_dir": row.get("run_dir")})
        print(f"[suite] {cell['cell_id']}: {row['outcome']}" + (f" ({row.get('error')})" if row.get("error") else ""), flush=True)

    any_failed = False
    if mode == "parallel" and max_parallel > 1:
        # Wave 7.5: bounded worker pool. Port lockdirs serialise allocation; W-6 gives each
        # run its own snapshots dir; the H-11 budget env keeps N cells from thrashing the host.
        # Stop-on-failure = stop SUBMITTING after the first failure; running cells drain.
        stop = threading.Event()
        with ThreadPoolExecutor(max_workers=max_parallel) as pool:
            futures = {}
            for cell in runnable:
                if stop.is_set():
                    break
                print(f"[suite] {cell['cell_id']}: submitted ({json.dumps(cell['overrides'], sort_keys=True)})", flush=True)
                futures[pool.submit(execute_cell, cell, materialised[cell["cell_id"]], suite["app"], timeout, launcher, driver, python_bin, budget, stall_seconds, max_wall_seconds, suite["name"], runtime_envs[cell["cell_id"]])] = cell
            for future in as_completed(futures):
                cell = futures[future]
                row = future.result()
                _record(cell, row)
                if row["outcome"] != "succeeded":
                    any_failed = True
                    if not continue_on_failure:
                        stop.set()
    else:
        for cell in runnable:
            print(f"[suite] {cell['cell_id']}: running ({json.dumps(cell['overrides'], sort_keys=True)})", flush=True)
            row = execute_cell(cell, materialised[cell["cell_id"]], suite["app"], timeout, launcher, driver, python_bin, budget, stall_seconds, max_wall_seconds, suite["name"], runtime_envs[cell["cell_id"]])
            _record(cell, row)
            if row["outcome"] != "succeeded":
                any_failed = True
                if not continue_on_failure:
                    break

    comparison = _run_comparison(args.compare_baseline, suite_dir) if getattr(args, "compare_baseline", None) else None
    rc = aggregate(suite_dir, suite, cells, comparison=comparison)
    print(f"[suite] wrote {suite_dir}/aggregate.csv + REPORT.md")
    return 1 if (any_failed or rc) else 0


if __name__ == "__main__":
    sys.exit(main())
