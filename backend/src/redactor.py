from typing import List, Dict, Tuple
import numpy as np
import cv2

def _clip_box(bx: Dict, w: int, h: int) -> Dict:
    return {
        "x1": int(max(0, min(w - 1, bx["x1"]))),
        "y1": int(max(0, min(h - 1, bx["y1"]))),
        "x2": int(max(0, min(w - 1, bx["x2"]))),
        "y2": int(max(0, min(h - 1, bx["y2"]))),
        "label": bx.get("label", "redact"),
        "score": float(bx.get("score", 1.0)) if bx.get("score") is not None else None
    }

def apply_redactions(img_rgb: np.ndarray, boxes: List[Dict], cfg) -> Tuple[np.ndarray, bool]:
    """
    Returns redacted image and a boolean applied.
    Strategy is configured in cfg["redaction"].
    Supported:
      mode: "fill" or "blur"
      fill_color: [r, g, b]
      blur_ksize: odd int
      blur_sigma: int
    """
    if not boxes:
        return img_rgb, False

    h, w = img_rgb.shape[:2]
    out = img_rgb.copy()

    red_cfg = cfg.get("redaction", {})
    mode = red_cfg.get("mode", "fill")
    fill_color = red_cfg.get("fill_color", [0, 0, 0])  # black box
    blur_ksize = int(red_cfg.get("blur_ksize", 23))
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blur_sigma = int(red_cfg.get("blur_sigma", 11))

    for raw in boxes:
        b = _clip_box(raw, w, h)
        x1, y1, x2, y2 = b["x1"], b["y1"], b["x2"], b["y2"]
        if x2 <= x1 or y2 <= y1:
            continue

        roi = out[y1:y2, x1:x2, :]
        if mode == "blur":
            blurred = cv2.GaussianBlur(roi, (blur_ksize, blur_ksize), blur_sigma)
            out[y1:y2, x1:x2, :] = blurred
        else:
            # fill by default
            out[y1:y2, x1:x2, :] = np.array(fill_color, dtype=np.uint8)

    return out, True