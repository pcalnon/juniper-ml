#!/usr/bin/env python3
"""
Import the INSTALLED juniper-cascor wheel and call ``compute_classification_accuracy`` (juniper-cascor#731).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — one-off (post-publication import probe of juniper-cascor 0.13.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4 APD-ML-002 row, §8);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_flood3-continuation-cascor-0-13-0-at-pypi-gate.md (item 5);
         util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py (the static half: sha256 + ast, nothing imported)

Why this exists
---------------
The 2026-10-28 static probe parses the published wheel with ``ast`` and never imports it. The flood-3
handoff's item 5 asks for the other half: install the wheel PyPI serves, import the module with
``importlib.import_module`` and call the function, so the check is of behaviour, not of source text.

Run it with the interpreter of a clean venv that holds only the wheel under test and torch, so nothing
can resolve from a checkout. The cascor conda env is unsuitable: it carries an editable install of the
cascor primary, which is exactly the source this must not read. The probe refuses to judge a module
that loaded from outside ``sys.prefix``.

    <venv>/bin/python -I util/ad-hoc/2026-10-29_cascor_0_13_0_wheel_import_probe.py --expect-version 0.13.0
    <control venv>/bin/python -I util/ad-hoc/2026-10-29_cascor_0_13_0_wheel_import_probe.py --expect-version 0.12.0   # fails: #731 postdates 0.12.0

On the Linux host, prefix both with ``env -u LD_LIBRARY_PATH -u LIBTORCH``: the login shell points
``LD_LIBRARY_PATH`` at rust_mudgeon's libtorch, so a pip torch loads the wrong ``libtorch_python.so``
(``undefined symbol: _PyObject_NextNotImplemented``) and the probe exits 2.

Run of record (2026-10-29, Python 3.14.7, torch 2.15.0+cpu, wheels sha256-checked against PyPI):
0.13.0 passed all 22 checks (exit 0); the 0.12.0 control failed 2, ``compute_classification_accuracy``
absent from both copies (exit 1).

The wheel ships the package tree twice, at the top level (``api``) and under ``src`` (``src.api``), so
every check runs on both copies. Each copy must:

1. load from inside this interpreter's ``sys.prefix``;
2. define ``compute_classification_accuracy`` as a callable;
3. return the documented answers on known-answer batches: one output column decoded at ``> 0.5``,
   one-hot columns decoded by ``argmax``, a single-class target scored rather than degraded, and
   ``(None, "empty_batch")`` / ``(None, "invalid_output")`` for the two degenerate batches.

Exit status: 0 when every check passes, 1 when any check fails (the 0.12.0 control lands here), and 2 on
anything else: the distribution is missing or at another version, torch does not import, or an
unexpected error. So 1 always means a check ran and failed.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import math
import sys
from pathlib import Path

COPIES = ("api.lifecycle.classification_metrics", "src.api.lifecycle.classification_metrics")
FUNC = "compute_classification_accuracy"


def _known_answer_cases(torch):
    """(label, output, target, expected) where expected is (value or None, reason or None)."""
    nan = float("nan")
    return [
        ("one column, decoded at > 0.5", torch.tensor([[0.9], [0.2], [0.6], [0.4]]), torch.tensor([[1.0], [0.0], [0.0], [1.0]]), (0.5, None)),
        ("one column given as 1-D", torch.tensor([0.9, 0.2, 0.6]), torch.tensor([1.0, 0.0, 1.0]), (1.0, None)),
        ("exactly 0.5 is not positive", torch.tensor([[0.5], [0.51]]), torch.tensor([[1.0], [1.0]]), (0.5, None)),
        ("one-hot, decoded by argmax", torch.tensor([[0.1, 0.9], [0.8, 0.2], [0.3, 0.7]]), torch.tensor([[0.0, 1.0], [1.0, 0.0], [1.0, 0.0]]), (2.0 / 3.0, None)),
        ("three classes", torch.tensor([[0.7, 0.2, 0.1], [0.1, 0.1, 0.8], [0.2, 0.5, 0.3], [0.6, 0.3, 0.1]]), torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]), (0.5, None)),
        ("single-class target is scored", torch.tensor([[0.9], [0.8], [0.1]]), torch.tensor([[1.0], [1.0], [1.0]]), (2.0 / 3.0, None)),
        ("empty batch degrades", torch.zeros((0, 1)), torch.zeros((0, 1)), (None, "empty_batch")),
        ("NaN output degrades", torch.tensor([[nan], [0.2]]), torch.tensor([[1.0], [0.0]]), (None, "invalid_output")),
        ("Inf target degrades", torch.tensor([[0.9], [0.2]]), torch.tensor([[float("inf")], [0.0]]), (None, "invalid_output")),
    ]


def _matches(got, expected) -> bool:
    if not isinstance(got, tuple) or len(got) != 2:
        return False
    value, reason = got
    want_value, want_reason = expected
    if reason != want_reason:
        return False
    if want_value is None:
        return value is None
    return isinstance(value, float) and math.isclose(value, want_value, rel_tol=0.0, abs_tol=1e-12)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 2)[1])
    parser.add_argument("--expect-version", required=True, help="the juniper-cascor version the venv must hold")
    args = parser.parse_args()

    prefix = Path(sys.prefix).resolve()
    print(f"interpreter: {sys.executable} (Python {sys.version.split()[0]})")
    print(f"sys.prefix:  {prefix}")
    try:
        installed = importlib.metadata.version("juniper-cascor")
    except importlib.metadata.PackageNotFoundError:
        print("ERROR: juniper-cascor is not installed in this interpreter")
        return 2
    print(f"juniper-cascor: {installed}")
    if installed != args.expect_version:
        print(f"ERROR: expected juniper-cascor {args.expect_version}, found {installed}")
        return 2
    try:
        import torch
    except ImportError as exc:
        print(f"ERROR: torch does not import: {exc}")
        return 2
    print(f"torch: {torch.__version__}")

    failures = 0
    for name in COPIES:
        print(f"\n== {name}")
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            print(f"ERROR: import failed: {exc}")
            return 2
        origin = Path(module.__file__).resolve()
        if not origin.is_relative_to(prefix):
            print(f"FAIL  loaded from outside sys.prefix: {origin}")
            failures += 1
            continue
        print(f"PASS  loaded from {origin}")
        func = getattr(module, FUNC, None)
        if not callable(func):
            print(f"FAIL  {FUNC} is not defined")
            failures += 1
            continue
        print(f"PASS  {FUNC} is defined")
        for label, output, target, expected in _known_answer_cases(torch):
            got = func(output, target)
            ok = _matches(got, expected)
            failures += 0 if ok else 1
            print(f"{'PASS' if ok else 'FAIL'}  {label}: got {got!r}, expected {expected!r}")

    print(f"\n{'PASS' if failures == 0 else 'FAIL'}: {failures} failed check(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # any unexpected error is exit 2, never a check failure
        print(f"ERROR: unexpected {type(exc).__name__}: {exc}")
        sys.exit(2)
