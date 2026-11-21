#!/usr/bin/env python3
"""Round-38 cascor PR-A: exact-match edits to manager.py + constants (session scratch).

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
MANAGER = W / "src/api/lifecycle/manager.py"
DEFAULTS = W / "src/cascor_constants/constants_api/constants_api_defaults.py"
INIT = W / "src/cascor_constants/constants_api/__init__.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL {path.name}: expected exactly 1 match, found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r}")


# ---------------------------------------------------------------- constants
replace_once(
    DEFAULTS,
    '_PROJECT_API_TRUNCATABLE_GENERATORS: frozenset = frozenset({"equities", "equities_seq", "csv_import"})\n',
    '_PROJECT_API_TRUNCATABLE_GENERATORS: frozenset = frozenset({"equities", "equities_seq", "csv_import"})\n'
    "\n"
    "# Machine-readable prefix on the run-failure message raised when juniper-data\n"
    "# refused (422) a dataset it could not produce in full and no opt-in was on the\n"
    "# wire. The prose after it is for an operator; the prefix is for a CONSUMER\n"
    "# (canopy's three-way partial-data prompt) that has to recognise the refusal\n"
    "# class without pattern-matching English. It rides inside the 409 ``detail``\n"
    "# string because that is the one channel every transport carries -- the WS\n"
    "# control path forwards ``error`` as a bare string.\n"
    '_PROJECT_API_SHORTFALL_REFUSAL_TOKEN: str = "[dataset_shortfall_refused]"\n'
    "\n"
    "# Who put the opt-in on the wire when a partial dataset was accepted. Recorded on\n"
    "# the ``dataset_shortfall`` annotation as ``acceptance_source`` so the annotation\n"
    "# says WHO accepted, not merely that something was. The third value exists\n"
    "# because juniper-data ORs the request with ITS OWN deployment opt-in and a\n"
    "# client cannot opt out of it: a partial dataset can arrive that nobody on this\n"
    "# side asked for, and the annotation must not then claim this run refused it.\n"
    '_PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST: str = "request_params"\n'
    '_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT: str = "allow_truncated_datasets"\n'
    '_PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER: str = "producer"\n',
)

replace_once(
    INIT,
    "    _PROJECT_API_SERVICE_TERMINATION_TIMEOUT,\n    _PROJECT_API_TLS_MIN_VERSION_DEFAULT,\n",
    "    _PROJECT_API_SERVICE_TERMINATION_TIMEOUT,\n"
    "    _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT,\n"
    "    _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER,\n"
    "    _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST,\n"
    "    _PROJECT_API_SHORTFALL_REFUSAL_TOKEN,\n"
    "    _PROJECT_API_TLS_MIN_VERSION_DEFAULT,\n",
)
replace_once(
    INIT,
    '    "_PROJECT_API_SERVICE_TERMINATION_TIMEOUT",\n    "_PROJECT_API_TLS_MIN_VERSION_DEFAULT",\n',
    '    "_PROJECT_API_SERVICE_TERMINATION_TIMEOUT",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER",\n'
    '    "_PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST",\n'
    '    "_PROJECT_API_SHORTFALL_REFUSAL_TOKEN",\n'
    '    "_PROJECT_API_TLS_MIN_VERSION_DEFAULT",\n',
)

# ---------------------------------------------------------------- manager: module import
replace_once(
    MANAGER,
    "from cascor_constants.constants_api import _PROJECT_API_DRAIN_THREAD_JOIN_TIMEOUT, _PROJECT_API_LIFECYCLE_DEFAULT_CANDIDATE_PATIENCE, _PROJECT_API_NETWORK_INPUT_SIZE_DEFAULT, _PROJECT_API_NETWORK_OUTPUT_SIZE_DEFAULT, _PROJECT_API_PROGRESS_QUEUE_GET_TIMEOUT, _PROJECT_API_PROGRESS_QUEUE_WAIT_TIMEOUT\n",
    "from cascor_constants.constants_api import _PROJECT_API_DRAIN_THREAD_JOIN_TIMEOUT, _PROJECT_API_LIFECYCLE_DEFAULT_CANDIDATE_PATIENCE, _PROJECT_API_NETWORK_INPUT_SIZE_DEFAULT, _PROJECT_API_NETWORK_OUTPUT_SIZE_DEFAULT, _PROJECT_API_PROGRESS_QUEUE_GET_TIMEOUT, _PROJECT_API_PROGRESS_QUEUE_WAIT_TIMEOUT, _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT, _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER, _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST, _PROJECT_API_SHORTFALL_REFUSAL_TOKEN\n",
)

# ---------------------------------------------------------------- manager: _describe_dataset_fetch_failure
replace_once(
    MANAGER,
    "    def _describe_dataset_fetch_failure(exc: Exception, *, allow_truncated: bool) -> str:\n",
    "    def _describe_dataset_fetch_failure(exc: Exception, *, allow_truncated: bool, caller_refused: bool = False) -> str:\n",
)
replace_once(
    MANAGER,
    "        and both remedies; it is quoted rather than replaced. What is added is\n"
    "        the part juniper-data cannot know: which knob to turn on THIS side.\n"
    '        """\n'
    "        detail = str(exc)\n"
    '        looks_like_shortfall = "422" in detail or "allow_truncation" in detail or "incomplete_rows" in detail\n'
    "        if not looks_like_shortfall or allow_truncated:\n"
    '            return f"juniper-data fetch failed: {detail}"\n'
    '        return f"juniper-data could not produce the requested dataset in full, and this run did not accept a partial one, so the run is FAILING rather than training on data nobody chose. " f"Producer detail: {detail} " f"To accept it, re-run with --allow-truncated-datasets (or set JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true, or allow_truncated_datasets: true in the experiment YAML service: block). " f"The resulting dataset is permanently annotated as partial, and so is every metric derived from it."\n',
    "        and both remedies; it is quoted rather than replaced. What is added is\n"
    "        the part juniper-data cannot know: which knob to turn on THIS side.\n"
    "\n"
    "        ``allow_truncated`` is the stance that went ON THE WIRE -- whether an\n"
    "        opt-in was sent, by this service's setting or by the caller's own params\n"
    "        -- not the setting alone. The two differ in exactly the case the remedy\n"
    "        exists for: a caller-supplied ``allow_truncation: false`` on a deployment\n"
    "        with the flag on is honoured (cascor#624), the producer refuses, and\n"
    "        keying this off the setting produced the bare ``fetch failed`` line with\n"
    "        no remedy at all. ``caller_refused`` distinguishes the two no-opt-in cases\n"
    "        because their remedies differ: a caller that sent ``false`` re-sends\n"
    "        ``true``; a silent caller turns the knob on this side.\n"
    "\n"
    "        The message opens with a machine-readable token so a consumer can\n"
    "        recognise the refusal class without matching prose; canopy's three-way\n"
    "        partial-data prompt keys on it.\n"
    '        """\n'
    "        detail = str(exc)\n"
    '        looks_like_shortfall = "422" in detail or "allow_truncation" in detail or "incomplete_rows" in detail\n'
    "        if not looks_like_shortfall or allow_truncated:\n"
    '            return f"juniper-data fetch failed: {detail}"\n'
    "        if caller_refused:\n"
    '            stance = "and this run explicitly refused a partial one (the dataset request sent allow_truncation=false)"\n'
    '            remedy = "To accept it, re-send the dataset request with allow_truncation=true, plus incomplete_rows=accept to keep the affected rows or incomplete_rows=drop to remove them."\n'
    "        else:\n"
    '            stance = "and this run did not accept a partial one"\n'
    '            remedy = "To accept it, re-run with --allow-truncated-datasets (or set JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true, or allow_truncated_datasets: true in the experiment YAML service: block), or send allow_truncation=true on the dataset request itself."\n'
    "        return (\n"
    '            f"{_PROJECT_API_SHORTFALL_REFUSAL_TOKEN} juniper-data could not produce the requested dataset in full, {stance}, so the run is FAILING rather than training on data nobody chose. "\n'
    '            f"Producer detail: {detail} "\n'
    '            f"{remedy} "\n'
    '            "The resulting dataset is permanently annotated as partial, and so is every metric derived from it."\n'
    "        )\n",
)

