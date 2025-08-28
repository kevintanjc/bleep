import json
from pathlib import Path
import cv2

from backend.src.lp_detector import load_yolo, detect
from backend.src.ocr import ocr_words, compile_patterns, detect_ids_in_words
from backend.src.redactor import draw_redactions

def run_pipeline(cfg: dict):
    model_cfg = cfg["model"]
    io_cfg = cfg["io"]
    ocr_cfg = cfg["ocr"]
    red_cfg = cfg["redaction"]

    model = load_yolo(model_cfg["path"], model_cfg.get("conf_threshold", 0.25))
    patterns = compile_patterns(cfg["patterns"])

    input_images = io_cfg["input_images"]
    out_dir = Path(io_cfg["results_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    all_reports = []

    for idx, img_path in enumerate(input_images, start=1):
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {img_path}")

        det = detect(model, img)
        det.save(filename=str(out_dir / f"pred_{idx}.jpg"))

        redact_boxes_global = []
        detections = []
        for j, box in enumerate(det.boxes.xyxy):
            x1, y1, x2, y2 = [int(v) for v in box.tolist()]
            crop = img[y1:y2, x1:x2]
            crop_name = out_dir / f"det_crop_{idx}_{j}.jpg"
            cv2.imwrite(str(crop_name), crop)

            words = ocr_words(crop, ocr_cfg["config"], ocr_cfg["conf_threshold"])
            findings = detect_ids_in_words(words, patterns)

            mapped_findings = []
            for f in findings:
                bx1, by1, bx2, by2 = f["bbox"]
                gx1, gy1, gx2, gy2 = x1 + bx1, y1 + by1, x1 + bx2, y1 + by2
                redact_boxes_global.append([gx1, gy1, gx2, gy2])
                f_m = dict(f)
                f_m["bbox_global_xyxy"] = [gx1, gy1, gx2, gy2]
                mapped_findings.append(f_m)

            detections.append({
                "detection_index": j,
                "bbox_xyxy": [x1, y1, x2, y2],
                "crop_path": str(crop_name),
                "ocr_word_count": len(words),
                "findings": mapped_findings,
            })

        redacted_image, final_boxes = draw_redactions(img, redact_boxes_global, pad=red_cfg["padding"])
        redacted_path = out_dir / f"redacted_{idx}.png"
        cv2.imwrite(str(redacted_path), redacted_image)

        report = {
            "source_image": img_path,
            "image_size_hw": list(img.shape[:2]),
            "model": model_cfg["path"],
            "detections": detections,
            "redactions": {
                "count": len(final_boxes),
                "boxes_xyxy": final_boxes,
                "redacted_image_path": str(redacted_path),
            },
            "engine": {
                "detector": "ultralytics YOLOv8",
                "ocr": "tesseract image_to_data",
                "tesseract_config": ocr_cfg["config"],
            },
        }
        report_path = out_dir / f"report_{idx}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        all_reports.append(str(report_path))

    return all_reports
