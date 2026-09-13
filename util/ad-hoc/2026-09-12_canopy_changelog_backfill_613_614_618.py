#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release train -- juniper-canopy v0.8.0
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Backfill canopy#613 / #614 / #618 into juniper-canopy's CHANGELOG ``[0.8.0]``.

All three merged BEFORE the release-bump PR (canopy#620, ``4006e74``) and are in the
v0.8.0 tree -- ``git log v0.7.0..HEAD`` lists ``b792256``, ``5c87f98``, ``ced1dd8`` --
but none of them touched CHANGELOG.md, so the ``[0.8.0]`` section documents the dataset
/ selection arc and says nothing about the three poll fixes.

That matters because the release-train ceremony renders the published Release body and
the archived notes file from exactly that section
(``ceremony.changelog_version_section``, :417). Cutting v0.8.0 as it stands would
publish notes that omit the largest behavioural fixes in the release -- and a Release
body is not re-cuttable.

Writes the amended file to ``--out``; never touches the shared canopy checkout, which
other sessions may be using. Land it with ``util/open_signed_pr.py``.
"""

import argparse
import sys
from pathlib import Path

BULLETS = '''- **The metrics store never advanced past its shipped empty default, so the main metrics plot, the
  candidate loss plot and every replay index control rendered their "no data" placeholder through
  entire live runs (F-CANOPY-035).** The writer was not broken. Measured on a live leg with a cascor
  fixture at 52 units and 66 metrics rows: **55 responses in 90 s, every one HTTP 200 carrying the
  full 66-row payload, store length 0 throughout** — and the store filled within ~3 s of the trigger
  being stopped, in two independent runs.

  **The cause is in dash-renderer, not in canopy's wiring.** Read from the unminified bundle that
  ships in `JuniperCanopy1` (`dash_renderer.dev.js`, dash 4.2.0): a deferred callback enters
  `watched` when its fetch is initiated (`:2676`), and on resolution it must **still** be there
  (`:2698`) or the observer returns and the result is discarded; `:3027` concatenates `requested`
  **last** when computing the duplicate set, so a newly requested invocation **evicts** the in-flight
  one. `getUniqueIdentifier` (`:1715`) hashes one callback's **own** inputs, outputs and state, so
  only this callback's own re-request can evict it — never a sibling on the same lane. Riding
  `fast-update-interval`, `update_metrics_store`'s ~1.5 s round trip was re-requested every 1.0 s, so
  every response was evicted before it could be applied. Same family as F-CANOPY-039, different
  failure point: F-039's lifecycle completes and dies at `RemoveExecuting`; this one never reaches a
  terminal list at all.

  **The fix is at the trigger, in two halves that are each insufficient alone.**
  `update_metrics_store` gets its own `dcc.Interval` (`metrics-store-interval`, period
  `METRICS_STORE_POLL_INTERVAL_MS`), because a guard on the *shared* lane would instead have silenced
  the other nine fast-lane callbacks for ~60% of every second; and
  `running=[(Output("metrics-store-interval", "disabled"), True, False)]` stops that clock for exactly
  the duration of each fetch, because a dedicated lane alone would still re-request over itself
  whenever the round trip exceeds the period. `running=` sits next to three parameters documented as
  background-only and does **not** carry that restriction — `dash/_callback.py` passes it through with
  no `background` gate. The new interval is registered in the gated-interval set, so the CAN-000 apply
  clamp still silences it exactly as before.

  **The measured cost, stated rather than buried.** The effective cadence goes from a nominal 1 Hz
  *delivering nothing* to ~5.5–7.3 s *delivering*. `FAST_UPDATE_INTERVAL_MS` is deliberately
  untouched: `network_visualizer.py` derives the cascade-add glow timing from it. During live training
  the WS append path owns the store at full speed and this poll short-circuits on `ws_live` without
  fetching, so the slower cadence applies only to the stale-stream backstop. (#613)

- **That `running=` guard never released on a network failure, stranding the metrics poll for the life
  of the page.** The renderer restores a `running=` guard from `completeJob()`
  (`dash_renderer.dev.js:925-932`), which runs on every HTTP *outcome* — 200, non-OK, prevent-update —
  but a request that never produces a response at all lands in `handleError` (`:987-998`), which
  dispatches `updateResourceUsage` and rejects **without** calling it. A canopy restart, a connection
  reset or a browser offline moment therefore left `disabled = true` with nothing to clear it: the
  metrics store stopped updating until a tab change or an apply-clamp release happened to re-enable
  it. (#613 asserted this could not happen, citing `:1038`/`:1113` — real error-path dispatches, but
  inside `_handleWebsocketCallback`, a transport this callback never takes.)

  Repaired with a clientside watchdog on the **existing** slow lane — no new poller, per the
  F-CANOPY-027 rule — which re-enables the interval once it has been continuously disabled for
  `METRICS_STORE_STRAND_TIMEOUT_MS` (30 s, ten times the worst round trip ever measured on this
  callback). It bounds the outage rather than making recovery fast, because fast recovery would
  reopen the eviction window above. It short-circuits while `apply-in-flight` is set and resets its
  timer then, so the CAN-000 apply clamp — which legitimately holds this interval disabled for a
  whole apply — is not defeated. `metrics-store-interval.disabled` consequently carries two
  registered writers, and that exception is pinned in the poll-gating tests rather than left to a
  commit message.

  Also corrected here: `FULL_HISTORY_POLL_TICK_MODULUS`'s comment still described "one full fetch per
  ~5 s at the 1 s fast interval", but #613 changed the tick it counts. `n` is now
  `metrics-store-interval.n_intervals`, which advances once per *completed round trip*, so
  full-history refetch went from ~5 s to **~27–37 s**. The constant is left at 5 deliberately: a full
  fetch is up to 10k rows, which lengthens the round trip, which lengthens the self-clocked period, so
  the two constants interact and no full-mode round trip has been measured. Documented rather than
  re-tuned blind. (#614)

- **The Candidate Training Loss plot rendered on roughly a third of page loads — the same eviction,
  one callback downstream (F-CANOPY-052, re-disposed as F-CANOPY-035's own mechanism).** The rest of
  the time it showed zero traces **and** zero annotations: not the
  `create_empty_plot("No candidate data available")` placeholder but the `dcc.Graph` mount default,
  a state neither of `update_loss_plot`'s two return paths can produce — so the callback's output was
  never reaching the component at all.

  `update_loss_plot` took `{component_id}-training-state-store` as an **Input**.
  `fetch_training_state` writes that store off the panel's own 1000 ms interval and returns
  unconditionally on both branches while the candidates tab is active, and `/api/state` carries a
  per-call `timestamp` — two consecutive GETs differ in exactly that key — so the written value is
  genuinely different every tick and the no-op-write suppression that protects other stores cannot
  bite. One `getUniqueIdentifier`, re-requested at ~1 Hz, evicted at `:3027` and discarded at
  `:2698`: #613's mechanism on the next callback. Its headline argument is what obscured this —
  "`getUniqueIdentifier` hashes one callback's own inputs/outputs/state, so siblings cannot evict it"
  is true, and the corollary that *the same callback re-triggered by its own other Input is the same
  identity* was never run on the neighbour.

  Fixed by demoting the Input to State — the trigger, not the work; the F-CANOPY-039 precedent, whose
  topology rebuild went 0/11 → 11/11 on exactly this change. A server-side guard would not help: by
  the time a handler can return `no_update`, the round trip has happened and the eviction is already
  booked. Nothing is lost by the demotion — `state` feeds only the fallback branch, which exists for a
  backend that supplies `epochs`/`losses`/`phases`, and F-CANOPY-035 established that `/api/state`
  never carries those keys in any lane. Measured with one variable (`setProps` on the panel interval's
  `disabled` and nothing else): **1 of 3 renders with the tick running, 3 of 3 with it stopped**, with
  zero loss-plot responses on the wire on every non-render against 79–88 naming other outputs in the
  same windows. (#618)
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--changelog", required=True, help="source CHANGELOG.md (read-only)")
    ap.add_argument("--out", required=True, help="where to write the amended file")
    ap.add_argument("--version", default="0.8.0")
    args = ap.parse_args()

    text = Path(args.changelog).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Locate the [<version>] section and its ``### Fixed`` heading, refusing anything
    # ambiguous: a silently mis-placed bullet would ship in the Release body.
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"## [{args.version}]")), None)
    if start is None:
        print(f"no '## [{args.version}]' heading in {args.changelog}", file=sys.stderr)
        return 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    fixed = next((i for i in range(start, end) if lines[i].strip() == "### Fixed"), None)
    if fixed is None:
        print(f"no '### Fixed' heading inside [{args.version}]", file=sys.stderr)
        return 2

    section = "".join(lines[start:end])
    for pr in ("(#613)", "(#614)", "(#618)"):
        if pr in section:
            print(f"{pr} already present in [{args.version}] -- refusing to duplicate", file=sys.stderr)
            return 1

    at = fixed + 1
    while at < end and lines[at].strip() == "":
        at += 1
    out = lines[:at] + [BULLETS, "\n"] + lines[at:]
    Path(args.out).write_text("".join(out), encoding="utf-8")
    print(f"inserted 3 bullets before line {at + 1} of {args.changelog} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
