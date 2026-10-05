#!/usr/bin/env python3
"""Lane C round 3: an edit whose `new` is "" can never FAIL on absence (already_applied returns True for
new == ""). If upstream rewords all five phase markers, the deletion is silently skipped as ALREADY and the
reworded "held by the STOP" markers survive into a design whose front matter says the STOP is cleared."""
import importlib.util

spec = importlib.util.spec_from_file_location("atk", "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/bin/t1_gate_attacks.py")
atk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atk)
atk.OUT.mkdir(parents=True, exist_ok=True)
old = "*Held by the STOP at the top of §8 (note 10.1g).*"
print("markers in staged D:", atk.STAGED.count(old))
d = atk.STAGED.replace(old, "*Held by the STOP (see the top of §8, note 10.1g).*")
r, wrote = atk.run_case("f1_all_markers_reworded", d, atk.SCRIPT, expect_write=True)
out = (atk.OUT / "f1_all_markers_reworded" / atk.D_REL).read_text(encoding="utf-8")
print("reworded markers left in the written design:", out.count("*Held by the STOP (see the top of §8, note 10.1g).*"))
print("ALREADY line for the marker edit:", [ln for ln in r.stdout.splitlines() if "phase markers" in ln])
d2 = atk.STAGED.replace("*Items 2 and 4 are held by the STOP at the top of §8; items 1, 5, 6 and 7 are released (note 10.1g).*", "*Items 2 and 4 are held by the STOP; items 1, 5, 6 and 7 are released (note 10.1g).*")
atk.run_case("f2_p05a_marker_reworded", d2, atk.SCRIPT, expect_write=True)
out2 = (atk.OUT / "f2_p05a_marker_reworded" / atk.D_REL).read_text(encoding="utf-8")
print("reworded P0.5a marker left:", out2.count("*Items 2 and 4 are held by the STOP; items"))
