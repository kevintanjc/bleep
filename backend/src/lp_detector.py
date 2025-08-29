from typing import List, Dict
import numpy as np
from ultralytics import YOLO

_model = None

def _get_model(weights_path: str) -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(weights_path)
    return _model

def detect_license_plates(img_rgb: np.ndarray, cfg) -> List[Dict]:
    """
    img_rgb: np.uint8 array in RGB
    cfg: expects cfg["models"]["lp_detector"] = path to YOLO weights
         optionally cfg["lp"]["score_threshold"] float
    """
    model = _get_model(cfg["models"]["lp_detector"])
    conf = float(cfg.get("lp", {}).get("score_threshold", 0.25))

    # YOLO expects RGB ndarray, so pass directly
    results = model.predict(img_rgb, conf=conf, verbose=False)
    out: List[Dict] = []

    if not results:
        return out

    r0 = results[0]
    if r0.boxes is None or r0.boxes.xyxy is None:
        return out

    xyxy = r0.boxes.xyxy.cpu().numpy()
    scores = r0.boxes.conf.cpu().numpy() if r0.boxes.conf is not None else [None] * len(xyxy)
    classes = r0.boxes.cls.cpu().numpy() if r0.boxes.cls is not None else [0] * len(xyxy)

    labels_map = cfg.get("lp", {}).get("labels_map") or {0: "license_plate"}

    h, w = img_rgb.shape[:2]
    for (x1, y1, x2, y2), sc, cl in zip(xyxy, scores, classes):
        bx = {
            "x1": int(max(0, min(w - 1, x1))),
            "y1": int(max(0, min(h - 1, y1))),
            "x2": int(max(0, min(w - 1, x2))),
            "y2": int(max(0, min(h - 1, y2))),
            "label": labels_map.get(int(cl), "license_plate"),
            "score": float(sc) if sc is not None else None,
        }
        out.append(bx)

    return out