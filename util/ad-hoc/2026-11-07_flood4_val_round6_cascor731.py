#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-6 validation
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Read juniper-cascor 0.12.0 and 0.13.0 wheels in memory and report whether
src/api/lifecycle/classification_metrics.py / manager.py compute `accuracy`
in the final evaluation (juniper-cascor#731). Also print cascor 0.11.0's
api/observability.py configure_sentry definition.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 6 (findings: tmp/flood4/ml-docs/val-round6/)

Usage: python3 -I <this> <out_txt>
"""
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile


def wheel(pkg, ver):
    meta = json.loads(urllib.request.urlopen("https://pypi.org/pypi/%s/%s/json" % (pkg, ver), timeout=60).read())
    f = [u for u in meta["urls"] if u["filename"].endswith(".whl")][0]
    blob = urllib.request.urlopen(f["url"], timeout=120).read()
    assert hashlib.sha256(blob).hexdigest() == f["digests"]["sha256"]
    return zipfile.ZipFile(io.BytesIO(blob))


def main():
    out = []
    for ver in ("0.12.0", "0.13.0"):
        zf = wheel("juniper-cascor", ver)
        for name in ("src/api/lifecycle/classification_metrics.py", "src/api/lifecycle/manager.py"):
            try:
                text = zf.read(name).decode("utf-8", "replace")
            except KeyError:
                out.append("%s %s: ABSENT" % (ver, name))
                continue
            hits = [(i, l.strip()) for i, l in enumerate(text.splitlines(), 1) if re.search(r"[\"']accuracy[\"']|accuracy_score|def .*accuracy", l)]
            out.append("%s %s: %d accuracy lines" % (ver, name, len(hits)))
            for i, l in hits[:12]:
                out.append("    :%d %s" % (i, l[:180]))
    zf = wheel("juniper-cascor", "0.11.0")
    text = zf.read("src/api/observability.py").decode("utf-8", "replace")
    for i, l in enumerate(text.splitlines(), 1):
        if "configure_sentry" in l or "sentry_sdk.init" in l or "include_local_variables" in l:
            out.append("0.11.0 src/api/observability.py:%d %s" % (i, l.rstrip()[:180]))
    app = zf.read("src/api/app.py").decode("utf-8", "replace")
    for i, l in enumerate(app.splitlines(), 1):
        if "configure_sentry" in l:
            out.append("0.11.0 src/api/app.py:%d %s" % (i, l.rstrip()[:180]))
    with open(sys.argv[1], "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
