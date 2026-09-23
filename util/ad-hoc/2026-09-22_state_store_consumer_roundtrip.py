#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""How much margin do the training-state stores' Input consumers actually have?

STILL-OWED ITEM 3 of the 2026-09-10 handoff
(``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-10_canopy-e2e-f035-fixed-at-the-renderer-and-the-defect-it-was-masking.md``):
the 2026-09-11 sibling sweep found three callbacks -- ``update_status_display``,
``update_epoch_progress``, ``update_pool_info`` -- that take
``candidate-metrics-panel-training-state-store`` as their ONLY Input. That store is
rewritten on every tick of a 1000 ms interval with a value that ALWAYS differs
(``/api/state`` carries a per-call ``timestamp``), which is exactly the shape that
evicted ``update_loss_plot`` (F-CANOPY-052): a consumer whose round trip outlasts its
re-request period is re-``requested`` under one ``getUniqueIdentifier`` and its
in-flight response is discarded (dash_renderer.dev.js :3027 / :2698). The sweep called
the three "not broken -- they survive on a margin nobody chose and nobody measures".
This probe measures that margin.

It also covers a SECOND store of the same shape that the 09-11 sweep did not look at:
``metrics-panel-training-state-store`` is REST-polled off ``metrics-panel-update-interval``
whenever the WS state stream is quiet, and four callbacks take it as their only Input
-- one of which, ``update_phase_duration``, computes ``now - phase_started_at`` at
invocation time, so it USES the store's 1 Hz rewrite as its clock.

WHAT IT RECORDS, per callback, off the browser's own request timing
(``request.timing`` from Playwright, i.e. the network stack's clock, not Python's):

  requests     how many ``_dash-update-component`` POSTs carried that callback's outputs
  rt_ms        round trip per request: request start -> response end
  gap_ms       gap between consecutive request STARTS of the same callback (its real
               re-request period, which Trap 2 of the handoff says is never the nominal one)
  overlaps     requests that started before the previous same-callback request had
               finished. An overlap is the HTTP-level signature of a re-request over an
               in-flight call. It is a LOWER BOUND on eviction, not a measure of it: the
               discard is decided at APPLY time, which Trap 1 measured at 0.7-7.0 s after
               the response lands, so a response can finish at the HTTP layer and still be
               thrown away. Zero overlaps does NOT prove zero evictions.

With ``--tab metrics`` it also samples the Phase Duration readout against the server's
own ``phase_started_at`` once a second, so a growth window run beside it shows whether
that clock-driven readout is current or trailing (the F-CANOPY-026 residual recorded a
10-25 s trail with no mechanism).

NO VERDICT on the margin. This is the measurement the handoff asked to take BEFORE
deciding between demoting the Inputs and fixing the writer; it does not decide.

