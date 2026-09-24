#!/usr/bin/env python3
"""Evaluate the gate's own cors-outside-auth ORDERED site (markers + order) against canopy main's
src/main.py, with juniper-data's and juniper-cascor's fixed app.py as positive controls, and a mutated
canopy copy (CORS block moved after RequestIdMiddleware) as the discriminating control.
Imports guard_is_present / ForkSite / markers_out_of_order from the PR-head test module (scratch copy)."""
import importlib.util
import os
import sys

S = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("drift", os.path.join(S, "head/tests/test_service_fork_drift.py"))
drift = importlib.util.module_from_spec(spec)
sys.modules["drift"] = drift
spec.loader.exec_module(drift)

cors = next(g for g in drift.GUARDS if g.guard_id == "cors-outside-auth")
markers = cors.sites[0].markers
print("cors-outside-auth markers:", markers, "ordered:", cors.sites[0].ordered)
site = drift.ForkSite("juniper-canopy", "src/main.py", markers, ordered=True)

def show(label, text):
    idx = [text.find(m) for m in markers]
    print(f"{label:34} present={all(m in text for m in markers)} first-index={idx} guard_is_present={drift.guard_is_present(text, site)}")

canopy = open(os.path.join(S, "canopy_main_6c4ad9a9.py"), encoding="utf-8").read()
show("canopy main 6c4ad9a9", canopy)
show("juniper-data app.py 3adb33e", open(os.path.join(S, "data_app_3adb33e.py"), encoding="utf-8").read())
show("juniper-cascor app.py 33c965b", open(os.path.join(S, "cascor_app_33c965b.py"), encoding="utf-8").read())

# discriminating control: move canopy's CORS block after RequestIdMiddleware registration
start = canopy.index("# CORS: only enable when origins are explicitly configured.")
end = canopy.index("# Security headers (outermost")
block = canopy[start:end]
mutated = canopy[:start] + canopy[end:]
anchor = "app.add_middleware(RequestIdMiddleware)"
pos = mutated.index(anchor) + len(anchor)
mutated = mutated[:pos] + "\n" + block + mutated[pos:]
show("canopy with CORS moved last (ctrl)", mutated)
