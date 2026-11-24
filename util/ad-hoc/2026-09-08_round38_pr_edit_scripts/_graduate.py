#!/usr/bin/env python3
"""
Copy the round-38 one-shot PR edit scripts out of the session scratchpad into this directory
and stamp each with the util/ad-hoc file header (so none is lost when the sandbox is reaped).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (run once on 2026-09-08 to populate this directory)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md;
         the script-placement rule in AGENTS.md (§ Script placement) and util/ad-hoc/README.md

Each copied script keeps its original module docstring; the header fields are appended inside it.
The `Related:` line names the PR the script was applied for (by file-name prefix).
"""
from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/4af5ce60-c37f-4baf-8585-18271a95cc91/scratchpad")

PR_BY_PREFIX = {
    "canopy_": "juniper-canopy#605 (worktree juniper-canopy--feature--partial-data-three-way-prompt--20260908-0729--eb05021d)",
    "cascor_": "juniper-cascor#633 (worktree juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e)",
    "data_": "juniper-data#388 (worktree juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f)",
}
SCRIPTS = [
    "canopy_prompt_edit.py",
    "cascor_pr_a_edit.py",
    "cascor_pr_a_tests.py",
    "cascor_pr_a_changelog.py",
    "cascor_changelog_rebuild.py",
    "cascor_changelog_rebuild2.py",
    "data_pr_finish.py",
    "data_fix_seq_fixture.py",
    "data_fix_cap_fixture.py",
    "data_graduate_instruments.py",
    "data_changelog_reapply.py",
]


def header_for(name: str) -> str:
    related = next(pr for prefix, pr in PR_BY_PREFIX.items() if name.startswith(prefix))
    return (
        "\n"
        "Project: juniper-ml\n"
        "Sub-Project: ad-hoc tooling\n"
        "Author: Paul Calnon\n"
        "Created: 2026-09-08\n"
        "Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)\n"
        "Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)\n"
        f"Related: {related};\n"
        "         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md\n"
    )


def stamp(path: Path) -> None:
    text = path.read_text()
    module = ast.parse(text)
    first = module.body[0] if module.body else None
    if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)):
        sys.exit(f"FAIL: {path.name} has no module docstring to extend")
    lines = text.splitlines(keepends=True)
    end = first.end_lineno - 1  # 0-based index of the line holding the closing quotes
    closing = lines[end]
    if closing.strip() == '"""':
        lines.insert(end, header_for(path.name))
    else:
        idx = closing.rstrip("\n").rfind('"""')
        if idx < 0:
            sys.exit(f"FAIL: cannot find the closing quotes in {path.name}:{end + 1}")
        lines[end] = closing[:idx] + "\n" + header_for(path.name) + '"""\n'
    path.write_text("".join(lines))
    ast.parse(path.read_text())  # still valid Python


def main() -> int:
    for name in SCRIPTS:
        src = SCRATCH / name
        if not src.is_file():
            sys.exit(f"FAIL: {src} missing")
        dst = HERE / name
        shutil.copyfile(src, dst)
        stamp(dst)
        print(f"copied + stamped {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
