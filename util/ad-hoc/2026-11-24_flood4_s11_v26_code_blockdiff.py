#!/usr/bin/env python3
"""Compare each ruling-26 port's frozen lockfile-update.yml with its main and with canopy main's block (V26 CODE lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens); juniper-canopy#814 (the model fix);
    notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 26)

For every --pair NAME MAIN FROZEN it reports, read-only:
  1. the raw text diff main -> frozen (zero context), split into banner hunks (the header's Version / Last Modified)
     and body hunks;
  2. whether the parsed YAML is identical once the commit step's `run` is set aside (step names, if, env, shell,
     every other step, triggers, permissions);
  3. the commit step's facts: name, `shell` (absent = the runner default `bash -e {0}`), env keys, first command;
  4. that the frozen `run` equals main's outside one region: main's bare `gh api graphql` line through the end of its
     `.errors` if-block, replaced by the fix block (prefix and suffix compared byte for byte);
  5. the fix block against canopy main's (from the "`gh api graphql` exits 1, not 0" comment to the line before the
     `Signed lockfile commit` print), as a unified diff;
  6. every system-temp path the step names and every redirect target (`>`/`>>`), main vs frozen.
Writes the report to --out and prints it. Exit 0 when every pair has a single body region, identical YAML outside
the run, identical prefix/suffix and a block that differs from canopy's only by added comment lines; 1 otherwise.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import re
import sys
from pathlib import Path
from typing import Any

import yaml

BLOCK_START = "# `gh api graphql` exits 1, not 0"
SUCCESS_PRINT = "jq -r '\"Signed lockfile commit: \""
BANNER_KEYS = ("# Version:", "# Last Modified:")
TEMP_PATH = re.compile(r"(?<![\w.])/(?:var/)?tmp/[^\s\"';)|&]*")
REDIRECT = re.compile(r"(?<![0-9&])(>>?)\s*([^\s;&|)]+)")


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))
    return data


def _commit_step(data: dict[str, Any]) -> tuple[str, int, dict[str, Any]]:
    for job_name, job in data["jobs"].items():
        for index, step in enumerate(job.get("steps", [])):
            if str(step.get("name", "")).startswith("Commit updated lockfile"):
                return job_name, index, step
    raise SystemExit("no commit step found")


def _block(run: str) -> list[str]:
    lines = run.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().startswith(BLOCK_START)]
    ends = [i for i, line in enumerate(lines) if line.strip().startswith(SUCCESS_PRINT)]
    if len(starts) != 1 or len(ends) != 1:
        return []
    block = lines[starts[0] : ends[0]]
    while block and not block[-1].strip():
        block.pop()
    return block


def _main_region(run: str) -> tuple[int, int] | None:
    """Line span of main's bare gh call through the `fi` closing its `.errors` check."""
    lines = run.splitlines()
    gh = [i for i, line in enumerate(lines) if line.strip().startswith("gh api graphql --input")]
    if len(gh) != 1:
        return None
    start = gh[0]
    errors_if = next((i for i in range(start, len(lines)) if lines[i].strip().startswith("if jq -e '.errors'")), None)
    if errors_if is None:
        return None
    end = next((i for i in range(errors_if, len(lines)) if lines[i].strip() == "fi"), None)
    if end is None:
        return None
    return start, end


def _frozen_region(run: str) -> tuple[int, int] | None:
    lines = run.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().startswith(BLOCK_START)]
    ends = [i for i, line in enumerate(lines) if line.strip().startswith(SUCCESS_PRINT)]
    if len(starts) != 1 or len(ends) != 1:
        return None
    end = ends[0] - 1
    while end > starts[0] and not lines[end].strip():
        end -= 1
    return starts[0], end


