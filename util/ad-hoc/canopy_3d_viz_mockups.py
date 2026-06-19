#!/usr/bin/env python
# Ad-hoc / single-use: mockup generator for the canopy 3-D (time-series) dataset
# visualization design session (2026-06-18). Synthesizes two complementary
# time-series dataset types and renders one comparison figure per design question
# (Q1-Q6), illustrating both sides of each dichotomy. Output: PNG (kaleido) +
# interactive HTML under notes/canopy_3d_viz_mockups/.
#
#   Run (env with plotly + kaleido + numpy):
#     conda activate JuniperCanopy1 && python util/ad-hoc/canopy_3d_viz_mockups.py
#
# Synthetic ("dummy") data only — NOT the real juniper-data generators.
from __future__ import annotations

import pathlib

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUT = pathlib.Path(__file__).resolve().parents[2] / "notes" / "canopy_3d_viz_mockups"
OUT.mkdir(parents=True, exist_ok=True)

# Canopy-light-ish palette + template.
TEMPLATE = "plotly_white"
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
RNG = np.random.default_rng(7)


# --------------------------------------------------------------------------- data
def gen_irregular_sine(n_windows=4, length=44, n_features=2):
    """Univariate-leaning smooth oscillation on an irregular time grid."""
    out = []
    for w in range(n_windows):
        gaps = RNG.exponential(1.0, size=length).cumsum()
        t = gaps / gaps[-1] * 6.0  # real time in [0, 6]
        freq = 0.9 + 0.25 * w
        f0 = np.sin(2 * np.pi * freq * t) + 0.04 * RNG.standard_normal(length)
        f1 = 0.6 * np.sin(2 * np.pi * freq * t + 1.1) + 0.04 * RNG.standard_normal(length)
        X = np.stack([f0, f1], axis=-1)[:, :n_features]
        dt = np.diff(t, prepend=t[0])
        out.append({"t": t, "dt": dt, "X": X.astype(np.float32),
                    "y": float(f0[-1]), "features": ["signal", "phase-shift"][:n_features],
                    "name": "irregular_sine"})
    return out


def gen_equities(n_windows=4, length=32):
    """5-feature OHLCV with weekend-gapped (irregular) trading days."""
    out = []
    for w in range(n_windows):
        days, d, cnt = [], 0, 0
        while cnt < length:
            if d % 7 not in (5, 6):  # skip Sat/Sun -> irregular spacing
                days.append(d)
                cnt += 1
            d += 1
        t = np.asarray(days, float)
        ret = 0.012 * RNG.standard_normal(length)
        close = 100 * np.exp(np.cumsum(ret))
        openp = close * (1 + 0.003 * RNG.standard_normal(length))
        high = np.maximum(openp, close) * (1 + 0.004 * np.abs(RNG.standard_normal(length)))
        low = np.minimum(openp, close) * (1 - 0.004 * np.abs(RNG.standard_normal(length)))
        vol = np.abs(1.0 + 0.35 * RNG.standard_normal(length)) * 1e6
        X = np.stack([openp, high, low, close, vol], axis=-1)
        dt = np.diff(t, prepend=t[0])
        out.append({"t": t, "dt": dt, "X": X.astype(np.float32),
                    "y": float(ret[-1]), "features": ["Open", "High", "Low", "Close", "Volume"],
                    "name": "equities_seq"})
    return out


SINE = gen_irregular_sine()
EQ = gen_equities()


def _style(fig, title, height=540):
    fig.update_layout(template=TEMPLATE, title={"text": title, "x": 0.5, "font": {"size": 17}},
                      height=height, width=1180, margin={"t": 92, "b": 56, "l": 64, "r": 28},
                      showlegend=True, legend={"orientation": "h", "y": -0.12},
                      font={"size": 12})
    fig.add_annotation(text="MOCKUP — synthetic data", xref="paper", yref="paper",
                       x=1.0, y=1.06, showarrow=False, font={"size": 10, "color": "#999"})
    return fig


def _save(fig, stem):
    fig.write_image(str(OUT / f"{stem}.png"), scale=2)
    fig.write_html(str(OUT / f"{stem}.html"), include_plotlyjs="cdn")
    print(f"  wrote {stem}.png + .html")


