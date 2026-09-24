"""Apply the proposed linear regex in a scratch copy; run the conditional suite + the ReDoS test (validator scratch)."""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/probes")
import my_mutations as mm  # noqa: E402

OLD = "_ENTITY_TAG_LIST = re.compile(r'[ \\t]*(?:(?:W/)?\"[^\"]*\")?[ \\t]*(?:,[ \\t]*(?:(?:W/)?\"[^\"]*\")?[ \\t]*)*')\n"
NEW = "_ENTITY_TAG_LIST = re.compile(r'[ \\t]*(?:(?:W/)?\"[^\"]*\"[ \\t]*)?(?:,[ \\t]*(?:(?:W/)?\"[^\"]*\"[ \\t]*)?)*')\n"
for name, fix in (("PR head (unfixed)", False), ("fixed regex", True)):
    work = mm.V / "redosfix" / name.split(" ")[0]
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(mm.SRC, work, ignore=shutil.ignore_patterns("__pycache__", "data", "logs", ".git"))
    if fix:
        p = work / "juniper_data/api/http_cache.py"
        text = p.read_text(encoding="utf-8")
        assert text.count(OLD) == 1, text.count(OLD)
        p.write_text(text.replace(OLD, NEW), encoding="utf-8")
    shutil.copy(mm.V / "probes" / "test_proposed_redos.py", work / "juniper_data/tests/unit/test_proposed_redos.py")
    args = ["juniper_data/tests/unit/test_conditional_requests.py", "juniper_data/tests/unit/test_proposed_redos.py", "-p", "no:cacheprovider", "--no-header", "-o", "timeout=20"]
    proc = subprocess.run([mm.PY, "-m", "pytest", *args], cwd=work, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    lines = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line or line.startswith("FAILED")]
    print(f"{name}: rc={proc.returncode}")
    for line in lines:
        print("   ", line[:200])
    shutil.rmtree(work)
