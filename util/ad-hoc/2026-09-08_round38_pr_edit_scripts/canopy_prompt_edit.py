#!/usr/bin/env python3
"""Round-38 canopy three-way prompt: exact-match edits (session scratch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#605 (worktree juniper-canopy--feature--partial-data-three-way-prompt--20260908-0729--eb05021d);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--feature--partial-data-three-way-prompt--20260908-0729--eb05021d")
PROTOCOL = W / "src/backend/protocol.py"
SERVICE = W / "src/backend/service_backend.py"
SCHEMA = W / "src/dataset_schema.py"
DM = W / "src/frontend/dashboard_manager.py"
MANIFEST = W / "src/tests/ui_contract/control_manifest.py"
CHANGELOG = W / "CHANGELOG.md"
T_SERVICE = W / "src/tests/unit/test_service_backend.py"
T_SCHEMA = W / "src/tests/unit/test_dataset_schema.py"
T_JS = W / "src/tests/unit/test_phase_d_button_clientside.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL {path.name}: expected exactly 1 match, found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r}")


# ---------------------------------------------------------------- protocol.py
replace_once(
    PROTOCOL,
    "    # None when the connected cascor predates the field.\n"
    "    completion_reason: str\n",
    "    # None when the connected cascor predates the field.\n"
    "    completion_reason: str\n"
    "    # Partial-data contract: cascor's ``dataset_shortfall`` annotation carried through\n"
    "    # from /v1/training/status -- ``None`` when the producer delivered in full (the\n"
    "    # overwhelming majority) or when the connected cascor predates the field. Non-null\n"
    "    # means THIS run is training on partial data; the dict carries ``dataset_id``,\n"
    "    # ``accepted_by_this_run``, ``acceptance_source``, the producer's ``truncation`` and\n"
    "    # ``data_quality`` descriptors, and a one-sentence ``summary`` for rendering.\n"
    "    dataset_shortfall: Optional[Dict[str, Any]]\n",
)

# ---------------------------------------------------------------- service_backend.py
replace_once(
    SERVICE,
    '                "pending_dataset": raw.get("pending_dataset"),\n'
    "                # cascor #320 (Issue #3 follow-up): which grow_network exit fired\n",
    '                "pending_dataset": raw.get("pending_dataset"),\n'
    "                # Partial-data contract (cascor#624 + #633): the ``dataset_shortfall``\n"
    "                # annotation -- ``None`` when the dataset was delivered in full. Carried\n"
    "                # through unchanged; this whitelist is the ONLY place it could be lost\n"
    "                # between cascor's status route and the dashboard (canopy already polls\n"
    "                # that route at 1 Hz through the status cache -- no new poller needed).\n"
    '                "dataset_shortfall": raw.get("dataset_shortfall"),\n'
    "                # cascor #320 (Issue #3 follow-up): which grow_network exit fired\n",
)

# ---------------------------------------------------------------- dataset_schema.py
replace_once(
    SCHEMA,
    '        "use_cache",\n'
    "    }\n"
    ")\n"
    "\n"
    "# canopy dataset-type value -> juniper-data generator name.",
    '        "use_cache",\n'
    "    }\n"
    ")\n"
    "\n"
    "# The partial-data contract's two DECISION fields. juniper-data's ``equities`` /\n"
    "# ``equities_seq`` / ``csv_import`` schemas carry ``allow_truncation`` (the gate: accept a\n"
    "# dataset the producer cannot deliver in full) and ``incomplete_rows`` (accept or drop the\n"
    "# rows it could not resolve, once the gate is open). Rendered as ordinary sidebar inputs\n"
    "# they broke the contract twice over: an unticked checkbox sent an EXPLICIT\n"
    "# ``allow_truncation: false`` on every apply -- which cascor#624 honours over its own\n"
    "# deployment default, so the operator's silence became a refusal and the failure message\n"
    "# lost its remedy -- and a ticked one pre-answered a question the contract says must be\n"
    "# put to the operator when the shortfall actually happens. The dashboard's three-way\n"
    "# prompt owns both fields: the form sends NEITHER, so a default apply expresses option 3\n"
    "# (fail) and the prompt supplies options 1 and 2 (accept / drop) on the re-stage.\n"
    'PARTIAL_DATA_POLICY_FIELDS: frozenset[str] = frozenset({"allow_truncation", "incomplete_rows"})\n'
    "\n"
    "# Everything the schema-driven form must neither render nor forward.\n"
    "FORM_EXCLUDED_FIELDS: frozenset[str] = INFRASTRUCTURE_FIELDS | PARTIAL_DATA_POLICY_FIELDS\n"
    "\n"
    "# canopy dataset-type value -> juniper-data generator name.",
)
replace_once(
    SCHEMA,
    "def parse_schema_fields(schema: Mapping[str, Any] | None, *, exclude: Iterable[str] = INFRASTRUCTURE_FIELDS) -> list[GeneratorField]:\n"
    '    """Return the ordered renderable content fields of a generator ``schema``.\n'
    "\n"
    "    ``schema`` is a Pydantic ``model_json_schema()`` dict (its ``properties`` map). Infrastructure\n"
    "    fields (``exclude`` — split/seed/cache by default) and non-renderable (array/object/null-only)\n",
    "def parse_schema_fields(schema: Mapping[str, Any] | None, *, exclude: Iterable[str] = FORM_EXCLUDED_FIELDS) -> list[GeneratorField]:\n"
    '    """Return the ordered renderable content fields of a generator ``schema``.\n'
    "\n"
    "    ``schema`` is a Pydantic ``model_json_schema()`` dict (its ``properties`` map). Excluded\n"
    "    fields (``exclude`` — the split/seed/cache plumbing plus the partial-data policy fields the\n"
    "    three-way prompt owns, by default) and non-renderable (array/object/null-only)\n",
)

