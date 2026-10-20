#!/usr/bin/env python3
"""Item 30: the Phase 4 fix wave's live re-drive -- F-CANOPY-018, -028, -001 (demo leg) and F-CANOPY-032 (cascor-down leg).

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 30 (ledger Phase 13, "Still owed")
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 13, item 30; the entries
              F-CANOPY-018, -028, -032, -001); notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md
              (C2.9-05, M-PARAMETERS-04/-05/-06, C2.1-01/-02, M-METRICS-03, M-WORKERS-02);
              util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the legs); util/ad-hoc/e2e_w3_params_driver.py and
              util/ad-hoc/e2e_f027_redrive.py (the idioms copied here: dispatched clicks, JS reads, Radix dropdowns)
License:      MIT License

LEGS. Every leg is a throwaway canopy on turing, launched from the E2 tree (canopy main 571743db, proved by
2026-10-20_e2_tree_blob_sha_check.py) by 2026-10-20_turing_canopy_leg.bash. The trio is not on this host.
THE LEG MUST RUN DASH 4.x. Under every dash 3.x (3.0.4, 3.2.0, 3.3.0, 3.4.0 measured 2026-10-20) canopy 571743db's
dashboard is inert in the browser: three callback pairs share an ``allow_duplicate`` output and identical inputs, their
ids collide, and the dash 3 renderer drops the whole callback graph (F-CANOPY-069;
2026-10-20_canopy_dash_duplicate_outputs_probe.py). dash 4.4.1 -- canopy's requirements.lock and its CI -- accepts them.
  demo leg     JUNIPER_CANOPY_DEMO_MODE=1, cascor and juniper-data at a closed port: the Parameters sidebar's Apply
               controls, the pin checkboxes and the dirty tracker are canopy-side (ledger Phase 13), so they are
               reachable here; the demo backend answers /api/set_params itself.
  cascor-down  JUNIPER_CANOPY_DEMO_MODE=0 with the cascor URL at a closed port: the "cascor stopped, canopy up" arm of
               M-WORKERS-02, F-CANOPY-032's first arm.

STEPS (one fresh browser context each, so localStorage starts clean):
  f018  C2.9-05 for F-CANOPY-018. Dirty the form with a dropdown change, click Apply, then sample `params-status`
        and the Apply button's disabled state every 100 ms for --settle-seconds. The row's own expectation is the
        toast (one of the three forms in _compose_apply_toast). The added expectation, scored separately (ledger
        item 30): after a successful apply the button is disabled and the status never reads "Unsaved changes"
        until the form is edited again. The toast's life is read as it is. A second dropdown change afterwards
        must re-enable Apply (the tracker still tracks).
  f028  M-PARAMETERS-04/-05/-06 for F-CANOPY-028. Pin key A; read the store, the sidebar card and list (M-04, M-05);
        reload; read A's checkbox (rehydration) and the store; pin key B; the store must now hold A and B (the
        original symptom was [B] alone). Then unpin both and reload: store empty, card hidden (M-06).
  f001  C2.1-01/-02 for F-CANOPY-001. Click the theme toggle, reload, and read the glyph: the fix derives it from
        the store on mount, so a dark theme after reload must show the sun glyph, not the layout-default moon.
  m03   M-METRICS-03: read `metrics-panel-phase-duration` on the Metrics tab. On a demo leg this is an observation
        only (the F-CANOPY-026 fix has a cascor half); it is scored on a cascor-backed leg.
  f032  M-WORKERS-02 for F-CANOPY-032 (cascor-down arm). Open the Workers tab and sample the error display, the
        status badge and the tiles every 2 s for --workers-seconds; read canopy's own /api/v1/workers/list and
        /stats directly; capture every _dash-update-component response that carries worker-panel-workers-store so
        a filled-store / dead-render split (the F-CANOPY-027 class) can be told from an empty store.

VERDICT RULES -- FIXED BEFORE THE FIRST RUN.
  f018  TOAST      one of the three toast forms appeared in params-status after the click.
        CLEAN      at every sample from +5 s to the end: Apply disabled and status != "Unsaved changes".
        LATCHED    "Unsaved changes" appeared after the apply with no edit in between (the original symptom).
        RETRACK    the second dropdown change re-enabled Apply.
        F-CANOPY-018 closes on TOAST + CLEAN + RETRACK; LATCHED reproduces it.
  f028  SURVIVES   after reload and the second pin the store holds both keys.
        DISCARDED  the store holds only the second key (the original symptom).
        REHYDRATED A's checkbox reads checked after the reload (not required by the fix, recorded).
        F-CANOPY-028 closes on SURVIVES with M-04/-05/-06's own expectations met.
  f001  SYNCED     after the reload the html carries dark-mode AND the glyph is the sun; STALE if it is the moon.
  f032  RENDERED   at any sample the error display's text starts with "Worker data degraded"; NEVER otherwise.
        STORE      FILLED if a captured store payload carries a truthy error, EMPTY if none carries one, UNSEEN if
                   no payload was captured. NEVER + FILLED is the F-CANOPY-027 class; NEVER + EMPTY points at the
                   proxy or the handler.

Usage:
    ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1/bin/python -I \\
        util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --base http://127.0.0.1:8058 --step f018,f028,f001,m03 \\
        --out reports/e2e-canopy-2026-09-02/item30-turing/demo_leg_8058.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

_T0 = time.time()
RESULTS: dict = {}
OUT_PATH = ""
SHOT_DIR = ""
BASE = ""
TOAST_RE = re.compile(r"^(Parameters applied|Applied \d+ (of \d+ )?parameter)")
UNSAVED = "Unsaved changes"
NE_STORE = "worker-panel-workers-store"


def log(msg: str) -> None:
    print(f"[t={int((time.time() - _T0) * 1000):>7d}ms] {msg}", flush=True)


def record(step: str, **kv) -> None:
    RESULTS.setdefault(step, {}).update(kv)
    if OUT_PATH:
        os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
        with open(OUT_PATH, "w", encoding="utf-8") as fh:
            json.dump(RESULTS, fh, indent=2, default=str)


def http(method: str, path: str, body=None, timeout: float = 15.0):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 -- loopback test leg
            raw = r.read().decode() or "null"
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:  # noqa: BLE001 -- recorded, never raised from a probe
        return None, f"{type(e).__name__}: {e}"[:300]


def serving() -> dict:
    code, payload = http("GET", "/v1/health", timeout=5)
    if code != 200 or not isinstance(payload, dict):
        return {"ok": False, "why": f"HTTP {code}: {payload}"}
    return {"ok": True, "git_sha": payload.get("git_sha"), "build_date": payload.get("build_date"), "version": payload.get("version"), "demo_mode": payload.get("demo_mode"), "read_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


# ----------------------------------------------------------------------------- browser helpers
def launch(pw):
    """Playwright over the host's installed Google Chrome (no browser download on turing)."""
    args = ["--disable-dev-shm-usage"]
    try:
        browser = pw.chromium.launch(channel="chrome", headless=True, args=args)
        log("  browser: chrome channel (installed Google Chrome)")
    except Exception as e:  # noqa: BLE001
        log(f"  chrome channel unavailable ({type(e).__name__}); falling back to bundled chromium")
        browser = pw.chromium.launch(headless=True, args=args)
    return browser


