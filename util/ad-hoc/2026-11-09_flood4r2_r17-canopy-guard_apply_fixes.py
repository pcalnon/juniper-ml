"""
Apply the ruling-17 test fixes to a juniper-canopy worktree: mock the transport every census-caught test reached.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). The base census
(util/ad-hoc/2026-11-09_flood4r2_r17-canopy-guard_census.py) found 16 unit-lane tests connecting to
127.0.0.1:8050 and 2 to 127.0.0.1:8200. Each edit below is an exact-text replacement with its expected
occurrence count; the script refuses to write a file whose count differs (nothing is applied twice or
silently missed), and ``--revert`` applies the inverse, which the mutation checks use. The 17th fix,
test_dashboard_helpers_coverage.py, was made by hand before this script and is not repeated here.

Pattern A (10 tests): ``_apply_params_via_backend`` reads ``/api/state`` back after a 200 POST; the tests
mocked only ``requests.post``. Pattern B (6 tests): ``_gate_dataset_options_handler`` with no ``generators``
fetches ``/api/dataset/generators``; the tests pin the state that fetch's FAILURE produces. :8200 (2 tests):
``start_metrics_relay`` starts the control-stream supervisor, whose ``CascorControlStream`` dials the adapter's
``ws://localhost:8200``.

Usage:
  python3 <this file> --wt <canopy worktree> [--revert] [--only <repo-relative file>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

READ_BACK = "        # The handler reads /api/state back after a 200; unmocked, that read reached 127.0.0.1:8050.\n"

EDITS: list[tuple[str, str, str, int]] = [
    (
        "src/tests/unit/frontend/test_dashboard_manager.py",
        '    def test_apply_parameters_success(self, dashboard_manager, mocker):\n        """Test apply_parameters successfully applies parameters."""\n        mock_response = MagicMock()\n        mock_response.status_code = 200\n        mocker.patch("requests.post", return_value=mock_response)\n',
        '    def test_apply_parameters_success(self, dashboard_manager, mocker):\n        """Test apply_parameters successfully applies parameters."""\n        mock_response = MagicMock()\n        mock_response.status_code = 200\n        mocker.patch("requests.post", return_value=mock_response)\n' + READ_BACK + '        mocker.patch("requests.get", return_value=MagicMock(status_code=200, json=MagicMock(return_value={})))\n',
        1,
    ),
    (
        "src/tests/unit/frontend/test_dashboard_manager_95.py",
        '    def test_parameter_handlers_with_edge_values(self, dashboard_manager, mocker):\n        """Test parameter handlers with edge case values."""\n        mock_response = MagicMock()\n        mock_response.status_code = 200\n        mocker.patch("requests.post", return_value=mock_response)\n',
        '    def test_parameter_handlers_with_edge_values(self, dashboard_manager, mocker):\n        """Test parameter handlers with edge case values."""\n        mock_response = MagicMock()\n        mock_response.status_code = 200\n        mocker.patch("requests.post", return_value=mock_response)\n' + READ_BACK + '        mocker.patch("requests.get", return_value=MagicMock(status_code=200, json=MagicMock(return_value={})))\n',
        1,
    ),
    (
        "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
        '    @patch("requests.post")\n    def test_apply_parameters_handler_success(self, mock_post, dashboard_manager):\n        """Test apply parameters handler with success."""\n        mock_response = Mock()\n        mock_response.status_code = 200\n        mock_post.return_value = mock_response\n',
        '    @patch("requests.get")\n    @patch("requests.post")\n    def test_apply_parameters_handler_success(self, mock_post, mock_get, dashboard_manager):\n        """Test apply parameters handler with success."""\n        mock_response = Mock()\n        mock_response.status_code = 200\n        mock_post.return_value = mock_response\n' + READ_BACK + "        mock_get.return_value = Mock(status_code=200, json=Mock(return_value={}))\n",
        1,
    ),
    (
        "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
        '    @patch("frontend.dashboard_manager.time.sleep")\n    @patch("requests.post")\n    def test_apply_parameters_handler_429_backs_off_then_succeeds(self, mock_post, mock_sleep, dashboard_manager):\n',
        '    @patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value={})))  # the /api/state read-back after the 200\n    @patch("frontend.dashboard_manager.time.sleep")\n    @patch("requests.post")\n    def test_apply_parameters_handler_429_backs_off_then_succeeds(self, mock_post, mock_sleep, _mock_get, dashboard_manager):\n',
        1,
    ),
    (
        "src/tests/unit/frontend/test_dashboard_manager_handlers.py",
        '    @patch("frontend.dashboard_manager.time.sleep")\n    @patch("requests.post")\n    def test_apply_parameters_handler_429_missing_header_uses_fallback(self, mock_post, mock_sleep, dashboard_manager):\n',
        '    @patch("requests.get", return_value=Mock(status_code=200, json=Mock(return_value={})))  # the /api/state read-back after the 200\n    @patch("frontend.dashboard_manager.time.sleep")\n    @patch("requests.post")\n    def test_apply_parameters_handler_429_missing_header_uses_fallback(self, mock_post, mock_sleep, _mock_get, dashboard_manager):\n',
        1,
    ),
    (
        "src/tests/unit/test_convergence_ui_regression.py",
        '            with patch("requests.post") as mock_post:\n                mock_post.return_value = Mock(status_code=200)\n',
        '            with patch("requests.post") as mock_post, patch("requests.get") as mock_get:\n                mock_post.return_value = Mock(status_code=200)\n                mock_get.return_value = Mock(status_code=200, json=Mock(return_value={}))  # the /api/state read-back after the 200\n',
        1,
    ),
    (
        "src/tests/unit/test_convergence_ui_regression.py",
        '        with patch("requests.post") as mock_post:\n            mock_post.return_value = Mock(status_code=200)\n',
        '        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:\n            mock_post.return_value = Mock(status_code=200)\n            mock_get.return_value = Mock(status_code=200, json=Mock(return_value={}))  # the /api/state read-back after the 200\n',
        3,
    ),
    (
        "src/tests/regression/test_availability_unknown_state.py",
        "@pytest.mark.regression\n@pytest.mark.unit\nclass TestTheGateSaysSoWithoutChangingWhatItGates:\n    def test_nothing_is_disabled_merely_because_availability_is_unknown(self, dm):\n",
        '@pytest.mark.regression\n@pytest.mark.unit\nclass TestTheGateSaysSoWithoutChangingWhatItGates:\n    @pytest.fixture(autouse=True)\n    def _the_generator_fetch_fails(self):\n        """``generators=None`` makes the gate fetch them, and these cases pin what that fetch\'s FAILURE produces.\n\n        Unmocked, the fetch went to whatever listened on 127.0.0.1:8050: refused on CI\'s runner (the unknown\n        state pinned here), answered by a live canopy on a developer machine (the unit-lane network guard).\n        """\n        with patch("frontend.dashboard_manager.requests.get", side_effect=OSError("connection refused")):\n            yield\n\n    def test_nothing_is_disabled_merely_because_availability_is_unknown(self, dm):\n',
        1,
    ),
    (
        "src/tests/regression/test_model_picker.py",
        'def _resp(*, ok, json_body=None, status_code=200, text=""):\n    resp = MagicMock(ok=ok, status_code=status_code, text=text)\n    resp.json.return_value = json_body or {}\n    return resp\n',
        'def _resp(*, ok, json_body=None, status_code=200, text=""):\n    resp = MagicMock(ok=ok, status_code=status_code, text=text)\n    resp.json.return_value = json_body or {}\n    return resp\n\n\ndef _generator_fetch_fails(manager, monkeypatch):\n    """Fail the generators fetch a gate call makes when it is passed none, as CI\'s empty runner does.\n\n    Unmocked, it went to whatever listened on 127.0.0.1:8050 (the unit-lane network guard), and the\n    module-scoped manager cached that answer for every later gate call: a live canopy\'s answer could\n    mark a dataset unavailable and grey it here.\n    """\n\n    def _refused(*_args, **_kwargs):\n        raise requests.ConnectionError("refused")\n\n    manager._generators_cache = None\n    monkeypatch.setattr(requests, "get", _refused)\n',
        1,
    ),
    (
        "src/tests/regression/test_model_picker.py",
        'def test_gate_dataset_options_handler_greys_and_clears_for_recurrence(manager):\n    options, value, _notice = manager._gate_dataset_options_handler("recurrence", "spirals")\n',
        'def test_gate_dataset_options_handler_greys_and_clears_for_recurrence(manager, monkeypatch):\n    _generator_fetch_fails(manager, monkeypatch)\n    options, value, _notice = manager._gate_dataset_options_handler("recurrence", "spirals")\n',
        1,
    ),
    (
        "src/tests/regression/test_model_picker.py",
        'def test_gate_dataset_options_handler_keeps_compatible_value(manager):\n    _options, value, _notice = manager._gate_dataset_options_handler("cascor", "spirals")\n',
        'def test_gate_dataset_options_handler_keeps_compatible_value(manager, monkeypatch):\n    _generator_fetch_fails(manager, monkeypatch)\n    _options, value, _notice = manager._gate_dataset_options_handler("cascor", "spirals")\n',
        1,
    ),
    (
        "src/tests/unit/backend/test_cascor_service_adapter_boundary.py",
        '    a = CascorServiceAdapter(service_url="http://localhost:8200")\n    a._client = mock_client\n    a.training_monitor = _ServiceTrainingMonitor(mock_client)\n    return a\n',
        '    a = CascorServiceAdapter(service_url="http://localhost:8200")\n    a._client = mock_client\n    a.training_monitor = _ServiceTrainingMonitor(mock_client)\n    # start_metrics_relay() also starts the control-stream supervisor, whose real CascorControlStream\n    # dials ws://localhost:8200 in the background (the unit-lane network guard). These tests drive the\n    # relay, not that socket; the real supervisor object (health, is_connected) is left in place.\n    a._control_supervisor.start = AsyncMock()\n    return a\n',
        1,
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--wt", required=True, type=Path)
    parser.add_argument("--revert", action="store_true")
    parser.add_argument("--only", help="apply only the edits to this repo-relative file")
    args = parser.parse_args()

    by_file: dict[str, list[tuple[str, str, int]]] = {}
    for path, old, new, count in EDITS:
        if args.only and path != args.only:
            continue
        by_file.setdefault(path, []).append((new, old, count) if args.revert else (old, new, count))
    for path, edits in by_file.items():
        target = args.wt / path
        text = target.read_text(encoding="utf-8")
        for old, new, count in edits:
            found = text.count(old)
            if found != count:
                print(f"[r17-fixes] REFUSED {path}: expected {count} occurrence(s), found {found}: {old.splitlines()[0][:90]!r}")
                return 1
            text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")
        print(f"[r17-fixes] {'reverted' if args.revert else 'applied'} {len(edits)} edit(s) in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