# ---------------------------------------------------------------- dashboard_manager.py: JS
replace_once(
    DM,
    "                    data: { last: triggerId, ts: Date.now() / 1000.0, success: false, command: command, detail: String(detail || '').slice(0, 300) }\n",
    "                    // detail is the alert's 300-char slice; detail_full keeps the producer's own\n"
    "                    // sentence (which symbols, how many rows) for the partial-data prompt.\n"
    "                    data: { last: triggerId, ts: Date.now() / 1000.0, success: false, command: command, detail: String(detail || '').slice(0, 300), detail_full: String(detail || '').slice(0, 4000) }\n",
)

# ---------------------------------------------------------------- dashboard_manager.py: constants
replace_once(
    DM,
    "def selection_axis_unset(value) -> bool:\n",
    "# Partial-data contract -- how canopy recognises a cascor Start refusal caused by\n"
    "# juniper-data being unable to produce the staged dataset in full. cascor#633 opens that\n"
    "# message with a machine-readable token (``_PROJECT_API_SHORTFALL_REFUSAL_TOKEN`` there);\n"
    "# the fixed sentence is matched as well so the prompt keeps working against a cascor that\n"
    "# predates the token. Neither string occurs in any other refusal cascor emits -- an outage\n"
    '# reads "juniper-data fetch failed: ..." -- and an outage must never open a prompt whose\n'
    "# every option re-sends the request.\n"
    'DATASET_SHORTFALL_REFUSAL_TOKEN = "[dataset_shortfall_refused]"\n'
    'DATASET_SHORTFALL_REFUSAL_SENTENCE = "could not produce the requested dataset in full"\n'
    "\n"
    "# The three options, as the Overtoad specified them (2026-09-05 ruling): option 3 -- fail -- is\n"
    "# the one that cancels the load and deselects the dataset. Options 1 and 2 are juniper-data\n"
    "# request parameters and travel on the generic ``nn_dataset_params`` channel.\n"
    "DATASET_SHORTFALL_OPTIONS = {\n"
    '    "dataset-shortfall-accept-button": {"allow_truncation": True, "incomplete_rows": "accept"},\n'
    '    "dataset-shortfall-drop-button": {"allow_truncation": True, "incomplete_rows": "drop"},\n'
    "}\n"
    'DATASET_SHORTFALL_FAIL_BUTTON = "dataset-shortfall-fail-button"\n'
    "\n"
    "# cascor's staged-config dialect -> canopy's ``/api/stage_dataset`` body keys, for re-staging\n"
    "# the config cascor still holds after a refused Start (it leaves the pending config in place\n"
    "# precisely so the operator can retry). The inverse of the adapter's ``_DATASET_PARAM_MAP``;\n"
    "# kept here rather than imported because the adapter is a service-mode module and this\n"
    "# handler must also run against demo mode.\n"
    "_CASCOR_TO_CANOPY_DATASET_KEYS = {\n"
    '    "dataset_type": "nn_dataset_type",\n'
    '    "n_samples": "nn_dataset_elements",\n'
    '    "noise": "nn_dataset_noise",\n'
    '    "rotations": "nn_spiral_rotations",\n'
    '    "n_spirals": "nn_spiral_number",\n'
    "}\n"
    "\n"
    "\n"
    "def selection_axis_unset(value) -> bool:\n",
)

