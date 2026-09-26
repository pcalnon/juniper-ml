"""Is the finding's frame in_app when the compare lives in a pip-installed package? (capturing transport)"""
import sentry_sdk
from sentry_sdk.transport import Transport

import juniper_service_core.security as sec


class Capturing(Transport):
    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


t = Capturing()
sentry_sdk.init(dsn="http://public@127.0.0.1:9/1", transport=t, include_local_variables=True)
print("service-core from:", sec.__file__)
try:
    sec.APIKeyAuth(["k-" + "x" * 8]).validate(chr(0xA0))
    print("no raise (fixed copy)")
except TypeError:
    sentry_sdk.capture_exception()
sentry_sdk.flush()
for env in t.envelopes:
    ev = env.get_event()
    if ev and ev.get("exception"):
        for fr in ev["exception"]["values"][-1]["stacktrace"]["frames"]:
            print(f"  frame {fr.get('function'):12} in_app={fr.get('in_app')} has_vars={'vars' in fr} module={fr.get('module')}")
