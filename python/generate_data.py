"""Generate 250,000+ realistic sales records and load into SQLite."""

import calendar
import sqlite3
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from config import (
    CATEGORIES,
    CHANNELS,
    DATA_DIR,
    DB_PATH,
    END_DATE,
    INDUSTRIES,
    MONTH_NAMES,
    NUM_CUSTOMERS,
    NUM_PRODUCTS,
    NUM_REGIONS,
    NUM_SALES_RECORDS,
    REGIONS,
    SEGMENTS,
    SQL_DIR,
    START_DATE,
)

fake = Faker()
Faker.seed(42)
np.random.seed(42)


def _build_date_dimension(start: str, end: str) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame({
        "date_id": range(1, len(dates) + 1),
        "full_date": dates.date,
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": [MONTH_NAMES[m - 1] for m in dates.month],
        "day_of_week": dates.dayofweek,
        "is_weekend": (dates.dayofweek >= 5).astype(int),
    })


def _build_products(n: int) -> pd.DataFrame:
    rows = []
    categories = list(CATEGORIES.keys())
    for i in range(1, n + 1):
        cat = categories[i % len(categories)]
        sub = CATEGORIES[cat][i % len(CATEGORIES[cat])]
        cost = round(np.random.uniform(5, 500), 2)
        markup = np.random.uniform(1.2, 2.5)
        rows.append({
            "product_id": i,
            "product_name": f"{sub} - {fake.word().title()} {i:04d}",
            "category": cat,
            "subcategory": sub,
            "unit_cost": cost,
            "unit_price": round(cost * markup, 2),
        })
    return pd.DataFrame(rows)


def _build_regions() -> pd.DataFrame:
    return pd.DataFrame(
        [{"region_id": i + 1, "region_name": r[0], "country": r[1], "territory": r[2]}
         for i, r in enumerate(REGIONS[:NUM_REGIONS])]
    )


def _build_customers(n: int) -> pd.DataFrame:
    start = date.fromisoformat(START_DATE)
    return pd.DataFrame({
        "customer_id": range(1, n + 1),
        "customer_name": [fake.company() for _ in range(n)],
        "segment": np.random.choice(SEGMENTS, n, p=[0.15, 0.30, 0.45, 0.10]),
        "industry": np.random.choice(INDUSTRIES, n),
        "acquisition_date": [
            (start + timedelta(days=int(d))).isoformat()
            for d in np.random.randint(0, 900, n)
        ],
    })


def _build_sales(
    n: int,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    regions: pd.DataFrame,
    dates: pd.DataFrame,
) -> pd.DataFrame:
    start = date.fromisoformat(START_DATE)
    end = date.fromisoformat(END_DATE)
    total_days = (end - start).days

    # Seasonal multiplier: higher sales in Q4 and summer
    date_weights = []
    for d in dates.itertuples():
        weight = 1.0
        if d.month in (11, 12):
            weight = 1.8
        elif d.month in (6, 7, 8):
            weight = 1.3
        elif d.month in (1, 2):
            weight = 0.7
        date_weights.append(weight)
    date_weights = np.array(date_weights)
    date_probs = date_weights / date_weights.sum()

    sampled_date_idx = np.random.choice(len(dates), size=n, p=date_probs)
    sampled_dates = dates.iloc[sampled_date_idx]

    product_ids = np.random.randint(1, len(products) + 1, n)
    customer_ids = np.random.randint(1, len(customers) + 1, n)
    region_ids = np.random.randint(1, len(regions) + 1, n)
    quantities = np.random.poisson(lam=3, size=n) + 1
    channels = np.random.choice(CHANNELS, n, p=[0.45, 0.25, 0.20, 0.10])

    # Segment-based discount distribution
    segment_map = customers.set_index("customer_id")["segment"]
    discounts = []
    prices = []
    costs = []
    revenues = []
    profits = []

    product_lookup = products.set_index("product_id")

    for i in range(n):
        pid = product_ids[i]
        cid = customer_ids[i]
        qty = quantities[i]
        base_price = product_lookup.loc[pid, "unit_price"]
        base_cost = product_lookup.loc[pid, "unit_cost"]
        seg = segment_map[cid]

        if seg == "Enterprise":
            disc = np.random.uniform(0.05, 0.20)
        elif seg == "Government":
            disc = np.random.uniform(0.10, 0.25)
        elif seg == "SMB":
            disc = np.random.uniform(0.0, 0.10)
        else:
            disc = np.random.uniform(0.0, 0.05)

        net_price = round(base_price * (1 - disc), 2)
        rev = round(net_price * qty, 2)
        cost = round(base_cost * qty, 2)

        discounts.append(round(disc, 4))
        prices.append(net_price)
        costs.append(cost)
        revenues.append(rev)
        profits.append(round(rev - cost, 2))

    return pd.DataFrame({
        "sale_id": range(1, n + 1),
        "order_date": sampled_dates["full_date"].values,
        "date_id": sampled_dates["date_id"].values,
        "product_id": product_ids,
        "customer_id": customer_ids,
        "region_id": region_ids,
        "quantity": quantities,
        "unit_price": prices,
        "discount_pct": discounts,
        "revenue": revenues,
        "cost": costs,
        "profit": profits,
        "order_channel": channels,
    })


