"""Lane B (r42d): is [0.16.0] (and everything below it) byte-identical to the v0.16.0 tag's?"""

import hashlib
import re
from pathlib import Path

G = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB/out/git")


def section(text: str, version: str) -> str:
    start = text.index(f"## [{version}]")
    nxt = re.search(r"^## \[", text[start + 3 :], re.M)
    return text[start : start + 3 + nxt.start()] if nxt else text[start:]


def tail(text: str, version: str) -> str:
    return text[text.index(f"## [{version}]") :]


tag = (G / "changelog-v0.16.0.md").read_text()
head = (G / "changelog-head.md").read_text()
main = (G / "changelog-main.md").read_text()
for name, text in (("head", head), ("main", main)):
    s_tag, s = section(tag, "0.16.0"), section(text, "0.16.0")
    print(f"{name}: [0.16.0] identical={s == s_tag} lines={s.count(chr(10))} sha={hashlib.sha256(s.encode()).hexdigest()[:12]} tag_sha={hashlib.sha256(s_tag.encode()).hexdigest()[:12]}")
    print(f"{name}: heading-to-EOF identical={tail(text, '0.16.0') == tail(tag, '0.16.0')}")
unrel_head = section(head, "Unreleased")
unrel_main = section(main, "Unreleased")
print("head [Unreleased] contains 'Moved here':", "Moved here" in unrel_head, "| main:", "Moved here" in unrel_main)
print("head [Unreleased] subsections:", re.findall(r"^### (\w+)", unrel_head, re.M))
