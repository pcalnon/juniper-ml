#!/usr/bin/env python3
"""
Materialize a release-train proposal's file edits + notes for a SIBLING repo.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc -- migration
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy v0.8.0 / juniper-cascor-worker v0.6.0 release prep (container-registry Wave 3)

Why this exists: ``propose.py --execute`` opens a sibling repo's PR only with
``--cross-repo`` AND a GitHub App installation token; without one it skips
sibling packages entirely. This takes the same proposal's ``--json`` output,
fetches each target file from the sibling's ``main`` via the API (never from a
possibly-stale local checkout), applies the proposal's own unified diffs with
``patch``, and writes the drafted notes -- leaving files ready for
``util/open_signed_pr.py``.

Usage:
  python3 util/ad-hoc/2026-09-11_materialize_release_proposal.py \
      --proposal-json <propose --json output> --package juniper-canopy --out-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def gh_file(repo: str, path: str, ref: str = "main") -> str:
    """Fetch one file's content from a repo at ``ref`` via the GitHub API."""
    out = subprocess.run(
        ["gh", "api", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}", "--jq", ".content"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    import base64

    return base64.b64decode(out).decode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal-json", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    doc = json.loads(Path(args.proposal_json).read_text(encoding="utf-8"))
    proposals = doc["proposals"] if isinstance(doc, dict) and "proposals" in doc else doc
    matches = [p for p in proposals if p["pypi_name"] == args.package]
    if not matches:
        print(f"ERROR: no proposal for {args.package}", file=sys.stderr)
        return 2
    p = matches[0]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    repo = p["repo"]

    print(f"{p['pypi_name']}: {p['from_version']} -> {p['to_version']} [{p['bump']}] in {repo}")
    print(f"  branch : {p['branch']}")
    print(f"  commit : {p['commit_message']}")

    for edit in p["edits"]:
        rel = edit["path"]
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(gh_file(repo, rel), encoding="utf-8")

        patch_file = out / (rel.replace("/", "__") + ".patch")
        patch_file.write_text(edit["diff"], encoding="utf-8")

        res = subprocess.run(
            ["patch", "--batch", "--forward", str(dest), str(patch_file)],
            capture_output=True,
            text=True,
        )
        status = "OK " if res.returncode == 0 else "FAIL"
        print(f"  [{status}] {rel}  {res.stdout.strip() or res.stderr.strip()}")
        if res.returncode != 0:
            return 1

    notes = out / "RELEASE_NOTES.md"
    notes.write_text(p["notes_draft"], encoding="utf-8")
    print(f"  notes  : {notes}  -> archive at {p['notes_relpath']}")

    (out / "PR_BODY.md").write_text(p["pr_body"], encoding="utf-8")
    (out / "META.json").write_text(
        json.dumps(
            {k: p[k] for k in ("repo", "branch", "commit_message", "pr_title", "notes_relpath", "from_version", "to_version", "bump")},
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
