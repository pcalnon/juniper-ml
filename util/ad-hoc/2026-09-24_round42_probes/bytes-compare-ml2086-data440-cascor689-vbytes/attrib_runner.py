"""Run each main-importing cascor test file in its own pytest process with a LOCAL DSN, and attribute
the envelopes the sink receives to the file that produced them.

python attrib_runner.py <cascor root> <sink.jsonl> <port>
"""

import json
import os
import subprocess
import sys
import time

root, sink, port = sys.argv[1], sys.argv[2], sys.argv[3]
files = [
    "src/tests/unit/test_cfg_03_sentry_dsn_resolution.py",
    "src/tests/unit/test_main_coverage.py",
    "src/tests/unit/test_import_hygiene_568.py",
    "src/tests/unit/api/test_allow_truncated_datasets.py",
    "src/tests/unit/api/test_auto_start_shortfall.py",
    "src/tests/unit/test_fp13_direct_cli_termination.py",
    "src/tests/unit/test_l1_spiral_output_epochs_budget.py",
    "src/tests/unit/test_main_profiling_coverage.py",
    "src/tests/unit/test_w11_cli_yaml_mapping.py",
]
env = {k: v for k, v in os.environ.items() if "DSN" not in k and k != "JUNIPER_CASCOR_LOG_DIR"}
env["SENTRY_SDK_DSN"] = f"http://public@127.0.0.1:{port}/1"
env["PYTHONDONTWRITEBYTECODE"] = "1"
assert all("DSN" not in k or env[k].startswith("http://public@127.0.0.1:") for k in env)


def lines():
    with open(sink) as fh:
        return [json.loads(line) for line in fh if line.strip()]


for f in files:
    before = len(lines())
    proc = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-m", "unit and not slow", f], cwd=root, env=env, capture_output=True, text=True)
    time.sleep(1.0)
    new = lines()[before:]
    summary = (proc.stdout.strip().splitlines() or ["?"])[-1]
    kinds = {}
    for rec in new:
        for t in rec["types"]:
            kinds[t] = kinds.get(t, 0) + 1
    print(f"{f.rsplit('/', 1)[-1]:44} rc={proc.returncode} posts={len(new):3} items={kinds}  [{summary[:60]}]")
    seen = set()
    for rec in new:
        for d in rec.get("details", []):
            key = (d["exc"], d["logger"])
            if key not in seen:
                seen.add(key)
                print(f"      event: {d['exc']} | logger={d['logger']} | msg={d['msg']}")
