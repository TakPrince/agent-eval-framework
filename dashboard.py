import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import glob
import os
import requests

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent Eval Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── THEME ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a28;
    --border: #2a2a3d;
    --accent: #7c6aff;
    --accent2: #ff6a9b;
    --accent3: #6affd4;
    --text: #e8e8f0;
    --muted: #6b6b8a;
    --success: #4ade80;
    --warning: #fbbf24;
    --danger: #f87171;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.stApp { background: var(--bg); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}

.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* Header */
.dash-title {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #fff 0%, var(--accent) 60%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.dash-sub {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.3rem;
    font-family: 'Space Mono', monospace;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* Score badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
}
.badge-green { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); }
.badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-red { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }

/* Judge box */
.judge-box {
    background: linear-gradient(135deg, rgba(124,106,255,0.1), rgba(255,106,155,0.05));
    border: 1px solid rgba(124,106,255,0.3);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    font-size: 0.92rem;
    line-height: 1.7;
    margin-top: 0.5rem;
}
.judge-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--accent);
    margin-bottom: 0.5rem;
}

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* Select box */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Section title */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

div[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace;
    color: var(--accent);
}
</style>
""", unsafe_allow_html=True)

# ─── PLOTLY TEMPLATE ────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#e8e8f0", size=12),
    xaxis=dict(gridcolor="#2a2a3d", zerolinecolor="#2a2a3d"),
    yaxis=dict(gridcolor="#2a2a3d", zerolinecolor="#2a2a3d"),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(18,18,26,0.8)", bordercolor="#2a2a3d", borderwidth=1),
)
COLORS = ["#7c6aff", "#ff6a9b", "#6affd4", "#fbbf24", "#f87171", "#60a5fa"]

def hex_to_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


# ─── DATA LOADING ───────────────────────────────────────────────────────────
REPORT_DIR = "evals/reports"

@st.cache_data
def load_json_reports():
    records = []
    for path in glob.glob(f"{REPORT_DIR}/report_*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
            model = os.path.basename(path).replace("report_", "").replace(".json", "")
            for item in data:
                item["_model"] = model
                records.append(item)
        except Exception as e:
            st.warning(f"Could not load {path}: {e}")
    return records

@st.cache_data
def load_excel():
    path = f"{REPORT_DIR}/benchmark.xlsx"
    if os.path.exists(path):
        try:
            return pd.read_excel(path)
        except Exception as e:
            st.warning(f"Could not load Excel: {e}")
    return None

def score_badge(score):
    if score >= 0.8:
        return f'<span class="badge badge-green">✓ {score:.2f}</span>'
    elif score >= 0.5:
        return f'<span class="badge badge-yellow">~ {score:.2f}</span>'
    else:
        return f'<span class="badge badge-red">✗ {score:.2f}</span>'

# ─── LLM JUDGE ──────────────────────────────────────────────────────────────
def llm_judge(model_name: str, results: list, api_key: str) -> str:
    avg_sql    = sum(r.get("final", {}).get("sql_score", 0) for r in results) / max(len(results), 1)
    avg_agent  = sum(r.get("final", {}).get("agent_score", 0) for r in results) / max(len(results), 1)
    avg_perf   = sum(r.get("final", {}).get("performance_score", 0) for r in results) / max(len(results), 1)
    avg_final  = sum(r.get("final", {}).get("final_score", 0) for r in results) / max(len(results), 1)
    exec_match = sum(r.get("sql_eval", {}).get("execution_match", 0) for r in results)
    total      = len(results)

    sample_queries = [r.get("query", "") for r in results[:3]]
    sample_sql     = [r.get("predicted_sql", "") for r in results[:3]]

    prompt = f"""You are an expert AI system evaluator. Analyze the following benchmark results for model "{model_name}" and give a concise, insightful judgment (3-4 sentences). Be specific about strengths and weaknesses. Avoid vague praise.

Model: {model_name}
Total queries tested: {total}
Execution match rate: {exec_match}/{total} ({exec_match/max(total,1)*100:.0f}%)
Average SQL score: {avg_sql:.2f}/1.0
Average agent score: {avg_agent:.2f}/1.0
Average performance score: {avg_perf:.2f}/1.0
Final score: {avg_final:.2f}/1.0

Sample queries tested: {sample_queries}
Sample predicted SQL: {sample_sql}

Give a verdict: Is this model production-ready for NL2SQL tasks? What is its biggest weakness?"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 512,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        return f"Judge failed: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Judge unavailable: {e}"

