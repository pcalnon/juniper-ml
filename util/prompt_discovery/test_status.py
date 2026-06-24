"""test_status probe: last pytest result for the target repo.

Crucially distinguishes ``cold_cache`` (tests were never run in this checkout) and
``unavailable`` (cache present but unreadable) from a genuine ``ok`` with zero failures --
so "no failures" can never masquerade as fact when the truth is simply "not measured"
(design S5.6).
"""

from __future__ import annotations

import json
from pathlib import Path


def probe(repo_root: str) -> dict:
    cache_dir = Path(repo_root) / ".pytest_cache"
    lastfailed = cache_dir / "v" / "cache" / "lastfailed"
    if not cache_dir.exists():
        return {
            "status": "cold_cache",
            "failing_count": None,
            "failing": [],
            "reason": "no .pytest_cache (the suite was not run in this checkout)",
        }
    if not lastfailed.exists():
        return {
            "status": "ok",
            "failing_count": 0,
            "failing": [],
            "reason": "pytest cache present with no lastfailed record",
        }
    try:
        data = json.loads(lastfailed.read_text(encoding="utf-8") or "{}")
    except (ValueError, OSError):
        return {"status": "unavailable", "failing_count": None, "failing": [], "reason": "lastfailed unreadable"}
    failing = sorted(data.keys()) if isinstance(data, dict) else []
    return {"status": "ok", "failing_count": len(failing), "failing": failing}
