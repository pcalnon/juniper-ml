"""
Read a public GHCR image's manifest list anonymously and print its entries' platforms, media types and annotations.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (claims and docs lens): juniper-data data-docs § Publish manifest gates
         (per-arch OCI index with a provenance attestation, flattened by `imagetools create`).

Anonymous pull token only; the token is never printed. Usage:
  python3 util/ad-hoc/2026-11-08_flood4r2_val_data-claims_ghcr_index.py pcalnon/juniper-data 0.17.1
"""

from __future__ import annotations

import json
import sys
import urllib.request

ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


def main() -> int:
    repo, ref = sys.argv[1], sys.argv[2]
    with urllib.request.urlopen(f"https://ghcr.io/token?scope=repository:{repo}:pull", timeout=30) as resp:  # noqa: S310 - fixed https host
        token = json.load(resp)["token"]
    req = urllib.request.Request(f"https://ghcr.io/v2/{repo}/manifests/{ref}", headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed https host
        body = json.load(resp)
        digest = resp.headers.get("Docker-Content-Digest")
    print(f"{repo}:{ref} digest={digest} mediaType={body.get('mediaType')}")
    for entry in body.get("manifests", []):
        plat = entry.get("platform", {})
        ann = entry.get("annotations", {})
        print(f"  {plat.get('os')}/{plat.get('architecture')}  {entry.get('mediaType')}  {entry.get('digest')[:19]}  {json.dumps(ann)[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
