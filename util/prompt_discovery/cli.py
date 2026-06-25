"""prompt-discovery CLI: emit a JSON grounding bundle for the Template Agent.

``util/`` is not a package, so this is invoked **by path** (the house idiom -- no
``python -m``):

    python util/prompt_discovery/cli.py --repo-root <path> [--subject S] [--symbols a,b]

It assembles a closed-world fact set from the probe modules and stamps a provenance
envelope (``captured_at`` / ``head_sha`` / ``dirty`` / ``ttl_seconds`` / ``per_probe_status``).
A discovery failure -- ``repo_context`` cannot resolve the target repo's HEAD -- is a
**hard stop** (exit code 2 + a ``discovery_failed`` envelope): the Template Agent must never
proceed on an empty-but-valid bundle (design S5.1 step 2).

Part of the custom-agent suite (PR 4). Design-of-record:
``notes/JUNIPER_ML_CUSTOM_AGENT_SUITE_DESIGN_2026-06-23.md`` (S5.6).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import concurrency
import conventions
import dependency_facts
import file_probe
import repo_context
import symbol_probe
import test_status

SCHEMA_VERSION = 1
TTL_SECONDS = 900


def build_bundle(repo_root: str, subject, symbols):
    """Return ``(bundle, repo_ctx)``; ``bundle`` is ``None`` on a hard-stop discovery failure."""
    repo_ctx = repo_context.probe(repo_root)
    if repo_ctx.get("status") != "ok" or not repo_ctx.get("head_sha"):
        return None, repo_ctx
    ts = test_status.probe(repo_root)
    fp = file_probe.probe(repo_root, subject)
    sp = symbol_probe.probe(repo_root, symbols)
    dep = dependency_facts.probe(repo_root)
    conv = conventions.probe(repo_root)
    conc = concurrency.probe(repo_root)
    per_probe = {
        "repo_context": repo_ctx["status"],
        "test_status": ts["status"],
        "file_probe": fp["status"],
        "symbol_probe": sp["status"],
        "dependency_facts": dep["status"],
        "conventions": conv["status"],
        "concurrency": conc["status"],
    }
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "provenance": {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "head_sha": repo_ctx["head_sha"],
            "dirty": repo_ctx["dirty"],
            "ttl_seconds": TTL_SECONDS,
            "per_probe_status": per_probe,
        },
        "repo_context": repo_ctx,
        "test_status": ts,
        "file_probe": fp,
        "symbol_probe": sp,
        "dependency_facts": dep,
        "conventions": conv,
        "concurrency": conc,
    }
    return bundle, repo_ctx


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Emit a prompt-discovery grounding bundle (JSON).")
    parser.add_argument("--repo-root", default=os.getcwd(), help="target repo to ground against (default: CWD)")
    parser.add_argument("--subject", default=None, help="task subject -> file_probe anchors")
    parser.add_argument("--symbols", default=None, help="comma-separated symbol names -> symbol_probe")
    parser.add_argument("--json", action="store_true", help="emit JSON (the default and only format)")
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] if args.symbols else []
    bundle, repo_ctx = build_bundle(repo_root, args.subject, symbols)
    if bundle is None:
        envelope = {
            "status": "discovery_failed",
            "reason": repo_ctx.get("reason", "repo_context unavailable"),
            "repo_root": repo_root,
        }
        print(json.dumps(envelope, indent=2))
        return 2
    print(json.dumps(bundle, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
