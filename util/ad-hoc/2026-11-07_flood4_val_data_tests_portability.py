#!/usr/bin/env python3
"""
Screen the juniper-data flood-4 tests carrier, and every shell it executes, for GNU-only and bash-4+ constructs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 validation brief (CI-parity / macOS lens)

The required macOS leg resolves `bash` from /usr/bin:/bin for #512's run_coverage rehearsal, #513 and #514,
which on macOS is /bin/bash 3.2 with BSD userland and Apple's /usr/bin/jq. This prints every line, in the
seven carried test files, util/run_coverage.bash, and the workflow `run:` blocks the tests execute, that
matches a GNU-only flag or a bash-4+ construct, plus every external command those blocks call.

    python3 2026-11-07_flood4_val_data_tests_portability.py <juniper-data worktree>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PATTERNS = {
    "sed -i (GNU form)": r"\bsed\s+-i(\s|$|[^ ']*\s)",
    "sed -r": r"\bsed\s+-r\b",
    "grep -P": r"\bgrep\s+(-[a-zA-Z]*P|--perl)",
    "base64 -w": r"\bbase64\s+-w",
    "date -d / --date": r"\bdate\s+(-d\b|--date)",
    "stat -c / --format": r"\bstat\s+(-c\b|--format)",
    "readlink -f": r"\breadlink\s+-f",
    "xargs -r": r"\bxargs\s+-r",
    "find -printf": r"-printf\b",
    "sha256sum/md5sum": r"\b(sha256sum|md5sum|sha1sum)\b",
    "timeout cmd": r"(^|[;&|]\s*|\s)timeout\s+\d",
    "tac": r"\btac\b",
    "GNU long option on coreutils": r"\b(sort|head|tail|cut|tr|wc|ls|cp|mv|mktemp|install|du|df|basename|dirname)\s+--[a-z]",
    "echo -e": r"\becho\s+-e\b",
    "mapfile/readarray": r"\b(mapfile|readarray)\b",
    "declare -A / -n": r"\b(declare|local|typeset)\s+-[a-zA-Z]*[An]\b",
    "case-modifying expansion": r"\$\{[A-Za-z_][A-Za-z0-9_]*(,,|\^\^|,|\^)\}",
    "negative array index": r"\$\{[A-Za-z_][A-Za-z0-9_]*\[-\d+\]\}",
    "[[ -v": r"\[\[\s+-v\b",
    "|& or &>>": r"\|&|&>>",
    "case fallthrough ;& ;;&": r";;&|;&",
    "${var@op}": r"\$\{[A-Za-z_][A-Za-z0-9_]*@[QEPAKa]\}",
    "wait -n / coproc / globstar": r"\bwait\s+-n\b|\bcoproc\b|globstar",
    "hard-coded /usr/bin interpreter": r"/usr/bin/(bash|env\s+-S|python3?|jq)\b",
    "/usr/local or /opt/homebrew path": r"/usr/local/|/opt/homebrew",
}

TEST_FILES = [
    "juniper_data/tests/unit/test_bandit_sarif_upload.py",
    "juniper_data/tests/unit/test_check_module_coverage.py",
    "juniper_data/tests/unit/test_run_coverage_gates.py",
    "juniper_data/tests/unit/test_publish_image_manifest_identity.py",
    "juniper_data/tests/unit/test_publish_manifest_tag_gates.py",
    "juniper_data/tests/unit/test_testpypi_install_verify.py",
    "juniper_data/tests/unit/test_middleware.py",
]

STEPS = [
    (".github/workflows/publish-image.yml", "merge", "Create manifest list"),
    (".github/workflows/publish-image.yml", "merge", "Verify both architectures are present"),
    (".github/workflows/publish-image.yml", "merge", "Verify the release produced a version tag"),
    (".github/workflows/publish-image.yml", "merge", "Verify published image is CPU-only"),
    (".github/workflows/publish.yml", "testpypi", "Verify TestPyPI install"),
]


def screen(label: str, text: str) -> int:
    hits = 0
    for n, line in enumerate(text.splitlines(), 1):
        for name, pat in PATTERNS.items():
            if re.search(pat, line):
                hits += 1
                print(f"  HIT [{name}] {label}:{n}: {line.strip()[:150]}")
    return hits


def main() -> int:
    root = Path(sys.argv[1])
    total = 0
    for rel in TEST_FILES:
        total += screen(rel, (root / rel).read_text(encoding="utf-8"))
    total += screen("util/run_coverage.bash", (root / "util/run_coverage.bash").read_text(encoding="utf-8"))
    for wf, job, name in STEPS:
        data = yaml.safe_load((root / wf).read_text(encoding="utf-8"))
        steps = [s for s in data["jobs"][job]["steps"] if s.get("name") == name]
        assert len(steps) == 1, (wf, name)
        run = steps[0]["run"]
        label = f"{wf}#{job}/{name}"
        total += screen(label, run)
        cmds = set()
        for line in run.splitlines():
            code = line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
            for m in re.finditer(r"(?:^|[;&|(]|\$\(|then|do|else)\s*([a-z][a-z0-9_.-]*)", code.strip()):
                cmds.add(m.group(1))
        print(f"  commands in {label}: {sorted(cmds)}")
    print(f"total hits: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
