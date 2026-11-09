"""
Re-resolve juniper-data's pinned action tags and fetch upstream sources at the pinned refs (flood-4 docs validator).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-data docs carrier validation (juniper-data #509, #510, #511, #515)

Usage: python3 2026-11-07_flood4_val_data_docs_upstream.py <out_dir>

Writes <out_dir>/tag_resolution.json and <out_dir>/upstream/<owner>__<repo>__<ref8>__<path_>.txt.
Read-only against GitHub (gh api GETs only).
"""

import json
import os
import subprocess
import sys

TAGS = [
    ("actions/checkout", "v7.0.1", "3d3c42e5aac5ba805825da76410c181273ba90b1"),
    ("actions/setup-python", "v7.1.0", "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0"),
    ("actions/setup-python", "v7.0.0", "5fda3b95a4ea91299a34e894583c3862153e4b97"),
    ("actions/cache", "v6.1.0", "55cc8345863c7cc4c66a329aec7e433d2d1c52a9"),
    ("actions/upload-artifact", "v7.0.2", "cf430e030ddbb5b0abf93d22962f4752f3646cd9"),
    ("actions/download-artifact", "v8.0.2", "9000827ccba6bdab643e8b6fd33ac0654aef8333"),
    ("codecov/codecov-action", "v7.1.1", "303a32d7a59b442fa8d48b6a1cc6825c09c847a5"),
    ("gitleaks/gitleaks-action", "v3.0.0", "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e"),
    ("github/codeql-action", "v4.39.1", "9b3254085494b55a0f7c4c2b3d2d52cc712ce370"),
    ("pypa/gh-action-pypi-publish", "v1.14.3", "7245906fb61fa33a13554f9d5fb856fe61758086"),
    ("conda-incubator/setup-miniconda", "v4.1.0", "be893c923ea9cf1cf7cd510fbdde27c7e18cbdcb"),
    ("docker/setup-buildx-action", "v4.4.1", "f87e5991a6d7451dcb8d9637bfbc97413f497069"),
    ("docker/login-action", "v4.7.0", "81c6f93d4bc991e510b342a00b419b3bb4efc5c6"),
    ("docker/build-push-action", "v7.4.0", "c3c9e263c25d99ce0380d002d59b67737d91b0dc"),
    ("docker/metadata-action", "v6.2.0", "dc802804100637a589fabce1cb79ff13a1411302"),
    ("anthropics/claude-code-action", "v1.0.265", "6d5ae526d25ce88daa2200be073e1a373167f064"),
    ("anthropics/claude-code-action", "v1.0.255", "e4a6faad497d33dbc7144135c75e41f82f0bf6c0"),
]

FILES = [
    ("anthropics/claude-code-action", "6d5ae526d25ce88daa2200be073e1a373167f064", "src/github/operations/branch.ts"),
    ("anthropics/claude-code-action", "6d5ae526d25ce88daa2200be073e1a373167f064", "src/modes/tag/index.ts"),
    ("anthropics/claude-code-action", "6d5ae526d25ce88daa2200be073e1a373167f064", "action.yml"),
    ("gitleaks/gitleaks-action", "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e", "src/index.js"),
    ("gitleaks/gitleaks-action", "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e", "src/gitleaks.js"),
    ("gitleaks/gitleaks", "v8.24.3", "cmd/root.go"),
    ("gitleaks/gitleaks", "v8.24.3", "cmd/detect.go"),
    ("gitleaks/gitleaks", "v8.24.3", "cmd/git.go"),
    ("gitleaks/gitleaks", "v8.24.3", "cmd/directory.go"),
    ("gitleaks/gitleaks", "v8.24.3", "sources/git.go"),
    ("gitleaks/gitleaks", "v8.24.3", "config/config.go"),
    ("gitleaks/gitleaks", "v8.24.3", "config/rule.go"),
    ("gitleaks/gitleaks", "v8.24.3", "config/allowlist.go"),
    ("actions/checkout", "3d3c42e5aac5ba805825da76410c181273ba90b1", "action.yml"),
]


def gh(args):
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def fetch(up, repo, ref, path):
    rc, out, err = gh(["-H", "Accept: application/vnd.github.raw", f"repos/{repo}/contents/{path}?ref={ref}"])
    name = f"{repo.replace('/', '__')}__{ref[:8]}__{path.replace('/', '_')}.txt"
    with open(os.path.join(up, name), "w") as fh:
        fh.write(out if rc == 0 else f"FETCH FAILED rc={rc}: {err}")
    print(f"fetched rc={rc} {len(out):7d} bytes {name}")


def main():
    out_dir = sys.argv[1]
    up = os.path.join(out_dir, "upstream")
    os.makedirs(up, exist_ok=True)
    if len(sys.argv) > 2:
        # Extra mode: each further argument is <owner/repo>@<ref>:<path>; fetch only those.
        for spec in sys.argv[2:]:
            repo_ref, path = spec.split(":", 1)
            repo, ref = repo_ref.split("@", 1)
            fetch(up, repo, ref, path)
        return
    res = []
    for repo, tag, want in TAGS:
        rc, out, err = gh([f"repos/{repo}/commits/{tag}", "--jq", ".sha"])
        got = out.strip()
        res.append({"repo": repo, "tag": tag, "doc_sha": want, "resolved": got, "rc": rc, "match": got == want, "err": err.strip()[:200]})
        print(f"{'OK ' if got == want else 'BAD'} {repo}@{tag} doc={want[:12]} resolved={got[:12]} rc={rc}")
    with open(os.path.join(out_dir, "tag_resolution.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    for repo, ref, path in FILES:
        fetch(up, repo, ref, path)


if __name__ == "__main__":
    main()