# ---------------------------------------------------------------- dashboard_manager.py: layout
replace_once(
    DM,
    "                # Hidden div to store WebSocket data\n"
    '                html.Div(id="websocket-data", style={"display": "none"}),\n',
    "                # Partial-data contract -- the three-way prompt. Opens when a Start is refused\n"
    "                # because juniper-data could not produce the staged dataset in full (cascor\n"
    "                # leaves the staged config in place for exactly this retry). The operator must\n"
    "                # choose: accept the broken rows and continue, drop them and continue, or fail\n"
    "                # the load -- which cancels the staged change and deselects the dataset. Fed by\n"
    "                # ``training-control-action`` on BOTH transports, so it fires whether the Start\n"
    "                # went over WS or REST. Static backdrop and no close button: the contract asks\n"
    "                # for an affirmative choice, and dismissing the modal would leave the staged\n"
    "                # change in place with the question unanswered.\n"
    '                dcc.Store(id="dataset-shortfall-context", data=None),\n'
    "                dbc.Modal(\n"
    "                    [\n"
    '                        dbc.ModalHeader(dbc.ModalTitle("The dataset could not be produced in full"), close_button=False),\n'
    '                        dbc.ModalBody(id="dataset-shortfall-modal-body"),\n'
    "                        dbc.ModalFooter(\n"
    "                            [\n"
    '                                dbc.Button("Accept broken rows and continue", id="dataset-shortfall-accept-button", color="warning", className="me-2"),\n'
    '                                dbc.Button("Drop broken rows and continue", id="dataset-shortfall-drop-button", color="warning", outline=True, className="me-auto"),\n'
    '                                dbc.Button("Fail the load and pick another dataset", id="dataset-shortfall-fail-button", color="danger", outline=True),\n'
    "                            ]\n"
    "                        ),\n"
    "                    ],\n"
    '                    id="dataset-shortfall-modal",\n'
    "                    is_open=False,\n"
    '                    backdrop="static",\n'
    "                    keyboard=False,\n"
    '                    size="lg",\n'
    "                    centered=True,\n"
    "                ),\n"
    "                # Outcome of the operator's choice (re-staged + started / cancelled + deselected /\n"
    "                # could not re-stage). Below dataset-stage-outcome-alert (top:17rem).\n"
    '                html.Div(id="dataset-shortfall-outcome-alert", style={"position": "fixed", "top": "21rem", "right": "1rem", "zIndex": 1060, "minWidth": "20rem"}),\n'
    "                # Hidden div to store WebSocket data\n"
    '                html.Div(id="websocket-data", style={"display": "none"}),\n',
)

# ---------------------------------------------------------------- dashboard_manager.py: callbacks
replace_once(
    DM,
    "        def surface_training_control_outcome(action):\n"
    '            """Render the danger alert on failure; clear it on success."""\n'
    "            return self._surface_training_control_outcome_handler(action=action)\n",
    "        def surface_training_control_outcome(action):\n"
    '            """Render the danger alert on failure; clear it on success."""\n'
    "            return self._surface_training_control_outcome_handler(action=action)\n"
    "\n"
    "        # Partial-data contract -- open the three-way prompt on a shortfall-refused Start.\n"
    "        # Registered unconditionally, beside the outcome alert, because both transports write\n"
    "        # the outcome into ``training-control-action``. A separate callback rather than an\n"
    "        # extra Output on the alert's, so the alert's pinned shape is untouched.\n"
    "        @self.app.callback(\n"
    '            Output("dataset-shortfall-modal", "is_open"),\n'
    '            Output("dataset-shortfall-modal-body", "children"),\n'
    '            Output("dataset-shortfall-context", "data"),\n'
    '            Input("training-control-action", "data"),\n'
    "            prevent_initial_call=True,\n"
    "        )\n"
    "        def open_dataset_shortfall_prompt(action):\n"
    '            """Open the accept / drop / fail prompt when a Start was refused for a partial dataset."""\n'
    "            return self._open_dataset_shortfall_prompt_handler(action=action)\n"
    "\n"
    "        # The operator's answer. Accept / drop re-stage the held config with the opt-in and Start\n"
    "        # again, writing the outcome into ``training-control-action`` so the existing alert (and,\n"
    "        # on a further shortfall, this prompt) render it; fail cancels the staged change and\n"
    "        # clears the dataset selection. The dropdown value and the pending banner are owned\n"
    "        # elsewhere, hence ``allow_duplicate``.\n"
    "        @self.app.callback(\n"
    '            Output("dataset-shortfall-modal", "is_open", allow_duplicate=True),\n'
    '            Output("dataset-shortfall-outcome-alert", "children"),\n'
    '            Output("training-control-action", "data", allow_duplicate=True),\n'
    '            Output("nn-dataset-type-dropdown", "value", allow_duplicate=True),\n'
    '            Output("pending-dataset-banner", "is_open", allow_duplicate=True),\n'
    '            Input("dataset-shortfall-accept-button", "n_clicks"),\n'
    '            Input("dataset-shortfall-drop-button", "n_clicks"),\n'
    '            Input("dataset-shortfall-fail-button", "n_clicks"),\n'
    '            dash.dependencies.State("dataset-shortfall-context", "data"),\n'
    "            prevent_initial_call=True,\n"
    "        )\n"
    "        def resolve_dataset_shortfall(accept_clicks, drop_clicks, fail_clicks, context):\n"
    '            """Apply the operator\'s choice: re-stage with the opt-in and start, or cancel and deselect."""\n'
    "            return self._resolve_dataset_shortfall_handler(\n"
    "                triggered_id=dash.callback_context.triggered_id,\n"
    "                clicks=(accept_clicks, drop_clicks, fail_clicks),\n"
    "                context=context,\n"
    "            )\n",
)

