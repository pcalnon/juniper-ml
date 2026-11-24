"""
Freeze a landed tree's carrier files for the sequence-safety probe: paths.txt, snapshot/ and plan.json (read-only on the tree).

The probe (util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py) builds its commit from main's tree with the
snapshot's paths applied. This copies, from --tree, every path named in --paths (one per line) into <out>/snapshot/,
writes ``add <path>`` per line to <out>/paths.txt, and records the main the tree was landed on in <out>/plan.json,
with the sha256 of every copied file so the freeze can be compared with the tree later.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads the directory this writes)

Usage:
    python3 <this file> --tree <landed tree> --paths <paths file> --main-sha <sha> --out <freeze dir>
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--paths", required=True)
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    tree, out = Path(args.tree), Path(args.out)
    if out.exists():
        raise SystemExit("%s exists: use a new freeze directory" % out)
    paths = [line.strip() for line in Path(args.paths).read_text(encoding="utf-8").splitlines() if line.strip()]
    hashes = {}
    for rel in paths:
        source = tree / rel
        if not source.is_file():
            raise SystemExit("not a file in the tree: %s" % rel)
        target = out / "snapshot" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
    (out / "paths.txt").write_text("".join("add %s\n" % rel for rel in paths), encoding="utf-8")
    (out / "plan.json").write_text(json.dumps({"main_sha": args.main_sha, "tree": str(tree), "files": hashes}, indent=1) + "\n", encoding="utf-8")
    print("froze %d files from %s on %s into %s" % (len(paths), tree, args.main_sha[:8], out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
