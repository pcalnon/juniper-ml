#!/usr/bin/env python3
"""Census the pilot probe runs that never entered the soak ledger, and screen them.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Why this exists
---------------
§5 of
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_soak-arc-evidence-recovered-predictors-refuted.md``
carries an open question: 57 transcripts describe a probe run, 40 bind to a ledger
observation, and of the 17 that do not, **10 have no recorded basis** -- "a selection question
upstream of every rate here".

This answers it mechanically rather than by argument: it reproduces the census, splits the
unbound runs by whether ``conf/soak_probes.json``'s ``retired`` block records a reason, and
runs the contamination screen over the ones it does not.

THE ID MATCH IS THE WHOLE TRICK, and getting it wrong is how the handoff's own §10 records an
earlier draft reaching "17, ~30%, no recorded basis". ``discover_transcripts()`` keys on the
3-character description head (``P17``) while the registry stores full slugs
(``P17-conda-activate-restore-arm``); comparing them directly matches nothing, every unbound
run reads as unexplained, and the wrong number looks exactly as confident as the right one.
``_full_id`` resolves the number to the slug, and ``--self-check`` fails loudly if that
resolution ever silently stops working.

Findings recorded in
``notes/JUNIPER_2026-09-10_JUNIPER-ML_SOAK-DISCARDED-RUN-SELECTION-ANALYSIS.md``.

Usage
-----
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/discarded_run_census.py
    python3 util/ad-hoc/2026-09-10_soak_stopping_rule/discarded_run_census.py --self-check

Read-only. Modifies no ledger, runs no probe.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
BINDER = REPO_ROOT / "util" / "ad-hoc" / "2026-09-08_soak_label_to_transcript.py"
SCREEN = REPO_ROOT / "util" / "ad-hoc" / "2026-08-21_soak_probe_evidence.py"
LEDGER = REPO_ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"
REGISTRY = REPO_ROOT / "conf" / "soak_probes.json"


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # before exec_module: a @dataclass resolves __module__ here
    spec.loader.exec_module(mod)
    return mod


def _full_id(num: str, retired: dict, live: set) -> str:
    """``P17`` -> ``P17-conda-activate-restore-arm``. See the docstring's warning."""
    for cand in list(retired) + sorted(live):
        if cand.startswith(num + "-"):
            return cand
    return f"{num}-<NOT IN REGISTRY>"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-check", action="store_true",
                    help="fail if the number->slug resolution is not working")
    args = ap.parse_args()

    binder = _load(BINDER, "soak_binder")
    screen = _load(SCREEN, "soak_screen")

    transcripts = binder.discover_transcripts()
    rows = binder.load_ledger(LEDGER)
    bound = binder.bind(rows, transcripts)
    used = {e["transcript"] for e in bound if e.get("transcript")}

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    retired = {e["probe_id"]: e for e in registry["retired"]}
    live = {p["probe_id"] for p in registry["probes"]}

    if args.self_check:
        # A silently-broken resolver returns the "<NOT IN REGISTRY>" sentinel for
        # everything, which reports every unbound run as unexplained -- the exact
        # error this guard exists to make loud.
        unresolved = [n for n in transcripts if _full_id(n, retired, live).endswith("<NOT IN REGISTRY>")]
        if unresolved:
            print(f"SELF-CHECK FAILED: {len(unresolved)} probe numbers resolve to nothing: "
                  f"{sorted(unresolved)}", file=sys.stderr)
            return 1
        print(f"self-check OK: all {len(transcripts)} probe numbers resolve to a registry slug")
        return 0

    all_paths = [d["path"] for runs in transcripts.values() for d in runs]
    unbound: list[tuple[str, object]] = []
    for num, runs in sorted(transcripts.items()):
        fid = _full_id(num, retired, live)
        for d in runs:
            if d["path"] not in used:
                unbound.append((fid, d))

    print("=" * 84)
    print("soak: pilot probe runs that never entered the ledger -- 2026-09-10")
    print("=" * 84)
    print(f"probe-id transcripts : {len(all_paths)}")
    print(f"bound to a row       : {len(all_paths) - len(unbound)}")
    print(f"unbound              : {len(unbound)}")
    print()

    with_reason = [(f, d) for f, d in unbound if f in retired]
    no_reason = [(f, d) for f, d in unbound if f not in retired]
    print(f"unbound WITH a recorded retirement reason : {len(with_reason)}")
    for fid, _ in sorted(with_reason):
        print(f"    {fid:<40} retired {retired[fid]['retired_on']}")
    print()
    print(f"unbound with NO recorded basis            : {len(no_reason)}"
          f"   ({len(no_reason) / len(all_paths) * 100:.1f}% of {len(all_paths)})")
    print()
    print(f"    {'probe':<36} {'run mtime':<18} {'contam':<7} {'retrieved':<10} ledger")
    contaminated = retrieved = 0
    for fid, d in sorted(no_reason, key=lambda x: (x[0], x[1]["mtime"])):
        r = screen.scan(d["path"])
        contaminated += bool(r["contaminated"])
        retrieved += bool(r["retrieved"])
        led = "CONTENT" if r["ledger_content_read"] else ("filename" if r["ledger_touched"] else "-")
        print(f"    {fid:<36} {d['mtime'].strftime('%Y-%m-%dT%H:%M'):<18} "
              f"{str(r['contaminated']):<7} {str(r['retrieved']):<10} {led}")

    n = len(no_reason)
    print()
    print(f"  contaminated : {contaminated}/{n}"
          f"{'  -- the discard IS principled; only the per-run REASON is unrecorded' if contaminated == n else ''}")
    print(f"  retrieved    : {retrieved}/{n} = {retrieved / n * 100:.1f}%"
          "   (compare the scored corpus's mechanism-checked 24/43 = 55.8%)")
    if n and retrieved / n > 24 / 43:
        print("  => the discarded set skews TOWARD retrieval, so including it would RAISE the")
        print("     pooled rate. The exclusion moves the estimate AWAY from the 0.75 boundary;")
        print("     it cannot have manufactured the BET-FAILING verdict.")

    # The ledger-leak sweep over the FULL transcript set, not just the scored corpus.
    c = f = 0
    for p in all_paths:
        r = screen.scan(p)
        if r["ledger_content_read"]:
            c += 1
        elif r["ledger_touched"]:
            f += 1
    print()
    print(f"ledger exposure over ALL {len(all_paths)} transcripts: content={c} filename={f} touched={c + f}")
    print("  (the scored 43-row corpus is content=1 filename=7 touched=8; the extra content")
    print("   reads are already-discarded runs, so owner decision 8 governs ONE scored row)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
