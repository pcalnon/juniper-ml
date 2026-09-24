"""Lane B, T1: does the PUBLISHED juniper-service-core (what juniper-recurrence installs) carry the guards?

Downloads the 0.6.0 and 0.7.0 wheels (recurrence pins >=0.6.0,<0.8.0) into this lane's scratch dir
and greps security.py inside each for the two guards' markers. Read-only; nothing is installed.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

LANE = Path(__file__).resolve().parent
MARKERS = {
    "blank-api-key-filter": ("isinstance(k, str)", "k.strip()"),
    "nonshortcircuit-key-compare": ("matched = False", "return matched"),
}


def main() -> int:
    meta = json.load(urllib.request.urlopen("https://pypi.org/pypi/juniper-service-core/json", timeout=30))
    for version in ("0.6.0", "0.7.0"):
        files = meta["releases"][version]
        wheel = next(f for f in files if f["filename"].endswith(".whl"))
        blob = urllib.request.urlopen(wheel["url"], timeout=60).read()
        (LANE / "wheels").mkdir(exist_ok=True)
        (LANE / "wheels" / wheel["filename"]).write_bytes(blob)
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            src = zf.read("juniper_service_core/security.py").decode("utf-8")
        print(f"{version} uploaded {wheel['upload_time_iso_8601']}")
        for guard, markers in MARKERS.items():
            print(f"   {guard}: {'PRESENT' if all(m in src for m in markers) else 'ABSENT'}")
        if "any(hmac.compare_digest" in src:
            print("   NOTE: the wheel still contains any(hmac.compare_digest ...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
