#!/usr/bin/env python3
"""Lane A: is the published juniper-doc-tools 0.1.2 wheel's checker identical to the in-repo copy at the head?

docs-full-check.yml installs `juniper-doc-tools>=0.1.0,<0.2.0` from PyPI, so the CI behaviour is the wheel's,
not the checkout's. Downloads the wheel into memory (no install) and compares the three modules byte for byte.
"""
import hashlib
import io
import json
import pathlib
import urllib.request
import zipfile

S = pathlib.Path(__file__).resolve().parent
REPO_PKG = S / "eco/juniper-ml/juniper-doc-tools/juniper_doc_tools"
meta = json.load(urllib.request.urlopen("https://pypi.org/pypi/juniper-doc-tools/0.1.2/json"))
wheel = [u for u in meta["urls"] if u["filename"].endswith(".whl")][0]
print("wheel:", wheel["filename"], "uploaded", wheel["upload_time_iso_8601"])
blob = urllib.request.urlopen(wheel["url"]).read()
assert hashlib.sha256(blob).hexdigest() == wheel["digests"]["sha256"], "digest mismatch"
zf = zipfile.ZipFile(io.BytesIO(blob))
for mod in ("check_doc_links.py", "_ecosystem.py", "cli.py"):
    w = zf.read(f"juniper_doc_tools/{mod}")
    r = (REPO_PKG / mod).read_bytes()
    print(f"{mod}: wheel==repo {w == r} (wheel {len(w)} B, repo {len(r)} B)")
