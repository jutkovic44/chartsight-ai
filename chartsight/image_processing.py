import cv2
import numpy as np
from typing import Dict, Any, Optional
from PIL import Image

try:
    import pytesseract
except Exception:
    pytesseract = None

def analyze_image(pil_image: Image.Image) -> Dict[str, Any]:
    img = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    v = np.median(gray)
    edges = cv2.Canny(gray, int(max(0,0.66*v)), int(min(255,1.33*v)))
    linesP = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=120, minLineLength=60, maxLineGap=10)

    h, w = gray.shape[:2]
    num_other = 0; num_h = 0; levels_px = []

    if linesP is not None:
        lines = linesP.reshape(-1,4)
        horizontals = []
        others = []
        for x1,y1,x2,y2 in lines:
            dx = x2-x1; dy = y2-y1
            slope = 1e9 if dx == 0 else dy/dx
            if abs(slope) < 0.15:
                horizontals.append((x1,y1,x2,y2))
            else:
                others.append((x1,y1,x2,y2))
        num_h = len(horizontals); num_other = len(others)
        ys = [y1 for _,y1,_,_ in horizontals] + [y2 for *_,y2 in horizontals]
        ys = [y for y in ys if int(0.05*h) < y < int(0.95*h)]
        ys.sort()
        if ys:
            cluster = [ys[0]]; clusters=[]
            for y in ys[1:]:
                if abs(y - np.mean(cluster)) <= 12:
                    cluster.append(y)
                else:
                    clusters.append(int(np.mean(cluster))); cluster=[y]
            clusters.append(int(np.mean(cluster)))
            levels_px = clusters

    trend = "Unknown"
    if linesP is not None:
        slopes = []
        for x1,y1,x2,y2 in linesP.reshape(-1,4):
            dx = x2-x1; dy = y2-y1
            if dx == 0: continue
            slopes.append(dy/dx)
        if slopes:
            m = float(np.mean(slopes))
            if m < -0.1: trend = "Uptrend (lower-left → upper-right)"
            elif m > 0.1: trend = "Downtrend (upper-left → lower-right)"
            else: trend = "Sideways / Range"

    return {
        "image_shape": (h, w),
        "num_horizontal_segments": int(num_h),
        "num_other_segments": int(num_other),
        "levels_px": levels_px,
        "trend_hint": trend,
        "triangle_hint": None,
        "ocr_prices_detected": []
    }