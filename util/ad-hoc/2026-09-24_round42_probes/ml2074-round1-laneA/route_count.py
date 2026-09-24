#!/usr/bin/env python3
"""Lane A: count canopy's key-gated (method, path) pairs at a given tree -- independent of canopy's
own sweep script. usage: route_count.py <tree-root>   (run in a subprocess per tree)
Key-gated = neither SecurityMiddleware._is_exempt nor _is_key_exempt (the tree's OWN methods).
Pairs exclude HEAD/OPTIONS; websocket routes have no methods and are skipped."""
import os
import sys

tree = sys.argv[1]
for k in [k for k in os.environ if k.startswith(("JUNIPER_CANOPY_", "CANOPY_", "JUNIPER_CASCOR", "JUNIPER_DATA", "CASCOR_"))]:
    del os.environ[k]
os.environ.update({"JUNIPER_CANOPY_DEMO_MODE": "true", "JUNIPER_CANOPY_JUNIPER_DATA_URL": "http://127.0.0.1:1"})
src = os.path.join(tree, "src")
sys.path.insert(0, src)
os.chdir(src)
import main  # noqa: E402
import middleware  # noqa: E402

assert main.__file__.startswith(src), main.__file__
assert middleware.__file__.startswith(src), middleware.__file__
mw = middleware.SecurityMiddleware.__new__(middleware.SecurityMiddleware)
pairs = []
for r in main.app.routes:
    methods = getattr(r, "methods", None)
    path = getattr(r, "path", None)
    if not methods or path is None:
        continue
    for m in sorted(methods - {"HEAD", "OPTIONS"}):
        pairs.append((m, path))
pairs = sorted(set(pairs))
gated = [(m, p) for m, p in pairs if not mw._is_exempt(p) and not mw._is_key_exempt(p)]
state = [(m, p) for m, p in gated if m in {"POST", "PUT", "PATCH", "DELETE"}]
pget = [(m, p) for m, p in gated if m == "GET" and "{" not in p]
print(f"tree={tree.rsplit('/', 1)[-1]} all_pairs={len(pairs)} key_gated={len(gated)} state_changing={len(state)} parameterless_GET={len(pget)} has_/api/selection={('GET', '/api/selection') in gated}")
