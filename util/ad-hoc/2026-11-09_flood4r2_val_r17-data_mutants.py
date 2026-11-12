"""
Apply one of three one-line mutants to a juniper-data tree, run pytest, and restore the file byte-for-byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, Cursor flood-4 round 2)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 ("data: 44 unrun tests"); independent validation of the r17-data-unit-marks carrier

Usage:
  python3 2026-11-09_flood4r2_val_r17-data_mutants.py --tree T --python P --mutant M1|M2|M3 --log F -- <pytest args>

M1  juniper_data/api/security.py   APIKeyAuth.__init__ keeps blank keys (drops ``and k.strip()``)
M2  juniper_data/api/security.py   RateLimiter._get_key's no-client fallback ``"unknown"`` -> ``"none"``
M3  juniper_data/api/settings.py   Settings._parse_api_keys' list branch stops filtering (``cleaned = list(v)``)

Each mutant's ``old`` text must occur exactly once. The file is restored in ``finally`` and its sha256
re-checked against the pre-mutation digest; a mismatch exits 3.
"""

import argparse
import hashlib
import os
import subprocess  # nosec B404 - runs pytest with a caller-chosen interpreter
import sys
from pathlib import Path

MUTANTS = {
    "M1": (
        "juniper_data/api/security.py",
        "if isinstance(k, str) and k.strip()))",
        "if isinstance(k, str)))",
    ),
    "M2": (
        "juniper_data/api/security.py",
        'client_ip = request.client.host if request.client else "unknown"',
        'client_ip = request.client.host if request.client else "none"',
    ),
    "M3": (
        "juniper_data/api/settings.py",
        "cleaned = [k.strip() if isinstance(k, str) else k for k in v if not isinstance(k, str) or k.strip()]",
        "cleaned = list(v)",
    ),
}


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--")
    parser = argparse.ArgumentParser(description="one-line mutant runner")
    parser.add_argument("--tree", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--mutant", required=True, choices=sorted(MUTANTS))
    parser.add_argument("--log", required=True)
    args = parser.parse_args(argv[:split])
    pytest_args = argv[split + 1 :]
    rel, old, new = MUTANTS[args.mutant]
    target = Path(args.tree).resolve() / rel
    original = target.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    if text.count(old) != 1:
        print(f"{args.mutant}: old text occurs {text.count(old)} times in {rel}; refusing")
        return 2
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        cmd = [args.python, "-m", "pytest", "-p", "no:cacheprovider", "-rf", *pytest_args]
        with open(args.log, "w", encoding="utf-8") as log:
            proc = subprocess.run(cmd, cwd=Path(args.tree).resolve(), env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
        rc = proc.returncode
    finally:
        target.write_bytes(original)
    restored = hashlib.sha256(target.read_bytes()).hexdigest() == digest
    summary = ""
    failed: list[str] = []
    for line in Path(args.log).read_text(encoding="utf-8").splitlines():
        if (" passed" in line or " failed" in line) and " in " in line:
            summary = line.strip("= ").strip()
        if line.startswith("FAILED "):
            failed.append(line.split()[1])
    print(f"{args.mutant}: pytest exit={rc} summary={summary!r} failed={len(failed)} restored={restored}")
    for name in failed:
        print(f"    FAILED {name}")
    return 0 if restored else 3


if __name__ == "__main__":
    sys.exit(main())
