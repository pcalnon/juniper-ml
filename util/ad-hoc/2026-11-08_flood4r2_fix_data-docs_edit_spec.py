#!/usr/bin/env python3
"""
Write the edit spec that applies the round-2 claims validator's findings to the juniper-data data-docs carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: validator findings -> data-docs carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/data-claims-lens/findings.json F2, F3, F6, F7, F8, F9 (F5: stamps left to the orchestrator)

Usage:
  2026-11-08_flood4r2_fix_data-docs_edit_spec.py <data-docs worktree> <out edits.json>

The document edits are the validator's exact old -> new texts. The CHANGELOG entry's "Corrected on the way in" list
is updated for F2 and F3 (F2 corrects #521's own sentence; F3 replaces the bullet that described the build's "Four
checks ... can fail the run, in this order"), re-flowed at the entry's own width (118, six-space continuation).
The apply step is 2026-11-08_flood4r2_fix_apply_edits.py.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path


def _bullet(text: str) -> str:
    return "\n".join(textwrap.wrap(text, width=118, initial_indent="    - ", subsequent_indent="      ", break_long_words=False, break_on_hyphens=False)) + "\n"


def main(argv: list[str]) -> int:
    worktree, out = argv[1], Path(argv[2])
    edits = [
        {
            "id": "claims-F2",
            "file": "docs/REFERENCE.md",
            "old": "Release tags from `docker/metadata-action` are `X.Y.Z`, `X.Y`, and `latest` (latest only when the event is a release). A manual run with `push` true adds `dispatch-<sha>` instead, because the semver rules match nothing on that event.",
            "new": "Release tags from `docker/metadata-action` are `X.Y.Z`, `X.Y`, and `latest`. A manual run with `push` true adds `dispatch-<sha>`. Run from a branch, that is its only tag: the semver rules read the ref, not the event, and a branch is not a tag. Run from a `vX.Y.Z` tag, the semver rules match and metadata-action's default `latest=auto` flavor adds `latest`, so that run re-points `X.Y.Z`, `X.Y` and `latest`.",
        },
        {
            "id": "claims-F3",
            "file": "docs/REFERENCE.md",
            "old": "Four checks in that job can fail the run, in this order.",
            "new": "Five checks in that job can fail the run. The four below, in this order, guard the tags and the list; the fifth is the CPU-only `docker run` of the first tag (`util/check_image_cpu_only.py`, `EXPECT_TORCH=absent`) that ends `Verify published image is CPU-only`.",
        },
        {
            "id": "claims-F8",
            "file": "docs/REFERENCE.md",
            "old": "and the old count stays in the table until that next failure replaces it.",
            "new": "and the old count stays in the table until that next failure replaces it or cleanup removes the row (below).",
        },
        {
            "id": "claims-F7",
            "file": "docs/DEVELOPER_CHEATSHEET.md",
            "old": "After that window, the next 401 starts the count at 1. See [Failed-Auth Throttle Retention](REFERENCE.md#failed-auth-throttle-retention).",
            "new": "After that window, the next 401 starts the count at 1. See [Rate-Limit Window](REFERENCE.md#rate-limit-window) and [Failed-Auth Throttle Retention](REFERENCE.md#failed-auth-throttle-retention).",
        },
        {
            "id": "claims-F9",
            "file": "docs/ci_cd/CICD_MANUAL.md",
            "old": "requires the published list to contain linux `amd64` and `arm64`",
            "new": "requires the published list's linux entries to be exactly `amd64` and `arm64`",
        },
        {
            "id": "claims-F6",
            "file": "CHANGELOG.md",
            "old": "    `CICD_QUICK_START.md`, `CICD_REFERENCE.md` and `DEVELOPER_CHEATSHEET.md`.\n",
            "new": "    `CICD_REFERENCE.md` and `DEVELOPER_CHEATSHEET.md` (`CICD_QUICK_START.md` links the manifest gates only).\n",
        },
    ]
    old_four = (
        "    - \"Four checks ... fail the run for a reason the job used to be able to miss\" now reads \"can fail the run, in\n"
        "      this order\": the workflow's history does not show all four as fixes.\n"
    )
    new_four = _bullet(
        "\"Four checks ... fail the run for a reason the job used to be able to miss\" now reads \"Five checks ... can fail "
        "the run\": the workflow's history does not show the four listed as fixes, and the CPU-only `docker run` that "
        "ends `Verify published image is CPU-only` is a fifth."
    ) + _bullet(
        "It said `latest` is added only on a release, and that a manual run adds only `dispatch-<sha>` because the semver "
        "rules match nothing on that event. metadata-action's semver rules read the ref, not the event, and its default "
        "`latest=auto` flavor adds `latest` to a non-prerelease match, so a manual run from a `vX.Y.Z` tag re-points "
        "`X.Y.Z`, `X.Y` and `latest`."
    )
    edits.append({"id": "claims-F2F3-changelog", "file": "CHANGELOG.md", "old": old_four, "new": new_four})
    out.write_text(json.dumps({"worktree": worktree, "edits": edits}, indent=1) + "\n", encoding="utf-8")
    print(new_four, end="")
    print(f"line lengths: {[len(line) for line in new_four.splitlines()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
