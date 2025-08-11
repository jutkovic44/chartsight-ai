# ChartSight AI — MVP

Upload a chart screenshot and get a data-driven trading plan (educational only).
This MVP detects basic structure from an image (trend, candidate support/resistance, triangle/channel hints),
optionally fetches OHLC data by ticker for backtesting similar setups, and produces an entry/target/stop plan.

## Quick Start

1) Create & activate a virtual environment (recommended).
2) `pip install -r requirements.txt`
3) Run the app: `streamlit run app.py`

### Notes
- Image parsing is heuristic. For best results, use clean screenshots with visible price axis.
- If OCR cannot read axis prices, you can manually calibrate price levels in the sidebar.
- Backtesting requires internet to fetch data via `yfinance`. If your environment blocks internet,
  the app still works in "image-only" mode and will generate a plan using your manual inputs.

### Educational Only
This is **not financial advice**. For research/education. Trading involves risk.