# ------------------------------------------------------------------- Q1 primary view
def q1_primary_view():
    fig = make_subplots(
        rows=2, cols=2, vertical_spacing=0.16, horizontal_spacing=0.09,
        subplot_titles=("A · sample lines — irregular_sine", "A · sample lines — equities_seq (Close)",
                        "C · characterization — irregular_sine (Δt histogram)",
                        "C · characterization — equities_seq (Δt histogram)"))
    s, e = SINE[0], EQ[0]
    fig.add_trace(go.Scatter(x=s["t"], y=s["X"][:, 0], mode="lines+markers", name="signal",
                             line={"color": COLORS[0]}), row=1, col=1)
    fig.add_trace(go.Scatter(x=e["t"], y=e["X"][:, 3], mode="lines+markers", name="Close",
                             line={"color": COLORS[1]}, showlegend=False), row=1, col=2)
    fig.add_trace(go.Histogram(x=s["dt"], marker_color=COLORS[0], name="Δt (sine)",
                               showlegend=False), row=2, col=1)
    fig.add_trace(go.Histogram(x=e["dt"], marker_color=COLORS[1], name="Δt (equities)",
                               showlegend=False), row=2, col=2)
    fig.update_xaxes(title_text="time", row=1, col=1)
    fig.update_xaxes(title_text="time (trading day)", row=1, col=2)
    fig.update_xaxes(title_text="Δt between steps", row=2, col=1)
    fig.update_xaxes(title_text="Δt (1=weekday gap, 3=weekend gap)", row=2, col=2)
    _style(fig, "Q1 — Primary view:  A (sample-sequence lines, top)  vs  C (Δt / characterization, bottom)", 640)
    _save(fig, "Q1_primary_view")


# ----------------------------------------------------------------- Q2 multi-feature
def q2_multifeature():
    e = EQ[0]
    feats = e["features"]
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.07,
                        subplot_titles=("Per-feature small-multiples", "Overlaid (shared axis)",
                                        "Single feature + selector"))
    # 1: small-multiples (vertically offset + normalized so all 5 fit one cell)
    for i, f in enumerate(feats):
        col = e["X"][:, i]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm + (len(feats) - 1 - i) * 1.15, mode="lines",
                                 line={"color": COLORS[i]}, name=f, legendgroup=f), row=1, col=1)
    # 2: overlaid (normalized so volume doesn't dwarf prices)
    for i, f in enumerate(feats):
        col = e["X"][:, i]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm, mode="lines", line={"color": COLORS[i]},
                                 name=f, legendgroup=f, showlegend=False), row=1, col=2)
    # 3: single feature (Close) + a mock selector annotation
    fig.add_trace(go.Scatter(x=e["t"], y=e["X"][:, 3], mode="lines+markers",
                             line={"color": COLORS[3]}, name="Close", showlegend=False), row=1, col=3)
    fig.add_annotation(text="▼ Feature:  [ Close ]", xref="x3 domain", yref="y3 domain",
                       x=0.04, y=1.14, showarrow=False, align="left",
                       font={"size": 12, "color": "#333"},
                       bordercolor="#888", borderwidth=1, borderpad=4, bgcolor="#fff")
    fig.update_yaxes(showticklabels=False, title_text="features (offset)", row=1, col=1)
    fig.update_yaxes(title_text="normalized", row=1, col=2)
    fig.update_yaxes(title_text="price", row=1, col=3)
    for c in (1, 2, 3):
        fig.update_xaxes(title_text="trading day", row=1, col=c)
    _style(fig, "Q2 — Multiple features (equities, 5 OHLCV):  small-multiples  vs  overlaid  vs  single+selector")
    _save(fig, "Q2_multifeature")


