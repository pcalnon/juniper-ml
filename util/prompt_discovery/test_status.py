"""test_status probe: last pytest result for the target repo.

Crucially distinguishes ``cold_cache`` (tests were never run in this checkout),
``unavailable`` (cache present but unreadable), and ``stale`` (the cache predates the
current HEAD commit -- or is older than the TTL -- so it measured a *different* tree) from a
genuine ``ok`` with zero failures. This is what keeps "no failures" from masquerading as
fact when the truth is "not measured" or "measured against an old tree" (design S5.6; the
D-1 cache-freshness guard).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from _util import run

# Default staleness TTL (seconds). Mirrors cli.TTL_SECONDS (the grounding bundle's provenance
# TTL); kept as a module-level default so the probe stays self-contained and importable
# without the cli composer. The HEAD-commit-time comparison is the *primary* staleness signal;
# this TTL is the secondary guard (it catches an old cache even with no intervening commit).
DEFAULT_TTL_SECONDS = 900


def _head_commit_time(repo_root: str) -> "int | None":
    """Committer epoch-seconds of the target repo's HEAD, or ``None`` when git is unavailable.

    Returning ``None`` (not a git repo / git missing) makes the HEAD-commit-time comparison a
    no-op and leaves the TTL as the sole staleness signal -- the same graceful-degradation
    contract every other probe honours.
    """
    rc, out, _ = run(["git", "-C", repo_root, "show", "-s", "--format=%ct", "HEAD"])
    out = out.strip()
    if rc != 0 or not out.isdigit():
        return None
    return int(out)


def _stamp_freshness(repo_root: str, mtime_path: Path, ttl_seconds: int, fresh: dict) -> dict:
    """Stamp ``cache_mtime``/``age_seconds`` onto a measured result and downgrade it to
    ``stale`` (with ``failing_count`` blanked) when the cache predates the current HEAD commit
    (primary signal) or is older than ``ttl_seconds`` (secondary signal).

    A genuinely fresh cache keeps its ``ok`` status and real ``failing_count`` -- only now it
    also carries the freshness provenance so a downstream reader can audit the claim.
    """
    try:
        cache_mtime = mtime_path.stat().st_mtime
    except OSError:
        return fresh  # cannot stat the cache -> leave the measured result unqualified (best effort)
    age_seconds = max(0.0, time.time() - cache_mtime)
    result = {**fresh, "cache_mtime": cache_mtime, "age_seconds": age_seconds}
    head_ct = _head_commit_time(repo_root)
    if head_ct is not None and cache_mtime < head_ct:
        reason = "pytest cache predates the current HEAD commit (measured against an older tree)"
    elif ttl_seconds is not None and age_seconds > ttl_seconds:
        reason = f"pytest cache is older than the {ttl_seconds}s TTL (age {int(age_seconds)}s)"
    else:
        return result  # fresh: keep the measured status, now with freshness provenance
    return {**result, "status": "stale", "failing_count": None, "reason": reason}


def probe(repo_root: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict:
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
        return _stamp_freshness(
            repo_root,
            cache_dir,
            ttl_seconds,
            {"status": "ok", "failing_count": 0, "failing": [], "reason": "pytest cache present with no lastfailed record"},
        )
    try:
        data = json.loads(lastfailed.read_text(encoding="utf-8") or "{}")
    except (ValueError, OSError):
        return {"status": "unavailable", "failing_count": None, "failing": [], "reason": "lastfailed unreadable"}
    failing = sorted(data.keys()) if isinstance(data, dict) else []
    return _stamp_freshness(
        repo_root,
        lastfailed,
        ttl_seconds,
        {"status": "ok", "failing_count": len(failing), "failing": failing},
    )
