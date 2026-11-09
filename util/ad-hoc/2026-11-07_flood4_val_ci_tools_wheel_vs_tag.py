#!/usr/bin/env python3
"""
Compare modules inside the PUBLISHED juniper-ci-tools wheel with the same files at a juniper-ml tag.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy DOCS carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#793 (header/version lint claims), the Sequence Safety docs screen (fence-aware in 0.9.1)

The wheel is read into memory from PyPI's JSON API URL and never written to disk. For each module named,
prints whether the wheel's bytes equal `git show <tag>:juniper-ci-tools/juniper_ci_tools/<module>`.

    python3 2026-11-07_flood4_val_ci_tools_wheel_vs_tag.py <juniper-ml worktree> <version> <module.py> [<module.py> ...]
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import urllib.request
import zipfile


def main() -> int:
    ml_root, version, modules = sys.argv[1], sys.argv[2], sys.argv[3:]
    with urllib.request.urlopen(f"https://pypi.org/pypi/juniper-ci-tools/{version}/json", timeout=60) as resp:  # nosec B310 -- fixed https URL
        meta = json.load(resp)
    wheel = next(u for u in meta["urls"] if u["filename"].endswith(".whl"))
    with urllib.request.urlopen(wheel["url"], timeout=120) as resp:  # nosec B310 -- PyPI file URL
        blob = resp.read()
    assert hashlib.sha256(blob).hexdigest() == wheel["digests"]["sha256"], "wheel sha256 does not match PyPI's digest"
    zf = zipfile.ZipFile(io.BytesIO(blob))
    out = {"wheel": wheel["filename"], "sha256": wheel["digests"]["sha256"], "modules": {}}
    for name in modules:
        in_wheel = zf.read(f"juniper_ci_tools/{name}")
        at_tag = subprocess.run(["git", "-C", ml_root, "show", f"juniper-ci-tools-v{version}:juniper-ci-tools/juniper_ci_tools/{name}"], check=True, capture_output=True).stdout
        out["modules"][name] = {"identical": in_wheel == at_tag, "wheel_sha256": hashlib.sha256(in_wheel).hexdigest()[:16], "tag_sha256": hashlib.sha256(at_tag).hexdigest()[:16]}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
