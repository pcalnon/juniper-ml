# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: the synthetic Dash app with the first fix's exact wiring, driven on the real renderer (the F-CANOPY-058 repro).
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/repro_f055.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Synthetic repro of the F-CANOPY-055 fix's wiring against the real dash 4.2.0 renderer.

NOT canopy. A minimal Dash app that copies the fix's shape:
  * ``lane``  -- dcc.Interval(1000 ms), the ``status-bar-interval`` analogue;
  * feeder    -- server callback, sole Input ``lane.n_intervals``,
                 ``running=[(Output('lane','disabled'), True, False)]``, prevent_initial_call=False,
                 server latency R (+ optional uniform jitter);
  * gate      -- (REPRO_GATE=1) clientside, Inputs apply-in-flight.data + tabs.value, writes
                 lane.disabled with canopy's per-lane expression for a tab===null lane;
  * watchdog  -- (REPRO_WATCHDOG=1) the status-bar strand watchdog JS copied VERBATIM from the
                 built fix app (fix/fix_callbacks.json), on a 5000 ms slow lane, 30000 ms timeout.

Applies are recorded by a MutationObserver on #out (independent of the Dash callback queue).
Requests are recorded server-side (seq, start, end). Each response carries its seq, so a request
whose seq never appears in #out was dropped by the renderer.

usage: python repro_f055.py <scenario> <seconds> [click_after_dispatch_s]
  scenario: control | gate-click | watchdog
