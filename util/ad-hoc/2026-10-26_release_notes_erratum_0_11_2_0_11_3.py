#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_release_notes_erratum_0_11_2_0_11_3.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Applies the owner-approved (2026-10-26) erratum to the juniper-ml 0.11.2
#   security notes and the clarification to the 0.11.3 notes, in every copy:
#     - notes/releases/RELEASE_NOTES_v0.11.2.md and the Release v0.11.2 body:
#       the Priority line corrected in place, plus a dated erratum block;
#     - notes/releases/RELEASE_NOTES_v0.11.3.md and the Release v0.11.3 body:
#       one clarifying sentence after "applies for the first time";
#     - CHANGELOG.md: a correction sub-bullet under [0.11.2]'s `[servers]`
#       security entry, and the same clarifying sentence under [0.11.3].
#   The facts are measured on PyPI's published metadata by
#   util/ad-hoc/2026-10-26_erratum_0_11_x_security_floor_probe.py.
#
#   Every edit asserts its exact old text and requires exactly one match, so a
#   file that has drifted is refused rather than half-edited. Each target is
#   optional, because the archives (an archive-only PR, Allow-Archive-Edit),
#   the CHANGELOG (its own PR) and the Release bodies (gh release edit) land
#   separately.
#
# Usage:
#   python3 -I util/ad-hoc/2026-10-26_release_notes_erratum_0_11_2_0_11_3.py \
#       [--notes-0112 PATH] [--notes-0113 PATH] [--changelog PATH] [--check]
#   A Release body fetched with
#   `gh release view v0.11.2 --json body --jq .body > FILE` is passed as
#   --notes-0112 FILE, and pushed back with `gh release edit v0.11.2 --notes-file FILE`.
#
# Exit codes: 0 applied (or, with --check, nothing owed); 1 an edit is owed
#   (--check) or a target drifted; 2 usage error.
# -----------------------------------------------------------------------------
"""Apply the 2026-10-26 erratum to the juniper-ml 0.11.2 / 0.11.3 release notes and CHANGELOG."""

import argparse
import sys
from pathlib import Path

MAX_LINE = 512  # .markdownlint.yaml line_length

OLD_PRIORITY = "**Priority:** High: upgrade every environment installed through `juniper-ml[servers]` without `[tools]`; `[tools]` and `[all]` already floor both patches, since 0.11.1\n"
NEW_PRIORITY = "**Priority:** High: upgrade every environment installed through `juniper-ml[servers]` or `juniper-ml[all]`, with or without `[tools]` (corrected 2026-10-26; see the erratum below)\n"

ERRATUM_0112 = """> **Erratum (2026-10-26).** As first published, these notes placed this release's security content in the two shared patches, and told `[tools]` and `[all]` users they were already covered. Both statements were wrong.
>
> - **The shared patches were not new to `[servers]`.** juniper-canopy 0.9.0 floors `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1` unconditionally, and `[servers]`, and so `[all]`, has required `juniper-canopy>=0.9.0` since 0.11.0.
> - **The security content is juniper-cascor 0.12.0's own fixes**, which no earlier `[servers]` or `[all]` floored: a non-ASCII `X-API-Key` is a 401, not a 500 whose Sentry event could carry the real key (juniper-cascor#689); `FailedAuthThrottle.check()` stays bounded (juniper-cascor#710); `APIKeyAuth` checks every configured key (juniper-cascor#659); and the CLI's own Sentry init stops sending frame-local variables.
> - **So the Priority line under-warned.** Any `[servers]` or `[all]` environment installed before 0.11.2, with or without `[tools]`, can still hold juniper-cascor 0.11.0 or older: upgrade it. `[tools]` alone installs no server and is unaffected.
>
> The Medium rating and the CWE-201, CWE-755 and CWE-770 classes stand, now for cascor's own fixes. Apart from the Priority line, the text below is as published on 2026-10-25. The Priority line read: "High: upgrade every environment installed through `juniper-ml[servers]` without `[tools]`; `[tools]` and `[all]` already floor both patches, since 0.11.1".
"""
ERRATUM_MARKER = "> **Erratum (2026-10-26).**"
# The erratum goes right after the header block's closing rule.
HEADER_END = "**Package Affected:** juniper-ml\n"
RULE = "\n---\n"

OLD_0113 = """data's `[api]` also
    carries its `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1` floors, which `[servers]` now applies
    for the first time.
"""
NEW_0113 = """data's `[api]` also
    carries its `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1` floors, which `[servers]` now applies
    for the first time. *(Clarified 2026-10-26: these are data's own floors. The same versions already reached
    `[servers]` through juniper-canopy 0.9.0 since 0.11.0, and through juniper-cascor 0.12.0 since 0.11.2, so no
    environment gains a patch from them.)*
"""

