#!/usr/bin/env python3
"""Lane B: mutants of head's II.11 toy beyond the six in 2026-09-24_primer_toy_pin_mutation_check.py.

Each mutant rewrites whole lines of head's primer (no line moves), runs the Appendix D harness, and also
runs the fix-forward's own error-paths probe, reporting CAUGHT / MISSED for each instrument.

Usage: python3 extra_mutants.py <venv>
"""
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
PRIMER = S / "head/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
HARNESS = S / "head/util/ad-hoc/2026-08-13_run_primer_examples.py"
PROBE = S / "head/util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py"
VENV = sys.argv[1]

L5498 = '    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)  # Python\'s JSON parser accepts NaN and Infinity: refuse them as a 422'
MUTANTS = {
    "lax int|float (strictness reverted)": {5502: "    params: dict[str, int | float] = Field(default_factory=dict)"},
    "lax float only": {5502: "    params: dict[str, float] = Field(default_factory=dict)"},
    "allow_inf_nan dropped only": {5498: '    model_config = ConfigDict(extra="forbid")'},
    "params Any, allow_inf_nan kept": {5502: "    params: dict[str, Any] = Field(default_factory=dict)"},
    "echo reverted only": {5631: "            errors=json.loads(json.dumps(exc.errors(), default=str)),"},
    "StrictFloat only": {5502: "    params: dict[str, StrictFloat] = Field(default_factory=dict)"},
    "n_samples truncation kept, but create ETag over unsorted json": {
        5672: "            __import__('json').dumps(dataset.metadata()), media_type=\"application/json\","
    },
}


def harness(doc: Path) -> tuple[bool, str]:
    p = subprocess.run([sys.executable, str(HARNESS), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True)
    tail = [ln for ln in p.stdout.split("\n") if " passed" in ln or " failed" in ln]
    return p.returncode == 0, (tail[-1].strip() if tail else f"exit {p.returncode}: {p.stderr.strip()[-200:]}")


def probe(doc: Path) -> tuple[bool, str]:
    p = subprocess.run([f"{VENV}/bin/python", str(PROBE), str(doc)], capture_output=True, text=True)
    last = [ln for ln in p.stdout.split("\n") if ln.startswith("RESULT")]
    return p.returncode == 0, (last[-1] if last else f"exit {p.returncode}")


def main() -> int:
    base = PRIMER.read_text(encoding="utf-8").split("\n")
    assert base[5498 - 1] == L5498, base[5498 - 1]
    ok, tail = harness(PRIMER)
    print(f"control: harness {'PASS' if ok else 'FAIL'} ({tail})")
    out = S / "mutants"
    out.mkdir(exist_ok=True)
    for name, edits in MUTANTS.items():
        lines = list(base)
        for n, text in edits.items():
            lines[n - 1] = text
        doc = out / ("m_" + "".join(c if c.isalnum() else "_" for c in name)[:40] + ".md")
        doc.write_text("\n".join(lines), encoding="utf-8")
        h_ok, h_tail = harness(doc)
        p_ok, p_tail = probe(doc)
        print(f"{name:62} harness {'MISSED' if h_ok else 'CAUGHT'} ({h_tail}); probe {'MISSED' if p_ok else 'CAUGHT'} ({p_tail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
