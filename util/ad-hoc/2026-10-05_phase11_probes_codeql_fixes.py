#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — one-off; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Fix the CodeQL alerts predicted on the archived Phase 11 lane probes before their PR is opened.

juniper-ml#2157 (Phase 10) drew 20 CodeQL review threads on its archived lane probes, and an unresolved thread
blocks a merge while every check reads green (memory ``reference_codeql_unused_global_cascor``: fix the code,
never suppress). ``util/ad-hoc/2026-10-05_codeql_python_prescreen.py``, which reproduces #2157's 20 threads
exactly and reports nothing on Phase 10's 33 merged scripts, predicts 51 alerts on the Phase 11 probes: 44 on
rounds 1 and 2's ``util/ad-hoc/2026-10-05_phase11_r{1,2}_*.py`` and 7 on round 3's
``util/ad-hoc/2026-10-08_phase11_r3_*.py``. It predicts none on the census scripts or the readers. Each edit below
moves an ``open()`` into a ``with`` block, or drops an import or a binding that nothing reads; what each probe
computes and prints is unchanged.

The probes were archived verbatim by ``util/ad-hoc/2026-10-05_archive_phase11_lane_probes.py``, and their
header says so, so each touched header is amended to say what changed and why. Every ``old`` must occur exactly
once in its file, and no file with an ``open()`` edit may already use the name ``fh``, or nothing is written. After the edits,
every touched file must compile and the prescreen must report nothing on it.

Round 4's probes (``util/ad-hoc/2026-10-08_phase11_r4_*.py``) were archived after this pass first ran, so they
carry their own 7 predicted alerts and are fixed by a second run, ``--round r4``; an empty handler there gains a
comment saying why it is empty (``py/empty-except``). Round 5's (``util/ad-hoc/2026-10-08_phase11_r5_*.py``)
carry 5 and are fixed by a third, ``--round r5``. A probe already fixed no longer carries the verbatim header
line, so a run must name only rounds not yet fixed.

Usage:
    python3 util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py [--round r1 --round r2 ...] [--check]
