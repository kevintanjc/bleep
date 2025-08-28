import json
from pathlib import Path
import cv2

from src.lp_detector import load_lp_dectector, detect
from src.ocr import ocr_words, compile_patterns, detect_ids_in_words
from src.redactor import draw_redactions

def load_images_from_folder(folder):
    folder_path = Path(folder)
    return [str(img_file) for img_file in folder_path.glob("*") if img_file.is_file()]

def run_pipeline(cfg: dict):
    model_cfg = cfg["model"]
    io_cfg = cfg["io"]
    ocr_cfg = cfg["ocr"]

    model = load_lp_dectector(model_cfg["path"], model_cfg.get("conf_threshold", 0.25))
    patterns = compile_patterns(cfg["patterns"])

    input_dir = Path(io_cfg["input_dir"])
    out_dir_img = Path(io_cfg["results_img_dir"]); out_dir_img.mkdir(parents=True, exist_ok=True)
    out_dir_rpt = Path(io_cfg["results_rpt_dir"]); out_dir_rpt.mkdir(parents=True, exist_ok=True)

    all_reports = []
    img_paths = [p for p in input_dir.iterdir() if p.is_file()]

    for idx, img_path in enumerate(img_paths, start=1):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        H, W = img.shape[:2]

        # Stage A, detector boxes
        det = detect(model, img)
        det.save(filename=str(out_dir_img / f"pred_{idx}.jpg"))

        det_boxes = []
        for j, b in enumerate(det.boxes.xyxy.detach().cpu().tolist()):
            x1, y1, x2, y2 = map(int, b)
            det_boxes.append([x1, y1, x2, y2])
            crop = img[y1:y2, x1:x2]
            cv2.imwrite(str(out_dir_img / f"det_crop_{idx}_{j}.jpg"), crop)

        # Stage B, OCR boxes from the full image
        # Do NOT OCR the blurred image. Use the original for accuracy.
        words = ocr_words(img, ocr_cfg["config"], ocr_cfg["conf_threshold"])
        ocr_hits = detect_ids_in_words(words, patterns)
        ocr_boxes = [list(map(int, f["bbox"])) for f in ocr_hits]   # bbox already in global coords? if not, map here

        # Union of boxes to redact: detector first, then OCR
        redact_boxes = det_boxes[:]
        # If your OCR returns local crop coords, map them to global first.
        redact_boxes.extend(ocr_boxes)

        # Single redaction pass
        redacted, final_boxes = draw_redactions(
            img,
            redact_boxes,
            pad=6,
            blur_strength=35,
        )
        redacted_path = out_dir_img / f"redacted_{idx}.png"
        cv2.imwrite(str(redacted_path), redacted)

        # Reporting
        report = {
            "source_image": str(img_path),
            "image_size_hw": [H, W],
            "model": model_cfg["path"],
            "detections": det_boxes,
            "ocr_findings": ocr_hits,
            "redactions": {
                "count": len(final_boxes),
                "boxes_xyxy": final_boxes,
                "redacted_image_path": str(redacted_path),
            },
            "engine": {"detector": "YOLOv8", "ocr": "tesseract image_to_data"},
        }
        rp = out_dir_rpt / f"report_{idx}.json"
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        all_reports.append(str(rp))

    return all_reports
