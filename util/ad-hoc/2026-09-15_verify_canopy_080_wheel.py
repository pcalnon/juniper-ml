#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release verification -- juniper-canopy 0.8.0
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Does the PUBLISHED juniper-canopy 0.8.0 wheel actually carry the v0.8.0 fixes?

A checkout is not a deployment. juniper-model-core 0.3.1 shipped a docstring the repo had
already fixed and served it for four days under an unchanged version, so "main is correct"
and "the wheel is correct" are separate claims. This checks the second one, against the
artifact PyPI serves rather than against any local tree.

It reads the wheel's own members instead of installing it: canopy's dependency tree is
large, and a source-level fingerprint is what distinguishes a stale build from a fresh one.
Importability would not -- a stale wheel imports perfectly.

Checks, one per thing v0.8.0 claims to have shipped:

  * the three version sites agree with the release (the PR-620 class: the version lives in
    four places and only one of them used to be guarded)
  * canopy#613 -- ``update_metrics_store`` rides its own guarded interval
  * canopy#614 -- the strand watchdog and its timeout constant are present
  * canopy#618 -- ``update_loss_plot``'s training-state store is State, not Input

``canopy_constants.py`` is NOT a wheel member (no canopy wheel back to 0.5.0 ships it), so the
version-fallback and constant checks report MISSING-FILE rather than FAIL. That absence is a
finding in its own right -- ``frontend/dashboard_manager.py`` opens with
``from canopy_constants import ...`` -- measured by
``util/ad-hoc/2026-09-15_canopy_wheel_import_probe.py``.

Usage:
  python util/ad-hoc/2026-09-15_verify_canopy_080_wheel.py --version 0.8.0
