#!/usr/bin/env python3
"""Lane A: does a missing juniper-data (or cascor / canopy) checkout change docs-full-check's link-check result?

Runs the checker's own validate_directory in "check" mode on the head tree (eco/juniper-ml) with the workflow's
excludes, against a synthetic ecosystem root eco/ whose sibling directories are placeholders holding exactly the
five cross-repo targets juniper-ml links to. Root discovery is exercised too (discover_ecosystem_root). Compares
each variant's error list with the all-present baseline.
"""
import pathlib
import shutil
import sys

S = pathlib.Path(__file__).resolve().parent
ECO = S / "eco"
ML = ECO / "juniper-ml"
sys.path.insert(0, str(ML / "juniper-doc-tools"))
from juniper_doc_tools import check_doc_links as cdl  # noqa: E402

SIBLINGS = ["juniper-data", "juniper-cascor", "juniper-canopy", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-recurrence", "juniper-deploy"]
TARGETS = {
    "juniper-cascor": ["AGENTS.md", "src/api/observability.py"],
    "juniper-canopy": ["notes/FRONTEND_ISSUES_PLAN_2026-05-09.md"],
}


def populate(missing: str | None) -> None:
    for repo in SIBLINGS:
        d = ECO / repo
        if d.exists():
            shutil.rmtree(d)
        if repo == missing:
            continue
        d.mkdir()
        for rel in TARGETS.get(repo, []):
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text("placeholder\n")


def run(label: str, missing: str | None):
    populate(missing)
    root = cdl.discover_ecosystem_root(ML)
    res = cdl.validate_directory(ML, exclude_dirs={"templates", "history", "legacy"}, cross_repo_mode="check", ecosystem_root=root)
    print(f"{label:<14} discovered_root={root is not None and root.name} ok={res.ok} errors={len(res.errors)} files={res.scanned_files}")
    return res.errors


base = run("all-present", None)
for e in base[:10]:
    print("   baseline error:", e.strip()[:160])
for m in ("juniper-data", "juniper-cascor", "juniper-canopy"):
    errs = run(f"no-{m[8:]}", m)
    new = [e for e in errs if e not in base]
    print(f"   new errors vs baseline: {len(new)}")
    for e in new:
        print("     +", e.strip()[:170])
for repo in SIBLINGS:
    shutil.rmtree(ECO / repo, ignore_errors=True)
