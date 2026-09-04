-- Sales Analytics & BI Platform — Database Schema
-- Designed for normalized reporting with star-schema-style fact table

PRAGMA foreign_keys = ON;

-- Dimension: Product categories and SKUs
CREATE TABLE IF NOT EXISTS dim_products (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT    NOT NULL,
    category        TEXT    NOT NULL,
    subcategory     TEXT    NOT NULL,
    unit_cost       REAL    NOT NULL CHECK (unit_cost >= 0),
    unit_price      REAL    NOT NULL CHECK (unit_price >= unit_cost)
);

-- Dimension: Sales regions and territories
CREATE TABLE IF NOT EXISTS dim_regions (
    region_id       INTEGER PRIMARY KEY,
    region_name     TEXT    NOT NULL UNIQUE,
    country         TEXT    NOT NULL,
    territory       TEXT    NOT NULL
);

-- Dimension: Customer segments
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id     INTEGER PRIMARY KEY,
    customer_name   TEXT    NOT NULL,
    segment         TEXT    NOT NULL CHECK (segment IN ('Enterprise', 'SMB', 'Consumer', 'Government')),
    industry        TEXT    NOT NULL,
    acquisition_date DATE   NOT NULL
);

-- Dimension: Time (for efficient date-based aggregations)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER PRIMARY KEY,
    full_date       DATE    NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month           INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name      TEXT    NOT NULL,
    day_of_week     INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_weekend      INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

-- Fact: Sales transactions (250,000+ rows)
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id         INTEGER PRIMARY KEY,
    order_date      DATE    NOT NULL,
    date_id         INTEGER NOT NULL REFERENCES dim_date(date_id),
    product_id      INTEGER NOT NULL REFERENCES dim_products(product_id),
    customer_id     INTEGER NOT NULL REFERENCES dim_customers(customer_id),
    region_id       INTEGER NOT NULL REFERENCES dim_regions(region_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      REAL    NOT NULL CHECK (unit_price >= 0),
    discount_pct    REAL    NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 1),
    revenue         REAL    NOT NULL CHECK (revenue >= 0),
    cost            REAL    NOT NULL CHECK (cost >= 0),
    profit          REAL    NOT NULL,
    order_channel   TEXT    NOT NULL CHECK (order_channel IN ('Online', 'Retail', 'Partner', 'Direct'))
);

-- Materialized-style summary table for fast dashboard KPIs
CREATE TABLE IF NOT EXISTS agg_monthly_sales (
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    region_id       INTEGER NOT NULL REFERENCES dim_regions(region_id),
    category        TEXT    NOT NULL,
    total_revenue   REAL    NOT NULL,
    total_profit    REAL    NOT NULL,
    total_orders    INTEGER NOT NULL,
    avg_order_value REAL    NOT NULL,
    PRIMARY KEY (year, month, region_id, category)
);
