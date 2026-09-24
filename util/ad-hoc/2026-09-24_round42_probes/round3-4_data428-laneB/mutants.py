#!/usr/bin/env python3
"""Lane B (round 3, juniper-data#428 at 3a76a4c): independent mutation runs.

Each mutant is applied to a FRESH copy of the extracted tree (never the repo), then:
  1. the conditional-request test file is run;
  2. if the mutant survives it, the WHOLE unit suite is run, so "survives" means the suite.
Every edit asserts its find-string occurs exactly once, so a stale mutant cannot pass vacuously.

Usage: mutants.py [name-prefix ...]   (no args = all)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LANE = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneB")
SRC = LANE / "src"
WORK = LANE / "mut"
PY = "/opt/miniforge3/envs/JuniperData/bin/python"
T_COND = "juniper_data/tests/unit/test_conditional_requests.py"
T_UNIT = "juniper_data/tests/unit"

ROUTES = "juniper_data/api/routes/datasets.py"
BASE = "juniper_data/storage/base.py"
CACHE = "juniper_data/api/http_cache.py"

LOCKED_BLOCK = (
    "        with self._version_lock, self._meta_write_lock(dataset_id):\n"
    "            meta = self.get_meta(dataset_id)\n"
    "            if meta is None:\n"
    "                return None\n"
    "            if precondition is not None and not precondition(meta):\n"
    "                raise PreconditionFailedError(dataset_id)\n"
    "            tags = set(meta.tags)\n"
    "            tags.update(add_tags)\n"
    "            tags -= set(remove_tags)\n"
    "            meta.tags = sorted(tags)\n"
    "            self.update_meta(dataset_id, meta)\n"
    "            return meta\n"
)

MUTATIONS: dict[str, list[tuple[str, str, str]]] = {
    # --- round 2's named mutations, re-derived against 3a76a4c ---
    "N1_check_before_version_lock": [
        (
            BASE,
            "        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n            if precondition is not None and not precondition(meta):\n                raise PreconditionFailedError(dataset_id)\n",
            "        if precondition is not None:\n            early = self.get_meta(dataset_id)\n            if early is not None and not precondition(early):\n                raise PreconditionFailedError(dataset_id)\n        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n",
        )
    ],
    "N2_route_checks_and_passes_None": [
        (
            ROUTES,
            "    try:\n        meta = await asyncio.to_thread(store.update_tags, dataset_id, request.add_tags, request.remove_tags, precondition if conditional else None)\n",
            "    if conditional:\n        early = await asyncio.to_thread(store.get_meta, dataset_id)\n        if early is not None and not precondition(early):\n            raise _precondition_failed()\n    try:\n        meta = await asyncio.to_thread(store.update_tags, dataset_id, request.add_tags, request.remove_tags, None)\n",
        )
    ],
    "N3_write_INM_honours_only_star": [
        (
            CACHE,
            "    return if_none_match is not None and (not _well_formed(if_none_match) or _list_names(if_none_match, etag, strong=False))\n",
            "    return if_none_match is not None and (not _well_formed(if_none_match) or if_none_match.strip() == \"*\")\n",
        )
    ],
    "N4_artifact_304_drops_cache_control": [
        (
            ROUTES,
            "                return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)\n",
            "                return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={k: v for k, v in headers.items() if k != \"Cache-Control\"})\n",
        )
    ],
    "N6_artifact_412_records_access": [
        (
            ROUTES,
            "            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                raise _precondition_failed()\n            if outcome == status.HTTP_304_NOT_MODIFIED:\n                # Revalidating",
            "            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                store.record_access(dataset_id)\n                raise _precondition_failed()\n            if outcome == status.HTTP_304_NOT_MODIFIED:\n                # Revalidating",
        )
    ],
    # --- Lane B's own: reorderings neither atomicity test targets ---
    "N7_check_inside_version_lock_but_outside_flock": [
        (
            BASE,
            LOCKED_BLOCK,
            "        with self._version_lock:\n"
            "            meta = self.get_meta(dataset_id)\n"
            "            if meta is None:\n"
            "                return None\n"
            "            if precondition is not None and not precondition(meta):\n"
            "                raise PreconditionFailedError(dataset_id)\n"
            "            with self._meta_write_lock(dataset_id):\n"
            "                meta = self.get_meta(dataset_id)\n"
            "                if meta is None:\n"
            "                    return None\n"
            "                tags = set(meta.tags)\n"
            "                tags.update(add_tags)\n"
            "                tags -= set(remove_tags)\n"
            "                meta.tags = sorted(tags)\n"
            "                self.update_meta(dataset_id, meta)\n"
            "                return meta\n",
        )
    ],
    "N8_stale_snapshot_checked_inside_the_lock": [
        (
            BASE,
            "        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n            if precondition is not None and not precondition(meta):\n                raise PreconditionFailedError(dataset_id)\n",
            "        snapshot = self.get_meta(dataset_id)\n        with self._version_lock, self._meta_write_lock(dataset_id):\n            meta = self.get_meta(dataset_id)\n            if meta is None:\n                return None\n            if precondition is not None and not precondition(snapshot if snapshot is not None else meta):\n                raise PreconditionFailedError(dataset_id)\n",
        )
    ],
    # --- the orphan path the fix added ---
    "O1_orphan_304_leaves_stream_open": [
        (
            ROUTES,
            "        if outcome is not None:\n            _close_artifact_stream(artifact_stream)\n            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                raise _precondition_failed()\n",
            "        if outcome is not None:\n            if outcome == status.HTTP_412_PRECONDITION_FAILED:\n                _close_artifact_stream(artifact_stream)\n                raise _precondition_failed()\n",
        )
    ],
    "O2_orphan_evaluated_only_for_if_match": [
        (
            ROUTES,
            "    if conditional and not evaluated:\n",
            "    if if_match and not evaluated:\n",
        )
    ],
    "O3_orphan_304_records_no_access": [
        (
            ROUTES,
            "                raise _precondition_failed()\n            asyncio.get_event_loop().call_soon(lambda: store.record_access(dataset_id))\n            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)\n",
            "                raise _precondition_failed()\n            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)\n",
        )
    ],
    # --- the cap and the write direction ---
    "C1_cap_off_by_one": [
        (CACHE, "    if len(field) > MAX_PRECONDITION_FIELD_LENGTH:\n", "    if len(field) >= MAX_PRECONDITION_FIELD_LENGTH:\n"),
    ],
    "C2_empty_write_INM_fails_closed": [
        (
            CACHE,
            "    return if_none_match is not None and (not _well_formed(if_none_match) or _list_names(if_none_match, etag, strong=False))\n",
            "    return if_none_match is not None and (not if_none_match.strip() or not _well_formed(if_none_match) or _list_names(if_none_match, etag, strong=False))\n",
        )
    ],
    "C3_patch_conditional_by_truthiness": [
        (
            ROUTES,
            "    conditional = if_match_field is not None or if_none_match_field is not None\n",
            "    conditional = bool(if_match_field or if_none_match_field)\n",
        )
    ],
    "C4_read_empty_if_match_ignored": [
        (
            CACHE,
            "    return if_match is not None and not _list_names(if_match, etag, strong=True)\n",
            "    return bool(if_match) and not _list_names(if_match, etag, strong=True)\n",
        )
    ],
    # --- the InvalidDatasetIdError split ---
    "I1_reraise_every_ValueError": [
        (ROUTES, "    except InvalidDatasetIdError:\n        raise\n", "    except ValueError:\n        raise\n"),
    ],
    "I2_traversal_check_raises_plain_ValueError": [
        (
            "juniper_data/storage/local_fs.py",
            '            raise InvalidDatasetIdError(f"Path traversal detected for dataset_id: {dataset_id!r}")\n',
            '            raise ValueError(f"Path traversal detected for dataset_id: {dataset_id!r}")\n',
        )
    ],
}


def run_pytest(work: Path, target: str) -> tuple[int, str]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(work), "TMPDIR": str(LANE / "tmp")}
    proc = subprocess.run([PY, "-m", "pytest", target, "-p", "no:cacheprovider", "-p", "no:randomly", "--no-header"], cwd=work, capture_output=True, text=True, env=env)
    lines = proc.stdout.splitlines()
    summary = [ln for ln in lines if (" passed" in ln or " failed" in ln or " error" in ln) and ("==" in ln or ln.startswith(("FAILED", "ERROR")) or " in " in ln)]
    failed = [ln for ln in lines if ln.startswith(("FAILED", "ERROR"))]
    return proc.returncode, "\n".join(["        " + s for s in (failed[:8] + summary[-1:])])


def run(name: str) -> str:
    edits = MUTATIONS[name]
    work = WORK / name
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SRC, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    for rel, find, repl in edits:
        path = work / rel
        text = path.read_text(encoding="utf-8")
        count = text.count(find)
        if count != 1:
            shutil.rmtree(work)
            return f"INVALID  {name}: find-string occurs {count} times in {rel}"
        path.write_text(text.replace(find, repl), encoding="utf-8")
    rc, out = run_pytest(work, T_COND)
    if rc != 0:
        shutil.rmtree(work)
        return f"CAUGHT   {name} (by {T_COND})\n{out}"
    rc2, out2 = run_pytest(work, T_UNIT)
    shutil.rmtree(work)
    verdict = "CAUGHT  " if rc2 != 0 else "SURVIVED"
    return f"{verdict} {name} (conditional file passed; whole unit suite rc={rc2})\n{out}\n{out2}"


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    (LANE / "tmp").mkdir(parents=True, exist_ok=True)
    wanted = [n for n in MUTATIONS if not sys.argv[1:] or any(n.startswith(p) for p in sys.argv[1:])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, wanted):
            print(result, flush=True)
