#!/usr/bin/env python3
"""Lane A round 2: does h11 (0.16.0, default 16 KiB max_incomplete_event_size) refuse the 26.7 KB deep-cursor
request line when it arrives in chunks, as a TCP read loop may deliver it? Feed it in chunks of N bytes and call
next_event() after each, the way an asyncio protocol's data_received loop does."""
import base64

import h11

deep = base64.urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode("ascii").rstrip("=")
req = f"GET /v1/datasets?cursor={deep} HTTP/1.1\r\nHost: t\r\n\r\n".encode("ascii")
for chunk in (65536, 32768, 16384, 8192, 4096, 1024):
    conn = h11.Connection(h11.SERVER)
    outcome = "?"
    try:
        for i in range(0, len(req), chunk):
            conn.receive_data(req[i:i + chunk])
            ev = conn.next_event()
            if ev is not h11.NEED_DATA:
                outcome = f"parsed ({type(ev).__name__}) after {i + chunk} bytes"
                break
    except h11.RemoteProtocolError as e:
        outcome = f"REFUSED: {e} (hint {e.error_status_hint})"
    print(f"chunk {chunk:6}: {outcome}")
