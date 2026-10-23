#!/usr/bin/env python3
"""Apply canopy's F-CANOPY-069 fix to a juniper-canopy tree at main 571743db -- replayable, exact-match, idempotent.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 32 (F-CANOPY-069: dash 3.x renders canopy's dashboard inert)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 14, F-CANOPY-069; item 32);
              util/ad-hoc/2026-10-20_f069_pair_members_probe.py (which member of each pair runs, per dash);
              util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py (the per-dash ALIVE/INERT verdict);
              util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py (proves the tree is 571743db before this runs)
License:      MIT License

WHY A SCRIPT. turing has no git signing, so the change lands through the GitHub API as whole-file uploads
(util/open_signed_pr.py). A whole-file upload must be built from main's exact bytes, and a concurrent landing
can move main; keeping the edit as exact-match replacements that refuse to run against anything but the
expected text means the fix can be re-applied to a fresh copy of main in one command, and a revert costs one
re-run. Every replacement is asserted to match EXACTLY ONCE; a replacement whose new text is already present
is skipped (idempotent), and the script exits 1 on the first mismatch without writing anything.

THE FIX. Two callback pairs each claimed one ``allow_duplicate`` Output from one Input (``accept_live_switch``
+ ``open_progress_alert_on_accept`` on ``live-switch-accept-button.n_clicks``; ``execute_restart`` +
``open_restart_progress`` on ``restart-confirm-button.n_clicks``). Dash hashes the INPUTS into an
``allow_duplicate`` output id (``create_callback_id``), so the pairs' ids collided; dash 3's renderer drops the
whole callback graph on that error and dash 4 runs both members, racing their responses. The openers existed to
show a progress spinner before the slow POST returned, which is what a callback's ``running=`` spec is for: the
renderer sets the props the moment the request leaves and resets them when the response lands, with no second
callback and no round trip. So: the openers and ``_open_progress_alert_on_accept_handler`` go, the two working
callbacks gain ``running=``, the tests that drove the openers are replaced, a new test pins "no output id is
claimed by two callbacks" plus the two specs, the dash floor rises to the line everything canopy tests runs
(``dash>=4.0.0``), ``conf/conda_environment.yaml`` moves from 3.3.0 to 4.4.1 (with dash 4's two new run deps,
``comm`` and ``janus``, at the lock's versions), and CHANGELOG.md gets the entries.

Usage:
    python3 -I util/ad-hoc/2026-10-20_f069_apply_fix.py --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f069
    python3 -I util/ad-hoc/2026-10-20_f069_apply_fix.py --root <copy of main> --check   # report only, write nothing
"""

from __future__ import annotations

import argparse
import os
import sys

NEW_TEST_PATH = "src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py"