# ---------------------------------------------------------------- dashboard_manager.py: handlers
replace_once(
    DM,
    "    def _update_button_appearance_handler(self, button_states=None, model_key=None, dataset_value=None):\n",
    "    # ------------------------------------------------------------------\n"
    "    # Partial-data contract: the three-way prompt (accept / drop / fail).\n"
    "    # ------------------------------------------------------------------\n"
    "\n"
    "    @staticmethod\n"
    "    def _is_dataset_shortfall_refusal(detail) -> bool:\n"
    '        """True when a Start refusal is the producer\'s "cannot deliver in full" class.\n'
    "\n"
    "        cascor#633 opens the message with ``DATASET_SHORTFALL_REFUSAL_TOKEN``; the fixed\n"
    "        sentence is matched too so the prompt works against a cascor that predates the\n"
    '        token. An ordinary outage ("juniper-data fetch failed: connection refused") carries\n'
    "        neither, and must not open a prompt whose every option re-sends the request.\n"
    '        """\n'
    '        text = str(detail or "")\n'
    "        return DATASET_SHORTFALL_REFUSAL_TOKEN in text or DATASET_SHORTFALL_REFUSAL_SENTENCE in text\n"
    "\n"
    "    @staticmethod\n"
    "    def _producer_detail_from_refusal(detail: str) -> str:\n"
    '        """Pull juniper-data\'s own sentence (affected symbols, row counts) out of cascor\'s refusal."""\n'
    '        marker = "Producer detail: "\n'
    "        if marker not in detail:\n"
    '            return ""\n'
    "        tail = detail.split(marker, 1)[1]\n"
    '        for stop in (" To accept it,", " The resulting dataset"):\n'
    "            if stop in tail:\n"
    "                tail = tail.split(stop, 1)[0]\n"
    "        return tail.strip()\n"
    "\n"
    "    def _open_dataset_shortfall_prompt_handler(self, action=None):\n"
    '        """Open the three-way prompt when a Start failed because the dataset is partial.\n'
    "\n"
    "        Returns ``(modal_is_open, body_children, context)``. Any other action -- a success, a\n"
    "        different command, an outage -- leaves the modal alone (``no_update``), so a later\n"
    "        unrelated outcome does not close a prompt the operator has not answered.\n"
    '        """\n'
    '        if not action or action.get("success", True) or action.get("command") != "start":\n'
    "            return dash.no_update, dash.no_update, dash.no_update\n"
    '        detail_full = (action.get("detail_full") or action.get("detail") or "").strip()\n'
    "        if not self._is_dataset_shortfall_refusal(detail_full):\n"
    "            return dash.no_update, dash.no_update, dash.no_update\n"
    '        self.logger.warning("Start refused for a partial dataset; opening the three-way prompt: %s", detail_full[:200])\n'
    "        producer_detail = self._producer_detail_from_refusal(detail_full)\n"
    "        body = [\n"
    "            html.P(\n"
    "                [\n"
    '                    html.Strong("juniper-data could not produce the staged dataset in full, and this run has not accepted a partial one. "),\n'
    '                    html.Span("Training did not start. The staged dataset change is still in place, so decide what to do with it."),\n'
    "                ]\n"
    "            ),\n"
    "        ]\n"
    "        if producer_detail:\n"
    '            body.append(html.P(producer_detail, className="text-muted", style={"fontSize": "0.85rem", "whiteSpace": "pre-wrap"}))\n'
    "        body.append(\n"
    "            html.Ul(\n"
    "                [\n"
    '                    html.Li([html.Strong("Accept broken rows and continue"), " — train on the partial dataset as delivered. Rows the producer could not resolve carry placeholder values; the run, its metrics and its results are permanently annotated as partial."]),\n'
    '                    html.Li([html.Strong("Drop broken rows and continue"), " — remove the affected symbols and train on the rest; the run is annotated as partial and the record says what was dropped."]),\n'
    '                    html.Li([html.Strong("Fail the load"), " — cancel the staged change, deselect this dataset, and choose another."]),\n'
    "                ]\n"
    "            )\n"
    "        )\n"
    '        return True, body, {"detail": detail_full, "ts": time.time()}\n'
    "\n"
    "    def _fetch_pending_dataset_config(self):\n"
    '        """The staged dataset config cascor still holds, in cascor\'s dialect, or ``None``."""\n'
    "        try:\n"
    '            resp = requests.get(self._api_url("/api/status"), timeout=DashboardConstants.API_TIMEOUT_SECONDS, headers=internal_api_headers())\n'
    "            if resp.status_code != 200:\n"
    "                return None\n"
    "            data = resp.json()\n"
    "        except (requests.RequestException, ValueError) as exc:\n"
    '            self.logger.warning("Could not read the pending dataset config: %s", exc)\n'
    "            return None\n"
    '        pending = data.get("pending_dataset") if isinstance(data, dict) else None\n'
    "        return dict(pending) if isinstance(pending, dict) and pending else None\n"
    "\n"
    "    @staticmethod\n"
    "    def _restage_payload_with_policy(pending, choice):\n"
    '        """Translate cascor\'s staged config back into an ``/api/stage_dataset`` body carrying the opt-in.\n'
    "\n"
    "        ``nn_dataset_params`` (the generic channel) is where the policy fields live -- they are\n"
    "        juniper-data request parameters, and the adapter forwards that dict verbatim as cascor's\n"
    "        ``params``. The typed spiral fields map back by name; anything unknown is dropped\n"
    "        rather than guessed.\n"
    '        """\n'
    "        payload = {}\n"
    "        for cascor_key, canopy_key in _CASCOR_TO_CANOPY_DATASET_KEYS.items():\n"
    "            value = pending.get(cascor_key)\n"
    "            if value is not None:\n"
    "                payload[canopy_key] = value\n"
    '        params = dict(pending.get("params") or {})\n'
    "        params.update(choice)\n"
    '        payload["nn_dataset_params"] = params\n'
    "        return payload\n"
    "\n"
    "    def _post_stage_dataset(self, payload):\n"
    '        """POST /api/stage_dataset; returns ``(ok, detail)``."""\n'
    "        try:\n"
    '            resp = requests.post(self._api_url("/api/stage_dataset"), json=payload, timeout=DashboardConstants.DASHBOARD_LONG_POST_TIMEOUT, headers=internal_api_headers())\n'
    "        except requests.RequestException as exc:\n"
    '            return False, f"backend unreachable: {exc}"\n'
    "        if resp.status_code == 200:\n"
    '            self.logger.info("Re-staged dataset with the partial-data choice: %s", payload)\n'
    '            return True, ""\n'
    '        return False, (resp.text[:300] if resp.text else f"HTTP {resp.status_code}")\n'
    "\n"
    "    def _post_train_start(self):\n"
    '        """POST /api/train/start the way the server-side control handler does; returns ``(started, detail)``."""\n'
    "        try:\n"
    '            resp = requests.post(self._api_url("/api/train/start"), timeout=DashboardConstants.DASHBOARD_POST_TIMEOUT, headers=internal_api_headers())\n'
    "            resp.raise_for_status()\n"
    '            return True, ""\n'
    "        except Exception as exc:\n"
    "            detail = self._extract_training_error_detail(exc)\n"
    '            self.logger.warning("Start after the partial-data choice failed: %s", detail)\n'
    "            return False, detail\n"
    "\n"
    "    def _cancel_pending_dataset_via_api(self):\n"
    '        """DELETE /api/cancel_pending_dataset; returns ``(ok, detail)``."""\n'
    "        try:\n"
    '            resp = requests.delete(self._api_url("/api/cancel_pending_dataset"), timeout=DashboardConstants.DASHBOARD_LONG_POST_TIMEOUT, headers=internal_api_headers())\n'
    "        except requests.RequestException as exc:\n"
    '            return False, f"backend unreachable: {exc}"\n'
    "        if resp.status_code == 200:\n"
    '            return True, ""\n'
    '        return False, (resp.text[:300] if resp.text else f"HTTP {resp.status_code}")\n'
    "\n"
    "    def _resolve_dataset_shortfall_handler(self, triggered_id=None, clicks=(None, None, None), context=None):\n"
    '        """Carry out the operator\'s answer to the three-way prompt.\n'
    "\n"
    "        Returns ``(modal_is_open, outcome_alert, control_action, dataset_dropdown_value,\n"
    "        pending_banner_is_open)``.\n"
    "\n"
    "        * accept / drop: re-stage the config cascor still holds (``pending_dataset`` on\n"
    "          ``/api/status``) with ``allow_truncation=true`` and the chosen ``incomplete_rows``,\n"
    "          then Start again. The outcome is written into ``training-control-action`` so the\n"
    "          existing alert renders a second failure -- and, if that failure is ANOTHER shortfall\n"
    "          refusal (drop can empty the universe), the prompt re-opens on it.\n"
    "        * fail: cancel the staged change and clear the dataset selection (``⊥``), so Start\n"
    "          and Apply are gated until the operator picks another dataset.\n"
    "\n"
    "        ``context`` is the prompt's own record of the refusal; it is informational here (the\n"
    "        config to re-stage is read back from cascor, which is the authority on what is staged).\n"
    '        """\n'
    "        idle = (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)\n"
    "        if not triggered_id or not any(clicks):\n"
    "            return idle\n"
    "        if triggered_id == DATASET_SHORTFALL_FAIL_BUTTON:\n"
    "            ok, detail = self._cancel_pending_dataset_via_api()\n"
    "            if ok:\n"
    '                self.logger.info("Partial-data prompt: load failed by operator choice; staged change discarded and dataset deselected")\n'
    "                alert = dbc.Alert(\n"
    '                    [html.Strong("Dataset load cancelled. "), html.Span("The staged change was discarded and the dataset deselected — choose another dataset.")],\n'
    '                    color="info",\n'
    "                    dismissable=True,\n"
    "                    duration=10000,\n"
    "                )\n"
    "                return False, alert, dash.no_update, None, False\n"
    '            alert = dbc.Alert([html.Strong("Could not cancel the staged dataset: "), html.Span(detail)], color="danger", dismissable=True, duration=10000)\n'
    "            return False, alert, dash.no_update, dash.no_update, dash.no_update\n"
    "        choice = DATASET_SHORTFALL_OPTIONS.get(triggered_id)\n"
    "        if choice is None:\n"
    "            return idle\n"
    "        pending = self._fetch_pending_dataset_config()\n"
    "        if not pending:\n"
    "            alert = dbc.Alert(\n"
    '                [html.Strong("Nothing to re-stage. "), html.Span("cascor no longer holds a staged dataset change; apply the dataset again, then Start.")],\n'
    '                color="warning",\n'
    "                dismissable=True,\n"
    "                duration=10000,\n"
    "            )\n"
    "            return False, alert, dash.no_update, dash.no_update, dash.no_update\n"
    "        payload = self._restage_payload_with_policy(pending, choice)\n"
    "        ok, detail = self._post_stage_dataset(payload)\n"
    "        if not ok:\n"
    '            alert = dbc.Alert([html.Strong("Could not re-stage the dataset with your choice: "), html.Span(detail)], color="danger", dismissable=True, duration=10000)\n'
    "            return False, alert, dash.no_update, dash.no_update, dash.no_update\n"
    "        started, start_detail = self._post_train_start()\n"
    "        action = {\n"
    '            "last": triggered_id,\n'
    '            "ts": time.time(),\n'
    '            "success": started,\n'
    '            "command": "start",\n'
    '            "transport": "rest",\n'
    '            "detail": (start_detail or "")[:300],\n'
    '            "detail_full": (start_detail or "")[:4000],\n'
    "        }\n"
    "        if not started:\n"
    "            # The training-control outcome alert renders the failure from ``action``.\n"
    "            return False, dash.no_update, action, dash.no_update, dash.no_update\n"
    '        label = "accepting" if choice["incomplete_rows"] == "accept" else "dropping"\n'
    "        alert = dbc.Alert(\n"
    '            [html.Strong("Training started on the partial dataset, "), html.Span(f"{label} the broken rows. The run is annotated as partial (status bar and Network Info).")],\n'
    '            color="warning",\n'
    "            dismissable=True,\n"
    "            duration=12000,\n"
    "        )\n"
    "        return False, alert, action, dash.no_update, dash.no_update\n"
    "\n"
    "    def _update_button_appearance_handler(self, button_states=None, model_key=None, dataset_value=None):\n",
)

