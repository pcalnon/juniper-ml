#!/usr/bin/env python3
"""
Re-derive the canopy flood-4 docs carrier's load-bearing claims from main's workflows, config and code.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (#790 Gitleaks, #791 Codecov / lane wiring, #793 AGENTS.md date check, #796 mnist)

Usage: 2026-11-07_flood4_canopy_docs_rederive.py <docs worktree> <juniper-ml checkout>
Prints each source line a claim rests on (file:line), and the mnist declared-param entry as
main's dataset_schema computes it (JuniperCanopy1, imported from the worktree's src/).
"""

import re
import subprocess
import sys
from pathlib import Path

CHECKS = [
    (".gitleaks.toml", r"^\[extend\]|useDefault|^\[\[rules\]\]|^id =|condition|conda_environment|requirements-conda"),
    (".github/workflows/ci.yml", r"gitleaks-action@|GITLEAKS_VERSION|GITLEAKS_PARITY_REQUIRED: "),
    (".github/workflows/security-scan.yml", r"cron|pip-audit --|bandit -r|pip install|gitleaks"),
    (".github/workflows/ci.yml", r"codecov/codecov-action@|token: \$\{\{ secrets.CODECOV_TOKEN|files: reports/coverage.xml|src/tests/unit/ src/tests/regression/"),
    ("src/tests/regression/test_ci_lane_wiring.py", r"class TestNoTestModuleSitsAtTheTopOfTheTestTree|class TestEveryTestDirectoryIsNamedBySomeLane"),
    (".github/workflows/agents-md-touch-up.yml", r"^name:|verify-date:|name: Verify AGENTS|git commit|git push|test_agents_md_"),
]

SNIPPET = (
    "import dataset_schema as d\n"
    "m = d.DECLARED_PARAM_DEFAULTS['mnist']\n"
    "print('mnist entry from', d.__file__)\n"
    "print('fields', len(m), 'n_samples', 'n_samples' in m, 'noise', 'noise' in m, 'flatten', m.get('flatten'))\n"
    "print('entries', sorted(d.DECLARED_PARAM_DEFAULTS))\n"
)


def main(argv: list[str]) -> int:
    wt, ml = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    for rel, pattern in CHECKS:
        rx = re.compile(pattern)
        print(f"# {rel}  /{pattern}/")
        for n, line in enumerate((wt / rel).read_text(encoding="utf-8").splitlines(), 1):
            if rx.search(line):
                print(f"{rel}:{n}: {line.strip()[:150]}")
    print("# top-level src/tests/test_*.py (expect none):", sorted(p.name for p in (wt / "src/tests").glob("test_*.py")))
    hdr = ml / "juniper-ci-tools/juniper_ci_tools/lint_agents_md_header.py"
    for n, line in enumerate(hdr.read_text(encoding="utf-8").splitlines(), 1):
        if 'startswith("## ")' in line:
            print(f"juniper-ci-tools lint_agents_md_header.py:{n}: {line.strip()}")
    proc = subprocess.run(["/opt/miniforge3/bin/conda", "run", "-n", "JuniperCanopy1", "python", "-c", SNIPPET], cwd=wt / "src", capture_output=True, text=True, check=False)
    print("# mnist (JuniperCanopy1, cwd src/):")
    print("\n".join(line for line in proc.stdout.splitlines() if not re.search(r"\| (INFO|DEBUG) \|", line)))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