# ─── BUILD DATAFRAME ─────────────────────────────────────────────────────────
def build_df(records):
    rows = []
    for r in records:
        sql_eval  = r.get("sql_eval", {})
        agent_eval = r.get("agent_eval", {})
        perf_eval = r.get("performance_eval", {})
        final     = r.get("final", {})
        rows.append({
            "model":           r.get("_model", "unknown"),
            "query":           r.get("query", ""),
            "expected_sql":    r.get("expected_sql", ""),
            "predicted_sql":   r.get("predicted_sql", ""),
            "execution_match": sql_eval.get("execution_match", 0),
            "exact_match":     sql_eval.get("exact_match", 0),
            "partial_match":   sql_eval.get("partial_match", 0),
            "sql_score":       sql_eval.get("score", 0),
            "agent_score":     agent_eval.get("score", 0),
            "tool_accuracy":   agent_eval.get("tool_accuracy", 0),
            "failure_rate":    agent_eval.get("failure_rate", 0),
            "latency":         perf_eval.get("latency", 0),
            "latency_score":   perf_eval.get("latency_score", 0),
            "perf_score":      perf_eval.get("score", 0),
            "final_score":     final.get("final_score", 0),
        })
    return pd.DataFrame(rows)

# ─── MAIN ───────────────────────────────────────────────────────────────────
records = load_json_reports()
excel_df = load_excel()

if not records:
    st.error("No report JSON files found in evals/reports/. Run your eval first.")
    st.stop()

