"""Does the before_send header scrub reach TRANSACTIONS? (send_pii True/False; capturing transport)"""

import sentry_sdk
from sentry_sdk.transport import Transport

from juniper_observability import configure_sentry

SECRET = "-".join(("txn", "probe", "secret", "LEAKMARK", "77aa"))
print("sentry-sdk", sentry_sdk.VERSION)


class Capturing(Transport):
    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


_real_init = sentry_sdk.init
_t = {}


def _init(*a, **kw):
    kw["transport"] = _t["transport"]
    kw["traces_sample_rate"] = 1.0  # sample every transaction so the probe is deterministic
    return _real_init(*a, **kw)


sentry_sdk.init = _init

for send_pii in (False, True):
    _t["transport"] = Capturing()
    configure_sentry("http://public@127.0.0.1:9/1", "txn-probe", "0", send_pii=send_pii)

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/ok", headers={"X-API-Key": SECRET, "Authorization": "Bearer " + SECRET})
    client.get("/boom", headers={"X-API-Key": SECRET})
    sentry_sdk.flush(timeout=5)
    for env in _t["transport"].envelopes:
        for item in env.items:
            if item.type not in ("transaction", "event"):
                continue
            body = item.get_bytes()
            print(f"  send_pii={send_pii!s:5} {item.type:11} secret-in-item={SECRET.encode() in body}", end="")
            if SECRET.encode() in body:
                i = body.find(SECRET.encode())
                print("   context:", body[max(0, i - 90): i + 5].decode("utf-8", "replace"), end="")
            print()
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)
