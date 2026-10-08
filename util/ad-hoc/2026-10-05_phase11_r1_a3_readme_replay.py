# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/readme_replay.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: run the evidence README's "Replaying the reading" block VERBATIM from a clean full extraction of 1b7cf44b."""
import re
import subprocess  # nosec B404 - runs the README's own commands in the scratch extraction
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
ROOT = S / "full"
readme = (ROOT / "reports/e2e-canopy-2026-09-02/f058-census-v2/README.md").read_text(encoding="utf-8")
sec = readme.split("## Replaying the reading", 1)[1]
block = re.search(r"```bash\n(.*?)```", sec, re.S).group(1)
(S / "tools/readme_block.bash").write_text("set -u\n" + block, encoding="utf-8")
print("---- block as documented ----")
print(block)
print("---- running from", ROOT, "----")
# Echo each command before running it, so each output can be matched to its line and its README comment.
script = "set -u\n" + "\n".join(f"echo '>>> {line.split('#')[0].strip()}'\n{line}\necho \"exit=$?\"" if line.startswith("python3") else line for line in block.splitlines())
out = subprocess.run(["bash", "-c", script], cwd=ROOT, capture_output=True, text=True)  # nosec B603 B607
(S / "tools/readme_block_out.txt").write_text(out.stdout + "\nSTDERR:\n" + out.stderr, encoding="utf-8")
print(out.stdout[-200:] if len(out.stdout) > 200 else out.stdout)
print("stderr:", out.stderr[:500])
print("python3 =", subprocess.run(["bash", "-c", "command -v python3; python3 --version"], capture_output=True, text=True).stdout)
