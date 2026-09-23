#!/usr/bin/env python3
"""Cut the P0.4 reference captures -- small, reviewable excerpts of REAL cascor log sinks.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc, roadmap step P0.4(a))
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — one-off (writes the cascor fixture files once; re-run only to re-capture)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md §3.1 (P0.4 part a)

WHY THIS EXISTS

P0.4(a) asks for "two reference captures, not one -- the file sink and the redirected-stdout
sink", because they differ: the console formatter omits the function name, and ``print()`` into
a redirected fd is block-buffered while the file path opens and closes per record. A full
capture is 9-15 MB, so this cuts an excerpt that is small enough to review in a PR and still
carries every shape a real run produces.

SELECTION RULE (deterministic, stated so a reviewer can re-derive the excerpt)

For each source file, in ORIGINAL ORDER, keep the union of:

  1. the first 12 lines;
  2. the first 3 lines of every envelope shape present (A_FILE, A_CONSOLE, STD_FILE_S,
     STD_FILE_MS, plus non-record lines, keyed by their first 16 characters);
  3. for every marker in the inventory, the first line that carries all its fragments in order;
  4. the first multi-line record: a record followed by its continuation lines (a message that
     contains a newline -- a tensor repr -- continues WITHOUT an envelope);

then drop any blank lines at the END of the result, so the fixture passes the repository's
end-of-file-fixer hook unchanged.

THE ONE TRANSFORMATION: ``/home/<user>/`` becomes ``~/`` so the fixtures do not carry a local
home directory. Nothing else is edited; every kept line is otherwise byte-identical to its source.

USAGE

    python3 util/ad-hoc/2026-09-22_p04_reference_capture_excerpt.py \\
        --inventory <cascor>/src/tests/fixtures/log_envelope/marker_inventory.json \\
        --out <cascor>/src/tests/fixtures/log_envelope

Exit 0 on success; 2 when a source file is missing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

STATE = Path.home() / ".local/state/juniper-experiments"

#: name -> (source path, the run's cascor revision or None when the run did not record it, note)
SOURCES = {
    "reference_cli_file_sink.txt": (STATE / "p01-logging-at8065ca0f-v3/cli-01/logs/juniper_cascor.log", "8065ca0f5b511121bfb0b4f14107b8dfe41ba82b", "P0.1 corpus run (direct CLI, cap 4), file sink"),
    "reference_cli_stdout_sink.txt": (STATE / "p01-logging-at8065ca0f-v3/cli-01/direct_cli.log", "8065ca0f5b511121bfb0b4f14107b8dfe41ba82b", "P0.1 corpus run (direct CLI, cap 4), redirected stdout"),
    "reference_service_file_sink.txt": (STATE / "20260901T103548Z-befc/logs/juniper_cascor.log.1", None, "2026-09-01 service run cited by RECON section 3, rotated file sink (.1)"),
    "reference_service_stdout_sink.txt": (STATE / "20260901T103548Z-befc/logs/juniper-cascor.log", None, "2026-09-01 service run cited by RECON section 3, redirected stdout+stderr"),
}

_TS = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
SHAPES = {
    "A_FILE": re.compile(rf"^\+\[[^\]:]+: [^\]:]+:\d+\] \({_TS}\) \[[A-Z]+\] "),
    "A_CONSOLE": re.compile(rf"^\+\[[^\]:]+: \d+\] \({_TS}\) \[[A-Z]+\] "),
    "STD_FILE_S": re.compile(rf"^\[[^\]:]+: [^\]:]+:\d+\] \({_TS}\) \[[A-Z]+\] "),
    "STD_FILE_MS": re.compile(rf"^\[[^\]:]+: [^\]:]+:\d+\] \({_TS},\d{{3}}\) \[[A-Z]+\] "),
}
HOME_RE = re.compile(r"/home/[^/\s]+/")


def shape_of(line: str) -> str:
    for name, pat in SHAPES.items():
        if pat.match(line):
            return name
    return "NONRECORD:" + line[:16]


def in_order(line: str, frags: list[str]) -> bool:
    pos = 0
    for frag in frags:
        at = line.find(frag, pos)
        if at < 0:
            return False
        pos = at + len(frag)
    return True


def excerpt(lines: list[str], markers: list[list[str]]) -> list[int]:
    keep: set[int] = set(range(min(12, len(lines))))
    seen_shape: dict[str, int] = {}
    pending = {i: frags for i, frags in enumerate(markers)}
    multiline_done = False
    for idx, line in enumerate(lines):
        shape = shape_of(line)
        if seen_shape.get(shape, 0) < 3:
            keep.add(idx)
            seen_shape[shape] = seen_shape.get(shape, 0) + 1
        for key in [k for k, frags in pending.items() if in_order(line, frags)]:
            keep.add(idx)
            del pending[key]
        if not multiline_done and shape.startswith("NONRECORD") and idx > 0 and not shape_of(lines[idx - 1]).startswith("NONRECORD") and line.strip():
            start = idx - 1
            end = idx
            while end + 1 < len(lines) and shape_of(lines[end + 1]).startswith("NONRECORD"):
                end += 1
            keep.update(range(start, end + 1))
            multiline_done = True
    return sorted(keep)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True, help="marker_inventory.json (from 2026-09-22_p04_log_marker_census.py --emit-inventory)")
    ap.add_argument("--out", required=True, help="the cascor fixtures directory to write into")
    args = ap.parse_args(argv)
    markers = [m["fragments"] for m in json.loads(Path(args.inventory).read_text(encoding="utf-8"))["markers"]]
    out_dir = Path(args.out)
    provenance: dict[str, dict] = {}
    for name, (src, rev, note) in SOURCES.items():
        if not src.is_file():
            print(f"excerpt: missing source {src}", file=sys.stderr)
            return 2
        raw = src.read_bytes()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        kept = excerpt(lines, markers)
        # The fixture must survive the repository's end-of-file-fixer and trailing-whitespace
        # hooks byte-for-byte, or its recorded line count stops matching: drop blank lines at the
        # END of the excerpt (blank lines inside it are untouched by both hooks), and refuse a
        # kept line with trailing whitespace rather than let a hook rewrite it silently.
        while kept and not lines[kept[-1]].strip():
            kept.pop()
        bad = [i + 1 for i in kept if lines[i] != lines[i].rstrip()]
        if bad:
            print(f"excerpt: {name}: source lines {bad[:8]} end in whitespace; a pre-commit hook would rewrite them", file=sys.stderr)
            return 2
        body = "\n".join(HOME_RE.sub("~/", lines[i]) for i in kept) + "\n"
        (out_dir / name).write_text(body, encoding="utf-8")
        provenance[name] = {
            "note": note,
            "source": str(src).replace(str(Path.home()), "~"),
            "source_bytes": len(raw),
            "source_lines": len(lines),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "cascor_rev": rev,
            "kept_lines": len(kept),
            "kept_source_line_numbers": [i + 1 for i in kept],
        }
        print(f"excerpt: {name}: kept {len(kept)} of {len(lines):,} lines from {src}")
    (out_dir / "reference_captures.json").write_text(json.dumps({"generated_by": "juniper-ml/util/ad-hoc/2026-09-22_p04_reference_capture_excerpt.py", "transformation": "/home/<user>/ -> ~/ (only)", "captures": provenance}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
