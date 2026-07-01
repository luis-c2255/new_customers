# 📊 Retail Insights Dashboard

An interactive Streamlit dashboard for retail customer and sales analytics — RFM
segmentation, sales performance, and geographic breakdowns — built for exploring
customer value and commercial trends at a glance.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-charts-3F4F75)

## Features

- **Global KPIs** — revenue, profit, margin, order count, average order value, and
  active customers, all responsive to filters.
- **RFM Customer Segmentation** — automatic scoring (Recency, Frequency, Monetary)
  that classifies customers into VIPs, At-Risk, New, Dormant, and Regular segments,
  with a searchable/downloadable customer explorer per segment.
- **Sales & Product Performance** — monthly revenue/profit trend, a profit-colored
  treemap by category and sub-category, and a top-10 products ranking.
- **Geographic View** — a U.S. choropleth map and top-10 states by revenue, with
  automatic normalization of city names (e.g. Chicago, Houston) to their state.
- **Global filters** — gender, product category, business segment, and date range,
  all applied consistently across every tab.
- **CSV export** — download any customer segment list directly from the app.

## Project Structure

```
.
├── app.py                # Streamlit application
├── customer_data.csv     # Customer demographic & profile data
├── order_data.csv        # Order/transaction data
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- `customer_data.csv` and `order_data.csv` in the same folder as `app.py`

### Installation

```bash
pip install streamlit pandas plotly
```

### Run the app

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

## Data

The dashboard joins two datasets on `Customer ID`:

**`customer_data.csv`** — one row per customer
| Column | Description |
|---|---|
| `Customer ID` | Unique customer identifier |
| `Age`, `Gender` | Demographics |
| `Location` | U.S. state (or a small number of major cities, normalized in-app) |
| `Purchase Amount (USD)`, `Previous Purchases` | Historical purchase signals |
| `Subscription Status`, `Discount Applied`, `Payment Method`, `Frequency of Purchases` | Behavioral attributes |

**`order_data.csv`** — one row per order line
| Column | Description |
|---|---|
| `Order Id`, `Order Date`, `Customer ID` | Order identifiers |
| `Ship Mode`, `Segment`, `Category`, `Sub Category`, `Product Id` | Order attributes |
| `cost price`, `List Price`, `Quantity`, `Discount Percent` | Used to compute revenue, cost, and profit |

`Total_Sales`, `Total_Cost`, and `Profit` are derived columns calculated at load time.

### RFM Methodology

Each customer is scored 1–4 (4 = best) on three dimensions, using rank-based
quartiles to avoid errors from duplicate values:

- **Recency (R)** — days since the customer's last order
- **Frequency (F)** — total number of orders placed
- **Monetary (M)** — total amount spent

Scores combine into five segments:

| Segment | Logic |
|---|---|
| 🏆 Campeones (VIP) | R ≥ 3, F ≥ 3, M ≥ 3 |
| ⚠️ En Riesgo de Abandono | R ≤ 2, F ≥ 3, M ≥ 3 |
| 🌱 Nuevos Clientes | R ≥ 3, F ≤ 2 |
| 💤 Clientes Dormidos | R ≤ 2, F ≤ 2 |
| Clientes Regulares | Everything else |

## Tech Stack

- [Streamlit](https://streamlit.io/) — app framework and UI
- [Pandas](https://pandas.pydata.org/) — data processing
- [Plotly Express](https://plotly.com/python/plotly-express/) — interactive charts

## Notes & Limitations

- A handful of rows in `Location` are cities rather than states; these are mapped
  to their state for the geographic view. Any location that can't be resolved is
  excluded from the map and flagged with a warning in the app.
- Customers with no matching orders (or vice versa) are dropped by the inner join,
  since RFM and sales metrics require both purchase and profile data.

## License

This project is provided as-is for portfolio and educational purposes.
