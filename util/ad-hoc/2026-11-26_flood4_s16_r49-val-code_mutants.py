"""
Apply the r49 code lens's mutants one at a time to a COPY of a juniper-canopy tree, run the chosen tests through the
lens's fenced launcher, and restore every mutated file byte for byte (sha256 checked) before the next mutant.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26), a follow-up of ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16, code lens
    r49-val-code; launcher util/ad-hoc/2026-11-26_flood4_s16_r49-val-code_run.py

Usage:
    python <this file> --adhoc <util/ad-hoc dir> --python <venv python> --tree <tree COPY> --out <dir> --spec <json>
        --set <name> [--ids M1,M2] [--repeat N] [--label-prefix P]

The spec is a JSON object: {"mutants": [{"id", "what", "file" (tree-relative), "edits": [{"old", "new"}]}],
"sets": {"<name>": {"targets": [...], "repeat": N, "stall": ..., "at": ..., "mech": ...}}}. Each edit's old text
must occur exactly once in the file as it stands when that edit is applied (edits apply in order); otherwise the
mutant is reported as not applied and nothing runs. The file is restored from the bytes read before the first edit,
in a finally, and its sha256 compared; the compiled caches of the mutated module are removed before and after each
run, so a cached byte-code file can never stand in for the source. Results: <out>/<prefix>mutants.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs the lane launcher under a chosen interpreter
import sys
import time
from pathlib import Path

LAUNCHER = "2026-11-26_flood4_s16_r49-val-code_run.py"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _drop_pyc(path: Path) -> list[str]:
    removed = []
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        for pyc in cache.glob(path.stem + ".*.pyc"):
            pyc.unlink()
            removed.append(pyc.name)
    return removed


def _apply(text: str, edits: list[dict]) -> tuple[str | None, str | None]:
    for number, edit in enumerate(edits):
        count = text.count(edit["old"])
        if count != 1:
            return None, f"edit {number}: old text occurs {count} times"
        text = text.replace(edit["old"], edit["new"], 1)
    return text, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adhoc", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--set", required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--repeat", default="")
    parser.add_argument("--label-prefix", default="")
    args = parser.parse_args()

    adhoc, tree, out = Path(args.adhoc).resolve(), Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with open(args.spec, encoding="utf-8") as handle:
        spec = json.load(handle)
    chosen = spec["sets"][args.set]
    wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
    results = []
    for mutant in spec["mutants"]:
        if wanted and mutant["id"] not in wanted:
            continue
        path = tree / mutant["file"]
        original = path.read_bytes()
        before = _sha(original)
        record = {"id": mutant["id"], "what": mutant["what"], "file": mutant["file"], "set": args.set, "sha256_before": before}
        mutated, problem = _apply(original.decode("utf-8"), mutant["edits"])
        if mutated is None:
            record.update({"applied": False, "problem": problem})
            results.append(record)
            print(json.dumps(record), flush=True)
            continue
        label = f"{args.label_prefix}{mutant['id']}_{args.set}"
        repeat = args.repeat or str(chosen.get("repeat", 1))
        command = [sys.executable, str(adhoc / LAUNCHER), "--adhoc", str(adhoc), "--python", args.python, "--tree", str(tree), "--out", str(out), "--label", label, "--repeat", repeat, "--stall", str(chosen.get("stall", "0")), "--at", chosen.get("at", "probe"), "--mech", chosen.get("mech", "gil"), "--", *chosen["targets"]]
        started = time.time()
        try:
            _drop_pyc(path)
            path.write_bytes(mutated.encode("utf-8"))
            record["sha256_mutated"] = _sha(path.read_bytes())
            proc = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv, no shell
        finally:
            path.write_bytes(original)
            record["pyc_removed_after"] = _drop_pyc(path)
        after = _sha(path.read_bytes())
        record.update({"applied": True, "label": label, "repeat": repeat, "exit": proc.returncode, "seconds": round(time.time() - started, 1), "sha256_after": after, "restored": after == before})
        summary = out / f"{label}.summary_r49v.json"
        if summary.exists():
            with open(summary, encoding="utf-8") as handle:
                record["tests"] = [{k: row[k] for k in ("test", "runs", "passed", "failed", "errors", "stub_verdicts")} for row in json.load(handle)]
        with open(out / f"{label}.mutant_stdout.txt", "w", encoding="utf-8") as handle:
            handle.write(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
        results.append(record)
        print(json.dumps({k: record.get(k) for k in ("id", "applied", "exit", "seconds", "restored")} | {"failed_by_test": {t["test"].split("::")[-1]: f"{t['failed']}/{t['runs']}" for t in record.get("tests", [])}}), flush=True)
        if not record["restored"]:
            print("RESTORE FAILED -- stopping", flush=True)
            break
    target = out / f"{args.label_prefix}{args.set}_mutants.json"
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1)
    return 0 if all(r.get("restored", True) for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
