"""Validator's own mutations: behaviours the PR harness does not mutate. Each runs in a fresh scratch copy."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

V = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2")
SRC = V / "pr"
PY = "/opt/miniforge3/envs/JuniperData/bin/python"
TESTS = ["juniper_data/tests/unit/test_conditional_requests.py", "juniper_data/tests/unit/test_storage.py", "juniper_data/tests/unit/test_api_routes.py"]

ROUTES = "juniper_data/api/routes/datasets.py"
BASE = "juniper_data/storage/base.py"
CACHE = "juniper_data/api/http_cache.py"

MUTATIONS = {
    "N1: base.update_tags evaluates the precondition BEFORE taking the lock (check-then-act race)": [
        (
            BASE,
            "        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n            if precondition is not None and not precondition(meta):\n                raise PreconditionFailedError(dataset_id)\n",
            "        if precondition is not None:\n            early = self.get_meta(dataset_id)\n            if early is not None and not precondition(early):\n                raise PreconditionFailedError(dataset_id)\n        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n",
        )
    ],
    "N2: the route evaluates the precondition itself, outside the store lock, and passes None": [
        (
            ROUTES,
            "    try:\n        meta = await asyncio.to_thread(store.update_tags, dataset_id, request.add_tags, request.remove_tags, precondition if conditional else None)\n",
            "    if conditional:\n        early = await asyncio.to_thread(store.get_meta, dataset_id)\n        if early is not None and not precondition(early):\n            raise _precondition_failed()\n    try:\n        meta = await asyncio.to_thread(store.update_tags, dataset_id, request.add_tags, request.remove_tags, None)\n",
        )
    ],
    "N3: PATCH honours If-None-Match only as '*' (a tag naming the current representation proceeds)": [
        (
            CACHE,
            "    return not if_match_fails(if_match, etag) and not if_none_match_hits(if_none_match, etag)\n",
            "    return not if_match_fails(if_match, etag) and not (if_none_match is not None and if_none_match.strip() == \"*\")\n",
        )
    ],
    "N4: the artifact 304 drops Cache-Control (RFC 9110 15.4.5)": [
        (
            ROUTES,
            "                return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)\n",
            "                return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={k: v for k, v in headers.items() if k != \"Cache-Control\"})\n",
        )
    ],
    "N5 (control): If-None-Match evaluated before If-Match on reads": [
        (
            CACHE,
            "    if if_match_fails(if_match, etag):\n        return 412\n    if if_none_match_hits(if_none_match, etag):\n        return 304\n",
            "    if if_none_match_hits(if_none_match, etag):\n        return 304\n    if if_match_fails(if_match, etag):\n        return 412\n",
        )
    ],
    "N6: a 412 on the ARTIFACT route is recorded as an access": [
        (
            ROUTES,
            "            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                raise _precondition_failed()\n            if outcome == status.HTTP_304_NOT_MODIFIED:\n                # Revalidating",
            "            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                store.record_access(dataset_id)\n                raise _precondition_failed()\n            if outcome == status.HTTP_304_NOT_MODIFIED:\n                # Revalidating",
        )
    ],
}


def run(name: str, edits) -> None:
    work = V / "mut" / name.split(":")[0]
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SRC, work, ignore=shutil.ignore_patterns("__pycache__", "data", "logs", ".git"))
    for rel, find, repl in edits:
        p = work / rel
        text = p.read_text(encoding="utf-8")
        assert text.count(find) == 1, (name, rel, text.count(find))
        p.write_text(text.replace(find, repl), encoding="utf-8")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run([PY, "-m", "pytest", *TESTS, "-p", "no:cacheprovider", "--no-header"], cwd=work, capture_output=True, text=True, env=env)
    tail = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line or line.startswith("FAILED")]
    verdict = "CAUGHT  " if proc.returncode != 0 else "SURVIVED"
    print(f"{verdict} {name}")
    for line in tail[-6:]:
        print("     ", line)
    shutil.rmtree(work)


if __name__ == "__main__":
    for name, edits in MUTATIONS.items():
        run(name, edits)
