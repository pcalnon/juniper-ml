"""Probe: which Dash components accept an aria-describedby wildcard prop."""

import dash_bootstrap_components as dbc
from dash import html

try:
    dbc.Button("Select", id="x", **{"aria-describedby": "reason-x"})
    print("dbc.Button: ACCEPTED aria-describedby")
except TypeError as exc:
    print(f"dbc.Button: REJECTED -> {exc}")

button = html.Button("Select", id="y", disabled=True, className="btn btn-outline-primary btn-sm", type="button", **{"aria-describedby": "reason-y"})
print("html.Button wildcards:", button._valid_wildcard_attributes)
print("html.Button props include type/title/disabled:", [p for p in ("type", "title", "disabled", "n_clicks") if p in button._prop_names])
print("html.Button to_plotly_json props:", button.to_plotly_json()["props"])
