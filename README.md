# International Merchandising Data Quality & Reporting Pipeline

## Overview

This project simulates an international merchandising data environment in which sales and inventory data arrive from multiple markets with inconsistent country identifiers, date formats, currencies, product naming conventions, duplicate records, and missing values.

The pipeline uses **Python and Pandas** to ingest, clean, standardize, validate, and transform the raw data before loading the results into **SQLite** for downstream SQL analysis and reporting.

The project focuses on the data-quality and reporting challenges that arise when combining operational data from multiple regional sources.

### Demo Video
https://github.com/user-attachments/assets/cea6ecad-bfbe-491f-8135-23ffd8837dea


---

## Project Objective

The goal is to demonstrate an end-to-end workflow for:

* Multi-source data ingestion
* ETL and data transformation
* Data cleaning and standardization
* Data validation and quality assurance
* Duplicate detection and removal
* Missing-value detection
* Currency normalization
* Product-name standardization
* Large-scale data workflow design
* Relational database loading
* SQL-based reporting
* Automated data-quality reporting
* Reproducible data processing

This is a **simulated international merchandising environment** using a small dataset. The purpose is to demonstrate the workflow and technical approach rather than reproduce proprietary company data.

---

## Architecture

```text
                    RAW DATA
                       │
          ┌────────────┴────────────┐
          │                         │
   sales_us.csv             sales_europe.csv
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
                Python / Pandas
                       │
                       ▼
              Combine Data Sources
                       │
                       ▼
              Country Normalization
                       │
                       ▼
                Date Normalization
                       │
                       ▼
              Product Normalization
                       │
                       ▼
              Currency Validation
                       │
                       ▼
             Duplicate Detection
                       │
                       ▼
            Missing-Value Detection
                       │
                       ▼
              Currency Conversion
                       │
                       ▼
              Sales Calculations
                       │
                       ▼
                Cleaned CSV
                       │
                       ▼
                     SQLite
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        SQL Reporting      QA Reporting
```

Inventory data follows a separate cleaning workflow before being loaded into the same SQLite database.

---

## Project Structure

```text
international-merchandising-pipeline/
│
├── data/
│   ├── sales_us.csv
│   ├── sales_europe.csv
│   └── inventory.csv
│
├── scripts/
│   └── pipeline.py
│
├── output/
│   ├── cleaned_sales.csv
│   ├── cleaned_inventory.csv
│   ├── data_quality_report.txt
│   ├── sql_results.txt
│   └── international_merchandising.db
│
└── README.md
```

---

## Raw Data

The project intentionally uses three raw source files.

### `sales_us.csv`

Contains simulated U.S. sales transactions.

The data includes multiple representations of the United States:

```text
United States
USA
US
```

These represent the type of inconsistent identifiers that can occur when data originates from different systems or business partners.

### `sales_europe.csv`

Contains simulated European sales transactions.

This file intentionally contains additional inconsistencies, including:

* Germany / DE
* United Kingdom / UK
* Multiple date formats
* EUR and GBP currencies
* Product naming differences such as `Sandalen` and `Sandals`
* Duplicate transaction records

### `inventory.csv`

Contains simulated inventory quantities by product and country.

---

## Data Quality Challenges

The pipeline intentionally introduces and detects several common operational-data problems.

### 1. Country inconsistencies

Raw values such as:

```text
United States
USA
US
Germany
DE
United Kingdom
UK
```

are standardized to:

```text
United States
Germany
United Kingdom
```

This creates a consistent country dimension for downstream reporting.

---

### 2. Date inconsistencies

Source systems use different date formats, including:

```text
08/01/2026
2026-08-01
01.08.2026
2026/08/01
```

The pipeline converts these values to a consistent format:

```text
YYYY-MM-DD
```

For example:

```text
2026-08-01
```

---

### 3. Currency differences

Transactions may be denominated in different currencies.

The project supports:

```text
USD
EUR
GBP
CAD
JPY
```

Illustrative static exchange rates are used for demonstration:

```python
exchange_rates = {
    "USD": 1.00,
    "EUR": 1.16,
    "GBP": 1.34,
    "CAD": 0.73,
    "JPY": 0.0067
}
```

The rates are **illustrative/static values and are not live financial data**.

Local-currency prices are converted to USD before calculating total sales.

---

### 4. Duplicate transactions

Duplicate records are deliberately introduced into the sales data.

The pipeline identifies duplicate `order_id` values and removes duplicate transactions while retaining the first occurrence.

This demonstrates a basic transaction-level data-quality control.

---

### 5. Missing values

The pipeline deliberately introduces missing values in fields such as:

* Country
* Quantity

Missing values are identified using Pandas and records requiring review are flagged.

Rather than treating all missing data as automatically valid or invalid, the pipeline distinguishes data-quality issues that may require business review.

---

### 6. Product-name inconsistencies

Product names are normalized to consistent values.

Examples include:

```text
Running Shoes
running shoes
RUNNING SHOES
Run Shoes
```

which are standardized to:

```text
Running Shoes
```

The demonstration also maps:

```text
Sandalen
```

to:

```text
Sandals
```

These mappings are project-specific demonstration rules rather than a universal translation system.

---

## ETL Pipeline

The main processing script is:

```text
scripts/pipeline.py
```

The pipeline performs the following steps:

```text
1. Load raw files
       ↓
2. Combine sales sources
       ↓
3. Introduce test data-quality issues
       ↓
4. Standardize country identifiers
       ↓
5. Standardize date formats
       ↓
6. Standardize product names
       ↓
7. Validate currencies
       ↓
8. Detect duplicate transactions
       ↓
9. Detect missing values
       ↓
10. Convert prices to USD
       ↓
11. Calculate total sales
       ↓
12. Clean inventory data
       ↓
13. Save cleaned CSV files
       ↓
14. Load data into SQLite
       ↓
15. Run SQL reporting queries
       ↓
16. Generate a data-quality report
```

