#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Which WebGL renderer does each Playwright launch configuration actually get?

WHY. Every canopy E2E browser measurement in this arc runs headless Chromium, and the
2026-09-22 Lane A2 validation measured the page's main thread 66-75% busy in long tasks,
with fetch() -> parsed JSON taking 3.2-5.5 s against a ~30 ms network leg. If that
saturation comes from software GL (SwiftShader) rendering plotly/WebGL surfaces, the
"frozen panel" findings could be properties of the HARNESS rather than of a real user's
GPU-backed browser. This reports the unmasked renderer string per configuration, so a
re-run can be pointed at a configuration that really has the GPU.

No page from canopy is loaded; this opens about:blank and a canvas.
"""

import json
import sys

JS = """() => {
  const c = document.createElement('canvas');
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  if (!gl) return {webgl: false};
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return {webgl: true,
          vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
          renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)};
}"""

CONFIGS = {
    "default (the arc's launch)": {"headless": True, "args": ["--disable-dev-shm-usage"]},
    "headless + gpu flags": {"headless": True, "args": ["--disable-dev-shm-usage", "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=vulkan", "--enable-features=Vulkan"]},
    "headless + gl-egl": {"headless": True, "args": ["--disable-dev-shm-usage", "--enable-gpu", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=gl-egl"]},
    "new headless channel": {"headless": True, "channel": "chromium", "args": ["--disable-dev-shm-usage", "--enable-gpu", "--ignore-gpu-blocklist"]},
}


def main() -> int:
    from playwright.sync_api import sync_playwright

    out = {}
    with sync_playwright() as pw:
        for name, cfg in CONFIGS.items():
            try:
                b = pw.chromium.launch(**cfg)
                page = b.new_context().new_page()
                page.goto("about:blank")
                out[name] = page.evaluate(JS)
                b.close()
            except Exception as exc:  # noqa: BLE001
                out[name] = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            print(f"{name:32s} {json.dumps(out[name])}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