# ------------------------------------------------------------------- Q3 irregular Δt
def q3_irregular_dt():
    s = SINE[1]
    n = len(s["t"])
    fig = make_subplots(rows=2, cols=3, row_heights=[0.78, 0.22], vertical_spacing=0.13,
                        horizontal_spacing=0.07, shared_xaxes=False,
                        subplot_titles=("vs cumulative REAL time (Δt honored)",
                                        "vs STEP INDEX (Δt hidden — misleading)",
                                        "vs step index + Δt strip",
                                        "", "", "Δt per step"),
                        specs=[[{}, {}, {}], [{"colspan": 3}, None, None]])
    # 1: real time (markers at true positions — irregular gaps visible)
    fig.add_trace(go.Scatter(x=s["t"], y=s["X"][:, 0], mode="lines+markers",
                             line={"color": COLORS[0]}, name="real time"), row=1, col=1)
    # 2: step index (evenly spaced — the irregular sampling is invisible / distorted)
    fig.add_trace(go.Scatter(x=np.arange(n), y=s["X"][:, 0], mode="lines+markers",
                             line={"color": COLORS[3]}, name="step index"), row=1, col=2)
    # 3: step index plot ...
    fig.add_trace(go.Scatter(x=np.arange(n), y=s["X"][:, 0], mode="lines+markers",
                             line={"color": COLORS[2]}, name="step+strip", showlegend=False), row=1, col=3)
    # ... + a Δt strip spanning the bottom (under all three, but driven by step index)
    fig.add_trace(go.Bar(x=np.arange(n), y=s["dt"], marker_color="#bbb", name="Δt",
                         showlegend=False), row=2, col=1)
    fig.update_xaxes(title_text="real time", row=1, col=1)
    fig.update_xaxes(title_text="step index", row=1, col=2)
    fig.update_xaxes(title_text="step index", row=1, col=3)
    fig.update_xaxes(title_text="step index", row=2, col=1)
    fig.update_yaxes(title_text="signal", row=1, col=1)
    fig.update_yaxes(title_text="Δt", row=2, col=1)
    _style(fig, "Q3 — Irregular Δt (irregular_sine):  real-time  vs  step-index  vs  step-index + Δt strip", 600)
    _save(fig, "Q3_irregular_dt")


# ------------------------------------------------------------------ Q4 sample count
def q4_sample_count():
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=("Fixed few (3 windows overlaid)",
                                        "Single window + ◀ selector ▶"))
    for i in range(3):
        s = SINE[i]
        fig.add_trace(go.Scatter(x=s["t"], y=s["X"][:, 0], mode="lines",
                                 line={"color": COLORS[i]}, name=f"window {i}"), row=1, col=1)
    s = SINE[2]
    fig.add_trace(go.Scatter(x=s["t"], y=s["X"][:, 0], mode="lines+markers",
                             line={"color": COLORS[2]}, name="window 2", showlegend=False), row=1, col=2)
    fig.add_annotation(text="◀  Window  2 / 200  ▶", xref="x2 domain", yref="y2 domain",
                       x=0.5, y=1.13, showarrow=False, font={"size": 13, "color": "#333"},
                       bordercolor="#888", borderwidth=1, borderpad=5, bgcolor="#fff")
    for c in (1, 2):
        fig.update_xaxes(title_text="time", row=1, col=c)
    fig.update_yaxes(title_text="signal", row=1, col=1)
    _style(fig, "Q4 — How many sample sequences:  fixed few  vs  single + window selector")
    _save(fig, "Q4_sample_count")


# ----------------------------------------------------------------------- Q5 target
def q5_target():
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=("Input sequence + y_reg target",
                                        "Inputs only"))
    e = EQ[0]
    close = e["X"][:, 3]
    # left: input (Close) + the regression target marked as the next-step prediction
    fig.add_trace(go.Scatter(x=e["t"], y=close, mode="lines+markers", line={"color": COLORS[1]},
                             name="Close (input)"), row=1, col=1)
    t_next = e["t"][-1] + 1
    fig.add_trace(go.Scatter(x=[e["t"][-1], t_next], y=[close[-1], close[-1] * (1 + e["y"])],
                             mode="lines+markers", line={"color": COLORS[3], "dash": "dot"},
                             marker={"size": 11, "symbol": "star"}, name="y_reg (target: next return)"),
                  row=1, col=1)
    # right: inputs only
    fig.add_trace(go.Scatter(x=e["t"], y=close, mode="lines+markers", line={"color": COLORS[1]},
                             name="Close", showlegend=False), row=1, col=2)
    for c in (1, 2):
        fig.update_xaxes(title_text="trading day", row=1, col=c)
    fig.update_yaxes(title_text="price", row=1, col=1)
    _style(fig, "Q5 — The target:  show y_reg (regression target)  vs  inputs only")
    _save(fig, "Q5_target")


