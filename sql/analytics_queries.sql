-- =============================================================================
-- SALES ANALYTICS QUERIES — Optimized for BI Reporting
-- Demonstrates: CTEs, window functions, subquery optimization, aggregations
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Q1: Executive KPI Summary (YTD vs Prior Year)
-- Uses indexed date_id join; single pass aggregation
-- -----------------------------------------------------------------------------
WITH current_ytd AS (
    SELECT
        SUM(f.revenue)                          AS total_revenue,
        SUM(f.profit)                           AS total_profit,
        COUNT(DISTINCT f.sale_id)               AS total_orders,
        COUNT(DISTINCT f.customer_id)           AS unique_customers,
        ROUND(AVG(f.revenue), 2)                AS avg_order_value,
        ROUND(SUM(f.profit) * 100.0 / NULLIF(SUM(f.revenue), 0), 2) AS profit_margin_pct
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE d.year = CAST(strftime('%Y', 'now') AS INTEGER)
),
prior_ytd AS (
    SELECT SUM(f.revenue) AS total_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE d.year = CAST(strftime('%Y', 'now') AS INTEGER) - 1
      AND d.month <= CAST(strftime('%m', 'now') AS INTEGER)
)
SELECT
    c.*,
    ROUND((c.total_revenue - p.total_revenue) * 100.0 / NULLIF(p.total_revenue, 0), 2) AS revenue_yoy_pct
FROM current_ytd c, prior_ytd p;


-- -----------------------------------------------------------------------------
-- Q2: Monthly Revenue Trend with Moving Average (12-month)
-- Window functions for trend smoothing
-- -----------------------------------------------------------------------------
SELECT
    d.year,
    d.month,
    d.month_name,
    SUM(f.revenue)                                              AS monthly_revenue,
    SUM(f.profit)                                               AS monthly_profit,
    COUNT(f.sale_id)                                            AS order_count,
    ROUND(AVG(SUM(f.revenue)) OVER (
        ORDER BY d.year, d.month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                       AS revenue_3mo_ma
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- -----------------------------------------------------------------------------
-- Q3: Regional Performance Ranking
-- Uses idx_fact_sales_region_date for efficient grouping
-- -----------------------------------------------------------------------------
SELECT
    r.region_name,
    r.country,
    COUNT(f.sale_id)                                            AS total_orders,
    ROUND(SUM(f.revenue), 2)                                    AS total_revenue,
    ROUND(SUM(f.profit), 2)                                     AS total_profit,
    ROUND(SUM(f.profit) * 100.0 / NULLIF(SUM(f.revenue), 0), 2) AS margin_pct,
    RANK() OVER (ORDER BY SUM(f.revenue) DESC)                  AS revenue_rank
FROM fact_sales f
JOIN dim_regions r ON f.region_id = r.region_id
GROUP BY r.region_id, r.region_name, r.country
ORDER BY total_revenue DESC;


-- -----------------------------------------------------------------------------
-- Q4: Product Category Mix & Pareto Analysis (80/20 rule)
-- Identifies top revenue-driving categories for inventory planning
-- -----------------------------------------------------------------------------
WITH category_revenue AS (
    SELECT
        p.category,
        SUM(f.revenue)  AS revenue,
        SUM(f.quantity) AS units_sold,
        COUNT(f.sale_id) AS orders
    FROM fact_sales f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.category
),
ranked AS (
    SELECT
        *,
        SUM(revenue) OVER () AS total_revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC) AS cumulative_revenue
    FROM category_revenue
)
SELECT
    category,
    ROUND(revenue, 2)                                           AS revenue,
    units_sold,
    orders,
    ROUND(revenue * 100.0 / total_revenue, 2)                   AS revenue_share_pct,
    ROUND(cumulative_revenue * 100.0 / total_revenue, 2)        AS cumulative_pct,
    CASE WHEN cumulative_revenue * 100.0 / total_revenue <= 80
         THEN 'Top 80%' ELSE 'Long Tail' END                    AS pareto_segment
FROM ranked
ORDER BY revenue DESC;


-- -----------------------------------------------------------------------------
-- Q5: Customer Segment Analysis by Channel
-- Cross-dimensional analysis for marketing spend allocation
-- -----------------------------------------------------------------------------
SELECT
    c.segment,
    f.order_channel,
    COUNT(DISTINCT c.customer_id)                               AS customers,
    COUNT(f.sale_id)                                            AS orders,
    ROUND(SUM(f.revenue), 2)                                    AS revenue,
    ROUND(AVG(f.revenue), 2)                                    AS avg_order_value,
    ROUND(AVG(f.discount_pct) * 100, 2)                         AS avg_discount_pct
FROM fact_sales f
JOIN dim_customers c ON f.customer_id = c.customer_id
GROUP BY c.segment, f.order_channel
ORDER BY revenue DESC;


-- -----------------------------------------------------------------------------
-- Q6: Top 10 Products by Profit (not just revenue)
-- Helps BA teams focus on margin, not volume alone
-- -----------------------------------------------------------------------------
SELECT
    p.product_name,
    p.category,
    SUM(f.quantity)                                             AS units_sold,
    ROUND(SUM(f.revenue), 2)                                    AS revenue,
    ROUND(SUM(f.profit), 2)                                     AS profit,
    ROUND(SUM(f.profit) * 100.0 / NULLIF(SUM(f.revenue), 0), 2) AS margin_pct
FROM fact_sales f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY profit DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- Q7: Slow-Moving Inventory Alert
-- Products with declining sales (last 3 months vs prior 3 months)
-- -----------------------------------------------------------------------------
WITH recent AS (
    SELECT product_id, SUM(quantity) AS qty
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE d.full_date >= date('now', '-3 months')
    GROUP BY product_id
),
prior AS (
    SELECT product_id, SUM(quantity) AS qty
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    WHERE d.full_date >= date('now', '-6 months')
      AND d.full_date < date('now', '-3 months')
    GROUP BY product_id
)
SELECT
    p.product_name,
    p.category,
    COALESCE(r.qty, 0)                                          AS recent_qty,
    COALESCE(pr.qty, 0)                                         AS prior_qty,
    ROUND((COALESCE(r.qty, 0) - COALESCE(pr.qty, 0)) * 100.0
        / NULLIF(pr.qty, 0), 2)                                 AS qty_change_pct
FROM dim_products p
LEFT JOIN recent r ON p.product_id = r.product_id
LEFT JOIN prior pr ON p.product_id = pr.product_id
WHERE COALESCE(pr.qty, 0) > 0
  AND COALESCE(r.qty, 0) < COALESCE(pr.qty, 0) * 0.7
ORDER BY qty_change_pct ASC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Q8: Pre-Aggregated Monthly Summary (uses agg_monthly_sales)
-- Demonstrates materialized aggregation for sub-second dashboard loads
-- -----------------------------------------------------------------------------
SELECT
    a.year,
    a.month,
    r.region_name,
    a.category,
    a.total_revenue,
    a.total_profit,
    a.total_orders,
    a.avg_order_value
FROM agg_monthly_sales a
JOIN dim_regions r ON a.region_id = r.region_id
WHERE a.year >= CAST(strftime('%Y', 'now') AS INTEGER) - 1
ORDER BY a.year DESC, a.month DESC, a.total_revenue DESC;
