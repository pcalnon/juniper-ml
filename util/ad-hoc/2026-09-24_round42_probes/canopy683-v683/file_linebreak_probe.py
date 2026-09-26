"""A CANOPY_API_KEY_FILE whose key has an INTERIOR line break: which variable does the padded WARNING name?

Run with PYTHONPATH=<tree>/src, CANOPY_API_KEY unset and CANOPY_API_KEY_FILE pointing at a two-line file.
"""

import security
from frontend import internal_api


class L:
    def __init__(self):
        self.m = []

    def warning(self, m):
        self.m.append(m)


auth = security.get_api_key_auth()
log = L()
n = security.report_api_key_configuration(log)
print("auth enabled:", auth.enabled, "| recorded padded source:", security._padded_key_source, "| warnings:", n)
print("warning begins:", log.m[0][:70] if log.m else None)
print("self-call sends a key:", "X-API-Key" in internal_api.internal_api_headers())