# ---------------------------------------------------------------- dashboard_manager.py: status bar suffix
replace_once(
    DM,
    '        if status == "Completed":\n'
    '            completion_label = self._completion_reason_label(status_data.get("completion_reason"))\n'
    "            if completion_label:\n"
    '                status = f"{status} — {completion_label}"\n',
    '        if status == "Completed":\n'
    '            completion_label = self._completion_reason_label(status_data.get("completion_reason"))\n'
    "            if completion_label:\n"
    '                status = f"{status} — {completion_label}"\n'
    "\n"
    "        # Partial-data contract: a run on a partial dataset carries the mark on the surface\n"
    "        # every operator watches, in every state -- progress while it runs, result when it\n"
    "        # completes. ``dataset_shortfall`` is None when the producer delivered in full.\n"
    '        if status_data.get("dataset_shortfall"):\n'
    '            status = f"{status} · partial data"\n',
)

# ---------------------------------------------------------------- dashboard_manager.py: network info
replace_once(
    DM,
    "    def _render_network_info(self, status):\n"
    '        """Render the Network Information panel body from an ``/api/status`` payload."""\n',
    "    @staticmethod\n"
    "    def _dataset_shortfall_note_children(status):\n"
    '        """A warning block for the Network Info panel when the run is on a partial dataset, else ``[]``.\n'
    "\n"
    "        Reads cascor's ``dataset_shortfall`` annotation (``None`` when the producer delivered in\n"
    "        full). The ``summary`` is cascor's own sentence -- one formatter, so the panel cannot\n"
    "        disagree with the training log -- and it already says who accepted the shortfall.\n"
    '        """\n'
    '        shortfall = status.get("dataset_shortfall") if isinstance(status, dict) else None\n'
    "        if not isinstance(shortfall, dict) or not shortfall:\n"
    "            return []\n"
    '        summary = shortfall.get("summary") or "the producer could not deliver the dataset in full"\n'
    '        dataset_id = shortfall.get("dataset_id")\n'
    "        children = [html.Strong(\"Partial dataset. \"), html.Span(f\"{summary}.\")]\n"
    "        if dataset_id:\n"
    '            children.extend([html.Br(), html.Small(f"dataset_id {dataset_id}", className="text-muted")])\n'
    '        return [dbc.Alert(children, color="warning", className="mb-2 py-2"), html.Hr()]\n'
    "\n"
    "    def _render_network_info(self, status):\n"
    '        """Render the Network Information panel body from an ``/api/status`` payload."""\n',
)
replace_once(
    DM,
    "        counters = self._counter_displays(status)\n"
    "\n"
    "        return html.Div(\n"
    "            [\n"
    "                html.P(\n"
    "                    [\n"
    '                        html.Strong("Input Nodes: "),\n',
    "        counters = self._counter_displays(status)\n"
    "\n"
    "        return html.Div(\n"
    "            self._dataset_shortfall_note_children(status)\n"
    "            + [\n"
    "                html.P(\n"
    "                    [\n"
    '                        html.Strong("Input Nodes: "),\n',
)

