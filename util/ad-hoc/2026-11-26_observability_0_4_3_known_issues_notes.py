#!/usr/bin/env python3
"""Write the juniper-observability 0.4.3 release notes with their Known Issues filled in.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — one-off (the juniper-observability 0.4.3 cut)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/release_train/notes_render.py (its standard template hard-codes "None known at time of release.");
    util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py (the measurements the list states);
    util/ad-hoc/2026-10-10_fill_security_notes_placeholders.py (the same after-the-cut, two-place edit, for the
    security template's placeholders).

Why this exists
---------------
The Overtoad ruled on 2026-11-26 that the 0.4.3 Release lists the pre-existing Sentry exposures that 0.4.3 leaves
as 0.4.2 had them, in place of the renderer's fixed "None known at time of release." The renderer has no input
for that section, so the ceremony's own body is rewritten after the cut, in the two places that hold it: the
Release (``gh release edit --notes-file``) and the archive branch's ``notes/releases/`` file.

The input must be the body the ceremony rendered, byte for byte: this replaces exactly one block, asserts the
rest is unchanged, and refuses a body that has already been filled.

Usage: python3 util/ad-hoc/2026-11-26_observability_0_4_3_known_issues_notes.py RENDERED.md FILLED.md
Exit status: 0 written; 2 refused (the input is not the rendered 0.4.3 body, or is already filled).
"""

import sys
from pathlib import Path

HEADER = "# juniper-observability v0.4.3 Release Notes\n"

OLD = "## Known Issues\n\nNone known at time of release.\n"

NEW = (
    "## Known Issues\n"
    "\n"
    "These predate 0.4.3, which leaves them as 0.4.2 had them. The next release, 0.4.4 (R-OBS-SC-3), is to decide"
    " them. juniper-deploy's defaults configure no Sentry DSN, so none of them sends anything until an operator"
    " sets one. Each was measured on the wire on sentry-sdk 2.35.0, 2.76.0 and 3.0.0, under either `send_pii` value,"
    " by juniper-ml's `util/ad-hoc/2026-11-26_observability_known_issues_wire_probe.py`.\n"
    "\n"
    "- **The client's address, through five proxy headers, even without `send_pii`.** `Forwarded`, `X-Client-IP`,"
    " `CF-Connecting-IP`, `True-Client-IP` and `X-Cluster-Client-IP` reach the error events and sampled transactions"
    " (on 3.x, spans) of a request that carries them, raw. Of the headers that carry a client address, only"
    " `X-Forwarded-For` and `X-Real-IP` are filtered.\n"
    "- **On 2.x, a request-body field whose name the denylist lacks.** juniper-canopy's `POST /api/remote/connect`"
    " carries its worker `authkey` in the JSON body. Its pydantic `SecretStr` hides it from logs and reprs, not from"
    " the raw body the SDK reads, so it reaches `request.data` in error events and in every sampled transaction."
    " 3.x sends no request bodies.\n"
    "- **Sentry Logs carry a log record's `extra` fields raw**, on either major, even under a name the denylist"
    " names (`api_key`): `configure_sentry` installs no `before_send_log` hook.\n"
)


def main(argv) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    rendered = Path(argv[1]).read_text(encoding="utf-8")
    if not rendered.startswith(HEADER):
        print(f"REFUSED: {argv[1]} does not start with {HEADER.strip()!r}", file=sys.stderr)
        return 2
    if rendered.count(NEW) or rendered.count(OLD) != 1:
        print(f"REFUSED: {argv[1]} holds the default Known Issues block x{rendered.count(OLD)} and the filled one x{rendered.count(NEW)} (expected 1 and 0)", file=sys.stderr)
        return 2
    filled = rendered.replace(OLD, NEW, 1)
    # Nothing but that block may change: the text before and after it must survive byte for byte.
    head, tail = rendered.split(OLD)
    assert filled == head + NEW + tail and filled.startswith(head) and filled.endswith(tail)
    assert filled.endswith("\n") and not filled.endswith("\n\n"), "one trailing newline, or end-of-file-fixer rewrites it"
    Path(argv[2]).write_text(filled, encoding="utf-8")
    print(f"wrote {argv[2]}: {len(rendered.splitlines())} -> {len(filled.splitlines())} lines; only the Known Issues block changed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
