#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""One live growth run, three tabs, four owed observations.

WHY ONE PROBE. A cascade growth run on the shared fixture is the scarce resource
of this arc: the fixture is grown, never rebuilt (``POST /v1/network`` destroys
it), so each run is a few minutes that come round only when the cap is raised.
Four items in the ledger's "still owed" list all need a LIVE run and nothing
else, and they have been waiting since 2026-08-27 for one:

  F-CANOPY-036   the candidate-pool history must ACCUMULATE in the live lane now
                 that canopy#536 moved the accumulation server-side. Owed: a run
                 with the Candidate Metrics tab open. Scores M-CANDIDATES-09.
  M-CANDIDATES-10/-11
                 the per-epoch history card header click and its collapse are
                 ``DEAD-EXPECTED``; the terminal ``DEAD-CONFIRMED`` needs a real
                 card to click, which needs the accumulation above.
  F-CANOPY-026   phase duration must read the run's real elapsed time, not the
                 host's UTC offset. Both fix halves merged 2026-08-28 (cascor#594,
                 canopy#534) and the live confirmation needs a MID-RUN sample:
                 ``phase_started_at`` is cleared at completion, so a post-run read
                 is ``None`` and proves nothing.
  M-TOPOLOGY-16  the cascade-add glow, a visual highlight on a newly installed
                 hidden unit. Needs a real ``cascade_add``.

So: one browser, three pages -- Candidate Metrics, Training Metrics, Network
Topology -- each left OPEN for the whole run, because every per-tab poll lane
gates on ``visualization-tabs.active_tab`` and a closed tab measures nothing.

WHAT IS SAMPLED, every ``--every`` seconds until cascor reports COMPLETED (plus
a grace period), then written as one JSON artifact:

  cascor      ``/v1/training/status``: FSM status, phase, ``phase_started_at``,
              hidden units, epoch. The oracle for everything below; read off the
              service, never through canopy.
  candidates  history-card count in the DOM, ``-pool-history-store`` length, the
              status badge. Card count rising from 0 is F-036's live confirmation.
  metrics     the ``metrics-panel-phase-duration`` text, paired with the oracle's
              ``phase_started_at`` read in the same sample, so the displayed
              duration can be checked against wall-clock elapsed.
  topology    the stats-bar hidden count, the ``ws-cascade-add-buffer`` ``gen``,
              and whether a trace named ``New Unit Glow`` exists on the graph.
  f035        the length of ``metrics-panel-metrics-store`` on the topology page.
              Not a scored row; recorded because the WS-primary append path
              (``append_ws_metrics_store``) is only live DURING training, and
              whether the store fills through it is evidence F-035 has never had.

