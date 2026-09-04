# Power BI Setup Guide

Connect Power BI Desktop to the Sales Analytics database for your portfolio demo.

---

## Option 1: Import CSV Exports (Easiest)

Export key tables from Python, then import into Power BI:

```bash
python -c "
import sqlite3, pandas as pd
from pathlib import Path
db = Path('data/sales_analytics.db')
conn = sqlite3.connect(db)
for table in ['fact_sales', 'dim_products', 'dim_regions', 'dim_customers', 'dim_date', 'agg_monthly_sales']:
    pd.read_sql(f'SELECT * FROM {table}', conn).to_csv(f'data/{table}.csv', index=False)
    print(f'Exported {table}')
conn.close()
"
```

In Power BI Desktop:
1. **Get Data** → **Text/CSV** → select all `data/*.csv` files
2. Create relationships:
   - `fact_sales[product_id]` → `dim_products[product_id]`
   - `fact_sales[customer_id]` → `dim_customers[customer_id]`
   - `fact_sales[region_id]` → `dim_regions[region_id]`
   - `fact_sales[date_id]` → `dim_date[date_id]`

---

## Option 2: SQLite ODBC Connector

1. Install [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/)
2. In Power BI: **Get Data** → **ODBC** → DSN pointing to `data/sales_analytics.db`
3. Select tables and load

---

## Recommended Power BI Report Pages

Mirror the Streamlit dashboard for consistency:

### Page 1: Executive Summary
- **Cards:** Total Revenue, Total Profit, Orders, Avg Order Value, Margin %
- **Line chart:** Monthly revenue trend (`dim_date[month_name]` × `SUM(fact_sales[revenue])`)
- **Donut chart:** Revenue by category

**DAX measures:**
```dax
Total Revenue = SUM(fact_sales[revenue])
Total Profit  = SUM(fact_sales[profit])
Profit Margin = DIVIDE([Total Profit], [Total Revenue], 0)
Total Orders  = DISTINCTCOUNT(fact_sales[sale_id])
AOV           = DIVIDE([Total Revenue], [Total Orders], 0)
```

### Page 2: Regional Performance
- **Map or bar chart:** Revenue by `dim_regions[region_name]`
- **Matrix:** Region × Category with revenue and margin

### Page 3: Product Analysis
- **Treemap:** `dim_products[category]` sized by revenue
- **Table:** Top 10 products by profit

### Page 4: Customer Segments
- **Stacked bar:** Revenue by `dim_customers[segment]` and `fact_sales[order_channel]`
- **Slicer:** Year filter using `dim_date[year]`

---

## Sample DAX for YoY Growth

```dax
Revenue YoY % =
VAR CurrentYear = [Total Revenue]
VAR PriorYear = CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR(dim_date[full_date])
)
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, 0)
```

---

## Portfolio Tip

Take screenshots of your Power BI report pages and add them to your README or LinkedIn. Mention both tools:

> "Built interactive dashboards in **Streamlit** (Python) and **Power BI** for executive reporting and ad-hoc analysis."