def _build_monthly_aggregates(sales: pd.DataFrame, products: pd.DataFrame, dates: pd.DataFrame) -> pd.DataFrame:
    merged = sales.merge(products[["product_id", "category"]], on="product_id")
    merged = merged.merge(dates[["date_id", "year", "month"]], on="date_id")
    agg = (
        merged.groupby(["year", "month", "region_id", "category"])
        .agg(
            total_revenue=("revenue", "sum"),
            total_profit=("profit", "sum"),
            total_orders=("sale_id", "count"),
            avg_order_value=("revenue", "mean"),
        )
        .reset_index()
    )
    for col in ("total_revenue", "total_profit", "avg_order_value"):
        agg[col] = agg[col].round(2)
    return agg


def _init_database(conn: sqlite3.Connection) -> None:
    for sql_file in ("schema.sql", "indexes.sql"):
        with open(SQL_DIR / sql_file) as f:
            conn.executescript(f.read())


def _prepare_df_for_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dtypes for reliable SQLite inserts across Python versions."""
    prepared = df.copy()
    for col in prepared.columns:
        series = prepared[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            prepared[col] = series.dt.strftime("%Y-%m-%d")
        elif series.dtype == object:
            if series.map(lambda x: hasattr(x, "isoformat")).any():
                prepared[col] = series.map(
                    lambda x: x.isoformat() if hasattr(x, "isoformat") else x
                )
            prepared[col] = prepared[col].astype(str).replace("nan", None)
        elif pd.api.types.is_bool_dtype(series):
            prepared[col] = series.astype(int)
        elif pd.api.types.is_integer_dtype(series):
            prepared[col] = series.astype(int)
        elif pd.api.types.is_float_dtype(series):
            prepared[col] = series.astype(float)
    return prepared


def _load_dataframe(conn: sqlite3.Connection, df: pd.DataFrame, table: str) -> None:
    prepared = _prepare_df_for_sqlite(df)
    chunksize = 10_000 if len(prepared) > 10_000 else None
    prepared.to_sql(table, conn, if_exists="append", index=False, chunksize=chunksize)


def generate_and_load() -> dict:
    """Generate all data and load into SQLite. Returns summary stats."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    print("Building dimension tables...")
    dates = _build_date_dimension(START_DATE, END_DATE)
    products = _build_products(NUM_PRODUCTS)
    regions = _build_regions()
    customers = _build_customers(NUM_CUSTOMERS)

    print(f"Generating {NUM_SALES_RECORDS:,} sales transactions...")
    sales = _build_sales(NUM_SALES_RECORDS, products, customers, regions, dates)
    monthly = _build_monthly_aggregates(sales, products, dates)

    print("Loading into database...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        _init_database(conn)
        for table, df in [
            ("dim_products", products),
            ("dim_regions", regions),
            ("dim_customers", customers),
            ("dim_date", dates),
            ("fact_sales", sales),
            ("agg_monthly_sales", monthly),
        ]:
            _load_dataframe(conn, df, table)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        if DB_PATH.exists():
            DB_PATH.unlink()
        raise
    finally:
        conn.close()

    summary = {
        "total_sales": len(sales),
        "total_revenue": round(sales["revenue"].sum(), 2),
        "total_profit": round(sales["profit"].sum(), 2),
        "date_range": f"{START_DATE} to {END_DATE}",
        "products": len(products),
        "customers": len(customers),
        "regions": len(regions),
        "db_path": str(DB_PATH),
    }
    print("\n=== Data Generation Complete ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    generate_and_load()