READING RULES, fixed before the run.

  M-CANDIDATES-09  PASS iff at least one history card rendered while the run was
                   live AND the store length agrees (>= 1). FAIL if the oracle
                   reported a candidate phase and no card ever rendered.
  M-CANDIDATES-10  DEAD-CONFIRMED iff a card existed, its header was clicked, and
                   neither its collapse class/height changed nor any callback
                   request named the header/collapse ids. If the collapse DID
                   open, that is a surprise: score PASS and say so.
  M-CANDIDATES-11  follows -10 (the collapse is what -10's click would drive).
  F-CANOPY-026     CLOSED-BY-VERIFICATION iff every mid-run sample's displayed
                   duration is within ``--tolerance`` seconds of the oracle's
                   elapsed. The old defect is off by the host's UTC offset
                   (~18,000 s here), so the tolerance is not delicate.
  M-TOPOLOGY-16    PASS iff a ``New Unit Glow`` trace appeared within 60 s of a
                   server-side hidden-unit increase. If the server grew and the
                   DOM count followed but no glow trace EVER appeared, report
                   BLOCKED with the reason the source gives: the detector
                   (``network_visualizer.py:562-568``) reads ``hidden_units``
                   deltas out of ``metrics-panel-metrics-store`` -- the F-035
                   store -- so an empty store makes the glow unreachable.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-08_live_run_probe.py --budget 1200
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")
_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
dismiss_welcome = _w3.dismiss_welcome
open_dashboard = _seg17.open_dashboard
_store = _seg17._store
counts = _seg17.counts
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal
vis = _f027.vis
fig_info = _f027.fig_info
shot = _f027.shot
CID = _f027.CID

CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202")
OUT = os.environ.get("LIVE_RUN_RESULTS", "/tmp/juniper-e2e/live_run_probe.json")

METRICS_STORE = "metrics-panel-metrics-store"
GLOW_TRACES = ("New Unit Glow", "New Unit Edges")
PHASE_DURATION = "metrics-panel-phase-duration"
BUFFER = "ws-cascade-add-buffer"
GRAPH = "network-visualizer-graph"

_DUR_RE = re.compile(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?")


def _cascor_status() -> dict:
    """The oracle. Read off cascor, never through canopy."""
    try:
        with urllib.request.urlopen(f"{CASCOR}/v1/training/status", timeout=8) as r:  # noqa: S310
            d = (json.loads(r.read().decode()) or {}).get("data") or {}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}"[:100]}
    sm = d.get("state_machine") or {}
    ts = d.get("training_state") or {}
    mon = d.get("monitor") or {}
    return {
        "ok": True,
        "fsm": sm.get("status"),
        "phase": ts.get("phase"),
        "status": ts.get("status"),
        "phase_started_at": ts.get("phase_started_at") or None,
        "hidden": mon.get("current_hidden_units"),
        "epoch": ts.get("current_epoch"),
        "cand_epoch": ts.get("candidate_epoch"),
        "cand_total": ts.get("candidate_total_epochs"),
        "candidates_trained": ts.get("candidates_trained"),
    }


def _cascor_hidden() -> int | None:
    try:
        with urllib.request.urlopen(f"{CASCOR}/v1/network", timeout=8) as r:  # noqa: S310
            return ((json.loads(r.read().decode()) or {}).get("data") or {}).get("hidden_units")
    except Exception:  # noqa: BLE001
        return None


def _parse_duration(text: str) -> float | None:
    """``Phase Duration: 2m 29s`` -> 149.0; anything unparseable -> None."""
    if not text:
        return None
    tail = text.split(":", 1)[1] if ":" in text else text
    m = _DUR_RE.search(tail.strip())
    if not m or not any(m.groups()):
        return None
    h, mi, s = (int(g) if g else 0 for g in m.groups())
    return float(h * 3600 + mi * 60 + s)


def _elapsed_since(iso: str) -> float | None:
    try:
        started = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return None
    if started.tzinfo is None:
        # cascor#594 emits tz-aware UTC; a naive value here would itself be the
        # F-026 regression, so record it as such rather than guess a zone.
        return None
    return (datetime.now(timezone.utc) - started).total_seconds()


def _cards(page) -> int:
    return page.evaluate("""() => document.querySelectorAll('[id*="history-pool-header"]').length""")


def _first_card(page) -> dict:
    return page.evaluate(
        """() => { const h = document.querySelector('[id*="history-pool-header"]');
             if (!h) return {present:false};
             const c = h.closest('.card'); const col = c ? c.querySelector('.collapse') : null;
             return {present:true, header_id:h.id, text:(h.innerText||'').trim().slice(0,120),
                     collapse_cls: col ? col.className : null,
                     collapse_h: col ? Math.round(col.getBoundingClientRect().height) : null}; }"""
    )


def _glow(page) -> dict:
    """Trace NAMES only. ``fig_info`` hashes the whole figure (``JSON.stringify(gd.data)``),
    which on a 944-connection graph cost ~20 s per call and left the first growth run with
    three samples in 50 s; the glow question needs only the trace-name list."""
    return page.evaluate(
        """(a) => { const [id, names] = a; const root = document.getElementById(id);
             if (!root) return {present:false, n_traces:0, glow:[]};
             const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
             if (!gd || !gd.data) return {present:true, n_traces:0, glow:[]};
             const out = []; for (const t of gd.data) { if (names.indexOf(t.name || '') !== -1) out.push(t.name); }
             return {present:true, n_traces: gd.data.length, glow: out}; }""",
        [GRAPH, list(GLOW_TRACES)],
    )


def _store_len(page, store_id: str):
    rd = _store(page, store_id) or {}
    v = rd.get("value")
    if isinstance(v, list):
        return len(v)
    if isinstance(v, dict):
        return v.get("gen") if "gen" in v else f"<dict:{len(v)}>"
    return None if v is None else f"<{type(v).__name__}>"


def _open_second_page(ctx, label: str, capture: list, tag: str):
    page = ctx.new_page()

    def on_request(req):
        if "_dash-update-component" in req.url:
            try:
                body = req.post_data or ""
            except Exception:  # noqa: BLE001
                body = ""
            capture.append({"t": round(time.time(), 3), "page": tag, "body": body[:600]})

    page.on("request", on_request)
    page.on("console", lambda m: log(f"  [{tag}] CONSOLE[{m.type}] {m.text[:200]}") if m.type == "error" else None)
    page.goto(CANOPY, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)
    dismiss_welcome(page)
    page.wait_for_timeout(1500)
    ensure_no_modal(page)
    ok = open_tab(page, label)
    log(f"  [{tag}] tab {label!r} opened={ok}")
    return page


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--budget", type=float, default=1200.0, help="seconds to watch at most")
    ap.add_argument("--every", type=float, default=2.0, help="sampling period, seconds")
    ap.add_argument("--grace", type=float, default=45.0, help="seconds to keep sampling after COMPLETED")
    ap.add_argument("--tolerance", type=float, default=20.0, help="F-026: allowed |displayed - elapsed| in seconds")
    ap.add_argument("--no-click", action="store_true", help="skip the M-CANDIDATES-10 header click at the end")
    ap.add_argument(
        "--start",
        action="store_true",
        help=(
            "POST /v1/training/start on cascor AFTER the three tabs are open, so the run's first "
            "candidate phase is not spent while the pages are still loading. The cap, the staged "
            "dataset and the FSM state are the operator's business and are set BEFORE this runs; the "
            "probe only presses Start and records cascor's reply."
        ),
    )
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    res: dict = {
        "canopy": CANOPY,
        "cascor": CASCOR,
        "serving": serving_commit(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "start_hidden": _cascor_hidden(),
        "samples": [],
        "events": [],
        "f026_samples": [],
        "glow_first_seen": None,
        "cards_first_seen": None,
        "server_growth": [],
        "dom_growth": [],
        "store_len_seq": [],
    }
    log(f"serving: {json.dumps(res['serving'])}")
    log(f"start: cascor hidden={res['start_hidden']} status={_cascor_status()}")

    with sync_playwright() as pw:
        browser, ctx, page_c = open_dashboard(pw, capture)
        try:
            open_tab(page_c, "Candidate Metrics")
            page_m = _open_second_page(ctx, "Training Metrics", capture, "metrics")
            page_t = _open_second_page(ctx, "Network Topology", capture, "topology")
            page_c.wait_for_timeout(2000)

            if args.start:
                req = urllib.request.Request(f"{CASCOR}/v1/training/start", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
                        res["start_response"] = {"http": r.status, "body": r.read().decode()[:600]}
                except urllib.error.HTTPError as e:
                    res["start_response"] = {"http": e.code, "body": e.read().decode()[:600]}
                except Exception as exc:  # noqa: BLE001
                    res["start_response"] = {"http": None, "body": f"{type(exc).__name__}: {exc}"[:300]}
                log(f"  POST /v1/training/start -> {json.dumps(res['start_response'])[:400]}")

            t0 = time.time()
            last = {"hidden": res["start_hidden"], "dom": None, "cards": None, "phase": None, "glow": None, "store": None, "gen": None, "fsm": None}
            completed_at = None
            while True:
                now = time.time()
                if now - t0 > args.budget:
                    res["events"].append({"t": round(now - t0, 1), "what": "budget exhausted"})
                    break
                if completed_at is not None and now - completed_at > args.grace:
                    break

                st = _cascor_status()
                t = round(now - t0, 1)
                sample = {"t": t, "cascor": st}
                # canopy's SERVER-side view of the same instant (/api/state, what the
                # training-state stores are filled from). Lets a blank phase-duration or an
                # 'Inactive' badge be attributed: either the canopy server never learned the
                # state, or it did and the browser store never applied it -- different Overtoads.
                try:
                    cs = _w3.http_get("/api/state", timeout=8)[1] or {}
                    sample["canopy_state"] = {k: cs.get(k) for k in ("status", "phase", "candidate_pool_status", "candidate_pool_phase", "candidate_pool_size", "phase_started_at", "current_epoch", "is_running")}
                except Exception as exc:  # noqa: BLE001
                    sample["canopy_state"] = {"_err": f"{type(exc).__name__}: {exc}"[:100]}
                try:
                    sample["cards"] = _cards(page_c)
                    sample["hist_store"] = _store_len(page_c, f"{CID}-pool-history-store")
                    sample["badge"] = (vis(page_c, f"{CID}-status-badge") or {}).get("text")
                    sample["phase_duration"] = (vis(page_m, PHASE_DURATION) or {}).get("text")
                    sample["dom_hidden"] = counts(page_t).get("hidden")
                    sample["glow"] = _glow(page_t)
                    sample["buffer_gen"] = _store_len(page_t, BUFFER)
                    sample["metrics_store_len"] = _store_len(page_t, METRICS_STORE)
                    # F-035 context for the live lane: did WS metrics frames reach the page
                    # (``ws-metrics-buffer`` gen), and did the liveness gate call the stream
                    # live (which DEMOTES the REST poll and hands the store to the WS appender)?
                    sample["ws_metrics_gen"] = _store_len(page_t, "ws-metrics-buffer")
                    lv = (_store(page_t, "ws-liveness-store") or {}).get("value")
                    sample["ws_metrics_live"] = lv.get("metrics_live") if isinstance(lv, dict) else None
                except Exception as exc:  # noqa: BLE001
                    sample["error"] = f"{type(exc).__name__}: {exc}"[:160]
                res["samples"].append(sample)

                # --- transitions, logged once each ---
                if st.get("ok"):
                    if st.get("fsm") != last["fsm"]:
                        log(f"  [t={t}] FSM {last['fsm']} -> {st.get('fsm')}  phase={st.get('phase')} hidden={st.get('hidden')} epoch={st.get('epoch')}")
                        res["events"].append({"t": t, "what": f"fsm {last['fsm']} -> {st.get('fsm')}"})
                        last["fsm"] = st.get("fsm")
                        if st.get("fsm") in ("COMPLETED", "FAILED", "STOPPED") and t > 5 and completed_at is None:
                            completed_at = now
                            log(f"  [t={t}] run reached {st.get('fsm')}; sampling for {args.grace}s more")
                    if st.get("phase") != last["phase"]:
                        res["events"].append({"t": t, "what": f"phase {last['phase']} -> {st.get('phase')}"})
                        last["phase"] = st.get("phase")
                    sh = _cascor_hidden()
                    if sh is not None and sh != last["hidden"]:
                        log(f"  [t={t}] *** SERVER GREW: hidden {last['hidden']} -> {sh} ***")
                        res["server_growth"].append({"t": t, "hidden": sh})
                        last["hidden"] = sh
                    # F-026: a mid-run pair
                    psa = st.get("phase_started_at")
                    disp = _parse_duration(sample.get("phase_duration") or "")
                    if psa and disp is not None:
                        el = _elapsed_since(psa)
                        res["f026_samples"].append({"t": t, "phase_started_at": psa, "elapsed_s": None if el is None else round(el, 1), "displayed_s": disp, "displayed_text": sample.get("phase_duration"), "delta_s": None if el is None else round(disp - el, 1)})
                if sample.get("cards") != last["cards"]:
                    log(f"  [t={t}] history cards {last['cards']} -> {sample.get('cards')} (store len {sample.get('hist_store')}, badge {sample.get('badge')!r})")
                    if sample.get("cards") and res["cards_first_seen"] is None:
                        res["cards_first_seen"] = t
                        shot(page_c, "LIVE-RUN__first_history_card.png")
                    last["cards"] = sample.get("cards")
                if sample.get("dom_hidden") != last["dom"]:
                    res["dom_growth"].append({"t": t, "hidden": sample.get("dom_hidden")})
                    log(f"  [t={t}] DOM hidden-count now {sample.get('dom_hidden')!r}")
                    last["dom"] = sample.get("dom_hidden")
                g = bool((sample.get("glow") or {}).get("glow"))
                if g != last["glow"]:
                    log(f"  [t={t}] glow traces {'PRESENT' if g else 'absent'}: {(sample.get('glow') or {}).get('glow')}")
                    if g and res["glow_first_seen"] is None:
                        res["glow_first_seen"] = t
                        shot(page_t, "LIVE-RUN__glow_first_seen.png")
                    last["glow"] = g
                if sample.get("buffer_gen") != last["gen"]:
                    log(f"  [t={t}] {BUFFER} gen {last['gen']} -> {sample.get('buffer_gen')}")
                    last["gen"] = sample.get("buffer_gen")
                if sample.get("metrics_store_len") != last["store"]:
                    log(f"  [t={t}] {METRICS_STORE} len {last['store']} -> {sample.get('metrics_store_len')}")
                    res["store_len_seq"].append({"t": t, "from": last["store"], "to": sample.get("metrics_store_len")})
                    last["store"] = sample.get("metrics_store_len")

                page_c.wait_for_timeout(int(args.every * 1000))

            res["end_hidden"] = _cascor_hidden()
            res["end_status"] = _cascor_status()
            res["end_cards"] = _cards(page_c)
            shot(page_c, "LIVE-RUN__candidates_end.png")
            shot(page_t, "LIVE-RUN__topology_end.png")
            shot(page_m, "LIVE-RUN__metrics_end.png")

            # --- M-CANDIDATES-10 / -11: click a REAL card header, if one exists ---
            click: dict = {"attempted": False}
            if res["end_cards"] and not args.no_click:
                before = _first_card(page_c)
                n_before = len(capture)
                page_c.evaluate("""() => { const h = document.querySelector('[id*="history-pool-header"]'); if (h) h.click(); }""")
                page_c.wait_for_timeout(6000)
                after = _first_card(page_c)
                new_reqs = [c for c in capture[n_before:] if "history-pool" in (c.get("body") or "")]
                click = {
                    "attempted": True,
                    "before": before,
                    "after": after,
                    "collapse_changed": (before.get("collapse_cls"), before.get("collapse_h")) != (after.get("collapse_cls"), after.get("collapse_h")),
                    "requests_naming_history_pool_after_click": len(new_reqs),
                    "total_requests_after_click": len(capture) - n_before,
                }
                log(f"  header click: collapse_changed={click['collapse_changed']} requests naming history-pool={len(new_reqs)} (of {click['total_requests_after_click']})")
                shot(page_c, "LIVE-RUN__after_header_click.png")
            res["header_click"] = click
        finally:
            browser.close()

    # --- verdicts, from the rules in the docstring ---
    grew = bool(res["server_growth"])
    cand_phase_seen = any((s.get("cascor") or {}).get("phase", "").lower().startswith("cand") for s in res["samples"] if s.get("cascor", {}).get("ok"))
    v: dict = {}
    if res["cards_first_seen"] is not None:
        v["M-CANDIDATES-09"] = "PASS"
    elif cand_phase_seen:
        v["M-CANDIDATES-09"] = "FAIL"
    else:
        v["M-CANDIDATES-09"] = "BLOCKED (no candidate phase observed)"
    hc = res.get("header_click") or {}
    if hc.get("attempted"):
        if not hc.get("collapse_changed") and hc.get("requests_naming_history_pool_after_click", 0) == 0:
            v["M-CANDIDATES-10"] = "DEAD-CONFIRMED"
            v["M-CANDIDATES-11"] = "DEAD-CONFIRMED"
        else:
            v["M-CANDIDATES-10"] = "PASS (surprise: the click DID something -- read header_click)"
            v["M-CANDIDATES-11"] = "PASS (collapse moved)"
    else:
        v["M-CANDIDATES-10"] = v["M-CANDIDATES-11"] = "BLOCKED (no card to click)"
    f026 = [s for s in res["f026_samples"] if s.get("delta_s") is not None]
    if f026:
        worst = max(abs(s["delta_s"]) for s in f026)
        v["F-CANOPY-026"] = f"CLOSED-BY-VERIFICATION ({len(f026)} mid-run samples, worst |delta| {worst}s)" if worst <= args.tolerance else f"STILL-OPEN (worst |delta| {worst}s over {len(f026)} samples)"
    else:
        naive = [s for s in res["f026_samples"] if s.get("elapsed_s") is None]
        v["F-CANOPY-026"] = "NOT-SAMPLED (no mid-run pair)" if not naive else f"STILL-OPEN (phase_started_at NAIVE in {len(naive)} samples)"
    if res["glow_first_seen"] is not None:
        v["M-TOPOLOGY-16"] = f"PASS (glow trace at t={res['glow_first_seen']}s)"
    elif grew:
        dom_followed = any(isinstance(d.get("hidden"), str) and d["hidden"].strip().isdigit() for d in res["dom_growth"][1:])
        v["M-TOPOLOGY-16"] = ("BLOCKED-BY-F-035 (server grew " + " -> ".join(str(x["hidden"]) for x in [{"hidden": res["start_hidden"]}] + res["server_growth"]) + f", DOM followed={dom_followed}, no glow trace ever; the detector reads hidden-unit deltas out of {METRICS_STORE}, whose length stayed {sorted({s.get('metrics_store_len') for s in res['samples']} - {None})})")
    else:
        v["M-TOPOLOGY-16"] = "BLOCKED (the server never grew during the window)"
    res["verdicts"] = v

    log("")
    log(f"  server growth : {res['start_hidden']} -> {res.get('end_hidden')} via {[x['hidden'] for x in res['server_growth']]}")
    log(f"  DOM growth    : {[x['hidden'] for x in res['dom_growth']]}")
    log(f"  cards         : first at t={res['cards_first_seen']}s, end={res.get('end_cards')}")
    log(f"  glow          : first at t={res['glow_first_seen']}s")
    log(f"  metrics store : {[(x['from'], x['to']) for x in res['store_len_seq']][:10]}")
    log(f"  F-026 samples : {len(f026)}  deltas={[s['delta_s'] for s in f026][:12]}")
    for k, val in v.items():
        log(f"  => {k}: {val}")

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
