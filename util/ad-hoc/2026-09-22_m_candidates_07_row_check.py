#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""M-CANDIDATES-07 -- the matrix row's OWN script, on a leg serving canopy#618 and later.

The row (``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md``) reads
"passive | Theme-aware candidate loss figure". The 2026-09-11 re-drive of F-CANOPY-052's fix
measured only whether the figure rendered, and left the row FAIL with "run the matrix's own
script". The script has two halves:

  RENDER   with the Candidate Metrics tab active and candidate rows in the metrics store,
           ``candidate-metrics-panel-loss-plot`` carries a trace with > 0 points, within
           F-CANOPY-004's fresh-session contract (<= 40 s after the tab opens).
  THEME    clicking ``#dark-mode-toggle`` re-renders that figure with a different
           ``paper_bgcolor`` or ``template``, within the interaction contract (<= 16 s).
           The toggle is clicked a second time afterwards to restore the theme, and that
           is checked too, since ``dark-mode-store`` is ``storage_type="local"`` and would
           otherwise leak into the next page (the arc's localStorage trap).

Each run uses a fresh browser, so one page's localStorage cannot reach another run.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.
  PASS       every run: RENDER within 40 s, and THEME changed within 16 s and restored.
  FAIL       any run: no rendered trace at 40 s, or the theme did not change within 16 s.
  BLOCKED    the metrics store holds no candidate rows (nothing to plot); says nothing.

Usage:
    JUNIPER_E2E_BROWSER_GPU=1 JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8051 LIBTORCH= LD_LIBRARY_PATH= \\
      /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-09-22_m_candidates_07_row_check.py --runs 3 \\
      --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_m_candidates_07_row_check.json
"""

import argparse
import importlib.util
import json
import sys
import time
import urllib.request
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
FIG = "candidate-metrics-panel-loss-plot"

_JS_FIG = """(id) => {
  const el = document.getElementById(id); if (!el) return {present: false};
  const gd = el.querySelector('.js-plotly-plot') || el;
  const data = gd && gd.data ? gd.data : null, layout = gd && gd.layout ? gd.layout : null;
  const tpl = layout && layout.template && layout.template.layout ? layout.template.layout : null;
  return {present: true,
          traces: data ? data.map(t => ({name: t.name || null, n: (t.x && t.x.length) || 0})) : null,
          paper_bgcolor: layout ? (layout.paper_bgcolor || (tpl && tpl.paper_bgcolor) || null) : null,
          font_color: layout && layout.font ? (layout.font.color || null) : null,
          html_dark: document.documentElement.classList.contains('dark-mode')};
}"""


def _candidate_rows() -> int:
    try:
        with urllib.request.urlopen(f"{CANOPY}/api/metrics/history?limit=0", timeout=10) as r:  # noqa: S310
            d = json.loads(r.read().decode("utf-8"))
        h = d.get("history", d.get("data", d)) if isinstance(d, dict) else d
        return sum(1 for row in h if (row.get("phase") or "").lower().startswith("cand"))
    except Exception:  # noqa: BLE001
        return -1


def _wait(page, pred, budget_s: float):
    t0 = time.time()
    last = None
    while time.time() - t0 < budget_s:
        last = page.evaluate(_JS_FIG, FIG)
        if pred(last):
            return True, round(time.time() - t0, 1), last
        page.wait_for_timeout(1000)
    return False, round(time.time() - t0, 1), last


def _one(pw, diagnose: bool = False) -> dict:
    rec: dict = {}
    browser, ctx, page = _seg17.open_dashboard(pw, [])
    reqs: list = []

    def on_request(req):
        if "_dash-update-component" not in req.url:
            return
        try:
            out = str((req.post_data_json or {}).get("output") or "")
        except Exception:  # noqa: BLE001
            return
        if FIG + ".figure" in out or "theme-state.data" in out:
            reqs.append({"t": time.time(), "output": out[:160]})

    page.on("request", on_request)
    try:
        _seg17.open_tab(page, "Candidate Metrics")
        ok, t, fig = _wait(page, lambda f: any((tr.get("n") or 0) > 0 for tr in (f.get("traces") or [])), 40.0)
        rec["render"] = {"ok": ok, "t_s": t, "figure": fig}
        if not ok:
            return rec
        before = (fig.get("paper_bgcolor"), fig.get("font_color"), fig.get("html_dark"))
        page.evaluate("() => { const b = document.getElementById('dark-mode-toggle'); if (b) b.click(); return !!b; }")
        ok2, t2, fig2 = _wait(page, lambda f: (f.get("paper_bgcolor"), f.get("font_color")) != before[:2] and any((tr.get("n") or 0) > 0 for tr in (f.get("traces") or [])), 16.0)
        rec["theme"] = {"ok": ok2, "t_s": t2, "before": before, "after": (fig2.get("paper_bgcolor"), fig2.get("font_color"), fig2.get("html_dark"))}
        if diagnose and not ok2:
            # DIAGNOSTIC ONLY -- the verdict above is already fixed at the 16 s contract.
            # Where does the chain stop: theme-state never written, or written and the
            # figure's callback never dispatched?
            t_toggle = time.time() - t2
            tl = []
            t0 = time.time()
            while time.time() - t0 < 40.0:
                ts = (_seg17._store(page, "theme-state") or {}).get("value")
                f = page.evaluate(_JS_FIG, FIG)
                tl.append({"t": round(time.time() - t_toggle, 1), "theme_state": ts, "paper_bgcolor": f.get("paper_bgcolor")})
                if f.get("paper_bgcolor") not in (None, before[0]):
                    break
                page.wait_for_timeout(2000)
            rec["diagnosis"] = {"timeline": tl, "requests_since_toggle": [r["output"] for r in reqs if r["t"] >= t_toggle]}
        page.evaluate("() => { const b = document.getElementById('dark-mode-toggle'); if (b) b.click(); return !!b; }")
        ok3, t3, fig3 = _wait(page, lambda f: (f.get("paper_bgcolor"), f.get("font_color")) == before[:2], 16.0)
        rec["restore"] = {"ok": ok3, "t_s": t3, "after": (fig3.get("paper_bgcolor"), fig3.get("font_color"), fig3.get("html_dark"))}
    finally:
        browser.close()
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--diagnose", action="store_true", help="on a THEME miss, record theme-state and the figure for 40 s more (diagnostic only; the verdict is unchanged)")
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "candidate_rows": _candidate_rows(), "runs": []}
    try:
        with urllib.request.urlopen(f"{CANOPY}/v1/health", timeout=5) as r:  # noqa: S310
            h = json.loads(r.read().decode("utf-8"))
        res["serving"] = {"git_sha": h.get("git_sha"), "version": h.get("version"), "build_date": h.get("build_date")}
    except Exception as exc:  # noqa: BLE001
        res["serving"] = {"error": str(exc)[:160]}
    log(f"serving {res['serving']}  candidate rows in the history: {res['candidate_rows']}")
    if res["candidate_rows"] <= 0:
        res["verdict"] = "BLOCKED"
    else:
        with sync_playwright() as pw:
            for i in range(args.runs):
                rec = _one(pw, args.diagnose)
                rec["i"] = i
                res["runs"].append(rec)
                log(f"  run {i + 1}: render={rec.get('render', {}).get('ok')} @ {rec.get('render', {}).get('t_s')}s "
                    f"traces={(rec.get('render', {}).get('figure') or {}).get('traces')} "
                    f"theme={rec.get('theme', {}).get('ok')} @ {rec.get('theme', {}).get('t_s')}s {rec.get('theme', {}).get('before')} -> {rec.get('theme', {}).get('after')} "
                    f"restore={rec.get('restore', {}).get('ok')}")
        passed = all(r.get("render", {}).get("ok") and r.get("theme", {}).get("ok") and r.get("restore", {}).get("ok") for r in res["runs"])
        res["verdict"] = "PASS" if passed else "FAIL"
    log(f"=> M-CANDIDATES-07: {res['verdict']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
