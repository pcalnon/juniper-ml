#!/usr/bin/env python3
"""
Read every published wheel of the five packages whose API-key / Sentry fix the flood-4 docs carrier dates, and print what each release's code does.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_fixes_round5.py (the corrections these facts support)

Each wheel is fetched from PyPI's JSON API and read in memory (zipfile over the downloaded bytes). Nothing is
extracted, imported or executed: modules are only parsed with `ast`. Per release with a wheel it prints:

- every module defining `class APIKeyAuth` (service-core, data, cascor, canopy): each `hmac.compare_digest(...)` call,
  and whether the module calls `.encode(..., "surrogatepass")` -- the byte compare;
- for observability's `sentry.py`: the `include_local_variables=` keywords passed, and whether it calls
  `.pop("vars", ...)` -- the frame-locals fix;
- every `sentry_sdk.init(...)` call outside juniper_observability, with its keyword names;
- for service-core's `FailedAuthThrottle`: whether it builds a `defaultdict`, and whether `check()` assigns into
  the failure map (an insert);
- for juniper-data: the `MAX_REQUEST_BODY_BYTES` assignment.

With --dump CLASS PACKAGE VERSION it prints that class's source from that release instead.

Usage: 2026-11-07_flood4_ml_docs_wheel_probe.py [<package> ...]
       2026-11-07_flood4_ml_docs_wheel_probe.py --dump <class> <package> <version>
"""

from __future__ import annotations

import ast
import io
import json
import sys
import urllib.request
import zipfile

PACKAGES = ("juniper-service-core", "juniper-observability", "juniper-cascor", "juniper-data", "juniper-canopy")


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resp:  # nosec B310 -- fixed https://pypi.org / files.pythonhosted.org URLs
        return resp.read()


def _wheels(package: str) -> list[tuple[str, str, str]]:
    releases = json.loads(_get(f"https://pypi.org/pypi/{package}/json"))["releases"]
    rows = []
    for version, files in releases.items():
        wheel = [f for f in files if f["filename"].endswith(".whl")]
        if wheel:
            rows.append((wheel[0]["upload_time_iso_8601"][:16], version, wheel[0]["url"]))
    return sorted(rows)


def _modules(blob: bytes) -> dict[str, str]:
    out = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            if name.endswith(".py"):
                out[name] = zf.read(name).decode("utf-8", "replace")
    return out


def _parse(src: str) -> ast.AST | None:
    try:
        return ast.parse(src)
    except SyntaxError:
        return None


def _attr_calls(tree: ast.AST, attr: str) -> list[ast.Call]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr]


def _is_const(node: ast.AST, value: object) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _report(package: str, version: str, uploaded: str, modules: dict[str, str]) -> None:
    print(f"== {package} {version} (uploaded {uploaded})")
    for name, src in sorted(modules.items()):
        tree = _parse(src)
        if tree is None:
            if "class APIKeyAuth" in src or "sentry_sdk.init(" in src:
                print(f"   {name}: UNPARSEABLE here (newer syntax?)")
            continue
        classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        if "APIKeyAuth" in classes:
            surrogate = any(any(_is_const(a, "surrogatepass") for a in c.args) for c in _attr_calls(tree, "encode"))
            print(f"   {name}: APIKeyAuth; byte compare (encode ... surrogatepass): {'YES' if surrogate else 'no'}")
            for call in _attr_calls(tree, "compare_digest"):
                print(f"      :{call.lineno} {ast.unparse(call)}")
        if name.endswith("juniper_observability/sentry.py"):
            kws = [(c.lineno, ast.unparse(k.value)) for c in ast.walk(tree) if isinstance(c, ast.Call) for k in c.keywords if k.arg == "include_local_variables"]
            pops = [c.lineno for c in _attr_calls(tree, "pop") if c.args and _is_const(c.args[0], "vars")]
            print(f"   {name}: include_local_variables= {kws or 'never passed'}; pop('vars') at {pops or 'nowhere'}")
        if not name.startswith("juniper_observability/"):
            for call in _attr_calls(tree, "init"):
                if isinstance(call.func.value, ast.Name) and call.func.value.id == "sentry_sdk":
                    print(f"   {name}:{call.lineno}: sentry_sdk.init keywords {[k.arg for k in call.keywords]}")
        if "FailedAuthThrottle" in classes:
            cls = classes["FailedAuthThrottle"]
            dd = any(isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", None)) == "defaultdict" for n in ast.walk(cls))
            check = [f for f in cls.body if isinstance(f, ast.FunctionDef) and f.name == "check"]
            stores = []
            for fn in check:
                for n in ast.walk(fn):
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, (ast.AugAssign, ast.AnnAssign)) else []
                    stores += [f":{n.lineno} {ast.unparse(t)}" for t in targets if isinstance(t, ast.Subscript)]
            subscript_reads = []
            for fn in check:
                subscript_reads += [f":{n.lineno} {ast.unparse(n)}" for n in ast.walk(fn) if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Load) and "fail" in ast.unparse(n.value)]
            print(f"   {name}: FailedAuthThrottle defaultdict: {'YES' if dd else 'no'}; check() subscript stores {stores or 'none'}; map subscript reads {subscript_reads or 'none'}")
        if name.endswith("juniper_data/api/constants.py"):
            for n in ast.walk(tree):
                if isinstance(n, (ast.Assign, ast.AnnAssign)) and "MAX_REQUEST_BODY_BYTES" in ast.unparse(n):
                    print(f"   {name}:{n.lineno}: {ast.unparse(n)}")


def _dump(cls_name: str, package: str, version: str) -> int:
    for uploaded, ver, url in _wheels(package):
        if ver != version:
            continue
        for name, src in sorted(_modules(_get(url)).items()):
            tree = _parse(src)
            for n in ast.walk(tree) if tree else []:
                if isinstance(n, ast.ClassDef) and n.name == cls_name:
                    print(f"== {package} {version} (uploaded {uploaded}) {name}:{n.lineno}")
                    print(ast.get_source_segment(src, n))
                    return 0
    print(f"{cls_name} not found in {package} {version}")
    return 1


def main(argv: list[str]) -> int:
    if argv[1:2] == ["--dump"]:
        if len(argv) != 5:
            print(__doc__)
            return 2
        return _dump(argv[2], argv[3], argv[4])
    for package in argv[1:] or PACKAGES:
        for uploaded, version, url in _wheels(package):
            _report(package, version, uploaded, _modules(_get(url)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