"""

import json
import os
import random
import re
import sys
import threading
import time

import dash
from dash import Input, Output, State, dcc, html
from flask import jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("REPRO_PORT", "18655"))
R = float(os.environ.get("REPRO_R", "3.0"))
JITTER = float(os.environ.get("REPRO_JITTER", "0.0"))
GATE = os.environ.get("REPRO_GATE", "0") == "1"
# REPRO_GATE_MOUNT=0 -> the gate does not run at mount (isolates a later gate fire).
GATE_MOUNT = os.environ.get("REPRO_GATE_MOUNT", "1") == "1"
WATCHDOG = os.environ.get("REPRO_WATCHDOG", "0") == "1"

scenario = sys.argv[1]
duration = float(sys.argv[2])
click_after = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

T0 = time.time()
lock = threading.Lock()
seq = {"n": 0}
log = []  # [seq, t_start, t_end] relative to T0

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div(
    [
        dcc.Interval(id="lane", interval=1000, n_intervals=0),
        dcc.Interval(id="slow", interval=5000, n_intervals=0),
        dcc.Store(id="apply-in-flight", data=False),
        dcc.Tabs(id="tabs", value="a", children=[dcc.Tab(label="A", value="a", id="tab-a"), dcc.Tab(label="B", value="b", id="tab-b")]),
        html.Div(id="out", children="init"),
        html.Button("apply", id="apply-btn"),
        html.Button("release", id="release-btn"),
    ]
)

# canopy's apply-clamp writers (dashboard_manager.py:4189-4213): click arms, release clears.
app.clientside_callback(
    """function(n){ if (!n) return window.dash_clientside.no_update; return {in_flight: true, since: Date.now()}; }""",
    Output("apply-in-flight", "data"),
    Input("apply-btn", "n_clicks"),
    prevent_initial_call=True,
)
app.clientside_callback(
    """function(n){ if (!n) return window.dash_clientside.no_update; return false; }""",
    Output("apply-in-flight", "data", allow_duplicate=True),
    Input("release-btn", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(Output("out", "children"), Input("lane", "n_intervals"), running=[(Output("lane", "disabled"), True, False)], prevent_initial_call=False)
def feeder(n):
    with lock:
        seq["n"] += 1
        k = seq["n"]
    t0 = time.time() - T0
    time.sleep(R + (random.uniform(0.0, JITTER) if JITTER else 0.0))
    log.append([k, round(t0, 3), round(time.time() - T0, 3)])
    return f"seq={k}"


if GATE:
    # canopy's gate body (dashboard_manager.py:2481-2489) with tabs = [null]: one global lane.
    app.clientside_callback(
        """
        function(inFlight, activeTab) {
            var clamped = Boolean(inFlight);
            var tabs = [null];
            return tabs.map(function (tab) {
                return clamped || (tab !== null && tab !== activeTab);
            });
        }
        """,
        [Output("lane", "disabled")],
        [Input("apply-in-flight", "data"), Input("tabs", "value")],
        prevent_initial_call=not GATE_MOUNT,
    )

WATCHDOG_FN = None
if WATCHDOG:
    dump = json.load(open(os.path.join(HERE, "fix", "fix_callbacks.json"), encoding="utf-8"))
    rec = [r for r in dump["records"] if r["output"].startswith("status-bar-interval.disabled@")]
    assert len(rec) == 1
    fn = rec[0]["clientside"]["function_name"]
    script = [s for s in dump["inline_scripts"] if fn in s][0]
    marker = f'ns["{fn}"] = '
    body = script[script.index(marker) + len(marker) : script.rindex("})();")]
    body = body.rstrip().rstrip(";").rstrip()
    assert body.strip().startswith("function(n, disabled, applyInFlight)"), body[:60]
    assert "__statusBarDisabledSince" in body and "30000" in body
    app.clientside_callback(
        body,
        Output("lane", "disabled", allow_duplicate=True),
        Input("slow", "n_intervals"),
        [State("lane", "disabled"), State("apply-in-flight", "data")],
        prevent_initial_call=True,
    )
    import hashlib

    WATCHDOG_FN = hashlib.sha256(body.encode("utf-8")).hexdigest()


@app.server.route("/stats")
def stats():
    return jsonify(log=list(log), seq=seq["n"])


def serve():
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False, threaded=True)


threading.Thread(target=serve, daemon=True).start()
time.sleep(2.0)

from playwright.sync_api import sync_playwright  # noqa: E402

INIT = """
window.__mut = [];
window.__wd = [];
new MutationObserver(function(){}).disconnect();
document.addEventListener('DOMContentLoaded', function () {
  var attach = function () {
    var el = document.getElementById('out');
    if (!el) { setTimeout(attach, 20); return; }
    window.__mut.push([performance.timeOrigin + performance.now(), el.textContent]);
    new MutationObserver(function () {
      window.__mut.push([performance.timeOrigin + performance.now(), el.textContent]);
    }).observe(el, {childList: true, characterData: true, subtree: true});
  };
  attach();
});
"""

WRAP = """
(fn) => {
  var ns = window.dash_clientside._dashprivate_clientside_funcs;
  var orig = ns[fn];
  ns[fn] = function (n, disabled, applyInFlight) {
    var out = orig(n, disabled, applyInFlight);
    if (out === false) { window.__wd.push([Date.now(), disabled]); }
    return out;
  };
  return typeof orig;
}
"""

feeder_reqs = []  # [t_rel_start]
result = {"scenario": scenario, "R": R, "jitter": JITTER, "gate": GATE, "gate_mount": GATE_MOUNT, "watchdog": WATCHDOG, "click_after": click_after, "feeder_posts_seen_by_browser": None}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script(INIT)

    def on_request(req):
        if "_dash-update-component" in req.url and req.post_data and '"output":"out.children"' in req.post_data:
            feeder_reqs.append(round(time.time() - T0, 3))

    page.on("request", on_request)
    page.goto(f"http://127.0.0.1:{PORT}/")
    page.wait_for_selector("#out")
    t_load = time.time() - T0
    if WATCHDOG_FN:
        result["wrap"] = page.evaluate(WRAP, WATCHDOG_FN)
    click_t = None
    if scenario == "gate-click":
        # settle, then click tab B `click_after` seconds after a feeder request is dispatched.
        # page.wait_for_timeout (not time.sleep) so Playwright pumps its request events.
        page.wait_for_timeout(int(float(os.environ.get("REPRO_SETTLE", "12")) * 1000))
        n0 = len(feeder_reqs)
        give_up = time.time() + 30
        while len(feeder_reqs) == n0 and time.time() < give_up:
            page.wait_for_timeout(10)
        page.wait_for_timeout(int(click_after * 1000))
        page.click("#tab-b")
        click_t = round(time.time() - T0, 3)
    if scenario == "apply-click":
        page.wait_for_timeout(int(float(os.environ.get("REPRO_SETTLE", "12")) * 1000))
        n0 = len(feeder_reqs)
        give_up = time.time() + 30
        while len(feeder_reqs) == n0 and time.time() < give_up:
            page.wait_for_timeout(10)
        page.wait_for_timeout(int(click_after * 1000))
        page.click("#apply-btn")
        click_t = round(time.time() - T0, 3)
        page.wait_for_timeout(int(float(os.environ.get("REPRO_HOLD", "11")) * 1000))
        page.click("#release-btn")
        result["release_t"] = round(time.time() - T0, 3)
    end = time.time() + duration
    while time.time() < end:
        page.wait_for_timeout(500)
    mut = page.evaluate("window.__mut")
    wd = page.evaluate("window.__wd")
    result["feeder_posts_seen_by_browser"] = feeder_reqs
    browser.close()

import urllib.request  # noqa: E402

srv = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/stats").read())
applied_seqs = []
applied_t = {}
for t_ms, text in mut:
    m = re.match(r"seq=(\d+)", text or "")
    if m:
        k = int(m.group(1))
        if k not in applied_t:
            applied_seqs.append(k)
            applied_t[k] = round(t_ms / 1000.0 - T0, 3)
rows = []
for k, ts, te in srv["log"]:
    rows.append({"seq": k, "start": ts, "end": te, "applied_at": applied_t.get(k)})
result.update(
    t_load=round(t_load, 3),
    click_t=click_t,
    watchdog_fires=[round(t / 1000.0 - T0, 3) for t, _d in wd],
    n_requests=len(rows),
    n_applied=sum(1 for r in rows if r["applied_at"] is not None),
    timeline=rows,
)
if click_t is not None:
    after = [r for r in rows if r["start"] >= click_t - 0.001 or (r["end"] >= click_t)]
    result["after_click_requests"] = len(after)
    result["after_click_applied"] = sum(1 for r in after if r["applied_at"] is not None)
if result["watchdog_fires"]:
    f0 = result["watchdog_fires"][0]
    after = [r for r in rows if r["end"] >= f0]
    result["after_first_fire_requests"] = len(after)
    result["after_first_fire_applied"] = sum(1 for r in after if r["applied_at"] is not None)
if "release_t" in result and click_t is not None:
    rel = result["release_t"]
    result["requests_dispatched_while_clamped"] = [r["seq"] for r in rows if click_t < r["start"] < rel]
    after_rel = [r for r in rows if r["end"] > rel]
    result["after_release_requests"] = len(after_rel)
    result["after_release_applied"] = sum(1 for r in after_rel if r["applied_at"] is not None and r["applied_at"] > rel)
out_file = os.environ.get("REPRO_OUT")
if out_file:
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
# Each watchdog fire, with the request(s) in flight at that instant (server-side intervals).
for f in result["watchdog_fires"]:
    inflight = [r["seq"] for r in rows if r["start"] <= f <= r["end"]]
    print(f"WATCHDOG FIRE t={f:.3f}  in-flight seq={inflight}")
print(json.dumps({k: v for k, v in result.items() if k not in ("timeline", "feeder_posts_seen_by_browser")}))
print("seq  start    end      applied_at")
for r in rows:
    print(f"{r['seq']:>3}  {r['start']:>7.3f}  {r['end']:>7.3f}  {r['applied_at'] if r['applied_at'] is not None else 'DROPPED'}")
