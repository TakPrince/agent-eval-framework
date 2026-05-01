"""
NL2SQL Evaluation Dashboard
Production-grade multi-agent evaluation framework dashboard.
Load from: evals/reports/report_*.json
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import glob
import os
import re
from typing import Optional

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NL2SQL Eval Framework",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME / CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0c10;
    color: #e2e8f0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 1600px; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d0f14;
    border-right: 1px solid #1a1f2e;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* ── Page header ── */
.dash-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 1.8rem;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid #1a1f2e;
}
.dash-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #7ee8fa 0%, #80ff72 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.dash-sub {
    font-size: 0.78rem;
    color: #4a5568;
    font-family: 'Space Mono', monospace;
    margin-top: 2px;
}

/* ── Metric card ── */
.metric-card {
    background: #111520;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #2d3f60; }
.metric-label {
    font-size: 0.68rem;
    font-family: 'Space Mono', monospace;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.7rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    line-height: 1;
}
.metric-delta {
    font-size: 0.72rem;
    color: #4a5568;
    margin-top: 4px;
}

/* ── Section label ── */
.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.8rem;
    margin-top: 0.4rem;
}

/* ── Card wrapper ── */
.card {
    background: #111520;
    border: 1px solid #1e2535;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

/* ── SQL blocks ── */
.sql-block {
    background: #090b0f;
    border: 1px solid #1a2035;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #a0c4ff;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
    margin-top: 6px;
}

/* ── Insight box ── */
.insight-box {
    background: linear-gradient(135deg, #0d1a2d 0%, #0d1f1a 100%);
    border: 1px solid #1a3040;
    border-left: 3px solid #7ee8fa;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.88rem;
    color: #b2c8d8;
    line-height: 1.65;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-pass { background: #0d2e1a; color: #4ade80; border: 1px solid #166534; }
.badge-fail { background: #2e0d0d; color: #f87171; border: 1px solid #7f1d1d; }
.badge-warn { background: #2e220d; color: #fbbf24; border: 1px solid #78350f; }

/* ── Execution path ── */
.exec-path {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 1rem 1.2rem;
    background: #090b0f;
    border: 1px solid #1a2035;
    border-radius: 10px;
}
.exec-node {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
}
.exec-node-ok  { background: #0d2e1a; color: #4ade80; border: 1px solid #166534; }
.exec-node-err { background: #2e0d0d; color: #f87171; border: 1px solid #7f1d1d; }
.exec-arrow { color: #2d3748; font-size: 1rem; }

/* ── Table ── */
.dataframe { border-radius: 10px; overflow: hidden; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    gap: 6px;
    background: transparent;
    border-bottom: 1px solid #1a1f2e;
}
[data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    padding: 8px 16px;
    color: #4a5568;
    background: transparent;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #7ee8fa;
    background: #111520;
    border-bottom: 2px solid #7ee8fa;
}

/* ── Selectbox / Input ── */
[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label  { font-size: 0.75rem; color: #4a5568; font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PLOTLY DARK TEMPLATE
# ─────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#94a3b8", size=12),
    xaxis=dict(gridcolor="#1a1f2e", zerolinecolor="#1a1f2e", linecolor="#1a1f2e"),
    yaxis=dict(gridcolor="#1a1f2e", zerolinecolor="#1a1f2e", linecolor="#1a1f2e"),
    margin=dict(l=30, r=20, t=40, b=30),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    colorway=["#7ee8fa", "#80ff72", "#f6a623", "#f87171", "#a78bfa", "#38bdf8"],
)

ACCENT_GRADIENT = ["#7ee8fa", "#5bc8e8", "#38a8c8", "#1a88a8", "#80ff72"]


# ─────────────────────────────────────────────
# SAFE ACCESSORS
# ─────────────────────────────────────────────
def safe_get(d: dict, *keys, default=None):
    """Safely traverse nested dict keys."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_reports(report_dir: str = "evals/reports") -> list[dict]:
    pattern = os.path.join(report_dir, "report_*.json")
    files = sorted(glob.glob(pattern))
    records = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                records.extend(data)
            elif isinstance(data, dict):
                records.append(data)
        except Exception as e:
            st.sidebar.warning(f"⚠ Could not load `{os.path.basename(f)}`: {e}")
    return records


