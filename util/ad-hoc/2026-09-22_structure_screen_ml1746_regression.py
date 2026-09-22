#!/usr/bin/env python3
"""2026-09-22_structure_screen_ml1746_regression.py -- does the screen still see ml#1746?

Project: juniper-ml
Sub-Project: ad-hoc tooling (gate regression proof)
Application: ad-hoc verification
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`util/ad-hoc/2026-09-05_markdown_structure_check.py` exists because juniper-ml#1746 dropped a
single closing fence in `docs/REFERENCE.md` and swallowed 36 H2 headings. ml#1944 then
NARROWED the screen's fence rule to clear 17 false positives, on the stated premise that
*"a dropped closer leaves the fence UNCLOSED, which is reported in its own right"* and that
*"ml#1746's own fence was bare."*

Both are false, and the second is checkable against the record: ml#1749's repair commit
(`7a4b1cb4`) says the lost line was *"the close of the ``text`` block at REFERENCE.md:1522"*
-- a TYPED fence, the class the narrowing exempts. The first fails because a dropped closer
only leaves a document unclosed when nothing follows it; in a real file the next block's
opener is absorbed and a later bare delimiter re-closes the span, restoring polarity.

The net effect was an instrument blind to its own founding incident, inside a REQUIRED check
(`util/markdown_structure_delta.py` execs this screen in the `Documentation Links` job).

WHAT IT PROVES

Three measurements against the ACTUAL damaged blob, `bcc89c45:docs/REFERENCE.md` -- not a
fixture, because a fixture only pins the shape its author thought of:

  * the PRE-NARROWING screen (`2f8653c6^`)  -> reports the damage   (the baseline)
  * the NARROWED screen      (`2f8653c6`)   -> reports NOTHING       (the regression)
  * the CURRENT screen        (working tree) -> reports the damage   (the repair)

and one measurement that the repair costs nothing: the whole tracked-markdown tree must still
screen clean, or the 17 false positives are back and the narrowing's purpose is lost.

LIMITS

  * It proves detection of ONE incident and absence of false positives on ONE tree. It is not
    a proof that every dropped-closer shape is caught; the unit fixtures in
    `tests/test_markdown_structure_screen.py` carry the shape coverage.
  * It reads three screen versions out of git. A shallow clone without `bcc89c45` or
    `2f8653c6` cannot run it, and it exits 2 rather than reporting a pass it did not measure.

EXIT CODES

  * 0 -- baseline detects, narrowed misses, current detects, tree still clean.
  * 1 -- the current screen missed the damage, or the tree regressed to non-zero.
  * 2 -- a required blob/rev is unavailable, so nothing was measured.

Usage:
    python3 util/ad-hoc/2026-09-22_structure_screen_ml1746_regression.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
SCREEN = REPO / "util" / "ad-hoc" / "2026-09-05_markdown_structure_check.py"

DAMAGED_BLOB = "bcc89c45:docs/REFERENCE.md"   # the ml#1746 merge commit's REFERENCE.md
NARROWING = "2f8653c6"                        # ml#1944, which narrowed the fence rule
SCREEN_REL = "util/ad-hoc/2026-09-05_markdown_structure_check.py"


def _git(*args: str) -> "str | None":
    proc = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def _load(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(f"screen_{abs(hash(str(path)))}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _count(module, target: pathlib.Path) -> int:
    return len([f for f in module.check(target) if "H2 swallowed" in f])


def main() -> int:
    damaged = _git("cat-file", "-p", DAMAGED_BLOB)
    if damaged is None:
        print(f"cannot read {DAMAGED_BLOB} -- nothing was measured", file=sys.stderr)
        return 2

    versions = {}
    for label, rev in (("pre-narrowing", f"{NARROWING}^"), ("narrowed", NARROWING)):
        src = _git("show", f"{rev}:{SCREEN_REL}")
        if src is None:
            print(f"cannot read {rev}:{SCREEN_REL} -- nothing was measured", file=sys.stderr)
            return 2
        versions[label] = src

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        blob = tmp / "REFERENCE_at_1746.md"
        blob.write_text(damaged, encoding="utf-8")

        counts = {}
        for label, src in versions.items():
            p = tmp / f"screen_{label.replace('-', '_')}.py"
            p.write_text(src, encoding="utf-8")
            counts[label] = _count(_load(p), blob)
        counts["current"] = _count(_load(SCREEN), blob)

    for label in ("pre-narrowing", "narrowed", "current"):
        print(f"  {label:<14} -> {counts[label]} 'H2 swallowed' finding(s) on the real ml#1746 blob")

    ok = True
    if counts["pre-narrowing"] == 0:
        print("\nbaseline reported ZERO -- the blob is not the damaged one; nothing was measured", file=sys.stderr)
        return 2
    if counts["narrowed"] != 0:
        print("\nthe narrowed screen DID report -- this script's premise no longer holds", file=sys.stderr)
        return 2
    if counts["current"] < counts["pre-narrowing"]:
        print(f"\nREGRESSION: current screen reports {counts['current']}, baseline {counts['pre-narrowing']}", file=sys.stderr)
        ok = False

    tracked = _git("ls-files", "-z", "*.md")
    if tracked is None:
        print("cannot list tracked markdown -- false-positive arm not measured", file=sys.stderr)
        return 2
    paths = [REPO / p for p in tracked.split("\0") if p]
    screen = _load(SCREEN)
    dirty = [(p, screen.check(p)) for p in paths]
    total = sum(len(f) for _p, f in dirty)
    print(f"\n  whole tree      -> {total} structural problem(s) across {len(paths)} tracked path(s)")
    if total:
        for p, f in dirty:
            if f:
                print(f"      {p.relative_to(REPO)}: {f[0]}")
        print("\nthe repair re-introduced false positives -- the narrowing's purpose is lost", file=sys.stderr)
        ok = False

    if not ok:
        return 1
    print("\nml#1746 is detected again AND the tree still screens clean -- the ml#1944 trade-off was false.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
