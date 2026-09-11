#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.1)
Application: ad-hoc verification
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: run the arc's central probe against a PATCHED copy of juniper-cascor's logger,
to prove P1.1 actually closes the guard/emit split -- BEFORE the change is pushed.

The session that owns this work is confined to a juniper-ml worktree and cannot commit
inside the sibling cascor checkout, so the patched ``log_config`` tree lives in the
scratchpad and is put AHEAD of cascor's ``src`` on sys.path. ``cascor_constants`` and
everything else still resolve to the real checkout, so this exercises the real imports.

Pass criterion, from the handoff's section 11: under ``set_level('TRACE')`` the row
``isEnabledFor(1)`` must read True on the left and -- AFTER P1.1 -- **True on the right
as well**. Before P1.1 it read True/False, and that disagreement IS the defect.

Run with the level vars unset; an exported JUNIPER_CASCOR_LOG_LEVEL seeds both states
identically and masks the very thing being measured.

Read-only with respect to both repositories.
"""
import os
import subprocess
import sys

SCRATCH_DIR = os.environ.get("P11_SCRATCH", "/tmp/claude-1000/p11-scratch")
CASCOR_SRC = os.environ.get("P11_CASCOR_SRC", "/home/pcalnon/Development/python/Juniper/juniper-cascor/src")

#: Directory CONTAINING a ``log_config/`` package to test as the "patched" side. Required --
#: there is deliberately no default, because the original was a session-specific scratchpad path
#: that would silently not exist for anyone else, and a probe pointed at a missing tree reports
#: a difference it did not measure.
#:
#: To check a tree that is already merged, materialise it first:
#:     mkdir -p /tmp/p11merged
#:     git -C <cascor> archive origin/main src/log_config | tar -x -C /tmp/p11merged --strip-components=1
#:     P11_PATCHED_TREE=/tmp/p11merged python3 <this script>
PATCHED = os.environ.get("P11_PATCHED_TREE")

CHILD = r'''
import contextlib, io, sys
sys.path.insert(0, "@@CASCOR@@")
sys.path.insert(0, "@@PATCHED@@")
from log_config.logger.logger import Logger
import log_config.logger.logger as M
print("LOADED_FROM=" + M.__file__)

# (name, numeric, the public method that emits at it)
LEVELS = (("TRACE", 1, "trace"), ("VERBOSE", 5, "verbose"),
          ("DEBUG", 10, "debug"), ("INFO", 20, "info"))

def emits(method, marker):
    """Drive the REAL emit path and observe whether a record came out.

    Deliberately NOT a reconstruction of the threshold expression: an earlier version of
    this harness recomputed it as ``_filter_by_level(level, _log_level)``, which IS the
    patched behaviour, so the unpatched baseline showed no split and the probe silently
    stopped measuring the defect. Calling the public method and watching stdout exercises
    whatever the code under test actually does.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        getattr(Logger, method)(marker)
    return marker in buf.getvalue()

def snapshot(tag):
    print("BLOCK " + tag)
    print("  _log_level=" + repr(Logger._log_level))
    for name, num, method in LEVELS:
        guard = Logger.isEnabledFor(level=num)
        emit = emits(method, f"__P11_{tag}_{name}__")
        print(f"  ROW {name} guard={guard} emit={emit} agree={guard == emit}")

snapshot("A-fresh")
Logger.set_level("VERBOSE"); snapshot("B-verbose")
Logger.set_level("TRACE");   snapshot("C-trace")
Logger.set_configured();     snapshot("D-configured")