CDN_GLOB = "https://cdn.jsdelivr.net/**"
LOCAL_CSS = ""  # --local-bootstrap: a Bootstrap 5 stylesheet already on this host, served to the page in place of the CDN


def _route_cdn(route, request):
    """turing: Google Chrome's outbound connections are filtered per application (Little Snitch), and the dashboard's one
    external resource, dbc.themes.BOOTSTRAP from cdn.jsdelivr.net, never resolves there -- the pending stylesheet holds
    DOMContentLoaded for the whole navigation timeout (probed 2026-10-20: readyState stayed 'loading' for 100 s; curl got
    the same URL in 0.1 s). The browser never attempts that connection here: the request is answered from a local
    copy when one is given, else aborted. Nothing is fetched on Chrome's behalf by another binary."""
    if LOCAL_CSS and request.url.endswith("bootstrap.min.css"):
        with open(LOCAL_CSS, "rb") as fh:
            route.fulfill(status=200, content_type="text/css", body=fh.read())
    else:
        route.abort()


def new_page(browser, captures: dict):
    ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
    ctx.route(CDN_GLOB, _route_cdn)
    page = ctx.new_page()
    page.set_default_timeout(15_000)
    captures.setdefault("requests", [])
    captures.setdefault("responses", [])
    captures.setdefault("console", [])

    def on_request(req):
        if "_dash-update-component" in req.url or "/api/" in req.url:
            try:
                body = req.post_data or ""
            except Exception:  # noqa: BLE001
                body = ""
            keep = 12000 if '"pinned-params-store.data"' in body else 2000
            captures["requests"].append({"t_ms": int((time.time() - _T0) * 1000), "method": req.method, "url": req.url.replace(BASE, ""), "body": body[:keep]})

    def on_response(resp):
        if "_dash-update-component" in resp.url:
            try:
                txt = resp.text()
            except Exception:  # noqa: BLE001
                return
            if NE_STORE in txt or "params-status" in txt or "pinned-params-store" in txt or "dark-mode" in txt:
                captures["responses"].append({"t_ms": int((time.time() - _T0) * 1000), "status": resp.status, "body": txt[:6000]})

    def on_console(msg):
        if msg.type in ("error", "warning"):
            captures["console"].append({"t_ms": int((time.time() - _T0) * 1000), "type": msg.type, "text": msg.text[:400]})

    page.on("request", on_request)
    page.on("response", on_response)
    page.on("console", on_console)
    return ctx, page


MOUNT_MS = 25_000  # --mount-seconds: F-CANOPY-004's fresh-session population envelope (<= 40 s, typically 20-30 s); an
# edit made before the mount seed lands is overwritten by it (seen 2026-10-20: a typed learning rate reverted at +2 s)


def goto(page) -> None:
    page.goto(BASE, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)
    ensure_no_modal(page)
    page.wait_for_timeout(MOUNT_MS)
    ensure_no_modal(page)


def ensure_no_modal(page, tries: int = 12) -> None:
    for i in range(tries):
        n_open = page.evaluate("""() => [...document.querySelectorAll('[role=dialog]')].filter(x => (x.className||'').includes('show')).length""")
        if not n_open:
            if i:
                log(f"  modal cleared after {i} attempt(s)")
            return
        page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
        page.wait_for_timeout(700)
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    log(f"  !! a modal is STILL open after {tries} attempts")


def open_tab(page, label: str, settle_ms: int = 3500) -> bool:
    ensure_no_modal(page)
    ok = page.evaluate(
        """(label) => { const t = [...document.querySelectorAll('[role=tab]')].find(x => x.textContent.trim() === label);
                        if (!t) return false; t.click(); return true; }""",
        label,
    )
    page.wait_for_timeout(settle_ms)
    return bool(ok)


def js_click(page, el_id: str) -> bool:
    """Dispatch the click from the page (the arc's idiom: Playwright's click ack times out on this page)."""
    return bool(page.evaluate("""(id) => { const el = document.getElementById(id); if (!el) return false; el.click(); return true; }""", el_id))


def text_of(page, el_id: str):
    return page.evaluate("""(id) => { const el = document.getElementById(id); return el ? (el.innerText || '').trim() : null; }""", el_id)


def is_disabled(page, el_id: str):
    return page.evaluate("""(id) => { const el = document.getElementById(id); if (!el) return null; return el.disabled === true || el.getAttribute('disabled') !== null; }""", el_id)


