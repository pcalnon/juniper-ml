#!/usr/bin/env python3
"""Round-38 cascor PR-A: exact-match edits to test_allow_truncated_datasets.py (session scratch).

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
TESTS = W / "src/tests/unit/api/test_allow_truncated_datasets.py"


def replace_once(path: Path, old: str, new: str, *, count: int = 1) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != count:
        sys.exit(f"FAIL {path.name}: expected exactly {count} match(es), found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r} x{count}")


# imports
replace_once(
    TESTS,
    "from cascor_constants.constants_api.constants_api_defaults import _PROJECT_API_ALLOW_TRUNCATED_DATASETS_DEFAULT\n",
    "from cascor_constants.constants_api.constants_api_defaults import _PROJECT_API_ALLOW_TRUNCATED_DATASETS_DEFAULT, _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT, _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER, _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST, _PROJECT_API_SHORTFALL_REFUSAL_TOKEN\n",
)

# TestRunFailureMessage: two new arms after the existing three
replace_once(
    TESTS,
    '        message = TrainingLifecycleManager._describe_dataset_fetch_failure(Exception("HTTP 422 allow_truncation"), allow_truncated=True)\n'
    '        assert message.startswith("juniper-data fetch failed:")\n'
    "\n",
    '        message = TrainingLifecycleManager._describe_dataset_fetch_failure(Exception("HTTP 422 allow_truncation"), allow_truncated=True)\n'
    '        assert message.startswith("juniper-data fetch failed:")\n'
    "\n"
    "    def test_the_refusal_opens_with_a_machine_readable_token(self) -> None:\n"
    '        """A consumer (canopy\'s three-way prompt) must recognise the class without matching prose.\n'
    "\n"
    "        The token is the contract; the sentence after it is free to change. An\n"
    "        ordinary outage must NOT carry it, or the prompt fires on a dead service.\n"
    '        """\n'
    '        refusal = TrainingLifecycleManager._describe_dataset_fetch_failure(Exception("HTTP 422 allow_truncation"), allow_truncated=False)\n'
    '        assert refusal.startswith(_PROJECT_API_SHORTFALL_REFUSAL_TOKEN + " ")\n'
    '        outage = TrainingLifecycleManager._describe_dataset_fetch_failure(Exception("connection refused"), allow_truncated=False)\n'
    "        assert _PROJECT_API_SHORTFALL_REFUSAL_TOKEN not in outage\n"
    "\n"
    "    def test_a_caller_that_refused_is_told_to_resend_not_to_flip_the_setting(self) -> None:\n"
    '        """An explicit allow_truncation=false wins over the service setting (cascor#624).\n'
    "\n"
    "        Pointing that caller at --allow-truncated-datasets would send them to a knob\n"
    "        that cannot change the outcome. The remedy is the request's own two\n"
    "        parameters, and the message must say which stance was actually taken.\n"
    '        """\n'
    '        message = TrainingLifecycleManager._describe_dataset_fetch_failure(Exception("HTTP 422 allow_truncation"), allow_truncated=False, caller_refused=True)\n'
    "        assert message.startswith(_PROJECT_API_SHORTFALL_REFUSAL_TOKEN)\n"
    '        assert "explicitly refused" in message\n'
    '        assert "allow_truncation=true" in message\n'
    '        assert "incomplete_rows=accept" in message and "incomplete_rows=drop" in message\n'
    '        assert "--allow-truncated-datasets" not in message\n'
    "\n",
)

# TestShortfallLogging: kwarg rename (four call sites) + a producer arm
replace_once(
    TESTS,
    "            self._manager()._log_dataset_shortfall({}, allow_truncated=False)\n",
    "            self._manager()._log_dataset_shortfall({}, acceptance_source=None)\n",
)
replace_once(
    TESTS,
    "            self._manager()._log_dataset_shortfall(meta, allow_truncated=True)\n",
    "            self._manager()._log_dataset_shortfall(meta, acceptance_source=_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT)\n",
    count=3,
)
replace_once(
    TESTS,
    '        assert "were dropped" in caplog.text\n'
    "\n"
    "\n"
    "class TestCallerStanceIsNotOverridden:\n",
    '        assert "were dropped" in caplog.text\n'
    "\n"
    "    def test_the_log_names_who_accepted_and_the_producer_when_nobody_here_did(self, caplog: pytest.LogCaptureFixture) -> None:\n"
    '        """juniper-data ORs the request with its own deployment opt-in; a client cannot opt out.\n'
    "\n"
    "        A partial dataset that arrives with no opt-in sent from this side was accepted\n"
    "        by the PRODUCER, and the log must say so rather than restate a setting that\n"
    '        was off -- the old line read "accepted it via allow_truncated_datasets=False".\n'
    '        """\n'
    '        meta = {"truncation": {"unit": "symbols", "cap": 14, "requested": 503, "imported": 14}}\n'
    "        with caplog.at_level(logging.WARNING):\n"
    "            self._manager()._log_dataset_shortfall(meta, acceptance_source=None)\n"
    '        assert "DATASET SHORTFALL" in caplog.text\n'
    '        assert "producer\'s own deployment default" in caplog.text\n'
    '        assert "allow_truncated_datasets=False" not in caplog.text\n'
    "\n"
    "        caplog.clear()\n"
    "        with caplog.at_level(logging.WARNING):\n"
    "            self._manager()._log_dataset_shortfall(meta, acceptance_source=_PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST)\n"
    '        assert "dataset request itself" in caplog.text\n'
    "\n"
    "\n"
    "class TestCallerStanceIsNotOverridden:\n",
)