def flatten_records(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        final     = r.get("final", {}) or {}
        traj      = final.get("trajectory_eval", {}) or {}
        sql_eval  = r.get("sql_eval", {}) or {}
        agent_eval= r.get("agent_eval", {}) or {}
        perf_eval = r.get("performance_eval", {}) or {}

        rows.append({
            "model":             r.get("model", "unknown"),
            "query":             r.get("query", ""),
            "predicted_sql":     r.get("predicted_sql", ""),
            "expected_sql":      r.get("expected_sql", ""),
            "final_score":       safe_float(final.get("final_score")),
            "ves_score":         safe_float(final.get("ves_score")),
            "adjusted_score":    safe_float(final.get("adjusted_score")),
            "trajectory_score":  safe_float(traj.get("trajectory_score")),
            "step_count":        int(traj.get("step_count", 0)),
            "error_steps":       int(traj.get("error_steps", 0)),
            "recovery_attempts": int(traj.get("recovery_attempts", 0)),
            "sql_score":         safe_float(sql_eval.get("score", sql_eval.get("sql_score"))),
            "agent_score":       safe_float(agent_eval.get("score", agent_eval.get("agent_score"))),
            "execution_match":   bool(sql_eval.get("execution_match", False)),
            "latency":           safe_float(perf_eval.get("latency_seconds", perf_eval.get("latency", 0))),
            "insight":           r.get("insight", ""),
            "steps":             r.get("steps", []),
            "_raw":              r,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# EXECUTION PATH BUILDER
# ─────────────────────────────────────────────
def build_exec_path_html(steps: list) -> str:
    if not steps:
        return "<span style='color:#4a5568;font-size:0.8rem'>No steps recorded</span>"

    nodes = []
    for i, step in enumerate(steps):
        name   = step.get("agent_name", step.get("name", f"step_{i}"))
        status = step.get("status", "ok").lower()
        is_err = status in ("error", "fail", "failed", "retry")
        is_retry = step.get("is_retry", False) or "retry" in name.lower()

        if is_retry:
            css = "exec-node-err"
            icon = "↩"
            label = f"retry"
        elif is_err:
            css = "exec-node-err"
            icon = "✗"
            label = name
        else:
            css = "exec-node-ok"
            icon = "✓"
            label = name

        node = f'<span class="exec-node {css}">{icon} {label}</span>'
        nodes.append(node)

        if i < len(steps) - 1:
            nodes.append('<span class="exec-arrow">→</span>')

    return '<div class="exec-path">' + "".join(nodes) + "</div>"


# ─────────────────────────────────────────────
# COLOUR SCALE FOR SCORES
# ─────────────────────────────────────────────
def score_color(val: float) -> str:
    if val >= 0.85:
        return "#4ade80"
    elif val >= 0.65:
        return "#fbbf24"
    else:
        return "#f87171"


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="dash-title" style="font-size:1rem">⚡ NL2SQL Eval</div>', unsafe_allow_html=True)
    st.markdown("---")

    report_dir = st.text_input("Reports directory", value="evals/reports")
    records    = load_reports(report_dir)

    if not records:
        st.error("No report_*.json files found.")
        st.stop()

    df = flatten_records(records)

    all_models = sorted(df["model"].unique().tolist())
    sel_models = st.multiselect("Filter models", all_models, default=all_models)
    if sel_models:
        df = df[df["model"].isin(sel_models)]

    st.markdown("---")
    st.markdown(f'<div class="section-label">Loaded</div>', unsafe_allow_html=True)
    st.markdown(f"**{len(records)}** records · **{len(all_models)}** models")


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div>
        <div class="dash-title">NL2SQL Evaluation Framework</div>
        <div class="dash-sub">multi-agent · trajectory · scoring</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_overview, tab_analytics, tab_query, tab_trajectory, tab_retry, tab_table = st.tabs([
    "📊 Model Overview",
    "📈 Analytics",
    "🔍 Query Explorer",
    "🛤️ Trajectory",
    "🔁 Retry Analysis",
    "📋 Data Table",
])


# ════════════════════════════════════════════
# TAB 1 — MODEL OVERVIEW
# ════════════════════════════════════════════
with tab_overview:
    model_stats = (
        df.groupby("model")
        .agg(
            final_score      =("final_score",       "mean"),
            sql_score        =("sql_score",          "mean"),
            agent_score      =("agent_score",        "mean"),
            ves_score        =("ves_score",          "mean"),
            trajectory_score =("trajectory_score",   "mean"),
            execution_rate   =("execution_match",    "mean"),
            avg_latency      =("latency",            "mean"),
            count            =("query",              "count"),
        )
        .reset_index()
        .sort_values("final_score", ascending=False)
    )

    for _, row in model_stats.iterrows():
        model_name = row["model"]
        st.markdown(f'<div class="section-label">{model_name}</div>', unsafe_allow_html=True)

        cols = st.columns(7)
        metrics = [
            ("Final Score",       row["final_score"],       ""),
            ("SQL Score",         row["sql_score"],         ""),
            ("Agent Score",       row["agent_score"],       ""),
            ("VES Score",         row["ves_score"],         ""),
            ("Trajectory",        row["trajectory_score"],  ""),
            ("Exec Rate",         row["execution_rate"],    ""),
            ("Avg Latency (s)",   row["avg_latency"],       "s"),
        ]
        for col, (label, val, unit) in zip(cols, metrics):
            color = score_color(val) if unit != "s" else "#7ee8fa"
            val_str = f"{val:.3f}{unit}" if unit == "s" else f"{val:.3f}"
            col.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color}">{val_str}</div>
                <div class="metric-delta">{int(row['count'])} queries</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)


# ════════════════════════════════════════════
# TAB 2 — ANALYTICS
# ════════════════════════════════════════════
with tab_analytics:

    model_stats2 = (
        df.groupby("model")
        .agg(
            final_score      =("final_score",       "mean"),
            sql_score        =("sql_score",          "mean"),
            agent_score      =("agent_score",        "mean"),
            ves_score        =("ves_score",          "mean"),
            trajectory_score =("trajectory_score",   "mean"),
        )
        .reset_index()
    )

    # ── Row 1: Radar + Bar ──
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-label">Score Radar</div>', unsafe_allow_html=True)
        categories = ["SQL Score", "Agent Score", "VES Score", "Trajectory", "Final Score"]
        fig_radar  = go.Figure()
        for _, row in model_stats2.iterrows():
            vals = [
                row["sql_score"], row["agent_score"],
                row["ves_score"], row["trajectory_score"], row["final_score"],
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=row["model"],
                opacity=0.7,
                line=dict(width=2),
            ))
        fig_radar.update_layout(
            **PLOTLY_LAYOUT,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                angularaxis=dict(color="#2d3748", gridcolor="#1a1f2e"),
                radialaxis=dict(color="#2d3748", gridcolor="#1a1f2e", range=[0, 1]),
            ),
            showlegend=True,
            height=340,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with c2:
        st.markdown('<div class="section-label">Score Breakdown</div>', unsafe_allow_html=True)
        score_cols = ["sql_score", "agent_score", "ves_score", "trajectory_score", "final_score"]
        labels     = ["SQL", "Agent", "VES", "Trajectory", "Final"]
        fig_bar    = go.Figure()
        for i, (col, label) in enumerate(zip(score_cols, labels)):
            fig_bar.add_trace(go.Bar(
                name=label,
                x=model_stats2["model"],
                y=model_stats2[col],
                marker_color=PLOTLY_LAYOUT["colorway"][i],
                marker_line_width=0,
            ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            barmode="group",
            height=340,
            xaxis_tickangle=-25,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Row 2: Scatter + Box ──
    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-label">Final Score vs VES Score</div>', unsafe_allow_html=True)
        fig_scatter = px.scatter(
            df,
            x="final_score",
            y="ves_score",
            color="model",
            hover_data=["query"],
            opacity=0.75,
            size_max=10,
        )
        fig_scatter.update_traces(marker=dict(size=8, line=dict(width=0)))
        fig_scatter.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c4:
        st.markdown('<div class="section-label">Score Distribution</div>', unsafe_allow_html=True)
        fig_box = go.Figure()
        for model in df["model"].unique():
            mdf = df[df["model"] == model]
            fig_box.add_trace(go.Box(
                y=mdf["final_score"],
                name=model,
                boxmean="sd",
                line_width=1.5,
            ))
        fig_box.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Row 3: Heatmap ──
    st.markdown('<div class="section-label">Query × Model Performance Heatmap</div>', unsafe_allow_html=True)
    pivot = df.pivot_table(index="query", columns="model", values="final_score", aggfunc="mean")
    if not pivot.empty:
        # truncate long queries
        pivot.index = [q[:55] + "…" if len(q) > 55 else q for q in pivot.index]
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, "#1a0a0a"], [0.5, "#1a2d1a"], [1, "#4ade80"]],
            zmin=0, zmax=1,
            text=[[f"{v:.2f}" if pd.notna(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont=dict(size=9, family="Space Mono"),
            showscale=True,
            colorbar=dict(
                tickfont=dict(color="#4a5568"),
                outlinecolor="rgba(0,0,0,0)",
            ),
        ))
        heatmap_layout = {**PLOTLY_LAYOUT, "xaxis": {**PLOTLY_LAYOUT.get("xaxis", {}), "side": "top"}}
        fig_heat.update_layout(
            **heatmap_layout,
            height=max(300, 30 * len(pivot) + 80),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Not enough data for heatmap (need multiple models × queries).")


# ════════════════════════════════════════════
# TAB 3 — QUERY EXPLORER
# ════════════════════════════════════════════
with tab_query:
    qc1, qc2 = st.columns([1, 2])

    with qc1:
        model_sel = st.selectbox("Select model", sorted(df["model"].unique()))

    model_df = df[df["model"] == model_sel]
    queries  = model_df["query"].unique().tolist()

    with qc2:
        query_sel = st.selectbox("Select query", queries)

    row = model_df[model_df["query"] == query_sel].iloc[0]

    st.markdown("---")

    # ── Score badges ──
    b1, b2, b3, b4, b5 = st.columns(5)
    score_items = [
        ("Final",      row["final_score"]),
        ("SQL",        row["sql_score"]),
        ("Agent",      row["agent_score"]),
        ("VES",        row["ves_score"]),
        ("Trajectory", row["trajectory_score"]),
    ]
    for col, (label, val) in zip([b1, b2, b3, b4, b5], score_items):
        color = score_color(val)
        col.markdown(f"""
        <div class="metric-card" style="text-align:center">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};font-size:1.3rem">{val:.3f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Execution match ──
    ex_badge = (
        '<span class="badge badge-pass">✓ EXECUTION MATCH</span>'
        if row["execution_match"]
        else '<span class="badge badge-fail">✗ NO EXECUTION MATCH</span>'
    )
    st.markdown(ex_badge, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── SQL blocks ──
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown('<div class="section-label">Expected SQL</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sql-block">{row["expected_sql"] or "—"}</div>', unsafe_allow_html=True)
    with sc2:
        st.markdown('<div class="section-label">Predicted SQL</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sql-block">{row["predicted_sql"] or "—"}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Execution path ──
    st.markdown('<div class="section-label">Execution Path</div>', unsafe_allow_html=True)
    st.markdown(build_exec_path_html(row["steps"]), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Insight ──
    st.markdown('<div class="section-label">LLM Insight</div>', unsafe_allow_html=True)
    insight = row["insight"] or "No insight recorded for this query."
    st.markdown(f'<div class="insight-box">💡 {insight}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════
# TAB 4 — TRAJECTORY
# ════════════════════════════════════════════
with tab_trajectory:

    # ── KPI row ──
    tk1, tk2, tk3, tk4 = st.columns(4)
    kpis = [
        ("Avg Step Count",       df["step_count"].mean(),        "#7ee8fa"),
        ("Avg Error Steps",      df["error_steps"].mean(),       "#f87171"),
        ("Avg Recoveries",       df["recovery_attempts"].mean(), "#fbbf24"),
        ("Avg Trajectory Score", df["trajectory_score"].mean(),  "#4ade80"),
    ]
    for col, (label, val, color) in zip([tk1, tk2, tk3, tk4], kpis):
        col.markdown(f"""
        <div class="metric-card" style="text-align:center">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};font-size:1.4rem">{val:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bar: trajectory score per model ──
    st.markdown('<div class="section-label">Trajectory Score by Model</div>', unsafe_allow_html=True)
    traj_model = (
        df.groupby("model")
        .agg(trajectory_score=("trajectory_score", "mean"),
             error_steps=("error_steps", "mean"),
             recovery_attempts=("recovery_attempts", "mean"))
        .reset_index()
        .sort_values("trajectory_score", ascending=False)
    )
    fig_traj = go.Figure()
    fig_traj.add_trace(go.Bar(
        x=traj_model["model"], y=traj_model["trajectory_score"],
        name="Trajectory Score", marker_color="#7ee8fa",
    ))
    fig_traj.add_trace(go.Bar(
        x=traj_model["model"], y=traj_model["error_steps"],
        name="Avg Error Steps", marker_color="#f87171",
    ))
    fig_traj.add_trace(go.Bar(
        x=traj_model["model"], y=traj_model["recovery_attempts"],
        name="Avg Recoveries", marker_color="#fbbf24",
    ))
    fig_traj.update_layout(**PLOTLY_LAYOUT, barmode="group", height=300)
    st.plotly_chart(fig_traj, use_container_width=True)

    # ── Trajectory table ──
    st.markdown('<div class="section-label">Trajectory Detail Table</div>', unsafe_allow_html=True)

    def build_path_text(steps: list) -> str:
        if not steps:
            return "—"
        parts = []
        for s in steps:
            name   = s.get("agent_name", s.get("name", "?"))
            status = s.get("status", "ok").lower()
            is_err = status in ("error", "fail", "failed")
            parts.append(f"{'✗' if is_err else '✓'} {name}")
        return " → ".join(parts)

    traj_table = df[["model", "query", "step_count", "error_steps",
                      "recovery_attempts", "trajectory_score", "steps"]].copy()
    traj_table["path"] = traj_table["steps"].apply(build_path_text)
    traj_table = traj_table.drop(columns=["steps"])
    traj_table["query"] = traj_table["query"].str[:60] + "…"
    traj_table = traj_table.rename(columns={
        "model": "Model", "query": "Query",
        "step_count": "Steps", "error_steps": "Errors",
        "recovery_attempts": "Retries", "trajectory_score": "Score",
        "path": "Path",
    })
    st.dataframe(
        traj_table.sort_values("Score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


# ════════════════════════════════════════════
# TAB 5 — RETRY ANALYSIS
# ════════════════════════════════════════════
with tab_retry:

    has_retries = df["recovery_attempts"].sum() > 0

    if not has_retries:
        st.info("No retry / recovery attempts detected in the loaded reports.")
    else:
        rc1, rc2 = st.columns(2)

        with rc1:
            st.markdown('<div class="section-label">Retry Distribution by Model</div>', unsafe_allow_html=True)
            retry_dist = (
                df.groupby("model")["recovery_attempts"]
                .value_counts()
                .reset_index(name="count")
            )
            fig_retry = px.bar(
                retry_dist,
                x="model", y="count",
                color="recovery_attempts",
                barmode="stack",
                color_continuous_scale=["#1a1f2e", "#f87171"],
            )
            fig_retry.update_layout(**PLOTLY_LAYOUT, height=300)
            st.plotly_chart(fig_retry, use_container_width=True)

        with rc2:
            st.markdown('<div class="section-label">Recovery Success Rate</div>', unsafe_allow_html=True)
            # queries with retries that have execution_match = True → recovered
            retry_df = df[df["recovery_attempts"] > 0].copy()
            success  = retry_df["execution_match"].mean() if not retry_df.empty else 0
            fail_r   = 1 - success
            fig_pie  = go.Figure(go.Pie(
                labels=["Recovered ✓", "Failed ✗"],
                values=[success, fail_r],
                hole=0.55,
                marker=dict(colors=["#4ade80", "#f87171"]),
                textfont=dict(size=12, family="Space Mono"),
            ))
            fig_pie.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Detail table
        st.markdown('<div class="section-label">Queries with Retries</div>', unsafe_allow_html=True)
        st.dataframe(
            retry_df[["model", "query", "recovery_attempts", "execution_match",
                       "final_score", "trajectory_score"]]
            .rename(columns={
                "model": "Model", "query": "Query",
                "recovery_attempts": "Retries", "execution_match": "Recovered",
                "final_score": "Final", "trajectory_score": "Traj",
            })
            .sort_values("Retries", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


# ════════════════════════════════════════════
# TAB 6 — DATA TABLE
# ════════════════════════════════════════════
with tab_table:
    st.markdown('<div class="section-label">Full Evaluation Records</div>', unsafe_allow_html=True)

    display_cols = [
        "model", "query", "final_score", "sql_score", "agent_score",
        "ves_score", "adjusted_score", "trajectory_score",
        "execution_match", "step_count", "error_steps", "recovery_attempts", "latency",
    ]
    display_df = df[[c for c in display_cols if c in df.columns]].copy()
    display_df["query"] = display_df["query"].str[:70] + "…"

    # colour-map numeric cols
    numeric_cols = ["final_score", "sql_score", "agent_score", "ves_score",
                    "adjusted_score", "trajectory_score"]

    def colour_score(val):
        if isinstance(val, float):
            c = score_color(val)
            return f"color: {c}"
        return ""

    styled = display_df.style.map(colour_score, subset=[c for c in numeric_cols if c in display_df.columns])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

    # Download
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name="nl2sql_eval_results.csv",
        mime="text/csv",
    )