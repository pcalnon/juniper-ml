"""
Probe the host's real gh binary with READ-ONLY GraphQL queries: exit status, stdout and stderr on an error response.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

Every request is a GraphQL `query` operation (never a mutation) sent with `gh api graphql --input FILE`,
the form the workflow step uses. The fake-token probe sends a literal that is not a credential.
Nothing from the environment is printed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

FAKE_TOKEN = "lockfile-val-probe-not-a-credential"

PROBES: list[dict[str, object]] = [
    {"id": "malformed_field", "query": "query { viewer { loginx } }", "fake_token": False},
    {"id": "syntax_error", "query": "query { viewer { ", "fake_token": False},
    {"id": "ok_typename", "query": "query { __typename }", "fake_token": False},
    {"id": "partial_data_with_errors", "query": 'query { __typename repository(owner: "cli", name: "no-such-repo-flood4-val-probe") { id } }', "fake_token": False},
    {"id": "fake_token_401", "query": "query { __typename }", "fake_token": True},
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    version = subprocess.run(["gh", "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0]
    results: list[dict[str, object]] = []
    for probe in PROBES:
        query = str(probe["query"])
        if "mutation" in query:
            print("refusing a mutation", file=sys.stderr)
            return 2
        body = args.out / f"{probe['id']}.request.json"
        with open(body, "w", encoding="utf-8") as fh:
            json.dump({"query": query}, fh)
        env = dict(os.environ)
        if probe["fake_token"]:
            env["GH_TOKEN"] = FAKE_TOKEN
            env.pop("GITHUB_TOKEN", None)
        stdout_path = args.out / f"{probe['id']}.stdout"
        with open(stdout_path, "wb") as out_fh:
            proc = subprocess.run(["gh", "api", "graphql", "--input", str(body)], stdout=out_fh, stderr=subprocess.PIPE, env=env, check=False, timeout=60)
        stderr = proc.stderr.decode("utf-8", "replace")
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        with open(args.out / f"{probe['id']}.stderr", "w", encoding="utf-8") as fh:
            fh.write(stderr)
        results.append({"id": probe["id"], "query": query, "fake_token": probe["fake_token"], "rc": proc.returncode, "stdout": stdout[:600], "stderr": stderr[:600], "fake_token_in_output": FAKE_TOKEN in stdout + stderr})
    summary = {"gh_version": version, "results": results}
    with open(args.out / "real_gh_probe.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