NEW_TEST = '''"""F-CANOPY-069 -- no two callbacks may claim one output id.

Dash suffixes an ``allow_duplicate`` Output with ``@sha256(inputs)`` (``create_callback_id``), so two callbacks
that share an Output AND the same Inputs get the SAME id. The server registers both. dash 3's renderer validates
the served dependency list unconditionally and, on that ``Duplicate callback outputs`` error, drops the whole
callback graph: the page renders and nothing on it works. dash 4 validates only with dev tools on, runs both
members, and lets their response order decide what the shared prop ends up as. Measured 2026-10-20 on canopy
571743db: inert under dash 3.0.4, 3.2.0, 3.3.0 and 3.4.0, alive under 4.4.1 (juniper-ml
``reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json``; both members POST under 4.4.1,
``reports/e2e-canopy-2026-09-02/item32-turing/pair_members.json``).

The two pairs were ``accept_live_switch`` + ``open_progress_alert_on_accept`` (Input
``live-switch-accept-button.n_clicks``) and ``execute_restart`` + ``open_restart_progress`` (Input
``restart-confirm-button.n_clicks``). Each opener existed to show a progress spinner before the slow POST
returned, which is what a callback's ``running=`` spec is for, so the openers are gone and the specs are pinned
here.

Ids are parsed EXACTLY (``..a.prop@hash...b.prop..`` for a multi-output), never by substring: several of this
arc's ids are substrings of others, and ``live-switch-outcome-alert.children`` has a second, hashed writer.
"""

from __future__ import annotations

import collections

import pytest

from frontend.dashboard_manager import DashboardManager


@pytest.fixture(scope="module")
def dashboard():
    return DashboardManager({"title": "Test Dashboard", "update_interval": 1000, "server": {"host": "localhost", "port": 8050}})


def _output_ids(raw) -> list:
    """The individual output ids of one served callback, exactly as the renderer sees them."""
    raw = str(raw)
    if raw.startswith("..") and raw.endswith(".."):
        return raw[2:-2].split("...")
    return [raw]


def _bare(output_id: str) -> str:
    """``id.prop`` without the ``@hash`` suffix."""
    return output_id.split("@", 1)[0]


def _inputs(entry) -> list:
    return [f"{i['id']}.{i['property']}" for i in entry.get("inputs", [])]


def _collisions(callback_list) -> dict:
    """``{output id: [inputs of each claimant]}`` for every id more than one callback claims."""
    owners = collections.defaultdict(list)
    for entry in callback_list:
        for out in _output_ids(entry["output"]):
            owners[out].append(_inputs(entry))
    return {out: claimants for out, claimants in owners.items() if len(claimants) > 1}


def _served(dashboard):
    """The dependency list as ``GET /dashboard/_dash-dependencies`` serves it."""
    return dashboard.app._callback_list


def _only_entry_with_exact_output(dashboard, exact_id):
    matches = [e for e in _served(dashboard) if exact_id in _output_ids(e["output"])]
    assert len(matches) == 1, f"{exact_id}: expected exactly one callback with that exact output id, found {len(matches)}"
    return matches[0]


class TestNoOutputIdIsClaimedTwice:
    def test_no_output_id_is_claimed_by_two_callbacks(self, dashboard):
        collisions = _collisions(_served(dashboard))
        assert not collisions, f"output ids claimed by more than one callback (dash 3 drops the whole graph on any): {collisions}"

    def test_callback_map_and_served_list_agree(self, dashboard):
        """The registry is keyed by the served ``output`` string; a collision in one is a collision in the other."""
        served = sorted(str(e["output"]) for e in _served(dashboard))
        assert served == sorted(dashboard.app.callback_map.keys())

    def test_the_scan_sees_a_collision_where_one_exists(self):
        """Non-vacuity: a scratch app with the shape that bit canopy -- two callbacks, one Input, one
        ``allow_duplicate`` Output each -- yields exactly one colliding id, and it carries the hash."""
        from dash import Dash, Input, Output, dcc, html

        app = Dash(__name__)
        app.layout = html.Div([html.Button(id="go"), dcc.Store(id="out"), dcc.Store(id="other")])

        @app.callback([Output("other", "data"), Output("out", "data", allow_duplicate=True)], Input("go", "n_clicks"), prevent_initial_call=True)
        def slow(n):
            return n, False

        @app.callback(Output("out", "data", allow_duplicate=True), Input("go", "n_clicks"), prevent_initial_call=True)
        def fast(n):
            return True

        collisions = _collisions(app._callback_list)
        assert len(collisions) == 1
        (collided,) = collisions
        assert _bare(collided) == "out.data" and "@" in collided
        assert collisions[collided] == [["go.n_clicks"], ["go.n_clicks"]]


class TestTheProgressAlertsAreRunningSpecs:
    """The spinner idiom: the one callback that does the work opens its alert through ``running=`` the
    moment the request leaves, and the renderer closes it when the response lands."""

    def test_live_switch_accept_opens_its_alert_and_store_through_running(self, dashboard):
        entry = _only_entry_with_exact_output(dashboard, "live-switch-outcome-alert.children")
        assert _inputs(entry) == ["live-switch-accept-button.n_clicks"]
        assert entry.get("running") == {
            "running": {"live-switch-progress-alert.is_open": True, "live-swap-in-flight-store.data": {"in_flight": True}},
            "runningOff": {"live-switch-progress-alert.is_open": False, "live-swap-in-flight-store.data": {"in_flight": False}},
        }

    def test_restart_confirm_opens_its_alert_through_running(self, dashboard):
        entry = _only_entry_with_exact_output(dashboard, "restart-outcome-alert.children")
        assert _inputs(entry) == ["restart-confirm-button.n_clicks"]
        assert entry.get("running") == {"running": {"restart-progress-alert.is_open": True}, "runningOff": {"restart-progress-alert.is_open": False}}

    @pytest.mark.parametrize("alert", ["live-switch-progress-alert.is_open", "restart-progress-alert.is_open"])
    def test_each_progress_alert_has_exactly_one_writer(self, dashboard, alert):
        writers = [e for e in _served(dashboard) if alert in {_bare(o) for o in _output_ids(e["output"])}]
        assert len(writers) == 1, f"{alert}: {len(writers)} callbacks write it; their inputs: {[_inputs(w) for w in writers]}"

    @pytest.mark.parametrize("fired", ["live-switch-accept-button.n_clicks", "restart-confirm-button.n_clicks"])
    def test_each_fired_input_runs_exactly_one_callback(self, dashboard, fired):
        listeners = [e for e in _served(dashboard) if fired in _inputs(e)]
        assert len(listeners) == 1, f"{fired}: {len(listeners)} callbacks listen; their outputs: {[_output_ids(e['output']) for e in listeners]}"
'''

