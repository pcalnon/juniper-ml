# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-F: _merge_session and render_session on cascor's real session (the KeyError).
# Source: session ddf7847c's tmpfs scratchpad, r2f.xB7Gf1/forkE/probe_merge.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
# Ephemeral read-only probe (Lane R2-F fork E): canopy e9053227 _merge_session vs cascor-shaped envelopes.
import ast
import copy

D = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/ddf7847c-b365-4e53-aaa2-3e68203684bd/scratchpad/r2f.xB7Gf1/forkE/"
src = open(D + "replay_player_panel_e905.py").read()
tree = ast.parse(src)
cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ReplayPlayerPanel"][0]
ns = {"SPEED_DEFAULT": 1.0}
exec("from typing import Any, Dict, Optional", ns)
methods = {}
for fn in cls.body:
    if isinstance(fn, ast.FunctionDef) and fn.name in ("_merge_session", "_session_summary", "_session_current_index", "_session_window"):
        f2 = copy.deepcopy(fn)
        f2.decorator_list = []
        exec(compile(ast.Module(body=[f2], type_ignores=[]), "x", "exec"), ns)
        methods[fn.name] = ns[fn.name]
reg = [fn for fn in cls.body if isinstance(fn, ast.FunctionDef) and fn.name == "register_callbacks"][0]
rs = [n for n in ast.walk(reg) if isinstance(n, ast.FunctionDef) and n.name == "render_session"][0]
rs2 = copy.deepcopy(rs)
rs2.decorator_list = []


class S:
    pass


s = S()
for k, v in methods.items():
    setattr(s, k, v)
ns["self"] = s
exec(compile(ast.Module(body=[rs2], type_ignores=[]), "y", "exec"), ns)
render = ns["render_session"]
merge = methods["_merge_session"]

SID = "snap_A"


def summ(speed=1.0, ti=0, paused=True, range_as="dict"):
    r = {"start": 0, "end": 100} if range_as == "dict" else [0, 100]
    return {"snapshot_id": SID, "length": 100, "time_index": ti, "speed": speed, "paused": paused, "range": r, "weights_available": False}


def start_session(range_as):
    # as confirm_snapshot_op builds it from cascor's POST /replay data block
    d = {"snapshot_id": SID, "operation": "replay", "fsm_state": "REPLAYING", "time_index": {"default": "start", "snapshot_window": {"start_epoch": 0, "end_epoch": 99}}, "status": "replaying", "session": summ(range_as=range_as)}
    d.setdefault("snapshot_id", SID)
    d.setdefault("speed", 1.0)
    d.setdefault("playing", False)
    return d


def env(action, result, stop=False, echo=True):
    data = {"operation": "replay_control", "action": action, "result": result}
    if echo:
        data["snapshot_id"] = SID
    if stop:
        data["fsm_state"] = "STOPPED"
    return {"status": "success", "data": data, "meta": {"timestamp": "t", "version": "v"}}


for range_as in ("dict", "list"):
    sess = start_session(range_as)
    print("== session range shape:", range_as)
    try:
        r0 = render(sess)
        print("   render(initial): sid=%r fsm=%r cur=%r speed=%r" % (r0[2], r0[3], r0[6], r0[12]))
    except Exception as e:
        print("   render(initial) raised %s: %s" % (type(e).__name__, e))
    cases = [
        ("speed", {"value": -5.0}, env("speed", summ(speed=-5.0, paused=False, range_as=range_as))),
        ("seek", {"time_index": 40}, env("seek", summ(ti=40, range_as=range_as))),
        ("play", {}, env("play", summ(paused=False, range_as=range_as))),
        ("stop", {}, env("stop", {"status": "stopped", "snapshot_id": SID}, stop=True)),
        ("stop(no-echo)", {}, {"status": "success", "data": {"operation": "replay_control", "action": "stop", "result": {"status": "stopped"}, "fsm_state": "STOPPED"}, "meta": {}}),
        ("stop(empty)", {}, {}),
        ("stop(None)", {}, None),
        ("speed(flat)", {"value": -5.0}, {"speed": -5.0}),
    ]
    for name, params, data in cases:
        action = name.split("(")[0]
        new = merge(sess, action, params, data)
        inner = methods["_session_summary"](new)
        ti = new.get("time_index")
        tic = ti.get("current") if isinstance(ti, dict) else ti
        try:
            r = render(new)
            rend = "idle=%s sid=%r fsm=%r cur=%r speed=%r" % (r[0].get("display") == "block", r[2], r[3], r[6], r[12])
        except Exception as e:
            rend = "render raised %s: %s" % (type(e).__name__, e)
        print("   %-14s snapshot_id=%r fsm_state=%r playing=%r top.speed=%r inner.speed=%r time_index.current=%r | %s" % (name, new.get("snapshot_id"), new.get("fsm_state"), new.get("playing"), new.get("speed"), inner.get("speed"), tic, rend))
e = env("stop", {})
print("envelope top-level keys:", sorted(e.keys()))
print("session top-level keys:", sorted(start_session("dict").keys()))
