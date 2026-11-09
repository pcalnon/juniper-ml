#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-6 validation
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Print juniper-canopy's own APIKeyAuth.validate (security.py) and where the
app wires it, for canopy 0.8.0, 0.8.1 and 0.9.0, read from the PyPI wheels in
memory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 6 (findings: tmp/flood4/ml-docs/val-round6/)

Usage: python3 -I <this> <out_txt>
"""
import ast
import hashlib
import io
import json
import sys
import urllib.request
import zipfile


def main():
    out = []
    for ver in ("0.8.0", "0.8.1", "0.9.0"):
        meta = json.loads(urllib.request.urlopen("https://pypi.org/pypi/juniper-canopy/%s/json" % ver, timeout=60).read())
        f = [u for u in meta["urls"] if u["filename"].endswith(".whl")][0]
        blob = urllib.request.urlopen(f["url"], timeout=120).read()
        assert hashlib.sha256(blob).hexdigest() == f["digests"]["sha256"]
        zf = zipfile.ZipFile(io.BytesIO(blob))
        out.append("=== canopy %s %s upload=%s" % (ver, f["filename"], f["upload_time_iso_8601"]))
        names = [n for n in zf.namelist() if n.endswith(".py") and "test" not in n]
        for n in names:
            t = zf.read(n).decode("utf-8", "replace")
            if "class APIKeyAuth" in t:
                tree = ast.parse(t)
                lines = t.splitlines()
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == "validate":
                        body = [l for l in lines[node.lineno - 1:node.end_lineno] if l.strip() and not l.strip().startswith("#")]
                        out.append("  %s L%d validate (comments dropped):" % (n, node.lineno))
                        out.extend("    " + l for l in body)
            for i, l in enumerate(t.splitlines(), 1):
                if "APIKeyAuth(" in l or ("import" in l and "APIKeyAuth" in l):
                    out.append("  USE %s:%d %s" % (n, i, l.strip()[:150]))
    with open(sys.argv[1], "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
