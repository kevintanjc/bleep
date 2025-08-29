from typing import List, Dict, Any, Optional
import numpy as np
import os

# simple cache so you do not reload per request
_MODEL_CACHE: Dict[str, Any] = {}

def _get_model(weights_path: str):
    from ultralytics import YOLO
    m = _MODEL_CACHE.get(weights_path)
    if m is None:
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"YOLO weights not found: {weights_path}")
        m = YOLO(weights_path)
        _MODEL_CACHE[weights_path] = m
    return m

from typing import List, Dict, Any
import numpy as np

def detect_license_plates(img_rgb: np.ndarray, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect license plates using a YOLO model.

    Expects:
      - img_rgb: HxWx3 uint8, RGB
      - cfg from config.yaml with:
          cfg["paths"]["yolo_weights"] -> path to YOLO weights
        Optional overrides:
          cfg["lp"]["score_threshold"] -> float, default 0.25
          cfg["lp"]["expects_bgr"] -> bool, default False
          cfg["lp"]["labels_map"] -> dict[int,str], default {0: "license_plate"}

    Returns a list of dicts:
      {"x1": int, "y1": int, "x2": int, "y2": int, "label": str, "score": float|None}
    """
    if not isinstance(img_rgb, np.ndarray) or img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        raise ValueError(f"Expected RGB ndarray HxWx3, got shape {getattr(img_rgb, 'shape', None)}")

    if img_rgb.dtype != np.uint8:
        img_rgb = np.clip(img_rgb, 0, 255).astype(np.uint8)

    # Config
    paths_cfg = cfg.get("paths") or {}
    weights_path = paths_cfg.get("yolo_weights")
    if not weights_path:
        raise KeyError("cfg['paths']['yolo_weights'] is required")

    lp_cfg = cfg.get("lp", {}) or {}
    conf = float(lp_cfg.get("score_threshold", 0.25))
    expects_bgr = bool(lp_cfg.get("expects_bgr", False))
    labels_map = lp_cfg.get("labels_map") or {0: "license_plate"}

    # Model
    model = _get_model(weights_path)

    # Input color space
    src = img_rgb[:, :, ::-1] if expects_bgr else img_rgb

    # Inference
    try:
        results = model.predict(src, conf=conf, verbose=False)
    except Exception as e:
        raise RuntimeError(f"YOLO predict failed: {type(e).__name__}: {e}")

    out: List[Dict[str, Any]] = []
    if not results:
        return out

    r0 = results[0]
    boxes = getattr(r0, "boxes", None)
    if boxes is None or getattr(boxes, "xyxy", None) is None:
        return out

    # Extract tensors safely
    xyxy = boxes.xyxy
    if hasattr(xyxy, "cpu"):
        xyxy = xyxy.cpu().numpy()

    scores = getattr(boxes, "conf", None)
    if hasattr(scores, "cpu"):
        scores = scores.cpu().numpy()

    classes = getattr(boxes, "cls", None)
    if hasattr(classes, "cpu"):
        classes = classes.cpu().numpy()

    if scores is None:
        scores = [None] * len(xyxy)
    if classes is None:
        classes = [0] * len(xyxy)

    h, w = img_rgb.shape[:2]
    for (x1, y1, x2, y2), sc, cl in zip(xyxy, scores, classes):
        # Clamp and cast to int
        x1i = int(max(0, min(w - 1, float(x1))))
        y1i = int(max(0, min(h - 1, float(y1))))
        x2i = int(max(0, min(w - 1, float(x2))))
        y2i = int(max(0, min(h - 1, float(y2))))

        out.append({
            "x1": x1i,
            "y1": y1i,
            "x2": x2i,
            "y2": y2i,
            "label": labels_map.get(int(cl), "license_plate"),
            "score": float(sc) if sc is not None else None,
        })

    return out