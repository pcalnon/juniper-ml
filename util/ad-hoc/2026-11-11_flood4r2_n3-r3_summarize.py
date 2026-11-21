"""
Print the numbers round 3's N-3 texts quote, from the run records under the carrier's tmp/flood4-fix/n3-r3/.

Read-only. For each pytest lane (runs/*.json): exit status, counts, seconds, load average. For the mutant run
(mutants/results-all.json): each phase's failures, and for each mutant which tests killed it, grouped by test name with
the failing parameters. For the seed sweeps (sweep_*.json): seeds, violations and the outcome split. The texts
(CHANGELOG.md, pr_body.txt, commit_body.txt) are written by hand from this output, so every number in them can be
traced to a record.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import json
import sys
from pathlib import Path

D = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c" / "tmp" / "flood4-fix" / "n3-r3"


def load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def grouped(failed_ids: list) -> dict:
    """Test name -> the parameters that failed (an empty list for an unparametrized test)."""
    out: dict = {}
    for fid in failed_ids:
        name = fid.split("::")[-1]
        base, _, param = name.partition("[")
        out.setdefault(base, [])
        if param:
            out[base].append(param.rstrip("]"))
    return out


def main() -> int:
    loads = []
    for run in sorted((D / "runs").glob("*.json")):
        r = load(run)
        c = r["counts"]
        loads.extend(r.get("load_average_end", [])[:1])
        print(f"{r['label']}: exit {r['exit_status']}; {c.get('passed')} passed, {c.get('failures')} failed, {c.get('errors')} errors of {c.get('tests')}; {r['seconds']} s; load {r.get('load_average_end')}; coverage gate {r.get('coverage_gate_exit_status')}")
    if loads:
        print(f"1-minute load average at the end of the lanes: {min(loads):.1f} to {max(loads):.1f}")
    results = D / "mutants" / "results-all.json"
    if results.exists():
        mut = load(results)
        for name, phase in mut["phases"].items():
            print(f"phase {name}: exit {phase['exit_status']}; {phase['failed']} of {phase['tests']} failed, {phase['failed_in_the_new_file']} in the new file")
        killed = 0
        for name, m in mut["mutants"].items():
            killed += m["killed"]
            print(f"{name}: {'KILLED' if m['killed'] else 'SURVIVED'}; {m['failed']} of {m['tests']} failed ({m['failed_in_the_new_file']} in the new file); mutated {m['mutated_sha256_differs_from_carrier']}; restored {m['restored_sha256_verified']}; {m['seconds']} s")
            for test, params in sorted(grouped(m["failed_ids"]).items()):
                if len(grouped(m["failed_ids"])) <= 6:
                    print(f"      {test} {sorted(params) if params else ''}")
        print(f"mutants killed: {killed} of {len(mut['mutants'])}; carrier unchanged: {all(mut['carrier_sha256_unchanged'].values())}; stale pycache dirs deleted first: {mut['stale_pycache_dirs_deleted']}; scratch src status after restore: {mut['scratch_src_status_after_restore']!r}")
    for sweep in sorted(D.glob("sweep_*.json")):
        s = load(sweep)
        print(f"{sweep.name}: code {s['code_under_test']}; {s['n']} seeds; violations {s['violations']}; {s['elapsed_s']} s; outcomes {s['outcomes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
