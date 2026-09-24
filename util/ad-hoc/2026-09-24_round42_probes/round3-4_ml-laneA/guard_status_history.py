"""Lane A: each guard's status at every commit that touched tests/test_service_fork_drift.py on
origin/main -- to re-derive "promoted from KNOWN_GAP, except the compare row, which entered the gate
already fixed and was added directly as ENFORCED" (register line 242), and the row-1278 anchors."""

import re
import subprocess

REPO = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map"
PATH = "tests/test_service_fork_drift.py"
commits = ["d1ce9958", "53751fac", "132832f0", "b9629de0", "ea24a19a", "f5222f9d"]
for c in ["27e1541d", "b8b24b41"]:
    commits.append(c)
for c in commits:
    src = subprocess.run(["git", "-C", REPO, "show", f"{c}:{PATH}"], capture_output=True, text=True, check=True).stdout
    pairs = re.findall(r'guard_id="([^"]+)".*?status=(ENFORCED|KNOWN_GAP)', src, flags=re.S)
    fork = re.search(r"^_FORK_REPOS = .*$", src, flags=re.M)
    fork_line = src[: fork.start()].count("\n") + 1 if fork else None
    assert_line = next((i + 1 for i, l in enumerate(src.splitlines()) if "self.assertIn(site.repo, _FORK_REPOS)" in l), None)
    print(f"{c}: " + ", ".join(f"{g}={s}" for g, s in pairs))
    print(f"          _FORK_REPOS at :{fork_line} -> {fork.group(0) if fork else None}; assertIn(site.repo, _FORK_REPOS) at :{assert_line}")
