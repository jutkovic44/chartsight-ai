import cv2
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from PIL import Image

try:
    import pytesseract
except Exception:
    pytesseract = None

def load_image(file) -> np.ndarray:
    if isinstance(file, Image.Image):
        img = cv2.cvtColor(np.array(file), cv2.COLOR_RGBA2BGR) if file.mode == "RGBA" else cv2.cvtColor(np.array(file), cv2.COLOR_RGB2BGR)
    else:
        # assume bytes
        img_array = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img

def preprocess(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    return gray

def detect_edges(gray: np.ndarray) -> np.ndarray:
    v = np.median(gray)
    lower = int(max(0, 0.66*v))
    upper = int(min(255, 1.33*v))
    edges = cv2.Canny(gray, lower, upper)
    return edges

def find_lines(edges: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    # Probabilistic Hough to find line segments
    linesP = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=120, minLineLength=60, maxLineGap=10)
    if linesP is None:
        return np.empty((0,4), dtype=np.int32), np.empty((0,4), dtype=np.int32)
    lines = linesP.reshape(-1,4)
    # Separate near-horizontal and near-diagonal/vertical
    horizontals, others = [], []
    for x1,y1,x2,y2 in lines:
        dx, dy = x2-x1, y2-y1
        if dx == 0: slope = 1e9
        else: slope = dy/dx
        if abs(slope) < 0.15:
            horizontals.append((x1,y1,x2,y2))
        else:
            others.append((x1,y1,x2,y2))
    return np.array(horizontals, dtype=np.int32), np.array(others, dtype=np.int32)

def cluster_levels(hlines: np.ndarray, img_h: int, tol_px: int = 12) -> List[int]:
    """Cluster horizontal lines into candidate support/resistance y-levels (pixel rows)."""
    if len(hlines) == 0: return []
    ys = []
    for x1,y1,x2,y2 in hlines:
        ys.append(y1)
        ys.append(y2)
    ys = np.array(ys, dtype=np.int32)
    ys = ys[(ys > int(0.05*img_h)) & (ys < int(0.95*img_h))]  # ignore borders
    ys.sort()
    clusters = []
    current = [ys[0]]
    for y in ys[1:]:
        if abs(y - np.mean(current)) <= tol_px:
            current.append(y)
        else:
            clusters.append(int(np.mean(current)))
            current = [y]
    clusters.append(int(np.mean(current)))
    return clusters

def detect_triangle(others: np.ndarray, width: int, height: int) -> Optional[str]:
    """Very rough triangle hint: look for two converging non-horizontal line sets."""
    if len(others) < 2: return None
    slopes = []
    for x1,y1,x2,y2 in others:
        dx = x2-x1
        dy = y2-y1
        if dx == 0: continue
        slopes.append(dy/dx)
    if not slopes: return None
    pos = [s for s in slopes if s > 0.25]
    neg = [s for s in slopes if s < -0.25]
    if len(pos) >= 2 and len(neg) >= 2:
        return "Sym/Asc/Desc Triangle (converging trendlines)"
    return None

def estimate_trend(others: np.ndarray) -> str:
    """Estimate trend direction from non-horizontal segments."""
    if len(others) == 0:
        return "Unknown"
    slopes = []
    for x1,y1,x2,y2 in others:
        dx = x2-x1
        dy = y2-y1
        if dx == 0: continue
        slopes.append(dy/dx)
    if not slopes:
        return "Unknown"
    mean_slope = np.mean(slopes)
    if mean_slope < -0.1:
        return "Uptrend (lower-left to upper-right)"
    elif mean_slope > 0.1:
        return "Downtrend (upper-left to lower-right)"
    else:
        return "Sideways / Range"

def ocr_axis_prices(img: np.ndarray) -> List[float]:
    """Try to read some price labels via OCR; return list of floats (may be empty)."""
    if pytesseract is None:
        return []
    # Crop a thin right-most strip where y-axis labels often live
    h, w = img.shape[:2]
    strip = img[:, int(w*0.85):, :]
    # OCR
    rgb = cv2.cvtColor(strip, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(rgb)
    vals = []
    for tok in text.replace("$"," ").replace(","," ").split():
        try:
            vals.append(float(tok))
        except:
            pass
    # Return unique sorted
    vals = sorted(list(set(vals)))
    return vals

def analyze_image(pil_image: Image.Image) -> Dict[str, Any]:
    """Main image analysis: edges -> lines -> levels -> pattern hints."""
    img = load_image(pil_image)
    gray = preprocess(img)
    edges = detect_edges(gray)
    hlines, others = find_lines(edges)
    h, w = gray.shape[:2]
    levels_px = cluster_levels(hlines, h)
    trend = estimate_trend(others)
    triangle_hint = detect_triangle(others, w, h)
    ocr_prices = ocr_axis_prices(img)
    result = {
        "image_shape": (h, w),
        "num_horizontal_segments": int(len(hlines)),
        "num_other_segments": int(len(others)),
        "levels_px": levels_px,
        "trend_hint": trend,
        "triangle_hint": triangle_hint,
        "ocr_prices_detected": ocr_prices[:6]  # preview a few
    }
    return result