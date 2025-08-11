import streamlit as st
from PIL import Image
import io
import numpy as np
import pandas as pd

from chartsight.image_processing import analyze_image
from chartsight.recommend import generate_plan
from chartsight.backtest import fetch_history, simple_level_backtest

st.set_page_config(page_title="ChartSight AI — MVP", page_icon="📈", layout="wide")

st.title("📈 ChartSight AI — MVP")
st.caption("Upload a chart screenshot → get structure + a trading plan. **Educational only, not financial advice.**")

col1, col2 = st.columns([1,1])

with col1:
    st.header("1) Upload Chart")
    img_file = st.file_uploader("Upload a chart screenshot (PNG/JPG)", type=["png","jpg","jpeg"])
    example_note = st.expander("Tips for best results")
    with example_note:
        st.markdown("""
        - Use a clean screenshot with visible price axis labels on the right.
        - Avoid extra UI panels; crop to the chart region if possible.
        - Candlesticks or line charts both work; candlesticks preferred.
        """)
    if img_file:
        pil = Image.open(img_file)
        st.image(pil, caption="Uploaded Chart", use_column_width=True)
        analysis = analyze_image(pil)
    else:
        analysis = None

with col2:
    st.header("2) Calibrate & Generate Plan")
    st.markdown("If OCR can't read axis prices, set **Price Min/Max** to calibrate levels.")

    price_min = st.number_input("Chart lower price (approx)", value=0.0, step=0.1, help="Price at the bottom of the visible chart area.")
    price_max = st.number_input("Chart upper price (approx)", value=0.0, step=0.1, help="Price at the top of the visible chart area.")
    current_price = st.number_input("Current/Last price (optional)", value=0.0, step=0.1)

    gen = st.button("Generate Trading Plan", type="primary", disabled=(analysis is None))
    if gen and analysis is not None:
        pmin = price_min if price_min > 0 else None
        pmax = price_max if price_max > 0 else None
        cpx = current_price if current_price > 0 else None
        plan = generate_plan(analysis, pmin, pmax, cpx)

        st.subheader("📋 Detected Structure")
        st.json({
            "Trend": analysis.get("trend_hint"),
            "Triangle hint": analysis.get("triangle_hint"),
            "OCR prices": analysis.get("ocr_prices_detected"),
            "Horizontal segments": analysis.get("num_horizontal_segments"),
            "Other segments": analysis.get("num_other_segments"),
        }, expanded=False)

        st.subheader("🎯 Trading Plan (Heuristic)")
        st.markdown(f"**Bias:** {plan['bias']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Entry", f"{plan['entry']:.4f}" if plan['entry'] else "—")
        c2.metric("Target 1", f"{plan['target1']:.4f}" if plan['target1'] else "—")
        c3.metric("Target 2", f"{plan['target2']:.4f}" if plan['target2'] else "—")
        st.metric("Stop", f"{plan['stop']:.4f}" if plan['stop'] else "—")
        st.caption("Notes: " + "; ".join(plan.get("notes", [])))
        st.caption(plan["disclaimer"])

        st.divider()
        st.subheader("🧪 Quick Historical Sanity Check (optional)")
        ticker = st.text_input("Ticker (for backtest fetch, e.g., AAPL)")
        bt_col1, bt_col2, bt_col3 = st.columns(3)
        tp_mult = bt_col1.slider("TP ATR multiple", 0.5, 3.0, 1.0, 0.1)
        sl_mult = bt_col2.slider("SL ATR multiple", 0.2, 3.0, 0.5, 0.1)
        direction = bt_col3.selectbox("Direction", ["auto (from bias)", "long", "short"])

        run_bt = st.button("Run Simple Backtest")
        if run_bt and ticker:
            df = fetch_history(ticker, period="5y", interval="1d")
            if df is None or df.empty:
                st.warning("Could not fetch data (no internet or invalid ticker). Try again locally.")
            else:
                entry = plan["entry"]
                if entry is None and "Buy" in plan["bias"]:
                    entry = plan["resistance"]
                elif entry is None and "Sell" in plan["bias"]:
                    entry = plan["support"]
                dirx = direction
                if dirx.startswith("auto"):
                    dirx = "long" if "Buy" in plan["bias"] else ("short" if "Sell" in plan["bias"] else "long")
                res = simple_level_backtest(df, float(entry), dirx, tp_mult=tp_mult, sl_mult=sl_mult) if entry else {"ok": False, "msg": "No entry"}
                if res.get("ok"):
                    st.json({
                        "Trades": res["trades"],
                        "Win rate": round(res["win_rate"]*100,2),
                        "Wins": res["wins"],
                        "Losses": res["losses"]
                    })
                else:
                    st.warning(res.get("msg","Backtest failed"))

st.divider()
st.caption("© ChartSight AI — MVP. Educational use only. Not financial advice.")