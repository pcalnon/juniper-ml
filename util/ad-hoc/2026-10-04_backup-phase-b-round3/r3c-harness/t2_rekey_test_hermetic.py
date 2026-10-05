#!/usr/bin/env python3
"""Lane C round 3: is test_rekey_dry_run_prints_the_whole_sequence_in_order_and_never_reverts hermetic?

The re-key script's INSTALLED_UNIT (/etc/systemd/system/duplicati.service) has no override, and the test
runs the real script. Simulate the production host AFTER the installer has run (P0 step 8 / assessment step
9) by running a copy whose INSTALLED_UNIT points at a scratch copy of the repository unit, then apply the
test's own assertions to its output. /etc is not touched.
"""
import shutil
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
F = S / "frozen"
W = S / "rekey_hermetic"
if W.exists():
    shutil.rmtree(W)
(W / "repo/util/ad-hoc").mkdir(parents=True)
(W / "repo/util/systemd").mkdir(parents=True)
shutil.copy(F / "util/systemd/duplicati.service", W / "repo/util/systemd/duplicati.service")
shutil.copy(F / "util/ad-hoc/2026-10-03_rekey_gate.py", W / "repo/util/ad-hoc/")
shutil.copy(F / "util/ad-hoc/yamaguchi_server_api.py", W / "repo/util/ad-hoc/")
(W / "installed").mkdir()
shutil.copy(F / "util/systemd/duplicati.service", W / "installed/duplicati.service")
text = (F / "util/ad-hoc/2026-10-03_rekey_settings_key.bash").read_text()
text = text.replace("INSTALLED_UNIT=/etc/systemd/system/${UNIT}", f"INSTALLED_UNIT={W}/installed/${{UNIT}}")
(W / "repo/util/ad-hoc/rekey.bash").write_text(text)
for label, script in (("as on CI (no installed unit)", F / "util/ad-hoc/2026-10-03_rekey_settings_key.bash"), ("after the installer ran (installed unit readable)", W / "repo/util/ad-hoc/rekey.bash")):
    r = subprocess.run(["bash", str(script), "--dry-run"], capture_output=True, text=True, env={"PATH": f"{S / 'stubs/bin'}:/usr/bin:/bin", "STUB_LOG": str(W / "stub.log"), "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(W)})
    would = [ln.split("would: ", 1)[1] for ln in r.stderr.splitlines() if "would: " in ln]
    print(f"{label}: exit={r.returncode} would-lines={len(would)} 'DRY RUN:' printed={'DRY RUN:' in r.stderr}"
          f"  -> the test's assertIn('DRY RUN:') would {'PASS' if 'DRY RUN:' in r.stderr else 'FAIL'}")
