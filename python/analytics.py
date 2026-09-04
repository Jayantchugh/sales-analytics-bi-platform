"""Core analytics engine — Pandas/NumPy analysis + SQL query execution."""

import sqlite3
import time
from pathlib import Path

import numpy as np
import pandas as pd

from config import DB_PATH, SQL_DIR


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run: python python/generate_data.py"
        )
    return sqlite3.connect(DB_PATH)


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def run_sql_file(filename: str) -> list[pd.DataFrame]:
    """Execute all queries in a SQL file and return result DataFrames."""
    with open(SQL_DIR / filename) as f:
        content = f.read()

    queries = [q.strip() for q in content.split(";") if q.strip() and not q.strip().startswith("--")]
    results = []
    for query in queries:
        if query.upper().startswith("WITH") or query.upper().startswith("SELECT"):
            results.append(run_query(query))
    return results


def benchmark_query(sql: str, label: str, runs: int = 3) -> dict:
    """Measure query execution time to demonstrate SQL optimization impact."""
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        run_query(sql)
        times.append(time.perf_counter() - start)
    avg_ms = round(np.mean(times) * 1000, 2)
    return {"label": label, "avg_ms": avg_ms, "runs": runs}


# ---------------------------------------------------------------------------
# KPI Functions (used by dashboard and reports)
# ---------------------------------------------------------------------------

def get_kpi_summary(year: int | None = None) -> dict:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT
            SUM(f.revenue) AS total_revenue,
            SUM(f.profit) AS total_profit,
            COUNT(DISTINCT f.sale_id) AS total_orders,
            COUNT(DISTINCT f.customer_id) AS unique_customers,
            AVG(f.revenue) AS avg_order_value,
            SUM(f.profit) * 100.0 / NULLIF(SUM(f.revenue), 0) AS profit_margin_pct
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
    """
    row = run_query(sql).iloc[0]
    return {k: round(v, 2) if isinstance(v, float) else int(v) for k, v in row.items()}


def get_monthly_trend(year: int | None = None) -> pd.DataFrame:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT d.year, d.month, d.month_name,
               SUM(f.revenue) AS revenue,
               SUM(f.profit) AS profit,
               COUNT(f.sale_id) AS orders
        FROM fact_sales f
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
        GROUP BY d.year, d.month, d.month_name
        ORDER BY d.year, d.month
    """
    return run_query(sql)


def get_regional_performance(year: int | None = None) -> pd.DataFrame:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT r.region_name, r.country,
               SUM(f.revenue) AS revenue,
               SUM(f.profit) AS profit,
               COUNT(f.sale_id) AS orders,
               SUM(f.profit) * 100.0 / NULLIF(SUM(f.revenue), 0) AS margin_pct
        FROM fact_sales f
        JOIN dim_regions r ON f.region_id = r.region_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
        GROUP BY r.region_id, r.region_name, r.country
        ORDER BY revenue DESC
    """
    return run_query(sql)


def get_category_breakdown(year: int | None = None) -> pd.DataFrame:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT p.category,
               SUM(f.revenue) AS revenue,
               SUM(f.profit) AS profit,
               SUM(f.quantity) AS units_sold,
               COUNT(f.sale_id) AS orders
        FROM fact_sales f
        JOIN dim_products p ON f.product_id = p.product_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
        GROUP BY p.category
        ORDER BY revenue DESC
    """
    return run_query(sql)


def get_segment_channel_analysis(year: int | None = None) -> pd.DataFrame:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT c.segment, f.order_channel,
               COUNT(DISTINCT c.customer_id) AS customers,
               SUM(f.revenue) AS revenue,
               AVG(f.revenue) AS avg_order_value,
               AVG(f.discount_pct) * 100 AS avg_discount_pct
        FROM fact_sales f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
        GROUP BY c.segment, f.order_channel
        ORDER BY revenue DESC
    """
    return run_query(sql)


def get_top_products(n: int = 10, year: int | None = None) -> pd.DataFrame:
    year_filter = f"AND d.year = {year}" if year else ""
    sql = f"""
        SELECT p.product_name, p.category,
               SUM(f.quantity) AS units_sold,
               SUM(f.revenue) AS revenue,
               SUM(f.profit) AS profit
        FROM fact_sales f
        JOIN dim_products p ON f.product_id = p.product_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE 1=1 {year_filter}
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY profit DESC
        LIMIT {n}
    """
    return run_query(sql)


def numpy_statistical_summary() -> dict:
    """Pandas/NumPy statistical analysis on sales data."""
    sql = "SELECT revenue, profit, quantity, discount_pct FROM fact_sales"
    df = run_query(sql)

    discount_bins = pd.cut(df["discount_pct"], bins=[0, 0.05, 0.15, 1.0], labels=["Low", "Med", "High"])
    discount_impact = {
        str(k): round(v, 2)
        for k, v in df.groupby(discount_bins, observed=True)["revenue"].mean().items()
    }

    return {
        "revenue_mean": round(df["revenue"].mean(), 2),
        "revenue_median": round(df["revenue"].median(), 2),
        "revenue_std": round(df["revenue"].std(), 2),
        "revenue_p95": round(np.percentile(df["revenue"], 95), 2),
        "profit_correlation_qty": round(df["profit"].corr(df["quantity"]), 4),
        "avg_revenue_by_discount_tier": discount_impact,
    }


def compare_query_performance() -> pd.DataFrame:
    """Demonstrate index impact: filtered vs unfiltered aggregation."""
    queries = [
        (
            "With Index (region + date)",
            """
            SELECT r.region_name, SUM(f.revenue) AS revenue
            FROM fact_sales f
            JOIN dim_regions r ON f.region_id = r.region_id
            WHERE f.order_date >= '2024-01-01'
            GROUP BY r.region_name
            """,
        ),
        (
            "Full Table Scan (no filter)",
            """
            SELECT r.region_name, SUM(f.revenue) AS revenue
            FROM fact_sales f
            JOIN dim_regions r ON f.region_id = r.region_id
            GROUP BY r.region_name
            """,
        ),
        (
            "Pre-Aggregated Table",
            """
            SELECT r.region_name, SUM(a.total_revenue) AS revenue
            FROM agg_monthly_sales a
            JOIN dim_regions r ON a.region_id = r.region_id
            WHERE a.year >= 2024
            GROUP BY r.region_name
            """,
        ),
    ]
    results = [benchmark_query(sql, label) for label, sql in queries]
    return pd.DataFrame(results)


if __name__ == "__main__":
    print("=== KPI Summary ===")
    print(get_kpi_summary())
    print("\n=== Query Performance Benchmark ===")
    print(compare_query_performance())