"""

import argparse
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
#: each round's archive prefix, by the first two characters of a probe's suffix
PREFIX = {"r1": "2026-10-05_phase11_", "r2": "2026-10-05_phase11_", "r3": "2026-10-08_phase11_", "r4": "2026-10-08_phase11_", "r5": "2026-10-08_phase11_"}
VERBATIM = "# Everything below this block is the lane's file, unmodified."
AMENDED = (
    "# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL ({what}),\n"
    "# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.\n"
    "# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py."
)
WHAT = {
    "open": "py/file-not-always-closed: it closes the files it opens",
    "import": "py/unused-import: an import nothing reads is gone",
    "local": "py/unused-local-variable: a binding nothing reads is gone",
    "global": "py/unused-global-variable: a binding nothing reads is gone",
    "except": "py/empty-except: an empty handler now says why it is empty",
}


def W(old: str) -> tuple[str, str, str]:
    """Rewrite one single-line statement holding one ``open(...)`` call as a ``with`` block around it."""
    indent = old[: len(old) - len(old.lstrip())]
    body = old.strip()
    starts = [m.start() for m in re.finditer(r"(?<![\w.])open\(", body)]
    if len(starts) != 1:
        raise SystemExit(f"W(): expected one open( in {old!r}")
    i = starts[0]
    j, depth = i + len("open("), 1
    while depth:
        depth += {"(": 1, ")": -1}.get(body[j], 0)
        j += 1
    call = body[i:j]
    return (old, f"{indent}with {call} as fh:\n{indent}    {body[:i]}fh{body[j:]}\n", "open")


def D(old: str, kind: str, new: str = "") -> tuple[str, str, str]:
    """Drop (or narrow) an import or a binding nothing reads."""
    return (old, new, kind)


#: probe suffix -> list of (old, new, kind); each old must occur exactly once.
EDITS: dict[str, list[tuple[str, str, str]]] = {
    "r1_a1_extract_interval.py": [D("import json, sys\n", "import", "import json\n")],
    "r1_a1_fire_ranges.py": [W("    res = rt.analyze(json.load(open(p)))\n")],
    "r1_a1_lane_types.py": [W("    d = json.load(open(p))\n")],
    "r1_a1_late_ranges.py": [W("    res = rt.analyze(json.load(open(p)))\n")],
    "r1_a1_write_pairs.py": [W('    d = json.load(open(p)); raw = d["raw"]\n')],
    "r1_a2_backdate.py": [
        D("from collections import Counter, defaultdict\n", "import", "from collections import defaultdict\n"),
        W('    L = json.load(open(p))["raw"]["lane"]\n'),
    ],
    "r1_a2_enabled_check.py": [D("import importlib.util, sys, io, contextlib, json\n", "import", "import importlib.util, sys, io, contextlib\n")],
    "r1_a2_mech.py": [D("import json\n", "import")],
    "r1_a2_myreader.py": [
        W("    d = json.load(open(path))\n"),
        D('    lane_first = min(x[0] for x in raw["lane"])\n', "local"),
    ],
    "r1_a2_replay_innermost.py": [D("orig = m.lane_timeline\n", "global")],
    "r1_a2_variants.py": [D("import importlib.util, sys, io, contextlib, statistics, math\n", "import", "import importlib.util, sys, io, contextlib, statistics\n")],
    "r1_a3_dump.py": [W("d = json.load(open(sys.argv[1]))\n")],
    "r1_a3_pairing.py": [D("import sys\n", "import")],
    "r1_a3_pyc_check.py": [W('b = open(pyc, "rb").read()\n'), W('s = open(src, encoding="utf-8").read()\n')],
    "r1_a3_stamp_skew.py": [
        D("import bisect\n", "import"),
        D("        eps, start, prev = [], None, False\n", "local", "        eps, start = [], None\n"),
    ],
    "r1_a3_wd_chance.py": [D("import statistics\n", "import")],
    "r1_a3_wd_more.py": [D("import statistics\n", "import")],
    "r1_b1_misc.py": [D("import statistics\n", "import")],
    "r1_b2_probe1.py": [W("    return json.load(open(p))\n")],
    "r1_b2_probe2.py": [W("    d = json.load(open(path))\n")],
    "r1_b2_probe3.py": [W("    d = json.load(open(path))\n")],
    "r1_b2_probe4.py": [D("import bisect\n", "import"), W("    d = json.load(open(path))\n")],
    "r1_b2_probe5.py": [W("    d = json.load(open(path))\n")],
    "r1_b2_probe7.py": [
        W("    d = json.load(open(p))\n"),
        (
            'for line in open("ev/2026-10-05_synth_check.jsonl"):\n    o = json.loads(line)\n    print(" synth:", {k: o[k] for k in list(o)[:4]})\n',
            'with open("ev/2026-10-05_synth_check.jsonl") as fh:\n    for line in fh:\n        o = json.loads(line)\n        print(" synth:", {k: o[k] for k in list(o)[:4]})\n',
            "open",
        ),
    ],
    "r2_a_horizon.py": [W("    d = json.load(open(p))\n")],
    "r2_a_jitter_dist_old.py": [D("import collections\n", "import")],
    "r2_a_myreader.py": [
        W("    return json.load(open(p))\n"),
        D('        back_imm = [c["t"] - c["enc"][0] for c in sm if c["enc"]]\n', "local"),
    ],
    "r2_a_myreplay.py": [W("    d = json.load(open(path))\n")],
    "r2_a_stall.py": [W('    raw = json.load(open(p))["raw"]\n')],
    "r2_a_trig.py": [W("    d = json.load(open(p))\n")],
    "r2_a_types.py": [W('    raw = json.load(open(p))["raw"]\n')],
    "r2_b_a_to_w.py": [W("    d = json.load(open(path))\n")],
    "r2_b_pairing_blindspot.py": [W("d = json.load(open(sys.argv[3]))\n")],
    "r2_b_peek2.py": [W("d = json.load(open(sys.argv[1]))\n")],
    "r2_b_peek.py": [W("d = json.load(open(sys.argv[1]))\n")],
    "r2_b_reenables.py": [W("    d = json.load(open(path))\n")],
    "r2_b_x_to_w.py": [W("    d = json.load(open(path))\n")],
    "r3_a_myhorizon.py": [D("import sys\n", "import")],
    "r3_b_horizon.py": [W('d = json.load(open(sys.argv[1], encoding="utf-8"))\n')],
    "r3_b_late_to_x.py": [W('    d = json.load(open(path, encoding="utf-8"))\n')],
    "r3_b_p1_headers.py": [W('text = open("/tmp/tmp.cIFAKjB6BD/7af/ledger.md", encoding="utf-8").read()\n')],
    "r3_b_peek.py": [W('d = json.load(open(sys.argv[1], encoding="utf-8"))\n')],
    "r3_b_r2b_case.py": [W('d = json.load(open(sys.argv[1], encoding="utf-8"))\n')],
    "r3_b_reenable_to_x.py": [W('    d = json.load(open(path, encoding="utf-8"))\n')],
    "r4_a_lane_interrupt.py": [
        D(
            "            except json.JSONDecodeError:\n                pass\n",
            "except",
            "            except json.JSONDecodeError:\n                pass  # a line that is not JSON carries no timestamp; it is skipped\n",
        )
    ],
    "r4_a_prescreen_sweep.py": [D("srcs = []\n", "global")],
    "r4_a_r3_probe_compare.py": [D("import hashlib\n", "import")],
    "r4_b_breakmut.py": [W("d = json.load(open(T1))\n")],
    "r4_b_myreader.py": [D("import sys\n", "import"), W("    d = json.load(open(p))\n")],
    "r4_b_triglag.py": [W("    d = json.load(open(p))\n")],
    "r5_a_cq_ast.py": [D("import sys\n", "import")],
    "r5_a_lane_transcripts.py": [D("import re\n", "import"), D("import sys\n", "import")],
    "r5_a_prescreen_branch.py": [D("import sys\n", "import")],
    "r5_a_triglag.py": [W('    d = json.load(open(p, encoding="utf-8"))\n')],
}


def _prescreen():
    spec = importlib.util.spec_from_file_location("prescreen", ADHOC / "2026-10-05_codeql_python_prescreen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    ap.add_argument("--round", action="append", choices=sorted(PREFIX), help="only these rounds' probes (repeatable; default: all)")
    args = ap.parse_args()
    pre = _prescreen()
    out, n_edits = {}, 0
    for suffix, edits in EDITS.items():
        if args.round and suffix[:2] not in args.round:
            continue
        path = ADHOC / f"{PREFIX[suffix[:2]]}{suffix}"
        text = path.read_text(encoding="utf-8")
        if text.count(VERBATIM) != 1:
            raise SystemExit(f"{path.name}: the verbatim header line is not there exactly once; nothing written")
        if any(kind == "open" for _o, _n, kind in edits) and re.search(r"\bfh\b", text):
            raise SystemExit(f"{path.name}: already uses the name fh; nothing written")
        for old, new, _kind in edits:
            n = text.count(old)
            if n != 1:
                raise SystemExit(f"{path.name}: anchor found {n} times; nothing written: {old[:80]!r}")
            text = text.replace(old, new)
        what = "; ".join(WHAT[k] for k in dict.fromkeys(kind for _o, _n, kind in edits))
        text = text.replace(VERBATIM, AMENDED.format(what=what))
        compile(text, path.name, "exec")
        with tempfile.TemporaryDirectory() as td:
            probe = Path(td) / path.name
            probe.write_text(text, encoding="utf-8")
            left = pre._scan(probe)
        if left:
            raise SystemExit(f"{path.name}: the prescreen still reports {left}; nothing written")
        out[path] = text
        n_edits += len(edits)
        print(f"{path.name}: {len(edits)} edit(s)")
    print(f"{n_edits} edits in {len(out)} files; every file compiles and the prescreen reports nothing on it")
    if not args.check:
        for path, text in out.items():
            path.write_text(text, encoding="utf-8")
        print(f"written: {len(out)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
