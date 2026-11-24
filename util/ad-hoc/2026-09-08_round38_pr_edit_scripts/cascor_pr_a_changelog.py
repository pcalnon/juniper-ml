#!/usr/bin/env python3
"""Round-38 cascor PR-A: CHANGELOG entry (session scratch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#633 (worktree juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--fix--dataset-shortfall-acceptance-source--20260908-0716--d39d537e")
CHANGELOG = W / "CHANGELOG.md"

OLD = "## [Unreleased]\n\n### Fixed\n\n- **An ingested artifact carrying NaN or Inf now fails at the boundary, by name.**\n"
NEW = (
    "## [Unreleased]\n\n### Fixed\n\n"
    "- **`dataset_shortfall` now says WHO accepted the partial dataset — and no longer denies an\n"
    "  acceptance it is annotating.** `accepted_via_allow_truncated_datasets` was the raw value of this\n"
    "  service's own setting. Two live paths made it read `false` on a run training on partial data:\n"
    "  the caller supplying `allow_truncation: true` in the staged params (the path canopy's options 1\n"
    "  and 2 use, with the service flag off), and juniper-data accepting on its **own** deployment\n"
    "  opt-in — which it ORs with the request and a client cannot refuse — while nothing was sent from\n"
    "  here. The annotation is additive: `accepted_by_this_run` (an opt-in went on the wire from this\n"
    "  side), `acceptance_source` (`request_params` | `allow_truncated_datasets` | `producer`), and the\n"
    "  original field kept with its literal meaning — true only when THIS service's setting supplied\n"
    "  the opt-in. The `summary` sentence and the training-log line carry the same clause.\n"
    "\n"
    "  Found by round-37 handoff validation in juniper-ml. The producer's descriptor carries no\n"
    "  authority field, so the source is derived from what this run **sent**, and `producer` is\n"
    "  inferred when nothing was sent and a shortfall arrived anyway. Pinned by three arms of\n"
    "  `TestShortfallIsPollable` that run `_reload_dataset` up to the annotation and stop.\n"
    "\n"
    "- **A caller's explicit `allow_truncation: false` now gets the refusal message, not a bare\n"
    '  "fetch failed".** `_describe_dataset_fetch_failure` keyed the remedy off the service **setting**;\n'
    "  with the flag on and the caller refusing (honoured since cascor#624), the producer's 422 came\n"
    "  back as `juniper-data fetch failed: …` with no remedy — in exactly the case the remedy exists\n"
    "  for. It now keys off the stance that went on the wire, and tells a caller that refused to\n"
    "  re-send `allow_truncation=true` with `incomplete_rows=accept|drop` rather than pointing them at\n"
    "  a service knob their own value overrides. The staged value is read as a tri-state\n"
    '  (`_as_bool_stance`), because the params cross a JSON boundary and `bool("false")` is `True`.\n'
    "\n"
    "- **The refusal message opens with a machine-readable token, `[dataset_shortfall_refused]`**\n"
    "  (`_PROJECT_API_SHORTFALL_REFUSAL_TOKEN`), so a consumer can recognise the class without\n"
    "  matching prose; canopy's three-way partial-data prompt keys on it. It rides inside the 409\n"
    "  `detail` because that is the one channel every transport carries — the WS control path\n"
    "  forwards `error` as a bare string. An ordinary outage does not carry it.\n"
    "\n"
    "- **Correction to the `dataset_shortfall` entry below: it does NOT ride the WS training\n"
    "  stream.** `get_status()` is read by the stream only in the one-shot `initial_status` frame at\n"
    "  connect; the broadcast set has no status frame. A client already connected when\n"
    "  `_reload_dataset` sets the field never sees it over WS — it polls `/v1/training/status`\n"
    "  (canopy does, at 1 Hz). The manager comment that made the same claim is corrected here.\n"
    "\n"
    "- **An ingested artifact carrying NaN or Inf now fails at the boundary, by name.**\n"
)

text = CHANGELOG.read_text()
if text.count(OLD) != 1:
    sys.exit(f"FAIL: CHANGELOG anchor found {text.count(OLD)} times")
CHANGELOG.write_text(text.replace(OLD, NEW))
print("CHANGELOG edited")