Usage (one tab per run -- one browser per run, so F-CANOPY-051's cross-page tab
bleed cannot occur):
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8051 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-22_state_store_consumer_roundtrip.py --tab candidates --seconds 60 \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_consumer_rt_candidates_idle.json
"""

import argparse
import importlib.util
import json
import statistics
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


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")
log = _seg17.log
CANOPY = _seg17.CANOPY

# callback -> the output-id substring that identifies its request (every one is unique
# within the app; checked against canopy main 9bffaba1).
CALLBACKS = {
    "candidates": {
        "fetch_training_state (WRITER)": "candidate-metrics-panel-training-state-store.data",
        "update_status_display": "candidate-metrics-panel-status-badge.children",
        "update_epoch_progress": "candidate-metrics-panel-progress-section.style",
        "update_pool_info": "candidate-metrics-panel-pool-info.children",
        "update_loss_plot (State since #618)": "candidate-metrics-panel-loss-plot.figure",
    },
    "metrics": {
        "fetch_training_state (WRITER)": "metrics-panel-training-state-store.data",
        "update_progress_detail": "metrics-panel-progress-detail.children",
        "update_learning_rate": "metrics-panel-current-lr.children",
        "update_phase_duration": "metrics-panel-phase-duration.children",
        "update_training_progress": "metrics-panel-progress-bars.style",
    },
}
TAB_LABEL = {"candidates": "Candidate Metrics", "metrics": "Training Metrics"}

_JS_PROP_DISABLED = """(id) => {
  const st = window.store && window.store.getState ? window.store.getState() : null;
  if (!st || !st.layout || !st.paths || !st.paths.strs || !st.paths.strs[id]) return null;
  let node = st.layout;
  for (const k of st.paths.strs[id]) { if (node == null) break; node = node[k]; }
  return (node && node.props && 'disabled' in node.props) ? node.props.disabled : null;
}"""
STORE_ID = {"candidates": "candidate-metrics-panel-training-state-store", "metrics": "metrics-panel-training-state-store"}


def _health() -> dict:
    try:
        with urllib.request.urlopen(f"{CANOPY}/v1/health", timeout=5) as r:  # noqa: S310
            p = json.loads(r.read().decode("utf-8"))
        return {"ok": True, "url": CANOPY, "version": p.get("version"), "git_sha": p.get("git_sha"), "build_date": p.get("build_date")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "url": CANOPY, "why": f"{type(exc).__name__}: {exc}"[:160]}


def _api_state() -> dict:
    try:
        with urllib.request.urlopen(f"{CANOPY}/api/state", timeout=3) as r:  # noqa: S310
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _pct(xs: list, q: float):
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, int(q * (len(s) - 1) + 0.5))], 1)


def _summ(xs: list) -> dict:
    return {"n": len(xs), "min": round(min(xs), 1) if xs else None, "p50": _pct(xs, 0.5), "p90": _pct(xs, 0.9), "max": round(max(xs), 1) if xs else None,
            "mean": round(statistics.fmean(xs), 1) if xs else None}


def _parse_duration(text: str):
    # "Phase Duration: 3m 07s" -> 187
    if not text or "Phase Duration:" not in text:
        return None
    try:
        body = text.split("Phase Duration:", 1)[1].strip()
        m, s = body.split("m", 1)
        return int(m.strip()) * 60 + int(s.strip().rstrip("s").strip())
    except (ValueError, IndexError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tab", choices=sorted(CALLBACKS), required=True)
    ap.add_argument("--seconds", type=float, default=60.0, help="length of the sampling window after the tab settles")
    ap.add_argument("--out", required=True)
    ap.add_argument("--grow-to", type=int, default=None, help="launch 2026-09-22_fixture_grow.py --to N inside the window (a live growth window)")
    ap.add_argument("--grow-after", type=float, default=10.0, help="seconds into the window at which to launch the growth")
    ap.add_argument("--census-store", action="append", help="also census responses writing this store id: carried / no_update / distinct payloads (repeatable)")
    ap.add_argument("--read-candidate-lane", action="store_true",
                    help="sample candidate-metrics-panel-update-interval.disabled every second (the F-CANOPY-027 gate check: it must stay "
                         "true while another tab is active)")
    ap.add_argument("--display-mode", choices=("window", "full", "hidden_units"), default=None,
                    help="(metrics tab) click this metrics display-mode radio before the window opens; the switch time is recorded")
    args = ap.parse_args()
    grow = {"proc": None, "launched_at": None}

    from playwright.sync_api import sync_playwright

    cbs = CALLBACKS[args.tab]
    reqs: dict = {name: [] for name in cbs}
    unmatched = {"n": 0}
    unmatched_outputs: dict = {}
    failed = {"n": 0}
    window = {"open": False}
    duration_samples: list = []
    panel_samples: list = []
    lane_samples: list = []
    store_stamps: list = []
    writer_resp = {"carried": 0, "no_update": 0, "unparsed": 0, "timestamps": []}
    store_id_for_tab = STORE_ID[args.tab]
    census_stores = list(args.census_store or [])
    census: dict = {}

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": _health(), "tab": args.tab,
           "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": args.seconds}
    log(f"serving: {res['serving']}")
    if not res["serving"].get("ok"):
        log("REFUSED: the leg is not answering /v1/health")
        return 2

    def on_finished(req):
        if not window["open"] or "_dash-update-component" not in req.url:
            return
        try:
            body = req.post_data_json or {}
        except Exception:  # noqa: BLE001
            body = {}
        output = str(body.get("output") or "")
        timing = req.timing or {}
        start = timing.get("startTime")
        end = timing.get("responseEnd")
        # Dash serialises outputs as ``id.prop`` (one) or ``..a.p...b.q..`` (several), and
        # an ``allow_duplicate`` output carries an ``@<hash>`` suffix. Match whole tokens:
        # ``metrics-panel-training-state-store.data`` is a SUBSTRING of the candidate
        # panel's ``candidate-metrics-panel-training-state-store.data``.
        tokens = {t.split("@", 1)[0] for t in output.strip(".").split("...") if t}
        hit = [name for name, needle in cbs.items() if needle in tokens]
        if not hit:
            unmatched["n"] += 1
            key = output[:160]
            unmatched_outputs[key] = unmatched_outputs.get(key, 0) + 1
            return
        for name in hit:
            reqs[name].append({"start_ms": start, "rt_ms": end if (end is not None and end >= 0) else None,
                               "trigger": [c for c in (body.get("changedPropIds") or [])][:3]})

    def on_response(resp):
        # The server's side of the writer: did its response CARRY a new store value?
        # ``distinct_timestamps`` here vs ``store_in_renderer.distinct_timestamps`` is the
        # delivered-vs-applied comparison. A response that omits the key is Dash's
        # ``no_update``; one we cannot parse is COUNTED, not swallowed (the 09-10 census
        # swallowed them, which round 2 recorded as R7).
        if not window["open"] or "_dash-update-component" not in resp.url:
            return
        try:
            body = resp.request.post_data_json or {}
        except Exception:  # noqa: BLE001
            body = {}
        tokens = {t.split("@", 1)[0] for t in str(body.get("output") or "").strip(".").split("...") if t}
        for extra in census_stores:
            if f"{extra}.data" not in tokens:
                continue
            c = census.setdefault(extra, {"responses": 0, "carried": 0, "no_update": 0, "unparsed": 0, "distinct_payloads": set(), "requests": []})
            c["responses"] += 1
            # Which tick drove this request, and when it started (browser clock): in full /
            # hidden_units mode only ticks with n % FULL_HISTORY_POLL_TICK_MODULUS == 0 fetch.
            try:
                body = resp.request.post_data_json or {}
                n_val = next((i.get("value") for i in (body.get("inputs") or []) if isinstance(i, dict) and i.get("property") == "n_intervals"), None)
                dup = "@" in str(body.get("output") or "")
                c["requests"].append({"start_ms": (resp.request.timing or {}).get("startTime"), "n": n_val, "allow_duplicate_writer": dup,
                                      "changed": list(body.get("changedPropIds") or [])[:2]})
            except Exception:  # noqa: BLE001
                pass
            try:
                pl = json.loads(resp.text())
            except Exception:  # noqa: BLE001
                c["unparsed"] += 1
                continue
            rm = pl.get("response") if isinstance(pl, dict) else None
            if not isinstance(rm, dict) or extra not in rm:
                c["no_update"] += 1
            else:
                c["carried"] += 1
                c["distinct_payloads"].add(json.dumps((rm.get(extra) or {}).get("data"), sort_keys=True, default=str)[:200000])
        if f"{store_id_for_tab}.data" not in tokens:
            return
        try:
            payload = json.loads(resp.text())
        except Exception:  # noqa: BLE001
            writer_resp["unparsed"] += 1
            return
        rmap = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(rmap, dict) or store_id_for_tab not in rmap:
            writer_resp["no_update"] += 1
            return
        data = (rmap.get(store_id_for_tab) or {}).get("data")
        writer_resp["carried"] += 1
        if isinstance(data, dict) and data.get("timestamp") is not None:
            writer_resp["timestamps"].append(data.get("timestamp"))

    def on_failed(req):
        if window["open"] and "_dash-update-component" in req.url:
            failed["n"] += 1

    with sync_playwright() as pw:
        browser, ctx, page = _seg17.open_dashboard(pw, [])
        try:
            page.on("requestfinished", on_finished)
            page.on("requestfailed", on_failed)
            page.on("response", on_response)
            opened = _seg17.open_tab(page, TAB_LABEL[args.tab])
            res["tab_opened"] = opened
            page.wait_for_timeout(3000)  # let the tab's mount burst finish before the window opens
            if args.display_mode:
                label = {"window": "Sliding Window", "full": "Full History", "hidden_units": "Between Hidden Units"}[args.display_mode]
                clicked = page.evaluate(
                    """(label) => { const root = document.getElementById('metrics-panel-display-mode'); if (!root) return 'no-radio';
                         const l = [...root.querySelectorAll('label')].find(x => x.textContent.trim() === label);
                         if (!l) return 'no-label'; l.click(); return 'clicked'; }""", label)
                res["display_mode_switch"] = {"mode": args.display_mode, "result": clicked, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                              "local": time.strftime("%Y-%m-%d %H:%M:%S")}
                log(f"display mode -> {args.display_mode}: {clicked} at {res['display_mode_switch']['local']}")
                page.wait_for_timeout(2000)
            window["open"] = True
            t_open = time.time()
            log(f"window open: tab={TAB_LABEL[args.tab]!r} opened={opened}; sampling {args.seconds:.0f}s")
            store_id = STORE_ID[args.tab]
            while time.time() - t_open < args.seconds:
                if args.grow_to and grow["proc"] is None and time.time() - t_open >= args.grow_after:
                    import subprocess  # noqa: S404 -- launches this directory's own grow helper

                    grow_out = str(Path(args.out).with_name(Path(args.out).stem + f"_grow_{args.grow_to}.json"))
                    grow["proc"] = subprocess.Popen([sys.executable, str(_HERE / "2026-09-22_fixture_grow.py"), "--to", str(args.grow_to), "--out", grow_out],  # noqa: S603
                                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    grow["launched_at"] = round(time.time() - t_open, 1)
                    grow["out"] = grow_out
                    log(f"growth window launched at t={grow['launched_at']}s (--to {args.grow_to})")
                # Does the WRITER's write reach the renderer? The value's ``timestamp`` is
                # per-call, so every applied write shows as a new stamp here.
                rd = _seg17._store(page, store_id) or {}
                val = rd.get("value") if isinstance(rd, dict) else None
                store_stamps.append({"t": round(time.time() - t_open, 1), "ok": rd.get("ok") if isinstance(rd, dict) else None,
                                     "timestamp": val.get("timestamp") if isinstance(val, dict) else None,
                                     "keys": len(val) if isinstance(val, dict) else None})
                if args.tab == "candidates":
                    # The user-visible side: what the panel SHOWS against what the server
                    # says at the same moment. A frozen store shows as a DOM that never
                    # follows a server that moves.
                    dom = page.evaluate("""() => { const g = id => { const e = document.getElementById(id); return e ? e.innerText : null; };
                        const ps = document.getElementById('candidate-metrics-panel-progress-section');
                        const hs = document.getElementById('candidate-metrics-panel-history-section');
                        const ep = document.getElementById('candidate-metrics-panel-epoch-progress');
                        return {badge: g('candidate-metrics-panel-status-badge'), phase: g('candidate-metrics-panel-phase'),
                                pool_size: g('candidate-metrics-panel-pool-size'),
                                progress_display: ps ? getComputedStyle(ps).display : null,
                                epoch_progress: ep ? (ep.innerText || null) : null,
                                pool_info: (g('candidate-metrics-panel-pool-info') || '').slice(0, 80),
                                history_cards: hs ? hs.querySelectorAll('[id*="history-pool-header"]').length : null}; }""")
                    st = _api_state()
                    panel_samples.append({"t": round(time.time() - t_open, 1), "dom": dom,
                                          "server": {"status": st.get("status"), "pool_status": st.get("candidate_pool_status"),
                                                     "pool_phase": st.get("candidate_pool_phase"), "pool_size": st.get("candidate_pool_size"),
                                                     "candidate_epoch": st.get("candidate_epoch"), "candidate_total_epochs": st.get("candidate_total_epochs")}})
                if args.read_candidate_lane:
                    lane_samples.append({"t": round(time.time() - t_open, 1),
                                         "disabled": page.evaluate(_JS_PROP_DISABLED, "candidate-metrics-panel-update-interval")})
                if args.tab == "metrics":
                    txt = page.evaluate("() => { const e = document.getElementById('metrics-panel-phase-duration'); return e ? e.innerText : null; }")
                    st = _api_state()
                    started = st.get("phase_started_at") or ""
                    expected = None
                    if started:
                        try:
                            dt = datetime.fromisoformat(started)
                            if dt.tzinfo is None:
                                dt = dt.astimezone()
                            expected = round((datetime.now(timezone.utc) - dt).total_seconds(), 1)
                        except ValueError:
                            expected = None
                    shown = _parse_duration(txt or "")
                    duration_samples.append({"t": round(time.time() - t_open, 1), "status": st.get("status"), "phase": st.get("phase"),
                                             "shown_text": txt, "shown_s": shown, "expected_s": expected,
                                             "lag_s": round(expected - shown, 1) if (expected is not None and shown is not None) else None})
                page.wait_for_timeout(1000)
            window["open"] = False
            page.wait_for_timeout(1500)  # let in-flight requests finish so their timing lands
        finally:
            browser.close()
    if grow["proc"] is not None:
        out, _ = grow["proc"].communicate(timeout=600)
        res["growth"] = {"launched_at_s": grow["launched_at"], "exit": grow["proc"].returncode, "record": grow.get("out"), "tail": (out or "").splitlines()[-8:]}
        for line in res["growth"]["tail"]:
            log(f"  [grow] {line}")

    per_cb = {}
    for name, rows in reqs.items():
        rows = sorted([r for r in rows if r["start_ms"] is not None], key=lambda r: r["start_ms"])
        rts = [r["rt_ms"] for r in rows if r["rt_ms"] is not None]
        gaps = [b["start_ms"] - a["start_ms"] for a, b in zip(rows, rows[1:])]
        overlaps = 0
        for a, b in zip(rows, rows[1:]):
            if a["rt_ms"] is not None and b["start_ms"] < a["start_ms"] + a["rt_ms"]:
                overlaps += 1
        per_cb[name] = {"requests": len(rows), "rt_ms": _summ(rts), "gap_ms": _summ(gaps), "overlaps": overlaps}
    res["callbacks"] = per_cb
    res["unmatched_update_requests"] = unmatched["n"]
    res["unmatched_outputs"] = dict(sorted(unmatched_outputs.items(), key=lambda kv: -kv[1]))
    res["failed_update_requests"] = failed["n"]
    distinct = sorted({s["timestamp"] for s in store_stamps if s["timestamp"] is not None})
    res["store_in_renderer"] = {"store": STORE_ID[args.tab], "reads": len(store_stamps),
                                "readable": sum(1 for s in store_stamps if s["ok"]),
                                "distinct_timestamps": len(distinct), "samples": store_stamps}
    res["writer_responses"] = {"carried_store": writer_resp["carried"], "no_update": writer_resp["no_update"], "unparsed": writer_resp["unparsed"],
                               "distinct_timestamps_delivered": len(set(writer_resp["timestamps"]))}
    log(f"writer responses: {res['writer_responses']}")
    if census:
        res["census"] = {k: {**{kk: vv for kk, vv in v.items() if kk != "distinct_payloads"}, "distinct_payloads": len(v["distinct_payloads"])} for k, v in census.items()}
        for k, v in res["census"].items():
            log(f"census {k}: " + json.dumps({kk: vv for kk, vv in v.items() if kk != "requests"}))
            polls = sorted([r for r in v.get("requests") or [] if not r["allow_duplicate_writer"] and r["start_ms"] and isinstance(r["n"], int)], key=lambda r: r["start_ms"])
            if polls:
                gaps = [b["start_ms"] - a["start_ms"] for a, b in zip(polls, polls[1:])]
                fetch = [r for r in polls if r["n"] % 5 == 0]
                fgaps = [b["start_ms"] - a["start_ms"] for a, b in zip(fetch, fetch[1:])]
                res.setdefault("cadence", {})[k] = {"poll_requests": len(polls), "poll_gap_ms": _summ(gaps), "modulus_ticks": len(fetch), "modulus_gap_ms": _summ(fgaps),
                                                    "n_values": [r["n"] for r in polls]}
                log(f"cadence {k}: polls={len(polls)} poll_gap_ms={_summ(gaps)} | n%5==0 ticks={len(fetch)} gap_ms={_summ(fgaps)}")
    log(f"store in renderer: {res['store_in_renderer']['readable']}/{len(store_stamps)} reads readable, "
        f"{len(distinct)} distinct timestamps (the writer ran {per_cb.get('fetch_training_state (WRITER)', {}).get('requests')} times)")
    if lane_samples:
        vals = [s["disabled"] for s in lane_samples]
        cand_writer = [r for r in (census.get("candidate-metrics-panel-training-state-store") or {}).get("requests") or []]
        res["candidate_lane"] = {"samples": len(vals), "disabled_true": sum(1 for v in vals if v is True),
                                 "disabled_false": sum(1 for v in vals if v is False), "unreadable": sum(1 for v in vals if v is None),
                                 "candidate_writer_requests_seen": len(cand_writer)}
        log(f"candidate lane (F-027 gate check): {res['candidate_lane']}")
    if panel_samples:
        server_seen = sorted({str(s["server"].get("pool_status")) for s in panel_samples})
        dom_seen = sorted({str((s["dom"] or {}).get("badge")) for s in panel_samples})
        res["panel"] = {"samples": panel_samples, "server_pool_status_seen": server_seen, "dom_badge_seen": dom_seen}
        log(f"candidate panel: server pool_status seen {server_seen}; DOM badge seen {dom_seen}")
    if duration_samples:
        lags = [s["lag_s"] for s in duration_samples if s["lag_s"] is not None]
        res["phase_duration"] = {"samples": duration_samples, "lag_s": _summ(lags)}

    log("")
    log(f"{'callback':38s} {'req':>4s} {'rt p50':>7s} {'rt p90':>7s} {'rt max':>7s} {'gap p50':>8s} {'gap min':>8s} {'ovl':>4s}")
    for name, s in per_cb.items():
        log(f"{name:38s} {s['requests']:4d} {str(s['rt_ms']['p50']):>7s} {str(s['rt_ms']['p90']):>7s} {str(s['rt_ms']['max']):>7s} "
            f"{str(s['gap_ms']['p50']):>8s} {str(s['gap_ms']['min']):>8s} {s['overlaps']:4d}")
    log(f"unmatched update requests: {unmatched['n']}; failed: {failed['n']}")
    for out, n in list(res["unmatched_outputs"].items())[:12]:
        log(f"    {n:4d}  {out}")
    if duration_samples:
        log(f"phase-duration lag (s): {res['phase_duration']['lag_s']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
