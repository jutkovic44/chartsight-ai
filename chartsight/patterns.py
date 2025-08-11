from typing import Optional

def derive_levels_from_pixels(levels_px, image_height, price_min: float = None, price_max: float = None):
    if not levels_px: return []
    if price_min is not None and price_max is not None and price_max > price_min:
        mapped = []
        for y in levels_px:
            price = price_max - (price_max - price_min) * (y / image_height)
            mapped.append(price)
        return sorted(mapped)
    return sorted([1.0 - (y / image_height) for y in levels_px])

def choose_key_levels(levels: list, current_price: Optional[float] = None):
    if not levels: return None, None
    lv = sorted(levels)
    if current_price is None:
        mid = len(lv)//2
        res = lv[mid] if mid < len(lv) else None
        sup = lv[mid-1] if mid-1 >= 0 else None
        return sup, res
    below = [x for x in lv if x <= current_price]
    above = [x for x in lv if x >= current_price]
    sup = below[-1] if below else lv[0]
    res = above[0] if above else lv[-1]
    return sup, res

def simple_recommendation(trend_hint: str, triangle_hint, support, resistance, current_price):
    bias="Neutral"; notes=[]; entry=t1=t2=stop=None
    if current_price is not None and support is not None and resistance is not None:
        height = abs(resistance - support) if (resistance and support) else None
        if trend_hint.startswith("Uptrend"):
            bias="Buy-breakout-bias"; entry=resistance*1.001
            t1 = resistance + (0.5 * (height or (0.02 * current_price)))
            t2 = resistance + (1.0 * (height or (0.04 * current_price)))
            stop = support - (0.25 * (height or (0.02 * current_price)))
        elif trend_hint.startswith("Downtrend"):
            bias="Sell-breakdown-bias"; entry=support*0.999
            t1 = support - (0.5 * (height or (0.02 * current_price)))
            t2 = support - (1.0 * (height or (0.04 * current_price)))
            stop = resistance + (0.25 * (height or (0.02 * current_price)))
        else:
            bias="Range-trade-bias"
            if abs(current_price - support) < abs(current_price - resistance):
                entry=current_price; t1=(current_price+resistance)/2.0; t2=resistance
                stop = support - (0.25 * (height or (0.02 * current_price)))
                notes.append("Near support → mean reversion long.")
            else:
                bias="Sell-range-bias"; entry=current_price; t1=(current_price+support)/2.0; t2=support
                stop = resistance + (0.25 * (height or (0.02 * current_price)))
    return {"bias": bias, "entry": entry, "target1": t1, "target2": t2, "stop": stop, "notes": notes}