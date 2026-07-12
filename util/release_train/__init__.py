"""Juniper PyPI release-train tooling (report-only detection engine).

This package implements Phase 1 of the ratified release-train plan
(``notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md``):

  * ``registry.yaml`` -- the single source of truth for the 18 publishable
    Juniper packages (plan Appendix B + audit S1), consumed data-driven so the
    detector hardcodes nothing (plan S4.1).
  * ``detect.py``     -- the deterministic, re-runnable per-package "does this
    package need a PyPI deploy?" detection engine (plan S4.2/S4.3). Report-only:
    it emits a release-manifest JSON + a human table and takes no action.

Later phases (propose.py / ceremony.py / release-train.yml) are out of scope for
Phase 1 and do not exist yet.

Project: juniper-ml
Sub-Project: automated PyPI release-train
Author: Paul Calnon
Created: 2026-07-11
Status: permanent utility
"""
