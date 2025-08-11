from typing import Optional, Dict, Any
from .patterns import derive_levels_from_pixels, choose_key_levels, simple_recommendation
DISCLAIMER = "Educational use only. Not financial advice. Markets involve risk."

def generate_plan(analysis: Dict[str, Any],
                  price_min: Optional[float],
                  price_max: Optional[float],
                  current_price: Optional[float]):
    levels_px = analysis.get("levels_px", [])
    mapped = derive_levels_from_pixels(levels_px, analysis["image_shape"][0], price_min, price_max)
    sup, res = choose_key_levels(mapped, current_price=current_price)
    rec = simple_recommendation(analysis.get("trend_hint","Unknown"),
                                analysis.get("triangle_hint"),
                                sup, res, current_price)
    rec["support"] = sup; rec["resistance"] = res; rec["disclaimer"] = DISCLAIMER
    return rec