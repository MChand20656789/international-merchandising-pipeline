"""
International Merchandising Data Quality & Reporting Pipeline

Purpose
-------
Simulates an international merchandising data workflow in which sales
and inventory data arrive from multiple markets with inconsistent:

- Country identifiers
- Date formats
- Product names
- Currencies
- Duplicate transactions
- Missing values

Pipeline
--------
1. Load raw files
2. Combine sales sources
3. Introduce test data-quality problems
4. Standardize country
5. Standardize dates
6. Standardize products
7. Validate currencies
8. Detect duplicates
9. Detect missing values
10. Convert currency to USD
11. Calculate sales
12. Save cleaned CSV
13. Load data into SQLite
14. Run SQL reporting queries
15. Generate QA report
"""

from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SALES_US_FILE = DATA_DIR / "sales_us.csv"
SALES_EUROPE_FILE = DATA_DIR / "sales_europe.csv"
INVENTORY_FILE = DATA_DIR / "inventory.csv"

CLEANED_SALES_FILE = OUTPUT_DIR / "cleaned_sales.csv"
CLEANED_INVENTORY_FILE = OUTPUT_DIR / "cleaned_inventory.csv"
QA_REPORT_FILE = OUTPUT_DIR / "data_quality_report.txt"
SQL_RESULTS_FILE = OUTPUT_DIR / "sql_results.txt"
DATABASE_FILE = OUTPUT_DIR / "international_merchandising.db"


# ============================================================
# 2. LOAD RAW FILES
# ============================================================

print("=" * 70)
print("INTERNATIONAL MERCHANDISING DATA PIPELINE")
print("=" * 70)

print("\n[1/12] Loading raw files...")

sales_us = pd.read_csv(SALES_US_FILE)
sales_europe = pd.read_csv(SALES_EUROPE_FILE)
inventory = pd.read_csv(INVENTORY_FILE)

print(f"  sales_us.csv:       {len(sales_us)} rows")
print(f"  sales_europe.csv:   {len(sales_europe)} rows")
print(f"  inventory.csv:      {len(inventory)} rows")


# ============================================================
# 3. COMBINE SALES SOURCES
# ============================================================

print("\n[2/12] Combining sales sources...")

sales_us["source_file"] = "sales_us.csv"
sales_europe["source_file"] = "sales_europe.csv"

sales = pd.concat(
    [sales_us, sales_europe],
    ignore_index=True
)

rows_received = len(sales)

print(f"  Combined sales rows: {rows_received}")


# ============================================================
# 4. INTRODUCE TEST DATA-QUALITY PROBLEMS
# ============================================================

print("\n[3/12] Introducing test data-quality problems...")

# ------------------------------------------------------------
# Duplicate records
# ------------------------------------------------------------
# Duplicate two existing records so the pipeline can detect
# and remove duplicate transactions.

if len(sales) >= 8:
    duplicate_rows = sales.iloc[[3, 7]].copy()

    sales = pd.concat(
        [sales, duplicate_rows],
        ignore_index=True
    )

# ------------------------------------------------------------
# Missing country
# ------------------------------------------------------------
# Intentionally create a missing country value.

if len(sales) > 5:
    sales.loc[5, "country"] = None

# ------------------------------------------------------------
# Missing quantity
# ------------------------------------------------------------
# Intentionally create a missing quantity value.

if len(sales) > 8:
    sales.loc[8, "quantity"] = None

print(f"  Rows after test issues: {len(sales)}")


# ============================================================
# 5. STANDARDIZE COUNTRY NAMES
# ============================================================

print("\n[4/12] Standardizing country names...")

country_map = {
    "United States": "United States",
    "USA": "United States",
    "US": "United States",

    "Germany": "Germany",
    "DE": "Germany",

    "United Kingdom": "United Kingdom",
    "UK": "United Kingdom",

    "Canada": "Canada",
    "CA": "Canada",

    "Japan": "Japan",
    "JP": "Japan",
}

sales["country"] = (
    sales["country"]
    .astype("string")
    .str.strip()
    .replace(country_map)
)