# ------------------------------------------------------------------------ Q6 scope
def q6_scope():
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=("Minimal first cut (1 feature, 1 window)",
                                        "Enriched (multi-feature + Δt-aware + target + selector)"))
    s = SINE[0]
    fig.add_trace(go.Scatter(x=s["t"], y=s["X"][:, 0], mode="lines", line={"color": COLORS[0]},
                             name="signal"), row=1, col=1)
    # enriched: 2 features (offset) over real time + a target star + selector + Δt-marker sizing
    e = EQ[0]
    for i, f in enumerate(["Open", "Close"]):
        idx = e["features"].index(f)
        col = e["X"][:, idx]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm + (1 - i) * 1.1, mode="lines+markers",
                                 line={"color": COLORS[i + 1]},
                                 marker={"size": 4 + 6 * (e["dt"] / e["dt"].max())},
                                 name=f), row=1, col=2)
    fig.add_trace(go.Scatter(x=[e["t"][-1] + 1], y=[2.1], mode="markers",
                             marker={"size": 13, "symbol": "star", "color": COLORS[3]},
                             name="y_reg"), row=1, col=2)
    fig.add_annotation(text="▼ Window 0/200   ▼ Features: [Open, Close]   marker size ∝ Δt",
                       xref="x2 domain", yref="y2 domain", x=0.5, y=1.14, showarrow=False,
                       font={"size": 11, "color": "#333"}, bordercolor="#888", borderwidth=1,
                       borderpad=4, bgcolor="#fff")
    fig.update_xaxes(title_text="time", row=1, col=1)
    fig.update_xaxes(title_text="real time", row=1, col=2)
    fig.update_yaxes(title_text="signal", row=1, col=1)
    fig.update_yaxes(showticklabels=False, title_text="features (offset)", row=1, col=2)
    _style(fig, "Q6 — Scope of the first cut:  minimal  vs  enriched")
    _save(fig, "Q6_scope")


# ================================================================ ROUND 2
# Mockups of the converging design: the two-mode configurable viewer, the overlay
# normalization fix, the full-cross-grid trap, and the Phase-1 minimal cut.
def _control_bar(fig, text):
    fig.add_annotation(text=text, xref="paper", yref="paper", x=0.5, y=1.13, showarrow=False,
                       align="center", font={"size": 11, "color": "#1a1a1a"}, bordercolor="#7a8aa0",
                       borderwidth=1, borderpad=6, bgcolor="#eef3f8")


def _dt_strip(fig, t, dt, row):
    fig.add_trace(go.Bar(x=t, y=dt, marker_color="#bbb", showlegend=False), row=row, col=1)
    fig.update_yaxes(title_text="Δt", row=row, col=1)


def r1a_viewer_compare_signals():
    e, feats = EQ[0], EQ[0]["features"]
    fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], vertical_spacing=0.09,
                        shared_xaxes=True, subplot_titles=("Compare signals · small-multiple · real time", ""))
    for i, f in enumerate(feats):
        col = e["X"][:, i]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm + (len(feats) - 1 - i) * 1.15, mode="lines+markers",
                                 line={"color": COLORS[i]}, marker={"size": 4}, name=f), row=1, col=1)
    _dt_strip(fig, e["t"], e["dt"], 2)
    fig.update_yaxes(showticklabels=False, title_text="signals (offset)", row=1, col=1)
    fig.update_xaxes(title_text="real time (trading day)", row=2, col=1)
    _control_bar(fig, "Compare: [● Signals | ○ Windows]    Signals ▾ [Open,High,Low,Close,Volume]"
                      "    Arrange: [◉ Small-multiple | ○ Overlay]    [ ☐ Show y_reg ]"
                      "    Window ◀ 0/200 ▶")
    _style(fig, "Converged viewer — Compare-signals mode (equities_seq)", 600)
    _save(fig, "R1a_viewer_compare_signals")


def r1b_viewer_compare_windows():
    fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], vertical_spacing=0.09,
                        subplot_titles=("Compare windows · Close overlaid · real time", ""))
    for i in range(3):
        e = EQ[i]
        close = e["X"][:, 3]
        norm = (close - close.min()) / (np.ptp(close) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm, mode="lines+markers", line={"color": COLORS[i]},
                                 marker={"size": 4}, name=f"window {i}"), row=1, col=1)
    _dt_strip(fig, EQ[0]["t"], EQ[0]["dt"], 2)
    fig.update_yaxes(title_text="Close (normalized)", row=1, col=1)
    fig.update_xaxes(title_text="real time", row=2, col=1)
    _control_bar(fig, "Compare: [○ Signals | ● Windows]    Signal ▾ [Close]"
                      "    Windows ▾ [0,1,2 …]    Arrange: [○ Small-multiple | ◉ Overlay]"
                      "    [ ☐ Show y_reg ]")
    _style(fig, "Converged viewer — Compare-windows mode (equities_seq, Close across windows)", 600)
    _save(fig, "R1b_viewer_compare_windows")


