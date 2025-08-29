from __future__ import annotations
from typing import List, Dict, Any, Tuple
from pathlib import Path
import io
import json
import numpy as np
from PIL import Image

# New-style modules that work on in-memory images
from .lp_detector import detect_license_plates
from .ocr import find_text_pii
from .redactor import apply_redactions


# ---------- Single-image path for the mobile POST /process ----------

def process_image_bytes(raw: bytes, cfg: dict) -> Tuple[bytes, Dict[str, Any], bool]:
    """
    Accepts raw image bytes.
    Returns JPEG bytes of the redacted image, metadata dict, and a boolean 'applied'.
    """
    # Decode to RGB ndarray
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img_rgb = np.array(img)

    # 1) plates via YOLO
    lp_boxes = detect_license_plates(img_rgb, cfg)  # list of {x1,y1,x2,y2,label,score}

    # 2) PII via OCR + analyzer
    pii_boxes = find_text_pii(img_rgb, cfg)         # same shape

    # 3) merge then redact once
    all_boxes: List[Dict[str, Any]] = lp_boxes + pii_boxes
    redacted_rgb, applied = apply_redactions(img_rgb, all_boxes, cfg)

    # Encode to JPEG bytes
    out = io.BytesIO()
    Image.fromarray(redacted_rgb).save(out, format="JPEG", quality=90)

    meta = {
        "boxes": all_boxes,
        "counts": {
            "license_plates": len(lp_boxes),
            "pii": len(pii_boxes),
            "total": len(all_boxes),
        }
    }
    return out.getvalue(), meta, applied


# ---------- Batch pipeline for folders (kept for your CLI) ----------

def _iter_input_images(input_dir: Path) -> List[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    return [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]


def run_pipeline(cfg: dict) -> List[str]:
    """
    Batch mode:
      - reads images from cfg['io']['input_dir'] (or a sensible default)
      - writes redacted images to results_img_dir
      - writes JSON reports to results_rpt_dir
      - returns list of report file paths
    """
    io_cfg = cfg.get("io", {})
    input_dir = Path(io_cfg.get("input_dir", "backend/resources/images"))
    out_dir_img = Path(io_cfg.get("results_img_dir", "backend/resources/outputs/images"))
    out_dir_rpt = Path(io_cfg.get("results_rpt_dir", "backend/resources/reports"))

    out_dir_img.mkdir(parents=True, exist_ok=True)
    out_dir_rpt.mkdir(parents=True, exist_ok=True)

    reports: List[str] = []

    for idx, img_path in enumerate(_iter_input_images(input_dir), start=1):
        # Read as bytes once, reuse the single-image codepath
        raw = Path(img_path).read_bytes()

        try:
            redacted_bytes, meta, applied = process_image_bytes(raw, cfg)
        except Exception as e:
            # Skip broken files, but leave a breadcrumb in reports
            err_report = {
                "source_image": str(img_path),
                "error": f"{type(e).__name__}: {e}"
            }
            rp = out_dir_rpt / f"report_{idx:04d}_ERROR.json"
            with open(rp, "w", encoding="utf-8") as f:
                json.dump(err_report, f, indent=2)
            reports.append(str(rp))
            continue

        # Save redacted image
        redacted_path = out_dir_img / f"redacted_{idx:04d}.jpg"
        # redacted_bytes are JPEG in RGB space, write directly
        redacted_path.write_bytes(redacted_bytes)

        # Build report
        report = {
            "source_image": str(img_path),
            "engines": {
                "detector": "YOLOv8",
                "ocr": "tesseract image_to_data",
                "nlp": "Presidio + DistilBERT",
            },
            "counts": meta.get("counts", {}),
            "redactions": {
                "applied": bool(applied),
                "boxes_xyxy": [
                    [int(b["x1"]), int(b["y1"]), int(b["x2"]), int(b["y2"])]
                    for b in meta.get("boxes", [])
                ],
                "redacted_image_path": str(redacted_path),
            },
        }

        rp = out_dir_rpt / f"report_{idx:04d}.json"
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        reports.append(str(rp))

    return reports