df = build_df(records)
models = sorted(df["model"].unique().tolist())

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="dash-title" style="font-size:1.3rem;">⚡ EVAL</p>', unsafe_allow_html=True)
    st.markdown('<p class="dash-sub">Agent Benchmark Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p class="section-title">Filter Models</p>', unsafe_allow_html=True)
    selected_models = st.multiselect("Models", models, default=models, label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<p class="section-title">LLM Judge</p>', unsafe_allow_html=True)
    groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", label_visibility="visible")

    st.markdown("---")
    show_excel = st.checkbox("Show Excel data", value=excel_df is not None)

filtered_df = df[df["model"].isin(selected_models)] if selected_models else df

# ─── HEADER ─────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown('<p class="dash-title">AGENT EVAL DASHBOARD</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="dash-sub">{len(filtered_df)} queries · {len(selected_models)} models · NL2SQL benchmark</p>', unsafe_allow_html=True)
with col_h2:
    best_model = filtered_df.groupby("model")["final_score"].mean().idxmax() if not filtered_df.empty else "—"
    best_score = filtered_df.groupby("model")["final_score"].mean().max() if not filtered_df.empty else 0
    st.markdown(f"""
    <div class="metric-card" style="text-align:right;">
        <div class="metric-val">{best_score:.2f}</div>
        <div class="metric-label">🏆 Best — {best_model}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TOP METRICS ────────────────────────────────────────────────────────────
summary = filtered_df.groupby("model").agg(
    sql_score=("sql_score", "mean"),
    agent_score=("agent_score", "mean"),
    perf_score=("perf_score", "mean"),
    final_score=("final_score", "mean"),
    exec_rate=("execution_match", "mean"),
    avg_latency=("latency", "mean"),
    queries=("query", "count"),
).reset_index()

cols = st.columns(len(selected_models) or 1)
for i, (_, row) in enumerate(summary.iterrows()):
    with cols[i % len(cols)]:
        st.markdown(f"""
        <div class="card">
            <div style="font-family:'Space Mono',monospace;font-size:0.75rem;color:var(--muted);margin-bottom:0.8rem;text-transform:uppercase;letter-spacing:0.08em;">{row['model']}</div>
            <div class="metric-val">{row['final_score']:.2f}</div>
            <div class="metric-label">Final Score</div>
            <div style="margin-top:1rem;display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.8rem;">
                <div>SQL <strong style="color:var(--accent3)">{row['sql_score']:.2f}</strong></div>
                <div>Agent <strong style="color:var(--accent)">{row['agent_score']:.2f}</strong></div>
                <div>Exec <strong style="color:var(--warning)">{row['exec_rate']*100:.0f}%</strong></div>
                <div>Latency <strong style="color:var(--accent2)">{row['avg_latency']:.2f}s</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Charts", "🔍 Query Explorer", "🤖 LLM Judge", "📋 Data Table", "📁 Excel"])

# ══ TAB 1: CHARTS ═══════════════════════════════════════════════════════════
with tab1:
    r1c1, r1c2 = st.columns(2)

    # Radar chart
    with r1c1:
        st.markdown('<p class="section-title">Model Radar — Score Dimensions</p>', unsafe_allow_html=True)
        categories = ["SQL Score", "Agent Score", "Perf Score", "Exec Rate", "Latency Score"]
        fig_radar = go.Figure()
        for i, (_, row) in enumerate(summary.iterrows()):
            vals = [row["sql_score"], row["agent_score"], row["perf_score"], row["exec_rate"], row["perf_score"]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=row["model"],
                line=dict(color=COLORS[i % len(COLORS)], width=2),
                fillcolor=hex_to_rgba(COLORS[i % len(COLORS)], 0.15),
            ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0,1], gridcolor="#2a2a3d", color="#6b6b8a"),
                angularaxis=dict(gridcolor="#2a2a3d", color="#6b6b8a"),
            ),
            **{k: v for k, v in PLOT_LAYOUT.items() if k not in ["xaxis","yaxis"]},
            height=380,
        )
        st.plotly_chart(fig_radar, width='stretch')

    # Bar comparison
    with r1c2:
        st.markdown('<p class="section-title">Score Breakdown by Model</p>', unsafe_allow_html=True)
        fig_bar = go.Figure()
        for i, metric in enumerate(["sql_score", "agent_score", "perf_score"]):
            labels = {"sql_score": "SQL", "agent_score": "Agent", "perf_score": "Performance"}
            fig_bar.add_trace(go.Bar(
                x=summary["model"],
                y=summary[metric],
                name=labels[metric],
                marker_color=COLORS[i],
                marker_line_width=0,
            ))
        fig_bar.update_layout(
            barmode="group",
            **{k: v for k, v in PLOT_LAYOUT.items() if k != "yaxis"},
            height=380,
            yaxis=dict(gridcolor="#2a2a3d", zerolinecolor="#2a2a3d", range=[0, 1.1]),
        )
        st.plotly_chart(fig_bar, width='stretch')

    r2c1, r2c2 = st.columns(2)

    # Execution match pie / donut per model
    with r2c1:
        st.markdown('<p class="section-title">Execution Match Rate</p>', unsafe_allow_html=True)
        fig_exec = go.Figure()
        for i, (_, row) in enumerate(summary.iterrows()):
            fig_exec.add_trace(go.Bar(
                x=[row["model"]],
                y=[row["exec_rate"] * 100],
                name=row["model"],
                marker_color=COLORS[i % len(COLORS)],
                text=[f"{row['exec_rate']*100:.0f}%"],
                textposition="outside",
                marker_line_width=0,
            ))
        fig_exec.update_layout(
            **{k: v for k, v in PLOT_LAYOUT.items() if k != 'yaxis'},
            height=320,
            showlegend=False,
            yaxis=dict(gridcolor="#2a2a3d", zerolinecolor="#2a2a3d", range=[0, 120], title="Execution Match %"),
        )
        st.plotly_chart(fig_exec, width='stretch')

    # Latency comparison
    with r2c2:
        st.markdown('<p class="section-title">Average Latency (seconds)</p>', unsafe_allow_html=True)
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Bar(
            x=summary["model"],
            y=summary["avg_latency"],
            marker=dict(
                color=summary["avg_latency"],
                colorscale=[[0, "#6affd4"], [0.5, "#7c6aff"], [1, "#ff6a9b"]],
                showscale=True,
                colorbar=dict(title="sec", tickfont=dict(color="#6b6b8a")),
            ),
            text=[f"{v:.2f}s" for v in summary["avg_latency"]],
            textposition="outside",
        ))
        fig_lat.update_layout(**PLOT_LAYOUT, height=320, showlegend=False)
        st.plotly_chart(fig_lat, width='stretch')

    # Score distribution box plot
    st.markdown('<p class="section-title">Final Score Distribution per Model</p>', unsafe_allow_html=True)
    fig_box = go.Figure()
    for i, model in enumerate(selected_models):
        mdf = filtered_df[filtered_df["model"] == model]
        fig_box.add_trace(go.Box(
            y=mdf["final_score"],
            name=model,
            marker_color=COLORS[i % len(COLORS)],
            line_color=COLORS[i % len(COLORS)],
            fillcolor=hex_to_rgba(COLORS[i % len(COLORS)], 0.2),
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.5,
        ))
    fig_box.update_layout(**PLOT_LAYOUT, height=350)
    st.plotly_chart(fig_box, width='stretch')

    # Heatmap: per-query scores across models
    if len(selected_models) > 1:
        st.markdown('<p class="section-title">Per-Query Score Heatmap</p>', unsafe_allow_html=True)
        pivot = filtered_df.pivot_table(index="query", columns="model", values="final_score", aggfunc="mean")
        pivot.index = [q[:40] + "..." if len(q) > 40 else q for q in pivot.index]
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, "#f87171"], [0.5, "#fbbf24"], [1, "#4ade80"]],
            zmin=0, zmax=1,
            text=[[f"{v:.2f}" if not pd.isna(v) else "—" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            hovertemplate="Query: %{y}<br>Model: %{x}<br>Score: %{z:.2f}<extra></extra>",
        ))
        fig_heat.update_layout(**{k: v for k, v in PLOT_LAYOUT.items() if k not in ["xaxis","yaxis"]},
            height=max(300, len(pivot) * 35),
            xaxis=dict(side="top"),
        )
        st.plotly_chart(fig_heat, width='stretch')

