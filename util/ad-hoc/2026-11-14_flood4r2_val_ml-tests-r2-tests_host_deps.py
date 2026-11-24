"""
List what each named test file needs from its host: the programs it starts, its skips, and platform / home / clock use.

For every file (by ast and by text, read-only) it reports: the first argv element of each list or tuple literal
that names a program (a string at the head of a list passed anywhere), every ``skip`` decorator or ``SkipTest``, and
whether the file reads ``sys.platform``, ``Path.home()`` / ``HOME``, ``time.sleep`` or a port number.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --root <tree> --paths <file listing test paths> --out <json>
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

PROGRAM_RE = re.compile(r"^(?:/[\w./-]+/)?(?P<name>[A-Za-z][\w.+-]*)$")
KNOWN = {"git", "bash", "sh", "env", "rm", "gpg", "gh", "uv", "brew", "sed", "grep", "date", "mktemp", "readlink", "realpath", "python3", "python", "pre-commit", "chmod", "cat", "ssh", "ssh-keygen", "git-lfs", "conda", "notify-send", "systemctl", "tar"}


def scan(path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    programs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)) and node.elts and isinstance(node.elts[0], ast.Constant) and isinstance(node.elts[0].value, str):
            match = PROGRAM_RE.match(node.elts[0].value)
            if match and match.group("name") in KNOWN:
                programs.add(node.elts[0].value)
    return {
        "programs": sorted(programs),
        "uses_sys_executable": "sys.executable" in text,
        "skips": sorted(set(re.findall(r"skip(?:If|Unless|Test)?\([^)]{0,80}", text))),
        "platform": "sys.platform" in text or "platform.system" in text,
        "home": "Path.home()" in text or '"HOME"' in text or "'HOME'" in text,
        "sleep": "time.sleep" in text,
        "ports": sorted(set(re.findall(r"\b(?:80[0-9]{2}|81[0-9]{2}|82[0-9]{2})\b", text))),
        "network": any(word in text for word in ("urllib", "requests", "socket.", "http.client")),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", required=True)
    parser.add_argument("--paths", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    rows = {}
    for rel in (line.strip() for line in Path(args.paths).read_text(encoding="utf-8").splitlines()):
        if rel:
            rows[rel] = scan(Path(args.root) / rel)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
        fh.write("\n")
    for rel, row in rows.items():
        print("%-58s programs=%s sys.executable=%s skips=%s platform=%s home=%s sleep=%s ports=%s network=%s" % (rel, row["programs"], row["uses_sys_executable"], row["skips"], row["platform"], row["home"], row["sleep"], row["ports"], row["network"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
