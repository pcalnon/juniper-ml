"""Run N1/N2 (and N3) against the WHOLE unit suite, plus the proposed fix-tests against N1/N2 (validator scratch)."""

import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/probes")
import my_mutations as mm  # noqa: E402

mm.TESTS = ["juniper_data/tests/unit"]
for key in list(mm.MUTATIONS):
    if key.startswith(("N1", "N2", "N3")):
        mm.run(key, mm.MUTATIONS[key])
