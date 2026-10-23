#!/usr/bin/env python3
"""Apply canopy's F-CANOPY-028 fix (item 31) to a juniper-canopy tree carrying main + the F-CANOPY-069 fix -- replayable, exact-match, idempotent.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 31 (F-CANOPY-028: a pin made just before a table rebuild is discarded;
              and the manual's row idiom for ``output_weights``, F-CANOPY-012's cases B and C)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (F-CANOPY-028's Phase 14 blockquote; item 31);
              util/ad-hoc/2026-10-20_f069_apply_fix.py (the same mechanism, item 32; this tree is its output);
              util/ad-hoc/2026-10-20_item30_fixwave_redrive.py (``--step f028``, the ``delay<N>`` arms)
License:      MIT License

WHY A SCRIPT. See 2026-10-20_f069_apply_fix.py: turing lands through the API as whole-file uploads, so the edit is
kept as exact-match replacements that refuse anything but the expected text and can be replayed on a fresh copy
of main. The anchors here include the F-CANOPY-069 CHANGELOG entry, so the tree must carry that fix (canopy#760).

THE FIX. ``update_pinned_params_store`` fires on every change to any pin checkbox's ``value``: a user's toggle, and
every rebuild of the Parameters tables, which re-creates all 22 checkboxes so every one arrives as "changed". A
rebuild whose request was in flight when a click's write landed renders the pin set it was computed from and fires
the writer with that stale set; canopy#533's merge of the rendered set into the stored one then persisted it over
the click (Phase 14, item 30: one drive in eight). The writer now persists a USER TOGGLE only -- exactly one pin
input triggered, read through ``CallbackContextAdapter.get_triggered_prop_ids`` -- adding or removing that key
alone; a rebuild (every input triggered at once) and a toggle the store already reflects write nothing.
``_merge_pinned_params`` becomes ``_apply_pin_toggle``; the tests are re-stated for the toggle and the stale
rebuild; the manual's Patch Weights sentence gets the row idiom; CHANGELOG.md gets the entries.

Usage:
    python3 -I util/ad-hoc/2026-10-20_f028_apply_fix.py --root ~/.local/state/juniper/turing-e2/trees/juniper-canopy-f028
    python3 -I util/ad-hoc/2026-10-20_f028_apply_fix.py --root <copy of main> --check   # report only, write nothing
"""

from __future__ import annotations

import argparse
import os
import sys

DM = "src/frontend/dashboard_manager.py"
T_B = "src/tests/unit/frontend/test_p2_wave_batch_b.py"
T_INNER1 = "src/tests/unit/frontend/test_dashboard_manager_gate_coverage_inner1.py"
MANUAL = "docs/USER_MANUAL.md"

