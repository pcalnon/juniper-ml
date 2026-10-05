#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — one-off; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Copy the Phase 10 round-1 lanes' probe scripts out of this session's tmpfs scratchpad into ``util/ad-hoc/``.

The ledger's Phase 10 cites executions those lanes ran (F-CANOPY-064's tile with cascor's real
``TrainingMonitor``, F-CANOPY-065 through the real ``apply_params`` and toast, F-CANOPY-067 through the real
relay loop and browser bridge, F-CANOPY-060 with the real error classes, and each instrument's mutation). The
scratchpad is tmpfs, which a reboot deletes, so the scripts are copied here with a provenance header, the
file's content otherwise unchanged. A file holding a secret shape or an e-mail address (other than a
``noreply`` one) is refused, and the run stops before writing anything.

Targets are ``util/ad-hoc/2026-10-04_phase10_r1_<lane>_<name>``. Paths and ports inside are the lane's own.

Usage:
    python3 util/ad-hoc/2026-10-04_archive_phase10_lane_probes.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad")
OUT = Path(__file__).resolve().parent
LANES = {
    "a2": ("lane10A2.g5NzBN", "Lane 10-A2 (evidence and instruments)", ["c1_timeline.py", "c3_captures.py", "crop.py", "f060_mutation_wrapper.py", "mutate.py", "my_f060_stage_a.py", "my_f060_stage_b.py", "my_o2.py", "my_o2_burst_panel.py", "my_o2_initial_burst.py", "my_o3.py", "o4_meta.py"]),
    "b1": ("lane10B1.8nGM", "Lane 10-B1 (adversarial, dispositions and ratings)", ["crop.py", "meta_check.py", "o2_window_probe.py", "triage.py"]),
    "b2": ("lane10B2.eZmWfY", "Lane 10-B2 (adversarial, claims beyond evidence)", ["check_lines.py", "crop.py", "extend_traces_fn.js", "inspect_hist.py", "inspect_hist2.py", "probe_bridge.js", "probe_o4.py", "probe_relay.py", "probe_toast.py"]),
}
SECRET = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}|AGE-SECRET-KEY-|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def header(lane_label: str, src: Path, comment: str) -> str:
    lines = [
        "ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.",
        f"Source: this session's tmpfs scratchpad, {src.parent.name}/{src.name}",
        f"Written by {lane_label}, a review lane (a subagent), not by the orchestrator.",
        "Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon",
        "Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)",
        "Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;",
        "  reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md",
        "Everything below this block is the lane's file, unmodified.",
    ]
    bar = comment + " " + "-" * 75
    return "\n".join([bar] + [f"{comment} {x}" for x in lines] + [bar]) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    plan, refused = [], []
    for lane, (dirname, label, files) in LANES.items():
        for name in files:
            src = SCRATCH / dirname / name
            text = src.read_text(encoding="utf-8")
            emails = [e for e in EMAIL.findall(text) if "noreply" not in e]
            if SECRET.search(text) or emails:
                refused.append(f"{dirname}/{name}")
                continue
            comment = "//" if name.endswith(".js") else "#"
            body = text
            shebang = ""
            if body.startswith("#!"):
                shebang, body = body.split("\n", 1)
                shebang += "\n"
            plan.append((OUT / f"2026-10-04_phase10_r1_{lane}_{name}", shebang + header(label, src, comment) + body))
    if refused:
        print("REFUSED (secret shape or e-mail address):", ", ".join(refused), file=sys.stderr)
        return 1
    for dst, content in plan:
        if dst.exists():
            print(f"REFUSED: {dst.name} exists", file=sys.stderr)
            return 1
    for dst, content in plan:
        print(("would write " if args.dry_run else "wrote ") + str(dst.relative_to(OUT.parents[1])))
        if not args.dry_run:
            dst.write_text(content, encoding="utf-8")
    print(f"{len(plan)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
