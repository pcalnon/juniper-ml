#!/usr/bin/env python3
"""Lane A1 (user-visible DOM entry point): does the Candidate Metrics panel move while canopy says Training?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc canopy E2E validation (independent-agent consensus, Lane A)
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.2.0  (0.2.0 changed ONLY the active-control pairing + added --reanalyse; the 2026-09-22 real run
             was measured with 0.1.0 -- identical measurement code -- and its record reanalysed with 0.2.0)
License:     MIT License
Status:      ad-hoc -- investigation (one-off Lane A measurement re-creation)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md section 2 (Lane A)

THE CLAIM UNDER TEST (a claim, not a fact). On canopy (default http://127.0.0.1:8051), during a
live cascor training window, ``#candidate-metrics-panel-status-badge`` / ``-phase`` /
``-pool-size`` stay at their mount values while canopy's own ``/api/state`` reports
``candidate_pool_status == "Training"``.

THE INSTRUMENT -- three readings on ONE wall clock (epoch seconds / ms):
  1. a ~1 Hz Python poll that reads the user-visible DOM (``innerText``) in one
     ``page.evaluate`` and immediately afterwards GETs ``/api/state``: the paired cross-tab;
  2. an in-page MutationObserver log (``textContent`` of the same elements plus the
     positive-control top status bar and the active tab), installed while the page is calm and
     harvested ONCE at the end, so a renderer that starves ``page.evaluate`` under training load
     cannot hide a change;
  3. a background thread polling ``/api/state`` and cascor's ``/v1/training/status`` at 1 Hz,
     so the server timeline is continuous even if the page stalls.
Secondary evidence: a wire census of ``/_dash-update-component`` POSTs (request/response COUNTS per
output, live), plus a time-bounded read of the bodies of the candidate-panel responses AFTER the run.
Bodies are never read mid-run: Chromium serves ``Network.getResponseBody`` from the renderer main
thread, and the dry run lost ~60 s of sampling to it.

POSITIVE CONTROLS, two of them:
  * PASSIVE -- the top status bar (``#top-status-display`` etc.), written off ``fast-update-interval``,
    a shared lane that is NOT tab-gated; its server truth is ``/api/status``, recorded alongside.
    The dry run found it stuck at its mount defaults ("Stopped"/"0") at idle while ``/api/status``
    said COMPLETED/58, so it may not move at all and cannot be relied on alone.
  * ACTIVE -- ``--toggle-at`` fires a DOM click on the Pool History header, whose one-shot server
    callback (``toggle_history``) rewrites ``#candidate-metrics-panel-history-icon``. It rides the same
    server-response -> DOM path as the badge and writes none of the measured elements. A registered
    icon change proves this read path sees a server-driven change on this page during the window.
If neither control registers a change, the instrument cannot tell "frozen panel" from "frozen page"
(or from a blind reader), and the verdict must be downgraded.

DRIVING NOTES (measured in the dry runs, 2026-09-22): a trusted ``click(force=True)`` took 2-18 s to
return and the welcome modal hid 6-9 s after it (its close is a server callback), so setup uses a 40 s
click timeout; ``page.evaluate`` itself took 0.2-3.5 s. Several other validators' headless renderers
were loading canopy concurrently; the preflight records load average and their count.

GROWTH. At ~``--grow-at`` s into sampling it launches ``2026-09-22_fixture_grow.py`` AT MOST
ONCE: only if cascor is idle (terminal FSM, ``training_active`` false) and the growth record does
not already exist. If cascor was already training at start, it never launches -- it observes
that window instead. ``--no-grow`` never launches (dry run / idle baseline).

Usage (Playwright lives in the canopy env):
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-22_laneA1_candidate_panel_dom_check.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_candidate_panel_dom.json
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request

from playwright.sync_api import sync_playwright

CANOPY = os.environ.get("LANEA1_CANOPY_URL", "http://127.0.0.1:8051")
CASCOR = os.environ.get("LANEA1_CASCOR_URL", "http://127.0.0.1:8202")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GROW_SCRIPT = os.path.join(REPO, "util", "ad-hoc", "2026-09-22_fixture_grow.py")

BADGE, PHASE, SIZE, INFO = (f"candidate-metrics-panel-{s}" for s in ("status-badge", "phase", "pool-size", "pool-info"))
PANEL_IDS = (BADGE, PHASE, SIZE, INFO)
CONTROL_IDS = ("top-status-display", "top-phase-display", "top-epoch-display", "top-hidden-units-display")
# ACTIVE control: a one-shot server callback (toggle_history) whose Output is this icon's text. It rides the
# same server-response -> DOM path as the badge but writes none of the measured elements.
HIST_TOGGLE, HIST_ICON = "candidate-metrics-panel-history-toggle", "candidate-metrics-panel-history-icon"
WATCH_IDS = PANEL_IDS + CONTROL_IDS + (HIST_ICON,)
STATUS_KEYS = ("is_training", "is_running", "completed", "fsm_status", "phase", "current_epoch", "hidden_units")
MOUNT = {BADGE: "Inactive", PHASE: "Idle", SIZE: "0"}  # the layout / empty-store defaults named by the claim
SERVER_KEYS = ("status", "phase", "candidate_pool_status", "candidate_pool_phase", "candidate_pool_size", "candidate_epoch", "candidate_total_epochs", "current_epoch", "max_hidden_units")
IDLE_FSM = {"COMPLETED", "STOPPED", "FAILED", "ERROR", "IDLE"}
TAB_TEXT = "Candidate Metrics"
TRUNC = 600

# One atomic read of everything user-visible that matters, plus how the active tab looks in the DOM.
SNAPSHOT_JS = """
([ids, tabText]) => {
  const out = {t_ms: Date.now(), text: {}, title: document.title};
  for (const id of ids) {
    const el = document.getElementById(id);
    out.text[id] = el ? el.innerText.slice(0, %d) : null;
  }
  let pool = Array.from(document.querySelectorAll('[role="tab"]'));
  out.tab_selector = 'role=tab';
  let cand = pool.find(el => el.innerText.trim() === tabText);
  if (!cand) { pool = Array.from(document.querySelectorAll('.nav-link')); out.tab_selector = '.nav-link'; cand = pool.find(el => el.innerText.trim() === tabText); }
  out.active_tabs = [];
  if (cand) {
    const list = cand.closest('[role="tablist"]') || (cand.parentElement && cand.parentElement.parentElement) || document;
    out.active_tabs = Array.from(new Set(Array.from(list.querySelectorAll('[role="tab"], .nav-link'))
      .filter(el => el.getAttribute('aria-selected') === 'true' || el.classList.contains('active'))
      .map(el => el.innerText.trim())));
    out.cand_tab = {aria_selected: cand.getAttribute('aria-selected'), cls: cand.className};
  }
  const badge = document.getElementById(ids[0]);
  out.badge_visible = badge ? badge.checkVisibility() : null;
  const pane = badge ? badge.closest('.tab-pane') : null;
  out.badge_pane_cls = pane ? pane.className : null;
  return out;
}
""" % TRUNC

DESCRIBE_JS = """
el => ({tag: el.tagName, role: el.getAttribute('role'), aria_selected: el.getAttribute('aria-selected'),
        cls: el.className, text: el.innerText.trim(), id: el.id || null,
        tablist: (el.closest('[role="tablist"]') || {}).id || null, outer: el.outerHTML.slice(0, 400)})
