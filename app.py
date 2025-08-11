import streamlit as st
from PIL import Image
from chartsight.image_processing import analyze_image
from chartsight.recommend import generate_plan
from chartsight.backtest import fetch_history, simple_level_backtest

st.set_page_config(page_title="ChartSight AI — MVP", page_icon="📈", layout="wide")
st.title("📈 ChartSight AI — MVP (Streamlit Cloud)")
st.caption("Upload a chart screenshot → get structure + a trading plan. **Educational only, not financial advice.**")

c1, c2 = st.columns([1,1])
with c1:
    st.header("1) Upload Chart")
    img_file = st.file_uploader("Upload a chart screenshot (PNG/JPG)", type=["png","jpg","jpeg"])
    if img_file:
        pil = Image.open(img_file)
        st.image(pil, caption="Uploaded Chart", use_column_width=True)
        analysis = analyze_image(pil)
    else:
        analysis = None

with c2:
    st.header("2) Calibrate & Generate Plan")
    price_min = st.number_input("Chart lower price (approx)", value=0.0, step=0.1)
    price_max = st.number_input("Chart upper price (approx)", value=0.0, step=0.1)
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
        })

        st.subheader("🎯 Trading Plan (Heuristic)")
        cols = st.columns(4)
        cols[0].metric("Entry", f"{plan['entry']:.4f}" if plan['entry'] else "—")
        cols[1].metric("Target 1", f"{plan['target1']:.4f}" if plan['target1'] else "—")
        cols[2].metric("Target 2", f"{plan['target2']:.4f}" if plan['target2'] else "—")
        cols[3].metric("Stop", f"{plan['stop']:.4f}" if plan['stop'] else "—")
        st.caption("Notes: " + "; ".join(plan.get("notes", [])))
        st.caption(plan["disclaimer"])

        st.divider()
        st.subheader("🧪 Quick Historical Sanity Check (optional)")
        ticker = st.text_input("Ticker (e.g., AAPL)")
        tp_mult = st.slider("TP ATR multiple", 0.5, 3.0, 1.0, 0.1)
        sl_mult = st.slider("SL ATR multiple", 0.2, 3.0, 0.5, 0.1)
        dir_choice = st.selectbox("Direction", ["auto (from bias)", "long", "short"])

        if st.button("Run Backtest") and ticker:
            df = fetch_history(ticker, period="5y", interval="1d")
            if df is None or df.empty:
                st.warning("Could not fetch data.")
            else:
                entry = plan["entry"] or (plan["resistance"] if "Buy" in plan["bias"] else plan["support"])
                direction = dir_choice if not dir_choice.startswith("auto") else ("long" if "Buy" in plan["bias"] else ("short" if "Sell" in plan["bias"] else "long"))
                if entry:
                    res = simple_level_backtest(df, float(entry), direction, tp_mult=tp_mult, sl_mult=sl_mult)
                    if res.get("ok"):
                        st.json({"Trades": res["trades"], "Win rate %": round(res["win_rate"]*100,2),
                                 "Wins": res["wins"], "Losses": res["losses"]})
                    else:
                        st.warning(res.get("msg","Backtest failed"))
                else:
                    st.info("No entry level to test.")

st.divider()
st.caption("© ChartSight AI — MVP. Educational use only. Not financial advice.")