REPLACEMENTS = [
    # --- dashboard_manager.py: the writer --------------------------------------------------------
    (
        DM,
        """        # F-CANOPY-018 / F-CANOPY-028: this writer collects the state of EVERY pin
        # checkbox and replaces the store wholesale, so it asserts "not pinned" for
        # every key whose checkbox it cannot see. The rendered set is not always the
        # full set: the Parameters tables are rebuilt on every params-store change,
        # and any render that happens while the store is empty or stale (mount before
        # ``storage_type="local"`` hydration, a tab whose tables are not in the DOM)
        # produces a values/ids pair that under-reports the real pin set — and the
        # next toggle then persists that under-report, silently discarding pins made
        # before a reload. It now writes only what it can actually observe and
        # preserves the rest.
        @self.app.callback(
            Output("pinned-params-store", "data"),
            Input({"type": "param-pin", "key": dash.ALL}, "value"),
            dash.dependencies.State({"type": "param-pin", "key": dash.ALL}, "id"),
            dash.dependencies.State("pinned-params-store", "data"),
            prevent_initial_call=True,
        )
        def update_pinned_params_store(values, ids, current):
            \"\"\"Merge the rendered checkboxes' state into the persisted pin list.\"\"\"
            return self._merge_pinned_params(values, ids, current)
""",
        """        # F-CANOPY-018 / F-CANOPY-028: this writer fires on EVERY change to any pin
        # checkbox's ``value`` — a user's toggle, and every rebuild of the Parameters
        # tables (the tables are rebuilt on every params-store or pin-store change, and
        # a rebuild re-creates all 22 checkboxes, so every one of them arrives as
        # "changed"). canopy#533 made it merge the rendered set into the stored one,
        # which closed the mount-with-an-empty-store shape; the Phase 14 re-drive
        # (2026-10-20) caught the other one: a rebuild whose request was in flight when
        # a click's write landed renders the pin set it was computed from, fires this
        # writer with that stale set, and the merge persisted it over the click. The
        # writer now acts on a USER TOGGLE only — exactly one pin input triggered — and
        # adds or removes that key alone; a rebuild (every input triggered at once) and
        # a toggle the store already reflects write nothing. Renders follow the store;
        # the store follows the user.
        @self.app.callback(
            Output("pinned-params-store", "data"),
            Input({"type": "param-pin", "key": dash.ALL}, "value"),
            dash.dependencies.State({"type": "param-pin", "key": dash.ALL}, "id"),
            dash.dependencies.State("pinned-params-store", "data"),
            prevent_initial_call=True,
        )
        def update_pinned_params_store(values, ids, current):
            \"\"\"Persist a user's toggle of one pin checkbox; ignore a rebuilt table.\"\"\"
            triggered = list(get_callback_context().get_triggered_prop_ids().values())
            return self._apply_pin_toggle(triggered, values, ids, current)
""",
    ),
    (
        DM,
        """    @staticmethod
    def _merge_pinned_params(values, ids, current):
        \"\"\"Merge the RENDERED pin checkboxes into the persisted pin list (F-CANOPY-028).

        The pattern-matched writer used to rebuild the whole list from the DOM, which
        makes "this checkbox is absent" indistinguishable from "this key is not
        pinned". Any render that under-reports the pin set — a mount before the
        ``storage_type="local"`` store hydrates, or tables that are not in the DOM —
        therefore got persisted on the next toggle, discarding earlier pins with no
        warning.

        Rules:

        - No checkboxes rendered at all → ``no_update``. An empty component set is
          never evidence that nothing is pinned, and writing ``[]`` there is exactly
          how a full pin set gets wiped.
        - Otherwise, keys whose checkbox IS rendered take their state from it (so
          unpinning still works), and keys that are pinned but NOT rendered are
          carried through untouched.

        Order is stable: preserved-but-unseen keys first, then the rendered keys in
        render order, so the sidebar mirror does not reshuffle on every toggle.
        \"\"\"
        rendered = [i.get("key") for i in (ids or []) if isinstance(i, dict) and i.get("key")]
        if not rendered:
            return dash.no_update
        checked = {i.get("key") for v, i in zip(values or [], ids or [], strict=False) if v and isinstance(i, dict)}
        rendered_set = set(rendered)
        preserved = [k for k in (current or []) if k and k not in rendered_set]
        return preserved + [k for k in rendered if k in checked]
""",
        """    @staticmethod
    def _apply_pin_toggle(triggered, values, ids, current):
        \"\"\"Persist a USER'S toggle of one pin checkbox, and nothing else (F-CANOPY-028).

        ``triggered`` is the list of component ids (the pattern-matching dicts) whose
        ``value`` fired this call: ``CallbackContextAdapter.get_triggered_prop_ids()``'s
        values. A user's click changes exactly one checkbox. A rebuilt table arrives
        with EVERY checkbox triggered at once, carrying the pin set the render was
        computed from — stale whenever its request was in flight while a click's write
        landed — and the mount render arrives the same way with whatever the store held
        when the page loaded. Neither is evidence about what the user wants pinned, so
        neither writes. (The pre-#533 writer rebuilt the list from the DOM and wiped
        off-screen pins; #533's merge of the rendered set into the stored one kept
        those but still persisted a stale rebuild over a click made just before it.)

        Rules:

        - not exactly one ``param-pin`` id triggered → ``no_update`` (a rebuild, or
          nothing);
        - the toggled key's rendered value decides it alone: checked → appended to the
          stored list if absent; unchecked → removed if present; every other key is
          carried through untouched, in its stored order, whatever its checkbox shows;
        - a toggle the store already reflects → ``no_update`` (no write, no re-render).
        \"\"\"
        keys = [t.get("key") for t in (triggered or []) if isinstance(t, dict) and t.get("type") == "param-pin" and t.get("key")]
        if len(keys) != 1:
            return dash.no_update
        key = keys[0]
        checked = None
        for value, cid in zip(values or [], ids or [], strict=False):
            if isinstance(cid, dict) and cid.get("key") == key:
                checked = bool(value)
                break
        if checked is None:
            return dash.no_update
        stored = [k for k in (current or []) if k]
        if checked:
            return dash.no_update if key in stored else stored + [key]
        return [k for k in stored if k != key] if key in stored else dash.no_update
""",
    ),
    # --- tests -------------------------------------------------------------------------------------
    (
        T_B,
        """@pytest.mark.unit
class TestF028PinnedParamsPreserved:
    \"\"\"The pattern-matched writer rebuilt the whole list from the DOM, so it asserted
    "not pinned" for every key whose checkbox it could not see — and the next toggle
    persisted that under-report.
    \"\"\"

    @staticmethod
    def _ids(*keys):
        return [{"type": "param-pin", "key": k} for k in keys]

    def test_unrendered_pins_are_preserved(self, dm):
        \"\"\"THE regression: pinning a NEW key must not drop a key that is off-screen.\"\"\"
        result = dm._merge_pinned_params([True], self._ids("max_iterations"), ["learning_rate"])
        assert "learning_rate" in result, "a pin whose checkbox was not rendered was silently discarded"
        assert "max_iterations" in result

    def test_no_checkboxes_rendered_is_never_a_wipe(self, dm):
        \"\"\"An empty component set is not evidence that nothing is pinned.\"\"\"
        assert dm._merge_pinned_params([], [], ["learning_rate", "patience"]) is dash.no_update
        assert dm._merge_pinned_params(None, None, ["learning_rate"]) is dash.no_update

    def test_unpinning_a_rendered_key_still_works(self, dm):
        \"\"\"Forward guard: preserving the unseen must not make pins un-removable.\"\"\"
        result = dm._merge_pinned_params([False, True], self._ids("learning_rate", "patience"), ["learning_rate", "patience"])
        assert result == ["patience"]

    def test_rendered_state_wins_over_the_stored_value(self, dm):
        \"\"\"A rendered checkbox is authoritative for its own key, checked or not.\"\"\"
        assert dm._merge_pinned_params([False], self._ids("a"), ["a"]) == []
        assert dm._merge_pinned_params([True], self._ids("a"), []) == ["a"]

    def test_order_is_stable(self, dm):
        \"\"\"Unseen keys first, then render order — the sidebar must not reshuffle.\"\"\"
        result = dm._merge_pinned_params([True, True], self._ids("b", "c"), ["a", "b"])
        assert result == ["a", "b", "c"]

    def test_empty_and_malformed_ids_do_not_crash(self, dm):
        assert dm._merge_pinned_params([True], [None], ["x"]) is dash.no_update
        assert dm._merge_pinned_params([True], [{"type": "param-pin"}], ["x"]) is dash.no_update
""",
        """@pytest.mark.unit
class TestF028PinnedParamsPreserved:
    \"\"\"The pattern-matched writer used to persist the RENDERED pin set: first the whole
    list rebuilt from the DOM (an off-screen pin read as "not pinned"), then, after
    canopy#533, the rendered set merged into the stored one — which still persisted a
    rebuilt table's stale set over a click made just before it (Phase 14, item 30: one
    drive in eight). It now persists a user's toggle alone: exactly one pin input
    triggered, that key added or removed, the rest untouched; a rebuild (every input
    triggered at once) writes nothing.
    \"\"\"

    ALL_KEYS = ("learning_rate", "max_iterations", "patience", "output_epochs")

    @staticmethod
    def _ids(*keys):
        return [{"type": "param-pin", "key": k} for k in keys]

    def test_unrendered_pins_are_preserved(self, dm):
        \"\"\"THE regression: pinning a NEW key must not drop a key that is off-screen.\"\"\"
        result = dm._apply_pin_toggle(self._ids("max_iterations"), [True], self._ids("max_iterations"), ["learning_rate"])
        assert result == ["learning_rate", "max_iterations"], "a pin whose checkbox was not rendered was silently discarded"

    def test_a_rebuilt_table_from_a_stale_set_writes_nothing(self, dm):
        \"\"\"Phase 14's loss (early#2): the click stored both keys, then a rebuild computed
        from the pre-click set arrived with every checkbox triggered and the new pin
        unchecked. The store keeps the toggle.\"\"\"
        ids = self._ids(*self.ALL_KEYS)
        values = [True, False, False, False]  # learning_rate checked; max_iterations stale, unchecked
        assert dm._apply_pin_toggle(ids, values, ids, ["learning_rate", "max_iterations"]) is dash.no_update

    def test_the_mount_render_writes_nothing_even_with_an_empty_store(self, dm):
        \"\"\"The original shape: a mount before the local store hydrates rendered every
        checkbox unchecked, and the writer persisted ``[]``.\"\"\"
        ids = self._ids(*self.ALL_KEYS)
        assert dm._apply_pin_toggle(ids, [False] * 4, ids, ["learning_rate", "patience"]) is dash.no_update
        assert dm._apply_pin_toggle(ids, [False] * 4, ids, []) is dash.no_update

    def test_no_checkboxes_rendered_is_never_a_wipe(self, dm):
        \"\"\"An empty component set is not evidence that nothing is pinned.\"\"\"
        assert dm._apply_pin_toggle([], [], [], ["learning_rate", "patience"]) is dash.no_update
        assert dm._apply_pin_toggle(None, None, None, ["learning_rate"]) is dash.no_update

    def test_unpinning_a_rendered_key_still_works(self, dm):
        \"\"\"Forward guard: acting on the toggle alone must not make pins un-removable.\"\"\"
        ids = self._ids("learning_rate", "patience")
        result = dm._apply_pin_toggle(self._ids("learning_rate"), [False, True], ids, ["learning_rate", "patience"])
        assert result == ["patience"]

    def test_rendered_state_wins_over_the_stored_value(self, dm):
        \"\"\"The toggled checkbox is authoritative for its own key, checked or not; a
        toggle the store already reflects writes nothing.\"\"\"
        assert dm._apply_pin_toggle(self._ids("a"), [False], self._ids("a"), ["a"]) == []
        assert dm._apply_pin_toggle(self._ids("a"), [True], self._ids("a"), []) == ["a"]
        assert dm._apply_pin_toggle(self._ids("a"), [True], self._ids("a"), ["a"]) is dash.no_update
        assert dm._apply_pin_toggle(self._ids("a"), [False], self._ids("a"), []) is dash.no_update

    def test_order_is_stable(self, dm):
        \"\"\"The stored order is kept and a new pin is appended — the sidebar must not reshuffle.\"\"\"
        result = dm._apply_pin_toggle(self._ids("c"), [True, True], self._ids("b", "c"), ["a", "b"])
        assert result == ["a", "b", "c"]

    def test_only_the_toggled_key_changes(self, dm):
        \"\"\"The other rendered checkboxes, however stale, are not consulted.\"\"\"
        ids = self._ids("a", "b", "c")
        assert dm._apply_pin_toggle(self._ids("c"), [False, False, True], ids, ["a", "b"]) == ["a", "b", "c"]

    def test_empty_and_malformed_ids_do_not_crash(self, dm):
        assert dm._apply_pin_toggle([None], [True], [None], ["x"]) is dash.no_update
        assert dm._apply_pin_toggle([{"type": "param-pin"}], [True], [{"type": "param-pin"}], ["x"]) is dash.no_update
        assert dm._apply_pin_toggle(self._ids("a"), [], [], ["x"]) is dash.no_update
""",
    ),
    (
        T_INNER1,
        """    def test_update_pinned_params_store(self, dm):
        cb = raw_cb(dm, "update_pinned_params_store")
        values = [True, None, False]
        ids = [{"type": "param-pin", "key": "a"}, {"type": "param-pin", "key": "b"}, {"type": "param-pin", "key": "c"}]
        # F-CANOPY-028: the writer now takes the persisted list as a third arg so it
        # can preserve pins whose checkbox is not currently rendered.
        assert cb(values, ids, []) == ["a"]
""",
        """    def test_update_pinned_params_store(self, dm):
        cb = raw_cb(dm, "update_pinned_params_store")
        values = [True, None, False]
        ids = [{"type": "param-pin", "key": "a"}, {"type": "param-pin", "key": "b"}, {"type": "param-pin", "key": "c"}]
        # F-CANOPY-028: the writer persists a USER toggle only — exactly one pin input
        # triggered, read through the adapter — and a rebuilt table (every input
        # triggered at once) writes nothing, whatever the rendered state says.
        one = {'{"key":"a","type":"param-pin"}.value': ids[0]}
        with patch.object(CallbackContextAdapter, "get_triggered_prop_ids", return_value=one):
            assert cb(values, ids, []) == ["a"]
        every = {f'{{"key":"{i["key"]}","type":"param-pin"}}.value': i for i in ids}
        with patch.object(CallbackContextAdapter, "get_triggered_prop_ids", return_value=every):
            assert cb(values, ids, ["b"]) is dash.no_update
""",
    ),
    # --- the manual's row idiom (item 31b) ---------------------------------------------------------
    (
        MANUAL,
        """   - Values can be entered as comma-, semicolon-, or newline-separated floats.
""",
        """   - Values are floats separated by commas or spaces. `output_weights` is a matrix, one row per input or hidden
     unit and one value per output unit: enter it as rows separated by newlines or semicolons, or as one flat
     comma-separated list of the full count, which Canopy reshapes from the topology readout. A flat list broken
     up by semicolons or newlines is read as one value per row and refused on any network with more than one
     output.
""",
    ),
    # --- the changelog -----------------------------------------------------------------------------
    (
        "CHANGELOG.md",
        """  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 14 (filed) and Phase 15 (closed).

### Changed
""",
        """  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 14 (filed) and Phase 15 (closed).
- **F-CANOPY-028: a pin made just before a table rebuild was discarded.** `update_pinned_params_store` fires on every
  change to any pin checkbox's `value`, and the Parameters tables are rebuilt on every params-store or pin-store
  change, each rebuild re-creating all 22 checkboxes, so a rebuild whose request was in flight when a click's write
  landed rendered the pin set it was computed from, fired the writer with every checkbox "changed" and the new pin
  unchecked, and the writer (canopy#533's merge of the rendered set into the stored one) persisted that set over
  the click (juniper-ml ledger Phase 14, item 30: one drive in eight; the mount render used to do the same with an
  empty store, the shape #533 closed). The writer now persists a user's toggle only: exactly one pin input
  triggered (`CallbackContextAdapter.get_triggered_prop_ids`), that key added to or removed from the stored list,
  the rest untouched; a rebuild (every input triggered at once) and a toggle the store already reflects write
  nothing. `_merge_pinned_params` is replaced by `_apply_pin_toggle`. Tests: `test_p2_wave_batch_b.py`
  (`TestF028PinnedParamsPreserved`: a rebuilt table from a stale set after a toggle leaves the store as the toggle
  left it, the mount render writes nothing, the toggle cases) and `test_dashboard_manager_gate_coverage_inner1.py`.
  Live: the pin-after-reload drive (`2026-10-20_item30_fixwave_redrive.py --step f028`) at fixed delays after the
  reload, on a leg of this tree, is recorded in the ledger's Phase 15.
- **`docs/USER_MANUAL.md`, Patch Weights:** the values sentence said comma-, semicolon- or newline-separated
  floats; for `output_weights` semicolons and newlines separate rows, so F-CANOPY-012's cases B and C (a flat list
  broken up by either) are refused on any network with more than one output. The sentence now states the row idiom
  and the flat-list reshape.

### Changed
""",
    ),
]


def apply(root: str, check_only: bool) -> int:
    pending = []
    for path, old, new in REPLACEMENTS:
        full = os.path.join(root, path)
        try:
            with open(full, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"ERROR cannot read {path}: {exc}")
            return 1
        if new and new in text:
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
    if check_only:
        for path, old, _new in pending:
            print(f"would   {path}: {old.strip().splitlines()[0][:70]!r}")
        return 0
    for path, old, new in pending:
        full = os.path.join(root, path)
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        assert text.count(old) == 1
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, new, 1))
        print(f"applied {path}: {old.strip().splitlines()[0][:70]!r}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="a juniper-canopy tree at main + canopy#760 (the F-CANOPY-069 fix)")
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isfile(os.path.join(root, DM)):
        print(f"ERROR {root} has no {DM}")
        return 2
    return apply(root, args.check)


if __name__ == "__main__":
    sys.exit(main())
