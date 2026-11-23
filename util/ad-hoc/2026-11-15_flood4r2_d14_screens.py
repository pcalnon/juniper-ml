"""
Screens for the D-14 carriers: list each carrier's changed files with sha256, and run G-PATH, G-TMP and the CodeQL prescreen on them.

Reads ``git status --porcelain --untracked-files=all`` of the juniper-ml carrier (this worktree) and the juniper-cascor
carrier, and writes ``screens.json``: per carrier, every changed path with its status and sha256 (the file list for
manifest.json, and the hashes to re-verify before a final message), then the gates' exit codes and output:

  G-PATH   ``util/home_path_literal_check.py`` on the juniper-ml files under util/, scripts/ or .github/ (its scope)
  G-TMP    ``util/tmp_path_literal_check.py`` on every changed juniper-ml file of a type the gate reads
  CodeQL   ``util/ad-hoc/2026-10-05_codeql_python_prescreen.py`` on every changed .py file of both carriers

Scratch files of the carriers (``tmp/``) are not carrier files and are skipped.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

GATE_TMP_SUFFIXES = (".bash", ".sh", ".py", ".yml", ".yaml", ".toml", ".service", ".timer")


def changed(repo: Path, own: bool) -> list[dict]:
    command = ["git", "status", "--porcelain", "--untracked-files=all"] if own else ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"]
    out = subprocess.run(command, cwd=repo if own else Path.cwd(), capture_output=True, text=True, check=True).stdout
    files = []
    for line in out.splitlines():
        status, path = line[:2].strip(), line[3:]
        if path.startswith("tmp/"):
            continue
        full = repo / path
        files.append({"path": path, "status": {"M": "modified", "??": "added", "A": "added", "D": "deleted"}.get(status, status), "sha256": hashlib.sha256(full.read_bytes()).hexdigest() if full.is_file() else None})
    return files


def run(command: list[str], cwd: Path) -> dict:
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return {"command": " ".join(command), "exit": done.returncode, "output": (done.stdout + done.stderr).strip()[-4000:]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--ml", type=Path, required=True, help="the juniper-ml carrier: this worktree")
    parser.add_argument("--cascor", type=Path, required=True, help="the juniper-cascor carrier worktree")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    ml_files = changed(args.ml, own=True)
    cascor_files = changed(args.cascor, own=False)
    ml_paths = [item["path"] for item in ml_files if item["sha256"] is not None]
    gpath = [path for path in ml_paths if path.split("/")[0] in ("util", "scripts", ".github")]
    gtmp = [path for path in ml_paths if path.endswith(GATE_TMP_SUFFIXES)]
    python_files = [str(args.ml / path) for path in ml_paths if path.endswith(".py")] + [str(args.cascor / item["path"]) for item in cascor_files if item["path"].endswith(".py") and item["sha256"] is not None]
    interpreter = sys.executable
    result = {
        "interpreter": interpreter,
        "juniper-ml": ml_files,
        "juniper-cascor": cascor_files,
        "G-PATH": run([interpreter, "util/home_path_literal_check.py", *gpath], args.ml),
        "G-TMP": run([interpreter, "util/tmp_path_literal_check.py", *gtmp], args.ml),
        "CodeQL prescreen": run([interpreter, "util/ad-hoc/2026-10-05_codeql_python_prescreen.py", *python_files], args.ml),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    for name in ("G-PATH", "G-TMP", "CodeQL prescreen"):
        print(f"{name}: exit {result[name]['exit']}: {result[name]['output'][-600:]}")
    print(f"juniper-ml: {len(ml_files)} changed files; juniper-cascor: {len(cascor_files)} changed files")


if __name__ == "__main__":
    main()