def vis(page, el_id: str) -> dict:
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return {present:false};
                     const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
                     return {present:true, display: cs.display, inline: el.style.display || null, w: Math.round(r.width), h: Math.round(r.height), text: (el.innerText||'').trim().slice(0,200), children: el.childElementCount}; }""",
        el_id,
    )


def ls_get(page, key: str):
    raw = page.evaluate("""(k) => localStorage.getItem(k)""", key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def shot(page, name: str) -> str:
    if not SHOT_DIR:
        return ""
    os.makedirs(SHOT_DIR, exist_ok=True)
    p = os.path.join(SHOT_DIR, name)
    try:
        page.screenshot(path=p, full_page=False)
    except Exception as e:  # noqa: BLE001
        log(f"  screenshot failed: {e}")
    return p


def dropdown_value(page, dd_id: str):
    return page.evaluate(
        """(id) => { const root = document.getElementById(id); if (!root) return null;
                     const v = root.querySelector('.dash-dropdown-value-item');
                     return v ? v.innerText.trim() : (root.innerText || '').trim(); }""",
        dd_id,
    )


def dropdown_select(page, dd_id: str, label: str) -> bool:
    """Dash 3.x dcc.Dropdown is a Radix Select: a button, options portalled to the body (W3 driver idiom)."""
    btn = page.locator(f"#{dd_id}")
    if not btn.count():
        log(f"  !! #{dd_id} absent")
        return False
    try:
        btn.scroll_into_view_if_needed()
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    for attempt in (1, 2):
        btn.first.click()
        page.wait_for_timeout(1000)
        opt = page.get_by_role("option", name=label, exact=True)
        if opt.count():
            opt.first.click()
            page.wait_for_timeout(1200)
            return True
        log(f"  !! option '{label}' not found for #{dd_id} on attempt {attempt} (data-state={page.evaluate('(id) => (document.getElementById(id)||{}).getAttribute(\"data-state\")', dd_id)!r})")
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
    return False


def pin_id(key: str) -> str:
    return json.dumps({"key": key, "type": "param-pin"}, separators=(",", ":"), sort_keys=True)


def pin_state(page, key: str):
    return page.evaluate("""(id) => { const el = document.getElementById(id); return el ? {checked: el.checked, present: true} : {present: false}; }""", pin_id(key))


def pin_click(page, key: str) -> bool:
    return js_click(page, pin_id(key))


def wait_store(page, key: str, pred, budget_s: float, every_ms: int = 500):
    """Poll a localStorage-backed store until pred(value) holds; returns (seconds, value) or (None, last value)."""
    t0 = time.time()
    val = ls_get(page, key)
    while time.time() - t0 < budget_s:
        val = ls_get(page, key)
        if pred(val):
            return round(time.time() - t0, 1), val
        page.wait_for_timeout(every_ms)
    return None, val


def wait_for(page, pred, budget_s: float, every_ms: int = 500):
    """Poll an arbitrary page predicate (a callable on the page) until it returns truthy; (seconds, last) or (None, last)."""
    t0 = time.time()
    last = pred(page)
    while time.time() - t0 < budget_s:
        last = pred(page)
        if last:
            return round(time.time() - t0, 1), last
        page.wait_for_timeout(every_ms)
    return None, last


def pin_requests(cap: dict) -> list:
    """The renderer's own view of every pin checkbox at each firing of the store writer: the request bodies whose
    output is pinned-params-store.data, reduced to {key: value} plus the State the writer received."""
    out = []
    for r in cap.get("requests", []):
        if "_dash-update-component" not in r["url"] or '"pinned-params-store.data"' not in r["body"]:
            continue
        try:
            body = json.loads(r["body"])
        except ValueError:
            out.append({"t_ms": r["t_ms"], "raw": r["body"][:300]})
            continue
        if body.get("output") != "pinned-params-store.data":
            continue
        vals = {}
        for grp in body.get("inputs", []):
            for item in grp if isinstance(grp, list) else [grp]:
                cid = item.get("id")
                if isinstance(cid, dict) and cid.get("type") == "param-pin":
                    vals[cid.get("key")] = item.get("value")
        state = None
        for grp in body.get("state", []):
            for item in grp if isinstance(grp, list) else [grp]:
                if item.get("id") == "pinned-params-store":
                    state = item.get("value")
        out.append({"t_ms": r["t_ms"], "checked": sorted(k for k, v in vals.items() if v), "rendered": len(vals), "state_store": state})
    return out


# ----------------------------------------------------------------------------- steps
def step_f018(browser, args) -> None:
    log("STEP f018 -- C2.9-05: Apply toast; added: Apply disabled + status clean after a successful apply (F-CANOPY-018)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving()}
    try:
        goto(page)
        rec["initial"] = {"apply_disabled": is_disabled(page, "apply-params-button"), "status": text_of(page, "params-status")}
        log(f"  initial: {rec['initial']}")
        dd = "nn-optimizer-type-dropdown"
        cur = dropdown_value(page, dd)
        tgt = "Adam" if (cur or "") != "Adam" else "AdamW"
        ok = dropdown_select(page, dd, tgt)
        page.wait_for_timeout(1500)
        rec["dirty"] = {"dropdown_from": cur, "dropdown_to": tgt, "selected": ok, "apply_disabled": is_disabled(page, "apply-params-button"), "status": text_of(page, "params-status")}
        log(f"  after dropdown change: {rec['dirty']}")
        _c, st0 = http("GET", "/api/state")
        rec["state_before"] = {"nn_optimizer_type": (st0 or {}).get("nn_optimizer_type") if isinstance(st0, dict) else st0}
        shot(page, "f018_dirty.png")
        page.focus("#apply-params-button")
        page.wait_for_timeout(300)
        t_click = time.time()
        js_click(page, "apply-params-button")
        samples = []
        while time.time() - t_click < args.settle_seconds:
            samples.append({"t_s": round(time.time() - t_click, 2), "status": text_of(page, "params-status"), "apply_disabled": is_disabled(page, "apply-params-button")})
            page.wait_for_timeout(100)
        rec["samples"] = samples
        _c, st1 = http("GET", "/api/state")
        rec["state_after"] = {"nn_optimizer_type": (st1 or {}).get("nn_optimizer_type") if isinstance(st1, dict) else st1}
        shot(page, "f018_after_apply.png")
        # verdicts
        toasts = [s for s in samples if s["status"] and TOAST_RE.match(s["status"])]
        # LATCHED means the tracker overwrote the toast: "Unsaved changes" AFTER the toast first appeared. The same text
        # before the toast is the pre-click dirty status still on screen (the click's own response takes 1-3 s here).
        toast_t0 = toasts[0]["t_s"] if toasts else None
        unsaved_after = [s for s in samples if s["status"] and UNSAVED in s["status"] and (toast_t0 is not None and s["t_s"] > toast_t0)]
        tail = [s for s in samples if s["t_s"] >= 5.0]
        clean = bool(tail) and all(s["apply_disabled"] is True and not (s["status"] and UNSAVED in s["status"]) for s in tail)
        toast_life = None
        if toasts:
            first_t = toasts[0]["t_s"]
            last_t = toasts[-1]["t_s"]
            toast_life = round(last_t - first_t, 2)
        statuses_seen = []
        for s in samples:
            if not statuses_seen or statuses_seen[-1]["status"] != s["status"]:
                statuses_seen.append({"t_s": s["t_s"], "status": s["status"], "apply_disabled": s["apply_disabled"]})
        rec["status_transitions"] = statuses_seen
        # re-track: a second change must re-enable Apply
        cur2 = dropdown_value(page, dd)
        tgt2 = "Adam" if (cur2 or "") != "Adam" else "AdamW"
        ok2 = dropdown_select(page, dd, tgt2)
        page.wait_for_timeout(2000)
        rec["retrack"] = {"dropdown_from": cur2, "dropdown_to": tgt2, "selected": ok2, "apply_disabled": is_disabled(page, "apply-params-button"), "status": text_of(page, "params-status")}
        log(f"  re-dirty: {rec['retrack']}")
        rec["verdicts"] = {
            "TOAST": bool(toasts),
            "toast_text": toasts[0]["status"] if toasts else None,
            "toast_first_t_s": toasts[0]["t_s"] if toasts else None,
            "toast_visible_span_s": toast_life,
            "CLEAN": clean,
            "LATCHED": bool(unsaved_after),
            "unsaved_first_t_s": unsaved_after[0]["t_s"] if unsaved_after else None,
            "RETRACK": rec["retrack"]["apply_disabled"] is False,
            "apply_landed": rec["state_after"]["nn_optimizer_type"] != rec["state_before"]["nn_optimizer_type"],
        }
        rec["console"] = cap["console"][:30]
        rec["dash_responses_params_status"] = [r for r in cap["responses"] if "params-status" in r["body"]][:12]
        log(f"  f018 verdicts: {json.dumps(rec['verdicts'])}")
    finally:
        record("f018", **rec)
        ctx.close()


def step_f028(browser, args) -> None:
    """Two arms, each in a fresh context. SETTLED pins the second key after the reloaded page has had MOUNT_MS to
    populate (M-PARAMETERS-04/-05/-06 as the matrix states them, plus M-06). EARLY pins it as soon as the reloaded
    page shows the checkbox, which is how run 1 on 2026-10-20 discarded the first pin on code that carries canopy#533:
    the manual's "survives a reload" has no settle clause, so the early arm is the one a user following it drives."""
    key_a, key_b = args.pin_keys.split(",")[:2]
    arms = [a.strip() for a in args.f028_arms.split(",") if a.strip()]
    prior = RESULTS.get("f028", {}) if isinstance(RESULTS.get("f028"), dict) else {}
    rec_all: dict = {"serving": serving(), "key_a": key_a, "key_b": key_b, "arms": dict(prior.get("arms", {}))}
    for rep in range(args.f028_repeat):
        for arm in arms:
            label = arm if args.f028_repeat == 1 else f"{arm}#{rep + 1}"
            log(f"STEP f028/{label} -- M-PARAMETERS-04/-05/-06: pin {key_a}, reload, pin {key_b} ({arm}); the first must survive (F-CANOPY-028)")
            rec_all["arms"][label] = _f028_arm(browser, args, arm, key_a, key_b)
    rec_all["verdicts"] = {k: v.get("verdicts", {}) for k, v in rec_all["arms"].items()}
    rec_all["summary"] = {"arms_driven": len(rec_all["arms"]), "survives": sum(1 for v in rec_all["verdicts"].values() if v.get("SURVIVES")), "discarded": sum(1 for v in rec_all["verdicts"].values() if v.get("DISCARDED"))}
    record("f028", **rec_all)
    log(f"  f028 summary: {json.dumps(rec_all['summary'])}")


