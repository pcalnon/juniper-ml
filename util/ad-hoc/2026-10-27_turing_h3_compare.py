"""
Compare an H3 agent report's gate verdicts with an independent host probe run (turing bring-up task H3).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-27
Status: ad-hoc — investigation (turing bring-up task H3: the live validation of the three SME agents)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (H3's row; §9.1's I-H3);
         .claude/agents/macos-host-sme.md and .claude/agents/signing-auth-sme.md (the reports it reads);
         util/host_state_check.py (its --probe-json evaluates the independent probe)

Why: H3 accepts an agent's report when it agrees with an independent `util/host_state_probe.bash --json` run
taken within ±10 minutes of the agent's own `probe.collected_at`, with zero contradictions on the gates the
agent covers. This reads both and names every disagreement.

What it compares, per covered gate: the gate's status (pass / fail / error), and the set of its fail and error
condition ids. A gate the report never puts in a row is "missing", never a pass.

How it reads the report: the markdown table rows and list items whose leading text names the gate
(`| G-SEC | ...` or `- G-SEC ...`). It prefers the agent's own structured record to prose that quotes the gate:
a row of a table with labelled columns first, then key-value rows, then any table row, and a list item last.

- **A table with labelled columns.** When the row sits in a table whose header names `status`, `fail`, `error`
  and `pass` columns, each cell is read on its own. The status cell holds the status word, and each of the
  three condition cells holds the check's ids for that gate that appear in it as whole words. All three sets
  must equal the check's, so the passing conditions are compared too.
- **Key-value rows.** When the gate takes two or more rows of a two-column table (`| G-SIGN `status` | fail |`,
  `| G-SIGN conditions with status `fail` | integration |`, ...), a key naming `status` gives the status, and a
  key naming conditions with `fail`, `error` or `pass` gives that set. Status, fail and error must all be
  present and equal the check's; a pass row, when present, must too.
- **Any other row.** The row's status is the first of pass / fail / error appearing in it as a whole word, in
  any case. Its condition ids are the check's ids for that gate that appear in it as whole words. A row that
  also names a passing condition id is "ambiguous" and needs a manual read.

The report's `probe.collected_at` is the first UTC timestamp on a line that mentions collected_at.

Usage:
    python3 -I util/ad-hoc/2026-10-27_turing_h3_compare.py --report FILE --probe-json FILE [--probe-json FILE ...] [--gates G-ALIAS,G-SIGN] [--json]

With several `--probe-json` captures (independent runs taken at intervals around the agent's run), the one whose
`collected_at` is nearest the agent's `probe.collected_at` is judged; the others are not read past that field.

Exit codes:

- 0: every covered gate agrees and the two runs are within ±10 minutes;
- 1: a contradiction, a missing or ambiguous gate, or the window missed;
- 2: a usage or input error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "util" / "host_state_check.py"
WINDOW_SECONDS = 600
STAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
STATUS_RE = re.compile(r"(?<![A-Za-z0-9_-])(pass|fail|error)(?![A-Za-z0-9_-])", re.IGNORECASE)


def word(token: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % re.escape(token))


def evaluate(probe_json: Path) -> dict:
    proc = subprocess.run([sys.executable, "-I", str(CHECK), "--probe-json", str(probe_json), "--json"], capture_output=True, text=True, cwd=str(REPO))
    if proc.returncode != 0:
        raise SystemExit("h3_compare: util/host_state_check.py --probe-json exited %d: %s" % (proc.returncode, proc.stderr.strip()[:400]))
    return json.loads(proc.stdout)


SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
COLUMNS = ("status", "fail", "error", "pass")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def gate_row(lines: list[str], gate: str) -> tuple[str | None, dict, list[tuple[str, str]]]:
    """The gate's first row; its table's status / fail / error / pass column indices (empty when unlabelled); and,
    when the gate takes two or more rows of a two-column table, those rows as (key, value) pairs."""
    lead = re.compile(r"^\s*(?:\|\s*|[-*]\s+)[`*_ ]*%s(?![A-Za-z0-9_-])" % re.escape(gate))
    found = []
    for n, line in enumerate(lines):
        if not lead.search(line):
            continue
        columns, pairs = {}, []
        if line.lstrip().startswith("|"):
            top = n
            while top > 0 and lines[top - 1].lstrip().startswith("|"):
                top -= 1
            if top + 1 < len(lines) and SEPARATOR_RE.match(lines[top + 1]):
                for i, head in enumerate(cells(lines[top])):
                    for name in COLUMNS:
                        if name in head.lower() and name not in columns:
                            columns[name] = i
            end = n
            while end < len(lines) and lines[end].lstrip().startswith("|"):
                end += 1
            pairs = [(cells(row)[0], cells(row)[1]) for row in lines[n:end] if lead.search(row) and len(cells(row)) == 2]
        found.append((line, (columns if len(columns) == len(COLUMNS) else {}), (pairs if len(pairs) >= 2 else [])))
    # prefer the agent's own structured record over prose that quotes the gate: labelled columns, then key-value
    # rows, then any table row, then a list item
    for rank in (lambda f: f[1], lambda f: f[2], lambda f: f[0].lstrip().startswith("|"), lambda f: True):
        for f in found:
            if rank(f):
                return f
    return None, {}, []


def report_stamp(lines: list[str]) -> str | None:
    for line in lines:
        if "collected_at" in line:
            found = STAMP_RE.search(line)
            if found:
                return found.group(0)
    return None


def parse_stamp(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)


def nearest(probes: list[Path], agent_at: str | None) -> Path:
    """The independent probe whose collected_at is nearest the agent's; the first one when the report has none."""
    if agent_at is None:
        return probes[0]
    target = parse_stamp(agent_at)
    stamps = {p: json.loads(p.read_text(encoding="utf-8"))["collected_at"] for p in probes}
    return min(probes, key=lambda p: abs((parse_stamp(stamps[p]) - target).total_seconds()))