# TestCallerStanceIsNotOverridden: the B1-finding-2 regression, after the incomplete_rows arm
replace_once(
    TESTS,
    '        params = self._params_on_the_wire({"allow_truncation": True, "incomplete_rows": "drop"}, deployment_flag=False)\n'
    '        assert params["incomplete_rows"] == "drop"\n'
    "\n",
    '        params = self._params_on_the_wire({"allow_truncation": True, "incomplete_rows": "drop"}, deployment_flag=False)\n'
    '        assert params["incomplete_rows"] == "drop"\n'
    "\n"
    "    def test_a_refusal_after_an_explicit_false_still_names_a_remedy(self) -> None:\n"
    '        """The failure message must key off the WIRE stance, not the setting.\n'
    "\n"
    "        Flag ON, caller sends allow_truncation=false: cascor withholds its default\n"
    "        (correct), the producer refuses, and the message used to consult the\n"
    '        SETTING -- so it returned the bare "fetch failed" line, with no remedy, in\n'
    "        exactly the case the remedy exists for. Found by round-37 validation.\n"
    '        """\n'
    "        sent: dict = {}\n"
    "\n"
    "        class _RefusingClient:\n"
    "            def __init__(self, **_kwargs: object) -> None:\n"
    "                pass\n"
    "\n"
    "            def create_dataset(self, *, generator: str, params: dict, persist: bool) -> dict:\n"
    '                sent["params"] = dict(params)\n'
    '                raise RuntimeError("HTTP 422: Shares outstanding could not be resolved for part of the requested universe. Re-submit with allow_truncation=true")\n'
    "\n"
    '        settings = SimpleNamespace(juniper_data_url="http://juniper-data:8100", allow_truncated_datasets=True)\n'
    "        with (\n"
    '            patch("juniper_data_client.JuniperDataClient", _RefusingClient),\n'
    '            patch("api.settings.Settings", lambda: settings),\n'
    '            patch("api.secrets.get_secret", lambda _name: "key"),\n'
    "            pytest.raises(RuntimeError) as excinfo,\n"
    "        ):\n"
    '            self._manager()._reload_dataset(dataset_type="equities", params={"allow_truncation": False})\n'
    '        assert sent["params"]["allow_truncation"] is False, "the caller\'s refusal must reach the producer unchanged"\n'
    "        message = str(excinfo.value)\n"
    "        assert message.startswith(_PROJECT_API_SHORTFALL_REFUSAL_TOKEN)\n"
    '        assert "explicitly refused" in message and "allow_truncation=true" in message\n'
    "\n",
)

# TestShortfallIsPollable: kwarg rename on the three existing builder calls
replace_once(
    TESTS,
    '        assert TrainingLifecycleManager._build_dataset_shortfall({}, dataset_id="d1", allow_truncated=False) is None\n',
    '        assert TrainingLifecycleManager._build_dataset_shortfall({}, dataset_id="d1", acceptance_source=None) is None\n',
)
replace_once(
    TESTS,
    '        built = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id="abc123", allow_truncated=True)\n',
    '        built = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id="abc123", acceptance_source=_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT)\n',
)
replace_once(
    TESTS,
    '        built = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id="d2", allow_truncated=True)\n',
    '        built = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id="d2", acceptance_source=_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT)\n',
)

