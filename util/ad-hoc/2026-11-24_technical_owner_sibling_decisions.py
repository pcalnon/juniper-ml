#!/usr/bin/env python3
"""
The reviewed decisions of the sibling repos' technical-owner sweep: every token their rename PRs changed that is NOT the person.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration (the technical-owner sweep that follows the 2026-11-20..23 rename PRs)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_technical_owner_sibling_sweep.py (writes the candidate lists this reads);
    util/ad-hoc/2026-11-24_technical_owner_decisions.py (juniper-ml's decisions, the categories used here);
    util/ad-hoc/2026-11-24_technical_owner_restore.py (applies the list this writes, one repo at a time)

How the decisions were reached
------------------------------
The candidate lists (728 renamed tokens in 9 repos; 721 still renamed on each repo's ``origin/main`` of
2026-11-24 ~21:20Z, deploy#285 having restored the other 5 and canopy having rewritten 2 CHANGELOG lines since)
were reviewed row by row, every row, not only the ones a net flagged. Then three passes for the shapes
``classify`` cannot see: the words before and after each token, the generic determiners and qualifiers
("an owner", "the deployment owner", "its real owner"), and every token that starts or ends its line, read
together with the neighbouring line (the line-wrap blind spot: ``classify`` reads one line, so "away from its
real" + "# owner." on the next line read as the person; ``2026-11-24_technical_owner_sibling_sweep.py wrap``
reproduces that pass), plus a net over each repo's current main rather than the diff (``... shapes``). An
independent review of all 721 rows followed, briefed
with the data and the blind spots but not these decisions. It found the same ten tokens: the seven below and the
three recurrence publish lines (next section). Its seven unsure rows were judged the person: canopy
``.github/workflows/main-verify.yml:48`` ("a later per-repo owner call" is the owner's call, made per repo);
cascor ``src/tests/unit/test_candidate_epochs_completed_advisory.py:217`` and ``:408`` (a message and the test
needle that matches it, both renamed, so they still agree); and data
``util/ad-hoc/2026-09-15_equities_version_pin_bump.py:26``, ``:35``, ``:58`` and ``:59`` (anchors of a one-shot
script kept as provenance, which already ran). Ad-hoc scripts are code, not records, under the owner's ruling 2
of 2026-11-23, so their person renames stay, as juniper-ml#2606 kept them in juniper-ml.

Categories (as juniper-ml's): UNIX, GITHUB, CODE, FIELD, ROLE, GPG, TECH; PATH is a filename reference.

Where they landed: juniper-cascor#780, juniper-canopy#841 and juniper-recurrence#239, one GitHub-signed commit
each, built on that repo's ``origin/main`` of the same hour. The other six repos had no technical token left:
juniper-data (131 rows), juniper-data-client (38), juniper-cascor-client (34), juniper-cascor-worker (33),
juniper-harcot (118) and juniper-deploy (51; deploy#285 had restored the five others).

Deliberately NOT here
---------------------
juniper-recurrence ``.github/workflows/publish-recurrence-{app,model,client}.yml:22`` ("owner = pcalnon", the
trusted publisher's owner field) is GITHUB, but the one-artifact lane took it as a recurrence-port item on
2026-11-24 13:25Z, and the files are byte-pinned publish templates; this sweep does not duplicate it.

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_sibling_decisions.py --candidates-dir tmp/tech-owner-siblings
        writes <dir>/<repo>/restore_list.tsv for every repo with a decision
"""

from __future__ import annotations

import argparse
import os
import sys

# repo -> [(path, line in the rename merge, occurrence on the base line, category, reason)]
DECISIONS: dict[str, list[tuple[str, int, int, str, str]]] = {
    "juniper-cascor": [
        ("src/api/workers/coordinator.py", 469, 1, "TECH", "a task's owner: 'yank an in-flight assignment away from its real' / 'owner' (line wrap)"),
        ("util/ad-hoc/2026-11-08_stop_then_start_race_repro.py", 31, 1, "TECH", "the race's owner: 'the stale fit is still the owner when it settles' (juniper-ml restored its twin)"),
        ("docs/ci_cd/MANUAL.md", 392, 1, "ROLE", "'then an owner may promote it to a required context': whoever holds the ruleset ('an Overtoad' is no person)"),
    ],
    "juniper-canopy": [
        ("docs/deployment/KUBERNETES_DEPLOYMENT_PLAN.md", 1149, 1, "UNIX", "a secret's backup written owner-only (file mode), in a shell block"),
        ("docs/ENVIRONMENT_SETUP.md", 471, 1, "ROLE", "'the deployment owner has consciously attested': the operator role ('Each is an operator attestation')"),
        ("docs/ENVIRONMENT_SETUP.md", 1100, 1, "ROLE", "'the deployment' / 'owner has verified that perimeter' (line wrap): the operator role"),
    ],
    "juniper-recurrence": [
        ("juniper-recurrence-model/CHANGELOG.md", 22, 1, "PATH", "a filename: juniper-ml's HANDOFF_2026-11-06_recurrence-equities-0-8-1-published-owner-rulings-recorded-ml-floor-next.md"),
    ],
}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--candidates-dir", required=True)
    args = ap.parse_args(argv)
    total = 0
    for repo, decisions in sorted(DECISIONS.items()):
        rows = {}
        with open(os.path.join(args.candidates_dir, repo, "labelled.tsv"), encoding="utf-8") as handle:
            for raw in handle:
                row = raw.rstrip("\n").split("\t")  # label, status, where, occurrence, orig, got, nets, kind, window
                rows[(row[2], int(row[3]))] = row
        chosen = {}
        for path, line, occurrence, category, reason in decisions:
            key = (f"{path}:{line}", occurrence)
            if key not in rows:
                raise SystemExit(f"{repo}: NOT A RENAMED TOKEN: {key[0]} occurrence {occurrence}")
            if rows[key][0] != "LIVE":
                raise SystemExit(f"{repo}: NOT LIVE ON MAIN ({rows[key][0]}): {key[0]} occurrence {occurrence}")
            if key in chosen:
                raise SystemExit(f"{repo}: DUPLICATE DECISION: {key[0]} occurrence {occurrence}")
            chosen[key] = (category, reason)
        out = ["path\tline\toccurrence\tbase\thead\tcategory\treason\tkind\twindow"]
        for (where, occurrence), (category, reason) in sorted(chosen.items(), key=lambda kv: (kv[0][0].rsplit(":", 1)[0], int(kv[0][0].rsplit(":", 1)[1]), kv[0][1])):
            row = rows[(where, occurrence)]
            path, line = where.rsplit(":", 1)
            out.append("\t".join((path, line, str(occurrence), row[4], row[5], category, reason, row[7], row[8])))
        target = os.path.join(args.candidates_dir, repo, "restore_list.tsv")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("\n".join(out) + "\n")
        total += len(chosen)
        print(f"{repo}: {len(chosen)} token(s) in {len({w.rsplit(':', 1)[0] for w, _ in chosen})} file(s) -> {target}")
    print(f"total {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