print("  Country identifiers standardized.")


# ============================================================
# 6. STANDARDIZE DATE FORMATS
# ============================================================

print("\n[5/12] Standardizing dates...")

# The source files intentionally contain formats such as:
#
# 08/01/2026
# 2026-08-01
# 01.08.2026
# 2026/08/01

def standardize_date(value):
    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    date_formats = [
        "%m/%d/%Y",   # 08/01/2026
        "%Y-%m-%d",   # 2026-08-01
        "%d.%m.%Y",   # 01.08.2026
        "%Y/%m/%d",   # 2026/08/01
        "%d/%m/%Y",   # 02/08/2026
    ]

    for fmt in date_formats:
        try:
            return pd.to_datetime(value, format=fmt)
        except ValueError:
            continue

    return pd.NaT


sales["order_date"] = sales["order_date"].apply(
    standardize_date
)

sales["order_date"] = sales["order_date"].dt.strftime(
    "%Y-%m-%d"
)

print("  Dates standardized to YYYY-MM-DD.")


# ============================================================
# 7. STANDARDIZE PRODUCT NAMES
# ============================================================

print("\n[6/12] Standardizing product names...")

product_map = {
    "running shoes": "Running Shoes",
    "running shoe": "Running Shoes",
    "run shoes": "Running Shoes",

    "sandals": "Sandals",
    "sandal": "Sandals",
    "sandalen": "Sandals",

    "sneakers": "Sneakers",
    "sneaker": "Sneakers",

    "hoodie": "Hoodie",

    "socks": "Socks",
    "sock": "Socks",

    "jacket": "Jacket",
}

sales["product"] = (
    sales["product"]
    .astype("string")
    .str.strip()
    .str.lower()
    .replace(product_map)
)

print("  Product names standardized.")


# ============================================================
# 8. VALIDATE CURRENCIES
# ============================================================

print("\n[7/12] Validating currencies...")

# These are deliberately static illustrative rates.
# They are NOT live financial-market exchange rates.

exchange_rates = {
    "USD": 1.00,
    "EUR": 1.16,
    "GBP": 1.34,
    "CAD": 0.73,
    "JPY": 0.0067,
}

valid_currencies = set(exchange_rates.keys())

sales["currency_valid"] = sales["currency"].isin(valid_currencies)

invalid_currency_count = int(
    (~sales["currency_valid"]).sum()
)

print(f"  Invalid currencies: {invalid_currency_count}")

sales["price_usd"] = (
    pd.to_numeric(sales["unit_price"], errors="coerce")
    * sales["currency"].map(exchange_rates)
)


# ============================================================
# 9. DETECT DUPLICATES
# ============================================================

print("\n[8/12] Detecting duplicate transactions...")

duplicates = int(
    sales.duplicated(
        subset=["order_id"],
        keep="first"
    ).sum()
)

print(f"  Duplicate transactions found: {duplicates}")

# Keep the first occurrence of each order ID.

sales = sales.drop_duplicates(
    subset=["order_id"],
    keep="first"
).copy()


# ============================================================
# 10. DETECT AND HANDLE MISSING VALUES
# ============================================================

print("\n[9/12] Checking missing values...")

missing_by_column = sales.isna().sum()

print("\n  Missing values by column:")

for column, count in missing_by_column.items():
    if count > 0:
        print(f"    {column}: {count}")

# Create a row-level data-quality flag.

quality_columns = [
    "order_id",
    "country",
    "order_date",
    "currency",
    "product",
    "quantity",
    "unit_price",
]

sales["data_quality_issue"] = sales[quality_columns].isna().any(axis=1)

# Also flag invalid currencies.

sales.loc[
    ~sales["currency_valid"],
    "data_quality_issue"
] = True

records_requiring_review = int(
    sales["data_quality_issue"].sum()
)

print(
    f"\n  Records requiring review: "
    f"{records_requiring_review}"
)

# Remove records missing fields required for sales calculation.
#
# In a production environment, these could instead be routed
# to a separate review/quarantine table.

