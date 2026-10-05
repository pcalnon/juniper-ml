#!/usr/bin/env python3
"""Lane C round 3: the re-key's snapshot-timer pre-flight checks is-ENABLED == "enabled" only.
A timer that is disabled but still ACTIVE (`systemctl disable` without --now), or "enabled-runtime",
passes it. Stubbed: is-enabled answers per case; is-active answers "active" for every unit."""
import importlib.util

spec =importlib.util.spec_from_file_location("t4", "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/bin/t4_rekey_trap.py")
t4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t4)
SRC = t4.F / "util/ad-hoc/2026-10-03_rekey_settings_key.bash"
for label, enabled in (("enabled", "enabled"), ("enabled-runtime", "enabled-runtime"), ("disabled but active", "disabled"), ("linked", "linked")):
    root, script = t4.prepare("T_" + label.replace(" ", "_"), SRC)
    r = t4.run(root, script, STUB_IS_ENABLED=enabled, STUB_IS_ACTIVE="active")
    log = (root / "stub.log").read_text().splitlines()
    timer_queries = [x for x in log if "yamaguchi-server-db-snapshot.timer" in x]
    print(f"timer is-enabled={enabled!r:18} (is-active=active): re-key exit={r.returncode} decrypt+encrypt starts={sum(1 for x in log if x.startswith('SYSTEMCTL-STUB start'))}; timer queries: {timer_queries}")
