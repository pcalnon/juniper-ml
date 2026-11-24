#!/usr/bin/env python3
"""
Correct cascor#640's explanation of WHY --allow-truncated-datasets is inert on main.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (applied to the cascor#640 worktree before that PR was merged)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#640; register row APD-CASCOR-011;
         HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md

The PR's conclusion is right and its reason is wrong. It says main.py "trains the in-process
two-spiral problem, which is synthesised locally ... it never asks juniper-data for anything".
main.py does ask: it resolves ``juniper_data_url``, health-checks ``/v1/health`` and REFUSES to
proceed when the service is unreachable, printing how to start it; ``SpiralDataProvider`` then
fetches over HTTP through ``JuniperDataClient``.

What actually makes the flag inert is narrower and more useful to an operator: the generator on
this path is hardcoded ``spiral``, and ``spiral`` is not in
``_PROJECT_API_TRUNCATABLE_GENERATORS`` — juniper-data synthesises it server-side and always
delivers it in full, so no shortfall can arise for the flag to act on. Same conclusion, a reason
that survives reading the code.

This matters beyond tidiness: the wrong reason tells an operator main.py has no juniper-data
dependency, which would send them the wrong way when the pre-flight check fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--partial-data-follow-ups--20260909-1536--3de89b11")

TRUE_REASON_SHORT = (
    "main.py does fetch its dataset from juniper-data (it health-checks the service first and refuses to run without it), "
    "but the generator on this path is hardcoded `spiral`, which juniper-data synthesises server-side and always delivers in full -- "
    "it is not one of the truncatable generators, so no shortfall can ever arise here for the flag to act on"
)

EDITS = [
    (
        "src/main.py",
        "NO EFFECT ON THIS ENTRY POINT'S OWN RUN: main.py trains the in-process two-spiral problem, which is synthesised locally and can never be partial -- it never asks juniper-data for anything. All this flag does here is EXPORT the environment variable, which configures the SERVICE this process may launch and is what every other entry point (src/server.py, the API's dataset paths) reads. Passing it to a plain `python main.py` changes nothing about that run, and the run logs a warning saying so.",
        "NO EFFECT ON THIS ENTRY POINT'S OWN RUN: " + TRUE_REASON_SHORT + ". All this flag does here is EXPORT the environment variable, which configures the SERVICE this process may launch and is what every other entry point (src/server.py, the API's dataset paths) reads. Passing it to a plain `python main.py` changes nothing about that run, and the run logs a warning saying so.",
    ),
    (
        "src/main.py",
        "    INERT ON THIS ENTRY POINT'S OWN RUN, which is why the warning exists rather\n"
        "    than being left for the operator to infer from an unchanged result. ``main``\n"
        "    reaches only the in-process two-spiral problem, which synthesises its data\n"
        "    locally and cannot be partial; the exported variable is read by the SERVICE\n"
        "    and by the API's dataset paths, and by nothing this process runs afterwards.\n",
        "    INERT ON THIS ENTRY POINT'S OWN RUN, which is why the warning exists rather\n"
        "    than being left for the operator to infer from an unchanged result. Not\n"
        "    because the data is local -- ``main`` DOES fetch from juniper-data, and\n"
        "    refuses to start when ``/v1/health`` is unreachable -- but because the\n"
        "    generator here is hardcoded ``spiral``, which juniper-data synthesises\n"
        "    server-side and always delivers in full. ``spiral`` is not in\n"
        "    ``_PROJECT_API_TRUNCATABLE_GENERATORS``, so no shortfall can arise for the\n"
        "    flag to act on. The exported variable is read by the SERVICE and by the\n"
        "    API's dataset paths, and by nothing else this process runs afterwards.\n",
    ),
    (
        "src/main.py",
        'Logger.warning("Cascor: --allow-truncated-datasets exported JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true, but it has NO EFFECT on this entry point\'s own run: main.py trains the in-process two-spiral problem, which is generated locally and can never be partial. It configures the service this process may launch, and the settings the other entry points read.")',
        'Logger.warning("Cascor: --allow-truncated-datasets exported JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true, but it has NO EFFECT on this entry point\'s own run: this path trains the `spiral` generator, which juniper-data always delivers in full and which is not truncatable, so there is no shortfall here for the flag to act on. It configures the service this process may launch, and the settings the other entry points read.")',
    ),
    (
        "CHANGELOG.md",
        "  does nothing but export `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`, and `main.py` reaches only\n"
        "  the in-process two-spiral problem — synthesised locally, never partial, and it asks juniper-data\n"
        "  for nothing. The readers are the SERVICE this process may launch and the API's dataset paths.\n",
        "  does nothing but export `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`, and the generator `main.py`\n"
        "  reaches is hardcoded `spiral` — which juniper-data synthesises server-side and always delivers\n"
        "  in full, and which is not one of the truncatable generators, so no shortfall can arise here for\n"
        "  the flag to act on. (Note the reason: `main.py` **does** fetch from juniper-data, and refuses to\n"
        "  start when `/v1/health` is unreachable. It is the generator that cannot be partial, not the\n"
        "  data path that is absent.) The readers are the SERVICE this process may launch and the API's\n"
        "  dataset paths.\n",
    ),
]


def main() -> int:
    for rel, old, new in EDITS:
        path = W / rel
        text = path.read_text()
        n = text.count(old)
        if n != 1:
            sys.exit(f"FAIL: {rel}: expected 1 match, found {n} for:\n---\n{old[:180]}\n---")
        path.write_text(text.replace(old, new))
        print(f"  ok  {rel}")

    for rel in ("src/main.py", "CHANGELOG.md"):
        text = (W / rel).read_text()
        for bad in ("in-process two-spiral", "synthesised locally", "never asks juniper-data", "generated locally and can never be partial"):
            if bad in text:
                sys.exit(f"FAIL: {rel} still contains {bad!r}")
    print("no surviving 'local data' claim in either file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
