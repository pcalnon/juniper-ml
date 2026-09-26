"""Lane B (r42d): my own mutants of the fix-forward, run against the tests that should see them.

Each mutant is applied to a scratch copy of head's ``juniper_data`` (plus pyproject.toml) by an
exact, count-checked string replacement; the selected test files are then run in that copy, and
the import origin is asserted inside the copy. A mutant "survives" when every selected test passes.

Usage: python my_mutants.py [MX-name ...]
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneB")
HEAD = S / "head"
PY = "/opt/miniforge3/envs/JuniperData/bin/python"
BASE = "juniper_data/storage/base.py"
LFS = "juniper_data/storage/local_fs.py"
ROUTES = "juniper_data/api/routes/datasets.py"

TESTS = [
    "juniper_data/tests/unit/test_conditional_requests.py",
    "juniper_data/tests/unit/test_meta_cross_process_lock.py",
    "juniper_data/tests/unit/test_record_access_concurrency.py",
    "juniper_data/tests/unit/test_storage.py",
    "juniper_data/tests/unit/test_lifecycle.py",
    "juniper_data/tests/unit/test_phase_2d_metrics.py",
    "juniper_data/tests/unit/test_api_routes.py",
]

CREATE_IF_ABSENT = (
    "        with self._version_lock, self._meta_write_lock(dataset_id):\n"
    "            existing = self.get_meta(dataset_id)\n"
    "            if existing is not None:\n"
    "                return existing\n"
    "            if meta.dataset_name is not None and meta.dataset_version is None:\n"
    "                meta.dataset_version = self.next_version_number(meta.dataset_name)\n"
    "            self.save(dataset_id, meta, arrays)\n"
    "            return meta\n"
)

MUTANTS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "MX1": (
        "save_versioned re-checks existence for UNNAMED creates only; a named create still overwrites",
        [(BASE, "            existing = self.get_meta(dataset_id)\n            if existing is not None:\n                return existing\n", "            existing = self.get_meta(dataset_id) if meta.dataset_name is None else None\n            if existing is not None:\n                return existing\n")],
    ),
    "MX2": (
        "the stripe index uses Python's per-process randomised hash(), so two workers pick different stripes for one id",
        [(LFS, "        stripe = int(hashlib.sha256(dataset_id.encode(CHARSET_UTF8)).hexdigest(), 16) % LOCK_STRIPE_COUNT\n", "        stripe = hash(dataset_id) % LOCK_STRIPE_COUNT\n")],
    ),
    "MX4": (
        "the lazy stripe creation no longer re-creates a missing locks/ directory",
        [(LFS, "        except FileNotFoundError:\n            self._ensure_lock_dir()\n", "        except FileNotFoundError:\n")],
    ),
    "MX9": (
        "save_versioned keeps an existing dataset only when its checksum matches; otherwise it overwrites it",
        [(BASE, "            if existing is not None:\n                return existing\n            if meta.dataset_name", "            if existing is not None and existing.checksum == meta.checksum:\n                return existing\n            if meta.dataset_name")],
    ),
    "MX10": (
        "save_versioned re-checks under _version_lock but OUTSIDE the cross-process file lock (check, then lock, then save)",
        [(BASE, CREATE_IF_ABSENT, (
            "        with self._version_lock:\n"
            "            existing = self.get_meta(dataset_id)\n"
            "            if existing is not None:\n"
            "                return existing\n"
            "            with self._meta_write_lock(dataset_id):\n"
            "                if meta.dataset_name is not None and meta.dataset_version is None:\n"
            "                    meta.dataset_version = self.next_version_number(meta.dataset_name)\n"
            "                self.save(dataset_id, meta, arrays)\n"
            "            return meta\n"
        ))],
    ),
    "MX13": (
        "_ensure_lock_dir no longer refuses a locks/ directory that is a symlink or leads out of the root",
        [(LFS, "        if self._lock_dir.is_symlink() or not self._lock_dir.resolve().is_relative_to(self._resolved_base):\n", "        if False:\n")],
    ),
    "MX14": (
        "_create_lock_stripes swallows every exception, including the containment refusal",
        [(LFS, "        except OSError as exc:\n            logging.getLogger(__name__).warning(\"Could not create the lock stripes", "        except Exception as exc:\n            logging.getLogger(__name__).warning(\"Could not create the lock stripes")],
    ),
    "MX17": (
        "a 200 artifact download never records an access (not even when the metadata is readable)",
        [(ROUTES, "    if metadata_readable:\n        asyncio.get_event_loop().call_soon(lambda: store.record_access(dataset_id))\n\n    return StreamingResponse(\n", "    if False:\n        asyncio.get_event_loop().call_soon(lambda: store.record_access(dataset_id))\n\n    return StreamingResponse(\n")],
    ),
    "MX23": (
        "the stripes are CREATED at init without O_NOFOLLOW (a symlink planted before startup is followed and its target created)",
        [(LFS, "os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600))", "os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600))")],
    ),
    "MX24": (
        "the first (non-creating) open of a stripe drops O_NOFOLLOW; only the lazy create keeps it",
        [(LFS, "        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC\n        try:\n            return os.open(lock_path, flags)\n", "        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC\n        try:\n            return os.open(lock_path, os.O_RDWR | os.O_CLOEXEC)\n")],
    ),
    "BASELINE": ("no edit: the selected tests at head, which must all pass", []),
}


def ignore(_dir: str, names: list[str]) -> set[str]:
    return {n for n in names if n in {"__pycache__", ".pytest_cache"}}


def run(name: str) -> dict:
    why, edits = MUTANTS[name]
    work = S / "bt" / f"mut-{name}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.rmtree(work)
    shutil.copytree(HEAD, work, ignore=ignore)  # the whole tree: some suites read repo-root files
    for rel, old, new in edits:
        path = work / rel
        text = path.read_text()
        count = text.count(old)
        assert count == 1, f"{name}: expected one match in {rel}, found {count}"
        path.write_text(text.replace(old, new))
    env = {"PATH": "/usr/bin:/bin", "HOME": str(S), "LANG": "C.UTF-8", "PYTHONPATH": str(work), "PYTHONDONTWRITEBYTECODE": "1"}
    origin = subprocess.run([PY, "-c", "import juniper_data, os; print(os.path.realpath(juniper_data.__file__))"], cwd=work, env=env, capture_output=True, text=True).stdout.strip()
    assert origin.startswith(str(work) + "/"), origin
    bt = S / "bt" / f"mutbt-{name}"
    tests = os.environ["MUT_TESTS"].split() if os.environ.get("MUT_TESTS") else TESTS
    proc = subprocess.run([PY, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider", f"--basetemp={bt}", "-rfE"], cwd=work, env=env, capture_output=True, text=True, timeout=1800)
    shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(bt, ignore_errors=True)
    failed = sorted(set(re.findall(r"^FAILED (\S+)", proc.stdout, re.M) + re.findall(r"^ERROR (\S+)", proc.stdout, re.M)))
    summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-300:]
    return {"mutant": name, "why": why, "rc": proc.returncode, "survived": proc.returncode == 0, "summary": summary, "failed": failed}


def main() -> None:
    names = sys.argv[1:] or list(MUTANTS)
    rows = []
    for name in names:
        row = run(name)
        print(json.dumps(row), flush=True)
        rows.append(row)
    suffix = "-full" if os.environ.get("MUT_TESTS") else ""
    out = S / "out" / ("my_mutants-" + "-".join(names) + suffix + ".json" if sys.argv[1:] else "my_mutants.json")
    out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
