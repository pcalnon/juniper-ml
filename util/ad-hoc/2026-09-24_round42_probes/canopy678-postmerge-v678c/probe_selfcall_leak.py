"""Adjacent (pre-existing) check: does a dashboard self-call log a raw CANOPY_API_KEY?

Imports canopy with CANOPY_API_KEY set to a REAL-looking key that carries a leading space (not
blank, so auth is ENABLED), then calls the dashboard's mount-time selection hydration handler,
which self-calls GET /api/selection with internal_api_headers(). Captures every log record.
"""

import logging
import os

os.environ["CANOPY_API_KEY"] = " leaked-key-XYZ123"
os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "1")

records = []


class H(logging.Handler):
    def emit(self, r):
        records.append(r)


root = logging.getLogger()
root.addHandler(H())
root.setLevel(logging.DEBUG)

import main  # noqa: E402

print("auth enabled:", main.api_key_auth.enabled)
dm = getattr(main, "dashboard_manager", None)
if dm is None:
    for name in dir(main):
        obj = getattr(main, name)
        if type(obj).__name__ == "DashboardManager":
            dm = obj
            break
print("dashboard manager:", type(dm).__name__ if dm else None)
out = dm._hydrate_selection_handler()
hits = [(r.name, r.levelname, r.getMessage()[:200]) for r in records if "leaked-key-XYZ123" in r.getMessage()]
print("records carrying the key:", len(hits))
for h in hits:
    print("  ", h)
