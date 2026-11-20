#!/usr/bin/env python3
"""
Move the parent ``Juniper/AGENTS.md`` RELEASED paragraph to juniper-ml 0.11.5, and name observability 0.4.2 and service-core 0.7.2.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (one edit of the unversioned parent AGENTS.md, approved by the Overtoad on 2026-11-14)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py (the re-probe that licenses the date move;
         run 2026-11-14 23:53Z, exit 0, with --expect for juniper-ml 0.11.5, observability 0.4.2, service-core 0.7.2,
         cascor 0.13.0 and canopy 0.9.0); notes/releases/RELEASE_NOTES_v0.11.5.md; publish run 43408809021

Why this exists
---------------
The parent ``Juniper/AGENTS.md`` is not in any repository, so an edit to it has no PR, no CI and no history. This
script is that history: it makes exactly four replacements, each of which must match once (or already be at its
target), and it refuses to write anything otherwise. The Overtoad approved the edit on 2026-11-14 (R-OBS-SC-2
follow-ups, "Parent docs": "Edit it (Recommended)").

1. "re-probed against PyPI on 2026-11-07 UTC" becomes 2026-11-14: every package the paragraph names was re-read;
2. a bullet for juniper-observability 0.4.2 and juniper-service-core 0.7.2 (PyPI 2026-11-09), which the paragraph
   did not name, goes in above the meta-package's;
3. the meta-package bullet names 0.11.5 as the latest, and 0.11.4 joins its predecessors;
4. its ``[tools]`` sub-bullet names 0.11.5's floors;
5. ``**Last Updated**`` becomes 2026-11-14.

    python3 util/ad-hoc/2026-11-14_parent_agents_released_paragraph_0_11_5.py [--path FILE] [--check]

Exit status: 0 when written (or, with --check, when every edit is already at target), 1 when an anchor is missing
or ambiguous (nothing is written) or --check finds an edit still to make.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def default_parent_agents() -> Path:
    """The ecosystem root's AGENTS.md: the nearest ancestor of this script holding both ``juniper-ml/`` and ``AGENTS.md``.

    It is found, not written down, so the script holds no home-directory literal (pre-commit's G5) and works from the
    primary checkout and from a ``.claude/worktrees/`` checkout alike.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "juniper-ml").is_dir() and (parent / "AGENTS.md").is_file():
            return parent / "AGENTS.md"
    raise SystemExit("no ancestor holds both juniper-ml/ and AGENTS.md; pass --path")


EDITS = [
    (
        "**Last Updated**: 2026-11-10\n",
        "**Last Updated**: 2026-11-14\n",
    ),
    (
        "    **What has moved since (re-probed against PyPI on 2026-11-07 UTC):**\n",
        "    **What has moved since (re-probed against PyPI on 2026-11-14 UTC):**\n",
    ),
    (
        """    - **The meta-package: juniper-ml 0.11.4** (2026-11-07 22:59Z, publish run
      42230617125; Release `v0.11.4`, tag at juniper-ml `957f0e94`) is the latest on PyPI.
      It is a patch with no security content: `[recurrence]` floors
      `juniper-recurrence>=0.8.1` (juniper-ml#2473), so `pip install -U juniper-ml[recurrence]`
      moves an environment off recurrence 0.8.0, and with it off model-core 0.2.0. It
      followed 0.11.3 (2026-10-26 17:48Z, publish run 40306687867; tag at `a771a5b8`),
      which carries juniper-ml#2062's fix (the last bullet below), 0.11.2 (2026-10-26
      08:38Z, publish run 40247789317), 0.11.1 (2026-10-25 18:03Z), 0.11.0 (2026-10-21)
      and 0.10.0 (2026-09-23, publish run 35879664979).
      - `[tools]` floors the security patches: `juniper-observability>=0.4.1` and
        `juniper-service-core>=0.7.1,<0.8.0` (juniper-ml#2314, since 0.11.1). 0.11.0's did not.
""",
        """    - **juniper-observability 0.4.2** (PyPI 2026-11-09 09:51Z) and **juniper-service-core
      0.7.2** (09:52Z), R-OBS-SC-2's two patches. observability 0.4.2's `configure_sentry`
      scrubs transactions as well as error events, redacts the parsed cookies and filters
      four more credential headers; service-core 0.7.2 rounds `FailedAuthThrottle`'s
      `Retry-After` up instead of truncating it. Of the published consumers, only juniper-ml
      0.11.5's `[tools]` floors them (next bullet). juniper-data 0.17.1 (under `[api]`),
      juniper-cascor 0.13.0, juniper-canopy 0.9.0 and juniper-recurrence 0.8.1 (its
      observability floor under `[observability]`) floor 0.4.1 and 0.7.1. juniper-cascor's
      and juniper-canopy's next releases raise theirs (Overtoad rulings of 2026-11-09 and
      2026-11-13).
    - **The meta-package: juniper-ml 0.11.5** (2026-11-14 00:16Z, publish run
      43408809021; Release `v0.11.5`, tag at juniper-ml `48b66130`) is the latest on PyPI.
      It is a security patch: `[tools]` floors `juniper-observability>=0.4.2` and
      `juniper-service-core>=0.7.2,<0.8.0` (juniper-ml#2555), so
      `pip install -U juniper-ml[tools]` moves an environment off 0.4.1 and 0.7.1. It
      followed 0.11.4 (2026-11-07 22:59Z, publish run 42230617125; tag at `957f0e94`), a
      patch with no security content: its `[recurrence]` floors `juniper-recurrence>=0.8.1`
      (juniper-ml#2473), so `pip install -U juniper-ml[recurrence]` moves an environment off
      recurrence 0.8.0, and with it off model-core 0.2.0. Before that came 0.11.3
      (2026-10-26 17:48Z, publish run 40306687867; tag at `a771a5b8`), which carries
      juniper-ml#2062's fix (the last bullet below), 0.11.2 (2026-10-26 08:38Z, publish run
      40247789317), 0.11.1 (2026-10-25 18:03Z), 0.11.0 (2026-10-21) and 0.10.0
      (2026-09-23, publish run 35879664979).
      - `[tools]` floors the security patches: `juniper-observability>=0.4.2` and
        `juniper-service-core>=0.7.2,<0.8.0` since 0.11.5 (juniper-ml#2555). 0.11.1 to
        0.11.4 floor `>=0.4.1` and `>=0.7.1,<0.8.0` (juniper-ml#2314); 0.11.0's did not.
""",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--path", type=Path, default=None, help="the parent AGENTS.md (default: found from this script, see default_parent_agents)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.path is None:
        args.path = default_parent_agents()
    text = args.path.read_text(encoding="utf-8")
    pending = 0
    for old, new in EDITS:
        n_old, n_new = text.count(old), text.count(new)
        label = old.strip().splitlines()[0][:72]
        if n_old == 1 and n_new == 0:
            text = text.replace(old, new, 1)
            pending += 1
            print(f"applied: {label}")
        elif n_old == 0 and n_new == 1:
            print(f"already at target: {label}")
        else:
            print(f"REFUSED: {label!r}: old x{n_old}, new x{n_new}; nothing written", file=sys.stderr)
            return 1
    if args.check:
        print(f"--check: {pending} edit(s) still to make" if pending else "--check: every edit is at target")
        return 1 if pending else 0
    if pending:
        args.path.write_text(text, encoding="utf-8")
    print(f"{pending} edit(s) written to {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
