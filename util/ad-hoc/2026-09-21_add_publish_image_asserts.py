#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Add the two missing post-build assertions to a repo's `publish-image.yml`.

WHAT IS MISSING, AND WHY IT MATTERS
-----------------------------------
Only juniper-deploy's publish workflow asserts anything about the artifact beyond its torch
posture. The other five assert:

  * on a PR build  -- the app imports, plus the CPU-only census;
  * on a RELEASE   -- the CPU-only census ONLY.

The import smoke is gated `if: github.event_name != 'release' && !inputs.push`, so **the path
that actually ships asserts the least**. `check_image_cpu_only.py` is a distribution census and
torch-version check; it never imports the application. That is the exact shape of the
juniper-deploy test runner, which built, started, looked fine, and ran zero tests for six months.

This inserts, into the publish-path verify step:

  1. `check_image_no_secrets.py` -- no credential-shaped file anywhere in the shipped trees.
     Layer 3 of the build-context defence. Layers 1 and 2 (the COPY allowlist and
     `.dockerignore`) are both weaker than they look: a DIRECTORY allowlist ships a whole tree,
     and `.dockerignore` is matched root-anchored, so a nested path escapes it. An unasserted
     defence is a comment.
  2. an application import -- the artifact must do its job on the path that ships it.

and adds (1) to the build-only smoke step as well, so a PR sees the same failure.

INVOCATION FORM DIFFERS BY IMAGE and getting it wrong yields a confusing failure rather than a
clean one: images whose Dockerfile sets ENTRYPOINT (juniper-cascor-worker, juniper-recurrence)
need `--entrypoint python IMAGE -`, while CMD-only images (juniper-cascor, juniper-data,
juniper-canopy) take `IMAGE python -`. Both forms are kept below, per repo.

Usage:  python3 2026-09-21_add_publish_image_asserts.py <repo-key> <path-to-publish-image.yml> [--write]
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

# repo key -> (needs --entrypoint, import module, distribution name)
REPOS = {
    "cascor": (False, "cascade_correlation", "juniper-cascor"),
    "data": (False, "juniper_data", "juniper-data"),
    "canopy": (False, "juniper_canopy", "juniper-canopy"),
    "worker": (True, "juniper_cascor_worker", "juniper-cascor-worker"),
    "recurrence": (True, "juniper_recurrence", "juniper-recurrence"),
}


def run_form(entrypoint: bool, ref: str) -> str:
    return f'--entrypoint python "{ref}" -' if entrypoint else f'"{ref}" python -'


def exec_form(entrypoint: bool, ref: str) -> str:
    return f'--entrypoint python "{ref}"' if entrypoint else f'"{ref}" python'


def build_publish_block(entrypoint: bool, module: str) -> str:
    return f"""
          # No credential may reach a PUBLIC image. The COPY allowlist and .dockerignore are
          # both defences, but an unasserted defence is a comment -- and both are weaker than
          # they look: a DIRECTORY allowlist (`COPY src/ ./src/`) ships everything beneath it,
          # and .dockerignore is matched ROOT-ANCHORED, so `foo/` never excludes `src/foo/`.
          # This asserts the artifact itself. Negative controls (2026-09-21): a planted
          # secrets/ dir, a planted .env and a planted .pem each exit 1; a scan that finds no
          # root, or walks zero files, exits 2 rather than reporting a vacuous pass.
          echo "--- no credentials in the published image"
          docker run --rm -i {run_form(entrypoint, "${ref}")} < util/check_image_no_secrets.py

          # The application must IMPORT in the image that ships. Until now this ran only on
          # build-only runs, so the publish path asserted torch posture and never that the app
          # loads -- the shape of juniper-deploy's test runner, which built, started, and ran
          # zero tests for six months.
          echo "--- the application imports"
          docker run --rm {exec_form(entrypoint, "${ref}")} -c 'import {module}; print("    {module} imports")'
"""


def build_smoke_block(entrypoint: bool) -> str:
    return f"""
          echo "--- no credentials packaged"
          docker run --rm -i {run_form(entrypoint, "${img}")} < util/check_image_no_secrets.py
"""


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    key, path = sys.argv[1], Path(sys.argv[2])
    write = "--write" in sys.argv
    if key not in REPOS:
        print(f"ERROR: unknown repo key {key!r}; expected one of {sorted(REPOS)}")
        return 2

    entrypoint, module, _dist = REPOS[key]
    before = path.read_text(encoding="utf-8")
    if "check_image_no_secrets.py" in before:
        print(f"{path}: already wired, no change")
        return 0

    text = before

    anchor_pub = "check_image_cpu_only.py\n"

    # 1) PUBLISH path. Anchor on the STEP NAME, not on the last occurrence of the script:
    #    `rfind` lands in the MERGE job's final manifest check, which is a different step in a
    #    different job with a different `ref`. Find the per-arch verify step, then the first
    #    cpu-only invocation after it.
    step = "- name: Verify pushed image is CPU-only (publish runs)"
    spos = text.find(step)
    if spos == -1:
        print(f"ERROR: step not found: {step}")
        return 2
    idx = text.find(anchor_pub, spos)
    if idx == -1:
        print("ERROR: no cpu-only invocation inside the publish-path verify step")
        return 2
    end = idx + len(anchor_pub)
    text = text[:end] + build_publish_block(entrypoint, module) + text[end:]

    # 2) SMOKE path -- the first cpu-only invocation in the file, which precedes that step.
    first = text.find(anchor_pub)
    if first != -1 and first < idx:
        fend = first + len(anchor_pub)
        text = text[:fend] + build_smoke_block(entrypoint) + text[fend:]

    sys.stdout.writelines(
        difflib.unified_diff(
            before.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile=f"a/{path.name}", tofile=f"b/{path.name}",
        )
    )
    if write:
        path.write_text(text, encoding="utf-8")
        print(f"\nWROTE {path}")
    else:
        print("\n(dry run -- pass --write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
