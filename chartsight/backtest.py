import pandas as pd, numpy as np
try: import yfinance as yf
except Exception: yf=None

def fetch_history(ticker: str, period: str = "5y", interval: str = "1d"):
    if yf is None: return None
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if hasattr(df,"empty") and not df.empty:
            return df.rename(columns=str.title)
    except Exception:
        return None
    return None

def atr(df: pd.DataFrame, window: int = 14):
    h,l,c = df["High"], df["Low"], df["Close"]
    tr = np.maximum(h-l, np.maximum(abs(h-c.shift()), abs(l-c.shift())))
    return tr.rolling(window).mean()

def simple_level_backtest(df: pd.DataFrame, entry_level: float, direction: str, tp_mult: float = 1.0, sl_mult: float = 0.5):
    if df is None or df.empty: return {"ok": False, "msg": "No data"}
    a = atr(df).fillna(method="bfill")
    entries=[]; wins=losses=0
    for i in range(1,len(df)):
        prev = df["Close"].iloc[i-1]; cur=df["Close"].iloc[i]; cur_atr=a.iloc[i]
        if direction=="long" and prev < entry_level <= cur:
            tp=entry_level+cur_atr*tp_mult; sl=entry_level-cur_atr*sl_mult
            entries.append(_sim(df.iloc[i+1:], tp, sl, "long"))
        elif direction=="short" and prev > entry_level >= cur:
            tp=entry_level-cur_atr*tp_mult; sl=entry_level+cur_atr*sl_mult
            entries.append(_sim(df.iloc[i+1:], tp, sl, "short"))
    if entries:
        wins=sum(1 for e in entries if e["result"]=="TP"); losses=sum(1 for e in entries if e["result"]=="SL")
        return {"ok": True, "trades": len(entries), "win_rate": wins/len(entries), "wins": wins, "losses": losses}
    return {"ok": True, "trades": 0, "win_rate": 0.0, "wins": 0, "losses": 0}

def _sim(df_slice: pd.DataFrame, tp: float, sl: float, direction: str):
    for _, row in df_slice.iterrows():
        hi, lo = row["High"], row["Low"]
        if direction == "long":
            if lo <= sl: return {"result":"SL"}
            if hi >= tp: return {"result":"TP"}
        else:
            if hi >= sl: return {"result":"SL"}
            if lo <= tp: return {"result":"TP"}
    return {"result":"SL"}