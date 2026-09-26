"""Lane B (r42d): which bytes around '*' does each parser pass, and does str.strip() eat them?

Feeds a raw request with `If-None-Match: <b>*<b>` to h11 and to httptools, for every byte b in
0x00-0xFF except CR/LF, and records whether the parser accepted the field; then whether Python's
str.strip() (on the latin-1 decoded value) reduces it to '*'.
"""

import json

import h11
import httptools


def h11_accepts(b: int) -> bool:
    conn = h11.Connection(h11.SERVER)
    conn.receive_data(b"GET / HTTP/1.1\r\nHost: x\r\nIf-None-Match: " + bytes([b]) + b"*" + bytes([b]) + b"\r\n\r\n")
    try:
        ev = conn.next_event()
    except h11.RemoteProtocolError:
        return False
    return isinstance(ev, h11.Request)


class P:
    def __init__(self):
        self.done = False

    def on_message_complete(self):
        self.done = True


def httptools_accepts(b: int) -> bool:
    p = P()
    parser = httptools.HttpRequestParser(p)
    try:
        parser.feed_data(b"GET / HTTP/1.1\r\nHost: x\r\nIf-None-Match: " + bytes([b]) + b"*" + bytes([b]) + b"\r\n\r\n")
    except httptools.HttpParserError:
        return False
    return p.done


rows = {}
for b in range(256):
    if b in (0x0A, 0x0D):
        continue
    stripped_to_star = (chr(b) + "*" + chr(b)).strip() == "*"
    if not stripped_to_star:
        continue
    rows[f"0x{b:02X}"] = {"h11": h11_accepts(b), "httptools": httptools_accepts(b)}
print(json.dumps({"h11": h11.__version__, "httptools": httptools.__version__, "bytes_str_strip_reduces_to_star": rows}, indent=1))
