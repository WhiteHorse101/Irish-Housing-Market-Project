# 🏠 Irish Housing Market — Data Pipeline & Analysis

An end-to-end data project on Ireland's residential property market: an automated pipeline that acquires and cleans official government sales data, and an in-depth exploratory analysis that goes well past surface-level charts — catching a currency-encoding bug, an inconsistent category, and a genuine institutional-sale anomaly hiding in the price column before trusting a single statistic.

Built to demonstrate a realistic data engineering + analytics workflow: **acquisition → cleaning → analysis → (in progress) communication.**

---

## 📊 What This Is

Ireland's [Property Price Register](https://www.propertypriceregister.ie) publishes every residential sale in the country as open data. This project pulls the last 24 months of that register, turns it into a clean dataset, and digs into what the numbers actually say — and, just as importantly, where they can't be trusted at face value.

## 🔍 Key Findings

- **The "average price" is misleading, and it's explainable, not just noisy.** Mean (€459k) sits far above median (€355k) because a small number of transactions are entire apartment *blocks* sold to institutional investors in a single register entry — e.g. `"202 Residential Units, Block 1, Spencer Place"` at €88.4M is a normal ~€437k/unit price, multiplied by 202 and logged as if it were one home.
- **A flat price cutoff isn't good enough to catch these.** Built a two-signal detection approach — regex matching on bulk-sale language in addresses, combined with a per-county statistical outlier test (median/IQR on log-transformed prices, since raw-price IQR is too aggressive for a naturally skewed distribution like housing prices) — validated against real cases (e.g. one anomalous €21M "sale" stood out clearly against five *other* units in the exact same development, all priced normally at €396k–€471k).
- **A currency-encoding bug would have silently corrupted every price.** The source file encodes `€` as a single Windows-1252 byte, not UTF-8 — caught before it became a wrong number three steps downstream.
- **Not every "cheap" sale is explained by the same thing.** Only ~29% of the bottom 1% of prices are flagged as below-market transactions — the rest are likely genuine small-value sales, and the analysis says so rather than forcing a tidy explanation onto data that doesn't support one.

## 🗂️ Project Structure

```
├── data_pipeline.py       # Download → extract → filter (last 24mo) → clean → save
├── notebooks/
│   └── EDA.ipynb          # Full exploratory analysis, outlier methodology, findings
├── data/
│   └── ppr_clean.csv      # Cleaned, filtered output (gitignored: raw zip/csv)
├── requirements.txt
└── README.md
```

## 🛠️ Tech Stack

`Python` · `Pandas` · `NumPy` · `Matplotlib` · `Jupyter` · *(planned: `Streamlit` + `Plotly` dashboard)*

## ⚙️ How to Run

```bash
# 1. Clone and enter the project
git clone https://github.com/WhiteHorse101/Irish-Housing-Market-Project.git
cd Irish-Housing-Market-Project

# 2. Set up the environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run the pipeline (downloads + cleans the dataset)
python data_pipeline.py

# 4. Explore the analysis
jupyter notebook notebooks/EDA.ipynb
```

## 🧠 Notable Engineering Decisions

- **Single source of truth:** every cleaning decision (encoding fix, category consolidation, column drops) lives in `data_pipeline.py`, not scattered across notebook cells — so the notebook and any future dashboard always see identical, correctly-cleaned data.
- **Documented, not silent, data-quality calls:** ambiguous or messy fields (`Not Full Market Price`, the now-empty `Size Band` column, the outlier flag) are kept and explained rather than quietly dropped — the goal is a defensible analysis, not just a clean-looking one.
- **Source legitimacy checked before writing a line of code:** confirmed the Property Price Register has no scraping restrictions and no bot-detection barrier before building anything against it.

## 🗺️ Roadmap

- [ ] Interactive Streamlit dashboard (county/date/property-type filters, price trend & distribution views)
- [ ] County-level price comparison and time-trend analysis
- [ ] Quantify the price impact of including vs. excluding non-market-price sales
- [ ] Deploy to Streamlit Community Cloud for a live public link

## 📄 Data Attribution

Data sourced from the [Residential Property Price Register](https://www.propertypriceregister.ie), published by the Property Services Regulatory Authority (PSRA), Ireland. Publicly available government data, used here for non-commercial analysis.
