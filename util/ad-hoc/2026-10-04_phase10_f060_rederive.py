#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Re-derive F-CANOPY-060 by EXECUTING the three functions on the refusal's path, each at a pinned commit.

F-CANOPY-060 (handed over by the defect-register arc, round 42): canopy's dataset-shortfall prompt
drops juniper-data's cap sentence, "The resulting dataset will be permanently annotated as truncated.",
because ``_producer_detail_from_refusal`` cuts the producer detail at ``" The resulting dataset"`` as
well as at ``" To accept it,"``.

The path, all three halves run from git OBJECTS (never a working tree), so a moved checkout cannot
change the answer:

  juniper-data   ``juniper_data/core/limits.py``: ``InputTooLargeError`` (the cap refusal) and
                 ``IncompleteDataError`` (the shortfall refusal, the control). Executed as a module;
                 it imports only ``typing``.
  data-client    renders a 422 as ``"Validation error (422): <detail>"`` with ``status_code=422``
                 (``juniper_data_client/client.py``). Reproduced here by a stand-in exception that
                 carries the same string and status; the format is quoted, not imported.
  juniper-cascor ``TrainingLifecycleManager._describe_dataset_fetch_failure``
                 (``src/api/lifecycle/manager.py``), lifted out of the class by AST and executed with
                 the module constants it reads.
  juniper-canopy ``DashboardManager._producer_detail_from_refusal`` and
                 ``_is_dataset_shortfall_refusal`` (``src/frontend/dashboard_manager.py``), lifted by AST.

Prints, for each refusal: whether cascor dresses it as a shortfall refusal (the token), whether canopy
opens its three-way prompt, the producer text canopy shows, and whether juniper-data's closing sentence
survives. Exit 0 always; the verdict lines are the result.

Could this instrument have produced a different answer? Yes, in each direction: the control
(``IncompleteDataError``) has no " The resulting dataset" in its detail, so its sentence must survive,
and ``--cut-only-at-remedy`` re-runs canopy's extractor with the proposed fix (cut only at
" To accept it,"), under which the cap sentence must survive too.

Usage:
    python3 util/ad-hoc/2026-10-04_phase10_f060_rederive.py [--cut-only-at-remedy]
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import textwrap
import types

JUNIPER = "/home/pcalnon/Development/python/Juniper"
DATA = (f"{JUNIPER}/juniper-data", "29be6d35", "juniper_data/core/limits.py")
CASCOR = (f"{JUNIPER}/juniper-cascor", "95cdc562", "src/api/lifecycle/manager.py")
CANOPY = (f"{JUNIPER}/juniper-canopy", "1b2dd438", "src/frontend/dashboard_manager.py")

DATA_CAP_SENTENCE = "The resulting dataset will be permanently annotated as truncated."


def git_show(repo: str, sha: str, path: str) -> str:
    """Return a file's text at a commit, from the object store."""
    return subprocess.run(["git", "-C", repo, "show", f"{sha}:{path}"], check=True, capture_output=True, text=True).stdout


def lift_method(source: str, class_name: str, method: str) -> str:
    """Return a method's source, dedented, with its decorators dropped, so it execs as a plain function."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method:
                    lines = source.splitlines()
                    return textwrap.dedent("\n".join(lines[item.lineno - 1 : item.end_lineno]))
    raise SystemExit(f"{class_name}.{method} not found")


def module_constant(source: str, name: str) -> object:
    """Return a module-level constant's literal value."""
    for node in ast.parse(source).body:
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name and node.value is not None:
                return ast.literal_eval(node.value)
    raise SystemExit(f"constant {name} not found")