# ---------------------------------------------------------------- manager: _build_dataset_shortfall
replace_once(
    MANAGER,
    "    def _build_dataset_shortfall(meta: Dict[str, Any], *, dataset_id: Optional[str], allow_truncated: bool) -> Optional[Dict[str, Any]]:\n",
    "    def _build_dataset_shortfall(meta: Dict[str, Any], *, dataset_id: Optional[str], acceptance_source: Optional[str]) -> Optional[Dict[str, Any]]:\n",
)
replace_once(
    MANAGER,
    "        re-deriving it from the parts -- two formatters over one structure drift,\n"
    "        and the drift shows up as a UI that disagrees with the log.\n"
    '        """\n',
    "        re-deriving it from the parts -- two formatters over one structure drift,\n"
    "        and the drift shows up as a UI that disagrees with the log.\n"
    "\n"
    "        ``acceptance_source`` is who put the opt-in on the wire -- the caller's\n"
    "        own params, or this service's ``allow_truncated_datasets`` setting -- or\n"
    "        ``None`` when nothing was sent. A partial dataset can still arrive in that\n"
    "        last case: juniper-data ORs the request with ITS deployment's opt-in and\n"
    "        a client cannot opt out of it. The annotation then records the producer\n"
    "        as the authority, rather than claiming this run refused the data it is\n"
    "        training on.\n"
    '        """\n',
)
replace_once(
    MANAGER,
    "        return {\n"
    '            "dataset_id": dataset_id,\n'
    "            # The stance THIS run took, recorded next to its consequence so a\n"
    "            # reader does not have to correlate with a settings dump to learn\n"
    "            # whether the shortfall was chosen or merely tolerated.\n"
    '            "accepted_via_allow_truncated_datasets": allow_truncated,\n'
    '            "truncation": truncation,\n'
    '            "data_quality": quality,\n'
    '            "summary": "; ".join(parts),\n'
    "        }\n",
    "        source = acceptance_source or _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER\n"
    "        parts.append(TrainingLifecycleManager._describe_acceptance(source))\n"
    "\n"
    "        return {\n"
    '            "dataset_id": dataset_id,\n'
    "            # WHO accepted the shortfall, recorded next to its consequence so a\n"
    "            # reader does not have to correlate with a settings dump to learn\n"
    "            # whether it was chosen or merely tolerated. ``accepted_by_this_run``\n"
    '            # answers the question a reader usually means ("did we ask for\n'
    "            # this?\"); ``acceptance_source`` is that answer's provenance; and the\n"
    "            # original field is kept for its consumers, now meaning exactly what\n"
    "            # its name says -- true only when THIS SERVICE'S setting supplied the\n"
    "            # opt-in. It used to be the setting's raw value, which read ``false``\n"
    "            # on a run that accepted via the caller's params and on one the\n"
    "            # producer accepted on its own authority: an annotation denying the\n"
    "            # acceptance it was annotating.\n"
    '            "accepted_by_this_run": source != _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER,\n'
    '            "acceptance_source": source,\n'
    '            "accepted_via_allow_truncated_datasets": source == _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT,\n'
    '            "truncation": truncation,\n'
    '            "data_quality": quality,\n'
    '            "summary": "; ".join(parts),\n'
    "        }\n"
    "\n"
    "    @staticmethod\n"
    "    def _describe_acceptance(source: str) -> str:\n"
    '        """One clause saying who let the partial dataset through -- for the log and the summary."""\n'
    "        return {\n"
    '            _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST: "accepted by the dataset request itself (allow_truncation=true)",\n'
    "            _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT: \"accepted by this service's allow_truncated_datasets setting\",\n"
    "            _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER: \"accepted by the producer's own deployment default (this run sent no opt-in, and a client cannot opt out of the producer's choice)\",\n"
    '        }.get(source, f"accepted via {source}")\n'
    "\n"
    "    @staticmethod\n"
    "    def _as_bool_stance(value: Any) -> Optional[bool]:\n"
    '        """Read a caller\'s ``allow_truncation`` as a tri-state: absent, refused, or opted in.\n'
    "\n"
    "        The staged params are a free-form dict that has crossed at least one JSON\n"
    "        boundary and possibly a YAML one, so the value may arrive as a string.\n"
    "        ``bool(\"false\")`` is ``True`` -- truthiness is not an \"is it set\" test --\n"
    "        so the string forms are read explicitly. Anything unrecognised falls back\n"
    "        to truthiness, which is what the producer's own coercion will make of it.\n"
    '        """\n'
    "        if value is None:\n"
    "            return None\n"
    "        if isinstance(value, bool):\n"
    "            return value\n"
    "        if isinstance(value, str):\n"
    "            lowered = value.strip().lower()\n"
    '            if lowered == "":\n'
    "                return None\n"
    '            if lowered in {"true", "1", "yes", "on"}:\n'
    "                return True\n"
    '            if lowered in {"false", "0", "no", "off"}:\n'
    "                return False\n"
    "        return bool(value)\n",
)

