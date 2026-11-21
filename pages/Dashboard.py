import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.file_handler import load_medicines, load_sales, load_stock_movements
from utils.analytics import get_kpi_metrics

st.markdown("<div class='page-eyebrow'>MEDIFLOW / OVERVIEW</div>", unsafe_allow_html=True)
st.title("Pharmacy command center")
st.caption(f"Inventory, sales and expiry performance · {dt.date.today().strftime('%A, %d %B %Y')}")

meds = load_medicines()
sales = load_sales()
kpi = get_kpi_metrics()

# Filters apply to visual analysis without changing the underlying records.
with st.container(border=True):
    f1, f2 = st.columns([1, 1])
    categories = sorted(meds["Category"].dropna().astype(str).unique()) if not meds.empty else []
    selected_categories = f1.multiselect("Filter categories", categories, default=categories, placeholder="All categories")
    period = f2.selectbox("Sales period", ["Last 30 days", "Last 90 days", "This year", "All time"], index=0)

filtered_meds = meds[meds["Category"].isin(selected_categories)] if not meds.empty and selected_categories else (meds.iloc[0:0] if not selected_categories else meds)
filtered_sales = sales.copy()
if not filtered_sales.empty:
    filtered_sales["Sale Date"] = pd.to_datetime(filtered_sales["Sale Date"], errors="coerce")
    today = pd.Timestamp.today().normalize()
    if period == "Last 30 days": filtered_sales = filtered_sales[filtered_sales["Sale Date"] >= today - pd.Timedelta(days=30)]
    elif period == "Last 90 days": filtered_sales = filtered_sales[filtered_sales["Sale Date"] >= today - pd.Timedelta(days=90)]
    elif period == "This year": filtered_sales = filtered_sales[filtered_sales["Sale Date"].dt.year == today.year]

st.markdown("### At a glance")
metrics = [
    ("Medicine SKUs", f"{len(filtered_meds):,}", "Unique inventory records", "💊"),
    ("Units in stock", f"{int(pd.to_numeric(filtered_meds.get('Quantity', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()):,}", "Across selected categories", "📦"),
    ("Low-stock items", f"{kpi['low_stock']:,}", "Below 20 units", "⚠️"),
    ("Expiry attention", f"{kpi['expired'] + kpi['expiring_soon']:,}", f"{kpi['expired']} expired · {kpi['expiring_soon']} due soon", "⏳"),
]
cols = st.columns(4)
for col, (label, value, hint, icon) in zip(cols, metrics):
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-icon'>{icon}</div><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-hint'>{hint}</div></div>", unsafe_allow_html=True)

st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
rev = float(pd.to_numeric(filtered_sales.get("Total Amount", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not filtered_sales.empty else 0.0
units_sold = int(pd.to_numeric(filtered_sales.get("Quantity Sold", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not filtered_sales.empty else 0
r1, r2, r3 = st.columns(3)
r1.metric("Revenue in selected period", f"₹{rev:,.2f}")
r2.metric("Units sold", f"{units_sold:,}")
r3.metric("Invoices", f"{len(filtered_sales):,}")

left, right = st.columns([1.45, 1])
with left:
    st.markdown("### Revenue performance")
    if not filtered_sales.empty:
        trend = filtered_sales.dropna(subset=["Sale Date"]).groupby("Sale Date", as_index=False)["Total Amount"].sum().sort_values("Sale Date")
        fig = px.area(trend, x="Sale Date", y="Total Amount", markers=True, color_discrete_sequence=["#0f9d8a"])
        fig.update_layout(height=330, margin=dict(l=8,r=8,t=18,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Revenue (₹)")
        fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="rgba(148,163,184,.18)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else: st.info("No sales found for this period.")
with right:
    st.markdown("### Inventory mix")
    if not filtered_meds.empty:
        cat = filtered_meds.groupby("Category", dropna=False)["Medicine ID"].count().reset_index(name="SKUs")
        fig = px.pie(cat, names="Category", values="SKUs", hole=.66, color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(height=330, margin=dict(l=5,r=5,t=18,b=5), showlegend=True, legend_title=None, paper_bgcolor="rgba(0,0,0,0)")
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else: st.info("No inventory records in this selection.")

low = filtered_meds[pd.to_numeric(filtered_meds.get("Quantity", pd.Series(dtype=float)), errors="coerce").fillna(0) < 20].copy() if not filtered_meds.empty else pd.DataFrame()
exp = filtered_meds.copy()
if not exp.empty:
    exp["Expiry Date"] = pd.to_datetime(exp["Expiry Date"], errors="coerce")
    exp = exp[exp["Expiry Date"].notna() & (exp["Expiry Date"].dt.date <= dt.date.today() + dt.timedelta(days=30))].sort_values("Expiry Date")

st.markdown("### Needs attention")
a, b = st.columns(2)
with a:
    st.markdown("**Low stock**")
    if low.empty: st.success("No low-stock products in this category selection.")
    else: st.dataframe(low[["Medicine ID", "Medicine Name", "Quantity", "Category"]].sort_values("Quantity"), use_container_width=True, hide_index=True)
with b:
    st.markdown("**Expired / expiring within 30 days**")
    if exp.empty: st.success("No expiry alerts in this category selection.")
    else: st.dataframe(exp[["Medicine ID", "Medicine Name", "Expiry Date", "Quantity"]], use_container_width=True, hide_index=True)

with st.expander("Recent stock movements"):
    movements = load_stock_movements(12)
    if movements.empty: st.info("No stock movements recorded yet.")
    else: st.dataframe(movements, use_container_width=True, hide_index=True)