sales = sales.dropna(
    subset=[
        "order_id",
        "product",
        "quantity",
        "unit_price"
    ]
).copy()


# ============================================================
# 11. CALCULATE SALES
# ============================================================

print("\n[10/12] Calculating sales metrics...")

sales["quantity"] = pd.to_numeric(
    sales["quantity"],
    errors="coerce"
)

sales["unit_price"] = pd.to_numeric(
    sales["unit_price"],
    errors="coerce"
)

sales["price_usd"] = (
    sales["unit_price"]
    * sales["currency"].map(exchange_rates)
)

sales["sales_usd"] = (
    sales["quantity"]
    * sales["price_usd"]
)

sales["sales_usd"] = sales["sales_usd"].round(2)

print("  USD conversion completed.")
print("  Sales totals calculated.")


# ============================================================
# 12. CLEAN INVENTORY
# ============================================================

print("\n[11/12] Cleaning inventory data...")

inventory["country"] = (
    inventory["country"]
    .astype("string")
    .str.strip()
    .replace(country_map)
)

inventory["product"] = (
    inventory["product"]
    .astype("string")
    .str.strip()
    .str.lower()
    .replace(product_map)
)

inventory["inventory_date"] = pd.to_datetime(
    inventory["inventory_date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

inventory["quantity"] = pd.to_numeric(
    inventory["quantity"],
    errors="coerce"
)

inventory = inventory.dropna(
    subset=[
        "product",
        "country",
        "inventory_date",
        "quantity"
    ]
).copy()


# ============================================================
# 13. SAVE CLEANED CSV FILES
# ============================================================

print("\n[12/12] Saving cleaned datasets...")

sales.to_csv(
    CLEANED_SALES_FILE,
    index=False
)

inventory.to_csv(
    CLEANED_INVENTORY_FILE,
    index=False
)

print(f"  Saved: {CLEANED_SALES_FILE}")
print(f"  Saved: {CLEANED_INVENTORY_FILE}")


# ============================================================
# 14. LOAD DATA INTO SQLITE
# ============================================================

print("\nLoading cleaned data into SQLite...")

conn = sqlite3.connect(DATABASE_FILE)

sales.to_sql(
    "international_sales",
    conn,
    if_exists="replace",
    index=False
)

inventory.to_sql(
    "inventory",
    conn,
    if_exists="replace",
    index=False
)

print(f"  Database: {DATABASE_FILE}")


# ============================================================
# 15. SQL REPORTING QUERIES
# ============================================================

print("\nRunning SQL reporting queries...")

sql_results = []


# ------------------------------------------------------------
# Sales by country
# ------------------------------------------------------------

query_country = """
SELECT
    country,
    ROUND(SUM(sales_usd), 2) AS total_sales,
    SUM(quantity) AS total_units
FROM international_sales
GROUP BY country
ORDER BY total_sales DESC;
"""

country_results = pd.read_sql_query(
    query_country,
    conn
)

sql_results.append(
    "SALES BY COUNTRY\n"
    + country_results.to_string(index=False)
)


# ------------------------------------------------------------
# Sales by product
# ------------------------------------------------------------

query_product = """
SELECT
    product,
    ROUND(SUM(sales_usd), 2) AS total_sales,
    SUM(quantity) AS total_units
FROM international_sales
GROUP BY product
ORDER BY total_sales DESC;
"""

product_results = pd.read_sql_query(
    query_product,
    conn
)

sql_results.append(
    "SALES BY PRODUCT\n"
    + product_results.to_string(index=False)
)


# ------------------------------------------------------------
# Inventory by country
# ------------------------------------------------------------

query_inventory = """
SELECT
    country,
    SUM(quantity) AS inventory_units
FROM inventory
GROUP BY country
ORDER BY inventory_units DESC;
"""

inventory_results = pd.read_sql_query(
    query_inventory,
    conn
)

sql_results.append(
    "INVENTORY BY COUNTRY\n"
    + inventory_results.to_string(index=False)
)


# ------------------------------------------------------------
# Country sales + inventory
# ------------------------------------------------------------

query_country_summary = """
SELECT
    s.country,
    ROUND(SUM(s.sales_usd), 2) AS total_sales,
    SUM(s.quantity) AS units_sold,
    COALESCE(i.inventory_units, 0) AS inventory_units
FROM international_sales s
LEFT JOIN (
    SELECT
        country,
        SUM(quantity) AS inventory_units
    FROM inventory
    GROUP BY country
) i
    ON s.country = i.country
GROUP BY s.country, i.inventory_units
ORDER BY total_sales DESC;
"""

country_summary_results = pd.read_sql_query(
    query_country_summary,
    conn
)

sql_results.append(
    "COUNTRY SALES + INVENTORY\n"
    + country_summary_results.to_string(index=False)
)


# ============================================================
# 16. SAVE SQL RESULTS
# ============================================================

with SQL_RESULTS_FILE.open("w", encoding="utf-8") as f:
    f.write(
        "\n\n".join(sql_results)
    )

print(f"  SQL results saved: {SQL_RESULTS_FILE}")


# ============================================================
# 17. GENERATE DATA QUALITY REPORT
# ============================================================

rows_after_cleaning = len(sales)

missing_total = int(
    missing_by_column.sum()
)

total_sales = float(
    sales["sales_usd"].sum()
)

total_units = int(
    sales["quantity"].sum()
)

countries = int(
    sales["country"].nunique()
)

products = int(
    sales["product"].nunique()
)

qa_report = f"""
DATA QUALITY REPORT
===================

Pipeline:
International Merchandising Data Quality & Reporting Pipeline

Source files:
- sales_us.csv
- sales_europe.csv
- inventory.csv

SALES DATA
----------

Rows received:                 {rows_received}
Rows after cleaning:           {rows_after_cleaning}

Duplicate transactions:        {duplicates}
Missing values detected:       {missing_total}
Invalid currencies:            {invalid_currency_count}
Records requiring review:      {records_requiring_review}

STANDARDIZATION
---------------

Countries standardized:        Yes
Dates standardized:            Yes
Products standardized:         Yes
Currency conversion:           Yes

Currency rates:
- USD = 1.00
- EUR = 1.16
- GBP = 1.34
- CAD = 0.73
- JPY = 0.0067

Note:
Exchange rates are illustrative/static values used solely
for demonstration purposes. They are not live financial data.

BUSINESS METRICS
----------------

Total sales (USD):             ${total_sales:,.2f}
Total units sold:              {total_units:,}
Countries represented:         {countries}
Products represented:          {products}

OUTPUTS
-------

Cleaned sales CSV:
{CLEANED_SALES_FILE}

Cleaned inventory CSV:
{CLEANED_INVENTORY_FILE}

SQLite database:
{DATABASE_FILE}

SQL results:
{SQL_RESULTS_FILE}

PIPELINE STATUS
---------------

Raw data ingestion:            COMPLETE
Source combination:            COMPLETE
Country normalization:         COMPLETE
Date normalization:            COMPLETE
Product normalization:         COMPLETE
Currency validation:           COMPLETE
Duplicate detection:           COMPLETE
Missing-value detection:       COMPLETE
Currency conversion:           COMPLETE
Sales calculation:             COMPLETE
SQLite loading:                COMPLETE
SQL reporting:                 COMPLETE
QA reporting:                  COMPLETE
"""

QA_REPORT_FILE.write_text(
    qa_report.strip(),
    encoding="utf-8"
)

print(f"  QA report saved: {QA_REPORT_FILE}")


# ============================================================
# 18. CLOSE DATABASE
# ============================================================

conn.close()


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PIPELINE COMPLETE")
print("=" * 70)

print(f"""
Cleaned sales rows:       {rows_after_cleaning}
Duplicate records:        {duplicates}
Missing values detected:  {missing_total}
Records for review:       {records_requiring_review}

Total sales:              ${total_sales:,.2f}
Total units:              {total_units:,}
Countries:                {countries}
Products:                 {products}

Output directory:
{OUTPUT_DIR}
""")