"""

# Installed once while the page is calm; re-reads by id on every mutation batch, so an element that
# Dash REPLACES is still seen. textContent (not innerText) so the observer forces no layout.
OBSERVER_JS = """
([ids, tabText]) => {
  if (window.__laneA1) return 'already-installed';
  const log = [];
  const last = {};
  const tabState = () => {
    let pool = Array.from(document.querySelectorAll('[role="tab"]'));
    let cand = pool.find(el => (el.textContent || '').trim() === tabText);
    if (!cand) { pool = Array.from(document.querySelectorAll('.nav-link')); cand = pool.find(el => (el.textContent || '').trim() === tabText); }
    if (!cand) return 'no-tab';
    const list = cand.closest('[role="tablist"]') || (cand.parentElement && cand.parentElement.parentElement) || document;
    return Array.from(new Set(Array.from(list.querySelectorAll('[role="tab"], .nav-link'))
      .filter(el => el.getAttribute('aria-selected') === 'true' || el.classList.contains('active'))
      .map(el => (el.textContent || '').trim()))).join('|');
  };
  const check = (why) => {
    const cur = {};
    for (const id of ids) { const el = document.getElementById(id); cur[id] = el ? (el.textContent || '').slice(0, %d) : null; }
    cur.__tab = tabState();
    const changed = {};
    let any = false;
    for (const k of Object.keys(cur)) { if (cur[k] !== last[k]) { changed[k] = cur[k]; last[k] = cur[k]; any = true; } }
    if (any) log.push({t_ms: Date.now(), why: why, changed: changed});
  };
  check('install');
  const mo = new MutationObserver(() => check('mutation'));
  mo.observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['class', 'aria-selected']});
  window.__laneA1 = {log: log, installed_ms: Date.now()};
  return 'installed';
}
""" % TRUNC

HARVEST_JS = "() => window.__laneA1 ? {installed_ms: window.__laneA1.installed_ms, log: window.__laneA1.log} : null"


def get_json(url: str, timeout: float = 5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 -- loopback only
            return json.loads(r.read().decode() or "null")
    except Exception as e:  # noqa: BLE001 -- recorded, never raised
        return {"__error__": f"{type(e).__name__}: {e}"}


def api_state() -> dict:
    d = get_json(CANOPY + "/api/state")
    if not isinstance(d, dict) or "__error__" in d:
        return {"__error__": d.get("__error__") if isinstance(d, dict) else f"non-dict {type(d).__name__}"}
    return {k: d.get(k) for k in SERVER_KEYS}


def api_status() -> dict:
    """What the top status bar's handler reads (``/api/status``) -- the control's server-side truth."""
    d = get_json(CANOPY + "/api/status")
    if not isinstance(d, dict) or "__error__" in d:
        return {"__error__": d.get("__error__") if isinstance(d, dict) else "non-dict"}
    return {k: d.get(k) for k in STATUS_KEYS}


def cascor_status() -> dict:
    d = get_json(CASCOR + "/v1/training/status")
    if not isinstance(d, dict) or "__error__" in d:
        return {"__error__": d.get("__error__") if isinstance(d, dict) else "non-dict"}
    data = d.get("data") or {}
    sm = data.get("state_machine") or {}
    mon = data.get("monitor") or {}
    return {"fsm": sm.get("status"), "fsm_phase": sm.get("phase"), "training_active": data.get("training_active"), "hidden_units": mon.get("current_hidden_units")}


def cascor_idle(cs: dict) -> bool:
    return cs.get("training_active") is False and (cs.get("fsm") or "").upper() in IDLE_FSM


def server_poller(stop: threading.Event, out: list) -> None:
    while not stop.is_set():
        t = time.time()
        out.append({"t": t, "api_state": api_state(), "api_status": api_status(), "cascor": cascor_status()})
        stop.wait(max(0.0, 1.0 - (time.time() - t)))


class Wire:
    """Census of Dash callback POSTs (counts, live) plus a BOUNDED body read after the run.

    Bodies are never read mid-run: Chromium serves ``Network.getResponseBody`` from the renderer main
    thread, which this page keeps busy for seconds at a time -- the dry run lost ~60 s of sampling to it.
    """

    def __init__(self) -> None:
        self.req_counts: collections.Counter = collections.Counter()
        self.resp_counts: collections.Counter = collections.Counter()
        self.fail_counts: collections.Counter = collections.Counter()
        self.responses: list = []  # (t, output, Response) for candidate-metrics-panel outputs
        self.events: list = []

    @staticmethod
    def _is_dash(req) -> bool:
        return req.method == "POST" and req.url.endswith("/_dash-update-component")

    @staticmethod
    def _output(req) -> str:
        try:
            return (req.post_data_json or {}).get("output") or "?"
        except Exception:  # noqa: BLE001
            return "?"

    def on_request(self, req) -> None:
        if self._is_dash(req):
            out = self._output(req)
            self.req_counts[out] += 1
            if "candidate-metrics-panel" in out:
                self.events.append({"t": time.time(), "kind": "request", "output": out})

    def on_response(self, resp) -> None:
        req = resp.request
        if self._is_dash(req):
            out = self._output(req)
            self.resp_counts[out] += 1
            if "candidate-metrics-panel" in out:
                t = time.time()
                self.responses.append((t, out, resp))
                self.events.append({"t": t, "kind": "response", "output": out, "http": resp.status})

    def on_failed(self, req) -> None:
        if self._is_dash(req):
            self.fail_counts[self._output(req)] += 1

    def read_bodies(self, want, budget_s: float) -> dict:
        """Parse bodies of the responses ``want(t, output)`` selects, newest-relevant first, within a time budget."""
        t_start = time.time()
        picked = [r for r in self.responses if want(r[0], r[1])]
        done = 0
        for t, out, resp in picked:
            if time.time() - t_start > budget_s:
                break
            ev = {"t": t, "kind": "body", "output": out, "http": resp.status}
            try:
                raw = resp.body()
                ev["bytes"] = len(raw)
                ev["values"] = _extract(json.loads(raw.decode() or "null") if raw else None)
            except Exception as e:  # noqa: BLE001
                ev["body_error"] = f"{type(e).__name__}: {e}"[:200]
            self.events.append(ev)
            done += 1
        return {"selected": len(picked), "read": done, "seconds": round(time.time() - t_start, 2), "budget_s": budget_s}


def _extract(payload):
    if not isinstance(payload, dict):
        return None
    out = {}
    for cid, props in (payload.get("response") or {}).items():
        if not isinstance(props, dict):
            continue
        if cid == "candidate-metrics-panel-training-state-store":
            data = props.get("data")
            out[cid] = {k: data.get(k) for k in SERVER_KEYS} if isinstance(data, dict) else repr(data)[:80]
        elif cid in (BADGE, PHASE, SIZE):
            out[cid] = props.get("children")
        else:
            out[cid] = sorted(props.keys())
    return out


def snapshot(page) -> dict:
    return page.evaluate(SNAPSHOT_JS, [list(WATCH_IDS), TAB_TEXT])


def wait_mount(page) -> dict:
    """First snapshot, then the first one where the badge callback has rendered text."""
    first = snapshot(page)
    deadline = time.time() + 20
    snap = first
    while time.time() < deadline and not (snap["text"].get(BADGE) or "").strip():
        page.wait_for_timeout(250)
        snap = snapshot(page)
    return {"first": first, "rendered": snap, "badge_rendered": bool((snap["text"].get(BADGE) or "").strip())}


def dismiss_modal(page) -> dict:
    res: dict = {"seen": False}
    btn = page.locator("#welcome-modal-close")
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            if btn.count() and btn.first.is_visible():
                res["seen"] = True
                break
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(250)
    if res["seen"]:
        t = time.time()
        res["click"] = click_robust(btn.first)
        deadline = time.time() + 30  # the close is a server callback; measured 6.7 s behind its click under load
        while time.time() < deadline:
            if not (btn.count() and btn.first.is_visible()):
                res["dismissed"] = True
                res["hidden_after_s"] = round(time.time() - t, 2)
                break
            page.wait_for_timeout(250)
    res["visible_after"] = bool(btn.count() and btn.first.is_visible())
    return res


def click_robust(loc) -> dict:
    """Trusted CDP click (force: canopy never reaches DOM stability); a DOM click event only if that times out."""
    t = time.time()
    try:
        loc.click(force=True, timeout=40000)
        return {"method": "trusted locator.click(force=True)", "s": round(time.time() - t, 2)}
    except Exception as e:  # noqa: BLE001
        err = str(e).splitlines()[0][:200]
    t2 = time.time()
    loc.dispatch_event("click")
    return {"method": "FALLBACK dispatch_event('click') after trusted click failed", "trusted_error": err, "trusted_s": round(t2 - t, 2), "s": round(time.time() - t2, 2)}


def activate_tab(page) -> dict:
    res: dict = {}
    loc = page.get_by_role("tab", name=TAB_TEXT, exact=True)
    res["role_tab_matches"] = loc.count()
    if res["role_tab_matches"] == 1:
        res["how_found"] = f"get_by_role('tab', name={TAB_TEXT!r}, exact=True)"
    else:
        loc = page.locator(".nav-link", has_text=re.compile(rf"^\s*{re.escape(TAB_TEXT)}\s*$"))
        res["how_found"] = f"fallback: .nav-link with exact text {TAB_TEXT!r} ({loc.count()} matches)"
    el = loc.first
    res["before_click"] = el.evaluate(DESCRIBE_JS)
    res["snapshot_before_click"] = snapshot(page)
    res["click"] = click_robust(el)
    t_click = time.time()
    verified = False
    deadline = t_click + 30
    while time.time() < deadline:
        desc = el.evaluate(DESCRIBE_JS)
        snap = snapshot(page)
        tab_on = desc.get("aria_selected") == "true" or "active" in (desc.get("cls") or "").split()
        pane_on = "active" in (snap.get("badge_pane_cls") or "").split()
        if tab_on and pane_on and snap.get("badge_visible") and snap.get("active_tabs") == [TAB_TEXT]:
            verified = True
            break
        page.wait_for_timeout(250)
    res.update(after_click=desc, snapshot_after_click=snap, verified=verified, verify_s=round(time.time() - t_click, 2))
    res["verification_rule"] = "tab element aria-selected=='true' or class 'active'; the badge's enclosing .tab-pane has class 'active'; badge.checkVisibility() true; and the only active tab in that tablist is 'Candidate Metrics'"
    return res


def toggle_control(page) -> dict:
    """Fire the ACTIVE control. A DOM click event, not a trusted CDP click: the latter blocked 2-18 s here."""
    t = time.time()
    try:
        page.locator(f"#{HIST_TOGGLE}").dispatch_event("click", timeout=15000)
        return {"t": t, "ok": True, "s": round(time.time() - t, 2)}
    except Exception as e:  # noqa: BLE001
        return {"t": t, "ok": False, "err": f"{type(e).__name__}: {e}"[:200], "s": round(time.time() - t, 2)}


def launch_growth(args, grow: dict):
    """Start the growth window AT MOST ONCE. Marks 'launched' before Popen so a raise cannot lead to a retry."""
    grow_out = args.grow_out if os.path.isabs(args.grow_out) else os.path.join(REPO, args.grow_out)
    cs = cascor_status()
    grow["cascor_at_launch_check"] = cs
    grow["checked_t"] = time.time()
    if os.path.exists(grow_out):
        grow["refused"] = f"growth record already exists ({grow_out}) -- one window only, never twice"
        return None, None
    if not cascor_idle(cs):
        grow["refused"] = "cascor is not idle -- will not start another window"
        return None, None
    cmd = ["python3", GROW_SCRIPT, "--to", str(args.grow_to), "--out", grow_out]
    fh = tempfile.TemporaryFile(mode="w+")
    grow.update(launched=True, launch_t=time.time(), cmd=cmd)
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT, text=True)  # noqa: S603 -- fixed argv
    print(f"[grow] launched pid={proc.pid}: {' '.join(cmd)}", flush=True)
    return proc, fh


def training_intervals(server_tl: list) -> list:
    """[start_t, end_t] runs of consecutive server-timeline entries with candidate_pool_status == 'Training'."""
    runs, cur = [], None
    for e in server_tl:
        on = (e["api_state"] or {}).get("candidate_pool_status") == "Training"
        if on and cur is None:
            cur = [e["t"], e["t"]]
        elif on:
            cur[1] = e["t"]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    return runs


def control_chain(toggles: list, icon_changes: list, wire_events: list, t0: float) -> dict:
    """Pair the ACTIVE control FIFO by order: k-th toggle -> k-th toggle request -> k-th response -> k-th icon change.

    A naive "first icon change after each toggle" pairing is WRONG here: the round trip (2-6 s) plus the
    renderer's apply delay (3-7 s) exceeds the toggle spacing, so it hands two toggles the same change.
    FIFO is sound only if every stage has the same count and the icon alternates; both are reported.
    """
    def rel(kind: str) -> list:
        return [round(e["t"] - t0, 3) for e in wire_events if e["kind"] == kind and "history-collapse" in e["output"]]

    reqs, resps = rel("request"), rel("response")
    changes = [c for c in icon_changes if c[0] > 0]
    alternates = all(a[1] != b[1] for a, b in zip(changes, changes[1:]))
    chain = []
    for k, tg in enumerate(toggles):
        def at(seq: list, i: int = k):
            return seq[i] if i < len(seq) else None

        ch = at(changes)
        chain.append({"toggle_dispatch_t_rel": tg["t_rel"], "ok": tg.get("ok"), "request_t_rel": at(reqs), "response_t_rel": at(resps), "icon_change_t_rel": ch[0] if ch else None, "icon_to": ch[1] if ch else None})
    counts = {"toggles": len(toggles), "requests": len(reqs), "responses": len(resps), "icon_changes_after_install": len(changes)}
    return {"counts": counts, "icon_alternates": alternates, "fifo_valid": len(set(counts.values())) == 1 and alternates, "chain": chain}


def analyse(samples: list, server_tl: list, obs, wire: Wire, t0: float, grow: dict, toggles: list) -> dict:
    A: dict = {"n_samples": len(samples)}
    A["n_samples_server_training"] = sum(1 for s in samples if (s["srv"] or {}).get("candidate_pool_status") == "Training")

    def ct(dom_id: str, key: str, subset=None) -> list:
        c = collections.Counter(((s["dom"]["text"].get(dom_id), (s["srv"] or {}).get(key)) for s in (subset if subset is not None else samples)))
        return [{"dom": k[0], "server": k[1], "n": v} for k, v in c.most_common()]

    A["crosstab_badge_vs_candidate_pool_status"] = ct(BADGE, "candidate_pool_status")
    A["crosstab_phase_vs_candidate_pool_phase"] = ct(PHASE, "candidate_pool_phase")
    A["crosstab_pool_size_vs_candidate_pool_size"] = ct(SIZE, "candidate_pool_size")
    A["crosstab_top_status_vs_status"] = ct("top-status-display", "status")
    A["distinct_dom_values"] = {i: sorted({str(s["dom"]["text"].get(i)) for s in samples}) for i in WATCH_IDS if i != INFO}
    A["distinct_pool_info_values"] = sorted({str(s["dom"]["text"].get(INFO)) for s in samples})[:10]
    A["distinct_server_values"] = {k: sorted({str((s["srv"] or {}).get(k)) for s in samples}) for k in ("status", "candidate_pool_status", "candidate_pool_phase", "candidate_pool_size")}
    tr = [s for s in samples if (s["srv"] or {}).get("candidate_pool_status") == "Training"]
    A["during_server_training"] = {i: sorted({str(s["dom"]["text"].get(i)) for s in tr}) for i in WATCH_IDS if i != INFO}
    A["during_server_training_pool_info"] = sorted({str(s["dom"]["text"].get(INFO)) for s in tr})[:10]
    A["active_tab_per_sample"] = {json.dumps(k): v for k, v in collections.Counter(tuple(s["dom"].get("active_tabs") or []) for s in samples).items()}
    A["badge_visible_per_sample"] = dict(collections.Counter(str(s["dom"].get("badge_visible")) for s in samples))
    A["samples_off_mount_during_training"] = sum(1 for s in tr if any(s["dom"]["text"].get(i) != v for i, v in MOUNT.items()))
    gaps = [b["t"] - a["t"] for a, b in zip(samples, samples[1:])]
    A["sample_gap_s"] = {"max": round(max(gaps), 2), "median": round(statistics.median(gaps), 2)} if gaps else None
    A["dom_eval_ms"] = {"max": max(s["dom_ms"] for s in samples), "median": statistics.median(s["dom_ms"] for s in samples)} if samples else None

    runs = training_intervals(server_tl)
    A["server_timeline_n"] = len(server_tl)
    A["server_timeline_training_entries"] = sum(1 for e in server_tl if (e["api_state"] or {}).get("candidate_pool_status") == "Training")
    A["server_training_intervals_rel_s"] = [[round(a - t0, 2), round(b - t0, 2)] for a, b in runs]
    A["server_timeline_distinct"] = {k: sorted({str((e["api_state"] or {}).get(k)) for e in server_tl}) for k in ("status", "candidate_pool_status", "candidate_pool_phase", "candidate_pool_size")}
    A["cascor_fsm_distinct"] = sorted({f"{(e['cascor'] or {}).get('fsm')}/{(e['cascor'] or {}).get('fsm_phase')}" for e in server_tl})

    if obs and isinstance(obs.get("log"), list):
        per: dict = collections.defaultdict(list)
        for ev in obs["log"]:
            for k, v in (ev.get("changed") or {}).items():
                per[k].append([round(ev["t_ms"] / 1000.0 - t0, 3), v if k != INFO else (v or "")[:120]])
        A["observer_changes_per_id"] = {k: len(v) for k, v in per.items()}
        A["observer_distinct_values"] = {k: sorted({str(x[1]) for x in v})[:15] for k, v in per.items()}
        A["observer_panel_changes"] = {k: per.get(k, []) for k in (BADGE, PHASE, SIZE)}
        A["observer_tab_changes"] = per.get("__tab", [])
        in_runs = []
        for k in (BADGE, PHASE, SIZE, INFO):
            for rel, v in per.get(k, []):
                ts = rel + t0
                if any(a - 0.5 <= ts <= b + 1.5 for a, b in runs):
                    in_runs.append({"id": k, "t_rel": rel, "value": v})
        A["observer_panel_changes_inside_server_training"] = in_runs
        for k in CONTROL_IDS + (HIST_ICON,):
            A.setdefault("observer_control_changes_after_growth_launch", {})[k] = sum(1 for rel, _v in per.get(k, []) if grow.get("launch_t") and grow["launch_t"] - t0 <= rel)
            A.setdefault("observer_control_changes_after_install", {})[k] = max(0, len(per.get(k, [])) - 1)  # minus the install baseline
        A["observer_hist_icon_changes"] = per.get(HIST_ICON, [])
        A["active_control_chain"] = control_chain(toggles, per.get(HIST_ICON, []), wire.events, t0)
    else:
        A["observer"] = "NO OBSERVER LOG HARVESTED"

    A["crosstab_top_status_vs_fsm_status"] = [{"dom": k[0], "server": k[1], "n": v} for k, v in collections.Counter((s["dom"]["text"].get("top-status-display"), (s.get("srv_status") or {}).get("fsm_status")) for s in samples).most_common()]
    A["crosstab_top_hidden_units_vs_hidden_units"] = [{"dom": k[0], "server": k[1], "n": v} for k, v in collections.Counter((s["dom"]["text"].get("top-hidden-units-display"), (s.get("srv_status") or {}).get("hidden_units")) for s in samples).most_common()]
    A["wire_candidate_outputs"] = {k: {"requests": wire.req_counts[k], "responses": wire.resp_counts[k], "failed": wire.fail_counts[k]} for k in sorted(set(wire.req_counts) | set(wire.resp_counts)) if "candidate-metrics-panel" in k}
    A["wire_top_status_outputs"] = {k: {"requests": wire.req_counts[k], "responses": wire.resp_counts[k]} for k in wire.req_counts if "top-status-display" in k}
    A["wire_total"] = {"requests": sum(wire.req_counts.values()), "responses": sum(wire.resp_counts.values()), "failed": sum(wire.fail_counts.values())}
    if grow.get("launch_t"):
        after = [e for e in wire.events if e["t"] >= grow["launch_t"] and e["kind"] in ("request", "response")]
        A["wire_candidate_outputs_after_growth_launch"] = {k: v for k, v in collections.Counter(f"{e['kind']}: {e['output'][:110]}" for e in after).items()}
    resp_vals = [e.get("values") or {} for e in wire.events if e["kind"] == "body"]
    A["wire_store_pool_status_values"] = dict(collections.Counter(str((v.get("candidate-metrics-panel-training-state-store") or {}).get("candidate_pool_status")) for v in resp_vals if "candidate-metrics-panel-training-state-store" in v))
    A["wire_badge_children_values"] = dict(collections.Counter(str(v.get(BADGE)) for v in resp_vals if BADGE in v))
    A["wire_pool_size_children_values"] = dict(collections.Counter(str(v.get(SIZE)) for v in resp_vals if SIZE in v))
    return A


def reanalyse(path: str) -> int:
    """Replace the v0.1.0 naive toggle->icon pairing in a saved record with the FIFO chain, and say so in the record."""
    with open(path, encoding="utf-8") as f:
        rec = json.load(f)
    t0 = rec["t0"]
    icon = []
    for ev in (rec.get("observer") or {}).get("log") or []:
        if HIST_ICON in (ev.get("changed") or {}):
            icon.append([round(ev["t_ms"] / 1000.0 - t0, 3), ev["changed"][HIST_ICON]])
    a = rec.setdefault("analysis", {})
    a["active_control_chain"] = control_chain(rec.get("active_control_toggles") or [], icon, rec.get("wire_candidate_events") or [], t0)
    old = a.pop("active_control_toggle_to_icon_change", None)
    if old is not None:
        rec.setdefault("analysis_corrections", []).append({
            "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "field": "analysis.active_control_toggle_to_icon_change -> analysis.active_control_chain",
            "why": (
                "v0.1.0 paired each toggle with the first icon change after its dispatch. When the dispatch->icon latency is "
                "comparable to the toggle spacing, that hands a toggle its PREDECESSOR's change (in the 2026-09-22 real run toggles "
                "1 and 2 were both assigned the +20.6 s change). Replaced by a FIFO chain over toggle -> wire request -> wire "
                "response -> icon change, valid only when all four counts agree and the icon alternates (see fifo_valid)."
            ),
            "superseded_value": old,
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, default=str)
    print(json.dumps(a["active_control_chain"], indent=1, ensure_ascii=False), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="JSON record path (required unless --reanalyse)")
    ap.add_argument("--reanalyse", metavar="RECORD", help="recompute the active-control chain of a saved record in place (no browser, no growth)")
    ap.add_argument("--grow-out", default="reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA1_grow_62.json")
    ap.add_argument("--grow-to", type=int, default=62)
    ap.add_argument("--grow-at", type=float, default=15.0, help="seconds into sampling to start the ONE growth window")
    ap.add_argument("--min-seconds", type=float, default=100.0)
    ap.add_argument("--post-grow-seconds", type=float, default=20.0, help="keep sampling this long after the growth window ends")
    ap.add_argument("--max-seconds", type=float, default=720.0)
    ap.add_argument("--no-grow", action="store_true", help="never start a growth window (dry run / idle baseline)")
    ap.add_argument("--toggle-at", type=float, nargs="*", default=[8.0, 20.0, 32.0], help="seconds into sampling at which to toggle Pool History (the ACTIVE control)")
    ap.add_argument("--body-budget", type=float, default=60.0, help="seconds allowed for the post-run response-body read")
    args = ap.parse_args()
    if args.reanalyse:
        return reanalyse(args.reanalyse)
    if not args.out:
        ap.error("--out is required unless --reanalyse is given")

    rec: dict = {"script": os.path.relpath(__file__, REPO), "argv": sys.argv[1:], "canopy": CANOPY, "cascor": CASCOR, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    pre_cascor = cascor_status()
    other_renderers = subprocess.run(["pgrep", "-fc", "chrome-headless-shell --type=renderer"], capture_output=True, text=True, check=False).stdout.strip()  # noqa: S603,S607
    rec["preflight"] = {"t": time.time(), "canopy_health": get_json(CANOPY + "/v1/health"), "cascor": pre_cascor, "api_state": api_state(), "api_status": api_status(), "loadavg": os.getloadavg(), "cpu_count": os.cpu_count(), "other_headless_renderers_before_launch": other_renderers}
    preexisting = not cascor_idle(pre_cascor)
    rec["preexisting_window"] = preexisting
    print(f"[pre] canopy git_sha={rec['preflight']['canopy_health'].get('git_sha')} version={rec['preflight']['canopy_health'].get('version')} cascor={pre_cascor} preexisting_window={preexisting}", flush=True)

    grow: dict = {"launched": False, "mode": "no-grow" if args.no_grow else ("observe-preexisting" if preexisting else "grow-once")}
    wire = Wire()
    console: list = []
    server_tl: list = []
    stop = threading.Event()
    poller = threading.Thread(target=server_poller, args=(stop, server_tl), daemon=True)
    samples: list = []
    toggles: list = []
    pending_toggles = sorted(args.toggle_at)
    proc = fh = None
    obs = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        page.on("request", wire.on_request)
        page.on("response", wire.on_response)
        page.on("requestfailed", wire.on_failed)

        def _console(m) -> None:
            if m.type in ("error", "warning"):
                console.append({"t": time.time(), "type": m.type, "text": m.text[:300]})

        page.on("console", _console)
        page.on("pageerror", lambda e: console.append({"t": time.time(), "type": "pageerror", "text": str(e)[:300]}))
        # Any failure after the growth launch must still produce a record: the window cannot be re-run.
        try:
            t_nav = time.time()
            page.goto(CANOPY + "/dashboard/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(f"#{BADGE}", state="attached", timeout=60000)
            rec["nav"] = {"url": page.url, "attached_s": round(time.time() - t_nav, 2)}
            rec["mount"] = wait_mount(page)
            print(f"[mount] {rec['mount']['rendered']['text'].get(BADGE)!r} / {rec['mount']['rendered']['text'].get(PHASE)!r} / {rec['mount']['rendered']['text'].get(SIZE)!r} active_tabs={rec['mount']['rendered'].get('active_tabs')}", flush=True)
            rec["modal"] = dismiss_modal(page)
            print(f"[modal] {rec['modal']}", flush=True)
            rec["tab"] = activate_tab(page)
            tab_after = {k: rec["tab"]["after_click"].get(k) for k in ("tag", "role", "aria_selected", "cls")}
            print(f"[tab] how={rec['tab']['how_found']} verified={rec['tab']['verified']} after={tab_after} pane={rec['tab']['snapshot_after_click'].get('badge_pane_cls')!r} visible={rec['tab']['snapshot_after_click'].get('badge_visible')}", flush=True)
            if not rec["tab"]["verified"]:
                grow["refused"] = "Candidate Metrics tab NOT verified active in the DOM -- the one growth window is not spent on an unverified page"
            rec["observer_install"] = page.evaluate(OBSERVER_JS, [list(WATCH_IDS), TAB_TEXT])
            poller.start()

            t0 = time.time()
            rec["t0"] = t0
            next_tick = t0
            while True:
                el = time.time() - t0
                if not args.no_grow and not preexisting and not grow["launched"] and "refused" not in grow and el >= args.grow_at:
                    proc, fh = launch_growth(args, grow)
                if proc is not None and "exit_t" not in grow and proc.poll() is not None:
                    grow.update(exit_t=time.time(), returncode=proc.returncode)
                    print(f"[grow] exited rc={proc.returncode} at el={grow['exit_t'] - t0:.1f}s", flush=True)
                done = el >= args.min_seconds
                if proc is not None:
                    done = done and "exit_t" in grow and time.time() - grow["exit_t"] >= args.post_grow_seconds
                if preexisting:
                    recent = server_tl[-int(args.post_grow_seconds):]
                    done = done and len(recent) >= int(args.post_grow_seconds) and all(cascor_idle(e["cascor"]) for e in recent)
                if done or el >= args.max_seconds:
                    rec["stop_reason"] = "done" if done else "max-seconds"
                    break
                if pending_toggles and el >= pending_toggles[0]:
                    pending_toggles.pop(0)
                    tg = toggle_control(page)
                    tg["t_rel"] = round(tg["t"] - t0, 2)
                    toggles.append(tg)
                    print(f"[control] toggled Pool History at el={tg['t_rel']}s ok={tg['ok']} ({tg['s']}s)", flush=True)
                t_a = time.time()
                try:
                    dom = snapshot(page)
                except Exception as e:  # noqa: BLE001 -- a failed read is a recorded sample, not a crash
                    dom = {"error": f"{type(e).__name__}: {e}"[:300], "text": {}}
                t_b = time.time()
                srv = api_state()
                srv_status = api_status()
                samples.append({"i": len(samples), "t": t_a, "el": round(t_a - t0, 2), "dom_ms": round((t_b - t_a) * 1000), "srv_t": t_b, "dom": dom, "srv": srv, "srv_status": srv_status})
                x = dom["text"]
                print(f"[{t_a - t0:6.1f}s eval={round((t_b - t_a) * 1000):5d}ms] DOM {x.get(BADGE)!r}/{x.get(PHASE)!r}/{x.get(SIZE)!r}", end="")
                print(f" | SRV {srv.get('status')}/{srv.get('candidate_pool_status')}/{srv.get('candidate_pool_phase')}/{srv.get('candidate_pool_size')} ep={srv.get('candidate_epoch')} | CTRL {x.get('top-status-display')!r}/{x.get('top-phase-display')!r} hu={x.get('top-hidden-units-display')!r} ep={x.get('top-epoch-display')!r} icon={x.get(HIST_ICON)!r} (srv {srv_status.get('fsm_status')}/hu={srv_status.get('hidden_units')}) | tab={dom.get('active_tabs')}", flush=True)
                next_tick += 1.0
                delay = next_tick - time.time()
                if delay < 0:
                    next_tick = time.time()
                    delay = 0.0
                page.wait_for_timeout(delay * 1000)

        except Exception:  # noqa: BLE001 -- recorded; the record below is still written
            rec["error"] = traceback.format_exc()[-4000:]
            print(f"[error] {rec['error']}", flush=True)
        finally:
            try:
                obs = page.evaluate(HARVEST_JS)  # ONE patient evaluate after the window
                rec["final_snapshot"] = snapshot(page)
            except Exception as e:  # noqa: BLE001
                rec["harvest_error"] = f"{type(e).__name__}: {e}"[:300]
            stop.set()
            if poller.is_alive():
                poller.join(5)
            try:  # what the server actually handed the page: every badge-consumer response, and store responses in/near Training
                runs = training_intervals(server_tl)
                launch = grow.get("launch_t") or float("inf")
                store_idle = [r[0] for r in wire.responses if "training-state-store" in r[1] and r[0] < launch][-3:]

                def _want(t: float, out: str) -> bool:
                    if BADGE in out:
                        return True
                    return "training-state-store" in out and (t in store_idle or any(a - 3 <= t <= b + 5 for a, b in runs))

                rec["body_read"] = wire.read_bodies(_want, args.body_budget)
            except Exception as e:  # noqa: BLE001
                rec["body_read_error"] = f"{type(e).__name__}: {e}"[:300]
            browser.close()

    if proc is not None:
        if proc.poll() is None:
            try:
                proc.wait(timeout=660)
            except subprocess.TimeoutExpired:
                grow["still_running_at_exit"] = True
        if proc.poll() is not None:
            grow.setdefault("exit_t", time.time())
            grow.setdefault("returncode", proc.returncode)
        fh.seek(0)
        grow["stdout_tail"] = fh.read()[-4000:]
    if rec.get("t0") is None:
        rec["t0"] = time.time()
        rec["error"] = (rec.get("error") or "") + "\n[sampling never started]"
    grow_out = args.grow_out if os.path.isabs(args.grow_out) else os.path.join(REPO, args.grow_out)
    if grow.get("launched") and os.path.exists(grow_out):
        try:
            with open(grow_out, encoding="utf-8") as g:
                gr = json.load(g)
            grow["record_summary"] = {"before": gr.get("before"), "after": gr.get("after"), "verdict": gr.get("verdict")}
        except Exception as e:  # noqa: BLE001
            grow["record_summary"] = f"unreadable: {type(e).__name__}: {e}"[:300]
    for key in ("launch_t", "exit_t", "checked_t"):
        if key in grow:
            grow[key + "_rel"] = round(grow[key] - rec["t0"], 2)

    rec["growth"] = grow
    try:
        rec["analysis"] = analyse(samples, server_tl, obs, wire, rec["t0"], grow, toggles)
    except Exception:  # noqa: BLE001 -- the raw record below must still be written
        rec["analysis"] = {"error": traceback.format_exc()[-3000:]}
    rec["active_control_toggles"] = toggles
    rec["samples"] = samples
    rec["server_timeline"] = [{"t_rel": round(e["t"] - rec["t0"], 2), **e} for e in server_tl]
    rec["observer"] = obs
    rec["wire_candidate_events"] = [{**e, "t_rel": round(e["t"] - rec["t0"], 3)} for e in wire.events]
    rec["wire_counts"] = {"requests": dict(wire.req_counts), "responses": dict(wire.resp_counts), "failed": dict(wire.fail_counts)}
    rec["console"] = console
    out = args.out if os.path.isabs(args.out) else os.path.join(REPO, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, default=str)
    a = rec["analysis"]
    keys = (
        "error", "n_samples", "n_samples_server_training", "distinct_dom_values", "during_server_training", "samples_off_mount_during_training",
        "server_training_intervals_rel_s", "observer_panel_changes_inside_server_training", "observer_distinct_values", "observer_control_changes_after_install",
        "observer_control_changes_after_growth_launch", "active_control_chain", "crosstab_top_status_vs_fsm_status", "crosstab_top_hidden_units_vs_hidden_units",
        "wire_candidate_outputs_after_growth_launch", "wire_store_pool_status_values", "wire_badge_children_values", "sample_gap_s", "dom_eval_ms",
    )
    print(json.dumps({k: a.get(k) for k in keys}, indent=1, default=str), flush=True)
    grow_brief = {k: grow.get(k) for k in ("mode", "launched", "refused", "launch_t_rel", "exit_t_rel", "returncode", "record_summary")}
    print(f"body_read={rec.get('body_read')} growth={grow_brief}", flush=True)
    print(f"=> record -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
