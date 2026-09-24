"""Lane B, T1: can an ASCII header carry a key that str.strip() empties?

juniper-ml#2059's blank-api-key-filter summary says a whitespace-only canopy key was "a key no ASCII
header can carry". canopy#678 records that U+001C..U+001F -- ASCII control characters, which
str.strip() removes -- pass h11. This feeds such a header to h11 (and httptools, if present) and
prints what the server side would see. Nothing is sent over a network.
"""

from __future__ import annotations

import sys

VALUES = {
    "space x3": b"   ",
    "tab": b"\t",
    "0x1c0x1c": b"\x1c\x1c",
    "0x1f": b"\x1f",
}


def via_h11(raw: bytes):
    import h11

    conn = h11.Connection(h11.SERVER)
    conn.receive_data(b"GET / HTTP/1.1\r\nHost: x\r\nX-API-Key: " + raw + b"\r\n\r\n")
    try:
        event = conn.next_event()
    except Exception as exc:  # noqa: BLE001 -- report the parser's refusal
        return f"REFUSED ({type(exc).__name__})"
    for name, value in event.headers:
        if name == b"x-api-key":
            text = value.decode("latin-1")
            return f"delivered {text!r}; str.strip() -> {text.strip()!r}"
    return "header absent"


def via_httptools(raw: bytes):
    try:
        import httptools
    except ImportError:
        return "httptools not installed"
    seen = {}

    class P:
        def on_header(self, name, value):
            if name.lower() == b"x-api-key":
                seen["v"] = value

    parser = httptools.HttpRequestParser(P())
    try:
        parser.feed_data(b"GET / HTTP/1.1\r\nHost: x\r\nX-API-Key: " + raw + b"\r\n\r\n")
    except Exception as exc:  # noqa: BLE001
        return f"REFUSED ({type(exc).__name__})"
    if "v" not in seen:
        return "header absent"
    text = seen["v"].decode("latin-1")
    return f"delivered {text!r} (before uvicorn's own strip)"


def main() -> int:
    import h11

    print(f"h11 {h11.__version__}")
    for label, raw in VALUES.items():
        print(f"{label:10} h11: {via_h11(raw)} | httptools: {via_httptools(raw)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