# ---------------------------------------------------------------- control manifest
replace_once(
    MANIFEST,
    '        notes="Cancel any staged dataset change.",\n'
    "    ),\n",
    '        notes="Cancel any staged dataset change.",\n'
    "    ),\n"
    "    # ---- Partial-data prompt (accept / drop re-stage the held config with the opt-in; fail cancels) ----\n"
    "    ControlContract(\n"
    '        control_id="dataset-shortfall-accept-button",\n'
    '        kind="button",\n'
    '        method="POST",\n'
    '        endpoint="/api/stage_dataset",\n'
    '        body={"nn_dataset_type": "xor", "nn_dataset_params": {"allow_truncation": True, "incomplete_rows": "accept"}},\n'
    '        resp_key="status",\n'
    '        resp_equals="success",\n'
    '        notes="Option 1: re-stage the held config with allow_truncation=true / incomplete_rows=accept, then Start.",\n'
    "    ),\n"
    "    ControlContract(\n"
    '        control_id="dataset-shortfall-drop-button",\n'
    '        kind="button",\n'
    '        method="POST",\n'
    '        endpoint="/api/stage_dataset",\n'
    '        body={"nn_dataset_type": "xor", "nn_dataset_params": {"allow_truncation": True, "incomplete_rows": "drop"}},\n'
    '        resp_key="status",\n'
    '        resp_equals="success",\n'
    '        notes="Option 2: re-stage the held config with allow_truncation=true / incomplete_rows=drop, then Start.",\n'
    "    ),\n"
    "    ControlContract(\n"
    '        control_id="dataset-shortfall-fail-button",\n'
    '        kind="button",\n'
    '        method="DELETE",\n'
    '        endpoint="/api/cancel_pending_dataset",\n'
    '        resp_key="status",\n'
    '        resp_equals="success",\n'
    '        notes="Option 3: fail the load -- cancel the staged change and deselect the dataset.",\n'
    "    ),\n",
)

