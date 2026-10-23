#!/usr/bin/env python3
"""Which member of each F-CANOPY-069 colliding callback pair runs when its Input fires, per dash version.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 32 (F-CANOPY-069: dash 3.x renders canopy's dashboard inert)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 14, F-CANOPY-069; item 32);
              util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py (the per-dash ALIVE/INERT verdict);
              util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the legs)
License:      MIT License

WHAT IT MEASURES, per leg. Item 32's first step: "read which member of each colliding pair dash 4's graph
runs on a click". The two Inputs are fired in the browser with ``window.dash_clientside.set_props`` (the
renderer's own prop-setting entry point; it notifies the callbacks that take the prop as an Input exactly as a
click does, and reaches a button inside a closed modal, which a real click cannot). For each firing the probe
records, in order:

  - every ``_dash-update-component`` POST the renderer sends whose ``changedPropIds`` carries the fired prop:
    its ``output`` id (which member of the pair), the request order, the response order, status, and the
    component props the response wrote;
  - the progress alert's DOM life (a MutationObserver on the page records the alert element appearing, its
    class changes, and its removal, each with a timestamp), so "the spinner opened and closed" is read from
    the page, not inferred from the responses;
  - the alert's state when the dust settles, and the ``running`` spec (if any) the served dependency list
    carries for each callback on the fired Input.

The fired Inputs are ``restart-confirm-button.n_clicks`` (the restart pair) and
``live-switch-accept-button.n_clicks`` (the live-switch pair). On a demo leg the POSTs behind them reach the
demo backend (``/api/train/restart``) or a closed port (``/api/live_dataset_swap`` is proxied to cascor); the
outcome alerts' text is recorded but not scored. Bootstrap's CDN stylesheet is aborted in the browser (turing's
per-app filter never answers Chrome; see 2026-10-20_item30_fixwave_redrive.py).

Usage:
    <venv with playwright>/bin/python -I util/ad-hoc/2026-10-20_f069_pair_members_probe.py \\
        --base http://127.0.0.1:8062 --label dash-4.4.1-571743db \\
        --out reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

PAIRS = (
    {"name": "restart", "input": "restart-confirm-button.n_clicks", "button": "restart-confirm-button", "alert": "restart-progress-alert"},
    {"name": "live_switch", "input": "live-switch-accept-button.n_clicks", "button": "live-switch-accept-button", "alert": "live-switch-progress-alert"},
)

OBSERVER_JS = """
() => {
  window.__f069 = window.__f069 || {log: []};
  const ids = new Set(['restart-progress-alert', 'live-switch-progress-alert']);
  const note = (kind, node) => {
    if (!node || !node.id || !ids.has(node.id)) return;
    window.__f069.log.push({t: performance.now(), id: node.id, kind: kind, cls: node.className || ''});
  };
  const walk = (node, kind) => {
    if (!node || node.nodeType !== 1) return;
    note(kind, node);
    if (node.querySelectorAll) {
      node.querySelectorAll('[id]').forEach(n => note(kind, n));
    }
  };
  if (window.__f069.observer) return 'already';
  const obs = new MutationObserver(muts => {
    for (const m of muts) {
      if (m.type === 'childList') {
        m.addedNodes.forEach(n => walk(n, 'added'));
        m.removedNodes.forEach(n => walk(n, 'removed'));
      } else if (m.type === 'attributes') {
        note('class', m.target);
      }
    }
  });
  obs.observe(document.body, {childList: true, subtree: true, attributes: true, attributeFilter: ['class']});
  window.__f069.observer = obs;
  return 'installed';
}
"""

ALERT_STATE_JS = """
(id) => {
  const el = document.getElementById(id);
  if (!el) return {present: false};
  const cs = window.getComputedStyle(el);
  return {present: true, cls: el.className || '', display: cs.display, opacity: cs.opacity, text: (el.textContent || '').trim().slice(0, 120)};
}
"""


def http_json(url: str, timeout: float = 20.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 -- loopback test leg
        return json.loads(r.read().decode())


def split_output(raw: str) -> list:
    raw = str(raw)
    if raw.startswith("..") and raw.endswith(".."):
        return raw[2:-2].split("...")
    return [raw]


def callbacks_on_input(deps: list, prop: str) -> list:
    found = []
    for d in deps:
        inputs = [f"{i['id']}.{i['property']}" for i in d.get("inputs", [])]
        if prop in inputs:
            found.append({"output": d["output"][:300], "outputs": split_output(d["output"]), "inputs": inputs, "running": d.get("running")})
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True, help="JSON file; one record per label, merged")
    ap.add_argument("--settle-seconds", type=float, default=20.0)
    ap.add_argument("--fire-budget-seconds", type=float, default=40.0)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    rec: dict = {"label": args.label, "base": base, "probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    health = http_json(base + "/v1/health")
    rec["serving"] = {k: health.get(k) for k in ("version", "git_sha", "demo_mode")}
    deps = http_json(base + "/dashboard/_dash-dependencies")
    rec["callbacks"] = len(deps)
    rec["pairs"] = {}
    for pair in PAIRS:
        rec["pairs"][pair["name"]] = {"input": pair["input"], "served_callbacks": callbacks_on_input(deps, pair["input"])}

    from playwright.sync_api import sync_playwright

    posts: list = []  # dicts: {seq, t, output, changed, status, written, response_seq, response_t}
    console_errors: list = []

    def on_request(r):
        if "_dash-update-component" not in r.url:
            return
        body = {}
        try:
            body = json.loads(r.post_data or "{}")
        except ValueError:
            body = {}
        posts.append({"seq": len(posts) + 1, "t": time.time(), "output": str(body.get("output", ""))[:300], "changed": body.get("changedPropIds", []), "status": None, "written": None, "response_seq": None, "response_t": None, "_req": r})

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        for p in posts:
            if p["_req"] is resp.request:
                p["status"] = resp.status
                p["response_t"] = time.time()
                p["response_seq"] = 1 + sum(1 for q in posts if q["response_seq"] is not None)
                try:
                    data = resp.json()
                    written = {}
                    if data.get("multi"):
                        for cid, props in (data.get("response") or {}).items():
                            written[cid] = sorted(props.keys())
                    else:
                        written = {"<single>": sorted((data.get("response") or {}).get("props", {}).keys())}
                    p["written"] = written
                except Exception as exc:  # noqa: BLE001 -- a non-JSON answer is itself the finding
                    p["written"] = f"non-JSON: {exc.__class__.__name__}"
                break

    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel="chrome", args=["--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width": 1600, "height": 1100})
        ctx.route("https://cdn.jsdelivr.net/**", lambda route, req: route.abort())
        page = ctx.new_page()
        page.on("console", lambda m: console_errors.append(m.text[:400]) if m.type == "error" else None)
        page.on("request", on_request)
        page.on("response", on_response)
        t0 = time.time()
        page.goto(base + "/dashboard/", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(int(args.settle_seconds * 1000))
        rec["duplicate_callback_errors_at_load"] = sum(1 for e in console_errors if "Duplicate callback" in e)
        rec["update_posts_at_settle"] = len(posts)
        page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
        page.wait_for_timeout(1500)
        rec["observer"] = page.evaluate(OBSERVER_JS)
        rec["set_props_available"] = bool(page.evaluate("() => !!(window.dash_clientside && window.dash_clientside.set_props)"))
        for pair in PAIRS:
            prec = rec["pairs"][pair["name"]]
            prec["alert_before"] = page.evaluate(ALERT_STATE_JS, pair["alert"])
            n_before = len(posts)
            page.evaluate("() => { window.__f069.log.length = 0; }")
            t_fire = time.time()
            prec["fired"] = page.evaluate("(id) => { window.dash_clientside.set_props(id, {n_clicks: 1}); return true; }", pair["button"])
            # Wait until every POST this firing caused has answered, or the budget runs out.
            deadline = t_fire + args.fire_budget_seconds
            while time.time() < deadline:
                mine = [p for p in posts[n_before:] if pair["input"] in p["changed"]]
                if mine and all(p["status"] is not None for p in mine) and time.time() - t_fire > 2.0:
                    break
                page.wait_for_timeout(250)
            page.wait_for_timeout(2000)
            mine = [p for p in posts[n_before:] if pair["input"] in p["changed"]]
            prec["posts"] = [
                {
                    "request_order": i + 1,
                    "request_at_s": round(p["t"] - t_fire, 3),
                    "output": p["output"],
                    "outputs": split_output(p["output"]),
                    "status": p["status"],
                    "response_order": p["response_seq"],
                    "response_at_s": round(p["response_t"] - t_fire, 3) if p["response_t"] else None,
                    "wrote": p["written"],
                }
                for i, p in enumerate(mine)
            ]
            prec["other_posts_in_window"] = len(posts[n_before:]) - len(mine)
            log = page.evaluate("() => window.__f069.log.slice()")
            prec["alert_dom_events"] = [{"at_ms": round(e["t"], 1), "kind": e["kind"], "cls": e["cls"]} for e in log if e["id"] == pair["alert"]]
            prec["alert_after"] = page.evaluate(ALERT_STATE_JS, pair["alert"])
            prec["outcome_text"] = page.evaluate(ALERT_STATE_JS, pair["alert"].replace("progress", "outcome")).get("text")
            page.wait_for_timeout(1000)
        rec["console_errors"] = console_errors[:8]
        rec["page_seconds"] = round(time.time() - t0, 1)
        b.close()

    for pair in PAIRS:
        prec = rec["pairs"][pair["name"]]
        members = [p["output"][:60] for p in prec["posts"]]
        ran = len(prec["posts"])
        opened = any(e["kind"] == "added" or "show" in e["cls"] for e in prec["alert_dom_events"])
        closed_after = prec["alert_after"].get("present") is False or "show" not in prec["alert_after"].get("cls", "")
        prec["reading"] = {"members_posted": ran, "served": len(prec["served_callbacks"]), "alert_opened": opened, "alert_closed_at_end": closed_after, "members": members}
    print(json.dumps(rec, indent=2, default=str))
    merged = {}
    if os.path.exists(args.out):
        try:
            with open(args.out, encoding="utf-8") as fh:
                merged = json.load(fh)
        except (OSError, ValueError):
            merged = {}
    merged[args.label] = rec
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2, default=str)
    for pair in PAIRS:
        r = rec["pairs"][pair["name"]]["reading"]
        print(f"{args.label} {pair['name']}: served={r['served']} posted={r['members_posted']} alert_opened={r['alert_opened']} closed_at_end={r['alert_closed_at_end']}")
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
