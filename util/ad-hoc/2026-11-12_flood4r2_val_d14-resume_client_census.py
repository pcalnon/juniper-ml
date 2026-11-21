"""
List, on each Juniper repository's origin/main, every line that could send or handle a /ws/training resume.

For each repository the script records the origin/main commit and the lines matching three pattern families:

  resume    the resume protocol's words (last_seq, resume_ok, resume_failed, the two reasons, server_instance_id)
  endpoint  the WebSocket paths (/ws/training, /ws/control, the worker paths)
  tier      juniper-service-core's WebSocket tier (its module path, router factory, bridge and handler names)

It reads commits with ``git grep <pattern> origin/main``, so a primary checkout that lags its remote, or carries
uncommitted work, does not change the answer. Sibling repositories are read with ``git -C``; juniper-ml is read from
the worktree this script is run in. Nothing is fetched and nothing is written outside ``--out-dir``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor#754; the design check of whether juniper-service-core follows cascor's two new resume answers
"""

import argparse
import json
import subprocess
from pathlib import Path

SIBLINGS = ["juniper-cascor", "juniper-canopy", "juniper-cascor-client", "juniper-cascor-worker", "juniper-recurrence", "juniper-data", "juniper-data-client", "juniper-deploy", "juniper-harcot"]

PATTERNS = {
    "resume": r"last_seq|lastSeq|resume_ok|resume_failed|malformed_resume|out_of_range|server_instance_id|serverInstanceId|[\"']resume[\"']",
    "endpoint": r"ws/training|ws/control|ws/v1/workers|ws/workers",
    "tier": r"juniper_service_core\.websocket|build_websocket_router|attach_websocket|training_stream_handler",
}

#: Code and configuration only: prose is read by hand where it matters.
PATHSPECS = ["*.py", "*.js", "*.ts", "*.html", "*.toml", "*.yml", "*.yaml", "*.json", "*.sh", "*.bash"]


def run(command: list[str], cwd: Path) -> tuple[int, str]:
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout


def census(name: str, repo: Path, own_worktree: bool) -> dict:
    prefix = ["git"] if own_worktree else ["git", "-C", str(repo)]
    cwd = repo if own_worktree else Path.cwd()
    code, sha = run([*prefix, "rev-parse", "origin/main"], cwd)
    if code != 0:
        return {"repo": name, "error": "origin/main could not be resolved"}
    sha = sha.strip()
    families = {}
    for family, pattern in PATTERNS.items():
        code, out = run([*prefix, "grep", "-n", "-I", "-E", "-e", pattern, sha, "--", *PATHSPECS], cwd)
        if code not in (0, 1):
            families[family] = {"error": f"grep exited {code}"}
            continue
        hits = []
        for line in out.splitlines():
            _, path, number, text = line.split(":", 3)
            hits.append({"path": path, "line": int(number), "text": text.strip()[:300]})
        families[family] = {"hits": len(hits), "files": sorted({hit["path"] for hit in hits}), "lines": hits}
    return {"repo": name, "origin_main": sha, "families": families}


def is_test_path(path: str) -> bool:
    parts = path.split("/")
    return "tests" in parts or "test" in parts or parts[-1].startswith("test_") or "util" in parts or "scripts" in parts or "notes" in parts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.home() / "Development" / "python" / "Juniper", help="the directory holding the sibling repositories")
    parser.add_argument("--ml-worktree", type=Path, required=True, help="the juniper-ml worktree this script runs in")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    results = [census(name, args.root / name, own_worktree=False) for name in SIBLINGS]
    results.append(census("juniper-ml", args.ml_worktree, own_worktree=True))

    lines = []
    for result in results:
        lines.append(f"===== {result['repo']} origin/main {result.get('origin_main', '?')[:8]} =====")
        if "error" in result:
            lines.append("  " + result["error"])
            continue
        for family, found in result["families"].items():
            if "error" in found:
                lines.append(f"  {family}: {found['error']}")
                continue
            production = [path for path in found["files"] if not is_test_path(path)]
            lines.append(f"  {family}: {found['hits']} lines in {len(found['files'])} files; outside tests/util/scripts/notes: {len(production)}")
            lines.extend(f"      {path}" for path in production)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "client_census.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1)
        handle.write("\n")
    with open(args.out_dir / "client_census.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
