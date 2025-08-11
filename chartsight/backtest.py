from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import datetime as dt

try:
    import yfinance as yf
except Exception:
    yf = None

def fetch_history(ticker: str, period: str = "5y", interval: str = "1d") -> Optional[pd.DataFrame]:
    if yf is None:
        return None
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if isinstance(df, pd.DataFrame) and not df.empty:
            df = df.rename(columns=str.title)
            return df
    except Exception:
        return None
    return None

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    h,l,c = df["High"], df["Low"], df["Close"]
    tr = np.maximum(h-l, np.maximum(abs(h-c.shift()), abs(l-c.shift())))
    return tr.rolling(window).mean()

def simple_level_backtest(df: pd.DataFrame, entry_level: float, direction: str, tp_mult: float = 1.0, sl_mult: float = 0.5) -> Dict[str, Any]:
    """
    Enter when Close crosses entry_level in chosen direction.
    Take profit at entry +/- ATR*tp_mult; stop at entry -/+ ATR*sl_mult.
    """
    if df is None or df.empty: 
        return {"ok": False, "msg": "No data"}
    a = atr(df).fillna(method="bfill")
    entries = []
    wins = losses = 0
    for i in range(1, len(df)):
        prev = df["Close"].iloc[i-1]
        cur = df["Close"].iloc[i]
        cur_atr = a.iloc[i]
        if direction == "long" and prev < entry_level <= cur:
            tp = entry_level + cur_atr*tp_mult
            sl = entry_level - cur_atr*sl_mult
            outcome = _simulate_from(df.iloc[i+1:], tp, sl, direction)
            entries.append(outcome)
        elif direction == "short" and prev > entry_level >= cur:
            tp = entry_level - cur_atr*tp_mult
            sl = entry_level + cur_atr*sl_mult
            outcome = _simulate_from(df.iloc[i+1:], tp, sl, direction)
            entries.append(outcome)
    if entries:
        wins = sum(1 for e in entries if e["result"] == "TP")
        losses = sum(1 for e in entries if e["result"] == "SL")
        wr = wins / len(entries)
    else:
        wr = 0.0
    return {"ok": True, "trades": len(entries), "win_rate": wr, "wins": wins, "losses": losses}

def _simulate_from(df_slice: pd.DataFrame, tp: float, sl: float, direction: str):
    for _, row in df_slice.iterrows():
        hi, lo = row["High"], row["Low"]
        if direction == "long":
            if lo <= sl: return {"result": "SL"}
            if hi >= tp: return {"result": "TP"}
        else:
            if hi >= sl: return {"result": "SL"}
            if lo <= tp: return {"result": "TP"}
    return {"result": "SL"}  # default fail-safe