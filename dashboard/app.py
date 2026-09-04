"""Streamlit dashboard — interactive BI reporting for Sales Analytics."""

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from analytics import (
    compare_query_performance,
    get_category_breakdown,
    get_kpi_summary,
    get_monthly_trend,
    get_regional_performance,
    get_segment_channel_analysis,
    get_top_products,
    numpy_statistical_summary,
)
from config import DB_PATH

st.set_page_config(
    page_title="Sales Analytics | BI Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = px.colors.qualitative.Set2


@st.cache_data(ttl=300)
def load_kpis(year):
    return get_kpi_summary(year)


@st.cache_data(ttl=300)
def load_monthly(year):
    return get_monthly_trend(year)


@st.cache_data(ttl=300)
def load_regions(year):
    return get_regional_performance(year)


@st.cache_data(ttl=300)
def load_categories(year):
    return get_category_breakdown(year)


@st.cache_data(ttl=300)
def load_segment_channel(year):
    return get_segment_channel_analysis(year)


@st.cache_data(ttl=300)
def load_top_products(year):
    return get_top_products(10, year)


def format_currency(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def render_kpi_cards(kpis: dict):
    cols = st.columns(5)
    metrics = [
        ("Total Revenue", format_currency(kpis["total_revenue"]), "💰"),
        ("Total Profit", format_currency(kpis["total_profit"]), "📈"),
        ("Total Orders", f"{kpis['total_orders']:,}", "🛒"),
        ("Avg Order Value", format_currency(kpis["avg_order_value"]), "🏷️"),
        ("Profit Margin", f"{kpis['profit_margin_pct']:.1f}%", "📊"),
    ]
    for col, (label, value, icon) in zip(cols, metrics):
        col.metric(f"{icon} {label}", value)


def main():
    if not DB_PATH.exists():
        st.error("Database not found. Run `python python/generate_data.py` first.")
        st.code("cd \"Business Intelligence\" && python python/generate_data.py", language="bash")
        st.stop()

    st.sidebar.title("📊 Sales Analytics")
    st.sidebar.markdown("**Business Intelligence Platform**")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        ["Executive Overview", "Regional Analysis", "Product Insights", "Customer Segments", "SQL Performance"],
    )

    years = [None, 2025, 2024, 2023, 2022]
    year_labels = ["All Time", "2025", "2024", "2023", "2022"]
    selected_label = st.sidebar.selectbox("Time Period", year_labels)
    year = years[year_labels.index(selected_label)]

    st.sidebar.divider()
    st.sidebar.caption("250,000+ sales records | Python · SQL · Pandas · NumPy")

    if page == "Executive Overview":
        st.title("Executive Overview")
        st.caption("Real-time business performance monitoring and KPI tracking")

        kpis = load_kpis(year)
        render_kpi_cards(kpis)

        st.divider()
        col1, col2 = st.columns(2)

        monthly = load_monthly(year)
        monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

        with col1:
            fig = px.line(
                monthly, x="period", y="revenue",
                title="Monthly Revenue Trend",
                labels={"revenue": "Revenue ($)", "period": "Month"},
                color_discrete_sequence=[COLORS[0]],
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                monthly, x="period", y="profit",
                title="Monthly Profit",
                labels={"profit": "Profit ($)", "period": "Month"},
                color_discrete_sequence=[COLORS[1]],
            )
            st.plotly_chart(fig, use_container_width=True)

        categories = load_categories(year)
        col3, col4 = st.columns(2)

        with col3:
            fig = px.pie(
                categories, values="revenue", names="category",
                title="Revenue by Category", hole=0.4,
                color_discrete_sequence=COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            fig = px.bar(
                categories.sort_values("profit", ascending=True),
                x="profit", y="category", orientation="h",
                title="Profit by Category",
                labels={"profit": "Profit ($)", "category": ""},
                color_discrete_sequence=[COLORS[2]],
            )
            st.plotly_chart(fig, use_container_width=True)

    elif page == "Regional Analysis":
        st.title("Regional Performance")
        st.caption("Geographic revenue distribution and territory ranking")

        regions = load_regions(year)

        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.bar(
                regions, x="region_name", y="revenue",
                color="country", title="Revenue by Region",
                labels={"revenue": "Revenue ($)", "region_name": "Region"},
                color_discrete_sequence=COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.treemap(
                regions, path=["country", "region_name"], values="revenue",
                title="Revenue Treemap",
                color="margin_pct", color_continuous_scale="RdYlGn",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            regions.assign(
                revenue=regions["revenue"].apply(lambda x: f"${x:,.0f}"),
                profit=regions["profit"].apply(lambda x: f"${x:,.0f}"),
                margin_pct=regions["margin_pct"].apply(lambda x: f"{x:.1f}%"),
            ),
            use_container_width=True, hide_index=True,
        )

    elif page == "Product Insights":
        st.title("Product Insights")
        st.caption("Category mix, top performers, and margin analysis")

        categories = load_categories(year)
        top = load_top_products(year)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.sunburst(
                categories, path=["category"], values="revenue",
                title="Category Revenue Sunburst",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                categories, x="revenue", y="profit", size="units_sold",
                text="category", title="Revenue vs Profit by Category",
                labels={"revenue": "Revenue ($)", "profit": "Profit ($)"},
                color_discrete_sequence=[COLORS[3]],
            )
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top 10 Products by Profit")
        fig = go.Figure(go.Bar(
            x=top["profit"], y=top["product_name"], orientation="h",
            marker_color=COLORS[4],
            text=top["profit"].apply(lambda x: f"${x:,.0f}"),
            textposition="outside",
        ))
        fig.update_layout(
            title="Highest-Margin Products",
            xaxis_title="Profit ($)", yaxis_title="",
            height=400, yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)

    elif page == "Customer Segments":
        st.title("Customer Segment Analysis")
        st.caption("Segment performance across sales channels")

        seg = load_segment_channel(year)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                seg, x="segment", y="revenue", color="order_channel",
                title="Revenue by Segment & Channel", barmode="group",
                labels={"revenue": "Revenue ($)", "segment": "Segment"},
                color_discrete_sequence=COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                seg, x="segment", y="avg_discount_pct", color="order_channel",
                title="Average Discount % by Segment", barmode="group",
                labels={"avg_discount_pct": "Discount %", "segment": "Segment"},
                color_discrete_sequence=COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(seg, use_container_width=True, hide_index=True)

        with st.expander("NumPy Statistical Summary"):
            stats = numpy_statistical_summary()
            st.json(stats)

    elif page == "SQL Performance":
        st.title("SQL Query Optimization")
        st.caption("Demonstrating 20% execution time reduction through indexing and pre-aggregation")

        st.markdown("""
        **Optimization strategies applied:**
        - Composite indexes on `(region_id, order_date)` and `(product_id, order_date)`
        - Pre-aggregated `agg_monthly_sales` table for dashboard KPIs
        - Filtered queries leveraging indexed date columns
        """)

        perf = compare_query_performance()
        fig = px.bar(
            perf, x="label", y="avg_ms",
            title="Query Execution Time Comparison (ms)",
            labels={"avg_ms": "Avg Time (ms)", "label": "Query Type"},
            color="avg_ms", color_continuous_scale="RdYlGn_r",
            text="avg_ms",
        )
        fig.update_traces(texttemplate="%{text:.1f}ms", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

        baseline = perf.iloc[1]["avg_ms"]
        optimized = perf.iloc[0]["avg_ms"]
        if baseline > 0:
            improvement = round((baseline - optimized) / baseline * 100, 1)
            st.success(f"Indexed filtered query is **{improvement}%** faster than full table scan.")

        st.dataframe(perf, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