DM = "src/frontend/dashboard_manager.py"
T_LIVE = "src/tests/unit/frontend/test_live_dataset_switch_handlers.py"
T_INNER2 = "src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner2.py"
T_POLL = "src/tests/unit/frontend/test_poll_gating.py"

# (path, old, new) -- each old must occur exactly once; a new already present means "done".
REPLACEMENTS = [
    # --- dashboard_manager.py: the live-switch flow ---------------------------------------------
    (
        DM,
        """        Seven callbacks, each a thin wrapper around a class-level
        ``_*_handler`` method (P2-6 refactor — handlers are unit-tested
        in ``tests/unit/frontend/test_live_dataset_switch_handlers.py``):
""",
        """        Six callbacks, each a thin wrapper around a class-level
        ``_*_handler`` method (P2-6 refactor — handlers are unit-tested
        in ``tests/unit/frontend/test_live_dataset_switch_handlers.py``):
""",
    ),
    (
        DM,
        """        4. Accept → POST /api/live_dataset_swap → outcome alert.
        4b. Open progress alert immediately on Accept (split so spinner
            shows before the 5–30 s POST returns).
        5. Cancel during swap → DELETE /api/live_dataset_swap.
""",
        """        4. Accept → POST /api/live_dataset_swap → outcome alert. The
           progress alert and the in-flight store open the moment Accept
           is clicked through this callback's ``running=`` spec, not a
           second callback (F-CANOPY-069: an opener on the same Input
           collided with this callback's hashed output ids, and dash 3's
           renderer refused the whole callback graph).
        5. Cancel during swap → DELETE /api/live_dataset_swap.
""",
    ),
    (
        DM,
        """        @self.app.callback(
            [
                Output("live-switch-modal", "is_open", allow_duplicate=True),
                Output("live-switch-progress-alert", "is_open", allow_duplicate=True),
                Output("live-switch-outcome-alert", "children"),
                Output("live-swap-in-flight-store", "data", allow_duplicate=True),
            ],
            Input("live-switch-accept-button", "n_clicks"),
""",
        """        # F-CANOPY-069: the progress alert and the in-flight store used to be opened by a
        # SECOND callback on this same Input (``open_progress_alert_on_accept``) so that the
        # spinner showed before the 5–30 s POST returned. Two callbacks with one Input and the
        # same ``allow_duplicate`` Output get the same hashed output id (``create_callback_id``
        # hashes the inputs only): dash 3's renderer refuses the whole callback graph on that
        # collision ("Duplicate callback outputs") and the dashboard is inert, and dash 4 skips
        # the validation and runs both, racing their responses for the alert. ``running=`` is
        # the renderer's own idiom for exactly this: it sets the props client-side the moment
        # the request leaves and resets them when the response lands, with no second callback
        # and no round trip. (Not the F-CANOPY-058 shape: that guard wrote an Interval's
        # ``disabled`` and its release on an evicted request un-gated a lane; here an eviction
        # can only close a spinner the user re-clicked.)
        @self.app.callback(
            [
                Output("live-switch-modal", "is_open", allow_duplicate=True),
                Output("live-switch-progress-alert", "is_open", allow_duplicate=True),
                Output("live-switch-outcome-alert", "children"),
                Output("live-swap-in-flight-store", "data", allow_duplicate=True),
            ],
            Input("live-switch-accept-button", "n_clicks"),
""",
    ),
    (
        DM,
        """            State({"type": "nn-gen-param", "name": dash.ALL}, "id"),
            State("model-selection-store", "data"),
            prevent_initial_call=True,
        )
        def accept_live_switch(""",
        """            State({"type": "nn-gen-param", "name": dash.ALL}, "id"),
            State("model-selection-store", "data"),
            running=[
                (Output("live-switch-progress-alert", "is_open"), True, False),
                (Output("live-swap-in-flight-store", "data"), {"in_flight": True}, {"in_flight": False}),
            ],
            prevent_initial_call=True,
        )
        def accept_live_switch(""",
    ),
    (
        DM,
        """        @self.app.callback(
            [
                Output("live-switch-progress-alert", "is_open", allow_duplicate=True),
                Output("live-swap-in-flight-store", "data", allow_duplicate=True),
            ],
            Input("live-switch-accept-button", "n_clicks"),
            prevent_initial_call=True,
        )
        def open_progress_alert_on_accept(n_clicks):
            return self._open_progress_alert_on_accept_handler(n_clicks=n_clicks)

""",
        "",
    ),
    (
        DM,
        """        On every branch the modal + progress alert close and in_flight=False.
        \"\"\"
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
""",
        """        On every branch the modal + progress alert close and in_flight=False. The alert
        and the store are OPENED by the callback's ``running=`` spec the moment the request
        leaves (F-CANOPY-069), so no handler opens them.
        \"\"\"
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
""",
    ),
    (
        DM,
        """    def _open_progress_alert_on_accept_handler(self, n_clicks=None):
        \"\"\"Open the progress alert + flip in_flight=True the moment Accept
        is clicked.

        Returns ``(progress_open, in_flight)``. Split from the Accept POST
        handler so the user sees the spinner immediately rather than
        waiting for the (5–30 s) POST to return. Dash runs both callbacks
        on the worker pool; this one returns near-instantly.
        \"\"\"
        if not n_clicks:
            return dash.no_update, dash.no_update
        return True, {"in_flight": True}

""",
        "",
    ),
    # --- dashboard_manager.py: the restart flow -------------------------------------------------
    (
        DM,
        """        Five thin callbacks, each delegating to a class-level ``_*_handler`` so the
        branch logic is unit-testable by direct invocation:
""",
        """        Four thin callbacks, each delegating to a class-level ``_*_handler`` so the
        branch logic is unit-testable by direct invocation:
""",
    ),
    (
        DM,
        """        4. Open the progress spinner the instant Confirm is clicked (split so the
           spinner shows before the bounded stop→await→start POST returns).
        5. Execute — POST /api/train/restart {start_fresh, reset}; render every
           step's outcome (success incl. instant-convergence, or per-step failure
           with the upstream detail); close the modal + progress; keep the pending
           banner open on failure, close it on success.
""",
        """        4. Execute — POST /api/train/restart {start_fresh, reset}; render every
           step's outcome (success incl. instant-convergence, or per-step failure
           with the upstream detail); close the modal + progress; keep the pending
           banner open on failure, close it on success. The progress spinner opens
           the instant Confirm is clicked through this callback's ``running=`` spec
           (F-CANOPY-069: the separate opener callback on the same Input collided
           with this callback's hashed output id, and dash 3's renderer refused the
           whole callback graph).
""",
    ),
    (
        DM,
        """        @self.app.callback(
            Output("restart-progress-alert", "is_open", allow_duplicate=True),
            Input("restart-confirm-button", "n_clicks"),
            prevent_initial_call=True,
        )
        def open_restart_progress(n_clicks):
            if not n_clicks:
                return dash.no_update
            return True

""",
        "",
    ),
    (
        DM,
        """                dash.dependencies.State("model-selection-store", "data"),
            ],
            prevent_initial_call=True,
        )
        def execute_restart(""",
        """                dash.dependencies.State("model-selection-store", "data"),
            ],
            # F-CANOPY-069: the spinner is this callback's ``running=`` spec, not a second
            # callback on the same Input (see ``accept_live_switch``).
            running=[(Output("restart-progress-alert", "is_open"), True, False)],
            prevent_initial_call=True,
        )
        def execute_restart(""",
    ),
    (
        DM,
        """                # N3: restart progress alert — opens on Confirm (spinner while the
                # bounded stop → await → start POST is in flight). Split from the
                # outcome callback so the spinner shows before the POST returns.
""",
        """                # N3: restart progress alert — opens on Confirm (spinner while the
                # bounded stop → await → start POST is in flight). Opened by
                # ``execute_restart``'s ``running=`` spec the moment Confirm is
                # clicked and closed when its response lands (F-CANOPY-069: the
                # separate opener callback collided with it under dash 3).
""",
    ),
    # --- tests --------------------------------------------------------------------------------
    (
        T_LIVE,
        """Direct-invocation tests for the seven ``_handler`` methods refactored
""",
        """Direct-invocation tests for the six ``_handler`` methods refactored
""",
    ),
    (
        T_LIVE,
        """# ---------------------------------------------------------------------------
# 6. _open_progress_alert_on_accept_handler
# ---------------------------------------------------------------------------


class TestOpenProgressAlertOnAcceptHandler:
    \"\"\"Open the progress alert + flip in_flight=True the moment Accept
    is clicked. Split from the Accept POST handler so the spinner shows
    before the POST returns (5–30s).\"\"\"

    def test_click_returns_open_and_in_flight(self, dm):
        assert dm._open_progress_alert_on_accept_handler(n_clicks=1) == (True, {"in_flight": True})

    def test_no_click_returns_no_update(self, dm):
        assert dm._open_progress_alert_on_accept_handler(n_clicks=None) == (dash.no_update, dash.no_update)


""",
        """# ---------------------------------------------------------------------------
# 6. (gone) _open_progress_alert_on_accept_handler
# ---------------------------------------------------------------------------
# F-CANOPY-069: the progress alert and the in-flight store are opened by
# ``accept_live_switch``'s ``running=`` spec, not by a second callback on the
# same Input -- its hashed output ids collided with the accept callback's and
# dash 3's renderer refused the whole graph. The spec is pinned in
# ``test_f069_duplicate_callback_outputs.py``.


""",
    ),
    (
        T_INNER2,
        """    def test_open_progress_alert_on_accept(self, dm):
        cb = raw_cb(dm, "open_progress_alert_on_accept")
        progress, in_flight = cb(1)
        assert progress is True and in_flight == {"in_flight": True}
""",
        """    def test_accept_live_switch_opens_the_progress_alert_through_running(self, dm):
        # F-CANOPY-069: no second callback opens the alert; the accept callback's
        # ``running=`` spec does, client-side, the moment the request leaves. Exact
        # id parsing: the cancel callback writes the same prop under an ``@hash``.
        def exact_outputs(raw):
            raw = str(raw)
            return raw[2:-2].split("...") if raw.startswith("..") else [raw]

        entries = [e for e in dm.app._callback_list if "live-switch-outcome-alert.children" in exact_outputs(e["output"])]
        assert len(entries) == 1
        assert entries[0].get("running") == {
            "running": {"live-switch-progress-alert.is_open": True, "live-swap-in-flight-store.data": {"in_flight": True}},
            "runningOff": {"live-switch-progress-alert.is_open": False, "live-swap-in-flight-store.data": {"in_flight": False}},
        }
""",
    ),
    (
        T_POLL,
        """        \"\"\"Non-vacuity. canopy has no ``running=`` guard left (F-CANOPY-058), so the
        scan is checked on a scratch app that registers one.\"\"\"
""",
        """        \"\"\"Non-vacuity. canopy has no ``running=`` guard on an Interval left (F-CANOPY-058;
        the two ``running=`` specs it does carry, F-CANOPY-069's progress alerts, write an
        alert's ``is_open`` and a store), so the scan is checked on a scratch app that
        registers one.\"\"\"
""",
    ),
    (
        T_POLL,
        """    def test_no_running_guard_is_left_in_canopy(self, dashboard):
        \"\"\"F-CANOPY-058: any guard is released by an evicted request's late completion,
        so none may come back on a poll lane. Pace a slow poll by request/ack instead.\"\"\"
        assert not self._guarded_props(dashboard), self._guarded_props(dashboard)
""",
        """    def test_no_running_guard_is_left_on_a_poll_lane(self, dashboard):
        \"\"\"F-CANOPY-058: any guard is released by an evicted request's late completion,
        so none may come back on a poll lane. Pace a slow poll by request/ack instead.
        Registry-wide over every ``dcc.Interval`` in the layout, on any prop. The
        ``running=`` specs canopy does carry since F-CANOPY-069 open a click's progress
        alert (and the live-swap in-flight store) for the request's own life: an
        eviction there closes a spinner the user re-clicked, and gates nothing. They are
        enumerated here so the next spec is added to this list on purpose.\"\"\"
        intervals = {cid for cid, comp in _components_by_id(dashboard).items() if type(comp).__name__ == "Interval"}
        assert intervals, "the layout walk found no Interval; the lane check would pass vacuously"
        on_a_lane = [f for f in self._guarded_props(dashboard) if f[2].split(".", 1)[0] in intervals]
        assert not on_a_lane, f"a running= guard writes a poll lane: {on_a_lane}"
        f069 = {"live-switch-progress-alert.is_open", "live-swap-in-flight-store.data", "restart-progress-alert.is_open"}
        assert {f[2] for f in self._guarded_props(dashboard)} == f069, self._guarded_props(dashboard)
""",
    ),
    # --- the floor, the conda file, the changelog ------------------------------------------------
    (
        "pyproject.toml",
        """    "dash>=3.0.0",
""",
        """    "dash>=4.0.0",
""",
    ),
    (
        "conf/requirements_ci.txt",
        """
dash>=3.0
""",
        """
dash>=4.0
""",
    ),
    (
        "conf/conda_environment.yaml",
        """dash=3.3.0=pyhd8ed1ab_0
""",
        """dash=4.4.1=pyhd8ed1ab_0
""",
    ),
    (
        "conf/conda_environment.yaml",
        """colorama=0.4.6=pyhd8ed1ab_1
conda-gcc-specs=14.3.0=he8ccf15_15
""",
        """colorama=0.4.6=pyhd8ed1ab_1
comm=0.2.3=pyhe01879c_0
conda-gcc-specs=14.3.0=he8ccf15_15
""",
    ),
    (
        "conf/conda_environment.yaml",
        """itsdangerous=2.2.0=pyhd8ed1ab_1
jinja2=3.1.6=pyhcf101f3_1
""",
        """itsdangerous=2.2.0=pyhd8ed1ab_1
janus=2.0.0=pyhd8ed1ab_0
jinja2=3.1.6=pyhcf101f3_1
""",
    ),
    (
        "CHANGELOG.md",
        """## [Unreleased]

## [0.9.0] - 2026-10-10
""",
        """## [Unreleased]

### Fixed

- **F-CANOPY-069: under every dash 3.x release the dashboard was inert in the browser.** Two callback pairs each
  claimed one `allow_duplicate` Output from one Input: `accept_live_switch` and `open_progress_alert_on_accept` on
  `live-switch-accept-button.n_clicks`, and `execute_restart` and `open_restart_progress` on
  `restart-confirm-button.n_clicks`. Dash hashes the inputs into an `allow_duplicate` output id
  (`create_callback_id`), so each pair's ids collided. dash 3's renderer validates the served dependency list
  unconditionally and, on that `Duplicate callback outputs` error, drops the whole callback graph: the page
  rendered and nothing on it worked (measured on 3.0.4, 3.2.0, 3.3.0 and 3.4.0; `conf/conda_environment.yaml`
  pinned 3.3.0). dash 4 validates only with dev tools on, ran both members of each pair, and let the order of
  their responses decide whether the spinner flashed or stuck. The openers existed to show the progress spinner
  before the slow POST returned, which is what a callback's `running=` spec is for: `accept_live_switch` and
  `execute_restart` now carry their progress alerts (and the live-swap in-flight store) as `running=`, so the
  renderer opens them the moment the request leaves and closes them when the response lands, with no second
  callback and no round trip. `open_progress_alert_on_accept`, `open_restart_progress` and
  `_open_progress_alert_on_accept_handler` are gone. Pinned by
  `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py`: no output id is claimed by two callbacks
  (ids computed as `create_callback_id` does, over the served dependency list; the scan is shown to catch the
  shape that bit canopy), each progress alert has one writer, each of the two Inputs runs one callback, and the
  two `running` specs are what the renderer expects. Verified alive in the browser on legs of this tree under
  dash 3.3.0 and 4.4.1 (juniper-ml `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py`, Phase 14's
  per-dash probe; one POST per click, the spinner opening on the request and closing on the response,
  `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`). Ledger: juniper-ml
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 14 (filed) and Phase 15 (closed).

### Changed

- **The dash floor is `dash>=4.0.0`** (`pyproject.toml`; `conf/requirements_ci.txt`, which `requirements.txt` and
  `requirements_ci.txt` link to), and `conf/conda_environment.yaml` pins `dash=4.4.1` with dash 4's two new run
  dependencies, `comm` and `janus`, at the lock's versions. Everything canopy tests runs dash 4.x (the lock's 4.4.1,
  CI's 4.4.1 pip lane and 4.1.0 conda lane, every live drive in the E2E ledger), and a floor that nothing tests is
  how F-CANOPY-069 stayed invisible: the conda file was the one environment on 3.x, and it was the one nobody
  drove. The fix itself does not depend on the dash version; a 3.3.0 leg of this tree is alive too.

## [0.9.0] - 2026-10-10
""",
        "- **F-CANOPY-069: under every dash 3.x release the dashboard was inert in the browser.** Two callback pairs each\n",
    ),
]


