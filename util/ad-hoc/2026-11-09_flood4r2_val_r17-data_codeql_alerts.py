"""
Read juniper-data's CodeQL code-scanning alerts (read-only GETs) and report the classes a pytestmark change could raise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, Cursor flood-4 round 2)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 ("data: 44 unrun tests"); independent validation of the r17-data-unit-marks carrier

Question answered: has GitHub's CodeQL EVER alerted (open, dismissed or fixed) on a module-level
``pytestmark`` in juniper-data, or on anything in ``juniper_data/tests/unit/test_security.py``? The
prescreen predicts ``py/unused-global-variable`` on the carrier's new ``pytestmark``; an alert of that
rule on any of the existing module-level assignments would mean the PR's CodeQL review opens a
blocking thread. Also lists the analyses' tool/config so the scan scope (tests included?) is visible.
"""

import argparse
import json
import subprocess  # nosec B404 - read-only gh api GETs
import sys
from collections import Counter
from pathlib import Path


def gh_get(path: str) -> list:
    cmd = ["gh", "api", "-X", "GET", "--paginate", path]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)  # nosec B603
    if proc.returncode != 0:
        raise SystemExit(f"gh failed ({proc.returncode}) for {path}: {proc.stderr.strip()[:300]}")
    # --paginate concatenates JSON arrays as ][; normalise.
    text = proc.stdout.strip().replace("]\n[", ",").replace("][", ",")
    return json.loads(text) if text else []


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeQL alert census for juniper-data")
    parser.add_argument("--repo", default="pcalnon/juniper-data")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    alerts = gh_get(f"repos/{args.repo}/code-scanning/alerts?tool_name=CodeQL&per_page=100")
    by_rule_state = Counter((a["rule"]["id"], a["state"]) for a in alerts)
    unused = [a for a in alerts if a["rule"]["id"] in ("py/unused-global-variable", "py/unused-local-variable")]
    in_tests = [a for a in alerts if "/tests/" in a["most_recent_instance"]["location"]["path"]]
    sec_file = [a for a in alerts if a["most_recent_instance"]["location"]["path"].endswith("tests/unit/test_security.py")]
    pytestmark_hits = [a for a in alerts if "pytestmark" in (a["most_recent_instance"].get("message", {}).get("text", ""))]
    analyses = gh_get(f"repos/{args.repo}/code-scanning/analyses?tool_name=CodeQL&per_page=5")
    summary = {
        "total_codeql_alerts_all_states": len(alerts),
        "states": dict(Counter(a["state"] for a in alerts)),
        "unused_rules": [
            {"number": a["number"], "rule": a["rule"]["id"], "state": a["state"], "path": a["most_recent_instance"]["location"]["path"], "line": a["most_recent_instance"]["location"]["start_line"], "message": a["most_recent_instance"].get("message", {}).get("text", "")[:160]}
            for a in unused
        ],
        "alerts_in_test_paths": [{"number": a["number"], "rule": a["rule"]["id"], "state": a["state"], "path": a["most_recent_instance"]["location"]["path"]} for a in in_tests],
        "alerts_in_test_security_py": [{"number": a["number"], "rule": a["rule"]["id"], "state": a["state"]} for a in sec_file],
        "alerts_naming_pytestmark": [{"number": a["number"], "rule": a["rule"]["id"], "state": a["state"], "path": a["most_recent_instance"]["location"]["path"]} for a in pytestmark_hits],
        "rule_state_counts": {f"{r}|{s}": c for (r, s), c in sorted(by_rule_state.items())},
        "recent_analyses": [{"ref": a.get("ref"), "created_at": a.get("created_at"), "category": a.get("category"), "results_count": a.get("results_count"), "tool": a.get("tool", {}).get("name")} for a in analyses[:5]],
    }
    Path(args.out).write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rule_state_counts"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
