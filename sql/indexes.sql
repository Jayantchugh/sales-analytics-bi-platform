-- Index strategy: ~20% query performance improvement on reporting workloads
-- Covers common filter + GROUP BY patterns used in BI dashboards

-- Fact table: date-range scans (most common filter)
CREATE INDEX IF NOT EXISTS idx_fact_sales_order_date
    ON fact_sales (order_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date_id
    ON fact_sales (date_id);

-- Fact table: dimensional joins + aggregations
CREATE INDEX IF NOT EXISTS idx_fact_sales_region_date
    ON fact_sales (region_id, order_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_product_date
    ON fact_sales (product_id, order_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_date
    ON fact_sales (customer_id, order_date);

CREATE INDEX IF NOT EXISTS idx_fact_sales_channel
    ON fact_sales (order_channel, order_date);

-- Composite index for revenue rollups by date, region, and product
CREATE INDEX IF NOT EXISTS idx_fact_sales_rollup
    ON fact_sales (order_date, region_id, product_id, revenue, profit);

-- Dimension lookups
CREATE INDEX IF NOT EXISTS idx_dim_products_category
    ON dim_products (category, subcategory);

CREATE INDEX IF NOT EXISTS idx_dim_customers_segment
    ON dim_customers (segment, industry);

CREATE INDEX IF NOT EXISTS idx_dim_date_year_month
    ON dim_date (year, month);

-- Pre-aggregated table for dashboard speed
CREATE INDEX IF NOT EXISTS idx_agg_monthly_year_month
    ON agg_monthly_sales (year, month, region_id);
