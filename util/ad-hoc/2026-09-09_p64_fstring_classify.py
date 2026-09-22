#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, ROADMAP decision 6 / P6.4)
Application: ad-hoc analysis
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: classify the LIVE Path-A f-string logger call sites in juniper-cascor by
the conversion hazard each one carries, so the P6.4 ("%-args where trivial")
decision is taken against real counts rather than an estimate.

Population, per RECON 3.1: tracked src/, less cascade_correlation/backups/ (dead),
less src/api/ (stdlib-bound, not Path A), less src/tests/.

Read-only. Prints a table plus samples.
"""
import re
import subprocess
import sys
from collections import Counter, defaultdict

import os  # noqa: E402

CASCOR = os.environ.get("P64_CASCOR", "/home/pcalnon/Development/python/Juniper/juniper-cascor")

#: The revision to classify. **Defaults to `origin/main`, NOT `HEAD`** -- and that is the whole
#: point of this knob. On 2026-09-22 a re-run of this script reported counts byte-identical to the
#: 2026-09-09 run, which read as confirmation that nothing had drifted. It was not: the shared
#: `juniper-cascor` checkout was sitting on another session's branch
#: (`b35fab1 Merge branch 'main' into fix/serena-mcp-file`), so `HEAD` was neither `main` nor
#: current, and cascor#670 -- which had just converted four of these very sites -- was invisible.
#: A stale revision does not announce itself; it returns a plausible number.
#: Override with P64_REV when you genuinely want a different revision.
REV = os.environ.get("P64_REV", "origin/main")

CALL = re.compile(r'\b[Ll]ogger\.(trace|verbose|debug|info|warning|error|critical|fatal)\(\s*f"')
FIELD = re.compile(r"\{([^{}]*)\}")
SPEC = re.compile(r":[^}]*$")
EXPR = re.compile(r"[()\[\]+\-*/]|\.\w+\(")


def tracked_files():
    out = subprocess.run(
        ["git", "-C", CASCOR, "grep", "-l", "-E", CALL.pattern, REV, "--",
         "src", ":!src/cascade_correlation/backups", ":!src/api", ":!src/tests"],
        capture_output=True, text=True, check=False).stdout
    return [ln.split(":", 1)[1] for ln in out.splitlines() if ":" in ln]


def main():
    # Print the provenance FIRST. A count without the revision it was taken at is not a
    # measurement, and this script produced a stale one once by reading a shared checkout's HEAD.
    sha = subprocess.run(["git", "-C", CASCOR, "rev-parse", "--short=8", REV],
                         capture_output=True, text=True, check=False).stdout.strip()
    if not sha:
        sys.exit(f"FATAL: {REV!r} does not resolve in {CASCOR} -- fetch first, or set P64_REV.")
    print(f"repo: {CASCOR}\nrev : {REV} ({sha})\n")

    counts = Counter()
    per_file = defaultdict(Counter)
    samples = defaultdict(list)
    total = 0
    for path in tracked_files():
        blob = subprocess.run(["git", "-C", CASCOR, "show", f"{REV}:{path}"],
                              capture_output=True, text=True, check=False).stdout
        for n, line in enumerate(blob.splitlines(), 1):
            if not CALL.search(line):
                continue
            if line.lstrip().startswith("#"):
                continue
            total += 1
            fields = FIELD.findall(line)
            # classify: most-severe first
            if re.search(r'f"[^"]*%', line):
                kind = "H1 literal-% (raises at emit)"
            elif any(SPEC.search(f) for f in fields):
                kind = "H2 format-spec (precision = parsing surface)"
            elif any(EXPR.search(f) for f in fields):
                kind = "expression arg (eager either way)"
            elif fields:
                kind = "MECHANICAL plain {name}"
            else:
                kind = "MECHANICAL no fields (f-prefix is spurious)"
            counts[kind] += 1
            per_file[path][kind] += 1
            if len(samples[kind]) < 4:
                samples[kind].append(f"{path}:{n}: {line.strip()[:190]}")

    print(f"LIVE Path-A f-string logger call sites: {total}\n")
    print(f"{'class':<48} {'n':>5}  {'%':>6}")
    print("-" * 64)
    for kind, n in counts.most_common():
        print(f"{kind:<48} {n:>5}  {100*n/total:>5.1f}%")
    print("-" * 64)
    mech = sum(v for k, v in counts.items() if k.startswith("MECHANICAL"))
    print(f"{'MECHANICAL subtotal (P6.4 is scoped to these)':<48} {mech:>5}  {100*mech/total:>5.1f}%")
    haz = sum(v for k, v in counts.items() if k.startswith(("H1", "H2")))
    print(f"{'HAZARD subtotal (H1+H2, excluded by P6.4 filter)':<48} {haz:>5}  {100*haz/total:>5.1f}%")

    print("\n\n=== SAMPLES ===")
    for kind, _ in counts.most_common():
        print(f"\n--- {kind} ---")
        for s in samples[kind]:
            print(f"  {s}")

    print("\n\n=== BY FILE (top 8) ===")
    for path, c in sorted(per_file.items(), key=lambda kv: -sum(kv[1].values()))[:8]:
        print(f"  {sum(c.values()):>4}  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
