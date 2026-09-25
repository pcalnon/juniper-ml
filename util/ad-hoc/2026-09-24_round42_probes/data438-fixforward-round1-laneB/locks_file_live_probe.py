"""Lane B (r42d): a live head server over a storage dir whose `locks` entry is a regular FILE.

Shows (1) how the startup warning reaches the log (configured format or Python's last-resort
handler), and (2) what each write route answers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from common import S, fresh_dir, server  # noqa: E402


def main() -> None:
    storage = fresh_dir(S / "locksfile" / "storage")
    (storage / "locks").write_text("not a directory")
    log = S / "out" / "locksfile-server-head.log"
    out: dict = {}
    with server("head", 18780, storage, log) as (base, _proc):
        with httpx.Client(base_url=base, timeout=60) as c:
            r = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}, "persist": True})
            out["create"] = [r.status_code, r.text[:80]]
            out["patch_absent"] = c.patch("/v1/datasets/spiral-3.0.0-0000000000000000/tags", json={"add_tags": ["x"]}).status_code
            out["delete_absent"] = c.delete("/v1/datasets/spiral-3.0.0-0000000000000000").status_code
            out["health"] = c.get("/v1/health").status_code
    lines = log.read_text().splitlines()
    out["log_lines_mentioning_stripes"] = [ln[:200] for ln in lines if "lock stripes" in ln]
    out["first_log_lines"] = [ln[:160] for ln in lines[:6]]
    print(json.dumps(out, indent=1))
    import shutil

    shutil.rmtree(S / "locksfile", ignore_errors=True)


if __name__ == "__main__":
    main()
