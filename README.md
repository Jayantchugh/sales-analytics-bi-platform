# Sales Analytics & Business Intelligence Platform

A portfolio-grade analytics project demonstrating end-to-end BI capabilities: **250,000+ sales records**, optimized SQL, Python/Pandas analysis, and interactive dashboards.

Built for Business Analyst (BA) and Project Analyst (PA) roles.

---

## What This Project Demonstrates

| Resume Bullet | How It's Shown Here |
|---|---|
| Analyzed 250,000+ sales records using Python, SQL, Pandas, NumPy | `generate_data.py` creates 250K transactions; `analytics.py` runs statistical analysis |
| Optimized SQL queries, reducing execution time by ~20% | Indexed schema + pre-aggregated tables; benchmark page in dashboard |
| Interactive dashboards for real-time business insights | Streamlit dashboard with 5 views; Power BI connection guide included |

---

## Tech Stack

- **Python** — Data generation, ETL, statistical analysis
- **SQL (SQLite)** — Star-schema design, CTEs, window functions, indexing
- **Pandas / NumPy** — Aggregations, correlations, percentile analysis
- **Streamlit + Plotly** — Interactive web dashboard
- **Power BI** — Optional connection via ODBC/SQLite connector

---

## Quick Start

### 1. Install dependencies

```bash
cd "Business Intelligence"
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate data (250,000+ records)

```bash
python python/generate_data.py
```

### 3. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure

```
Business Intelligence/
├── dashboard/
│   └── app.py                  # Streamlit BI dashboard (5 pages)
├── python/
│   ├── config.py               # Project constants
│   ├── generate_data.py        # Synthetic data generator (250K+ rows)
│   └── analytics.py            # KPI queries + NumPy analysis
├── sql/
│   ├── schema.sql              # Star-schema (dims + fact table)
│   ├── indexes.sql             # Performance indexes
│   └── analytics_queries.sql   # 8 production BI queries
├── data/
│   └── sales_analytics.db      # Generated SQLite database
├── docs/
│   └── POWER_BI_SETUP.md       # Connect Power BI to this data
└── requirements.txt
```

---

## Dashboard Pages

1. **Executive Overview** — KPIs, revenue trends, category mix
2. **Regional Analysis** — Geographic performance, treemap, rankings
3. **Product Insights** — Pareto analysis, top products by profit
4. **Customer Segments** — Channel × segment cross-analysis
5. **SQL Performance** — Query benchmark showing optimization impact

---

## Key Business Questions Answered

- What is YTD revenue and how does it compare to last year?
- Which regions and product categories drive the most profit?
- What is the 80/20 (Pareto) split across categories?
- How do customer segments behave across sales channels?
- Which products are declining and need inventory attention?

---

## SQL Highlights

See `sql/analytics_queries.sql` for 8 production queries including:

- YTD vs prior-year KPI comparison (CTEs)
- 3-month moving average revenue trend (window functions)
- Regional performance ranking (`RANK()`)
- Pareto / 80-20 category analysis
- Slow-moving inventory alerts

---

## For Your Resume / Interviews

**Talking points:**

> "I built an end-to-end sales analytics platform processing 250K+ transactions. I designed a star-schema database with strategic indexes that cut query time by ~20%, and built interactive dashboards surfacing KPIs, regional performance, and customer segment insights for stakeholders."

**Metrics you can cite from this project:**
- 250,000 sales transactions across 500 products, 10K customers, 12 regions
- 3-year date range with seasonal patterns
- 8 optimized SQL queries with window functions and CTEs
- 5 dashboard views with drill-down capability

---

## Power BI

See [docs/POWER_BI_SETUP.md](docs/POWER_BI_SETUP.md) for connecting Power BI Desktop to the SQLite database.

---

## License

MIT — free to use in your portfolio.
