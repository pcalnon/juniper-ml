#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 docs carrier, round-6 validation
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Round-6 validator probe: read every published wheel (or sdist) of
juniper-service-core, juniper-observability, juniper-cascor and juniper-data
IN MEMORY (nothing extracted, nothing imported), and dump the source of the
API-key compare, the Sentry init / before_send hook, FailedAuthThrottle,
cascor's final-eval accuracy and juniper-data's body-limit constant.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 6 (findings: tmp/flood4/ml-docs/val-round6/)

Usage: python3 -I <this> <out_dir>
Writes <out_dir>/round6_wheels.json and <out_dir>/round6_snippets.txt.
"""
import ast
import hashlib
import io
import json
import re
import sys
import tarfile
import urllib.request
import zipfile

PKGS = ["juniper-service-core", "juniper-observability", "juniper-cascor", "juniper-data"]


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def members(blob, fname):
    """Yield (path, text) for every .py member."""
    if fname.endswith(".whl") or fname.endswith(".zip"):
        zf = zipfile.ZipFile(io.BytesIO(blob))
        for n in zf.namelist():
            if n.endswith(".py"):
                yield n, zf.read(n).decode("utf-8", "replace")
    else:
        tf = tarfile.open(fileobj=io.BytesIO(blob), mode="r:*")
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith(".py"):
                f = tf.extractfile(m)
                yield m.name, f.read().decode("utf-8", "replace")


def func_src(text, names):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return ["<syntax error %s>" % e]
    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names:
            out.append("L%d-%d %s:\n%s" % (node.lineno, node.end_lineno, node.name, "\n".join(lines[node.lineno - 1:node.end_lineno])))
    return out


def sentry_init_calls(text):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = ""
            if isinstance(f, ast.Attribute):
                name = f.attr
                if isinstance(f.value, ast.Name):
                    name = f.value.id + "." + f.attr
            elif isinstance(f, ast.Name):
                name = f.id
            if name in ("sentry_sdk.init", "configure_sentry", "init") and ("sentry" in text):
                kws = {k.arg: ast.unparse(k.value) for k in node.keywords}
                out.append({"line": node.lineno, "call": name, "kw": kws})
    return out


def main():
    out_dir = sys.argv[1]
    report = {}
    snippets = []
    for pkg in PKGS:
        meta = json.loads(fetch("https://pypi.org/pypi/%s/json" % pkg))
        rels = meta["releases"]
        report[pkg] = {}
        for ver in sorted(rels, key=lambda v: [(int(x), "") if x.isdigit() else (-1, x) for x in re.split(r"[.]", v)]):
            files = rels[ver]
            if not files:
                report[pkg][ver] = {"files": 0}
                continue
            whl = [f for f in files if f["filename"].endswith(".whl")]
            pick = whl[0] if whl else files[0]
            blob = fetch(pick["url"])
            sha = hashlib.sha256(blob).hexdigest()
            entry = {"file": pick["filename"], "upload": pick["upload_time_iso_8601"], "yanked": pick.get("yanked"), "sha256_ok": sha == pick["digests"]["sha256"], "hits": []}
            snippets.append("\n" + "=" * 100 + "\n%s %s %s upload=%s sha_ok=%s" % (pkg, ver, pick["filename"], pick["upload_time_iso_8601"], entry["sha256_ok"]))
            for path, text in members(blob, pick["filename"]):
                hit = []
                if "compare_digest" in text:
                    hit.append("compare_digest")
                    for ln, line in enumerate(text.splitlines(), 1):
                        if "compare_digest" in line or "surrogate" in line or re.search(r"\bfor \w+ in self\._api_keys", line) or "encode(" in line and "key" in line:
                            snippets.append("  %s:%d: %s" % (path, ln, line.strip()))
                    for s in func_src(text, {"validate", "_matches", "_compare", "verify_api_key", "check_api_key"}):
                        snippets.append("  --- %s %s" % (path, s))
                if re.search(r"^\s*from juniper_service_core[\w.]* import .*\b(APIKeyAuth|SecurityMiddleware|FailedAuthThrottle)", text, re.M):
                    hit.append("imports_sc_auth")
                    for ln, line in enumerate(text.splitlines(), 1):
                        if "juniper_service_core" in line and "import" in line:
                            snippets.append("  IMPORT %s:%d: %s" % (path, ln, line.strip()))
                if "class APIKeyAuth" in text:
                    hit.append("defines_APIKeyAuth")
                if "class FailedAuthThrottle" in text:
                    hit.append("FailedAuthThrottle")
                    for s in func_src(text, {"FailedAuthThrottle"}):
                        snippets.append("  --- %s %s" % (path, s[:6000]))
                if "sentry" in text.lower():
                    calls = sentry_init_calls(text)
                    if calls:
                        hit.append("sentry_init")
                        snippets.append("  SENTRY %s: %s" % (path, json.dumps(calls)))
                    if pkg == "juniper-observability" and path.endswith("sentry.py"):
                        for ln, line in enumerate(text.splitlines(), 1):
                            if "include_local_variables" in line or "vars" in line or "def " in line or "before_send" in line:
                                snippets.append("  OBS %s:%d: %s" % (path, ln, line.rstrip()))
                    if pkg in ("juniper-cascor", "juniper-data"):
                        for ln, line in enumerate(text.splitlines(), 1):
                            if "_strip_sensitive_headers" in line or "include_local_variables" in line or ("before_send" in line and "=" in line):
                                snippets.append("  SVC-SENTRY %s:%d: %s" % (path, ln, line.strip()))
                if pkg == "juniper-cascor" and ("final" in text and "accuracy" in text and "eval" in path.lower()):
                    for ln, line in enumerate(text.splitlines(), 1):
                        if re.search(r"[\"']accuracy[\"']", line):
                            snippets.append("  ACC %s:%d: %s" % (path, ln, line.strip()))
                if pkg == "juniper-data" and path.endswith("constants.py"):
                    for ln, line in enumerate(text.splitlines(), 1):
                        if "BODY" in line or "1024 * 1024" in line:
                            snippets.append("  CONST %s:%d: %s" % (path, ln, line.strip()))
                if hit:
                    entry["hits"].append({"path": path, "hit": hit})
            report[pkg][ver] = entry
    with open(out_dir + "/round6_wheels.json", "w") as fh:
        json.dump(report, fh, indent=1)
    with open(out_dir + "/round6_snippets.txt", "w") as fh:
        fh.write("\n".join(snippets))
    print("done", {p: len(report[p]) for p in report})


if __name__ == "__main__":
    main()
