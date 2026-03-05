import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="State Analysis", page_icon="📊", layout="wide")

# ── Shared CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f7f8fa; }
    .block-container { padding: 2rem 3rem; max-width: 1300px; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ebebeb; }
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #ebebeb;
        border-radius: 12px; padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] { color: #111 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #999 !important; font-size: 0.78rem !important; }
    [data-testid="stMetricDelta"] { color: #2e7d32 !important; font-size: 0.78rem !important; }
    hr { border-color: #ebebeb !important; margin: 1.5rem 0; }
    .kicker { font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: #2e7d32; margin-bottom: 4px; }
    .page-title { font-size: 1.6rem; font-weight: 700; color: #111; letter-spacing: -0.3px; margin: 0; }
    .page-sub { font-size: 0.85rem; color: #888; margin: 4px 0 0 0; }
    .filter-bar {
        background: #ffffff; border: 1px solid #ebebeb; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .insight-pill {
        background: #f0faf0; border: 1px solid #c8e6c9; border-radius: 8px;
        padding: 10px 16px; font-size: 0.8rem; color: #2e7d32;
        font-weight: 500; margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    os.chdir('/Users/manaskolaskar/Developer/projects/india-ev-adoption')
    sales = pd.read_csv('data/raw/EV_Ice_Market_Sales_India.csv')
    sales['ev_share_pct'] = (sales['ev_sales'] / sales['total_sales'] * 100).round(2)
    sales['ice_share_pct'] = (sales['ice_sales'] / sales['total_sales'] * 100).round(2)
    master = pd.read_csv('data/processed/master_ev_data.csv')
    return sales, master

sales, master = load_data()

# ── Header ────────────────────────────────────────────────────────────
st.markdown('<p class="kicker">State Analysis</p>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">EV vs ICE — How are states performing?</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Select states and segments to explore adoption trends interactively</p>', unsafe_allow_html=True)

st.divider()

# ── Filters ───────────────────────────────────────────────────────────
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns([2, 2, 1])

with fc1:
    selected_states = st.multiselect(
        "States",
        options=sorted(sales['state'].unique()),
        default=sorted(sales['state'].unique()),
        key="states_filter"
    )
with fc2:
    selected_segments = st.multiselect(
        "Vehicle Segments",
        options=['2W', '3W', '4W'],
        default=['2W', '3W', '4W'],
        key="segments_filter"
    )
with fc3:
    metric = st.selectbox(
        "Metric",
        options=["EV Share %", "EV Sales (units)", "ICE Sales (units)"],
        key="metric_filter"
    )
st.markdown('</div>', unsafe_allow_html=True)

# Filter data
filtered = sales[
    (sales['state'].isin(selected_states)) &
    (sales['vehicle_segment'].isin(selected_segments))
]

metric_col = {
    "EV Share %": "ev_share_pct",
    "EV Sales (units)": "ev_sales",
    "ICE Sales (units)": "ice_sales"
}[metric]

# ── Top Metrics (dynamic) ─────────────────────────────────────────────
agg = filtered.groupby('year')[metric_col].mean().reset_index()
latest = filtered[filtered['year'] == 2024].groupby('state')[metric_col].mean()
prev   = filtered[filtered['year'] == 2023].groupby('state')[metric_col].mean()

m1, m2, m3, m4 = st.columns(4)
with m1:
    val = filtered[filtered['year'] == 2024][metric_col].mean()
    prev_val = filtered[filtered['year'] == 2023][metric_col].mean()
    delta = round(val - prev_val, 2)
    label = "%" if "Share" in metric else " units"
    st.metric(f"Avg {metric} (2024)", f"{val:.1f}{label}", f"{delta:+.1f} vs 2023")

with m2:
    top_state = latest.idxmax() if len(latest) > 0 else "—"
    top_val   = latest.max() if len(latest) > 0 else 0
    st.metric("Top State 2024", top_state, f"{top_val:.1f}{'%' if 'Share' in metric else ''}")

with m3:
    bot_state = latest.idxmin() if len(latest) > 0 else "—"
    bot_val   = latest.min() if len(latest) > 0 else 0
    st.metric("Lowest State 2024", bot_state, f"{bot_val:.1f}{'%' if 'Share' in metric else ''}")

with m4:
    total_ev = filtered['ev_sales'].sum()
    st.metric("Total EV Sales", f"{total_ev:,.0f}", "Selected states & years")

st.divider()

# ── Chart Row 1: Line + Bar ───────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("**EV Adoption Trend Over Time**")
    trend_data = filtered.groupby(['year', 'state'])[metric_col].mean().reset_index()

    fig_line = px.line(
        trend_data, x='year', y=metric_col, color='state',
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={metric_col: metric, 'year': 'Year', 'state': 'State'}
    )
    fig_line.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter', size=12),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode='x unified',
        xaxis=dict(showgrid=False, tickmode='linear'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
    )
    fig_line.update_traces(line_width=2.5, marker_size=6)
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.markdown("**2024 State Comparison**")
    bar_data = filtered[filtered['year'] == 2024].groupby('state')[metric_col].mean().reset_index()
    bar_data = bar_data.sort_values(metric_col, ascending=True)

    fig_bar = px.bar(
        bar_data, x=metric_col, y='state',
        orientation='h',
        color=metric_col,
        color_continuous_scale=['#c8e6c9', '#1b5e20'],
        labels={metric_col: metric, 'state': ''},
    )
    fig_bar.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter', size=12),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Chart Row 2: Segment + Stacked ───────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("**EV Share by Vehicle Segment Over Time**")
    seg_data = filtered.groupby(['year', 'vehicle_segment'])['ev_share_pct'].mean().reset_index()

    fig_seg = px.line(
        seg_data, x='year', y='ev_share_pct', color='vehicle_segment',
        markers=True,
        color_discrete_map={'2W': '#2e7d32', '3W': '#66bb6a', '4W': '#a5d6a7'},
        labels={'ev_share_pct': 'EV Share %', 'year': 'Year', 'vehicle_segment': 'Segment'}
    )
    fig_seg.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter', size=12),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, tickmode='linear'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
    )
    fig_seg.update_traces(line_width=2.5, marker_size=6)
    st.plotly_chart(fig_seg, use_container_width=True)

with col4:
    st.markdown("**EV vs ICE Split — Latest Year (2024)**")
    split_data = filtered[filtered['year'] == 2024].groupby('state').agg(
        EV=('ev_sales', 'sum'),
        ICE=('ice_sales', 'sum')
    ).reset_index()
    split_melted = split_data.melt(id_vars='state', value_vars=['EV', 'ICE'], var_name='Type', value_name='Sales')

    fig_stacked = px.bar(
        split_melted, x='state', y='Sales', color='Type',
        barmode='stack',
        color_discrete_map={'EV': '#2e7d32', 'ICE': '#e0e0e0'},
        labels={'Sales': 'Units Sold', 'state': '', 'Type': ''}
    )
    fig_stacked.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter', size=12),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
    )
    st.plotly_chart(fig_stacked, use_container_width=True)

# ── Insight pills ─────────────────────────────────────────────────────
st.divider()
st.markdown('<p class="kicker">Auto Insights from Selected Data</p>', unsafe_allow_html=True)

i1, i2, i3 = st.columns(3)
with i1:
    top = filtered.groupby('state')['ev_share_pct'].mean().idxmax()
    val = filtered.groupby('state')['ev_share_pct'].mean().max()
    st.markdown(f'<div class="insight-pill">🏆 <strong>{top}</strong> has the highest average EV share at <strong>{val:.1f}%</strong> across all selected years</div>', unsafe_allow_html=True)

with i2:
    seg_avg = filtered.groupby('vehicle_segment')['ev_share_pct'].mean()
    top_seg = seg_avg.idxmax()
    st.markdown(f'<div class="insight-pill">🚗 <strong>{top_seg}</strong> segment leads EV adoption with avg <strong>{seg_avg[top_seg]:.1f}%</strong> share</div>', unsafe_allow_html=True)

with i3:
    yoy = filtered.groupby('year')['ev_share_pct'].mean()
    best_year = yoy.diff().idxmax()
    best_growth = yoy.diff().max()
    st.markdown(f'<div class="insight-pill">📈 Biggest growth year was <strong>{int(best_year)}</strong> with avg <strong>+{best_growth:.1f}%</strong> increase in EV share</div>', unsafe_allow_html=True)