# TestShortfallIsPollable: the acceptance-source arms, before test_get_status_carries_it
replace_once(
    TESTS,
    "    def test_get_status_carries_it(self) -> None:\n",
    '    _PARTIAL_META = {"truncation": {"unit": "symbols", "cap": 14, "requested": 503, "imported": 14}}\n'
    "\n"
    "    @staticmethod\n"
    "    def _annotation_after_reload(caller_params: dict, *, deployment_flag: bool, meta: dict) -> dict:\n"
    '        """Run ``_reload_dataset`` up to the point the annotation is set, then stop.\n'
    "\n"
    "        The fake client delivers ``meta`` and a placeholder artifact; tensor\n"
    "        conversion is patched to raise, because the annotation is built BEFORE it\n"
    "        and everything after it is tensor plumbing this test has no opinion about.\n"
    '        """\n'
    "\n"
    "        class _PartialClient:\n"
    "            def __init__(self, **_kwargs: object) -> None:\n"
    "                pass\n"
    "\n"
    "            def create_dataset(self, *, generator: str, params: dict, persist: bool) -> dict:\n"
    '                return {"dataset_id": "partial-1", "meta": meta}\n'
    "\n"
    "            def download_artifact_npz(self, dataset_id: str) -> dict:\n"
    "                return {}\n"
    "\n"
    "        class _StopAfterAnnotation(Exception):\n"
    "            pass\n"
    "\n"
    "        manager = TrainingLifecycleManager.__new__(TrainingLifecycleManager)\n"
    '        manager.logger = logging.getLogger("test.annotation")\n'
    "        manager._dataset_shortfall = None\n"
    '        settings = SimpleNamespace(juniper_data_url="http://juniper-data:8100", allow_truncated_datasets=deployment_flag)\n'
    "        with (\n"
    '            patch("juniper_data_client.JuniperDataClient", _PartialClient),\n'
    '            patch("api.settings.Settings", lambda: settings),\n'
    '            patch("api.secrets.get_secret", lambda _name: "key"),\n'
    '            patch.object(TrainingLifecycleManager, "_artifact_to_tensors", side_effect=_StopAfterAnnotation("stop")),\n'
    "            pytest.raises(_StopAfterAnnotation),\n"
    "        ):\n"
    '            manager._reload_dataset(dataset_type="equities", params=dict(caller_params))\n'
    "        assert manager._dataset_shortfall is not None\n"
    "        return manager._dataset_shortfall\n"
    "\n"
    "    def test_a_caller_opt_in_is_recorded_as_the_request(self) -> None:\n"
    '        """Options 1 and 2 of the partial-data contract arrive as request params, with the service flag off."""\n'
    '        built = self._annotation_after_reload({"allow_truncation": True}, deployment_flag=False, meta=self._PARTIAL_META)\n'
    '        assert built["accepted_by_this_run"] is True\n'
    '        assert built["acceptance_source"] == _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST\n'
    "        # The original field means exactly what its name says: the SETTING did not supply this opt-in.\n"
    '        assert built["accepted_via_allow_truncated_datasets"] is False\n'
    '        assert "dataset request itself" in built["summary"]\n'
    "\n"
    "    def test_the_service_setting_is_recorded_as_the_deployment(self) -> None:\n"
    '        built = self._annotation_after_reload({}, deployment_flag=True, meta=self._PARTIAL_META)\n'
    '        assert built["accepted_by_this_run"] is True\n'
    '        assert built["acceptance_source"] == _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT\n'
    '        assert built["accepted_via_allow_truncated_datasets"] is True\n'
    '        assert "allow_truncated_datasets setting" in built["summary"]\n'
    "\n"
    "    def test_a_partial_dataset_nobody_here_asked_for_names_the_producer(self) -> None:\n"
    '        """THE REGRESSION (round-37 handoff §0.13).\n'
    "\n"
    "        Flag off, caller silent, and the producer delivered a partial dataset anyway\n"
    "        -- its own deployment opt-in, which a client cannot refuse. The annotation\n"
    "        used to read ``accepted_via_allow_truncated_datasets: false``: the truth\n"
    "        about the setting, and a denial of the acceptance it was annotating. It now\n"
    "        says who accepted, and that this run did not.\n"
    '        """\n'
    '        built = self._annotation_after_reload({}, deployment_flag=False, meta=self._PARTIAL_META)\n'
    '        assert built["accepted_by_this_run"] is False\n'
    '        assert built["acceptance_source"] == _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER\n'
    '        assert built["accepted_via_allow_truncated_datasets"] is False\n'
    '        assert "producer" in built["summary"]\n'
    "\n"
    "    def test_a_string_stance_is_read_as_a_bool(self) -> None:\n"
    '        """The staged params cross a JSON boundary; ``bool("false")`` is ``True``."""\n'
    '        assert TrainingLifecycleManager._as_bool_stance("false") is False\n'
    '        assert TrainingLifecycleManager._as_bool_stance("True") is True\n'
    "        assert TrainingLifecycleManager._as_bool_stance(False) is False\n"
    "        assert TrainingLifecycleManager._as_bool_stance(None) is None\n"
    '        assert TrainingLifecycleManager._as_bool_stance("") is None\n'
    "\n"
    "    def test_get_status_carries_it(self) -> None:\n",
)
print("ALL TEST EDITS APPLIED")
