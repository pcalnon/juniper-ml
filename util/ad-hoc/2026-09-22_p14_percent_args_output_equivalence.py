#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.4)
Application: ad-hoc verification
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: prove that P1.4's f-string -> %-args conversion in
``CandidateUnit._display_training_progress`` is OUTPUT-IDENTICAL, by driving the REAL cascor
``Logger`` and comparing the emitted text, not by reasoning about it.

§5 of ``notes/JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-CALL-SITE-MIGRATION-ANALYSIS.md`` names
four conversion hazards. Three bear on these four messages:

  1. **A literal ``%`` becomes a format spec.** ``f"progress {pct}%"`` -> ``"progress %s%"`` raises
     ``ValueError: incomplete format`` AT EMIT TIME -- i.e. only at a level that emits, which is why
     a suppressed site can carry it for months. Checked here by scanning the templates.
  2. **Format specs do not survive.** ``f"{x:.4f}"`` must become ``"%.4f"``. None of these four
     messages carries a spec; asserted rather than assumed.
  3. **A lone tuple argument splats.** ``msg % args`` where ``args`` is a tuple spreads it across
     the placeholders. ``residual_error.shape`` is a ``torch.Size``, which **is a tuple subclass**,
     so this is a live hazard at the ``verbose`` site -- the one message the arc most cares about.

The instrument renders each message BOTH ways with representative values and compares the strings
byte for byte, then drives the real ``Logger`` at an enabled level and compares what actually
reaches the sink. A reasoning error in this file cannot produce a false pass, because the
comparison is between two independently-constructed strings.

ANTI-VACUITY: a deliberately WRONG conversion is included and must be reported as DIFFERENT. If the
comparison cannot fail, it is not a comparison.

Usage:
    python 2026-09-22_p14_percent_args_output_equivalence.py [--tree <cascor-tree>]
"""
import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

DEFAULT_TREE = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--logging-p14-guard-display-progress--20260922-0530--0c14e92d"


def _bootstrap(tree: str):
    src = Path(tree) / "src"
    if not (src / "log_config" / "logger" / "logger.py").is_file():
        sys.exit(f"FATAL: no logger under {src}")
    sys.path[:0] = [str(src)]
    from log_config.logger.logger import Logger  # noqa: E402

    resolved = str(Path(sys.modules[Logger.__module__].__file__).resolve())
    assert resolved.startswith(str(Path(tree).resolve())), f"Logger outside tree: {resolved}"
    return Logger, resolved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=DEFAULT_TREE)
    args = ap.parse_args()

    Logger, logger_file = _bootstrap(args.tree)
    import torch

    print(f"Logger: {logger_file}\n")

    # Representative values, matching the real call site's types.
    epoch = 41
    display_frequency = 10
    candidate_display_progress = None
    residual_error = torch.zeros((128, 64), dtype=torch.float32)

    #: (label, f-string rendering, %-template, %-args)
    CASES = [
        (
            "debug :731 display frequency",
            f"CandidateUnit: _display_training_progress: Display frequency: {display_frequency}, Current Epoch: {epoch + 1}",
            "CandidateUnit: _display_training_progress: Display frequency: %s, Current Epoch: %d",
            (display_frequency, epoch + 1),
        ),
        (
            "debug :734 display function",
            f"CandidateUnit: _display_training_progress: Display function: Type: {type(candidate_display_progress)}, Value: {candidate_display_progress}",
            "CandidateUnit: _display_training_progress: Display function: Type: %s, Value: %s",
            (type(candidate_display_progress), candidate_display_progress),
        ),
        (
            "debug :735 re-initialising",
            f"CandidateUnit: _display_training_progress: Display function is None, re-initializing with frequency: Type: {type(display_frequency)}, Value: {display_frequency}",
            "CandidateUnit: _display_training_progress: Display function is None, re-initializing with frequency: Type: %s, Value: %s",
            (type(display_frequency), display_frequency),
        ),
        (
            "verbose :742 residual error  <-- the torch.Size tuple-subclass hazard",
            f"CandidateUnit: train: Epoch {epoch + 1} - Residual Error: Shape: {residual_error.shape}, Dtype: {residual_error.dtype}",
            "CandidateUnit: train: Epoch %d - Residual Error: Shape: %s, Dtype: %s",
            (epoch + 1, residual_error.shape, residual_error.dtype),
        ),
    ]

    failures = []

    print("Hazard 1/2 -- template scan (a literal %% or a surviving format spec)")
    for label, _f, template, _a in CASES:
        stripped = template.replace("%s", "").replace("%d", "")
        assert "%" not in stripped, f"{label}: stray % in template -> {template!r}"
        print(f"  ok  {label}")
    print()

    print("Hazard 3 -- string equivalence (torch.Size IS a tuple subclass)")
    for label, f_form, template, pct_args in CASES:
        pct_form = template % pct_args
        status = "ok " if pct_form == f_form else "DIFF"
        if pct_form != f_form:
            failures.append((label, f_form, pct_form))
        print(f"  {status} {label}")
        if pct_form != f_form:
            print(f"        f-string: {f_form!r}")
            print(f"        %-args  : {pct_form!r}")
    print()

    print("Anti-vacuity -- a deliberately WRONG conversion must be reported DIFFERENT")
    wrong_template = "CandidateUnit: train: Epoch %d - Residual Error: Shape: %s"  # drops Dtype
    wrong = wrong_template % (epoch + 1, residual_error.shape)
    right = CASES[3][1]
    if wrong == right:
        print("  VACUOUS: the comparison cannot distinguish a wrong conversion")
        return 2
    print("  ok  a dropped field is detected\n")

    print("End to end -- drive the REAL Logger at an ENABLED level and compare emitted text")
    saved = Logger._log_level
    try:
        Logger.set_level("TRACE")
        for label, f_form, template, pct_args in CASES:
            buf_f, buf_p = io.StringIO(), io.StringIO()
            with redirect_stdout(buf_f):
                Logger.verbose(f_form)
            with redirect_stdout(buf_p):
                Logger.verbose(template, *pct_args)
            # Strip the per-record prefix (timestamp/line number) and compare the MESSAGE tail.
            got_f = buf_f.getvalue().strip().split("] ", 1)[-1]
            got_p = buf_p.getvalue().strip().split("] ", 1)[-1]
            if not got_f:
                failures.append((label, "<nothing emitted>", "<nothing emitted>"))
                print(f"  DIFF {label}: nothing was emitted -- the check is vacuous")
                continue
            status = "ok " if got_f == got_p else "DIFF"
            if got_f != got_p:
                failures.append((label, got_f, got_p))
            print(f"  {status} {label}")
            if got_f != got_p:
                print(f"        f-string: {got_f!r}")
                print(f"        %-args  : {got_p!r}")
    finally:
        Logger._log_level = saved

    print()
    if failures:
        print(f"RESULT: {len(failures)} DIFFERENCE(S) -- the conversion is NOT output-identical")
        return 1
    print(f"RESULT: all {len(CASES)} messages render identically both ways, "
          f"as strings and through the real Logger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
