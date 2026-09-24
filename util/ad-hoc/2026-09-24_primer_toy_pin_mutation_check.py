#!/usr/bin/env python3
"""
Show that the primer's own example harness now catches a revert of the II.11 toy's ETag fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling (API primer correction, v3)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- read-only mutation check; writes mutated copies to a scratch directory only
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

v2 of the primer correction (juniper-ml#2075) made the II.11 toy's four metadata responses send exactly
the canonical bytes their strong `ETag` hashes. Round 2 of its validation found that nothing in the
Appendix D harness pinned that: reverting GET, PATCH or POST-reuse to `JSONResponse` still passed 62/62
(`primer-correction-round2-laneB-refute.md`, L-5). v3 adds same-line assertions to the example's own tests
(lines 5838, 5857 and 5945, with `import hashlib` on the formerly blank line 5791).

This reverts each route in a scratch copy of the primer and runs the Appendix D harness
(util/ad-hoc/2026-08-13_run_primer_examples.py) on it. Each mutant must FAIL; the unmutated primer is the
control and must pass.

Extended the same day by the second round-42 fix-forward. The post-merge validation of v3
(reports/2026-09-24_defect-register-round-42/ml2080-round1-laneA-reprobe.md M1,
ml2080-round1-laneB-refute.md M1) reverted the fourth route, POST create (lines 5671-5672), and the
harness still passed 62/62: line 5838 hashed only the second, 200, response's body, so the "each" in
Appendix E was false. Line 5838 now hashes the 201's own body too, and the "POST create" mutant below pins
it. The two "NaN" mutants pin that fix-forward's other toy change (lane B, L4): the NaN refusal (lines
5400, 5498, 5502) and a 422 handler that can echo the refused NaN (line 5631), both caught by the NaN arm
of the validation-shape test (lines 6119-6120). They pin the NaN refusal only.

Not every mutant is a revert. The "lax union", "admit bool" and "admit None" mutants are VARIANTS: line 5502
never read any of them (it was `dict[str, Any]` on main and `StrictInt | StrictFloat` since the fix-forward),
so they test that the suite refuses a plausible wrong fix, not that it notices the old code. Round 2 of the
fix-forward's pre-PR validation (register-fixforward2-round2-laneA-reprobe.md N6,
register-fixforward2-round2-laneB-refute.md N3 and L5) found this file calling the lax union a revert, and
found `true` and `null` pinned only by the external probe. The suite now has arms for both (lines 6117-6118,
on `seed`, so the n_samples bound cannot be what refuses them), and the two variants below pin them.

The same round's other fixes are reverts, each pinned in the suite: the `n_samples` bound (lines 5658-5659,
caught by the fraction arm on 6118), the ASCII-escaped problem body (line 5464, with 5399's import restored
so the revert runs, caught by the lone-surrogate arm on 6119), and the deep-cursor catch (line 5600, caught by
the 15,000-deep arm on 6084). The list route's rendering (5682, 5699) is pinned by
util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py only: a same-line arm would have to store a tag and
list in one expression.

Usage: python3 util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py --venv <venv with the Appendix D pins> --scratch <dir>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRIMER = REPO / "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
HARNESS = REPO / "util/ad-hoc/2026-08-13_run_primer_examples.py"

# mutant -> {line: text}. A revert puts back the text the line held before the fix it pins; a variant (marked)
# puts in a plausible wrong fix the line never held. Each must fail the harness.
MUTANTS = {
    "GET": {5722: "        return JSONResponse(dataset.metadata(), headers=headers)"},
    "PATCH": {5773: "        return JSONResponse(", 5774: "            dataset.metadata(),"},
    "POST reuse": {5653: "            return JSONResponse(", 5654: "                existing.metadata(),"},
    "POST create": {5671: "        return JSONResponse(", 5672: "            dataset.metadata(),"},
    "NaN schema": {
        5400: "from pydantic import BaseModel, ConfigDict, Field",
        5498: '    model_config = ConfigDict(extra="forbid")',
        5502: "    params: dict[str, Any] = Field(default_factory=dict)",
    },
    "NaN echo": {5631: "            errors=json.loads(json.dumps(exc.errors(), default=str)),"},
    "n_samples bound": {5658: "", 5659: '        n_samples = int(body.params.get("n_samples", 512))'},
    "problem rendering": {
        5399: "from fastapi.responses import JSONResponse, Response",
        5464: "        return JSONResponse(body, status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)",
    },
    "deep cursor": {5600: "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:"},
    "lax union (variant)": {5502: "    params: dict[str, int | float] = Field(default_factory=dict)"},
    "admit bool (variant)": {5502: "    params: dict[str, StrictInt | StrictFloat | bool] = Field(default_factory=dict)"},
    "admit None (variant)": {5502: "    params: dict[str, StrictInt | StrictFloat | None] = Field(default_factory=dict)"},
}


def run(doc: Path, venv: str) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, str(HARNESS), "--doc", str(doc), "--venv", venv], capture_output=True, text=True)
    tail = [line for line in proc.stdout.split("\n") if " passed" in line or " failed" in line]
    return proc.returncode == 0, (tail[-1].strip() if tail else f"exit {proc.returncode}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--venv", required=True)
    ap.add_argument("--scratch", required=True, type=Path)
    args = ap.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    base = PRIMER.read_text(encoding="utf-8").split("\n")

    ok, tail = run(PRIMER, args.venv)
    print(f"  control (unmutated): {'PASS' if ok else 'FAIL'} -- {tail}")
    bad = not ok
    for name, edits in MUTANTS.items():
        lines = list(base)
        for lineno, text in edits.items():
            if lines[lineno - 1] == text:
                raise SystemExit(f"line {lineno} already holds the mutant text; the primer is not v2 or later")
            lines[lineno - 1] = text
        doc = args.scratch / f"primer_mutant_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}.md"
        doc.write_text("\n".join(lines), encoding="utf-8")
        ok, tail = run(doc, args.venv)
        print(f"  {name:22} {'CAUGHT' if not ok else 'MISSED'} -- {tail}")
        bad |= ok
    print("RESULT:", f"all {len(MUTANTS)} mutants are caught, and the control passes" if not bad else "a mutant went uncaught, or the control failed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
