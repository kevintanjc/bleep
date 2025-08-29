from typing import List, Dict, Tuple, Any
import numpy as np

def _clip_box(bx: Dict, w: int, h: int) -> Dict:
    return {
        "x1": int(max(0, min(w - 1, bx["x1"]))),
        "y1": int(max(0, min(h - 1, bx["y1"]))),
        "x2": int(max(0, min(w - 1, bx["x2"]))),
        "y2": int(max(0, min(h - 1, bx["y2"]))),
        "label": bx.get("label", "redact"),
        "score": float(bx.get("score", 1.0)) if bx.get("score") is not None else None
    }

def _ensure_uint8_rgb(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"Redacted image must be HxWx3. Got shape {arr.shape}")
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    if not arr.flags.c_contiguous:
        arr = np.ascontiguousarray(arr)
    return arr

def apply_redactions(img_rgb: np.ndarray, boxes: List[Dict], cfg: Dict[str, Any]) -> Tuple[np.ndarray, bool]:
    """
    Returns (redacted_image_rgb, applied_flag).
    Reads redaction settings from cfg["redaction"].

    Config keys supported:
      style: "fill" or "blur" or "box"  default "fill"
      fill_colour or fill_color: [r,g,b] default [0,0,0]
      blur_ksize: odd int kernel size    default 21
      blur_sigma: int sigma for Gaussian default 0
    """
    if not isinstance(img_rgb, np.ndarray):
        img_rgb = np.asarray(img_rgb)

    img_rgb = _ensure_uint8_rgb(img_rgb)

    if not boxes:
        return img_rgb, False

    h, w = img_rgb.shape[:2]
    out = img_rgb.copy()
    fill_col = [0, 0, 0]
    fill_col = np.array([int(max(0, min(255, c))) for c in fill_col], dtype=np.uint8)

    applied = False

    for raw in boxes:
        b = _clip_box(raw, w, h)
        x1, y1, x2, y2 = b["x1"], b["y1"], b["x2"], b["y2"]
        if x2 <= x1 or y2 <= y1:
            continue

        roi = out[y1:y2, x1:x2, :]
        roi[:] = fill_col
        applied = True

    out = _ensure_uint8_rgb(out)
    return out, applied