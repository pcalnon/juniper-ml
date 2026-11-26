"""
Mutants of the r28 carrier's test HARNESS (the _HeldCall in juniper-canopy's test_x7_sites_outside_main_gate.py), alone
and combined with a code mutant, against the carrier's file and against the lens's proposed fix (a second control).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code; fixes in S/tmp/flood4/session14/r28-val-code/fixes.json

Usage:
    python <this file> --python <venv python> --tree <assembled tree copy> --fixes <fixes.json> --out <dir>

Variants of the test file: "carrier" (as shipped) and "fixed" (the carrier with every fixes.json entry for that file
applied). Harness mutants: H1 the releaser no longer waits for the call to enter (it releases at once); H2 the release
verdict is always True; H3 the thread verdict is always False. Each is run alone and with code mutant R2 (the relay
offloads extract_network_topology, then blocks the loop on its result). Every file is restored byte for byte in a
`finally:` (sha256 before == after, else the script stops).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs the lens's own runner
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "2026-11-25_flood4_s14_r28-val-code_run.py"
SUMMARY = HERE / "2026-11-25_flood4_s14_r28-val-code_summarize.py"
TEST = "src/tests/regression/test_x7_sites_outside_main_gate.py"
ADAPTER = "src/backend/cascor_service_adapter.py"
R2 = ("topology = await asyncio.to_thread(self.extract_network_topology)", 'topology = __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=1).submit(self.extract_network_topology).result()')
HARNESS = {
    "H0": [],
    "H1": [("        await self._entered.wait()\n        self._release.set()\n", "        self._release.set()\n")],
    "H2": [("        self.released_by_loop = self._release.wait(timeout=self.hold_seconds)\n", "        self._release.wait(timeout=self.hold_seconds)\n        self.released_by_loop = True\n")],
    "H3": [("        self.ran_on_loop_thread = threading.get_ident() == self._loop_thread\n", "        self.ran_on_loop_thread = False\n")],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"replacement text occurs {text.count(old)} times: {old[:60]!r}")
    return text.replace(old, new)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--fixes", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    tree, out = Path(args.tree), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    test_path, code_path = tree / TEST, tree / ADAPTER
    test_text, code_text = test_path.read_text(encoding="utf-8"), code_path.read_text(encoding="utf-8")
    test_sha, code_sha = sha256(test_path), sha256(code_path)
    fixed_text = test_text
    for fix in json.loads(Path(args.fixes).read_text(encoding="utf-8")):
        if fix["file"] == TEST:
            fixed_text = replace_once(fixed_text, fix["old"], fix["new"])
    results = []
    try:
        for variant, base in (("carrier", test_text), ("fixed", fixed_text)):
            for hid, edits in HARNESS.items():
                for code in ("clean", "R2"):
                    text = base
                    for old, new in edits:
                        text = replace_once(text, old, new)
                    test_path.write_text(text, encoding="utf-8")
                    code_path.write_text(replace_once(code_text, *R2) if code == "R2" else code_text, encoding="utf-8")
                    label = f"{variant}_{hid}_{code}"
                    subprocess.run([sys.executable, str(RUNNER), "--python", args.python, "--tree", str(tree), "--out", str(out), "--label", label, "--no-cov", "--no-maxfail", "--", TEST], check=False, capture_output=True, text=True)  # nosec B603
                    summary = subprocess.run([sys.executable, str(SUMMARY), str(out), label], check=False, capture_output=True, text=True)  # nosec B603
                    row = json.loads(summary.stdout.strip().splitlines()[-1])
                    brief = {"label": label, "variant": variant, "harness": hid, "code": code, "per_test": row.get("per_test"), "junit": row.get("junit")}
                    results.append(brief)
                    print(json.dumps(brief), flush=True)
    finally:
        test_path.write_text(test_text, encoding="utf-8")
        code_path.write_text(code_text, encoding="utf-8")
    restored = {"test_sha256_before": test_sha, "test_sha256_after": sha256(test_path), "code_sha256_before": code_sha, "code_sha256_after": sha256(code_path)}
    restored["restored_byte_for_byte"] = restored["test_sha256_before"] == restored["test_sha256_after"] and restored["code_sha256_before"] == restored["code_sha256_after"]
    (out / "harness_mutants.json").write_text(json.dumps({"results": results, "restore": restored}, indent=1), encoding="utf-8")
    print(json.dumps(restored), flush=True)
    return 0 if restored["restored_byte_for_byte"] else 2


if __name__ == "__main__":
    sys.exit(main())
