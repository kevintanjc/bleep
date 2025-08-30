from __future__ import annotations
from typing import List, Dict, Any, Tuple
import numpy as np

# New-style modules that work on in-memory images
from .lp_detector import detect_license_plates
from .ocr import find_text_pii
from .redactor import apply_redactions


# ---------- Single-image path for the mobile POST /process ----------

def process_image_np(img_rgb: np.ndarray, cfg: dict) -> Tuple[np.ndarray, Dict[str, Any], bool]:
    """
    Accepts an RGB ndarray (H, W, 3), dtype uint8.
    Returns redacted RGB ndarray, metadata dict, and 'applied' flag.
    """
    print("PROCESSING IMAGE.......")
    if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        raise ValueError(f"Expected HxWx3 RGB, got shape {img_rgb.shape}")

    # 1) license plates
    print("Detecting License Plates")
    lp_boxes = detect_license_plates(img_rgb, cfg)

    # 2) PII text
    print("Detecting text PII")
    pii_boxes = find_text_pii(img_rgb, cfg)

    # 3) merge and redact
    print("Redacting..")
    all_boxes: List[Dict[str, Any]] = lp_boxes + pii_boxes
    redacted_rgb, applied = apply_redactions(img_rgb, all_boxes, cfg)

    # normalize result
    redacted_rgb = np.clip(redacted_rgb, 0, 255).astype(np.uint8)

    meta = {
        "boxes": all_boxes,
        "counts": {
            "license_plates": len(lp_boxes),
            "pii": len(pii_boxes),
            "total": len(all_boxes),
        }
    }
    return redacted_rgb, meta, applied