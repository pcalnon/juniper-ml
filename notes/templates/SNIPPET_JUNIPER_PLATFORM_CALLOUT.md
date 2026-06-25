<!--
  Canonical "Part of the Juniper platform" callout for lean package READMEs.
  Style of record: notes/JUNIPER_README_STYLE_RECONCILIATION_2026-06-24.md.

  Purpose: every lean package README carries a SHORT ecosystem on-ramp instead
  of the full platform intro + Research Philosophy essay (which lives only in
  the juniper-ml root README). Copy the blockquote below into a package README's
  intro and replace <package-name> / <its one-line role>.

  Keep it to 2–3 sentences. The two fixed messages it must convey:
    1. what role this package plays in Juniper, and
    2. that you don't need the rest of the platform to use it (deps come from PyPI).
-->

> **Part of the Juniper platform.** <package-name> is <its one-line role> in
> [Juniper](https://github.com/pcalnon/juniper-ml) — a multi-package ML research platform built around
> constructive (Cascade-Correlation) and recurrent neural networks. You don't need the rest of the
> platform to use this package; its Juniper dependencies resolve from PyPI.

<!--
  Role examples (pick the register, then tailor):
    - juniper-cascor-client   → "the HTTP/WebSocket client for the juniper-cascor training service"
    - juniper-data            → "the dataset-generation REST service"
    - juniper-service-core    → "the shared FastAPI service-tier framework every model service is built on"
    - juniper-canopy          → "the real-time training-monitoring dashboard"
  For a service whose deps are heavier (e.g. torch via a worker), say so plainly
  rather than implying a trivial install.
-->
