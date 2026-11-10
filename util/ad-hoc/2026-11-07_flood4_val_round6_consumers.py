#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-6 validation
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""For every published release of juniper-canopy and juniper-recurrence, read
the wheel in memory and report (a) whether it imports service-core's auth
(APIKeyAuth / build_api_key_auth / SecurityMiddleware / create_service_app),
(b) every sentry_sdk.init / configure_sentry call with its keywords, and
(c) any own `compare_digest` key compare.

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
import re
import sys
import urllib.request
import zipfile


def calls(text):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                name = f.value.id + "." + f.attr
            if name in ("sentry_sdk.init", "configure_sentry", "_shared_configure_sentry"):
                out.append("%s(L%d){%s}" % (name, node.lineno, ",".join("%s=%s" % (k.arg, ast.unparse(k.value)[:40]) for k in node.keywords)))
    return out


def main():
    lines = []
    for pkg in ("juniper-canopy", "juniper-recurrence"):
        meta = json.loads(urllib.request.urlopen("https://pypi.org/pypi/%s/json" % pkg, timeout=60).read())
        for ver, files in sorted(meta["releases"].items(), key=lambda kv: kv[1][0]["upload_time_iso_8601"] if kv[1] else ""):
            whl = [f for f in files if f["filename"].endswith(".whl")]
            if not whl:
                continue
            f = whl[0]
            blob = urllib.request.urlopen(f["url"], timeout=120).read()
            ok = hashlib.sha256(blob).hexdigest() == f["digests"]["sha256"]
            zf = zipfile.ZipFile(io.BytesIO(blob))
            sc_auth, sentry, own = [], [], []
            for n in zf.namelist():
                if not n.endswith(".py") or "/tests/" in n or n.startswith("tests/"):
                    continue
                t = zf.read(n).decode("utf-8", "replace")
                for i, l in enumerate(t.splitlines(), 1):
                    if re.search(r"juniper_service_core[\w.]*\s+import\s+.*(APIKeyAuth|build_api_key_auth|SecurityMiddleware|create_service_app|ws_authenticate)", l):
                        sc_auth.append("%s:%d" % (n, i))
                    if "compare_digest" in l and not l.strip().startswith("#"):
                        own.append("%s:%d %s" % (n, i, l.strip()[:90]))
                c = calls(t)
                if c:
                    sentry.append("%s %s" % (n, c))
            lines.append("%s %s upload=%s sha_ok=%s" % (pkg, ver, f["upload_time_iso_8601"][:16], ok))
            lines.append("   sc_auth_imports=%s" % sc_auth[:4])
            lines.append("   own_compare=%s" % own[:3])
            for s in sentry:
                lines.append("   SENTRY %s" % s[:300])
    with open(sys.argv[1], "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