def client_validation_error(message: str, status_code: int) -> Exception:
    """Stand-in for juniper_data_client's JuniperDataValidationError: same str(), same status_code."""
    exc = Exception(message)
    exc.status_code = status_code  # type: ignore[attr-defined]
    return exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cut-only-at-remedy", action="store_true", help="run canopy's extractor with the proposed fix")
    args = ap.parse_args()

    limits = types.ModuleType("limits_at_29be6d35")
    exec(compile(git_show(*DATA), "limits.py", "exec"), limits.__dict__)  # noqa: S102 -- a pinned git object, read-only

    cascor_src = git_show(*CASCOR)
    cascor_ns = {
        "Optional": __import__("typing").Optional,
        "_PRODUCER_REFUSAL_REMEDY": module_constant(cascor_src, "_PRODUCER_REFUSAL_REMEDY"),
        "_PRODUCER_REFUSAL_STATUS": module_constant(cascor_src, "_PRODUCER_REFUSAL_STATUS"),
        "_OPT_IN_SKIPPED_NOT_TRUNCATABLE": module_constant(cascor_src, "_OPT_IN_SKIPPED_NOT_TRUNCATABLE"),
        "_OPT_IN_SKIPPED_CALLER_DEFERRED": module_constant(cascor_src, "_OPT_IN_SKIPPED_CALLER_DEFERRED"),
        "_OPT_IN_SKIPPED_LIST_UNREADABLE": module_constant(cascor_src, "_OPT_IN_SKIPPED_LIST_UNREADABLE"),
        # constants_api_defaults.py:145 at 95cdc562; read from the object, not typed here.
        "_PROJECT_API_SHORTFALL_REFUSAL_TOKEN": module_constant(git_show(CASCOR[0], CASCOR[1], "src/cascor_constants/constants_api/constants_api_defaults.py"), "_PROJECT_API_SHORTFALL_REFUSAL_TOKEN"),
    }
    exec(lift_method(cascor_src, "TrainingLifecycleManager", "_describe_dataset_fetch_failure"), cascor_ns)  # noqa: S102
    describe = cascor_ns["_describe_dataset_fetch_failure"]

    canopy_src = git_show(*CANOPY)
    canopy_ns = {
        "DATASET_SHORTFALL_REFUSAL_MARKER": module_constant(canopy_src, "DATASET_SHORTFALL_REFUSAL_MARKER"),
        "DATASET_SHORTFALL_REFUSAL_SENTENCE": module_constant(canopy_src, "DATASET_SHORTFALL_REFUSAL_SENTENCE"),
    }
    extractor_src = lift_method(canopy_src, "DashboardManager", "_producer_detail_from_refusal")
    if args.cut_only_at_remedy:
        old = 'for stop in (" To accept it,", " The resulting dataset"):'
        if old not in extractor_src:
            raise SystemExit("canopy's cut list moved; the proposed-fix mutation no longer applies")
        extractor_src = extractor_src.replace(old, 'for stop in (" To accept it,",):')
    exec(extractor_src, canopy_ns)  # noqa: S102
    exec(lift_method(canopy_src, "DashboardManager", "_is_dataset_shortfall_refusal"), canopy_ns)  # noqa: S102
    extract = canopy_ns["_producer_detail_from_refusal"]
    opens_prompt = canopy_ns["_is_dataset_shortfall_refusal"]

    cases = {
        "cap (InputTooLargeError, equities symbol cap at its default 14)": limits.InputTooLargeError(source="The requested universe", unit=limits.UNIT_SYMBOLS, cap=14, actual=503, opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION"),
        "control (IncompleteDataError)": limits.IncompleteDataError(detail="3 symbols had no usable share history.", unrescued=["AAA", "BBB", "CCC"], rows_affected=1200, opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION"),
    }
    print(f"pins: data {DATA[1]}  cascor {CASCOR[1]}  canopy {CANOPY[1]}  extractor={'PROPOSED FIX (cut only at the remedy)' if args.cut_only_at_remedy else 'as on main'}")
    for label, data_exc in cases.items():
        data_detail = str(data_exc)
        closing = data_detail.rsplit(". ", 1)[-1]
        client_exc = client_validation_error(f"Validation error (422): {data_detail}", status_code=422)
        message = describe(client_exc, allow_truncated=False)
        shown = extract(message)
        print(f"\n== {label}")
        print(f"   juniper-data closing sentence : {closing!r}")
        print(f"   cascor token present          : {message.startswith(cascor_ns['_PROJECT_API_SHORTFALL_REFUSAL_TOKEN'])}")
        print(f"   canopy opens three-way prompt : {opens_prompt(message)}")
        print(f"   canopy shows                  : {shown!r}")
        print(f"   closing sentence survives     : {closing in shown}")
        print(f"   cascor remedy leaks into it   : {'To accept it,' in shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