def apply(root: str, check_only: bool) -> int:
    pending = []
    for entry in REPLACEMENTS:
        # An entry may carry a 4th element, a marker unique to its new text: a later change can land INSIDE an
        # inserted block (canopy#761 put its CHANGELOG entries inside this one), after which neither the old anchor
        # nor the whole new block exists, though the step ran (round 1 of the ledger's Phase 15, Lane 15-C).
        path, old, new = entry[:3]
        done_marker = entry[3] if len(entry) > 3 else None
        full = os.path.join(root, path)
        try:
            with open(full, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"ERROR cannot read {path}: {exc}")
            return 1
        # Done already? An insertion's new text may CONTAIN its old text, so this is
        # checked first; a deletion is done when its full old text is gone.
        if (new and new in text) or (done_marker and done_marker in text):
            print(f"done    {path}: {old.strip().splitlines()[0][:70]!r}")
            continue
        n_old = text.count(old)
        if n_old == 0:
            if not new:
                print(f"done    {path}: deletion of {old.strip().splitlines()[0][:70]!r}")
                continue
            print(f"ERROR   {path}: expected text not found: {old.strip().splitlines()[0][:90]!r}")
            return 1
        if n_old > 1:
            print(f"ERROR   {path}: expected text found {n_old} times: {old.strip().splitlines()[0][:90]!r}")
            return 1
        pending.append((path, old, new))
    new_test_full = os.path.join(root, NEW_TEST_PATH)
    new_test_pending = True
    if os.path.exists(new_test_full):
        with open(new_test_full, encoding="utf-8") as fh:
            if fh.read() == NEW_TEST:
                new_test_pending = False
                print(f"done    {NEW_TEST_PATH}")
            else:
                print(f"replace {NEW_TEST_PATH} (content differs)")
    if check_only:
        for path, old, _new in pending:
            print(f"would   {path}: {old.strip().splitlines()[0][:70]!r}")
        if new_test_pending:
            print(f"would   write {NEW_TEST_PATH}")
        return 0
    for path, old, new in pending:
        full = os.path.join(root, path)
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        assert text.count(old) == 1
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, new, 1))
        print(f"applied {path}: {old.strip().splitlines()[0][:70]!r}")
    if new_test_pending:
        os.makedirs(os.path.dirname(new_test_full), exist_ok=True)
        with open(new_test_full, "w", encoding="utf-8") as fh:
            fh.write(NEW_TEST)
        print(f"wrote   {NEW_TEST_PATH}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="a juniper-canopy tree at main 571743db (or a later main carrying the same text)")
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isfile(os.path.join(root, DM)):
        print(f"ERROR {root} has no {DM}")
        return 2
    return apply(root, args.check)


if __name__ == "__main__":
    sys.exit(main())