# ---------------------------------------------------------------- manager: _log_dataset_shortfall
replace_once(
    MANAGER,
    "    def _log_dataset_shortfall(self, meta: Dict[str, Any], *, allow_truncated: bool) -> None:\n",
    "    def _log_dataset_shortfall(self, meta: Dict[str, Any], *, acceptance_source: Optional[str]) -> None:\n",
)
replace_once(
    MANAGER,
    "        if not truncation and not quality:\n"
    "            return\n"
    "\n"
    "        if truncation:\n"
    "            self.logger.warning(\n"
    '                "DATASET IS PARTIAL: %s of %s %s were imported (cap %s). This run accepted it via allow_truncated_datasets=%s; the artifact carries a permanent annotation, and this run reports it as `dataset_shortfall` on /v1/training/status.",\n'
    '                truncation.get("imported"),\n'
    '                truncation.get("requested"),\n'
    '                truncation.get("unit"),\n'
    '                truncation.get("cap"),\n'
    "                allow_truncated,\n"
    "            )\n",
    "        if not truncation and not quality:\n"
    "            return\n"
    "\n"
    "        # WHO let it through comes first, once, because it is the same answer for\n"
    "        # both kinds of shortfall and it is the line an operator reads back to\n"
    "        # decide whether this run's numbers were chosen or merely tolerated.\n"
    "        source = acceptance_source or _PROJECT_API_SHORTFALL_ACCEPTED_BY_PRODUCER\n"
    '        self.logger.warning("DATASET SHORTFALL: this run is training on a partial dataset, %s.", self._describe_acceptance(source))\n'
    "        if truncation:\n"
    "            self.logger.warning(\n"
    '                "DATASET IS PARTIAL: %s of %s %s were imported (cap %s); the artifact carries a permanent annotation, and this run reports it as `dataset_shortfall` on /v1/training/status.",\n'
    '                truncation.get("imported"),\n'
    '                truncation.get("requested"),\n'
    '                truncation.get("unit"),\n'
    '                truncation.get("cap"),\n'
    "            )\n",
)