OLD_0112_CHANGELOG = """    extra, and `[servers]` installs bare `juniper-data`, so in a `[servers]` environment the patches arrive through
    cascor 0.12.0. The data floor keeps `[servers]` level with the image juniper-deploy#258 pins.
"""
NEW_0112_CHANGELOG = OLD_0112_CHANGELOG + """  - **Correction (2026-10-26).** The two shared patches were not new to `[servers]`: juniper-canopy 0.9.0 floors
    both unconditionally, and `[servers]` has required it since 0.11.0. This release's security content is
    juniper-cascor 0.12.0's own fixes above, which no earlier `[servers]` or `[all]` floored, so any `[servers]` or
    `[all]` environment installed before 0.11.2, with or without `[tools]`, can still hold juniper-cascor 0.11.0 or
    older. The release notes told `[tools]` and `[all]` users they were covered; the Release v0.11.2 body and
    `notes/releases/RELEASE_NOTES_v0.11.2.md` now carry an erratum. Measured on PyPI's published metadata by
    `util/ad-hoc/2026-10-26_erratum_0_11_x_security_floor_probe.py`.
"""


class Drift(Exception):
    """A target's text is not what the edit was written against."""


def replace_once(text: str, old: str, new: str, what: str) -> tuple[str, bool]:
    """Replace `old` with `new` exactly once. Returns (text, changed); already-applied is not an error."""
    if new != old and new in text:
        return text, False
    n = text.count(old)
    if n != 1:
        raise Drift(f"{what}: expected exactly one match of the old text, found {n}")
    return text.replace(old, new), True


def edit_0112(text: str) -> tuple[str, list[str]]:
    done = []
    text, changed = replace_once(text, OLD_PRIORITY, NEW_PRIORITY, "0.11.2 Priority line")
    if changed:
        done.append("Priority line")
    if ERRATUM_MARKER not in text:
        if text.count(HEADER_END) != 1:
            raise Drift("0.11.2 header: expected one Package Affected line")
        at = text.index(RULE, text.index(HEADER_END)) + len(RULE)
        text = text[:at] + "\n" + ERRATUM_0112 + text[at:]
        done.append("erratum block")
    return text, done


def edit_0113(text: str) -> tuple[str, list[str]]:
    text, changed = replace_once(text, OLD_0113, NEW_0113, "0.11.3 clause")
    return text, (["0.11.3 clarification"] if changed else [])


def edit_changelog(text: str) -> tuple[str, list[str]]:
    done = []
    head_0112 = text.index("## [0.11.2]")
    head_0111 = text.index("## [0.11.1]")
    section = text[head_0112:head_0111]
    section, changed = replace_once(section, OLD_0112_CHANGELOG, NEW_0112_CHANGELOG, "CHANGELOG [0.11.2] correction")
    if changed:
        done.append("[0.11.2] correction")
    text = text[:head_0112] + section + text[head_0111:]
    head_0113 = text.index("## [0.11.3]")
    head_0112 = text.index("## [0.11.2]")
    section = text[head_0113:head_0112]
    section, changed = replace_once(section, OLD_0113, NEW_0113, "CHANGELOG [0.11.3] clarification")
    if changed:
        done.append("[0.11.3] clarification")
    return text[:head_0113] + section + text[head_0112:], done


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--notes-0112", type=Path, help="RELEASE_NOTES_v0.11.2.md or a fetched Release v0.11.2 body")
    ap.add_argument("--notes-0113", type=Path, help="RELEASE_NOTES_v0.11.3.md or a fetched Release v0.11.3 body")
    ap.add_argument("--changelog", type=Path, help="CHANGELOG.md")
    ap.add_argument("--check", action="store_true", help="report what is owed; write nothing")
    args = ap.parse_args()
    targets = [(args.notes_0112, edit_0112), (args.notes_0113, edit_0113), (args.changelog, edit_changelog)]
    if not any(path for path, _ in targets):
        ap.error("name at least one target")
    owed = 0
    for path, fn in targets:
        if path is None:
            continue
        before = path.read_text(encoding="utf-8")
        try:
            after, done = fn(before)
        except Drift as exc:
            print(f"DRIFT {path}: {exc}")
            return 1
        long_lines = [i + 1 for i, line in enumerate(after.splitlines()) if len(line) > MAX_LINE and line not in before.splitlines()]
        if long_lines:
            print(f"DRIFT {path}: new lines over {MAX_LINE} characters at {long_lines}")
            return 1
        if not done:
            print(f"OK    {path}: nothing owed")
            continue
        owed += 1
        if args.check:
            print(f"OWED  {path}: {', '.join(done)}")
        else:
            path.write_text(after, encoding="utf-8")
            print(f"EDIT  {path}: {', '.join(done)}")
    return 1 if (args.check and owed) else 0


if __name__ == "__main__":
    sys.exit(main())
