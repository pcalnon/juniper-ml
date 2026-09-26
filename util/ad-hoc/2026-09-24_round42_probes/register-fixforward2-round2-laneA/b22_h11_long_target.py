#!/usr/bin/env python3
"""Lane A round 2: the probe comment says the ~26.7 KB deep-cursor URL is refused by uvicorn's h11 parser before
the app sees it. Check the h11 half: an h11 SERVER connection at h11's default max_incomplete_event_size (16 KiB,
which uvicorn uses unless configured) fed that request line. Run with the pinned venv's python (h11 0.16.0).
uvicorn itself is NOT installed in the venv, so its default is not measured here."""
import base64

import h11

deep = base64.urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode("ascii").rstrip("=")
target = f"/v1/datasets?cursor={deep}"
req = f"GET {target} HTTP/1.1\r\nHost: t\r\n\r\n".encode("ascii")
print("request-target bytes:", len(target), "h11 default max_incomplete_event_size:", h11._connection.DEFAULT_MAX_INCOMPLETE_EVENT_SIZE)
conn = h11.Connection(h11.SERVER)
conn.receive_data(req)
try:
    ev = conn.next_event()
    print("h11 parsed the request:", type(ev).__name__)
except h11.RemoteProtocolError as e:
    print("h11 refused:", e, "| status hint", e.error_status_hint)