def _pair(name: str, main_path: Path, frozen_path: Path, canopy_block: list[str]) -> tuple[list[str], bool]:
    out: list[str] = [f"=== {name} ===", f"  main   {main_path}", f"  frozen {frozen_path}"]
    ok = True
    main_text = main_path.read_text(encoding="utf-8")
    frozen_text = frozen_path.read_text(encoding="utf-8")

    # 1. raw hunks
    banner, body = [], []
    matcher = difflib.SequenceMatcher(a=main_text.splitlines(), b=frozen_text.splitlines(), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old = main_text.splitlines()[i1:i2]
        new = frozen_text.splitlines()[j1:j2]
        is_banner = all(any(line.startswith(key) for key in BANNER_KEYS) for line in old + new) and (old or new)
        (banner if is_banner else body).append((tag, i1 + 1, i2, j1 + 1, j2, old, new))
    out.append(f"  1. raw hunks: {len(banner)} banner, {len(body)} body")
    for tag, i1, i2, j1, j2, old, new in banner:
        out.append(f"     banner {tag} main:{i1}-{i2} frozen:{j1}-{j2}: {old} -> {new}")
    for tag, i1, i2, j1, j2, old, new in body:
        out.append(f"     body {tag} main:{i1}-{i2} ({len(old)} lines) -> frozen:{j1}-{j2} ({len(new)} lines)")
    if len(body) < 1:
        ok = False

    # 2. YAML outside the run
    main_data, frozen_data = _load(main_path), _load(frozen_path)
    m_job, m_idx, m_step = _commit_step(main_data)
    f_job, f_idx, f_step = _commit_step(frozen_data)
    m_copy, f_copy = copy.deepcopy(main_data), copy.deepcopy(frozen_data)
    m_copy["jobs"][m_job]["steps"][m_idx]["run"] = "<run>"
    f_copy["jobs"][f_job]["steps"][f_idx]["run"] = "<run>"
    same_yaml = m_copy == f_copy
    out.append(f"  2. parsed YAML identical outside the commit step's run: {same_yaml}")
    ok &= same_yaml
    last = m_idx == len(main_data["jobs"][m_job]["steps"]) - 1
    out.append(f"     commit step is the job's last step: {last} (job {m_job!r}, step index {m_idx})")

    # 3. step facts
    first_cmd = next(line for line in f_step["run"].splitlines() if line.strip() and not line.strip().startswith("#"))
    out.append(f"  3. step name {f_step['name']!r}; shell {f_step.get('shell', '<absent: runner default bash -e {0}>')!r}; env keys {sorted(f_step.get('env', {}))}; first command {first_cmd.strip()!r}")
    out.append(f"     env: {f_step.get('env')}")

    # 4. prefix/suffix identity
    m_run, f_run = m_step["run"], f_step["run"]
    m_lines, f_lines = m_run.splitlines(), f_run.splitlines()
    m_reg, f_reg = _main_region(m_run), _frozen_region(f_run)
    if m_reg is None or f_reg is None:
        out.append(f"  4. could not locate the regions: main {m_reg}, frozen {f_reg}")
        ok = False
    else:
        prefix_same = m_lines[: m_reg[0]] == f_lines[: f_reg[0]]
        suffix_same = m_lines[m_reg[1] + 1 :] == f_lines[f_reg[1] + 1 :]
        out.append(f"  4. run prefix identical: {prefix_same} ({m_reg[0]} lines); run suffix identical: {suffix_same} ({len(m_lines) - m_reg[1] - 1} lines)")
        out.append(f"     main region run-lines {m_reg[0] + 1}-{m_reg[1] + 1}:")
        out.extend(f"       - {line}" for line in m_lines[m_reg[0] : m_reg[1] + 1])
        out.append(f"     suffix (unchanged success print): {[line.strip() for line in f_lines[f_reg[1] + 1 :] if line.strip()]}")
        ok &= prefix_same and suffix_same

    # 5. block vs canopy
    block = _block(f_run)
    diff = list(difflib.unified_diff(canopy_block, block, "canopy-main-block", f"{name}-frozen-block", n=0, lineterm=""))
    added = [line for line in diff if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in diff if line.startswith("-") and not line.startswith("---")]
    only_comments_added = not removed and all(line[1:].strip().startswith("#") for line in added)
    out.append(f"  5. block vs canopy main: canopy {len(canopy_block)} lines, port {len(block)} lines; removed {len(removed)}, added {len(added)}; only comment lines added: {only_comments_added}")
    out.extend(f"     {line}" for line in diff)
    ok &= only_comments_added

    # 6. paths and redirects
    for label, run in (("main", m_run), ("frozen", f_run)):
        code = "\n".join(line for line in run.splitlines() if not line.strip().startswith("#"))
        temps = sorted(set(TEMP_PATH.findall(code)))
        redirects = sorted({f"{op} {target}" for op, target in REDIRECT.findall(code)})
        out.append(f"  6. {label}: temp paths {temps}; redirect targets {redirects}")
    return out, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--canopy", type=Path, required=True, help="canopy main's lockfile-update.yml")
    parser.add_argument("--pair", nargs=3, action="append", metavar=("NAME", "MAIN", "FROZEN"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    canopy_data = _load(args.canopy)
    _job, _idx, canopy_step = _commit_step(canopy_data)
    canopy_block = _block(canopy_step["run"])
    lines = [f"canopy main block: {len(canopy_block)} lines from {args.canopy}"]
    all_ok = bool(canopy_block)
    for name, main_path, frozen_path in args.pair:
        report, ok = _pair(name, Path(main_path), Path(frozen_path), canopy_block)
        lines.extend(report)
        lines.append(f"  RESULT {name}: {'OK' if ok else 'CHECK'}")
        all_ok &= ok
    text = "\n".join(lines) + "\n"
    args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
