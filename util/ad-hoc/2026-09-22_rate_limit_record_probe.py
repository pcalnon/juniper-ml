#!/usr/bin/env python3
"""
Probe the shape of the structured rate-limit records Claude Code writes into session transcripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (evidence for the dynamic-workflow harness design)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why this exists
---------------
The dynamic-workflow harness design (notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md)
needs to know whether a session can OBSERVE its usage-limit state rather than infer it from a
prose error. Session transcripts under ~/.claude/projects/<slug>/*.jsonl carry records with a
`rateLimitType` key (values seen: five_hour, seven_day) alongside `resetsAt`, `overageStatus`,
`overageDisabledReason` and `remaining`. This script reports the exact key path, the field
set, and one masked sample, so the design cites a measured shape rather than an assumed one.

Usage
-----
    python3 util/ad-hoc/2026-09-22_rate_limit_record_probe.py [PROJECT_SLUG_DIR] [--max-files N]

Defaults to the juniper-ml project slug under ~/.claude/projects. Read-only.
"""

from __future__ import annotations

import collections
import glob
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_DIR = os.path.expanduser("~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml")


def walk(obj, path, out):
    if isinstance(obj, dict):
        if "rateLimitType" in obj:
            out.append((path, obj))
        for key, val in obj.items():
            walk(val, f"{path}.{key}", out)
    elif isinstance(obj, list):
        for val in obj:
            walk(val, f"{path}[]", out)


def main(argv):
    target = DEFAULT_DIR
    max_files = 80
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--max-files":
            max_files = int(args.pop(0))
        else:
            target = arg
    files = sorted(glob.glob(os.path.join(target, "*.jsonl")), key=os.path.getmtime, reverse=True)[:max_files]
    shapes = collections.Counter()
    by_type = collections.Counter()
    resets = collections.defaultdict(set)
    sample = None
    total = 0
    for path in files:
        with open(path, errors="ignore") as handle:
            for line in handle:
                if "rateLimitType" not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                found = []
                walk(rec, rec.get("type", "?"), found)
                for keypath, obj in found:
                    total += 1
                    shapes[(keypath, tuple(sorted(obj.keys())))] += 1
                    by_type[obj.get("rateLimitType")] += 1
                    if isinstance(obj.get("resetsAt"), (int, float)):
                        resets[obj.get("rateLimitType")].add(int(obj["resetsAt"]))
                    if sample is None:
                        content = rec.get("message", {}).get("content") if isinstance(rec.get("message"), dict) else None
                        sample = (keypath, obj, {k: rec.get(k) for k in ("type", "isSidechain", "timestamp")}, content)
    print(f"files scanned: {len(files)}  records: {total}")
    for (keypath, keys), count in shapes.most_common(6):
        print(f"  {count:5d}  {keypath}  keys={list(keys)}")
    print("by rateLimitType:", dict(by_type))
    for kind, values in resets.items():
        stamps = sorted(values)
        rendered = [datetime.fromtimestamp(v, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ") for v in stamps[-8:]]
        print(f"distinct resetsAt for {kind}: {len(stamps)} (last 8, UTC): {rendered}")
    if sample:
        keypath, obj, meta, content = sample
        print("SAMPLE keypath:", keypath)
        print("SAMPLE object:", json.dumps(obj)[:700])
        print("SAMPLE record meta:", meta)
        print("SAMPLE message content:", json.dumps(content)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
