#!/usr/bin/env python3
"""Render a lock-round PR body's "Tested" section from the per-lock probe's before/after artifacts.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Every number in the section is read from ``<runs>/<repo>-{before,after}/summary.json`` and the
two ``record.json`` files written by ``2026-11-09_lock_round_2_probe.py``, so a PR body cannot
quote a result the artifacts do not hold. The section carries the owner's ruling and the
sentence that this probe is NOT S0.11's relay run.

Usage:
    python3 util/ad-hoc/2026-11-09_lock_round_2_tested_section.py --repo juniper-data \
        --runs tmp/lr2/runs --sha 4f04fc8d --freshness "..." [--note "..."]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RULING = (
    "**The per-lock probe** (owner ruling, 2026-11-09T00:24:20Z: \"Per-lock probe (Recommended)\"). **This is NOT "
    "S0.11's relay run.** The consolidated plan's Security step 4 asks each image lock PR to carry S0.11's relay run, "
    "but S0.11's relay tests (a planted fake key driven through every relay) do not exist yet for juniper-data, "
    "juniper-cascor or juniper-canopy, because A1's F-S10 rulings are open; the owner ruled this probe in its place."
)


def _load(runs: Path, repo: str, label: str) -> tuple[dict, dict]:
    summary = json.loads((runs / f"{repo}-{label}" / "summary.json").read_text())
    record = summary.get("record")
    if not isinstance(record, dict):
        raise SystemExit(f"{repo}-{label}: no telemetry record in summary.json")
    return summary, record


def _wire(summary: dict) -> str:
    probe = summary["wire_probe"]
    if probe["exit"] is None:
        return "not applicable: the lock installs no `sentry-sdk`"
    result = probe["result"].removeprefix("RESULT: ")
    return f"{result} (exit {probe['exit']})"


def _telemetry(record: dict) -> str:
    v = record["versions"]
    parts = [f"Python {record['python']}, FastAPI {v['fastapi']}, Starlette {v['starlette']}, sentry-sdk {v['sentry-sdk'] or 'not installed'}"]
    if record["fastapi_has_native_telemetry"]:
        default = record["fastapi_default_telemetry"] or {}
        on = [key for key in ("tracing", "metrics", "logs", "operation_spans") if default.get(key)]
        parts.append(f"FastAPI's native telemetry, as an app built without `telemetry=` gets it: {', '.join(f'`{k}`' for k in on) or 'nothing'} on, `auto_configure` {default.get('auto_configure')}, no tracer/meter/logger provider passed")
    else:
        parts.append("this FastAPI has no native telemetry (it arrived in 0.142)")
    otel = record["opentelemetry_distributions"]
    parts.append(f"OpenTelemetry installed: {', '.join(f'`{d}`' for d in otel) if otel else 'none'}; SDK, exporter, distro or instrumentation: {', '.join(record['span_paths_present']) or 'none'}; global tracer provider: `{record['otel_tracer_provider']}`; `OTEL_*` variables: {', '.join(record['otel_env_names']) or 'none'}")
    return "; ".join(parts) + "."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--sha", required=True, help="the main SHA both runs were built from")
    parser.add_argument("--freshness", required=True, help="the freshness-replay sentence (markdown)")
    parser.add_argument("--note", action="append", default=[], help="an extra bullet (markdown), repeatable")
    args = parser.parse_args()
    before, before_rec = _load(args.runs, args.repo, "before")
    after, after_rec = _load(args.runs, args.repo, "after")
    suites = after["pytest"]["suites"]
    if suites != before["pytest"]["suites"]:
        raise SystemExit("the before and after runs ran different suites; refusing")
    bv, av = before_rec["versions"], after_rec["versions"]
    out = [
        "## Tested",
        "",
        RULING,
        "",
        f"Each run built a fresh venv from one lock (`uv`; every pin held, the installed set compared with the lock), with the six Sentry DSN variables of plan H-14 set to `\"\"`, then ran P3-07's wire probe (juniper-ml `util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py`: the installed `configure_sentry` sends a request carrying a planted secret in seven headers and two cookies into a capturing transport, as an error event and as transactions, under both `send_pii` values) and the suites below. Driver: juniper-ml `util/ad-hoc/2026-11-09_lock_round_2_run_probes.py`.",
        "",
        f"| | before: `main` `{args.sha}` (observability {bv['juniper-observability']}, service-core {bv['juniper-service-core']}) | after: this PR (observability {av['juniper-observability']}, service-core {av['juniper-service-core']}) |",
        "| --- | --- | --- |",
        f"| Wire probe | {_wire(before)} | {_wire(after)} |",
        f"| Suites ({len(suites)} paths) | {before['pytest']['summary']} (exit {before['pytest']['exit']}) | {after['pytest']['summary']} (exit {after['pytest']['exit']}) |",
        f"| Installed pins that differ from the lock | {len(before['pin_drift'])} of {before['lock_pins']} | {len(after['pin_drift'])} of {after['lock_pins']} |",
        "",
        "Suites: " + ", ".join(f"`{s}`" for s in suites) + ".",
        "",
        f"- **Telemetry** (after): {_telemetry(after_rec)}",
        f"- {args.freshness}",
    ]
    out += [f"- {note}" for note in args.note]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