"""

import argparse
import io
import json
import re
import sys
import urllib.request
import zipfile

PYPI = "https://pypi.org/pypi/{pkg}/{ver}/json"


def fetch_wheel(pkg: str, ver: str) -> "tuple[str, bytes]":
    """Return (filename, bytes) for the version's wheel, read from the VERSION-specific
    endpoint -- the aggregate ``/pypi/<pkg>/json`` lags behind a fresh publish via Fastly."""
    with urllib.request.urlopen(PYPI.format(pkg=pkg, ver=ver), timeout=60) as r:  # noqa: S310
        meta = json.load(r)
    urls = [u for u in meta["urls"] if u["packagetype"] == "bdist_wheel"]
    if not urls:
        raise SystemExit(f"{pkg} {ver}: no wheel on PyPI (urls: {[u['packagetype'] for u in meta['urls']]})")
    u = urls[0]
    with urllib.request.urlopen(u["url"], timeout=180) as r:  # noqa: S310
        return u["filename"], r.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", default="juniper-canopy")
    ap.add_argument("--version", default="0.8.0")
    args = ap.parse_args()

    name, blob = fetch_wheel(args.package, args.version)
    zf = zipfile.ZipFile(io.BytesIO(blob))
    members = zf.namelist()
    print(f"wheel: {name}  ({len(blob)} bytes, {len(members)} members)")

    def read(suffix: str) -> "str | None":
        hits = [m for m in members if m.endswith(suffix)]
        if not hits:
            return None
        return zf.read(sorted(hits, key=len)[0]).decode("utf-8", "replace")

    results: list = []

    def check(label: str, ok: "bool | None", detail: str = "") -> None:
        results.append((label, ok, detail))
        mark = "PASS" if ok else ("MISSING-FILE" if ok is None else "FAIL")
        print(f"  [{mark}] {label}" + (f" -- {detail}" if detail else ""))

    # --- version sites -------------------------------------------------------
    consts = read("canopy_constants.py")
    if consts is None:
        check("version: canopy_constants.resolve_app_version fallback", None, "canopy_constants.py not in wheel")
    else:
        m = re.search(r"def resolve_app_version\(fallback: str = \"([^\"]+)\"", consts)
        check("version: canopy_constants.resolve_app_version fallback", bool(m and m.group(1) == args.version),
              f"fallback={m.group(1) if m else 'unparsed'}")

    for init in ("juniper_canopy/__init__.py", "src/__init__.py"):
        txt = read(init)
        if txt is None:
            check(f"version: {init}", None, "not in wheel")
        else:
            m = re.search(r"__version__\s*=\s*\"([^\"]+)\"", txt)
            check(f"version: {init}", bool(m and m.group(1) == args.version),
                  f"__version__={m.group(1) if m else 'unparsed'}")

    # --- canopy#613: the guarded, dedicated metrics-store lane ---------------
    dm = read("frontend/dashboard_manager.py")
    if dm is None:
        check("canopy#613: metrics-store-interval + running= guard", None, "dashboard_manager.py not in wheel")
    else:
        has_interval = "metrics-store-interval" in dm
        has_running = bool(re.search(r"running\s*=\s*\[\s*\(\s*Output\(\s*_METRICS_STORE_INTERVAL", dm))
        check("canopy#613: dedicated metrics-store interval", has_interval)
        check("canopy#613: running= guard on that interval", has_running)

        # --- canopy#614: the strand watchdog ---------------------------------
        check("canopy#614: strand watchdog references the timeout constant",
              "METRICS_STORE_STRAND_TIMEOUT_MS" in dm)
        check("canopy#614: watchdog tracks a disabled-since timestamp",
              "__metricsStoreDisabledSince" in dm)
        # NOT checked here, deliberately: whether the threshold actually INTERPOLATED. An
        # f-string's source always contains the brace expression, so reading it from a wheel
        # cannot distinguish a live f-string from a lost prefix -- the first draft of this
        # script "failed" on exactly that and the failure was the instrument's. The real test
        # reads the registered clientside source off ``app._inline_scripts`` by function_name
        # hash, which needs a BUILT app; it lives in canopy's own test_poll_gating.py.

    if consts is not None:
        check("canopy#614: METRICS_STORE_STRAND_TIMEOUT_MS defined", "METRICS_STORE_STRAND_TIMEOUT_MS" in consts)
        check("canopy#613: METRICS_STORE_POLL_INTERVAL_MS defined", "METRICS_STORE_POLL_INTERVAL_MS" in consts)

    # --- canopy#618: the trigger demotion ------------------------------------
    panel = read("components/candidate_metrics_panel.py")
    if panel is None:
        check("canopy#618: training-state store is State, not Input", None, "candidate_metrics_panel.py not in wheel")
    else:
        # Scope to update_loss_plot's own decorator. The file legitimately contains THREE
        # other callbacks that take this store as their only Input (update_status_display,
        # update_epoch_progress, update_pool_info) -- structurally exposed to the same
        # eviction, cheap enough to survive it, recorded as a latent risk and deliberately
        # not filed. A file-scoped grep scores those and reports a fix that shipped as absent.
        # The decorator is ``@app.callback(`` in this file, not ``@self.app.callback(`` --
        # so anchor on the DEF and walk back to the nearest preceding decorator rather than
        # guessing the receiver. Guessing it produced a MISSING-FILE verdict on a file that
        # was present and correct.
        defpos = panel.find("def update_loss_plot")
        decpos = max(panel.rfind("@app.callback(", 0, defpos), panel.rfind("@self.app.callback(", 0, defpos)) if defpos > 0 else -1
        if defpos < 0 or decpos < 0:
            check("canopy#618: update_loss_plot decorator located", None,
                  f"def found={defpos >= 0}, preceding @callback found={decpos >= 0}")
        else:
            dec = panel[decpos:defpos]
            as_input = re.search(r"Input\(\s*f?\"\{?self\.component_id\}?-training-state-store\"", dec)
            as_state = re.search(r"State\(\s*f?\"\{?self\.component_id\}?-training-state-store\"", dec)
            check("canopy#618: update_loss_plot does NOT take the store as an Input", not as_input)
            check("canopy#618: update_loss_plot takes the store as State", bool(as_state))

    failed = [label for label, ok, _ in results if ok is False]
    missing = [label for label, ok, _ in results if ok is None]
    print(f"\n{len(results) - len(failed) - len(missing)} pass / {len(failed)} fail / {len(missing)} unresolved")
    if missing:
        print("UNRESOLVED (a file the wheel does not ship -- decide whether that is expected):", file=sys.stderr)
        for label in missing:
            print(f"  {label}", file=sys.stderr)
    if failed:
        print("FAILED:", file=sys.stderr)
        for label in failed:
            print(f"  {label}", file=sys.stderr)
        return 1
    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
