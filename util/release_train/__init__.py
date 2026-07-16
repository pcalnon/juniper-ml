"""Juniper PyPI release-train tooling (report-only detection engine).

This package implements Phase 1 of the ratified release-train plan
(``notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md``):

  * ``registry.yaml`` -- the single source of truth for the 18 publishable
    Juniper packages (plan Appendix B + audit S1), consumed data-driven so the
    detector hardcodes nothing (plan S4.1).
  * ``detect.py``     -- the deterministic, re-runnable per-package "does this
    package need a PyPI deploy?" detection engine (plan S4.2/S4.3). Report-only:
    it emits a release-manifest JSON + a human table and takes no action.

Phase 2.1 adds the proposal-PR generation layer (plan S5.4/S6/S10.1):

  * ``notes_render.py`` -- template-driven release-notes DRAFT generation (plan S10.1).
  * ``propose.py``      -- consumes ``detect.py``'s manifest and, for each
    ``UNRELEASED_CHANGES`` package, builds the complete standard-gated release-proposal
    PR content (version bump + CHANGELOG move + notes draft + co-changes +
    propagation edges). Dry-run by default; opens nothing.

The remaining ``ceremony.py`` (Phase 3, the exempt archive PR + Release cut) is still
out of scope and does not exist yet.

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-11
Status: permanent utility
"""
