#!/usr/bin/env python3
"""Lane A: the body's account of M57's control -- under M57, WITHOUT the test's mkdir line, does
test_a_symlink_planted_at_a_lock_file_is_refused_not_followed error on its own setup (FileNotFoundError)?
And WITH the line (the head's test), does it pass under M57?  Runs in a scratch copy of the head tree."""

import shutil
import subprocess
import tempfile
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneA/head")
root = Path(tempfile.mkdtemp(prefix="m57-history-"))
work = root / "repo"
shutil.copytree(HEAD, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "data", "logs", "notes", "docs"))
lfs = work / "juniper_data/storage/local_fs.py"
text = lfs.read_text(encoding="utf-8")
m57_find = "        self._lock_dir = self._base_path / LOCK_DIR_NAME\n        self._create_lock_stripes()\n"
assert text.count(m57_find) == 1
lfs.write_text(text.replace(m57_find, "        self._lock_dir = self._base_path / LOCK_DIR_NAME\n"), encoding="utf-8")
test = work / "juniper_data/tests/unit/test_conditional_requests.py"
node = "juniper_data/tests/unit/test_conditional_requests.py::TestLockStripes::test_a_symlink_planted_at_a_lock_file_is_refused_not_followed"
env = {"PATH": "/opt/miniforge3/envs/JuniperData/bin:/usr/bin:/bin", "HOME": str(Path.home()), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(root)}


def run(label):
    proc = subprocess.run(["/opt/miniforge3/envs/JuniperData/bin/python", "-m", "pytest", node, "-q", "--no-header", "-p", "no:cacheprovider", "--tb=line"], cwd=work, capture_output=True, text=True, env=env)
    lines = [ln for ln in proc.stdout.splitlines() if "Error" in ln or "passed" in ln or "failed" in ln]
    print(f"{label}: rc={proc.returncode} :: {' | '.join(ln.strip()[-160:] for ln in lines[-3:])}")


run("M57, head's test (with the mkdir line)")
t = test.read_text(encoding="utf-8")
line = "        lock_path.parent.mkdir(exist_ok=True)\n"
assert t.count(line) == 1
test.write_text(t.replace(line, ""), encoding="utf-8")
run("M57, the test WITHOUT the mkdir line")
shutil.rmtree(root, ignore_errors=True)
