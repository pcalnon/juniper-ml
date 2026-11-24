"""
Compare the ruling-10 port's two new Security Scans steps with juniper-data's on its current main, byte for byte.

For each of the two steps it compares the parsed ``run:`` string and the raw YAML source lines of the block, then the
step's other keys, and writes each ``run:`` block to a file (for shellcheck) plus a unified diff of the two jobs.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_compare_run_blocks.py <carrier ci.yml> <juniper-data ci.yml> <out dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import difflib
import hashlib
import json
import sys
from pathlib import Path

import yaml

STEPS = ["Install Gitleaks (pull request)", "Run Gitleaks over the pull request (Secrets Detection)"]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def security_job(path: Path) -> tuple[str, dict]:
    """The id and body of the job that holds the gitleaks action step."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for job_id, job in data["jobs"].items():
        if any(str(step.get("uses", "")).startswith("gitleaks/gitleaks-action@") for step in job.get("steps", [])):
            return job_id, job
    raise SystemExit(f"{path}: no job runs gitleaks/gitleaks-action")


def raw_run_block(path: Path, step_name: str) -> list[str]:
    """The source lines under the step's ``run: |``, with the block's own indentation removed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {step_name}")
    run_at = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "run: |")
    key_indent = len(lines[run_at]) - len(lines[run_at].lstrip())
    block = []
    for line in lines[run_at + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= key_indent:
            break
        block.append(line)
    while block and not block[-1].strip():
        block.pop()
    indent = min(len(line) - len(line.lstrip()) for line in block if line.strip())
    return [line[indent:] if line.strip() else "" for line in block]


def job_source(path: Path, job_id: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {job_id}:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  ") and not lines[i].startswith("   ") and lines[i].rstrip().endswith(":") and not lines[i].lstrip().startswith("#")), len(lines))
    return lines[start:end]


def main() -> int:
    carrier, data, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    carrier_id, carrier_job = security_job(carrier)
    data_id, data_job = security_job(data)
    report: dict = {"carrier_job": carrier_id, "data_job": data_id, "steps": {}}
    for name in STEPS:
        ours = next(step for step in carrier_job["steps"] if step.get("name") == name)
        theirs = next(step for step in data_job["steps"] if step.get("name") == name)
        ours_raw, theirs_raw = raw_run_block(carrier, name), raw_run_block(data, name)
        slug = "install" if name.startswith("Install") else "scan"
        (out / f"{slug}_carrier.sh").write_text(str(ours["run"]), encoding="utf-8")
        (out / f"{slug}_data.sh").write_text(str(theirs["run"]), encoding="utf-8")
        report["steps"][name] = {
            "parsed_run_equal": ours["run"] == theirs["run"],
            "parsed_run_sha256": {"carrier": digest(str(ours["run"])), "data": digest(str(theirs["run"]))},
            "parsed_run_bytes": {"carrier": len(str(ours["run"]).encode("utf-8")), "data": len(str(theirs["run"]).encode("utf-8"))},
            "raw_block_equal": ours_raw == theirs_raw,
            "raw_block_lines": {"carrier": len(ours_raw), "data": len(theirs_raw)},
            "other_keys_equal": {key: ours.get(key) == theirs.get(key) for key in sorted((set(ours) | set(theirs)) - {"run"})},
            "other_keys": {"carrier": {k: v for k, v in ours.items() if k != "run"}, "data": {k: v for k, v in theirs.items() if k != "run"}},
        }
    report["step_names"] = {"carrier": [step.get("name") for step in carrier_job["steps"]], "data": [step.get("name") for step in data_job["steps"]]}
    report["job_keys"] = {"carrier": {k: v for k, v in carrier_job.items() if k != "steps"}, "data": {k: v for k, v in data_job.items() if k != "steps"}}
    diff = difflib.unified_diff(job_source(data, data_id), job_source(carrier, carrier_id), "juniper-data ci.yml (job)", "carrier ci.yml (job)", lineterm="", n=2)
    (out / "job_data_vs_carrier.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")
    with open(out / "compare_run_blocks.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
        fh.write("\n")
    print(json.dumps(report, indent=2, default=str))
    return 0 if all(step["parsed_run_equal"] and step["raw_block_equal"] for step in report["steps"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
