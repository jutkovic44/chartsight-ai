from typing import Dict, Any, Optional, Tuple

def derive_levels_from_pixels(levels_px, image_height, price_min: float = None, price_max: float = None):
    """Map pixel y-levels to price using linear interpolation if bounds are provided.
    If bounds unknown, return normalized 0..1 scale.
    """
    if not levels_px:
        return []
    # Pixel y increases downward; typical chart price increases upward
    if price_min is not None and price_max is not None:
        mapped = []
        for y in levels_px:
            # y=0 (top) -> price_max, y=image_height (bottom) -> price_min
            price = price_max - (price_max - price_min) * (y / image_height)
            mapped.append(price)
        mapped = sorted(mapped)
        return mapped
    else:
        return sorted([1.0 - (y / image_height) for y in levels_px])

def choose_key_levels(levels: list, current_price: Optional[float] = None):
    """Pick candidate support/resistance around current price."""
    if not levels:
        return None, None
    levels_sorted = sorted(levels)
    if current_price is None:
        # pick two central levels
        mid = len(levels_sorted)//2
        res = levels_sorted[mid] if mid < len(levels_sorted) else None
        sup = levels_sorted[mid-1] if mid-1 >= 0 else None
        return sup, res
    # Find nearest below/above
    below = [lv for lv in levels_sorted if lv <= current_price]
    above = [lv for lv in levels_sorted if lv >= current_price]
    sup = below[-1] if below else (levels_sorted[0] if levels_sorted else None)
    res = above[0] if above else (levels_sorted[-1] if levels_sorted else None)
    return sup, res

def simple_recommendation(trend_hint: str,
                          triangle_hint: Optional[str],
                          support: Optional[float],
                          resistance: Optional[float],
                          current_price: Optional[float]) -> Dict[str, Any]:
    """Generate a basic plan (entry/targets/stop) using detected structure."""
    bias = "Neutral"
    notes = []
    entry = None
    t1 = t2 = stop = None

    if triangle_hint:
        notes.append(f"Triangle hint detected: {triangle_hint}")

    if current_price is not None and support is not None and resistance is not None:
        height = abs(resistance - support) if (resistance and support) else None
        if trend_hint.startswith("Uptrend") or (triangle_hint and "Asc" in triangle_hint):
            bias = "Buy-breakout-bias"
            entry = resistance * 1.001  # minor buffer
            t1 = resistance + (0.5 * (height or (0.02 * current_price)))
            t2 = resistance + (1.0 * (height or (0.04 * current_price)))
            stop = support - (0.25 * (height or (0.02 * current_price)))
        elif trend_hint.startswith("Downtrend"):
            bias = "Sell-breakdown-bias"
            entry = support * 0.999
            t1 = support - (0.5 * (height or (0.02 * current_price)))
            t2 = support - (1.0 * (height or (0.04 * current_price)))
            stop = resistance + (0.25 * (height or (0.02 * current_price)))
        else:
            bias = "Range-trade-bias"
            # if near support -> buy to resistance; near resistance -> sell to support
            if abs(current_price - support) < abs(current_price - resistance):
                entry = current_price
                t1 = (current_price + resistance) / 2.0
                t2 = resistance
                stop = support - (0.25 * (height or (0.02 * current_price)))
                notes.append("Closer to support: mean-reversion long idea.")
            else:
                bias = "Sell-range-bias"
                entry = current_price
                t1 = (current_price + support) / 2.0
                t2 = support
                stop = resistance + (0.25 * (height or (0.02 * current_price)))

    return {
        "bias": bias,
        "entry": entry,
        "target1": t1,
        "target2": t2,
        "stop": stop,
        "notes": notes
    }