# ══ TAB 2: QUERY EXPLORER ════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-title">Inspect Individual Queries</p>', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        sel_model = st.selectbox("Model", selected_models)
    with col_f2:
        model_df = filtered_df[filtered_df["model"] == sel_model]
        sel_query = st.selectbox("Query", model_df["query"].tolist())

    row = model_df[model_df["query"] == sel_query].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final Score", f"{row['final_score']:.2f}")
    c2.metric("SQL Score", f"{row['sql_score']:.2f}")
    c3.metric("Exec Match", "✓" if row["execution_match"] else "✗")
    c4.metric("Latency", f"{row['latency']:.2f}s")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Expected SQL**")
        st.code(row["expected_sql"], language="sql")
    with col_r:
        st.markdown("**Predicted SQL**")
        st.code(row["predicted_sql"], language="sql")

    match_cols = st.columns(3)
    match_cols[0].markdown(f"Execution match {score_badge(row['execution_match'])}", unsafe_allow_html=True)
    match_cols[1].markdown(f"Exact match {score_badge(row['exact_match'])}", unsafe_allow_html=True)
    match_cols[2].markdown(f"Partial match {score_badge(row['partial_match'])}", unsafe_allow_html=True)

# ══ TAB 3: LLM JUDGE ════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-title">LLM Judge — Claude Evaluates Each Model</p>', unsafe_allow_html=True)
    st.markdown("Click a model to get Claude's verdict on its performance.")

    judge_model = st.selectbox("Select model to judge", selected_models, key="judge_sel")

    if st.button("⚡ Run Judge", type="primary"):
        if not groq_api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            model_records = [r for r in records if r.get("_model") == judge_model]
            with st.spinner("Groq (llama3-70b) is evaluating..."):
                verdict = llm_judge(judge_model, model_records, groq_api_key)
        st.session_state[f"verdict_{judge_model}"] = verdict

    verdict_key = f"verdict_{judge_model}"
    if verdict_key in st.session_state:
        st.markdown(f"""
        <div class="judge-box">
            <div class="judge-label">⚖️ Claude's Verdict — {judge_model}</div>
            {st.session_state[verdict_key]}
        </div>
        """, unsafe_allow_html=True)

    # Auto-compare all models
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ Judge ALL models & Compare"):
        if not groq_api_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            all_verdicts = {}
            for m in selected_models:
                m_records = [r for r in records if r.get("_model") == m]
                with st.spinner(f"Judging {m}..."):
                    all_verdicts[m] = llm_judge(m, m_records, groq_api_key)
        st.session_state["all_verdicts"] = all_verdicts

    if "all_verdicts" in st.session_state:
        for model_name, verdict in st.session_state["all_verdicts"].items():
            st.markdown(f"""
            <div class="judge-box" style="margin-bottom:1rem;">
                <div class="judge-label">⚖️ {model_name}</div>
                {verdict}
            </div>
            """, unsafe_allow_html=True)

# ══ TAB 4: DATA TABLE ════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-title">Raw Results Table</p>', unsafe_allow_html=True)

    display_cols = ["model", "query", "sql_score", "agent_score", "perf_score",
                    "final_score", "execution_match", "exact_match", "latency"]
    st.dataframe(
        filtered_df[display_cols].sort_values("final_score", ascending=False),
        width='stretch',
        height=500,
    )

    # Download
    csv = filtered_df.to_csv(index=False)
    st.download_button("⬇ Download CSV", csv, "eval_results.csv", "text/csv")

# ══ TAB 5: EXCEL ═════════════════════════════════════════════════════════════
with tab5:
    if show_excel and excel_df is not None:
        st.markdown('<p class="section-title">Excel Benchmark Data</p>', unsafe_allow_html=True)
        st.dataframe(excel_df, width='stretch', height=500)

        # If numeric columns exist, plot them
        num_cols = excel_df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            st.markdown('<p class="section-title">Excel — Numeric Column Chart</p>', unsafe_allow_html=True)
            sel_col = st.selectbox("Column to chart", num_cols)
            fig_xl = px.bar(excel_df, y=sel_col, color_discrete_sequence=COLORS)
            fig_xl.update_layout(**PLOT_LAYOUT, height=350)
            st.plotly_chart(fig_xl, width='stretch')
    else:
        st.info("No Excel file found at evals/reports/benchmark.xlsx, or Excel view is disabled in sidebar.")
        st.markdown("The JSON data is available in the other tabs.")