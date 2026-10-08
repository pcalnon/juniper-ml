# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/synth_pred.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: would a broken shim pass the synthetic check? Feed the check's OWN pass predicates (read out of the
frozen file by AST, not retyped) the re-run's records, mutated the way four broken shims would report them."""
import ast
import copy
import json
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
src = (S / "frozen/util/ad-hoc/2026-10-04_f058_census_v2_synth_check.py").read_text(encoding="utf-8")
tree = ast.parse(src)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
cases = next(n for n in main.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "cases").value
PRED = {}
for elt in cases.elts:
    name = elt.elts[0].value
    PRED[name] = eval(compile(ast.Expression(elt.elts[4]), "<pred>", "eval"))  # noqa: S307 - the frozen file's own lambda
rows = [json.loads(line) for line in (S / "synth_run/synth_check.jsonl").read_text().splitlines() if line.startswith("{")]
R = {r["case"]: r for r in rows}
print("as run:", {k: PRED[k](R[k]) for k in PRED})


def mutate(name, fn):
    r = copy.deepcopy(R[name])
    fn(r)
    return PRED[name](r)


def v1_noupdate_as_x(r):  # v1: every answer without props read EVICTED
    st = r["stats"]
    st["evicted"] += st["answered"] - st["answered_with_props"]
    st["answered"] = st["answered_with_props"]


def blind_to_x(r):  # never records X: evictions read as answered
    st = r["stats"]
    st["answered"] += st["evicted"]
    st["evicted"] = 0
    if r.get("after_first_fire"):
        r["after_first_fire"]["answered"] += r["after_first_fire"]["evicted"]
        r["after_first_fire"]["evicted"] = 0


def lane_after(r):  # v1: the lane read AFTER the fire's own write
    r["fires"] = [[t, False, s] for t, b, s in r["fires"]]


def first_fire_only(r):  # catches only the first fire
    r["fires"] = r["fires"][:1]


def spurious_x_after_reenable(r):  # answered requests read X only after a re-enable (no such event in the controls)
    pass  # the trigger cases already read 100% X; a shim inventing X there passes by construction


print("v1 no_update-as-X  on noupdate-control:", mutate("noupdate-control", v1_noupdate_as_x), "| on data-control:", mutate("data-control", v1_noupdate_as_x))
print("blind to X         on data-mode / noupdate-mode / mount-cascade / watchdog:", [mutate(k, blind_to_x) for k in ("data-mode", "noupdate-mode", "mount-cascade", "watchdog")])
print("lane read after fire on watchdog:", mutate("watchdog", lane_after))
print("first fire only    on watchdog:", mutate("watchdog", first_fire_only), "(the check passes; it needs >= 1 fire, not the 5 a 5 s sampler and STRAND_MS 8000 give in 78 s)")
print("watchdog fire times:", [f[0] for f in R["watchdog"]["fires"]], "spacing", [b[0] - a[0] for a, b in zip(R["watchdog"]["fires"], R["watchdog"]["fires"][1:])])
print("data cases: store values vs answers -> data-mode store_distinct", R["data-mode"]["store_distinct_nonnull"], "answered after trigger", R["data-mode"]["stats"]["answered"], "; mount-cascade", R["mount-cascade"]["store_distinct_nonnull"], R["mount-cascade"]["stats"]["answered"], "; watchdog", R["watchdog"]["store_distinct_nonnull"], R["watchdog"]["stats"]["answered"])