# ---------------------------------------------------------------- CHANGELOG
replace_once(
    CHANGELOG,
    "## [Unreleased]\n\n### Changed\n\n- **The five registry resolvers that closed over module globals are now injectable** --\n",
    "## [Unreleased]\n\n### Added\n\n"
    "- **The partial-data contract's three-way prompt — the last unbuilt piece of the contract.** When a\n"
    "  Start is refused because juniper-data could not produce the staged dataset in full (cascor leaves\n"
    "  the staged config in place for exactly this retry), a modal now puts the Overtoad's three options to\n"
    "  the operator and requires an affirmative choice: **accept** the broken rows and continue, **drop**\n"
    "  them and continue, or **fail** the load — which cancels the staged change and deselects the\n"
    "  dataset (`⊥`) so Start and Apply stay gated until another is chosen. Accept and drop re-stage\n"
    "  the config cascor still holds with `allow_truncation=true` and the chosen `incomplete_rows`\n"
    "  through the existing `/api/stage_dataset` route, then Start again; the outcome rides the\n"
    "  existing `training-control-action` store, so a second refusal renders through the same alert\n"
    "  and — if it is another shortfall (drop can empty a universe) — re-opens the prompt.\n"
    "\n"
    "  The prompt fires on **both** transports (the Phase D clientside WS/REST path and the server-side\n"
    "  handler) because both write the outcome into that store; the clientside JS now also carries\n"
    "  `detail_full` (4000 chars) beside the alert's 300-char `detail`, so the producer's own sentence —\n"
    "  which symbols, how many rows — survives to the modal. It recognises the refusal by cascor#633's\n"
    "  machine-readable token `[dataset_shortfall_refused]`, and by the fixed sentence for a cascor that\n"
    '  predates it; an outage ("juniper-data fetch failed: …") carries neither and never opens it.\n'
    "\n"
    "  **A run on partial data is now marked where the operator looks**: `dataset_shortfall` is carried\n"
    "  through `normalize_status` (the whitelist was the one place it was lost — canopy already polls\n"
    "  cascor's status route at 1 Hz, so no new poller), the status bar appends `· partial data` in\n"
    "  every state (progress while it runs, result when it completes), and the Network Info panel opens\n"
    "  with cascor's own one-sentence summary, which names who accepted the shortfall.\n"
    "\n"
    "  **Two form defects fixed on the way.** The schema-driven sidebar rendered juniper-data's\n"
    "  `allow_truncation` checkbox and `incomplete_rows` select as ordinary inputs, so an unticked box\n"
    "  sent an **explicit `allow_truncation: false` on every equities apply** — which cascor#624\n"
    "  honours over its own deployment default, turning the operator's silence into a refusal and\n"
    "  stripping the remedy from the failure message — while a ticked one pre-answered a question the\n"
    "  contract says must be asked when the shortfall happens. Both are now `PARTIAL_DATA_POLICY_FIELDS`,\n"
    "  excluded from the form; the prompt owns them, and a default apply sends neither (option 3).\n"
    "\n"
    "  Found by the round-37 handoff validation in juniper-ml. Not in this change: an equities request\n"
    '  at canopy\'s defaults (`start_date` 2000, `fundamentals_fill="nan"`) is refused by cascor#630\'s\n'
    "  NaN guard *after* the shortfall is accepted, so exercising the prompt end-to-end on equities\n"
    "  needs a later `start_date` or a fill policy — a separate finding, recorded in that handoff.\n"
    "\n"
    "### Changed\n\n- **The five registry resolvers that closed over module globals are now injectable** --\n",
)