def _f028_arm(browser, args, arm: str, key_a: str, key_b: str) -> dict:
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"arm": arm}
    try:
        budget = args.poll_seconds
        goto(page)
        rec["store_fresh"] = ls_get(page, "pinned-params-store")
        open_tab(page, "Parameters", 2000)
        t_tab, n_cb = wait_for(page, lambda p: p.evaluate("""() => document.querySelectorAll('input[type=checkbox][id*="param-pin"]').length"""), budget)
        rec["checkboxes_rendered"] = {"after_s": t_tab, "count": n_cb}
        # the tables re-render when the params store fills (late on a fresh session); pin only once a value shows
        t_val, _ = wait_for(page, lambda p: (p.evaluate("""() => { const t = document.getElementById('parameters-panel-network-table'); return t && t.innerText.includes('0.01'); }""")), budget)
        rec["checkboxes_rendered"]["values_after_s"] = t_val
        rec["a_before"] = pin_state(page, key_a)
        log(f"  Parameters tab: {n_cb} pin checkboxes after {t_tab}s, values after {t_val}s; {key_a} before={rec['a_before']}")
        pin_click(page, key_a)
        t_a, store_a = wait_store(page, "pinned-params-store", lambda v: v and key_a in v, budget)
        page.wait_for_timeout(1500)
        rec["m04"] = {"store": store_a, "store_after_s": t_a, "a_checked": pin_state(page, key_a)}
        t_card, _ = wait_for(page, lambda p: p.evaluate("""() => { const c = document.getElementById('sidebar-pinned-card'); return c && getComputedStyle(c).display !== 'none'; }"""), budget)
        rec["m05"] = {"card": vis(page, "sidebar-pinned-card"), "card_after_s": t_card, "list_text": text_of(page, "sidebar-pinned-list")}
        log(f"  M-04 store={store_a} after {t_a}s ; M-05 card display={rec['m05']['card'].get('display')} after {t_card}s list={rec['m05']['list_text']!r}")
        shot(page, "f028_pinned_a.png")
        rec["pin_requests_before_reload"] = pin_requests(cap)
        # reload: same context, so localStorage survives
        n_req_mark = len(cap["requests"])
        page.reload(wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        ensure_no_modal(page)
        rec["after_reload"] = {"store_immediately": ls_get(page, "pinned-params-store")}
        t_reload = time.time()
        if arm == "settled":
            page.wait_for_timeout(MOUNT_MS)
            ensure_no_modal(page)
        elif arm == "mid":
            # run 1's timing (2026-10-20): 4 s after the reload, the tab opened with a 5 s settle, the pin at ~10 s
            page.wait_for_timeout(1000)
            ensure_no_modal(page)
        rec["after_reload"]["store_after_wait"] = ls_get(page, "pinned-params-store")
        rec["after_reload"]["card"] = vis(page, "sidebar-pinned-card")
        open_tab(page, "Parameters", {"early": 500, "mid": 5000}.get(arm, 2000))
        t_tab2, _ = wait_for(page, lambda p: p.evaluate("""(k) => !!document.getElementById(k)""", pin_id(key_a)), budget, every_ms=100 if arm == "early" else 500)
        t_val2 = None
        if arm == "settled":
            t_val2, _ = wait_for(page, lambda p: (p.evaluate("""() => { const t = document.getElementById('parameters-panel-network-table'); return t && t.innerText.includes('0.01'); }""")), budget)
        rec["after_reload"]["tables_after_s"] = t_tab2
        rec["after_reload"]["values_after_s"] = t_val2
        rec["after_reload"]["second_pin_at_s_after_reload"] = round(time.time() - t_reload, 1)
        rec["after_reload"]["a_checkbox"] = pin_state(page, key_a)
        rec["after_reload"]["store_before_second_pin"] = ls_get(page, "pinned-params-store")
        rec["after_reload"]["list_text"] = text_of(page, "sidebar-pinned-list")
        log(f"  after reload: store={rec['after_reload']['store_before_second_pin']} card={rec['after_reload']['card'].get('display')} tables after {t_tab2}s values after {t_val2}s; {key_a} checkbox={rec['after_reload']['a_checkbox']}")
        shot(page, "f028_after_reload.png")
        # second pin: the store must CHANGE (poll for any change, then settle)
        before2 = ls_get(page, "pinned-params-store")
        pin_click(page, key_b)
        t_b, store_b = wait_store(page, "pinned-params-store", lambda v: v != before2, budget)
        page.wait_for_timeout(3000)
        store_b_settled = ls_get(page, "pinned-params-store")
        rec["after_second_pin"] = {"store_first_change": store_b, "store_changed_after_s": t_b, "store_settled": store_b_settled, "a_checked": pin_state(page, key_a), "b_checked": pin_state(page, key_b), "card": vis(page, "sidebar-pinned-card"), "list_text": text_of(page, "sidebar-pinned-list")}
        log(f"  after pinning {key_b}: store {before2} -> {store_b} after {t_b}s, settled {store_b_settled}; list={rec['after_second_pin']['list_text']!r}")
        shot(page, "f028_after_second_pin.png")
        rec["pin_requests_after_reload"] = pin_requests({"requests": cap["requests"][n_req_mark:]})
        rec["pin_request_bodies_after_reload"] = [r["body"][:12000] for r in cap["requests"][n_req_mark:] if '"pinned-params-store.data"' in r["body"]][:6]
        for r in rec["pin_requests_after_reload"]:
            log(f"    pin writer fired t={r.get('t_ms')}ms rendered={r.get('rendered')} checked={r.get('checked')} state={r.get('state_store')} raw={(r.get('raw') or '')[:80]!r}")
        store2 = store_b_settled or []
        rec["verdicts"] = {
            "SURVIVES": key_a in store2 and key_b in store2,
            "DISCARDED": store2 == [key_b],
            "REHYDRATED": bool((rec["after_reload"]["a_checkbox"] or {}).get("checked")),
            "M04": store_a == [key_a],
            "M05": (rec["m05"]["card"].get("display") not in (None, "none")) and bool(rec["m05"]["list_text"]),
            "second_pin_at_s_after_reload": rec["after_reload"]["second_pin_at_s_after_reload"],
        }
        if arm != "settled":
            rec["console"] = cap["console"][:30]
            rec["dash_responses_pinned_store"] = [r for r in cap["responses"] if "pinned-params-store" in r["body"]][:20]
            log(f"  f028/{arm}: {json.dumps(rec['verdicts'])}")
            return rec
        # M-06: unpin all, reload (settled arm only)
        for k in (key_a, key_b):
            st = pin_state(page, k)
            if st.get("checked"):
                before = ls_get(page, "pinned-params-store")
                pin_click(page, k)
                wait_store(page, "pinned-params-store", lambda v, _b=before: v != _b, budget)
                page.wait_for_timeout(1500)
        t_hide, _ = wait_for(page, lambda p: p.evaluate("""() => { const c = document.getElementById('sidebar-pinned-card'); return c && getComputedStyle(c).display === 'none'; }"""), budget)
        rec["after_unpin"] = {"store": ls_get(page, "pinned-params-store"), "card": vis(page, "sidebar-pinned-card"), "card_hidden_after_s": t_hide}
        page.reload(wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        ensure_no_modal(page)
        page.wait_for_timeout(MOUNT_MS)
        rec["after_unpin_reload"] = {"store": ls_get(page, "pinned-params-store"), "card": vis(page, "sidebar-pinned-card")}
        rec["verdicts"]["M06"] = (rec["after_unpin"]["store"] in ([], None)) and rec["after_unpin"]["card"].get("display") == "none" and (rec["after_unpin_reload"]["store"] in ([], None)) and rec["after_unpin_reload"]["card"].get("display") == "none"
        log(f"  M-06 after unpin: store={rec['after_unpin']['store']} card={rec['after_unpin']['card'].get('display')} (hidden after {t_hide}s); after reload: store={rec['after_unpin_reload']['store']} card={rec['after_unpin_reload']['card'].get('display')}")
        rec["console"] = cap["console"][:30]
        rec["dash_responses_pinned_store"] = [r for r in cap["responses"] if "pinned-params-store" in r["body"]][:20]
        log(f"  f028/{arm}: {json.dumps(rec['verdicts'])}")
        return rec
    finally:
        ctx.close()


def _theme(page) -> dict:
    return page.evaluate(
        """() => { const b = document.getElementById('dark-mode-toggle');
                   return {glyph: b ? (b.innerText||'').trim() : null, html_dark: document.documentElement.classList.contains('dark-mode'),
                           html_class: document.documentElement.className, store: localStorage.getItem('dark-mode-store')}; }"""
    )


def step_f001(browser, args) -> None:
    log("STEP f001 -- C2.1-01/-02: theme toggle, reload, glyph synced from the store on mount (F-CANOPY-001)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving()}
    try:
        budget = args.poll_seconds
        goto(page)
        rec["initial"] = _theme(page)
        log(f"  initial: {rec['initial']}")
        init_dark = rec["initial"]["html_dark"]
        js_click(page, "dark-mode-toggle")
        t_html, _ = wait_for(page, lambda p: p.evaluate("document.documentElement.classList.contains('dark-mode')") is not init_dark, budget)
        t_glyph, _ = wait_for(page, lambda p: (p.evaluate("(document.getElementById('dark-mode-toggle')||{innerText:''}).innerText.trim()") != rec["initial"]["glyph"]), budget)
        rec["after_click"] = {**_theme(page), "html_flipped_after_s": t_html, "glyph_swapped_after_s": t_glyph}
        log(f"  after click: {rec['after_click']}")
        shot(page, "f001_dark.png")
        page.reload(wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)
        ensure_no_modal(page)
        rec["after_reload_early"] = _theme(page)
        t_sync, _ = wait_for(page, lambda p: (p.evaluate("(document.getElementById('dark-mode-toggle')||{innerText:''}).innerText.trim()") == ("☀️" if rec["after_click"]["html_dark"] else "🌙")), budget)
        rec["after_reload"] = {**_theme(page), "glyph_synced_after_s": t_sync}
        log(f"  after reload: early {rec['after_reload_early']} ; settled {rec['after_reload']}")
        shot(page, "f001_after_reload.png")
        dark_now = rec["after_reload"]["html_dark"]
        js_click(page, "dark-mode-toggle")
        t_html2, _ = wait_for(page, lambda p: p.evaluate("document.documentElement.classList.contains('dark-mode')") is not dark_now, budget)
        rec["after_second_click"] = {**_theme(page), "html_flipped_after_s": t_html2}
        log(f"  after second click: {rec['after_second_click']}")
        dark_glyph, light_glyph = "☀️", "🌙"
        rec["verdicts"] = {
            "C2_1_01": rec["after_click"]["html_dark"] is not rec["initial"]["html_dark"] and rec["after_click"]["glyph"] != rec["initial"]["glyph"],
            "C2_1_02_theme_persists": rec["after_reload"]["html_dark"] == rec["after_click"]["html_dark"],
            "SYNCED": (rec["after_reload"]["html_dark"] and rec["after_reload"]["glyph"] == dark_glyph) or ((not rec["after_reload"]["html_dark"]) and rec["after_reload"]["glyph"] == light_glyph),
            "STALE": rec["after_reload"]["html_dark"] and rec["after_reload"]["glyph"] == light_glyph,
            "second_click_flips_back": rec["after_second_click"]["html_dark"] == rec["initial"]["html_dark"],
        }
        rec["console"] = cap["console"][:30]
        log(f"  f001 verdicts: {json.dumps(rec['verdicts'])}")
    finally:
        record("f001", **rec)
        ctx.close()


def step_m03(browser, args) -> None:
    log("STEP m03 -- M-METRICS-03: metrics-panel-phase-duration (observation on a demo leg; scored on a cascor-backed leg)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving()}
    try:
        goto(page)
        _c, st = http("GET", "/api/status")
        rec["status"] = st if isinstance(st, dict) else {"raw": st}
        samples = []
        t0 = time.time()
        while time.time() - t0 < args.m03_seconds:
            samples.append({"t_s": round(time.time() - t0, 1), "phase_duration": text_of(page, "metrics-panel-phase-duration"), "status_pill": text_of(page, "metrics-panel-status")})
            page.wait_for_timeout(5000)
        rec["samples"] = samples
        _c, st2 = http("GET", "/api/status")
        rec["status_after"] = st2 if isinstance(st2, dict) else {"raw": st2}
        shot(page, "m03_metrics.png")
        log(f"  phase-duration samples: {[s['phase_duration'] for s in samples]}")
    finally:
        record("m03", **rec)
        ctx.close()


def step_f032(browser, args) -> None:
    log("STEP f032 -- M-WORKERS-02, cascor-down arm: Workers tab open; the 'Worker data degraded' alert (F-CANOPY-032)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving()}
    try:
        rec["api_list_before"] = http("GET", "/api/v1/workers/list", timeout=20)
        rec["api_stats_before"] = http("GET", "/api/v1/workers/stats", timeout=20)
        rec["stream_health_before"] = next((r for r in (http("GET", p, timeout=10) for p in ("/api/stream_health", "/api/v1/stream_health", "/api/health/streams")) if r[0] == 200), None)
        rec["cascor_health_before"] = _http_abs(CASCOR + "/v1/health", timeout=5)
        log(f"  stream_health -> {json.dumps(rec['stream_health_before'])[:300]} ; cascor -> {rec['cascor_health_before'][0]}")
        log(f"  /api/v1/workers/list -> {rec['api_list_before']}")
        log(f"  /api/v1/workers/stats -> {rec['api_stats_before']}")
        goto(page)
        ok = open_tab(page, "Workers", 3000)
        rec["tab_opened"] = ok
        samples = []
        t0 = time.time()
        while time.time() - t0 < args.workers_seconds:
            samples.append({"t_s": round(time.time() - t0, 1), "error_display": vis(page, "worker-panel-error-display"), "badge": text_of(page, "worker-panel-status-badge"), "total": text_of(page, "worker-panel-total"), "list": (text_of(page, "worker-panel-worker-list") or "")[:120]})
            page.wait_for_timeout(2000)
        rec["samples"] = samples
        shot(page, "f032_workers.png")
        rec["api_list_after"] = http("GET", "/api/v1/workers/list", timeout=20)
        store_payloads = []
        for r in cap["responses"]:
            if NE_STORE in r["body"]:
                try:
                    body = json.loads(r["body"])
                    data = (((body.get("response") or {}).get(NE_STORE) or {}).get("data")) if isinstance(body, dict) else None
                except ValueError:
                    data = None
                store_payloads.append({"t_ms": r["t_ms"], "status": r["status"], "store_data": data, "raw_head": r["body"][:400] if data is None else None})
        rec["store_payloads"] = store_payloads[:20]
        rendered = [s for s in samples if (s["error_display"].get("text") or "").startswith("Worker data degraded")]
        filled = [p for p in store_payloads if isinstance(p.get("store_data"), dict) and p["store_data"].get("error")]
        rec["verdicts"] = {
            "RENDERED": bool(rendered),
            "rendered_first_t_s": rendered[0]["t_s"] if rendered else None,
            "alert_text": rendered[0]["error_display"].get("text") if rendered else None,
            "STORE": "FILLED" if filled else ("EMPTY" if store_payloads else "UNSEEN"),
            "store_error_seen": (filled[0]["store_data"].get("error") if filled else None),
            "badges_seen": sorted({s["badge"] for s in samples if s["badge"] is not None}),
            "api_list_error_key": (rec["api_list_before"][1] or {}).get("error") if isinstance(rec["api_list_before"][1], dict) else None,
            "api_list_http": rec["api_list_before"][0],
        }
        rec["console"] = cap["console"][:40]
        log(f"  f032 verdicts: {json.dumps(rec['verdicts'])}")
    finally:
        record(f"f032{args.f032_arm}", **rec)
        ctx.close()


# ----------------------------------------------------------------------------- service leg: the Network Editor rows
NE = "network-editor-panel"
CASCOR = ""  # --cascor: the writable cascor behind the service leg, read directly for the effect of every edit


def cascor_get(path: str):
    code, payload = _http_abs(CASCOR + path)
    if code == 200 and isinstance(payload, dict):
        return payload.get("data", payload)
    return {"_http": code, "_body": payload}


def _http_abs(url: str, timeout: float = 20.0):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 -- loopback test leg
            raw = r.read().decode() or "null"
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"[:300]


def set_native_value(page, el_id: str, value: str) -> bool:
    """React-safe fill for <input>/<textarea> (the arc's native value-setter idiom)."""
    return bool(
        page.evaluate(
            """([id, v]) => { const el = document.getElementById(id); if (!el) return false;
                 const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                 const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                 setter.call(el, v);
                 el.dispatchEvent(new Event('input', {bubbles:true}));
                 el.dispatchEvent(new Event('change', {bubbles:true}));
                 return true; }""",
            [el_id, value],
        )
    )


def select_native(page, el_id: str, value=None, index=None):
    """Set a native <select> (dbc.Select) by value or index; returns {value, n, options}."""
    return page.evaluate(
        """([id, v, i]) => { const el = document.getElementById(id); if (!el) return null;
             if (v !== null) el.value = v; else if (i !== null) el.selectedIndex = i;
             el.dispatchEvent(new Event('change', {bubbles:true}));
             el.dispatchEvent(new Event('input', {bubbles:true}));
             return {value: el.value, n: el.options.length, options: [...el.options].map(o => o.value).slice(0, 40)}; }""",
        [el_id, value, index],
    )


def topo_dims() -> dict:
    t = cascor_get("/v1/network/topology")
    hid = t.get("hidden_units") or []
    return {"I": t.get("input_size"), "H": len(hid) if isinstance(hid, list) else hid, "O": t.get("output_size"), "output_weights": t.get("output_weights"), "output_bias": t.get("output_bias"), "hidden_units": hid}


def _close(a, b, tol=1e-6) -> bool:
    try:
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b, strict=True))
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def submit_and_wait(page, submit_id: str, budget_s: float):
    """Click a submit button and poll the panel's status block until its text changes; (seconds, text)."""
    prev = text_of(page, f"{NE}-status") or ""
    # clear the stale text first so an identical message still reads as a transition
    page.evaluate("""(id) => { const el = document.getElementById(id); if (el) el.setAttribute('data-prev', el.innerText); }""", f"{NE}-status")
    js_click(page, submit_id)
    t0 = time.time()
    cur = prev
    while time.time() - t0 < budget_s:
        cur = text_of(page, f"{NE}-status") or ""
        if cur and cur != prev:
            return round(time.time() - t0, 1), cur
        page.wait_for_timeout(300)
    return None, cur


def open_editor(page, budget_s: float) -> dict:
    open_tab(page, "Network Editor", 2000)
    t_active, _ = wait_for(page, lambda p: p.evaluate("""(id) => { const a = document.getElementById(id); return !!a && getComputedStyle(a).display !== 'none'; }""", f"{NE}-active"), budget_s)
    t_topo, _ = wait_for(page, lambda p: (p.evaluate("""(id) => { const r = document.getElementById(id); return !!r && r.innerText.trim() && !r.innerText.includes('No topology'); }""", f"{NE}-topology-readout")), budget_s)
    return {"active_after_s": t_active, "readout_after_s": t_topo, "badge": text_of(page, f"{NE}-idle-fsm-badge"), "readout": (text_of(page, f"{NE}-topology-readout") or "")[:300], "idle": vis(page, f"{NE}-idle"), "active": vis(page, f"{NE}-active")}


def step_f012(browser, args) -> None:
    log("STEP f012 -- M-NETWORK-EDITOR-17: Patch Weights, all four targets; output_weights in the manual's three forms, as rows, and wrong-count (F-CANOPY-012)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving(), "cascor": CASCOR, "cascor_health": cascor_get("/v1/health")}
    try:
        budget = args.poll_seconds
        goto(page)
        rec["editor"] = open_editor(page, budget)
        log(f"  editor: {json.dumps({k: v for k, v in rec['editor'].items() if k not in ('idle', 'active')})}")
        dims = topo_dims()
        I, H, O = dims["I"], dims["H"], dims["O"]
        rec["dims"] = {"I": I, "H": H, "O": O}
        rows_n = I + H
        n_vals = rows_n * O
        log(f"  cascor topology I={I} H={H} O={O}: output_weights is ({rows_n}, {O}) = {n_vals} values")
        sel = select_native(page, f"{NE}-patch-target", value="output_weights")
        rec["patch_target_options"] = sel
        cases = []

        def vals(prefix: float, n: int) -> list:
            return [round(prefix + 0.001 * (k + 1), 4) for k in range(n)]

        def run_case(name: str, target: str, text: str, idx=None, expect: str = "", check=None):
            select_native(page, f"{NE}-patch-target", value=target)
            page.wait_for_timeout(300)
            if idx is not None:
                set_native_value(page, f"{NE}-patch-idx", str(idx))
                page.wait_for_timeout(300)
            set_native_value(page, f"{NE}-patch-values", text)
            page.wait_for_timeout(500)
            t_s, status = submit_and_wait(page, f"{NE}-patch-submit", budget)
            page.wait_for_timeout(1000)
            after = topo_dims()
            landed = check(after) if check else None
            c = {"name": name, "target": target, "idx": idx, "text": text.replace("\n", "\\n"), "expect": expect, "status_after_s": t_s, "status": status[:400], "landed_in_cascor": landed, "output_weights_after": after["output_weights"], "output_bias_after": after["output_bias"], "hidden_units_after": after["hidden_units"]}
            cases.append(c)
            log(f"  [{name}] {target} idx={idx} -> {status[:160]!r} after {t_s}s; landed={landed}")
            shot(page, f"f012_{name}.png")
            return c

        # A: the manual's comma-separated floats, flat, the right count -> reshaped by the fix
        a = vals(0.10, n_vals)
        run_case("A_comma_flat", "output_weights", ", ".join(str(x) for x in a), expect="PATCHED", check=lambda t, a=a: _close([x for r in (t["output_weights"] or []) for x in r], a))
        # B: the manual's semicolon-separated floats, flat -> by source one row per value (width 1 != O)
        b = vals(0.20, n_vals)
        run_case("B_semicolon_flat", "output_weights", "; ".join(str(x) for x in b), expect="REJECTED by source (rows of width 1)", check=lambda t, b=b: _close([x for r in (t["output_weights"] or []) for x in r], b))
        # C: the manual's newline-separated floats, flat -> same as B
        c = vals(0.30, n_vals)
        run_case("C_newline_flat", "output_weights", "\n".join(str(x) for x in c), expect="REJECTED by source (rows of width 1)", check=lambda t, c=c: _close([x for r in (t["output_weights"] or []) for x in r], c))
        # D: rows, one line per input/hidden unit, one value per output
        d = vals(0.40, n_vals)
        d_rows = [d[i * O : (i + 1) * O] for i in range(rows_n)]
        run_case("D_rows_newline", "output_weights", "\n".join(", ".join(str(x) for x in r) for r in d_rows), expect="PATCHED", check=lambda t, d=d: _close([x for r in (t["output_weights"] or []) for x in r], d))
        # E: rows separated by semicolons
        e = vals(0.50, n_vals)
        e_rows = [e[i * O : (i + 1) * O] for i in range(rows_n)]
        run_case("E_rows_semicolon", "output_weights", "; ".join(", ".join(str(x) for x in r) for r in e_rows), expect="PATCHED", check=lambda t, e=e: _close([x for r in (t["output_weights"] or []) for x in r], e))
        # F: wrong count, flat -> the fix's own message, nothing on the wire
        f = vals(0.60, n_vals - 1)
        run_case("F_wrong_count_flat", "output_weights", ", ".join(str(x) for x in f), expect="REJECTED by the panel (count)", check=lambda t, f=f: _close([x for r in (t["output_weights"] or []) for x in r], f))
        # the other three targets
        g = vals(0.70, O)
        run_case("G_output_bias", "output_bias", ", ".join(str(x) for x in g), expect="PATCHED", check=lambda t, g=g: _close(t["output_bias"], g))
        if H >= 1:
            hu0 = dims["hidden_units"][0] if isinstance(dims["hidden_units"], list) and dims["hidden_units"] else {}
            n_w = len(hu0.get("weights") or []) or I
            h = vals(0.80, n_w)
            run_case("H_hidden_unit_weights_0", "hidden_unit_weights", ", ".join(str(x) for x in h), idx=0, expect="PATCHED", check=lambda t, h=h: _close(((t["hidden_units"] or [{}])[0] or {}).get("weights"), h))
            run_case("I_hidden_unit_bias_0", "hidden_unit_bias", "0.9", idx=0, expect="PATCHED", check=lambda t: _close(((t["hidden_units"] or [{}])[0] or {}).get("bias"), 0.9))
        rec["cases"] = cases
        ok = {c["name"]: c for c in cases}
        rec["verdicts"] = {
            "A_comma_flat_patched": bool(ok.get("A_comma_flat", {}).get("landed_in_cascor")),
            "D_rows_patched": bool(ok.get("D_rows_newline", {}).get("landed_in_cascor")),
            "E_rows_semicolon_patched": bool(ok.get("E_rows_semicolon", {}).get("landed_in_cascor")),
            "B_semicolon_flat_rejected": not ok.get("B_semicolon_flat", {}).get("landed_in_cascor"),
            "C_newline_flat_rejected": not ok.get("C_newline_flat", {}).get("landed_in_cascor"),
            "F_wrong_count_message": ok.get("F_wrong_count_flat", {}).get("status", ""),
            "G_output_bias_patched": bool(ok.get("G_output_bias", {}).get("landed_in_cascor")),
            "H_hidden_unit_weights_patched": bool(ok.get("H_hidden_unit_weights_0", {}).get("landed_in_cascor")),
            "I_hidden_unit_bias_patched": bool(ok.get("I_hidden_unit_bias_0", {}).get("landed_in_cascor")),
            "targets_patched": sum(1 for n in ("A_comma_flat", "G_output_bias", "H_hidden_unit_weights_0", "I_hidden_unit_bias_0") if ok.get(n, {}).get("landed_in_cascor")),
        }
        rec["console"] = cap["console"][:30]
        log(f"  f012 verdicts: {json.dumps(rec['verdicts'])}")
    finally:
        record("f012", **rec)
        ctx.close()


def _snap_count():
    s = cascor_get("/v1/snapshots")
    if isinstance(s, list):
        return len(s)
    if isinstance(s, dict):
        return s.get("total", len(s.get("snapshots", []) or []))
    return None


APPEND_RE = re.compile(r"Appended unit at index (\S+) \(now (\S+) hidden units\)")
REMOVE_RE = re.compile(r"Removed unit (\S+) \(now (\S+) hidden units\)")


def step_f013(browser, args) -> None:
    log("STEP f013 -- M-NETWORK-EDITOR-09 and -13: the status alert's index and count on a successful append and remove (F-CANOPY-013)")
    cap: dict = {}
    ctx, page = new_page(browser, cap)
    rec: dict = {"serving": serving(), "cascor": CASCOR}
    try:
        budget = args.poll_seconds
        goto(page)
        rec["editor"] = open_editor(page, budget)
        dims = topo_dims()
        I, H = dims["I"], dims["H"]
        rec["dims_before"] = {"I": I, "H": H, "O": dims["O"]}
        rec["snapshots_total_before"] = _snap_count()
        # M-09 append
        w = [round(0.1 * (k + 1), 3) for k in range(I + H)]
        set_native_value(page, f"{NE}-add-weights", ", ".join(str(x) for x in w))
        set_native_value(page, f"{NE}-add-bias", "0.05")
        page.wait_for_timeout(500)
        t_add, st_add = submit_and_wait(page, f"{NE}-add-submit", budget)
        page.wait_for_timeout(1000)
        after_add = topo_dims()
        m = APPEND_RE.search(st_add or "")
        rec["append"] = {"weights": w, "status_after_s": t_add, "status": (st_add or "")[:300], "index_reported": m.group(1) if m else None, "count_reported": m.group(2) if m else None, "hidden_after_in_cascor": after_add["H"], "new_unit": (after_add["hidden_units"] or [None])[-1]}
        log(f"  M-09 append: {st_add[:200]!r} after {t_add}s; cascor hidden {H} -> {after_add['H']}")
        shot(page, "f013_append.png")
        # M-13 remove: the dropdown fills from the panel's 2 s topology poll
        t_opt, opts = wait_for(page, lambda p: (lambda s: s if s and s.get("n", 0) > H and any(o != "" for o in s.get("options", [])) else None)(p.evaluate("""(id) => { const el = document.getElementById(id); return el ? {n: el.options.length, options: [...el.options].map(o => o.value)} : null; }""", f"{NE}-remove-idx")), budget)
        rec["remove_options"] = {"after_s": t_opt, "options": opts}
        last_opt = [o for o in (opts or {}).get("options", []) if o != ""][-1] if opts else None
        if last_opt is None:
            rec["remove"] = {"blocked": "remove dropdown never listed the new unit"}
        else:
            select_native(page, f"{NE}-remove-idx", value=last_opt)
            page.wait_for_timeout(400)
            js_click(page, f"{NE}-remove-submit")
            t_modal, _ = wait_for(page, lambda p: p.evaluate("""() => [...document.querySelectorAll('[role=dialog]')].filter(x => (x.className||'').includes('show')).length"""), budget)
            body = text_of(page, f"{NE}-remove-modal-body")
            snap_first = page.evaluate("""(id) => { const el = document.getElementById(id); return el ? el.checked : null; }""", f"{NE}-remove-snapshot-first")
            t_rm, st_rm = submit_and_wait(page, f"{NE}-remove-confirm", budget)
            page.wait_for_timeout(1000)
            after_rm = topo_dims()
            m2 = REMOVE_RE.search(st_rm or "")
            rec["remove"] = {"idx": last_opt, "modal_after_s": t_modal, "modal_body": (body or "")[:200], "snapshot_first_checked": snap_first, "status_after_s": t_rm, "status": (st_rm or "")[:300], "index_reported": m2.group(1) if m2 else None, "count_reported": m2.group(2) if m2 else None, "hidden_after_in_cascor": after_rm["H"], "snapshots_total_after": _snap_count()}
            log(f"  M-13 remove idx={last_opt}: modal={body!r} snapshot_first={snap_first} -> {st_rm[:200]!r} after {t_rm}s; cascor hidden {after_add['H']} -> {after_rm['H']}")
            shot(page, "f013_remove.png")
        ap = rec["append"]
        rm = rec.get("remove", {})
        h_after_add = ap["hidden_after_in_cascor"]
        rec["verdicts"] = {
            "M09_appended_in_cascor": h_after_add == H + 1,
            "M09_message_index": ap["index_reported"],
            "M09_message_count": ap["count_reported"],
            "M09_message_true": ap["index_reported"] == str(H) and ap["count_reported"] == str(H + 1),
            "M09_message_none": "None" in (ap["status"] or ""),
            "M13_removed_in_cascor": rm.get("hidden_after_in_cascor") == h_after_add - 1 if rm else None,
            "M13_message_index": rm.get("index_reported"),
            "M13_message_count": rm.get("count_reported"),
            "M13_message_true": rm.get("index_reported") == str(rm.get("idx")) and rm.get("count_reported") == str(h_after_add - 1) if rm else None,
            "M13_message_none": "None" in (rm.get("status") or "") if rm else None,
            "M13_snapshot_first_sequence": {"checkbox": rm.get("snapshot_first_checked"), "snapshots_before": rec["snapshots_total_before"], "snapshots_after": rm.get("snapshots_total_after"), "status_says_snapshot_taken": "Snapshot taken" in (rm.get("status") or "")} if rm else None,
        }
        rec["console"] = cap["console"][:30]
        log(f"  f013 verdicts: {json.dumps(rec['verdicts'])}")
    finally:
        record("f013", **rec)
        ctx.close()


STEPS = {"f018": step_f018, "f028": step_f028, "f001": step_f001, "m03": step_m03, "f032": step_f032, "f012": step_f012, "f013": step_f013}


def main() -> int:
    global OUT_PATH, SHOT_DIR, BASE  # noqa: PLW0603
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="the leg, e.g. http://127.0.0.1:8058")
    ap.add_argument("--step", required=True, help="comma-separated: " + ", ".join(STEPS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--shots", default=None, help="screenshot dir (default: <out dir>/shots)")
    ap.add_argument("--settle-seconds", type=float, default=15.0)
    ap.add_argument("--workers-seconds", type=float, default=60.0)
    ap.add_argument("--m03-seconds", type=float, default=30.0)
    ap.add_argument("--pin-keys", default="learning_rate,max_iterations")
    ap.add_argument("--f028-arms", default="settled,early", help="comma-separated arms for f028: settled (pin after the mount settle), early (pin as soon as the checkbox renders), mid (run 1's ~10 s timing)")
    ap.add_argument("--f028-repeat", type=int, default=1, help="drive each f028 arm this many times (labels arm#n)")
    ap.add_argument("--local-bootstrap", default="", help="serve this local Bootstrap 5 CSS to the page in place of the CDN (see _route_cdn)")
    ap.add_argument("--mount-seconds", type=float, default=25.0, help="settle after each page load before the first interaction (see MOUNT_MS)")
    ap.add_argument("--poll-seconds", type=float, default=30.0, help="budget when polling for a transition (an interaction's render lands in 1-16 s under F-CANOPY-004's contract)")
    ap.add_argument("--cascor", default="http://127.0.0.1:8222", help="the writable cascor behind a service leg (f012, f013 read its topology for the effect of every edit)")
    ap.add_argument("--f032-arm", default="", help="suffix for the f032 record: '' (cascor down) or '_degraded' (cascor up with a bogus WS origin)")
    args = ap.parse_args()
    BASE = args.base.rstrip("/")
    global LOCAL_CSS, MOUNT_MS, CASCOR  # noqa: PLW0603
    LOCAL_CSS = args.local_bootstrap
    MOUNT_MS = int(args.mount_seconds * 1000)
    CASCOR = args.cascor.rstrip("/")
    OUT_PATH = args.out
    SHOT_DIR = args.shots or os.path.join(os.path.dirname(os.path.abspath(OUT_PATH)), "shots")
    wanted = [s.strip() for s in args.step.split(",") if s.strip()]
    bad = [s for s in wanted if s not in STEPS]
    if bad:
        print(f"unknown step(s): {bad}", file=sys.stderr)
        return 2
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH, encoding="utf-8") as fh:
                RESULTS.update(json.load(fh))
        except (OSError, ValueError):
            # A missing, partial or corrupt prior record only means this run starts fresh: there is
            # nothing to merge and nothing to raise. The verdicts a run writes are its own.
            pass
    RESULTS["_run"] = {"base": BASE, "steps": wanted, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "serving": serving(), "host": os.uname().nodename, "external_css": (f"fulfilled from {LOCAL_CSS}" if LOCAL_CSS else "aborted (cdn.jsdelivr.net unreachable from Chrome on this host)")}
    log(f"leg {BASE} serving {json.dumps(RESULTS['_run']['serving'])}")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = launch(pw)
        try:
            for s in wanted:
                STEPS[s](browser, args)
        finally:
            browser.close()
    record("_run", finished=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log(f"results -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