print("VALIDITY is_valid_level('BANANA')=" + repr(Logger.is_valid_level("BANANA")))
print("VALIDITY is_valid_level(None)=" + repr(Logger.is_valid_level(None)))
print("VALIDITY is_valid_level('DEBUG')=" + repr(Logger.is_valid_level("DEBUG")))
print("VALIDITY is_valid_level(10)=" + repr(Logger.is_valid_level(10)))
print("VALIDITY is_valid_level(8)=" + repr(Logger.is_valid_level(8)))
'''


def run(tree_label, patched_first):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    # The emit path also WRITES a record. Give each run its own log dir so this probe can
    # never interleave with, or rotate away, a live run's evidence (ROADMAP trap 1).
    logdir = os.path.join(SCRATCH_DIR, f"p11-logs-{'patched' if patched_first else 'baseline'}")
    os.makedirs(logdir, exist_ok=True)
    env["JUNIPER_CASCOR_LOG_DIR"] = logdir
    src = CHILD.replace("@@CASCOR@@", CASCOR_SRC)
    src = src.replace("@@PATCHED@@", PATCHED if patched_first else CASCOR_SRC)
    out = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True,
                         env=env, check=False)
    if out.returncode != 0:
        print(f"--- {tree_label}: CHILD FAILED\n{out.stderr[-1500:]}")
        return None
    return out.stdout


def parse(text):
    blocks, cur, extra = {}, None, {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("BLOCK "):
            cur = line.split(None, 1)[1]
            blocks[cur] = []
        elif line.startswith("ROW ") and cur:
            parts = dict(p.split("=", 1) for p in line.split()[2:])
            blocks[cur].append((line.split()[1], parts["guard"] == "True", parts["emit"] == "True"))
        elif line.startswith("VALIDITY ") or line.startswith("LOADED_FROM="):
            k, v = line.replace("VALIDITY ", "").split("=", 1)
            extra[k] = v
    return blocks, extra


def show(label, text):
    blocks, extra = parse(text)
    print(f"\n===== {label} =====")
    print(f"  loaded: {extra.get('LOADED_FROM')}")
    worst = []
    for name, rows in blocks.items():
        flags = " ".join(f"{lv}:{'ok' if g == e else 'SPLIT'}" for lv, g, e in rows)
        print(f"  {name:<14} {flags}")
        worst += [(name, lv) for lv, g, e in rows if g != e]
    return blocks, extra, worst


def main():
    if not PATCHED:
        print("P11_PATCHED_TREE is not set.\n")
        print("Set it to a directory containing a log_config/ package, e.g.:")
        print("  mkdir -p /tmp/p11merged")
        print(f"  git -C <cascor> archive origin/main src/log_config | tar -x -C /tmp/p11merged --strip-components=1")
        print("  P11_PATCHED_TREE=/tmp/p11merged python3 util/ad-hoc/2026-09-11_p11_verify_patched_logger.py")
        return 2
    if not os.path.isdir(os.path.join(PATCHED, "log_config")):
        print(f"P11_PATCHED_TREE={PATCHED!r} has no log_config/ subdirectory.")
        print("Refusing to run: a probe pointed at a missing tree would report a difference it")
        print("did not measure.")
        return 2

    before = run("BASELINE (unpatched cascor)", patched_first=False)
    after = run("PATCHED (P1.1)", patched_first=True)
    if before is None or after is None:
        return 2

    _, xb, split_before = show("BASELINE — cascor as it ships today", before)
    _, xa, split_after = show("PATCHED — with P1.1 applied", after)

    print("\n===== VERDICT =====")
    print(f"  guard/emit disagreements BEFORE : {len(split_before)}  {split_before}")
    print(f"  guard/emit disagreements AFTER  : {len(split_after)}  {split_after}")

    ok = True
    if not split_before:
        print("  !! BASELINE shows no split -- the probe is not measuring the defect. Check env.")
        ok = False
    if split_after:
        print("  !! PATCHED still splits -- P1.1 is NOT complete.")
        ok = False
    if ok:
        print("  P1.1 closes the split: every level agrees on both paths, in all four blocks.")

    print("\n  is_valid_level, BEFORE -> AFTER:")
    for key in ("is_valid_level('BANANA')", "is_valid_level(None)",
                "is_valid_level('DEBUG')", "is_valid_level(10)", "is_valid_level(8)"):
        b, a = xb.get(key), xa.get(key)
        mark = "" if b == a else "   <-- changed"
        print(f"    {key:<26} {b!s:<6} -> {a!s:<6}{mark}")
    if xa.get("is_valid_level('BANANA')") != "False" or xa.get("is_valid_level(None)") != "False":
        print("  !! is_valid_level still accepts junk -- P1.1(c) is NOT complete.")
        ok = False
    if xa.get("is_valid_level('DEBUG')") != "True" or xa.get("is_valid_level(10)") != "True":
        print("  !! is_valid_level now REJECTS a valid level -- regression.")
        ok = False

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