---

## Sales Calculation

The pipeline calculates USD-denominated sales using:

```python
df["sales_usd"] = (
    df["quantity"]
    * df["unit_price"]
    * df["currency"].map(exchange_rates)
)
```

This creates a consistent monetary field for cross-country reporting.

---

## SQLite Database

Cleaned data is loaded into:

```text
output/international_merchandising.db
```

The database contains tables including:

```text
international_sales
inventory
```

Example loading operation:

```python
df.to_sql(
    "international_sales",
    conn,
    if_exists="replace",
    index=False
)
```

SQLite provides a lightweight relational database layer for downstream SQL analysis.

---

## SQL Reporting

The pipeline generates SQL-based reporting for several business questions.

### Sales by Country

```sql
SELECT
    country,
    SUM(sales_usd) AS total_sales
FROM international_sales
GROUP BY country
ORDER BY total_sales DESC;
```

### Sales by Product

```sql
SELECT
    product,
    SUM(sales_usd) AS total_sales
FROM international_sales
GROUP BY product
ORDER BY total_sales DESC;
```

### Inventory by Country

```sql
SELECT
    country,
    SUM(quantity) AS inventory
FROM inventory
GROUP BY country;
```

The results are saved to:

```text
output/sql_results.txt
```

---

## Data Quality Report

The pipeline automatically generates:

```text
output/data_quality_report.txt
```

The report summarizes:

* Rows received
* Rows after cleaning
* Duplicate transactions
* Missing values
* Invalid currencies
* Records requiring review
* Standardization steps
* Business-level metrics
* Pipeline completion status

For the current simulated dataset, the pipeline detects the deliberately introduced duplicate and missing-value issues.

This creates an auditable summary of the transformation process rather than silently modifying the source data.

---

## Example Output

The pipeline currently produces metrics including:

```text
Cleaned sales rows:       26
Duplicate records:        3
Missing values detected:  2
Records for review:       2

Total sales:              $2,521.08
Total units:              52
Countries:                3
Products:                 6
```

The exact values will change if the raw data is modified.

---

## Running the Project

### Requirements

Python 3.11+ is recommended.

Install the project dependency:

```bash
python3 -m pip install pandas
```

`pathlib` and `sqlite3` are part of Python's standard library and do not need to be installed separately.

### Run the pipeline

From the project root:

```bash
python3 scripts/pipeline.py
```

The pipeline will create the output files automatically.

### Inspect the QA report

```bash
cat output/data_quality_report.txt
```

### Inspect SQL results

```bash
cat output/sql_results.txt
```

---

## Outputs

After a successful run, the `output/` directory contains:

```text
cleaned_sales.csv
cleaned_inventory.csv
data_quality_report.txt
sql_results.txt
international_merchandising.db
```

### `cleaned_sales.csv`

Standardized sales data containing fields such as:

```text
order_id
country
order_date
currency
product
quantity
unit_price
price_usd
sales_usd
data_quality_issue
```

### `cleaned_inventory.csv`

Standardized inventory data.

### `data_quality_report.txt`

Automated QA summary of the pipeline.

### `sql_results.txt`

Results of the SQL reporting queries.

### `international_merchandising.db`

SQLite database containing the cleaned datasets.

---

## Business Questions

The cleaned dataset can support questions such as:

* Which countries generate the most sales?
* Which products generate the most revenue?
* How many units are sold by country?
* How much inventory is available by country?
* Which records require data-quality review?
* Are there duplicate transactions?
* Are all currencies recognized?
* Are country identifiers standardized?
* Are transaction dates consistently formatted?
* Which products require name normalization?

---

## Limitations

This project is intentionally small and simulated.

It does **not** represent:

* Proprietary merchandising data
* Live exchange rates
* Real distributor systems
* Production-scale data volumes
* Real-time report scheduling
* Enterprise data governance platforms
* Actual international business processes

The purpose is to demonstrate the technical workflow used to handle common multi-source operational-data problems.

---

## Skills Demonstrated

### Data & Analytics

* Data cleaning
* Data validation
* Data quality assurance
* Data reconciliation
* Data standardization
* Statistical/quantitative analysis
* KPI development
* Business reporting

### ETL & Data Management

* Multi-source ingestion
* ETL pipeline development
* Data transformation
* Duplicate detection
* Missing-value handling
* Data normalization
* Relational database loading
* SQLite

### Programming

* Python
* Pandas
* File-based data processing
* Reproducible workflows

### SQL & Reporting

* SQL aggregation
* `GROUP BY`
* `SUM`
* `JOIN`
* Sorting and filtering
* Country/product reporting
* Inventory reporting

### Data Governance & QA

* Data-quality rules
* Validation checks
* Records requiring review
* Data dictionaries/documentation
* QA reporting
* Auditability

---

## Why This Project Matters

International operational data often arrives from multiple sources with differences in formatting, naming conventions, currencies, and data quality.

This project demonstrates an end-to-end approach for turning those inconsistent source files into standardized, validated, queryable data that can support downstream reporting and business decision-making.

The emphasis is on **data integrity, repeatability, quality assurance, and reporting**, rather than simply producing a visualization.

```

One change I'd make **before you publish the project to GitHub**: add the `data_dictionary.csv` you mentioned as a documentation artifact, and then add a small **Power BI screenshot** to this README. That will connect the Python/SQLite pipeline to the reporting side of the project and make the workflow much easier for a recruiter to understand.
```
