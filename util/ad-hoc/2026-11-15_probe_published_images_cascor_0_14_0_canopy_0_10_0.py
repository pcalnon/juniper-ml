#!/usr/bin/env python3
"""Pull the published juniper-cascor 0.14.0 and juniper-canopy 0.10.0 images by digest and report what they install.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the image half of the juniper-deploy pin PR's verification)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-deploy#266 (the precedent: cascor 0.13.0's pin, whose image was pulled by digest and run);
         notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md and notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md;
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md

Why
---
R-OBS-SC-2's fix reaches a running service only through an image that installs juniper-observability 0.4.2 and
juniper-service-core 0.7.2. cascor 0.14.0 and canopy 0.10.0 are the first releases cut from locks on both, so before
juniper-deploy pins them, this reads the images themselves, not a lock or a checkout: each is pulled by the index digest
GHCR showed on 2026-11-15, then run with no network, and its interpreter prints the installed versions.

Usage
-----
    python3 util/ad-hoc/2026-11-15_probe_published_images_cascor_0_14_0_canopy_0_10_0.py

Exit 0 when both images report the expected juniper-observability and juniper-service-core versions; 1 otherwise. It
needs docker; it pulls two images (several GB) and writes nothing else.
"""

from __future__ import annotations

import subprocess
import sys

IMAGES = {
    "juniper-cascor": ("0.14.0", "sha256:6b3e64bd76ef3db9be14c3c62f3af43ce145f3013fd723c2084a21afb006fafb"),
    "juniper-canopy": ("0.10.0", "sha256:d9a966ff7d4f34c9eb793942a9739c3bfe7ad1923717d4c2d84247ae0295ae28"),
}
EXPECT = {"juniper-observability": "0.4.2", "juniper-service-core": "0.7.2"}
REPORT = (
    "juniper-observability",
    "juniper-service-core",
    "juniper-data-client",
    "juniper-cascor-client",
    "sentry-sdk",
    "fastapi",
    "starlette",
    "pydantic",
)

_PROBE = """
import importlib.metadata as md, json, sys
names = json.loads(sys.argv[1])
have = {d.metadata["Name"].lower(): d.version for d in md.distributions()}
print(json.dumps({"python": sys.version.split()[0], "versions": {n: have.get(n.lower()) for n in names}}))
"""


def main() -> int:
    import json

    failed = False
    for name, (version, digest) in IMAGES.items():
        ref = f"ghcr.io/pcalnon/{name}:{version}@{digest}"
        subprocess.run(["docker", "pull", "-q", ref], check=True, timeout=1800)
        names = [name, *REPORT]
        out = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", ref, "-c", _PROBE, json.dumps(names)],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        ).stdout
        got = json.loads(out.strip().splitlines()[-1])
        print(f"== {ref}")
        print(f"   python {got['python']}")
        for n in names:
            print(f"   {n} {got['versions'].get(n)}")
        own_ok = got["versions"].get(name) == version
        exp_ok = all(got["versions"].get(k) == v for k, v in EXPECT.items())
        print(f"   {'PASS' if own_ok and exp_ok else 'FAIL'}: {name} {version}; " + ", ".join(f"{k} {v}" for k, v in EXPECT.items()))
        failed |= not (own_ok and exp_ok)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
