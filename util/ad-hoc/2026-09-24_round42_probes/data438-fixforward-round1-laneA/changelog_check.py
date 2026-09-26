#!/usr/bin/env python3
"""Lane A: compare CHANGELOG.md sections across head, base (0f0f7e0e) and the v0.16.0 tag, byte for byte.

Reads the three CHANGELOG.md blobs with ``git show`` (read-only) from the juniper-data checkout.
"""

import re
import subprocess

REPO = "/home/pcalnon/Development/python/Juniper/juniper-data"
REFS = {"head": "d1c66a112e4bc70ee97496a14265f7b90e10fb88", "base": "0f0f7e0e226e6046fc49541a4baa6dd1bd8b67ce", "tag": "v0.16.0"}


def blob(ref: str) -> bytes:
    return subprocess.run(["git", "-C", REPO, "show", f"{ref}:CHANGELOG.md"], check=True, capture_output=True).stdout


def section(text: bytes, version: str) -> bytes:
    """From the ``## [version]`` heading up to (not including) the next ``## [`` heading."""
    start = re.search(rb"^## \[" + re.escape(version.encode()) + rb"\].*$", text, re.M)
    assert start, version
    nxt = re.search(rb"^## \[", text[start.end():], re.M)
    end = start.end() + nxt.start() if nxt else len(text)
    return text[start.start():end]


def tail_from(text: bytes, version: str) -> bytes:
    start = re.search(rb"^## \[" + re.escape(version.encode()) + rb"\].*$", text, re.M)
    return text[start.start():]


texts = {name: blob(ref) for name, ref in REFS.items()}
print("tag object:", subprocess.run(["git", "-C", REPO, "rev-parse", "v0.16.0^{commit}"], capture_output=True, text=True).stdout.strip())
for name, text in texts.items():
    s = section(text, "0.16.0")
    print(f"{name:5} [0.16.0] section: {len(s)} bytes, {s.count(b'\n')} lines")
h, b, t = (section(texts[n], "0.16.0") for n in ("head", "base", "tag"))
print("head [0.16.0] == tag [0.16.0]:", h == t)
print("base [0.16.0] == tag [0.16.0]:", b == t)
ht, bt, tt = (tail_from(texts[n], "0.16.0") for n in ("head", "base", "tag"))
print(f"heading-to-EOF: head {len(ht)} bytes / tag {len(tt)} bytes / base {len(bt)} bytes")
print("head heading-to-EOF == tag heading-to-EOF:", ht == tt)
print("head heading-to-EOF == base heading-to-EOF:", ht == bt)
unrel_head = section(texts["head"], "Unreleased")
unrel_base = section(texts["base"], "Unreleased")
print("'Moved here from' in head [Unreleased]:", b"Moved here from" in unrel_head)
print("'Moved here from' in base [Unreleased]:", b"Moved here from" in unrel_base)
print("'Moved here from' anywhere in head CHANGELOG:", b"Moved here from" in texts["head"])