# ---------------------------------------------------------------- tests: service backend
replace_once(
    T_SERVICE,
    '        assert service_backend.get_status()["completion_reason"] is None\n'
    "\n"
    "    def test_get_metrics_returns_dict(self, service_backend):\n",
    '        assert service_backend.get_status()["completion_reason"] is None\n'
    "\n"
    "    def test_get_status_carries_dataset_shortfall(self, service_backend, mock_adapter):\n"
    '        """cascor#624\'s partial-data annotation is carried through unchanged (partial-data contract).\n'
    "\n"
    "        ``normalize_status`` is a whitelist, so this line is the ONLY place the field could be lost\n"
    "        between cascor's status route and the dashboard's status bar / Network Info panel.\n"
    '        """\n'
    '        shortfall = {"dataset_id": "equities-3.0.0-abc", "accepted_by_this_run": True, "acceptance_source": "request_params", "summary": "14 of 503 symbols imported (cap 14)"}\n'
    "        mock_adapter.get_training_status.return_value = {\n"
    '            "state_machine": {"status": "Running", "phase": "output"},\n'
    '            "monitor": {"current_epoch": 5},\n'
    '            "training_state": {"input_size": 16, "output_size": 3},\n'
    '            "training_active": True,\n'
    '            "network_loaded": True,\n'
    '            "dataset_shortfall": shortfall,\n'
    "        }\n"
    '        assert service_backend.get_status()["dataset_shortfall"] == shortfall\n'
    "\n"
    "    def test_get_status_dataset_shortfall_absent_is_none(self, service_backend, mock_adapter):\n"
    '        """A clean dataset (or a cascor that predates the field) reads None -- consumers branch on presence."""\n'
    "        mock_adapter.get_training_status.return_value = {\n"
    '            "state_machine": {"status": "Stopped", "phase": "idle"},\n'
    '            "monitor": {},\n'
    '            "training_state": {},\n'
    '            "training_active": False,\n'
    '            "network_loaded": True,\n'
    "        }\n"
    '        assert service_backend.get_status()["dataset_shortfall"] is None\n'
    "\n"
    "    def test_get_metrics_returns_dict(self, service_backend):\n",
)

# ---------------------------------------------------------------- tests: dataset schema
replace_once(
    T_SCHEMA,
    "    INFRASTRUCTURE_FIELDS,\n",
    "    INFRASTRUCTURE_FIELDS,\n    PARTIAL_DATA_POLICY_FIELDS,\n",
)
replace_once(
    T_SCHEMA,
    "    assert INFRASTRUCTURE_FIELDS.isdisjoint(names)\n"
    "\n"
    "\n"
    "def test_parse_maps_types_bounds_defaults_and_enums():\n",
    "    assert INFRASTRUCTURE_FIELDS.isdisjoint(names)\n"
    "\n"
    "\n"
    "def test_parse_excludes_partial_data_policy_fields():\n"
    '    """The three-way prompt owns allow_truncation / incomplete_rows; the form must send neither.\n'
    "\n"
    "    Rendered as inputs, an unticked checkbox sent an explicit ``allow_truncation: false`` on every\n"
    "    equities apply -- which cascor#624 honours over its deployment default -- and a ticked one\n"
    "    pre-answered the question the contract puts to the operator at the shortfall itself.\n"
    '    """\n'
    "    schema = {\n"
    '        "properties": {\n'
    '            "start_date": {"type": "string", "default": "2000-01-01"},\n'
    '            "allow_truncation": {"type": "boolean", "default": False},\n'
    '            "incomplete_rows": {"type": "string", "enum": ["accept", "drop"], "default": "accept"},\n'
    '            "max_symbols": {"type": "integer", "default": 14},\n'
    "        }\n"
    "    }\n"
    "    names = [f.name for f in parse_schema_fields(schema)]\n"
    '    assert names == ["start_date", "max_symbols"]\n'
    "    assert PARTIAL_DATA_POLICY_FIELDS.isdisjoint(names)\n"
    "    # A caller that passes its own ``exclude`` is unaffected -- the default is what the sidebar uses.\n"
    '    assert "allow_truncation" in [f.name for f in parse_schema_fields(schema, exclude=())]\n'
    "\n"
    "\n"
    "def test_parse_maps_types_bounds_defaults_and_enums():\n",
)

# ---------------------------------------------------------------- tests: JS contract
replace_once(
    T_JS,
    "    def test_js_forwards_oneshot_dataset_ref_body(self):\n",
    "    def test_js_report_failure_carries_the_full_detail_for_the_partial_data_prompt(self):\n"
    '        """``detail`` is the alert\'s 300-char slice; ``detail_full`` keeps the producer\'s own\n'
    "        sentence (which symbols, how many rows) for the three-way prompt, which the slice cuts off.\"\"\"\n"
    "        from frontend.dashboard_manager import PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS\n"
    "\n"
    "        js = PHASE_D_TRAINING_BUTTONS_CLIENTSIDE_JS\n"
    "        assert \"detail_full: String(detail || '').slice(0, 4000)\" in js\n"
    "        assert \"detail: String(detail || '').slice(0, 300)\" in js\n"
    "\n"
    "    def test_js_forwards_oneshot_dataset_ref_body(self):\n",
)
print("ALL CANOPY EDITS APPLIED")
