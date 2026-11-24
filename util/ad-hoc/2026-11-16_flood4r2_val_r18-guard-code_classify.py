"""
Re-run the differential's UNSAFE and REFUSE->PASS examples through bash and both guards, and label each by the
protected target bash reached, so a validator can see which rule families stay open (validator JL1).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (flood-4 round-2 validation, r18-guard code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-16_flood4r2_val_r18-guard-code_differential.py

Usage: python3 <this file> <scratch dir> <differential json> [<key> ...]
Same hygiene as the differential: printf only, PATH empty, scratch home; the guards judge payloads only.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path


def load_helper(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list) -> int:
    scratch = Path(argv[0]).resolve()
    report = json.loads(Path(argv[1]).read_text())
    keys = argv[2:] or [k for k in report["examples"] if k.startswith(("UNSAFE", "refuse_to_pass_reach", "LOST"))]
    diff = load_helper(Path(__file__).with_name("2026-11-16_flood4r2_val_r18-guard-code_differential.py"), "jl1_diff")
    home = str(scratch / "scratch_home")
    emptybin = str(scratch / "emptybin")
    cwds = {"HOME": home, "REPO": os.path.join(home, "Development", "repo")}
    os.environ.pop("CLAUDE_PROJECT_DIR", None)
    guards = {"main": diff.load(scratch / "work" / "guard_main.py", "jl1_gm"), "new": diff.load(scratch / "work" / "guard_new.py", "jl1_gn")}
    for key in keys:
        print("==", key)
        for ex in report["examples"].get(key, []):
            cwd = cwds[ex["cwd"]]
            word = ex["command"].split(" ", 1)[1] if ex["kind"] == "path" else ex["command"]
            if ex["kind"] == "path":
                rc, words = diff.bash_words(word, home, cwd, emptybin)
                labels = sorted({lab for w in words for lab in diff.protected(w, home, cwd)})
            else:
                labels = [ex["kind"]]
            verdicts = " ".join("%s=%s" % (n, diff.decide(g, ex["command"], home, cwd)[0]) for n, g in guards.items())
            print("  %-10s %-26s %s" % (",".join(labels), verdicts, ex["command"][:150]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
