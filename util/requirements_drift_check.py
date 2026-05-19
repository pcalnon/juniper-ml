#!/usr/bin/env python3
"""Drift detection for the Juniper requirements snapshot.

Reads ``notes/requirements/id_assignments.yaml`` and reports whether each
entry's cited sources still resolve. Implements ``--mode quick`` from the
spec at ``notes/REQUIREMENTS_NEXT_STEPS.md`` §7: path + structural
line-range validity, no file reads.

``--mode full`` and ``--mode rewrite`` are placeholders for future work
(content-match drift + automatic fixes per the same spec).

Exit codes
----------
0   No drift detected (every source is OK).
1   At least one source is BAD_PATH or BAD_RANGE.
2   Invocation error (missing YAML, unknown mode, etc.).

Project: juniper-ml
Sub-Project: requirements snapshot tooling
Author: Paul Calnon
Created: 2026-05-18
Status: permanent utility (graduates immediately to ``util/``)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - clear failure mode for users
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

DEFAULT_YAML = Path("notes/requirements/id_assignments.yaml")
SNAPSHOT_ECOSYSTEM_ROOT = "/home/pcalnon/Development/python/Juniper"


@dataclass(frozen=True)
class SourceFinding:
    """Result of validating a single (entry, source) pair."""

    entry_id: str
    path: str
    line_start: Any
    line_end: Any
    category: str  # OK | BAD_PATH | BAD_RANGE
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.entry_id,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "category": self.category,
            "detail": self.detail,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="requirements_drift_check.py",
        description=(
            "Validate the Juniper requirements snapshot for citation drift. "
            "See notes/REQUIREMENTS_NEXT_STEPS.md §7 for the spec."
        ),
    )
    p.add_argument(
        "--mode",
        choices=("quick", "full", "rewrite"),
        default="quick",
        help="Detection mode. Only 'quick' is implemented; 'full' and "
        "'rewrite' are reserved for future expansion.",
    )
    p.add_argument(
        "--yaml",
        type=Path,
        default=DEFAULT_YAML,
        help=f"Path to id_assignments.yaml (default: {DEFAULT_YAML}).",
    )
    p.add_argument(
        "--ecosystem-root",
        type=Path,
        default=None,
        help=(
            "If set, rewrite each source path by replacing the "
            f"'{SNAPSHOT_ECOSYSTEM_ROOT}' prefix with this directory. "
            "Useful when the snapshot's absolute paths point at a different "
            "checkout location (e.g., CI, another developer's machine)."
        ),
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON on stdout instead of a human report.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-finding detail in human-mode output; only print the summary.",
    )
    return p.parse_args(argv)


def load_entries(yaml_path: Path) -> list[dict[str, Any]]:
    if not yaml_path.is_file():
        raise FileNotFoundError(f"YAML not found: {yaml_path}")
    with yaml_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected top-level YAML to be a list, got {type(data).__name__}")
    return data


def rewrite_path(raw_path: str, ecosystem_root: Path | None) -> str:
    """Apply --ecosystem-root rewriting if requested."""
    if ecosystem_root is None:
        return raw_path
    if raw_path.startswith(SNAPSHOT_ECOSYSTEM_ROOT + os.sep):
        suffix = raw_path[len(SNAPSHOT_ECOSYSTEM_ROOT) + 1 :]
        return str(ecosystem_root / suffix)
    return raw_path


def validate_range(line_start: Any, line_end: Any) -> str | None:
    """Return an error string if the line range is structurally invalid, else None."""
    if line_start is None or line_end is None:
        return "missing line_start or line_end"
    if not isinstance(line_start, int) or isinstance(line_start, bool):
        return f"line_start is not an integer ({type(line_start).__name__}: {line_start!r})"
    if not isinstance(line_end, int) or isinstance(line_end, bool):
        return f"line_end is not an integer ({type(line_end).__name__}: {line_end!r})"
    if line_start < 1:
        return f"line_start < 1 ({line_start})"
    if line_end < line_start:
        return f"line_end ({line_end}) < line_start ({line_start})"
    return None


def check_quick(
    entries: Iterable[dict[str, Any]],
    ecosystem_root: Path | None,
) -> list[SourceFinding]:
    findings: list[SourceFinding] = []
    for entry in entries:
        entry_id = entry.get("id", "<no-id>")
        for src in entry.get("sources") or ():
            raw_path = src.get("path", "")
            line_start = src.get("line_start")
            line_end = src.get("line_end")
            resolved = rewrite_path(raw_path, ecosystem_root)

            range_err = validate_range(line_start, line_end)
            if range_err is not None:
                findings.append(
                    SourceFinding(
                        entry_id=entry_id,
                        path=raw_path,
                        line_start=line_start,
                        line_end=line_end,
                        category="BAD_RANGE",
                        detail=range_err,
                    )
                )
                continue

            if not raw_path:
                findings.append(
                    SourceFinding(
                        entry_id=entry_id,
                        path=raw_path,
                        line_start=line_start,
                        line_end=line_end,
                        category="BAD_PATH",
                        detail="path is empty",
                    )
                )
                continue

            if not Path(resolved).is_file():
                findings.append(
                    SourceFinding(
                        entry_id=entry_id,
                        path=raw_path,
                        line_start=line_start,
                        line_end=line_end,
                        category="BAD_PATH",
                        detail=f"file not found (resolved to {resolved})",
                    )
                )
                continue

            findings.append(
                SourceFinding(
                    entry_id=entry_id,
                    path=raw_path,
                    line_start=line_start,
                    line_end=line_end,
                    category="OK",
                    detail="",
                )
            )
    return findings


def emit_human(findings: list[SourceFinding], quiet: bool) -> None:
    counts = Counter(f.category for f in findings)
    total = sum(counts.values())
    ok = counts.get("OK", 0)
    bad_path = counts.get("BAD_PATH", 0)
    bad_range = counts.get("BAD_RANGE", 0)
    pct_ok = (100.0 * ok / total) if total else 100.0

    if not quiet:
        bad = [f for f in findings if f.category != "OK"]
        if bad:
            print(f"{'CATEGORY':10s}  {'JR-ID':22s}  {'L_START':>7s}  {'L_END':>7s}  PATH / DETAIL")
            for f in bad:
                print(
                    f"{f.category:10s}  {f.entry_id:22s}  "
                    f"{str(f.line_start):>7s}  {str(f.line_end):>7s}  "
                    f"{f.path}  --  {f.detail}"
                )
            print()

    print("=" * 60)
    print(f"Drift summary (mode: quick)")
    print("=" * 60)
    print(f"  total citations checked: {total}")
    print(f"  OK:        {ok} ({pct_ok:.2f}%)")
    print(f"  BAD_PATH:  {bad_path}")
    print(f"  BAD_RANGE: {bad_range}")
    print("=" * 60)


def emit_json(findings: list[SourceFinding]) -> None:
    counts = Counter(f.category for f in findings)
    payload = {
        "mode": "quick",
        "totals": {
            "checked": sum(counts.values()),
            "ok": counts.get("OK", 0),
            "bad_path": counts.get("BAD_PATH", 0),
            "bad_range": counts.get("BAD_RANGE", 0),
        },
        "findings": [f.as_dict() for f in findings if f.category != "OK"],
    }
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.mode != "quick":
        print(
            f"ERROR: --mode {args.mode} is not yet implemented. "
            "Only --mode quick is available; see notes/REQUIREMENTS_NEXT_STEPS.md §7 "
            "for the full/rewrite spec.",
            file=sys.stderr,
        )
        return 2

    try:
        entries = load_entries(args.yaml)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    findings = check_quick(entries, args.ecosystem_root)

    if args.json:
        emit_json(findings)
    else:
        emit_human(findings, args.quiet)

    has_drift = any(f.category != "OK" for f in findings)
    return 1 if has_drift else 0


if __name__ == "__main__":
    sys.exit(main())