# ---------------------------------------------------------------- manager: _reload_dataset
replace_once(
    MANAGER,
    "        allow_truncated = bool(Settings().allow_truncated_datasets)\n"
    '        if allow_truncated and generator in _PROJECT_API_TRUNCATABLE_GENERATORS and "allow_truncation" not in jd_params:\n',
    '        caller_stance = self._as_bool_stance(jd_params.get("allow_truncation"))\n'
    "        allow_truncated = bool(Settings().allow_truncated_datasets)\n"
    '        if allow_truncated and generator in _PROJECT_API_TRUNCATABLE_GENERATORS and "allow_truncation" not in jd_params:\n',
)
replace_once(
    MANAGER,
    '            jd_params = {**jd_params, "allow_truncation": True}\n'
    "\n"
    "        try:\n"
    "            result = client.create_dataset(generator=generator, params=jd_params, persist=True)\n",
    '            jd_params = {**jd_params, "allow_truncation": True}\n'
    "\n"
    "        # What actually went on the wire, and who put it there. The setting alone\n"
    "        # is the wrong witness on both sides of this: a caller-supplied value wins\n"
    "        # over it (above), and the producer applies its OWN deployment opt-in on\n"
    '        # top of whatever arrives. So "did this run accept a partial dataset" is\n'
    '        # answered by the request that was sent, and "who accepted it" needs a\n'
    "        # third value for the case where nobody on this side did.\n"
    '        requested_truncation = bool(self._as_bool_stance(jd_params.get("allow_truncation")))\n'
    "        if caller_stance is not None:\n"
    "            acceptance_source = _PROJECT_API_SHORTFALL_ACCEPTED_BY_REQUEST if caller_stance else None\n"
    "        else:\n"
    "            acceptance_source = _PROJECT_API_SHORTFALL_ACCEPTED_BY_DEPLOYMENT if requested_truncation else None\n"
    "\n"
    "        try:\n"
    "            result = client.create_dataset(generator=generator, params=jd_params, persist=True)\n",
)
replace_once(
    MANAGER,
    "            raise RuntimeError(self._describe_dataset_fetch_failure(exc, allow_truncated=allow_truncated)) from exc\n",
    "            raise RuntimeError(self._describe_dataset_fetch_failure(exc, allow_truncated=requested_truncation, caller_refused=caller_stance is False)) from exc\n",
)
replace_once(
    MANAGER,
    "        self._log_dataset_shortfall(meta, allow_truncated=allow_truncated)\n"
    "        # ...AND ON THE RUN, not only in the log. A log line is not a surface: it\n"
    "        # cannot be polled, it does not reach the WS stream, and canopy cannot\n"
    "        # render it. Without this, a run that accepted a partial dataset is\n"
    "        # indistinguishable over the API from one that got everything it asked\n"
    "        # for -- so the score it reports carries no mark of the data it was\n"
    "        # computed on. ``get_status()`` reads this, which puts it on\n"
    "        # ``/v1/training/status`` and the WS training stream at once.\n",
    "        self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n"
    "        # ...AND ON THE RUN, not only in the log. A log line is not a surface: it\n"
    "        # cannot be polled, it does not reach the WS stream, and canopy cannot\n"
    "        # render it. Without this, a run that accepted a partial dataset is\n"
    "        # indistinguishable over the API from one that got everything it asked\n"
    "        # for -- so the score it reports carries no mark of the data it was\n"
    "        # computed on. ``get_status()`` reads this, which puts it on\n"
    "        # ``/v1/training/status``. It does NOT ride the WS training stream: the\n"
    "        # stream's only reader of ``get_status()`` is the one-shot\n"
    "        # ``initial_status`` frame sent at connect (``training_stream.py``), and\n"
    "        # the broadcast set has no status frame -- a client already connected\n"
    "        # when this is set never sees it over WS. A live consumer polls the\n"
    "        # status route; canopy does, at 1 Hz.\n",
)
replace_once(
    MANAGER,
    "        self._dataset_shortfall = self._build_dataset_shortfall(meta, dataset_id=dataset_id, allow_truncated=allow_truncated)\n",
    "        self._dataset_shortfall = self._build_dataset_shortfall(meta, dataset_id=dataset_id, acceptance_source=acceptance_source)\n",
)
print("ALL EDITS APPLIED")
