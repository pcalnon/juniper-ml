"""
Census, on each repository's freshly fetched origin/main, of every caller of replay_since / promote_to_active and of anything that sends a resume frame.

The ten Juniper repositories: nine sibling primaries (fetched here with ``git -C <primary> fetch origin``, which
touches no working tree) and the juniper-ml worktree this script runs in. ``git grep`` reads origin/main's tree,
not any checkout. Families:

  replay_since   ``replay_since`` (the public method whose answer above the last seq numbered changes)
  promote        ``promote_to_active`` / ``replayed_through``
  resume_sender  a ``last_seq`` / ``lastSeq`` or a ``"resume"`` frame type, in code
  tier           service-core's WebSocket tier: ``juniper_service_core.websocket``, ``build_websocket_router``,
                 ``attach_websocket``, ``training_stream_handler``, ``ReplayOutOfRange``

Writes ``consumer_census.json`` (every hit) and ``consumer_census.txt`` (per repository and family, the files,
with test / notes / util / scripts paths counted apart from the rest).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14); adapted from 2026-11-12_flood4r2_val_d14-resume_client_census.py
"""

import argparse
import json
import subprocess
from pathlib import Path

SIBLINGS = ["juniper-cascor", "juniper-canopy", "juniper-cascor-client", "juniper-cascor-worker", "juniper-recurrence", "juniper-data", "juniper-data-client", "juniper-deploy", "juniper-harcot"]

PATTERNS = {
    "replay_since": r"replay_since",
    "promote": r"promote_to_active|replayed_through",
    "resume_sender": r"last_seq|lastSeq|[\"']resume[\"']",
    "tier": r"juniper_service_core\.websocket|build_websocket_router|attach_websocket|training_stream_handler|ReplayOutOfRange",
}

#: Code and configuration only; prose is read by hand where a hit matters.
PATHSPECS = ["*.py", "*.js", "*.ts", "*.tsx", "*.html", "*.toml", "*.yml", "*.yaml", "*.json", "*.sh", "*.bash"]


def run(command: list[str], cwd: Path) -> tuple[int, str, str]:
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout, done.stderr


def is_support_path(path: str) -> bool:
    parts = path.split("/")
    return any(part in ("tests", "test", "util", "scripts", "notes", "docs") for part in parts) or parts[-1].startswith("test_")


def census(name: str, repo: Path, own_worktree: bool) -> dict:
    prefix = ["git"] if own_worktree else ["git", "-C", str(repo)]
    cwd = repo if own_worktree else Path.cwd()
    fetched = "own worktree, fetched before this run"
    if not own_worktree:
        code, _out, err = run([*prefix, "fetch", "--quiet", "origin"], cwd)
        fetched = "fetched" if code == 0 else f"fetch failed ({err.strip()[:200]})"
    code, sha, _err = run([*prefix, "rev-parse", "origin/main"], cwd)
    if code != 0:
        return {"repo": name, "error": "origin/main could not be resolved", "fetched": fetched}
    sha = sha.strip()
    families = {}
    for family, pattern in PATTERNS.items():
        code, out, _err = run([*prefix, "grep", "-n", "-I", "-E", "-e", pattern, sha, "--", *PATHSPECS], cwd)
        if code not in (0, 1):
            families[family] = {"error": f"git grep exited {code}"}
            continue
        hits = []
        for line in out.splitlines():
            _rev, path, number, text = line.split(":", 3)
            hits.append({"path": path, "line": int(number), "text": text.strip()[:300], "support": is_support_path(path)})
        families[family] = {"hits": len(hits), "files": sorted({hit["path"] for hit in hits}), "lines": hits}
    return {"repo": name, "origin_main": sha, "fetched": fetched, "families": families}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.home() / "Development" / "python" / "Juniper", help="the directory holding the sibling primaries")
    parser.add_argument("--ml-worktree", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    results = [census(name, args.root / name, own_worktree=False) for name in SIBLINGS]
    results.append(census("juniper-ml", args.ml_worktree, own_worktree=True))

    lines = []
    for result in results:
        lines.append(f"===== {result['repo']} origin/main {result.get('origin_main', '?')[:8]} ({result['fetched']}) =====")
        if "error" in result:
            lines.append("  " + result["error"])
            continue
        for family, found in result["families"].items():
            if "error" in found:
                lines.append(f"  {family}: {found['error']}")
                continue
            code_hits = [hit for hit in found["lines"] if not hit["support"]]
            lines.append(f"  {family}: {found['hits']} lines in {len(found['files'])} files; outside tests/util/scripts/notes/docs: {len(code_hits)} lines")
            lines.extend(f"      {hit['path']}:{hit['line']}: {hit['text'][:160]}" for hit in code_hits)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "consumer_census.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=1)
        handle.write("\n")
    with open(args.out_dir / "consumer_census.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