def r2_overlay_normalization():
    e, feats = EQ[0], EQ[0]["features"]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.10,
                        subplot_titles=("RAW overlay — Volume dwarfs prices (flat)",
                                        "Per-signal NORMALIZED overlay — all legible"))
    for i, f in enumerate(feats):
        fig.add_trace(go.Scatter(x=e["t"], y=e["X"][:, i], mode="lines", line={"color": COLORS[i]},
                                 name=f, legendgroup=f), row=1, col=1)
    for i, f in enumerate(feats):
        col = e["X"][:, i]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm, mode="lines", line={"color": COLORS[i]},
                                 name=f, legendgroup=f, showlegend=False), row=1, col=2)
    fig.update_yaxes(title_text="raw value", row=1, col=1)
    fig.update_yaxes(title_text="normalized [0,1]", row=1, col=2)
    for c in (1, 2):
        fig.update_xaxes(title_text="trading day", row=1, col=c)
    _style(fig, "Overlay arrangement — raw (Volume dominates) vs per-signal normalized")
    _save(fig, "R2_overlay_normalization")


def r3_full_cross_grid():
    sig_idx = {"Open": 0, "Close": 3, "Volume": 4}
    sigs = list(sig_idx)
    fig = make_subplots(rows=3, cols=3, horizontal_spacing=0.05, vertical_spacing=0.09,
                        column_titles=sigs, row_titles=["window 0", "window 1", "window 2"])
    for r in range(3):
        e = EQ[r]
        for c, s in enumerate(sigs):
            col = e["X"][:, sig_idx[s]]
            norm = (col - col.min()) / (np.ptp(col) + 1e-9)
            fig.add_trace(go.Scatter(x=e["t"], y=norm, mode="lines", line={"color": COLORS[c], "width": 1.3},
                                     showlegend=False), row=r + 1, col=c + 1)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    _style(fig, "Full-cross faceted grid (3 signals × 3 windows) — powerful but cluttered; the trap the two-mode viewer avoids", 600)
    _save(fig, "R3_full_cross_grid")


def r4_phase1_minimal():
    e, feats = EQ[0], EQ[0]["features"]
    fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], vertical_spacing=0.09,
                        shared_xaxes=True, subplot_titles=("Phase-1 minimal — signals small-multiple, real time", ""))
    for i, f in enumerate(feats):
        col = e["X"][:, i]
        norm = (col - col.min()) / (np.ptp(col) + 1e-9)
        fig.add_trace(go.Scatter(x=e["t"], y=norm + (len(feats) - 1 - i) * 1.15, mode="lines",
                                 line={"color": COLORS[i]}, name=f), row=1, col=1)
    _dt_strip(fig, e["t"], e["dt"], 2)
    fig.update_yaxes(showticklabels=False, title_text="signals (offset)", row=1, col=1)
    fig.update_xaxes(title_text="real time", row=2, col=1)
    fig.add_annotation(text="Phase 1 ships this · existing dataset selector + Load only · "
                            "selectors / toggles / window-compare → Phase 2",
                       xref="paper", yref="paper", x=0.5, y=1.10, showarrow=False,
                       font={"size": 11, "color": "#555"})
    _style(fig, "Phase-1 minimal cut — smallest honest 3-D viewer", 560)
    _save(fig, "R4_phase1_minimal")


if __name__ == "__main__":
    print(f"Generating canopy 3-D viz mockups -> {OUT}")
    q1_primary_view()
    q2_multifeature()
    q3_irregular_dt()
    q4_sample_count()
    q5_target()
    q6_scope()
    print("-- round 2 --")
    r1a_viewer_compare_signals()
    r1b_viewer_compare_windows()
    r2_overlay_normalization()
    r3_full_cross_grid()
    r4_phase1_minimal()
    print("done.")
