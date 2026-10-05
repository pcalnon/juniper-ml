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
"""Close every file the archived Phase 10 round-1 lane probes open, so juniper-ml#2157 can merge.

CodeQL posted 20 review threads on the probes ``util/ad-hoc/2026-10-04_phase10_r1_*`` (19 of
``py/file-not-always-closed``, 1 ``py/unused-import``), and an unresolved thread blocks the merge
(memory ``reference_codeql_unused_global_cascor``: fix the code, never suppress). Each edit below moves an
``open()`` into a ``with`` block, or drops the unused ``import re``; what each probe computes is unchanged.

The probes were archived verbatim, and their header says so, so each touched header is amended to say what
changed and why. Every ``old`` must occur exactly once in its file, or nothing is written.

Usage:
    python3 util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py [--check]
"""

import argparse
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
PREFIX = "2026-10-04_phase10_r1_"
VERBATIM = "# Everything below this block is the lane's file, unmodified."
AMENDED = (
    "# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens\n"
    "# (CodeQL py/file-not-always-closed on juniper-ml#2157{extra}); what it computes is unchanged.\n"
    "# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py."
)

#: file suffix -> list of (old, new); each old must occur exactly once.
EDITS: dict[str, list[tuple[str, str]]] = {
    "b2_check_lines.py": [
        (
            '    src = open(os.path.join(T, rel), encoding="utf-8").read().splitlines()\n',
            '    with open(os.path.join(T, rel), encoding="utf-8") as fh:\n        src = fh.read().splitlines()\n',
        ),
    ],
    "b2_probe_toast.py": [
        ("rec = json.load(open(ARCHIVE))\n", "with open(ARCHIVE) as fh:\n    rec = json.load(fh)\n"),
    ],
    "b2_probe_relay.py": [
        (
            'consts_src = open(os.path.join(CASCOR_SRC, "cascor_constants/constants_api/constants_api_defaults.py")).read()\n',
            'with open(os.path.join(CASCOR_SRC, "cascor_constants/constants_api/constants_api_defaults.py")) as fh:\n    consts_src = fh.read()\n',
        ),
        (
            'json.dump(CAPTURED, open(os.path.join(SCRATCH, "relayed_frames.json"), "w"))\n',
            'with open(os.path.join(SCRATCH, "relayed_frames.json"), "w") as fh:\n    json.dump(CAPTURED, fh)\n',
        ),
        (
            'mp_src = open(os.path.join(CANOPY_SRC, "frontend/components/metrics_panel.py")).read()\n',
            'with open(os.path.join(CANOPY_SRC, "frontend/components/metrics_panel.py")) as fh:\n    mp_src = fh.read()\n',
        ),
        (
            'open(os.path.join(SCRATCH, "extend_traces_fn.js"), "w").write(js)\n',
            'with open(os.path.join(SCRATCH, "extend_traces_fn.js"), "w") as fh:\n    fh.write(js)\n',
        ),
    ],
    "b2_inspect_hist.py": [("d = json.load(open(path))\n", "with open(path) as fh:\n    d = json.load(fh)\n")],
    "b2_inspect_hist2.py": [("d = json.load(open(path))\n", "with open(path) as fh:\n    d = json.load(fh)\n")],
    "a2_my_f060_stage_a.py": [('json.dump(out, open(OUT, "w"), indent=1)\n', 'with open(OUT, "w") as fh:\n    json.dump(out, fh, indent=1)\n')],
    "a2_my_f060_stage_b.py": [("data = json.load(open(IN))\n", "with open(IN) as fh:\n    data = json.load(fh)\n")],
    "a2_mutate.py": [
        ("    text = open(path).read()\n", "    with open(path) as fh:\n        text = fh.read()\n"),
        ('    open(path, "w").write(text.replace(old, new))\n', '    with open(path, "w") as fh:\n        fh.write(text.replace(old, new))\n'),
    ],
    "a2_c3_captures.py": [
        ("        p = json.load(open(pt))\n", "        with open(pt) as fh:\n            p = json.load(fh)\n"),
        ("        j = json.load(open(t))\n", "        with open(t) as fh:\n            j = json.load(fh)\n"),
        (
            '    h = json.load(open(f"{d}/13_render_api_metrics_history_limit_0.json"))\n',
            '    with open(f"{d}/13_render_api_metrics_history_limit_0.json") as fh:\n        h = json.load(fh)\n',
        ),
    ],
    "a2_c1_timeline.py": [
        ("import os\nimport re\nfrom datetime", "import os\nfrom datetime"),
        ('    s = json.load(open(f"{d}summary.json"))\n', '    with open(f"{d}summary.json") as fh:\n        s = json.load(fh)\n'),
        ('    idx = json.load(open(f"{d}index.json"))\n', '    with open(f"{d}index.json") as fh:\n        idx = json.load(fh)\n'),
        ("        j = json.load(open(t))\n", "        with open(t) as fh:\n            j = json.load(fh)\n"),
        (
            'lines = [l for l in open(f"{ROOT}/00_stack/logs/juniper-canopy.log", errors="replace") if "Network stats API returned 503" in l]\n',
            'with open(f"{ROOT}/00_stack/logs/juniper-canopy.log", errors="replace") as fh:\n    lines = [l for l in fh if "Network stats API returned 503" in l]\n',
        ),
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="apply in memory only; write nothing")
    args = ap.parse_args()
    out = {}
    for suffix, edits in EDITS.items():
        path = ADHOC / f"{PREFIX}{suffix}"
        text = path.read_text(encoding="utf-8")
        if text.count(VERBATIM) != 1:
            raise SystemExit(f"{path.name}: the verbatim header line is not there exactly once; nothing written")
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                raise SystemExit(f"{path.name}: anchor found {n} times; nothing written: {old[:80]!r}")
            text = text.replace(old, new)
        extra = "; and py/unused-import, so `import re` is gone" if suffix == "a2_c1_timeline.py" else ""
        out[path] = text.replace(VERBATIM, AMENDED.format(extra=extra))
        print(f"{path.name}: {len(edits)} edit(s)")
    if not args.check:
        for path, text in out.items():
            path.write_text(text, encoding="utf-8")
        print(f"written: {len(out)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