def compare(report: Path, probes: list[Path], gates: list[str] | None) -> dict:
    lines = report.read_text(encoding="utf-8").splitlines()
    probe_json = nearest(probes, report_stamp(lines))
    check = evaluate(probe_json)
    by_id = {g["id"]: g for g in check["gates"]}
    covered = gates or list(by_id)
    rows = []
    for gate in covered:
        if gate not in by_id:
            raise SystemExit("h3_compare: the check evaluated no gate %s" % gate)
        truth = by_id[gate]
        bad = sorted(c["id"] for c in truth["conditions"] if c["status"] in ("fail", "error"))
        good = sorted(c["id"] for c in truth["conditions"] if c["status"] == "pass")
        row, columns, pairs = gate_row(lines, gate)
        entry = {"gate": gate, "check_status": truth["status"], "check_conditions": bad, "row": row}
        ids = [c["id"] for c in truth["conditions"]]
        if row is None:
            entry.update(report_status=None, report_conditions=None, verdict="missing")
            rows.append(entry)
            continue
        if pairs:
            # one gate over several (key, value) rows: "G-X `status`", "G-X conditions with status `fail`", ...
            want = {s: sorted(c["id"] for c in truth["conditions"] if c["status"] == s) for s in ("fail", "error", "pass")}
            got, status = {}, None
            for key, value in pairs:
                k = key.lower()
                if "condition" in k:
                    for s in ("fail", "error", "pass"):
                        if s in k:
                            got[s] = sorted(c for c in ids if word(c).search(value))
                elif "status" in k:
                    found = STATUS_RE.search(value)
                    status = found.group(1).lower() if found else None
            entry.update(row="; ".join("%s = %s" % p for p in pairs), report_status=status, report_conditions=sorted(got.get("fail", []) + got.get("error", [])), columns="key-value", report_sets=got)
            complete = "fail" in got and "error" in got
            entry["verdict"] = "agree" if complete and status == truth["status"] and all(got[s] == want[s] for s in got) else "contradiction"
            rows.append(entry)
            continue
        if columns:
            row_cells = cells(row)

            def named(column: str) -> list[str]:
                cell = row_cells[columns[column]] if columns[column] < len(row_cells) else ""
                return sorted(c for c in ids if word(c).search(cell))

            want = {s: sorted(c["id"] for c in truth["conditions"] if c["status"] == s) for s in ("fail", "error", "pass")}
            got = {s: named(s) for s in ("fail", "error", "pass")}
            status = STATUS_RE.search(row_cells[columns["status"]] if columns["status"] < len(row_cells) else "")
            entry.update(report_status=status.group(1).lower() if status else None, report_conditions=sorted(got["fail"] + got["error"]), columns="labelled", report_pass=got["pass"], check_pass=want["pass"])
            entry["verdict"] = "agree" if entry["report_status"] == truth["status"] and got == want else "contradiction"
            rows.append(entry)
            continue
        status = STATUS_RE.search(row)
        named = sorted(c for c in bad + good if word(c).search(row))
        entry.update(report_status=status.group(1).lower() if status else None, report_conditions=[c for c in named if c in bad])
        if entry["report_status"] != truth["status"] or entry["report_conditions"] != bad:
            entry["verdict"] = "contradiction"
        elif any(c in good for c in named):
            entry["verdict"] = "ambiguous"
        else:
            entry["verdict"] = "agree"
        rows.append(entry)
    agent_at = report_stamp(lines)
    independent_at = check["probe"]["collected_at"]
    delta = None if agent_at is None else int(abs((parse_stamp(agent_at) - parse_stamp(independent_at)).total_seconds()))
    return {
        "report": str(report),
        "independent_probe": str(probe_json),
        "independent_collected_at": independent_at,
        "agent_collected_at": agent_at,
        "delta_seconds": delta,
        "within_window": delta is not None and delta <= WINDOW_SECONDS,
        "gates": rows,
        "contradictions": sum(1 for r in rows if r["verdict"] == "contradiction"),
        "missing": sum(1 for r in rows if r["verdict"] == "missing"),
        "ambiguous": sum(1 for r in rows if r["verdict"] == "ambiguous"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--report", required=True, type=Path, help="the agent's report (markdown)")
    ap.add_argument("--probe-json", required=True, type=Path, action="append", help="an independent util/host_state_probe.bash --json capture; repeatable, and the one nearest the agent's probe.collected_at is judged")
    ap.add_argument("--gates", help="comma-separated gates the agent covers (default: every gate the check evaluates)")
    ap.add_argument("--json", action="store_true", help="print one JSON object instead of the table")
    args = ap.parse_args(argv)
    for path in [args.report] + args.probe_json:
        if not path.is_file():
            print("h3_compare: not a file: %s" % path, file=sys.stderr)
            return 2
    result = compare(args.report, args.probe_json, args.gates.split(",") if args.gates else None)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("independent probe %s; agent probe %s; delta %s s (window %d s)" % (result["independent_collected_at"], result["agent_collected_at"], result["delta_seconds"], WINDOW_SECONDS))
        for r in result["gates"]:
            print("%-13s %-8s check %-5s %-28s report %-5s %s" % (r["verdict"], r["gate"], r["check_status"], ",".join(r["check_conditions"]), r["report_status"], ",".join(r["report_conditions"] or [])))
        print("contradictions %d, missing %d, ambiguous %d, within window %s" % (result["contradictions"], result["missing"], result["ambiguous"], result["within_window"]))
    clean = result["contradictions"] == 0 and result["missing"] == 0 and result["ambiguous"] == 0 and result["within_window"]
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
