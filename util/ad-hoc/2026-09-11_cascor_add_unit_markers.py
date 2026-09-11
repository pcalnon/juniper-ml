#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (juniper-cascor CI marker gap)
Application: ad-hoc migration
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: add a module-level ``pytestmark = pytest.mark.unit`` to the juniper-cascor unit-test
files that carry no ``unit`` marker, so CI's ``-m "unit and not slow"`` lane actually runs them.

Writes to a STAGING directory, never to the cascor checkout -- this session is confined to a
juniper-ml worktree and lands cascor changes through the signed-commit API path.

It refuses rather than guesses:

* a file that already defines ``pytestmark`` is REPORTED, not edited -- merging into an
  existing declaration (a list? a different marker?) is a judgement call, not a rewrite.
* a file with no ``import pytest`` gets one inserted after the last existing import; if the
  import block cannot be located unambiguously, the file is reported instead.
* it never touches a file whose tests all already carry ``unit``.

Module-level ``pytestmark`` is additive: a test that already carries ``@pytest.mark.unit``
simply carries it twice, which pytest treats as one. So partly-marked files are safe.
"""
import argparse
import os
import re
import shutil
import sys

CASCOR = os.environ.get("CASCOR_ROOT", "/home/pcalnon/Development/python/Juniper/juniper-cascor")

#: Files with tests missing the ``unit`` marker, from
#: util/ad-hoc/2026-09-11_cascor_unit_marker_gap.py at cascor 43785fe.
TARGETS = [
    "src/tests/unit/test_dockerfile_cpu_torch_pin.py",
    "src/tests/unit/test_cascor_plotter_coverage.py",
    "src/tests/unit/api/test_phase1c_security.py",
    "src/tests/unit/test_candidate_training_manager.py",
    "src/tests/unit/api/test_metrics_auth_middleware.py",
    "src/tests/unit/test_spiral_problem_coverage.py",
    "src/tests/unit/api/test_r2_1_4_wire_compat.py",
    "src/tests/unit/test_blas_thread_policy.py",
    "src/tests/unit/test_logger_frame_resolution.py",
    "src/tests/unit/test_p1_fixes.py",
    "src/tests/unit/test_critical_fixes.py",
    "src/tests/unit/test_dockerignore_egg_info.py",
    "src/tests/unit/test_cascor_fix.py",
    "src/tests/unit/test_final.py",
    "src/tests/unit/test_hdf5.py",
]

BANNER = (
    "# CI's unit lane runs ``pytest -m \"unit and not slow\" src/tests/unit`` (ci.yml:312-317),\n"
    "# so a test here with no ``unit`` marker is collected and then silently DESELECTED -- it\n"
    "# never runs and the job still reports success. Module-level, so it covers every test in\n"
    "# the file including ones added later.\n"
    "pytestmark = pytest.mark.unit\n"
)

IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+\S", re.M)
DOCSTRING_RE = re.compile(r'^\s*(?:"""|\'\'\')')


def insert_marker(text):
    """Return (new_text, note) or (None, reason-for-refusal)."""
    if re.search(r"^\s*pytestmark\s*=", text, re.M):
        return None, "already defines pytestmark -- merging is a judgement call, left alone"

    lines = text.splitlines(keepends=True)

    # find the last top-level import line
    last_import = None
    for i, line in enumerate(lines):
        if re.match(r"^(?:import|from)\s+\S", line):
            last_import = i
    if last_import is None:
        return None, "no top-level import block found -- cannot place the marker unambiguously"

    # walk past a multi-line parenthesised import
    idx = last_import
    if "(" in lines[idx] and ")" not in lines[idx]:
        while idx + 1 < len(lines) and ")" not in lines[idx]:
            idx += 1

    needs_pytest_import = not re.search(r"^\s*import pytest\b", text, re.M)
    block = ""
    if needs_pytest_import:
        block += "import pytest\n"
    block = "\n" + block + "\n" + BANNER if not needs_pytest_import else "\n" + "import pytest\n" + "\n" + BANNER

    new = "".join(lines[: idx + 1]) + block + "".join(lines[idx + 1 :])
    note = "marker added" + (" (+ import pytest)" if needs_pytest_import else "")
    return new, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, help="directory to write patched copies into")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ok, refused = [], []
    for rel in TARGETS:
        src = os.path.join(CASCOR, rel)
        if not os.path.exists(src):
            refused.append((rel, "file does not exist at CASCOR_ROOT"))
            continue
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        new, note = insert_marker(text)
        if new is None:
            refused.append((rel, note))
            continue
        ok.append((rel, note))
        if not args.dry_run:
            dst = os.path.join(args.staging, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(new)

    print(f"{'would patch' if args.dry_run else 'patched'}: {len(ok)}")
    for rel, note in ok:
        print(f"  + {rel}  [{note}]")
    if refused:
        print(f"\nREFUSED: {len(refused)} -- handle these by hand")
        for rel, why in refused:
            print(f"  ! {rel}\n      {why}")
    if not args.dry_run:
        print(f"\nstaged under {args.staging}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
