#!/usr/bin/env python3
"""Apply ONE repository's reviewed install pin(s) from a port's proposed pins file to this checkout's canonical pins file.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the one-artifact template sweep's pin applications, one per port after its review)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_publish_port_install_pins.json (the canonical pins file this edits);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the checker that reads it);
         reports/2026-11-23_one-artifact-template-sweep-reviews/dispositions.md (the arc's record of each application);
         plan v1.15.18 (notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)

Why
---
Each port proposes its repository's install pins in a copy of the pins file, and its review checks them. This takes
that repository's entries, and only those, into the canonical file. Promoted with plan v1.15.18 from session b71989's
``apply_pin.py`` (worktree moonlit-percolating-sun, its ``tmp/s2/``), which edited the sweep's working copy of the pins
file and regenerated the sweep's separate sha256 manifest. The pins file is in git now, and git is its manifest: no
manifest is regenerated, and an application is a change to commit. The refusals are the original's.

    python3 -I util/ad-hoc/2026-11-26_publish_port_apply_install_pin.py REPO PROPOSED.json [--dry-run] [--pins FILE]

Refuses (writes nothing, exit 1) unless:

- the proposed file's format and ``about`` equal the canonical file's, and its pins have the same keys
  (repo, workflow, step);
- each pin of every OTHER repository equals the canonical file's, or that repository's pin in an EARLIER canonical
  version (a proposal built before another repository's pin was applied): every version of
  ``util/ad-hoc/2026-11-24_publish_port_install_pins.json`` in this checkout's git history, and every backup this tool
  made of it (``tmp/publish-port-apply-install-pin/*/pins.before-*.json``);
- each of REPO's proposed pins keeps its package, and its sha256 is that of ``"\\n".join(lines)``, UTF-8;
- the canonical file re-serializes byte for byte under the layout used to write it back (so nothing else moves);
- the result is pure ASCII.

``--dry-run`` prints what would be applied and writes nothing. ``--pins FILE`` edits FILE in place of the checkout's
pins file, for a rehearsal on a copy; the earlier versions above are still the checkout's. Before it writes, the tool
backs the file up into a new directory, ``tmp/publish-port-apply-install-pin/<UTC stamp>/``, under the checkout root:
as ``pins.before-<REPO>-<stamp>.json`` for the checkout's own file, or ``rehearsal.before-<REPO>-<stamp>.json`` for any
other, so a rehearsal's backup never counts as an earlier canonical version. It runs from any juniper-ml checkout (the
root is found from this script's own location) and needs no third-party module. Exit status: 0 when the pins were
applied, when there was nothing to apply, or after a dry run; 1 when refused; 2 on a usage or environment error.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

PINS_REL = "util/ad-hoc/2026-11-24_publish_port_install_pins.json"
BACKUPS_REL = "tmp/publish-port-apply-install-pin"


def key(p: dict) -> tuple:
    return (p["repo"], p["workflow"], p["step"])


def dump(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n"


def git(root: Path, *args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def checkout_root() -> Path:
    here = Path(__file__).resolve().parent
    proc = git(here, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        raise SystemExit(f"this script is not inside a git checkout: {proc.stderr.strip()}")
    return Path(proc.stdout.strip())


def earlier_versions(root: Path) -> "list[dict]":
    """The canonical pins file's earlier versions: each in this checkout's git history, and each backup this tool made."""
    log = git(root, "log", "--format=%H", "--", PINS_REL)
    if log.returncode != 0:
        raise SystemExit(f"git log failed in {root}: {log.stderr.strip()}")
    versions = []
    for commit in log.stdout.split():
        show = git(root, "show", f"{commit}:{PINS_REL}")
        if show.returncode == 0:
            versions.append(json.loads(show.stdout))
    for path in sorted((root / BACKUPS_REL).glob("*/pins.before-*.json")):
        versions.append(json.loads(path.read_text(encoding="utf-8")))
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", help="the repository whose pins are taken from the proposal, e.g. juniper-canopy")
    parser.add_argument("proposed", type=Path, help="the port's proposed pins file")
    parser.add_argument("--dry-run", action="store_true", help="print what would be applied; write nothing")
    parser.add_argument("--pins", type=Path, help=f"the pins file to edit (default: the checkout's {PINS_REL})")
    args = parser.parse_args()
    root = checkout_root()
    canonical = (root / PINS_REL).resolve()
    target = args.pins.resolve() if args.pins else canonical
    repo, dry = args.repo, args.dry_run
    raw = target.read_text(encoding="utf-8")
    canon = json.loads(raw)
    if dump(canon) != raw:
        print("REFUSED: the canonical pins file does not re-serialize byte for byte under indent=2, ensure_ascii")
        return 1
    prop = json.loads(args.proposed.read_text(encoding="utf-8"))
    if (prop.get("format"), prop.get("about")) != (canon["format"], canon["about"]):
        print("REFUSED: the proposal's format/about differ from the canonical file's")
        return 1
    cmap = {key(p): p for p in canon["pins"]}
    pmap = {key(p): p for p in prop["pins"]}
    if set(cmap) != set(pmap):
        print(f"REFUSED: the key sets differ: only canonical {sorted(set(cmap) - set(pmap))}, only proposed {sorted(set(pmap) - set(cmap))}")
        return 1
    known: dict = {}
    for version in earlier_versions(root):
        for p in version["pins"]:
            known.setdefault(key(p), []).append(p)
    changed = []
    for k, p in pmap.items():
        if k[0] != repo:
            if p != cmap[k] and p not in known.get(k, []):
                print(f"REFUSED: the proposal changes another repository's pin {k} (equal to no canonical version)")
                return 1
            continue
        text = "\n".join(p["lines"])
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != p["sha256"]:
            print(f"REFUSED: {k}'s sha256 is not that of its lines")
            return 1
        if p["package"] != cmap[k]["package"]:
            print(f"REFUSED: {k}'s package moved")
            return 1
        if p != cmap[k]:
            changed.append((k, cmap[k]["sha256"], p["sha256"], len(cmap[k]["lines"]), len(p["lines"])))
    if not changed:
        print(f"nothing to apply: {repo}'s pins already equal the proposal's")
        return 0
    new = dict(canon)
    new["pins"] = [pmap[key(p)] if key(p)[0] == repo else p for p in canon["pins"]]
    out = dump(new)
    if not out.isascii():
        print("REFUSED: the result holds a non-ASCII character")
        return 1
    for k, old, new_sha, n_old, n_new in changed:
        print(f"{'WOULD APPLY' if dry else 'APPLY'} {k}: {old[:16]}... ({n_old} lines) -> {new_sha[:16]}... ({n_new} lines)")
    if dry:
        return 0
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = root / BACKUPS_REL / stamp
    try:
        backups.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"REFUSED (nothing written): {backups} exists (each run backs up into a new directory)")
        return 2
    backup = backups / f"{'pins' if target == canonical else 'rehearsal'}.before-{repo}-{stamp}.json"
    shutil.copy2(target, backup)
    target.write_text(out, encoding="utf-8")
    print(f"pins file {target} now {hashlib.sha256(out.encode()).hexdigest()}; backup: {backup.relative_to(root)}")
    if target == canonical:
        print(f"commit {PINS_REL}: git is its manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
